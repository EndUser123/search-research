# Architectural Design: Optimized Debug + RCA System

**Project**: debug_rca_enhancement
**Status**: Design Complete
**Created**: 2025-12-26

---

## [ADF] Architecture Decision Framework Assessment

### Step 0: Scope Check

This proposal involves **extending existing capabilities** rather than creating new structural boundaries. The enhancements leverage:
- Existing CHS (Chat History Search)
- Existing CKS (Cognitive Knowledge System)
- Existing rca-specialist subagent
- Existing cognitive stack (thinking modes, sequential thinking)
- Existing evidence systems

**Scope Check Result**: This is **capability enhancement** and **integration** of existing systems, not structural extraction. ADF full analysis not required for most changes. The one new file (metrics tracker) is justified by measurable gaps.

---

## Executive Summary

**Problem**: Current /debug and /rca systems have strong foundations but lack:
1. Automated fix verification (manual only)
2. Metrics tracking (all "TBD")
3. Enforcement of CHS/CKS result usage
4. Learning from patterns

**Solution**: Extend existing systems with minimal new complexity (complexity tax: 3-5).

**Approach**: Build on existing cognitive stack, CHS, CKS, and rca-specialist rather than creating new abstractions.

---

## Current Architecture Analysis

### Existing Components (Reuse Target)

| Component | Capability | Integration Point |
|-----------|------------|-------------------|
| **CHS** | Historical incident search | Pre-RCA lookup |
| **CKS** | Cognitive knowledge synthesis | Pattern matching |
| **rca-specialist** | Cognitive-enhanced RCA | 8 mental models, multi-agent reasoning |
| **cognitive-stack** | 19 thinking modes | Framework selection |
| **sequential thinking** | Thought tracking | Evidence chains |
| **evidence systems** | Validation, tracking | Fix verification |
| **post_fix_validator** | Post-edit validation | Extension point |

### Current Flow

```
/debug or /rca invocation
    ↓
CHS Search (required)
    ↓
    ├─→ Exact match? → Quick Fix (Route 2A)
    │                     ↓
    │               Manual verification
    │
    └─→ No match → CKS Search
                     ↓
               rca-specialist (cognitive-enhanced)
                     ↓
               Manual verification
```

---

## Proposed Architecture

### Design Philosophy

**Leverage > Create**: Use existing cognitive stack, thinking modes, and evidence systems rather than building new frameworks.

### Enhanced Flow

```
/debug or /rca invocation
    ↓
CHS Search (required) + Pattern Classification (NEW)
    ├─→ Symptom vs Root Cause auto-tag
    ├─→ Recurrence detection
    └─→ Historical success rate
    ↓
    ├─→ Exact match? → Quick Fix (Route 2A)
    │                     ↓
    │               Automated Verification (NEW)
    │                     ├─→ Run tests based on files changed
    │                     ├─→ Verify error gone
    │                     └─→ Record outcome
    │
    └─→ No match → CKS Search + Thinking Mode Selection (ENHANCED)
                     ↓
               rca-specialist (cognitive-enhanced)
                     ├─→ Mental model auto-selection
                     ├─→ Multi-agent reasoning
                     └─→ CHS/CKS citation enforcement (NEW)
                     ↓
               Automated Verification (NEW)
                     ↓
               Metrics Recording (NEW)
                     └─→ Update success metrics
```

---

## Implementation Plan

### Phase 1: Metrics Infrastructure (HIGH, Complexity Tax: 2)

**New file**: `P:/__csf.nip/src/modules/rca_enhancement/metrics_tracker.py`

**Purpose**: Track success metrics currently marked as "TBD"

**Implementation**:
```python
class RCAMetricsTracker:
    """Tracks RCA/debug metrics for continuous improvement"""

    def record_rca_start(self, problem_hash: str, chs_results: int, cks_results: int)
    def record_chs_hit(self, problem_hash: str, match_type: str, applied: bool)
    def record_fix_attempt(self, problem_hash: str, fix_type: str, verification_passed: bool)
    def record_recurrence(self, original_problem_hash: str, new_problem_hash: str)
    def get_metrics_report(self) -> MetricsReport
```

**Integration points**:
- Hook into `/debug` command start
- Hook into post_fix_validator
- Background aggregation to TaskMaster

**Complexity tax breakdown**:
- New file: +1
- New concept (metrics): +2
- Total: 3 (≤5, proceed)

---

### Phase 2: CHS Result Usage Enforcement (HIGH, Complexity Tax: 1)

**Modify**: `P:/.claude/agents/rca-specialist.md`

