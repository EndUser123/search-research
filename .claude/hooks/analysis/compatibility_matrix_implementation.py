"""
Compatibility Matrix Implementation for 3D Cognitive Combinations

This module provides the schema and helper functions for managing the compatibility
matrix that stores validated framework + mode + profile combinations.

Integration: Add this code to UserPromptSubmit_modules/unified_detection.py
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Required, TypedDict

# =============================================================================
# SCHEMA DEFINITIONS
# =============================================================================

class CompatibilityMatrixEntry(TypedDict, total=False):
    """Schema for compatibility matrix entry.

    Required Fields:
        combination: (framework, mode, profile) tuple - unique identifier
        enhancement: Specialized enhancement name (lowercase_with_underscores)
        evidence_source: Where validated (cks_memory, user_correction, testing)
        creation_date: ISO 8601 timestamp when entry was added

    Optional Fields:
        usage_count: How often triggered (default: 0)
        last_used: ISO timestamp of most recent use (default: None)
        rationale: Why this combination works (default: "")
    """
    combination: Required[tuple[str, str, str]]
    enhancement: Required[str]
    evidence_source: Required[str]
    creation_date: Required[str]
    usage_count: int
    last_used: str | None
    rationale: str


@dataclass(frozen=True)
class CompatibilityMatrixMetadata:
    """Metadata for compatibility matrix version tracking."""
    version: str
    schema_version: str = "1.0"
    last_updated: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    total_entries: int = 0
    maintenance_target: int = 50  # Target max entries for O(1) lookup


# =============================================================================
# MATRIX STORAGE
# =============================================================================

# State file path for persistent storage
_MATRIX_STATE_PATH = Path(__file__).parent.parent / "state" / "compatibility_matrix.json"


def load_matrix_from_disk() -> dict[
    tuple[str, str, str],
    CompatibilityMatrixEntry
] | None:
    """Load compatibility matrix from JSON state file.

    Returns:
        Matrix dictionary, or None if file doesn't exist or is invalid
    """
    try:
        if _MATRIX_STATE_PATH.exists():
            with open(_MATRIX_STATE_PATH, encoding='utf-8') as f:
                data = json.load(f)

            # Convert JSON list combinations back to tuples
            matrix = {}
            for entry_data in data.get("entries", []):
                combination = tuple(entry_data["combination"])  # type: ignore[assignment]
                entry: CompatibilityMatrixEntry = {
                    "combination": combination,
                    "enhancement": entry_data["enhancement"],
                    "evidence_source": entry_data["evidence_source"],
                    "creation_date": entry_data["creation_date"],
                    "usage_count": entry_data.get("usage_count", 0),
                    "last_used": entry_data.get("last_used"),
                    "rationale": entry_data.get("rationale", ""),
                }
                matrix[combination] = entry

            return matrix
    except (OSError, json.JSONDecodeError, KeyError, ValueError):
        # Graceful degradation on file system or JSON errors
        pass
    return None


def save_matrix_to_disk(
    matrix: dict[tuple[str, str, str], CompatibilityMatrixEntry],
    metadata: CompatibilityMatrixMetadata
) -> bool:
    """Save compatibility matrix to JSON state file.

    Args:
        matrix: Current compatibility matrix
        metadata: Matrix metadata (version, last_updated, etc.)

    Returns:
        True if save succeeded, False otherwise
    """
    try:
        # Ensure parent directory exists
        _MATRIX_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)

        # Convert matrix to JSON-serializable format
        entries = []
        for combination, entry in matrix.items():
            entry_data = {
                "combination": list(combination),  # Convert tuple to list for JSON
                "enhancement": entry["enhancement"],
                "evidence_source": entry["evidence_source"],
                "creation_date": entry["creation_date"],
                "usage_count": entry.get("usage_count", 0),
                "last_used": entry.get("last_used"),
                "rationale": entry.get("rationale", ""),
            }
            entries.append(entry_data)

        # Build JSON structure
        data = {
            "metadata": {
                "version": metadata.version,
                "schema_version": metadata.schema_version,
                "last_updated": metadata.last_updated,
                "total_entries": len(matrix),
                "maintenance_target": metadata.maintenance_target,
            },
            "entries": entries,
        }

        # Write to file atomically
        temp_path = _MATRIX_STATE_PATH.with_suffix('.tmp')
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Atomic rename (Windows-safe)
        temp_path.replace(_MATRIX_STATE_PATH)

        return True
    except (OSError, json.JSONEncodeError, RuntimeError):
        # Graceful degradation on file system or JSON errors
        return False


# =============================================================================
# USAGE TRACKING
# =============================================================================

def track_combination_usage(
    combination: tuple[str, str, str],
    matrix: dict[tuple[str, str, str], CompatibilityMatrixEntry],
    save_immediately: bool = False
) -> bool:
    """Update usage count and last_used timestamp for a combination.

    Args:
        combination: The (framework, mode, profile) tuple to track
        matrix: Current compatibility matrix
        save_immediately: If True, save to disk after update (default: False)

    Returns:
        True if update succeeded, False otherwise
    """
    try:
        if combination in matrix:
            entry = matrix[combination]
            entry["usage_count"] = entry.get("usage_count", 0) + 1
            entry["last_used"] = datetime.now(UTC).isoformat()

            # Optionally save immediately (for critical analytics)
            if save_immediately:
                metadata = CompatibilityMatrixMetadata(version="1.0.0")
                return save_matrix_to_disk(matrix, metadata)

            return True
    except (KeyError, RuntimeError):
        # Graceful degradation on errors
        pass
    return False


# =============================================================================
# VALIDATION
# =============================================================================

def validate_matrix_entry(
    entry: CompatibilityMatrixEntry,
    valid_frameworks: set[str],
    valid_modes: set[str],
    valid_profiles: set[str]
) -> tuple[bool, str | None]:
    """Validate a single matrix entry.

    Args:
        entry: Entry to validate
        valid_frameworks: Set of valid framework names
        valid_modes: Set of valid mode names
        valid_profiles: Set of valid profile names

    Returns:
        (is_valid, error_message) tuple
    """
    combination = entry["combination"]
    framework, mode, profile = combination

    # Validate framework name
    if framework not in valid_frameworks:
        return False, f"Invalid framework: {framework}"

    # Validate mode name
    if mode not in valid_modes:
        return False, f"Invalid mode: {mode}"

    # Validate profile name
    if profile not in valid_profiles:
        return False, f"Invalid profile: {profile}"

    # Validate enhancement naming (lowercase_with_underscores)
    enhancement = entry["enhancement"]
    if not enhancement.islower() or not enhancement.replace('_', '').isalnum():
        return False, f"Invalid enhancement name: {enhancement}"

    # Validate ISO dates
    try:
        datetime.fromisoformat(entry["creation_date"].replace('Z', '+00:00'))
        if entry.get("last_used"):
            datetime.fromisoformat(entry["last_used"].replace('Z', '+00:00'))
    except ValueError:
        return False, "Invalid ISO date format"

    return True, None


def validate_matrix(
    matrix: dict[tuple[str, str, str], CompatibilityMatrixEntry],
    valid_frameworks: set[str],
    valid_modes: set[str],
    valid_profiles: set[str]
) -> None:
    """Validate entire compatibility matrix.

    Raises:
        ValueError: If validation fails (with detailed error message)
    """
    # Check for duplicate keys
    if len(matrix) != len(set(matrix.keys())):
        duplicates = [k for k in matrix.keys() if list(matrix.keys()).count(k) > 1]
        raise ValueError(
            f"Duplicate keys in matrix: {duplicates}\n"
            f"Each (framework, mode, profile) combination must be unique."
        )

    # Validate each entry
    for combination, entry in matrix.items():
        is_valid, error_msg = validate_matrix_entry(
            entry, valid_frameworks, valid_modes, valid_profiles
        )
        if not is_valid:
            raise ValueError(
                f"Invalid entry {combination}: {error_msg}\n"
                f"Entry: {entry}"
            )


# =============================================================================
# EXAMPLE USAGE (for integration into unified_detection.py)
# =============================================================================

"""
# In unified_detection.py, add this after the existing _COMPATIBILITY_MATRIX definition:

