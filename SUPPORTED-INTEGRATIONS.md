# Supported integrations

What these templates are tested and supported on, and where the boundaries are.

Anything not listed here may still work — it is simply not something a bug
report can be held against. When in doubt, open an issue with the environment
filled in; the `bug` template asks for exactly the fields this page indexes.

🌍 Companion pages: [README.md](README.md) · [SUPPORT.md](SUPPORT.md) ·
[CONTRIBUTING.md](CONTRIBUTING.md)

---

## Platforms

| Platform                               | How it is consumed                                                                                                       | Status            |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ----------------- |
| **GitLab CI — remote include**         | `include: - remote: "https://raw.githubusercontent.com/Tooark/template-ci-security-scanner/v1.3.0/templates/<scan>.yml"` | ✅ Supported      |
| **GitLab CI — CI/CD Catalog**          | `include: - component: $CI_SERVER_FQDN/tooark/ci-security-scanner/<scan>@1.3.0`                                          | ✅ Supported      |
| **GitLab CI — local copy**             | The files of `templates/` vendored into a project, `include: - local:`                                                   | ⚠️ Best effort    |
| **GitHub Actions**                     | [`Tooark/action-security-scanner`](https://github.com/Tooark/action-security-scanner)                                    | ➡️ Sister project |
| Jenkins, Azure DevOps, CircleCI, Drone | —                                                                                                                        | ❌ Not covered    |

The templates are a packaging layer. On an unsupported CI system you can still
run the underlying image directly — that is
[`Tooark/base-images`](https://github.com/Tooark/base-images/tree/main/security-scanner)
territory, not this repository's.

The CI/CD Catalog only lists components hosted on the GitLab instance itself, so
that route requires the mirror project in [`catalog-mirror/`](catalog-mirror/).

---

## GitLab versions

| Use                                   | Minimum          | Why                                                                                  |
| ------------------------------------- | ---------------- | ------------------------------------------------------------------------------------ |
| Remote include                        | **GitLab 16.11** | Array-typed inputs (`rules`, `tags`), and boolean values under `variables:`          |
| CI/CD Catalog component               | **GitLab 17.0**  | The release in which components and the catalog became generally available           |
| Publishing with the mirror as shipped | **GitLab 18.0**  | Its `release` job runs `glab`; on an older instance switch that job to `release-cli` |

Both gitlab.com and self-managed instances are supported, on any tier: nothing
here depends on a paid feature.

---

## Runners and executors

| Requirement              | Supported                                                        |
| ------------------------ | ---------------------------------------------------------------- |
| Operating system         | **Linux only**                                                   |
| Executor                 | `docker`, `docker+machine` or `kubernetes`                       |
| Architecture             | Whatever the scanner image is published for: `amd64` and `arm64` |
| `shell` / `ssh` executor | ❌ Not supported                                                 |
| Windows / macOS runners  | ❌ Not supported                                                 |

**Why the executor matters.** The templates run the job _inside_ the scanner
image and clear its entrypoint (`entrypoint: [""]`). An executor that ignores
the `image:` keyword — `shell`, `ssh` — will run the script on the runner host,
where `ark-tools` does not exist.

---

## Scans

One template per scan, each generating one job.

| Template              | Tool        |
| --------------------- | ----------- |
| `full-scan.yml`       | all three   |
| `image-scan.yml`      | Trivy       |
| `filesystem-scan.yml` | Trivy       |
| `config-scan.yml`     | Trivy       |
| `repo-scan.yml`       | Trivy       |
| `dockerfile-lint.yml` | Hadolint    |
| `secret-scan.yml`     | Betterleaks |

### Scan-specific requirements

| Scan                                            | Requires                                                                                                                                     |
| ----------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `secret-scan`, and `full-scan` secrets          | Full git history — `GIT_DEPTH: "0"`, which the templates set through `git_depth`                                                             |
| `image-scan`, and the image step of `full-scan` | The image in a registry the job can reach, plus `TRIVY_USERNAME` / `TRIVY_PASSWORD` when it is private — the project's own registry included |
| `dockerfile-lint`                               | One Dockerfile per job — use `full-scan` with `dockerfiles:` for several                                                                     |
| Any Trivy scan                                  | Network reach to the vulnerability database, or a `trivy_server`                                                                             |

A shallow clone is the trap worth repeating: Betterleaks walks the history, and
with a shallow clone it sees almost nothing **and does not complain**.

---

## Versions

| Component version   | Scanner image                          | Status     |
| ------------------- | -------------------------------------- | ---------- |
| `1.3.x`             | `ghcr.io/tooark/security-scanner:1.10` | Current    |
| `1.2.x`             | `ghcr.io/tooark/security-scanner:1.10` | Superseded |
| `1.0.x` and `1.1.x` | `ghcr.io/tooark/security-scanner:1.9`  | Superseded |

[`VERSION`](VERSION) is the single source of truth for this pairing, and
`scripts/check-sync.sh` fails CI when any template drifts from it. Overriding
`scanner_version` to a tag this table does not list is allowed and occasionally
useful, but it is unsupported: the inputs are written against the variables a
specific image reads.

Releases up to `1.2.x` were cut together with the GitHub Action, from a
repository then called `Tooark/ci-security-scanner` and now
[`Tooark/action-security-scanner`](https://github.com/Tooark/action-security-scanner).
This repository continues from the same history and carries the same tags, so
`v1.1.0` and `v1.2.0` resolve here too.

### Reference tags

| Reference | Resolves to                    | Mutable            |
| --------- | ------------------------------ | ------------------ |
| `v1.0.0`  | Exactly that release           | No                 |
| `v1.0`    | Newest patch of 1.0            | Yes                |
| `v1`      | Newest release of the 1.x line | Yes                |
| `main`    | Unreleased work                | Yes — never pin it |

A catalog component takes the bare version: `@1.0.0`, `@1.0`, `@1`.

---

## Network

| Destination                     | Needed for                             | Avoidable with                                              |
| ------------------------------- | -------------------------------------- | ----------------------------------------------------------- |
| `ghcr.io`                       | Pulling the scanner image              | A mirror, via `scanner_image`                               |
| Trivy vulnerability database    | Every Trivy scan                       | `trivy_server`, or `TRIVY_SKIP_DB_UPDATE` with a warm cache |
| `raw.githubusercontent.com`     | A remote include, at pipeline creation | The CI/CD Catalog mirror                                    |
| `api.github.com` · `github.com` | The catalog mirror's scheduled sync    | —                                                           |

Fully air-gapped instances are not a supported configuration today. The pieces
exist — a mirrored image, a Trivy server, the catalog mirror instead of a
remote include — but the combination is untested.

---

## Reports and formats

Report formats, SBOM formats and the consolidated `ark-report-tools` envelope
are produced by the image, not by these templates. The templates forward the
format inputs, tell the image the name and tag it ran under, which fill the
envelope's `image` object, and keep whatever lands in the reports directory as
job artifacts.

The authoritative list of supported values for `trivy_format`,
`hadolint_format`, `betterleaks_format` and `sbom_format` is the `options:`
block of each input in [`templates/`](templates/), which mirrors the
[image README](https://github.com/Tooark/base-images/blob/main/security-scanner/README.md).

The templates keep the reports as plain artifacts and do not declare
`artifacts:reports`, so the findings do not feed GitLab's own security widgets.

---

## Not supported

- Windows and macOS runners
- GitLab `shell` and `ssh` executors
- GitLab versions older than 16.11
- CI systems other than GitLab CI — GitHub Actions has its
  [own project](https://github.com/Tooark/action-security-scanner)
- Fully air-gapped installations
- Scanner image tags outside the pairing table above
- `main` as a pinned reference
