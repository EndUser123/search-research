---
title: "NVIDIA NeMo Guardrails"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, guardrails]
summary: >
  NVIDIA NeMo Guardrails is an open-source toolkit for adding programmable guardrails to LLM-based conversational systems, allowing developers to define behavioral constraints and content policies through configuration files and code.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 8138a528-f5c2-4ee4-b5a9-f3359f48f0dc" ([INGESTED] - Mastering Claude Skills, synced 2026-07-28)
  - "Security Best Practices - Model Context Protocol" (https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices, transcript synced 2026-07-28)
  - "Colang Guide — NVIDIA NeMo Guardrails Library Developer Guide" (https://docs.nvidia.com/nemo/guardrails/latest/configure-rails/colang/index.html, transcript synced 2026-07-28)
  - "GitHub - NVIDIA-NeMo/Guardrails: NeMo Guardrails is an open-source toolkit for easily adding programmable guardrails to LLM-based conversational systems." (https://github.com/NVIDIA-NeMo/Guardrails, transcript synced 2026-07-28)
  - "NeMo Guardrails 2026: NVIDIA's LLM Safety Toolkit - AppSec Santa" (https://appsecsanta.com/nemo-guardrails, transcript synced 2026-07-28)
  - "Guardrails Configuration — NVIDIA NeMo Guardrails Library Developer Guide" (https://docs.nvidia.com/nemo/guardrails/latest/configure-rails/yaml-schema/guardrails-configuration/index.html, transcript synced 2026-07-28)
  - "Python API — NVIDIA NeMo Guardrails" (https://docs.nvidia.com/nemo/guardrails/0.19.0/user-guides/python-api.html, transcript synced 2026-07-28)
  - "Guardrails Configuration — NVIDIA NeMo Guardrails" (https://docs.nvidia.com/nemo/guardrails/0.18.0/user-guides/configuration-guide/guardrails-configuration.html, transcript synced 2026-07-28)
  - "Working with Actions — NVIDIA NeMo Guardrails Library Developer Guide" (https://docs.nvidia.com/nemo/guardrails/latest/configure-rails/colang/colang-2/language-reference/working-with-actions.html, transcript synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: nvidia-nemo-guardrails
    - level: notebook
      id: 8138a528-f5c2-4ee4-b5a9-f3359f48f0dc
      title: [INGESTED] - Mastering Claude Skills
      url: https://notebooklm.google.com/notebook/8138a528-f5c2-4ee4-b5a9-f3359f48f0dc
    - level: cluster
      id: 6
      name: guardrails-nemo-nvidia
    - level: source_url
      url: https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices
      title: Security Best Practices - Model Context Protocol
    - level: source_url
      url: https://docs.nvidia.com/nemo/guardrails/latest/configure-rails/colang/index.html
      title: Colang Guide — NVIDIA NeMo Guardrails Library Developer Guide
    - level: source_url
      url: https://github.com/NVIDIA-NeMo/Guardrails
      title: GitHub - NVIDIA-NeMo/Guardrails: NeMo Guardrails is an open-source toolkit for easily adding programmable guardrails to LLM-based conversational systems.
    - level: source_url
      url: https://appsecsanta.com/nemo-guardrails
      title: NeMo Guardrails 2026: NVIDIA's LLM Safety Toolkit - AppSec Santa
    - level: source_url
      url: https://docs.nvidia.com/nemo/guardrails/latest/configure-rails/yaml-schema/guardrails-configuration/index.html
      title: Guardrails Configuration — NVIDIA NeMo Guardrails Library Developer Guide
    - level: source_url
      url: https://docs.nvidia.com/nemo/guardrails/0.19.0/user-guides/python-api.html
      title: Python API — NVIDIA NeMo Guardrails
    - level: source_url
      url: https://docs.nvidia.com/nemo/guardrails/0.18.0/user-guides/configuration-guide/guardrails-configuration.html
      title: Guardrails Configuration — NVIDIA NeMo Guardrails
    - level: source_url
      url: https://docs.nvidia.com/nemo/guardrails/latest/configure-rails/colang/colang-2/language-reference/working-with-actions.html
      title: Working with Actions — NVIDIA NeMo Guardrails Library Developer Guide
relations:
  - target: wiki/concepts/model-context-protocol.md
    type: related
  - target: wiki/concepts/colang-language.md
    type: related
  - target: wiki/concepts/llm-security.md
    type: related
---

# NVIDIA NeMo Guardrails

## Decision context

**Definition:** NVIDIA NeMo Guardrails is an open-source toolkit for adding programmable guardrails to LLM-based conversational systems, allowing developers to define behavioral constraints and content policies through configuration files and code.

Synthesized from **8 contributing transcripts** in NotebookLM notebook *[INGESTED] - Mastering Claude Skills*, clustered into the "guardrails-nemo-nvidia" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The toolkit is implemented as an open-source project hosted on GitHub under the NVIDIA-NeMo organization
- Colang serves as the primary configuration language for defining guardrail behaviors and flows
- YAML-based configuration files provide the structural definition for guardrail rules and settings
- A Python API is available for programmatic integration and control of guardrail execution
- The library integrates with Model Context Protocol to apply security best practices in LLM interactions
- Custom actions can be defined within the Colang 2.0 language specification for extended functionality

## Verifiable values

| Name | Value |
|---|---|
| GitHub repository stars | `6466` |
| GitHub repository forks | `733` |

## Related concepts

- model-context-protocol — Model Context Protocol
- colang-language — Colang Language
- llm-security — LLM Security
- yaml-configuration — YAML Configuration

## Citations (from contributing transcripts)

- **Claim:** NeMo Guardrails is an open-source toolkit for adding programmable guardrails to LLM-based conversational systems
  - Source: GitHub - NVIDIA-NeMo/Guardrails: NeMo Guardrails is an open-source toolkit for easily adding programmable guardrails to LLM-based conversational systems. (`64825b99-5eca-4724-87c2-faefa1b76b82`)
  - Context: NeMo Guardrails is an open-source toolkit for easily adding programmable guardrails to LLM-based conversational systems
- **Claim:** The toolkit uses Colang as its configuration language
  - Source: Colang Guide — NVIDIA NeMo Guardrails Library Developer Guide (`39925472-60d2-492b-a740-85f4a1f8d0b5`)
  - Context: Colang Guide — NVIDIA NeMo Guardrails Library Developer Guide
- **Claim:** YAML files are used for guardrail configuration
  - Source: Guardrails Configuration — NVIDIA NeMo Guardrails Library Developer Guide (`a56ba4e3-66e0-4991-9562-6330a041ad6d`)
  - Context: Configuring YAML File
- **Claim:** A Python API exists for the guardrails library
  - Source: Python API — NVIDIA NeMo Guardrails (`bce65027-96db-4d7e-aa28-a3184e62277a`)
  - Context: Python API — NVIDIA NeMo Guardrails
- **Claim:** The library supports Model Context Protocol integration for security
  - Source: Security Best Practices - Model Context Protocol (`1be0d712-b2d4-4be5-bc9c-13128f30d94b`)
  - Context: Security Best Practices - Model Context Protocol
- **Claim:** Custom actions can be defined using Colang 2.0
  - Source: Working with Actions — NVIDIA NeMo Guardrails Library Developer Guide (`e5dc9350-c9ff-4f8c-a5d8-6b9f53364f0b`)
  - Context: Working with Actions — NVIDIA NeMo Guardrails Library Developer Guide

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `8138a528-f5c2-4ee4-b5a9-f3359f48f0dc`
(cluster `guardrails-nemo-nvidia`). No claims are made
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
