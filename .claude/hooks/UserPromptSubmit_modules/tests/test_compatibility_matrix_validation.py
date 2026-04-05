"""Test compatibility matrix validation (T-002)."""

import re
import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from unified_detection import (
    _COGNITIVE_FRAMEWORKS,
    _COMPATIBILITY_MATRIX,
    _REASONING_MODES,
    _THINK_PROFILES,
)


def test_compatibility_matrix_structure():
    """Test that compatibility matrix has correct structure."""
    # Should be a dict
    assert isinstance(_COMPATIBILITY_MATRIX, dict)

    # Should have entries
    assert len(_COMPATIBILITY_MATRIX) > 0

    # All keys should be 3-tuples
    for key in _COMPATIBILITY_MATRIX.keys():
        assert isinstance(key, tuple), f"Key {key} is not a tuple"
        assert len(key) == 3, f"Key {key} does not have 3 elements"


def test_compatibility_matrix_no_duplicate_keys():
    """Test that there are no duplicate keys in the matrix."""
    keys = list(_COMPATIBILITY_MATRIX.keys())
    unique_keys = set(keys)

    duplicates = [k for k in keys if keys.count(k) > 1]

    assert len(duplicates) == 0, f"Duplicate keys found: {duplicates}"


def test_compatibility_matrix_valid_frameworks():
    """Test that all framework names in matrix are valid."""
    valid_frameworks = set(_COGNITIVE_FRAMEWORKS.keys())
    invalid_frameworks = {
        fw for (fw, _, _) in _COMPATIBILITY_MATRIX.keys()
        if fw not in valid_frameworks
    }

    assert len(invalid_frameworks) == 0, (
        f"Invalid framework names: {invalid_frameworks}. "
        f"Valid frameworks: {sorted(valid_frameworks)}"
    )


def test_compatibility_matrix_valid_modes():
    """Test that all mode names in matrix are valid."""
    valid_modes = set(_REASONING_MODES.keys())
    invalid_modes = {
        mode for (_, mode, _) in _COMPATIBILITY_MATRIX.keys()
        if mode not in valid_modes
    }

    assert len(invalid_modes) == 0, (
        f"Invalid mode names: {invalid_modes}. "
        f"Valid modes: {sorted(valid_modes)}"
    )


def test_compatibility_matrix_valid_profiles():
    """Test that all profile names in matrix are valid."""
    valid_profiles = set(_THINK_PROFILES.keys())
    invalid_profiles = {
        profile for (_, _, profile) in _COMPATIBILITY_MATRIX.keys()
        if profile not in valid_profiles
    }

    assert len(invalid_profiles) == 0, (
        f"Invalid profile names: {invalid_profiles}. "
        f"Valid profiles: {sorted(valid_profiles)}"
    )


def test_compatibility_matrix_enhancement_names():
    """Test that enhancement names follow naming conventions."""
    enhancement_names = set(_COMPATIBILITY_MATRIX.values())

    # Enhancement names should be lowercase_with_underscores
    invalid_enhancements = {
        name for name in enhancement_names
        if not re.match(r'^[a-z][a-z0-9_]*$', name)
    }

    assert len(invalid_enhancements) == 0, (
        f"Invalid enhancement names: {invalid_enhancements}. "
        f"Names must be lowercase_with_underscores (e.g., 'parallel_assumption_checking')"
    )


def test_compatibility_matrix_high_value_combinations():
    """Test that high-value combinations from the plan are included."""
    # These are the key combinations from the plan
    high_value_combinations = [
        ("assumption_surfacing", "multi_agent", "architecture"),
        ("socratic_decomposition", "multi_agent", "tradeoff_decision"),
        ("outcome_anchoring", "two_stage", "pre_commit_risk"),
        ("chestertons_fence", "sequential", "debug_rca"),
        ("hanlons_razor", "sequential", "debug_rca"),
        ("inversion_prompting", "graph", "performance_analysis"),
        ("devils_advocate", "multi_agent", "security_review"),
        ("calibrated_confidence", "two_stage", "pre_commit_risk"),
    ]

    for combination in high_value_combinations:
        assert combination in _COMPATIBILITY_MATRIX, (
            f"High-value combination {combination} not found in matrix"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
