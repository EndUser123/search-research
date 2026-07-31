---
thread_id: ship-workflow-improvements-20260730
parent_handoff_path: none
current_session_id: 019fb177-e5d5-7520-92f5-0158f87639c9
current_terminal_id: 3c773c60-e09f-490c-a96b-b14fa5208849
produced_at: 2026-07-30T20:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 32395cc
---

# Handoff — /ship profile + workflow improvements + Stop hook false-positive fix

## Objective

Design and build the /ship profile for /go, fix workflow friction identified by /tp analysis, and fix the Stop hook false-positive that blocked aligned CLOSE INCOMPLETE output.

## Status

OPEN — code complete and committed, but /ship untested against a real feature branch.

## Read-first list

1. `C:/Users/brsth/.grok/skills/go/SKILL.md` — ship profile at Step 4 (`### ship`), Phase 0-5 + receipt template
2. `C:/Users/brsth/.grok/skills/ship/SKILL.md` — /ship alias skill
3. `C:/Users/brsth/.grok/hooks/scripts/close_enforcement_gate.py` — Stop hook with false-positive fix
4. `C:/Users/brsth/.grok/skills/close/__lib/close_runner.py` — blocked vs malformed terminal state fix

## Verified facts

- [FACT] /ship profile exists in go/SKILL.md with 5 phases, don't-merge matrix, SHIP BLOCKED output (commits `454e4e2`, `8f8b0be`, `1447cbd`, `c36b2dd`)
- [FACT] /ship alias skill registered and visible in session skill catalog (commit `0cbf0cc`)
- [FACT] Stop hook false-positive fixed: only blocks when model CLAIMS COMPLETE but scanner disagrees (commit `137cc90`)
- [FACT] close_runner distinguishes "blocked" (gates unresolved) from "malformed" (bad output) (commit `3f69bc0`)
- [FACT] 95 tests pass (23 hook + 44 runner + 28 acceptance)

## Current state

**Done (committed on main):**
- /ship profile: Phase 0 (branch detection with confidence tiers + health-check default), Phase 1 (self-review), Phase 2 (fix-loop max 2), Phase 3 (12-check verify), Phase 4 (safe-merge), Phase 5 (auto-close prep)
- /ship alias skill
- Stop hook false-positive fix
- close_runner blocked vs malformed label fix

**NOT done (deferred):**
- /ship first real test against a feature branch
- Stop hook live test after Grok restart (operator restarted; hook should now be active)
- Full SHIP DONE receipt using the enhanced template (my run produced a thin receipt)

## Task packets

### SHIP-TEST-01: First real /ship run

- **goal:** Run /ship on a real feature branch end-to-end
- **acceptance:** SHIP DONE receipt produced with all fields filled (review, verify, docs, spec, breaking, rollback)
- **falsifier:** /ship crashes or produces an incomplete receipt
- **verification level required:** LIVE_BEHAVIOR

### SHIP-RECEIPT-01: Mechanical receipt generator

- **goal:** Build `~/.grok/skills/go/__lib/ship_receipt.py` that mechanically collects git state + runs Phase 3 checks + assembles the SHIP DONE receipt. The LLM fills only review verdict + handoff/wiki fields.
- **problem:** The LLM produces thin receipts (missing fields, understated check disclosure). Code enforcement ensures every field is populated.
- **in scope:** git state collection (branch, HEAD, commits, diff stat), test runner invocation + parsing, lint invocation, doc-check invocation, receipt assembly from template
- **out of scope:** review specialist (LLM judgment), handoff writing (LLM judgment), merge logic (already in SKILL.md)
- **acceptance:** running `python ship_receipt.py --repo <path> --since <merge-base>` produces a complete SHIP DONE receipt with all 13 fields populated or explicitly marked SKIP
- **falsifier:** receipt is missing fields or contains placeholder text instead of real data
- **verification level required:** UNIT_TEST

## Resumption protocol

1. Create a small feature branch with a trivial change
2. Run `/ship` — verify Phase 0 branch detection, Phase 1 review, Phase 3 verify all fire
3. Check the receipt has all fields from the template (lines 917-937 of go/SKILL.md)

## Suggested next invocation

```
/go test /ship on a trivial branch change — verify all phases fire and the receipt is complete
```

---

## Revision 1 — 20260731T050000Z (session 019fb177)

**Trigger:** auto-update — SHIP-RECEIPT-01 completed, usability fixes applied, ship_receipt.py built and tested.

**What changed since the original:**

- **SHIP-RECEIPT-01: DONE.** Built `~/.grok/skills/go/__lib/ship_receipt.py` (692 lines). Mechanically collects git state, runs 6 Phase 3 checks scoped to changed files, DERIVES the SHIP DONE/BLOCKED verdict from check results. Tested against real workspace state — produced clean SHIP DONE with exit code 0. Dogfooded itself (caught its own lint violations). Commits: `07c863d`, `ba5ae88`.
- **Spawn gate test fix.** `mistral-medium-latest` was correctly added to `spawn_broken` set but test still used it as "allowed model." Fixed test + added spawn_broken coverage. Commit `485aebc`.
- **Usability fixes (from /tp cold-read critique).** 5 fixes: deleted 42-line reference list (dual-path hazard), enriched blocker detail (`--tb=short` + failing test names), enriched ship alias, dropped misleading `--since` placeholder, added re-run-after-fix recipe. Commit `85d87bd`.
- **Phase 3 rewired.** go/SKILL.md Phase 3 now calls ship_receipt.py at Step 3a instead of 12-item manual list. Old list deleted (dual-path hazard). Commit `07c863d`.
- **SHIP-TEST-01: PARTIALLY DONE.** Ran `/ship` in health-check mode (on main, no feature branch). Script produced correct SHIP DONE. NOT tested against a real feature branch with merge.

**Updated evidence:**
- `07c863d` — ship_receipt.py + SKILL.md wiring
- `485aebc` — spawn gate test fix
- `ba5ae88` — lint fixes (script caught its own issues)
- `85d87bd` — 5 usability fixes from /tp critique
- `2479080`, `7c9971d`, `17c9e6c` — wiki concepts for the design decision

**Status update:** SHIP-RECEIPT-01 is DONE. SHIP-TEST-01 is partially done (health-check tested, feature-branch merge NOT tested). The remaining task is a real `/ship` run against a feature branch with a merge.

**New open items:**
- SHIP-TEST-01 remains: test `/ship` on a real feature branch with Phase 4 (safe-merge) firing
- 3 failing tests in close skill test suite (503 service unavailable — network-dependent, pre-existing, not our changes)
