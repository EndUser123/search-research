---
title: "Adversarial Review Skill Bundle"
created: 2026-08-09
source: nlm-sync-2026-08-09
tags: [nlm-synced, reference, bundle]
summary: >
  A coordinated set of analysis skills that perform parallel multi-perspective code review through specialist subagents, followed by sequential meta-analysis. The bundle centers on /adversarial-review dispatching 7 specialist agents, with /adversarial-critic synthesizing their JSON findings via consen
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "NotebookLM notebook 16dac687-5ab6-4bf4-8330-632b0e92d852" (Software Quality Assurance (SQA), synced 2026-08-09)
  - "NotebookLM source 34edd71e-ef49-4e7b-bf2b-a608249175cd" (review_bundle_adversarial-review_20260326.md, synced 2026-08-09)
  - "NotebookLM source 3e12f06e-8699-4618-8c9e-487d25a7eebf" (review_bundle_adversarial-performance_20260326.md, synced 2026-08-09)
  - "NotebookLM source df0b3e22-4ca9-469f-9a1c-a8fa721b5d16" (review_bundle_code-review_20260326.md, synced 2026-08-09)
  - "NotebookLM source e3a6f9b5-ea64-4f9a-891a-2c1dc760b666" (review_bundle_critique_20260326.md, synced 2026-08-09)
  - "NotebookLM source f2c88675-a5c4-4563-ac5f-49b75f13d589" (review_bundle_adversarial-critic_20260326.md, synced 2026-08-09)
provenance:
  chain:
    - level: concept
      id: adversarial-review-skill-bundle
    - level: notebook
      id: 16dac687-5ab6-4bf4-8330-632b0e92d852
      title: Software Quality Assurance (SQA)
      url: https://notebooklm.google.com/notebook/16dac687-5ab6-4bf4-8330-632b0e92d852
    - level: cluster
      id: 2
      name: bundle-adversarial-skill
relations:
  - target: wiki/concepts/adversarial-security.md
    type: related
  - target: wiki/concepts/adversarial-performance.md
    type: related
  - target: wiki/concepts/adversarial-compliance.md
    type: related
---

# Adversarial Review Skill Bundle

## Decision context

**Definition:** A coordinated set of analysis skills that perform parallel multi-perspective code review through specialist subagents, followed by sequential meta-analysis. The bundle centers on /adversarial-review dispatching 7 specialist agents, with /adversarial-critic synthesizing their JSON findings via consensus, blind spot, bias, contradiction, and calibration functions.

Synthesized from **5 contributing transcripts** in NotebookLM notebook *Software Quality Assurance (SQA)*, clustered into the "bundle-adversarial-skill" sub-topic. Each claim below cites the specific transcript (source_id + title) that supports it; the frontmatter provenance chain carries the full concept → notebook → cluster → source URL hops.

**Why this matters:** concepts synced from NotebookLM carry provenance back to the source material (notebook → cluster → original URL when invoked via `--from-clusters`). A reader can verify any claim by following the provenance chain in the frontmatter.

## Operational details

