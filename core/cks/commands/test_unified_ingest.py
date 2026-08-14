#!/usr/bin/env python3
"""Tests for unified_ingest.py."""

import sys
from pathlib import Path

src_dir = Path(__file__).parent.parent.parent


def test_import() -> bool | None:
    """Test that the module can be imported."""
    try:
        from .unified_ingest import UnifiedCKSIngestion

        return True
    except ImportError as e:
        print(f"Import failed: {e}")
        return False


def test_initialization():
    """Test that UnifiedCKSIngestion can be initialized."""
    try:
        from .unified_ingest import UnifiedCKSIngestion

        ingestion = UnifiedCKSIngestion(enable_semantic=False)
        return ingestion is not None
    except Exception as e:
        print(f"Initialization failed: {e}")
        return False


def test_extract_title() -> bool:
    """Test title extraction from content."""
    from .unified_ingest import UnifiedCKSIngestion

    ingestion = UnifiedCKSIngestion(enable_semantic=False)

    # Test markdown header
    content = "# My Title\n\nSome content"
    title = ingestion._extract_title(content, Path("test.md"))
    assert title == "My Title", f"Expected 'My Title', got '{title}'"

    # Test filename fallback
    content = "No header here"
    title = ingestion._extract_title(content, Path("my_test_file.md"))
    assert "My Test File" in title, f"Expected filename-based title, got '{title}'"

    return True


def test_ingest_pattern() -> bool:
    """Test pattern ingestion."""
    from .unified_ingest import UnifiedCKSIngestion

    ingestion = UnifiedCKSIngestion(enable_semantic=False)

    result = ingestion.ingest_pattern(
        title="Test Pattern",
        content="This is a test pattern for unified ingestion.",
        entry_type="pattern",
        tags=["test", "unified"],
    )

    assert result["status"] == "success", f"Expected success, got {result}"
    assert "entry_id" in result, "Expected entry_id in result"
    print(f"Created entry: {result['entry_id']}")

    return True


def test_search() -> bool:
    """Test search functionality."""
    from .unified_ingest import UnifiedCKSIngestion

    ingestion = UnifiedCKSIngestion(enable_semantic=False)

    results = ingestion.search("test pattern", semantic=False, limit=5)

    assert isinstance(results, list), "Expected list of results"
    print(f"Found {len(results)} results")

    return True


if __name__ == "__main__":
    tests = [
        ("Import", test_import),
        ("Initialization", test_initialization),
        ("Extract Title", test_extract_title),
        ("Ingest Pattern", test_ingest_pattern),
        ("Search", test_search),
    ]

    print("Running tests for unified_ingest.py\n")
    print("=" * 50)

    failed = []
    for name, test_func in tests:
        print(f"\nTest: {name}")
        try:
            result = test_func()
            if result:
                print("  ✅ PASSED")
            else:
                print("  ❌ FAILED")
                failed.append(name)
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            failed.append(name)

    print("\n" + "=" * 50)
    if failed:
        print(f"\n❌ {len(failed)} test(s) failed: {', '.join(failed)}")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)
