# Plan: separate intent, spec and plan files

Date: 2026-10-23. Spec: [spec.md](spec.md).

## Files that change
- `templates/intent/intent.md`, `templates/intent/spec.md`, `templates/intent/plan.md` (new; `templates/spec.md` moves)
- `templates/REVIEW.md`
- `skills/adlc-plan/SKILL.md`, `skills/adlc-spec/SKILL.md`, `skills/adlc-review/SKILL.md`, `skills/adlc-retire/SKILL.md`
- `docs/stages.md`, `docs/risk-tiers.md`, `docs/retire.md`
- `AGENTS.md`

## Order of work
1. Commit `intent.md`, then `spec.md`, then this plan.
2. Move `templates/spec.md` to `templates/intent/spec.md` and drop its Intent section.
   Add `templates/intent/intent.md` and `templates/intent/plan.md`.
3. Add a Roles section to `docs/stages.md`, and point stages 1 to 3 at the new files.
4. Update the T3 column in `docs/risk-tiers.md`.
5. Update `adlc-plan` (T3 intent and plan) and `adlc-spec` (T3 spec).
6. Name the owner and the files to check in `templates/REVIEW.md`.
   Add the same spec and plan check to `adlc-review`.
7. Add monthly review tuning to `docs/retire.md` and `adlc-retire`.
8. Add `intent/` to the layout in `AGENTS.md`.
9. Run `python3 scripts/adlc.py manifest --write` and `bash tests/run.sh`.

## Risks
- Repos that already have `REVIEW.md` keep the old compliance line. The `adlc-review` skill
  carries the spec and plan check, so reviews still read the files.
- No CI check enforces the hand-off order, so it holds only as far as the skills are followed.

## Proof
`bash tests/run.sh` passes. `grep -rn "docs/specs" docs skills templates` shows only lines saying
that old specs stay where they are.

Update this file in the same commit when the work departs from it.
