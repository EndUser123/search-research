"""Tests for the request envelope + quote-aware task_start_contract_writer.

Regression coverage for the bug where a UserPromptSubmit hook misclassified
quoted proposal text as the user's actual request.

Run with: pytest P:/.claude/hooks/UserPromptSubmit_modules/tests/test_request_envelope.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure hooks directory is on sys.path for imports
HOOKS_DIR = Path(__file__).resolve().parent.parent.parent
LIB_DIR = HOOKS_DIR / "__lib"
for d in (str(HOOKS_DIR), str(LIB_DIR)):
    if d not in sys.path:
        sys.path.insert(0, d)


def _load_module(name: str, path: Path):
    """Fresh-import a hook module by file path so each test sees the current code."""
    import importlib
    import importlib.util
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def tsc():
    """Fresh task_start_contract_writer module."""
    return _load_module(
        "task_start_contract_writer",
        HOOKS_DIR / "UserPromptSubmit_modules" / "task_start_contract_writer.py",
    )


@pytest.fixture
def envelope_mod():
    from UserPromptSubmit_modules.request_envelope import analyze_prompt
    return analyze_prompt


# =============================================================================
# Request envelope: quote/fence stripping
# =============================================================================


class TestStripQuotedSpans:
    def _strip(self):
        from UserPromptSubmit_modules.request_envelope import strip_quoted_spans
        return strip_quoted_spans

    def test_double_quotes_stripped(self):
        outer, spans = self._strip()('He said "Implement the hook." today.')
        assert "Implement the hook" not in outer
        assert "today" in outer
        assert spans and '"Implement the hook."' in spans[0]

    def test_single_quotes_stripped(self):
        outer, spans = self._strip()("Do these 'Every handoff must X' make sense?")
        assert "Every handoff" not in outer
        assert "Do these" in outer and "make sense" in outer

    def test_curly_double_quotes_stripped(self):
        outer, spans = self._strip()("He said “Implement the hook.” today.")
        assert "Implement the hook" not in outer
        assert any("“" in s for s in spans)

    def test_curly_single_quote_pair_stripped(self):
        outer, spans = self._strip()("Do these ‘Every handoff must X’ make sense?")
        assert "Every handoff" not in outer
        assert "make sense" in outer

    def test_fenced_block_stripped(self):
        outer, spans = self._strip()("Try this:\n```\nfix the bug\n```\nDoes it work?")
        assert "fix the bug" not in outer
        assert "Does it work" in outer

    def test_blockquote_stripped(self):
        outer, spans = self._strip()("What do you think?\n> Implement the hook")
        assert "Implement the hook" not in outer
        assert "What do you think" in outer

    def test_apostrophe_not_treated_as_quote(self):
        # 's contractions must remain; only balanced PAIRS get stripped
        outer, _ = self._strip()("It's a test of the system.")
        # "It's" is not a balanced pair, so it should remain
        assert "It" in outer
        assert "system" in outer

    def test_no_quotes_returns_full_text(self):
        text = "Implement the UserPromptSubmit request envelope."
        outer, spans = self._strip()(text)
        assert outer.strip() == text
        assert spans == []


# =============================================================================
# Request envelope: mode classification
# =============================================================================


class TestRequestEnvelopeMode:
    def test_recap_evaluation(self, envelope_mod):
        # The exact /recap bug pattern.
        env = envelope_mod("for the /recap skill, do these enhancements make sense? 'Every handoff must X'")
        assert env.mode == "evaluation"
        assert "Every handoff" in env.quoted_spans[0]

    def test_quoted_implement_inside_evaluation(self, envelope_mod):
        env = envelope_mod("Do these changes make sense? 'Implement the hook.'")
        assert env.mode == "evaluation"

    def test_quoted_bug_inside_proposal(self, envelope_mod):
        env = envelope_mod("What do you think of this design? 'fix the parser bug'")
        assert env.mode == "evaluation"

    def test_fenced_imperative_ignored(self, envelope_mod):
        env = envelope_mod("What do you think?\n```\nfix the bug\n```\n")
        assert env.mode == "evaluation"
        assert env.quoted_spans, "fenced block should be captured as a span"

    def test_make_sense_not_implementation(self, envelope_mod):
        env = envelope_mod("Do these make sense?")
        assert env.mode == "evaluation"

    def test_do_this_implement_not_mixed(self, envelope_mod):
        """Regression: 'Do this: implement X' should classify as implementation,
        NOT mixed/evaluation. The bare 'do this' was removed from _EVAL_RE because
        it false-negatives on real implementation requests."""
        env = envelope_mod("Do this: implement the cache layer")
        assert env.mode == "implementation"

    def test_review_then_implement_is_mixed(self, envelope_mod):
        env = envelope_mod("Review proposal A, then implement proposal B.")
        assert env.mode == "mixed"
        assert env.multiple_requests

    def test_does_this_make_sense_then_implement(self, envelope_mod):
        env = envelope_mod("Does this make sense? If yes, implement it.")
        assert env.mode == "mixed"

    def test_explicit_implementation(self, envelope_mod):
        env = envelope_mod("Implement the UserPromptSubmit request envelope.")
        assert env.mode == "implementation"

    def test_explicit_diagnosis(self, envelope_mod):
        env = envelope_mod("Diagnose why the parser crashes.")
        assert env.mode == "diagnosis"

    def test_explicit_fix_is_implementation(self, envelope_mod):
        # bug_fix task class still creates a contract, so envelope treats
        # "fix X" as the implementation mode.
        env = envelope_mod("Fix the task contract false positive.")
        assert env.mode == "implementation"

    def test_explicit_refactor(self, envelope_mod):
        env = envelope_mod("Refactor task_start_contract_writer.py.")
        assert env.mode == "implementation"

    def test_ambiguous_no_signal(self, envelope_mod):
        env = envelope_mod("What is the weather like?")
        assert env.mode == "ambiguous"

    def test_research_signal(self, envelope_mod):
        env = envelope_mod("Explain the failure, update the docs, and run the tests.")
        assert env.mode == "research"

    def test_quoted_signal_ignored_reason(self, envelope_mod):
        env = envelope_mod("What do you think of this plan? 'fix the bug'")
        # Quoted impl signal ignored; outer is evaluation.
        assert env.mode == "evaluation"
        assert env.reason == "quoted_signal_ignored"


# =============================================================================
# task_start_contract_writer: quote-aware detection (regression)
# =============================================================================


@pytest.fixture(autouse=True)
def _isolated_artifacts(tmp_path, monkeypatch):
    import __lib.task_contract as _tc
    monkeypatch.setattr(_tc, "_home", lambda: tmp_path)
    yield


def _load_fresh_tsc():
    import importlib
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "task_start_contract_writer",
        HOOKS_DIR / "UserPromptSubmit_modules" / "task_start_contract_writer.py",
    )
    mod = importlib.util.module_from_spec(spec)
    import __lib.task_contract
    sys.modules["__lib.task_contract"] = __lib.task_contract
    spec.loader.exec_module(mod)
    return mod


def _ensure_envelope(mod, prompt):
    """Build a real RequestEnvelope and stash it on a fake context."""
    from UserPromptSubmit_modules.request_envelope import analyze_prompt
    from UserPromptSubmit_modules.base import HookContext
    env = analyze_prompt(prompt)
    ctx = HookContext(prompt=prompt, data={"request_envelope": env}, session_id="s", terminal_id="t")
    return ctx, env


class TestTaskStartContractWriterRegression:
    def test_recap_prompt_does_not_create_contract(self, tmp_path):
        """The exact /recap evaluation pattern must NOT create a bug_diagnosis or implementation contract."""
        from __lib.task_contract import load_contract
        mod = _load_fresh_tsc()
        # Patch _home for the freshly loaded module too
        mod._home = lambda: tmp_path  # type: ignore[attr-defined]

        prompt = "for the /recap skill, do these enhancements make sense? 'Every handoff must X'"
        ctx, _ = _ensure_envelope(mod, prompt)
        # Replace context.terminal_id with our own so the fixture-scoped tmp_path is used.
        ctx = type(ctx)(
            prompt=prompt,
            data={**ctx.data},
            session_id="s",
            terminal_id="term-recap",
        )
        result = mod.task_start_contract_writer(ctx)
        assert result.is_empty()
        assert load_contract("term-recap") is None

    def test_quoted_implement_in_evaluation_skipped(self, tmp_path):
        from __lib.task_contract import load_contract
        mod = _load_fresh_tsc()
        mod._home = lambda: tmp_path  # type: ignore[attr-defined]
        prompt = "Do these changes make sense? 'Implement the hook.'"
        ctx = mod.HookContext(prompt=prompt, data={}, session_id="s", terminal_id="term-qi")
        mod.task_start_contract_writer(ctx)
        assert load_contract("term-qi") is None

    def test_quoted_bug_in_proposal_skipped(self, tmp_path):
        from __lib.task_contract import load_contract
        mod = _load_fresh_tsc()
        mod._home = lambda: tmp_path  # type: ignore[attr-defined]
        prompt = "What do you think of this design? 'fix the parser bug'"
        ctx = mod.HookContext(prompt=prompt, data={}, session_id="s", terminal_id="term-qb")
        mod.task_start_contract_writer(ctx)
        assert load_contract("term-qb") is None

    def test_fenced_imperative_ignored(self, tmp_path):
        from __lib.task_contract import load_contract
        mod = _load_fresh_tsc()
        mod._home = lambda: tmp_path  # type: ignore[attr-defined]
        prompt = "What do you think?\n```\nfix the bug\n```\n"
        ctx = mod.HookContext(prompt=prompt, data={}, session_id="s", terminal_id="term-fence")
        mod.task_start_contract_writer(ctx)
        assert load_contract("term-fence") is None

    def test_make_sense_does_not_create_implementation(self, tmp_path):
        from __lib.task_contract import load_contract
        mod = _load_fresh_tsc()
        mod._home = lambda: tmp_path  # type: ignore[attr-defined]
        prompt = "Do these make sense?"
        ctx = mod.HookContext(prompt=prompt, data={}, session_id="s", terminal_id="term-ms")
        mod.task_start_contract_writer(ctx)
        assert load_contract("term-ms") is None

    def test_review_then_implement_fails_open(self, tmp_path):
        from __lib.task_contract import load_contract
        mod = _load_fresh_tsc()
        mod._home = lambda: tmp_path  # type: ignore[attr-defined]
        prompt = "Review proposal A, then implement proposal B."
        ctx = mod.HookContext(prompt=prompt, data={}, session_id="s", terminal_id="term-mix")
        mod.task_start_contract_writer(ctx)
        assert load_contract("term-mix") is None

    def test_does_this_then_implement_fails_open(self, tmp_path):
        from __lib.task_contract import load_contract
        mod = _load_fresh_tsc()
        mod._home = lambda: tmp_path  # type: ignore[attr-defined]
        prompt = "Does this make sense? If yes, implement it."
        ctx = mod.HookContext(prompt=prompt, data={}, session_id="s", terminal_id="term-cond")
        mod.task_start_contract_writer(ctx)
        assert load_contract("term-cond") is None

    def test_explicit_implementation_still_creates(self, tmp_path):
        from __lib.task_contract import load_contract
        mod = _load_fresh_tsc()
        mod._home = lambda: tmp_path  # type: ignore[attr-defined]
        prompt = "Implement the UserPromptSubmit request envelope."
        ctx = mod.HookContext(prompt=prompt, data={}, session_id="s", terminal_id="term-impl")
        mod.task_start_contract_writer(ctx)
        assert load_contract("term-impl") is not None

    def test_explicit_diagnosis_still_creates(self, tmp_path):
        from __lib.task_contract import load_contract
        mod = _load_fresh_tsc()
        mod._home = lambda: tmp_path  # type: ignore[attr-defined]
        prompt = "Diagnose why the parser crashes."
        ctx = mod.HookContext(prompt=prompt, data={}, session_id="s", terminal_id="term-diag")
        mod.task_start_contract_writer(ctx)
        contract = load_contract("term-diag")
        assert contract is not None
        assert contract["task_class"] == "bug_diagnosis"

    def test_explicit_fix_still_creates(self, tmp_path):
        from __lib.task_contract import load_contract
        mod = _load_fresh_tsc()
        mod._home = lambda: tmp_path  # type: ignore[attr-defined]
        prompt = "Fix the task contract false positive."
        ctx = mod.HookContext(prompt=prompt, data={}, session_id="s", terminal_id="term-fix")
        mod.task_start_contract_writer(ctx)
        contract = load_contract("term-fix")
        assert contract is not None
        assert contract["task_class"] == "bug_fix"

    def test_explicit_refactor_still_creates(self, tmp_path):
        from __lib.task_contract import load_contract
        mod = _load_fresh_tsc()
        mod._home = lambda: tmp_path  # type: ignore[attr-defined]
        prompt = "Refactor task_start_contract_writer.py."
        ctx = mod.HookContext(prompt=prompt, data={}, session_id="s", terminal_id="term-ref")
        mod.task_start_contract_writer(ctx)
        contract = load_contract("term-ref")
        assert contract is not None
        assert contract["task_class"] == "refactor"

    def test_session_identity_isolated(self, tmp_path):
        """Different terminals must not share contracts."""
        from __lib.task_contract import load_contract
        mod = _load_fresh_tsc()
        mod._home = lambda: tmp_path  # type: ignore[attr-defined]
        prompt = "Implement the UserPromptSubmit request envelope."

        ctx_a = mod.HookContext(prompt=prompt, data={}, session_id="s", terminal_id="term-A")
        mod.task_start_contract_writer(ctx_a)
        ctx_b = mod.HookContext(prompt=prompt, data={}, session_id="s", terminal_id="term-B")
        mod.task_start_contract_writer(ctx_b)

        a = load_contract("term-A")
        b = load_contract("term-B")
        assert a is not None and b is not None
        # Same prompt, same task_id, but the contract for B is a separate
        # store entry because terminal_id is the namespacing key.
        assert a["task_id"] == b["task_id"]


class TestRequestEnvelopeCache:
    def test_ensure_request_envelope_caches_on_context(self):
        from UserPromptSubmit_modules.base import HookContext
        from UserPromptSubmit_modules.unified_detection import ensure_request_envelope

        prompt = "Do these make sense? 'implement X'"
        ctx = HookContext(prompt=prompt, data={}, session_id="s", terminal_id="t")
        e1 = ensure_request_envelope(ctx)
        e2 = ensure_request_envelope(ctx)
        # Same object — cached on context.data
        assert e1 is e2
        assert e1.mode == "evaluation"
