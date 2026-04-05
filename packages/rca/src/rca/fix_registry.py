"""
Fix Registry for Stack Trace Fingerprinting

Stores fingerprints of errors with their applied fixes.
Enables instant lookup: "Seen this error before? → Here's what worked."
"""

from __future__ import annotations

import json
import logging
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .stack_trace_fingerprint import (
    FixRecord,
    StackTraceFingerprint,
    fingerprint_from_error,
)

logger = logging.getLogger(__name__)


class FixRegistry:
    """Registry of error fingerprints and their fixes."""

    DEFAULT_CACHE_DIR = "P:/__csf/.data/rca"
    REGISTRY_FILE = "fix_registry.json"

    def __init__(self, cache_dir: str | Path | None = None) -> None:
        """
        Initialize the fix registry.

        Args:
            cache_dir: Directory for registry file (default: __csf/.data/rca/)

        """
        if cache_dir is None:
            cache_dir = self.DEFAULT_CACHE_DIR

        self.cache_dir = Path(cache_dir)
        self.registry_file = self.cache_dir / self.REGISTRY_FILE

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load existing registry
        self._registry: dict[str, dict[str, Any]] = self._load_registry()

    def _load_registry(self) -> dict[str, dict[str, Any]]:
        """Load registry from disk."""
        if not self.registry_file.exists():
            return {"fingerprints": {}, "metadata": {"version": "1.0"}}

        try:
            data = json.loads(self.registry_file.read_text(encoding="utf-8"))
            return data
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Failed to load fix registry: %s", e)
            return {"fingerprints": {}, "metadata": {"version": "1.0"}}

    def _save_registry(self) -> bool:
        """Save registry to disk."""
        try:
            self.registry_file.write_text(
                json.dumps(self._registry, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError:
            logger.exception("Failed to save fix registry")
            return False
        else:
            return True

    def add_fix(
        self,
        fingerprint: StackTraceFingerprint,
        fix_description: str,
        verified: bool = False,
        error_message: str = "",
        commit_hash: str = "",
        related_files: list[str] | None = None,
    ) -> bool:
        """
        Add or update a fix record for a fingerprint.

        Args:
            fingerprint: The error fingerprint
            fix_description: What fix was applied
            verified: Whether the fix was verified to work
            error_message: The original error message (for context)
            commit_hash: Git commit hash of the fix
            related_files: Other files affected by the fix

        Returns:
            True if saved successfully

        """
        key = fingerprint.fingerprint_hash
        now = datetime.now(tz=UTC).isoformat()

        # Check if this fingerprint exists
        if key in self._registry["fingerprints"]:
            # Update existing record
            existing = self._registry["fingerprints"][key]
            existing["times_seen"] = existing.get("times_seen", 1) + 1
            existing["last_seen"] = now
            existing["verified"] = verified or existing.get("verified", False)

            # Update fix description if provided (prefer verified fixes)
            if fix_description and (verified or not existing.get("verified")):
                existing["fix_description"] = fix_description

            if commit_hash:
                existing["commit_hash"] = commit_hash

            if related_files:
                existing["related_files"] = list(
                    set(existing.get("related_files", [])) | set(related_files)
                )

            logger.info("Updated fix record for %s (seen %d times)",
                       key, existing["times_seen"])
        else:
            # Create new record
            record = FixRecord(
                fingerprint=fingerprint,
                fix_description=fix_description,
                applied_at=now,
                verified=verified,
                times_seen=1,
                last_seen=now,
                error_message=error_message,
                commit_hash=commit_hash,
                related_files=related_files or [],
            )
            self._registry["fingerprints"][key] = record.to_dict()
            logger.info("Added new fix record for %s", key)

        return self._save_registry()

    def get_fix(
        self,
        fingerprint: StackTraceFingerprint,
    ) -> FixRecord | None:
        """
        Get fix record for an exact fingerprint match.

        Args:
            fingerprint: The error fingerprint to look up

        Returns:
            FixRecord if found, None otherwise

        """
        key = fingerprint.fingerprint_hash
        data = self._registry["fingerprints"].get(key)

        if data:
            return FixRecord.from_dict(data)
        return None

    def find_similar(
        self,
        fingerprint: StackTraceFingerprint,
        min_similarity: float = 0.6,
    ) -> list[tuple[float, FixRecord]]:
        """
        Find similar fingerprints with their fixes.

        Args:
            fingerprint: The error fingerprint
            min_similarity: Minimum similarity score (0.0 to 1.0)

        Returns:
            List of (similarity, FixRecord) tuples, sorted by similarity desc

        """
        results = []

        for _key, data in self._registry["fingerprints"].items():
            record = FixRecord.from_dict(data)
            similarity = fingerprint.similarity_to(record.fingerprint)

            if similarity >= min_similarity:
                results.append((similarity, record))

        # Sort by similarity descending
        results.sort(key=lambda x: x[0], reverse=True)
        return results

    def search_by_file(
        self,
        file_path: str,
    ) -> list[FixRecord]:
        """
        Get all fix records for a specific file.

        Args:
            file_path: File path to search (normalized)

        Returns:
            List of FixRecords for that file

        """
        results = []
        normalized_path = file_path.replace("\\", "/")

        for data in self._registry["fingerprints"].values():
            record = FixRecord.from_dict(data)
            if record.fingerprint.file_path.replace("\\", "/") == normalized_path:
                results.append(record)

        return sorted(results, key=lambda r: r.times_seen, reverse=True)

    def search_by_error_type(
        self,
        error_type: str,
    ) -> list[FixRecord]:
        """
        Get all fix records for a specific error type.

        Args:
            error_type: Error type to search (e.g., "AttributeError")

        Returns:
            List of FixRecords for that error type

        """
        results = []

        for data in self._registry["fingerprints"].values():
            record = FixRecord.from_dict(data)
            if record.fingerprint.error_type == error_type:
                results.append(record)

        return sorted(results, key=lambda r: r.times_seen, reverse=True)

    def get_stats(self) -> dict[str, Any]:
        """Get registry statistics."""
        fingerprints = self._registry["fingerprints"]

        # Count by error type
        error_types: dict[str, int] = {}
        # Count by file
        files: dict[str, int] = {}
        # Total times seen
        total_seen = 0
        # Verified count
        verified_count = 0

        for data in fingerprints.values():
            record = FixRecord.from_dict(data)

            error_type = record.fingerprint.error_type
            error_types[error_type] = error_types.get(error_type, 0) + 1

            file_path = record.fingerprint.file_path
            files[file_path] = files.get(file_path, 0) + 1

            total_seen += record.times_seen
            if record.verified:
                verified_count += 1

        # Top files
        top_files = sorted(files.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_fingerprints": len(fingerprints),
            "total_times_seen": total_seen,
            "verified_fixes": verified_count,
            "error_types": error_types,
            "top_files": top_files,
            "registry_file": str(self.registry_file),
        }

    def clear_stale(self, max_age_days: int = 90) -> int:
        """
        Remove old unverified entries.

        Args:
            max_age_days: Remove entries older than this (default: 90 days)

        Returns:
            Number of entries removed

        """
        cutoff = time.time() - (max_age_days * 86400)
        removed = 0

        to_remove = []
        for key, data in self._registry["fingerprints"].items():
            record = FixRecord.from_dict(data)

            # Don't remove verified fixes
            if record.verified:
                continue

            # Parse last_seen timestamp
            try:
                from email.utils import parsedate_to_datetime
                last_seen = parsedate_to_datetime(record.last_seen).timestamp()
                if last_seen < cutoff:
                    to_remove.append(key)
            except Exception:
                pass

        for key in to_remove:
            del self._registry["fingerprints"][key]
            removed += 1

        if removed > 0:
            self._save_registry()

        return removed


# Singleton instance with thread-safe initialization
_default_registry: FixRegistry | None = None
_registry_lock = threading.Lock()


def get_fix_registry() -> FixRegistry:
    """Get the default fix registry instance (thread-safe)."""
    global _default_registry
    if _default_registry is not None:
        return _default_registry
    with _registry_lock:
        if _default_registry is None:
            _default_registry = FixRegistry()
    return _default_registry


# Convenience functions
def register_fix(
    error_message: str,
    fix_description: str,
    file_path: str = "",
    verified: bool = False,
) -> bool:
    """
    Register a fix for an error.

    Args:
        error_message: The error message or stack trace
        fix_description: What fix was applied
        file_path: Optional file path if not in error message
        verified: Whether the fix was verified

    Returns:
        True if saved successfully

    """
    fp = fingerprint_from_error(error_message, file_path)
    if not fp:
        return False

    registry = get_fix_registry()
    return registry.add_fix(fp, fix_description, verified=verified, error_message=error_message)


def lookup_fix(error_message: str, file_path: str = "") -> FixRecord | None:
    """
    Look up a fix for an error.

    Args:
        error_message: The error message or stack trace
        file_path: Optional file path if not in error message

    Returns:
        FixRecord if exact match found, None otherwise

    """
    fp = fingerprint_from_error(error_message, file_path)
    if not fp:
        return None

    registry = get_fix_registry()
    return registry.get_fix(fp)


def find_similar_fixes(
    error_message: str,
    file_path: str = "",
    min_similarity: float = 0.6,
) -> list[tuple[float, FixRecord]]:
    """
    Find similar fixes for an error.

    Args:
        error_message: The error message or stack trace
        file_path: Optional file path if not in error message
        min_similarity: Minimum similarity score

    Returns:
        List of (similarity, FixRecord) tuples

    """
    fp = fingerprint_from_error(error_message, file_path)
    if not fp:
        return []

    registry = get_fix_registry()
    return registry.find_similar(fp, min_similarity=min_similarity)


# CLI test function
def _test() -> None:
    """Run built-in tests."""
    import shutil
    import tempfile

    # Use temp directory for testing
    temp_dir = tempfile.mkdtemp()
    registry = FixRegistry(cache_dir=temp_dir, max_age_hours=24)

    print("Fix Registry Tests")
    print("=" * 60)

    # Test 1: Add a fix
    from .stack_trace_fingerprint import StackTraceFingerprint

    fp = StackTraceFingerprint(
        file_path="download_handler.py",
        line_number=127,
        error_type="AttributeError",
        function_name="get_vtt",
    )

    print("Test 1 - Add fix:")
    success = registry.add_fix(
        fp,
        "Initialize yt_dlp_options before use",
        verified=True,
        error_message="AttributeError: 'NoneType' object has no attribute '__getitem__'",
    )
    print(f"  Added: {success}")

    # Test 2: Lookup exact match
    print("Test 2 - Lookup exact match:")
    found = registry.get_fix(fp)
    print(f"  Found: {found is not None}")
    print(f"  Fix: {found.fix_description if found else 'N/A'}")

    # Test 3: Find similar
    print("Test 3 - Find similar:")
    fp2 = StackTraceFingerprint("download_handler.py", 130, "AttributeError")
    similar = registry.find_similar(fp2, min_similarity=0.6)
    print(f"  Similar fixes found: {len(similar)}")
    if similar:
        print(f"  Top similarity: {similar[0][0]:.1f}")

    # Test 4: Stats
    print("Test 4 - Stats:")
    stats = registry.get_stats()
    print(f"  Total fingerprints: {stats['total_fingerprints']}")
    print(f"  Verified fixes: {stats['verified_fixes']}")

    # Cleanup
    shutil.rmtree(temp_dir)
    print()


if __name__ == "__main__":
    _test()
