#!/usr/bin/env python3
"""
Test Suite for PRD Registry (Lazy Loading & Caching)

Tests the lazy loading, caching, thread-safety, and file watching features
of the PRDRegistry.

Author: Claude Code
Version: 1.0.0
"""

import concurrent.futures

# Import module to test
import sys
import tempfile
import time
from pathlib import Path
from unittest import mock

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from registry import (
    PRDCacheEntry,
    PRDRegistry,
    create_registry,
)

# Fixtures

@pytest.fixture
def sample_prd_content():
    """Sample PRD content for testing."""
    return """---
prd_name: test_project
version: 1.0.0
---

# Requirements

#### **FR-1:** First Requirement
*   Description of first requirement.

#### **FR-2:** Second Requirement
*   Description of second requirement.

#### **NFR-1:** Performance Requirement
*   System must be fast.
"""


@pytest.fixture
def temp_prd_dir(sample_prd_content):
    """Create temporary directory with sample PRD files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create multiple PRD files
        projects = ["project_a", "project_b", "project_c"]

        for project in projects:
            project_dir = tmpdir / project / "docs"
            project_dir.mkdir(parents=True, exist_ok=True)

            prd_file = project_dir / "PRD.md"
            content = sample_prd_content.replace("test_project", project)
            prd_file.write_text(content, encoding='utf-8')

        yield tmpdir


@pytest.fixture
def registry(temp_prd_dir):
    """Create a PRD registry for testing."""
    pattern = str(temp_prd_dir / "*/docs/PRD.md")
    reg = PRDRegistry(
        prd_paths=[pattern],
        cache_size=10,
        ttl_seconds=None,
        base_path=str(temp_prd_dir),
    )
    reg.discover()
    return reg


# Discovery Tests

def test_discover_prds(registry, temp_prd_dir):
    """Test PRD discovery finds all files."""
    prd_names = registry.list_prds()

    assert len(prd_names) == 3
    assert "project_a" in prd_names
    assert "project_b" in prd_names
    assert "project_c" in prd_names


def test_discover_with_custom_paths(temp_prd_dir):
    """Test discovery with custom paths."""
    pattern = str(temp_prd_dir / "project_a/docs/PRD.md")
    reg = PRDRegistry(prd_paths=[pattern], base_path=str(temp_prd_dir))

    count = reg.discover()

    assert count == 1
    assert "project_a" in reg.list_prds()


def test_discover_empty_registry():
    """Test discovery when no paths configured."""
    reg = PRDRegistry()
    count = reg.discover()

    assert count == 0


def test_list_prds_loaded_only(registry):
    """Test listing only loaded PRDs."""
    all_prds = registry.list_prds()
    loaded = registry.list_prds(loaded_only=True)

    assert len(all_prds) == 3
    assert len(loaded) == 0

    # Load one PRD
    registry.get("project_a")

    loaded = registry.list_prds(loaded_only=True)
    assert len(loaded) == 1
    assert "project_a" in loaded


# Lazy Loading Tests

def test_lazy_loading_on_get(registry):
    """Test PRDs are loaded lazily on first get."""
    assert not registry.is_loaded("project_a")

    prd = registry.get("project_a")

    assert prd is not None
    assert registry.is_loaded("project_a")
    assert prd.prd_name == "project_a"


def test_lazy_loading_statistics(registry):
    """Test lazy loading affects statistics correctly."""
    stats = registry.get_stats()

    assert stats.total_prds == 3
    assert stats.loaded_prds == 0

    # Load first PRD
    registry.get("project_a")
    stats = registry.get_stats()

    assert stats.loaded_prds == 1
    assert stats.cache_misses == 1
    assert stats.cache_hits == 0


def test_get_unknown_prd(registry):
    """Test getting unknown PRD returns None."""
    prd = registry.get("nonexistent")

    assert prd is None


def test_get_by_path(temp_prd_dir):
    """Test loading PRD by direct path."""
    prd_path = temp_prd_dir / "project_a" / "docs" / "PRD.md"
    reg = PRDRegistry(base_path=str(temp_prd_dir))

    prd = reg.get_by_path(str(prd_path))

    assert prd is not None
    assert "project_a" in reg.list_prds()


# Caching Tests

def test_cache_hit_on_second_get(registry):
    """Test cache hit on subsequent gets."""
    # First get - cache miss
    prd1 = registry.get("project_a")
    stats = registry.get_stats()

    assert stats.cache_misses == 1
    assert stats.cache_hits == 0

    # Second get - cache hit
    prd2 = registry.get("project_a")
    stats = registry.get_stats()

    assert stats.cache_hits == 1
    assert stats.cache_misses == 1
    assert prd1 is prd2  # Same object reference


def test_cache_invalidation(registry):
    """Test manual cache invalidation."""
    registry.get("project_a")
    assert registry.is_loaded("project_a")

    invalidated = registry.invalidate("project_a")

    assert invalidated is True
    assert not registry.is_loaded("project_a")


def test_cache_invalidation_unknown(registry):
    """Test invalidating unknown PRD returns False."""
    result = registry.invalidate("unknown")

    assert result is False


def test_clear_cache(registry):
    """Test clearing all cache entries."""
    registry.get("project_a")
    registry.get("project_b")

    assert len(registry.list_prds(loaded_only=True)) == 2

    cleared = registry.clear_cache()

    assert cleared == 2
    assert len(registry.list_prds(loaded_only=True)) == 0


def test_lru_eviction(temp_prd_dir):
    """Test LRU eviction when cache is full."""
    reg = PRDRegistry(
        prd_paths=[str(temp_prd_dir / "*/docs/PRD.md")],
        cache_size=2,  # Small cache to force eviction
        base_path=str(temp_prd_dir),
    )
    reg.discover()

    # Load first PRD
    prd_a = reg.get("project_a")
    assert reg.is_loaded("project_a")

    # Load second PRD
    prd_b = reg.get("project_b")
    assert reg.is_loaded("project_a")
    assert reg.is_loaded("project_b")

    # Load third PRD - should evict project_a (least recently used)
    prd_c = reg.get("project_c")

    assert reg.is_loaded("project_b")
    assert reg.is_loaded("project_c")
    assert not reg.is_loaded("project_a")

    stats = reg.get_stats()
    assert stats.evictions >= 1


def test_ttl_expiration(temp_prd_dir, sample_prd_content):
    """Test TTL-based cache expiration."""
    reg = PRDRegistry(
        prd_paths=[str(temp_prd_dir / "*/docs/PRD.md")],
        cache_size=10,
        ttl_seconds=0.1,  # Very short TTL
        base_path=str(temp_prd_dir),
    )
    reg.discover()

    # Load PRD
    prd1 = reg.get("project_a")
    assert prd1 is not None
    assert reg.is_loaded("project_a")

    # Wait for TTL to expire
    time.sleep(0.15)

    # Try to get again - should reload
    prd2 = reg.get("project_a")

    assert prd2 is not None
    # Objects should be different (reloaded after TTL expiration)
    assert prd1 is not prd2


def test_cache_entry_touch(temp_prd_dir):
    """Test cache entry updates access time on touch."""
    from datetime import datetime

    entry = PRDCacheEntry(
        prd=mock.Mock(),
        loaded_at=datetime.now(),
        last_accessed=datetime.now(),
        file_hash="abc123",
    )

    old_access_count = entry.access_count
    old_last_accessed = entry.last_accessed

    time.sleep(0.01)
    entry.touch()

    assert entry.access_count == old_access_count + 1
    assert entry.last_accessed > old_last_accessed


def test_stale_eviction(registry):
    """Test eviction of idle PRDs."""
    # Load all PRDs
    registry.preload()

    # Access project_a to make it recently used
    time.sleep(0.01)
    registry.get("project_a")

    # Evict PRDs idle for more than 0.005 seconds
    # project_b and project_c should be evicted (not accessed recently)
    evicted = registry.evict_stale(max_idle_seconds=0.005)

    assert evicted >= 2
    assert registry.is_loaded("project_a")


# Preloading Tests

def test_preload_all(registry):
    """Test preloading all discovered PRDs."""
    loaded_count = registry.preload()

    assert loaded_count == 3
    assert len(registry.list_prds(loaded_only=True)) == 3


def test_preload_specific(registry):
    """Test preloading specific PRDs."""
    loaded_count = registry.preload(["project_a", "project_b"])

    assert loaded_count == 2
    assert registry.is_loaded("project_a")
    assert registry.is_loaded("project_b")
    assert not registry.is_loaded("project_c")


# Thread Safety Tests

def test_concurrent_loading(registry):
    """Test thread-safe concurrent loading."""
    prd_name = "project_a"
    num_threads = 10

    def load_prd():
        return registry.get(prd_name)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(load_prd) for _ in range(num_threads)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # All threads should get valid PRDs
    assert all(r is not None for r in results)

    # Should only load once (cache hits for others)
    stats = registry.get_stats()
    assert stats.loaded_prds == 1
    assert stats.cache_misses == 1
    assert stats.cache_hits == num_threads - 1


def test_concurrent_different_prds(registry):
    """Test thread-safe loading of different PRDs."""
    prd_names = ["project_a", "project_b", "project_c"]

    def load_prd(name):
        return registry.get(name)

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(load_prd, name)
            for name in prd_names * 3  # Repeat 3 times
        ]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert all(r is not None for r in results)

    stats = registry.get_stats()
    assert stats.loaded_prds == 3  # Each PRD loaded once


# Statistics Tests

def test_statistics_tracking(registry):
    """Test statistics are tracked correctly."""
    # Load PRDs
    registry.get("project_a")
    registry.get("project_a")  # Cache hit
    registry.get("project_b")

    stats = registry.get_stats()

    assert stats.total_prds == 3
    assert stats.loaded_prds == 2
    assert stats.cache_hits == 1
    assert stats.cache_misses == 2
    # 1 hit / (1 hit + 2 misses) = 1/3 = 0.333
    assert stats.cache_hit_rate() == pytest.approx(0.333, abs=0.01)


def test_average_load_time(registry):
    """Test average load time calculation."""
    registry.get("project_a")
    registry.get("project_b")

    stats = registry.get_stats()

    assert stats.loaded_prds == 2
    assert stats.total_load_time > 0
    assert stats.avg_load_time > 0
    assert stats.avg_load_time == stats.total_load_time / stats.loaded_prds


def test_cache_info(registry):
    """Test getting cache info for specific PRD."""
    registry.get("project_a")

    info = registry.get_cache_info("project_a")

    assert info is not None
    assert info["prd_name"] == "project_a"
    assert info["access_count"] == 1
    assert "age_seconds" in info
    assert "idle_seconds" in info


def test_cache_info_not_loaded(registry):
    """Test cache info returns None for unloaded PRD."""
    info = registry.get_cache_info("project_a")

    assert info is None


def test_get_loaded_prds_info(registry):
    """Test getting info for all loaded PRDs."""
    registry.preload(["project_a", "project_b"])

    info_list = registry.get_loaded_prds_info()

    assert len(info_list) == 2
    assert any(i["prd_name"] == "project_a" for i in info_list)
    assert any(i["prd_name"] == "project_b" for i in info_list)


# File Watching Tests

def test_file_change_detection(temp_prd_dir, sample_prd_content):
    """Test that file changes are detected."""
    prd_path = temp_prd_dir / "project_a" / "docs" / "PRD.md"

    reg = PRDRegistry(
        prd_paths=[str(temp_prd_dir / "*/docs/PRD.md")],
        cache_size=10,
        enable_file_watching=True,
        base_path=str(temp_prd_dir),
    )
    reg.discover()

    # Load PRD
    prd1 = reg.get("project_a")
    req_count_1 = prd1.total_requirements

    # Modify file
    time.sleep(0.01)  # Ensure different mtime
    modified_content = sample_prd_content + "\n\n#### **FR-3:** New Requirement\n"
    prd_path.write_text(modified_content)

    # Get again - should detect change and reload
    prd2 = reg.get("project_a")

    assert prd2.total_requirements > req_count_1


def test_file_watching_disabled(temp_prd_dir, sample_prd_content):
    """Test that file watching can be disabled."""
    prd_path = temp_prd_dir / "project_a" / "docs" / "PRD.md"

    reg = PRDRegistry(
        prd_paths=[str(temp_prd_dir / "*/docs/PRD.md")],
        cache_size=10,
        enable_file_watching=False,  # Disabled
        base_path=str(temp_prd_dir),
    )
    reg.discover()

    # Load PRD
    prd1 = reg.get("project_a")

    # Modify file
    time.sleep(0.01)
    prd_path.write_text(sample_prd_content + "\n\n#### **FR-3:** New Requirement\n")

    # Get again - should NOT detect change
    prd2 = reg.get("project_a", force_reload=False)

    # Should get same cached object
    assert prd1 is prd2


# Search Tests

def test_search_requirements_titles(registry):
    """Test searching requirement titles."""
    results = registry.search_requirements(
        "First",
        search_titles=True,
        search_descriptions=False,
        loaded_only=False,
    )

    assert len(results) >= 1
    assert any("project_a" in r for r, _, _ in results)


def test_search_requirements_all(registry):
    """Test searching both titles and descriptions."""
    results = registry.search_requirements(
        "requirement",
        search_titles=True,
        search_descriptions=True,
        loaded_only=False,
    )

    assert len(results) > 0


def test_search_requirements_case_sensitive(registry):
    """Test case-sensitive search."""
    results_lower = registry.search_requirements(
        "first",
        case_sensitive=False,
        loaded_only=False,
    )

    results_upper = registry.search_requirements(
        "First",
        case_sensitive=False,
        loaded_only=False,
    )

    # Case-insensitive should find same results
    assert len(results_lower) == len(results_upper)


def test_search_loaded_only(registry):
    """Test searching only loaded PRDs."""
    # Don't preload - search loaded only
    results = registry.search_requirements(
        "requirement",
        loaded_only=True,
    )

    assert len(results) == 0

    # Load one PRD
    registry.get("project_a")

    results = registry.search_requirements(
        "requirement",
        loaded_only=True,
    )

    assert len(results) > 0


# Iteration Tests

def test_iterate_loaded_prds(registry):
    """Test iterating over loaded PRDs."""
    registry.preload(["project_a", "project_b"])

    loaded_names = []
    for name, prd in registry.iterate_loaded_prds():
        loaded_names.append(name)
        assert prd is not None

    assert len(loaded_names) == 2
    assert "project_a" in loaded_names
    assert "project_b" in loaded_names


def test_iterate_updates_access_time(registry):
    """Test that iteration updates access times."""
    registry.get("project_a")

    info_before = registry.get_cache_info("project_a")
    count_before = info_before["access_count"]

    time.sleep(0.01)

    # Iterate
    for _, _ in registry.iterate_loaded_prds():
        pass

    info_after = registry.get_cache_info("project_a")

    assert info_after["access_count"] > count_before


# Force Reload Tests

def test_force_reload(registry):
    """Test force_reload parameter."""
    prd1 = registry.get("project_a")
    assert prd1 is not None

    # Force reload should create new object
    prd2 = registry.get("project_a", force_reload=True)

    assert prd2 is not None
    assert prd1 is not prd2  # Different objects after force reload


# Edge Cases

def test_empty_registry():
    """Test registry with no PRDs."""
    reg = PRDRegistry(prd_paths=[])

    assert len(reg.list_prds()) == 0
    assert reg.get("anything") is None


def test_invalid_prd_path(temp_prd_dir):
    """Test handling of invalid PRD path."""
    reg = PRDRegistry(
        prd_paths=["nonexistent/*/PRD.md"],
        base_path=str(temp_prd_dir),
    )

    count = reg.discover()

    assert count == 0


def test_prd_name_inference(temp_prd_dir, sample_prd_content):
    """Test PRD name inference from path."""
    # Create PRD in non-standard location
    custom_dir = temp_prd_dir / "custom_location"
    custom_dir.mkdir()
    prd_file = custom_dir / "my_project.md"
    prd_file.write_text(sample_prd_content)

    reg = PRDRegistry(base_path=str(temp_prd_dir))
    reg.get_by_path(str(prd_file))

    # When PRD is directly in a directory (not in docs/),
    # the parent directory name is used
    assert "custom_location" in reg.list_prds()


# Convenience Functions

def test_create_registry(temp_prd_dir):
    """Test create_registry convenience function."""
    pattern = str(temp_prd_dir / "*/docs/PRD.md")

    reg = create_registry(
        prd_paths=[pattern],
        cache_size=50,
    )

    assert isinstance(reg, PRDRegistry)
    assert len(reg.list_prds()) == 3


# Run tests
if __name__ == "__main__":
    # Run pytest with verbose output
    import sys
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
