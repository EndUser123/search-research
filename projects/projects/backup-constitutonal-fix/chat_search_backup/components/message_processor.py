from __future__ import annotations

from dataclasses import field
from datetime import datetime
from typing import Any
import logging
import re
import statistics

from ..interfaces.analysis_interfaces import (

#!/usr/bin/env python3
"""Message Processor Implementation
Follows CSF NIP standards for clean architecture.
"""


    ChatMessage,
    IConfigurationManager,
    ILogger,
    IMessageProcessor,
)


class MessageProcessor(IMessageProcessor):
    """Message processor following SRP with security validation and normalization."""

    def __init__(self, container=None) -> None:
        self.container = container
        self.logger = container.resolve(ILogger) if container else None
        self.config_manager = (
            container.resolve(IConfigurationManager) if container else None
        )
        self._processed_count = 0
        self._error_count = 0

    async def process_message(self, message: ChatMessage) -> ChatMessage:
        """Process individual message with validation and normalization."""
        try:
            if self.logger:
                await self.logger.debug(f"Processing message {message.id}")

            # Validate message structure
            if not await self.validate_message(message):
                if self.logger:
                    await self.logger.warning(
                        f"Invalid message structure: {message.id}"
                    )
                self._error_count += 1
                # Return sanitized message instead of failing
                return self._create_safe_message(message)

            # Normalize content
            processed_message = ChatMessage(
                id=message.id,
                content=self._normalize_content(message.content),
                timestamp=self._normalize_timestamp(message.timestamp),
                author=self._normalize_author(message.author),
                metadata=self._process_metadata(message.metadata),
            )

            self._processed_count += 1
            return processed_message

        except Exception as e:
            self._error_count += 1
            if self.logger:
                await self.logger.exception(
                    f"Error processing message {message.id}: {e}"
                )
            # Return safe fallback message
            return self._create_safe_message(message)

    async def normalize_messages(
        self, messages: list[ChatMessage]
    ) -> list[ChatMessage]:
        """Normalize a list of messages with batch processing."""
        if not messages:
            return []

        try:
            # Process messages in batches to manage memory
            batch_size = await self._get_batch_size()
            normalized_messages = []

            for i in range(0, len(messages), batch_size):
                batch = messages[i : i + batch_size]
                batch_results = []

                for message in batch:
                    try:
                        processed = await self.process_message(message)
                        batch_results.append(processed)
                    except Exception as e:
                        if self.logger:
                            await self.logger.exception(
                                f"Failed to process message in batch: {e}"
                            )
                        # Add safe message instead of skipping
                        batch_results.append(self._create_safe_message(message))

                normalized_messages.extend(batch_results)

            if self.logger:
                await self.logger.info(
                    f"Normalized {len(normalized_messages)} messages"
                )

            return normalized_messages

        except Exception as e:
            if self.logger:
                await self.logger.exception(f"Error normalizing messages: {e}")
            # Return safe messages as fallback
            return [self._create_safe_message(msg) for msg in messages]

    async def validate_message(self, message: ChatMessage) -> bool:
        """Comprehensive message validation."""
        try:
            # Check required fields
            if not message.id or not isinstance(message.id, str):
                return False

            if not message.content or not isinstance(message.content, str):
                return False

            if not message.author or not isinstance(message.author, str):
                return False

            # Validate content length
            max_length = await self._get_max_message_length()
            if len(message.content) > max_length:
                if self.logger:
                    await self.logger.warning(
                        f"Message too long: {len(message.content)} chars"
                    )
                return False

            # Validate timestamp format
            try:
                datetime.fromisoformat(message.timestamp.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                if self.logger:
                    await self.logger.warning(
                        f"Invalid timestamp format: {message.timestamp}"
                    )
                return False

            # Validate author format
            if not self._is_valid_author(message.author):
                if self.logger:
                    await self.logger.warning(
                        f"Invalid author format: {message.author}"
                    )
                return False

            # Check for dangerous content
            if self._contains_dangerous_content(message.content):
                if self.logger:
                    await self.logger.warning(
                        f"Dangerous content detected in message {message.id}"
                    )
                return False

            return True

        except Exception as e:
            if self.logger:
                await self.logger.exception(f"Error validating message: {e}")
            return False

    def _normalize_content(self, content: str) -> str:
        """Normalize message content."""
        if not content:
            return ""

        # Remove excessive whitespace
        content = re.sub(r"\s+", " ", content.strip())

        # Normalize line endings
        content = content.replace("\r\n", "\n").replace("\r", "\n")

        # Remove control characters except newlines and tabs
        return re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", content)

    def _normalize_timestamp(self, timestamp: str) -> str:
        """Normalize timestamp to ISO format."""
        try:
            # Parse and reformat timestamp
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            return dt.isoformat()
        except (ValueError, AttributeError):
            # Fallback to current time
            return datetime.now().isoformat()

    def _normalize_author(self, author: str) -> str:
        """Normalize author name."""
        if not author:
            return "Unknown"

        # Remove special characters and normalize case
        author = re.sub(r"[^\w\s-]", "", author.strip())
        return author.title() if author else "Unknown"

    def _process_metadata(self, metadata: dict[str, Any]) -> dict[str, Any]:
        """Process and sanitize metadata."""
        if not metadata:
            return {}

        processed = {}
        for key, value in metadata.items():
            # Sanitize key
            safe_key = re.sub(r"[^\w_-]", "", str(key))

            # Sanitize value
            if isinstance(value, str):
                safe_value = self._normalize_content(value)[:500]  # Limit length
            elif isinstance(value, (int, float, bool)):
                safe_value = value
            else:
                safe_value = str(value)[:200]  # Convert other types to string

            processed[safe_key] = safe_value

        return processed

    def _create_safe_message(self, message: ChatMessage) -> ChatMessage:
        """Create safe fallback message."""
        return ChatMessage(
            id=message.id or "unknown",
            content=(
                self._normalize_content(message.content)[:1000]
                if message.content
                else ""
            ),
            timestamp=(
                self._normalize_timestamp(message.timestamp)
                if message.timestamp
                else datetime.now().isoformat()
            ),
            author=(
                self._normalize_author(message.author) if message.author else "Unknown"
            ),
            metadata=(
                self._process_metadata(message.metadata) if message.metadata else {}
            ),
        )

    def _is_valid_author(self, author: str) -> bool:
        """Validate author format."""
        if not author or len(author) > 100:
            return False

        # Check for reasonable characters
        return re.match(r"^[\w\s\-_.@]+$", author)

    def _contains_dangerous_content(self, content: str) -> bool:
        """Check for dangerous content patterns."""
        dangerous_patterns = [
            r"<script[^>]*>",
            r"javascript:",
            r"vbscript:",
            r"onload\s*=",
            r"onerror\s*=",
            r"eval\s*\(",
            r"exec\s*\(",
        ]

        content_lower = content.lower()
        return any(re.search(pattern, content_lower) for pattern in dangerous_patterns)

    async def _get_batch_size(self) -> int:
        """Get processing batch size from configuration."""
        if self.config_manager:
            return await self.config_manager.get_setting("message_batch_size", 100)
        return 100

    async def _get_max_message_length(self) -> int:
        """Get maximum message length from configuration."""
        if self.config_manager:
            return await self.config_manager.get_setting("max_message_length", 10000)
        return 10000

    async def get_processing_stats(self) -> dict[str, Any]:
        """Get processing statistics."""
        return {
            "processed_count": self._processed_count,
            "error_count": self._error_count,
            "error_rate": self._error_count / max(1, self._processed_count),
            "success_rate": (self._processed_count - self._error_count)
            / max(1, self._processed_count),
        }
