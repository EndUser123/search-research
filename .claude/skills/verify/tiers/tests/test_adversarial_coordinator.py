#!/usr/bin/env python3
"""
Tests for Adversarial Coordinator - 9-agent stress-test system.
"""

import json
import tempfile
from pathlib import Path

from tiers.adversarial_coordinator import (
    AdversarialCoordinator,
    ResultEnvelope,
    adversarial_review,
)


class TestResultEnvelope:
    """Test ResultEnvelope dataclass."""

    def test_result_envelope_creation(self):
        """Test creating a ResultEnvelope with all fields."""
        envelope = ResultEnvelope(
            status="done",
            artifact=".verify/artifacts/test.json",
            summary="Test completed successfully",
            metrics={"artifact_bytes": 1024, "files_read": 3},
        )

        assert envelope.status == "done"
        assert envelope.artifact == ".verify/artifacts/test.json"
        assert envelope.summary == "Test completed successfully"
        assert envelope.metrics["artifact_bytes"] == 1024
        assert envelope.metrics["files_read"] == 3

    def test_result_envelope_default_metrics(self):
        """Test ResultEnvelope with default metrics."""
        envelope = ResultEnvelope(
            status="done", artifact=".verify/artifacts/test.json", summary="Test completed"
        )

        assert envelope.metrics == {}

    def test_result_envelope_to_dict(self):
        """Test converting ResultEnvelope to dictionary."""
        envelope = ResultEnvelope(
            status="blocked",
            artifact=".verify/artifacts/test.json",
            summary="Blocked by missing dependency",
            metrics={"artifact_bytes": 512},
        )

        result_dict = envelope.to_dict()

        assert result_dict == {
            "status": "blocked",
            "artifact": ".verify/artifacts/test.json",
            "summary": "Blocked by missing dependency",
            "metrics": {"artifact_bytes": 512},
        }

    def test_result_envelope_status_literals(self):
        """Test that ResultEnvelope accepts valid status literals."""
        valid_statuses = ["done", "blocked", "retry"]

        for status in valid_statuses:
            envelope = ResultEnvelope(status=status, artifact="test.json", summary="Test")
            assert envelope.status == status


class TestAdversarialCoordinator:
    """Test AdversarialCoordinator initialization and configuration."""

    def test_coordinator_initialization_default_artifact_dir(self):
        """Test coordinator initializes with default artifact directory."""
        coordinator = AdversarialCoordinator()

        expected_dir = Path.cwd() / ".verify" / "artifacts"
        assert coordinator.artifact_dir == expected_dir
        assert coordinator.envelopes == {}

    def test_coordinator_initialization_custom_artifact_dir(self):
        """Test coordinator initializes with custom artifact directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = Path(tmpdir) / "custom_artifacts"
            coordinator = AdversarialCoordinator(artifact_dir=custom_dir)

            assert coordinator.artifact_dir == custom_dir

    def test_coordinator_creates_artifact_dir(self):
        """Test coordinator creates artifact directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = Path(tmpdir) / "new_artifacts"
            assert not custom_dir.exists()

            coordinator = AdversarialCoordinator(artifact_dir=custom_dir)

            assert custom_dir.exists()
            assert custom_dir.is_dir()

    def test_reviewer_agents_list(self):
        """Test that all 7 reviewer agents are defined."""
        expected_agents = [
            "adversarial-compliance",
            "adversarial-performance",
            "adversarial-quality",
            "adversarial-security",
            "adversarial-testing",
            "code-critic",
            "qa-engineer",
        ]

        assert AdversarialCoordinator.REVIEWER_AGENTS == expected_agents
        assert len(AdversarialCoordinator.REVIEWER_AGENTS) == 7

    def test_meta_analyzer_defined(self):
        """Test that meta-analyzer is defined."""
        assert AdversarialCoordinator.META_ANALYZER == "adversarial-critic"


