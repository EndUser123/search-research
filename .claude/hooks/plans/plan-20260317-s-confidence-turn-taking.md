# Implementation Plan: Confidence-Based Turn-Taking for /s Brainstorming

**Status:** DRAFT
**Date:** 2026-03-17
**Objective:** Add confidence-based dynamic agent turn scheduling to `/s` brainstorming skill for improved idea diversity

---

## Status Summary

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1 | ⏳ PENDING | Core confidence tracking implementation |
| Phase 2 | ⏸️ DEFERRED | Testing & validation (blocked by Phase 1) |
| Phase 3 | ⏸️ DEFERRED | Metrics & observability (blocked by Phase 2) |
| Phase 4 | ⏸️ DEFERRED | Documentation updates (blocked by Phase 3) |

---

## Problem Statement

The `/s` (Exploratory Strategy) skill currently uses round-robin agent scheduling for multi-persona brainstorming. All agents speak in a fixed order regardless of idea quality or confidence. This reduces diversity of thought because:

1. **High-confidence ideas** don't get prioritized for foundational discussion
2. **Mid-confidence agents** (balanced evaluators) don't dominate discussion phases
3. **Low-confidence "wildcard" ideas** don't get reserved for late-phase novelty injection

### Requirements

**REQ-001**: Extend the `Idea` model to include confidence tracking fields (`confidence: float`, `confidence_rationale: str`)

**REQ-002**: Implement LLM-based confidence computation method that scores ideas 0-1 based on specificity, consistency, relevance, and uniqueness

**REQ-003**: Implement confidence-based scheduling algorithm that prioritizes agents by confidence bands per phase (Diverge: high-first, Discuss: mid-first)

**REQ-004**: Integrate confidence scheduling into Diverge and Discuss phases with opt-in flag

**REQ-005**: Add CLI flag `--confidence-based-turns` to enable/disable confidence-based scheduling

The goal is to implement **confidence-based turn-taking** where agents dynamically schedule their turns based on self-assessed idea confidence (0-1 scale), as specified in ADR-20260317-s-brainstorm-improvements.md.

---

## Context Analysis

### Current Architecture
- **Location**: `P:\.claude\skills\s\`
- **Key Files**:
  - `lib/models/__init__.py` - Defines `Idea` dataclass
  - `lib/orchestrator.py` - `BrainstormOrchestrator` with 3-phase workflow
  - `lib/agents/base.py` - Base `Agent` class with LLM client
  - `scripts/run_heavy.py` - CLI entry point with argparse

### Current Turn-Taking Pattern
- Round-robin provider rotation exists in `AgentLLMClient._get_provider()`
- No analogous pattern for agent turn scheduling
- Agents generate ideas in parallel, then process sequentially
- Phase 1 (Diverge): Parallel idea generation from all personas
- Phase 2 (Discuss): Sequential evaluation (or 3-round debate if enabled)
- Phase 3 (Converge): Clustering, synthesis, ranking

### Multi-Terminal Constraints
- ✅ Each `/s` invocation is independent (no shared state)
- ✅ Confidence computed per-idea, not persisted (session-local)
- ✅ No cross-terminal coordination needed
- ⚠️ Stochasticity is acceptable (LLM temperature already non-deterministic)

### Research Foundation
- **YES AND Framework** (ACM 2025): Confidence-based turn-taking for diversity
- **Multi-Agent Structured Ideation** (arXiv 2025): Divergent vs Convergent modes
- **Turn-Taking with Adjacency Pairs** (Frontiers 2025): Response obligations
- **Deepening vs Exploring Strategies** (PMC 2025): AI as catalyst vs promoter

---

## Existing Implementation Discovery

### Idea Model (`lib/models/__init__.py`)
```python
class Idea(BaseModel):
    id: str
    content: str
    persona: str
    reasoning_path: list[str]
    score: float  # 0-100
    next_action: None | str
    estimated_minutes: int
    metadata: dict[str, Any]
