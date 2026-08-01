---
title: "Lint as Forward-Looking Research Source"
created: 2026-08-01
source: dream-2026-08-01
tags: [lint, wiki-maintenance, research-suggestions, forward-looking, karpathy]
summary: >
  Health checks and lint passes are typically backward-looking: "what's
  broken?" But lint also has access to signals that generate forward-looking
  research suggestions: contradictions, stale time-sensitive pages, evidence
  gaps, falsifier conditions, hub pages at risk. Making research suggestions
  a mandatory output of lint turns each maintenance pass into a source of
  actionable next work, not just a health report.
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
sources:
  - SCHEMA.md §10 Lint Phase 3 (implemented 2026-08-01)
  - https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f (Karpathy LLM Wiki gist)
relations:
  - target: wiki/concepts/proactive-ai-volunteering-mechanisms.md
    type: extends
  - target: wiki/concepts/scheduled-tasks-wiki-content-maintenance.md
    type: related
  - target: wiki/concepts/knowledge-capture-cant-afford-to-lose.md
    type: related
---

# Lint as Forward-Looking Research Source

## Decision context

**The problem:** Wiki lint passes produce health reports — broken links, stale pages, orphan concepts. These are backward-looking: "what went wrong?" But the lint process also scans signals that answer a different question: "what should we research next?" Without surfacing these signals as actionable suggestions, the lint pass leaves its most valuable output on the floor.

## Key findings

**Two independent sources converged on the same principle:**

1. **SCHEMA.md §10 Lint Phase 3 (implemented 2026-08-01):** Added a mandatory Phase 3 to the wiki lint operation that generates research suggestions from 8 signal sources: contradictions, stale time-sensitive pages, orphans, INFERENCE/UNKNOWN labels, EVIDENCE_GAP markers, shared-source clusters, falsifier-triggered concepts, and high-connectivity stale hub pages. Output written to `_state/research-suggestions.json` for `/todo` consumption. Receipt: commit `fca163a`.

2. **Karpathy LLM Wiki gist (ingested 2026-08-01):** "Periodically, ask the LLM to health-check the wiki. Look for: contradictions between pages, stale claims that newer sources have superseded, orphan pages with no inbound links, important concepts mentioned but lacking their own page, missing cross-references, data gaps that could be filled with a web search. The LLM is good at suggesting new questions to investigate and new sources to be for." Receipt: `P:/.data/wiki/sources/gist.github.com/000-karpathy-llm-wiki-gist.md`.

**The principle:** lint is not just maintenance — it's discovery. The same scan that finds broken links can find "this concept's falsifier may have fired" or "these three pages share a source but nobody synthesized a hub page." These are research opportunities, not health problems. Making them a mandatory output ensures they're surfaced every time the corpus is scanned, not just when someone happens to think of them.

## What this means for our workspace

The [[proactive-ai-volunteering-mechanisms]] concept covers proactive surfacing generally; this concept names the specific application to lint. The [[scheduled-tasks-wiki-content-maintenance]] pattern covers scheduling; lint-as-research-source reframes the OUTPUT of that scheduling from "health report" to "research queue." This also serves the [[knowledge-capture-cant-afford-to-lose]] principle: the lint pass is already scanning the corpus — extracting research suggestions from that scan costs nothing and captures opportunities that would otherwise be missed.

When `/todo` runs its Step 3 wiki scan, it should read `_state/research-suggestions.json` and surface the items alongside handoffs and unreviewed concepts.

**Signal sources (8):** contradictions between pages, stale time-sensitive pages (library docs >90d), orphan pages mentioning important concepts, `[INFERENCE]`/`[UNKNOWN]` labels needing upgrade, `EVIDENCE_GAP:` markers, shared-source clusters suggesting a missing hub page, concepts whose `## Falsifier` conditions may have triggered, and high-connectivity hub pages (≥8 inbound links) that are stale (>60d).

**Output format:** each suggestion has a topic, one-line reason, suggested skill route (`/www`, `/todo`, manual), and confidence level (high/medium/low based on signal strength). Written to `P:/.data/wiki/_state/research-suggestions.json` for programmatic consumption by `/todo`.

**Trade-off:** adding research suggestions to lint increases lint pass duration by ~30s (the LLM judgment phase for generating suggestions). This is negligible compared to the value of surfacing 3-5 actionable research items per maintenance pass that would otherwise require a separate manual discovery step.

**Routing:** suggestions are written to `P:/.data/wiki/_state/research-suggestions.json` with fields: topic, reason, suggested_skill, confidence. The `/todo` skill reads this file in its Step 3 wiki scan and surfaces items alongside open handoffs and unreviewed concepts. This creates a maintenance-to-research pipeline: every lint pass feeds the next `/todo` run with fresh research targets.

## Falsifier

If the research suggestions produced by lint Phase 3 are consistently acted on by the operator (promoted to /www research, /todo items, or direct investigation), the feature has positive ROI. If after 3 lint runs the suggestions are never acted on, either the signal quality is too low (the suggestions aren't actionable) or the routing to /todo is broken. Test by tracking suggestion-to-action conversion rate over the next 3 lint runs.

## Sources

- SCHEMA.md §10 Lint Phase 3, commit `fca163a` (2026-08-01).
- [Karpathy LLM Wiki gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — §Operations → Lint.

## Auto-related

- [[multi-model-ai-workflow-patterns]]
- [[claude-code-multi-agent-collaboration-patterns]]
- [[metabolic-health-optimization]]
- [[metabolic-health-and-visceral-fat-management]]
- [[claude-code-automation-capabilities]]

