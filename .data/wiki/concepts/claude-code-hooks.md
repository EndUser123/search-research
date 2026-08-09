---
title: "Claude Code Hooks"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, claude]
summary: >
  Claude Code hooks are a pattern that allows execution of custom scripts at defined points during the agent's operation, enabling automation and customization of the coding workflow.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 224c7571-440c-4ff0-b699-17045b28ff2d" (Claude Code Skills and Features Reference Guide, synced 2026-07-28)
  - "Claude Code Skills Complete Guide - Creating, Testing, and Distributing Agent Skills" (https://hidekazu-konishi.com/entry/claude_code_skills_complete_guide.html, transcript synced 2026-07-28)
  - "Tools reference - Claude Code Docs" (https://code.claude.com/docs/en/tools-reference, transcript synced 2026-07-28)
  - "Best practices for Claude Code" (https://code.claude.com/docs/en/best-practices, transcript synced 2026-07-28)
  - "Claude Code Features and Settings Reference 2026 | hidekazu-konishi.com" (https://hidekazu-konishi.com/entry/claude_code_features_settings_reference_2026.html, transcript synced 2026-07-28)
  - "[BUG] PostToolUse Hook Exit Code 1 Blocks Claude Execution · Issue #4809 - GitHub" (https://github.com/anthropics/claude-code/issues/4809, transcript synced 2026-07-28)
  - "what are the biggest risks of agentic AI in supply chain production? : r/AI_Agents - Reddit" (https://www.reddit.com/r/AI_Agents/comments/1t02m8b/what_are_the_biggest_risks_of_agentic_ai_in/, transcript synced 2026-07-28)
  - "Debug your configuration - Claude Code Docs" (https://code.claude.com/docs/en/debug-your-config, transcript synced 2026-07-28)
  - "My Claude Code setup - Freek Van der Herten's blog on Laravel, PHP and AI" (https://freek.dev/3026-my-claude-code-setup, transcript synced 2026-07-28)
  - "Create custom subagents - Claude Code Docs" (https://code.claude.com/docs/en/sub-agents, transcript synced 2026-07-28)
  - "Guide Claude Code with Rich PreToolUse Feedback - Egghead.io" (https://egghead.io/guide-claude-code-with-rich-pre-tool-use-feedback~ex177, transcript synced 2026-07-28)
  - "Tools - Claude Code" (https://vineetagarwal-code-claude-code.mintlify.app/concepts/tools, transcript synced 2026-07-28)
  - "Choose a permission mode - Claude Code Docs" (https://code.claude.com/docs/en/permission-modes, transcript synced 2026-07-28)
  - "Custom Skills with Frontmatter - The AI Agent Factory - Panaversity" (https://agentfactory.panaversity.org/docs/General-Agents-Foundations/claude-code-teams-cicd/custom-skills-with-frontmatter, transcript synced 2026-07-28)
  - "How the agent loop works - Claude Code Docs" (https://code.claude.com/docs/en/agent-sdk/agent-loop, transcript synced 2026-07-28)
  - "Claude Code Hooks: From Linting to Hardened AI Workflows | Thomas Wiegold Blog" (https://thomas-wiegold.com/blog/claude-code-hooks/, transcript synced 2026-07-28)
  - "A Practical Guide to the Claude Code CLI: Mastering Usage Through 'Why' and 'Combination' - Zenn" (https://zenn.dev/haboshi/articles/claude-code-cli-practical-guide?locale=en, transcript synced 2026-07-28)
  - "How Claude remembers your project - Claude Code Docs" (https://code.claude.com/docs/en/memory, transcript synced 2026-07-28)
  - "NotebookLM source 6b76b355-bb41-4ae0-975b-c3d6c07f8b35" (_Find official documentation, community tutorials,.md, synced 2026-07-28)
  - "Claude Code Hooks - DEV Community" (https://dev.to/helderberto/claude-code-hooks-1k7a, transcript synced 2026-07-28)
  - "Claude Code v2.1.50: Major Memory Optimizations and Worktree Isolation - ClaudeWorld" (https://claude-world.com/articles/claude-code-2150-release/, transcript synced 2026-07-28)
  - "NotebookLM source 6eb8f63c-0ac1-4853-90ec-e2b6c350bd0a" (goal-md-template-library.md, synced 2026-07-28)
  - "Configure permissions - Claude Code Docs" (https://code.claude.com/docs/en/agent-sdk/permissions, transcript synced 2026-07-28)
  - "Claude Code hooks: a bookmarkable guide to git automation - AI @ Sulat.com" (https://ai.sulat.com/claude-code-hooks-a-bookmarkable-guide-to-git-automation-11b4516adc5d, transcript synced 2026-07-28)
  - "Run Claude Code programmatically" (https://code.claude.com/docs/en/headless, transcript synced 2026-07-28)
  - "Claude code docs map" (https://code.claude.com/docs/en/claude_code_docs_map, transcript synced 2026-07-28)
  - "12 Claude Code Settings You Should Enable Right Now | MindStudio" (https://www.mindstudio.ai/blog/12-claude-code-settings-enable-now, transcript synced 2026-07-28)
  - "What are test hooks in AI-native development? - CircleCI" (https://circleci.com/blog/test-hooks-ai-development/, transcript synced 2026-07-28)
  - "CLI reference - Claude Code Docs" (https://code.claude.com/docs/en/cli-reference, transcript synced 2026-07-28)
  - "Extend Claude Code - Claude Code Docs" (https://code.claude.com/docs/en/features-overview, transcript synced 2026-07-28)
  - "Agent Skills in the SDK - Claude Code Docs" (https://code.claude.com/docs/en/agent-sdk/skills, transcript synced 2026-07-28)
  - "Claude Code Hooks: 12 Production Configs I Run Daily (with Failure Modes)" (https://www.heyuan110.com/posts/ai/2026-02-28-claude-code-hooks-guide/, transcript synced 2026-07-28)
  - "Explore the .claude directory - Claude Code Docs" (https://code.claude.com/docs/en/claude-directory, transcript synced 2026-07-28)
  - "Hooks reference - Claude Code Docs" (https://code.claude.com/docs/en/hooks, transcript synced 2026-07-28)
  - "Automate actions with hooks - Claude Code Docs" (https://code.claude.com/docs/en/hooks-guide, transcript synced 2026-07-28)
  - "PreToolUse hook exit code 2 does not block Task tool calls (agents launch despite block) · Issue #26923 · anthropics/claude-code - GitHub" (https://github.com/anthropics/claude-code/issues/26923, transcript synced 2026-07-28)
  - "Explore the context window - Claude Code Docs" (https://code.claude.com/docs/en/context-window, transcript synced 2026-07-28)
  - "Error reference - Claude Code Docs" (https://code.claude.com/docs/en/errors, transcript synced 2026-07-28)
  - "Claude Code CLI Documentation: Commands, Flags, and Governance - Gravitee" (https://www.gravitee.io/blog/claude-code-cli-documentation-commands-flags-and-governance, transcript synced 2026-07-28)
  - "The 15-File Setup That Turned Claude Code Into My Development Team - Towards AI" (https://pub.towardsai.net/the-15-file-setup-that-turned-claude-code-into-my-development-team-04bc38da49de, transcript synced 2026-07-28)
  - "[BUG] PreToolUse hook exit code 2 causes Claude to stop instead of acting on error feedback #24327 - GitHub" (https://github.com/anthropics/claude-code/issues/24327, transcript synced 2026-07-28)
  - "Claude Code settings - Claude Code Docs" (https://code.claude.com/docs/en/settings, transcript synced 2026-07-28)
  - "How Claude Code works - Claude Code Docs" (https://code.claude.com/docs/en/how-claude-code-works, transcript synced 2026-07-28)
  - "10 Best Claude Code Hooks to Add in 2026 - AY Automate" (https://www.ayautomate.com/blog/best-claude-code-hooks, transcript synced 2026-07-28)
  - "Claude Code Hooks Complete Guide - Deterministic Enforcement Across the Tool Lifecycle" (https://hidekazu-konishi.com/entry/claude_code_hooks_complete_guide.html, transcript synced 2026-07-28)
  - "Claude Code CLI Runtime Analysis - GitHub Gist" (https://gist.github.com/VoidChecksum/0c156a14ccb227f952fe4772bc294e40, transcript synced 2026-07-28)
  - "I stopped writing rules in CLAUDE.md and started writing hooks. The rules finally hold. : r/ClaudeAI - Reddit" (https://www.reddit.com/r/ClaudeAI/comments/1ucnasw/i_stopped_writing_rules_in_claudemd_and_started/, transcript synced 2026-07-28)
  - "Git Integration - Checklist | SFEIR Institute" (https://institute.sfeir.com/en/claude-code/claude-code-git-integration/checklist/, transcript synced 2026-07-28)
  - "Claude Code Hooks (2026): Block Claude Reading .env + 30 Hook Events, JSON Input, Exit Codes - MorphLLM" (https://www.morphllm.com/claude-code-hooks, transcript synced 2026-07-28)
  - "Build an Autonomous Code Review Bot with Claude Code Hooks + GitHub Actions in 30 Minutes | by Vikas Sah | Medium" (https://engineeratheart.medium.com/build-an-autonomous-code-review-bot-with-claude-code-hooks-github-actions-in-30-minutes-038e92e59eeb, transcript synced 2026-07-28)
  - "Introducing Agent Governance: Using Hooks to Bring Visibility to AI Coding Agents | Blog" (https://www.endorlabs.com/learn/introducing-agent-governance-using-hooks-to-bring-visibility-to-ai-coding-agents, transcript synced 2026-07-28)
  - "Claude Code Source Code Deep Research Report" (https://claudeai.dev/docs/mechanics/development/claude-code-source-deep-research/, transcript synced 2026-07-28)
  - "NotebookLM source fdd118ad-4327-4530-b2e6-5ee189d11129" (Architectural Optimization of Agentic Development: Resolving Friction Between Thoroughness and Velocity in Claude Code Workflows, synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: claude-code-hooks
    - level: notebook
      id: 224c7571-440c-4ff0-b699-17045b28ff2d
      title: Claude Code Skills and Features Reference Guide
      url: https://notebooklm.google.com/notebook/224c7571-440c-4ff0-b699-17045b28ff2d
    - level: cluster
      id: 0
      name: claude-code-https
    - level: source_url
      url: https://hidekazu-konishi.com/entry/claude_code_skills_complete_guide.html
      title: Claude Code Skills Complete Guide - Creating, Testing, and Distributing Agent Skills
    - level: source_url
      url: https://code.claude.com/docs/en/tools-reference
      title: Tools reference - Claude Code Docs
    - level: source_url
      url: https://code.claude.com/docs/en/best-practices
      title: Best practices for Claude Code
    - level: source_url
      url: https://hidekazu-konishi.com/entry/claude_code_features_settings_reference_2026.html
      title: Claude Code Features and Settings Reference 2026 | hidekazu-konishi.com
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/4809
      title: [BUG] PostToolUse Hook Exit Code 1 Blocks Claude Execution · Issue #4809 - GitHub
    - level: source_url
      url: https://www.reddit.com/r/AI_Agents/comments/1t02m8b/what_are_the_biggest_risks_of_agentic_ai_in/
      title: what are the biggest risks of agentic AI in supply chain production? : r/AI_Agents - Reddit
    - level: source_url
      url: https://code.claude.com/docs/en/debug-your-config
      title: Debug your configuration - Claude Code Docs
    - level: source_url
      url: https://freek.dev/3026-my-claude-code-setup
      title: My Claude Code setup - Freek Van der Herten's blog on Laravel, PHP and AI
    - level: source_url
      url: https://code.claude.com/docs/en/sub-agents
      title: Create custom subagents - Claude Code Docs
    - level: source_url
      url: https://egghead.io/guide-claude-code-with-rich-pre-tool-use-feedback~ex177
      title: Guide Claude Code with Rich PreToolUse Feedback - Egghead.io
    - level: source_url
      url: https://vineetagarwal-code-claude-code.mintlify.app/concepts/tools
      title: Tools - Claude Code
    - level: source_url
      url: https://code.claude.com/docs/en/permission-modes
      title: Choose a permission mode - Claude Code Docs
    - level: source_url
      url: https://agentfactory.panaversity.org/docs/General-Agents-Foundations/claude-code-teams-cicd/custom-skills-with-frontmatter
      title: Custom Skills with Frontmatter - The AI Agent Factory - Panaversity
    - level: source_url
      url: https://code.claude.com/docs/en/agent-sdk/agent-loop
      title: How the agent loop works - Claude Code Docs
    - level: source_url
      url: https://thomas-wiegold.com/blog/claude-code-hooks/
      title: Claude Code Hooks: From Linting to Hardened AI Workflows | Thomas Wiegold Blog
    - level: source_url
      url: https://zenn.dev/haboshi/articles/claude-code-cli-practical-guide?locale=en
      title: A Practical Guide to the Claude Code CLI: Mastering Usage Through 'Why' and 'Combination' - Zenn
    - level: source_url
      url: https://code.claude.com/docs/en/memory
      title: How Claude remembers your project - Claude Code Docs
    - level: source_url
      url: https://dev.to/helderberto/claude-code-hooks-1k7a
      title: Claude Code Hooks - DEV Community
    - level: source_url
      url: https://claude-world.com/articles/claude-code-2150-release/
      title: Claude Code v2.1.50: Major Memory Optimizations and Worktree Isolation - ClaudeWorld
    - level: source_url
      url: https://code.claude.com/docs/en/agent-sdk/permissions
      title: Configure permissions - Claude Code Docs
    - level: source_url
      url: https://ai.sulat.com/claude-code-hooks-a-bookmarkable-guide-to-git-automation-11b4516adc5d
      title: Claude Code hooks: a bookmarkable guide to git automation - AI @ Sulat.com
    - level: source_url
      url: https://code.claude.com/docs/en/headless
      title: Run Claude Code programmatically
    - level: source_url
      url: https://code.claude.com/docs/en/claude_code_docs_map
      title: Claude code docs map
    - level: source_url
      url: https://www.mindstudio.ai/blog/12-claude-code-settings-enable-now
      title: 12 Claude Code Settings You Should Enable Right Now | MindStudio
    - level: source_url
      url: https://circleci.com/blog/test-hooks-ai-development/
      title: What are test hooks in AI-native development? - CircleCI
    - level: source_url
      url: https://code.claude.com/docs/en/cli-reference
      title: CLI reference - Claude Code Docs
    - level: source_url
      url: https://code.claude.com/docs/en/features-overview
      title: Extend Claude Code - Claude Code Docs
    - level: source_url
      url: https://code.claude.com/docs/en/agent-sdk/skills
      title: Agent Skills in the SDK - Claude Code Docs
    - level: source_url
      url: https://www.heyuan110.com/posts/ai/2026-02-28-claude-code-hooks-guide/
      title: Claude Code Hooks: 12 Production Configs I Run Daily (with Failure Modes)
    - level: source_url
      url: https://code.claude.com/docs/en/claude-directory
      title: Explore the .claude directory - Claude Code Docs
    - level: source_url
      url: https://code.claude.com/docs/en/hooks
      title: Hooks reference - Claude Code Docs
    - level: source_url
      url: https://code.claude.com/docs/en/hooks-guide
      title: Automate actions with hooks - Claude Code Docs
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/26923
      title: PreToolUse hook exit code 2 does not block Task tool calls (agents launch despite block) · Issue #26923 · anthropics/claude-code - GitHub
    - level: source_url
      url: https://code.claude.com/docs/en/context-window
      title: Explore the context window - Claude Code Docs
    - level: source_url
      url: https://code.claude.com/docs/en/errors
      title: Error reference - Claude Code Docs
    - level: source_url
      url: https://www.gravitee.io/blog/claude-code-cli-documentation-commands-flags-and-governance
      title: Claude Code CLI Documentation: Commands, Flags, and Governance - Gravitee
    - level: source_url
      url: https://pub.towardsai.net/the-15-file-setup-that-turned-claude-code-into-my-development-team-04bc38da49de
      title: The 15-File Setup That Turned Claude Code Into My Development Team - Towards AI
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/24327
      title: [BUG] PreToolUse hook exit code 2 causes Claude to stop instead of acting on error feedback #24327 - GitHub
    - level: source_url
      url: https://code.claude.com/docs/en/settings
      title: Claude Code settings - Claude Code Docs
    - level: source_url
      url: https://code.claude.com/docs/en/how-claude-code-works
      title: How Claude Code works - Claude Code Docs
    - level: source_url
      url: https://www.ayautomate.com/blog/best-claude-code-hooks
      title: 10 Best Claude Code Hooks to Add in 2026 - AY Automate
    - level: source_url
      url: https://hidekazu-konishi.com/entry/claude_code_hooks_complete_guide.html
      title: Claude Code Hooks Complete Guide - Deterministic Enforcement Across the Tool Lifecycle
    - level: source_url
      url: https://gist.github.com/VoidChecksum/0c156a14ccb227f952fe4772bc294e40
      title: Claude Code CLI Runtime Analysis - GitHub Gist
    - level: source_url
      url: https://www.reddit.com/r/ClaudeAI/comments/1ucnasw/i_stopped_writing_rules_in_claudemd_and_started/
      title: I stopped writing rules in CLAUDE.md and started writing hooks. The rules finally hold. : r/ClaudeAI - Reddit
    - level: source_url
      url: https://institute.sfeir.com/en/claude-code/claude-code-git-integration/checklist/
      title: Git Integration - Checklist | SFEIR Institute
    - level: source_url
      url: https://www.morphllm.com/claude-code-hooks
      title: Claude Code Hooks (2026): Block Claude Reading .env + 30 Hook Events, JSON Input, Exit Codes - MorphLLM
    - level: source_url
      url: https://engineeratheart.medium.com/build-an-autonomous-code-review-bot-with-claude-code-hooks-github-actions-in-30-minutes-038e92e59eeb
      title: Build an Autonomous Code Review Bot with Claude Code Hooks + GitHub Actions in 30 Minutes | by Vikas Sah | Medium
    - level: source_url
      url: https://www.endorlabs.com/learn/introducing-agent-governance-using-hooks-to-bring-visibility-to-ai-coding-agents
      title: Introducing Agent Governance: Using Hooks to Bring Visibility to AI Coding Agents | Blog
    - level: source_url
      url: https://claudeai.dev/docs/mechanics/development/claude-code-source-deep-research/
      title: Claude Code Source Code Deep Research Report
relations:
  - target: wiki/concepts/claude-code-skills.md
    type: related
  - target: wiki/concepts/agent-loop.md
    type: related
  - target: wiki/concepts/claude-code-extension-layers.md
    type: related
---

# Claude Code Hooks

## Decision context

**Definition:** Claude Code hooks are a pattern that allows execution of custom scripts at defined points during the agent's operation, enabling automation and customization of the coding workflow.

Synthesized from **52 contributing transcripts** in NotebookLM notebook *Claude Code Skills and Features Reference Guide*, clustered into the "claude-code-https" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Custom scripts can be configured to execute at specific points during Claude Code's operation, such as before or after tool use
- Hooks support various use cases including file editing, command execution, and code deployment
- Exit code handling determines subsequent behavior; exit code 2 from PreToolUse hooks causes Claude to stop rather than continue with error feedback
- The hooks system serves both operational automation and governance visibility purposes, allowing teams to monitor AI agent activity
- Scripts are placed in the .claude directory and follow naming conventions to be recognized by the system
- Hooks operate synchronously, blocking the agent loop until the script completes

## Verifiable values

| Name | Value |
|---|---|
| Hook exit code for stop behavior | `2` |
| Configuration location | `.claude directory` |

## Related concepts

- claude-code-skills — Claude Code Skills
- agent-loop — Agent Loop
- [[claude-code-extension-patterns]] — Claude Code Extension Layers

## Citations (from contributing transcripts)

- **Claim:** Hooks let you execute custom scripts at specific points during Claude Code's operation
  - Source: Claude Code Hooks - DEV Community (`6bc6ab50-fdf0-435c-aabd-87967842178c`)
  - Context: Hooks let...custom scripts at specific points during execution. Claude Code moves fast: editing files, running commands, pushing code in quick succession.
- **Claim:** PreToolUse hook with exit code 2 causes Claude to stop
  - Source: [BUG] PreToolUse hook exit code 2 causes Claude to stop instead of acting on error feedback #24327 - GitHub (`d65a6ba5-3e21-4573-a8fe-84f31c675951`)
  - Context: PreToolUse hook exit code 2 causes Claude to stop instead of acting on error feedback
- **Claim:** Hooks provide visibility into AI coding agents for governance purposes
  - Source: Introducing Agent Governance: Using Hooks to Bring Visibility to AI Coding Agents | Blog (`f9edccda-bda2-42ab-a475-723d7e746111`)
  - Context: Using Hooks to Bring Visibility to AI Coding Agents
- **Claim:** Hooks are configured through the .claude directory
  - Source: Explore the .claude directory - Claude Code Docs (`a427318b-518a-4380-b590-4ddc1303f032`)
  - Context: Explore the .claude directory

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `224c7571-440c-4ff0-b699-17045b28ff2d`
(cluster `claude-code-https`). No claims are made
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

- NotebookLM notebook [Claude Code Skills and Features Reference Guide](https://notebooklm.google.com/notebook/224c7571-440c-4ff0-b699-17045b28ff2d)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
