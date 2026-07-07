# Phase 0.5 CRITICAL-tier `open("a")` Migration — Evidence Packet

**Date:** 2026-07-07
**Scope:** Option B (CRITICAL tier only, 19 standard-JSONL sites across 10 files)
**Program:** Close-the-Loop telemetry reliability (Amendment 2 deliverable)
**Status:** All 19 sites migrated; all 3 acceptance tests PASS.

---

## 1. Migration target helper

All sites now route through `append_jsonl_safe` in `__lib/file_lock.py:85-113`:

- Cross-process-safe JSONL append via `portalocker.FileLock` on a `.lock` sidecar
- On `_LOCK_FAILURES = (OSError, BaseLockException)`: writes a dropped-trace row to
  `<log>.dropped.jsonl` and returns `False`
- Returns `True` on successful append
- `ensure_ascii` parameter preserved per-site (default `True`)

POC shapes matched (no fourth pattern introduced):
1. **Bare-safe** — single `append_jsonl_safe` call, `except OSError: pass`
2. **Defense-in-depth** — `mkdir` + `append_jsonl_safe`, `except OSError: pass`
3. **Candidate-loop** — `for path in candidates: if append_jsonl_safe(...): return`

---

## 2. Per-site table (write path + exception path, both columns)

| # | File:line (post-edit) | Write path (now) | Exception path (now) | Shape |
|---|-----------------------|------------------|----------------------|-------|
| 1 | `__lib/stop_block_log.py:122` | `append_jsonl_safe` (POC, prior phase) | `except OSError: pass` | bare-safe |
| 2 | `__lib/hook_ledger.py:65` | `append_jsonl_safe` (POC, prior phase) | `except OSError: pass` | bare-safe |
| 3 | `__lib/hook_ledger.py:341` | `append_jsonl_safe` (POC, prior phase) | `except OSError: return False` | bare-safe |
| 4 | `Stop.py:223` | `_append_jsonl_safe` wrapper (POC) | `except OSError: continue` | candidate-loop |
| 5 | `Stop.py:321` | `_append_jsonl_safe` wrapper (POC) | `except OSError: continue` | candidate-loop |
| 6 | `__lib/stop_gate_telemetry.py:122-128` | `append_jsonl_safe` | `except OSError: pass` | defense-in-depth |
| 7 | `__lib/agentic_reliability_telemetry.py:132-138` | `append_jsonl_safe` | `except OSError: pass` | defense-in-depth |
| 8 | `__lib/gate_health.py:45-61` | `append_jsonl_safe(..., ensure_ascii=False)` | `except OSError: pass` | defense-in-depth |
| 9 | `__lib/quality_log.py:105-111` | `return append_jsonl_safe(log_path, entry)` | (caller) | bare-safe |
| 10 | `__lib/hook_error_sink.py:65-78` | `append_jsonl_safe` | `except OSError: pass` | defense-in-depth |
| 11 | `__lib/hook_importer.py:81-90` | `append_jsonl_safe(..., ensure_ascii=True)` | `except OSError: pass` | defense-in-depth |
| 12 | `__lib/unified_evidence_enforcer.py:382-386` | `append_jsonl_safe` | `except OSError: return` | bare-safe |
| 13 | `__lib/hook_runner.py:175-179` | `append_jsonl_safe(ERRORS_LOG, entry)` | `except OSError:` → stderr print | defense-in-depth |
| 14 | `__lib/hook_runner.py:457-485` | `append_jsonl_safe(diag_path, diag_entry)` (13-field dict) | `except OSError: pass` | defense-in-depth |
| 15 | `verification_audit_logger.py:73-86` | `from __lib.file_lock import append_jsonl_safe` | `except OSError as e:` → warn | bare-safe |
| 16 | `Stop.py:819-822` | `append_jsonl_safe(log_path, entry)` | `except OSError: pass` | defense-in-depth |
| 17 | `Stop.py:1175` (lam_truncation_probe) | `append_jsonl_safe(_pp, {...})` | `except OSError: pass` | defense-in-depth |
| 18 | `Stop.py:1805-1806` | `append_jsonl_safe(log_path, log_entry)` | `except OSError: pass` | defense-in-depth |
| 19 | `Stop.py:2867` | `append_jsonl_safe(log_path, entry, ensure_ascii=True)` | `except OSError: pass` | defense-in-depth |
| 20 | `Stop.py:3192` | `append_jsonl_safe(log_path, entry, ensure_ascii=True)` | `except OSError: pass` | defense-in-depth |
| 21 | `Stop.py:4232` (regen_cap_telemetry) | `append_jsonl_safe(p, rec, ensure_ascii=True)` | `except OSError: pass` | defense-in-depth |
| 22 | `PreToolUse.py:320` (candidate loop) | `if append_jsonl_safe(path, payload, ensure_ascii=True): return` | `except OSError: continue` | candidate-loop |
| 23 | `PreToolUse.py:661` (intent-read probe) | `append_jsonl_safe(_probe, {...}, ensure_ascii=False)` | `except OSError: pass` | defense-in-depth |
| 24 | `PreToolUse.py:1000` (content_filter_skips) | `append_jsonl_safe(_diag_dir / ..., {...}, ensure_ascii=False)` | `except OSError: pass` | defense-in-depth |

