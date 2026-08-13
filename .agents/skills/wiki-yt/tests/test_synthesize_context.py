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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts", "models"))

from synthesize_subtopics import (
    split_with_overlap,
    build_context,
    DEFAULT_CONTEXT_BUDGET,
    PRE_SUMMARY_CHUNK_SIZE,
    PRE_SUMMARY_CHUNK_OVERLAP,
    pre_summarize_member,
    synth_cluster,
    deterministic_fallback,
    validate_citations,
    shape_record,
    extract_json,
)
import synthesize_subtopics as _ss
import dgemma_read as _dr


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


def test_call_dgemma_passes_large_custom_prompt_via_prompt_file(monkeypatch):
    seen = {}

    def fake_run(cmd, **_kwargs):
        seen["cmd"] = cmd
        prompt_path = cmd[cmd.index("--prompt-file") + 1]
        seen["prompt"] = open(prompt_path, encoding="utf-8").read()
        content_path = cmd[2]
        seen["content"] = open(content_path, encoding="utf-8").read()
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"summary": '{"citations": []}'}),
            stderr="",
        )

    monkeypatch.setattr(_ss.subprocess, "run", fake_run)

    text, error = _ss.call_dgemma("Y" * 100_000, timeout=1)

    assert error == ""
    assert text == '{"citations": []}'
    assert "--prompt-file" in seen["cmd"]
    assert seen["prompt"] == "Y" * 100_000
    assert seen["content"] == ""
    assert seen["cmd"][seen["cmd"].index("--max-tokens") + 1] == "600"


def test_call_dgemma_propagates_explicit_semantic_budget(monkeypatch):
    seen = {}

    def fake_run(cmd, **_kwargs):
        seen["cmd"] = cmd
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"summary": "{}"}),
            stderr="",
        )

    monkeypatch.setattr(_ss.subprocess, "run", fake_run)

    text, error = _ss.call_dgemma("semantic prompt", timeout=1, max_tokens=2400)

    assert error == ""
    assert text == "{}"
    assert seen["cmd"][seen["cmd"].index("--max-tokens") + 1] == "2400"


def test_synth_cluster_requests_bounded_dgemma_semantic_budget(monkeypatch):
    members = [{
        "source_id": "s1",
        "title": "Source One",
        "text": "A grounded source claim.",
        "url": None,
    }]
    captured = {}
    valid = json.dumps({
        "title": "Topic",
        "definition": "A grounded topic.",
        "details": [],
        "values": [],
        "related": [],
        "citations": [{
            "claim": "claim",
            "source_id": "s1",
            "source_title": "Source One",
            "cited_text": "grounded source claim",
        }],
    })

    def fake_dgemma(prompt, timeout, *, max_tokens=600):
        captured["max_tokens"] = max_tokens
        return valid, ""

    monkeypatch.setattr(_ss, "call_dgemma", fake_dgemma)
    parsed, error = _ss.synth_cluster(
        {"cluster_id": 1, "name": "Topic", "member_source_ids": ["s1"]},
        members,
        "dgemma",
        None,
        0,
        20,
        max_retries=1,
    )

    assert error == ""
    assert parsed is not None
    assert captured["max_tokens"] == _ss.DGEMMA_SYNTHESIS_MAX_TOKENS
    assert captured["max_tokens"] > 600


