#!/usr/bin/env python3
from __future__ import annotations

from posttooluse.base import HookRegistry, PostToolUseHook, is_block_result

# Artifact scraper - records locally-found artifacts into session ledger
from posttooluse.artifact_scraper import ArtifactScraperHook

# Agent contract validator - validates adversarial agent .md files on Write/Edit
from posttooluse.agent_contract_validator import AgentContractValidator

# Absorbed from standalone processes (wave 2 - eliminates 4 subprocess spawns)
from posttooluse.breadcrumb_tracker_hook import BreadcrumbTrackerHook
from posttooluse.change_propagation_hook import ChangePropagationHook

# Cleanup tracker - tracks tool usage for cleanup verification
from posttooluse.cleanup_tracker_hook import CleanupTrackerHook

# Auto-lint - absorbed from archived PostToolUse_lint_router.py
from posttooluse.completion_validator import CompletionValidator

# Edit verifier - verifies Write/Edit operations actually persisted to disk
from posttooluse.edit_verifier import EditVerifier

# E2E tracker - for end-to-end workflow tracking
from posttooluse.e2e_tracker_hook import E2ETrackerHook

# Enforcement tier validator - validates enforcement field in SKILL.md frontmatter
from posttooluse.enforcement_tier_validator import EnforcementTierValidator
from posttooluse.error_attribution_hook import ErrorAttributionHook
from posttooluse.error_attribution_tracker import ErrorAttributionTracker

# Absorbed from standalone processes (wave 1)
from posttooluse.evidence_tracker_hook import EvidenceTrackerHook
from posttooluse.failure_recorder_hook import FailureRecorderHook
from posttooluse.falsification_assessor import FalsificationAssessor
from posttooluse.file_activity_tracker_hook import FileActivityTrackerHook
from posttooluse.file_invalidation_tracker import FileInvalidationTrackerHook

# Original in-process hooks (kept)
from posttooluse.fix_validator import FixValidator
from posttooluse.implementation_verifier import ImplementationVerifier
from posttooluse.inherited_choice_hook import InheritedChoiceHook
from posttooluse.integration_verifier import IntegrationVerifier
from posttooluse.investigation_tracker import InvestigationTracker

# REMOVED: structurally disabled — lint_hook.py runs ruff --fix, corrupts code between sequential edits
# from posttooluse.lint_hook import LintHook
from posttooluse.observable_effect_verifier import ObservableEffectVerifier
from posttooluse.python_syntax_checker import PythonSyntaxChecker
from posttooluse.outcome_validator_hook import OutcomeValidatorHook

# SQA Phase Tracker - tracks layer-specific tool invocations during SQA execution
from posttooluse.posttooluse_sqa_phase_tracker import SQAPhaseTrackerHook
from posttooluse.reflexion_verifier import ReflexionVerifier
from posttooluse.semantic_compress import SemanticCompress
from posttooluse.skill_command_hook import SkillCommandHook
from posttooluse.skill_execution_tracker import SkillExecutionTracker

# Skill invocation logger - logs Skill() tool invocations to JSONL file
from posttooluse.skill_invocation_logger_hook import SkillInvocationLoggerHook
from posttooluse.speculation_detector_hook import SpeculationDetectorHook
from posttooluse.strategy_escalation_hook import StrategyEscalationHook
from posttooluse.system2_hook import System2Hook

# VStateTrackerHook removed: source file deleted
# Task tracker - absorbed from subprocess PostToolUse_task_tracker.py
from posttooluse.task_tracker_hook import TaskTrackerHook
from posttooluse.task_unresolved_suggester_hook import TaskUnresolvedSuggesterHook
from posttooluse.tdd95_autoscaffold_hook import TDD95AutoScaffoldHook
from posttooluse.tdd_state_hook import TDDStateHook
from posttooluse.workflow_completion_tracker import WorkflowCompletionTracker

"""
PostToolUse Hook Package
========================

In-process PostToolUse hooks - eliminates subprocess overhead.

18 hooks in a single process with matcher filtering.
Each hook defines tool_matcher to control which tools trigger it.
Registry is created fresh per invocation — no cross-process state leaks.

Usage (from router):
    from posttooluse import HookRegistry, create_registry

    registry = create_registry()
    result = registry.run_all(data)
"""

__all__ = [
    "PostToolUseHook",
    "HookRegistry",
    "create_registry",
    "is_block_result",
]


