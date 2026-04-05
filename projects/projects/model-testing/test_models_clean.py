#!/usr/bin/env python3
"""
Simple Model Testing Script without Unicode
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


async def test_functional_models():
    """Test models using the functional test framework"""
    print("Testing Available AI Models")
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
        print(f"Failed to import functional test framework: {e}")
        return None

    print("\nRunning Functional Tests with Real Models...")
    print("This will test actual model performance across different tasks.\n")

    try:
        # Run the complete functional test suite
        print("Running complete functional test suite...")
        result = await run_all_functional_tests()

        if result.get("success", False):
            print("\nFunctional tests completed successfully!")
            print(f"Tests executed: {result.get('total_tests', 0)}")
            print(f"Tests passed: {result.get('passed_tests', 0)}")
            print(f"Tests failed: {result.get('failed_tests', 0)}")
            print(f"Success rate: {result.get('success_rate', 0):.1f}%")

            # Show individual test results
            if "test_results" in result:
                print("\nIndividual Test Results:")
                for test_result in result["test_results"]:
                    status = "PASS" if test_result.get("success", False) else "FAIL"
                    test_name = test_result.get("test_name", "Unknown")
                    print(f"  {status}: {test_name}")
                    if test_result.get("model_used"):
                        print(f"    Model: {test_result['model_used']}")
                    if test_result.get("execution_time"):
                        print(f"    Time: {test_result['execution_time']:.2f}s")
                    if test_result.get("tokens_used"):
                        print(f"    Tokens: {test_result['tokens_used']}")

            return result
        else:
            print(f"Functional tests failed: {result.get('error', 'Unknown error')}")
            return result

    except Exception as e:
        print(f"Failed to run functional tests: {e}")
        import traceback

        traceback.print_exc()
        return {"success": False, "error": str(e)}


async def test_individual_tasks():
    """Test individual model tasks"""
    print("\nTesting Individual Model Tasks")
    print("=" * 40)

    try:
        from cognitive_stack.multi_agent.functional_test_fixed import (
            test_code_analysis,
            test_performance_analysis,
        )

        tasks = [
            ("Code Analysis", test_code_analysis),
            ("Performance Analysis", test_performance_analysis),
        ]

        results = []

        for task_name, task_func in tasks:
            print(f"\nRunning {task_name}...")
            try:
                result = await task_func()
                results.append((task_name, result))

                status = "SUCCESS" if result.get("success", False) else "FAILED"
                print(f"Status: {status}")

                if result.get("success", False):
                    if result.get("model_used"):
                        print(f"Model: {result['model_used']}")
                    if result.get("execution_time"):
                        print(f"Execution time: {result['execution_time']:.2f}s")
                    if result.get("tokens_used"):
                        print(f"Tokens used: {result['tokens_used']}")

                    # Show part of the response
                    response = result.get("response", "")
                    if response:
                        lines = response.split("\n")
                        print("Response preview:")
                        for line in lines[:3]:  # Show first 3 lines
                            if line.strip():
                                print(f"  {line}")
                        if len(lines) > 3:
                            print(f"  ... ({len(lines) - 3} more lines)")
                else:
                    if result.get("error"):
                        print(f"Error: {result['error']}")

            except Exception as e:
                print(f"Task crashed: {e}")
                results.append((task_name, {"success": False, "error": str(e)}))

            # Small delay between tasks
            await asyncio.sleep(2)

        # Summary
        print("\nTask Summary:")
        print("=" * 20)
        successful = sum(1 for _, result in results if result.get("success", False))
        total = len(results)
        print(f"Total tasks: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {total - successful}")
        print(f"Success rate: {(successful/total)*100:.1f}%")

        return results

    except ImportError as e:
        print(f"Failed to import test functions: {e}")
        return []
    except Exception as e:
        print(f"Failed to run individual tasks: {e}")
        return []


async def check_configuration():
    """Check what's configured for model testing"""
    print("Checking Model Configuration")
    print("=" * 35)

    try:
        import os

        # Check environment variables
        api_keys = {
            "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY"),
            "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"),
            "GOOGLE_API_KEY": os.environ.get("GOOGLE_API_KEY"),
            "OPENROUTER_API_KEY": os.environ.get("OPENROUTER_API_KEY"),
        }

        print("API Key Configuration:")
        for key, value in api_keys.items():
            if value:
                masked = value[:8] + "***" + value[-4:] if len(value) > 12 else "***"
                print(f"  {key}: Configured ({masked})")
            else:
                print(f"  {key}: Not configured")

        # Check cognitive stack
        cognitive_path = Path(__file__).parent / "cognitive_stack"
        if cognitive_path.exists():
            print(f"\nCognitive stack: Found at {cognitive_path}")

            # Check functional test file
            functional_test = (
                cognitive_path / "multi_agent" / "functional_test_fixed.py"
            )
            if functional_test.exists():
                print("Functional test framework: Available")
            else:
                print("Functional test framework: Not found")
        else:
            print("\nCognitive stack: Not found")

    except Exception as e:
        print(f"Error checking configuration: {e}")


async def main():
    """Main test function"""
    print("AI Model Testing Suite")
    print("=" * 30)
    print("Testing real AI models across multiple tasks")
    print("including code analysis, security analysis, and performance evaluation.")
    print()

    # Check configuration first
    await check_configuration()

    # Test with functional framework
    functional_result = await test_functional_models()

    # Test individual tasks if functional tests didn't run completely
    if not functional_result or not functional_result.get("success", False):
        await test_individual_tasks()

    print("\nModel testing completed!")
    print("The tests above demonstrate real AI model performance")
    print("across different analytical tasks and capabilities.")


if __name__ == "__main__":
    asyncio.run(main())
