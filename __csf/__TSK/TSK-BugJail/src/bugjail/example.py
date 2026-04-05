"""
BugJail Example Usage

Demonstrates BugJail bug detection and analysis capabilities.
"""

import sys
import tempfile
from pathlib import Path

# Add the bugjail module to the path
sys.path.insert(0, str(Path(__file__).parent))

from bugjail import BugJailAnalyzer, BugJailConfig, BugJailDetector, BugSeverity


def create_example_code_with_issues():
    """Create example code with various bugs and vulnerabilities."""
    return '''
import sqlite3
import os
import subprocess

# Example 1: SQL Injection vulnerability
def get_user_by_id(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # SQL Injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)

    return cursor.fetchone()

# Example 2: Resource leak (file not closed)
def read_config():
    file = open('config.json', 'r')
    data = file.read()
    # Missing file.close() or context manager
    return data

# Example 3: Division by zero
def calculate_ratio(numerator, denominator):
    # Potential division by zero
    return numerator / denominator

# Example 4: Null pointer dereference
def process_user_data(user_id):
    user = find_user(user_id)  # Could return None
    # Missing null check
    return user.get_profile()

# Example 5: Hardcoded password/secret
API_SECRET = "sk-1234567890abcdef"  # Hardcoded secret
DATABASE_PASSWORD = "admin123"  # Hardcoded password

# Example 6: Command injection
def run_system_command(command):
    # Command injection vulnerability
    result = subprocess.run(command, shell=True, check=True)
    return result.stdout

# Example 7: Use of eval() (security risk)
def evaluate_expression(expr):
    # Dangerous eval usage
    return eval(expr)

# Example 8: Assignment in condition (common mistake)
def check_value(value):
    # Assignment instead of comparison
    if value = None:
        return False
    return True

# Example 9: Race condition (non-atomic operation)
counter = 0
def increment_counter():
    global counter
    # Non-atomic increment
    counter = counter + 1

# Example 10: Weak cryptographic algorithm
def hash_password(password):
    # Weak hashing algorithm
    import hashlib
    return hashlib.md5(password.encode()).hexdigest()

# Helper functions
def find_user(user_id):
    # Simulate finding user (sometimes returns None)
    if user_id == 0:
        return None
    return {"id": user_id, "name": f"User {user_id}"}

# Main execution
if __name__ == "__main__":
    print("Running example with various bugs and vulnerabilities...")

    # Trigger some of the bugs
    result = get_user_by_id("1; DROP TABLE users; --")
    config = read_config()
    ratio = calculate_ratio(10, 0)  # Division by zero!
    profile = process_user_data(0)  # Null pointer!

    print(f"Result: {result}")
    print(f"Config: {config[:50]}...")
    print(f"Ratio: {ratio}")
    print(f"Profile: {profile}")
'''


def run_basic_detection_example():
    """Example 1: Basic bug detection."""
    print("\n" + "="*60)
    print("Example 1: Basic Bug Detection")
    print("="*60)

    # Create temporary file with example code
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(create_example_code_with_issues())
        f.flush()
        temp_file = f.name

    try:
        # Create detector
        config = BugJailConfig(
            enable_vulnerability_scanning=True,
            enable_constitutional_compliance=True,
            min_severity_level=BugSeverity.LOW
        )
        detector = BugJailDetector(config)

        print(f"\nAnalyzing file: {temp_file}")

        # Run detection
        report = detector.analyze_path(temp_file)

        # Display results
        print(f"\n✓ Analysis completed in {report.duration_seconds:.2f} seconds")
        print("📊 Summary:")
        print(f"   - Total issues: {report.total_issues}")
        print(f"   - Bugs: {len(report.bugs)}")
        print(f"   - Vulnerabilities: {len(report.vulnerabilities)}")
        print(f"   - Files analyzed: {len(report.files_analyzed)}")
        print(f"   - Constitutional compliance: {report.constitutional_compliance.value}")

        # Show bug details
        if report.bugs:
            print(f"\n🐛 Found {len(report.bugs)} bugs:")
            for i, bug in enumerate(report.bugs[:5], 1):  # Show first 5
                print(f"\n  {i}. {bug.message}")
                print(f"     Type: {bug.type.value}")
                print(f"     Severity: {bug.severity.value}")
                print(f"     Location: {bug.file_path}:{bug.line_number}")
                print(f"     Code: {bug.code_snippet.strip()}")
                print(f"     Confidence: {bug.confidence:.1%}")

        # Show vulnerability details
        if report.vulnerabilities:
            print(f"\n🔒 Found {len(report.vulnerabilities)} vulnerabilities:")
            for i, vuln in enumerate(report.vulnerabilities[:5], 1):  # Show first 5
                print(f"\n  {i}. {vuln.message}")
                print(f"     OWASP Category: {vuln.vulnerability_type.value}")
                print(f"     Severity: {vuln.severity.value}")
                print(f"     CVSS Score: {vuln.cvss_score}")
                print(f"     CWE: {vuln.cwe_id}")

        # Show recommendations
        if report.recommendations:
            print(f"\n💡 Generated {len(report.recommendations)} recommendations:")
            for i, rec in enumerate(report.recommendations[:3], 1):  # Show first 3
                print(f"\n  {i}. {rec.title}")
                print(f"     {rec.description}")
                if rec.effort_estimate:
                    print(f"     Effort: {rec.effort_estimate}")
                if rec.before_example and rec.after_example:
                    print(f"     Before: {rec.before_example}")
                    print(f"     After:  {rec.after_example}")

    finally:
        # Clean up
        Path(temp_file).unlink()


