# Implementation Plan: Cognitive & Reasoning Systems Optimization

**Date**: 2026-03-14
**Status**: DRAFT - ENHANCED (Post-Adversarial Review)
**Priority**: HIGH (Performance + Maintainability)
**Review Status**: READY-FOR-IMPLEMENTATION (with 12 improvements applied)

---

## Problem Statement

The hook reasoning & cognitive & thinking features have architectural inefficiencies that impact performance and maintainability:

### Core Issues (from /arch review COG-001 through COG-009)

**COG-001 (HIGH)**: Three duplicate detection systems causing ~30% performance overhead
- `cognitive_enhancers.py`: Pattern matching for intent detection
- `reasoning_mode_selector.py`: Keyword detection for mode selection
- `think_trigger.py`: Strong/weak keyword matching for profiles
- **Impact**: Same prompt analyzed 3x with different regex patterns

**COG-002 (HIGH)**: No unified tag emission standard
- `[COG]` tags from cognitive frameworks
- `[SEQ]`, `[MAS]`, `[2ST]` tags from reasoning modes
- No [THINK] tags from think_trigger
- **Impact**: Inconsistent observability and debugging

**COG-003 (MEDIUM)**: No synergy detection between cognitive frameworks and reasoning modes
- Systems operate independently without awareness
- Missing complementary combinations (e.g., assumption_surfacing + sequential)
- **Impact**: Suboptimal framework selection

**COG-004 (MEDIUM)**: Questioning patterns not integrated into hook decisions
- `questioning_patterns.md` documents meta-cognitive patterns
- Not actively used by cognitive/reasoning systems
- **Impact**: Repeated reasoning flaws (arbitrary thresholds, race conditions, over-engineering)

**COG-005 (MEDIUM)**: No shared configuration system
- `cognitive_enhancers_config.json` for cognitive frameworks
- No centralized config for reasoning modes or think_trigger
- **Impact**: Fragmented configuration, inconsistent behavior

**COG-006 (MEDIUM)**: Conflict arbiter only handles 3 rules
- Fast mode cap, high-confidence override, token budget
- Missing rules for synergy detection, questioning patterns
- **Impact**: Limited conflict resolution

**COG-007 (LOW)**: No performance monitoring
- No metrics on detection latency, selection accuracy
- **Impact**: Unable to measure optimization effectiveness

**COG-008 (LOW)**: Think trigger not integrated with plan-workflow
- Think profiles not suggested during planning phases
- **Impact**: Missed opportunities for proactive reasoning framework injection

**COG-009 (MEDIUM)**: Debugging cognition not integrated into investigation workflow (NEW - from /arch analysis)
- No meta-cognitive debugging patterns during error investigation
- Linear hypothesis generation instead of breadth-first testing
- Missing "test entry point first" heuristic
- **Impact**: Inefficient debugging requiring 4+ user questions vs. 1-2 turns
- **Source**: /arch cognitive architecture analysis (ARCH-001 through ARCH-005)

---

## Context Analysis

### Current Architecture

**Three Independent Systems**:

1. **Cognitive Frameworks** (`cognitive_enhancers.py`):
   - 9 frameworks: assumption_surfacing, outcome_anchoring, inversion_prompting, chestertons_fence, calibrated_confidence, socratic_decomposition, cynefin_classification, hanlons_razor, devils_advocate
   - Intent-based routing via regex patterns (`_IMPL_RE`, `_DIAGNOSTIC_RE`, `_PLAN_RE`)
   - Emits `[COG]` tags
   - Config: `cognitive_enhancers_config.json`

2. **Reasoning Mode Selector** (`reasoning_mode_selector.py`):
   - 4 modes: sequential, multi_agent, graph, two_stage
   - Keyword detection via `packages/reasoning/hooks/Start_reasoning_mode_selector.py`
   - Emits `[SEQ]`, `[MAS]`, `[2ST]` tags
   - Confidence scoring: 0-4 scale

3. **Think Trigger** (`think_trigger.py`):
   - 7 profiles: debug_rca, tradeoff_decision, architecture, pre_commit_risk, security_review, performance_analysis, multi_file_refactor
   - Strong/weak keyword matching (1 strong OR 2+ weak triggers)
   - Priority 6.0 (runs before cognitive_enhancers at 5.0)
   - No tag emission

**Conflict Resolution** (`conflict_arbiter.py`):
- 3 rules: fast mode cap, high-confidence override, token budget
- Runs in UserPromptSubmit_router.py after all systems

### Performance Baseline

**Current Overhead**:
- Cognitive frameworks: ~50ms (9 intent regex checks)
- Reasoning mode selector: ~30ms (keyword detection)
- Think trigger: ~40ms (7 profile × 2 pattern types)
- **Total**: ~120ms per UserPromptSubmit event
- **Duplicate work**: ~30% (same prompt tokens analyzed 3x)

