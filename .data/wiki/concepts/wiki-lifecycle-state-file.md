---
title: "Wiki Lifecycle State File: Design, Tests, and Gaps"
created: 2026-07-20
source: session-2026-07-20
tags: ["wiki", "lifecycle", "state-machine", "atomic-write", "host-agnostic", "observability"]
summary: >
  Lifecycle state file at P:/.data/wiki/_state/<session-id>.json tracking which
  wiki-ingest phases ran in a session. 5-state machine (discovered → ingesting
  → linking → linting → complete) with atomic JSON writes. Single-source-of-truth
  in the phase booleans; state is derived, not stored. Honest about gaps:
  tested happy path only, no concurrent-session coverage, no enforcement gate,
  no cross-host verification.
agent: grok
cognitive_load: 4
verification: "local-only"
host: both
---

## Summary

A lifecycle state file (`P:/.data/wiki/_state/<session-id>.json`) records which phases of a wiki ingestion session actually ran. Backed by a 5-state machine with atomic JSON writes, designed to surface "I forgot to run health-check" type omissions rather than relying on the executor's memory. Currently shipped: `wiki_state.py` (manager) + `wiki_ingest.py` integration. NOT YET shipped: `wiki_health_check.py --lifecycle` flag, `SessionStart` hook surfacing incomplete states, cross-host generalization.

## What it is

Each wiki-touching session gets a state file at `P:/.data/wiki/_state/<session-id>.json` with this shape:

```json
{
  "schema_version": 1,
  "session_id": "lifecycle-smoke-test",
  "agent": "grok",
  "host": "grok",
  "workspace": "",
  "started_at": "2026-07-20T21:36:57+00:00",
  "state": "complete",
  "phases": {
    "ingest_started": true,
    "ingest_completed": true,
    "qmd_updated": true,
    "auto_link_run": true,
    "contradiction_scan_run": true,
    "log_appended": true,
    "health_check_run": false,
    "drift_check_run": false
  },
  "required_for_complete": [
    "ingest_completed", "auto_link_run",
    "contradiction_scan_run", "log_appended", "qmd_updated"
  ],
  "completed_at": "2026-07-20T21:37:03+00:00",
  "exit_clean": true
}
```

## State machine

Five states, transitions explicit (per MindStudio workflow-state-vs-session-state guidance: "each state should represent a distinct phase... avoid creating states that differ only in data values"):

```
discovered → ingesting → linking → linting → complete
            ↓          ↓         ↓
            incomplete (terminal failure branch)
```

- `discovered` — session exists but hasn't touched the wiki
- `ingesting` — state file created, page write in progress
- `linking` — page written, post-write pipeline (auto-link, contradiction scan, log append, qmd update) running
- `linting` — post-write done, health check or drift check in progress
- `complete` — all required phases true, `exit_clean: true`
- `incomplete` — terminal failure branch; session ended before all required phases

State is **derived** from the phase booleans, not stored separately. Single source of truth: the phase booleans. `_derive_state()` is the function.

## Required phases for `complete`

The five phases that must all be `true`:

| Phase | Set by | After step |
|---|---|---|
| `ingest_started` | `wiki_ingest.py` | Before step 1 (verify) |
| `ingest_completed` | `wiki_ingest.py` | After step 1 (verify) succeeds |
| `qmd_updated` | `wiki_ingest.py` | After step 2 (qmd update) succeeds |
| `auto_link_run` | `wiki_ingest.py` | After step 3 (auto-link) succeeds |
| `contradiction_scan_run` | `wiki_ingest.py` | After step 4 (contradiction scan) succeeds |
| `log_appended` | `wiki_ingest.py` | After step 5 (log append) succeeds |

Optional phases (not required for complete, but tracked when run):
- `health_check_run` — for future `wiki_health_check.py --lifecycle` integration
- `drift_check_run` — for future semantic-drift check integration

## Atomic write pattern

Per `python-atomicwrites` / `npm/write-file-atomic` convention:

```python
def _atomic_write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())  # durability across power loss
        os.replace(tmp, path)       # atomic on same filesystem (POSIX + Windows NTFS)
    except Exception:
        try: tmp.unlink()
        except OSError: pass
        raise
```

`fsync` before rename = survives process kill / power loss. `os.replace` is atomic on the same volume. On Windows NTFS, `os.replace` is atomic for files on the same drive (verified).

## What I tested (happy path, smoke test)

A single end-to-end run with `$GROK_SESSION_ID = "lifecycle-smoke-test"` against an existing page:

1. `wiki_ingest.py --post-write agent-failure-modes-2026.md` → all 5 step `ok=True`
2. State file created at `P:/.data/wiki/_state/lifecycle-smoke-test.json`
3. All 5 required phases marked `true`
4. State transitioned: `ingesting → linking → complete`
5. `exit_clean: true` set
6. `completed_at` recorded
7. `wiki_state.py check` returned exit 0 (no incomplete)

**The test was a single happy-path run. It does not prove the system is reliable.** It proves the wiring is correct.

## What I did NOT test (gaps — the honest list)

These are real gaps in the verification. Future testing should close them before relying on the lifecycle for anything load-bearing.

