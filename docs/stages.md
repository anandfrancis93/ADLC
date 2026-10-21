# Stages

Each stage ends with an output in git or CI. Stage 1 sets a risk tier (T1, T2, T3),
and the tier decides how much of stages 2 to 6 a change goes through
([risk-tiers.md](risk-tiers.md)). Stage 7 feeds new intents back to stage 1.

## 1 Plan
- Write the intent: what is wanted, why, constraints, open questions.
- T1: one line in the PR. T2: an issue. T3: `intent.md`.
- Set the tier with `scripts/adlc-tier` on the planned files. A person may raise a tier, never lower it.

## 2 Design (T2, T3)
- `spec.md` lists the acceptance tests to add and the files in scope.
- Results are not written in the spec. Tests and CI produce them.

## 3 Build
- T2 and T3 start from an accepted plan (plan mode in Claude Code, or a written plan in any tool).
- The pre-commit hook formats, lints and type-checks staged files only.
- No pre-push hook.

## 4 Verify
- CI runs the full test suite once per change.
- T3: commit a failing test before the fix; the fix must not edit that test.
- T3: re-run only the proof records whose input hash changed. Full re-proof runs on a schedule.

## 5 Review
- One agent review per PR against `REVIEW.md`. See [review-budget.md](review-budget.md).

## 6 Release
- T1, T2: merge when CI and review pass.
- T3: the owner approves. Where the repo deploys, use a feature flag or staged rollout and a tested rollback.

## 7 Operate
- Monitors, scheduled scans and incidents open issues that start at stage 1.
- Each incident adds a regression test or eval.

## 8 Retire
- Monthly, and when `AGENTS.md` passes 60 lines. See [retire.md](retire.md).
