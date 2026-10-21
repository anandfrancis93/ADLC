---
name: adlc-retire
description: Run the monthly ADLC retire review. Proposes removing code, and rules, hooks, CI checks, tests or proof suites that cost more than they give. Use monthly, when AGENTS.md passes 60 lines, or when asked to retire something.
---
# ADLC Retire

1. Count lines in `AGENTS.md`. Over 60: list each line that is process rather than a repo fact.
2. For each row in `.adlc/retire-log.md`, and each hook, CI job and test suite not yet in it:
   - Cost: run time per change, review findings it causes, lines of instructions.
   - Value: real defects it caught in the last 90 days (from CI history, PR history, git log).
3. Propose removal for each item with no caught defect in 90 days, or cost plainly above value.
4. For prose rules worth keeping, propose the test, lint rule or hook that replaces them.
5. Review the "Candidates from repeated review findings" table the same way.
6. Open one PR per removal (T1 or T2). The owner approves each process removal.
   Update `Last reviewed` and `Decision` in the log.

Product retirement (features, dependencies, repos): mark deprecated, remove callers, delete, archive if empty.
