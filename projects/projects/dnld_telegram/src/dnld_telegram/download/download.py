import asyncio
import os
import shutil
import time
import uuid
from contextlib import asynccontextmanager
from enum import Enum
from typing import Any

from loguru import logger
from telethon import TelegramClient  # type: ignore
from telethon.tl.types import Message  # type: ignore

from .channel_fixer import ChannelFixer
from .config.logging_config import log_performance
from .display import show_enhanced_enumeration_display
from .storage import (
    get_file_id,
    get_messages_to_download,
    get_temp_download_dir,
    load_downloaded_files,
    save_downloaded_files,
    save_enumerated_files,
    update_enumerated_file_status,
)
from .telegram_errors import TelegramErrorHandler

# --- Configuration Constants ---
FILENAME_MAX_LENGTH = (
    200  # Max length for generated filenames to avoid Windows path limits
)
PROGRESS_UPDATE_BYTES_THRESHOLD = 5 * 1024 * 1024  # Update progress every 5MB
PROGRESS_UPDATE_TIME_THRESHOLD = 5.0  # Update progress every 5 seconds
MIN_TIMEOUT_SECONDS = (
    60  # Minimum download timeout (1 minute) - reduced for smaller files
)
MAX_TIMEOUT_SECONDS = (
    1800  # Maximum download timeout (30 minutes) - as per strategy for 50GB+ channels
)
ASSUMED_MIN_SPEED_BPS = 50 * 1024  # Assumed minimum download speed (50 KB/s)
DISK_SPACE_BUFFER_PERCENT = 0.1  # 10% buffer for disk space check

# --- Helper Functions ---


def _get_file_type_icon(filename: str) -> str:
    """Get appropriate icon based on file extension."""
    if not filename:
        return "📁"

    extension = filename.lower().split(".")[-1] if "." in filename else ""

    # Video files
    if extension in ["mp4", "avi", "mov", "mkv", "wmv", "flv", "m4v", "webm"]:
        return "🎥"
    # Image files
    elif extension in ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp"]:
        return "🖼️"
    # Audio files
    elif extension in ["mp3", "wav", "flac", "aac", "m4a", "ogg"]:
        return "🎵"
    # Document files
    elif extension in ["pdf", "doc", "docx", "txt", "rtf"]:
        return "📄"
    # Archive files
    elif extension in ["zip", "rar", "7z", "tar", "gz"]:
        return "📦"
    # Binary/unknown files
    elif extension in ["bin", "exe", "dll"]:
        return "⚙️"
    # Default
    else:
        return "📁"


def _log_with_progress(
    message: str, progress: Any | None = None, level: str = "info"
) -> None:
    """Logs a message, respecting tqdm's reserved region for progress bars.

    CRITICAL: tqdm reserves the bottom portion of the terminal for progress bars.
    This reserved region CANNOT be disrupted by regular print/log statements.
    All status messages must go ABOVE the reserved region using tqdm.write().

    The reserved region layout:
    - Top of terminal: Status messages (via tqdm.write())
    - Bottom of terminal: Reserved region for progress bars (positions 0, 1, 2, etc.)
    - NEVER mix regular print/log with active tqdm bars - it breaks positioning
    """
    if (
        progress
        and hasattr(progress, "__class__")
        and "TQDM" in progress.__class__.__name__
    ):
        # Use tqdm.write() to output above the reserved progress bar region
        try:
            from tqdm import tqdm

            tqdm.write(message)
        except ImportError:
            # Fallback if tqdm not available
            getattr(logger, level)(message)
    elif progress and hasattr(progress, "log"):
        # For non-tqdm displays, use their log method
        progress.log(message)
    else:
        # Standard logging for cases without progress display
        getattr(logger, level)(message)


def _determine_filename_and_extension(message: Message, message_id: int) -> str:
    """Determines the final filename and extension for a given message."""
    final_filename: str
    try:
        msg_file = getattr(message, "file", None)  # type: ignore[attr-defined]
        name_val = getattr(msg_file, "name", None) if msg_file is not None else None
        if name_val:
            final_filename = str(name_val)
        else:
            raise AttributeError("no name")
    except Exception:
        # Generate filename with appropriate extension based on media type
        extension = ""
        mime_type = ""

        # Try to get MIME type
        try:
            msg_file = getattr(message, "file", None)  # type: ignore[attr-defined]
            mime_type_val = (
                getattr(msg_file, "mime_type", None) if msg_file is not None else None
            )
            if mime_type_val:
                mime_type = str(mime_type_val).lower()
        except Exception:
            mime_type = ""

        # Determine extension from MIME type
        if mime_type:
            if mime_type.startswith("image/"):
                extension = (
                    ".jpg" if "jpeg" in mime_type else f".{mime_type.split('/')[-1]}"
                )
            elif mime_type.startswith("video/"):
                extension = f".{mime_type.split('/')[-1]}"
            elif mime_type.startswith("audio/"):
                extension = f".{mime_type.split('/')[-1]}"
            elif mime_type == "application/pdf":
                extension = ".pdf"
            elif mime_type.startswith("application/"):
                # Handle common application types
                if "zip" in mime_type:
                    extension = ".zip"
                elif "rar" in mime_type:
                    extension = ".rar"
                elif "json" in mime_type:
                    extension = ".json"
                elif "xml" in mime_type:
                    extension = ".xml"
                else:
                    # Generic application file, use the subtype
                    subtype = mime_type.split("/")[-1]
                    extension = f".{subtype}" if subtype else ".bin"
            else:
                # Unknown MIME type, try to extract extension
                if "/" in mime_type:
                    subtype = mime_type.split("/")[-1]
                    extension = f".{subtype}"

        # If no extension from MIME type, try media type class name
        if not extension:
            media_type_name = type(message.media).__name__
            if "Photo" in media_type_name:
                extension = ".jpg"
            elif "Document" in media_type_name:
                # For documents, try harder to detect the type
                extension = ".doc"  # More reasonable default than .bin
            elif "Video" in media_type_name:
                extension = ".mp4"
            elif "Audio" in media_type_name:
                extension = ".mp3"

        # Final fallback to .unknown if we still can't determine
        if not extension:
            extension = ".unknown"

        final_filename = f"{message_id}{extension}"
        logger.debug(
            f"Message {message_id}: mime_type='{mime_type}', extension='{extension}', media_type='{type(message.media).__name__}'"
        )

    # Ensure filename isn't too long for Windows (260 char path limit)
    if len(final_filename) > FILENAME_MAX_LENGTH:  # Leave room for directory path
        name, ext = os.path.splitext(final_filename)
        # Truncate name but keep extension
        final_filename = f"{name[: FILENAME_MAX_LENGTH - 3 - len(ext)]}...{ext}"
        logger.debug(f"Truncated long filename to: {final_filename}")

    return final_filename


# Global termination event - will be set by main module
termination_event: asyncio.Event | None = None


@asynccontextmanager
async def download_context(channel_name: str, operation: str):
    """Async context manager for structured logging of download operations."""
    start_time = time.time()
    # Generate a more unique context ID with UUID for better correlation
    context_id = f"{channel_name}_{operation}_{int(start_time)}_{str(uuid.uuid4())[:8]}"

    # Add structured context for all logs within this context
    with logger.contextualize(
        context_id=context_id,
        channel=channel_name,
        operation=operation,
        start_time=start_time,
    ):
        logger.info(
            f"START: {operation} for channel '{channel_name}' (context_id: {context_id})"
        )

        try:
            yield context_id

            elapsed = time.time() - start_time
            logger.info(
                f"END: {operation} for channel '{channel_name}' (context_id: {context_id}) - Duration: {elapsed:.2f}s"
            )

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(
                f"ERROR: {operation} for channel '{channel_name}' (context_id: {context_id}) - Duration: {elapsed:.2f}s - Error: {str(e)}"
            )
            raise


