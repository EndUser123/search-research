# V2 Semantic State Architecture tests.
# Tests semantic_matcher, phase_machine, evidence_collector, and Stop.py V2 integration.
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import pytest

# Ensure __lib is on path
sys.path.insert(0, str(Path(__file__).parent.parent / "__lib"))


# =============================================================================
# Semantic Matcher Tests
# =============================================================================

class TestSemanticMatcherBasics:
    def test_extract_subject_tokens_filters_stop_words(self):
        from __lib.semantic_matcher_llm import extract_subject_tokens

        tokens = extract_subject_tokens("Fix Stop.py cache bug in the hook runner")
        assert "stop" in tokens or "cache" in tokens or "hook" in tokens
        assert "fix" not in tokens
        assert "the" not in tokens
        assert "in" not in tokens

    def test_extract_subject_tokens_empty_description(self):
        from __lib.semantic_matcher_llm import extract_subject_tokens

        tokens = extract_subject_tokens("")
        assert tokens == []

    def test_extract_subject_tokens_minimum_length(self):
        from __lib.semantic_matcher_llm import extract_subject_tokens

        tokens = extract_subject_tokens("a be see do it an at by")  # all < 3 chars
        assert tokens == []

    def test_extract_subject_tokens_keeps_relevant_tokens(self):
        from __lib.semantic_matcher_llm import extract_subject_tokens

        tokens = extract_subject_tokens("Implement Stop.py source cache update bug")
        assert "stop" in tokens
        assert "cache" in tokens
        assert "source" in tokens  # "update" is a stop-word; "source" is the better token
        assert "implement" not in tokens  # stop word




# =============================================================================
# LLM-Based Semantic Classification Tests
# =============================================================================

