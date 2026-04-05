"""Channel data repair utility.

Fixes malformed channel entries in-place instead of deleting them.
"""

import re
import sqlite3
from datetime import datetime
from pathlib import Path


class ChannelRepairer:
    """Repairs malformed channel data in the database."""

    def __init__(self, db_path: str, log_path: str | None = None):
        """Initialize the repairer.
        
        Args:
            db_path: Path to the SQLite database
            log_path: Optional path to log file for repair operations
        """
        self.db_path = db_path
        self.log_path = Path(log_path) if log_path else None

    def _extract_channel_id(self, value: str) -> str | None:
        """Extract channel_id from URL or handle malformed formats.

        Args:
            value: Potentially malformed channel_id (URL, @prefix, etc.)

        Returns:
            Cleaned channel_id or None if cannot be extracted
        """
        if not value:
            return None

        # If it starts with UC and looks like a channel ID, return as-is
        if value.startswith("UC") and len(value) >= 20:
            return value

        # Extract from YouTube URLs
        # Pattern: /@UCxxxx or /channel/UCxxxx or /c/UCxxxx
        patterns = [
            r"@([A-Za-z0-9_-]{20,})",  # @handle format - only if long enough to be UC ID
            r"/channel/([A-Za-z0-9_-]+)",  # /channel/ format
            r"/c/([A-Za-z0-9_-]+)",  # /c/ format
            r"/user/([A-Za-z0-9_-]+)",  # /user/ format
            r"youtu\.be/([A-Za-z0-9_-]+)",  # youtu.be short URLs
        ]

        for pattern in patterns:
            match = re.search(pattern, value)
            if match:
                extracted = match.group(1)
                # Only return if it looks like a channel ID (starts with UC)
                if extracted.startswith("UC") and len(extracted) >= 20:
                    return extracted

        # Remove @ prefix only if result looks like a valid channel_id
        if value.startswith("@"):
            cleaned = value[1:]
            if cleaned.startswith("UC") and len(cleaned) >= 20:
                return cleaned

        return None

    def detect_malformed(self) -> list[dict]:
        """Detect all malformed channel entries.
        
        Returns:
            List of dicts with channel info for malformed entries
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT channel_id, channel_name, channel_url
            FROM channels
        """)

        malformed = []
        for row in cursor.fetchall():
            channel_id, channel_name, channel_url = row

            # Check for malformations
            issues = []

            # Empty channel_id
            if not channel_id or channel_id.strip() == "":
                issues.append("empty_channel_id")

            # @ prefix in channel_id
            elif channel_id.startswith("@"):
                issues.append("at_prefix")

            # URL stored as channel_id
            elif channel_id.startswith("http://") or channel_id.startswith("https://"):
                issues.append("url_as_id")

            # No UC prefix and short (likely not a real channel_id)
            elif not channel_id.startswith("UC") and len(channel_id) < 10:
                issues.append("invalid_format")

            if issues:
                malformed.append({
                    "channel_id": channel_id,
                    "channel_name": channel_name,
                    "channel_url": channel_url,
                    "issues": issues
                })

        conn.close()
        return malformed

    def _log_repair(self, old_id: str, new_id: str, action: str):
        """Log a repair operation."""
        if not self.log_path:
            return

        timestamp = datetime.now().isoformat()
        log_entry = f"{timestamp} | {action} | {old_id} -> {new_id}\n"

        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(log_entry)

    def repair_all(self, dry_run: bool = True) -> list[dict]:
        """Repair all malformed channel entries.
        
        Args:
            dry_run: If True, only report what would be repaired
            
        Returns:
            List of repaired entries with old_id and new_id
        """
        malformed = self.detect_malformed()
        repaired = []

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for entry in malformed:
            old_id = entry["channel_id"]

            # Try to extract proper channel_id
            # First try from the malformed channel_id itself
            new_id = self._extract_channel_id(old_id)

            # If that fails, try from channel_url
            if not new_id and entry["channel_url"]:
                new_id = self._extract_channel_id(entry["channel_url"])

            if not new_id:
                # Cannot repair this entry - delete it
                cursor.execute(
                    "DELETE FROM channels WHERE channel_id = ?",
                    (old_id,)
                )
                self._log_repair(old_id, None, "DELETED_UNREPAIRABLE")
                continue

            # Check if new_id would conflict with existing entry
            cursor.execute(
                "SELECT channel_id FROM channels WHERE channel_id = ?",
                (new_id,)
            )
            if cursor.fetchone():
                # Would create duplicate, skip
                continue

            if dry_run:
                repaired.append({
                    "old_id": old_id,
                    "new_id": new_id,
                    "channel_name": entry["channel_name"]
                })
                self._log_repair(old_id, new_id, "DRY_RUN")
            else:
                # Delete old entry and insert with corrected channel_id
                cursor.execute(
                    "SELECT * FROM channels WHERE channel_id = ?",
                    (old_id,)
                )
                row = cursor.fetchone()

                if row:
                    # Delete old entry
                    cursor.execute(
                        "DELETE FROM channels WHERE channel_id = ?",
                        (old_id,)
                    )

                    # Insert with corrected channel_id
                    cursor.execute(
                        "INSERT INTO channels VALUES (?, ?, ?, ?, ?)",
                        (new_id,) + row[1:]  # Skip old channel_id, use new_id
                    )

                    repaired.append({
                        "old_id": old_id,
                        "new_id": new_id,
                        "channel_name": entry["channel_name"]
                    })
                    self._log_repair(old_id, new_id, "REPAIRED")

        if not dry_run:
            conn.commit()

        conn.close()
        return repaired
