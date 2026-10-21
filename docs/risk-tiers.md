# Risk tiers

The change sets the tier, not the author. `scripts/adlc-tier` reads the files a
change touches and the repo's `.adlc/tiers` map, and returns the highest tier hit.
Files that match no pattern are T2.

| | T1 Low | T2 Standard | T3 High |
| --- | --- | --- | --- |
| Examples | Docs, copy, CSS, comments, config with no behavior change | A behavior change inside one module | Data and schemas, auth, grading or scoring logic, migrations, public interfaces, CI workflows, anything not reversible |
| Plan | One line in the PR | Issue with intent | `intent.md` |
| Design | None | Spec: tests to add | Spec plus accepted plan |
| Verify | Pre-commit, CI | Pre-commit, CI | Pre-commit, CI, failing test first, proof for changed inputs |
| Review | One review | One review | One review |
| Release | Merge when green | Merge when green | Owner approves |
| Proof records | Not touched | Re-run if inputs changed | Re-run if inputs changed |

The T3 default is broad on purpose: start strict and loosen with evidence.
CI workflow files are always T3.

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
