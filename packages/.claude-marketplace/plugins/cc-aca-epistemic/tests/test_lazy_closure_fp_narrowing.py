"""Regression tests for the 2026-06-01 false-positive narrowings.

Three lazy_closure patterns were over-firing (101 blocks/7d, ~85% of all Stop-hook
friction). These tests pin the narrowed behavior:

1. sycophancy_capitulation — fires only when the agreement sits near an empirical
   behavior-claim. Bare social/preference agreement must pass.
2. self_referential_evasion — the hypothesis pattern requires a hedge modal in the
   same clause; "hypothesis" as a plain technical noun must not fire.

The genuine catches MUST still block — that is the value these guards exist for.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Mirror the working inline-invocation path setup: __lib dir + plugin root.
_PLUGIN_ROOT = Path(__file__).resolve().parents[1]
_LIB = _PLUGIN_ROOT / "__lib"
for _p in (str(_LIB), str(_PLUGIN_ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from anti_sycophancy.lazy_closure_detector import detect_lazy_closure  # noqa: E402


def _types(response: str, user_prompt: str = "") -> set[str]:
    m = detect_lazy_closure(response, user_prompt=user_prompt)
    return {m.pattern_type} if m else set()


class TestSycophancyEmpiricalNarrowing:
    """Social/preference agreement passes; empirical concession still blocks."""

    def test_preference_agreement_passes(self):
        # "You're right" + a design/preference judgment, no behavior claim.
        assert "sycophancy_capitulation" not in _types(
            "You're right, Option B is cleaner and easier to maintain."
        )

    def test_agreement_to_flag_passes(self):
        assert "sycophancy_capitulation" not in _types(
            "You're right to flag that. The naming could be clearer."
        )

    def test_empirical_concession_still_blocks(self):
        # Agreement + claim about external behavior, no Bash evidence -> block.
        assert "sycophancy_capitulation" in _types(
            "You're right. The bug is fixed now."
        )

    def test_behavior_claim_concession_still_blocks(self):
        assert "sycophancy_capitulation" in _types(
            "I see now. The command works correctly and returns the full list."
        )

    def test_bash_evidence_still_exempts(self):
        # Real shell output present -> never fires regardless of empirical claim.
        assert "sycophancy_capitulation" not in _types(
            "You're right. The bug is fixed.\n$ pytest\nexit code: 0\nstdout: 3 passed"
        )


class TestSelfReferentialHypothesisNarrowing:
    """Technical 'hypothesis' noun passes; genuine hedge-modal evasion still blocks.

    Note: self_referential_evasion is scope-guarded to fire only when tool-usage
    markers are present, so each sample includes an 'edited the file' marker.
    """

    _TOOL = " I edited the file to apply the change."

    def test_technical_hypothesis_noun_passes(self):
        # "single hypothesis, no discriminating test — would now be" — no hedge modal
        # before 'be'. Previously matched via the over-broad .*?...be pattern.
        assert "self_referential_evasion" not in _types(
            "We had a single hypothesis, no discriminating test — would now be tighter."
            + self._TOOL
        )

    def test_hypothesis_noun_then_clause_passes(self):
        # "hypothesis, then ran the test" - plain noun, no hedge modal before be/apply/
        # explain. Previously matched via the over-broad .*?...be pattern.
        assert "self_referential_evasion" not in _types(
            "We narrowed it to a single hypothesis, then ran the discriminating test."
            + self._TOOL
        )

    # KNOWN RESIDUAL (not fixed here): text that *quotes* reasoning-contract phrasing
    # containing "competing hypotheses" still matches the competing/ruling-out pattern.
    # That is a quote/injected-context exemption problem, not a hypothesis-noun problem.
    # Tracked separately - see the self_referential quote-exemption follow-up.

    def test_genuine_hedge_modal_still_blocks(self):
        # "hypothesis might still be" — real decision-evasion hedging.
        assert "self_referential_evasion" in _types(
            "I verified the root cause, but the hypothesis might still be wrong." + self._TOOL
        )


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-q"]))
