# ADLC

The development lifecycle that every one of Anand's repos follows. It works with
any AI coding tool (Claude, ChatGPT/Codex, Gemini and others) because the rules
are enforced by git hooks and CI, and the instructions use open formats:
[AGENTS.md](https://agents.md/) and [Agent Skills](https://agentskills.io/).
Claude Code users also get an optional plugin.

## The eight stages

| # | Stage | Output |
| --- | --- | --- |
| 1 | Plan | Intent and risk tier |
| 2 | Design | Spec as a list of tests to add (T2, T3) |
| 3 | Build | Commits from an accepted plan; fast hooks only |
| 4 | Verify | Full suite once in CI; proof for T3 |
| 5 | Review | One review; only Important blocks; 2 rounds, then the owner decides |
| 6 | Release | Merge; owner approval for T3 |
| 7 | Operate | Monitors and schedules open new intents |
| 8 | Retire | Removes code, and rules or checks that cost more than they give |

Details: [docs/stages.md](docs/stages.md), [docs/risk-tiers.md](docs/risk-tiers.md),
[docs/review-budget.md](docs/review-budget.md), [docs/retire.md](docs/retire.md),
[docs/commits-and-releases.md](docs/commits-and-releases.md) (Conventional Commits, SemVer,
Common Changelog), [docs/design-md.md](docs/design-md.md) (optional, repos with a UI),
[docs/formatting.md](docs/formatting.md), [docs/secrets.md](docs/secrets.md),
[docs/toolchain.md](docs/toolchain.md) (version files, lockfiles, Dependabot),
[docs/sync.md](docs/sync.md) (keeping repos on the latest release).
Sources and what each contributed: [docs/sources.md](docs/sources.md).

## Adopt it in a repo

1. Run `scripts/adlc.py sync` from a release tag of this repo ([how](docs/sync.md)).
   It writes the files the ADLC manages and adds templates for the files the repo owns.
2. Fill in `AGENTS.md` (under 60 lines) and `.adlc/tiers`, `install`, `fast-check` and `full-test`.
   Keep one entry per ecosystem in `.github/dependabot.yml`.
3. Commit a version file per language and the lockfile ([toolchain](docs/toolchain.md)).
   Install Betterleaks v1.9.0 ([how](docs/secrets.md)). There is no pre-push hook.
4. Set the repo settings once: squash-only merging ([how](docs/commits-and-releases.md#commits-every-repo)),
   the `ADLC_OWNER` and `ADLC_REVIEWERS` variables, and the required checks named in the `adlc.yml`
   and `adlc-pr-title.yml` callers.
5. Skills: Claude Code users install the plugin (below). For other tools, copy
   `skills/*` into that tool's skills directory.

CI fails a PR that edits a file the ADLC manages. Updates arrive as sync PRs ([sync](docs/sync.md)).

## Versions

The ADLC follows [SemVer](https://semver.org/spec/v2.0.0.html). Its public API is the rules in
`docs/`, the `scripts/adlc.py` commands, the files in `templates/`, the shared workflows in
`.github/workflows/adlc*.yml`, and the skills. A change
that makes a compliant repo non-compliant is a new major version. Before 1.0.0 it is a new
minor version instead, because SemVer lets anything change while the major version is 0. Changes are listed in
[CHANGELOG.md](CHANGELOG.md) ([Common Changelog](https://common-changelog.org/) format).

## Claude Code plugin

This repo is also a Claude Code plugin marketplace:

```
/plugin marketplace add anandfrancis93/ADLC
/plugin install adlc@adlc
```

The plugin adds the skills, a reviewer subagent that follows the review budget,
and a hook that blocks edits to paths listed in `.adlc/protected` as they happen.
CI enforces the same list for every tool.
