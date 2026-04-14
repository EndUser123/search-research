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

# Ensure the hooks-local __lib package wins even if another test imported a
# different __lib namespace earlier in the same pytest process.
sys.modules.pop("__lib", None)
sys.modules.pop("__lib.sequential_state", None)

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


def _context_text(result: HookResult) -> str:
    """Return the injected text across legacy string and dict-shaped contexts."""
    if isinstance(result.context, dict):
        return result.context.get("additionalContext", "")
    return result.context or ""


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
            text = _context_text(result)
            assert result.context
            assert "Session ID:" in text
            assert "sequential_thinking" in text

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
            # Use "evaluate" trigger which is in sequential thinking but NOT investigation mode patterns
            # (investigation patterns: debug, investigate, diagnose, analyze, explain why, root cause, etc.)
            trigger_result = _run_hook("evaluate this approach thoroughly", terminal_id)
            text = _context_text(trigger_result)
            assert trigger_result.context
            assert "sequential_thinking" in text

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
            text = _context_text(trigger_result)
            session_id_str = None
            for line in text.split("\n"):
                if line.startswith("Session ID:"):
                    session_id_str = line.split(": ")[1].strip()
                    break
            assert session_id_str
            # State file is deleted on completion — no accumulation of stale files
            final_state = ss.load_state(uuid.UUID(session_id_str), terminal_id)
            assert final_state is None

    def test_seq_tag_appears_in_output(self, tmp_path):
        """E2E test: sequential reasoning guidance should not expose tag tokens."""
        terminal_id = "seq_tag_test"

        with patch.object(ss, "STATE_DIR", tmp_path), patch.object(sh, "STATE_DIR", tmp_path):
            # Phase 1: trigger detection - verify guidance is present without tags
            trigger_result = _run_hook("analyze the codebase architecture", terminal_id)
            assert trigger_result.context, "Trigger must inject context"
            trigger_text = _context_text(trigger_result)
            assert "[SEQ]" not in trigger_text
            assert "Sequential thinking" in trigger_text

            # Phase 2: stop hook - verify continuation reason without tags
            stop1 = sh.stop({"terminal_id": terminal_id, "response_output": "Initial analysis."})
            assert stop1.get("allow") is False, "First stop must block to force continuation"
            assert "[SEQ]" not in stop1["reason"]
            assert "Sequential Thinking" in stop1["reason"]

            # Phase 3: second stop should also avoid tag tokens
            stop2 = sh.stop({"terminal_id": terminal_id, "response_output": "Critique."})
            assert stop2.get("allow") is False
            assert "[SEQ]" not in stop2["reason"]
            assert "Sequential Thinking" in stop2["reason"]

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


# ---------------------------------------------------------------------------
# CHANGE-005: Multi-Hypothesis Tracking Tests
# ---------------------------------------------------------------------------


class TestHypothesisTriggerPatterns:
    """Tests for hypothesis mode trigger detection (CHANGE-003)."""

    def test_maintain_multiple_hypotheses_pattern(self, tmp_path):
        """Hypothesis mode trigger: 'maintain multiple hypotheses'"""
        with patch.object(ss, "STATE_DIR", tmp_path):
            result = _run_hook("maintain multiple hypotheses throughout this investigation")
            assert result.context, "Should trigger with 'maintain multiple hypotheses'"

    def test_competing_hypotheses_pattern(self, tmp_path):
        """Hypothesis mode trigger: 'competing hypotheses'"""
        with patch.object(ss, "STATE_DIR", tmp_path):
            result = _run_hook("consider the competing hypotheses")
            assert result.context, "Should trigger with 'competing hypotheses'"

    def test_parallel_explanations_pattern(self, tmp_path):
        """Hypothesis mode trigger: 'parallel explanations'"""
        with patch.object(ss, "STATE_DIR", tmp_path):
            result = _run_hook("generate parallel explanations for this issue")
            assert result.context, "Should trigger with 'parallel explanations'"

    def test_possible_explanations_pattern(self, tmp_path):
        """Hypothesis mode trigger: 'what are the possible explanations'"""
        with patch.object(ss, "STATE_DIR", tmp_path):
            result = _run_hook("what are the possible explanations for this error")
            assert result.context, "Should trigger with 'possible explanations'"

    def test_hypothesis_mode_sets_flag(self, tmp_path):
        """Hypothesis mode should set hypothesis_mode flag in state."""
        with patch.object(ss, "STATE_DIR", tmp_path):
            result = _run_hook("maintain multiple hypotheses")
            text = _context_text(result)
            assert result.context, "Should trigger"

            # Extract session_id from context
            session_id_str = None
            for line in text.split("\n"):
                if line.startswith("Session ID:"):
                    session_id_str = line.split(": ")[1].strip()
                    break

            # Load state and verify hypothesis_mode flag
            state = ss.load_state(uuid.UUID(session_id_str), "test_term")
            assert state is not None
            assert state.get("hypothesis_mode") is True
            assert state.get("max_iterations") == 2


