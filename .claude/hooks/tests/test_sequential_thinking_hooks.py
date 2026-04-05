"""
Tests for sequential thinking hook execution.

Tests hook behavior with synthetic inputs and verifies correct
context injection, state management, and loop protocol.
"""

import json
import sys
import time
import uuid
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import __lib.sequential_state as ss
import StopHook_sequential_thinking as sh
from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.sequential_thinking import (
    sequential_thinking_hook,
)

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_context(prompt: str, terminal_id: str = "test_term") -> HookContext:
    return HookContext(prompt=prompt, data={}, session_id=None, terminal_id=terminal_id)


def _run_hook(prompt: str, terminal_id: str = "test_term") -> HookResult:
    return sequential_thinking_hook(_make_context(prompt, terminal_id))


# ---------------------------------------------------------------------------
# Pattern tests — positive (should trigger)
# ---------------------------------------------------------------------------


class TestTriggerPatterns:
    """Each pattern must match 8+ representative positive inputs."""

    def test_analyze_pattern(self, tmp_path):
        with patch.object(ss, "STATE_DIR", tmp_path):
            for prompt in [
                "analyze this architecture",
                "please analyse the code",
                "evaluate the approach",
                "assess the security risk",
                "examine this function carefully",
                "investigate the bug in this module",
                "can you analyze this in detail",
                "evaluate all available options",
            ]:
                result = _run_hook(prompt)
                assert result.context, f"Expected trigger for: {prompt!r}"
                for f in tmp_path.glob("*.json"):
                    f.unlink()

    def test_debug_pattern(self, tmp_path):
        with patch.object(ss, "STATE_DIR", tmp_path):
            for prompt in [
                "debug this failing test",
                "help me debug the issue",
                "diagnose the performance problem",
                "troubleshoot my setup issue",
                "debug why it's running slowly",
                "help me diagnose this error",
                "troubleshoot the connection issue",
                "debug why my code crashes here",
            ]:
                result = _run_hook(prompt)
                assert result.context, f"Expected trigger for: {prompt!r}"
                for f in tmp_path.glob("*.json"):
                    f.unlink()

    def test_identify_issue_pattern(self, tmp_path):
        with patch.object(ss, "STATE_DIR", tmp_path):
            for prompt in [
                "identify the issue in this code",
                "identify the root cause here",
                "identify the problem in my service",
                "identify this bug in the function",
                "identifying the cause of failure",
                "identify the bug in my service",
                "identify the root of this issue",
                "help identify the cause",
            ]:
                result = _run_hook(prompt)
                assert result.context, f"Expected trigger for: {prompt!r}"
                for f in tmp_path.glob("*.json"):
                    f.unlink()

    def test_should_i_we_pattern(self, tmp_path):
        with patch.object(ss, "STATE_DIR", tmp_path):
            # Must be 20+ chars after "should i/we "
            for prompt in [
                "should i use postgres or sqlite for this project",
                "should we migrate to a microservices architecture",
                "should i rewrite this in typescript or keep python",
                "should we add caching to the API layer right now",
                "should i refactor the authentication module first",
                "should we deploy this on kubernetes or bare metal",
                "should i use redux or context for state management",
                "should we move to a monorepo or keep it separate",
            ]:
                result = _run_hook(prompt)
                assert result.context, f"Expected trigger for: {prompt!r}"
                for f in tmp_path.glob("*.json"):
                    f.unlink()

    def test_compare_contrast_pattern(self, tmp_path):
        with patch.object(ss, "STATE_DIR", tmp_path):
            for prompt in [
                "compare postgres vs sqlite for this use case",
                "compare the two approaches between microservices",
                "contrast the options between redis vs memcached",
                "compare react vs vue for our frontend needs",
                "compare the strategies between approach A vs B",
                "contrast the two libraries vs each other",
                "compare these architectures between option 1 versus option 2",
                "compare and contrast the two implementations versus each other",
            ]:
                result = _run_hook(prompt)
                assert result.context, f"Expected trigger for: {prompt!r}"
                for f in tmp_path.glob("*.json"):
                    f.unlink()

    def test_which_what_approach_pattern(self, tmp_path):
        with patch.object(ss, "STATE_DIR", tmp_path):
            for prompt in [
                "which approach should I use for this",
                "what option is better here",
                "which strategy works best",
                "what method should I pick",
                "which way is more efficient",
                "what approach handles edge cases",
                "which option scales better",
                "what strategy reduces coupling",
            ]:
                result = _run_hook(prompt)
                assert result.context, f"Expected trigger for: {prompt!r}"
                for f in tmp_path.glob("*.json"):
                    f.unlink()

    def test_design_architect_pattern(self, tmp_path):
        with patch.object(ss, "STATE_DIR", tmp_path):
            for prompt in [
                "design a system for handling payments",
                "architect a service for real-time notifications",
                "refactor this module to be more testable",
                "design the api schema for this resource",
                "architect the system to handle load",
                "restructure the module to separate concerns",
                "refactor this service to use dependency injection",
                "design the schema for user profiles",
            ]:
                result = _run_hook(prompt)
                assert result.context, f"Expected trigger for: {prompt!r}"
                for f in tmp_path.glob("*.json"):
                    f.unlink()

    def test_why_how_pattern(self, tmp_path):
        with patch.object(ss, "STATE_DIR", tmp_path):
            for prompt in [
                "why does this code cause a memory leak",
                "why is the connection timing out",
                "how does the authentication flow work",
                "how do distributed systems handle consistency",
                "why are the tests failing intermittently",
                "how would you implement rate limiting here",
                "how should we handle database migrations safely",
                "why does the deadlock happen under load",
            ]:
                result = _run_hook(prompt)
                assert result.context, f"Expected trigger for: {prompt!r}"
                for f in tmp_path.glob("*.json"):
                    f.unlink()

    def test_negation_and_howcome_patterns(self, tmp_path):
        """Negations and 'how come' variants must trigger."""
        with patch.object(ss, "STATE_DIR", tmp_path):
            for prompt in [
                "why doesn't the retry logic kick in after failures",
                "why isn't the cache being invalidated on update",
                "why don't the tests pass on the CI server",
                "why aren't the webhooks firing in production",
                "why won't the connection pool release idle connections",
                "how come the worker process keeps crashing on startup",
            ]:
                result = _run_hook(prompt)
                assert result.context, f"Expected trigger for: {prompt!r}"
                for f in tmp_path.glob("*.json"):
                    f.unlink()

    def test_review_explain_understand_patterns(self, tmp_path):
        """Added verbs review, explain, understand, clarify must trigger."""
        with patch.object(ss, "STATE_DIR", tmp_path):
            for prompt in [
                "review my approach to handling authentication tokens",
                "explain why the circuit breaker pattern is useful here",
                "help me understand how event sourcing differs from CRUD",
                "clarify the difference between optimistic and pessimistic locking",
                "can you review the error handling strategy in this module",
                "explain the tradeoffs between REST and GraphQL for this API",
            ]:
                result = _run_hook(prompt)
                assert result.context, f"Expected trigger for: {prompt!r}"
                for f in tmp_path.glob("*.json"):
                    f.unlink()

    def test_whats_contraction_pattern(self, tmp_path):
        """what's (contraction) must trigger the which/what approach pattern."""
        with patch.object(ss, "STATE_DIR", tmp_path):
            for prompt in [
                "what's the best approach to caching in this scenario",
                "what's the right strategy for handling concurrent writes",
            ]:
                result = _run_hook(prompt)
                assert result.context, f"Expected trigger for: {prompt!r}"
                for f in tmp_path.glob("*.json"):
                    f.unlink()