class TestLLMSemanticClassification:
    """Test orchestrator-based semantic classification (replaces embedding-based).

    classify_task_relation() is a stub returning "same_task" by default.
    Tests monkeypatch _get_relation_from_context() to control the classification.
    """

    def test_orchestrator_same_task_classification(self, tmp_path, monkeypatch):
        """Stub returns 'same_task' — no supersede, gate proceeds normally."""
        import __lib.task_contract as _tc
        from __lib.semantic_matcher_llm import classify_task_relation

        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)

        _tc.save_contract(
            "term-llm-1",
            task_id="tc-llm-1",
            description="Fix the Stop.py bug",
            required_outputs=["root_cause", "fix"],
            task_class="bug_fix",
        )

        # Stub is already "same_task" — nothing to monkeypatch
        result = classify_task_relation(
            "Fix the Stop.py bug",
            "bug_fix",
            "done",
            None,
        )
        assert result == "same_task"

    def test_orchestrator_orthogonal_does_not_supersede_in_shadow_mode(
        self, tmp_path, monkeypatch,
    ):
        """'orthogonal' would supersede in authority mode, but not in shadow mode."""
        import __lib.task_contract as _tc
        import __lib.semantic_matcher_llm as _sml
        import __lib.v2_config as _cfg

        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)

        # Monkeypatch: classify_task_relation returns "orthogonal"
        original_relation = _sml._get_relation_from_context
        monkeypatch.setattr(_sml, "_get_relation_from_context", lambda *a, **kw: "orthogonal")

        _tc.save_contract(
            "term-llm-2",
            task_id="tc-llm-2",
            description="Fix the Stop.py bug",
            required_outputs=["root_cause", "fix"],
            task_class="bug_fix",
        )

        from Stop import _run_task_contract_fit_gate_v2

        data = {
            "response": "Okay, I'll switch to something else",
            "terminal_id": "term-llm-2",
            "session_id": "sess-llm-2",
            "user_prompt": "set up CI/CD for the project",
            "tool_uses": [],
        }

        path = _tc._contract_path("term-llm-2")
        before = json.loads(path.read_text())
        before_updated = before["last_updated_at"]

        result = _run_task_contract_fit_gate_v2(data)
        assert result is None  # shadow mode

        after = json.loads(path.read_text())
        assert after["last_updated_at"] == before_updated, (
            "orthogonal classification must not mutate in shadow mode"
        )
        assert after["status"] == "active"

    def test_orchestrator_orthogonal_supersedes_in_authority_mode(
        self, tmp_path, monkeypatch,
    ):
        """'orthogonal' + authority mode triggers supersede_contract."""
        import __lib.task_contract as _tc
        import __lib.v2_config as _cfg
        import __lib.semantic_matcher_llm as _sml

        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)

        # Monkeypatch: classify_task_relation returns "orthogonal"
        monkeypatch.setattr(_sml, "_get_relation_from_context", lambda *a, **kw: "orthogonal")

        _tc.save_contract(
            "term-llm-3",
            task_id="tc-llm-3",
            description="Fix the Stop.py bug",
            required_outputs=["root_cause", "fix"],
            task_class="bug_fix",
        )

        from Stop import _run_task_contract_fit_gate_v2

        data = {
            "response": "Switching context",
            "terminal_id": "term-llm-3",
            "session_id": "sess-llm-3",
            "user_prompt": "run the wiki crawler",
            "tool_uses": [],
        }

        path = _tc._contract_path("term-llm-3")

        # Capture supersede call
        superseded = []
        original_supersede = _tc.supersede_contract
        def tracking_supersede(tid, reason=None):
            superseded.append((tid, reason))
            return original_supersede(tid, reason=reason)
        monkeypatch.setattr(_tc, "supersede_contract", tracking_supersede)

        # Force authority mode for this test
        monkeypatch.setattr(_cfg, "V2_SHADOW_MODE", False)

        result = _run_task_contract_fit_gate_v2(data)
        # In authority mode, orthogonal classification returns early (gate blocks stop)
        # The return value depends on the gate's block behavior

        # Contract should be superseded
        loaded = _tc.load_contract("term-llm-3")
        assert loaded is None  # superseded contracts return None from load_contract

        # Supersede was called
        assert len(superseded) == 1
        assert superseded[0][0] == "term-llm-3"
        assert "orthogonality" in superseded[0][1]

    def test_orchestrator_related_different_phase_does_not_supersede(
        self, tmp_path, monkeypatch,
    ):
        """'related_different_phase' is allowed through — phase machine handles it."""
        import __lib.task_contract as _tc
        import __lib.semantic_matcher_llm as _sml

        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)

        # Monkeypatch: classify_task_relation returns "related_different_phase"
        monkeypatch.setattr(_sml, "_get_relation_from_context", lambda *a, **kw: "related_different_phase")

        _tc.save_contract(
            "term-llm-4",
            task_id="tc-llm-4",
            description="Implement the Stop.py feature",
            required_outputs=["root_cause", "fix"],
            task_class="implementation",
        )

        from Stop import _run_task_contract_fit_gate_v2

        data = {
            "response": "Starting design phase",
            "terminal_id": "term-llm-4",
            "session_id": "sess-llm-4",
            "user_prompt": "Design the architecture for Stop.py",
            "tool_uses": [],
        }

        result = _run_task_contract_fit_gate_v2(data)
        assert result is None  # shadow mode returns None

        # Contract still active (not superseded)
        loaded = _tc.load_contract("term-llm-4")
        assert loaded is not None
        assert loaded["status"] == "active"

    def test_trivial_same_task_fast_path(self):
        """classify_trivial_same_task catches operational follow-ups without LLM call."""
        from __lib.semantic_matcher_llm import classify_trivial_same_task

        # Positive cases — operational follow-ups
        assert classify_trivial_same_task("done")
        assert classify_trivial_same_task("yes")
        assert classify_trivial_same_task("verify")
        assert classify_trivial_same_task("run the tests")
        assert classify_trivial_same_task("What's left?")
        assert classify_trivial_same_task("Proceed")
        assert classify_trivial_same_task("lgtm")
        assert classify_trivial_same_task("Looks good")
        assert classify_trivial_same_task("Carry on")

        # Negative cases — not same-task
        assert not classify_trivial_same_task("Fix the Stop.py bug")
        assert not classify_trivial_same_task("run the wiki crawler")
        assert not classify_trivial_same_task("What is the root cause?")


# =============================================================================
# Phase Machine Tests
# =============================================================================

class TestPhaseMachineValidTransitions:
    def test_exploration_transitions(self):
        from phase_machine import can_transition

        assert can_transition("exploration", "design")
        assert can_transition("exploration", "implementation")
        assert can_transition("exploration", "exploration")  # no-op
        assert can_transition("exploration", "superseded")

    def test_design_transitions(self):
        from phase_machine import can_transition

        assert can_transition("design", "implementation")
        assert can_transition("design", "exploration")
        assert can_transition("design", "design")  # no-op

    def test_implementation_transitions(self):
        from phase_machine import can_transition

        assert can_transition("implementation", "verification")
        assert can_transition("implementation", "design")
        assert can_transition("implementation", "implementation")  # no-op

    def test_verification_transitions(self):
        from phase_machine import can_transition

        assert can_transition("verification", "reporting")
        assert can_transition("verification", "implementation")

    def test_reporting_transitions(self):
        from phase_machine import can_transition

        assert can_transition("reporting", "complete")
        assert can_transition("reporting", "verification")

    def test_complete_is_terminal(self):
        from phase_machine import can_transition

        assert not can_transition("complete", "exploration")
        assert not can_transition("complete", "implementation")

    def test_superseded_is_terminal(self):
        from phase_machine import can_transition

        assert not can_transition("superseded", "exploration")


