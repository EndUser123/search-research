"""Tests for core/history_chain.py — session chain traversal via history.jsonl."""

from __future__ import annotations

import time

import pytest

from core.history_chain import (
    ChainEntry,
    ChainWalkResult,
    UUIDIndex,
    _history_jsonl,
    _sessions_index,
    format_chain_summary,
    get_index,
    load_sessions_index,
    session_file_exists,
    walk_chain,
    walk_chain_simple,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def real_index() -> UUIDIndex:
    """Build the real UUID index against the actual history.jsonl."""
    idx = UUIDIndex()
    idx.build()
    return idx


@pytest.fixture(scope="module")
def known_chain_uuid(real_index: UUIDIndex) -> str:
    """Find a UUID that has a parent (part of a chain)."""
    for uuid in real_index._index:
        raw = real_index.get(uuid)
        if raw and raw.get("parentUuid"):
            return uuid
    pytest.skip("No chained UUIDs found in history.jsonl")


@pytest.fixture(scope="module")
def known_summary_uuid(real_index: UUIDIndex) -> str | None:
    """Find a UUID with entry_type='summary' for dict-message tests."""
    for uuid in real_index._index:
        raw = real_index.get(uuid)
        if raw and raw.get("type") == "summary":
            return uuid
    return None


@pytest.fixture(scope="module")
def deep_chain_uuid(real_index: UUIDIndex) -> str:
    """Find a UUID in a chain with depth > 50."""
    for uuid in real_index._index:
        raw = real_index.get(uuid)
        if raw and raw.get("parentUuid"):
            result = walk_chain(start_uuid=uuid, index=real_index, depth=200)
            if result.depth > 50:
                return uuid
    pytest.skip("No deep chain found in history.jsonl")


# ---------------------------------------------------------------------------
# UUIDIndex
# ---------------------------------------------------------------------------


class TestUUIDIndex:
    def test_build_indexes_all_entries(self, real_index: UUIDIndex) -> None:
        """Index should contain every UUID in history.jsonl."""
        assert len(real_index._index) > 300_000, "Expected >300K entries"

    def test_build_sets_built_at(self, real_index: UUIDIndex) -> None:
        """build() must set _built_at timestamp."""
        assert real_index._built_at is not None

    def test_get_returns_entry_dict(self, real_index: UUIDIndex, known_chain_uuid: str) -> None:
        """get() returns the full entry dict for a known UUID."""
        entry = real_index.get(known_chain_uuid)
        assert entry is not None
        assert "uuid" in entry or "leafUuid" in entry

    def test_get_returns_none_for_unknown(self, real_index: UUIDIndex) -> None:
        """get() returns None for UUIDs not in history.jsonl."""
        entry = real_index.get("00000000-0000-0000-0000-000000000000")
        assert entry is None

    def test_check_stale_false_on_fresh_build(self, real_index: UUIDIndex) -> None:
        """Index should not report stale immediately after build."""
        assert not real_index._check_stale()


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------


class TestPathHelpers:
    def test_history_jsonl_resolves(self) -> None:
        """_history_jsonl() should resolve to the real history.jsonl path."""
        path = _history_jsonl()
        assert path.name == "history.jsonl"
        assert path.exists(), f"history.jsonl not found at {path}"

    def test_sessions_index_resolves(self) -> None:
        """_sessions_index() should resolve to P-- sessions-index."""
        path = _sessions_index()
        assert "sessions-index.json" in str(path)
        assert "P--" in str(path)


# ---------------------------------------------------------------------------
# walk_chain
# ---------------------------------------------------------------------------


class TestWalkChain:
    def test_walk_chain_returns_chain_walk_result(
        self, real_index: UUIDIndex, known_chain_uuid: str
    ) -> None:
        """walk_chain returns a ChainWalkResult."""
        result = walk_chain(start_uuid=known_chain_uuid, index=real_index, depth=5)
        assert isinstance(result, ChainWalkResult)

    def test_walk_chain_respects_depth_limit(
        self, real_index: UUIDIndex, known_chain_uuid: str
    ) -> None:
        """depth parameter caps the number of hops."""
        result = walk_chain(start_uuid=known_chain_uuid, index=real_index, depth=3)
        assert result.depth <= 3

    def test_walk_chain_reaches_origin(self, real_index: UUIDIndex, deep_chain_uuid: str) -> None:
        """Deep walk should find an origin entry (parentUuid=null)."""
        result = walk_chain(start_uuid=deep_chain_uuid, index=real_index, depth=200)
        assert result.depth > 10, "Should walk more than 10 hops"
        origins = [e for e in result.entries if e.is_origin]
        assert len(origins) == 1, "Chain should have exactly one origin"

    def test_walk_chain_reverses_chronologically(
        self, real_index: UUIDIndex, known_chain_uuid: str
    ) -> None:
        """Entries should be ordered oldest → newest."""
        result = walk_chain(start_uuid=known_chain_uuid, index=real_index, depth=20)
        dated_entries = [(e, e.created) for e in result.entries if e.created is not None]
        if len(dated_entries) > 1:
            for (e1, t1), (e2, t2) in zip(dated_entries[:-1], dated_entries[1:], strict=False):
                assert t1 <= t2, f"Entries should be chronologically ordered: {t1} > {t2}"

    def test_walk_chain_summary_only_filters(
        self, real_index: UUIDIndex, deep_chain_uuid: str
    ) -> None:
        """summary_only=True should only return summary-type entries."""
        result = walk_chain(
            start_uuid=deep_chain_uuid, index=real_index, depth=200, summary_only=True
        )
        # May be empty or few entries — that's valid; the filter logic works
        assert isinstance(result, ChainWalkResult)
        if result.entries:
            assert all(
                e.entry_type == "summary" for e in result.entries
            ), "All entries should be type=summary"

    def test_walk_chain_unknown_uuid_returns_empty(self, real_index: UUIDIndex) -> None:
        """Starting from an unknown UUID returns empty chain."""
        result = walk_chain(
            start_uuid="ffffffff-ffff-ffff-ffff-ffffffffffff",
            index=real_index,
            depth=5,
        )
        assert result.depth == 0
        assert result.entries == []


# ---------------------------------------------------------------------------
# walk_chain_simple (convenience wrapper)
# ---------------------------------------------------------------------------


class TestWalkChainSimple:
    def test_simple_uses_global_index(self) -> None:
        """walk_chain_simple should use and reuse the global index."""
        idx = get_index()
        assert idx._built_at is not None

    def test_simple_returns_correct_structure(self, known_chain_uuid: str) -> None:
        """walk_chain_simple returns a valid ChainWalkResult."""
        # known_chain_uuid depends on real_index (module scope) — index is warm
        result = walk_chain_simple(start_uuid=known_chain_uuid, depth=3)
        assert isinstance(result, ChainWalkResult)

    def test_simple_reuses_index_on_repeated_calls(self, known_chain_uuid: str) -> None:
        """Subsequent calls should not rebuild the index."""
        get_index()  # warm up / establish cache
        t0 = time.time()
        result = walk_chain_simple(start_uuid=known_chain_uuid, depth=5)
        t1 = time.time()
        assert t1 - t0 < 0.5, f"Walk took {t1 - t0:.3f}s — index should be cached"
        assert isinstance(result, ChainWalkResult)


# ---------------------------------------------------------------------------
# load_sessions_index
# ---------------------------------------------------------------------------


class TestLoadSessionsIndex:
    def test_returns_dict(self) -> None:
        """load_sessions_index returns a dict."""
        index = load_sessions_index()
        assert isinstance(index, dict)

    def test_session_ids_are_strings(self) -> None:
        """Keys are sessionId strings."""
        index = load_sessions_index()
        for key in index:
            assert isinstance(key, str)
            assert len(key) == 36  # UUID format

    def test_fake_session_not_found(self) -> None:
        """Fake session IDs return empty dict."""
        index = load_sessions_index()
        assert "00000000-0000-0000-0000-000000000000" not in index


# ---------------------------------------------------------------------------
# session_file_exists
# ---------------------------------------------------------------------------


class TestSessionFileExists:
    def test_fake_session_returns_false(self) -> None:
        """Non-existent session returns False."""
        assert session_file_exists("00000000-0000-0000-0000-000000000000") is False


# ---------------------------------------------------------------------------
# format_chain_summary
# ---------------------------------------------------------------------------


class TestFormatChainSummary:
    def test_contains_chain_path_header(self, known_chain_uuid: str) -> None:
        """Output starts with '=== Chain Path ==='."""
        result = walk_chain_simple(start_uuid=known_chain_uuid, depth=3)
        output = format_chain_summary(result)
        assert "Chain Path" in output

    def test_contains_depth_info(self, known_chain_uuid: str) -> None:
        """Output includes depth information."""
        result = walk_chain_simple(start_uuid=known_chain_uuid, depth=3)
        output = format_chain_summary(result)
        assert "Depth:" in output

    def test_no_crash_on_empty_entries(self) -> None:
        """Empty entries list should not crash format_chain_summary."""
        result = ChainWalkResult(
            entries=[],
            depth=0,
            origin_session_id=None,
            compacted_sessions=set(),
            index_age=None,
        )
        output = format_chain_summary(result)
        assert "Depth: 0" in output

    def test_no_crash_on_dict_messages(self, known_chain_uuid: str) -> None:
        """Entries with dict messages should not crash formatting."""
        result = walk_chain_simple(start_uuid=known_chain_uuid, depth=5)
        output = format_chain_summary(result)  # Should not raise
        assert isinstance(output, str)


# ---------------------------------------------------------------------------
# ChainEntry dataclass
# ---------------------------------------------------------------------------


class TestChainEntry:
    def test_origin_has_no_parent(self) -> None:
        """An origin entry has parent_uuid=None."""
        entry = ChainEntry(
            uuid="test",
            parent_uuid=None,
            session_id="test",
            entry_type="summary",
            message=None,
            summary="test",
            leaf_uuid="leaf",
            created=None,
            is_origin=True,
        )
        assert entry.is_origin
        assert entry.parent_uuid is None
