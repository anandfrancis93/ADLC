---
name: adlc-retire
description: Run the monthly ADLC retire review. Proposes removing code, flags, and rules, skills, hooks, CI checks, tests or proof suites that cost more than they give. Use monthly, when AGENTS.md passes 60 lines, when the main AI model changes, or when asked to retire something.
---
# ADLC Retire

1. Count lines in `AGENTS.md`. Over 60: list each line that is process rather than a repo fact.
2. For each row in the first table of `.adlc/retire-log.md`, and each skill, hook, CI job and test suite not yet in it:
   - Cost: run time per change, review findings it causes, lines of instructions.
   - Value: real defects it caught in the last 90 days (from CI history, PR history, git log).
     For a skill: how often it was used in that time.
3. Propose removal for each item with no caught defect in 90 days (a skill: no use in 90 days),
   or cost plainly above value. A check that broke and could not run is not "no defect". Fix it first.
4. For prose rules worth keeping, propose the test, lint rule or hook that replaces them.
5. Review the "Candidates from repeated review findings" table the same way.
6. After a model change: read `AGENTS.md`, the skills and `REVIEW.md` for rituals written for an
   older model, and for instructions that contradict each other. Propose removing them.
7. Open one PR per removal (T1 or T2). The owner approves each process removal.
   Update `Last reviewed` and `Decision` in the log.

Product retirement (features, dependencies, repos): mark deprecated, remove callers, delete, archive if empty.
Feature flags: remove each ramp flag whose rollout is at 100%, with the code path it turned off.
Keep kill switches, listed in the log's Kill switches table.
