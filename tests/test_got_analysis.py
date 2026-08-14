"""Unit tests for Graph-of-Thought (GoT) analysis module."""

from __future__ import annotations

from core.processing.got_analysis import GotAnalyzer, GotEdge


class MockResult:
    """Mock search result for testing."""
    def __init__(self, title: str, content: str):
        self.title = title
        self.content = content


class TestGotNodeExtraction:
    """Test node extraction from search results."""

    def test_extract_constraint_nodes(self):
        """Test extraction of constraint patterns (must, should, required)."""
        analyzer = GotAnalyzer()
        result = MockResult(
            "Requirements",
            "You must use async for performance. It is required to handle errors."
        )

        nodes = analyzer.extract_nodes_from_result(result, "result_0")

        constraint_nodes = [n for n in nodes if n.node_type == "constraint"]
        assert len(constraint_nodes) >= 2, "Should extract constraint patterns"
        assert any("must" in n.text.lower() for n in constraint_nodes)
        assert any("required" in n.text.lower() for n in constraint_nodes)

    def test_extract_idea_nodes(self):
        """Test extraction of idea patterns (can, could, might, suggest)."""
        analyzer = GotAnalyzer()
        result = MockResult(
            "Suggestions",
            "You can use caching. We could implement Redis. It might improve speed."
        )

        nodes = analyzer.extract_nodes_from_result(result, "result_0")

        idea_nodes = [n for n in nodes if n.node_type == "idea"]
        assert len(idea_nodes) >= 2, "Should extract idea patterns"
        assert any("can" in n.text.lower() or "could" in n.text.lower() for n in idea_nodes)

    def test_extract_risk_nodes(self):
        """Test extraction of risk patterns (risk, danger, warning, error)."""
        analyzer = GotAnalyzer()
        result = MockResult(
            "Warnings",
            "There is a risk of data corruption. Warning: this may fail. Error handling needed."
        )

        nodes = analyzer.extract_nodes_from_result(result, "result_0")

        risk_nodes = [n for n in nodes if n.node_type == "risk"]
        assert len(risk_nodes) >= 2, "Should extract risk patterns"
        assert any("risk" in n.text.lower() or "warning" in n.text.lower() for n in risk_nodes)

    def test_extract_keyword_nodes(self):
        """Test extraction of keyword patterns (two-word phrases)."""
        analyzer = GotAnalyzer()
        result = MockResult(
            "Overview",
            "Knowledge graphs provide semantic search. Entity extraction improves accuracy."
        )

        nodes = analyzer.extract_nodes_from_result(result, "result_0")

        keyword_nodes = [n for n in nodes if n.node_type == "keyword"]
        assert len(keyword_nodes) >= 2, "Should extract keyword phrases"
        assert all(len(n.text.split()) >= 2 for n in keyword_nodes), "Keywords should be multi-word"

    def test_node_confidence_scores(self):
        """Test that nodes have appropriate confidence scores."""
        analyzer = GotAnalyzer()
        result = MockResult(
            "Mixed Content",
            "You must implement this. It can improve performance. There is a risk of failure."
        )

        nodes = analyzer.extract_nodes_from_result(result, "result_0")

        assert all(0.0 <= n.confidence <= 1.0 for n in nodes), "Confidence should be between 0 and 1"
        assert any(n.confidence >= 0.6 for n in nodes), "Some nodes should have high confidence"

    def test_empty_result_handling(self):
        """Test node extraction from empty or null results."""
        analyzer = GotAnalyzer()

        # Empty content
        result = MockResult("Empty", "")
        nodes = analyzer.extract_nodes_from_result(result, "result_0")
        assert len(nodes) == 0, "Empty content should return no nodes"

        # Result with no content/title attributes
        nodes = analyzer.extract_nodes_from_result(None, "result_0")
        assert len(nodes) == 0, "None result should return no nodes"


