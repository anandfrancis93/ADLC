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
[docs/review-budget.md](docs/review-budget.md), [docs/retire.md](docs/retire.md).
Sources and what each contributed: [docs/sources.md](docs/sources.md).

## Adopt it in a repo

1. Copy `templates/AGENTS.md` to the repo root and fill in its facts. Keep it under 60 lines.
2. Copy `templates/adlc/` to `.adlc/` and edit `tiers` (path-to-tier map) and `config`.
3. Copy `templates/git-hooks/pre-commit` to `.githooks/pre-commit` and run
   `git config core.hooksPath .githooks`. There is no pre-push hook.
4. Copy `templates/github/workflows/adlc.yml` to `.github/workflows/`, and
   `templates/REVIEW.md` and `templates/pull_request_template.md` to the repo root and `.github/`.
5. Copy `scripts/` to `.adlc/scripts/` (the hook and workflow call them there).
6. Skills: Claude Code users install the plugin (below). For other tools, copy
   `skills/*` into that tool's skills directory.

## Claude Code plugin

This repo is also a Claude Code plugin marketplace:

```
/plugin marketplace add anandfrancis93/ADLC
/plugin install adlc@adlc
```

The plugin adds the skills, a reviewer subagent that follows the review budget,
and a hook that blocks edits to paths listed in `.adlc/protected`.
