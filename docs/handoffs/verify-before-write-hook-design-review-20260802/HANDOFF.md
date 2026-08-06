# Handoff: Verify-Before-Write Hook — Design, Red-Team, TP Review

**Session:** 019fc313 (2026-08-02)
**Status:** OPEN — design reviewed, implementation tested, decision point for operator
**Work stream:** PreToolUse hook for external-sourced code constants

## Objective

Design and implement a PreToolUse hook that structurally enforces the "verify-before-write" rule from `inference-in-code-blind-spot.md`. The hook intercepts `write`/`search_replace` tool calls, detects config-flavored numeric constants (POOL, QUOTA, LIMIT, RATE, etc.), and blocks writes lacking a `# verified:` or `# ESTIMATED` annotation.

## What was done

### 1. Hook implementation (COMPLETE — 19 tests pass)
- `~/.grok/hooks/PreToolUse_verify_before_write.py` (265 lines)
- `~/.grok/hooks/verify-before-write.json` (registration, matcher `write|search_replace`)
- `~/.grok/hooks/tests/test_verify_before_write.py` (19 cases: TP, TN, FP, escape hatch, e2e)
- Design doc: `P:/.data/wiki/concepts/verify-before-write-hook-design.md`

### 2. Red-team review (COMPLETE — REVISE verdict)
- 7 specialists, 37 raw findings, 6 root-cause clusters
- Run dir: `P:/.artifacts/red-team/verify-before-write/20260802-095040/`
- SYNTHESIS at: `P:/.artifacts/red-team/verify-before-write/20260802-095040/SYNTHESIS.md`
- Key clusters:
  - RC-1: Raw-text regex (comments/strings trigger FPs; computed values bypass)
  - RC-2: Annotation rubber-stampable (4 specialists — highest amplification)
  - RC-3: Multiple bypass paths (shell, MultiEdit, non-Python files)
  - RC-4: search_replace loses file context
  - RC-5: Timeout + fail-open inverts intent (4s timeout)
  - RC-6: No observability/metrics

### 3. TP review (COMPLETE — REVISE verdict)
- Fresh subagent (1/3 lenses; codex failed flag, agy timed out)
- Key finding: **workspace already has authoritative-receipt infrastructure** (`verification_receipt_writer.py` → `quality_gate.py`)
- The hook invents a parallel annotation contract that is structurally weaker
- The existing pipeline doesn't cover config constants today, but could be extended (~15-30 lines)

## Decision point for operator

Two fix directions, not contradictory:

| Path | Description | Effort | Risk |
|---|---|---|---|
| **A: Ship hook as bridge** | Apply 6-item fix-set, ship as transitional gate | ~30 min | Parallel system until receipt pipeline extended |
| **B: Extend receipt pipeline** | Add `pwm usage` patterns to `verification_receipt_writer.py`, have hook consume receipts | ~2-4 hours | More work, but no parallel system |

**My recommendation:** Path A first (tactical), then Path B (architectural). Ship the bridge now with the annotation contract, migrate to receipt dependency within one release cycle.

## 6-item minimum fix-set (from red-team)

1. Strip comments before `DICT_NUM_RE` matching (closes CM-1 false positive — VERIFIED)
2. Raise timeout 4s→30s + try/except guard (closes PERF-002 — VERIFIED)
3. Require `# verified: <tool>, <date>` structural shape (tightens RC-2 rubber-stamp)
4. Fix deny message: remove `<code>` HTML tags, use `file:///` path (META-01 — VERIFIED)
5. Remove MultiEdit from WATCHED_TOOLS or implement parsing (CM-4 — VERIFIED)
6. Commit files + `/hooks` → `r` to verify activation (WF-01/WF-02)

## Critical unknown

Whether `quality_gate.py`'s receipt consumption logic (line 999: "Check if a VERIFICATION_SUCCEEDED receipt satisfies the obligation") can be trivially extended to check config-constant provenance, or whether it requires architectural changes. This determines whether Path B is 15 lines or 150.

## Files

| File | Location | Status |
|---|---|---|
| Hook script | `~/.grok/hooks/PreToolUse_verify_before_write.py` | Committed (f21e847) |
| Registration | `~/.grok/hooks/verify-before-write.json` | Committed |
| Tests | `~/.grok/hooks/tests/test_verify_before_write.py` | Committed |
| Design doc | `P:/.data/wiki/concepts/verify-before-write-hook-design.md` | Committed |
| Red-team artifacts | `P:/.artifacts/red-team/verify-before-write/20260802-095040/` | Gitignored (on disk) |
| TP context packet | `P:/tmp/tp-verify-hook-context.md` | Temp — cleanup candidate |

## Verification receipts

- Tests pass: `pytest tests/test_verify_before_write.py -v` → 19 passed (receipt from earlier this session)
- Red-team claims verified: 5 directly verified against source (CM-1 comment FP, GAP-005 rubber-stamp, GAP-007 computed values, PERF-02 timeout, META-01 deny message)
- TP finding verified: `verification_receipt_writer.py` confirmed as authoritative receipt producer (lines 1-30 read directly)
