# Intent: T3 approval passes after the label, with no re-run

Author: Claude (engineer), for Anand (owner). Date: 2026-10-23. Tier: T3.

## Problem
The documented T3 merge is: the owner adds `adlc:t3-approved`, `adlc / t3-approval` passes, and the PR merges.
On a T3 PR, the run of `adlc.yml` that a push or the PR's opening starts fails `t3-approval`, because the label is not on yet.
GitHub keeps that red check after the label goes on, so the merge stays blocked.
On [portfolio PR #23](https://github.com/anandfrancis93/portfolio/pull/23), three label runs of `adlc / t3-approval` passed.
The merge API still answered 405, "Required status check "adlc / t3-approval" is failing".
A re-run of the red job cannot clear it when a push started the run:

1. The re-run keeps the event of the first attempt, `synchronize`.
2. So the step "Drop the T3 approval label after a new commit" runs again and removes the owner's label.
3. The approval step then fails, because the last change to the label is that removal.

Run 40014695943 of portfolio did this at attempts 2 and 3.
The PR merged only after it went to draft and back to ready, which started a new run of `adlc.yml`.
Each repo on the ADLC has this problem on each T3 PR, and portfolio PR #22 needed manual re-runs too.

## Proposed outcome
- After the owner adds the label, the PR can merge when its other checks pass. No one re-runs a job or moves the PR to draft.
- A re-run never removes a label that the owner added after the head commit.

## Affected users and systems
- Each repo on the ADLC: the owner and the agents that merge T3 PRs.
- `.github/workflows/adlc.yml` and `adlc-review.yml`, and their callers in `templates/github/workflows/`.
- `docs/risk-tiers.md` and `tests/test_adlc.py`.

## Constraints
- A label added before the head commit never passes `t3-approval`.
- A label event never skips or replaces the result of the `checks` job.
- A repo gets each ADLC change only through a release and its sync PR.
- The caller workflows get no write permission that the outcome does not need.

## Open questions
- How the label event replaces the red check of the earlier run: CI re-runs that job, or another way. The spec decides.

## Done when
- `bash tests/run.sh` passes, with a new test that fails on `main` today.
- On a T3 PR in a repo on the new release, the owner adds the label after a push.
  The PR then merges with no re-run and no draft toggle.