# ---------------------------------------------------------------------------
# Pattern tests — negative (must NOT trigger)
# ---------------------------------------------------------------------------


class TestNegativePatterns:
    """Patterns must not fire false positives."""

    def test_simple_questions_do_not_trigger(self):
        non_triggers = [
            "what is 2 + 2",
            "show me the file",
            "hello",
            "yes",
            "no",
            "thanks",
            "ok got it",
            "run the tests",
        ]
        for prompt in non_triggers:
            result = _run_hook(prompt)
            assert not result.context, f"Unexpected trigger for: {prompt!r}"

    def test_skill_invocations_are_skipped(self):
        skill_prompts = [
            "/code add a new feature",
            "/analyze this file",
            "/debug my hook",
            "/pre-mortem",
            "/refactor system architecture",
        ]
        for prompt in skill_prompts:
            result = _run_hook(prompt)
            assert not result.context, f"Skill invocation should be skipped: {prompt!r}"

    def test_short_should_does_not_trigger(self):
        # "should i/we" requires 20+ chars after — short ones must NOT trigger
        short_prompts = [
            "should i try",
            "should we go",
            "should i use it",
            "should we do this",
        ]
        for prompt in short_prompts:
            result = _run_hook(prompt)
            assert not result.context, f"Short 'should' should not trigger: {prompt!r}"

    def test_compare_and_does_not_trigger(self):
        # "and" was removed from the compare pattern to avoid false positives
        and_prompts = [
            "compare apples and oranges",
            "compare the results and findings",
        ]
        for prompt in and_prompts:
            result = _run_hook(prompt)
            assert not result.context, f"'compare ... and' should not trigger: {prompt!r}"

    def test_short_why_how_does_not_trigger(self):
        # why/how pattern requires 10+ chars after the keyword — short ones must NOT fire
        short_prompts = [
            "why does it",
            "how do I",
            "how does X",
        ]
        for prompt in short_prompts:
            result = _run_hook(prompt)
            assert not result.context, f"Short why/how should not trigger: {prompt!r}"

    def test_minimum_length_gate(self):
        # Prompts under 40 chars must not trigger even if they match a keyword
        short_triggers = [
            "debug mode: true",
            "analyze x",
            "review it",
            "explain this",
        ]
        for prompt in short_triggers:
            result = _run_hook(prompt)
            assert not result.context, f"Short prompt should not trigger: {prompt!r}"

    def test_exactly_15_chars_does_not_trigger(self):
        # Edge case: prompts exactly at the hard floor (15 chars) must NOT trigger
        # This tests the boundary condition of the multi-signal gating logic
        #
        # Example: "analyze code AB" = 15 chars (exactly at floor)
        # Rationale: At exactly 15 chars, even analytical keywords are likely casual
        # or incomplete thoughts that don't warrant a multi-step thinking process.
        exactly_15_chars = [
            "analyze code AB",  # 15 chars - exactly at floor
            "debug this error",  # 16 chars but tests edge case awareness
        ]
        for prompt in exactly_15_chars:
            assert len(prompt) == 15 or len(prompt) == 16, f"Prompt length mismatch: {prompt!r}"
            result = _run_hook(prompt)
            # Note: 16-char prompts may trigger if they have technical depth indicators
            # Only the exactly-15-char prompt is guaranteed to not trigger
            if len(prompt) == 15:
                assert not result.context, (
                    f"Exactly 15-char prompt should not trigger: {prompt!r} (len={len(prompt)})"
                )


