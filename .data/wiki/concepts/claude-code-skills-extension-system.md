---
title: "Claude Code Skills Extension System"
created: 2026-08-10
source: nlm-sync-2026-08-10
tags: [nlm-synced, reference, claude]
summary: >
  Skills are prompt-based extension packages for Claude Code that teach the model to perform specific tasks in a repeatable, standardized way. Unlike built-in slash commands that execute fixed logic, skills are markdown-defined instruction sets that Claude orchestrates dynamically, supported by a prog
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
provenance_status: complete_4_hop
sources:
  - "NotebookLM notebook c8b07a4c-607c-4ddc-94be-688206daf737" ([INGESTED] - Claude Code x NotebookLM x Obsidian Research, synced 2026-08-10)
  - "Extend Claude with skills - Claude Code Docs" (https://code.claude.com/docs/en/skills, transcript synced 2026-08-10)
  - "GitHub - travisvn/awesome-claude-skills: A curated list of awesome Claude Skills, resources, and tools for customizing Claude AI workflows — particularly Claude Code" (https://github.com/travisvn/awesome-claude-skills, transcript synced 2026-08-10)
  - "GitHub - alirezarezvani/claude-skills: +192 Claude Code skills & agent plugins for Claude Code, Codex, Gemini CLI, Cursor, and 8 more coding agents — engineering, marketing, product, compliance, C-level advisory." (https://github.com/alirezarezvani/claude-skills, transcript synced 2026-08-10)
  - "How Claude Code works - Claude Code Docs" (https://code.claude.com/docs/en/how-claude-code-works, transcript synced 2026-08-10)
  - "ComposioHQ/awesome-claude-skills - GitHub" (https://github.com/ComposioHQ/awesome-claude-skills, transcript synced 2026-08-10)
  - "Orchestrate teams of Claude Code sessions" (https://code.claude.com/docs/en/agent-teams, transcript synced 2026-08-10)
  - "Claude Code Agent Teams: Setup & Usage Guide 2026" (https://claudefa.st/blog/guide/agents/agent-teams, transcript synced 2026-08-10)
  - "Create custom subagents - Claude Code Docs" (https://code.claude.com/docs/en/sub-agents, transcript synced 2026-08-10)
  - "Automate workflows with hooks - Claude Code Docs" (https://code.claude.com/docs/en/hooks-guide, transcript synced 2026-08-10)
  - "Claude Code overview - Claude Code Docs" (https://code.claude.com/docs/en/overview, transcript synced 2026-08-10)
  - "Hooks reference - Claude Code Docs" (https://code.claude.com/docs/en/hooks, transcript synced 2026-08-10)
  - "Best Practices for Claude Code - Claude Code Docs" (https://code.claude.com/docs/en/best-practices, transcript synced 2026-08-10)
provenance:
  chain:
    - level: concept
      id: claude-code-skills-extension-system
    - level: notebook
      id: c8b07a4c-607c-4ddc-94be-688206daf737
      title: [INGESTED] - Claude Code x NotebookLM x Obsidian Research
      url: https://notebooklm.google.com/notebook/c8b07a4c-607c-4ddc-94be-688206daf737
    - level: cluster
      id: 1
      name: claude-code-https
    - level: source_url
      url: https://code.claude.com/docs/en/skills
      title: Extend Claude with skills - Claude Code Docs
    - level: source_url
      url: https://github.com/travisvn/awesome-claude-skills
      title: GitHub - travisvn/awesome-claude-skills: A curated list of awesome Claude Skills, resources, and tools for customizing Claude AI workflows — particularly Claude Code
    - level: source_url
      url: https://github.com/alirezarezvani/claude-skills
      title: GitHub - alirezarezvani/claude-skills: +192 Claude Code skills & agent plugins for Claude Code, Codex, Gemini CLI, Cursor, and 8 more coding agents — engineering, marketing, product, compliance, C-level advisory.
    - level: source_url
      url: https://code.claude.com/docs/en/how-claude-code-works
      title: How Claude Code works - Claude Code Docs
    - level: source_url
      url: https://github.com/ComposioHQ/awesome-claude-skills
      title: ComposioHQ/awesome-claude-skills - GitHub
    - level: source_url
      url: https://code.claude.com/docs/en/agent-teams
      title: Orchestrate teams of Claude Code sessions
    - level: source_url
      url: https://claudefa.st/blog/guide/agents/agent-teams
      title: Claude Code Agent Teams: Setup & Usage Guide 2026
    - level: source_url
      url: https://code.claude.com/docs/en/sub-agents
      title: Create custom subagents - Claude Code Docs
    - level: source_url
      url: https://code.claude.com/docs/en/hooks-guide
      title: Automate workflows with hooks - Claude Code Docs
    - level: source_url
      url: https://code.claude.com/docs/en/overview
      title: Claude Code overview - Claude Code Docs
    - level: source_url
      url: https://code.claude.com/docs/en/hooks
      title: Hooks reference - Claude Code Docs
    - level: source_url
      url: https://code.claude.com/docs/en/best-practices
      title: Best Practices for Claude Code - Claude Code Docs
relations:
  - target: wiki/concepts/claude-code-subagents.md
    type: related
  - target: wiki/concepts/claude-code-hooks.md
    type: related
  - target: wiki/concepts/model-context-protocol-(mcp).md
    type: related
---

# Claude Code Skills Extension System

## Decision context

**Definition:** Skills are prompt-based extension packages for Claude Code that teach the model to perform specific tasks in a repeatable, standardized way. Unlike built-in slash commands that execute fixed logic, skills are markdown-defined instruction sets that Claude orchestrates dynamically, supported by a progressive disclosure architecture that loads metadata first and full content only when activated.

Synthesized from **12 contributing transcripts** in NotebookLM notebook *[INGESTED] - Claude Code x NotebookLM x Obsidian Research*, clustered into the "claude-code-https" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Skills use a progressive disclosure design: only skill metadata (name and description, ~100 tokens) is scanned for relevance, with full instruction content (up to 5000 tokens) loaded only when the skill is activated, so many skills can coexist without exhausting the context window.
- A skill is a directory containing a required SKILL.md file (YAML frontmatter plus markdown instructions) and optional template.md, examples/, and scripts/ (executable code such as Bash or Python) folders.
- Skill loading follows a hierarchy: Enterprise managed settings (highest), Personal (~/.claude/skills/, cross-project for that user), Project (.claude/skills/, repository-scoped), and Plugin (<plugin-name>/skills/, namespaced). Claude Code also auto-discovers skills nested in subdirectories such as packages/frontend/.skills/ within monorepos.
- YAML frontmatter parameters controlling behavior include: name (display name and slash-command, max 64 chars), description (decides auto-loading, truncated at 250 chars in menus), argument_hint, disable_model_invocation (forces manual invocation), user_invocable (hides from / menu), allowed_tools, model, effort (low/medium/high/max), context: fork (isolates execution in a subagent), agent, paths (glob patterns restricting activation), and shell.
- Skills support string substitution variables in SKILL.md: $ARGUMENTS for all arguments, $ARGUMENTS[N] for indexed access, ${CLAUDE_SESSION_ID}, and ${CLAUDE_SKILL_DIR}.
- Dynamic context injection via the !`command` syntax runs a shell command before the skill executes; the command's output replaces the placeholder so Claude receives live data rather than the literal command string.
- Subagent execution via context: fork runs the skill's instructions as a prompt to an isolated subagent, which returns only its summary to the main conversation, preserving main context cleanliness.
- Including the word 'ultrathink' inside skill content forces use of extended thinking models for that skill.
- To keep SKILL.md lean (recommended under 500 lines), supporting reference material, examples, and documentation are placed in separate files inside the skill directory; Claude references them only when needed.
- Bundled skills ship with Claude Code in every session and include /batch (decomposes work into 5–30 independent units with one background agent each), /simplify (spawns three parallel review agents over recent changes), /loop [interval] (polling on a timer), and /debug (enables session debug logging).
- Skills are installed in Claude Code via /plugin marketplace add [repository] or /plugin add /path/to/skill; on Claude.ai they are toggled in Settings > Capabilities, with Team/Enterprise accounts requiring admin enablement organization-wide.
- Skills are accessible across Claude.ai, Claude Code, and the Claude API via the /v1/skills endpoint.
- Skills are distinct from MCP (which connects external data sources and APIs), distinct from system prompts (skills are reusable, version-controlled, shareable, composable), and distinct from Projects (which provide persistent background knowledge within a workspace).
- Skills can be loaded and composed together automatically as Claude determines relevance to the task; there is currently no official marketplace for paid skills, though Anthropic has indicated plans for a community-driven marketplace.
- Security warning from the sources: skills can execute arbitrary code in Claude's environment, so users should only install skills from trusted sources and review SKILL.md and all scripts before enabling.
- Skill creation best practices include keeping descriptions concise for discovery, writing instructions specifically for the Claude model (not the end-user), using clear actionable instructions, providing edge-case examples, listing required dependencies, and including explicit error handling guidance.
- The skill-creator is an interactive tool that guides users through building new skills via a Q&A workflow.

## Verifiable values

| Name | Value |
|---|---|
| Metadata scan token cost | `~100 tokens per skill for relevance scanning` |
| Full content token cost when activated | `up to 5000 tokens` |
| name field max length | `64 characters` |
| description field menu truncation | `250 characters` |
| Recommended SKILL.md size | `under 500 lines` |
| Auto memory (MEMORY.md) load size | `first 200 lines or 25KB, whichever comes first` |
| effort level options | `low, medium, high, max` |
| ClaudeFast Code Kit agent count | `18 specialized agents` |

## Related concepts

- /claude-code-subagents — Claude Code Subagents
- [[claude-code-hooks]] — Claude Code Hooks
- /model-context-protocol-(mcp) — Model Context Protocol (MCP)
- /claude-code-agent-teams — Claude Code Agent Teams
- /claude.md-project-instructions — CLAUDE.md project instructions
- /claude-code-plugins — Claude Code Plugins
- /progressive-disclosure-architecture — Progressive Disclosure Architecture
- /explore-plan-code-workflow — Explore-Plan-Code Workflow

## Citations (from contributing transcripts)

- **Claim:** Skills are prompt-based extensions that add new capabilities and orchestrate work, unlike built-in commands with fixed logic
  - Source: Extend Claude with skills - Claude Code Docs (`17cb5806-f618-44eb-888f-f1f24e26a61e`)
  - Context: Unlike built-in commands that execute fixed logic, skills are prompt-based, allowing Claude to orchestrate work.
- **Claim:** Skills use progressive disclosure architecture scanning ~100 tokens of metadata and loading up to 5000 tokens when activated
  - Source: GitHub - travisvn/awesome-claude-skills (`1af26266-735c-44d3-be7b-c69353f18651`)
  - Context: Claude scans skill metadata (name and description) using approximately 100 tokens to identify relevant matches, only loading the full content (up to 5000 tokens) when the skill is activated.
- **Claim:** Skills consist of a SKILL.md with YAML frontmatter and optional scripts/ folder
  - Source: GitHub - travisvn/awesome-claude-skills (`1af26266-735c-44d3-be7b-c69353f18651`)
  - Context: A skill typically consists of a directory containing a SKILL.md file with YAML frontmatter (name, description) and detailed instructions, and optionally includes a scripts/ folder for executable code
- **Claim:** Skills are available across Claude.ai, Claude Code, and the Claude API via /v1/skills
  - Source: GitHub - travisvn/awesome-claude-skills (`1af26266-735c-44d3-be7b-c69353f18651`)
  - Context: Skills are available across Claude.ai, Claude Code, and the Claude API via the /v1/skills endpoint.
- **Claim:** Skills are distinct from MCP, system prompts, and Projects
  - Source: GitHub - travisvn/awesome-claude-skills (`1af26266-735c-44d3-be7b-c69353f18651`)
  - Context: Skills are distinct from Model Context Protocol (MCP): Skills are used for task-specific expertise and workflows, while MCP is used for connecting to external data sources and APIs.
- **Claim:** Skills can execute arbitrary code; only install from trusted sources
  - Source: GitHub - travisvn/awesome-claude-skills (`1af26266-735c-44d3-be7b-c69353f18651`)
  - Context: Security Warning: Skills can execute arbitrary code in Claude's environment; users should only install skills from trusted sources and review SKILL.md and all scripts before enabling.
- **Claim:** Skill priority hierarchy: Enterprise, Personal ~/.claude/skills/, Project .claude/skills/, Plugin
  - Source: Extend Claude with skills - Claude Code Docs (`17cb5806-f618-44eb-888f-f1f24e26a61e`)
  - Context: Skill Locations and Priority: 1. Enterprise: Managed settings (highest priority). 2. Personal: Located in ~/.claude/skills/ 3. Project: Located in .claude/skills/ 4. Plugin: Located in <plugin-name>/skills/
- **Claim:** Frontmatter fields include disable_model_invocation, allowed_tools, effort, context: fork
  - Source: Extend Claude with skills - Claude Code Docs (`17cb5806-f618-44eb-888f-f1f24e26a61e`)
  - Context: disable_model_invocation: If true, Claude will not trigger the skill automatically; effort: Overrides the session effort level (low, medium, high, max); context: Set to fork to run the skill in an isolated subagent.
- **Claim:** String substitution variables $ARGUMENTS, $ARGUMENTS[N], ${CLAUDE_SESSION_ID}, ${CLAUDE_SKILL_DIR} are supported
  - Source: Extend Claude with skills - Claude Code Docs (`17cb5806-f618-44eb-888f-f1f24e26a61e`)
  - Context: $ARGUMENTS: All arguments passed after the skill name. ${CLAUDE_SESSION_ID}: The current session ID. ${CLAUDE_SKILL_DIR}: The directory containing the skill.
- **Claim:** Bundled skills /batch, /simplify, /loop, /debug ship with every session
  - Source: Extend Claude with skills - Claude Code Docs (`17cb5806-f618-44eb-888f-f1f24e26a61e`)
  - Context: Bundled Skills: Skills that ship with Claude Code and are available in every session (e.g., /batch, /debug, /simplify).

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `c8b07a4c-607c-4ddc-94be-688206daf737`
(cluster `claude-code-https`). No claims are made
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

- NotebookLM notebook [[INGESTED] - Claude Code x NotebookLM x Obsidian Research](https://notebooklm.google.com/notebook/c8b07a4c-607c-4ddc-94be-688206daf737)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
