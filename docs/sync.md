# Keeping repos in sync

Each repo pins one ADLC release. CI fails a PR when the repo's copy of the ADLC differs
from that release. After each release, a check finds the repos behind it.

## How it works

- The CI jobs live in this repo as shared workflows: `.github/workflows/adlc*.yml`.
  Each repo has short caller workflows that run them at a release tag, such as `@v0.4.0`.
- `scripts/adlc.py sync` writes two kinds of files into a repo: managed and repo-owned.
- `.adlc/version` records the release the repo is on.
- The `drift` job fails a PR when a managed file differs from the pinned release.
  It compares SHA-256 hashes written into the shared `adlc.yml`, so a repo cannot edit them.
- Review events run a separate caller, `adlc-review.yml`, with only `tier`, `t3-approval` and `review-budget`.
  A job skipped on a review run would report success under its check name, and hide a failure.

Managed files belong to the ADLC. Every sync overwrites them, and the repo never edits them:

- `.adlc/version`, `.adlc/scripts/adlc.py`, `.githooks/pre-commit`
- `.github/workflows/adlc.yml`, `adlc-review.yml`, `adlc-pr-title.yml`, `adlc-dependabot.yml`
- `.github/workflows/adlc-release.yml`, only in repos that ship releases
- `.github/pull_request_template.md`

Repo-owned files start from a template. Sync adds each one only when it is missing, and nothing checks them:

- `AGENTS.md`, `REVIEW.md`, `.editorconfig`, `.github/dependabot.yml`
- `.adlc/tiers`, `.adlc/protected`, `.adlc/install`, `.adlc/fast-check`, `.adlc/full-test`, `.adlc/retire-log.md`
- `CHANGELOG.md`, only in repos that ship releases

To change a managed file for every repo, change it in this repo and release a new version.

## One-time setup in the ADLC repo

This repo is private. Let the owner's other private repos call its workflows:
Settings > Actions > General > Access > "Accessible from repositories owned by 'anandfrancis93' user" > Save
([GitHub docs](https://docs.github.com/actions/creating-actions/sharing-actions-and-workflows-from-your-private-repository)).

A public repo can call only public workflows
([GitHub docs](https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations)).
A public repo can use the ADLC's shared CI only after this repo is made public.

## Adopt the ADLC or update a repo

Run this in the repo's root, on a new branch:

```
v=$(gh release view -R anandfrancis93/ADLC --json tagName -q .tagName)
tmp=$(mktemp -d)
git -c advice.detachedHead=false clone -q --depth 1 --branch "$v" https://github.com/anandfrancis93/ADLC "$tmp/ADLC"
python3 "$tmp/ADLC/scripts/adlc.py" sync .
```

- Add `--releases` on the first sync of a repo that ships releases.
- `--check` lists what sync would change, and writes nothing.
- Sync stops if the ADLC checkout is not exactly at a release tag.
- Sync sets `core.hooksPath` to `.githooks` in that clone.

Then:

1. Read the ADLC changelog from the repo's old version to the new one.
   Do what each **Breaking** line asks.
2. Open a PR titled `chore(adlc): sync to X.Y.Z`. CI rates it T3, because it changes CI files.
3. For a new repo, fill in the repo-owned files and settings. See "Adopt it in a repo" in the README.

### First sync of a repo set up by copying (v0.3.0 or earlier)

- Sync replaces the full `.github/workflows/adlc*.yml` files with callers.
- The required check names change, because each job now runs inside a caller job.
  After the first PR runs, copy the new names from its checks list into branch protection.
- Add the `ignore` entry from `templates/github/dependabot.yml` to the repo's `.github/dependabot.yml`.

## New repos

Create the repo, then adopt the ADLC as above:

```
gh repo create anandfrancis93/NAME --private --clone
```

A template repo is optional. It saves the sync command, but it is one more repo to keep in sync.
GitHub copies only its files into a new repo, not its settings. To set one up:

1. Create `anandfrancis93/adlc-template`, sync it with `--releases`, and push.
2. Mark it as a template: `gh repo edit anandfrancis93/adlc-template --template`.
3. Start a new repo from it: `gh repo create anandfrancis93/NAME --private --template anandfrancis93/adlc-template --clone`.

The release check covers the template repo like any other repo.

## After each ADLC release

Run this check right after pushing the release tag. A weekly run of the same check catches anything missed.

1. It reads the latest release: `gh release view -R anandfrancis93/ADLC --json tagName -q .tagName`.
2. It reads `.adlc/version` on each repo's default branch.
   A repo with `.adlc/tiers` but no `.adlc/version` was set up by copying, before sync existed.
   A repo with neither file does not use the ADLC, and the check skips it.
3. It lists each repo behind the latest release, with both versions.
   Each listed repo gets a sync PR, made as in "Adopt the ADLC or update a repo".
4. A repo it cannot read is a failed check, not "up to date".

Dependabot does not bump the ADLC tag in callers. The template's `.github/dependabot.yml` ignores
`anandfrancis93/ADLC*`, for two reasons:

- A bump changes only the tag. `drift` fails until someone also runs sync.
  A Dependabot PR with commits from anyone else also loses its tier.
- Dependabot needs a token to read a private repo. GitHub's documented way is a `git` registry
  with a personal access token, stored as a Dependabot secret in each repo.

## Changing the ADLC itself

- After a change to `scripts/` or `templates/`, run `python3 scripts/adlc.py manifest --write`.
  The test suite fails until the manifest in `.github/workflows/adlc.yml` matches.
- A release PR also bumps `.claude-plugin/plugin.json`, then runs the same command.
  The version is part of the hashes, because callers and `.adlc/version` contain it.

## Limits

- Sync does not copy skills. Claude Code users get them from the plugin. Other tools copy `skills/` again.
- Sync never deletes a file. When a release stops managing a file, its changelog says to delete it.
- A caller must pin a release tag. A branch or commit pin fails `drift`.
