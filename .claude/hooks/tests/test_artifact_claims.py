#!/usr/bin/env python3
"""Tests for artifact_claims.py — claim extraction and observation detection."""

import sys
from pathlib import Path

# Add hooks dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from artifact_claims import (
    ArtifactClaim,
    _is_meta_or_self_ref,
    _split_sentences,
    extract_artifact_claims,
    find_concrete_observation,
)

# ===== Sentence splitting =====

class TestSentenceSplitting:
    def test_preserves_file_paths(self):
        text = "I fixed the bug in Stop_behavior_audit.py. The test passes now."
        sentences = _split_sentences(text)
        # Should NOT split on .py
        assert any("Stop_behavior_audit.py" in s for s in sentences)

    def test_preserves_urls(self):
        text = "See https://example.com/docs/api.html for details. It explains everything."
        sentences = _split_sentences(text)
        assert any("https://example.com/docs/api.html" in s for s in sentences)

    def test_normal_sentence_split(self):
        text = "The bug is fixed. Tests pass. Everything works."
        sentences = _split_sentences(text)
        assert len(sentences) == 3

    def test_multiline_preserved(self):
        text = "I read config.json and found the issue. The key was missing."
        sentences = _split_sentences(text)
        assert any("config.json" in s for s in sentences)


# ===== Meta-conversation exclusion =====

class TestMetaExclusion:
    def test_hypothetical_excluded(self):
        assert _is_meta_or_self_ref("If you want to fix this, the approach would be...")

    def test_recommendation_excluded(self):
        assert _is_meta_or_self_ref("I would suggest using a different pattern.")

    def test_direct_claim_not_excluded(self):
        assert not _is_meta_or_self_ref("The bug in Stop.py is fixed.")

    def test_apology_excluded(self):
        assert _is_meta_or_self_ref("I apologize, I misread the file.")


# ===== Claim extraction =====

class TestExtractClaims:
    def test_fix_claim_with_artifact(self):
        text = "I fixed the bug in hooks/Stop.py. The test suite passes."
        claims = extract_artifact_claims(text)
        assert len(claims) >= 1
        fix_claims = [c for c in claims if c.claim_type == "fix"]
        assert len(fix_claims) >= 1
        assert fix_claims[0].target_artifact is not None
        assert "Stop.py" in fix_claims[0].target_artifact

    def test_root_cause_claim(self):
        text = "The root cause is a missing import in validator.py."
        claims = extract_artifact_claims(text)
        assert len(claims) >= 1
        assert claims[0].claim_type == "root_cause"

    def test_characterization_claim(self):
        text = "The logo.png is generic and should be replaced."
        claims = extract_artifact_claims(text)
        assert len(claims) >= 1
        assert claims[0].claim_type == "characterization"
        assert claims[0].target_artifact is not None

    def test_no_claim_in_normal_text(self):
        text = "Here is the implementation plan. We need to consider performance."
        claims = extract_artifact_claims(text)
        assert len(claims) == 0

    def test_meta_discussion_excluded(self):
        text = "If you want, the generic approach would be to use a factory pattern."
        claims = extract_artifact_claims(text)
        assert len(claims) == 0

    def test_outcome_only_fix_claim(self):
        text = "The bug is fixed and tests pass now."
        claims = extract_artifact_claims(text)
        fix_claims = [c for c in claims if c.claim_type == "fix"]
        assert len(fix_claims) >= 1
        # No artifact reference — outcome-only
        assert any(c.target_artifact is None for c in fix_claims)


# ===== Concrete observation detection =====

class TestConcreteObservation:
    def test_line_number_counts(self):
        claim = ArtifactClaim(
            text="The bug in config.json is fixed.",
            target_artifact="config.json",
            claim_type="fix",
        )
        full_text = (
            "I read config.json and found the issue at line 42. "
            "The bug in config.json is fixed."
        )
        obs = find_concrete_observation(full_text, claim)
        assert obs is not None

    def test_function_call_counts(self):
        claim = ArtifactClaim(
            text="The broken validator.py has been resolved.",
            target_artifact="validator.py",
            claim_type="fix",
        )
        full_text = (
            "In validator.py, the validate_input() function was missing a null check. "
            "The broken validator.py has been resolved."
        )
        obs = find_concrete_observation(full_text, claim)
        assert obs is not None

    def test_vague_observation_rejected(self):
        claim = ArtifactClaim(
            text="The config.json is broken.",
            target_artifact="config.json",
            claim_type="characterization",
        )
        full_text = "I looked at it. The config.json is broken."
        obs = find_concrete_observation(full_text, claim)
        assert obs is None

    def test_no_artifact_mention_rejected(self):
        claim = ArtifactClaim(
            text="The bug is fixed.",
            target_artifact="config.json",
            claim_type="fix",
        )
        full_text = "Everything looks good now. The bug is fixed."
        obs = find_concrete_observation(full_text, claim)
        assert obs is None


# ===== Gate integration (stop.py pattern) =====