- The /adversarial-review skill dispatches 7 specialist agents (security, performance, compliance, quality, testing, logic, failure-modes) in parallel within a single message, each writing JSON findings to .claude/state/adversarial-{type}-[datetime].json.
- After all parallel agents complete, /adversarial-critic runs sequentially to read the 7 JSON files and apply 5 meta-analysis functions: consensus detection (3+ agents same issue = consensus, 5+ = strong consensus), blind spot detection, bias detection, contradiction detection, and quality calibration.
- The /critique skill (v2.0.0) absorbs /adversarial-review functionality as an adaptive dispatcher, using a 3-phase workflow: triage and specialist dispatch (parallel), cross-agent meta-critique, and synthesized final critique, eliminating overlap between two pipelines.
- The /adversarial-performance subagent focuses on 5 performance categories: timeout detection (FAST mode >1s local, >10s web; cache lookup >10ms), bottleneck analysis, cache efficiency (>50% miss rate, <300s TTL), N+1 query detection, and concurrent execution issues, with self-verification requirements to prevent false positives.
- The /code-review skill runs a 6-step workflow (Target → Session → Parallel Dispatch → Synthesis → Report) using 6 specialists (security, logic, performance, io-validation, quality, testing) dispatched via Task tool to general-purpose subagents, with session persistence in P:/.claude/.evidence/code-review/{session_id}/.
- Health Score is computed consistently across skills as: Health Score = 100 - (CRITICAL×20 + HIGH×10 + MEDIUM×5 + LOW×2), capped at 0-100, where ≥80% is Healthy, 50-79% is Warning, and <50% is Critical.
- All findings follow a structured JSON schema with severity tiers (CRITICAL|HIGH|MEDIUM|LOW), triage categories (nit|fix_before_merge|pre-existing), evidence objects (code_excerpt, file_path, line_number, proof), impact descriptions, and recommendations with confidence scores.
- A Constitutional Filter blocks findings containing prohibited patterns: continuous monitoring/always-on tracking without idle timeout, self-healing/auto-correction without approval, team coordination gates in solo environments, and enterprise deployment pipelines for local dev.
- Architectural non-negotiables include: parallel-to-sequential ordering (critic waits for all agents), JSON output schema stability (external tools depend on it), state file naming conventions (adversarial-critic uses glob pattern), and the health score formula.
- Skills in the bundle support trigger aliases: /ar for adversarial-review, /perf-review and /performance for adversarial-performance, /review for code-review, /meta-review and /critic for adversarial-critic.
- The /adversarial-review output uses GTO v2 RSN format with 7 sections (Security, Performance, Quality, Testing, Compliance, Root Cause, Meta-Analysis) and mandatory terminator '0 - Do ALL Recommended Next Steps'.

## Verifiable values

| Name | Value |
|---|---|
| SKILL.md line count (adversarial-review) | `302 lines` |
| SKILL.md line count (adversarial-performance) | `199 lines` |
| SKILL.md line count (code-review) | `200 lines` |
| SKILL.md line count (critique) | `273 lines` |
| SKILL.md line count (adversarial-critic) | `139 lines` |
| FAST mode latency threshold | `<1s` |
| COMPREHENSIVE mode latency range | `5-10s` |
| Cache lookup threshold | `<10ms` |
| Backend health detection interval | `24h` |
| Cache miss rate trigger | `>50%` |
| TTL minimum threshold | `<300s` |
| Consensus threshold (agents same issue) | `3+ agents` |
| Strong consensus threshold | `5+ agents` |
| Health Score CRITICAL penalty | `20 points` |
| Health Score HIGH penalty | `10 points` |
| Health Score MEDIUM penalty | `5 points` |
| Health Score LOW penalty | `2 points` |
| Healthy score range | `≥80%` |
| Warning score range | `50-79%` |
| Critical score range | `<50%` |
| N+1 query impact range | `10-1000x` |
| Cache misconfiguration impact | `50%+ miss rate` |
| Async blocking impact | `2-10x slowdown` |

## Related concepts

- [[adversarial-security]] — adversarial-security
- [[adversarial-performance]] — adversarial-performance
- [[adversarial-compliance]] — adversarial-compliance
- [[adversarial-quality]] — adversarial-quality
- [[adversarial-testing]] — adversarial-testing
- [[adversarial-logic]] — adversarial-logic
- [[adversarial-failure-modes]] — adversarial-failure-modes
- [[adversarial-state-machine]] — adversarial-state-machine
- [[adversarial-io-validation]] — adversarial-io-validation
- [[adversarial-rca]] — adversarial-rca
- [[code-critic]] — code-critic
- [[qa-engineer]] — qa-engineer
- [[health-score-computation]] — Health Score computation
- [[gto-v2-rsn-format]] — GTO v2 RSN format
- [[constitutional-filter]] — Constitutional Filter
- [[/code-review-skill]] — /code-review skill
- [[/critique-skill]] — /critique skill
- [[session-persistence]] — Session persistence

## Citations (from contributing transcripts)

- **Claim:** Parallel adversarial code review system dispatching 7 specialist agents simultaneously
  - Source: review_bundle_adversarial-review_20260326.md (`34edd71e-ef49-4e7b-bf2b-a608249175cd`)
  - Context: Parallel adversarial code review system dispatching 7 specialist agents simultaneously (security, performance, compliance, quality, testing, logic, failure-modes), then running adversarial-critic as sequential meta-analysis
- **Claim:** Each agent writes JSON findings to .claude/state/; the critic aggregates them
  - Source: review_bundle_adversarial-review_20260326.md (`34edd71e-ef49-4e7b-bf2b-a608249175cd`)
  - Context: Each agent writes JSON findings to .claude/state/; the critic aggregates them
