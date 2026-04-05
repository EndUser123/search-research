from __future__ import annotations

from datetime import datetime, timedelta
from datetime import timedelta
from pathlib import Path
import json
import os
import re
import statistics
import sys

from domain_models.chat_models import (
from enhanced_chat_analyzer import EnhancedChatAnalyzer, create_enhanced_chat_analyzer
from interfaces.chat_interfaces import IChatAnalyzer
from unittest.mock import patch
import tempfile
import unittest

#!/usr/bin/env python3
"""Comprehensive Tests and Validation for Enhanced CHS
Complete test suite for enhanced chat analyzer functionality.
"""


# Add project paths
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent.parent))
sys.path.append(
    str(Path(__file__).parent.parent.parent.parent.parent.parent / "src" / "lib")
)

# Import components to test
    AnalysisSession,
    ChatMessage,
    ConversationContext,
    ConversationPattern,
    ExportConfiguration,
    KnowledgeGraph,
    SearchRanking,
    SearchResult,
    TemporalMetrics,
    TemporalScale,
)


class TestEnhancedStorageEngine(unittest.TestCase):
    """Test enhanced storage engine functionality."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        from components.storage_engine.enhanced_storage import EnhancedStorageEngine

        self.storage_engine = EnhancedStorageEngine(Path(self.temp_dir))

    def test_storage_initialization(self) -> None:
        """Test storage engine initialization."""
        assert self.storage_engine.index_dir.exists()
        assert self.storage_engine.db_path.exists()

    def test_index_operations(self) -> None:
        """Test index save/load operations."""
        test_index = {
            "entries": {"test_id": {"content": "test message"}},
            "word_index": {"test": [("test_id", 1.0)]},
            "date_index": {"2023-01-01": ["test_id"]},
            "project_index": {"test_project": ["test_id"]},
        }

        # Save index
        self.storage_engine.save_index(test_index)

        # Load index
        loaded_index = self.storage_engine.load_index()
        assert loaded_index["entries"]["test_id"]["content"] == "test message"
        assert "test" in loaded_index["word_index"]

    def test_vocabulary_operations(self) -> None:
        """Test vocabulary save/load operations."""
        test_vocabulary = {
            "test": {"doc_freq": 5, "idf": 1.5},
            "python": {"doc_freq": 10, "idf": 0.8},
        }

        # Save vocabulary
        self.storage_engine.save_vocabulary(test_vocabulary)

        # Load vocabulary
        loaded_vocabulary = self.storage_engine.load_vocabulary()
        assert loaded_vocabulary["test"]["doc_freq"] == 5

    def test_temporal_entry_operations(self) -> None:
        """Test temporal entry operations."""
        entry_data = {
            "id": "test_entry",
            "content": "Test message content",
            "timestamp": int(datetime.now().timestamp() * 1000),
            "context": "technical",
        }

        # Add temporal entry
        self.storage_engine.add_temporal_entry(
            entry_id="test_entry",
            entry=entry_data,
            intensity_score=0.7,
            topic_vector=[0.1, 0.2, 0.3],
        )

        # Verify entry was added
        temporal_count = self.storage_engine._get_temporal_entry_count()
        assert temporal_count == 1

    def test_cache_operations(self) -> None:
        """Test semantic cache operations."""
        query = "test query"
        filters = {"context_filter": "technical"}
        test_results = [
            SearchResult(
                message=ChatMessage(content="Test result"),
                relevance_score=0.8,
            ),
        ]

        # Cache miss
        cached_results = self.storage_engine.get_cached_search_results(query, filters)
        assert cached_results is None

        # Cache results
        self.storage_engine.cache_search_results(query, filters, test_results)

        # Cache hit
        cached_results = self.storage_engine.get_cached_search_results(query, filters)
        assert len(cached_results) == 1
        assert cached_results[0].relevance_score == 0.8

    def test_storage_stats(self) -> None:
        """Test storage statistics."""
        stats = self.storage_engine.get_storage_stats()
        assert "storage_engine" in stats
        assert "version" in stats
        assert stats["storage_engine"] == "enhanced"
        assert stats["version"] == "2.0"

    def tearDown(self) -> None:
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir)


class TestTemporalAnalyzer(unittest.TestCase):
    """Test temporal intelligence layer."""

    def setUp(self) -> None:
        """Set up test environment."""
        from components.temporal_intelligence.temporal_analyzer import (
            EnhancedTemporalAnalyzer,
        )

        self.temporal_analyzer = EnhancedTemporalAnalyzer()

        # Create test messages
        self.test_messages = [
            ChatMessage(
                content="Python code for testing",
                timestamp=int((datetime.now() - timedelta(days=2)).timestamp() * 1000),
                context=ConversationContext.TECHNICAL,
            ),
            ChatMessage(
                content="Docker deployment issues",
                timestamp=int((datetime.now() - timedelta(days=1)).timestamp() * 1000),
                context=ConversationContext.DEBUGGING,
            ),
            ChatMessage(
                content="API design discussion",
                timestamp=int(datetime.now().timestamp() * 1000),
                context=ConversationContext.PLANNING,
            ),
        ]

    def test_conversation_intensity_analysis(self) -> None:
        """Test conversation intensity analysis."""
        metrics = self.temporal_analyzer.analyze_conversation_intensity(
            self.test_messages,
            TemporalScale.DAILY,
        )

        assert isinstance(metrics, list)
        assert len(metrics) > 0

        for metric in metrics:
            assert isinstance(metric, TemporalMetrics)
            assert metric.message_count >= 0
            assert metric.intensity_average >= 0.0
            assert metric.intensity_average <= 1.0

    def test_temporal_pattern_detection(self) -> None:
        """Test temporal pattern detection."""
        # Create more test data for pattern detection
        extended_messages = []
        base_time = datetime.now() - timedelta(days=10)

        for i in range(10):
            message = ChatMessage(
                content=f"Day {i} discussion about python development",
                timestamp=int((base_time + timedelta(days=i)).timestamp() * 1000),
                context=ConversationContext.TECHNICAL,
            )
            extended_messages.append(message)

        metrics = self.temporal_analyzer.analyze_conversation_intensity(
            extended_messages,
            TemporalScale.DAILY,
        )
        patterns = self.temporal_analyzer.detect_temporal_patterns(metrics)

        assert isinstance(patterns, list)

        for pattern in patterns:
            assert isinstance(pattern, ConversationPattern)
            assert pattern.pattern_type is not None
            assert pattern.frequency >= 0
            assert pattern.confidence >= 0.0
            assert pattern.confidence <= 1.0

    def test_trend_calculation(self) -> None:
        """Test trend calculation."""
        metrics = self.temporal_analyzer.analyze_conversation_intensity(
            self.test_messages,
            TemporalScale.DAILY,
        )

        if len(metrics) > 1:
            trends = self.temporal_analyzer.calculate_trends(metrics)
            assert isinstance(trends, dict)

            expected_keys = [
                "message_count_slope",
                "message_count_correlation",
                "intensity_slope",
                "intensity_correlation",
            ]
            for key in expected_keys:
                assert key in trends

    def test_anomaly_detection(self) -> None:
        """Test temporal anomaly detection."""
        # Create messages with one anomaly
        normal_messages = [
            ChatMessage(
                content="Normal message",
                timestamp=int((datetime.now() - timedelta(days=i)).timestamp() * 1000),
            )
            for i in range(5, 0, -1)
        ]

        # Add anomaly (high intensity message)
        anomaly_message = ChatMessage(
            content="CRITICAL ERROR! System failure detected immediately!",
            timestamp=int(datetime.now().timestamp() * 1000),
        )
        normal_messages.append(anomaly_message)

        metrics = self.temporal_analyzer.analyze_conversation_intensity(
            normal_messages,
            TemporalScale.DAILY,
        )

        anomalies = self.temporal_analyzer.identify_anomalies(metrics)
        assert isinstance(anomalies, list)

    def test_activity_prediction(self) -> None:
        """Test activity prediction."""
        # Create historical data
        historical_messages = []
        base_time = datetime.now() - timedelta(days=14)

        for i in range(14):
            message = ChatMessage(
                content=f"Historical activity day {i}",
                timestamp=int((base_time + timedelta(days=i)).timestamp() * 1000),
            )
            historical_messages.append(message)

        metrics = self.temporal_analyzer.analyze_conversation_intensity(
            historical_messages,
            TemporalScale.DAILY,
        )

        predictions = self.temporal_analyzer.predict_activity(
            metrics, prediction_periods=3
        )
        assert isinstance(predictions, list)
        assert len(predictions) == 3

        for prediction in predictions:
            assert isinstance(prediction, TemporalMetrics)


class TestSemanticEngine(unittest.TestCase):
    """Test semantic engine functionality."""

    def setUp(self) -> None:
        """Set up test environment."""
        from components.semantic_engine.semantic_analyzer import (
            EnhancedSemanticAnalyzer,
        )

        self.semantic_engine = EnhancedSemanticAnalyzer()

        # Create test messages
        self.test_messages = [
            ChatMessage(
                content="Python function for data processing",
                semantic_tags=["python", "data", "processing"],
            ),
            ChatMessage(
                content="Docker container deployment strategy",
                semantic_tags=["docker", "deployment", "containers"],
            ),
            ChatMessage(
                content="API endpoint implementation with REST",
                semantic_tags=["api", "rest", "endpoint"],
            ),
        ]

    def test_topic_extraction(self) -> None:
        """Test topic extraction from messages."""
        topics = self.semantic_engine.extract_topics(self.test_messages)

        assert isinstance(topics, dict)
        assert len(topics) > 0

        for topic, messages in topics.items():
            assert isinstance(topic, str)
            assert isinstance(messages, list)
            assert len(messages) > 0

    def test_semantic_similarity(self) -> None:
        """Test semantic similarity calculation."""
        message1 = self.test_messages[0]
        message2 = self.test_messages[1]

        similarity = self.semantic_engine.calculate_semantic_similarity(
            message1, message2
        )

        assert isinstance(similarity, float)
        assert similarity >= 0.0
        assert similarity <= 1.0

    def test_knowledge_graph_building(self) -> None:
        """Test knowledge graph construction."""
        graph = self.semantic_engine.build_knowledge_graph(self.test_messages)

        assert isinstance(graph, KnowledgeGraph)
        assert graph.node_count > 0
        assert graph.edge_count >= 0

        # Check that message nodes exist
        for message in self.test_messages:
            assert message.id in graph.nodes

    def test_knowledge_graph_update(self) -> None:
        """Test knowledge graph updating."""
        # Build initial graph
        graph = self.semantic_engine.build_knowledge_graph(self.test_messages[:2])

        # Add new message
        new_message = ChatMessage(
            content="Additional message for testing",
            semantic_tags=["testing", "update"],
        )

        # Update graph
        updated_graph = self.semantic_engine.update_knowledge_graph(
            graph, [new_message]
        )

        assert isinstance(updated_graph, KnowledgeGraph)
        assert updated_graph.node_count >= graph.node_count
        assert new_message.id in updated_graph.nodes

    def test_related_concepts(self) -> None:
        """Test related concept finding."""
        graph = self.semantic_engine.build_knowledge_graph(self.test_messages)

        # Find concepts related to "python"
        related_concepts = self.semantic_engine.find_related_concepts("python", graph)

        assert isinstance(related_concepts, list)

    def test_expertise_domain_identification(self) -> None:
        """Test expertise domain identification."""
        domains = self.semantic_engine.identify_expertise_domains(self.test_messages)

        assert isinstance(domains, dict)

        for domain, score in domains.items():
            assert isinstance(domain, str)
            assert isinstance(score, float)
            assert score >= 0.0
            assert score <= 1.0

    def test_topic_vector_generation(self) -> None:
        """Test topic vector generation."""
        vectors = self.semantic_engine.generate_topic_vectors(self.test_messages)

        assert isinstance(vectors, dict)

        for vector in vectors.values():
            assert isinstance(vector, list)
            assert len(vector) > 0

            # Check that vector contains only numbers
            for value in vector:
                assert isinstance(value, (int, float))


class TestPatternRecognizer(unittest.TestCase):
    """Test pattern recognition system."""

    def setUp(self) -> None:
        """Set up test environment."""
        from components.pattern_recognition.pattern_analyzer import (
            EnhancedPatternRecognizer,
        )

        self.pattern_recognizer = EnhancedPatternRecognizer()

        # Create test messages with patterns
        self.test_messages = [
            ChatMessage(
                content="I'm having an error with my Python code",
                context=ConversationContext.DEBUGGING,
            ),
            ChatMessage(
                content="Try using a try-catch block to handle exceptions",
                context=ConversationContext.TECHNICAL,
            ),
            ChatMessage(
                content="That fixed it! The error is resolved now",
                context=ConversationContext.TECHNICAL,
            ),
            ChatMessage(
                content="We need to decide between PostgreSQL and MongoDB",
                context=ConversationContext.PLANNING,
            ),
            ChatMessage(
                content="Let's go with PostgreSQL for better relational features",
                context=ConversationContext.TECHNICAL,
            ),
        ]

    def test_conversation_pattern_identification(self) -> None:
        """Test conversation pattern identification."""
        patterns = self.pattern_recognizer.identify_conversation_patterns(
            self.test_messages
        )

        assert isinstance(patterns, list)

        for pattern in patterns:
            assert isinstance(pattern, ConversationPattern)
            assert pattern.pattern_type is not None
            assert pattern.description is not None
            assert pattern.frequency >= 0
            assert pattern.confidence >= 0.0

    def test_decision_trail_analysis(self) -> None:
        """Test decision trail analysis."""
        decision_trails = self.pattern_recognizer.analyze_decision_trails(
            self.test_messages
        )

        assert isinstance(decision_trails, list)

        for trail in decision_trails:
            assert isinstance(trail, dict)
            assert "decision_point" in trail
            assert "decision_quality" in trail

    def test_problem_solution_detection(self) -> None:
        """Test problem-solution pair detection."""
        problem_solution_pairs = self.pattern_recognizer.detect_problem_solution_pairs(
            self.test_messages
        )

        assert isinstance(problem_solution_pairs, list)

        for pair in problem_solution_pairs:
            assert isinstance(pair, dict)
            assert "problem_message" in pair
            assert "solution_message" in pair
            assert "resolution_time" in pair

    def test_workflow_pattern_identification(self) -> None:
        """Test workflow pattern identification."""
        workflow_patterns = self.pattern_recognizer.identify_workflow_patterns(
            self.test_messages
        )

        assert isinstance(workflow_patterns, list)

        for workflow in workflow_patterns:
            assert isinstance(workflow, dict)
            assert "type" in workflow
            assert "efficiency" in workflow
            assert "messages" in workflow

    def test_context_switch_detection(self) -> None:
        """Test context switch detection."""
        context_switches = self.pattern_recognizer.detect_context_switches(
            self.test_messages
        )

        assert isinstance(context_switches, list)

        for switch in context_switches:
            assert isinstance(switch, dict)
            assert "from_context" in switch
            assert "to_context" in switch
            assert "timestamp" in switch

    def test_pattern_confidence_calculation(self) -> None:
        """Test pattern confidence calculation."""
        # Create a test pattern
        from domain_models.chat_models import ConversationPattern

        pattern = ConversationPattern(
            pattern_type="test_pattern",
            description="Test pattern for confidence calculation",
            frequency=5,
            confidence=0.7,
            evidence_entries=[msg.id for msg in self.test_messages],
        )

        confidence = self.pattern_recognizer.calculate_pattern_confidence(
            pattern, self.test_messages
        )

        assert isinstance(confidence, float)
        assert confidence >= 0.0
        assert confidence <= 1.0


class TestCLIProcessor(unittest.TestCase):
    """Test CLI processor functionality."""

    def setUp(self) -> None:
        """Set up test environment."""
        from components.cli_interface.enhanced_cli import EnhancedCLIProcessor

        self.cli_processor = EnhancedCLIProcessor()

    def test_natural_language_query_parsing(self) -> None:
        """Test natural language query parsing."""
        queries = [
            "find python errors from last week",
            "analyze patterns in technical discussions",
            "show me docker issues as json",
            "help me understand database performance",
        ]

        for query in queries:
            parsed = self.cli_processor.parse_natural_language_query(query)

            assert isinstance(parsed, dict)
            assert "intent" in parsed
            assert "search_terms" in parsed
            assert "entities" in parsed
            assert "confidence" in parsed

            assert parsed["confidence"] > 0.0
            assert parsed["confidence"] <= 1.0

    def test_intent_classification(self) -> None:
        """Test intent classification."""
        test_cases = [
            ("find python errors", "search"),
            ("analyze conversation patterns", "analyze"),
            ("compare docker vs kubernetes", "compare"),
            ("export results as json", "export"),
            ("help me search", "help"),
            ("system status", "status"),
        ]

        for query, expected_intent in test_cases:
            intent = self.cli_processor.classify_intent(query)
            assert intent == expected_intent

    def test_entity_extraction(self) -> None:
        """Test entity extraction."""
        query = "find python errors from last week in technical context as json"
        entities = self.cli_processor.extract_entities(query)

        assert isinstance(entities, dict)

        # Check for expected entities
        assert "technical_terms" in entities
        assert "time_period" in entities
        assert "context" in entities
        assert "format" in entities

    def test_query_suggestions(self) -> None:
        """Test query improvement suggestions."""
        query = "python"
        context = {"recent_searches": []}

        suggestions = self.cli_processor.suggest_query_improvements(query, context)

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

    def test_result_formatting(self) -> None:
        """Test result formatting."""
        from domain_models.chat_models import ChatMessage, SearchResult

        results = [
            SearchResult(
                message=ChatMessage(
                    content="Test search result about Python",
                    timestamp=int(datetime.now().timestamp() * 1000),
                ),
                relevance_score=0.8,
            ),
        ]

        formats = ["text", "json", "markdown", "table", "summary"]
        for format_type in formats:
            formatted = self.cli_processor.format_results(results, format_type)
            assert isinstance(formatted, str)
            assert len(formatted) > 0


class TestExportIntegration(unittest.TestCase):
    """Test export integration functionality."""

    def setUp(self) -> None:
        """Set up test environment."""
        from components.export_integration.knowledge_exporter import (
            EnhancedKnowledgeExporter,
        )

        self.exporter = EnhancedKnowledgeExporter()
        self.temp_dir = tempfile.mkdtemp()

    def test_search_results_export(self) -> None:
        """Test search results export."""

        results = [
            SearchResult(
                message=ChatMessage(
                    content="Test search result",
                    timestamp=int(datetime.now().timestamp() * 1000),
                ),
                relevance_score=0.8,
            ),
        ]

        config = ExportConfiguration(
            format="json",
            output_path=str(Path(self.temp_dir) / "test_results.json"),
        )

        success = self.exporter.export_search_results(results, config)
        assert success

        # Verify file was created
        assert Path(config.output_path).exists()

    def test_patterns_export(self) -> None:
        """Test patterns export."""

        patterns = [
            ConversationPattern(
                pattern_type="test_pattern",
                description="Test pattern for export",
                frequency=5,
                confidence=0.8,
            ),
        ]

        config = ExportConfiguration(
            format="json",
            output_path=str(Path(self.temp_dir) / "test_patterns.json"),
        )

        success = self.exporter.export_patterns(patterns, config)
        assert success

        # Verify file was created
        assert Path(config.output_path).exists()

    def test_temporal_analysis_export(self) -> None:
        """Test temporal analysis export."""
        from domain_models.chat_models import TemporalMetrics

        metrics = [
            TemporalMetrics(
                time_bucket="2023-01-01",
                scale=TemporalScale.DAILY,
                message_count=10,
                intensity_average=0.7,
            ),
        ]

        config = ExportConfiguration(
            format="json",
            output_path=str(Path(self.temp_dir) / "test_temporal.json"),
        )

        success = self.exporter.export_temporal_analysis(metrics, config)
        assert success

        # Verify file was created
        assert Path(config.output_path).exists()

    def test_knowledge_graph_export(self) -> None:
        """Test knowledge graph export."""
        from domain_models.chat_models import KnowledgeGraph

        graph = KnowledgeGraph()
        graph.add_node("test_node", {"type": "test"})
        graph.add_edge("node1", "node2", {"weight": 0.5})

        config = ExportConfiguration(
            format="json",
            output_path=str(Path(self.temp_dir) / "test_graph.json"),
        )

        success = self.exporter.export_knowledge_graph(graph, config)
        assert success

        # Verify file was created
        assert Path(config.output_path).exists()

    def test_evidence_tracking(self) -> None:
        """Test evidence tracking."""
        query = "python errors"

        results = [
            SearchResult(
                message=ChatMessage(
                    content="Python error with traceback",
                    timestamp=int(datetime.now().timestamp() * 1000),
                ),
                relevance_score=0.8,
                matched_terms=["python", "error"],
            ),
        ]

        evidence = self.exporter.evidence_tracker.collect_evidence(query, results)

        assert isinstance(evidence, dict)
        assert "query_terms" in evidence
        assert "matched_content" in evidence
        assert "semantic_sources" in evidence
        assert "temporal_context" in evidence

    def tearDown(self) -> None:
        """Clean up test environment."""

        shutil.rmtree(self.temp_dir)


class TestEnhancedChatAnalyzer(unittest.TestCase):
    """Test main enhanced chat analyzer."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {
            "project_root": self.temp_dir,
        }
        self.analyzer = create_enhanced_chat_analyzer(self.config)

    def test_analyzer_initialization(self) -> None:
        """Test analyzer initialization."""
        assert isinstance(self.analyzer, EnhancedChatAnalyzer)
        assert isinstance(self.analyzer, IChatAnalyzer)

        # Check components are initialized
        assert self.analyzer.storage_engine is not None
        assert self.analyzer.temporal_analyzer is not None
        assert self.analyzer.semantic_engine is not None
        assert self.analyzer.pattern_recognizer is not None
        assert self.analyzer.cli_processor is not None
        assert self.analyzer.export_integration is not None

    def test_system_status(self) -> None:
        """Test system status retrieval."""
        status = self.analyzer.get_system_status()

        assert isinstance(status, dict)
        assert "analyzer" in status
        assert "storage_engine" in status
        assert "components" in status
        assert "features" in status

        # Check analyzer status
        analyzer_status = status["analyzer"]
        assert analyzer_status["status"] == "ready"
        assert analyzer_status["version"] == "2.0"

        # Check features
        features = status["features"]
        assert features["enhanced_search"]
        assert features["temporal_analysis"]
        assert features["semantic_analysis"]
        assert features["pattern_recognition"]

    def test_natural_language_query_processing(self) -> None:
        """Test natural language query processing."""
        # Mock the legacy searcher to avoid dependency on actual chat history
        with patch.object(self.analyzer.legacy_searcher, "search") as mock_search:
            mock_search.return_value = []

            session = self.analyzer.process_natural_language_query("test python query")

            assert isinstance(session, AnalysisSession)
            assert session.query == "test python query"
            assert "filters" in session.session_metadata
            assert session.validation_status == "validated"

    def test_pattern_analysis(self) -> None:
        """Test pattern analysis functionality."""
        # Create test messages
        test_messages = [
            ChatMessage(
                content="Test message for pattern analysis",
                timestamp=int(datetime.now().timestamp() * 1000),
            ),
        ]

        session = self.analyzer.analyze_patterns(messages=test_messages)

        assert isinstance(session, AnalysisSession)
        assert session.query == "comprehensive_pattern_analysis"
        assert session.validation_status == "validated"
        assert session.confidence_score > 0.0

    def test_export_functionality(self) -> None:
        """Test export functionality."""
        from domain_models.chat_models import AnalysisSession

        session = AnalysisSession(query="test query")
        session.results = []

        config = ExportConfiguration(
            format="json",
            output_path=str(Path(self.temp_dir) / "test_export.json"),
        )

        success = self.analyzer.export_analysis(session, config)
        assert success

    def test_performance_optimization(self) -> None:
        """Test system optimization."""
        success = self.analyzer.optimize_system()
        assert success

        # Check performance metrics are reset
        metrics = self.analyzer.performance_metrics
        assert metrics["total_queries"] == 0
        assert metrics["cache_hits"] == 0
        assert metrics["cache_misses"] == 0

    def test_csf_nip_integration(self) -> None:
        """Test CSF NIP integration (mocked)."""

        session = AnalysisSession(query="test query")
        session.patterns = []

        # Mock the CSF NIP integration
        with patch.object(
            self.analyzer.export_integration, "integrate_with_csf_nip"
        ) as mock_integrate:
            mock_integrate.return_value = True

            success = self.analyzer.export_integration.integrate_with_csf_nip(session)
            assert success

    def tearDown(self) -> None:
        """Clean up test environment."""

        shutil.rmtree(self.temp_dir)


