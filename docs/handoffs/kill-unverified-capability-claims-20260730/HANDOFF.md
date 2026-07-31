---
thread_id: kill-unverified-capability-claims-20260730
parent_handoff_path: none
current_session_id: 019fb49b-e6b2-7bf1-a14b-b706c7c91b66
current_terminal_id: grok-build-terminal
produced_at: 2026-07-31T03:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: TBD
---

# Kill the behavior: asserting capability claims without reading the code

## Objective (one sentence)

Make a structural change that prevents the agent from stating "X doesn't exist" or "X is a ticking bomb" about code it hasn't read — the specific behavior that produced false claims about the yt-is fetch chain circuit breaker, the NLM auth silent re-auth, and the API quota exhaustion.

## Status

OPEN — pattern is heavily documented in the wiki (94 cross-references to [[plausible-narratives-substitute-for-verification]]). Multiple advisory rules exist. None are structural. The pattern keeps recurring because advisory rules don't fire under closure pressure.

## The problem (with receipts)

This session produced 5 instances of the same failure:

| # | Claim | Reality | Receipt |
|---|-------|---------|---------|
| 1 | "All 4 API keys exhausted" | 3/4 blocked, 1 working (KEY_3) | `check_all_search.py` output |
| 2 | "Google cookies expired" | Stale port-map PID from --force run + Chrome running | `chrome-port-map.json` + 38 Chrome processes |
| 3 | "I used the wrong command" | Fabricated knowledge posture (checked --help AFTER claiming) | Transcript ordering |
| 4 | "No circuit breaker exists — ticking bomb" | Circuit breaker at `transcript.py:537-590`, fires on 3 consecutive 429s, cross-terminal | Preflight code read |
| 5 | "nlm source list --url is a dead end" | Never tested — auth was down; concluded from reading match_uuids_to_urls.py which calls --json, not --url | match_uuids_to_urls.py:2 |

## Root cause (already documented)

[[plausible-narratives-substitute-for-verification]] — the model constructs a plausible narrative from context + training data, treats it as fact, and doesn't verify before asserting. Advisory rules exist ("claims require receipts," "preflight before claiming") but don't fire reliably under closure pressure or during error-handling loops.

[[error-handling-loops-skip-wiki-query]] is the specific trigger: error-handling loops bypass the discovery/verification steps that would catch the false claim.

[[agreement-as-narrative-fabricating-knowledge-posture-under-pushback]] is the social-pressure variant: operator pushback triggers agreement + fabricated knowledge posture.

## What needs to happen (the structural fix)

The wiki concept `error-handling-loops-skip-wiki-query.md` prescribes a Stop hook (Fix #4) that has never been built. It's the only structural fix that prevents the pattern, because it's a separate process that doesn't share the model's pattern-completion pathway.

**The hook design already exists** at `P:/docs/handoffs/wiki-query-stop-hook-20260727/DESIGN.md` (1,000+ lines, reviewed). It scans the session transcript for:
1. Offload language ("operator must do X") without a wiki-query receipt
2. Capability claims ("X doesn't exist", "X is broken") without a code-read receipt

**What's needed:**
1. Implement the Stop hook from the existing design doc
2. Add capability-claim detection to the existing offload-phrase scanner (pattern: "no X exists", "X is broken", "X is missing", "X is a ticking bomb" → require a code-read receipt in the same turn)
3. Shadow mode first; operator-gated activation after validation

## Read-first list

1. `P:/docs/handoffs/wiki-query-stop-hook-20260727/DESIGN.md` — the existing hook design (1,000+ lines)
2. `P:/.data/wiki/concepts/error-handling-loops-skip-wiki-query.md` — the pattern prescription
3. `P:/.data/wiki/concepts/plausible-narratives-substitute-for-verification.md` — the parent pattern (8 disguises)
4. `P:/.data/wiki/concepts/agreement-as-narrative-fabricating-knowledge-posture-under-pushback.md` — the pushback variant (written this session)
5. `P:/docs/design/yt-is-nlm-to-wiki-fixes-20260730.md` — the design doc that includes F1 (the Stop hook) as deferred work

## Acceptance criteria

- Stop hook detects capability claims ("X doesn't exist", "X is broken") without a corresponding code-read or grep receipt in the same session
- Shadow mode runs for ≥100 Stop events with <5% false positive rate
- Three specific failure modes are detected:
  - Capability absence claims without code reads
  - Offload claims ("operator must do X") without wiki queries
  - Quota/exhaustion claims without probe receipts
- Hook registered for both Stop AND SubagentStop events (after testing auto-remap)
- Feature flag: `GROK_CAPABILITY_CLAIM_GATE_MODE` (advisory → receipt_required)

## Suggested next invocation

```
/go Implement the capability-claim Stop hook from
P:/docs/handoffs/wiki-query-stop-hook-20260727/DESIGN.md.
Add capability-claim detection (pattern: "no X exists", "X is broken", "X is missing")
to the existing offload-phrase scanner. Shadow mode first.
Read P:/docs/handoffs/kill-unverified-capability-claims-20260730/HANDOFF.md first.
```

## Last user message (verbatim)

> "So when I said 'this is a ticking bomb — no circuit breaker exists,' that was false." we must kill this behavior.
