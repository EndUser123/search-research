<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# skill-creator @ claude-plugins-official

Scope: user
Create new skills, improve existing skills, and measure skill performance. Use when users want to create a skill from
scratch, update or optimize an existing skill, run evals to test a skill, or benchmark skill performance with variance
analysis.

Author: Anthropic
Status: Enabled

Installed components:
• Skills: skill-creator

In Claude Code, what are the best use cases for this? How do I get maximum value from it?

The skill-creator from claude-plugins-official in Claude Code is an AI-powered toolkit for rapidly building, refining, and evaluating custom skills to extend Claude's capabilities in your workflows.  It shines in agentic development by automating SKILL.md generation, frontmatter optimization, and iterative improvements based on real usage.[^1_1][^1_2][^1_3]

## Top Use Cases

- **New skill creation from scratch**: Describe a workflow (e.g., "RCA debugging loop for Python monorepos") and let it generate a full skill folder with SKILL.md, description, triggers, and supporting files like examples or templates. Ideal for your multi-agent systems or hook integrations.[^1_3][^1_4]
- **Optimizing existing skills**: Feed in a failing SKILL.md or chat transcript with edge cases; it flags issues like vague triggers or over-invocation, then suggests refined versions with better auto-activation.[^1_3]
- **Performance evals and benchmarking**: Run variance analysis on skill outputs across test cases, measuring reliability in tasks like code review or prompt engineering—pairs with your TDD/verify loops.[^1_2]


## Maximizing Value

Invoke via `/skill-creator` or naturally ("Use skill-creator to build a skill for...") in Claude Code sessions.  Start with concrete examples from your transcripts (thousands available in your setup), iterate in 15-30 minutes per skill, and test in git worktrees for quick validation.[^1_1][^1_5][^1_3]

Chain with plugin-dev for full plugins or claudit for audits, and store in `~/.claude/skills/` for personal reuse across projects.  Focus on micro-skills (e.g., one for semantic search, one for graph-of-thoughts prompting) that compose via subagents for 50-70% workflow speedups.[^1_6][^1_1][^1_5]

Do you have a specific workflow or existing skill to create/optimize first?
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_16][^1_7][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://code.claude.com/docs/en/skills

[^1_2]: https://github.com/anthropics/claude-plugins-official/blob/main/plugins/skill-creator/skills/skill-creator/SKILL.md

[^1_3]: https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf

[^1_4]: https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/

[^1_5]: https://www.reddit.com/r/ClaudeAI/comments/1r3hr40/anthropic_released_32_page_detailed_guide_on/

[^1_6]: https://www.perplexity.ai/search/09823bfb-b98b-4e07-8361-154cc2114356

[^1_7]: https://www.youtube.com/watch?v=6EFOT6hjvAU

[^1_8]: https://www.youtube.com/watch?v=X3uum6W2xEI

[^1_9]: https://www.youtube.com/watch?v=sduaTkhIm_w

[^1_10]: https://www.reddit.com/r/ClaudeAI/comments/1qrlsly/everyones_hyped_on_skills_but_claude_code_plugins/

[^1_11]: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices

[^1_12]: https://scottspence.com/posts/how-to-make-claude-code-skills-activate-reliably

[^1_13]: https://support.claude.com/en/articles/12512180-use-skills-in-claude

[^1_14]: https://www.youtube.com/watch?v=zKBPwDpBfhs

[^1_15]: https://simonwillison.net/2025/Oct/16/claude-skills/

[^1_16]: https://www.youtube.com/watch?v=Ik-Xbz2hvM0

