# Intent: separate intent, spec and plan files

Author: Anand (owner). Date: 2026-10-23. Tier: T3.

## Problem
A T3 change keeps its intent and spec in one file, `docs/specs/YYYY-MM-DD-<slug>.md`.
No plan is saved, yet `REVIEW.md` asks the reviewer to check the change against its plan.
The [AI-native SDLC playbook](https://claude.com/resources/articles/the-ai-native-sdlc-playbook)
commits `intent.md`, `spec.md` and `plan.md` as separate files.
Each one is accepted at its own hand-off, and its commit starts the next stage.
The ADLC must assume every role exists, even when one person does all the work.

## Proposed outcome
Each T3 change gets one folder, `intent/YYYY-MM-DD-<slug>/`, with `intent.md`, `spec.md` and `plan.md`.
Each file is accepted at its own hand-off, in that order.
`REVIEW.md` names its owner, gets tuned monthly, and names the files to check a change against.

## Affected users and systems
- Every repo on the ADLC.
- The `adlc-plan`, `adlc-spec`, `adlc-review` and `adlc-retire` skills.
- `docs/stages.md`, `docs/risk-tiers.md`, `docs/retire.md` and the templates.

## Constraints
- The files stay Markdown, so any AI tool can read them and GitHub renders them in PRs.
- T1 and T2 keep their light path.
- Existing files in `docs/specs/` stay where they are.
- `REVIEW.md` is repo-owned, so sync does not update it in repos that already have one.

## Open questions
- No CI check enforces the hand-off order or the plan acceptance yet.

## Done when
`bash tests/run.sh` passes, and `grep -rn "docs/specs" docs skills templates` shows only lines
saying that old specs stay where they are.
