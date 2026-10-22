# Secret scanning

[Betterleaks](https://github.com/betterleaks/betterleaks), from the people who wrote Gitleaks,
pinned to **v1.9.0**, the latest stable release (v2 is still a release candidate).

- Pre-commit: `betterleaks git . --pre-commit --staged --redact` scans only the staged diff.
  The hook fails if `betterleaks` is not installed.
- CI: the `secrets` step of the `checks` job scans only the PR's commits with `--log-opts="BASE..HEAD"`. There is no
  official GitHub Action, so the step downloads the v1.9.0 release archive and checks it against the
  release's `checksums.txt`.
- Both exit 1 when they find a secret. `--redact` keeps the secret out of logs.
- A found secret is compromised: revoke it first, then remove it from the commits.

## Install v1.9.0 locally

- macOS: `brew install --cask betterleaks/tap/betterleaks@1`. The cask's command is `betterleaks-v1`;
  link it as `betterleaks` (for example `ln -s "$(command -v betterleaks-v1)" ~/bin/betterleaks`).
- Any OS with Go: `go install github.com/betterleaks/betterleaks@v1.9.0`.
- Or download `betterleaks_1.9.0_<os>_<arch>` from the
  [v1.9.0 release](https://github.com/betterleaks/betterleaks/releases/tag/v1.9.0).

Move to v2 in its own PR once v2 is stable; its CLI and config changed (see the project's v2 migration guide).
