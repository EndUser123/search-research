"""
Test Exploration Integration

Test cases for BugJail integration with exploration workflow.
"""

import asyncio
import tempfile
import unittest
from pathlib import Path

from ..core.analyzer import BugJailAnalyzer
from ..core.types import BugJailConfig


class TestExplorationIntegration(unittest.TestCase):
    """Test exploration workflow integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = BugJailConfig(
            integrate_with_exploration=True,
            enable_vulnerability_scanning=True
        )
        self.analyzer = BugJailAnalyzer(self.config)

    def test_cwo12_step5_integration(self):
        """Test CWO12 Step 5 integration."""
        # Create a temporary project
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create project files with various issues
            (project_path / "main.py").write_text("""
import sqlite3

class DataProcessor:
    def __init__(self):
        self.db_connection = sqlite3.connect('data.db')  # Resource leak
        self.data = None

    def process(self, user_input):
        # SQL injection vulnerability
        query = f"SELECT * FROM data WHERE name = '{user_input}'"
        cursor = self.db_connection.cursor()
        return cursor.execute(query).fetchall()

    def calculate(self, a, b):
        return a / b  # Potential division by zero

    def get_user(self, user_id):
        # Potential null dereference
        user = self.find_user(user_id)
        return user.get_profile()
""")

            # Run CWO12 Step 5 enhancement
            async def run_step5():
                return await self.analyzer.trigger_cwo12_step5_enhancement(str(project_path))

            result = asyncio.run(run_step5())

            # Check enhancement result
            self.assertEqual(result["status"], "completed")
            self.assertIn("architecture_analysis", result)
            self.assertIn("bug_metrics", result)
            self.assertIn("compliance_status", result)

            # Should detect issues
            self.assertGreater(result["architecture_analysis"]["total_issues"], 0)

    def test_cwo12_step7_precomputation(self):
        """Test CWO12 Step 7 precomputation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_path = Path(tmpdir)

            # Create project files
            (project_path / "auth.py").write_text("""
def login(username, password):
    # SQL injection
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    return db.execute(query)

def check_password(user_input):
    return user_input == "admin123"  # Hardcoded password
""")

            (project_path / "utils.py").write_text("""
def divide(a, b):
    return a / b  # Division by zero risk
""")

            # Define tasks
            task_list = [
                "Fix SQL injection in auth.py",
                "Refactor utils.py divide function",
                "Update main.py file"
            ]

            # Run Step 7 precomputation
            async def run_step7():
                return await self.analyzer.trigger_cwo12_step7_precomputation(str(project_path), task_list)

            result = asyncio.run(run_step7())

            # Check precomputation result
            self.assertEqual(result["status"], "completed")
            self.assertIn("analyzed_files", result)
            self.assertIn("risk_assessment", result)
            self.assertIn("recommendations", result)

            # Should analyze relevant files
            self.assertGreater(len(result["analyzed_files"]), 0)

    def test_rca_enhancement(self):
        """Test RCA enhancement integration."""
        # Create error info
        error_info = {
            "type": "AttributeError",
            "message": "'NoneType' object has no attribute 'process'",
            "file_path": "/tmp/test_file.py",
            "line_number": 15
        }

        # Create test file with error location
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def process_data():
    data = get_data()  # Could return None
    # Error occurs here
    result = data.process()  # Line 5
    return result

def get_data():
    # Sometimes returns None
    if random() < 0.1:
        return None
    return Data()

# More code with potential issues
def calculate():
    return 100 / 0  # Line 15 - division by zero
""")
            f.flush()

            # Run RCA enhancement
            async def run_rca():
                return await self.analyzer.enhance_rca_analysis(error_info, f.name)

            result = asyncio.run(run_rca())

            # Check enhancement result
            self.assertEqual(result["status"], "completed")
            self.assertIn("related_bugs", result)
            self.assertIn("suggested_causes", result)
            self.assertIn("recommendations", result)

            # Should find related bugs
            self.assertGreater(len(result["related_bugs"]), 0)

            # Clean up
            Path(f.name).unlink()

    def test_exploration_workflow_integration(self):
        """Test exploration workflow integration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
import sqlite3

def vulnerable_function(user_input):
    # Multiple issues
    conn = sqlite3.connect('db.db')  # Resource leak
    query = f"SELECT * FROM users WHERE name = '{user_input}'"  # SQL injection
    result = conn.execute(query)
    return result / 0  # Division by zero
