---
title: "Design target: review-relay finding lifecycle + convergence score + per-section parallel review"
session: 019fdf47-6ec5-7b82-b363-a256a98cb5fc
date: 2026-08-09
status: ready-to-design
host: grok
---

# Handoff: Review-relay architectural improvements

## Design target

Design three improvements to the review-relay controller and skill:

1. **Finding lifecycle tracking** — durable `findings.jsonl` per session with state field per finding (`open`/`rebutted`/`upheld`/`resolved`/`superseded`). Partners read this in addition to `previous_result`. Prevents re-verifying the same corrections every round.

2. **Continuous convergence score** — replace boolean `ready_for_parent_review` with a weighted score derived from finding-delta, actor-coverage, and engagement depth. Based on POIROT (arXiv:2606.02282) weighted-aggregation pattern.

3. **Per-section parallel review** — split proposal into sections, let each partner focus on different sections per round (GPT Researcher pattern). Converge per-section before declaring the whole ready.

## Research findings (from /www session 2026-08-09)

### Finding lifecycle (ReviewingAgents pattern)
- Source: https://www.emergentmind.com/topics/reviewingagents
- 14 review-agent frameworks surveyed. Finding lifecycle (open → rebutted → upheld → resolved) outperforms round-reset approaches.
- DIAGPaper adversarial-rebuttal prunes 40-60% of invalid critiques before they accumulate.
- MARG reduced generic-comment rate from 60% to 29%, doubled good-comments-per-paper (3.7 vs 1.7).

### Continuous convergence (POIROT pattern)
- Source: https://arxiv.org/html/2606.02282
- Decentralized failure-detection with binary attribution vector over shared hazard space.
- Distance-weighted voting assigns higher weight to agents structurally closer to each hazard dimension.
- Our hazards: {finding-already-adjudicated, finding-still-open, finding-new-this-round, finding-rejected-and-superseded}.

### Per-section parallel review (GPT Researcher LangGraph)
- Source: https://docs.gptr.dev/docs/gpt-researcher/multi_agents/langgraph
- 7-agent team: Chief Editor → Editor → Researcher + Reviewer + Revisor (per-section loop) → Writer → Publisher.
- Inner loop: for each outline topic in parallel, Researcher drafts → Reviewer validates → Revisor revises until satisfactory.
- Convergence is per-criterion scoring, not by turn count.

### Lease duration (Gerrit CI amplification)
- Source: https://arxiv.org/html/2607.20189
- Dependency-linked reviews experience 5-20x overhead vs solo changes.
- **ALREADY IMPLEMENTED:** lease increased from 120s to 600s this session.

### Stable review key (path-derived)
- **ALREADY IMPLEMENTED:** registry bucket changed from content-hash to path-derived review key this session.

## What already changed this session

These changes are committed and pushed:

1. **Stable review key** — `reviewKeyFromPaths()` in `P:\packages\codex-external-delegation\src\review-relay.mjs`. Registry bucket is now `rk-<pathHash>` instead of `<contentHash>`.
2. **Lease: 120s → 600s** — `DEFAULT_LEASE_SECONDS = 600` in the same file.
3. **Convergence heuristic** — added to `~/.grok/skills/review-relay/SKILL.md`. Tracks finding deltas: converged/stuck/active.

## Files to read

- Controller: `P:\packages\codex-external-delegation\src\review-relay.mjs` (~1300 lines)
- Grok skill: `C:\Users\brsth\.grok\skills\review-relay\SKILL.md`
- Codex operational contract: `P:\packages\codex-external-delegation\docs\review-relay.md`
- Wiki concept: `P:\.data\wiki\concepts\review-relay-improvements-stable-key-lease-calibration-convergence-detection.md`

## Context for the design

The relay just went through 7+ sessions reviewing one proposal (the common model-selection policy). 42 findings, 0 disputes, but massive overhead from:
- Session fragmentation (fixed)
- Lease timeouts (fixed)
- Re-verifying corrections every round (NOT fixed — finding lifecycle is the fix)
- Manual convergence detection (heuristic added, not yet automatic)
- Manual prompt relay between hosts (monitor pattern added, but fragile)

## Run this in a fresh session

```
/design Design the review-relay finding lifecycle tracking, continuous convergence score, and per-section parallel review improvements identified in the /www research at P:\.data\wiki\concepts\review-relay-improvements-stable-key-lease-calibration-convergence-detection.md
```
