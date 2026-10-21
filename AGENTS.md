# ADLC repo

This repo defines a lifecycle; it has no application code.

## Commands
- Test: `bash tests/run.sh` (tests the scripts in `scripts/`)
- Validate plugin: `claude plugin validate .`

## Layout
- `docs/`: the lifecycle, one file per topic.
- `skills/`: Agent Skills (SKILL.md). Name must match the folder.
- `scripts/`: tier classifier, protected-path check, review-round counter.
- `templates/`: files a repo copies to adopt the ADLC.
- `.claude-plugin/`, `agents/`, `hooks/`: Claude Code plugin only.

## Rules
- Keep this file and `templates/AGENTS.md` under 60 lines.
- Process rules go in a skill, a script or CI, not in prose here.