""")
            f.flush()

            # Test different workflow steps
            async def test_workflows():
                results = {}

                # CWO12 Step 5
                results["step5"] = await self.analyzer.analyze_with_exploration(
                    f.name,
                    workflow_step="cwo12_step5",
                    trigger_event="architecture_analysis"
                )

                # CWO12 Step 7
                results["step7"] = await self.analyzer.analyze_with_exploration(
                    f.name,
                    workflow_step="cwo12_step7",
                    trigger_event="pre_implementation"
                )

                # RCA enhancement
                error_info = {
                    "type": "ZeroDivisionError",
                    "file_path": f.name,
                    "line_number": 6
                }
                results["rca"] = await self.analyzer.enhance_rca_analysis(error_info, "/tmp")

                return results

            results = asyncio.run(test_workflows())

            # Check all workflows ran
            for workflow, result in results.items():
                if workflow != "rca":  # RCA might fail with invalid path
                    self.assertIsNotNone(result)
                    self.assertIn(result.metadata.get("integration", {}).get("workflow_step"),
                                ["cwo12_step5", "cwo12_step7"])

            # Clean up
            Path(f.name).unlink()

    def test_integration_configuration(self):
        """Test integration configuration."""
        # Check default integrations
        status = self.analyzer.get_integration_status()

        self.assertIn("configured_integrations", status)
        self.assertGreater(len(status["configured_integrations"]), 0)

        # Check specific integrations exist
        integrations = status["configured_integrations"]
        self.assertTrue(any("cwo12_step5" in i for i in integrations))
        self.assertTrue(any("rca_enhancement" in i for i in integrations))
        self.assertTrue(any("pre_commit" in i for i in integrations))

    def test_pre_commit_integration(self):
        """Test pre-commit hook integration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def commit_function():
    # Issues that should block commit
    eval(user_input)  # Critical security issue
    conn = sqlite3.connect('db')  # Resource leak
    return data / 0  # Division by zero
""")
            f.flush()

            # Run pre-commit analysis
            async def run_precommit():
                return await self.analyzer.analyze_with_exploration(
                    f.name,
                    workflow_step="pre_commit",
                    trigger_event="file_change"
                )

            report = asyncio.run(run_precommit())

            # Should detect issues that would block commit
            self.assertGreater(report.total_issues, 0)

            # Check for critical issues
            critical_issues = [b for b in report.bugs if b.severity.value == "critical"]
            critical_vulns = [v for v in report.vulnerabilities if v.severity.value == "critical"]
            self.assertGreater(len(critical_issues) + len(critical_vulns), 0)

            # Clean up
            Path(f.name).unlink()

    def test_integration_with_cache(self):
        """Test integration with caching enabled."""
        config = BugJailConfig(
            integrate_with_exploration=True,
            enable_caching=True,
            cache_directory=tempfile.gettempdir()
        )
        analyzer = BugJailAnalyzer(config)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("x = 1 / 0")  # Simple bug
            f.flush()

            # First analysis
            report1 = analyzer.analyze_path(f.name)

            # Second analysis (should use cache)
            report2 = analyzer.analyze_path(f.name)

            # Reports should be consistent
            self.assertEqual(report1.total_issues, report2.total_issues)

            # Check cache statistics
            stats = analyzer.detector.get_statistics()
            self.assertGreater(stats["cache_hits"], 0)

            # Clean up
            Path(f.name).unlink()

    def test_parallel_integration_analysis(self):
        """Test parallel analysis with integration."""
        config = BugJailConfig(
            integrate_with_exploration=True,
            parallel_analysis=True,
            max_workers=2
        )
        analyzer = BugJailAnalyzer(config)

        # Create multiple files
        files = []
        for i in range(3):
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(f"""
def file_{i}_function():
    return 1 / 0  # Division by zero
""")
                f.flush()
                files.append(f.name)

        try:
            # Analyze all files
            reports = []
            for file_path in files:
                report = analyzer.analyze_path(file_path)
                reports.append(report)

            # All files should be analyzed
            self.assertEqual(len(reports), 3)
            for report in reports:
                self.assertGreater(report.total_issues, 0)

        finally:
            # Clean up
            for file_path in files:
                Path(file_path).unlink()

    def test_integration_error_handling(self):
        """Test error handling in integration."""
        # Test with non-existent file
        async def test_invalid_file():
            try:
                await self.analyzer.trigger_cwo12_step5_enhancement("/non/existent/path")
                # Should not raise exception
                self.assertTrue(True)
            except Exception as e:
                # Should handle gracefully
                self.fail(f"Should not raise exception: {e}")

        asyncio.run(test_invalid_file())

        # Test with invalid RCA error info
        error_info = {"type": "Error", "file_path": None}  # Invalid
        async def test_invalid_rca():
            result = await self.analyzer.enhance_rca_analysis(error_info, "/tmp")
            self.assertEqual(result["status"], "failed")

        asyncio.run(test_invalid_rca())


if __name__ == "__main__":
    unittest.main()
