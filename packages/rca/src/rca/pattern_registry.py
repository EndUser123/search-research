"""
Pattern Fix Registry for Error Signature Matching

Stores pattern-level fixes that apply across locations.
Unlike fix_registry (location-specific), this stores solutions by error pattern.

Example:
- Pattern: null_dict_access
- Fix: "Use dict.get(key, default)"
- Works at: download_handler.py:127, batch_downloader.py:85, anywhere with same pattern

"""

from __future__ import annotations

import json
import logging
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .error_signature import (
    ErrorSignature,
    PatternFixRecord,
    SignatureMatch,
    extract_signature,
    match_to_pattern,
)

logger = logging.getLogger(__name__)


class PatternRegistry:
    """Registry of error patterns and their cross-location fixes."""

    DEFAULT_CACHE_DIR = "P:/__csf/.data/rca"
    REGISTRY_FILE = "pattern_registry.json"

    def __init__(self, cache_dir: str | Path | None = None) -> None:
        """Initialize the pattern registry."""
        if cache_dir is None:
            cache_dir = self.DEFAULT_CACHE_DIR

        self.cache_dir = Path(cache_dir)
        self.registry_file = self.cache_dir / self.REGISTRY_FILE
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._registry: dict[str, dict[str, Any]] = self._load_registry()

    def _load_registry(self) -> dict[str, dict[str, Any]]:
        """Load registry from disk."""
        if not self.registry_file.exists():
            return {"patterns": {}, "metadata": {"version": "1.0"}}

        try:
            data = json.loads(self.registry_file.read_text(encoding="utf-8"))
            return data
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Failed to load pattern registry: %s", e)
            return {"patterns": {}, "metadata": {"version": "1.0"}}

    def _save_registry(self) -> bool:
        """Save registry to disk."""
        try:
            self.registry_file.write_text(
                json.dumps(self._registry, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError:
            logger.exception("Failed to save pattern registry")
            return False
        else:
            return True

    def add_pattern_fix(
        self,
        signature: ErrorSignature,
        fix_description: str,
        fix_template: str = "",
        code_diff: str = "",
        location: str = "",
        verified: bool = False,
    ) -> bool:
        """
        Add or update a pattern fix.

        Args:
            signature: The error signature
            fix_description: What fix to apply
            fix_template: Template for generating fix
            code_diff: Example code diff
            location: Where this was applied (for tracking)
            verified: Whether the fix was verified

        Returns:
            True if saved successfully

        """
        key = signature.signature_hash
        now = datetime.now(tz=UTC).isoformat()

        if key in self._registry["patterns"]:
            # Update existing
            existing = self._registry["patterns"][key]
            existing["applied_count"] = existing.get("applied_count", 0) + 1
            existing["last_seen"] = now
            existing["verified"] = verified or existing.get("verified", False)

            if location and location not in existing.get("locations_seen", []):
                existing.setdefault("locations_seen", []).append(location)

            # Update fix description if better (verified) or new
            if fix_description and (verified or not existing.get("verified")):
                existing["fix_description"] = fix_description
            if fix_template:
                existing["fix_template"] = fix_template
            if code_diff:
                existing["code_diff"] = code_diff

            logger.info("Updated pattern fix %s (applied %d times, %d locations)",
                       signature.pattern_name,
                       existing["applied_count"],
                       len(existing.get("locations_seen", [])))
        else:
            # Create new
            record = PatternFixRecord(
                signature=signature,
                fix_description=fix_description,
                fix_template=fix_template or signature.fix_template,
                code_diff=code_diff,
                applied_count=1,
                locations_seen=[location] if location else [],
                first_seen=now,
                last_seen=now,
                verified=verified,
            )
            self._registry["patterns"][key] = record.to_dict()
            logger.info("Added new pattern fix: %s", signature.pattern_name)

        return self._save_registry()

    def get_pattern_fix(
        self,
        signature: ErrorSignature,
    ) -> PatternFixRecord | None:
        """
        Get fix record for a signature.

        Args:
            signature: The error signature

        Returns:
            PatternFixRecord if found, None otherwise

        """
        key = signature.signature_hash
        data = self._registry["patterns"].get(key)

        if data:
            return PatternFixRecord.from_dict(data)
        return None

    def find_match(
        self,
        error_message: str,
        min_confidence: float = 0.5,
    ) -> SignatureMatch | None:
        """
        Find matching pattern fix for an error.

        Args:
            error_message: The error message
            min_confidence: Minimum confidence threshold

        Returns:
            SignatureMatch if found, None otherwise

        """
        # First, find matching signature
        match = match_to_pattern(error_message)
        if not match or match.confidence < min_confidence:
            return None

        # Check if we have a recorded fix for this pattern
        fix_record = self.get_pattern_fix(match.signature)
        if fix_record:
            # Use recorded fix (potentially with code_diff)
            match.suggested_fix = fix_record.fix_description

            # Enhance match with additional context
            return SignatureMatch(
                signature=match.signature,
                confidence=match.confidence,
                matched_text=match.matched_text,
                suggested_fix=fix_record.fix_description,
            )

        # Return signature match with template fix
        return match

    def get_all_patterns(self) -> list[PatternFixRecord]:
        """Get all pattern fix records."""
        records = []
        for data in self._registry["patterns"].values():
            records.append(PatternFixRecord.from_dict(data))
        return sorted(records, key=lambda r: r.applied_count, reverse=True)

    def get_stats(self) -> dict[str, Any]:
        """Get registry statistics."""
        patterns = self._registry["patterns"]

        # Count by pattern name
        pattern_counts: dict[str, int] = {}
        total_locations = 0
        total_applied = 0
        verified_count = 0

        for data in patterns.values():
            record = PatternFixRecord.from_dict(data)
            pattern_counts[record.signature.pattern_name] = (
                pattern_counts.get(record.signature.pattern_name, 0) + 1
            )
            total_locations += len(record.locations_seen)
            total_applied += record.applied_count
            if record.verified:
                verified_count += 1

        # Top patterns
        top_patterns = sorted(
            pattern_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        return {
            "total_patterns": len(patterns),
            "total_applied": total_applied,
            "total_locations": total_locations,
            "verified_patterns": verified_count,
            "top_patterns": top_patterns,
            "registry_file": str(self.registry_file),
        }

    def search_by_pattern_name(
        self,
        pattern_name: str,
    ) -> list[PatternFixRecord]:
        """Get all records for a specific pattern name."""
        records = []
        for data in self._registry["patterns"].values():
            record = PatternFixRecord.from_dict(data)
            if record.signature.pattern_name == pattern_name:
                records.append(record)
        return records


# Singleton instance with thread-safe initialization
_default_registry: PatternRegistry | None = None
_registry_lock = threading.Lock()


def get_pattern_registry() -> PatternRegistry:
    """Get the default pattern registry instance (thread-safe)."""
    global _default_registry
    if _default_registry is not None:
        return _default_registry
    with _registry_lock:
        if _default_registry is None:
            _default_registry = PatternRegistry()
    return _default_registry


# Convenience functions
def register_pattern_fix(
    error_message: str,
    fix_description: str,
    fix_template: str = "",
    location: str = "",
    verified: bool = False,
) -> bool:
    """
    Register a pattern fix from an error message.

    Args:
        error_message: The error message
        fix_description: What fix to apply
        fix_template: Template for generating fix
        location: Where this was applied
        verified: Whether the fix was verified

    Returns:
        True if saved successfully

    """
    sig = extract_signature(error_message)
    if not sig:
        return False

    registry = get_pattern_registry()
    return registry.add_pattern_fix(
        sig,
        fix_description,
        fix_template=fix_template,
        location=location,
        verified=verified,
    )


def lookup_pattern_fix(
    error_message: str,
) -> SignatureMatch | None:
    """
    Look up a pattern fix for an error.

    Args:
        error_message: The error message

    Returns:
        SignatureMatch if found, None otherwise

    """
    registry = get_pattern_registry()
    return registry.find_match(error_message)


# CLI test function
def _test() -> None:
    """Run built-in tests."""
    import shutil
    import tempfile

    temp_dir = tempfile.mkdtemp()
    registry = PatternRegistry(cache_dir=temp_dir)

    print("Pattern Registry Tests")
    print("=" * 60)

    # Test 1: Register a pattern fix
    from .error_signature import extract_signature

    error1 = "AttributeError: 'NoneType' object has no attribute '__getitem__'"
    sig1 = extract_signature(error1)

    print("Test 1 - Register pattern fix:")
    success = registry.add_pattern_fix(
        sig1,
        "Use dict.get(key, default) or check if dict is None",
        location="download_handler.py:127",
        verified=True,
    )
    print(f"  Registered: {success}")

    # Test 2: Lookup pattern fix (same pattern, different location)
    error2 = """
Traceback:
  File "batch_downloader.py", line 85
    videos = channel["videos"]
KeyError: 'videos'
"""
    match = registry.find_match(error2)
    print("Test 2 - Pattern match for different location:")
    print(f"  Match found: {match is not None}")
    if match:
        print(f"  Pattern: {match.signature.pattern_name}")
        print(f"  Fix: {match.suggested_fix}")

    # Test 3: Stats
    print("Test 3 - Stats:")
    stats = registry.get_stats()
    print(f"  Total patterns: {stats['total_patterns']}")
    print(f"  Total applied: {stats['total_applied']}")

    # Cleanup
    shutil.rmtree(temp_dir)
    print()


if __name__ == "__main__":
    _test()
