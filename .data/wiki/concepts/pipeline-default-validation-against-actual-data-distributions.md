---
title: "Pipeline Default Validation Against Actual Data Distributions"
created: 2026-08-01
source: dream-2026-08-01
tags: [pipeline, defaults, validation, data-distribution, truncation, signal-loss]
summary: >
  Pipeline scripts ship with conservative defaults (truncation limits, batch
  sizes, timeouts) guessed at authoring time rather than validated against
  actual data. The defaults are typically 100-1000x too conservative relative
  to available resources, silently destroying signal at scale. The pipeline
  runs successfully, produces output, but the output is generated from a
  fraction of the input data.
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
sources:
  - session-019fbdfb (2026-08-01, wiki-yt 1200-char truncation bug)
  - session-019f9aff (2026-07-26, qmd staleness E7)
relations:
  - target: wiki/concepts/asserting-runtime-behavior-from-memory-not-testing.md
    type: related
  - target: wiki/concepts/verification-state-tracking-content-identity-vs-temporal-proxies.md
    type: related
  - target: wiki/concepts/llm-synthesis-context-truncation-blind-spot.md
    type: extends
---

# Pipeline Default Validation Against Actual Data Distributions

## Decision context

**The problem:** Pipeline scripts that transform, summarize, or synthesize data ship with default parameters chosen at authoring time. These defaults (truncation limits, batch sizes, timeout values, chunk counts) are conservative guesses intended to prevent resource exhaustion. But without validation against the actual data the pipeline will process, the defaults can be orders of magnitude too conservative — silently destroying signal while the pipeline reports success.

## Key findings

**The failure mode is invisible.** The pipeline runs, produces output, and reports no errors. The only way to detect the signal loss is to compare what the pipeline saw vs. what was available — which nobody does unless they notice a specific missing result.

**Two independent instances:**

1. **wiki-yt truncation bug (2026-08-01):** `synthesize_subtopics.py` defaulted to `per_member_chars=1200`, passing only 0.15% of each transcript to the LLM synthesis. The canonicalization technique from Cole Medin's video sat at char 9,903 of 16,973 — invisible. 7,565 transcripts were processed with 3.8% of content visible. The default was 250x too conservative for the 205K-token MiniMax context window. Fixed: default to full text + map-reduce fallback. Receipt: commit `e61fcd3`.

2. **qmd index staleness (2026-07-26):** The qmd semantic index was 83/221 docs stale. Search "ran successfully" but returned degraded results. The staleness threshold (mtime-based) didn't account for bulk-sync events that invalidated large swaths of the index simultaneously. Receipt: AAR episode E7.

**The pattern:** defaults are set for safety, but safety without measurement is guessing. The right approach: measure the actual data distribution (average size, P90, max), measure the available resources (context window, memory), and set defaults to use ~80% of the safe zone.

## What this means for our workspace

Every pipeline script with a size/count/timeout default should be audited:
- What data distribution does it process? (measure average, P90, max)
- What resource budget is available? (context window, memory, disk)
- Is the default using <10% of the safe zone? If so, it's likely destroying signal.

This extends the [[llm-synthesis-context-truncation-blind-spot]] finding from a specific bug to a general principle. The [[asserting-runtime-behavior-from-memory-not-testing]] concept covers the broader discipline; this concept names the specific failure class for pipeline defaults. The [[verification-state-tracking-content-identity-vs-temporal-proxies]] pattern is adjacent: pipeline defaults that go stale (like qmd's index) are a temporal proxy for content identity, not a measurement of actual data state.

## Falsifier

If a systematic audit of pipeline defaults (synthesize_subtopics.py, crawl_to_qmd.py, wiki_manifest.py, wiki_signal_extract.py) finds that all defaults are within 2x of the optimal value given actual data distributions, then this pattern doesn't apply to this workspace and the concept should be retired as over-generalized.

## Sources

- Session 019fbdfb (2026-08-01): wiki-yt truncation bug. Commit `e61fcd3`. Wiki concept: `llm-synthesis-context-truncation-blind-spot.md`.
- Session 019f9aff AAR (2026-07-26): qmd staleness. `P:/docs/aars/aar-019f9aff-20260726.md` episode E7.

## Auto-related

- [[youtube-transcript-extraction-techniques]]
- [[Python-Behavior-Tree-Framework-for-Autonomous-LLM-Agents--Technical-Specificatio]]
- [[skill-catalog]]
- [[video-to-wiki-pipeline-report-metrics-and-framework]]
- [[multi-model-ai-workflow-patterns]]

