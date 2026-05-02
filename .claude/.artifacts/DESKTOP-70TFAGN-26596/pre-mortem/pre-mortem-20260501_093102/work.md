# v1 Budget Coordination for UPS Pipeline

**Target files (5):**
- `P:\.claude\hooks\UserPromptSubmit_modules\unified_detection.py`
- `P:\.claude\templates\llm_behavior_contract.md`
- `P:\.claude\hooks\UserPromptSubmit_modules\reasoning_mode_selector.py`
- `P:\.claude\hooks\UserPromptSubmit_modules\cognitive_enhancers.py`
- `P:\.claude\hooks\UserPromptSubmit_modules\testing_strategy_router.py`
- `P:\.claude\hooks\UserPromptSubmit.py`

## Summary of Changes

### 1. unified_detection.py
- Added `direct_answer_hint` property to `UnifiedDetectionResult` dataclass
- Hook sets `context.data["remaining_budget"] = 20000` and `context.data["direct_answer_hint"]`

### 2. llm_behavior_contract.md (line 17)
- Strengthened direct-answer rule to explicitly require first-sentence direct answers

### 3. reasoning_mode_selector.py (budget guard at line 67-76)
- Budget guard: skips if `budget < 400`; appends to `skipped_budget`
- Budget decrement after injection

### 4. cognitive_enhancers.py (budget guard at lines 434-442)
- Budget guard: skips if `budget < 400`; appends to `skipped_budget`
- Budget decrement before return

### 5. testing_strategy_router.py (budget guard at lines 95-103)
- Budget guard: skips if `budget < 250`; appends to `skipped_budget`
- Budget decrement before return

### 6. UserPromptSubmit.py (budget trace logging at lines 380-406)
- Appends budget trace to `logs/diagnostics/ups_budget_trace.jsonl`

## Key Design Decisions

1. **Tiered fixed budgets (model-free):**
   - SAFETY_MODULES = behavior_contract, operating_rules, verify_before_claim, truthfulness_gate → skip budget check
   - CONDITIONAL_MIN = 400 (reasoning_mode_selector, cognitive_enhancers)
   - NICE_MIN = 250 (testing_strategy_router)

2. **Fail-open**: Missing `remaining_budget` → assume unlimited (20000 default)

3. **Char counts only** (simpler than token estimation)

4. **Budget flow**: `unified_detection` initializes at 20000; conditional modules decrement; trace logged at end

## Specific Code to Review

### unified_detection.py — direct_answer_hint property
```python
@property
def direct_answer_hint(self) -> bool:
    """Concrete question needing direct first-sentence answer."""
    return (
        self.intent_classification in ("diagnostic", "meta_rca")
        or any(p in self.matched_profiles for p in ("debug_rca", "tradeoff_decision"))
    )
```

### reasoning_mode_selector.py — budget guard
```python
try:
    # Budget guard
    SAFETY_MODULES = {"behavior_contract", "operating_rules", "verify_before_claim", "truthfulness_gate"}
    _mod_name = "reasoning_mode_selector"
    if _mod_name not in SAFETY_MODULES:
        budget = context.data.get("remaining_budget", 20000)
        min_chars = 400
        if budget < min_chars:
            context.data.setdefault("skipped_budget", []).append(_mod_name)
            return HookResult.empty()
```

### testing_strategy_router.py — budget decrement
```python
injection_text = _build_injection(style)
# Update remaining budget
context.data["remaining_budget"] = budget - len(injection_text)
return HookResult(context={"additionalContext": injection_text})
```

### UserPromptSubmit.py — budget trace logging
```python
# Budget trace logging
_TRACE_LOG = HOOKS_DIR / "logs" / "diagnostics" / "ups_budget_trace.jsonl"
try:
    _TRACE_LOG.parent.mkdir(parents=True, exist_ok=True)
    final_budget = data.get("remaining_budget", "unknown")
    total_injected = sum(len(i) for i in injections) if injections else 0
    skipped = data.get("skipped_budget", [])

    trace = {
        "turn_id": data.get("turn_id", "unknown"),
        "initial_budget": 20000,
        "final_budget": final_budget,
        "total_injected_chars": total_injected,
        "modules_skipped_budget": skipped,
        "safety_tier_fired": data.get("_safety_tier_count", 0)
    }
    with open(_TRACE_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(trace) + "\n")
except Exception:
    pass
```