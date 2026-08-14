"""Tests for per-query telemetry: writer + router instrumentation.

Proves:
- log_query_event writes a valid JSON line with all 8 schema fields.
- hash_query is stable and privacy-truncated.
- _get_backends_for_mode stashes the 6 filter fields on a real router call.
- A real search_async() call emits exactly one telemetry line with cache_hit=False.
- A cache-hit search_async() emits one line with cache_hit=True / intent=skipped_cache.
- The writer is non-blocking (bad path never raises).
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import pytest

from search_research import AsyncSearchRouter
from core import query_telemetry as qt

REAL_BACKEND_NAMES = [
    "cds", "grep", "skills", "cks", "claude-history",
    "vault", "notebooklm", "ast_code", "lsp", "yt_is",
]


def _read_lines(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


@pytest.fixture
def telemetry_path(tmp_path, monkeypatch) -> Path:
    """Point the telemetry writer at a tmp file via the env override."""
    p = tmp_path / "query_telemetry.jsonl"
    monkeypatch.setenv("SR_QUERY_TELEMETRY_PATH", str(p))
    # resolve_path() reads the env live, so no module reload needed.
    assert qt.resolve_path() == p
    return p


class TestWriter:
    def test_writes_all_schema_fields(self, telemetry_path: Path) -> None:
        qt.log_query_event(
            query_hash="abc123", intent="technical", confidence=0.9,
            all_backends_count=18, filtered_backends_count=8,
            classify_ms=9.4, returned_count=7, cache_hit=False,
        )
        rows = _read_lines(telemetry_path)
        assert len(rows) == 1
        r = rows[0]
        for field in ("ts", "query_hash", "intent", "confidence",
                      "all_backends_count", "filtered_backends_count",
                      "classify_ms", "returned_count", "cache_hit"):
            assert field in r, f"missing schema field: {field}"
        assert r["intent"] == "technical"
        assert r["returned_count"] == 7
        assert r["cache_hit"] is False

    def test_hash_is_stable_and_truncated(self) -> None:
        h1 = qt.hash_query("what is faiss")
        h2 = qt.hash_query("what is faiss")
        assert h1 == h2
        assert len(h1) == 16
        # Different queries produce different hashes.
        assert qt.hash_query("def foo") != h1

    def test_non_blocking_on_bad_path(self, monkeypatch) -> None:
        # A path whose parent cannot be created must NOT raise.
        monkeypatch.setenv("SR_QUERY_TELEMETRY_PATH", "/nonexistent-root/x/y/z.jsonl")
        qt.log_query_event(
            query_hash="x", intent="unknown", confidence=0.0,
            all_backends_count=0, filtered_backends_count=0,
            classify_ms=0.0, returned_count=0, cache_hit=False,
        )

    def test_log_quality_check_writes_fm4_record(self, telemetry_path: Path) -> None:
        qt.log_quality_check(
            query_hash="deadbeef", satisfactory=True, confidence=0.91,
            backend_diversity=3, fresh=True,
        )
        rows = _read_lines(telemetry_path)
        assert len(rows) == 1
        r = rows[0]
        assert r["event"] == "quality_check"
        assert r["satisfactory"] is True
        assert r["backend_diversity"] == 3
        assert r["query_hash"] == "deadbeef"


@pytest.fixture
def stub_router() -> AsyncSearchRouter:
    """Router with backends stubbed to real names — no slow/networked init."""
    r = AsyncSearchRouter()
    r._backends = {name: object() for name in REAL_BACKEND_NAMES}
    r._backends_initialized = True
    r.enable_cache = False
    return r


class TestRouterInstrumentation:
    def test_get_backends_stashes_filter_telemetry(self, stub_router: AsyncSearchRouter) -> None:
        """_get_backends_for_mode(query=) stashes the 6 filter fields."""
        assert not hasattr(stub_router, "_last_filter_telemetry") or \
            stub_router._last_filter_telemetry is None
        filtered = stub_router._get_backends_for_mode(query="what is faiss vector")
        stash = stub_router._last_filter_telemetry
        assert stash is not None
        for field in ("query_hash", "intent", "confidence",
                      "all_backends_count", "filtered_backends_count", "classify_ms"):
            assert field in stash, f"stash missing {field}"
        assert stash["intent"] == "informational"
        assert stash["all_backends_count"] == len(REAL_BACKEND_NAMES)
        assert stash["filtered_backends_count"] == len(filtered)
        assert stash["filtered_backends_count"] < stash["all_backends_count"]
        assert stash["classify_ms"] >= 0.0
        assert len(stash["query_hash"]) == 16

    def test_unknown_query_stash_all_count_equal_filtered(self, stub_router: AsyncSearchRouter) -> None:
        """UNKNOWN intent falls back to all backends → filtered==all in the stash."""
        stub_router._get_backends_for_mode(query="test")  # fast-path → UNKNOWN
        stash = stub_router._last_filter_telemetry
        assert stash["intent"] == "unknown"
        assert stash["filtered_backends_count"] == stash["all_backends_count"]

    def test_search_async_emits_one_non_cache_line(
        self, stub_router: AsyncSearchRouter, telemetry_path: Path, monkeypatch
    ) -> None:
        """A real search_async() call emits exactly one cache_hit=False telemetry line."""
        async def fake_search_backend(self, backend, query, limit):
            return []
        monkeypatch.setattr(
            AsyncSearchRouter, "_search_backend_async", fake_search_backend, raising=True
        )

        results = asyncio.run(stub_router.search_async("what is faiss vector", limit=5))
        assert isinstance(results, list)

        rows = _read_lines(telemetry_path)
        assert len(rows) == 1, f"expected 1 telemetry line, got {len(rows)}"
        r = rows[0]
        assert r["cache_hit"] is False
        assert r["intent"] == "informational"
        assert r["all_backends_count"] == len(REAL_BACKEND_NAMES)
        assert r["filtered_backends_count"] < r["all_backends_count"]
        assert r["returned_count"] == len(results)

    def test_cache_hit_emits_skipped_cache_line(
        self, tmp_path: Path, telemetry_path: Path, monkeypatch
    ) -> None:
        """When the cache serves the query, telemetry records cache_hit=True."""
        r = AsyncSearchRouter()
        r._backends = {name: object() for name in REAL_BACKEND_NAMES}
        r._backends_initialized = True
        r.enable_cache = True
        # Prime the cache so the next .get() hits.
        cached_payload = [{"title": "cached hit", "content": "x", "url": None,
                           "source": "test", "score": 0.9, "metadata": {}}]
        r._cache.set("what is faiss", cached_payload, limit=5, backends=None)

        rows_before = len(_read_lines(telemetry_path))
        asyncio.run(r.search_async("what is faiss", limit=5))
        rows = _read_lines(telemetry_path)
        assert len(rows) == rows_before + 1
        assert rows[-1]["cache_hit"] is True
        assert rows[-1]["intent"] == "skipped_cache"
        assert rows[-1]["returned_count"] == 1
