---
name: adlc-plan
description: Start any change in a repo that follows the ADLC (has .adlc/tiers). Writes the intent and sets the risk tier T1, T2 or T3 before code is written. Use when beginning a feature, fix, refactor or removal.
---
# ADLC Plan

1. State the intent in the owner's words: what, why, constraints, open questions, and done when:
   the test, command or check that proves the work is done.
2. List the files the change will touch, then run:
   `printf '%s\n' <files> | python3 .adlc/scripts/adlc.py tier --explain`
3. The printed tier is the minimum. Raise it if the change is riskier than its paths suggest; never lower it.
4. Write the intent where the tier says:
   - T1: one line for the PR description that ends with done when. Go straight to building.
   - T2: an issue, or the PR description, with the intent. Then use `adlc-spec`.
   - T3: `intent/YYYY-MM-DD-<slug>/intent.md` (template: `templates/intent/intent.md` in the ADLC repo).
     Open it as its own PR. The product owner accepts it by merging. Then use `adlc-spec`.
5. Before building T2 or T3, write a plan: files that change, order of work, risks, tests that prove it.
6. T3 plan: commit it as `plan.md` in the change folder (template: `templates/intent/plan.md`).
   - Make it the first commit of the code PR, and open that PR as a draft.
   - The tech lead accepts the plan in a PR comment. Push no code before that.
   - When the work departs from the plan, update `plan.md` in the same commit.
