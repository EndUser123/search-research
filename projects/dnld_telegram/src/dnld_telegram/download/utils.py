import os
import shutil

from loguru import logger

from .storage import (
    get_temp_download_dir,
    load_downloaded_files,
    load_enumerated_files,
    save_downloaded_files,
)


def human_readable_size(size, decimal_places=2):
    """Convert bytes to human-readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.{decimal_places}f}{unit}"
        size /= 1024.0


def cleanup_temp_directory(channel_name):
    """Clean up the temporary download directory for a channel."""
    logger.debug(f"cleanup_temp_directory called with channel_name='{channel_name}'")
    temp_dir = get_temp_download_dir(channel_name)
    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up temporary directory: {temp_dir}")
        except (OSError, PermissionError) as e:
            logger.error(
                f"File system error cleaning up temporary directory {temp_dir}: {str(e)}"
            )
        except Exception as e:
            logger.error(
                f"Unexpected error cleaning up temporary directory {temp_dir}: {str(e)}"
            )
    # Recreate the directory
    os.makedirs(temp_dir, exist_ok=True)


async def scan_and_organize_existing_files(channel_name):
    """Scan for existing files in both the target subfolder and the main temp folder,
    move them to the correct subfolder, and add them to the tracking system.
    Also check against enumerated files to identify missing files."""
    logger.debug(
        f"scan_and_organize_existing_files called with channel_name='{channel_name}'"
    )
    downloaded_files = await load_downloaded_files(channel_name)
    enumerated_files = await load_enumerated_files(channel_name)
    target_directory = os.path.join(channel_name, "_media")
    main_temp_directory = "."  # Current working directory

    logger.info(
        f"Scanning for existing files in {target_directory} and {main_temp_directory}..."
    )
    logger.info(f"Checking against {len(enumerated_files)} enumerated files...")

    # Create target directory if it doesn't exist
    os.makedirs(target_directory, exist_ok=True)

    moved_count = 0
    tracked_count = 0
    missing_count = 0

    # Check for missing files (files that are enumerated but not downloaded)
    if enumerated_files:
        for msg_id_str, file_info in enumerated_files.items():
            # Check if this file is already in our downloaded files list
            already_downloaded = False
            file_id = file_info.get("file_id")
            if file_id:
                for downloaded_msg_id, downloaded_info in downloaded_files.items():
                    if downloaded_info.get("file_id") == file_id:
                        already_downloaded = True
                        break

            if not already_downloaded:
                missing_count += 1

    logger.info(
        f"Found {missing_count} missing files out of {len(enumerated_files)} enumerated files"
    )

    # Scan main temp folder for files belonging to this channel
    if os.path.exists(main_temp_directory):
        for filename in os.listdir(main_temp_directory):
            file_path = os.path.join(main_temp_directory, filename)
            if (
                os.path.isfile(file_path)
                and filename.startswith(channel_name)
                and os.path.dirname(file_path) == main_temp_directory
            ):
                # Check if this file is already in our downloaded files list
                already_tracked = False
                for msg_id, file_info in downloaded_files.items():
                    if file_info.get("file_path") == file_path or file_info.get(
                        "file_path"
                    ) == os.path.join(channel_name, "_media", filename):
                        already_tracked = True
                        break

                if not already_tracked:
                    # Move file to target directory
                    new_file_path = os.path.join(target_directory, filename)
                    try:
                        shutil.move(file_path, new_file_path)
                        moved_count += 1

                        # Add to downloaded files list with placeholder info
                        placeholder_msg_id = f"moved_{len(downloaded_files) + 1}"
                        logger.debug(
                            f"scan_and_organize_existing_files - adding file_path='{new_file_path}'"
                        )
                        downloaded_files[placeholder_msg_id] = {
                            "chat_id": 0,
                            "message_id": -1,
                            "file_path": os.path.join(channel_name, "_media", filename),
                            "file_id": f"unknown_{filename}",
                            "timestamp": None,
                            "moved_file": True,
                        }
                        tracked_count += 1
                    except (OSError, PermissionError) as e:
                        logger.error(
                            f"File system error moving file {file_path}: {str(e)}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Unexpected error moving file {file_path}: {str(e)}"
                        )

    # Scan target subfolder for untracked files
    if os.path.exists(target_directory):
        for filename in os.listdir(target_directory):
            file_path = os.path.join(target_directory, filename)
            if os.path.isfile(file_path):
                # Check if this file is already in our downloaded files list
                already_tracked = False
                for msg_id, file_info in downloaded_files.items():
                    if file_info.get("file_path") == file_path:
                        already_tracked = True
                        break

                if not already_tracked:
                    # Add to downloaded files list with placeholder info
                    placeholder_msg_id = f"moved_{len(downloaded_files) + 1}"
                    logger.debug(
                        f"scan_and_organize_existing_files - adding file_path='{file_path}'"
                    )
                    downloaded_files[placeholder_msg_id] = {
                        "chat_id": 0,
                        "message_id": -1,
                        "file_path": os.path.join(channel_name, "_media", filename),
                        "file_id": f"unknown_{filename}",
                        "timestamp": None,
                        "moved_file": True,
                    }
                    tracked_count += 1

    # Save updated downloaded files list
    if moved_count > 0 or tracked_count > 0:
        import asyncio

        asyncio.run(save_downloaded_files(channel_name, downloaded_files))
        logger.info(
            f"Moved {moved_count} files and added {tracked_count} files to tracking."
        )
    else:
        logger.info("No untracked files found.")

    logger.info("Finished scanning and organizing existing files.")
    return moved_count, tracked_count


async def scan_existing_files(channel_name):
    """Scan for existing files in both the target subfolder and the main temp folder."""
    logger.debug(f"scan_existing_files called with channel_name='{channel_name}'")
    downloaded_files = await load_downloaded_files(channel_name)
    target_directory = os.path.join(channel_name, "_media")
    main_temp_directory = "."  # Current working directory

    logger.info(
        f"Scanning for existing files in {target_directory} and {main_temp_directory}..."
    )

    # Scan target subfolder
    if os.path.exists(target_directory):
        for filename in os.listdir(target_directory):
            file_path = os.path.join(target_directory, filename)
            if os.path.isfile(file_path):
                # Check if this file is already in our downloaded files list
                already_tracked = False
                for msg_id, file_info in downloaded_files.items():
                    if file_info.get("file_path") == file_path:
                        already_tracked = True
                        break

                if not already_tracked:
                    logger.info(f"Found untracked file: {file_path}")

    # Scan main temp folder
    if os.path.exists(main_temp_directory):
        for filename in os.listdir(main_temp_directory):
            file_path = os.path.join(main_temp_directory, filename)
            if (
                os.path.isfile(file_path)
                and filename.startswith(channel_name)
                and os.path.dirname(file_path) == main_temp_directory
            ):
                # Check if this file is already in our downloaded files list
                already_tracked = False
                for msg_id, file_info in downloaded_files.items():
                    if file_info.get("file_path") == file_path:
                        already_tracked = True
                        break

                if not already_tracked:
                    logger.info(f"Found untracked file: {file_path}")

    logger.info("Finished scanning for existing files.")