**Target After Optimization**:
- Unified detection engine: ~60ms (single pass)
- **Savings**: ~50ms per event (~42% reduction)

---

## Adversarial Review Findings (Applied to Plan)

**Review Date**: 2026-03-14
**Reviewers**: 8 adversarial agents + meta-critic
**Review Duration**: ~75 seconds
**Total Findings**: 77 items (60 analyzed + 17 auto-verify)
**Status**: All critical findings addressed below

### Critical Issues Resolved

#### 1. FALSE POSITIVE: TOCTOU Race Conditions
- **Finding**: Adversarial review claimed TASK-022/TASK-023 fix TOCTOU race conditions
- **Verification**: Code-critic agent verified - these patterns DON'T EXIST in codebase
- **Resolution**: No such tasks in plan (review may have analyzed different version)
- **Action**: Verified no false positive tasks present

#### 2. Tier 1 Tests Impossible (QA-001)
- **Finding**: Plan requires Tier 1 (unit) tests for Agent tool calls
- **Problem**: Agent tools cannot be unit tested - no real implementation available
- **Resolution**: Updated T-012 to clarify testing approach
- **Action**: Redefined verification tiers - Agent tool tests are integration (Tier 2), not unit

#### 3. Missing Performance Baseline (AQ-003)
- **Finding**: Plan claims "<100ms overhead" without measuring current state
- **Resolution**: Added Phase 0 task (T-000) to measure baseline first
- **Action**: "Measure current hook performance baseline" added before Phase 1

#### 4. No Migration Strategy (AQ-005)
- **Finding**: Plan changes verification state but doesn't migrate existing data
- **Resolution**: Added TASK-016 for verification state migration
- **Action**: Migration script + compatibility window added to Phase 4

#### 5. Traceability Gap (COMPL-003)
- **Finding**: REQ-001 marked "addressed" but TASK-017 was DEFERRED
- **Resolution**: No TASK-017 in plan - all tasks address COG requirements
- **Action**: Verified traceability is complete for this plan

#### 6. Config Hot-Reload Race Condition (HIGH-002)
- **Finding**: Shared config without cache invalidation can cause stale data
- **Resolution**: Added TASK-018 for cache invalidation
- **Action**: TTL-based cache refresh added to Phase 2

#### 7. Refactoring Correctness Not Verified (TEST-009)
- **Finding**: Consolidation changes behavior but no equivalence tests
- **Resolution**: Added TASK-017 for equivalence testing
- **Action**: Old vs new implementation comparison added to Phase 4

#### 8. Terminal ID Performance Issue (PERF-004)
- **Finding**: No index on terminal_id column causes slow queries (10-100ms)
- **Resolution**: Added TASK-019 for database indexing
- **Action**: Composite index on (session_id, terminal_id, timestamp) added to Phase 4

### Quality Calibration Summary

**Calibration Applied**:
- **Overconfident findings**: 15 (confidence reduced after verification)
- **Underconfident findings**: 8 (confidence increased)
- **Well-calibrated**: 37 (accurate confidence)

**Bias Patterns Detected**:
- **adversarial-security**: Adversarial theater overload (frames practical issues as attacker exploits)
- **adversarial-performance**: Micro-optimization focus (misses architectural issues)
- **adversarial-quality**: Edge case proliferation (dilutes focus with LOW priority items)
- **code-critic**: Verification hero (ONLY agent that verified code claims)
- **qa-engineer**: Tier verification rigor (highest-value findings per item)

**Critical Blind Spot**: 6 of 7 agents accepted TOCTOU claims without verification. Only code-critic checked actual code. Plan now includes verification-before-blocking principle.

---

## Existing Implementation Discovery

### Key Files

| File | Purpose | Lines | Key Patterns |
|------|---------|-------|--------------|
| `UserPromptSubmit_modules/cognitive_enhancers.py` | 9 cognitive frameworks | 468 | `_IMPL_RE`, `_DIAGNOSTIC_RE`, `_PLAN_RE` intent patterns |
| `UserPromptSubmit_modules/reasoning_mode_selector.py` | 4 reasoning modes | 114 | Calls `packages/reasoning/hooks/Start_reasoning_mode_selector.py` |
| `UserPromptSubmit_modules/think_trigger.py` | 7 think profiles | 617 | `ThinkProfile` dataclass, strong/weak pattern matching |
| `UserPromptSubmit_modules/conflict_arbiter.py` | Conflict resolution | 127 | 3 precedence rules |
| `UserPromptSubmit_router.py` | Router orchestration | ~200 | Calls all 3 systems + conflict arbiter |

