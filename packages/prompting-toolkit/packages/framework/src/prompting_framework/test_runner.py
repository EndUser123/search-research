from __future__ import annotations

import asyncio
import sys

"""Simple test runner for QueryFanoutTechnique to verify GREEN phase functionality."""


async def test_basic_functionality():
    """Test basic QueryFanoutTechnique functionality."""
    print("🧪 Testing QueryFanoutTechnique Basic Functionality")
    print("=" * 60)

    try:
        from .context_models import PromptingContext
        from .query_fanout_technique import QueryFanoutTechnique

        print("✅ Imports successful")

        # Test 1: Technique initialization
        technique = QueryFanoutTechnique()
        custom_technique = QueryFanoutTechnique(max_follow_ups=7, coverage_threshold=0.9)

        assert technique.technique.value == "query_fanout"
        assert technique.max_follow_ups == 5
        assert technique.coverage_threshold == 0.8
        assert custom_technique.max_follow_ups == 7
        assert custom_technique.coverage_threshold == 0.9
        print("✅ Test 1: Technique initialization - PASSED")

        # Test 2: Applicability for simple query
        simple_context = PromptingContext(
            query="What is Python?",
            domain="general",
            complexity="simple",
            user_intent="get_advice",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
        )

        is_applicable = await technique.is_applicable(simple_context)
        assert not is_applicable
        print("✅ Test 2: Simple query applicability - PASSED")

        # Test 3: Applicability for complex query
        complex_context = PromptingContext(
            query="How do I design a scalable microservices architecture with proper security?",
            domain="architecture",
            complexity="complex",
            user_intent="solve_problem",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
        )

        is_applicable = await technique.is_applicable(complex_context)
        assert is_applicable
        print("✅ Test 3: Complex query applicability - PASSED")

        # Test 4: Confidence scoring
        confidence = await technique.get_applicability_confidence(simple_context)
        assert 0.0 <= confidence <= 1.0
        assert confidence < 0.4

        confidence = await technique.get_applicability_confidence(complex_context)
        assert confidence >= 0.7
        print("✅ Test 4: Confidence scoring - PASSED")

        # Test 5: Technique application
        original_prompt = "How should I design a microservices architecture for an online retail platform?"
        enhanced_prompt = await technique.apply_technique(original_prompt, complex_context)

        assert len(enhanced_prompt) > len(original_prompt)
        assert original_prompt in enhanced_prompt
        assert any(indicator in enhanced_prompt.lower() for indicator in ["follow-up", "explore", "coverage"])
        print("✅ Test 5: Technique application - PASSED")

        print("\n🎉 All basic functionality tests PASSED!")
        return True

    except Exception as e:
        print(f"❌ Basic functionality test failed: {e!s}")
        import traceback

        traceback.print_exc()
        return False


async def test_query_decomposition():
    """Test query decomposition and analysis."""
    print("\n🧪 Testing Query Decomposition")
    print("=" * 60)

    try:

        technique = QueryFanoutTechnique()

        # Test architecture query decomposition
        architecture_query = (
            "Design a microservices architecture for e-commerce with scalability, security, and cost optimization"
        )
        components = await technique._analyze_query_components(architecture_query)

        assert len(components) >= 3, f"Should identify multiple components, got {len(components)}"
        assert any("microservices" in comp.text.lower() for comp in components)
        assert any("security" in comp.text.lower() for comp in components)
        assert any("scalability" in comp.text.lower() for comp in components)
        print("✅ Architecture query decomposition - PASSED")

        # Test follow-up generation

        context = PromptingContext(
            query=architecture_query,
            domain="architecture",
            complexity="complex",
            user_intent="solve_problem",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
        )

        from .query_fanout_technique import ExplorationStrategy

        follow_ups = await technique._generate_follow_up_questions(
            architecture_query,
            context,
            strategy=ExplorationStrategy.BREADTH_FIRST,
        )

        assert 3 <= len(follow_ups) <= 7, f"Should generate 3-7 follow-ups, got {len(follow_ups)}"
        for question in follow_ups:
            assert question.question.endswith("?")
            assert len(question.question) > 10

        print("✅ Follow-up question generation - PASSED")

        print("\n🎉 All query decomposition tests PASSED!")
        return True

    except Exception as e:
        print(f"❌ Query decomposition test failed: {e!s}")

        traceback.print_exc()
        return False


async def test_exploration_strategies():
    """Test different exploration strategies."""
    print("\n🧪 Testing Exploration Strategies")
    print("=" * 60)

    try:
        from .query_fanout_technique import ExplorationStrategy, QueryFanoutTechnique

        technique = QueryFanoutTechnique()

        context = PromptingContext(
            query="Build a comprehensive IoT platform with device management, data processing, and user interface",
            domain="architecture",
            complexity="expert",
            user_intent="solve_problem",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
        )

        # Test breadth-first
        bf_questions = await technique._generate_follow_up_questions(
            context.query,
            context,
            strategy=ExplorationStrategy.BREADTH_FIRST,
        )
        assert len(bf_questions) >= 1, "Breadth-first should generate at least 1 question"
        print("✅ Breadth-first strategy - PASSED")

        # Test depth-first
        df_questions = await technique._generate_follow_up_questions(
            context.query,
            context,
            strategy=ExplorationStrategy.DEPTH_FIRST,
        )
        assert len(df_questions) >= 3, "Depth-first should generate multiple questions"
        print("✅ Depth-first strategy - PASSED")

        # Test hybrid
        hybrid_questions = await technique._generate_follow_up_questions(
            context.query,
            context,
            strategy=ExplorationStrategy.HYBRID,
        )
        assert len(hybrid_questions) >= 1, "Hybrid should generate at least 1 question"
        print("✅ Hybrid strategy - PASSED")

        # Verify strategies produce different results
        assert len(df_questions) != len(bf_questions) or len(hybrid_questions) != len(
            bf_questions
        ), "Different strategies should produce different results"
        print("✅ Strategy differentiation - PASSED")

        print("\n🎉 All exploration strategy tests PASSED!")
        return True

    except Exception as e:
        print(f"❌ Exploration strategy test failed: {e!s}")

        traceback.print_exc()
        return False