def create_registry() -> HookRegistry:
    """Create and register all PostToolUse hooks.

    Registry is created fresh per invocation. No cross-process state.
    Each hook's tool_matcher controls which tools trigger it.
    Each hook's errors are isolated — one failure never crashes the router.

    Removed (no value or broken):
    - next_command_suggester: ERROR on every call, 117ms wasted
    - change_verification: redundant with file_activity_tracker
    - value_tracker: passive metric with no consumer (archived 2026-03-04)
    - utility_awareness: passive metric with no consumer (archived 2026-03-04)
    - falsification_assessor_standalone: duplicate of falsification_assessor
    - verification_tracker: no consumer reads its state
    - tool_thrashing_tracker: redundant with strategy_escalation (archived 2026-03-04)
    """
    registry = HookRegistry()

    # --- Original in-process hooks ---
    registry.register("fix_validator", FixValidator())
    registry.register("reflexion_verifier", ReflexionVerifier())
    # Artifact scraper - records locally-found artifacts into session ledger (replaces subprocess hook_runner.py)
    registry.register("artifact_scraper", ArtifactScraperHook())
    # Implementation Verifier - verifies Write/Edit actually creates claimed files
    registry.register("implementation_verifier", ImplementationVerifier())
    # Observable Effect Verifier - verifies expected side effects from code changes
    registry.register("observable_effect_verifier", ObservableEffectVerifier())
    # Integration Verifier - verifies skill integration claims match implementation
    registry.register("integration_verifier", IntegrationVerifier())
    # Completion Validator - verifies completion claims against integration status
    registry.register("completion_validator", CompletionValidator())
    registry.register("falsification_assessor", FalsificationAssessor())
    registry.register("semantic_compress", SemanticCompress())
    registry.register("error_attribution_tracker", ErrorAttributionTracker())
    registry.register("skill_execution_tracker", SkillExecutionTracker())
    registry.register("investigation_tracker", InvestigationTracker())
    # Breadcrumb tracker - automatic workflow step tracking from tool usage
    registry.register("breadcrumb_tracker", BreadcrumbTrackerHook())

    # --- Absorbed from standalone processes ---
    registry.register("evidence_tracker", EvidenceTrackerHook())
    registry.register("failure_recorder", FailureRecorderHook())
    registry.register("system2", System2Hook())
    registry.register("file_activity_tracker", FileActivityTrackerHook())
    # File invalidation tracker - marks modified files as invalid for cross-validator
    registry.register("file_invalidation_tracker", FileInvalidationTrackerHook())
    registry.register("speculation_detector", SpeculationDetectorHook())
    # TDD state - handles TDD phase transitions after tool execution
    registry.register("tdd_state", TDDStateHook())
    # TDD-95 auto-scaffold - creates test stubs for implementation files
    registry.register("tdd95_autoscaffold", TDD95AutoScaffoldHook())
    registry.register("inherited_choice", InheritedChoiceHook())
    registry.register("strategy_escalation", StrategyEscalationHook())

    # --- Wave 2: absorbed from standalone subprocesses ---
    # Previously: post_tool_use_change_propagation.py (subprocess, 65ms)
    registry.register("change_propagation", ChangePropagationHook())
    # Previously: PostToolUse_outcome_validator.py (subprocess, 130ms)
    registry.register("outcome_validator", OutcomeValidatorHook())
    # Previously: error_attribution_validator.py via PostToolUse_bash_router.py (2x subprocess, 256ms)
    registry.register("error_attribution", ErrorAttributionHook())
    # VStateTrackerHook removed: source file deleted
    # Previously: PostToolUse_task_tracker.py (subprocess, 50ms)
    registry.register("task_tracker", TaskTrackerHook())
    # Adds unresolved chat-history suggestions for TaskList outputs (non-blocking)
    registry.register("task_unresolved_suggester", TaskUnresolvedSuggesterHook())
    # E2E tracker - tracks skill invocations and workflows (TASK-003, TASK-006)
    registry.register("e2e_tracker", E2ETrackerHook())
    # Auto-lint - STRUCTURALLY DISABLED: ruff --fix strips code between sequential edits
    # Registry entry REMOVED: lint_hook.py is kept on disk for reference but never registered
    # Reason: default_enabled=False was flag-based and bypassable via LINT_ROUTER_ENABLED=true env var
    # lint_hook.py runs "ruff check --fix" which silently corrupts code during sequential edits
    # To re-enable: add back registry.register("lint", LintHook()) AND set default_enabled=True
    # registry.register("lint", LintHook())
    # Cleanup tracker - tracks tool usage for cleanup verification
    registry.register("cleanup_tracker", CleanupTrackerHook())
    # Skill invocation logger - logs Skill() tool invocations for verification
    registry.register("skill_invocation_logger", SkillInvocationLoggerHook())
    # Enforcement tier validator - validates enforcement field in SKILL.md frontmatter
    registry.register("enforcement_tier_validator", EnforcementTierValidator())
    # Workflow completion tracker - tracks phase transitions and completion criteria
    registry.register("workflow_completion_tracker", WorkflowCompletionTracker())
    # SQA Phase Tracker - tracks layer-specific tool invocations during SQA execution
    registry.register("sqa_phase_tracker", SQAPhaseTrackerHook())
    # Agent contract validator - validates adversarial agent .md files on Write/Edit
    registry.register("agent_contract_validator", AgentContractValidator())
    # Edit verifier - verifies Write/Edit operations actually persisted to disk
    registry.register("edit_verifier", EditVerifier())
    # Python syntax checker - catches SyntaxErrors after Edit/Write on .py files
    registry.register("python_syntax_checker", PythonSyntaxChecker())
    # Characterization capture - stores AST characterization of hook files after edits
    from posttooluse.characterization_capture_hook import CharacterizationCaptureHook
    registry.register("characterization_capture", CharacterizationCaptureHook())

    # --- Discovered skill hooks from SKILL.md frontmatter ---
    # Auto-discover hooks declared in skill SKILL.md files and register them
    # Suppress skill_guard logger stderr — yaml.safe_load() warnings on malformed SKILL.md
    # frontmatter go to logger.warning() which emits to stderr, causing CLI "hook error"
    # display despite hooks exiting 0 (success). NullHandler redirects to silence.
    import logging

    logging.getLogger("skill_guard").addHandler(logging.NullHandler())

    try:
        from skill_guard.skill_auto_discovery import discover_hooks

        discovered = discover_hooks()
        for hook_config in discovered:
            hook = SkillCommandHook(
                skill=hook_config["skill"],
                name=hook_config["name"],
                command=hook_config["command"],
                timeout=hook_config.get("timeout", 10),
                matcher_pattern=hook_config.get("matcher"),
            )
            registry.register(hook_config["name"], hook)
    except ImportError as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"skill_guard not available - discovered hooks skipped: {e}")

    return registry