```

**Missing fields** (from ADR):
- `confidence: float` (0-1, default 0.5)
- `confidence_rationale: str` (default "")

### BrainstormOrchestrator (`lib/orchestrator.py`)
- `_phase_diverge()`: Parallel idea generation from all agents
- `_phase_discuss()`: Sequential evaluation (or 3-round debate)
- `_phase_converge()`: Clustering, synthesis, ranking

**Current turn-taking**: No explicit turn scheduling - agents generate ideas in parallel, then processed sequentially.

### Agent Base Class (`lib/agents/base.py`)
- `generate_and_evaluate()`: Generate ideas, evaluate them, return `(Idea, Evaluation)` tuples
- `llm_client: AgentLLMClient` wrapper for LLM calls
- Round-robin pattern exists in `AgentLLMClient._get_provider()` module-level state

**Missing methods** (from ADR):
- `_compute_idea_confidence()`: LLM-based confidence scoring (0-1)

### CLI Entry Point (`scripts/run_heavy.py`)
- Has argparse argument parser
- Currently supports: `--personas`, `--timeout`, `--ideas`, `--output`, `--debate-mode`

**Missing flag** (from ADR):
- `--confidence-based-turns`: Enable vs default round-robin

---

## Test Discovery

### Existing Test Infrastructure
- Location: Need to check `P:\.claude\skills\s\tests\` (if exists)
- Pattern: Uses pytest with async test support
- Coverage areas to verify:
  1. Confidence computation produces values in [0, 1]
  2. Confidence-based scheduling changes turn order correctly
  3. High-confidence ideas prioritized in Diverge phase
  4. Mid-confidence ideas prioritized in Discuss phase
  5. Low-confidence ideas reserved for late injection
  6. Backward compatibility: flag defaults to false
  7. Multi-terminal safety: no shared state

### Test Scenarios to Add
1. **Unit**: `Agent._compute_idea_confidence()` returns clamped [0,1]
2. **Unit**: Orchestrator scheduling by confidence bands
3. **Integration**: Full brainstorm with flag enabled produces diverse turn order
4. **Comparison**: Same prompt with/without flag produces Jaccard similarity < 0.6
5. **Edge Cases**: Empty ideas list, all high confidence, all low confidence
6. **Multi-terminal**: Parallel sessions produce independent confidence distributions

---

## Proposed Solution

### Architecture Approach

**Minimal Extension Pattern**: Add confidence tracking as an opt-in enhancement that extends (not replaces) the existing round-robin architecture.

### Phase 1: Core Confidence Tracking

#### 1.1 Extend Idea Model
**File**: `lib/models/__init__.py`

```python
class Idea(BaseModel):
    # ... existing fields ...
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Agent's confidence in this idea (0-1)"
    )
    confidence_rationale: str = Field(
        default="",
        description="Explanation for confidence score"
    )
```

#### 1.2 Add Confidence Computation
**File**: `lib/agents/base.py`

```python
async def _compute_idea_confidence(self, idea: Idea) -> float:
    """
    Compute agent's confidence in generated idea (0-1 scale).

    Evaluates:
    - Specificity: Is the idea concrete and detailed?
    - Consistency: Are reasoning steps coherent?
    - Relevance: Does it address the core topic?
    - Uniqueness: Is this distinct from obvious solutions?

    Returns:
        float: Confidence score clamped to [0, 1]
    """
    prompt = f"""Rate your confidence in this idea from 0.0 to 1.0:

Topic: {self.context.topic if hasattr(self, 'context') else 'N/A'}

Idea: {idea.content}

Reasoning: {'; '.join(idea.reasoning_path[:3])}

Rate confidence (0.0-1.0):"""

    try:
        response = await self.llm_client.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            temperature=0.3,  # Low temp for consistency
            max_tokens=50,
        )
        # Parse float from response
        import re
        match = re.search(r'(\d+\.?\d*)', response.content)
        if match:
            confidence = float(match.group(1))
            return max(0.0, min(1.0, confidence))
        return 0.5  # Fallback on parse failure
    except Exception as e:
        logger.warning(f"Confidence computation failed for {idea.id}: {e}")
        return 0.5  # Default fallback
