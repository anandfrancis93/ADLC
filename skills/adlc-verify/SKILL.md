---
name: adlc-verify
description: Check your own work in an ADLC repo before asking for review. Runs the fast check locally and leaves the full suite to CI, which runs it once. Use before opening or updating a PR.
---
# ADLC Verify

1. Run the fast check on changed files: `.adlc/fast-check <files>`. Fix what it reports.
2. Run only the tests that cover the files you changed, if the repo's test runner can target them.
   Do not run the full suite locally; CI runs it once per change.
3. Fixing a flaky test: run that one test the same number of times on the base and on the branch.
   Pick a count that makes the base fail at least once. The branch must pass every run.
   Put both counts in Testing. If the base never fails, say the fix is not proven.
4. T3: confirm the committed failing test now passes without being edited.
5. T3 with proof records: re-run only the records whose input files changed.
   Never re-run all proof because an unrelated file (for example CSS) changed.
6. In the PR, fill in Testing with the commands you ran and their result, Risk, and How to revert.
   A check that did not start, or only checked syntax, is not a pass. Name each check you did
   not run, and why.
