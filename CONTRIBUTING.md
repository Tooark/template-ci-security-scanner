# Contributing to template-security-scanner

First off, thank you for considering contributing to
**Tooark template-security-scanner**! 🎉

This repository publishes one thing: the GitLab CI/CD templates that run the
Tooark `security-scanner` image. What they promise a consumer is that every
documented input does what the documentation says — which is the constraint
that shapes almost every rule below.

The same scans ship for GitHub Actions from a sister repository,
[`Tooark/action-security-scanner`](https://github.com/Tooark/action-security-scanner).
The two share input names on purpose, so a change to an input here is usually
worth an issue there.

If you are new to CI pipelines, read the
[onboarding guide](https://tooark.com/template-security-scanner/) first — it
explains what each file does and why.

## Table of contents

- [Ways to contribute](#ways-to-contribute)
- [What belongs here and what does not](#what-belongs-here-and-what-does-not)
- [Repository layout](#repository-layout)
- [Development workflow](#development-workflow)
- [Adding or renaming an input](#adding-or-renaming-an-input)
- [Versioning](#versioning)
- [Commit convention](#commit-convention)
- [Documentation standards](#documentation-standards)
- [Releasing](#releasing)
- [Pull Request checklist](#pull-request-checklist)
- [Community](#community)

---

## Ways to contribute

- 🐛 **Report bugs** — open an issue with the `bug` template.
- ✨ **Suggest improvements** — open an issue with the `feature` template.
- 📖 **Improve documentation** — the READMEs (English and Portuguese) and the
  onboarding guide in `docs/` are first-class.
- 🔒 **Review security** — question a default, or a place where a value could
  reach a shell.
- 💻 **Write code** — templates, examples, the catalog mirror, validation.

---

## What belongs here and what does not

These templates **forward configuration**; they do not implement scanning.
Trivy, Hadolint, Betterleaks and the `ark-tools` CLI live in the image, built
from [`Tooark/base-images`](https://github.com/Tooark/base-images/tree/main/security-scanner).

| Change                                                   | Repository                |
| -------------------------------------------------------- | ------------------------- |
| A new input that forwards a variable the image reads     | here                      |
| A job fails before `ark-tools` starts                    | here                      |
| The cache, the artifacts, the rules of the generated job | here                      |
| The catalog mirror does not sync or publish              | here                      |
| A tool needs a flag the image does not expose            | `base-images`             |
| The report format or the consolidated envelope           | `base-images`             |
| Anything about the GitHub Action                         | `action-security-scanner` |

Before proposing a new input, check that it cannot already be done by
redeclaring the generated job or setting the matching CI/CD variable — a
generated job is an ordinary job, and every variable reaches the tools because
the job runs inside the image.

---

## Repository layout

```text
templates/          The component templates, one job each
examples/           Ready-to-copy pipelines
catalog-mirror/     Mirror project that publishes to a CI/CD Catalog
scripts/            Checks run in CI and locally
tests/              Tests of the generated jobs, no GitLab needed
docs/               Onboarding guide, published to GitHub Pages
VERSION             Single source of truth for versions
```

---

## Development workflow

```bash
python3 -m pip install pyyaml

python3 scripts/validate-templates.py   # structure, input wiring, dead inputs
./scripts/check-sync.sh                 # version pins, ARK_IN_* wiring, docs
python3 scripts/check-examples.py       # examples and README snippets match the templates
python3 tests/templates.test.py         # the job each template generates, without GitLab
shellcheck -s bash scripts/*.sh
```

Run all five before opening a PR. CI runs them, lints the script blocks of the
templates with ShellCheck, runs `actionlint`, and scans this repository with
the sister GitHub Action.

**Install `shellcheck` locally.** It fails on `info`-level findings, and it is
the easiest of the five to discover only after CI has turned red. To lint the
shell inside the templates the way CI does:

```bash
python3 tests/templates.test.py --dump /tmp/job-scripts
shellcheck -s sh /tmp/job-scripts/*.sh
```

All of this exists because GitLab reports a broken template only when a
pipeline is created — which happens in a _consuming_ project, not here. So the
repository answers the same questions ahead of time:

- `validate-templates.py` — does every `$[[ inputs.x ]]` resolve, is every
  declared input used, and is none of them spliced into a script block?
- `check-examples.py` — would GitLab accept the inputs each documented include
  passes? Unknown input, wrong type, value outside `options`: all caught.
- `tests/templates.test.py` — does the generated job do the right thing? It
  renders a template with a set of inputs, runs its `before_script` and
  `script` with a stand-in `ark-tools` on the `PATH`, and asserts on the
  command line and environment that stand-in received. A change to precedence
  or to an argument gets its case there.

`scripts/component.py` is the piece the last two share: it reads a template and
applies the documented rules of `spec:inputs` and of `$[[ ]]` interpolation.

---

## Adding or renaming an input

An input lives in **four places**. Miss one and the checks fail the build —
which is the point, because the failure mode they replace is silent: the input
exists in the documentation, the user sets it, and nothing happens.

1. The template's `spec:inputs` — with a `description`, plus `options` or
   `regex` where the value is constrained. This block is the authoritative
   reference for users.
2. The template's `variables:` block, staged as `ARK_IN_<NAME>`.
3. The job script — either passed to `ark_apply_inputs`, which exports it as
   `<NAME>` when it is non-empty, or read directly to build the command line.
4. The input tables of `README.md` and `README.pt-BR.md`.

Three rules that are not negotiable:

**Names match the image and the GitHub Action.** An input that forwards an
image variable takes its name in `snake_case`: `TRIVY_SEVERITY` is
`trivy_severity` here and `trivy-severity` in the Action. Someone moving
between the two platforms should have nothing to relearn.

**An empty input is never forwarded, and a forwarding input defaults to
empty.** That is what makes `input > CI/CD variable > image default` hold.
Forwarding an empty value would overwrite, with an empty string, a variable the
project set globally; and a default that merely repeats the image default
(`"fs"`, `"Dockerfile"`) overrides that variable just the same.

**Inputs never reach a shell as text.** They arrive as environment variables. A
`$[[ inputs.x ]]` spliced into a `script:` line is a command injection waiting
for the right input, and `validate-templates.py` refuses it.

---

## Versioning

The project follows [Semantic Versioning](https://semver.org/).

[`VERSION`](VERSION) is the single source of truth for the component version,
the scanner image tag that every template pins, and the report envelope that
image writes:

```text
COMPONENT_VERSION=1.3.1
SCANNER_IMAGE=ghcr.io/tooark/security-scanner
SCANNER_VERSION=1.10
REPORT_SCHEMA=ark-report-tools
REPORT_VERSION=1.3
```

Bumping the scanner image is a three-step change: edit `VERSION` (and
`REPORT_VERSION` when the new image writes a new envelope), run
`./scripts/check-sync.sh`, update the pins and mentions it flags. Never edit a
pin directly. The onboarding guide needs no edit: it has no version of its own
to update.

What counts as breaking here is anything that changes what runs inside a
consumer's pipeline: a removed or renamed input, a changed default, a job that
is renamed, or a new minimum GitLab version. Record it in `CHANGELOG.md` — the
consumer cannot see the diff, only the tag.

The scanner image default is the exception: it follows the image's own
versioning. A minor or patch bump of the image ships in a minor or patch
release here, a major one in a major release. What the image changes with it —
the report envelope, a tool version — is the image's to version; the
changelog entry still names anything a consumer has to act on, such as a
collector that must accept a new envelope version.

---

## Commit convention

We use [**Conventional Commits**](https://www.conventionalcommits.org/).

Format:

```text
<type>(<scope>): <short summary>
```

Common types: `feat`, `fix`, `docs`, `refactor`, `build`, `ci`, `chore`.

Use the area as the scope when it applies:

```text
feat(templates): add trivy_ignorefile to the Trivy scans
fix(full-scan): keep FULL_SCAN_MODE when scan_mode is blank
fix(mirror): push the catalog mirror with its own token
chore(version): bump the scanner image to 1.10
```

---

## Documentation standards

- The repository ships a **bilingual README**: `README.md` in English and
  `README.pt-BR.md` in Portuguese, with the language selector at the top.
  **Keep both in sync** — a change in one requires the same change in the
  other.
- Every input is documented in the template's `spec:inputs` block, and has a
  row in the README tables. `check-sync.sh` fails when a README misses one.
- The README is also the page of the CI/CD Catalog: the mirror syncs it
  together with `templates/`, `LICENSE` and `VERSION`, and nothing else. Links
  to any other file must be absolute, or they break there.
- Every YAML block in the READMEs that includes a template is checked against
  it by `check-examples.py`, exactly like the files in `examples/`. Write
  snippets that parse on their own.
- `docs/` holds the onboarding guide, published to GitHub Pages. It explains
  _why_ a decision was made; the README explains _how_ to use the templates.
  Resist adding a third place that says the same thing — there is no
  `check-sync.sh` for prose.
- The guide never types a version. It writes `{{COMPONENT_VERSION}}`,
  `{{SCANNER_VERSION}}` and the other `VERSION` keys, and
  `scripts/render-docs.sh` fills them in before Pages publishes it; the header
  of that script lists the derived ones, such as `{{COMPONENT_MINOR}}`.
  `check-sync.sh` fails on a version typed by hand. To preview the page, run
  `./scripts/render-docs.sh` and open `_site/index.html` — `docs/index.html`
  itself shows the raw placeholders.
- Comments in the templates record the reason a line exists, not what it does.
  Several of them are the only surviving record of a bug that took a while to
  find.

---

## Releasing

Releases are cut from tags:

1. Update `COMPONENT_VERSION` in `VERSION`.
2. Move the `[Unreleased]` entries in `CHANGELOG.md` under the new version.
3. Tag `vMAJOR.MINOR.PATCH` and push it.

[`.github/workflows/release.yml`](.github/workflows/release.yml) runs the
checks, **refuses a tag that disagrees with `COMPONENT_VERSION`**, creates the
release with generated notes, and force-moves the floating `vMAJOR` and
`vMAJOR.MINOR` tags.

A remote include can use the new tag immediately. The GitLab CI/CD Catalog only
lists components hosted on the GitLab instance itself, so each instance picks
the release up through its own mirror project, described in
[`catalog-mirror/`](catalog-mirror/): the `sync` job there notices the new
release on its next scheduled run.

---

## Pull Request checklist

The [PR template](.github/PULL_REQUEST_TEMPLATE.md) carries the full list. The
short version:

- [ ] The five local validations pass
- [ ] A new input landed in all four places
- [ ] `README.md` and `README.pt-BR.md` are in sync
- [ ] `CHANGELOG.md` has an `[Unreleased]` entry
- [ ] Consumer-visible changes are called out explicitly

---

## Community

- 💬 Questions and support: [`SUPPORT.md`](SUPPORT.md)
- 🔒 Security reports: [`SECURITY.md`](SECURITY.md) — never a public issue
- 🤝 Expected behaviour: [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md)