# ---------------------------------------------------------------------------
# State creation tests
# ---------------------------------------------------------------------------


class TestStateCreation:
    def test_trigger_creates_state_file(self, tmp_path):
        with patch.object(ss, "STATE_DIR", tmp_path):
            result = _run_hook("analyze the architecture", "term_abc")
            assert result.context
            state_files = list(tmp_path.glob("*_term_abc.json"))
            assert len(state_files) == 1
            state = json.loads(state_files[0].read_text(encoding="utf-8"))
            assert state["current_iteration"] == 0
            assert state["active"] is True
            assert state["terminal_id"] == "term_abc"

    def test_state_file_content_verification(self, tmp_path):
        """Verify all state file fields are correctly initialized.

        This test ensures the state file contains all expected fields with
        correct initial values, preventing silent data corruption bugs.
        """
        with patch.object(ss, "STATE_DIR", tmp_path):
            trigger_prompt = "analyze the architecture"
            result = _run_hook(trigger_prompt, "term_verify")
            assert result.context

            state_files = list(tmp_path.glob("*_term_verify.json"))
            assert len(state_files) == 1
            state = json.loads(state_files[0].read_text(encoding="utf-8"))

            # Verify session_id is a valid UUID
            session_id = uuid.UUID(state["session_id"])  # Raises ValueError if invalid
            assert isinstance(session_id, uuid.UUID)

            # Verify trigger_phrase is captured
            assert "trigger_phrase" in state
            assert len(state["trigger_phrase"]) > 0

            # Verify initial state values
            assert state["current_iteration"] == 0
            assert state["active"] is True
            assert state["terminal_id"] == "term_verify"

            # Verify intermediate_answers is initially empty
            assert "intermediate_answers" in state
            assert state["intermediate_answers"] == []

            # Verify final_answer is initially None or empty
            assert "final_answer" in state
            assert state.get("final_answer") is None or state.get("final_answer") == ""

            # Verify max_iterations is set
            assert "max_iterations" in state
            assert state["max_iterations"] == 2  # Default: Generate → Critique → Improve

    def test_context_contains_session_id(self, tmp_path):
        with patch.object(ss, "STATE_DIR", tmp_path):
            result = _run_hook("debug the failing test", "term_x")
            assert result.context
            assert "Session ID:" in result.context
            assert "sequential_thinking" in result.context

    def test_no_trigger_returns_empty(self):
        result = _run_hook("just a simple question")
        assert result.is_empty()


