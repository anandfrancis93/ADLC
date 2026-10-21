---
name: adlc-spec
description: Write the spec for a T2 or T3 change in an ADLC repo. The spec lists the tests to add and the files in scope, not prose results. Use after adlc-plan when the tier is T2 or T3.
---
# ADLC Spec

Write `spec.md` (T3) or a Spec section in the PR (T2) with only:

1. **Tests to add**: one line each, as the test name and what it asserts.
2. **Files in scope**: the paths the change may touch.
3. **Out of scope**: what this change will not do.

Do not write expected results, counts or proof in prose. The tests and CI produce
the results; the PR links to the CI run.

For T3 bug fixes, the first test reproduces the bug and must fail before the fix.
Add its path to `.adlc/protected` so the fix cannot edit it.
