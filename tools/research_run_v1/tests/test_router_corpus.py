from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT))

from research_runtime.evaluate_router import evaluate  # noqa: E402


def test_realistic_router_corpus_matches_expected_decisions() -> None:
    results = evaluate()

    assert len(results) == 18
    for result in results:
        assert result["refined_router"] == result["expected_lane"], result
        assert result["human_escalation"] == result["expected_escalation"], result
        assert result["stop_reason"] == result["expected_stop"], result
        if result["required_rejection"]:
            reasons = [reason for values in result["rejected"].values() for reason in values]
            assert result["required_rejection"] in reasons, result

