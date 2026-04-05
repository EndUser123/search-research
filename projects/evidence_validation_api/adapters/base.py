"""
Base adapter interface for evidence validation system components.

This module defines the abstract base classes and interfaces that all
system component adapters must implement for consistent integration.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from ..models.schemas import (
    CacheStrategy,
    EvidenceContent,
    EvidenceMetadata,
    EvidenceRequest,
    EvidenceResponse,
    EvidenceType,
    SeverityLevel,
)


class ComponentAdapter(ABC):
    """
    Abstract base class for all component adapters.

    Provides a consistent interface for different system components
    to interact with the evidence validation API.
    """

    def __init__(
        self,
        component_name: str,
        component_version: str,
        base_url: str,
        api_key: str | None = None,
    ):
        """Initialize the component adapter.

        Args:
            component_name: Name of the component
            component_version: Version of the component
            base_url: Base URL for the evidence validation API
            api_key: Optional API key for authentication
        """
        self.component_name = component_name
        self.component_version = component_version
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client_id = uuid4()

    @abstractmethod
    async def validate_evidence(
        self,
        evidence_data: dict[str, Any],
        evidence_type: EvidenceType,
        metadata: dict[str, Any] | None = None,
        validation_rules: list[str] | None = None,
        async_validation: bool = False,
        cache_strategy: CacheStrategy = CacheStrategy.MEDIUM_TERM,
    ) -> EvidenceResponse:
        """
        Validate evidence using the evidence validation API.

        Args:
            evidence_data: Evidence content to validate
            evidence_type: Type of evidence
            metadata: Additional metadata
            validation_rules: Specific validation rules to apply
            async_validation: Whether to perform validation asynchronously
            cache_strategy: Caching strategy for results

        Returns:
            EvidenceResponse with validation results
        """
        pass

    @abstractmethod
    async def get_validation_status(self, request_id: UUID) -> dict[str, Any] | None:
        """
        Get status of an ongoing validation request.

        Args:
            request_id: Request identifier

        Returns:
            Validation status information
        """
        pass

    @abstractmethod
    async def cancel_validation(self, request_id: UUID) -> bool:
        """
        Cancel an ongoing validation request.

        Args:
            request_id: Request identifier

        Returns:
            True if successfully cancelled
        """
        pass

    def create_evidence_request(
        self,
        evidence_data: dict[str, Any],
        evidence_type: EvidenceType,
        metadata: dict[str, Any] | None = None,
        validation_rules: list[str] | None = None,
        async_validation: bool = False,
        cache_strategy: CacheStrategy = CacheStrategy.MEDIUM_TERM,
    ) -> EvidenceRequest:
        """
        Create an EvidenceRequest from component data.

        Args:
            evidence_data: Evidence content
            evidence_type: Type of evidence
            metadata: Additional metadata
            validation_rules: Validation rules to apply
            async_validation: Whether validation should be async
            cache_strategy: Caching strategy

        Returns:
            EvidenceRequest ready for validation
        """
        # Create evidence content
        evidence_content = EvidenceContent(
            content_type="application/json",
            data=evidence_data,
            raw_content=None,
            binary_content=None,
        )

        # Create evidence metadata
        evidence_metadata = EvidenceMetadata(
            evidence_type=evidence_type,
            source_system=self.component_name,
            source_component=f"{self.component_name}_v{self.component_version}",
            timestamp=datetime.now(UTC),
            workflow_id=metadata.get("workflow_id") if metadata else None,
            task_id=metadata.get("task_id") if metadata else None,
            user_id=metadata.get("user_id") if metadata else None,
            session_id=metadata.get("session_id") if metadata else None,
            tags=metadata.get("tags", []) if metadata else [],
            severity=SeverityLevel(metadata.get("severity", "medium"))
            if metadata
            else SeverityLevel.MEDIUM,
        )

        # Create evidence request
        return EvidenceRequest(
            evidence=evidence_content,
            metadata=evidence_metadata,
            validation_rules=validation_rules or [],
            cache_strategy=cache_strategy,
            async_validation=async_validation,
            priority=metadata.get("priority", 5) if metadata else 5,
        )


class HTTPAdapter(ComponentAdapter):
    """
    HTTP-based adapter for REST API communication.

    Provides HTTP client implementation for components that can
    communicate with the evidence validation API via HTTP/HTTPS.
    """

    def __init__(
        self,
        component_name: str,
        component_version: str,
        base_url: str,
        api_key: str | None = None,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """Initialize HTTP adapter.

        Args:
            component_name: Name of the component
            component_version: Version of the component
            base_url: Base URL for the evidence validation API
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries
        """
        super().__init__(component_name, component_version, base_url, api_key)
        self.timeout = timeout
        self.max_retries = max_retries
        self._http_client = None

    async def _get_http_client(self):
        """Get or create HTTP client."""
        if self._http_client is None:
            import httpx

            headers = {
                "User-Agent": f"{self.component_name}/{self.component_version}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            self._http_client = httpx.AsyncClient(
                headers=headers,
                timeout=self.timeout,
                limits=httpx.Limits(max_keepalive_connections=20, max_connections=100),
            )

        return self._http_client

    async def validate_evidence(
        self,
        evidence_data: dict[str, Any],
        evidence_type: EvidenceType,
        metadata: dict[str, Any] | None = None,
        validation_rules: list[str] | None = None,
        async_validation: bool = False,
        cache_strategy: CacheStrategy = CacheStrategy.MEDIUM_TERM,
    ) -> EvidenceResponse:
        """Validate evidence via HTTP API."""
        client = await self._get_http_client()

        # Create evidence request
        request_data = self.create_evidence_request(
            evidence_data=evidence_data,
            evidence_type=evidence_type,
            metadata=metadata,
            validation_rules=validation_rules,
            async_validation=async_validation,
            cache_strategy=cache_strategy,
        )

        try:
            response = await client.post(
                f"{self.base_url}/validate",
                json=request_data.model_dump(),
            )
            response.raise_for_status()

            response_data = response.json()
            return EvidenceResponse(**response_data)

        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP error {e.response.status_code}: {e.response.text}")
        except httpx.RequestError as e:
            raise Exception(f"Request error: {str(e)}")
        except Exception as e:
            raise Exception(f"Validation failed: {str(e)}")

    async def get_validation_status(self, request_id: UUID) -> dict[str, Any] | None:
        """Get validation status via HTTP API."""
        client = await self._get_http_client()

        try:
            response = await client.get(f"{self.base_url}/validate/{request_id}/status")

            if response.status_code == 404:
                return None

            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise Exception(f"HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise Exception(f"Failed to get validation status: {str(e)}")

    async def cancel_validation(self, request_id: UUID) -> bool:
        """Cancel validation via HTTP API."""
        client = await self._get_http_client()

        try:
            response = await client.delete(f"{self.base_url}/validate/{request_id}")

            if response.status_code == 404:
                return False

            response.raise_for_status()
            return True

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return False
            raise Exception(f"HTTP error {e.response.status_code}: {e.response.text}")
        except Exception as e:
            raise Exception(f"Failed to cancel validation: {str(e)}")

    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None


class WebSocketAdapter(ComponentAdapter):
    """
    WebSocket-based adapter for real-time communication.

    Provides WebSocket client implementation for components that need
    real-time validation updates and notifications.
    """

    def __init__(
        self,
        component_name: str,
        component_version: str,
        base_url: str,
        api_key: str | None = None,
        ws_url: str | None = None,
    ):
        """Initialize WebSocket adapter.

        Args:
            component_name: Name of the component
            component_version: Version of the component
            base_url: Base URL for HTTP API
            api_key: Optional API key for authentication
            ws_url: WebSocket URL (defaults to base_url with /ws)
        """
        super().__init__(component_name, component_version, base_url, api_key)

        if ws_url is None:
            # Convert HTTP URL to WebSocket URL
            if base_url.startswith("https://"):
                ws_url = base_url.replace("https://", "wss://") + "/ws"
            else:
                ws_url = base_url.replace("http://", "ws://") + "/ws"

        self.ws_url = ws_url
        self.http_adapter = HTTPAdapter(
            component_name, component_version, base_url, api_key
        )
        self._websocket = None
        self._message_handlers = {}
        self._connected = False

    async def connect(self):
        """Connect to WebSocket server."""
        import websockets

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            self._websocket = await websockets.connect(
                self.ws_url,
                extra_headers=headers,
                ping_interval=20,
                ping_timeout=10,
            )
            self._connected = True

            # Start message listener
            asyncio.create_task(self._listen_for_messages())

        except Exception as e:
            raise Exception(f"Failed to connect to WebSocket: {str(e)}")

    async def disconnect(self):
        """Disconnect from WebSocket server."""
        self._connected = False
        if self._websocket:
            await self._websocket.close()
            self._websocket = None

    async def _listen_for_messages(self):
        """Listen for WebSocket messages."""
        try:
            async for message in self._websocket:
                await self._handle_message(message)
        except Exception as e:
            if self._connected:  # Only log if not intentionally disconnected
                print(f"WebSocket error: {e}")
        finally:
            self._connected = False

    async def _handle_message(self, message: str):
        """Handle incoming WebSocket message."""
        try:
            import json

            data = json.loads(message)
            message_type = data.get("type")

            if message_type in self._message_handlers:
                handler = self._message_handlers[message_type]
                if asyncio.iscoroutinefunction(handler):
                    await handler(data)
                else:
                    handler(data)

        except Exception as e:
            print(f"Error handling WebSocket message: {e}")

    def add_message_handler(self, message_type: str, handler):
        """Add message handler for specific message type."""
        self._message_handlers[message_type] = handler

    async def send_message(self, message: dict[str, Any]):
        """Send message to WebSocket server."""
        if self._websocket and self._connected:
            import json

            await self._websocket.send(json.dumps(message))

    async def validate_evidence(
        self,
        evidence_data: dict[str, Any],
        evidence_type: EvidenceType,
        metadata: dict[str, Any] | None = None,
        validation_rules: list[str] | None = None,
        async_validation: bool = False,
        cache_strategy: CacheStrategy = CacheStrategy.MEDIUM_TERM,
    ) -> EvidenceResponse:
        """Validate evidence using HTTP API with WebSocket notifications."""
        return await self.http_adapter.validate_evidence(
            evidence_data=evidence_data,
            evidence_type=evidence_type,
            metadata=metadata,
            validation_rules=validation_rules,
            async_validation=async_validation,
            cache_strategy=cache_strategy,
        )

    async def get_validation_status(self, request_id: UUID) -> dict[str, Any] | None:
        """Get validation status using HTTP API."""
        return await self.http_adapter.get_validation_status(request_id)

    async def cancel_validation(self, request_id: UUID) -> bool:
        """Cancel validation using HTTP API."""
        return await self.http_adapter.cancel_validation(request_id)

    async def subscribe_to_validation(self, request_id: UUID, callback):
        """Subscribe to validation updates for a specific request."""
        self.add_message_handler("validation_completed", callback)

        await self.send_message(
            {
                "type": "subscribe_validation",
                "request_id": str(request_id),
            }
        )

    async def close(self):
        """Close adapter connections."""
        await self.disconnect()
        await self.http_adapter.close()


class DirectAdapter(ComponentAdapter):
    """
    Direct adapter for components running in the same process.

    Provides direct method calls for components that are running
    in the same process as the evidence validation API.
    """

    def __init__(self, component_name: str, component_version: str, validation_service):
        """Initialize direct adapter.

        Args:
            component_name: Name of the component
            component_version: Version of the component
            validation_service: Validation service instance
        """
        super().__init__(component_name, component_version, "")
        self.validation_service = validation_service

    async def validate_evidence(
        self,
        evidence_data: dict[str, Any],
        evidence_type: EvidenceType,
        metadata: dict[str, Any] | None = None,
        validation_rules: list[str] | None = None,
        async_validation: bool = False,
        cache_strategy: CacheStrategy = CacheStrategy.MEDIUM_TERM,
    ) -> EvidenceResponse:
        """Validate evidence using direct service call."""
        # Create evidence request
        request_data = self.create_evidence_request(
            evidence_data=evidence_data,
            evidence_type=evidence_type,
            metadata=metadata,
            validation_rules=validation_rules,
            async_validation=async_validation,
            cache_strategy=cache_strategy,
        )

        # Direct service call
        return await self.validation_service.validate_evidence(request_data)

    async def get_validation_status(self, request_id: UUID) -> dict[str, Any] | None:
        """Get validation status using direct service call."""
        return await self.validation_service.get_validation_status(request_id)

    async def cancel_validation(self, request_id: UUID) -> bool:
        """Cancel validation using direct service call."""
        return await self.validation_service.cancel_validation(request_id)

    async def close(self):
        """No cleanup needed for direct adapter."""
        pass