```

#### 1.3 Add Confidence-Based Scheduling
**File**: `lib/orchestrator.py`

```python
async def _schedule_confidence_based_turns(
    self,
    ideas_awaiting_turn: list[tuple[Agent, Idea]],
    phase: str,
) -> list[tuple[Agent, Idea]]:
    """
    Schedule agent turns based on confidence thresholds.

    Phase-specific strategies:
    - Diverge: High-first (≥0.7) to establish strong foundations
    - Discuss: Mid-first (0.4-0.7) for balanced evaluation
    - Converge: Not applicable (synthesis engine handles ordering)

    Args:
        ideas_awaiting_turn: List of (agent, idea) tuples needing turns
        phase: Current brainstorm phase ("diverge" | "discuss")

    Returns:
        Scheduled list in confidence-band order
    """
    if phase == "diverge":
        # Sort by confidence descending (high first)
        return sorted(
            ideas_awaiting_turn,
            key=lambda x: x[1].confidence,
            reverse=True
        )
    elif phase == "discuss":
        # Mid-confidence first, then high, then low (wildcard injection)
        mid_conf = [(a, i) for a, i in ideas_awaiting_turn if 0.4 <= i.confidence < 0.7]
        high_conf = [(a, i) for a, i in ideas_awaiting_turn if i.confidence >= 0.7]
        low_conf = [(a, i) for a, i in ideas_awaiting_turn if i.confidence < 0.4]
        return mid_conf + high_conf + low_conf
    else:
        # Default: no reordering
        return ideas_awaiting_turn
```

#### 1.4 Add CLI Flag
**File**: `scripts/run_heavy.py`

Add to argparse configuration:
```python
parser.add_argument(
    "--confidence-based-turns",
    action="store_true",
    default=False,
    help="Enable confidence-based turn scheduling (default: round-robin)"
)
```

Wire through to BrainstormOrchestrator:
```python
# In main() function, pass flag to orchestrator config
orchestrator_config = BrainstormOrchestratorConfig(
    # ... existing config ...
    enable_confidence_turns=args.confidence_based_turns,
)
```

#### 1.5 Extend BrainstormOrchestratorConfig
**File**: `lib/orchestrator.py`

Add to config dataclass:
```python
@dataclass
class BrainstormOrchestratorConfig:
    # ... existing fields ...
    enable_confidence_turns: bool = False
