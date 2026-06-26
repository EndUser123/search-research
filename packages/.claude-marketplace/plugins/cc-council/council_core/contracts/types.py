"""Data contracts and types for council system.

These are pure data structures with no dependencies on
providers, engines, or Claude Code.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any


# ── State Machine ────────────────────────────────────────────────────────────────


class CouncilState(Enum):
    """Durable states for council sessions.

    States must be terminal or can transition to terminal.
    Terminal states cannot transition further.
    """

    IDLE = "idle"
    CLASSIFYING = "classifying"
    DRAFTING = "drafting"
    REVIEWING = "reviewing"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"

    @classmethod
    def terminal_states(cls) -> set[CouncilState]:
        """States that cannot transition to other states."""
        return {cls.COMPLETED, cls.FAILED, cls.ABORTED}

    def is_terminal(self) -> bool:
        """Check if this state is terminal."""
        return self in self.terminal_states()


# ── Consensus Types ──────────────────────────────────────────────────────────────


class ConsensusStrategy(Enum):
    """Strategies for selecting consensus from multiple opinions."""

    RANKED_PEER_REVIEW = "ranked_peer_review"
    MAJORITY_VOTE = "majority_vote"
    CHAIRMAN_OVERRIDE = "chairman_override"
    NO_CONSENSUS = "no_consensus"


@dataclass
class ConsensusPolicy:
    """Policy for consensus selection.

    Do NOT rely on uncalibrated model confidence as primary rule.
    """

    strategy: ConsensusStrategy
    minimum_agreement_ratio: float = 0.67  # 2/3 for 3 models
    fallback_on_tie: ConsensusStrategy = ConsensusStrategy.CHAIRMAN_OVERRIDE
    escalate_to_human: bool = False


# ── Session Metadata ─────────────────────────────────────────────────────────────


@dataclass
class SessionMetadata:
    """Metadata for council sessions."""

    session_id: str
    prompt: str
    state: CouncilState
    created_at: datetime
    updated_at: datetime
    gating_reason: str | None = None
    failure_reason: str | None = None
    total_rounds: int = 0
    models_used: list[str] = field(default_factory=list)
    duration_ms: int = 0


# ── Deliberation Artifacts ───────────────────────────────────────────────────────


@dataclass
class DraftResponse:
    """Independent opinion from a single model.

    Stored with model identity for provenance, but
    presented anonymously during peer review.
    """

    model: str
    role: str  # "draft"
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class ReviewResult:
    """Peer review and ranking of drafts.

    Rankings are 1-5 scale (1=poor, 5=excellent).
    Critiques provide qualitative feedback.
    """

    model: str
    role: str  # "critic", "reviewer"
    rankings: dict[str, int]  # {draft_id: rank}
    critiques: dict[str, str]  # {draft_id: critique_text}
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class SynthesisResult:
    """Final synthesis from chairman/judge model."""

    model: str
    role: str  # "chairman", "judge"
    content: str
    contradiction_notes: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class CouncilOutcome:
    """Complete council deliberation result."""

    session_id: str
    metadata: SessionMetadata
    drafts: list[DraftResponse]
    reviews: list[ReviewResult]
    synthesis: SynthesisResult | None
    consensus_ratio: float | None
    contradictions: list[str]
    provenance: dict[str, Any]


# ── Provider Contracts ────────────────────────────────────────────────────────────


@dataclass
class ModelCapability:
    """Capabilities and constraints of a model.

    Resource score: 1-10, lower = more resource-hungry.
    Used for scheduling and timeout decisions.
    """

    name: str
    max_context: int
    supports_json: bool
    estimated_latency_ms: int
    resource_score: int


@dataclass
class ProviderHealth:
    """Health status of a provider."""

    provider_id: str
    is_healthy: bool
    available_models: list[str]
    error_message: str | None = None


class ProviderAdapter(ABC):
    """Abstract interface for LLM providers.

    Design is transport-agnostic. Concrete implementations wrap external
    transport layers (e.g., ai-api SDK clients for z.ai, MiniMax, opencode-go).

    Providers handle:
    - Health status monitoring
    - Model capability discovery
    - Resource-aware scheduling (concurrency limits)
    - Error handling and retries
    """

    provider_id: str

    @abstractmethod
    async def health_check(self) -> ProviderHealth:
        """Check if provider is available and list models."""
        ...

    @abstractmethod
    async def generate(
        self,
        model: str,
        prompt: str,
        *,
        max_tokens: int = 1024,
        timeout_ms: int = 30000,
        system_prompt: str | None = None,
    ) -> str:
        """Generate a response from the specified model."""
        ...

    @abstractmethod
    async def get_model_capabilities(self, model: str) -> ModelCapability:
        """Get capability flags for a model."""
        ...

    @abstractmethod
    async def list_models(self) -> list[str]:
        """List all available models."""
        ...

    @abstractmethod
    def get_concurrency_limit(self) -> int:
        """Return max concurrent requests for this provider.

        Local providers have CPU/memory constraints.
        This limit prevents resource exhaustion.
        """
        ...