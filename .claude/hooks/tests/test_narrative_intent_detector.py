from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import narrative_intent_detector as nid

# ── Detection: should detect ────────────────────────────────────

class TestDetectIntentNarratives:

    def test_author_wanted(self):
        text = "The author wanted to prevent session leaks across terminals."
        assert len(nid.detect_intent_narratives(text)) == 1

    def test_passive_was_designed_to(self):
        text = "The resume matcher was designed to handle session restoration edge cases."
        assert len(nid.detect_intent_narratives(text)) == 1

    def test_exists_because(self):
        text = "The hook exists because users might not remember to run /clear."
        assert len(nid.detect_intent_narratives(text)) == 1

    def test_exists_to(self):
        text = "This exists to ensure backward compatibility with older plugins."
        assert len(nid.detect_intent_narratives(text)) == 1

    def test_purpose_of(self):
        text = "The purpose of this matcher is to catch startup events."
        assert len(nid.detect_intent_narratives(text)) == 1

    def test_was_added_so_that(self):
        text = "The flag was added so that hooks can skip expensive checks."
        assert len(nid.detect_intent_narratives(text)) == 1

    def test_plugin_author_included(self):
        text = "The plugin author included resume in the matcher for robustness."
        assert len(nid.detect_intent_narratives(text)) == 1

    def test_they_wanted(self):
        text = "They wanted to avoid race conditions during initialization."
        assert len(nid.detect_intent_narratives(text)) == 1

    def test_it_is_meant_to(self):
        text = "It is meant to guard against accidental double-fire."
        assert len(nid.detect_intent_narratives(text)) == 1

    def test_was_introduced_to_prevent(self):
        text = "This was introduced to prevent the daemon from starting twice."
        assert len(nid.detect_intent_narratives(text)) == 1


# ── Detection: should NOT detect ────────────────────────────────

class TestNonIntentNarratives:

    def test_code_behavior_reasoning(self):
        """Code reasoning ('crashes because state') is not intent."""
        text = "The function crashes because it mutates shared state."
        assert len(nid.detect_intent_narratives(text)) == 0

    def test_factual_code_state(self):
        """Pure code-state claim (handled by unified_claim_verifier)."""
        text = "The file exists at P:/.claude/hooks/Stop.py."
        assert len(nid.detect_intent_narratives(text)) == 0

    def test_question(self):
        text = "Why was the resume matcher included?"
        assert len(nid.detect_intent_narratives(text)) == 0

    def test_short_line(self):
        text = "It exists."
        assert len(nid.detect_intent_narratives(text)) == 0

    def test_empty(self):
        assert len(nid.detect_intent_narratives("")) == 0

    def test_markdown_header(self):
        text = "## The author designed this system"
        assert len(nid.detect_intent_narratives(text)) == 0

    def test_returns_because_value(self):
        """Code reasoning with 'returns because' should be excluded."""
        text = "The method returns because the value is null."
        assert len(nid.detect_intent_narratives(text)) == 0


# ── Hedging detection ───────────────────────────────────────────

class TestHedging:

    def test_probably(self):
        assert nid._sentence_has_hedge("The author probably wanted this for safety.")

    def test_i_believe(self):
        assert nid._sentence_has_hedge("I believe the matcher was included for robustness.")

    def test_it_seems(self):
        assert nid._sentence_has_hedge("It seems like this was designed for session recovery.")

    def test_plausible_reason(self):
        assert nid._sentence_has_hedge("One plausible reason is backward compat.")

    def test_might_be(self):
        assert nid._sentence_has_hedge("This might be for preventing race conditions.")

    def test_my_speculation(self):
        assert nid._sentence_has_hedge("My speculation is that the author wanted idempotency.")

    def test_no_hedge(self):
        assert not nid._sentence_has_hedge("The author included this for robustness.")


# ── Citation detection ──────────────────────────────────────────

