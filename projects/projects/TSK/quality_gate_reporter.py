"""
Quality Gate Reporter for Phase 2 Implementation.

This module generates comprehensive quality gate reports that aggregate results
from all quality validation tests and provide actionable insights.

Report Features:
- Aggregated test results
- Trend analysis
- Actionable recommendations
- Executive summary
- Detailed technical findings
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class QualityGateReporter:
    """Comprehensive quality gate reporting system."""

    def __init__(self, output_dir: str = "P:/projects/TSK/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.report_data = {}
        self.timestamp = datetime.now().isoformat()

    def run_all_quality_gates(self) -> dict[str, Any]:
        """Run all quality gate tests and collect results."""
        print("Running Comprehensive Quality Gate Assessment...")
        print("=" * 70)

        # Run quality gates tests
        print("1. Running Code Quality Gates...")
        try:
            result = subprocess.run([
                sys.executable, "-m", "unittest",
                "tests.test_quality_gates.run_quality_gates"
            ], capture_output=True, text=True, cwd="P:/projects/TSK")

            quality_results = self._parse_test_output(result.stdout, result.stderr)
            self.report_data['code_quality'] = quality_results
        except Exception as e:
            self.report_data['code_quality'] = {
                'error': str(e),
                'status': 'ERROR',
                'passed': False,
            }

        # Run performance benchmarks
        print("2. Running Performance Benchmarks...")
        try:
            result = subprocess.run([
                sys.executable, "tests/test_performance_benchmarks.py"
            ], capture_output=True, text=True, cwd="P:/projects/TSK")

            # Parse JSON output if available
            try:
                performance_results = json.loads(result.stdout)
            except json.JSONDecodeError:
                performance_results = self._parse_test_output(result.stdout, result.stderr)

            self.report_data['performance'] = performance_results
        except Exception as e:
            self.report_data['performance'] = {
                'error': str(e),
                'status': 'ERROR',
                'passed': False,
            }

        # Run security validation
        print("3. Running Security Validation...")
        try:
            result = subprocess.run([
                sys.executable, "tests/test_security_validation.py"
            ], capture_output_output=True, text=True, cwd="P:/projects/TSK")

            # Parse JSON output if available
            try:
                security_results = json.loads(result.stdout)
            except json.JSONDecodeError:
                security_results = self._parse_test_output(result.stdout, result.stderr)

            self.report_data['security'] = security_results
        except Exception as e:
            self.report_data['security'] = {
                'error': str(e),
                'status': 'ERROR',
                'passed': False,
            }

        # Run integration tests
        print("4. Running Integration Tests...")
        try:
            result = subprocess.run([
                sys.executable, "tests/test_phase1_integration.py"
            ], capture_output=True, text=True, cwd="P:/projects/TSK")

            # Parse JSON output if available
            try:
                integration_results = json.loads(result.stdout)
            except json.JSONDecodeError:
                integration_results = self._parse_test_output(result.stdout, result.stderr)

            self.report_data['integration'] = integration_results
        except Exception as e:
            self.report_data['integration'] = {
                'error': str(e),
                'status': 'ERROR',
                'passed': False,
            }

        # Generate overall assessment
        self._generate_overall_assessment()

        return self.report_data

    def _parse_test_output(self, stdout: str, stderr: str) -> dict[str, Any]:
        """Parse test output to extract results."""
        return {
            'stdout': stdout,
            'stderr': stderr,
            'timestamp': datetime.now().isoformat(),
            'status': 'COMPLETED',
            'passed': 'FAIL' not in stdout and 'ERROR' not in stdout,
        }

    def _generate_overall_assessment(self):
        """Generate overall quality assessment."""
        categories = ['code_quality', 'performance', 'security', 'integration']

        passed_count = 0
        total_count = 0
        critical_issues = []
        recommendations = []

        for category in categories:
            if category in self.report_data:
                total_count += 1
                category_data = self.report_data[category]

                if isinstance(category_data, dict):
                    if category_data.get('passed', False):
                        passed_count += 1
                    else:
                        # Identify critical issues
                        if category == 'security':
                            high_severity = category_data.get('high_severity_count', 0)
                            if high_severity > 0:
                                critical_issues.append(f"Security: {high_severity} high severity vulnerabilities")
                                recommendations.append("Address all high severity security vulnerabilities immediately")

                        elif category == 'performance':
                            if not category_data.get('overall_pass', False):
                                critical_issues.append("Performance: Benchmarks not met")
                                recommendations.append("Optimize performance to meet benchmark targets")

                        elif category == 'code_quality':
                            if not category_data.get('passed', False):
                                critical_issues.append("Code Quality: Standards not met")
                                recommendations.append("Improve code quality to meet standards")

                        elif category == 'integration':
                            if not category_data.get('overall_passed', False):
                                critical_issues.append("Integration: Phase 1 compatibility issues")
                                recommendations.append("Fix integration issues with Phase 1 components")

        success_rate = (passed_count / total_count * 100) if total_count > 0 else 0

        self.report_data['overall_assessment'] = {
            'total_categories': total_count,
            'passed_categories': passed_count,
            'success_rate': success_rate,
            'overall_status': 'PASS' if passed_count == total_count else 'FAIL',
            'critical_issues': critical_issues,
            'recommendations': recommendations,
        }

    def generate_executive_summary(self) -> str:
        """Generate executive summary of quality gate results."""
        if 'overall_assessment' not in self.report_data:
            return "Quality gate assessment not completed."

        assessment = self.report_data['overall_assessment']

        summary = f"""
