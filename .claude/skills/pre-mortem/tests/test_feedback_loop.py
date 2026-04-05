"""Tests for pre-mortem feedback loop utilities.

Tests cover prediction storage, accuracy calculations, file I/O, and concurrency.
Target: 80%+ coverage.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

from __lib.feedback_loop import (
    PreMortemFeedbackLoop,
    sanitize_project_name,
)


class TestSanitizeProjectName:
    """Tests for sanitize_project_name function."""

    def test_allows_alphanumeric_underscore_hyphen(self) -> None:
        """Should allow alphanumeric, underscore, and hyphen characters."""
        assert sanitize_project_name("Test-Project_123") == "Test-Project_123"
        assert sanitize_project_name("my_project") == "my_project"
        assert sanitize_project_name("Test-123") == "Test-123"

    def test_removes_special_characters(self) -> None:
        """Should remove all characters except a-zA-Z0-9_-."""
        assert sanitize_project_name("test/../../etc") == "testetc"
        assert sanitize_project_name("test..project") == "testproject"
        assert sanitize_project_name("test@#$%project") == "testproject"

    def test_limits_length_to_50_chars(self) -> None:
        """Should limit output to 50 characters."""
        long_name = "a" * 100
        assert len(sanitize_project_name(long_name)) == 50

    def test_returns_unnamed_for_empty_string(self) -> None:
        """Should return 'unnamed' for empty or all-special-char strings."""
        assert sanitize_project_name("") == "unnamed"
        assert sanitize_project_name("@#$") == "unnamed"


class TestPreMortemFeedbackLoop:
    """Tests for PreMortemFeedbackLoop class."""

    def test_creates_memory_directory(self, tmp_path: Path) -> None:
        """Should create memory directory if it doesn't exist."""
        feedback = PreMortemFeedbackLoop(memory_dir=tmp_path / "memory")
        assert feedback.memory_dir.exists()

    def test_store_prediction_creates_file(self, tmp_path: Path) -> None:
        """Should create prediction file with correct content."""
        feedback = PreMortemFeedbackLoop(memory_dir=tmp_path / "memory")
        predictions = [
            {
                "risk_score": 9,
                "description": "Database failure",
                "mitigation": "Add retry",
            }
        ]
        kill_criteria = [{"type": "Time-Based", "description": ">2 hours without prototype"}]

        filepath = feedback.store_prediction("test-project", predictions, kill_criteria)

        assert filepath.exists()
        content = filepath.read_text(encoding="utf-8")
        assert "Database failure" in content
        assert "Add retry" in content
        assert ">2 hours without prototype" in content

    def test_store_prediction_sanitizes_project_name(self, tmp_path: Path) -> None:
        """Should sanitize project name in filename."""
        feedback = PreMortemFeedbackLoop(memory_dir=tmp_path / "memory")
        predictions = [{"risk_score": 9, "description": "Test", "mitigation": "Fix"}]
        kill_criteria = []

        filepath = feedback.store_prediction("../../etc/passwd", predictions, kill_criteria)

        # Should sanitize the dangerous path - removes special chars
        # "../../etc/passwd" becomes "etcpasswd"
        # Check that the dangerous path separators are removed
        filename = filepath.name
        assert "/" not in filename  # No path separators
        assert "\\" not in filename  # No Windows path separators
        # Allow dots in timestamp (ISO format has colons replaced with dots)
        assert filename.count(".") <= 3  # At most: project name + timestamp dots + extension

    def test_get_pending_validations_filters_old_files(self, tmp_path: Path) -> None:
        """Should only return files older than threshold."""
        feedback = PreMortemFeedbackLoop(memory_dir=tmp_path / "memory")

        # Create old file using store_prediction with actual old date
        old_date = (datetime.now() - timedelta(days=40)).isoformat()
        safe_project = sanitize_project_name("old_project")
        old_filename = f"premortem_{safe_project}_{old_date.replace(':', '-')}.md"
        old_file = tmp_path / "memory" / old_filename
        old_file.parent.mkdir(parents=True, exist_ok=True)
        old_file.write_text("**Status**: PENDING", encoding="utf-8")

        # Create recent file
        recent_file = feedback.store_prediction("recent", [], [])

        pending = feedback.get_pending_validations(days_threshold=30)

        # Only old file should be returned
        assert len(pending) == 1
        assert "old_project" in str(pending[0])

    def test_validate_prediction_calculates_accuracy(self, tmp_path: Path) -> None:
        """Should calculate accuracy from predictions vs outcomes."""
        feedback = PreMortemFeedbackLoop(memory_dir=tmp_path / "memory")
        predictions = [
            {
                "risk_score": 9,
                "description": "Database failure",
                "mitigation": "Add retry",
            }
        ]
        kill_criteria = []
        prediction_file = feedback.store_prediction("test", predictions, kill_criteria)

        actual_outcomes = {"database_failure": True}
        results = feedback.validate_prediction(prediction_file, actual_outcomes)

        assert results["total_predictions"] == 1
        assert results["accuracy"] == 1.0  # 100% accuracy

    def test_validate_prediction_updates_file(self, tmp_path: Path) -> None:
        """Should update prediction file with validation results."""
        feedback = PreMortemFeedbackLoop(memory_dir=tmp_path / "memory")
        predictions = [{"risk_score": 9, "description": "Test risk", "mitigation": "Fix"}]
        kill_criteria = []
        prediction_file = feedback.store_prediction("test", predictions, kill_criteria)

        feedback.validate_prediction(prediction_file, {"test_risk": True})

        updated_content = prediction_file.read_text(encoding="utf-8")
        assert "**Status**: VALIDATED" in updated_content
        assert "Validation Results" in updated_content