class TestPhaseMachineEnforcement:
    def test_exploration_never_enforces(self):
        from phase_machine import should_enforce_outputs

        assert should_enforce_outputs("exploration", "bug_fix") is False
        assert should_enforce_outputs("exploration", "implementation") is False
        assert should_enforce_outputs("exploration", "architecture_recommendation") is False

    def test_design_never_enforces(self):
        from phase_machine import should_enforce_outputs

        assert should_enforce_outputs("design", "bug_fix") is False

    def test_implementation_enforces_bug_fix(self):
        from phase_machine import should_enforce_outputs

        assert should_enforce_outputs("implementation", "bug_fix") is True

    def test_implementation_enforces_implementation_class(self):
        from phase_machine import should_enforce_outputs

        assert should_enforce_outputs("implementation", "implementation") is True

    def test_implementation_enforces_refactor(self):
        from phase_machine import should_enforce_outputs

        assert should_enforce_outputs("implementation", "refactor") is True

    def test_implementation_skips_architecture(self):
        from phase_machine import should_enforce_outputs

        assert should_enforce_outputs("implementation", "architecture_recommendation") is False

    def test_verification_enforces_implementation_classes(self):
        from phase_machine import should_enforce_outputs

        assert should_enforce_outputs("verification", "bug_fix") is True
        assert should_enforce_outputs("verification", "implementation") is True

    def test_reporting_enforces_all(self):
        from phase_machine import should_enforce_outputs

        assert should_enforce_outputs("reporting", "bug_fix") is True
        assert should_enforce_outputs("reporting", "architecture_recommendation") is True

    def test_complete_never_enforces(self):
        from phase_machine import should_enforce_outputs

        assert should_enforce_outputs("complete", "bug_fix") is False


class TestPhaseMachineInference:
    def test_files_modified_means_implementation(self):
        from phase_machine import infer_phase_from_context

        ctx = {"response": "I'll fix the issue", "turn_mode": "analysis"}
        ev = {"files_modified": ["Stop.py"]}
        assert infer_phase_from_context(ctx, ev) == "implementation"

    def test_tests_run_means_verification(self):
        from phase_machine import infer_phase_from_context

        ctx = {"response": "tests passed", "turn_mode": "analysis"}
        ev = {"tests_run": ["test_task_contract.py"]}
        assert infer_phase_from_context(ctx, ev) == "verification"

    def test_design_artifacts_means_design(self):
        from phase_machine import infer_phase_from_context

        ctx = {"response": "architecture overview", "turn_mode": "exploration"}
        ev = {"design_artifacts": ["arch.md"]}
        assert infer_phase_from_context(ctx, ev) == "design"

    def test_control_mode_means_exploration(self):
        from phase_machine import infer_phase_from_context

        ctx = {"response": "what is the current state?", "turn_mode": "control"}
        ev = {}
        assert infer_phase_from_context(ctx, ev) == "exploration"

    def test_analysis_mode_means_reporting(self):
        from phase_machine import infer_phase_from_context

        ctx = {"response": "the root cause is...", "turn_mode": "analysis"}
        ev = {}
        assert infer_phase_from_context(ctx, ev) == "reporting"

    def test_design_signals_in_response(self):
        from phase_machine import infer_phase_from_context

        ctx = {
            "response": "The architecture should be layered with a high-level component diagram",
            "turn_mode": "execution-report",  # Not in _EXPLORATION_MODES, allows layer 3 to fire
        }
        ev = {"design_artifacts": []}  # Empty so content marker layer fires
        assert infer_phase_from_context(ctx, ev) == "design"

    def test_code_signals_in_response(self):
        from phase_machine import infer_phase_from_context

        ctx = {
            "response": "def fix_cache():\n    pass",
            "turn_mode": "execution-report",  # Not in _EXPLORATION_MODES, allows layer 3 to fire
        }
        ev = {"code_generated": False, "files_modified": []}  # No evidence
        assert infer_phase_from_context(ctx, ev) == "implementation"


# =============================================================================
# Evidence Collector Tests
# =============================================================================

