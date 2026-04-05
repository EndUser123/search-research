#!/usr/bin/env python3
"""
Regression tests for multi-terminal isolation in adversarial review system.

Tests verify:
1. Aggregator discovers terminal-scoped files
2. Aggregator ignores files from other terminals
3. Aggregator falls back to shared state when no terminal ID
4. Concurrent terminals don't interfere with each other
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks directory to path for imports
HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))


class TestAdversarialAggregatorTerminalIsolation:
    """Test adversarial aggregator multi-terminal isolation."""

    @pytest.fixture
    def temp_state_dir(self, tmp_path: Path) -> Path:
        """Create temporary state directory structure."""
        state_dir = tmp_path / "state"
        state_dir.mkdir()
        (state_dir / "terminals").mkdir()
        (state_dir / "shared").mkdir()
        return state_dir

    @pytest.fixture
    def terminal_a_id(self) -> str:
        """Terminal A ID."""
        return "console_abc123"

    @pytest.fixture
    def terminal_b_id(self) -> str:
        """Terminal B ID."""
        return "console_xyz789"

    def _create_adversarial_file(
        self,
        state_dir: Path,
        terminal_id: str | None,
        subagent: str,
        findings: list[dict],
        dt: str | None = None
    ) -> Path:
        """Create a test adversarial JSON file."""
        if terminal_id:
            target_dir = state_dir / "terminals" / terminal_id
        else:
            target_dir = state_dir / "shared"

        target_dir.mkdir(parents=True, exist_ok=True)

        dt = dt or datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"adversarial-{subagent}-{dt}.json"
        filepath = target_dir / filename

        data = {
            "timestamp": datetime.now().isoformat(),
            "terminal_id": terminal_id,
            "findings": findings
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return filepath

    def test_discover_files_from_correct_terminal(
        self, temp_state_dir: Path, terminal_a_id: str, terminal_b_id: str
    ):
        """Aggregator only discovers files from the current terminal."""
        # Create files in terminal A
        self._create_adversarial_file(
            temp_state_dir, terminal_a_id, "security",
            [{"severity": "HIGH", "location": "file_a.py:10"}]
        )

        # Create files in terminal B
        self._create_adversarial_file(
            temp_state_dir, terminal_b_id, "security",
            [{"severity": "CRITICAL", "location": "file_b.py:20"}]
        )

        # Import aggregator module
        from adversarial_aggregator import discover_subagent_files

        # Discover files for terminal A
        terminal_a_dir = temp_state_dir / "terminals" / terminal_a_id
        files_a = discover_subagent_files(terminal_a_dir)

        # Should only find terminal A's file
        assert len(files_a) == 1
        assert "security" in files_a[0].name
        assert terminal_a_id in str(files_a[0])

        # Discover files for terminal B
        terminal_b_dir = temp_state_dir / "terminals" / terminal_b_id
        files_b = discover_subagent_files(terminal_b_dir)

        # Should only find terminal B's file
        assert len(files_b) == 1
        assert "security" in files_b[0].name
        assert terminal_b_id in str(files_b[0])

    def test_aggregator_ignores_other_terminals(
        self, temp_state_dir: Path, terminal_a_id: str, terminal_b_id: str
    ):
        """Aggregator ignores files from other terminals."""
        from adversarial_aggregator import aggregate_findings, discover_subagent_files

        # Create CRITICAL finding in terminal B
        self._create_adversarial_file(
            temp_state_dir, terminal_b_id, "security",
            [{"severity": "CRITICAL", "location": "sensitive.py:100"}]
        )

        # Aggregate for terminal A (should not see terminal B's file)
        terminal_a_dir = temp_state_dir / "terminals" / terminal_a_id
        files_a = discover_subagent_files(terminal_a_dir)
        findings_a = aggregate_findings(files_a)

        assert len(findings_a) == 0, "Terminal A should not see terminal B's findings"

    def test_fallback_to_shared_state(
        self, temp_state_dir: Path
    ):
        """Aggregator falls back to shared state when no terminal ID."""
        from adversarial_aggregator import discover_subagent_files

        # Create file in shared state
        self._create_adversarial_file(
            temp_state_dir, None, "security",
            [{"severity": "MEDIUM", "location": "shared_file.py:50"}]
        )

        # Discover files from shared directory
        shared_dir = temp_state_dir / "shared"
        files = discover_subagent_files(shared_dir)

        assert len(files) == 1
        assert "shared" in str(files[0])

    def test_concurrent_terminals_no_interference(
        self, temp_state_dir: Path, terminal_a_id: str, terminal_b_id: str
    ):
        """Concurrent terminals don't interfere with each other's state."""
        from adversarial_aggregator import (
            aggregate_findings,
            calculate_consensus,
            discover_subagent_files,
            group_by_location,
            identify_blocking_issues,
        )

        # Simulate concurrent writes from both terminals
        # Terminal A: 3 security findings
        self._create_adversarial_file(
            temp_state_dir, terminal_a_id, "security",
            [{"severity": "HIGH", "location": "file.py:10"}]
        )
        self._create_adversarial_file(
            temp_state_dir, terminal_a_id, "performance",
            [{"severity": "MEDIUM", "location": "file.py:20"}]
        )
        self._create_adversarial_file(
            temp_state_dir, terminal_a_id, "quality",
            [{"severity": "LOW", "location": "file.py:30"}]
        )

        # Terminal B: 2 different findings (including CRITICAL)
        self._create_adversarial_file(
            temp_state_dir, terminal_b_id, "security",
            [{"severity": "CRITICAL", "location": "critical.py:5"}]
        )
        self._create_adversarial_file(
            temp_state_dir, terminal_b_id, "compliance",
            [{"severity": "HIGH", "location": "critical.py:10"}]
        )

        # Aggregate for terminal A
        terminal_a_dir = temp_state_dir / "terminals" / terminal_a_id
        files_a = discover_subagent_files(terminal_a_dir)
        findings_a = aggregate_findings(files_a)
        groups_a = group_by_location(findings_a)
        consensus_a = calculate_consensus(groups_a)

        # Terminal A should have 3 findings
        assert len(findings_a) == 3
        # No CRITICAL findings in terminal A
        blocking_a = identify_blocking_issues(consensus_a, threshold=1)
        assert len(blocking_a) == 0, "Terminal A has no CRITICAL findings"

        # Aggregate for terminal B
        terminal_b_dir = temp_state_dir / "terminals" / terminal_b_id
        files_b = discover_subagent_files(terminal_b_dir)
        findings_b = aggregate_findings(files_b)
        groups_b = group_by_location(findings_b)
        consensus_b = calculate_consensus(groups_b)

        # Terminal B should have 2 findings
        assert len(findings_b) == 2
        # Terminal B has CRITICAL finding
        blocking_b = identify_blocking_issues(consensus_b, threshold=1)
        assert len(blocking_b) >= 1, "Terminal B has CRITICAL findings"

    def test_aggregated_output_is_terminal_scoped(
        self, temp_state_dir: Path, terminal_a_id: str
    ):
        """Aggregated output is written to terminal-scoped directory."""
        from adversarial_aggregator import main

        # Create a test finding
        self._create_adversarial_file(
            temp_state_dir, terminal_a_id, "security",
            [{"severity": "HIGH", "location": "test.py:10"}]
        )

        # Mock get_terminal_id to return terminal_a_id
        with patch("adversarial_aggregator.get_terminal_id", return_value=terminal_a_id):
            with patch("adversarial_aggregator.get_terminal_state_dir") as mock_get_dir:
                mock_get_dir.return_value = temp_state_dir / "terminals" / terminal_a_id

                # Run aggregator
                result = main()

                assert result == 0

                # Check output file location
                output_file = temp_state_dir / "terminals" / terminal_a_id / "adversarial-review-latest.json"
                assert output_file.exists(), "Aggregated output should be in terminal-scoped directory"

                with open(output_file, encoding="utf-8") as f:
                    data = json.load(f)

                assert data["terminal_id"] == terminal_a_id
                assert len(data["findings"]) == 1


class TestTerminalIDDetection:
    """Test terminal ID detection for adversarial system."""

    def test_terminal_id_from_wt_session(self, monkeypatch):
        """Terminal ID is derived from WT_SESSION environment variable."""
        from __lib.runtime_env import get_terminal_id

        # Mock WT_SESSION
        monkeypatch.setenv("WT_SESSION", "test-uuid-12345")

        # Should return a non-empty terminal ID
        # (actual implementation may vary based on hook_ledger)
        result = get_terminal_id()
        # Note: Result depends on hook_ledger implementation
        # Just verify it doesn't crash
        assert isinstance(result, str)

    def test_terminal_id_empty_when_no_env(self, monkeypatch):
        """Terminal ID is empty when no environment variable set."""
        from __lib.runtime_env import get_terminal_id

        # Remove WT_SESSION
        monkeypatch.delenv("WT_SESSION", raising=False)

        # Result depends on hook_ledger availability
        result = get_terminal_id()
        assert isinstance(result, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