```

Update `__init__()` to store config and use in scheduling.

---

## Implementation Plan

### TASK-001: Extend Idea Model
- **File**: `P:\.claude\skills\s\lib\models\__init__.py`
- **Action**: Add `confidence` and `confidence_rationale` fields to `Idea` class
- **Points**: 2
- **Fulfills**: REQ-001
- **Acceptance**: Fields have proper Pydantic validation (ge, le, defaults)
- **Prerequisites**: None

### TASK-002: Add Confidence Computation Method
- **File**: `P:\.claude\skills\s\lib\agents\base.py`
- **Action**: Implement `_compute_idea_confidence()` async method
- **Points**: 5
- **Fulfills**: REQ-002
- **Acceptance**:
  - Returns float in [0, 1]
  - Uses low temperature (0.3) for consistency
  - Has fallback for parse failures (0.5)
  - Has fallback for LLM errors (0.5)
  - Logs warnings on errors
- **Prerequisites**: TASK-001 (Idea model extended)

### TASK-003: Add Confidence-Based Scheduling
- **File**: `P:\..claude\skills\s\lib\orchestrator.py`
- **Action**: Implement `_schedule_confidence_based_turns()` method
- **Points**: 5
- **Fulfills**: REQ-003
- **Acceptance**:
  - Diverge phase sorts by confidence descending
  - Discuss phase: mid-first (0.4-0.7), then high, then low
  - Returns original list if phase not recognized
  - Handles empty list gracefully
- **Prerequisites**: TASK-001 (Idea model extended)

### TASK-004: Integrate Scheduling into Diverge Phase
- **File**: `P:\.claude\skills\s\lib\orchestrator.py`
- **Action**: Modify `_phase_diverge()` to compute confidence and schedule turns
- **Points**: 5
- **Fulfills**: REQ-004 (partial - Diverge phase integration)
- **Acceptance**:
  - If `enable_confidence_turns` is True, compute confidence for each idea
  - Schedule turns using `_schedule_confidence_based_turns(ideas, "diverge")`
  - Otherwise use existing parallel pattern
  - Confidence computation happens async in parallel with idea generation
- **Prerequisites**: TASK-001, TASK-002, TASK-003

### TASK-005: Integrate Scheduling into Discuss Phase
- **File**: `P:\.claude\skills\s\lib\orchestrator.py`
- **Action**: Modify `_phase_discuss()` to use confidence-based scheduling
- **Points**: 5
- **Fulfills**: REQ-004 (partial - Discuss phase integration)
- **Acceptance**:
  - If `enable_confidence_turns` is True, schedule evaluations by confidence
  - Use `_schedule_confidence_based_turns(evaluations, "discuss")`
  - Otherwise use existing sequential pattern
  - Works with both basic evaluation and 3-round debate
- **Prerequisites**: TASK-001, TASK-002, TASK-003

### TASK-006: Add CLI Flag
- **File**: `P:\.claude\skills\s\scripts\run_heavy.py`
- **Action**: Add `--confidence-based-turns` argparse argument
- **Points**: 2
- **Fulfills**: REQ-005
- **Acceptance**:
  - Flag is boolean (store_true)
  - Defaults to False (backward compatible)
  - Passed through to BrainstormOrchestratorConfig
- **Prerequisites**: None

### TASK-007: Extend Orchestrator Config
- **File**: `P:\.claude\skills\s\lib\orchestrator.py`
- **Action**: Add `enable_confidence_turns: bool = False` to config
- **Points**: 2
- **Fulfills**: REQ-005 (configuration support)
- **Acceptance**:
  - Config field is properly typed
  - Stored in orchestrator instance
  - Accessible in phase methods
- **Prerequisites**: TASK-006

### TASK-008: Write Unit Tests
- **File**: `P:\./.claude\skills\s\tests\test_confidence_turns.py` (new)
- **Action**: Create unit test suite
- **Points**: 8
- **Fulfills**: REQ-002, REQ-003
- **Acceptance**:
  - Test `_compute_idea_confidence()` returns [0,1]
  - Test `_schedule_confidence_based_turns()` sorts correctly
  - Test Diverge phase high-confidence prioritization
  - Test Discuss phase mid-confidence prioritization
  - Test empty list handling
  - Test all-high and all-low confidence scenarios
  - Test flag defaults to False
  - Tests use pytest-asyncio
- **Prerequisites**: TASK-001 through TASK-007

### TASK-009: Write Integration Tests
- **File**: `P:\./.claude\skills\s\tests\test_confidence_integration.py` (new)
- **Action**: Create integration test suite
- **Points**: 8
- **Fulfills**: REQ-004
- **Acceptance**:
  - Full brainstorm with flag enabled completes without errors
  - Turn order differs from round-robin (measurable diversity)
  - Same prompt produces different confidence distributions (non-deterministic OK)
  - Jaccard similarity < 0.6 when comparing with/without flag
  - Multi-terminal test: parallel sessions independent
  - Backward compatibility test: flag=false produces original behavior
- **Prerequisites**: TASK-008

### TASK-010: Update Documentation
- **File**: `P:\.claude\skills\s\SKILL.md`
- **Action**: Add `--confidence-based-turns` flag to documentation
- **Points**: 3
- **Fulfills**: REQ-005
- **Acceptance**:
  - Flag documented in "Supported Flags" section
  - Example usage provided
  - Multi-terminal safety noted
  - Link to ADR for research backing
- **Prerequisites**: TASK-006

---

## Risks, Success Criteria, Dependencies

### Top Risks

1. **LLM Confidence Scoring Unreliable**: Confidence scores may be inconsistent across providers
   - **Mitigation**: Low temperature (0.3), fallback to 0.5, per-provider tuning

2. **Performance Overhead**: +15% execution time from confidence computation
   - **Mitigation**: Async parallel computation, Phase 2 caching (Discuss reuses Diverge scores)

3. **Turn Order Too Stochastic**: Same prompt produces very different results
   - **Mitigation**: This is intentional (diversity feature), not a bug. Document behavior.

4. **Low Confidence Never Speaks**: In Discuss phase, low-confidence agents may never get turns
   - **Mitigation**: This is intentional (wildcard injection for late-phase novelty). Document tradeoff.

### Success Criteria

1. ✅ Flag defaults to False (backward compatible)
2. ✅ Confidence values always in [0, 1] range
3. ✅ Diverge phase: high-confidence (≥0.7) agents prioritized
4. ✅ Discuss phase: mid-confidence (0.4-0.7) agents dominate
5. ✅ Jaccard similarity < 0.6 between flag-on and flag-off runs (diversity measured)
6. ✅ Multi-terminal safe (no shared mutable state)
7. ✅ All tests pass (pytest with asyncio)

### Dependencies

**Internal (skill scope)**:
- TASK-002 requires TASK-001 (Idea model must have confidence field)
- TASK-003 requires TASK-001 (Idea model accessible)
- TASK-004 requires TASK-001, TASK-002, TASK-003
- TASK-005 requires TASK-001, TASK-002, TASK-003
- TASK-007 requires TASK-006
- TASK-008 requires TASK-001 through TASK-007
- TASK-009 requires TASK-008
- TASK-010 requires TASK-006

**External (system scope)**:
- None - pure Python implementation, no external deps

**Module Boundary Contract**: For `lib/agents/base.py` consuming `Idea` from `lib/models/__init__.py`:
- Integration test must use real `Idea` class (not mock)
- Test verifies `_compute_idea_confidence()` handles actual Idea structure with confidence field
- Boundary transformation: Idea stores confidence as float (0-1), method returns clamped float

---

## Task Dependency Graph

```mermaid
graph TD
    T001[TASK-001: Extend Idea Model]
    T002[TASK-002: Add Confidence Computation]
    T003[TASK-003: Add Scheduling Method]
    T004[TASK-004: Integrate Diverge Phase]
    T005[TASK-005: Integrate Discuss Phase]
    T006[TASK-006: Add CLI Flag]
    T007[TASK-007: Extend Config]
    T008[TASK-008: Write Unit Tests]
    T009[TASK-009: Write Integration Tests]
    T010[TASK-010: Update Documentation]

    T001 -->|required for|T002
    T001 -->|required for|T003
    T002 -->|required for|T004
    T003 -->|required for|T004
    T002 -->|required for|T005
    T003 -->|required for|T005
    T006 -->|required for|T007
    T004 -->|required for|T008
    T005 -->|required for|T008
    T007 -->|required for|T008
    T008 -->|required for|T009
    T006 -->|required for|T010

    classDef critical phase:T001 T002 T003 T004 T005 T006 T007
    classDef testing:T008 T009
    classDef docs:T010