- **Claim:** Launch ALL selected agents in ONE message (critical)
  - Source: review_bundle_adversarial-review_20260326.md (`34edd71e-ef49-4e7b-bf2b-a608249175cd`)
  - Context: Launch ALL selected agents in ONE message (critical)
- **Claim:** 5 meta-analysis functions: consensus, blind spot, bias, contradiction, calibration
  - Source: review_bundle_adversarial-critic_20260326.md (`f2c88675-a5c4-4563-ac5f-49b75f13d589`)
  - Context: Consensus Detection, Blind Spot Detection, Bias Detection, Contradiction Detection, Quality Calibration
- **Claim:** Consensus: 3+ agents same issue at same location; Strong Consensus: 5+ agents
  - Source: review_bundle_adversarial-critic_20260326.md (`f2c88675-a5c4-4563-ac5f-49b75f13d589`)
  - Context: Consensus: 3+ agents same issue at same location, Strong Consensus: 5+ agents
- **Claim:** Reads findings from 7 specialist agents (security, performance, compliance, quality, testing, code-critic, qa-engineer)
  - Source: review_bundle_adversarial-critic_20260326.md (`f2c88675-a5c4-4563-ac5f-49b75f13d589`)
  - Context: Reads findings from 7 specialist agents (security, performance, compliance, quality, testing, code-critic, qa-engineer), identifies consensus patterns, blind spots, bias, contradictions, and quality calibration issues
- **Claim:** /critique absorbs /adversarial-review as one adaptive skill instead of two overlapping pipelines
  - Source: review_bundle_critique_20260326.md (`e3a6f9b5-ea64-4f9a-891a-2c1dc760b666`)
  - Context: Absorbs /adversarial-review — one adaptive skill instead of two overlapping pipelines
- **Claim:** 3-phase workflow: triage and specialist dispatch (parallel), cross-agent meta-critique, synthesized final critique
  - Source: review_bundle_critique_20260326.md (`e3a6f9b5-ea64-4f9a-891a-2c1dc760b666`)
  - Context: Phase 1: general-purpose (triage) Orchestrator Classify target, dispatch specialists in parallel; Phase 2: general-purpose After Phase 1 Cross-agent meta-critique; Phase 3: general-purpose After Phase 2 Synthesized final critique
- **Claim:** 5 performance categories: Timeout, Bottleneck, Cache, N+1, Concurrency
  - Source: review_bundle_adversarial-performance_20260326.md (`3e12f06e-8699-4618-8c9e-487d25a7eebf`)
  - Context: 1. Timeout Detection... 2. Bottleneck Analysis... 3. Cache Efficiency... 4. N+1 Query Detection... 5. Concurrent Execution Issues
- **Claim:** Self-verification requirement: Located the code, Measured or traced, Hot path confirmed
  - Source: review_bundle_adversarial-performance_20260326.md (`3e12f06e-8699-4618-8c9e-487d25a7eebf`)
  - Context: Before claiming performance issues exist, verify bottleneck is real: Located the code - Read actual implementation, Measured or traced - Evidence of actual performance impact, Hot path confirmed - Code is on frequently-executed path

## Receipts

Source-derived concept: all claims in this page originate from
transcripts in NotebookLM notebook `16dac687-5ab6-4bf4-8330-632b0e92d852`
(cluster `bundle-adversarial-skill`). No claims are made
about local workspace implementation. Trigger words like
'mechanism', 'scanner', 'gate', 'hook', 'because' refer to concepts
discussed in the source videos, not to local code behavior.
Implementation path: wiki-yt/scripts/synthesize_subtopics.py
(LLM synthesis from transcripts — no local code inspected).

## What this means for our workspace

Synced from NotebookLM. Provenance chain (concept → notebook → cluster → URL) is in frontmatter; follow it back to the source material.

## Falsifier

If a re-sync of the source notebook produces a different definition or different values, this page should be updated (or marked as superseded). The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records when this page was last regenerated.

## Sources

- NotebookLM notebook [Software Quality Assurance (SQA)](https://notebooklm.google.com/notebook/16dac687-5ab6-4bf4-8330-632b0e92d852)
- Studio artifacts: Report (concept extraction) + Data-Table (tabular facts)
