# ADR-20260328: SQA Multi-Terminal Hardening

**Status**: Accepted

**Date**: 2026-03-28

**Deciders**: Solo-dev architect

---

## Context

SQA orchestrator (`orchestrator.py`) lacks three critical properties for multi-terminal solo-dev environment:

1. **No multi-terminal isolation** — `save_report()` writes to shared path; concurrent terminals overwrite each other's reports
2. **No stale data immunity** — `SQAReport` has no timestamp; reports never expire; staleness cannot be detected
3. **No compact resilience** — `layer2_had_failures` is in-memory boolean; compact event wipes it; L4 hard-dependency gate resets incorrectly after session compaction

**Evidence**: `orchestrator.py:237-239` — non-atomic `write_text()` + `chmod()`. `orchestrator.py:147-171` — `layer2_had_failures` only in function scope. `findings/models.py:85-92` — `SQAReport` has no timestamp field.

**Reusable patterns exist in hooks**:
- `file_lock_manager.py` — `atomic_write()` (temp file → `shutil.move()`), session-isolated lock dirs
- `evidence_store.py` — SQLite WAL mode, `busy_timeout=5000`, session-scoped storage

---

## Decision

Implement **Option A (Atomic Write + Terminal State)** — minimal viable fix addressing all three requirements with ~40 lines changed.

**Option B (SQLite WAL)** deferred to v2 when schema migration cost is justified.

---

## Options Considered

| Option | Complexity | Multi-Terminal | Compact Resilience | Staleness Immunity | Notes |
|--------|-----------|----------------|-------------------|-------------------|-------|
| **A: Atomic + Terminal** | ~40 lines | Terminal-isolated paths | L2 checkpoint to disk | Report timestamp | **Selected** |
| B: SQLite WAL | ~120 lines | WAL mode | DB survives | SQL TTL query | v2 candidate |
| C: Checkpoint/Resume | ~80 lines | Terminal dirs | Layer-level resume | Per-checkpoint | Over-engineered |
| D: Full Evidence Infra | ~200 lines | Shared DB | Full audit trail | TTL on reads | Couples to evidence_store |

---

## Implementation: Option A

### Changes

#### 1. `findings/models.py` — Add timestamp to SQAReport

```python
@dataclass
class SQAReport:
    findings: list[Finding] = field(default_factory=list)
    health_score: int = 100
    layers_completed: list[str] = field(default_factory=list)
    audit_trail: list[AuditEntry] = field(default_factory=list)
    target: str = ""
    timestamp: str = ""  # NEW: ISO UTC timestamp
```

#### 2. `orchestrator.py` — Checkpoint L2 state + atomic writes

**New imports**: `hashlib`

**New helper** — sanitized terminal ID:
```python
def _sanitize_terminal_id terminal_id: str) -> str:
    # Remove anything that isn't alphanumeric or underscore
    sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", terminal_id)
    return sanitized if sanitized else "default"
```

**New helper** — terminal state directory:
```python
def _get_terminal_state_dir() -> Path:
    terminal_id = os.environ.get("CLAUDE_TERMINAL_ID", os.environ.get("TERMINAL_ID", "default"))
    state_root = Path.home() / ".claude" / "sqa_state" / f"terminal_{_sanitize_terminal_id(terminal_id)}"
    state_root.mkdir(parents=True, exist_ok=True)
    return state_root
```

**New helper** — atomic write:
```python
def _atomic_write(path: Path, data: str) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(data)
    os.replace(str(tmp), str(path))  # Atomic on Windows
```

**Checkpoint L2 after Layer 2**:
```python
# After L2 runs, persist layer2_had_failures
state_dir = _get_terminal_state_dir()
target_hash = hashlib.sha256(str(validated).encode()).hexdigest()[:16]
l2_state_file = state_dir / f"{target_hash}_l2.json"
l2_state = {"layer2_had_failures": critical_or_high, "target": str(validated)}
_atomic_write(l2_state_file, json.dumps(l2_state))
```

**Load L2 state on startup** (before Layer 1):
```python
state_dir = _get_terminal_state_dir()
target_hash = hashlib.sha256(str(validated).encode()).hexdigest()[:16]
l2_state_file = state_dir / f"{target_hash}_l2.json"
if l2_state_file.exists():
    # Validate target matches current invocation before trusting stale state
    l2_state = json.loads(l2_state_file.read_text())
    if l2_state.get("target") == str(validated):
        layer2_had_failures = l2_state.get("layer2_had_failures", False)
```

**Update save_report()** — terminal-isolated path + atomic write:
```python
def save_report(report: SQAReport, path: Path) -> None:
    terminal_id = os.environ.get("CLAUDE_TERMINAL_ID", os.environ.get("TERMINAL_ID", "default"))
    report_dir = Path.home() / ".claude" / "sqa_reports" / f"terminal_{_sanitize_terminal_id(terminal_id)}"
    report_dir.mkdir(parents=True, exist_ok=True)
    # Derive filename from target hash (deterministic, cross-platform)
    target_hash = hashlib.sha256(report.target.encode()).hexdigest()[:16]
    terminal_path = report_dir / f"{target_hash}.json"
    # Atomic write
    _atomic_write(terminal_path, json.dumps(asdict(report), indent=2))
```

**Update SQAReport instantiation** — set timestamp:
```python
report = SQAReport(
    findings=findings,
    layers_completed=[ln for ln, _ in layers],
    audit_trail=audit,
    target=str(validated),
    timestamp=datetime.now(timezone.utc).isoformat(),  # NEW
)
```

### Staleness Detection (Read Path)

On report load, check:
```python
def is_report_stale(report: SQAReport, max_age_hours: int = 24) -> bool:
    if not report.timestamp:
        return True  # No timestamp = unknown age = stale
    try:
        report_time = datetime.fromisoformat(report.timestamp.replace("Z", "+00:00"))
        age = datetime.now(timezone.utc) - report_time
        return age.total_seconds() > max_age_hours * 3600
    except ValueError:
        return True  # Malformed timestamp = treat as stale
```

---

## Consequences

**Positive**:
- Concurrent terminals produce isolated reports (no overwrite)
- L2 state survives compact (L4 gate works correctly after resume)
- Reports include timestamp enabling staleness detection
- Atomic write prevents partial-file corruption

**Negative**:
- Report path changes — existing integrations depending on old path break
- Terminal ID dependency on `CLAUDE_TERMINAL_ID`/`TERMINAL_ID` env var (must be set by Claude Code runtime)
- Checkpoint files accumulate — need periodic cleanup (deferred to v2)

**Deferred**:
- TTL enforcement (report cleanup on read) — v2
- SQLite-based structured storage — v2
- Checkpoint-per-layer resume — v2

---

## Verification Plan

| Test | Method | Pass Criteria |
|------|--------|---------------|
| Atomic write | Concurrent `save_report()` from 2 threads | No partial files; both complete |
| Terminal isolation | Run `/sqa` from terminal A and B simultaneously | Reports land in different `terminal_*` dirs |
| Compact resilience | Set `layer2_had_failures=True`; simulate compact; re-run | L4 skips correctly |
| Timestamp present | Run `/sqa`; load report JSON | `timestamp` field is ISO-8601 UTC |
| Staleness detection | Create report with 25h-old timestamp | `is_report_stale()` returns True |
