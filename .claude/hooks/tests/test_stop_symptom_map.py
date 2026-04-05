#!/usr/bin/env python3
"""Tests for Stop_symptom_map.py

Tests the symptom mapping gate.
"""

from Stop_symptom_map import run


class TestBlockMultiSymptomWithoutCauseMapping:
    """Block fixes without shared cause mapping."""

    def test_fixing_both_issues_blocks(self):
        """Must block when 'fixing both issues' without cause mapping."""
        data = {
            "response_text": "Let me fix both issues. First, the timeout. Second, the memory leak."
        }
        result = run(data)
        assert result["allow"] is False
        assert "SYMPTOM MAPPING REQUIRED" in result["reason"]

    def test_issues_list_blocks(self):
        """Must block when 'issues: 1, 2, 3' without cause mapping."""
        data = {
            "response_text": "Issues: 1) timeout, 2) memory leak, 3) error. Let me fix all of them."
        }
        result = run(data)
        assert result["allow"] is False

    def test_several_issues_blocks(self):
        """Must block 'several issues' without cause mapping."""
        data = {
            "response_text": "There are several issues here. Let me fix the timeout, the error, and the crash."
        }
        result = run(data)
        assert result["allow"] is False

    def test_multiple_problems_blocks(self):
        """Must block 'multiple problems' without cause mapping."""
        data = {
            "response_text": "Multiple problems exist. Fix the timeout and fix the memory issue."
        }
        result = run(data)
        assert result["allow"] is False

    def test_symptom_keyword_blocks(self):
        """Must block explicit 'symptoms' mention without mapping."""
        data = {"response_text": "These symptoms are related. Let me fix symptom 1 and symptom 2."}
        result = run(data)
        assert result["allow"] is False


class TestAllowWithCauseMapping:
    """Allow when cause mapping is present."""

    def test_shared_cause_allows(self):
        """Must allow when 'shared cause' is mentioned."""
        data = {
            "response_text": "Both issues are symptoms of a shared cause. The resource leak. Let me fix the leak."
        }
        result = run(data)
        assert result["allow"] is True

    def test_symptoms_point_to_allows(self):
        """Must allow when 'symptoms point to X'."""
        data = {
            "response_text": "These symptoms point to a connection pool exhaustion. Fix the pool."
        }
        result = run(data)
        assert result["allow"] is True

    def test_may_be_caused_by_allows(self):
        """Must allow with 'may be caused by'."""
        data = {
            "response_text": "The timeout and error may be caused by the same thread contention issue."
        }
        result = run(data)
        assert result["allow"] is True

    def test_root_cause_allows(self):
        """Must allow with 'root cause'."""
        data = {"response_text": "The root cause of both issues is the memory leak. Fix the leak."}
        result = run(data)
        assert result["allow"] is True

    def test_all_share_allows(self):
        """Must allow with 'all share' pattern."""
        data = {"response_text": "All these issues share a common thread pool exhaustion problem."}
        result = run(data)
        assert result["allow"] is True

    def test_common_source_allows(self):
        """Must allow with 'common source'."""
        data = {"response_text": "These errors have a common source: the database connection pool."}
        result = run(data)
        assert result["allow"] is True

    def test_same_issue_allows(self):
        """Must allow with 'same issue'."""
        data = {"response_text": "Both problems are symptoms of the same underlying issue."}
        result = run(data)
        assert result["allow"] is True

    def test_traced_to_allows(self):
        """Must allow with 'traced to'."""
        data = {"response_text": "The timeout and memory leak traced to the same goroutine leak."}
        result = run(data)
        assert result["allow"] is True

    def test_narrowed_down_to_allows(self):
        """Must allow with 'narrowed down to'."""
        data = {
            "response_text": "Both issues narrowed down to the configuration refresh mechanism."
        }
        result = run(data)
        assert result["allow"] is True


class TestEdgeCases:
    """Edge cases."""

    def test_empty_response_allows(self):
        """Empty response should be allowed."""
        data = {"response_text": ""}
        result = run(data)
        assert result["allow"] is True

    def test_short_response_allows(self):
        """Very short response should be allowed."""
        data = {"response_text": "Hi"}
        result = run(data)
        assert result["allow"] is True

    def test_single_issue_allows(self):
        """Response about single issue should be allowed."""
        data = {"response_text": "The timeout is caused by a slow query."}
        result = run(data)
        assert result["allow"] is True

    def test_gate_disabled_allows(self, monkeypatch):
        """When gate is disabled, should allow everything."""
        monkeypatch.setenv("SYMPTOM_MAP_ENABLED", "false")
        data = {"response_text": "Let me fix both issues."}
        result = run(data)
        assert result["allow"] is True
        assert "Gate disabled" in result["reason"]

    def test_multi_symptom_no_fix_allows(self):
        """Multi-symptom mention without fix language should be allowed."""
        data = {"response_text": "There are multiple issues here - the timeout and the error."}
        result = run(data)
        assert result["allow"] is True
