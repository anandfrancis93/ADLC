# Intent: T3 approval passes after the owner approves, with no re-run

Author: Claude (engineer), for Anand (owner). Date: 2026-10-23. Tier: T3.

## Problem
The documented T3 merge is: the owner approves, `adlc / t3-approval` passes, and the PR merges.
The owner approves with the `adlc:t3-approved` label or an approving review of the head commit ([risk-tiers.md](../../docs/risk-tiers.md#t3-approval)).
The first run of `adlc.yml` on a T3 PR fails `t3-approval`, because the owner has not approved yet.
After the approval, GitHub keeps that red check, so the merge stays blocked.

On [portfolio PR #23](https://github.com/anandfrancis93/portfolio/pull/23), times in UTC:

1. Run 40014695943 (`ADLC`, started by a push) failed `t3-approval` at 19:51:40.
2. The owner's label went on at 19:59:36. Three label runs of `adlc / t3-approval` in `ADLC review` passed by 19:59:54.
3. Attempt 2 of run 40014695943 started at 19:59:47. Its step "Drop the T3 approval label after a new commit" ran again, because a re-run keeps the event `synchronize`. It removed the label at 19:59:53 and failed.
4. That removal also failed attempt 2 of run 40015403288 (`ADLC review`, a review event, no drop step) at 20:00:00.
5. The label went on again at 20:02:56. With every `ADLC review` run passed by 20:07, the merge API still answered 405, "Required status check "adlc / t3-approval" is failing".
6. The PR went to draft at 20:09:53 and back at 20:10:04. That started run 40017105804 of `ADLC`, which passed at 20:10:23. The PR merged at 20:15:04.

So GitHub appears to count the latest result in each workflow, not the latest result under the check name.
This is observed behavior. I don't know GitHub's documented rule.
It contradicts the comments in `adlc.yml` and `adlc-review.yml`, which say a label or review event "re-checks the approval under the same check name".
Each repo on the ADLC meets this on each T3 PR. Portfolio PR #22 needed manual re-runs too; they passed because its runs started on `opened`.

## Proposed outcome
- After the owner approves, the PR can merge when its other checks pass. No one re-runs a job or moves the PR to draft.
- A re-run never removes a label that the owner added after the head commit.

## Affected users and systems
- Each repo on the ADLC: the owner and the agents that merge T3 PRs.
- `.github/workflows/adlc.yml` and `adlc-review.yml`, and their callers in `templates/github/workflows/`.
- `docs/risk-tiers.md` and `tests/test_adlc.py`.

## Constraints
- `t3-approval` passes on a T3 PR only with the owner's label or approving review of the head commit, whichever workflow runs it.
- A label added before the head commit, or by another account, never passes `t3-approval`.
- A label or review event never skips or replaces the result of the `checks` job.
- A repo gets each ADLC change only through a release and its sync PR.
- The caller workflows get no write permission that the outcome does not need.

## Open questions
- How the owner's approval replaces the red check of the earlier `ADLC` run: CI re-runs that job, or another way. The spec decides.

## Done when
- `bash tests/run.sh` passes, with new tests that fail on `main` today. They pin two things:
  the drop step does not run on a re-run, and the owner's approval clears the red check of the earlier `ADLC` run.
- On a T3 PR in a repo on the new release, after a push:
  1. Before any approval, `gh pr merge` is refused. A label from another account does not change that.
  2. The owner adds the label, and the PR then merges with no re-run and no draft toggle.
  3. A re-run of the earlier `ADLC` run keeps the label and passes.
- The approving-review path is checked the same way on a PR opened by another account, if the repo has one.
