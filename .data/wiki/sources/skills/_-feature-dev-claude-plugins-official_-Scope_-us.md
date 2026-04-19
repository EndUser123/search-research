<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# " feature-dev @ claude-plugins-official

Scope: user
Comprehensive feature development workflow with specialized agents for codebase exploration, architecture design, and quality review

Author: Anthropic
Status: Enabled

Installed components:
• Commands: feature-dev
• Agents: code-architect, code-explorer, code-reviewer"

In Claude Code, what are the best use cases for this? How do I get maximum value from it?

The feature-dev plugin in Claude Code provides a structured 7-phase workflow for developing medium-complexity features, leveraging specialized agents like code-explorer, code-architect, and code-reviewer. It excels at tasks requiring codebase analysis, design decisions, and multi-file changes, outperforming ad-hoc prompting by enforcing checkpoints for human approval.[^1][^2][^3]

## Best Use Cases

- Adding new API endpoints, OAuth authentication, or business logic where scope includes validation, errors, and integrations—Phase 2 explores relevant code patterns automatically.[^3][^1]
- Building UI components or modules like notifications/pagination, as agents match existing styles and propose balanced designs in Phase 4.[^3]
- Prototyping features or extending unfamiliar codebases, using early phases for discovery and exploration without full implementation commitment.[^3]
- Avoid for trivial edits (e.g., typos) or massive refactors—break large ones into bounded stages instead.[^1][^3]


## Maximizing Value

Start from a clean repo state (commit/stash changes) and invoke with a concise description: `/feature-dev Add rate limiting to API endpoints`.[^1][^3]
Engage deeply in Phase 3 (clarifying questions on edges/performance) and Phase 4 (pick from 2-3 architecture options, e.g., reuse vs. clean design)—concrete answers prevent drift.[^3]
Maintain an up-to-date CLAUDE.md with conventions/tests; review Phase 6's 80%+ confidence issues before committing; run iteratively for multi-stage features.[^1][^3]


| Phase | Focus | Agent Used | Your Role |
| :-- | :-- | :-- | :-- |
| 1: Discovery | Clarify requirements | None | Approve problem statement |
| 2: Exploration | Map codebase/files | code-explorer (parallel) | Review findings |
| 3: Questions | Fill gaps (edges/auth) | None | Answer specifically |
| 4: Design | Propose approaches | code-architect (parallel) | Select option |
| 5: Implement | Code changes | None | N/A (post-approval) |
| 6: Review | Bugs/style/confidence-filtered issues | code-reviewer (parallel) | Decide fixes |
| 7: Summary | Docs/next steps | None | Final check[^3][^1] |

<span style="display:none">[^10][^11][^12][^13][^14][^15][^4][^5][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://www.reddit.com/r/ClaudeCode/comments/1pcxzln/the_featuredev_plugin_leveled_up_my_code/

[^2]: https://github.com/anthropics/claude-code/blob/main/plugins/README.md

[^3]: https://www.leanware.co/insights/how-to-use-feature-dev-claude-code

[^4]: https://github.com/anthropics/claude-code/tree/main/plugins/feature-dev

[^5]: https://code.claude.com/docs/en/plugins

[^6]: https://composio.dev/blog/claude-code-plugin

[^7]: https://github.com/anthropics/claude-plugins-official

[^8]: https://www.reddit.com/r/ClaudeAI/comments/1k5slll/anthropics_guide_to_claude_code_best_practices/

[^9]: https://code.claude.com/docs/en/plugins-reference

[^10]: https://blog.devgenius.io/the-claude-code-plugin-starter-stack-for-web-developers-f2d85b0335fa

[^11]: https://code.claude.com/docs/en/common-workflows

[^12]: https://www-cdn.anthropic.com/58284b19e702b49db9302d5b6f135ad8871e7658.pdf

[^13]: https://www.youtube.com/watch?v=-KusSduAP1A

[^14]: https://claudemarketplaces.com

[^15]: https://www.reddit.com/r/ClaudeAI/comments/1r6uaf9/a_thread_for_use_cases_of_claude_code/