def run_cwo12_integration_example():
    """Example 2: CWO12 workflow integration."""
    print("\n" + "="*60)
    print("Example 2: CWO12 Workflow Integration")
    print("="*60)

    # Create temporary project
    with tempfile.TemporaryDirectory() as tmpdir:
        project_path = Path(tmpdir)

        # Create project files
        (project_path / "main.py").write_text('''
# Main application code
import sqlite3

class UserManager:
    def __init__(self):
        self.db = sqlite3.connect('users.db')  # Resource leak

    def get_user(self, user_id):
        query = f"SELECT * FROM users WHERE id = {user_id}"  # SQL injection
        cursor = self.db.cursor()
        return cursor.execute(query).fetchone()

    def calculate_stats(self, total, count):
        return total / count  # Division by zero
''')

        (project_path / "auth.py").write_text('''
# Authentication module
SECRET_KEY = "hardcoded-secret-key"  # Hardcoded secret

def login(username, password):
    # SQL injection in login
    query = f"SELECT * FROM users WHERE username = '{username}'"
    return db.execute(query)
''')

        try:
            import asyncio
            analyzer = BugJailAnalyzer()

            async def run_cwo12_analysis():
                print(f"\nProject path: {project_path}")

                # CWO12 Step 5 - Architecture analysis
                print("\n🔍 Running CWO12 Step 5 analysis...")
                step5_result = await analyzer.trigger_cwo12_step5_enhancement(str(project_path))

                print("✓ Step 5 completed")
                print(f"  - Architecture issues: {step5_result['architecture_analysis']['total_issues']}")
                print(f"  - Critical issues: {len(step5_result['architecture_analysis']['critical_issues'])}")
                print(f"  - Security issues: {len(step5_result['architecture_analysis']['security_issues'])}")
                print(f"  - Compliance violations: {step5_result['compliance_status']['violations']}")

                # CWO12 Step 7 - Pre-implementation analysis
                print("\n📋 Running CWO12 Step 7 precomputation...")
                tasks = [
                    "Fix SQL injection in auth.py",
                    "Implement proper resource cleanup in main.py",
                    "Add input validation"
                ]
                step7_result = await analyzer.trigger_cwo12_step7_precomputation(str(project_path), tasks)

                print("✓ Step 7 completed")
                print(f"  - Files analyzed: {len(step7_result['analyzed_files'])}")
                print(f"  - Total issues: {step7_result['total_issues']}")
                print(f"  - High risk files: {len(step7_result['risk_assessment']['high_risk_files'])}")
                print(f"  - Implementation ready: {step7_result['recommendations']['implementation_ready']}")

                return step5_result, step7_result

            # Run async analysis
            step5_result, step7_result = asyncio.run(run_cwo12_analysis())

        except Exception as e:
            print(f"✗ CWO12 integration example failed: {e}")


def run_rca_enhancement_example():
    """Example 3: RCA enhancement."""
    print("\n" + "="*60)
    print("Example 3: RCA Enhancement")
    print("="*60)

    # Create file with error location
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write('''
import sqlite3

def process_user(user_id):
    conn = sqlite3.connect('database.db')  # Line 4 - Resource leak
    query = f"SELECT * FROM users WHERE id = {user_id}"  # Line 5 - SQL injection
    cursor = conn.cursor()
    result = cursor.execute(query).fetchone()

    data = result['data']  # Line 8 - Potential null dereference
    return data.upper()

def calculate_average(numbers):
    return sum(numbers) / len(numbers)  # Line 12 - Division by zero
''')
        f.flush()
        error_file = f.name

    try:
        import asyncio
        analyzer = BugJailAnalyzer()

        async def run_rca_enhancement():
            # Simulate error information
            error_info = {
                "type": "AttributeError",
                "message": "'NoneType' object has no attribute 'upper'",
                "file_path": error_file,
                "line_number": 8
            }

            print(f"\nError occurred in {error_file} at line 8")
            print(f"Error: {error_info['message']}")

            print("\n🔍 Running RCA enhancement...")
            rca_result = await analyzer.enhance_rca_analysis(error_info, "/tmp")

            print("✓ RCA enhancement completed")
            print(f"  - Related bugs found: {len(rca_result['related_bugs'])}")

            if rca_result['related_bugs']:
                print("\n  Related issues:")
                for bug in rca_result['related_bugs'][:3]:
                    print(f"    - {bug['type']} at line {bug['line']} (confidence: {bug['confidence']:.1%})")
                    print(f"      Distance from error: {bug['distance_from_error']} lines")

            print("\n  Suggested causes:")
            for cause in rca_result['suggested_causes'][:3]:
                print(f"    - {cause}")

            print("\n  Recommendations:")
            for rec in rca_result['recommendations'][:3]:
                print(f"    - {rec}")

            return rca_result

        # Run async RCA
        rca_result = asyncio.run(run_rca_enhancement())

    except Exception as e:
        print(f"✗ RCA enhancement example failed: {e}")

    finally:
        Path(error_file).unlink()


def main():
    """Run all examples."""
    print("BugJail - Automated Bug Detection System")
    print("Phase 2 Implementation for CSF NIP Security Framework")

    try:
        # Run examples
        run_basic_detection_example()
        run_cwo12_integration_example()
        run_rca_enhancement_example()

        print("\n" + "="*60)
        print("✅ All examples completed successfully!")
        print("="*60)

        print("\nBugJail features demonstrated:")
        print("  ✓ Bug pattern detection")
        print("  ✓ OWASP vulnerability scanning")
        print("  ✓ Constitutional compliance validation")
        print("  ✓ Actionable fix recommendations")
        print("  ✓ CWO12 workflow integration")
        print("  ✓ RCA enhancement")

        print("\nTo learn more:")
        print("  - Read the documentation in README.md")
        print("  - Run the test suite: python test_runner.py")
        print("  - Check the API endpoints in api/endpoints.py")

    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
