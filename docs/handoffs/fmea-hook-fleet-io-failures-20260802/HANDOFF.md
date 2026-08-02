---
thread_id: fmea-hook-fleet-io-failures-019fa8f8
parent_handoff_path: none
current_session_id: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14
current_terminal_id: unknown
produced_at: 2026-08-02T00:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: efac5a42fb93d25224ca4bf0c9237c8afc23607
---

# Handoff: FMEA findings — hook fleet I/O failure modes

## Objective

Capture the 12 FMEA findings from the session 019fa8f8 close-check sweep as a durable handoff so they are not lost and can be triaged for fixes in a future session.

## Status

OPEN — 12 FMEA findings identified, no fixes applied yet.

## Producing context

- Session: 019fa8f8-7e86-77f0-8e81-a7609f3c8b14 (started 2026-07-28T07:44:45)
- Models in play: minimax-m3, nim-openai-gpt-oss-20b, or-ling-3-flash-free
- Sweep: close-check mechanical sweep of 30 modified Python files from git log --since='24 hours ago'
- FMEA findings: 12 file:line targets across the post-compaction hook fleet

## Read-first list

1. `P:/.data/wiki/concepts/workspace-script-fmea-concurrent-io-and-shell-injection-patterns.md` — FMEA patterns wiki concept
2. `P:/.data/wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md` — close-check workflow context
3. `P:/.data/wiki/concepts/python-m-ruff-swallows-stdout-in-powershell.md` — ruff fallback context
4. `P:/.claude/rules/hook-development.md` — hook development standards

## Verified facts

- [FACT] FMEA scan identified 12 specific Python file failure-mode findings (source: sweep evidence, FMEA raw evidence section)
- [FACT] 8+ files use atomic write (tmp+os.replace) pattern (source: FMEA raw evidence)
- [FACT] 4 hook files use bare `except Exception:pass` on file writes (source: FMEA raw evidence)
- [FACT] fleet_quota.py uses shell=True for subprocess calls (source: FMEA raw evidence)
- [FACT] ship_receipt.py has python -m ruff fallback known broken on PowerShell (source: FMEA raw evidence)
- [FACT] launch_llm_chrome.py uses os.system() for schtasks with no timeout or error checking (source: FMEA raw evidence)
- [FACT] close_accounting.py write_evidence_ledger() uses os.replace() which can fail on Windows (source: FMEA raw evidence)
- [FACT] fleet-quota-cache.json has no file locking — concurrent writes from PostToolUseFailure + UserPromptSubmit can corrupt (source: FMEA raw evidence)

## Findings

### F1 — ship_receipt.py: python -m ruff fallback broken on PowerShell

- **File:** ship_receipt.py ~line 290
- **Problem:** `python -m ruff check <file>` returns exit code 1 with zero stdout/stderr on PowerShell — output is silently eaten. The fallback path reports PASS when lint actually failed.
- **Fix:** Replace fallback with direct `ruff check <file>` binary invocation, or remove fallback (primary path is sufficient).
- **Priority:** HIGH — false PASS on lint failures hides real issues

### F2 — PostToolUse_auto_verify.py: silent OSError swallow in _write_receipt

- **File:** PostToolUse_auto_verify.py, _write_receipt()
- **Problem:** Catches OSError and silently passes. If receipt directory is unwritable, verification receipts are lost and Stop hook re-blocks with NO_COVERING_RECEIPT.
- **Fix:** Emit structured warning to P:/.claude/hooks/.evidence/ before passing.
- **Priority:** HIGH — silent failure breaks the verification chain

### F3 — PostToolUseFailure_spawn_quota.py: bare except on file writes

- **File:** PostToolUseFailure_spawn_quota.py — learn_serde_broken(), update_cache(), track_escalation()
- **Problem:** Bare `except Exception: pass` on file writes. Concurrent write contention silently drops quota state updates.
- **Fix:** At minimum log exception to sidecar file with attempt count.
- **Priority:** MEDIUM — stale provider status is a correctness issue

### F4 — PreToolUse_spawn_model_gate.py: silent cache miss

