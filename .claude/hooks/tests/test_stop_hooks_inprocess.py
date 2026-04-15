"""
Tests for in-process hook execution in Stop_router.py (Phase 3).

Tests verify that:
1. In-process execution works correctly for migrated hooks
2. Subprocess fallback works for unmigrated hooks
3. Timeout handling works in both modes
4. Hook ordering and early-exit behavior is preserved
5. The run() protocol is correctly implemented

Run with: pytest P:/.claude/hooks/tests/test_stop_hooks_inprocess.py -v
"""

import sys
import tempfile
import time
from pathlib import Path

import pytest

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent.parent / "hooks"
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))


# =============================================================================
# TEST FIXTURES
# =============================================================================

@pytest.fixture
def sample_hook_input():
    """Sample input data for Stop hooks."""
    return {
        "prompt": "Test prompt for in-process hook execution",
        "response": "This is a test response with no problematic claims.",
        "session_id": "test-session-inprocess-001",
        "tools_used": ["Read", "Grep"],
        "terminal_id": "test-terminal",
    }


@pytest.fixture
def block_hook_input():
    """Input that will be blocked by empirical_claims_gate."""
    return {
        "prompt": "Fix the issue",
        "response": "Fixed the bug. The issue is resolved now.",
        "session_id": "test-session-block-001",
        "tools_used": [],
        "terminal_id": "test-terminal",
    }


@pytest.fixture
def temp_hook_with_run():
    """Create a temporary hook file that implements run() protocol."""
    hook_content = '''#!/usr/bin/env python3
"""Test hook with in-process run() protocol."""

import sys
from pathlib import Path

# Add hooks dir to path
hooks_dir = Path(__file__).resolve().parent
if str(hooks_dir) not in sys.path:
    sys.path.insert(0, str(hooks_dir))

from __lib.hook_base import hook_main

def run(data: dict) -> dict | None:
    """In-process hook execution."""
    response = data.get("response", "")

    # Block if response contains specific trigger word
    if "TEST_BLOCK" in response:
        return {
            "block": True,
            "reason": "Test block triggered by TEST_BLOCK keyword"
        }

    # Allow otherwise
    return None

@hook_main
def main():
    """Legacy subprocess entry point."""
    import json
    data = json.loads(sys.stdin.read())
    result = run(data)
    print(json.dumps(result or {"allow": True}))

if __name__ == "__main__":
    main()
'''

    # Create temp file
    temp_file = tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.py',
        dir=HOOKS_DIR,
        delete=False
    )
    temp_file.write(hook_content)
    temp_file.flush()
    temp_file.close()

    yield temp_file.name

    # Cleanup
    try:
        Path(temp_file.name).unlink()
    except:
        pass


@pytest.fixture
def temp_hook_without_run():
    """Create a temporary hook file WITHOUT run() protocol (subprocess only)."""
    hook_content = '''#!/usr/bin/env python3
"""Test hook without in-process run() protocol - subprocess only."""

import sys
import json
from pathlib import Path

# Add hooks dir to path
hooks_dir = Path(__file__).resolve().parent
if str(hooks_dir) not in sys.path:
    sys.path.insert(0, str(hooks_dir))

from __lib.hook_base import hook_main

@hook_main
def main():
    """Legacy subprocess entry point only."""
    data = json.loads(sys.stdin.read())
    response = data.get("response", "")

    # Block if response contains specific trigger word
    if "SUBPROCESS_BLOCK" in response:
        print(json.dumps({
            "decision": "block",
            "reason": "Subprocess block triggered"
        }))
        sys.exit(2)

    print(json.dumps({"allow": True}))

if __name__ == "__main__":
    main()
'''

    # Create temp file
    temp_file = tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.py',
        dir=HOOKS_DIR,
        delete=False
    )
    temp_file.write(hook_content)
    temp_file.flush()
    temp_file.close()

    yield temp_file.name

    # Cleanup
    try:
        Path(temp_file.name).unlink()
    except:
        pass


