# Multi-Hypothesis Tracking Architecture Decision

**Status:** Accepted
**Date:** 2026-04-06
**Context:** Perplexity AI chat analysis identified GLM/MiniMax failure mode "Overfits to first plausible explanation"
**Decision:** Extend existing sequential thinking system with multi-hypothesis mode (Option A)

---

## Context

### Problem Statement

From Perplexity AI chat analysis (`C:\Users\brsth\Downloads\I'm using glm and minimax in claude code and I alw (1).md`):

GLM/MiniMax LLMs exhibit a critical failure mode:
> **Overfits to first plausible explanation** - Once an LLM generates a working hypothesis, it tends to defend it rather than exploring alternatives, even when evidence is weak.

### Proposed Solutions (from chat)

1. **Multi-Hypothesis Tracking** - Maintain 2-3 competing explanations throughout investigation
2. **Exit-Code Feedback Loop** - Capture failed Bash output and re-inject (ALREADY IMPLEMENTED)
3. **Git-Diff Re-grounding** - Detect file changes during investigation (DEFERRED)
4. **Root-Cause vs Workaround Evaluator** - Distinguish fixes from workarounds
5. **Atomic Commit Enforcement** - Suggest git commit after each edit (DEFERRED)

---

## Decision

### Option A Selected: Extend Sequential Thinking

**Extend the existing sequential thinking system (`PreToolUse_sequential_thinking.py`) with multi-hypothesis tracking capability.**

### Rationale

| Factor | Finding |
|--------|----------|
| **Existing Infrastructure** | State management, terminal isolation, and mode injection already implemented |
| **Code Verification** | Read and verified `sequential_state.py`, `PreToolUse_sequential_thinking.py`, `StopHook_sequential_thinking.py` |
| **Backward Compatibility** | Existing modes (initial/critique/improvement) unchanged; new modes additive |
| **Reversibility** | 1.25 (moderate) - Can revert by removing new mode entries |
| **Effort** | ~4 phases, 80% value for 20% effort of standalone system |

### Verified Current State (from source code)

**State Schema** (`sequential_state.py:8-18`):
```json
{
  "session_id": "uuid",
  "trigger_phrase": "string",
  "current_iteration": 0,
  "max_iterations": 2,
  "mode": "initial|critique|improvement",
  "intermediate_answers": [],
  "final_answer": null,
  "active": true,
  "terminal_id": "identifier"
}
```

**MODE_MESSAGES** (`PreToolUse_sequential_thinking.py:24-44`):
- `initial` - Generate your best answer
- `critique` - Analyze for gaps, assumptions, weaknesses
- `improvement` - Synthesize improved answer

**Infrastructure Verified**:
- State directory: `P:/.claude/state/sequential-thinking/`
- Terminal-scoped filenames: `{session_id}_{terminal_id}.json`
- State module: `__lib/sequential_state.py` with CRUD functions
- Multi-terminal isolation: Already implemented

---

## Implementation Plan

### Phase 1: State Schema Extension

**File:** `P:/.claude/hooks/__lib/sequential_state.py`

**Changes:**
1. Add `hypotheses: []` array to state schema
2. Add `hypothesis_mode: false` flag for backward compatibility
3. Extend `create_state()` to initialize empty hypotheses array

**Schema Extension:**
```python
state = {
    # ... existing fields ...
    "hypotheses": [],  # NEW: Array of competing hypotheses
    "hypothesis_mode": False,  # NEW: Enable multi-hypothesis tracking
}
```

### Phase 2: Mode Messages

**File:** `P:/.claude/hooks/PreToolUse_sequential_thinking.py`

**New Modes:**
```python
MODE_MESSAGES = {
    # ... existing modes ...

    "multi_hypothesis": """You are in MULTI-HYPOTHESIS mode. Generate 2-3 competing explanations for the problem.

For each hypothesis:
1. State the explanation clearly
2. Identify what evidence would support it
3. Identify what evidence would refute it

Maintain all hypotheses as equally plausible until evidence discriminates between them.""",

    "hypothesis_critique": """You are in HYPOTHESIS CRITIQUE mode. Evaluate each competing hypothesis against the evidence.

For each hypothesis:
1. Compare predictions to actual observations
2. Identify inconsistencies or contradictions
3. Rank hypotheses by explanatory power

Do NOT eliminate a hypothesis until you have strong evidence against it.""",

    "hypothesis_resolution": """You are in HYPOTHESIS RESOLUTION mode. Synthesize the best explanation from competing hypotheses.

1. Select the hypothesis best supported by evidence
2. Explain why other hypotheses were weaker
3. Identify what additional evidence would strengthen confidence

This is your final answer - make it comprehensive and well-reasoned.""",
}
```