class TestCitations:

    def test_file_reference(self):
        assert nid._sentence_has_citation("According to Stop.py, this was designed for safety.")

    def test_line_reference(self):
        assert nid._sentence_has_citation("The comment at line 42 explains the design rationale.")

    def test_readme_states(self):
        assert nid._sentence_has_citation("The README states this was added for backward compat.")

    def test_according_to(self):
        assert nid._sentence_has_citation("According to the commit message, this is intentional.")

    def test_quoted_evidence(self):
        assert nid._sentence_has_citation('The docstring says "prevent session leaks".')

    def test_no_citation(self):
        assert not nid._sentence_has_citation("The author wanted this for robustness.")


# ── End-to-end evaluate_narratives ──────────────────────────────

class TestEvaluateNarratives:

    def test_no_narratives_allows(self):
        result = nid.evaluate_narratives(
            "The file exists at P:/foo.py. Tests pass.",
            tool_sequence=[{"name": "Read", "command": "P:/foo.py", "output": "ok"}],
        )
        assert result["decision"] == "allow"
        assert result["reason"] == "NO_INTENT_NARRATIVES"

    def test_hedged_narrative_allows(self):
        result = nid.evaluate_narratives(
            "The author probably wanted to prevent session leaks.",
            tool_sequence=[],
        )
        assert result["decision"] == "allow"
        assert result["reason"] == "NARRATIVES_HEDGED_OR_CITED"

    def test_cited_narrative_allows(self):
        result = nid.evaluate_narratives(
            "According to the README, this was designed to prevent leaks.",
            tool_sequence=[{"name": "Read", "command": "README.md", "output": "prevent leaks"}],
        )
        assert result["decision"] == "allow"

    def test_unhedged_uncited_warns(self):
        """The core case: storytelling as fact with no evidence."""
        result = nid.evaluate_narratives(
            "The author included resume in the matcher because users might not remember to run /clear.",
            tool_sequence=[],
        )
        assert result["decision"] == "warn"
        assert result["reason"] == "UNHEDGED_INTENT_NARRATIVE"
        assert len(result["unhedged"]) == 1
        assert "systemMessage" in result

    def test_unhedged_but_investigated_allows(self):
        """If the speaker read the relevant file, allow even without hedge."""
        result = nid.evaluate_narratives(
            "The resume matcher was designed to handle session restoration.",
            tool_sequence=[
                {"name": "Read", "command": "SessionStart.py", "output": "matcher: startup|resume|clear"},
            ],
        )
        # No path entities in the sentence itself to match against evidence,
        # so this should warn (no overlap). This is correct — if you want to
        # claim design intent, either cite or hedge.
        assert result["decision"] == "warn"

    def test_unhedged_with_file_path_and_evidence_allows(self):
        """If the sentence mentions a file AND that file is in evidence, allow."""
        result = nid.evaluate_narratives(
            "The SessionStart.py hook was designed to inject behavioral guidance.",
            tool_sequence=[
                {"name": "Read", "command": "SessionStart.py", "output": "behavioral mode injection"},
            ],
        )
        assert result["decision"] == "allow"

    def test_multiple_narratives_mixed(self):
        """Mix of hedged and unhedged — only unhedged ones trigger warn."""
        text = (
            "The author probably wanted idempotency.\n"
            "The matcher was added so that hooks can fire on resume."
        )
        result = nid.evaluate_narratives(text, tool_sequence=[])
        assert result["decision"] == "warn"
        assert len(result["unhedged"]) == 1
        assert "resume" in result["unhedged"][0].lower()

    def test_real_world_resume_matcher_example(self):
        """The exact failure from the conversation that motivated this module."""
        response = (
            "Session restoration means 'new session' from the model's perspective. "
            "Users might not remember to run /clear after restoring. "
            "The plugin author wanted behavioral guidance available immediately, "
            "so the resume matcher ensures the hook fires on session restore too."
        )
        result = nid.evaluate_narratives(response, tool_sequence=[])
        assert result["decision"] == "warn"
        assert any("plugin author wanted" in s.lower() for s in result["unhedged"])