# Phase 2 Quality Gate Executive Summary

**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Overall Status**: {assessment['overall_status']}
**Success Rate**: {assessment['success_rate']:.1f}%

## Quality Assessment by Category

"""
        # Add category summaries
        for category, data in self.report_data.items():
            if category in ['code_quality', 'performance', 'security', 'integration']:
                status = "✅ PASS" if data.get('passed', data.get('overall_passed', False)) else "❌ FAIL"
                summary += f"- **{category.title()}**: {status}\n"

        # Add critical issues
        if assessment['critical_issues']:
            summary += "\n## Critical Issues\n\n"
            for issue in assessment['critical_issues']:
                summary += f"- 🔴 {issue}\n"

        # Add recommendations
        if assessment['recommendations']:
            summary += "\n## Recommendations\n\n"
            for rec in assessment['recommendations']:
                summary += f"- {rec}\n"

        return summary

    def generate_detailed_report(self) -> str:
        """Generate detailed technical report."""
        report = f"""
# Phase 2 Quality Gate Detailed Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Report Version**: 1.0

## Overview

This report provides a comprehensive assessment of Phase 2 implementation quality across multiple dimensions including code quality, performance, security, and integration with Phase 1 components.

## Executive Summary

{self.generate_executive_summary()}

## Detailed Results

