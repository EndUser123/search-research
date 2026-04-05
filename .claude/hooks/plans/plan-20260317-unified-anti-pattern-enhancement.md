# Unified Anti-Pattern Detection Enhancement Plan

**Source:** Analysis of 100+ chat history files (2026-03-16)
**Purpose:** Enhance 4 skills to detect LLM anti-patterns and improve investigation methodology

---

## Status Summary

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: /plan-workflow | ⏳ PENDING | Plan Assumption Gate, speculation detection |
| Phase 2: /verify | ⏳ PENDING | Verification Claim Evidence, false positive handling |
| Phase 3: /arch | ⏳ PENDING | Architectural Hypothesis Validation, evidence requirements |
| Phase 4: /refactor | ⏳ PENDING | Evidence-based refactoring claims, thrashing detection |
| Phase 5: Testing | ⏳ PENDING | Cross-skill integration tests |
| Phase 6: Documentation | ⏳ PENDING | Update SKILL.md files |

---

## Problem Statement

Analysis of 100+ chat history files reveals 7 major LLM behavior patterns that cause failures across multiple skills, not just /debugRCA:

### The 7 Anti-Patterns (Universal)

1. **Hypothesis-as-Fact** - Treating unverified hypotheses as established facts
   - *Example*: "The issue is the cache invalidation" without evidence
   - *Applies to*: /plan-workflow (assumptions), /verify (claims), /arch (decisions), /refactor (change rationale)

2. **Format Non-Compliance Loop** - Repeatedly ignoring documented output formats
   - *Example*: Skipping Status Summary after explicit requirement
   - *Applies to*: /plan-workflow (output format), /verify (verification output)

3. **Speculation Without Evidence** - Making claims with "probably", "likely", "might be"
   - *Example*: "This is probably caused by..." without verification
   - *Applies to*: ALL SKILLS - universal pattern

4. **Thrashing** - 3+ fix attempts in different files, each revealing new problems
   - *Example*: Fix A → new bug B → fix B → new bug C (infinite loop)
   - *Applies to*: /refactor (multi-file changes), /debugRCA (already has detection)

5. **Context Transfer Failure** - State corruption between sessions/terminals
   - *Example*: After compaction, LLM forgets task and starts new investigation
   - *Applies to*: ALL SKILLS - multi-terminal safety

6. **False Positive Cascade** - Verification systems triggering incorrectly
   - *Example*: Evidence gate blocking legitimate work
   - *Applies to*: /verify (evidence gates), /plan-workflow (adversarial review)

7. **Context Bloat** - Performance degradation from excessive context
   - *Example*: SKILL.md files exceeding 50KB
   - *Applies to*: ALL SKILLS - documentation hygiene

### Impact by Skill

| Skill | Anti-Patterns Most Relevant | Current Protection |
|-------|---------------------------|-------------------|
| /plan-workflow | Hypothesis-as-Fact, Speculation, Format Non-Compliance | Partial (adversarial review) |
| /verify | Hypothesis-as-Fact, False Positive Cascade, Speculation | Minimal |
| /arch | Hypothesis-as-Fact, Speculation, Thrashing | Minimal |
| /refactor | Thrashing, Speculation, Context Transfer Failure | Partial (constitutional filter) |
| /debugRCA | All 7 | COMPLETE (Phase 0/1 done) |
| /handoff | Context Transfer Failure | NEW (TASK-504) |
| /reflect | Speculation Without Evidence | NEW (TASK-505) |
| /adversarial-review | Hypothesis-as-Fact, Evidence Tiers | NEW (TASK-506) |

---

## Context Analysis

### Existing Implementations

**debugRCA (Reference Implementation):**
- Red Flag Detection (lines 168-183): Auto-detects anti-debugging behaviors
- ACH Methodology (lines 201-273): 6-category hypothesis generation
- Evidence Strength Classification (lines 250-261): Direct/Correlational/Testimonial/Absence
- Iron Law Enforcement (lines 151-166): NO FIXES WITHOUT ROOT CAUSE INVESTIGATION
- Circuit Breaker for evidence gates (plan-20260316-debugrca-enhancement.md)