class TestGateIntegration:
    """Test the gate function via direct import, matching Stop.py patterns."""

    def _make_data(self, response: str, tool_calls=None, tools_used=None):
        data = {"response": response}
        if tool_calls is not None:
            data["tool_calls"] = tool_calls
        if tools_used is not None:
            data["tools_used"] = tools_used
        return data

    def test_allows_verified_claim(self):
        """Claim with matching tool + concrete observation → allow."""
        from Stop import _run_unverified_artifact_claims

        data = self._make_data(
            response=(
                "I read config.json and found the issue at line 42 where the key was missing. "
                "The bug in config.json is fixed."
            ),
            tools_used=[{"name": "Read", "input": {"file_path": "config.json"}}],
        )
        result = _run_unverified_artifact_claims(data)
        assert result is None  # Allowed

    def test_blocks_unverified_claim(self):
        """Claim with no tool and no observation → block."""
        from Stop import _run_unverified_artifact_claims

        data = self._make_data(
            response="The config.json is broken and needs to be replaced.",
        )
        result = _run_unverified_artifact_claims(data)
        assert result is not None
        assert result["decision"] == "block"

    def test_blocks_tool_without_observation(self):
        """Tool used but no concrete observation in response → block."""
        from Stop import _run_unverified_artifact_claims

        data = self._make_data(
            response="The config.json is broken.",
            tools_used=[{"name": "Read", "input": {"file_path": "config.json"}}],
        )
        result = _run_unverified_artifact_claims(data)
        assert result is not None
        assert result["decision"] == "block"

    def test_fix_claim_without_bash_blocked(self):
        """Outcome-only fix claim without Bash (test run) → block."""
        from Stop import _run_unverified_artifact_claims

        data = self._make_data(
            response="The bug is fixed and everything works now.",
            tools_used=[{"name": "Read", "input": {"file_path": "some_file.py"}}],
        )
        result = _run_unverified_artifact_claims(data)
        assert result is not None
        assert result["decision"] == "block"

    def test_fix_claim_with_bash_allowed(self):
        """Outcome-only fix claim with Bash + concrete observation → allow."""
        from Stop import _run_unverified_artifact_claims

        data = self._make_data(
            response=(
                "I ran the test suite and all 15 tests passed. "
                "The bug is fixed and everything works now."
            ),
            tools_used=[{"name": "Bash", "input": {"command": "pytest tests/"}}],
        )
        result = _run_unverified_artifact_claims(data)
        assert result is None  # Allowed

    def test_env_disable(self):
        """Gate disabled via env var → allow."""
        import os

        from Stop import _run_unverified_artifact_claims

        os.environ["UNVERIFIED_ARTIFACT_CLAIMS_DISABLED"] = "true"
        try:
            data = self._make_data(response="The config.json is broken.")
            result = _run_unverified_artifact_claims(data)
            assert result is None
        finally:
            del os.environ["UNVERIFIED_ARTIFACT_CLAIMS_DISABLED"]


# ===== Sycophancy patterns =====

class TestSycophancyPatterns:
    """Agreement-as-claim: 'you're right, X is Y' must require same verification."""

    def _make_data(self, response: str, tool_calls=None, tools_used=None, transcript=None):
        data = {"response": response}
        if tool_calls is not None:
            data["tool_calls"] = tool_calls
        if tools_used is not None:
            data["tools_used"] = tools_used
        if transcript is not None:
            data["transcript"] = transcript
        return data

    def test_agrees_generic_png_without_read(self):
        """'You're right, logo.png is generic' without Read → block."""
        from Stop import _run_unverified_artifact_claims

        data = self._make_data(
            response="You're right, logo.png is generic and should be replaced.",
            transcript=[
                {"role": "user", "content": "I think logo.png is just generic stock art."},
            ],
        )
        result = _run_unverified_artifact_claims(data)
        assert result is not None
        assert result["decision"] == "block"

    def test_agrees_root_cause_without_tools(self):
        """'You're right, root cause is X' without tools → block."""
        from Stop import _run_unverified_artifact_claims

        data = self._make_data(
            response="You're right, the root cause is a missing import in validator.py.",
            transcript=[
                {"role": "user", "content": "I bet the root cause is a missing import in validator.py."},
            ],
        )
        result = _run_unverified_artifact_claims(data)
        assert result is not None
        assert result["decision"] == "block"

    def test_agrees_bug_fixed_without_bash(self):
        """'You're right, bug is fixed' with only Read (no Bash) → block."""
        from Stop import _run_unverified_artifact_claims

        data = self._make_data(
            response="You're right, the bug is fixed now.",
            tools_used=[
                {"name": "Read", "input": {"file_path": "some_file.py"}},
            ],
            transcript=[
                {"role": "user", "content": "So the bug is fixed now, right?"},
            ],
        )
        result = _run_unverified_artifact_claims(data)
        assert result is not None
        assert result["decision"] == "block"

    def test_agrees_but_with_verification_allowed(self):
        """'You're right, X is generic' WITH Read + concrete observation → allow."""
        from Stop import _run_unverified_artifact_claims

        data = self._make_data(
            response=(
                "I opened logo.png and it contains a placeholder icon with no custom branding — "
                "just a grey circle with initials at line 1 of the SVG source. "
                "You're right, logo.png is generic and should be replaced."
            ),
            tools_used=[
                {"name": "Read", "input": {"file_path": "logo.png"}},
            ],
        )
        result = _run_unverified_artifact_claims(data)
        assert result is None  # Allowed — verified before agreeing

    def test_bare_agreement_no_artifact_passes(self):
        """'You're right, let me look into that' — no artifact, not a claim."""
        from Stop import _run_unverified_artifact_claims

        data = self._make_data(
            response="You're right, let me look into that more carefully.",
        )
        result = _run_unverified_artifact_claims(data)
        assert result is None  # Not a claim about an artifact