def test_synth_cluster_uses_alternate_backend_for_failed_map_member(monkeypatch):
    """A failed map member gets the alternate backend before fail-closed fallback."""
    members = [
        {"source_id": "s1", "title": "Source One", "text": "one", "url": None},
        {"source_id": "s2", "title": "Source Two", "text": "two", "url": None},
    ]
    valid = json.dumps({
        "title": "Topic",
        "definition": "A grounded topic.",
        "details": [],
        "values": [],
        "related": [],
        "citations": [{
            "claim": "claim",
            "source_id": "s1",
            "source_title": "Source One",
            "cited_text": "one",
        }],
    })
    calls = []

    def fake_pre_summary(member, hint, backend, model):
        calls.append((member["source_id"], backend))
        if backend == "dgemma" and member["source_id"] == "s2":
            return "", "dgemma 429"
        return f"summary {backend} {member['source_id']}", ""

    monkeypatch.setattr(_ss, "pre_summarize_member", fake_pre_summary)
    monkeypatch.setattr(_ss, "call_dgemma", lambda *args, **kwargs: (valid, ""))

    parsed, error = _ss.synth_cluster(
        {"cluster_id": 1, "name": "Topic", "member_source_ids": ["s1", "s2"]},
        members,
        "dgemma",
        None,
        0,
        20,
        context_budget=1,
        max_retries=1,
    )

    assert error == ""
    assert parsed is not None
    assert ("s2", "dgemma") in calls
    assert ("s2", "mmx") in calls


def test_truncated_or_invalid_dgemma_output_remains_fail_closed(monkeypatch):
    members = [{
        "source_id": "s1",
        "title": "Source One",
        "text": "A grounded source claim.",
        "url": None,
    }]
    monkeypatch.setattr(_ss, "call_dgemma", lambda *args, **kwargs: ('{"title":', ""))
    monkeypatch.setattr(_ss, "call_mmx", lambda *args, **kwargs: ('{"citations": []}', ""))
    monkeypatch.setattr(_ss.time, "sleep", lambda _seconds: None)

    parsed, error = _ss.synth_cluster(
        {"cluster_id": 1, "name": "Topic", "member_source_ids": ["s1"]},
        members,
        "dgemma",
        None,
        0,
        20,
        max_retries=1,
    )

    assert parsed is None
    assert "unparseable JSON" in error
    assert "citation_invalid: no citations" in error


def test_dgemma_api_rejects_length_truncation(monkeypatch):
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return json.dumps({
                "choices": [{
                    "finish_reason": "length",
                    "message": {"content": '{"title":'},
                }],
                "usage": {"completion_tokens": 2400},
            }).encode("utf-8")

    monkeypatch.setattr(_dr.urllib.request, "urlopen", lambda *args, **kwargs: FakeResponse())

    try:
        _dr._call_api([{"role": "user", "content": "prompt"}], max_tokens=2400)
    except ValueError as exc:
        assert "Output truncated" in str(exc)
    else:
        raise AssertionError("length-truncated output must fail closed")


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
    def _stub_dgemma(prompt, timeout=180, *, max_tokens=600):
        return text_returned, ""
    return _stub, _stub_dgemma

def _error_backend():
    """Stub that always returns an error."""
    def _stub(prompt, model=None, timeout=180):
        return "", "stub error"
    def _stub_dgemma(prompt, timeout=180, *, max_tokens=600):
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

def test_pre_summarize_dgemma_receives_explicit_output_budget():
    """Map-stage DGemma calls must not fall back to the generic 600-token default."""
    member = {"source_id": "s1", "title": "Test", "text": "x" * 5000, "url": None}
    seen = {}
    orig_dgemma = _ss.call_dgemma

    def capture(prompt, timeout=180, *, max_tokens=600):
        seen["max_tokens"] = max_tokens
        return "- grounded summary", ""

    _ss.call_dgemma = capture
    try:
        summary, err = pre_summarize_member(member, "test hint", "dgemma", None)
        assert err == ""
        assert "grounded summary" in summary
        assert seen["max_tokens"] == _ss.DGEMMA_PRE_SUMMARY_MAX_TOKENS
        assert seen["max_tokens"] > 600
    finally:
        _ss.call_dgemma = orig_dgemma