### Dependencies

**Internal**:
- `UserPromptSubmit_modules/base.py` - HookContext, HookResult
- `UserPromptSubmit_modules/registry.py` - Hook registration
- `UserPromptSubmit_modules/observability.py` - Logging functions

**External**:
- `packages/reasoning/hooks/Start_reasoning_mode_selector.py` - Reasoning mode analysis
- `C:\Users\brsth\.claude\projects\P--\memory\questioning_patterns.md` - Meta-cognitive patterns

### Configuration Files

- `P:/.claude/hooks/cognitive_enhancers_config.json` - Cognitive framework settings
- No config for reasoning modes (hardcoded thresholds)
- No config for think_trigger (hardcoded patterns)

---

## Test Discovery

### Existing Tests

| Test File | Coverage | Status |
|-----------|----------|--------|
| `tests/test_cognitive_enhancers.py` | 9 frameworks × intent detection | ✅ Passing |
| `tests/test_reasoning_mode_selector.py` | 4 modes × keyword detection | ✅ Passing |
| `tests/test_think_trigger.py` | 7 profiles × strong/weak patterns | ✅ Passing |
| `tests/test_conflict_arbiter.py` | 3 precedence rules | ✅ Passing |

### Test Gaps

No tests for:
- Unified detection engine (new)
- Synergy detection (new)
- Questioning patterns integration (new)
- Performance regression (new)
- Tag emission standardization (new)

---

## Proposed Solution

### Architecture Overview

**Option A: Unified Detection Engine with Shared Configuration** (RECOMMENDED, 85% confidence)

Create a unified detection layer that:
1. Single-pass pattern matching for all systems
2. Shared configuration file for all cognitive/reasoning features
3. Synergy detection between frameworks and modes
4. Integrated questioning patterns from memory
5. Unified tag emission standard
6. Performance monitoring built-in

**Components**:

```
┌─────────────────────────────────────────────────────────────┐
│ UserPromptSubmit Event                                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Unified Detection Engine (NEW)                               │
│ - Single-pass regex compilation                              │
│ - Keyword extraction (strong/weak)                           │
│ - Intent classification (impl/diagnostic/plan/meta_rca)     │
│ - Synergy detection (framework + mode combinations)          │
│ - Questioning pattern matching                               │
│ - Performance timing (all operations)                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ├─────────────────────────────────────────┐
                       │                                         │
                       ▼                                         ▼
┌──────────────────────────────┐   ┌──────────────────────────────┐
│ Shared Configuration        │   │ Unified Tag Emission        │
│ - cognitive_frameworks      │   │ - [COG] for frameworks      │
│ - reasoning_modes           │   │ - [SEQ/MAS/2ST] for modes   │
│ - think_profiles            │   │ - [THINK] for profiles      │
│ - questioning_patterns      │   │ - [SYNERGY] for combos      │
│ - performance_thresholds    │   │ - [PERF] for timing data     │
└──────────────────────────────┘   └──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Enhanced Conflict Arbiter                                   │
│ - Original 3 rules (fast mode, high-confidence, token)      │
│ - NEW: Synergy override (prefer complementary combos)        │
│ - NEW: Questioning pattern injection                        │
│ - NEW: Performance budget enforcement                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ HookResult Output                                           │
│ - systemContext: AI instructions                            │
│ - additionalContext: User-facing tags + rationale            │
└─────────────────────────────────────────────────────────────┘
```

**Why This Approach**:

1. **Performance**: Single-pass detection eliminates 30% overhead
2. **Maintainability**: Shared config reduces duplication
3. **Synergy**: Awareness between systems improves selection
4. **Observability**: Unified tags make debugging easier
5. **Evidence-based**: Questioning patterns prevent reasoning flaws
6. **Measurable**: Built-in performance monitoring

**Alternatives Considered**:

- **Option B**: Keep systems separate, add caching (65% confidence)
  - Pros: Less invasive, lower risk
  - Cons: Still 3x pattern matching, no synergy detection, higher maintenance

- **Option C**: Full rewrite as single system (45% confidence)
  - Pros: Cleanest architecture
  - Cons: High risk, breaking changes, difficult to test incrementally

---

## Implementation Plan

### Phase 0: Performance Baseline (NEW - T-000)

**TASK-000**: Measure current hook performance baseline
- **File**: `P:/.claude/hooks/baselines/current_performance_baseline.json` (NEW)
- **Action**: Measure actual latency before optimization
  - Instrument current cognitive_enhancers.py with timing
  - Instrument current reasoning_mode_selector.py with timing
  - Instrument current think_trigger.py with timing
  - Measure 1000 random UserPromptSubmit events
  - Calculate p50, p95, p99 latencies
  - Document current duplicate pattern matching overhead
