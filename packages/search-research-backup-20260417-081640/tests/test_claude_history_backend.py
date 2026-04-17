"""Test Claude History backend integration."""

import pytest

from core.backends.local.claude_history_backend import ClaudeHistoryBackend
from core.router_async import AsyncSearchRouter


@pytest.mark.asyncio
async def test_claude_history_backend_registered():
    """Test that claude-history backend is registered in router."""
    router = AsyncSearchRouter()

    # Trigger backend initialization
    _ = router._create_backends()

    # Check that claude-history is in backends
    assert "claude-history" in router._backends, "claude-history backend should be registered"


@pytest.mark.asyncio
async def test_claude_history_backend_search():
    """Test that claude-history backend can search."""
    router = AsyncSearchRouter()

    try:
        # Try a simple search
        results = await router.search_async("test", limit=5, backends=["claude-history"])

        # Results should be a list (may be empty if no history)
        assert isinstance(results, list), "Results should be a list"

    except FileNotFoundError:
        # CLI not built - skip test
        pytest.skip("claude-history CLI not built")
    except Exception as e:
        # Other errors should fail the test
        pytest.fail(f"Search failed: {e}")


@pytest.mark.asyncio
async def test_claude_history_backend_error_handling():
    """Test that router handles claude-history backend errors gracefully."""
    router = AsyncSearchRouter()

    # If CLI doesn't exist, router should still work (just without this backend)
    # The backend initialization should fail silently
    backends = router._create_backends()

    # Router should have other backends even if claude-history fails
    assert len(backends) > 0, "Router should have at least some backends"


# Diversification tests - test the core logic directly
def test_diversify_results_basic():
    """Test that results from same session are limited to max_per_session."""
    backend = ClaudeHistoryBackend()

    # Create mock results from 3 sessions, 3 results each
    results = []
    for session_num in range(3):
        for msg_num in range(3):
            results.append({
                "title": f"msg-{session_num}-{msg_num}",
                "content": f"content {session_num} {msg_num}",
                "score": 1.0 - (msg_num * 0.1),
                "metadata": {"session_id": f"session-{session_num}"}
            })

    diversified = backend._diversify_results(results, limit=6, max_per_session=2)

    # Count results per session
    session_counts: dict[str, int] = {}
    for r in diversified:
        sid = r["metadata"]["session_id"]
        session_counts[sid] = session_counts.get(sid, 0) + 1

    # Each session should have at most 2 results
    for count in session_counts.values():
        assert count <= 2, f"Session had {count} results, expected <= 2"

    # Should have exactly 6 results (limit)
    assert len(diversified) == 6, f"Expected 6 results, got {len(diversified)}"


def test_diversify_results_empty():
    """Test that empty results returns empty list."""
    backend = ClaudeHistoryBackend()
    diversified = backend._diversify_results([], limit=10)
    assert diversified == []


def test_diversify_results_single_session():
    """Test diversification with single session - returns up to limit."""
    backend = ClaudeHistoryBackend()

    results = []
    for msg_num in range(5):
        results.append({
            "title": f"msg-{msg_num}",
            "content": f"content {msg_num}",
            "score": 1.0 - (msg_num * 0.1),
            "metadata": {"session_id": "session-only"}
        })

    # With only 1 session, round-robin takes 2 (max_per_session) then fallback fills remaining 1 slot
    diversified = backend._diversify_results(results, limit=3, max_per_session=2)

    # Should get exactly 3 (limit) - 2 from round-robin, 1 from fallback fill
    assert len(diversified) == 3


def test_diversify_results_round_robin():
    """Test that results are interleaved across sessions (round-robin)."""
    backend = ClaudeHistoryBackend()

    # 2 sessions with 2 results each, ordered by score
    results = [
        # Session A results (higher scores first)
        {"title": "A-high", "content": "", "score": 1.0, "metadata": {"session_id": "A"}},
        {"title": "A-low", "content": "", "score": 0.5, "metadata": {"session_id": "A"}},
        # Session B results (higher scores first)
        {"title": "B-high", "content": "", "score": 0.9, "metadata": {"session_id": "B"}},
        {"title": "B-low", "content": "", "score": 0.4, "metadata": {"session_id": "B"}},
    ]

    diversified = backend._diversify_results(results, limit=4, max_per_session=2)

    # Check round-robin interleaving: A, B, A, B (or A, B, B, A depending on sort)
    titles = [r["title"] for r in diversified]
    # First two should be A-high and B-high (best from each)
    assert "A-high" in titles[:2]
    assert "B-high" in titles[:2]


