---
name: adlc-review
description: Review a pull request under the ADLC review budget. One review, only Important findings block, nits capped at five, pre-existing bugs never block, no repeated findings. Use when asked to review a PR in a repo with REVIEW.md or .adlc/.
---
# ADLC Review

Review in a fresh session that did not write the change. If this session wrote it, stop and
ask for a new session or another model.

Read `REVIEW.md` first. Then:

1. Review the diff against the whole repo and the PR's stated intent.
2. Tag every finding:
   - **Important**: would break behavior, leak data or breach a policy. Give file, line, evidence,
     and how to show it fails (an input, a test or a command).
   - **Nit**: at most five; summarize the rest as a count.
   - **Pre-existing**: a bug the PR did not introduce. Never blocking.
3. Drop style-only, diagnostics-only and cleanup-only findings, and anything CI enforces.
4. Flag the class of bug with every instance, not one line.
5. On round 2: review only the diff since round 1. Do not repeat any finding already posted.
6. Start the summary with the number of Important findings. If it is zero, say so plainly.
7. Post the summary as one comment on the PR. Submit it as a review with the Comment option,
   so CI counts the round: `gh pr review <number> --comment --body-file <file>`.
   The `adlc-release` skill reads it to check that no Important finding is open.

There is no round 3. After 2 rounds the owner decides.
A finding that keeps recurring goes in `.adlc/retire-log.md` as a candidate check,
not into AGENTS.md or CLAUDE.md.
