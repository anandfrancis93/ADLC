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

## Conventions (read in full on 22 Oct 2026)

| Source | What the ADLC takes from it |
| --- | --- |
| [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/) | PR title format; `feat`/`fix`/`!` map to SemVer MINOR/PATCH/MAJOR; squash workflow (FAQ) |
| [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html) | Version numbers, declared public API, start at 0.1.0, released versions never change, `v` only in tags |
| [Common Changelog](https://common-changelog.org/) | CHANGELOG.md format, written at release time, no Unreleased section, commit and PR references, `**Breaking:**` prefix. Its section 4.2 calls Conventional Commits an antipattern; see [commits-and-releases.md](commits-and-releases.md) |
| [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) | Common Changelog's parent. Read to compare; the ADLC follows the stricter Common Changelog |
| [DESIGN.md](https://github.com/google-labs-code/design.md), Google Labs, Apache 2.0, format version alpha | Optional design file for UI repos and its `lint` command |
| [Version your app](https://developer.android.com/studio/publish/versioning), Android Developers | `versionCode` must increase per release; `versionName` is a free string shown to users |
