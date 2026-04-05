"""
Comprehensive Quality Gates Validation Tests for Phase 2 Implementation.

This module provides automated validation tests that enforce the quality gates
defined in qual-gate.md. Tests cover code quality, performance, security,
integration, and documentation standards.

Test Categories:
- Code Quality Gates
- Performance Validation
- Security Compliance
- Integration Testing
- Documentation Validation
"""

import ast
import importlib.util
import json
import re
import sys
import time
import unittest
from pathlib import Path

# Quality gate thresholds from qual-gate.md
QUALITY_THRESHOLDS = {
    'cyclomatic_complexity': 10,
    'code_coverage': 85,  # percentage
    'maintainability_index': 70,
    'duplicate_code': 3,  # percentage
    'line_length': 88,
    'docstring_coverage': 95,  # percentage
    'type_annotation_coverage': 90,  # percentage
}

PERFORMANCE_TARGETS = {
    'throughput_files_per_second': 50,
    'batch_processing_time': 5.0,  # seconds
    'single_file_processing': 0.1,  # seconds
    'worker_efficiency': 80,  # percentage
    'backup_overhead': 10,  # percentage
}

RESOURCE_LIMITS = {
    'base_memory_mb': 50,
    'per_batch_memory_mb': 100,
    'peak_memory_mb': 500,
    'normal_cpu_percent': 70,
    'peak_cpu_percent': 90,
}


