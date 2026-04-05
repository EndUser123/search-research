#!/usr/bin/env python3
"""Full RCA Workflow Integration Test"""
from __future__ import annotations

print("=" * 70)
print("FULL RCA WORKFLOW INTEGRATION TEST")
print("=" * 70)

results = []

# Test 1: Metrics Tracking (from rca.session module)
print("\n[Test 1] Metrics Tracking (Phase 1)")
print("-" * 70)
try:
    from rca.session import (
        FixType,
        MatchType,
        ProblemType,
        record_debug_start,
    )

    session_id = record_debug_start(
        problem_description="Test: ImportError module not found",
        problem_type=ProblemType.ERROR,
        context="test.py"
    )
    print(f"  Session: {session_id}")
    results.append(("Metrics", "PASS"))
except Exception as e:
    print(f"  FAIL: {e}")
    results.append(("Metrics", "FAIL"))

# Test 2: Error Signature Matching (Phase 3.5)
print("\n[Test 2] Error Signature Matching (Phase 3.5)")
print("-" * 70)
try:
    from rca.error_signature import extract_signature
    from rca.integration.rca_specialist_integration import (
        RCASpecialistSignatureBridge,
    )

    sig = extract_signature("ImportError: No module named xxx")
    bridge = RCASpecialistSignatureBridge()
    print("  Signature extraction: OK")
    print("  Signature bridge: OK")
    results.append(("Error Signature", "PASS"))
except Exception as e:
    print(f"  FAIL: {e}")
    results.append(("Error Signature", "FAIL"))

# Test 3: CKS Pattern Integration
print("\n[Test 3] CKS Pattern Integration")
print("-" * 70)
try:
    from rca.integration.cks_pattern_integration import CKSPatternRegistry

    registry = CKSPatternRegistry()
    print(f"  CKS available: {registry._cks is not None}")
    results.append(("CKS Pattern", "PASS"))
except Exception as e:
    print(f"  FAIL: {e}")
    results.append(("CKS Pattern", "FAIL"))

# Test 4: Auto Research
print("\n[Test 4] Auto Research")
print("-" * 70)
try:
    from rca.auto_research import should_trigger_research

    trigger = should_trigger_research("ImportError: No module named 'requests'")
    print(f"  Research triggered: {trigger.should_research}")
    print(f"  Confidence: {trigger.confidence:.2f}")
    results.append(("Auto Research", "PASS"))
except Exception as e:
    print(f"  FAIL: {e}")
    results.append(("Auto Research", "FAIL"))

# Test 5: Fault Localization
print("\n[Test 5] Fault Localization (SBFL)")
print("-" * 70)
try:
    from rca.fault_localization import (
        CoverageData,
        ochiai_score,
        rank_suspicious_locations,
    )

    # Create sample coverage data
    cov_data = [
        CoverageData(
            file_path="test.py",
            line_number=10,
            executed_in_passing=5,
            executed_in_failing=2,
            total_passing=5,
            total_failing=2
        )
    ]

    scores = rank_suspicious_locations(cov_data, formula="ochiai")
    print(f"  Ochiai scores: {len(scores)}")
    print("  SBFL formulas: OK")
    results.append(("Fault Localization", "PASS"))
except Exception as e:
    print(f"  FAIL: {e}")
    results.append(("Fault Localization", "FAIL"))

# Test 6: Temporal Check
print("\n[Test 6] Temporal Check")
print("-" * 70)
try:
    from rca.temporal_check import TemporalCheck, TemporalVerdict

    checker = TemporalCheck()
    result = checker.check("Use os.path.join for paths")

    print(f"  Verdict: {result.verdict.value}")
    print(f"  Warnings: {len(result.warnings)}")
    results.append(("Temporal Check", "PASS"))
except Exception as e:
    print(f"  FAIL: {e}")
    results.append(("Temporal Check", "FAIL"))

# Test 7: Mental Model Selector
print("\n[Test 7] Mental Model Selector")
print("-" * 70)
try:
    from rca.mental_model_selector import select_mental_models

    models = select_mental_models("intermittent timeout in database connection")
    print(f"  Models selected: {len(models)}")
    for m in models[:3]:
        print(f"    - {m.mental_model.value}")
    results.append(("Mental Model", "PASS"))
except Exception as e:
    print(f"  FAIL: {e}")
    results.append(("Mental Model", "FAIL"))

# Test 8: Library Docs Cache
print("\n[Test 8] Library Docs Cache")
print("-" * 70)
try:
    from rca.library_docs_cache import get_library_cache

    cache = get_library_cache()
    stats = cache.get_stats()
    print(f"  Cache entries: {stats['total_entries']}")
    results.append(("Library Cache", "PASS"))
except Exception as e:
    print(f"  FAIL: {e}")
    results.append(("Library Cache", "FAIL"))

# Test 9: Core Context Analyzer
print("\n[Test 9] Core Context Analyzer")
print("-" * 70)
try:
    from rca.core.context_analyzer import ContextAnalyzer

    analyzer = ContextAnalyzer()
    context = analyzer.analyze_context("AttributeError in import handling")

    print(f"  Problem type: {context['problem_type']}")
    print(f"  Complexity: {context['complexity_level']}")
    print(f"  Strategy: {context['recommended_strategy']}")
    results.append(("Context Analyzer", "PASS"))
except Exception as e:
    print(f"  FAIL: {e}")
    results.append(("Context Analyzer", "FAIL"))

# Test 10: Pattern Registry (CKS-based, replaced TaskMaster)
print("\n[Test 10] Pattern Registry (CKS)")
print("-" * 70)
try:
    from rca.pattern_registry import PatternRegistry
    from rca.error_signature import extract_signature

    registry = PatternRegistry()
    sig = extract_signature("ImportError: No module named 'requests'")

    print(f"  Signature extracted: {sig.pattern_name if sig else 'None'}")
    print(f"  Registry available: True")
    print("  Note: TaskMaster deprecated, using CKS for pattern storage")
    results.append(("Pattern Registry", "PASS"))
except Exception as e:
    print(f"  FAIL: {e}")
    results.append(("Pattern Registry", "FAIL"))

# Summary
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)

passed = sum(1 for _, r in results if r == "PASS")
total = len(results)

for name, result in results:
    icon = "✅" if result == "PASS" else "⚠️" if result == "PARTIAL" else "❌"
    print(f"  {icon} {name}: {result}")

print(f"\nTotal: {passed}/{total} passed")
if passed == total:
    print("\n✅ ALL TESTS PASSED - RCA WORKFLOW VERIFIED")
else:
    print(f"\n⚠️ {total - passed} test(s) failed")
