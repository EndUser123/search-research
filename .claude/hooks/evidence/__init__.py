"""
Evidence validation system with layered approach.

This module provides unified evidence validation that separates:
1. Content validity (file unchanged via hash verification)
2. Workflow causality (fresh observation this turn)

Post-block behavior:
- Hash-verified evidence: ACCEPT (content valid, ceremony unnecessary)
- Fresh observation: ACCEPT (workflow causality satisfied)
- Neither: REQUIRE_OBSERVATION
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional


@dataclass(frozen=True)
class EvidenceValidity:
    """Result of evidence validation check.

    Attributes:
        is_valid: Whether evidence is valid for the claim
        source: Type of evidence that validated the claim
        cached_hash: The hash value if source is "hash_verified"
        observation_age_seconds: Age of the evidence in seconds
    """
    is_valid: bool
    source: Literal["hash_verified", "fresh_observation", "none"]
    cached_hash: str | None
    observation_age_seconds: float | None


class EvidenceValidator:
    """Unified evidence validation with layered approach.

    Layer 1: Hash-verified content (file unchanged?)
    Layer 2: Fresh observation (tool used THIS turn?)
    Layer 3: No evidence at all
    """

    HASH_CACHE_TTL_SECONDS = 1800  # 30 minutes
    FRESH_OBSERVATION_TTL_SECONDS = 60  # 1 minute

    def __init__(self, cache_dir: Path):
        """Initialize EvidenceValidator with cache directory.

        Args:
            cache_dir: Directory to store hash cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _compute_file_hash_uncached(self, path: Path) -> str:
        """Compute SHA256 hash of file contents without LRU cache.

        Use this when you need to verify current file content regardless
        of what's in the LRU cache.

        Args:
            path: Path to file to hash

        Returns:
            SHA256 hash as hex string, or empty string if file doesn't exist
        """
        if not path.exists():
            return ""

        h = hashlib.sha256()
        try:
            with path.open("rb") as f:
                # Read in 1MB chunks for memory efficiency
                for chunk in iter(lambda: f.read(1024 * 1024), b""):
                    h.update(chunk)
            return h.hexdigest()
        except OSError:
            return ""

    @lru_cache(maxsize=1024)
    def _file_hash(self, path: Path) -> str:
        """Compute SHA256 hash of file contents.

        Results are cached via @lru_cache for performance.

        Args:
            path: Path to file to hash

        Returns:
            SHA256 hash as hex string, or empty string if file doesn't exist
        """
        return self._compute_file_hash_uncached(path)

    def validate_claim_evidence(
        self,
        claimed_paths: set[Path],
        observation_receipt: Optional[dict],
        post_block_required: bool = False,
        terminal_key: str = "default"
    ) -> EvidenceValidity:
        """Validate claim evidence using layered approach.

        Checks hash cache first (content validity), then falls back to
        fresh observation (workflow causality).

        IMPORTANT: For hash-verified evidence, ALL claimed paths must be
        verified. If any file has changed or lacks valid cache, the overall
        validation fails (returns is_valid=False).

        Args:
            claimed_paths: Set of file paths referenced in the claim
            observation_receipt: Optional observation receipt metadata
            post_block_required: Whether this is a post-block validation
            terminal_key: Terminal identifier for cache isolation

        Returns:
            EvidenceValidity result indicating validation outcome
        """
        now = time.time()

        # Layer 1: Check hash cache for content validity
        # ALL claimed paths must be hash-verified for this layer to succeed
        if claimed_paths:
            hash_cache = self._load_hash_cache(terminal_key)
            all_verified = True
            latest_age = 0.0
            verified_hash = None

            for path in claimed_paths:
                cache_entry = hash_cache.get(str(path))
                if not cache_entry:
                    # No cache entry for this path
                    all_verified = False
                    break

                cached_hash = cache_entry.get("hash")
                cached_at = cache_entry.get("updated_at", 0)

                # Verify hash still matches (file hasn't changed)
                current_hash = self._compute_file_hash_uncached(path)
                if not current_hash or current_hash != cached_hash:
                    # File has changed
                    all_verified = False
                    break

                age_seconds = now - cached_at
                if age_seconds > self.HASH_CACHE_TTL_SECONDS:
                    # Cache expired
                    all_verified = False
                    break

                # Track the latest age for reporting
                if age_seconds > latest_age:
                    latest_age = age_seconds
                    verified_hash = cached_hash

            if all_verified:
                # All files verified with hash cache
                return EvidenceValidity(
                    is_valid=True,
                    source="hash_verified",
                    cached_hash=verified_hash,
                    observation_age_seconds=latest_age
                )

        # Layer 2: Check for fresh observation (workflow causality)
        if observation_receipt and post_block_required:
            receipt_age = now - observation_receipt.get("updated_at", 0)
            if receipt_age <= self.FRESH_OBSERVATION_TTL_SECONDS:
                return EvidenceValidity(
                    is_valid=True,
                    source="fresh_observation",
                    cached_hash=None,
                    observation_age_seconds=receipt_age
                )

        # Layer 3: No valid evidence found
        return EvidenceValidity(
            is_valid=False,
            source="none",
            cached_hash=None,
            observation_age_seconds=None
        )

    def _load_hash_cache(self, terminal_key: str) -> dict:
        """Load hash cache from disk for a terminal.

        Args:
            terminal_key: Terminal identifier for cache file naming

        Returns:
            Dictionary mapping file paths to cache entries
        """
        cache_file = self.cache_dir / f"hash_cache_{terminal_key}.json"
        if not cache_file.exists():
            return {}
        try:
            return json.loads(cache_file.read_text())
        except (OSError, json.JSONDecodeError):
            return {}

    def update_hash_cache(
        self,
        file_path: Path,
        terminal_key: str = "default"
    ) -> str:
        """Update hash cache with current file hash.

        Args:
            file_path: Path to file to cache
            terminal_key: Terminal identifier for cache isolation

        Returns:
            The hash that was cached
        """
        file_hash = self._file_hash(file_path)
        if not file_hash:
            return ""

        cache_file = self.cache_dir / f"hash_cache_{terminal_key}.json"
        try:
            if cache_file.exists():
                cache_data = json.loads(cache_file.read_text())
            else:
                cache_data = {}

            cache_data[str(file_path)] = {
                "hash": file_hash,
                "updated_at": time.time()
            }

            cache_file.write_text(json.dumps(cache_data, indent=2))
        except (OSError, json.JSONDecodeError):
            # Fail silently - cache miss is acceptable
            pass

        return file_hash
