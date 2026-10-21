# Sources

All four were read in full on 21 Oct 2026.

| Source | What the ADLC takes from it |
| --- | --- |
| [The AI-native SDLC playbook](https://claude.com/resources/articles/the-ai-native-sdlc-playbook), Anthropic, Louis Claxton, 21 Aug 2026 | Main source. Six stages (Plan, Design, Build, Test, Deploy, Maintain), intent/spec/plan files, plan mode, skills backed by hooks, fast build hooks with heavy checks at commit or PR, failing test first, REVIEW.md with Important vs Nit and a nit cap, rollback, monitoring that writes new intents |
| [How the Claude Code team does code review](https://claude.dev/blog/solving-code-review-at-anthropic/), Addy Osmani, Morgan Westlee Lunt, Qing Wang, 15 Oct 2026 | Risk tiers set by the change; review round cap; diff-only re-review; Pre-existing tag; no repeated findings; PR template with Testing, Risk, How to revert |
| [The Agent Development Lifecycle](https://architect.salesforce.com/docs/architect/fundamentals/guide/agent-development-lifecycle.html), Salesforce Architects (no date shown) | Layered testing, canary rollout, deploy separate from activation, rollback to last good version. It covers building an agent as a product |
| [The Agent Development Lifecycle has arrived on Cloudflare](https://blog.cloudflare.com/agent-development-lifecycle/), Brendan Irvine-Broque, 4 Aug 2026 | Lists Retire as an SDLC phase (no guidance); every change independently testable, releasable, observable, reversible; feature flag per change; CI cached by input files |

No source gives guidance on retiring rules or checks. The Retire stage extends
the playbook's monthly review tuning and its advice to replace evals that stop
discriminating.
