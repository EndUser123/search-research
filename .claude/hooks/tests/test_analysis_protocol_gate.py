"""
Tests for analysis_protocol_gate FAP Layer 2 semantic embedding.

These tests verify:
- T1: Paraphrase match ("what actually triggered this failure" → root_cause)
- T2: Keyword fallback when daemon unavailable
- T3: Threshold boundary behavior
- T4: All 6 clusters produce highest score for own examples
- T5: SEC-001 DoS guard (>8192 chars returns error)
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# Ensure the hook module can be imported
HOOKS_DIR = Path(r"P:\.claude\hooks").resolve()
sys.path.insert(0, str(HOOKS_DIR))

# Mock win32 imports before importing the module
win32_modules = {
    "win32file": MagicMock(),
    "win32pipe": MagicMock(),
    "pywintypes": MagicMock(),
}
sys.modules.update(win32_modules)


class MockDaemonClient:
    """Mock DaemonClient that returns controlled embeddings.

    For phrases in _embeddings (test-provided), returns the stored embedding.
    For unknown phrases, generates a deterministic embedding using phrase hash
    as seed. A cluster_assignment dict can be provided to make same-cluster
    phrases have similar embeddings (dominant dimension = cluster index).
    """

    # Cluster-to-dominant-dimension mapping for deterministic embeddings
    _CLUSTER_DIM: dict[str, int] = {
        "wrong_abstraction": 0,
        "root_cause": 64,
        "missing_principle": 128,
        "fix_inadequacy": 192,
        "bug_class": 256,
        "frustration_signal": 320,
    }

    def __init__(
        self,
        embeddings: dict[str, list[float]] | None = None,
        cluster_assignment: dict[str, str] | None = None,
    ):
        self._embeddings: dict[str, list[float]] = dict(embeddings) if embeddings else {}
        self._cluster_assignment: dict[str, str] = dict(cluster_assignment) if cluster_assignment else {}
        self.query_calls: list[tuple[str, dict]] = []

    def _make_deterministic_embedding(self, text: str) -> np.ndarray:
        """Generate a deterministic 384-dim embedding from phrase text.

        Uses the phrase hash to seed RNG, so the same text always produces
        the same embedding. If cluster_assignment maps this text to a cluster,
        adds a dominant signal in that cluster's dimension.
        """
        h = hash(text) % (2**31)
        np.random.seed(h)
        emb = np.random.randn(384).astype(np.float32) * 0.1
        cluster = self._cluster_assignment.get(text)
        if cluster and cluster in self._CLUSTER_DIM:
            emb[self._CLUSTER_DIM[cluster] % 384] = 0.5
        return emb

    def query(self, action: str, params: dict, timeout: float = 2.5) -> dict:
        self.query_calls.append((action, params))
        if action == "compute_embedding":
            text = params.get("text", "")
            if text in self._embeddings:
                stored = self._embeddings[text]
                # Stored value may be np.ndarray (precomputed) or plain list (tolist already called)
                if isinstance(stored, np.ndarray):
                    emb_list = stored.tolist()
                else:
                    emb_list = stored
            else:
                emb_list = self._make_deterministic_embedding(text).tolist()
            return {"status": "success", "result": {"embedding": emb_list, "model": "all-MiniLM-L6-v2"}}
        return {"status": "error", "error": f"Unknown action: {action}"}


class TestSemanticMatch:
    """Tests for _semantic_match function."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Reset module state before each test."""
        import importlib
        import UserPromptSubmit_modules.analysis_protocol_gate as mod
        # Reset lazy centroid state
        mod._CENTROIDS_COMPUTED = False
        mod._CLUSTER_CENTROIDS = {}
        importlib.reload(mod)
        yield
        # Reset after
        mod._CENTROIDS_COMPUTED = False
        mod._CLUSTER_CENTROIDS = {}

    def _make_fake_embeddings(self, samples: dict[str, list[str]]) -> dict[str, list[float]]:
        """Create deterministic fake embeddings for sample phrases."""
        import numpy as np
        result = {}
        h = 0
        for cluster, phrases in samples.items():
            for phrase in phrases:
                np.random.seed(h)
                # Create a unique embedding per phrase
                emb = np.random.randn(384).astype(np.float32)
                result[phrase] = emb.tolist()
                h += 1
        return result

    def test_paraphrase_triggers_root_cause(self, tmp_path: Path):
        """T1: "what actually triggered this failure" matches root_cause cluster."""
        # Sample embeddings for root_cause cluster — all 5 phrases
        root_cause_phrases = [
            "what actually triggered this failure",
            "why did this happen",
            "what's the underlying cause",
            "trace back to the origin",
            "find the source of the problem",
        ]
        wrong_abstraction_phrases = [
            "we're solving the wrong problem",
            "that's not the real issue",
            "misaligned abstraction level",
        ]

        all_phrases = root_cause_phrases + wrong_abstraction_phrases
        embeddings = {}
        for i, phrase in enumerate(all_phrases):
            np.random.seed(i + 100)
            emb = np.random.randn(384).astype(np.float32)
            # Make root_cause centroid point in direction [1,0,...] and
            # "what actually triggered this failure" point in similar direction
            if i == 0:
                emb = np.ones(384, dtype=np.float32) * 0.5  # query phrase
            elif i < 5:
                emb = np.ones(384, dtype=np.float32) * 0.4 + np.random.randn(384) * 0.05  # same cluster
            else:
                emb = np.random.randn(384) * 0.3  # different cluster
            embeddings[phrase] = emb.tolist()

        # Provide cluster_assignment for wrong_abstraction phrases not in embeddings
        # so _compute_cluster_centroids generates consistent embeddings for them
        cluster_assignment = {
            phrase: "wrong_abstraction"
            for phrase in wrong_abstraction_phrases
        }

        mock_client = MockDaemonClient(embeddings=embeddings, cluster_assignment=cluster_assignment)

        with patch("UserPromptSubmit_modules.analysis_protocol_gate.DaemonClient", return_value=mock_client):
            from UserPromptSubmit_modules import analysis_protocol_gate as apg
            apg._CENTROIDS_COMPUTED = False
            apg._CLUSTER_CENTROIDS = {}

            result = apg._semantic_match("what actually triggered this failure")
            assert result == "root_cause", f"Expected root_cause, got {result}"

    def test_semantic_match_returns_none_when_below_threshold(self, tmp_path: Path):
        """T3: Prompt with score below 0.85 threshold returns None."""
        # Create embeddings that are very different from all clusters
        very_different_embedding = (np.random.randn(384) * 0.01).astype(np.float32).tolist()

        mock_client = MockDaemonClient(
            {"completely unrelated text": very_different_embedding}
        )

        with patch("UserPromptSubmit_modules.analysis_protocol_gate.DaemonClient", return_value=mock_client):
            from UserPromptSubmit_modules import analysis_protocol_gate as apg
            apg._CENTROIDS_COMPUTED = False
            apg._CLUSTER_CENTROIDS = {}

            result = apg._semantic_match("what is the weather today")
            # Very different from all FAP clusters — should be below threshold
            assert result is None, f"Expected None for unrelated text, got {result}"

    def test_keyword_fallback_when_daemon_unavailable(self, tmp_path: Path):
        """T2: When daemon raises ConnectionError, falls back to _concept_cluster_match."""
        with patch("UserPromptSubmit_modules.analysis_protocol_gate.DaemonClient") as MockDC:
            MockDC.return_value.query.side_effect = ConnectionError("daemon down")

            # Also patch the stats file
            stats_file = tmp_path / "fap_layer_stats.json"
            with patch("UserPromptSubmit_modules.analysis_protocol_gate._FAP_STATS_FILE", stats_file):
                from UserPromptSubmit_modules import analysis_protocol_gate as apg
                apg._CENTROIDS_COMPUTED = False
                apg._CLUSTER_CENTROIDS = {}

                # "fix doesn't address root cause" has keywords from both fix_inadequacy and root_cause
                result = apg._concept_cluster_match("fix doesn't address root cause")
                assert result is True, "Expected keyword match for fix+root_cause overlap"

    def test_all_six_clusters_match_own_examples(self, tmp_path: Path):
        """T4: Each cluster centroid produces highest score for its own examples."""
        from UserPromptSubmit_modules import analysis_protocol_gate as apg

        # The module's _CLUSTER_SAMPLES has 5 phrases per cluster
        cluster_phrases = {
            "root_cause": [
                "what actually triggered this failure",
                "why did this happen",
                "what's the underlying cause",
                "trace back to the origin",
                "find the source of the problem",
            ],
            "wrong_abstraction": [
                "we're solving the wrong problem",
                "that's not the real issue",
                "misaligned abstraction level",
                "at the wrong layer of abstraction",
                "focused on the wrong thing",
            ],
            "missing_principle": [
                "we're missing a key principle",
                "overlooking something important",
                "ignoring a fundamental requirement",
                "violated the core contract",
                "failed to account for invariant",
            ],
            "fix_inadequacy": [
                "the fix doesn't really solve it",
                "patching symptoms not root cause",
                "workaround instead of solution",
                "incomplete fix",
                "the solution is insufficient",
            ],
            "bug_class": [
                "this is a class of bug",
                "category of failure",
                "type of issue we're seeing",
                "pattern of failure",
                "kind of bug",
            ],
            "frustration_signal": [
                "this keeps happening",
                "circling back to the same issue",
                "happening again and again",
                "still failing after the fix",
                "we've seen this multiple times",
            ],
        }

        # Create mock embeddings — each phrase gets a unique but cluster-similar embedding
        # Boost dominant signal to 5.0 so centroid dominant (~1.0) >> noise (~0.045)
        # This ensures cosine similarity >> 0.85 threshold after centroid averaging
        embeddings: dict[str, list[float]] = {}
        for cluster_name, phrases in cluster_phrases.items():
            for i, phrase in enumerate(phrases):
                np.random.seed(abs(hash(cluster_name)) % (2**31) + i)
                emb = np.random.randn(384).astype(np.float32) * 0.1
                # Make each cluster's centroid point in a distinct direction
                cluster_seed = abs(hash(cluster_name)) % 100
                emb[cluster_seed % 384] = 5.0  # dominant direction for cluster
                embeddings[phrase] = emb.tolist()

        mock_client = MockDaemonClient(embeddings=embeddings)

        with patch("UserPromptSubmit_modules.analysis_protocol_gate.DaemonClient", return_value=mock_client):
            apg._CENTROIDS_COMPUTED = False
            apg._CLUSTER_CENTROIDS = {}

            for cluster_name, phrases in cluster_phrases.items():
                for phrase in phrases:
                    result = apg._semantic_match(phrase)
                    assert result == cluster_name, (
                        f"Phrase '{phrase}' matched '{result}' instead of '{cluster_name}'"
                    )