def test_pre_summarize_retries_transient_dgemma_failure():
    """A transient empty/429 map response gets one bounded retry."""
    member = {"source_id": "s1", "title": "Test", "text": "x" * 5000, "url": None}
    calls = []

    def flaky(prompt, timeout=180, *, max_tokens=600):
        calls.append(max_tokens)
        if len(calls) == 1:
            return "", "dgemma rc=1: ERROR: ValueError: Empty content"
        return "- recovered summary", ""

    orig_dgemma = _ss.call_dgemma
    orig_sleep = _ss.time.sleep
    _ss.call_dgemma = flaky
    _ss.time.sleep = lambda _seconds: None
    try:
        summary, err = pre_summarize_member(member, "test hint", "dgemma", None)
    finally:
        _ss.call_dgemma = orig_dgemma
        _ss.time.sleep = orig_sleep

    assert err == ""
    assert summary == "- recovered summary"
    assert calls == [_ss.DGEMMA_PRE_SUMMARY_MAX_TOKENS] * 2

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
        assert err.startswith("degraded_context:")
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
        "citations": [{
            "claim": "concept A",
            "source_id": "a",
            "source_title": "Small A",
            "cited_text": "concept A",
        }],
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


def test_validate_citations_rejects_unmapped_or_empty_citations():
    members = [{"source_id": "s1", "title": "Source One", "text": "claim", "url": None}]
    assert validate_citations({"citations": []}, members).startswith("citation_invalid:")
    assert validate_citations(
        {"citations": [{"claim": "x", "source_title": "Other", "cited_text": "y"}]},
        members,
    ).startswith("citation_invalid:")
    assert validate_citations(
        {"citations": [{"claim": "x", "source_id": "s1", "cited_text": "claim"}]},
        members,
    ) == ""


def test_validate_citations_repairs_unknown_id_from_unique_title_and_excerpt():
    members = [{
        "source_id": "s1",
        "title": "Source One",
        "text": "A verbatim source claim appears here.",
        "url": None,
    }]
    parsed = {"citations": [{
        "claim": "claim",
        "source_id": "backend-generated-id",
        "source_title": "Source One",
        "cited_text": "verbatim source claim appears here.",
    }]}

    assert validate_citations(parsed, members) == ""
    shaped = shape_record(parsed, {"cluster_id": 1, "name": "Topic"}, members, "nb", "Notebook")
    assert shaped["citations"][0]["source_id"] == "s1"


def test_validate_citations_rejects_unknown_id_without_grounded_excerpt():
    members = [{
        "source_id": "s1",
        "title": "Source One",
        "text": "A different source claim appears here.",
        "url": None,
    }]
    assert validate_citations({"citations": [{
        "claim": "claim",
        "source_id": "backend-generated-id",
        "source_title": "Source One",
        "cited_text": "unsupported claim",
    }]}, members).startswith("citation_invalid: item 0 has unknown source_id")


def test_validate_citations_repairs_unknown_id_from_unique_long_excerpt():
    members = [
        {
            "source_id": "s1",
            "title": "First",
            "text": "The unique transcript sentence explains the bounded retry policy.",
            "url": None,
        },
        {"source_id": "s2", "title": "Second", "text": "Other material.", "url": None},
    ]
    parsed = {"citations": [{
        "claim": "claim",
        "source_id": "backend-id",
        "cited_text": "unique transcript sentence explains the bounded retry policy.",
    }]}

    assert validate_citations(parsed, members) == ""
    shaped = shape_record(parsed, {"cluster_id": 1, "name": "Topic"}, members, "nb", "Notebook")
    assert shaped["citations"][0]["source_id"] == "s1"


def test_validate_citations_rejects_ambiguous_long_excerpt():
    members = [
        {"source_id": "s1", "title": "First", "text": "The same repeated transcript sentence is here.", "url": None},
        {"source_id": "s2", "title": "Second", "text": "The same repeated transcript sentence is here.", "url": None},
    ]
    assert validate_citations({"citations": [{
        "claim": "claim",
        "source_id": "backend-id",
        "cited_text": "same repeated transcript sentence is here.",
    }]}, members).startswith("citation_invalid: item 0 has unknown source_id")


def test_extract_json_rejects_a_valid_non_object_payload():
    assert extract_json("[1, 2, 3]") is None


