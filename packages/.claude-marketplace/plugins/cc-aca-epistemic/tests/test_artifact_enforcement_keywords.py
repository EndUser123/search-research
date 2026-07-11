"""Regression lock for #1444: Stop_artifact_enforcement claim-keyword FPs.

Incident (2026-07-11, session 1319db79, diagnostics.db row 130687): a response
containing "Spec Kit (overlaps `/go`)" — a product-comparison sentence — was
blocked with "Co-fire claims require ups_execution_trace.jsonl same-turn
evidence" because the old keyword map used bare substrings ("overlap",
"same turn", noun "co-fire"). Meta-discussion of the gate itself ("co-fire
claim gate") also re-triggered it. 51 blocks from this gate were in the
FP-ledger at fix time.

The fix matches ASSERTIONS that a runtime event happened (verb forms), not
noun mentions or generic English. Same defect family as #882/#1415.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).parent.parent

sys.path.insert(0, r"P:/.claude/hooks")
sys.path.insert(0, str(PLUGIN_ROOT / "__lib"))

_spec = importlib.util.spec_from_file_location(
    "stop_artifact_enforcement",
    PLUGIN_ROOT / "hooks" / "stop" / "Stop_artifact_enforcement.py",
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
check = _mod._check_claim_keywords


class TestNoFalsePositives:
    def test_incident_product_overlap_prose(self):
        """The exact #1444 incident text must not classify as a co-fire claim."""
        text = (
            "Spec Kit (overlaps `/go`), EventCatalog (infrastructure too heavy; "
            "use only the semantic model)"
        )
        assert check(text) == []

    def test_meta_discussion_of_the_gate_itself(self):
        """Discussing this gate must not re-trigger it (self-referential FP)."""
        assert check("the co-fire claim gate needs same-turn evidence refs") == []

    def test_same_turn_idiom_in_workflow_prose(self):
        assert check("we did both fixes in the same turn") == []

    def test_generic_overlap_noun(self):
        assert check("there is overlap between the two skills") == []


class TestTruePositivesStillFire:
    def test_cofired_past_tense_verb(self):
        assert "co-fire" in check(
            "operating_rules and behavior_contract co-fired this turn"
        )

    def test_mechanism_fired_together_sentence(self):
        assert "co-fire" in check("both gates fired together after the prompt")

    def test_mechanism_fired_same_turn_sentence(self):
        assert "co-fire" in check("the hooks fired in the same turn as the injector")

    def test_gate_fired_token(self):
        assert "gate_fired" in check("telemetry shows gate_fired for the age guard")

    def test_age_guard_fired(self):
        assert "age_guard_fired" in check("the age guard fired on the stale check")
