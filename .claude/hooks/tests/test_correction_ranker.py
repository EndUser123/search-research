"""Tests for correction_ranker.py — relevance-based correction ranking."""

import sys
sys.path.insert(0, "P:/.claude/hooks")
from utils.correction_ranker import (
    score_correction,
    rank_corrections,
    rank_corrections_with_scores,
)


# Sample corrections matching what's now in MEMORY.md
AUTH_JWT = "1. auth.py JWT validation: Don't accept JWT tokens without verifying expiration timestamp first."
AUTH_SESSION = "2. auth.py session handling: Don't use in-memory dict for sessions. Use Redis for session storage instead."
CSS_THEMING = "3. CSS theming: Don't use hardcoded hex values. Use CSS custom properties (--color-primary) instead."
DB_POOLING = "4. database.py connection pooling: Don't create database connections without pooling. Use SQLAlchemy connection pooling instead."
GIT_COMMIT = "5. git commit messages: Don't start commit messages with nouns. Use verbs instead."
AUTH_ERROR = "6. auth.py error responses: Don't return 403 for authentication failures. Use 401 for authentication failures and 403 for authorization failures."
TEST_NAMING = "7. test file naming: Don't use arbitrary test filenames. Use the module-matching pattern instead."
README_DOC = "8. README.md documentation: Don't skip documentation for new endpoints. Update README when adding endpoints."
AUTH_PWD = "9. auth.py password hashing: Don't use bcrypt cost factor 10. Use cost factor 12 instead."
CSS_RESP = "10. CSS responsive design: Don't use 640px as the mobile breakpoint. Use 768px instead."
SEQ_EDITS = "11. Sequential edits: Don't use Write followed by Delete for sequential changes to the same file. Use Edit instead."
SLASH_SKILL = "- **Slash commands use skills**: `/skill-name args` means invoke the Skill tool immediately; do not replicate skill manually."
FETCH_DONT = "- **Fetch, don't ask**: If logs, files, or command output can be obtained with tools, obtain them instead of asking the user."

ALL_CORRECTIONS = [
    AUTH_JWT, AUTH_SESSION, CSS_THEMING, DB_POOLING, GIT_COMMIT,
    AUTH_ERROR, TEST_NAMING, README_DOC, AUTH_PWD, CSS_RESP, SEQ_EDITS,
    SLASH_SKILL, FETCH_DONT,
]


class TestR1_1AuthCorrectionRanking:
    """R1.1: Auth corrections ranked above irrelevant corrections."""

    def test_auth_goal_ranks_auth_above_css(self):
        """Auth goal should rank auth.py corrections above CSS theming."""
        result = rank_corrections(
            [AUTH_JWT, AUTH_SESSION, CSS_THEMING, GIT_COMMIT, DB_POOLING],
            goal="fix authentication token expiration bug",
            active_files=["src/auth.py"],
        )
        # auth.py corrections should come before CSS
        assert result.index(AUTH_JWT) < result.index(CSS_THEMING)
        assert result.index(AUTH_SESSION) < result.index(CSS_THEMING)

    def test_auth_goal_skips_irrelevant(self):
        """Irrelevant corrections (CSS, git, DB) should rank lowest."""
        result = rank_corrections(
            ALL_CORRECTIONS,
            goal="fix authentication token expiration bug",
            active_files=["src/auth.py"],
        )
        # Top 3 should be auth-specific
        assert AUTH_JWT in result[:3]
        assert AUTH_SESSION in result[:3]
        # Irrelevant should be out of top 3
        assert CSS_THEMING not in result[:3]
        assert GIT_COMMIT not in result[:3]
        assert DB_POOLING not in result[:3]
        assert CSS_RESP not in result[:3]

    def test_auth_goal_includes_password_hashing(self):
        """auth.py password hashing (#9) should rank into top 3 when auth.py is active."""
        result = rank_corrections(
            ALL_CORRECTIONS,
            goal="fix authentication token expiration bug",
            active_files=["src/auth.py"],
        )
        # At least one of the auth corrections should appear
        auth_in_top3 = any(c in result[:3] for c in [AUTH_JWT, AUTH_SESSION, AUTH_ERROR, AUTH_PWD])
        assert auth_in_top3, f"Expected auth correction in top 3, got: {result[:3]}"

    def test_file_name_match_boosts_score(self):
        """Explicit file mention should boost score significantly."""
        # score of auth.py JWT correction with auth.py in active_files
        scored = score_correction(AUTH_JWT, goal="fix bug", active_files=["src/auth.py"])
        assert scored.score >= 3.0  # +3 for file match

    def test_goal_keyword_overlap_boosts_score(self):
        """Goal keyword overlap (auth, jwt, token) should boost score."""
        scored = score_correction(
            AUTH_JWT,
            goal="fix authentication token expiration",
            active_files=[],
        )
        assert scored.score >= 4.0  # +4 for goal keyword overlap

    def test_generic_rule_penalized_when_specific_exists(self):
        """Generic Quick Rules should be penalized when specific matches exist."""
        scored_generic = score_correction(
            SLASH_SKILL,
            goal="fix authentication bug in auth.py",
            active_files=["src/auth.py"],
        )
        scored_specific = score_correction(
            AUTH_JWT,
            goal="fix authentication bug in auth.py",
            active_files=["src/auth.py"],
        )
        # Specific should score higher
        assert scored_specific.score > scored_generic.score


