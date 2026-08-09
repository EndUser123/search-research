---
title: "AI Prompting Optimization Techniques"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, claude]
summary: >
  A collection of approaches for maximizing AI assistant effectiveness through configuration settings, prompt structure modifications, and contextual customization, driven by the observation that newer AI models interpret instructions with increased literalness and that default responses tend toward g
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 23bf4931-d0cb-4550-9d11-f9b38843254a" (WL-Pilot: Claude Skills & Code, synced 2026-07-27)
  - "NotebookLM source 1372f1bf-d46e-4667-8ff8-4fc9972ab84a" (3 Claude Settings That Make It Super Powerful, synced 2026-07-27)
  - "NotebookLM source 14a31c42-3616-4cdd-98e4-bf1a28ca39b8" (Your Best Prompts Make the New Claude Worse, synced 2026-07-27)
  - "NotebookLM source 308fb766-de3c-4081-9b7b-9f7bcc8d0963" (Claude and ChatGPT Got More Literal. Your Old Prompts Are Backfiring, synced 2026-07-27)
  - "NotebookLM source 4b746787-86cc-45ef-8d2a-d6384a1e50e9" (The Skill That 10x’d My Claude Code Projects, synced 2026-07-27)
  - "NotebookLM source 55b2212f-e6d8-4f83-880b-cc5d2c16c0fa" (Add THIS Before Every AI Prompt! (Gemini, ChatGPT, Claude), synced 2026-07-27)
  - "NotebookLM source 582adee1-7db8-4c8e-9237-eb1ee7fb9f07" (ChatGPT & Claude Are Built to Give You the Average Answer, synced 2026-07-27)
  - "NotebookLM source 64b7ef22-8b36-4e50-a63a-6eec42b6fe04" (Claude and ChatGPT Gets Smarter When You Change This One Setting, synced 2026-07-27)
  - "NotebookLM source 6cd1f07c-58b2-44bf-87f3-5d90abe32c9a" (The prompting playbook, synced 2026-07-27)
  - "NotebookLM source edd6be9f-e00b-42cd-a223-170e72db8656" (Advanced Claude Prompt Tricks You Need to Know., synced 2026-07-27)
provenance:
  chain:
    - level: concept
      id: ai-prompting-optimization-techniques
    - level: notebook
      id: 23bf4931-d0cb-4550-9d11-f9b38843254a
      title: WL-Pilot: Claude Skills & Code
      url: https://notebooklm.google.com/notebook/23bf4931-d0cb-4550-9d11-f9b38843254a
    - level: cluster
      id: 5
      name: claude-chatgpt-prompt
relations:
  - target: wiki/concepts/ai-contextual-customization.md
    type: related
  - target: wiki/concepts/model-reasoning-levels.md
    type: related
  - target: wiki/concepts/prompt-structure-optimization.md
    type: related
---

# AI Prompting Optimization Techniques

## Decision context

**Definition:** A collection of approaches for maximizing AI assistant effectiveness through configuration settings, prompt structure modifications, and contextual customization, driven by the observation that newer AI models interpret instructions with increased literalness and that default responses tend toward generic outputs.

Synthesized from **9 contributing transcripts** in NotebookLM notebook *WL-Pilot: Claude Skills & Code*, clustered into the "claude-chatgpt-prompt" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Newer models such as Fable 5, Opus 4.7/4.8, and GPT5.5 take user prompts more literally, making word choice more consequential than with previous generations [source 2, 3]
- Extended multi-step prompts designed for older models can cause newer models to execute unintended actions or generate excessive outputs [source 2]
- Memory settings enable AI to retain project context, preferences, and user information across conversations [source 1]
- Style settings allow users to define tone preferences (normal, learning, concise, explanatory, or custom) that persist across conversations [source 1]
- Connected apps integration permits AI to access actual files and data from Google Drive, Notion, Gmail, and Calendar [source 1]
- Model selection and reasoning level settings significantly impact output quality; the presenter checks these settings before examining prompts when clients report issues [source 7]
- Adding personal context, taste, and voice to prompts differentiates outputs when multiple users operate the same model [source 4]
- Slash commands such as /ghost produce more natural writing, /artifacts generate interactive outputs, and L99 produces expert-level depth [source 9]
- AI models default to the most common answer when responding to general queries, producing average outputs that other users also receive [source 6]

