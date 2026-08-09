---
title: "AI Agent Skill Design Patterns"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, going]
summary: >
  AI agent skills are reusable instruction sets that extend the capabilities of AI coding agents by providing structured approaches to specific tasks such as planning, handoff between sessions, and self-directed learning.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 7ef4d1e8-319f-4e27-a751-e777ddc2b723" (WL: Anthropic & Agent Ecosystem, synced 2026-07-27)
  - "NotebookLM source 0ae9ab2d-a3f0-4d27-85c2-49c6f83cfd21" (How to Teach Yourself Anything (The Self-Study Blueprint), synced 2026-07-27)
  - "NotebookLM source 21071493-6c1c-413f-9dc2-26ad63d0736f" (Master AI Filmmaking in 30 Minutes - Advanced AI Video Course, synced 2026-07-27)
  - "NotebookLM source 222a63f5-5e93-4201-8cd9-2471e1224917" (Learn to use AI as your strategic thought partner | Google AI Professional Certificate, synced 2026-07-27)
  - "NotebookLM source 2654d4e1-f195-4d1e-9b1a-ef89778d422e" (The Prompt Formula That Makes AI Images Look Too Real, synced 2026-07-27)
  - "NotebookLM source 28166c0c-728f-40c2-bbbf-d9e0bb313526" (If you master this one characteristic, you will win in life., synced 2026-07-27)
  - "NotebookLM source 44f8727c-6c3f-4bb2-948f-111e29edc510" (My AI Presentation Setup For Teaching and Coaching Online, synced 2026-07-27)
  - "NotebookLM source 4f4afa6a-9553-4a53-a6d9-64575d5f7934" (Combine Skills and MCP to Close the Context Gap — Pedro Rodrigues, Supabase, synced 2026-07-27)
  - "NotebookLM source 50278f5e-bd7d-44ac-9176-24f491097aea" (Your Teaching Experience Doesn't Matter Anymore — AI Changed Everything, synced 2026-07-27)
  - "NotebookLM source 507f4144-7b16-4b08-b9e2-4c50a69607ee" (6/10/2026 - Why You Need to Stop Prompting and Start Designing AI Loops, synced 2026-07-27)
  - "NotebookLM source 576b3c03-2224-4335-bdbd-6d42d9ce4873" (4 easy tips for writing better AI prompts | Kunalsinh Kathia | TEDxSaffrony Institute of Technology, synced 2026-07-27)
  - "NotebookLM source 57b46c80-8547-40ed-8a0c-4e3508b3647b" (Claude Design’s New Features: Worth It or Too Expensive?, synced 2026-07-27)
  - "NotebookLM source 5ed33833-d4c5-4020-932b-2394f72f13e0" (This change makes /grill-me SO MUCH BETTER, synced 2026-07-27)
  - "NotebookLM source 69b269f8-a18b-40c1-add1-517cf538fd66" (I Used GPT-5.6-Sol to Scan Codebase and Build a Diagram, synced 2026-07-27)
  - "NotebookLM source 741b7513-349d-4fd1-86b6-8c0d7336b6cd" (/handoff is my new favourite skill, synced 2026-07-27)
  - "NotebookLM source 7a1e1113-4482-4bed-a0ae-c3d2d1c18c6b" (New Skills! v1.1 brings /wayfinder, /research, /implement, /to-spec, /to-tickets, synced 2026-07-27)
  - "NotebookLM source 7bf47ce3-b552-4a2f-8b34-fb7510b2fda2" (Stop Using AI For This, synced 2026-07-27)
  - "NotebookLM source 7c08c6ce-5e82-4ee3-b57e-850df61fdd51" (Don't waste time on specs: /prototype instead, synced 2026-07-27)
  - "NotebookLM source b40d64c4-927a-4c3a-b884-bdbaef8491e4" (grill-me + Codex: The Planning Workflow That Caught My Bug, synced 2026-07-27)
  - "NotebookLM source b6632a79-5178-4c1d-b5a7-eadb249576bc" (Build Your First AI Web Researcher in Minutes, synced 2026-07-27)
  - "NotebookLM source bb370ebd-b7ac-4c89-b403-a01253e6fc8c" (I Found One Prompt Change For Better AI Code, synced 2026-07-27)
  - "NotebookLM source bb4345a9-e55c-498c-b7ad-c3c12795d43c" (What the Best Agents Share — Mardu Swanepoel, Flinn AI, synced 2026-07-27)
  - "NotebookLM source bfc178f0-9a66-4585-8e2c-f1102f1d6293" (How to be a NotebookLM Ninja: Five Simple Tips, synced 2026-07-27)
  - "NotebookLM source c664b9c0-429d-4ca7-a2b2-ece5d28dd898" (Help AI Finally Understand You — in 13 Minutes, synced 2026-07-27)
  - "NotebookLM source cfddbcb7-2669-4270-a8e7-47a4a116f355" (I Tried /teach and 10x'd My Ability To Learn, synced 2026-07-27)
  - "NotebookLM source e3518c73-0cd0-4bd3-b0c1-e77723023afe" (Building Great Agent Skills: The Missing Manual, synced 2026-07-27)
  - "NotebookLM source eed6a6cc-0202-476f-92a6-3d89848510b1" (7 Prompts To Setup Auto AI Research, synced 2026-07-27)
  - "NotebookLM source f21b8491-9d0d-4d64-ba84-969482bdaf04" (I Tried /grill-with-docs Skill: Massive Difference, synced 2026-07-27)
  - "NotebookLM source f76d7206-bd9a-4026-ad20-4a43a15b4a6a" (9 Things People Get Wrong With My /grill-* skills, synced 2026-07-27)
  - "NotebookLM source f7ba3ce1-2401-48bc-96f7-2ef2762881d5" (Full Workshop: Build Your Own Deep Research Agents - Louis-François Bouchard, Paul Iusztin, Samridhi, synced 2026-07-27)
  - "NotebookLM source fa370541-0aac-423e-b9dc-b54a88dc67c2" (99% of Beginners Never Use These Two Prompts, synced 2026-07-27)
  - "NotebookLM source ff5c4820-3600-4cc7-9cf3-01d0921d924c" (How To Write a Literature Review With AI (Without Getting Caught Lying), synced 2026-07-27)
provenance:
  chain:
    - level: concept
      id: ai-agent-skill-design-patterns
    - level: notebook
      id: 7ef4d1e8-319f-4e27-a751-e777ddc2b723
      title: WL: Anthropic & Agent Ecosystem
      url: https://notebooklm.google.com/notebook/7ef4d1e8-319f-4e27-a751-e777ddc2b723
    - level: cluster
      id: 1
      name: going-skills-grill
relations:
  - target: wiki/concepts/context-management.md
    type: related
  - target: wiki/concepts/prompt-engineering.md
    type: related
  - target: wiki/concepts/ai-agent-workflows.md
    type: related
---

# AI Agent Skill Design Patterns

## Decision context

**Definition:** AI agent skills are reusable instruction sets that extend the capabilities of AI coding agents by providing structured approaches to specific tasks such as planning, handoff between sessions, and self-directed learning.

Synthesized from **31 contributing transcripts** in NotebookLM notebook *WL: Anthropic & Agent Ecosystem*, clustered into the "going-skills-grill" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Skills are implemented as markdown files (such as skills.md, agents.md, or soul.md) that are read at the beginning of an interaction to provide context to the model, since AI models are static and know nothing about the user or task without context [13]
- The /grill-me skill family implements a questioning technique that relentlessly asks questions one at a time until shared understanding is reached, serving as a replacement for plan mode in agents [12, 18, 19]
- The /grill-with-docs skill is a successor to grill-me that incorporates documentation review, replacing plan mode with structured interviewing [18]
- The /handoff skill compresses the current session context into a markdown file that can be handed off to another session, saving to the user's temporary directory [10]
- The slasheach skill (slash teach) turns an AI coding agent into a personal tutor capable of teaching code, frameworks, or open-source models [16]
- Skills can be organized in repositories, with some publicly available repos accumulating significant community adoption [10, 11]
- The 'skill hell' problem emerges when developers have access to many freely available skills but lack guidance on how to distinguish good skills from bad ones [17]
- Effective skill usage requires the human user to possess planning abilities, understand scope, and know what level of fidelity is needed to answer questions—this aids rather than replaces the engineer [19]
- Research profiles in platforms like NotebookLM allow users to provide custom instructions up to 10,000 characters to steer model outputs through role-based guidance [15]
- When building skills for complex products, the documentation and definition process can require significant effort comparable to academic work [5]

## Verifiable values

| Name | Value |
|---|---|
| NotebookLM custom instruction limit | `10,000 characters` |

## Related concepts

- context-management — Context Management
- prompt-engineering — Prompt Engineering
- ai-agent-workflows — AI Agent Workflows
- retrieval-augmented-generation — Retrieval Augmented Generation

## Citations (from contributing transcripts)

- **Claim:** Skills are implemented as markdown files read at the beginning of an interaction
  - Source: Build Your First AI Web Researcher in Minutes (`b6632a79-5178-4c1d-b5a7-eadb249576bc`)
  - Context: we have things like skills.md file or agents.md file or soul.md these are all files that get read in at the beginning of uh some kind of interaction with a model to kind of give it some context
- **Claim:** The /grill-me skill relentlessly questions the user one at a time until shared understanding is reached
  - Source: grill-me + Codex: The Planning Workflow That Caught My Bug (`b40d64c4-927a-4c3a-b884-bdbaef8491e4`)
  - Context: First, it interviews you properly: a dozen questions, one at a time. No skipping ahead
- **Claim:** The /grill-with-docs skill is a successor to grill-me that incorporates documentation
  - Source: I Tried /grill-with-docs Skill: Massive Difference (`f21b8491-9d0d-4d64-ba84-969482bdaf04`)
  - Context: grill with dogs AI skill by Matt Pacock which is a successor to a very popular skill called Grill Me
- **Claim:** The /handoff skill compresses session context into a file for another session
  - Source: /handoff is my new favourite skill (`741b7513-349d-4fd1-86b6-8c0d7336b6cd`)
  - Context: this skill would take the context window of the current session and compress it down into a markdown file that could be handed off to another session
- **Claim:** The slasheach skill turns an AI agent into a personal tutor
  - Source: I Tried /teach and 10x'd My Ability To Learn (`cfddbcb7-2669-4270-a8e7-47a4a116f355`)
  - Context: What this slasheach skill does is it literally turns your claw code agent into a personal tutor that can teach you anything
- **Claim:** Skill hell is when developers have access to many skills but don't know how to distinguish good from bad
  - Source: Building Great Agent Skills: The Missing Manual (`e3518c73-0cd0-4bd3-b0c1-e77723023afe`)
  - Context: Skill hell is where you have all of these skills available freely available that you can download contribute to you can figure out on your own but you don't really know how t
- **Claim:** Using grill-me skills requires the user to have planning abilities and understand scope
  - Source: 9 Things People Get Wrong With My /grill-* skills (`f76d7206-bd9a-4026-ad20-4a43a15b4a6a`)
  - Context: the person answering the questions in other words you using the grill me skill need to be good at planning you need to understand things like scope
- **Claim:** NotebookLM supports custom instructions up to 10,000 characters
  - Source: How to be a NotebookLM Ninja: Five Simple Tips (`bfc178f0-9a66-4585-8e2c-f1102f1d6293`)
  - Context: buried in the chat configuration settings is a custom instruction box that now supports up to 10,000 characters
- **Claim:** Writing skills for complex products requires significant documentation effort
  - Source: Combine Skills and MCP to Close the Context Gap — Pedro Rodrigues, Supabase (`4f4afa6a-9553-4a53-a6d9-64575d5f7934`)
  - Context: I've never spent more time writing a single document since I've wrote my master thesis

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `7ef4d1e8-319f-4e27-a751-e777ddc2b723`
(cluster `going-skills-grill`). No claims are made
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

- NotebookLM notebook [WL: Anthropic & Agent Ecosystem](https://notebooklm.google.com/notebook/7ef4d1e8-319f-4e27-a751-e777ddc2b723)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
