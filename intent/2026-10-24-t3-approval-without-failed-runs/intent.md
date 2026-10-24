# Intent: T3 approval waits for the owner without a failed run

Author: Claude (engineer), for Anand (owner). Date: 2026-10-24. Tier: T3.

## Problem
Each run of `adlc / t3-approval` on a T3 PR fails until the owner approves. The failed run is how the gate blocks the merge.
GitHub sends a notification to the user who triggered a run, and the user can choose to get one only for failed runs
([GitHub docs](https://docs.github.com/en/actions/concepts/workflows-and-actions/notifications-for-workflow-runs)).
Agents push and review from the owner's account, so the owner triggers each of these runs, and gets an email for each one.

The owner's Gmail, 2026-10-23 07:40 to 2026-10-24 05:10 UTC, held 91 "run failed" emails from GitHub:

- 74 include a failed `t3-approval`. In 64 of them, it is the only failed job.
- By repo: health 35, portfolio 29, courses 10.
- Each push to a T3 PR sends one. Each review or label event before the approval sends one more, from `ADLC review`.

For example, run 40057245531 of courses (PR #62) failed with "T3 change: needs the adlc:t3-approved label from anandfrancis93 after commit 2991044…, or an approval of that commit."
Nothing was wrong with that PR. The owner had not approved it yet.

So a failure email no longer means that something broke, and real failures are lost among the others.
The failed runs also cause the extra work of release 0.7.0: GitHub keeps the failed check after a later run passes,
so `rerun-t3-approval` re-runs it, and a T3 PR open across a sync needs a draft toggle ([0.7.0 intent](../2026-10-23-t3-approval-after-label/intent.md)).

## Proposed outcome
- A T3 PR that waits for the owner's approval has no failed run, so the owner gets no failure email for it.
- The merge stays blocked until the owner approves, as today.
- After the approval, the PR can merge when its other checks pass. No one re-runs a job or moves the PR to draft.

## Affected users and systems
- The owner, who reads the failure emails.
- Each repo on the ADLC, and the agents that merge its T3 PRs.
- `.github/workflows/adlc.yml` and `adlc-review.yml`, and their callers in `templates/github/workflows/`.
- `docs/risk-tiers.md`, `docs/sync.md` and `tests/test_adlc.py`.

## Constraints
- The approval rule does not change. Only the owner's label after the head commit, or the owner's approving review of that commit, approves.
- A failed tier, or any error in the approval check, still blocks the merge.
- A label or review event never skips or replaces the result of the `checks` job.
- The callers get no write permission that the outcome does not need.
- A repo gets each ADLC change only through a release and its sync PR.
- Any change to a repo's settings, such as its required checks, goes in the changelog as a Breaking line.

## Open questions
- How the gate blocks the merge without a failed run: a pending commit status, a check run left open, or another way. The spec decides.
- Whether the required check `adlc / t3-approval` that each repo has today can stay, with no settings change.

## Done when
- `bash tests/run.sh` passes, with new tests that fail on `main` today.
- On the first T3 sync PR of the new release:
  1. Before the approval, no job fails for want of the approval, and `gh pr merge` is refused.
  2. The owner adds the label. The PR then merges with no re-run and no draft toggle.
  3. The owner's Gmail holds no "run failed" email in which `t3-approval` failed on that PR.

Failure emails from other workflows, such as portfolio's watch heartbeat, are not part of this change.
