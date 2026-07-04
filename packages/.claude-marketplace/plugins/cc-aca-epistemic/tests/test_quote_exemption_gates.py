"""Regression tests for the shared use/mention quote-exemption across prose Stop gates.

Covers the shared __lib/quote_exemption.py primitive and its wiring into the five
prose-matching Stop gates. The invariant under test: a trigger phrase that appears
only inside quoted text, code spans, blockquotes, tables, or prose double-quotes
(the model *discussing* a claim) must not fire the gate, while the same phrase
asserted plainly still does.
"""
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
# NOTE: do NOT insert the plugin root — it would shadow the global hooks __lib
# (which holds anti_lazy_policy); see conftest.py. Only add what this file needs.
sys.path.insert(0, str(_ROOT / "__lib"))     # __lib on path (quote_exemption, etc.)
sys.path.insert(0, str(_ROOT / "hooks" / "stop"))

from quote_exemption import (
    is_inside_quoted_content,
    search_unquoted,
    finditer_unquoted,
    has_unquoted_match,
)


class TestSharedPrimitive:
    def _m(self, text, phrase):
        m = re.search(re.escape(phrase), text)
        assert m is not None
        return text, m

    def test_unquoted_match_not_exempt(self):
        t, m = self._m("the root cause is X", "root cause")
        assert not is_inside_quoted_content(t, m)

    def test_prose_double_quote_exempt(self):
        t, m = self._m('it said "root cause" here', "root cause")
        assert is_inside_quoted_content(t, m)

    def test_inline_backtick_exempt(self):
        t, m = self._m("the `root cause` detector", "root cause")
        assert is_inside_quoted_content(t, m)

    def test_fenced_block_exempt(self):
        t, m = self._m("x\n```\nroot cause: y\n```\n", "root cause")
        assert is_inside_quoted_content(t, m)

    def test_blockquote_exempt(self):
        t, m = self._m("> root cause: y", "root cause")
        assert is_inside_quoted_content(t, m)

    def test_search_unquoted_skips_quoted_returns_real(self):
        p = re.compile("root cause", re.I)
        text = 'it said "root cause" but the real root cause is timeout'
        m = search_unquoted(p, text)
        assert m is not None and m.start() == text.index("real root cause") + 5

    def test_finditer_unquoted_counts_only_unquoted(self):
        p = re.compile("root cause", re.I)
        text = 'it said "root cause" but the real root cause is timeout'
        assert len(list(finditer_unquoted(p, text))) == 1

    def test_has_unquoted_match_false_when_all_quoted(self):
        p = re.compile("root cause", re.I)
        assert has_unquoted_match(p, 'only "root cause" here') is False

    def test_stray_quote_does_not_leak_across_lines(self):
        # Regression (parity robustness): a lone unbalanced quote on an earlier
        # line must NOT flip quote pairing for a genuinely-quoted citation on a
        # later line. The old global-parity scan exposed the citation as unquoted;
        # single-line balanced-span matching bounds the stray's effect to its line.
        t, m = self._m(
            'a stray " quote on line one\nthe survey says "root cause" clearly',
            "root cause",
        )
        assert is_inside_quoted_content(t, m)


class TestDiagnosticGate:
    def _gate(self):
        import Stop_diagnostic_analysis_quality_gate as g
        return g

    def test_real_diagnostic_classifies(self):
        g = self._gate()
        real = ("The root cause is the revoked virtual key. This is why all seven providers "
                "fail with identical 401 errors: the regression occurs because the token is "
                "not being injected into the outbound request, which leads directly to the "
                "authentication rejection we observe. Diagnosing further, the causal chain is "
                "that Bifrost reads an empty env var, so the upstream call is unauthenticated "
                "and every route returns the same failure mode across all providers right now.")
        assert g._is_diagnostic_turn(real) is True

    def test_quoted_meta_does_not_classify(self):
        g = self._gate()
        meta = ('The previous agent wrote "the root cause is X" and titled a block "diagnosis". '
                'It claimed something "is why" the failure happened, all inside `regression` quotes. '
                'I am analyzing whether that meta-phrasing should trip the gate, discussing it at '
                'great length here without asserting any causal claim of my own about the system.')
        assert g._is_diagnostic_turn(meta) is False


class TestPerfGate:
    def _gate(self):
        import StopHook_perf_attribution_gate as g
        return g

    def test_unquoted_perf_claim_fires(self):
        g = self._gate()
        # Includes a measurement (~480s) so "dominant factor" is promoted by
        # _MEASUREMENT_SIGNAL — the invariant under test is that an UNQUOTED
        # perf claim fires (vs the quoted variant in the next test).
        assert g._detect_perf_claims(
            "The dominant factor is the idle_wait loop, causing the ~480s total."
        ) is True

    def test_quoted_perf_claim_exempt(self):
        g = self._gate()
        assert g._detect_perf_claims(
            'The old note said "the bottleneck is the idle_wait loop" but I am only quoting it here.'
        ) is False


class TestDeletionGuard:
    def _gate(self):
        import Stop_deletion_verification_guard as g
        return g

    def test_unquoted_deletion_claim_detected(self):
        g = self._gate()
        assert len(g._detect_deletion_claims(
            "I deleted the old config files and removed the stale cache directory."
        )) > 0

    def test_quoted_deletion_claim_exempt(self):
        g = self._gate()
        assert len(g._detect_deletion_claims(
            'The transcript said "files deleted" inside its quoted block, which I am analyzing.'
        )) == 0


class TestComparativeGuard:
    def _gate(self):
        import Stop_comparative_claim_guard as g
        return g

    def test_unquoted_comparison_detected(self):
        g = self._gate()
        assert len(g._find_comparisons(
            "Benchmarking foo.py vs bar.py shows foo.py is the faster path here."
        )) > 0

    def test_quoted_comparison_exempt(self):
        g = self._gate()
        assert len(g._find_comparisons(
            'The doc gave an example "foo.py vs bar.py" which I am merely citing in prose.'
        )) == 0


class TestRemovalGuard:
    def _gate(self):
        import Stop_removal_completeness_guard as g
        return g

    def test_unquoted_completion_trigger_fires(self):
        g = self._gate()
        assert has_unquoted_match(
            g.REMOVAL_COMPLETION_PATTERNS,
            "The auth_handler module was fully removed and all references deleted.",
        ) is True

    def test_quoted_completion_trigger_exempt(self):
        g = self._gate()
        assert has_unquoted_match(
            g.REMOVAL_COMPLETION_PATTERNS,
            'Someone earlier wrote "the auth_handler module" but I am quoting that phrase only.',
        ) is False
