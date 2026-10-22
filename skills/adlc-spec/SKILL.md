---
name: adlc-spec
description: Write the spec for a T2 or T3 change in an ADLC repo. The spec lists the tests to add and the files in scope, not prose results; T3 specs also record the decision. Use after adlc-plan when the tier is T2 or T3.
---
# ADLC Spec

T2: a Spec section in the PR description. T3: the file `docs/specs/YYYY-MM-DD-<slug>.md`
(template: `templates/spec.md` in the ADLC repo), which already holds the Intent from `adlc-plan`.
Write only:

1. **Tests to add**: one line each, as the test name and what it asserts.
2. **Files in scope**: the paths the change may touch.
3. **Out of scope**: what this change will not do.
4. **Decision** (T3 only): the choice made, the alternatives considered, and why this one.
   A few lines. This replaces separate architecture decision records.

Do not write expected results, counts or proof in prose. The tests and CI produce
the results; the PR links to the CI run.

T3 specs stay in the repo after merging, as the record of why the change was made. Do not edit
an old spec to describe a later change; write a new spec that links to it.

For T3 bug fixes, the first test reproduces the bug and must fail before the fix.
Add its path to `.adlc/protected` so the fix cannot edit it.
