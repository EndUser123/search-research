---
title: "Review-relay improvements: stable review key, lease calibration, convergence detection"
created: 2026-08-09
source: session-2026-08-09
tags: [review-relay, multi-agent-review, convergence-detection, lease-timeout, session-fragmentation, architecture, decision]
host: grok
agent: grok
cognitive_load: 2
verification: directly-verified
relations:
  - target: wiki/concepts/adversarial-multi-agent-code-review.md
    type: implements
  - target: wiki/concepts/pecd-loop-iterative-proposal-evidence-critique-deepen.md
    type: extends
  - target: wiki/concepts/multi-agent-code-review-systems.md
    type: related
summary: >
  Three improvements to the review-relay based on /www research into multi-agent
  review coordination patterns: (1) stable review key derived from file paths
  instead of content hash, preventing session fragmentation when the proposal is
  edited between turns; (2) lease duration increased from 120s to 600s based on
  Gerrit CI amplification research showing 5-20x overhead for dependency-linked
  reviews; (3) convergence auto-detection heuristic that tracks finding deltas
  to suggest ready_for_parent_review when both actors produce 0 new findings.
---

# Review-relay improvements: stable review key, lease calibration, convergence detection

## Decision context

A single proposal (the common model-selection policy) went through 7+ relay
sessions producing 42 findings across 16 turns. Three structural problems
emerged:

1. **Session fragmentation:** each edit to the proposal changed the content
   hash, creating a new session. Prior findings didn't carry forward.
2. **Lease timeouts:** the 120s default lease expired repeatedly during LLM
   review writes, forcing re-tick cycles.
3. **No convergence detection:** both actors agreed on all findings but the
   relay had no mechanism to detect this and suggest stopping.

## What changed

### 1. Stable review key (path-derived, not content-derived)

The registry bucket key changed from `inputSetHash` (SHA-256 of content) to
`reviewKey` (SHA-256 of sorted normalized file paths). This means editing the
proposal between turns continues the same review session. The content hash is
still recorded per-snapshot for audit.

**Before:** `registry/<contentHash>/review-id.json`
**After:** `registry/rk-<pathHash>/review-id.json`

The controller still creates a new immutable snapshot per content revision, but
the session identity is stable.

### 2. Lease duration: 120s → 600s

Research on Gerrit CI amplification (arXiv:2607.20189) found that
dependency-linked reviews experience 5-20x overhead compared to solo changes.
For LLM review turns averaging 5-10 minutes of wall-clock time, the 120s lease
was empirically too tight. The new 600s (10 min) default provides headroom
without sacrificing stale-claim recovery.

### 3. Convergence auto-detection heuristic

Added to the skill: when acting as coordinator, track finding deltas:

- **Converged:** 0 new findings and 0 disputes in last complete round
- **Stuck:** 0 new findings but unresolved findings remain across 2+ rounds
- **Active:** new findings introduced

This is a heuristic, not a gate. The coordinator may still declare
`ready_for_parent_review` manually.

## What the research found (not yet implemented)

The /www research identified three further improvements that require larger
architectural changes:

1. **Finding lifecycle tracking** (ReviewingAgents pattern): durable
   `findings.jsonl` per session with state field
   (`open`/`rebutted`/`upheld`/`resolved`/`superseded`). Partners read this
   in addition to `previous_result`. Prevents re-verifying the same corrections.

2. **Continuous convergence score** (POIROT pattern): replace boolean
   `ready_for_parent_review` with a weighted score derived from
   finding-overlap deltas, actor-coverage, and engagement depth.

3. **Per-section parallel review** (GPT Researcher pattern): split the
   proposal into sections, let each partner focus on different sections per
   round. Converge per-section before declaring the whole ready.

These are design-level changes that should go through `/design` before
implementation.

## Design completed (2026-08-09)

The `/design` run (b1abe493) completed with **reviewer PROCEED** (0 critical/major) and **critical friend PROCEED** (round 2, 1 implementer caveat). All three improvements ship as skill-side sidecars preserving the dumb-pipe invariant (0 LoC in `src/review-relay.mjs`).

**Key architectural decision:** adr-011-review-relay-dumb-pipe-invariant — ship dumb-pipe first, migrate to inspecting-pipe only on production bottleneck (≥30 days + cross-section/adaptive-lease/finding-provenance requirement materializes).

**Implementation units:** 15 units across 4 phases (~1830 new LoC, 6 skill helpers + 8 test files, 0 relay LoC).

**Open implementer question:** `previous_findings_path` tick-input inconsistency (R2-N1) — resolved as coordinator-side sidecar (true 0 relay lines, preserves invariant strictly).

**Design artifacts (in temp, will be reaped by OS):**
- Design doc: `C:/Users/brsth/AppData/Local/Temp/grok-design-b1abe493/grok-design-doc-b1abe493.md`
- Summary: `C:/Users/brsth/AppData/Local/Temp/grok-design-b1abe493/grok-design-summary-b1abe493.md`

The durable decision is captured in the ADR above; the design doc is working scaffolding.

## Receipts

- `P:\packages\codex-external-delegation\src\review-relay.mjs` — reviewKeyFromPaths, registryBucket, DEFAULT_LEASE_SECONDS=600
- `~/.grok/skills/review-relay/SKILL.md` — convergence auto-detection heuristic, stable review key documentation
- `P:\packages\codex-external-delegation\docs\review-relay.md` — stable review key in operational contract

## Auto-related

- [[adversarial-multi-agent-code-review]] — the architectural pattern this relay implements
- [[pecd-loop-iterative-proposal-evidence-critique-deepen]] — convergence detection via "zero refine items → exit"
- [[multi-agent-code-review-systems]] — role-differentiated agents with structured communication
- [[token-optimization-patterns-for-agent-fleets]] — convergence detection prevents wasting tokens on non-converging loops
