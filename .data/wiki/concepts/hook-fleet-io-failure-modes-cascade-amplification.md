---
title: "Hook fleet I/O failure modes — cascade amplification in verification gates"
created: 2026-08-02
source: session-019fa8f8-7e86-77f0-8e81-a7609f3c8b14
tags: [fmea, hook-i/o, cascade-amplification, fail-open, verification-receipt, hook-fleet, capture]
summary: >
  Hook script I/O failures have a cascade-amplification property that workspace
  scripts lack: silent drops break the verification chain downstream, producing
  opaque "blocked" loops far from the actual cause. The 2026-08-02 FMEA sweep
  surfaced 8 findings across the hook fleet. The fix is a 5-rule I/O contract
  (warn-on-fail writes, file-locked shared state, warn-on-missing reads,
  explicit arg arrays, finally-guarded temp cleanup), not 8 individual patches.
agent: grok
host: grok
cognitive_load: 3
verification: observed
tier: warm
sources:
  - ~/.grok/hooks/scripts/PostToolUse_auto_verify.py (_write_receipt silent OSError swallow)
  - ~/.grok/hooks/scripts/PostToolUseFailure_spawn_quota.py (bare except on quota cache writes)
  - ~/.grok/hooks/scripts/PreToolUse_spawn_model_gate.py (silent cache miss via except)
  - ~/.grok/hooks/scripts/UserPromptSubmit_quota_availability.py (silent OSError on state save)
  - ~/.grok/hooks/scripts/fleet_quota.py (shell=True + no file locking on cache)
  - ~/.grok/hooks/scripts/ship_receipt.py (python -m ruff fallback broken on PowerShell)
  - P:/.claude/hooks/close_accounting.py (os.replace() Windows file-locking race)
  - Existing: P:/.data/wiki/concepts/workspace-script-fmea-concurrent-io-and-shell-injection-patterns.md
  - Existing: P:/.data/wiki/concepts/python-m-ruff-swallows-stdout-in-powershell.md
  - Existing: P:/.data/wiki/concepts/enforcement-hierarchy-and-compaction-strategy.md
  - Existing: P:/.data/wiki/concepts/capability-hierarchy-for-hook-path-verification.md
  - Handoff: P:/docs/handoffs/fmea-hook-fleet-io-failures-20260802/HANDOFF.md
relations:
  - target: wiki/concepts/workspace-script-fmea-concurrent-io-and-shell-injection-patterns.md
    type: extends — that concept covers workspace scripts (P:/.agents/scripts/); this captures the hook fleet (different file locations, different failure mode)
  - target: wiki/concepts/enforcement-hierarchy-and-compaction-strategy.md
    type: related — silent hook failures are the specific instantiation of "hooks have silent-failure modes"
  - target: wiki/concepts/capability-hierarchy-for-hook-path-verification.md
    type: complements — that concept covers verification receipt mismatches; this covers I/O paths that prevent receipt creation
  - target: wiki/concepts/python-m-ruff-swallows-stdout-in-powershell.md
    type: refines — applied to ship_receipt.py fallback path specifically
  - target: wiki/concepts/auto-commit-authority-isolation.md
    type: parallel — both discuss controlled fail-open semantics; the difference is "intentional vs accidental"
---

# Hook fleet I/O failure modes — cascade amplification in verification gates

## The meta-finding (the learning that transfers)

The 2026-08-02 FMEA sweep of `~/.grok/hooks/scripts/` and `P:/.claude/hooks/` surfaced **8 specific findings** in a single pass. **What is worth capturing is not the individual bugs — it is that hook scripts share a failure mode that workspace scripts do NOT have: cascade amplification.**

A workspace script's silent I/O failure is a one-shot operational gap: the script didn't do its job, the next session fixes it. A hook script's silent I/O failure is a **cascade amplifier**: the hook silently drops its write, the verification gate downstream sees no receipt, that gate blocks the next operation, the model retries the operation, the hook silently drops the write again — and the user sees a loop of "blocked" messages with no diagnostic.

The two file populations are governed by the same I/O hygiene rules but the failure mode is fundamentally different. This concept captures the hook-specific pattern.

## Distinction from the workspace-script FMEA concept

[[workspace-script-fmea-concurrent-io-and-shell-injection-patterns]] captured the same-class patterns in `P:/.agents/scripts/` and `P:/packages/nlm-to-wiki/scripts/`. That concept recognized the pattern ("scripts under-engineer concurrent I/O and shell invocation") but scoped itself to workspace scripts. This concept adds the **hook fleet layer** of the same pattern AND the failure-mode distinction that makes hooks worse.

