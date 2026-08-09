---
title: "Microclots vs Normal Clots"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, years]
summary: >
  Microclots are anomalous blood formations that differ fundamentally from normal clotting responses, persisting in the bloodstream rather than dissolving after serving their hemostatic purpose.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook b8a105cf-ada2-4343-88ce-184b1e7c9387" (WL: Health (ADHD/Sleep/Cancer), synced 2026-07-28)
  - "NotebookLM source 019e42e4-4bb5-4865-87ca-c89fc4995a52" (Real TRT Experience: 6 Years Later at 66 Years Old | My Current Dosage, synced 2026-07-28)
  - "NotebookLM source 3bc4384a-54b7-47bc-bfcd-8f192afe3510" (Scientists Cure Age Related Vision Loss, synced 2026-07-28)
  - "NotebookLM source b32689ac-f8da-4583-8e71-1f37386838f9" (Microdosing TRT - Truth vs Lies, synced 2026-07-28)
  - "NotebookLM source da8ae0d9-054a-4ad3-a2b8-f023dd4657a5" (They Injected a Human With “Youth Genes” — Here’s What Actually Happened, synced 2026-07-28)
  - "NotebookLM source dd836c83-7a12-4e5c-8aeb-1c1d4229ed35" (Why long COVID microclots are different from normal blood clots, synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: microclots-vs-normal-clots
    - level: notebook
      id: b8a105cf-ada2-4343-88ce-184b1e7c9387
      title: WL: Health (ADHD/Sleep/Cancer)
      url: https://notebooklm.google.com/notebook/b8a105cf-ada2-4343-88ce-184b1e7c9387
    - level: cluster
      id: 8
      name: years-clots-normal
relations:
  - target: wiki/concepts/fibrinogen.md
    type: related
  - target: wiki/concepts/thrombin.md
    type: related
  - target: wiki/concepts/coagulation.md
    type: related
---

# Microclots vs Normal Clots

## Decision context

**Definition:** Microclots are anomalous blood formations that differ fundamentally from normal clotting responses, persisting in the bloodstream rather than dissolving after serving their hemostatic purpose.

Synthesized from **5 contributing transcripts** in NotebookLM notebook *WL: Health (ADHD/Sleep/Cancer)*, clustered into the "years-clots-normal" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Normal clots form through a wound-induced process where thrombin cleaves fibrinogen, converting it from water-soluble to insoluble, creating small jelly pad-like structures approximately 100 micrometers in size that dissolve easily after their purpose is fulfilled
- Microclots are not easily dissolved afterwards and can persist because of how they form; they are resistant to destruction once formed
- Microclots are unusual because they are referred to by researchers as amastigotes, indicating an abnormal formation mechanism distinct from standard coagulation
- The source emphasizes that microclots are fundamentally different from normal clots in their persistence and resistance to breakdown

## Verifiable values

| Name | Value |
|---|---|
| Normal clot size | `approximately 100 micrometers` |

## Related concepts

- fibrinogen — Fibrinogen
- thrombin — Thrombin
- coagulation — Coagulation
- long-covid — Long COVID

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `b8a105cf-ada2-4343-88ce-184b1e7c9387`
(cluster `years-clots-normal`). No claims are made
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

- NotebookLM notebook [WL: Health (ADHD/Sleep/Cancer)](https://notebooklm.google.com/notebook/b8a105cf-ada2-4343-88ce-184b1e7c9387)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
