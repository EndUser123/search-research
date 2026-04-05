import asyncio

from loguru import logger

from ...exceptions import ConfigurationError, DnldTelegramError
from ..config.logging_config import log_performance
from ..storage import (
    get_file_id,
    load_enumerated_files,
    load_enumeration_metadata,
    save_enumerated_files,
)
from ..telegram_errors import TelegramErrorHandler


async def ensure_client_connected(client, operation_name="operation"):
    """Ensure client is connected, attempt reconnection if needed.

    Args:
        client: Telethon TelegramClient instance
        operation_name: Name of operation for logging

    Returns:
        bool: True if connected, False if connection failed

    Raises:
        ConnectionError: If reconnection attempts fail
    """
    try:
        # Check if client has is_connected method and use it
        if hasattr(client, "is_connected") and callable(client.is_connected):
            if client.is_connected():
                return True

            logger.warning(
                f"Client disconnected during {operation_name}, attempting reconnection..."
            )

            # Attempt reconnection
            await client.connect()

            if client.is_connected():
                logger.info(f"Successfully reconnected client for {operation_name}")
                return True
            else:
                logger.error(f"Failed to reconnect client for {operation_name}")
                return False
        else:
            # Fallback: assume connected if no is_connected method
            logger.debug(
                f"Client connection status unknown for {operation_name}, proceeding"
            )
            return True

    except Exception as e:
        logger.error(
            f"Error checking/restoring client connection for {operation_name}: {e}"
        )
        raise ConnectionError(
            f"Unable to ensure client connection for {operation_name}: {e}"
        ) from e


def is_connection_error(error_msg: str) -> bool:
    """Check if a ValueError message indicates a connection issue.

    Args:
        error_msg: The error message string

    Returns:
        bool: True if this appears to be a connection-related ValueError
    """
    connection_indicators = [
        "no active connection",
        "not connected",
        "connection closed",
        "connection lost",
        "disconnected",
        "network error",
        "connection timeout",
    ]

    error_lower = str(error_msg).lower()
    return any(indicator in error_lower for indicator in connection_indicators)


class MediaMessagesDict(dict):
    """Dict subclass that supports custom attributes for enumeration stats."""

    pass


async def _save_metadata_safely(channel_name, media_messages, metadata):
    """Save enumeration metadata with truly independent database connection.

    Creates a completely independent database connection that is isolated from
    any Telegram client connection issues, with local file fallback.

    Args:
        channel_name: Channel name
        media_messages: Dictionary of media messages
        metadata: Metadata dictionary to update and save
    """
    try:
        # Save enumeration metadata with the ID of the newest message
        if media_messages:
            newest_id = max(int(msg_id) for msg_id in media_messages.keys())
            metadata["last_enumerated_id"] = newest_id

            # Use independent database connection for metadata operations
            await _save_metadata_with_independent_connection(channel_name, metadata)
            logger.info(
                f"Saved enumeration metadata with last_enumerated_id: {newest_id}"
            )
        else:
            logger.debug("No media messages found, skipping metadata save")
    except (ConfigurationError, DnldTelegramError) as e:
        # Handle database/configuration errors gracefully without affecting enumeration
        logger.error(
            f"Failed to save enumeration metadata for {channel_name}: {str(e)}"
        )
        logger.warning(
            "Metadata save failed but enumeration completed successfully. "
            "Check database configuration and channel setup."
        )
    except Exception as e:
        # Handle any other unexpected errors in metadata save
        logger.error(f"Unexpected error saving metadata for {channel_name}: {str(e)}")
        logger.warning("Metadata save failed but enumeration data was preserved.")


