# ADR: Hook-Based Detection for Proposal-Decision Conflation

**Status:** Accepted
**Date:** 2026-04-07
**Context:** LLM wrote "Option B is correct" in a plan after user rejected Option B and confirmed removal. Behavioral pattern — conflation of proposal state with decision state.

---

### Decision

Add a **PostToolUse** hook that detects when plan files contain decision claims that contradict user rejections, using a lightweight contradiction scanner.

---

### Rationale

The `inherited_choice_validator.py` (archived) shows the pattern: PostToolUse detects → state file stores → PreToolUse checks. The proposal-decision conflation can be caught similarly:
1. **Stop hook** scans generated plan content for decision-vs-rejection contradictions
2. **Warning injection** before plan is considered complete
3. **No blocking** — advisory only (behavioral pattern, not security/critical)

This is **not** contract-sensitive — no persistent state, no cross-boundary handoff, no multi-terminal state. The hook operates on generated content within a single turn.

---

### Alternatives Considered

| Option | Description | Pros | Cons | Why Rejected |
|--------|-------------|------|------|--------------|
| **A (chosen)** | Stop hook contradiction scanner | Lightweight, no state persistence, uses existing evidence patterns | Advisory only (can't block plan writing) | Simplest fix for behavioral pattern |
| B | New PreToolUse plan-state tracker | Could block earlier | Requires cross-turn state management, complexity | Over-engineering for P2 behavioral issue |
| C | Extend inherited_choice_validator | Reuses existing pattern | Wrong scope — this hook detects version patterns, not decision state | Conceptually wrong |
| D | No hook — behavioral reminder only | Simplest | No enforcement, relies on LLM compliance | Insufficient for recurring pattern |

---

### Tradeoffs

| Quality | Improved | Degraded |
|---------|----------|----------|
| Correctness | Detects opposite decision claims in plans | None |
| Performance | Lightweight regex scan on Stop event | Negligible (<10ms) |
| Complexity | Minimal new code | None |
| Reliability | Catches the specific conflation pattern | May miss similar patterns not matching regex |

---

### Multi-Terminal Safety

- **Safe** — Hook operates on generated content, no file state, no cross-terminal dependency
- Each terminal's Stop hook processes its own response independently

---

### Implementation

**New hook**: `Stop_proposal_decision_scanner.py`

**Detection patterns:**
```python
DECISION_CLAIM_PATTERNS = [
    r"(Option\s+[A-Z])\s+is\s+correct",
    r"(Option\s+[A-Z])\s+is\s+right",
    r"(Option\s+[A-Z])\s+should\s+be\s+used",
    r"go\s+with\s+(Option\s+[A-Z])",
]

REJECTION_PATTERNS = [
    r"(Option\s+[A-Z])\s+(doesn't\s+make\s+sense|rejected|removed)",
    r"(Option\s+[A-Z])\s+(shouldn't?\s+be\s+used",
    r"don't\s+rebuild",
]
```

**Detection flow:**
1. Stop hook receives response
2. Extract plan content (section between "### Implementation" or similar headers)
3. Scan for decision claims ("Option X is correct")
4. Cross-check against tracked rejections from conversation
5. If contradiction found → inject advisory warning

---

### Consequences

- **Positive:** Catches proposal-decision conflation before user sees plan
- **Negative:** Advisory only — LLM can ignore warning
- **Risk:** False positives on similar phrases (mitigate: require both rejection + opposite claim)

---

**Confidence:** 70% — Behavioral pattern with existing hook infrastructure, but efficacy depends on regex quality

**Evidence basis:**
- `inherited_choice_validator.py` (archived) shows PostToolUse→state→PreToolUse pattern works
- `Stop_completion_verification_guard.py` shows Stop hook claim scanning is feasible
- No CKS entries for this specific pattern (first occurrence)

**Key assumptions:**
1. Plan content is included in Stop hook message
2. Contradiction can be reliably detected via regex
3. Advisory warning is sufficient (user will catch remaining cases)

**Source:** /arch session `5802b6ad-f42c-4fb0-9015-83044d96c2bf.jsonl` (2026-04-07)
