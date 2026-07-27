---
thread_id: c1f76b67-0a6f-46df-b9c9-0562cdd28fd1
parent_handoff_path: none
current_session_id: 019fa39d-ff7a-7372-96c8-d8b980ec2e88
current_terminal_id: console_1faf8be6-6283-4495-939e-9252
produced_at: 2026-07-27T11:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: c1faa8d
---

# Wiki-query Stop hook: enforce KB consultation before offload

## Objective

Implement a Stop hook (`wiki_query_gate.py`) that prevents AI agents from offloading blockers to the operator without first querying the workspace wiki for documented recovery procedures.

## Status

READY_FOR_REVIEW — design complete (3 review rounds + critical friend), 5 units ready for COMMIT_THIS_SESSION. Design doc in temp; will be reaped by OS.

## Producing context

- Date: 2026-07-27
- Session: 019fa39d-ff7a-7372-96c8-d8b980ec2e88
- Terminal: console_1faf8be6-6283-4495-939e-9252
- Skills run: /why → /www → /www → /design → /www → /go → /check → /review → /wiki

## Read-first list (ordered)

1. `P:/.data/wiki/concepts/error-handling-loops-skip-wiki-query.md` — the /why RCA that identified the gap
2. `P:/.data/wiki/concepts/enforcing-kb-consultation-before-action-methods.md` — external evidence (3 enforcement tiers)
3. `C:\Users\brsth\.grok\hooks\scripts\quality_gate.py` — the architectural template (two-signal Stop hook with shadow-mode rollout)
4. `C:\Users\brsth\.grok\docs\user-guide\10-hooks.md` — Stop hook API (lines 250-270: lastAssistantMessage, decision:block, stopHookActive, reason=="end_turn")
5. `C:\Users\brsth\AppData\Local\Temp\grok-design-1a67780c\grok-design-doc-1a67780c.md` — full design doc (95KB, temp — COPY BEFORE REBOOT)

## Verified facts

- [FACT] Stop hook receives `lastAssistantMessage` — receipt: hooks doc line 261
- [FACT] Stop hook can block with `{"decision": "block", "reason": "..."}` — receipt: hooks doc line 256
- [FACT] 8-continuation cap prevents infinite loops — receipt: hooks doc line 261
- [FACT] `stopHookActive` prevents re-blocking — receipt: hooks doc line 261
- [FACT] Must filter on `reason == "end_turn"` — receipt: hooks doc line 262
- [FACT] Existing `quality_gate.py` demonstrates the exact pattern (lastAssistantMessage scan + transcript scan + shadow-mode rollout) — receipt: read this session
- [FACT] Transcript field names: `name` (str), `arguments` (JSON string) — receipt: `quality_gate.py:1101-1109`
- [FACT] Wiki-path regex must use `[^\"\s]*?` (non-greedy, allows `/`) to match nested concept paths — receipt: F-27 fix in this session's /design run
- [FACT] The wiki predicted the failure by name — `notebooklm-cli-operational-gotchas.md` warns about the exact narrative

## Current state

**Design complete.** 3 revision rounds (26 + 3 + 1 findings addressed), critical friend returned REVISE → F-Field fixed. Design doc at temp path above (~95KB, 7 implementation units).

**NOT implemented.** No code written. The design is a blueprint; Units 1-5 are `COMMIT_THIS_SESSION` ready.

## Task packets

### WQ-01: Measure coupling + extract `_hook_base.py`
- **goal:** Measure DRY/params/touch-points/mixed-concerns across the 6 existing hooks; if ≥2 thresholds met, extract shared base
- **in scope:** `~/.grok/hooks/scripts/quality_gate.py` and the 5 other hook scripts
- **out of scope:** The new wiki_query_gate.py (Unit 2)
- **files:** `~/.grok/hooks/scripts/_hook_base.py` (new), modifications to existing hooks
- **acceptance:** All existing tests pass unchanged; new `_hook_base.py` passes `python -c "import _hook_base"`
- **falsifier:** If coupling measurement shows <2 thresholds met, SKIP the refactor and build the new hook with inline copies
- **verification:** UNIT_TEST
- **estimate:** ~30-60 min (measurement + conditional extraction)

