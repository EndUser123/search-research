---
title: "File edit failures: two classes with distinct fixes"
created: 2026-07-21
source: session-2026-07-21
tags: [file-editing, multi-agent, concurrency, persistence, windows, failure-mode, structural-fix]
summary: >
  File edit losses on a multi-agent host come in two distinct classes with
  distinct fixes. Class A (persistence failure) is an OS/tool-layer problem
  where the edit tool returns success but the file content is unchanged —
  fixed by Python atomic write (tmp + os.replace). Class B (sequential
  collision) is an agent-concurrency problem where one agent's search_replace
  matches a stale old_string and silently reverts another agent's edit — NOT
  fixed by atomic write, which overwrites stale reads just as silently. The
  fix for Class B depends on file shape: append-only for logs, conditional
  write for shared structured docs. Conflating the two classes leads to
  applying the wrong fix.
agent: grok
host: both
cognitive_load: 2
verification: session-verified
relations:
  - target: wiki/concepts/plausible-narratives-substitute-for-verification
    type: related
  - target: wiki/concepts/external-state-cross-check-as-structural-fix
    type: related
  - target: wiki/concepts/worktree-writes-dont-sync-to-canonical
    type: related
---

# File edit failures: two classes with distinct fixes

## The distinction that matters

When an edit "succeeds" but the content doesn't persist (or prior content vanishes), there are two structurally different causes. Treating them as one failure class — "edits got lost" — leads to applying the wrong fix.

| Class | Layer | What happens | Detection signal | Fix |
|---|---|---|---|---|
| **A. Persistence failure** | OS / Windows / tool | Edit tool returns success; file content unchanged on disk | Read-back of YOUR edited line shows the OLD content | Python atomic write (`tmp + os.replace`) |
| **B. Sequential collision** | Application / agent concurrency | Agent A edits. Agent B's `search_replace` matches a pre-A `old_string` and silently reverts A's edit. B's read-back confirms B's change — A's change is gone. | Read-back of surrounding lines (or git diff) shows A's content missing | Depends on file shape — see below |

## Why Python atomic write solves Class A but NOT Class B

Atomic write (`write_text(tmp); os.replace(tmp, path)`) solves the persistence problem: the OS guarantees the replace is atomic, so either the old or new content is on disk, never a partial write.

**Atomic write does not solve sequential collision.** If I read the file, another agent edits it, and then I atomically write my modified version — I've just clobbered their edit with my stale-read-based write. The atomicity guarantees my write lands; it doesn't guarantee my write preserves their concurrent changes.

This is the trap: "use atomic write" feels like a structural fix for edit loss, but it only addresses one of the two failure classes. A protocol that recommends atomic write as the universal fix for edit loss will still lose edits to Class B collisions.

## The fix for Class B depends on file shape

Different file shapes have different concurrency profiles. The right write pattern matches the file's shape:

| File shape | Examples | Write pattern | Why |
|---|---|---|---|
| **Append-only log** | `wiki/log.md`, session journals | `open(path, 'a')` append mode | Appends never collide; each agent adds to the end without reading prior content |
| **Shared structured doc** | `AGENTS.md`, `CLAUDE.md`, `SKILL.md` | Conditional write: read+hash → edit → write-if-unchanged → retry on conflict | Detects concurrent modification; forces re-read-integrate-retry instead of silent clobber |
| **One-writer-per-file** | A handoff you own, a concept you're authoring | `search_replace` is fine | No concurrent writer exists; collision risk is zero |

**The anti-pattern:** treating all shared files the same way. Using `search_replace` on a log file makes every entry a target for the next agent's `old_string` match — which is exactly what happened to `wiki/log.md` on 2026-07-21.

## Worked example: the 2026-07-21 log.md incident

