# Sources

The four lifecycle sources were read in full on 21 Oct 2026.

| Source | What the ADLC takes from it |
| --- | --- |
| [The AI-native SDLC playbook](https://claude.com/resources/articles/the-ai-native-sdlc-playbook), Anthropic, Louis Claxton, 21 Aug 2026 | Main source. Six stages (Plan, Design, Build, Test, Deploy, Maintain), intent/spec/plan files, plan mode, skills backed by hooks, fast build hooks with heavy checks at commit or PR, failing test first, REVIEW.md with Important vs Nit and a nit cap, rollback, monitoring that writes new intents |
| [How the Claude Code team does code review](https://claude.dev/blog/solving-code-review-at-anthropic/), Addy Osmani, Morgan Westlee Lunt, Qing Wang, 15 Oct 2026 | Risk tiers set by the change; review round cap; diff-only re-review; Pre-existing tag; no repeated findings; PR template with Testing, Risk, How to revert |
| [The Agent Development Lifecycle](https://architect.salesforce.com/docs/architect/fundamentals/guide/agent-development-lifecycle.html), Salesforce Architects (no date shown) | Layered testing, canary rollout, deploy separate from activation, rollback to last good version. It covers building an agent as a product |
| [The Agent Development Lifecycle has arrived on Cloudflare](https://blog.cloudflare.com/agent-development-lifecycle/), Brendan Irvine-Broque, 4 Aug 2026 | Lists Retire as an SDLC phase (no guidance); every change independently testable, releasable, observable, reversible; feature flag per change; CI cached by input files |

No source gives guidance on retiring rules or checks. The Retire stage extends
the playbook's monthly review tuning and its advice to replace evals that stop
discriminating.

## Conventions (read on 22 Oct 2026)

| Source | What the ADLC takes from it |
| --- | --- |
| [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) | PR title format; `feat`/`fix`/`!` map to SemVer MINOR/PATCH/MAJOR; squash workflow (FAQ) |
| [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html) | Version numbers, declared public API, start at 0.1.0, released versions never change, `v` only in tags |
| [Common Changelog](https://common-changelog.org/) | CHANGELOG.md format, written at release time, no Unreleased section, commit and PR references, `**Breaking:**` prefix. Its section 4.2 calls Conventional Commits an antipattern; see [commits-and-releases.md](commits-and-releases.md) |
| [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) | Common Changelog's parent. Read to compare; the ADLC follows the stricter Common Changelog |
| [DESIGN.md](https://github.com/google-labs-code/design.md), Google Labs, Apache 2.0, format version alpha | Optional design file for UI repos and its `lint` command |
| [Version your app](https://developer.android.com/studio/publish/versioning), Android Developers | `versionCode` must increase per release; `versionName` is a free string shown to users |
| [Prettier: configuration](https://prettier.io/docs/configuration) and [install](https://prettier.io/docs/install) | Prettier reads `.editorconfig`; pin its exact version |
| [Ruff formatter](https://docs.astral.sh/ruff/formatter/) | `ruff format --check` exits 1 when files would change; style changes ship in minor releases |
| [Betterleaks v1.x README and scanning guide](https://github.com/betterleaks/betterleaks/tree/v1.x) | `git --pre-commit --staged`, `--log-opts`, `--redact`; v1 install paths; main branch is v2 |
| [actions/setup-node](https://github.com/actions/setup-node), [actions/setup-python](https://github.com/actions/setup-python) | `node-version-file`, `python-version-file` |
| [npm ci](https://docs.npmjs.com/cli/commands/npm-ci), [uv sync](https://docs.astral.sh/uv/concepts/projects/sync/) | Exact installs that fail on a stale lockfile |
| [Karpathy on making LLM output easier to understand](https://x.com/karpathy/status/2105819303471976479), 1 Oct 2026, and [SKYbrary: Simplified Technical English](https://skybrary.aero/articles/simplified-technical-english-ste) (secondary source) | `adlc-writing`: 20-word instructions, 25-word descriptions, 6-sentence paragraphs, one instruction per sentence; aim for most of it, not all. Diagrams over prose for flows. ASD-STE100 itself is copyrighted, so the rules are in our own words |
| [GitHub: creating diagrams](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams) | Mermaid renders in Markdown files and PRs |
| [Dependabot options reference](https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-options-reference), [dependabot/fetch-metadata](https://github.com/dependabot/fetch-metadata) | Weekly schedule, groups by update type, `commit-message` prefix, cooldown for version updates only; read-only token on Dependabot `pull_request` runs |
