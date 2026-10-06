<!--
  Links to files outside templates/, LICENSE and VERSION are absolute on
  purpose: the CI/CD Catalog mirror (catalog-mirror/) syncs this README without
  those files, so relative links break on the catalog page.

  Every section heading starts with an icon, and the anchor then starts with a
  hyphen: "## 🔧 Inputs" is #-inputs. Two rules keep those anchors the same on
  GitHub and on the GitLab catalog page. Pick icons that are a single
  character: one that carries a variation selector (U+FE0F, as in the warning
  sign) leaves an invisible character in the anchor. And keep "&" out of
  headings: it turns into a double hyphen on GitHub and a single one on GitLab.
-->
<div align="left">
  <img src="https://raw.githubusercontent.com/Tooark/template-security-scanner/main/media/banner-ci-security-scanner.png" alt="CI Security Scanner" width="100%" />
</div>

# CI Security Scanner — GitLab CI/CD templates

GitLab CI/CD templates that run the Tooark
[`security-scanner`](https://github.com/Tooark/base-images/tree/main/security-scanner)
image — **Trivy** (vulnerabilities), **Hadolint** (Dockerfile lint) and
**Betterleaks** (secret detection) behind one `ark-tools` CLI, producing a
single `ark-report-tools v1.3` report.

Seven templates in [`templates/`](templates/), one job each. Include one, pass
inputs, and the pipeline gets the scan, the failure gates, a cached
vulnerability database and the reports as job artifacts. They work through
`include: remote:` from any GitLab instance, or as components of a CI/CD
Catalog.

> **On GitHub Actions?** The same scans ship as a GitHub Action in
> [`Tooark/action-security-scanner`](https://github.com/Tooark/action-security-scanner).
> Its inputs carry the same names in kebab-case: `trivy_severity` here is
> `trivy-severity` there.

New to CI pipelines? The
[onboarding guide](https://tooark.com/template-security-scanner/) walks
through every file in this repository and the reasoning behind each decision,
written for readers who know software development but not CI. Source in
[`docs/`](https://github.com/Tooark/template-security-scanner/tree/main/docs).

🌍 **Languages:** ![USA Flag](https://flagcdn.com/w20/us.png) **English (this file)** · [![Brazil Flag](https://flagcdn.com/w20/br.png) Português](https://github.com/Tooark/template-security-scanner/blob/main/README.pt-BR.md)

---

## 📑 Contents

- [🚀 Quick start](#-quick-start)
- [📋 Requirements](#-requirements)
- [🧩 Templates](#-templates)
- [🚦 Failure gates](#-failure-gates)
- [🔧 Inputs](#-inputs)
- [📊 Reports](#-reports)
- [🔀 How precedence works](#-how-precedence-works)
- [🔑 Secrets](#-secrets)
- [🍳 Recipes](#-recipes)
- [🔩 Overriding what inputs do not expose](#-overriding-what-inputs-do-not-expose)
- [💾 Trivy database cache](#-trivy-database-cache)
- [🐳 Which image wrote the report](#-which-image-wrote-the-report)
- [🔐 Security notes](#-security-notes)
- [🔖 Versioning](#-versioning)
- [📦 Publishing](#-publishing)
- [🚧 Gotchas](#-gotchas)
- [📁 Repository layout](#-repository-layout)
- [🧪 Development](#-development)
- [🔗 Related projects](#-related-projects)
- [🤝 Contributing](#-contributing)
- [🆘 Help and Security](#-help-and-security)
- [💖 Support](#-support)
- [📝 License](#-license)

---

## 🚀 Quick start

### Remote include

Works on gitlab.com and on any instance that can reach
`raw.githubusercontent.com`. No catalog required.

```yaml
include:
  - remote: "https://raw.githubusercontent.com/Tooark/template-security-scanner/v1.3.0/templates/full-scan.yml"
```

That one include adds a `security:full-scan` job to the `test` stage. With no
inputs it runs without the image step: Trivy over the source tree, Betterleaks
over the git history and Hadolint over `./Dockerfile`. The job fails when a
[gate](#-failure-gates) trips, and the reports are kept as artifacts either way.

To include the container image the pipeline has built:

```yaml
include:
  - remote: "https://raw.githubusercontent.com/Tooark/template-security-scanner/v1.3.0/templates/full-scan.yml"
    inputs:
      stage: test
      image: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
      trivy_severity: "CRITICAL,HIGH"
      hadolint_failure_level: "warning"
```

### CI/CD Catalog

The catalog only lists components hosted on the GitLab instance itself. Once
the [mirror project](https://github.com/Tooark/template-security-scanner/tree/main/catalog-mirror)
has published a version to yours:

```yaml
include:
  - component: $CI_SERVER_FQDN/tooark/ci-security-scanner/full-scan@1.3.0
    inputs:
      image: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"
      trivy_severity: "CRITICAL,HIGH"
```

Complete pipelines, ready to copy, live in
[`examples/`](https://github.com/Tooark/template-security-scanner/tree/main/examples):

| Example                                                                                                                                        | What it shows                                                             |
| ---------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| [`quick-start.gitlab-ci.yml`](https://github.com/Tooark/template-security-scanner/blob/main/examples/quick-start.gitlab-ci.yml)             | The one-line include above                                                |
| [`remote-include.gitlab-ci.yml`](https://github.com/Tooark/template-security-scanner/blob/main/examples/remote-include.gitlab-ci.yml)       | Build, full scan of the pushed image, a merge-request job, a job override |
| [`catalog-component.gitlab-ci.yml`](https://github.com/Tooark/template-security-scanner/blob/main/examples/catalog-component.gitlab-ci.yml) | The same scans as catalog components, with rules and runner tags          |

---

## 📋 Requirements

| Requirement | Detail                                                                                                                                        |
| ----------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| GitLab      | **16.11 or newer**, gitlab.com or self-managed; 17.0 or newer to consume from a CI/CD Catalog                                                 |
| Runner      | An executor that runs the job inside the image: `docker`, `docker+machine` or `kubernetes`. Not `shell` or `ssh`                              |
| Stage       | The stage named by `stage` (default `test`) must exist in the pipeline                                                                        |
| Network     | `ghcr.io` for the scanner image, the Trivy vulnerability database (or a `trivy_server`), and `raw.githubusercontent.com` for a remote include |

The full support matrix is in
[`SUPPORTED-INTEGRATIONS.md`](https://github.com/Tooark/template-security-scanner/blob/main/SUPPORTED-INTEGRATIONS.md).

---

## 🧩 Templates

Each template generates exactly one job, named `security:<template>`, that runs
the `ark-tools` command of the same name inside the image.

| Template                                               | Tool        | What it does                                                  | Main input           |
| ------------------------------------------------------ | ----------- | ------------------------------------------------------------- | -------------------- |
| [`full-scan.yml`](templates/full-scan.yml)             | all three   | Image + source + secrets + Dockerfile lint, one merged report | `image`, `scan_path` |
| [`image-scan.yml`](templates/image-scan.yml)           | Trivy       | Vulnerability scan of a container image                       | `image` (required)   |
| [`filesystem-scan.yml`](templates/filesystem-scan.yml) | Trivy       | Scan of the source tree (lockfiles, OS and language deps)     | `path`               |
| [`config-scan.yml`](templates/config-scan.yml)         | Trivy       | IaC / misconfiguration scan                                   | `path`               |
| [`repo-scan.yml`](templates/repo-scan.yml)             | Trivy       | Repository scan; accepts a remote URL                         | `target`             |
| [`dockerfile-lint.yml`](templates/dockerfile-lint.yml) | Hadolint    | Lint of one Dockerfile                                        | `dockerfile`         |
| [`secret-scan.yml`](templates/secret-scan.yml)         | Betterleaks | Secrets in the working tree and the git history               | `path`, `no_git`     |

`full-scan` without an `image` skips the image step; the other steps can be
turned off with `skip_lint` and `skip_secrets`.

---

## 🚦 Failure gates

A tripped gate fails the job, and with it the pipeline.

| Tool        | Fails when                                                     | Turn it off with                        |
| ----------- | -------------------------------------------------------------- | --------------------------------------- |
| Trivy       | A severity in `trivy_severity_fail` is found, and it has a fix | `trivy_exit_code: "0"`                  |
| Hadolint    | A finding at `hadolint_failure_level` or above                 | `hadolint_failure_level: "none"`        |
| Betterleaks | Any secret is detected                                         | `betterleaks_fail_on_findings: "false"` |

The report and the gate are separate settings: `trivy_severity` decides what is
written to the report, `trivy_severity_fail` what fails the job. The same split
applies to `trivy_ignore_unfixed` and `trivy_ignore_unfixed_fail`.

`allow_failure: true` keeps every gate but lets the pipeline continue: the job
ends in a warning instead of a failure.

---

## 🔧 Inputs

Every input is optional except `image` for `image-scan`. The `spec:inputs`
block at the top of each template is the authoritative reference, with a
description and the allowed values of each input.

Mind the types: GitLab rejects an include whose value has the wrong one.
`allow_failure` and `sbom` are **booleans** and take a bare `true`; `rules` and
`tags` are **arrays**; everything else is a **string**, so the on/off switches
among them take a quoted `"true"` or `"false"`.

### The job

On every template.

| Input                 | Default                           | Notes                                                        |
| --------------------- | --------------------------------- | ------------------------------------------------------------ |
| `job_name`            | `security:<template>`             | Change it to include the same template more than once        |
| `stage`               | `test`                            | The stage must exist in the pipeline                         |
| `rules`               | `[{when: on_success}]`            | Replace to control when the scan runs                        |
| `tags`                | `[]`                              | Runner tags; empty means any runner                          |
| `timeout`             | `1h`                              | `15m` on `dockerfile-lint`                                   |
| `allow_failure`       | `false`                           | Let the pipeline continue when a gate trips                  |
| `reports_dir`         | `scan-reports`                    | Where reports are written, relative to the project directory |
| `artifacts_expire_in` | `7 days`                          | How long the report artifacts are kept                       |
| `scanner_image`       | `ghcr.io/tooark/security-scanner` | Change it to pull from a mirror                              |
| `scanner_version`     | `1.10`                            | Image tag. Pin it; `latest` makes pipelines non-reproducible |
| `extra_args`          | —                                 | Extra flags forwarded to the underlying tool after `--`      |

### What to scan

| Input          | Default                      | Templates                                       | Notes                                                                                |
| -------------- | ---------------------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------ |
| `image`        | —                            | `full-scan`, `image-scan`                       | Image reference. Empty skips the image step of `full-scan`; required by `image-scan` |
| `scan_path`    | `$CI_PROJECT_DIR`            | `full-scan`                                     | Project path scanned for vulnerabilities, secrets and Dockerfiles                    |
| `path`         | `$CI_PROJECT_DIR`            | `filesystem-scan`, `config-scan`, `secret-scan` | Directory to scan                                                                    |
| `target`       | `$CI_PROJECT_DIR`            | `repo-scan`                                     | Local path or remote repository URL                                                  |
| `dockerfile`   | `$CI_PROJECT_DIR/Dockerfile` | `dockerfile-lint`                               | The one Dockerfile to lint                                                           |
| `dockerfiles`  | `Dockerfile`                 | `full-scan`                                     | Comma-separated Dockerfiles, relative to `scan_path`                                 |
| `scan_mode`    | `fs`                         | `full-scan`                                     | Trivy source scan mode: `fs` or `repo`                                               |
| `skip_image`   | `false`                      | `full-scan`                                     | Skip the Trivy image step                                                            |
| `skip_lint`    | `false`                      | `full-scan`                                     | Skip the Hadolint step                                                               |
| `skip_secrets` | `false`                      | `full-scan`                                     | Skip the Betterleaks step                                                            |
| `no_git`       | `false`                      | `secret-scan`                                   | Scan only the working tree, not the git history                                      |
| `git_depth`    | `0`                          | `full-scan`, `repo-scan`, `secret-scan`         | Clone depth. Keep `0` so Betterleaks can walk the whole history                      |
| `sbom`         | `false`                      | `full-scan`, `image-scan`, `filesystem-scan`    | Also generate an SBOM                                                                |
| `sbom_format`  | `cyclonedx`                  | same as `sbom`                                  | `cyclonedx` or `spdx-json`                                                           |

### Trivy

On `full-scan`, `image-scan`, `filesystem-scan`, `config-scan` and `repo-scan`.

| Input                       | Image default                      | Notes                                                                               |
| --------------------------- | ---------------------------------- | ----------------------------------------------------------------------------------- |
| `trivy_severity`            | `UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL` | Severities written to the report                                                    |
| `trivy_severity_fail`       | `HIGH,CRITICAL`                    | Severities that trip the gate                                                       |
| `trivy_ignore_unfixed`      | `false`                            | Drop vulnerabilities without a fix from the report. Not on `config-scan`            |
| `trivy_ignore_unfixed_fail` | `true`                             | Gate only on vulnerabilities that have a fix. Not on `config-scan`                  |
| `trivy_exit_code`           | `1`                                | `0` disables the Trivy gate                                                         |
| `trivy_format`              | `json`                             | `json`, `sarif` or `table`; also `cyclonedx` or `spdx-json` except on `config-scan` |
| `trivy_scanners`            | Trivy's own                        | E.g. `vuln,secret,misconfig,license`. Not on `config-scan`                          |
| `trivy_timeout`             | `10m`                              | E.g. `15m`                                                                          |
| `trivy_server`              | —                                  | Trivy server endpoint; set `TRIVY_TOKEN` as a masked variable. Not on `config-scan` |
| `trivy_ignorefile`          | auto-detected                      | Path to a `.trivyignore` file                                                       |

### Hadolint

On `dockerfile-lint` and `full-scan`.

| Input                       | Image default | Notes                                                                |
| --------------------------- | ------------- | -------------------------------------------------------------------- |
| `hadolint_failure_level`    | `error`       | Lowest level that fails: `error`, `warning`, `info`, `style`, `none` |
| `hadolint_config`           | —             | Path to a `.hadolint.yaml` file                                      |
| `hadolint_format`           | `json`        | `json`, `tty` or `sarif`                                             |
| `hadolint_log_max_findings` | `20`          | Findings itemized in the log. `dockerfile-lint` only                 |

### Betterleaks

On `secret-scan` and `full-scan`.

| Input                          | Image default | Notes                                                             |
| ------------------------------ | ------------- | ----------------------------------------------------------------- |
| `betterleaks_fail_on_findings` | `true`        | Fail when a secret is detected                                    |
| `betterleaks_redact`           | `100`         | Percentage of each secret masked in the report (`0`–`100`)        |
| `betterleaks_baseline`         | —             | Path to a `betterleaks-baseline.json` with accepted findings      |
| `betterleaks_config`           | —             | Path to a `.betterleaks.toml` file                                |
| `betterleaks_format`           | `json`        | `json`, `csv`, `junit`, `sarif` or `template`. `secret-scan` only |
| `betterleaks_log_max_findings` | `20`          | Findings itemized in the log. `secret-scan` only                  |

### Report webhook

On every template.

| Input                  | Image default | Notes                                        |
| ---------------------- | ------------- | -------------------------------------------- |
| `report_url`           | —             | Comma-separated URLs the report is POSTed to |
| `report_fail_on_error` | `false`       | Fail the job when the upload fails           |

The bearer token is a secret: set `REPORT_TOKEN` as a masked CI/CD variable,
see [Secrets](#-secrets).

The tool inputs map one to one to the environment variables documented in the
[image README](https://github.com/Tooark/base-images/blob/main/security-scanner/README.md):
`trivy_severity` sets `TRIVY_SEVERITY`, `betterleaks_redact` sets
`BETTERLEAKS_REDACT`, and so on. A variable with no input of its own — or an
input a given template does not declare — is set as a CI/CD variable instead;
see [How precedence works](#-how-precedence-works).

---

## 📊 Reports

Everything lands in `reports_dir` and is kept as job artifacts, including when
the job fails.

| Template          | Tool report                                                          | `ark-report-tools` envelope       |
| ----------------- | -------------------------------------------------------------------- | --------------------------------- |
| `full-scan`       | the files below, per step; the lint report is `hadolint-<file>.json` | `full-scan-report.json`           |
| `image-scan`      | `trivy-image.json`                                                   | `ark-report-image-scan.json`      |
| `filesystem-scan` | `trivy-filesystem.json`                                              | `ark-report-filesystem-scan.json` |
| `config-scan`     | `trivy-config.json`                                                  | `ark-report-config-scan.json`     |
| `repo-scan`       | `trivy-repo.json`                                                    | `ark-report-repo-scan.json`       |
| `dockerfile-lint` | `hadolint.json`                                                      | `ark-report-dockerfile-lint.json` |
| `secret-scan`     | `betterleaks.json`                                                   | `ark-report-secret-scan.json`     |

The envelope is the stable format: tool output wrapped with the scan target,
the project, the commit and the scanner image that produced it. It is what
`report_url` receives. `sbom: true` adds `trivy-image.sbom.json` or
`trivy-filesystem.sbom.json`, and a `trivy_format` other than `json` adds a
converted copy next to the JSON report, such as `trivy-filesystem.sarif`.

---

## 🔀 How precedence works

Every tunable resolves in the same order:

```text
input  >  CI/CD variable  >  image default
```

An **empty input is never forwarded**. That is deliberate: it lets a project,
or a whole group, set `TRIVY_SEVERITY` once as a CI/CD variable and leave the
matching input blank in every include, rather than repeating it. Setting both
means the input wins.

```yaml
variables:
  TRIVY_SEVERITY: "CRITICAL,HIGH" # every scan in this pipeline
  HADOLINT_FAILURE_LEVEL: "warning"

include:
  - remote: "https://raw.githubusercontent.com/Tooark/template-security-scanner/v1.3.0/templates/filesystem-scan.yml"
  - remote: "https://raw.githubusercontent.com/Tooark/template-security-scanner/v1.3.0/templates/dockerfile-lint.yml"
```

The job runs inside the scanner image, so every CI/CD variable reaches the
tools directly — including the ones that have no input, such as
`TRIVY_SKIP_DB_UPDATE` or `REPORT_METHOD`.

Two exceptions, both about paths. `scan_path` always carries a value, so it
wins over a `FULL_SCAN_PATH` variable. And `REPORT_DIR` and `TRIVY_CACHE_DIR`
are not yours to set as CI/CD variables: the job declares its artifacts and its
cache against the paths the template chose, through `reports_dir`.

---

## 🔑 Secrets

Input values are visible in the rendered pipeline configuration, so secrets
never travel as inputs. Set them as **masked** CI/CD variables under
_Settings > CI/CD > Variables_, on the project or the group, and the job picks
them up:

`TRIVY_TOKEN`, `TRIVY_USERNAME`, `TRIVY_PASSWORD`, `REPORT_TOKEN`,
`REPORT_HEADERS`, `REPORT_SBOM_URL`, `REPORT_SBOM_TOKEN`.

A **protected** variable only reaches jobs on protected branches and tags; a
scan on a merge request from a feature branch will not see it.

Betterleaks redacts every secret in the report by default
(`betterleaks_redact: "100"`), and the job log prints only rule, file, line and
short commit — never the secret itself.

---

## 🍳 Recipes

**Scan the image the pipeline pushed to the project registry.** The registry is
private unless the project is public, so hand Trivy the job's own credentials
by redeclaring the generated job:

```yaml
include:
  - remote: "https://raw.githubusercontent.com/Tooark/template-security-scanner/v1.3.0/templates/image-scan.yml"
    inputs:
      image: "$CI_REGISTRY_IMAGE:$CI_COMMIT_SHORT_SHA"

"security:image-scan":
  needs: ["build"]
  variables:
    TRIVY_USERNAME: "$CI_REGISTRY_USER"
    TRIVY_PASSWORD: "$CI_REGISTRY_PASSWORD"
```

**Run the same template twice.** Give the second include its own `job_name`,
and its own `reports_dir` so the two sets of artifacts do not overwrite each
other in a later job that downloads both:

```yaml
include:
  - remote: "https://raw.githubusercontent.com/Tooark/template-security-scanner/v1.3.0/templates/dockerfile-lint.yml"
  - remote: "https://raw.githubusercontent.com/Tooark/template-security-scanner/v1.3.0/templates/dockerfile-lint.yml"
    inputs:
      job_name: "security:dockerfile-lint-worker"
      dockerfile: "$CI_PROJECT_DIR/docker/Dockerfile.worker"
      reports_dir: "scan-reports/worker"
```

**Scan merge requests only.** Replace `rules`:

```yaml
include:
  - remote: "https://raw.githubusercontent.com/Tooark/template-security-scanner/v1.3.0/templates/secret-scan.yml"
    inputs:
      rules:
        - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

**Accept a known finding.** Commit a `.trivyignore` at the project root — it is
picked up automatically — or a Betterleaks baseline:

```yaml
include:
  - remote: "https://raw.githubusercontent.com/Tooark/template-security-scanner/v1.3.0/templates/secret-scan.yml"
    inputs:
      betterleaks_baseline: ".security/betterleaks-baseline.json"
```

**Report without blocking.** `allow_failure: true` turns a tripped gate into a
warning on the pipeline:

```yaml
include:
  - remote: "https://raw.githubusercontent.com/Tooark/template-security-scanner/v1.3.0/templates/filesystem-scan.yml"
    inputs:
      allow_failure: true
```

---

## 🔩 Overriding what inputs do not expose

A generated job is an ordinary job. Redeclare it by name to change anything the
inputs do not cover:

```yaml
"security:full-scan":
  needs: ["build"]
  services:
    - docker:27-dind
  cache: [] # disable the Trivy database cache
  variables:
    TRIVY_SCANNERS: "vuln,secret,misconfig,license"
```

GitLab merges the two definitions key by key, so the override only has to name
what changes. If you renamed the job with `job_name`, redeclare that name.

---

## 💾 Trivy database cache

Downloading the vulnerability database on every build is the slowest part of a
scan and the easiest way to hit registry rate limits, so the templates cache
it. `dockerfile-lint` and `secret-scan` skip the cache entirely — Hadolint and
Betterleaks never read the database.

`TRIVY_CACHE_DIR` points at `$CI_PROJECT_DIR/.cache/trivy`, and that path is
cached under the fixed key `ark-trivy-db`, so every branch shares one database.
The cache is saved with `when: always`: a tripped gate fails the job by design,
and GitLab does not save the cache of a failed job unless told to.

> On a self-hosted instance, runner caches are stored on the runner's own disk
> by default. With several runners, a job only hits the cache when it lands on
> the runner that wrote it. Configuring
> [distributed caching](https://docs.gitlab.com/runner/configuration/autoscale/#distributed-runners-caching)
> (S3 or equivalent) in `config.toml` is what makes the hit rate consistent.

| Goal                     | How                                                |
| ------------------------ | -------------------------------------------------- |
| Disable the cache        | Redeclare the job with `cache: []`                 |
| Reuse without refreshing | `TRIVY_SKIP_DB_UPDATE: "true"` as a CI/CD variable |

A cached database is still refreshed when Trivy considers it stale; the cache
saves the download, it does not freeze the data. `TRIVY_SKIP_DB_UPDATE` does
freeze it, which trades result accuracy for speed — the image forwards it to
Trivy, which reads the variable natively.

---

## 🐳 Which image wrote the report

The `ark-report-tools` envelope carries an `image` object naming the scanner
that produced the report. The image knows only its own build version, so the
templates pass the rest: `ARK_IMAGE_NAME` and `ARK_IMAGE_TAG` come from
`scanner_image` and `scanner_version`, so a mirror or a floating tag is recorded
as it ran. GitLab exposes no digest for a job image; set `ARK_IMAGE_DIGEST` as
a CI/CD variable to record one, which makes `image.reference` an immutable
`name@sha256:…`. A CI/CD variable overrides all three.

---

## 🔐 Security notes

Three things are worth knowing before you wire this into a pipeline that holds
credentials.

**Reports can contain the secrets they found.** Two settings turn an artifact
into a disclosure: `betterleaks_redact: "0"` writes detected secrets in
cleartext, and adding `secret` to `trivy_scanners` puts Trivy's findings in the
report. Artifacts are downloadable by everyone with read access to the project,
so leave redaction at its default unless the artifact destination is as
restricted as the secrets themselves.

**Floating tags are mutable by design.** Each release force-moves `v1` and
`v1.0`, so pinning either means code you have not reviewed runs in your
pipeline after the next release. `v1.0.0` is never moved, but a GitHub tag can
in principle be rewritten by anyone with push access; a remote include pinned
to a commit SHA is the only fully immutable reference:

```yaml
include:
  - remote: "https://raw.githubusercontent.com/Tooark/template-security-scanner/<commit-sha>/templates/full-scan.yml"
```

**A remote include is fetched when the pipeline is created.** If
`raw.githubusercontent.com` is unreachable at that moment, the pipeline is not
created at all. An instance that cannot depend on that should publish the
templates to its own CI/CD Catalog through the mirror project.

### What was checked

`eval` appears in the templates, but only ever iterates a hardcoded list of
variable names — no input reaches it. Inputs arrive in the job script as
environment variables, never spliced into it as text, and
`scripts/validate-templates.py` fails CI on a template that does. Word splitting of
`extra_args` is deliberate and runs under `set -f`, so a value like `*` cannot
expand against repository files. `tests/templates.test.py` asserts all of this
on every commit, and the script blocks of the templates are linted with
ShellCheck. The validation scripts use `yaml.safe_load`. Workflow tokens are
scoped: `contents: read` for CI, `contents: write` only for the release job.
The third-party `actionlint` image is pinned by digest, and Dependabot tracks
the rest.

---

## 🔖 Versioning

Releases are tagged `vMAJOR.MINOR.PATCH`. Each release also moves two floating
tags so consumers can track a line without editing pipelines on every patch:

| Reference | Resolves to                    | Use when                           |
| --------- | ------------------------------ | ---------------------------------- |
| `v1.0.0`  | Exactly that release           | Reproducible pipelines             |
| `v1.0`    | Newest patch of 1.0            | Automatic patch updates            |
| `v1`      | Newest release of the 1.x line | Automatic minor and patch updates  |
| `main`    | Unreleased work                | Never in a pipeline you care about |

A catalog component takes the bare version instead — `@1.0.0`, `@1.0`, `@1` —
because that is how the catalog names releases.

[`VERSION`](VERSION) is the single source of truth for both the component
version and the scanner image tag that every template pins.
`scripts/check-sync.sh` fails CI if any of them drift, and the release workflow
refuses a tag that disagrees with `COMPONENT_VERSION`.

Bumping the scanner image is therefore a three-line change: edit `VERSION`,
run `./scripts/check-sync.sh`, update the pins it flags.

---

## 📦 Publishing

### GitHub Releases

Push a `v*.*.*` tag. [`.github/workflows/release.yml`](https://github.com/Tooark/template-security-scanner/blob/main/.github/workflows/release.yml)
runs the checks, compares the tag against `VERSION`, creates the release with
generated notes and moves the floating tags. A remote include can use the tag
as soon as it exists.

### GitLab CI/CD Catalog

The catalog only lists components hosted on the GitLab instance itself, so a
GitHub repository cannot be published to it directly. Set up the mirror project
described in [`catalog-mirror/`](https://github.com/Tooark/template-security-scanner/tree/main/catalog-mirror):
it polls the releases here on a schedule, copies `templates/` across when the
version moves, and publishes to the catalog of your instance.

---

## 🚧 Gotchas

**The entrypoint override is required.** The image entrypoint execs `ark-tools`
directly, and GitLab Runner keeps the image entrypoint and attaches a shell to
it. Every template sets `entrypoint: [""]`; removing it in an override breaks
the job before the script runs.

**`GIT_DEPTH: "0"` matters for secret scanning.** Betterleaks walks the git
history. With GitLab's default shallow clone it silently sees almost nothing.
The templates set `git_depth: "0"`; lower it only when the history is too large
to clone and you accept scanning less.

**The stage must exist.** The default is `test`, which every pipeline has
unless it declares `stages:` without it. A pipeline with its own stage list
must either include `test` or pass `stage`.

**Booleans and strings are not interchangeable.** `sbom: "true"` and
`no_git: true` are both rejected: the first is a boolean input given a string,
the second a string input given a boolean. See [Inputs](#-inputs).

**A private image needs credentials.** `image-scan` and the image step of
`full-scan` pull the image from the registry themselves. For the project's own
registry, pass the job credentials as shown in [Recipes](#-recipes).

**Dockerfile lint handles one file per job.** Use `full-scan` with
`dockerfiles: "a,b,c"`, or include `dockerfile-lint` once per file with
different `job_name` values.

**The empty `tags` default renders as `tags: []`.** GitLab has no way for an
input to omit a keyword, and an empty tag list is how you say "any runner".
Pipelines accept it; only GitLab's editor JSON schema rejects empty arrays
([gitlab#551088](https://gitlab.com/gitlab-org/gitlab/-/issues/551088)), and
that schema applies to `.gitlab-ci.yml` files, not to these templates.

---

## 📁 Repository layout

```text
templates/                  The component templates, one job each
examples/                   Ready-to-copy pipelines
catalog-mirror/             Mirror project that publishes to a CI/CD Catalog
scripts/                    Checks run in CI and locally
tests/                      Tests of the generated jobs, no GitLab needed
docs/                       Onboarding guide, published to GitHub Pages
SUPPORTED-INTEGRATIONS.md   GitLab versions, runners and executors supported
VERSION                     Single source of truth for versions
```

---

## 🧪 Development

```bash
python3 -m pip install pyyaml

python3 scripts/validate-templates.py   # structure, input wiring, dead inputs
./scripts/check-sync.sh                 # version pins, ARK_IN_* wiring, docs
python3 scripts/check-examples.py       # examples and README snippets match the templates
python3 tests/templates.test.py         # the job each template generates, without GitLab
shellcheck -s bash scripts/*.sh
```

CI runs all five, lints the script blocks of the templates with ShellCheck,
runs `actionlint`, and scans this repository with the sister GitHub Action.

When adding an input, touch all four places or the checks will say so: the
template's `spec:inputs`, its `variables:` block as `ARK_IN_*`, the job script
that reads it, and the tables in both READMEs.
[`CONTRIBUTING.md`](https://github.com/Tooark/template-security-scanner/blob/main/CONTRIBUTING.md)
has the details.

---

## 🔗 Related projects

| Project                                                                                  | What it is                                                      |
| ---------------------------------------------------------------------------------------- | --------------------------------------------------------------- |
| [`Tooark/action-security-scanner`](https://github.com/Tooark/action-security-scanner)    | The same scans as a GitHub Action                               |
| [`Tooark/base-images`](https://github.com/Tooark/base-images/tree/main/security-scanner) | The `security-scanner` image: the tools and the `ark-tools` CLI |

---

## 🤝 Contributing

Contributions are welcome! Start with
[CONTRIBUTING.md](https://github.com/Tooark/template-security-scanner/blob/main/CONTRIBUTING.md)
— it covers what belongs here and what belongs in the scanner image, the
development workflow, how to add an input, the commit convention and the
release process.

Quick notes:

- Run the five checks under [Development](#-development) before opening a PR
- A new input lands in four places, or the checks fail the build
- Keep `README.md` and `README.pt-BR.md` in sync
- Commits follow [Conventional Commits](https://www.conventionalcommits.org/)
- Record anything a consumer will notice in `CHANGELOG.md`, under `[Unreleased]`

By participating you agree to the [Code of Conduct](https://github.com/Tooark/template-security-scanner/blob/main/CODE_OF_CONDUCT.md).

---

## 🆘 Help and Security

- ❓ **Questions, bugs, feature ideas** — see [SUPPORT.md](https://github.com/Tooark/template-security-scanner/blob/main/SUPPORT.md) for the right channel
- 🔒 **Security vulnerabilities** — do **not** open a public issue; follow [SECURITY.md](https://github.com/Tooark/template-security-scanner/blob/main/SECURITY.md)
- 🐳 **A problem inside the scanner itself** — Trivy, Hadolint, Betterleaks and `ark-tools` live in [`Tooark/base-images`](https://github.com/Tooark/base-images/tree/main/security-scanner)

---

## 💖 Support

If these templates help your pipelines, consider supporting their development:

- 💙 [GitHub Sponsors](https://github.com/sponsors/paulosfjunior)
- ☕ [Ko-fi](https://ko-fi.com/paulosfjunior)

Every contribution helps keep the project maintained and improving. Thank you! 🙏

---

## 📝 License

This project is licensed under the [MIT License](LICENSE).
