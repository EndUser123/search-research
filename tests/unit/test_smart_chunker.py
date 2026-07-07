"""Tests for SmartChunker content-addressed chunk identity (ADR-002 + KB durability).

Covers:
- chunk() backward compatibility: full coverage, overlap behavior
- chunk_with_metadata(): stable IDs across rebuilds, ID sensitivity to
  doc_id/text changes, span-text consistency, provenance metadata
"""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

# Load the module directly by path: the chunker is dependency-free, and this
# avoids importing the full `core` package (heavy, version-sensitive imports).
_MOD_PATH = Path(__file__).parents[2] / "core" / "chunking" / "smart_chunker.py"
_spec = importlib.util.spec_from_file_location("smart_chunker_under_test", _MOD_PATH)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

CHUNKER_NAME = _mod.CHUNKER_NAME
CHUNKER_VERSION = _mod.CHUNKER_VERSION
SmartChunker = _mod.SmartChunker

DOC = "\n\n".join(
    f"## Section {i}\n\n" + ("word " * 300).strip() for i in range(8)
)


def test_chunk_covers_full_text_no_overlap():
    chunker = SmartChunker(overlap=False)
    chunks = chunker.chunk(DOC)
    assert len(chunks) > 1
    assert "".join(chunks) == DOC


def test_chunk_overlap_repeats_boundary_text():
    chunker = SmartChunker(overlap=True)
    chunks = chunker.chunk(DOC)
    assert len(chunks) > 1
    # With overlap, the tail of chunk N reappears at the head of chunk N+1
    overlap_chars = int(SmartChunker.TARGET_TOKENS * SmartChunker.OVERLAP_RATIO)
    for prev, nxt in zip(chunks, chunks[1:]):
        assert prev[-overlap_chars:] == nxt[:overlap_chars]


def test_empty_text_yields_no_chunks():
    chunker = SmartChunker()
    assert chunker.chunk("") == []
    assert chunker.chunk_with_metadata("", doc_id="d") == []


def test_metadata_matches_plain_chunks():
    chunker = SmartChunker()
    plain = chunker.chunk(DOC)
    records = chunker.chunk_with_metadata(DOC, doc_id="doc-1")
    assert [r["text"] for r in records] == plain
    for r in records:
        assert DOC[r["char_start"]:r["char_end"]] == r["text"]


def test_chunk_ids_stable_across_rebuilds():
    chunker = SmartChunker()
    ids_a = [r["chunk_id"] for r in chunker.chunk_with_metadata(DOC, doc_id="doc-1")]
    ids_b = [r["chunk_id"] for r in SmartChunker().chunk_with_metadata(DOC, doc_id="doc-1")]
    assert ids_a == ids_b
    assert len(set(ids_a)) == len(ids_a)  # unique within document


def test_chunk_ids_change_with_doc_id():
    chunker = SmartChunker()
    ids_a = {r["chunk_id"] for r in chunker.chunk_with_metadata(DOC, doc_id="doc-1")}
    ids_b = {r["chunk_id"] for r in chunker.chunk_with_metadata(DOC, doc_id="doc-2")}
    assert ids_a.isdisjoint(ids_b)


def test_chunk_ids_change_when_text_changes():
    chunker = SmartChunker()
    before = [r["chunk_id"] for r in chunker.chunk_with_metadata(DOC, doc_id="d")]
    mutated = DOC.replace("Section 7", "Section 7 CHANGED", 1)
    after = [r["chunk_id"] for r in chunker.chunk_with_metadata(mutated, doc_id="d")]
    assert before != after
    # Early chunks (before the mutation point) keep their IDs
    assert before[0] == after[0]


def test_chunk_id_derivation_is_documented_formula():
    chunker = SmartChunker()
    rec = chunker.chunk_with_metadata(DOC, doc_id="doc-1")[0]
    text_sha = hashlib.sha256(rec["text"].encode("utf-8")).hexdigest()
    expected = hashlib.sha256(
        f"doc-1|{rec['char_start']}|{rec['char_end']}|{text_sha}".encode("utf-8")
    ).hexdigest()
    assert rec["text_sha256"] == text_sha
    assert rec["chunk_id"] == expected


def test_provenance_metadata_present():
    chunker = SmartChunker(overlap=False)
    rec = chunker.chunk_with_metadata(DOC, doc_id="d")[0]
    assert rec["chunker_name"] == CHUNKER_NAME
    assert rec["chunker_version"] == CHUNKER_VERSION
    assert rec["chunker_params"]["overlap"] is False
    assert rec["chunker_params"]["target_tokens"] == SmartChunker.TARGET_TOKENS
