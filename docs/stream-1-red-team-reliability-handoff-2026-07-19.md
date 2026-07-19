# Stream 1: Red-team reliability handoff

| Field | Value |
|---|---|
| **Stream** | Red-team workflow reliability code fixes |
| **Priority** | HIGHEST — prevents silent failure mode observed this session |
| **Status** | **DONE 2026-07-19** — deliverable #1 pre-shipped (commit `22338d0e`), deliverable #2 implemented this session |
| **Effort** | ~45 min (actual: ~35 min for #2 + cache + verification) |
| **Delegation** | One subagent (`capability_mode: execute`); `/agy` reviews after |

## Status (updated 2026-07-19)

| Deliverable | Status | Notes |
|---|---|---|
| #1 Post-dispatch verification (FM-4) | **Pre-shipped** (commit `22338d0e`, 2026-07-19 09:05 -0600) | The handoff was written assuming #1 was unwritten. It is already in `commands/red-team.md` L189-209 — and *exceeds* spec: includes Test-Path gate, retry-once, DEFERRED manifest, `incidents.py` logging, plus an **FM-4b addendum** (L201-209) for dispatch-level failures (rate limits) added after validation incident `inc-a5f7867e3190`. No work needed. |
| #2 Specialist WRITE_FAILED clause | **Done this session** | 10 specialist files updated, version bumped 0.2.24 → 0.2.25, cache rebuilt. See "Implementation log" below. |

**Stale-handoff finding (prominent):** the handoff was written assuming both deliverables were unwritten. Deliverable #1 was not only done but exceeded spec. Only deliverable #2 remained — and it was load-bearing because the FM-4 procedure already referenced `WRITE_FAILED: <reason>` as a valid specialist response, but no specialist had been told it could emit one.

**Scope judgment calls (flagged, not silently made):**
- Planner (`red-team-planner.md`) and critic (`red-team-critic.md`) were **deliberately skipped** — their output contracts are structurally different (planner emits structured prose, critic writes `critic.json` with its own gate path), and FM-4 scopes itself to "after a specialist returns". The /review verify pass later surfaced that FM-3 at `red-team-critic.md:11` (empty-input guard) partially covers critic silent-no-write at the synthesis layer → BLOCK. See INT-002 in Findings.
- Live `/red-team` dispatch test was skipped — handoff's verification criteria #1-#2 test the already-shipped FM-4 gate, not this session's specialist-prompt change.

## Goal

Make `/red-team` catch silent-no-write failures at dispatch time instead of after the critic runs. Three code changes to the red-team plugin source.

## Background (from session 2026-07-19)

During a `/red-team` self-review run, the `red-team-failure-modes` specialist reported success (exit 0, file path in response) but never invoked the write tool. The orchestrator had no post-dispatch verification; the missing file was only caught by manual `Get-ChildItem`. Incident logged as `inc-48fd0ac31fb7`.

Full investigation: `P:/docs/red-team-workflow-reliability-handoff-2026-07-19.md` (sections 1.1, 2.1, 2.2, 2.5).

## Deliverables (2 code changes — merged from original 3)

### 1. Post-dispatch verification with retry-once-and-log policy (~35 lines)

**File:** `P:/packages/.claude-marketplace/plugins/red-team/commands/red-team.md` — §2 (Specialists section), specifically after the line "Collect only the path each specialist returns." This is where the orchestrator reads the dispatch-loop instructions. Do NOT look in `__lib/` — the dispatch loop is prompt-driven, not code-driven.

**Change:** After the sentence "Collect only the path each specialist returns. Do not Read the findings files yourself — that defeats the handoff." (approximately line 189 of the current red-team.md), add:

```
**Post-dispatch verification (mandatory):** After each specialist returns its response text:
1. Extract the file path from the response (it is the sole content of the response per the output rule — one line, no prose).
2. Run `Test-Path <extracted-path>`. If the file exists → proceed to next specialist.
3. If the file does NOT exist → retry once: re-dispatch the same specialist with the explicit instruction: *"You previously failed to write the file. You MUST invoke the write tool before responding. Confirm with Test-Path after writing."*
4. If the retry's file STILL does not exist → log incident (`python "<plugin_root>/__lib/incidents.py" add --category specialist-miss --run-id <run_id> --summary "<specialist> did not write file after retry"`), mark the specialist as DEFERRED in the dispatch manifest, and proceed with the coverage gap (the critic will note the missing specialist).
```

This merges the original deliverables #1 (Test-Path gate) and #3 (retry policy) into one coherent code path, since the check and the retry cannot be separated.

### 2. Agent prompt verification step (~5 lines per specialist, 8+ files)

**Files:** Each specialist agent prompt at `P:/packages/.claude-marketplace/plugins/red-team/agents/red-team-{planner,claim-refuter,gate-reviewer,workflow-reviewer,logic,state,failure-modes,plugin,testing,critic}.md`.

**Change:** Append to each specialist's output rule:

> Your response must contain ONLY the file path, **and the file MUST exist on disk before responding**. If your `write` tool call failed, do NOT report the path; report `WRITE_FAILED: <reason>` instead.

## Dependencies

- None. All changes are to red-team plugin source, independent of other streams.

## Verification criteria

1. After changes, run a test `/red-team` dispatch. The `Test-Path` gate should fire on every specialist.
2. Deliberately dispatch a specialist that doesn't write (simulate the failure). The gate should catch it, retry, and if retry fails, log incident + mark DEFERRED.
3. Plugin cache rebuilt (`plugin-audit-and-fix.py --bump red-team`).

## External review

After implementation, dispatch `/agy` with: "Review these changes to the red-team orchestrator dispatch loop. Does the Test-Path gate actually catch the silent-no-write failure mode? Any bypass path where a specialist could report success without the gate firing?"

## Source references

- `P:/docs/red-team-workflow-reliability-handoff-2026-07-19.md` — full investigation + 5 priorities
- `P:/.claude/.artifacts/019f7a64-4517-7263-9794-24e553c42376/red-team/20260719-133433/_run.json` — the run where the failure occurred
- `P:/.claude/state/red-team/incidents.jsonl` — incident `inc-48fd0ac31fb7`
- `P:/.data/wiki/concepts/subagent-silent-no-write-failure.md` — wiki page documenting the failure mode

---

## Implementation log (2026-07-19)

### Deliverable #2 — shipped (10 specialist files)

Appended a new paragraph after the existing "ONLY the file path" output rule in all 10 specialist agent prompts. The paragraph tells each specialist: (1) the file MUST exist on disk before responding, (2) verify with `Test-Path <path>` (or host equivalent), (3) on write failure respond `WRITE_FAILED: <reason>` instead of a fake path, (4) explains the FM-4 gate behavior (retry once → DEFERRED → incident).

Files modified (line of new paragraph noted):
- `agents/red-team-failure-modes.md` (L24)
- `agents/red-team-gate-reviewer.md` (L40)
- `agents/red-team-logic.md` (L18)
- `agents/red-team-performance.md` (L24)
- `agents/red-team-plugin.md` (L44)
- `agents/red-team-security.md` (L18)
- `agents/red-team-state.md` (L51)
- `agents/red-team-testing.md` (L44)
- `agents/red-team-workflow-reviewer.md` (L39)
- `agents/red-team-claim-refuter.md` (L89 — different anchor sentence, same appended paragraph)

Each edit: +2 lines (new paragraph + blank), 0 deletions. Original "ONLY the file path" rule preserved verbatim in all 10 files (claim-refuter uses a semantically identical short variant).

### Cache + version

- `plugin.json`: 0.2.24 → **0.2.25** via `plugin-audit-and-fix.py --bump red-team`
- Cache rebuilt: `C:/Users/brsth/.claude/plugins/cache/local/red-team/0.2.25/` (27 files synced source→cache)
- Stale cache `0.2.24` removed
- `--sync-dry-run red-team`: 27 identical, 0 divergent
- MD5 hashes: all 12 cache agent files byte-identical to source

### Verification chain

| Step | Tool | Result |
|---|---|---|
| Edit-then-verify (per Windows rule) | grep + read-back | 10/10 ✓ |
| /check (3 verifier concerns: edits+cache, scope judgment, agy conductor) | spawned verifiers | **CHECK PASS** — all 3 PASS |
| /agy external review (USEFUL_DISAGREEMENT) | conductor verification of 6 findings | 4 accepted as valid pre-existing concerns, 2 rejected (both rejections verified sound by /check) |
| /review (2 specialists + 1 independent verifier) | full /review pipeline | **needs_attention** — 0 bugs, 3 risks, 2 suggestions, 1 nit (all verified) |

### Artifacts

- `/check` run dir: `P:/.artifacts/console_4d1b1fcf-6f5b-41ce-a192-1be0/grok-check/20260719-114613-542/`
- `/review` run dir: `P:/.artifacts/console_4d1b1fcf-6f5b-41ce-a192-1be0/grok-review/red-team-local/20260719-115653/`
- `/review` FINDINGS.md: `P:/.artifacts/console_4d1b1fcf-6f5b-41ce-a192-1be0/grok-review/red-team-local/20260719-115653/FINDINGS.md`
- `/agy` raw output: `P:/tmp/agy-red-team-review-prompt.txt` (prompt) + session terminal log (output)
- Terminal state file: `P:/.artifacts/console_4d1b/red-team-state.md`

### Two user actions still pending

1. **Run `/reload-plugins`** to activate red-team 0.2.25 in the TUI (cache is rebuilt but live session still has 0.2.24 loaded).
2. **Inspect staged set before any commit.** The bump script staged 27 files mid-run (including this handoff doc, staged by marketplace sync — not by me). The 10 specialist edits + `plugin.json` bump are unstaged ` M`.

---

## Findings (from /check + /review, 2026-07-19)

**Tally: 0 bugs, 3 risks, 2 suggestions, 1 nit. No blocking issues.** The change correctly closes the contract gap (specialists can now honestly report `WRITE_FAILED` instead of fake-reporting a path). Overall correctness: **patch is correct**.

All 7 findings independently verified against source at HEAD `dbe0932`.

### INT-004 — risk, **pre-existing** (highest leverage)

`writer_session` is documented as required (red-team.md:124; findings_schema.py:4) but `findings_schema.py:14` does NOT enforce it. Combined with FM-4's existence-only Test-Path check (red-team.md:195), a specialist could return a path to a well-formed-but-stale JSON file from a prior run and pass the gate. The new contract's framing ("the file MUST exist on disk") overstates coverage.

**Fix:** Add `writer_session` to `REQUIRED_FINDING_FIELDS`. Instruct specialists to include it. Optionally have FM-4 validate it matches the dispatching session.

*This was the finding I personally hand-waved during the /agy conductor pass — I cited "writer_session field" as a mitigation but the field is not actually enforced. The /check Concern C verifier caught it.*

### INT-003 — risk, introduced by this change

Specialist text embeds FM-4 internals ("retries once", "logs an incident", "marks DEFERRED"). Creates coupling: any future FM-4 change invalidates the specialist text without a mechanical signal. **Precedent:** FM-4b was added at red-team.md:201-209 for dispatch-failure handling without any specialist-file edits.

**Fix:** Reduce specialist text to behavior-agnostic: *"If you fail to write the file, respond with `WRITE_FAILED: <reason>` instead of reporting a path. The orchestrator will detect the missing file and proceed accordingly."* Drop the embedded description of FM-4 procedure.

### INT-001 — risk, introduced by this change

FM-4 step 1 (first-attempt WRITE_FAILED, red-team.md:194) marks the dispatch manifest `DEFERRED — write-failed: <reason>` but does NOT call `incidents.py`. Steps 2 (L199) and FM-4b (L207) both do. The dispatch manifest is a per-run render; `incidents.jsonl` is the Phase 3 improvement loop's input. Result: **honest write failures are invisible to the improvement loop**.

**Fix:** Add an `incidents.py` call to FM-4 step 1 with a new category `specialist-honest-fail`. Pairs with INT-005.

### INT-002 — risk, introduced by this change

FM-4 scopes itself to "after a specialist returns its claimed file path and before invoking the critic" (L191). Planner (writes `prospect.md` conditionally) and critic (writes `critic.json`) have no analogous honest-fail path.

**Mitigation surfaced by /review verify pass** (the integrity specialist missed this): FM-3 at `red-team-critic.md:11` catches critic silent-no-write at the synthesis layer — empty-input guard produces a BLOCK verdict. Planner silent-no-write is uncovered but `prospect.md` is best-effort.

**Fix (recommended option a):** Document the asymmetry explicitly in `commands/red-team.md` and add a comment explaining FM-3 covers critic and planner is best-effort.

### INT-005 — suggestion, introduced by this change

`incidents.py` accepts `--category` values; existing categories are `specialist-miss` (silent no-write after retry) and `other` (dispatch-failure). An honest `WRITE_FAILED` on first attempt fits neither cleanly — `specialist-miss` overstates (the specialist didn't miss, it honestly reported), `other` understates (loses the signal).

**Fix:** Add `specialist-honest-fail` to the category list. Pairs with INT-001's proposed logging addition.

### CORR-001 — suggestion, introduced by this change

PowerShell `Test-Path` returns true for 0-byte files and (default flags) for directories. A specialist that writes an empty file passes both the specialist-side verify AND FM-4 step 2, then gets marked DISPATCHED. Mitigated downstream by critic FM-2 (malformed JSON → BLOCK-severity finding).

**Fix:** Strengthen to `Test-Path -PathType Leaf <path> AND (Get-Item <path>).Length -gt 0`. Mirror in FM-4 step 2.

### CORR-002 — nit, introduced by this change

Specialist paragraph reads *"FM-4 retries once on a missing file, then logs an incident and marks the specialist DEFERRED"*. Strictly read, "then" implies retry → always incident+DEFERRED. FM-4 actually has three branches (retry succeeds → DISPATCHED with note `recovered-after-retry`; retry fails → DEFERRED + incident; honest WRITE_FAILED → DEFERRED — write-failed). Specialist text describes only the middle (worst) case.

**Fix:** Rephrase: *"FM-4 retries once on a missing file; if the retry succeeds, the run continues; if the retry also fails, the orchestrator logs an incident and marks the specialist DEFERRED."*

---

## Follow-ups (recommended priority order)

| # | Finding | Priority | Effort |
|---|---|---|---|
| 1 | **INT-004** writer_session enforcement (pre-existing, closes real bypass) | High | Medium — schema change + specialist instructions + optional FM-4 check |
| 2 | **INT-003** Decouple specialist text from FM-4 internals | Medium | Small — wording change to 10 files |
| 3 | **INT-001 + INT-005** Honest-fail incident logging + category | Medium | Small — `incidents.py` + FM-4 step 1 |
| 4 | **INT-002 option (a)** Document planner/critic asymmetry | Low | Trivial — comment in `commands/red-team.md` |
| 5 | **CORR-001 + CORR-002** Tighten Test-Path + rephrase retry paragraph | Low | Trivial — wording pass |
| 6 | (From /agy, not adopted) Critic glob race at `red-team.md:211` — critic should consult dispatch manifest before globbing to avoid DEFERRED-timeout specialist being silently ingested | Medium | Medium — critic prompt + dispatcher integration |

Items 1–5 ship naturally as one follow-up commit. Item 6 is independent (orchestrator-side, pre-existing) and worth a separate change.
