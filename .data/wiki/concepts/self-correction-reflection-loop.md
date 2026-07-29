---
title: "Self-Correction Reflection Loop"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, https]
summary: >
  The self-correction reflection loop is a design pattern for coding agents that enables automatic retry after failed edits by providing structured error feedback, allowing the agent to反思 and adjust its approach without manual intervention.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 590ac9fd-01f0-4b85-97ff-7d49bd5ed78d" (Deep Research Prompts, Methods, Examples, synced 2026-07-28)
  - "Self-Correction Reflection Loop — Automatic Retry with Structured Error Feedback After Failed Edits (inspired by Aider) · Issue #536 · NousResearch/hermes-agent - GitHub" (https://github.com/NousResearch/hermes-agent/issues/536, transcript synced 2026-07-28)
  - "Inside a 116-Configuration Claude Code Setup: Skills, Hooks, Agents, and the Layering That Makes It Work - Reddit" (https://www.reddit.com/r/ClaudeCode/comments/1rltiv7/inside_a_116configuration_claude_code_setup/, transcript synced 2026-07-28)
  - "[Fix] Claude Code Error: 'Error during compaction... thinking blocks cannot be modified' (API Error 400) : r/ClaudeAI - Reddit" (https://www.reddit.com/r/ClaudeAI/comments/1pfd5sr/fix_claude_code_error_error_during_compaction/, transcript synced 2026-07-28)
  - "Claude Code Hooks Explained: The Deterministic Layer Around Your Agent - Blake Crosley" (https://blakecrosley.com/pl/blog/claude-code-hooks-explained, transcript synced 2026-07-28)
  - "Best practices for Claude Code" (https://code.claude.com/docs/en/best-practices, transcript synced 2026-07-28)
  - "I stopped writing rules in CLAUDE.md and started writing hooks. The rules finally hold. : r/ClaudeAI - Reddit" (https://www.reddit.com/r/ClaudeAI/comments/1ucnasw/i_stopped_writing_rules_in_claudemd_and_started/, transcript synced 2026-07-28)
  - "Writing a good CLAUDE.md | HumanLayer Blog" (https://www.humanlayer.dev/blog/writing-a-good-claude-md, transcript synced 2026-07-28)
  - "Automate actions with hooks - Claude Code Docs" (https://code.claude.com/docs/en/hooks-guide, transcript synced 2026-07-28)
  - "Overview - Claude Code Docs" (https://code.claude.com/docs/en/overview, transcript synced 2026-07-28)
  - "How to build self-improving coding agents - Part 1 - Eric J. Ma's Personal Site" (https://ericmjl.github.io/blog/2026/1/17/how-to-build-self-improving-coding-agents-part-1/, transcript synced 2026-07-28)
  - "attractor/coding-agent-loop-spec.md at main - GitHub" (https://github.com/strongdm/attractor/blob/main/coding-agent-loop-spec.md, transcript synced 2026-07-28)
  - "[Gemini UI Bug] Nested Markdown code blocks break outer code fences early" (https://discuss.ai.google.dev/t/gemini-ui-bug-nested-markdown-code-blocks-break-outer-code-fences-early/171407, transcript synced 2026-07-28)
  - "Hooks reference - Claude Code Docs" (https://code.claude.com/docs/en/hooks, transcript synced 2026-07-28)
  - "Claude Code settings.json Hooks: Auto-Run Scripts at Every Step - Vincent" (https://blog.vincentqiao.com/en/posts/claude-code-settings-hooks/, transcript synced 2026-07-28)
  - "CLAUDE.md, AGENTS.md & Copilot Instructions: Configure Every AI Coding Assistant" (https://www.deployhq.com/blog/ai-coding-config-files-guide, transcript synced 2026-07-28)
  - "Improving Deep Agents with harness engineering - LangChain" (https://www.langchain.com/blog/improving-deep-agents-with-harness-engineering, transcript synced 2026-07-28)
  - "cy0307/awesome-loop-engineering · Datasets at Hugging Face" (https://huggingface.co/datasets/cy0307/awesome-loop-engineering, transcript synced 2026-07-28)
  - "Please tell me How to reliably parse Claude/LLM output that's wrapped in ```json code fences with the JSON > Parse JSON module? - Make Community" (https://community.make.com/t/please-tell-me-how-to-reliably-parse-claude-llm-output-thats-wrapped-in-json-code-fences-with-the-json-parse-json-module/110253, transcript synced 2026-07-28)
  - "3 weeks of daily AI agent work — what I learned about memory and persona - Reddit" (https://www.reddit.com/r/ClaudeCode/comments/1rg6x15/3_weeks_of_daily_ai_agent_work_what_i_learned/, transcript synced 2026-07-28)
  - "Claude Code Hooks: Automate Your AI Coding Workflow - Kyle Redelinghuys" (https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/, transcript synced 2026-07-28)
  - "How to Set Up Claude Code Agent Teams (Full Walkthrough + What Actually Changed)" (https://www.reddit.com/r/ClaudeCode/comments/1qz8tyy/how_to_set_up_claude_code_agent_teams_full/, transcript synced 2026-07-28)
  - "CLAUDE.md - multica-ai/andrej-karpathy-skills - GitHub" (https://github.com/multica-ai/andrej-karpathy-skills/blob/main/CLAUDE.md, transcript synced 2026-07-28)
  - "Create custom subagents - Claude Code Docs" (https://code.claude.com/docs/en/sub-agents, transcript synced 2026-07-28)
  - "AI-agent skills for distributed-systems testing - GitHub" (https://github.com/shenli/distributed-system-testing, transcript synced 2026-07-28)
  - "Over-editing refers to a model modifying code beyond what is necessary - Hacker News" (https://news.ycombinator.com/item?id=47866913, transcript synced 2026-07-28)
  - "Claude Code Hooks Complete Guide - Deterministic Enforcement Across the Tool Lifecycle" (https://hidekazu-konishi.com/entry/claude_code_hooks_complete_guide.html, transcript synced 2026-07-28)
  - "How Claude remembers your project - Claude Code Docs" (https://code.claude.com/docs/en/memory, transcript synced 2026-07-28)
  - "[BUG] PreToolUse hook permissionDecision 'allow' does not suppress native permission prompt in interactive mode (v2.1.119) · Issue #52822 · anthropics/claude-code - GitHub" (https://github.com/anthropics/claude-code/issues/52822, transcript synced 2026-07-28)
  - "GitHub - snap-stanford/POPPER: Automated Hypothesis Testing with Agentic Sequential Falsifications" (https://github.com/snap-stanford/POPPER, transcript synced 2026-07-28)
  - "Hooks - ClaudeKit Documentation" (https://docs.claudekit.cc/docs/engineer/configuration/hooks, transcript synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: self-correction-reflection-loop
    - level: notebook
      id: 590ac9fd-01f0-4b85-97ff-7d49bd5ed78d
      title: Deep Research Prompts, Methods, Examples
      url: https://notebooklm.google.com/notebook/590ac9fd-01f0-4b85-97ff-7d49bd5ed78d
    - level: cluster
      id: 0
      name: https-claude-code
    - level: source_url
      url: https://github.com/NousResearch/hermes-agent/issues/536
      title: Self-Correction Reflection Loop — Automatic Retry with Structured Error Feedback After Failed Edits (inspired by Aider) · Issue #536 · NousResearch/hermes-agent - GitHub
    - level: source_url
      url: https://www.reddit.com/r/ClaudeCode/comments/1rltiv7/inside_a_116configuration_claude_code_setup/
      title: Inside a 116-Configuration Claude Code Setup: Skills, Hooks, Agents, and the Layering That Makes It Work - Reddit
    - level: source_url
      url: https://www.reddit.com/r/ClaudeAI/comments/1pfd5sr/fix_claude_code_error_error_during_compaction/
      title: [Fix] Claude Code Error: 'Error during compaction... thinking blocks cannot be modified' (API Error 400) : r/ClaudeAI - Reddit
    - level: source_url
      url: https://blakecrosley.com/pl/blog/claude-code-hooks-explained
      title: Claude Code Hooks Explained: The Deterministic Layer Around Your Agent - Blake Crosley
    - level: source_url
      url: https://code.claude.com/docs/en/best-practices
      title: Best practices for Claude Code
    - level: source_url
      url: https://www.reddit.com/r/ClaudeAI/comments/1ucnasw/i_stopped_writing_rules_in_claudemd_and_started/
      title: I stopped writing rules in CLAUDE.md and started writing hooks. The rules finally hold. : r/ClaudeAI - Reddit
    - level: source_url
      url: https://www.humanlayer.dev/blog/writing-a-good-claude-md
      title: Writing a good CLAUDE.md | HumanLayer Blog
    - level: source_url
      url: https://code.claude.com/docs/en/hooks-guide
      title: Automate actions with hooks - Claude Code Docs
    - level: source_url
      url: https://code.claude.com/docs/en/overview
      title: Overview - Claude Code Docs
    - level: source_url
      url: https://ericmjl.github.io/blog/2026/1/17/how-to-build-self-improving-coding-agents-part-1/
      title: How to build self-improving coding agents - Part 1 - Eric J. Ma's Personal Site
    - level: source_url
      url: https://github.com/strongdm/attractor/blob/main/coding-agent-loop-spec.md
      title: attractor/coding-agent-loop-spec.md at main - GitHub
    - level: source_url
      url: https://discuss.ai.google.dev/t/gemini-ui-bug-nested-markdown-code-blocks-break-outer-code-fences-early/171407
      title: [Gemini UI Bug] Nested Markdown code blocks break outer code fences early
    - level: source_url
      url: https://code.claude.com/docs/en/hooks
      title: Hooks reference - Claude Code Docs
    - level: source_url
      url: https://blog.vincentqiao.com/en/posts/claude-code-settings-hooks/
      title: Claude Code settings.json Hooks: Auto-Run Scripts at Every Step - Vincent
    - level: source_url
      url: https://www.deployhq.com/blog/ai-coding-config-files-guide
      title: CLAUDE.md, AGENTS.md & Copilot Instructions: Configure Every AI Coding Assistant
    - level: source_url
      url: https://www.langchain.com/blog/improving-deep-agents-with-harness-engineering
      title: Improving Deep Agents with harness engineering - LangChain
    - level: source_url
      url: https://huggingface.co/datasets/cy0307/awesome-loop-engineering
      title: cy0307/awesome-loop-engineering · Datasets at Hugging Face
    - level: source_url
      url: https://community.make.com/t/please-tell-me-how-to-reliably-parse-claude-llm-output-thats-wrapped-in-json-code-fences-with-the-json-parse-json-module/110253
      title: Please tell me How to reliably parse Claude/LLM output that's wrapped in ```json code fences with the JSON > Parse JSON module? - Make Community
    - level: source_url
      url: https://www.reddit.com/r/ClaudeCode/comments/1rg6x15/3_weeks_of_daily_ai_agent_work_what_i_learned/
      title: 3 weeks of daily AI agent work — what I learned about memory and persona - Reddit
    - level: source_url
      url: https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/
      title: Claude Code Hooks: Automate Your AI Coding Workflow - Kyle Redelinghuys
    - level: source_url
      url: https://www.reddit.com/r/ClaudeCode/comments/1qz8tyy/how_to_set_up_claude_code_agent_teams_full/
      title: How to Set Up Claude Code Agent Teams (Full Walkthrough + What Actually Changed)
    - level: source_url
      url: https://github.com/multica-ai/andrej-karpathy-skills/blob/main/CLAUDE.md
      title: CLAUDE.md - multica-ai/andrej-karpathy-skills - GitHub
    - level: source_url
      url: https://code.claude.com/docs/en/sub-agents
      title: Create custom subagents - Claude Code Docs
    - level: source_url
      url: https://github.com/shenli/distributed-system-testing
      title: AI-agent skills for distributed-systems testing - GitHub
    - level: source_url
      url: https://news.ycombinator.com/item?id=47866913
      title: Over-editing refers to a model modifying code beyond what is necessary - Hacker News
    - level: source_url
      url: https://hidekazu-konishi.com/entry/claude_code_hooks_complete_guide.html
      title: Claude Code Hooks Complete Guide - Deterministic Enforcement Across the Tool Lifecycle
    - level: source_url
      url: https://code.claude.com/docs/en/memory
      title: How Claude remembers your project - Claude Code Docs
    - level: source_url
      url: https://github.com/anthropics/claude-code/issues/52822
      title: [BUG] PreToolUse hook permissionDecision 'allow' does not suppress native permission prompt in interactive mode (v2.1.119) · Issue #52822 · anthropics/claude-code - GitHub
    - level: source_url
      url: https://github.com/snap-stanford/POPPER
      title: GitHub - snap-stanford/POPPER: Automated Hypothesis Testing with Agentic Sequential Falsifications
    - level: source_url
      url: https://docs.claudekit.cc/docs/engineer/configuration/hooks
      title: Hooks - ClaudeKit Documentation
relations:
  - target: wiki/concepts/claude-code-hooks.md
    type: related
  - target: wiki/concepts/claude.md-configuration.md
    type: related
  - target: wiki/concepts/agent-harness-engineering.md
    type: related
---

# Self-Correction Reflection Loop

## Decision context

**Definition:** The self-correction reflection loop is a design pattern for coding agents that enables automatic retry after failed edits by providing structured error feedback, allowing the agent to反思 and adjust its approach without manual intervention.

Synthesized from **30 contributing transcripts** in NotebookLM notebook *Deep Research Prompts, Methods, Examples*, clustered into the "https-claude-code" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The pattern was inspired by Aider and proposed as a feature in the NousResearch/hermes-agent project (Issue #536)
- Structured error feedback is provided to the agent after failed edits, enabling it to understand what went wrong
- The agent automatically retries with adjusted parameters based on the received error information
- Hooks in Claude Code serve as a deterministic enforcement layer that can intercept tool execution and inject behavioral modifications
- Multiple hook events exist across the tool lifecycle, including before tool execution (PreToolUse) and after completion
- The coding agent loop can be specified and controlled through configuration files and harness engineering
- Over-editing refers to a model modifying code beyond what is necessary, which self-correction loops aim to mitigate
- CLAUDE.md files serve as a primary context mechanism for establishing agent behavior patterns and constraints
- The pattern relates to self-improving agents that can iteratively refine their approach based on failure feedback

## Verifiable values

| Name | Value |
|---|---|
| configuration count reported | `116 configurations in one Claude Code setup` |
| self-correction approach | `automatic retry with structured error feedback` |

## Related concepts

- [[claude-code-hooks]] — Claude Code Hooks
- [[claude.md-configuration]] — CLAUDE.md Configuration
- [[agent-harness-engineering]] — Agent Harness Engineering
- [[over-editing-mitigation]] — Over-editing Mitigation

## Citations (from contributing transcripts)

- **Claim:** The self-correction reflection loop pattern was inspired by Aider and proposed as a feature in the NousResearch/hermes-agent project
  - Source: Self-Correction Reflection Loop — Automatic Retry with Structured Error Feedback After Failed Edits (inspired by Aider) · Issue #536 · NousResearch/hermes-agent - GitHub (`0b7ca6d8-c548-4abd-83cb-75b167f93f33`)
  - Context: Feature: Self-Correction Reflection Loop — Automatic Retry with Structured Error Feedback After Failed Edits (inspired by Aider)
- **Claim:** Hooks serve as a deterministic enforcement layer around the agent that can intercept and modify behavior
  - Source: Claude Code Hooks Explained: The Deterministic Layer Around Your Agent - Blake Crosley (`145c11fd-9d12-47d6-b8e4-0de05d7c8c4e`)
  - Context: Claude Code Hooks Explained: The Deterministic Layer Around Your Agent
- **Claim:** A setup with 116 configurations demonstrates the complexity possible in Claude Code organizational patterns
  - Source: Inside a 116-Configuration Claude Code Setup: Skills, Hooks, Agents, and the Layering That Makes It Work - Reddit (`12f40133-5dc0-45d4-8f77-d1fae6d9d3e9`)
  - Context: Inside a 116-Configuration Claude Code Setup
- **Claim:** Over-editing refers to a model modifying code beyond what is necessary, a behavior that self-correction loops aim to mitigate
  - Source: Over-editing refers to a model modifying code beyond what is necessary - Hacker News (`dc14252f-5350-4a5b-b0ea-ae92fd32ae8a`)
  - Context: Over-editing refers to a model modifying code beyond what is necessary
- **Claim:** Claude Code provides hooks as a mechanism to automate actions at various points in the tool lifecycle
  - Source: Automate actions with hooks - Claude Code Docs (`3f6f6772-68ba-4b37-8c19-48444cf0dc1e`)
  - Context: Automate actions with hooks - Claude Code Docs
- **Claim:** CLAUDE.md files serve as a primary mechanism for establishing agent behavior patterns
  - Source: Writing a good CLAUDE.md | HumanLayer Blog (`364145b1-ee6b-4f5a-bc56-9cf64b365321`)
  - Context: LLMs are stateless functions. Their weights are frozen by the time they're used for inference

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `590ac9fd-01f0-4b85-97ff-7d49bd5ed78d`
(cluster `https-claude-code`). No claims are made
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

- NotebookLM notebook [Deep Research Prompts, Methods, Examples](https://notebooklm.google.com/notebook/590ac9fd-01f0-4b85-97ff-7d49bd5ed78d)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
