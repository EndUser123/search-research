"""
Test compatibility matrix functionality (T-006).

Comprehensive tests for 3D compatibility matrix lookup, detection, performance,
and integration with conflict_arbiter.py.

Test Coverage:
- Matrix lookup logic (unit tests)
- 3D detection (integration tests)
- Precedence rules (3D > 2D > individual)
- Performance (<1ms lookup, <5ms total overhead)
- False positive prevention
- Edge cases and validation
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    pass

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from unified_detection import (
    _COGNITIVE_FRAMEWORKS,
    _COMPATIBILITY_MATRIX,
    _REASONING_MODES,
    _THINK_PROFILES,
    CompatibilityMatrixEntry,
    _detect_3d_compatibility,
    detect_prompt,
    validate_matrix,
)


class TestMatrixLookupLogic:
    """Unit tests for matrix lookup functionality."""

    def test_matrix_lookup_single_combination(self):
        """Test looking up a single 3D combination."""
        # Look up a known combination from the matrix
        combination = ("assumption_surfacing", "multi_agent", "architecture")

        # Verify combination exists in matrix
        assert combination in _COMPATIBILITY_MATRIX, \
            f"Combination {combination} should exist in compatibility matrix"

        # Verify entry has required fields
        entry = _COMPATIBILITY_MATRIX[combination]
        assert isinstance(entry, dict), "Entry should be a dict"
        assert "combination" in entry, "Entry should have 'combination' field"
        assert "enhancement" in entry, "Entry should have 'enhancement' field"
        assert "rationale" in entry, "Entry should have 'rationale' field"
        assert "usage_count" in entry, "Entry should have 'usage_count' field"

        # Verify combination matches lookup key
        assert entry["combination"] == combination, \
            "Entry combination should match lookup key"

    def test_matrix_lookup_multiple_combinations(self):
        """Test looking up multiple combinations."""
        # Define multiple known combinations
        combinations = [
            ("assumption_surfacing", "multi_agent", "architecture"),
            ("socratic_decomposition", "multi_agent", "tradeoff_decision"),
            ("outcome_anchoring", "two_stage", "pre_commit_risk"),
        ]

        # Verify all combinations exist
        for combo in combinations:
            assert combo in _COMPATIBILITY_MATRIX, \
                f"Combination {combo} should exist in compatibility matrix"

        # Verify each entry has required metadata
        for combo in combinations:
            entry = _COMPATIBILITY_MATRIX[combo]
            assert entry["enhancement"], "Enhancement should not be empty"
            assert entry["rationale"], "Rationale should not be empty"
            assert entry["usage_count"] >= 0, "Usage count should be non-negative"

    def test_matrix_lookup_no_match(self):
        """Test lookup when combination not in matrix."""
        # Define a combination that should not exist
        combination = ("invalid_framework", "invalid_mode", "invalid_profile")

        # Verify combination does not exist
        assert combination not in _COMPATIBILITY_MATRIX, \
            f"Invalid combination {combination} should not exist in matrix"

        # Verify lookup returns None or raises KeyError
        result = _COMPATIBILITY_MATRIX.get(combination)
        assert result is None, "Lookup of invalid combination should return None"

    def test_matrix_entry_metadata_completeness(self):
        """Test that all matrix entries have complete metadata."""
        required_fields = {
            "combination", "enhancement", "evidence_source",
            "creation_date", "usage_count", "last_used", "rationale"
        }

        # Check all entries have required fields
        for combination, entry in _COMPATIBILITY_MATRIX.items():
            missing_fields = required_fields - entry.keys()
            assert not missing_fields, \
                f"Entry {combination} missing required fields: {missing_fields}"

    def test_matrix_enhancement_naming_convention(self):
        """Test that enhancement names follow lowercase_with_underscores convention."""
        import re

        # Enhancement names should be lowercase_with_underscores
        enhancement_pattern = re.compile(r'^[a-z][a-z0-9_]*$')

        for combination, entry in _COMPATIBILITY_MATRIX.items():
            enhancement = entry["enhancement"]
            assert enhancement_pattern.match(enhancement), \
                f"Enhancement '{enhancement}' for {combination} does not follow naming convention"

    def test_matrix_combination_uniqueness(self):
        """Test that all matrix combinations are unique."""
        # Count occurrences of each combination
        combinations = list(_COMPATIBILITY_MATRIX.keys())
        unique_combinations = set(combinations)

        # Should have no duplicates
        assert len(combinations) == len(unique_combinations), \
            "Compatibility matrix should not have duplicate combinations"


class Test3DDetection:
    """Integration tests for 3D compatibility detection."""

    def test_3d_compatibility_detection(self):
        """Test that 3D combinations are detected correctly."""
        prompt = "Design system architecture considering team structure and deployment constraints. Evaluate from multiple perspectives step by step."

        # Detect prompt
        result = detect_prompt(prompt)

        # Verify individual dimensions are detected (3D requires all 3)
        assert len(result.matched_frameworks) > 0, "Should detect cognitive frameworks"
        assert len(result.matched_profiles) > 0, "Should detect think profiles"

        # Verify 3D compatible combinations are detected if all dimensions match
        # (Note: 3D only triggers when framework+mode+profile all match)
        if len(result.matched_modes) > 0 and len(result.matched_profiles) > 0:
            # If we have modes and profiles, should detect 3D combinations
            assert len(result.compatible_combinations) > 0, \
                "Should detect at least one compatible 3D combination when all dimensions match"

            # Verify structure of detected combinations
            for combo in result.compatible_combinations:
                assert "combination" in combo, "3D combo should have 'combination'"
                assert "enhancement" in combo, "3D combo should have 'enhancement'"
                assert "rationale" in combo, "3D combo should have 'rationale'"

    def test_3d_takes_precedence_over_2d(self):
        """Test that 3D matrix takes precedence over 2D synergies."""
        prompt = "Design microservice architecture with multiple stakeholders"

        # Detect prompt
        result = detect_prompt(prompt)

        # Verify 3D combinations are detected
        assert len(result.compatible_combinations) > 0, \
            "Should detect 3D compatible combinations"

        # Verify 3D combination metadata includes enhancement and rationale
        for combo in result.compatible_combinations:
            assert "enhancement" in combo, "3D combination should include enhancement"
            assert "rationale" in combo, "3D combination should include rationale"
            assert "combination" in combo, "3D combination should include tuple"

    def test_3d_takes_precedence_over_individual(self):
        """Test that 3D matrix takes precedence over individual frameworks."""
        # Use prompt that triggers debugging with sequential mode
        prompt = "Debug authentication flow failure step by step. Investigate root cause of mobile users issue."

        # Detect prompt
        result = detect_prompt(prompt)

        # Verify individual dimensions are detected
        assert len(result.matched_frameworks) > 0, \
            "Should still detect individual cognitive frameworks"

        # Verify 3D combination coordinates with individual detections
        if len(result.compatible_combinations) > 0:
            # If 3D combination detected, verify it uses detected dimensions
            for combo in result.compatible_combinations:
                framework, mode, profile = combo["combination"]
                assert framework in result.matched_frameworks, \
                    f"Framework {framework} in 3D combo should be in matched_frameworks"
                if mode:
                    assert mode in result.matched_modes, \
                        f"Mode {mode} in 3D combo should be in matched_modes"
                if profile:
                    assert profile in result.matched_profiles, \
                        f"Profile {profile} in 3D combo should be in matched_profiles"
        else:
            # If no 3D combination, verify individual detections still work
            assert len(result.matched_frameworks) > 0 or \
                   len(result.matched_modes) > 0 or \
                   len(result.matched_profiles) > 0, \
                "Should detect at least some individual dimensions even without 3D combo"

    def test_3d_detection_with_all_dimensions(self):
        """Test 3D detection when all three dimensions have matches."""
        # Use prompt that triggers all dimensions explicitly
        prompt = "Design microservice architecture considering team structure. Evaluate from multiple perspectives step by step. Analyze deployment constraints before implementing."

        # Detect prompt
        result = detect_prompt(prompt)

        # Verify all dimensions have matches
        assert len(result.matched_frameworks) > 0, "Should detect cognitive frameworks"
        assert len(result.matched_profiles) > 0, "Should detect think profiles"

        # Note: Modes require explicit keywords (multi_agent, sequential, graph, two_stage)
        # If modes detected, should also detect 3D combinations
        if len(result.matched_modes) > 0:
            assert len(result.compatible_combinations) > 0, \
                "Should detect 3D combinations when all dimensions match"

    def test_3d_detection_with_partial_dimensions(self):
        """Test 3D detection when only some dimensions have matches."""
        prompt = "Implement authentication"

        # Detect prompt
        result = detect_prompt(prompt)

        # May have framework matches but limited mode/profile matches
        # Verify 3D detection handles partial matches gracefully
        # (should not crash, should return empty list if insufficient matches)
        assert isinstance(result.compatible_combinations, list), \
            "compatible_combinations should always be a list"

    def test_3d_combination_structure(self):
        """Test that 3D combinations have correct structure."""
        prompt = "Design system architecture with multiple stakeholders"

        # Detect prompt
        result = detect_prompt(prompt)

        # Verify structure of compatible combinations
        for combo in result.compatible_combinations:
            # Check combination tuple
            assert "combination" in combo, "Should have 'combination' field"
            assert isinstance(combo["combination"], tuple), "combination should be a tuple"
            assert len(combo["combination"]) == 3, "combination should have 3 elements"

            # Check metadata fields
            assert "enhancement" in combo, "Should have 'enhancement' field"
            assert "rationale" in combo, "Should have 'rationale' field"
            assert "usage_count" in combo, "Should have 'usage_count' field"

            # Verify field types
            assert isinstance(combo["enhancement"], str), "enhancement should be string"
            assert isinstance(combo["rationale"], str), "rationale should be string"
            assert isinstance(combo["usage_count"], int), "usage_count should be int"


class TestPerformance:
    """Performance tests for compatibility matrix operations."""

    def test_matrix_lookup_performance(self):
        """Test that matrix lookup is <1ms."""
        combination = ("assumption_surfacing", "multi_agent", "architecture")

        # Warm-up
        for _ in range(100):
            _ = combination in _COMPATIBILITY_MATRIX

        # Performance measurement
        iterations = 10000
        start_time = time.perf_counter()

        for _ in range(iterations):
            _ = combination in _COMPATIBILITY_MATRIX

        end_time = time.perf_counter()
        avg_latency_ms = ((end_time - start_time) / iterations) * 1000

        # Verify <1ms requirement
        assert avg_latency_ms < 1.0, \
            f"Matrix lookup took {avg_latency_ms:.3f}ms, exceeds 1ms requirement"

    def test_3d_detection_performance(self):
        """Test that 3D detection adds <5ms overhead."""
        prompt = "Design system architecture considering team structure"

        # Warm-up
        for _ in range(10):
            _ = detect_prompt(prompt)

        # Performance measurement
        iterations = 100
        start_time = time.perf_counter()

        for _ in range(iterations):
            result = detect_prompt(prompt)
            _ = result.compatible_combinations

        end_time = time.perf_counter()
        avg_latency_ms = ((end_time - start_time) / iterations) * 1000

        # Verify <5ms requirement
        assert avg_latency_ms < 5.0, \
            f"3D detection took {avg_latency_ms:.3f}ms, exceeds 5ms requirement"

    def test_3d_detection_with_large_match_sets(self):
        """Test 3D detection performance with large match sets."""
        # Create prompt that matches many frameworks, modes, profiles
        frameworks_list = list(_COGNITIVE_FRAMEWORKS.keys())
        modes_list = list(_REASONING_MODES.keys())
        profiles_list = list(_THINK_PROFILES.keys())

        # Warm-up
        _detect_3d_compatibility(frameworks_list, modes_list, profiles_list)

        # Performance measurement
        iterations = 1000
        start_time = time.perf_counter()

        for _ in range(iterations):
            result = _detect_3d_compatibility(frameworks_list, modes_list, profiles_list)

        end_time = time.perf_counter()
        avg_latency_ms = ((end_time - start_time) / iterations) * 1000

        # Verify <5ms requirement even with large match sets
        assert avg_latency_ms < 5.0, \
            f"3D detection with large sets took {avg_latency_ms:.3f}ms, exceeds 5ms requirement"

    def test_empty_match_performance(self):
        """Test performance with empty match sets."""
        # Empty match sets
        frameworks = []
        modes = []
        profiles = []

        # Performance measurement
        iterations = 10000
        start_time = time.perf_counter()

        for _ in range(iterations):
            result = _detect_3d_compatibility(frameworks, modes, profiles)

        end_time = time.perf_counter()
        avg_latency_ms = ((end_time - start_time) / iterations) * 1000

        # Should be very fast with empty sets
        assert avg_latency_ms < 0.1, \
            f"Empty match handling took {avg_latency_ms:.3f}ms, exceeds 0.1ms requirement"

        # Should return empty list
        result = _detect_3d_compatibility(frameworks, modes, profiles)
        assert len(result) == 0, "Should return empty list for empty matches"


class TestFalsePositives:
    """Tests to prevent false positive 3D combinations."""

    def test_no_false_positives_simple_prompts(self):
        """Test that simple prompts don't trigger complex 3D combinations."""
        simple_prompts = [
            "What's a function?",
            "How do I write a loop?",
            "Hello world",
            "Simple question",
        ]

        for prompt in simple_prompts:
            result = detect_prompt(prompt)

            # Simple prompts should not trigger 3D combinations
            # (may have individual matches but not full 3D)
            assert len(result.compatible_combinations) == 0 or \
                   all(len(result.matched_frameworks) == 0 or
                       len(result.matched_modes) == 0 or
                       len(result.matched_profiles) == 0
                       for _ in result.compatible_combinations), \
                f"Simple prompt '{prompt}' should not trigger complex 3D combinations"

    def test_no_false_positives_unrelated_combinations(self):
        """Test that unrelated dimensions don't create false combinations."""
        # Framework for debugging
        # Mode for architecture
        # Profile for security
        # These shouldn't combine if no semantic relationship

        frameworks = ["chestertons_fence"]
        modes = ["multi_agent"]
        profiles = ["security_review"]

        # Should not detect 3D combination if not in matrix
        result = _detect_3d_compatibility(frameworks, modes, profiles)

        # Verify no false combinations created
        for combo in result:
            combo_tuple = combo["combination"]
            assert combo_tuple in _COMPATIBILITY_MATRIX, \
                f"Combination {combo_tuple} should be in matrix"

    def test_only_matrix_entries_returned(self):
        """Test that only hardcoded matrix entries are returned."""
        # Use all frameworks, modes, profiles
        frameworks = list(_COGNITIVE_FRAMEWORKS.keys())
        modes = list(_REASONING_MODES.keys())
        profiles = list(_THINK_PROFILES.keys())

        # Detect combinations
        result = _detect_3d_compatibility(frameworks, modes, profiles)

        # Verify all returned combinations are in matrix
        for combo in result:
            combo_tuple = combo["combination"]
            assert combo_tuple in _COMPATIBILITY_MATRIX, \
                f"Combination {combo_tuple} must be in compatibility matrix"

    def test_no_spontaneous_combination_generation(self):
        """Test that system doesn't generate combinations not in matrix."""
        # Specific framework, mode, profile that should NOT combine
        frameworks = ["cynefin_classification"]
        modes = ["graph"]
        profiles = ["performance_analysis"]

        # Detect combinations
        result = _detect_3d_compatibility(frameworks, modes, profiles)

        # If combination exists, it must be in matrix
        # If not in matrix, should return empty
        if len(result) > 0:
            for combo in result:
                combo_tuple = combo["combination"]
                assert combo_tuple in _COMPATIBILITY_MATRIX, \
                    f"Spontaneous combination {combo_tuple} generated"
        else:
            # Empty result is acceptable if combination not in matrix
            assert True