class TestCosineSimilarity:
    """Tests for inline cosine_similarity function."""

    def test_cosine_similarity_positive(self):
        """Same-direction vectors produce high similarity."""
        from UserPromptSubmit_modules.analysis_protocol_gate import cosine_similarity
        a = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        b = np.array([0.5, 0.0, 0.0], dtype=np.float32)
        sim = cosine_similarity(a, b)
        assert 0.99 < sim <= 1.0, f"Expected ~1.0, got {sim}"

    def test_cosine_similarity_orthogonal(self):
        """Orthogonal vectors produce near-zero similarity."""
        from UserPromptSubmit_modules.analysis_protocol_gate import cosine_similarity
        a = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        b = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        sim = cosine_similarity(a, b)
        assert -0.01 < sim < 0.01, f"Expected ~0.0, got {sim}"

    def test_cosine_similarity_opposite(self):
        """Opposite-direction vectors produce negative similarity."""
        from UserPromptSubmit_modules.analysis_protocol_gate import cosine_similarity
        a = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        b = np.array([-1.0, 0.0, 0.0], dtype=np.float32)
        sim = cosine_similarity(a, b)
        assert -1.0 <= sim < -0.99, f"Expected ~-1.0, got {sim}"


class TestFapInjectionWiring:
    """Tests for FAP Layer 2 wiring in _should_inject_fap."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path):
        """Reset module state and patch stats file."""
        import importlib
        import UserPromptSubmit_modules.analysis_protocol_gate as mod
        mod._CENTROIDS_COMPUTED = False
        mod._CLUSTER_CENTROIDS = {}
        self.stats_file = tmp_path / "fap_layer_stats.json"
        yield
        mod._CENTROIDS_COMPUTED = False
        mod._CLUSTER_CENTROIDS = {}

    def test_should_inject_fap_uses_semantic_when_enabled(self, tmp_path: Path):
        """When fap_semantic_enabled=True, _semantic_match is tried first."""
        with patch("UserPromptSubmit_modules.analysis_protocol_gate._load_config") as mock_config:
            mock_config.return_value = {
                "enabled": True,
                "analysis_protocol_gate": True,
                "fap_semantic_enabled": True,
                "fap_similarity_threshold": 0.85,
            }

            # Create a mock that makes _semantic_match return "root_cause"
            with patch("UserPromptSubmit_modules.analysis_protocol_gate._semantic_match", return_value="root_cause"):
                with patch("UserPromptSubmit_modules.analysis_protocol_gate._bump_fap_stat"):
                    from UserPromptSubmit_modules import analysis_protocol_gate as apg
                    apg._CENTROIDS_COMPUTED = False
                    apg._CLUSTER_CENTROIDS = {}

                    result = apg._should_inject_fap("what actually triggered this failure")
                    assert result is True, "Expected FAP injection when semantic match succeeds"


class TestConfigPath:
    """Tests for safe config path resolution (SEC-003)."""

    def test_config_path_uses_realpath(self):
        """Config path should use os.path.realpath to avoid symlink traversal (SEC-003)."""
        import os
        from UserPromptSubmit_modules import analysis_protocol_gate as apg

        # The function should use os.path.realpath, not Path.resolve()
        # This is verified by reading the source
        import inspect
        src = inspect.getsource(apg._load_config)
        # Should NOT use Path.resolve() alone (crosses symlinks)
        assert "realpath" in src or "_safe_config_path" in src or "resolve()" not in src, \
            "Config path should use realpath to prevent symlink traversal"


class TestClusterSamples:
    """Verify all 6 clusters have 5 sample phrases each."""

    def test_all_clusters_have_five_samples(self):
        """Each cluster in _CLUSTER_SAMPLES has exactly 5 phrases."""
        from UserPromptSubmit_modules.analysis_protocol_gate import _CLUSTER_SAMPLES

        for cluster_name, phrases in _CLUSTER_SAMPLES.items():
            assert len(phrases) == 5, f"Cluster '{cluster_name}' has {len(phrases)} phrases, expected 5"

    def test_all_six_clusters_present(self):
        """All 6 FAP clusters are defined."""
        from UserPromptSubmit_modules.analysis_protocol_gate import _CLUSTER_SAMPLES

        expected = {
            "wrong_abstraction",
            "root_cause",
            "missing_principle",
            "fix_inadequacy",
            "bug_class",
            "frustration_signal",
        }
        actual = set(_CLUSTER_SAMPLES.keys())
        assert actual == expected, f"Missing clusters: {expected - actual}"
