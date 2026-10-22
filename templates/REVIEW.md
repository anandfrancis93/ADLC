# Review instructions (ADLC review budget)

## What to check
- Bugs: logic errors, broken edge cases, regressions.
- Security: injection, auth gaps, secrets or personal data in logs.
- Compliance: the change matches its spec and plan, if any.

## Tags
- Important: would break behavior, leak data or breach a policy. Only Important blocks.
  Say how to show it fails: an input, a test or a command.
- Nit: at most five per review; summarize the rest as a count. Never blocking.
- Pre-existing: a bug this PR did not introduce. Report it; do not block.

## Do not report
- Style-only, diagnostics-only or cleanup-only findings.
- Anything CI already enforces (format, lint, types).
- Generated files: <paths>.

## Rounds
- After round 1, review only the new diff. Never repeat a finding already posted.
- Flag the class of bug, with every instance, not one line.
- Start the summary with the count of Important findings; say plainly when there is nothing to fix.
