"""Dispatch manifest schema validator for /red-team.

The dispatch manifest is the orchestrator's on-disk summary of which specialists
ran, which succeeded, and which were DEFERRED. It exists to close the critic-glob
race (item 6 from the 2026-07-19 review): without it, the critic blindly globs
`{run_dir}/*.json` and cannot distinguish a fresh DISPATCHED write from a late
write by a DEFERRED-timeout specialist — which would be silently ingested.

The manifest is written by the orchestrator after FM-4 (post-dispatch
verification) completes, before the critic is invoked. The critic reads it
first; for each specialist marked DISPATCHED, the critic Reads the listed
`path`. Files for DEFERRED specialists are ignored even if they exist on disk
(late writes, partial recoveries). If the manifest is missing (old run_dir or
crash mid-run), the critic falls back to globbing — backward compatible.

Pure logic, no I/O — sibling to findings_schema.py.
"""

from __future__ import annotations
from typing import Any

REQUIRED_TOP_LEVEL_FIELDS = ("run_id", "session_id", "specialists")
VALID_SPECIALIST_STATUSES = ("DISPATCHED", "DEFERRED")
REQUIRED_SPECIALIST_FIELDS = ("name", "status")


def validate(manifest_obj: Any) -> list[str]:
    """Return validation error strings; empty list = valid.

    Accepts a parsed manifest object (dict). Does NOT parse JSON — the caller
    wraps Read in try/except.
    """
    if not isinstance(manifest_obj, dict):
        return ["manifest object is not a dict"]
    errors: list[str] = []
    for field in REQUIRED_TOP_LEVEL_FIELDS:
        if field not in manifest_obj:
            errors.append(f"missing required top-level field '{field}'")
    specialists = manifest_obj.get("specialists")
    if specialists is None:
        return errors + ["missing 'specialists' list"]
    if not isinstance(specialists, list):
        return errors + ["'specialists' is not a list"]
    seen_names: set[str] = set()
    for i, s in enumerate(specialists):
        if not isinstance(s, dict):
            errors.append(f"specialist[{i}] is not a dict")
            continue
        for field in REQUIRED_SPECIALIST_FIELDS:
            if field not in s:
                errors.append(f"specialist[{i}] missing required field '{field}'")
        name = s.get("name")
        if name is not None:
            if not isinstance(name, str) or not name:
                errors.append(f"specialist[{i}] name must be a non-empty string")
            elif name in seen_names:
                errors.append(f"specialist[{i}] duplicate name '{name}'")
            else:
                seen_names.add(name)
        status = s.get("status")
        if status is not None and status not in VALID_SPECIALIST_STATUSES:
            errors.append(
                f"specialist[{i}] status '{status}' not in {VALID_SPECIALIST_STATUSES}"
            )
        # DISPATCHED entries must list a path (the file the critic should Read).
        # DEFERRED entries may have path=null (no file expected) or a path
        # (late write — must be ignored by the critic per the manifest contract).
        if status == "DISPATCHED":
            path = s.get("path")
            if not isinstance(path, str) or not path:
                errors.append(
                    f"specialist[{i}] status DISPATCHED requires a non-empty 'path'"
                )
    return errors


def dispatched_paths(manifest_obj: Any) -> list[str]:
    """Return the file paths the critic should Read, in manifest order.

    Convenience helper. Returns [] if the manifest is structurally invalid or
    no specialists are DISPATCHED. The critic treats an empty return as FM-3
    (empty input → BLOCK).
    """
    if not isinstance(manifest_obj, dict):
        return []
    specialists = manifest_obj.get("specialists")
    if not isinstance(specialists, list):
        return []
    return [
        s["path"]
        for s in specialists
        if isinstance(s, dict)
        and s.get("status") == "DISPATCHED"
        and isinstance(s.get("path"), str)
        and s["path"]
    ]
