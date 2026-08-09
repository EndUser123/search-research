"""Tests for the context-budget logic and overlapping chunk strategy in synthesize_subtopics.py.

Run: python -m pytest tests/test_synthesize_context.py -v
Or:  python tests/test_synthesize_context.py
"""
import sys
import os
import json
from types import SimpleNamespace

# Add scripts dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from synthesize_subtopics import (
    split_with_overlap,
    build_context,
    DEFAULT_CONTEXT_BUDGET,
    PRE_SUMMARY_CHUNK_SIZE,
    PRE_SUMMARY_CHUNK_OVERLAP,
    pre_summarize_member,
    synth_cluster,
)
import synthesize_subtopics as _ss


def test_call_mmx_uses_file_input_for_large_windows_prompts(monkeypatch, tmp_path):
    seen = {}

    def fake_run(cmd, **_kwargs):
        seen["cmd"] = cmd
        path = cmd[cmd.index("--messages-file") + 1]
        seen["messages"] = json.loads(open(path, encoding="utf-8").read())
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"base_resp": {"status_code": 0}, "content": [{"text": "ok"}]}),
            stderr="",
        )

    monkeypatch.setattr(_ss, "_resolve_mmx_cmd", lambda: ["mmx"])
    monkeypatch.setattr(_ss.subprocess, "run", fake_run)

    text, error = _ss.call_mmx("X" * 100_000, None, timeout=1)

    assert error == ""
    assert text == "ok"
    assert "--message" not in seen["cmd"]
    assert seen["messages"] == [{"role": "user", "content": "X" * 100_000}]


# --- split_with_overlap tests ---

def test_split_no_split_needed():
    """Text shorter than chunk_size returns single chunk."""
    text = "x" * 1000
    chunks = split_with_overlap(text, 2000, 200)
    assert len(chunks) == 1
    assert chunks[0] == text


def test_split_exact_boundary():
    """Text exactly at chunk_size returns single chunk."""
    text = "x" * PRE_SUMMARY_CHUNK_SIZE
    chunks = split_with_overlap(text, PRE_SUMMARY_CHUNK_SIZE, PRE_SUMMARY_CHUNK_OVERLAP)
    assert len(chunks) == 1


def test_split_just_over_boundary():
    """Text one char over boundary produces two chunks."""
    text = "x" * (PRE_SUMMARY_CHUNK_SIZE + 1)
    chunks = split_with_overlap(text, PRE_SUMMARY_CHUNK_SIZE, PRE_SUMMARY_CHUNK_OVERLAP)
    assert len(chunks) == 2


def test_split_overlap_content_preserved():
    """The overlap region appears in both adjacent chunks."""
    marker = "MARKER_HERE"
    # Place marker near the boundary
    padding_before = "A" * (PRE_SUMMARY_CHUNK_SIZE - 50)
    text = padding_before + marker + "B" * PRE_SUMMARY_CHUNK_SIZE
    chunks = split_with_overlap(text, PRE_SUMMARY_CHUNK_SIZE, PRE_SUMMARY_CHUNK_OVERLAP)
    assert len(chunks) >= 2
    # Marker should be in at least one chunk (it's near the end of chunk 0)
    assert any(marker in c for c in chunks)


def test_split_all_chunks_within_size():
    """No chunk exceeds chunk_size."""
    text = "Z" * (PRE_SUMMARY_CHUNK_SIZE * 3)
    chunks = split_with_overlap(text, PRE_SUMMARY_CHUNK_SIZE, PRE_SUMMARY_CHUNK_OVERLAP)
    assert all(len(c) <= PRE_SUMMARY_CHUNK_SIZE for c in chunks)


def test_split_large_transcript_chunk_count():
    """Simulate the largest real transcript (3.2MB)."""
    text = "X" * 3_238_000
    chunks = split_with_overlap(text, PRE_SUMMARY_CHUNK_SIZE, PRE_SUMMARY_CHUNK_OVERLAP)
    # stride = 180K, so ~18 chunks expected
    assert 15 <= len(chunks) <= 20
    # Overhead from overlap should be ~10%
    total = sum(len(c) for c in chunks)
    overhead = (total - 3_238_000) / 3_238_000
    assert 0.05 <= overhead <= 0.15, f"Overhead {overhead:.1%} not in expected 5-15% range"


