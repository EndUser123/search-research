# Implementation Plan: Cognitive Cross-Category Compatibility Matrix

**Date**: 2026-03-15
**Status**: DRAFT
**Priority**: HIGH (Architecture Decision Record)
**Related ADR**: `2025-03-14_fast_cognitive-reasoning-cross-category-triggers.md`

---

## Context Section: Trigger for Architectural Decision

### Problem Statement

The CKS memory integration (completed 2026-03-14) revealed a critical missed synergy in the cognitive reasoning system: **cross-category triggers are not being detected or utilized**.

**Specific Example from CKS Integration**:
- User message: "I need to add git-based state tracking for multi-terminal support"
- Current system behavior: Triggers individual categories (git → investigation_gate, multi-terminal → questioning_patterns)
- **Missed opportunity**: The COMBINATION of "git" + "multi-terminal" should trigger a specialized cross-category enhancement (e.g., "concurrent_state_management_with_git_fallback")
- User correction required: Git has race conditions in multi-terminal environments (already documented in `questioning_patterns.md`)
- Root cause: Cognitive frameworks, reasoning modes, and think profiles operate in isolation without cross-category awareness

**Evidence from CKS Usage Logs** (2026-03-14):
- 331 CKS chunks ingested from 40 memory files
- 141 knowledge entries, 128 pattern entries, 62 correction entries
- CKS query: "git multi-terminal race condition" → 3 relevant entries found
- **Gap**: These synergies should be detected BEFORE CKS query, not after

### Why This Matters Now

**Timing Driver**: CKS memory integration is now operational and surfacing missed cross-category patterns in real usage. The compatibility matrix will:
1. **Prevent redundant CKS queries** by detecting cross-category patterns upfront
2. **Improve cognitive accuracy** by applying specialized enhancements for known cross-category combinations
3. **Reduce correction cycles** by surfacing relevant lessons earlier in the workflow

**Reference**: `docs/cks_memory_integration_20260314.md` for complete integration details

---

## Related Decisions

### Architecture Decision Records (ADRs)

**Primary ADR**: `2025-03-14_fast_cognitive-reasoning-cross-category-triggers.md`
- **Decision**: Matrix-based organization with compatibility rules (Option C)
- **Key insight**: Current `unified_detection.py` returns all three lists (`matched_frameworks`, `matched_modes`, `matched_profiles`) but doesn't detect cross-category combinations
- **Implementation**: Add compatibility matrix layer to enable cross-pollination where valuable

**Related ADRs**:
1. **Cognitive Architecture ADRs** (P:/.claude/arch_decisions/):
   - Cognitive reasoning framework design
   - Unified detection engine architecture
   - Questioning patterns integration

2. **CKS Integration ADRs**:
   - Memory to CKS integration (2026-03-14)
   - Auto-retrieval patterns for hooks
   - Semantic search optimizations

3. **Performance Optimization ADRs**:
   - Single-pass detection vs multi-pass overhead
   - Synergy detection performance requirements
   - Compatibility matrix lookup optimization

### Implementation Context

**Current Code State** (from ADR analysis):
```python
# Current: unified_detection.py lines 30-51
@dataclass(frozen=True)
class UnifiedDetectionResult:
    matched_frameworks: list[str] = field(default_factory=list)
    matched_modes: list[str] = field(default_factory=list)
    matched_profiles: list[str] = field(default_factory=list)
    # MISSING: No cross-category combination detection
```

**Proposed Enhancement**:
```python
# Add: Compatibility matrix for cross-category triggers
_COMPATIBILITY_MATRIX: dict[tuple[str, str, str], str] = {
    # (framework, mode, profile) -> enhancement_to_apply
    ("assumption_surfacing", "multi_agent", "debug_rca"): "parallel_assumption_checking",
    ("socratic_decomposition", "graph", "architecture"): "branching_decomposition",
    # Add more as discovered
}

# Extend UnifiedDetectionResult
@dataclass(frozen=True)
class UnifiedDetectionResult:
    matched_frameworks: list[str]
    matched_modes: list[str]
    matched_profiles: list[str]
    compatible_combinations: list[str] = field(default_factory=list)  # NEW
```

---

## Success Criteria: Measurable Outcomes

### Primary Metrics (Must Achieve)

