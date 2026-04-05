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
        assert rca.__version__ == "0.1.0"

    def test_core_classes_import(self):
        """Test that core RCA classes can be imported."""
        from rca import (
            EvidenceSaturationDetector,
            PhaseStateManager,
            HypothesisScorer,
            EvidenceLedger,
            ActionTracer,
        )
        assert EvidenceSaturationDetector is not None
        assert PhaseStateManager is not None
        assert HypothesisScorer is not None
        assert EvidenceLedger is not None
        assert ActionTracer is not None

    def test_evidence_tier_classification(self):
        """Test evidence tier classification system."""
        from rca import EvidenceTier, EvidenceSource, get_lowest_tier
        source1 = EvidenceSource(
            type="user_report",
            tier=EvidenceTier.TIER1_DIRECT_OBSERVATION,
            confidence=0.95,
        )
        assert source1.tier == EvidenceTier.TIER1_DIRECT_OBSERVATION
        sources = [source1]
        lowest_tier = get_lowest_tier(sources)
        assert lowest_tier == EvidenceTier.TIER1_DIRECT_OBSERVATION

    def test_action_tracer_workflow(self):
        """Test action tracing workflow."""
        from rca import Action, ActionType, ActionTracer
        tracer = ActionTracer(session_id="test_session_001")
        action1 = Action(
            action_type=ActionType.READ,
            target="src/main.py",
            timestamp="2026-02-25T10:00:00Z",
        )
        tracer.add_action(action1)
        actions = tracer.get_actions()
        assert len(actions) == 1
        assert actions[0].action_type == ActionType.READ

    def test_evidence_ledger_workflow(self):
        """Test evidence ledger workflow."""
        from rca import EvidenceLedger, EvidenceTier, EvidenceSource
        ledger = EvidenceLedger(session_id="test_session_002")
        source = EvidenceSource(
            type="error_log",
            tier=EvidenceTier.TIER1_DIRECT_OBSERVATION,
            confidence=0.9,
        )
        ledger.add_evidence(
            evidence_id="ev_001",
            source=source,
            content="Error: FileNotFoundError at line 42",
        )
        evidence = ledger.get_evidence("ev_001")
        assert evidence is not None
        assert evidence.content == "Error: FileNotFoundError at line 42"

    def test_rca_engine_creation(self):
        """Test SimpleRCAEngine can be instantiated."""
        from rca import SimpleRCAEngine
        engine = SimpleRCAEngine()
        assert engine is not None
        assert hasattr(engine, "analyze_issue")

    def test_phase_state_manager(self):
        """Test phase state manager workflow."""
        from rca import PhaseStateManager
        manager = PhaseStateManager(session_id="test_session_003")
        manager.initialize_phase("investigation")
        current_phase = manager.get_current_phase()
        assert current_phase == "investigation"
        manager.update_progress(0.5)
        progress = manager.get_progress()
        assert progress == 0.5
        manager.complete_phase()
        assert manager.is_phase_complete()

    def test_hypothesis_scorer(self):
        """Test hypothesis scoring workflow."""
        from rca import HypothesisScorer, EvidenceTier, EvidenceSource
        scorer = HypothesisScorer()
        hypothesis = "The error is caused by missing file permissions"
        evidence = [
            EvidenceSource(
                type="error_message",
                tier=EvidenceTier.TIER1_DIRECT_OBSERVATION,
                confidence=0.9,
            ),
        ]
        score = scorer.score_hypothesis(hypothesis, evidence)
        assert 0 <= score <= 1

    def test_metrics_tracker(self):
        """Test metrics tracking workflow."""
        from rca import RCAMetricsTracker, ProblemType
        tracker = RCAMetricsTracker(session_id="test_session_004")
        tracker.record_debug_start(
            problem_type=ProblemType.RUNTIME_ERROR,
            problem_description="Test error",
        )
        metrics = tracker.get_metrics()
        assert metrics is not None
        assert metrics.problem_type == ProblemType.RUNTIME_ERROR

    def test_convergence_validator(self):
        """Test convergence validation."""
        from rca import ConvergeValidator
        validator = ConvergeValidator()
        result = validator.validate(
            hypothesis="Test hypothesis",
            evidence=[],
            confidence_threshold=0.7,
        )
        assert result is not None
        assert hasattr(result, "is_converged")
        assert hasattr(result, "confidence")

    def test_complete_rca_workflow(self):
        """Test complete RCA workflow from start to finish."""
        from rca import (
            ActionTracer,
            EvidenceLedger,
            EvidenceTier,
            EvidenceSource,
            PhaseStateManager,
            HypothesisScorer,
            ConvergeValidator,
            Action,
            ActionType,
        )
        session_id = "e2e_test_session"
        tracer = ActionTracer(session_id=session_id)
        ledger = EvidenceLedger(session_id=session_id)
        phase_manager = PhaseStateManager(session_id=session_id)
        scorer = HypothesisScorer()
        validator = ConvergeValidator()
        phase_manager.initialize_phase("investigation")
        evidence_source = EvidenceSource(
            type="error_log",
            tier=EvidenceTier.TIER1_DIRECT_OBSERVATION,
            confidence=0.9,
        )
        ledger.add_evidence(
            evidence_id="ev_e2e_001",
            source=evidence_source,
            content="Test error evidence",
        )
        action = Action(
            action_type=ActionType.READ,
            target="test.py",
            timestamp="2026-02-25T10:00:00Z",
        )
        tracer.add_action(action)
        hypothesis = "Test hypothesis"
        evidence_list = [evidence_source]
        score = scorer.score_hypothesis(hypothesis, evidence_list)
        assert 0 <= score <= 1
        result = validator.validate(hypothesis, evidence_list, 0.7)
        assert result is not None
        actions = tracer.get_actions()
        assert len(actions) == 1
        all_evidence = ledger.get_all_evidence()
        assert len(all_evidence) == 1
        current_phase = phase_manager.get_current_phase()
        assert current_phase == "investigation"