"""

        # Add detailed sections for each category
        for category, data in self.report_data.items():
            if category in ['code_quality', 'performance', 'security', 'integration']:
                report += self._generate_category_report(category, data)

        # Add trend analysis (placeholder for future implementation)
        report += self._generate_trend_analysis()

        # Add action items
        report += self._generate_action_items()

        return report

    def _generate_category_report(self, category: str, data: dict[str, Any]) -> str:
        """Generate detailed report for a specific category."""
        report = f"\n### {category.title()}\n\n"

        if isinstance(data, dict):
            status = "✅ PASS" if data.get('passed', data.get('overall_passed', False)) else "❌ FAIL"
            report += f"**Status**: {status}\n\n"

            # Add category-specific details
            if category == 'code_quality':
                report += self._generate_code_quality_details(data)
            elif category == 'performance':
                report += self._generate_performance_details(data)
            elif category == 'security':
                report += self._generate_security_details(data)
            elif category == 'integration':
                report += self._generate_integration_details(data)

        return report

    def _generate_code_quality_details(self, data: dict[str, Any]) -> str:
        """Generate code quality details."""
        details = "**Code Quality Metrics**:\n\n"

        if 'tests_run' in data:
            details += f"- Tests Run: {data['tests_run']}\n"
            details += f"- Success Rate: {data.get('success_rate', 0):.1f}%\n"

        if 'failures' in data:
            details += f"- Failures: {data['failures']}\n"

        if 'errors' in data:
            details += f"- Errors: {data['errors']}\n"

        details += "\n**Recommendations**:\n"
        details += "- Maintain code coverage above 85%\n"
        details += "- Address any code quality violations\n"
        details += "- Ensure all public APIs have proper documentation\n"

        return details + "\n"

    def _generate_performance_details(self, data: dict[str, Any]) -> str:
        """Generate performance details."""
        details = "**Performance Metrics**:\n\n"

        if 'passed_count' in data and 'total_count' in data:
            details += f"- Benchmarks Passed: {data['passed_count']}/{data['total_count']}\n"
            details += f"- Success Rate: {data.get('success_rate', 0):.1f}%\n"

        if 'results' in data:
            for result in data['results']:
                metric_name = result.get('test_name', 'unknown')
                metric_value = result.get('metric_value', 0)
                target_value = result.get('target_value', 0)
                unit = result.get('unit', '')
                passed = result.get('passed', False)

                status = "✅" if passed else "❌"
                details += f"- {status} {metric_name}: {metric_value:.1f}/{target_value} {unit}\n"

        details += "\n**Recommendations**:\n"
        details += "- Optimize processing throughput to meet target benchmarks\n"
        details += "- Monitor memory usage during peak operations\n"
        details += "- Ensure scalability across multiple worker processes\n"

        return details + "\n"

    def _generate_security_details(self, data: dict[str, Any]) -> str:
        """Generate security details."""
        details = "**Security Assessment**:\n\n"

        if 'total_findings' in data:
            details += f"- Total Security Findings: {data['total_findings']}\n"
            details += f"- High Severity: {data.get('high_severity_count', 0)}\n"
            details += f"- Medium Severity: {data.get('medium_severity_count', 0)}\n"
            details += f"- Low Severity: {data.get('low_severity_count', 0)}\n"

        details += "\n**Security Scan Results**:\n"
        if 'scan_results' in data:
            for scan_name, scan_result in data['scan_results'].items():
                findings_count = scan_result.get('total_count', 0)
                status = "✅" if findings_count == 0 else f"❌ ({findings_count} findings)"
                details += f"- {scan_name}: {status}\n"

        details += "\n**Recommendations**:\n"
        details += "- Address all high severity security vulnerabilities immediately\n"
        details += "- Implement secure coding practices across all components\n"
        details += "- Regular security scans should be integrated into CI/CD pipeline\n"

        return details + "\n"

    def _generate_integration_details(self, data: dict[str, Any]) -> str:
        """Generate integration details."""
        details = "**Integration Assessment**:\n\n"

        if 'total_passed' in data and 'total_tests' in data:
            details += f"- Tests Passed: {data['total_passed']}/{data['total_tests']}\n"
            details += f"- Success Rate: {data.get('success_rate', 0):.1f}%\n"

        details += "\n**Integration Test Results**:\n"
        if 'test_results' in data:
            for test_name, test_result in data['test_results'].items():
                passed = test_result.get('passed', False)
                status = "✅" if passed else "❌"
                details += f"- {test_name}: {status}\n"

        details += "\n**Recommendations**:\n"
        details += "- Ensure backward compatibility with Phase 1 components\n"
        details += "- Maintain API contract compliance\n"
        details += "- Monitor performance impact of Phase 2 integration\n"

        return details + "\n"

    def _generate_trend_analysis(self) -> str:
        """Generate trend analysis section."""
        return """
## Trend Analysis

*Note: Trend analysis requires historical data. This section will be populated after multiple quality gate runs.*

**Tracking Metrics**:
- Code quality score over time
- Performance benchmark trends
- Security vulnerability trends
- Integration test success rate

**Benchmarks**:
- Target: Maintain >90% pass rate across all categories
- Alert: Trigger investigation if any category falls below 80%

"""

    def _generate_action_items(self) -> str:
        """Generate actionable items section."""
        action_items = """
## Action Items

### Immediate Actions (Required for Deployment)

1. **Security Issues**
   - [ ] Address all high severity vulnerabilities
   - [ ] Review and fix medium severity issues
   - [ ] Implement security scanning in CI/CD

2. **Performance Optimization**
   - [ ] Optimize components failing benchmarks
   - [ ] Implement performance monitoring
   - [ ] Document performance characteristics

3. **Code Quality Improvements**
   - [ ] Fix code quality violations
   - [ ] Improve test coverage where needed
   - [ ] Update documentation gaps

### Phase 2 Deployment Prerequisites

