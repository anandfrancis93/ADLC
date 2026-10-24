# Changelog

## [0.7.0] - 2026-10-24

_To upgrade a repo, do what the Breaking line asks in its sync PR, then merge it. A T3 PR that is open when the sync PR merges needs one draft toggle after the approval (`docs/sync.md`)._

### Changed

- **Breaking:** start each new T3 change as `intent/YYYY-MM-DD-<slug>/intent.md` in its own PR, then `spec.md` in its own PR, then `plan.md` as the first commit of the code PR; `templates/intent/` holds the three templates and replaces `templates/spec.md`; in the sync PR, update the maintainer line and the Compliance lines of your `REVIEW.md` from `templates/REVIEW.md`, because sync never changes an existing `REVIEW.md`; old specs in `docs/specs/` stay where they are ([`9190b6d`](https://github.com/anandfrancis93/ADLC/commit/9190b6d)) ([#3](https://github.com/anandfrancis93/ADLC/pull/3))
- Check a T3 change against its `spec.md` and `plan.md` in the `adlc-review` skill, and flag a departure from the plan ([`9190b6d`](https://github.com/anandfrancis93/ADLC/commit/9190b6d)) ([#3](https://github.com/anandfrancis93/ADLC/pull/3))
- Say in `docs/sync.md` that the ADLC repo is public, so any repo can call its workflows with no Access setting ([`004249f`](https://github.com/anandfrancis93/ADLC/commit/004249f)) ([#2](https://github.com/anandfrancis93/ADLC/pull/2))

### Added

- Name the roles in `docs/stages.md`: product owner, tech lead, engineer and owner; the tech lead accepts each T3 plan and maintains `REVIEW.md` ([`9190b6d`](https://github.com/anandfrancis93/ADLC/commit/9190b6d)) ([#3](https://github.com/anandfrancis93/ADLC/pull/3))
- Rate last month's review findings in the monthly retire run, and propose `REVIEW.md` edits for the tech lead to approve ([`9190b6d`](https://github.com/anandfrancis93/ADLC/commit/9190b6d)) ([#3](https://github.com/anandfrancis93/ADLC/pull/3))

### Fixed

- Let a T3 PR merge once the owner approves, with no re-run by hand: a re-run keeps a label added after the push, and the new `rerun-t3-approval` job re-runs the failed approval checks of the earlier runs; the `adlc.yml` caller grants `actions: read` for the drop step, and the `adlc-review.yml` caller grants `actions: write`, which only `rerun-t3-approval` uses; the one exception is a T3 PR open across the sync ([`3ec3948`](https://github.com/anandfrancis93/ADLC/commit/3ec3948)) ([#6](https://github.com/anandfrancis93/ADLC/pull/6))
- Count the `adlc:t3-approved` label only when it came after the newest force push ([`3ec3948`](https://github.com/anandfrancis93/ADLC/commit/3ec3948)) ([#6](https://github.com/anandfrancis93/ADLC/pull/6))

## [0.6.0] - 2026-10-22

_To upgrade a repo, merge its sync PR. In a repo with branch protection, change the required checks first, as the Breaking line says. The sync PR waits on the old checks until then._

### Changed

- **Breaking:** run the ADLC's PR checks in two jobs, `t3-approval` and `checks`, because GitHub bills each job as at least one minute; in branch protection, remove `drift`, `fast-check`, `secrets`, `protected` and `full-test`, and require `checks` ([`bb9de4e`](https://github.com/anandfrancis93/ADLC/commit/bb9de4e)) ([#16](https://github.com/anandfrancis93/ADLC/pull/16))
- Check out the full history for `full-test`, so a test suite can read the base branch ([`bb9de4e`](https://github.com/anandfrancis93/ADLC/commit/bb9de4e)) ([#16](https://github.com/anandfrancis93/ADLC/pull/16))
- Show a failed DESIGN.md lint as a warning in `checks`; it never blocks a merge ([`bb9de4e`](https://github.com/anandfrancis93/ADLC/commit/bb9de4e)) ([#16](https://github.com/anandfrancis93/ADLC/pull/16))

### Fixed

- Fail the tier and fast-check steps when `git diff` fails, instead of rating the PR T1 or checking no files ([`bb9de4e`](https://github.com/anandfrancis93/ADLC/commit/bb9de4e)) ([#16](https://github.com/anandfrancis93/ADLC/pull/16))
- Give the `checks` job, which runs the PR's own code, a read-only token ([`bb9de4e`](https://github.com/anandfrancis93/ADLC/commit/bb9de4e)) ([#16](https://github.com/anandfrancis93/ADLC/pull/16))

## [0.5.0] - 2026-10-22

_From this release on, each release opens a sync PR in each repo behind it; set up `ADLC_SYNC_TOKEN` first (`docs/sync.md`)._

### Added

- Open a sync PR in each repo behind a release when its tag arrives (`adlc.py sync-repos`, secret `ADLC_SYNC_TOKEN`) ([`fb42fa2`](https://github.com/anandfrancis93/ADLC/commit/fb42fa2)) ([#14](https://github.com/anandfrancis93/ADLC/pull/14))
- Accept the owner's `adlc:t3-approved` label, added after the latest commit, as the T3 approval (`adlc.py t3-approved`), because GitHub does not let a PR's author approve it ([`fb42fa2`](https://github.com/anandfrancis93/ADLC/commit/fb42fa2)) ([#14](https://github.com/anandfrancis93/ADLC/pull/14))

### Fixed

- Fail `t3-approval` when the `tier` job fails, instead of skipping it, which GitHub counts as passed ([`fb42fa2`](https://github.com/anandfrancis93/ADLC/commit/fb42fa2)) ([#14](https://github.com/anandfrancis93/ADLC/pull/14))

## [0.4.0] - 2026-10-22

_To upgrade a repo, sync it from v0.4.0 as `docs/sync.md` describes._

### Changed

- **Breaking:** run the ADLC's CI as shared workflows that each repo calls at a release tag, so the required check names change after the first sync ([`757b855`](https://github.com/anandfrancis93/ADLC/commit/757b855)) ([#12](https://github.com/anandfrancis93/ADLC/pull/12))
- **Breaking:** add a required `drift` check that fails a PR when a file the ADLC manages differs from the pinned release ([`757b855`](https://github.com/anandfrancis93/ADLC/commit/757b855)) ([#12](https://github.com/anandfrancis93/ADLC/pull/12))
- **Breaking:** run review events in their own caller, `adlc-review.yml`, so a job skipped on a review no longer turns a failed required check green ([`757b855`](https://github.com/anandfrancis93/ADLC/commit/757b855)) ([#12](https://github.com/anandfrancis93/ADLC/pull/12))
- **Breaking:** ignore the ADLC's own workflows in Dependabot; ADLC releases reach repos as sync PRs ([`757b855`](https://github.com/anandfrancis93/ADLC/commit/757b855)) ([#12](https://github.com/anandfrancis93/ADLC/pull/12))

### Added

- Add `adlc.py sync`, which writes the ADLC's files into a repo from a release tag and records the version in `.adlc/version` ([`757b855`](https://github.com/anandfrancis93/ADLC/commit/757b855)) ([#12](https://github.com/anandfrancis93/ADLC/pull/12))
- Add `docs/sync.md`: adopt and update repos, start new ones, and check for repos behind each release ([`757b855`](https://github.com/anandfrancis93/ADLC/commit/757b855)) ([#12](https://github.com/anandfrancis93/ADLC/pull/12))

## [0.3.0] - 2026-10-22

### Changed

- **Breaking:** scan staged changes for secrets with Betterleaks v1.9.0 in the pre-commit hook, which fails when Betterleaks is not installed ([`61eb03d`](https://github.com/anandfrancis93/ADLC/commit/61eb03d)) ([#5](https://github.com/anandfrancis93/ADLC/pull/5))
- **Breaking:** run `.adlc/install` before the CI `fast-check` and `full-test` jobs, so each repo needs that file from the template ([`61eb03d`](https://github.com/anandfrancis93/ADLC/commit/61eb03d)) ([#5](https://github.com/anandfrancis93/ADLC/pull/5))
- **Breaking:** format staged files in the pre-commit `fast-check` and stage the result; a staged file that also has unstaged edits stops the commit ([`61eb03d`](https://github.com/anandfrancis93/ADLC/commit/61eb03d)) ([#5](https://github.com/anandfrancis93/ADLC/pull/5))
- **Breaking:** require one auto-fixing formatter per language, pinned to an exact version and checked in CI ([`61eb03d`](https://github.com/anandfrancis93/ADLC/commit/61eb03d)) ([#5](https://github.com/anandfrancis93/ADLC/pull/5))
- **Breaking:** require a committed version file per language (`.nvmrc`, `.python-version`) and installs exactly from the lockfile ([`61eb03d`](https://github.com/anandfrancis93/ADLC/commit/61eb03d)) ([#5](https://github.com/anandfrancis93/ADLC/pull/5))
- **Breaking:** require `.github/dependabot.yml` from the template, with weekly grouped updates tiered T1 for patch and minor and T2 for major ([`61eb03d`](https://github.com/anandfrancis93/ADLC/commit/61eb03d)) ([#5](https://github.com/anandfrancis93/ADLC/pull/5))
- **Breaking:** keep each T3 intent and spec, with a Decision section, in one file at `docs/specs/YYYY-MM-DD-<slug>.md` after merge ([`61eb03d`](https://github.com/anandfrancis93/ADLC/commit/61eb03d)) ([#5](https://github.com/anandfrancis93/ADLC/pull/5))
- **Breaking:** add `fast-check`, `secrets` and `protected` to the required checks ([`61eb03d`](https://github.com/anandfrancis93/ADLC/commit/61eb03d), [`d82d462`](https://github.com/anandfrancis93/ADLC/commit/d82d462)) ([#5](https://github.com/anandfrancis93/ADLC/pull/5), [#8](https://github.com/anandfrancis93/ADLC/pull/8))
- **Breaking:** label every feature flag a ramp or a kill switch, and remove each ramp flag once its rollout reaches 100% ([`526a90e`](https://github.com/anandfrancis93/ADLC/commit/526a90e)) ([#9](https://github.com/anandfrancis93/ADLC/pull/9))
- **Breaking:** give scheduled agents read-only tokens where they only read, let an agent that reads outside content only comment, and make a scheduled check that cannot run report a failure ([`526a90e`](https://github.com/anandfrancis93/ADLC/commit/526a90e)) ([#9](https://github.com/anandfrancis93/ADLC/pull/9))
- Protect a T3 failing test in the same commit that adds it, and remove a protected line only in the PR's last commit, which changes nothing else ([`d82d462`](https://github.com/anandfrancis93/ADLC/commit/d82d462)) ([#8](https://github.com/anandfrancis93/ADLC/pull/8))
- Run the agent review in a fresh session, and have each Important finding say how to show it fails ([`526a90e`](https://github.com/anandfrancis93/ADLC/commit/526a90e)) ([#9](https://github.com/anandfrancis93/ADLC/pull/9))
- Require a done-when line in every intent: the test, command or check that proves the work is done ([`526a90e`](https://github.com/anandfrancis93/ADLC/commit/526a90e)) ([#9](https://github.com/anandfrancis93/ADLC/pull/9))
- Count a check that did not start, or only checked syntax, as not run, and name each check not run in the PR ([`526a90e`](https://github.com/anandfrancis93/ADLC/commit/526a90e)) ([#9](https://github.com/anandfrancis93/ADLC/pull/9))
- Replace the Architecture section of the AGENTS.md template with gotchas the file tree does not show ([`526a90e`](https://github.com/anandfrancis93/ADLC/commit/526a90e)) ([#9](https://github.com/anandfrancis93/ADLC/pull/9))

### Added

- Add a CI `protected` job that enforces `.adlc/protected` on each commit of the PR branch, counting a merge as one commit ([`d82d462`](https://github.com/anandfrancis93/ADLC/commit/d82d462)) ([#8](https://github.com/anandfrancis93/ADLC/pull/8))
- Add a CI `secrets` job that scans the PR's commits with Betterleaks ([`61eb03d`](https://github.com/anandfrancis93/ADLC/commit/61eb03d)) ([#5](https://github.com/anandfrancis93/ADLC/pull/5))
- Add the `adlc-writing` skill for plain prose, and an optional Mermaid diagram in T3 specs ([`d773735`](https://github.com/anandfrancis93/ADLC/commit/d773735)) ([#7](https://github.com/anandfrancis93/ADLC/pull/7))
- Add skills and model changes to Retire: a skill is valued by use, and a model change triggers an audit of old workarounds ([`526a90e`](https://github.com/anandfrancis93/ADLC/commit/526a90e)) ([#9](https://github.com/anandfrancis93/ADLC/pull/9))
- Add a flaky-test proof by repeated runs on the base and the branch ([`526a90e`](https://github.com/anandfrancis93/ADLC/commit/526a90e)) ([#9](https://github.com/anandfrancis93/ADLC/pull/9))
- Add a Screenshots section to the PR template for user-visible changes ([`526a90e`](https://github.com/anandfrancis93/ADLC/commit/526a90e)) ([#9](https://github.com/anandfrancis93/ADLC/pull/9))
- Add a deploy watch to `adlc-release`: after a merge, watch the deploy run on main and tell the owner at once if it fails ([`648b0eb`](https://github.com/anandfrancis93/ADLC/commit/648b0eb)) ([#11](https://github.com/anandfrancis93/ADLC/pull/11))
- Post the agent review's summary on the PR as one review comment, so CI counts the round ([`648b0eb`](https://github.com/anandfrancis93/ADLC/commit/648b0eb)) ([#11](https://github.com/anandfrancis93/ADLC/pull/11))

### Fixed

- Compute the `tier` job's files with a three-dot diff, so changes on main since the branch point no longer raise the tier ([`61eb03d`](https://github.com/anandfrancis93/ADLC/commit/61eb03d)) ([#5](https://github.com/anandfrancis93/ADLC/pull/5))

## [0.2.0] - 2026-10-22

### Changed

- **Breaking:** require Conventional Commit PR titles and squash merges in every repo ([`782a15e`](https://github.com/anandfrancis93/ADLC/commit/782a15e)) ([#2](https://github.com/anandfrancis93/ADLC/pull/2))

### Added

- Add SemVer and Common Changelog rules for repos that ship releases, with the `adlc-version` skill and a tag-triggered release workflow; before 1.0.0 a breaking change bumps MINOR ([`782a15e`](https://github.com/anandfrancis93/ADLC/commit/782a15e), [`fa29b18`](https://github.com/anandfrancis93/ADLC/commit/fa29b18)) ([#2](https://github.com/anandfrancis93/ADLC/pull/2), [#4](https://github.com/anandfrancis93/ADLC/pull/4))
- Add `pr-title`, `changelog-draft` and `changelog-entry` commands to `scripts/adlc.py` ([`782a15e`](https://github.com/anandfrancis93/ADLC/commit/782a15e)) ([#2](https://github.com/anandfrancis93/ADLC/pull/2))
- Add optional `DESIGN.md` for repos with a UI, linted in CI with a pinned CLI ([`782a15e`](https://github.com/anandfrancis93/ADLC/commit/782a15e)) ([#2](https://github.com/anandfrancis93/ADLC/pull/2))

## [0.1.0] - 2026-10-21

_First release._

[0.7.0]: https://github.com/anandfrancis93/ADLC/releases/tag/v0.7.0
[0.6.0]: https://github.com/anandfrancis93/ADLC/releases/tag/v0.6.0
[0.5.0]: https://github.com/anandfrancis93/ADLC/releases/tag/v0.5.0
[0.4.0]: https://github.com/anandfrancis93/ADLC/releases/tag/v0.4.0
[0.3.0]: https://github.com/anandfrancis93/ADLC/releases/tag/v0.3.0
[0.2.0]: https://github.com/anandfrancis93/ADLC/releases/tag/v0.2.0
[0.1.0]: https://github.com/anandfrancis93/ADLC/releases/tag/v0.1.0
