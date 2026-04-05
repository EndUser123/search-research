# Preflight and Severity Split (2026-02-11)

## Goal
Reduce stop-hook churn by pushing evidence discipline into pre-generation guidance, while preserving hard blocks for truly unsafe behavior.

## Preflight Prompt (Injected at UserPromptSubmit)
```
EMPIRICAL PRECHECK REQUIRED (before final answer)

Your response is likely to contain verifiable claims. Use this format:

1) Observed:
- Facts directly seen in tool output only.
- For each failure pattern, cite at least one concrete example:
  <test_or_file>: <exact error or state>

2) Inferred:
- Conclusions derived from observed evidence.
- Mark as inference, not fact.

3) Unknown:
- Anything not yet verified.
- Do not present unknowns as causes.

Hard rule:
- Every causal claim ("because", "root cause", "most failures are X") must be
  backed by at least one observed traceback/log line in the same response.
```

## Severity Split
### Keep Hard Block
- Stop hook evidence mismatch (`SCOPE_MISMATCH`, unverified causal claims).
- Unparseable command gate for direct injection patterns:
  - `eval(...)`
  - `exec(...)`
  - complex `$()` command substitution

### Warn + Rewrite Guidance
- Shell complexity gate (already warn-only).
- Unparseable mutation patterns (opaque `python -c` file/config writes) when:
  - `UNPARSEABLE_MUTATION_MODE=warn`

Warning guidance should redirect to:
- `Write` / `Edit` / `apply_patch`
- explicit shell file operations with clear paths

## Config Knobs
Set in `P:\.claude\settings.json` under `env`:

```json
"EMPIRICAL_CLAIMS_PRECHECK_ENABLED": "true",
"UNPARSEABLE_MUTATION_MODE": "warn"
```

To restore stricter mutation enforcement:
```json
"UNPARSEABLE_MUTATION_MODE": "block"
```
