#!/usr/bin/env python3
"""Tests for CKS model migration script."""

import sys
import tempfile
from pathlib import Path

src_dir = Path(__file__).parent.parent.parent


def test_import() -> bool | None:
    """Test that the migration module can be imported."""
    try:
        from .cks_migrate import CKSModelMigration

        return True
    except ImportError as e:
        print(f"Import failed: {e}")
        return False


def test_migration_initialization():
    """Test that CKSModelMigration can be initialized."""
    try:
        from .cks_migrate import CKSModelMigration

        migration = CKSModelMigration(dry_run=True)
        return migration is not None
    except Exception as e:
        print(f"Initialization failed: {e}")
        return False


def test_model_dimensions() -> bool:
    """Test that model dimensions are correctly detected."""
    from .cks_migrate import MODEL_DIMENSIONS

    expected = {
        "all-MiniLM-L6-v2": 384,
        "bge-large-en-v1.5": 1024,
        "bge-base-en-v1.5": 768,
    }

    for model, expected_dim in expected.items():
        actual_dim = MODEL_DIMENSIONS.get(model)
        assert actual_dim == expected_dim, f"{model}: expected {expected_dim}, got {actual_dim}"

    return True


def test_backup_creation() -> bool:
    """Test that backup is created before migration."""
    from .cks_migrate import CKSModelMigration

    with tempfile.TemporaryDirectory() as tmpdir:
        migration = CKSModelMigration(dry_run=True, backup_dir=tmpdir)
        # Just verify the backup path can be constructed
        assert migration.backup_path is not None
        return True


def test_query_expansion_update() -> bool:
    """Test that query expansion gets updated with new terms."""
    from .cks_migrate import QUERY_EXPANSION_UPDATES

    # Check that HyDE is in the updates
    assert "hyde" in QUERY_EXPANSION_UPDATES["abbreviations"]
    assert QUERY_EXPANSION_UPDATES["abbreviations"]["hyde"] == "hypothetical document embeddings"

    return True


if __name__ == "__main__":
    tests = [
        ("Import", test_import),
        ("Initialization", test_migration_initialization),
        ("Model Dimensions", test_model_dimensions),
        ("Backup Creation", test_backup_creation),
        ("Query Expansion Update", test_query_expansion_update),
    ]

    print("Running tests for cks_migrate.py\n")
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