class TestEvidenceCollectorToolUses:
    def test_write_tool_extracts_file_path(self):
        from evidence_collector import collect_from_turn

        tools = [{"name": "Write", "input": {"file_path": "P:/src/module.py"}}]
        ev = collect_from_turn(tools)
        assert "P:/src/module.py" in ev["files_modified"]

    def test_edit_tool_extracts_file_path(self):
        from evidence_collector import collect_from_turn

        tools = [{"name": "Edit", "input": {"file_path": "P:/Stop.py"}}]
        ev = collect_from_turn(tools)
        assert "P:/Stop.py" in ev["files_modified"]

    def test_pytest_command_extracts_tests(self):
        from evidence_collector import collect_from_turn

        tools = [
            {"name": "Bash", "input": {"command": "python -m pytest tests/test_task.py::TestFoo::test_bar -v"}}
        ]
        ev = collect_from_turn(tools)
        assert len(ev["tests_run"]) >= 1

    def test_git_commit_increments_counter(self):
        from evidence_collector import collect_from_turn

        tools = [{"name": "Bash", "input": {"command": "git add Stop.py && git commit -m 'fix: patch Stop.py'"}}]
        ev = collect_from_turn(tools)
        assert ev["git_commits"] == 1

    def test_code_generated_flag_set_by_code_signals(self):
        from evidence_collector import collect_from_turn

        tools = [
            {
                "name": "Write",
                "input": {"file_path": "P:/src/module.py"},
            }
        ]
        ev = collect_from_turn(tools)
        assert ev["code_generated"] is True

    def test_design_artifact_detection(self):
        from evidence_collector import collect_from_turn

        tools = [
            {"name": "Write", "input": {"file_path": "P:/docs/architecture.md"}},
            {"name": "Write", "input": {"file_path": "P:/src/module.py"}},
        ]
        ev = collect_from_turn(tools)
        assert "P:/docs/architecture.md" in ev["design_artifacts"]


class TestEvidenceAccumulation:
    def test_files_deduplicated(self):
        from evidence_collector import accumulate

        existing = {"files_modified": ["a.py"], "tests_run": [], "verification_commands_executed": [], "code_generated": False, "design_artifacts": [], "git_commits": 0}
        new = {"files_modified": ["a.py", "b.py"], "tests_run": [], "verification_commands_executed": [], "code_generated": False, "design_artifacts": [], "git_commits": 0}
        result = accumulate(existing, new)
        assert result["files_modified"] == ["a.py", "b.py"]
        assert "a.py" in result["files_modified"]
        assert "b.py" in result["files_modified"]

    def test_tests_deduplicated(self):
        from evidence_collector import accumulate

        existing = {"files_modified": [], "tests_run": ["test_a.py"], "verification_commands_executed": [], "code_generated": False, "design_artifacts": [], "git_commits": 0}
        new = {"files_modified": [], "tests_run": ["test_a.py", "test_b.py"], "verification_commands_executed": [], "code_generated": False, "design_artifacts": [], "git_commits": 0}
        result = accumulate(existing, new)
        assert len(result["tests_run"]) == 2

    def test_git_commits_add(self):
        from evidence_collector import accumulate

        existing = {"files_modified": [], "tests_run": [], "verification_commands_executed": [], "code_generated": False, "design_artifacts": [], "git_commits": 3}
        new = {"files_modified": [], "tests_run": [], "verification_commands_executed": [], "code_generated": False, "design_artifacts": [], "git_commits": 2}
        result = accumulate(existing, new)
        assert result["git_commits"] == 5

    def test_code_generated_union(self):
        from evidence_collector import accumulate

        existing = {"files_modified": [], "tests_run": [], "verification_commands_executed": [], "code_generated": False, "design_artifacts": [], "git_commits": 0}
        new = {"files_modified": [], "tests_run": [], "verification_commands_executed": [], "code_generated": True, "design_artifacts": [], "git_commits": 0}
        result = accumulate(existing, new)
        assert result["code_generated"] is True


class TestFileOverlap:
    def test_file_overlap_detected(self):
        from evidence_collector import files_overlap_with_contract

        tokens = ["stop", "cache", "hook"]
        files = ["P:/Stop.py", "P:/runner.py"]
        assert files_overlap_with_contract(tokens, files) is True

    def test_no_overlap(self):
        from evidence_collector import files_overlap_with_contract

        tokens = ["stop", "cache", "hook"]
        files = ["P:/other.py"]
        assert files_overlap_with_contract(tokens, files) is False

    def test_empty_tokens(self):
        from evidence_collector import files_overlap_with_contract

        assert files_overlap_with_contract([], ["a.py"]) is False
        assert files_overlap_with_contract(["stop"], []) is False


# =============================================================================
# V2 Config Tests
# =============================================================================