# Load matrix from disk on module import
_LOADED_MATRIX = load_matrix_from_disk()
if _LOADED_MATRIX is not None:
    # Merge loaded matrix with hardcoded matrix (loaded takes precedence)
    _COMPATIBILITY_MATRIX.update(_LOADED_MATRIX)

# Validate matrix at module load time
def _validate_compatibility_matrix() -> None:
    # ... existing validation code ...

# In _detect_3d_compatibility(), add usage tracking:
def _detect_3d_compatibility(...) -> list[dict[str, str]]:
    compatible_combinations = []

    for (framework, mode, profile), entry in _COMPATIBILITY_MATRIX.items():
        if (framework in framework_set and
            mode in mode_set and
            profile in profile_set):
            compatible_combinations.append({
                "framework": framework,
                "mode": mode,
                "profile": profile,
                "enhancement": entry["enhancement"],
                "rationale": entry.get("rationale", ""),
            })

            # Track usage (non-blocking, async-ideal)
            track_combination_usage((framework, mode, profile), _COMPATIBILITY_MATRIX)

    return compatible_combinations
"""

# =============================================================================
# MATRIX CREATION HELPER (for new entries)
# =============================================================================

def create_matrix_entry(
    framework: str,
    mode: str,
    profile: str,
    enhancement: str,
    evidence_source: str,
    rationale: str = ""
) -> CompatibilityMatrixEntry:
    """Create a new compatibility matrix entry with required fields.

    Args:
        framework: Cognitive framework name
        mode: Reasoning mode name
        profile: Think profile name
        enhancement: Specialized enhancement name (lowercase_with_underscores)
        evidence_source: Where this combination was validated
        rationale: Why this combination works (optional)

    Returns:
        Complete CompatibilityMatrixEntry with current timestamp

    Example:
        entry = create_matrix_entry(
            framework="assumption_surfacing",
            mode="multi_agent",
            profile="architecture",
            enhancement="parallel_assumption_checking",
            evidence_source="cks_memory_20260314",
            rationale="Multi-agent prevents blind spots in architecture design"
        )
        _COMPATIBILITY_MATRIX[(framework, mode, profile)] = entry
    """
    return CompatibilityMatrixEntry(
        combination=(framework, mode, profile),
        enhancement=enhancement,
        evidence_source=evidence_source,
        creation_date=datetime.now(UTC).isoformat(),
        usage_count=0,
        last_used=None,
        rationale=rationale,
    )


# =============================================================================
# ANALYTICS QUERIES (for performance monitoring)
# =============================================================================

def get_matrix_statistics(
    matrix: dict[tuple[str, str, str], CompatibilityMatrixEntry]
) -> dict[str, any]:
    """Get statistics about compatibility matrix usage.

    Returns:
        Dictionary with matrix statistics:
        - total_entries: Total number of combinations
        - total_usage_count: Sum of all usage counts
        - most_used_combinations: Top 5 most-used combinations
        - least_used_combinations: Bottom 5 least-used combinations
        - orphan_entries: Entries never used (usage_count = 0)
    """
    entries = list(matrix.values())

    total_usage = sum(e.get("usage_count", 0) for e in entries)

    # Sort by usage count
    sorted_entries = sorted(
        entries,
        key=lambda e: e.get("usage_count", 0),
        reverse=True
    )

    most_used = [
        {
            "combination": e["combination"],
            "enhancement": e["enhancement"],
            "usage_count": e.get("usage_count", 0),
            "last_used": e.get("last_used"),
        }
        for e in sorted_entries[:5]
    ]

    least_used = [
        {
            "combination": e["combination"],
            "enhancement": e["enhancement"],
            "usage_count": e.get("usage_count", 0),
            "creation_date": e["creation_date"],
        }
        for e in sorted_entries[-5:]
    ]

    orphan_entries = [
        {
            "combination": e["combination"],
            "enhancement": e["enhancement"],
            "creation_date": e["creation_date"],
        }
        for e in entries
        if e.get("usage_count", 0) == 0
    ]

    return {
        "total_entries": len(matrix),
        "total_usage_count": total_usage,
        "most_used_combinations": most_used,
        "least_used_combinations": least_used,
        "orphan_entries": orphan_entries,
    }
