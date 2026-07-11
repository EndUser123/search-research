"""
Pytest configuration for prompt-enhancer tests.

Adds package root to sys.path so tests can import from top-level modules.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolated_home(monkeypatch, tmp_path):
    """Redirect HOME/USERPROFILE/CLAUDE_TERMINAL_ID to tmp_path for all tests.

    autouse=True ensures every test gets a fresh isolated environment without
    needing an explicit fixture reference.  Tests that need the isolated
    paths can reference the yielded (tmp_path, terminal_id) values directly.

    Yields (tmp_path, terminal_id) so callers can compute artifact paths.
    """
    terminal_id = f"test-{os.getpid()}-{int(time.time() * 1000)}"
    monkeypatch.setenv("CLAUDE_TERMINAL_ID", terminal_id)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.delenv("CLAUDE_PLUGIN_ROOT", raising=False)
    yield tmp_path, terminal_id


# ---------------------------------------------------------------------------
# Shared helpers (also usable by other test modules)
# ---------------------------------------------------------------------------


def _active_enhancement_path(tmp_path: Path, terminal_id: str) -> Path:
    """Path to active_enhancement.json inside the isolated HOME."""
    return (
        tmp_path
        / ".claude"
        / ".artifacts"
        / terminal_id
        / "prompt-enhancer"
        / "active_enhancement.json"
    )


def _seed_enhancement(
    tmp_path: Path,
    terminal_id: str,
    missing_details: list[str],
    *,
    clarified_intent: str = "delete the database",
    confidence: float = 0.9,
    **extra_fields,
) -> Path:
    """Write a controlled active_enhancement.json for hook tests."""
    data = {
        "clarified_intent": clarified_intent,
        "missing_details": missing_details,
        "analysis": "test analysis",
        "safety_flags": [],
        "estimated_tokens": 5,
        "confidence": confidence,
        **extra_fields,
    }
    path = _active_enhancement_path(tmp_path, terminal_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def _hook_invoke(hook_script: Path, payload: dict) -> dict:
    """Run a hook entrypoint as a subprocess; pass JSON payload on stdin; return parsed stdout."""
    result = subprocess.run(
        [sys.executable, str(hook_script)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Hook exited {result.returncode}: {result.stderr}")
    return json.loads(result.stdout)


# Referent resolution and its session-context store were removed 2026-07-11
# (wrong-anchor injection incident); the _seed_session_context helpers went
# with them. See tests/test_no_referent_injection.py for the regression lock.