| Dimension | Workspace script | Hook script |
|---|---|---|
| **Failure detection** | Operator notices missing artifact | Hook exit 0 + downstream gate blocks — symptoms far from cause |
| **Recovery path** | Re-run the script | Need to identify which hook failed; no diagnostic in the receipt |
| **Amplification** | One-shot operational gap | Cascade: silent drop → no receipt → gate blocks → user re-runs → silent drop loop |
| **Write amplification** | Single write per invocation | Multiple writes per session could collide (lock contention between hooks) |
| **Caller trust** | Operator can verify directly | Caller is the verification system itself — silent failure breaks the system |

## The 8 hook-fleet findings (verbatim from FMEA sweep, 2026-08-02)

### Tier 1 — HIGH (silent failure hides verification gate failure)

#### F1 — ship_receipt.py: python -m ruff fallback reports PASS on actual failure

- **File:** `~/.grok/hooks/scripts/ship_receipt.py` ~line 290
- **Pattern:** Fallback to `python -m ruff check <file>` when primary `ruff` binary fails
- **Failure mode:** On PowerShell, `python -m ruff` returns exit code 1 with **zero stdout and zero stderr** (documented in [[python-m-ruff-swallows-stdout-in-powershell]]). The fallback path interprets this as "no output = no errors" and reports PASS.
- **Cascade:** lint failure → false PASS receipt → verification gate accepts → model ships code with lint regressions.
- **Fix:** Remove the fallback (primary `ruff` binary is sufficient) OR check exit code AND output length, not just one.

#### F2 — PostToolUse_auto_verify.py: silent OSError swallow in `_write_receipt()`

- **File:** `~/.grok/hooks/scripts/PostToolUse_auto_verify.py`
- **Pattern:** `try: ... except OSError: pass`
- **Failure mode:** If the receipt directory is unwritable (permission denied, locked by another process), the verification receipt is silently dropped.
- **Cascade:** Tool ran → no receipt → Stop hook blocks with `NO_COVERING_RECEIPT` → model re-runs → same silent drop → user sees an opaque "blocked" without knowing the receipt-write failed.
- **Fix:** Emit structured warning to `~/.grok/hooks/.evidence/` before passing. At minimum log stderr to evidence.

### Tier 2 — MEDIUM (silent failure causes stale state without diagnostic)

#### F3 — PostToolUseFailure_spawn_quota.py: bare `except Exception: pass` on file writes

- **File:** `~/.grok/hooks/scripts/PostToolUseFailure_spawn_quota.py`
- **Pattern:** `learn_serde_broken()`, `update_cache()`, `track_escalation()` all use bare `except Exception: pass` on file writes
- **Failure mode:** Concurrent write contention (lock held by another hook) silently drops quota state updates.
- **Cascade:** Provider marked healthy → spawn fails → quota check stale → wrong routing decision.
- **Fix:** At minimum log exception to sidecar file with attempt count.

#### F4 — PreToolUse_spawn_model_gate.py: silent cache miss via broad except

- **File:** `~/.grok/hooks/scripts/PreToolUse_spawn_model_gate.py`
- **Pattern:** `read_quota_cache()` and `get_serde_broken()` catch all exceptions and return `{}` / `set()`
- **Failure mode:** Missing or corrupt cache is invisible — the hook fires `allow` (fail-open) which is correct for availability, but the operator never sees "cache is corrupted, fix it."
- **Cascade:** Stale quota → wrong model routing → operator notices degraded performance but can't trace it to "the cache was corrupted 3 days ago."
- **Fix:** Emit one-time warning to evidence log when cache is missing/corrupt.

#### F5 — UserPromptSubmit_quota_availability.py: silent OSError on `save_state()`

- **File:** `~/.grok/hooks/scripts/UserPromptSubmit_quota_availability.py`
- **Pattern:** `save_state()` catches OSError and silently passes
- **Failure mode:** Short-circuit optimization that should skip quota checks on subsequent prompts won't engage if state file is unwritable.
- **Cascade:** Quota check runs on every prompt (5-30s wasted per turn) → operator sees slow prompts but no diagnostic.
- **Fix:** Log the exception (same as F3).

#### F6 — close_accounting.py: os.replace() Windows failure + None return

- **File:** `P:/.claude/hooks/close_accounting.py`
- **Pattern:** `write_evidence_ledger()` uses `os.replace()` which can fail on Windows if another process holds the file open. Returns None on `allow_persist=False` but callers may not handle None gracefully.
- **Failure mode:** Evidence ledger is lost during close-check; lose of audit trail.
- **Cascade:** Close-check runs without ledger → cannot prove verification chain → runtime gate misses.
- **Fix:** Explicit None-handling audit on all callers. Consider retry-with-backoff for Windows file-locking contention.

### Tier 3 — MEDIUM (security surface area)

#### F7 — fleet_quota.py: shell=True + no file locking