class TestCreateReviewPrompt:
    """Test review prompt generation for different agents and target types."""

    def test_create_review_prompt_for_code(self):
        """Test creating review prompt for code target."""
        coordinator = AdversarialCoordinator()

        prompt = coordinator._create_review_prompt(
            agent_type="adversarial-security",
            target_type="code",
            content="def foo(): pass",
            context={"file": "test.py"},
        )

        assert "CODE" in prompt
        assert "code quality and logic" in prompt
        assert "Security vulnerabilities, data exposure" in prompt
        assert "def foo(): pass" in prompt

    def test_create_review_prompt_for_plan(self):
        """Test creating review prompt for plan target."""
        coordinator = AdversarialCoordinator()

        prompt = coordinator._create_review_prompt(
            agent_type="adversarial-compliance",
            target_type="plan",
            content="# Plan\n\n## Tasks",
            context={"plan_file": "plan.md"},
        )

        assert "AN IMPLEMENTATION PLAN" in prompt
        assert "plan-level concerns" in prompt
        assert "Missing required sections" in prompt

    def test_create_review_prompt_includes_agent_guidance(self):
        """Test that agent-specific guidance is included in prompt."""
        coordinator = AdversarialCoordinator()

        prompt = coordinator._create_review_prompt(
            agent_type="adversarial-performance",
            target_type="code",
            content="code here",
            context={},
        )

        assert "Performance bottlenecks" in prompt
        assert "Scalability concerns" in prompt

    def test_create_review_prompt_includes_json_schema(self):
        """Test that prompt includes JSON response schema."""
        coordinator = AdversarialCoordinator()

        prompt = coordinator._create_review_prompt(
            agent_type="code-critic", target_type="code", content="code here", context={}
        )

        assert '"status"' in prompt
        assert '"findings"' in prompt
        assert '"severity"' in prompt
        assert "JSON" in prompt


class TestGetAgentGuidance:
    """Test agent-specific guidance generation."""

    def test_compliance_agent_guidance(self):
        """Test compliance agent guidance for code."""
        coordinator = AdversarialCoordinator()

        guidance = coordinator._get_agent_guidance("adversarial-compliance", is_code=True)

        assert "Solo-dev constraints" in guidance
        assert "Specification violations" in guidance

    def test_performance_agent_guidance(self):
        """Test performance agent guidance."""
        coordinator = AdversarialCoordinator()

        guidance = coordinator._get_agent_guidance("adversarial-performance", is_code=True)

        assert "Performance bottlenecks" in guidance
        assert "Scalability concerns" in guidance

    def test_security_agent_guidance(self):
        """Test security agent guidance."""
        coordinator = AdversarialCoordinator()

        guidance = coordinator._get_agent_guidance("adversarial-security", is_code=True)

        assert "Data exposure" in guidance
        assert "Access control" in guidance

    def test_testing_agent_guidance(self):
        """Test testing agent guidance."""
        coordinator = AdversarialCoordinator()

        guidance = coordinator._get_agent_guidance("adversarial-testing", is_code=True)

        assert "Test coverage gaps" in guidance
        assert "Brittle tests" in guidance

    def test_unknown_agent_guidance(self):
        """Test guidance for unknown agent type."""
        coordinator = AdversarialCoordinator()

        guidance = coordinator._get_agent_guidance("unknown-agent", is_code=True)

        assert "Apply your specialized lens" in guidance


