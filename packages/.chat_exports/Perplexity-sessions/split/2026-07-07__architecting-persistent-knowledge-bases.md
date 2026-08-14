---
title: "Architecting Persistent Knowledge Bases"
date: "2026-07-07"
mode: "ASI"
uuid: "4d8c0e5d-4094-4dae-a90f-26ef1253ad25"
entry_count: 3
---

## Human

[Deep Research](/computer/skills?skillId=deep-research) How to architect persistent knowledge base systems that survive after specialized AI model access ends

## Assistant

Waiting for deep research on persistent knowledge base architecture

## Assistant

Completed and saved the report.

- Report: `persistent_kb_research/persistent-kb-architecture-surviving-model-sunsets.pplx.md`
- Research manifest: `persistent_kb_research/research_artifacts_manifest.json`
- Supporting evidence: `persistent_kb_research/evidence_notes.jsonl`
- Source fetches/searches: `persistent_kb_research/fetched_sources.jsonl`, `persistent_kb_research/search_results.jsonl`

The report has also been shared as `persistent_kb_architecture_report`.

## Assistant

The deep research is complete. Here's the full report on architecting persistent knowledge base systems that survive when specialized AI model access ends.

## Bottom line

The durable part of an AI knowledge system is **not the model and not the vector index** — it's the canonical corpus, provenance, schemas, skills, prompts, tool contracts, evals, and reproducible build pipeline that can regenerate every derived artifact after a model disappears. Vendors are explicit that shutdown means inaccessible: OpenAI says deprecated models are unavailable after their shutdown date, Anthropic says requests to retired models fail, Google says a shut-down Gemini endpoint is "completely turned off," and Microsoft says retired Azure OpenAI deployments return `410 Gone` ([OpenAI](https://platform.openai.com/docs/deprecations/deprecation-history), [Anthropic](https://docs.anthropic.com/en/docs/about-claude/model-deprecations), [Gemini](https://ai.google.dev/gemini-api/docs/deprecations), [Microsoft](https://learn.microsoft.com/en-us/azure/foundry/openai/concepts/model-retirements)).

## Key findings

**The four-layer separation** — canonical content store, derived indexes, retrieval abstraction, generation/routing layer — lets you swap any single model or vector store without losing knowledge. The report includes a Mermaid reference architecture.

**The central rule:** the canonical store must be readable without the model, and every derived store must be disposable. If deleting the vector DB would destroy knowledge, the vector DB has been misclassified as a source of truth rather than a rebuildable cache. This mirrors RAG's original split between parametric model memory and external non-parametric index ([RAG paper](https://arxiv.org/abs/2005.11401)).

**Embeddings are the biggest trap.** Vector coordinates are not portable across embedding spaces. Azure explicitly states moving from `text-embedding-ada-002` to `text-embedding-3-large` requires generating new embeddings. The durable fix is fast **side-by-side re-embedding from a canonical chunk table** with stable chunk IDs derived from document structure (not token counts).

**The single best survivability hedge is a golden eval suite that travels with the KB.** It turns "does this still work?" into a reproducible measurement. Promptfoo, Inspect, Braintrust, Ragas, and DeepEval cover provider-agnostic and RAG-specific metrics.

**For your 12GB VRAM setup:** BGE/E5/Nomic local embeddings + sqlite-vec or LanceDB for local vectors + LM Studio/Ollama for Q4 7B-8B generation + cloud burst for larger consensus/debate runs. LM Studio exposes OpenAI- and Anthropic-compatible local REST endpoints, making the adapter pattern practical for local failover.

## What's in the report

- Real failure-mode taxonomy (deprecation, alias drift, preview cliffs, fine-tune loss, endpoint retirement, rate cliffs, region blocks) with documented examples
- Survivability matrix for each knowledge layer
- TypeScript Zod schemas for canonical documents, chunks, embedding records, and skill recipes
- Python re-embedding pipeline (deterministic, resumable, side-by-side)
- TypeScript model-agnostic retrieval interface with consensus retrieval
- Python RAG regression eval harness skeleton
- 5-phase migration/deprecation playbook as a checklist plus a decision tree
- A 15-category, 45-point **survivability scoring rubric** you can apply to your own KB
- A 5-week implementation roadmap starting with a deprecation drill

## Uncertainty flagged

Public postmortems of organizations losing production KB capability from model sunsets are scarce — the strongest evidence is vendor lifecycle docs and developer forum questions rather than formal incident reports. The report treats that absence explicitly as weak evidence, not proof.
