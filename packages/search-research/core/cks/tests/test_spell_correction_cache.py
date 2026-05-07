"""Tests for CKS Spell Correction Cache

TDD Approach: RED -> GREEN -> REFACTOR
Tests spell correction dictionary caching for performance.
"""

import time
from pathlib import Path

import pytest


def test_spell_correction_cache_performance():
    """Test that cached spell correction loads faster than rebuilding."""
    from ..spell_correction import QuerySpellCorrector
    from ..unified import CKS

    # Use existing CKS database for test
    cks = CKS()  # Uses default cks.db

    # Delete cache if exists to test first load
    cache_file = Path("P:\\\\__csf/data/symspell_cache.pkl")
    if cache_file.exists():
        cache_file.unlink()

    # First load - should build dictionary and create cache
    corrector1 = QuerySpellCorrector()
    start = time.time()
    corrector1.initialize(str(cks.db_path))
    first_load_time = time.time() - start

    # Verify cache was created after first load
    assert cache_file.exists(), "Cache file should be created after first load"

    # Get cache file size after first load
    cache_size_after_first = cache_file.stat().st_size
    assert (
        cache_size_after_first > 1000
    ), f"Cache file should have content, size: {cache_size_after_first}"

    # Second load - should use cache (faster)
    # Note the modification time shouldn't change if cache is used
    mod_time_before_second = cache_file.stat().st_mtime

    corrector2 = QuerySpellCorrector()
    start = time.time()
    corrector2.initialize(str(cks.db_path))
    second_load_time = time.time() - start

    mod_time_after_second = cache_file.stat().st_mtime

    # Cache file should NOT be rewritten on second load (mod time unchanged)
    assert (
        mod_time_before_second == mod_time_after_second
    ), "Cache file should not be rewritten on cached load"

    # Cached load should be significantly faster than rebuilding
    assert (
        second_load_time < first_load_time
    ), f"Cached load ({second_load_time:.2f}s) should be faster than rebuild ({first_load_time:.2f}s)"

    print(f"First load: {first_load_time:.2f}s, Cached load: {second_load_time:.2f}s")


def test_spell_correction_works():
    """Test that spell correction works correctly."""
    from ..spell_correction import QuerySpellCorrector
    from ..unified import CKS

    cks = CKS()
    corrector = QuerySpellCorrector()
    corrector.initialize(str(cks.db_path))

    # Test correction works
    corrected = corrector.correct_query("databse timeout")
    assert "database" in corrected.lower(), f"Expected 'database' in '{corrected}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