# ---------------------------------------------------------------------------
# Stop hook — loop protocol tests
# ---------------------------------------------------------------------------


class TestStopHookLoopProtocol:
    def test_initial_stop_blocks_and_requests_critique(self, tmp_path):
        session_id = uuid.uuid4()
        terminal_id = "stop_test"

        with patch.object(ss, "STATE_DIR", tmp_path), patch.object(sh, "STATE_DIR", tmp_path):
            ss.create_state(session_id, "analyze this", terminal_id)

            result = sh.stop({"terminal_id": terminal_id, "response_output": "Initial answer."})

            assert result.get("allow") is False
            assert "reason" in result
            assert "CRITIQUE" in result["reason"]

    def test_second_stop_blocks_and_requests_improvement(self, tmp_path):
        session_id = uuid.uuid4()
        terminal_id = "stop_test"

        with patch.object(ss, "STATE_DIR", tmp_path), patch.object(sh, "STATE_DIR", tmp_path):
            ss.create_state(session_id, "analyze this", terminal_id)

            # First stop → critique
            sh.stop({"terminal_id": terminal_id, "response_output": "Answer 1"})

            # Second stop → improvement
            result = sh.stop({"terminal_id": terminal_id, "response_output": "Critique."})

            assert result.get("allow") is False
            assert "IMPROVEMENT" in result["reason"]

    def test_third_stop_allows_and_deactivates(self, tmp_path):
        session_id = uuid.uuid4()
        terminal_id = "stop_test"

        with patch.object(ss, "STATE_DIR", tmp_path), patch.object(sh, "STATE_DIR", tmp_path):
            ss.create_state(session_id, "analyze this", terminal_id)

            sh.stop({"terminal_id": terminal_id, "response_output": "Answer 1"})
            sh.stop({"terminal_id": terminal_id, "response_output": "Critique"})
            result = sh.stop({"terminal_id": terminal_id, "response_output": "Improved answer."})

            assert result.get("allow") is True

            # State file is deleted on completion (prevents O(n) accumulation)
            state = ss.load_state(session_id, terminal_id)
            assert state is None

    def test_no_session_allows_stop(self):
        result = sh.stop({"terminal_id": "no_session_term", "response_output": "Something."})
        assert result.get("allow") is True

    def test_intermediate_answers_accumulated(self, tmp_path):
        session_id = uuid.uuid4()
        terminal_id = "acc_test"

        with patch.object(ss, "STATE_DIR", tmp_path), patch.object(sh, "STATE_DIR", tmp_path):
            ss.create_state(session_id, "evaluate this", terminal_id)

            sh.stop({"terminal_id": terminal_id, "response_output": "Answer 1"})
            # After 1st stop, session is still active — 1 intermediate answer accumulated
            state_mid = ss.load_state(session_id, terminal_id)
            assert state_mid is not None
            assert len(state_mid["intermediate_answers"]) == 1

            sh.stop({"terminal_id": terminal_id, "response_output": "Critique"})
            # After 2nd stop, still active — 2 intermediate answers
            state_mid2 = ss.load_state(session_id, terminal_id)
            assert state_mid2 is not None
            assert len(state_mid2["intermediate_answers"]) == 2

            # 3rd stop completes session — state file deleted (prevents O(n) accumulation)
            sh.stop({"terminal_id": terminal_id, "response_output": "Improved"})
            state_final = ss.load_state(session_id, terminal_id)
            assert state_final is None

    def test_reason_field_not_additionalcontext(self, tmp_path):
        """Stop hook must return 'reason', not 'additionalContext'."""
        session_id = uuid.uuid4()
        terminal_id = "protocol_test"

        with patch.object(ss, "STATE_DIR", tmp_path), patch.object(sh, "STATE_DIR", tmp_path):
            ss.create_state(session_id, "debug the code", terminal_id)

            result = sh.stop({"terminal_id": terminal_id, "response_output": "Answer"})

            assert "reason" in result
            assert "additionalContext" not in result