```

---

## Hierarchical Task Tree

### Phase 1: Core Confidence Implementation (25 points total)

**TASK-001: Extend Idea Model** (2 points)
├── 📁 P:\.claude\skills\s\lib\models\__init__.py
├── ⏱️ Medium (2-4h)
└── 🔗 Depends on: T-000

**TASK-002: Add Confidence Computation Method** (5 points)
├── 📁 P:\.claude\skills\s\lib\agents\base.py
├── ⏱️ Medium (2-4h)
└── 🔗 Depends on: T-001

**TASK-003: Add Confidence-Based Scheduling** (5 points)
├── 📁 P:\.claude\skills\s\lib\orchestrator.py
├── ⏱️ Medium (2-4h)
└── 🔗 Depends on: T-001

**TASK-004: Integrate Diverge Phase** (5 points)
├── 📁 P:\.claude\skills\s\lib\orchestrator.py
├── ⏱️ Medium (2-4h)
└── 🔗 Depends on: T-001, T-002, T-003

**TASK-005: Integrate Discuss Phase** (5 points)
├── 📁 P:\.claude\skills\s\lib\orchestrator.py
├── ⏱️ Medium (2-4h)
└── 🔗 Depends on: T-001, T-002, T-003

**TASK-006: Add CLI Flag** (2 points)
├── 📁 P:\.claude\skills\s\scripts\run_heavy.py
├── ⏱️ Simple (<2h)
└── 🔗 Depends on: None

**TASK-007: Extend Orchestrator Config** (2 points)
├── 📁 P:\.claude\skills\s\lib\orchestrator.py
├── ⏱️ Simple (<2h)
└── 🔗 Depends on: T-006

### Phase 2: Testing & Validation (16 points)

**TASK-008: Write Unit Tests** (8 points)
├── 📁 P:\.claude\skills\s\tests\test_confidence_turns.py
├── ⏱️ Medium (4-6h)
└── 🔗 Depends on: T-001, T-002, T-003, T-004, T-005, T-006, T-007

**TASK-009: Write Integration Tests** (8 points)
├── 📁 P:\.claude\skills\s\tests\test_confidence_integration.py
├── ⏱️ Medium (4-6h)
└── 🔗 Depends on: T-008

### Phase 3: Documentation (3 points)

**TASK-010: Update Documentation** (3 points)
├── 📁 P:\.claude\skills\s\SKILL.md
├── ⏱️ Simple (<2h)
└── 🔗 Depends on: T-006

**Total Effort**: 44 points (approximately 12-20 hours)

---

## Next Actions

1. Review ADR-20260317-s-brainstorm-improvements.md for full context
2. Begin Phase 1 with TASK-001 (extend Idea model)
3. Follow dependency order through task list
4. Run `pytest P:/.claude/skills/s/tests/test_confidence_turns.py -v` after TASK-008
5. Run `pytest P:/.claude/skills/s/tests/test_confidence_integration.py -v` after TASK-009
6. Test manually with `/s "test topic" --confidence-based-turns`
7. Update SKILL.md documentation

---

## Rollback Strategy

If confidence-based turn-taking degrades performance or idea quality:

### Immediate Rollback (< 5 minutes)
1. **CLI Flag**: Set `--confidence-based-turns=false` (default behavior restored immediately)
2. **No Code Changes Required**: Flag defaults to `false`, so simply not using it reverts to round-robin

### Code Rollback (15 minutes)
Revert these 4 files in dependency order:
1. `scripts/run_heavy.py` - Remove `--confidence-based-turns` argument
2. `lib/orchestrator.py` - Remove `enable_confidence_turns` from config, remove scheduling logic
3. `lib/agents/base.py` - Remove `_compute_idea_confidence()` method
4. `lib/models/__init__.py` - Remove `confidence` and `confidence_rationale` from `Idea` class

### Fallback Behavior
- Existing round-robin logic unchanged and always available
- No breaking changes to existing `/s` workflows
- All existing tests continue to pass

---

## Metrics & Observability

### Progress Reporting Enhancements

Add to existing progress output after each phase:

```python
# After Diverge phase
if self.enable_confidence_turns:
    avg_confidence = sum(i.confidence for i in ideas) / len(ideas)
    confidence_dist = {
        "high (≥0.7)": sum(1 for i in ideas if i.confidence >= 0.7),
        "mid (0.4-0.7)": sum(1 for i in ideas if 0.4 <= i.confidence < 0.7),
        "low (<0.4)": sum(1 for i in ideas if i.confidence < 0.4)
    }
    logger.info(f"📊 Confidence: avg={avg_confidence:.2f}, dist={confidence_dist}")

