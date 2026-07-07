# `open("a")` Write-Site Classification — 2026-07-07

**Purpose:** Phase 0 scope boundary for the Close-the-Loop telemetry-reliability
program (Amendment 2 deliverable). Classifies every file under `P:/.claude/hooks/`
that contains an `open(..., "a")` write into **critical / debug / evidence-scratch**,
so the Phase 0 POC and Phase 0.5 expansion have a committed target list — not a
re-derived one.

**Source list:** 63 files matched by `grep 'open([^)]*["'\'']a["'\''])'` over
`P:/.claude/hooks/` on 2026-07-07. This doc is that list, classified.

**Evidence-level key** (Language Precision Rules apply):
- **[READ]** = the write site was opened and the `open("a")` line + its enclosing
  `except` were inspected this session. Justification is direct.
- **[PATH]** = classified from path + `CLAUDE.md` architecture knowledge only; the
  site was NOT read this session. Every **[PATH]**-tagged critical site MUST be
  re-read before its migration in Phase 0.5 expansion — the classification is a
  hypothesis for these, not a verified fact.

**Provenance facts (verified 2026-07-07):**
- `append_jsonl(log_path, entry)` already exists at `__lib/file_lock.py:60`.
  Cross-process-safe via `portalocker` `FileLock` on a `.lock` sidecar. Raises
  `TimeoutError` (a subclass of `OSError`) on lock-exhaustion — callers narrow
  enclosing handlers to `OSError`, NOT to a bespoke `LockRetryExhausted`.
- `log_hook.py` lives at the **hook root** (`P:/.claude/hooks/log_hook.py`), NOT
  under `__lib/`. It carries its OWN retry scheme (`_retry_on_locked` +
  `LockRetryExhausted` + `O_EXCL` `get_lock`), distinct from `append_jsonl`.
  It is a migration candidate, not a reference implementation.
- Scope is **~25 critical sites across ~25 files**, not the "6" the original plan
  stated. The POC migrates 3; Phase 0.5 migrates the remainder.

---

## CRITICAL — verdict / block / telemetry / state logs

Loss or corruption of these writes breaks block attribution, RCA, retirement
decisions, or multi-terminal turn-state correctness. **Phase 0 + Phase 0.5 scope.**

### POC targets (Phase 0 — migrated this session)

| # | File:line | Writes | Exception path today | Evidence |
|---|-----------|--------|----------------------|----------|
| 1 | `__lib/stop_block_log.py:122` | `stop_blocks.jsonl` — THE canonical Stop-block log; sole source for retirement decisions per the 2026-07-06 addendum | `except Exception: pass` at L124 — **broad swallow, must narrow to `except OSError: pass`** (Amendment 1) | **[READ]** |
| 2 | `__lib/hook_ledger.py:65` | `hook_ledger_anomalies.jsonl` (`_log_anomaly`) | `except OSError: pass` at L77 — **already narrow** (`TimeoutError` ⊂ `OSError`); write-path migration only | **[READ]** |
| 2 | `__lib/hook_ledger.py:341` | `hook_ledger_spool/events_*.jsonl` (`_append_spool_record`) — turn-event fallback when SQLite unavailable | `except OSError: return False` at L344 — **already narrow**; write-path migration only | **[READ]** |
| 3 | `Stop.py:223` | `skill_first_enforcement.jsonl` (`_log_skill_first_stop_event`) — records each inline-bypass verdict (reason_code `E_SKILL_FIRST_INLINE_BYPASS`) | `except OSError: continue` in candidate loop at L226 — **already narrow**; write-path migration only | **[READ]** |
| 3 | `Stop.py:321` | `anti_sycophancy_violations.jsonl` (`_append_anti_sycophancy_log`) — records each anti-sycophancy verdict | `except OSError: continue` at L324 — **already narrow**; write-path migration only | **[READ]** |

**POC note:** Stop.py's `_log_stop_block_event` (def L230) does NOT use `open("a")` —
it calls `_log_hook_invocation` (the diagnostics-DB writer). Not a POC site.
Stop.py's remaining `open("a")` sites (827, 1183, 1813, 2875, 3200, 4240) are
*other* telemetry writes — they are critical but deferred to Phase 0.5 (below).

### Phase 0.5 targets (expansion — migrate only after POC diff pattern holds)

