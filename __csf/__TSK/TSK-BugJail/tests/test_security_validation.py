"""
Security Validation Tests for Phase 2 Implementation.

This module provides comprehensive security testing including vulnerability scanning,
secure coding practices validation, and compliance checks.

Security Test Categories:
- Static Analysis Security Testing (SAST)
- Dependency Security Scanning
- Secure Coding Practices
- Access Control Validation
- Data Protection Tests
- Input Validation Tests
"""

import ast
import json
import re
import subprocess
import unittest
from pathlib import Path
from typing import Any


class SecurityValidationSuite:
    """Comprehensive security validation suite."""

    def __init__(self, src_root: str = "P:/__csf/src"):
        self.src_root = Path(src_root)
        self.findings: list[dict[str, Any]] = []
        self.security_patterns = self._load_security_patterns()

    def _load_security_patterns(self) -> dict[str, list[str]]:
        """Load security vulnerability patterns."""
        return {
            'hardcoded_secrets': [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api_key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']',
                r'aws_access_key_id\s*=\s*["\'][^"\']+["\']',
                r'aws_secret_access_key\s*=\s*["\'][^"\']+["\']',
                r'private_key\s*=\s*["\'][^"\']+["\']',
                r'credential\s*=\s*["\'][^"\']+["\']',
            ],
            'dangerous_functions': [
                r'\beval\s*\(',
                r'\bexec\s*\(',
                r'\b__import__\s*\(',
                r'\bcompile\s*\(',
                r'\bsubprocess\s*\.\w*\s*\(\s*shell\s*=\s*True',
                r'\bos\.system\s*\(',
                r'\binput\s*\(',  # In certain contexts
            ],
            'sql_injection': [
                r'execute\s*\(\s*["\'].*%s',
                r'execute\s*\(\s*["\'].*\+.*["\']',
                r'format\s*\(\s*["\'].*SELECT',
            ],
            'path_traversal': [
                r'open\s*\(\s*["\'][^"\']*["\']\s*\)',
                r'file\s*\(\s*["\'][^"\']*["\']',
                r'\.\.\/',
                r'\.\.\\\\',
            ],
            'weak_cryptography': [
                r'md5\s*\(',
                r'sha1\s*\(',
                r'AES\s*\(\s*[^,)]*\s*,\s*[^,)]*\s*,\s*ECB',
            ],
            'insecure_random': [
                r'random\.random\s*\(',
                r'random\.randint\s*\(',
                r'random\.choice\s*\(',
            ],
        }

    def scan_for_hardcoded_secrets(self) -> dict[str, Any]:
        """Scan for hardcoded secrets and sensitive information."""
        findings = []

        for file_path in self.src_root.rglob("*.py"):
            if not self._should_include_file(file_path):
                continue

            try:
                with open(file_path, encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                for pattern in self.security_patterns['hardcoded_secrets']:
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line, re.IGNORECASE):
                            # Skip if it's clearly a test or example
                            if not self._is_test_or_example(line, file_path):
                                findings.append({
                                    'file': str(file_path),
                                    'line': line_num,
                                    'content': line.strip(),
                                    'pattern': pattern,
                                    'severity': 'HIGH',
                                    'type': 'hardcoded_secret',
                                })

            except Exception as e:
                findings.append({
                    'file': str(file_path),
                    'error': str(e),
                    'severity': 'MEDIUM',
                    'type': 'scan_error',
                })

        return {
            'scan_type': 'hardcoded_secrets',
            'findings': findings,
            'total_count': len(findings),
        }

    def scan_for_dangerous_functions(self) -> dict[str, Any]:
        """Scan for dangerous function usage."""
        findings = []

        for file_path in self.src_root.rglob("*.py"):
            if not self._should_include_file(file_path):
                continue

            try:
                with open(file_path, encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')

                for pattern in self.security_patterns['dangerous_functions']:
                    for line_num, line in enumerate(lines, 1):
                        if re.search(pattern, line):
                            # Check context for legitimate usage
                            if not self._is_legitimate_usage(line, pattern):
                                severity = 'HIGH' if 'eval' in pattern or 'exec' in pattern else 'MEDIUM'
                                findings.append({
                                    'file': str(file_path),
                                    'line': line_num,
                                    'content': line.strip(),
                                    'pattern': pattern,
                                    'severity': severity,
                                    'type': 'dangerous_function',
                                })

            except Exception as e:
                findings.append({
                    'file': str(file_path),
                    'error': str(e),
                    'severity': 'MEDIUM',
                    'type': 'scan_error',
                })

        return {
            'scan_type': 'dangerous_functions',
            'findings': findings,
            'total_count': len(findings),
        }

    def validate_secure_coding_practices(self) -> dict[str, Any]:
        """Validate secure coding practices."""
        findings = []

        for file_path in self.src_root.rglob("*.py"):
            if not self._should_include_file(file_path):
                continue

            try:
                with open(file_path, encoding='utf-8') as f:
                    content = f.read()

                # Parse AST for deeper analysis
                tree = ast.parse(content)

                # Check for security issues using AST
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        # Check for subprocess calls with shell=True
                        if (isinstance(node.func, ast.Attribute) and
                            isinstance(node.func.value, ast.Name) and
                            node.func.value.id == 'subprocess'):
                            for keyword in node.keywords:
                                if (keyword.arg == 'shell' and
                                    isinstance(keyword.value, ast.Constant) and
                                    keyword.value.value is True):
                                    findings.append({
                                        'file': str(file_path),
                                        'line': node.lineno,
                                        'content': 'subprocess call with shell=True',
                                        'severity': 'HIGH',
                                        'type': 'insecure_subprocess',
                                    })

                        # Check for weak random usage
                        elif (isinstance(node.func, ast.Attribute) and
                              isinstance(node.func.value, ast.Name) and
                              node.func.value.id == 'random'):
                            if node.func.attr in ['random', 'randint', 'choice']:
                                findings.append({
                                    'file': str(file_path),
                                    'line': node.lineno,
                                    'content': f'random.{node.func.attr}() usage',
                                    'severity': 'MEDIUM',
                                    'type': 'weak_random',
                                })

                    # Check for exception handling that exposes sensitive data
                    elif isinstance(node, ast.ExceptHandler):
                        if node.name and isinstance(node.name, str):
                            # Check if exception is being logged or printed without sanitization
                            pass  # Would need more sophisticated analysis

            except Exception as e:
                findings.append({
                    'file': str(file_path),
                    'error': str(e),
                    'severity': 'LOW',
                    'type': 'analysis_error',
                })

        return {
            'scan_type': 'secure_coding_practices',
            'findings': findings,
            'total_count': len(findings),
        }

    def test_input_validation(self) -> dict[str, Any]:
        """Test input validation implementation."""
        findings = []

        for file_path in self.src_root.rglob("*.py"):
            if not self._should_include_file(file_path):
                continue

            try:
                with open(file_path, encoding='utf-8') as f:
                    content = f.read()
                    tree = ast.parse(content)

                # Look for functions that process external input
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        # Check if function processes file paths or user input
                        has_input_processing = False
                        has_validation = False

                        # Analyze function body for input processing
                        for child in ast.walk(node):
                            if isinstance(child, ast.Call):
                                # File operations
                                if (isinstance(child.func, ast.Name) and
                                    child.func.id in ['open', 'file']):
                                    has_input_processing = True

                                # Path operations
                                elif (isinstance(child.func, ast.Attribute) and
                                      isinstance(child.func.value, ast.Name) and
                                      child.func.value.id == 'Path'):
                                    has_input_processing = True

                            # Check for validation patterns
                            if isinstance(child, ast.Call):
                                if (isinstance(child.func, ast.Attribute) and
                                    child.func.attr in ['validate', 'sanitize', 'escape']):
                                    has_validation = True

                        # Report if input processing without validation
                        if has_input_processing and not has_validation:
                            findings.append({
                                'file': str(file_path),
                                'line': node.lineno,
                                'function': node.name,
                                'content': f'Function {node.name} processes input without validation',
                                'severity': 'MEDIUM',
                                'type': 'missing_input_validation',
                            })

            except Exception as e:
                findings.append({
                    'file': str(file_path),
                    'error': str(e),
                    'severity': 'LOW',
                    'type': 'analysis_error',
                })

        return {
            'scan_type': 'input_validation',
            'findings': findings,
            'total_count': len(findings),
        }

    def test_file_permissions_and_access(self) -> dict[str, Any]:
        """Test file permissions and access control."""
        findings = []

        for file_path in self.src_root.rglob("*.py"):
            if not self._should_include_file(file_path):
                continue

            try:
                # Check file permissions
                stat_info = file_path.stat()
                mode = oct(stat_info.st_mode)[-3:]

                # Check for world-writable files
                if mode[2] in ['2', '3', '6', '7']:  # World writable
                    findings.append({
                        'file': str(file_path),
                        'content': f'File has world-writable permissions ({mode})',
                        'severity': 'HIGH',
                        'type': 'world_writable_file',
                    })

                # Check for files with sensitive content that are world-readable
                if 'config' in file_path.name.lower() or 'secret' in file_path.name.lower():
                    if mode[2] in ['4', '5', '6', '7']:  # World readable
                        findings.append({
                            'file': str(file_path),
                            'content': f'Config file has world-readable permissions ({mode})',
                            'severity': 'HIGH',
                            'type': 'world_readable_config',
                        })

            except Exception as e:
                findings.append({
                    'file': str(file_path),
                    'error': str(e),
                    'severity': 'LOW',
                    'type': 'permission_check_error',
                })

        return {
            'scan_type': 'file_permissions',
            'findings': findings,
            'total_count': len(findings),
        }

    def run_dependency_security_scan(self) -> dict[str, Any]:
        """Run security scan on dependencies."""
        findings = []

        try:
            # Try to run safety check
            result = subprocess.run(
                ['safety', 'check', '--json'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                # No vulnerabilities found
                safety_data = json.loads(result.stdout)
            else:
                # Vulnerabilities found
                try:
                    safety_data = json.loads(result.stdout)
                    for vuln in safety_data:
                        findings.append({
                            'package': vuln.get('package', 'unknown'),
                            'version': vuln.get('version', 'unknown'),
                            'vulnerability': vuln.get('vulnerability', 'unknown'),
                            'advisory': vuln.get('advisory', ''),
                            'severity': 'HIGH',
                            'type': 'dependency_vulnerability',
                        })
                except json.JSONDecodeError:
                    findings.append({
                        'error': 'Failed to parse safety output',
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'severity': 'MEDIUM',
                        'type': 'scan_error',
                    })

        except subprocess.TimeoutExpired:
            findings.append({
                'error': 'Safety scan timed out',
                'severity': 'MEDIUM',
                'type': 'timeout_error',
            })
        except FileNotFoundError:
            findings.append({
                'error': 'Safety package not installed. Install with: pip install safety',
                'severity': 'LOW',
                'type': 'missing_tool',
            })
        except Exception as e:
            findings.append({
                'error': str(e),
                'severity': 'LOW',
                'type': 'scan_error',
            })

        return {
            'scan_type': 'dependency_security',
            'findings': findings,
            'total_count': len(findings),
        }

    def run_bandit_scan(self) -> dict[str, Any]:
        """Run Bandit static analysis security scan."""
        findings = []

        try:
            # Run bandit on the source directory
            result = subprocess.run(
                ['bandit', '-r', str(self.src_root), '-f', 'json'],
                capture_output=True,
                text=True,
                timeout=60
            )

            try:
                bandit_data = json.loads(result.stdout)
                for issue in bandit_data.get('results', []):
                    findings.append({
                        'file': issue.get('filename', ''),
                        'line': issue.get('line_number', 0),
                        'test_name': issue.get('test_name', ''),
                        'issue_text': issue.get('issue_text', ''),
                        'severity': issue.get('issue_severity', 'MEDIUM'),
                        'type': 'bandit_finding',
                    })
            except json.JSONDecodeError:
                findings.append({
                    'error': 'Failed to parse bandit output',
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'severity': 'MEDIUM',
                    'type': 'scan_error',
                })

        except subprocess.TimeoutExpired:
            findings.append({
                'error': 'Bandit scan timed out',
                'severity': 'MEDIUM',
                'type': 'timeout_error',
            })
        except FileNotFoundError:
            findings.append({
                'error': 'Bandit package not installed. Install with: pip install bandit',
                'severity': 'LOW',
                'type': 'missing_tool',
            })
        except Exception as e:
            findings.append({
                'error': str(e),
                'severity': 'LOW',
                'type': 'scan_error',
            })

        return {
            'scan_type': 'bandit_static_analysis',
            'findings': findings,
            'total_count': len(findings),
        }

    def _should_include_file(self, file_path: Path) -> bool:
        """Check if file should be included in security scan."""
        # Skip test files for certain scans
        exclude_patterns = ['test_', '_test.py', '/tests/', '__pycache__']
        return not any(pattern in str(file_path) for pattern in exclude_patterns)

    def _is_test_or_example(self, line: str, file_path: Path) -> bool:
        """Check if line is in test or example context."""
        return ('test' in str(file_path).lower() or
                'example' in line.lower() or
                'TODO' in line or
                'FIXME' in line or
                line.strip().startswith('#'))

    def _is_legitimate_usage(self, line: str, pattern: str) -> bool:
        """Check if dangerous function usage is legitimate."""
        # Check for common legitimate patterns
        legitimate_contexts = [
            'logging.debug',
            'logging.info',
            '# TODO',
            '# FIXME',
            'except:',
            'raise',
        ]

        return any(context in line for context in legitimate_contexts)

    def run_all_security_scans(self) -> dict[str, Any]:
        """Run all security scans and compile results."""
        print("Running Phase 2 Security Validation...")
        print("=" * 60)

        scans = [
            self.scan_for_hardcoded_secrets,
            self.scan_for_dangerous_functions,
            self.validate_secure_coding_practices,
            self.test_input_validation,
            self.test_file_permissions_and_access,
            self.run_dependency_security_scan,
            self.run_bandit_scan,
        ]

        all_results = {}
        total_findings = 0
        high_severity_count = 0
        medium_severity_count = 0
        low_severity_count = 0

        for scan in scans:
            try:
                result = scan()
                scan_name = result['scan_type']
                all_results[scan_name] = result

                findings_count = result['total_count']
                total_findings += findings_count

                # Count severities
                for finding in result.get('findings', []):
                    severity = finding.get('severity', 'LOW').upper()
                    if severity == 'HIGH':
                        high_severity_count += 1
                    elif severity == 'MEDIUM':
                        medium_severity_count += 1
                    else:
                        low_severity_count += 1

                status = "✓ PASS" if findings_count == 0 else f"✗ {findings_count} issues"
                print(f"{scan_name:<35}: {status}")

            except Exception as e:
                print(f"Error running {scan.__name__}: {e}")

        print("\n" + "=" * 60)
        print("SECURITY SCAN SUMMARY")
        print("=" * 60)
        print(f"Total Findings: {total_findings}")
        print(f"  High Severity: {high_severity_count}")
        print(f"  Medium Severity: {medium_severity_count}")
        print(f"  Low Severity: {low_severity_count}")
        print(f"Overall Status: {'PASS' if high_severity_count == 0 else 'FAIL'}")

        return {
            'overall_pass': high_severity_count == 0,
            'total_findings': total_findings,
            'high_severity_count': high_severity_count,
            'medium_severity_count': medium_severity_count,
            'low_severity_count': low_severity_count,
            'scan_results': all_results,
        }


class TestSecurityValidation(unittest.TestCase):
    """Unit tests for security validation."""

    def setUp(self):
        """Set up security validation suite."""
        self.suite = SecurityValidationSuite()

    def test_hardcoded_secrets_scan(self):
        """Test hardcoded secrets scan."""
        result = self.suite.scan_for_hardcoded_secrets()
        self.assertIn('scan_type', result)
        self.assertIn('findings', result)
        self.assertIn('total_count', result)

    def test_dangerous_functions_scan(self):
        """Test dangerous functions scan."""
        result = self.suite.scan_for_dangerous_functions()
        self.assertIn('scan_type', result)
        self.assertIn('findings', result)
        self.assertIn('total_count', result)

    def test_secure_coding_practices_validation(self):
        """Test secure coding practices validation."""
        result = self.suite.validate_secure_coding_practices()
        self.assertIn('scan_type', result)
        self.assertIn('findings', result)
        self.assertIn('total_count', result)

    def test_input_validation_test(self):
        """Test input validation test."""
        result = self.suite.test_input_validation()
        self.assertIn('scan_type', result)
        self.assertIn('findings', result)
        self.assertIn('total_count', result)

    def test_file_permissions_test(self):
        """Test file permissions test."""
        result = self.suite.test_file_permissions_and_access()
        self.assertIn('scan_type', result)
        self.assertIn('findings', result)
        self.assertIn('total_count', result)


def main():
    """Run security validation and save results."""
    import argparse

    parser = argparse.ArgumentParser(description="Run Phase 2 Security Validation")
    parser.add_argument("--output", "-o", help="Output file for results (JSON)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    # Run security scans
    suite = SecurityValidationSuite()
    results = suite.run_all_security_scans()

    # Save results if output file specified
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\nResults saved to: {args.output}")

    # Print detailed findings if verbose
    if args.verbose and results['total_findings'] > 0:
        print("\nDETAILED FINDINGS:")
        print("-" * 40)
        for scan_name, scan_result in results['scan_results'].items():
            if scan_result['total_count'] > 0:
                print(f"\n{scan_name.upper()}:")
                for finding in scan_result['findings']:
                    if 'error' in finding:
                        print(f"  ERROR: {finding['error']}")
                    else:
                        print(f"  {finding['severity']}: {finding.get('file', 'unknown')}:{finding.get('line', '?')} - {finding.get('content', 'unknown')}")

    # Exit with appropriate code
    return 0 if results['overall_pass'] else 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
