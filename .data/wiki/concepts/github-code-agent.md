---
title: "GitHub Code Agent"
created: 2026-08-10
source: nlm-sync-2026-08-10
tags: [nlm-synced, reference, github]
summary: >
  A category of AI coding agents built on GitHub, exemplified by projects such as code_puppy (mpfaffenberger/code_puppy) and kuutsav/kon, that operate locally in a terminal to read files, search codebases, edit files, and execute shell commands via tool-calling interfaces. These agents package model a
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
provenance_status: complete_4_hop
sources:
  - "NotebookLM notebook f5f8b2fa-c0ba-4d1a-acc2-02cb13a65ee2" ([INGESTED] - ext-The Renaissance of the Terminal, synced 2026-08-10)
  - "Python Advanced AI Agent Tutorial - LangGraph, LangChain, Firecrawl & More!" (https://www.youtube.com/watch?v=xekw62yQu14, transcript synced 2026-08-10)
  - "Anatomy of a Textual User Interface - Textual" (https://textual.textualize.io/blog/2024/09/15/anatomy-of-a-textual-user-interface/, transcript synced 2026-08-10)
  - "Textualize/rich: Rich is a Python library for rich text and beautiful formatting in the terminal. - GitHub" (https://github.com/Textualize/rich, transcript synced 2026-08-10)
  - "open-thoughts/OpenThoughts-Agent: Data recipes and robust infrastructure for training AI agents - GitHub" (https://github.com/open-thoughts/OpenThoughts-Agent, transcript synced 2026-08-10)
  - "This example demonstrates how to design a PydanticAI agent workflow where the LLM must call external tools instead of solving tasks independently. The CodeBreaker agent first retrieves an encrypted text but lacks decryption capabilities, forcing it to call the DecryptText agent. Additionally, a result validator ensures that decryption occurs, preventing the LLM from bypassing the intended workflow. - GitHub Gist" (https://gist.github.com/ishswar/53a15796fe1ec290ceab3cb9d24b15cc, transcript synced 2026-08-10)
  - "kuutsav/kon: Kon is a minimal coding agent (and also a ... - GitHub" (https://github.com/kuutsav/kon, transcript synced 2026-08-10)
  - "kevinelliott/agentpipe: A CLI/TUI app that orchestrates multi ... - GitHub" (https://github.com/kevinelliott/agentpipe, transcript synced 2026-08-10)
  - "awesome-python/README.md at main - GitHub" (https://github.com/dylanhogg/awesome-python/blob/main/README.md, transcript synced 2026-08-10)
  - "Python Textual: Build Beautiful UIs in the Terminal" (https://realpython.com/python-textual/, transcript synced 2026-08-10)
  - "mpfaffenberger/code_puppy: Agentic AI for writing code - GitHub" (https://github.com/mpfaffenberger/code_puppy, transcript synced 2026-08-10)
  - "together-cookbook/Agents/PydanticAI/PydanticAI_Agents.ipynb at main - GitHub" (https://github.com/togethercomputer/together-cookbook/blob/main/Agents/PydanticAI/PydanticAI_Agents.ipynb, transcript synced 2026-08-10)
  - "This pattern demonstrates how to implement advanced Pydantic AI features on AWS serverless architecture, including basic synchronous agents, real-time streaming responses, and multi-agent orchestration with structured outputs. - GitHub" (https://github.com/aws-samples/sample-pydantic-ai-streaming-rag-multiagent, transcript synced 2026-08-10)
  - "pproenca/agent-tui: TUI automation for AI agents. Control ... - GitHub" (https://github.com/pproenca/agent-tui, transcript synced 2026-08-10)
  - "generative-ai/gemini/agents/research-multi-agents/intro_research_multi_agents_gemini_2_0.ipynb at main - GitHub" (https://github.com/GoogleCloudPlatform/generative-ai/blob/main/gemini/agents/research-multi-agents/intro_research_multi_agents_gemini_2_0.ipynb, transcript synced 2026-08-10)
  - "pydantic/pydantic-ai-temporal-example - GitHub" (https://github.com/pydantic/pydantic-ai-temporal-example, transcript synced 2026-08-10)
provenance:
  chain:
    - level: concept
      id: github-code-agent
    - level: notebook
      id: f5f8b2fa-c0ba-4d1a-acc2-02cb13a65ee2
      title: [INGESTED] - ext-The Renaissance of the Terminal
      url: https://notebooklm.google.com/notebook/f5f8b2fa-c0ba-4d1a-acc2-02cb13a65ee2
    - level: cluster
      id: 0
      name: github-code-agent
    - level: source_url
      url: https://www.youtube.com/watch?v=xekw62yQu14
      title: Python Advanced AI Agent Tutorial - LangGraph, LangChain, Firecrawl & More!
    - level: source_url
      url: https://textual.textualize.io/blog/2024/09/15/anatomy-of-a-textual-user-interface/
      title: Anatomy of a Textual User Interface - Textual
    - level: source_url
      url: https://github.com/Textualize/rich
      title: Textualize/rich: Rich is a Python library for rich text and beautiful formatting in the terminal. - GitHub
    - level: source_url
      url: https://github.com/open-thoughts/OpenThoughts-Agent
      title: open-thoughts/OpenThoughts-Agent: Data recipes and robust infrastructure for training AI agents - GitHub
    - level: source_url
      url: https://gist.github.com/ishswar/53a15796fe1ec290ceab3cb9d24b15cc
      title: This example demonstrates how to design a PydanticAI agent workflow where the LLM must call external tools instead of solving tasks independently. The CodeBreaker agent first retrieves an encrypted text but lacks decryption capabilities, forcing it to call the DecryptText agent. Additionally, a result validator ensures that decryption occurs, preventing the LLM from bypassing the intended workflow. - GitHub Gist
    - level: source_url
      url: https://github.com/kuutsav/kon
      title: kuutsav/kon: Kon is a minimal coding agent (and also a ... - GitHub
    - level: source_url
      url: https://github.com/kevinelliott/agentpipe
      title: kevinelliott/agentpipe: A CLI/TUI app that orchestrates multi ... - GitHub
    - level: source_url
      url: https://github.com/dylanhogg/awesome-python/blob/main/README.md
      title: awesome-python/README.md at main - GitHub
    - level: source_url
      url: https://realpython.com/python-textual/
      title: Python Textual: Build Beautiful UIs in the Terminal
    - level: source_url
      url: https://github.com/mpfaffenberger/code_puppy
      title: mpfaffenberger/code_puppy: Agentic AI for writing code - GitHub
    - level: source_url
      url: https://github.com/togethercomputer/together-cookbook/blob/main/Agents/PydanticAI/PydanticAI_Agents.ipynb
      title: together-cookbook/Agents/PydanticAI/PydanticAI_Agents.ipynb at main - GitHub
    - level: source_url
      url: https://github.com/aws-samples/sample-pydantic-ai-streaming-rag-multiagent
      title: This pattern demonstrates how to implement advanced Pydantic AI features on AWS serverless architecture, including basic synchronous agents, real-time streaming responses, and multi-agent orchestration with structured outputs. - GitHub
    - level: source_url
      url: https://github.com/pproenca/agent-tui
      title: pproenca/agent-tui: TUI automation for AI agents. Control ... - GitHub
    - level: source_url
      url: https://github.com/GoogleCloudPlatform/generative-ai/blob/main/gemini/agents/research-multi-agents/intro_research_multi_agents_gemini_2_0.ipynb
      title: generative-ai/gemini/agents/research-multi-agents/intro_research_multi_agents_gemini_2_0.ipynb at main - GitHub
    - level: source_url
      url: https://github.com/pydantic/pydantic-ai-temporal-example
      title: pydantic/pydantic-ai-temporal-example - GitHub
relations:
  - target: wiki/concepts/agentpipe-(kevinelliott/agentpipe)---multi-agent-orchestration-cli.md
    type: related
  - target: wiki/concepts/textual-tui-framework---underlying-terminal-ui-toolkit.md
    type: related
  - target: wiki/concepts/rich-library---terminal-formatting-backbone.md
    type: related
---

# GitHub Code Agent

## Decision context

**Definition:** A category of AI coding agents built on GitHub, exemplified by projects such as code_puppy (mpfaffenberger/code_puppy) and kuutsav/kon, that operate locally in a terminal to read files, search codebases, edit files, and execute shell commands via tool-calling interfaces. These agents package model access, MCP servers, and reusable skills into installable CLIs, distinct from agent orchestration frameworks or training/infrastructure stacks.

Synthesized from **15 contributing transcripts** in NotebookLM notebook *[INGESTED] - ext-The Renaissance of the Terminal*, clustered into the "github-code-agent" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- code_puppy is installed via `uvx code-puppy -i` and exposes an interactive TUI for code generation tasks
- Kon is packaged globally with `uv tool install kon-coding-agent` and provides a CLI/TUI binary called `kon` with slash commands like `/login`, `/new`, `/resume`, `/model`, `/compact`, `/export`
- Kon's system prompt is about 215 tokens and tool definitions about 600 tokens, totaling under 1k tokens before conversation context
- Both agents load project guidelines from AGENTS.md files into the system prompt, supporting global (~/.kon/AGENTS.md) and project-level scopes
- Skills are reusable instruction packs loaded from project (.kon/skills/) or global (~/.kon/skills/) directories, each with a SKILL.md front matter file
- Kon's required tools include read, edit, write, bash, grep, and find; binary helpers fd and ripgrep are auto-downloaded if missing, with eza optional
- Kon's supported providers include github-copilot, openai, openai-codex, openai-responses, and zhipu, configured via CLI flags like --provider, --api-key, --base-url
- code_puppy integrates models.dev to browse and add models from 65+ providers via the /add_model command, with offline fallback to a bundled database
- code_puppy supports round-robin model distribution to spread load across multiple API keys, controlled by a rotate_every parameter
- code_puppy supports DBOS durable execution when enabled, checkpointing agent inputs, LLM responses, MCP calls, and tool calls for recovery
- code_puppy enables custom JSON agents created via Agent Creator (/agent agent-creator) with schema-validated name, description, system_prompt, and tools fields
- code_puppy enforces a 600-line max per file for its default Code-Puppy agent and follows YAGNI/SRP/DRY principles
- Kon's configuration lives at ~/.kon/config.toml with knobs like llm.default_provider, llm.default_model, llm.system_prompt, and compaction.buffer_tokens
- Sessions in Kon are append-only JSONL files stored under ~/.kon/sessions/, resumable via /resume, --continue, or --resume flags

## Verifiable values

| Name | Value |
|---|---|
| kon system prompt tokens | `~215 tokens` |
| kon tool definition tokens | `~600 tokens` |
| kon total pre-context tokens | `under 1k tokens` |
| kon file count comparison vs opencode | `108 vs 4107 files` |
| kon file count comparison vs pi-mono | `108 vs 740 files` |
| kon queued prompt capacity | `up to 5 queued prompts` |
| code_puppy file limit per file | `600 lines` |
| code_puppy supported providers via models.dev | `65+ providers, >1000 model offerings` |
| code_puppy default model config extras | `timeout: 60, max_retries: 3` |
| code_puppy DBOS default database | `dbos_store.sqlite in config directory` |
| Kon CLI flags | `--model, --provider, --api-key, --base-url, --continue, --resume` |
| Kon tab autocomplete paths | `~, ./, ../, absolute, quoted paths` |

## Related concepts

- [[agentpipe-(kevinelliott/agentpipe)---multi-agent-orchestration-cli]] — AgentPipe (kevinelliott/agentpipe) - multi-agent orchestration CLI
- [[textual-tui-framework---underlying-terminal-ui-toolkit]] — Textual TUI framework - underlying terminal UI toolkit
- [[rich-library---terminal-formatting-backbone]] — Rich library - terminal formatting backbone
- [[pydantic-ai---structured-output-agent-framework]] — Pydantic AI - structured-output agent framework
- [[dbos-durable-execution---checkpointing-integration]] — DBOS durable execution - checkpointing integration
- [[harbor---containerized-eval-sandbox-backend]] — Harbor - containerized eval sandbox backend
- [[openthoughts-agent---data-recipes-for-training-agentic-models]] — OpenThoughts-Agent - data recipes for training agentic models

## Citations (from contributing transcripts)

- **Claim:** code_puppy is installed via uvx code-puppy -i
  - Source: mpfaffenberger/code_puppy: Agentic AI for writing code - GitHub (`973b6a1d-132c-4a61-80e4-9e60fe185e61`)
  - Context: Quick start
uvx code-puppy -i
- **Claim:** Kon is a minimal coding agent with about 215 tokens for the system prompt and around 600 tokens for tool definitions, under 1k tokens before conversation context
  - Source: kuutsav/kon: Kon is a minimal coding agent (and also a ... - GitHub (`7afea346-e9a2-45b9-8e62-cd98ef1bb6a6`)
  - Context: Kon is a minimal coding agent with a tiny harness: about 215 tokens for the system prompt and around 600 tokens for tool definitions – so under 1k tokens before conversation context.
- **Claim:** Kon is installed globally with uv tool install kon-coding-agent
  - Source: kuutsav/kon: Kon is a minimal coding agent (and also a ... - GitHub (`7afea346-e9a2-45b9-8e62-cd98ef1bb6a6`)
  - Context: Install (recommended)
uv tool install kon-coding-agent
- **Claim:** Kon's required tools include read, edit, write, bash, grep, and find
  - Source: kuutsav/kon: Kon is a minimal coding agent (and also a ... - GitHub (`7afea346-e9a2-45b9-8e62-cd98ef1bb6a6`)
  - Context: Tool Purpose read Read file contents (pagination for large files, image support) edit Surgical find-and-replace edits write Create or overwrite files bash Execute shell commands grep Search file contents with regex find Find files by glob pattern
- **Claim:** Kon's slash commands include /login, /new, /resume, /model, /compact, /export
  - Source: kuutsav/kon: Kon is a minimal coding agent (and also a ... - GitHub (`7afea346-e9a2-45b9-8e62-cd98ef1bb6a6`)
  - Context: /new   Start a new conversation and reload project context/skills /resume   Browse and restore a saved session /model   Switch model via interactive picker /session   Show session metadata and token stats /compact   Compact the current conversation immediately /export   Export current session to HTML /copy   Copy last assistant response to clipboard /login   Authenticate with a provider /logout   Log out from a provider /clear   Clear current conversation /help   Show commands and keybindings /q
- **Claim:** Kon loads project guidelines from AGENTS.md (or CLAUDE.md) into the system prompt
  - Source: kuutsav/kon: Kon is a minimal coding agent (and also a ... - GitHub (`7afea346-e9a2-45b9-8e62-cd98ef1bb6a6`)
  - Context: Kon loads project guidelines from AGENTS.md (or CLAUDE.md) files into the system prompt:
Global: ~/.kon/AGENTS.md
Ancestor directories from git root (or home) down to current working directory
- **Claim:** Skills are reusable instruction packs loaded from project or global directories, each with a SKILL.md front matter file
  - Source: kuutsav/kon: Kon is a minimal coding agent (and also a ... - GitHub (`7afea346-e9a2-45b9-8e62-cd98ef1bb6a6`)
  - Context: Skills are reusable instruction packs loaded from:
Project: .kon/skills/
Global: ~/.kon/skills/
Each skill has a SKILL.md file with front matter
- **Claim:** code_puppy integrates models.dev to browse and add models from 65+ providers via /add_model command
  - Source: mpfaffenberger/code_puppy: Agentic AI for writing code - GitHub (`973b6a1d-132c-4a61-80e4-9e60fe185e61`)
  - Context: Code Puppy integrates with models.dev to let you browse and add models from 65+ providers with a single command:
/add_model
- **Claim:** code_puppy supports round-robin model distribution with a rotate_every parameter
  - Source: mpfaffenberger/code_puppy: Agentic AI for writing code - GitHub (`973b6a1d-132c-4a61-80e4-9e60fe185e61`)
  - Context: The rotate_every parameter controls how many requests are made to each model before rotating to the next one. In this example, the round-robin model will use each Qwen model for 5 consecutive requests before moving to the next model in the sequence.
- **Claim:** code_puppy supports DBOS durable execution checkpointing agent inputs, LLM responses, MCP calls, and tool calls
  - Source: mpfaffenberger/code_puppy: Agentic AI for writing code - GitHub (`973b6a1d-132c-4a61-80e4-9e60fe185e61`)
  - Context: Code Puppy now supports DBOS durable execution. When enabled, every agent is automatically wrapped as a DBOSAgent, checkpointing key interactions (including agent inputs, LLM responses, MCP calls, and tool calls) in a database for durability and recovery.

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `f5f8b2fa-c0ba-4d1a-acc2-02cb13a65ee2`
(cluster `github-code-agent`). No claims are made
about local workspace implementation. Trigger words like
'mechanism', 'scanner', 'gate', 'hook', 'because' refer to concepts
discussed in the source videos, not to local code behavior.
Implementation path: wiki-yt/scripts/synthesize_subtopics.py
(LLM synthesis from transcripts — no local code inspected).

## What this means for our workspace

Synced from NotebookLM. Provenance chain (concept → notebook → cluster → URL) is in frontmatter; follow it back to the source material.

## Falsifier

If a re-sync of the source notebook produces a different definition or different values, this page should be updated (or marked as superseded). The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records when this page was last regenerated.

## Sources

- NotebookLM notebook [[INGESTED] - ext-The Renaissance of the Terminal](https://notebooklm.google.com/notebook/f5f8b2fa-c0ba-4d1a-acc2-02cb13a65ee2)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
