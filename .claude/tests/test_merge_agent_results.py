"""Tests for merge_agent_results.py."""

import json
import sys
from pathlib import Path

# Add lib/ to path for import
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "gto" / "lib"))

from merge_agent_results import load_json_file, validate_finding, merge_gaps


def test_validate_finding_accepts_valid_finding():
    """Valid finding with all required fields passes."""
    finding = {
        "id": "LOGIC-001",
        "severity": "HIGH",
        "location": "test.py:10",
        "title": "Off-by-one error",
    }
    assert validate_finding(finding, "logic") is True


def test_validate_finding_rejects_missing_field():
    """Finding missing a required field is rejected."""
    finding = {"id": "LOGIC-001", "severity": "HIGH"}  # missing location, title
    assert validate_finding(finding, "logic") is False


def test_validate_finding_rejects_invalid_severity():
    """Finding with invalid severity is rejected."""
    finding = {
        "id": "LOGIC-001",
        "severity": "INVALID",
        "location": "test.py:10",
        "title": "Off-by-one error",
    }
    assert validate_finding(finding, "logic") is False


def test_merge_gaps_combines_l1_and_agent_data(tmp_path):
    """merge_gaps combines L1 gaps with agent findings."""
    l1_data = {"gaps": [{"id": "L1-001", "severity": "high", "title": "L1 gap"}]}
    agent_data = {
        "logic": {"findings": [{"id": "LOGIC-001", "severity": "HIGH", "location": "test.py:10", "title": "Logic issue"}]},
        "quality": {"findings": []},
    }
    result = merge_gaps(l1_data, agent_data)
    assert len(result["gaps"]) == 2
    # Agent findings get source field added
    logic_gap = next(g for g in result["gaps"] if g["id"] == "LOGIC-001")
    assert logic_gap["source"] == "adversarial-logic"


def test_load_json_file_missing_raises(tmp_path):
    """Missing file raises FileNotFoundError."""
    missing = tmp_path / "nonexistent.json"
    try:
        load_json_file(missing)
        assert False, "Expected FileNotFoundError"
    except FileNotFoundError:
        pass  # expected

