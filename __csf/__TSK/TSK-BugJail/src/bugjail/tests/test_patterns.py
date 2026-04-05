"""
Test Bug Detection Patterns

Comprehensive test cases for bug detection patterns.
"""

import tempfile
import unittest
from pathlib import Path

from ..core.detector import BugJailDetector
from ..core.types import BugCategory, BugJailConfig, BugSeverity


class TestBugPatterns(unittest.TestCase):
    """Test bug detection patterns."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = BugJailConfig()
        self.detector = BugJailDetector(self.config)

    def test_null_pointer_detection(self):
        """Test null pointer bug detection."""
        code = """
def process_data(data):
    # Missing null check
    result = data.process()
    return result

def main():
    user_data = get_user()  # Could return None
    process_data(user_data)
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()

            report = self.detector.analyze_path(f.name)

            # Should detect potential null pointer
            null_pointer_bugs = [b for b in report.bugs if b.type == BugCategory.NULL_POINTER]
            self.assertGreater(len(null_pointer_bugs), 0)

            # Clean up
            Path(f.name).unlink()

    def test_resource_leak_detection(self):
        """Test resource leak detection."""
        code = """
def read_config():
    # File without context manager
    file = open('config.json', 'r')
    data = file.read()
    # Missing file.close()
    return data

def read_database():
    # Database connection without proper cleanup
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    return cursor.fetchall()
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()

            report = self.detector.analyze_path(f.name)

            # Should detect resource leaks
            resource_leaks = [b for b in report.bugs if b.type == BugCategory.RESOURCE_LEAK]
            self.assertGreater(len(resource_leaks), 0)

            # Clean up
            Path(f.name).unlink()

    def test_division_by_zero_detection(self):
        """Test division by zero detection."""
        code = """
def calculate_average(total, count):
    return total / count  # Potential division by zero

def process_numbers(numbers):
    result = 0
    for num in numbers:
        result = result / 0  # Definite division by zero
    return result
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()

            report = self.detector.analyze_path(f.name)

            # Should detect division by zero
            division_bugs = [b for b in report.bugs if b.type == BugCategory.DIVISION_BY_ZERO]
            self.assertGreater(len(division_bugs), 0)

            # Clean up
            Path(f.name).unlink()

    def test_race_condition_detection(self):
        """Test race condition detection."""
        code = """
import threading

class Counter:
    def __init__(self):
        self.value = 0

    def increment(self):
        # Non-atomic increment
        self.value = self.value + 1

    def check_and_set(self, new_value):
        # Check-then-act pattern
        if self.value < 100:
            self.value = new_value

# Global counter without synchronization
global_counter = 0
def update_counter():
    global global_counter
    global_counter += 1
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()

            report = self.detector.analyze_path(f.name)

            # Should detect race conditions
            race_conditions = [b for b in report.bugs if b.type == BugCategory.RACE_CONDITION]
            self.assertGreater(len(race_conditions), 0)

            # Clean up
            Path(f.name).unlink()

    def test_api_misuse_detection(self):
        """Test API misuse detection."""
        code = """
def process_user_input(user_input):
    # Dangerous use of eval
    result = eval(user_input)
    return result

def execute_command(command):
    # exec with user input
    exec(f"import os; os.system('{command}')")
    return True

def run_subprocess(cmd):
    # subprocess with shell=True (security risk)
    import subprocess
    result = subprocess.run(cmd, shell=True)
    return result

