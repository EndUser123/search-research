---
title: "Model-web launcher: usage counts, quality scores, and model-strength tracking"
created: 2026-08-02
status: OPEN — design ready, implementation needed
assigned_to: grok
assigned_at: 2026-08-02T15:30
assigned_by: 019fba58
tags: [model-web, launcher, model-tracking, ensemble, cross-model, fleet-management]
---

# Model-web launcher: usage counts, quality scores, and model-strength tracking

## Goal

Update the `/model-web` launcher page (`~/.grok/skills/model-web/launcher.html`) to show per-model usage counts and a quality/"chess" score, so the operator can see at a glance which models are being used and how good they are. Also: branch out to underused models in ensemble runs instead of always defaulting to the same 5 (ChatGPT, Gemini, Claude, DeepSeek, Perplexity).

## Background

This session ran a `/design` review ensemble against 5 browser LLMs. The operator noticed:
1. **Same 5 models every time** — no rotation or exploration of underused models (Kimi, Qwen, HuggingChat, Grok, Le Chat, MiniMax, Multio, Poe, Z.ai Chat, Copilot)
2. **No tracking** — the launcher page shows model names and "Verified" badges but no usage counts or quality scores
3. **Relative strengths not captured** — when ChatGPT produces the best insight and DeepSeek is the most rigorous, that knowledge is lost after the session

The operator's directive: "You keep using the same models, we need to branch out more. We will eventually find the good combinations."

## Current state

**Launcher page** (`~/.grok/skills/model-web/launcher.html`):
- 2-column layout: "No Login Required" (5 sites) + "Login Required" (10 sites)
- Each site entry: name, note, "Verified" badge
- No usage tracking, no quality score, no per-model metadata beyond a short note

**Model benchmark skill** (`~/.grok/skills/model-benchmark/`):
- Has latency + quality scoring + cost tracking + telemetry infrastructure
- SQLite database at `~/.grok/state/model_benchmark.db`
- Could be the data source for the launcher's scores — but currently not connected to model-web

**Ensemble observations from this session:**

| Model | Role | Key strength | Notable weakness |
|-------|------|-------------|-----------------|
| ChatGPT | Insight generation | Highest density of novel, actionable artifacts (Design Intent Contract, Evidence Ledger, "Elegant Fiction" failure mode) | No citations; minimal-diff bias |
| DeepSeek | Rigor/citations | Cited architecture standards, Databricks guidance, NeurIPS papers; RAIDC framework | Dense; sometimes over-structured |
| Gemini | Systematic analysis | Best failure-mode taxonomy framing; deterministic schema gate proposal | Conservative; converges on known patterns |
| Claude | Provenance/audit | Sharpest on orphaned wiki decisions, persona version pinning, FPR tracking | Slow to generate; focused on governance |
| Perplexity | Research grounding | "Design Spine" pattern, Tourniquet cost model, outcome-driven framing | Shorter responses; less depth |

## What needs to happen

### 1. Launcher page enhancement

Add to each model entry:
- **Usage count** — how many times this model has been queried via `/model-web` (tracked in a JSON state file or the benchmark DB)
- **Quality score** — a 1-10 "chess score" rating the model's ensemble contribution quality. Seeded from this session's observations above. Updated by the orchestrator after each ensemble run.
- **Strength tag** — short label(s) for the model's relative strength (e.g., "Insight generation," "Citations/rigor," "Systematic analysis," "Provenance/audit," "Research grounding")
- **Last used** — date of last ensemble query

**State file:** `~/.grok/state/model-web/model-stats.json` — per-model stats that the launcher page reads on load.

### 2. Model rotation in ensemble runs

The `/model-web ensemble` command currently sends to ALL open tabs. The operator wants to **branch out** — systematically try models that haven't been used or have low usage counts. Two approaches:

