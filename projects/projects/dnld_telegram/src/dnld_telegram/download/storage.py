import os
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from .config import should_download_media_type
from .database.storage import get_storage
from .database.storage import load_downloaded_files as db_load_downloaded_files

# Import database functions - database storage is required
from .database.storage import load_enumerated_files as db_load_enumerated_files
from .database.storage import load_enumeration_metadata as db_load_enumeration_metadata
from .database.storage import save_downloaded_files as db_save_downloaded_files
from .database.storage import save_enumerated_files as db_save_enumerated_files
from .database.storage import save_enumeration_metadata as db_save_enumeration_metadata

logger.debug("Database storage layer initialized - using SQLite backend")

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except Exception:
        return False


def validate_path_safety(file_path):
    """Validate that a file path is safe and within expected boundaries."""
    try:
        # Convert to Path object for safe manipulation
        path_obj = Path(file_path).resolve()
        base_path = Path(PROJECT_ROOT).resolve()

        # Check if the resolved path is within the base directory
        path_obj.relative_to(base_path)

        logger.debug(f"Path safety validation passed for: {file_path}")
        return True
    except (ValueError, OSError) as e:
        # For relative paths within project directory, this is expected and safe
        # Only warn for actual security concerns (directory traversal, etc.)
        if (
            ".." in file_path
            or file_path.startswith("/")
            or "\\" in file_path.replace(os.sep, "")
        ):
            logger.warning(f"Potentially unsafe path detected: {file_path} - {e}")
            return False
        else:
            logger.debug(
                f"Path safety check - relative path within working directory: {file_path}"
            )
            return True


def validate_channel_name(channel_name):
    """Validate channel name to prevent directory traversal and other security issues."""
    if not channel_name:
        raise ValueError("Channel name cannot be empty")

    # Convert to string and strip whitespace
    channel_name = str(channel_name).strip()

    # Check for directory traversal attempts
    if ".." in channel_name or "/" in channel_name or "\\" in channel_name:
        raise ValueError(
            "Channel name contains invalid characters (directory traversal)"
        )

    # Check for reserved names on Windows
    reserved_names = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }
    if channel_name.upper() in reserved_names:
        raise ValueError(f"Channel name '{channel_name}' is a reserved system name")

    # Check for invalid characters
    invalid_chars = '<>:"|?*'
    if any(char in channel_name for char in invalid_chars):
        raise ValueError(f"Channel name contains invalid characters: {invalid_chars}")

    # Check length
    if len(channel_name) > 255:
        raise ValueError("Channel name is too long (max 255 characters)")

    # Check for only dots (which could cause issues)
    if channel_name.strip(".") == "":
        raise ValueError("Channel name cannot consist only of dots")

    return channel_name


async def load_downloaded_files(channel_name):
    """Load the list of already downloaded files for a channel."""
    logger.debug(f"load_downloaded_files called with channel_name='{channel_name}'")
    return await db_load_downloaded_files(channel_name)


async def save_downloaded_files(channel_name, downloaded_files):
    """Save the list of downloaded files for a channel."""
    logger.debug(f"save_downloaded_files called with channel_name='{channel_name}'")
    await db_save_downloaded_files(channel_name, downloaded_files)


async def load_enumerated_files(channel_name):
    """Load the list of enumerated files for a channel."""
    logger.debug(f"load_enumerated_files called with channel_name='{channel_name}'")
    return await db_load_enumerated_files(channel_name)


async def save_enumerated_files(
    channel_name, enumerated_files, telegram_channel_id=None
):
    """Save the list of enumerated files for a channel with proper concurrency handling."""
    logger.debug(
        f"save_enumerated_files called with channel_name='{channel_name}', telegram_channel_id={telegram_channel_id}"
    )

    if telegram_channel_id is None:
        raise ValueError("telegram_channel_id is required for database storage")

    logger.debug(
        f"Saving enumerated files with telegram_channel_id={telegram_channel_id}"
    )
    await db_save_enumerated_files(channel_name, enumerated_files, telegram_channel_id)
    logger.debug("Database save successful")


async def load_enumeration_metadata(channel_name):
    """Load enumeration metadata for a channel."""
    logger.debug(f"load_enumeration_metadata called with channel_name='{channel_name}'")
    return await db_load_enumeration_metadata(channel_name)


async def save_enumeration_metadata(channel_name, metadata):
    """Save enumeration metadata for a channel."""
    logger.debug(f"save_enumeration_metadata called with channel_name='{channel_name}'")
    await db_save_enumeration_metadata(channel_name, metadata)


async def remove_from_enumerated_files(channel_name, message_id):
    """DEPRECATED: Remove a message from the enumerated files list after successful download.
    Use update_enumerated_file_status() instead to maintain complete audit trail."""
    logger.debug(
        f"remove_from_enumerated_files called with channel_name='{channel_name}', message_id={message_id}"
    )
    enumerated_files = await load_enumerated_files(channel_name)
    if str(message_id) in enumerated_files:
        del enumerated_files[str(message_id)]
        await save_enumerated_files(channel_name, enumerated_files)


async def update_enumerated_file_status(
    channel_name, message_id, new_status, log_level="info"
):
    """Update the status of a file in the enumerated files list.

    Args:
        channel_name: Name of the channel
        message_id: Message ID to update
        new_status: New status to set
        log_level: Logging level ('info', 'debug', 'warning')

    Returns:
        bool: True if status was updated, False if file not found or status unchanged
    """
    logger.debug(
        f"update_enumerated_file_status called with channel_name='{channel_name}', "
        f"message_id={message_id}, new_status='{new_status}'"
    )

    storage = get_storage(channel_name)
    await storage.update_download_status(message_id, new_status)

    # Log with appropriate level
    log_message = f"Updated message {message_id} status to '{new_status}'"
    if log_level == "info":
        logger.info(log_message)
    elif log_level == "warning":
        logger.warning(log_message)
    else:
        logger.debug(log_message)

    return True