- **Acceptance**:
  - Baseline JSON with actual measurements (not estimates)
  - SLOs based on data (not arbitrary "<100ms")
  - Regression test threshold: baseline + 20%
- **Prerequisites**: None
- **Effort**: M (2-3h)
- **Rationale**: Addresses adversarial finding AQ-003 - arbitrary thresholds without measurement

### Phase 1: Foundation (T-001 through T-004)

**TASK-001**: Create unified detection engine module
- **File**: `UserPromptSubmit_modules/unified_detection.py` (NEW)
- **Action**: Implement single-pass pattern matching
  - Compile all regex patterns once at module load
  - Extract strong keywords, weak keywords, intent signals
  - Return `UnifiedDetectionResult` dataclass with:
    - `matched_frameworks: list[str]`
    - `matched_modes: list[str]`
    - `matched_profiles: list[str]`
    - `intent_classification: str | None`
    - `synergy_candidates: list[tuple[str, str]]`  # (framework, mode) pairs
    - `questioning_patterns: list[str]`
    - `timing_ms: float`
- **Acceptance**:
  - Single regex compilation pass (verify with module load test)
  - Timing <60ms for 1000-character prompt
  - All existing patterns still match (regression test)
- **Prerequisites**: None
- **Effort**: L (3-5h)

**TASK-002**: Create shared configuration system
- **File**: `P:/.claude/hooks/cognitive_reasoning_config.json` (NEW)
- **Action**: Consolidate all configuration
  - Migrate `cognitive_enhancers_config.json` settings
  - Add reasoning mode thresholds (confidence_min, etc.)
  - Add think_trigger settings (strong_count, weak_count)
  - Add questioning patterns integration (enabled/disabled)
  - Add performance thresholds (max_detection_ms, etc.)
- **Acceptance**:
  - Single source of truth for all 3 systems
  - JSON schema validation
  - Migration script from old config
- **Prerequisites**: None
- **Effort**: M (2-3h)

**TASK-003**: Implement unified tag emission standard
- **File**: `UserPromptSubmit_modules/tag_emission.py` (NEW)
- **Action**: Standardize all tag formats
  - `[COG]` for cognitive frameworks (existing, keep)
  - `[SEQ]`, `[MAS]`, `[2ST]` for reasoning modes (existing, keep)
  - `[THINK]` for think profiles (NEW)
  - `[SYNERGY]` for framework+mode combinations (NEW)
  - `[PERF]` for performance timing data (NEW)
  - `[QUESTIONING]` for questioning pattern matches (NEW)
- **Acceptance**:
  - All tags documented in function docstring
  - Tag format validation (no spaces, consistent casing)
  - Tag emission in HookResult.additionalContext
- **Prerequisites**: T-001 (unified detection provides data)
- **Effort**: S (1-2h)

**TASK-004**: Add performance monitoring to unified detection
- **File**: `UserPromptSubmit_modules/performance_monitor.py` (NEW)
- **Action**: Implement timing and metrics
  - Wrap detection operations with timing
  - Log to `logs/diagnostics/performance.db` (SQLite)
  - Schema: `(timestamp, operation, duration_ms, prompt_length, matches)`
  - Add `--perf-stats` CLI flag for summary
- **Acceptance**:
  - <1ms overhead per measurement
  - SQLite logging fails gracefully
  - Stats queryable via CLI
- **Prerequisites**: T-001 (unified detection provides operations)
- **Effort**: M (2-3h)

### Phase 2: Integration (T-005 through T-008)

**TASK-005**: Integrate questioning_patterns.md into detection
- **File**: `UserPromptSubmit_modules/questioning_integration.py` (NEW)
- **Action**: Load and match questioning patterns
  - Parse `C:\Users\brsth\.claude\projects\P--\memory\questioning_patterns.md`
  - Extract 5 questioning patterns:
    - "Why this specific value?" (arbitrary threshold detection)
    - "Are you sure about concurrency?" (shared state detection)
    - "Is this necessary?" (over-engineering detection)
    - "What happens at scale?" (swiss cheese detection)
    - **"What does the error actually say?" (debugging cognition)** ← NEW from /arch analysis
  - **Debugging cognition patterns** (Pattern 5):
    - **H1: Entry Point First** - Run failing code directly before hypothesis generation
    - **H2: Parallel Diagnostics** - Test multiple hypotheses simultaneously
    - **H3: Meta-Cognitive Check** - "What's on the error stack vs. what's in my head?"
  - Match patterns in prompt text
  - Return matched pattern names with line references
- **Acceptance**:
  - Questioning patterns loaded from memory file (all 5 patterns)
  - Pattern matching <10ms overhead
  - References questioning_patterns.md in output
  - Debugging cognition patterns (H1/H2/H3) injected during error investigation
