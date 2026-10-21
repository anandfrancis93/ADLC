---
name: adlc-release
description: Decide whether an ADLC pull request may merge, by tier. Use when a PR's checks have finished and the question is whether to merge.
---
# ADLC Release

1. Read the PR's `adlc:T*` label (set by CI).
2. T1 and T2: merge when `full-test` passes and no Important finding is open.
3. T3: merge only after the owner has approved the latest commit (`t3-approval` check passes).
   If the repo deploys, ship behind a feature flag or staged rollout, and confirm the rollback command works.
4. If the PR has `adlc:owner-decides`, do not push more fixes. Summarize the open
   findings for the owner, who merges or closes it.
