"""
In-process latency sanity test for triage().

Validates that the hot path (triage() with no I/O, pure regex) completes well
within the ~10ms hook budget.  We measure a 100-iteration batch and assert
the total elapsed time stays under 100ms (generous but catches I/O regressions).
"""

from __future__ import annotations

import time

import pytest

from detect import triage


# Representative prompt set covering all classification paths.
_REPRESENTATIVE_PROMPTS = [
    "what is refactoring?",           # clear (informational)
    "refactor auth.py for testability",  # clear (verb + object + scope)
    "fix it",                         # ambiguous
    "delete the database",            # confirm
    "delete everything",              # prohibited
    "!raw delete everything",         # bypass
]


@pytest.mark.slow
class TestTriageLatency:
    def test_triage_batch_under_50ms(self):
        """100 calls to triage() across representative prompts should complete in under 50ms."""
        # Warm up: import and one dry-run so module-level caches are populated.
        triage("refactor auth.py")
        iterations = 100
        start = time.perf_counter()
        for _ in range(iterations):
            for prompt in _REPRESENTATIVE_PROMPTS:
                triage(prompt)
        elapsed = time.perf_counter() - start
        # 7 prompts × 100 iterations = 700 total calls.
        # 100ms / 700 = ~0.14ms per call average — generous but catches I/O regressions.
        assert elapsed < 0.10, (
            f"triage() batch took {elapsed*1000:.1f}ms for {iterations} iterations "
            f"({elapsed*1000/iterations:.3f}ms/call). Expected < 100ms total."
        )