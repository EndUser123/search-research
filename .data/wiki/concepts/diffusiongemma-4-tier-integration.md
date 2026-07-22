---
title: "DiffusionGemma integration: 4-tier model routing for optimal LLM usage"
created: 2026-07-21
source: session-2026-07-21 (/design synthesis from verified testing)
sources:
  - P:/.data/wiki/concepts/diffusiongemma-optimal-usage-dos-and-donts.md
  - P:/.data/wiki/concepts/compensating-for-weaker-models-ensemble-multi-pass.md
  - P:/.data/wiki/concepts/testing-methodology-both-outcomes-informative.md
  - P:/.data/wiki/concepts/skill-techniques-index.md
  - P:/.agents/scripts/models/dgemma_read.py
  - C:/Users/brsth/.grok/config.toml
tags: [diffusiongemma, model-routing, 4-tier, integration, optimal-usage, batch, enhanced]
host: grok
verification: verified_T1_T4_plus_batch_test_20260721
cognitive_load: 3
summary: "Verified integration design for DiffusionGemma across our workflow. 4-tier model routing: code scan → DiffusionGemma batch → DiffusionGemma enhanced/ccr-ornith → parent synthesis. All tiers verified with receipts this session."
---

# DiffusionGemma integration: 4-tier model routing

## The 4-tier architecture

```
Tier 0: Code breadth scan (Python regex, scan_techniques.py)
    ↓ identifies high-density subset
Tier 1: DiffusionGemma batch read (diffusiongemma_read.py --batch)
    ↓ summarizes 20-50 files per call in ~6.5s
Tier 2: DiffusionGemma enhanced (diffusiongemma_read.py --enhanced)
    OR ccr-ornith depth read (spawn_subagent)
    ↓ per-file analysis, 20/20 quality
Tier 3: Parent-inherited synthesis (Grok)
    ↓ judgment, cross-referencing, durable output
```

## Verified performance characteristics

| Tier | Tool | Speed | Quality | Cost | Verified |
|---|---|---|---|---|---|
| 0 | `scan_techniques.py` | 17s/968 skills | Mechanical indicators | Free | ✅ 2026-07-21 |
| 1 | `diffusiongemma_read.py --batch` | 6.5s/20 files | 1-sentence summaries, 20/20 correct | Free | ✅ 2026-07-21 |
| 2a | `diffusiongemma_read.py --enhanced` | 2.4s/file | 20/20 blind comparison | Free | ✅ T4 test |
| 2b | ccr-ornith via spawn_subagent | 46s/file | 20/20 with line citations | Free | ✅ T4 test |
| 3 | Parent-inherited (Grok) | 60-90s | Highest quality | Paid API | ✅ All session |

## What's built and working

| Component | Path | Status |
|---|---|---|
| `diffusiongemma_read.py` (single) | `P:/.data/wiki/scripts/` | ✅ |
| `diffusiongemma_read.py` (--enhanced) | same | ✅ Parallel fan-out + merge |
| `diffusiongemma_read.py` (--batch) | same | ✅ 20-50 files per call |
| `scan_techniques.py` | `P:/tmp/` | ✅ 968 skills in 17s |
| `index_skills.py` | `P:/.data/wiki/scripts/` | ✅ 954 stubs across 24 scopes |
| AGENTS.md model-tiering rules | `P:/AGENTS.md` | ✅ |
| tool-fallbacks.md | `~/.grok/tool-fallbacks.md` | ✅ All models tested |

## Usage boundary (when to use which tier)

| Task | Tier | Why |
|---|---|---|
| "What skills do we have?" | 0 + 1 | Scan all, batch-summarize high-density |
| "Summarize this one file" | 2a (--enhanced) | 2.4s, 20/20 quality |
| "Deep analysis with line citations" | 2b (ccr-ornith) | 46s, line-level detail |
| "Synthesize findings across files" | 3 (parent) | Judgment, cross-referencing |
| Bulk portfolio analysis (968 skills) | 0 → 1 → selective 2a | Code scan narrows to ~80 high-density, batch-summarize, enhanced-read the top 10 |
| Interactive question | 3 only | Speed matters; 7s TTFT on DiffusionGemma |

## What we explicitly DON'T do

- ❌ No PreToolUse hook for model routing (wrong layer)
- ❌ No spawn_subagent with DiffusionGemma (thinking mode incompatibility)
- ❌ No DiffusionGemma for synthesis/judgment (5-19 point quality gap on reasoning)
- ❌ No DiffusionGemma for tool-calling (framework incompatibility + lower Tool-Eval-Bench)
- ❌ No forcing any tier — the agent chooses based on AGENTS.md guidance

## Relationship to existing concepts

- [[diffusiongemma-optimal-usage-dos-and-donts]] — the full optimal-usage guide
- [[compensating-for-weaker-models-ensemble-multi-pass]] — the multi-perspective recipe
- [[testing-methodology-both-outcomes-informative]] — how we verified each tier
- [[skill-techniques-index]] T20 (two-phase analysis) — the meta-pattern
- [[skill-techniques-index]] T22 (model tiering) — this concept is the implementation

## Auto-related

- [[plan-then-execute-pattern]]
- [[operator-collaboration-style-and-leverage]]

