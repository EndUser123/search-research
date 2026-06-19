"""Tests for overconfidence_detector — comparison-evidence exemption on flat events.

Covers the 2026-06-18 fix: Read-inspection paths are read from event["file_path"]
(the flat schema gates feed via build_turn_tool_events), not from a dead
`command.get("file_path")` branch that left inspected_paths empty. No mocks.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent.parent / "__lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
_spec = importlib.util.spec_from_file_location(
    "overconfidence_detector", _LIB / "anti_sycophancy" / "overconfidence_detector.py"
)
ocd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ocd)


def _ev(name, command="", file_path="", output_excerpt=""):
    return {
        "name": name,
        "command": command,
        "file_path": file_path,
        "skill": "",
        "output_excerpt": output_excerpt,
    }


# ── _has_comparison_evidence: the function the fix touched ────────────────────

def test_comparison_evidence_from_flat_file_path():
    """Enumeration + >=2 sibling Reads (flat file_path) -> comparison evidence."""
    evs = [
        _ev("Bash", command="ls skills/*/"),
        _ev("Read", file_path="skills/a/SKILL.md"),
        _ev("Read", file_path="skills/b/SKILL.md"),
    ]
    assert ocd._has_comparison_evidence(evs, "") is True


def test_no_comparison_evidence_when_empty():
    assert ocd._has_comparison_evidence([], "") is False


def test_no_comparison_evidence_single_peer():
    evs = [
        _ev("Bash", command="ls skills/*/"),
        _ev("Read", file_path="skills/a/SKILL.md"),
    ]
    assert ocd._has_comparison_evidence(evs, "") is False


# ── detect_all_overconfidence: integration with flat events ──────────────────

def test_detect_all_runs_on_flat_events_no_crash():
    evs = [_ev("Bash", command="ls", output_excerpt="a\nb")]
    out = ocd.detect_all_overconfidence("Some analysis text.", tool_events=evs)
    assert isinstance(out, list)


def test_detect_all_empty_response_returns_empty():
    assert ocd.detect_all_overconfidence("", None) == []