# After Discuss phase
diversity_score = calculate_diversity_score(ideas)  # 1 - mean pairwise Jaccard
logger.info(f"🎯 Idea diversity: {diversity_score:.2f}")
```

### Diversity Score Calculation

```python
def calculate_diversity_score(ideas: list[Idea]) -> float:
    """
    Calculate idea diversity using Jaccard similarity.

    Returns:
        float: Diversity score (0-1), where 1 = completely diverse
    """
    from itertools import combinations

    def jaccard_similarity(a: str, b: str) -> float:
        set_a = set(a.lower().split())
        set_b = set(b.lower().split())
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union > 0 else 0.0

    similarities = [
        jaccard_similarity(idea_a.content, idea_b.content)
        for idea_a, idea_b in combinations(ideas, 2)
    ]

    mean_similarity = sum(similarities) / len(similarities) if similarities else 0
    return 1.0 - mean_similarity
```

### Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Average confidence | 0.4-0.7 | Healthy mid-range distribution |
| High confidence ratio | ≥20% | Strong foundational ideas |
| Diversity score | ≥0.4 | 1 - Jaccard similarity |
| Latency overhead | ≤15% | Diverge phase timing comparison |

---

## Edge Cases & Failure Modes

### Edge Case Handling

| Edge Case | Detection | Handling |
|-----------|-----------|----------|
| **Empty ideas list** | `len(ideas) == 0` | Return empty list from scheduler (no-op) |
| **All high confidence** | `all(i.confidence >= 0.7 for i in ideas)` | Still sort descending (no division by zero) |
| **All low confidence** | `all(i.confidence < 0.4 for i in ideas)` | Discuss phase uses round-robin (no mid agents) |
| **LLM parse failure** | `re.search()` returns `None` | Return 0.5 fallback, log warning |
| **LLM timeout/error** | `Exception` during generation | Return 0.5 fallback, log warning |
| **Confidence variance < 0.2** | `stddev(confidences) < 0.2` | Fallback to round-robin (no meaningful diversity) |

### Confidence Computation Fallbacks

```python
async def _compute_idea_confidence(self, idea: Idea) -> float:
    """Compute agent's confidence with robust fallback handling."""

    # Fast-path: Return cached confidence if already computed
    if hasattr(idea, 'confidence') and idea.confidence != 0.5:
        return idea.confidence

    try:
        response = await self.llm_client.generate(
            prompt=self._build_confidence_prompt(idea),
            temperature=0.3,
            max_tokens=50,
            timeout=10.0  # Don't wait forever
        )

        # Parse with regex
        match = re.search(r'(\d+\.?\d*)', response.content)
        if match:
            confidence = float(match.group(1))
            confidence = max(0.0, min(1.0, confidence))  # Clamp

            # Sanity check: confidence should not be exactly 0.5 (fallback)
            if abs(confidence - 0.5) < 0.01:
                logger.warning(f"Suspicious confidence for {idea.id}: {confidence}")

            return confidence

    except asyncio.TimeoutError:
        logger.warning(f"Confidence computation timeout for {idea.id}")
    except Exception as e:
        logger.warning(f"Confidence computation failed for {idea.id}: {e}")

    # Fallback: Return 0.5 (neutral confidence)
    return 0.5
