---
title: "Claude Code Hooks System"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, claude]
summary: >
  The Claude Code hooks system provides extension points that allow users to intercept and control agent behavior at defined stages of execution, enabling automation of workflows and enforcement of project-specific policies.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 8138a528-f5c2-4ee4-b5a9-f3359f48f0dc" ([INGESTED] - Mastering Claude Skills, synced 2026-07-28)
  - "[BUG] Claude Code Destructive Action + Repeated User Interaction Failures #34514" (https://github.com/anthropics/claude-code/issues/34514, transcript synced 2026-07-28)
  - "Add Vibe-Guardian — Pre-commit security scanner for AI-generated code #751 - GitHub" (https://github.com/hesreallyhim/awesome-claude-code/issues/751, transcript synced 2026-07-28)
  - "GitHub - Dicklesworthstone/destructive_command_guard: The Destructive Command Guard (dcg) is for blocking dangerous git and shell commands from being executed by agents." (https://github.com/Dicklesworthstone/destructive_command_guard, transcript synced 2026-07-28)
  - "yurukusa/claude-code-hooks - GitHub" (https://github.com/yurukusa/claude-code-hooks, transcript synced 2026-07-28)
  - "Integrate skill-security-auditor as CI/CD PR check · Issue #241 · alirezarezvani/claude-skills" (https://github.com/alirezarezvani/claude-skills/issues/241, transcript synced 2026-07-28)
  - "From assistants to trustworthy AI co-workers: Operationalizing responsible agentic AI - CGI" (https://www.cgi.com/en/blog/artificial-intelligence/from-assistants-to-trustworthy-AI-coworkers-operationalizing-responsible-agentic-AI, transcript synced 2026-07-28)
  - "GitHub - rohitg00/awesome-claude-code-toolkit" (https://github.com/rohitg00/awesome-claude-code-toolkit, transcript synced 2026-07-28)
  - "ComposioHQ/awesome-claude-skills - GitHub" (https://github.com/ComposioHQ/awesome-claude-skills, transcript synced 2026-07-28)
  - "Claude Skills — Claude Code Plugin" (https://www.aitmpl.com/plugins/alirezarezvani-claude-skills/, transcript synced 2026-07-28)
  - "SECURITY.md - alirezarezvani/claude-skills - GitHub" (https://github.com/alirezarezvani/claude-skills/blob/main/SECURITY.md, transcript synced 2026-07-28)
  - "Add obey — Plugin that makes Claude follow your rules · Issue #1060 · hesreallyhim/awesome-claude-code - GitHub" (https://github.com/hesreallyhim/awesome-claude-code/issues/1060, transcript synced 2026-07-28)
  - "[BUG] Claude Code assistant not aware of available skills in .claude/skills/ directory · Issue #9716 · anthropics/claude-code - GitHub" (https://github.com/anthropics/claude-code/issues/9716?timeline_page=1, transcript synced 2026-07-28)
  - "zilliztech/claude-context: Code search MCP for Claude Code. Make entire codebase the context for any coding agent. - GitHub" (https://github.com/zilliztech/claude-context, transcript synced 2026-07-28)
  - "mattpocock/skills - git-guardrails-claude-code - GitHub" (https://github.com/mattpocock/skills/blob/main/skills/misc/git-guardrails-claude-code/SKILL.md, transcript synced 2026-07-28)
  - "skill-advisor · GitHub Topics" (https://github.com/topics/skill-advisor, transcript synced 2026-07-28)
  - "yurukusa/claude-code-ops-starter - GitHub" (https://github.com/yurukusa/claude-code-ops-starter, transcript synced 2026-07-28)
  - "CONVENTIONS.md - alirezarezvani/claude-skills - GitHub" (https://github.com/alirezarezvani/claude-skills/blob/main/CONVENTIONS.md, transcript synced 2026-07-28)
  - "CONTRIBUTING.md - alirezarezvani/claude-skills - GitHub" (https://github.com/alirezarezvani/claude-skills/blob/main/CONTRIBUTING.md, transcript synced 2026-07-28)
  - "Claude-Skills/engineering/skill-security-auditor/SKILL.md at main - GitHub" (https://github.com/borghei/Claude-Skills/blob/main/engineering/skill-security-auditor/SKILL.md, transcript synced 2026-07-28)
  - "Security - alirezarezvani/claude-skills - GitHub" (https://github.com/alirezarezvani/claude-skills/security, transcript synced 2026-07-28)
  - "LLMSecurity/skillguard: Agent Skill Security Auditor - GitHub" (https://github.com/LLMSecurity/skillguard, transcript synced 2026-07-28)
  - "Connect Claude Code to tools via MCP - Claude Code Docs" (https://code.claude.com/docs/en/mcp, transcript synced 2026-07-28)
  - "Extend Claude with skills - Claude Code Docs" (https://code.claude.com/docs/en/skills, transcript synced 2026-07-28)
  - "Extend Claude with skills - Claude Code Docs" (https://code.claude.com/docs/en/skills, transcript synced 2026-07-28)
  - "Give Claude custom tools - Claude Code Docs" (https://code.claude.com/docs/en/agent-sdk/custom-tools, transcript synced 2026-07-28)
  - "Claude Code Best Practices: Lessons From Real Projects - Ran the Builder" (https://ranthebuilder.cloud/blog/claude-code-best-practices-lessons-from-real-projects/, transcript synced 2026-07-28)
  - "Hooks reference - Claude Code Docs" (https://code.claude.com/docs/en/hooks, transcript synced 2026-07-28)
  - "Best practices for Claude Code" (https://code.claude.com/docs/en/best-practices, transcript synced 2026-07-28)
  - "Explore the .claude directory - Claude Code Docs" (https://code.claude.com/docs/en/claude-directory, transcript synced 2026-07-28)
  - "Overview - Claude Code Docs" (https://code.claude.com/docs/en/overview, transcript synced 2026-07-28)
  - "Define tools - Claude API Docs" (https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools, transcript synced 2026-07-28)
  - "Define tools - Claude API Docs - Claude Console" (https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools, transcript synced 2026-07-28)
  - "NotebookLM source b28abc3f-af49-4ef8-b3f7-f0f5a6aadbc9" (gto_full.md, synced 2026-07-28)
  - "Agent Skills - Claude API Docs" (https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview, transcript synced 2026-07-28)
  - "Skill authoring best practices - Claude API Docs" (https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices, transcript synced 2026-07-28)
  - "Documentation - Claude API Docs - Claude Console" (https://platform.claude.com/docs, transcript synced 2026-07-28)
  - "Gateguard - Skills - Claude Code Marketplaces" (https://claudemarketplaces.com/skills/affaan-m/everything-claude-code/gateguard, transcript synced 2026-07-28)
  - "Claude Code Hooks: 6 Production Patterns (2026) - Pixelmojo" (https://www.pixelmojo.io/blogs/claude-code-hooks-production-quality-ci-cd-patterns, transcript synced 2026-07-28)
  - "Claude Code: Best Practices for Developers - SAP Community" (https://community.sap.com/t5/artificial-intelligence-blogs-posts/claude-code-best-practices-for-developers/ba-p/14394164, transcript synced 2026-07-28)
  - "skill-security-auditor · alirezarezvani/claude-skills · Claude Code Plugins" (https://claudemarketplaces.com/plugins/alirezarezvani-claude-skills/skill-security-auditor, transcript synced 2026-07-28)
  - "GitHub - alirezarezvani/claude-skills: 337 Claude Code skills & agent skills & plugins (30+ Agents, 70+ custom commands, 330+ skills, customizable references, scripts)for Claude Code, Codex, Gemini CLI, Cursor, and 8 more coding agents — engineering, marketing, product, compliance, C-level advisory, research, business operations, commercial & finance, and your daily productivity skills." (https://github.com/alirezarezvani/claude-skills, transcript synced 2026-07-28)
  - "GitHub - alirezarezvani/claude-skills: 337 Claude Code skills & agent skills & plugins (30+ Agents, 70+ custom commands, 330+ skills, customizable references, scripts)for Claude Code, Codex, Gemini CLI, Cursor, and 8 more coding agents — engineering, marketing, product, compliance, C-level advisory, research, business operations, commercial & finance, and your daily productivity skills." (https://github.com/alirezarezvani/claude-skills, transcript synced 2026-07-28)
  - "NotebookLM source cd707464-99b0-4c07-be62-715a07c58175" (skill-guard_full.md, synced 2026-07-28)
  - "Building a Reliable LangGraph Workflow: Plan-Execute-Validate ..." (https://dev.to/manjunathgovindaraju/building-a-reliable-langgraph-workflow-plan-execute-validate-pev-automated-retries-and-mcp-1pik, transcript synced 2026-07-28)
  - "Securing LangGraph Multi-Agent Workflows: How to Enforce Tool-Level Permissions" (https://dev.to/cogniwall/securing-langgraph-multi-agent-workflows-how-to-enforce-tool-level-permissions-13cm, transcript synced 2026-07-28)
  - "Claude Code Hooks 101: Turning Your AI Coding Assistant Into an Automated Teammate" (https://dev.to/shrsv/claude-code-hooks-101-turning-your-ai-coding-assistant-into-an-automated-teammate-4lee, transcript synced 2026-07-28)
  - "How to Activate Claude Skills Automatically: 2 Fixes for 95 ..." (https://dev.to/oluwawunmiadesewa/claude-code-skills-not-triggering-2-fixes-for-100-activation-3b57, transcript synced 2026-07-28)
  - "The Complete Guide to Claude Code Hooks: Automating Your AI Coding Workflow - Blog" (https://home.mlops.community/public/blogs/the-complete-guide-to-claude-code-hooks-automating-your-ai-coding-workflow, transcript synced 2026-07-28)
  - "Claude Code Hooks: From Linting to Hardened AI Workflows | Thomas Wiegold Blog" (https://thomas-wiegold.com/blog/claude-code-hooks/, transcript synced 2026-07-28)
  - "Separation of Planning and Execution: The Key Pattern for Reliable AI Coding Agents" (https://dev.to/varun_pratapbhardwaj_b13/separation-of-planning-and-execution-the-key-pattern-for-reliable-ai-coding-agents-5b53, transcript synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: claude-code-hooks-system
    - level: notebook
      id: 8138a528-f5c2-4ee4-b5a9-f3359f48f0dc
      title: [INGESTED] - Mastering Claude Skills
      url: https://notebooklm.google.com/notebook/8138a528-f5c2-4ee4-b5a9-f3359f48f0dc
    - level: cluster
      id: 0
      name: claude-https-code
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/34514
      title: [BUG] Claude Code Destructive Action + Repeated User Interaction Failures #34514
    - level: source_url
      url: https://github.com/hesreallyhim/awesome-claude-code/issues/751
      title: Add Vibe-Guardian — Pre-commit security scanner for AI-generated code #751 - GitHub
    - level: source_url
      url: https://github.com/Dicklesworthstone/destructive_command_guard
      title: GitHub - Dicklesworthstone/destructive_command_guard: The Destructive Command Guard (dcg) is for blocking dangerous git and shell commands from being executed by agents.
    - level: source_url
      url: https://github.com/yurukusa/claude-code-hooks
      title: yurukusa/claude-code-hooks - GitHub
    - level: source_url
      url: https://github.com/alirezarezvani/claude-skills/issues/241
      title: Integrate skill-security-auditor as CI/CD PR check · Issue #241 · alirezarezvani/claude-skills
    - level: source_url
      url: https://www.cgi.com/en/blog/artificial-intelligence/from-assistants-to-trustworthy-AI-coworkers-operationalizing-responsible-agentic-AI
      title: From assistants to trustworthy AI co-workers: Operationalizing responsible agentic AI - CGI
    - level: source_url
      url: https://github.com/rohitg00/awesome-claude-code-toolkit
      title: GitHub - rohitg00/awesome-claude-code-toolkit
    - level: source_url
      url: https://github.com/ComposioHQ/awesome-claude-skills
      title: ComposioHQ/awesome-claude-skills - GitHub
    - level: source_url
      url: https://www.aitmpl.com/plugins/alirezarezvani-claude-skills/
      title: Claude Skills — Claude Code Plugin
    - level: source_url
      url: https://github.com/alirezarezvani/claude-skills/blob/main/SECURITY.md
      title: SECURITY.md - alirezarezvani/claude-skills - GitHub
    - level: source_url
      url: https://github.com/hesreallyhim/awesome-claude-code/issues/1060
      title: Add obey — Plugin that makes Claude follow your rules · Issue #1060 · hesreallyhim/awesome-claude-code - GitHub
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/9716?timeline_page=1
      title: [BUG] Claude Code assistant not aware of available skills in .claude/skills/ directory · Issue #9716 · anthropics/claude-code - GitHub
    - level: source_url
      url: https://github.com/zilliztech/claude-context
      title: zilliztech/claude-context: Code search MCP for Claude Code. Make entire codebase the context for any coding agent. - GitHub
    - level: source_url
      url: https://github.com/mattpocock/skills/blob/main/skills/misc/git-guardrails-claude-code/SKILL.md
      title: mattpocock/skills - git-guardrails-claude-code - GitHub
    - level: source_url
      url: https://github.com/topics/skill-advisor
      title: skill-advisor · GitHub Topics
    - level: source_url
      url: https://github.com/yurukusa/claude-code-ops-starter
      title: yurukusa/claude-code-ops-starter - GitHub
    - level: source_url
      url: https://github.com/alirezarezvani/claude-skills/blob/main/CONVENTIONS.md
      title: CONVENTIONS.md - alirezarezvani/claude-skills - GitHub
    - level: source_url
      url: https://github.com/alirezarezvani/claude-skills/blob/main/CONTRIBUTING.md
      title: CONTRIBUTING.md - alirezarezvani/claude-skills - GitHub
    - level: source_url
      url: https://github.com/borghei/Claude-Skills/blob/main/engineering/skill-security-auditor/SKILL.md
      title: Claude-Skills/engineering/skill-security-auditor/SKILL.md at main - GitHub
    - level: source_url
      url: https://github.com/alirezarezvani/claude-skills/security
      title: Security - alirezarezvani/claude-skills - GitHub
    - level: source_url
      url: https://github.com/LLMSecurity/skillguard
      title: LLMSecurity/skillguard: Agent Skill Security Auditor - GitHub
    - level: source_url
      url: https://code.claude.com/docs/en/mcp
      title: Connect Claude Code to tools via MCP - Claude Code Docs
    - level: source_url
      url: https://code.claude.com/docs/en/skills
      title: Extend Claude with skills - Claude Code Docs
    - level: source_url
      url: https://code.claude.com/docs/en/agent-sdk/custom-tools
      title: Give Claude custom tools - Claude Code Docs
    - level: source_url
      url: https://ranthebuilder.cloud/blog/claude-code-best-practices-lessons-from-real-projects/
      title: Claude Code Best Practices: Lessons From Real Projects - Ran the Builder
    - level: source_url
      url: https://code.claude.com/docs/en/hooks
      title: Hooks reference - Claude Code Docs
    - level: source_url
      url: https://code.claude.com/docs/en/best-practices
      title: Best practices for Claude Code
    - level: source_url
      url: https://code.claude.com/docs/en/claude-directory
      title: Explore the .claude directory - Claude Code Docs
    - level: source_url
      url: https://code.claude.com/docs/en/overview
      title: Overview - Claude Code Docs
    - level: source_url
      url: https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools
      title: Define tools - Claude API Docs
    - level: source_url
      url: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
      title: Agent Skills - Claude API Docs
    - level: source_url
      url: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
      title: Skill authoring best practices - Claude API Docs
    - level: source_url
      url: https://platform.claude.com/docs
      title: Documentation - Claude API Docs - Claude Console
    - level: source_url
      url: https://claudemarketplaces.com/skills/affaan-m/everything-claude-code/gateguard
      title: Gateguard - Skills - Claude Code Marketplaces
    - level: source_url
      url: https://www.pixelmojo.io/blogs/claude-code-hooks-production-quality-ci-cd-patterns
      title: Claude Code Hooks: 6 Production Patterns (2026) - Pixelmojo
    - level: source_url
      url: https://community.sap.com/t5/artificial-intelligence-blogs-posts/claude-code-best-practices-for-developers/ba-p/14394164
      title: Claude Code: Best Practices for Developers - SAP Community
    - level: source_url
      url: https://claudemarketplaces.com/plugins/alirezarezvani-claude-skills/skill-security-auditor
      title: skill-security-auditor · alirezarezvani/claude-skills · Claude Code Plugins
    - level: source_url
      url: https://github.com/alirezarezvani/claude-skills
      title: GitHub - alirezarezvani/claude-skills: 337 Claude Code skills & agent skills & plugins (30+ Agents, 70+ custom commands, 330+ skills, customizable references, scripts)for Claude Code, Codex, Gemini CLI, Cursor, and 8 more coding agents — engineering, marketing, product, compliance, C-level advisory, research, business operations, commercial & finance, and your daily productivity skills.
    - level: source_url
      url: https://dev.to/manjunathgovindaraju/building-a-reliable-langgraph-workflow-plan-execute-validate-pev-automated-retries-and-mcp-1pik
      title: Building a Reliable LangGraph Workflow: Plan-Execute-Validate ...
    - level: source_url
      url: https://dev.to/cogniwall/securing-langgraph-multi-agent-workflows-how-to-enforce-tool-level-permissions-13cm
      title: Securing LangGraph Multi-Agent Workflows: How to Enforce Tool-Level Permissions
    - level: source_url
      url: https://dev.to/shrsv/claude-code-hooks-101-turning-your-ai-coding-assistant-into-an-automated-teammate-4lee
      title: Claude Code Hooks 101: Turning Your AI Coding Assistant Into an Automated Teammate
    - level: source_url
      url: https://dev.to/oluwawunmiadesewa/claude-code-skills-not-triggering-2-fixes-for-100-activation-3b57
      title: How to Activate Claude Skills Automatically: 2 Fixes for 95 ...
    - level: source_url
      url: https://home.mlops.community/public/blogs/the-complete-guide-to-claude-code-hooks-automating-your-ai-coding-workflow
      title: The Complete Guide to Claude Code Hooks: Automating Your AI Coding Workflow - Blog
    - level: source_url
      url: https://thomas-wiegold.com/blog/claude-code-hooks/
      title: Claude Code Hooks: From Linting to Hardened AI Workflows | Thomas Wiegold Blog
    - level: source_url
      url: https://dev.to/varun_pratapbhardwaj_b13/separation-of-planning-and-execution-the-key-pattern-for-reliable-ai-coding-agents-5b53
      title: Separation of Planning and Execution: The Key Pattern for Reliable AI Coding Agents
relations:
  - target: wiki/concepts/claude-code-skills.md
    type: related
  - target: wiki/concepts/mcp-tools-integration.md
    type: related
  - target: wiki/concepts/agent-quality-gates.md
    type: related
---

# Claude Code Hooks System

## Decision context

**Definition:** The Claude Code hooks system provides extension points that allow users to intercept and control agent behavior at defined stages of execution, enabling automation of workflows and enforcement of project-specific policies.

Synthesized from **50 contributing transcripts** in NotebookLM notebook *[INGESTED] - Mastering Claude Skills*, clustered into the "claude-https-code" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The system includes four primary hook types: pretooluse, posttooluse, sessionstart, and stop hooks that fire at different stages of agent execution.
- Hooks are defined in Python files within a hooks/ directory, with common utilities shared across hook implementations in hooks/common.py.
- The pretooluse hook executes before a tool call is made, allowing interception or modification of agent-intended actions.
- The posttooluse hook executes after a tool call completes, enabling review or logging of actions taken.
- The sessionstart hook runs when a new Claude Code session begins, useful for initialization tasks.
- The stop hook executes when an agent session terminates, enabling cleanup or finalization workflows.
- Hooks can be combined with skills and MCP tools to create comprehensive automation patterns for production environments.
- Security-focused hook patterns exist, such as the Destructive Command Guard approach that intercepts dangerous git and shell commands before execution.
- The hooks system enables quality gates that review agent actions against defined criteria before allowing execution to proceed.
- Hook implementations can maintain state across multiple tool calls within a session using shared configuration and state files.
- Best practices include structuring hooks to handle edge cases, as noted in lessons from real production deployments of Claude Code.

## Verifiable values

| Name | Value |
|---|---|
| total hook types | `4 (pretooluse, posttooluse, sessionstart, stop)` |
| production-ready setup time | `15 minutes (with starter templates)` |
| Claude Code Ops Starter hooks count | `16` |
| Claude Code Ops Starter tools count | `3` |
| Claude Code Ops Starter templates count | `5` |

## Related concepts

- [[claude-code-skills]] — Claude Code Skills
- [[mcp-tools-integration]] — MCP Tools Integration
- [[agent-quality-gates]] — Agent Quality Gates
- [[destructive-command-guard]] — Destructive Command Guard
- [[skillguard-security-audit]] — SkillGuard Security Audit

## Citations (from contributing transcripts)

- **Claim:** The Claude Code hooks system includes pretooluse, posttooluse, sessionstart, and stop hook types
  - Source: gto_full.md (`b28abc3f-af49-4ef8-b3f7-f0f5a6aadbc9`)
  - Context: hooks\pretooluse.py, hooks\posttooluse.py, hooks\sessionstart.py, hooks\stop.py
- **Claim:** Hooks are implemented as Python files with common utilities in a shared module
  - Source: gto_full.md (`b28abc3f-af49-4ef8-b3f7-f0f5a6aadbc9`)
  - Context: hooks\common.py, Line 22, Line 47, Line 67, Line 84, Line 116, Line 128, Line 138, Line 149, Line 157, Line 166
- **Claim:** A 16-hook, 3-tool, 5-template starter kit enables production-ready setup in 15 minutes
  - Source: yurukusa/claude-code-ops-starter - GitHub (`c8c449b2-e217-433b-aba5-166fcac96c4e`)
  - Context: 16 hooks + 3 tools + 5 templates for autonomous Claude Code operation. Production-ready in 15 minutes
- **Claim:** Destructive Command Guard intercepts dangerous git and shell commands from being executed by agents
  - Source: GitHub - Dicklesworthstone/destructive_command_guard: The Destructive Command Guard (dcg)
  - Context: The Destructive Command Guard (dcg) is for blocking dangerous git and shell commands from being executed by agents
- **Claim:** Security auditing tools exist to review agent skills against security standards before installation
  - Source: LLMSecurity/skillguard: Agent Skill Security Auditor - GitHub (`ff99042f-f533-4dc0-8d61-99b77eff5a52`)
  - Context: Audit agent skills against OWASP Agentic Top 10 & MITRE ATLAS before installation
- **Claim:** Hooks enable quality gate patterns that review agent actions against defined criteria
  - Source: gto_full.md (`b28abc3f-af49-4ef8-b3f7-f0f5a6aadbc9`)
  - Context: agents\findings_reviewer.py, agents\gap_reviewer.py, agents\session_reviewer.py

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `8138a528-f5c2-4ee4-b5a9-f3359f48f0dc`
(cluster `claude-https-code`). No claims are made
about local workspace implementation. Trigger words like
'mechanism', 'scanner', 'gate', 'hook', 'because' refer to concepts
discussed in the source videos, not to local code behavior.
Implementation path: nlm-to-wiki/scripts/synthesize_subtopics.py
(LLM synthesis from transcripts — no local code inspected).

## What this means for our workspace

Synced from NotebookLM. Provenance chain (concept → notebook → cluster → URL) is in frontmatter; follow it back to the source material.

## Falsifier

If a re-sync of the source notebook produces a different definition or different values, this page should be updated (or marked as superseded). The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records when this page was last regenerated.

## Sources

- NotebookLM notebook [[INGESTED] - Mastering Claude Skills](https://notebooklm.google.com/notebook/8138a528-f5c2-4ee4-b5a9-f3359f48f0dc)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