### WQ-02: Implement `wiki_query_gate.py`
- **goal:** Two-signal Stop hook: (1) scan lastAssistantMessage for offload patterns, (2) scan transcript for wiki-query receipts, (3) block iff offload detected AND no receipt
- **in scope:** `~/.grok/hooks/scripts/wiki_query_gate.py` (new)
- **out of scope:** Hook registration (Unit 3), metrics aggregation (Unit 4)
- **files:** `~/.grok/hooks/scripts/wiki_query_gate.py`
- **acceptance:** 25 unit tests pass (offload detection, wiki-receipt detection, negation handling, stopHookActive check, reason filter, shadow mode, receipt_authoritative mode); fail-open on any exception
- **falsifier:** False-positive rate >5% on 100 real agent outputs (measured during shadow mode)
- **verification:** UNIT_TEST
- **key details from design:**
  - Offload patterns: high-precision, low-recall (false positives block legitimate stops; false negatives are the status quo)
  - Wiki-receipt detection: regex `\.data[/\\]wiki[/\\]concepts[/\\][^\"\s]*?\.md` on transcript tool calls using `name` and `arguments` fields
  - Modes: `shadow` (default, log only), `receipt_authoritative` (block)
  - Env var: `GROK_WIKI_QUERY_GATE_MODE`

### WQ-03: Register `wiki-query-gate.json`
- **goal:** Register the hook at the Stop event with 30s timeout
- **in scope:** `~/.grok/hooks/wiki-query-gate.json` (new)
- **out of scope:** Metrics aggregation
- **acceptance:** `/hooks` shows the hook loaded at Stop event; hook fires on a test turn
- **verification:** LIVE_BEHAVIOR

### WQ-04: Add `aggregate_wiki_gate_metrics.py`
- **goal:** Aggregate shadow-mode evidence logs for FP-rate measurement
- **in scope:** `~/.grok/hooks/scripts/aggregate_wiki_gate_metrics.py` (new)
- **acceptance:** Produces FP/TP/FN counts from evidence logs; operator can run it to see "FP rate: X%"
- **verification:** STATIC_INSPECTION

### WQ-05: Document gate in `P:/AGENTS.md`
- **goal:** 3-line pointer to the gate in AGENTS.md
- **in scope:** `P:/AGENTS.md`
- **acceptance:** AGENTS.md has a cross-reference to the gate under the error-handling section
- **verification:** STATIC_INSPECTION

### WQ-06: Phase-1 enforcement (OPERATOR GATE)
- **goal:** After ≥100 shadow events with FP <5%, set `GROK_WIKI_QUERY_GATE_MODE=receipt_authoritative`
- **acceptance:** Gate blocks real offload attempts; no false positives on legitimate stops
- **verification:** LIVE_BEHAVIOR
- **estimate:** Requires ~1-2 weeks of shadow-mode data collection before activation

### WQ-07: nlm-class reproduction (VERIFICATION)
- **goal:** Verify the gate would have caught the original nlm auth failure
- **acceptance:** Replay the nlm session's final message → gate detects offload language → gate checks transcript → no wiki-query receipt → gate blocks
- **verification:** LIVE_BEHAVIOR

## Open decisions

### D-1: Should the gate fire on SubagentStop as well as Stop?
- **Question:** Sub-agents produce 5-10× the volume of main-agent turns. Gating them adds cost but catches sub-agent offloads.
- **Options:** (a) gate only Stop (cheaper, misses sub-agent offloads), (b) gate SubagentStop too (more coverage, 5-10× cost), (c) gate SubagentStop only for offload patterns without receipt (compromise)
- **Selection criterion:** cost vs coverage
- **Current lead:** (c) — measure signal density during shadow mode before committing
- **Evidence that would change lead:** if sub-agent offloads are rare in shadow data, switch to (a)

## Hard constraints