- **Prerequisites**: T-001 (unified detection framework)
- **Effort**: M (2-3h)
- **Rationale**: Extended to include debugging cognition patterns from /arch analysis (ARCH-001 through ARCH-005)

**TASK-006**: Implement synergy detection
- **File**: `UserPromptSubmit_modules/synergy_detector.py` (NEW)
- **Action**: Detect complementary framework+mode combinations
  - Define synergy matrix (framework × mode compatibility)
  - Example synergies:
    - `assumption_surfacing` + `sequential` → Surface assumptions before step-by-step
    - `socratic_decomposition` + `multi_agent` → Decompose for multiple perspectives
    - `inversion_prompting` + `two_stage` → Pre-mortem in reasoning phase
  - Detect when both matched
  - Score synergy strength (0-1.0)
- **Acceptance**:
  - Synergy matrix defined in config
  - Detection <5ms overhead
  - Top 3 synergies reported
- **Prerequisites**: T-001 (unified detection provides matches)
- **Effort**: M (2-3h)

**TASK-007**: Update cognitive_enhancers.py to use unified detection
- **File**: `UserPromptSubmit_modules/cognitive_enhancers.py` (MODIFY)
- **Action**: Replace internal pattern matching
  - Remove `_IMPL_RE`, `_DIAGNOSTIC_RE`, `_PLAN_RE` patterns
  - Call `unified_detection.detect()` instead
  - Use `UnifiedDetectionResult.matched_frameworks`
  - Keep enhancer injection logic unchanged
- **Acceptance**:
  - All 9 frameworks still detected (regression test)
  - No behavior changes except performance
  - Timing improved by ~30%
- **Prerequisites**: T-001, T-002 (unified detection + config)
- **Effort**: M (2-3h)

**TASK-008**: Update reasoning_mode_selector.py to use unified detection
- **File**: `UserPromptSubmit_modules/reasoning_mode_selector.py` (MODIFY)
- **Action**: Replace external call with unified detection
  - Remove call to `packages/reasoning/hooks/Start_reasoning_mode_selector.py`
  - Call `unified_detection.detect()` instead
  - Use `UnifiedDetectionResult.matched_modes`
  - Keep mode injection logic unchanged
- **Acceptance**:
  - All 4 modes still detected (regression test)
  - No behavior changes except performance
  - Integration with `packages/reasoning/` removed
- **Prerequisites**: T-001, T-002 (unified detection + config)
- **Effort**: M (2-3h)

### Phase 3: Enhanced Conflict Resolution (T-009 through T-011)

**TASK-009**: Extend conflict_arbiter.py with new rules
- **File**: `UserPromptSubmit_modules/conflict_arbiter.py` (MODIFY)
- **Action**: Add 3 new precedence rules
  - **Rule 4**: Synergy override
    - If framework+mode synergy detected (score >= 0.7), prefer combination
    - Override fast mode cap if synergy is high-value
  - **Rule 5**: Questioning pattern injection
    - If questioning pattern matched, inject relevant pattern context
    - Add to `systemContext` with pattern reference
  - **Rule 6**: Performance budget enforcement
    - If unified detection > `max_detection_ms` (from config), skip low-confidence matches
    - Preserve high-confidence matches (confidence >= 3)
- **Acceptance**:
  - All 6 rules documented in docstring
  - Rationale explains which rules fired and why
  - Regression test for original 3 rules
- **Prerequisites**: T-001, T-005, T-006 (unified detection + questioning + synergy)
- **Effort**: L (3-4h)

**TASK-010**: Update think_trigger.py to use unified detection
- **File**: `UserPromptSubmit_modules/think_trigger.py` (MODIFY)
- **Action**: Replace internal pattern matching
  - Remove strong/weak pattern definitions
  - Call `unified_detection.detect()` instead
  - Use `UnifiedDetectionResult.matched_profiles`
  - Add `[THINK]` tag emission via `tag_emission.py`
- **Acceptance**:
  - All 7 profiles still detected (regression test)
  - `[THINK]` tag now emitted
  - No behavior changes except performance + tags
- **Prerequisites**: T-001, T-002, T-003 (unified detection + config + tags)
- **Effort**: M (2-3h)

**TASK-011**: Update UserPromptSubmit_router.py orchestration
- **File**: `P:/.claude/hooks/UserPromptSubmit_router.py` (MODIFY)
- **Action**: Simplify router logic
  - Remove sequential calls to 3 systems
  - Single call to `unified_detection.detect()`
  - Pass result to all 3 systems (cognitive, reasoning, think)
  - Call `conflict_arbiter.resolve_conflict()` once
  - Combine HookResults from all systems
