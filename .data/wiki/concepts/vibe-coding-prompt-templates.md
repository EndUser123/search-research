---
title: "Vibe-Coding Prompt Templates"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, vibe]
summary: >
  A structured repository of AI interaction prompts designed to guide AI assistants through comprehensive software development workflows, with an emerging shift toward artifact-first memory and multi-agent orchestration approaches.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook f7806918-c135-4931-944d-09d94ccc458d" (ext-Gemini CLI, Jules CLI, and Claude Code, synced 2026-07-28)
  - "NotebookLM source 00701f57-7602-4cb1-80c3-493c2321d24a" (KhazP-vibe-coding-prompt-template.md, synced 2026-07-28)
  - "NotebookLM source 331e7d86-74db-484a-a2a2-498aadd3b8e2" (KhazP-vibe-coding-prompt-template.md, synced 2026-07-28)
  - "Power Prompts v.1" (https://www.smarason.is/en/blog/power-prompts-v1, transcript synced 2026-07-28)
  - "NotebookLM source c16cd1d6-564c-47e2-b7fa-987ca2c21359" (KhazP-vibe-coding-prompt-template.md, synced 2026-07-28)
  - "NotebookLM source cdd6afa7-bf99-4bc2-a3db-6d60c3cf8494" (KhazP-vibe-coding-prompt-template.md, synced 2026-07-28)
  - "NotebookLM source d11cb56a-2169-4fd6-8364-9928a452767e" (KhazP-vibe-coding-prompt-template.md, synced 2026-07-28)
  - "NotebookLM source f3914139-260b-4be9-b098-1db9c8c39376" (KhazP-vibe-coding-prompt-template.md, synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: vibe-coding-prompt-templates
    - level: notebook
      id: f7806918-c135-4931-944d-09d94ccc458d
      title: ext-Gemini CLI, Jules CLI, and Claude Code
      url: https://notebooklm.google.com/notebook/f7806918-c135-4931-944d-09d94ccc458d
    - level: cluster
      id: 4
      name: vibe-prompt-khazp
    - level: source_url
      url: https://www.smarason.is/en/blog/power-prompts-v1
      title: Power Prompts v.1
relations:
  - target: wiki/concepts/prompt-engineering.md
    type: related
  - target: wiki/concepts/multi-agent-systems.md
    type: related
  - target: wiki/concepts/artifact-first-memory.md
    type: related
---

# Vibe-Coding Prompt Templates

## Decision context

**Definition:** A structured repository of AI interaction prompts designed to guide AI assistants through comprehensive software development workflows, with an emerging shift toward artifact-first memory and multi-agent orchestration approaches.

Synthesized from **7 contributing transcripts** in NotebookLM notebook *ext-Gemini CLI, Jules CLI, and Claude Code*, clustered into the "vibe-prompt-khazp" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The repository contains multiple specialized skill paths covering distinct phases: vibe-research for initial exploration, vibe-prd for product requirements definition, vibe-techdesign for technical architecture, and vibe-build for implementation
- The skills directory includes shared templates for product requirements, project briefs, tech stack documentation, and testing specifications
- The repository structure follows a progression from deep research through PRD creation to technical design and implementation
- A planned March 2026 update (Agentic Era v2.0) aims to transition from chat-based prompt generation to artifact-first memory techniques
- The CHANGELOG documents a shift toward multi-agent orchestration as a core design principle
- Power Prompts v.1 describes techniques for transforming unstructured ideas into more structured AI interactions

## Verifiable values

| Name | Value |
|---|---|
| repository word count (vibe-techdesign) | `~59,629 words (~238,518 chars)` |
| repository word count (vibe-workflow) | `~56,271 words (~225,087 chars)` |
| repository word count (vibe-agents) | `~59,997 words (~239,991 chars)` |
| repository word count (vibe-research) | `~59,585 words (~238,341 chars)` |
| repository word count (vibe-prd) | `~59,559 words (~238,236 chars)` |
| repository word count (vibe-build) | `~59,440 words (~237,760 chars)` |
| planned update version | `Agentic Era v2.0` |
| planned update date | `March 2026` |

## Related concepts

- [[prompt-engineering]] — Prompt Engineering
- [[multi-agent-systems]] — Multi-Agent Systems
- [[artifact-first-memory]] — Artifact-First Memory
- [[vibe-coding]] — Vibe-Coding

## Citations (from contributing transcripts)

- **Claim:** The repository contains multiple specialized skill paths for different development phases
  - Source: KhazP-vibe-coding-prompt-template.md (`f3914139-260b-4be9-b098-1db9c8c39376`)
  - Context: Path: .claude/skills/vibe-techdesign | Path: skills/vibe-workflow | Path: .claude/skills/vibe-agents | Path: .claude/skills/vibe-research | Path: .claude/skills/vibe-prd | Path: .claude/skills/vibe-build
- **Claim:** The shared templates include product requirements, project briefs, tech stack, and testing documentation
  - Source: KhazP-vibe-coding-prompt-template.md (`f3914139-260b-4be9-b098-1db9c8c39376`)
  - Context: 📁 templates/agent_docs/ | 📄 product_requirements.md | 📄 project_brief.md | 📄 tech_stack.md | 📄 testing.md
- **Claim:** A March 2026 update (Agentic Era v2.0) plans to shift from chat-based prompt generation to artifact-first memory and multi-agent orchestration
  - Source: KhazP-vibe-coding-prompt-template.md (`f3914139-260b-4be9-b098-1db9c8c39376`)
  - Context: ## [Unreleased] - March 2026 — Agentic Era v2.0 | This major update shifts the repository from "chat-based prompt generation" to **Artifact-First Memory** and **Multi-Agent Orchestration**
- **Claim:** Power Prompts v.1 discusses transforming unstructured ideas into more structured AI interactions
  - Source: Power Prompts v.1 (`a79faf27-09fe-490e-8279-cf13323b483e`)
  - Context: Two powerful prompts to transform unstructured ideas int

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `f7806918-c135-4931-944d-09d94ccc458d`
(cluster `vibe-prompt-khazp`). No claims are made
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

- NotebookLM notebook [ext-Gemini CLI, Jules CLI, and Claude Code](https://notebooklm.google.com/notebook/f7806918-c135-4931-944d-09d94ccc458d)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