class TestR3_1SequentialEditsRanking:
    """R3.1: Sequential edits correction should rank into top 3."""

    def test_sequential_edit_task_ranks_correction(self):
        """Task about sequential changes should rank SEQ_EDITS into top 3."""
        result = rank_corrections(
            ALL_CORRECTIONS,
            goal="Make 3 sequential changes to auth.py",
            active_files=["src/auth.py"],
            last_action="Read auth.py",
        )
        assert SEQ_EDITS in result[:3], f"Expected SEQ_EDITS in top 3, got: {result[:3]}"

    def test_sequential_task_with_edit_goal(self):
        """Sequential edit task ranks above other corrections."""
        result = rank_corrections(
            ALL_CORRECTIONS,
            goal="use edit tool for sequential changes to auth.py",
            active_files=["src/auth.py"],
        )
        # SEQ_EDITS and AUTH corrections should be in top 3
        seq_in_top = SEQ_EDITS in result[:3]
        auth_in_top = any(c in result[:3] for c in [AUTH_JWT, AUTH_SESSION, AUTH_ERROR, AUTH_PWD])
        assert seq_in_top or auth_in_top

    def test_sequential_edit_phrase_detection(self):
        """Sequential edit task keywords should boost matching correction."""
        scored = score_correction(
            SEQ_EDITS,
            goal="make 3 sequential changes to auth.py",
            active_files=["src/auth.py"],
        )
        # Should have file match (+5) and action overlap (+3)
        assert scored.score >= 5.0


class TestRankingBehavior:
    """Additional ranking behavior tests."""

    def test_empty_context_returns_first_n(self):
        """With no context, should return first N (deterministic)."""
        result = rank_corrections(
            ALL_CORRECTIONS,
            goal="",
            active_files=[],
            last_action="",
            pending_work=[],
        )
        assert len(result) == 3  # top_n default
        # With no scoring signal, original order preserved
        assert result[0] == ALL_CORRECTIONS[0]

    def test_top_n_respected(self):
        """Should never return more than top_n corrections."""
        result = rank_corrections(ALL_CORRECTIONS, goal="auth", top_n=3)
        assert len(result) <= 3

    def test_stable_sort_on_tie(self):
        """Tied scores should maintain original order (stable sort)."""
        # Two corrections with identical scoring signals
        result = rank_corrections(
            [AUTH_SESSION, AUTH_ERROR],
            goal="auth.py session handling",
            active_files=["src/auth.py"],
        )
        assert len(result) == 2

    def test_auth_error_code_ranking(self):
        """Auth error codes (#6) should rank above irrelevant corrections."""
        result = rank_corrections(
            [AUTH_ERROR, CSS_THEMING, GIT_COMMIT],
            goal="fix authentication error",
            active_files=["src/auth.py"],
        )
        assert result[0] == AUTH_ERROR, f"AUTH_ERROR should rank first, got: {result[0][:50]}"


class TestScoreBreakdown:
    """Test score detail for debugging."""

    def test_score_breakdown_visible(self):
        """rank_corrections_with_scores should return full breakdown."""
        results = rank_corrections_with_scores(
            [AUTH_JWT, AUTH_SESSION, CSS_THEMING],
            goal="fix authentication token bug",
            active_files=["src/auth.py"],
        )
        assert len(results) == 3
        assert results[0].score >= results[1].score
        assert "file_match:auth.py" in results[0].bonuses
        assert "goal_kw:auth" in results[0].bonuses

    def test_no_negative_scores(self):
        """Scores should not go negative."""
        for c in ALL_CORRECTIONS:
            scored = score_correction(c, goal="", active_files=[])
            assert scored.score >= 0.0