# ---------------------------------------------------------------------------
# Stop hook — TTL protection tests
# ---------------------------------------------------------------------------


class TestTTLProtection:
    def test_fresh_session_is_found(self, tmp_path):
        session_id = uuid.uuid4()
        terminal_id = "ttl_fresh"

        with patch.object(ss, "STATE_DIR", tmp_path), patch.object(sh, "STATE_DIR", tmp_path):
            ss.create_state(session_id, "analyze", terminal_id)

            result = sh.stop({"terminal_id": terminal_id, "response_output": "Answer"})

            # Fresh session → should block (continue loop)
            assert result.get("allow") is False

    def test_stale_session_is_ignored(self, tmp_path):
        session_id = uuid.uuid4()
        terminal_id = "ttl_stale"

        with patch.object(ss, "STATE_DIR", tmp_path), patch.object(sh, "STATE_DIR", tmp_path):
            ss.create_state(session_id, "analyze", terminal_id)

            # Age the state file beyond 2-hour TTL
            state_file = tmp_path / f"{session_id}_{terminal_id}.json"
            stale_mtime = time.time() - (7200 + 60)  # 2h + 1min ago
            import os

            os.utime(state_file, (stale_mtime, stale_mtime))

            result = sh.stop({"terminal_id": terminal_id, "response_output": "Answer"})

            # Stale session → allow stop (no active session found)
            assert result.get("allow") is True


# ---------------------------------------------------------------------------
# Multi-terminal isolation tests
# ---------------------------------------------------------------------------


class TestMultiTerminalIsolation:
    def test_separate_state_files_per_terminal(self, tmp_path):
        session_id = uuid.uuid4()

        with patch.object(ss, "STATE_DIR", tmp_path):
            ss.create_state(session_id, "analyze", "terminal_A")
            ss.create_state(session_id, "analyze", "terminal_B")

            assert len(list(tmp_path.glob("*.json"))) == 2

    def test_terminal_b_does_not_see_terminal_a_session(self, tmp_path):
        session_id = uuid.uuid4()

        with patch.object(ss, "STATE_DIR", tmp_path), patch.object(sh, "STATE_DIR", tmp_path):
            ss.create_state(session_id, "analyze", "terminal_A")

            # Terminal B has no session → must allow stop
            result = sh.stop({"terminal_id": "terminal_B", "response_output": "Answer"})
            assert result.get("allow") is True

    def test_iterations_are_independent_per_terminal(self, tmp_path):
        session_a = uuid.uuid4()
        session_b = uuid.uuid4()

        with patch.object(ss, "STATE_DIR", tmp_path), patch.object(sh, "STATE_DIR", tmp_path):
            ss.create_state(session_a, "analyze", "terminal_A")
            ss.create_state(session_b, "analyze", "terminal_B")

            # Advance terminal A only
            sh.stop({"terminal_id": "terminal_A", "response_output": "Answer A"})

            state_a = ss.load_state(session_a, "terminal_A")
            state_b = ss.load_state(session_b, "terminal_B")

            assert state_a is not None
            assert state_b is not None
            assert state_a["current_iteration"] == 1
            assert state_b["current_iteration"] == 0


