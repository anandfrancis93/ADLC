# Formatting

- One auto-fixing formatter per language, for example [Prettier](https://prettier.io/) for
  JavaScript, TypeScript, CSS, JSON, YAML and Markdown, and the [Ruff](https://docs.astral.sh/ruff/formatter/)
  formatter for Python. No second formatter for the same files.
- Pin the formatter's exact version (Prettier's install guide uses `--save-exact`; Ruff ships
  style changes in minor releases), so the hook and CI format the same way.
- Pre-commit: `.adlc/fast-check` formats the staged files and stages the result. If a staged file
  also has unstaged edits, it stops and asks you to stage or stash them, because re-staging the
  file would also stage those edits.
- CI: the `fast-check` step of the `checks` job runs the same script with `ADLC_CHECK_ONLY=1` on the PR's changed files,
  so it checks without writing (`prettier --check`, `ruff format --check`).
- `.editorconfig`: copy `templates/editorconfig`. It stays short and exists only because Prettier
  reads it ([docs](https://prettier.io/docs/configuration#editorconfig)). Other settings belong in
  each formatter's own config. There is no editorconfig-checker.
