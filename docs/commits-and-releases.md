# Commits, versions and changelogs

## Commits: every repo

- PR titles follow [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/):
  `<type>[(scope)][!]: <description>`, for example `fix(api): reject empty names`.
- Types: `feat`, `fix`, `build`, `chore`, `ci`, `docs`, `perf`, `refactor`, `revert`, `style`, `test`.
  The spec defines `feat` and `fix` and allows others; the rest are the commitlint
  config-conventional types the spec cites.
- `!` before the colon, or a `BREAKING CHANGE:` footer, marks a breaking change.
- Write the description in the imperative mood ("add", "fix", "drop"), so it can go into a
  changelog with little rewording.
- PRs are squash-merged, so the PR title becomes the one commit on the main branch. CI checks
  only the PR title (`adlc-pr-title.yml`); commits inside a PR are not checked.
- Repo settings: allow squash merging only, with the PR title as the commit title:

  ```
  gh api -X PATCH repos/OWNER/NAME -F allow_squash_merge=true -F allow_merge_commit=false \
    -F allow_rebase_merge=false -f squash_merge_commit_title=PR_TITLE -f squash_merge_commit_message=PR_BODY
  ```

## Versions: only repos that ship releases

A repo ships releases when something outside the repo installs or depends on a version of it:
the ADLC plugin, a package, a mobile app. A website that deploys from main has no version.

- Use [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html): `MAJOR.MINOR.PATCH`.
  Breaking change: MAJOR. New feature: MINOR. Fix only: PATCH.
  Before 1.0.0, a breaking change bumps MINOR instead (SemVer item 4: anything may change in 0.y.z).
- Declare the public API in the README. For the ADLC, the public API is its rules, scripts,
  templates and skills, so a rule change that makes a compliant repo non-compliant is breaking.
- Start at `0.1.0`. A released version is never changed; fix it in a new version.
- Tag each release `vX.Y.Z` on the main branch. The version is `X.Y.Z`; `v` is only in the tag.
- Android apps: `versionCode` must increase with every upload (Google Play rejects a used one).
  `versionName` is the string users see; SemVer there is optional.
  Source: [Version your app](https://developer.android.com/studio/publish/versioning).

## Changelogs: only where SemVer applies

- `CHANGELOG.md` in [Common Changelog](https://common-changelog.org/) format. Template:
  `templates/CHANGELOG.md`.
- Written once per release, at release time, in a release PR. Never edited in feature PRs
  (Common Changelog has no Unreleased section).
- Each release: `## [X.Y.Z] - YYYY-MM-DD`, latest version first; groups in the order Changed,
  Added, Removed, Fixed; one line per change in the imperative mood, with a commit link and
  the PR link; breaking changes first, prefixed `**Breaking:**`. There are no Deprecated or
  Security groups; list a deprecation under Changed.
- Leave out maintenance noise (CI, dotfiles, dev dependencies, formatting) but keep
  refactors, runtime support changes and new documentation.

Common Changelog calls Conventional Commits an antipattern (section 4.2), because commit
prefixes are written for machines. The ADLC uses both: the prefix gives CI and the version
bump a type to read, and the release step rewrites each entry for people, as Common Changelog
asks. The `adlc-version` skill does this.

## Release steps

1. `git log --format='%h%x1f%s%x1f%b%x1e' vX.Y.Z..HEAD | python3 .adlc/scripts/adlc.py changelog-draft --current X.Y.Z --repo OWNER/NAME`
   prints the next version and a draft entry. Exit 3 means nothing user-facing changed.
2. Edit the draft: merge related lines, reword for users, check the version is right.
3. Open a PR titled `chore(release): X.Y.Z` that adds the entry and bumps the version file.
4. After it merges, tag the merge commit `vX.Y.Z` and push the tag. `adlc-release.yml` creates
   the GitHub release from the entry and fails if the entry is missing.
