#!/usr/bin/env python3
"""
SessionStart Characterization Drift Check

Compares current hook files against stored characterizations.
Warns if API signatures have changed since last session.

Passive: warns on drift, never blocks.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR / "__lib"))

_char_ok = False
try:
    from characterization_engine import CharacterizationEngine
    _char_ok = True
except ImportError:
    CharacterizationEngine = None

_detector_ok = False
try:
    from api_breakage_detector import APIDriftDetector
    _detector_ok = True
except ImportError:
    APIDriftDetector = None

_state_ok = False
try:
    from protection_state import StateManager
    _state_ok = True
except ImportError:
    StateManager = None


def _get_hook_files() -> list[Path]:
    """Get all Python hook files in the hooks directory (no duplicates)."""
    hooks_dir = Path(__file__).resolve().parent
    # Only **/*.py - covers all subdirs including root
    files = list(hooks_dir.glob("**/*.py"))
    # Lowercase for case-insensitive comparison (Windows filesystem is case-insensitive)
    skip_dirs_lower = {d.lower() for d in (
        "__lib", "tests", ".archive", "posttooluse", "pretooluse",
        "userpromptsubmit_modules", "shared_utils", "investigation-ledger",
    )}
    hook_files = []
    for f in files:
        parts = f.relative_to(hooks_dir).parts
        # Normalize to lowercase for case-insensitive matching
        if any(part.lower() in skip_dirs_lower or part.startswith("__") for part in parts):
            continue
        if f.name.startswith(".") or f.name.startswith("test_"):
            continue
        hook_files.append(f)
    return hook_files


def _run_drift_check() -> list[str]:
    """Run drift check on all hook files. Returns warning messages."""
    if not _char_ok or not _detector_ok or not _state_ok:
        if not _char_ok:
            logger.debug("CharacterizationEngine not available")
        if not _detector_ok:
            logger.debug("APIDriftDetector not available")
        if not _state_ok:
            logger.debug("StateManager not available")
        return []

    warnings = []
    try:
        state_mgr = StateManager()
        engine = CharacterizationEngine()
        detector = APIDriftDetector()
    except Exception as e:
        logger.debug(f"Failed to initialize drift detection components: {e}")
        return []

    for hook_file in _get_hook_files():
        try:
            stored = state_mgr.load_characterization(str(hook_file))
            if stored is None:
                continue

            current = engine.capture_characterization(str(hook_file))
            if current is None:
                continue

            diff = detector.detect_api_drift(stored=stored, current=current)
            if diff and diff.get("breaking_changes"):
                changes = diff["breaking_changes"]
                file_name = hook_file.name
                for change in changes[:3]:
                    warnings.append(
                        f"API drift: `{file_name}` — {change.get('type', 'change')}: "
                        f"{change.get('description', change.get('item', 'unknown'))}"
                    )
        except Exception as e:
            # Per-file errors don't stop the scan
            logger.debug(f"Drift check error for {hook_file.name}: {e}")
            continue

    return warnings[:5]


def main():
    raw_input = sys.stdin.read().strip()
    if not raw_input:
        sys.exit(0)

    try:
        data = json.loads(raw_input.lstrip("﻿"))
    except json.JSONDecodeError:
        sys.exit(0)

    if os.environ.get("CHARACTERIZATION_DRIFT_CHECK_ENABLED", "true").lower() in ("false", "0", "no"):
        sys.exit(0)

    warnings = _run_drift_check()

    if warnings:
        warning_text = "Hook API drift detected (from prior session):\n  " + "\n  ".join(warnings)
        warning_text += "\nRun /hook-obs to inspect hook health."
        print(json.dumps({
            "additionalContext": warning_text
        }))

    sys.exit(0)


if __name__ == "__main__":
    main()
