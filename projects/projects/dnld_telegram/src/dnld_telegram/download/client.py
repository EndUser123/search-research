import asyncio
import logging

from loguru import logger
from telethon import TelegramClient  # type: ignore
from telethon.sessions import StringSession  # type: ignore

from ..config.config_manager import ConfigManager  # Import ConfigManager

# Suppress verbose Telethon protocol error logging
logging.getLogger("telethon").setLevel(logging.ERROR)
logging.getLogger("telethon.network").setLevel(logging.CRITICAL)


def validate_credentials():
    """Validate and load credentials with security checks."""
    # Configuration from ConfigManager
    config = ConfigManager()
    api_id = config.get("telegram.api_id")
    api_hash = config.get("telegram.api_hash")
    session_string = config.get("telegram.session_string")

    # Validate that we have the required credentials
    if not api_id:
        logger.error("TELEGRAM_API_ID not found in configuration")
        raise ValueError("TELEGRAM_API_ID not found in configuration")
    if not api_hash:
        logger.error("TELEGRAM_API_HASH not found in configuration")
        raise ValueError("TELEGRAM_API_HASH not found in configuration")
    if not session_string:
        logger.error("TELEGRAM_SESSION_STRING not found in configuration")
        raise ValueError("TELEGRAM_SESSION_STRING not found in configuration")

    # Validate API_ID format and range
    try:
        api_id_int = int(api_id)
        if api_id_int <= 0:
            logger.error("TELEGRAM_API_ID must be a positive integer")
            raise ValueError("TELEGRAM_API_ID must be a positive integer")
    except ValueError:
        logger.error("TELEGRAM_API_ID must be a valid positive integer")
        raise ValueError("TELEGRAM_API_ID must be a valid positive integer")

    # Validate API_HASH format (should be 32 character hex string)
    api_hash_str = str(api_hash).strip()
    if len(api_hash_str) != 32:
        logger.error("TELEGRAM_API_HASH must be a 32-character string")
        raise ValueError("TELEGRAM_API_HASH must be a 32-character string")
    if not all(c in "0123456789abcdefABCDEF" for c in api_hash_str):
        logger.error("TELEGRAM_API_HASH must contain only hexadecimal characters")
        raise ValueError("TELEGRAM_API_HASH must contain only hexadecimal characters")

    # Validate session string is not empty and has reasonable length
    session_string_str = str(session_string).strip()
    if len(session_string_str) < 50:  # Session strings are typically much longer
        logger.error("TELEGRAM_SESSION_STRING appears to be invalid (too short)")
        raise ValueError("TELEGRAM_SESSION_STRING appears to be invalid (too short)")

    # Don't log sensitive information
    logger.info("Credentials validated successfully")

    return api_id_int, api_hash_str, session_string_str


# Validate and load credentials


async def get_client(api_id, api_hash, session_string):
    """Get the Telegram client with enhanced connection retry logic."""
    max_retries = 5
    retry_delay = 2  # Initial delay in seconds

    for attempt in range(max_retries):
        try:
            logger.debug(
                f"Creating Telegram client (attempt {attempt + 1}/{max_retries})"
            )

            # Enhanced client configuration
            client = TelegramClient(
                StringSession(session_string),
                api_id,
                api_hash,
                connection_retries=3,  # Telethon internal retry logic
                retry_delay=1,  # Delay between Telethon retries
                timeout=30,  # Connection timeout
                flood_sleep_threshold=60,  # Wait time for flood protection
            )

            # Connection with timeout
            logger.debug("Attempting to connect to Telegram...")
            await asyncio.wait_for(client.connect(), timeout=30.0)

            # Verify connection and authorization
            logger.debug("Verifying client authorization...")
            is_authorized = await asyncio.wait_for(
                client.is_user_authorized(), timeout=10.0
            )

            if not is_authorized:
                logger.error(
                    "Client is not authorized. Session string may be expired or invalid."
                )
                await client.disconnect()
                raise Exception("Client not authorized - session string may be expired")

            # Test basic functionality
            logger.debug("Testing client functionality...")
            try:
                me = await asyncio.wait_for(client.get_me(), timeout=10.0)
                logger.info(
                    f"✅ Client connected successfully as: {me.first_name} (@{me.username})"
                )
            except Exception as test_error:
                logger.warning(f"Client connection test failed: {test_error}")
                await client.disconnect()
                raise Exception(f"Client functionality test failed: {test_error}")

            return client

        except TimeoutError as e:
            logger.warning(
                f"Connection timeout on attempt {attempt + 1}/{max_retries}: {e}"
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                continue
            else:
                raise Exception(
                    "Connection timeout - Telegram servers may be unreachable"
                )

        except (ConnectionError, OSError) as e:
            logger.warning(f"Network error on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))
                continue
            else:
                raise Exception(f"Network connection failed: {e}")

        except Exception as e:
            # Check if this is a session/authentication error (don't retry)
            error_msg = str(e).lower()
            if any(
                keyword in error_msg
                for keyword in ["not authorized", "session", "unauthorized", "expired"]
            ):
                logger.error(f"Authentication error: {e}")
                raise Exception(f"Session authentication failed: {e}")

            logger.warning(
                f"Unexpected error on attempt {attempt + 1}/{max_retries}: {e}"
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay * (attempt + 1))
                continue
            else:
                raise Exception(
                    f"Failed to create client after {max_retries} attempts: {e}"
                )