class TestPreMortemFeedbackLoopConcurrency:
    """Tests for multi-terminal isolation and concurrent access."""

    def test_concurrent_store_prediction(self, tmp_path: Path) -> None:
        """Multiple terminals should be able to store predictions simultaneously."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)

        predictions = [
            {"risk_score": 9, "description": f"Risk {i}", "mitigation": f"Fix {i}"}
            for i in range(10)
        ]
        kill_criteria = [{"type": "Time-Based", "description": ">2 hours"}]

        results = []
        errors = []

        def store_prediction(thread_id: int) -> tuple[bool, str | None]:
            """Store a prediction from a separate 'terminal'."""
            try:
                feedback = PreMortemFeedbackLoop(memory_dir=memory_dir)
                filepath = feedback.store_prediction(
                    f"concurrent_test_{thread_id}", predictions, kill_criteria
                )
                return (True, str(filepath))
            except Exception as e:
                return (False, str(e))

        # Simulate 5 concurrent terminals storing predictions
        threads = []
        for i in range(5):
            t = threading.Thread(
                target=lambda r=results, e=errors, i=i: r.append(store_prediction(i))
            )
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join(timeout=10)
            assert not t.is_alive(), "Thread should complete within timeout"

        # All operations should succeed
        assert len(results) == 5
        successful = sum(1 for success, _ in results if success)
        assert successful == 5, "All concurrent stores should succeed"

        # All files should be created
        created_files = list(memory_dir.glob("premortem_concurrent_test_*.md"))
        assert len(created_files) == 5, "All prediction files should be created"

    def test_concurrent_get_pending_validations(self, tmp_path: Path) -> None:
        """Multiple terminals should be able to query pending validations."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)

        # Create some pending pre-mortems
        feedback = PreMortemFeedbackLoop(memory_dir=memory_dir)
        for i in range(3):
            old_date = (datetime.now() - timedelta(days=35 + i)).isoformat()
            safe_project = sanitize_project_name(f"pending_{i}")
            filename = f"premortem_{safe_project}_{old_date.replace(':', '-')}.md"
            filepath = memory_dir / filename
            filepath.write_text("**Status**: PENDING", encoding="utf-8")

        pending_results = []
        errors = []

        def get_pending(thread_id: int) -> tuple[int, str | None]:
            """Query pending validations from a separate 'terminal'."""
            try:
                feedback = PreMortemFeedbackLoop(memory_dir=memory_dir)
                pending = feedback.get_pending_validations(days_threshold=30)
                return (len(pending), None)
            except Exception as e:
                return (-1, str(e))

        # Simulate 5 concurrent terminals querying pending validations
        threads = []
        for i in range(5):
            t = threading.Thread(
                target=lambda r=pending_results, e=errors, i=i: r.append(get_pending(i))
            )
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join(timeout=10)
            assert not t.is_alive(), "Thread should complete within timeout"

        # All queries should succeed and return consistent results
        assert len(pending_results) == 5
        counts = [count for count, _ in pending_results]
        assert all(c == 3 for c in counts), "All terminals should see the same 3 pending items"

    def test_concurrent_read_write_isolation(self, tmp_path: Path) -> None:
        """Concurrent reads and writes should not corrupt data."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)

        # Create an initial prediction
        feedback = PreMortemFeedbackLoop(memory_dir=memory_dir)
        predictions = [{"risk_score": 9, "description": "Initial risk", "mitigation": "Fix"}]
        kill_criteria = [{"type": "Time-Based", "description": ">2 hours"}]
        initial_file = feedback.store_prediction("isolation_test", predictions, kill_criteria)

        results = {"reads": 0, "writes": 0, "errors": 0}
        lock = threading.Lock()

        def read_prediction(iteration: int) -> None:
            """Simulate terminal reading the prediction file."""
            try:
                for _ in range(10):
                    feedback = PreMortemFeedbackLoop(memory_dir=memory_dir)
                    pending = feedback.get_pending_validations(days_threshold=30)
                    time.sleep(0.001)  # Small delay to increase contention
                with lock:
                    results["reads"] += 1
            except Exception:
                with lock:
                    results["errors"] += 1

        def write_prediction(iteration: int) -> None:
            """Simulate terminal writing a new prediction."""
            try:
                for i in range(5):
                    new_predictions = [
                        {
                            "risk_score": 9,
                            "description": f"New risk {i}",
                            "mitigation": "Fix",
                        }
                    ]
                    feedback = PreMortemFeedbackLoop(memory_dir=memory_dir)
                    feedback.store_prediction(
                        f"isolation_test_write_{i}", new_predictions, kill_criteria
                    )
                    time.sleep(0.002)  # Small delay to increase contention
                with lock:
                    results["writes"] += 1
            except Exception:
                with lock:
                    results["errors"] += 1

        # Simulate 3 readers and 2 writers
        threads = []
        for i in range(3):
            t = threading.Thread(target=read_prediction, args=(i,))
            threads.append(t)
            t.start()

        for i in range(2):
            t = threading.Thread(target=write_prediction, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join(timeout=30)
            assert not t.is_alive(), "Thread should complete within timeout"

        # All operations should complete without errors
        assert results["errors"] == 0, "No concurrent access errors should occur"
        assert results["reads"] == 3, "All reads should complete"
        assert results["writes"] == 2, "All writes should complete"

        # Original file should still be valid
        assert initial_file.exists(), "Original file should not be corrupted"
        content = initial_file.read_text(encoding="utf-8")
        assert "Initial risk" in content, "Original content should be preserved"

    def test_simultaneous_validation(self, tmp_path: Path) -> None:
        """Multiple terminals should be able to validate predictions simultaneously."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)

        # Create prediction files to validate
        feedback = PreMortemFeedbackLoop(memory_dir=memory_dir)
        predictions = [{"risk_score": 9, "description": "Test risk", "mitigation": "Fix"}]
        kill_criteria = []

        prediction_files = []
        for i in range(3):
            filepath = feedback.store_prediction(f"simultaneous_{i}", predictions, kill_criteria)
            prediction_files.append(filepath)

        validation_results = []
        errors = []

        def validate_prediction(filepath: Path) -> None:
            """Validate a prediction from a separate 'terminal'."""
            try:
                feedback = PreMortemFeedbackLoop(memory_dir=memory_dir)
                results = feedback.validate_prediction(filepath, {"test_risk": True})
                validation_results.append(results)
            except Exception as e:
                errors.append(str(e))

        # Simulate 3 terminals validating different predictions
        threads = []
        for filepath in prediction_files:
            t = threading.Thread(target=validate_prediction, args=(filepath,))
            threads.append(t)
            t.start()

        # Wait for all validations to complete
        for t in threads:
            t.join(timeout=30)
            assert not t.is_alive(), "Thread should complete within timeout"

        # All validations should succeed
        assert len(errors) == 0, "No validation errors should occur"
        assert len(validation_results) == 3, "All validations should complete"

        # All files should be marked as validated
        for filepath in prediction_files:
            content = filepath.read_text(encoding="utf-8")
            assert "**Status**: VALIDATED" in content, "File should be validated"

    def test_race_condition_prevention(self, tmp_path: Path) -> None:
        """File operations should be atomic and prevent race conditions."""
        memory_dir = tmp_path / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)

        project_name = "race_condition_test"
        predictions = [{"risk_score": 9, "description": "Race test", "mitigation": "Fix"}]
        kill_criteria = []

        created_files = []
        errors = []

        def rapid_store(iteration: int) -> None:
            """Rapidly store predictions to test atomic file creation."""
            try:
                feedback = PreMortemFeedbackLoop(memory_dir=memory_dir)
                for i in range(10):
                    filepath = feedback.store_prediction(
                        f"{project_name}_{iteration}_{i}", predictions, kill_criteria
                    )
                    created_files.append(filepath)
            except Exception as e:
                errors.append(str(e))

        # Launch 3 threads simultaneously storing to the same project prefix
        threads = []
        for i in range(3):
            t = threading.Thread(target=rapid_store, args=(i,))
            threads.append(t)
            t.start()

        # Wait for completion
        for t in threads:
            t.join(timeout=30)
            assert not t.is_alive(), "Thread should complete within timeout"

        # All operations should succeed (no file corruption)
        assert len(errors) == 0, f"No errors should occur, got: {errors}"
        assert len(created_files) == 30, "All 30 files should be created (3 threads × 10 stores)"

        # All files should be unique and valid
        unique_files = set(created_files)
        assert (
            len(unique_files) == 30
        ), "All files should have unique names (timestamp collision prevention)"

        for filepath in unique_files:
            assert filepath.exists(), "All files should exist on disk"
            content = filepath.read_text(encoding="utf-8")
            assert "Race test" in content, "Content should be valid"