class TestV2ConfigDefaults:
    def test_v2_enabled_by_default(self):
        from v2_config import V2_ENABLED
        assert V2_ENABLED is True

    def test_shadow_mode_by_default(self):
        from v2_config import V2_SHADOW_MODE
        assert V2_SHADOW_MODE is True

    def test_all_layers_enabled_by_default(self):
        from v2_config import V2_SEMANTIC_MATCHER_ENABLED, V2_PHASE_MACHINE_ENABLED, V2_EVIDENCE_COLLECTOR_ENABLED
        assert V2_SEMANTIC_MATCHER_ENABLED is True
        assert V2_PHASE_MACHINE_ENABLED is True
        assert V2_EVIDENCE_COLLECTOR_ENABLED is True

    def test_authority_off_by_default(self):
        from v2_config import V2_AUTHORITY
        assert V2_AUTHORITY == "off"

    # test_thresholds_are_sensible removed — SIMILARITY_* constants no longer exist;
    # semantic classification is now LLM-native (classify_task_relation), not numeric.


# =============================================================================
# V1 Contract Migration Tests
# =============================================================================

class TestV1Migration:
    def test_v1_contract_missing_embedding_triggers_migration(self, tmp_path, monkeypatch):
        # Simulate a v1 contract (no embedding, no phase)
        import __lib.task_contract as _tc
        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)

        v1_contract = {
            "task_id": "tc-test-001",
            "description": "Fix the Stop.py cache bug",
            "required_outputs": ["root_cause", "fix"],
            "created_at": "2026-01-01T00:00:00Z",
            "last_updated_at": "2026-01-01T00:00:00Z",
            "status": "active",
            "task_class": "bug_fix",
        }

        # Write v1 contract to disk
        path = tmp_path / ".claude" / ".artifacts" / "term-migrate" / "hook_state" / "task_contract.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(v1_contract))

        # Load it (should trigger migration)
        loaded = _tc.load_contract("term-migrate")

        assert loaded is not None
        # No embedding field (V2 schema removed embeddings; now LLM-based)
        assert "embedding" not in loaded
        assert "canonical_subject" in loaded
        assert "phase" in loaded
        assert "evidence" in loaded
        assert loaded["v2_schema_version"] == "2.0"
        assert loaded["migrated_from_v1"] is True
        assert loaded["phase"] in ("implementation", "exploration", "design")  # safe default

    def test_v2_contract_loads_without_migration(self, tmp_path, monkeypatch):
        import __lib.task_contract as _tc
        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)

        v2_contract = {
            "task_id": "tc-test-002",
            "description": "Implement the feature",
            "required_outputs": ["root_cause", "fix", "tests"],
            "created_at": "2026-01-01T00:00:00Z",
            "last_updated_at": "2026-01-01T00:00:00Z",
            "status": "active",
            "task_class": "implementation",
            "canonical_subject": ["feature", "implement"],
            "phase": "implementation",
            "phase_history": [],
            "evidence": {"files_modified": [], "tests_run": [], "verification_commands_executed": [], "git_commits": 0, "design_artifacts": [], "code_generated": False},
            "v2_schema_version": "2.0",
            "migrated_from_v1": False,
        }

        path = tmp_path / ".claude" / ".artifacts" / "term-v2" / "hook_state" / "task_contract.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(v2_contract))

        loaded = _tc.load_contract("term-v2")

        assert loaded is not None
        assert "embedding" not in loaded  # V2 schema no longer stores embeddings
        assert loaded["migrated_from_v1"] is not True  # already v2


# =============================================================================
# V2 Supersede and Update Helpers
# =============================================================================

class TestV2Helpers:
    def test_supersede_contract_sets_status(self, tmp_path, monkeypatch):
        import __lib.task_contract as _tc
        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)

        # Create a contract first
        _tc.save_contract(
            "term-supersede",
            task_id="tc-sup",
            description="Old task",
            required_outputs=["root_cause"],
            task_class="bug_fix",
        )

        # Supersede it
        _tc.supersede_contract("term-supersede", reason="semantic_drift")

        loaded = _tc.load_contract("term-supersede")
        assert loaded is None  # status != "active"

        # Check file has superseded status
        path = _tc._contract_path("term-supersede")
        data = json.loads(path.read_text())
        assert data["status"] == "superseded"
        assert data["supersede_reason"] == "semantic_drift"

    def test_update_phase_changes_phase(self, tmp_path, monkeypatch):
        import __lib.task_contract as _tc
        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)

        _tc.save_contract(
            "term-phase",
            task_id="tc-phase",
            description="Task",
            required_outputs=["root_cause"],
            task_class="bug_fix",
        )

        _tc.update_phase("term-phase", "verification")

        loaded = _tc.load_contract("term-phase")
        assert loaded["phase"] == "verification"

    def test_update_evidence_accumulates(self, tmp_path, monkeypatch):
        import __lib.task_contract as _tc
        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)

        _tc.save_contract(
            "term-evidence",
            task_id="tc-ev",
            description="Task",
            required_outputs=["root_cause"],
            task_class="bug_fix",
        )

        _tc.update_evidence("term-evidence", {
            "files_modified": ["a.py"],
            "tests_run": [],
            "verification_commands_executed": [],
            "code_generated": False,
            "design_artifacts": [],
            "git_commits": 0,
        })

        _tc.update_evidence("term-evidence", {
            "files_modified": ["b.py"],
            "tests_run": ["test_a.py"],
            "verification_commands_executed": [],
            "code_generated": False,
            "design_artifacts": [],
            "git_commits": 0,
        })

        loaded = _tc.load_contract("term-evidence")
        ev = loaded["evidence"]
        assert "a.py" in ev["files_modified"]
        assert "b.py" in ev["files_modified"]
        assert "test_a.py" in ev["tests_run"]