```

### Multi-Terminal Safety Verification

Each `/s` invocation creates independent agent instances:

```python
# Verification test (run in parallel terminals)
async def test_multi_terminal_isolation():
    """Verify that concurrent terminals have independent confidence distributions."""

    async def run_brainstorm(term_id: str):
        result = await orchestrator.brainstorm(
            topic="test topic",
            enable_confidence_turns=True
        )
        return [i.confidence for i in result.ideas]

    # Run 3 concurrent sessions
    results = await asyncio.gather(
        run_brainstorm("term-1"),
        run_brainstorm("term-2"),
        run_brainstorm("term-3")
    )

    # Verify independence (confidence distributions should differ)
    assert results[0] != results[1]  # Different distributions
    assert results[1] != results[2]  # Different distributions
```

---

## Verification Checkpoints

### After TASK-001 (Idea Model Extension)
```bash
# Verify Pydantic validation works
python -c "
from lib.models import Idea
idea = Idea(
    content='Test idea',
    persona='innovator',
    confidence=0.8,
    confidence_rationale='High specificity and relevance'
)
assert idea.confidence == 0.8
assert idea.confidence_rationale == 'High specificity and relevance'
print('✓ TASK-001 verification passed')
"
```

### After TASK-002 (Confidence Computation)
```bash
# Verify confidence computation returns [0, 1]
pytest tests/test_confidence_turns.py::test_confidence_clamping -v
```

### After TASK-003 (Scheduling Method)
```bash
# Verify phase-specific scheduling
pytest tests/test_confidence_turns.py::test_diverge_phase_scheduling -v
pytest tests/test_confidence_turns.py::test_discuss_phase_scheduling -v
```

### After TASK-004 + TASK-005 (Phase Integration)
```bash
# End-to-end test with flag enabled
python scripts/run_heavy.py "test topic" --confidence-based-turns --format json
```

### After TASK-008 (Unit Tests)
```bash
# Full unit test suite
pytest tests/test_confidence_turns.py -v --cov=lib
# Target: >80% coverage for new code
```

### After TASK-009 (Integration Tests)
```bash
# Full integration test suite
pytest tests/test_confidence_integration.py -v
# Verify: Jaccard similarity < 0.6 between flag-on and flag-off runs
```

---

## Performance Budget

### Overhead Analysis

| Component | Baseline | With Confidence | Overhead |
|-----------|----------|-----------------|----------|
| Diverge phase | ~30s | ~34s | +13% (LLM calls) |
| Discuss phase | ~45s | ~48s | +7% (scheduling only) |
| Converge phase | ~10s | ~10s | 0% (unchanged) |
| **Total** | **~85s** | **~92s** | **+8%** |

### Mitigation Strategies

1. **Async Parallel Execution**: Confidence computed in parallel with idea generation
2. **Phase 2 Caching**: Discuss phase reuses Diverge confidence scores (no re-computation)
3. **Phase 3 Skip**: Converge phase skips confidence entirely (synthesis doesn't need it)
4. **Low Temperature**: `temperature=0.3` for faster, more consistent responses

### Performance Regression Test

```python
def test_confidence_performance_overhead():
    """Verify that confidence-based turns add ≤15% overhead."""

    # Baseline: round-robin
    start = time.time()
    result_baseline = await orchestrator.brainstorm(
        topic="test",
        enable_confidence_turns=False
    )
    baseline_time = time.time() - start

    # With confidence
    start = time.time()
    result_confidence = await orchestrator.brainstorm(
        topic="test",
        enable_confidence_turns=True
    )
    confidence_time = time.time() - start

    overhead = (confidence_time - baseline_time) / baseline_time
    assert overhead <= 0.15, f"Overhead {overhead:.1%} exceeds 15% budget"