- **File:** PreToolUse_spawn_model_gate.py — read_quota_cache(), get_serde_broken()
- **Problem:** Catch all exceptions and return empty dict/set. Missing/corrupt cache is invisible.
- **Fix:** Emit one-time warning when cache is missing/corrupt.
- **Priority:** MEDIUM — fail-open is correct for availability but invisible corruption is a risk

### F5 — UserPromptSubmit_quota_availability.py: silent OSError swallow

- **File:** UserPromptSubmit_quota_availability.py — save_state()
- **Problem:** Catches OSError and silently passes. Short-circuit optimization re-runs on every prompt if state file is unwritable.
- **Fix:** Same as F3 — log the exception.
- **Priority:** MEDIUM — wasted startup time on every prompt

### F6 — fleet_quota.py: shell=True + no file locking

- **File:** fleet_quota.py
- **Problem:** shell=True for npx opencode-quota and pwm subprocess calls (security concern). No file locking on fleet-quota-cache.json — concurrent writes from PostToolUseFailure + UserPromptSubmit can corrupt.
- **Fix:** Add msvcrt file locking or rename-and-swap scheme. Replace shell=True with subprocess.run with explicit args.
- **Priority:** HIGH — security concern + data corruption risk

### F7 — close_accounting.py: os.replace() Windows failure + None return

- **File:** close_accounting.py — write_evidence_ledger()
- **Problem:** os.replace() can fail on Windows if another process holds the file open. Returns None on allow_persist=False but callers may not handle None gracefully.
- **Fix:** Explicit None-handling audit on all callers. Consider retry with backoff for Windows file-locking contention.
- **Priority:** MEDIUM — evidence ledger loss breaks close-check audit trail

### F8 — launch_llm_chrome.py: os.system() with no error handling

- **File:** launch_llm_chrome.py
- **Problem:** Uses os.system() for schtasks commands with no timeout, no error checking, no output capture. If schtasks fails, error is invisible and Chrome may not launch.
- **Fix:** Switch to subprocess.run with timeout + check returncode.
- **Priority:** MEDIUM — Chrome launch failures are silent

### F9 — synthesize_subtopics.py: temp file leak on kill

- **File:** synthesize_subtopics.py
- **Problem:** Creates temp files with delete=False in try/finally, but finally only unlinks on success path. If process is killed between write and unlink, temp files leak.
- **Fix:** Unlink in finally regardless of success path; on Windows use os.close() first.
- **Priority:** LOW — temp file accumulation over time

### F10 — crawl_to_qmd.py: rg timeout on large concept dirs

- **File:** crawl_to_qmd.py
- **Problem:** rg subprocess with 10s timeout for wiki search. On large concept directories may timeout and return no results, causing related-link injection to be silently skipped.
- **Fix:** Emit warning when rg returns non-zero. Increase timeout to 30s.
- **Priority:** LOW — missing related links degrade wiki quality but don't break anything

### F11 — nlm_deep_research.py: notebook deletion silently fails

- **File:** nlm_deep_research.py — finally block
- **Problem:** Notebook deletion catches Exception and prints warning but does not propagate. If deletion fails, temp notebook accumulates in user's NotebookLM account.
- **Fix:** At minimum mark notebook for cleanup retry on next run.
- **Priority:** LOW — NotebookLM account accumulation

### F12 — run_state.py: atomic_write retry blocks caller

- **File:** run_state.py — atomic_write()
- **Problem:** Retries PermissionError 3 times with 0.5s sleep, then raises. Correct for Windows file-locking contention but blocks caller for up to ~1.5s.
- **Fix:** Consider yield control via asyncio.sleep or threading the write. Current behavior is acceptable for low-contention scenarios.
- **Priority:** LOW — acceptable for current usage patterns

## Task packets

### T1: Fix HIGH-priority FMEA findings (F1, F2, F6)

- **id:** FMEA-HIGH-01
- **goal:** Fix the three HIGH-priority FMEA findings
- **in scope:** ship_receipt.py, PostToolUse_auto_verify.py, fleet_quota.py
- **out of scope:** MEDIUM/LOW findings (separate tickets)
- **files / anchors:** see findings above
- **acceptance:** Each fix applied, tested, and committed individually
- **falsifier:** if a fix breaks hook runtime behavior, revert that fix
- **verification level required:** UNIT_TEST + LIVE_BEHAVIOR