## Verifiable values

| Name | Value |
|---|---|
| Recommended memory settings | `Both memory options enabled in capabilities` |
| Prompt modifications needed for newer models | `Shorter, more precise prompts replacing verbose multi-step instructions` |
| Slash commands available | `/ghost, /artifacts, OODA, L99, /God mode` |

## Related concepts

- ai-contextual-customization — AI Contextual Customization
- model-reasoning-levels — Model Reasoning Levels
- prompt-structure-optimization — Prompt Structure Optimization
- slash-command-patterns — Slash Command Patterns

## Citations (from contributing transcripts)

- **Claim:** Newer models like Fable 5 and GPT5.6 take user prompts more literally, requiring more precise word choice
  - Source: Claude and ChatGPT Got More Literal. Your Old Prompts Are Backfiring (`308fb766-de3c-4081-9b7b-9f7bcc8d0963`)
  - Context: the primary thing that's changed that's impacting a lot of people's prompts is the fact that these models take you more literally
- **Claim:** Extended multi-step prompts can cause newer models to execute unintended actions
  - Source: Your Best Prompts Make the New Claude Worse (`14a31c42-3616-4cdd-98e4-bf1a28ca39b8`)
  - Context: it'll run for hours take actions that you never asked for or even claim it finished work it never touched
- **Claim:** Memory settings allow AI to retain context across conversations
  - Source: 3 Claude Settings That Make It Super Powerful (`1372f1bf-d46e-4667-8ff8-4fc9972ab84a`)
  - Context: Claude remembers your projects your preferences even your name across every single conversation
- **Claim:** Connected apps integration enables AI to access actual files and data
  - Source: 3 Claude Settings That Make It Super Powerful (`1372f1bf-d46e-4667-8ff8-4fc9972ab84a`)
  - Context: connect your tools GoogleDrive notion Gmail and calendar a plot can pull your actual files and data into the conversation
- **Claim:** Model and reasoning level settings are checked before prompts when troubleshooting AI issues
  - Source: Claude and ChatGPT Gets Smarter When You Change This One Setting (`64b7ef22-8b36-4e50-a63a-6eec42b6fe04`)
  - Context: the first thing that I do is have them share their screen with me and I look at exactly which model they're using and which reasoning level
- **Claim:** Adding personal context differentiates outputs from other users of the same model
  - Source: The Skill That 10x'd My Claude Code Projects
  - Context: what really makes the difference is when you add context into that model and you give it your taste your voice your decisions
- **Claim:** AI models default to the most common answer for general queries
  - Source: ChatGPT & Claude Are Built to Give You the Average Answer (`582adee1-7db8-4c8e-9237-eb1ee7fb9f07`)
  - Context: both ChatBT and Claude are built to give you the average answer the middle of everything that they've read
- **Claim:** Slash commands provide specialized output behaviors
  - Source: Advanced Claude Prompt Tricks You Need to Know. (`edd6be9f-e00b-42cd-a223-170e72db8656`)
  - Context: / ghost add this before your prompt when you want the writing to sound more natural and / artifacts use this after your prompt and Claude can generate interactive outputs

## What this means for our workspace

Synced from NotebookLM. Provenance chain (concept → notebook → cluster → URL) is in frontmatter; follow it back to the source material.

## Falsifier

If a re-sync of the source notebook produces a different definition or different values, this page should be updated (or marked as superseded). The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records when this page was last regenerated.

## Sources

- NotebookLM notebook [WL-Pilot: Claude Skills & Code](https://notebooklm.google.com/notebook/23bf4931-d0cb-4550-9d11-f9b38843254a)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
