# ADR-20260327: Extract Layer0 Scanner from GTO into Shared Skill Layer

**Status:** Proposed
**Date:** 2026-03-27
**Decider:** Architectural review via /arch
**Target:** `P:/packages/search-research` → `~/.claude/skills/`

---

## Context

GTO v3.5 embeds filesystem walking logic in each of its 21 detector modules. Four project-root-walking detectors (`CodeMarkerScanner`, `DependencyChecker`, `DocsPresenceChecker`, `TestPresenceChecker`) each implement near-identical `rglob` + filter loops with inconsistent security properties:

- `CodeMarkerScanner` (`lib/code_marker_scanner.py`): has path-escape prevention (`resolve()` + `relative_to()` guard), `.gitignore` loading, SKIP_DIRS enforcement, symlink guards, max-file-size filtering
- `DependencyChecker` (`lib/dependency_checker.py`): walks `*.py` files with no path sanitization, no symlink guards, no size limits
- `DocsPresenceChecker` (`lib/docs_presence_checker.py`): same — no path sanitization, no symlink guards
- `TestPresenceChecker` (`lib/test_presence_checker.py`): same — no path sanitization, no symlink guards

The remaining detectors (`HistoryScanner`, `AdjacentFileScanner`, session/transcript parsers) walk different surfaces (`~/.claude/projects/`, transcript JSONL) and are out of scope.

Evidence: `gto_orchestrator.py:524-589` (`_run_detectors()`) calls each detector as a direct function. No scanner abstraction exists. `code_marker_scanner.py:1-60` shows the full scanner interface: `.gitignore` awareness, path sanitization, symlink guards, max-size limits.

---

## Decision

**Extract a Layer0 `FileScanner` base class to `~/.claude/skills/_shared/scanners/`** and refactor the four project-root-walking detectors to consume scanner output instead of embedding their own `rglob` loops.

The two non-project-root detectors (`HistoryScanner`, `AdjacentFileScanner`) remain unchanged.

---

## Architecture

### Layer Separation

| Layer | Responsibility | Example |
|-------|---------------|---------|
| **Layer0: Scanner** | Pure filesystem traversal → raw file list | `FileScanner.scan()` returns `list[Path]` |
| **Layer1: Detector** | Gap logic on scanner output | `CodeMarkerDetector.detect()` |
| **Layer2: Orchestrator** | Dispatches detectors, aggregates results | `gto_orchestrator._run_detectors()` |

### Shared Scanner Interface

```python
# ~/.claude/skills/_shared/scanners/base.py

from dataclasses import dataclass
from pathlib import Path

SKIP_DIRS = {".git", "__pycache__", ".claude", "node_modules", ".venv", ".env"}
MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB

@dataclass
class ScanResult:
    files: list[Path]
    skipped_dirs: list[str]
    scan_time_ms: float

class FileScanner:
    """Layer0: pure filesystem traversal. No gap logic."""

    def __init__(
        self,
        root: Path,
        *,
        skip_dirs: frozenset[str] = SKIP_DIRS,
        max_file_size: int = MAX_FILE_SIZE,
        follow_symlinks: bool = False,
    ) -> None:
        ...

    def scan(self) -> ScanResult:
        """Walk root, apply filters, return raw file list."""
        ...

    def _is_safe(self, path: Path) -> bool:
        """Path sanitization: resolve + relative_to guard."""
        ...

    def _should_skip(self, path: Path) -> bool:
        """Check .gitignore, skip-dirs, max-size, symlink guards."""
        ...
```

### Refactored Detectors

Each detector becomes a thin consumer of `FileScanner`:

```python
# In gto/lib/code_marker_scanner.py (refactored)

from gto_skills_shared.scanners.base import FileScanner

class CodeMarkerScanner:
    """Layer1: gap detection on scanner output."""

    def __init__(self, project_root: Path) -> None:
        self.scanner = FileScanner(project_root)

    def scan(self) -> CodeMarkerResult:
        files = self.scanner.scan().files
        # Detector logic only — no filesystem walking
        markers: list[CodeMarker] = []
        for f in files:
            if f.suffix in {".py", ".md", ".txt", ".yaml", ".yml", ".json"}:
                ...
        return CodeMarkerResult(markers=markers, ...)
```

### Migration Strategy

Use `ScannerAdapter` (Candidate D) as a **transitional shim** during the refactor:

1. Define `IScanner` protocol
2. Wrap existing detector scanners as adapters one-at-a-time
3. After all four are wrapped, extract shared `FileScanner`
4. Migrate detectors from adapter → direct `FileScanner` usage
5. Remove adapter shim

This allows incremental migration without a big-bang rewrite.

---

## Rationale

### Why this solves the problem

- **Eliminates duplication**: Four `rglob` + filter loops → one shared `FileScanner`
- **Fixes security gap**: Path traversal prevention currently exists only in `CodeMarkerScanner`. Extraction makes it apply to all four detectors
- **Reduces maintenance**: Any fix to filesystem walking (new skip dir, size limit adjustment) requires one edit, not four
- **Enables caching**: `.gitignore` patterns loaded and cached once per scan; currently re-parsed per detector

