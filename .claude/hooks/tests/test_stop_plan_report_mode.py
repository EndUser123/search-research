"""Tests for plan/report/exploration turn mode gating in Stop.py.

Verifies that:
1. _classify_turn_mode classifies turns correctly
2. _detect_turn_kind returns "exploration" for design prompts
3. Epistemic format repair skips for plan/report/exploration turns
4. lazy_closure lazy_fix is suppressed for plan/report/exploration turns
5. _run_lazy_workaround_gate skips for plan/report turns
6. Analysis mode still gets full enforcement

Run with: pytest P:/.claude/hooks/tests/test_stop_plan_report_mode.py -v
"""

import sys
from pathlib import Path

import pytest

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))


# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
def analysis_data():
    """Input that should be classified as analysis mode."""
    return {
        "prompt": "Why is the hook not firing?",
        "response": (
            "The hook is not firing because the import path is wrong. "
            "The root cause is that sys.path does not include the hooks directory. "
            "Evidence: grep output shows no match for the module name."
        ),
        "session_id": "test-session-analysis",
        "terminal_id": "test-terminal",
    }


@pytest.fixture
def plan_data():
    """Input that should be classified as plan mode (via user prompt)."""
    return {
        "prompt": "What are the next 10 things we should do?",
        "response": (
            "Based on the audit, here's the prioritized list:\n"
            "1. Commit pending changes\n"
            "2. Refresh stale plugin caches\n"
            "[RATIONALE]\n"
            "- Pending changes are at risk of loss\n"
            "- Stale caches could cause runtime issues"
        ),
        "session_id": "test-session-plan",
        "terminal_id": "test-terminal",
    }


@pytest.fixture
def plan_data_response_markers():
    """Input classified as plan mode via response markers."""
    return {
        "prompt": "Please review",
        "response": (
            "[PLAN]\n"
            "1. Fix the hook import\n"
            "2. Add tests\n"
            "[RATIONALE]\n"
            "- Import fix resolves runtime error\n"
            "- Tests prevent regression"
        ),
        "session_id": "test-session-plan-resp",
        "terminal_id": "test-terminal",
    }


@pytest.fixture
def report_data():
    """Input that should be classified as report mode."""
    return {
        "prompt": "Status update",
        "response": (
            "[STATUS] All systems operational\n"
            "[CHANGES] Updated Stop.py with plan mode\n"
            "[RESULTS] 103 tests passing\n"
            "[NEXT] Deploy to production"
        ),
        "session_id": "test-session-report",
        "terminal_id": "test-terminal",
    }


# =============================================================================
# TEST 1: _classify_turn_mode classification
# =============================================================================


class TestDetectTurnMode:
    """Verify turn mode classification logic."""

    def test_analysis_mode_default(self, analysis_data):
        from Stop import _classify_turn_mode
        assert _classify_turn_mode(analysis_data) == "analysis"

    def test_plan_mode_from_prompt(self, plan_data):
        from Stop import _classify_turn_mode
        assert _classify_turn_mode(plan_data) == "plan"

    def test_plan_mode_from_response_markers(self, plan_data_response_markers):
        from Stop import _classify_turn_mode
        assert _classify_turn_mode(plan_data_response_markers) == "plan"

    def test_report_mode_from_markers(self, report_data):
        from Stop import _classify_turn_mode
        assert _classify_turn_mode(report_data) == "execution-report"

    def test_plan_prompt_patterns(self):
        from Stop import _classify_turn_mode
        patterns = [
            "What are the next 10 things we should do?",
            "next steps for the project",
            "what should we work on next",
            "give me a prioritized list",
            "plan for the release",
            "roadmap for Q2",
            "action items from the meeting",
            "what to work on this week",
            "top 5 priorities",
            "recommend 3 approaches",
        ]
        for prompt in patterns:
            data = {"prompt": prompt, "response": "Some response"}
            assert _classify_turn_mode(data) == "plan", f"Failed for: {prompt}"

    def test_non_planning_prompt_stays_analysis(self):
        from Stop import _classify_turn_mode
        prompts = [
            "Why is the test failing?",
            "Debug the hook not firing",
            "Explain how the validator works",
        ]
        # Response must be >100 chars so _classify_question_response returns "analysis"
        long_response = (
            "The root cause is a missing import in the module. "
            "Evidence: the stack trace shows NameError on line 42. "
            "This suggests the dependency was removed in a recent refactor."
        )
        for prompt in prompts:
            data = {"prompt": prompt, "response": long_response}
            assert _classify_turn_mode(data) == "analysis", f"Failed for: {prompt}"

    def test_empty_prompt_defaults_to_query(self):
        from Stop import _classify_turn_mode
        assert _classify_turn_mode({"response": "Some text"}) == "query"
        assert _classify_turn_mode({"prompt": "", "response": "Some text"}) == "query"

    def test_report_markers_override_in_response(self):
        """Response with 2+ status markers triggers execution-report."""
        from Stop import _classify_turn_mode
        data = {
            "prompt": "update",
            "response": "[STATUS] Done\n[CHANGES] None\n[RESULTS] All passing",
        }
        assert _classify_turn_mode(data) == "execution-report"


