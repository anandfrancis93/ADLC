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
   - T3: the Intent section of `docs/specs/YYYY-MM-DD-<slug>.md`, committed on the branch. Then use `adlc-spec`, and get the owner to accept the plan before building.
5. Before building T2 or T3, write a plan: files that change, order of work, tests that prove it.
