#!/usr/bin/env python3
"""Tests for PreToolUse_bulk_delete_gate.py

Tests the bulk delete gate hook that prevents destructive bulk deletions
by requiring inventory awareness before proceeding.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest import mock

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))
sys.path.insert(0, str(HOOKS_DIR / "__lib"))

import PreToolUse_bulk_delete_gate as gate

# =============================================================================
# extract_delete_target tests
# =============================================================================


class TestExtractDeleteTarget:
    def test_rm_rf(self):
        assert gate.extract_delete_target("rm -rf /some/path") == "/some/path"

    def test_rm_fr(self):
        assert gate.extract_delete_target("rm -fr /some/path") == "/some/path"

    def test_rm_r(self):
        assert gate.extract_delete_target("rm -r /some/path") == "/some/path"

    def test_rm_rf_quoted(self):
        assert gate.extract_delete_target('rm -rf "/some/path"') == "/some/path"

    def test_rm_rf_single_quoted(self):
        assert gate.extract_delete_target("rm -rf '/some/path'") == "/some/path"

    def test_rmdir_s(self):
        assert gate.extract_delete_target("rmdir /s C:\\some\\path") == "C:\\some\\path"

    def test_remove_item_recurse(self):
        result = gate.extract_delete_target("Remove-Item C:\\path -Recurse")
        assert result == "C:\\path"

    def test_not_a_delete(self):
        assert gate.extract_delete_target("ls -la /some/path") is None

    def test_rm_single_file(self):
        """rm without -r should not trigger."""
        assert gate.extract_delete_target("rm file.txt") is None

    def test_empty_command(self):
        assert gate.extract_delete_target("") is None


# =============================================================================
# is_safe_target tests
# =============================================================================


class TestIsSafeTarget:
    def test_pycache(self):
        assert gate.is_safe_target("some/path/__pycache__") is True

    def test_node_modules(self):
        assert gate.is_safe_target("/project/node_modules") is True

    def test_venv(self):
        assert gate.is_safe_target("P:/project/venv") is True

    def test_pytest_cache(self):
        assert gate.is_safe_target(".pytest_cache") is True

    def test_source_code_not_safe(self):
        assert gate.is_safe_target("P:/project/src/skills") is False

    def test_skills_dir_not_safe(self):
        assert gate.is_safe_target("P:/.claude/skills/v") is False


# =============================================================================
# count_files tests
# =============================================================================


class TestCountFiles:
    def test_nonexistent_directory(self):
        count, files = gate.count_files(Path("/nonexistent/path/xyz123"))
        assert count == 0
        assert files == []

    def test_directory_with_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create 8 test files
            for i in range(8):
                (Path(tmpdir) / f"script_{i}.py").write_text(f"# script {i}")

            count, files = gate.count_files(Path(tmpdir))
            assert count == 8
            assert len(files) == 8

    def test_sample_capped_at_20(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(25):
                (Path(tmpdir) / f"file_{i}.txt").write_text("content")

            count, files = gate.count_files(Path(tmpdir))
            assert count == 25
            assert len(files) == 20  # Capped

    def test_nested_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sub = Path(tmpdir) / "sub"
            sub.mkdir()
            (Path(tmpdir) / "top.py").write_text("top")
            (sub / "nested.py").write_text("nested")

            count, files = gate.count_files(Path(tmpdir))
            assert count == 2


# =============================================================================
# run() integration tests
# =============================================================================


class TestRunIntegration:
    def test_non_bash_tool_allowed(self):
        """Non-Bash tools should pass through."""
        data = {"tool_name": "Write", "tool_input": {"file_path": "/some/file"}}
        assert gate.run(data) is None

    def test_simple_rm_allowed(self):
        """Simple rm (no recursive) should pass."""
        data = {"tool_name": "Bash", "tool_input": {"command": "rm file.txt"}}
        assert gate.run(data) is None

    def test_empty_command_allowed(self):
        data = {"tool_name": "Bash", "tool_input": {"command": ""}}
        assert gate.run(data) is None

    def test_safe_target_allowed(self):
        """Deleting __pycache__ should pass even with -rf."""
        data = {"tool_name": "Bash", "tool_input": {"command": "rm -rf __pycache__"}}
        assert gate.run(data) is None

    def test_bulk_delete_blocked(self):
        """Deleting a directory with >5 files should be blocked."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create 10 files to exceed threshold
            for i in range(10):
                (Path(tmpdir) / f"script_{i}.py").write_text(f"# script {i}")

            data = {
                "tool_name": "Bash",
                "tool_input": {"command": f"rm -rf {tmpdir}"},
            }

            # Mock git tag creation to avoid git dependency in tests
            with mock.patch.object(gate, "create_git_tag", return_value=None):
                result = gate.run(data)

            assert result is not None
            assert result["decision"] == "block"
            assert "10 files" in result["reason"]
            assert "BULK DELETE GATE" in result["reason"]

    def test_below_threshold_allowed(self):
        """Deleting a directory with <=5 files should pass."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(3):
                (Path(tmpdir) / f"file_{i}.txt").write_text("content")

            data = {
                "tool_name": "Bash",
                "tool_input": {"command": f"rm -rf {tmpdir}"},
            }
            assert gate.run(data) is None

    def test_bypass_env_var(self):
        """BULK_DELETE_BYPASS=1 should skip the gate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(10):
                (Path(tmpdir) / f"script_{i}.py").write_text(f"# script {i}")

            data = {
                "tool_name": "Bash",
                "tool_input": {"command": f"rm -rf {tmpdir}"},
            }

            with mock.patch.dict(os.environ, {"BULK_DELETE_BYPASS": "1"}):
                assert gate.run(data) is None

    def test_nonexistent_target_allowed(self):
        """Deleting a nonexistent directory should pass (0 files)."""
        data = {
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /nonexistent/path/xyz123abc"},
        }
        assert gate.run(data) is None

    def test_git_tag_in_block_message(self):
        """When git tag succeeds, it should appear in the block message."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(10):
                (Path(tmpdir) / f"file_{i}.py").write_text("content")

            data = {
                "tool_name": "Bash",
                "tool_input": {"command": f"rm -rf {tmpdir}"},
            }

            with mock.patch.object(gate, "create_git_tag", return_value="pre-delete-test-20260216"):
                result = gate.run(data)

            assert result is not None
            assert "pre-delete-test-20260216" in result["reason"]
            assert "Recovery tag created" in result["reason"]

    def test_file_inventory_in_message(self):
        """Block message should list the files that would be deleted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "important.py").write_text("critical code")
            for i in range(7):
                (Path(tmpdir) / f"helper_{i}.py").write_text("helper")

            data = {
                "tool_name": "Bash",
                "tool_input": {"command": f"rm -rf {tmpdir}"},
            }

            with mock.patch.object(gate, "create_git_tag", return_value=None):
                result = gate.run(data)

            assert result is not None
            assert "File inventory" in result["reason"]
            assert "important.py" in result["reason"]

    def test_inline_bypass_in_command(self):
        """BULK_DELETE_BYPASS=1 inline in command should bypass gate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(10):
                (Path(tmpdir) / f"file_{i}.py").write_text("x")

            data = {
                "tool_name": "Bash",
                "tool_input": {"command": f"BULK_DELETE_BYPASS=1 rm -rf {tmpdir}"},
            }

            # Ensure env var is NOT set (testing inline detection)
            with mock.patch.dict(os.environ, {}, clear=True):
                result = gate.run(data)

            assert result is None

    def test_backup_dir_is_safe(self):
        """Directories named .backup are always safe to delete."""
        assert gate.is_safe_target("project/.backup") is True
        assert gate.is_safe_target("project/.backup/") is True