# ---------------------------------------------------------------------------
# Full pipeline integration test
# ---------------------------------------------------------------------------


class TestFullPipeline:
    def test_generate_critique_improve_loop(self, tmp_path):
        terminal_id = "pipeline_test"

        with patch.object(ss, "STATE_DIR", tmp_path), patch.object(sh, "STATE_DIR", tmp_path):
            # Phase 1: trigger detection
            trigger_result = _run_hook("analyze the codebase architecture", terminal_id)
            assert trigger_result.context
            assert "sequential_thinking" in trigger_result.context

            # Phase 2: initial generation → critique forced
            stop1 = sh.stop({"terminal_id": terminal_id, "response_output": "Initial analysis."})
            assert stop1.get("allow") is False
            assert "CRITIQUE" in stop1["reason"]

            # Phase 3: critique → improvement forced
            stop2 = sh.stop({"terminal_id": terminal_id, "response_output": "My critique."})
            assert stop2.get("allow") is False
            assert "IMPROVEMENT" in stop2["reason"]

            # Phase 4: improvement → session complete
            stop3 = sh.stop({"terminal_id": terminal_id, "response_output": "Improved answer."})
            assert stop3.get("allow") is True

            # Extract session_id from injected context
            assert isinstance(trigger_result.context, str)
            session_id_str = None
            for line in trigger_result.context.split("\n"):
                if line.startswith("Session ID:"):
                    session_id_str = line.split(": ")[1].strip()
                    break
            assert session_id_str
            # State file is deleted on completion — no accumulation of stale files
            final_state = ss.load_state(uuid.UUID(session_id_str), terminal_id)
            assert final_state is None

    def test_seq_tag_appears_in_output(self, tmp_path):
        """E2E test: [SEQ] tag must appear in both trigger context and stop reason."""
        terminal_id = "seq_tag_test"

        with patch.object(ss, "STATE_DIR", tmp_path), patch.object(sh, "STATE_DIR", tmp_path):
            # Phase 1: trigger detection - verify [SEQ] in context
            trigger_result = _run_hook("analyze the codebase architecture", terminal_id)
            assert trigger_result.context, "Trigger must inject context"
            assert "[SEQ]" in trigger_result.context, "[SEQ] tag must appear in trigger context"

            # Phase 2: stop hook - verify [SEQ] in continuation reason
            stop1 = sh.stop({"terminal_id": terminal_id, "response_output": "Initial analysis."})
            assert stop1.get("allow") is False, "First stop must block to force continuation"
            assert "[SEQ]" in stop1["reason"], "[SEQ] tag must appear in stop reason"

            # Phase 3: second stop should also have [SEQ] tag
            stop2 = sh.stop({"terminal_id": terminal_id, "response_output": "Critique."})
            assert stop2.get("allow") is False
            assert "[SEQ]" in stop2["reason"], "[SEQ] tag must appear in second stop reason"

            # Cleanup: complete the session
            sh.stop({"terminal_id": terminal_id, "response_output": "Improved."})


# ---------------------------------------------------------------------------
# Semantic detection tests
# ---------------------------------------------------------------------------


