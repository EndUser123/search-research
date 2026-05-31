"""Tests for anti_sycophancy_injector in cc-aca-epistemic plugin."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Add plugin paths FIRST (so plugin modules take precedence)
def _find_epistemic_plugin():
    paths = [
        Path("P:/packages/cc-aca-epistemic"),
        Path("P:/packages/.claude-marketplace/plugins/cc-aca-epistemic")
    ]
    for p in paths:
        if p.exists():
            return p
    return paths[0]

EPISTEMIC_PLUGIN = _find_epistemic_plugin()
EPISTEMIC_HOOKS_UPS = EPISTEMIC_PLUGIN / "hooks" / "userpromptsubmit"
EPISTEMIC_LIBS = [str(EPISTEMIC_HOOKS_UPS), str(EPISTEMIC_PLUGIN / "__lib")]
for lib_path in EPISTEMIC_LIBS:
    if Path(lib_path).exists() and lib_path not in sys.path:
        sys.path.insert(0, lib_path)

from UserPromptSubmit_modules.base import HookContext


def _state_file(session_id: str, terminal_id: str) -> Path:
    safe_session = "".join(c if c.isalnum() or c in "._-" else "_" for c in session_id)
    safe_terminal = "".join(c if c.isalnum() or c in "._-" else "_" for c in terminal_id)
    return Path(tempfile.gettempdir()) / "claude_hooks" / "state" / "anti_sycophancy_injector" / f"{safe_session}__{safe_terminal}.json"


def test_low_stakes_dedupe_and_cooldown():
    from UserPromptSubmit.anti_sycophancy_injector import run_anti_sycophancy_injector

    os.environ["ANTI_SYCOPHANCY_ENABLED"] = "true"
    session_id = "test-anti-syc-1"
    terminal_id = "term-a"
    state = _state_file(session_id, terminal_id)
    state.unlink(missing_ok=True)

    ctx = HookContext(
        prompt="are you sure this is necessary?",
        data={"session_id": session_id, "terminal_id": terminal_id},
        session_id=session_id,
        terminal_id=terminal_id,
    )

    r1 = run_anti_sycophancy_injector(ctx)
    assert r1 is not None
    assert "ADVOCATE_PROTOCOL_LIGHT" in str(r1.context)

    # Same prompt signature should not re-inject.
    r2 = run_anti_sycophancy_injector(ctx)
    assert r2 is None

    # Different low-stakes prompt in same streak should also avoid repeated low inject.
    ctx2 = HookContext(
        prompt="I don't think this is needed",
        data={"session_id": session_id, "terminal_id": terminal_id},
        session_id=session_id,
        terminal_id=terminal_id,
    )
    r3 = run_anti_sycophancy_injector(ctx2)
    assert r3 is None


def test_high_stakes_escalation():
    from UserPromptSubmit.anti_sycophancy_injector import run_anti_sycophancy_injector

    os.environ["ANTI_SYCOPHANCY_ENABLED"] = "true"
    session_id = "test-anti-syc-2"
    terminal_id = "term-b"
    state = _state_file(session_id, terminal_id)
    state.unlink(missing_ok=True)

    ctx = HookContext(
        prompt="is that really the best approach?",
        data={"session_id": session_id, "terminal_id": terminal_id},
        session_id=session_id,
        terminal_id=terminal_id,
    )
    r1 = run_anti_sycophancy_injector(ctx)
    assert r1 is not None
    assert "ADVOCATE_PROTOCOL" in str(r1.context)

    # Different high-stakes prompt should follow with concise followup protocol.
    ctx2 = HookContext(
        prompt="this is way too complicated",
        data={"session_id": session_id, "terminal_id": terminal_id},
        session_id=session_id,
        terminal_id=terminal_id,
    )
    r2 = run_anti_sycophancy_injector(ctx2)
    assert r2 is not None
    assert "ADVOCATE_PROTOCOL_FOLLOWUP" in str(r2.context)


def test_low_stakes_protocol_restates_evidence():
    from UserPromptSubmit.anti_sycophancy_injector import run_anti_sycophancy_injector

    os.environ["ANTI_SYCOPHANCY_ENABLED"] = "true"
    session_id = "test-anti-syc-3"
    terminal_id = "term-c"
    state = _state_file(session_id, terminal_id)
    state.unlink(missing_ok=True)

    ctx = HookContext(
        prompt="are you sure this is needed?",
        data={"session_id": session_id, "terminal_id": terminal_id},
        session_id=session_id,
        terminal_id=terminal_id,
    )

    result = run_anti_sycophancy_injector(ctx)
    assert result is not None
    text = str(result.context)
    assert "Restate the conclusion and the specific evidence" in text
    assert "Check whether this challenge actually invalidates that evidence" in text
