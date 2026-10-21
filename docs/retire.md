# Retire

Runs monthly, and whenever `AGENTS.md` passes 60 lines. Every removal is an
ordinary T1 or T2 change, and the owner approves each process removal.

## Product
Features, code paths, dependencies, whole repos: mark deprecated, remove callers,
delete, archive the repo if empty.

## Process
CLAUDE.md or AGENTS.md rules, hooks, CI checks, tests, evals, proof suites.
Each has a row in `.adlc/retire-log.md` with:

- **Cost:** run time per change, review findings it causes, lines of instructions.
- **Value:** real defects it caught in the last 90 days.

Propose removal when it caught no defect in 90 days, or its cost is plainly
higher than its value. A rule worth keeping but written as prose becomes a test,
lint rule or hook, and the prose is deleted.
