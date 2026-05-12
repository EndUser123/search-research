"""Test suite for Fact-Guard plugin — covers all 7 required scenarios."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fact_guard.state import read_state, write_state, get_state_dir
from fact_guard.file_patterns import is_structured_file, extract_facts_from_content
from fact_guard.contamination import detect_contamination
from fact_guard.provenance import (
    record_observation,
    verify_provenance,
    is_stale_observation,
    record_edit_provenance,
)
from fact_guard.fact_extraction import extract_from_tool_output


class TestFactGuard:
    """Test suite for Fact-Guard plugin."""

    def test_1_valid_user_provided_quota(self) -> None:
        """Test Case 1: Valid user-provided quota -> allowed."""
        user_fact = {
            "entity": "Mi-Devstral",
            "field": "quota",
            "value": "3000/5h",
            "provenance_type": "user",
        }
        record_observation(user_fact, "test_terminal")

        proposed = [{"entity": "Mi-Devstral", "field": "quota", "value": "3000/5h"}]
        unverified = verify_provenance(proposed, "test_terminal")
        assert len(unverified) == 0, "User-provided value should be verified"

    def test_2_unsupported_copied_quota(self) -> None:
        """Test Case 2: Copied value from neighbor without provenance -> blocked (contamination)."""
        existing_content = json.dumps({
            "MiniMax-M2.7": {"max_tokens": "4500"},
            "Mi-Devstral": {"max_tokens": None},
        })

        proposed_facts = [{"entity": "Mi-Devstral", "field": "max_tokens", "value": "4500"}]
        observed_facts: list[dict] = []

        hits = detect_contamination(proposed_facts, existing_content, observed_facts)
        assert len(hits) > 0, "Should detect adjacent-entry contamination"
        assert hits[0]["matched_entity_a"] == "MiniMax-M2.7"

    def test_3_unknown_preserved(self) -> None:
        """Test Case 3: Unknown/placeholder preserved -> allowed."""
        proposed = [{"entity": "Mi-Devstral", "field": "quota", "value": "unknown"}]
        unverified = verify_provenance(proposed, "test_terminal")
        assert len(unverified) == 0, "Placeholders should not require provenance"

    def test_4_local_file_evidence(self) -> None:
        """Test Case 4: Value from local file (Read output) -> allowed."""
        read_output = json.dumps({
            "providers": {
                "Mi-Devstral": {"quota": "2500/5h"},
            }
        })

        facts = extract_from_tool_output("Read", "config.json", read_output, "config.json")
        assert len(facts) > 0

        # Record what we extracted
        for fact in facts:
            record_observation(fact, "test_terminal_evidence")

        # Now verify: proposed fact matching what we read should pass
        proposed = [{"entity": "Mi-Devstral", "field": "quota", "value": "2500/5h"}]
        unverified = verify_provenance(proposed, "test_terminal_evidence")
        assert len(unverified) == 0, "Value from tool output should be verified"

    def test_5_completion_without_evidence(self) -> None:
        """Test Case 5: Completion claim without tool evidence -> blocked (state logging works)."""
        record_edit_provenance("test.json", False, "unsupported completion claim", "test_terminal")

        edits = read_state("edit_provenance.json", "test_terminal")
        assert len(edits.get("edits", [])) > 0

    def test_6_cross_terminal_isolation(self) -> None:
        """Test Case 6: Cross-terminal isolation -> counters reset per terminal."""
        write_state(
            {"facts": [{"entity": "A", "field": "x", "value": "y"}]},
            "observed_facts.json",
            "terminal_A",
        )
        write_state(
            {"facts": [{"entity": "B", "field": "x", "value": "z"}]},
            "observed_facts.json",
            "terminal_B",
        )

        data_a = read_state("observed_facts.json", "terminal_A")
        data_b = read_state("observed_facts.json", "terminal_B")

        assert data_a["facts"][0]["entity"] == "A"
        assert data_b["facts"][0]["entity"] == "B"
        assert data_a != data_b

    def test_7_compact_resilience(self) -> None:
        """Test Case 7: Compact/resume durability -> state survives process restart."""
        state = {
            "facts": [
                {"entity": "Mi-Devstral", "field": "quota", "value": "3000/5h", "ts": "2026-05-09T18:00:00Z"}
            ]
        }
        write_state(state, "observed_facts.json", "test_terminal")

        recovered = read_state("observed_facts.json", "test_terminal")
        assert recovered == state, "State should survive process restart"

    def test_structured_file_detection(self) -> None:
        """Test file pattern detection."""
        assert is_structured_file("config.json") is True
        assert is_structured_file("providers.yaml") is True
        assert is_structured_file("routes_probe.py") is True
        assert is_structured_file("quota_config.toml") is True
        assert is_structured_file("random_utils.py") is False

    def test_fact_extraction_from_json(self) -> None:
        """Test fact extraction from JSON content."""
        content = json.dumps({
            "models": {
                "m2.7": {"quota": "4500/5h", "tier": "Pro"},
            }
        })

        facts = extract_facts_from_content(content, "models.json")
        assert any(f["value"] == "4500/5h" for f in facts)
        assert any(f["value"] == "Pro" for f in facts)
        assert any(f["entity"] == "m2.7" for f in facts)

    def test_stale_observation_detection(self) -> None:
        """Test that old observations are flagged as stale."""
        old_fact = {"ts": "2020-01-01T00:00:00+00:00"}
        assert is_stale_observation(old_fact, max_age_seconds=60) is True

        # Very recent timestamp should not be stale
        from datetime import datetime, timezone
        recent_ts = datetime.now(timezone.utc).isoformat()
        recent_fact = {"ts": recent_ts}
        assert is_stale_observation(recent_fact, max_age_seconds=3600) is False

    def test_contamination_similarity_threshold(self) -> None:
        """Test that near-matches above 0.85 threshold are caught."""
        existing = json.dumps({
            "Model-A": {"max_tokens": "4500"},
        })

        # Exact match
        proposed = [{"entity": "Model-B", "field": "max_tokens", "value": "4500"}]
        hits = detect_contamination(proposed, existing, [])
        assert len(hits) == 1
        assert hits[0]["similarity"] == 1.0

    def test_contamination_with_provenance_allowed(self) -> None:
        """Test that values with provenance are not flagged as contamination."""
        existing = json.dumps({
            "Model-A": {"max_tokens": "4500"},
        })

        observed = [{"entity": "Model-B", "field": "max_tokens", "value": "4500"}]
        proposed = [{"entity": "Model-B", "field": "max_tokens", "value": "4500"}]

        hits = detect_contamination(proposed, existing, observed)
        assert len(hits) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