**plan-workflow:**
- Multi-Agent Adversarial Review: Catches issues before implementation
- RTM Generation: Requirements traceability matrix
- Solo-Dev Constraints: Single-developer workflow enforcement

**verify:**
- 4-Tier Verification: Tier 0→1→2→3 progression
- TSR Calculation: Task Success Rate ≥95%
- Post-Hoc Mode: RTM validation after implementation

**arch:**
- GoT Integration: Graph-of-Thought node extraction
- Lean System Design: Value optimization, dependency pruning
- Multi-Terminal Lens: Constitutional compliance check

**refactor:**
- SoloDevConstitutionalFilter: Enterprise bloat prevention
- 7-Step Workflow: DISCOVER → DEDUPLICATE → PRIORITIZE → FILTER → RED → REFACTOR → REGRESSION

### Gaps Identified

1. **No unified speculation detection** - Each skill handles differently or not at all
2. **No cross-skill thrashing detection** - Only debugRCA has this
3. **No evidence tier validation** - debugRCA has it, others don't
4. **No circuit breaker pattern** - False positive cascades not handled
5. **No format compliance enforcement** - Skills trust LLM to follow format

---

## Existing Implementation Discovery

### Files Analyzed

| File | Purpose | Anti-Pattern Detection |
|------|---------|----------------------|
| `.claude/skills/debugRCA.md` | Root cause analysis | COMPLETE |
| `.claude/skills/verify/SKILL.md` | Verification workflow | MINIMAL |
| `.claude/skills/refactor/SKILL.md` | Refactoring workflow | PARTIAL |
| `.claude/skills/plan-workflow/SKILL.md` | Plan creation | PARTIAL |
| `.claude/skills/arch/SKILL.md` | Architecture decisions | MINIMAL |

### Chat History Evidence

| File | Anti-Pattern Demonstrated |
|------|--------------------------|
| `speculating without evidence.txt` | Speculation Without Evidence |
| `handoff and lazy problems3.txt` | Context Transfer Failure |
| `example of stupid*.txt` series | Hypothesis-as-Fact, Thrashing |

---

## Test Discovery

### Existing Tests

- `test_debugrca_enhancements.py` - 35 tests for debugRCA patterns
- `test_plan_visualizer.py` - RTM generation tests
- `test_adversarial_review.py` - 8-agent review tests

### Tests Needed

- Cross-skill anti-pattern detection tests
- Evidence tier validation tests per skill
- Format compliance tests per skill
- Circuit breaker integration tests

---

## Proposed Solution

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  ANTI-PATTERN DETECTOR                       │
│  (Shared utility for all skills - token efficient)          │
├─────────────────────────────────────────────────────────────┤
│  detect_hypothesis_as_fact(text) → bool                     │
│  detect_speculation(text) → list[speculation_phrases]       │
│  detect_thrashing(fix_history) → bool                       │
│  detect_format_non_compliance(output, template) → list      │
│  validate_evidence_tier(claim, evidence) → tier             │
│  circuit_breaker_check(gate_name, consecutive_fails) → bool │
│  [NEW] llm_verify_detection(text, pattern) → bool (opt)     │
└─────────────────────────────────────────────────────────────┘
          ↓           ↓           ↓           ↓
    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
    │  plan-  │ │ verify  │ │  arch   │ │refactor │
    │ workflow│ │         │ │         │ │         │
    └─────────┘ └─────────┘ └─────────┘ └─────────┘
          ↓           ↓           ↓           ↓
    ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
    │ handoff │ │ reflect │ │adversary│ │         │
    │ (NEW)   │ │ (NEW)   │ │  (NEW)  │ │         │
    └─────────┘ └─────────┘ └─────────┘ └─────────┘