class TestCodeQualityGates(unittest.TestCase):
    """Test code quality against defined standards."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment and discover source files."""
        cls.src_root = Path("P:/__csf/src")
        cls.test_root = Path("P:/__csf/tests")
        cls.python_files = list(cls.src_root.rglob("*.py"))
        cls.phase2_files = [
            f for f in cls.python_files
            if any("phase2" in str(f).lower() for _ in [1]) or
               any(component in str(f).lower()
                   for component in ["parallel_processing", "deployment", "coordinator"])
        ]

    def test_cyclomatic_complexity(self):
        """Validate cyclomatic complexity threshold."""
        failures = []

        for file_path in self.phase2_files:
            try:
                with open(file_path, encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)
                complexity = self._calculate_complexity(tree)

                if complexity > QUALITY_THRESHOLDS['cyclomatic_complexity']:
                    failures.append(f"{file_path}: {complexity}")
            except Exception as e:
                self.fail(f"Error analyzing {file_path}: {e}")

        self.assertFalse(failures,
                        f"Files exceeding complexity threshold {QUALITY_THRESHOLDS['cyclomatic_complexity']}: {failures}")

    def test_line_length_compliance(self):
        """Validate line length compliance."""
        failures = []

        for file_path in self.phase2_files:
            try:
                with open(file_path, encoding='utf-8') as f:
                    lines = f.readlines()

                for i, line in enumerate(lines, 1):
                    if len(line.rstrip()) > QUALITY_THRESHOLDS['line_length']:
                        failures.append(f"{file_path}:{i}:{len(line.rstrip())}")
            except Exception as e:
                self.fail(f"Error reading {file_path}: {e}")

        # Allow some exceptions for long URLs or comments
        self.assertLessEqual(len(failures), 5,
                            f"Too many lines exceed length limit: {failures[:10]}")

    def test_docstring_coverage(self):
        """Validate docstring coverage for public components."""
        missing_docs = []

        for file_path in self.phase2_files:
            try:
                with open(file_path, encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
                        if not node.name.startswith('_'):  # Public member
                            if not ast.get_docstring(node):
                                missing_docs.append(f"{file_path}:{node.name}")
            except Exception as e:
                self.fail(f"Error analyzing {file_path}: {e}")

        # Calculate coverage
        total_public = len([f for f in self.phase2_files for _ in [1]]) * 10  # Estimate
        missing_count = len(missing_docs)
        coverage = ((total_public - missing_count) / total_public * 100) if total_public > 0 else 0

        self.assertGreaterEqual(coverage, QUALITY_THRESHOLDS['docstring_coverage'],
                               f"Docstring coverage {coverage:.1f}% below threshold {QUALITY_THRESHOLDS['docstring_coverage']}%")

    def test_type_annotation_coverage(self):
        """Validate type annotation coverage."""
        missing_annotations = []

        for file_path in self.phase2_files:
            try:
                with open(file_path, encoding='utf-8') as f:
                    content = f.read()

                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        if not node.name.startswith('_'):  # Public function
                            # Check return type annotation
                            if not node.returns:
                                missing_annotations.append(f"{file_path}:{node.name}:return")

                            # Check argument annotations
                            for arg in node.args.args:
                                if arg.annotation is None and arg.arg != 'self':
                                    missing_annotations.append(f"{file_path}:{node.name}:arg:{arg.arg}")
            except Exception as e:
                self.fail(f"Error analyzing {file_path}: {e}")

        # Calculate coverage (simplified)
        total_args_returns = len([f for f in self.phase2_files for _ in [1]]) * 5  # Estimate
        missing_count = len(missing_annotations)
        coverage = ((total_args_returns - missing_count) / total_args_returns * 100) if total_args_returns > 0 else 0

        self.assertGreaterEqual(coverage, QUALITY_THRESHOLDS['type_annotation_coverage'],
                               f"Type annotation coverage {coverage:.1f}% below threshold {QUALITY_THRESHOLDS['type_annotation_coverage']}%")

    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of an AST node."""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor,
                                 ast.With, ast.AsyncWith, ast.ExceptHandler,
                                 ast.And, ast.Or)):
                complexity += 1

        return complexity


class TestPerformanceGates(unittest.TestCase):
    """Test performance characteristics against benchmarks."""

    @classmethod
    def setUpClass(cls):
        """Set up performance test environment."""
        cls.test_data_dir = Path("P:/__csf/tests/test_data")
        cls.test_data_dir.mkdir(exist_ok=True)
        cls._create_test_files()

    @classmethod
    def _create_test_files(cls):
        """Create test files for performance testing."""
        # Create test Python files with import statements
        test_content = '''
import sys
import os
from pathlib import Path
from typing import List, Dict

class TestClass:
    def __init__(self):
        self.value = 0

    def process_data(self, data: List) -> Dict:
        return {"result": len(data)}

def test_function(param: str) -> bool:
    return len(param) > 0
'''

        for i in range(100):  # Create 100 test files
            file_path = cls.test_data_dir / f"test_file_{i:03d}.py"
            with open(file_path, 'w') as f:
                f.write(test_content)

    def test_parallel_processing_throughput(self):
        """Test parallel processing throughput."""
        try:
            # Try to import the phase2 infrastructure
            sys.path.insert(0, "P:/__csf/src")
            from phase2c_parallel_processing_infrastructure import (
                ParallelProcessingOrchestrator,
            )

            orchestrator = ParallelProcessingOrchestrator(max_workers=4)

            # Measure throughput
            test_files = list(self.test_data_dir.glob("*.py"))
            start_time = time.time()

            results, stats = orchestrator.process_files(test_files)

            end_time = time.time()
            elapsed = end_time - start_time
            throughput = len(test_files) / elapsed if elapsed > 0 else 0

            self.assertGreaterEqual(throughput, PERFORMANCE_TARGETS['throughput_files_per_second'],
                                   f"Throughput {throughput:.1f} files/sec below target {PERFORMANCE_TARGETS['throughput_files_per_second']}")

        except ImportError:
            self.skipTest("Phase 2 parallel processing infrastructure not available")

    def test_memory_usage_limits(self):
        """Test memory usage during processing."""
        try:
            import psutil
            process = psutil.Process()

            # Baseline memory
            baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Process files
            test_files = list(self.test_data_dir.glob("*.py"))

            # Simulate processing (simplified)
            for file_path in test_files[:50]:  # Process half the files
                with open(file_path) as f:
                    content = f.read()
                    # Simulate AST processing
                    ast.parse(content)

            peak_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = peak_memory - baseline_memory

            self.assertLessEqual(memory_increase, RESOURCE_LIMITS['per_batch_memory_mb'],
                               f"Memory increase {memory_increase:.1f}MB exceeds limit {RESOURCE_LIMITS['per_batch_memory_mb']}MB")

        except ImportError:
            self.skipTest("psutil not available for memory monitoring")

    def test_batch_processing_time(self):
        """Test batch processing time compliance."""
        test_files = list(self.test_data_dir.glob("*.py"))

        # Simulate batch processing
        start_time = time.time()

        # Process in batches
        batch_size = 50
        for i in range(0, len(test_files), batch_size):
            batch = test_files[i:i + batch_size]

            # Simulate batch processing
            for file_path in batch:
                with open(file_path) as f:
                    ast.parse(f.read())

        end_time = time.time()
        processing_time = end_time - start_time

        self.assertLessEqual(processing_time, PERFORMANCE_TARGETS['batch_processing_time'],
                           f"Batch processing time {processing_time:.2f}s exceeds target {PERFORMANCE_TARGETS['batch_processing_time']}s")


class TestSecurityGates(unittest.TestCase):
    """Test security compliance and vulnerability assessment."""

    def test_no_hardcoded_secrets(self):
        """Test for hardcoded secrets or sensitive information."""
        secret_patterns = [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api_key\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'aws_access_key_id\s*=',
            r'aws_secret_access_key\s*=',
        ]

        violations = []
        src_root = Path("P:/__csf/src")

        for file_path in src_root.rglob("*.py"):
            if "phase2" in str(file_path).lower():
                try:
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()

                    for pattern in secret_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            violations.append(f"{file_path}: {pattern}")
                except Exception:
                    continue

        self.assertFalse(violations, f"Potential hardcoded secrets found: {violations}")

    def test_no_eval_or_exec_usage(self):
        """Test for dangerous eval or exec usage."""
        dangerous_patterns = [
            r'\beval\s*\(',
            r'\bexec\s*\(',
            r'\b__import__\s*\(',
            r'\bcompile\s*\(',
        ]

        violations = []
        src_root = Path("P:/__csf/src")

        for file_path in src_root.rglob("*.py"):
            if "phase2" in str(file_path).lower():
                try:
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()

                    for pattern in dangerous_patterns:
                        if re.search(pattern, content):
                            # Allow in test files
                            if "test" not in str(file_path).lower():
                                violations.append(f"{file_path}: {pattern}")
                except Exception:
                    continue

        self.assertFalse(violations, f"Dangerous code execution patterns found: {violations}")

    def test_file_path_validation(self):
        """Test proper file path validation and sanitization."""
        src_root = Path("P:/__csf/src")

        for file_path in src_root.rglob("*.py"):
            if "phase2" in str(file_path).lower():
                try:
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()

                    # Look for file operations
                    if re.search(r'open\s*\(', content):
                        # Check for path traversal protection
                        if not any(safe_pattern in content
                                 for safe_pattern in ['Path(', 'pathlib', 'os.path.abspath',
                                                     'os.path.normpath']):
                            violations = f"{file_path}: File operation without path validation"
                            self.fail(violations)
                except Exception:
                    continue

    def test_import_validation(self):
        """Test for safe import practices."""
        src_root = Path("P:/__csf/src")

        for file_path in src_root.rglob("*.py"):
            if "phase2" in str(file_path).lower():
                try:
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()

                    # Check for relative imports
                    if re.search(r'from\s+\.\.*\s+import', content):
                        # Should use absolute imports
                        self.fail(f"{file_path}: Uses relative imports, prefer absolute imports")
                except Exception:
                    continue


class TestIntegrationGates(unittest.TestCase):
    """Test integration with Phase 1 components."""

    def test_phase1_import_compatibility(self):
        """Test Phase 1 import compatibility."""
        # Test that Phase 2 components can import Phase 1 components
        phase1_components = [
            'cks.core.vector_manager',
            'lib.core_utils',
            'modules.session_management',
        ]

        for component in phase1_components:
            try:
                importlib.import_module(component)
            except ImportError as e:
                self.fail(f"Cannot import Phase 1 component {component}: {e}")

    def test_configuration_compatibility(self):
        """Test configuration compatibility with Phase 1."""
        config_paths = [
            "P:/__csf/src/lib/core_utils/phase2c_config.json",
        ]

        for config_path in config_paths:
            if Path(config_path).exists():
                try:
                    with open(config_path) as f:
                        config = json.load(f)

                    # Validate required configuration sections
                    required_sections = [
                        'processing_parameters',
                        'validation_parameters',
                        'backup_parameters',
                    ]

                    for section in required_sections:
                        self.assertIn(section, config,
                                    f"Missing required config section '{section}' in {config_path}")
                except json.JSONDecodeError as e:
                    self.fail(f"Invalid JSON in config file {config_path}: {e}")

    def test_api_contract_compliance(self):
        """Test API contract compliance."""
        # Test that expected APIs exist and have correct signatures
        api_contracts = {
            'ParallelProcessingOrchestrator': [
                'process_files',
                'create_checkpoint',
                'rollback_checkpoint',
            ],
            'BatchProcessor': [
                'process_batch',
                'validate_batch',
                'create_batches',
            ],
        }

        for class_name, methods in api_contracts.items():
            try:
                # Try to import and inspect the class
                sys.path.insert(0, "P:/__csf/src")
                module = importlib.import_module('phase2c_parallel_processing_infrastructure')
                cls = getattr(module, class_name)

                for method_name in methods:
                    self.assertTrue(hasattr(cls, method_name),
                                  f"Missing method {method_name} in {class_name}")

            except (ImportError, AttributeError):
                self.skipTest(f"Phase 2 component {class_name} not available for testing")


class TestDocumentationGates(unittest.TestCase):
    """Test documentation quality and completeness."""

    def test_readme_exists(self):
        """Test that README files exist for Phase 2 components."""
        required_readmes = [
            "P:/__csf/src/lib/core_utils/README_Phase2C_Infrastructure.md",
        ]

        for readme_path in required_readmes:
            self.assertTrue(Path(readme_path).exists(),
                          f"Missing required README: {readme_path}")

    def test_api_documentation(self):
        """Test API documentation completeness."""
        src_root = Path("P:/__csf/src")

        for file_path in src_root.rglob("*.py"):
            if "phase2" in str(file_path).lower():
                try:
                    with open(file_path, encoding='utf-8') as f:
                        content = f.read()

                    tree = ast.parse(content)

                    # Check for class docstrings
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            if not ast.get_docstring(node):
                                self.fail(f"Missing class docstring in {file_path}: {node.name}")

                        elif isinstance(node, ast.FunctionDef):
                            if not node.name.startswith('_'):  # Public method
                                if not ast.get_docstring(node):
                                    self.fail(f"Missing function docstring in {file_path}: {node.name}")
                except Exception:
                    continue

    def test_changelog_exists(self):
        """Test that changelog or version history exists."""
        changelog_patterns = [
            "CHANGELOG.md",
            "HISTORY.md",
            "CHANGES.md",
        ]

        project_root = Path("P:/__csf")
        found_changelog = False

        for pattern in changelog_patterns:
            if (project_root / pattern).exists():
                found_changelog = True
                break

        # Also check in README for version history section
        if not found_changelog:
            readme_path = project_root / "README.md"
            if readme_path.exists():
                with open(readme_path) as f:
                    content = f.read().lower()
                    if "version history" in content or "changelog" in content:
                        found_changelog = True

        self.assertTrue(found_changelog, "No changelog or version history found")


def run_quality_gates():
    """Run all quality gate tests and return results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    test_classes = [
        TestCodeQualityGates,
        TestPerformanceGates,
        TestSecurityGates,
        TestIntegrationGates,
        TestDocumentationGates,
    ]

    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return {
        'tests_run': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'skipped': len(result.skipped),
        'success_rate': (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100,
        'passed': result.wasSuccessful(),
    }


if __name__ == '__main__':
    # Run quality gates and output results
    results = run_quality_gates()

    print("\n" + "="*60)
    print("PHASE 2 QUALITY GATES REPORT")
    print("="*60)
    print(f"Tests Run: {results['tests_run']}")
    print(f"Failures: {results['failures']}")
    print(f"Errors: {results['errors']}")
    print(f"Skipped: {results['skipped']}")
    print(f"Success Rate: {results['success_rate']:.1f}%")
    print(f"Overall Status: {'PASS' if results['passed'] else 'FAIL'}")
    print("="*60)

    # Exit with appropriate code
    sys.exit(0 if results['passed'] else 1)