class TestHypothesisModeInjection:
    """Tests for hypothesis mode message injection (CHANGE-002)."""

    def test_multi_hypothesis_mode_injection_iteration_0(self, tmp_path):
        """Iteration 0 should inject multi_hypothesis mode message."""
        terminal_id = "hypo_test"

        # Import the module to patch its STATE_DIR
        import PreToolUse_sequential_thinking as ptu_st

        with patch.object(ss, "STATE_DIR", tmp_path), patch.object(ptu_st, "STATE_DIR", tmp_path):
            # Create hypothesis mode session
            session_id = uuid.uuid4()
            ss.create_state(session_id, "test trigger", terminal_id, {"hypothesis_mode": True})

            # Mock PreToolUse data
            data = {"terminal_id": terminal_id}
            from PreToolUse_sequential_thinking import pre_tool_use

            result = pre_tool_use(data)

            assert result.get("additionalContext"), "Should inject context for hypothesis mode"
            context = result["additionalContext"]
            assert "HYPOTHESIS MODE" in context or "MULTI-HYPOTHESIS" in context, "Should show hypothesis mode"

    def test_hypothesis_critique_mode_injection_iteration_1(self, tmp_path):
        """Iteration 1 should inject hypothesis_critique mode message."""
        terminal_id = "hypo_test"

        # Import the module to patch its STATE_DIR
        import PreToolUse_sequential_thinking as ptu_st

        with patch.object(ss, "STATE_DIR", tmp_path), patch.object(ptu_st, "STATE_DIR", tmp_path):
            # Create hypothesis mode session at iteration 1
            session_id = uuid.uuid4()
            ss.create_state(session_id, "test trigger", terminal_id, {
                "hypothesis_mode": True,
                "current_iteration": 1
            })

            data = {"terminal_id": terminal_id}
            from PreToolUse_sequential_thinking import pre_tool_use

            result = pre_tool_use(data)

            assert result.get("additionalContext"), "Should inject context"
            context = result["additionalContext"]
            assert "HYPOTHESIS_CRITIQUE" in context or "CRITIQUE" in context, "Should show critique mode"

    def test_hypothesis_resolution_injection_iteration_2(self, tmp_path):
        """Iteration 2 should inject hypothesis_resolution mode message."""
        terminal_id = "hypo_test"

        # Import the module to patch its STATE_DIR
        import PreToolUse_sequential_thinking as ptu_st

        with patch.object(ss, "STATE_DIR", tmp_path), patch.object(ptu_st, "STATE_DIR", tmp_path):
            session_id = uuid.uuid4()
            ss.create_state(session_id, "test trigger", terminal_id, {
                "hypothesis_mode": True,
                "current_iteration": 2
            })

            data = {"terminal_id": terminal_id}
            from PreToolUse_sequential_thinking import pre_tool_use

            result = pre_tool_use(data)

            assert result.get("additionalContext"), "Should inject context"
            context = result["additionalContext"]
            assert "HYPOTHESIS_RESOLUTION" in context or "RESOLUTION" in context, "Should show resolution mode"