class TestGotEdgeAnalysis:
    """Test edge analysis between search results."""

    def test_supports_edge_detection(self):
        """Test detection of 'supports' relationship with high Jaccard similarity."""
        analyzer = GotAnalyzer()

        # Create results with overlapping content
        results = [
            MockResult("Async Python", "async await coroutine performance"),
            MockResult("Async Patterns", "async await coroutine speed"),
        ]

        result_to_nodes = {
            "result_0": ["result_0_async", "result_0_coroutine"],
            "result_1": ["result_1_async", "result_1_coroutine"],
        }

        edges = analyzer._analyze_edges(results, result_to_nodes)

        supports_edges = [e for e in edges if e.edge_type == "supports"]
        assert len(supports_edges) >= 1, "Should detect supports relationship with overlap"
        assert edges[0].strength > 0, "Supports edge should have positive strength"

    def test_contradiction_detection(self):
        """Test detection of contradictory results."""
        analyzer = GotAnalyzer()

        # Create contradictory results
        results = [
            MockResult("Pro Async", "async is great, always use it"),
            MockResult("Anti Async", "never use async, it only adds complexity"),
        ]

        result_to_nodes = {
            "result_0": ["result_0_async"],
            "result_1": ["result_1_async"],
        }

        edges = analyzer._analyze_edges(results, result_to_nodes)

        contradict_edges = [e for e in edges if e.edge_type == "contradicts"]
        assert len(contradict_edges) >= 1, "Should detect contradiction with negation words"

    def test_unrelated_detection(self):
        """Test detection of unrelated results with low similarity."""
        analyzer = GotAnalyzer()

        # Create unrelated results
        results = [
            MockResult("Databases", "sql database normalization"),
            MockResult("UI Design", "css styling responsive layout"),
        ]

        result_to_nodes = {
            "result_0": ["result_0_sql"],
            "result_1": ["result_1_css"],
        }

        edges = analyzer._analyze_edges(results, result_to_nodes)

        unrelated_edges = [e for e in edges if e.edge_type == "unrelated"]
        assert len(unrelated_edges) >= 1, "Should detect unrelated results"

    def test_jaccard_similarity_calculation(self):
        """Test Jaccard similarity calculation for edge strength."""
        analyzer = GotAnalyzer()

        results = [
            MockResult("Test1", "a b c"),
            MockResult("Test2", "a b d"),
        ]

        result_to_nodes = {
            "result_0": ["result_0_a", "result_0_b", "result_0_c"],
            "result_1": ["result_1_a", "result_1_b", "result_1_d"],
        }

        edges = analyzer._analyze_edges(results, result_to_nodes)

        # Jaccard similarity = intersection/union = 2/4 = 0.5
        assert len(edges) >= 1, "Should create edge for results"
        edge = edges[0]
        assert edge.strength == 0.5, f"Jaccard similarity should be 0.5, got {edge.strength}"

    def test_empty_results_handling(self):
        """Test edge analysis with empty results."""
        analyzer = GotAnalyzer()
        edges = analyzer._analyze_edges([], {})
        assert len(edges) == 0, "Empty results should return no edges"


class TestGotClustering:
    """Test result clustering functionality."""

    def test_cluster_creation_with_min_size(self):
        """Test that clusters are only created with minimum size."""
        analyzer = GotAnalyzer(min_cluster_size=2)

        # Create only 1 result (below min size)
        results = [MockResult("Single", "test content")]
        result_to_nodes = {"result_0": ["result_0_test"]}

        clusters = analyzer._cluster_results(results, result_to_nodes)
        assert len(clusters) == 0, "Should not create clusters below min size"

    def test_cluster_with_multiple_results(self):
        """Test clustering of related results."""
        analyzer = GotAnalyzer(min_cluster_size=2)

        # Create results with shared nodes (edges created in _analyze_edges)
        results = [
            MockResult("Test1", "shared content"),
            MockResult("Test2", "shared content"),
        ]

        # Simulate edges being created
        analyzer.edges = [
            GotEdge("result_0", "result_1", "supports", 0.5, "Shared nodes")
        ]

        result_to_nodes = {
            "result_0": ["result_0_shared", "result_0_content"],
            "result_1": ["result_1_shared", "result_1_content"],
        }

        clusters = analyzer._cluster_results(results, result_to_nodes)
        assert len(clusters) >= 1, "Should create cluster for connected results"

    def test_cluster_confidence_calculation(self):
        """Test confidence score calculation for clusters."""
        analyzer = GotAnalyzer(min_cluster_size=2)

        # Create results with edges
        results = [
            MockResult("Test1", "a b"),
            MockResult("Test2", "a b"),
        ]

        analyzer.edges = [
            GotEdge("result_0", "result_1", "supports", 0.7, "Shared nodes")
        ]

        result_to_nodes = {
            "result_0": ["result_0_a", "result_0_b"],
            "result_1": ["result_1_a", "result_1_b"],
        }

        clusters = analyzer._cluster_results(results, result_to_nodes)
        if clusters:
            cluster = clusters[0]
            assert 0.0 <= cluster.confidence <= 1.0, "Confidence should be between 0 and 1"
            assert cluster.confidence > 0, "Cluster with strong edges should have positive confidence"


