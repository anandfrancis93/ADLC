---
name: adlc-version
description: Cut a versioned release in an ADLC repo that ships releases (a plugin, package or app). Picks the SemVer version from Conventional Commit titles and writes the Common Changelog entry. Use when asked to release, tag or bump a version.
---
# ADLC Version

Only for repos that ship releases (see `docs/commits-and-releases.md` in the ADLC repo).

1. Find the last tag: `git describe --tags --abbrev=0` (none yet: the first release is 0.1.0 with notice `_First release._`).
2. Draft: `git log --format='%h%x1f%s%x1f%b%x1e' vX.Y.Z..HEAD | python3 .adlc/scripts/adlc.py changelog-draft --current X.Y.Z --repo OWNER/NAME`.
   Exit 3 means nothing user-facing changed: stop and say so.
3. Edit the draft for people, not machines: one line per change, imperative mood, merge related
   lines, drop lines a user would not notice, keep refactors. Check the left-out list in the comment.
4. Check the version: anything that makes existing users change their setup is breaking (MAJOR).
5. Add the entry under `# Changelog`, above the previous release, plus its link line at the bottom.
   Bump the version file (for example `.claude-plugin/plugin.json`, `package.json`, or
   `versionCode` and `versionName` in an Android `build.gradle`; `versionCode` must increase).
6. Open a PR titled `chore(release): X.Y.Z`. After the owner merges it, tag the merge commit
   `vX.Y.Z` and push the tag; the release workflow publishes the entry as release notes.
