---
title: "Shared dispatch component — deep module pattern for fleet model dispatch"
date: 2026-08-11
tags: [deep-module, dispatch-component, pi-dispatch, retry, telemetry, concurrency, abstraction, root-cause]
provenance:
  source: session 019fdf47
  trigger: "operator asked 'shouldn't our reusable functions not need ship-py to retry?'"
  verified: 2026-08-11
---

# Shared dispatch component — deep module pattern

## The pattern

Fleet model dispatch (PI, HTTP, opencode) involves five concerns that every caller would otherwise duplicate:

1. **Binary resolution** — `shutil.which("pi")` on Windows (`.cmd` shims)
2. **Provider mapping** — registry slug → PI provider name
3. **Model selection** — `pick_model.py` receipt
4. **Retry on transient failure** — re-select different model on 429/timeout
5. **Telemetry logging** — record to `usage.db` for circuit breaker
6. **Concurrency** — acquire/release slots per provider ceiling

The deep-module solution: one `pi_dispatch.py` (or `model_dispatch.py`) module absorbs all six concerns. Callers get:

```python
result = pi_dispatch.dispatch(prompt, lane="critic", effort="medium")
# result.success, result.content, result.model_used, result.retries, result.warnings
```

The caller notes `result.model_used` for provenance (may differ from initial pick after retry) but writes zero retry/telemetry/concurrency code.

## Why this matters

Without the shared component, each caller writes its own dispatch path:

| Caller | Had its own dispatch? | Problems |
|--------|----------------------|----------|
| `pool_test._call_via_pi` | Yes | No retry, no telemetry, WinError 2 bug |
| `ship-py.dispatch_base.invoke_scan` | Yes | No retry, no telemetry logging for circuit breaker |
| Future caller | Would write another | Same bugs recur |

Every new caller that writes `subprocess.run(["pi", ...])` gets:
- No retry on transient failure (429 → skip to fallback)
- No telemetry (circuit breaker never learns)
- No concurrency tracking (provider ceiling bypassed)
- Same Windows binary-resolution bug

## Enforcement

A PreToolUse hook (`PreToolUse_code_pattern_checks.py` Pattern 4) detects direct `subprocess.run(["pi"` or `subprocess.run(["opencode"` in `.py` files and WARNS:

```
[CODE PATTERN CHECK] Direct PI/opencode subprocess bypasses shared dispatch.

Anti-pattern:  subprocess.run(['pi', '-p', '--provider', 'nvidia-nim', ...])
Pattern:       from pi_dispatch import dispatch
               result = dispatch(prompt, lane='critic', effort='medium')
```

The canonical implementation files (`pi_dispatch.py`, `model_dispatch.py`) are exempt.

## The general principle

This is the [[design-codebase]] "depth" principle applied to fleet infrastructure:

- **Module**: `pi_dispatch.py`
- **Interface**: `dispatch(prompt, lane, effort) → DispatchResult` (simple, 3 params)
- **Depth**: 6 concerns absorbed internally (binary, provider, selection, retry, telemetry, concurrency)
- **Seam**: the `DispatchResult` dataclass — callers depend on the interface, not the implementation

The alternative (shallow modules with retry in each caller) violates DRY: the retry logic, telemetry logging, and concurrency tracking would be copy-pasted into every caller. Adding a new concern (e.g., circuit breaker quarantine) would require touching every caller instead of one module.

## When to apply this pattern

Any shared infrastructure concern that callers would otherwise duplicate:

| Infrastructure concern | Shared module | Anti-pattern |
|------------------------|-------------|-------------|
| PI/opencode dispatch | `pi_dispatch.py` | `subprocess.run(["pi", ...])` in callers |
| Model selection | `pick_model.py` | Direct registry reads in callers |
| Telemetry | `telemetry.log_call()` | Direct SQLite writes in callers |
| Concurrency tracking | `concurrency_gate.py` | Direct counter manipulation |
| Quota checking | `capacity_adapter.py` | Direct cache reads |

The test: if three or more callers would write the same 10+ lines of boilerplate, extract a shared module.

## Reference implementation

`~/.grok/skills/model-quota/scripts/pi_dispatch.py`:
- `dispatch()` — public interface (one function, 7 params, returns DispatchResult)
- `_select_model()` — calls pick_model.py
- `_fire_pi()` — single PI subprocess call
- `_classify_pi_error()` — determines retry vs permanent failure
- `DispatchResult` — dataclass with success, content, model_used, retries, warnings

7 unit tests in `test_pi_dispatch.py` covering: transient retry, permanent no-retry, exhaustion, first-try success, binary missing, telemetry logging, model_changed property.
