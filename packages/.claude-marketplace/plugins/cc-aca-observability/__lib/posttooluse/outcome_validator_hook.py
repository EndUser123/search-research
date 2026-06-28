#!/usr/bin/env python3
from __future__ import annotations

"""In-process wrapper for PostToolUse_outcome_validator.

Tracks fix success/failure and updates causal graphs using Bayesian learning.
"""

import json
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook

_hooks_dir = Path(__file__).resolve().parent.parent
from _bootstrap import state_root
_SESSION_STATE_FILE = state_root() / "debug_session_state.json"
_CAUSAL_STATE_FILE = state_root() / "causal_learning.json"

_MIN_PROB = 0.01
_MAX_PROB = 0.99


class OutcomeValidatorHook(PostToolUseHook):
    """Validate fix outcomes and update causal graphs."""

    tool_matcher = {"Bash"}

    def process(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_response: dict[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(tool_response, dict):
            return {"passed": True}

        exit_code = tool_response.get("exit_code", tool_response.get("exitCode", 0))
        stderr = tool_response.get("stderr", "")

        session_state = self._load_json(_SESSION_STATE_FILE)
        last_error = session_state.get("last_error", {})

        if not last_error:
            return {"passed": True}

        success = exit_code == 0 and not str(stderr).strip()
        error_type = last_error.get("error_type")
        cause_id = last_error.get("cause_id")

        if error_type and cause_id:
            causal = self._load_json(_CAUSAL_STATE_FILE)
            causal.setdefault(error_type, {})
            causal[error_type].setdefault(cause_id, {
                "attempts": 0, "successes": 0, "adjusted_probability": 0.5
            })
            entry = causal[error_type][cause_id]
            entry["attempts"] += 1
            if success:
                entry["successes"] += 1
                entry["adjusted_probability"] = min(entry["adjusted_probability"] * 1.1, _MAX_PROB)
            else:
                entry["adjusted_probability"] = max(entry["adjusted_probability"] * 0.9, _MIN_PROB)
            self._save_json(_CAUSAL_STATE_FILE, causal)

        if success:
            self._clear(_SESSION_STATE_FILE)

        return {"passed": True}

    # -- helpers --

    @staticmethod
    def _load_json(path: Path) -> dict:
        try:
            if path.exists():
                with open(path) as f:
                    return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
        return {}

    @staticmethod
    def _save_json(path: Path, data: dict) -> None:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w") as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass

    @staticmethod
    def _clear(path: Path) -> None:
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass
