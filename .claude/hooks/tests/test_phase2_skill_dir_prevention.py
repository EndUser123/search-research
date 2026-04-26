#!/usr/bin/env python3
"""Tests for Phase 2 skill-dir prevention (writer + gate)."""

from __future__ import annotations

import json
import os
import sys
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from UserPromptSubmit_modules.skill_context_writer import (
    _extract_skill_from_prompt,
    _safe_id,
    skill_context_writer,
)
from UserPromptSubmit_modules.base import HookContext

# ---------------------------------------------------------------------------
# Writer tests
# ---------------------------------------------------------------------------

class TestSkillContextWriter:
    """Tests for skill_context_writer.py."""

    def test_skill_found_file_written(self, tmp_path: Path):
        """Prompt /ai-pcli do X → state file has expected_skill and expected_dir."""
        with patch(
            "UserPromptSubmit_modules.skill_context_writer._STATE_DIR",
            tmp_path / "state" / "skill_context",
        ):
            ctx = HookContext(
                prompt="/ai-pcli do something",
                data={},
                session_id="sess-1",
                terminal_id="term-1",
            )
            skill_context_writer(ctx)

            sf = tmp_path / "state" / "skill_context" / "skill_context_term-1.json"
            assert sf.exists()
            data = json.loads(sf.read_text(encoding="utf-8"))
            assert data["expected_skill"] == "ai-pcli"
            assert data["expected_dir"] == ".claude/skills/ai-pcli"
            assert data["terminal_id"] == "term-1"
            assert data["session_id"] == "sess-1"

    def test_no_skill_file_cleared(self, tmp_path: Path):
        """Prompt 'what time is it' → state file deleted if it existed."""
        state_dir = tmp_path / "state" / "skill_context"
        state_dir.mkdir(parents=True)
        sf = state_dir / "skill_context_term-1.json"
        sf.write_text("{}")

        with patch(
            "UserPromptSubmit_modules.skill_context_writer._STATE_DIR",
            state_dir,
        ):
            ctx = HookContext(
                prompt="what time is it",
                data={},
                session_id="sess-1",
                terminal_id="term-1",
            )
            skill_context_writer(ctx)

        assert not sf.exists(), "state file should be deleted"

    def test_false_positive_single_char_excluded(self, tmp_path: Path):
        """Prompt /v (single char) → no state file written."""
        with patch(
            "UserPromptSubmit_modules.skill_context_writer._STATE_DIR",
            tmp_path / "state" / "skill_context",
        ):
            ctx = HookContext(
                prompt="/v do something",
                data={},
                session_id="sess-1",
                terminal_id="term-1",
            )
            skill_context_writer(ctx)

            sf = tmp_path / "state" / "skill_context" / "skill_context_term-1.json"
            assert not sf.exists(), "/v should be filtered as single-char"

    def test_known_non_skill_excluded(self, tmp_path: Path):
        """Prompt /README → no state file (README is in _NON_SKILL_NAMES)."""
        with patch(
            "UserPromptSubmit_modules.skill_context_writer._STATE_DIR",
            tmp_path / "state" / "skill_context",
        ):
            ctx = HookContext(
                prompt="/README do something",
                data={},
                session_id="sess-1",
                terminal_id="term-1",
            )
            skill_context_writer(ctx)

            sf = tmp_path / "state" / "skill_context" / "skill_context_term-1.json"
            assert not sf.exists(), "README should be filtered by _NON_SKILL_NAMES"

    def test_extract_skill_from_prompt(self):
        """Unit test for _extract_skill_from_prompt."""
        assert _extract_skill_from_prompt("/ai-pcli do something") == "ai-pcli"
        assert _extract_skill_from_prompt("use /search now") == "search"
        assert _extract_skill_from_prompt("no skill here") is None
        assert _extract_skill_from_prompt("/v") is None           # single char
        assert _extract_skill_from_prompt("/README") is None      # in non-skill names
        assert _extract_skill_from_prompt("/ai-pcli") == "ai-pcli"

    def test_safe_id(self):
        """Unit test for _safe_id."""
        assert _safe_id("term-1") == "term-1"
        assert _safe_id("term:1") == "term_1"
        assert _safe_id("term/1") == "term_1"


# ---------------------------------------------------------------------------
# Gate tests
# ---------------------------------------------------------------------------

GATE_SCRIPT = Path(r"P:/.claude/hooks/PreToolUse_skill_dir_gate.py")
REAL_STATE_DIR = Path(r"P:/.claude/hooks/state/skill_context")