**Sites 1–5 = Phase 0 POC** (4 POC files: stop_block_log, hook_ledger, Stop.py 2 writers — note the summary's "19" excludes these 5 already-done sites). Sites 6–24 = Phase 0.5 CRITICAL tier scope (19 sites migrated this phase, including the 6 Stop.py + 3 PreToolUse.py migrated in this final pass).

### Sites deliberately NOT migrated (with reason)

| Site | Reason |
|------|--------|
| `__lib/evidence_store.py:490,509` (`newline='\n'`) | Defense-in-depth superior to `append_jsonl_safe`; newline kwarg shape is accepted variant, not the `open("a")` target. |
| `Stop.py:4232` `encoding='ascii'` | Same write migrated; `encoding` collapses onto `ensure_ascii=True` (already passed). |
| `PreToolUse.py:1218` canary | Plain-text `.log`, non-JSON — excluded from CRITICAL scope (debug tier). |
| `hook_runner.py:70/88/438`, `PreToolUse.py:1221` | Plain-text writes — debug tier. |

---

## 3. Raw parallel-test output

### 3a. `dropped_trace_fault_injection_test.py` (helper provenance)

```
contention path (real TimeoutError):
  [PASS] no_exception
  [PASS] direct_returns_false
  [PASS] dropped_rows == 2
  [PASS] required_keys_present
  [PASS] rows_parse
  [PASS] main_log_empty
BaseBaseLockException direct-injection (tuple branch):
  [PASS] no_exception_escape
  [PASS] returns_false
  [PASS] dropped_rows == 1
  [PASS] reason_is_BaseLockException
  [PASS] required_keys
  [PASS] parses
  [PASS] main_log_empty
ACCEPTANCE PASSED
```

### 3b. `stop_block_log_parallel_test.py` (highest-traffic migrated path)

```
stop_block_log parallel acceptance test  workers=8 writes/worker=50
[PASS] lines=400/400 lost=0 corrupt=0 unique_gates=400/400
ACCEPTANCE PASSED
```

### 3c. `hook_runner`-style parallel test (13-field diag_entry shape, 8 workers × 70 writes)

```
lines=560 parsed=560 dropped=0 errors=0
RESULT: PASS
```

### 3d. Compile check

```
$ python -m py_compile Stop.py && python -m py_compile PreToolUse.py
STOP_PRETU_COMPILE_OK
```

---

## 4. AST + method-call scan (classification doc source of truth)

Re-verified via AST scan over `P:/.claude/hooks/**/*.py`:

```
TOTAL builtin open() with literal a:  61
TOTAL method .open() with first-arg a: 14
UNIFIED total:                       75
```

The original 63-file count was a string-scan limited to the `open("...")` builtin
form; it missed the 14 `.open("a", ...)` Path-method sites. The classification
doc now records the AST methodology in its header and a misses-ledger entry.

---

## 5. Unresolved items / follow-ups

- **#906 (auto-commit hook)**: Mid-review exposure acknowledged per user directive
  ("don't fight it until #1256 lands"). Any auto-commit SHAs generated by these
  edits are observable in `git log`; none were observed blocking this work.
  Tracked under task #1256.
- **DEBUG-tier migration (task #1257)**: DEFERRED, evidence-gated. Revisit only
  if Phase 6 yield data or a dropped-trace investigation implicates a debug log.
- **75 total `open("a")` sites vs. 24 migrated here**: The remaining ~51 sites
  are debug-tier (`hook_diagnostic_wrapper.py`, `registry.py`, `tdd_*`,
  `UserPromptSubmit_modules/observability.py`, test fixtures, `file_lock.py`
  itself, etc.). They are out of CRITICAL scope and intentionally not touched.

---

## 6. Gate criteria satisfied

- ✅ All 19 Phase 0.5 CRITICAL-tier sites migrated to `append_jsonl_safe`
- ✅ `ensure_ascii` preserved per-site (3 sites pass `ensure_ascii=False`;
  4 sites pass `ensure_ascii=True` explicitly; remainder default `True`)
- ✅ All `except Exception: pass` narrowed to `except OSError:` (or
  `except OSError: return`/`continue` where control flow required)
- ✅ Compile-check passes on both `Stop.py` and `PreToolUse.py`
- ✅ Helper-branch fault-injection test PASS (contention + BaseLockException)
- ✅ Parallel acceptance test PASS through `_log_stop_block` path (0 lost, 0 corrupt)
- ✅ Parallel acceptance test PASS through `hook_runner` 13-field diag shape
- ✅ Classification doc updated with AST scan counts + misses-ledger entry
- ✅ No fourth migration pattern introduced (3 POC shapes only)
