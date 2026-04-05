"""TDD Clean-Room Loop v2 package.

This package extends TDD-95 with autonomous RED→GREEN→REFACTOR execution,
Cold Code Review, and Three-File Contract patterns.

ADR: P:/.claude/arch_decisions/ADR-20260324-clean-room-tdd-loop.md
"""

from .cold_code_review_dispatch import (
    ColdReviewResult,
    build_blinded_prompt,
    build_review_context,
    dispatch_cold_code_review,
    should_dispatch_review,
)
from .contract_cleanup import (
    DEFAULT_RETENTION_DAYS,
    CleanupResult,
    cleanup_all_completed_contracts,
    cleanup_completed_contract,
    get_cleanup_stats,
    get_completed_contracts,
)
from .enforcement_tiers import (
    EnforcementTier,
    EnforcementTierManager,
    TierConfig,
    get_enforcement_tier,
    should_enforce,
)
from .gto_assertions import GTOAssertionRunner
from .phase_transition_logger import (
    PhaseTransition,
    compute_evidence_hash,
    get_transition_history,
    log_phase_transition,
    validate_transition_sequence,
)
from .ralph_loop_engine import MAX_ITERATIONS, RalphLoopEngine
from .tdd_phase_state import TDDPhaseState, TDDPhaseStateManager
from .three_file_contract import ThreeFileContract

__all__ = [
    # Cold Code Review
    "ColdReviewResult",
    "build_blinded_prompt",
    "build_review_context",
    "dispatch_cold_code_review",
    "should_dispatch_review",
    # Contract Cleanup
    "DEFAULT_RETENTION_DAYS",
    "CleanupResult",
    "cleanup_all_completed_contracts",
    "cleanup_completed_contract",
    "get_cleanup_stats",
    "get_completed_contracts",
    # Enforcement Tiers
    "EnforcementTier",
    "EnforcementTierManager",
    "TierConfig",
    "get_enforcement_tier",
    "should_enforce",
    # GTO Assertions
    "GTOAssertionRunner",
    # Phase Transition Logger
    "PhaseTransition",
    "compute_evidence_hash",
    "get_transition_history",
    "log_phase_transition",
    "validate_transition_sequence",
    # Ralph Loop Engine
    "MAX_ITERATIONS",
    "RalphLoopEngine",
    # TDD Phase State
    "TDDPhaseState",
    "TDDPhaseStateManager",
    # Three-File Contract
    "ThreeFileContract",
]
