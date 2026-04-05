"""
Telegram API Error Handling
Enhanced error handling for common Telegram API issues
"""

import asyncio
import re
from typing import NamedTuple

from loguru import logger


class RetryOutcome(NamedTuple):
    """Standard result for handling errors."""

    success: bool
    skip: bool
    error_count: int


class TelegramErrorHandler:
    """Centralized error handling for Telegram API operations"""

    # Common error patterns
    DISCONNECTION_PATTERNS = [
        "Cannot send requests while disconnected",
        "Connection to Telegram failed",
        "no active connection",  # Telethon ValueError for disconnected client
        "disconnected",
        "connection lost",
        "network error",
        "connection closed",
        "connection timeout",
    ]

    RATE_LIMIT_PATTERNS = [
        "Too Many Requests",
        "rate limit",
        "flood wait",
        "FLOOD_WAIT",
    ]

    PROTOCOL_ERROR_PATTERNS = [
        "Constructor ID",
        "Remaining bytes",
        "deserialization error",
        "protocol error",
    ]

    MEDIA_ERROR_PATTERNS = [
        "Media empty",
        "File reference expired",
        "media not found",
        "FILE_REFERENCE_EXPIRED",
    ]

    CHAT_ERROR_PATTERNS = [
        "Invalid object ID for a chat",
        "ChatIdInvalidError",
        "chat id invalid",
        "CHAT_ID_INVALID",
    ]

    @classmethod
    def categorize_error(cls, error_msg: str) -> str:
        """Categorize error type for better handling"""
        error_lower = error_msg.lower()

        if any(
            pattern.lower() in error_lower for pattern in cls.DISCONNECTION_PATTERNS
        ):
            return "disconnection"
        elif any(pattern.lower() in error_lower for pattern in cls.RATE_LIMIT_PATTERNS):
            return "rate_limit"
        elif any(
            pattern.lower() in error_lower for pattern in cls.PROTOCOL_ERROR_PATTERNS
        ):
            return "protocol"
        elif any(
            pattern.lower() in error_lower for pattern in cls.MEDIA_ERROR_PATTERNS
        ):
            return "media"
        elif any(pattern.lower() in error_lower for pattern in cls.CHAT_ERROR_PATTERNS):
            return "chat"
        else:
            return "unknown"

    @classmethod
    def parse_flood_wait_seconds(cls, error_msg: str) -> int | None:
        """Parse FLOOD_WAIT seconds from error message"""
        match = re.search(r"FLOOD_WAIT_(\d+)", error_msg)
        if match:
            return int(match.group(1))
        return None

    @classmethod
    def should_retry(
        cls, error_category: str, attempt: int = 1, error_msg: str = ""
    ) -> tuple[bool, float]:
        """
        Determine if error should be retried and suggested delay
        Returns: (should_retry, delay_seconds)
        """
        if error_category == "protocol" and attempt < 2:
            return True, 1.0  # Retry protocol errors once with 1s delay
        elif error_category == "rate_limit" and attempt < 3:
            # Check for specific FLOOD_WAIT seconds
            flood_wait_seconds = cls.parse_flood_wait_seconds(error_msg)
            if flood_wait_seconds:
                # Cap flood wait at 300 seconds (5 minutes) max
                delay = float(min(flood_wait_seconds, 300))
                logger.info(f"FLOOD_WAIT detected: waiting {delay} seconds")
                return True, delay
            else:
                # Regular exponential backoff for other rate limits
                delay = float(min(10.0 * attempt, 60.0))
                return True, delay
        elif error_category == "media" and attempt < 2:
            return True, 2.0  # Retry media errors once with 2s delay
        elif error_category == "chat":
            return False, 0.0  # Don't retry chat errors - they're permanent
        else:
            return False, 0.0

    @classmethod
    def should_suppress_during_shutdown(
        cls, error_category: str, termination_event: asyncio.Event | None
    ) -> bool:
        """Check if error should be suppressed during graceful shutdown"""
        if termination_event and termination_event.is_set():
            # Suppress connection-related errors during shutdown
            return error_category in ["disconnection", "protocol"]
        return False

    @classmethod
    def format_error_message(
        cls, error_msg: str, message_id: int, error_category: str
    ) -> str:
        """
        Format error message based on category, redacting sensitive data and handling edge cases.
        """
        # Redact sensitive info (simple example: API keys, session strings)
        redacted = error_msg.replace("api_hash", "[REDACTED]").replace(
            "session", "[REDACTED]"
        )
        msg_short = redacted[:100] if redacted else "(no details)"
        if error_category == "disconnection":
            return f"Connection lost for message {message_id}"
        elif error_category == "rate_limit":
            return f"Rate limited for message {message_id}: {msg_short}"
        elif error_category == "protocol":
            return f"Protocol error for message {message_id} (retryable)"
        elif error_category == "media":
            return f"Media error for message {message_id}: {msg_short}"
        else:
            return f"Unknown error for message {message_id}: {msg_short}"

    @classmethod
    async def handle_telegram_error(
        cls,
        error: Exception,
        message_id: int,
        attempt: int = 1,
        termination_event: asyncio.Event | None = None,
        suppress_logs: bool = False,
    ) -> RetryOutcome:
        """
        Handle Telegram API error with appropriate action
        Returns: (success, should_skip, error_count)
        """
        error_msg = str(error)
        error_category = cls.categorize_error(error_msg)

        # Check if we should suppress this error during shutdown
        if cls.should_suppress_during_shutdown(error_category, termination_event):
            logger.debug(
                f"Suppressing {error_category} error during shutdown: message {message_id}"
            )
            return RetryOutcome(False, True, 0)  # Skip without counting as error

        # Check if we should retry
        should_retry, delay = cls.should_retry(error_category, attempt, error_msg)

        if should_retry:
            if not suppress_logs:
                logger.debug(
                    f"Retrying message {message_id} after {delay}s delay (attempt {attempt})"
                )
            await asyncio.sleep(delay)
            return RetryOutcome(False, False, 0)  # Indicate retry needed
        else:
            # Log appropriate message based on error category (only if not suppressed)
            if not suppress_logs:
                formatted_msg = cls.format_error_message(
                    error_msg, message_id, error_category
                )

                if error_category in ["disconnection", "rate_limit"]:
                    logger.warning(f"⚠️ {formatted_msg}")
                    return RetryOutcome(
                        False, True, 0
                    )  # Skip without counting as error
                else:
                    logger.error(formatted_msg)
                    return RetryOutcome(False, False, 1)  # Count as error
            else:
                # Still count errors but don't log to preserve TQDM display
                if error_category in ["disconnection", "rate_limit"]:
                    return RetryOutcome(
                        False, True, 0
                    )  # Skip without counting as error
                else:
                    return RetryOutcome(False, False, 1)  # Count as error


# Convenience function for backward compatibility
async def handle_download_error(
    error: Exception,
    message_id: int,
    attempt: int = 1,
    termination_event: asyncio.Event | None = None,
    suppress_logs: bool = False,
) -> RetryOutcome:
    """Wrapper function for download error handling"""
    return await TelegramErrorHandler.handle_telegram_error(
        error, message_id, attempt, termination_event, suppress_logs
    )
