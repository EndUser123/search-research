"""
Channel ID Fixer - Intelligent channel validation and repair.

Extracts and centralizes all channel ID fixing logic for reliable,
automatic channel management.
"""

from pathlib import Path

from loguru import logger


class ChannelFixer:
    """Intelligent channel ID validation and fixing."""

    @staticmethod
    async def auto_fix_channel_id(
        client, channel_name: str, chat_id: int
    ) -> int | None:
        """
        Intelligently auto-fix channel ID by trying multiple approaches.
        Returns the correct ID or None if it can't be fixed.
        """

        # Try multiple strategies in order of likelihood
        strategies = [
            ("stored_id", lambda: client.get_entity(chat_id)),
            ("channel_name", lambda: client.get_entity(channel_name)),
            (
                "with_at_prefix",
                lambda: client.get_entity(f"@{channel_name}")
                if not channel_name.startswith("@")
                else None,
            ),
        ]

        # Add variation strategies
        if "_" in channel_name:
            strategies.append(
                (
                    "no_underscores",
                    lambda: client.get_entity(channel_name.replace("_", "")),
                )
            )
        if not channel_name.islower():
            strategies.append(
                ("lowercase", lambda: client.get_entity(channel_name.lower()))
            )

        for strategy_name, get_entity_func in strategies:
            try:
                if get_entity_func is None:  # Skip invalid strategies
                    continue

                entity = await get_entity_func()
                correct_id = entity.id

                # Ensure proper ID format: channels/supergroups should be negative
                from telethon.tl.types import Channel, Chat

                if isinstance(entity, (Channel, Chat)):
                    # Channels and chats should have negative IDs
                    if correct_id > 0:
                        # Convert to proper channel format: -100{channel_id}
                        if hasattr(entity, "megagroup") or hasattr(entity, "broadcast"):
                            # This is a supergroup or channel
                            correct_id = -1000000000000 - correct_id
                        else:
                            # Regular group chat
                            correct_id = -correct_id

                # Log successful fixes (not for stored_id since that's not actually a fix)
                if strategy_name != "stored_id" or correct_id != chat_id:
                    try:
                        from tqdm import tqdm

                        tqdm.write(
                            f"✅ Auto-fixed '{channel_name}': {chat_id} → {correct_id} ({strategy_name})"
                        )
                    except ImportError:
                        logger.info(
                            f"✅ Auto-fixed '{channel_name}': {chat_id} → {correct_id} ({strategy_name})"
                        )

                return correct_id

            except Exception:
                continue  # Try next strategy

        # All strategies failed
        try:
            from tqdm import tqdm

            tqdm.write(f"❌ Could not auto-fix '{channel_name}' (ID: {chat_id})")
            tqdm.write(
                f"   🔧 To fix manually: python src/find_channel_id.py {channel_name}"
            )
        except ImportError:
            logger.warning(f"❌ Could not auto-fix '{channel_name}' (ID: {chat_id})")

        return None

    @staticmethod
    def persist_fix(channel_name: str, old_id: int, new_id: int) -> bool:
        """
        Update channels.toml with the corrected channel ID.
        Returns True if update was successful.
        """
        if old_id == new_id:
            return True  # No fix needed

        toml_path = Path("channels.toml")
        if not toml_path.exists():
            return False

        try:
            # Read current content
            with open(toml_path, encoding="utf-8") as f:
                content = f.read()

            # Create backup
            backup_path = toml_path.with_suffix(".toml.backup")
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Apply fix
            old_line = f"{channel_name} = {old_id}"
            new_line = f"{channel_name} = {new_id}"

            if old_line in content:
                updated_content = content.replace(old_line, new_line)

                # Write updated content
                with open(toml_path, "w", encoding="utf-8") as f:
                    f.write(updated_content)

                try:
                    from tqdm import tqdm

                    tqdm.write(f"📝 Updated channels.toml: {channel_name} = {new_id}")
                    tqdm.write(f"💾 Backup saved: {backup_path}")
                except ImportError:
                    logger.info(f"📝 Updated channels.toml: {channel_name} = {new_id}")
                    logger.info(f"💾 Backup saved: {backup_path}")

                return True

        except Exception as e:
            try:
                from tqdm import tqdm

                tqdm.write(f"⚠️ Could not update channels.toml: {e}")
            except ImportError:
                logger.warning(f"⚠️ Could not update channels.toml: {e}")

        return False

    @staticmethod
    def is_channel_id_error(error_str: str) -> bool:
        """Check if an error is related to invalid channel ID."""
        channel_error_indicators = [
            "Could not find the input entity",
            "Invalid object ID",
            "ChatIdInvalidError",
            "PeerIdInvalidError",
            "UsernameInvalidError",
            "UsernameNotOccupiedError",
        ]

        return any(indicator in error_str for indicator in channel_error_indicators)
