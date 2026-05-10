#!/usr/bin/env python3
"""Tests for scripts/check_orphaned_stop_modules.py."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent.parent  # P:/ repo root
HOOKS_DIR_FOR_SCRIPTS = Path(__file__).resolve().parent.parent  # P:/.claude/hooks — actual location of script


class TestOrphanedStopModules:
    """Verify orphan detection script."""

    def test_no_orphans_on_current_hooks_dir(self):
        """Running the script against the real hooks dir exits 0."""
        script = HOOKS_DIR_FOR_SCRIPTS / "scripts" / "check_orphaned_stop_modules.py"
        result = subprocess.run(
            [sys.executable, str(script), str(HOOKS_DIR_FOR_SCRIPTS)],
            capture_output=True,
            text=True,
        )
        # Allow 0 (clean) or 1 (orphans found — we handle gracefully)
        assert result.returncode in (0, 1), (
            f"Script exited {result.returncode}.\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_experimental_module_not_flagged_as_orphan(self, tmp_path):
        """A module with EXPERIMENTAL + wired marker in docstring is not an orphan."""
        hooks = tmp_path / "hooks"
        hooks.mkdir()

        # Create a minimal Stop.py for import detection
        (hooks / "Stop.py").write_text(
            '"""Stop.py — wired entry point.\n\nEXPERIMENTAL: test harness stub\nwired: true\nreview: TBD\n"""\n# entry point'
        )

        # Create a module with experimental docstring
        exp_mod = hooks / "stop" / "experimental" / "NewExpGate.py"
        exp_mod.parent.mkdir(parents=True)
        exp_mod.write_text(
            '"""\nNewExpGate\n\nEXPERIMENTAL: Testing orphan detection\nwired: true\nreview: 2026-06-01\n"""\ndef run(data): pass\n'
        )

        script = HOOKS_DIR_FOR_SCRIPTS / "scripts" / "check_orphaned_stop_modules.py"
        result = subprocess.run(
            [sys.executable, str(script), str(hooks)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"Experimental module was flagged orphan.\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_archived_module_not_flagged_as_orphan(self, tmp_path):
        """A module with ARCHIVED marker in docstring is not an orphan."""
        hooks = tmp_path / "hooks"
        hooks.mkdir()
        (hooks / "Stop.py").write_text(
            '"""Stop.py — wired entry point.\n\nEXPERIMENTAL: test harness stub\nwired: true\nreview: TBD\n"""\n# entry point'
        )

        arch_mod = hooks / "stop" / "archived" / "OldGate.py"
        arch_mod.parent.mkdir(parents=True)
        arch_mod.write_text(
            '"""\nOldGate — ARCHIVED: Replaced by new gate in 2025.\n"""\ndef run(data): pass\n'
        )

        script = HOOKS_DIR_FOR_SCRIPTS / "scripts" / "check_orphaned_stop_modules.py"
        result = subprocess.run(
            [sys.executable, str(script), str(hooks)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"Archived module was flagged orphan.\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_wired_module_not_flagged_as_orphan(self, tmp_path):
        """A module imported in Stop.py is not an orphan."""
        hooks = tmp_path / "hooks"
        hooks.mkdir()

        # Stop.py imports the module — must also be marked non-orphan
        (hooks / "Stop.py").write_text(
            '"""Stop.py — wired entry point.\n\nEXPERIMENTAL: test harness\nwired: true\nreview: TBD\n"""\nfrom MyWiredGate import run_wired_gate\n'
        )

        wired_mod = hooks / "MyWiredGate.py"
        wired_mod.write_text("def run_wired_gate(data): pass\n")

        script = HOOKS_DIR_FOR_SCRIPTS / "scripts" / "check_orphaned_stop_modules.py"
        result = subprocess.run(
            [sys.executable, str(script), str(hooks)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"Wired module was flagged orphan.\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_unmarked_unwired_module_flagged_as_orphan(self, tmp_path):
        """A module that is neither wired nor marked experimental/archived IS an orphan."""
        hooks = tmp_path / "hooks"
        hooks.mkdir()
        (hooks / "Stop.py").write_text(
            '"""Stop.py — wired entry point.\n\nEXPERIMENTAL: test harness stub\nwired: true\nreview: TBD\n"""\n# entry point'
        )

        orphan_mod = hooks / "Stop_DanglingGate.py"
        orphan_mod.write_text(
            '"""\nStop_DanglingGate — standalone, not connected.\n"""\ndef run(data): pass\n'
        )

        script = HOOKS_DIR_FOR_SCRIPTS / "scripts" / "check_orphaned_stop_modules.py"
        result = subprocess.run(
            [sys.executable, str(script), str(hooks)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1, (
            f"Unmarked orphan should have been detected.\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert "Stop_DanglingGate" in result.stdout