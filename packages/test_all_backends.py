#!/usr/bin/env python3
"""
Comprehensive backend test - verifies all backends can be instantiated and searched.
Tests both search-research and search-backends packages.
"""

import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "search-research"))
sys.path.insert(0, str(Path(__file__).parent / "search-backends"))

# Test results tracking
results = []


def test_backend(
    name, backend_class, can_instantiate=True, can_search=False, skip_search=False
):
    """Test a single backend."""
    print(f"\n{name}:")
    try:
        backend = None

        # Test instantiation
        if can_instantiate:
            backend = backend_class()
            print("  ✓ Instantiated")
        else:
            print("  ⊘ Skipped instantiation (base class)")
            backend = None

        # Test search
        if can_search and backend and not skip_search:
            search_results = backend.search("test", limit=1)
            print(f"  ✓ search() returned {type(search_results).__name__}")
        elif skip_search:
            print("  ⊘ Skipped search (may hang or requires external services)")
        elif can_search and not backend:
            print("  ⊘ Skipped search (requires instantiation)")
        else:
            print("  ⊘ Skipped search (base/abstract class)")

        return True
    except Exception as e:
        print(f"  ✗ Failed: {type(e).__name__}: {e}")
        return False


def main():
    """Test all backends."""
    print("=" * 80)
    print("COMPREHENSIVE BACKEND TEST")
    print("=" * 80)

    # Import search-backends
    print("\n--- search-backends Package ---")
    try:
        from search_backends import (
            BaseLocalBackend,
            CKSMetadataBackend,
            CodeAnalysisBackend,
        )

        print("✓ search-backends imports successful")

        # Test search-backends
        results.append(
            (
                "search-backends: BaseLocalBackend",
                test_backend(
                    "BaseLocalBackend",
                    BaseLocalBackend,
                    can_instantiate=False,
                    can_search=False,
                ),
            )
        )
        results.append(
            (
                "search-backends: CKSMetadataBackend",
                test_backend(
                    "CKSMetadataBackend",
                    CKSMetadataBackend,
                    can_instantiate=True,
                    can_search=True,
                ),
            )
        )
        results.append(
            (
                "search-backends: CodeAnalysisBackend",
                test_backend(
                    "CodeAnalysisBackend",
                    CodeAnalysisBackend,
                    can_instantiate=False,
                    can_search=False,
                ),
            )
        )

    except ImportError as e:
        print(f"✗ search-backends import failed: {e}")
        results.append(("search-backends imports", False))

    # Import search-research backends
    print("\n--- search-research Package ---")
    try:
        from core.backends.base.code_analysis_backend import (
            CodeAnalysisBackend as CoreCodeAnalysisBackend,
        )
        from core.backends.kg import KGBackend as CoreKGBackend
        from core.backends.local.ast_code_backend import ASTCodeBackend
        from core.backends.local.base_local_backend import (
            BaseLocalBackend as CoreBaseLocalBackend,
        )
        from core.backends.local.call_graph_backend import CallGraphBackend
        from core.backends.local.cds_backend import CDSBackend
        from core.backends.local.cks_metadata_backend import (
            CKSMetadataBackend as CoreCKSMetadataBackend,
        )
        from core.backends.local.cpg_backend import CPGBackend
        from core.backends.local.dependency_backend import DependencyBackend
        from core.backends.local.enhanced_cds_backend import EnhancedCDSBackend
        from core.backends.local.grep_backend import GrepBackend
        from core.backends.local.hdma_backend import HDMABackend
        from core.backends.local.kg_backend import KGBackend
        from core.backends.local.lsp_backend import LSPSymbolBackend
        from core.backends.local.multilang_backend import MultiLangCodeBackend
        from core.backends.local.rlm_backend import RLMBackend
        from core.backends.local.skills_backend import SkillsBackend
        from core.backends.persona import PersonaMemoryBackend
        from core.backends.rlm import RLMBackend as CoreRLMBackend

        print("✓ search-research backend imports successful")

        # Test base/abstract classes
        results.append(
            (
                "core: CodeAnalysisBackend",
                test_backend(
                    "CodeAnalysisBackend",
                    CoreCodeAnalysisBackend,
                    can_instantiate=False,
                    can_search=False,
                ),
            )
        )
        results.append(
            (
                "core: BaseLocalBackend",
                test_backend(
                    "BaseLocalBackend",
                    CoreBaseLocalBackend,
                    can_instantiate=False,
                    can_search=False,
                ),
            )
        )

        # Test concrete local backends
        results.append(
            (
                "core: ASTCodeBackend",
                test_backend(
                    "ASTCodeBackend",
                    ASTCodeBackend,
                    can_instantiate=True,
                    can_search=True,
                ),
            )
        )
        results.append(
            (
                "core: CallGraphBackend",
                test_backend(
                    "CallGraphBackend",
                    CallGraphBackend,
                    can_instantiate=True,
                    can_search=True,
                ),
            )
        )
        results.append(
            (
                "core: CDSBackend",
                test_backend(
                    "CDSBackend", CDSBackend, can_instantiate=True, can_search=True
                ),
            )
        )
        results.append(
            (
                "core: CKSMetadataBackend",
                test_backend(
                    "CKSMetadataBackend",
                    CoreCKSMetadataBackend,
                    can_instantiate=True,
                    can_search=True,
                ),
            )
        )
        results.append(
            (
                "core: CPGBackend",
                test_backend(
                    "CPGBackend", CPGBackend, can_instantiate=True, can_search=True
                ),
            )
        )
        results.append(
            (
                "core: DependencyBackend",
                test_backend(
                    "DependencyBackend",
                    DependencyBackend,
                    can_instantiate=True,
                    can_search=True,
                ),
            )
        )
        results.append(
            (
                "core: EnhancedCDSBackend",
                test_backend(
                    "EnhancedCDSBackend",
                    EnhancedCDSBackend,
                    can_instantiate=True,
                    can_search=True,
                ),
            )
        )
        results.append(
            (
                "core: GrepBackend",
                test_backend(
                    "GrepBackend", GrepBackend, can_instantiate=True, can_search=True
                ),
            )
        )
        results.append(
            (
                "core: HDMABackend",
                test_backend(
                    "HDMABackend", HDMABackend, can_instantiate=True, can_search=True
                ),
            )
        )
        results.append(
            (
                "core: KGBackend (local)",
                test_backend(
                    "KGBackend (local)",
                    KGBackend,
                    can_instantiate=True,
                    can_search=True,
                ),
            )
        )
        results.append(
            (
                "core: LSPSymbolBackend",
                test_backend(
                    "LSPSymbolBackend",
                    LSPSymbolBackend,
                    can_instantiate=True,
                    can_search=True,
                ),
            )
        )
        results.append(
            (
                "core: MultiLangCodeBackend",
                test_backend(
                    "MultiLangCodeBackend",
                    MultiLangCodeBackend,
                    can_instantiate=True,
                    can_search=True,
                ),
            )
        )
        results.append(
            (
                "core: RLMBackend (local)",
                test_backend(
                    "RLMBackend (local)",
                    RLMBackend,
                    can_instantiate=True,
                    can_search=True,
                ),
            )
        )
        results.append(
            (
                "core: SkillsBackend",
                test_backend(
                    "SkillsBackend",
                    SkillsBackend,
                    can_instantiate=True,
                    can_search=True,
                ),
            )
        )

        # Test top-level backends
        results.append(
            (
                "core: KGBackend (top-level)",
                test_backend(
                    "KGBackend (top-level)",
                    CoreKGBackend,
                    can_instantiate=True,
                    can_search=True,
                ),
            )
        )
        results.append(
            (
                "core: RLMBackend (top-level)",
                test_backend(
                    "RLMBackend (top-level)",
                    CoreRLMBackend,
                    can_instantiate=True,
                    can_search=True,
                ),
            )
        )
        results.append(
            (
                "core: PersonaMemoryBackend",
                test_backend(
                    "PersonaMemoryBackend",
                    PersonaMemoryBackend,
                    can_instantiate=True,
                    can_search=True,
                ),
            )
        )

    except ImportError as e:
        print(f"✗ search-research backend import failed: {e}")
        results.append(("search-research backend imports", False))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} backends tested")

    if passed == total:
        print("\n✓ All backends working!")
        return 0
    else:
        print(f"\n✗ {total - passed} backend(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