### Why not the alternatives

| Candidate | Elimination Reason |
|-----------|------------------|
| **B: Plugin entry-point** | Solves extensibility problem not requested. GTO has one consumer. Runtime discovery adds complexity with zero benefit for solo-dev skill. |
| **C: Status quo** | Does not solve the problem. Security gap in `DependencyChecker` (no path sanitization) is a real vulnerability. |
| **D: Adapter only** | Does not eliminate duplication — wraps duplicated code behind a protocol. The duplication persists. Appropriate only as a transitional migration shim within Candidate A. |

### Evidence

- `gto_orchestrator.py:524-589` — `_run_detectors()` calls 21 detectors directly; no scanner abstraction
- `code_marker_scanner.py:1-60` — scanner interface with full security properties documented
- `dependency_checker.py` (inspected) — walks `*.py` files with no path guards
- Web research: Python plugin architecture (entry-point discovery, abstract base interfaces, lazy loading) — confirms plugin pattern is overkill for single-consumer ecosystem

---

## Tradeoffs

| Dimension | Before | After |
|-----------|--------|-------|
| **Maintainability** | N edits for scanner fix | 1 edit |
| **Security** | 1 of 4 detectors has path guards | 4 of 4 detectors share path guards |
| **Performance** | `.gitignore` parsed N times | Parsed once per scan session |
| **Migration cost** | — | 4 detector modules refactored |
| **Coupling** | Detectors independent | Detectors depend on `_shared/scanners/` |

**Reversibility: 1.25 (Trivial)** — Directory move + import path change. Rollback via `git mv`.

---

## Consequences

### Positive
- All four project-root detectors gain consistent path sanitization, symlink guards, `.gitignore` awareness
- Single point of maintenance for filesystem walking
- Enables future caching optimizations across detector runs

### Negative
- Breaking change: detector modules that were self-contained now import from `_shared/scanners/`
- Migration must be done carefully to avoid behavioral regressions in file filtering order

### Risks
- Shared scanner defaults (SKIP_DIRS, MAX_FILE_SIZE) may not fit all detectors — `DependencyChecker` uses AST parsing and may want different limits than text-based detectors
- Risk mitigation: scanner parameters are configurable at construction; defaults are conservative; detectors that need different limits pass custom params

---

## Edge Case Considerations

**Non-project-root detectors**: `HistoryScanner` (walks `~/.claude/projects/`), `AdjacentFileScanner` (parses transcript JSONL), and session/transcript parsers are explicitly **out of scope**. They walk fundamentally different surfaces and have no duplication with the project-root scanners.

**Windows path handling**: The current `CodeMarkerScanner` uses `resolve()` and `relative_to()` guards. These must be verified to work correctly on Windows (`Path` objects with Windows drive letters, long paths). The test corpus in `code_marker_scanner.py` should include Windows-specific path examples.

**`.gitignore` caching**: If GTO runs multiple detector passes in one session (e.g., rerun after fixes), the shared scanner should cache `.gitignore` patterns to avoid redundant file I/O. Implementation: pass cached `GitIgnore` instance to `FileScanner.__init__()`.

**Circular dependency risk**: `_shared/scanners/` would be imported by detector modules in `gto/lib/`. This creates a dependency from GTO detectors → shared layer, not the reverse. No circular dependency risk.

**Multi-terminal safety**: `FileScanner` is stateless per-call (no in-memory shared state). Each call to `scanner.scan()` is independent. Multi-terminal execution is safe — no shared mutable state.

---

## Implementation Notes

1. Create `~/.claude/skills/_shared/scanners/__init__.py` and `~/.claude/skills/_shared/scanners/base.py`
2. Extract `FileScanner` class from `code_marker_scanner.py`, stripping detector-specific logic
3. Add `IScanner` protocol for adapter shim compatibility
4. Refactor detectors one at a time: `CodeMarkerScanner` → `DependencyChecker` → `DocsPresenceChecker` → `TestPresenceChecker`
5. Add test corpus for `FileScanner` covering: normal paths, path traversal attempts, symlink loops, large files, `.gitignore` patterns
6. Run GTO binary assertions after migration to verify gap detection still works

---

## References

- `P:/.claude/skills/gto/gto_orchestrator.py:524-589` — `_run_detectors()` current implementation
- `P:/.claude/skills/gto/lib/code_marker_scanner.py:1-60` — scanner pattern to extract
- `P:/.claude/skills/gto/lib/dependency_checker.py` — detector lacking path guards
- `P:/.claude/skills/gto/lib/docs_presence_checker.py` — detector lacking path guards
- `P:/.claude/skills/gto/lib/test_presence_checker.py` — detector lacking path guards
- Web research: Python plugin architecture best practices — entry-point discovery, abstract base interfaces, lazy loading
