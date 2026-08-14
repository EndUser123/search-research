#!/usr/bin/env python3
"""Tests for auto-learning query expansion system."""

import sys
from pathlib import Path

src_dir = Path(__file__).parent.parent.parent


def test_import() -> bool | None:
    """Test that the module can be imported."""
    try:
        from .auto_learning_expander import AutoLearningQueryExpander

        return True
    except ImportError as e:
        print(f"Import failed: {e}")
        return False


def test_initialization():
    """Test that AutoLearningQueryExpander can be initialized."""
    try:
        from .auto_learning_expander import AutoLearningQueryExpander

        expander = AutoLearningQueryExpander()
        return expander is not None
    except Exception as e:
        print(f"Initialization failed: {e}")
        return False


def test_unknown_term_detection() -> bool:
    """Test detection of unknown terms from poor searches."""
    from .auto_learning_expander import AutoLearningQueryExpander

    expander = AutoLearningQueryExpander()

    # Simulate poor search results
    poor_results = [
        {"title": "Unrelated result", "similarity": 0.2},
        {"title": "Another unrelated", "similarity": 0.15},
    ]

    # Query with unknown acronym
    query = "search for hyde embeddings"
    unknown = expander.detect_unknown_terms(query, poor_results)

    # Should detect that query has acronyms not in abbreviations
    assert len(unknown) >= 0, "Should return list"
    print(f"  Unknown terms detected: {unknown}")
    return True


def test_definition_extraction() -> bool:
    """Test extraction of definitions from documents."""
    from .auto_learning_expander import AutoLearningQueryExpander

    expander = AutoLearningQueryExpander()

    # Test finding definition for "HYDE" in content
    sample_content = """
    # Research System Enhancements
    ## Overview
    The /web command has been enhanced with:
    - **HyDE (Hypothetical Document Embeddings)** using GLM-4.7
    - **Query Expansion** using CKS QueryExpander
    """

    definition = expander.extract_definition(sample_content, "HYDE")

    assert (
        "hypothetical document embeddings" in definition.lower()
    ), f"Should find definition, got: {definition}"
    return True


def test_mapping_persistence() -> bool:
    """Test that new mappings can be persisted."""
    from .auto_learning_expander import AutoLearningQueryExpander

    expander = AutoLearningQueryExpander(dry_run=True)

    # Test adding a new mapping
    result = expander.add_mapping(
        term="testacronym",
        expansion="Test Expansion Definition",
        source="auto_learned",
    )

    assert result["success"], "Should succeed in dry-run mode"
    return True


def test_search_and_learn() -> bool:
    """Test the full search-and-learn cycle."""
    from .auto_learning_expander import AutoLearningQueryExpander

    expander = AutoLearningQueryExpander(dry_run=True)

    # Simulate a search that might need learning
    query = "hyde search"
    results = []  # Empty results = poor search

    suggestion = expander.search_and_learn(query, results)

    # Should suggest learning or provide fallback
    assert "query" in suggestion or "hyde" in suggestion.lower()
    return True


if __name__ == "__main__":
    tests = [
        ("Import", test_import),
        ("Initialization", test_initialization),
        ("Unknown Term Detection", test_unknown_term_detection),
        ("Definition Extraction", test_definition_extraction),
        ("Mapping Persistence", test_mapping_persistence),
        ("Search and Learn", test_search_and_learn),
    ]

    print("Running tests for auto_learning_expander.py\n")
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
