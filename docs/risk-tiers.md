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

The `t3-approval` check passes when the owner (the `ADLC_OWNER` variable) did one of these:

- Added the `adlc:t3-approved` label after the latest commit, and no one changed that label since.
  CI also removes the label after each new commit.
- Approved the latest commit in a review.

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