### T2: Fix MEDIUM-priority FMEA findings (F3, F4, F5, F7, F8)

- **id:** FMEA-MED-01
- **goal:** Fix the five MEDIUM-priority FMEA findings
- **in scope:** PostToolUseFailure_spawn_quota.py, PreToolUse_spawn_model_gate.py, UserPromptSubmit_quota_availability.py, close_accounting.py, launch_llm_chrome.py
- **out of scope:** HIGH and LOW findings
- **acceptance:** Each fix applied, tested, and committed individually
- **falsifier:** if a fix breaks hook runtime behavior, revert
- **verification level required:** UNIT_TEST + LIVE_BEHAVIOR

### T3: Fix LOW-priority FMEA findings (F9, F10, F11, F12)

- **id:** FMEA-LOW-01
- **goal:** Fix the four LOW-priority FMEA findings
- **in scope:** synthesize_subtopics.py, crawl_to_qmd.py, nlm_deep_research.py, run_state.py
- **out of scope:** HIGH/MEDIUM findings
- **acceptance:** Each fix applied, tested, and committed individually
- **falsifier:** if a fix breaks runtime behavior, revert
- **verification level required:** UNIT_TEST + LIVE_BEHAVIOR

## Open decisions

1. **Fix order:** Should HIGH/MEDIUM/LOW be fixed in separate commits or batched by priority?
   - Option A: One fix per commit (clearer history, easier rollback)
   - Option B: One commit per priority tier (less ceremony)
   - **Leading option:** Option A — matches AGENTS.md auto-commit rule

2. **F12 (run_state.py retry blocking):** Is the 1.5s blocking acceptable or worth the async refactor?
   - Option A: Accept current behavior (low impact)
   - Option B: Async refactor (higher effort, marginal gain)
   - **Leading option:** Option A — defer unless user reports blocking issues

## Hard constraints

- AGENTS.md destructive-git ban: no force-push, no reset --hard, no rebase -i, no clean -fd
- AGENTS.md auto-commit: stage only files you changed; surgical git add
- All hook changes must be tested with real dispatch (not mocked), per .claude/rules/testing.md
- FMEA fixes must not regress hook behavior — if a fix breaks a hook, revert
- shell=True replacements must use explicit argument arrays, not string concatenation (security)

## Cross-reference couplings

- `P:/.data/wiki/concepts/workspace-script-fmea-concurrent-io-and-shell-injection-patterns.md` — FMEA patterns wiki concept
- `P:/.data/wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md` — close-check workflow context
- `P:/docs/handoffs/close-check-blocked-019fa8f8-20260801/HANDOFF.md` — close-check remediation handoff (T3 covers FMEA)
- `P:/docs/handoffs/close-check-lifecycle-019fb937-20260802/HANDOFF.md` — close-check lifecycle (sibling session)

## Resumption protocol

1. Start with T1 (HIGH-priority fixes)
2. Run close-check after each fix to confirm no regressions
3. Commit each fix individually
4. Re-run FMEA scan after all fixes to confirm findings are resolved

## Suggested next invocation

```
/go FMEA-HIGH-01 — fix HIGH-priority FMEA findings (F1, F2, F6)
```

## Last user message (verbatim)

> "Run the /handoff skill."

## Epistemic labels per claim

- "FMEA scan identified 12 findings" — [FACT] (source: sweep evidence, FMEA raw evidence)
- "python -m ruff fallback is broken on PowerShell" — [FACT] (source: AGENTS.md Class C quoting section + FMEA raw evidence)
- "fleet_quota.py shell=True is a security concern" — [FACT] (source: FMEA raw evidence)
- "Option A (one fix per commit) is leading" — [INFERENCE] (based on AGENTS.md auto-commit rule and bisectability)
- "F12 current behavior is acceptable" — [INFERENCE] (based on low-contention assumption, not measured)

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-02 | 019fa8f8 | created |