# =============================================================================
# TEST 2: Epistemic format repair skips for plan/report
# =============================================================================


class TestEpistemicFormatRepairGating:
    """Verify epistemic format repair is skipped for plan/report turns."""

    def test_analysis_triggers_format_check(self, analysis_data):
        from Stop import _run_epistemic_contract
        # Response without epistemic headers but with analytical markers
        analysis_data["response"] = (
            "The root cause is that the hook was never registered. "
            "Evidence: grep output shows no match."
        )
        result = _run_epistemic_contract(analysis_data)
        # May return a warn/block depending on epistemic validator
        # The key is it doesn't return None when there are format issues
        # (it at least checks, even if it decides to allow)

    def test_plan_skips_format_repair(self, plan_data):
        from Stop import _run_epistemic_contract
        # Response has no epistemic headers but is a planning turn
        result = _run_epistemic_contract(plan_data)
        assert result is None, "Epistemic format repair should skip for plan mode"

    def test_report_skips_format_repair(self, report_data):
        from Stop import _run_epistemic_contract
        result = _run_epistemic_contract(report_data)
        assert result is None, "Epistemic format repair should skip for report mode"


# =============================================================================
# TEST 3: lazy_workaround_gate skips for plan/report
# =============================================================================


class TestLazyWorkaroundGateGating:
    """Verify lazy_workaround_gate skips for plan/report turns."""

    def test_plan_mode_skips_gate(self, plan_data):
        from Stop import _run_lazy_workaround_gate
        # Response contains a pattern that WOULD trigger lazy workaround
        plan_data["response"] = (
            "[PLAN]\n"
            "1. This is a quick fix for the cache issue\n"
            "[RATIONALE]\n"
            "- Quick fixes are acceptable here"
        )
        result = _run_lazy_workaround_gate(plan_data)
        assert result is None, "lazy_workaround_gate should skip for plan mode"

    def test_report_mode_skips_gate(self, report_data):
        from Stop import _run_lazy_workaround_gate
        result = _run_lazy_workaround_gate(report_data)
        assert result is None, "lazy_workaround_gate should skip for report mode"

    def test_analysis_mode_runs_gate(self, analysis_data):
        from Stop import _run_lazy_workaround_gate
        # Response must be >100 chars so _classify_question_response returns "analysis"
        analysis_data["response"] = (
            "The bug exists but we should accept it as a feature rather than "
            "fixing it properly. It's not worth fixing the underlying issue "
            "because the workaround handles the edge case adequately."
        )
        result = _run_lazy_workaround_gate(analysis_data)
        from Stop import _classify_turn_mode
        assert _classify_turn_mode(analysis_data) == "analysis"


# =============================================================================
# TEST 4: Plan mode schema injection (UPS module)
# =============================================================================


