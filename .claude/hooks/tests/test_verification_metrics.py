#!/usr/bin/env python3
"""
Test suite for verification gate metrics collection system.

TASK-010: Monitoring & Iteration
Tests for telemetry collection, security fixes (SEC-003), and weekly analysis.
"""

import json
import os
import sys
from pathlib import Path
from unittest import mock

import pytest

# Add hooks directory to path for imports
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from telemetry.verification_metrics import (
    SECURE_PERMISSIONS,
    VerificationMetrics,
    collect_verification_metric,
    get_metrics_summary,
    sanitize_metric_entry,
)


class TestSecurePermissions:
    """Test SEC-003: Secure file permissions (0600 owner-only)."""

    def test_metrics_log_created_with_secure_permissions(self, tmp_path):
        """Test that metrics log is created with owner-only permissions (0600)."""
        metrics_file = tmp_path / "test_metrics.jsonl"

        collector = VerificationMetrics(metrics_file=str(metrics_file))
        collector.record_event(
            tier="tier1_component",
            blocked=True,
            confidence=0.95,
            reason="Test block"
        )

        # Check file permissions on Unix-like systems
        if os.name != 'nt':  # Skip on Windows
            stat_info = os.stat(metrics_file)
            mode = oct(stat_info.st_mode & 0o777)
            assert mode == oct(SECURE_PERMISSIONS), f"Expected {oct(SECURE_PERMISSIONS)}, got {mode}"

    def test_secure_permissions_constant(self):
        """Test that SECURE_PERMISSIONS is set to 0600."""
        assert SECURE_PERMISSIONS == 0o600, "SECURE_PERMISSIONS should be 0o600 (owner-only)"


class TestMetricSanitization:
    """Test SEC-003: Sanitization removes sensitive data."""

    def test_sanitize_removes_commands(self):
        """Test that command strings are removed from metrics."""
        entry = {
            "tier": "tier1_component",
            "blocked": True,
            "command": "python P:/.claude/hooks/test.py",  # Sensitive
            "timestamp": "2026-03-10T12:00:00"
        }

        sanitized = sanitize_metric_entry(entry)

        assert "command" not in sanitized, "Command field should be removed"
        assert sanitized["tier"] == "tier1_component"
        assert sanitized["blocked"] is True

    def test_sanitize_removes_file_paths(self):
        """Test that file paths are removed from metrics."""
        entry = {
            "tier": "tier1_component",
            "blocked": True,
            "file_path": "P:/secret/project/config.py",  # Sensitive
            "timestamp": "2026-03-10T12:00:00"
        }

        sanitized = sanitize_metric_entry(entry)

        assert "file_path" not in sanitized, "file_path field should be removed"
        assert sanitized["tier"] == "tier1_component"

    def test_sanitize_removes_user_content(self):
        """Test that user response content is removed from metrics."""
        entry = {
            "tier": "tier1_component",
            "blocked": True,
            "response_text": "The user said: My password is secret123",  # Sensitive
            "timestamp": "2026-03-10T12:00:00"
        }

        sanitized = sanitize_metric_entry(entry)

        assert "response_text" not in sanitized, "response_text field should be removed"
        assert "user_content" not in sanitized, "user_content field should be removed"

    def test_sanitize_keeps_required_fields(self):
        """Test that required fields are preserved after sanitization."""
        entry = {
            "tier": "tier2_e2e",
            "blocked": False,
            "confidence": 0.85,
            "category": "completion_claim",
            "timestamp": "2026-03-10T12:00:00",
            "command": "rm -rf /",  # Sensitive
            "response": "User data here"  # Sensitive
        }

        sanitized = sanitize_metric_entry(entry)

        # Required fields must remain
        assert sanitized["tier"] == "tier2_e2e"
        assert sanitized["blocked"] is False
        assert sanitized["confidence"] == 0.85
        assert sanitized["category"] == "completion_claim"
        assert "timestamp" in sanitized

        # Sensitive fields must be removed
        assert "command" not in sanitized
        assert "response" not in sanitized

    def test_sanitize_handles_empty_dict(self):
        """Test that sanitization handles empty entries."""
        sanitized = sanitize_metric_entry({})
        # Empty dict gets timestamp added (required field)
        assert "timestamp" in sanitized
        assert len(sanitized) == 1