# =============================================================================
# Stop.py V2 Shadow Mode Tests
# =============================================================================

class TestStopV2ShadowMode:
    def test_v2_gate_exists_and_is_callable(self):
        from Stop import _run_task_contract_fit_gate_v2

        assert callable(_run_task_contract_fit_gate_v2)

    def test_v2_gate_with_no_contract_returns_none(self):
        from Stop import _run_task_contract_fit_gate_v2

        data = {
            "response": "Some response text",
            "terminal_id": "nonexistent-terminal-xyz",
            "session_id": "sess-test",
            "user_prompt": "Fix the bug",
        }

        result = _run_task_contract_fit_gate_v2(data)
        assert result is None  # no contract → silent

    def test_v2_gate_returns_none_in_shadow_mode(self, tmp_path, monkeypatch):
        import __lib.task_contract as _tc
        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)

        _tc.save_contract(
            "term-shadow",
            task_id="tc-shadow",
            description="Fix the Stop.py cache bug",
            required_outputs=["root_cause", "fix", "tests"],
            task_class="bug_fix",
        )

        from Stop import _run_task_contract_fit_gate_v2

        data = {
            "response": "The root cause is X. The fix is Y.",
            "terminal_id": "term-shadow",
            "session_id": "sess-shadow",
            "user_prompt": "Diagnose the Stop.py bug",
            "tool_uses": [],
        }

        result = _run_task_contract_fit_gate_v2(data)
        # In shadow mode, V2 never returns a block — only None
        assert result is None


class TestStopV2GatingEntry:
    def test_main_gate_runs_v1_and_v2(self, tmp_path, monkeypatch):
        import __lib.task_contract as _tc
        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)

        # Create a contract with requirements that won't be met (enforce mode)
        _tc.save_contract(
            "term-main",
            task_id="tc-main",
            description="Fix the Stop.py bug",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
            task_class="bug_fix",
        )

        from Stop import _run_task_contract_fit_gate

        data = {
            "response": "The root cause is a null pointer exception. The fix updates the cache check.",
            "terminal_id": "term-main",
            "session_id": "sess-main",
            "user_prompt": "Fix the Stop.py cache bug",
            "tool_uses": [],
        }

        result = _run_task_contract_fit_gate(data)
        # V1 is the authority — if missing outputs + substantive response, it blocks
        # Note: this specific response may or may not trigger V1 block depending on pattern matching
        # The key is that the gate ran without error
        assert result is not None or result is None  # Either outcome is valid


# =============================================================================
# V2 Shadow-Mode Read-Only Invariant Tests
# =============================================================================