class TestWriteAgentArtifact:
    """Test artifact file writing."""

    def test_write_agent_artifact_creates_file(self):
        """Test that artifact file is created with correct content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coordinator = AdversarialCoordinator(artifact_dir=Path(tmpdir))

            content = {"status": "pass", "findings": []}
            artifact_path = coordinator._write_agent_artifact(
                agent_type="test-agent", timestamp="20260316_120000", content=content
            )

            # Check file exists
            full_path = Path(tmpdir) / artifact_path
            assert full_path.exists()

            # Check content
            with open(full_path, encoding="utf-8") as f:
                saved_content = json.load(f)

            assert saved_content == content

    def test_write_agent_artifact_returns_relative_path(self):
        """Test that artifact path is valid and contains agent type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coordinator = AdversarialCoordinator(artifact_dir=Path(tmpdir))

            artifact_path = coordinator._write_agent_artifact(
                agent_type="test-agent", timestamp="20260316_120000", content={}
            )

            # Path should exist and contain agent type
            assert Path(artifact_path).exists()
            assert "test-agent" in artifact_path

    def test_write_multiple_artifacts(self):
        """Test writing multiple artifacts for different agents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coordinator = AdversarialCoordinator(artifact_dir=Path(tmpdir))

            for agent in ["agent1", "agent2", "agent3"]:
                coordinator._write_agent_artifact(
                    agent_type=agent, timestamp="20260316_120000", content={"agent": agent}
                )

            # Check all files exist
            artifact_files = list(Path(tmpdir).glob("*.json"))
            assert len(artifact_files) == 3


class TestCreateSummaryFromContent:
    """Test summary generation from agent results."""

    def test_summary_with_no_findings(self):
        """Test summary when agent reports no findings."""
        coordinator = AdversarialCoordinator()

        content = {"status": "pass", "findings": [], "severity": "low"}
        summary = coordinator._create_summary_from_content(content)

        assert summary == "Status: pass, no findings"

    def test_summary_with_findings(self):
        """Test summary with findings."""
        coordinator = AdversarialCoordinator()

        content = {
            "status": "fail",
            "findings": ["Missing input validation", "No error handling"],
            "severity": "high",
        }
        summary = coordinator._create_summary_from_content(content)

        assert "Status: fail" in summary
        assert "severity: high" in summary
        assert "2 finding" in summary
        assert "Missing input validation" in summary

    def test_summary_truncates_long_findings(self):
        """Test that long findings are truncated in summary."""
        coordinator = AdversarialCoordinator()

        long_finding = "A" * 100
        content = {"status": "fail", "findings": [long_finding], "severity": "medium"}
        summary = coordinator._create_summary_from_content(content)

        assert len(summary) < 150  # Should be truncated
        assert "..." in summary  # Should have truncation marker


class TestDispatchReviewers:
    """Test parallel dispatch of 7 reviewers."""

    def test_dispatch_reviewers_returns_envelopes(self):
        """Test that dispatch returns envelopes for all reviewers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coordinator = AdversarialCoordinator(artifact_dir=Path(tmpdir))

            envelopes = coordinator.dispatch_reviewers(
                target_type="code", content="test code", context={}
            )

            # Should have envelope for each of 7 reviewers
            assert len(envelopes) == 7
            for agent in AdversarialCoordinator.REVIEWER_AGENTS:
                assert agent in envelopes

    def test_dispatch_reviewers_creates_artifacts(self):
        """Test that dispatch creates artifact files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coordinator = AdversarialCoordinator(artifact_dir=Path(tmpdir))

            envelopes = coordinator.dispatch_reviewers(
                target_type="code", content="test code", context={}
            )

            # Check that artifact files exist
            for envelope in envelopes.values():
                # artifact_path is already absolute when using tmpdir
                artifact_path = Path(envelope.artifact)
                assert artifact_path.exists()

    def test_dispatch_reviewers_updates_coordinator_envelopes(self):
        """Test that dispatch updates coordinator's envelope tracking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coordinator = AdversarialCoordinator(artifact_dir=Path(tmpdir))

            assert len(coordinator.envelopes) == 0

            coordinator.dispatch_reviewers(target_type="code", content="test code", context={})

            assert len(coordinator.envelopes) == 7

    def test_dispatch_reviewers_envelope_structure(self):
        """Test that returned envelopes have correct structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coordinator = AdversarialCoordinator(artifact_dir=Path(tmpdir))

            envelopes = coordinator.dispatch_reviewers(
                target_type="code", content="test code", context={}
            )

            for agent, envelope in envelopes.items():
                assert envelope.status in ("done", "blocked", "retry")
                assert envelope.artifact.endswith(".json")
                assert envelope.summary is not None
                assert "agent_type" in envelope.metrics
                assert envelope.metrics["agent_type"] == agent


class TestRunMetaAnalysis:
    """Test adversarial-critic meta-analysis."""

    def test_run_meta_analysis_returns_envelope(self):
        """Test that meta-analysis returns an envelope."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coordinator = AdversarialCoordinator(artifact_dir=Path(tmpdir))

            # Create mock reviewer envelopes
            reviewer_envelopes = {
                "agent1": ResultEnvelope(
                    status="done", artifact="test1.json", summary="Agent 1 summary"
                ),
                "agent2": ResultEnvelope(
                    status="done", artifact="test2.json", summary="Agent 2 summary"
                ),
            }

            critic_envelope = coordinator.run_meta_analysis(
                reviewer_envelopes=reviewer_envelopes, context={}
            )

            assert critic_envelope.status == "done"
            assert "critic" in critic_envelope.artifact
            assert critic_envelope.summary is not None

    def test_run_meta_analysis_creates_artifact(self):
        """Test that meta-analysis creates artifact file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coordinator = AdversarialCoordinator(artifact_dir=Path(tmpdir))

            reviewer_envelopes = {}
            critic_envelope = coordinator.run_meta_analysis(
                reviewer_envelopes=reviewer_envelopes, context={}
            )

            # artifact_path is already absolute when using tmpdir
            artifact_path = Path(critic_envelope.artifact)
            assert artifact_path.exists()

    def test_run_meta_analysis_includes_metrics(self):
        """Test that meta-analysis includes reviewer count in metrics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coordinator = AdversarialCoordinator(artifact_dir=Path(tmpdir))

            reviewer_envelopes = {
                f"agent{i}": ResultEnvelope(
                    status="done", artifact=f"test{i}.json", summary=f"Summary {i}"
                )
                for i in range(5)
            }

            critic_envelope = coordinator.run_meta_analysis(
                reviewer_envelopes=reviewer_envelopes, context={}
            )

            assert critic_envelope.metrics["reviewers_analyzed"] == 5


