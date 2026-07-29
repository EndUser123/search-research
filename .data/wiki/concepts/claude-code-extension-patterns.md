---
title: "Claude Code Extension Patterns"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, reddit]
summary: >
  Claude Code supports multiple extension approaches that allow users to customize behavior, automate workflows, and enhance the AI assistant's capabilities through prompts, hooks, skills, and plugins.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 29bbaa7b-965f-40b5-a404-76b4d2e7308c" (Claude Code - Skills: Agentic Coding and Prompt Engineering, synced 2026-07-27)
  - "Claude code vs Aider : r/ClaudeAI - Reddit" (https://www.reddit.com/r/ClaudeAI/comments/1lv8p26/claude_code_vs_aider/, transcript synced 2026-07-27)
  - "A quick guide to Ralph Wiggum : r/ClaudeAI - Reddit" (https://www.reddit.com/r/ClaudeAI/comments/1pxc31u/a_quick_guide_to_ralph_wiggum/, transcript synced 2026-07-27)
  - "Pseudo-PostCompact Hook—Reminding Claude of what it should already know - Reddit" (https://www.reddit.com/r/ClaudeAI/comments/1qws098/pseudopostcompact_hookreminding_claude_of_what_it/, transcript synced 2026-07-27)
  - "Simplest guide to claude skills : r/ClaudeAI - Reddit" (https://www.reddit.com/r/ClaudeAI/comments/1rsa8vm/simplest_guide_to_claude_skills/, transcript synced 2026-07-27)
  - "Examples of 'extreme' Claude Code workflows : r/ClaudeCode - Reddit" (https://www.reddit.com/r/ClaudeCode/comments/1rzbb3n/examples_of_extreme_claude_code_workflows/, transcript synced 2026-07-27)
  - "Claude Code Hooks - all 23 explained and implemented : r/ClaudeAI - Reddit" (https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/claude_code_hooks_all_23_explained_and_implemented/, transcript synced 2026-07-27)
  - "What's your go-to prompt structure for Claude Code? : r/ClaudeCode - Reddit" (https://www.reddit.com/r/ClaudeCode/comments/1rtizvs/whats_your_goto_prompt_structure_for_claude_code/, transcript synced 2026-07-27)
  - "This Meta-Prompt Will 100X Claude Code : r/ClaudeAI - Reddit" (https://www.reddit.com/r/ClaudeAI/comments/1owdtaa/this_metaprompt_will_100x_claude_code/, transcript synced 2026-07-27)
  - "Your SKILL.md doesn't have to be static, you can make the script write the prompt - Reddit" (https://www.reddit.com/r/ClaudeCode/comments/1rsmntd/your_skillmd_doesnt_have_to_be_static_you_can/, transcript synced 2026-07-27)
  - "Understanding Claude Code's 3 system prompt methods (Output Styles - Reddit" (https://www.reddit.com/r/ClaudeCode/comments/1o65jva/understanding_claude_codes_3_system_prompt/, transcript synced 2026-07-27)
  - "Ralph Wiggum plugin for Claude Code (set it, walk away, come back to finished code) : r/ClaudeAI - Reddit" (https://www.reddit.com/r/ClaudeAI/comments/1qy35lc/ralph_wiggum_plugin_for_claude_code_set_it_walk/, transcript synced 2026-07-27)
provenance:
  chain:
    - level: concept
      id: claude-code-extension-patterns
    - level: notebook
      id: 29bbaa7b-965f-40b5-a404-76b4d2e7308c
      title: Claude Code - Skills: Agentic Coding and Prompt Engineering
      url: https://notebooklm.google.com/notebook/29bbaa7b-965f-40b5-a404-76b4d2e7308c
    - level: cluster
      id: 4
      name: reddit-claude-claudeai
    - level: source_url
      url: https://www.reddit.com/r/ClaudeAI/comments/1lv8p26/claude_code_vs_aider/
      title: Claude code vs Aider : r/ClaudeAI - Reddit
    - level: source_url
      url: https://www.reddit.com/r/ClaudeAI/comments/1pxc31u/a_quick_guide_to_ralph_wiggum/
      title: A quick guide to Ralph Wiggum : r/ClaudeAI - Reddit
    - level: source_url
      url: https://www.reddit.com/r/ClaudeAI/comments/1qws098/pseudopostcompact_hookreminding_claude_of_what_it/
      title: Pseudo-PostCompact Hook—Reminding Claude of what it should already know - Reddit
    - level: source_url
      url: https://www.reddit.com/r/ClaudeAI/comments/1rsa8vm/simplest_guide_to_claude_skills/
      title: Simplest guide to claude skills : r/ClaudeAI - Reddit
    - level: source_url
      url: https://www.reddit.com/r/ClaudeCode/comments/1rzbb3n/examples_of_extreme_claude_code_workflows/
      title: Examples of 'extreme' Claude Code workflows : r/ClaudeCode - Reddit
    - level: source_url
      url: https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/claude_code_hooks_all_23_explained_and_implemented/
      title: Claude Code Hooks - all 23 explained and implemented : r/ClaudeAI - Reddit
    - level: source_url
      url: https://www.reddit.com/r/ClaudeCode/comments/1rtizvs/whats_your_goto_prompt_structure_for_claude_code/
      title: What's your go-to prompt structure for Claude Code? : r/ClaudeCode - Reddit
    - level: source_url
      url: https://www.reddit.com/r/ClaudeAI/comments/1owdtaa/this_metaprompt_will_100x_claude_code/
      title: This Meta-Prompt Will 100X Claude Code : r/ClaudeAI - Reddit
    - level: source_url
      url: https://www.reddit.com/r/ClaudeCode/comments/1rsmntd/your_skillmd_doesnt_have_to_be_static_you_can/
      title: Your SKILL.md doesn't have to be static, you can make the script write the prompt - Reddit
    - level: source_url
      url: https://www.reddit.com/r/ClaudeCode/comments/1o65jva/understanding_claude_codes_3_system_prompt/
      title: Understanding Claude Code's 3 system prompt methods (Output Styles - Reddit
    - level: source_url
      url: https://www.reddit.com/r/ClaudeAI/comments/1qy35lc/ralph_wiggum_plugin_for_claude_code_set_it_walk/
      title: Ralph Wiggum plugin for Claude Code (set it, walk away, come back to finished code) : r/ClaudeAI - Reddit
relations:
  - target: wiki/concepts/claude-code-hooks.md
    type: related
  - target: wiki/concepts/claude-skills.md
    type: related
  - target: wiki/concepts/system-prompt-methods.md
    type: related
---

# Claude Code Extension Patterns

## Decision context

**Definition:** Claude Code supports multiple extension approaches that allow users to customize behavior, automate workflows, and enhance the AI assistant's capabilities through prompts, hooks, skills, and plugins.

Synthesized from **11 contributing transcripts** in NotebookLM notebook *Claude Code - Skills: Agentic Coding and Prompt Engineering*, clustered into the "reddit-claude-claudeai" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Claude Code provides three system prompt methods: Output Styles, --append-system-prompt, and --system-prompt flags for customizing behavior
- The platform exposes 23 distinct hooks that can be implemented to intercept and modify execution phases
- Skills are created through SKILL.md files, which can be dynamically generated by scripts rather than static content
- The Ralph Wiggum technique is a plugin pattern that automates task completion, allowing users to set parameters and retrieve finished code
- Meta-prompts are structured prompt templates designed to optimize Claude Code performance and output quality
- Community members compare Claude Code with alternatives like Aider, noting both use agentic workflows under the hood

## Verifiable values

| Name | Value |
|---|---|
| number of hooks available | `23 hooks` |
| system prompt methods | `3 methods (Output Styles, --append-system-prompt, --system-prompt)` |

## Related concepts

- [[claude-code-hooks]] — Claude Code Hooks
- [[claude-skills]] — Claude Skills
- [[system-prompt-methods]] — System Prompt Methods
- [[meta-prompts]] — Meta-Prompts
- [[ralph-wiggum-technique]] — Ralph Wiggum Technique

## Citations (from contributing transcripts)

- **Claim:** Claude Code provides three system prompt methods
  - Source: Understanding Claude Code's 3 system prompt methods (Output Styles - Reddit (`d6d88b25-0c25-4529-9933-9368b473eba4`)
  - Context: Understanding Claude Code's 3 system prompt methods (Output Styles, --append-system-prompt, --system-prompt)
- **Claim:** Claude Code exposes 23 hooks that can be implemented
  - Source: Claude Code Hooks - all 23 explained and implemented : r/ClaudeAI - Reddit (`8e5a3217-acee-4675-acd3-fc7aabda49d5`)
  - Context: Claude Code Hooks - all 23 explained and implemented
- **Claim:** SKILL.md files can be dynamically generated by scripts
  - Source: Your SKILL.md doesn't have to be static, you can make the script write the prompt - Reddit (`d692cbef-e461-4d12-894e-e0338e631700`)
  - Context: Your SKILL.md doesn't have to be static, you can make the script write the prompt
- **Claim:** Ralph Wiggum is a plugin technique for automated code completion
  - Source: Ralph Wiggum plugin for Claude Code (set it, walk away, come back to finished code) : r/ClaudeAI - Reddit (`ec2ec7b7-5165-4e73-a2d1-b725c42429c1`)
  - Context: Ralph Wiggum plugin for Claude Code (set it, walk away, come back to finished code)
- **Claim:** Meta-prompts are designed to enhance Claude Code performance
  - Source: This Meta-Prompt Will 100X Claude Code : r/ClaudeAI - Reddit (`c3e1884b-af85-445d-a063-606357326640`)
  - Context: This Meta-Prompt Will 100X Claude Code
- **Claim:** Claude Code uses agentic workflows similar to other AI coding assistants
  - Source: Claude code vs Aider : r/ClaudeAI - Reddit (`174777ac-1717-47da-a7b5-3e6ab1d2b3c1`)
  - Context: both very capable interfaces, apply agentic workflow under the hood

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `29bbaa7b-965f-40b5-a404-76b4d2e7308c`
(cluster `reddit-claude-claudeai`). No claims are made
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

- NotebookLM notebook [Claude Code - Skills: Agentic Coding and Prompt Engineering](https://notebooklm.google.com/notebook/29bbaa7b-965f-40b5-a404-76b4d2e7308c)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
