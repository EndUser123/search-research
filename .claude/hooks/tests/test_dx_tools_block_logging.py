"""
Tests for DX Tools Block Decision Logging

Tests authorization gate block decision logging and analysis.
"""
import json
import sys
from datetime import datetime
from pathlib import Path

# Add __lib to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "__lib"))

from unittest.mock import patch


class TestBlockLogging:
    """Test block decision logging functionality."""

    def test_log_block_decision_creates_file(self, tmp_path):
        """Test block logging creates auth_blocks.jsonl file."""
        # Import after ensuring tmp_path exists
        hooks_dir = Path(__file__).resolve().parent.parent

        # Mock the hooks directory to use tmp_path
        with patch('dx_tools_observability.Path') as mock_path:
            mock_path.return_value.parent = tmp_path
            mock_path.return_value = tmp_path / "logs"

            # Import and call the function
            import importlib

            import PreToolUse_authorization_gate

            # Reload to pick up mocked path
            importlib.reload(PreToolUse_authorization_gate)

            # Call the logging function
            PreToolUse_authorization_gate._log_block_decision(
                command="rm -rf /some/path",
                working_dir="P:/packages/test",
                reason="not_project_tree",
                pattern="rm -rf"
            )

            # Verify log file was created
            log_file = tmp_path / "logs" / "auth_blocks.jsonl"
            assert log_file.exists()

    def test_log_block_decision_jsonl_format(self, tmp_path):
        """Test logged blocks are in valid JSONL format."""
        hooks_dir = Path(__file__).resolve().parent.parent

        with patch('dx_tools_observability.Path') as mock_path:
            mock_path.return_value.parent = tmp_path
            mock_path.return_value = tmp_path / "logs"

            import importlib

            import PreToolUse_authorization_gate
            importlib.reload(PreToolUse_authorization_gate)

            # Log a block decision
            PreToolUse_authorization_gate._log_block_decision(
                command="git branch -D feature",
                working_dir="C:/system",
                reason="not_project_tree",
                pattern="git branch -D"
            )

            # Read and parse log entry
            log_file = tmp_path / "logs" / "auth_blocks.jsonl"
            with open(log_file) as f:
                line = f.readline()
                entry = json.loads(line)

            # Verify entry structure
            assert "timestamp" in entry
            assert "command" in entry
            assert "working_dir" in entry
            assert "reason" in entry
            assert "pattern" in entry

    def test_log_block_decision_multiple_entries(self, tmp_path):
        """Test multiple block decisions are logged correctly."""
        hooks_dir = Path(__file__).resolve().parent.parent

        with patch('dx_tools_observability.Path') as mock_path:
            mock_path.return_value.parent = tmp_path
            mock_path.return_value = tmp_path / "logs"

            import importlib

            import PreToolUse_authorization_gate
            importlib.reload(PreToolUse_authorization_gate)

            # Log multiple blocks
            PreToolUse_authorization_gate._log_block_decision(
                "rm -rf cache", "P:/test", "not_safe_pattern", ""
            )
            PreToolUse_authorization_gate._log_block_decision(
                "git reset --hard", "P:/test", "no_authorization", ""
            )
            PreToolUse_authorization_gate._log_block_decision(
                "drop table users", "P:/test", "not_safe_pattern", ""
            )

            # Verify all entries logged
            log_file = tmp_path / "logs" / "auth_blocks.jsonl"
            with open(log_file) as f:
                lines = f.readlines()

            assert len(lines) == 3

            # Verify each can be parsed
            for line in lines:
                entry = json.loads(line)
                assert "command" in entry
                assert "reason" in entry


class TestBlockAnalysisScript:
    """Test block analysis script functionality."""

    def test_parse_block_log_file(self, tmp_path):
        """Test script can parse block log file."""
        # Create test block log
        log_file = tmp_path / "auth_blocks.jsonl"

        test_entries = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "command": "rm -rf test",
                "working_dir": "C:/system",
                "reason": "not_project_tree",
                "pattern": "rm -rf"
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "command": "git branch -D feature",
                "working_dir": "C:/system",
                "reason": "not_project_tree",
                "pattern": "git branch -D"
            }
        ]

        with open(log_file, "w") as f:
            for entry in test_entries:
                f.write(json.dumps(entry) + "\n")

        # Import and test analysis script
        scripts_dir = Path(__file__).resolve().parent.parent / "scripts"
        sys.path.insert(0, str(scripts_dir))

        import dx_tools_analyze_blocks
        blocks = dx_tools_analyze_blocks.load_blocks(log_file, days=7)

        assert len(blocks) == 2
        assert blocks[0]["command"] == "rm -rf test"
        assert blocks[1]["command"] == "git branch -D feature"

    def test_analyze_blocks_calculates_metrics(self):
        """Test block analysis calculates correct metrics."""
        test_blocks = [
            {"reason": "not_project_tree", "pattern": "rm -rf"},
            {"reason": "not_project_tree", "pattern": "rm -rf"},
            {"reason": "not_safe_pattern", "pattern": ""},
            {"reason": "not_project_tree", "pattern": "git branch -D"},
        ]

        import dx_tools_analyze_blocks
        analysis = dx_tools_analyze_blocks.analyze_blocks(test_blocks)

        assert analysis["total_blocks"] == 4
        assert analysis["by_reason"]["not_project_tree"] == 3
        assert analysis["by_reason"]["not_safe_pattern"] == 1

    def test_analyze_blocks_top_patterns(self):
        """Test analysis identifies top blocked patterns."""
        test_blocks = [
            {"reason": "test", "pattern": "rm -rf"},
            {"reason": "test", "pattern": "rm -rf"},
            {"reason": "test", "pattern": "rm -rf"},
            {"reason": "test", "pattern": "git branch -D"},
            {"reason": "test", "pattern": "git reset --hard"},
        ]

        import dx_tools_analyze_blocks
        analysis = dx_tools_analyze_blocks.analyze_blocks(test_blocks)

        assert "by_pattern" in analysis
        assert analysis["by_pattern"]["rm -rf"] == 3

    def test_recent_blocks_sorted(self):
        """Test recent blocks are sorted by timestamp (newest first)."""
        now = datetime.utcnow()

        test_blocks = [
            {"timestamp": (now - __import__("datetime").timedelta(hours=3)).isoformat(), "command": "old"},
            {"timestamp": (now - __import__("datetime").timedelta(hours=1)).isoformat(), "command": "recent"},
            {"timestamp": (now - __import__("datetime").timedelta(hours=2)).isoformat(), "command": "middle"},
        ]

        import dx_tools_analyze_blocks
        analysis = dx_tools_analyze_blocks.analyze_blocks(test_blocks)

        recent = analysis["recent_blocks"]
        assert len(recent) == 3
        assert recent[0]["command"] == "recent"  # Most recent first

    def test_empty_block_log_handling(self, tmp_path):
        """Test script handles empty block log gracefully."""
        log_file = tmp_path / "empty_blocks.jsonl"

        # Create empty file
        log_file.touch()

        import dx_tools_analyze_blocks
        blocks = dx_tools_analyze_blocks.load_blocks(log_file, days=7)

        assert len(blocks) == 0

        analysis = dx_tools_analyze_blocks.analyze_blocks(blocks)
        assert analysis["total_blocks"] == 0
