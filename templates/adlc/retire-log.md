# Retire log

Reviewed monthly, when AGENTS.md passes 60 lines, and when the main AI model changes.
Propose removal when an item caught no real defect in 90 days (a skill: it was not used
in 90 days), or its cost is plainly higher than its value.

| Item | Kind | Added | Cost (run time, findings caused, lines) | Value, last 90 days (defects caught; uses for a skill) | Last reviewed | Decision |
| --- | --- | --- | --- | --- | --- | --- |

## Kill switches

Feature flags kept on purpose. Not proposed for removal.

| Flag | What it turns off | Owner | Last reviewed |
| --- | --- | --- | --- |

## Candidates from repeated review findings

| Finding | Times seen | Proposed check (test, lint rule, hook) | Owner decision |
| --- | --- | --- | --- |