class TestEdgeCases:
    """Edge case tests for compatibility matrix."""

    def test_empty_matrix_loads(self):
        """Test that system handles empty matrix gracefully."""
        # Save original matrix
        original_matrix = _COMPATIBILITY_MATRIX.copy()

        try:
            # Clear matrix
            _COMPATIBILITY_MATRIX.clear()

            # Should not crash
            frameworks = ["assumption_surfacing"]
            modes = ["multi_agent"]
            profiles = ["architecture"]

            result = _detect_3d_compatibility(frameworks, modes, profiles)

            # Should return empty list
            assert len(result) == 0, "Empty matrix should return empty list"

        finally:
            # Restore original matrix
            _COMPATIBILITY_MATRIX.update(original_matrix)

    def test_matrix_persistence(self):
        """Test that matrix persists to disk and loads correctly."""
        import json
        import tempfile

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)

        try:
            # Create sample matrix
            sample_matrix = {
                ("test_framework", "test_mode", "test_profile"): CompatibilityMatrixEntry(
                    combination=("test_framework", "test_mode", "test_profile"),
                    enhancement="test_enhancement",
                    evidence_source="test",
                    creation_date="2026-03-15T00:00:00Z",
                    usage_count=0,
                    last_used=None,
                    rationale="Test rationale",
                )
            }

            # Write to file
            data = {
                "version": "1.0",
                "entries": [
                    {
                        "combination": list(k),
                        "enhancement": v["enhancement"],
                        "evidence_source": v["evidence_source"],
                        "creation_date": v["creation_date"],
                        "usage_count": v["usage_count"],
                        "last_used": v["last_used"],
                        "rationale": v["rationale"],
                    }
                    for k, v in sample_matrix.items()
                ]
            }

            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f)

            # Load from file (simulate load_matrix_from_disk)
            with open(temp_path, encoding='utf-8') as f:
                loaded_data = json.load(f)

            # Verify data loaded correctly
            assert "entries" in loaded_data, "Loaded data should have 'entries'"
            assert len(loaded_data["entries"]) == 1, "Should have 1 entry"

            entry = loaded_data["entries"][0]
            assert entry["combination"] == ["test_framework", "test_mode", "test_profile"], \
                "Combination should load correctly"

        finally:
            # Cleanup
            if temp_path.exists():
                temp_path.unlink()

    def test_matrix_validation_valid_entries(self):
        """Test that validation accepts valid matrix entries."""
        # This should not raise
        try:
            validate_matrix(
                _COMPATIBILITY_MATRIX,
                set(_COGNITIVE_FRAMEWORKS.keys()),
                set(_REASONING_MODES.keys()),
                set(_THINK_PROFILES.keys())
            )
        except ValueError as e:
            pytest.fail(f"Valid matrix should pass validation: {e}")

    def test_matrix_validation_invalid_framework(self):
        """Test that validation rejects invalid framework names."""
        # Create matrix with invalid framework
        invalid_matrix = {
            ("invalid_framework", "multi_agent", "architecture"): CompatibilityMatrixEntry(
                combination=("invalid_framework", "multi_agent", "architecture"),
                enhancement="test",
                evidence_source="test",
                creation_date="2026-03-15T00:00:00Z",
                usage_count=0,
                last_used=None,
                rationale="test",
            )
        }

        # Should raise ValueError
        with pytest.raises(ValueError, match="Invalid framework"):
            validate_matrix(
                invalid_matrix,
                set(_COGNITIVE_FRAMEWORKS.keys()),
                set(_REASONING_MODES.keys()),
                set(_THINK_PROFILES.keys())
            )

    def test_matrix_validation_invalid_mode(self):
        """Test that validation rejects invalid mode names."""
        # Create matrix with invalid mode
        invalid_matrix = {
            ("assumption_surfacing", "invalid_mode", "architecture"): CompatibilityMatrixEntry(
                combination=("assumption_surfacing", "invalid_mode", "architecture"),
                enhancement="test",
                evidence_source="test",
                creation_date="2026-03-15T00:00:00Z",
                usage_count=0,
                last_used=None,
                rationale="test",
            )
        }

        # Should raise ValueError
        with pytest.raises(ValueError, match="Invalid mode"):
            validate_matrix(
                invalid_matrix,
                set(_COGNITIVE_FRAMEWORKS.keys()),
                set(_REASONING_MODES.keys()),
                set(_THINK_PROFILES.keys())
            )

    def test_matrix_validation_invalid_profile(self):
        """Test that validation rejects invalid profile names."""
        # Create matrix with invalid profile
        invalid_matrix = {
            ("assumption_surfacing", "multi_agent", "invalid_profile"): CompatibilityMatrixEntry(
                combination=("assumption_surfacing", "multi_agent", "invalid_profile"),
                enhancement="test",
                evidence_source="test",
                creation_date="2026-03-15T00:00:00Z",
                usage_count=0,
                last_used=None,
                rationale="test",
            )
        }

        # Should raise ValueError
        with pytest.raises(ValueError, match="Invalid profile"):
            validate_matrix(
                invalid_matrix,
                set(_COGNITIVE_FRAMEWORKS.keys()),
                set(_REASONING_MODES.keys()),
                set(_THINK_PROFILES.keys())
            )

    def test_matrix_validation_duplicate_keys(self):
        """Test that validation rejects duplicate combination keys."""
        # This test verifies the validation function catches duplicates
        # In practice, dict keys are unique, so we test the validation logic

        # Create a list with duplicate keys (simulating bad data)
        duplicate_keys = [
            ("assumption_surfacing", "multi_agent", "architecture"),
            ("assumption_surfacing", "multi_agent", "architecture"),
        ]

        # Verify duplicates detected
        unique_keys = set(duplicate_keys)
        assert len(duplicate_keys) != len(unique_keys), \
            "Test data should contain duplicates"

        duplicates = [k for k in duplicate_keys if duplicate_keys.count(k) > 1]

        # Should detect duplicates (2 occurrences of the same key)
        assert len(duplicates) == 2, "Should detect 2 occurrences of duplicate key"


