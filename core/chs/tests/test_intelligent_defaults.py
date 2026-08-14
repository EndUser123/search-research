"""Tests for intelligent defaults detection."""

from .intelligent_defaults import (
    IntelligentDefaults,
    _cluster_reason,
    _explain_reason,
    _session_reason,
    get_feature_config,
    should_cluster,
    should_enable_session,
    should_explain,
)


class TestShouldExplain:
    """Tests for should_explain function."""

    def test_short_simple_query_no_explain(self):
        """Simple short query should not trigger explain."""
        assert not should_explain("simple query", execution_time_ms=100)

    def test_long_query_triggers_explain(self):
        """Queries >100 chars trigger explain."""
        long_query = "x" * 101
        assert should_explain(long_query)

    def test_or_query_triggers_explain(self):
        """Multi-part OR queries trigger explain."""
        assert should_explain("query1 OR query2")

    def test_slow_query_triggers_explain(self):
        """Slow queries (>2s) trigger explain."""
        assert should_explain("simple query", execution_time_ms=2500)

    def test_multiple_backends_triggers_explain(self):
        """Multiple backends trigger explain."""
        assert should_explain("query", backend_count=3)

    def test_no_results_triggers_explain(self):
        """Empty results trigger explain for debugging."""
        assert should_explain("query", result_count=0)

    def test_complex_and_triggers_explain(self):
        """Complex AND queries with many words trigger explain."""
        complex_and = "word1 AND word2 AND word3 AND word4 AND word5"
        assert should_explain(complex_and)

    def test_nested_groups_trigger_explain(self):
        """Nested query groups trigger explain."""
        nested = "(group1) AND (group2) AND (group3)"
        assert should_explain(nested)

    def test_case_insensitive_or_detection(self):
        """OR detection should be case-insensitive."""
        assert should_explain("query1 or query2")
        assert should_explain("query1 Or query2")
        assert should_explain("QUERY1 OR QUERY2")


class TestShouldEnableSession:
    """Tests for should_enable_session function."""

    def test_session_enabled_when_wt_session_set(self, monkeypatch):
        """Session should enable when WT_SESSION is set."""
        monkeypatch.setenv("WT_SESSION", "test_session_12345")
        assert should_enable_session()

    def test_session_disabled_when_no_wt_session(self, monkeypatch):
        """Session should disable when WT_SESSION is not set."""
        monkeypatch.delenv("WT_SESSION", raising=False)
        assert not should_enable_session()

    def test_session_disabled_with_empty_wt_session(self, monkeypatch):
        """Session should disable with empty WT_SESSION."""
        monkeypatch.setenv("WT_SESSION", "")
        assert not should_enable_session()


class TestShouldCluster:
    """Tests for should_cluster function."""

    def test_no_cluster_below_threshold(self):
        """Fewer than 10 results should not cluster."""
        results = [{"source": "code"}] * 5
        assert not should_cluster(results)

    def test_cluster_with_single_source(self):
        """Single source results should not cluster."""
        results = [{"source": "code"}] * 10
        assert not should_cluster(results)

    def test_cluster_with_diverse_sources(self):
        """Diverse sources should trigger clustering."""
        results = [{"source": "code"}, {"source": "docs"}, {"source": "git"}] * 4
        assert should_cluster(results)

    def test_cluster_respects_custom_threshold(self):
        """Clustering respects custom min_results."""
        results = [{"source": "code"}] * 15
        assert should_cluster(results, min_results=20) is False
        assert should_cluster(results, min_results=10) is False

    def test_cluster_with_enough_diverse_results(self):
        """Clustering works with enough diverse results."""
        results = [{"source": "code"}, {"source": "docs"}] * 8
        assert should_cluster(results, min_results=10)

    def test_cluster_respects_source_diversity(self):
        """Clustering respects custom source diversity."""
        results = [{"source": "code"}, {"source": "docs"}] * 5
        assert should_cluster(results, min_source_diversity=3) is False
        assert should_cluster(results, min_source_diversity=2)

    def test_results_without_source_field(self):
        """Results without source field should count as 'unknown'."""
        results = [{}] * 10
        assert not should_cluster(results)


class TestGetFeatureConfig:
    """Tests for get_feature_config function."""

    def test_returns_all_flags(self):
        """Config dict should include all feature flags."""
        config = get_feature_config(
            query="test query", execution_time_ms=100, backend_count=1, result_count=5, results=[]
        )
        assert "explain" in config
        assert "session" in config
        assert "cluster" in config
        assert "reasons" in config

    def test_reasons_include_explain_decision(self):
        """Reasons should explain the explain decision."""
        config = get_feature_config(query="x" * 101, execution_time_ms=100)
        assert "explain" in config["reasons"]
        assert config["explain"] is True

    def test_reasons_include_session_decision(self, monkeypatch):
        """Reasons should explain the session decision."""
        monkeypatch.setenv("WT_SESSION", "test_session")
        config = get_feature_config()
        assert "session" in config["reasons"]
        assert config["session"] is True

    def test_reasons_include_cluster_decision(self):
        """Reasons should explain the cluster decision."""
        results = [{"source": "code"}, {"source": "docs"}] * 5
        config = get_feature_config(results=results)
        assert "cluster" in config["reasons"]
        assert config["cluster"] is True


