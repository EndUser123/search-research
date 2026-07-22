# Design: Drift-Surfacing SessionStart Hook

**Status:** design approved (in-plan Stage 5)
**Date:** 2026-07-21
**Author:** Session 019f8523-d9f7-73c3-9e25-9e6c417cfccd (via `/go plan triage-review-findings-2026-07-21`)
**Related:** `P:/docs/plans/triage-review-findings-2026-07-21.md` Stage 5; finding I-1 in `P:/.artifacts/.../grok-review/session-20260721/.../FINDINGS.md`

---

## Problem

`P:\.grok\skills\handoff\SKILL.md` Hard Constraint #7 mandates: *"When `/handoff list --head <sha>` shows `head:DRIFT` or `head:?` for a handoff... before resuming work on such a handoff, run `/handoff verify <path>` and either (a) bump `accurate_as_of_head` to current HEAD if all citations still resolve, or (b) fix the citations / close the handoff if any fail."*

The mandate is **advisory**. It depends on the reader happening to run `/handoff list --head <sha>` before resuming work. **Nothing forces it.** Observed drift-endemic: 4 of 6 handoffs sat with `head:DRIFT` for hours before this session corrected it. The "structural fix for drift endemic" must be structural, not advisory.

## Goal

A Grok-native SessionStart hook that:
1. **Surfaces** the current drift state across all open handoffs.
2. **Recommends** the remediation command for each drifted handoff.
3. **Fail-open** — never blocks session start, even if drift detection fails.
4. **Coexists** with the existing `qmd_patches_session_start.py` SessionStart hook.

---

## Background

### Existing infrastructure

- `P:/.grok/skills/handoff/__lib/list_handoffs.py` — CLI that emits drift flags (`head:DRIFT`, `head:?`) with `--head <sha>`. Already exists; works correctly.
- `~/.grok/hooks/scripts/qmd_patches_session_start.py` — existing SessionStart hook (currently the only registered one per `active-surface.last.md`).
- `~/.grok/hooks/active-surface.json` — Grok-native hooks registry (currently lists only the qmd-patches hook).
- `~/.grok/hooks/hooks.json` — alternative hooks registry (per skill-config compatibility).

### Why now

The drift problem was a real session failure mode (2026-07-21 transcript analysis). The `/handoff verify` and `/handoff migrate` CLIs shipped this session make remediation cheap (~1s per handoff). The remaining gap is **surfacing** — the CLIs solve the problem if you know to use them; a hook closes the gap by telling you.

---

## Architecture

### Component

A new Grok-native SessionStart hook:
- **Source:** `~/.grok/hooks/scripts/drift_surface_session_start.py`
- **Registration:** add to `~/.grok/hooks/active-surface.json` (the same file the qmd-patches hook is in)
- **Trigger:** SessionStart event (runs once per session start)

### Algorithm

```
1. Get current git HEAD at P:/ (git rev-parse HEAD).
2. Invoke list_handoffs.py --head <HEAD> at P:/.grok/skills/handoff/__lib/.
3. Parse the drift-flagged rows (head:DRIFT and head:?).
4. If any drift detected:
   - Print a "Drift detected" banner to stderr (NOT stdout; SessionStart hook output should not pollute the user's session output).
   - For each drifted handoff, print:
     - Path
     - Drift type (DRIFT vs no-head-field)
     - Remediation command: `/handoff verify <path>` or `/handoff migrate <path>` as appropriate
5. Exit 0 regardless of drift state. (Fail-open; the hook is informational only.)
```

### Why stderr, not stdout

SessionStart hooks may have their stdout displayed to the user. Drift reports are advisory; they should not be mistaken for skill output or commingled with model prompts. stderr is the conventional channel for hook telemetry on Grok Build.

### Why fail-open

If the hook fails (git not found, list_handoffs.py error, etc.), the session MUST still start. Drift detection is informational; session start is critical. The hook logs the error and returns 0.

---

## Key decisions

### Decision: emit to stderr, not a separate telemetry file

**Rejected alternative:** write drift state to `~/.grok/logs/drift_surface.jsonl` for later analysis.

**Why rejected:** telemetry aggregation is valuable long-term, but the immediate goal is *surfacing* drift to the user. stderr is the simplest surface that meets this goal without adding infrastructure. Telemetry can be added later if usage patterns warrant it.

### Decision: print remediation command per row, not just the path

**Rejected alternative:** print only the path; let the user construct the command.

**Why rejected:** drift reports without remediation commands force the user to remember the skill contract. Per `/handoff/SKILL.md` Hard Constraint #7, the remediation command is `/handoff verify <path>` (or `/handoff migrate <path>` for v0.1 docs without `accurate_as_of_head`). Embedding the command reduces friction and matches the goal of catching drift before it becomes endemic.

### Decision: no automatic remediation in the hook

**Rejected alternative:** the hook could automatically run `/handoff verify --update` on each drifted handoff.

**Why rejected:** automatic remediation violates the "make re-verification cheap and mandatory" structure. Auto-bumping SHAs without user awareness would mask real citation failures (some handoffs legitimately need fixes, not just SHA bumps). The hook surfaces; the user decides.

### Decision: coexist with qmd-patches via separate hook script, not modification