def test_diversify_results_respects_limit():
    """Test that limit is respected after round-robin fill."""
    backend = ClaudeHistoryBackend()

    results = []
    for session_num in range(4):
        for msg_num in range(3):
            results.append({
                "title": f"{session_num}-{msg_num}",
                "content": "",
                "score": 1.0,
                "metadata": {"session_id": f"s{session_num}"}
            })

    diversified = backend._diversify_results(results, limit=3, max_per_session=2)

    assert len(diversified) == 3


def test_diversify_results_metadata_none():
    """Test that metadata=None is handled gracefully."""
    backend = ClaudeHistoryBackend()

    results = [
        {"title": "msg-1", "content": "", "score": 1.0, "metadata": None},
        {"title": "msg-2", "content": "", "score": 0.9, "metadata": {"session_id": "s1"}},
        {"title": "msg-3", "content": "", "score": 0.8, "metadata": {"session_id": "s1"}},
    ]

    # Should not raise AttributeError — metadata=None should be treated as {}
    diversified = backend._diversify_results(results, limit=3, max_per_session=2)

    assert len(diversified) == 3
    # Results with metadata=None should be grouped under "unknown" session
    # Use safe access pattern to check
    session_ids = [(r.get("metadata") or {}).get("session_id", "unknown") for r in diversified]
    assert "unknown" in session_ids


def test_diversify_results_missing_metadata_key():
    """Test that missing 'metadata' key is handled gracefully."""
    backend = ClaudeHistoryBackend()

    results = [
        {"title": "msg-1", "content": "", "score": 1.0},  # no metadata key at all
        {"title": "msg-2", "content": "", "score": 0.9, "metadata": {"session_id": "s1"}},
    ]

    # Should not raise — should use {} as fallback
    diversified = backend._diversify_results(results, limit=2, max_per_session=2)

    assert len(diversified) == 2


def test_diversify_results_max_per_session_zero():
    """Test that max_per_session=0 returns score-sorted results without diversification."""
    backend = ClaudeHistoryBackend()

    results = []
    for session_num in range(3):
        for msg_num in range(2):
            results.append({
                "title": f"s{session_num}-msg{msg_num}",
                "content": "",
                "score": 1.0 - (msg_num * 0.2),
                "metadata": {"session_id": f"s{session_num}"}
            })

    # max_per_session=0 should skip diversification and return score-sorted
    diversified = backend._diversify_results(results, limit=4, max_per_session=0)

    # Verify count and score ordering (score-sorted, not session-round-robin)
    assert len(diversified) == 4
    scores = [r["score"] for r in diversified]
    assert scores == sorted(scores, reverse=True), "Results should be sorted by score descending"


def test_diversify_results_max_per_session_one():
    """Test that max_per_session=1 limits to one result per session."""
    backend = ClaudeHistoryBackend()

    results = [
        {"title": "s0-high", "content": "", "score": 1.0, "metadata": {"session_id": "s0"}},
        {"title": "s0-low", "content": "", "score": 0.5, "metadata": {"session_id": "s0"}},
        {"title": "s1-high", "content": "", "score": 0.9, "metadata": {"session_id": "s1"}},
        {"title": "s1-low", "content": "", "score": 0.4, "metadata": {"session_id": "s1"}},
    ]

    diversified = backend._diversify_results(results, limit=2, max_per_session=1)

    assert len(diversified) == 2
    # Each session should contribute at most 1 result
    session_counts: dict[str, int] = {}
    for r in diversified:
        sid = r["metadata"].get("session_id", "unknown")
        session_counts[sid] = session_counts.get(sid, 0) + 1
    for count in session_counts.values():
        assert count <= 1


def test_diversify_results_no_duplicates():
    """Test that _diversify_results never returns duplicate titles."""
    backend = ClaudeHistoryBackend()

    # 3 sessions with 3 results each
    results = []
    for session_num in range(3):
        for msg_num in range(3):
            results.append({
                "title": f"session-{session_num}-msg-{msg_num}",
                "content": f"content {session_num} {msg_num}",
                "score": 1.0 - (msg_num * 0.1),
                "metadata": {"session_id": f"session-{session_num}"}
            })

    diversified = backend._diversify_results(results, limit=10, max_per_session=2)

    # No duplicates allowed
    titles = [r["title"] for r in diversified]
    assert len(titles) == len(set(titles)), f"Duplicates found: {[t for t in titles if titles.count(t) > 1]}"
    # With 3 sessions and max_per_session=2, round-robin gives 6 results;
    # remaining fallback adds up to 3 more (one per session) = 9 total
    assert len(diversified) == 9
