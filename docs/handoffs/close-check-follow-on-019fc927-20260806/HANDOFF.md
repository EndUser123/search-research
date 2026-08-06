---
thread_id: close-check-follow-on-019fc927
parent_handoff_path: P:/docs/handoffs/system-redesign-deferred-phases-20260802/HANDOFF.md
current_session_id: 019fc927-d207-7c41-a512-5e90ff0c8b91
parent_session: 019fc0a7-b736-7eb3-8974-ede7d60cc647
current_terminal_id: grok-019fc927
produced_at: 2026-08-06T22:00:00Z
last_updated_by: 019fc927-d207-7c41-a512-5e90ff0c8b91
last_updated_at: 2026-08-06T22:00:00Z
status: open
handoff_type: implementation
accurate_as_of_head: HEAD
---

# Handoff: Close-Check Git-State Hygiene — Follow-On Work

## Objective

Implement the remaining units from the close-check git-state hygiene design that were NOT shipped in the core fix (commit `f1d6956`). The core fix (Path B override + raw_lines error guard) is shipped and working. These units are incremental improvements.

## Status

OPEN — core fix shipped. Follow-on units deferred pending production evidence.

## Context

The core fix (commit `f1d6956` in ~/.grok) changed the close-check `git_state` gate to stop blocking on sibling-session dirty files. It addresses Path B (the persistence override at line ~2624) and adds a `raw_lines` error guard. Both blocking paths from the design doc are addressed for the dominant case.

What remains: Path A (receipts-empty branch at line 2577) still escalates when `session_write_paths` is empty. The design doc proposed a receipts fallback (Unit C-modified), but the `/risks` assessment proved it's structurally broken for subagent-heavy sessions because parent receipt files don't contain child subagent writes.

## Design doc

The full design doc (676 lines, 4 rounds of review) is at:
`C:\Users\brsth\AppData\Local\Temp\grok-design-f1f76075\design-doc.md`

**Note:** temp file — may be reaped by OS. Key decisions and file change inventory are in this handoff.

## Shipped (commit f1d6956)

| Change | What | Lines in close_accounting.py |
|--------|------|------------------------------|
| Path B override | Stop escalating `pre_satisfied` to `needs_llm_check` on unclean persistence checks. Now informational. | ~2624-2640 |
| raw_lines error guard | If `scan_git_status` errored, don't allow `pre_satisfied` via override. Escalate to `needs_attention`. | ~2533, ~2592 |

## Follow-on units (deferred)

### Unit 1: Subagent-receipt aggregation (CRITICAL prerequisite for Path A fix)

**Problem:** `_extract_session_write_paths` only scans the parent session's transcript. Subagent writes go to child session transcripts and child receipt files (`mutation-receipts-{child_session_id}.jsonl`). The parent's receipt file does NOT contain child writes.

**What to build:** Enumerate child session_ids from the parent's `spawn_subagent` calls in the transcript, then aggregate receipts across all child sessions. The aggregated set becomes the session-owned path set.

**Acceptance:** A session with 5+ subagent calls where subagents wrote files → the aggregated receipt set includes child writes → Path A can use receipts as a real fallback.

**Falsifier:** If the aggregated set still misses >10% of subagent writes, the receipts fallback is insufficient.

### Unit 2: Receipt-coverage monitor (diagnostic)

**Problem:** Receipts fail open under timeout (hook timeout → no receipt → no attribution data). Today, no monitor detects this.

**What to build:** `P:/.agents/scripts/monitor_receipt_coverage.py` — reads receipt JSONL files and transcript files for the trailing 1-hour window, computes coverage ratio. Exit codes: 0 (≥90%), 1 (70-89%), 2 (<70%).

**Acceptance:** Synthetic JSONL fixtures with known coverage produce correct exit codes.

### Unit 3: Session-aware push helper (orthogonal)

**Problem:** 7-25 unpushed commits accumulate at session end. The AGENTS.md "push at session end" recommendation exists but is not mechanically surfaced.

**What to build:** `~/.grok/skills/handoff/__lib/session_push_helper.py` — reads commit count ahead of origin, emits a `Note:` when >3. Never auto-pushes. Handles both P:/ and ~/.grok repos.

**Acceptance:** `--dry-run` mode runs end-to-end with no push side effect.

### Unit 4: Wiki propagation

Update 3 wiki concepts to reference the shipped fix:
- `chronic-git-state-hygiene-shared-tree-is-structural.md` → add §"Shipped targeted fix"
- `session-write-path-attribution-gap-no-receipts.md` → update detection signals
- `git-state-drift-multi-repo.md` → update remediation pointer

## Hard constraints

1. Do NOT modify `git_state_check.py` or `dirty_age.py` — both are untouched per DEC-8
2. Do NOT create a separate receipts helper that re-parses the JSONL format — reuse `load_session_receipts()` from `receipt_commit.py`
3. Do NOT add `--json` / `--attribution-json` flags to wrapper scripts — dead code per the design trimming
4. The Path A receipts fallback (Unit 1) is BROKEN without subagent-receipt aggregation — do not ship it standalone

## Resumption protocol

1. Read the design doc if it still exists (temp file, may be reaped)
2. Read the wiki concept: `P:/.data/wiki/concepts/chronic-git-state-hygiene-shared-tree-is-structural.md`
3. Read `close_accounting.py` lines 2530-2640 to see the shipped fix
4. Start with Unit 1 (subagent-receipt aggregation) — it's the CRITICAL prerequisite
5. Then Unit 2 (monitor) and Unit 3 (push helper) in parallel
6. Unit 4 (wiki) last

## Epistemic labels

- [FACT] Core fix is shipped and syntax-valid (commit `f1d6956`, `py_compile` PASS)
- [FACT] Subagent receipts are partitioned by session_id (verified by `/risks` critic 1 reading `mutation_receipt.py:177`)
- [INFERENCE] The core fix will eliminate the dominant false-BLOCKED verdict (untested in production — requires a real close-check run to verify)
- [UNKNOWN] Whether Path A (receipts-empty) fires frequently enough in production to justify Unit 1's complexity

## Suggested next invocation

```
/go implement subagent-receipt aggregation for close-check Path A
```
