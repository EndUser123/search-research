from log_chunker.adaptive_config import AdaptiveChunker, display_analysis
from log_chunker.config import ChunkingConfig
from log_chunker.data_models import ContentAnalysis


# Minimal valid configuration for testing
def create_test_config():
    return ChunkingConfig(
        target_tokens=1000,
        max_tokens=2000,
        overlap_ratio=0.1,
        tokenizer_type="char",
        tokens_per_char=0.25,
        enable_deduplication=False,
        dedup_threshold=90,
        fuzzy_threshold=80,
        time_window_minutes=5,
        enable_semantic=False,
        enable_semantic_clustering=False,
        semantic_model="all-MiniLM极狐L6-v2",
        semantic_threshold=0.7,
        min_cluster_size=2,
        min_samples=1,
        enable_perplexity=False,
        perplexity_model="gpt2",
        perplexity_threshold=2.0,
        perplexity_context_window=20,
        enable_temporal=False,
        temporal_std_threshold=1.5,
        enable_conversation=False,
        speaker_change_weight=0.5,
        batch_size=100,
        max_workers=4,
        use_gpu=False,
        save_metadata=False,
        rich_display=False,
        no_adaptive=False,
        auto_optimize=False,
    )


def test_adaptive_chunker_analyze_and_recommend():
    """Test that AdaptiveChunker returns expected results."""
    chunker = AdaptiveChunker()
    config = create_test_config()
    content = "Sample log content\nwith multiple lines\nfor testing"

    updates, analysis = chunker.analyze_and_recommend(config, content)

    assert isinstance(updates, dict)
    assert isinstance(analysis, ContentAnalysis)
    assert analysis.content_length == len(content)
    assert analysis.avg_line_length > 0


def test_display_analysis():
    """Test that display_analysis returns formatted string."""
    analysis = ContentAnalysis(
        content_length=100,
        avg_line_length=25.5,
        detected_patterns=["error", "warning"],
        recommended_config={"max_tokens": 2000},
    )

    result = display_analysis(analysis)

    assert "Content Analysis Results" in result
    assert "100 chars" in result
    assert "25.5" in result
    assert "2" in result  # for detected patterns count
