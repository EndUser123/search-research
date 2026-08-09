# Handoff — ship-py Phase 2: functionality composition improvements

## Status
OPEN — Phase 1 shipped (defect fixes + FMEA phase). Phase 2 is feature composition.
/www research resolved 3 uncertainties (see Research Verdicts below).

## Objective

Wire ship-py to compose with existing workspace skills at each pipeline phase.
Phase 1 shipped: abort, secret-scan, FMEA phase, session-scoped verdict staleness,
atomic hook state sync, merge-unreachable fix, all_merged fix, SKILL.md 15-phase
docs, 55 tests. Phase 2 is about making ship-py more valuable by leveraging
tools the fleet already has.

## Research verdicts (/www confidence-gap analysis)

| Candidate | Verdict | Evidence | Disposition |
|---|---|---|---|
| /why in fix phase | IMPLEMENT | 4 peer-reviewed RAG-APR papers (RAGFix, ReCode, ReAPR, Dual Retrieval) | P2-3 below |
| review-relay in review | DON'T WIRE | Adds external state files (snapshots, leases) = stale-data risk. Current cmd_review already works (found the critical merge bug). | Replace with cmd_review improvement |
| N-runs flaky detection | DON'T IMPLEMENT | Field consensus: flaky reruns belong in CI, not local. Our "flakiness" is non-hermetic tests, not order-dependence. /check post-ship is the right fix. | Removed from candidate list |
| /design conformance check | IMPLEMENT | Concept documented in wiki (design-doc-conformance-check-procedure.md). Catches proposal-vs-code mismatches. | P2-5 below |

## Phase 2 workstream (4 items)

### P2-1: Improve cmd_review pause instructions (replaces review-relay)

**Current:** review phase spawns 2 agents with "different models" but doesn't enforce model-family diversity.
**Target:** mandate different model families per agent in the pause instruction. The cmd_* function can't spawn agents, but it CAN set the instruction text that tells the LLM which models to use.
**Effort:** S — edit PAUSE_INSTRUCTIONS["review"] in run_all.py.

### P2-2: Integrate version-bump into publish phase

**Current:** publish is `git push origin main` + optional `--tag`.
**Target:** publish phase calls version-bump for full semver + manifest sync + changelog.
**Spike:** read version-bump SKILL.md for manifest assumptions.
**Effort:** M.

### P2-3: Add /why grounding to fix phase

**Current:** fix agent does symptomatic patches.
**Target:** fix agent queries wiki for known failure patterns before proposing fixes.
**Evidence:** 4 peer-reviewed RAG-APR papers (RAGFix IEEE BigData 2024, ReCode ASE 2025, ReAPR EMSE 2025, Dual Retrieval arXiv 2507.10103) show RAG significantly improves LLM bug repair.
**Effort:** M — modify PAUSE_INSTRUCTIONS["fix"] to include /why grounding step.

### P2-4: Add pr-babysit post-publish loop

**Current:** pipeline stops at publish. CI failures, review comments unhandled.
**Target:** optional post-publish phase invoking pr-babysit.
**Effort:** M.

### P2-5: Add /design conformance check

**Current:** no phase verifies implementation matches design doc.
**Target:** when a design doc exists for shipped work, extract behavioral claims and verify against codebase (VERIFIED/ASPIRATIONAL/PARTIAL/CONTRADICTED).
**Concept:** design-doc-conformance-check-procedure.md (already in wiki).
**Effort:** M — new conditional phase, triggered by detect when a design doc is found.

## Remaining low-severity items (from review agent 1)

- gitleaks fail-open in automated runs — document as design choice, consider --strict flag
- abort ownership check — LOW, deferred
