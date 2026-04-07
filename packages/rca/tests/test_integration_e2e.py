#!/usr/bin/env python3
"""End-to-end integration tests for rca."""

import subprocess
import sys


class TestDebugRCAIntegration:
    """End-to-end rca workflow tests."""

    def test_package_import(self):
        """Test that rca package can be imported."""
        import rca
        assert rca is not None
        assert rca.__version__ == "2.5.0"

    def test_core_classes_import(self):
        """Test that core RCA classes can be imported."""
        from rca import (
            EvidenceSaturationDetector,
            HypothesisScorer,
            EvidenceLedger,
            ActionTracer,
        )
        assert EvidenceSaturationDetector is not None
        assert HypothesisScorer is not None
        assert EvidenceLedger is not None
        assert ActionTracer is not None

    def test_evidence_tier_classification(self):
        """Test evidence tier classification system."""
        from rca import EvidenceTier, EvidenceSource, get_lowest_tier
        source1 = EvidenceSource(
            source_type="user_report",
            description="User reported the issue",
            tier=EvidenceTier.TIER_1,
        )
        assert source1.tier == EvidenceTier.TIER_1
        sources = [source1]
        lowest_tier = get_lowest_tier(sources)
        assert lowest_tier == EvidenceTier.TIER_1

    def test_action_tracer_workflow(self):
        """Test action tracing workflow."""
        from rca import Action, ActionType, ActionTracer
        tracer = ActionTracer(session_id="test_session_001")
        action = tracer.record_action(
            action_type=ActionType.READ_FILE,
            tool_used="Read",
            tool_input={"file_path": "src/main.py"},
            tool_output="file content",
            phase=1,
        )
        assert action is not None
        assert action.action_type == ActionType.READ_FILE

    def test_evidence_ledger_workflow(self):
        """Test evidence ledger workflow."""
        from rca import EvidenceLedger, EvidenceTier, EvidenceSource
        ledger = EvidenceLedger()
        ledger.claim = "Test issue"
        source = EvidenceSource(
            source_type="error_log",
            description="Error occurred",
            tier=EvidenceTier.TIER_1,
        )
        ledger.add_evidence(source)
        assert len(ledger.sources) == 1

    def test_rca_engine_creation(self):
        """Test SimpleRCAEngine can be instantiated."""
        from rca import SimpleRCAEngine
        engine = SimpleRCAEngine()
        assert engine is not None
        assert hasattr(engine, "analyze_issue")

    def test_phase_state_manager(self):
        """Test phase state manager workflow."""
        from rca import PhaseStateManager
        manager = PhaseStateManager(enabled=False)
        state_id = manager.save("investigation", {"data": "test"}, "test_session")
        assert state_id == ""  # disabled returns empty

    def test_hypothesis_scorer(self):
        """Test hypothesis scoring workflow."""
        from rca import HypothesisScorer
        scorer = HypothesisScorer()
        hypothesis_id = scorer.add_hypothesis(
            "The error is caused by missing file permissions",
            reproducibility=0.8,
            recency=0.9,
            impact=0.7,
        )
        assert hypothesis_id is not None
        confidence = scorer.get_confidence(hypothesis_id)
        assert 0 <= confidence <= 1

    def test_convergence_validator(self):
        """Test convergence validation."""
        from rca import ConvergeValidator
        validator = ConvergeValidator()
        result = validator.validate(hypothesis_score=0.85)
        assert result is not None
        assert hasattr(result, "is_valid")
        assert hasattr(result, "hypothesis_score")

    def test_complete_rca_workflow(self):
        """Test complete RCA workflow from start to finish."""
        from rca import (
            ActionTracer,
            EvidenceLedger,
            EvidenceTier,
            EvidenceSource,
            HypothesisScorer,
            ConvergeValidator,
            ActionType,
        )
        session_id = "e2e_test_session"
        tracer = ActionTracer(session_id=session_id)
        ledger = EvidenceLedger()
        ledger.claim = "Test RCA"
        scorer = HypothesisScorer()
        validator = ConvergeValidator()
        evidence_source = EvidenceSource(
            source_type="error_log",
            description="Test error evidence",
            tier=EvidenceTier.TIER_1,
        )
        ledger.add_evidence(evidence_source)
        action = tracer.record_action(
            action_type=ActionType.READ_FILE,
            tool_used="Read",
            tool_input={"file_path": "test.py"},
            tool_output="file content",
            phase=1,
        )
        assert action is not None
        hypothesis_id = scorer.add_hypothesis(
            "Test hypothesis",
            reproducibility=0.8,
            recency=0.9,
            impact=0.7,
        )
        confidence = scorer.get_confidence(hypothesis_id)
        assert 0 <= confidence <= 1
        result = validator.validate(hypothesis_score=confidence)
        assert result is not None
        graph = tracer.get_action_graph()
        assert len(graph.actions) == 1
        assert len(ledger.sources) == 1

    def test_simple_rca_engine_analyze_issue(self):
        """Test that SimpleRCAEngine.analyze_issue() works end-to-end."""
        from rca import SimpleRCAEngine

        engine = SimpleRCAEngine()
        result = engine.analyze_issue(
            "Database connection failure in production environment",
            {"environment": "production", "technology": "postgresql"},
        )

        # Verify the result structure is valid
        assert result is not None
        assert hasattr(result, "issue")
        assert result.issue == "Database connection failure in production environment"
        assert hasattr(result, "fishbone_result")
        assert result.fishbone_result is not None
        assert hasattr(result, "fault_tree_result")
        assert result.fault_tree_result is not None
        assert hasattr(result, "overall_confidence")
        assert 0.0 <= result.overall_confidence <= 1.0
        assert hasattr(result, "actionable_recommendations")
        assert isinstance(result.actionable_recommendations, list)
