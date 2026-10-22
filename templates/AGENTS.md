# <Repo name>

This repo follows the ADLC: https://github.com/anandfrancis93/ADLC
Keep this file under 60 lines. Facts only; process lives in the ADLC skills, hooks and CI.
Never edit the files the ADLC manages (`docs/sync.md` there lists them). CI fails if they change.
Write all prose for people (PRs, commits, reviews, docs, replies) by the `adlc-writing` skill.

## Commands
- Install (exact, from the lockfile): see `.adlc/install`
- Fast check (pre-commit, staged files): see `.adlc/fast-check`
- Full test suite (CI only): <command>

## Releases
- Ships versioned releases: <yes, version in <file> | no>
- DESIGN.md: <yes | no>

## Risk tiers
Path-to-tier map: `.adlc/tiers`. Protected paths: `.adlc/protected`.

## Facts an agent would get wrong
<!-- Gotchas the file tree does not show. Skip what an agent can see by reading the repo. -->
- <fact>