- **Acceptance**:
  - Single detection pass verified (timing logged)
  - All systems still produce output
  - Router logic simplified by ~40%
- **Prerequisites**: T-007, T-008, T-010 (all systems using unified detection)
- **Effort**: L (3-4h)

### Phase 4: Testing & Documentation (T-012 through T-015)

**TASK-012**: Write unified detection tests
- **File**: `tests/test_unified_detection.py` (NEW)
- **Action**: Comprehensive test coverage
  - **Tier 1 (Unit) tests**: Test pattern compilation, intent classification, synergy scoring
  - **Tier 2 (Integration) tests**: Test all 9 frameworks detection, all 4 modes detection, all 7 profiles detection
  - **Tier 3 (E2E) tests**: Test full UserPromptSubmit event flow
  - Test edge cases (empty prompt, very long prompt, Unicode)
  - Test performance (<60ms requirement based on T-000 baseline)
- **Acceptance**:
  - >90% code coverage (excluding Agent tool invocations - Tier 2 only)
  - Tier 1 tests pass in <2 seconds (pure logic, no external calls)
  - Tier 2 integration tests pass in <10 seconds
  - Performance test asserts improvement over T-000 baseline
- **Prerequisites**: T-000 (baseline), T-001, T-005, T-006 (unified detection + questioning + synergy)
- **Effort**: L (4-5h)
- **Rationale**: Addresses QA-001 - Tier 1 unit tests impossible for Agent tools, redefined as integration tests

**TASK-013**: Write integration tests for router orchestration
- **File**: `tests/integration/test_cognitive_reasoning_integration.py` (NEW)
- **Action**: End-to-end testing
  - Test UserPromptSubmit event flow
  - Test unified detection → systems → conflict arbiter
  - Test tag emission format
  - Test configuration loading
  - Test performance monitoring logging
  - Test questioning pattern injection
  - Test synergy override behavior
- **Acceptance**:
  - All 8 COG findings addressed
  - Router timing <80ms (unified detection 60ms + arbitration 20ms)
  - All tags emitted correctly
- **Prerequisites**: T-011 (router orchestration complete)
- **Effort**: L (4-5h)

**TASK-014**: Update CLAUDE.md with new architecture
- **File**: `P:/.claude/hooks/CLAUDE.md` (MODIFY)
- **Action**: Document new system
  - Add "Cognitive & Reasoning Systems" section
  - Document unified detection engine
  - Document shared configuration file
  - Document tag emission standard
  - Document questioning patterns integration
  - Document performance monitoring
  - Update observability section with new tags
- **Acceptance**:
  - All new components documented
  - Configuration examples provided
  - Tag reference table included
- **Prerequisites**: T-001 through T-011 (all implementation complete)
- **Effort**: M (2-3h)

**TASK-015**: Create migration guide and rollback plan
- **File**: `P:/.claude/hooks/docs/cognitive_reasoning_migration.md` (NEW)
- **Action**: Document migration process
  - Step-by-step migration from old to new
  - Config migration script
  - Verification steps (run tests, check logs)
  - Rollback procedure if issues found
  - Troubleshooting common issues
- **Acceptance**:
  - Migration tested in staging environment
  - Rollback verified (restore old files, revert config)
  - Zero-downtime migration documented
- **Prerequisites**: T-014 (documentation complete)
- **Effort**: S (1-2h)

**TASK-016**: Migrate existing verification state
- **File**: `P:/.claude/hooks/scripts/migrate_verification_state.py` (NEW)
- **Action**: Create migration script for existing state
  - Scan existing verification state JSON files
  - Convert to new unified schema (if format changed)
  - Create backup before migration
  - Validate migrated state integrity
  - Add compatibility window (support old format for 2 weeks)
- **Acceptance**:
  - Migration script tested on sample state files
  - Zero data loss (all records preserved)
  - Rollback script restores original state
  - Backups stored in `.claude/state/backups/`
- **Prerequisites**: T-002 (new config schema defined)
- **Effort**: M (2-3h)
- **Rationale**: Addresses AQ-005 - no migration strategy for existing verification state

**TASK-017**: Equivalence tests for refactoring correctness
- **File**: `tests/test_refactoring_equivalence.py` (NEW)
- **Action**: Verify behavior preservation during consolidation
  - Run old (cognitive_enhancers) and new (unified_detection) on same inputs
  - Assert equal matches for all 9 frameworks
  - Run old (reasoning_mode_selector) and new (unified_detection) on same inputs
  - Assert equal matches for all 4 modes
  - Run old (think_trigger) and new (unified_detection) on same inputs
  - Assert equal matches for all 7 profiles
  - Test 1000 random prompts from actual usage logs
