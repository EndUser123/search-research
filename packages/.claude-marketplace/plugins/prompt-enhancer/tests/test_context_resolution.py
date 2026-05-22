"""Tests for context-aware referent resolution.

Covers:
- extract_subject() priority: file ref > slash command > "the X" NP
- is_continuation() pattern matching
- resolve_referent() for continuations and pronouns
- enhance() ambiguous→resolved path uses session context
- _is_conversational_clear() recognizes context-bound questions
"""

from __future__ import annotations

import pytest

# autouse _isolated_home in conftest.py handles terminal/HOME isolation for all tests.
# Consume the yielded values to satisfy pytest's fixture protocol.
from conftest import _isolated_home

_ = _isolated_home  # noqa: F841 — isolation handled by autouse fixture


from context import (
    SessionContext,
    Turn,
    extract_subject,
    is_continuation,
    resolve_referent,
    read_session_context,
    write_session_context,
)
from detect import _is_conversational_clear, triage
from prompt_enhancer import enhance


class TestExtractSubject:
    def test_file_reference_wins(self):
        assert extract_subject("fix wiki_manifest.py logic") == "wiki_manifest.py"

    def test_slash_command_second(self):
        assert extract_subject("/cc-skills-sdlc:pre-mortem the wiki work") == "/cc-skills-sdlc:pre-mortem"

    def test_the_noun_phrase_third(self):
        # No file, no slash command — the "the X" phrase wins.
        assert extract_subject("refactor the user controller") == "the user controller"

    def test_returns_none_on_bare_verb(self):
        assert extract_subject("fix") is None

    def test_returns_none_on_empty(self):
        assert extract_subject("") is None

    def test_informational_prompt_returns_none(self):
        """'what's the time?' should not extract 'the time' as the subject."""
        result = extract_subject("what's the time?")
        assert result is None

    def test_informational_what_returns_none(self):
        result = extract_subject("what is refactoring?")
        assert result is None

    def test_informational_short_question_returns_none(self):
        result = extract_subject("how does it work?")
        assert result is None

    def test_informational_long_prompt_bypasses_filter(self):
        """Long informational prompts (>20 words) bypass the informational filter.
        The 'the X' phrase is extracted normally — the filter only targets short questions."""
        long_q = ("what is the specific mechanism by which the authentication token "
                 "gets validated against the database and what timeout applies here")
        result = extract_subject(long_q)
        # Bypasses informational filter; the-NP regex grabs "the specific mechanism by which"
        assert result.startswith("the specific")


class TestIsContinuation:
    @pytest.mark.parametrize("prompt", [
        "continue", "proceed", "go ahead", "yes", "yes please",
        "one more time", "carry on", "more.", "OK!",
    ])
    def test_exact_continuations(self, prompt):
        assert is_continuation(prompt) is True

    @pytest.mark.parametrize("prompt", [
        "continue tests 1..5", "proceed with the fix", "retry the build",
    ])
    def test_leading_continuation_with_args(self, prompt):
        assert is_continuation(prompt) is True

    @pytest.mark.parametrize("prompt", [
        "fix the bug", "delete the database", "build a feature",
        "what about fix 3?",
    ])
    def test_non_continuations(self, prompt):
        assert is_continuation(prompt) is False


class TestResolveReferent:
    def test_continuation_resolves_to_last_subject(self):
        ctx = SessionContext(turns=[
            Turn(prompt="fix wiki_manifest.py", subject="wiki_manifest.py", timestamp=0)
        ])
        resolution = resolve_referent("continue", ctx)
        assert resolution is not None
        assert resolution.inferred_subject == "wiki_manifest.py"
        assert resolution.confidence >= 0.7

    def test_pronoun_resolves_to_last_subject(self):
        ctx = SessionContext(turns=[
            Turn(prompt="refactor auth.py", subject="auth.py", timestamp=0)
        ])
        resolution = resolve_referent("fix it", ctx)
        assert resolution is not None
        assert resolution.inferred_subject == "auth.py"

    def test_no_context_returns_none(self):
        resolution = resolve_referent("continue", SessionContext())
        assert resolution is None

    def test_unrelated_prompt_returns_none(self):
        ctx = SessionContext(turns=[
            Turn(prompt="fix wiki_manifest.py", subject="wiki_manifest.py", timestamp=0)
        ])
        # "Tell me about Python" has no continuation or pronoun marker.
        assert resolve_referent("tell me about Python", ctx) is None


class TestSessionContextPersistence:
    def test_write_then_read_roundtrip(self):
        write_session_context("fix wiki_manifest.py", "wiki_manifest.py")
        ctx = read_session_context()
        assert ctx.last_turn is not None
        assert ctx.last_turn.prompt == "fix wiki_manifest.py"
        assert ctx.last_subject == "wiki_manifest.py"

    def test_history_pruned_to_max(self):
        for i in range(10):
            write_session_context(f"prompt {i}", f"subject{i}")
        ctx = read_session_context()
        # _MAX_TURN_HISTORY is 5 — only the latest 5 should remain.
        assert len(ctx.turns) == 5
        assert ctx.turns[-1].prompt == "prompt 9"

    def test_empty_when_no_file(self):
        ctx = read_session_context()
        assert ctx.turns == []


class TestEnhanceWithContext:
    def test_continuation_with_prior_subject(self):
        ctx = SessionContext(turns=[
            Turn(prompt="fix wiki_manifest.py", subject="wiki_manifest.py", timestamp=0)
        ])
        er = enhance("continue", cwd="", ctx=ctx)
        assert er.inferred_subject == "wiki_manifest.py"
        assert er.confidence >= 0.7
        assert "wiki_manifest.py" in er.clarified_intent

    def test_ambiguous_without_context_low_confidence(self):
        er = enhance("fix", cwd="", ctx=SessionContext())
        # No prior subject to resolve against — falls back to generic, low confidence.
        assert er.confidence < 0.5
        assert er.inferred_subject is None


class TestConversationalClear:
    @pytest.mark.parametrize("prompt", [
        "your proposal results in the best software development projects?",
        "what about fix 3?",
        "does that include cleanup?",
        "is it ready?",
        "can we proceed?",
        "how about a different approach?",
        "let's go with option B",
        "tell me more",
    ])
    def test_recognized_as_clear(self, prompt):
        result = triage(prompt)
        assert result["classification"] == "clear", (
            f"Expected '{prompt}' to be conversational-clear, got {result}"
        )

    def test_question_without_context_opener_not_misclassified(self):
        # "delete the database?" should still hit confirm, not conversational-clear.
        result = triage("delete the database?")
        assert result["classification"] in ("confirm", "ambiguous")
