#!/usr/bin/env python3
"""
runtime_env.py
==============
Canonical runtime environment helpers for hook files.

Import these instead of defining LEDGER_AVAILABLE, terminal ID resolution,
or active turn ID inline. Inline definitions of these patterns are prohibited
(enforced by tests/test_no_inline_ledger_available.py).
"""
from __future__ import annotations

from typing import Any, Optional


def ledger_available() -> bool:
    """Return True if hook_ledger can be imported successfully."""
    try:
        from __lib import hook_ledger
        return True
    except ImportError:
        try:
            import hook_ledger
            return True
        except ImportError:
            return False


def get_terminal_id(input_data: Optional[dict[str, Any]] = None) -> str:
    """Resolve terminal ID from input_data, environment, or skill-guard detection.

    Returns empty string if not resolvable. Never raises.
    """
    try:
        from __lib import hook_ledger
        return hook_ledger.detect_terminal_id_from_payload(input_data or {})
    except ImportError:
        try:
            import hook_ledger
            return hook_ledger.detect_terminal_id_from_payload(input_data or {})
        except ImportError:
            return ""


def get_active_turn_id(terminal_id: str) -> Optional[str]:
    """Return the active turn ID for the given terminal, or None.

    Returns None if ledger is unavailable or terminal_id is empty. Never raises.
    """
    if not terminal_id:
        return None

    try:
        from __lib import hook_ledger
        return hook_ledger.get_active_turn(terminal_id)
    except ImportError:
        try:
            import hook_ledger
            return hook_ledger.get_active_turn(terminal_id)
        except ImportError:
            return None