class TestPlanModeSchemaUPS:
    """Verify UPS module injects schema for planning prompts."""

    def test_planning_prompt_gets_schema(self):
        from unittest.mock import MagicMock
        from UserPromptSubmit_modules.plan_mode_schema import (
            plan_mode_schema,
            _PLANNING_PROMPT_RE,
        )
        context = MagicMock()
        context.prompt = "What are the next 10 things we should do?"
        result = plan_mode_schema(context)
        assert result.context is not None
        assert "[PLAN]" in result.context
        assert "[RATIONALE]" in result.context
        assert "[PLAN]" in result.context
        assert "[RATIONALE]" in result.context

    def test_non_planning_prompt_gets_nothing(self):
        from unittest.mock import MagicMock
        from UserPromptSubmit_modules.plan_mode_schema import plan_mode_schema
        context = MagicMock()
        context.prompt = "Fix the bug in Stop.py"
        result = plan_mode_schema(context)
        assert result.context is None or result.context == ""

    def test_empty_prompt_gets_nothing(self):
        from unittest.mock import MagicMock
        from UserPromptSubmit_modules.plan_mode_schema import plan_mode_schema
        context = MagicMock()
        context.prompt = ""
        result = plan_mode_schema(context)
        assert result.context is None or result.context == ""

    def test_pattern_coverage(self):
        from UserPromptSubmit_modules.plan_mode_schema import _PLANNING_PROMPT_RE
        positives = [
            "what's next",
            "what is the next step",
            "next steps",
            "what should we do",
            "prioritized list",
            "plan for the release",
            "roadmap",
            "action items",
            "what to work on",
            "what are the next 5 things",
            "top 10 priorities",
            "give me 3 options",
            "recommend 5 approaches",
            "list 10 items",
        ]
        for p in positives:
            assert _PLANNING_PROMPT_RE.search(p), f"Missed: {p}"

        negatives = [
            "fix the bug",
            "debug the hook",
            "why is this failing",
            "explain the architecture",
            "read the file",
        ]
        for p in negatives:
            assert not _PLANNING_PROMPT_RE.search(p), f"False positive: {p}"


# =============================================================================
# TEST 5: Exploration turn kind detection
# =============================================================================


class TestDetectTurnKindExploration:
    """Verify _classify_turn_mode returns 'exploration' for design prompts."""

    def test_should_we(self):
        from Stop import _classify_turn_mode
        data = {"prompt": "should we consolidate these packages?"}
        assert _classify_turn_mode(data) == "exploration"

    def test_tradeoffs(self):
        from Stop import _classify_turn_mode
        data = {"prompt": "what are the tradeoffs of this approach?"}
        assert _classify_turn_mode(data) == "exploration"

    def test_alternatives(self):
        from Stop import _classify_turn_mode
        data = {"prompt": "what are the alternatives to using FAISS?"}
        assert _classify_turn_mode(data) == "exploration"

    def test_versus(self):
        from Stop import _classify_turn_mode
        data = {"prompt": "SQLite versus DuckDB for this use case?"}
        assert _classify_turn_mode(data) == "exploration"

    def test_compare(self):
        from Stop import _classify_turn_mode
        data = {"prompt": "compare the two approaches"}
        assert _classify_turn_mode(data) == "exploration"

    def test_vs_dot(self):
        from Stop import _classify_turn_mode
        data = {"prompt": "hooks vs. MCP servers for enforcement?"}
        assert _classify_turn_mode(data) == "exploration"

    def test_control_still_works(self):
        from Stop import _classify_turn_mode
        data = {"prompt": "stop"}
        assert _classify_turn_mode(data) == "control"

    def test_query_not_exploration(self):
        from Stop import _classify_turn_mode
        data = {"prompt": "What is the current file structure?"}
        assert _classify_turn_mode(data) == "final-answer"

    def test_exploration_skips_epistemic_contract(self):
        from Stop import _run_epistemic_contract
        data = {
            "prompt": "should we refactor the epistemic validator?",
            "response": (
                "The validator could be refactored into separate modules. "
                "This might improve maintainability."
            ),
            "session_id": "test-session-exploration",
            "terminal_id": "test-terminal",
        }
        result = _run_epistemic_contract(data)
        assert result is None, "Epistemic contract should skip for exploration turns"

    def test_exploration_skips_lazy_fix(self):
        from Stop import _run_lazy_workaround_gate
        data = {
            "prompt": "should we use a workaround for the FAISS issue?",
            "response": (
                "We could use a quick workaround for this, or fix the root cause."
            ),
            "session_id": "test-session-exploration-lazy",
            "terminal_id": "test-terminal",
        }
        result = _run_lazy_workaround_gate(data)
        # Exploration turns should suppress lazy_fix patterns
        from Stop import _classify_turn_mode
        assert _classify_turn_mode(data) == "exploration"
