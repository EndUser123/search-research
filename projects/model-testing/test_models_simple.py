#!/usr/bin/env python3
"""
Simple Model Testing Script
Tests available models using the functional test framework
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

# Add cognitive stack for LLM integration
cognitive_stack_path = Path(__file__).parent / "cognitive_stack"
if cognitive_stack_path.exists():
    sys.path.append(str(cognitive_stack_path))


async def test_available_models():
    """Test models using the functional test framework"""
    print("🧪 Testing Available AI Models")
    print("=" * 50)

    # Import the functional test framework
    try:
        from cognitive_stack.multi_agent.functional_test_fixed import (
            run_all_functional_tests,
            test_code_analysis,
            test_cost_tracking,
            test_performance_analysis,
            test_security_analysis,
        )
    except ImportError as e:
        print(f"❌ Failed to import functional test framework: {e}")
        return

    print("\n🔍 Running Functional Tests with Real Models...")
    print("This will test actual model performance across different tasks.\n")

    try:
        # Run individual tests to see model performance
        tests = [
            ("Code Analysis", test_code_analysis),
            ("Performance Analysis", test_performance_analysis),
            ("Security Analysis", test_security_analysis),
            ("Cost Tracking", test_cost_tracking),
        ]

        results = []

        for test_name, test_func in tests:
            print(f"\n📊 Running {test_name} Test...")
            print("-" * 30)

            try:
                result = await test_func()
                results.append((test_name, result))

                if result.get("success"):
                    print(f"✅ {test_name} test completed successfully")
                    print(f"   Model used: {result.get('model_used', 'Unknown')}")
                    print(f"   Execution time: {result.get('execution_time', 0):.2f}s")
                    print(f"   Tokens used: {result.get('tokens_used', 0)}")

                    # Show response preview
                    response = result.get("response", "")
                    if response:
                        preview = (
                            response[:200] + "..." if len(response) > 200 else response
                        )
                        print(f"   Response preview: {preview}")
                else:
                    print(f"❌ {test_name} test failed")
                    if result.get("error"):
                        print(f"   Error: {result['error']}")

            except Exception as e:
                print(f"❌ {test_name} test crashed: {e}")
                results.append((test_name, {"success": False, "error": str(e)}))

            # Add delay between tests
            await asyncio.sleep(1)

        # Summary
        print("\n📈 Test Results Summary")
        print("=" * 30)

        successful_tests = sum(1 for _, result in results if result.get("success"))
        total_tests = len(results)

        print(f"Total tests run: {total_tests}")
        print(f"Successful tests: {successful_tests}")
        print(f"Success rate: {(successful_tests/total_tests)*100:.1f}%")

        print("\n🔧 Detailed Results:")
        for test_name, result in results:
            status = "✅" if result.get("success") else "❌"
            print(f"  {status} {test_name}")
            if result.get("success") and result.get("model_used"):
                print(f"      Model: {result['model_used']}")
                if result.get("execution_time"):
                    print(f"      Time: {result['execution_time']:.2f}s")

    except Exception as e:
        print(f"❌ Failed to run functional tests: {e}")
        import traceback

        traceback.print_exc()


async def test_specific_model():
    """Test a specific model with comprehensive tasks"""
    print("\n🎯 Testing Specific Model Performance")
    print("=" * 40)

    try:
        # Import MultiAgentSystem for direct model testing
        from cognitive_stack.multi_agent.functional_test_fixed import test_code_analysis

        # Test with the current model configuration
        print("Testing current model configuration with code analysis task...")

        result = await test_code_analysis()

        if result.get("success"):
            print("✅ Model test successful!")
            print("Model Response:")
            print("-" * 20)
            print(result.get("response", "No response"))
            print("-" * 20)
            print("Execution metrics:")
            print(f"  - Time: {result.get('execution_time', 0):.2f}s")
            print(f"  - Tokens: {result.get('tokens_used', 0)}")
            print(f"  - Success: {result.get('success', False)}")
        else:
            print("❌ Model test failed")
            if result.get("error"):
                print(f"Error: {result['error']}")

    except ImportError as e:
        print(f"❌ Failed to import testing components: {e}")
        print("This may indicate that the cognitive stack is not properly configured.")

    except Exception as e:
        print(f"❌ Test execution failed: {e}")


async def check_available_providers():
    """Check what LLM providers and models are available"""
    print("\n📋 Checking Available Providers")
    print("=" * 35)

    try:
        # Try to import and check provider configurations
        import os

        # Check for environment variables that might indicate LLM configuration
        llm_vars = {
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", "Not set"),
            "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", "Not set"),
            "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY", "Not set"),
        }

        print("Environment Configuration:")
        for var, value in llm_vars.items():
            status = "✅" if value != "Not set" else "❌"
            masked_value = (
                "***" + value[-4:] if value != "Not set" and len(value) > 4 else value
            )
            print(f"  {status} {var}: {masked_value}")

        # Try to check cognitive stack configuration
        cognitive_stack_path = Path(__file__).parent / "cognitive_stack"
        if cognitive_stack_path.exists():
            print(f"\n✅ Cognitive stack found at: {cognitive_stack_path}")

            # List available components
            multi_agent_path = cognitive_stack_path / "multi_agent"
            if multi_agent_path.exists():
                components = list(multi_agent_path.glob("*.py"))
                print(f"📦 {len(components)} multi-agent components available")
                for component in components[:5]:  # Show first 5
                    print(f"   - {component.name}")
                if len(components) > 5:
                    print(f"   ... and {len(components) - 5} more")
        else:
            print("\n❌ Cognitive stack not found at expected path")

    except Exception as e:
        print(f"❌ Error checking providers: {e}")


async def main():
    """Main test function"""
    print("🚀 AI Model Testing Suite")
    print("=" * 30)
    print("This script will test available AI models using")
    print("the functional testing framework with real API calls.")
    print()

    # Check what's available
    await check_available_providers()

    # Test available models
    await test_available_models()

    # Test specific model
    await test_specific_model()

    print("\n🎉 Testing completed!")
    print("📊 Results demonstrate real AI model performance across multiple tasks.")


if __name__ == "__main__":
    asyncio.run(main())
