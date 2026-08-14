"""Tests for core.chs.embeddings module."""

from __future__ import annotations

import pytest
import numpy as np


def test_embeddings_module_import():
    """Smoke test: embeddings module can be imported."""
    from core.chs import embeddings

    assert embeddings is not None


def test_get_st_model_returns_transformer():
    """Test _get_st_model returns a SentenceTransformer."""
    from core.chs.embeddings import _get_st_model, _reset_st_model_cache

    _reset_st_model_cache()
    try:
        model = _get_st_model()
        assert model is not None
        assert hasattr(model, "encode")
    finally:
        _reset_st_model_cache()


def test_direct_embed_produces_valid_vectors():
    """Test _direct_embed produces valid float32 vectors of dimension 384."""
    from core.chs.embeddings import (
        EmbedClient,
        _reset_st_model_cache,
        DEFAULT_EMBEDDING_DIM,
    )

    _reset_st_model_cache()
    try:
        client = EmbedClient(daemon_client=None)
        texts = ["hello world", "test sentence"]
        results = client._direct_embed(texts)

        assert len(results) == 2
        for blob in results:
            vec = np.frombuffer(blob, dtype=np.float32)
            assert vec.shape == (DEFAULT_EMBEDDING_DIM,)
            assert np.linalg.norm(vec) > 0.01
    finally:
        _reset_st_model_cache()


def test_embed_texts_falls_back_to_direct_when_no_embed_method():
    """Test embed_texts falls back to _direct_embed when daemon lacks embed_texts."""
    from core.chs.embeddings import EmbedClient, _reset_st_model_cache

    _reset_st_model_cache()
    try:
        class FakeDaemonClient:
            pass

        client = EmbedClient(daemon_client=FakeDaemonClient())
        texts = ["hello world"]
        results = client.embed_texts(texts)

        assert len(results) == 1
        vec = np.frombuffer(results[0], dtype=np.float32)
        assert vec.shape == (384,)
    finally:
        _reset_st_model_cache()


def test_reset_embed_client_singleton():
    """Test reset_embed_client clears the singleton."""
    from core.chs.embeddings import get_embed_client, reset_embed_client

    client1 = get_embed_client()
    reset_embed_client()
    client2 = get_embed_client()
    assert client1 is not client2
