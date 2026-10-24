# Plan: T3 approval waits for the owner without a failed run

Date: 2026-10-24. Spec: [spec.md](spec.md).

## Files that change
- `tests/test_adlc.py`: the tests of the spec. The fake `gh` also logs the `-f` fields of each request.
  The tests of `RerunStep` go. The caller test reads only `uses:` lines, because `statuses: write` also holds "uses: ".
- `scripts/adlc.py`: the command `t3-status` in place of `t3-approved`, and the help text.
- `.github/workflows/adlc.yml`: the job `tier` in place of `t3-approval`, the header comment, the manifest.
- `.github/workflows/adlc-review.yml`: the same job `tier`, no `rerun-t3-approval`, the header comment.
- `.github/workflows/adlc-dependabot.yml`: the status step first, and `statuses: write`.
- `templates/github/workflows/adlc.yml`, `adlc-review.yml` and `adlc-dependabot.yml`: the permissions and the comments.
- `docs/risk-tiers.md`, `docs/sync.md`, `skills/adlc-release/SKILL.md`.

## Order of work
1. Commit this plan, and open the code PR as a draft. Push no code until the tech lead accepts the plan in a PR comment.
2. Commit the tests of the spec, and nothing else. Paste in the PR the output that shows each new test fails on the old code.
3. `scripts/adlc.py`: `t3_status(tier, owner, head, since, reviews, events)` returns the state and a description of at most 140 characters.
   `t3-status` prints them as JSON and exits 0. It reads the reviews and events files only for T3, and fails on a file that is not JSON.
   `t3_approval` does not change.
4. The job `tier`, the same in `adlc.yml` and `adlc-review.yml`. It runs no file from the PR:
   - The drop and label steps stay as they are.
   - A first checkout gets the ADLC at `job.workflow_repository` and `job.workflow_sha` into `adlc-release`.
     A second gets the PR into `pr`. Both use `persist-credentials: false`.
   - The tier step runs in `pr`: `git diff` and `python3 -I ../adlc-release/scripts/adlc.py tier --explain`, which reads the PR's `.adlc/tiers`.
   - The step "Report the owner's approval" runs for each tier. For T3 it reads the reviews, the events and the first check suite.
     It runs `python3 -I adlc-release/scripts/adlc.py t3-status`, and posts the result to `POST repos/{repo}/statuses/{head}` under `adlc / t3-approval`, with the run's URL.
     It reads again after each post. It stops when a read gives the posted answer, and fails after 5 reads.
   - The step "Block the merge when this job fails" runs on `failure() || cancelled()`, and posts `failure`.
   - Permissions: those of the old job, and `statuses: write`. No `outputs`.
5. `adlc-review.yml`: remove `rerun-t3-approval`.
6. `adlc-dependabot.yml`: a first step posts `success` under `adlc / t3-approval`. The workflow grants `statuses: write`.
7. Caller templates: `statuses: write` in all three. `actions: read` in place of `actions: write` in `adlc-review.yml`.
8. Docs: `docs/risk-tiers.md` says what the status is, when it passes, and how to wait for the other checks.
   `docs/sync.md` names the jobs and the required checks, and gives the step for a T3 PR open across the sync.
   `skills/adlc-release/SKILL.md` says the same in step 3, with the guard of spec Decision 9:
   before a T3 merge, the agent checks the owner's label event or review itself.
9. Run `python3 scripts/adlc.py manifest --write` and `bash tests/run.sh`.

## Risks
- The trial is the first proof that the status meets each repo's required check. The ADLC repo does not run its own shared workflows.
  If a repo's rule expects the check from one GitHub App and the status does not count, the sync PR stays blocked.
  The owner then sets the rule's source to GitHub Actions, not to any source, from the MacBook. I don't know if any repo sets a source.
- A T3 PR open across the sync needs its branch updated once, before the approval. Strict rules ask for that anyway.
- Accepted in the spec (Decision 9): a workflow of another branch of the repo can post the status. The guard is in step 8.
- `job.workflow_sha` and `job.workflow_repository` are in the GitHub docs, but no run of the ADLC has used them yet.
  The trial is their first proof. If they are empty, the checkout gets the calling repo, which has no `scripts/adlc.py`.
  The tier step then fails, and the job posts `failure`, so the merge stays blocked.
- Each read of a T3 PR is 3 to 4 requests, and a run reads at least twice. The `GITHUB_TOKEN` limit is 1,000 requests per hour per repo
  ([GitHub docs](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api#primary-rate-limit-for-github_token-in-github-actions)).
- GitHub keeps at most 1,000 statuses for one commit and context ([GitHub docs](https://docs.github.com/en/rest/commits/statuses)).
  A commit gets one or two for each run.

## Proof
- Step 2: each new test fails on the old code.
- `bash tests/run.sh` passes after step 9.
- The trial in the spec, on the first T3 sync PR of the new release.

Update this file in the same commit when the work departs from it.