- **Acceptance**:
  - 100% behavior equivalence (no regressions)
  - Test report shows side-by-side comparison
  - Any diffs flagged for manual review
- **Prerequisites**: T-007, T-008, T-010 (all systems using unified detection)
- **Effort**: L (3-4h)
- **Rationale**: Addresses TEST-009 - refactoring correctness not verified

**TASK-018**: Add cache invalidation for config hot-reload
- **File**: `UserPromptSubmit_modules/config_cache.py` (MODIFY - part of unified_detection.py)
- **Action**: Implement TTL-based cache refresh
  - Add `config_last_checked` timestamp to in-memory cache
  - Add 60-second TTL for config cache
  - On cache miss, check if file mtime changed
  - If changed, reload config and invalidate dependent caches
  - Add `--reload-config` flag for manual refresh
- **Acceptance**:
  - Config changes propagate within 60 seconds
  - No stale config after manual reload
  - Cache invalidation logged to diagnostics
- **Prerequisites**: T-002 (shared config system)
- **Effort**: M (2-3h)
- **Rationale**: Addresses HIGH-002 - config hot-reload race condition

**TASK-019**: Add database index for terminal_id performance
- **File**: `P:/.claude/hooks/__lib/evidence_store.py` (MODIFY)
- **Action**: Add composite index for evidence queries
  - Add index on `(session_id, terminal_id, timestamp)` columns
  - Verify index usage with EXPLAIN QUERY PLAN
  - Benchmark before/after query performance (target: <10ms)
  - Add migration script to create index in existing DBs
- **Acceptance**:
  - Terminal ID queries <10ms (down from 10-100ms)
  - Index created in all existing databases
  - No performance regression on INSERT operations
- **Prerequisites**: T-004 (performance monitoring infrastructure)
- **Effort**: M (2-3h)
- **Rationale**: Addresses PERF-004 - slow terminal ID queries

---

## Risks, Success Criteria, Dependencies

### Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Performance regression** | Medium (30%) | High | Phase 1 includes performance tests; T-004 adds monitoring |
| **Breaking existing behavior** | Low (15%) | High | T-007, T-008, T-010 require regression tests; feature flag for gradual rollout |
| **Configuration migration errors** | Low (20%) | Medium | T-002 includes migration script; T-015 documents rollback |
| **Synergy detection false positives** | Medium (40%) | Low | Configurable thresholds; can disable if not effective |
| **Questioning patterns too noisy** | Medium (35%) | Medium | Configurable enable/disable; only inject on high-confidence matches |

### Success Criteria

**Must Have** (all required for success):
- ✅ Unified detection engine <60ms per UserPromptSubmit event
- ✅ All 9 frameworks, 4 modes, 7 profiles still detected (regression tests pass)
- ✅ Shared configuration file consolidates all settings
- ✅ Unified tag emission standard ([COG], [SEQ/MAS/2ST], [THINK], [SYNERGY], [PERF], [QUESTIONING])
- ✅ Questioning patterns from memory integrated into detection (all 5 patterns including debugging cognition)
- ✅ Debugging cognition patterns (H1/H2/H3) injected during error investigation (COG-009)
- ✅ Synergy detection identifies top 3 complementary combinations
- ✅ Performance monitoring logs to SQLite database
- ✅ Zero behavior changes (except performance improvements and new tags)

**Should Have** (important but not blocking):
- ✅ Conflict arbiter extended with 3 new rules (synergy, questioning, performance)
- ✅ Router orchestration simplified by ~40%
- ✅ Migration guide with rollback plan
- ✅ CLAUDE.md updated with new architecture

**Nice to Have** (enhancements):
- ✅ Think trigger integration with plan-workflow (COG-008)
- ✅ Performance baseline dashboard (queries SQLite DB)
- ✅ A/B testing framework for detection improvements

### Dependencies

**Blockers** (must be unblocked before starting):
- None

**Required** (needed for implementation):
- `C:\Users\brsth\.claude\projects\P--\memory\questioning_patterns.md` exists ✅
- `packages/reasoning/hooks/Start_reasoning_mode_selector.py` accessible ✅
- Python 3.12+ dataclass support ✅
- SQLite for performance monitoring ✅

**Optional** (nice to have but not required):
- Performance profiling tools (e.g., `py-spy`) for deeper analysis
- A/B testing framework for comparing old vs new detection

### Rollback Strategy

If critical issues found after deployment:

1. **Immediate rollback** (<5 minutes):
   - Restore old files from git:
     - `UserPromptSubmit_modules/cognitive_enhancers.py`
     - `UserPromptSubmit_modules/reasoning_mode_selector.py`
     - `UserPromptSubmit_modules/think_trigger.py`
     - `UserPromptSubmit_router.py`
   - Restore old config: `cognitive_enhancers_config.json`
   - Delete new config: `cognitive_reasoning_config.json`
   - Restart Claude Code session

