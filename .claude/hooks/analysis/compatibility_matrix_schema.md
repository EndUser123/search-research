# Compatibility Matrix Schema Definition

## Purpose

This document defines the schema for the **3D Compatibility Matrix** used in the Cognitive Steering Framework (CSF-COE) to store and validate optimal combinations of cognitive frameworks, reasoning modes, and think profiles.

## Data Structure

### Python Type Definitions

```python
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Required, TypedDict
import json
from datetime import datetime, UTC
from pathlib import Path

class CompatibilityMatrixEntry(TypedDict, total=False):
    """Schema for a single compatibility matrix entry.

    Represents a validated, high-value combination of cognitive framework +
    reasoning mode + think profile that has been tested and documented.

    Required Fields:
        combination: The (framework, mode, profile) tuple that uniquely identifies this entry
        enhancement: Specialized enhancement name for this combination
        evidence_source: Where this combination was discovered/validated
        creation_date: When this entry was added to the matrix

    Optional Fields:
        usage_count: How often this combination has been triggered (default: 0)
        last_used: ISO timestamp of most recent use (default: None)
        rationale: Why this combination works well (human-readable explanation)
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
    """Metadata for the entire compatibility matrix.

    Provides version tracking and matrix evolution support.
    """
    version: str
    schema_version: str = "1.0"
    last_updated: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    total_entries: int = 0
    maintenance_target: int = 50  # Target max entries to maintain O(1) lookup


# Main matrix structure
_COMPATIBILITY_MATRIX: dict[
    tuple[str, str, str],  # (framework, mode, profile) - O(1) lookup key
    CompatibilityMatrixEntry
] = {}
```

## Metadata Fields

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `combination` | `tuple[str, str, str]` | (framework, mode, profile) unique identifier | `("assumption_surfacing", "multi_agent", "architecture")` |
| `enhancement` | `str` | Specialized enhancement name (lowercase_with_underscores) | `"parallel_assumption_checking"` |
| `evidence_source` | `str` | Where this combination was discovered/validated | `"cks_memory_20260314"`, `"user_correction"`, `"testing_validation"` |
| `creation_date` | `str` | ISO 8601 timestamp when entry was added | `"2026-03-15T10:30:00Z"` |

### Optional Fields

| Field | Type | Description | Default | Example |
|-------|------|-------------|---------|---------|
| `usage_count` | `int` | How often this combination has been triggered | `0` | `42` |
| `last_used` | `str \| None` | ISO 8601 timestamp of most recent use | `None` | `"2026-03-15T14:25:00Z"` |
| `rationale` | `str` | Human-readable explanation of why this combination works | `""` | `"Multi-agent prevents blind spots, architecture profile provides structure"` |

## JSON Template for New Entries

### Template Structure

```json
{
  "metadata": {
    "version": "1.0.0",
    "schema_version": "1.0",
    "last_updated": "2026-03-15T10:30:00Z",
    "total_entries": 1,
    "maintenance_target": 50
  },
  "entries": [
    {
      "combination": ["framework_name", "mode_name", "profile_name"],
      "enhancement": "specialized_enhancement_name",
      "evidence_source": "cks_memory_20260314",
      "creation_date": "2026-03-15T10:30:00Z",
      "usage_count": 0,
      "last_used": null,
      "rationale": "Human-readable explanation of why this combination works well"
    }
  ]
}
```

### Example: Complex Architecture Design

```json
{
  "combination": ["assumption_surfacing", "multi_agent", "architecture"],
  "enhancement": "parallel_assumption_checking",
  "evidence_source": "cks_memory_20260314",
  "creation_date": "2026-03-15T10:30:00Z",
  "usage_count": 15,
  "last_used": "2026-03-15T14:25:00Z",
  "rationale": "Multi-agent perspective prevents blind spots in architecture design, while assumption surfacing ensures unstated constraints are made explicit before implementation begins"
}
```

### Example: Root Cause Analysis

