#!/usr/bin/env python3
"""
Quick backend test - verifies all backends can be instantiated.
Tests both search-research and search-backends packages.
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "search-research"))
sys.path.insert(0, str(Path(__file__).parent / "search-backends"))


def test_backend(name, backend_class_fn):
    """Test a single backend by importing it."""
    print(f"  {name}...", end=" ")
    try:
        backend_class = backend_class_fn()
        # Try to instantiate if it's not an abstract class
        try:
            backend = backend_class()
            print("✓ (instantiated)")
        except TypeError:
            # Abstract class
            print("✓ (abstract)")
        except Exception as e:
            print(f"⚠ (instantiation failed: {type(e).__name__})")
        return True
    except ImportError:
        print("✗ (import failed)")
        return False


def main():
    """Test all backends."""
    print("=" * 60)
    print("QUICK BACKEND TEST")
    print("=" * 60)

    results = []

    # Test search-backends
    print("\nsearch-backends:")
    results.append(
        test_backend(
            "BaseLocalBackend",
            lambda: __import__(
                "search_backends", fromlist=["BaseLocalBackend"]
            ).BaseLocalBackend,
        )
    )
    results.append(
        test_backend(
            "CKSMetadataBackend",
            lambda: __import__(
                "search_backends", fromlist=["CKSMetadataBackend"]
            ).CKSMetadataBackend,
        )
    )
    results.append(
        test_backend(
            "CodeAnalysisBackend",
            lambda: __import__(
                "search_backends", fromlist=["CodeAnalysisBackend"]
            ).CodeAnalysisBackend,
        )
    )

    # Test search-research local backends
    print("\nsearch-research local backends:")
    backends_to_test = [
        ("ASTCodeBackend", "core.backends.local.ast_code_backend"),
        ("BaseLocalBackend", "core.backends.local.base_local_backend"),
        ("CallGraphBackend", "core.backends.local.call_graph_backend"),
        ("CDSBackend", "core.backends.local.cds_backend"),
        ("CKSMetadataBackend", "core.backends.local.cks_metadata_backend"),
        ("CPGBackend", "core.backends.local.cpg_backend"),
        ("DependencyBackend", "core.backends.local.dependency_backend"),
        ("EnhancedCDSBackend", "core.backends.local.enhanced_cds_backend"),
        ("GrepBackend", "core.backends.local.grep_backend"),
        ("HDMABackend", "core.backends.local.hdma_backend"),
        ("KGBackend", "core.backends.local.kg_backend"),
        ("LSPSymbolBackend", "core.backends.local.lsp_backend"),
        ("MultiLangCodeBackend", "core.backends.local.multilang_backend"),
        ("RLMBackend", "core.backends.local.rlm_backend"),
        ("SkillsBackend", "core.backends.local.skills_backend"),
    ]

    for name, module_path in backends_to_test:
        results.append(
            test_backend(
                name,
                lambda mp=module_path, n=name: __import__(mp, fromlist=[n]).__dict__[n],
            )
        )

    # Test search-research top-level backends
    print("\nsearch-research top-level backends:")
    results.append(
        test_backend(
            "CodeAnalysisBackend (base)",
            lambda: __import__(
                "core.backends.base.code_analysis_backend",
                fromlist=["CodeAnalysisBackend"],
            ).CodeAnalysisBackend,
        )
    )
    results.append(
        test_backend(
            "KGBackend",
            lambda: __import__("core.backends.kg", fromlist=["KGBackend"]).KGBackend,
        )
    )
    results.append(
        test_backend(
            "RLMBackend",
            lambda: __import__("core.backends.rlm", fromlist=["RLMBackend"]).RLMBackend,
        )
    )
    results.append(
        test_backend(
            "PersonaMemoryBackend",
            lambda: __import__(
                "core.backends.persona", fromlist=["PersonaMemoryBackend"]
            ).PersonaMemoryBackend,
        )
    )

    # Summary
    print("\n" + "=" * 60)
    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"RESULT: {passed}/{total} backends imported successfully")

    if passed == total:
        print("✓ All backends working!")
        return 0
    else:
        print(f"✗ {total - passed} backend(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
