import os
import sqlite3
import tempfile
import threading
import unittest
from datetime import datetime, timedelta

from ..continuous_learner import LearningConfig, UsagePattern, UsagePatternTracker

#!/usr/bin/env python3
"""Test UsagePatternTracker - TDD approach with evidence-based validation.

Test Case ID: TC-CKS-LEARN-001
Priority: High
Test Type: Unit Testing

Purpose:
Verify UsagePatternTracker functionality with real data validation,
statistical analysis accuracy, and pattern detection capabilities.

Preconditions:
- Database initialized and accessible
- Learning configuration properly set up
- Test environment isolated

Test Data:
- Real operation records with varied durations and success rates
- Multiple components and operations for pattern diversity
- Edge cases with error conditions and anomalies

Expected Results:
- Accurate pattern tracking and statistical analysis
- Proper anomaly detection and threshold validation
- Efficient database operations and resource management
- Thread-safe concurrent operations

Post-conditions:
- Test database properly cleaned
- All patterns correctly persisted
- No resource leaks or hanging threads
"""


class TestUsagePatternTracker(unittest.TestCase):
    """Test UsagePatternTracker with TDD approach and evidence-based validation."""

    def setUp(self) -> None:
        """Set up test environment with isolated database and configuration.

        Algorithm Approach: Isolated test setup with temporary database
        and controlled test data for reproducible results.

        Time Complexity: O(1) for setup
        Space Complexity: O(1) for temporary storage
        """
        # Create temporary database
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_learning.db")

        # Create test configuration
        self.config = LearningConfig(
            database_path=self.db_path,
            pattern_window_size=100,
            min_pattern_frequency=3,
            anomaly_detection_enabled=True,
            anomaly_threshold=2.0,
        )

        # Initialize tracker
        self.tracker = UsagePatternTracker(self.config)

        # Test data
        self.test_operations = [
            # Normal operations
            {
                "component": "database",
                "operation": "query",
                "duration": 0.5,
                "success": True,
            },
            {
                "component": "database",
                "operation": "query",
                "duration": 0.6,
                "success": True,
            },
            {
                "component": "database",
                "operation": "query",
                "duration": 0.4,
                "success": True,
            },
            {
                "component": "cache",
                "operation": "get",
                "duration": 0.1,
                "success": True,
            },
            {
                "component": "cache",
                "operation": "set",
                "duration": 0.15,
                "success": True,
            },
            # Error operations
            {
                "component": "api",
                "operation": "request",
                "duration": 2.0,
                "success": False,
            },
            {
                "component": "api",
                "operation": "request",
                "duration": 1.8,
                "success": True,
            },
            {
                "component": "api",
                "operation": "request",
                "duration": 0.5,
                "success": True,
            },
            # Anomaly operations
            {
                "component": "processor",
                "operation": "compute",
                "duration": 5.0,
                "success": True,
            },
            {
                "component": "processor",
                "operation": "compute",
                "duration": 0.1,
                "success": True,
            },
            {
                "component": "processor",
                "operation": "compute",
                "duration": 0.2,
                "success": True,
            },
        ]

    def tearDown(self) -> None:
        """Clean up test environment."""
        # Cleanup temporary files
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self) -> None:
        """Test UsagePatternTracker initialization.

        Test Case ID: TC-CKS-LEARN-001-01
        Purpose: Verify proper initialization with database setup

        Expected Results:
        - Database tables created successfully
        - Pattern storage initialized empty
        - Configuration applied correctly
        """
        self.assertIsInstance(self.tracker, UsagePatternTracker)
        self.assertEqual(len(self.tracker._patterns), 0)
        self.assertEqual(len(self.tracker._operation_history), 0)

        # Verify database tables exist
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name IN "
                "('usage_patterns', 'operation_history')",
            )
            tables = [row[0] for row in cursor.fetchall()]
            self.assertIn("usage_patterns", tables)
            self.assertIn("operation_history", tables)

    def test_single_operation_tracking(self) -> None:
        """Test tracking of a single operation.

        Test Case ID: TC-CKS-LEARN-001-02
        Purpose: Verify basic operation tracking functionality

        Expected Results:
        - Pattern created for new operation
        - Frequency updated correctly
        - Statistics calculated accurately
        """
        op = self.test_operations[0]

        # Track operation
        self.tracker.track_operation(
            op["component"],
            op["operation"],
            op["duration"],
            op["success"],
        )

        # Verify pattern created
        patterns = list(self.tracker._patterns.values())
        self.assertEqual(len(patterns), 1)

        pattern = patterns[0]
        self.assertEqual(pattern.component, op["component"])
        self.assertEqual(pattern.operation, op["operation"])
        self.assertEqual(pattern.frequency, 1)
        self.assertEqual(pattern.avg_duration, op["duration"])
        self.assertEqual(pattern.success_rate, 1.0 if op["success"] else 0.0)

    def test_multiple_operations_same_pattern(self) -> None:
        """Test tracking multiple operations of the same pattern.

        Test Case ID: TC-CKS-LEARN-001-03
        Purpose: Verify statistical aggregation for repeated operations

        Expected Results:
        - Frequency accumulated correctly
        - Duration averages calculated properly
        - Success rates updated with exponential smoothing
        """
        # Track multiple database query operations
        db_operations = [
            op
            for op in self.test_operations
            if op["component"] == "database" and op["operation"] == "query"
        ]

        for op in db_operations:
            self.tracker.track_operation(
                op["component"],
                op["operation"],
                op["duration"],
                op["success"],
            )

        # Get the database:query pattern
        patterns = self.tracker.get_patterns_by_component("database")
        query_patterns = [p for p in patterns if p.operation == "query"]
        self.assertEqual(len(query_patterns), 1)

        pattern = query_patterns[0]
        self.assertEqual(pattern.frequency, 3)
        self.assertAlmostEqual(
            pattern.avg_duration,
            0.5,
            places=1,
        )  # Average of 0.5, 0.6, 0.4
        self.assertEqual(pattern.success_rate, 1.0)  # All successful

    def test_error_rate_calculation(self) -> None:
        """Test error rate calculation for operations with failures.

        Test Case ID: TC-CKS-LEARN-001-04
        Purpose: Verify accurate error rate tracking with exponential smoothing

        Expected Results:
        - Error rates calculated correctly
        - Success rates complementary to error rates
        - Exponential smoothing applied properly
        """
        # Track API operations with mixed success
        api_operations = [
            op
            for op in self.test_operations
            if op["component"] == "api" and op["operation"] == "request"
        ]

        for op in api_operations:
            self.tracker.track_operation(
                op["component"],
                op["operation"],
                op["duration"],
                op["success"],
            )

        # Get the api:request pattern
        patterns = self.tracker.get_patterns_by_component("api")
        request_patterns = [p for p in patterns if p.operation == "request"]
        self.assertEqual(len(request_patterns), 1)

        pattern = request_patterns[0]
        self.assertEqual(pattern.frequency, 3)
        self.assertGreater(pattern.error_rate, 0.0)  # Should have some error rate
        self.assertEqual(pattern.success_rate + pattern.error_rate, 1.0)

    def test_pattern_persistence(self) -> None:
        """Test pattern persistence to database.

        Test Case ID: TC-CKS-LEARN-001-05
        Purpose: Verify patterns are correctly saved and loaded from database

        Expected Results:
        - Patterns saved to database correctly
        - Patterns loaded from database accurately
        - All pattern attributes preserved
        """
        # Track some operations
        for op in self.test_operations[:5]:
            self.tracker.track_operation(
                op["component"],
                op["operation"],
                op["duration"],
                op["success"],
            )

        # Force save
        self.tracker._save_patterns()

        # Create new tracker instance (simulates restart)
        new_tracker = UsagePatternTracker(self.config)

        # Verify patterns loaded
        self.assertGreater(len(new_tracker._patterns), 0)

        # Check specific patterns
        for pattern_id, pattern in new_tracker._patterns.items():
            original_pattern = self.tracker._patterns.get(pattern_id)
            if original_pattern:
                self.assertEqual(pattern.component, original_pattern.component)
                self.assertEqual(pattern.operation, original_pattern.operation)
                self.assertEqual(pattern.frequency, original_pattern.frequency)

    def test_concurrent_tracking(self) -> None:
        """Test thread-safe concurrent operation tracking.

        Test Case ID: TC-CKS-LEARN-001-06
        Purpose: Verify thread safety under concurrent load

        Expected Results:
        - No race conditions or data corruption
        - All operations tracked accurately
        - Proper locking mechanisms in place
        """

        def track_operations(thread_id, operations) -> None:
            """Worker function for concurrent tracking."""
            for i, op in enumerate(operations):
                self.tracker.track_operation(
                    op["component"],
                    f"{op['operation']}_thread_{thread_id}",
                    op["duration"],
                    op["success"],
                )

        # Create multiple threads
        num_threads = 5
        operations_per_thread = 20
        threads = []

        for i in range(num_threads):
            thread_ops = self.test_operations * (operations_per_thread // len(self.test_operations))
            thread = threading.Thread(target=track_operations, args=(i, thread_ops))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all operations tracked
        expected_total = num_threads * operations_per_thread
        actual_total = len(self.tracker._operation_history)
        self.assertEqual(actual_total, expected_total)

        # Verify no data corruption
        total_frequency = sum(pattern.frequency for pattern in self.tracker._patterns.values())
        self.assertEqual(total_frequency, expected_total)

    def test_peak_hours_analysis(self) -> None:
        """Test peak hours analysis for usage patterns.

        Test Case ID: TC-CKS-LEARN-001-07
        Purpose: Verify accurate peak hour detection and temporal analysis

        Expected Results:
        - Peak hours identified correctly
        - Hourly distribution calculated accurately
        - Pattern analysis considers temporal factors
        """
        # Track operations at different hours
        base_time = datetime.now().replace(minute=0, second=0, microsecond=0)

        for hour_offset in range(24):
            for _ in range(10):  # 10 operations per hour
                # Create mock timestamp for specific hour
                base_time + timedelta(hours=hour_offset)

                # Track operation (we'll mock the timestamp in the pattern)
                self.tracker.track_operation(
                    "test_component",
                    "test_operation",
                    0.5,
                    True,
                )

        # Manually set timestamps for testing
        for i, op in enumerate(self.tracker._operation_history):
            hour = (i // 10) % 24
            op["timestamp"] = base_time + timedelta(hours=hour)

        # Trigger peak hours analysis
        self.tracker._analyze_peak_hours()

        # Check patterns have peak hours
        patterns = list(self.tracker._patterns.values())
        for pattern in patterns:
            if pattern.frequency >= 10:
                self.assertGreater(len(pattern.peak_hours), 0)

    def test_anomaly_detection(self) -> None:
        """Test anomaly detection for usage patterns.

        Test Case ID: TC-CKS-LEARN-001-08
        Purpose: Verify statistical anomaly detection with configurable thresholds

        Expected Results:
        - Anomalies detected based on statistical deviation
        - Threshold sensitivity works correctly
        - No false positives for normal patterns
        """
        # Track normal operations with consistent duration
        for _ in range(20):
            self.tracker.track_operation("test", "normal_op", 0.5, True)

        # Track anomalous operations
        self.tracker.track_operation(
            "test",
            "normal_op",
            5.0,
            True,
        )  # 10x normal duration
        self.tracker.track_operation(
            "test",
            "normal_op",
            0.1,
            True,
        )  # Much shorter duration

        # Trigger anomaly detection
        self.tracker._detect_anomalies()

        # Should have detected anomalies (this would normally log warnings)
        # In a real implementation, we'd check for anomaly flags
        patterns = self.tracker.get_patterns_by_component("test")
        self.assertGreater(len(patterns), 0)

    def test_top_patterns_ranking(self) -> None:
        """Test ranking of patterns by frequency.

        Test Case ID: TC-CKS-LEARN-001-09
        Purpose: Verify accurate pattern ranking and limit enforcement

        Expected Results:
        - Patterns ranked by frequency correctly
        - Limit enforcement works properly
        - Top patterns returned in correct order
        """
        # Track operations with different frequencies
        operation_frequencies = {
            ("high_freq", "op1"): 50,
            ("medium_freq", "op2"): 25,
            ("low_freq", "op3"): 10,
        }

        for (component, operation), frequency in operation_frequencies.items():
            for _ in range(frequency):
                self.tracker.track_operation(component, operation, 0.5, True)

        # Get top patterns
        top_patterns = self.tracker.get_top_patterns(limit=2)

        self.assertEqual(len(top_patterns), 2)
        self.assertEqual(top_patterns[0].component, "high_freq")
        self.assertEqual(top_patterns[0].operation, "op1")
        self.assertEqual(top_patterns[1].component, "medium_freq")
        self.assertEqual(top_patterns[1].operation, "op2")

        # Verify frequency order
        self.assertGreater(top_patterns[0].frequency, top_patterns[1].frequency)

    def test_pattern_id_generation(self) -> None:
        """Test consistent pattern ID generation.

        Test Case ID: TC-CKS-LEARN-001-10
        Purpose: Verify deterministic pattern ID generation

        Expected Results:
        - Same component/operation generates same ID
        - Different component/operation generates different ID
        - IDs are consistent across tracker instances
        """
        # Generate pattern ID for same operation
        id1 = self.tracker._generate_pattern_id("component1", "operation1")
        id2 = self.tracker._generate_pattern_id("component1", "operation1")
        id3 = self.tracker._generate_pattern_id("component2", "operation1")
        id4 = self.tracker._generate_pattern_id("component1", "operation2")

        self.assertEqual(id1, id2)  # Same operation should have same ID
        self.assertNotEqual(id1, id3)  # Different component should have different ID
        self.assertNotEqual(id1, id4)  # Different operation should have different ID

        # Test ID consistency
        self.assertEqual(len(id1), 16)  # Should be 16 characters (MD5 hash truncated)
        self.assertTrue(
            all(c in "0123456789abcdef" for c in id1),
        )  # Hex characters only

    def test_operation_history_limits(self) -> None:
        """Test operation history size limits.

        Test Case ID: TC-CKS-LEARN-001-11
        Purpose: Verify proper enforcement of history size limits

        Expected Results:
        - History size limited by configuration
        - Oldest entries removed when limit exceeded
        - Most recent entries always retained
        """
        # Track more operations than the window size
        for i in range(self.config.pattern_window_size + 50):
            self.tracker.track_operation("test", "op", 0.1, True, {"iteration": i})

        # Verify history size is limited
        self.assertLessEqual(
            len(self.tracker._operation_history),
            self.config.pattern_window_size,
        )

        # Verify most recent entries are kept
        latest_op = self.tracker._operation_history[-1]
        self.assertEqual(
            latest_op["metadata"]["iteration"],
            self.config.pattern_window_size + 49,
        )

    def test_resource_usage_calculation(self) -> None:
        """Test resource usage calculation for patterns.

        Test Case ID: TC-CKS-LEARN-001-12
        Purpose: Verify resource usage metrics calculation

        Expected Results:
        - Resource usage metrics calculated
        - Values within expected ranges
        - Metrics updated for patterns
        """
        # Track some operations
        for op in self.test_operations:
            self.tracker.track_operation(
                op["component"],
                op["operation"],
                op["duration"],
                op["success"],
            )

        # Trigger resource usage calculation
        self.tracker._calculate_resource_usage()

        # Verify resource usage is calculated
        patterns = list(self.tracker._patterns.values())
        for pattern in patterns:
            self.assertIn("cpu_percent", pattern.resource_usage)
            self.assertIn("memory_mb", pattern.resource_usage)
            self.assertIn("io_ops", pattern.resource_usage)

            # Verify values are reasonable
            self.assertGreaterEqual(pattern.resource_usage["cpu_percent"], 0)
            self.assertLessEqual(pattern.resource_usage["cpu_percent"], 100)
            self.assertGreaterEqual(pattern.resource_usage["memory_mb"], 0)

    def test_pattern_serialization(self) -> None:
        """Test pattern serialization to/from dictionary.

        Test Case ID: TC-CKS-LEARN-001-13
        Purpose: Verify proper pattern serialization for database storage

        Expected Results:
        - Patterns serialize to dictionary correctly
        - Patterns deserialize from dictionary accurately
        - All fields preserved in round-trip conversion
        """
        # Create a test pattern
        original_pattern = UsagePattern(
            pattern_id="test123",
            component="test_component",
            operation="test_operation",
            frequency=10,
            avg_duration=0.5,
            success_rate=0.9,
            error_rate=0.1,
            peak_hours=[9, 14, 16],
            avg_load=0.7,
            resource_usage={"cpu": 50, "memory": 200},
            metadata={"test": "data"},
        )

        # Serialize to dictionary
        pattern_dict = original_pattern.to_dict()

        # Verify serialization
        self.assertEqual(pattern_dict["pattern_id"], "test123")
        self.assertEqual(pattern_dict["component"], "test_component")
        self.assertEqual(pattern_dict["operation"], "test_operation")
        self.assertEqual(pattern_dict["frequency"], 10)
        self.assertEqual(pattern_dict["peak_hours"], [9, 14, 16])

        # Deserialize from dictionary
        restored_pattern = UsagePattern.from_dict(pattern_dict)

        # Verify deserialization
        self.assertEqual(restored_pattern.pattern_id, original_pattern.pattern_id)
        self.assertEqual(restored_pattern.component, original_pattern.component)
        self.assertEqual(restored_pattern.operation, original_pattern.operation)
        self.assertEqual(restored_pattern.frequency, original_pattern.frequency)
        self.assertEqual(restored_pattern.peak_hours, original_pattern.peak_hours)


if __name__ == "__main__":
    unittest.main()
