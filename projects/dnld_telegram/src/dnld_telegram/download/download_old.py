import asyncio
import os
import shutil
import time
import uuid
from enum import Enum
from typing import Any

from loguru import logger
from telethon import TelegramClient  # type: ignore
from telethon.tl.types import Message  # type: ignore

from .channel_fixer import ChannelFixer
from .config.logging_config import log_performance
from .storage import (
    get_file_id,
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
MIN_TIMEOUT_SECONDS = 600  # Minimum download timeout (10 minutes)
MAX_TIMEOUT_SECONDS = 7200  # Maximum download timeout (2 hours)
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

    if save_directory is None:
        logger.error("save_directory is None - cannot download media")
        return DownloadResult.ERROR

    if channel_name is None:
        logger.error("channel_name is None - cannot download media")
        return DownloadResult.ERROR

    message_id = message.id

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
        # Check if we already have a task with this filename (for retries)
        existing_tasks = getattr(progress, "download_tqdms", {})
        if hasattr(progress, "download_tqdms") and final_filename in existing_tasks:
            # Reuse existing task for retries
            download_task_id = final_filename
        else:
            # Create new task only if it doesn't exist
            download_task_id = progress.add_download_task(final_filename, total_bytes)
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
        # For large files, allow more time: assume minimum 50KB/s instead of 100KB/s
        # and increase maximum to 2 hours for very large files
        timeout_seconds = float(
            max(
                MIN_TIMEOUT_SECONDS,
                min(
                    MAX_TIMEOUT_SECONDS,
                    int(total_bytes) // ASSUMED_MIN_SPEED_BPS
                    if total_bytes
                    else MIN_TIMEOUT_SECONDS,
                ),
            )
        )  # 10min minimum, 2 hours maximum, assuming 50KB/s minimum speed

        try:
            logger.debug(f"Attempting to download media for message {message.id}")
            logger.debug(f"File size: {total_bytes} bytes, timeout: {timeout_seconds}s")
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
                    progress_callback=enhanced_progress_callback if progress else None,  # type: ignore[arg-type]
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
                logger.debug(f"Cleaned up partial download for message {message_id}")
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


def download_media_from_message(
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
            logger.warning(f"No media found in message {message.id}")
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
        downloaded_files = load_downloaded_files(channel_name)

        # Check if file with same ID already downloaded
        already_downloaded = False
        for _, downloaded_info in downloaded_files.items():
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
    media_dir = os.path.join("channels", channel_name, "_media")
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
        for _, downloaded_info in downloaded_files.items():
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


def _process_media_message(
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
):
    """Prepare for download session by loading and filtering files."""
    # Remove duplicate logging - already shown in main module

    # Create save directory if it doesn't exist
    os.makedirs(save_directory, exist_ok=True)

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
                    return None, {}, {}, 0
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
                return (
                    None,
                    {},
                    {},
                    0,
                )  # Return proper 4-tuple with None entity and empty files
        else:
            # Re-raise other types of errors
            raise

    # Beautiful Unified File Discovery & Sync Coordination
    # This replaces fragmented sync logic with intelligent coordination
    if skip_reverse_sync:
        logger.info(f"⏭️ File sync disabled by user for '{channel_name}'")
        # Still do basic discovery for progress tracking
        try:
            from .file_discovery_coordinator import FileDiscoveryCoordinator

            coordinator = FileDiscoveryCoordinator(channel_name)
            discovery = coordinator.discover_complete_file_state()
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
            discovery = coordinator.discover_complete_file_state()

            # 2. Force sync if requested, otherwise use intelligent decision
            if force_reverse_sync:
                _log_with_progress(
                    f"🔄 Force sync requested for '{channel_name}'", progress
                )
                discovery.needs_reverse_sync = True
                discovery.reverse_sync_reason = "Force sync requested by user"

            # 3. Coordinate all sync operations in correct order
            if discovery.requires_action:
                sync_stats = coordinator.coordinate_sync_operations(
                    discovery, dry_run=False, progress=progress
                )
                _log_with_progress(
                    f"✨ Sync coordination complete: {sync_stats['total_files_ready']} files ready",
                    progress,
                )
            else:
                _log_with_progress(
                    f"✅ No sync operations needed for '{channel_name}': {discovery.reverse_sync_reason}",
                    progress,
                )

        except Exception as e:
            _log_with_progress(
                f"File discovery and sync coordination failed for '{channel_name}': {e}",
                progress,
                level="warning",
            )
            # Don't let sync failures prevent the download session from continuing

    logger.debug("DEBUG: About to start enumeration phase")
    # Always run incremental enumeration to ensure we have the latest files in database
    _log_with_progress(
        f"📤 Checking for new messages from Telegram for channel '{channel_name}'...",
        progress,
    )
    # Import here to avoid circular dependency
    from .plugins.enumeration import enumerate_media_in_channel

    # Perform incremental enumeration to update database
    _log_with_progress("Starting enumeration...", progress)
    enumerated_files = await enumerate_media_in_channel(
        client,
        chat_id,
        limit=None,
        channel_name=channel_name,
        incremental=True,
        progress=progress,
        termination_event=termination_event,
    )
    _log_with_progress("Enumeration finished.", progress)

    if not enumerated_files:
        _log_with_progress(
            f"No media files found in channel '{channel_name}' after enumeration.",
            progress,
        )
        return entity, {}, {}, 0  # Return empty files_to_download

    _log_with_progress(
        f"Enumeration complete. Found {len(enumerated_files)} media files.", progress
    )

    # Database sync already handled by FileDiscoveryCoordinator above
    # This ensures all filesystem files are properly synced with database state
    # before we start the download process

    # Use database to get only files that need downloading (status = pending/failed)
    # Note: get_messages_to_download() now automatically filters out unddownloadable media types
    _log_with_progress(
        f"📋 Preparing download queue for channel '{channel_name}'...", progress
    )
    from .storage import get_messages_to_download

    messages_to_download = get_messages_to_download(channel_name, limit=limit)

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
    downloaded_files = load_downloaded_files(channel_name)

    total_files = len(files_to_download)
    # Debug: Log the function call and file count
    logger.debug(f"_prepare_download_session ending: {total_files} files to download")

    # Log the file count with channel name to identify source of duplicates
    if total_files > 0:
        _log_with_progress(
            f"📊 {channel_name}: {total_files} files to download", progress
        )
    else:
        _log_with_progress(
            f"📊 {channel_name}: {total_files} files to download (no files)", progress
        )

    return entity, files_to_download, downloaded_files, total_files


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


def download_all_media_from_channel(
    client,
    chat_id,
    save_directory,
    limit=None,
    channel_name=None,
    progress=None,
    concurrent_downloads=2,
    incremental=False,
    media_type_filter="all",
    force_reverse_sync=False,
    skip_reverse_sync=False,
):
    """Download all media files from a channel using a temporary download approach."""
    logger.debug(
        f"download_all_media_from_channel called with channel_name='{channel_name}'"
    )
    global termination_event

    try:
        # Prepare download session
        (
            entity,
            files_to_download,
            downloaded_files,
            total_files,
        ) = await _prepare_download_session(
            client,
            chat_id,
            save_directory,
            channel_name,
            limit,
            incremental=incremental,
            progress=progress,
            force_reverse_sync=force_reverse_sync,
            skip_reverse_sync=skip_reverse_sync,
        )

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
