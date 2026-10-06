# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.3.0] - 2026-10-05

This repository is now the home of the GitLab CI/CD templates, and of nothing
else. The GitHub Action stays in the repository the two used to share, renamed
[`Tooark/action-security-scanner`](https://github.com/Tooark/action-security-scanner).
**A remote include and a catalog mirror both have to point here** — see the
first entry under _Changed_.

### Added

- `examples/quick-start.gitlab-ci.yml`, the one-line include, and a recipe in
  the README and in `examples/remote-include.gitlab-ci.yml` for the case that
  trips most first pipelines: scanning an image in the project's own, private
  registry needs `TRIVY_USERNAME` and `TRIVY_PASSWORD` set from
  `CI_REGISTRY_USER` and `CI_REGISTRY_PASSWORD`.
- `tests/templates.test.py` runs the job each template generates, without
  GitLab and without the scanner image. It renders the template with a set of
  inputs, runs `before_script` and `script` against a stand-in `ark-tools`, and
  asserts on the command line and the environment that stand-in received:
  precedence, the arguments of each scan, `extra_args` splitting, the exit
  code. CI runs it on every commit, and also lints the script blocks of the
  templates with ShellCheck, which nothing did before.
- `scripts/check-examples.py` checks every include of these templates, in
  `examples/` and in the YAML blocks of the READMEs, the way GitLab would when
  creating the pipeline: an undeclared input, a value of the wrong type or
  outside `options`, or a missing required input fails CI here instead of in
  the project of whoever copied the example.
- `scripts/check-sync.sh` now also fails when an input is missing from either
  README, and when the `scanner_version` row of a README or the current line
  of `SUPPORTED-INTEGRATIONS.md` names an image tag other than the one in
  `VERSION`. `scripts/validate-templates.py` now fails when a template
  interpolates an input into `before_script`, `script` or `after_script`:
  inputs reaching the shell only as environment variables was a rule on paper,
  and is now a check.
- `SUPPORTED-INTEGRATIONS.md` states the minimum GitLab version: 16.11 for a
  remote include, because the templates use array-typed inputs and stage a
  boolean input under `variables:`; 17.0 for a CI/CD Catalog component.
- Contributing, Help and Security and Support sections at the end of both
  READMEs.

### Changed

- **The templates are released from this repository.** Up to 1.2.0 they were
  released together with the GitHub Action, from a repository then called
  `Tooark/ci-security-scanner`; this one continues them from the same history
  and the same tags. The templates themselves did not move inside the
  repository. What a consumer has to change:
  - a remote include now points at
    `https://raw.githubusercontent.com/Tooark/template-ci-security-scanner/<tag>/templates/<scan>.yml`.
    One that still names `Tooark/ci-security-scanner` resolves only for as
    long as GitHub redirects the old name, only for tags up to `v1.2.0`, and
    gets no further releases;
  - a catalog mirror must set `UPSTREAM_REPO` to
    `Tooark/template-ci-security-scanner`, in its `.gitlab-ci.yml` or as a
    project CI/CD variable. `catalog-mirror/README.md` has the steps. Component
    paths on your instance do not change.
- The catalog mirror moved from `examples/gitlab-catalog-mirror/` to
  `catalog-mirror/`, and the example pipelines from `examples/gitlab/` to
  `examples/`.
- The README is written for GitLab only: every input with its default and the
  templates that accept it, the report files each scan writes, the GitLab
  version and executors required, and recipes. Every section heading carries
  an icon, which changes the anchor of the section: it now starts with a
  hyphen, `#-inputs` where it was `#inputs`.
- `SUPPORTED-INTEGRATIONS.md`, `CONTRIBUTING.md`, `SECURITY.md`, `SUPPORT.md`
  and the issue and pull request templates describe the templates only, and
  send GitHub Actions questions to the sister repository.
- The onboarding guide covers the templates only, at its own address,
  <https://tooark.com/template-ci-security-scanner/>. It gained sections on how
  a project consumes a template, the anatomy of one, the path of a run and the
  catalog; it takes GitLab's orange as its accent colour; and it closes with a
  card pointing at the sibling guide of the GitHub Action.

### Removed

- The GitHub Action — `action.yml` and `src/run-scanner.sh` — and the GitHub
  example workflow. They live on in
  [`Tooark/action-security-scanner`](https://github.com/Tooark/action-security-scanner).

### Fixed

- `full-scan` no longer overrides `FULL_SCAN_DOCKERFILES` and `FULL_SCAN_MODE`
  set as CI/CD variables. The `dockerfiles` and `scan_mode` inputs defaulted to
  `"Dockerfile"` and `"fs"` — the image's own defaults — and a non-empty
  default is always forwarded, so a project that set either variable and left
  the input alone had it silently replaced. Both inputs now default to empty,
  like every other forwarding input, and `scan_mode` accepts `""`. A pipeline
  that sets neither the input nor the variable behaves exactly as before. **A
  project that does set `FULL_SCAN_DOCKERFILES` or `FULL_SCAN_MODE` as a
  variable will see it take effect for the first time.**
- The Trivy database cache is now saved when the job fails too. The five
  templates that cache it declared no `cache:when`, and GitLab's default saves
  a cache only on success — while these jobs fail by design whenever a gate
  trips. A project with findings therefore never populated the cache and
  downloaded the whole database on every run. The cache entry now sets
  `when: always`, the counterpart of the separate save step the GitHub Action
  has always had.

## [1.2.0] - 2026-09-27

### Added

- The onboarding guide is bilingual. A language button beside the theme button
  switches between Portuguese and English without reloading the page. Both
  languages live in the same file, side by side, so they cannot drift apart the
  way two separate files can; the choice is remembered per visitor, and a
  first-time visitor gets whichever language their browser asks for. Without
  JavaScript the page still renders, in Portuguese.
- The guide links out: a GitHub button beside the language and theme buttons
  and the repository badge open the repository, the version badge opens that
  version's release, and the scanner badge opens the `Tooark/base-images`
  release of the image it pins.

### Changed

- The onboarding guide no longer carries versions of its own. It writes
  placeholders, and `scripts/render-docs.sh` fills them in from `VERSION` —
  which now also declares `REPORT_SCHEMA` and `REPORT_VERSION` — before Pages
  publishes the page. Pages now also redeploys when only `VERSION` changes.
  `check-sync.sh` reads the rendered page, fails on a version typed into the
  guide by hand, and checks that every live mention of the report envelope
  names `REPORT_VERSION`.

- Scanner image bumped to `ghcr.io/tooark/security-scanner:1.10`, the new
  default of `scanner_version` / `scanner-version`. Its reports use the
  `ark-report-tools` envelope v1.3, which adds an optional `image` object —
  `name`, `version`, `tag`, `digest` and `reference` of the scanner image that
  produced the report — and sets `version` to `"1.3"`. A collector behind
  `report_url` / `report-url` that only accepts the literal `"1.2"` must be
  updated; reports without `image` still validate against the new schema.
  Released as a minor because the image moved a minor: the scanner default
  follows the image's own versioning (see `CONTRIBUTING.md`).
- Reports say which image produced them. The image knows only its own build
  version, so both front ends pass `ARK_IMAGE_NAME` and `ARK_IMAGE_TAG` from
  `scanner_image` / `scanner-image` and `scanner_version` / `scanner-version`:
  a mirror or the floating `1.10` tag is recorded as it ran, not as
  `ghcr.io/tooark/security-scanner:1.10.0`. The Action also resolves the
  digest of the image it runs and passes `ARK_IMAGE_DIGEST`, so
  `image.reference` becomes an immutable `name@sha256:…`. GitLab exposes no
  digest for a job image; a project that wants one sets `ARK_IMAGE_DIGEST` as
  a CI/CD variable. A CI/CD variable, or the job `env` on GitHub, overrides all
  three.

### Fixed

- The onboarding guide no longer serves `uses: Tooark/ci-security-scanner@v1.1.0`
  as `[email protected]`. Cloudflare proxies `tooark.com` and its Email Address
  Obfuscation rewrites anything shaped like an address; `name@vX.Y.Z` qualifies.
  The affected spans now carry Cloudflare's `email_off` opt-out.
- The `[1.0.0]` and `[1.1.0]` links at the bottom of this file pointed at a
  `v1.0.0` tag that was never pushed, so both 404'd.
- The guide's JavaScript moved out of the page and into `docs/guide.js`. The
  site is served behind a Content Security Policy of `script-src 'self'`, which
  blocks inline `<script>` outright — so the theme toggle, the language toggle
  and the nav highlight were all dead on the published page while working
  locally. The button labels moved into `data-` attributes on the buttons, so
  the script file now carries no translated text at all.
- The guide serves its own favicon. The link pointed at `../media/favicon.png`,
  which resolves above the published root — `docs/` is the site root — and only
  appeared to work because the organization's site happens to serve an
  identical file at that path. It also declared `image/x-icon` for a PNG.
- The Portuguese half of the guide had fallen behind the English one. It still
  showed `v1.0.0` in both tag tables, `actions/cache/restore@v4` and
  `actions/checkout@v4`, and it listed three `check-sync.sh` invariants where
  there are four. Both halves said the scanner version is pinned in ten places;
  it is nine, since `run-scanner.sh` has a single version fallback. On narrow
  phones the header buttons no longer overlap the eyebrow line.
- The catalog mirror's `sync` job could not push. GitLab Runner rewrites the
  bare project URL to one carrying `CI_JOB_TOKEN`
  (`url.<with token>.insteadOf <without>`), so the push went out with the
  read-only job token instead of `CATALOG_PUSH_TOKEN` and failed with
  `You are not allowed to push code to this project`. The push URL now carries
  a user part (`https://oauth2@…`), which that prefix match no longer rewrites,
  and every push resets `credential.helper` first, so a job-token helper the
  runner installs under `FF_GIT_URLS_WITHOUT_TOKENS` cannot answer instead.
- The mirror's push to the default branch carries `-o ci.skip`. Without it the
  push started a branch pipeline whose own `sync` job raced the tag push, and
  failed trying to create the same tag whenever it won.
- The README reaches the catalog mirror without `media/`, `docs/`, `examples/`,
  `action.yml` or the other language's README, so on the catalog page the
  banner and those links were broken. Links to files the mirror does not sync
  are now absolute; `templates/`, `LICENSE` and `VERSION` stay relative.
- The mirror's troubleshooting table blamed branch protection for the 403 that
  was really the runner's job token, and listed a missing description as a
  cause of an empty catalog, when it actually fails the release job with
  `Project must have a description`. It now covers both, and how to publish a
  release that was created while the **CI/CD Catalog project** toggle was off.

### Security

- The mirror pipeline pins its images by digest: `alpine:3.24.2` for `sync`,
  which holds `CATALOG_PUSH_TOKEN` (3.20 reached end of support on
  2026-04-01), and `glab` v1.119.0 for `release` instead of the mutable
  `latest`. The mirror's README notes that the `glab` path needs GitLab 18.0 or
  later.

## [1.1.0] - 2026-09-22

### Added

- Onboarding guide in `docs/`, deployed to GitHub Pages by
  `.github/workflows/pages.yml`. It walks the repository file by file and
  records the reasoning behind each decision, for readers who know software
  development but not CI.
- OSS governance files modelled on `Tooark/base-images`: `SECURITY.md`,
  `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SUPPORT.md`, `.github/CODEOWNERS`,
  `.github/FUNDING.yml`, a pull request template and issue forms.
- `SUPPORTED-INTEGRATIONS.md`, recording the support boundaries previously
  scattered across header comments and README gotchas: supported platforms,
  runners and executors, the component-to-image version pairing, and the
  network destinations a scan needs.
- `scripts/check-sync.sh` now also verifies that every copy-paste reference in
  the README, the examples, the onboarding guide and
  `SUPPORTED-INTEGRATIONS.md` pins `COMPONENT_VERSION`. Only the three forms a
  reader actually copies are matched; prose explaining the tagging scheme is
  not. Without it, a release silently left the quick start teaching the
  previous version.

### Changed

- **Minimum Actions Runner version on self-hosted runners.** `action.yml` now
  references `actions/upload-artifact@v7` and `actions/cache@v6`, which run on
  Node.js 24 and require Actions Runner **2.327.1 or newer** — the floor
  introduced by `actions/upload-artifact@v6`. GitHub-hosted runners are
  unaffected. A self-hosted runner older than that will fail the artifact
  upload and the cache steps once `v1` or `v1.0` moves to a release containing
  this change.
- This repository's own workflows moved to `actions/checkout@v7`,
  `actions/configure-pages@v6` and `actions/deploy-pages@v5`. No consumer
  impact; the runners had started warning that Node 20 is deprecated.
- The GitHub example in `examples/` moved to `actions/checkout@v7`, so a reader
  copying it does not start on a version the runner already warns about.

### Fixed

- `scripts/check-sync.sh` no longer trips ShellCheck `SC2013`, which failed the
  CI lint step on every commit and blocked every Dependabot pull request. The
  `ARK_IN_*` parity check now reads names with `while read` fed by process
  substitution, which keeps the loop in the current shell so the failure flag
  survives it.
- The onboarding guide is linked by its canonical address,
  `https://tooark.com/ci-security-scanner/`. The `tooark.github.io` URL used
  until now is a redirect: the organization serves Pages from a custom domain.

## [1.0.0] - 2026-09-21

First release. Pins `ghcr.io/tooark/security-scanner:1.9`. Never published as
a tag — this content first reached consumers as part of 1.1.0.

### Added

- GitLab CI/CD component templates, one job each: `full-scan`, `image-scan`,
  `filesystem-scan`, `config-scan`, `repo-scan`, `dockerfile-lint` and
  `secret-scan`. Usable through `include: remote:` or from a CI/CD Catalog.
- GitHub composite Action (`action.yml`) covering the same seven scans through
  a `command` input, with `exit-code`, `reports-dir` and `report` outputs.
- Shared precedence rule across both platforms: an empty input is never
  forwarded, so `input > CI variable > image default` holds everywhere.
- Secret passthrough (`TRIVY_TOKEN`, `REPORT_TOKEN`, registry credentials and
  friends) via environment rather than inputs.
- Trivy database caching on both platforms, skipped for the two scans that do
  not read the database. GitLab caches `.cache/trivy` under a fixed key; GitHub
  uses `actions/cache` with one entry per day per scanner version, saved from
  an explicit step so a tripped failure gate still populates it.
- `scripts/validate-templates.py` and `scripts/check-sync.sh`, which fail CI on
  undeclared or unused inputs, broken `ARK_IN_*` wiring, and version pins that
  drift from `VERSION`.
- Release workflow that validates, checks the tag against `VERSION`, publishes
  the GitHub release and moves the floating `vMAJOR` and `vMAJOR.MINOR` tags.
- Mirror pipeline in `examples/gitlab-catalog-mirror/` that polls GitHub
  releases on a schedule and republishes to a self-hosted CI/CD Catalog.
- Copy-ready examples for both platforms in `examples/`.

### Security

- `extra_args` is split under `set -f`, so a value such as `*` is passed
  literally instead of expanding against the files in the repository.
- The catalog mirror hands its push token to git through a credential helper
  rather than a remote URL, keeping it out of argv and out of git's errors.
- The third-party `actionlint` image is pinned by digest, and Dependabot keeps
  the remaining action references current.
- The reports directory is tightened again once a scan finishes, limiting the
  world-writable window the non-root container user requires.
- Documented the disclosure paths that configuration can open: the Docker
  socket mount, unredacted Betterleaks output, and Trivy's secret scanner
  writing findings into an uploaded artifact.

[Unreleased]: https://github.com/Tooark/template-ci-security-scanner/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/Tooark/template-ci-security-scanner/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/Tooark/template-ci-security-scanner/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/Tooark/template-ci-security-scanner/releases/tag/v1.1.0
[1.0.0]: https://github.com/Tooark/template-ci-security-scanner/commit/56263b1c4c085d5ce785ed263194c04609b8f0be
