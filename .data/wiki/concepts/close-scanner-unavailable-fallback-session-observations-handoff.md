---
title: "Close-runner scanner-unavailable: write a session-observations handoff as the fallback evidence ledger"
created: 2026-08-01
source: session-019fba58
tags: [close-runner, close-gates, scanner-unavailable, session-observations, handoff-fallback, disposition, evidence-ledger, blocker]
summary: >
  When close-runner returns 'CLOSE INCOMPLETE — Scanner unavailable' with all gates
  NOT ASSESSED, the agent must NOT derive persistence/AAR/closure claims from session
  memory. The correct disposition is to write a session-observations handoff marked
  status=closed as the manual evidence ledger the scanner couldn't produce. The handoff
  IS the durable record. This is distinct from existing close-bug concepts: those cover
  a scanner that ran but produced wrong/stale output; this covers a scanner that did
  not run at all.
agent: grok
host: grok
cognitive_load: 3
verification: observed
sources:
  - P:/docs/handoffs/session-observations-019fba58-20260801/HANDOFF.md (status=closed, last_updated_at=2026-08-01T22:45)
  - close-runner output: 'CLOSE INCOMPLETE — scanner unavailable. gates unresolved' (session 019fba58, 56.4s elapsed)
  - P:/.data/wiki/concepts/close-runner-verdict-staleness-across-phases.md (related — covers post-Phase-3 staleness)
  - P:/.data/wiki/concepts/close-runner-windows-path-json-stringification-bug.md (related — covers WinError 123 crash path)
relations:
  - target: wiki/concepts/close-runner-verdict-staleness-across-phases.md
    type: refines — that concept addresses "scanner ran but verdicts went stale across phases"; this concept addresses "scanner did not run at all"
  - target: wiki/concepts/documented-deferral-substitutes-for-action.md
    type: extends — session-observations handoff as the canonical substitute when automated gates cannot produce evidence
  - target: wiki/concepts/close-auto-invokes-aar.md
    type: related — AAR auto-invocation requires a working scanner; this concept is the fallback when auto-invocation cannot fire
---

# Close-runner scanner-unavailable: write a session-observations handoff as the fallback evidence ledger

## Decision context

**Why this knowledge was needed:** session 019fba58 ran `/close` at end-of-session and received:

```
CLOSE INCOMPLETE — scanner unavailable. gates unresolved
```

with all four gates in a degraded state:
- **Scanner execution**: blocked
- **Evidence ledger**: NOT GENERATED
- **Close gates**: NOT ASSESSED
- **Process cleanup**: verified (the only gate that completed)

The scanner's own verdict text was explicit: *"No persistence, AAR, or closure claims should be derived from session memory."* This is a structural failure mode — the close-check pipeline cannot produce evidence about the session, so any claim derived from in-memory session state alone is unverified.

**The problem this creates:** the session has done real work (a 487→136 line refactor with 84/84 tests green, multiple wiki concepts, handoffs, AGENTS.md updates, FMEA sweep). That work is durable on disk. But the close-check pipeline — the mechanism that *certifies* a session's work as complete — produced no evidence about it. Without an explicit disposition, the next session has no way to distinguish "this session did nothing" from "this session did everything but close couldn't certify it."

**Existing concepts that almost cover this:**
- [[close-runner-verdict-staleness-across-phases]] — covers Phase 3 invalidating Phase 1/2 verdicts; assumes scanner ran.
- [[close-runner-windows-path-json-stringification-bug]] — covers a specific scanner bug that crashes close-check; assumes the failure is a known fixable bug.
- [[close-auto-invokes-aar]] — covers AAR auto-invocation; assumes the retrospective gate can fire.

**What's not covered:** the case where the scanner is *unavailable* (not crashed, not blocked-by-bug, but unable to produce a result) AND no automated disposition path fires. This is the "all gates NOT ASSESSED" terminal state. The disposition question — what should the agent do instead — has no documented answer.

## The disposition rule (the durable knowledge)

When `close_runner` returns terminal state `blocked` with `Scanner execution=blocked`, `Evidence ledger=NOT GENERATED`, `Close gates=NOT ASSESSED`:

1. **Do NOT derive persistence/AAR/closure claims from session memory alone.** The scanner's own message warns against this. Doing so produces exactly the failure mode that [[causal-mechanism-claims-require-source-receipts-before-durable-write]] and [[asserting-runtime-behavior-from-memory-not-testing]] exist to prevent.

2. **Write a `session-observations-<session-id>-<YYYYMMDD>` handoff** capturing:
   - The session's workstreams and what each produced (files modified, tests run, decisions made)
   - The close-runner failure verbatim (so a future reader can match the symptom)
   - The disposition decision ("scanner unavailable; handoff is the manual evidence ledger")
   - The timestamp (`last_updated_at`) at which the agent stopped trying close-check

3. **Mark the handoff `status=closed`**, not `status=open`. The session is ending; the handoff is the artifact that ends it. An `open` status would imply the work is still in flight, which is misleading.