class TestMetricsCollection:
    """Test metrics collection and storage."""

    def test_record_event_writes_jsonl(self, tmp_path):
        """Test that events are written in JSONL format (one JSON per line)."""
        metrics_file = tmp_path / "test_metrics.jsonl"

        collector = VerificationMetrics(metrics_file=str(metrics_file))
        collector.record_event(
            tier="tier1_component",
            blocked=True,
            confidence=0.95,
            category="completion_claim"
        )
        collector.record_event(
            tier="tier2_e2e",
            blocked=False,
            confidence=0.80,
            category="stance_verification"
        )

        # Verify JSONL format
        lines = metrics_file.read_text().strip().split("\n")
        assert len(lines) == 2

        # Verify each line is valid JSON
        for line in lines:
            data = json.loads(line)
            assert "tier" in data
            assert "blocked" in data
            assert "timestamp" in data

    def test_record_event_sanitizes_before_writing(self, tmp_path):
        """Test that events are sanitized before being written to disk."""
        metrics_file = tmp_path / "test_metrics.jsonl"

        collector = VerificationMetrics(metrics_file=str(metrics_file))
        collector.record_event(
            tier="tier1_component",
            blocked=True,
            confidence=0.95,
            command="python secret_script.py",  # Should be removed
            file_path="P:/secret/config.py"  # Should be removed
        )

        # Read back the file
        lines = metrics_file.read_text().strip().split("\n")
        data = json.loads(lines[0])

        # Verify sanitization occurred
        assert "command" not in data
        assert "file_path" not in data
        assert "tier" in data
        assert "blocked" in data

    def test_collect_verification_metric_helper(self, tmp_path):
        """Test the collect_verification_metric() helper function."""
        metrics_file = tmp_path / "test_metrics.jsonl"

        with mock.patch('telemetry.verification_metrics.DEFAULT_METRICS_FILE', str(metrics_file)):
            collect_verification_metric(
                tier="tier1_component",
                blocked=True,
                confidence=0.95,
                category="test_category"
            )

            # Verify metric was collected
            lines = metrics_file.read_text().strip().split("\n")
            assert len(lines) == 1
            data = json.loads(lines[0])
            assert data["tier"] == "tier1_component"
            assert data["blocked"] is True


class TestMetricsSummary:
    """Test metrics summary and analysis functions."""

    def test_get_metrics_summary_empty(self, tmp_path):
        """Test summary with no metrics."""
        metrics_file = tmp_path / "test_metrics.jsonl"
        metrics_file.write_text("")

        summary = get_metrics_summary(metrics_file=str(metrics_file))

        assert summary["total_events"] == 0
        assert summary["blocked_count"] == 0
        assert summary["allowed_count"] == 0

    def test_get_metrics_summary_with_data(self, tmp_path):
        """Test summary with actual metrics data."""
        metrics_file = tmp_path / "test_metrics.jsonl"

        # Write test data
        collector = VerificationMetrics(metrics_file=str(metrics_file))
        collector.record_event(tier="tier1_component", blocked=True, confidence=0.95)
        collector.record_event(tier="tier1_component", blocked=True, confidence=0.85)
        collector.record_event(tier="tier2_e2e", blocked=False, confidence=0.80)

        summary = get_metrics_summary(metrics_file=str(metrics_file))

        assert summary["total_events"] == 3
        assert summary["blocked_count"] == 2
        assert summary["allowed_count"] == 1
        assert summary["block_rate"] == pytest.approx(0.667, rel=0.01)

    def test_get_metrics_summary_by_tier(self, tmp_path):
        """Test summary breakdown by verification tier."""
        metrics_file = tmp_path / "test_metrics.jsonl"

        collector = VerificationMetrics(metrics_file=str(metrics_file))
        collector.record_event(tier="tier1_component", blocked=True, confidence=0.95)
        collector.record_event(tier="tier1_component", blocked=False, confidence=0.80)
        collector.record_event(tier="tier2_e2e", blocked=True, confidence=0.85)

        summary = get_metrics_summary(metrics_file=str(metrics_file))

        assert "tier1_component" in summary["by_tier"]
        assert "tier2_e2e" in summary["by_tier"]
        assert summary["by_tier"]["tier1_component"]["count"] == 2
        assert summary["by_tier"]["tier2_e2e"]["count"] == 1

    def test_get_metrics_summary_confidence_distribution(self, tmp_path):
        """Test confidence score distribution in summary."""
        metrics_file = tmp_path / "test_metrics.jsonl"

        collector = VerificationMetrics(metrics_file=str(metrics_file))
        collector.record_event(tier="tier1_component", blocked=True, confidence=0.95)
        collector.record_event(tier="tier1_component", blocked=True, confidence=0.65)
        collector.record_event(tier="tier2_e2e", blocked=False, confidence=0.50)

        summary = get_metrics_summary(metrics_file=str(metrics_file))

        assert "confidence_distribution" in summary
        assert "high" in summary["confidence_distribution"]
        assert "medium" in summary["confidence_distribution"]
        assert "low" in summary["confidence_distribution"]


