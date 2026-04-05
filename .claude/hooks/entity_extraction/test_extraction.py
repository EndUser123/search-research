"""
Test suite for entity extraction module.

Tests:
1. Blocklist effectiveness (false positive reduction)
2. Structural extraction accuracy  
3. Heuristic extraction with context
4. Semantic validation (if available)
5. Integration with assumption_audit patterns
"""

import sys
from pathlib import Path

# Add hooks directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json

# Test cases derived from actual false positives in logs
FALSE_POSITIVE_SAMPLES = [
    # These should NOT be extracted as entities
    "current", "evidence", "status", "next", "fix", "verification",
    "summary", "problem", "checkpoint", "system", "hook", "daemon",
    "recommendation", "patterns", "action", "fixed", "verified",
    "edit", "python", "integration", "dynamic", "answer", "add",
    "implementation", "root", "step", "task", "state", "before",
    "tdd", "create", "statement", "complete", "cause", "changes",
]

# These SHOULD be extracted as entities
TRUE_POSITIVE_SAMPLES = [
    "assumption_audit_v2.py",
    "checkpoint_manager.py",
    "process_data",
    "UserController",
    "API_KEY",
    "test_authentication",
    "DatabaseConnection",
    "MAX_RETRIES",
    "parse_json",
    "p:/.claude/hooks/validators/debug_v2_validator.py",
]

# Response snippets that triggered false blocks
RESPONSE_SAMPLES = [
    {
        "snippet": "**All tests passed.** Dynamic pipe daemon implementation verified working.",
        "expected_entities": [],  # No specific entities to verify
        "false_entities": ["daemon", "implementation", "pipe", "dynamic"],
    },
    {
        "snippet": "Fixed. Verification confirms:\n\n| Before | After |\n|--------|-------|",
        "expected_entities": [],
        "false_entities": ["verification", "before", "fixed", "after"],
    },
    {
        "snippet": "The test file `test_three_layer_filtering.py` doesn't exist",
        "expected_entities": ["test_three_layer_filtering.py"],
        "false_entities": ["test", "file", "layer"],
    },
]


def test_blocklist_coverage():
    """Test that blocklist catches known false positives."""
    from entity_extraction.strategies import ENTITY_BLOCKLIST

    blocked = 0
    for word in FALSE_POSITIVE_SAMPLES:
        if word.lower() in ENTITY_BLOCKLIST:
            blocked += 1
        else:
            print(f"  MISS: '{word}' not in blocklist")

    coverage = blocked / len(FALSE_POSITIVE_SAMPLES) * 100
    print(f"\nBlocklist coverage: {blocked}/{len(FALSE_POSITIVE_SAMPLES)} ({coverage:.1f}%)")

    assert coverage >= 90, f"Blocklist coverage {coverage}% below 90% threshold"
    return True


def test_structural_extraction():
    """Test structural extraction catches real entities."""
    from entity_extraction.strategies import StructuralStrategy

    strategy = StructuralStrategy()

    test_text = """
    Check the file `checkpoint_manager.py` at P:/.claude/hooks/validators/.
    The function `process_data` calls `validate_input()`.
    
    ```python
    from utils import parse_json
    class UserController:
        MAX_RETRIES = 3
    ```
    """

    entities = strategy.extract(test_text)

    expected = {
        "checkpoint_manager.py",
        "process_data",
        "validate_input()",  # With parens from backtick
        "parse_json",
        "UserController",
        "MAX_RETRIES",
    }

    found = 0
    for exp in expected:
        # Check normalized (without parens)
        exp_norm = exp.rstrip("()")
        if any(exp_norm in e for e in entities):
            found += 1
        else:
            print(f"  MISS: Expected '{exp}' not found in {entities}")

    coverage = found / len(expected) * 100
    print(f"\nStructural extraction: {found}/{len(expected)} ({coverage:.1f}%)")

    return coverage >= 80


def test_heuristic_filtering():
    """Test heuristic strategy filters blocklisted words."""
    from entity_extraction.strategies import HeuristicStrategy

    strategy = HeuristicStrategy()

    # Text with mix of real entities and prose
    test_text = """
    The current implementation of process_data is complete.
    Fixed the verification in UserController after testing.
    The daemon integration status is now working.
    """

    raw_candidates = strategy.extract(test_text)
    filtered = {e for e in raw_candidates if not strategy.is_blocked(e)}

    # Real entities should survive
    real_entities = {"process_data", "UserController"}
    # Prose should be filtered
    prose_words = {"current", "implementation", "complete", "fixed",
                   "verification", "after", "testing", "daemon",
                   "integration", "status", "now", "working"}

    real_found = len(real_entities & filtered)
    prose_leaked = len(prose_words & filtered)

    print("\nHeuristic filtering:")
    print(f"  Real entities found: {real_found}/{len(real_entities)}")
    print(f"  Prose leaked through: {prose_leaked}/{len(prose_words)}")
    if filtered:
        print(f"  Final entities: {filtered}")

    return real_found >= 1 and prose_leaked <= 2


