# Retire

Runs monthly, whenever `AGENTS.md` passes 60 lines, and when the main AI model changes.
Every removal is an ordinary T1 or T2 change, and the owner approves each process removal.

## Product
Features, code paths, dependencies, whole repos: mark deprecated, remove callers,
delete, archive the repo if empty.

Feature flags: label each one a ramp or a kill switch. Remove a ramp flag, and the code path
it turned off, once its rollout reaches 100%. Keep kill switches on purpose, and list them in
the Kill switches table of `.adlc/retire-log.md`, not in the removal table.

## Process
CLAUDE.md or AGENTS.md rules, skills, hooks, CI checks, tests, evals, proof suites.
Each has a row in `.adlc/retire-log.md` with:

- **Cost:** run time per change, review findings it causes, lines of instructions.
- **Value:** real defects it caught in the last 90 days. For a skill, how often it was used
  in that time. Claude Code can log skill use with a PreToolUse hook; other tools use the
  owner's estimate.

Propose removal when it caught no defect in 90 days (a skill: it was not used in 90 days),
or its cost is plainly higher than its value. A rule worth keeping but written as prose becomes a test,
lint rule or hook, and the prose is deleted.

A check that broke and could not run in those 90 days has no value data, not zero value.
Fix it, then judge it. A check that ran rarely because few changes touched its paths is
judged as usual.

## Review tuning
Monthly only. The retire run rates last month's review findings as useful or not, from the PR history.
It then proposes `REVIEW.md` edits: what to skip, and examples of Important findings for this repo.
The Important definition and the five-nit cap stay as [review-budget.md](review-budget.md) sets them.
These edits are tuning, not process removals, so the tech lead approves them.
Generated paths and anything CI enforces stay on the skip list.

## After a model change
Read `AGENTS.md`, the skills and `REVIEW.md` for rules written around an older model's faults:
forced step-by-step rituals, "think carefully" lines, verify-twice rules, retry workarounds.
Also look for instructions that contradict each other. Propose removing each one. CI still
enforces the rules that matter. The evidence so far is for Claude models only.