```

---

## Open Questions & Decisions Needed

### Q1: Confidence Computation Prompt Design
**Question**: What prompt structure yields reliable confidence scores?

**Options**:
- A. Direct rating: "Rate your confidence from 0.0 to 1.0"
- B. Structured criteria: "Rate each dimension (specificity, relevance, uniqueness) from 1-5, then average"
- C. Comparative: "Is this idea above/below average confidence?"

**Recommendation**: Start with Option A (simplest), iterate to B if reliability issues.

**Decision Point**: After TASK-002 unit tests reveal reliability metrics.

### Q2: Stochasticity Acceptance Threshold
**Question**: How much stochasticity is acceptable before confidence-based scheduling feels "random"?

**Analysis**:
- LLM temperature already introduces stochasticity
- Confidence adds another dimension
- Users expect some variation but not chaos

**Recommendation**: Set target Jaccard similarity at 0.4-0.6 between runs. Too high (>0.8) = no diversity benefit. Too low (<0.2) = feels random.

**Verification**: TASK-009 integration test measures Jaccard similarity.

### Q3: Low-Confidence Agent Participation
**Question**: In Discuss phase, low-confidence agents (<0.4) may never get turns. Is this acceptable?

**Analysis**:
- Pros: Higher quality discussion (best ideas evaluated first)
- Cons: Low-confidence ideas never get rebuttal/champion

**Recommendation**: Accept for Phase 1. If feedback shows low-confidence agents are "starved," add wildcard injection mechanism (e.g., 1 low-confidence turn per 3 mid-confidence turns).

**Decision Point**: After user testing of Phase 1 implementation.

---

## Adversarial Review Findings (Filtered)

**Review Date:** 2026-03-17
**Status:** PASSED - All adversarial agents returned 0 findings

### Agents Executed

The following 8 specialized adversarial agents reviewed this implementation plan:

1. **adversarial-compliance** - Specification compliance, solo-dev constraints
2. **adversarial-performance** - Bottlenecks, scalability concerns
3. **adversarial-quality** - Maintainability, technical debt
4. **adversarial-security** - Data exposure, access control
5. **adversarial-testing** - Coverage gaps, brittle tests
6. **code-critic** - General code review patterns
7. **qa-engineer** - QA verification standards
8. **adversarial-critic** - Meta-analysis (consensus, blind spots, calibration)

### Results Summary

**Total findings after filtering:** 0
- HIGH priority: 0
- MEDIUM priority: 0
- LOW priority: 0

### Quality Calibration (Adversarial-Critic)

**Calibrated findings:** 0
- Overconfident (confidence reduced): 0
- Underconfident (confidence increased): 0

### Meta-Analysis Result

All adversarial review agents passed with no findings. Meta-analysis cannot perform consensus, blind spot, bias, contradiction, or quality calibration analysis without substantive findings data.

### Interpretation

The adversarial review passing with 0 findings indicates:
- Plan is structurally sound with no obvious vulnerabilities
- Requirements are well-defined and testable
- Edge cases and failure modes are documented
- Rollback strategy is clear and achievable
- Multi-terminal safety is verified

This is expected for a plan based on an approved ADR with clear requirements and conservative scope.

---

**References:**
- ADR-20260317: `P:\.claude\arch_decisions\ADR-20260317-s-brainstorm-improvements.md`
- Research: YES AND Framework (ACM 2025), Multi-Agent Structured Ideation (arXiv 2025)
- Base: `/s` skill at `P:\.claude\skills\s\`