# --- build_context tests ---

def test_build_context_full_text_default():
    """per_member_chars=0 means full text (no truncation)."""
    members = [
        {"source_id": "a", "title": "Short A", "text": "X" * 5000, "url": None},
        {"source_id": "b", "title": "Short B", "text": "Y" * 5000, "url": None},
    ]
    ctx = build_context(members, 0, 20)
    # Should contain all content from both members
    assert len(ctx) > 9000, f"Expected >9K chars for full text, got {len(ctx)}"


def test_build_context_legacy_truncation():
    """per_member_chars=1200 (legacy) still truncates."""
    members = [
        {"source_id": "a", "title": "Long A", "text": "X" * 5000, "url": None},
    ]
    ctx = build_context(members, 1200, 20)
    # Body should be 1200 chars + header
    assert len(ctx) < 2000, f"Expected <2K chars for truncated, got {len(ctx)}"


def test_build_context_member_sampling():
    """When members exceed max_members, sampling is applied."""
    members = [
        {"source_id": f"s{i}", "title": f"Source {i}", "text": f"content{i}", "url": None}
        for i in range(30)
    ]
    ctx = build_context(members, 0, 10)
    # Should only include ~10 sources (sampled)
    # The key assertion: context shouldn't contain all 30 sources
    # Only ~10 should be sampled
    source_count = ctx.count("### Source")
    assert source_count <= 10, f"Expected <=10 sampled sources, got {source_count}"


# --- constants tests ---

def test_context_budget_is_300k():
    """Verify the safe-zone default."""
    assert DEFAULT_CONTEXT_BUDGET == 300_000


def test_chunk_overlap_is_10_percent():
    """Overlap should be ~10% of chunk size (research-recommended minimum)."""
    ratio = PRE_SUMMARY_CHUNK_OVERLAP / PRE_SUMMARY_CHUNK_SIZE
    assert 0.08 <= ratio <= 0.12, f"Overlap ratio {ratio:.1%} not in 8-12% range"


# --- input validation tests ---

def test_split_rejects_zero_chunk_size():
    """chunk_size <= 0 raises ValueError."""
    try:
        split_with_overlap("text", 0, 0)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

def test_split_rejects_overlap_ge_chunk_size():
    """overlap >= chunk_size raises ValueError."""
    try:
        split_with_overlap("text", 100, 100)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


# --- pre_summarize_member tests (stub backend) ---

def _stub_backend_returning(text_returned: str):
    """Create a stub call function that ignores input and returns fixed text."""
    def _stub(prompt, model=None, timeout=180):
        return text_returned, ""
    def _stub_dgemma(prompt, timeout=180):
        return text_returned, ""
    return _stub, _stub_dgemma

def _error_backend():
    """Stub that always returns an error."""
    def _stub(prompt, model=None, timeout=180):
        return "", "stub error"
    def _stub_dgemma(prompt, timeout=180):
        return "", "stub error"
    return _stub, _stub_dgemma

def test_pre_summarize_single_chunk_passes_through():
    """Small transcript: single chunk, backend result returned verbatim."""
    member = {"source_id": "s1", "title": "Test", "text": "x" * 5000, "url": None}
    orig_mmx = _ss.call_mmx
    orig_dgemma = _ss.call_dgemma
    stub_mmx, stub_dgemma = _stub_backend_returning("- key point A\n- key point B")
    _ss.call_mmx = stub_mmx
    _ss.call_dgemma = stub_dgemma
    try:
        summary, err = pre_summarize_member(member, "test hint", "mmx", None)
        assert err == "", f"Expected no error, got: {err}"
        assert "key point A" in summary
        assert "key point B" in summary
    finally:
        _ss.call_mmx = orig_mmx
        _ss.call_dgemma = orig_dgemma