def check_condition(value):
    # Assignment in condition
    if value = None:
        return False
    return True
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()

            report = self.detector.analyze_path(f.name)

            # Should detect API misuse
            api_misuse = [b for b in report.bugs if b.type == BugCategory.API_MISUSE]
            self.assertGreater(len(api_misuse), 0)

            # Clean up
            Path(f.name).unlink()

    def test_javascript_patterns(self):
        """Test JavaScript bug detection patterns."""
        code = """
function processUser(user) {
    // Potential null dereference
    return user.name.toUpperCase();
}

function checkValue(value) {
    // Using == instead of ===
    if (value == null) {
        return false;
    }
    return true;
}

function calculateResult(a, b) {
    // Division without zero check
    return a / b;
}

// Global variable leak
function leakGlobal() {
    leaked = "This becomes global";
}

// Dangerous eval
function processInput(input) {
    return eval(input);
}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            f.flush()

            report = self.detector.analyze_path(f.name)

            # Should detect various issues
            self.assertGreater(report.total_issues, 0)

            # Clean up
            Path(f.name).unlink()

    def test_multiple_files_analysis(self):
        """Test analysis of multiple files."""
        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create multiple Python files
            files = {
                "main.py": """
def main():
    data = get_data()
    processed = data.process()  # Potential null pointer
    return processed
""",
                "utils.py": """
def open_config():
    file = open('config.json')  # Resource leak
    return file.read()
""",
                "math.py": """
def divide(a, b):
    return a / b  # Potential division by zero
"""
            }

            for filename, content in files.items():
                (tmpdir_path / filename).write_text(content)

            # Analyze directory
            report = self.detector.analyze_path(tmpdir)

            # Should detect issues across all files
            self.assertEqual(len(report.files_analyzed), 3)
            self.assertGreater(report.total_issues, 0)

    def test_severity_filtering(self):
        """Test severity filtering configuration."""
        # Configure to only detect HIGH and CRITICAL issues
        config = BugJailConfig(
            min_severity_level=BugSeverity.HIGH,
            include_info_level=False
        )
        detector = BugJailDetector(config)

        code = """
def process(data):
    # Critical: Division by zero
    result = 100 / 0

    # High: Resource leak
    file = open('test.txt')

    # Medium: Logic error
    if True:
        return True
    return False

    # Low: Style issue
    x=1+2

    return result
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()

            report = detector.analyze_path(f.name)

            # Should only include HIGH and CRITICAL issues
            for bug in report.bugs:
                self.assertIn(bug.severity, [BugSeverity.HIGH, BugSeverity.CRITICAL])

            # Clean up
            Path(f.name).unlink()

    def test_exclude_patterns(self):
        """Test file exclusion patterns."""
        config = BugJailConfig(
            exclude_patterns=["**/test_*.py", "**/*_test.py"]
        )
        detector = BugJailDetector(config)

        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create main file and test file
            (tmpdir_path / "main.py").write_text("x = 1 / 0")
            (tmpdir_path / "test_main.py").write_text("y = 2 / 0")

            # Analyze directory
            report = detector.analyze_path(tmpdir)

            # Should only analyze main.py, not test_main.py
            self.assertIn("main.py", [Path(f).name for f in report.files_analyzed])
            self.assertNotIn("test_main.py", [Path(f).name for f in report.files_analyzed])

    def test_confidence_scoring(self):
        """Test confidence scoring for detections."""
        code = """
def process():
    # High confidence: Definite division by zero
    result = 42 / 0

    # Medium confidence: Potential null pointer
    user = get_user()
    name = user.name

    return result
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            f.flush()

            report = self.detector.analyze_path(f.name)

            # Check confidence scores
            for bug in report.bugs:
                self.assertGreaterEqual(bug.confidence, 0.0)
                self.assertLessEqual(bug.confidence, 1.0)

            # Division by zero should have high confidence
            division_bugs = [b for b in report.bugs if b.type == BugCategory.DIVISION_BY_ZERO]
            if division_bugs:
                self.assertGreater(division_bugs[0].confidence, 0.8)

            # Clean up
            Path(f.name).unlink()

    def test_custom_patterns(self):
        """Test custom bug detection patterns."""
        config = BugJailConfig(
            enable_custom_patterns=True,
            custom_pattern_paths=["custom_patterns.json"]
        )

        # This would test custom pattern loading
        # For now, just ensure config is properly set
        self.assertEqual(config.custom_pattern_paths, ["custom_patterns.json"])
        self.assertTrue(config.enable_custom_patterns)


if __name__ == "__main__":
    unittest.main()