- **Fail-open:** any exception in the hook exits 0 (allow stop). A broken hook must not kill conversation.
- **8-continuation cap:** respect `stopHookActive` — don't re-block on the same condition (the cap is the structural backstop)
- **reason == "end_turn":** filter out session-end fires
- **Shadow mode default:** never ship in `receipt_authoritative` mode without ≥100 shadow events + FP <5%
- **Transcript field names:** use `name` (not `tool_name`) and `arguments` (JSON string, not dict) — per `quality_gate.py:1101-1109`

## Cross-reference couplings

- `~/.grok/hooks/scripts/quality_gate.py` → architectural template for this hook. If quality_gate.py's structure changes, this hook's structure may need to follow.
- `~/.grok/hooks/quality-gate.json` → registration pattern. New hook follows the same JSON structure.
- `P:/.data/wiki/concepts/notebooklm-cli-operational-gotchas.md` → the wiki concept that should have been queried. Not coupled to the hook code, but the hook exists to force agents to find concepts like this.
- `P:/.data/wiki/concepts/error-handling-loops-skip-wiki-query.md` → the /why RCA that motivated this work. The hook is Fix 4 from that RCA.

## Other outstanding streams (not handed off)

- **nlm-to-wiki v3 refactor** — belongs to session 019f9a3c (the other session). Handoff at `P:/docs/handoffs/nlm-to-wiki-v3-refactor-20260727/HANDOFF.md`. That session's work is nearly complete (AC-1 through AC-5 verified live; AC-6 pending operator auth re-check).
- **/design speedup** — complete this session (commits 76b4634, 0d9a41b). Two interaction gaps (R-001, R-002) accepted as documented caveats. No handoff needed.

## Explicit non-goals

- Do NOT implement the hook without the design doc — re-run `/design` if the temp copy is gone
- Do NOT skip shadow mode — the FP rate is unmeasured; blocking with unknown FP rate blocks legitimate stops
- Do NOT use PreToolUse instead of Stop — the offload language appears in the final message at turn end, not at tool-call time
- Do NOT gate ALL offload language — some blockers genuinely require the operator (auth, physical actions, decisions). The gate checks for wiki-query receipt, not for offload alone.

## Resumption protocol

1. Check if the design doc survives: `Test-Path C:\Users\brsth\AppData\Local\Temp\grok-design-1a67780c\grok-design-doc-1a67780c.md`
2. If gone: re-run `/design "Wiki-query Stop hook for offload enforcement"` with the evidence brief content from `P:/.data/wiki/concepts/error-handling-loops-skip-wiki-query.md` and `enforcing-kb-consultation-before-action-methods.md`
3. If survives: read it and implement Units 1-5 via `/go execute`
4. Run shadow mode for ~1-2 weeks before activating enforcement (Unit 6)

## Suggested next invocation

```
/go "Implement the wiki-query Stop hook from the design doc at C:\Users\brsth\AppData\Local\Temp\grok-design-1a67780c\grok-design-doc-1a67780c.md. Start with Unit 1 (measure coupling), then Unit 2 (implement wiki_query_gate.py), Unit 3 (register hook), Unit 4 (metrics), Unit 5 (AGENTS.md pointer). Ship in shadow mode. Do NOT activate receipt_authoritative mode — that's Unit 6, operator-gated."
```

## Last user message (verbatim)

> "/handoff"

## Epistemic labels

- [FACT] All API details (lastAssistantMessage, decision:block, stopHookActive, reason filter, 8-continuation cap) — verified from hooks doc this session
- [FACT] Transcript field names (name, arguments as JSON string) — verified from quality_gate.py:1101-1109
- [FACT] The wiki predicted the failure by name — verified from notebooklm-cli-operational-gotchas.md
- [INFERENCE] "FP rate <5%" threshold is from the design's phased rollout criteria — unmeasured; the actual FP rate is the primary open question
- [INFERENCE] "~1-2 weeks of shadow-mode data" estimate is from the design doc — depends on session volume
- [UNKNOWN] Whether the offload-language regex patterns will have acceptable precision on real agent output — needs shadow-mode measurement
