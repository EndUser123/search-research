# Handoff — ship-py pi dispatch: pi_not_found despite correct binary resolution

## Status
OPEN — investigation needed in `validator_dispatch.py`

## Objective

The ship-py v2.5 trace phase (and cross-validate phase) report `"reason": "pi_not_found"` when dispatching to a cross-family model via the `pi` CLI. However, `_PI_BINARY = shutil.which("pi")` correctly resolves to `pi.CMD` on this Windows host, and `subprocess.run([pi.CMD, ...])` succeeds (exit 0, stdout "0.82.1"). The failure must be in a separate resolution path.

## What's known

### Verified facts (with receipts)
- `shutil.which("pi")` = `C:\Users\brsth\AppData\Roaming\npm\pi.CMD` (receipt: `P:/tmp/diagnose_pi.py`, session 019fdf3c)
- `subprocess.run(["C:\...\pi.CMD", "--version"])` = exit 0, stdout "0.82.1" (receipt: `P:/tmp/diagnose_pi2.py`)
- `_PI_BINARY = shutil.which("pi") or "pi"` at `dispatch_base.py:36` resolves correctly
- The ship-py output showed `"reason": "pi_not_found"` for both cross-validate and trace phases
- `pi --version` from PowerShell returns `0.82.1`

### What's NOT the cause
- NOT a `.ps1` vs `.CMD` issue — `shutil.which` returns `.CMD` (verified)
- NOT a missing binary — pi exists and works from both PowerShell and Python subprocess
- NOT a `shell=True` issue — `.CMD` files execute directly via `subprocess.run` without shell

## Where to investigate

The `pi_not_found` error string likely originates in `validator_dispatch.py` (NOT `dispatch_base.py`). The dispatch chain is:

```
dispatch_base.py:try_orchestrator_dispatch()
  → validator_dispatch.py:select_validator_model(lane="critic")
  → validator_dispatch.py:resolve_pi_invocation(receipt)
  → subprocess.run([pi_binary, ...])
```

The failure is likely in one of:
1. `select_validator_model()` — returns a model the pi provider doesn't support, causing pi to exit non-zero
2. `resolve_pi_invocation()` — returns None for the selected model (provider/model mismatch)
3. `_classify_pi_error()` — classifies a non-binary-not-found error as "pi_not_found"

## Acceptance criteria

- `pi_not_found` root cause identified with a tool-call receipt (not inference)
- Either fixed OR documented as a known limitation with a workaround

## Files to read first

1. `C:/Users/brsth/.grok/skills/ship-py/__lib/validator_dispatch.py` — `resolve_pi_invocation()`, `select_validator_model()`, `_classify_pi_error()`
2. `C:/Users/brsth/.grok/skills/ship-py/__lib/dispatch_base.py` — `try_orchestrator_dispatch()`, `invoke_scan()`
3. `C:/Users/brsth/.grok/skills/ship-py/__lib/phases/trace.py` — `cmd_trace()`, `_try_orchestrator_trace_scan()`

## Provenance

- Source: AAR second pass (session 019fdf3c, 2026-08-09) — uncaptured knowledge section
- Wiki: [[tool-mismatch-confabulation-using-wrong-tool-output]]
- Prior fix: commit `07ac6e7` ("ship-py: fix pi PATH resolution + add provenance gate")
