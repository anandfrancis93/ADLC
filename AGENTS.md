# ADLC repo

This repo defines a lifecycle; it has no application code.

## Commands
- Test: `bash tests/run.sh` (tests the scripts in `scripts/`)
- Validate plugin: `claude plugin validate .`

## Layout
- `docs/`: the lifecycle, one file per topic.
- `skills/`: Agent Skills (SKILL.md). Name must match the folder.
- `scripts/`: tier classifier, protected-path check, review-round counter, PR-title check,
  changelog draft and entry.
- `templates/`: files a repo copies to adopt the ADLC.
- `.claude-plugin/`, `agents/`, `hooks/`: Claude Code plugin only.

## Rules
- Keep this file and `templates/AGENTS.md` under 60 lines.
- Process rules go in a skill, a script or CI, not in prose here.
- PR titles are Conventional Commits; PRs are squash-merged.
- Do not edit `CHANGELOG.md` in feature PRs. Releases use the `adlc-version` skill.
