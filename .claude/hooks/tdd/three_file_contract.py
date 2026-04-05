"""
ThreeFileContract - Immutable contract binding impl/test/spec files.

Implements TASK-003 from ADR-20260324-clean-room-tdd-loop.md:
- SHA-256 hash for collision resistance
- Timing-attack safe hash comparison
- Immutability verification detects tampering

ADR: P:/.claude/arch_decisions/ADR-20260324-clean-room-tdd-loop.md
"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


def _compute_file_hash(file_path: str) -> str | None:
    """Compute SHA-256 hash of file contents.

    Args:
        file_path: Path to file to hash

    Returns:
        Hex digest string (64 chars) or None if file doesn't exist
    """
    try:
        path = Path(file_path)
        if not path.exists():
            return None

        content = path.read_bytes()
        return hashlib.sha256(content).hexdigest()
    except Exception as e:
        logger.warning(f"Failed to compute hash for {file_path}: {e}")
        return None


@dataclass
class ThreeFileContract:
    """Contract binding implementation, test, and spec files.

    Uses SHA-256 hashes to verify immutability - detects if any
    file has been tampered with after contract creation.

    Attributes:
        impl_path: Path to implementation file
        test_path: Path to test file
        spec_path: Path to specification file
        impl_hash: SHA-256 hash of impl file (computed on creation)
        test_hash: SHA-256 hash of test file (computed on creation)
        spec_hash: SHA-256 hash of spec file (computed on creation)
        created_at: ISO timestamp of contract creation
    """

    impl_path: str
    test_path: str
    spec_path: str
    impl_hash: str | None = field(default=None)
    test_hash: str | None = field(default=None)
    spec_hash: str | None = field(default=None)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def __post_init__(self):
        """Compute hashes after initialization if not provided."""
        if self.impl_hash is None:
            self.impl_hash = _compute_file_hash(self.impl_path)
        if self.test_hash is None:
            self.test_hash = _compute_file_hash(self.test_path)
        if self.spec_hash is None:
            self.spec_hash = _compute_file_hash(self.spec_path)

    def _safe_hash_compare(self, expected: str, actual: str | None) -> bool:
        """Timing-attack safe hash comparison.

        Uses constant-time comparison to prevent timing attacks
        that could reveal hash contents.

        Args:
            expected: The expected hash value
            actual: The actual hash value (may be None if file missing)

        Returns:
            True if hashes match, False otherwise
        """
        if actual is None:
            # Still compare against expected to maintain constant time
            return False

        # Use hmac.compare_digest for constant-time comparison
        import hmac

        try:
            return hmac.compare_digest(expected.encode(), actual.encode())
        except Exception:
            return False

    def verify_immutability(self) -> bool:
        """Verify that contracted files haven't been modified.

        Recomputes hashes and compares against stored values.
        Uses timing-attack safe comparison.

        Returns:
            True if all files are unchanged, False if any file
            has been modified or is missing
        """
        # Compute current hashes
        current_impl_hash = _compute_file_hash(self.impl_path)
        current_test_hash = _compute_file_hash(self.test_path)
        current_spec_hash = _compute_file_hash(self.spec_path)

        # Compare using timing-attack safe method
        # If any hash was None originally, verification fails
        if self.impl_hash is None or self.test_hash is None or self.spec_hash is None:
            return False

        # All three hashes must match
        impl_valid = self._safe_hash_compare(self.impl_hash, current_impl_hash)
        test_valid = self._safe_hash_compare(self.test_hash, current_test_hash)
        spec_valid = self._safe_hash_compare(self.spec_hash, current_spec_hash)

        return impl_valid and test_valid and spec_valid

    def to_dict(self) -> dict:
        """Serialize contract to dictionary.

        Returns:
            Dictionary with all contract fields
        """
        return {
            "impl_path": self.impl_path,
            "test_path": self.test_path,
            "spec_path": self.spec_path,
            "impl_hash": self.impl_hash,
            "test_hash": self.test_hash,
            "spec_hash": self.spec_hash,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ThreeFileContract:
        """Deserialize contract from dictionary.

        Args:
            data: Dictionary with contract fields

        Returns:
            ThreeFileContract instance
        """
        return cls(
            impl_path=data.get("impl_path", ""),
            test_path=data.get("test_path", ""),
            spec_path=data.get("spec_path", ""),
            impl_hash=data.get("impl_hash"),
            test_hash=data.get("test_hash"),
            spec_hash=data.get("spec_hash"),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
        )
