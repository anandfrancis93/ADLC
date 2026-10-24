# Risk tiers

The change sets the tier, not the author. `scripts/adlc.py tier` reads the files a
change touches and the repo's `.adlc/tiers` map, and returns the highest tier hit.
Files that match no pattern are T2.

| | T1 Low | T2 Standard | T3 High |
| --- | --- | --- | --- |
| Examples | Docs, copy, CSS, comments, config with no behavior change | A behavior change inside one module | Data and schemas, auth, grading or scoring logic, migrations, public interfaces, CI workflows, anything not reversible |
| Plan | One line in the PR | Issue with intent | `intent/<change>/intent.md`, own PR |
| Design | None | Spec: tests to add | `spec.md` with Decision section, own PR; `plan.md` accepted before code ([folder](stages.md#t3-change-folder)) |
| Verify | Pre-commit, CI | Pre-commit, CI | Pre-commit, CI, failing test first, proof for changed inputs |
| Review | One review | One review | One review |
| Release | Merge when green | Merge when green | Owner approves |
| Proof records | Not touched | Re-run if inputs changed | Re-run if inputs changed |

The T3 default is broad on purpose: start strict and loosen with evidence.
CI workflow files are always T3, except in Dependabot PRs: patch and minor updates are T1 and
major updates T2, whatever files they touch ([toolchain.md](toolchain.md)).

## T3 approval

`adlc / t3-approval` is a commit status on the PR's head commit. The `tier` job posts it on each push,
label change and review. A T3 change passes when the owner (the `ADLC_OWNER` variable) did one of these:

- Added the `adlc:t3-approved` label after the latest commit and after the newest force push,
  and no one changed that label since. CI removes the label after each new commit, unless the label
  was added after GitHub created the run of that push. A re-run of that run keeps the label too.
- Approved the latest commit in a review.

Until then, the status is pending, and a pending required check blocks the merge.
The `tier` job itself passes, so GitHub sends no failure email while the PR waits.
GitHub counts the latest status of each name, so the run of the owner's label or review turns it to success.
No one re-runs a job or moves the PR to draft.
T1 and T2 changes, and Dependabot PRs, get a passing status at once.
When the `tier` job fails, it posts a failed status, so the merge stays blocked.
The job runs no file from the PR, because it can write statuses. It runs the ADLC's own `adlc.py` at the release.
Any workflow of the repo can post a status, and GitHub shows each as from GitHub Actions.
So a PR from a branch of the repo could post `success` on another PR. A fork PR cannot, as its token can only read.
The owner accepted this risk in the [spec](../intent/2026-10-24-t3-approval-without-failed-runs/spec.md).
So before an agent merges a T3 PR, it checks the owner's label or review itself (the `adlc-release` skill, step 3).
To wait for the other checks before the approval, watch the `ADLC` run with `gh run watch`, not `gh pr checks --watch`.
One exception: a T3 PR that was open when its repo moved to a new release ([sync.md](sync.md#a-t3-pr-open-across-a-sync)).

GitHub does not let a PR's author approve it
([GitHub docs](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/approving-a-pull-request-with-required-reviews)).
Use the label on PRs opened from the owner's account.

## `.adlc/tiers` format

One rule per line: a tier, a space, a path glob. `#` starts a comment.
`**` matches across directories. The highest matching tier wins.

```
T1 docs/**
T1 **/*.md
T1 **/*.css
T3 .github/workflows/**
T3 src/grading/**
```
