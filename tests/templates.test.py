#!/usr/bin/env python3
"""Runs the job each template generates, without GitLab and without the image.

A template is YAML until a pipeline renders it, and nothing in this repository
renders one: GitLab does, in the project of whoever includes it. So each case
below renders a template with a set of inputs (``scripts/component.py``), then
runs the resulting ``before_script`` and ``script`` in a shell the way a runner
would -- the job's ``variables:`` in the environment, project CI/CD variables
on top of them -- with a stand-in ``ark-tools`` on the ``PATH`` that records
its arguments and environment instead of scanning anything.

What this covers is the contract the README documents: the command line each
template builds, and the precedence ``input > CI/CD variable > image default``.
What it cannot cover is GitLab's own handling of the YAML, nor the image.

  python3 tests/templates.test.py                # run the cases
  python3 tests/templates.test.py --dump DIR     # write each job script to
                                                 # DIR/<template>.sh, for shellcheck
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import component  # noqa: E402  (needs the path set above)

# Records argv, one argument per line, and the exported environment, then exits
# the way the case asks. The environment is written NUL-separated, which keeps
# a value with newlines in one piece, and from bash itself because `env -0` is
# a GNU extension.
ARK_TOOLS_STUB = """#!/usr/bin/env bash
printf '%s\\n' "$@" > "$ARK_STUB_ARGV"
for name in $(compgen -e); do
  printf '%s=%s\\0' "$name" "${!name}"