- [ ] All quality gates must pass
- [ ] Performance benchmarks met or exceeded
- [ ] No high severity security issues
- [ ] Full Phase 1 compatibility verified
- [ ] Documentation complete and up-to-date

### Ongoing Quality Assurance

- [ ] Daily automated quality gate runs
- [ ] Weekly comprehensive reports
- [ ] Monthly trend analysis
- [ ] Quarterly quality improvement planning

"""

        # Add specific action items based on results
        if 'overall_assessment' in self.report_data:
            for rec in self.report_data['overall_assessment'].get('recommendations', []):
                action_items += f"- [ ] {rec}\n"

        return action_items

    def save_reports(self) -> dict[str, str]:
        """Save all reports to files."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_files = {}

        # Save executive summary
        exec_summary_file = self.output_dir / f"quality_gate_executive_summary_{timestamp}.md"
        with open(exec_summary_file, 'w') as f:
            f.write(self.generate_executive_summary())
        report_files['executive_summary'] = str(exec_summary_file)

        # Save detailed report
        detailed_report_file = self.output_dir / f"quality_gate_detailed_report_{timestamp}.md"
        with open(detailed_report_file, 'w') as f:
            f.write(self.generate_detailed_report())
        report_files['detailed_report'] = str(detailed_report_file)

        # Save raw JSON data
        json_report_file = self.output_dir / f"quality_gate_data_{timestamp}.json"
        with open(json_report_file, 'w') as f:
            json.dump(self.report_data, f, indent=2, default=str)
        report_files['json_data'] = str(json_report_file)

        return report_files

    def generate_and_save_reports(self) -> dict[str, str]:
        """Complete pipeline: run tests and save reports."""
        print("Running complete quality gate assessment...")

        # Run all tests
        self.run_all_quality_gates()

        # Generate and save reports
        report_files = self.save_reports()

        # Print summary
        print("\n" + "=" * 70)
        print("QUALITY GATE ASSESSMENT COMPLETE")
        print("=" * 70)

        if 'overall_assessment' in self.report_data:
            assessment = self.report_data['overall_assessment']
            print(f"Overall Status: {assessment['overall_status']}")
            print(f"Success Rate: {assessment['success_rate']:.1f}%")
            print(f"Categories Passed: {assessment['passed_categories']}/{assessment['total_categories']}")

            if assessment['critical_issues']:
                print("\nCritical Issues:")
                for issue in assessment['critical_issues']:
                    print(f"  - {issue}")

        print("\nReports saved to:")
        for report_type, file_path in report_files.items():
            print(f"  - {report_type}: {file_path}")

        return report_files


def main():
    """Main entry point for quality gate reporting."""
    parser = argparse.ArgumentParser(
        description="Generate Phase 2 Quality Gate Reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python quality_gate_reporter.py                    # Run assessment and generate reports
  python quality_gate_reporter.py --output-dir ./reports  # Custom output directory
  python quality_gate_reporter.py --summary-only     # Generate summary only
        """
    )

    parser.add_argument(
        "--output-dir", "-o",
        default="P:/projects/TSK/reports",
        help="Output directory for reports (default: P:/projects/TSK/reports)"
    )

    parser.add_argument(
        "--summary-only", "-s",
        action="store_true",
        help="Generate executive summary only"
    )

    parser.add_argument(
        "--json-output", "-j",
        help="Save JSON results to specified file"
    )

    args = parser.parse_args()

    # Create reporter
    reporter = QualityGateReporter(args.output_dir)

    if args.summary_only:
        # Generate summary only
        print("Generating executive summary...")
        reporter.run_all_quality_gates()
        summary = reporter.generate_executive_summary()
        print(summary)

        if args.json_output:
            with open(args.json_output, 'w') as f:
                json.dump(reporter.report_data, f, indent=2, default=str)
            print(f"\nJSON data saved to: {args.json_output}")
    else:
        # Generate full reports
        report_files = reporter.generate_and_save_reports()

        if args.json_output and 'json_data' in report_files:
            # Copy JSON file to requested location
            import shutil
            shutil.copy2(report_files['json_data'], args.json_output)
            print(f"JSON data also saved to: {args.json_output}")

    # Exit with appropriate code based on overall status
    if 'overall_assessment' in reporter.report_data:
        return 0 if reporter.report_data['overall_assessment']['overall_status'] == 'PASS' else 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
