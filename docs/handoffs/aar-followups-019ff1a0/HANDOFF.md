---
title: "AAR follow-ups: shared-directory audit + detector false-positive"
session_id: 019ff1a0-26ab-7003-8192-7e653852f6bf
created_at: 2026-08-11T19:55:00Z
status: OPEN
assignee: unassigned
---

# AAR follow-ups from session 019ff1a0

Two INVESTIGATE-disposition opportunities surfaced by `/aar` that need bounded investigation before promoting to action.

## O1 — Audit other skills with shared-directory `--out` defaults

**Source:** AAR session 019ff1a0, opportunity O1

**Observation:** `/packet` had `default="P:/.artifacts"` (shared root) which violated the session-scoping principle (AGENTS.md 2026-08-10). Fixed in commit `6f55e27`. Other skills may have similar defaults.

**Investigation needed:**
- Scan all skills' `argparse` defaults for shared-directory paths (grep for `default=` in `scripts/*.py` across `~/.grok/skills/`)
- Check if any other skill writes artifacts to a shared root by default
- For each hit: is the output ephemeral or durable? Does it risk collision on this multi-agent host?

**Why INVESTIGATE not ACT_NOW:** needs a bounded scan first to determine scope. May find zero additional instances.

## O2 — Detector false-positive: `unused_capability` from directory enumeration

**Source:** AAR session 019ff1a0, opportunity O2

**Observation:** The AAR preprocessor's `detect_unused_capability` detector produced 70 of 92 signals (76%), all LOW severity, all false positives. They flag every file name seen during `list_dir` / `Get-ChildItem` enumeration as a "capability discovered but not invoked." This swamps the signal landscape with noise, making real signals harder to spot.

**Evidence:** `signals.json` for session 019ff1a0 shows 70 `opportunity_candidate_unused_capability` signals, all from event indices 8, 13, 27, 72, 132, 140 — each corresponding to a `list_dir` or `Get-ChildItem` call that enumerated directory contents. Second AAR (20260812) confirmed: 137 of 248 signals (55%) from the same detector on the same session.

**ESCALATED to ACT_NOW (2026-08-12):** chronicity confirmed — 2 instances in one session (70/92 + 137/248). The detector needs a tool-name filter to exclude `list_dir`/`Get-ChildItem` results. No longer INVESTIGATE — evidence is sufficient to implement the fix.

**Investigation needed:**
- Review `detect_unused_capability` in the AAR preprocessor (likely in `~/.grok/skills/aar/__lib/`)
- Add a filter: don't flag capabilities discovered via directory-enumeration tools (`list_dir`, `Get-ChildItem`, `ls`)
- Or: downgrade these to INFO severity so they don't appear in the MEDIUM+ signal landscape

**Why INVESTIGATE not ACT_NOW:** needs confirmation the pattern recurs in other AARs. This is one session's observation.

## Cross-references

- AAR report: `P:/.artifacts/grok-aar/console_console_ff229e6d-d51c-4749-a738-b39b/20260811-aar/aar-report.md`
- Packet session-scoping fix: commit `6f55e27`

---

## Revision 2 — 2026-08-12T12:30:00Z (session 019ff1a0, post-compaction)

**O2 RESOLVED.** The `unused_capability` detector false-positive was fixed
in commit `6b73818`. Added `_DIR_LISTING_TOOLS` frozenset filter +
`tool_call_id -> tool_name` map to skip `list_dir`/`Get-ChildItem`/`glob`/
`find` results before scanning. AAR tests 16/16 pass. Wiki concept written:
`[[aar-detector-false-positives-directory-listing-tool-results]]`.

**O1 still open.** The shared-directory audit has not been run. Still
INVESTIGATE — scan all skills' argparse defaults for shared-directory paths.

**Status update:**
- O1: OPEN (INVESTIGATE)
- O2: RESOLVED (commit `6b73818`)

**accurate_as_of_head:**
- P:/: `116d86c`
- ~/.grok: `4c8c3d8`