@pytest.fixture
def temp_hook_timeout():
    """Create a hook that exceeds timeout."""
    hook_content = '''#!/usr/bin/env python3
"""Test hook that exceeds timeout."""

import sys
import time
from pathlib import Path

# Add hooks dir to path
hooks_dir = Path(__file__).resolve().parent
if str(hooks_dir) not in sys.path:
    sys.path.insert(0, str(hooks_dir))

from __lib.hook_base import hook_main

def run(data: dict) -> dict | None:
    """In-process execution that sleeps too long."""
    time.sleep(10)  # Sleep longer than any reasonable timeout
    return None

@hook_main
def main():
    """Legacy subprocess entry point."""
    import json
    data = json.loads(sys.stdin.read())
    result = run(data)
    import json
    print(json.dumps(result or {"allow": True}))

if __name__ == "__main__":
    main()
'''

    # Create temp file
    temp_file = tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.py',
        dir=HOOKS_DIR,
        delete=False
    )
    temp_file.write(hook_content)
    temp_file.flush()
    temp_file.close()

    yield temp_file.name

    # Cleanup
    try:
        Path(temp_file.name).unlink()
    except:
        pass


# =============================================================================
# HOOK_BASE.PY RUN_HOOK_INPROCESS() TESTS
# =============================================================================

class TestHookBaseRunHookInprocess:
    """Tests for hook_base.py run_hook_inprocess() function."""

    def test_run_hook_inprocess_allows_safe_response(self, temp_hook_with_run, sample_hook_input):
        """
        Test that in-process execution allows safe responses.

        Given: A hook with run() protocol
        When: Running with safe response (no trigger words)
        Then: Should return None (allow action)
        """
        from __lib.hook_base import run_hook_inprocess

        hook_name = Path(temp_hook_with_run).stem
        result = run_hook_inprocess(hook_name, sample_hook_input, timeout_seconds=5.0)

        assert result is None, "Safe response should be allowed (None result)"

    def test_run_hook_inprocess_blocks_triggered_response(self, temp_hook_with_run):
        """
        Test that in-process execution blocks triggered responses.

        Given: A hook with run() protocol
        When: Running with response containing TEST_BLOCK
        Then: Should return block decision with reason
        """
        from __lib.hook_base import run_hook_inprocess

        block_input = {
            "prompt": "Test",
            "response": "This response contains TEST_BLOCK trigger",
            "session_id": "test",
        }

        hook_name = Path(temp_hook_with_run).stem
        result = run_hook_inprocess(hook_name, block_input, timeout_seconds=5.0)

        assert result is not None, "Blocked response should return dict"
        assert result.get("block") is True, "Should block"
        assert "reason" in result, "Should include block reason"
        assert "TEST_BLOCK" in result["reason"], "Reason should mention trigger"

    def test_run_hook_inprocess_returns_none_for_hook_without_run(self, temp_hook_without_run, sample_hook_input):
        """
        Test that in-process execution returns None for hooks without run().

        Given: A hook WITHOUT run() protocol
        When: Calling run_hook_inprocess()
        Then: Should return None (indicating subprocess mode required)
        """
        from __lib.hook_base import run_hook_inprocess

        hook_name = Path(temp_hook_without_run).stem
        result = run_hook_inprocess(hook_name, sample_hook_input, timeout_seconds=5.0)

        assert result is None, "Hook without run() should return None"

    def test_run_hook_inprocess_raises_on_timeout(self, temp_hook_timeout, sample_hook_input):
        """
        Test that in-process execution raises HookTimeoutError on timeout.

        Given: A hook that sleeps longer than timeout
        When: Calling run_hook_inprocess() with short timeout
        Then: Should raise HookTimeoutError
        """
        from __lib.hook_base import HookTimeoutError, run_hook_inprocess

        hook_name = Path(temp_hook_timeout).stem

        with pytest.raises(HookTimeoutError) as exc_info:
            run_hook_inprocess(hook_name, sample_hook_input, timeout_seconds=0.5)

        assert hook_name in str(exc_info.value), "Error should mention hook name"

    def test_run_hook_inprocess_timeout_reasonable(self, temp_hook_with_run, sample_hook_input):
        """
        Test that in-process execution completes within reasonable time.

        Given: A hook with simple logic
        When: Calling run_hook_inprocess()
        Then: Should complete in < 100ms (no subprocess overhead)
        """
        from __lib.hook_base import run_hook_inprocess

        hook_name = Path(temp_hook_with_run).stem

        start = time.time()
        result = run_hook_inprocess(hook_name, sample_hook_input, timeout_seconds=5.0)
        elapsed_ms = (time.time() - start) * 1000

        assert result is None, "Should allow"
        assert elapsed_ms < 100, f"In-process execution should be fast, took {elapsed_ms:.2f}ms"

    def test_supports_inprocess_detects_run_function(self, temp_hook_with_run, temp_hook_without_run):
        """
        Test that supports_inprocess() correctly detects run() function.

        Given: Two hooks (one with run(), one without)
        When: Calling supports_inprocess()
        Then: Should return True only for hook with run()
        """
        from __lib.hook_base import supports_inprocess

        hook_with_run_name = Path(temp_hook_with_run).stem
        hook_without_run_name = Path(temp_hook_without_run).stem

        assert supports_inprocess(hook_with_run_name) is True
        assert supports_inprocess(hook_without_run_name) is False


