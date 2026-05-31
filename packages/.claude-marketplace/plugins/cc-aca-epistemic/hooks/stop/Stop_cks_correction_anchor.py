#!/usr/bin/env python3
"""Stop hook gate: persist skill-dir correction events to CKS.

Trigger conditions:
1. User challenged the AI after a wrong-skill-dir response (challenge marker present)
2. Tool events this turn vs prior turn show different skill dirs
   (i.e., user read the CORRECT skill dir after the AI wrongly named one)

When both fire, write a CKS 'correction' entry capturing:
- The wrong skill the AI mentioned
- The correct skill the user read
- The challenge text
"""
from __future__ import annotations


# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---




# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---



import os
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# Path setup                                                                  #
# --------------------------------------------------------------------------- #
_marketplace_plugins = _hooks_dir.parent.parent.parent
__csf_src = _marketplace_plugins / "search-research" / "core"
sys.path.insert(0, str(__csf_src))

# --------------------------------------------------------------------------- #
# Internal imports                                                            #
# --------------------------------------------------------------------------- #
from evidence_scope import (
    SCOPE_SESSION_FRESH,
    SCOPE_TURN_STRICT,
    load_scoped_tool_events,
)
from Stop_skill_dir_correlation_gate import (
    _extract_accessed_skills,
    _get_user_skill_from_conversation,
)
from anti_sycophancy.challenge_marker import challenge_marker_path as _challenge_marker_path

# Lazy CKS import — resolved at call time to avoid module-load errors in tests
_ingest_memory: MagicMock | None = None


def _get_ingest():
    global _ingest_memory
    if _ingest_memory is None:
        _marketplace_plugins = _hooks_dir.parent.parent.parent
        __csf_src = _marketplace_plugins / "search-research" / "core"
        sys.path.insert(0, str(__csf_src))
        from cks.unified import ingest_correction as _ic

        _ingest_memory = _ic
    return _ingest_memory

# --------------------------------------------------------------------------- #
# Constants                                                                   #
# --------------------------------------------------------------------------- #
ENABLED = os.environ.get("STOP_CKS_CORRECTION_ANCHOR_ENABLED", "true").lower() == "true"
CHALLENGE_MARKER_VERSION = "v1"

# Daemon client for write signal
_write_signal_client = None


def _get_write_signal_client():
    """Get or create daemon client for write signals."""
    global _write_signal_client
    if _write_signal_client is None:
        try:
            # Add semantic_daemon path
            semantic_daemon_path = _marketplace_plugins / "search-research" / "contrib" / "semantic_daemon"
            if str(semantic_daemon_path) not in sys.path:
                sys.path.insert(0, str(semantic_daemon_path))
            from daemons.daemon_client import DaemonClient

            _write_signal_client = DaemonClient(auto_start=False, enable_fallback=True)
        except Exception:
            return None
    return _write_signal_client


def _send_write_signal(entry_id: str, entry_type: str, workspace: str, terminal_id: str) -> None:
    """Send write signal to daemon after CKS ingest (fire-and-forget).

    This is advisory only - failure does not raise, just returns False.
    The daemon will catch up on its next idle cycle if the signal is missed.
    """
    client = _get_write_signal_client()
    if client is None:
        return
    try:
        client.send_write_signal(
            entry_id=entry_id,
            entry_type=entry_type,
            workspace=workspace,
            terminal_id=terminal_id,
        )
    except Exception:
        pass  # fire-and-forget, never block


def run(data: dict) -> dict | None:
    """Persist skill-dir correction event to CKS.

    Returns None (side-effect writer — no output control).
    """
    if not ENABLED:
        return None

    session_id = data.get("session_id", "")
    terminal_id = data.get("terminal_id", "")

    if not session_id or not terminal_id:
        return None

    # --- Challenge marker check ---------------------------------------------- #
    marker_path = _challenge_marker_path(session_id, terminal_id)
    if not marker_path or not marker_path.exists():
        return None

    # --- Expected skill from conversation --------------------------------- #
    expected_skill = _get_user_skill_from_conversation(data)
    if not expected_skill:
        return None

    # --- Current-turn skill dirs ------------------------------------------ #
    try:
        current_events = load_scoped_tool_events(
            session_id=session_id,
            terminal_id=terminal_id,
            scope=SCOPE_TURN_STRICT,
        )
    except Exception:
        return None

    current_skills = _extract_accessed_skills(current_events)
    if not current_skills:
        return None

    current_skill = next(iter(current_skills))  # pick any/only

    # --- Prior-turn skill dirs via event-ID set difference --------------- #
    try:
        session_events = load_scoped_tool_events(
            session_id=session_id,
            terminal_id=terminal_id,
            scope=SCOPE_SESSION_FRESH,
        )
    except Exception:
        return None

    current_ids = {e["id"] for e in current_events if "id" in e}
    prior_events = [e for e in session_events if e.get("id") not in current_ids]
    prior_skills = _extract_accessed_skills(prior_events)

    # --- Condition: prior had a skill dir, current has a different one ------------ #
    # After a challenge, the user reads the CORRECT skill dir (current turn).
    # The PRIOR turn had the WRONG skill dir (what the AI wrongly referred to).
    # We detect this as: prior_skills has something, and current_skill is NOT in it.
    if prior_skills and current_skill not in prior_skills:
        wrong_skill = next(iter(prior_skills))   # what the AI wrongly said
        correct_skill = current_skill            # what the user actually read

        question = f"Correcting skill directory reference: {wrong_skill}"
        answer = (
            f"AI incorrectly referenced '{wrong_skill}' but user corrected to "
            f"'{correct_skill}' after challenge. "
            f"Challenge marker: {marker_path.name}"
        )

        try:
            ingest_correction = _get_ingest()
            entry_id = ingest_correction(
                title=question,
                content=answer,
                wrong_skill=wrong_skill,
                correct_skill=correct_skill,
                session_id=session_id,
                terminal_id=terminal_id,
                marker_version=CHALLENGE_MARKER_VERSION,
            )
            # Send write signal to daemon for immediate FAISS refresh.
            # DISABLED: daemon not running (pipe code 3), write-signal path untested for CKS entries.
            # Remove comment to re-enable once: daemon starts reliably, vector query path exists for CKS,
            # and end-to-end signal test passes. See decision-memo-2026-05-05.
            # _send_write_signal(entry_id, "correction", session_id, terminal_id)
        except Exception:
            pass  # fail open — CKS write error must not block stop

    return None