def get_file_id(media):
    """Extract file ID from media object."""
    logger.debug(f"get_file_id called with media={type(media)}")
    if hasattr(media, "document") and media.document:
        return str(media.document.id)
    elif hasattr(media, "photo") and media.photo:
        return str(media.photo.id)
    elif hasattr(media, "extended_media") and media.extended_media:
        # Handle MessageMediaPaidMedia with extended_media
        for ext_media in media.extended_media:
            if hasattr(ext_media, "media") and ext_media.media:
                # Recursively get file ID from extended media
                return get_file_id(ext_media.media)
    # For MessageMediaPaidMedia without accessible extended_media, generate a unique ID
    media_type = type(media).__name__
    if media_type == "MessageMediaPaidMedia":
        # Use a hash of the media object to create a consistent ID
        return f"paid_media_{hash(str(media))}"
    return None


def get_temp_download_dir(channel_name):
    """Get the path to the temporary download directory for a channel."""
    from .config.paths import get_channel_temp_path

    # Validate and sanitize channel_name to prevent directory traversal
    safe_channel_name = validate_channel_name(channel_name)
    path = str(get_channel_temp_path(safe_channel_name))

    # Additional path safety validation
    if not validate_path_safety(path):
        raise ValueError(f"Unsafe path detected for channel '{channel_name}'")

    logger.debug(
        f"get_temp_download_dir called with channel_name='{channel_name}', returning path='{path}'"
    )
    return path


# === Enhanced Database Functions ===
# These functions expose enhanced database functionality when available


async def get_messages_to_download(
    channel_name: str,
    limit: int | None = None,
    media_type_filter: str = "all",
    telegram_id: int | None = None,
) -> list:
    """Get messages that need to be downloaded (database-enhanced function)."""
    storage = get_storage(channel_name, telegram_id)
    messages = await storage.get_messages_to_download(limit)

    # First filter out unddownloadable media types
    downloadable_messages = []
    for msg in messages:
        media_type = msg.get("media_type", "")
        # Skip media types that are not directly downloadable files
        if media_type in [
            "MessageMediaWebPage",
            "MessageMediaGiveaway",
            "MessageMediaPaidMedia",
        ]:
            continue
        downloadable_messages.append(msg)

    # Apply additional media type filter if specified
    if media_type_filter != "all":
        filtered_messages = []
        for msg in downloadable_messages:
            if should_download_media_type(
                msg.get("media_type", ""), msg.get("filename", ""), media_type_filter
            ):
                filtered_messages.append(msg)
        return filtered_messages

    return downloadable_messages


async def get_channel_statistics(channel_name: str) -> dict[str, Any]:
    """Get comprehensive channel statistics (database-enhanced function)."""
    storage = get_storage(channel_name)
    return await storage.get_channel_statistics()


def atomic_json_dump(data: dict, target: Path) -> None:
    """Atomically dumps data to a JSON file, ensuring data integrity.
    Writes to a temporary file first, then renames it to the target.
    """
    import json

    temp_file = target.with_suffix(f".{os.getpid()}.tmp")
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    os.replace(temp_file, target)
    logger.debug(f"Atomically dumped JSON to {target}")


def ensure_database_initialized(channel_name: str, telegram_channel_id: int) -> bool:
    """Ensure database is initialized for a channel (database-only function)."""
    try:
        from .database.schema import ensure_channel_exists

        ensure_channel_exists(channel_name, telegram_channel_id)
        logger.info(
            f"Database initialized for channel '{channel_name}' (ID: {telegram_channel_id})"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database for channel '{channel_name}': {e}")
        return False


# === Message Content and Thread Functions ===


async def save_message_with_content(
    channel_name: str,
    telegram_id: int,
    message_text: str | None = None,
    reply_to_message_id: int | None = None,
    date: datetime | None = None,
    media_type: str | None = None,
    file_id: str | None = None,
    file_size: int | None = None,
) -> bool:
    """Save a complete message with text content and thread relationship."""
    try:
        storage = get_storage(channel_name)
        await storage.save_message_with_content(
            telegram_id,
            message_text,
            reply_to_message_id,
            date,
            media_type,
            file_id,
            file_size,
        )
        return True
    except Exception as e:
        logger.error(
            f"Failed to save message content for channel '{channel_name}': {e}"
        )
        return False


async def get_messages_by_thread(
    channel_name: str, thread_root_id: int | None = None, include_root: bool = True
) -> list[dict[str, Any]]:
    """Get messages organized by thread (database-enhanced function)."""
    try:
        storage = get_storage(channel_name)
        return await storage.get_messages_by_thread(thread_root_id, include_root)
    except Exception as e:
        logger.error(
            f"Failed to get messages by thread for channel '{channel_name}': {e}"
        )
        return []


async def get_thread_roots(channel_name: str) -> list[dict[str, Any]]:
    """Get all thread root messages (messages that have replies)."""
    try:
        storage = get_storage(channel_name)
        return await storage.get_thread_roots()
    except Exception as e:
        logger.error(f"Failed to get thread roots for channel '{channel_name}': {e}")
        return []


async def search_messages(
    channel_name: str, search_text: str, limit: int = 50
) -> list[dict[str, Any]]:
    """Search messages by text content (database-enhanced function)."""
    try:
        storage = get_storage(channel_name)
        return await storage.search_messages(search_text, limit)
    except Exception as e:
        logger.error(f"Failed to search messages for channel '{channel_name}': {e}")
        return []
