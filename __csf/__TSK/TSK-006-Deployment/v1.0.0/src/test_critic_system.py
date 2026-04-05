#!/usr/bin/env python3
"""
Test script for the Critic System

This script tests the functionality of the critic system including
code analysis, architecture evaluation, and the evaluation pipeline.
"""

import sys
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from critic import create_critic
from evaluation import EvaluationConfig, create_evaluation_pipeline


def test_code_critic():
    """Test the code critic functionality."""
    print("\n=== Testing Code Critic ===")

    # Sample code with various issues
    problematic_code = '''
import os

def very_complex_function(param1, param2, param3, param4, param5, param6, param7, param8):
    """A function with too many parameters and high complexity."""
    if param1 > 0:
        if param2 > 0:
            if param3 > 0:
                if param4 > 0:
                    if param5 > 0:
                        if param6 > 0:
                            if param7 > 0:
                                if param8 > 0:
                                    # This is deeply nested
                                    result = param1 + param2 + param3 + param4 + param5 + param6 + param7 + param8
                                    return result
                                else:
                                    return param1 + param2 + param3 + param4 + param5 + param6 + param7
                            else:
                                return param1 + param2 + param3 + param4 + param5 + param6
                        else:
                            return param1 + param2 + param3 + param4 + param5
                    else:
                        return param1 + param2 + param3 + param4
                else:
                    return param1 + param2 + param3
            else:
                return param1 + param2
        else:
            return param1
    else:
        return 0

class EmptyClass:
    pass

class TooManyMethods:
    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
    def method6(self): pass
    def method7(self): pass
    def method8(self): pass
    def method9(self): pass
    def method10(self): pass
    def method11(self): pass
    def method12(self): pass
    def method13(self): pass
    def method14(self): pass
    def method15(self): pass
    def method16(self): pass
    def method17(self): pass
    def method18(self): pass
    def method19(self): pass
    def method20(self): pass
    def method21(self): pass

def insecure_function():
    password = "hardcoded_password_123"
    api_key = "sk-1234567890abcdef"
    os.system(f"echo {password}")
    eval("print('dangerous')")
    return True

# TODO: Fix this function
# FIXME: This is broken
def function_with_issues():
    pass  # Empty function

if True:
    pass  # Empty if block
'''

    critic = create_critic()
    result = critic.evaluate_code(problematic_code, "test_problematic.py")

    print("✓ Code evaluation completed successfully")
    print(f"  Overall Quality Score: {result.quality_score.overall:.1f}/100")
    print(f"  Total Issues: {len(result.issues)}")
    print(f"  Evaluation Time: {result.evaluation_time:.3f}s")

    # Show issues by severity
    issues_by_severity = {}
    for issue in result.issues:
        severity = issue.severity.value
        issues_by_severity[severity] = issues_by_severity.get(severity, 0) + 1

    print("\n  Issues by Severity:")
    for severity, count in sorted(issues_by_severity.items()):
        print(f"    {severity.capitalize()}: {count}")

    # Show top 5 issues
    print("\n  Top 5 Issues:")
    sorted_issues = sorted(result.issues, key=lambda x: x.severity.value, reverse=True)
    for i, issue in enumerate(sorted_issues[:5], 1):
        print(f"    {i}. [{issue.severity.value.upper()}] {issue.title}")
        print(f"       {issue.description}")
        if issue.suggestion:
            print(f"       Suggestion: {issue.suggestion}")
        print()

    # Show recommendations
    print("  Recommendations:")
    for i, rec in enumerate(result.recommendations[:3], 1):
        print(f"    {i}. {rec}")

    return result


def test_evaluation_pipeline():
    """Test the evaluation pipeline functionality."""
    print("\n=== Testing Evaluation Pipeline ===")

    # Create pipeline configuration
    config = EvaluationConfig(
        max_concurrent_evaluations=2,
        cache_enabled=True,
        auto_save_results=False,  # Don't save files during test
        quality_gates={
            'critical_threshold': 60.0,
            'warning_threshold': 80.0,
            'max_critical_issues': 5,
            'max_total_issues': 50
        }
    )

    pipeline = create_evaluation_pipeline(config)
    pipeline.start()

    try:
        # Test code evaluation
        print("\n  Submitting code evaluation task...")
        sample_code = '''
def sample_function(x, y):
    return x + y

class SampleClass:
    def __init__(self):
        self.value = 0
'''

        task_id = pipeline.evaluate_code(
            sample_code,
            file_path="sample_test.py",
            priority=Priority.HIGH
        )

        print(f"    Task ID: {task_id}")

        # Wait for completion
        print("    Waiting for completion...")
        result = pipeline.wait_for_completion(task_id, timeout=10.0)

        if result:
            print("  ✓ Code evaluation completed")
            print(f"    Quality Score: {result.quality_score.overall:.1f}/100")
            print(f"    Issues: {len(result.issues)}")
        else:
            print("  ✗ Code evaluation failed or timed out")
            return False

        # Test batch evaluation
        print("\n  Submitting batch evaluation task...")
        batch_files = [__file__]  # Test with this file

        batch_task_id = pipeline.evaluate_batch(
            batch_files,
            evaluation_type=EvaluationType.CODE,
            priority=Priority.MEDIUM
        )

        print(f"    Batch Task ID: {batch_task_id}")

        # Wait for batch completion
        print("    Waiting for batch completion...")
        batch_result = pipeline.wait_for_completion(batch_task_id, timeout=15.0)

        if batch_result:
            print("  ✓ Batch evaluation completed")
            print(f"    Quality Score: {batch_result.quality_score.overall:.1f}/100")
            print(f"    Issues: {len(batch_result.issues)}")
            if 'total_targets' in batch_result.metrics:
                print(f"    Targets: {batch_result.metrics['total_targets']}")
                print(f"    Successful: {batch_result.metrics['successful_evaluations']}")
        else:
            print("  ✗ Batch evaluation failed or timed out")
            return False

        # Show pipeline statistics
        print("\n  Pipeline Statistics:")
        stats = pipeline.get_statistics()
        for key, value in stats.items():
            print(f"    {key}: {value}")

        return True

    finally:
        pipeline.stop()
        print("\n  Pipeline stopped")


