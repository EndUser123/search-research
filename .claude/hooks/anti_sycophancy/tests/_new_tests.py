import sys
sys.path.insert(0, str(__file__).rsplit("tests", 1)[0])
from overconfidence_detector import (
    detect_overconfidence,
)

class TestRuntimeMismatchAttribution:
    """Runtime mismatch + singular cause detection (Part 2 new patterns)."""

    def test_mismatch_plus_singular_cause_blocked(self):
        """Mismatch language + singular cause claim without evidence -> flagged."""
        response = (
            "The issue is stale bytecode. Live hook differs from what you're seeing. "
            "The test passes but runtime doesn't."
        )
        result = detect_overconfidence(response)
        assert result is not None
        assert result.pattern_type == "runtime_mismatch_attribution"

    def test_mismatch_alone_allowed(self):
        """Mismatch language only (no singular cause) -> allowed."""
        response = "Live hook differs from what you're seeing."
        result = detect_overconfidence(response)
        assert result is None

    def test_singular_cause_alone_allowed(self):
        """Singular cause phrase only (no mismatch) -> allowed."""
        response = "The issue is a bug in the code."
        result = detect_overconfidence(response)
        assert result is None or result.pattern_type != "runtime_mismatch_attribution"

    def test_mismatch_with_evidence_allowed(self):
        """Mismatch + singular cause but has evidence marker -> allowed."""
        response = (
            "[Tier 2]: The issue is stale bytecode. "
            "Live hook differs from what you're seeing."
        )
        result = detect_overconfidence(response)
        assert result is None

    def test_properly_hedged_mismatch_allowed(self):
        """Mismatched described with proper Observed/Possible causes structure -> allowed."""
        response = (
            "Observed: live hook differs from local verification. "
            "Possible causes: stale bytecode, version mismatch, persistent process state. "
            "Next check: inspect __file__ in the live process."
        )
        result = detect_overconfidence(response)
        assert result is None

    def test_multiple_causes_allowed(self):
        """Multiple possible causes listed without singular claim -> allowed."""
        response = (
            "Live hook differs - could be stale bytecode, version mismatch, or persistent state. "
            "Need to check __file__ to narrow it down."
        )
        result = detect_overconfidence(response)
        assert result is None


class TestBlindSyspathWorkaround:
    """Blind sys.path insertion without diagnostic label (Part 4 new pattern)."""

    def test_bare_syspath_insert_blocked(self):
        """Bare sys.path.insert without temporary/diagnostic label -> flagged."""
        response = "I will add sys.path.insert(0, os.path.dirname(__file__)) to fix the import."
        result = detect_overconfidence(response)
        assert result is not None
        assert result.pattern_type == "blind_syspath_workaround"

    def test_syspath_with_temporary_label_allowed(self):
        """sys.path.insert labeled as temporary diagnostic -> allowed."""
        response = (
            "For verification purposes only (temporary workaround), "
            "I will add sys.path.insert(0, os.path.dirname(__file__))."
        )
        result = detect_overconfidence(response)
        assert result is None

    def test_syspath_with_diagnostic_label_allowed(self):
        """sys.path.insert labeled as diagnostic snippet -> allowed."""
        response = (
            "This is a diagnostic snippet: "
            "sys.path.insert(0, os.path.dirname(__file__))"
        )
        result = detect_overconfidence(response)
        assert result is None

    def test_syspath_reassignment_blocked(self):
        """sys.path reassignment without verification label -> flagged."""
        response = "Add sys.path = [os.path.dirname(__file__)] + sys.path to fix imports."
        result = detect_overconfidence(response)
        assert result is not None
        assert result.pattern_type == "blind_syspath_workaround"

    def test_syspath_append_blocked(self):
        """Bare sys.path.append without workaround label -> flagged."""
        response = "Use sys.path.append(os.path.dirname(__file__)) to fix the path."
        result = detect_overconfidence(response)
        assert result is not None
        assert result.pattern_type == "blind_syspath_workaround"