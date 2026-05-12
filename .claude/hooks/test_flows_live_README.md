# Phase 2 Local-Summary Guidance — Behavior Spec

## Two Enforcement Paths

| Mode | Verdict | Guidance Mechanism | Trigger Condition |
|------|---------|-------------------|-------------------|
| `warn` (default) | `warn` | Inline advisory display | unsupported_fact → `decide_from_issues` downgrades block→warn at line 1066 |
| `block` (`--epistemic-strict`) | `block` | Guidance marker → UPS one-turn injection | Same issue, mode override preserves block |

**Root cause**: `decide_from_issues` (epistemic_validator.py:1066):
```python
if cfg.mode == "warn" and worst == "block":
    worst = "warn"
```
This fires BEFORE the policy table override and before the guidance-marker branch check at Stop.py:551.

## How Phase 2 Works in Practice

### Default (`EPISTEMIC_CONTRACT_MODE=warn`)

1. Model gives analytical response with unsupported claim, no citation
2. `validate()` → `unsupported_fact` issue found → `decide_from_issues` returns `warn` (not `block`)
3. **No guidance marker written** (Stop.py:551 requires `verdict.decision == "block"`)
4. Advisory shown inline via Stop.py:623 — model sees the tip inline
5. Model self-corrects on next turn using link phrase (e.g., "From the pytest run above...")
6. `_is_locally_grounded_summary` passes → `allow`

### Strict (`--epistemic-strict` in prompt, or `EPISTEMIC_CONTRACT_MODE=block`)

1. Model gives analytical response with unsupported claim, no citation
2. `validate()` → `unsupported_fact` issue found → `decide_from_issues` returns `block`
3. **Guidance marker written** to `state/local_summary_guidance/guidance__{session}__{terminal}.json`
4. UPS reads marker on next turn, self-deletes, injects as `additionalContext`
5. Model uses link phrase + 2+ overlap words → passes

## Why the Marker Path Exists

The marker is for **high-stakes or explicit-context turns** where:
- The user wants hard enforcement (strict mode)
- The advisory-only path might be ignored by the model
- The one-turn marker ensures the guidance is not just inline but injected as a separate context signal

The advisory display is the **primary mechanism** for warn mode; the marker is a **reinforced path** for block mode.

## Negative Control

Local-summary guidance MUST NOT trigger when `tool_transcript` is empty. The check at `build_local_summary_guidance` (epistemic_validator.py:561):
```python
if not tool_transcript:
    return ""
```
This prevents guidance from leaking into non-tool analytical responses.

## Running the Tests

```bash
python "P:\.claude\hooks\test_flows_live.py"
```

Expected output: ALL PASS (4/4)

## Adding New Test Cases

When adding a new flow, specify:
1. **Mode**: `warn` (default) or `block`
2. **Response**: The exact text that triggers the issue
3. **Expected verdict**: `block`, `warn`, or `allow`
4. **Expected mechanism**: advisory-inline, marker-written, or bypass-pass

The test file is the authoritative executable spec — if behavior diverges, update this README.