async def _save_metadata_with_independent_connection(channel_name: str, metadata: dict):
    """Save metadata using the proper connection pool system.

    This function now uses the connection pool to avoid conflicts with
    the main application's database connections.
    """
    from ..database.schema import get_connection_pool
    from ..database.storage import DatabaseStorage

    try:
        # Use the connection pool system instead of direct connections
        storage = DatabaseStorage(channel_name)

        # Get channel ID through the proper storage system (this will create if needed)
        channel_id = await storage.get_channel_id(channel_name)
        if not channel_id:
            raise ConfigurationError(f"Failed to get channel ID for: {channel_name}")

        # Use connection pool for metadata save
        pool = await get_connection_pool(channel_name)
        async with pool.get_connection() as conn:
            # Save metadata as special messages with negative IDs
            for key, value in metadata.items():
                await conn.execute(
                    """
                    INSERT OR REPLACE INTO messages
                    (telegram_id, channel_id, date, text, media_type, created_at)
                    VALUES (?, ?, datetime('now'), ?, 'metadata', datetime('now'))
                """,
                    (-hash(key) % 1000000, channel_id, f"{key}:{value}"),
                )

            await conn.commit()
            logger.debug(
                f"✅ Metadata saved via connection pool for channel: {channel_name}"
            )

    except Exception as e:
        logger.error(
            f"❌ Connection pool metadata save failed for {channel_name}: {str(e)}"
        )
        logger.warning("Metadata save failed but enumeration data was preserved.")


async def _handle_connection_error_and_retry(
    client,
    chat_id,
    limit,
    channel_name,
    incremental,
    progress,
    termination_event,
    retry_count,
    error_msg,
):
    """Handle connection errors and retry enumeration with exponential backoff.

    Args:
        client: Telethon client
        chat_id: Channel ID
        limit: Message limit
        channel_name: Channel name
        incremental: Incremental enumeration flag
        progress: Progress handler
        termination_event: Termination event
        retry_count: Current retry count
        error_msg: Original error message

    Returns:
        MediaMessagesDict: Result of retry or empty dict if failed
    """
    # Calculate exponential backoff delay: 2s, 5s, 10s, 20s, 40s
    backoff_delays = [2, 5, 10, 20, 40]
    delay = backoff_delays[min(retry_count, len(backoff_delays) - 1)]

    logger.info(
        f"Attempting to reconnect and retry enumeration (attempt {retry_count + 1}/5) after {delay}s delay..."
    )

    # Wait with exponential backoff before retrying
    await asyncio.sleep(delay)

    # Try to reconnect and retry
    try:
        # First attempt: gentle reconnection
        if await ensure_client_connected(client, "enumeration retry"):
            logger.info("Reconnection successful, retrying enumeration...")
            # Retry the enumeration with the reconnected client
            return await enumerate_media_in_channel(
                client,
                chat_id,
                limit=limit,
                channel_name=channel_name,
                incremental=incremental,
                progress=progress,
                termination_event=termination_event,
                _retry_count=retry_count + 1,
            )
        else:
            logger.error("Gentle reconnection attempt failed")
    except Exception as reconnect_error:
        logger.error(f"Error during gentle reconnection attempt: {reconnect_error}")

    # Second attempt: aggressive reconnection with longer delay
    try:
        logger.info(
            f"Attempting aggressive reconnection after additional {delay}s delay..."
        )
        await asyncio.sleep(delay)  # Additional delay for aggressive retry
        await client.disconnect()
        await asyncio.sleep(2)  # Brief pause for connection cleanup
        await client.connect()

        # Verify connection with health check
        if client.is_connected():
            # Additional connection health validation
            try:
                # Test connection with a simple API call
                await client.get_me()
                logger.info(
                    "Aggressive reconnection successful with health check, retrying enumeration..."
                )
                return await enumerate_media_in_channel(
                    client,
                    chat_id,
                    limit=limit,
                    channel_name=channel_name,
                    incremental=incremental,
                    progress=progress,
                    termination_event=termination_event,
                    _retry_count=retry_count + 1,
                )
            except Exception as health_check_error:
                logger.error(f"Connection health check failed: {health_check_error}")
        else:
            logger.error("Aggressive reconnection failed - client not connected")
    except Exception as final_reconnect_error:
        logger.error(f"Aggressive reconnection attempt failed: {final_reconnect_error}")

    return MediaMessagesDict()


