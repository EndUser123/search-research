---
title: "Kimi K2.7 Code Mixture-of-Experts Architecture"
created: 2026-07-28
source: nlm-sync-2026-07-28
tags: [nlm-synced, reference, model]
summary: >
  Kimi K2.7 Code is an open-source Mixture of Experts model released by Moonshot AI that achieves improved reasoning efficiency through sparse activation, activating only a fraction of its one trillion total parameters per token.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 56999a7a-e52f-4e04-9335-342df85cdfde" ([INGESTED] - WL: AI Coding & Tooling, synced 2026-07-28)
  - "NotebookLM source 05e29d32-9f93-4a83-b996-25bcc13652b2" (Kimi K2.7 Code:  Open Source Model Beating Claude, 1 Trillion Params, 30% Fewer Tokens, synced 2026-07-28)
  - "NotebookLM source 10e0a4a0-f843-4882-b39f-415a9c70b45b" (VibeThinker-3B: This Small Open Source Model Just Matched Claude ai and GLM5 | vibethinker ai, synced 2026-07-28)
  - "NotebookLM source 15aa1da9-f985-42ac-af49-62645c10d0a9" (Use Kimi K2.7 Completely FREE  – Best AI Coding Setup 2026 | Claude Code Alternative, synced 2026-07-28)
  - "NotebookLM source 3dbefe2e-0833-4727-a463-a90f92c888f4" (Google DeepMind Has a Very Big Problem!, synced 2026-07-28)
  - "NotebookLM source 7cc84d27-c581-4d3c-bdfe-27e915700d0c" (Kimi K2.7 Code Just Changed AI Coding With Preserve thinking, synced 2026-07-28)
  - "NotebookLM source 92c975da-1ccb-4f14-a297-c54929527cf1" (I Tested NEW Kimi-K2.7-Code with 20 Prompts, synced 2026-07-28)
  - "NotebookLM source b94b5de0-f1dc-4068-8d48-fc9b57442732" (A 744B AI Model Runs On A Laptop (GLM-5.2 Via Colibri), synced 2026-07-28)
  - "NotebookLM source e11749de-f738-4547-bbb7-fe9e5dd77e2c" (I Tried Laguna S 2.1 So You Don't Have To..., synced 2026-07-28)
provenance:
  chain:
    - level: concept
      id: kimi-k27-code-mixture-of-experts-architecture
    - level: notebook
      id: 56999a7a-e52f-4e04-9335-342df85cdfde
      title: [INGESTED] - WL: AI Coding & Tooling
      url: https://notebooklm.google.com/notebook/56999a7a-e52f-4e04-9335-342df85cdfde
    - level: cluster
      id: 5
      name: model-code-kimi
relations:
  - target: wiki/concepts/mixture-of-experts-architecture.md
    type: related
  - target: wiki/concepts/sparse-activation.md
    type: related
  - target: wiki/concepts/kimi-k2.6.md
    type: related
---

# Kimi K2.7 Code Mixture-of-Experts Architecture

## Decision context

**Definition:** Kimi K2.7 Code is an open-source Mixture of Experts model released by Moonshot AI that achieves improved reasoning efficiency through sparse activation, activating only a fraction of its one trillion total parameters per token.

Synthesized from **8 contributing transcripts** in NotebookLM notebook *[INGESTED] - WL: AI Coding & Tooling*, clustered into the "model-code-kimi" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- Uses a sparse Mixture of Experts architecture with 384 total experts, selecting 8 per token plus one shared expert across 61 layers
- Activates approximately 32 billion parameters per token out of 1 trillion total parameters, reducing compute requirements while maintaining capability
- Post-training is specifically focused on coding tasks, leading to improved performance on longer coding operations
- Implements a preserved thinking approach that reduces redundant token generation during reasoning
- Achieves 30% fewer thinking tokens compared to K2.6 by eliminating unnecessary self-questioning patterns
- Runs efficiently despite the large parameter count due to the mixture-of-experts design pattern

## Verifiable values

| Name | Value |
|---|---|
| Total Parameters | `1 trillion` |
| Activated Parameters per Token | `32 billion` |
| Total Experts | `384` |
| Experts Selected per Token | `8 + 1 shared` |
| Thinking Token Reduction | `30% (vs K2.6)` |
| Model Layers | `61` |

## Related concepts

- [[mixture-of-experts-architecture]] — Mixture of Experts Architecture
- [[sparse-activation]] — Sparse Activation
- [[kimi-k2.6]] — Kimi K2.6
- [[thinking-token-efficiency]] — Thinking Token Efficiency
- [[open-source-coding-models]] — Open Source Coding Models

## Citations (from contributing transcripts)

- **Claim:** Kimi K2.7 Code uses a mixture of expert setup with 1 trillion total parameters and 32 billion activated per token
  - Source: Kimi K2.7 Code:  Open Source Model Beating Claude, 1 Trillion Params, 30% Fewer Tokens (`05e29d32-9f93-4a83-b996-25bcc13652b2`)
  - Context: One trillion total parameters sits on the model card which sounds insane until you realize only 32 billion of them activate per token
- **Claim:** The model holds 384 experts, picks eight per token plus one shared expert, and runs across 61 layers
  - Source: Kimi K2.7 Code:  Open Source Model Beating Claude, 1 Trillion Params, 30% Fewer Tokens (`05e29d32-9f93-4a83-b996-25bcc13652b2`)
  - Context: The model holds 384 experts picks eight per token plus one shared expert and runs across 61 layers
- **Claim:** Kimi K2.7 uses 30% fewer thinking tokens compared to K2.6
  - Source: Use Kimi K2.7 Completely FREE – Best AI Coding Setup 2026 | Claude Code Alternative
  - Context: the bigger upgrade from the older version is it reasoning efficiency kimik K 2.7 uses 30% fewer thinking tokens
- **Claim:** Post-training is focused on coding tasks with improved instruction on longer coding tasks
  - Source: I Tested NEW Kimi-K2.7-Code with 20 Prompts (`92c975da-1ccb-4f14-a297-c54929527cf1`)
  - Context: improved instruction on longer coding tasks and I will show you that specifically and also less overthinking and lower token usage
- **Claim:** The model implements preserved thinking for long horizon thinking processes
  - Source: Kimi K2.7 Code Just Changed AI Coding With Preserve thinking (`7cc84d27-c581-4d3c-bdfe-27e915700d0c`)
  - Context: they have used some of the new technologies and one of the interesting technologies is this preserved thinking so that is why here you see 30% fewer thinking tokens than the Kimik 2.6 and also they have improved a lot for the long horizon thinking process

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `56999a7a-e52f-4e04-9335-342df85cdfde`
(cluster `model-code-kimi`). No claims are made
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

- NotebookLM notebook [[INGESTED] - WL: AI Coding & Tooling](https://notebooklm.google.com/notebook/56999a7a-e52f-4e04-9335-342df85cdfde)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
