# ADLC repo

This repo defines a lifecycle; it has no application code.

## Commands
- Test: `bash tests/run.sh` (tests the scripts in `scripts/`)
- Validate plugin: `claude plugin validate .`

## Layout
- `docs/`: the lifecycle, one file per topic.
- `skills/`: Agent Skills (SKILL.md). Name must match the folder.
- `scripts/`: tier classifier, protected-path check, review-round counter, PR-title check,
  changelog draft and entry, sync into a repo, drift manifest.
- `templates/`: files `adlc.py sync` writes into a repo (`docs/sync.md`).
- `.github/workflows/adlc*.yml`: shared CI that other repos call at a release tag.
  The other workflows run on this repo only.
- `.claude-plugin/`, `agents/`, `hooks/`: Claude Code plugin only.

## Rules
- Keep this file and `templates/AGENTS.md` under 60 lines.
- Process rules go in a skill, a script or CI, not in prose here.
- Write prose for people by `skills/adlc-writing/SKILL.md`.
- PR titles are Conventional Commits; PRs are squash-merged.
- Do not edit `CHANGELOG.md` in feature PRs. Releases use the `adlc-version` skill.
- After changing `scripts/`, `templates/` or the version in `.claude-plugin/plugin.json`,
  run `python3 scripts/adlc.py manifest --write`. The tests fail until you do.
- After pushing a release tag, read the summary of its `ADLC sync repos` run (`docs/sync.md`).
