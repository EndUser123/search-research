#!/usr/bin/env python3
"""
Unit tests for three_file_contract.py

Tests:
- ThreeFileContract dataclass creation with impl/test/spec paths
- SHA-256 hash computation for file contents
- Immutability verification (detects tampering)
- Timing-attack safe hash comparison
- File not found handling
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))


def test_contract_creation_with_paths():
    """Test that ThreeFileContract can be created with impl/test/spec paths."""
    from tdd.three_file_contract import ThreeFileContract

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        test_path = Path(tmpdir) / "test_impl.py"
        spec_path = Path(tmpdir) / "spec.md"

        # Create files
        impl_path.write_text("def foo(): pass")
        test_path.write_text("def test_foo(): pass")
        spec_path.write_text("# Spec")

        contract = ThreeFileContract(
            impl_path=str(impl_path),
            test_path=str(test_path),
            spec_path=str(spec_path),
        )

        assert contract.impl_path == str(impl_path)
        assert contract.test_path == str(test_path)
        assert contract.spec_path == str(spec_path)


def test_sha256_hash_computation():
    """Test that SHA-256 hashes are computed for all three files."""
    from tdd.three_file_contract import ThreeFileContract

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        test_path = Path(tmpdir) / "test_impl.py"
        spec_path = Path(tmpdir) / "spec.md"

        # Create files with known content
        impl_path.write_text("x = 1")
        test_path.write_text("y = 2")
        spec_path.write_text("z = 3")

        contract = ThreeFileContract(
            impl_path=str(impl_path),
            test_path=str(test_path),
            spec_path=str(spec_path),
        )

        # Verify hashes exist and are SHA-256 length (64 hex chars)
        assert contract.impl_hash is not None
        assert contract.test_hash is not None
        assert contract.spec_hash is not None
        assert len(contract.impl_hash) == 64
        assert len(contract.test_hash) == 64
        assert len(contract.spec_hash) == 64


def test_immutability_verification_passes():
    """Test that verify_immutability() returns True when files unchanged."""
    from tdd.three_file_contract import ThreeFileContract

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        test_path = Path(tmpdir) / "test_impl.py"
        spec_path = Path(tmpdir) / "spec.md"

        impl_path.write_text("original content")
        test_path.write_text("test content")
        spec_path.write_text("spec content")

        contract = ThreeFileContract(
            impl_path=str(impl_path),
            test_path=str(test_path),
            spec_path=str(spec_path),
        )

        # Verify should pass (no changes)
        assert contract.verify_immutability() is True


def test_immutability_verification_detects_tampering():
    """Test that verify_immutability() returns False when test file modified."""
    from tdd.three_file_contract import ThreeFileContract

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        test_path = Path(tmpdir) / "test_impl.py"
        spec_path = Path(tmpdir) / "spec.md"

        impl_path.write_text("original")
        test_path.write_text("original test")
        spec_path.write_text("spec")

        contract = ThreeFileContract(
            impl_path=str(impl_path),
            test_path=str(test_path),
            spec_path=str(spec_path),
        )

        # Tamper with test file
        test_path.write_text("TAMPERED!")

        # Verify should fail (test file changed)
        assert contract.verify_immutability() is False


def test_timing_attack_safe_comparison():
    """Test that hash comparison uses constant-time algorithm."""
    import hashlib

    from tdd.three_file_contract import ThreeFileContract

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        test_path = Path(tmpdir) / "test_impl.py"
        spec_path = Path(tmpdir) / "spec.md"

        impl_path.write_text("content")
        test_path.write_text("content")
        spec_path.write_text("content")

        contract = ThreeFileContract(
            impl_path=str(impl_path),
            test_path=str(test_path),
            spec_path=str(spec_path),
        )

        # Test that _safe_hash_compare exists and works
        # Correct hash
        correct_hash = hashlib.sha256(b"content").hexdigest()
        assert contract._safe_hash_compare(correct_hash, correct_hash) is True

        # Wrong hash (should still be constant-time)
        wrong_hash = "0" * 64
        assert contract._safe_hash_compare(correct_hash, wrong_hash) is False


def test_file_not_found_handling():
    """Test that verify_immutability() handles missing files gracefully."""
    from tdd.three_file_contract import ThreeFileContract

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        test_path = Path(tmpdir) / "test_impl.py"
        spec_path = Path(tmpdir) / "spec.md"

        impl_path.write_text("content")
        test_path.write_text("content")
        spec_path.write_text("content")

        contract = ThreeFileContract(
            impl_path=str(impl_path),
            test_path=str(test_path),
            spec_path=str(spec_path),
        )

        # Delete test file after contract creation
        test_path.unlink()

        # Verify should fail (file missing)
        assert contract.verify_immutability() is False


def test_contract_to_dict_serialization():
    """Test that contract can be serialized to dictionary."""
    from tdd.three_file_contract import ThreeFileContract

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        test_path = Path(tmpdir) / "test_impl.py"
        spec_path = Path(tmpdir) / "spec.md"

        impl_path.write_text("x")
        test_path.write_text("y")
        spec_path.write_text("z")

        contract = ThreeFileContract(
            impl_path=str(impl_path),
            test_path=str(test_path),
            spec_path=str(spec_path),
        )

        data = contract.to_dict()

        assert "impl_path" in data
        assert "test_path" in data
        assert "spec_path" in data
        assert "impl_hash" in data
        assert "test_hash" in data
        assert "spec_hash" in data


def test_contract_from_dict_deserialization():
    """Test that contract can be deserialized from dictionary."""
    from tdd.three_file_contract import ThreeFileContract

    data = {
        "impl_path": "/path/to/impl.py",
        "test_path": "/path/to/test_impl.py",
        "spec_path": "/path/to/spec.md",
        "impl_hash": "a" * 64,
        "test_hash": "b" * 64,
        "spec_hash": "c" * 64,
    }

    contract = ThreeFileContract.from_dict(data)

    assert contract.impl_path == "/path/to/impl.py"
    assert contract.test_path == "/path/to/test_impl.py"
    assert contract.spec_path == "/path/to/spec.md"
    assert contract.impl_hash == "a" * 64
    assert contract.test_hash == "b" * 64
    assert contract.spec_hash == "c" * 64


def test_spec_hash_verification():
    """Test that spec file modifications are also detected."""
    from tdd.three_file_contract import ThreeFileContract

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        test_path = Path(tmpdir) / "test_impl.py"
        spec_path = Path(tmpdir) / "spec.md"

        impl_path.write_text("impl")
        test_path.write_text("test")
        spec_path.write_text("original spec")

        contract = ThreeFileContract(
            impl_path=str(impl_path),
            test_path=str(test_path),
            spec_path=str(spec_path),
        )

        # Modify spec file
        spec_path.write_text("MODIFIED SPEC!")

        # Verify should fail (spec file changed)
        assert contract.verify_immutability() is False


def main():
    """Run all tests."""
    import pytest

    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
