---
title: "Claude Code Worktree Isolation"
created: 2026-08-09
source: nlm-sync-2026-08-09
tags: [nlm-synced, reference, claude]
summary: >
  A method utilizing Git worktrees to run multiple Claude Code sessions or subagents in parallel within isolated directories to prevent file conflicts and shared state corruption.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook afd2f1dd-ff64-44f7-9259-6f923b6c081a" (Claude Code Worktree Guide: Hooks, Setup, and Parallel Workflows, synced 2026-08-09)
  - "Run agents in parallel - Claude Code Docs" (https://code.claude.com/docs/en/agents, transcript synced 2026-08-09)
  - "5 claude code worktree tips from creator of claude code in feb 2026 : r/ClaudeCode - Reddit" (https://www.reddit.com/r/ClaudeCode/comments/1rae7sa/5_claude_code_worktree_tips_from_creator_of/, transcript synced 2026-08-09)
  - "Creating worktrees with Claude Code in a custom directory - sabatino.dev" (https://www.sabatino.dev/creating-worktrees-with-claude-code-in-a-custom-directory/, transcript synced 2026-08-09)
  - "Auto-setup hooks for Claude Code worktrees: env files, dependencies, and deterministic ports - GitHub" (https://github.com/tfriedel/claude-worktree-hooks, transcript synced 2026-08-09)
  - "Manage multiple agents with agent view - Claude Code Docs" (https://code.claude.com/docs/en/agent-view, transcript synced 2026-08-09)
  - "Claude Code Git Worktree Support for Parallel Agents - SuperGok" (https://supergok.com/claude-code-git-worktree-support/, transcript synced 2026-08-09)
  - "Git Worktrees + Claude Code: The 2026 Playbook for Running Parallel Agents Without Context Switching - Developers Digest" (https://www.developersdigest.tech/blog/git-worktrees-claude-code-parallel-agents-guide, transcript synced 2026-08-09)
  - "Hooks 參考- Claude Code Docs" (https://code.claude.com/docs/zh-TW/hooks, transcript synced 2026-08-09)
  - "Claude Code Hooks Explained: The Deterministic Layer Around Your Agent - Blake Crosley" (https://blakecrosley.com/pl/blog/claude-code-hooks-explained, transcript synced 2026-08-09)
  - "Git Worktrees in Claude Code - Run Parallel AI Sessions - codewithmukesh" (https://codewithmukesh.com/blog/git-worktrees-claude-code/, transcript synced 2026-08-09)
  - "Parallel Vibe Coding: Using Git Worktrees with Claude Code | Dan Does Code" (https://www.dandoescode.com/blog/parallel-vibe-coding-with-git-worktrees, transcript synced 2026-08-09)
  - "Automate actions with hooks - Claude Code Docs" (https://code.claude.com/docs/en/hooks-guide, transcript synced 2026-08-09)
  - "Claude Code Worktrees: Setting Up Parallel Work with - Felix Schmidt" (https://felixschmidt.software/en/blog/claude-code-worktrees-2026, transcript synced 2026-08-09)
  - "Claude Code Worktrees Guide (2026): Parallel Agents Without Conflicts" (https://claudedirectory.org/blog/claude-code-worktrees-guide, transcript synced 2026-08-09)
  - "NotebookLM source 7f60d8bd-8b2f-41f6-808a-fb02212e123b" (Orchestration Blueprint for Concurrent Claude Code Sessions: Multi-Agent Worktree Isolation and Lifecycle Integration, synced 2026-08-09)
  - "5 claude code worktree tips from creator of claude code in feb 2026 : r/ClaudeAI - Reddit" (https://www.reddit.com/r/ClaudeAI/comments/1rae05r/5_claude_code_worktree_tips_from_creator_of/, transcript synced 2026-08-09)
  - "Intercept and control agent behavior with hooks - Claude Code Docs" (https://code.claude.com/docs/en/agent-sdk/hooks, transcript synced 2026-08-09)
  - "Claude Code Worktrees: Run Parallel Sessions Without Conflicts" (https://claudefa.st/blog/guide/development/worktree-guide, transcript synced 2026-08-09)
  - "Hooks reference - Claude Code Docs" (https://code.claude.com/docs/en/hooks, transcript synced 2026-08-09)
  - "Week 15 · April 6–10, 2026 - Claude Code Docs" (https://code.claude.com/docs/en/whats-new/2026-w15, transcript synced 2026-08-09)
  - "Run parallel sessions with worktrees - Claude Code Docs" (https://code.claude.com/docs/en/worktrees, transcript synced 2026-08-09)
  - "We ditched worktrees for Claude Code. Here's what we use instead - Trigger.dev" (https://trigger.dev/blog/parallel-agents-gitbutler, transcript synced 2026-08-09)
provenance:
  chain:
    - level: concept
      id: claude-code-worktree-isolation
    - level: notebook
      id: afd2f1dd-ff64-44f7-9259-6f923b6c081a
      title: Claude Code Worktree Guide: Hooks, Setup, and Parallel Workflows
      url: https://notebooklm.google.com/notebook/afd2f1dd-ff64-44f7-9259-6f923b6c081a
    - level: cluster
      id: 0
      name: claude-code-https
    - level: source_url
      url: https://code.claude.com/docs/en/agents
      title: Run agents in parallel - Claude Code Docs
    - level: source_url
      url: https://www.reddit.com/r/ClaudeCode/comments/1rae7sa/5_claude_code_worktree_tips_from_creator_of/
      title: 5 claude code worktree tips from creator of claude code in feb 2026 : r/ClaudeCode - Reddit
    - level: source_url
      url: https://www.sabatino.dev/creating-worktrees-with-claude-code-in-a-custom-directory/
      title: Creating worktrees with Claude Code in a custom directory - sabatino.dev
    - level: source_url
      url: https://github.com/tfriedel/claude-worktree-hooks
      title: Auto-setup hooks for Claude Code worktrees: env files, dependencies, and deterministic ports - GitHub
    - level: source_url
      url: https://code.claude.com/docs/en/agent-view
      title: Manage multiple agents with agent view - Claude Code Docs
    - level: source_url
      url: https://supergok.com/claude-code-git-worktree-support/
      title: Claude Code Git Worktree Support for Parallel Agents - SuperGok
    - level: source_url
      url: https://www.developersdigest.tech/blog/git-worktrees-claude-code-parallel-agents-guide
      title: Git Worktrees + Claude Code: The 2026 Playbook for Running Parallel Agents Without Context Switching - Developers Digest
    - level: source_url
      url: https://code.claude.com/docs/zh-TW/hooks
      title: Hooks 參考- Claude Code Docs
    - level: source_url
      url: https://blakecrosley.com/pl/blog/claude-code-hooks-explained
      title: Claude Code Hooks Explained: The Deterministic Layer Around Your Agent - Blake Crosley
    - level: source_url
      url: https://codewithmukesh.com/blog/git-worktrees-claude-code/
      title: Git Worktrees in Claude Code - Run Parallel AI Sessions - codewithmukesh
    - level: source_url
      url: https://www.dandoescode.com/blog/parallel-vibe-coding-with-git-worktrees
      title: Parallel Vibe Coding: Using Git Worktrees with Claude Code | Dan Does Code
    - level: source_url
      url: https://code.claude.com/docs/en/hooks-guide
      title: Automate actions with hooks - Claude Code Docs
    - level: source_url
      url: https://felixschmidt.software/en/blog/claude-code-worktrees-2026
      title: Claude Code Worktrees: Setting Up Parallel Work with - Felix Schmidt
    - level: source_url
      url: https://claudedirectory.org/blog/claude-code-worktrees-guide
      title: Claude Code Worktrees Guide (2026): Parallel Agents Without Conflicts
    - level: source_url
      url: https://www.reddit.com/r/ClaudeAI/comments/1rae05r/5_claude_code_worktree_tips_from_creator_of/
      title: 5 claude code worktree tips from creator of claude code in feb 2026 : r/ClaudeAI - Reddit
    - level: source_url
      url: https://code.claude.com/docs/en/agent-sdk/hooks
      title: Intercept and control agent behavior with hooks - Claude Code Docs
    - level: source_url
      url: https://claudefa.st/blog/guide/development/worktree-guide
      title: Claude Code Worktrees: Run Parallel Sessions Without Conflicts
    - level: source_url
      url: https://code.claude.com/docs/en/hooks
      title: Hooks reference - Claude Code Docs
    - level: source_url
      url: https://code.claude.com/docs/en/whats-new/2026-w15
      title: Week 15 · April 6–10, 2026 - Claude Code Docs
    - level: source_url
      url: https://code.claude.com/docs/en/worktrees
      title: Run parallel sessions with worktrees - Claude Code Docs
    - level: source_url
      url: https://trigger.dev/blog/parallel-agents-gitbutler
      title: We ditched worktrees for Claude Code. Here's what we use instead - Trigger.dev

---

# Claude Code Worktree Isolation

## Decision context

**Definition:** A method utilizing Git worktrees to run multiple Claude Code sessions or subagents in parallel within isolated directories to prevent file conflicts and shared state corruption.

Synthesized from **22 contributing transcripts** in NotebookLM notebook *Claude Code Worktree Guide: Hooks, Setup, and Parallel Workflows*, clustered into the "claude-code-https" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Related concepts

- [[notebooklm-cli-operational-gotchas]] — operational traps for the nlm CLI
- [[nlm-synced]] — other concepts synced from NotebookLM
- [[claude-code-worktree-guide:-hooks,-setup,-and-parallel-workflows]] — source notebook

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `afd2f1dd-ff64-44f7-9259-6f923b6c081a`
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

- NotebookLM notebook [Claude Code Worktree Guide: Hooks, Setup, and Parallel Workflows](https://notebooklm.google.com/notebook/afd2f1dd-ff64-44f7-9259-6f923b6c081a)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