class TestGotCycleDetection:
    """Test cycle detection in edge graph."""

    def test_no_cycles_in_acyclic_graph(self):
        """Test that acyclic graphs return no cycles."""
        analyzer = GotAnalyzer()

        # Create acyclic edges: A -> B -> C
        analyzer.edges = [
            GotEdge("A", "B", "supports", 0.5, ""),
            GotEdge("B", "C", "supports", 0.5, ""),
        ]

        cycles = analyzer._detect_cycles()
        assert len(cycles) == 0, "Acyclic graph should have no cycles"

    def test_cycle_detection_in_cyclic_graph(self):
        """Test detection of cycles in graph."""
        analyzer = GotAnalyzer()

        # Create cyclic edges: A -> B -> C -> A
        analyzer.edges = [
            GotEdge("A", "B", "supports", 0.5, ""),
            GotEdge("B", "C", "supports", 0.5, ""),
            GotEdge("C", "A", "supports", 0.5, ""),
        ]

        cycles = analyzer._detect_cycles()
        assert len(cycles) >= 1, "Cyclic graph should detect at least one cycle"

    def test_empty_graph_handling(self):
        """Test cycle detection with no edges."""
        analyzer = GotAnalyzer()
        analyzer.edges = []

        cycles = analyzer._detect_cycles()
        assert len(cycles) == 0, "Empty graph should have no cycles"


class TestGotAnalyzerIntegration:
    """Integration tests for complete GoT analysis workflow."""

    def test_analyze_results_with_empty_input(self):
        """Test analyze_results with empty results list."""
        analyzer = GotAnalyzer()
        analysis = analyzer.analyze_results([])

        assert analysis["nodes"] == []
        assert analysis["edges"] == []
        assert analysis["clusters"] == []
        assert analysis["cycles"] == []
        assert "summary" in analysis

    def test_analyze_results_creates_components(self):
        """Test that analyze_results creates all expected components."""
        analyzer = GotAnalyzer()

        results = [
            MockResult("Test1", "You must use async"),
            MockResult("Test2", "async is great"),
            MockResult("Test3", "never use async"),
        ]

        analysis = analyzer.analyze_results(results)

        assert "nodes" in analysis
        assert "edges" in analysis
        assert "clusters" in analysis
        assert "cycles" in analysis
        assert "summary" in analysis

    def test_summary_generation(self):
        """Test that summary is generated correctly."""
        analyzer = GotAnalyzer()

        results = [
            MockResult("Test1", "content"),
            MockResult("Test2", "more content"),
        ]

        analysis = analyzer.analyze_results(results)

        assert "summary" in analysis
        assert len(analysis["summary"]) > 0, "Summary should not be empty"
        assert "Analyzed" in analysis["summary"] or "GoT" in analysis["summary"]

    def test_format_results_with_got(self):
        """Test formatting of results with GoT metadata."""
        analyzer = GotAnalyzer()

        results = [
            MockResult("Test1", "async await"),
            MockResult("Test2", "coroutine"),
        ]

        analysis = analyzer.analyze_results(results)
        formatted = analyzer.format_results_with_got(results, analysis)

        assert isinstance(formatted, str)
        assert len(formatted) > 0, "Formatted output should not be empty"
        # Should contain summary section
        assert "summary" in formatted.lower() or "**" in formatted

    def test_min_cluster_size_filtering(self):
        """Test that min_cluster_size parameter filters small clusters."""
        analyzer_strict = GotAnalyzer(min_cluster_size=3)
        analyzer_lenient = GotAnalyzer(min_cluster_size=1)

        results = [
            MockResult("Test1", "shared"),
            MockResult("Test2", "shared"),
        ]

        # Simulate edges
        for analyzer in [analyzer_strict, analyzer_lenient]:
            analyzer.edges = [
                GotEdge("result_0", "result_1", "supports", 0.5, "")
            ]
            result_to_nodes = {
                "result_0": ["result_0_shared"],
                "result_1": ["result_1_shared"],
            }
            analyzer._cluster_results(results, result_to_nodes)

        # Strict analyzer should filter out 2-result cluster
        assert len(analyzer_strict.clusters) == 0, "Strict min size should filter small clusters"

        # Lenient analyzer should allow 2-result cluster
        assert len(analyzer_lenient.clusters) >= 1, "Lenient min size should allow small clusters"