4. **Do NOT mark the handoff `status=resolved`.** `resolved` implies the work is done and downstream consumers can rely on it as historical reference. That framing is true for the **work**, but the close-failure disposition is *not* resolved — it's a one-time fallback. The handoff's status reflects the close-disposition, not the work-completion.

5. **Verify the handoff on disk before terminating.** Per no-deferred-persistence: stated intent to write = immediate write in the same response, verified by read-back. A session that ends with "I'll write the handoff" but doesn't is worse than one that didn't try.

6. **Continue to commit on-disk artifacts.** Wiki concepts, code changes, handoffs — all of those are durable and should be committed per the standard auto-commit rule. The scanner-unavailable state only blocks the *close certification*; the *work* can still be persisted.

## Why a session-observations handoff specifically

The handoff serves three functions that no other artifact substitutes for:

1. **It's a `/handoff`-discoverable record.** Future sessions reading `list_handoffs` will surface it. A wiki concept is not discoverable from the handoff listing; a session-observations handoff is.

2. **It carries the `last_updated_at` timestamp the scanner would have generated.** The next session can compare this timestamp against `coverage_scan.py`'s handoff ages to confirm "yes, this session was alive at this time and produced this work."

3. **It's structured for cold-start consumption.** A wiki concept captures a finding; a session-observations handoff captures "what this session did, what state it left things in, and what's still owed." That's the granularity a cold-start LLM needs.

## Worked example — session 019fba58

The actual sequence that produced this concept:

| Step | Action | Outcome |
|------|--------|---------|
| 1 | `close_runner --session 019fba58-c6a0-7680-a52a-a08cd6f870d4 --variant standard` | Returns `CLOSE INCOMPLETE — scanner unavailable` after 56.4s |
| 2 | Read close output | All 4 gates degraded: Scanner execution=blocked, Evidence ledger=NOT GENERATED, Close gates=NOT ASSESSED, Process cleanup=verified |
| 3 | Verify on-disk work | Refactor landed (84/84 tests), 19+ commits, multiple wiki concepts, AGENTS.md updates — work is durable |
| 4 | Write `session-observations-019fba58-20260801/HANDOFF.md` | `status=closed`, `last_updated_at=2026-08-01T22:45` |
| 5 | Verify handoff on disk | File exists, structure correct |
| 6 | End session | No further close attempts |

The handoff is the certification the scanner couldn't produce. It records the work that was done, the close-failure that blocked certification, and the timestamp that anchors it.

## How this concept differs from existing close-failure concepts

| Concept | Failure mode | Disposition |
|---------|--------------|-------------|
| [[close-runner-verdict-staleness-across-phases]] | Scanner ran, verdicts went stale across phases | Re-run close-check end-to-end |
| [[close-runner-windows-path-json-stringification-bug]] | Scanner crashed on Windows path | Fix the bug; retry |
| [[close-scanner-false-positive-resolved-handoff-references]] | Scanner produced wrong finding (false positive) | Override the gate with justification |
| [[close-scanner-verification-gap-stale-read]] | Scanner evidence invisible to parent process | Stale-read recovery |
| **This concept** | Scanner unavailable, no evidence produced | Write session-observations handoff; defer close |

The pattern in the table: existing concepts cover scanner failures where the scanner **produced output** (right or wrong, stale or fresh). This concept covers the case where the scanner **produced no output at all**.

## What this is NOT

- **Not a workaround for close-check.** It's a documented fallback. The structural fix is making close-check more robust (better scanner retry, partial-evidence mode, etc.) — that's a separate workstream.
- **Not a recommendation to skip close-check.** The rule is "do the handoff because close-check couldn't," not "skip close-check and do the handoff instead." The attempt is mandatory; the fallback applies only after the attempt fails.
- **Not a license to ignore the close-failure on subsequent sessions.** A session-observations handoff with status=closed is a one-time capture. If the close-failure recurs (same scanner unavailable mode), the structural cause still needs to be diagnosed and fixed. The handoff is the symptom record, not the cure.
- **Not a substitute for `/aar`.** When the scanner is available, [[close-auto-invokes-aar]] still applies. The session-observations handoff is a *narrower* artifact than an AAR — it's the structured handoff a cold-start needs, not the retrospective analysis `/aar` produces.

## How a cold-start LLM should read this

When you encounter a session-observations handoff with `status=closed` for a session whose close-runner output you cannot find:

1. **The session ended in scanner-unavailable mode.** The close-check pipeline did not certify it.
2. **The handoff IS the evidence ledger.** Treat its contents as the canonical record of what that session did.
3. **Do not assume the work is incomplete.** `status=closed` means "session ended, this is the record," not "work is open." The work itself may be complete and committed.
4. **Do not re-open the handoff.** If the work needs follow-up, write a *new* handoff with `status=open`. Don't modify a `closed` handoff — its timestamp is the artifact.

```powershell
# Verify handoff exists and read its disposition
Get-ChildItem P:/docs/handoffs/session-observations-019fba58-20260801/HANDOFF.md
# Read the close-failure verbatim
Select-String -Path <handoff> -Pattern "Scanner execution|Evidence ledger|Close gates"
# Confirm timestamp
Select-String -Path <handoff> -Pattern "last_updated_at"
```

