from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
YT_IS_ROOT = Path("P:/packages/yt-is")
for path in (SKILL_ROOT / "scripts", YT_IS_ROOT, YT_IS_ROOT / "scripts"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import csf.cache as cache
import title_bridge
import yt_is_forward_sync
import export_transcripts


def test_fetch_from_cache_returns_transcript_and_video_id(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def match_title(title: str, bridge: dict[str, list[str]]) -> tuple[str, str]:
        assert title == "A cached video"
        assert bridge == {"cached": ["video-id"]}
        return "video-id", "exact"

    monkeypatch.setattr(title_bridge, "match_title", match_title)
    monkeypatch.setattr(
        cache,
        "get_cached_transcript_by_video_id",
        lambda video_id: calls.append(video_id) or SimpleNamespace(transcript="cached transcript"),
    )

    assert yt_is_forward_sync.fetch_from_yt_is_cache(
        {"title": "A cached video"}, {"cached": ["video-id"]}
    ) == ("cached transcript", "video-id")
    assert calls == ["video-id"]


def test_fetch_from_cache_returns_empty_on_cache_miss(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(title_bridge, "match_title", lambda _title, _bridge: ("video-id", "exact"))
    monkeypatch.setattr(cache, "get_cached_transcript_by_video_id", lambda _video_id: None)

    assert yt_is_forward_sync.fetch_from_yt_is_cache(
        {"title": "Not cached"}, {"not-cached": ["video-id"]}
    ) == ("", "")


def test_fetch_from_cache_is_fail_through_on_cache_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(title_bridge, "match_title", lambda _title, _bridge: ("video-id", "exact"))

    def fail(_video_id: str) -> None:
        raise RuntimeError("cache unavailable")

    monkeypatch.setattr(cache, "get_cached_transcript_by_video_id", fail)

    assert yt_is_forward_sync.fetch_from_yt_is_cache(
        {"title": "Cache failure"}, {"cache-failure": ["video-id"]}
    ) == ("", "")


def test_resolve_video_id_uses_title_bridge(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(title_bridge, "match_title", lambda title, bridge: ("video-id", "exact"))

    assert yt_is_forward_sync._resolve_video_id({"title": "A video"}, {}) == "video-id"


def test_empty_title_does_not_query_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    def unexpected(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("empty titles must not query the cache")

    monkeypatch.setattr(cache, "get_cached_transcript_by_video_id", unexpected)
    assert yt_is_forward_sync.fetch_from_yt_is_cache({}, {}) == ("", "")


def test_export_uses_cache_before_notebooklm(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    source = {"id": "source-1", "title": "Cached video", "url": "https://example.test/video"}
    monkeypatch.setattr(export_transcripts, "list_sources", lambda *_args, **_kwargs: [source])
    monkeypatch.setattr(yt_is_forward_sync, "build_bridge_once", lambda: {"cached": ["video-id"]})
    monkeypatch.setattr(
        yt_is_forward_sync,
        "fetch_from_yt_is_cache",
        lambda _source, _bridge: ("cached transcript", "video-id"),
    )
    monkeypatch.setattr(yt_is_forward_sync, "_resolve_video_id", lambda _source, _bridge: "video-id")
    monkeypatch.setattr(cache, "set_cached_transcript", lambda *_args, **_kwargs: None)

    def unexpected_nlm(*_args: object, **_kwargs: object) -> tuple[str, str]:
        raise AssertionError("NotebookLM must not be called after a cache hit")

    monkeypatch.setattr(export_transcripts, "fetch_content", unexpected_nlm)
    monkeypatch.setattr(export_transcripts, "fetch_via_ytdlp", unexpected_nlm)
    monkeypatch.setattr(export_transcripts, "log", lambda *_args, **_kwargs: None)

    result = export_transcripts._export_notebook(
        "notebook-1", "a.hominidae", tmp_path, spacing=0, force=False, limit=None, client=object()
    )

    assert result["exported"] == 1
    assert result["from_cache_count"] == 1
    assert result["cache_hit_count"] == 1
    assert result["cache_miss_count"] == 0
    assert result["cache_unresolved_count"] == 0
    assert result["feed_forward_success_count"] == 1
    assert result["feed_forward_failure_count"] == 0
    assert (tmp_path / "source-1.md").read_text(encoding="utf-8").endswith("cached transcript\n")


def test_export_falls_through_to_notebooklm_on_cache_miss(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = {"id": "source-2", "title": "Uncached video", "url": "https://example.test/video"}
    monkeypatch.setattr(export_transcripts, "list_sources", lambda *_args, **_kwargs: [source])
    monkeypatch.setattr(yt_is_forward_sync, "build_bridge_once", lambda: {})
    monkeypatch.setattr(yt_is_forward_sync, "fetch_from_yt_is_cache", lambda *_args: ("", ""))
    monkeypatch.setattr(yt_is_forward_sync, "_resolve_video_id", lambda *_args: "")
    monkeypatch.setattr(
        export_transcripts,
        "fetch_content",
        lambda *_args, **_kwargs: ("notebooklm transcript", ""),
    )
    monkeypatch.setattr(export_transcripts, "fetch_via_ytdlp", lambda *_args: ("", "unexpected"))
    monkeypatch.setattr(export_transcripts, "log", lambda *_args, **_kwargs: None)

    result = export_transcripts._export_notebook(
        "notebook-1", "a.hominidae", tmp_path, spacing=0, force=False, limit=None, client=object()
    )

    assert result["exported"] == 1
    assert result["from_cache_count"] == 0
    assert result["cache_hit_count"] == 0
    assert result["cache_miss_count"] == 1
    assert result["cache_unresolved_count"] == 0
    assert result["feed_forward_success_count"] == 0
    assert result["feed_forward_failure_count"] == 1
    assert (tmp_path / "source-2.md").read_text(encoding="utf-8").endswith("notebooklm transcript\n")


def test_export_falls_through_to_notebooklm_on_cache_exception(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    source = {"id": "source-3", "title": "Cache error video", "url": "https://example.test/video"}
    monkeypatch.setattr(export_transcripts, "list_sources", lambda *_args, **_kwargs: [source])
    monkeypatch.setattr(yt_is_forward_sync, "build_bridge_once", lambda: {"cache-error": ["video-id"]})

    def fail(*_args: object, **_kwargs: object) -> tuple[str, str]:
        raise RuntimeError("cache unavailable")

    monkeypatch.setattr(yt_is_forward_sync, "fetch_from_yt_is_cache", fail)
    monkeypatch.setattr(yt_is_forward_sync, "_resolve_video_id", lambda *_args: "")
    monkeypatch.setattr(
        export_transcripts,
        "fetch_content",
        lambda *_args, **_kwargs: ("notebooklm transcript", ""),
    )
    monkeypatch.setattr(export_transcripts, "fetch_via_ytdlp", lambda *_args: ("", "unexpected"))
    monkeypatch.setattr(export_transcripts, "log", lambda *_args, **_kwargs: None)

    result = export_transcripts._export_notebook(
        "notebook-1", "a.hominidae", tmp_path, spacing=0, force=False, limit=None, client=object()
    )

    assert result["exported"] == 1
    assert result["from_cache_count"] == 0
    assert (tmp_path / "source-3.md").read_text(encoding="utf-8").endswith("notebooklm transcript\n")
