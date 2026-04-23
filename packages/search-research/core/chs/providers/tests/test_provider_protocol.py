"""T13: ProviderProtocol interface contract tests."""


import pytest

from .base import (
    NormalizedEvent,
    Provider,
    ProviderCapabilities,
)


class MockProvider:
    """Concrete implementation for testing."""

    provider_id: str = "test_provider"
    capabilities: ProviderCapabilities = ProviderCapabilities(
        supports_incremental=True,
        supports_backfill=False,
        has_task_events=True,
        has_tool_events=False,
    )

    def discover(self) -> list[dict]:
        return []

    def ingest_since(self, watermark: dict | None) -> list[dict]:
        return []

    def fetch_session(self, source_id: str) -> dict:
        return {}

    def fetch_message(self, source_id: str, message_id: str) -> dict:
        return {}


class TestProviderProtocolInterface:
    """T13: ProviderProtocol interface contract."""

    def test_provider_protocol_is_runtime_checkable(self):
        """Provider must be usable with runtime_checkable."""
        assert hasattr(Provider, '__protocol_attrs__')

    def test_provider_has_provider_id_property(self):
        """Provider must have provider_id property."""
        p = MockProvider()
        assert hasattr(p, 'provider_id')
        assert isinstance(p.provider_id, str)

    def test_provider_has_capabilities_property(self):
        """Provider must have capabilities property returning ProviderCapabilities."""
        p = MockProvider()
        assert hasattr(p, 'capabilities')
        assert isinstance(p.capabilities, ProviderCapabilities)

    def test_provider_has_discover_method(self):
        """Provider must have discover() method."""
        p = MockProvider()
        assert callable(getattr(p, 'discover', None))

    def test_provider_has_ingest_since_method(self):
        """Provider must have ingest_since() method."""
        p = MockProvider()
        assert callable(getattr(p, 'ingest_since', None))

    def test_provider_has_fetch_session_method(self):
        """Provider must have fetch_session() method."""
        p = MockProvider()
        assert callable(getattr(p, 'fetch_session', None))

    def test_provider_has_fetch_message_method(self):
        """Provider must have fetch_message() method."""
        p = MockProvider()
        assert callable(getattr(p, 'fetch_message', None))

    def test_discover_returns_list(self):
        """discover() must return list[dict]."""
        p = MockProvider()
        result = p.discover()
        assert isinstance(result, list)

    def test_ingest_since_accepts_none_watermark(self):
        """ingest_since(None) must be valid call."""
        p = MockProvider()
        result = p.ingest_since(None)
        assert isinstance(result, list)

    def test_fetch_session_signature(self):
        """fetch_session(source_id: str) must accept string."""
        p = MockProvider()
        result = p.fetch_session("source_123")
        assert isinstance(result, dict)

    def test_fetch_message_signature(self):
        """fetch_message(source_id: str, message_id: str) must accept two strings."""
        p = MockProvider()
        result = p.fetch_message("source_123", "msg_456")
        assert isinstance(result, dict)

    def test_capabilities_has_correct_fields(self):
        """ProviderCapabilities must have all required fields."""
        caps = ProviderCapabilities(
            supports_incremental=True,
            supports_backfill=False,
            has_task_events=True,
            has_tool_events=False,
        )
        assert caps.supports_incremental is True
        assert caps.supports_backfill is False
        assert caps.has_task_events is True
        assert caps.has_tool_events is False

    def test_normalized_event_has_required_fields(self):
        """NormalizedEvent must have all required fields."""
        event = NormalizedEvent(
            provider_id="test",
            source_id="src1",
            event_id="evt1",
            conversation_id="conv1",
            session_id="sess1",
            terminal_id="term1",
            turn_id="turn1",
            occurred_at="2026-04-02T00:00:00Z",
            content_hash="abc123",
            raw_payload_path="/path/to/raw.jsonl",
            metadata_json="{}",
        )
        assert event.provider_id == "test"
        assert event.source_id == "src1"
        assert event.event_id == "evt1"
        assert event.conversation_id == "conv1"
        assert event.session_id == "sess1"
        assert event.terminal_id == "term1"
        assert event.turn_id == "turn1"
        assert event.occurred_at == "2026-04-02T00:00:00Z"
        assert event.content_hash == "abc123"
        assert event.raw_payload_path == "/path/to/raw.jsonl"
        assert event.metadata_json == "{}"

    def test_normalized_event_is_frozen(self):
        """NormalizedEvent must be immutable (frozen=True)."""
        event = NormalizedEvent(
            provider_id="test",
            source_id="src1",
            event_id="evt1",
            conversation_id=None,
            session_id=None,
            terminal_id=None,
            turn_id=None,
            occurred_at="2026-04-02T00:00:00Z",
            content_hash="abc123",
            raw_payload_path="/path/to/raw.jsonl",
            metadata_json="{}",
        )
        with pytest.raises(AttributeError):
            event.provider_id = "changed"

    def test_capabilities_is_frozen(self):
        """ProviderCapabilities must be immutable (frozen=True)."""
        caps = ProviderCapabilities(
            supports_incremental=True,
            supports_backfill=False,
            has_task_events=True,
            has_tool_events=False,
        )
        with pytest.raises(AttributeError):
            caps.supports_incremental = False
