---
name: adlc-release
description: Decide whether an ADLC pull request may merge, by tier, and watch the deploy after the merge. Use when a PR's checks have finished and the question is whether to merge.
---
# ADLC Release

1. Read the PR's `adlc:T*` label (set by CI).
2. T1 and T2: merge when the `checks` check passes and no Important finding is open.
3. T3: merge only after the owner approves, and `t3-approval` passes.
   The owner adds the `adlc:t3-approved` label, or approves the latest commit in a review.
   `t3-approval` is a commit status. It stays pending until the approval, and no run fails while it waits.
   To wait for the other checks first, use `gh run watch` on the `ADLC` run, not `gh pr checks --watch`.
   If the owner tells you to merge and you work from the owner's account, add the label yourself.
   Before you merge, check the approval yourself, not only the green status: any workflow of the repo can post it.
   The last `adlc:t3-approved` event in `gh api repos/{owner}/{repo}/issues/N/events` must be `labeled`
   by the owner after the head commit, or the owner approved the head commit.
   If the repo deploys, ship behind a feature flag or staged rollout, and confirm the rollback command works.
4. If the PR has `adlc:owner-decides`, do not push more fixes. Summarize the open
   findings for the owner, who merges or closes it.
5. Merge with squash; the commit title is the PR title. Versioned releases are a separate
   step: use the `adlc-version` skill.
6. If the repo deploys on a push to main, watch the deploy run until it ends.
   For GitHub Actions, find the run with `gh run list --commit <merge-sha>`,
   then run `gh run watch <run-id> --exit-status`.
   If the run fails, tell the owner at once and name the failed step.
   `gh run view <run-id> --log-failed` shows the failed step.
