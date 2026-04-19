<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# "  agent-sdk-dev @ claude-plugins-official

Scope: user
Claude Agent SDK Development Plugin

Author: Anthropic
Status: Enabled

Installed components:
• Commands: new-sdk-app
• Agents: agent-sdk-verifier-py, agent-sdk-verifier-ts"

In Claude Code, what are the best use cases for this? How do I get maximum value from it?

The agent-sdk-dev plugin equips Claude Code with tools for developing applications using the Claude Agent SDK. It provides a command for scaffolding projects and agents for validation in Python and TypeScript.

## Best Use Cases

- **Project Scaffolding**: Use `/new-sdk-app` to interactively set up new Agent SDK apps, handling boilerplate for Python or TypeScript projects with tools, hooks, and configurations.[^1_1][^1_2]
- **Code Validation**: Invoke `agent-sdk-verifier-py` or `agent-sdk-verifier-ts` to check SDK apps against best practices, catching issues in agent loops, tool definitions, permissions, and MCP integrations early.[^1_2][^1_1]
- **SDK Prototyping**: Build custom agents that mimic Claude Code's capabilities (e.g., file editing, bash execution) for standalone apps or embedding in SaaS products.[^1_3][^1_1]
- **Plugin Development**: Test SDK-based plugins locally before sharing, leveraging verifiers for hooks, skills, and commands.[^1_4][^1_1]


## Maximizing Value

Integrate it into your workflow by starting sessions with `/new-sdk-app` for quick prototypes, then running verifiers iteratively during development. Combine with your multi-terminal setup and git worktrees for parallel Python/TS validation, and use MCP servers (like your Tavily/Serper) in scaffolded apps for enhanced agentic flows.[^1_3][^1_2]

Configure in `.claude/settings.json` for project persistence:

```
{
  "plugins": ["agent-sdk-dev@claude-plugins-official"]
}
```

This aligns with your agentic CLI optimization by accelerating SDK experiments without manual boilerplate.[^1_2]
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_16][^1_17][^1_18][^1_19][^1_20][^1_21][^1_22][^1_5][^1_6][^1_7][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://platform.claude.com/docs/en/agent-sdk/overview

[^1_2]: https://github.com/anthropics/claude-code/blob/main/plugins/README.md

[^1_3]: https://platform.claude.com/docs/en/agent-sdk/plugins

[^1_4]: https://claudepluginhub.com/plugins/syeeel-agent-sdk-dev-plugins-agent-sdk-dev

[^1_5]: https://www.reddit.com/r/ClaudeAI/comments/1rallfy/should_i_be_building_my_own_coding_agent_with/

[^1_6]: https://www.datacamp.com/tutorial/how-to-use-claude-agent-sdk

[^1_7]: https://skywork.ai/blog/claude-agent-sdk-use-cases-2025/

[^1_8]: https://www.youtube.com/watch?v=MG9K1odJgw0

[^1_9]: https://platform.claude.com/docs/en/agent-sdk/skills

[^1_10]: https://dev.to/rajeshroyal/claude-agent-sdk-build-agents-that-work-like-claude-code-50ln

[^1_11]: https://www.youtube.com/watch?v=TqC1qOfiVcQ

[^1_12]: https://blog.bjdean.id.au/2025/11/embedding-claide-code-sdk-in-applications/

[^1_13]: https://github.com/anthropics/claude-agent-sdk-python

[^1_14]: https://www.youtube.com/watch?v=jNpH_hOFvg4

[^1_15]: https://www.reddit.com/r/ClaudeAI/comments/1r4tk3u/there_are_28_official_claude_code_plugins_most/

[^1_16]: https://www.youtube.com/watch?v=dVfW6Xsx2H8

[^1_17]: https://www.firecrawl.dev/blog/best-claude-code-plugins

[^1_18]: https://lobehub.com/skills/melodic-software-claude-code-plugins-agent-sdk-development

[^1_19]: https://platform.claude.com/docs/en/agent-sdk/typescript

[^1_20]: https://www.reddit.com/r/Anthropic/comments/1p4hb5d/valid_criticism_the_shift_from_claude_to_gemini_3/

[^1_21]: https://community.tmpdir.org/t/claude-claude-code/1534

[^1_22]: https://platform.claude.com/docs/en/agent-sdk/hosting


---

# How to use new-sdk-app command

The `new-sdk-app` command from the agent-sdk-dev plugin scaffolds new Claude Agent SDK projects interactively in Claude Code. It handles setup for Python or TypeScript, installs dependencies, and runs initial verification.[^2_1][^2_2]

## Usage Steps

Run it directly in a Claude Code session (plugin must be enabled).

1. Type `/new-sdk-app [project-name]` or just `/new-sdk-app` (name optional).[^2_1]
2. Answer interactive prompts:
    - Language: TypeScript or Python.
    - Project name (defaults to provided or "my-sdk-app").
    - Agent type: Coding, business, custom.
    - Starting point: Minimal, basic, or example-based.
    - Package manager: npm/yarn/pnpm (TS) or pip/poetry (Py).[^2_2][^2_1]
3. Claude creates the project folder, files (e.g., `agent.ts/py`, `.env.example`, `.gitignore`), installs SDK, validates syntax/types, and verifies with `agent-sdk-verifier-py/ts`.[^2_1]

## Example Output

After prompts, expect a new directory like `my-project/` with runnable agent code. Test by running `npm run dev` (TS) or `python main.py` (Py).[^2_1]

## Tips for Value

Use in a git worktree for isolation, then verify iteratively with "Verify my Agent SDK application". Integrates seamlessly with your MCP servers and multi-LLM prompts for custom agent prototyping.[^2_2][^2_1]
<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15][^2_3][^2_4][^2_5][^2_6][^2_7][^2_8][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://self.md/skills/anthropics-claude-code-plugins/agent-sdk-dev/

[^2_2]: https://claude.com/plugins/agent-sdk-dev

[^2_3]: https://platform.claude.com/docs/en/agent-sdk/overview

[^2_4]: https://code.claude.com/docs/en/cli-reference

[^2_5]: https://www.producttalk.org/how-to-use-claude-code-features/

[^2_6]: https://code.claude.com/docs/en/overview

[^2_7]: https://www.datacamp.com/tutorial/how-to-use-claude-agent-sdk

[^2_8]: https://nader.substack.com/p/the-complete-guide-to-building-agents

[^2_9]: https://aiengineerguide.com/blog/claude-code-sdk/

[^2_10]: https://www.youtube.com/watch?v=sCIS05Qt79Y

[^2_11]: https://www.youtube.com/watch?v=yGU1gHHItDA

[^2_12]: https://www.youtube.com/watch?v=CY8_Mm3lfk4

[^2_13]: https://www.kdnuggets.com/getting-started-with-the-claude-agent-sdk

[^2_14]: https://www.youtube.com/watch?v=dVfW6Xsx2H8

[^2_15]: https://learn.microsoft.com/en-us/microsoft-365-copilot/extensibility/create-deploy-agents-sdk