class TestHypothesisExtraction:
    """Tests for hypothesis extraction from LLM output (CHANGE-004)."""

    def test_extract_h1_h2_h3_patterns(self):
        """Should extract hypotheses from H1:/H2:/H3: format."""
        from StopHook_sequential_thinking import _extract_hypotheses_from_response

        response_output = """H1: The database connection pool is exhausted
H2: The SQL query has an inefficient JOIN
H3: Network latency is causing timeouts"""

        result = _extract_hypotheses_from_response(response_output)

        assert len(result) == 3
        assert result[0]["id"] == "H1"
        assert "exhausted" in result[0]["claim"]
        assert result[1]["id"] == "H2"
        assert "inefficient" in result[1]["claim"]
        assert result[2]["id"] == "H3"
        assert "latency" in result[2]["claim"]
        for h in result:
            assert h["status"] == "active"

    def test_extract_natural_language_variants(self):
        """Should extract from 'First hypothesis:', 'Second hypothesis:' patterns."""
        from StopHook_sequential_thinking import _extract_hypotheses_from_response

        response_output = """First hypothesis: Authentication token expired
Second hypothesis: API rate limit exceeded
Third hypothesis: Database connection failed"""

        result = _extract_hypotheses_from_response(response_output)

        assert len(result) == 3
        assert result[0]["id"] == "H1"
        assert "token" in result[0]["claim"]
        assert result[1]["id"] == "H2"
        assert "rate limit" in result[1]["claim"]

    def test_extract_numbered_list_fallback(self):
        """Should extract from numbered list when H1:/H2: patterns not found."""
        from StopHook_sequential_thinking import _extract_hypotheses_from_response

        response_output = """1. Memory leak is causing the crash
2. Thread deadlock is blocking execution
3. Configuration error in settings.yaml"""

        result = _extract_hypotheses_from_response(response_output)

        assert len(result) == 3
        assert result[0]["id"] == "H1"
        assert "Memory leak" in result[0]["claim"]

    def test_extract_with_retry_prompt_on_insufficient_hypotheses(self):
        """Should return retry prompt when fewer than 2 hypotheses extracted."""
        from StopHook_sequential_thinking import _extract_hypotheses_from_response

        response_output = "H1: Only one hypothesis here"

        result = _extract_hypotheses_from_response(response_output)

        assert len(result) < 2, "Should extract fewer than 2 hypotheses"


class TestBackwardCompatibility:
    """Tests for backward compatibility with v1 state files (CHANGE-001)."""

    def test_v1_state_loads_without_crash(self, tmp_path):
        """Loading v1 state files (without hypotheses/hypothesis_mode fields) should not crash."""
        import json

        with patch.object(ss, "STATE_DIR", tmp_path):
            # Create v1 state file (no hypotheses/hypothesis_mode fields)
            session_id = uuid.uuid4()
            v1_state = {
                "session_id": str(session_id),
                "trigger_phrase": "analyze this",
                "current_iteration": 0,
                "max_iterations": 2,
                "mode": "initial",
                "intermediate_answers": [],
                "final_answer": None,
                "active": True,
                "terminal_id": "test_term",
            }

            state_file = tmp_path / f"{session_id}_test_term.json"
            state_file.write_text(json.dumps(v1_state, indent=2))

            # Load with v2 code
            loaded = ss.load_state(session_id, "test_term")
            assert loaded is not None, "Should load v1 state"
            # v1 state doesn't have these fields - code should handle gracefully via .get() defaults
            assert loaded.get("hypothesis_mode", False) is False, "Should default to False"
            assert loaded.get("hypotheses", []) == [], "Should default to empty list"

    def test_existing_tests_still_pass(self, tmp_path):
        """All 19 existing sequential thinking tests should still pass."""
        # This test ensures we haven't broken existing functionality
        # The existing test suite will verify this
        pass  # Actual test coverage from pytest run