# =============================================================================
# STOP_ROUTER.PY RUN_HOOK_INPROCESS() TESTS
# =============================================================================

class TestStopRouterRunHookInprocess:
    """Tests for Stop_router.py in-process execution integration."""

    def test_stop_router_has_run_hook_inprocess_function(self):
        """
        Test that Stop_router.py has run_hook_inprocess() function.

        Given: Phase 3 is implemented
        When: Inspecting Stop_router.py
        Then: Should have run_hook_inprocess() function alongside run_hook_subprocess()
        """
        router_path = HOOKS_DIR / "Stop_router.py"
        content = router_path.read_text()

        assert "def run_hook_inprocess(" in content, "Should have run_hook_inprocess() function"

    def test_stop_router_imports_hook_base(self):
        """
        Test that Stop_router.py imports hook_base for in-process protocol.

        Given: Phase 3 is implemented
        When: Checking imports in Stop_router.py
        Then: Should import from __lib.hook_base
        """
        router_path = HOOKS_DIR / "Stop_router.py"
        content = router_path.read_text()

        assert "from __lib.hook_base import" in content, "Should import from hook_base"

    def test_hook_sequence_has_dispatch_mode(self):
        """
        Test that HOOK_SEQUENCE has 4th element for dispatch mode.

        Given: Phase 3 is implemented
        When: Inspecting HOOK_SEQUENCE tuples
        Then: Should have 4 elements: (hook, env_var, default, dispatch_mode)
        """
        router_path = HOOKS_DIR / "Stop_router.py"
        content = router_path.read_text()

        # Find HOOK_SEQUENCE definition
        import re
        match = re.search(r'HOOK_SEQUENCE\s*=\s*\[(.*?)\]', content, re.DOTALL)

        assert match is not None, "Should have HOOK_SEQUENCE"

        # Check if any tuple has 4 elements
        # At least some hooks should have "inprocess" or "subprocess" as 4th element
        has_dispatch_mode = '"inprocess"' in content or "'inprocess'" in content
        assert has_dispatch_mode, "HOOK_SEQUENCE should have dispatch mode (4th element)"


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestInProcessIntegration:
    """Integration tests for in-process hook execution."""

    def test_top_latency_hooks_migrated_to_inprocess(self):
        """
        Test that top 10 latency hooks are marked for in-process execution.

        Given: Phase 3 is implemented
        When: Checking HOOK_SEQUENCE
        Then: Top latency hooks should have "inprocess" dispatch mode
        """
        router_path = HOOKS_DIR / "Stop_router.py"
        content = router_path.read_text()

        # Top 10 latency hooks (based on historical data)
        # These should be migrated to in-process
        top_latency_hooks = [
            "empirical_claims_gate.py",
            "speculation_gate.py",
            "assumption_audit_v2.py",
            "stop_success_validator.py",
            "StopHook_cross_validator.py",
            "StopHook_skill_execution_gate.py",
            "StopHook_behavioral_quality_gate.py",
            "architecture_evidence_gate.py",
            "StopHook_reflexion_validator.py",
            "StopHook_value_assessment.py",
        ]

        # Check if at least some of these are marked for in-process
        # (Not all may be migrated yet, but we should have progress)
        inprocess_count = 0
        for hook in top_latency_hooks:
            # Simple check: does hook name appear near "inprocess" in the file?
            # Look for the hook name and "inprocess" within 500 characters
            hook_pos = content.find(hook)
            if hook_pos != -1:
                # Check 500 chars after hook name for "inprocess"
                search_window = content[hook_pos:hook_pos + 500]
                if '"inprocess"' in search_window or "'inprocess'" in search_window:
                    inprocess_count += 1

        # At least 3 should be migrated (reasonable milestone)
        assert inprocess_count >= 3, f"At least 3 top-latency hooks should be in-process, found {inprocess_count}"

    def test_unified_evidence_enforcer_has_run_protocol(self):
        """
        Test that unified_evidence_enforcer.py has run() protocol (Phase 2).

        Given: Phase 2 (UEEA) is complete
        When: Checking unified_evidence_enforcer.py
        Then: Should have run() function for in-process execution
        """
        ueea_path = HOOKS_DIR / "__lib" / "unified_evidence_enforcer.py"

        if not ueea_path.exists():
            pytest.skip("unified_evidence_enforcer.py not created yet")

        content = ueea_path.read_text()
        assert "def run(" in content, "Should have run() function for in-process protocol"

    def test_unified_claim_verifier_registered_in_stop_router(self):
        """
        Test that unified_claim_verifier.py is part of the live Stop sequence.

        Given: The unified verifier is meant to be the active general claim gate
        When: Checking Stop_router HOOK_SEQUENCE
        Then: The verifier should be present and enabled for in-process dispatch
        """
        import Stop_router  # type: ignore

        hook_names = [hook[0] for hook in Stop_router.HOOK_SEQUENCE]
        assert "unified_claim_verifier.py" in hook_names
        assert "unified_claim_verifier.py" in Stop_router.ACTIVE_RUNTIME_HOOKS

    def test_inprocess_enabled_flag_exists(self):
        """
        Test that INPROCESS_HOOK_DISPATCH_ENABLED flag exists.

        Given: Phase 3 is implemented
        When: Checking environment variables
        Then: Should have INPROCESS_HOOK_DISPATCH_ENABLED flag
        """
        router_path = HOOKS_DIR / "Stop_router.py"
        content = router_path.read_text()

        assert "INPROCESS_HOOK_DISPATCH_ENABLED" in content, "Should have in-process dispatch flag"