async def test_socratic_integration():
    """Test integration with Socratic Technique."""
    print("\n🧪 Testing Socratic Integration")
    print("=" * 60)

    try:
        from .socratic_technique import SocraticTechnique

        query_fanout = QueryFanoutTechnique()
        socratic_method = SocraticTechnique()

        context = PromptingContext(
            query="Evaluate different architectural patterns for scalable systems",
            domain="architecture",
            complexity="complex",
            user_intent="solve_problem",
            available_evidence=[],
            performance_constraints={},
            constitutional_requirements={},
        )

        original_prompt = "Evaluate different architectural patterns for scalable systems"

        # Apply both techniques
        fanout_enhanced = await query_fanout.apply_technique(original_prompt, context)
        socratic_enhanced = await socratic_method.apply_technique(original_prompt, context)

        # Verify both techniques enhance the prompt
        assert len(fanout_enhanced) > len(original_prompt)
        assert len(socratic_enhanced) > len(original_prompt)

        # Check for technique signatures
        fanout_aspects = ["follow-up", "explore", "coverage", "component"]
        socratic_aspects = ["socratic", "questioning", "assumption", "why"]

        fanout_coverage = sum(1 for aspect in fanout_aspects if aspect in fanout_enhanced.lower())
        socratic_coverage = sum(1 for aspect in socratic_aspects if aspect in socratic_enhanced.lower())

        assert fanout_coverage >= 1, "Query fan-out should provide exploration coverage"
        assert socratic_coverage >= 1, "Socratic method should provide questioning coverage"

        print("✅ Individual technique enhancement - PASSED")

        # Test combined application
        combined_enhanced = await query_fanout.apply_technique(socratic_enhanced, context)

        # Verify combined enhancement preserves both techniques
        assert len(combined_enhanced) > len(socratic_enhanced)
        assert original_prompt in combined_enhanced

        combined_fanout = sum(1 for aspect in fanout_aspects if aspect in combined_enhanced.lower())
        combined_socratic = sum(1 for aspect in socratic_aspects if aspect in combined_enhanced.lower())

        assert combined_fanout >= 1, "Combined should have query fan-out indicators"
        assert combined_socratic >= 1, "Combined should have socratic indicators"

        print("✅ Combined technique application - PASSED")

        print("\n🎉 All Socratic integration tests PASSED!")
        return True

    except Exception as e:
        print(f"❌ Socratic integration test failed: {e!s}")

        traceback.print_exc()
        return False


async def test_performance_requirements():
    """Test performance requirements."""
    print("\n🧪 Testing Performance Requirements")
    print("=" * 60)

    try:
        import time

        technique = QueryFanoutTechnique()

        test_cases = [
            ("simple design question", "simple"),
            ("moderately complex system design", "moderate"),
            ("complex architectural design with multiple constraints", "complex"),
            ("expert level system design with comprehensive requirements", "expert"),
        ]

        for query_text, complexity in test_cases:
            context = PromptingContext(
                query=query_text,
                domain="architecture",
                complexity=complexity,
                user_intent="solve_problem",
                available_evidence=[],
                performance_constraints={},
                constitutional_requirements={},
            )

            # Measure processing time
            start_time = time.time()
            result = await technique.apply_technique(query_text, context)
            end_time = time.time()

            processing_time = end_time - start_time

            assert processing_time < 5.0, f"Processing time {processing_time:.2f}s for {complexity} should be under 5s"
            assert len(result) > len(query_text), "Should enhance the prompt"

            print(f"✅ {complexity.capitalize()} query processing - PASSED ({processing_time:.2f}s)")

        print("\n🎉 All performance requirement tests PASSED!")
        return True

    except Exception as e:
        print(f"❌ Performance requirement test failed: {e!s}")

        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting QueryFanoutTechnique Test Suite")
    print("=" * 80)

    test_results = []

    # Run all test suites
    test_results.append(await test_basic_functionality())
    test_results.append(await test_query_decomposition())
    test_results.append(await test_exploration_strategies())
    test_results.append(await test_socratic_integration())
    test_results.append(await test_performance_requirements())

    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)

    passed_tests = sum(test_results)
    total_tests = len(test_results)

    print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
    print(f"Success Rate: {passed_tests / total_tests * 100:.1f}%")

    if passed_tests == total_tests:
        print("\n🎉 GREEN PHASE COMPLETE - All tests passed!")
        print("QueryFanoutTechnique is ready for REFACTOR phase.")
    else:
        print(f"\n⚠️  {total_tests - passed_tests} test suite(s) failed.")
        print("Additional work needed before REFACTOR phase.")

    return passed_tests == total_tests


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
