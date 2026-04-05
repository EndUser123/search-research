#!/usr/bin/env python3
"""
Unit tests for Stop_ralph_loop.py

Tests:
- Logs state on stop during active loop
- Checks iteration count against MAX_ITERATIONS
- Provides advisory warnings when approaching limit
- Non-blocking (advisory only)
- Respects RALPH_LOOP_BYPASS env var
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


def test_allows_stop_when_no_active_loop():
    """Test that stop is allowed when no loop is active."""
    from Stop_ralph_loop import process_hook

    with tempfile.TemporaryDirectory() as tmpdir:
        # No state file exists - no active loop
        input_data = {
            "session_id": "test_session",
            "terminal_id": "test_terminal",
        }

        # Save original env
        old_bypass = os.environ.get("RALPH_LOOP_BYPASS")
        os.environ["RALPH_LOOP_BYPASS"] = "0"

        try:
            allow, reason, context = process_hook(input_data, state_dir=Path(tmpdir) / "state")
            assert allow is True, "Should allow stop when no loop active"
        finally:
            if old_bypass is not None:
                os.environ["RALPH_LOOP_BYPASS"] = old_bypass
            else:
                del os.environ["RALPH_LOOP_BYPASS"]


def test_logs_state_on_stop_during_loop():
    """Test that state is logged when stopping during active loop."""
    from Stop_ralph_loop import process_hook
    from tdd.tdd_phase_state import TDDPhaseState, TDDPhaseStateManager

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        impl_path.write_text("def foo(): pass")

        # Set up state manager with GREEN phase (active loop)
        manager = TDDPhaseStateManager(
            session_id="test_session",
            terminal_id="test_terminal",
            state_dir=Path(tmpdir) / "state",
        )
        manager.set_phase(str(impl_path), TDDPhaseState.GREEN)

        input_data = {
            "session_id": "test_session",
            "terminal_id": "test_terminal",
        }

        old_bypass = os.environ.get("RALPH_LOOP_BYPASS")
        os.environ["RALPH_LOOP_BYPASS"] = "0"

        try:
            allow, reason, context = process_hook(input_data, state_dir=Path(tmpdir) / "state")
            # Should allow (advisory) but include context about loop state
            assert allow is True, "Should allow stop (advisory)"
            assert context is not None, "Should return context"
            assert "loop_active" in context, "Should include loop_active in context"
        finally:
            if old_bypass is not None:
                os.environ["RALPH_LOOP_BYPASS"] = old_bypass
            else:
                del os.environ["RALPH_LOOP_BYPASS"]


def test_warns_when_approaching_max_iterations():
    """Test that warning is issued when approaching MAX_ITERATIONS."""
    from Stop_ralph_loop import process_hook
    from tdd.tdd_phase_state import TDDPhaseState, TDDPhaseStateManager

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        impl_path.write_text("def foo(): pass")

        manager = TDDPhaseStateManager(
            session_id="test_session",
            terminal_id="test_terminal",
            state_dir=Path(tmpdir) / "state",
        )

        # Set up loop with high iteration count
        manager.set_phase(str(impl_path), TDDPhaseState.RED)
        manager.set_phase(str(impl_path), TDDPhaseState.GREEN)
        # Simulate multiple iterations
        for _ in range(7):
            manager.set_phase(str(impl_path), TDDPhaseState.RED)
            manager.set_phase(str(impl_path), TDDPhaseState.GREEN)

        input_data = {
            "session_id": "test_session",
            "terminal_id": "test_terminal",
        }

        old_bypass = os.environ.get("RALPH_LOOP_BYPASS")
        os.environ["RALPH_LOOP_BYPASS"] = "0"

        try:
            allow, reason, context = process_hook(input_data, state_dir=Path(tmpdir) / "state")
            assert allow is True, "Should allow stop (advisory)"
            assert "warning" in reason.lower() or "iteration" in reason.lower()
        finally:
            if old_bypass is not None:
                os.environ["RALPH_LOOP_BYPASS"] = old_bypass
            else:
                del os.environ["RALPH_LOOP_BYPASS"]


def test_bypass_allows_silent_stop():
    """Test that RALPH_LOOP_BYPASS=1 allows silent stop."""
    from Stop_ralph_loop import process_hook
    from tdd.tdd_phase_state import TDDPhaseState, TDDPhaseStateManager

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        impl_path.write_text("def foo(): pass")

        manager = TDDPhaseStateManager(
            session_id="test_session",
            terminal_id="test_terminal",
            state_dir=Path(tmpdir) / "state",
        )
        manager.set_phase(str(impl_path), TDDPhaseState.GREEN)

        input_data = {
            "session_id": "test_session",
            "terminal_id": "test_terminal",
        }

        old_bypass = os.environ.get("RALPH_LOOP_BYPASS")
        os.environ["RALPH_LOOP_BYPASS"] = "1"

        try:
            allow, reason, context = process_hook(input_data, state_dir=Path(tmpdir) / "state")
            assert allow is True, "Should allow stop with bypass"
            assert context is not None
            assert context.get("bypassed") is True
        finally:
            if old_bypass is not None:
                os.environ["RALPH_LOOP_BYPASS"] = old_bypass
            else:
                del os.environ["RALPH_LOOP_BYPASS"]


def test_returns_iteration_count_in_context():
    """Test that iteration count is returned in context."""
    from Stop_ralph_loop import process_hook
    from tdd.tdd_phase_state import TDDPhaseState, TDDPhaseStateManager

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        impl_path.write_text("def foo(): pass")

        manager = TDDPhaseStateManager(
            session_id="test_session",
            terminal_id="test_terminal",
            state_dir=Path(tmpdir) / "state",
        )

        # Create some iterations
        manager.set_phase(str(impl_path), TDDPhaseState.RED)
        manager.set_phase(str(impl_path), TDDPhaseState.GREEN)
        manager.set_phase(str(impl_path), TDDPhaseState.RED)
        manager.set_phase(str(impl_path), TDDPhaseState.GREEN)

        input_data = {
            "session_id": "test_session",
            "terminal_id": "test_terminal",
        }

        old_bypass = os.environ.get("RALPH_LOOP_BYPASS")
        os.environ["RALPH_LOOP_BYPASS"] = "0"

        try:
            allow, reason, context = process_hook(input_data, state_dir=Path(tmpdir) / "state")
            assert context is not None, "Should return context"
            assert "iterations" in context, "Should include iterations count"
        finally:
            if old_bypass is not None:
                os.environ["RALPH_LOOP_BYPASS"] = old_bypass
            else:
                del os.environ["RALPH_LOOP_BYPASS"]


def test_identifies_active_contract_files():
    """Test that active contract files are identified in context."""
    from Stop_ralph_loop import process_hook
    from tdd.tdd_phase_state import TDDPhaseState, TDDPhaseStateManager

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        impl_path.write_text("def foo(): pass")

        manager = TDDPhaseStateManager(
            session_id="test_session",
            terminal_id="test_terminal",
            state_dir=Path(tmpdir) / "state",
        )
        manager.set_phase(str(impl_path), TDDPhaseState.GREEN)

        input_data = {
            "session_id": "test_session",
            "terminal_id": "test_terminal",
        }

        old_bypass = os.environ.get("RALPH_LOOP_BYPASS")
        os.environ["RALPH_LOOP_BYPASS"] = "0"

        try:
            allow, reason, context = process_hook(input_data, state_dir=Path(tmpdir) / "state")
            assert context is not None
            assert "active_files" in context or "contracts" in context
        finally:
            if old_bypass is not None:
                os.environ["RALPH_LOOP_BYPASS"] = old_bypass
            else:
                del os.environ["RALPH_LOOP_BYPASS"]


def test_multiple_contracts_tracked():
    """Test that multiple contracts are tracked."""
    from Stop_ralph_loop import process_hook
    from tdd.tdd_phase_state import TDDPhaseState, TDDPhaseStateManager

    with tempfile.TemporaryDirectory() as tmpdir:
        impl1 = Path(tmpdir) / "impl1.py"
        impl2 = Path(tmpdir) / "impl2.py"
        impl1.write_text("def foo(): pass")
        impl2.write_text("def bar(): pass")

        manager = TDDPhaseStateManager(
            session_id="test_session",
            terminal_id="test_terminal",
            state_dir=Path(tmpdir) / "state",
        )
        manager.set_phase(str(impl1), TDDPhaseState.GREEN)
        manager.set_phase(str(impl2), TDDPhaseState.RED)

        input_data = {
            "session_id": "test_session",
            "terminal_id": "test_terminal",
        }

        old_bypass = os.environ.get("RALPH_LOOP_BYPASS")
        os.environ["RALPH_LOOP_BYPASS"] = "0"

        try:
            allow, reason, context = process_hook(input_data, state_dir=Path(tmpdir) / "state")
            assert allow is True
            # Should identify multiple active contracts
            if "active_files" in context:
                assert len(context["active_files"]) >= 2
        finally:
            if old_bypass is not None:
                os.environ["RALPH_LOOP_BYPASS"] = old_bypass
            else:
                del os.environ["RALPH_LOOP_BYPASS"]


def main():
    """Run all tests."""
    import pytest

    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
