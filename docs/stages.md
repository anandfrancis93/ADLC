# Stages

Each stage ends with an output in git or CI. Stage 1 sets a risk tier (T1, T2, T3),
and the tier decides how much of stages 2 to 6 a change goes through
([risk-tiers.md](risk-tiers.md)). Stage 7 feeds new intents back to stage 1.

## 1 Plan
- Write the intent: what is wanted, why, constraints, open questions.
- T1: one line in the PR. T2: an issue. T3: the Intent section of `docs/specs/YYYY-MM-DD-<slug>.md`.
- Set the tier with `scripts/adlc.py tier` on the planned files. A person may raise a tier, never lower it.

## 2 Design (T2, T3)
- The spec lists the acceptance tests to add and the files in scope. T3 specs add a short
  Decision section (choice, alternatives, why) and stay in `docs/specs/` after merging.
  There are no separate architecture decision records.
- Results are not written in the spec. Tests and CI produce them.
- Repos with a UI may keep a `DESIGN.md`; CI lints it. See [design-md.md](design-md.md).

## 3 Build
- T2 and T3 start from an accepted plan (plan mode in Claude Code, or a written plan in any tool).
- The pre-commit hook scans the staged diff for secrets, then formats, lints and type-checks
  staged files only. See [formatting.md](formatting.md) and [secrets.md](secrets.md).
- Tool versions come from committed version files and lockfiles. See [toolchain.md](toolchain.md).
- No pre-push hook.
- The PR title is a Conventional Commit; PRs are squash-merged. See [commits-and-releases.md](commits-and-releases.md).

## 4 Verify
- CI runs the fast check and secret scan on the PR's changes, and the full test suite once per change.
- T3: commit a failing test before the fix; the fix must not edit that test.
- T3: re-run only the proof records whose input hash changed. Full re-proof runs on a schedule.

## 5 Review
- One agent review per PR against `REVIEW.md`. See [review-budget.md](review-budget.md).

## 6 Release
- T1, T2: merge when CI and review pass.
- T3: the owner approves. Where the repo deploys, use a feature flag or staged rollout and a tested rollback.
- Repos that ship releases: SemVer version, Common Changelog entry written at release time, tag `vX.Y.Z`.
  See [commits-and-releases.md](commits-and-releases.md).

## 7 Operate
- Monitors, scheduled scans and incidents open issues that start at stage 1.
- Dependabot opens weekly version updates, and security updates outside that schedule. See [toolchain.md](toolchain.md).
- Each incident adds a regression test or eval.

## 8 Retire
- Monthly, and when `AGENTS.md` passes 60 lines. See [retire.md](retire.md).
