<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# " claude-code-setup @ claude-plugins-official

Scope: user
Version: 1.0.0
Analyze codebases and recommend tailored Claude Code automations such as hooks, skills, MCP servers, and subagents.

Author: Anthropic
Status: Enabled

Installed components:
• Skills: claude-automation-recommender"

In claude code, what are the best use cases for this?  How do I get value from it?

Claude Automation Recommender is a “workflow architect” for Claude Code: it reads your repo and tells you which hooks, skills, MCP servers, and subagents are actually worth wiring up for that specific stack.[^1][^2][^3]

## What this thing actually does

- Inspects the repo in a read‑only way using glob/grep and config detection (e.g. `package.json`, `pyproject.toml`, `go.mod`, framework files).[^3][^1]
- Classifies the project (language, framework, tooling) and then proposes a small set of high‑value automations per category: hooks, subagents, skills, plugins, MCP servers.[^2][^1][^3]
- Outputs concrete suggestions with rationale and implementation notes; it does not modify files, you (or Claude) implement the wiring afterward.[^1][^3]

Think of it as a targeted checklist of “if you only add 3–5 automations to this repo, make them these.”

## Best use cases in Claude Code

- **New repo or new stack**
    - Point Claude at the repo and run the skill to bootstrap a Claude Code setup that isn’t generic (e.g. monorepo with mixed TS/Go, or a weird framework combo).[^3][^1]
    - Use its suggestions as the initial `~/.claude/skills/`, hooks, and MCP list instead of guessing what to wire up.
- **Audit/upgrade an existing Claude Code setup**
    - When you’ve been adding hooks and skills ad‑hoc, run it to see “what’s missing” (e.g. test-on-edit hooks, security subagents, dependency-review flows).[^2][^3]
    - Good trigger points: after adding a new language, migrating build tooling, or introducing a big dependency (e.g. Prisma, LangChain, Next.js).
- **Designing opinionated project templates**
    - Run it over a “golden” repo and turn its recommendations into baked-in `.claude` config for future projects (starter hooks, standard MCP, default subagents).[^1][^2]
    - Especially useful if you want a consistent Claude Code experience across many services/microservices.
- **Choosing MCP servers that actually matter**
    - Instead of browsing MCP marketplaces blindly, you get a curated list based on detected tech: DB tools for ORM projects, HTTP/API tools for service repos, browser/research tools for data projects, etc.[^4][^2][^1]
- **Guiding subagent / team design**
    - Use its “subagent” recommendations as a blueprint for how to split work (e.g. test-runner agent, security agent, docs agent) and then implement teams around that.[^5][^2][^1]


## How to get concrete value from it

Here’s a practical loop tailored to heavy Claude Code use:

1. **Run it on a repo you care about**
    - In Claude Code, open the project and invoke the skill (e.g. via its named skill command from the plugin; exact slash name depends on how it’s exposed, but it’s a read‑only “analyze repo and propose automations” action).[^2][^3][^1]
2. **Pick 1–2 automations per category, not everything**
    - For each of: hooks, skills, MCP servers, subagents, choose the top one or two that would remove the most pain in your current workflow (format/lint on edit, pre‑commit tests, dep‑update helper, etc.).[^3][^1][^2]
3. **Ask Claude Code to implement the chosen items**
    - For each recommendation: paste it back to Claude and say “implement this as a hook/skill/MCP config for this repo,” letting it generate `.claude/hooks`, skill markdown, or `.mcp.json` entries.[^6][^1][^2]
4. **Bake the winners into user‑scope if they’re generally useful**
    - Once something proves itself (e.g. a security scan subagent or log‑analysis skill), promote it from project scope into user‑scope so all future repos benefit.[^7][^6][^2]
5. **Re‑run when the architecture changes**
    - After big shifts (new language, new framework, infra changes), run the skill again to refresh the automation roadmap.[^1][^3]

## Example scenarios where it shines

- **Polyglot monorepo (TS + Python + infra)**
    - It can recommend language‑specific hooks and MCPs (node tooling, Python test runners, infra scanners) instead of you manually curating per‑stack automations.[^2][^3][^1]
- **Security‑sensitive repo**
    - Expect suggestions like pre‑commit secrets scanners, subagents dedicated to security review, and MCP connections to SAST/dep‑vuln tools.[^3][^1][^2]
- **Data/ML project**
    - Likely to suggest MCP servers for databases, notebooks, and data warehouses, plus skills for repeatable evaluation or report generation workflows.[^4][^1][^2]

If you want, describe one of your active repos (stack, size, pain points), and I can spell out the 5–10 highest‑leverage automations you should ask this skill to design.
<span style="display:none">[^10][^11][^12][^13][^14][^15][^8][^9]</span>

<div align="center">⁂</div>

[^1]: https://lobehub.com/skills/philoserf-claude-code-setup-claude-automation-recommender

[^2]: https://mcpmarket.com/tools/skills/claude-automation-recommender-3

[^3]: https://mcpmarket.com/tools/skills/claude-automation-recommender-1

[^4]: https://aimaker.substack.com/p/what-are-claude-skills-ai-workflow-automation

[^5]: https://okhlopkov.com/claude-code-setup-mcp-hooks-skills-2026/

[^6]: https://github.com/anthropics/claude-code/blob/main/plugins/README.md

[^7]: https://code.claude.com/docs/en/discover-plugins

[^8]: https://github.com/anthropics/claude-plugins-official

[^9]: https://code.claude.com/docs/en/plugins

[^10]: https://www.reddit.com/r/ClaudeAI/comments/1r4tk3u/there_are_28_official_claude_code_plugins_most/

[^11]: https://www.anthropic.com/news/enabling-claude-code-to-work-more-autonomously

[^12]: https://www.datacamp.com/tutorial/how-to-build-claude-code-plugins

[^13]: https://www.anthropic.com/learn/build-with-claude

[^14]: https://code.claude.com/docs/en/setup

[^15]: https://www.reddit.com/r/ClaudeAI/comments/1qcwckg/the_complete_guide_to_claude_code_v2_claudemd_mcp/

