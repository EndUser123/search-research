---
name: hooktimer-shared-phase-timing-pattern
description: >
  Reusable design pattern for adding phase-level timing instrumentation to any
  hook on Grok Build. A shared 94-line module (_hook_timing.py) provides
  fail-safe timing with rotation, imported via try/except so the hook works
  even if the module is missing. 8/8 hooks on this host are now instrumented.
  Generalizes beyond Stop hooks — works for UserPromptSubmit and any future
  hook type.
tags: [hooks, observability, pattern, timing, fail-safe]
last_verified: 2026-08-08
host_applicability: both
---

# HookTimer shared phase-timing pattern

## The problem

When a hook times out or produces unexpected behavior, there is no
forensic data showing which phase was slow. The operator sees "exit code 1
(236ms)" but cannot determine what happened inside the hook without
re-reading the source and reasoning about execution paths.

## The pattern

A shared module (`~/.grok/hooks/scripts/_hook_timing.py`, 94 lines)
provides:

1. **`HookTimer.start(hook_name, session_id)`** — creates a timer, returns
   `None` if the state dir is unwritable (fail-safe)
2. **`HookTimer.phase(name)`** — logs elapsed_ms since start for the named
   phase, writes one JSONL line to `~/.grok/hooks/state/<hook>-timing.jsonl`
3. **Rotation at 10MB / 5000 lines** — one rotated copy (`.jsonl.1`)
4. **All methods swallow errors** — timing is best-effort, never blocks the hook

## Integration (5 lines per hook)

```python
# At top of hook file, after stdlib imports:
try:
    _hooks_scripts = Path(__file__).resolve().parent / "scripts"
    if str(_hooks_scripts) not in sys.path:
        sys.path.insert(0, str(_hooks_scripts))
    from _hook_timing import HookTimer
except Exception:
    HookTimer = None

# In main():
_t = HookTimer.start("<hook-name>", session_id) if HookTimer else None

# At each phase checkpoint:
if _t: _t.phase("phase_name")
```

The `if _t:` guard means every phase call is a no-op when HookTimer is
unavailable. The hook continues to work normally.

## Phase naming convention

| Phase | When | Example |
|-------|------|---------|
| `stdin_parsed` | After JSON parse | Hook received valid input |
| `prompt_extracted` / `text_extracted` | After extracting the relevant data | Text ready for checking |
| `skills_found` / `violations_checked` | After the main work | Findings produced |
| `done` | Before exit | Final phase |
| Early exits | `parse_failed`, `no_prompt`, `no_skills_detected`, `terminal_output_skipped` | Short-circuit paths |

## Fleet coverage (as of 2026-08-08)

8/8 hooks instrumented:

| Hook | Type | Phases |
|------|------|--------|
| behavioral_check | Stop | stdin_parsed, text_extracted, violations_checked, done |
| Stop_creative_nudge | Stop | stdin_parsed, done |
| Stop_claim_judge | Stop | stdin_parsed, text_extracted, done |
| minimal_bias_gate | Stop | stdin_parsed, text_extracted, done |
| dbr_language_check | Stop | stdin_parsed, text_extracted, done |
| close_enforcement_gate | Stop | stdin_parsed, done |
| notice_trigger_hook | Stop | stdin_parsed, done |
| UserPromptSubmit_skill_precheck | UserPromptSubmit | stdin_parsed, prompt_extracted, skills_found, checks_done, done + 4 early-exit |

## Why this works

- **Fail-safe by design**: the hook never depends on HookTimer being
  available. If the module is deleted, corrupted, or the import path
  changes, the hook continues to function — timing data is simply absent.
- **One line per phase**: adding instrumentation to a new hook requires
  ~5 lines of boilerplate + one `if _t: _t.phase(...)` call per checkpoint.
- **JSONL format**: each phase is a separate line, so `Get-Content -Tail N`
  shows recent invocations. No JSON parsing needed for quick inspection.
- **Session-scoped**: each log entry includes the session ID (first 8 chars),
  so concurrent sessions' timing data is distinguishable.
- **Rotation prevents unbounded growth**: 10MB threshold with one rotated
  copy keeps total storage under ~20MB per hook.

## Design decisions

- **No aggregation in the module**: each phase writes a separate line.
  Aggregation (total time, slowest phase) is done at read time by grepping
  the JSONL. This keeps the module simple (94 lines) and avoids stateful
  complexity.
- **mtime-based session ID fallback**: when `GROK_SESSION_ID` is not set,
  the caller resolves it from the most-recently-modified transcript. This
  is fragile under concurrent sessions (see
  [[multi-terminal-isolation-stale-data-immunity]]) but only affects
  timing data, not hook behavior.
- **Append-only, not atomic**: Windows append-mode doesn't guarantee
  atomicity, but with ~100 bytes per line and low write frequency (one
  hook invocation per user prompt), interleaving probability is negligible.

## Falsifier

This pattern is wrong if:
- The timing data is never used (operators never grep the JSONL files)
- The fail-safe import masks real import failures that would otherwise be
  caught and fixed
- The JSONL files grow unbounded despite rotation (rotation logic is buggy)
- The phase names are too generic to diagnose anything ("done" doesn't
  help if the timeout happened between "text_extracted" and "done")

## Provenance

Built 2026-08-08 from:
- AAR session 019fde37 (O2: phase-timing instrumentation as standard)
- The operator's directive: "It should be a standard" (referring to all
  hooks having timing)
- The `quality_nudge.py` / `quality-nudge-timing.jsonl` pattern that
  already existed for one hook — generalized into a shared module
- Reference incident: skill-precheck exit code 1 with no diagnostic data
  available because the hook had zero observability logging