**Rejected alternative:** extend `qmd_patches_session_start.py` to also do drift detection.

**Why rejected:** single-responsibility. The qmd-patches hook does qmd-patch verification (a separate concern). Drift detection is a separate concern. Two scripts, two registrations, both fire on SessionStart. Grok Build supports multiple SessionStart hooks per `~/.grok/hooks/active-surface.json`.

---

## API / Interface Changes

### New file: `~/.grok/hooks/scripts/drift_surface_session_start.py`

```python
"""SessionStart hook: surface handoff drift via stderr."""
import os, subprocess, sys
from pathlib import Path

HANDOFF_LIST = Path("P:/.grok/skills/handoff/__lib/list_handoffs.py")
HEAD = None
try:
    HEAD = subprocess.run(
        ["git", "-C", "P:/", "rev-parse", "HEAD"],
        capture_output=True, text=True, timeout=10,
    ).stdout.strip()
except Exception as exc:
    print(f"[drift-surface] HEAD detection failed: {exc}", file=sys.stderr)
    sys.exit(0)  # fail-open

if not HEAD:
    sys.exit(0)

try:
    result = subprocess.run(
        ["python", str(HANDOFF_LIST), "--head", HEAD],
        capture_output=True, text=True, timeout=15,
    )
    output = result.stdout + result.stderr
except Exception as exc:
    print(f"[drift-surface] list_handoffs failed: {exc}", file=sys.stderr)
    sys.exit(0)

# Parse output for drift-flagged rows.
# list_handoffs emits "<topic>-<date>" rows with flags like "head:DRIFT" or "head:?".
drifted = []
for line in output.splitlines():
    if "head:DRIFT" in line or "head:?" in line:
        # Path is the first whitespace-separated token.
        path = line.split()[0] if line.split() else ""
        if path:
            drifted.append((path, "DRIFT" if "head:DRIFT" in line else "no-head-field"))

if not drifted:
    sys.exit(0)

print(f"\n[drift-surface] {len(drifted)} handoff(s) drifted from current HEAD ({HEAD[:12]}...):",
      file=sys.stderr)
for path, kind in drifted:
    cmd = "/handoff verify" if kind == "DRIFT" else "/handoff migrate"
    print(f"  - {path}  ({kind})  →  {cmd} {path}", file=sys.stderr)
sys.exit(0)
```

### Modification: `~/.grok/hooks/active-surface.json`

Add the new script to the SessionStart event hooks array. (The current file lists `qmd_patches_session_start.py` for SessionStart; we add `drift_surface_session_start.py` alongside it.)

---

## Implementation Sketch

```text
~/.grok/hooks/scripts/drift_surface_session_start.py   # new
~/.grok/hooks/active-surface.json                      # modified: add hook to SessionStart array
```

That's it. No new CLIs, no new libraries, no new dependencies. The hook is a thin wrapper over the existing `list_handoffs.py`.

---

## Data Model

N/A. The hook is read-only: queries `list_handoffs.py`, prints to stderr, exits. No persistent state.

---

## Rollout

1. **Merge:** single PR.
2. **Activate:** the hook fires automatically on next SessionStart. No flag-day.
3. **Observe:** drift reports should appear in stderr for users with drifted handoffs; nothing appears for users with clean handoffs.
4. **Validate:** run a session in a state with at least one drifted handoff; confirm the hook reports it with the remediation command.

---

## Key Decisions (for wiki promotion)

1. **drift detection via stderr** — simplest surface that meets goal; telemetry can be added later.
2. **print remediation command per row** — reduces friction; matches skill contract.
3. **no automatic remediation** — preserves user agency; auto-bump would mask real failures.
4. **separate hook script, not qmd-patches extension** — single-responsibility; both hooks fire on SessionStart.

---

## Open Questions

None. All design decisions are concrete and reversible.

---

## PR Plan

### PR 1: Drift-surface SessionStart hook

- **Files:**
  - **NEW** `~/.grok/hooks/scripts/drift_surface_session_start.py` (~50 lines)
  - **MODIFIED** `~/.grok/hooks/active-surface.json` (add hook entry)
- **Dependencies:** none.
- **Review focus:** fail-open behavior; stderr vs stdout; coexistence with qmd-patches.
- **Acceptance:** hook reports at least one drifted handoff in a test session with a synthetic drift; no false positives on a clean handoff set; session start is never blocked.

---

## Rejected Alternatives

1. **Auto-remediate in the hook** (run `/handoff verify --update` automatically). Rejected because it violates "make re-verification cheap and mandatory" by removing user agency.
2. **Extend qmd-patches to do drift detection.** Rejected because of single-responsibility; two hooks fire on SessionStart and are independently maintained.
3. **Persist drift state to a telemetry file.** Rejected because stderr output meets the goal without adding infrastructure.
4. **Block session start on critical drift.** Rejected because fail-open is required for a SessionStart hook; critical drift is informational, not a session-start blocker.

---

## Self-check

- [x] Goal in one sentence.
- [x] Implementation approach is concrete (file paths, algorithm steps).
- [x] API/interface changes named with file paths.
- [x] Key decisions + rejected alternatives.
- [x] Rollout + verification steps.
- [x] PR Plan with files + dependencies.
- [x] Open questions: none.

Design is complete. Ready for Stage 6 (implementation).