```json
{
  "combination": ["chestertons_fence", "sequential", "debug_rca"],
  "enhancement": "legacy_reasoning_validation",
  "evidence_source": "testing_validation",
  "creation_date": "2026-03-15T11:00:00Z",
  "usage_count": 8,
  "last_used": "2026-03-15T12:30:00Z",
  "rationale": "Sequential reasoning follows causal chain systematically, Chesterton's Fence ensures existing code logic is understood before modification, preventing regression bugs"
}
```

## Performance Characteristics

### Lookup Performance

| Operation | Complexity | Performance | Notes |
|-----------|-----------|-------------|-------|
| **Entry lookup** | O(1) | <1ms | Dictionary key access |
| **Combination validation** | O(n) | <2ms | Iterate over matched frameworks × modes × profiles (small n) |
| **Matrix update** | O(1) | <1ms | Dictionary insertion |
| **Usage tracking** | O(1) | <1ms | Increment counter |
| **Total overhead** | - | <5ms | Including detection + validation + update |

### Memory Footprint

| Component | Memory | Notes |
|-----------|--------|-------|
| **Per entry** | ~100 bytes | Dictionary entry + TypedDict + metadata |
| **50 entries (target)** | ~5 KB | Maintenance target for matrix size |
| **100 entries (max)** | ~10 KB | Absolute upper bound |

### Validation Performance

```python
# Matrix validation at module load time
def _validate_compatibility_matrix() -> None:
    """Validate matrix for duplicates and invalid entries.

    Performance: <10ms at module load (one-time cost)
    """
    # Check duplicate keys: O(n) where n = matrix size
    # Validate framework names: O(n) set lookup
    # Validate mode names: O(n) set lookup
    # Validate profile names: O(n) set lookup
    # Validate enhancement naming: O(n) regex check
    # Total: <10ms for n=50 entries
```

## Version Tracking and Evolution

### Matrix Versioning

```python
@dataclass(frozen=True)
class CompatibilityMatrixMetadata:
    """Metadata for matrix evolution tracking."""
    version: str                    # Matrix version (e.g., "1.0.0")
    schema_version: str = "1.0"     # Schema version (increment on breaking changes)
    last_updated: str = ...         # ISO timestamp of last update
    total_entries: int = 0          # Current entry count
    maintenance_target: int = 50    # Target max entries
```

### Version Increment Rules

| Change Type | Version Increment | Example |
|-------------|-------------------|---------|
| **New entry added** | Patch version (third digit) | `1.0.0` → `1.0.1` |
| **Entry removed** | Patch version (third digit) | `1.0.1` → `1.0.2` |
| **Schema structure change** | Schema version increment | `schema: "1.0"` → `schema: "2.0"` |
| **Validation rules change** | Minor version (second digit) | `1.0.2` → `1.1.0` |
| **Breaking API change** | Major version (first digit) | `1.1.0` → `2.0.0` |

### Migration Path

```python
def migrate_matrix_schema(
    old_matrix: dict,
    old_schema_version: str,
    new_schema_version: str
) -> dict:
    """Migrate matrix from old schema to new schema.

    Example migration: Add new required field 'rationale'
    """
    if old_schema_version == "1.0" and new_schema_version == "1.1":
        # Add 'rationale' field with default value
        for entry in old_matrix.values():
            if "rationale" not in entry:
                entry["rationale"] = ""
        return old_matrix
    else:
        raise ValueError(f"Unsupported migration: {old_schema_version} → {new_schema_version}")
```

## Usage Tracking and Analytics

### Tracking Usage

```python
def track_combination_usage(
    combination: tuple[str, str, str],
    matrix: dict[tuple[str, str, str], CompatibilityMatrixEntry]
) -> None:
    """Update usage count and last_used timestamp for a combination."""
    if combination in matrix:
        entry = matrix[combination]
        entry["usage_count"] = entry.get("usage_count", 0) + 1
        entry["last_used"] = datetime.now(UTC).isoformat()
```

### Analytics Queries