1. **Concurrent sessions on the same session-id** — race conditions possible if two processes mark the same phase simultaneously. Atomic write is atomic per-file but the read-modify-write cycle is not. No file locking.
2. **Failure of wiki_state.py subprocess** — `_mark_phase` swallows all exceptions. If `wiki_state.py` errors out (path doesn't exist, permissions, Python not found), the lifecycle phase is silently never marked. No signal to the operator.
3. **wiki_ingest.py behavior when lifecycle tracking silently fails** — currently returns exit 0 anyway. The ingest appears successful but the lifecycle is incomplete. There is no gate that fails the ingest if lifecycle tracking fails.
4. **`wiki_health_check.py --lifecycle` flag** — not implemented yet. The `wiki_state.py check` command works standalone (returns exit 1 if any incomplete), but health check integration is pending.
5. **`SessionStart` hook surfacing incomplete states** — not implemented. Operator has no automatic visibility into incomplete prior-session lifecycles.
6. **Cross-host behavior** — `_state/` is at a shared path (`P:/.data/wiki/_state/`). If Claude Code sessions write to the same dir with overlapping session-ids, races possible. Not tested.
7. **`fsync` failure semantics** — on some filesystems `fsync` can fail or be silently dropped. Not tested.
8. **Cross-volume rename** — `os.replace` is atomic only on the same volume. If `P:` is a junction/symlink to another volume, atomicity breaks. Not tested.
9. **Long-running session with many wiki touches** — the state file only reflects the most recent `mark()` call. If you mark phase X, then re-mark phase Y, you don't get a history of transitions. The `notes` array captures some but is ad-hoc.
10. **Schema versioning** — `schema_version: 1` is set but no migration path is defined. If the schema changes, old files will silently parse incorrectly.

## Known failure modes (what can go wrong)

Per Saplin's failure-mode taxonomy (`agent-failure-modes-2026`), the lifecycle is itself subject to several modes:

| Mode | How it could happen here |
|---|---|
| **Self-review softness** | The state says `complete` because the executor said so. There's no independent verification that the phases actually ran correctly (e.g., that auto-link ran with real links, not empty results). |
| **Hidden harness control** | The lifecycle tracking is controlled by `_mark_phase` inside `wiki_ingest.py`. If that hook is disabled or the script is modified, the lifecycle goes silent without external signal. |
| **Progress-as-completion** | The state machine has `complete` as a happy terminal state, but a phase can be marked true without the phase's actual work being successful (e.g., `auto_link_run: true` set because the subprocess returned 0 even if the auto-link returned 0 links). |
| **Local patching** | If the executor does partial work (e.g., writes 3 of 5 pages), the lifecycle for one session might show 5 phases marked but only some pages got all 5 steps. Per-page lifecycle isn't tracked — only per-session. |
| **Working-memory rot** | The state file is durable on disk, but the operator/agent's context about it is not. After a compaction or new session, the lifecycle context is gone. |
| **Async reconciliation failure** | If multiple sessions run concurrently, their state files merge inconsistently. No cross-session reconciliation. |

## How to use

**Mark phases automatically** (via `wiki_ingest.py --post-write <page>` — already wired):
```bash
GROK_SESSION_ID=my-session python wiki_ingest.py --post-write P:/.data/wiki/concepts/foo.md
```

**Mark phases manually** (e.g., for ad-hoc operations not through wiki_ingest.py):
```bash
python wiki_state.py init my-session
python wiki_state.py mark my-session health_check_run
python wiki_state.py mark my-session drift_check_run
```

**Check all sessions** (returns exit 1 if any incomplete — wire into CI/automation):
```bash
python wiki_state.py check
```

**Check one session**:
```bash
python wiki_state.py status my-session
```

## Anti-patterns (don't do this)

1. **Don't add `health_check_run: true` from `wiki_ingest.py`** — health check isn't part of the post-write pipeline. It belongs to a separate gate. Don't conflate.
2. **Don't mark phases outside the wiki skill** — the lifecycle is for wiki operations. Other skills have their own state machines (or should). Don't pollute the wiki state file with non-wiki phases.
3. **Don't use the state file as a lock** — atomic write protects against torn writes, not concurrent mark. If two sessions with the same session-id both mark, last write wins, no merge.
4. **Don't delete state files to "fake complete"** — defeats the purpose. If a state file shows incomplete, run the missing phases.
5. **Don't trust `complete` as proof the work was correct** — `complete` means the phases ran, not that they ran with correct outputs. Re-verify via `wiki_health_check.py --json`.

## Related

- [[agent-failure-modes-2026]] — Saplin's taxonomy; this lifecycle is itself subject to several modes
- [[agent-oversight-rubber-stamping]] — operator discipline to actually read the lifecycle state instead of trusting self-report
- [[verification-before-completion-principle]] — the lifecycle implements this principle: state is the tool call that proves a phase ran
- [[grok-build-cc-aca-actually-enabled]] — the cc-aca-* enforcement suite is the runtime analog (PreToolUse gates that fire on every tool call)

## Auto-related

- [[grok-build-plan-mode-structured-thinking]]
- [[i'm-going-to-create-a-hook-to-enforce-discovery-be]]

## Sources

- session-2026-07-20 — `wiki/scripts/wiki_state.py` (created)
- session-2026-07-20 — `wiki/scripts/wiki_ingest.py` (modified: lifecycle integration)
- session-2026-07-20 — `wiki/scripts/wiki_log_append.py` (atomic-write precedent, same `.tmp + os.replace` pattern)
- session-2026-07-20 — Anthropic long-running-agents research (state files as cold-start mitigation)
- session-2026-07-20 — python-atomicwrites documentation (atomic write pattern reference)
- session-2026-07-20 — npm/write-file-atomic (Node equivalent for cross-reference)
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
