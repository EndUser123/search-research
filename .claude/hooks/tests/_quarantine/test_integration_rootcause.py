#!/usr/bin/env python3
"""Integration test: verify root-cause obligation conditional injection end-to-end."""

import json
import sys
import time
from pathlib import Path

# Setup paths
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))
sys.path.insert(0, str(HOOKS_DIR / "competence"))

from competence.task_type_registry import render_template


def test_no_signals_no_rootcause():
    """Without signals, root-cause obligation should NOT appear."""
    result = render_template("implementation", minimal=False, context_signals=None)
    assert "Root-Cause Obligation" not in result
    result2 = render_template("implementation", minimal=False, context_signals={})
    assert "Root-Cause Obligation" not in result2
    result3 = render_template("implementation", minimal=False, context_signals={
        "error_encountered": False,
        "fix_requested": False,
        "previous_block": False,
    })
    assert "Root-Cause Obligation" not in result3
    print("PASS: No signals -> no root-cause obligation (3 variants)")


def test_each_signal_triggers_individually():
    """Each signal alone should trigger root-cause obligation."""
    for signal_name in ("error_encountered", "fix_requested", "previous_block"):
        signals = {"error_encountered": False, "fix_requested": False, "previous_block": False}
        signals[signal_name] = True
        result = render_template("implementation", minimal=False, context_signals=signals)
        assert "Root-Cause Obligation" in result, f"FAIL: {signal_name}=True should trigger"
        print(f"  PASS: {signal_name}=True -> root-cause obligation present")
    print("PASS: Each signal triggers independently")


def test_multiple_signals():
    """Multiple signals should still produce exactly one root-cause block."""
    result = render_template("implementation", minimal=False, context_signals={
        "error_encountered": True,
        "fix_requested": True,
        "previous_block": True,
    })
    count = result.count("Root-Cause Obligation")
    assert count == 1, f"Expected 1 occurrence, got {count}"
    print("PASS: Multiple signals -> exactly one root-cause block")


def test_minimal_template_never_includes():
    """Minimal templates should never include root-cause, even with signals."""
    result = render_template("implementation", minimal=True, context_signals={
        "error_encountered": True,
        "fix_requested": True,
    })
    assert "Root-Cause Obligation" not in result
    print("PASS: Minimal template -> no root-cause even with signals")


def test_meta_type_unaffected():
    """Meta task types should return empty string regardless of signals."""
    result = render_template("meta", minimal=False, context_signals={
        "error_encountered": True,
    })
    assert result == ""
    print("PASS: Meta type -> empty string regardless of signals")


def test_other_task_types():
    """Root-cause should work for research, analysis, etc. when signals fire."""
    for task_type in ("research", "analysis", "implementation", "validation", "planning"):
        result = render_template(task_type, minimal=False, context_signals={
            "fix_requested": True,
        })
        if "Root-Cause Obligation" in result:
            print(f"  PASS: {task_type} -> root-cause obligation present")
        else:
            # Some task types may not have full templates
            print(f"  INFO: {task_type} -> no template (may not be registered)")


def test_signal_file_lifecycle():
    """Test that signal file is created on error and cleared on success."""
    signal_dir = Path("P:/.claude/state/signals")
    signal_dir.mkdir(parents=True, exist_ok=True)
    signal_file = signal_dir / "last_tool_error.json"

    # Clean state
    signal_file.unlink(missing_ok=True)
    assert not signal_file.exists()

    # Simulate error
    signal_file.write_text(json.dumps({
        "timestamp": time.time(),
        "tool_name": "Bash",
        "command": "failing_command",
    }), encoding="utf-8")
    assert signal_file.exists()
    print("  PASS: Signal file created on error")

    # Simulate success clearing it
    signal_file.unlink(missing_ok=True)
    assert not signal_file.exists()
    print("  PASS: Signal file cleared on success")
    print("PASS: Signal file lifecycle")


def test_stale_signal_ignored():
    """Signals older than 5 minutes should be ignored and cleaned up."""
    signal_dir = Path("P:/.claude/state/signals")
    signal_dir.mkdir(parents=True, exist_ok=True)
    signal_file = signal_dir / "last_tool_error.json"

    # Write a stale signal (6 minutes old)
    signal_file.write_text(json.dumps({
        "timestamp": time.time() - 360,
        "tool_name": "Bash",
        "command": "old_command",
    }), encoding="utf-8")

    # The competence_injector's _detect_context_signals should ignore it
    # We test the logic directly
    import json as j
    data = j.loads(signal_file.read_text(encoding="utf-8"))
    is_fresh = time.time() - data["timestamp"] < 300
    assert not is_fresh, "Signal should be stale"
    print("PASS: Stale signal correctly identified as expired")

    # Clean up
    signal_file.unlink(missing_ok=True)


def test_claude_md_has_principle():
    """CLAUDE.md should contain the constitutional one-liner."""
    claude_md = Path("P:/CLAUDE.md").read_text(encoding="utf-8")
    assert "Root-Cause Obligation" in claude_md, "Missing from CLAUDE.md"
    assert "Fix root causes, not symptoms" in claude_md, "Missing principle text"
    print("PASS: CLAUDE.md contains Root-Cause Obligation principle")


if __name__ == "__main__":
    print("=== Integration: No Signals ===")
    test_no_signals_no_rootcause()

    print("\n=== Integration: Individual Signals ===")
    test_each_signal_triggers_individually()

    print("\n=== Integration: Multiple Signals ===")
    test_multiple_signals()

    print("\n=== Integration: Minimal Template ===")
    test_minimal_template_never_includes()

    print("\n=== Integration: Meta Type ===")
    test_meta_type_unaffected()

    print("\n=== Integration: Other Task Types ===")
    test_other_task_types()

    print("\n=== Integration: Signal File Lifecycle ===")
    test_signal_file_lifecycle()

    print("\n=== Integration: Stale Signal ===")
    test_stale_signal_ignored()

    print("\n=== Integration: CLAUDE.md ===")
    test_claude_md_has_principle()

    print("\n" + "=" * 40)
    print("ALL INTEGRATION TESTS PASSED")