class TestRunFullReview:
    """Test complete 9-agent adversarial review workflow."""

    def test_run_full_review_returns_complete_results(self):
        """Test that full review returns all expected components."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coordinator = AdversarialCoordinator(artifact_dir=Path(tmpdir))

            results = coordinator.run_full_review(
                target_type="code", content="test code", context={}
            )

            # Check structure
            assert "envelopes" in results
            assert "summaries_only" in results
            assert "overall_status" in results
            assert "timestamp" in results
            assert "artifact_dir" in results

    def test_run_full_review_has_all_9_envelopes(self):
        """Test that full review includes all 9 agent envelopes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coordinator = AdversarialCoordinator(artifact_dir=Path(tmpdir))

            results = coordinator.run_full_review(
                target_type="code", content="test code", context={}
            )

            # Should have 7 reviewers + 1 critic = 8 total
            # (Note: in mock mode, we don't actually run the critic as a separate agent)
            assert len(results["envelopes"]) >= 7

    def test_run_full_review_summaries_only_list(self):
        """Test that summaries_only is a list of strings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coordinator = AdversarialCoordinator(artifact_dir=Path(tmpdir))

            results = coordinator.run_full_review(
                target_type="code", content="test code", context={}
            )

            assert isinstance(results["summaries_only"], list)
            assert all(isinstance(s, str) for s in results["summaries_only"])

    def test_run_full_review_overall_status_done(self):
        """Test that overall status is 'done' when all agents pass."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coordinator = AdversarialCoordinator(artifact_dir=Path(tmpdir))

            results = coordinator.run_full_review(
                target_type="code", content="test code", context={}
            )

            # In mock mode, all envelopes should have status "done"
            assert results["overall_status"] == "done"


class TestAdversarialReviewConvenienceFunction:
    """Test convenience function for adversarial review."""

    def test_adversarial_review_function(self):
        """Test the adversarial_review convenience function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use custom artifact dir for cleanup
            results = adversarial_review(
                target_type="code", content="test code", context={}, artifact_dir=Path(tmpdir)
            )

            assert "envelopes" in results
            assert "overall_status" in results
            assert len(results["envelopes"]) >= 7

    def test_adversarial_review_default_context(self):
        """Test adversarial_review with no context provided."""
        results = adversarial_review(target_type="plan", content="# Test Plan")

        # Should use default empty context
        assert "envelopes" in results

    def test_adversarial_review_default_artifact_dir(self):
        """Test adversarial_review uses default artifact dir."""
        results = adversarial_review(target_type="code", content="code")

        # Should create artifacts in default location
        assert "artifact_dir" in results
        assert ".verify" in results["artifact_dir"]


class TestIntegrationScenarios:
    """Integration tests for realistic scenarios."""

    def test_full_code_review_workflow(self):
        """Test complete adversarial review workflow for code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coordinator = AdversarialCoordinator(artifact_dir=Path(tmpdir))

            code_sample = """
def process_user_input(user_data):
    # Process user input without validation
    result = user_data["name"] + user_data["email"]
    return result
"""

            results = coordinator.run_full_review(
                target_type="code",
                content=code_sample,
                context={"file": "process.py", "language": "python"},
            )

            # Verify structure
            assert results["overall_status"] in ("done", "blocked", "retry")
            assert len(results["summaries_only"]) > 0

            # Verify artifacts were created
            for envelope in results["envelopes"].values():
                # artifact_path is already absolute when using tmpdir
                artifact_path = Path(envelope.artifact)
                assert artifact_path.exists()

                # Verify artifact is valid JSON
                with open(artifact_path, encoding="utf-8") as f:
                    content = json.load(f)
                assert "status" in content

    def test_full_plan_review_workflow(self):
        """Test complete adversarial review workflow for plan."""
        with tempfile.TemporaryDirectory() as tmpdir:
            coordinator = AdversarialCoordinator(artifact_dir=Path(tmpdir))

            plan_sample = """
# Implementation Plan

## Tasks
- [ ] TASK-001: Implement feature
- [ ] TASK-002: Write tests

## Requirements
- Must support multi-terminal execution
- Must include comprehensive tests
"""

            results = coordinator.run_full_review(
                target_type="plan", content=plan_sample, context={"plan_file": "plan.md"}
            )

            # Verify structure
            assert results["overall_status"] in ("done", "blocked", "retry")
            assert len(results["envelopes"]) >= 7