class TestExplainReason:
    """Tests for _explain_reason function."""

    def test_slow_query_reason(self):
        """Slow query should mention execution time."""
        reason = _explain_reason("query", execution_time_ms=3000, backend_count=1, result_count=5)
        assert "3000ms" in reason or "Slow" in reason

    def test_long_query_reason(self):
        """Long query should mention character count."""
        reason = _explain_reason("x" * 101, 0, 1, 5)
        assert "101" in reason or "chars" in reason

    def test_or_query_reason(self):
        """OR query should mention multi-part."""
        reason = _explain_reason("a OR b", 0, 1, 5)
        assert "OR" in reason or "multi" in reason.lower()

    def test_multiple_backends_reason(self):
        """Multiple backends should mention count."""
        reason = _explain_reason("query", 0, backend_count=4, result_count=5)
        assert "4" in reason

    def test_no_results_reason(self):
        """No results should mention explanation helpful."""
        reason = _explain_reason("query", 0, 1, result_count=0)
        assert "No results" in reason


class TestSessionReason:
    """Tests for _session_reason function."""

    def test_terminal_mode_reason(self, monkeypatch):
        """Terminal mode should mention WT_SESSION."""
        monkeypatch.setenv("WT_SESSION", "abc123def456")  # pragma: allowlist secret
        reason = _session_reason()
        assert "Terminal" in reason
        assert "WT_SESSION" in reason

    def test_script_mode_reason(self, monkeypatch):
        """Script mode should mention programmatic."""
        monkeypatch.delenv("WT_SESSION", raising=False)
        reason = _session_reason()
        assert "script" in reason.lower() or "programmatic" in reason.lower()


class TestClusterReason:
    """Tests for _cluster_reason function."""

    def test_too_few_results_reason(self):
        """Few results should mention count."""
        reason = _cluster_reason([{"source": "code"}] * 5)
        assert "5" in reason
        assert "10" in reason

    def test_low_diversity_reason(self):
        """Low diversity should mention source count."""
        results = [{"source": "code"}] * 10
        reason = _cluster_reason(results)
        assert "1" in reason
        assert "source" in reason.lower()

    def test_diverse_results_reason(self):
        """Diverse results should mention counts."""
        results = [{"source": "code"}, {"source": "docs"}, {"source": "git"}] * 4
        reason = _cluster_reason(results)
        assert "12" in reason
        assert "3" in reason


class TestIntelligentDefaults:
    """Tests for IntelligentDefaults class."""

    def test_default_thresholds(self):
        """Should have default thresholds configured."""
        config = IntelligentDefaults()
        assert config.explain_threshold_ms == 2000
        assert config.explain_query_length == 100
        assert config.cluster_min_results == 10
        assert config.cluster_min_sources == 2

    def test_custom_thresholds(self):
        """Should accept custom thresholds."""
        config = IntelligentDefaults(
            explain_threshold_ms=5000,
            explain_query_length=50,
            cluster_min_results=20,
            cluster_min_sources=3,
        )
        assert config.explain_threshold_ms == 5000
        assert config.explain_query_length == 50
        assert config.cluster_min_results == 20
        assert config.cluster_min_sources == 3

    def test_should_explain_uses_custom_threshold(self):
        """Should use custom explain threshold."""
        config = IntelligentDefaults(explain_threshold_ms=5000)
        assert not config.should_explain("query", execution_time_ms=3000)
        assert config.should_explain("query", execution_time_ms=6000)

    def test_should_cluster_uses_custom_thresholds(self):
        """Should use custom cluster thresholds."""
        config = IntelligentDefaults(cluster_min_results=20, cluster_min_sources=3)
        results = [{"source": "code"}, {"source": "docs"}] * 10
        assert not config.should_cluster(results)

    def test_get_config_returns_full_config(self):
        """get_config should return complete configuration."""
        config = IntelligentDefaults()
        cfg = config.get_config(
            query="test", execution_time_ms=100, backend_count=1, result_count=5, results=[]
        )
        assert "explain" in cfg
        assert "session" in cfg
        assert "cluster" in cfg
        assert "reasons" in cfg


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""

    def test_simple_quick_search(self):
        """Simple fast search should not trigger extra features."""
        config = get_feature_config(
            query="async",
            execution_time_ms=150,
            backend_count=1,
            result_count=10,
            results=[{"source": "code"}] * 10,
        )
        assert config["explain"] is False
        assert config["cluster"] is False

    def test_complex_slow_search(self, monkeypatch):
        """Complex slow search should trigger explain."""
        monkeypatch.delenv("WT_SESSION", raising=False)
        config = get_feature_config(
            query="async patterns OR event loop OR coroutines",
            execution_time_ms=3500,
            backend_count=3,
            result_count=25,
            results=[{"source": "code"}, {"source": "docs"}, {"source": "git"}] * 8,
        )
        assert config["explain"] is True
        assert config["cluster"] is True
        assert config["session"] is False

    def test_terminal_research_session(self, monkeypatch):
        """Terminal mode with diverse results should enable session + cluster."""
        monkeypatch.setenv("WT_SESSION", "terminal_session_123")
        config = get_feature_config(
            query="python async",
            execution_time_ms=500,
            backend_count=2,
            result_count=15,
            results=[{"source": "code"}, {"source": "docs"}] * 8,
        )
        assert config["session"] is True
        assert config["cluster"] is True

    def test_failed_search(self):
        """Failed search should trigger explain for debugging."""
        config = get_feature_config(
            query="some complex query here",
            execution_time_ms=1000,
            backend_count=2,
            result_count=0,
            results=[],
        )
        assert config["explain"] is True
        assert config["cluster"] is False

    def test_script_single_shot(self, monkeypatch):
        """Script usage should not enable session."""
        monkeypatch.delenv("WT_SESSION", raising=False)
        config = get_feature_config(
            query="get me info on X",
            execution_time_ms=200,
            backend_count=1,
            result_count=5,
            results=[{"source": "docs"}] * 5,
        )
        assert config["session"] is False
        assert config["cluster"] is False
        assert config["explain"] is False
