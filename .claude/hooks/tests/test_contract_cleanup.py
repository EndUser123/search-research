#!/usr/bin/env python3
"""
Unit tests for tdd/contract_cleanup.py

Tests:
- Completed contract detection
- Retention period enforcement
- Cleanup execution
- Statistics reporting

ADR: P:/docs/adrs/ADR-20260324-clean-room-tdd-loop.md
"""

from __future__ import annotations

import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))


def test_get_completed_contracts_returns_empty_for_no_evidence():
    """Test that empty list returned when no evidence exists."""
    from tdd.contract_cleanup import get_completed_contracts

    with tempfile.TemporaryDirectory() as tmpdir:
        evidence_dir = Path(tmpdir) / "evidence"
        contracts = get_completed_contracts(evidence_dir)
        assert contracts == []


def test_get_completed_contracts_finds_completed():
    """Test that completed contracts are found."""
    import json

    from tdd.contract_cleanup import get_completed_contracts

    with tempfile.TemporaryDirectory() as tmpdir:
        evidence_dir = Path(tmpdir) / "evidence"
        contract_dir = evidence_dir / "tdd95" / "abc123"
        contract_dir.mkdir(parents=True)

        # Create COMPLETE phase evidence
        evidence_file = contract_dir / "complete_2026-03-25T10-00-00.json"
        evidence_data = {
            "transition": {
                "from_phase": "refactor",
                "to_phase": "complete",
                "impl_path": "impl.py",
                "timestamp": "2026-03-25T10:00:00Z",
            }
        }
        with open(evidence_file, "w") as f:
            json.dump(evidence_data, f)

        contracts = get_completed_contracts(evidence_dir)

        assert len(contracts) == 1
        assert contracts[0]["contract_id"] == "abc123"
        assert contracts[0]["impl_path"] == "impl.py"


def test_get_completed_contracts_skips_incomplete():
    """Test that incomplete contracts are skipped."""
    import json

    from tdd.contract_cleanup import get_completed_contracts

    with tempfile.TemporaryDirectory() as tmpdir:
        evidence_dir = Path(tmpdir) / "evidence"
        contract_dir = evidence_dir / "tdd95" / "xyz789"
        contract_dir.mkdir(parents=True)

        # Create GREEN phase evidence (not complete)
        evidence_file = contract_dir / "green_2026-03-25T09-00-00.json"
        evidence_data = {
            "transition": {
                "from_phase": "red",
                "to_phase": "green",
                "impl_path": "impl.py",
                "timestamp": "2026-03-25T09:00:00Z",
            }
        }
        with open(evidence_file, "w") as f:
            json.dump(evidence_data, f)

        contracts = get_completed_contracts(evidence_dir)

        assert contracts == []


def test_cleanup_completed_contract_respects_retention():
    """Test that cleanup respects retention period."""
    import json

    from tdd.contract_cleanup import cleanup_completed_contract

    with tempfile.TemporaryDirectory() as tmpdir:
        evidence_dir = Path(tmpdir) / "evidence"
        contract_dir = evidence_dir / "tdd95" / "recent"
        contract_dir.mkdir(parents=True)

        # Create recent COMPLETE evidence (within retention)
        recent_time = datetime.now(timezone.utc) - timedelta(days=3)
        # Use safe filename format (replace colons with dashes)
        timestamp_safe = recent_time.isoformat().replace(":", "-").replace(".", "-")
        evidence_file = contract_dir / f"complete_{timestamp_safe}.json"
        evidence_data = {
            "transition": {
                "from_phase": "refactor",
                "to_phase": "complete",
                "impl_path": "impl.py",
                "timestamp": recent_time.isoformat(),
            }
        }
        with open(evidence_file, "w") as f:
            json.dump(evidence_data, f)

        # Try to cleanup with 7-day retention
        result = cleanup_completed_contract("recent", evidence_dir, retention_days=7)

        # Should return None (not eligible yet)
        assert result is None
        assert contract_dir.exists()


def test_cleanup_completed_contract_removes_old():
    """Test that cleanup removes old contracts."""
    import json

    from tdd.contract_cleanup import cleanup_completed_contract

    with tempfile.TemporaryDirectory() as tmpdir:
        evidence_dir = Path(tmpdir) / "evidence"
        contract_dir = evidence_dir / "tdd95" / "old123"
        contract_dir.mkdir(parents=True)

        # Create old COMPLETE evidence (beyond retention)
        old_time = datetime.now(timezone.utc) - timedelta(days=10)
        evidence_file = contract_dir / "complete_old.json"
        evidence_data = {
            "transition": {
                "from_phase": "refactor",
                "to_phase": "complete",
                "impl_path": "impl.py",
                "timestamp": old_time.isoformat(),
            }
        }
        with open(evidence_file, "w") as f:
            json.dump(evidence_data, f)

        # Cleanup with 7-day retention
        result = cleanup_completed_contract("old123", evidence_dir, retention_days=7)

        # Should cleanup successfully
        assert result is not None
        assert result.contract_id == "old123"
        assert result.evidence_files_removed == 1
        assert not contract_dir.exists()


