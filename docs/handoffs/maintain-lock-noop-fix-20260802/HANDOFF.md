---
title: "Fix /maintain concurrent-execution lock no-op (REV-003)"
created: 2026-08-02
source: session-019fc303
status: OPEN
yaml_status: open
assignee: unassigned
session: 019fc303-700f-7711-b376-12da1aff578a
tags: [maintain, bug, concurrent-execution, lock, review-finding]
---

# Fix /maintain concurrent-execution lock no-op (REV-003)

## Objective

Replace the subprocess-based lock in `/maintain` Step 0 with a file-based sentinel that actually persists for the session duration.

## Context

The `/review` (REV-003, verified risk) found that the concurrent-execution lock added to `/maintain` Step 0 is a **functional no-op**. The lock uses `python -c` with `msvcrt.locking()` — but the `python -c` subprocess exits immediately after printing "Lock acquired." When the subprocess exits, the fd closes and the OS releases the lock. The subsequent `/maintain` steps run in a different process context and are **not protected**.

**Review finding:** `P:/.artifacts/console_ca63859a-033d-4fe8-a5eb-56467a426e4d/grok-review/local/20260802-173537/FINDINGS.md` — REV-003, verified, confidence 0.85.

## Root cause

The lock was written and committed but never test-fired — the exact failure mode the "execution receipts for executable artifacts" AGENTS.md rule is designed to prevent. The lock passed static inspection (the code is syntactically correct and the msvcrt API usage is right) but fails at runtime (the subprocess lifetime is too short).

## Fix

Replace the subprocess-based lock with a **file-based sentinel**:

1. At `/maintain` Step 0 start: check if `P:/.data/maintain.lock` exists. If yes, exit with "another /maintain is in progress."
2. If no: create the file (atomic write with PID + timestamp for diagnostics).
3. At `/maintain` completion or exit: delete the file.

**Why file-based over process-level lock:** the `/maintain` flow is orchestrated by the LLM across multiple shell invocations — there is no single process that holds the lock for the session. A file-based sentinel is the only mechanism that persists across process boundaries.

**Alternative considered:** wrap the entire flow in one Python process. Rejected because `/maintain` is LLM-orchestrated (the LLM reads output from each step and decides what to do next), not a linear script.

## Acceptance criteria

- [ ] Lock file created at start of `/maintain`, deleted at end
- [ ] Second concurrent `/maintain` invocation exits with message when lock file exists
- [ ] Lock file includes PID + timestamp for stale-lock diagnosis
- [ ] Stale lock detection: if lock file mtime > 1 hour old, warn but allow override
- [ ] Test-fired: verify the lock actually blocks a second invocation
