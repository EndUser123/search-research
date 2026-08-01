---
thread_id: fleet-code-bugs-2026-07-24
parent_handoff_path: none
current_session_id: 019f91d3-2741-7f83-af68-211796180474
current_terminal_id: console_b7ba7bf3-2403-437a-b44a-c5c9
produced_at: 2026-07-24T21:05:00Z
status: open
handoff_type: implementation
accurate_as_of_head: non-git-session
---

# Fleet code bugs: DeepSeek serialization + telemetry connection leak

## Objective

Fix two code bugs found during this session's /review and runtime testing:
(1) DeepSeek V4 Flash fails via spawn_subagent with serialization error,
and (2) telemetry log_call() leaks SQLite connections on error paths.

## Status

OPEN — both identified with root cause, not fixed.

## Read-first list

1. `C:/Users/brsth/.grok/skills/model-benchmark/scripts/telemetry.py` — log_call() connection lifecycle
2. `P:/docs/handoffs/routing-library/HANDOFF.md` — route.py should handle model fallback including the DeepSeek issue
3. `P:/.data/wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md` — domain table recommends DeepSeek for code-verification

## Task packets

### BUG-03: DeepSeek spawn_subagent serialization failure

- **Goal:** Investigate and resolve why `zen-deepseek-v4-flash-free` fails when passed as `model=` to `spawn_subagent`
- **Symptom:** `Session error: Internal error: "serialization error: missing field 'id' at line 1 column 214"` — subagent crashes at dispatch, 0 tool calls, exit 1
- **Evidence:** Subagent 019f9653-0016 failed at 2026-07-24T22:50:49Z. The /check skill was edited to use `model="zen-deepseek-v4-flash-free"` for verifiers; it crashed; the edit was reverted to omit the model parameter.
- **Scope of investigation:**
  - Is this a Grok Build serialization bug (model response format doesn't match expected schema)?
  - Is this a config.toml model definition issue (missing field in the model config)?
  - Is this specific to `zen-deepseek-v4-flash-free` or do other Zen models also fail?
  - Does `zen-mimo-v2-5-free` work via spawn_subagent? (It was not tested this session)
- **Impact:** the domain table recommends DeepSeek as the default for code-verification (2900ms, free, code-specialized). Without spawn_subagent support, every skill that wants to use the domain table's #1 recommendation is blocked.
- **Acceptance:** `spawn_subagent(model="zen-deepseek-v4-flash-free", ...)` completes without serialization error, OR root cause is identified and documented with a workaround
- **Falsifier:** DeepSeek still crashes via spawn_subagent after investigation

### BUG-04: Telemetry connection leak on error path

- **Goal:** Fix `log_call()` in telemetry.py to close SQLite connections on error
- **Root cause:** `conn = _get_conn()` opens a connection. If `conn.execute(...)` raises, the `except` blocks catch the error but `conn` is never closed. The connection leaks until GC collects it.
- **Evidence:** `/review` Finding 2 (static code analysis). Code flow: `_get_conn()` → `conn.execute()` (raises) → `except (sqlite3.Error, OSError, TypeError)` → `conn` never closed.
- **Fix:** Use try/finally:
  ```python
  conn = _get_conn()
  try:
      conn.execute(...)
      conn.commit()
  except (sqlite3.Error, OSError, TypeError) as e:
      print(f"telemetry warning: {type(e).__name__}: {e}", file=sys.stderr)
  finally:
      conn.close()
  ```
- **Acceptance:** connections are closed even when execute raises
- **Falsifier:** any connection leak after the fix (monitor with `sqlite3.connect().execute("PRAGMA database_list")` count)

## Hard constraints

- BUG-03 investigation must not break other models' spawn_subagent compatibility
- BUG-04 must not change log_call()'s public API signature

## Cross-reference couplings

- `routing-library` handoff — route.py needs to know which models work via spawn_subagent; BUG-03's resolution feeds into route.py's fallback chain
- `model-pool-selection-policy-speed-quota-diversity.md` — domain table recommends DeepSeek; BUG-03 blocks this recommendation

## Resumption protocol

1. BUG-04 first (2-minute fix — add try/finally to log_call)
2. BUG-03 second (investigation — test `spawn_subagent(model="zen-deepseek-v4-flash-free")` with a trivial prompt; test `zen-mimo-v2-5-free` to see if it's Zen-wide or DeepSeek-specific; check config.toml model definition for missing fields)

## Suggested next invocation

```
/go fix two fleet code bugs per P:/docs/handoffs/fleet-code-bugs/HANDOFF.md. BUG-03: investigate DeepSeek spawn_subagent serialization error. BUG-04: fix telemetry log_call() connection leak with try/finally.
```

## Last user message (verbatim)

> "/handoff for all the findings that are not already in handoff files."

## Epistemic labels

- [FACT] BUG-03: serialization error observed (subagent exit 1, 0 tool calls, error message captured)
- [FACT] BUG-04: connection leak identified by static analysis (code flow traceable)
- [UNKNOWN] BUG-03 root cause: could be Grok Build, config.toml, or model-specific. No investigation done.
- [INFERENCE] BUG-04 fix is safe (try/finally is standard Python resource management)
