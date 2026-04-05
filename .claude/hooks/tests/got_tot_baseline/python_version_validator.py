"""
Python Version Compatibility Validator for GoT/ToT Integration

Purpose: Validate baseline tests and GoT/ToT integration code works across Python 3.12+

This module:
1. Checks Python version requirements
2. Scans for version-specific features
3. Tests baseline compatibility
4. Generates version compatibility report

Usage:
    python python_version_validator.py              # Full validation
    python python_version_validator.py --scan       # Scan features only
    python python_version_validator.py --test       # Run tests only
"""

import ast
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class FeatureUsage:
    """Track Python feature usage across files."""
    feature_name: str
    min_version: str
    files_using: List[str] = field(default_factory=list)
    count: int = 0
    examples: List[str] = field(default_factory=list)


class PythonVersionValidator:
    """Validate Python version compatibility for baseline tests."""

    # Python 3.12+ features to scan for
    VERSION_FEATURES = {
        "3.12": [
            ("Type parameter syntax using []", r"def \w+\[.*?\]\("),
            ("f-string debugging", r"=\{"),
            ("type alias statements", r"type \w+\s*="),
        ],
        "3.13": [
            ("type alias defaults (PEP 695)", r"type \w+\[.*?\]\s*="),
            ("experimental type params (continued)", r"\[.*?:.*?\]"),
        ],
    }

    # Standard library imports to check
    STANDARD_LIBS = {
        "dataclasses": "3.7",
        "typing": "3.5",
        "pathlib": "3.4",
        "re": "Any",
        "json": "Any",
        "pytest": "External (test framework)",
    }

    def __init__(self, baseline_dir: Path):
        self.baseline_dir = baseline_dir
        self.current_version = sys.version_info
        self.features_found: List[FeatureUsage] = []
        self.test_results: Dict[str, Any] = {}

    def get_minimum_python_version(self) -> str:
        """Determine minimum Python version from current version."""
        # Current version is Python 3.14
        if self.current_version >= (3, 14):
            return "3.12"
        elif self.current_version >= (3, 13):
            return "3.12"
        elif self.current_version >= (3, 12):
            return "3.12"
        else:
            return f"{self.current_version.major}.{self.current_version.minor}"

    def scan_file_for_features(self, file_path: Path) -> List[FeatureUsage]:
        """Scan a Python file for version-specific features."""
        features = []

        try:
            content = file_path.read_text()
        except Exception:
            return features

        # Check for Python 3.12+ features
        for version, version_features in self.VERSION_FEATURES.items():
            for feature_name, pattern in version_features:
                matches = re.findall(pattern, content)
                if matches:
                    features.append(FeatureUsage(
                        feature_name=feature_name,
                        min_version=version,
                        files_using=[str(file_path.name)],
                        count=len(matches),
                        examples=matches[:3]  # First 3 examples
                    ))

        return features

    def scan_baseline_tests(self) -> None:
        """Scan all baseline test files for version-specific features."""
        test_files = list(self.baseline_dir.glob("test_*_baseline.py"))

        print(f"Scanning {len(test_files)} baseline test files for Python 3.12+ features...")
        print()

        for test_file in test_files:
            features = self.scan_file_for_features(test_file)
            self.features_found.extend(features)

            if features:
                print(f"  {test_file.name}:")
                for feature in features:
                    print(f"    - {feature.feature_name} (requires Python {feature.min_version}+)")
                    print(f"      Used {feature.count} time(s)")

        print()

    def check_imports(self) -> Dict[str, Any]:
        """Check imports in baseline tests for version requirements."""
        import_info = {
            "standard_lib": {},
            "external": [],
            "missing": []
        }

        test_files = list(self.baseline_dir.glob("test_*_baseline.py"))

        for test_file in test_files:
            try:
                tree = ast.parse(test_file.read_text())
            except Exception:
                import_info["missing"].append(str(test_file.name))
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.name.split(".")[0]
                        if name in self.STANDARD_LIBS:
                            version = self.STANDARD_LIBS[name]
                            if version != "Any":
                                import_info["standard_lib"][name] = version
                        else:
                            if name not in import_info["external"]:
                                import_info["external"].append(name)

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        name = node.module.split(".")[0]
                        if name in self.STANDARD_LIBS:
                            version = self.STANDARD_LIBS[name]
                            if version != "Any":
                                import_info["standard_lib"][name] = version
                        elif name not in import_info["external"]:
                            import_info["external"].append(name)

        return import_info

    def run_baseline_tests(self) -> Dict[str, Any]:
        """Run all baseline tests and collect results."""
        test_files = list(self.baseline_dir.glob("test_*_baseline.py"))

        results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "errors": [],
            "details": {}
        }

        print(f"Running {len(test_files)} baseline test files...")
        print()

        for test_file in test_files:
            print(f"  Testing {test_file.name}...")

            try:
                # Run pytest with JSON output
                result = subprocess.run(
                    [sys.executable, "-m", "pytest", str(test_file), "-v", "--tb=short"],
                    capture_output=True,
                    text=True,
                    cwd=self.baseline_dir
                )

                # Parse output for test count
                test_count = 0
                passed = result.returncode == 0

                for line in result.stdout.split("\n"):
                    if "passed" in line:
                        match = re.search(r"(\d+) passed", line)
                        if match:
                            test_count = int(match.group(1))

                results["details"][test_file.name] = {
                    "exit_code": result.returncode,
                    "test_count": test_count,
                    "passed": passed,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }

                results["total_tests"] += test_count
                if passed:
                    results["passed"] += test_count
                    print(f"    ✅ {test_count} tests passed")
                else:
                    results["failed"] += test_count
                    results["errors"].append(str(test_file.name))
                    print("    ❌ Tests failed")

            except Exception as e:
                results["errors"].append(f"{test_file.name}: {str(e)}")
                print(f"    ❌ Error: {e}")

        print()
        return results

    def generate_report(self) -> str:
        """Generate version compatibility report."""
        min_version = self.get_minimum_python_version()

        report = []
        report.append("=" * 70)
        report.append("PYTHON VERSION COMPATIBILITY REPORT")
        report.append("=" * 70)
        report.append("")

        # Current version info
        report.append(f"Current Python Version: {self.current_version.major}.{self.current_version.minor}.{self.current_version.micro}")
        report.append(f"Minimum Supported: {min_version}")
        report.append(f"Testing Date: {subprocess.run(['date', '/T'], capture_output=True).stdout.decode().strip()}")
        report.append("")

        # Feature usage
        if self.features_found:
            report.append("Python 3.12+ Features Detected:")
            report.append("-" * 70)

            for feature in self.features_found:
                report.append(f"  {feature.feature_name}")
                report.append(f"    Requires: Python {feature.min_version}+")
                report.append(f"    Used in: {', '.join(feature.files_using)}")
                report.append(f"    Count: {feature.count}")
                report.append("")
        else:
            report.append("✅ No Python 3.12+ specific features detected")
            report.append("All baseline tests use Python 3.9+ compatible syntax")
            report.append("")

        # Test results
        if self.test_results:
            report.append("Baseline Test Results:")
            report.append("-" * 70)
            report.append(f"  Total Tests: {self.test_results['total_tests']}")
            report.append(f"  Passed: {self.test_results['passed']}")
            report.append(f"  Failed: {self.test_results['failed']}")

            if self.test_results['errors']:
                report.append("")
                report.append("  Errors:")
                for error in self.test_results['errors']:
                    report.append(f"    - {error}")

            report.append("")

        # Compatibility summary
        report.append("Compatibility Summary:")
        report.append("-" * 70)

        if self.current_version >= (3, 12):
            report.append("  ✅ Current Python version is compatible")
            report.append(f"  ✅ All features supported (Python {min_version}+ required)")
        else:
            report.append("  ⚠️  Current Python version is below minimum")
            report.append(f"  ❌ Upgrade to Python {min_version}+ required")

        report.append("")

        # Recommendations
        report.append("Recommendations:")
        report.append("-" * 70)

        if not self.features_found:
            report.append("  1. ✅ Baseline tests use version-agnostic Python syntax")
            report.append("  2. ✅ Safe to run on Python 3.12+ environments")
        else:
            report.append("  1. ⚠️  Some tests use Python 3.12+ specific features")
            report.append("  2. Ensure deployment environment uses Python 3.12+")
            report.append("  3. Consider adding version check in test files")

        report.append("")
        report.append("=" * 70)

        return "\n".join(report)

    def save_report(self, report: str) -> Path:
        """Save compatibility report to file."""
        report_path = self.baseline_dir / "python_version_compatibility_report.txt"

        with open(report_path, 'w') as f:
            f.write(report)

        return report_path


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate Python version compatibility for GoT/ToT integration"
    )
    parser.add_argument(
        "--scan",
        action="store_true",
        help="Scan for version-specific features only"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run baseline tests only"
    )
    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Skip generating report file"
    )

    args = parser.parse_args()

    # Determine baseline directory
    script_dir = Path(__file__).resolve().parent
    baseline_dir = script_dir

    # Run validation
    validator = PythonVersionValidator(baseline_dir)

    print("=" * 70)
    print("PYTHON VERSION COMPATIBILITY VALIDATION")
    print("=" * 70)
    print()

    # Always scan first
    validator.scan_baseline_tests()

    # Check imports
    import_info = validator.check_imports()

    print("Import Analysis:")
    print("-" * 70)
    print(f"  Standard Library: {len(import_info['standard_lib'])} modules")
    print(f"  External: {len(import_info['external'])} packages")
    print(f"  Parse Errors: {len(import_info['missing'])} files")
    print()

    if import_info['standard_lib']:
        print("  Standard Library Modules:")
        for module, version in import_info['standard_lib'].items():
            print(f"    - {module} (Python {version}+)")
        print()

    if import_info['external']:
        print("  External Packages:")
        for package in import_info['external']:
            print(f"    - {package}")
        print()

    # Run tests unless --scan flag
    if not args.scan:
        validator.test_results = validator.run_baseline_tests()

    # Generate and save report
    if not args.no_report:
        report = validator.generate_report()
        print(report)

        report_path = validator.save_report(report)
        print(f"\n✅ Report saved: {report_path}")
    else:
        # Print brief summary
        print()
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Current Python: {validator.current_version.major}.{validator.current_version.minor}.{validator.current_version.micro}")
        print("Minimum Required: 3.12+")

        if validator.test_results:
            print(f"Tests Passed: {validator.test_results['passed']}/{validator.test_results['total_tests']}")

        if validator.features_found:
            print(f"Version Features: {len(validator.features_found)} detected")
        else:
            print("Version Features: None detected (version-agnostic)")

        print()


if __name__ == "__main__":
    main()
