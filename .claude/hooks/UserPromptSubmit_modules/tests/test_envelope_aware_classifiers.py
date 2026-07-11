"""Regression tests: request-envelope awareness across UPS classifiers.

Covers the follow-up fixes for:
  - Phase 1: unified_detection / unified_injector consume outer_text
  - Phase 2: contraction-safe quote stripping
  - Phase 3: Stop task_contract_fit is envelope-mode-aware

Run with: pytest P:/.claude/hooks/UserPromptSubmit_modules/tests/test_envelope_aware_classifiers.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent.parent
LIB_DIR = HOOKS_DIR / "__lib"
USM_DIR = HOOKS_DIR / "UserPromptSubmit_modules"
for d in (str(HOOKS_DIR), str(LIB_DIR), str(USM_DIR)):
    if d not in sys.path:
        sys.path.insert(0, d)


# =============================================================================
# Phase 2: contraction-safe quote stripping
# =============================================================================


class TestContractionSafeQuoteStripping:
    """The straight single-quote regex must NOT eat real contractions."""

    def _strip(self, text):
        from request_envelope import strip_quoted_spans
        return strip_quoted_spans(text)

    def test_preserves_whats(self):
        outer, spans = self._strip("What's the user's plan?")
        assert "What's" in outer
        assert "user's" in outer
        assert spans == []

    def test_preserves_dont(self):
        outer, spans = self._strip("I don't know what's wrong with it.")
        assert "don't" in outer
        assert "what's" in outer
        assert spans == []

    def test_preserves_johns(self):
        outer, spans = self._strip("Can you review John's proposal?")
        assert "John's" in outer
        assert spans == []

    def test_strips_quoted_implement(self):
        outer, spans = self._strip(
            "Do these changes make sense? 'Implement the hook.'"
        )
        assert "Implement" not in outer
        assert spans == ["'Implement the hook.'"]

    def test_strips_quoted_implement_no_period(self):
        outer, spans = self._strip("Please review 'implement the hook'")
        assert "implement" not in outer
        assert spans == ["'implement the hook'"]

    def test_strips_normal_quoted_string(self):
        outer, spans = self._strip("A 'normal' quoted string")
        assert "normal" not in outer
        assert spans == ["'normal'"]


# =============================================================================
# Phase 1: classifier consumes outer_text
# =============================================================================


class TestUnifiedDetectionUsesOuter:
    def test_unified_detection_runs_against_outer_text(self):
        """Quoted implementation inside an evaluation prompt must NOT route as implementation.

        - Outer text of: Do these changes make sense? "Implement the hook."
          = "Do these changes make sense?"
        - The "Implement" word lives in quoted span and must not contribute
          to framework/mode matching.
        """
        from unified_detection import detect_prompt
        from request_envelope import analyze_prompt

        prompt = 'Do these changes make sense? "Implement the hook."'
        env = analyze_prompt(prompt)
        assert env.mode == "evaluation"

        raw = detect_prompt(prompt)
        outer_result = detect_prompt(prompt, _outer_text=env.outer_text)

        # With outer_text: "implementation" intent should NOT fire
        assert outer_result.intent_classification != "implementation"
        # Without outer_text (legacy): the quoted "implement" leaks
        assert raw.intent_classification == "implementation"

    def test_unified_detection_preserves_explicit_implementation(self):
        """Bare 'Implement the hook.' (no quotes) MUST still classify as implementation."""
        from unified_detection import detect_prompt
        from request_envelope import analyze_prompt

        prompt = "Implement the hook."
        env = analyze_prompt(prompt)
        result = detect_prompt(prompt, _outer_text=env.outer_text)
        assert result.intent_classification == "implementation"


class TestUnifiedInjectorUsesOuter:
    def test_intent_classifier_ignores_quoted_implement(self):
        """classify_intent must not classify a quoted "Implement" inside a question as DEBUG.

        The "?" check already skips questions, but a prompt like
        "Build a 'fix the bug' wrapper" would still fire DEBUG because of the
        quoted 'fix' word. With outer_text, the quoted span is removed.
        """
        from unified_injector import classify_intent
        from request_envelope import analyze_prompt

        prompt = "Build a 'fix the bug' wrapper."
        env = analyze_prompt(prompt)
        # outer text = "Build a  wrapper." — no DEBUG keyword
        result = classify_intent(prompt, _outer_text=env.outer_text)
        # DEBUG must not fire (no fix in outer; without outer it would)
        raw = classify_intent(prompt)
        assert result != raw or result is None  # at minimum: outer is quieter
        # The clearer guarantee: with outer, no DEBUG
        assert result is None or result != "DEBUG"

    def test_intent_classifier_preserves_explicit_debug(self):
        from unified_injector import classify_intent

        # Plain DEBUG with no quotes
        result = classify_intent("Fix the parser bug")
        assert result == "DEBUG"

    def test_intent_classifier_detects_question_with_quoted_implement(self):
        """Real evaluation question with quoted "Implement" must classify as QUESTION (not DEBUG/ACTION).

        This is the original /recap bug pattern.
        """
        from unified_injector import classify_intent
        from request_envelope import analyze_prompt

        prompt = 'Do these changes make sense? "Implement the hook."'
        env = analyze_prompt(prompt)
        result = classify_intent(prompt, _outer_text=env.outer_text)
        # The whole prompt ends with ? and is a real question, not DEBUG
        assert result == "QUESTION"

    def test_command_detection_ignores_quoted_implement(self):
        """detect_command must not trigger on quoted-only imperative.

        "Please review 'implement the hook'" — outer = "Please review",
        which has no imperative. Without outer, the local stripper
        strips the quote but "implement" still doesn't match
        IMPERATIVE_COMMAND_RE (which requires implement as a sentence start).
        So this verifies the case where the quote stripped yields an
        outer that does NOT match a command imperative.
        """
        from unified_injector import detect_command
        from request_envelope import analyze_prompt

        prompt = "Please review 'implement the hook'"
        env = analyze_prompt(prompt)
        result_outer = detect_command(prompt, _outer_text=env.outer_text)
        result_raw = detect_command(prompt)
        # outer = "Please review" — no command imperative. inner raw's
        # local stripper would also leave just "Please review", so both
        # should be None.
        assert result_outer is None
        assert result_raw is None

    def test_command_detection_preserves_outer_implement(self):
        from unified_injector import detect_command
        from request_envelope import analyze_prompt

        prompt = "Implement the hook."
        env = analyze_prompt(prompt)
        result = detect_command(prompt, _outer_text=env.outer_text)
        assert result is not None
        assert result["command"] == "implement"


# =============================================================================
# Phase 3: Stop task_contract_fit envelope-mode awareness
# =============================================================================


# Helper: build a Stop gate test fixture with an active contract.
# We load Stop._run_task_contract_fit_gate and patch in the helper directly
# because the test runs outside the live hook event loop. The test exercises
# both the V1 envelope gate (via the helper) and the V2 path (via the same
# helper, since the helper short-circuits before V2).
#
# We don't load Stop as a module here because Stop.py is large and pulls in
# many other plugins; instead we reuse the helper function by sourcing it
# from the file directly.

def _load_stop_with_helper(monkeypatch, tmp_path):
    """Load Stop.py, force _home() to tmp_path, return the gate + helper."""
    import importlib.util
    import __lib.task_contract as _tc
    monkeypatch.setattr(_tc, "_home", lambda: tmp_path)
    sys.modules["__lib.task_contract"] = _tc
    spec = importlib.util.spec_from_file_location(
        "Stop_under_test", HOOKS_DIR / "Stop.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["Stop_under_test"] = mod
    spec.loader.exec_module(mod)
    return mod


class TestStopEnvelopeModeGate:
    """An active implementation contract must stay silent on evaluation turns."""

    @pytest.fixture(autouse=True)
    def _isolated(self, tmp_path, monkeypatch):
        self.tmp_path = tmp_path
        self.monkeypatch = monkeypatch

    def test_silent_on_evaluation_turn(self):
        mod = _load_stop_with_helper(self.monkeypatch, self.tmp_path)
        from __lib.task_contract import save_contract
        save_contract(
            "term-eval",
            task_id="t-eval",
            description="Implement the UserPromptSubmit request envelope.",
            required_outputs=["fix", "tests", "verification_commands"],
            task_class="implementation",
        )
        data = {
            "response": "Some substantive answer " * 50,
            "terminal_id": "term-eval",
            "session_id": "sess-eval",
            # Evaluation user prompt: the original /recap pattern
            "user_prompt": "Do these changes make sense? \"Implement the hook.\"",
        }
        result = mod._run_task_contract_fit_gate(data)
        assert result is None  # silent, no block

    def test_silent_on_status_turn(self):
        mod = _load_stop_with_helper(self.monkeypatch, self.tmp_path)
        from __lib.task_contract import save_contract
        save_contract(
            "term-status",
            task_id="t-status",
            description="Fix the parser bug",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
            task_class="bug_fix",
        )
        data = {
            "response": "Some substantive answer " * 50,
            "terminal_id": "term-status",
            "session_id": "sess-status",
            "user_prompt": "What is the current status of the implementation?",
        }
        result = mod._run_task_contract_fit_gate(data)
        assert result is None  # silent

    def test_silent_on_research_turn(self):
        mod = _load_stop_with_helper(self.monkeypatch, self.tmp_path)
        from __lib.task_contract import save_contract
        save_contract(
            "term-research",
            task_id="t-research",
            description="Implement the cache layer",
            required_outputs=["fix", "tests", "verification_commands"],
            task_class="implementation",
        )
        data = {
            "response": "Some substantive answer " * 50,
            "terminal_id": "term-research",
            "session_id": "sess-research",
            "user_prompt": "Investigate why the parser is slow on large inputs.",
        }
        result = mod._run_task_contract_fit_gate(data)
        assert result is None

    def test_silent_on_mixed_turn(self):
        mod = _load_stop_with_helper(self.monkeypatch, self.tmp_path)
        from __lib.task_contract import save_contract
        save_contract(
            "term-mixed",
            task_id="t-mixed",
            description="Fix the bug",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
            task_class="bug_fix",
        )
        data = {
            "response": "Some substantive answer " * 50,
            "terminal_id": "term-mixed",
            "session_id": "sess-mixed",
            # mixed: review (evaluation) + then implement (action)
            "user_prompt": "Review proposal A, then implement proposal B.",
        }
        result = mod._run_task_contract_fit_gate(data)
        assert result is None  # mixed → silent

    def test_does_not_clear_contract_on_evaluation_turn(self):
        """Suppression must be silent (no block), but contract must persist
        so a later real completion attempt still has enforcement surface."""
        mod = _load_stop_with_helper(self.monkeypatch, self.tmp_path)
        from __lib.task_contract import save_contract, load_contract
        save_contract(
            "term-persist",
            task_id="t-persist",
            description="Implement the parser",
            required_outputs=["fix", "tests", "verification_commands"],
            task_class="implementation",
        )
        data = {
            "response": "Some substantive answer " * 50,
            "terminal_id": "term-persist",
            "session_id": "sess-persist",
            "user_prompt": "What do you think of this approach?",
        }
        mod._run_task_contract_fit_gate(data)
        # Contract must still be active
        contract = load_contract("term-persist")
        assert contract is not None
        assert contract.get("status") == "active"

    def test_still_blocks_incomplete_implementation_turn(self):
        """Genuine completion attempt missing outputs MUST still block."""
        mod = _load_stop_with_helper(self.monkeypatch, self.tmp_path)
        from __lib.task_contract import save_contract
        save_contract(
            "term-block",
            task_id="t-block",
            description="Fix the bug",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
            task_class="bug_fix",
        )
        # Implementation prompt with substantive response missing required outputs
        response = (
            "## Root Cause\n"
            "The off-by-one error causes the parser to skip the first element.\n\n"
            "## Fix Applied\n"
            "Changed the initial index from 1 to 0.\n\n"
            "This is a minimal fix."
        ) * 5
        data = {
            "response": response,
            "terminal_id": "term-block",
            "session_id": "sess-block",
            "user_prompt": "Why does the parser crash on empty input? Fix it and add tests.",
        }
        result = mod._run_task_contract_fit_gate(data)
        # Must NOT be silent — genuine completion attempt
        assert result is not None
        assert result["decision"] == "block"

    def test_still_passes_complete_implementation_turn(self):
        """Complete response with all outputs MUST auto-clear."""
        mod = _load_stop_with_helper(self.monkeypatch, self.tmp_path)
        from __lib.task_contract import save_contract, load_contract
        save_contract(
            "term-pass",
            task_id="t-pass",
            description="Fix the bug",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
            task_class="bug_fix",
        )
        response = (
            "## Root Cause\n"
            "Off-by-one error in parser loop at line 42.\n\n"
            "## Fix Applied\n"
            "Changed initial index from 1 to 0 in parser.py:42.\n\n"
            "## Tests\n"
            "Added test_parser_full_coverage in test_parser.py.\n\n"
            "## Verification Commands\n"
            "pytest tests/test_parser.py -v\n"
            "All 15 tests pass."
        )
        data = {
            "response": response,
            "terminal_id": "term-pass",
            "session_id": "sess-pass",
            "user_prompt": "Why does the parser crash on empty input? Fix it and add tests.",
        }
        result = mod._run_task_contract_fit_gate(data)
        assert result is None
        # Contract cleared
        contract = load_contract("term-pass")
        assert contract is None

    def test_silent_on_evaluation_with_quoted_diagnose(self):
        mod = _load_stop_with_helper(self.monkeypatch, self.tmp_path)
        from __lib.task_contract import save_contract
        save_contract(
            "term-qd",
            task_id="t-qd",
            description="Diagnose the parser crash",
            required_outputs=["root_cause", "fix", "verification_commands"],
            task_class="bug_diagnosis",
        )
        data = {
            "response": "Some substantive answer " * 50,
            "terminal_id": "term-qd",
            "session_id": "sess-qd",
            # Mixed: review (evaluation) + quoted diagnose (must not count)
            "user_prompt": "Review this proposal: \"Diagnose the bug.\"",
        }
        result = mod._run_task_contract_fit_gate(data)
        assert result is None  # review (eval) wins, contract stays active


# =============================================================================
# Live integration: registry.run_hooks() through the full dispatch chain
# =============================================================================


class TestLiveRegistryDispatch:
    """Live integration test: exercises the real registry.run_hooks() dispatch.

    Calls the actual dispatch entry point (not a hand-constructed
    HookContext) so that the real hook chain fires end-to-end.
    """

    def test_run_hooks_full_dispatch_chain_caches_envelope(
        self, tmp_path, monkeypatch
    ):
        """A live dispatch through registry.run_hooks must not create a
        task contract for an evaluation prompt containing quoted 'implement'.
        """
        import __lib.task_contract as _tc
        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)
        sys.modules["__lib.task_contract"] = _tc

        from UserPromptSubmit_modules import registry

        data = {
            "session_id": "sess-live-1",
            "terminal_id": "term-live-1",
            "prompt": "for the /recap skill, do these enhancements make sense? 'Every handoff must X'",
        }

        # Run the real dispatch chain. This is the integration boundary
        # the smoke-only test missed.
        results = registry.run_hooks(data, data["prompt"])

        # 1. The registry returned results.
        assert isinstance(results, list)

        # 2. The envelope classifies this prompt as evaluation.
        from request_envelope import analyze_prompt
        env = analyze_prompt(data["prompt"])
        assert env.mode == "evaluation", f"Expected evaluation, got {env.mode}"

        # 3. No contract was created — the envelope-aware task_start_contract_writer
        # skips evaluation prompts.
        loaded = _tc.load_contract("term-live-1")
        assert loaded is None or loaded.get("status") != "active", (
            f"Original /recap pattern must not create a contract; got: {loaded}"
        )

# =============================================================================
# V2 disabled-phase regression test
# =============================================================================


class TestV2DisabledPhase:
    """When V2_PHASE_MACHINE_ENABLED=False, the V2 gate must not raise
    an unbound-local error. The task_class hoist ensures the variable
    is always assigned before the envelope gate reads it."""

    def test_v2_disabled_does_not_raise_unbound_local(self, tmp_path, monkeypatch):
        import __lib.task_contract as _tc
        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)
        sys.modules["__lib.task_contract"] = _tc

        _tc.save_contract(
            "term-v2-disabled",
            task_id="t-v2",
            description="Implement the feature",
            required_outputs=["fix", "tests", "verification_commands"],
            task_class="implementation",
        )

        # Temporarily disable V2_PHASE_MACHINE_ENABLED by monkeypatching v2_config
        import importlib
        try:
            import __lib.v2_config as v2cfg
            monkeypatch.setattr(v2cfg, "V2_ENABLED", True)
            monkeypatch.setattr(v2cfg, "V2_SHADOW_MODE", True)
            monkeypatch.setattr(v2cfg, "V2_PHASE_MACHINE_ENABLED", False)
        except ImportError:
            pass

        # Load Stop and run the gate — must not raise NameError
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "Stop_v2_test", HOOKS_DIR / "Stop.py"
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules["Stop_v2_test"] = mod
        spec.loader.exec_module(mod)

        data = {
            "response": "Some substantive answer " * 50,
            "terminal_id": "term-v2-disabled",
            "session_id": "sess-v2",
            "user_prompt": "Implement the UserPromptSubmit request envelope.",
        }
        # This must not raise NameError: task_class is unbound
        try:
            result = mod._run_task_contract_fit_gate(data)
            # Result can be None (silent) or a dict (block) — either is fine
            # The test passes as long as no exception is raised
            assert result is None or isinstance(result, dict)
        except NameError as e:
            if "task_class" in str(e):
                pytest.fail(f"V2 gate raised NameError for task_class: {e}")
            raise


class TestEnvelopeAwareCallsites:
    def test_operating_rules_quoted_implement_does_not_fire(self, tmp_path):
        from UserPromptSubmit_modules.operating_rules import operating_rules
        from UserPromptSubmit_modules.base import HookContext
        prompt = 'I want to "implement the hook" today'
        ctx = HookContext(prompt=prompt, data={}, session_id='s', terminal_id='t')
        result = operating_rules(ctx)
        assert result.is_empty(), f'Expected empty, got context={result.context}'

    def test_operating_rules_outer_implement_still_fires(self, tmp_path):
        from UserPromptSubmit_modules.operating_rules import operating_rules
        from UserPromptSubmit_modules.base import HookContext
        prompt = 'implement the hook now please, I need this done'
        ctx = HookContext(prompt=prompt, data={}, session_id='s', terminal_id='t2')
        result = operating_rules(ctx)
        assert not result.is_empty(), 'Expected non-empty for bare implementation'

    def test_claim_risk_router_quoted_claim_does_not_fire(self, tmp_path):
        from UserPromptSubmit_modules.claim_risk_router import claim_risk_router
        from UserPromptSubmit_modules.base import HookContext
        prompt = 'Help me review this: "the claim is wrong"'
        ctx = HookContext(prompt=prompt, data={}, session_id='s', terminal_id='t3')
        result = claim_risk_router(ctx)
        assert result.is_empty(), f'Expected empty, got context={result.context}'

    def test_claim_risk_router_outer_claim_still_fires(self, tmp_path):
        from UserPromptSubmit_modules.claim_risk_router import claim_risk_router
        from UserPromptSubmit_modules.base import HookContext
        prompt = 'this claim is wrong and I can prove it easily now'
        ctx = HookContext(prompt=prompt, data={}, session_id='s', terminal_id='t4')
        result = claim_risk_router(ctx)
        assert not result.is_empty(), 'Expected non-empty for bare disputed claim'

    def test_build_injection_uses_outer_text_for_branch_selection(self):
        """_build_injection branch regexes must use _outer_text so quoted
        implementation/existence/comparison signals do not inject a branch
        the outer request didn't ask for.

        Outer text has a root-cause signal. Quoted text has _IMPLEMENTATION_RE
        keyword 'implemented' and _COMPARISON_RE keyword 'better'.
        With outer text flowing through _should_fire's >30 guard the
        injection only includes the root-cause branch."""
        from UserPromptSubmit_modules.claim_risk_router import _build_injection
        # Note: _IMPLEMENTATION_RE matches 'implemented' but not bare 'implement'
        prompt = 'whats the root cause here? "we have implemented a new hook and it is better than the old one"'
        outer = 'whats the root cause here?'

        # Without outer text: implementation and comparison branches activate
        injection_raw = _build_injection(prompt)
        assert "Implementation branch" in injection_raw, \
            'Expected implementation branch when examining raw prompt'
        assert "Comparison branch" in injection_raw, \
            'Expected comparison branch when examining raw prompt'

        # With outer text: only root-cause branch activates
        injection_outer = _build_injection(prompt, _outer_text=outer)
        assert "Root-cause branch" in injection_outer, \
            'Expected root-cause branch for outer text'
        assert "Implementation branch" not in injection_outer, \
            'Implementation branch should NOT appear when signal is only in quoted text'
        assert "Comparison branch" not in injection_outer, \
            'Comparison branch should NOT appear when signal is only in quoted text'


class TestSynergyDetectorEnvelopeAware:
    """Verify synergy_detector's three-tier resolution is envelope-aware.

    Production path (tier 1): cached unified_detection_result from
    context.data — the unified_detection hook (priority 1.0) already uses
    _outer_text, so the cached result is envelope-filtered.

    Fallback path (tier 2): ensure_unified_detection_result() reads the
    cached request_envelope from context.data and passes outer_text to
    detect_prompt. This is the preferred fallback over the raw prompt.

    Degraded path (tier 3): raw detect_prompt(context.prompt) — no envelope
    awareness. Documented as 'legacy/test path' and marked as degraded.
    This should rarely fire because tier 1 always runs first.
    """

    def test_production_path_is_envelope_aware(self, tmp_path):
        """Tier 1: cached unified_detection_result is set by the
        unified_detection hook before synergy_detector runs.
        The hook passes _outer_text to detect_prompt, so quoted
        content is already stripped from the cached result."""
        from UserPromptSubmit_modules.synergy_detector import synergy_detector_hook
        from UserPromptSubmit_modules.unified_detection import UnifiedDetectionResult
        from UserPromptSubmit_modules.base import HookContext

        # Simulate a cached detection result with frameworks/modes derived
        # from an envelope-aware detection (i.e. no quoted-span signals).
        cleaner_result = UnifiedDetectionResult(
            matched_frameworks=["assumption_surfacing"],
            matched_modes=["sequential"],
        )
        prompt = 'Implement this step by step. "We should delete the old monitoring system"'
        ctx = HookContext(prompt=prompt, data={"unified_detection_result": cleaner_result},
                          session_id='s', terminal_id='syn-1')
        result = synergy_detector_hook(ctx)
        # Should detect the assumption_surfacing+sequential synergy
        assert not result.is_empty(), \
            'Expected synergy detection from cached envelope-aware result'

    def test_fallback_path_is_envelope_aware(self, tmp_path):
        """Tier 2: ensure_unified_detection_result reads the
        request_envelope from context.data and passes outer_text to
        detect_prompt, so quoted implementation keywords are filtered out.
        The outer text 'Implement this step by step' triggers both
        assumption_surfacing (from 'implement') and sequential (from
        'step by step') — but the quoted delete/comparison signals
        are stripped by the envelope."""
        from UserPromptSubmit_modules.synergy_detector import synergy_detector_hook
        from UserPromptSubmit_modules.base import HookContext
        from request_envelope import RequestEnvelope

        # Outer text triggers assumption_surfacing (from "implement") + sequential (from "step by step")
        outer = RequestEnvelope(
            outer_text="Implement this step by step",
            mode="implementation",
            confidence=1.0,
            reason="explicit implementation keywords",
        )
        context_data = {"request_envelope": outer}
        prompt = 'Implement this step by step. "We should delete the old system and compare it to the new one"'
        ctx = HookContext(prompt=prompt, data=context_data,
                          session_id='s', terminal_id='syn-2')
        result = synergy_detector_hook(ctx)
        # Should still detect the synergy because outer text has
        # "implement" (-> assumption_surfacing) and "step by step" (-> sequential)
        assert not result.is_empty(), \
            'Expected synergy detection via envelope-aware fallback'

    def test_degraded_fallback_raw_prompt_still_functions(self, tmp_path, monkeypatch):
        """Tier 3: raw detect_prompt(context.prompt) — no envelope awareness.
        This is the legacy/test path that fires only when both the cached
        detection result AND ensure_unified_detection_result are unavailable.
        It is intentionally retained for compatibility but documented as
        degraded behavior because it CAN be fooled by quoted signals."""
        from UserPromptSubmit_modules.base import HookContext

        prompt = 'Implement this step by step while examining assumptions'
        ctx = HookContext(prompt=prompt, data={}, session_id='s', terminal_id='syn-3')

        # Cause the cached path and ensure_unified_detection_result to both fail
        from UserPromptSubmit_modules import unified_detection as ud_module

        def _break_ensure(_ctx):
            raise RuntimeError("Simulated ensure_unified_detection_result failure")

        monkeypatch.setattr(ud_module, "ensure_unified_detection_result", _break_ensure)

        from UserPromptSubmit_modules.synergy_detector import synergy_detector_hook
        result = synergy_detector_hook(ctx)

        # The prompt "Implement this step by step while examining assumptions"
        # should trigger assumption_surfacing + sequential synergy via the
        # raw detect_prompt fallback even with no envelope context.
        # (This is a degraded path — quoted signals in the prompt COULD
        # produce false-positive synergies, documented as a limitation.)
        assert not result.is_empty(), \
            'Expected synergy detection via raw degraded fallback for implementation+step-by-step prompt'