def test_quality_scores():
    """Test quality score calculation and feedback mechanisms."""
    print("\n=== Testing Quality Scores Calculation ===")

    test_cases = [
        {
            'name': 'Good Code',
            'code': '''
def add_numbers(a, b):
    """
    Add two numbers together.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    return a + b

class Calculator:
    """Simple calculator class."""

    def __init__(self):
        self.history = []

    def add(self, a, b):
        """Add two numbers and record in history."""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
'''
        },
        {
            'name': 'Code with Issues',
            'code': '''
def x(a,b,c,d,e,f,g,h):
    if a:
        if b:
            if c:
                if d:
                    if e:
                        if f:
                            return a+b+c+d+e+f
    return 0

class Big:
    def m1(self):pass
    def m2(self):pass
    def m3(self):pass
    def m4(self):pass
    def m5(self):pass
    def m6(self):pass
    def m7(self):pass
    def m8(self):pass
    def m9(self):pass
    def m10(self):pass
    def m11(self):pass
    def m12(self):pass
    def m13(self):pass
    def m14(self):pass
    def m15(self):pass

def func():
    pass
'''
        }
    ]

    critic = create_critic()

    for test_case in test_cases:
        print(f"\n  Testing: {test_case['name']}")
        result = critic.evaluate_code(test_case['code'])

        print(f"    Overall Score: {result.quality_score.overall:.1f}/100")
        print("    Category Scores:")
        for category, score in result.quality_score.categories.items():
            print(f"      {category}: {score:.1f}")

        print("    Issues by Severity:")
        for severity, count in result.quality_score.issues_by_severity.items():
            if count > 0:
                print(f"      {severity}: {count}")

        print(f"    Recommendations: {len(result.recommendations)}")
        for i, rec in enumerate(result.recommendations[:2], 1):
            print(f"      {i}. {rec}")

        # Test feedback mechanism
        actionable_issues = [issue for issue in result.issues if issue.suggestion]
        print(f"    Actionable Issues: {len(actionable_issues)}/{len(result.issues)}")


def test_architecture_critic():
    """Test the architecture critic functionality."""
    print("\n=== Testing Architecture Critic ===")

    # Test with current directory
    current_dir = Path(__file__).parent.parent.parent.parent.parent  # Go up to project root

    critic = create_critic()

    try:
        result = critic.evaluate_architecture(current_dir)

        print("✓ Architecture evaluation completed")
        print(f"  Overall Quality Score: {result.quality_score.overall:.1f}/100")
        print(f"  Total Issues: {len(result.issues)}")
        print(f"  Evaluation Time: {result.evaluation_time:.3f}s")

        # Show category scores
        print("  Category Scores:")
        for category, score in result.quality_score.categories.items():
            print(f"    {category}: {score:.1f}")

        # Show architecture-specific metrics
        if result.metrics:
            print("  Architecture Metrics:")
            for key, value in result.metrics.items():
                if key != 'error':
                    print(f"    {key}: {value}")

    except Exception as e:
        print(f"✗ Architecture evaluation failed: {e}")
        return False

    return True


def main():
    """Run all tests."""
    print("=== Critic System Integration Test ===")

    test_results = {}

    try:
        # Test code critic
        test_results['code_critic'] = test_code_critic()

        # Test evaluation pipeline
        test_results['evaluation_pipeline'] = test_evaluation_pipeline()

        # Test quality scores
        test_results['quality_scores'] = test_quality_scores()

        # Test architecture critic
        test_results['architecture_critic'] = test_architecture_critic()

    except Exception as e:
        print(f"\n✗ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Summary
    print("\n=== Test Summary ===")
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)

    for test_name, result in test_results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {test_name.replace('_', ' ').title()}: {status}")

    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")

    if passed_tests == total_tests:
        print("🎉 All tests passed! Critic system is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    # Import required enums for the test
    from evaluation import EvaluationType, Priority

    success = main()
    sys.exit(0 if success else 1)
