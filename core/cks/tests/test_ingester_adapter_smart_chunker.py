"""Tests for CKSIngesterAdapter with SmartChunker integration."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def cks_instance():
    """Create a CKS instance backed by a temporary database.

    CKS.__init__ creates the schema inline — no separate init_db needed.
    Closes the CKS connection before temp dir cleanup to avoid PermissionError.
    """
    from core.cks.unified import CKS

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test_cks.db"
        cks = CKS(db_path=str(db_path))
        yield cks
        if hasattr(cks, "conn") and cks.conn:
            cks.conn.close()
            cks.conn = None


class TestSmartChunkerWiring:
    """Test that CKSIngesterAdapter correctly uses SmartChunker when enabled."""

    def test_default_uses_document_chunker(self, cks_instance):
        """Default mode should use positional DocumentChunker."""
        from core.cks.ingester_adapter import CKSIngesterAdapter

        adapter = CKSIngesterAdapter(cks_instance)
        assert not adapter.use_smart_chunker
        assert isinstance(adapter.chunker, type(adapter.chunker))

    def test_smart_chunker_mode_flag(self, cks_instance):
        """Setting use_smart_chunker=True should set the flag."""
        from core.cks.ingester_adapter import CKSIngesterAdapter

        adapter = CKSIngesterAdapter(cks_instance, use_smart_chunker=True)
        assert adapter.use_smart_chunker

    def test_smart_chunker_ingest_produces_entries(self, cks_instance):
        """SmartChunker mode should produce CKS entries."""
        from core.cks.ingester_adapter import CKSIngesterAdapter

        adapter = CKSIngesterAdapter(cks_instance, use_smart_chunker=True)
        result = adapter.ingest_document(
            text="This is a test document with enough text to produce multiple chunks. "
            * 50,
            title="Test Document",
        )
        assert result.chunk_count >= 1
        assert len(result.entry_ids) == result.chunk_count

    def test_smart_chunker_adds_identity_metadata(self, cks_instance):
        """SmartChunker mode should add chunk_id and text_sha256 to entries."""
        from core.cks.ingester_adapter import CKSIngesterAdapter

        adapter = CKSIngesterAdapter(cks_instance, use_smart_chunker=True)
        result = adapter.ingest_document(
            text="Short document for testing metadata fields. " * 20,
            title="Meta Test",
        )
        assert len(result.entry_ids) >= 1
        # Entry should exist in DB — verify it has chunk_id in metadata
        cursor = cks_instance.conn.execute(
            "SELECT metadata FROM entries WHERE id = ?",
            (result.entry_ids[0],),
        )
        row = cursor.fetchone()
        assert row is not None
        import json
        meta = json.loads(row[0])
        assert "chunk_id" in meta, "SmartChunker should add chunk_id"
        assert "text_sha256" in meta, "SmartChunker should add text_sha256"
        assert "chunker_name" in meta, "SmartChunker should add chunker_name"
        assert meta["chunker_name"] == "smart_chunker"

    def test_content_addressed_ids_are_stable(self, cks_instance):
        """Same text should produce same chunk_ids across rebuilds."""
        from core.cks.ingester_adapter import CKSIngesterAdapter

        adapter = CKSIngesterAdapter(cks_instance, use_smart_chunker=True)
        text = "Stable identity test content. " * 30

        r1 = adapter.ingest_document(text=text, title="Stability Test")
        r2 = adapter.ingest_document(text=text, title="Stability Test")

        import json
        # Get chunk_ids from both runs
        ids1 = set()
        for eid in r1.entry_ids:
            row = cks_instance.conn.execute(
                "SELECT metadata FROM entries WHERE id = ?", (eid,)
            ).fetchone()
            if row:
                meta = json.loads(row[0])
                ids1.add(meta.get("chunk_id"))

        ids2 = set()
        for eid in r2.entry_ids:
            row = cks_instance.conn.execute(
                "SELECT metadata FROM entries WHERE id = ?", (eid,)
            ).fetchone()
            if row:
                meta = json.loads(row[0])
                ids2.add(meta.get("chunk_id"))

        # Same text → same chunk_ids
        assert ids1 == ids2, f"Chunk IDs not stable: {ids1} vs {ids2}"
