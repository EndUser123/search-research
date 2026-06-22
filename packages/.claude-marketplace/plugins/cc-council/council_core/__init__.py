"""Council Core - Multi-model deliberation system.

Top-level exports for the council system.
"""

from council_core.contracts.types import (
    CouncilState,
    ConsensusPolicy,
    ConsensusStrategy,
    CouncilOutcome,
    SessionMetadata,
    DraftResponse,
    ReviewResult,
    SynthesisResult,
    ModelCapability,
    ProviderHealth,
    ProviderAdapter,
)

from council_core.providers.ollama import (
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_CONCURRENCY,
    DEFAULT_TIMEOUT_MS,
    OllamaConfig,
    OllamaProvider,
)

from council_core.persistence.store import CouncilStore, get_connection, init_schema

from council_core.policy.consensus import (
    compute_consensus_ratio,
    select_consensus,
    validate_consensus_reached,
)

from council_core.policy.gating import classify_task, should_bypass_council

__all__ = [
    # Types
    "CouncilState",
    "ConsensusPolicy",
    "ConsensusStrategy",
    "CouncilOutcome",
    "SessionMetadata",
    "DraftResponse",
    "ReviewResult",
    "SynthesisResult",
    "ModelCapability",
    "ProviderHealth",
    "ProviderAdapter",
    # Providers
    "DEFAULT_OLLAMA_BASE_URL",
    "DEFAULT_CONCURRENCY",
    "DEFAULT_TIMEOUT_MS",
    "OllamaConfig",
    "OllamaProvider",
    # Persistence
    "CouncilStore",
    "get_connection",
    "init_schema",
    # Policy
    "compute_consensus_ratio",
    "select_consensus",
    "validate_consensus_reached",
    "classify_task",
    "should_bypass_council",
]
