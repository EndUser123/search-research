#!/usr/bin/env python3
"""
Canonical state resolver foundation (Phase 0C).

Provides classification and resolution for ALL state paths across the
repository, mapping each known state type to its canonical category
and current/legacy roots.  This module is READ-ONLY — it catalogs,
classifies, and resolves paths but does NOT migrate any consumers.

Architecture:
  StateCategory (enum)
      ├── TERMINAL    — scoped to one terminal (anti_sycophancy, followup_context, …)
      ├── SESSION     — scoped to one session  (compaction_marker, session_ledger, …)
      ├── SHARED      — global across terminals/sessions (hook_ledger.db, …)
      ├── LOG         — append-only log files  (tool_use_log, path_errors, …)
      ├── DIAGNOSTIC  — telemetry, metrics     (hook_observability.db, …)
      └── UNKNOWN     — unrecognised pattern   (requires registration)

  Every known state type is registered in TYPE_MAP with:
    - its StateCategory
    - its current root (one of the ACTIVE_ROOTS)
    - an optional canonical (target) root for eventual migration

Usage:
    from state_resolver import resolve_type, inventory, StateCategory

    cat, path = resolve_type("anti_sycophancy_injector", terminal_id="c_1")
    # → (StateCategory.TERMINAL, Path("P:/.claude/state/terminals/c_1/anti_sycophancy_injector.json"))

    report = inventory()
    # → dict of {StateCategory: [paths]} across all roots

Ponytail: stdlib only, zero dependencies, pure path resolution.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Iterator


# ── State classification ──────────────────────────────────────────────────

class StateCategory(Enum):
    """Every flavour of state the resolver knows about.

    Keep this enum in sync with the SDLC target operating model
    Part 0.1 (session / terminal / workspace identity levels).
    """

    TERMINAL     = auto()   # scoped to one terminal_id
    SESSION      = auto()   # scoped to one session_id
    SHARED       = auto()   # global across all terminals and sessions
    LOG          = auto()   # append-only sequence (JSONL, rows)
    SESSION_LEDGER = auto() # session-metadata ledger (.session/ root)
    DIAGNOSTIC   = auto()   # telemetry, metrics, health data
    HIDDEN_STATE = auto()   # .state/ hidden root (ad-hoc, to be migrated)
    CACHE        = auto()   # regenerable cache (cks cache, etc.)
    UNKNOWN      = auto()   # unrecognised — needs registration


# ── Registered roots ──────────────────────────────────────────────────────

# Absolute paths seeded once at import.  Tests override PROJECT_ROOT to
# redirect STATE_DIR into a tmp dir — the same pattern state_paths.py uses.
def _resolve_project_root() -> Path:
    """Derive project root from this module's own location.

    state_resolver.py lives at <project>/.claude/hooks/__lib/state_resolver.py
    → parents[3] is the project root.
    """
    env = os.environ.get("PROJECT_ROOT")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[3]


PROJECT_ROOT      = _resolve_project_root()
STATE_DIR         = PROJECT_ROOT / ".claude" / "state"          # state_paths.py canonical
HOOKS_DIR         = PROJECT_ROOT / ".claude" / "hooks"
HOOKS_STATE_DIR   = HOOKS_DIR / "state"                         # aca_state_paths legacy
HOOKS_DOT_STATE   = HOOKS_DIR / ".state"                        # hidden ad-hoc root
SESSION_DIR       = PROJECT_ROOT / ".claude" / ".session"       # session ledger
HOOKS_DATA_DIR    = HOOKS_DIR / "data"                          # sparse data
HOOKS_LOGS_DIR    = HOOKS_DIR / "logs"                          # diagnostics / metrics

# ── State type registry ───────────────────────────────────────────────────

# Each entry maps a filename regex/prefix → classification.
# The regex is anchored to the basename (lowercased, no extension).
# Ordered: first match wins.  Register new types here.


@dataclass
class StateTypeEntry:
    """Classification for a family of state files."""
    category: StateCategory
    name: str                                          # human-readable type key (for resolve_type)
    current_root: Path
    canonical_root: Path | None = None                 # target for eventual migration
    filename_pattern: re.Pattern | None = None         # regex matching actual filenames (default: derived from name)
    description: str = ""
    consumes_session_id: bool = True
    consumes_terminal_id: bool = True
    is_log: bool = False
    is_deprecated_root: bool = False

    def matches_filename(self, stem: str) -> bool:
        """True when *stem* (lowercased, no extension) matches this type."""
        pat = self.filename_pattern
        if pat is None:
            return stem.startswith(self.name)
        return pat.search(stem) is not None


# ── Registry helpers ──────────────────────────────────────────────────────

def _pat(raw: str) -> re.Pattern:
    """Compile a case-insensitive pattern for filename matching."""
    return re.compile(raw, re.I)


def _entry(
    category: StateCategory,
    name: str,
    current_root: Path,
    canonical_root: Path | None = None,
    *,
    filename_pattern: re.Pattern | None = None,
    description: str = "",
) -> StateTypeEntry:
    """Convenience constructor; filename_pattern defaults to a prefix match on name."""
    return StateTypeEntry(
        category=category,
        name=name,
        current_root=current_root,
        canonical_root=canonical_root,
        filename_pattern=filename_pattern or _pat(re.escape(name) + r"(?:$|[_/.])"),
        description=description or name,
        consumes_session_id="session" in name.lower(),
        consumes_terminal_id="terminal" in name.lower(),
        is_log=category in (StateCategory.LOG, StateCategory.DIAGNOSTIC),
        is_deprecated_root=False,
    )


STATE_TYPE_REGISTRY: list[StateTypeEntry] = [
    # ── Terminal-scoped (P:/.claude/state/terminals/<tid>/…) ──
    _entry(StateCategory.TERMINAL, "investigation_state_console", STATE_DIR / "terminals"),
    _entry(StateCategory.TERMINAL, "pretool_degraded", STATE_DIR / "terminals"),
    _entry(StateCategory.TERMINAL, "lazy_closure_capitulation_console", STATE_DIR / "terminals"),
    _entry(StateCategory.TERMINAL, "delegation_expected", STATE_DIR / "terminals"),
    # ── Terminal-scoped (hooks/state/) with canonical target ──
    _entry(StateCategory.TERMINAL, "anti_sycophancy_injector",
           HOOKS_STATE_DIR / "anti_sycophancy_injector", STATE_DIR / "terminals"),
    _entry(StateCategory.TERMINAL, "followup_context",
           HOOKS_STATE_DIR, STATE_DIR / "terminals"),
    _entry(StateCategory.TERMINAL, "consultation_aware",
           HOOKS_STATE_DIR, STATE_DIR / "terminals"),
    _entry(StateCategory.TERMINAL, "arch_declaration",
           HOOKS_STATE_DIR, STATE_DIR / "terminals"),
    # ── Session-scoped (P:/.claude/state/sessions/<sid>/…) ──
    _entry(StateCategory.SESSION, "compaction_marker", STATE_DIR / "sessions"),
    _entry(StateCategory.SESSION, "auth_gate", STATE_DIR, STATE_DIR / "sessions"),
    _entry(StateCategory.SESSION, "terminal", STATE_DIR, STATE_DIR / "sessions"),
    # ── Session ledger (P:/.claude/.session/) ──
    _entry(StateCategory.SESSION_LEDGER, "session_ledger", SESSION_DIR),
    _entry(StateCategory.SESSION_LEDGER, "reasoning_metrics", SESSION_DIR),
    # ── Hidden state / logs (hooks/.state/) ──
    _entry(StateCategory.LOG, "tool_use_log", HOOKS_DOT_STATE, HOOKS_STATE_DIR),
    _entry(StateCategory.LOG, "path_errors", HOOKS_DOT_STATE, HOOKS_STATE_DIR),
    _entry(StateCategory.LOG, "negation_hits", HOOKS_DOT_STATE, HOOKS_STATE_DIR),
    _entry(StateCategory.LOG, "referent_anchors", HOOKS_DOT_STATE, HOOKS_STATE_DIR),
    _entry(StateCategory.LOG, "agentic_reliability_telemetry", HOOKS_DOT_STATE, HOOKS_STATE_DIR),
    _entry(StateCategory.LOG, "claim_type", HOOKS_DOT_STATE, HOOKS_STATE_DIR),
    # ── Diagnostics (hooks/logs/) ──
    _entry(StateCategory.DIAGNOSTIC, "diagnostics", HOOKS_LOGS_DIR),
    _entry(StateCategory.DIAGNOSTIC, "hook_observability", HOOKS_LOGS_DIR),
    _entry(StateCategory.LOG, "stop_blocks", HOOKS_LOGS_DIR),
    _entry(StateCategory.DIAGNOSTIC, "hook-health-summary", HOOKS_LOGS_DIR),
    _entry(StateCategory.DIAGNOSTIC, "implementation-default-gate-audit", HOOKS_LOGS_DIR),
    # ── Hook data (hooks/data/) ──
    _entry(StateCategory.LOG, "reflexion_verifications", HOOKS_DATA_DIR),
    _entry(StateCategory.LOG, "semantic_compress_log", HOOKS_DATA_DIR),
    # ── Shared state (P:/.claude/state/shared/) ──
    _entry(StateCategory.SHARED, "hook_ledger", STATE_DIR / "shared"),
    # ── Flat files at state/ root that should be in shared/ ──
    _entry(StateCategory.SHARED, "adr_critic", STATE_DIR, STATE_DIR / "shared"),
    _entry(StateCategory.SHARED, "adr_red_team_process_lifecycle", STATE_DIR, STATE_DIR / "shared"),
    # ── CKS cache ──
    _entry(StateCategory.CACHE, "cks_cache", HOOKS_DIR),
]

# Index for O(1) name lookups (built once at import time).
TYPE_NAME_INDEX: dict[str, StateTypeEntry] = {
    e.name: e for e in STATE_TYPE_REGISTRY
}


# ── Resolver functions ────────────────────────────────────────────────────

def classify_filename(name: str) -> StateTypeEntry | None:
    """Match a filename (no path) to its registered state-type entry."""
    stem = Path(name).stem.lower()
    for entry in STATE_TYPE_REGISTRY:
        if entry.matches_filename(stem):
            return entry
    return None


@dataclass
class Resolution:
    """Result of resolving a state type or file to its canonical location."""
    category: StateCategory
    primary: Path                      # canonical (target) path
    current: Path                      # actual write path today
    entry: StateTypeEntry | None = None
    alternate_roots: list[Path] = field(default_factory=list)


def resolve_type(
    state_type: str,
    terminal_id: str = "",
    session_id: str = "",
    filename: str = "",
) -> Resolution | None:
    """Resolve a registered state type to its canonical path.

    Parameters
    ----------
    state_type : str
        The registered type name (e.g. ``"anti_sycophancy_injector"``).
    terminal_id, session_id : str
        Identity scoping — used when the category requires it.
    filename : str
        Optional literal filename to append.

    Returns
    -------
    Resolution or None
        ``None`` when *state_type* matches no registered entry.
    """
    entry = TYPE_NAME_INDEX.get(state_type)
    if entry is None:
        return None

    cat = entry.category
    current_root = entry.current_root
    canonical_root = entry.canonical_root or current_root

    # Build the primary (canonical) path
    primary = _build_path(entry, canonical_root, terminal_id, session_id, filename)
    current = _build_path(entry, current_root, terminal_id, session_id, filename)

    return Resolution(
        category=cat,
        primary=primary,
        current=current,
        entry=entry,
        alternate_roots=_find_alternate_roots(state_type),
    )


def _build_path(
    entry: StateTypeEntry,
    base: Path,
    terminal_id: str,
    session_id: str,
    filename: str,
) -> Path:
    """Construct a resolved path under *base* for the given identity scoping."""
    cat = entry.category
    fname = filename or f"{entry.name}.json"

    if cat == StateCategory.TERMINAL and terminal_id:
        return base / terminal_id / fname
    if cat == StateCategory.SESSION and session_id:
        return base / session_id / fname
    return base / fname


def _find_alternate_roots(state_type: str) -> list[Path]:
    """Return all active roots that contain files matching *state_type*."""
    found: list[Path] = []
    for root in (STATE_DIR, HOOKS_STATE_DIR, HOOKS_DOT_STATE):
        matches = list(root.rglob(f"*{state_type}*"))
        if matches:
            found.append(root)
    return found


# ── Inventory ─────────────────────────────────────────────────────────────

@dataclass
class StateFile:
    """One discovered state file with classification."""
    path: Path
    category: StateCategory
    state_type: str | None = None
    entry: StateTypeEntry | None = None
    size_bytes: int = 0
    modified: str = ""


def _inventory_root(root: Path) -> Iterator[StateFile]:
    """Yield classified StateFile entries for every file under *root*."""
    if not root.is_dir():
        return
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        entry = classify_filename(path.name)
        cat = entry.category if entry else StateCategory.UNKNOWN
        try:
            st = path.stat()
            mtime = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(timespec="minutes")
        except OSError:
            st = None
            mtime = ""
        yield StateFile(
            path=path,
            category=cat,
            state_type=path.stem if entry else "unregistered",
            entry=entry,
            size_bytes=st.st_size if st else 0,
            modified=mtime,
        )


def inventory(
    include_roots: list[Path] | None = None,
) -> dict[str, object]:
    """Build a full inventory of state files across all known roots.

    Returns a dict with keys:
      - ``roots`` : summary per root
      - ``by_category`` : files grouped by StateCategory name
      - ``unknown`` : unregistered file paths (need registration)
      - ``total_files``, ``total_bytes``
    """
    if include_roots is None:
        include_roots = [STATE_DIR, HOOKS_STATE_DIR, HOOKS_DOT_STATE,
                         SESSION_DIR, HOOKS_DATA_DIR, HOOKS_LOGS_DIR]

    by_category: dict[str, list[dict]] = {}
    unknown_entries: list[dict] = []
    root_counts: dict[str, int] = {}
    total_bytes = 0
    total_files = 0

    for root in include_roots:
        count = 0
        for sf in _inventory_root(root):
            total_files += 1
            total_bytes += sf.size_bytes
            cat_name = sf.category.name
            by_category.setdefault(cat_name, []).append({
                "path": str(sf.path),
                "state_type": sf.state_type,
                "size": sf.size_bytes,
                "modified": sf.modified,
            })
            if sf.category == StateCategory.UNKNOWN:
                unknown_entries.append({
                    "path": str(sf.path),
                    "size": sf.size_bytes,
                })
            count += 1
        root_counts[str(root)] = count

    # Sort categories by count descending
    by_category = dict(sorted(
        by_category.items(),
        key=lambda kv: len(kv[1]),
        reverse=True,
    ))

    return {
        "schema_version": "state-resolver.v1",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "roots": root_counts,
        "by_category": by_category,
        "unknown": unknown_entries,
        "total_files": total_files,
        "total_bytes": total_bytes,
    }


def inventory_report(output_path: str | Path | None = None) -> str:
    """Produce a JSON inventory report, optionally writing to *output_path*."""
    report = inventory()
    encoded = json.dumps(report, indent=2) + "\n"
    if output_path:
        Path(output_path).write_text(encoded, encoding="utf-8")
    return encoded


# ── CLI entry point ───────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    """Run a full state inventory and print the report."""
    import argparse
    parser = argparse.ArgumentParser(description="Canonical state resolver — inventory all state roots")
    parser.add_argument("--output", help="Write JSON report to this path")
    parser.add_argument("--resolve", help="Resolve a specific state type (filename prefix)")
    parser.add_argument("--terminal-id", default="")
    parser.add_argument("--session-id", default="")
    parser.add_argument("--filename", default="",
                        help="Explicit filename for --resolve")
    args = parser.parse_args(argv)

    if args.resolve:
        res = resolve_type(args.resolve, args.terminal_id, args.session_id, args.filename)
        if res is None:
            print(f"UNKNOWN: {args.resolve}")
            return 1
        print(json.dumps({
            "state_type": args.resolve,
            "category": res.category.name,
            "primary": str(res.primary),
            "current": str(res.current),
            "alternate_roots": [str(p) for p in res.alternate_roots],
            "description": res.entry.description if res.entry else "",
        }, indent=2))
        return 0

    encoded = inventory_report(args.output)
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
