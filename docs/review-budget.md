# Review budget

1. One agent review per PR, against the repo's `REVIEW.md`. Any model may review.
   The review runs in a fresh session, not the one that wrote the change, because a model
   tends to favour results it produced. A fresh session drops the author's reasoning; a
   different model is better still.
2. Findings are tagged **Important**, **Nit** or **Pre-existing**.
   - Important: would break behavior, leak data or breach a policy. Only Important blocks.
     Each one says how to show it fails: an input, a test or a command.
   - Nit: at most five, listed, never blocking.
   - Pre-existing: a bug the PR did not introduce. Reported, not blocking.
3. Style-only, diagnostics-only and cleanup-only findings are dropped.
4. After round 1, re-review only the new diff. Never repeat a posted finding.
5. Flag the class of bug, so the author fixes every instance at once.
6. After 2 rounds, CI labels the PR `adlc:owner-decides` and the owner merges or closes it.
   `scripts/adlc-review-rounds` counts the rounds.

## Repeated findings

A finding that repeats does **not** become a new line in `AGENTS.md`. It goes into
the retire log as a candidate. It becomes a rule only as a test, lint rule or
hook, and only after the owner accepts it.

This departs from the Anthropic playbook, which adds a twice-repeated mistake to
CLAUDE.md. That rule made each later review check more.
