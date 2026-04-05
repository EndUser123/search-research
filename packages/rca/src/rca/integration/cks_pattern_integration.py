"""
CKS Integration for Error Signature Pattern Storage

Stores pattern-level fixes in CKS for semantic search and retrieval.
This replaces the JSON-based pattern_registry with a knowledge-enabled backend.

Usage:
    from rca.integration.cks_pattern_integration import CKSPatternRegistry

    registry = CKSPatternRegistry()

    # Register a pattern fix
    registry.register_fix(
        error_message="AttributeError: 'NoneType' object has no attribute '__getitem__'",
        fix_description="Use dict.get(key, default) or check if dict is None",
        location="download_handler.py:127",
        verified=True,
    )

    # Lookup a pattern fix
    match = registry.lookup(error_message)
    if match:
        print(f"Pattern: {match['pattern_name']}")
        print(f"Fix: {match['fix_description']}")
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

# import CKS
try:
    from search_research.cks.unified import CKS

    CKS_AVAILABLE = True
except ImportError:
    CKS_AVAILABLE = False
    CKS = None  # type: ignore[assignment]

# Import error signature matching
try:
    from ..error_signature import (
        ErrorSignature,
        extract_signature,
        match_to_pattern,
    )
except ImportError:
    # Fallback for standalone usage
    from rca.error_signature import (
        ErrorSignature,
        extract_signature,
        match_to_pattern,
    )

logger = logging.getLogger(__name__)


class CKSPatternRegistry:
    """CKS-backed registry for error signature pattern fixes."""

    # Entry type for CKS
    ENTRY_TYPE = "correction"  # Use 'correction' type for pattern fixes

    # Metadata schema
    METADATA_SCHEMA = {
        "pattern_name": str,
        "error_type": str,
        "signature_hash": str,
        "applied_count": int,
        "verified": bool,
        "locations_seen": list,
        "first_seen": str,
        "last_seen": str,
    }

    def __init__(self, cks_instance: CKS | None = None) -> None:
        """
        Initialize the CKS pattern registry.

        Args:
            cks_instance: Optional CKS instance (uses default if not provided)

        """
        if not CKS_AVAILABLE:
            logger.warning("CKS not available - pattern registry will fall back to JSON")
            self._cks = None
        else:
            self._cks = cks_instance if cks_instance else CKS()

    def register_fix(
        self,
        error_message: str,
        fix_description: str,
        fix_template: str = "",
        code_diff: str = "",
        location: str = "",
        verified: bool = False,
    ) -> bool:
        """
        Register a pattern fix in CKS.

        Args:
            error_message: The error message
            fix_description: What fix to apply
            fix_template: Template for generating fix
            code_diff: Example code diff
            location: Where this was applied (for tracking)
            verified: Whether the fix was verified

        Returns:
            True if saved successfully

        """
        if not self._cks:
            logger.warning("CKS not available - cannot register fix")
            return False

        # Extract signature
        sig = extract_signature(error_message)
        if not sig:
            logger.warning("Could not extract signature from error: %s", error_message[:100])
            return False

        # Check if pattern already exists
        existing = self._get_existing_pattern(sig.signature_hash)
        now = datetime.now(tz=UTC).isoformat()

        if existing:
            # Update existing pattern
            return self._update_existing_pattern(
                existing,
                fix_description,
                fix_template,
                code_diff,
                location,
                verified,
                now,
            )
        # Create new pattern entry
        return self._create_new_pattern(
            sig,
            fix_description,
            fix_template,
            code_diff,
            location,
            verified,
            now,
        )

    def _get_existing_pattern(self, signature_hash: str) -> dict[str, Any] | None:
        """Check if a pattern already exists in CKS."""
        if not self._cks:
            return None

        # Search for existing pattern by signature hash
        results = self._cks.search(
            query=signature_hash,
            entry_type=self.ENTRY_TYPE,
            limit=10,
        )

        for result in results:
            metadata = result.get("metadata", {})
            if metadata.get("signature_hash") == signature_hash:
                return result

        return None

    def _update_existing_pattern(
        self,
        existing: dict[str, Any],
        fix_description: str,
        fix_template: str,
        code_diff: str,
        location: str,
        verified: bool,
        now: str,
    ) -> bool:
        """Update existing pattern entry."""
        if not self._cks:
            return False

        try:
            metadata = existing.get("metadata", {})

            # Update counts
            metadata["applied_count"] = metadata.get("applied_count", 0) + 1
            metadata["last_seen"] = now
            metadata["verified"] = verified or metadata.get("verified", False)

            # Update locations
            if location:
                locations = metadata.get("locations_seen", [])
                if location not in locations:
                    locations.append(location)
                metadata["locations_seen"] = locations

            # Update fix if better (verified) or new
            if fix_description and (verified or not metadata.get("verified")):
                metadata["fix_description"] = fix_description
            if fix_template:
                metadata["fix_template"] = fix_template
            if code_diff:
                metadata["code_diff"] = code_diff

            # Update content with new fix info
            content = self._format_pattern_content(metadata)

            # Remove keys that conflict with ingest_correction parameters
            metadata_clean = {k: v for k, v in metadata.items() if k not in ("title", "content")}

            # Update in CKS (requires re-inserting with same ID or using update)
            # For now, we'll create a new entry and mark the old one as superseded
            entry_id = self._cks.ingest_correction(
                title=f"Pattern: {metadata.get('pattern_name', 'unknown')}",
                content=content,
                **metadata_clean,
            )

            logger.info(
                "Updated pattern fix %s (applied %d times, %d locations)",
                metadata.get("pattern_name"),
                metadata["applied_count"],
                len(metadata.get("locations_seen", [])),
            )
            return bool(entry_id)

        except Exception as e:
            logger.exception("Failed to update pattern in CKS: %s", e)
            return False

    def _create_new_pattern(
        self,
        sig: ErrorSignature,
        fix_description: str,
        fix_template: str,
        code_diff: str,
        location: str,
        verified: bool,
        now: str,
    ) -> bool:
        """Create new pattern entry in CKS."""
        if not self._cks:
            return False

        try:
            metadata = {
                "pattern_name": sig.pattern_name,
                "error_type": sig.error_type,
                "signature_hash": sig.signature_hash,
                "fix_description": fix_description,
                "fix_template": fix_template or sig.fix_template,
                "code_diff": code_diff,
                "applied_count": 1,
                "locations_seen": [location] if location else [],
                "first_seen": now,
                "last_seen": now,
                "verified": verified,
            }

            content = self._format_pattern_content(metadata)

            # Remove keys that conflict with ingest_correction parameters
            metadata_clean = {
                k: v for k, v in metadata.items() if k not in ("title", "content", "source_chunk")
            }

            entry_id = self._cks.ingest_correction(
                title=f"Pattern: {sig.pattern_name}",
                content=content,
                source_chunk=f"{sig.pattern_name}: {fix_description}",
                **metadata_clean,
            )

            logger.info("Added new pattern fix: %s", sig.pattern_name)
            return bool(entry_id)

        except Exception as e:
            logger.exception("Failed to create pattern in CKS: %s", e)
            return False

    def _format_pattern_content(self, metadata: dict[str, Any]) -> str:
        """Format pattern metadata as readable content."""
        parts = [
            f"**Pattern**: {metadata.get('pattern_name', 'unknown')}",
            f"**Error Type**: {metadata.get('error_type', 'unknown')}",
            f"**Fix**: {metadata.get('fix_description', 'No description')}",
        ]

        if metadata.get("fix_template"):
            parts.append(f"**Template**: {metadata['fix_template']}")

        if metadata.get("code_diff"):
            parts.append(f"**Code Diff**:\n```\n{metadata['code_diff']}\n```")

        parts.append(f"**Applied**: {metadata.get('applied_count', 0)} times")

        if metadata.get("locations_seen"):
            parts.append(f"**Locations**: {', '.join(metadata['locations_seen'][:5])}")
            if len(metadata["locations_seen"]) > 5:
                parts.append(f"  ... and {len(metadata['locations_seen']) - 5} more")

        if metadata.get("verified"):
            parts.append("**Status**: VERIFIED ✓")

        return "\n".join(parts)

    def lookup(self, error_message: str, min_confidence: float = 0.5) -> dict[str, Any] | None:
        """
        Look up a pattern fix for an error.

        Args:
            error_message: The error message
            min_confidence: Minimum confidence threshold

        Returns:
            Dictionary with pattern match info or None

        """
        if not self._cks:
            return None

        # First, try pattern matching
        match = match_to_pattern(error_message)
        if not match or match.confidence < min_confidence:
            return None

        # Check CKS for stored fix
        sig_hash = match.signature.signature_hash
        existing = self._get_existing_pattern(sig_hash)

        if existing:
            metadata = existing.get("metadata", {})
            return {
                "pattern_name": metadata.get("pattern_name"),
                "error_type": metadata.get("error_type"),
                "fix_description": metadata.get("fix_description", match.suggested_fix),
                "fix_template": metadata.get("fix_template", ""),
                "code_diff": metadata.get("code_diff", ""),
                "applied_count": metadata.get("applied_count", 0),
                "locations_seen": metadata.get("locations_seen", []),
                "verified": metadata.get("verified", False),
                "confidence": match.confidence,
                "source": "cks",
            }

        # Return template match if no stored fix
        return {
            "pattern_name": match.signature.pattern_name,
            "error_type": match.signature.error_type,
            "fix_description": match.suggested_fix,
            "fix_template": match.signature.fix_template,
            "code_diff": "",
            "applied_count": 0,
            "locations_seen": [],
            "verified": False,
            "confidence": match.confidence,
            "source": "template",
        }

    def lookup_semantic(
        self,
        error_message: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Look up pattern fixes using semantic search.

        This finds similar patterns even if they don't match exactly.

        Args:
            error_message: The error message
            limit: Max results to return

        Returns:
            List of matching patterns with similarity scores

        """
        if not self._cks:
            return []

        try:
            # Use semantic search for similar patterns
            results = self._cks.search_semantic(
                query=error_message,
                entry_type=self.ENTRY_TYPE,
                limit=limit,
            )

            matches = []
            for result in results:
                metadata = result.get("metadata", {})
                matches.append(
                    {
                        "pattern_name": metadata.get("pattern_name", "unknown"),
                        "error_type": metadata.get("error_type", "unknown"),
                        "fix_description": metadata.get("fix_description", ""),
                        "similarity": result.get("similarity", 0),
                        "applied_count": metadata.get("applied_count", 0),
                        "verified": metadata.get("verified", False),
                        "source": "cks_semantic",
                    }
                )

            return matches

        except Exception as e:
            logger.exception("Semantic lookup failed: %s", e)
            return []

    def get_stats(self) -> dict[str, Any]:
        """Get registry statistics."""
        if not self._cks:
            return {"cks_available": False, "total_patterns": 0}

        try:
            stats = self._cks.get_statistics()
            return {
                "cks_available": True,
                "total_patterns": stats.get("by_type", {}).get(self.ENTRY_TYPE, 0),
            }
        except Exception as e:
            logger.exception("Failed to get stats: %s", e)
            return {"cks_available": True, "total_patterns": 0}