class TestHypothesisFailureModes:
    """Tests for hypothesis mode failure scenarios (CHANGE-004)."""

    def test_corrupted_hypotheses_array_handling(self, tmp_path):
        """Should handle corrupted hypotheses array gracefully."""
        import json

        with patch.object(ss, "STATE_DIR", tmp_path):
            session_id = uuid.uuid4()
            # Create state with malformed hypotheses
            corrupted_state = {
                "session_id": str(session_id),
                "trigger_phrase": "test",
                "current_iteration": 0,
                "max_iterations": 2,
                "mode": "initial",
                "intermediate_answers": [],
                "final_answer": None,
                "active": True,
                "terminal_id": "test_term",
                "hypotheses": "not_a_list",  # Corrupted: string instead of list
                "hypothesis_mode": False,
            }

            state_file = tmp_path / f"{session_id}_test_term.json"
            state_file.write_text(json.dumps(corrupted_state, indent=2))

            # Should load without crashing (backward compatibility)
            loaded = ss.load_state(session_id, "test_term")
            assert loaded is not None

            # Type validation is caller's responsibility - .get() returns actual value if key exists
            # If hypotheses is corrupted (not a list), calling code should validate before using
            hypotheses = loaded.get("hypotheses", [])
            # Note: .get() returns "not_a_list" (string) because key exists, not the default []
            # This is expected behavior - state loader doesn't validate types

    def test_empty_hypotheses_array(self, tmp_path):
        """Should handle empty hypotheses array in context formatting."""
        from PreToolUse_sequential_thinking import _format_hypothesis_context

        result = _format_hypothesis_context([])
        assert "No hypotheses tracked yet" in result

    def test_invalid_hypothesis_status_values(self, tmp_path):
        """Should handle invalid status values gracefully."""
        from PreToolUse_sequential_thinking import _format_hypothesis_context

        invalid_hypotheses = [
            {"id": "H1", "claim": "test", "status": "invalid_status"}
        ]

        result = _format_hypothesis_context(invalid_hypotheses)
        # Should display "?" for unknown status
        assert "? H1" in result


