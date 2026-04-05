"""ProviderProtocol base types for CHS multi-provider history archive."""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class ProviderCapabilities:
    """Capabilities supported by a provider."""

    supports_incremental: bool
    supports_backfill: bool
    has_task_events: bool
    has_tool_events: bool


@dataclass(frozen=True)
class NormalizedEvent:
    """Normalized event from any history provider."""

    provider_id: str
    source_id: str
    event_id: str
    conversation_id: str | None
    session_id: str | None
    terminal_id: str | None
    turn_id: str | None
    occurred_at: str  # ISO 8601
    content_hash: str  # SHA-256
    raw_payload_path: str
    metadata_json: str


@runtime_checkable
class Provider(Protocol):
    """Protocol for history providers."""

    @property
    def provider_id(self) -> str:
        """Unique identifier for this provider."""
        ...

    @property
    def capabilities(self) -> ProviderCapabilities:
        """Capabilities supported by this provider."""
        ...

    def discover(self) -> list[dict]:
        """Discover available sources from this provider."""
        ...

    def ingest_since(self, watermark: dict | None) -> list[dict]:
        """Ingest events since watermark."""
        ...

    def fetch_session(self, source_id: str) -> dict:
        """Fetch full session by source_id."""
        ...

    def fetch_message(self, source_id: str, message_id: str) -> dict:
        """Fetch single message by source_id and message_id."""
        ...
