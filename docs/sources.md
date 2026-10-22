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

## claude.dev articles (read on 22 Oct 2026)

The blog had 16 posts. The code review post is listed above.

| Source | What the ADLC takes from it |
| --- | --- |
| [How we made claude.ai 3x faster in two weeks](https://claude.dev/blog/how-we-made-claude-ai-faster/), Raymond Wang, Sam Attard, Issac G., 23 Sep 2026 | Retire ramp flags and keep kill switches; flaky-test proof by repeated runs on main and on the branch; before and after screenshots for user-visible changes |
| [The new rules of context engineering for Claude 5 generation models](https://claude.dev/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models/), Thariq Shihipar, 24 Jul 2026 | AGENTS.md holds gotchas, not what the file tree shows; after a model change, remove old workarounds and conflicting instructions |
| [Lessons from building Claude Code: How we use skills](https://claude.dev/blog/lessons-from-building-claude-code-how-we-use-skills/), Thariq Shihipar, 3 Jun 2026 | Skills join the Retire list, valued by use; gotchas over the obvious |
| [A harness for every task: dynamic workflows in Claude Code](https://claude.dev/blog/a-harness-for-every-task-dynamic-workflows-in-claude-code/), Thariq Shihipar, Sid Bidasaria, 2 Jun 2026 | Review in a fresh session, because a model favours its own work; agents that read public content take no write actions |
| [Claude Code in the cloud](https://claude.dev/blog/claude-code-in-the-cloud/), Addy Osmani, 6 Oct 2026 | Each intent says when it is done and which check proves it; flaky-test proof by repeated runs |
| [Building effective agent automations](https://claude.dev/blog/building-effective-agent-automations/), Lance Martin, CJ Avilla, 8 Oct 2026 | A scheduled check that cannot run reports a failure, never zero findings; read-only tokens for scheduled agents |
| [Getting started with Claude Code mods](https://claude.dev/blog/getting-started-with-claude-code-mods/), Addy Osmani, 1 Oct 2026 | A tool-call hook is a safety net, not a hard block, so the hard block for `.adlc/protected` belongs in CI |
| [Building with Claude Sonnet 5.5](https://claude.dev/blog/building-with-claude-sonnet-5-5/), Addy Osmani, 28 Sep 2026 | A check that did not start, or only checked syntax, is not a pass; remove prompt workarounds after a model change |
| [What a task costs on Opus 5.5](https://claude.dev/blog/what-a-task-costs-on-opus-5-5/), Addy Osmani, 25 Sep 2026 | After a model change, remove ritual instructions such as verify-twice rules |
| [Getting the most out of Opus 5.5 in Claude and Claude Code](https://claude.dev/blog/getting-the-most-out-of-opus-5-5/), Addy Osmani, 22 Sep 2026 | Name the finish line; an Important finding says how to show it fails; delete "think carefully" lines |
| [Automating eval design and hillclimbing with Claude](https://claude.dev/blog/automating-eval-design-and-hillclimbing/), Lance Martin, 28 Sep 2026 | The judge should not be the model it judges, which backs "a different model is better still" in review |
| [Seeing like an agent](https://claude.dev/blog/seeing-like-an-agent/), Thariq Shihipar, 10 Apr 2026 | Revisit old scaffolding as models improve |

The model-change findings come from tests with Claude models only. CI
still enforces the rules that matter for every tool. Two posts were not used:
the HTML post (ADLC files are reviewed as Markdown diffs) and the prompt
caching post (agent harness design). Effort per stage (from
[Spending your effort](https://claude.dev/blog/spending-your-effort/), Thariq
Shihipar, 25 Sep 2026), eval rules and ratchet checks wait until a repo needs
them. The page dates differ from the sitemap
for the six oldest posts; the table uses the page dates.
