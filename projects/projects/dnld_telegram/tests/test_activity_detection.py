"""
Test for robust activity detection (Protocol v4.1)
"""

import tempfile
from pathlib import Path


def test_detects_recent_file_activity():
    """Test that recent file modifications are detected as activity"""
    # This test will fail until we implement ActivityDetector
    from dev.refactors.coordination.activity_detector import ActivityDetector

    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test directory structure
        src_dir = Path(temp_dir) / "src"
        src_dir.mkdir()

        # Create a recent Python file
        test_file = src_dir / "test_module.py"
        test_file.write_text("# Recent activity")

        # Create ActivityDetector
        detector = ActivityDetector(
            coordination_file=str(Path(temp_dir) / "tasks.json"),
            stale_timeout_minutes=15,
        )
        detector.project_root = Path(temp_dir)

        # Should detect recent file activity
        has_activity = detector.check_file_activity("test-llm", "QW-3")

        assert has_activity, "Should detect recent file modifications as activity"
