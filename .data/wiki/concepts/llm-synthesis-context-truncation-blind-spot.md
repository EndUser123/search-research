---
title: "LLM Synthesis Context Truncation Blind Spot"
created: 2026-08-01
source: session-20260801
tags: [incident, pipeline-bug, wiki-yt, knowledge-loss, truncation, map-reduce]
summary: >
  The wiki-yt synthesis pipeline (synthesize_subtopics.py) truncated each
  transcript to 1,200 characters before feeding it to the LLM, while average
  transcripts are 31KB. This meant the synthesis LLM saw only ~3.8% of each
  transcript, systematically capturing video introductions and missing
  substantive mid-transcript content. Fixed by defaulting to full text with
  automatic map-reduce fallback when context exceeds a 300K-char budget.
agent: grok
host: grok
cognitive_load: 2
verification: observed-verified
sources:
  - https://arxiv.org/abs/2307.03172 (Liu et al., 2023 — "Lost in the Middle")
  - https://bestllmfor.com/best/summarization-long-docs/ (BestLLMFor, 2026)
  - https://galileo.ai/blog/llm-summarization-strategies (Galileo, 2026)
relations:
  - target: wiki/concepts/llm-concept-canonicalization-technique.md
    type: related
  - target: wiki/concepts/llm-wiki-knowledge-pattern.md
    type: extends
  - target: wiki/concepts/compensating-for-weaker-models-ensemble-multi-pass.md
    type: related
  - target: wiki/concepts/knowledge-capture-cant-afford-to-lose.md
    type: extends
---

# LLM Synthesis Context Truncation Blind Spot

## Decision context