Each **[PATH]** row is a hypothesis pending read-verification at migration time.

| File:line(s) (approx) | Writes / why critical | Enclosing except (hypothesis) | Evidence |
|---|---|---|---|
| `Stop.py:827` | Stop telemetry write | unverified | **[PATH]** |
| `Stop.py:1183` | Stop telemetry write | unverified | **[PATH]** |
| `Stop.py:1813` | Stop telemetry write | unverified | **[PATH]** |
| `Stop.py:2875` | Stop telemetry write | unverified | **[PATH]** |
| `Stop.py:3200` | Stop telemetry write | unverified | **[PATH]** |
| `Stop.py:4240` | Stop telemetry write (`encoding="ascii"` — differs) | unverified | **[PATH]** |
| `__lib/stop_gate_telemetry.py:125` | per-gate decision telemetry — retirement join depends on it | unverified | **[PATH]** |
| `__lib/hook_runner.py:70,88,175,438,479` | `hook_runner_stderr.jsonl` failsafe + execution trace — last-resort RCA when imports/DB fail | unverified | **[PATH]** |
| `__lib/hook_error_sink.py:75` | error sink | unverified | **[PATH]** |
| `__lib/hook_importer.py:86` | importer diagnostics (`load`/`execute`/`timeout`/`stderr`) | unverified | **[PATH]** |
| `__lib/unified_evidence_enforcer.py:383` | evidence-enforcement verdict log | unverified | **[PATH]** |
| `__lib/agentic_reliability_telemetry.py:135` | reliability telemetry | unverified | **[PATH]** |
| `__lib/gate_health.py:55` | gate-health log | unverified | **[PATH]** |
| `__lib/quality_log.py:107` | quality log | unverified | **[PATH]** |
| `__lib/hook_diagnostic_wrapper.py` | diagnostic wrapper | unverified | **[PATH]** |
| `__lib/task_contract.py` | task-contract state | unverified | **[PATH]** |
| `log_hook.py:155,171` | `claude-log.jsonl` (`_append_log`, `_append_log_batch`) — has OWN retry scheme; migration retires `_retry_on_locked`/`LockRetryExhausted` in favor of `append_jsonl` | `except LockRetryExhausted` at L390 + `except Exception` at L395 | **[READ]** |
| `PreToolUse.py` | verify at migration time — may log blocks | unverified | **[PATH]** |
| `PostToolUse_router.py` | verify at migration time | unverified | **[PATH]** |
| `PostToolUse_artifact_access_tracker.py` | artifact-access tracking | unverified | **[PATH]** |
| `PostToolUse_e2e_tracker.py` | e2e tracking | unverified | **[PATH]** |
| `evidence_store.py` | evidence DB fallback | unverified | **[PATH]** |
| `verification_audit_logger.py` | verification audit | unverified | **[PATH]** |
| `recursive_failure_detector.py` | Catch-22 detection | unverified | **[PATH]** |
| `hook_tracker.py` | `log_block` — block tracking | unverified | **[PATH]** |
| `shared_utils.py` | `log_hook_event` — shared hook-event logger | unverified | **[PATH]** |
| `tdd_core.py` / `tdd_diagnostics.py` | TDD diagnostics | unverified | **[PATH]** |
| `telemetry/verification_metrics.py` | verification metrics | unverified | **[PATH]** |
| `posttooluse/skill_invocation_logger_hook.py` | skill-invocation log | unverified | **[PATH]** |
| `posttooluse/semantic_compress.py` | semantic-compress log | unverified | **[PATH]** |
| `posttooluse/fix_validator.py` | fix-validation log | unverified | **[PATH]** |
| `scripts/cks/quality_gate.py` | CKS quality-gate log | unverified | **[PATH]** |
| `PreToolUse_verification_modules/investigation_verification.py` | investigation-verification log | unverified | **[PATH]** |
| `UserPromptSubmit.py` | verify at migration time | unverified | **[PATH]** |
| `UserPromptSubmit_modules/registry.py` | verify at migration time | unverified | **[PATH]** |
| `UserPromptSubmit_modules/observability.py` | observability log | unverified | **[PATH]** |
| `UserPromptSubmit_modules/cks_context.py` | CKS context | unverified | **[PATH]** |
| `UserPromptSubmit_modules/task_start_contract_writer.py` | contract writer | unverified | **[PATH]** |
| `UserPromptSubmit_modules/subagent_enforcer.py` | subagent enforcement | unverified | **[PATH]** |
| `UserPromptSubmit_modules/competence_injector.py` | competence injection | unverified | **[PATH]** |
| `__lib/dx_tools_observability.py` | DX observability | unverified | **[PATH]** |
| `__lib/migrate_legacy_state.py` | one-shot migration (debug-critical during runs) | unverified | **[PATH]** |