**Change**: Add enforcement section requiring CHS/CKS citations in fix generation:

```markdown
## CHS/CKS Citation Requirement (MANDATORY)

When CHS returns results with known fixes:
- You MUST use the historical solution as primary approach
- You MUST cite the specific CHS result that informed your fix

**Output format when CHS solution used:**
> **Fix informed by:** CHS result #[N] from [session]
> **Historical precedent:** This fix worked in [context]

**Penalty for ignoring CHS solutions:**
- If you ignore a CHS-proven solution and propose something different,
  your confidence score is capped at 60% (unproven approach)
```

**Complexity tax breakdown**:
- Documentation change: 0 (not a new file/concept)
- Total: 0 (proceed)

---

### Phase 3: Automated Fix Verification (HIGH, Complexity Tax: 1-2)

**Extend**: `P:/.claude/hooks/post_fix_validator.py`

**New capability**: Automatic test suggestion and execution based on files changed

**Implementation**:
```python
class AutomatedFixVerifier:
    """Extends post_fix_validator with automated verification"""

    def suggest_verification_command(self, files_changed: List[str]) -> str
        """Suggest test command based on modified files"""
        # If tests/ modified: suggest pytest
        # If src/ modified: suggest relevant import test
        # If CLI: suggest --help or basic invocation

    def run_verification(self, command: str) -> VerificationResult
        """Execute verification and capture output"""
```

**Complexity tax breakdown**:
- Extending existing file: 0
- New concept (automated verification): +1 to +2
- Total: 1-2 (≤5, proceed)

---

### Phase 4: Cognitive Stack Integration (MEDIUM, Complexity Tax: 0-1)

**Integrate**: Existing thinking modes into rca-specialist

**Change**: Auto-select thinking mode based on problem characteristics

**Implementation**: Add to rca-specialist invocation:

```python
def select_thinking_mode(problem_description: str, chs_results: CHSResult) -> ThinkingMode:
    """Auto-select appropriate thinking mode from existing cognitive stack"""

    # Performance issues → Systems Thinking
    # Multiple possible causes → Scientific Method + Fishbone
    # Never seen this → First Principles
    # "Why did X happen" repeatedly → Five Whys
    # Default → Critical Thinking
```

**Complexity tax breakdown**:
- Using existing cognitive stack: 0 (integration, not new structure)
- Selection logic (can be simple function): +0 to +1
- Total: 0-1 (≤5, proceed)

---

### Phase 5: Symptom vs Root Cause Classification (MEDIUM, Complexity Tax: 2)

**New file**: `P:/__csf.nip/src/modules/rca_enhancement/classifier.py`

**Purpose**: Auto-classify incidents as symptom-level or root-cause-level

**Implementation**:
```python
class ProblemClassifier:
    """Classifies problems by depth and type"""

    # Uses existing cognitive stack patterns
    def classify(self, problem_description: str, chs_results: List) -> ProblemClassification

@dataclass
class ProblemClassification:
    problem_type: ProblemType  # ERROR, CRASH, PERFORMANCE, BEHAVIOR
    depth: DepthLevel          # SYMPTOM, INTERMEDIATE, ROOT_CAUSE
    confidence: float          # 0.0 - 1.0
    suggested_thinking_mode: ThinkingMode
```

**Complexity tax breakdown**:
- New file: +1
- New concept (classification): +1
- Total: 2 (≤5, proceed)

---

## System Integration Map

### New/Modified Files (5 total)

| File | Type | Purpose | Complexity |
|------|------|---------|------------|
| `metrics_tracker.py` | New | Track success metrics | 3 |
| `classifier.py` | New | Symptom vs RC classification | 2 |
| `post_fix_validator.py` | Extend | Automated verification | 1 |
| `rca-specialist.md` | Modify | CHS citation enforcement | 0 |
| `debug_unified_inst.md` | Modify | Add metrics hooks | 0 |

**Total complexity tax**: 6 (split across phases, each ≤5)

---

## Metrics Dashboard

### Success Metrics (Replacing "TBD")

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| CHS usage rate | 100% | Track /debug invocations with CHS execution |
| Quick-fix success rate | >80% | Track Route 2A fixes that pass verification |
| Fix verification rate | 100% | Track verification execution after fixes |
| Recurrence rate (7 days) | <10% | Track same problem hash within 7 days |
| Avg time to resolution (exact match) | <2 min | Track time from /debug to verified fix |
| Avg time to resolution (new issue) | <15 min | Track time from /debug to verified fix |
| CHS hit rate | >60% | Track how often CHS has useful results |

