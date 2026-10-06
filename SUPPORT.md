# Support

Thanks for your interest in **Tooark template-security-scanner**! 💙

This document explains where to get help based on what you're trying to do.

---

## 🤔 I have a question

**Read the onboarding guide first:** <https://tooark.com/template-security-scanner/>

It walks the repository file by file — what each artifact does, how an input
travels from the include to the scanner, and the reasoning behind the
decisions that look odd on a first read.

Still stuck? **Open an issue:**
<https://github.com/Tooark/template-security-scanner/issues/new/choose>

Please **search existing issues** first. The authoritative reference for any
input is the `spec:inputs` block of the matching template in
[`templates/`](templates/); ready-made pipelines live in
[`examples/`](examples/).

Using GitHub Actions? Questions about the Action go to
[`Tooark/action-security-scanner`](https://github.com/Tooark/action-security-scanner/issues/new/choose).

---

## 🐛 I found a bug

**Open an issue using the "Bug report" template:**
<https://github.com/Tooark/template-security-scanner/issues/new/choose>

Please include:

- **How you consume it** (remote include or CI/CD Catalog component).
- **Which template** (`full-scan`, `secret-scan`, …).
- **The component version** you pinned (e.g. `v1.0.0`) and the **scanner image
  tag**.
- **The GitLab version and the runner executor** — self-hosted runners behave
  differently for image scanning and caching.
- **The include**, with its inputs, and any override of the generated job.
- **Relevant logs** — redact credentials, tokens and any detected secret.

---

## 🐳 The problem is inside the scanner itself

Trivy, Hadolint, Betterleaks and the `ark-tools` CLI are **not** in this
repository. They ship in the `security-scanner` image, built from
[`Tooark/base-images`](https://github.com/Tooark/base-images/tree/main/security-scanner).

Rule of thumb:

| Symptom                                                     | Where it belongs                                                               |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------ |
| An input is ignored, mis-named, or rejected by GitLab       | here                                                                           |
| The job fails before `ark-tools` runs                       | here                                                                           |
| The catalog mirror does not sync or does not publish        | here                                                                           |
| A scan finds the wrong thing, or a tool flag is unsupported | `base-images`                                                                  |
| The report format or the consolidated envelope is wrong     | `base-images`                                                                  |
| The report's `image` object names the wrong image           | here                                                                           |
| Anything in a GitHub workflow                               | [`action-security-scanner`](https://github.com/Tooark/action-security-scanner) |

---

## ✨ I have an improvement idea

**Open an issue using the "Feature request" template:**
<https://github.com/Tooark/template-security-scanner/issues/new/choose>

Explain the **problem** you are trying to solve, not just the solution. Note
that a generated GitLab job is an ordinary job — much of what people ask for
can already be done by redeclaring the job or setting the matching environment
variable.

---

## 🔒 I found a security vulnerability

**Do NOT open a public issue.** Use one of these private channels:

- **Preferred**: [GitHub Security Advisories](https://github.com/Tooark/template-security-scanner/security/advisories/new)
- **Email**: `security@tooark.com` _(PGP key available on request)_

Full policy and response targets are in [`SECURITY.md`](SECURITY.md).

---

## 📚 I want to read the docs

| Audience                 | Start here                                                                          |
| ------------------------ | ----------------------------------------------------------------------------------- |
| **New to CI pipelines**  | [Onboarding guide](https://tooark.com/template-security-scanner/)                |
| **Users**                | [README.md](README.md) · [README.pt-BR.md](README.pt-BR.md)                         |
| **Every input**          | The `spec:inputs` block of each file in [`templates/`](templates/)                  |
| **Support boundaries**   | [SUPPORTED-INTEGRATIONS.md](SUPPORTED-INTEGRATIONS.md)                              |
| **Pipeline examples**    | [examples/](examples/)                                                              |
| **Contributors**         | [CONTRIBUTING.md](CONTRIBUTING.md)                                                  |
| **Catalog publishing**   | [catalog-mirror/](catalog-mirror/)                                                  |
| **GitHub Actions users** | [Tooark/action-security-scanner](https://github.com/Tooark/action-security-scanner) |