---

## DEBUG — trace / probe logs (loss tolerable, corruption annoying)

Not Phase 0/0.5 scope unless a "non-critical" log later turns out to matter
(per Amendment 2: such a discovery becomes the misses-ledger's first entry).

- `__lib/file_lock.py:60` — this IS `append_jsonl` itself, not a bypasser. The helper, not a target.
- Any production trace/probe opt-in logs uncovered during Phase 0.5 read-verification get reclassified here or up to CRITICAL.

---

## EVIDENCE-SCRATCH — tests, archives, docs, plans (NOT production write paths)

Excluded from scope. Listed for completeness so the 63-file count reconciles.

**Tests** (assert on `open("a")` shape; migration would break them):
`tests/test_epistemic_validator.py`, `test_assumption_audit.py`, `tests/test_error_tagging.py`,
`test_read_pretooluse.py`, `test_precompact_input.py`, `test_post_input.py`,
`test_injection_format.py`, `tests/test_python_argument_forwarding_validator.py`,
`tests/test_powerhook_validation.py`, `tests/test_hook_base.py`, `tests/test_dreaming_tailer.py`,
`UserPromptSubmit_modules/tests/test_continuation_spine.py`, `__lib/file_lock_test.py` (the
integration-test harness — KEEP as-is).

**Archived / dead** (not dispatched):
`.archive/PostToolUse_drift_detector.py`, `_archive_v1/PreToolUse_command_intent_gate.py`,
`PreToolUse/PreToolUse_skill_pattern_gate_testlink`.

**Docs / plans** (pattern appears in prose, not executable):
`plans/plan-20260318-hook-system-state-safety-improvements.md`,
`plans/plan-20260310-pretooluse-verification-router.md`,
`evidence_hooks_source_collection.md`, `docs/development_guide.md`,
`PRETOOLUSE_BASH_ERROR_FIX.md`.

---

## Migration shape (per-site Evidence Packet contract)

For each migrated site, the Evidence Packet shows BOTH:
1. **Write path** — the `open("a") + write` line replaced by `append_jsonl(path, entry[, ensure_ascii=...])`.
2. **Exception path** — the enclosing `except` after narrowing. Sites already at
   `except OSError` need no narrowing (`TimeoutError` ⊂ `OSError`). Sites at
   `except Exception` (only `stop_block_log.py:124` among the POC set) narrow to
   `except OSError`.

**`ensure_ascii` behavior preservation:** `stop_block_log.py:123` uses
`ensure_ascii=False` (deliberate — preserves UTF-8 in `reason`/`matched_span`).
`hook_ledger` sites use `ensure_ascii=True`. Stop.py POC sites use
`ensure_ascii=True`. Resolution decided at POC time (see plan handoff).

**Spool byte-size change (item 3, accepted 2026-07-07):** migrating
`hook_ledger._append_spool_record` to `append_jsonl_safe` dropped the prior
`separators=(",", ":")` (compact) and explicit `newline="\n"`. The helper uses
`json.dumps()` default separators (with ascii whitespace) + `"\n"`, so spool
rows are slightly larger bytes. Functionally equivalent for JSONL parsing. If a
future "spool got bigger / disk usage spiked" investigation starts, start here.

## Integration proof

`__lib/file_lock_test.py` is the ≥8-proc integration test the POC requires
(8 workers × 200 lines, asserts `lost==0` AND `corrupt==0`). Baseline verified
GREEN 2026-07-07. Re-run after each POC site migration — do NOT write a new test.

## Reversibility

Each migration is a single-file edit revertable via `git restore <file>`. No
new files created by migration itself (this classification doc is the only new
file, authorized by Amendment 2). No plugin version bump required for the POC
(`__lib/` helpers under `cc-aca-authority` and local hooks — verify cache
implication at expansion if any migrated file lives under a versioned plugin).