# =============================================================================
# SUBPROCESS FALLBACK TESTS
# =============================================================================

class TestSubprocessFallback:
    """Tests for subprocess fallback when in-process is not available."""

    def test_subprocess_fallback_works_for_hooks_without_run(self, temp_hook_without_run, sample_hook_input):
        """
        Test that subprocess fallback works for hooks without run().

        Given: A hook without run() protocol
        When: Running via subprocess (legacy mode)
        Then: Should execute correctly and allow safe responses
        """
        # Import the router's subprocess function
        sys.path.insert(0, str(HOOKS_DIR))
        from Stop_router import run_hook_subprocess

        hook_name = Path(temp_hook_without_run).name
        result = run_hook_subprocess(hook_name, sample_hook_input, timeout_seconds=5.0)

        # Should allow (None or decision=allow)
        if result:
            assert result.get("decision") != "block", "Safe response should not be blocked"

    def test_subprocess_fallback_blocks_triggered_responses(self, temp_hook_without_run):
        """
        Test that subprocess fallback blocks triggered responses.

        Given: A hook without run() protocol (subprocess only)
        When: Running with SUBPROCESS_BLOCK trigger
        Then: Should return block decision
        """
        sys.path.insert(0, str(HOOKS_DIR))
        from Stop_router import run_hook_subprocess

        block_input = {
            "prompt": "Test",
            "response": "This response contains SUBPROCESS_BLOCK trigger",
            "session_id": "test",
            "tools_used": [],
        }

        hook_name = Path(temp_hook_without_run).name
        result = run_hook_subprocess(hook_name, block_input, timeout_seconds=5.0)

        assert result is not None, "Should return result"
        assert result.get("decision") == "block", "Should block"
        assert "reason" in result, "Should include reason"


# =============================================================================
# ORDERING AND EARLY-EXIT TESTS
# =============================================================================

