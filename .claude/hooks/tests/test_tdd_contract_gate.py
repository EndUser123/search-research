#!/usr/bin/env python3
"""
Unit tests for PreToolUse_tdd_contract_gate.py

Tests:
- Blocks edits to test files during GREEN phase
- Allows test edits only in RED phase
- Allows impl edits in RED, GREEN, REFACTOR phases
- Respects TDD_CONTRACT_BYPASS env var
- Integration with TDDPhaseStateManager
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))


def test_allows_test_edits_in_red_phase():
    """Test that test file edits are allowed during RED phase."""
    from PreToolUse_tdd_contract_gate import process_hook
    from tdd.tdd_phase_state import TDDPhaseState, TDDPhaseStateManager

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        test_path = Path(tmpdir) / "test_impl.py"

        impl_path.write_text("def foo(): pass")
        test_path.write_text("def test_foo(): pass")

        # Set up state manager with RED phase
        manager = TDDPhaseStateManager(
            session_id="test_session",
            terminal_id="test_terminal",
            state_dir=Path(tmpdir) / "state",
        )
        manager.set_phase(str(impl_path), TDDPhaseState.RED)

        # Process edit to test file
        input_data = {
            "name": "Edit",
            "tool_input": {
                "file_path": str(test_path),
                "old_string": "pass",
                "new_string": "assert True",
            },
            "session_id": "test_session",
            "terminal_id": "test_terminal",
        }

        # Save original env
        old_bypass = os.environ.get("TDD_CONTRACT_BYPASS")
        os.environ["TDD_CONTRACT_BYPASS"] = "0"

        try:
            allow, reason, context = process_hook(input_data, state_dir=Path(tmpdir) / "state")
            assert allow is True, f"Should allow test edit in RED phase, got: {reason}"
        finally:
            if old_bypass is not None:
                os.environ["TDD_CONTRACT_BYPASS"] = old_bypass
            else:
                del os.environ["TDD_CONTRACT_BYPASS"]


def test_blocks_test_edits_in_green_phase():
    """Test that test file edits are blocked during GREEN phase."""
    from PreToolUse_tdd_contract_gate import process_hook
    from tdd.tdd_phase_state import TDDPhaseState, TDDPhaseStateManager

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        test_path = Path(tmpdir) / "test_impl.py"

        impl_path.write_text("def foo(): return 1")
        test_path.write_text("def test_foo(): assert foo() == 1")

        # Set up state manager with GREEN phase
        manager = TDDPhaseStateManager(
            session_id="test_session",
            terminal_id="test_terminal",
            state_dir=Path(tmpdir) / "state",
        )
        manager.set_phase(str(impl_path), TDDPhaseState.GREEN)

        # Process edit to test file
        input_data = {
            "name": "Edit",
            "tool_input": {
                "file_path": str(test_path),
                "old_string": "assert foo() == 1",
                "new_string": "assert foo() == 2",
            },
            "session_id": "test_session",
            "terminal_id": "test_terminal",
        }

        # Save original env
        old_bypass = os.environ.get("TDD_CONTRACT_BYPASS")
        os.environ["TDD_CONTRACT_BYPASS"] = "0"

        try:
            allow, reason, context = process_hook(input_data, state_dir=Path(tmpdir) / "state")
            assert allow is False, "Should block test edit in GREEN phase"
            assert "GREEN" in reason or "test" in reason.lower()
        finally:
            if old_bypass is not None:
                os.environ["TDD_CONTRACT_BYPASS"] = old_bypass
            else:
                del os.environ["TDD_CONTRACT_BYPASS"]


def test_blocks_test_edits_in_refactor_phase():
    """Test that test file edits are blocked during REFACTOR phase."""
    from PreToolUse_tdd_contract_gate import process_hook
    from tdd.tdd_phase_state import TDDPhaseState, TDDPhaseStateManager

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        test_path = Path(tmpdir) / "test_impl.py"

        impl_path.write_text("def foo(): return 1")
        test_path.write_text("def test_foo(): assert foo() == 1")

        # Set up state manager with REFACTOR phase
        manager = TDDPhaseStateManager(
            session_id="test_session",
            terminal_id="test_terminal",
            state_dir=Path(tmpdir) / "state",
        )
        manager.set_phase(str(impl_path), TDDPhaseState.GREEN)
        manager.set_phase(str(impl_path), TDDPhaseState.REFACTOR)

        # Process edit to test file
        input_data = {
            "name": "Edit",
            "tool_input": {
                "file_path": str(test_path),
                "old_string": "assert foo() == 1",
                "new_string": "assert foo() == 2",
            },
            "session_id": "test_session",
            "terminal_id": "test_terminal",
        }

        # Save original env
        old_bypass = os.environ.get("TDD_CONTRACT_BYPASS")
        os.environ["TDD_CONTRACT_BYPASS"] = "0"

        try:
            allow, reason, context = process_hook(input_data, state_dir=Path(tmpdir) / "state")
            assert allow is False, "Should block test edit in REFACTOR phase"
        finally:
            if old_bypass is not None:
                os.environ["TDD_CONTRACT_BYPASS"] = old_bypass
            else:
                del os.environ["TDD_CONTRACT_BYPASS"]


def test_allows_impl_edits_in_green_phase():
    """Test that impl file edits are allowed during GREEN phase."""
    from PreToolUse_tdd_contract_gate import process_hook
    from tdd.tdd_phase_state import TDDPhaseState, TDDPhaseStateManager

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        test_path = Path(tmpdir) / "test_impl.py"

        impl_path.write_text("def foo(): pass")
        test_path.write_text("def test_foo(): assert foo() == 1")

        # Set up state manager with GREEN phase
        manager = TDDPhaseStateManager(
            session_id="test_session",
            terminal_id="test_terminal",
            state_dir=Path(tmpdir) / "state",
        )
        manager.set_phase(str(impl_path), TDDPhaseState.GREEN)

        # Process edit to impl file
        input_data = {
            "name": "Edit",
            "tool_input": {
                "file_path": str(impl_path),
                "old_string": "pass",
                "new_string": "return 1",
            },
            "session_id": "test_session",
            "terminal_id": "test_terminal",
        }

        # Save original env
        old_bypass = os.environ.get("TDD_CONTRACT_BYPASS")
        os.environ["TDD_CONTRACT_BYPASS"] = "0"

        try:
            allow, reason, context = process_hook(input_data, state_dir=Path(tmpdir) / "state")
            assert allow is True, f"Should allow impl edit in GREEN phase, got: {reason}"
        finally:
            if old_bypass is not None:
                os.environ["TDD_CONTRACT_BYPASS"] = old_bypass
            else:
                del os.environ["TDD_CONTRACT_BYPASS"]


def test_allows_impl_edits_in_refactor_phase():
    """Test that impl file edits are allowed during REFACTOR phase."""
    from PreToolUse_tdd_contract_gate import process_hook
    from tdd.tdd_phase_state import TDDPhaseState, TDDPhaseStateManager

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        test_path = Path(tmpdir) / "test_impl.py"

        impl_path.write_text("def foo(): return 1")
        test_path.write_text("def test_foo(): assert foo() == 1")

        # Set up state manager with REFACTOR phase
        manager = TDDPhaseStateManager(
            session_id="test_session",
            terminal_id="test_terminal",
            state_dir=Path(tmpdir) / "state",
        )
        manager.set_phase(str(impl_path), TDDPhaseState.GREEN)
        manager.set_phase(str(impl_path), TDDPhaseState.REFACTOR)

        # Process edit to impl file
        input_data = {
            "name": "Edit",
            "tool_input": {
                "file_path": str(impl_path),
                "old_string": "return 1",
                "new_string": "return 1  # optimized",
            },
            "session_id": "test_session",
            "terminal_id": "test_terminal",
        }

        # Save original env
        old_bypass = os.environ.get("TDD_CONTRACT_BYPASS")
        os.environ["TDD_CONTRACT_BYPASS"] = "0"

        try:
            allow, reason, context = process_hook(input_data, state_dir=Path(tmpdir) / "state")
            assert allow is True, f"Should allow impl edit in REFACTOR phase, got: {reason}"
        finally:
            if old_bypass is not None:
                os.environ["TDD_CONTRACT_BYPASS"] = old_bypass
            else:
                del os.environ["TDD_CONTRACT_BYPASS"]


def test_bypass_allows_all_edits():
    """Test that TDD_CONTRACT_BYPASS=1 allows all edits."""
    from PreToolUse_tdd_contract_gate import process_hook
    from tdd.tdd_phase_state import TDDPhaseState, TDDPhaseStateManager

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        test_path = Path(tmpdir) / "test_impl.py"

        impl_path.write_text("def foo(): pass")
        test_path.write_text("def test_foo(): pass")

        # Set up state manager with GREEN phase
        manager = TDDPhaseStateManager(
            session_id="test_session",
            terminal_id="test_terminal",
            state_dir=Path(tmpdir) / "state",
        )
        manager.set_phase(str(impl_path), TDDPhaseState.GREEN)

        # Process edit to test file with bypass
        input_data = {
            "name": "Edit",
            "tool_input": {
                "file_path": str(test_path),
                "old_string": "pass",
                "new_string": "assert True",
            },
            "session_id": "test_session",
            "terminal_id": "test_terminal",
        }

        # Save original env
        old_bypass = os.environ.get("TDD_CONTRACT_BYPASS")
        os.environ["TDD_CONTRACT_BYPASS"] = "1"

        try:
            allow, reason, context = process_hook(input_data, state_dir=Path(tmpdir) / "state")
            assert allow is True, "Should allow test edit with bypass"
            assert context is not None
            assert context.get("bypassed") is True
        finally:
            if old_bypass is not None:
                os.environ["TDD_CONTRACT_BYPASS"] = old_bypass
            else:
                del os.environ["TDD_CONTRACT_BYPASS"]


def test_non_contract_files_allowed():
    """Test that files not in a contract are always allowed."""
    from PreToolUse_tdd_contract_gate import process_hook

    with tempfile.TemporaryDirectory() as tmpdir:
        # File not associated with any contract
        other_path = Path(tmpdir) / "other.py"
        other_path.write_text("print('hello')")

        # Process edit to non-contract file
        input_data = {
            "name": "Edit",
            "tool_input": {
                "file_path": str(other_path),
                "old_string": "print('hello')",
                "new_string": "print('world')",
            },
            "session_id": "test_session",
            "terminal_id": "test_terminal",
        }

        # Save original env
        old_bypass = os.environ.get("TDD_CONTRACT_BYPASS")
        os.environ["TDD_CONTRACT_BYPASS"] = "0"

        try:
            allow, reason, context = process_hook(input_data, state_dir=Path(tmpdir) / "state")
            assert allow is True, "Should allow edit to non-contract file"
        finally:
            if old_bypass is not None:
                os.environ["TDD_CONTRACT_BYPASS"] = old_bypass
            else:
                del os.environ["TDD_CONTRACT_BYPASS"]


def test_test_file_detection():
    """Test that test files are correctly identified."""
    from PreToolUse_tdd_contract_gate import _is_test_file

    # Test patterns
    assert _is_test_file(Path("test_foo.py")) is True
    assert _is_test_file(Path("tests/test_bar.py")) is True
    assert _is_test_file(Path("foo_test.py")) is True
    assert _is_test_file(Path("conftest.py")) is True

    # Non-test patterns
    assert _is_test_file(Path("foo.py")) is False
    assert _is_test_file(Path("impl.py")) is False
    assert _is_test_file(Path("README.md")) is False


def test_impl_file_detection():
    """Test that impl files are correctly identified from test files."""
    from PreToolUse_tdd_contract_gate import _get_impl_for_test

    # Standard patterns
    impl = _get_impl_for_test(Path("test_foo.py"))
    assert impl == Path("foo.py")

    impl = _get_impl_for_test(Path("tests/test_bar.py"))
    assert impl == Path("bar.py") or impl == Path("tests/bar.py")

    # Edge case: no test_ prefix
    impl = _get_impl_for_test(Path("foo_test.py"))
    assert impl == Path("foo.py")


def main():
    """Run all tests."""
    import pytest

    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