```sql
-- Most frequently used combinations
SELECT
    json_extract(combination, '$[0]') as framework,
    json_extract(combination, '$[1]') as mode,
    json_extract(combination, '$[2]') as profile,
    usage_count,
    last_used
FROM compatibility_matrix
ORDER BY usage_count DESC
LIMIT 10;

-- Combinations not used in last 30 days (cleanup candidates)
SELECT
    combination,
    enhancement,
    usage_count,
    last_used
FROM compatibility_matrix
WHERE date(last_used) < date('now', '-30 days')
ORDER BY usage_count ASC;
```

## Maintenance Guidelines

### Target Matrix Size

**Target**: 50 entries maximum
**Rationale**: Maintains O(1) lookup performance and manageable cognitive load for manual review

### Entry Addition Criteria

Add new entries when:
1. **High-value use case identified**: Solves a specific problem better than existing combinations
2. **Evidence-based validation**: Backed by CKS memory, user correction, or testing validation
3. **Unique combination**: Not already covered by existing entry
4. **Measurable benefit**: Quantifiable improvement (e.g., +15% design quality, -40% resolution time)

### Entry Removal Criteria

Remove entries when:
1. **Low usage**: <5 uses in 30 days AND not high-value combo
2. **Redundant**: Covered by another entry with better performance
3. **Obsolete**: Framework/mode/profile no longer exists or is deprecated
4. **Poor performance**: User satisfaction score <3.0/5.0

### Review Schedule

- **Weekly**: Review usage analytics, identify low-usage entries
- **Monthly**: Comprehensive matrix review, add/remove based on evidence
- **Quarterly**: Schema version review, breaking changes evaluation

## Integration with Unified Detection

### Matrix Lookup Flow

```python
def _detect_3d_compatibility(
    matched_frameworks: set[str],
    matched_modes: set[str],
    matched_profiles: set[str],
) -> list[dict[str, str]]:
    """Detect 3D compatibility combinations using the matrix.

    Uses O(1) dictionary lookups for <5ms performance.
    """
    compatible_combinations = []

    for (framework, mode, profile), entry in _COMPATIBILITY_MATRIX.items():
        if (framework in matched_frameworks and
            mode in matched_modes and
            profile in matched_profiles):
            compatible_combinations.append({
                "framework": framework,
                "mode": mode,
                "profile": profile,
                "enhancement": entry["enhancement"],
                "rationale": entry.get("rationale", ""),
            })

            # Track usage (async, non-blocking)
            _track_usage_async((framework, mode, profile))

    return compatible_combinations
```

## File Storage Format

### JSON Storage Location

```
P:/.claude/hooks/state/compatibility_matrix.json
```

### JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Compatibility Matrix",
  "description": "Validated combinations of cognitive frameworks, reasoning modes, and think profiles",
  "type": "object",
  "required": ["metadata", "entries"],
  "properties": {
    "metadata": {
      "type": "object",
      "required": ["version", "schema_version", "last_updated"],
      "properties": {
        "version": {"type": "string"},
        "schema_version": {"type": "string"},
        "last_updated": {"type": "string", "format": "date-time"},
        "total_entries": {"type": "integer"},
        "maintenance_target": {"type": "integer"}
      }
    },
    "entries": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["combination", "enhancement", "evidence_source", "creation_date"],
        "properties": {
          "combination": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 3,
            "maxItems": 3
          },
          "enhancement": {"type": "string"},
          "evidence_source": {"type": "string"},
          "creation_date": {"type": "string", "format": "date-time"},
          "usage_count": {"type": "integer", "minimum": 0},
          "last_used": {"type": "string", "format": "date-time"},
          "rationale": {"type": "string"}
        }
      }
    }
  }
}
```

## See Also

- `UserPromptSubmit_modules/unified_detection.py` - Matrix implementation
- `UserPromptSubmit_modules/cognitive_enhancers.py` - Matrix consumer
- `plans/plan-20260314-cognitive-reasoning-optimization.md` - Architecture overview
- `state/performance.db` - Usage analytics storage

**Schema Version**: 1.0
**Last Updated**: 2026-03-15
**Document Version**: 1.0.0