**What happened:** 13 log entries written by multiple agents via `search_replace` over ~2 hours. Each agent's edit targeted a unique `old_string` near the top of the file. Later agents' `old_string` values matched earlier file states (before prior agents' inserts landed). Result: each later edit silently reverted the earlier edits. All 13 entries vanished.

**Root cause:** Class B sequential collision on an append-shaped file. The file was being edited as if it were a structured doc (read-modify-write via `search_replace`) when its semantics are append-only.

**The wrong fix:** "use Python atomic write for log.md." This would not have helped. Each agent would still have read a stale version and atomically written their stale version minus concurrent appends.

**The right fix:** `open(path, 'a')` for all log.md writes. Appends are commutative; order doesn't matter for a log; no agent needs to read prior content to append.

**The verification gap:** none of the agents verified that prior entries survived their edit. Each agent read back only their own entry and confirmed it landed. The surrounding-lines read would have caught the collision — which is why the verification protocol (read before AND after, not just your own change) is structural, not advisory.

## The conflation trap

The failure mode that produces wrong fixes:

1. Agent loses edits → labels it "Windows persistence failure"
2. Applies the Class A fix (atomic write)
3. Next collision happens anyway (because it was Class B)
4. Agent concludes "atomic write doesn't work on this host"
5. Agent either gives up or tries a bigger hammer (full Python rewrite, git checkpoints, etc.)

The correct diagnostic question when edits are lost: **was MY edit missing (Class A), or was PRIOR content missing (Class B)?** The answer determines the fix.

## Why this isn't just "be more careful"

The operator's workspace already has rules about edit-then-verify and read-before-write. Those rules are necessary but not sufficient — they tell the agent to verify, but not what to do when verification fails. The two-class distinction tells the agent what fix to apply based on which class of failure verification detected.

This is the same structural-fix pattern documented in [[external-state-cross-check-as-structural-fix]]: when a rule fails repeatedly (edit-then-verify was a rule; edits still got lost), the structural fix is to derive the correct intervention from the failure's class, not to repeat the rule more emphatically.

## Applicability beyond this host

The two-class distinction is host-agnostic:

- **Class A (persistence):** more common on Windows, rare on POSIX. POSIX editors generally have fewer persistence glitches because of different fsync/replace semantics.
- **Class B (collision):** equally common on any multi-agent host. Anywhere multiple processes edit the same file without locking, sequential collision is the dominant failure mode.

The file-shape → write-pattern mapping applies everywhere. The specific tools (`search_replace`, `Write`, Python `open(path, 'a')`) are host-specific, but the pattern (append for logs, conditional for shared docs, in-place for one-writer files) generalizes.

## Falsifier

If, after adopting the two-class distinction and matching write patterns to file shapes, the next multi-agent session still loses edits:
- **to Class A persistence failure despite atomic write:** the atomic-write pattern is broken on this host — investigate `os.replace` semantics on NTFS for the specific file path
- **to Class B collision despite append/conditional write:** the write pattern wasn't matched to the file shape correctly — either the file was misclassified, or the conditional-write retry logic has a bug

If neither happens for 30 days across 5+ multi-agent sessions, the distinction is working.

## Related

- `P:/tmp/file-editing-protocol-v2-019f819a.md` — the full protocol based on this distinction
- `P:/tmp/file-editing-protocol-for-review.md` — v1, which conflated the two classes (the artifact this concept exists to correct)
- [[plausible-narratives-substitute-for-verification]] — Disguise 5 (metadata-self-report-as-answer) is adjacent: treating "edit tool returned success" as evidence the edit persisted
- [[external-state-cross-check-as-structural-fix]] — the structural-fix pattern this concept applies (verification of persistence = external state the actor cannot self-certify)
- [[worktree-writes-dont-sync-to-canonical]] — a different multi-agent file coordination failure with a different fix

## Auto-related

- [[claude-code-skill-failure-patterns]]
- [[learn-skill-scoring-fix-summary]]
- [[rule-not-fired-vs-rule-doesnt-exist]]
- [[grok-pretooluse-matcher-and-readonly-fastpath]]
- [[portfolio-deep-read-transferable-techniques]]

## Sources

- Session 2026-07-21 — 13 log entries lost to sequential collision; root cause documented in `wiki/log.md` line 1-10 by the session that discovered the loss
- Session 2026-07-21 — review of v1 file-editing-protocol (`P:/tmp/file-editing-protocol-for-review.md`) revealed the conflation; v2 (`P:/tmp/file-editing-protocol-v2-019f819a.md`) codifies the distinction
- [[testing-methodology-both-outcomes-informative]] — the four-outcome model applies here too: a "fix" that addresses one class but not the other is a false positive (appears to work until the other class strikes)
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