- **File:** `~/.grok/hooks/scripts/fleet_quota.py`
- **Pattern:** `subprocess.run(['npx', 'opencode-quota', ...], shell=True)` and `pwm` subprocess calls
- **Failure mode:** Two issues:
  1. **Security:** shell=True with string interpolation creates injection surface
  2. **Concurrency:** fleet-quota-cache.json written with tmp+replace but **no file locking** — concurrent writes from PostToolUseFailure + UserPromptSubmit can corrupt
- **Cascade:** Either issue breaks the quota-tracking chain; corruption makes the cache unreliable.
- **Fix:** Replace shell=True with explicit argument arrays. Add `msvcrt.locking()` (Windows) or `fcntl.flock()` (POSIX) for concurrent writes.

### Tier 4 — LOW (clean-up edge cases)

#### F8 — synthesize_subtopics.py: temp file leak on SIGKILL

- **File:** `P:/packages/nlm-to-wiki/scripts/synthesize_subtopics.py`
- **Pattern:** `tempfile.NamedTemporaryFile(delete=False)` in try/finally, but finally only unlinks on success path
- **Failure mode:** If process is killed between write and unlink, temp files leak
- **Cascade:** Slow accumulation over time → eventually fills disk → terminal fails
- **Fix:** Unlink in finally regardless of success path; on Windows use `os.close()` first.

## Why this pattern emerges: the three-fragment-development model

Hook scripts are developed in three distinct fragments:

1. **Single execution intent** — the dev writes the hook to fire once per event, no concurrency assumption
2. **Different dev context** — the hook is deployed in a multi-agent, multi-terminal environment where the same hook can fire concurrently from N processes
3. **Verification-gate assumption** — the calling system assumes the hook writes its receipt; the hook doesn't check whether the write succeeded

The three fragments each have a reasonable mental model. Composed, they produce the cascade. The fix is to model the hook's I/O contract explicitly:

- **The hook writes a receipt.** If the write fails, the system MUST know — the alternative is silent drop → cascade.
- **The hook reads shared state.** If the read fails, the system MUST know — silent fallback to defaults is acceptable only when the alternative is unintentional denial.
- **The hook writes shared state.** If concurrent writes can corrupt, the hook MUST lock.

## The structural fix (not individual patches)

The 8 findings are not 8 unrelated bugs. They are a **single architectural gap**: hook scripts do not have I/O contracts that match the cascade-amplification property of the verification system they participate in.

The structural fix is to define an I/O contract for hook scripts — a set of rules every hook MUST follow:

1. **Receipt writes must emit a warning on failure, not silently drop.** (Addresses F1, F2)
2. **Shared-state writes must use fcntl.flock / msvcrt.locking.** (Addresses F6, F7)
3. **Shared-state reads must emit a warning on missing/corrupt state, not silently fall back.** (Addresses F3, F4, F5)
4. **Subprocess calls must use explicit argument arrays, never shell=True with string interpolation.** (Addresses F7)
5. **Temp files must be unlinked in finally regardless of success path.** (Addresses F8)

These are 5 rules, not 8 individual fixes. They can be enforced as a pre-commit hook (parallel to the existing ruff/pyright tier) or as a Stop-hook check that fails any hook script that violates them.

## What this concept does NOT claim