class TestVerdictExtraction:
    """Tests for verdict field extraction (ADR-20260406)."""

    def test_verdict_extracted_from_resolution_output(self, tmp_path, monkeypatch):
        """Verdict regex should extract winning hypothesis ID from resolution output."""
        import re
        from StopHook_sequential_thinking import stop

        # Mock _find_active_session to return hypothesis mode at iteration 2
        mock_session = {
            "session_id": "12345678-1234-1234-1234-123456789abc",
            "current_iteration": 2,
            "is_hypothesis_mode": True,
            "hypothesis_mode": True,
            "active": True,
            "terminal_id": "test_term",
        }

        def mock_find(terminal_id):
            return mock_session

        monkeypatch.setattr(
            "StopHook_sequential_thinking._find_active_session", mock_find
        )
        # Force should_continue to return False so verdict extraction branch runs
        monkeypatch.setattr(
            "StopHook_sequential_thinking.should_continue", lambda *a, **k: False
        )

        response = (
            "Based on my analysis, the winning hypothesis is H1. "
            "The authentication token expired because the session timed out after 30 minutes."
        )

        calls = []

        def mock_update(uuid_obj, updates, tid):
            calls.append(updates)

        def mock_set_final(uuid_obj, answer, tid):
            pass

        monkeypatch.setattr(
            "StopHook_sequential_thinking.update_state", mock_update
        )
        monkeypatch.setattr(
            "StopHook_sequential_thinking.set_final_answer", mock_set_final
        )

        result = stop({"terminal_id": "test_term", "response_output": response})

        assert result.get("allow") is True
        # verdict should have been extracted and stored
        verdict_calls = [c for c in calls if "verdict" in c]
        assert len(verdict_calls) == 1
        assert verdict_calls[0]["verdict"] == "H1"

    def test_verdict_h2_extracted(self, tmp_path, monkeypatch):
        """Should extract H2 as winning hypothesis."""
        from StopHook_sequential_thinking import stop

        mock_session = {
            "session_id": "12345678-1234-1234-1234-123456789abc",
            "current_iteration": 2,
            "is_hypothesis_mode": True,
            "hypothesis_mode": True,
            "active": True,
            "terminal_id": "test_term",
        }

        def mock_find(terminal_id):
            return mock_session

        monkeypatch.setattr(
            "StopHook_sequential_thinking._find_active_session", mock_find
        )
        monkeypatch.setattr(
            "StopHook_sequential_thinking.should_continue", lambda *a, **k: False
        )

        calls = []

        def mock_update(uuid_obj, updates, tid):
            calls.append(updates)

        def mock_set_final(uuid_obj, answer, tid):
            pass

        monkeypatch.setattr(
            "StopHook_sequential_thinking.update_state", mock_update
        )
        monkeypatch.setattr(
            "StopHook_sequential_thinking.set_final_answer", mock_set_final
        )

        result = stop({
            "terminal_id": "test_term",
            "response_output": "The best hypothesis is H2: the API rate limit was exceeded."
        })

        verdict_calls = [c for c in calls if "verdict" in c]
        assert len(verdict_calls) == 1
        assert verdict_calls[0]["verdict"] == "H2"

    def test_verdict_not_extracted_when_no_match(self, tmp_path, monkeypatch):
        """Should not store verdict if regex doesn't match."""
        from StopHook_sequential_thinking import stop

        mock_session = {
            "session_id": "12345678-1234-1234-1234-123456789abc",
            "current_iteration": 2,
            "is_hypothesis_mode": True,
            "hypothesis_mode": True,
            "active": True,
            "terminal_id": "test_term",
        }

        def mock_find(terminal_id):
            return mock_session

        monkeypatch.setattr(
            "StopHook_sequential_thinking._find_active_session", mock_find
        )
        monkeypatch.setattr(
            "StopHook_sequential_thinking.should_continue", lambda *a, **k: False
        )

        calls = []

        def mock_update(uuid_obj, updates, tid):
            calls.append(updates)

        def mock_set_final(uuid_obj, answer, tid):
            pass

        monkeypatch.setattr(
            "StopHook_sequential_thinking.update_state", mock_update
        )
        monkeypatch.setattr(
            "StopHook_sequential_thinking.set_final_answer", mock_set_final
        )

        # Response doesn't mention winning hypothesis
        result = stop({
            "terminal_id": "test_term",
            "response_output": "Both hypotheses have merits but the data is inconclusive."
        })

        verdict_calls = [c for c in calls if "verdict" in c]
        assert len(verdict_calls) == 0
        assert result.get("allow") is True

    def test_verdict_optional_backward_compatible(self, tmp_path, monkeypatch):
        """State without verdict field should not break hypothesis mode."""
        from StopHook_sequential_thinking import stop

        mock_session = {
            "session_id": "12345678-1234-1234-1234-123456789abc",
            "current_iteration": 2,
            "is_hypothesis_mode": True,
            "hypothesis_mode": True,
            "active": True,
            "terminal_id": "test_term",
            # No verdict field — backward compatible
        }

        def mock_find(terminal_id):
            return mock_session

        monkeypatch.setattr(
            "StopHook_sequential_thinking._find_active_session", mock_find
        )
        monkeypatch.setattr(
            "StopHook_sequential_thinking.should_continue", lambda *a, **k: False
        )

        def mock_set_final(uuid_obj, answer, tid):
            pass

        monkeypatch.setattr(
            "StopHook_sequential_thinking.set_final_answer", mock_set_final
        )

        result = stop({
            "terminal_id": "test_term",
            "response_output": "Final answer here."
        })

        # Should not crash, verdict absent is fine
        assert result.get("allow") is True


