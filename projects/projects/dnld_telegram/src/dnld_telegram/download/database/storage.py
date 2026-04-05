"""
Database storage layer for dnld_telegram

This module provides database-backed replacements for the JSON storage functions,
with enhanced functionality for message threads and improved performance.
"""

import sqlite3
from datetime import datetime
from typing import Any

import aiosqlite
from loguru import logger

from ...exceptions import ConfigurationError, ValidationError
from ..config.logging_config import log_performance
from .schema import ensure_channel_exists, get_connection
from .sharding import get_shard_manager


class DatabaseStorage:
    """Database storage manager for channel data."""

    def __init__(self, channel_name: str, telegram_id: int | None = None):
        self.channel_name = channel_name
        self.telegram_id = telegram_id
        self._channel_id: int | None = None
        self._shard_manager = get_shard_manager(channel_name)

    async def get_channel_id(self, telegram_id: int | None = None) -> int:
        """Get or create channel ID in database."""
        if self._channel_id is None:
            # Use self.telegram_id if telegram_id parameter is None
            effective_telegram_id = telegram_id or self.telegram_id
            if effective_telegram_id is None:
                # Try to get existing channel by name
                async with get_connection(self.channel_name) as conn:
                    cursor = await conn.execute(
                        "SELECT id FROM channels WHERE name = ?", (self.channel_name,)
                    )
                    row = await cursor.fetchone()
                    if row:
                        self._channel_id = row["id"]
                    else:
                        raise ConfigurationError(
                            f"Channel '{self.channel_name}' not found and no telegram_id provided",
                            config_key="telegram_id",
                        )
            else:
                self._channel_id = await ensure_channel_exists(
                    self.channel_name, effective_telegram_id
                )
                if self._channel_id is None or self._channel_id <= 0:
                    raise RuntimeError(
                        f"ensure_channel_exists returned invalid ID: {self._channel_id}"
                    )
        return self._channel_id

    async def _ensure_channel_exists_in_conn(
        self, conn: aiosqlite.Connection, telegram_id: int
    ) -> int:
        """
        Ensure channel exists within a specific database connection.

        Args:
            conn: Database connection to use
            telegram_id: Telegram channel ID

        Returns:
            Channel ID in the database
        """
        logger.debug(
            f"_ensure_channel_exists_in_conn called: channel_name='{self.channel_name}', telegram_id={telegram_id}"
        )

        # Try to get existing channel by telegram_id first (most reliable)
        cursor = await conn.execute(
            "SELECT id FROM channels WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()

        if row:
            logger.info(
                f"✅ Channel found by telegram_id {telegram_id} with id={row['id']}"
            )
            return row["id"]
        else:
            logger.info(f"❌ Channel NOT found by telegram_id {telegram_id}")

        # Try to get by name if not found by telegram_id
        cursor = await conn.execute(
            "SELECT id FROM channels WHERE name = ?", (self.channel_name,)
        )
        row = await cursor.fetchone()

        if row:
            logger.info(
                f"✅ Channel found by name '{self.channel_name}' with id={row['id']}"
            )
            # Channel exists but has different telegram_id - update it
            current_telegram_id = (
                await (
                    await conn.execute(
                        "SELECT telegram_id FROM channels WHERE id = ?", (row["id"],)
                    )
                ).fetchone()
            )[0]

            if current_telegram_id != telegram_id:
                # Check if this is a normal Telegram ID truncation case
                # Full chat_id format: -100XXXXXXXXX, Entity ID format: XXXXXXXXX
                if str(current_telegram_id).startswith("-100") and abs(
                    current_telegram_id
                ) == int(f"100{telegram_id}"):
                    logger.info(
                        f"Channel {row['id']} telegram_id format difference is normal: DB has full chat_id {current_telegram_id}, entity has truncated id {telegram_id}. No update needed."
                    )
                else:
                    logger.info(
                        f"Channel {row['id']} telegram_id mismatch: DB has {current_telegram_id}, updating to {telegram_id}"
                    )
                    update_cursor = await conn.execute(
                        "UPDATE channels SET telegram_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (telegram_id, row["id"]),
                    )
                    logger.info(f"Update affected {update_cursor.rowcount} rows")

                # Verify the update within the transaction
                verify_cursor = await conn.execute(
                    "SELECT telegram_id FROM channels WHERE id = ?", (row["id"],)
                )
                new_telegram_id = (await verify_cursor.fetchone())[0]
                logger.info(f"After update: telegram_id = {new_telegram_id}")
            else:
                logger.debug(
                    f"Channel found by name with id={row['id']}, telegram_id matches"
                )
            return row["id"]

        # Channel doesn't exist - create it
        logger.debug(
            f"Creating new channel: name='{self.channel_name}', telegram_id={telegram_id}"
        )
        try:
            cursor = await conn.execute(
                "INSERT INTO channels (name, telegram_id) VALUES (?, ?)",
                (self.channel_name, telegram_id),
            )
            new_id = cursor.lastrowid
            if new_id is None:
                raise RuntimeError(
                    f"Failed to create channel '{self.channel_name}' - INSERT returned no ID"
                )
            logger.debug(f"Channel created successfully with id={new_id}")
            return new_id
        except aiosqlite.IntegrityError as e:
            # Handle race condition where another process created the channel
            if "UNIQUE constraint failed" in str(e):
                logger.debug(
                    "Channel creation failed due to UNIQUE constraint - another process created it"
                )
                # Try to get the channel that was created by the other process
                cursor = await conn.execute(
                    "SELECT id FROM channels WHERE telegram_id = ?", (telegram_id,)
                )
                row = await cursor.fetchone()
                if row:
                    logger.debug(
                        f"Found channel created by other process with id={row['id']}"
                    )
                    return row["id"]
                # Also try by name
                cursor = await conn.execute(
                    "SELECT id FROM channels WHERE name = ?", (self.channel_name,)
                )
                row = await cursor.fetchone()
                if row:
                    logger.debug(
                        f"Found channel created by other process by name with id={row['id']}"
                    )
                    return row["id"]
            logger.error(f"Failed to create or find channel after IntegrityError: {e}")
            raise

    async def _cleanup_orphaned_download_history(
        self, conn: aiosqlite.Connection
    ) -> None:
        """
        Clean up orphaned download_history entries that reference non-existent messages.
        This prevents FOREIGN KEY constraint failures during new message insertions.
        """
        try:
            # Count orphaned entries before cleanup
            cursor = await conn.execute(
                """
                SELECT COUNT(*) as count
                FROM download_history dh
                LEFT JOIN messages m ON dh.message_id = m.id
                WHERE m.id IS NULL
            """
            )
            orphaned_count = (await cursor.fetchone())["count"]

            if orphaned_count > 0:
                logger.info(
                    f"Found {orphaned_count} orphaned download_history entries, cleaning up..."
                )

                # Delete orphaned entries
                await conn.execute(
                    """
                    DELETE FROM download_history
                    WHERE message_id NOT IN (SELECT id FROM messages)
                """
                )
                await conn.commit()
                logger.info(
                    f"Cleaned up {orphaned_count} orphaned download_history entries"
                )
            else:
                logger.debug("No orphaned download_history entries found")

        except Exception as e:
            logger.warning(f"Failed to cleanup orphaned download_history entries: {e}")
            # Don't raise - this is a cleanup operation that shouldn't block the main functionality

    # === Message Management ===

    @log_performance("db_save_enumerated_messages")
    async def save_enumerated_messages(
        self, messages: dict[str, dict[str, Any]], telegram_channel_id: int
    ) -> None:
        """
        Save enumerated messages to database with proper concurrency handling.

        Args:
            messages: Dictionary of message_id -> message_info
            telegram_channel_id: Telegram channel ID
        """
        if not messages:
            logger.debug("No messages to save")
            return

        logger.debug(
            f"save_enumerated_messages called: channel={self.channel_name}, messages={len(messages)}, telegram_id={telegram_channel_id}"
        )

        # Implement batch processing for large channels - adjust batch size based on channel size
        # For very large databases (50GB+), use smaller batches to prevent timeouts
        total_message_count = len(messages)
        if total_message_count > 10000:  # Very large channel
            BATCH_SIZE = 100  # Smaller batches for large channels
        elif total_message_count > 1000:  # Medium channel
            BATCH_SIZE = 250  # Standard batch size
        else:
            BATCH_SIZE = 500  # Larger batches for small channels

        if len(messages) > BATCH_SIZE:
            logger.info(
                f"Using batch processing: {len(messages)} messages > {BATCH_SIZE} (large channel optimization)"
            )
            await self._save_messages_in_batches(
                messages, telegram_channel_id, BATCH_SIZE
            )
            return
        else:
            logger.info(
                f"Using direct processing: {len(messages)} messages <= {BATCH_SIZE}"
            )

        conn = None
        try:
            async with get_connection(self.channel_name) as conn:
                # Use single transaction for channel creation and message saving (same pattern as _save_single_batch)
                await conn.execute("PRAGMA defer_foreign_keys = ON")
                await conn.execute("BEGIN IMMEDIATE")  # Acquire write lock immediately
                try:
                    # Ensure channel exists within this transaction
                    channel_id = await self._ensure_channel_exists_in_conn(
                        conn, telegram_channel_id
                    )
                    logger.debug(f"Channel {channel_id} verified in single transaction")

                    # Run cleanup with timeout for small to medium channels
                    # Skip for very large channels to prevent excessive wait times
                    if len(messages) <= 5000:
                        logger.debug(
                            f"Running orphaned entry cleanup for {self.channel_name}"
                        )
                        await self._cleanup_orphaned_download_history(conn)
                    else:
                        logger.debug(
                            f"Skipping orphaned entry cleanup for large channel {self.channel_name} ({len(messages)} messages)"
                        )

                    # Validate channel_id is valid
                    if channel_id is None or channel_id <= 0:
                        raise ValidationError(
                            f"Invalid channel_id: {channel_id}",
                            field_name="channel_id",
                            invalid_value=channel_id,
                        )

                    logger.debug(
                        f"Processing {len(messages)} messages for {self.channel_name}"
                    )
                    logger.debug(
                        f"Using channel_id={channel_id} for telegram_channel_id={telegram_channel_id}"
                    )

                    # Process messages within the same transaction
                    verify_cursor = await conn.execute(
                        "SELECT id FROM channels WHERE id = ?", (channel_id,)
                    )
                    verify_row = await verify_cursor.fetchone()
                    if not verify_row:
                        logger.error(
                            f"Channel {channel_id} is not visible in the new transaction"
                        )
                        raise RuntimeError(
                            f"Channel {channel_id} not found in new transaction"
                        )

                    # Process all messages in this transaction
                    logger.debug(
                        f"Processing {len(messages)} messages for database insertion"
                    )
                    for msg_id_str, msg_info in messages.items():
                        try:
                            telegram_id = int(msg_id_str)
                        except (ValueError, TypeError) as e:
                            # Use domain-specific exception for message ID parsing errors
                            logger.warning(
                                f"Invalid message ID: {msg_id_str}, skipping... Error: {e}"
                            )
                            continue

                        # Parse date
                        date_str = msg_info.get("date")
                        if date_str:
                            try:
                                # Handle different date formats
                                if "T" in date_str or "+00:00" in date_str:
                                    # Handle ISO format or datetime with timezone
                                    if date_str.endswith("+00:00"):
                                        date_str = date_str[:-6]  # Remove timezone
                                    elif date_str.endswith("Z"):
                                        date_str = date_str[:-1]  # Remove Z
                                    # Parse ISO format without timezone or space-separated with timezone removed
                                    if "T" in date_str:
                                        date_obj = datetime.fromisoformat(date_str)
                                    else:
                                        # Handle space-separated format: "2025-01-17 00:57:56"
                                        date_obj = datetime.strptime(
                                            date_str, "%Y-%m-%d %H:%M:%S"
                                        )
                                else:
                                    # Try standard format
                                    date_obj = datetime.strptime(
                                        date_str, "%Y-%m-%d %H:%M:%S"
                                    )
                            except (ValueError, TypeError) as e:
                                # Use current time for unparseable dates
                                logger.debug(f"Date parsing failed for {date_str}: {e}")
                                date_obj = datetime.now()
                        else:
                            date_obj = datetime.now()

                        # Insert or update message
                        values = (
                            telegram_id,
                            channel_id,
                            date_obj,
                            msg_info.get("media_type"),
                            msg_info.get("file_id"),
                            msg_info.get("file_size"),
                        )
                        logger.debug(
                            f"Inserting message: telegram_id={telegram_id}, channel_id={channel_id}, values={values}"
                        )

                        try:
                            # First try to update existing message preserving filename data
                            # This ensures reverse sync data is not lost during enumeration
                            update_cursor = await conn.execute(
                                """
                                UPDATE messages
                                SET date = ?, media_type = ?, file_id = ?, file_size = ?, updated_at = CURRENT_TIMESTAMP
                                WHERE telegram_id = ? AND channel_id = ?
                            """,
                                (
                                    date_obj,
                                    msg_info.get("media_type"),
                                    msg_info.get("file_id"),
                                    msg_info.get("file_size"),
                                    telegram_id,
                                    channel_id,
                                ),
                            )

                            if update_cursor.rowcount == 0:
                                # No existing record to update, insert new one
                                await conn.execute(
                                    """
                                    INSERT INTO messages
                                    (telegram_id, channel_id, date, media_type, file_id, file_size)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """,
                                    values,
                                )
                                logger.debug(f"Inserted new message {telegram_id}")
                            else:
                                logger.debug(
                                    f"Updated existing message {telegram_id} (preserving filename)"
                                )
                        except aiosqlite.IntegrityError as ie:
                            if "FOREIGN KEY constraint failed" in str(ie):
                                logger.error(
                                    f"Failed to insert message {telegram_id}: FOREIGN KEY constraint failed - channel_id {channel_id} doesn't exist"
                                )
                                # Check if channel still exists
                                check_cursor = await conn.execute(
                                    "SELECT id FROM channels WHERE id = ?",
                                    (channel_id,),
                                )
                                check_row = await check_cursor.fetchone()
                                if not check_row:
                                    logger.error(
                                        f"Channel {channel_id} is missing from database!"
                                    )
                                else:
                                    logger.error(
                                        f"Channel {channel_id} exists but FK constraint still failed - this suggests a transaction issue"
                                    )
                            else:
                                logger.error(
                                    f"Failed to insert message {telegram_id}: {ie}"
                                )
                            continue

                    # Check for foreign key violations before committing
                    fk_check_cursor = await conn.execute("PRAGMA foreign_key_check")
                    fk_violations = await fk_check_cursor.fetchall()
                    if fk_violations:
                        logger.error("Foreign key violations detected before commit:")
                        for violation in fk_violations:
                            logger.error(
                                f"  Table: {violation[0]}, Row: {violation[1]}, Parent: {violation[2]}, FK Index: {violation[3]}"
                            )
                        raise RuntimeError(
                            f"Foreign key constraint violations: {len(fk_violations)} violations found"
                        )

                    await conn.commit()
                    logger.debug(
                        f"Saved {len(messages)} enumerated messages for channel '{self.channel_name}'"
                    )
                    logger.info(
                        f"✅ Database save completed for {self.channel_name} ({len(messages)} messages)"
                    )

                except Exception as e:
                    await conn.rollback()
                    logger.error(
                        f"Database transaction failed for channel '{self.channel_name}': {e}"
                    )

                    # If it's a foreign key error, run diagnostic check
                    if "FOREIGN KEY constraint failed" in str(e):
                        try:
                            fk_check_cursor = await conn.execute(
                                "PRAGMA foreign_key_check"
                            )
                            fk_violations = await fk_check_cursor.fetchall()
                            if fk_violations:
                                logger.error("Foreign key violations found:")
                                for violation in fk_violations:
                                    logger.error(
                                        f"  Table: {violation[0]}, Row: {violation[1]}, Parent: {violation[2]}, FK Index: {violation[3]}"
                                    )
                        except Exception as check_error:
                            logger.error(
                                f"Failed to run foreign key check: {check_error}"
                            )
                    raise
                finally:
                    # Reset defer_foreign_keys pragma
                    await conn.execute("PRAGMA defer_foreign_keys = OFF")
        finally:
            # Ensure connection is always closed
            if conn:
                try:
                    await conn.close()
                    logger.debug(f"Database connection closed for {self.channel_name}")
                except Exception as e:
                    logger.warning(
                        f"Error closing database connection for {self.channel_name}: {e}"
                    )

    async def _save_messages_in_batches(
        self,
        messages: dict[str, dict[str, Any]],
        telegram_channel_id: int,
        batch_size: int,
    ) -> None:
        """Save large message sets in smaller batches to prevent database timeouts."""
        import math

        message_items = list(messages.items())
        total_batches = math.ceil(len(message_items) / batch_size)

        logger.info(
            f"Processing {len(message_items)} messages in {total_batches} batches for {self.channel_name}"
        )

        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(message_items))
            batch_messages = dict(message_items[start_idx:end_idx])

            logger.debug(
                f"Processing batch {batch_num + 1}/{total_batches} ({len(batch_messages)} messages)"
            )

            # Process this batch with the normal save logic
            await self._save_single_batch(batch_messages, telegram_channel_id)

        logger.info(
            f"✅ Completed batch processing for {self.channel_name}: {total_batches} batches, {len(message_items)} messages"
        )

    async def _save_single_batch(
        self, messages: dict[str, dict[str, Any]], telegram_channel_id: int
    ) -> None:
        """Save a single batch of messages (used by batch processing)."""
        logger.debug(
            f"_save_single_batch called: channel={self.channel_name}, messages={len(messages)}, telegram_channel_id={telegram_channel_id}"
        )

        async with get_connection(self.channel_name) as conn:
            # Use single transaction for channel creation and message saving
            # Temporarily disable FK constraints during batch insert, then manually verify
            original_fk_state = (
                await (await conn.execute("PRAGMA foreign_keys")).fetchone()
            )[0]
            logger.debug(f"Original FK state: {original_fk_state}")

            await conn.execute("PRAGMA foreign_keys = OFF")
            await conn.execute("BEGIN IMMEDIATE")
            try:
                # Ensure channel exists within this transaction
                logger.debug(
                    f"Before channel check: telegram_channel_id={telegram_channel_id}"
                )
                channel_id = await self._ensure_channel_exists_in_conn(
                    conn, telegram_channel_id
                )
                logger.debug(f"After channel check: channel_id={channel_id}")
                logger.debug(
                    f"Channel {channel_id} verified for batch in single transaction"
                )

                # Verify channel creation was successful
                verify_cursor = await conn.execute(
                    "SELECT id, name, telegram_id FROM channels WHERE id = ?",
                    (channel_id,),
                )
                verify_row = await verify_cursor.fetchone()
                if not verify_row:
                    raise RuntimeError(
                        f"Channel {channel_id} not found after creation!"
                    )
                logger.debug(
                    f"Channel verification: id={verify_row['id']}, name='{verify_row['name']}', telegram_id={verify_row['telegram_id']}"
                )

                # Validate channel_id
                if channel_id is None or channel_id <= 0:
                    raise ValidationError(
                        f"Invalid channel_id: {channel_id}",
                        field_name="channel_id",
                        invalid_value=channel_id,
                    )

                logger.debug(f"Processing batch of {len(messages)} messages")
                logger.debug(
                    f"Starting message processing: channel_id={channel_id}, batch_size={len(messages)}"
                )

                # Process messages in this batch
                processed_count = 0
                for msg_id_str, msg_info in messages.items():
                    try:
                        telegram_id = int(msg_id_str)
                    except (ValueError, TypeError) as e:
                        # Log parsing error but continue processing
                        logger.warning(
                            f"Invalid message ID: {msg_id_str}, skipping... Error: {e}"
                        )
                        continue

                    processed_count += 1
                    if processed_count <= 3:
                        logger.debug(
                            f"Message {processed_count}: telegram_id={telegram_id}, channel_id={channel_id}"
                        )

                    # Parse date - use current time as fallback for invalid dates
                    date_str = msg_info.get("date")
                    if date_str:
                        try:
                            # Handle different date formats
                            if "T" in date_str or "+00:00" in date_str:
                                # Handle ISO format or datetime with timezone
                                if date_str.endswith("+00:00"):
                                    date_str = date_str[:-6]  # Remove timezone
                                elif date_str.endswith("Z"):
                                    date_str = date_str[:-1]  # Remove Z
                                # Parse ISO format without timezone or space-separated with timezone removed
                                if "T" in date_str:
                                    date_obj = datetime.fromisoformat(date_str)
                                else:
                                    # Handle space-separated format: "2025-01-17 00:57:56"
                                    date_obj = datetime.strptime(
                                        date_str, "%Y-%m-%d %H:%M:%S"
                                    )
                            else:
                                # Try standard format
                                date_obj = datetime.strptime(
                                    date_str, "%Y-%m-%d %H:%M:%S"
                                )
                        except (ValueError, TypeError) as e:
                            # Date parsing failed, use current time
                            logger.debug(
                                f"Date parsing failed for message {telegram_id}: {date_str}, using current time. Error: {e}"
                            )
                            date_obj = datetime.now()  # Use current time as fallback
                    else:
                        logger.debug(
                            f"No date provided for message {telegram_id}, using current time"
                        )
                        date_obj = datetime.now()  # Use current time as fallback

                    media_type = msg_info.get("media_type", "unknown")
                    file_id = msg_info.get("file_id")

                    # Insert or update the message, preserving filename data from reverse sync
                    try:
                        if processed_count <= 3:
                            logger.debug(
                                f"About to INSERT/UPDATE: telegram_id={telegram_id}, channel_id={channel_id}, media_type={media_type}, file_id={file_id}"
                            )

                        # First try to update existing message preserving filename data
                        # This ensures reverse sync data is not lost during enumeration
                        update_cursor = await conn.execute(
                            """
                            UPDATE messages
                            SET date = ?, media_type = ?, file_id = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE telegram_id = ? AND channel_id = ?
                        """,
                            (date_obj, media_type, file_id, telegram_id, channel_id),
                        )

                        if update_cursor.rowcount == 0:
                            # No existing record to update, insert new one
                            await conn.execute(
                                """
                                INSERT INTO messages (
                                    telegram_id, channel_id, date, media_type, file_id
                                ) VALUES (?, ?, ?, ?, ?)
                            """,
                                (
                                    telegram_id,
                                    channel_id,
                                    date_obj,
                                    media_type,
                                    file_id,
                                ),
                            )
                            if processed_count <= 3:
                                logger.debug(f"Inserted new message {telegram_id}")
                        else:
                            if processed_count <= 3:
                                logger.debug(
                                    f"Updated existing message {telegram_id} (preserving filename)"
                                )

                        logger.debug(
                            f"Successfully processed message {telegram_id} with channel_id {channel_id}"
                        )
                    except sqlite3.IntegrityError as insert_error:
                        logger.error(
                            f"🚨 IMMEDIATE FK ERROR at message {processed_count}: {insert_error}"
                        )
                        logger.error(
                            f"🚨 Failed message: telegram_id={telegram_id}, channel_id={channel_id}"
                        )
                        if "FOREIGN KEY constraint failed" in str(insert_error):
                            logger.error(
                                f"FK constraint failed for message {telegram_id}: channel_id={channel_id}"
                            )
                            # Double-check if channel exists
                            check_cursor = await conn.execute(
                                "SELECT id, name, telegram_id FROM channels WHERE id = ?",
                                (channel_id,),
                            )
                            check_row = await check_cursor.fetchone()
                            if check_row:
                                logger.error(
                                    f"Channel EXISTS: id={check_row['id']}, name='{check_row['name']}', telegram_id={check_row['telegram_id']}"
                                )
                            else:
                                logger.error(
                                    f"Channel {channel_id} NOT FOUND in database!"
                                )
                        raise
                    except Exception as e:
                        logger.error(f"An unexpected error occurred: {e}")
                        raise

                # Before committing, re-enable FK constraints and validate
                await conn.execute(f"PRAGMA foreign_keys = {original_fk_state}")
                logger.debug(f"Re-enabled FK constraints: {original_fk_state}")

                # Clean up orphaned download_history records that reference non-existent messages
                logger.debug("Cleaning up orphaned download_history records...")
                cleanup_cursor = await conn.execute(
                    """
                    DELETE FROM download_history
                    WHERE message_id NOT IN (SELECT id FROM messages)
                """
                )
                if cleanup_cursor.rowcount > 0:
                    logger.info(
                        f"Cleaned up {cleanup_cursor.rowcount} orphaned download_history records"
                    )

                # Manually check for FK violations before commit
                fk_check_cursor = await conn.execute("PRAGMA foreign_key_check")
                violations = await fk_check_cursor.fetchall()
                if violations:
                    logger.error(
                        f"🚨 FK violations detected before commit ({len(violations)} violations):"
                    )
                    for i, violation in enumerate(
                        violations[:10]
                    ):  # Show first 10 violations
                        try:
                            # PRAGMA foreign_key_check returns: table, rowid, parent, fkid
                            table = violation[0] if len(violation) > 0 else "unknown"
                            rowid = violation[1] if len(violation) > 1 else "unknown"
                            parent = violation[2] if len(violation) > 2 else "unknown"
                            fkid = violation[3] if len(violation) > 3 else "unknown"
                            logger.error(
                                f"  Violation {i + 1}: table='{table}', rowid={rowid}, parent='{parent}', fkid={fkid}"
                            )
                        except Exception as parse_error:
                            logger.error(
                                f"  Violation {i + 1}: {violation} (parse error: {parse_error})"
                            )
                    if len(violations) > 10:
                        logger.error(
                            f"  ... and {len(violations) - 10} more violations"
                        )

                    # Don't raise immediately - let's see if it's a transient issue
                    logger.warning(
                        "FK violations detected but continuing with commit to see if they're transient"
                    )
                    # raise sqlite3.IntegrityError("Foreign key violations detected during manual check")

                await conn.commit()
                logger.debug(f"Batch saved successfully: {len(messages)} messages")

            except Exception as e:
                await conn.rollback()
                logger.error(f"Batch transaction failed: {e}")

                # If it's a FK error, run detailed diagnostics
                if "FOREIGN KEY constraint failed" in str(e):
                    try:
                        logger.error("=== FOREIGN KEY VIOLATION DETAILS ===")
                        fk_check_cursor = await conn.execute("PRAGMA foreign_key_check")
                        violations = await fk_check_cursor.fetchall()
                        for violation in violations:
                            logger.error(
                                f"FK Violation: {dict(violation) if hasattr(violation, 'keys') else violation}"
                            )

                        # Check current channel state
                        ch_cursor = await conn.execute(
                            "SELECT id, name, telegram_id FROM channels"
                        )
                        channels = await ch_cursor.fetchall()
                        logger.error(
                            f"Current channels: {[dict(ch) for ch in channels]}"
                        )

                    except Exception as diag_error:
                        logger.error(f"Failed to run FK diagnostics: {diag_error}")

                raise
            finally:
                # Ensure defer_foreign_keys is always reset to OFF
                try:
                    await conn.execute("PRAGMA defer_foreign_keys = OFF")
                except Exception as e:
                    logger.debug(f"Failed to reset defer_foreign_keys: {e}")
                    pass

    @log_performance("db_load_enumerated_messages")
    async def load_enumerated_messages(self) -> dict[str, dict[str, Any]]:
        """
        Load enumerated messages from database in JSON-compatible format.

        Returns:
            Dictionary of message_id -> message_info (compatible with existing code)
        """
        channel_id = await self.get_channel_id()
        messages = {}

        async with get_connection(self.channel_name) as conn:
            cursor = await conn.execute(
                """
                SELECT telegram_id, date, media_type, file_id, file_size
                FROM messages
                WHERE channel_id = ? AND media_type IS NOT NULL AND media_type != 'metadata'
                ORDER BY telegram_id
            """,
                (channel_id,),
            )

            for row in await cursor.fetchall():  # Fetch all rows for iteration
                msg_id_str = str(row["telegram_id"])
                messages[msg_id_str] = {
                    "id": row["telegram_id"],
                    "date": row["date"],
                    "media_type": row["media_type"],
                    "file_id": row["file_id"],
                }
                if row["file_size"]:
                    messages[msg_id_str]["file_size"] = row["file_size"]

        logger.debug(
            f"Loaded {len(messages)} enumerated messages for channel '{self.channel_name}'"
        )
        return messages

    # === Database Sharding Management ===

    def should_shard_database(self) -> bool:
        """Check if this channel's database should be sharded."""
        return self._shard_manager.should_shard_database()

    def get_sharding_status(self) -> dict[str, Any]:
        """Get comprehensive sharding status for this channel."""
        return self._shard_manager.get_shard_summary()

    def needs_new_shard(self) -> bool:
        """Check if current shard needs to be archived and a new one created."""
        return self._shard_manager.needs_new_shard()

    # === Download Tracking ===

    @log_performance("db_save_downloaded_files")
    async def save_downloaded_files(
        self, downloaded_files: dict[str, dict[str, Any]]
    ) -> None:
        """
        Save downloaded files tracking to database.

        Args:
            downloaded_files: Dictionary of message_id -> download_info
        """
        channel_id = await self.get_channel_id()

        async with get_connection(self.channel_name) as conn:
            for msg_id_str, download_info in downloaded_files.items():
                telegram_id = int(msg_id_str)

                # Update message download status
                await conn.execute(
                    """
                    UPDATE messages
                    SET download_status = 'completed',
                        filename = ?,
                        download_path = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE telegram_id = ? AND channel_id = ?
                """,
                    (
                        download_info.get("filename"),
                        download_info.get("download_path"),
                        telegram_id,
                        channel_id,
                    ),
                )

                # Record download history
                await conn.execute(
                    """
                    INSERT INTO download_history
                    (message_id, status, start_time, end_time, file_size)
                    SELECT id, 'completed', ?, ?, ?
                    FROM messages
                    WHERE telegram_id = ? AND channel_id = ?
                """,
                    (
                        download_info.get("start_time", datetime.now()),
                        download_info.get("end_time", datetime.now()),
                        download_info.get("file_size"),
                        telegram_id,
                        channel_id,
                    ),
                )

            await conn.commit()
            logger.debug(
                f"Saved {len(downloaded_files)} downloaded file records for channel '{self.channel_name}'"
            )

    @log_performance("db_load_downloaded_files")
    async def load_downloaded_files(self) -> dict[str, dict[str, Any]]:
        """
        Load downloaded files from database in JSON-compatible format.

        Returns:
            Dictionary of message_id -> download_info (compatible with existing code)
        """
        channel_id = await self.get_channel_id()
        downloaded_files = {}

        async with get_connection(self.channel_name) as conn:
            cursor = await conn.execute(
                """
                SELECT telegram_id, filename, download_path, file_size, updated_at
                FROM messages
                WHERE channel_id = ? AND download_status = 'completed'
                ORDER BY telegram_id
            """,
                (channel_id,),
            )

            async for row in cursor:
                msg_id_str = str(row["telegram_id"])
                downloaded_files[msg_id_str] = {
                    "message_id": row["telegram_id"],
                    "filename": row["filename"],
                    "download_path": row["download_path"],
                    "file_size": row["file_size"],
                    "downloaded_at": row["updated_at"],
                }

        logger.debug(
            f"Loaded {len(downloaded_files)} downloaded file records for channel '{self.channel_name}'"
        )
        return downloaded_files

    # === Message Content and Thread Management ===

    @log_performance("db_save_message_with_content")
    async def save_message_with_content(
        self,
        telegram_id: int,
        message_text: str | None = None,
        reply_to_message_id: int | None = None,
        date: datetime | None = None,
        media_type: str | None = None,
        file_id: str | None = None,
        file_size: int | None = None,
    ) -> None:
        """
        Save a complete message with text content and thread relationship.

        Args:
            telegram_id: Telegram message ID
            message_text: Text content of the message
            reply_to_message_id: ID of message this is replying to (for threading)
            date: Message date
            media_type: Type of media attached
            file_id: File ID if media present
            file_size: Size of media file
        """
        channel_id = await self.get_channel_id()

        if date is None:
            date = datetime.now()

        async with get_connection(self.channel_name) as conn:
            # Try to update existing message first (UPDATE-first pattern)
            update_cursor = conn.execute(
                """
                UPDATE messages
                SET reply_to_message_id = ?, date = ?, text = ?, media_type = ?, file_id = ?, file_size = ?, updated_at = CURRENT_TIMESTAMP
                WHERE telegram_id = ? AND channel_id = ?
            """,
                (
                    reply_to_message_id,
                    date,
                    message_text,
                    media_type,
                    file_id,
                    file_size,
                    telegram_id,
                    channel_id,
                ),
            )

            if update_cursor.rowcount == 0:
                # No existing record to update, insert new one
                conn.execute(
                    """
                    INSERT INTO messages
                    (telegram_id, channel_id, reply_to_message_id, date, text, media_type, file_id, file_size)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        telegram_id,
                        channel_id,
                        reply_to_message_id,
                        date,
                        message_text,
                        media_type,
                        file_id,
                        file_size,
                    ),
                )
            conn.commit()

        logger.debug(
            f"Saved message {telegram_id} with text content for channel '{self.channel_name}'"
        )

    @log_performance("db_get_messages_by_thread")
    async def get_messages_by_thread(
        self, thread_root_id: int | None = None, include_root: bool = True
    ) -> list[dict[str, Any]]:
        """
        Get messages organized by thread.

        Args:
            thread_root_id: Root message ID to get thread for (None for all thread roots)
            include_root: Whether to include the root message in results

        Returns:
            List of message dictionaries with thread relationships
        """
        channel_id = await self.get_channel_id()

        async with get_connection(self.channel_name) as conn:
            if thread_root_id is None:
                # Get all thread root messages (messages with replies)
                sql = """
                    SELECT DISTINCT m1.telegram_id, m1.date, m1.text, m1.media_type, m1.file_id,
                           COUNT(m2.telegram_id) as reply_count
                    FROM messages m1
                    LEFT JOIN messages m2 ON m2.reply_to_message_id = m1.telegram_id
                    WHERE m1.channel_id = ? AND m1.reply_to_message_id IS NULL
                    GROUP BY m1.telegram_id
                    HAVING reply_count > 0
                    ORDER BY m1.date ASC
                """
                cursor = await conn.execute(sql, (channel_id,))
            else:
                # Get specific thread messages
                if include_root:
                    sql = """
                        SELECT telegram_id, date, text, media_type, file_id, reply_to_message_id,
                               CASE WHEN reply_to_message_id IS NULL THEN 0 ELSE 1 END as is_reply
                        FROM messages
                        WHERE channel_id = ? AND (telegram_id = ? OR reply_to_message_id = ?)
                        ORDER BY is_reply ASC, date ASC
                    """
                    cursor = await conn.execute(
                        sql, (channel_id, thread_root_id, thread_root_id)
                    )
                else:
                    sql = """
                        SELECT telegram_id, date, text, media_type, file_id, reply_to_message_id
                        FROM messages
                        WHERE channel_id = ? AND reply_to_message_id = ?
                        ORDER BY date ASC
                    """
                    cursor = await conn.execute(sql, (channel_id, thread_root_id))

            messages = []
            for row in cursor:
                # Convert sqlite3.Row to dict for safe access
                row_dict = dict(row)
                messages.append(
                    {
                        "telegram_id": row_dict["telegram_id"],
                        "date": row_dict["date"],
                        "text": row_dict["text"],
                        "media_type": row_dict["media_type"],
                        "file_id": row_dict["file_id"],
                        "reply_to_message_id": row_dict.get("reply_to_message_id"),
                        "reply_count": row_dict.get("reply_count", 0),
                    }
                )

        return messages

    @log_performance("db_get_thread_roots")
    async def get_thread_roots(self) -> list[dict[str, Any]]:
        """Get all thread root messages (messages that have replies)."""
        return await self.get_messages_by_thread(thread_root_id=None)

    @log_performance("db_search_messages")
    async def search_messages(
        self, search_text: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Search messages by text content.

        Args:
            search_text: Text to search for
            limit: Maximum number of results

        Returns:
            List of matching messages with context
        """
        channel_id = await self.get_channel_id()

        async with get_connection(self.channel_name) as conn:
            cursor = await conn.execute(
                """
                SELECT telegram_id, date, text, media_type, file_id, reply_to_message_id
                FROM messages
                WHERE channel_id = ? AND text LIKE ? AND text IS NOT NULL
                ORDER BY date DESC
                LIMIT ?
            """,
                (channel_id, f"%{search_text}%", limit),
            )

            messages = []
            for row in cursor:
                # Convert sqlite3.Row to dict for safe access
                row_dict = dict(row)
                messages.append(
                    {
                        "telegram_id": row_dict["telegram_id"],
                        "date": row_dict["date"],
                        "text": row_dict["text"],
                        "media_type": row_dict["media_type"],
                        "file_id": row_dict["file_id"],
                        "reply_to_message_id": row_dict["reply_to_message_id"],
                    }
                )

        return messages

    # === Enhanced Message Queries ===

    @log_performance("db_get_messages_to_download")
    async def get_messages_to_download(
        self, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Get messages that need to be downloaded.

        Args:
            limit: Optional limit on number of messages

        Returns:
            List of message dictionaries ready for download
        """
        channel_id = await self.get_channel_id()

        async with get_connection(self.channel_name) as conn:
            sql = """
                SELECT telegram_id, media_type, file_id, file_size, filename
                FROM messages
                WHERE channel_id = ?
                AND media_type IS NOT NULL AND media_type != 'metadata'
                AND download_status IN ('pending', 'failed')
                ORDER BY date ASC
            """
            params = [channel_id]

            if limit:
                sql += " LIMIT ?"
                params.append(limit)

            cursor = await conn.execute(sql, params)
            messages = []

            async for row in cursor:
                messages.append(
                    {
                        "id": row["telegram_id"],
                        "media_type": row["media_type"],
                        "file_id": row["file_id"],
                        "file_size": row["file_size"],
                        "filename": row["filename"],
                    }
                )

        return messages

    @log_performance("db_update_download_status")
    async def update_download_status(
        self,
        telegram_id: int,
        status: str,
        filename: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """
        Update download status for a message.

        Args:
            telegram_id: Telegram message ID
            status: New status (pending, downloading, completed, failed, skipped)
            filename: Optional filename if completed
            error_message: Optional error message if failed
        """
        channel_id = await self.get_channel_id()

        async with get_connection(self.channel_name) as conn:
            await conn.execute(
                """
                UPDATE messages
                SET download_status = ?,
                    filename = COALESCE(?, filename),
                    error_message = ?,
                    download_attempts = download_attempts + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE telegram_id = ? AND channel_id = ?
            """,
                (status, filename, error_message, telegram_id, channel_id),
            )

            await conn.commit()

    async def create_orphaned_file_record(
        self,
        channel_id: int,
        filename: str,
        file_size: int,
        file_path: str,
    ) -> None:
        """
        Create a database record for an orphaned file that already exists on disk.

        This marks the file as "completed" to prevent the system from trying to
        download it again, which is useful for reconciling existing files.

        Args:
            channel_id: Channel ID for the record
            filename: Name of the file
            file_size: Size of the file in bytes
            file_path: Full path to the file on disk
        """
        # Generate a synthetic telegram_id based on filename hash to make it deterministic
        import hashlib

        telegram_id = abs(hashlib.md5(filename.encode()).hexdigest().__hash__()) % (
            10**10
        )

        # Create a minimal message record to represent this orphaned file
        async with get_connection(self.channel_name) as conn:
            try:
                # Insert a synthetic message record
                await conn.execute(
                    """
                    INSERT OR IGNORE INTO messages
                    (telegram_id, channel_id, date, media_type, file_size, filename, download_status, download_path)
                    VALUES (?, ?, datetime('now'), 'orphaned', ?, ?, 'completed', ?)
                    """,
                    (
                        telegram_id,
                        channel_id,
                        file_size,
                        filename,
                        file_path,
                    ),
                )

                # Also record in download history
                await conn.execute(
                    """
                    INSERT OR IGNORE INTO download_history
                    (telegram_id, channel_id, start_time, end_time, file_size, status)
                    VALUES (?, ?, datetime('now'), datetime('now'), ?, 'completed')
                    """,
                    (
                        telegram_id,
                        channel_id,
                        file_size,
                    ),
                )

                await conn.commit()
                logger.debug(f"Created orphaned file record for {filename}")

            except Exception as e:
                logger.error(
                    f"Failed to create orphaned file record for {filename}: {e}"
                )
                # Don't re-raise - we want graceful degradation

    # === Statistics and Metadata ===

    @log_performance("db_get_channel_statistics")
    async def get_channel_statistics(self) -> dict[str, Any]:
        """Get comprehensive channel statistics."""
        channel_id = await self.get_channel_id()

        async with get_connection(self.channel_name) as conn:
            # Basic counts
            cursor = await conn.execute(
                """
                SELECT
                    COUNT(*) as total_messages,
                    COUNT(CASE WHEN media_type IS NOT NULL THEN 1 END) as media_messages,
                    COUNT(CASE WHEN download_status = 'completed' THEN 1 END) as downloaded,
                    COUNT(CASE WHEN download_status = 'pending' THEN 1 END) as pending,
                    COUNT(CASE WHEN download_status = 'failed' THEN 1 END) as failed,
                    MIN(date) as earliest_message,
                    MAX(date) as latest_message
                FROM messages
                WHERE channel_id = ?
            """,
                (channel_id,),
            )

            stats = dict(await cursor.fetchone())

            # Thread statistics
            cursor = await conn.execute(
                """
                SELECT
                    COUNT(DISTINCT reply_to_message_id) as thread_count
                FROM messages
                WHERE channel_id = ? AND reply_to_message_id IS NOT NULL
            """,
                (channel_id,),
            )

            thread_stats = await cursor.fetchone()
            stats["thread_count"] = thread_stats["thread_count"]

            return stats

    @log_performance("db_save_enumeration_metadata")
    async def save_enumeration_metadata(self, metadata: dict[str, Any]) -> None:
        """Save enumeration metadata."""
        # For now, store in a simple key-value way
        # Could be enhanced with a dedicated metadata table
        channel_id = await self.get_channel_id()

        async with get_connection(self.channel_name) as conn:
            for key, value in metadata.items():
                await conn.execute(
                    """
                    INSERT OR REPLACE INTO messages
                    (telegram_id, channel_id, date, text, media_type)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (-1, channel_id, datetime.now(), f"{key}:{value}", "metadata"),
                )
            await conn.commit()

    @log_performance("db_load_enumeration_metadata")
    async def load_enumeration_metadata(self) -> dict[str, Any]:
        """Load enumeration metadata."""
        channel_id = await self.get_channel_id()
        metadata = {}

        async with get_connection(self.channel_name) as conn:
            cursor = await conn.execute(
                """
                SELECT text FROM messages
                WHERE channel_id = ? AND media_type = 'metadata'
            """,
                (channel_id,),
            )

            async for row in cursor:
                if ":" in row["text"]:
                    key, value = row["text"].split(":", 1)
                    try:
                        metadata[key] = int(value)
                    except ValueError as e:
                        # Keep as string if integer conversion fails
                        logger.debug(
                            f"Integer conversion failed for metadata key '{key}' value '{value}': {e}"
                        )
                        metadata[key] = value

        return metadata


# === Compatibility Functions ===
# These functions maintain compatibility with existing JSON-based code


def get_storage(channel_name: str, telegram_id: int | None = None) -> DatabaseStorage:
    """Get a DatabaseStorage instance for a channel.

    Args:
        channel_name: Name of the channel
        telegram_id: Optional Telegram ID for channel identification/creation
    """
    return DatabaseStorage(channel_name, telegram_id=telegram_id)


async def load_enumerated_files(channel_name: str) -> dict[str, dict[str, Any]]:
    """Load enumerated files - database replacement for JSON function."""
    storage = get_storage(channel_name)
    return await storage.load_enumerated_messages()


async def save_enumerated_files(
    channel_name: str,
    enumerated_files: dict[str, dict[str, Any]],
    telegram_channel_id: int | None = None,
) -> None:
    """Save enumerated files - database replacement for JSON function."""
    storage = get_storage(channel_name)
    if telegram_channel_id:
        await storage.save_enumerated_messages(enumerated_files, telegram_channel_id)
    else:
        # No telegram_channel_id provided - skip database storage
        raise ConfigurationError(
            "telegram_channel_id is required for database storage",
            config_key="telegram_channel_id",
        )


async def load_downloaded_files(channel_name: str) -> dict[str, dict[str, Any]]:
    """Load downloaded files - database replacement for JSON function."""
    storage = get_storage(channel_name)
    return await storage.load_downloaded_files()


async def save_downloaded_files(
    channel_name: str, downloaded_files: dict[str, dict[str, Any]]
) -> None:
    """Save downloaded files - database replacement for JSON function."""
    storage = get_storage(channel_name)
    await storage.save_downloaded_files(downloaded_files)


async def load_enumeration_metadata(channel_name: str) -> dict[str, Any]:
    """Load enumeration metadata - database replacement for JSON function."""
    storage = get_storage(channel_name)
    return await storage.load_enumeration_metadata()


async def save_enumeration_metadata(
    channel_name: str, metadata: dict[str, Any]
) -> None:
    """Save enumeration metadata - database replacement for JSON function."""
    storage = get_storage(channel_name)
    await storage.save_enumeration_metadata(metadata)
