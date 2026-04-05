# Architecture Decision: Hooks Improvement Gaps Analysis

**Date:** 2026-02-09
**Template:** python
**Trigger:** IMPROVE_SYSTEM - Review LLM's hook optimization recommendations

---

## Decision

The hooks system has sophisticated token-based evidence enforcement already implemented (7 disqualifying conditions), but lacks a circuit breaker for consecutive blocks—the only high-value gap.

## Rationale

### 1. Token System EXISTS (LLM Missed This)

**Location:** `Stop_router.py:753-880`

The LLM proposed an "event-driven token system with disqualifying conditions" as a new feature. This already exists:

```python
# Disqualifying reasons (Stop_router.py:97-103)
EVIDENCE_TOKEN_DISQUALIFY_TERMINAL_MISMATCH = "TERMINAL_MISMATCH"
EVIDENCE_TOKEN_DISQUALIFY_SESSION_MISMATCH = "SESSION_MISMATCH"
EVIDENCE_TOKEN_DISQUALIFY_WORKFLOW_MISMATCH = "WORKFLOW_MISMATCH"
EVIDENCE_TOKEN_DISQUALIFY_EVIDENCE_SUPERSEDED = "EVIDENCE_SUPERSEDED"
EVIDENCE_TOKEN_DISQUALIFY_BLOCKER_INTERVENED = "BLOCKER_INTERVENED"
EVIDENCE_TOKEN_DISQUALIFY_CONTRACT_VIOLATION = "CONTRACT_VIOLATION"
EVIDENCE_TOKEN_DISQUALIFY_REPLAY_OR_DOUBLE_USE = "REPLAY_OR_DOUBLE_USE"
EVIDENCE_TOKEN_DISQUALIFY_MANUAL_INVALIDATION = "MANUAL_INVALIDATION"
```

Token structure includes:
- `token_id`, `scope_key`, `terminal_key`, `session_id`, `workflow_id`
- `state`: active/disqualified
- `observation_receipt_id`, `observation_signature`, `observation_count`
- `required_contract_fields` (evidence field names)

### 2. LOOP_PREVENTION is Overstated

**Location:** `assumption_audit_v2.py:1441`

The LLM claimed "LOOP_PREVENTION logic exists" as a mechanism. Reality:

```python
if input_data.get("stop_hook_active", False):
    print(format_hook_output(decision="allow", reason="LOOP_PREVENTION"))
    sys.exit(0)
```

This is a simple guard to prevent recursive blocking when `stop_hook_active=True`—not a sophisticated loop prevention mechanism.

### 3. quantitative_topic_guard EXISTS (LLM Missed This)

**Location:** `UserPromptSubmit_router.py:86, 1371, 2172`

The LLM recommended "moving claim-quality enforcement to UserPromptSubmit" as if this were new. Already implemented:

```python
"quantitative_topic_guard": 5.1,  # Confident quantitative claims without sources
```

Per `STOP_HOOK_TRANSCRIPT_PROBLEM.md:142`, this was implemented 2026-02-09.

### 4. Real Gap: No Circuit Breaker

**Evidence:** `stop_churn_metrics.json`

```json
"env_8c8ca074...|7edab35e-b1ed-4d4e-a6ba-edb172bc2b45": {
  "consecutive_blocks": 28,
  "last_block_hook": "unified_evidence_enforcer"
}
```

No `MAX_CONSECUTIVE_BLOCKS` constant exists in `Stop_router.py`. The session hit 28 blocks without intervention.

## Alternatives Considered

| Alternative | Trade-off |
|-------------|-----------|
| **Add `MAX_CONSECUTIVE_BLOCKS=5` with fail-open to warn** | Simple, protects against 28-block loops, but may hide legitimate enforcement needs |
| Investigate 28-block root cause first | High effort, may be one-time anomaly, doesn't add structural protection |
| Consolidate evidence gates further | UEEA already consolidates 4 gates; additional merging risks regression |
| Remove all TTLs (per user preference) | Breaks existing cache invalidation (`_GRACE_CACHE_TTL=30`, `BLOCK_DEDUPE_TTL_SECONDS=20`) |

## Risk

- **Adding circuit breaker**: May suppress legitimate repeated blocks if user genuinely needs multiple attempts to satisfy evidence requirements
- **Token system already complex**: 8 disqualifying conditions + scope resolution logic—additional complexity increases maintenance burden
- **Python 3.12+ not fully leveraged**: No type generics for token state, `@overload` for scope resolution variants could improve clarity

## Confidence

**85%** — Evidence from actual code (`Stop_router.py:97-103`, `assumption_audit_v2.py:1441`, `UserPromptSubmit_router.py:86`) confirms most claimed gaps are already implemented or overstated. Only missing piece is consecutive block circuit breaker.

## Adversarial Self-Review

Weakest assumption is that the 28-block loop represents a systemic problem rather than a one-time edge case. If it's edge case, adding circuit breaker adds complexity for minimal benefit.

## Recommended Action

Add `MAX_CONSECUTIVE_BLOCKS` circuit breaker:

```python
# Stop_router.py (new constant)
MAX_CONSECUTIVE_BLOCKS = int(os.environ.get("STOP_MAX_CONSECUTIVE_BLOCKS", "5"))

# In block recording logic
if consecutive_blocks >= MAX_CONSECUTIVE_BLOCKS:
    return {
        "decision": "warn",
        "reason": f"Hit {consecutive_blocks} consecutive blocks. Circuit breaker: allowing with warning."
    }
```

**Reversibility:** R:1.25 (environment variable override, simple addition)

## References

- Token system: `Stop_router.py:737-880`
- LOOP_PREVENTION: `assumption_audit_v2.py:1441`
- quantitative_topic_guard: `UserPromptSubmit_router.py:86, 1371, 2172`
- 28-block session: `stop_churn_metrics.json` line `7edab35e-b1ed-4d4e-a6ba-edb172bc2b45`