### Phase 3: Trigger Detection

**File:** `P:/.claude/hooks/UserPromptSubmit_modules/sequential_thinking.py`

**New Trigger Patterns:**
```python
r"\bmaintain\s+multiple\s+hypotheses\b"
r"\bcompeting\s+hypotheses\b"
r"\bparallel\s+explanations\b"
r"\bwhat\s+(?:are|could\s+be)\s+(?:the\s+)?(?:possible|alternative)\s+explanations\b"
```

### Phase 4: Integration & Testing

**Files:**
- `P:/.claude/hooks/PreToolUse_sequential_thinking.py`
- `P:/.claude/hooks/StopHook_sequential_thinking.py`
- `P:/.claude/hooks/tests/test_sequential_thinking_hooks.py`

**Tasks:**
1. Extend PreToolUse hook for hypothesis mode injection
2. Extend Stop hook for hypothesis tracking
3. Add test cases for multi-hypothesis workflow

---

## Contract Authority Packet

```yaml
contract_authority_packet:
  packet_version: "1"
  contract_sensitive: false  # Extension to existing system, no new boundaries

  boundaries:
    - boundary_id: "sequential-thinking-state"
      producer: "UserPromptSubmit_sequential_thinking.py"
      consumer: "PreToolUse_sequential_thinking.py, StopHook_sequential_thinking.py"
      schema:
        id: "sequential-thinking-state"
        version: "2"  # Extended from v1
      required_fields: ["session_id", "mode", "current_iteration"]
      optional_fields: ["hypotheses", "hypothesis_mode"]
      freshness_authority: "state_file_mtime"
      invalidation_trigger: "session exceeds TTL (7200s)"
      precedence_rule: "state_file wins"
      failure_behavior: "degrade_to_standard_mode"
      validator_owner: "sequential_thinking"
      proof_owner: "tests/test_sequential_thinking_hooks.py"
```

---

## Decision Matrix

| Option | VALUE | EVIDENCE | DISSENT | REVERSIBILITY | SECOND_ORDER | FAILURE_SCENARIO | SCORE |
|--------|-------|----------|---------|---------------|--------------|------------------|-------|
| **A: Extend** | +4 (leverage existing) | Tier 1: Read actual source | Higher complexity later | 1.25 | Clean: single system | State corruption unlikely | **18.0** |
| B: Standalone | +2 (clean slate) | Tier 3: Logical derivation | New code to maintain | 1.5 | Fragmented: two systems | Duplicate state logic | 12.0 |
| C: Hybrid | +1 (best of both) | Tier 4: Speculative | Integration overhead | 2.0 | Complex: glue needed | Sync issues likely | 4.0 |

**Recommendation:** Option A (Extend existing sequential thinking)
**Confidence:** 85% (based on verified code analysis, not speculation)

---

## Alternatives Considered

### Option B: Standalone Multi-Hypothesis System

**Pros:**
- Clean separation of concerns
- No risk to existing sequential thinking
- Can optimize for hypothesis-specific needs

**Cons:**
- Duplicate state management logic
- Fragmented user experience (two separate systems)
- Higher maintenance burden

**Rejected:** Lower value/effort ratio. Existing infrastructure is sufficient.

### Option C: Hybrid Approach

**Pros:**
- Best of both worlds (shared state, specialized logic)

**Cons:**
- Higher complexity
- Integration points create fragility
- Sync issues between systems

**Rejected:** Complexity not justified by benefits.

---

## Related Decisions

- **Exit-Code Feedback Loop:** Already implemented via `failure_context_injector.py` and `write_tool_error_signal.py`
- **Git-Diff Re-grounding:** Deferred - separate feature, merit not established
- **Atomic Commit Enforcement:** Deferred - advisory-only, may create noise

---

## References

- Source: `C:\Users\brsth\Downloads\I'm using glm and minimax in claude code and I alw (1).md`
- Handoff: `P:/__csf/handoffs/RNS-implementation-handoff.md`
- Implementation: `P:/.claude/hooks/PreToolUse_sequential_thinking.py`
- State: `P:/.claude/hooks/__lib/sequential_state.py`
- Tests: `P:/.claude/hooks/tests/test_sequential_thinking_hooks.py`