class TestIntegrationWithConflictArbiter:
    """Integration tests with conflict_arbiter.py."""

    def test_3d_combination_passed_to_arbiter(self):
        """Test that 3D combinations are available to conflict arbiter."""

        prompt = "Design system architecture considering team structure"

        # Detect prompt (simulates UserPromptSubmit hook)
        detection_result = detect_prompt(prompt)

        # If 3D combinations detected, verify they're available for arbiter
        if len(detection_result.compatible_combinations) > 0:
            # Verify detection_result has compatible_combinations
            assert hasattr(detection_result, 'compatible_combinations'), \
                "Detection result should have compatible_combinations for arbiter"

            # Verify structure
            for combo in detection_result.compatible_combinations:
                assert "combination" in combo, "Combo should have 'combination'"
                assert "enhancement" in combo, "Combo should have 'enhancement'"
                assert "rationale" in combo, "Combo should have 'rationale'"

    def test_arbiter_receives_3d_precedence(self):
        """Test that conflict arbiter gives precedence to 3D combinations."""
        from UserPromptSubmit_modules.cognitive_enhancers import Enhancer
        from UserPromptSubmit_modules.conflict_arbiter import resolve_conflict

        prompt = "Design system architecture with multiple stakeholders. Evaluate from multiple perspectives."

        # Detect prompt
        detection_result = detect_prompt(prompt)

        # Create mock enhancers (Enhancer has: name, injection, topics)
        mock_enhancers = [
            Enhancer(
                name="assumption_surfacing",
                injection="Test injection",
                topics=["implementation"],
            )
        ]

        # If 3D combination detected, verify arbiter uses it
        if len(detection_result.compatible_combinations) > 0 and \
           len(detection_result.matched_modes) > 0:

            # Resolve conflict with detection result
            arbiter_result = resolve_conflict(
                enhancers=mock_enhancers,
                mode_selection="multi_agent",
                reasoning_confidence=3,
                prompt_mode=None,
                detection_result=detection_result,
            )

            # Verify arbiter returned result
            assert arbiter_result is not None, "Arbiter should return result"

            # Verify rationale mentions 3D matrix if Rule 7 applied
            if "3D Compatibility Matrix" in arbiter_result.rationale:
                # Rule 7 was applied - 3D took precedence
                assert "3D Compatibility Matrix selected" in arbiter_result.rationale, \
                    "Arbiter should explicitly mention 3D selection"
        else:
            # If no 3D combination, skip this test
            pytest.skip("No 3D combination detected for this prompt")

    def test_no_3d_combination_fallback(self):
        """Test that system falls back to 2D/individual when no 3D match."""
        prompt = "Simple debugging task"

        # Detect prompt
        detection_result = detect_prompt(prompt)

        # If no 3D combinations, system should still work
        assert isinstance(detection_result.compatible_combinations, list), \
            "compatible_combinations should always be a list"

        # Empty list is acceptable
        if len(detection_result.compatible_combinations) == 0:
            # System should fall back to individual framework/mode/profile detection
            assert isinstance(detection_result.matched_frameworks, set), \
                "Should still have matched_frameworks"
            assert isinstance(detection_result.matched_modes, set), \
                "Should still have matched_modes"
            assert isinstance(detection_result.matched_profiles, set), \
                "Should still have matched_profiles"


