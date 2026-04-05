#!/usr/bin/env python3
"""
Critic System Demo

This script demonstrates the full functionality of the Critic System including
code analysis, architecture evaluation, and evaluation pipeline usage.
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from critic import (
    create_critic,
    evaluate_file,
    quick_evaluate_code,
    quick_evaluate_project,
)
from evaluation import (
    EvaluationConfig,
    Priority,
    create_evaluation_pipeline,
)


def demo_basic_code_analysis():
    """Demonstrate basic code analysis functionality."""
    print("\n" + "="*60)
    print("🔍 DEMO: Basic Code Analysis")
    print("="*60)

    # Sample code with various issues
    sample_code = '''
def calculate_total(items, tax_rate, discount, shipping, handling, gift_wrap, expedited):
    """Calculate total with too many parameters and complexity."""
    if len(items) > 0:
        if tax_rate > 0:
            if discount > 0:
                if shipping > 0:
                    if handling > 0:
                        if gift_wrap:
                            if expedited:
                                subtotal = sum(item.price for item in items)
                                total = subtotal * (1 + tax_rate)
                                total -= discount
                                total += shipping + handling
                                total *= 1.2  # Gift wrap charge
                                total *= 1.5  # Expedited charge
                                return total
                            else:
                                subtotal = sum(item.price for item in items)
                                total = subtotal * (1 + tax_rate)
                                total -= discount
                                total += shipping + handling
                                total *= 1.2
                                return total
                        else:
                            subtotal = sum(item.price for item in items)
                            total = subtotal * (1 + tax_rate)
                            total -= discount
                            total += shipping + handling
                            return total
                    else:
                        subtotal = sum(item.price for item in items)
                        total = subtotal * (1 + tax_rate)
                        total -= discount
                        total += shipping
                        return total
                else:
                    subtotal = sum(item.price for item in items)
                    total = subtotal * (1 + tax_rate)
                    total -= discount
                    return total
            else:
                subtotal = sum(item.price for item in items)
                total = subtotal * (1 + tax_rate)
                return total
        else:
            subtotal = sum(item.price for item in items)
            return subtotal
    else:
        return 0

class UserManager:
    """A class with too many responsibilities."""

    def __init__(self):
        self.users = []
        self.db_connection = None
        self.email_server = None
        self.logger = None

    def create_user(self, username, password, email): pass
    def delete_user(self, user_id): pass
    def update_user(self, user_id, data): pass
    def authenticate_user(self, username, password): pass
    def send_welcome_email(self, email): pass
    def log_user_action(self, user_id, action): pass
    def backup_user_data(self, user_id): pass
    def validate_user_data(self, data): pass
    def encrypt_password(self, password): pass
    def generate_user_report(self, user_id): pass
    def export_user_data(self, format): pass
    def import_user_data(self, data): pass
    def audit_user_permissions(self, user_id): pass
    def reset_user_password(self, user_id): pass
    def lock_user_account(self, user_id): pass
    def unlock_user_account(self, user_id): pass
    def delete_user_history(self, user_id): pass
    def archive_user(self, user_id): pass
    def restore_user(self, user_id): pass
    def merge_user_accounts(self, user1, user2): pass

def insecure_function():
    # Security issues
    password = "admin123"
    api_key = "sk-1234567890abcdef"

    eval("print('This is dangerous')")

    import os
    os.system(f"echo {password}")

    return True

def empty_function():
    pass

if True:
    pass  # Empty if block
'''

    print("📝 Analyzing sample code with various quality issues...")
    critic = create_critic()
    result = critic.evaluate_code(sample_code, "demo_complex_code.py")

    print("\n📊 Quality Assessment Results:")
    print(f"   Overall Score: {result.quality_score.overall:.1f}/100")
    print(f"   Total Issues: {len(result.issues)}")
    print(f"   Evaluation Time: {result.evaluation_time:.3f} seconds")

    # Quality breakdown
    print("\n📈 Quality Score Breakdown:")
    for category, score in result.quality_score.categories.items():
        status = "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"
        print(f"   {status} {category.title():12}: {score:6.1f}/100")

    # Issues by severity
    print("\n🚨 Issues by Severity:")
    severity_counts = {}
    for issue in result.issues:
        severity = issue.severity.value
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

    for severity in ['critical', 'high', 'medium', 'low', 'info']:
        count = severity_counts.get(severity, 0)
        if count > 0:
            icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢", "info": "🔵"}[severity]
            print(f"   {icon} {severity.title():10}: {count:3d} issues")

    # Top issues
    print("\n🔝 Top 5 Issues:")
    sorted_issues = sorted(result.issues, key=lambda x: x.severity.value, reverse=True)
    for i, issue in enumerate(sorted_issues[:5], 1):
        print(f"   {i}. [{issue.severity.value.upper():8}] {issue.title}")
        print(f"      📍 Line {issue.line_number}: {issue.description[:60]}...")
        if issue.suggestion:
            print(f"      💡 Suggestion: {issue.suggestion[:60]}...")
        print()

    # Recommendations
    if result.recommendations:
        print("💬 Recommendations:")
        for i, rec in enumerate(result.recommendations[:3], 1):
            print(f"   {i}. {rec}")
        print()


def demo_evaluation_pipeline():
    """Demonstrate the evaluation pipeline functionality."""
    print("\n" + "="*60)
    print("⚡ DEMO: Evaluation Pipeline")
    print("="*60)

    # Create pipeline configuration
    config = EvaluationConfig(
        max_concurrent_evaluations=3,
        cache_enabled=True,
        cache_ttl=1800.0,  # 30 minutes
        auto_save_results=False,  # Don't save files during demo
        quality_gates={
            'critical_threshold': 65.0,
            'warning_threshold': 80.0,
            'max_critical_issues': 3,
            'max_total_issues': 40
        }
    )

    print("🔧 Starting evaluation pipeline...")
    pipeline = create_evaluation_pipeline(config)
    pipeline.start()

    try:
        # Submit various evaluation tasks
        tasks = []

        print("📤 Submitting evaluation tasks...")

        # Task 1: Good code
        good_code = '''
def add_numbers(a, b):
    """Add two numbers with proper documentation."""
    return a + b

class SimpleCalculator:
    """A simple calculator with single responsibility."""

    def __init__(self):
        self.history = []

    def add(self, a, b):
        """Add numbers and record in history."""
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
'''
        task1 = pipeline.evaluate_code(good_code, priority=Priority.HIGH)
        tasks.append(("Good Code", task1))
        print("   ✓ Task 1: Good code evaluation submitted")

        # Task 2: Code with issues
        problematic_code = '''
def func(x,y,z,w,u,v):
    if x:
        if y:
            if z:
                if w:
                    if u:
                        return x+y+z+w+u+v
    return 0

password = "secret123"
eval("print('dangerous')")
'''
        task2 = pipeline.evaluate_code(problematic_code, priority=Priority.MEDIUM)
        tasks.append(("Problematic Code", task2))
        print("   ✓ Task 2: Problematic code evaluation submitted")

        # Task 3: Batch evaluation
        batch_files = [__file__]  # Evaluate this file
        task3 = pipeline.evaluate_batch(batch_files, priority=Priority.LOW)
        tasks.append(("Batch Evaluation", task3))
        print("   ✓ Task 3: Batch evaluation submitted")

        # Wait for all tasks to complete
        print("\n⏳ Waiting for all evaluations to complete...")
        results = []

        for task_name, task_id in tasks:
            result = pipeline.wait_for_completion(task_id, timeout=20.0)
            if result:
                quality_score = result.quality_score.overall
                issues_count = len(result.issues)
                print(f"   ✅ {task_name}: Score {quality_score:.1f}/100, {issues_count} issues")
                results.append((task_name, result))
            else:
                print(f"   ❌ {task_name}: Failed or timed out")

        # Show pipeline statistics
        print("\n📊 Pipeline Statistics:")
        stats = pipeline.get_statistics()
        for key, value in stats.items():
            print(f"   {key.replace('_', ' ').title():20}: {value}")

        # Quality gate analysis
        print("\n🚦 Quality Gate Analysis:")
        for task_name, result in results:
            score = result.quality_score.overall
            critical_issues = len([i for i in result.issues if i.severity.value == 'critical'])

            if score < config.quality_gates['critical_threshold']:
                status = "❌ FAILED"
            elif score < config.quality_gates['warning_threshold']:
                status = "⚠️ WARNING"
            else:
                status = "✅ PASSED"

            print(f"   {task_name:20}: {status} (Score: {score:.1f}, Critical: {critical_issues})")

    finally:
        pipeline.stop()
        print("\n🛑 Evaluation pipeline stopped")


def demo_quick_evaluations():
    """Demonstrate quick evaluation functions."""
    print("\n" + "="*60)
    print("🚀 DEMO: Quick Evaluation Functions")
    print("="*60)

    # Quick code evaluation
    print("1️⃣ Quick Code Evaluation:")
    simple_code = '''
def multiply(a, b):
    """Multiply two numbers."""
    return a * b
'''
    result = quick_evaluate_code(simple_code)
    print(f"   Score: {result.quality_score.overall:.1f}/100")
    print(f"   Issues: {len(result.issues)}")
    print(f"   Status: {'✅ Good' if result.quality_score.overall >= 80 else '⚠️ Needs improvement'}")

    # Quick file evaluation
    print("\n2️⃣ Quick File Evaluation:")
    try:
        file_result = evaluate_file(__file__)
        print(f"   File: {Path(__file__).name}")
        print(f"   Score: {file_result.quality_score.overall:.1f}/100")
        print(f"   Issues: {len(file_result.issues)}")
        print(f"   Status: {'✅ Good' if file_result.quality_score.overall >= 80 else '⚠️ Needs improvement'}")
    except Exception as e:
        print(f"   Error evaluating file: {e}")

    # Quick project evaluation (limited scope to avoid timeout)
    print("\n3️⃣ Quick Project Evaluation:")
    try:
        # Evaluate just the current directory
        project_result = quick_evaluate_project(Path(__file__).parent)
        if isinstance(project_result, dict) and 'aggregate' in project_result:
            aggregate = project_result['aggregate']
            avg_score = aggregate.get('average_quality_score', 0)
            total_issues = aggregate.get('total_issues', 0)
            files_analyzed = aggregate.get('total_files_analyzed', 0)

            print(f"   Directory: {Path(__file__).parent.name}")
            print(f"   Files Analyzed: {files_analyzed}")
            print(f"   Average Score: {avg_score:.1f}/100")
            print(f"   Total Issues: {total_issues}")
            print(f"   Status: {'✅ Good' if avg_score >= 80 else '⚠️ Needs improvement'}")
        else:
            print("   Project evaluation returned unexpected result")
    except Exception as e:
        print(f"   Error evaluating project: {e}")


def demo_architecture_analysis():
    """Demonstrate architecture analysis."""
    print("\n" + "="*60)
    print("🏗️ DEMO: Architecture Analysis")
    print("="*60)

    # Test with the current directory
    current_dir = Path(__file__).parent

    print(f"🔍 Analyzing architecture of: {current_dir.name}")
    print("   (This may take a moment...)")

    try:
        critic = create_critic()
        result = critic.evaluate_architecture(current_dir)

        print("\n📊 Architecture Analysis Results:")
        print(f"   Overall Score: {result.quality_score.overall:.1f}/100")
        print(f"   Total Issues: {len(result.issues)}")
        print(f"   Evaluation Time: {result.evaluation_time:.3f} seconds")

        # Architecture-specific metrics
        if result.metrics:
            print("\n📐 Architecture Metrics:")
            for key, value in result.metrics.items():
                if key != 'error':
                    print(f"   {key.replace('_', ' ').title():25}: {value}")

        # Top architectural issues
        if result.issues:
            print("\n🏛️ Top Architectural Issues:")
            sorted_issues = sorted(result.issues, key=lambda x: x.severity.value, reverse=True)
            for i, issue in enumerate(sorted_issues[:3], 1):
                print(f"   {i}. [{issue.severity.value.upper():8}] {issue.title}")
                if issue.suggestion:
                    print(f"      💡 {issue.suggestion}")
                print()

        # Recommendations
        if result.recommendations:
            print("🎯 Architecture Recommendations:")
            for i, rec in enumerate(result.recommendations[:3], 1):
                print(f"   {i}. {rec}")

    except Exception as e:
        print(f"❌ Architecture analysis failed: {e}")


def main():
    """Run all demonstrations."""
    print("🎭 CRITIC SYSTEM COMPREHENSIVE DEMO")
    print("=" * 60)
    print("This demo showcases the full capabilities of the Critic System")
    print("including code analysis, architecture evaluation, and pipeline processing.")

    try:
        # Run all demos
        demo_basic_code_analysis()
        demo_evaluation_pipeline()
        demo_quick_evaluations()
        demo_architecture_analysis()

        print("\n" + "="*60)
        print("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\n📚 Key Takeaways:")
        print("   ✅ Code analysis with detailed quality scoring")
        print("   ✅ Issue detection with actionable suggestions")
        print("   ✅ Architecture evaluation and design pattern analysis")
        print("   ✅ Concurrent evaluation pipeline with caching")
        print("   ✅ Quality gates and continuous evaluation support")
        print("   ✅ Flexible configuration and customization")

        print("\n🔗 For more information, see: CRITIC_SYSTEM_README.md")
        print("🚀 Start using the Critic System to improve your code quality!")

        return True

    except KeyboardInterrupt:
        print("\n\n⏹️ Demo interrupted by user")
        return False
    except Exception as e:
        print(f"\n\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
