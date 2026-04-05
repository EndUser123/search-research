# ADR-20260322-handoff-sync: Fix PreCompact Capture Sync

**Status:** Accepted
**Date:** 2026-03-22
**Context:** The PreCompact handoff capture has been failing silently since 2026-03-21 due to two separate bugs: (1) the `.claude/hooks/PreCompact_handoff_capture.py` was never updated from the canonical version in `packages/handoff/scripts/hooks/`, and (2) even after copying, the marker file path was wrong (`parent.parent` instead of `parent.parent.parent`), causing `handoff_task_injector` to never find the marker files.

### Decision

1. Copy `packages/handoff/scripts/hooks/PreCompact_handoff_capture.py` → `.claude/hooks/PreCompact_handoff_capture.py`
2. Fix marker path: change `storage.handoff_file.parent.parent / "hooks" / "state"` to `storage.handoff_file.parent.parent.parent / "hooks" / "state"` in both production (`.claude/hooks/`) and source (`packages/handoff/scripts/hooks/`) versions

### Rationale

The runtime hook at `.claude/hooks/PreCompact_handoff_capture.py` is invoked by the hook runner on every PreCompact event. The `packages/` copy is a source artifact. Two failures prevented handoff from working:

1. **Copy never happened**: The ADR was documented but `.claude/hooks/` was never actually updated — it retained the old stale version.
2. **Path mismatch**: Even after copying, `marker_dir = storage.handoff_file.parent.parent / "hooks" / "state"` resolved to `P:/.claude/state/hooks/state/` instead of `P:/.claude/hooks/state/`. The `handoff_task_injector` reads markers from `P:/.claude/hooks/state/` via `_locate_hooks_state_dir()`, so markers were never found.

Fixing both issues restores the compaction marker bridge pattern: PreCompact writes `compaction_marker_{terminal_id}.json` to `P:/.claude/hooks/state/`, and UserPromptSubmit reads it via `handoff_task_injector` to inject handoff context.

### Alternatives Considered

| Option | Description | Pros | Cons | Why Rejected |
|--------|-------------|------|------|--------------|
| **Chosen** | Copy newer to `.claude/hooks/` | Single file copy, instant fix, no build change | None | Optimal |
| Symlink `.claude/hooks/` → `packages/` | Single-source-of-truth | Forces use of canonical file | Relies on `packages/` path being stable; violates `.claude/` isolation principle | Fragile, platform issues |
| Delete `packages/` copy | Eliminates confusion | Removes reference artifact | Loses source tracking | Too aggressive |
| Build-time copy script | Auto-sync on deploy | Prevents drift | Adds deployment complexity, didn't prevent this drift | Over-engineered for solo-dev |

### Tradeoffs

| Quality | Improved | Degraded |
|---------|----------|----------|
| Reliability | PreCompact capture now works (was broken) | None |
| Maintainability | Fewer divergent copies | None |
| Operational Excellence | Simpler mental model (one copy) | None |

### Multi-Terminal Safety

- **Safe** — Hook is terminal-scoped, atomic writes with FileLock already in place, no shared state between terminals.

### Implementation

1. Copy `packages/handoff/scripts/hooks/PreCompact_handoff_capture.py` → `.claude/hooks/PreCompact_handoff_capture.py`
2. In both files (production and source), fix marker path from `storage.handoff_file.parent.parent / "hooks" / "state"` to `storage.handoff_file.parent.parent.parent / "hooks" / "state"` (three `parent` calls, not two)
3. Clear `__pycache__` in `__lib/` to avoid bytecode stale-load
4. Verify: trigger a PreCompact event and confirm marker file appears in `P:/.claude/hooks/state/`

**Rollback:** Revert the file and path to the pre-fix state from git.

### Consequences

- **Positive:** PreCompact capture resumes, handoff context available after compaction (compaction marker bridge pattern now functions)
- **Negative:** None

### Notes

The `handoff_context_injector.py` in `UserPromptSubmit_modules/` is deprecated. It has a three-way mismatch (wrong directory, wrong lookup key, wrong pattern). The active injector is `handoff_task_injector.py` in `packages/handoff/scripts/hooks/`, which uses the compaction marker bridge pattern.