**M1: Cross-Category Trigger Usage**
- **Target**: >15% of UserPromptSubmit events use cross-category triggers
- **Measurement**: Track `compatible_combinations` usage in performance.db
- **Baseline**: 0% (current system has no cross-category detection)
- **Rationale**: If cross-category triggers are <15%, the compatibility matrix provides insufficient value

**M2: Performance Overhead**
- **Target**: <5ms overhead for compatibility matrix lookup
- **Measurement**: Add timing to `unified_detection.py` compatibility check
- **Baseline**: Current detection ~60ms (from plan-20260314-cognitive-reasoning-optimization.md T-000)
- **Rationale**: Matrix lookup should be negligible (O(1) dictionary lookup)

**M3: Maintainability**
- **Target**: <50 compatibility matrix entries
- **Measurement**: Count entries in `_COMPATIBILITY_MATRIX` dictionary
- **Baseline**: 0 entries (starting fresh)
- **Rationale**: If matrix grows beyond 50 entries, curation burden exceeds value

### Secondary Metrics (Should Achieve)

**S1: CKS Query Reduction**
- **Target**: 20% reduction in CKS queries for cross-category patterns
- **Measurement**: Compare CKS query counts before/after implementation
- **Baseline**: Current CKS auto-retrieval on every trigger word
- **Rationale**: Cross-category detection should surface patterns before CKS query

**S2: Correction Cycle Reduction**
- **Target**: 30% reduction in user corrections for cross-category issues
- **Measurement**: Track user correction frequency in logs
- **Baseline**: 1-2 corrections per session (from CKS integration analysis)
- **Rationale**: Cross-category enhancements should prevent common mistake patterns

**S3: False Positive Rate**
- **Target**: <10% false positive rate for cross-category triggers
- **Measurement**: User feedback on irrelevant cross-category enhancements
- **Baseline**: Unknown (no implementation yet)
- **Rationale**: High false positive rate will lead to users disabling the feature

### Tertiary Metrics (Nice to Have)

**T1: Coverage**
- **Target**: Detect top 10 most common cross-category combinations from CKS logs
- **Measurement**: Analyze CKS query patterns from last 30 days
- **Baseline**: Unknown (need to analyze logs first)
- **Rationale**: Ensure compatibility matrix covers high-value combinations

**T2: Discovery Latency**
- **Target**: <1 week from new cross-category pattern → matrix entry
- **Measurement**: Time from CKS log analysis → matrix update
- **Baseline**: Unknown (no discovery mechanism yet)
- **Rationale**: Fast iteration on new patterns improves system value

---

## Baseline Measurements (Pre-Implementation)

### Current System State

**Cognitive Frameworks** (9 frameworks):
- `assumption_surfacing`, `outcome_anchoring`, `inversion_prompting`, `chestertons_fence`, `calibrated_confidence`, `socratic_decomposition`, `cynefin_classification`, `hanlons_razor`, `devils_advocate`

**Reasoning Modes** (4 modes):
- `sequential`, `multi_agent`, `graph`, `two_stage`

**Think Profiles** (7 profiles):
- `debug_rca`, `tradeoff_decision`, `architecture`, `pre_commit_risk`, `security_review`, `performance_analysis`, `multi_file_refactor`

**Theoretical Combinations**: 9 × 4 × 7 = 252 possible cross-category combinations

**CKS Integration Data** (from `docs/cks_memory_integration_20260314.md`):
- 331 CKS chunks ingested
- 141 knowledge entries, 128 pattern entries, 62 correction entries
- CKS query success rate: 100% (operational)
- Multi-terminal safety: VERIFIED (PID-based locking)

### Performance Baseline

**From plan-20260314-cognitive-reasoning-optimization.md T-000**:
- Current overhead: ~120ms per UserPromptSubmit event
  - Cognitive frameworks: ~50ms (9 intent regex checks)
  - Reasoning mode selector: ~30ms (keyword detection)
  - Think trigger: ~40ms (7 profile × 2 pattern types)
- Duplicate work: ~30% (same prompt tokens analyzed 3x)
- **Target after optimization**: ~60ms per event

**Compatibility Matrix Overhead Target**:
- Additional overhead: <5ms (8% of optimized baseline)
- Lookup complexity: O(1) dictionary lookup
- Memory footprint: <1KB for 50 entries