```

### Design Principles

1. **Token Efficiency**: Detection patterns use regex, not LLM calls
2. **Graceful Degradation**: Detection failure doesn't block skill execution
3. **Progressive Disclosure**: Advanced patterns in separate file, not inline
4. **Cross-Skill Reuse**: Shared utility, skill-specific configuration
5. **Hybrid Detection (NEW)**: Regex-first with optional LLM verification for context awareness

### Hybrid Detection Configuration

**Purpose**: Resolve tension between regex efficiency and context-aware detection.

**Architecture Review Finding**: Regex patterns are fast but may miss context-dependent anti-patterns. LLM verification adds context awareness but increases latency.

**Solution**: Hybrid approach with configuration flag:

```python
# Environment configuration
ANTI_PATTERN_LLM_VERIFICATION = os.environ.get("ANTI_PATTERN_LLM_VERIFICATION", "false").lower() == "true"

# Detection flow
def detect_anti_pattern(text: str, pattern_type: str) -> DetectionResult:
    # Step 1: Fast regex check (always runs)
    regex_match = REGEX_PATTERNS[pattern_type].search(text)

    if not regex_match:
        return DetectionResult(match=False, confidence=1.0)

    # Step 2: Optional LLM verification (when enabled)
    if ANTI_PATTERN_LLM_VERIFICATION:
        llm_result = llm_verify_context(text, regex_match, pattern_type)
        return DetectionResult(
            match=llm_result.is_anti_pattern,
            confidence=llm_result.confidence,
            context=llm_result.reasoning
        )

    # Step 3: Return regex result (default)
    return DetectionResult(match=True, confidence=0.7, context=None)