class TestWeeklyAnalysisScript:
    """Test the weekly verification analysis script."""

    def test_weekly_analysis_generates_report(self, tmp_path):
        """Test that weekly analysis script generates a report."""
        metrics_file = tmp_path / "test_metrics.jsonl"

        # Create test data spanning 7 days
        collector = VerificationMetrics(metrics_file=str(metrics_file))
        for i in range(10):
            collector.record_event(
                tier="tier1_component",
                blocked=(i % 2 == 0),  # Alternate blocked/allowed
                confidence=0.8 + (i * 0.01)
            )

        # Import and run analysis script
        from scripts.weekly_verification_analysis import generate_weekly_report

        report = generate_weekly_report(metrics_file=str(metrics_file))

        assert report["period_days"] == 7
        assert report["total_events"] == 10
        assert "recommendations" in report
        assert len(report["recommendations"]) > 0

    def test_weekly_analysis_tunes_patterns(self, tmp_path):
        """Test that weekly analysis provides tuning recommendations."""
        metrics_file = tmp_path / "test_metrics.jsonl"

        # Create test data with high false positive rate
        # Need >50% block rate and >10% low confidence to trigger FP warning
        collector = VerificationMetrics(metrics_file=str(metrics_file))
        for i in range(20):
            # All blocked = 100% block rate
            collector.record_event(
                tier="tier1_component",
                blocked=True,
                confidence=0.4,  # Low confidence (<0.5 = "low" in distribution)
                category="suspicious_pattern"
            )

        from scripts.weekly_verification_analysis import generate_weekly_report

        report = generate_weekly_report(metrics_file=str(metrics_file))

        # Should recommend pattern tuning due to high block rate + low confidence
        assert any("false positive" in rec.lower() for rec in report["recommendations"])

    def test_weekly_analysis_handles_empty_metrics(self, tmp_path):
        """Test that weekly analysis handles empty metrics file."""
        metrics_file = tmp_path / "test_metrics.jsonl"
        metrics_file.write_text("")

        from scripts.weekly_verification_analysis import generate_weekly_report

        report = generate_weekly_report(metrics_file=str(metrics_file))

        assert report["total_events"] == 0
        assert report["period_days"] == 7


class TestStopHookIntegration:
    """Test integration with StopHook_unverified_stance.py."""

    def test_stophook_collects_metrics_on_block(self, tmp_path):
        """Test that StopHook collects metrics when blocking."""
        metrics_file = tmp_path / "test_metrics.jsonl"

        with mock.patch('telemetry.verification_metrics.DEFAULT_METRICS_FILE', str(metrics_file)):
            # Simulate StopHook blocking an event
            collect_verification_metric(
                tier="tier1_component",
                blocked=True,
                confidence=0.95,
                category="completion_claim",
                reason="No runtime evidence for completion claim"
            )

            # Verify metric was collected
            summary = get_metrics_summary(metrics_file=str(metrics_file))
            assert summary["total_events"] == 1
            assert summary["blocked_count"] == 1

    def test_stophook_collects_metrics_on_allow(self, tmp_path):
        """Test that StopHook collects metrics when allowing."""
        metrics_file = tmp_path / "test_metrics.jsonl"

        with mock.patch('telemetry.verification_metrics.DEFAULT_METRICS_FILE', str(metrics_file)):
            # Simulate StopHook allowing an event
            collect_verification_metric(
                tier="tier2_e2e",
                blocked=False,
                confidence=0.75,
                category="stance_verification",
                reason="Stance verification passed"
            )

            # Verify metric was collected
            summary = get_metrics_summary(metrics_file=str(metrics_file))
            assert summary["total_events"] == 1
            assert summary["allowed_count"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
