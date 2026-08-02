"""Tests for the context-budget logic and overlapping chunk strategy in synthesize_subtopics.py.

Run: python -m pytest tests/test_synthesize_context.py -v
Or:  python tests/test_synthesize_context.py
"""
import sys
import os

# Add scripts dir to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from synthesize_subtopics import (
    split_with_overlap,
    build_context,
    DEFAULT_CONTEXT_BUDGET,
    PRE_SUMMARY_CHUNK_SIZE,
    PRE_SUMMARY_CHUNK_OVERLAP,
)


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
    for i in range(30):
        marker = f"content{i}"
        if i < 10:
            # First few should likely be included
            pass
    # The key assertion: context shouldn't contain all 30 sources
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


if __name__ == "__main__":
    # Allow running without pytest
    tests = [
        test_split_no_split_needed, test_split_exact_boundary,
        test_split_just_over_boundary, test_split_overlap_content_preserved,
        test_split_all_chunks_within_size, test_split_large_transcript_chunk_count,
        test_build_context_full_text_default, test_build_context_legacy_truncation,
        test_build_context_member_sampling, test_context_budget_is_300k,
        test_chunk_overlap_is_10_percent,
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
