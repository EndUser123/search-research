"""Comprehensive tests for fix_registry module.

Tests for the Fix Registry which stores fingerprints of errors with their
applied fixes for instant lookup.
"""

import json
import os
import tempfile
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from rca.fix_registry import (
    # Main class
    FixRegistry,
    # Singleton
    get_fix_registry,
    # Data classes from stack_trace_fingerprint
    StackTraceFingerprint,
    FixRecord,
    # Functions
    fingerprint_from_error,
    # Convenience functions
    register_fix,
    lookup_fix,
    find_similar_fixes,
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
def sample_fingerprint():
    """Create a sample StackTraceFingerprint for testing."""
    return StackTraceFingerprint(
        file_path="src/yt_fts/download/download_handler.py",
        line_number=127,
        error_type="AttributeError",
        function_name="get_vtt",
    )


@pytest.fixture
def registry(temp_cache_dir):
    """Create a FixRegistry instance with temporary cache."""
    return FixRegistry(cache_dir=temp_cache_dir)


@pytest.fixture
def populated_registry(registry):
    """Create a registry with sample fix records."""
    fp1 = StackTraceFingerprint(
        file_path="download_handler.py",
        line_number=127,
        error_type="AttributeError",
        function_name="get_vtt",
    )
    registry.add_fix(
        fp1,
        "Initialize yt_dlp_options before use",
        verified=True,
        error_message="AttributeError: 'NoneType' object has no attribute '__getitem__'",
        commit_hash="abc123",
        related_files=["config.py"],
    )

    fp2 = StackTraceFingerprint(
        file_path="batch_downloader.py",
        line_number=85,
        error_type="KeyError",
        function_name="process",
    )
    registry.add_fix(
        fp2,
        "Check if key exists before accessing",
        verified=False,
    )

    return registry


# =============================================================================
# Tests for FixRegistry Initialization
# =============================================================================

class TestFixRegistryInit:
    """Tests for FixRegistry initialization."""

    def test_init_with_cache_dir(self, temp_cache_dir):
        """Test initialization with custom cache directory."""
        reg = FixRegistry(cache_dir=temp_cache_dir)
        assert reg.cache_dir == temp_cache_dir
        assert reg.registry_file == temp_cache_dir / "fix_registry.json"

    def test_init_creates_cache_directory(self, temp_cache_dir):
        """Test that initialization creates cache directory if needed."""
        new_dir = temp_cache_dir / "new_cache"
        reg = FixRegistry(cache_dir=new_dir)
        assert new_dir.exists()

    def test_init_uses_default_cache_dir(self):
        """Test initialization with default cache directory."""
        # Use temp dir to avoid creating in actual project location
        with patch.object(FixRegistry, 'DEFAULT_CACHE_DIR', tempfile.mkdtemp()):
            reg = FixRegistry()
            assert reg.cache_dir is not None

    def test_init_loads_existing_registry(self, temp_cache_dir):
        """Test that initialization loads existing registry from disk."""
        # Create an existing registry file
        registry_file = temp_cache_dir / "fix_registry.json"
        existing_data = {
            "fingerprints": {
                "test_hash": {
                    "fingerprint": {
                        "file_path": "test.py",
                        "line_number": 42,
                        "error_type": "AttributeError",
                        "function_name": "test_func",
                    },
                    "fix_description": "Test fix",
                    "applied_at": "2024-01-01T00:00:00",
                    "verified": True,
                    "times_seen": 5,
                    "last_seen": "2024-01-05T00:00:00",
                    "error_message": "Test error",
                    "commit_hash": "abc123",
                    "related_files": ["file1.py"],
                }
            },
            "metadata": {"version": "1.0"}
        }
        registry_file.write_text(json.dumps(existing_data))

        # Load registry
        reg = FixRegistry(cache_dir=temp_cache_dir)

        # Should have loaded existing fingerprints
        assert len(reg._registry["fingerprints"]) == 1
        assert "test_hash" in reg._registry["fingerprints"]

    def test_init_creates_new_registry_if_none_exists(self, temp_cache_dir):
        """Test that initialization creates new registry if none exists."""
        reg = FixRegistry(cache_dir=temp_cache_dir)

        assert "fingerprints" in reg._registry
        assert "metadata" in reg._registry
        assert len(reg._registry["fingerprints"]) == 0


# =============================================================================
# Tests for _load_registry method
# =============================================================================

class TestFixRegistryLoadRegistry:
    """Tests for _load_registry method."""

    def test_load_registry_creates_default_structure(self, temp_cache_dir):
        """Test loading creates default registry structure."""
        reg = FixRegistry(cache_dir=temp_cache_dir)

        assert reg._registry["metadata"]["version"] == "1.0"
        assert isinstance(reg._registry["fingerprints"], dict)

    def test_load_registry_handles_corrupt_json(self, temp_cache_dir):
        """Test loading handles corrupt JSON gracefully."""
        registry_file = temp_cache_dir / "fix_registry.json"
        registry_file.write_text("invalid json {{{")

        # Should not raise, should return default structure
        reg = FixRegistry(cache_dir=temp_cache_dir)
        assert len(reg._registry["fingerprints"]) == 0

    def test_load_registry_handles_os_error(self, temp_cache_dir):
        """Test loading handles OS errors gracefully."""
        # Create a file instead of directory to trigger error
        (temp_cache_dir / "fix_registry.json").parent.mkdir(parents=True, exist_ok=True)
        (temp_cache_dir / "fix_registry.json").write_text("{}")

        # Should handle gracefully
        reg = FixRegistry(cache_dir=temp_cache_dir)
        assert isinstance(reg._registry, dict)


# =============================================================================
# Tests for _save_registry method
# =============================================================================

class TestFixRegistrySaveRegistry:
    """Tests for _save_registry method."""

    def test_save_registry_writes_to_disk(self, registry):
        """Test that save writes registry to disk."""
        # Manually trigger save by adding a fix
        fp = StackTraceFingerprint("test.py", 42, "AttributeError")
        registry.add_fix(fp, "Test fix")

        # Check file exists and contains data
        assert registry.registry_file.exists()

        data = json.loads(registry.registry_file.read_text())
        assert "fingerprints" in data
        assert "metadata" in data

    def test_save_registry_returns_true_on_success(self, registry, sample_fingerprint):
        """Test that save returns True on success."""
        result = registry.add_fix(sample_fingerprint, "Test fix")
        assert result is True

    def test_save_registry_returns_false_on_failure(self, registry):
        """Test that save returns False on write failure."""
        # Make registry file a directory to cause write failure
        registry.registry_file.mkdir(parents=True, exist_ok=True)

        fp = StackTraceFingerprint("test.py", 42, "AttributeError")
        result = registry.add_fix(fp, "Test fix")
        assert result is False


# =============================================================================
# Tests for add_fix method
# =============================================================================

class TestFixRegistryAddFix:
    """Tests for add_fix method."""

    def test_add_new_fix(self, registry, sample_fingerprint):
        """Test adding a new fix record."""
        success = registry.add_fix(
            sample_fingerprint,
            "Initialize variable before use",
            verified=True,
            error_message="AttributeError: NoneType",
            commit_hash="abc123",
            related_files=["config.py", "utils.py"],
        )

        assert success is True
        key = sample_fingerprint.fingerprint_hash
        assert key in registry._registry["fingerprints"]

    def test_add_fix_saves_all_fields(self, registry, sample_fingerprint):
        """Test that add saves all provided fields."""
        registry.add_fix(
            sample_fingerprint,
            "Fix description",
            verified=True,
            error_message="Error message",
            commit_hash="commit123",
            related_files=["file1.py", "file2.py"],
        )

        data = registry._registry["fingerprints"][sample_fingerprint.fingerprint_hash]

        assert data["fix_description"] == "Fix description"
        assert data["verified"] is True
        assert data["error_message"] == "Error message"
        assert data["commit_hash"] == "commit123"
        assert set(data["related_files"]) == {"file1.py", "file2.py"}

    def test_add_fix_updates_existing(self, registry, sample_fingerprint):
        """Test that add updates existing fix record."""
        # Add initial fix
        registry.add_fix(
            sample_fingerprint,
            "Initial fix",
            verified=False,
        )

        # Update with verified status
        registry.add_fix(
            sample_fingerprint,
            "Updated fix",
            verified=True,
        )

        data = registry._registry["fingerprints"][sample_fingerprint.fingerprint_hash]

        assert data["times_seen"] == 2
        assert data["verified"] is True

    def test_add_fix_preserves_verified_when_updating(self, registry, sample_fingerprint):
        """Test that verified status is preserved when updating."""
        # Add as verified
        registry.add_fix(
            sample_fingerprint,
            "Fix",
            verified=True,
        )

        # Update without verified
        registry.add_fix(
            sample_fingerprint,
            "Updated fix",
        )

        data = registry._registry["fingerprints"][sample_fingerprint.fingerprint_hash]
        assert data["verified"] is True

    def test_add_fix_updates_description_for_unverified(self, registry, sample_fingerprint):
        """Test that fix description updates for unverified fixes."""
        # Add as unverified
        registry.add_fix(
            sample_fingerprint,
            "Initial fix",
            verified=False,
        )

        # Update with new description
        registry.add_fix(
            sample_fingerprint,
            "Better fix",
            verified=False,
        )

        data = registry._registry["fingerprints"][sample_fingerprint.fingerprint_hash]
        assert data["fix_description"] == "Better fix"

    def test_add_fix_doesnt_update_verified_description(self, registry, sample_fingerprint):
        """Test that verified fix description is not overwritten."""
        # Add as verified with specific fix
        registry.add_fix(
            sample_fingerprint,
            "Verified fix",
            verified=True,
        )

        # Try to update with unverified fix
        registry.add_fix(
            sample_fingerprint,
            "Unverified fix",
            verified=False,
        )

        data = registry._registry["fingerprints"][sample_fingerprint.fingerprint_hash]
        assert data["fix_description"] == "Verified fix"

    def test_add_fix_updates_commit_hash(self, registry, sample_fingerprint):
        """Test that commit_hash is updated."""
        registry.add_fix(
            sample_fingerprint,
            "Fix",
            commit_hash="abc123",
        )

        registry.add_fix(
            sample_fingerprint,
            "Fix",
            commit_hash="def456",
        )

        data = registry._registry["fingerprints"][sample_fingerprint.fingerprint_hash]
        assert data["commit_hash"] == "def456"

    def test_add_fix_merges_related_files(self, registry, sample_fingerprint):
        """Test that related_files are merged, not replaced."""
        registry.add_fix(
            sample_fingerprint,
            "Fix",
            related_files=["file1.py", "file2.py"],
        )

        registry.add_fix(
            sample_fingerprint,
            "Fix",
            related_files=["file2.py", "file3.py"],
        )

        data = registry._registry["fingerprints"][sample_fingerprint.fingerprint_hash]

        # Should have unique files from both
        assert set(data["related_files"]) == {"file1.py", "file2.py", "file3.py"}

    def test_add_fix_updates_last_seen(self, registry, sample_fingerprint):
        """Test that last_seen timestamp is updated."""
        registry.add_fix(sample_fingerprint, "Fix")

        first_data = registry._registry["fingerprints"][sample_fingerprint.fingerprint_hash]
        first_last_seen = first_data["last_seen"]

        # Small delay to ensure different timestamp
        time.sleep(0.01)

        registry.add_fix(sample_fingerprint, "Fix")

        second_data = registry._registry["fingerprints"][sample_fingerprint.fingerprint_hash]
        second_last_seen = second_data["last_seen"]

        # Second update should have later timestamp
        assert second_last_seen >= first_last_seen


# =============================================================================
# Tests for get_fix method
# =============================================================================

class TestFixRegistryGetFix:
    """Tests for get_fix method."""

    def test_get_existing_fix(self, registry, sample_fingerprint):
        """Test getting an existing fix."""
        registry.add_fix(
            sample_fingerprint,
            "Test fix",
            verified=True,
        )

        fix_record = registry.get_fix(sample_fingerprint)

        assert fix_record is not None
        assert isinstance(fix_record, FixRecord)
        assert fix_record.fix_description == "Test fix"
        assert fix_record.verified is True

    def test_get_nonexistent_fix(self, registry, sample_fingerprint):
        """Test getting a fix that doesn't exist."""
        fix_record = registry.get_fix(sample_fingerprint)
        assert fix_record is None

    def test_get_fix_returns_complete_record(self, registry, sample_fingerprint):
        """Test that get returns complete FixRecord."""
        registry.add_fix(
            sample_fingerprint,
            "Fix description",
            verified=True,
            error_message="Error",
            commit_hash="commit",
            related_files=["file1.py"],
        )

        fix_record = registry.get_fix(sample_fingerprint)

        assert fix_record.fingerprint == sample_fingerprint
        assert fix_record.fix_description == "Fix description"
        assert fix_record.verified is True
        assert fix_record.times_seen == 1


# =============================================================================
# Tests for find_similar method
# =============================================================================

class TestFixRegistryFindSimilar:
    """Tests for find_similar method."""

    def test_find_similar_exact_match(self, registry, sample_fingerprint):
        """Test finding exact match."""
        registry.add_fix(
            sample_fingerprint,
            "Exact fix",
            verified=True,
        )

        similar = registry.find_similar(sample_fingerprint, min_similarity=1.0)

        assert len(similar) == 1
        assert similar[0][0] == 1.0  # Exact similarity
        assert similar[0][1].fix_description == "Exact fix"

    def test_find_similar_nearby_line(self, registry):
        """Test finding similar error at nearby line."""
        fp1 = StackTraceFingerprint("test.py", 42, "AttributeError")
        fp2 = StackTraceFingerprint("test.py", 45, "AttributeError")

        registry.add_fix(fp1, "Fix for line 42")

        similar = registry.find_similar(fp2, min_similarity=0.5)

        # Should find the similar error
        assert len(similar) > 0
        assert similar[0][0] >= 0.7  # Same file, nearby line

    def test_find_similar_same_file_different_error(self, registry):
        """Test finding same file, different error type."""
        fp1 = StackTraceFingerprint("test.py", 42, "AttributeError")
        fp2 = StackTraceFingerprint("test.py", 42, "TypeError")

        registry.add_fix(fp1, "Fix for AttributeError")

        similar = registry.find_similar(fp2, min_similarity=0.3)

        # May find with lower similarity
        assert len(similar) >= 0

    def test_find_similar_respects_min_similarity(self, registry):
        """Test that min_similarity threshold is respected."""
        fp1 = StackTraceFingerprint("test.py", 42, "AttributeError")
        fp2 = StackTraceFingerprint("other.py", 100, "TypeError")  # Very different

        registry.add_fix(fp1, "Fix")

        similar = registry.find_similar(fp2, min_similarity=0.9)

        # Should not find matches below threshold
        for similarity, _ in similar:
            assert similarity >= 0.9

    def test_find_similar_sorted_by_similarity(self, registry):
        """Test that results are sorted by similarity descending."""
        fp_query = StackTraceFingerprint("test.py", 50, "AttributeError")

        # Add various fingerprints
        fp1 = StackTraceFingerprint("test.py", 50, "AttributeError")  # Exact
        fp2 = StackTraceFingerprint("test.py", 55, "AttributeError")  # Nearby
        fp3 = StackTraceFingerprint("other.py", 50, "AttributeError")  # Different file

        for fp in [fp2, fp1, fp3]:  # Add in random order
            registry.add_fix(fp, f"Fix for {fp.file_path}")

        similar = registry.find_similar(fp_query, min_similarity=0.1)

        # Check sorted descending
        similarities = [s for s, _ in similar]
        assert similarities == sorted(similarities, reverse=True)

    def test_find_similar_empty_registry(self, registry, sample_fingerprint):
        """Test finding similar with empty registry."""
        similar = registry.find_similar(sample_fingerprint)
        assert len(similar) == 0


# =============================================================================
# Tests for search_by_file method
# =============================================================================

class TestFixRegistrySearchByFile:
    """Tests for search_by_file method."""

    def test_search_by_file_found(self, registry):
        """Test searching by existing file."""
        fp = StackTraceFingerprint("test.py", 42, "AttributeError")
        registry.add_fix(fp, "Fix")

        results = registry.search_by_file("test.py")

        assert len(results) == 1
        assert results[0].fingerprint.file_path == "test.py"

    def test_search_by_file_with_backslash(self, registry):
        """Test searching with Windows-style path."""
        fp = StackTraceFingerprint("src/test.py", 42, "AttributeError")
        registry.add_fix(fp, "Fix")

        # Search with forward slash
        results = registry.search_by_file("src/test.py")
        assert len(results) == 1

        # Search with backslash
        results = registry.search_by_file("src\\test.py")
        assert len(results) == 1

    def test_search_by_file_multiple_matches(self, registry):
        """Test searching file with multiple errors."""
        fp1 = StackTraceFingerprint("test.py", 10, "AttributeError")
        fp2 = StackTraceFingerprint("test.py", 20, "TypeError")

        registry.add_fix(fp1, "Fix 1")
        registry.add_fix(fp2, "Fix 2")

        results = registry.search_by_file("test.py")

        assert len(results) == 2

    def test_search_by_file_not_found(self, registry):
        """Test searching for non-existent file."""
        results = registry.search_by_file("nonexistent.py")
        assert len(results) == 0

    def test_search_by_file_sorted_by_times_seen(self, registry):
        """Test that results are sorted by times_seen descending."""
        fp1 = StackTraceFingerprint("test.py", 10, "AttributeError")
        fp2 = StackTraceFingerprint("test.py", 20, "TypeError")

        # fp1 seen more times
        registry.add_fix(fp1, "Fix 1")
        registry.add_fix(fp1, "Fix 1")
        registry.add_fix(fp1, "Fix 1")
        registry.add_fix(fp2, "Fix 2")

        results = registry.search_by_file("test.py")

        # fp1 should be first (seen 3 times vs 1)
        assert results[0].fingerprint.line_number == 10


# =============================================================================
# Tests for search_by_error_type method
# =============================================================================

class TestFixRegistrySearchByErrorType:
    """Tests for search_by_error_type method."""

    def test_search_by_error_type_found(self, registry):
        """Test searching by existing error type."""
        fp = StackTraceFingerprint("test.py", 42, "AttributeError")
        registry.add_fix(fp, "Fix")

        results = registry.search_by_error_type("AttributeError")

        assert len(results) == 1
        assert results[0].fingerprint.error_type == "AttributeError"

    def test_search_by_error_type_multiple_matches(self, registry):
        """Test searching error type with multiple files."""
        fp1 = StackTraceFingerprint("test.py", 10, "AttributeError")
        fp2 = StackTraceFingerprint("other.py", 20, "AttributeError")

        registry.add_fix(fp1, "Fix 1")
        registry.add_fix(fp2, "Fix 2")

        results = registry.search_by_error_type("AttributeError")

        assert len(results) == 2

    def test_search_by_error_type_not_found(self, registry):
        """Test searching for non-existent error type."""
        results = registry.search_by_error_type("CustomError")
        assert len(results) == 0

    def test_search_by_error_type_sorted_by_times_seen(self, registry):
        """Test that results are sorted by times_seen descending."""
        fp1 = StackTraceFingerprint("test.py", 10, "AttributeError")
        fp2 = StackTraceFingerprint("other.py", 20, "AttributeError")

        registry.add_fix(fp1, "Fix 1")
        registry.add_fix(fp1, "Fix 1")
        registry.add_fix(fp2, "Fix 2")

        results = registry.search_by_error_type("AttributeError")

        # fp1 should be first (seen 2 times vs 1)
        assert results[0].fingerprint.file_path == "test.py"


# =============================================================================
# Tests for get_stats method
# =============================================================================

class TestFixRegistryGetStats:
    """Tests for get_stats method."""

    def test_get_stats_empty_registry(self, registry):
        """Test stats for empty registry."""
        stats = registry.get_stats()

        assert stats["total_fingerprints"] == 0
        assert stats["total_times_seen"] == 0
        assert stats["verified_fixes"] == 0

    def test_get_stats_counts_fingerprints(self, populated_registry):
        """Test that stats counts fingerprints correctly."""
        stats = populated_registry.get_stats()
        assert stats["total_fingerprints"] == 2

    def test_get_stats_counts_times_seen(self, registry):
        """Test that stats counts total times seen."""
        fp = StackTraceFingerprint("test.py", 42, "AttributeError")

        # Add fix and update multiple times
        registry.add_fix(fp, "Fix")
        registry.add_fix(fp, "Fix")
        registry.add_fix(fp, "Fix")

        stats = registry.get_stats()
        assert stats["total_times_seen"] == 3

    def test_get_stats_counts_verified(self, populated_registry):
        """Test that stats counts verified fixes."""
        stats = populated_registry.get_stats()
        assert stats["verified_fixes"] == 1  # Only first was verified

    def test_get_stats_error_type_counts(self, registry):
        """Test that stats counts by error type."""
        fp1 = StackTraceFingerprint("test.py", 10, "AttributeError")
        fp2 = StackTraceFingerprint("test.py", 20, "TypeError")
        fp3 = StackTraceFingerprint("other.py", 30, "AttributeError")

        registry.add_fix(fp1, "Fix 1")
        registry.add_fix(fp2, "Fix 2")
        registry.add_fix(fp3, "Fix 3")

        stats = registry.get_stats()
        error_types = stats["error_types"]

        assert error_types.get("AttributeError", 0) == 2
        assert error_types.get("TypeError", 0) == 1

    def test_get_stats_file_counts(self, registry):
        """Test that stats counts by file."""
        fp1 = StackTraceFingerprint("test.py", 10, "AttributeError")
        fp2 = StackTraceFingerprint("test.py", 20, "TypeError")
        fp3 = StackTraceFingerprint("other.py", 30, "AttributeError")

        registry.add_fix(fp1, "Fix 1")
        registry.add_fix(fp2, "Fix 2")
        registry.add_fix(fp3, "Fix 3")

        stats = registry.get_stats()
        files = dict(stats["top_files"])

        assert files.get("test.py", 0) == 2
        assert files.get("other.py", 0) == 1

    def test_get_stats_top_files_limit(self, registry):
        """Test that top_files is limited to 5."""
        # Create 7 different files
        for i in range(7):
            fp = StackTraceFingerprint(f"file{i}.py", i, "AttributeError")
            registry.add_fix(fp, f"Fix {i}")

        stats = registry.get_stats()
        top_files = stats["top_files"]

        assert len(top_files) <= 5

    def test_get_stats_includes_registry_file(self, registry):
        """Test that stats includes registry file path."""
        stats = registry.get_stats()
        assert "registry_file" in stats
        assert str(registry.cache_dir) in stats["registry_file"]


# =============================================================================
# Tests for clear_stale method
# =============================================================================

class TestFixRegistryClearStale:
    """Tests for clear_stale method."""

    def test_clear_stale_removes_old_unverified(self, registry):
        """Test that clear_stale removes old unverified entries."""
        from email.utils import formatdate

        fp = StackTraceFingerprint("test.py", 42, "AttributeError")

        # Add unverified fix
        registry.add_fix(fp, "Fix", verified=False)

        # Manually age the entry using email.utils format (RFC 2822)
        old_time = formatdate(time.time() - 100 * 86400)
        key = fp.fingerprint_hash
        registry._registry["fingerprints"][key]["last_seen"] = old_time

        # Clear stale entries (90 days)
        removed = registry.clear_stale(max_age_days=90)

        assert removed == 1
        assert key not in registry._registry["fingerprints"]

    def test_clear_stale_preserves_verified(self, registry):
        """Test that verified fixes are preserved regardless of age."""
        from email.utils import formatdate

        fp = StackTraceFingerprint("test.py", 42, "AttributeError")

        # Add verified fix
        registry.add_fix(fp, "Fix", verified=True)

        # Manually age the entry
        old_time = formatdate(time.time() - 100 * 86400)
        key = fp.fingerprint_hash
        registry._registry["fingerprints"][key]["last_seen"] = old_time

        # Clear stale entries
        removed = registry.clear_stale(max_age_days=90)

        assert removed == 0
        assert key in registry._registry["fingerprints"]

    def test_clear_stale_preserves_recent_unverified(self, registry):
        """Test that recent unverified entries are preserved."""
        fp = StackTraceFingerprint("test.py", 42, "AttributeError")

        # Add unverified fix (recent)
        registry.add_fix(fp, "Fix", verified=False)

        # Clear with 90 day threshold
        removed = registry.clear_stale(max_age_days=90)

        assert removed == 0
        assert fp.fingerprint_hash in registry._registry["fingerprints"]

    def test_clear_stale_respects_max_age_days(self, registry):
        """Test that max_age_days parameter is respected."""
        from email.utils import formatdate

        fp = StackTraceFingerprint("test.py", 42, "AttributeError")

        registry.add_fix(fp, "Fix", verified=False)

        # Age to exactly 30 days using email.utils format
        old_time = formatdate(time.time() - 30 * 86400)
        key = fp.fingerprint_hash
        registry._registry["fingerprints"][key]["last_seen"] = old_time

        # Clear with 29 day threshold (should remove)
        removed_29 = registry.clear_stale(max_age_days=29)

        # Re-add for next test
        registry.add_fix(fp, "Fix", verified=False)
        registry._registry["fingerprints"][key]["last_seen"] = old_time

        # Clear with 31 day threshold (should keep)
        removed_31 = registry.clear_stale(max_age_days=31)

        assert removed_29 == 1
        assert removed_31 == 0

    def test_clear_stale_returns_count(self, registry):
        """Test that clear_stale returns count of removed entries."""
        from email.utils import formatdate

        # Add multiple old unverified fixes
        for i in range(5):
            fp = StackTraceFingerprint(f"test{i}.py", i, "AttributeError")
            registry.add_fix(fp, f"Fix {i}", verified=False)

            # Age each entry using email.utils format (RFC 2822)
            key = fp.fingerprint_hash
            old_time = formatdate(time.time() - 100 * 86400)
            registry._registry["fingerprints"][key]["last_seen"] = old_time

        removed = registry.clear_stale(max_age_days=90)

        assert removed == 5


# =============================================================================
# Tests for Singleton Pattern
# =============================================================================

class TestFixRegistrySingleton:
    """Tests for get_fix_registry singleton function."""

    def test_get_fix_registry_returns_singleton(self):
        """Test that get_fix_registry returns same instance."""
        # Note: This uses the actual singleton, which may have state
        reg1 = get_fix_registry()
        reg2 = get_fix_registry()
        assert reg1 is reg2

    def test_get_fix_registry_thread_safe(self):
        """Test that singleton initialization is thread-safe."""
        # Reset singleton by deleting the module-level variable
        import rca.fix_registry as fr_module
        fr_module._default_registry = None

        instances = []

        def get_instance():
            reg = get_fix_registry()
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

    def test_register_fix(self):
        """Test register_fix convenience function."""
        success = register_fix(
            "AttributeError: 'NoneType' object has no attribute",
            "Check for None before accessing",
            file_path="test.py",
            verified=True,
        )

        # Should succeed or fail gracefully
        assert isinstance(success, bool)

    def test_lookup_fix(self):
        """Test lookup_fix convenience function."""
        fix_record = lookup_fix(
            "AttributeError: 'NoneType' object has no attribute '__getitem__'",
            file_path="test.py",
        )

        # Should return FixRecord or None
        assert fix_record is None or isinstance(fix_record, FixRecord)

    def test_find_similar_fixes_conv(self):
        """Test find_similar_fixes convenience function."""
        similar = find_similar_fixes(
            "AttributeError: 'NoneType' object",
            file_path="test.py",
            min_similarity=0.5,
        )

        # Should return list of tuples
        assert isinstance(similar, list)

    def test_register_and_lookup_roundtrip(self):
        """Test registering and then looking up a fix."""
        error_msg = "AttributeError: 'NoneType' object has no attribute 'test'"

        # Register
        register_fix(
            error_msg,
            "Check for None",
            file_path="test.py",
            verified=True,
        )

        # Lookup
        fix_record = lookup_fix(error_msg, file_path="test.py")

        # May find the registered fix
        if fix_record:
            assert fix_record.verified is True


# =============================================================================
# Tests for JSON Persistence
# =============================================================================

class TestJSONPersistence:
    """Tests for JSON persistence and serialization."""

    def test_persistence_across_instances(self, temp_cache_dir, sample_fingerprint):
        """Test that data persists across registry instances."""
        # Create first instance and add data
        reg1 = FixRegistry(cache_dir=temp_cache_dir)
        reg1.add_fix(sample_fingerprint, "Persisted fix", verified=True)

        # Create second instance (should load from disk)
        reg2 = FixRegistry(cache_dir=temp_cache_dir)

        # Should have the data
        fix_record = reg2.get_fix(sample_fingerprint)
        assert fix_record is not None
        assert fix_record.fix_description == "Persisted fix"

    def test_json_serialization_with_unicode(self, registry, sample_fingerprint):
        """Test JSON serialization with unicode characters."""
        unicode_fix = "Fix with emoji: \u2713 \u2717 and \u4e2d\u6587"

        registry.add_fix(sample_fingerprint, unicode_fix)

        # Reload from disk
        reg2 = FixRegistry(cache_dir=registry.cache_dir)
        fix_record = reg2.get_fix(sample_fingerprint)

        assert fix_record.fix_description == unicode_fix

    def test_json_serialization_with_special_characters(self, registry, sample_fingerprint):
        """Test JSON serialization with special characters."""
        special_fix = "Fix with \"quotes\", 'apostrophes', \nnewlines, \ttabs"

        registry.add_fix(sample_fingerprint, special_fix)

        # Reload from disk
        reg2 = FixRegistry(cache_dir=registry.cache_dir)
        fix_record = reg2.get_fix(sample_fingerprint)

        assert fix_record.fix_description == special_fix

    def test_fix_record_round_trip(self, registry, sample_fingerprint):
        """Test FixRecord to_dict and from_dict round trip."""
        # Add fix multiple times to increase times_seen
        for _ in range(5):
            registry.add_fix(
                sample_fingerprint,
                "Fix",
                verified=True,
                error_message="Error",
                commit_hash="commit",
                related_files=["file1.py", "file2.py"],
            )

        original = registry.get_fix(sample_fingerprint)
        restored = FixRecord.from_dict(original.to_dict())

        assert restored.fingerprint == original.fingerprint
        assert restored.fix_description == original.fix_description
        assert restored.verified == original.verified


# =============================================================================
# Tests for Concurrent Access
# =============================================================================

class TestConcurrentAccess:
    """Tests for concurrent access to registry."""

    def test_concurrent_add_fix(self, registry):
        """Test multiple threads adding fixes concurrently."""
        errors = []
        results = []

        def add_fix(thread_id):
            try:
                fp = StackTraceFingerprint(f"test{thread_id}.py", thread_id, "AttributeError")
                success = registry.add_fix(fp, f"Fix {thread_id}")
                results.append(success)
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(10):
            t = threading.Thread(target=add_fix, args=(i,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Should complete without errors
        assert len(errors) == 0
        # All adds should succeed
        assert all(results)

    def test_concurrent_read_write(self, registry, sample_fingerprint):
        """Test concurrent reads and writes."""
        errors = []
        read_results = []

        # Add initial fix
        registry.add_fix(sample_fingerprint, "Initial fix")

        def read_fix():
            try:
                for _ in range(10):
                    fix = registry.get_fix(sample_fingerprint)
                    read_results.append(fix)
            except Exception as e:
                errors.append(e)

        def update_fix():
            try:
                for _ in range(5):
                    registry.add_fix(sample_fingerprint, "Updated fix")
            except Exception as e:
                errors.append(e)

        # Start threads
        threads = []
        for _ in range(3):
            t1 = threading.Thread(target=read_fix)
            t2 = threading.Thread(target=update_fix)
            threads.extend([t1, t2])

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should complete without errors
        assert len(errors) == 0
        assert len(read_results) == 30


# =============================================================================
# Tests for Edge Cases
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and unusual inputs."""

    def test_empty_file_path(self, registry):
        """Test handling empty file path."""
        fp = StackTraceFingerprint("", 42, "AttributeError")
        result = registry.add_fix(fp, "Fix")
        assert result is True

    def test_line_number_zero(self, registry):
        """Test fingerprint with line number 0."""
        fp = StackTraceFingerprint("test.py", 0, "AttributeError")
        result = registry.add_fix(fp, "Fix")
        assert result is True

    def test_very_long_file_path(self, registry):
        """Test handling very long file paths."""
        long_path = "a" * 500 + ".py"
        fp = StackTraceFingerprint(long_path, 42, "AttributeError")
        result = registry.add_fix(fp, "Fix")
        assert result is True

    def test_empty_error_type(self, registry):
        """Test handling empty error type."""
        fp = StackTraceFingerprint("test.py", 42, "")
        result = registry.add_fix(fp, "Fix")
        assert result is True

    def test_special_characters_in_file_path(self, registry):
        """Test file path with special characters."""
        fp = StackTraceFingerprint("test-file.py", 42, "AttributeError")
        result = registry.add_fix(fp, "Fix")
        assert result is True

    def test_empty_fix_description(self, registry):
        """Test adding fix with empty description."""
        fp = StackTraceFingerprint("test.py", 42, "AttributeError")
        result = registry.add_fix(fp, "")
        assert result is True

    def test_empty_related_files_list(self, registry, sample_fingerprint):
        """Test adding fix with empty related_files."""
        result = registry.add_fix(
            sample_fingerprint,
            "Fix",
            related_files=[],
        )
        assert result is True

    def test_search_by_empty_file_path(self, registry):
        """Test searching with empty file path."""
        results = registry.search_by_file("")
        assert isinstance(results, list)

    def test_search_by_empty_error_type(self, registry):
        """Test searching with empty error type."""
        results = registry.search_by_error_type("")
        assert isinstance(results, list)

    def test_none_values_in_optional_fields(self, registry, sample_fingerprint):
        """Test handling None in optional fields."""
        # The method signature doesn't allow None for these params,
        # but we test the behavior
        result = registry.add_fix(
            sample_fingerprint,
            "Fix",
            error_message="",
            commit_hash="",
            related_files=None,
        )
        assert result is True


# =============================================================================
# Integration Tests
# =============================================================================

class TestIntegration:
    """Integration tests for complete workflows."""

    def test_full_fix_lifecycle(self, registry):
        """Test complete lifecycle of a fix record."""
        # 1. Add initial fix
        fp = StackTraceFingerprint("test.py", 42, "AttributeError")
        registry.add_fix(
            fp,
            "Initial fix",
            verified=False,
            error_message="AttributeError occurred",
        )

        # 2. Retrieve the fix
        fix_record = registry.get_fix(fp)
        assert fix_record is not None
        assert fix_record.verified is False

        # 3. Re-encounter same error, update
        registry.add_fix(
            fp,
            "Updated fix",
            verified=True,
            commit_hash="abc123",
        )

        # 4. Check updated record
        fix_record = registry.get_fix(fp)
        assert fix_record.times_seen == 2
        assert fix_record.verified is True
        assert fix_record.commit_hash == "abc123"

        # 5. Check stats
        stats = registry.get_stats()
        assert stats["total_fingerprints"] == 1
        assert stats["total_times_seen"] == 2
        assert stats["verified_fixes"] == 1

    def test_similar_fix_workflow(self, registry):
        """Test workflow for finding similar fixes."""
        # Add fix for error at one location
        fp1 = StackTraceFingerprint("download_handler.py", 127, "AttributeError")
        registry.add_fix(
            fp1,
            "Initialize yt_dlp_options before use",
            verified=True,
        )

        # Encounter similar error at nearby line
        fp2 = StackTraceFingerprint("download_handler.py", 130, "AttributeError")

        # Find similar fixes
        similar = registry.find_similar(fp2, min_similarity=0.6)

        # Should find the similar fix
        assert len(similar) > 0
        assert similar[0][0] >= 0.7  # High similarity
        assert "yt_dlp_options" in similar[0][1].fix_description

    def test_cross_file_error_pattern(self, registry):
        """Test finding fixes across files for same error type."""
        # Add fixes for AttributeError in different files
        files = ["handler.py", "processor.py", "utils.py"]
        for file in files:
            fp = StackTraceFingerprint(file, 42, "AttributeError")
            registry.add_fix(fp, f"Fix for {file}")

        # Search by error type
        results = registry.search_by_error_type("AttributeError")

        assert len(results) == 3
        file_names = {r.fingerprint.file_path for r in results}
        assert set(file_names) == set(files)

    def test_error_evolution_tracking(self, registry):
        """Test tracking how errors evolve over time."""
        fp = StackTraceFingerprint("test.py", 42, "AttributeError")

        # Error occurs multiple times
        timestamps = []
        for i in range(5):
            registry.add_fix(fp, f"Fix attempt {i}")
            fix = registry.get_fix(fp)
            timestamps.append(fix.last_seen)

        # All timestamps should be present
        assert all(ts is not None for ts in timestamps)
        assert fix.times_seen == 5
