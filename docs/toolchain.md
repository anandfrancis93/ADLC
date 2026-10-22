# Toolchain and dependencies

## Pinned versions

- One version file per language, committed: `.nvmrc` for Node, `.python-version` for Python.
- CI reads them: `actions/setup-node` with `node-version-file: .nvmrc` and `actions/setup-python`
  with `python-version-file: .python-version` (both in `adlc.yml`, used only when the file exists).
- Commit the lockfile and install exactly from it in `.adlc/install`: `npm ci` (fails if
  `package-lock.json` and `package.json` disagree, never writes them) or `uv sync --locked`.
- [mise](https://mise.jdx.dev/) is optional for installing these versions locally.

## Dependabot

Copy `templates/github/dependabot.yml` to `.github/dependabot.yml`, keep one entry per ecosystem
the repo uses, and always keep `github-actions`.

- Version updates weekly. Patch and minor updates are grouped into one PR per ecosystem; each major
  update gets its own PR.
- PR titles start `chore(deps):` so they pass the Conventional Commits title check.
- Tiers (`adlc-dependabot.yml`): patch and minor are T1, major is T2, whatever files they touch.
  A Dependabot PR with commits from anyone else fails that job and is tiered by hand.
- Security updates: turn on "Dependabot security updates" in the repo settings. The weekly
  `schedule` and the cooldown apply only to version updates, so security updates do not wait for them
  ([options reference](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference)).
- T1 merges when CI is green. T2 also needs its one review.