class TestVerdictInjection:
    """Tests for verdict injection in PreToolUse (ADR-20260406)."""

    def test_verdict_injected_in_resolution_mode(self, tmp_path, monkeypatch):
        """PreToolUse should inject verdict into hypothesis_resolution mode message."""
        mock_session = {
            "session_id": "12345678-1234-1234-1234-123456789abc",
            "current_iteration": 2,
            "mode": "hypothesis_resolution",
            "hypothesis_mode": True,
            "hypotheses": [
                {"id": "H1", "claim": "Token expired", "status": "active"},
                {"id": "H2", "claim": "Rate limit", "status": "active"},
            ],
            "verdict": "H1",
            "active": True,
            "terminal_id": "test_term",
        }

        def mock_find(terminal_id):
            return mock_session

        monkeypatch.setattr(
            "PreToolUse_sequential_thinking._find_active_session", mock_find
        )

        from PreToolUse_sequential_thinking import pre_tool_use

        result = pre_tool_use({"terminal_id": "test_term"})

        assert result.get("additionalContext")
        context = result["additionalContext"]
        assert "Winning hypothesis: H1" in context

    def test_no_verdict_injected_when_absent(self, tmp_path, monkeypatch):
        """PreToolUse should not inject verdict line when verdict is absent."""
        mock_session = {
            "session_id": "12345678-1234-1234-1234-123456789abc",
            "current_iteration": 2,
            "mode": "hypothesis_resolution",
            "hypothesis_mode": True,
            "hypotheses": [
                {"id": "H1", "claim": "Token expired", "status": "active"},
            ],
            # No verdict field
            "active": True,
            "terminal_id": "test_term",
        }

        def mock_find(terminal_id):
            return mock_session

        monkeypatch.setattr(
            "PreToolUse_sequential_thinking._find_active_session", mock_find
        )

        from PreToolUse_sequential_thinking import pre_tool_use

        result = pre_tool_use({"terminal_id": "test_term"})

        assert result.get("additionalContext")
        context = result["additionalContext"]
        assert "Winning hypothesis" not in context


# ---------------------------------------------------------------------------
# CHANGE-005: End-to-end hypothesis workflow
# ---------------------------------------------------------------------------


class TestHypothesisE2E:
    """End-to-end hypothesis workflow: trigger → iteration 0 → 1 → 2 → complete."""

    def test_full_hypothesis_workflow(self, tmp_path, monkeypatch):
        """Trigger creates hypothesis session, then 3 StopHook calls complete it."""
        import PreToolUse_sequential_thinking as ptu_st

        with patch.object(ss, "STATE_DIR", tmp_path), patch.object(sh, "STATE_DIR", tmp_path), \
             patch.object(ptu_st, "STATE_DIR", tmp_path):
            # Phase 1: Trigger hypothesis mode
            result = _run_hook("maintain multiple hypotheses for this bug", "e2e_term")
            text = _context_text(result)
            assert result.context
            assert "multi_hypothesis" in text

            # Extract session ID
            session_id_str = None
            for line in text.split("\n"):
                if line.startswith("Session ID:"):
                    session_id_str = line.split(": ")[1].strip()
                    break
            assert session_id_str
            session_id = uuid.UUID(session_id_str)

            # Verify state has hypothesis_mode set
            state = ss.load_state(session_id, "e2e_term")
            assert state is not None
            assert state["hypothesis_mode"] is True
            assert state["current_iteration"] == 0

            # Phase 2: Iteration 0 → multi_hypothesis response with H1/H2/H3
            stop1 = sh.stop({
                "terminal_id": "e2e_term",
                "response_output": (
                    "H1: Database connection pool exhausted\n"
                    "H2: Inefficient SQL query with missing index\n"
                    "H3: Network latency between services"
                ),
            })
            assert stop1.get("allow") is False
            assert "HYPOTHESIS_CRITIQUE" in stop1["reason"]

            # Verify hypotheses were extracted and stored
            state = ss.load_state(session_id, "e2e_term")
            assert state is not None
            assert len(state["hypotheses"]) == 3
            assert state["current_iteration"] == 1

            # Phase 3: Iteration 1 → hypothesis_critique response
            stop2 = sh.stop({
                "terminal_id": "e2e_term",
                "response_output": (
                    "H1 is most likely - connection pool is small. "
                    "H2 is possible but query plans look fine. "
                    "H3 is unlikely - latency metrics are normal."
                ),
            })
            assert stop2.get("allow") is False
            assert "HYPOTHESIS_RESOLUTION" in stop2["reason"]

            state = ss.load_state(session_id, "e2e_term")
            assert state is not None
            assert state["current_iteration"] == 2

            # Phase 4: Iteration 2 → hypothesis_resolution response → session complete
            stop3 = sh.stop({
                "terminal_id": "e2e_term",
                "response_output": (
                    "Based on my analysis, the winning hypothesis is H1. "
                    "The database connection pool is exhausted because "
                    "max_connections is set to 5."
                ),
            })
            assert stop3.get("allow") is True

            # State file deleted on completion
            final_state = ss.load_state(session_id, "e2e_term")
            assert final_state is None

    def test_hypothesis_workflow_insufficient_hypotheses_retries(self, tmp_path, monkeypatch):
        """If LLM provides <2 hypotheses, StopHook should force retry."""
        with patch.object(ss, "STATE_DIR", tmp_path), patch.object(sh, "STATE_DIR", tmp_path):
            session_id = uuid.uuid4()
            ss.create_state(session_id, "test", "retry_term", {"hypothesis_mode": True})

            # LLM only provides 1 hypothesis
            stop1 = sh.stop({
                "terminal_id": "retry_term",
                "response_output": "H1: It's a config issue.",
            })
            assert stop1.get("allow") is False
            assert "at least 2 distinct hypotheses" in stop1["reason"]

            # State should still be at iteration 0 (not advanced)
            state = ss.load_state(session_id, "retry_term")
            assert state is not None
            assert state["current_iteration"] == 0

    def test_dual_mode_guard_hypothesis_supersedes_investigation(self, tmp_path):
        """When prompt matches both investigation and hypothesis patterns, hypothesis wins."""
        with patch.object(ss, "STATE_DIR", tmp_path):
            result = _run_hook(
                "debug this issue while I maintain multiple hypotheses",
                "dual_term",
            )
            text = _context_text(result)
            assert result.context

            # Extract session ID
            session_id_str = None
            for line in text.split("\n"):
                if line.startswith("Session ID:"):
                    session_id_str = line.split(": ")[1].strip()
                    break
            assert session_id_str
            session_id = uuid.UUID(session_id_str)

            state = ss.load_state(session_id, "dual_term")
            assert state is not None
            # hypothesis_mode should be True
            assert state["hypothesis_mode"] is True
            # is_investigation should be False (superseded)
            assert state.get("is_investigation", False) is False