- **Not "all hook scripts are broken."** Many hooks correctly handle I/O. The pattern is the under-engineering TENDENCY, not a universal property.
- **Not "fail-open is wrong."** [[auto-commit-authority-isolation]] documents intentional fail-open for solo sessions. The difference is intentional fail-open (declared, monitored) vs. accidental fail-open (silent except that the operator doesn't read).
- **Not a replacement for /fmea.** This concept captures the meta-finding from a single FMEA sweep. The /fmea skill is the engine that produces the findings; this concept captures the hook-specific pattern.
- **Not unique to Grok hooks.** The same pattern applies to any hook system where the hook silently fails and the verification system depends on the hook's success.

## How to use this concept

When reviewing a hook script, in addition to the 4 checks in [[workspace-script-fmea-concurrent-io-and-shell-injection-patterns]] § How to use:

5. **Does it write a verification receipt?** If yes, does the failure path emit a warning? (Catches F1, F2)
6. **Does it read shared state (cache, ledger, config)?** If yes, does the read failure path emit a warning? (Catches F3, F4, F5)
7. **Does it write shared state?** If yes, does it use file locking? (Catches F6, F7)
8. **Does it use `shell=True`?** If yes, why isn't it using explicit argument arrays? (Catches F7)

When writing a new hook script: apply the 4 workspace-script checks + these 4 as a pre-commit checklist.

## Source provenance

FMEA sweep output (session 019fa8f8, 2026-08-01, sweep pass). Files modified in 24h prior to sweep:
`PostToolUse_auto_verify.py`, `PostToolUseFailure_spawn_quota.py`, `PreToolUse_spawn_model_gate.py`, `UserPromptSubmit_quota_availability.py`, `fleet_quota.py`, `ship_receipt.py`, `close_accounting.py`,
`synthesize_subtopics.py`.

I/O patterns identified via file content analysis: bare `except Exception: pass`, `except OSError: pass`, `subprocess.run(shell=True)`, `os.replace()` without retry, `tempfile.NamedTemporaryFile(delete=False)`.

**Reference failure (predicted):** if a future session sees `NO_COVERING_RECEIPT` blocks that don't respond to fixes, OR quota cache corruption that doesn't have a diagnostic, OR repeated `schtasks` hangs, that is the cascade-amplification failure this concept exists to prevent. The fix handoff is `docs/handoffs/fmea-fix-batch-20260802/HANDOFF.md`.

## What this means for our workspace

The hook fleet is the verification gate of last resort. Every silent drop in
the hook fleet translates to a downstream gate failure. The 8 FMEA findings
are not 8 separate bugs - they are 8 instances of a single architectural gap:
the hook fleet does not have I/O contracts that match the cascade-amplification
property of the verification system.

**Concrete actions for our workspace:**

1. **Add the 5-rule I/O contract to ~/.claude/rules/hook-development.md** as a
   mandatory pre-commit checklist (parallel to the existing tests/anti-mock
   rules). The rules are stated in the "Structural fix" section above.
2. **Add a Stop-hook check** that scans the hook fleet for the 5 anti-patterns
   (silent except, shell=True, os.replace without retry, NamedTemporaryFile
   delete=False without finally-guarded unlink, concurrent writes without
   locking). Print a warning with file:line; require fix before merge.
3. **Refactor the 8 hooks identified in the FMEA sweep** to comply with the
   contract. Each fix is a separate commit (matching AGENTS.md auto-commit
   rule). The handoff at docs/handoffs/fmea-fix-batch-20260802/HANDOFF.md has
   task packets T1 (HIGH), T2 (MEDIUM), T3 (LOW).
4. **Wire the existing PostToolUse_auto_verify.py failure path to the
   evidence log** so silent OSError swallows produce a structured warning.
   This addresses F2 (the highest-impact finding) at the lowest cost.
5. **Replace python -m ruff fallback in ship_receipt.py with a hard
   failure** - the primary ruff binary is sufficient. The fallback
   produces silent PASS on actual lint failure, which is the worst case
   (truthful failure masked as success).

**What this concept does NOT change**: the existing workspace-script FMEA
concept remains the canonical reference for P:/.agents/scripts/ patterns.
This concept is the hook-fleet complement.

## Receipts

- **F1 (ship_receipt.py python -m ruff fallback):** read_file confirmed the
  fallback path at the ship_receipt.py line ~290 in the FMEA sweep; the
  breakage is documented in [[python-m-ruff-swallows-stdout-in-powershell.md]]
  (verified by AGENTS.md Class C quoting section).
- **F2 (PostToolUse_auto_verify.py _write_receipt):** the silent except is
  in function _write_receipt() - FMEA sweep identified the pattern.
- **F3 (PostToolUseFailure_spawn_quota.py):** learn_serde_broken(),
  update_cache(), track_escalation() per FMEA sweep raw evidence.
- **F4 (PreToolUse_spawn_model_gate.py):** read_quota_cache(),
  get_serde_broken() per FMEA sweep raw evidence.
- **F5 (UserPromptSubmit_quota_availability.py):** save_state() per FMEA
  sweep raw evidence.
- **F6 (close_accounting.py):** write_evidence_ledger() per FMEA sweep
  raw evidence.
- **F7 (fleet_quota.py):** subprocess calls per FMEA sweep raw evidence.
- **F8 (synthesize_subtopics.py):** temp file handling per FMEA sweep
  raw evidence.
- **Source provenance:** session 019fa8f8-7e86-77f0-8e81-a7609f3c8b14,
  2026-08-01 sweep pass, FMEA raw evidence section.
- **Implementation handoff:** P:/docs/handoffs/fmea-hook-fleet-io-failures-20260802/HANDOFF.md
  has task packets T1 (HIGH-priority fixes), T2 (MEDIUM), T3 (LOW).

## Falsifier

This concept is wrong if:
- All 8 hook files were actually fixed individually and the pattern is not architectural (i.e., the under-engineering is per-script, not systematic)
- The cascade-amplification property is rare in real deployments (the 8 findings are not user-facing in production)
- The 5-rule I/O contract is too restrictive (most hooks genuinely don't need it)

The first falsifier is testable: survey the hook fleet for I/O patterns and check whether the 5-rule contract would have prevented the FMEA findings. If yes, the pattern is architectural.

## Auto-related

- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]
- [[hook-failure-mode-taxonomy]]
- [[claude-code-hook-system-patterns]]
- [[claude-code-hook-system]]
- [[Are-there-repos-or-solutions-to-claude-code-gettin]]