class DownloadResult(Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


@log_performance("download_media")
async def _download_media(
    client: TelegramClient,
    message: Message,
    save_directory: str,
    channel_name: str,
    downloaded_files: dict[int, dict[str, Any]],
    progress: Any | None = None,
) -> DownloadResult:
    """Download media from a message and handle progress, temporary files, and tracking."""
    global termination_event

    message_id = message.id

    # Add structured logging context for async debugging with better correlation
    task_id = str(uuid.uuid4())[:8]
    with logger.contextualize(
        message_id=message_id,
        channel=channel_name,
        task_id=task_id,
        media_type=type(message.media).__name__ if message.media else "unknown",
    ):
        logger.info("Starting media download")

        if save_directory is None:
            logger.error("save_directory is None - cannot download media")
            return DownloadResult.ERROR

        if channel_name is None:
            logger.error("channel_name is None - cannot download media")
            return DownloadResult.ERROR

        # Create temporary download directory
        temp_dir = get_temp_download_dir(channel_name)
        os.makedirs(temp_dir, exist_ok=True)

        # Safely get file attributes via getattr/hasattr to satisfy Telethon's dynamic API
        total_bytes = 0
        try:
            msg_file = getattr(message, "file", None)  # type: ignore[attr-defined]
            if msg_file is not None:
                size_val = getattr(msg_file, "size", None)
                if size_val is not None:
                    total_bytes = int(size_val)
        except Exception:
            total_bytes = 0

        # Get filename using extracted helper function
        final_filename = _determine_filename_and_extension(message, message_id)

        # Generate unique temporary filename to avoid conflicts
        temp_filename = f"temp_download_{uuid.uuid4().hex}_{final_filename}"
        temp_file_path = os.path.join(temp_dir, temp_filename)

        # Create individual task for this download (Rich supports multiple concurrent tasks)
        # DEBUG: Add logging to trace progress bar creation
        download_task_id = None
        if progress:
            # Determine the correct attribute name for tracking download tasks
            # This handles both RichProgressDisplay (download_tasks) and TQDMDisplay (download_tqdms)
            task_attribute_name = None
            if hasattr(progress, "download_tasks"):
                task_attribute_name = "download_tasks"
            elif hasattr(progress, "download_tqdms"):
                task_attribute_name = "download_tqdms"

            # Check if we already have a task with this filename (for retries)
            if task_attribute_name and hasattr(progress, task_attribute_name):
                existing_tasks = getattr(progress, task_attribute_name, {})
                if final_filename in existing_tasks:
                    # Reuse existing task for retries
                    download_task_id = final_filename
                else:
                    # Create new task only if it doesn't exist
                    download_task_id = progress.add_download_task(
                        final_filename, total_bytes
                    )
                    progress.start_download_task(download_task_id)
            else:
                # Fallback: create new task if attribute not found
                download_task_id = progress.add_download_task(
                    final_filename, total_bytes
                )
                progress.start_download_task(download_task_id)

        # Progress callback with proper Rich task updates
        last_current = 0
        last_update_time = 0

        def progress_callback(current: int, total: int) -> None:
            nonlocal last_current, last_update_time
            now = time.time()
            # Update every 5MB or 5 seconds for performance
            bytes_since_last = current - last_current
            time_since_last = now - last_update_time
            if (
                bytes_since_last >= PROGRESS_UPDATE_BYTES_THRESHOLD
                or time_since_last >= PROGRESS_UPDATE_TIME_THRESHOLD
                or current == total
            ):
                # Update progress display if available
                if progress and download_task_id:
                    progress.update_download_task(download_task_id, bytes_since_last)

                last_current = current
                last_update_time = now

        try:
            if total_bytes == 0:
                # For zero-byte files, treat as an instant download
                if progress and download_task_id:
                    progress.complete_download_task(download_task_id)
                return DownloadResult.SUCCESS

            # Check available disk space before download
            try:
                available_space = shutil.disk_usage(save_directory).free
                # Add 10% buffer for safety
                required_space = int(total_bytes * (1 + DISK_SPACE_BUFFER_PERCENT))
                if required_space > available_space:
                    logger.error(
                        f"Not enough disk space for {final_filename}: need {required_space / (1024**3):.1f}GB, have {available_space / (1024**3):.1f}GB"
                    )
                    if progress and download_task_id:
                        progress.error_download_task(
                            download_task_id, "Insufficient disk space"
                        )
                    return DownloadResult.ERROR
            except Exception as e:
                logger.warning(f"Could not check disk space: {e}")

            # Download with generous timeout based on file size
            # Enhanced timeout formula from Large Database Strategy:
            # For 50GB+ channels: timeout = min(1800, max(60, base_timeout + (size_gb * 30)))
            file_size_gb = (total_bytes / (1024**3)) if total_bytes else 0
            base_timeout = 60  # 1 minute base
            size_based_timeout = base_timeout + (file_size_gb * 30)  # Add 30s per GB
            timeout_seconds = float(
                min(MAX_TIMEOUT_SECONDS, max(MIN_TIMEOUT_SECONDS, size_based_timeout))
            )

            try:
                logger.debug(f"Attempting to download media for message {message.id}")
                logger.debug(
                    f"File size: {total_bytes} bytes, timeout: {timeout_seconds}s"
                )
                logger.debug(f"Download path: {temp_file_path}")

                # Enhanced progress callback that checks for termination
                def enhanced_progress_callback(current: int, total: int) -> None:
                    # Check termination event first
                    if termination_event and termination_event.is_set():
                        logger.info(
                            "🛑 Termination requested during download, attempting to cancel..."
                        )
                        print(
                            "🛑 Termination requested during download, attempting to cancel...",
                            flush=True,
                        )
                        raise asyncio.CancelledError(
                            "Download cancelled due to termination request"
                        )

                    # Call original progress callback logic
                    progress_callback(current, total)

                # Telethon progress_callback signature accepts (bytes_downloaded, total_bytes)
                downloaded_file_path = await asyncio.wait_for(
                    client.download_media(
                        message,
                        file=str(temp_file_path),  # ensure str for typing
                        progress_callback=enhanced_progress_callback
                        if progress
                        else None,  # type: ignore[arg-type]
                    ),
                    timeout=timeout_seconds,  # Dynamic timeout based on file size
                )
                logger.debug(
                    f"Download completed for message {message.id}, path: {downloaded_file_path}"
                )
            except TimeoutError as e:
                # Use structured error handling for timeouts
                # Suppress logs if using TQDM to prevent breaking progress display
                suppress_logs = bool(
                    progress
                    and hasattr(progress, "__class__")
                    and "TQDM" in progress.__class__.__name__
                )
                await TelegramErrorHandler.handle_telegram_error(
                    e,
                    message_id,
                    attempt=1,
                    termination_event=termination_event,
                    suppress_logs=suppress_logs,
                )
                if not suppress_logs:
                    logger.warning(
                        f"Download timeout for {final_filename} after {timeout_seconds / 60:.1f} minutes"
                    )
                if progress and download_task_id:
                    progress.error_download_task(download_task_id, "Download timeout")
                return DownloadResult.TIMEOUT  # Return special timeout status

            # Complete the download task
            if progress and download_task_id:
                progress.complete_download_task(download_task_id)

        except (asyncio.CancelledError, Exception) as e:
            # Use structured error handling for download interruptions
            if isinstance(e, asyncio.CancelledError):
                logger.debug(f"Download of message {message_id} was cancelled")
            else:
                # Suppress logs if using TQDM to prevent breaking progress display
                suppress_logs = bool(
                    progress
                    and hasattr(progress, "__class__")
                    and "TQDM" in progress.__class__.__name__
                )
                await TelegramErrorHandler.handle_telegram_error(
                    e,
                    message_id,
                    attempt=1,
                    termination_event=termination_event,
                    suppress_logs=suppress_logs,
                )
                if not suppress_logs:
                    logger.info(
                        f"Download of message {message_id} was interrupted: {type(e).__name__}"
                    )

            # Clean up the temporary file if it exists
            if os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    logger.debug(
                        f"Cleaned up partial download for message {message_id}"
                    )
                except Exception as cleanup_e:
                    logger.error(
                        f"Error cleaning up partial download for message {message_id}: {str(cleanup_e)}"
                    )

            return (
                DownloadResult.ERROR
            )  # Indicate that the download was cancelled or interrupted

        # Check if download was successful
        if not downloaded_file_path:
            logger.error(
                f"Error: Could not download media from message {message_id}. downloaded_file_path is None."
            )
            return DownloadResult.ERROR

        # Check if termination was requested after downloading
        if termination_event and termination_event.is_set():
            logger.info("Termination requested. Stopping download process...")
            # Clean up the temporary file if it exists
            if os.path.exists(downloaded_file_path):
                try:
                    os.remove(downloaded_file_path)
                    logger.info(f"Cleaned up temporary file: {downloaded_file_path}")
                except Exception as e:
                    logger.error(
                        f"Error cleaning up temporary file {downloaded_file_path}: {str(e)}"
                    )
            return DownloadResult.ERROR

        # Get the final file path using the original filename
        final_file_path = os.path.join(save_directory, final_filename)

        # Move file from temporary location to final location
        try:
            shutil.move(str(downloaded_file_path), str(final_file_path))
            # Skip completion messages during concurrent downloads to avoid interrupting progress bars
            # Completion status is already shown by the progress bars themselves
            # Final summary will be shown at the end with all results
            if (
                progress
                and hasattr(progress, "__class__")
                and "TQDM" in progress.__class__.__name__
            ):
                # For tqdm, suppress individual completion messages to maintain clean progress bar display
                # The progress bars already show completion status with their final state
                pass
            else:
                # For non-tqdm displays, show completion message
                display_filename = final_filename
                if (
                    progress
                    and hasattr(progress, "config")
                    and progress.config
                    and hasattr(progress.config, "max_name_width")
                ):
                    max_width = progress.config.max_name_width
                    if len(display_filename) > max_width:
                        display_filename = display_filename[: max_width - 3] + "..."
                icon = _get_file_type_icon(display_filename)
                _log_with_progress(f"{icon} {display_filename}", progress)

            # Verify file integrity after download
            if os.path.exists(final_file_path):
                actual_size = os.path.getsize(final_file_path)
                if total_bytes > 0 and actual_size != total_bytes:
                    logger.warning(
                        f"Size mismatch for {final_filename}: expected {total_bytes:,} bytes, got {actual_size:,} bytes"
                    )
                    # Don't fail here - file might still be usable, just log the warning
                else:
                    logger.debug(
                        f"File integrity verified: {final_filename} ({actual_size:,} bytes)"
                    )

        except (FileNotFoundError, PermissionError) as e:
            logger.error(
                f"File system error moving file from temporary to final location: {str(e)}"
            )
            return DownloadResult.ERROR
        except Exception as e:
            logger.error(
                f"Unexpected error moving file from temporary to final location: {str(e)}"
            )
            return DownloadResult.ERROR

        # Update the file path to be relative to temp directory for tracking
        relative_file_path = os.path.join(channel_name, "_media", final_filename)
        logger.debug(f"_download_media - relative_file_path='{relative_file_path}'")

        # Update downloaded files tracker
        file_id = get_file_id(message.media)
        downloaded_files[message_id] = {
            "chat_id": getattr(message, "chat_id", None),
            "message_id": message_id,
            "file_path": relative_file_path,
            "file_id": file_id,
            "timestamp": message.date.isoformat() if message.date else None,
        }

        # Mark as successfully downloaded in enumerated files
        await update_enumerated_file_status(channel_name, message_id, "completed")

        # Save download tracking immediately to prevent re-downloads on subsequent runs
        await save_downloaded_files(channel_name, downloaded_files)

        return DownloadResult.SUCCESS


async def download_media_from_message(
    client, chat_id, message_id, save_directory, channel_name
):
    """Download media from a specific message using a temporary download approach."""
    logger.debug(
        f"download_media_from_message called with channel_name='{channel_name}'"
    )
    global termination_event

    # Input validation
    if not client:
        raise ValueError("Client cannot be None")
    if not chat_id:
        raise ValueError("Chat ID cannot be empty")
    if not isinstance(message_id, int) or message_id <= 0:
        raise ValueError("Message ID must be a positive integer")
    if not save_directory or not isinstance(save_directory, str):
        raise ValueError("Save directory must be a non-empty string")
    if not channel_name or not isinstance(channel_name, str):
        raise ValueError("Channel name must be a non-empty string")

    try:
        # Check if termination was requested before starting
        if termination_event and termination_event.is_set():
            print("\nTermination requested. Stopping download process...")
            return False

        # Get the entity (channel/user) with error handling
        try:
            entity = await client.get_entity(chat_id)
        except Exception as e:
            error_category = TelegramErrorHandler.categorize_error(str(e))
            if error_category == "chat":
                # Channel ID error - try to auto-fix
                fixed_id = await ChannelFixer.auto_fix_channel_id(
                    client, channel_name, chat_id
                )
                if fixed_id is not None:
                    # Fix succeeded, persist it and retry
                    ChannelFixer.persist_fix(channel_name, chat_id, fixed_id)

                    # Retry with fixed ID
                    try:
                        return await download_media_from_message(
                            client, fixed_id, message_id, save_directory, channel_name
                        )
                    except Exception:
                        # Retry failed - show that the fix didn't work
                        try:
                            from tqdm import tqdm

                            tqdm.write(
                                f"❌ Channel '{channel_name}' auto-fix failed - retry unsuccessful"
                            )
                        except ImportError:
                            logger.error(
                                f"❌ Channel '{channel_name}' auto-fix failed - retry unsuccessful"
                            )
                        return False
                else:
                    # Auto-fix failed - show helpful error
                    try:
                        from tqdm import tqdm

                        tqdm.write(
                            f"❌ Channel '{channel_name}' has invalid chat ID {chat_id} - skipping message {message_id}"
                        )
                        tqdm.write(
                            "   💡 To fix: python src/find_channel_id.py --fix-toml"
                        )
                    except ImportError:
                        logger.error(
                            f"❌ Channel '{channel_name}' has invalid chat ID {chat_id} - skipping message {message_id}"
                        )
                        logger.info(
                            "   💡 To fix: python src/find_channel_id.py --fix-toml"
                        )
                    return False  # Return False to indicate download failed
            else:
                # Re-raise other types of errors
                raise

        # Get the specific message
        message = await client.get_messages(entity, ids=message_id)

        if not message:
            logger.warning(f"Message {message_id} not found in chat {chat_id}")
            return False

        if not message.media:
            logger.warning(f"No media found in message {message_id}")
            return False

        # Show what we're downloading
        media_type = type(message.media).__name__
        media_type = type(message.media).__name__

        # Skip media types that are not directly downloadable files
        if media_type in [
            "MessageMediaWebPage",
            "MessageMediaGiveaway",
            "MessageMediaPaidMedia",
        ]:
            logger.debug(
                f"Skipping {media_type} from message {message_id} as it is not a direct downloadable file."
            )
            return True  # Indicate success for skipping

        # Create save directory if it doesn't exist
        os.makedirs(save_directory, exist_ok=True)

        # Get file ID for tracking
        file_id = get_file_id(message.media)
        if not file_id:
            logger.warning(
                f"Could not get file ID for message {message_id} (media_type: {media_type})"
            )
            # Mark as unable to get file ID for tracking
            update_enumerated_file_status(
                channel_name, message_id, STATUS_NO_FILE_ID, "warning"
            )
            return True  # Skip this file gracefully

        # Check if file already downloaded
        # ASYNC REQUIREMENT: load_downloaded_files() is async and MUST be awaited
        # Fixed: Added await to prevent "RuntimeWarning: coroutine never awaited"
        downloaded_files = await load_downloaded_files(channel_name)

        # Check if file with same ID already downloaded
        already_downloaded = False
        for downloaded_msg_id, downloaded_info in downloaded_files.items():
            if downloaded_info.get("file_id") == file_id:
                already_downloaded = True
                break

        if already_downloaded:
            # Mark as already downloaded in enumerated files
            update_enumerated_file_status(
                channel_name, message_id, "completed", "debug"
            )
            logger.debug(f"Message {message_id} already downloaded, skipping")
            return True

        # Check if termination was requested before downloading
        if termination_event and termination_event.is_set():
            print("\nTermination requested. Stopping download process...")
            return False

        logger.debug(f"Starting actual download for message {message_id}")
        result = await _download_media(
            client, message, save_directory, channel_name, downloaded_files
        )
        logger.debug(f"Download result for message {message_id}: {result}")
        return result

    except Exception as e:
        logger.error(f"Error downloading media from message {message_id}: {str(e)}")
        return False


def _rebuild_downloaded_files_from_enumerated(enumerated_files, channel_name):
    """Rebuild downloaded files tracker by checking which enumerated files exist in _media directory."""
    from .config.paths import get_channel_media_path

    media_dir = str(get_channel_media_path(channel_name))
    downloaded_files = {}

    # Get list of actual files in media directory
    if os.path.exists(media_dir):
        existing_files = set(os.listdir(media_dir))
        logger.info(f"Found {len(existing_files)} files in {media_dir}")

        # Match enumerated files with existing files
        for message_id_str, file_info in enumerated_files.items():
            # Try to find a matching file in the media directory
            # This is approximate since we don't have the original filename mapping
            for existing_file in existing_files:
                if existing_file.endswith(".mp4"):  # Basic match for now
                    downloaded_files[message_id_str] = {
                        "chat_id": file_info.get("chat_id", -1002436706028),
                        "message_id": int(message_id_str),
                        "file_path": os.path.join(
                            channel_name, "_media", existing_file
                        ),
                        "file_id": file_info.get("file_id", "unknown"),
                        "timestamp": file_info.get("date"),
                    }
                    existing_files.remove(existing_file)  # Don't match same file twice
                    break

    logger.info(
        f"Rebuilt downloaded files tracker with {len(downloaded_files)} entries"
    )
    return downloaded_files


# Status constants for enumerated files tracking
SKIP_STATUS_NULL_FILE_ID = "skipped_null_file_id"
SKIP_STATUS_PAID_MEDIA = "skipped_paid_media"
STATUS_DOWNLOADED = "downloaded"
STATUS_DOWNLOAD_SUCCESS = (
    "download_success"  # Successfully downloaded and moved to final location
)
STATUS_DOWNLOAD_ERROR = "download_error"  # Download failed due to error
STATUS_NO_FILE_ID = "no_file_id"  # Could not extract file ID from media


def _update_file_status(
    enumerated_files, message_id_str, file_info, new_status, message_id
):
    """Update file status and return whether enumerated_files was updated."""
    current_status = file_info.get("status")
    if current_status != new_status:
        file_info["status"] = new_status
        enumerated_files[message_id_str] = file_info

        # Use appropriate log level based on status type
        if new_status in [SKIP_STATUS_NULL_FILE_ID, SKIP_STATUS_PAID_MEDIA]:
            logger.info(f"Marked message {message_id} as {new_status}")
        else:
            logger.debug(f"Marked message {message_id} as {new_status}")

        return True
    return False


async def _filter_already_downloaded(
    enumerated_files, downloaded_files, channel_name, chat_id=None
):
    """Filter out already downloaded files from the enumerated list."""
    files_to_download = {}
    enumerated_files_updated = False
    status_updates_since_save = 0
    SAVE_INTERVAL = (
        25  # Save every 25 status updates to prevent data loss (aggressive for safety)
    )

    for message_id_str, file_info in enumerated_files.items():
        message_id = int(message_id_str)

        # Skip files with null file_id or MessageMediaPaidMedia
        file_id = file_info.get("file_id")
        media_type = file_info.get("media_type", "")

        if file_id is None or media_type == "MessageMediaPaidMedia":
            # Determine appropriate skip status
            skip_status = (
                SKIP_STATUS_NULL_FILE_ID if file_id is None else SKIP_STATUS_PAID_MEDIA
            )

            # Update status if needed
            if _update_file_status(
                enumerated_files, message_id_str, file_info, skip_status, message_id
            ):
                enumerated_files_updated = True
                status_updates_since_save += 1

                # Periodic save to prevent data loss on interruption
                if status_updates_since_save >= SAVE_INTERVAL:
                    await save_enumerated_files(channel_name, enumerated_files, chat_id)
                    logger.debug(
                        f"Periodic save: updated {status_updates_since_save} file statuses"
                    )
                    status_updates_since_save = 0
            else:
                logger.debug(
                    f"Skipping message {message_id} - already marked as {skip_status}"
                )

            continue

        # Check if file with same ID already downloaded
        already_downloaded = False
        for downloaded_msg_id, downloaded_info in downloaded_files.items():
            # Compare file_id, handling None values
            if downloaded_info.get("file_id") == file_id:
                already_downloaded = True
                break

        if not already_downloaded:
            files_to_download[message_id_str] = file_info
        else:
            # Mark as already downloaded if not already marked
            if _update_file_status(
                enumerated_files,
                message_id_str,
                file_info,
                STATUS_DOWNLOADED,
                message_id,
            ):
                enumerated_files_updated = True
                status_updates_since_save += 1

                # Periodic save to prevent data loss on interruption
                if status_updates_since_save >= SAVE_INTERVAL:
                    await save_enumerated_files(channel_name, enumerated_files, chat_id)
                    logger.debug(
                        f"Periodic save: updated {status_updates_since_save} file statuses"
                    )
                    status_updates_since_save = 0

    # Final save for any remaining status updates
    if enumerated_files_updated and status_updates_since_save > 0:
        await save_enumerated_files(channel_name, enumerated_files, chat_id)
        logger.info(
            f"Final save: updated {status_updates_since_save} remaining file statuses for channel '{channel_name}'"
        )

    return files_to_download


async def _process_media_message(
    client, message, save_directory, channel_name, downloaded_files, progress=None
):
    """Process a single media message, downloading it if necessary."""
    if not message:
        logger.warning("Message not found")
        return False, True, False  # Error, Skip, No Timeout

    if not message.media:
        logger.warning(f"No media found in message {message.id}")
        return False, True, False  # Error, Skip, No Timeout

    # Show what we're downloading
    media_type = type(message.media).__name__

    # Skip media types that are not directly downloadable files
    if media_type in [
        "MessageMediaWebPage",
        "MessageMediaGiveaway",
        "MessageMediaPaidMedia",
    ]:
        return False, True, False  # Error, Skip, No Timeout

    logger.debug(
        f"Starting download for message {message.id}, media type: {media_type}"
    )
    download_result = await _download_media(
        client, message, save_directory, channel_name, downloaded_files, progress
    )
    logger.debug(
        f"Download completed for message {message.id}, result: {download_result}"
    )

    if download_result == DownloadResult.SUCCESS:
        return True, False, False  # Success, No Skip, No Timeout
    elif download_result == DownloadResult.TIMEOUT:
        return False, False, True  # Error, No Skip, Timeout
    else:
        return False, False, False  # Error, No Skip, No Timeout


@log_performance("prepare_download_session")
async def _prepare_download_session(
    client,
    chat_id,
    save_directory,
    channel_name,
    limit=None,
    incremental=False,
    progress=None,
    force_reverse_sync=False,
    skip_reverse_sync=False,
    debug_trace=False,
):
    """Prepare for download session by loading and filtering files."""
    # Remove duplicate logging - already shown in main module
    if debug_trace:
        print(
            f"🚀 TRACE: _prepare_download_session ENTRY: channel='{channel_name}', chat_id={chat_id}"
        )
    logger.debug(
        f"🚀 DEBUG: Entering _prepare_download_session for channel '{channel_name}', chat_id={chat_id}"
    )

    # Create save directory if it doesn't exist
    os.makedirs(save_directory, exist_ok=True)

    # Get the entity (channel/user) with error handling - outside context for auto-fix retries
    try:
        entity = await client.get_entity(chat_id)
        if debug_trace:
            print(
                f"✅ TRACE: Entity retrieved successfully: {getattr(entity, 'title', 'unknown')}"
            )
        logger.debug(
            f"✅ DEBUG: Entity successfully retrieved: {entity.title if hasattr(entity, 'title') else entity}"
        )
    except Exception as e:
        error_category = TelegramErrorHandler.categorize_error(str(e))
        if error_category == "chat":
            # Channel ID error - try to auto-fix
            fixed_id = await ChannelFixer.auto_fix_channel_id(
                client, channel_name, chat_id
            )
            if fixed_id is not None:
                # Fix succeeded, persist it and retry
                ChannelFixer.persist_fix(channel_name, chat_id, fixed_id)

                # Retry with fixed ID
                try:
                    return await _prepare_download_session(
                        client,
                        fixed_id,
                        save_directory,
                        channel_name,
                        limit,
                        incremental,
                        progress,
                        force_reverse_sync,
                        skip_reverse_sync,
                        debug_trace,
                    )
                except Exception:
                    # Retry failed - show that the fix didn't work
                    try:
                        from tqdm import tqdm

                        tqdm.write(
                            f"❌ Channel '{channel_name}' auto-fix failed - retry unsuccessful"
                        )
                    except ImportError:
                        logger.error(
                            f"❌ Channel '{channel_name}' auto-fix failed - retry unsuccessful"
                        )
                    if debug_trace:
                        print(
                            f"❌ TRACE: Returning None - auto-fix retry failed for channel '{channel_name}'"
                        )
                    logger.debug(
                        f"❌ DEBUG: Returning None due to failed auto-fix retry for channel '{channel_name}'"
                    )
                    return None
            else:
                # Auto-fix failed - show helpful error
                try:
                    from tqdm import tqdm

                    tqdm.write(
                        f"❌ Channel '{channel_name}' has invalid chat ID {chat_id} - skipping"
                    )
                    tqdm.write("   💡 To fix: python src/find_channel_id.py --fix-toml")
                except ImportError:
                    logger.error(
                        f"❌ Channel '{channel_name}' has invalid chat ID {chat_id} - skipping"
                    )
                    logger.info(
                        "   💡 To fix: python src/find_channel_id.py --fix-toml"
                    )
                if debug_trace:
                    print(
                        f"❌ TRACE: Returning None - auto-fix failed for channel '{channel_name}', chat_id={chat_id}"
                    )
                logger.debug(
                    f"❌ DEBUG: Returning None due to auto-fix failure for channel '{channel_name}', chat_id={chat_id}"
                )
                return None  # Return None to indicate connection error
        else:
            # Re-raise other types of errors
            raise

    # Main preparation logic with structured logging context
    async with download_context(channel_name or "unknown", "prepare_download_session"):
        if debug_trace:
            print(
                f"🔍 TRACE: Starting main preparation logic for channel '{channel_name}'"
            )
        logger.debug(
            f"🔍 DEBUG: Starting main preparation logic for channel '{channel_name}'"
        )
        # Beautiful Unified File Discovery & Sync Coordination
        # This replaces fragmented sync logic with intelligent coordination
        if skip_reverse_sync:
            logger.info(f"⏭️ File sync disabled by user for '{channel_name}'")
            # Still do basic discovery for progress tracking
            try:
                from .file_discovery_coordinator import FileDiscoveryCoordinator

                coordinator = FileDiscoveryCoordinator(channel_name)
                discovery = await coordinator.discover_complete_file_state()
                logger.info(
                    f"🎯 Discovered {len(discovery.files_on_disk)} files on disk, sync operations skipped by user"
                )
            except Exception as e:
                logger.warning(f"File discovery failed: {e}")
        else:
            try:
                from .file_discovery_coordinator import FileDiscoveryCoordinator

                # 1. Discover complete file state with full context
                coordinator = FileDiscoveryCoordinator(channel_name)
                discovery = await coordinator.discover_complete_file_state()

                # 2. Force sync if requested, otherwise use intelligent decision
                if force_reverse_sync:
                    _log_with_progress(
                        f"🔄 Force sync requested for '{channel_name}'", progress
                    )
                    discovery.needs_reverse_sync = True
                    discovery.reverse_sync_reason = "Force sync requested by user"

                # 3. Coordinate all sync operations in correct order
                if discovery.requires_action:
                    sync_stats = await coordinator.coordinate_sync_operations(
                        discovery, dry_run=False, progress=progress
                    )
                else:
                    _log_with_progress(
                        f"✅ No sync operations needed for '{channel_name}': {discovery.reverse_sync_reason}",
                        progress,
                    )
                    sync_stats = {"database_updated": 0}

                # 4. Generate and display comprehensive status report
                try:
                    messages_to_download = await get_messages_to_download(channel_name)

                    def count_by_ext(files, exts):
                        return len([f for f in files if f.get("extension") in exts])

                    def count_by_media_type(files, media_types):
                        return len(
                            [f for f in files if f.get("media_type") in media_types]
                        )

                    video_exts = [
                        ".mp4",
                        ".mkv",
                        ".avi",
                        ".mov",
                        ".webm",
                        ".flv",
                        ".m4v",
                        ".wmv",
                    ]
                    image_exts = [
                        ".jpg",
                        ".jpeg",
                        ".png",
                        ".gif",
                        ".bmp",
                        ".tiff",
                        ".webp",
                    ]
                    audio_exts = [".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg"]
                    text_exts = [".txt", ".pdf", ".doc", ".docx"]

                    # Count database files by media type
                    all_db_files = (
                        discovery.database_matched + discovery.database_unmatched
                    )
                    video_media_types = ["video", "Video"]
                    image_media_types = ["image", "Image", "photo"]
                    audio_media_types = ["audio", "Audio", "voice"]
                    text_media_types = ["document", "Document"]

                    stats = {
                        "channel_name": channel_name,
                        "unmatched_files": [
                            f.get("full_path", f.get("filename", ""))
                            for f in discovery.filesystem_unmatched
                        ],
                        "fs_total_files": len(discovery.files_on_disk),
                        "fs_video_files": count_by_ext(
                            discovery.files_on_disk, video_exts
                        ),
                        "fs_image_files": count_by_ext(
                            discovery.files_on_disk, image_exts
                        ),
                        "fs_audio_files": count_by_ext(
                            discovery.files_on_disk, audio_exts
                        ),
                        "fs_text_files": count_by_ext(
                            discovery.files_on_disk, text_exts
                        ),
                        "fs_other_files": len(discovery.files_on_disk)
                        - count_by_ext(
                            discovery.files_on_disk,
                            video_exts + image_exts + audio_exts + text_exts,
                        ),
                        "db_pending_files": len(messages_to_download),
                        "matches_found": len(discovery.database_matched),
                        "updated_to_completed": sync_stats.get("database_updated", 0),
                        "errors": 0,  # Could be enhanced if error tracking is added
                        "db_total_media_files": len(all_db_files),
                        "db_video_files": count_by_media_type(
                            all_db_files, video_media_types
                        ),
                        "db_image_files": count_by_media_type(
                            all_db_files, image_media_types
                        ),
                        "db_audio_files": count_by_media_type(
                            all_db_files, audio_media_types
                        ),
                        "db_text_files": count_by_media_type(
                            all_db_files, text_media_types
                        ),
                        "db_other_files": len(all_db_files)
                        - count_by_media_type(
                            all_db_files,
                            video_media_types
                            + image_media_types
                            + audio_media_types
                            + text_media_types,
                        ),
                        "new_messages": 0,  # This would need enumeration stats
                        "new_media_files": 0,  # This would need enumeration stats
                        "new_video_files": 0,  # Would need enhancement in enumeration to track by type
                        "new_image_files": 0,  # Would need enhancement in enumeration to track by type
                        "new_audio_files": 0,  # Would need enhancement in enumeration to track by type
                        "new_text_files": 0,  # Would need enhancement in enumeration to track by type
                        "new_other_files": 0,  # Would need enhancement in enumeration to track by type
                        "new_files_to_download": len(messages_to_download),
                    }
                    show_enhanced_enumeration_display(stats)
                except Exception as display_error:
                    _log_with_progress(
                        f"Status display failed: {display_error}",
                        progress,
                        level="warning",
                    )

            except Exception as e:
                if debug_trace:
                    print(
                        f"⚠️ TRACE: Exception in file discovery/sync for '{channel_name}': {e}"
                    )
                _log_with_progress(
                    f"File discovery and sync coordination failed for '{channel_name}': {e}",
                    progress,
                    level="warning",
                )
                # Don't let sync failures prevent the download session from continuing

        # === DATABASE SECTION: Previously Tracked Files ===
        if debug_trace:
            print(f"🗄️ TRACE: Entering database section for channel '{channel_name}'")
        _log_with_progress("  💾 Database Status", progress)
        from .storage import get_storage

        storage = get_storage(channel_name)

        try:
            # Get database connection to query media type statistics
            from .database.schema import get_connection

            async with get_connection(channel_name) as conn:
                channel_id = await storage.get_channel_id()

                # Get total tracked files
                cursor = await conn.execute(
                    """
                    SELECT COUNT(*) FROM messages
                    WHERE channel_id = ? AND media_type IS NOT NULL
                """,
                    (channel_id,),
                )
                row = await cursor.fetchone()
                total_tracked = row[0] if row else 0

                _log_with_progress(
                    f"        Media files tracked in database: {total_tracked}",
                    progress,
                )

            # Get comprehensive media type breakdown by status
            cursor = await conn.execute(
                """
                SELECT
                    media_type,
                    download_status,
                    COUNT(*) as count
                FROM messages
                WHERE channel_id = ? AND media_type IS NOT NULL
                GROUP BY media_type, download_status
                ORDER BY media_type, download_status
            """,
                (channel_id,),
            )

            all_files = await cursor.fetchall()

            # Categorize files into standard media types
            categories = {
                "Video": {"completed": 0, "failed": 0, "pending": 0},
                "Image": {"completed": 0, "failed": 0, "pending": 0},
                "Audio": {"completed": 0, "failed": 0, "pending": 0},
                "Txt/PDF": {"completed": 0, "failed": 0, "pending": 0},
                "Other": {"completed": 0, "failed": 0, "pending": 0},
            }

            for media_type, status, count in all_files:
                # Categorize media types
                media_lower = media_type.lower()
                if any(
                    vid_type in media_lower
                    for vid_type in ["video", "document", "mp4", "mov", "avi"]
                ):
                    category = "Video"
                elif any(
                    img_type in media_lower
                    for img_type in ["image", "photo", "jpg", "png", "gif"]
                ):
                    category = "Image"
                elif any(
                    aud_type in media_lower
                    for aud_type in ["audio", "mp3", "wav", "flac"]
                ):
                    category = "Audio"
                elif any(doc_type in media_lower for doc_type in ["pdf", "txt", "doc"]):
                    category = "Txt/PDF"
                else:
                    category = "Other"

                if status in categories[category]:
                    categories[category][status] += count

            # Display hierarchical breakdown by category (mirroring HDD section format)
            for category in ["Video", "Image", "Audio", "Txt/PDF", "Other"]:
                completed = categories[category]["completed"]
                failed = categories[category]["failed"]
                total_category = completed + failed

                if total_category > 0:
                    if completed > 0 and failed > 0:
                        _log_with_progress(
                            f"            {category}: {completed} (already downloaded), {failed} (failed)",
                            progress,
                        )
                    elif completed > 0:
                        _log_with_progress(
                            f"            {category}: {completed} (already downloaded)",
                            progress,
                        )
                    elif failed > 0:
                        _log_with_progress(
                            f"            {category}: {failed} (failed downloads)",
                            progress,
                        )
                else:
                    _log_with_progress(f"            {category}: 0", progress)

        except Exception as e:
            if debug_trace:
                print(
                    f"⚠️ TRACE: Exception in detailed media statistics for '{channel_name}': {e}"
                )
            logger.debug(f"Could not get detailed media statistics: {e}")
            # Fallback to basic display
            try:
                channel_stats = await storage.get_channel_statistics()
                old_media_count = channel_stats.get("downloaded", 0)
                _log_with_progress(
                    f"        Old media files tracked: {old_media_count}", progress
                )
                _log_with_progress(
                    f"        Completed media files skipped: {old_media_count}",
                    progress,
                )
            except Exception as e:
                if debug_trace:
                    print(
                        f"⚠️ TRACE: Exception in basic channel statistics for '{channel_name}': {e}"
                    )
                logger.debug(f"Could not get basic channel statistics: {e}")
                pass

        # === TELEGRAM SYNC COORDINATION ===
        if debug_trace:
            print(f"📡 TRACE: Starting Telegram sync coordination for '{channel_name}'")
        logger.debug("DEBUG: About to start enumeration phase")
        _log_with_progress("  ✨ Incremental Telegram sync starting", progress)

        # Import here to avoid circular dependency
        from .plugins.enumeration import enumerate_media_in_channel

        # Perform incremental enumeration to update database and get fresh stats
        if debug_trace:
            print(f"📄 TRACE: About to enumerate media for '{channel_name}'")
        enumerated_files = await enumerate_media_in_channel(
            client,
            chat_id,
            limit=None,
            channel_name=channel_name,
            incremental=True,
            progress=progress,
            termination_event=termination_event,
        )
        if debug_trace:
            print(
                f"📄 TRACE: Media enumeration completed for '{channel_name}' - found {len(enumerated_files) if enumerated_files else 0} files"
            )

        _log_with_progress("  ✨ Incremental Telegram sync completed", progress)

        # === TELEGRAM SECTION: Enumeration Results ===
        # Show detailed enumeration results
        if hasattr(enumerated_files, "_enumeration_stats"):
            stats = enumerated_files._enumeration_stats
            total_messages = stats.get("total_messages", 0)
            media_messages = stats.get("media_messages", 0)
            stats.get("new_count", 0)

            _log_with_progress(f"        New Messages: {total_messages}", progress)
            _log_with_progress(f"        New Media files: {media_messages}", progress)

            # Show media breakdown by category from new enumeration
            # TODO: Add category breakdown from enumeration results
            # For now show placeholder structure
            _log_with_progress("            Video: 0", progress)
            _log_with_progress("            Image: 0", progress)
            _log_with_progress("            Audio: 0", progress)
            _log_with_progress("            Txt/PDF: 0", progress)
            _log_with_progress("            Other: 0", progress)

        else:
            _log_with_progress("        No enumeration statistics available", progress)

        # === DELTA SECTION: New Files to Download ===
        if debug_trace:
            print(f"📋 TRACE: Entering download queue section for '{channel_name}'")
        _log_with_progress("  📋 Download Queue", progress)
        logger.debug(
            f"🔍 DEBUG: About to call get_messages_to_download for channel '{channel_name}' with limit={limit}"
        )
        if debug_trace:
            print(f"💬 TRACE: About to get messages to download for '{channel_name}'")
        messages_to_download = await get_messages_to_download(channel_name, limit=limit)
        if debug_trace:
            print(
                f"💬 TRACE: Got {len(messages_to_download) if messages_to_download else 0} messages to download for '{channel_name}'"
            )
        logger.debug(
            f"📊 DEBUG: get_messages_to_download returned {len(messages_to_download) if messages_to_download else 0} messages for channel '{channel_name}'"
        )

        # Display final download count with category breakdown
        download_count = len(messages_to_download)
        _log_with_progress(
            f"        New media files to download: {download_count}", progress
        )

    # Add hierarchical breakdown of new files by category
    if download_count > 0:
        new_categories = {"Video": 0, "Image": 0, "Audio": 0, "Txt/PDF": 0, "Other": 0}

        # Categorize new files to download
        for msg in messages_to_download:
            media_type = msg.get("media_type", "").lower()
            if any(
                vid_type in media_type
                for vid_type in ["video", "document", "mp4", "mov", "avi"]
            ):
                new_categories["Video"] += 1
            elif any(
                img_type in media_type
                for img_type in ["image", "photo", "jpg", "png", "gif"]
            ):
                new_categories["Image"] += 1
            elif any(
                aud_type in media_type for aud_type in ["audio", "mp3", "wav", "flac"]
            ):
                new_categories["Audio"] += 1
            elif any(doc_type in media_type for doc_type in ["pdf", "txt", "doc"]):
                new_categories["Txt/PDF"] += 1
            else:
                new_categories["Other"] += 1

        # Display breakdown with hierarchical indentation
        for category, count in new_categories.items():
            if count > 0:
                _log_with_progress(f"            {category}: {count} (new)", progress)
            else:
                _log_with_progress(f"            {category}: 0", progress)

    # Check if no new files were found during enumeration (but we may still have pending downloads)
    if not enumerated_files and download_count == 0:
        # Redundant message removed - already shown "New media files to download: 0" above
        if debug_trace:
            print(
                f"✅ TRACE: Taking early return path - no new files found for channel '{channel_name}'"
            )
        logger.debug(
            f"✅ DEBUG: Returning early - no new files found for channel '{channel_name}' (enumerated_files={len(enumerated_files) if enumerated_files else 0}, download_count={download_count})"
        )
        return entity, {}, {}, 0  # Return empty files_to_download

    # Convert database format to legacy format for compatibility with existing download code
    files_to_download = {}
    for msg in messages_to_download:
        msg_id_str = str(msg["id"])
        files_to_download[msg_id_str] = {
            "id": msg["id"],
            "media_type": msg["media_type"],
            "file_id": msg["file_id"],
            "file_size": msg.get("file_size"),
            "filename": msg.get("filename"),
        }

    # Load downloaded files for compatibility (though database is source of truth)
    # ASYNC REQUIREMENT: load_downloaded_files() is async and MUST be awaited
    # Fixed: Added await to prevent "RuntimeWarning: coroutine never awaited"
    downloaded_files = await load_downloaded_files(channel_name)

    total_files = len(files_to_download)
    # Debug: Log the function call and file count
    logger.debug(f"_prepare_download_session ending: {total_files} files to download")

    # Log the file count with channel name to identify source of duplicates
    if total_files > 0:
        _log_with_progress(f"  📊 {total_files} files to download", progress)
    else:
        _log_with_progress(
            f"  📊 {total_files} files to download (all files completed)", progress
        )

    if debug_trace:
        print(
            f"✅ TRACE: Normal successful return for channel '{channel_name}' - total_files={total_files}"
        )
    logger.debug(
        f"✅ DEBUG: Returning successful result for channel '{channel_name}' - entity={entity.title if hasattr(entity, 'title') else entity}, files_to_download={len(files_to_download)}, downloaded_files={len(downloaded_files)}, total_files={total_files}"
    )
    return entity, files_to_download, downloaded_files, total_files


async def _try_offline_download_session(
    channel_name: str, save_directory: str, progress=None
):
    """Attempt to create a download session using cached enumeration data.

    This function provides graceful degradation when Telegram connection fails
    but we have previously enumerated data that can be used for offline operations.

    Args:
        channel_name: Channel name
        save_directory: Directory to save downloads
        progress: Progress handler

    Returns:
        Tuple of (entity, files_to_download, downloaded_files, total_files) or None
    """
    try:
        from .storage import load_downloaded_files, load_enumerated_files

        # Try to load cached enumeration data
        enumerated_files = await load_enumerated_files(channel_name)

        if not enumerated_files:
            logger.debug(f"No cached enumeration data found for {channel_name}")
            return None

        # Load downloaded files for filtering
        # ASYNC REQUIREMENT: load_downloaded_files() returns a coroutine that must be awaited
        downloaded_files = await load_downloaded_files(channel_name)

        # Filter out already downloaded files using cached data
        files_to_download = {}
        for message_id_str, file_info in enumerated_files.items():
            file_id = file_info.get("file_id")

            # Skip files with no file_id or special media types
            if (
                file_id is None
                or file_info.get("media_type") == "MessageMediaPaidMedia"
            ):
                continue

            # Check if already downloaded
            already_downloaded = False
            for downloaded_info in downloaded_files.values():
                if downloaded_info.get("file_id") == file_id:
                    already_downloaded = True
                    break

            if not already_downloaded:
                files_to_download[message_id_str] = file_info

        # Create a mock entity for offline mode
        class OfflineEntity:
            def __init__(self, channel_name):
                self.id = f"offline_{channel_name}"
                self.title = f"Offline: {channel_name}"

        entity = OfflineEntity(channel_name)
        total_files = len(files_to_download)

        if total_files > 0:
            _log_with_progress(
                f"🔄 Offline mode: Found {total_files} files to download from cache",
                progress,
            )
            return entity, files_to_download, downloaded_files, total_files
        else:
            _log_with_progress(
                "✅ Offline mode: All cached files already downloaded", progress
            )
            return entity, {}, downloaded_files, 0

    except Exception as e:
        logger.error(f"Failed to prepare offline download session: {str(e)}")
        return None


async def _download_single_file(
    client,
    entity,
    message_id_str,
    file_info,
    save_directory,
    channel_name,
    downloaded_files,
    progress,
    semaphore,
):
    """Download a single file with semaphore control for concurrency."""
    async with semaphore:  # Limit concurrent downloads
        message_id = int(message_id_str)

        try:
            # Check for termination
            global termination_event
            if (termination_event and termination_event.is_set()) or (
                progress and progress.is_termination_requested()
            ):
                return (
                    False,
                    True,
                    0,
                    False,
                )  # success=False, skip=True, error=0, timeout=False

            message = await client.get_messages(entity, ids=message_id)
            # Handle case where message is None (deleted or unavailable)
            if message is None:
                logger.debug(f"Message {message_id} not found (deleted or unavailable)")
                return (
                    False,
                    True,
                    0,
                    False,
                )  # success=False, skip=True, error=0, timeout=False

            success, skip, timeout = await _process_media_message(
                client,
                message,
                save_directory,
                channel_name,
                downloaded_files,
                progress,
            )

            return success, skip, 0, timeout

        except Exception as e:
            # Use structured error handling
            # Suppress logs if using TQDM to prevent breaking progress display
            suppress_logs = (
                progress
                and hasattr(progress, "__class__")
                and "TQDM" in progress.__class__.__name__
            )
            (
                success,
                should_skip,
                error_count,
            ) = await TelegramErrorHandler.handle_telegram_error(
                e,
                message_id,
                attempt=1,
                termination_event=termination_event,
                suppress_logs=suppress_logs,
            )

            # If error handler suggests retry, try once more
            if not success and not should_skip and error_count == 0:
                try:
                    message = await client.get_messages(entity, ids=message_id)
                    # Handle case where message is None (deleted or unavailable)
                    if message is None:
                        logger.debug(
                            f"Message {message_id} not found on retry (deleted or unavailable)"
                        )
                        return (
                            False,
                            True,
                            0,
                            False,
                        )  # success=False, skip=True, error=0, timeout=False

                    success, skip, timeout = await _process_media_message(
                        client,
                        message,
                        save_directory,
                        channel_name,
                        downloaded_files,
                        progress,
                    )
                    return success, skip, 0, timeout
                except Exception as retry_e:
                    # Handle retry failure with structured error handling
                    # Suppress logs if using TQDM to prevent breaking progress display
                    suppress_logs = bool(
                        progress
                        and hasattr(progress, "__class__")
                        and "TQDM" in progress.__class__.__name__
                    )
                    retry_outcome = await TelegramErrorHandler.handle_telegram_error(
                        retry_e,
                        message_id,
                        attempt=2,
                        termination_event=termination_event,
                        suppress_logs=suppress_logs,
                    )
                    return (
                        retry_outcome.success,
                        retry_outcome.skip,
                        retry_outcome.error_count,
                        False,
                    )

            return success, should_skip, error_count, False


async def _download_files_batch(
    client,
    entity,
    files_to_download,
    save_directory,
    channel_name,
    downloaded_files,
    progress=None,
    concurrent_downloads=2,
    limit=None,
):
    """Download a batch of files with concurrent downloads and progress tracking."""
    global termination_event

    total_files = len(files_to_download)

    # Convert to list for processing
    files_list = list(files_to_download.items())

    # Remove redundant download start message - already shown in enumeration

    # Semaphore to limit concurrent downloads (configurable)
    semaphore = asyncio.Semaphore(concurrent_downloads)

    # Create download tasks (convert coroutines to actual Tasks)
    tasks = []
    for i, (message_id_str, file_info) in enumerate(files_list):
        if limit is not None and i >= limit:
            break
        coro = _download_single_file(
            client,
            entity,
            message_id_str,
            file_info,
            save_directory,
            channel_name,
            downloaded_files,
            progress,
            semaphore,
        )
        task = asyncio.create_task(coro)
        tasks.append(task)

    # Execute downloads concurrently with progress tracking
    downloaded_count = 0
    skipped_count = 0
    error_count = 0
    timeout_count = 0
    current_index = 0

    try:
        # Process tasks as they complete
        completed_tasks = set()
        # Process download tasks as they complete
        for task in asyncio.as_completed(tasks):
            try:
                success, skip, error, timeout = await task
                completed_tasks.add(task)
                current_index = len(completed_tasks)

                # Update counts
                if success:
                    downloaded_count += 1
                    if progress:
                        progress.update_stats(files_downloaded=downloaded_count)
                elif skip:
                    skipped_count += 1
                elif timeout:
                    timeout_count += 1
                else:
                    error_count += error
                    if progress and error > 0:
                        progress.update_stats(
                            errors=progress.stats.get("errors", 0) + error
                        )

                # Update progress
                if progress:
                    progress.update_main_task(
                        "download",
                        advance=1,
                        status=f"{current_index}/{total_files} files processed",
                    )

                # Check for termination after each task result
                if (termination_event and termination_event.is_set()) or (
                    progress
                    and hasattr(progress, "is_termination_requested")
                    and progress.is_termination_requested()
                ):
                    _log_with_progress("🛑 Graceful shutdown in progress...", progress)
                    # Cancel remaining tasks more aggressively
                    cancelled_count = 0
                    for remaining_task in tasks:
                        if (
                            remaining_task not in completed_tasks
                            and not remaining_task.done()
                        ):
                            remaining_task.cancel()
                            cancelled_count += 1

                    if cancelled_count > 0:
                        _log_with_progress(
                            f"Cancelled {cancelled_count} pending downloads", progress
                        )
                        # Wait briefly for cancelled tasks to finish, but don't hang
                        try:
                            await asyncio.wait_for(
                                asyncio.gather(
                                    *[t for t in tasks if t not in completed_tasks],
                                    return_exceptions=True,
                                ),
                                timeout=2.0,  # Max 2 seconds to wait for cleanup
                            )
                        except TimeoutError:
                            logger.debug(
                                "Some tasks didn't cancel cleanly, proceeding anyway"
                            )
                    break
            except asyncio.CancelledError:
                logger.info("Download task was cancelled")
                break
            except Exception as e:
                error_count += 1
                logger.error(f"Error in download task: {str(e)}")
                continue

    except KeyboardInterrupt:
        logger.info("\n\nKeyboardInterrupt received. Cancelling downloads...")
        if termination_event:
            termination_event.set()
        # Cancel all remaining tasks
        for task in tasks:
            if not task.done():
                task.cancel()
        # Wait for tasks to finish cancellation
        await asyncio.gather(*tasks, return_exceptions=True)

    return (
        downloaded_count,
        skipped_count,
        error_count,
        timeout_count,
        current_index,
        total_files,
    )


def _report_download_results(
    downloaded_count,
    skipped_count,
    error_count,
    timeout_count,
    current_index,
    total_files,
    progress=None,
    channel_name=None,
):
    """Report download results and statistics."""
    global termination_event

    # For individual channel completion, use more concise format
    if channel_name:
        total_processed = downloaded_count + skipped_count + error_count + timeout_count
        status_parts = []
        if downloaded_count > 0:
            status_parts.append(f"✅ {downloaded_count}")
        if skipped_count > 0:
            status_parts.append(f"⏭️ {skipped_count}")
        if error_count > 0:
            status_parts.append(f"❌ {error_count}")
        if timeout_count > 0:
            status_parts.append(f"⏱️ {timeout_count}")

        status_summary = (
            " | ".join(status_parts) if status_parts else "No files processed"
        )
        _log_with_progress(
            f"📊 {channel_name}: {status_summary} (Total: {total_processed})", progress
        )

        if termination_event and termination_event.is_set():
            remaining = total_files - total_processed
            if remaining > 0:
                _log_with_progress(
                    f"   ⏸️  {remaining} files remaining (can resume later)", progress
                )
    else:
        # For overall completion or legacy calls, use detailed format
        _log_with_progress("Download process completed or interrupted!", progress)
        _log_with_progress(
            f"Successfully downloaded: {downloaded_count} files", progress
        )
        _log_with_progress(f"Skipped: {skipped_count} files", progress)
        _log_with_progress(f"Errors: {error_count} files", progress)
        if timeout_count > 0:
            _log_with_progress(f"Timeouts: {timeout_count} files", progress)

        if termination_event and termination_event.is_set():
            remaining = total_files - (current_index + 1)
            _log_with_progress(f"Remaining files: {remaining}", progress)
            _log_with_progress(
                "You can restart the download later to process remaining files (completed files will be skipped).",
                progress,
            )


async def download_all_media_from_channel(
    client,
    chat_id,
    save_directory,
    limit=None,
    channel_name=None,
    progress=None,
    concurrent_downloads=2,
    incremental=False,
    media_type_filter="all",  # TODO: Implement media type filtering
    force_reverse_sync=False,
    skip_reverse_sync=False,
):
    """Download all media files from a channel using a temporary download approach."""
    logger.debug(
        f"download_all_media_from_channel called with channel_name='{channel_name}'"
    )
    global termination_event

    async with download_context(channel_name or "unknown", "download_all_media"):
        try:
            # Prepare download session
            prepare_result = await _prepare_download_session(
                client,
                chat_id,
                save_directory,
                channel_name,
                limit,
                incremental=incremental,
                progress=progress,
                force_reverse_sync=force_reverse_sync,
                skip_reverse_sync=skip_reverse_sync,
                debug_trace=False,  # Debug tracing disabled
            )

            # Check if prepare_result is None (connection error)
            if prepare_result is None:
                logger.error(
                    f"Failed to prepare download session for channel {channel_name}"
                )

                # Try graceful degradation - use cached enumeration data
                cached_result = await _try_offline_download_session(
                    channel_name, save_directory, progress
                )
                if cached_result:
                    logger.warning(
                        f"Using cached enumeration data for offline download of {channel_name}"
                    )
                    # Unpack cached result for offline processing
                    (
                        entity,
                        files_to_download,
                        downloaded_files,
                        total_files,
                    ) = cached_result
                else:
                    logger.error(
                        f"No cached data available for offline mode. Channel {channel_name} requires active connection."
                    )
                    return
            else:
                # Unpack the result
                (
                    entity,
                    files_to_download,
                    downloaded_files,
                    total_files,
                ) = prepare_result

            if total_files == 0:
                logger.info("No files to download.")
                return

            # Download files in batch
            # Start progress tracking
            if progress:
                await progress.start_progress(len(files_to_download))

            (
                downloaded_count,
                skipped_count,
                error_count,
                timeout_count,
                current_index,
                total_files,
            ) = await _download_files_batch(
                client,
                entity,
                files_to_download,
                save_directory,
                channel_name,
                downloaded_files,
                progress,
                concurrent_downloads,
                limit,
            )

            # Save progress if terminated
            if termination_event and termination_event.is_set():
                save_downloaded_files(channel_name, downloaded_files)
                logger.info("Progress saved due to termination.")

            # Report results for this channel
            _report_download_results(
                downloaded_count,
                skipped_count,
                error_count,
                timeout_count,
                current_index,
                total_files,
                progress,
                channel_name,
            )

        except (TimeoutError, ConnectionError) as e:
            logger.error(
                f"Network error downloading media from channel {chat_id}: {str(e)}"
            )
        except KeyboardInterrupt:
            logger.info("Download interrupted by user. Progress has been saved.")
        except Exception as e:
            logger.error(
                f"Unexpected error downloading media from channel {chat_id}: {str(e)}"
            )
            import traceback

            logger.error(traceback.format_exc())