class TestIntegrationValidation(unittest.TestCase):
    """Integration tests for component validation."""

    def setUp(self) -> None:
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = {"project_root": self.temp_dir}
        self.analyzer = create_enhanced_chat_analyzer(self.config)

    def test_end_to_end_search_workflow(self) -> None:
        """Test complete search workflow."""
        # Mock legacy searcher
        with patch.object(self.analyzer.legacy_searcher, "search") as mock_search:
            mock_search.return_value = [
                {
                    "display": "Python code example",
                    "timestamp": int(datetime.now().timestamp() * 1000),
                    "project": "test_project",
                    "relevance_score": 0.8,
                    "matched_tokens": ["python", "code"],
                },
            ]

            # Perform search
            results = self.analyzer.search_chat_history(
                query="python code examples",
                ranking=SearchRanking.RELEVANCE,
                limit=10,
            )

            assert isinstance(results, list)
            assert len(results) > 0

            for result in results:
                assert isinstance(result, SearchResult)
                assert isinstance(result.message, ChatMessage)
                assert result.relevance_score > 0.0

    def test_end_to_end_analysis_workflow(self) -> None:
        """Test complete analysis workflow."""
        # Create test messages
        test_messages = [
            ChatMessage(
                content="Python function for data processing",
                timestamp=int(datetime.now().timestamp() * 1000),
                semantic_tags=["python", "data"],
            ),
            ChatMessage(
                content="Error handling in Python code",
                timestamp=int((datetime.now() + timedelta(hours=1)).timestamp() * 1000),
                semantic_tags=["python", "error"],
            ),
        ]

        # Perform analysis
        session = self.analyzer.analyze_patterns(messages=test_messages)

        # Verify analysis results
        assert isinstance(session, AnalysisSession)
        assert session.validation_status == "validated"
        assert session.confidence_score > 0.0

        # Check components are populated
        if session.temporal_metrics:
            assert isinstance(session.temporal_metrics, list)

        if session.knowledge_graph:
            assert isinstance(session.knowledge_graph, KnowledgeGraph)

        if session.patterns:
            assert isinstance(session.patterns, list)

    def test_export_integration_workflow(self) -> None:
        """Test export integration workflow."""
        # Create test session
        from domain_models.chat_models import AnalysisSession, ChatMessage, SearchResult

        session = AnalysisSession(query="integration test")
        session.results = [
            SearchResult(
                message=ChatMessage(content="Test result"),
                relevance_score=0.8,
            ),
        ]

        # Test export
        output_path = Path(self.temp_dir) / "integration_test.json"
        config = ExportConfiguration(
            format="json",
            output_path=str(output_path),
            include_analysis=True,
            include_evidence=True,
        )

        success = self.analyzer.export_analysis(session, config)
        assert success

        # Verify file exists and has content
        assert output_path.exists()
        assert output_path.stat().st_size > 0

        # Verify JSON structure
        with open(output_path) as f:
            exported_data = json.load(f)
            assert "export_metadata" in exported_data
            assert "data" in exported_data

    def test_caching_integration(self) -> None:
        """Test caching integration across components."""
        # Mock legacy searcher
        with patch.object(self.analyzer.legacy_searcher, "search") as mock_search:
            mock_search.return_value = []

            query = "test caching query"
            filters = {"context_filter": "technical"}

            # First call - should be cache miss
            self.analyzer.search_chat_history(query, filters, limit=5)
            cache_misses = self.analyzer.performance_metrics["cache_misses"]
            cache_hits = self.analyzer.performance_metrics["cache_hits"]

            # Second call - should be cache hit
            self.analyzer.search_chat_history(query, filters, limit=5)

            # Verify caching behavior
            assert self.analyzer.performance_metrics["cache_misses"] == cache_misses
            assert self.analyzer.performance_metrics["cache_hits"] > cache_hits

    def tearDown(self) -> None:
        """Clean up integration test environment."""

        shutil.rmtree(self.temp_dir)


def run_validation_suite() -> bool:
    """Run complete validation suite."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    test_classes = [
        TestEnhancedStorageEngine,
        TestTemporalAnalyzer,
        TestSemanticEngine,
        TestPatternRecognizer,
        TestCLIProcessor,
        TestExportIntegration,
        TestEnhancedChatAnalyzer,
        TestIntegrationValidation,
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary

    if result.failures:
        for _test, _traceback in result.failures:
            pass

    if result.errors:
        for _test, _traceback in result.errors:
            pass

    return bool(result.wasSuccessful())


if __name__ == "__main__":
    success = run_validation_suite()
    sys.exit(0 if success else 1)
