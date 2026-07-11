"""Regression lock for the referent-inference removal (2026-07-11).

Incident: user typed "fix it directly" after pasting a long closeout. The
deleted resolve_referent() path inferred the referent from the FIRST file
reference in the prior prompt (an incidental `console_*.jsonl` in ls output)
and injected "Likely subject: console_4ccbe717...jsonl" — a confidently wrong
anchor. The consuming model holds the conversation and resolves pronouns
natively; deterministic referent guessing was removed outright.

These tests lock the replacement behavior: ambiguous pronoun prompts produce
a low-confidence result (below DEFAULT_INJECT_THRESHOLD) and the hook injects
NOTHING — no "Likely subject", no "inferred from prior turn".
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from prompt_enhancer import (  # noqa: E402
    DEFAULT_INJECT_THRESHOLD,
    build_additional_context,
    enhance,
)


class TestNoReferentInjection:
    def test_pronoun_prompt_stays_below_inject_threshold(self):
        """'fix it directly' must not clear the injection gate."""
        er = enhance("fix it directly", "P:/")
        assert er.confidence < DEFAULT_INJECT_THRESHOLD, (
            f"ambiguous pronoun prompt got confidence {er.confidence}; "
            "it must stay below the inject threshold so the hook stays silent"
        )

    def test_no_inferred_subject_field_exists(self):
        """The schema no longer carries an inferred_subject to render."""
        er = enhance("fix it directly", "P:/")
        assert not hasattr(er, "inferred_subject")

    def test_context_module_is_gone(self):
        """resolve_referent's home module must not resurface silently."""
        assert not (Path(__file__).parent.parent / "context.py").exists()

    def test_rendered_context_never_claims_prior_turn_inference(self):
        """Even if rendered, output must not contain the wrong-anchor header."""
        er = enhance("fix it directly", "P:/")
        rendered = build_additional_context(er)
        assert "inferred from prior turn" not in rendered
        assert "Likely subject" not in rendered