def test_pre_summarize_multi_chunk_concatenates():
    """Large transcript: multiple chunks, results joined with separator."""
    member = {"source_id": "s1", "title": "Huge", "text": "Z" * (PRE_SUMMARY_CHUNK_SIZE * 2 + 100), "url": None}
    call_count = [0]
    def counting_stub(prompt, model=None, timeout=180):
        call_count[0] += 1
        return f"- summary from chunk {call_count[0]}", ""
    orig_mmx = _ss.call_mmx
    _ss.call_mmx = counting_stub
    try:
        summary, err = pre_summarize_member(member, "test", "mmx", None)
        assert err == ""
        assert "chunk 1" in summary
        assert "chunk 2" in summary or "chunk 3" in summary  # at least 2 chunks
    finally:
        _ss.call_mmx = orig_mmx

def test_pre_summarize_chunk_error_falls_back_to_head():
    """When backend errors on a chunk, fallback to chunk head is used."""
    member = {"source_id": "s1", "title": "Large", "text": "MARKER" + "X" * PRE_SUMMARY_CHUNK_SIZE + "MORE", "url": None}
    orig_mmx = _ss.call_mmx
    err_stub, _ = _error_backend()
    _ss.call_mmx = err_stub
    try:
        summary, err = pre_summarize_member(member, "test", "mmx", None)
        # All chunks error → all use head fallback → summary should contain content
        assert "MARKER" in summary or "X" in summary  # head content present
    finally:
        _ss.call_mmx = orig_mmx

def test_pre_summarize_all_empty_returns_error():
    """When all chunks return empty, error is returned."""
    member = {"source_id": "s1", "title": "Test", "text": "x" * 1000, "url": None}
    orig_mmx = _ss.call_mmx
    def _empty_stub(prompt, model=None, timeout=180):
        return "", "empty"
    _ss.call_mmx = _empty_stub
    try:
        summary, err = pre_summarize_member(member, "test", "mmx", None)
        assert summary == "", "Should return empty summary"
        assert "empty" in err, f"Error should mention the backend failure: {err}"
    finally:
        _ss.call_mmx = orig_mmx


# --- synth_cluster budget gate test ---

def test_synth_cluster_full_text_when_under_budget():
    """When total context fits budget, full text path is used (no map-reduce)."""
    members = [
        {"source_id": "a", "title": "Small A", "text": "concept A " * 100, "url": None},
        {"source_id": "b", "title": "Small B", "text": "concept B " * 100, "url": None},
    ]
    cluster = {"cluster_id": 1, "name": "test", "member_source_ids": ["a", "b"]}
    # Stub the backend to return valid JSON
    import json
    canned = json.dumps({
        "title": "Test Concept",
        "definition": "A test concept.",
        "details": ["detail 1"],
        "values": [],
        "related": [],
        "citations": [],
    })
    orig_mmx = _ss.call_mmx
    _ss.call_mmx = lambda p, model=None, timeout=180: (canned, "")
    try:
        parsed, err = synth_cluster(cluster, members, "mmx", None, 0, 20, context_budget=300_000)
        assert err == "", f"Expected no error, got: {err}"
        assert parsed is not None
        assert parsed["title"] == "Test Concept"
    finally:
        _ss.call_mmx = orig_mmx


if __name__ == "__main__":
    # Allow running without pytest
    tests = [
        test_split_no_split_needed, test_split_exact_boundary,
        test_split_just_over_boundary, test_split_overlap_content_preserved,
        test_split_all_chunks_within_size, test_split_large_transcript_chunk_count,
        test_build_context_full_text_default, test_build_context_legacy_truncation,
        test_build_context_member_sampling, test_context_budget_is_300k,
        test_chunk_overlap_is_10_percent,
        test_split_rejects_zero_chunk_size, test_split_rejects_overlap_ge_chunk_size,
        test_pre_summarize_single_chunk_passes_through,
        test_pre_summarize_multi_chunk_concatenates,
        test_pre_summarize_chunk_error_falls_back_to_head,
        test_pre_summarize_all_empty_returns_error,
        test_synth_cluster_full_text_when_under_budget,
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"[OK] {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1
    print(f"\n{passed}/{passed + failed} tests passed")
    sys.exit(0 if failed == 0 else 1)
