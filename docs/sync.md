# Keeping repos in sync

Each repo pins one ADLC release. CI fails a PR when the repo's copy of the ADLC differs
from that release. Each new release opens a sync PR in every repo behind it.

## How it works

- The CI jobs live in this repo as shared workflows: `.github/workflows/adlc*.yml`.
  Each repo has short caller workflows that run them at a release tag, such as `@v0.4.0`.
- `scripts/adlc.py sync` writes two kinds of files into a repo: managed and repo-owned.
- `.adlc/version` records the release the repo is on.
- The `drift` check fails a PR when a managed file differs from the pinned release.
  It compares SHA-256 hashes written into the shared `adlc.yml`, so a repo cannot edit them.
- A PR runs three jobs: `t3-approval`, `checks` and `pr-title`. `checks` runs drift, protected, secrets,
  design-md, fast-check and full-test as steps of one job. GitHub bills each job as at least one minute
  ([GitHub docs](https://docs.github.com/en/billing/reference/actions-runner-pricing)).
- Review and label events run a separate caller, `adlc-review.yml`, with only `t3-approval` and `review-budget`.
  A job skipped on those runs would report success under its check name, and hide a failure.
- A release tag starts `.github/workflows/sync-repos.yml` in this repo.
  It opens a sync PR in each repo on an older release.

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

This repo is public, so any repo can call its workflows, public or private
([GitHub docs](https://docs.github.com/en/actions/reference/workflows-and-actions/reusing-workflow-configurations)).
Public repos use standard GitHub-hosted runners for free
([GitHub docs](https://docs.github.com/en/billing/concepts/product-billing/github-actions)).

The sync PRs need a token. The built-in workflow token works only in the repo that runs the workflow
([GitHub docs](https://docs.github.com/en/actions/concepts/security/github_token)). Create a fine-grained token once:

1. Open [this prefilled form](https://github.com/settings/personal-access-tokens/new?name=ADLC+sync&description=Opens+ADLC+sync+PRs+from+the+ADLC+release+workflow&target_name=anandfrancis93&expires_in=365&contents=write&pull_requests=write&workflows=write).
   It sets Contents, Pull requests and Workflows to write, and an expiry of 365 days.
2. Under Repository access, pick "All repositories". The form cannot prefill this choice.
3. Generate the token, and copy it.
4. In this repo: Settings > Secrets and variables > Actions > New repository secret.
   Name it `ADLC_SYNC_TOKEN`, paste the token, and save.
5. Add the secret before pushing the next release tag. That tag starts the first run.

A repository secret is open to every workflow in this repo, on any branch. So anyone who can push a branch here
can use the token on every repo it reaches. GitHub Pro and Team can limit an environment secret to `v*` tags
([GitHub docs](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)).
That also needs `environment:` on the `sync-repos` job, which this repo does not set yet.

To run it again: Actions > ADLC sync repos > Run workflow, then pick the release tag.
The box "List what it would do, and open no PRs" starts checked. Clear it to open PRs.

The token expires after 365 days. The first release after that fails its sync run. Make a new token then.
([GitHub docs](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens))

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

Release sync PRs cover the template repo like any other repo.

## After each ADLC release

Pushing a release tag starts the `ADLC sync repos` workflow. For each of the owner's repos, it reads
`.adlc/version` on the default branch:

- A repo on the new release needs nothing.
- A repo on an older release gets a PR titled `chore(adlc): sync to X.Y.Z`, from branch `adlc/sync-X.Y.Z`.
  The PR body lists the changed files and the changelog entries since the repo's version.
  If an open PR from that branch exists, the workflow leaves it.
- A repo with `.adlc/tiers` but no `.adlc/version` was set up by copying, before sync existed.
  The workflow lists it, and opens no PR. Do its first sync by hand, as in "First sync of a repo set up by copying".
- A repo with neither file does not use the ADLC. The workflow leaves it out.
- A repo the workflow cannot read is a failure. The run fails, so a failure is never read as "up to date".

The run's summary lists each repo and what happened.

A sync PR changes CI files, so it is T3. Before merging, do what each **Breaking** line in its body asks.
It then needs the owner's approval like any T3 PR ([T3 approval](risk-tiers.md#t3-approval)).

Dependabot does not bump the ADLC tag in callers. The template's `.github/dependabot.yml` ignores
`anandfrancis93/ADLC*`. A bump changes only the tag, so `drift` fails until someone also runs sync.
A Dependabot PR with commits from anyone else also loses its tier.

## Changing the ADLC itself

- After a change to `scripts/` or `templates/`, run `python3 scripts/adlc.py manifest --write`.
  The test suite fails until the manifest in `.github/workflows/adlc.yml` matches.
- A release PR also bumps `.claude-plugin/plugin.json`, then runs the same command.
  The version is part of the hashes, because callers and `.adlc/version` contain it.

## Limits

- Sync does not copy skills. Claude Code users get them from the plugin. Other tools copy `skills/` again.
- Sync never deletes a file. When a release stops managing a file, its changelog says to delete it.
- A caller must pin a release tag. A branch or commit pin fails `drift`.
- The workflow sees only the repos the token can read. A repo outside the token's access gets no sync PR.
- It skips forks and archived repos, and reads at most 1000 repos.