**The problem:** While evaluating a YouTube video (Cole Medin's OKF knowledge base tutorial), I discovered that the wiki-yt synthesis pipeline had silently dropped the video's most valuable content — a canonicalization technique (now captured as [[llm-concept-canonicalization-technique]]) described at 58% through the transcript. Investigation revealed the root cause was not in the transcript or the NotebookLM export, but in `synthesize_subtopics.py:build_context()`, which truncated each transcript to its first 1,200 characters before feeding it to the synthesis LLM.

The canonicalization content sat at character 9,903 of a 16,973-char transcript. The LLM literally never saw it. This was not a one-off — it was systematic across all 7,565 transcripts in the vault.

## The bug

**File:** `P:/.agents/skills/wiki-yt/scripts/synthesize_subtopics.py`
**Function:** `build_context()` (line 68 in the original)
**Code:** `body = m["text"][:per_member_chars]` where `per_member_chars` defaulted to `1200`

**Impact measured from the vault:**

| Metric | Value |
|---|---|
| Transcript count | 7,565 |
| Average transcript size | 31 KB |
| Median transcript size | 15 KB |
| P90 transcript size | 48 KB |
| Max transcript size | 3.2 MB |
| **% of average transcript visible to LLM** | **3.8%** |
| **% of max transcript visible to LLM** | **0.04%** |

The 1,200-char default was ~250x too conservative given the backends' actual context windows:

| Backend | Context window | Effective safe zone | What 1,200 chars used |
|---|---|---|---|
| MiniMax M2 (mmx) | 205K tokens (~800K chars) | ~80K tokens (~320K chars) | 0.15% |
| DiffusionGemma | 256K tokens (~1M chars) | ~80K tokens (~320K chars) | 0.12% |

## Research findings

Three parallel research agents investigated best practices for multi-document LLM synthesis:

1. **Map-reduce is the canonical fix.** When documents exceed context windows, the two-tier pattern (per-document pre-summary, then cross-document synthesis) is recommended by LangChain, Galileo (2026), and arXiv 2410.09342. Every source flags "chunk-boundary content loss" as the primary failure mode.

2. **"Lost in the middle" sets the real budget.** Liu et al. 2023 showed a U-shaped retrieval curve; BestLLMFor 2026 confirmed KV-cache degradation past 80K tokens even on 200K+ context models. Both backends degrade 40-80% on multi-hop retrieval past ~80K tokens (~320K chars).

3. **Video transcripts have a content-density curve.** Educational videos follow "intro then demo then deep-dive then conclusion." The highest-value content (techniques, workflows, trade-offs) clusters in the middle — exactly where truncation hits hardest. This is consistent with the [[llm-wiki-knowledge-pattern]] where raw sources must be fully processed to extract structural knowledge.

## The fix (implemented)

Three-tier context strategy in `synthesize_subtopics.py`:

1. **Default (`per_member_chars=0`):** Pass FULL transcripts. With average transcripts at 31KB and clusters of 3-8 members, total context is 93-248KB — within the 300K-char safe zone.
2. **Map-reduce fallback:** When total context exceeds 300K chars (configurable via `--context-budget`), pre-summarize each transcript individually using a dedicated extraction prompt, then synthesize across the summaries.
3. **Legacy mode (`--per-member-chars=N`):** Still available for explicit truncation if needed.

New CLI args: `--per-member-chars 0` (default, full text), `--context-budget 300000` (map-reduce threshold).

**Pre-summary prompt** (`PRE_SUMMARY_PROMPT`) extracts: definitions, operational details, techniques/methods/patterns, named entities, claims with evidence, comparisons/trade-offs, surprising findings, and canonicalization signals. This is a content-type filter, not a positional truncation — it captures what matters regardless of where it appears in the transcript.

## What this means for our workspace

**Immediate:** all future wiki-yt syncs will see full transcript content. The map-reduce fallback ensures even 3MB outlier transcripts are processed without silent truncation.

**Retroactive:** existing wiki concepts synced via the pipeline (7,565 transcripts across ~100+ concept pages) were generated from truncated input. Concepts that primarily cited "video introductions" may be missing deeper technical content. A re-sync of high-value notebooks would recover lost signal, but this is a cost/benefit decision for the operator.

**The broader lesson:** The [[knowledge-capture-cant-afford-to-lose]] principle applies to pipeline defaults. A conservative default that silently drops 96% of input is worse than no pipeline at all — it creates the illusion of coverage while systematically missing exactly the content worth capturing. The map-reduce fallback addresses the [[compensating-for-weaker-models-ensemble-multi-pass]] concern: even when context budget is exceeded, the two-tier approach (individual extraction, then cross-source synthesis) preserves signal that flat truncation destroys. The fix is not just changing a number; it is the principle that **pipeline defaults must be validated against actual data distributions, not guessed.**

## Falsifier

If A/B testing (full-text vs. 1200-char truncation on the same set of transcripts) produces concept pages of equivalent quality — same claims extracted, same entities identified, same citations — then the truncation was not causing real signal loss and this fix was unnecessary overhead. Test: re-sync one notebook with the old default and one with the new, diff the output concepts.

## Sources

- [Lost in the Middle (Liu et al., 2023)](https://arxiv.org/abs/2307.03172) — U-shaped retrieval curve; positional degradation in long contexts
- [BestLLMFor (2026)](https://bestllmfor.com/best/summarization-long-docs/) — KV-cache degradation past 80K tokens
- [Galileo (2026)](https://galileo.ai/blog/llm-summarization-strategies) — overlapping chunks + map-reduce best practices
- [arXiv 2410.09342](https://arxiv.org/html/2410.09342v1) — LLM x MapReduce framework formalization
- [LangChain map_reduce docs](https://python.langchain.com/docs/versions/migrating_chains/map_reduce_chain/) — recursive collapsing for arbitrarily long inputs
- Commit: `e61fcd3` — the fix implementation

## Auto-related

- [[skill-graph]]
- [[blind-spot-detection-methods]]
- [[skill-catalog]]
- [[wiki-improvement-opportunities-practitioner-evidence]]
- [[context-management-in-claude-code]]

