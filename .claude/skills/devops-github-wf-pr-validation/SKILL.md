---
name: devops-github-wf-pr-validation
description: Basic GitHub Actions workflow for PR validation — running unit tests
  and checking that the application version is bumped when code changes.
when_to_use: when you need to create or update `.github/workflows/pr.yml` (or a similar
  file) to validate pull requests into develop/master.
---

# Goal
- Create a minimal, clear workflow that runs unit tests on every pull request to `develop` or `master`.
- Verify that the application version is increased when a PR targets `master` and changes source code or the workflow itself.
- Protect the `develop` and `master` branches from unvalidated changes.

# Core Principle
- Every PR to `develop` or `master` must run unit tests.
- If a PR targets `master` and touches application code or CI, the project metadata version must be strictly greater than the version in the target branch.
- The AI agent **never** pushes directly to `master` or `develop`. Always create a separate branch and open a PR.
- If it is impossible to create a separate branch, the changes must not be pushed at all.
- If the project is a console application that can run on different operating systems, the workflow must test it on multiple OSs.

# Rule

## MUST
- Trigger the workflow on `pull_request` to `develop` and `master` (or `main` if that is the project's default branch).
- Provide a `test` job that installs dependencies and runs unit tests.
- Provide a `version-check` job that runs only when:
  - `github.base_ref == 'master'` (or `main`), and
  - source code (`src/**`, `*.py`, `*.cs`, etc.) or the workflow file (`.github/workflows/pr.yml`) has changed.
- Use a path filter, e.g. `dorny/paths-filter@v3`, to detect changed files.
- Compare versions semantically: `PR version > base version`. Plain string comparison is not enough.
- Use the correct version file for the stack:
  - Python — `pyproject.toml` (`project.version`),
  - .NET — `*.csproj` / `Directory.Build.props` / `version.json`,
  - Node.js — `package.json` (`version`),
  - for other stacks, ask the user where the version is stored.
- If the application is a cross-platform console app, use an OS matrix. At minimum include `ubuntu-latest` and `windows-latest`; add `macos-latest` if relevant.
- The AI agent must work in a separate branch and create a PR. Direct push to `develop`/`master` is forbidden. If a separate branch cannot be created, do not push the changes.

## SHOULD
- Cache dependencies (`actions/setup-python` with `cache: pip`, `actions/cache` for other ecosystems).
- Pin action versions to tags or SHAs; avoid unpinned `latest` references.
- Give jobs and steps clear, descriptive names.
- Use `fail-fast: false` in the matrix so every OS/version combination runs to completion.
- Enable Git long paths on Windows runners when the workflow clones repositories or installs packages from Git URLs:
  ```yaml
  - name: Enable Git long paths
    run: git config --global core.longpaths true
  ```
  This prevents checkout failures for paths longer than 260 characters or paths containing special characters such as curly braces.

## MAY
- Add extra jobs such as linting, type checking, or formatting checks.
- Publish a coverage report if the project already collects coverage.

## SHOULD NOT
- Hardcode secrets, tokens, or credentials in the workflow.
- Overload the workflow with build/publish artifact steps — those belong in other workflows.

## MUST NOT
- Push workflow or code directly to `develop` or `master` without a PR.
- Skip the version check for a `master` PR that changes code or the workflow.
- Require a version bump for PRs that only change documentation, tests, or non-publishable configuration.

# Anti-patterns
- **Pushing directly to `master` or `develop`**
  - Consequence: unvalidated changes enter the protected branch, breaking the stable version and bypassing review history.
  - Instead: always create a separate branch, let the workflow run, and open a PR.

- **Skipping the version check for a code-changing PR to `master`**
  - Consequence: releases are built with duplicate or stale versions, confusing the release process and artifacts.
  - Instead: add a `version-check` job that compares the PR version with the version in `origin/master`.

- **Not bumping the version when the CI workflow changes**
  - Consequence: a new validation logic, build environment, or test matrix is released under an existing version, making it impossible to trace which version introduced the CI behavior. Reproducing an old release may produce different results because the workflow changed silently.
  - Instead: include workflow file changes (`.github/workflows/pr.yml`) in the `version-check` job conditions so that any CI change targeting `master` also requires a version bump.

- **Testing cross-platform console apps on a single OS only**
  - Consequence: OS-specific bugs are only discovered by end users.
  - Instead: use an OS matrix for console applications.

- **Failing to enable long paths on Windows when cloning Git dependencies**
  - Consequence: `git clone` or `pip install` from a Git URL fails with errors like `cannot create directory ... Filename too long`, especially for paths containing curly braces or other special characters.
  - Instead: add `git config --global core.longpaths true` before the clone or install step on Windows runners.

- **Comparing versions as strings**
  - Consequence: `"10.0.0"` is considered less than `"2.0.0"` with string comparison, leading to false positives or missed errors.
  - Instead: use semantic version comparison (`packaging.Version` in Python, `System.Version` in .NET, `semver` in Node.js, etc.).

- **Requiring a version bump for every PR, including `develop` PRs and documentation changes**
  - Consequence: unnecessary version bumps, noisy history, and slower development.
  - Instead: check the version only for PRs to `master`/`main` and only when code or the workflow has changed.

# Example

See [Python PR workflow example](.claude/skills/devops-github-wf-pr-validation/templates/python-pr.example.md) for a Python project using `pyproject.toml`.

# Check list
- [ ] Workflow triggers on PR to `develop` and `master` (or `main`).
- [ ] The `test` job runs unit tests and uses an OS matrix for cross-platform console apps.
- [ ] The `version-check` job runs only for PRs to `master`/`main` when code or the workflow changed.
- [ ] Versions are compared semantically and must strictly increase.
- [ ] The AI agent created a separate branch and PR; no direct push to `develop`/`master`.
- [ ] The workflow contains no secrets, tokens, or deployment steps.
- [ ] For non-Python stacks, the version file and reading method are adapted accordingly.
- [ ] Windows jobs that clone Git repositories or install packages from Git URLs enable `core.longpaths`.

## Metadata

```yaml
tags:
- devops
- github-actions
- ci
- pr-validation
- testing
```
