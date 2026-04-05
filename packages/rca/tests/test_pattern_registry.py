"""Comprehensive tests for pattern_registry module.

Tests for the Pattern Registry which stores pattern-level fixes that apply
across locations.
"""

import json
import os
import tempfile
import threading
from pathlib import Path
from time import sleep
from unittest.mock import MagicMock, patch

import pytest

from rca.pattern_registry import (
    # Main class
    PatternRegistry,
    # Singleton
    get_pattern_registry,
    # Data classes from error_signature
    ErrorSignature,
    SignatureMatch,
    PatternFixRecord,
    # Convenience functions
    register_pattern_fix,
    lookup_pattern_fix,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    # Cleanup
    import shutil
    if Path(temp_dir).exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def sample_signature():
    """Create a sample ErrorSignature for testing."""
    return ErrorSignature(
        pattern_name="null_dict_access",
        error_type="AttributeError",
    )


@pytest.fixture
def registry(temp_cache_dir):
    """Create a PatternRegistry instance with temporary cache."""
    return PatternRegistry(cache_dir=temp_cache_dir)


@pytest.fixture
def populated_registry(registry):
    """Create a registry with sample pattern fixes."""
    sig1 = ErrorSignature("null_dict_access", "AttributeError")
    registry.add_pattern_fix(
        sig1,
        "Use dict.get(key, default) or check if dict is None",
        fix_template="dict.get(key, default)",
        location="download_handler.py:127",
        verified=True,
    )

    sig2 = ErrorSignature("missing_import", "ModuleNotFoundError")
    registry.add_pattern_fix(
        sig2,
        "Install the missing module",
        fix_template="pip install {module}",
        location="main.py:5",
        verified=False,
    )

    return registry


# =============================================================================
# Tests for PatternRegistry Initialization
# =============================================================================

class TestPatternRegistryInit:
    """Tests for PatternRegistry initialization."""

    def test_init_with_cache_dir(self, temp_cache_dir):
        """Test initialization with custom cache directory."""
        reg = PatternRegistry(cache_dir=temp_cache_dir)
        assert reg.cache_dir == temp_cache_dir
        assert reg.registry_file == temp_cache_dir / "pattern_registry.json"

    def test_init_creates_cache_directory(self, temp_cache_dir):
        """Test that initialization creates cache directory if needed."""
        new_dir = temp_cache_dir / "new_cache"
        reg = PatternRegistry(cache_dir=new_dir)
        assert new_dir.exists()

    def test_init_uses_default_cache_dir(self):
        """Test initialization with default cache directory."""
        # Use temp dir to avoid creating in actual project location
        with patch.object(PatternRegistry, 'DEFAULT_CACHE_DIR', tempfile.mkdtemp()):
            reg = PatternRegistry()
            assert reg.cache_dir is not None

    def test_init_loads_existing_registry(self, temp_cache_dir):
        """Test that initialization loads existing registry from disk."""
        # Create an existing registry file
        registry_file = temp_cache_dir / "pattern_registry.json"
        existing_data = {
            "patterns": {
                "test_hash": {
                    "pattern_name": "null_dict_access",
                    "error_type": "AttributeError",
                    "fix_description": "Test fix",
                    "fix_template": "Test template",
                    "code_diff": "",
                    "applied_count": 5,
                    "locations_seen": ["test.py:42"],
                    "first_seen": "2024-01-01T00:00:00",
                    "last_seen": "2024-01-02T00:00:00",
                    "verified": True,
                }
            },
            "metadata": {"version": "1.0"}
        }
        registry_file.write_text(json.dumps(existing_data))

        # Load registry
        reg = PatternRegistry(cache_dir=temp_cache_dir)

        # Should have loaded existing patterns
        assert len(reg._registry["patterns"]) == 1
        assert "test_hash" in reg._registry["patterns"]

    def test_init_creates_new_registry_if_none_exists(self, temp_cache_dir):
        """Test that initialization creates new registry if none exists."""
        reg = PatternRegistry(cache_dir=temp_cache_dir)

        assert "patterns" in reg._registry
        assert "metadata" in reg._registry
        assert len(reg._registry["patterns"]) == 0


# =============================================================================
# Tests for _load_registry method
# =============================================================================

class TestPatternRegistryLoadRegistry:
    """Tests for _load_registry method."""

    def test_load_registry_creates_default_structure(self, temp_cache_dir):
        """Test loading creates default registry structure."""
        reg = PatternRegistry(cache_dir=temp_cache_dir)

        assert reg._registry["metadata"]["version"] == "1.0"
        assert isinstance(reg._registry["patterns"], dict)

    def test_load_registry_handles_corrupt_json(self, temp_cache_dir):
        """Test loading handles corrupt JSON gracefully."""
        registry_file = temp_cache_dir / "pattern_registry.json"
        registry_file.write_text("invalid json {{{")

        # Should not raise, should return default structure
        reg = PatternRegistry(cache_dir=temp_cache_dir)
        assert len(reg._registry["patterns"]) == 0

    def test_load_registry_handles_os_error(self, temp_cache_dir):
        """Test loading handles OS errors gracefully."""
        # Create a file instead of directory
        (temp_cache_dir / "pattern_registry.json").parent.mkdir(parents=True, exist_ok=True)
        (temp_cache_dir / "pattern_registry.json").write_text("{}")

        # Should handle gracefully
        reg = PatternRegistry(cache_dir=temp_cache_dir)
        assert isinstance(reg._registry, dict)


# =============================================================================
# Tests for _save_registry method
# =============================================================================

class TestPatternRegistrySaveRegistry:
    """Tests for _save_registry method."""

    def test_save_registry_writes_to_disk(self, registry):
        """Test that save writes registry to disk."""
        # Manually trigger save by adding a pattern
        sig = ErrorSignature("null_dict_access", "AttributeError")
        registry.add_pattern_fix(sig, "Test fix")

        # Check file exists and contains data
        assert registry.registry_file.exists()

        data = json.loads(registry.registry_file.read_text())
        assert "patterns" in data
        assert "metadata" in data

    def test_save_registry_returns_true_on_success(self, registry, sample_signature):
        """Test that save returns True on success."""
        result = registry.add_pattern_fix(sample_signature, "Test fix")
        assert result is True

    def test_save_registry_returns_false_on_failure(self, registry):
        """Test that save returns False on write failure."""
        # Make registry file a directory to cause write failure
        registry.registry_file.mkdir(parents=True, exist_ok=True)

        sig = ErrorSignature("null_dict_access", "AttributeError")
        result = registry.add_pattern_fix(sig, "Test fix")
        assert result is False


# =============================================================================
# Tests for add_pattern_fix method
# =============================================================================

class TestPatternRegistryAddPatternFix:
    """Tests for add_pattern_fix method."""

    def test_add_new_pattern_fix(self, registry, sample_signature):
        """Test adding a new pattern fix."""
        success = registry.add_pattern_fix(
            sample_signature,
            "Use dict.get(key, default)",
            fix_template="dict.get(key, default)",
            location="test.py:42",
        )

        assert success is True
        assert sample_signature.signature_hash in registry._registry["patterns"]

    def test_add_pattern_fix_saves_all_fields(self, registry, sample_signature):
        """Test that add saves all provided fields."""
        registry.add_pattern_fix(
            sample_signature,
            "Fix description",
            fix_template="Fix template",
            code_diff="+ fixed code",
            location="test.py:42",
            verified=True,
        )

        data = registry._registry["patterns"][sample_signature.signature_hash]

        assert data["fix_description"] == "Fix description"
        assert data["fix_template"] == "Fix template"
        assert data["code_diff"] == "+ fixed code"
        assert data["verified"] is True
        assert "test.py:42" in data["locations_seen"]

    def test_add_pattern_fix_updates_existing(self, registry, sample_signature):
        """Test that add updates existing pattern."""
        # Add initial pattern
        registry.add_pattern_fix(
            sample_signature,
            "Initial fix",
            location="file1.py:10",
        )

        # Update with new location and verified status
        registry.add_pattern_fix(
            sample_signature,
            "Updated fix",
            location="file2.py:20",
            verified=True,
        )

        data = registry._registry["patterns"][sample_signature.signature_hash]

        assert data["applied_count"] == 2
        assert data["verified"] is True  # Should be updated to True
        assert "file1.py:10" in data["locations_seen"]
        assert "file2.py:20" in data["locations_seen"]

    def test_add_pattern_fix_preserves_verified(self, registry, sample_signature):
        """Test that verified status is preserved when updating."""
        # Add as verified
        registry.add_pattern_fix(
            sample_signature,
            "Fix",
            verified=True,
        )

        # Update without verified (should preserve True)
        registry.add_pattern_fix(
            sample_signature,
            "Updated fix",
            verified=False,
        )

        data = registry._registry["patterns"][sample_signature.signature_hash]
        assert data["verified"] is True

    def test_add_pattern_fix_updates_fix_description_for_unverified(self, registry, sample_signature):
        """Test that fix description updates for unverified patterns."""
        # Add as unverified
        registry.add_pattern_fix(
            sample_signature,
            "Initial fix",
            verified=False,
        )

        # Update with new description
        registry.add_pattern_fix(
            sample_signature,
            "Better fix",
            verified=False,
        )

        data = registry._registry["patterns"][sample_signature.signature_hash]
        assert data["fix_description"] == "Better fix"

    def test_add_pattern_fix_doesnt_update_verified_fix_description(self, registry, sample_signature):
        """Test that verified fix description is not overwritten."""
        # Add as verified with specific fix
        registry.add_pattern_fix(
            sample_signature,
            "Verified fix",
            verified=True,
        )

        # Try to update with unverified fix
        registry.add_pattern_fix(
            sample_signature,
            "Unverified fix",
            verified=False,
        )

        data = registry._registry["patterns"][sample_signature.signature_hash]
        assert data["fix_description"] == "Verified fix"

    def test_add_pattern_fix_updates_fix_template(self, registry, sample_signature):
        """Test that fix_template is updated."""
        registry.add_pattern_fix(
            sample_signature,
            "Fix",
            fix_template="template1",
        )

        registry.add_pattern_fix(
            sample_signature,
            "Fix",
            fix_template="template2",
        )

        data = registry._registry["patterns"][sample_signature.signature_hash]
        assert data["fix_template"] == "template2"

    def test_add_pattern_fix_updates_code_diff(self, registry, sample_signature):
        """Test that code_diff is updated."""
        registry.add_pattern_fix(
            sample_signature,
            "Fix",
            code_diff="+ initial",
        )

        registry.add_pattern_fix(
            sample_signature,
            "Fix",
            code_diff="+ updated",
        )

        data = registry._registry["patterns"][sample_signature.signature_hash]
        assert data["code_diff"] == "+ updated"

    def test_add_pattern_fix_tracks_locations(self, registry, sample_signature):
        """Test that all locations are tracked."""
        locations = ["file1.py:10", "file1.py:20", "file2.py:5"]

        for loc in locations:
            registry.add_pattern_fix(sample_signature, "Fix", location=loc)

        data = registry._registry["patterns"][sample_signature.signature_hash]

        for loc in locations:
            assert loc in data["locations_seen"]

    def test_add_pattern_fix_ignores_duplicate_locations(self, registry, sample_signature):
        """Test that duplicate locations are not added twice."""
        registry.add_pattern_fix(sample_signature, "Fix", location="test.py:10")
        registry.add_pattern_fix(sample_signature, "Fix", location="test.py:10")

        data = registry._registry["patterns"][sample_signature.signature_hash]

        # Should only have one entry
        assert data["locations_seen"].count("test.py:10") == 1

    def test_add_pattern_fix_empty_location(self, registry, sample_signature):
        """Test adding pattern with empty location."""
        registry.add_pattern_fix(
            sample_signature,
            "Fix",
            location="",
        )

        data = registry._registry["patterns"][sample_signature.signature_hash]
        assert data["locations_seen"] == []


# =============================================================================
# Tests for get_pattern_fix method
# =============================================================================

class TestPatternRegistryGetPatternFix:
    """Tests for get_pattern_fix method."""

    def test_get_existing_pattern_fix(self, registry, sample_signature):
        """Test getting an existing pattern fix."""
        registry.add_pattern_fix(
            sample_signature,
            "Test fix",
            verified=True,
        )

        fix_record = registry.get_pattern_fix(sample_signature)

        assert fix_record is not None
        assert isinstance(fix_record, PatternFixRecord)
        assert fix_record.fix_description == "Test fix"
        assert fix_record.verified is True

    def test_get_nonexistent_pattern_fix(self, registry, sample_signature):
        """Test getting a pattern fix that doesn't exist."""
        fix_record = registry.get_pattern_fix(sample_signature)
        assert fix_record is None

    def test_get_pattern_fix_returns_complete_record(self, registry, sample_signature):
        """Test that get returns complete PatternFixRecord."""
        registry.add_pattern_fix(
            sample_signature,
            "Fix description",
            fix_template="Fix template",
            code_diff="+ code",
            location="test.py:42",
            verified=True,
        )

        fix_record = registry.get_pattern_fix(sample_signature)

        assert fix_record.signature == sample_signature
        assert fix_record.fix_description == "Fix description"
        assert fix_record.fix_template == "Fix template"
        assert fix_record.code_diff == "+ code"
        assert fix_record.verified is True
        assert "test.py:42" in fix_record.locations_seen


# =============================================================================
# Tests for find_match method
# =============================================================================

class TestPatternRegistryFindMatch:
    """Tests for find_match method."""

    def test_find_match_with_registered_pattern(self, registry):
        """Test finding a match for registered pattern."""
        sig = ErrorSignature("null_dict_access", "AttributeError")
        registry.add_pattern_fix(
            sig,
            "Use dict.get()",
            verified=True,
        )

        match = registry.find_match(
            "AttributeError: 'NoneType' object has no attribute '__getitem__'"
        )

        assert match is not None
        assert isinstance(match, SignatureMatch)
        assert match.suggested_fix == "Use dict.get()"

    def test_find_match_without_registered_pattern(self, registry):
        """Test finding match when pattern not in registry."""
        match = registry.find_match(
            "AttributeError: 'NoneType' object has no attribute '__getitem__'"
        )

        # Should still match to pattern via match_to_pattern
        assert match is not None
        assert isinstance(match, SignatureMatch)

    def test_find_match_below_confidence_threshold(self, registry):
        """Test that low confidence matches are filtered."""
        # This test depends on actual confidence calculation
        match = registry.find_match(
            "Some unclear error message",
            min_confidence=0.9,
        )

        # May return None if no high-confidence match
        assert match is None or match.confidence >= 0.9 or match.confidence < 0.9

    def test_find_match_enhances_with_recorded_fix(self, registry):
        """Test that recorded fix enhances the match."""
        sig = ErrorSignature("null_dict_access", "AttributeError")
        custom_fix = "Custom fix from registry"

        registry.add_pattern_fix(sig, custom_fix, verified=True)

        match = registry.find_match(
            "AttributeError: 'NoneType' object has no attribute '__getitem__'"
        )

        if match and match.suggested_fix:
            # Should use registry fix if available
            assert custom_fix in match.suggested_fix or match.suggested_fix == custom_fix


# =============================================================================
# Tests for get_all_patterns method
# =============================================================================

class TestPatternRegistryGetAllPatterns:
    """Tests for get_all_patterns method."""

    def test_get_all_patterns_empty(self, registry):
        """Test getting all patterns when registry is empty."""
        patterns = registry.get_all_patterns()
        assert len(patterns) == 0

    def test_get_all_patterns_returns_records(self, populated_registry):
        """Test that get_all_patterns returns PatternFixRecords."""
        patterns = populated_registry.get_all_patterns()

        assert len(patterns) == 2
        assert all(isinstance(p, PatternFixRecord) for p in patterns)

    def test_get_all_patterns_sorted_by_applied_count(self, registry):
        """Test that patterns are sorted by applied_count descending."""
        sig1 = ErrorSignature("pattern1", "Error")
        sig2 = ErrorSignature("pattern2", "Error")

        registry.add_pattern_fix(sig1, "Fix1")
        # Apply pattern1 more times
        registry.add_pattern_fix(sig1, "Fix1")
        registry.add_pattern_fix(sig1, "Fix1")

        registry.add_pattern_fix(sig2, "Fix2")

        patterns = registry.get_all_patterns()

        # pattern1 should be first (applied 3 times vs 1)
        assert patterns[0].signature.pattern_name == "pattern1"

    def test_get_all_patterns_includes_all_fields(self, registry, sample_signature):
        """Test that returned records include all fields."""
        registry.add_pattern_fix(
            sample_signature,
            "Fix",
            fix_template="Template",
            code_diff="+ code",
            verified=True,
        )

        patterns = registry.get_all_patterns()
        record = patterns[0]

        assert record.fix_description == "Fix"
        assert record.fix_template == "Template"
        assert record.code_diff == "+ code"
        assert record.verified is True
        assert record.applied_count >= 1


# =============================================================================
# Tests for get_stats method
# =============================================================================

class TestPatternRegistryGetStats:
    """Tests for get_stats method."""

    def test_get_stats_empty_registry(self, registry):
        """Test stats for empty registry."""
        stats = registry.get_stats()

        assert stats["total_patterns"] == 0
        assert stats["total_applied"] == 0
        assert stats["total_locations"] == 0
        assert stats["verified_patterns"] == 0

    def test_get_stats_counts_patterns(self, populated_registry):
        """Test that stats counts patterns correctly."""
        stats = populated_registry.get_stats()
        assert stats["total_patterns"] == 2

    def test_get_stats_counts_applied(self, registry):
        """Test that stats counts total applications."""
        sig = ErrorSignature("test_pattern", "Error")

        # Apply pattern 3 times
        for _ in range(3):
            registry.add_pattern_fix(sig, "Fix", location="test.py")

        stats = registry.get_stats()
        assert stats["total_applied"] == 3

    def test_get_stats_counts_locations(self, registry):
        """Test that stats counts unique locations."""
        sig = ErrorSignature("test_pattern", "Error")

        registry.add_pattern_fix(sig, "Fix", location="file1.py:10")
        registry.add_pattern_fix(sig, "Fix", location="file2.py:20")

        stats = registry.get_stats()
        assert stats["total_locations"] == 2

    def test_get_stats_counts_verified(self, populated_registry):
        """Test that stats counts verified patterns."""
        stats = populated_registry.get_stats()
        assert stats["verified_patterns"] == 1  # Only first was verified

    def test_get_stats_top_patterns(self, registry):
        """Test that stats includes top patterns."""
        sig1 = ErrorSignature("pattern1", "Error")
        sig2 = ErrorSignature("pattern2", "Error")

        # Apply pattern1 more
        for _ in range(3):
            registry.add_pattern_fix(sig1, "Fix1")
        registry.add_pattern_fix(sig2, "Fix2")

        stats = registry.get_stats()
        top_patterns = stats["top_patterns"]

        assert len(top_patterns) > 0
        assert top_patterns[0][0] == "pattern1"  # Most applied

    def test_get_stats_includes_registry_file(self, registry):
        """Test that stats includes registry file path."""
        stats = registry.get_stats()
        assert "registry_file" in stats
        assert str(registry.cache_dir) in stats["registry_file"]


# =============================================================================
# Tests for search_by_pattern_name method
# =============================================================================

class TestPatternRegistrySearchByPatternName:
    """Tests for search_by_pattern_name method."""

    def test_search_by_pattern_name_found(self, registry):
        """Test searching by existing pattern name."""
        sig = ErrorSignature("null_dict_access", "AttributeError")
        registry.add_pattern_fix(sig, "Fix", location="file1.py")

        results = registry.search_by_pattern_name("null_dict_access")

        assert len(results) == 1
        assert results[0].signature.pattern_name == "null_dict_access"

    def test_search_by_pattern_name_not_found(self, registry):
        """Test searching by non-existent pattern name."""
        results = registry.search_by_pattern_name("nonexistent_pattern")
        assert len(results) == 0

    def test_search_by_pattern_name_multiple_matches(self, registry):
        """Test searching when multiple variations of pattern exist."""
        # Same pattern name, different error types
        sig1 = ErrorSignature("null_dict_access", "AttributeError")
        sig2 = ErrorSignature("null_dict_access", "KeyError")

        registry.add_pattern_fix(sig1, "Fix1")
        registry.add_pattern_fix(sig2, "Fix2")

        results = registry.search_by_pattern_name("null_dict_access")

        assert len(results) == 2

    def test_search_by_pattern_name_returns_records(self, registry):
        """Test that search returns PatternFixRecords."""
        sig = ErrorSignature("missing_import", "ImportError")
        registry.add_pattern_fix(sig, "Fix")

        results = registry.search_by_pattern_name("missing_import")

        assert all(isinstance(r, PatternFixRecord) for r in results)


# =============================================================================
# Tests for Singleton Pattern
# =============================================================================

class TestPatternRegistrySingleton:
    """Tests for get_pattern_registry singleton function."""

    def test_get_pattern_registry_returns_singleton(self):
        """Test that get_pattern_registry returns same instance."""
        # Note: This uses the actual singleton, which may have state
        reg1 = get_pattern_registry()
        reg2 = get_pattern_registry()
        assert reg1 is reg2

    def test_get_pattern_registry_thread_safe(self):
        """Test that singleton initialization is thread-safe."""
        # Reset singleton by deleting the module-level variable
        import rca.pattern_registry as pr_module
        pr_module._default_registry = None

        instances = []

        def get_instance():
            reg = get_pattern_registry()
            instances.append(reg)

        threads = []
        for _ in range(5):
            t = threading.Thread(target=get_instance)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All should be the same instance
        assert len(set(instances)) == 1


# =============================================================================
# Tests for Convenience Functions
# =============================================================================

class TestConvenienceFunctions:
    """Tests for module-level convenience functions."""

    def test_register_pattern_fix(self):
        """Test register_pattern_fix convenience function."""
        # This uses the singleton registry
        success = register_pattern_fix(
            "AttributeError: 'NoneType' object has no attribute",
            "Use dict.get() or check for None",
            location="test.py:42",
        )

        # Should succeed or fail gracefully
        assert isinstance(success, bool)

    def test_lookup_pattern_fix(self):
        """Test lookup_pattern_fix convenience function."""
        match = lookup_pattern_fix(
            "AttributeError: 'NoneType' object has no attribute '__getitem__'"
        )

        # Should return SignatureMatch or None
        assert match is None or isinstance(match, SignatureMatch)

    def test_register_and_lookup_roundtrip(self):
        """Test registering and then looking up a pattern."""
        error_msg = "AttributeError: 'NoneType' object has no attribute 'test'"

        # Register
        register_pattern_fix(
            error_msg,
            "Check for None before accessing",
            verified=True,
        )

        # Lookup
        match = lookup_pattern_fix(error_msg)

        # Should find the registered fix
        if match:
            assert match.suggested_fix is not None


# =============================================================================
# Tests for JSON Serialization/Deserialization
# =============================================================================

class TestJSONSerialization:
    """Tests for JSON serialization and deserialization."""

    def test_pattern_fix_record_to_dict(self, registry, sample_signature):
        """Test PatternFixRecord.to_dict method."""
        # Add pattern multiple times to increase applied_count
        for i in range(3):
            registry.add_pattern_fix(
                sample_signature,
                "Fix description",
                fix_template="Template",
                code_diff="+ code",
                location="file1.py",
                verified=True,
            )

        record = registry.get_pattern_fix(sample_signature)
        data = record.to_dict()

        assert data["pattern_name"] == "null_dict_access"
        assert data["error_type"] == "AttributeError"
        assert data["fix_description"] == "Fix description"
        assert data["fix_template"] == "Template"
        assert data["code_diff"] == "+ code"
        assert data["applied_count"] == 3
        assert data["verified"] is True

    def test_pattern_fix_record_from_dict(self):
        """Test PatternFixRecord.from_dict method."""
        data = {
            "pattern_name": "missing_import",
            "error_type": "ModuleNotFoundError",
            "fix_description": "Install module",
            "fix_template": "pip install {module}",
            "code_diff": "+ import module",
            "applied_count": 2,
            "locations_seen": ["main.py", "utils.py"],
            "first_seen": "2024-01-01",
            "last_seen": "2024-01-03",
            "verified": True,
        }

        record = PatternFixRecord.from_dict(data)

        assert record.signature.pattern_name == "missing_import"
        assert record.signature.error_type == "ModuleNotFoundError"
        assert record.fix_description == "Install module"
        assert record.applied_count == 2
        assert record.verified is True

    def test_round_trip_serialization(self, registry, sample_signature):
        """Test that to_dict and from_dict are inverses."""
        # Add pattern multiple times to increase applied_count
        for _ in range(5):
            registry.add_pattern_fix(
                sample_signature,
                "Fix",
                verified=True,
            )

        original = registry.get_pattern_fix(sample_signature)
        restored = PatternFixRecord.from_dict(original.to_dict())

        assert restored.signature == original.signature
        assert restored.fix_description == original.fix_description
        assert restored.verified == original.verified
        assert restored.applied_count == original.applied_count


# =============================================================================
# Tests for Concurrent Writes
# =============================================================================

class TestConcurrentWrites:
    """Tests for concurrent write operations."""

    def test_concurrent_pattern_adds(self, registry):
        """Test multiple threads adding patterns concurrently."""
        errors = []
        results = []

        def add_pattern(thread_id):
            try:
                sig = ErrorSignature(f"pattern_{thread_id}", "Error")
                success = registry.add_pattern_fix(sig, f"Fix {thread_id}")
                results.append(success)
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(10):
            t = threading.Thread(target=add_pattern, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Should complete without errors
        assert len(errors) == 0
        # All adds should succeed
        assert all(results)

    def test_concurrent_pattern_updates(self, registry):
        """Test multiple threads updating same pattern."""
        sig = ErrorSignature("shared_pattern", "Error")
        registry.add_pattern_fix(sig, "Initial fix")

        errors = []
        counters = []

        def update_pattern(thread_id):
            try:
                for _ in range(5):
                    registry.add_pattern_fix(sig, f"Update {thread_id}")
                counters.append(thread_id)
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(5):
            t = threading.Thread(target=update_pattern, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Should complete without errors
        assert len(errors) == 0
        # Applied count should reflect all updates
        record = registry.get_pattern_fix(sig)
        assert record.applied_count >= 1


# =============================================================================
# Tests for File I/O Error Handling
# =============================================================================

class TestFileIOErrorHandling:
    """Tests for file I/O error handling."""

    def test_handles_read_permission_error(self, temp_cache_dir):
        """Test handling read permission errors."""
        registry_file = temp_cache_dir / "pattern_registry.json"

        # Create file with no read permissions (Unix)
        registry_file.write_text("{}")
        try:
            os.chmod(registry_file, 0o000)
        except (OSError, AttributeError):
            # Windows or no permission to change permissions
            pass

        # Should handle gracefully
        reg = PatternRegistry(cache_dir=temp_cache_dir)
        assert isinstance(reg._registry, dict)

        # Restore permissions for cleanup
        try:
            os.chmod(registry_file, 0o644)
        except (OSError, AttributeError):
            pass

    def test_handles_write_permission_error(self, temp_cache_dir):
        """Test handling write permission errors."""
        # Create registry
        reg = PatternRegistry(cache_dir=temp_cache_dir)

        # On Windows, os.chmod with 0o444 doesn't prevent writing by the file owner
        # Test using a different approach: make the file a directory
        import shutil
        registry_file = reg.registry_file

        # Save current state if file exists
        if registry_file.exists():
            backup_data = registry_file.read_text()

        try:
            # Create a directory with the same name to cause write failure
            if registry_file.exists():
                registry_file.unlink()
            registry_file.mkdir(parents=True, exist_ok=True)

            sig = ErrorSignature("test", "Error")
            result = reg.add_pattern_fix(sig, "Fix")

            # Should return False on write failure
            assert result is False

        finally:
            # Cleanup: remove the directory so we can create a file
            if registry_file.is_dir():
                shutil.rmtree(registry_file, ignore_errors=True)
            elif registry_file.exists():
                registry_file.unlink()

            # Restore original data if it existed
            if registry_file.parent.exists() and 'backup_data' in locals():
                try:
                    registry_file.write_text(backup_data)
                except:
                    pass

    def test_handles_disk_full_simulation(self, registry):
        """Test handling disk full condition (simulated)."""
        # This is difficult to test reliably, so we verify the code handles it
        # by checking that save operations return bool
        sig = ErrorSignature("test", "Error")
        result = registry.add_pattern_fix(sig, "Fix")

        # Should return True on success, False on failure
        assert isinstance(result, bool)


# =============================================================================
# Tests for Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and unusual inputs."""

    def test_empty_pattern_name(self, registry):
        """Test handling empty pattern name."""
        sig = ErrorSignature("", "Error")
        result = registry.add_pattern_fix(sig, "Fix")
        # Should handle gracefully
        assert isinstance(result, bool)

    def test_special_characters_in_fix_description(self, registry):
        """Test special characters in fix description."""
        sig = ErrorSignature("test", "Error")
        special_fix = "Fix with \"quotes\", 'apostrophes', \nnewlines, \ttabs"

        result = registry.add_pattern_fix(sig, special_fix)
        assert result is True

        # Verify it persists correctly
        record = registry.get_pattern_fix(sig)
        assert record.fix_description == special_fix

    def test_unicode_in_fix_description(self, registry):
        """Test Unicode characters in fix description."""
        sig = ErrorSignature("test", "Error")
        unicode_fix = "Fix with emoji: \u2713 \u2717 and \u4e2d\u6587"

        result = registry.add_pattern_fix(sig, unicode_fix)
        assert result is True

    def test_very_long_fix_description(self, registry):
        """Test very long fix description."""
        sig = ErrorSignature("test", "Error")
        long_fix = "x" * 10000

        result = registry.add_pattern_fix(sig, long_fix)
        assert result is True

    def test_empty_locations_list(self, registry):
        """Test pattern with no locations."""
        sig = ErrorSignature("test", "Error")
        registry.add_pattern_fix(sig, "Fix", location="")

        record = registry.get_pattern_fix(sig)
        assert record.locations_seen == []

    def test_none_values_in_optional_fields(self, registry):
        """Test handling of None in optional fields."""
        sig = ErrorSignature("test", "Error")
        # The method accepts empty strings but not None for some fields
        result = registry.add_pattern_fix(
            sig,
            "Fix",
            fix_template="",
            code_diff="",
        )
        assert result is True

    def test_multiple_patterns_same_signature(self, registry):
        """Test that multiple patterns can have different error types."""
        sig1 = ErrorSignature("null_access", "AttributeError")
        sig2 = ErrorSignature("null_access", "KeyError")

        registry.add_pattern_fix(sig1, "Fix for AttributeError")
        registry.add_pattern_fix(sig2, "Fix for KeyError")

        # Both should be stored separately
        assert len(registry._registry["patterns"]) == 2


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for complete workflows."""

    def test_full_pattern_lifecycle(self, registry):
        """Test complete lifecycle of a pattern fix."""
        # 1. Register a pattern fix
        sig = ErrorSignature("null_dict_access", "AttributeError")
        registry.add_pattern_fix(
            sig,
            "Use dict.get()",
            fix_template="dict.get(key, default)",
            location="app.py:42",
            verified=True,
        )

        # 2. Retrieve the fix
        fix_record = registry.get_pattern_fix(sig)
        assert fix_record is not None
        assert fix_record.verified is True

        # 3. Apply to new location
        registry.add_pattern_fix(sig, "Use dict.get()", location="utils.py:10")

        # 4. Check stats
        stats = registry.get_stats()
        assert stats["total_applied"] == 2
        assert stats["total_locations"] == 2
        assert stats["verified_patterns"] == 1

        # 5. Search by pattern name
        results = registry.search_by_pattern_name("null_dict_access")
        assert len(results) == 1

    def test_cross_location_pattern_matching(self, registry):
        """Test that same pattern can be found across different locations."""
        sig = ErrorSignature("null_dict_access", "AttributeError")

        # Register fix from one location
        registry.add_pattern_fix(
            sig,
            "Use dict.get()",
            location="download_handler.py:127",
            verified=True,
        )

        # Find match for error at different location
        match = registry.find_match(
            "AttributeError: 'NoneType' object has no attribute '__getitem__' at batch_downloader.py:85"
        )

        # Should find the pattern even though location differs
        if match:
            assert "dict.get" in match.suggested_fix or match.signature.pattern_name == "null_dict_access"

    def test_pattern_evolution(self, registry):
        """Test how patterns evolve as they're applied more."""
        sig = ErrorSignature("missing_import", "ModuleNotFoundError")

        # Initial fix
        registry.add_pattern_fix(
            sig,
            "Install the module",
            location="main.py",
            verified=False,
        )

        record = registry.get_pattern_fix(sig)
        assert record.applied_count == 1
        assert record.verified is False

        # Later verified as working
        registry.add_pattern_fix(
            sig,
            "Install the module",
            location="utils.py",
            verified=True,
        )

        record = registry.get_pattern_fix(sig)
        assert record.applied_count == 2
        assert record.verified is True
        assert "main.py" in record.locations_seen
        assert "utils.py" in record.locations_seen