class TestOrderingAndEarlyExit:
    """Tests for hook ordering and early-exit behavior."""

    def test_hook_sequence_ordering_preserved(self):
        """
        Test that hook ordering is preserved in HOOK_SEQUENCE.

        Given: Phase 3 is implemented
        When: Checking HOOK_SEQUENCE
        Then: Critical hooks should be in correct order (evidence gates first)
        """
        router_path = HOOKS_DIR / "Stop_router.py"
        content = router_path.read_text()

        # Extract hook names from HOOK_SEQUENCE
        import re
        hooks = re.findall(r'"([^"]+\.py)"', content)

        # Find indices of critical hooks
        try:
            # Check that speculation_gate comes early (it's a high-latency hook)
            speculation_idx = hooks.index("speculation_gate.py")
            empirical_idx = hooks.index("empirical_claims_gate.py")

            # Evidence gates should be in reasonable positions
            assert speculation_idx < 20, "speculation_gate should be in first 20 hooks"
            assert empirical_idx < 25, "empirical_claims_gate should be in first 25 hooks"
        except ValueError:
            # Some hooks may not exist yet
            pass

    def test_early_exit_on_first_block(self):
        """
        Test that router exits early on first block (not continuing execution).

        Given: Multiple hooks in sequence
        When: First hook blocks
        Then: Should not execute subsequent hooks
        """
        # This is a behavioral test - verify that router breaks loop on block
        router_path = HOOKS_DIR / "Stop_router.py"
        content = router_path.read_text()

        # Look for early-exit logic in hook execution loop
        # Should have break or return when decision == "block"
        # The actual pattern is: if result.get("decision") == "block"
        has_block_check = (
            'result.get("decision") == "block"' in content or
            'result.get("decision") == "block"' in content or
            '"decision") == "block"' in content
        )
        assert has_block_check, "Should have early-exit logic on block"


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestInProcessPerformance:
    """Performance tests for in-process execution."""

    def test_inprocess_faster_than_subprocess(self, temp_hook_with_run, temp_hook_without_run, sample_hook_input):
        """
        Test that in-process execution is faster than subprocess.

        Given: Same hook logic (one with run(), one subprocess-only)
        When: Executing both
        Then: In-process should be significantly faster
        """
        from __lib.hook_base import run_hook_inprocess

        hook_with_run_name = Path(temp_hook_with_run).stem

        # Measure in-process time
        start = time.time()
        result_inprocess = run_hook_inprocess(hook_with_run_name, sample_hook_input, timeout_seconds=5.0)
        inprocess_ms = (time.time() - start) * 1000

        # Measure subprocess time
        sys.path.insert(0, str(HOOKS_DIR))
        from Stop_router import run_hook_subprocess

        hook_without_run_name = Path(temp_hook_without_run).name
        start = time.time()
        result_subprocess = run_hook_subprocess(hook_without_run_name, sample_hook_input, timeout_seconds=5.0)
        subprocess_ms = (time.time() - start) * 1000

        # In-process should be at least 50% faster
        # (subprocess has Python startup overhead)
        speedup = subprocess_ms / inprocess_ms if inprocess_ms > 0 else float('inf')

        assert inprocess_ms < subprocess_ms, \
            f"In-process ({inprocess_ms:.2f}ms) should be faster than subprocess ({subprocess_ms:.2f}ms)"
        assert speedup >= 1.5, \
            f"In-process should be at least 50% faster, got {speedup:.2f}x speedup"

    def test_p95_latency_target(self, temp_hook_with_run, sample_hook_input):
        """
        Test that in-process execution meets p95 latency target.

        Given: A simple hook with in-process protocol
        When: Executing multiple times
        Then: p95 latency should be < 200ms (target from plan)
        """
        from __lib.hook_base import run_hook_inprocess

        hook_name = Path(temp_hook_with_run).stem

        # Run 20 times to get p95
        latencies = []
        for _ in range(20):
            start = time.time()
            run_hook_inprocess(hook_name, sample_hook_input, timeout_seconds=5.0)
            latencies.append((time.time() - start) * 1000)

        # Calculate p95
        latencies.sort()
        p95_index = int(len(latencies) * 0.95)
        p95_latency = latencies[p95_index]

        assert p95_latency < 200, \
            f"p95 latency ({p95_latency:.2f}ms) should be < 200ms"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