def test_cleanup_all_with_dry_run():
    """Test dry-run mode reports without deleting."""
    import json

    from tdd.contract_cleanup import cleanup_all_completed_contracts

    with tempfile.TemporaryDirectory() as tmpdir:
        evidence_dir = Path(tmpdir) / "evidence"
        contract_dir = evidence_dir / "tdd95" / "drytest"
        contract_dir.mkdir(parents=True)

        # Create old evidence
        old_time = datetime.now(timezone.utc) - timedelta(days=10)
        evidence_file = contract_dir / "complete_old.json"
        evidence_data = {
            "transition": {
                "from_phase": "refactor",
                "to_phase": "complete",
                "impl_path": "impl.py",
                "timestamp": old_time.isoformat(),
            }
        }
        with open(evidence_file, "w") as f:
            json.dump(evidence_data, f)

        # Dry-run
        results = cleanup_all_completed_contracts(evidence_dir, retention_days=7, dry_run=True)

        assert len(results) == 1
        assert results[0].contract_id == "drytest"
        # Directory should still exist
        assert contract_dir.exists()


def test_get_cleanup_stats_reports_correctly():
    """Test statistics reporting."""
    import json

    from tdd.contract_cleanup import get_cleanup_stats

    with tempfile.TemporaryDirectory() as tmpdir:
        evidence_dir = Path(tmpdir) / "evidence"

        # Create one completed old contract (past retention)
        old_contract = evidence_dir / "tdd95" / "old"
        old_contract.mkdir(parents=True)
        old_time = datetime.now(timezone.utc) - timedelta(days=10)
        timestamp_safe = old_time.isoformat().replace(":", "-").replace(".", "-")
        with open(old_contract / f"complete_{timestamp_safe}.json", "w") as f:
            json.dump(
                {
                    "transition": {
                        "from_phase": "refactor",
                        "to_phase": "complete",
                        "impl_path": "old.py",
                        "timestamp": old_time.isoformat(),
                    }
                },
                f,
            )

        # Create one completed recent contract (within retention)
        recent_contract = evidence_dir / "tdd95" / "recent"
        recent_contract.mkdir(parents=True)
        recent_time = datetime.now(timezone.utc) - timedelta(days=3)
        recent_timestamp_safe = recent_time.isoformat().replace(":", "-").replace(".", "-")
        with open(recent_contract / f"complete_{recent_timestamp_safe}.json", "w") as f:
            json.dump(
                {
                    "transition": {
                        "from_phase": "refactor",
                        "to_phase": "complete",
                        "impl_path": "recent.py",
                        "timestamp": recent_time.isoformat(),
                    }
                },
                f,
            )

        # Create one incomplete contract
        incomplete_contract = evidence_dir / "tdd95" / "incomplete"
        incomplete_contract.mkdir(parents=True)
        with open(incomplete_contract / "green.json", "w") as f:
            json.dump(
                {
                    "transition": {
                        "from_phase": "red",
                        "to_phase": "green",
                        "impl_path": "incomplete.py",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                },
                f,
            )

        stats = get_cleanup_stats(evidence_dir)

        assert stats["total_contracts"] == 3
        assert stats["completed_contracts"] == 2
        assert stats["eligible_for_cleanup"] == 1  # Only old one
        assert stats["total_bytes_reclaimable"] > 0


def test_cleanup_handles_malformed_json():
    """Test that malformed JSON files are handled gracefully."""
    from tdd.contract_cleanup import get_completed_contracts

    with tempfile.TemporaryDirectory() as tmpdir:
        evidence_dir = Path(tmpdir) / "evidence"
        contract_dir = evidence_dir / "tdd95" / "malformed"
        contract_dir.mkdir(parents=True)

        # Create malformed JSON
        evidence_file = contract_dir / "complete_bad.json"
        with open(evidence_file, "w") as f:
            f.write("{ invalid json }")

        contracts = get_completed_contracts(evidence_dir)

        # Should skip malformed file
        assert contracts == []


def test_cleanup_result_dataclass():
    """Test CleanupResult dataclass fields."""
    from tdd.contract_cleanup import CleanupResult

    result = CleanupResult(
        contract_id="abc123",
        impl_path="impl.py",
        evidence_files_removed=5,
        freed_bytes=1024,
        completed_at="2026-03-25T10:00:00Z",
    )

    assert result.contract_id == "abc123"
    assert result.impl_path == "impl.py"
    assert result.evidence_files_removed == 5
    assert result.freed_bytes == 1024
    assert result.completed_at == "2026-03-25T10:00:00Z"


def main():
    """Run all tests."""
    import pytest

    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
