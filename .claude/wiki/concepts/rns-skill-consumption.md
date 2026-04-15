---
title: "RNS: Format Agnostic Consumption"
created: 2026-04-15
tags: [rns, pre-mortem, format, workflow]
summary: "RNS skill transforms any input into selectable RNS format — structured or unstructured. Producers should output plain content; RNS handles transformation."
---

# RNS: Format Agnostic Consumption

## The Insight

RNS (Recommended Next Steps) is designed to **consume anything** — structured critiques with severity tags, GTO v2 format, or plain prose. The transformation happens in RNS, not in the producer.

**Wrong approach**: Producer formats its output to "look like RNS" before passing to RNS.
**Right approach**: Producer outputs plain structured content (7 sections, severity tags). RNS transforms to selectable action items.

## Why This Matters

When `/pre-mortem` was outputting a "GTO v2 style" in Phase 3, it was:
1. Adding formatting overhead in the wrong place
2. Potentially getting the format wrong anyway (inconsistent terminator, double-heading)
3. Treating RNS as a format specifier rather than a transformation step

## Lesson: Separation of Concerns

| Layer | Responsibility |
|-------|----------------|
| **Producer** (pre-mortem) | Output 7-section critique with severity-tagged findings |
| **Transformer** (RNS) | Consume any format, produce selectable RNS action items |
| **Consumer** (user) | Select items, issue "0 — Do ALL" directive |

## Related

- [[pre-mortem]] — Adaptive adversarial critique skill
- [[gto-v2]] — GTO v2 recommended next steps format