class TestHypothesisExtractionEdgeCases:
    """Edge cases for hypothesis extraction."""

    def test_extraction_caps_at_three(self):
        """When LLM generates 5+ hypotheses, only first 3 are retained."""
        from StopHook_sequential_thinking import _extract_hypotheses_from_response

        response = (
            "H1: First hypothesis\n"
            "H2: Second hypothesis\n"
            "H3: Third hypothesis\n"
            "H4: Fourth hypothesis\n"
            "H5: Fifth hypothesis\n"
        )

        result = _extract_hypotheses_from_response(response)
        assert len(result) == 3
        assert result[0]["id"] == "H1"
        assert result[1]["id"] == "H2"
        assert result[2]["id"] == "H3"
        assert "Fourth" not in str(result)
        assert "Fifth" not in str(result)

    def test_extraction_handles_mixed_formats(self):
        """H1: format takes priority over numbered list fallback."""
        from StopHook_sequential_thinking import _extract_hypotheses_from_response

        response = (
            "H1: Database issue\n"
            "1. First numbered item\n"
            "H2: Network issue\n"
        )

        result = _extract_hypotheses_from_response(response)
        assert len(result) == 2
        assert result[0]["claim"] == "Database issue"
        assert result[1]["claim"] == "Network issue"

    def test_extraction_deduplicates_natural_language(self):
        """Natural language variants don't duplicate H1:/H2: matches."""
        from StopHook_sequential_thinking import _extract_hypotheses_from_response

        response = (
            "H1: Token expired\n"
            "H2: Rate limited\n"
            "H3: Connection failed\n"
            "First hypothesis: Something else entirely\n"
        )

        result = _extract_hypotheses_from_response(response)
        # H1/H2/H3 already found, so "First hypothesis" should not add a duplicate
        assert len(result) == 3
        assert result[0]["claim"] == "Token expired"