def _gate_run(
    tool_name: str,
    tool_input: dict,
    terminal_id: str,
    state_data: dict | None,
    env: dict | None = None,
) -> tuple[int, str, str]:
    """Run the gate as a subprocess; state written to REAL_STATE_DIR."""
    sf = REAL_STATE_DIR / f"skill_context_{terminal_id}.json"
    if state_data is not None:
        REAL_STATE_DIR.mkdir(parents=True, exist_ok=True)
        sf.write_text(json.dumps(state_data), encoding="utf-8")
    elif sf.exists():
        sf.unlink()

    try:
        inp = {"tool_name": tool_name, "tool_input": tool_input, "terminal_id": terminal_id}
        env_vars = dict(os.environ)
        env_vars["CLAUDE_TERMINAL_ID"] = terminal_id
        if env:
            env_vars.update(env)

        r = subprocess.run(
            [sys.executable, str(GATE_SCRIPT)],
            input=json.dumps(inp).encode(),
            capture_output=True,
            env=env_vars,
            timeout=5,
        )
        return r.returncode, r.stdout.decode(), r.stderr.decode()
    finally:
        if sf.exists():
            try:
                sf.unlink()
            except OSError:
                pass


class TestSkillDirGate:
    """Tests for PreToolUse_skill_dir_gate.py."""

    def test_scoped_glob_allowed(self):
        """Pattern targeting expected_dir → exit 0."""
        rc, _, stderr = _gate_run(
            "Glob",
            {"pattern": "P:/.claude/skills/ai-pcli/**/*.md"},
            "gate-scop-glob",
            {"expected_skill": "ai-pcli", "expected_dir": ".claude/skills/ai-pcli"},
        )
        assert rc == 0, f"Expected allow (0), got {rc}. stderr: {stderr}"

    def test_unscoped_glob_blocked(self):
        """Pattern **/*.md without expected_dir → exit 2."""
        rc, _, stderr = _gate_run(
            "Glob",
            {"pattern": "**/*.md"},
            "gate-unscop-glob",
            {"expected_skill": "ai-pcli", "expected_dir": ".claude/skills/ai-pcli"},
        )
        assert rc == 2, f"Expected block (2), got {rc}. stderr: {stderr}"
        assert "BLOCKED" in stderr
        assert "ai-pcli" in stderr

    def test_scoped_grep_allowed(self):
        """Path .claude/skills/ai-pcli → exit 0."""
        rc, _, stderr = _gate_run(
            "Grep",
            {"path": ".claude/skills/ai-pcli/**/*.py"},
            "gate-scop-grep",
            {"expected_skill": "ai-pcli", "expected_dir": ".claude/skills/ai-pcli"},
        )
        assert rc == 0, f"Expected allow (0), got {rc}. stderr: {stderr}"

    def test_grep_no_path_blocked(self):
        """Grep without path key → exit 2."""
        rc, _, stderr = _gate_run(
            "Grep",
            {"pattern": "TODO"},   # no "path" key
            "gate-no-path",
            {"expected_skill": "ai-pcli", "expected_dir": ".claude/skills/ai-pcli"},
        )
        assert rc == 2, f"Expected block (2), got {rc}. stderr: {stderr}"
        assert "BLOCKED" in stderr

    def test_no_state_file_allow(self):
        """State file missing → exit 0 (fail open)."""
        rc, _, stderr = _gate_run(
            "Glob",
            {"pattern": "**/*.md"},
            "gate-no-state",
            None,   # no state file
        )
        assert rc == 0, f"Expected fail-open (0), got {rc}. stderr: {stderr}"

    def test_disabled_by_env(self):
        """SKILL_DIR_GATE_ENABLED=false → exit 0 regardless."""
        rc, _, stderr = _gate_run(
            "Glob",
            {"pattern": "**/*.md"},
            "gate-disabled",
            {"expected_skill": "ai-pcli", "expected_dir": ".claude/skills/ai-pcli"},
            env={"SKILL_DIR_GATE_ENABLED": "false"},
        )
        assert rc == 0, f"Expected disabled allow (0), got {rc}. stderr: {stderr}"

    def test_backslash_normalization(self):
        r"""Pattern with backslashes (Windows) → normalized and matched."""
        rc, _, stderr = _gate_run(
            "Glob",
            {"pattern": r".claude\skills\ai-pcli\**\*.md"},
            "gate-backslash",
            {"expected_skill": "ai-pcli", "expected_dir": ".claude/skills/ai-pcli"},
        )
        # After normalization: .claude/skills/ai-pcli is found
        assert rc == 0, f"Expected allow (0), got {rc}. stderr: {stderr}"

    def test_unscoped_grep_blocked(self):
        """Grep path not containing expected_dir → exit 2."""
        rc, _, stderr = _gate_run(
            "Grep",
            {"path": "src/**/*.py"},   # wrong dir
            "gate-unscop-grep",
            {"expected_skill": "ai-pcli", "expected_dir": ".claude/skills/ai-pcli"},
        )
        assert rc == 2, f"Expected block (2), got {rc}. stderr: {stderr}"
        assert "BLOCKED" in stderr