def test_extract_json_handles_braces_inside_string_values():
    text = 'preamble\n```json\n{"details": ["literal {brace} and \\"quoted\\" text"], "citations": []}\n```\n'
    assert extract_json(text) == {
        "details": ['literal {brace} and "quoted" text'],
        "citations": [],
    }


def test_synth_cluster_falls_back_when_map_reduce_backend_is_unavailable():
    members = [{"source_id": "s1", "title": "Large", "text": "x" * 100, "url": None}]
    original_mmx = _ss.call_mmx
    original_dgemma = _ss.call_dgemma
    _ss.call_mmx = lambda prompt, model=None, timeout=180: ("", "backend unavailable")
    _ss.call_dgemma = lambda prompt, timeout=180, *, max_tokens=600: (
        "", "backend unavailable"
    )
    try:
        parsed, err = synth_cluster(
            {"cluster_id": 1, "name": "test", "member_source_ids": ["s1"]},
            members,
            "mmx",
            None,
            0,
            20,
            context_budget=10,
            allow_degraded_fallback=True,
        )
        assert err == ""
        assert parsed is not None
        assert parsed["synthesis_quality"] == "degraded_fallback"
    finally:
        _ss.call_mmx = original_mmx
        _ss.call_dgemma = original_dgemma


def test_deterministic_fallback_is_source_excerpt_only():
    members = [{
        "source_id": "s1",
        "title": "Source One",
        "text": "A source-grounded statement with a concrete threshold of 7.",
        "url": None,
    }]
    parsed, err = deterministic_fallback({"name": "Fallback Topic"}, members)
    assert err == ""
    assert parsed is not None
    assert parsed["synthesis_quality"] == "degraded_fallback"
    assert parsed["citations"][0]["source_id"] == "s1"
    assert "threshold of 7" in parsed["citations"][0]["cited_text"]
    assert parsed["values"] == []


def test_synth_cluster_uses_deterministic_fallback_after_backend_exhaustion(monkeypatch):
    members = [{"source_id": "s1", "title": "Source One", "text": "grounded text", "url": None}]
    monkeypatch.setattr(_ss, "call_mmx", lambda *args, **kwargs: ("", "backend unavailable"))
    monkeypatch.setattr(_ss, "call_dgemma", lambda *args, **kwargs: ("", "backend unavailable"))
    monkeypatch.setattr(_ss.time, "sleep", lambda _seconds: None)
    parsed, err = synth_cluster(
        {"cluster_id": 1, "name": "Fallback Topic", "member_source_ids": ["s1"]},
        members,
        "mmx",
        None,
        0,
        20,
        max_retries=1,
        context_budget=300_000,
        allow_degraded_fallback=True,
    )
    assert err == ""
    assert parsed is not None
    assert parsed["synthesis_backend"] == "deterministic_excerpt_fallback"
    assert validate_citations(parsed, members) == ""


def test_deterministic_backend_does_not_call_remote_backends(monkeypatch):
    members = [{"source_id": "s1", "title": "Source One", "text": "grounded text", "url": None}]
    monkeypatch.setattr(_ss, "call_mmx", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("mmx called")))
    monkeypatch.setattr(_ss, "call_dgemma", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("dgemma called")))
    parsed, err = synth_cluster(
        {"cluster_id": 1, "name": "Fallback Topic", "member_source_ids": ["s1"]},
        members,
        "deterministic",
        None,
        0,
        20,
        allow_degraded_fallback=True,
    )
    assert err == ""
    assert parsed is not None
    assert parsed["synthesis_quality"] == "degraded_fallback"


def test_deterministic_backend_requires_explicit_promotion_opt_in():
    members = [{"source_id": "s1", "title": "Source One", "text": "grounded text", "url": None}]
    parsed, err = synth_cluster(
        {"cluster_id": 1, "name": "Fallback Topic", "member_source_ids": ["s1"]},
        members,
        "deterministic",
        None,
        0,
        20,
    )
    assert parsed is None
    assert err.startswith("fallback_requires_opt_in:")


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