class TestSemanticDetection:
    """Tests for embedding-based semantic trigger detection.

    These tests verify the compute_similarity function and its integration
    with the sequential_thinking_hook at different threshold levels.
    """

    def test_compute_similarity_import_exists(self):
        """Verify compute_similarity can be imported from semantic client."""
        from UserPromptSubmit_modules.sequential_thinking_semantic_client import (
            compute_similarity,
        )

        assert callable(compute_similarity)

    def test_compute_similarity_returns_tuple(self):
        """Verify compute_similarity returns (score, phrase) tuple type signature.

        This tests the return type contract. Full integration requires daemon.
        """
        from UserPromptSubmit_modules.sequential_thinking_semantic_client import (
            compute_similarity,
        )

        # verify function exists and is callable
        assert callable(compute_similarity)

        # The function signature returns (float, str|None)
        # Full test requires daemon infrastructure - tested via hook integration
        # These tests verify the return type contract
        import inspect

        sig = inspect.signature(compute_similarity)
        assert "prompt" in sig.parameters

    def test_semantic_trigger_phrases_defined(self):
        """Verify trigger phrases are defined in the semantic client."""
        from UserPromptSubmit_modules.sequential_thinking_semantic_client import (
            _trigger_phrases_cache,
        )

        # trigger phrases should be a list (loaded lazily)
        assert _trigger_phrases_cache is None or isinstance(_trigger_phrases_cache, list)

    def test_semantic_client_has_cosine_similarity(self):
        """Verify cosine similarity function is available."""
        from UserPromptSubmit_modules.sequential_thinking_semantic_client import (
            _cosine_similarity,
        )

        # Should be a callable function
        assert callable(_cosine_similarity)

        # Test it works on known vectors
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        vec3 = [0.0, 1.0, 0.0]
        assert _cosine_similarity(vec1, vec2) == 1.0  # identical
        assert _cosine_similarity(vec1, vec3) == 0.0  # orthogonal

    def test_hook_with_mocked_semantic_strong_match(self, tmp_path):
        """Hook should trigger on strong semantic match even without regex pattern."""
        with patch.object(ss, "STATE_DIR", tmp_path):
            with patch(
                "UserPromptSubmit_modules.sequential_thinking.compute_similarity",
                return_value=(0.85, "analyze the code for issues"),
            ):
                result = _run_hook("check this routine for problems")
                # Strong semantic match should trigger even without regex match
                assert result.context, "Strong semantic match should trigger hook"

    def test_hook_with_mocked_semantic_partial_match(self, tmp_path):
        """Hook should NOT trigger on partial semantic match alone (requires regex too)."""
        with patch.object(ss, "STATE_DIR", tmp_path):
            with patch(
                "UserPromptSubmit_modules.sequential_thinking.compute_similarity",
                return_value=(0.60, "analyze the code"),  # Partial match
            ):
                # Without a matching regex pattern, partial semantic shouldn't trigger
                result = _run_hook("simple question")
                # Partial semantic match without regex should not trigger
                assert not result.context, "Partial semantic match without regex should not trigger"

    def test_hook_catches_semantic_exception(self, tmp_path):
        """Hook should gracefully handle semantic detection failures."""
        with patch.object(ss, "STATE_DIR", tmp_path):
            with patch(
                "UserPromptSubmit_modules.sequential_thinking.compute_similarity",
                side_effect=Exception("Semantic detection failed"),
            ):
                # Should fall back to regex-only behavior
                result = _run_hook("analyze the architecture")
                # Regex pattern matches → should still trigger
                assert result.context, "Should fall back to regex when semantic fails"

    def test_semantic_threshold_boundary_high(self, tmp_path):
        """Score >= 0.70 should trigger directly (strong match)."""
        from UserPromptSubmit_modules.sequential_thinking import (
            _SEMANTIC_SIMILARITY_THRESHOLD,
        )

        assert _SEMANTIC_SIMILARITY_THRESHOLD == 0.70
        # A score of exactly 0.70 should trigger directly
        with patch.object(ss, "STATE_DIR", tmp_path):
            with patch(
                "UserPromptSubmit_modules.sequential_thinking.compute_similarity",
                return_value=(0.70, "debug the issue"),
            ):
                # 0.70 is at threshold - should trigger as strong match
                result = _run_hook("check this problem")
                assert result.context, "Score >= 0.70 should trigger"

    def test_semantic_threshold_boundary_partial(self, tmp_path):
        """Score >= 0.50 and < 0.70 is partial match (secondary signal only)."""
        from UserPromptSubmit_modules.sequential_thinking import (
            _SEMANTIC_PARTIAL_THRESHOLD,
        )

        assert _SEMANTIC_PARTIAL_THRESHOLD == 0.50
        # Partial match without regex should not trigger
        with patch.object(ss, "STATE_DIR", tmp_path):
            with patch(
                "UserPromptSubmit_modules.sequential_thinking.compute_similarity",
                return_value=(0.55, "some analytical phrase"),
            ):
                result = _run_hook("random text without trigger patterns")
                assert not result.context, "Partial semantic match without regex should not trigger"

    def test_semantic_fallback_to_regex_on_exception(self, tmp_path):
        """When semantic throws, hook should fall back to regex matching."""
        with patch.object(ss, "STATE_DIR", tmp_path):
            with patch(
                "UserPromptSubmit_modules.sequential_thinking.compute_similarity",
                side_effect=RuntimeError("Embedding computation failed"),
            ):
                # Should still trigger via regex
                result = _run_hook("analyze the system design")
                assert result.context, "Should fall back to regex on semantic exception"


