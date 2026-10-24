# Plan: T3 approval passes after the owner approves, with no re-run

Date: 2026-10-23. Spec: [spec.md](spec.md).

## Files that change
- `tests/test_adlc.py`: the tests of the spec, and a fake `gh` that serves fixed API answers and logs each request.
- `scripts/adlc.py`: `t3_approval` counts a label only after the newest `head_ref_force_pushed` event too.
- `.github/workflows/adlc.yml`: the drop step, `outputs.tier` and a `permissions` block on `t3-approval`, the comments, the manifest.
- `.github/workflows/adlc-review.yml`: the same `t3-approval` job, a `permissions` block on `review-budget`, the new job `rerun-t3-approval`, the comments.
- `templates/github/workflows/adlc.yml`: `actions: read`.
- `templates/github/workflows/adlc-review.yml`: `actions: write`, the comments.
- `docs/risk-tiers.md`, `docs/sync.md`.

## Order of work
1. Commit this plan, and open the code PR as a draft. Push no code until the tech lead accepts the plan in a PR comment.
2. Commit the tests of the spec, and nothing else. Paste in the PR the output that shows each new test fails on the old code.
3. `t3_approval`: the label counts only when it came after the later of `--since` and the newest `head_ref_force_pushed` event.
   The rule for `--since` itself does not change.
4. The drop step reads the run's `created_at` (`GET actions/runs/$GITHUB_RUN_ID`) and the PR's issue events.
   It keeps the label when its last change is a `labeled` after that time. Otherwise it sends the `DELETE`, as today.
5. Permissions: move each job's scopes into its own `permissions` block, and remove the workflow-level block from both shared workflows.
   Each job keeps the scopes it has today. `t3-approval` also gets `actions: read`, for step 4.
6. `t3-approval` gets `outputs.tier`. The new job `rerun-t3-approval` in `adlc-review.yml`:
   - `needs: t3-approval`, and runs only when `needs.t3-approval.outputs.tier == 'T3'` and `github.run_attempt == '1'`.
   - Its permissions are `actions: write`, `contents: read` and `pull-requests: read`. It has no checkout.
   - One step, a Python script inline in the workflow (`shell: python3 -I {0}`), which calls only `gh api`.
     It lists the runs on the head commit of the callers `adlc.yml` and `adlc-review.yml`,
     and the latest attempt of each run's `t3-approval` job.
   - It waits while a run of the same ADLC commit has a `t3-approval` that is running, or that failed in a run that is still running.
     It reads the PR's head on each poll, and stops with no re-run when the head moved. It polls each 30 seconds, for up to 30 minutes.
   - Then it re-runs each failed `t3-approval` job of those runs (`POST actions/jobs/{id}/rerun`).
     When a request fails, it reads the run again, and passes when the run is queued or running again.
   - It tries a failed read twice more, one poll interval apart. A re-run of its own run skips it,
     so each of its errors says which `t3-approval` jobs to re-run by hand.
   - For a run of another ADLC commit with a failed `t3-approval`: it passes with a notice when a newer run of the same caller passed `t3-approval`.
     Otherwise it fails, and names that run and the draft step in `docs/sync.md`.
7. Caller templates: `actions: read` in `adlc.yml`, `actions: write` in `adlc-review.yml`. Update the comments of both.
8. Docs: `docs/risk-tiers.md` says the drop step keeps a label added after the push, and that the owner's approval re-runs
   the failed approval checks. `docs/sync.md` names the three jobs of `adlc-review.yml`, and gives the draft step
   for a T3 PR whose `ADLC` run is from the release before.
9. Run `python3 scripts/adlc.py manifest --write` and `bash tests/run.sh`.

## Risks
- The GitHub docs say a called workflow can only downgrade the caller's permissions. They do not say whether a job
  block in a called workflow can name a scope that the called workflow's own top-level block leaves out.
  With no top-level block in the shared workflows, each job gets exactly its own block, capped by the caller. Step 5 does that.
- A caller that does not grant `actions` breaks the drop step and the re-run job. The sync PR writes
  the callers and the version together, and the drift check fails a caller that differs.
- The runs list asks for 100 runs of each caller on one commit, with no pagination. A commit with more runs than that is
  not expected. The script then sees only the newest 100.
- The re-run job waits for up to 30 minutes: 60 polls, each of 3 requests and one more for each run. The `GITHUB_TOKEN` limit is
  1,000 requests per hour per repo ([GitHub docs](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api#primary-rate-limit-for-github_token-in-github-actions)).
- The GitHub docs say that an event the `GITHUB_TOKEN` triggers starts no new workflow run, except `workflow_dispatch`
  and `repository_dispatch` ([GitHub docs](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)).
  They do not say whether a re-run that this token asks for starts. If the trial shows that it does not, the red check
  stays after the approval, and the fix needs a new spec.
- The ADLC repo does not run its own shared workflows on its PRs. So only the tests and the trial prove the workflow paths.

## Proof
- Step 2: each new test fails on the old code.
- `bash tests/run.sh` passes after step 9.
- The trial in the spec, on the first T3 sync PR of the new release.

Update this file in the same commit when the work departs from it.