---

## Implementation Phases

### Phase 1: Data Collection & Analysis (Week 1)

**T-001**: Analyze CKS logs for cross-category patterns
- Query CKS database for last 30 days of query patterns
- Identify top 20 cross-category combinations
- Document evidence for each combination (user corrections, repeated mistakes)
- **Deliverable**: `analysis/cross_category_patterns_20260315.md`

**T-002**: Define initial compatibility matrix schema
- Design `_COMPATIBILITY_MATRIX` data structure
- Document metadata requirements for each entry:
  - Combination tuple (framework, mode, profile)
  - Enhancement name
  - Evidence source (CKS entry, user correction, memory file)
  - Creation date
  - Usage count
- **Deliverable**: Schema document + JSON template

### Phase 2: Core Implementation (Week 2)

**T-003**: Implement compatibility matrix in unified_detection.py
- Add `_COMPATIBILITY_MATRIX` dictionary
- Extend `UnifiedDetectionResult` with `compatible_combinations` field
- Implement matrix lookup logic in `detect()` function
- Add timing for matrix lookup overhead
- **Deliverable**: Updated `unified_detection.py` with compatibility detection

**T-004**: Add initial 10-15 compatibility matrix entries
- Seed matrix from T-001 analysis results
- Focus on high-value combinations (>5 occurrences in CKS logs)
- Document evidence for each entry
- **Deliverable**: Initial `_COMPATIBILITY_MATRIX` with 10-15 entries

**T-005**: Extend conflict_arbiter.py with cross-category rules
- Add Rule 7: Cross-category synergy override
- Implement precedence logic (matrix > individual triggers)
- Add rationale output explaining cross-category selection
- **Deliverable**: Updated `conflict_arbiter.py` with cross-category rules

### Phase 3: Testing & Validation (Week 3)

**T-006**: Write compatibility matrix tests
- Unit tests for matrix lookup logic
- Integration tests for cross-category detection
- Performance tests for <5ms overhead requirement
- False positive rate tests
- **Deliverable**: `tests/test_compatibility_matrix.py` with >90% coverage

**T-007**: Add performance monitoring for cross-category metrics
- Track `compatible_combinations` usage in performance.db
- Log cross-category trigger events
- Monitor CKS query reduction rate
- **Deliverable**: Updated `performance_monitor.py` with cross-category metrics

**T-008**: Measure baseline metrics before deployment
- Measure M1: Cross-category trigger usage (baseline: 0%)
- Measure M2: Performance overhead (baseline: 0ms)
- Measure M3: Matrix entry count (baseline: 0 entries)
- Measure S1: CKS query count (baseline: current rate)
- **Deliverable**: `baselines/cross_category_baseline_20260315.json`

### Phase 4: Deployment & Monitoring (Week 4)

**T-009**: Deploy compatibility matrix to production
- Roll out to 10% of sessions (feature flag)
- Monitor M1-M3 metrics for 48 hours
- Check false positive rate (S3)
- **Deliverable**: Gradual rollout plan + monitoring dashboard

**T-010**: Full production deployment
- Enable for 100% of sessions
- Monitor all metrics for 1 week
- Create weekly analysis report
- **Deliverable**: Production monitoring dashboard + weekly reports

**T-011**: Iteration based on metrics
- Analyze M1-M3 performance
- Add new matrix entries based on usage patterns
- Remove low-value entries (<1% usage)
- Tune thresholds based on false positive rate
- **Deliverable**: Monthly optimization report

---

## Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Performance regression** | Low (15%) | High | T-006 includes performance tests; T-007 monitors overhead |
| **High false positive rate** | Medium (35%) | Medium | S3 metric monitoring; T-011 for iteration; disable threshold at >20% false positive |
| **Matrix curation burden** | High (50%) | Medium | M3 metric (<50 entries); T-011 monthly pruning; auto-suggestion from CKS logs |
| **Conflict with existing triggers** | Low (20%) | Medium | T-005 precedence rules; backward compatibility; individual triggers still work |
| **CKS integration complexity** | Medium (30%) | Low | S1 metric measures reduction; graceful degradation if CKS unavailable |

### Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **User confusion from new tags** | Medium (40%) | Low | Clear documentation; gradual rollout; user feedback collection |
| **Matrix entry quality variance** | Medium (35%) | Medium | Evidence-based entries (CKS/memory); peer review for high-impact entries |
| **Maintenance overhead** | High (60%) | Medium | M3 metric enforces <50 entries; monthly review process; auto-pruning |

---

## Dependencies

### Blockers (must be unblocked before starting)
- None (can start immediately)

### Required (needed for implementation)
- CKS memory integration operational ✅ (completed 2026-03-14)
- Unified detection engine implemented ✅ (from plan-20260314-cognitive-reasoning-optimization.md)
- Performance monitoring infrastructure ✅ (from plan-20260314-cognitive-reasoning-optimization.md T-004)

### Optional (nice to have but not required)
- Automated CKS log analysis tools
- Compatibility matrix visualization dashboard
- Community contribution workflow for matrix entries

---

## Rollback Strategy

If critical issues found after deployment:

### Immediate Rollback (<5 minutes)
1. Disable compatibility matrix via feature flag
2. Revert to individual category triggers only
3. Clear `_COMPATIBILITY_MATRIX` dictionary
4. Restart Claude Code session

### Verification
1. Run `tests/test_compatibility_matrix.py` to verify disabled state
2. Check performance.db for no cross-category events
3. Confirm individual triggers still work

### Post-Mortem
1. Analyze performance.db for failure patterns
2. Review CKS logs for missed patterns
3. Create fix and re-test in staging
4. Update matrix with corrections

---

## Appendix: Task Summary

### Task Breakdown

| ID | Task | Effort | Priority | Dependencies |
|----|------|--------|----------|--------------|
| T-001 | Analyze CKS logs for cross-category patterns | M (2-3h) | HIGH | None |
| T-002 | Define initial compatibility matrix schema | S (1-2h) | HIGH | T-001 |
| T-003 | Implement compatibility matrix in unified_detection.py | L (3-4h) | HIGH | T-002 |
| T-004 | Add initial 10-15 compatibility matrix entries | M (2-3h) | HIGH | T-001, T-003 |
| T-005 | Extend conflict_arbiter.py with cross-category rules | M (2-3h) | HIGH | T-003 |
| T-006 | Write compatibility matrix tests | L (3-4h) | HIGH | T-003, T-004, T-005 |
| T-007 | Add performance monitoring for cross-category metrics | M (2-3h) | MEDIUM | T-003 |
| T-008 | Measure baseline metrics before deployment | M (2-3h) | MEDIUM | T-003, T-004, T-005 |
| T-009 | Deploy compatibility matrix to production (10% rollout) | M (2-3h) | HIGH | T-006, T-007, T-008 |
| T-010 | Full production deployment | S (1-2h) | HIGH | T-009 |
| T-011 | Iteration based on metrics | M (2-3h) | MEDIUM | T-010 |

**Total Effort**: ~23-33 hours (2.9-4.1 working days)

### Critical Path

```
T-001 (CKS log analysis) → T-002 (schema) → T-003 (implementation) → T-004 (initial entries) → T-005 (conflict arbiter) → T-006 (tests) → T-009 (10% rollout) → T-010 (full rollout)
                                                    → T-007 (monitoring) ↗
                                                    → T-008 (baseline) ↗
```

**Parallel Opportunities**:
- T-002 (schema) can start after T-001 begins
- T-005 (conflict arbiter) can run parallel to T-004 (entries)
- T-007 (monitoring) and T-008 (baseline) can run parallel after T-003
- T-011 (iteration) runs after T-010 (ongoing)

**Minimum Viable Implementation** (MVP):
- T-001, T-002, T-003, T-004, T-005, T-006, T-008, T-009
- Addresses M1-M3 primary metrics
- Effort: ~16-22 hours (2.0-2.8 working days)

**Full Implementation** (all 11 tasks):
- Addresses all M/S/T metrics
- Includes monitoring and iteration
- Effort: ~23-33 hours (2.9-4.1 working days)

---

**Plan Version**: 1.0 (INITIAL DRAFT)
**Last Updated**: 2026-03-15
**Status**: READY-FOR-REVIEW
**Next Step**: T-001 - Analyze CKS logs for cross-category patterns
