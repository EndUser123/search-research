# ADR-20260329: SQA Skill — Five Enhancement Ideas

**Status**: Accepted (supersedes initial Defer on Idea 2)

**Date**: 2026-03-29

**Target**: `/sqa` skill — `orchestrator.py` + `layers/`

---

## Context

Five enhancement ideas were evaluated for the `/sqa` skill (7-layer sequential quality model: Syntactic→Semantic→Structural→Requirements→Security→Performance→Operational→Meta-Synthesis):

1. Multi-Agent Parallel Reasoning & Synthesis
2. Strict Convergence Gates & Hook-Driven Transitions
3. Weighted Quality Scoring Algorithms
4. "Zero Guessing" Evidence Citations
5. Pre-Mortem Analysis for Layer 4 (Requirements)

**Key architectural constraint discovered during review**: The orchestrator has only one hard dependency (L2→L4). All other layers (L1, L3, L5, L6, L7) are independent and can run concurrently.

**Key architectural insight on Idea 2**: `PostToolUse_rca_phase_tracker.py` is a passive phase detector (not a gate). It infers phase from tool names, skill names, and output content — it does not block transitions. The real problem Idea 2 solves is **detecting whether a layer actually executed its characteristic analysis** (vs. returning empty findings benignly).

---

## Decisions

### Idea 1 — Multi-Agent Parallel Reasoning & Synthesis

**Decision**: ADOPT

**Rationale**: Only L2→L4 is a hard dependency. L1, L3, L5, L6, L7 are fully independent. Batch-dispatching these via `ThreadPoolExecutor` in `_run_layer()` could cut wall-clock time by ~40-60%.

**Implementation**:
- Batch L1/L3/L5/L6 in parallel via `concurrent.futures.ThreadPoolExecutor`
- Collect all results before proceeding to L4
- L4 waits for L2 (hard dep) + L1/L3/L5/L6 (for layered findings context)
- L7 runs after all others complete

**Risk**: L4/L7 are still sequential. No failure conditions beyond existing graceful degradation.

---

### Idea 2 — Convergence Gates via Hook Pattern

**Decision**: ADAPT (upgraded from Defer)

**Original Defer rationale was wrong**: `PostToolUse_rca_phase_tracker.py` does not block transitions — it only detects phase from output patterns. The convergence problem is real: a layer could return zero findings because it genuinely found nothing, OR because the LLM silently skipped the analysis.

**Revised rationale**: A `PostToolUse_sqa_phase_tracker.py` hook can detect whether each layer's characteristic tool was actually invoked during its execution window:
- L1: ruff, mypy (Bash)
- L2: verify/diagnose (Skill)
- L3: meta-review, harden (Skill)
- L5: adversarial-security (Task/Agent)
- L6: adversarial-performance (Task/Agent)
- L7: verify, hook-audit (Skill)

**Implementation constraint**: Requires per-layer tool signature tracking — not a generic phase gate. Each layer uses different tool types (Bash, Skill, Task/Agent). The hook must know which signature maps to which layer.

**Implementation**:
- Create `PostToolUse_sqa_phase_tracker.py` with layer-specific detection patterns
- Track execution window per layer (start/end markers in state)
- Flag as warning if a layer completes but its characteristic tool was never invoked
- Does NOT block — advisory only (layer returning empty findings may be legitimate)

---

### Idea 3 — Weighted Quality Scoring Algorithms

**Decision**: ADOPT

**Rationale**: Current formula treats all layers/severties equally. Enhancement adds:
- Severity bands: 95-100 NOMINAL, 80-94 MINOR, <50 CRITICAL
- Per-finding score: `Reproducibility(0.3) × Recency(0.2) × Impact(0.5)` (rca hypothesis scoring)
- Layer weights: 30% Semantic, 25% Structural, 20% Security (residual to others)

**Implementation**: Add `_compute_layer_weights()` helper + severity band constants. Findings model already supports all required fields (severity, evidence_tier, consensus).

**Risk**: Low. Pure formula change, no pipeline restructuring.

---

### Idea 4 — "Zero Guessing" Evidence Citations

**Decision**: ADOPT

**Rationale**: Meta-synthesis (`layer_meta.py`) already flags T4-only findings via `_check_evidence_quality()`. Missing: enforcement pass — findings without `file:line` from L1-L7 should be auto-downgraded to T4 before meta runs.

**Implementation**:
- Add `_enforce_evidence_citations(findings)` in meta-synthesis
- Auto-downgrade any L1-L7 finding with `evidence_tier >= T1` but `location is None` to T4
- Allowlist for design-level findings that cannot provide `file:line` (e.g., architectural concerns)
- Report downgraded count as a meta-finding

**Risk**: Low. Existing evidence model supports this.

---

### Idea 5 — Pre-Mortem Analysis for Layer 4 (Requirements)

**Decision**: ADAPT

**Rationale**: Layer 4 currently runs `gto` gap analysis and `spec-compliance`. Embedding reflect's pre-mortem engine directly would require significant integration work (free-text requirements vs. artifact status files).

**Implementation**: Add a lightweight pre-flight call to reflect's contradiction detection on existing spec files *before* gto runs. No deep embedding — one-shot check on PRD/ARD/CHANGELOG/README.

**Risk**: Medium. Reflect operates on natural language; spec files are structured. May need prompt engineering to bridge the gap.

---

## Summary

| Idea | Decision | Implementation Risk | Priority |
|------|----------|---------------------|----------|
| 1. Parallel layers | **ADOPT** | Medium | 2 |
| 2. Convergence gates | **ADAPT** | Medium | 4 |
| 3. Weighted scoring | **ADOPT** | Low | 1 |
| 4. Zero-guessing citations | **ADOPT** | Low | 1 |
| 5. Pre-mortem L4 | **ADAPT** | Medium | 3 |

**Implementation priority order**: 3 → 4 → 1 → 5 → 2

**Reversibility**: 1.0 (all changes are additive formula/flow changes; no deletion of existing behavior)

---

## Change Log

- 2026-03-29: Initial ADR created
- 2026-03-29: Idea 2 upgraded from Defer to Adapt after architectural review revealed `PostToolUse_rca_phase_tracker.py` is a passive detector, not a gate. Real value identified as per-layer tool signature tracking.