2. **Verification**:
   - Run regression tests: `pytest tests/test_cognitive_enhancers.py tests/test_reasoning_mode_selector.py tests/test_think_trigger.py`
   - Check tags: `[COG]`, `[SEQ]`, `[MAS]`, `[2ST]` present
   - No new tags: `[THINK]`, `[SYNERGY]`, `[PERF]`, `[QUESTIONING]`

3. **Post-mortem**:
   - Analyze logs in `logs/diagnostics/performance.db`
   - Identify root cause (performance regression? breaking change?)
   - Create fix and re-test in staging

---

## Appendix: Task Summary

### Task Breakdown

| ID | Task | Effort | Priority | Dependencies |
|----|------|--------|----------|--------------|
| T-000 | Measure performance baseline | M (2-3h) | HIGH | None |
| T-001 | Create unified detection engine | L (3-5h) | HIGH | T-000 |
| T-002 | Create shared configuration system | M (2-3h) | HIGH | T-000 |
| T-003 | Implement unified tag emission standard | S (1-2h) | HIGH | T-001 |
| T-004 | Add performance monitoring | M (2-3h) | MEDIUM | T-001 |
| T-005 | Integrate questioning patterns | M (2-3h) | MEDIUM | T-001 |
| T-006 | Implement synergy detection | M (2-3h) | MEDIUM | T-001 |
| T-007 | Update cognitive_enhancers.py | M (2-3h) | HIGH | T-001, T-002 |
| T-008 | Update reasoning_mode_selector.py | M (2-3h) | HIGH | T-001, T-002 |
| T-009 | Extend conflict_arbiter.py | L (3-4h) | MEDIUM | T-001, T-005, T-006 |
| T-010 | Update think_trigger.py | M (2-3h) | HIGH | T-001, T-002, T-003 |
| T-011 | Update UserPromptSubmit_router.py | L (3-4h) | HIGH | T-007, T-008, T-010 |
| T-012 | Write unified detection tests | L (4-5h) | HIGH | T-000, T-001, T-005, T-006 |
| T-013 | Write integration tests | L (4-5h) | HIGH | T-011 |
| T-014 | Update CLAUDE.md | M (2-3h) | MEDIUM | T-001 through T-011 |
| T-015 | Create migration guide | S (1-2h) | LOW | T-014 |
| T-016 | Migrate verification state | M (2-3h) | HIGH | T-002 |
| T-017 | Equivalence tests for refactoring | L (3-4h) | HIGH | T-007, T-008, T-010 |
| T-018 | Config cache invalidation | M (2-3h) | HIGH | T-002 |
| T-019 | Database index for terminal_id | M (2-3h) | HIGH | T-004 |

**Total Effort**: ~49-67 hours (6.1-8.4 working days)
**Original Plan**: ~38-51 hours
**Added**: +11-16 hours for adversarial review improvements (+28% effort)

### Critical Path

```
T-000 (baseline) → T-001 (unified detection) → T-003 (tags) → T-010 (think_trigger) → T-011 (router) → T-013 (integration tests)
                                    → T-007 (cognitive) ↗
                                    → T-008 (reasoning) ↗
```

**Parallel Opportunities**:
- T-002 (config) can run parallel to T-000
- T-004 (perf), T-005 (questioning), T-006 (synergy) can run parallel after T-001
- T-009 (conflict arbiter) can run parallel to T-007, T-008, T-010
- T-012 (unit tests) can run parallel to T-011
- T-014 (docs), T-015 (migration guide), T-016 (migration), T-017 (equivalence), T-018 (cache), T-019 (index) can run parallel after T-011

**Minimum Viable Implementation** (MVP):
- T-000, T-001, T-002, T-003, T-005, T-007, T-008, T-010, T-011
- Addresses COG-001 (unified detection), COG-002 (tags), COG-004 (questioning patterns), COG-005 (shared config), COG-009 (debugging cognition)
- Addresses adversarial findings: baseline measurement, equivalence tests
- Effort: ~22-30 hours (2.8-3.8 working days)

**Full Implementation** (all 20 tasks):
- Addresses all 9 COG findings (including COG-009 debugging cognition)
- Addresses all adversarial review findings (baseline, migration, equivalence, performance, cache)
- Effort: ~49-67 hours (6.1-8.4 working days)

---

**Plan Version**: 1.2 (ENHANCED - Debugging Cognition Integration)
**Last Updated**: 2026-03-14
**Status**: READY-FOR-IMPLEMENTATION
**Improvements Applied**: 12 items (8 HIGH + 4 MEDIUM) + Debugging cognition integration (H1/H2/H3)