# Singleton instance
_default_cks_registry: CKSPatternRegistry | None = None


def get_cks_pattern_registry() -> CKSPatternRegistry:
    """Get the default CKS pattern registry instance."""
    global _default_cks_registry
    if _default_cks_registry is None:  # type: ignore[truthy-operand]
        _default_cks_registry = CKSPatternRegistry()  # type: ignore[truthy-operand]
    return _default_cks_registry  # type: ignore[truthy-operand]


# Convenience functions
def register_cks_pattern_fix(
    error_message: str,
    fix_description: str,
    fix_template: str = "",
    location: str = "",
    verified: bool = False,
) -> bool:
    """
    Register a pattern fix using CKS backend.

    Args:
        error_message: The error message
        fix_description: What fix to apply
        fix_template: Template for generating fix
        location: Where this was applied
        verified: Whether the fix was verified

    Returns:
        True if saved successfully

    """
    registry = get_cks_pattern_registry()
    return registry.register_fix(
        error_message,
        fix_description,
        fix_template=fix_template,
        location=location,
        verified=verified,
    )


def lookup_cks_pattern_fix(
    error_message: str,
) -> dict[str, Any] | None:
    """
    Look up a pattern fix using CKS backend.

    Args:
        error_message: The error message

    Returns:
        Dictionary with pattern match info or None

    """
    registry = get_cks_pattern_registry()
    return registry.lookup(error_message)


