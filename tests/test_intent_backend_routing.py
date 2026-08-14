"""Gate test: _get_backends_for_mode(query=...) narrows backend fan-out by intent.

Closes the "wired but unverified" gap for Stream B (intent-based backend routing).
If _get_backends_for_mode ignores the `query` argument, every test in this file
fails — this is the single proof that the intent filter is live at runtime.

The filtering logic under test is core/router_async.py:1087-1098. Backends are
stubbed (real names, sentinel objects) so the test exercises the real classifier
+ BACKEND_FOR_INTENT intersection without initializing slow/networked backends.
"""

from __future__ import annotations

import pytest

from search_research import AsyncSearchRouter

# Real backend names registered by AsyncSearchRouter._create_backends().
# Must be a superset of every BACKEND_FOR_INTENT set so the intersection is real.
REAL_BACKEND_NAMES = [
    "cds", "grep", "skills", "cks", "kg", "rlm", "claude-history",
    "vault", "notebooklm", "ast_code", "cpg", "hdma", "lsp",
    "dependency", "call_graph", "qmd_wiki", "yt_is", "domain_constraint",
]


@pytest.fixture
def router() -> AsyncSearchRouter:
    """Router with backends stubbed to real names — no slow initialization."""
    r = AsyncSearchRouter()
    r._backends = {name: object() for name in REAL_BACKEND_NAMES}
    r._backends_initialized = True
    return r


class TestIntentFilterWiring:
    """The wiring proof: query= narrows fan-out; query=None preserves all."""

    def test_no_query_returns_all_backends(self, router: AsyncSearchRouter) -> None:
        """Backward compat: no query = no filter, all backends returned."""
        result = router._get_backends_for_mode()
        assert set(result) == set(REAL_BACKEND_NAMES)

    def test_none_query_returns_all_backends(self, router: AsyncSearchRouter) -> None:
        result = router._get_backends_for_mode(query=None)
        assert set(result) == set(REAL_BACKEND_NAMES)

    def test_intent_filter_narrows_fan_out(self, router: AsyncSearchRouter) -> None:
        """A classified query must return FEWER backends than no query.

        This is the load-bearing assertion: if _get_backends_for_mode ignores
        `query`, this fails and the entire intent-routing change is inert.
        """
        all_backends = router._get_backends_for_mode()
        filtered = router._get_backends_for_mode(query="what is faiss vector")
        assert len(filtered) < len(all_backends), (
            f"Intent filter did not narrow fan-out: all={len(all_backends)}, "
            f"filtered={len(filtered)} — wiring is inert"
        )

    def test_unknown_intent_returns_all_backends(self, router: AsyncSearchRouter) -> None:
        """UNKNOWN intent (empty allowed set) falls back to all backends."""
        result = router._get_backends_for_mode(query="test")
        assert set(result) == set(REAL_BACKEND_NAMES)


class TestIntentToBackendMapping:
    """Pin the exact backend set each IntentType resolves to.

    If BACKEND_FOR_INTENT changes, these break loudly — no silent drift.
    Queries chosen to hit deterministic fast-path keyword patterns, not the
    embedding model, so the mapping is stable across runs.
    """

    @pytest.mark.parametrize(
        "query,expected",
        [
            # INFORMATIONAL (fast path: "what is")
            (
                "what is faiss vector",
                {"cds", "cks", "claude-history", "notebooklm", "qmd_wiki", "skills", "yt_is"},
            ),
            # TECHNICAL (fast path: "def ")
            (
                "python def example code",
                {"ast_code", "cds", "cpg", "grep", "lsp", "notebooklm", "skills", "yt_is"},
            ),
            # NAVIGATIONAL (fast path: "how do i")
            (
                "how do I configure router",
                {"cds", "claude-history", "grep", "notebooklm", "skills", "vault"},
            ),
            # EXPLORATORY (fast path: "best practices")
            (
                "best practices for caching",
                {"ast_code", "cds", "cks", "notebooklm", "qmd_wiki", "skills", "vault", "yt_is"},
            ),
        ],
    )
    def test_query_maps_to_expected_backends(
        self,
        router: AsyncSearchRouter,
        query: str,
        expected: set[str],
    ) -> None:
        result = set(router._get_backends_for_mode(query=query))
        assert result == expected, f"{query!r} -> {sorted(result)}, expected {sorted(expected)}"
