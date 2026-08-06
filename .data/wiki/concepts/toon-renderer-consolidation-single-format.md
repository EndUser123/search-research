---
title: Toon renderer consolidation — single format for /todo
slug: toon-renderer-consolidation-single-format
last_verified: 2026-08-06
verified_on_host: grok
host_applicability: grok
---

# Toon renderer consolidation — single format for /todo

## Decision

The `/todo` skill uses a single renderer (`format_toon_rns`) for all output. The hierarchical (`render_actions`) and v2 (`render_actions_v2`) renderers were removed (851→88 lines, -902 net) after the operator confirmed the toon format was the keeper.

## Rationale

Three render paths existed but only one was used. The toon format produces:

```
## NOW

1. <text> [source]

2. <text> [source]

## NEXT
...

---
* N item(s) already have handoffs — ready for cold-start sessions.

0. Do all N actionable items (NOW + NEXT)
```

The hierarchical renderer (DO NOW/FIX/CAPTURE/MAINTAIN/BACKLOG with priority tags, action subtypes, dependency annotations) added visual complexity without improving the ADHD-friendly "what should I do?" question. The v2 renderer added per-section footers the operator found confusing.

## Key insight from /tp critique

The initial recommendation was to wire the LLM evaluation gate into the v2 path. A `/tp` critique (REVISE verdict, `zen-deepseek-v4-flash-free`) correctly identified this was wrong:

1. The v2 path's determinism was a **designed contract**, not a defect
2. The 8-question evaluation filter would run in a context vacuum (no transcript, no session history)
3. LLM evaluation would make v2 = toon, collapsing the two-path design

The correct fix was **mechanical dedup at the scanner layer** (`_normalize_ref` + `_dedup_scan_items` in `scan_functions.py`), not LLM judgment in the renderer. This is an instance of [[mechanical-as-input-not-mechanical-as-frame]]: the scanner should emit clean data; the renderer should format it; the LLM should evaluate it. Each layer has one job.

## Architecture after consolidation

```
scan_all() → post_scan_filter() → sort by severity → _dedup_scan_items()
                                                           ↓
                                              LLM evaluates (8 questions)
                                                           ↓
                                              format_toon_rns() → output
```

One scanner path, one dedup pass, one renderer. The LLM evaluation gate runs between scan output and rendering — it's the LLM's judgment, not code.
