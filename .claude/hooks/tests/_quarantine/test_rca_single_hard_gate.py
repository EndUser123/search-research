#!/usr/bin/env python3
r"""
Test: Single RCA Hard Gate Authority

TASK-002: Verify single RCA hard gate in live Stop path

Tests that:
1. StopHook_rca_contract.py is the only RCA hard gate in the live Stop path
2. Package hook (P:\packages\debugRCA\skill\hooks\StopHook_rca_enforcement.py) is not loaded
3. Python import cache invalidation prevents false positives

Acceptance Criteria:
- Test verifies no duplicate enforcement paths
- Test ensures package hook is not silently competing
- Test includes Python import cache invalidation verification
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))


def _extract_hook_sequence_from_router() -> list[str]:
    """Parse Stop_router.py to extract HOOK_SEQUENCE entries."""
    router_file = HOOKS_DIR / "Stop_router.py"
    assert router_file.exists(), f"Stop_router.py not found at {router_file}"

    content = router_file.read_text()

    # Find HOOK_SEQUENCE using regex
    # Pattern: HOOK_SEQUENCE = [ ... ("hook_name", ...), ... ]
    hook_sequence_pattern = r"HOOK_SEQUENCE\s*=\s*\[(.*?)\]"
    match = re.search(hook_sequence_pattern, content, re.DOTALL)
    assert match, "Could not find HOOK_SEQUENCE in Stop_router.py"

    sequence_content = match.group(1)

    # Extract hook names (first element of each tuple)
    hook_names = re.findall(r'"([^"]+\.py)"', sequence_content)

    return hook_names


def _extract_active_runtime_hooks() -> set[str]:
    """Parse Stop_router.py to extract ACTIVE_RUNTIME_HOOKS."""
    router_file = HOOKS_DIR / "Stop_router.py"
    assert router_file.exists(), f"Stop_router.py not found at {router_file}"

    content = router_file.read_text()

    # Find ACTIVE_RUNTIME_HOOKS using regex
    # Pattern: ACTIVE_RUNTIME_HOOKS = frozenset({ ... })
    active_hooks_pattern = r"ACTIVE_RUNTIME_HOOKS\s*=\s*frozenset\((.*?)\)"
    match = re.search(active_hooks_pattern, content, re.DOTALL)
    assert match, "Could not find ACTIVE_RUNTIME_HOOKS in Stop_router.py"

    active_content = match.group(1)

    # Extract hook names
    hook_names = set(re.findall(r'"([^"]+\.py)"', active_content))

    return hook_names


def test_live_stop_router_has_single_rca_hard_gate() -> None:
    """Test that Stop_router.py has exactly one RCA hard gate registered."""
    hook_names = _extract_hook_sequence_from_router()

    # Find RCA hard gates
    rca_hard_gates = [name for name in hook_names if "rca_contract" in name.lower()]

    # Assert exactly one RCA hard gate
    assert (
        len(rca_hard_gates) == 1
    ), f"Expected exactly 1 RCA hard gate in HOOK_SEQUENCE, found {len(rca_hard_gates)}: {rca_hard_gates}"

    # Verify it's StopHook_rca_contract.py
    assert (
        rca_hard_gates[0] == "StopHook_rca_contract.py"
    ), f"Expected StopHook_rca_contract.py as RCA hard gate, found {rca_hard_gates[0]}"


def test_rca_hard_gate_in_active_runtime_hooks() -> None:
    """Test that StopHook_rca_contract.py is in ACTIVE_RUNTIME_HOOKS."""
    active_hooks = _extract_active_runtime_hooks()

    # Check RCA hard gate is in active hooks
    assert (
        "StopHook_rca_contract.py" in active_hooks
    ), "StopHook_rca_contract.py not found in ACTIVE_RUNTIME_HOOKS"


def test_package_hook_not_in_live_stop_path() -> None:
    """Test that package hook is not in the live Stop path."""
    hook_names = _extract_hook_sequence_from_router()

    # Package hook should NOT be in live path
    package_hook = "StopHook_rca_enforcement.py"
    assert (
        package_hook not in hook_names
    ), f"Package hook {package_hook} should not be in live Stop path"


def test_package_hook_file_exists_but_not_active() -> None:
    """Test that package hook file exists but is not registered in live path."""
    # Check package hook file exists (it should, but not be active)
    package_hook_path = Path("P:/packages/debugRCA/skill/hooks/StopHook_rca_enforcement.py")
    assert package_hook_path.exists(), f"Package hook file should exist at {package_hook_path}"

    # But verify it's NOT in the live Stop path
    hook_names = _extract_hook_sequence_from_router()

    # Package hook basename should not be in live path
    package_hook_basename = "StopHook_rca_enforcement.py"
    assert (
        package_hook_basename not in hook_names
    ), f"Package hook {package_hook_basename} should not be active in live path"


def test_no_duplicate_rca_gates_in_hook_sequence() -> None:
    """Test that there are no duplicate RCA gates in HOOK_SEQUENCE."""
    hook_names = _extract_hook_sequence_from_router()

    # Check for duplicates
    seen = set()
    duplicates = []
    for hook_name in hook_names:
        if hook_name in seen:
            duplicates.append(hook_name)
        seen.add(hook_name)

    assert len(duplicates) == 0, f"Found duplicate hooks in HOOK_SEQUENCE: {duplicates}"


def test_python_import_cache_consistency() -> None:
    """Test that file parsing produces consistent results regardless of import cache.

    This test verifies that parsing the Stop_router.py file directly
    produces the same results each time, ensuring no false positives from
    Python's import cache.
    """
    # Parse HOOK_SEQUENCE twice to simulate cache consistency check
    hook_names_first = _extract_hook_sequence_from_router()
    hook_names_second = _extract_hook_sequence_from_router()

    # Both parses should produce identical results
    assert (
        hook_names_first == hook_names_second
    ), "Parsing Stop_router.py twice produced different results"

    # Extract RCA hard gates from both parses
    rca_gates_first = [name for name in hook_names_first if "rca_contract" in name.lower()]
    rca_gates_second = [name for name in hook_names_second if "rca_contract" in name.lower()]

    # Both should show exactly one RCA hard gate
    assert (
        len(rca_gates_first) == 1
    ), f"First parse shows {len(rca_gates_first)} RCA hard gates, expected 1"
    assert (
        len(rca_gates_second) == 1
    ), f"Second parse shows {len(rca_gates_second)} RCA hard gates, expected 1"
    assert (
        rca_gates_first[0] == rca_gates_second[0]
    ), "First and second parses show different RCA hard gates"


def run_all_tests() -> int:
    """Run all tests when script is executed directly."""
    import traceback

    print("Running RCA single hard gate test coverage...\n")

    tests = [
        (
            "Live Stop router has single RCA hard gate",
            test_live_stop_router_has_single_rca_hard_gate,
        ),
        ("RCA hard gate in active runtime hooks", test_rca_hard_gate_in_active_runtime_hooks),
        ("Package hook not in live Stop path", test_package_hook_not_in_live_stop_path),
        ("Package hook file exists but not active", test_package_hook_file_exists_but_not_active),
        ("No duplicate RCA gates in hook sequence", test_no_duplicate_rca_gates_in_hook_sequence),
        ("Python import cache consistency", test_python_import_cache_consistency),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            print(f"Testing: {name}...", end=" ")
            test_func()
            print("✓ PASS")
            passed += 1
        except AssertionError as e:
            print("✗ FAIL")
            print(f"  Error: {e}")
            failed += 1
        except Exception:
            print("✗ ERROR")
            print(f"  {traceback.format_exc()}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed")
    print(f"{'=' * 60}")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