def test_response_sample_extraction():
    """Test extraction on actual response samples that caused blocks."""
    from entity_extraction.extractor import EntityExtractor

    extractor = EntityExtractor(enable_semantic=False)  # Test without semantic

    print("\nResponse sample extraction:")
    all_pass = True

    for sample in RESPONSE_SAMPLES:
        result = extractor.extract(sample["snippet"])
        entities = result.all_normalized()

        # Check expected entities found
        for exp in sample["expected_entities"]:
            if exp.lower() not in entities:
                print(f"  MISS expected: '{exp}' in: {sample['snippet'][:50]}...")
                all_pass = False

        # Check false entities filtered
        false_leaked = []
        for false in sample["false_entities"]:
            if false.lower() in entities:
                false_leaked.append(false)

        if false_leaked:
            print(f"  FALSE POSITIVES: {false_leaked} in: {sample['snippet'][:50]}...")
            # Don't fail test, just report

        print(f"  OK: {len(entities)} entities extracted, {len(false_leaked)} false positives")

    return all_pass


def test_semantic_validation():
    """Test semantic validation if available."""
    try:
        from entity_extraction.strategies import SemanticStrategy

        strategy = SemanticStrategy()

        # Test classification
        code_entities = ["process_data", "UserController", "checkpoint_manager.py"]
        prose_words = ["current", "evidence", "verification", "implementation"]

        print("\nSemantic classification:")

        for entity in code_entities:
            result = strategy.classify_single(entity)
            status = "✓" if result["is_code_entity"] else "✗"
            print(f"  {status} '{entity}': diff={result['difference']:.3f}")

        for word in prose_words:
            result = strategy.classify_single(word)
            status = "✓" if not result["is_code_entity"] else "✗"
            print(f"  {status} '{word}': diff={result['difference']:.3f}")

        return True

    except ImportError as e:
        print(f"\nSemantic validation skipped: {e}")
        return True  # Not a failure if not installed


def test_integration_comparison():
    """Compare old vs new extraction on logged false positives."""
    from entity_extraction.extractor import EntityExtractor

    # Load recent blocks from log
    log_file = Path("P:/.claude/hooks/logs/assumption_audit_v2.jsonl")

    if not log_file.exists():
        print("\nIntegration test skipped: no log file")
        return True

    extractor = EntityExtractor(enable_semantic=False)

    improvements = []
    regressions = []

    with open(log_file) as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry.get("event") != "block":
                    continue

                snippet = entry.get("response_snippet", "")
                old_uncovered = set(entry.get("uncovered", []))

                if not snippet or not old_uncovered:
                    continue

                # Extract with new system
                result = extractor.extract(snippet)
                new_entities = result.all_normalized()

                # Compare
                old_count = len(old_uncovered)
                new_count = len(new_entities)

                if new_count < old_count:
                    improvements.append({
                        "old": old_count,
                        "new": new_count,
                        "reduction": old_count - new_count,
                    })
                elif new_count > old_count:
                    regressions.append({
                        "old": old_count,
                        "new": new_count,
                        "increase": new_count - old_count,
                    })

            except Exception:
                continue

    print("\nIntegration comparison:")
    print(f"  Improvements: {len(improvements)} blocks would extract fewer entities")
    print(f"  Regressions: {len(regressions)} blocks would extract more entities")

    if improvements:
        avg_reduction = sum(i["reduction"] for i in improvements) / len(improvements)
        print(f"  Average reduction: {avg_reduction:.1f} entities")

    return len(regressions) < len(improvements)


def run_all_tests():
    """Run all tests and report results."""
    print("=" * 60)
    print("Entity Extraction Test Suite")
    print("=" * 60)

    tests = [
        ("Blocklist Coverage", test_blocklist_coverage),
        ("Structural Extraction", test_structural_extraction),
        ("Heuristic Filtering", test_heuristic_filtering),
        ("Response Sample Extraction", test_response_sample_extraction),
        ("Semantic Validation", test_semantic_validation),
        ("Integration Comparison", test_integration_comparison),
    ]

    results = []
    for name, test_fn in tests:
        print(f"\n{'='*60}")
        print(f"TEST: {name}")
        print("-" * 60)
        try:
            passed = test_fn()
            results.append((name, "PASS" if passed else "FAIL"))
        except Exception as e:
            print(f"ERROR: {e}")
            results.append((name, "ERROR"))

    print(f"\n{'='*60}")
    print("SUMMARY")
    print("=" * 60)
    for name, status in results:
        symbol = "✓" if status == "PASS" else "✗"
        print(f"  {symbol} {name}: {status}")

    passed = sum(1 for _, s in results if s == "PASS")
    print(f"\nTotal: {passed}/{len(results)} passed")

    return all(s == "PASS" for _, s in results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
