---
title: "Vibe Prompt Template"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, vibe]
summary: >
  The KhazP vibe-coding prompt template is a structured approach for transforming high-level project concepts into detailed, actionable prompts for AI coding assistants, organized across multiple skill domains including research, PRD, technical design, and build phases.
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
      id: vibe-prompt-template
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
  - target: wiki/concepts/power-prompts.md
    type: related
  - target: wiki/concepts/artifact-first-memory.md
    type: related
  - target: wiki/concepts/multi-agent-orchestration.md
    type: related
---

# Vibe Prompt Template

## Decision context

**Definition:** The KhazP vibe-coding prompt template is a structured approach for transforming high-level project concepts into detailed, actionable prompts for AI coding assistants, organized across multiple skill domains including research, PRD, technical design, and build phases.

Synthesized from **7 contributing transcripts** in NotebookLM notebook *ext-Gemini CLI, Jules CLI, and Claude Code*, clustered into the "vibe-prompt-khazp" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The template repository is organized into four main parts: deep research, product requirements (PRD/MVP), technical design (MVP), and agent notes
- Planned March 2026 update (Agentic Era v2.0) shifts focus from chat-based prompt generation to Artifact-First Memory and Multi-Agent Orchestration
- Template directory contains modular components: AGENTS.md, MEMORY.md, REVIEW-CHECKLIST.md, and agent documentation templates
- Agent documentation templates cover product_requirements.md, project_brief.md, tech_stack.md, and testing.md
- The approach transforms unstructured ideas into structured prompts through two-stage power prompt methodology
- Skills are organized by domain: vibe-research, vibe-prd, vibe-techdesign, vibe-agents, vibe-workflow, and vibe-build
- Documentation includes support for Claude agent teams and cursor-cloud-agents configurations

## Verifiable values

| Name | Value |
|---|---|
| Repository size (chars) | `~225,000-240,000 per skill module` |
| Template modules | `6 skill domains (research, prd, techdesign, agents, workflow, build)` |
| Changelog version | `Unreleased - March 2026 (Agentic Era v2.0)` |

## Related concepts

- power-prompts — Power Prompts
- artifact-first-memory — Artifact-First Memory
- [[multi-agent-orchestration]] — Multi-Agent Orchestration
- vibe-coding — Vibe Coding

## Citations (from contributing transcripts)

- **Claim:** The repository shifts from chat-based prompt generation to Artifact-First Memory and Multi-Agent Orchestration
  - Source: KhazP-vibe-coding-prompt-template.md (`f3914139-260b-4be9-b098-1db9c8c39376`)
  - Context: This major update shifts the repository from "chat-based prompt generation" to **Artifact-First Memory** and **Multi-Agent Orchestration**
- **Claim:** The template supports transforming unstructured ideas into actionable prompts
  - Source: Power Prompts v.1 (`a79faf27-09fe-490e-8279-cf13323b483e`)
  - Context: Two powerful prompts to transform unstructured ideas into
- **Claim:** Template structure includes four main parts for project development
  - Source: KhazP-vibe-coding-prompt-template.md (`f3914139-260b-4be9-b098-1db9c8c39376`)
  - Context: part1-deepresearch.md, part2-prd-mvp.md, part3-tech-design-mvp.md, part4-notes-for-agent.md
- **Claim:** Agent documentation templates cover key development artifacts
  - Source: KhazP-vibe-coding-prompt-template.md (`f3914139-260b-4be9-b098-1db9c8c39376`)
  - Context: templates/agent_docs/ product_requirements.md, project_brief.md, tech_stack.md, testing.md

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
