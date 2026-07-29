---
title: "Kimi K2.7 Code MoE Architecture"
created: 2026-07-27
source: nlm-sync-2026-07-27
tags: [nlm-synced, reference, model]
summary: >
  Kimi K2.7 Code implements a sparse Mixture of Experts architecture that achieves computational efficiency through selective expert activation while maintaining high model capacity, enabling the model to perform coding tasks with significantly reduced token consumption compared to its predecessors.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 56999a7a-e52f-4e04-9335-342df85cdfde" (WL: AI Coding & Tooling, synced 2026-07-27)
  - "NotebookLM source 05e29d32-9f93-4a83-b996-25bcc13652b2" (Kimi K2.7 Code:  Open Source Model Beating Claude, 1 Trillion Params, 30% Fewer Tokens, synced 2026-07-27)
  - "NotebookLM source 10e0a4a0-f843-4882-b39f-415a9c70b45b" (VibeThinker-3B: This Small Open Source Model Just Matched Claude ai and GLM5 | vibethinker ai, synced 2026-07-27)
  - "NotebookLM source 15aa1da9-f985-42ac-af49-62645c10d0a9" (Use Kimi K2.7 Completely FREE  – Best AI Coding Setup 2026 | Claude Code Alternative, synced 2026-07-27)
  - "NotebookLM source 3dbefe2e-0833-4727-a463-a90f92c888f4" (Google DeepMind Has a Very Big Problem!, synced 2026-07-27)
  - "NotebookLM source 7cc84d27-c581-4d3c-bdfe-27e915700d0c" (Kimi K2.7 Code Just Changed AI Coding With Preserve thinking, synced 2026-07-27)
  - "NotebookLM source 92c975da-1ccb-4f14-a297-c54929527cf1" (I Tested NEW Kimi-K2.7-Code with 20 Prompts, synced 2026-07-27)
  - "NotebookLM source b94b5de0-f1dc-4068-8d48-fc9b57442732" (A 744B AI Model Runs On A Laptop (GLM-5.2 Via Colibri), synced 2026-07-27)
  - "NotebookLM source e11749de-f738-4547-bbb7-fe9e5dd77e2c" (I Tried Laguna S 2.1 So You Don't Have To..., synced 2026-07-27)
provenance:
  chain:
    - level: concept
      id: kimi-k27-code-moe-architecture
    - level: notebook
      id: 56999a7a-e52f-4e04-9335-342df85cdfde
      title: WL: AI Coding & Tooling
      url: https://notebooklm.google.com/notebook/56999a7a-e52f-4e04-9335-342df85cdfde
    - level: cluster
      id: 5
      name: model-code-kimi
relations:
  - target: wiki/concepts/mixture-of-experts-architecture.md
    type: related
  - target: wiki/concepts/sparse-activation-patterns.md
    type: related
  - target: wiki/concepts/kimi-k2.6-model.md
    type: related
---

# Kimi K2.7 Code MoE Architecture

## Decision context

**Definition:** Kimi K2.7 Code implements a sparse Mixture of Experts architecture that achieves computational efficiency through selective expert activation while maintaining high model capacity, enabling the model to perform coding tasks with significantly reduced token consumption compared to its predecessors.

Synthesized from **8 contributing transcripts** in NotebookLM notebook *WL: AI Coding & Tooling*, clustered into the "model-code-kimi" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The model utilizes a sparse MoE design where only 32 billion of the total 1 trillion parameters activate per token during inference, reducing computational cost while preserving model capability
- The architecture comprises 384 total experts, with each token routed to 8 specialized experts plus 1 shared expert across 61 model layers
- The model achieves 30% fewer thinking tokens compared to Kimi K2.6, indicating improved reasoning efficiency and reduced overthinking on coding tasks
- The model was released under a modified MIT license on Hugging Face by Moonshot AI on June 12, positioning it as an open-source coding model
- Post-training emphasis on coding tasks differentiates K2.7 from earlier K2.5 and K2.6 iterations that used the same base architecture
- The preserved thinking technique contributes to improved long-horizon thinking processes while maintaining lower token overhead
- Comparison benchmarks against Claude and other coding models show competitive performance on code generation and reasoning tasks

## Verifiable values

| Name | Value |
|---|---|
| Total Parameters | `1 trillion` |
| Active Parameters per Token | `32 billion` |
| Number of Experts | `384` |
| Experts Activated per Token | `8 + 1 shared` |
| Model Layers | `61` |
| Thinking Token Reduction | `30% compared to K2.6` |
| License Type | `modified MIT` |

## Related concepts

- [[mixture-of-experts-architecture]] — Mixture of Experts Architecture
- [[sparse-activation-patterns]] — Sparse Activation Patterns
- [[kimi-k2.6-model]] — Kimi K2.6 Model
- [[token-efficiency-optimization]] — Token Efficiency Optimization
- [[coding-model-benchmarks]] — Coding Model Benchmarks

## Citations (from contributing transcripts)

- **Claim:** The model has 1 trillion total parameters but only 32 billion activate per token
  - Source: Kimi K2.7 Code: Open Source Model Beating Claude, 1 Trillion Params, 30% Fewer Tokens
  - Context: One trillion total parameters sits on the model card which sounds insane until you realize only 32 billion of them activate per token
- **Claim:** The architecture uses 384 experts with 8 per token plus 1 shared expert across 61 layers
  - Source: Kimi K2.7 Code: Open Source Model Beating Claude, 1 Trillion Params, 30% Fewer Tokens
  - Context: The model holds 384 experts picks eight per token plus one shared expert and runs across 61 layers
- **Claim:** The model achieves 30% fewer thinking tokens compared to K2.6
  - Source: Kimi K2.7 Code: Open Source Model Beating Claude, 1 Trillion Params, 30% Fewer Tokens
  - Context: 30% fewer thinking tokens compared to K2.6 is the headline moonshot is pushing
- **Claim:** The model uses a preserved thinking technique to improve long-horizon thinking while reducing tokens
  - Source: Kimi K2.7 Code Just Changed AI Coding With Preserve thinking (`7cc84d27-c581-4d3c-bdfe-27e915700d0c`)
  - Context: they have used some of the new technologies and one of the interesting technologies is this preserved thinking so that is why here you see 30% fewer thinking tokens than the Kimik 2.6
- **Claim:** The model demonstrates less overthinking and lower token usage compared to K2.6
  - Source: I Tested NEW Kimi-K2.7-Code with 20 Prompts (`92c975da-1ccb-4f14-a297-c54929527cf1`)
  - Context: improved instruction on longer coding tasks and I will show you that specifically and also less overthinking and lower token usage
- **Claim:** The model was released on Hugging Face under a modified MIT license
  - Source: Kimi K2.7 Code: Open Source Model Beating Claude, 1 Trillion Params, 30% Fewer Tokens
  - Context: The Beijing team published this model on Hugging Face under a modified MIT license
- **Claim:** The model achieves 30% fewer thinking tokens compared to the K2.6 version
  - Source: Use Kimi K2.7 Completely FREE – Best AI Coding Setup 2026
  - Context: the bigger upgrade from the older version is it reasoning efficiency kimik K 2.7 uses 30% fewer thinking tokens

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

- NotebookLM notebook [WL: AI Coding & Tooling](https://notebooklm.google.com/notebook/56999a7a-e52f-4e04-9335-342df85cdfde)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