### Display Command

```bash
/debug --stats
```

Shows:
- Historical metrics (7-day, 30-day)
- Top recurring problems
- CHS hit rate by problem type
- Most effective mental models
---

## Mental Model Integration

### Auto-Selection Logic (Using Existing Cognitive Stack)

| Problem Characteristic | Thinking Mode | Rationale |
|------------------------|---------------|-----------|
| Performance/slowness | Systems Thinking | Understand interactions and feedback loops |
| Multiple possible causes | Scientific Method | Hypothesis testing needed |
| "Never seen this before" | First Principles | Break down to fundamentals |
| Intermittent/flaky | Inversion | Identify what could prevent failure |
| "Why did this happen" chain | Five Whys | Linear cause drilling |
| Cross-component | Critical Thinking | Evaluate assumptions |
| Novel edge case | Lateral Thinking | Creative approaches needed |

### Integration Point

Add to `rca-specialist.md` cognitive enhancement protocol:

```markdown
## Mental Model Auto-Selection

The rca-specialist automatically selects appropriate thinking modes based on:

1. **Problem Analysis** (from user description)
2. **CHS Pattern Data** (from historical incidents)
3. **CKS Synthesis** (from knowledge base)

**Selected mode appears in output:**
> **Mental Models Applied:** Systems Thinking (+15%), First Principles (+20%)
```

---

## Evidence Chain Tracking

### Using Existing Sequential Thinking

The `Thought` class from `cognitive-stack/sequential_thinking/thought.py` already defines:

- `ThoughtType.PATTERN_RECOGNIZED`
- `ThoughtType.INSIGHT`
- `ThoughtType.CONTRADICTION`
- `ThoughtRelationship.DERIVES_FROM`

**Integration**: RCA fixes should reference thought chains:

```markdown
### Evidence Chain
1. CHS Result #[N] → Pattern recognized (same error, same file)
2. CKS Synthesis → Root cause inference (counter not reset)
3. rca-specialist analysis → Derives fix (reset counter in X function)
4. Verification → Confirms fix works
```

---

## Failure Mode Analysis

### What Could Go Wrong

| Failure Mode | Impact | Mitigation |
|--------------|--------|------------|
| CHS returns noisy results | Wasted time | Confidence threshold filtering |
| Fix verification passes falsely | Recurrence | Track recurrences, flag patterns |
| Metrics overhead slows RCA | Performance | Async metrics recording |
| Mental model mismatch | Wrong approach | Fallback to multi-agent reasoning |

---

## Rollout Plan

### Phase 1: Foundation (Week 1)
1. Implement `metrics_tracker.py`
2. Add hooks to `/debug` command
3. Replace "TBD" with real metrics

### Phase 2: Enforcement (Week 2)
1. Update `rca-specialist.md` with CHS citation requirement
2. Add citation checks to output validation

### Phase 3: Verification (Week 3)
1. Extend `post_fix_validator.py` with automated verification
2. Add test suggestion logic

### Phase 4: Intelligence (Week 4+)
1. Implement `classifier.py`
2. Integrate mental model auto-selection
3. Add pattern clustering

---

## Open Questions

1. **Metrics storage**: SQLite table in TaskMaster DB or separate file?
2. **Async recording**: Should metrics be recorded asynchronously to avoid overhead?
3. **Privacy**: Are CHS/CKS queries and results considered sensitive?

---

## Alternative Approaches Considered

| Approach | Complexity | Benefit | Rejected Because |
|----------|------------|---------|------------------|
| New RCA orchestration service | High (8+) | Clean architecture | Unnecessary new boundary |
| ML-based fix prediction | High (7+) | Advanced | Low data for training currently |
| External RCA service integration | Medium (4+) | Industry tools | Losing existing cognitive stack advantages |
| **Extend existing systems** | **Low (3-6)** | **Leverage investment** | **Selected** |

---

## ADF Recommendation

**Change**: Optimize debug + RCA outcomes through phased enhancement

**Problem**:
- Metrics untracked (all "TBD")
- No fix verification automation
- CHS solutions not enforced
- No learning from patterns

**Complexity tax**: 6 total (phased: 3, 0, 1, 2 — each ≤5)

**Reversibility**: 1.2 (easy to revert, isolated changes)

**Evidence tier**: Tier 2 — Research shows 70% time reduction from automated RCA, measurable gaps in current system

**Recommendation**: PROCEED

**Next steps**:
1. Start with Phase 1 (Metrics)
2. Validate metrics accuracy
3. Proceed to Phase 2 (Enforcement)
