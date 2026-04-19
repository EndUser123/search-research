<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# " code-review @ claude-plugins-official

Scope: user
Automated code review for pull requests using multiple specialized agents with confidence-based scoring

Author: Anthropic
Status: Enabled

Installed components:
• Commands: code-review"

In Claude Code, what are the best use cases for this? How do I get maximum value from it?

The Claude Code "code-review" plugin from claude-plugins-official automates PR reviews using multiple specialized agents for perspectives like bug detection, CLAUDE.md compliance, git history analysis, previous PR comments, and code verification, with confidence scoring to filter noise.[^1][^2]

## Best Use Cases

- Solo development or small teams without human reviewers, providing an extra layer of scrutiny before pushing code.[^1]
- GitHub pull requests needing fast, parallel audits to catch high-confidence issues like security risks or bugs early.[^2]
- Pre-PR validation workflows to reduce cycle time, such as reviewing changes for tests, docs, or simplification.[^3]


## Maximizing Value

Run `/code-review` directly on a PR branch to trigger the full automated analysis, which posts filtered comments (threshold: 80 confidence) with GitHub links and line references.[^2][^1]
Customize via command config for focus areas like security or performance, and re-run after fixes to verify resolutions.[^3][^2]
Integrate into routine: review before commits/PRs, use parallel agents for speed, and combine with manual checks for production code.[^4][^3]
<span style="display:none">[^10][^11][^12][^13][^14][^15][^5][^6][^7][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://www.reddit.com/r/ClaudeAI/comments/1r4tk3u/there_are_28_official_claude_code_plugins_most/

[^2]: https://claude.com/plugins/code-review

[^3]: https://fasterthanlight.me/blog/post/claude-code-best-practices-for-local-code-review

[^4]: https://rosmur.github.io/claudecode-best-practices/

[^5]: https://github.com/anthropics/claude-plugins-official

[^6]: https://github.com/anthropics/claude-code/blob/main/plugins/code-review/README.md

[^7]: https://code.claude.com/docs/en/discover-plugins

[^8]: https://jangwook.net/en/blog/en/claude-code-plugins-complete-guide/

[^9]: https://composio.dev/blog/claude-code-plugin

[^10]: https://www.reddit.com/r/ClaudeCode/comments/1ph8n4h/claude_code_review_best_practices/

[^11]: https://www.firecrawl.dev/blog/best-claude-code-plugins

[^12]: https://agnost.ai/blog/claude-code-plugins-guide

[^13]: https://www.youtube.com/watch?v=n7iT5r0Sl_Y

[^14]: https://www.youtube.com/watch?v=tTlfUgZOL_0

[^15]: https://www.youtube.com/watch?v=3T6CATN2BNE