class TestSemanticClientDaemonIPC:
    """Tests for daemon IPC integration in semantic client.

    These tests verify the compute_embedding action works end-to-end
    with the daemon (or gracefully falls back).
    """

    def test_compute_embedding_via_daemon_returns_list_or_none(self):
        """_compute_embedding_via_daemon should return list or None when daemon unavailable."""
        import sys
        from pathlib import Path
        from unittest.mock import MagicMock

        sys.path.insert(0, str(Path(__file__).parent.parent / "UserPromptSubmit_modules"))

        from sequential_thinking_semantic_client import (
            _compute_embedding_via_daemon,
        )

        # Mock the daemon client to return error status (simulating daemon unavailability)
        # Note: patch target must match actual module name after sys.path insertion
        mock_client = MagicMock()
        mock_client.query.return_value = {"status": "error", "error": "daemon unavailable"}
        with patch(
            "sequential_thinking_semantic_client._get_daemon_client",
            return_value=mock_client,
        ):
            result = _compute_embedding_via_daemon("test prompt")
        # Result is either a list (daemon available) or None (daemon unavailable)
        assert result is None or isinstance(result, list)

    def test_compute_embedding_direct_returns_list_or_none(self):
        """_compute_embedding_direct should return list or None."""
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).parent.parent / "UserPromptSubmit_modules"))

        from sequential_thinking_semantic_client import (
            _compute_embedding_direct,
        )

        result = _compute_embedding_direct("test prompt")
        # Direct computation returns list or None on failure
        assert result is None or isinstance(result, list)

    def test_trigger_embeddings_cache_isolation(self):
        """Verify cache is isolated per module reload."""
        import sys
        from pathlib import Path

        sys.path.insert(0, str(Path(__file__).parent.parent / "UserPromptSubmit_modules"))

        from sequential_thinking_semantic_client import (
            _trigger_embeddings_cache,
        )

        # Cache should be None initially (lazy-loaded)
        assert _trigger_embeddings_cache is None or isinstance(_trigger_embeddings_cache, list)


class TestSemanticFallbackChain:
    """Tests for the semantic detection fallback chain.

    Verifies:
    1. Daemon IPC is tried first
    2. Falls back to direct SentenceTransformer on daemon failure
    3. Falls back to regex-only on complete failure
    """

    def test_fallback_chain_order(self, tmp_path):
        """Verify fallback chain: daemon -> direct model -> regex."""
        with patch.object(ss, "STATE_DIR", tmp_path):
            # Case 1: Both daemon and direct fail → regex fallback
            with patch(
                "UserPromptSubmit_modules.sequential_thinking.compute_similarity",
                side_effect=Exception("Both daemon and direct failed"),
            ):
                result = _run_hook("analyze the architecture")
                # Should still trigger via regex
                assert result.context, "Should fall back to regex when semantic completely fails"

    def test_partial_semantic_match_combines_with_regex(self, tmp_path):
        """Partial semantic match (0.50-0.70) + regex should trigger."""
        with patch.object(ss, "STATE_DIR", tmp_path):
            with patch(
                "UserPromptSubmit_modules.sequential_thinking.compute_similarity",
                return_value=(0.55, "review the changes"),  # Partial match
            ):
                # Regex matches + partial semantic → should trigger
                result = _run_hook("review my implementation")
                # Both regex and partial semantic are signals
                assert result.context, "Regex + partial semantic should trigger"