# CLI test function
def _test() -> None:
    """Run built-in tests."""
    print("CKS Pattern Registry Tests")
    print("=" * 60)

    if not CKS_AVAILABLE:
        print("CKS not available - skipping tests")
        return

    registry = CKSPatternRegistry()

    # Test 1: Register a pattern fix
    error1 = "AttributeError: 'NoneType' object has no attribute '__getitem__'"
    print("Test 1 - Register pattern fix:")
    success = registry.register_fix(
        error1,
        "Use dict.get(key, default) or check if dict is None",
        location="download_handler.py:127",
        verified=True,
    )
    print(f"  Registered: {success}")

    # Test 2: Lookup pattern fix
    error2 = """
Traceback:
  File "batch_downloader.py", line 85
    videos = channel["videos"]
KeyError: 'videos'
"""
    match = registry.lookup(error2)
    print("Test 2 - Pattern lookup:")
    print(f"  Match found: {match is not None}")
    if match:
        print(f"  Pattern: {match.get('pattern_name')}")
        print(f"  Fix: {match.get('fix_description')}")
        print(f"  Source: {match.get('source')}")

    # Test 3: Semantic lookup
    print("Test 3 - Semantic lookup:")
    semantic_results = registry.lookup_semantic("null dict access error")
    print(f"  Semantic results: {len(semantic_results)}")
    for r in semantic_results[:3]:
        print(f"    - {r.get('pattern_name')}: {r.get('similarity', 0):.2f}")

    # Test 4: Stats
    print("Test 4 - Stats:")
    stats = registry.get_stats()
    print(f"  CKS available: {stats.get('cks_available')}")
    print(f"  Total patterns: {stats.get('total_patterns')}")

    print()


if __name__ == "__main__":
    _test()
