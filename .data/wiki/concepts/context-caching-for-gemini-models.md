---
title: "Context Caching for Gemini Models"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, google]
summary: >
  Context caching is a technique on Vertex AI that allows users to store and reuse context between API calls with Gemini models, reducing redundant processing and enabling cost-effective interactions with fine-tuned models.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 84f90a47-9448-4652-82e1-c8dec495fc68" (Video Pipeline, synced 2026-07-27)
  - "Context caching overview | Generative AI on Vertex AI - Google Cloud Documentation" (https://docs.cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-overview, transcript synced 2026-07-27)
  - "Gemini 2.0 Flash | Generative AI on Vertex AI - Google Cloud Documentation" (https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-0-flash, transcript synced 2026-07-27)
  - "Agent Factory Recap: Deep Dive into Gemini CLI with Taylor Mullen | Google Cloud Blog" (https://cloud.google.com/blog/topics/developers-practitioners/agent-factory-recap-deep-dive-into-gemini-cli-with-taylor-mullen, transcript synced 2026-07-27)
  - "Gemini 2.5 Flash | Generative AI on Vertex AI | Google Cloud Documentation" (https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-5-flash, transcript synced 2026-07-27)
  - "Gemini 3 is available for enterprise | Google Cloud Blog" (https://cloud.google.com/blog/products/ai-machine-learning/gemini-3-is-available-for-enterprise, transcript synced 2026-07-27)
  - "Analyze data with the Gemini CLI | BigQuery - Google Cloud Documentation" (https://docs.cloud.google.com/bigquery/docs/develop-with-gemini-cli, transcript synced 2026-07-27)
  - "Context Caching for Fine-tuned Gemini Models | Generative AI on Vertex AI" (https://docs.cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-for-tuned-gemini, transcript synced 2026-07-27)
  - "Gemini 2.5 Flash | Generative AI on Vertex AI - Google Cloud Documentation" (https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-5-flash, transcript synced 2026-07-27)
  - "n8n Use Cases for Outbound: Automating Your Sales Prospecting Workflows - Databar.ai" (https://databar.ai/blog/article/n8n-use-cases-for-outbound-automating-your-sales-prospecting-workflows, transcript synced 2026-07-27)
  - "Video understanding | Generative AI on Vertex AI - Google Cloud Documentation" (https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/video-understanding, transcript synced 2026-07-27)
provenance:
  chain:
    - level: concept
      id: context-caching-for-gemini-models
    - level: notebook
      id: 84f90a47-9448-4652-82e1-c8dec495fc68
      title: Video Pipeline
      url: https://notebooklm.google.com/notebook/84f90a47-9448-4652-82e1-c8dec495fc68
    - level: cluster
      id: 5
      name: google-cloud-docs
    - level: source_url
      url: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-overview
      title: Context caching overview | Generative AI on Vertex AI - Google Cloud Documentation
    - level: source_url
      url: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-0-flash
      title: Gemini 2.0 Flash | Generative AI on Vertex AI - Google Cloud Documentation
    - level: source_url
      url: https://cloud.google.com/blog/topics/developers-practitioners/agent-factory-recap-deep-dive-into-gemini-cli-with-taylor-mullen
      title: Agent Factory Recap: Deep Dive into Gemini CLI with Taylor Mullen | Google Cloud Blog
    - level: source_url
      url: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-5-flash
      title: Gemini 2.5 Flash | Generative AI on Vertex AI | Google Cloud Documentation
    - level: source_url
      url: https://cloud.google.com/blog/products/ai-machine-learning/gemini-3-is-available-for-enterprise
      title: Gemini 3 is available for enterprise | Google Cloud Blog
    - level: source_url
      url: https://docs.cloud.google.com/bigquery/docs/develop-with-gemini-cli
      title: Analyze data with the Gemini CLI | BigQuery - Google Cloud Documentation
    - level: source_url
      url: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-for-tuned-gemini
      title: Context Caching for Fine-tuned Gemini Models | Generative AI on Vertex AI
    - level: source_url
      url: https://databar.ai/blog/article/n8n-use-cases-for-outbound-automating-your-sales-prospecting-workflows
      title: n8n Use Cases for Outbound: Automating Your Sales Prospecting Workflows - Databar.ai
    - level: source_url
      url: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/video-understanding
      title: Video understanding | Generative AI on Vertex AI - Google Cloud Documentation
relations:
  - target: wiki/concepts/gemini-cli.md
    type: related
  - target: wiki/concepts/gemini-2.5-flash.md
    type: related
  - target: wiki/concepts/vertex-ai-generative-ai.md
    type: related
---

# Context Caching for Gemini Models

## Decision context

**Definition:** Context caching is a technique on Vertex AI that allows users to store and reuse context between API calls with Gemini models, reducing redundant processing and enabling cost-effective interactions with fine-tuned models.

Synthesized from **10 contributing transcripts** in NotebookLM notebook *Video Pipeline*, clustered into the "google-cloud-docs" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Context caching enables storing background information, uploaded files, and system instructions that can be reused across multiple API calls
- The cached context remains available for the duration of a specified TTL (time-to-live) period
- This approach reduces token costs by avoiding reprocessing of repeated context across conversations or requests
- Context caching is supported for fine-tuned Gemini models in addition to base models

## Verifiable values

| Name | Value |
|---|---|
| Supported Models | `Fine-tuned Gemini models, Base Gemini models` |
| TTL Duration | `User-configurable time period` |

## Related concepts

- [[gemini-cli]] — Gemini CLI
- [[gemini-2.5-flash]] — Gemini 2.5 Flash
- [[vertex-ai-generative-ai]] — Vertex AI Generative AI

## Citations (from contributing transcripts)

- **Claim:** Context caching overview document exists for Generative AI on Vertex AI
  - Source: Context caching overview | Generative AI on Vertex AI - Google Cloud Documentation (`3535b6cf-dffc-44ad-8724-c10351575ee9`)
  - Context: Context caching overview | Generative AI on Vertex AI | Google Cloud Documentation
- **Claim:** Context caching is specifically documented for fine-tuned Gemini models
  - Source: Context Caching for Fine-tuned Gemini Models | Generative AI on Vertex AI (`c6942114-8569-4b2a-8bc3-814457c321c8`)
  - Context: Context Caching for Fine-tuned Gemini Models | Generative AI on Vertex AI | Google Cloud Documentation
- **Claim:** Gemini CLI is available for use with BigQuery data analysis
  - Source: Analyze data with the Gemini CLI | BigQuery - Google Cloud Documentation (`b9f49fa6-64a4-41d2-80d1-1ad3875bc35f`)
  - Context: Analyze data with the Gemini CLI | BigQuery | Google Cloud Documentation
- **Claim:** Context caching is part of the Vertex AI Generative AI documentation suite
  - Source: Context caching overview | Generative AI on Vertex AI - Google Cloud Documentation (`3535b6cf-dffc-44ad-8724-c10351575ee9`)
  - Context: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-overview

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `84f90a47-9448-4652-82e1-c8dec495fc68`
(cluster `google-cloud-docs`). No claims are made
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

- NotebookLM notebook [Video Pipeline](https://notebooklm.google.com/notebook/84f90a47-9448-4652-82e1-c8dec495fc68)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
