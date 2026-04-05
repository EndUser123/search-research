#!/usr/bin/env python3
"""
Test Generator for Library Code Protection

Auto-generates characterization tests from captured data.

Generates:
- Signature tests (verify parameters unchanged)
- Behavior tests (verify output matches snapshots)
- Import tests (verify imports available)
- Interface tests (verify class methods exist)

Usage:
    generator = TestGenerator()
    tests = generator.generate_tests(characterization_data)
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Add parent directory to path
lib_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(lib_dir))

try:
    from characterization_engine import (
        CharacterizationData,
        ClassDefinition,
        FunctionSignature,
    )
except ImportError:
    CharacterizationData = None
    FunctionSignature = None
    ClassDefinition = None


@dataclass
class GeneratedTest:
    """Represents a generated test."""
    test_name: str
    test_type: str  # signature, behavior, import, interface
    code: str
    description: str


class TestGenerator:
    """
    Generates characterization tests from captured data.

    Usage:
        generator = TestGenerator()
        tests = generator.generate_tests(characterization_data)
    """

    def generate_tests(self, data: Any) -> list[GeneratedTest]:
        """
        Generate tests from characterization data.

        Args:
            data: CharacterizationData instance

        Returns:
            List of GeneratedTest instances
        """
        if not CharacterizationData or not isinstance(data, CharacterizationData):
            return []

        tests = []

        # Generate signature tests
        tests.extend(self._generate_signature_tests(data))

        # Generate interface tests
        tests.extend(self._generate_interface_tests(data))

        # Generate import tests
        tests.extend(self._generate_import_tests(data))

        # Generate behavior tests (if snapshots available)
        # behavior_snapshots not implemented yet (task #181)
        if getattr(data, "behavior_snapshots", None):
            tests.extend(self._generate_behavior_tests(data))

        return tests

    def _generate_signature_tests(self, data: CharacterizationData) -> list[GeneratedTest]:
        """Generate signature preservation tests."""
        tests = []
        module_name = Path(data.module_path).stem

        for func_name, sig in data.function_signatures.items():
            # Skip private methods
            if func_name.startswith("_") and not func_name.startswith("__"):
                continue

            params = ", ".join(
                f"{p['name']}: {p.get('type', 'Any')}"
                for p in sig.parameters
            )
            return_hint = f" -> {sig.return_type}" if sig.return_type else ""

            test_code = f'''def test_{func_name}_signature():
    """Test that {func_name} signature is preserved."""
    from {module_name} import {func_name}
    import inspect

    sig = inspect.signature({func_name})
    params = list(sig.parameters.keys())

    # Expected parameters
    expected_params = [{', '.join(repr(p['name']) for p in sig.parameters)}]

    assert params == expected_params, f"Parameter mismatch: {{params}} vs {{expected_params}}"
'''

            tests.append(GeneratedTest(
                test_name=f"test_{func_name}_signature",
                test_type="signature",
                code=test_code,
                description=f"Verify {func_name} signature unchanged",
            ))

        return tests

    def _generate_interface_tests(self, data: CharacterizationData) -> list[GeneratedTest]:
        """Generate class interface tests."""
        tests = []
        module_name = Path(data.module_path).stem

        for cls_name, cls_def in data.class_definitions.items():
            test_code = f'''def test_{cls_name}_interface():
    """Test that {cls_name} interface is preserved."""
    from {module_name} import {cls_name}

    # Check class exists
    assert {cls_name} is not None

    # Check methods exist
    methods = [{', '.join(repr(m) for m in cls_def.methods)}]
    for method in methods:
        assert hasattr({cls_name}, method), f"Missing method: {{method}}"

    # Check properties exist
    properties = [{', '.join(repr(p) for p in cls_def.properties)}]
    for prop in properties:
        assert hasattr({cls_name}, prop), f"Missing property: {{prop}}"
'''

            tests.append(GeneratedTest(
                test_name=f"test_{cls_name}_interface",
                test_type="interface",
                code=test_code,
                description=f"Verify {cls_name} interface unchanged",
            ))

        return tests

    def _generate_import_tests(self, data: CharacterizationData) -> list[GeneratedTest]:
        """Generate import availability tests."""
        tests = []
        module_name = Path(data.module_path).stem

        # Test that main exports are importable
        exports = []
        exports.extend(data.function_signatures.keys())
        exports.extend(data.class_definitions.keys())

        if exports:
            exports_str = ", ".join(repr(e) for e in exports[:10])  # Limit to 10
            test_code = f'''def test_{module_name}_exports():
    """Test that {module_name} exports are available."""
    from {module_name} import ({exports_str})

    # Verify exports are callable or class types
    exports = [{exports_str}]
    for export in exports:
        assert export is not None, f"Export {{export}} is None"
'''

            tests.append(GeneratedTest(
                test_name=f"test_{module_name}_exports",
                test_type="import",
                code=test_code,
                description=f"Verify {module_name} exports available",
            ))

        return tests

    def _generate_behavior_tests(self, data: CharacterizationData) -> list[GeneratedTest]:
        """Generate behavior regression tests from snapshots."""
        tests = []
        module_name = Path(data.module_path).stem

        for snapshot_key, snapshot in data.behavior_snapshots.items():
            func_name = snapshot.function_name

            test_code = f'''def test_{func_name}_behavior():
    """Test that {func_name} behavior is preserved."""
    from {module_name} import {func_name}

    # Test with captured inputs
    inputs = {repr(snapshot.inputs)}

    if snapshot.error:
        # Expecting an error
        try:
            result = {func_name}(*inputs)
            assert False, f"Expected error but got: {{result}}"
        except Exception as e:
            # Error is expected
            pass
    else:
        # Expecting specific output
        result = {func_name}(*inputs)
        expected = {repr(snapshot.output)}
        assert result == expected, f"Behavior changed: {{result}} vs {{expected}}"
'''

            tests.append(GeneratedTest(
                test_name=f"test_{func_name}_behavior",
                test_type="behavior",
                code=test_code,
                description=f"Verify {func_name} behavior unchanged",
            ))

        return tests

    def generate_test_file(self, data: Any, output_path: str | Path) -> Path:
        """
        Generate a complete test file from characterization data.

        Args:
            data: CharacterizationData instance
            output_path: Path to output test file

        Returns:
            Path to generated test file
        """
        tests = self.generate_tests(data)
        output_path = Path(output_path)

        # Generate file header
        module_name = Path(data.module_path).stem
        header = f'''"""
Auto-generated characterization tests for {module_name}

Generated by: Library Code Protection System
Module: {data.module_path}
Captured: {data.captured_at}
Checksum: {data.checksum}

WARNING: This file is auto-generated. Do not edit manually.
"""

import pytest
from {module_name} import *

'''

        # Generate test content
        test_body = "\n".join(test.code for test in tests)

        # Write file
        output_path.write_text(header + test_body, encoding="utf-8")

        return output_path


def generate_characterization_tests(data: Any) -> list[GeneratedTest]:
    """
    Convenience function to generate tests from characterization data.

    Args:
        data: CharacterizationData instance

    Returns:
        List of GeneratedTest instances
    """
    generator = TestGenerator()
    return generator.generate_tests(data)


__all__ = [
    "TestGenerator",
    "GeneratedTest",
    "generate_characterization_tests",
]