done > "$ARK_STUB_ENV"
exit "${ARK_STUB_EXIT:-0}"
"""

# The project directory inside the job. Kept symbolic in the cases below and
# replaced with the temporary directory of the run.
PROJECT_DIR = "$CI_PROJECT_DIR"

# Each case: the template, the inputs of the include, the CI/CD variables the
# project sets, and what the job must have done. `env` maps a variable to the
# value ark-tools must see, or to None when it must not be set at all.
CASES = [
    # --- full-scan -------------------------------------------------------------
    dict(
        name="full-scan with no inputs scans the project and skips the image step",
        template="full-scan",
        argv=["full-scan"],
        env={
            "FULL_SCAN_SKIP_IMAGE": "true",
            "FULL_SCAN_PATH": PROJECT_DIR,
            "REPORT_DIR": f"{PROJECT_DIR}/scan-reports",
            "TRIVY_CACHE_DIR": f"{PROJECT_DIR}/.cache/trivy",
            "GIT_DEPTH": "0",
            "ARK_IMAGE_NAME": "ghcr.io/tooark/security-scanner",
            "TRIVY_SEVERITY": None,
            "HADOLINT_FAILURE_LEVEL": None,
            "BETTERLEAKS_REDACT": None,
        },
    ),
    dict(
        name="full-scan with an image, an SBOM and tool inputs",
        template="full-scan",
        inputs={
            "image": "registry.example.com/app:1",
            "sbom": True,
            "trivy_severity": "CRITICAL,HIGH",
            "hadolint_failure_level": "warning",
            "dockerfiles": "Dockerfile,docker/Dockerfile.worker",
            "reports_dir": "out/security",
        },
        argv=["full-scan", "registry.example.com/app:1", "--sbom"],
        env={
            "FULL_SCAN_SKIP_IMAGE": None,
            "TRIVY_SEVERITY": "CRITICAL,HIGH",
            "HADOLINT_FAILURE_LEVEL": "warning",
            "FULL_SCAN_DOCKERFILES": "Dockerfile,docker/Dockerfile.worker",
            "REPORT_DIR": f"{PROJECT_DIR}/out/security",
        },
    ),
    dict(
        name="a blank input keeps the project's CI/CD variable",
        template="full-scan",
        variables={
            "TRIVY_SEVERITY": "CRITICAL",
            "FULL_SCAN_DOCKERFILES": "a.Dockerfile,b.Dockerfile",
            "FULL_SCAN_MODE": "repo",
        },
        argv=["full-scan"],
        env={
            "TRIVY_SEVERITY": "CRITICAL",
            "FULL_SCAN_DOCKERFILES": "a.Dockerfile,b.Dockerfile",
            "FULL_SCAN_MODE": "repo",
        },
    ),
    dict(
        name="an input wins over the project's CI/CD variable",
        template="full-scan",
        inputs={"trivy_severity": "HIGH", "scan_mode": "fs", "dockerfiles": "Dockerfile"},
        variables={
            "TRIVY_SEVERITY": "CRITICAL",
            "FULL_SCAN_DOCKERFILES": "a.Dockerfile",
            "FULL_SCAN_MODE": "repo",
        },
        argv=["full-scan"],
        env={"TRIVY_SEVERITY": "HIGH", "FULL_SCAN_DOCKERFILES": "Dockerfile", "FULL_SCAN_MODE": "fs"},
    ),
    dict(
        name="FULL_SCAN_SKIP_IMAGE set by the project is not forced back to true",
        template="full-scan",
        variables={"FULL_SCAN_SKIP_IMAGE": "false"},
        argv=["full-scan"],
        env={"FULL_SCAN_SKIP_IMAGE": "false"},
    ),
    dict(
        name="extra_args are split on spaces but never globbed",
        template="full-scan",
        inputs={"extra_args": "--skip-dirs * --debug"},
        argv=["full-scan", "--", "--skip-dirs", "*", "--debug"],
    ),
    # --- image-scan ------------------------------------------------------------
    dict(
        name="image-scan puts --sbom before the image",
        template="image-scan",
        inputs={"image": "app:1", "sbom": True, "sbom_format": "spdx-json"},
        argv=["image-scan", "--sbom", "app:1"],
        env={"SBOM_FORMAT": "spdx-json", "TRIVY_CACHE_DIR": f"{PROJECT_DIR}/.cache/trivy"},
    ),
    dict(
        name="image-scan refuses an empty image before ark-tools runs",
        template="image-scan",
        inputs={"image": ""},
        exit_code=2,
        argv=None,
    ),
    # --- the single-tool scans -------------------------------------------------
    dict(
        name="filesystem-scan defaults to the project directory",
        template="filesystem-scan",
        argv=["filesystem-scan", PROJECT_DIR],
    ),
    dict(
        name="filesystem-scan with a path and an SBOM",
        template="filesystem-scan",
        inputs={"path": "services/api", "sbom": True},
        argv=["filesystem-scan", "--sbom", "services/api"],
    ),
    dict(
        name="config-scan",
        template="config-scan",
        inputs={"path": "deploy/terraform", "trivy_exit_code": "0"},
        argv=["config-scan", "deploy/terraform"],
        env={"TRIVY_EXIT_CODE": "0"},
    ),
    dict(
        name="repo-scan accepts a remote URL",
        template="repo-scan",
        inputs={"target": "https://gitlab.example.com/group/project.git"},
        argv=["repo-scan", "https://gitlab.example.com/group/project.git"],
    ),
    dict(
        name="dockerfile-lint defaults to the Dockerfile at the project root",
        template="dockerfile-lint",
        argv=["dockerfile-lint", f"{PROJECT_DIR}/Dockerfile"],
        env={"TRIVY_CACHE_DIR": None},
    ),
    dict(
        name="secret-scan --no-git",
        template="secret-scan",
        inputs={"no_git": "true", "betterleaks_redact": "80"},
        argv=["secret-scan", "--no-git", PROJECT_DIR],
        env={"BETTERLEAKS_REDACT": "80", "GIT_DEPTH": "0", "TRIVY_CACHE_DIR": None},
    ),
    # --- across templates ------------------------------------------------------
    dict(
        name="a failing scan fails the job with the scanner's exit code",
        template="secret-scan",
        stub_exit=1,
        exit_code=1,
        argv=["secret-scan", PROJECT_DIR],
    ),
    dict(
        name="a secret set as a masked CI/CD variable reaches the scanner untouched",
        template="full-scan",
        inputs={"report_url": "https://hub.example.com/api/reports"},
        variables={"REPORT_TOKEN": "s3cr3t"},
        argv=["full-scan"],
        env={"REPORT_URL": "https://hub.example.com/api/reports", "REPORT_TOKEN": "s3cr3t"},
        log_excludes="s3cr3t",
    ),
]


def job_script(job: dict) -> str:
  """before_script and script as the one shell script a runner makes of them."""
  lines = ["set -e"]
  for section in ("before_script", "script"):
    lines.extend(job.get(section, []))
  return "\n".join(lines) + "\n"


def expand(value: str, project_dir: str) -> str:
  return value.replace(PROJECT_DIR, project_dir)


def install_stub(directory: Path) -> Path:
  """Writes the stand-in ark-tools once; every case shares it."""
  directory.mkdir()
  stub = directory / "ark-tools"
  stub.write_text(ARK_TOOLS_STUB, encoding="utf-8", newline="\n")
  stub.chmod(0o755)
  return directory


def run_case(case: dict, components: dict, bash: str, stub_dir: Path, workdir: Path) -> list[str]:
  """Runs one case in its own directory and returns what went wrong."""
  project_dir = (workdir / "project").as_posix()
  (workdir / "project").mkdir(parents=True)
  argv_file, env_file = workdir / "argv.txt", workdir / "env.bin"

  _, job = component.render(components[case["template"]], case.get("inputs"))

  env = {
      "PATH": stub_dir.as_posix() + os.pathsep + os.environ["PATH"],
      "CI_PROJECT_DIR": project_dir,
      "ARK_STUB_ARGV": argv_file.as_posix(),
      "ARK_STUB_ENV": env_file.as_posix(),
      "ARK_STUB_EXIT": str(case.get("stub_exit", 0)),
  }
  # A runner expands variables inside `variables:`; the templates only ever
  # refer to the project directory there. A boolean input staged there, such
  # as sbom, arrives as the text "true". Project CI/CD variables are applied
  # last because they take precedence over the ones a job declares.
  for name, value in job.get("variables", {}).items():
    env[name] = expand(component.as_text(value), project_dir)
  env.update(case.get("variables", {}))

  result = subprocess.run(
      [bash, "-c", job_script(job)],
      env=env, cwd=project_dir, capture_output=True, text=True, check=False,
  )

  problems: list[str] = []
  expected_exit = case.get("exit_code", 0)
  if result.returncode != expected_exit:
    problems.append(f"exit {result.returncode}, expected {expected_exit}\n{result.stdout}{result.stderr}")

  expected_argv = case.get("argv")
  if expected_argv is None:
    if argv_file.exists():
      problems.append("ark-tools ran, but the job should have stopped before it")
    return problems
  if not argv_file.exists():
    problems.append(f"ark-tools never ran\n{result.stdout}{result.stderr}")
    return problems

  actual_argv = argv_file.read_text(encoding="utf-8").splitlines()
  expected_argv = [expand(arg, project_dir) for arg in expected_argv]
  if actual_argv != expected_argv:
    problems.append(f"ran 'ark-tools {' '.join(actual_argv)}', expected 'ark-tools {' '.join(expected_argv)}'")

  seen = dict(
      entry.split("=", 1) for entry in env_file.read_text(encoding="utf-8").split("\0") if "=" in entry
  )
  for name, expected in case.get("env", {}).items():
    actual = seen.get(name)
    if expected is not None:
      expected = expand(expected, project_dir)
    if actual != expected:
      problems.append(f"ark-tools saw {name}={actual!r}, expected {expected!r}")

  secret = case.get("log_excludes")
  if secret and secret in result.stdout + result.stderr:
    problems.append(f"the job log printed {secret!r}")

  return problems


def dump(directory: Path, components: dict) -> int:
  """Writes the script of each template, rendered with its defaults."""
  directory.mkdir(parents=True, exist_ok=True)
  for name, loaded in components.items():
    required = {key: "" for key, definition in loaded.inputs.items() if "default" not in definition}
    _, job = component.render(loaded, required)
    target = directory / f"{name}.sh"
    target.write_text("#!/bin/sh\n" + job_script(job), encoding="utf-8", newline="\n")
    print(f"  wrote {target.as_posix()}")
  return 0


def main(argv: list[str]) -> int:
  components = component.load_all()

  if len(argv) == 3 and argv[1] == "--dump":
    return dump(Path(argv[2]), components)
  if len(argv) != 1:
    print(__doc__, file=sys.stderr)
    return 2

  bash = shutil.which("bash")
  if bash is None:
    print("bash is required to run the job scripts", file=sys.stderr)
    return 1

  failed = 0
  with tempfile.TemporaryDirectory() as tmp:
    stub_dir = install_stub(Path(tmp) / "bin")
    for index, case in enumerate(CASES):
      problems = run_case(case, components, bash, stub_dir, Path(tmp) / f"case-{index}")
      if problems:
        failed += 1
        print(f"  FAIL {case['name']}")
        for problem in problems:
          print("       " + problem.replace("\n", "\n       "))
      else:
        print(f"  ok   {case['name']}")

  untested = sorted(set(components) - {case["template"] for case in CASES})
  for name in untested:
    failed += 1
    print(f"  FAIL templates/{name}.yml has no case in this file")

  if failed:
    print(f"\n{failed} case(s) failed", file=sys.stderr)
    return 1

  print(f"\nall {len(CASES)} template cases passed")
  return 0


if __name__ == "__main__":
  sys.exit(main(sys.argv))