```

**Configuration**:
- `ANTI_PATTERN_LLM_VERIFICATION=false` (default) - Regex-only detection
- `ANTI_PATTERN_LLM_VERIFICATION=true` - Enable LLM context verification

**When to enable LLM verification**:
- High-stakes claims (production deployment decisions)
- Complex multi-sentence reasoning
- Context-dependent patterns (sarcasm, technical jargon)

**Performance expectations**:
- Regex-only: <10ms per detection
- With LLM verification: 100-500ms per detection

---

## Implementation Plan

### Phase 1: /plan-workflow Enhancements (P0)

**TASK-101**: Add Plan Assumption Gate
- **File**: `.claude/skills/plan-workflow/SKILL.md`
- **Action**: Add gate that checks for hypothesis-as-fact patterns in plan assumptions
- **Points**: 3
- **Acceptance**: Plans with unverified assumptions are flagged before implementation
- **Pattern**: "The solution is X" without evidence → Gate blocks with "Evidence required for claim"

**TASK-102**: Add Speculation Detection in Plans
- **File**: `.claude/skills/plan-workflow/SKILL.md`
- **Action**: Detect speculation phrases ("probably", "likely", "might be") in plan text
- **Points**: 2
- **Acceptance**: Speculation phrases trigger advisory warning (not blocking)
- **Pattern**: "This will probably work" → Warning: "Speculation detected. Consider: verify first"

**TASK-103**: Add Format Compliance Check
- **File**: `.claude/skills/plan-workflow/SKILL.md`
- **Action**: Verify Status Summary section present and complete
- **Points**: 2
- **Acceptance**: Plans without Status Summary are rejected
- **Prerequisites**: TASK-101

### Phase 2: /verify Enhancements (P1)

**TASK-201**: Add Verification Claim Evidence Gate
- **File**: `.claude/skills/verify/SKILL.md`
- **Action**: Require evidence tier for verification claims
- **Points**: 3
- **Acceptance**: Claims without evidence are flagged: "Claim requires Direct/Correlational/Testimonial evidence"
- **Evidence Tiers**: Direct (file:line) > Correlational (commit SHA) > Testimonial (source) > Absence (none found)

**TASK-202**: Add False Positive Cascade Protection (Circuit Breaker)
- **File**: `.claude/skills/verify/SKILL.md`, `.claude/skills/verify/core/verifier.py`
- **Action**: Implement circuit breaker with auto-suppression for evidence gates
- **Points**: 3
- **Acceptance**: After 3 consecutive false positives:
  1. Gate is temporarily disabled
  2. Suppression event logged
  3. User alerted once (not per-instance)
  4. Gate re-enabled after cooldown period
- **Configuration**:
  ```python
  VERIFY_CIRCUIT_BREAKER_THRESHOLD = 3
  VERIFY_CIRCUIT_BREAKER_COOLDOWN = 3600  # 1 hour
  ```
- **Architecture Review**: RISK:9-4 mitigation enhanced from tiered warnings to circuit breaker pattern (2026-03-17)

**TASK-203**: Add Speculation Detection in Verification
- **File**: `.claude/skills/verify/SKILL.md`
- **Action**: Detect speculation in verification output
- **Points**: 2
- **Acceptance**: "This appears to be correct" triggers: "Verify with evidence, not speculation"
- **Prerequisites**: TASK-201

### Phase 3: /arch Enhancements (P1)

**TASK-301**: Add Architectural Hypothesis Validation
- **File**: `.claude/skills/arch/SKILL.md`
- **Action**: Require evidence for architectural claims
- **Points**: 3
- **Acceptance**: "This is the best approach" requires: citation, precedent, or analysis evidence
- **Pattern**: Claim + "because [evidence]" required

**TASK-302**: Add Thrashing Detection for Design Iterations
- **File**: `.claude/skills/arch/SKILL.md`
- **Action**: Detect 3+ design iterations without convergence
- **Points**: 2
- **Acceptance**: After 3 iterations, prompt: "Consider: Is the problem well-defined?"
- **Prerequisites**: TASK-301

**TASK-303**: Add Speculation Detection in Architecture Output
- **File**: `.claude/skills/arch/SKILL.md`
- **Action**: Detect speculation in architecture recommendations
- **Points**: 2
- **Acceptance**: "This should work" triggers: "Verify with analysis, not speculation"

### Phase 4: /refactor Enhancements (P2)

**TASK-401**: Add Evidence-Based Refactoring Claims
- **File**: `.claude/skills/refactor/SKILL.md`
- **Action**: Require evidence for refactoring rationale
- **Points**: 3
- **Acceptance**: "This improves X" requires: measurement, citation, or analysis
- **Pattern**: "Refactor improves readability" → Evidence: "Cyclomatic complexity reduced from 15 to 8"

**TASK-402**: Add Thrashing Detection for Multi-File Refactors
- **File**: `.claude/skills/refactor/SKILL.md`
- **Action**: Detect 3+ files changed, each revealing new issues
- **Points**: 2
- **Acceptance**: Pattern triggers: "Consider: Is this a refactoring or a rewrite?"
- **Prerequisites**: TASK-401

**TASK-403**: Add Context Transfer Check
- **File**: `.claude/skills/refactor/SKILL.md`
- **Action**: Verify state persistence across refactor phases
- **Points**: 2
- **Acceptance**: After compaction, verify refactor state is recoverable
- **Prerequisites**: TASK-402

### Phase 5: Testing (P0 - Parallel with Implementation)

**TASK-501**: Write Cross-Skill Anti-Pattern Tests
- **File**: `.claude/hooks/tests/test_unified_anti_pattern.py`
- **Action**: Test all 7 anti-patterns across all 4 skills
- **Points**: 5
- **Acceptance**: 100% detection rate for known anti-patterns in test corpus

**TASK-502**: Write Evidence Tier Validation Tests
- **File**: `.claude/hooks/tests/test_evidence_tiers.py`
- **Action**: Test evidence tier classification for each skill
- **Points**: 3
- **Acceptance**: Correct tier assignment for Direct/Correlational/Testimonial/Absence evidence

**TASK-503**: Write Circuit Breaker Integration Tests
- **File**: `.claude/hooks/tests/test_circuit_breaker.py`
- **Action**: Test circuit breaker activation and recovery
- **Points**: 2
- **Acceptance**: Gate disables after 3 false positives, re-enables after cooldown

**TASK-504**: Add Handoff Context Transfer Validation
- **File**: `.claude/skills/handoff/SKILL.md`
- **Action**: Detect Context Transfer Failure in handoff restoration (anti-pattern #5)
- **Points**: 3
- **Acceptance**: After compaction, verify handoff state is recoverable and complete
- **Pattern**: Handoff internal state missing → Warning: "Context transfer incomplete, verify handoff_internal populated"

**TASK-505**: Add Reflect Speculation Detection
- **File**: `.claude/skills/reflect/SKILL.md`
- **Action**: Detect speculation without verification in pattern capture (anti-pattern #3)
- **Points**: 2
- **Acceptance**: Pattern capture claims require evidence tier validation
- **Pattern**: "Users often X" → Warning: "Provide evidence (chat history, metrics) for pattern claims"

**TASK-506**: Add Adversarial-Review Evidence Tier Validation
- **File**: `.claude/skills/adversarial-review/SKILL.md`
- **Action**: Validate evidence tiers for 8-agent findings (anti-pattern #1)
- **Points**: 3
- **Acceptance**: Adversarial findings include evidence tier (Direct/Correlational/Testimonial/Absence)
- **Pattern**: Finding without evidence tier → Warning: "Classify evidence quality for finding"

### Phase 6: Documentation (P1 - After Testing)

**TASK-007-DEF**: Context Bloat Detection (DEFERRED)
- **Status**: DEFERRED
- **Rationale**: Context bloat is addressed at the architecture level (progressive disclosure, separate reference files) rather than through per-skill detection tasks. The shared utility uses regex patterns (not LLM calls) to minimize token overhead. Future enhancement may add context budget monitoring.
- **Acceptance**: (Deferred - see rationale)

**TASK-601**: Update /plan-workflow SKILL.md
- **Action**: Add Anti-Pattern Detection section
- **Points**: 1
- **Acceptance**: Section documents all 7 patterns and detection approach
- **Prerequisites**: TASK-101, TASK-102, TASK-103

**TASK-602**: Update /verify SKILL.md
- **Action**: Add Evidence Tier Validation section
- **Points**: 1
- **Acceptance**: Section documents evidence tiers and circuit breaker
- **Prerequisites**: TASK-201, TASK-202, TASK-203

**TASK-603**: Update /arch SKILL.md
- **Action**: Add Hypothesis Validation section
- **Points**: 1
- **Acceptance**: Section documents evidence requirements for architectural claims
- **Prerequisites**: TASK-301, TASK-302, TASK-303

**TASK-604**: Update /refactor SKILL.md
- **Action**: Add Evidence-Based Refactoring section
- **Points**: 1
- **Acceptance**: Section documents evidence requirements for refactoring rationale
- **Prerequisites**: TASK-401, TASK-402, TASK-403

---

## Risks

| Risk | Mitigation |
|------|------------|
| Token overhead from detection patterns | Use regex, not LLM calls; progressive disclosure |
| False positive cascade in detection | Circuit breaker pattern (disable after 3, cooldown 1h) |
| Cross-skill inconsistency | Shared utility module, skill-specific config |
| Context bloat in SKILL.md files | Advanced patterns in separate reference files |
| Regression in existing functionality | Full test suite per skill before merge |
| Regex lacks context awareness | Hybrid detection with ANTI_PATTERN_LLM_VERIFICATION flag |
| LLM verification latency | Default to regex-only; LLM only when flag enabled |

---

## Success Criteria

- [ ] All 4 skills detect Hypothesis-as-Fact pattern
- [ ] All 4 skills detect Speculation Without Evidence pattern
- [ ] /verify has evidence tier validation with circuit breaker
- [ ] /plan-workflow has format compliance enforcement
- [ ] /arch has architectural hypothesis validation
- [ ] /refactor has evidence-based refactoring claims
- [ ] /handoff has context transfer validation (TASK-504)
- [ ] /reflect has speculation detection in pattern capture (TASK-505)
- [ ] /adversarial-review has evidence tier validation (TASK-506)
- [ ] 100% test pass rate for all anti-pattern tests
- [ ] No regression in existing skill tests
- [ ] Hybrid detection available via ANTI_PATTERN_LLM_VERIFICATION flag

---

## Dependencies

- **debugRCA Phase 0/1 COMPLETE** - Reference implementation exists
- **plan-workflow adversarial review** - Already has automated multi-perspective review
- **verify RTM generation** - Already has PlanVisualizer integration

---

## RTM (Requirements Traceability Matrix)

| Requirement | Tasks | Coverage |
|-------------|-------|----------|
| REQ-001: Hypothesis-as-Fact Detection | TASK-101, TASK-201, TASK-301, TASK-401, TASK-506 | 5 skills (plan, verify, arch, refactor, adversarial-review) |
| REQ-002: Format Non-Compliance Detection | TASK-103 | /plan-workflow |
| REQ-003: Speculation Detection | TASK-102, TASK-203, TASK-303, TASK-505 | 4 skills (plan, verify, arch, reflect) |
| REQ-004: Thrashing Detection | TASK-302, TASK-402 | /arch, /refactor |
| REQ-005: Evidence Tier Validation | TASK-201, TASK-301, TASK-401, TASK-502, TASK-506, TASK-602 | 4 skills + testing + docs |
| REQ-006: False Positive Cascade Protection | TASK-202, TASK-503 | /verify + testing (circuit breaker) |
| REQ-007: Context Bloat Detection | TASK-007-DEF | **DEFERRED** - See rationale below |
| REQ-008: Context Transfer Failure Detection | TASK-403, TASK-504 | /refactor, /handoff |
| REQ-009: Cross-Skill Testing | TASK-501, TASK-502, TASK-503 | All skills |
| REQ-010: Documentation Updates | TASK-601, TASK-602, TASK-603, TASK-604 | All skills |
| REQ-011: Hybrid Detection (Regex + LLM) | Architecture section | Config flag: ANTI_PATTERN_LLM_VERIFICATION |

**Coverage**: 11 requirements (10 active, 1 deferred), 23 tasks (22 active + 1 deferred) = 100% mapped

**REQ-007 DEFERRED Rationale**: Context bloat is addressed at the architecture level (progressive disclosure, separate reference files) rather than through per-skill detection tasks. The shared utility uses regex patterns (not LLM calls) to minimize token overhead. Future enhancement may add context budget monitoring.

---

## Changelog

### v1.1.0 (2026-03-17)
- **Architecture Review Enhancements** (from /arch evaluation):
  - RISK:9-4 mitigation upgraded: tiered warnings → circuit breaker with auto-suppression
  - Added hybrid detection configuration (ANTI_PATTERN_LLM_VERIFICATION flag)
  - Added 3 new skills to plan: /handoff (TASK-504), /reflect (TASK-505), /adversarial-review (TASK-506)
- **Updated RTM**: 11 requirements (10 active), 23 tasks (22 active)
- **Circuit Breaker Pattern**: After 3 consecutive false positives → disable, log, alert once, re-enable after cooldown

### v1.0.0 (2026-03-17)
- Initial unified enhancement plan
- 4 phases for 4 skills (/plan-workflow, /verify, /arch, /refactor)
- 20 tasks across 6 phases (19 active + 1 deferred)
- 10 requirements (9 active, 1 deferred) with 100% RTM coverage
