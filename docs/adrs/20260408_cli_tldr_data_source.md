# ADR-20260408-tldr-data-source: TLDR Summary Data Source

**Status:** Accepted
**Date:** 2026-04-08
**Context:** SessionEnd_tldr.py cannot read breadcrumb logs due to data format mismatch, causing empty TLDR summaries ("no activity recorded").

### Problem Statement

TLDR summaries display empty content because SessionEnd_tldr.py's `_collect_session_activity()` function has a **data source mismatch**:

| Expected | Actual |
|----------|--------|
| `state_base / "breadcrumb"` | `breadcrumbs_console_{id}` |
| Line-based: `Edit: file.py` | JSON/JSONL: `{"skill": "tdd", ...}` |
| Tool usage logs | Skill workflow state |

**Evidence:**
- `SessionEnd_tldr.py:162` — Wrong path: `breadcrumbs_dir = state_base / "breadcrumb"`
- `SessionEnd_tldr.py:174-180` — Wrong format: expects lines with "Edit:", "Write:"
- Actual files: `P:/.claude/state/breadcrumbs_console_6e1909dc-2371-4989-972a-0863b7c98bb3/breadcrumb_tdd.json` (JSON format)

### Decision

**Use handoff V2 envelopes as the data source for TLDR summaries.**

Instead of reading breadcrumb logs, SessionEnd_tldr.py will read the existing handoff file and extract activity data from the `resume_snapshot` field.

### Rationale

1. **Consolidation principle**: Handoff already captures session state correctly (verified working April 1, 2026)
2. **No new dependencies**: Reuses existing infrastructure vs maintaining parallel data sources
3. **Data format match**: Handoff JSON schema is known and stable vs parsing breadcrumb JSONL
4. **Separation of concerns maintained**: TLDR (human-readable briefings) and handoff (machine-readable restoration) serve different purposes

### Alternatives Considered

| Option | Description | Pros | Cons | Why Rejected |
|--------|-------------|------|------|--------------|
| **Chosen** | Use handoff data source | Fixes immediate problem, reuses working system, no new dependencies | Requires handoff file to exist | N/A |
| Parse JSON breadcrumbs | Rewrite `_collect_session_activity()` | Preserves current architecture | Breadcrumb format unstable, adds parsing complexity, duplicates data collection | Higher complexity for same outcome |
| Disable TLDR | Remove SessionStart/SessionEnd_tldr.py | Eliminates broken code | Loses human-readable session briefing | User values TLDR functionality |

### Tradeoffs

| Quality | Improved | Degraded |
|---------|----------|----------|
| Maintainability | Single data source vs two parallel systems | None |
| Reliability | Uses proven handoff system | TLDR depends on handoff being written |
| Performance | Eliminates redundant file scanning | None |

### Multi-Terminal Safety

- **Safe**: Handoff files are terminal-scoped (`console_{terminal_id}_handoff.json`)
- **No shared state**: Each terminal reads its own handoff file
- **Atomic reads**: Handoff storage uses file locking

### Contract Authority Packet

```yaml
contract_authority_packet:
  packet_version: "1"
  contract_sensitive: true
  authority:
    closure_source: "contract_authority_packet"
    prose_role: "explanatory_only"
  boundaries:
    - boundary_id: "tldr-handoff-read"
      producer: "PreCompact_handoff_capture.py"
      consumer: "SessionEnd_tldr.py"
      schema:
        id: "handoff-envelope"
        version: "2"
      required_fields: ["resume_snapshot"]
      optional_fields: ["active_files", "current_task"]
      freshness_authority: "handoff file write time"
      invalidation_trigger: "new handoff envelope written"
      precedence_rule: "handoff file wins over stale TLDR summary"
      failure_behavior: "graceful degradation - write summary with limited data"
      validator_owner: "SessionEnd_tldr.py"
      proof_owner: "/verify --contracts"
      downstream_consumers: ["SessionStart_tldr.py"]
```

### Implementation

**File modified:** `P:/.claude/hooks/SessionEnd_tldr.py`

**Change:** Replace `_collect_session_activity()` function:

```python
# OLD (broken - reads non-existent breadcrumb logs)
def _collect_session_activity() -> dict:
    result = {"files_changed": [], "accomplishments": [], "open_items": []}
    state_base = HOOKS_DIR.parent / "state"
    terminal_id = _resolve_terminal_id(None)
    # ... attempts to read breadcrumb logs that don't exist ...

# NEW (fixed - reads handoff envelope)
def _collect_session_activity_from_handoff() -> dict:
    """Extract activity data from handoff V2 envelope."""
    result = {"files_changed": [], "accomplishments": [], "open_items": []}

    try:
        # Import handoff storage
        sys.path.insert(0, str(Path(__file__).parent.parent / "packages" / "handoff" / "scripts"))
        from handoff_v2 import HandoffFileStorage

        storage = HandoffFileStorage(project_root, terminal_id)
        handoff = storage.load_raw_handoff()

        if handoff:
            snapshot = handoff.get("resume_snapshot", {})

            # Extract goal as accomplishment
            goal = snapshot.get("goal", "")
            if goal:
                result["accomplishments"].append(f"- Worked on: {goal}")

            # Extract active files
            active_files = snapshot.get("active_files", [])
            if active_files:
                result["files_changed"] = [f"- {Path(f).name}" for f in active_files[:5]]

            # Extract current task as open item
            current_task = snapshot.get("current_task", "")
            if current_task and current_task != goal:
                result["open_items"].append(f"- {current_task}")

    except Exception as e:
        logger.warning("SessionEnd_tldr: failed to read handoff: %s", e)

    return result
```

**Testing approach:**
1. Create session with activity
2. Trigger SessionEnd hook
3. Verify TLDR summary contains goal and active files
4. Verify SessionStart displays TLDR content

**Rollback:** Restore original `_collect_session_activity()` function if issues arise.

### Consequences

- **Positive:** TLDR summaries will display actual session activity instead of "no activity recorded"
- **Negative:** TLDR depends on handoff being written (mitigation: graceful degradation if handoff missing)
- **Neutral:** TLDR and handoff remain coexisting systems with different purposes

### Open Questions

None. Implementation-ready.

---

**Confidence:** 85% — Evidence basis: Handoff system verified working (file examination), data format validated (JSON schema read), existing TLDR architecture analyzed.

**Adversarial Self-Review:**
Weakest assumption: Handoff file always exists when SessionEnd fires. If wrong: Handoff write failed or was skipped. Mitigation: Function already has try/except with graceful degradation.
