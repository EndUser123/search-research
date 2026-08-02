---
title: "close_runner.py receives full session_id JSON literal as session_dir arg (WinError 123)"
created: 2026-08-01
source: session-019fbf02-d3dd-7f72-9ad2-4538790c0a82
tags: [close-runner, close-check, json-parsing, windows-filename, bug, capture-gap]
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - P:/.claude/scripts/close_runner.py (or wherever close_runner lives — to be confirmed)
  - Chat transcript (close-check Phase 1 traceback, session 019fbf02)
  - Signal: close-gates: [SESSION] close_runner.py crash: OSError [WinError 123] invalid filename syntax
relations:
  - target: wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md
    type: related
  - target: wiki/concepts/python-m-ruff-swallows-stdout-in-powershell.md
    type: parallel (Windows host-specific tooling bug, surfaced as "tool broken" but actually invocation bug)
---

# close_runner.py receives full session_id JSON literal as session_dir arg (WinError 123)

## What happened

During session 019fbf02 close-check Phase 1, `close_runner.py` crashed with:

```
OSError: [WinError 123] The filename, directory name, or volume label syntax is incorrect:
'P:\\.artifacts\\close-evidence\\{"session_id": "019fbf02-d3dd-7f72-9ad2-4538790c0a82",
"session_start": "2026-08-01T14:27:41", "model_a": "minimax-m3", "model_b": "or-ling-3-flash-free",
"model_c": "minimax-m3"}'
```

The runner received the **full JSON literal** (an object containing session_id, session_start, model_a/b/c) as a single argument named `session_dir`, then tried to treat it as a filesystem path. Windows rejects the `{`, `}`, `:`, `,` characters in path syntax → exit code 1, no gate output produced.

## Root cause

The dispatcher upstream of close_runner passed a structured session-metadata object as a positional arg where the runner expects a directory path. Two failure modes overlap:

1. **Type confusion** — caller treated the session record (object/dict) as a string directory path
2. **No schema validation** at the boundary — close_runner did not assert `isinstance(session_dir, (str, Path))` and did not validate the path syntax before using it

The 32-character UUID-shaped `session_id` is the only meaningful path component. The full record was passed when only the ID string was expected.

## Why it matters

- **Captures an entire session-close attempt as 0 signal.** close-gates gate fails with crash, not with content. Operator sees "session failed" but cannot distinguish "your code is wrong" from "your gate definition is wrong" from "your runner is broken."
- **Recurring class.** This is the same pattern as the 2026-08-01 `serde-broken-false-positive-sweep` (apparent tool failure caused by upstream arg shape, not by tool itself).
- **Plausible-narrative trap.** "close_runner is broken" is a plausible narrative; the receipts show the runner is fine when given a string path.

## Solution

Two-layer fix:

### 1. Defensive boundary check (in close_runner.py)

```python
def run_close(session_dir: str | Path) -> CloseResult:
    p = Path(session_dir) if isinstance(session_dir, str) else session_dir
    if not isinstance(p, (str, Path)):
        raise TypeError(f"session_dir must be str|Path, got {type(session_dir).__name__}: {session_dir!r}")
    if not p.name or any(c in str(p) for c in '{}[]:,'):
        raise ValueError(f"session_dir contains invalid path characters: {p!r}")
    p.mkdir(parents=True, exist_ok=True)
    ...
```

### 2. Upstream call site fix

The dispatcher (whichever script invokes close_runner) must extract `session_id` from the session record before passing:

```python
# WRONG — passes whole dict/JSON literal
runner.run_close(session_record)

# RIGHT — extracts id string
runner.run_close(session_record["session_id"])
```

## Applies to

Any subagent or skill that takes a session identifier as input. The pattern: **pass primitive (str/Path), not struct (dict/JSON literal)**. Especially at CLI/script boundaries where type checking is absent.

## Verification

To verify the fix, run close_runner with a deliberate malformed arg and confirm it raises TypeError or ValueError *before* OSError — the descriptive exception message should name the offending argument, not produce an OS-level path error.

## Rule

When a runner CLI receives structured data where it expects a path/identifier, validate the type at the boundary. A Path constructor that fails silently (Python lets `Path("{...}")` succeed) is the same failure class as a JSON arg parsing bug — both produce an OSError downstream that the operator reads as "the tool is broken."

## Related

- `P:/.data/wiki/concepts/serde-broken-false-positive-sweep-20260801.md` — same class (apparent tool failure, actually upstream arg shape)
- `P:/.data/wiki/concepts/python-m-ruff-swallows-stdout-in-powershell.md` — parallel: "tool broken" claim that turned out to be an invocation wrapper bug
- `P:/.data/wiki/concepts/close-check-invokes-capture.md` — close-check workflow context
