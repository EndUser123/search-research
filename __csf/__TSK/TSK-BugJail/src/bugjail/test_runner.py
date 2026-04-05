"""
BugJail Test Runner

Simple test runner for validating BugJail functionality.
"""

import sys
import tempfile
import unittest
from pathlib import Path

# Add the bugjail module to the path
sys.path.insert(0, str(Path(__file__).parent))

def create_test_code():
    """Create test code with various bugs and vulnerabilities."""
    test_code = '''
import sqlite3
import os

def vulnerable_function(user_input):
    # SQL Injection vulnerability
    conn = sqlite3.connect('database.db')
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    return conn.execute(query).fetchall()

def resource_leak():
    # Resource without cleanup
    file = open('data.txt', 'r')
    return file.read()

def division_by_zero(a, b):
    # Potential division by zero
    return a / b

def null_pointer_issue():
    # Potential null dereference
    data = get_data()
    return data.process()

def hard_coded_secret():
    # Hardcoded password
    password = "admin123"
    return password

def eval_usage(user_input):
    # Dangerous eval usage
    return eval(user_input)

def get_data():
    # Could return None
    return None
'''
    return test_code

def run_basic_test():
    """Run a basic test of BugJail functionality."""
    print("Running BugJail Basic Test...")

    try:
        from bugjail import BugJailConfig, BugJailDetector

        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(create_test_code())
            f.flush()
            test_file = f.name

        # Test detection
        config = BugJailConfig(
            enable_vulnerability_scanning=True,
            enable_constitutional_compliance=True
        )
        detector = BugJailDetector(config)

        print(f"  Analyzing {test_file}...")
        report = detector.analyze_path(test_file)

        # Check results
        print(f"  Analysis complete in {report.duration_seconds:.2f} seconds")
        print(f"  Total issues found: {report.total_issues}")
        print(f"  Bugs: {len(report.bugs)}")
        print(f"  Vulnerabilities: {len(report.vulnerabilities)}")
        print(f"  Recommendations: {len(report.recommendations)}")
        print(f"  Compliance level: {report.constitutional_compliance.value}")

        # Clean up
        Path(test_file).unlink()

        # Verify detection worked
        if report.total_issues > 0:
            print("  ✓ Bug detection working")
        else:
            print("  ✗ No issues detected (unexpected)")

        if report.vulnerabilities:
            print("  ✓ Vulnerability scanning working")
        else:
            print("  ✗ No vulnerabilities detected (unexpected)")

        if report.compliance_level.value != "compliant":
            print("  ✓ Constitutional compliance validation working")
        else:
            print("  ✗ No compliance violations detected (unexpected)")

        return report.total_issues > 0

    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_pattern_library_test():
    """Test pattern library functionality."""
    print("\nRunning Pattern Library Test...")

    try:
        from bugjail.patterns.library import PatternLibrary

        library = PatternLibrary()
        library.load_builtin_patterns()

        stats = library.get_statistics()
        print(f"  Total patterns: {stats['total_patterns']}")
        print(f"  Languages supported: {list(stats['patterns_by_language'].keys())}")

        if stats['total_patterns'] > 0:
            print("  ✓ Pattern library loaded successfully")
            return True
        else:
            print("  ✗ No patterns loaded")
            return False

    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False

def run_compliance_test():
    """Test constitutional compliance validation."""
    print("\nRunning Constitutional Compliance Test...")

    try:
        from bugjail.compliance.validator import ConstitutionalValidator
        from bugjail.core.types import BugCategory, BugSeverity, DetectionResult

        validator = ConstitutionalValidator()

        # Create test issues
        issues = [
            DetectionResult(
                id="test1",
                type=BugCategory.API_MISUSE,
                severity=BugSeverity.HIGH,  # Should be CRITICAL for eval()
                message="eval() usage",
                description="Use of eval() function",
                file_path="/test.py",
                line_number=10,
                code_snippet="eval(user_input)",
                confidence=0.9
            )
        ]

        result = validator.validate_results(issues, [])

        print(f"  Compliance level: {result.compliance_level.value}")
        print(f"  Violations: {len(result.violations)}")
        print(f"  Warnings: {len(result.warnings)}")

        if result.compliance_level.value != "compliant":
            print("  ✓ Constitutional compliance validation working")
            return True
        else:
            print("  ✗ No compliance violations detected")
            return False

    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False

def run_recommendation_test():
    """Test recommendation engine."""
    print("\nRunning Recommendation Engine Test...")

    try:
        from bugjail.core.types import BugCategory, BugSeverity, DetectionResult
        from bugjail.recommendations.engine import RecommendationEngine

        engine = RecommendationEngine()

        # Create test bug
        bug = DetectionResult(
            id="test1",
            type=BugCategory.NULL_POINTER,
            severity=BugSeverity.HIGH,
            message="Potential null dereference",
            description="Variable accessed without null check",
            file_path="/test.py",
            line_number=10,
            code_snippet="obj.method()",
            confidence=0.8
        )

        recommendations = engine.generate_recommendations([bug])

        print(f"  Generated {len(recommendations)} recommendations")

        if recommendations:
            print(f"  First recommendation: {recommendations[0].title}")
            print("  ✓ Recommendation engine working")
            return True
        else:
            print("  ✗ No recommendations generated")
            return False

    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False

def run_unit_tests():
    """Run the full unit test suite."""
    print("\nRunning Unit Test Suite...")

    try:
        # Discover and run tests
        loader = unittest.TestLoader()
        start_dir = Path(__file__).parent / "tests"
        suite = loader.discover(str(start_dir), pattern="test_*.py")

        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)

        if result.wasSuccessful():
            print("\n✓ All unit tests passed")
            return True
        else:
            print(f"\n✗ {len(result.failures)} test failures, {len(result.errors)} errors")
            return False

    except Exception as e:
        print(f"  ✗ Test suite failed: {e}")
        return False

def main():
    """Run all tests."""
    print("BugJail Test Runner")
    print("=" * 50)

    results = []

    # Run individual tests
    results.append(run_basic_test())
    results.append(run_pattern_library_test())
    results.append(run_compliance_test())
    results.append(run_recommendation_test())

    # Run unit tests
    results.append(run_unit_tests())

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")

    passed = sum(results)
    total = len(results)

    print(f"  Tests passed: {passed}/{total}")

    if passed == total:
        print("  ✓ All tests successful!")
        return 0
    else:
        print("  ✗ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