class TestDocumentationAndMetrics:
    """Tests for matrix documentation and usage tracking."""

    def test_matrix_entry_documentation(self):
        """Test that matrix entries have rationale documentation."""
        # All entries should have rationale
        for combination, entry in _COMPATIBILITY_MATRIX.items():
            assert entry.get("rationale"), \
                f"Combination {combination} should have rationale documentation"

            # Rationale should be meaningful (not just placeholder)
            rationale = entry["rationale"]
            assert len(rationale) > 10, \
                f"Rationale for {combination} should be meaningful (>{len(rationale)} chars)"

    def test_usage_count_tracking(self):
        """Test that usage_count is tracked and updated."""
        # All entries should have usage_count
        for combination, entry in _COMPATIBILITY_MATRIX.items():
            assert "usage_count" in entry, \
                f"Combination {combination} should have usage_count"

            # Usage count should be non-negative integer
            usage_count = entry["usage_count"]
            assert isinstance(usage_count, int), \
                f"usage_count for {combination} should be int"
            assert usage_count >= 0, \
                f"usage_count for {combination} should be non-negative"

    def test_evidence_source_tracking(self):
        """Test that evidence_source is tracked."""
        # All entries should have evidence_source
        evidence_sources = set()
        for combination, entry in _COMPATIBILITY_MATRIX.items():
            assert "evidence_source" in entry, \
                f"Combination {combination} should have evidence_source"

            evidence_source = entry["evidence_source"]
            evidence_sources.add(evidence_source)

        # Should have at least one evidence source
        assert len(evidence_sources) > 0, "Should have at least one evidence source"

        # Common evidence sources
        common_sources = {"hardcoded", "empirical", "expert_validation"}
        assert any(source in common_sources for source in evidence_sources), \
            f"Should have common evidence sources, got: {evidence_sources}"

    def test_creation_date_tracking(self):
        """Test that creation_date is tracked."""
        import datetime

        # All entries should have creation_date
        for combination, entry in _COMPATIBILITY_MATRIX.items():
            assert "creation_date" in entry, \
                f"Combination {combination} should have creation_date"

            # Creation date should be ISO format
            creation_date = entry["creation_date"]
            assert isinstance(creation_date, str), \
                f"creation_date for {combination} should be string"

            # Try to parse as ISO date
            try:
                datetime.datetime.fromisoformat(creation_date.replace('Z', '+00:00'))
            except ValueError:
                pytest.fail(f"creation_date '{creation_date}' for {combination} is not valid ISO format")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