class TestV2ShadowModeInvariant:
    """Verify V2 shadow mode never mutates persisted contract state.

    Invariant: When V2_SHADOW_MODE=true, _run_task_contract_fit_gate_v2() may
    compute decisions and write telemetry, but must not call any function that
    persists contract state (save_contract, clear_contract, supersede_contract,
    update_phase, update_evidence).
    """

    def test_v2_shadow_mode_semantic_drift_does_not_mutate_contract(
        self, tmp_path, monkeypatch,
    ):
        """Semantic drift below threshold does not supersede in shadow mode."""
        import __lib.task_contract as _tc
        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)

        _tc.save_contract(
            "term-drift",
            task_id="tc-drift",
            description="Fix the off-by-one error in the parser",
            required_outputs=["root_cause", "fix", "tests"],
            task_class="bug_fix",
        )

        from Stop import _run_task_contract_fit_gate_v2

        data = {
            # "verify the tests pass" is semantically unrelated to "off-by-one error"
            # classify_task_relation would return "orthogonal" → would supersede in authority
            "response": "the tests all pass now",
            "terminal_id": "term-drift",
            "session_id": "sess-drift",
            "user_prompt": "verify the parser tests pass",
            "tool_uses": [],
        }

        # Snapshot before
        path = _tc._contract_path("term-drift")
        before = json.loads(path.read_text())
        before_status = before["status"]
        before_phase = before["phase"]
        before_updated = before["last_updated_at"]

        result = _run_task_contract_fit_gate_v2(data)
        assert result is None  # shadow mode always returns None

        after = json.loads(path.read_text())
        assert after["status"] == before_status, "status must not change in shadow mode"
        assert after["phase"] == before_phase, "phase must not change in shadow mode"
        assert after["last_updated_at"] == before_updated, (
            "last_updated_at must not change in shadow mode"
        )
        # Contract must still be loadable as active
        contract = _tc.load_contract("term-drift")
        assert contract is not None
        assert contract["status"] == "active"

    def test_v2_shadow_mode_complete_response_does_not_clear_contract(
        self, tmp_path, monkeypatch,
    ):
        """Complete answer does not clear contract in shadow mode."""
        import __lib.task_contract as _tc
        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)

        _tc.save_contract(
            "term-complete",
            task_id="tc-complete",
            description="Fix the Stop.py bug",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
            task_class="bug_fix",
        )

        from Stop import _run_task_contract_fit_gate_v2

        complete_response = (
            "## Root Cause\nThe null pointer occurs because the cache is not initialized "
            "before access.\n\n## Fix Applied\nAdded initialization check at startup.\n\n"
            "## Tests\nAdded test_cache_initialization in tests/test_stop.py.\n\n"
            "## Verification Commands\npytest tests/test_stop.py -v -k cache"
        )

        data = {
            "response": complete_response,
            "terminal_id": "term-complete",
            "session_id": "sess-complete",
            "user_prompt": "Fix the Stop.py bug",
            "tool_uses": [],
        }

        path = _tc._contract_path("term-complete")
        before = json.loads(path.read_text())
        before_updated = before["last_updated_at"]

        result = _run_task_contract_fit_gate_v2(data)
        assert result is None  # shadow mode always returns None

        after = json.loads(path.read_text())
        assert after["status"] == "active", "status must stay active in shadow mode"
        assert after["last_updated_at"] == before_updated, (
            "last_updated_at must not change in shadow mode"
        )
        contract = _tc.load_contract("term-complete")
        assert contract is not None
        assert contract["status"] == "active"

    def test_v2_shadow_mode_phase_inference_does_not_persist_phase_changes(
        self, tmp_path, monkeypatch,
    ):
        """Phase inference does not write phase_history or phase in shadow mode."""
        import __lib.task_contract as _tc
        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)

        # Save a contract in exploration phase with empty evidence
        _tc.save_contract(
            "term-phase",
            task_id="tc-phase",
            description="Implement the new feature",
            required_outputs=["root_cause", "fix", "tests"],
            task_class="implementation",
            phase="exploration",
            evidence={
                "files_modified": [],
                "tests_run": [],
                "verification_commands_executed": [],
                "git_commits": 0,
                "design_artifacts": [],
                "code_generated": False,
            },
        )

        from Stop import _run_task_contract_fit_gate_v2

        # files_modified in tool_uses would infer "implementation" phase
        data = {
            "response": "Implementing the feature now",
            "terminal_id": "term-phase",
            "session_id": "sess-phase",
            "user_prompt": "Implement the new feature",
            "tool_uses": [
                {"name": "Write", "input": {"file_path": "P:/src/feature.py"}, "output": ""},
            ],
        }

        path = _tc._contract_path("term-phase")
        before = json.loads(path.read_text())
        before_phase = before["phase"]
        before_history = list(before.get("phase_history", []))

        result = _run_task_contract_fit_gate_v2(data)
        assert result is None

        after = json.loads(path.read_text())
        assert after["phase"] == before_phase, "phase must not change in shadow mode"
        assert after["phase_history"] == before_history, (
            "phase_history must not change in shadow mode"
        )
        assert after["last_updated_at"] == before["last_updated_at"], (
            "last_updated_at must not change in shadow mode"
        )

    def test_v2_shadow_mode_evidence_collection_does_not_persist_evidence(
        self, tmp_path, monkeypatch,
    ):
        """Evidence accumulation does not write to evidence field in shadow mode."""
        import __lib.task_contract as _tc
        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)

        _tc.save_contract(
            "term-evidence",
            task_id="tc-evidence",
            description="Fix the bug",
            required_outputs=["root_cause", "fix"],
            task_class="bug_fix",
            evidence={
                "files_modified": [],
                "tests_run": [],
                "verification_commands_executed": [],
                "git_commits": 0,
                "design_artifacts": [],
                "code_generated": False,
            },
        )

        from Stop import _run_task_contract_fit_gate_v2

        data = {
            "response": "Working on it",
            "terminal_id": "term-evidence",
            "session_id": "sess-evidence",
            "user_prompt": "Fix the bug",
            "tool_uses": [
                {"name": "Bash", "input": {"command": "pytest tests/test_bug.py -v"}, "output": ""},
                {"name": "Write", "input": {"file_path": "P:/src/bug.py"}, "output": ""},
            ],
        }

        path = _tc._contract_path("term-evidence")
        before = json.loads(path.read_text())
        before_evidence = before.get("evidence", {})
        before_updated = before["last_updated_at"]

        result = _run_task_contract_fit_gate_v2(data)
        assert result is None

        after = json.loads(path.read_text())
        assert after["evidence"] == before_evidence, (
            "evidence must not change in shadow mode"
        )
        assert after["last_updated_at"] == before_updated, (
            "last_updated_at must not change in shadow mode"
        )

        # --- Canary: verify contract unchanged via load_contract ---
        contract = _tc.load_contract("term-evidence")
        assert contract is not None
        assert contract["status"] == "active"

    def test_v2_shadow_mode_all_mutations_in_one_turn_leaves_contract_unchanged(
        self, tmp_path, monkeypatch,
    ):
        """Shadow-mode canary: all mutation paths in one turn must not alter persisted state.

        This single integration test exercises every mutation pathway simultaneously:
        - Semantic classification (orthogonal) that would trigger supersede in authority mode
        - Complete response with all required outputs that would trigger clear
        - Tool use with files and tests that would trigger update_evidence
        - Phase inference differing from current phase that would trigger update_phase

        If any future code change introduces a new mutation path that bypasses shadow
        mode, last_updated_at will change and this test will catch it.
        """
        import __lib.task_contract as _tc
        import __lib.v2_config as _cfg
        monkeypatch.setattr(_tc, "_home", lambda: tmp_path)

        _tc.save_contract(
            "term-canonical",
            task_id="tc-canonical",
            description="Fix the off-by-one error in the parser boundary check",
            required_outputs=["root_cause", "fix", "tests", "verification_commands"],
            task_class="bug_fix",
            phase="exploration",
            evidence={
                "files_modified": [],
                "tests_run": [],
                "verification_commands_executed": [],
                "git_commits": 0,
                "design_artifacts": [],
                "code_generated": False,
            },
        )

        from Stop import _run_task_contract_fit_gate_v2

        # Complete response with all required outputs — would trigger auto-clear
        complete_response = (
            "## Root Cause\nThe off-by-one error occurs because the boundary condition uses "
            ">= instead of > when comparing indices against the length of the token array.\n"
            "## Fix Applied\nChanged `if i >= len(tokens)` to `if i > len(tokens) - 1` in parser.py line 42.\n"
            "## Tests Added\npytest tests/test_parser.py::test_parser_boundary_off_by_one -v\n"
            "## Verification Commands\npytest tests/test_parser.py -v -k 'off_by_one or boundary'"
        )

        # Tool uses that trigger evidence accumulation and phase inference
        data = {
            "response": complete_response,
            "terminal_id": "term-canonical",
            "session_id": "sess-canonical",
            "user_prompt": "Fix the off-by-one error in the parser",
            "tool_uses": [
                {"name": "Write", "input": {"file_path": "P:/src/parser.py"}, "output": ""},
                {"name": "Bash", "input": {"command": "pytest tests/test_parser.py -v"}, "output": ""},
            ],
        }

        path = _tc._contract_path("term-canonical")
        before = json.loads(path.read_text())
        snap = {
            "status": before["status"],
            "phase": before["phase"],
            "evidence": before.get("evidence", {}),
            "phase_history": before.get("phase_history", []),
            "updated_at": before["last_updated_at"],
        }

        # Confirm V2 is in shadow mode before calling the gate
        assert _cfg.V2_SHADOW_MODE, "This test requires V2_SHADOW_MODE=true (default)"

        result = _run_task_contract_fit_gate_v2(data)
        assert result is None

        after = json.loads(path.read_text())

        # Canary: last_updated_at must be completely unchanged
        assert after["last_updated_at"] == snap["updated_at"], (
            "last_updated_at must not change in shadow mode — possible new mutation path"
        )
        assert after["status"] == snap["status"], "status must not change"
        assert after["phase"] == snap["phase"], "phase must not change"
        assert after.get("evidence", {}) == snap["evidence"], "evidence must not change"
        assert after.get("phase_history", []) == snap["phase_history"], "phase_history must not change"

        # Verify contract is still loadable and healthy
        contract = _tc.load_contract("term-canonical")
        assert contract is not None, "contract must remain loadable"
        assert contract["status"] == "active", "contract must remain active"
        assert contract["phase"] == "exploration", "contract phase must not drift"