@log_performance("enumerate_media_in_channel")
async def enumerate_media_in_channel(
    client,
    chat_id,
    limit=None,
    channel_name=None,
    incremental=False,
    progress=None,
    termination_event=None,
    _retry_count=0,  # Internal parameter to track retries
):
    """Enumerate all media files in a channel without downloading."""
    logger.debug(
        f"enumerate_media_in_channel called with channel_name='{channel_name}' (retry {_retry_count})"
    )

    # Prevent infinite recursion - max 5 retries with exponential backoff
    if _retry_count >= 5:
        logger.error(
            f"Maximum retry attempts ({_retry_count}) reached for channel {chat_id}"
        )
        return MediaMessagesDict()

    # Input validation
    if not client:
        raise ValueError("Client cannot be None")
    if not chat_id:
        raise ValueError("Chat ID cannot be empty")
    if limit is not None and (not isinstance(limit, int) or limit <= 0):
        raise ValueError("Limit must be a positive integer or None")
    if incremental is not None and not isinstance(incremental, bool):
        raise ValueError("Incremental must be a boolean")

    try:
        # Get the entity (channel/user) - handle invalid chat IDs
        try:
            entity = await client.get_entity(chat_id)
        except ValueError as e:
            # Check if this is a connection error that should trigger retry
            error_category = TelegramErrorHandler.categorize_error(str(e))
            if error_category == "disconnection":
                logger.error(
                    f"Connection error during get_entity for channel {chat_id}: {str(e)}"
                )
                # Handle reconnection and retry at this level
                return await _handle_connection_error_and_retry(
                    client,
                    chat_id,
                    limit,
                    channel_name,
                    incremental,
                    progress,
                    termination_event,
                    _retry_count,
                    str(e),
                )
            else:
                # Not a connection error, re-raise
                raise
        except Exception as e:
            if "Invalid object ID" in str(e) or "ChatIdInvalidError" in str(e):
                logger.error(f"Invalid chat ID {chat_id}: {str(e)}")
                return MediaMessagesDict()
            raise

        if not channel_name:
            # Use chat_id as fallback channel name
            channel_name = str(chat_id)
            logger.debug(
                f"enumerate_media_in_channel - determined channel_name='{channel_name}'"
            )

        logger.info(f"Enumerating media in {channel_name}...")

        # Add enumeration task to progress display
        if progress:
            progress.add_main_task("enumeration", "Enumerating media files", total=None)
            progress.start_main_task("enumeration")

        # Initialize variables
        media_messages = MediaMessagesDict()
        existing_files = {}
        count = 0

        # Load existing enumerated files if doing incremental enumeration
        if incremental:
            existing_files = await load_enumerated_files(channel_name)
            logger.info(
                f"Loaded {len(existing_files)} existing enumerated files for incremental enumeration"
            )

        # Load enumeration metadata to get the last enumerated message ID
        metadata = await load_enumeration_metadata(channel_name)
        last_enumerated_id = metadata.get("last_enumerated_id", 0) if incremental else 0

        # Get messages with media using pagination
        count = 0
        total_messages_scanned = 0
        media_messages_found = 0
        text_messages_found = 0

        # Add progress indicator for Telegram API query
        if incremental and last_enumerated_id > 0:
            logger.info(
                f"⚡ Querying Telegram API for new messages after ID {last_enumerated_id}..."
            )
        else:
            logger.info("⚡ Querying Telegram API for all messages...")

        # Ensure client is connected before starting enumeration
        if not await ensure_client_connected(client, "media enumeration"):
            logger.error(
                f"Failed to establish client connection for channel {channel_name}"
            )
            return MediaMessagesDict()

        # If doing incremental enumeration, only get messages newer than the last enumerated ID
        async for message in client.iter_messages(
            entity, reverse=False, min_id=last_enumerated_id if incremental else 0
        ):
            total_messages_scanned += 1
            # Check for termination every message

            if termination_event and termination_event.is_set():
                logger.info(
                    f"🛑 Termination requested during enumeration of {channel_name} after {count} messages"
                )
                break

            if message.media:
                media_messages_found += 1

                # Skip if this message is already enumerated (for incremental enumeration)
                if incremental and str(message.id) in existing_files:
                    continue

                # Get file ID for tracking
                file_id = get_file_id(message.media)

                media_messages[message.id] = {
                    "id": message.id,
                    "date": message.date.isoformat() if message.date else None,
                    "media_type": type(message.media).__name__,
                    "file_id": file_id,
                }

                count += 1
            else:
                text_messages_found += 1

                # Update progress display
                if progress:
                    if count % 50 == 0:  # Update every 50 messages
                        progress.update_main_task(
                            "enumeration",
                            status=f"Found {len(media_messages)} media files",
                        )

                    # Check for termination
                    if progress.is_termination_requested():
                        progress.update_main_task(
                            "enumeration", status="Stopping enumeration..."
                        )
                        break

                if count % 100 == 0:
                    logger.info(f"Processed {count} messages...")

                # If a limit is specified and we've reached it, stop
                if limit and count >= limit:
                    break

        logger.info(f"✅ Retrieved {count} new messages from Telegram API")
        logger.info(
            f"✅ Found {len(media_messages)} new media messages in {channel_name}"
        )

        # Capture NEW count before merging
        new_media_count = len(media_messages)

        # Update progress display
        if progress:
            progress.complete_main_task(
                "enumeration", f"Found {len(media_messages)} media files"
            )

        # For incremental enumeration, merge with existing files
        if incremental and existing_files:
            media_messages.update(existing_files)
            logger.info(
                f"Merged with {len(existing_files)} existing files, total: {len(media_messages)}"
            )

        # Store counts for caller
        media_messages._enumeration_stats = {
            "new_count": new_media_count,
            "total_count": len(media_messages),
            "existing_count": len(existing_files) if existing_files else 0,
            "total_messages": total_messages_scanned,
            "media_messages": media_messages_found,
            "text_messages": text_messages_found,
        }

        # Save enumerated files - use entity.id as the proper telegram channel ID
        telegram_channel_id = entity.id if hasattr(entity, "id") else chat_id
        logger.debug(
            f"Saving enumerated files with telegram_channel_id={telegram_channel_id}, type={type(telegram_channel_id)}"
        )
        await save_enumerated_files(channel_name, media_messages, telegram_channel_id)

        # Save enumeration metadata independently - handle database errors separately
        await _save_metadata_safely(channel_name, media_messages, metadata)

        return media_messages

    except (TimeoutError, ConnectionError) as e:
        logger.error(f"Network error enumerating media in channel {chat_id}: {str(e)}")
        return MediaMessagesDict()
    except ValueError as e:
        # Use centralized error handling to categorize the error
        error_category = TelegramErrorHandler.categorize_error(str(e))

        if error_category == "disconnection":
            logger.error(
                f"Connection error during enumeration in channel {chat_id}: {str(e)}"
            )
            logger.info("Attempting to reconnect and retry enumeration...")

            # Try to reconnect and retry once
            try:
                if await ensure_client_connected(client, "enumeration retry"):
                    logger.info("Reconnection successful, retrying enumeration...")
                    # Retry the enumeration with the reconnected client
                    return await enumerate_media_in_channel(
                        client,
                        chat_id,
                        limit=limit,
                        channel_name=channel_name,
                        incremental=incremental,
                        progress=progress,
                        termination_event=termination_event,
                        _retry_count=_retry_count + 1,
                    )
                else:
                    logger.error("Reconnection attempt failed")
            except Exception as reconnect_error:
                logger.error(f"Error during reconnection attempt: {reconnect_error}")
                # If reconnection itself fails, try one more time with a fresh connection attempt
                try:
                    logger.info("Attempting final reconnection...")
                    await client.disconnect()
                    await asyncio.sleep(2)  # Brief pause before reconnection
                    await client.connect()
                    if client.is_connected():
                        logger.info(
                            "Final reconnection successful, retrying enumeration..."
                        )
                        return await enumerate_media_in_channel(
                            client,
                            chat_id,
                            limit=limit,
                            channel_name=channel_name,
                            incremental=incremental,
                            progress=progress,
                            termination_event=termination_event,
                            _retry_count=_retry_count + 1,
                        )
                except Exception as final_reconnect_error:
                    logger.error(
                        f"Final reconnection attempt failed: {final_reconnect_error}"
                    )
        else:
            logger.error(f"Invalid channel ID or data error: {str(e)}")
        return MediaMessagesDict()
    except (ConfigurationError, DnldTelegramError) as e:
        # Handle application-specific errors separately from Telegram connection issues
        logger.error(
            f"Configuration or application error in channel {chat_id}: {str(e)}"
        )
        logger.info("This is not a connection issue - check channel configuration")
        return MediaMessagesDict()
    except Exception as e:
        logger.error(
            f"Unexpected error enumerating media in channel {chat_id}: {str(e)}"
        )
        return MediaMessagesDict()
