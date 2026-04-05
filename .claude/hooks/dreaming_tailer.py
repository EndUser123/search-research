"""
JSONL Tailer module (T-004).

Provides time-based partitioning for the dream journal JSONL:
- Read new events since last offset
- Skip malformed JSON lines
- Detect file rotation
- Reset offset on rotation
- Time-based partitioning
- Preserve all raw events
- Track offset across partitions
- Clean up old partitions
"""

import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Iterator, Optional

logger = logging.getLogger(__name__)


class JSONLTailer:
    """
    Tails a JSONL file with time-based partitioning and offset tracking.

    Features:
    - Reads new events since last offset
    - Skips malformed JSON lines with warnings
    - Detects file rotation (size decrease)
    - Resets offset on rotation
    - Rotates files when size exceeds threshold
    - Adds date suffix to rotated files
    - Cleans up old partitions
    """

    def __init__(
        self,
        log_path: Path | str,
        state_path: Optional[Path | str] = None,
        max_size_mb: int = 50,
        retention_days: int = 30
    ):
        """
        Initialize the JSONL tailer.

        Args:
            log_path: Path to the JSONL file to tail
            state_path: Path to store offset state (defaults to log_path.state)
            max_size_mb: Maximum file size before rotation (default: 50MB)
            retention_days: Days to keep old partitions (default: 30)
        """
        self.log_path = Path(log_path)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.retention_days = retention_days

        # State file path
        if state_path is None:
            state_path = self.log_path.parent / f"{self.log_path.stem}.state"
        self.state_path = Path(state_path)

        # Initialize offset
        self.offset: int = 0
        self._previous_size: int = 0

        # Load state if exists, otherwise initialize from current file
        self._load_state()

        # If no state file exists, initialize previous_size from current file
        if not self.state_path.exists() and self.log_path.exists():
            self._previous_size = self.log_path.stat().st_size

    def _load_state(self) -> None:
        """Load offset and previous size from state file."""
        if self.state_path.exists():
            try:
                with open(self.state_path) as f:
                    state = json.load(f)
                    self.offset = state.get('offset', 0)
                    self._previous_size = state.get('previous_size', 0)
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to load state from {self.state_path}: {e}")
                self.offset = 0
                self._previous_size = 0
        else:
            self.offset = 0
            self._previous_size = 0

    def _save_state(self) -> None:
        """Save offset and previous size to state file atomically."""
        state = {
            'offset': self.offset,
            'previous_size': self._previous_size,
            'timestamp': datetime.now(UTC).isoformat()
        }

        # Atomic write: write to temp file, then rename
        temp_path = self.state_path.with_suffix('.tmp')
        try:
            with open(temp_path, 'w') as f:
                json.dump(state, f, indent=2)
            temp_path.replace(self.state_path)
        except OSError as e:
            logger.warning(f"Failed to save state to {self.state_path}: {e}")

    def _detect_rotation(self) -> bool:
        """
        Detect if file has been rotated (size decreased).

        Returns:
            True if rotation detected (file size < previous size)
        """
        if not self.log_path.exists():
            return False

        current_size = self.log_path.stat().st_size

        # Rotation detected if current size < previous size
        if current_size < self._previous_size:
            logger.info(f"Rotation detected: {self.log_path} size {self._previous_size} -> {current_size}")
            return True

        return False

    def read_new_events(self) -> Iterator[dict]:
        """
        Read new events since last offset.

        Yields:
            Parsed JSON events (dicts)

        Skips malformed JSON lines with warnings.
        Resets offset on rotation detection.
        """
        if not self.log_path.exists():
            return

        # Check for rotation
        if self._detect_rotation():
            self.offset = 0
            self._save_state()

        # Read events from current offset
        line_number = 0
        events_yielded = 0
        try:
            with open(self.log_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        line_number += 1
                        continue

                    # Skip lines before offset
                    if line_number < self.offset:
                        line_number += 1
                        continue

                    # Parse and yield event
                    try:
                        event = json.loads(line)
                        yield event
                        events_yielded += 1
                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping malformed JSON at line {line_number + 1}: {e}")

                    line_number += 1

        except OSError as e:
            logger.error(f"Failed to read {self.log_path}: {e}")
            return

        # Update offset to current line count
        self.offset = line_number
        self._previous_size = self.log_path.stat().st_size
        self._save_state()

    def check_rotation(self) -> None:
        """
        Check if file needs rotation and rotate if necessary.

        Rotation occurs when file size exceeds max_size_bytes.
        Old file is renamed with date suffix: basename_YYYY-MM-DD[_N].jsonl
        """
        if not self.log_path.exists():
            return

        current_size = self.log_path.stat().st_size

        # Rotate if exceeds threshold
        if current_size > self.max_size_bytes:
            self._rotate_file()

    def _rotate_file(self) -> None:
        """
        Rotate the log file with date suffix.

        Renames current file to: basename_YYYY-MM-DD[_N].jsonl
        Creates new empty file at original path.
        Resets offset to 0.
        """
        if not self.log_path.exists():
            return

        # Generate date suffix
        today = datetime.now(UTC).strftime("%Y-%m-%d")

        # Find next available suffix for multiple rotations per day
        counter = 0
        while True:
            if counter == 0:
                suffix = f"_{today}"
            else:
                suffix = f"_{today}_{counter}"

            rotated_path = self.log_path.with_name(
                f"{self.log_path.stem}{suffix}{self.log_path.suffix}"
            )

            if not rotated_path.exists():
                break

            counter += 1

        # Rename current file
        try:
            self.log_path.rename(rotated_path)
            logger.info(f"Rotated {self.log_path} -> {rotated_path}")
        except OSError as e:
            logger.error(f"Failed to rotate {self.log_path}: {e}")
            return

        # Create new empty file
        try:
            self.log_path.touch()
            logger.info(f"Created new {self.log_path}")
        except OSError as e:
            logger.error(f"Failed to create new {self.log_path}: {e}")
            return

        # Reset offset
        self.offset = 0
        self._previous_size = 0
        self._save_state()

    def cleanup_old_partitions(self) -> None:
        """
        Delete partition files older than retention_days.

        Looks for files matching: basename_YYYY-MM-DD*.jsonl
        Deletes files where date < (now - retention_days)
        """
        if not self.log_path.exists():
            return

        # Pattern for partition files
        pattern = f"{self.log_path.stem}_*{self.log_path.suffix}"
        partitions = list(self.log_path.parent.glob(pattern))

        cutoff_date = datetime.now(UTC) - timedelta(days=self.retention_days)

        for partition in partitions:
            # Skip the current file (no date suffix)
            if partition == self.log_path:
                continue

            # Extract date from filename
            date_str = self._extract_date_from_partition(partition)
            if date_str is None:
                continue

            try:
                partition_date = datetime.fromisoformat(date_str)
                if partition_date < cutoff_date:
                    partition.unlink()
                    logger.info(f"Deleted old partition: {partition}")
            except ValueError:
                logger.warning(f"Could not parse date from partition: {partition}")

    def _extract_date_from_partition(self, partition_path: Path) -> Optional[str]:
        """
        Extract date string from partition filename.

        Args:
            partition_path: Path to partition file

        Returns:
            ISO date string (YYYY-MM-DD) or None if not found
        """
        # Pattern: basename_YYYY-MM-DD[_N].jsonl
        stem = partition_path.stem

        # Remove basename prefix
        if not stem.startswith(self.log_path.stem + "_"):
            return None

        suffix = stem[len(self.log_path.stem) + 1:]

        # Extract date part (before optional counter)
        parts = suffix.split("_")
        if len(parts) >= 3:
            # Should be YYYY-MM-DD format
            date_str = "_".join(parts[:3])
            # Validate format
            try:
                datetime.fromisoformat(date_str)
                return date_str
            except ValueError:
                return None

        return None