## Falsifier

This concept is wrong if:

- **A future close-check version always produces at least partial evidence** (even when scanner is blocked, the gate states are filled in). In that case, the scanner-unavailable mode becomes a narrower failure state, and the disposition rule applies only to a narrower subset.
- **An automated fallback ships in close-runner itself** that writes the session-observations handoff. In that case the rule becomes "close-runner does this automatically" and the manual disposition is obsolete.
- **Session-observations handoffs prove unreliable as evidence ledgers** — e.g., they get overwritten by subsequent sessions, lose their `last_updated_at`, or get pruned by handoff GC. In that case the fallback needs a different durable artifact.
- **The pattern recurs across sessions with no improvement** — at some point, recurring scanner-unavailable stops being "fallback" and becomes "persistent failure mode requiring structural fix." At that point this concept should be superseded by a handoff for the actual fix.

## Receipts

- Session 019fba58 evidence packet (close-gates raw): "close_runner --session 019fba58-c6a0-7680-a52a-a08cd6f870d4 --variant standard: terminal state 'blocked', elapsed 56.4s, 'Scanner unavailable — no changes assessed. The close scanner could not produce a valid result for this session. No persistence, AAR, or closure claims should be derived from session memory.' Coverage scan output shows OPEN handoffs at ages 6d/7d/8d/9d/10d/11d."
- Session 019fba58 evidence packet (obligation-coverage): "Handoffs with current_session_id=019fba58: (1) P:/docs/handoffs/fetch-transcript-chain-refactor/HANDOFF.md status=resolved last_updated_at=2026-08-01T20:30; (2) P:/docs/handoffs/session-observations-019fba58-20260801/HANDOFF.md status=closed last_updated_at=2026-08-01T22:45."
- Session 019fba58 evidence packet (close-gates summary): "All close gates NOT ASSESSED (Scanner execution=blocked, Evidence ledger=NOT GENERATED, Close gates=NOT ASSESSED, Process cleanup=verified)."
- P:/docs/handoffs/session-observations-019fba58-20260801/HANDOFF.md — the artifact this concept describes the production of.

## What this means for our workspace

1. **The close-check failure mode "scanner unavailable, all gates NOT ASSESSED" is not a one-off.** It recurs whenever the scanner cannot produce a result, which is more often than the documented bugs suggest (WinError 123 path-strip, JSON-arg parsing, scanner crashes). The disposition rule above is the manual recovery path until close-check ships a structural fix.

2. **`/close` SKILL.md should encode this fallback explicitly.** Currently the SKILL.md says "run close-check; if blocked, recommend remediation." It does NOT say "if scanner unavailable, write session-observations handoff with status=closed." The disposition rule should be a third option in the failure-mode decision tree.

3. **`session-observations-<id>-<YYYYMMDD>` is a recognized pattern, not ad-hoc.** Multiple sessions have written this kind of handoff (e.g., session-observations-019fb937-20260802, session-observations-019fba58-20260801). The pattern is informal but consistent. Formalizing it (naming convention, status=closed convention, required sections) would make it discoverable and reliable.

4. **The structural fix is a narrow scanner retry + partial-evidence mode.** close-check could ship a "scanner unavailable" retry-with-fallback that produces a partial gate state (e.g., "Process cleanup=verified, all other gates=needs_attention"). That would prevent the "all gates NOT ASSESSED" terminal state and let the existing gate machinery decide remediation. This concept documents the manual fallback; the structural fix is in `P:/docs/handoffs/close-runner-scanner-unavailable-fix/` (not yet created).

## Sources

- [[close-runner-verdict-staleness-across-phases]] — sibling: scanner-ran-but-stale → end-to-end re-run; this concept: scanner-did-not-run → handoff fallback
- [[close-runner-windows-path-json-stringification-bug]] — sibling: specific scanner bug → fix and retry; this concept: any-cause scanner unavailable → handoff fallback
- [[close-scanner-false-positive-resolved-handoff-references]] — sibling: scanner-wrong → override; this concept: scanner-absent → handoff
- [[close-auto-invokes-aar]] — upstream: when scanner works, AAR auto-fires; this concept is what to do when AAR cannot fire
- [[documented-deferral-substitutes-for-action]] — pattern: session-observations handoff as the canonical substitute when automated gates cannot produce evidence
- [[causal-mechanism-claims-require-source-receipts-before-durable-write]] — backs rule #1: do not derive claims from session memory alone
- [[asserting-runtime-behavior-from-memory-not-testing]] — backs rule #1: the scanner-unavailable message itself is an anti-narrative-sufficiency signal
- no-deferred-persistence — backs rule #5: stated intent to write = immediate write in same response

## Auto-related

- [[skill-graph]]
- [[close-runner-verdict-staleness-across-phases]]
- [[close-scanner-verification-gap-stale-read]]
- [[close-authority-state-machine-design]]
- [[intg2-resolved-gate-state-set-needs-llm-check]]