**Option A: Suggested rotation** — the launcher page highlights underused models (e.g., glow effect on models with 0 uses or below-average quality scores that haven't been tried recently).

**Option B: Auto-rotation** — `/model-web ensemble` queries the stats file and suggests which models to open for this run based on: (1) diversity (rotate through model families), (2) usage recency (prefer less-recently-used), (3) task fit (match strength tags to the task type).

### 3. Strength tracking

After each ensemble run, the orchestrator:
1. Collects each model's response
2. Assesses quality (novelty, rigor, actionability, citations)
3. Updates `model-stats.json` with: usage count++, quality score (rolling average), last-used date, strength tags (add/confirm/refine)

This is lightweight — not a full benchmark run, just a quality signal from the orchestrator's reading of the responses.

## Files to modify

| File | Change |
|------|--------|
| `~/.grok/skills/model-web/launcher.html` | Add usage count + quality score + strength tag display per model entry; read from `model-stats.json` |
| `~/.grok/state/model-web/model-stats.json` | NEW — per-model stats (usage count, quality score, strength tags, last used) |
| `~/.grok/skills/model-web/SKILL.md` | Document: orchestrator updates stats after each ensemble run; rotation suggestion logic |

## Acceptance criteria

1. Launcher page shows usage count + quality score + strength tag for each model
2. Stats persist in `model-stats.json` and survive page reloads
3. After each `/model-web ensemble` run, the orchestrator updates stats automatically
4. At least 3 underused models (Kimi, Qwen, HuggingChat) have non-zero usage counts after the next 3 ensemble runs
5. Quality scores reflect real observed quality, not placeholder values

## Constraints

- Launcher reads `model-stats.json` via `fetch()` — the file must be served from the Chrome profile or loaded via a file:// path the launcher can access
- Quality scores are subjective (orchestrator-assessed) — label them as such, don't pretend they're benchmarks
- The chess-score metaphor: higher = better, range 800-3000 like real chess ratings. Or simpler: 1-10 scale. Operator preference TBD.

## What the operator wants

The operator's exact words: "We need to capture the relative strengths of each model for our searches, we need to update the landing page with the count each model has for usage, and it's 'chess' score. You keep using the same models, we need to branch out more. We will eventually find the good combinations."

The goal is exploration: systematically trying model combinations to find which pairs/groups produce the best complementarity for different task types (design review, code review, research synthesis, brainstorming).

## Seed data from this session

Use these as initial quality scores and strength tags:

```json
{
  "ChatGPT": {"uses": 1, "elo": 2400, "strengths": ["insight-generation", "novel-artifacts", "failure-mode-naming"], "last_used": "2026-08-02"},
  "DeepSeek": {"uses": 1, "elo": 2350, "strengths": ["citations", "rigor", "enterprise-frameworks"], "last_used": "2026-08-02"},
  "Gemini": {"uses": 1, "elo": 2200, "strengths": ["systematic-analysis", "deterministic-gates", "oscillation-detection"], "last_used": "2026-08-02"},
  "Claude": {"uses": 1, "elo": 2250, "strengths": ["provenance", "governance", "audit-trails", "fpr-tracking"], "last_used": "2026-08-02"},
  "Perplexity": {"uses": 1, "elo": 2150, "strengths": ["research-grounding", "cost-models", "outcome-framing"], "last_used": "2026-08-02"},
  "Kimi": {"uses": 0, "elo": 1200, "strengths": [], "last_used": null},
  "Qwen": {"uses": 0, "elo": 1200, "strengths": [], "last_used": null},
  "HuggingChat": {"uses": 0, "elo": 1200, "strengths": [], "last_used": null},
  "Grok": {"uses": 0, "elo": 1200, "strengths": [], "last_used": null},
  "Copilot": {"uses": 0, "elo": 1200, "strengths": [], "last_used": null},
  "Le Chat": {"uses": 0, "elo": 1200, "strengths": [], "last_used": null},
  "MiniMax": {"uses": 0, "elo": 1200, "strengths": [], "last_used": null},
  "Multio": {"uses": 0, "elo": 1200, "strengths": [], "last_used": null},
  "Z.ai Chat": {"uses": 0, "elo": 1200, "strengths": [], "last_used": null},
  "Poe": {"uses": 0, "elo": 1200, "strengths": [], "last_used": null}
}
```

ELO scale: 1200 = untested (provisional), 2000+ = strong contributor, 2400+ = elite. Untested models start at 1200 so the launcher visually distinguishes "never tried" from "tried and weak." Scores adjust after each ensemble run based on response quality.

## Revision: 2026-08-03 (session 019fba58)

### What was shipped this session

The launcher page was fully redesigned and shipped (7 commits `840233a` through `677431e`):

- 5-column family grouping (US Frontier / Chinese Frontier / European / Search-Augmented / Aggregators)
- ELO scores per model (seed data from 2 ensemble rounds)
- Clickable sub/free tier toggle (persists in localStorage)
- Model notes showing available chat models per provider
- ELO sorting (highest-to-lowest, ties shuffle on refresh)
- "new" tags removed (all tested)

### What remains

| Item | Status | Notes |
|------|--------|-------|
| Dynamic stats tracking (`P:/.data/model-web/model-stats.json`) | Not started | Source of truth for ELO/usage; launcher reads generated `.js` copy |
| Orchestrator auto-update after ensemble | Not started | Read each response, assess quality, update stats file |
| Model rotation suggestion | Not started | Highlight underused models based on usage count + ELO |
| Fusion page enhancements | Shipped separately | ELO display, reasoning level dropdowns, file input — multiple commits |

The launcher currently has hardcoded ELO scores. Dynamic tracking is the next step but requires the `model-stats.js` JSONP pattern described in the resolved decisions section.

1. **Chess score scale:** ELO-style 800-3000.
2. **Stats file location:** `P:/.data/model-web/model-stats.json` — consistent with workspace data root (`P:/.data/chrome-llm-profile/`, `P:/.data/harvest/`, `P:/.data/www-ledger/`).
3. **Integration with model-benchmark DB:** **Keep separate.** The data shapes are fundamentally different — benchmark DB tracks programmatic, quantitative, repeatable metrics (ms latency, token count, $ cost, same prompt → measure). Model-web tracks subjective, qualitative, one-shot assessments (each ensemble prompt is different, quality assessed by orchestrator reading responses). Merging forces one schema to accommodate the other's shape. Instead: model-web writes to `P:/.data/model-web/model-stats.json`; the model-benchmark dashboard can optionally read from both sources for a unified view if desired later.

### CORS solution for launcher loading stats

The launcher is `file:///C:/Users/brsth/.grok/skills/model-web/launcher.html`. `fetch()` from `file://` to `file:///P:/...` hits CORS in Chrome. Fix: the skill writes a sibling `model-stats.js` (JSONP-style: `window.MODEL_STATS = {...}`) to `~/.grok/skills/model-web/model-stats.js` before opening the launcher. The launcher loads it via `<script src="model-stats.js">` (relative path, same directory, no CORS issue). Source of truth stays at `P:/.data/model-web/model-stats.json`; the `.js` copy is generated from it.

## Launcher categorization (resolved 2026-08-02)

Replace the 2-column "No Login Required" / "Login Required" layout with **5 columns by model family / lab origin** — the training lineage that determines blind-spot correlation (FERZ Oct 2025: cross-family diversity is the highest-leverage decorrelation).

### Column 1: US Frontier Labs

| Model | Lab | Family | Access | Notes |
|-------|-----|--------|--------|-------|
| ChatGPT | OpenAI | GPT-5 | Plus (paid) | Best insight density in ensemble tests |
| Gemini | Google | Gemini 2.5 | Free + Paid | Systematic analysis strength |
| Claude | Anthropic | Claude 4 | Pro (paid) | Provenance, governance, audit trails |
| Grok | xAI | Grok 4 | Free (1) + Paid | Direct style, empirical rigor |

### Column 2: Chinese Frontier Labs

| Model | Lab | Family | Access | Notes |
|-------|-----|--------|--------|-------|
| DeepSeek | DeepSeek | V3 + R1 | Free | Best citation rigor in ensemble tests |
| Qwen Chat | Alibaba | Qwen 3 | Free | Sharpest critique — "the plan is probably wrong" |
| Kimi | Moonshot | K3 (2M ctx) | Free + Paid | Untested via web ensemble |
| Z.ai Chat | Zhipu | GLM-5 | Free | Untested via web ensemble |
| MiniMax | MiniMax | M3 | Free | Untested via web (tested via CLI extensively) |

### Column 3: European / Open-Source

| Model | Lab | Family | Access | Notes |
|-------|-----|--------|--------|-------|
| Le Chat | Mistral (FR) | Mistral Large | Free | Execution discipline, structured plans |
| HuggingChat | Hugging Face | Multi (open) | Free | Model picker: Llama, Mistral, Qwen |

### Column 4: Search-Augmented

| Model | Lab | Family | Access | Notes |
|-------|-----|--------|--------|-------|
| Perplexity | Perplexity | Multi-model + search | Free + Paid | Research grounding, source citations |

### Column 5: Aggregators (multi-model in one tab)

| Model | Lab | Family | Access | Notes |
|-------|-----|--------|--------|-------|
| Copilot | Microsoft | GPT | Free + Paid | Least naggy GPT access |
| Poe | Quora | Aggregator | Free + Paid | Thousands of models |
| Multio | Multio | Aggregator | Free | 100+ models |

### Why this grouping works for ensemble selection

1. **Pick one from each family group** → maximum blind-spot decorrelation. ChatGPT + DeepSeek + Qwen + Le Chat + Gemini covers US-GPT, Chinese-reasoning, Chinese-critique, European, and US-Google — five different training lineages.
2. **Within a group, models share more blind spots** — ChatGPT + Copilot both run GPT models; running both wastes an ensemble slot. The grouping makes this visible.
3. **Chinese labs are NOT a monolith** — DeepSeek, Qwen, Kimi, Z.ai, and MiniMax are five different companies with different training data, alignment approaches, and architectures. Grouping them as "Chinese" hides the diversity within.
4. **Subscription tier is a tag, not a grouping** — `paid` or `free` on each entry so you can see quota impact at a glance, but it doesn't drive the column structure.

### Updated seed data (ELO + family tagging, post-round-2 ensemble)

```json
{
  "ChatGPT":    {"uses": 2, "elo": 2420, "family": "us-frontier", "lab": "OpenAI", "access": "paid", "strengths": ["insight-generation", "novel-artifacts", "failure-mode-naming", "architecture-vision"], "last_used": "2026-08-02"},
  "Gemini":     {"uses": 2, "elo": 2230, "family": "us-frontier", "lab": "Google", "access": "free", "strengths": ["systematic-analysis", "deterministic-gates", "oscillation-detection", "decoupled-orchestration"], "last_used": "2026-08-02"},
  "Claude":     {"uses": 1, "elo": 2250, "family": "us-frontier", "lab": "Anthropic", "access": "paid", "strengths": ["provenance", "governance", "audit-trails", "fpr-tracking"], "last_used": "2026-08-02"},
  "Grok":       {"uses": 1, "elo": 2000, "family": "us-frontier", "lab": "xAI", "access": "free", "strengths": ["empirical-rigor", "measurement-design", "blind-scoring"], "last_used": "2026-08-02"},
  "DeepSeek":   {"uses": 1, "elo": 2350, "family": "cn-frontier", "lab": "DeepSeek", "access": "free", "strengths": ["citations", "rigor", "enterprise-frameworks"], "last_used": "2026-08-02"},
  "Qwen Chat":  {"uses": 1, "elo": 2100, "family": "cn-frontier", "lab": "Alibaba", "access": "free", "strengths": ["critical-thinking", "challenges-framing", "uncomfortable-truths"], "last_used": "2026-08-02"},
  "Kimi":       {"uses": 0, "elo": 1200, "family": "cn-frontier", "lab": "Moonshot", "access": "free", "strengths": [], "last_used": null},
  "Z.ai Chat":  {"uses": 0, "elo": 1200, "family": "cn-frontier", "lab": "Zhipu", "access": "free", "strengths": [], "last_used": null},
  "MiniMax":    {"uses": 0, "elo": 1200, "family": "cn-frontier", "lab": "MiniMax", "access": "free", "strengths": [], "last_used": null},
  "Le Chat":    {"uses": 1, "elo": 1950, "family": "eu-opensource", "lab": "Mistral", "access": "free", "strengths": ["execution-discipline", "structured-plans", "ship-or-kill"], "last_used": "2026-08-02"},
  "HuggingChat":{"uses": 0, "elo": 1200, "family": "eu-opensource", "lab": "HuggingFace", "access": "free", "strengths": [], "last_used": null},
  "Perplexity": {"uses": 1, "elo": 2150, "family": "search-augmented", "lab": "Perplexity", "access": "free", "strengths": ["research-grounding", "cost-models", "outcome-framing"], "last_used": "2026-08-02"},
  "Copilot":    {"uses": 0, "elo": 1200, "family": "aggregator", "lab": "Microsoft", "access": "free", "strengths": [], "last_used": null},
  "Poe":        {"uses": 0, "elo": 1200, "family": "aggregator", "lab": "Quora", "access": "free", "strengths": [], "last_used": null},
  "Multio":     {"uses": 0, "elo": 1200, "family": "aggregator", "lab": "Multio", "access": "free", "strengths": [], "last_used": null}
}
```
