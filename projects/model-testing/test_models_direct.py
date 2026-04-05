#!/usr/bin/env python3
"""
Direct Model Testing Script
Tests models using direct OpenRouter API calls
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path

import aiohttp

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))


async def test_openrouter_models():
    """Test models directly via OpenRouter API"""
    print("Direct Model Testing via OpenRouter")
    print("=" * 50)

    # Get OpenRouter API key
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not found in environment")
        return

    print(f"OpenRouter API Key: {api_key[:12]}...{api_key[-4:]}")

    # Models to test (using free tier models from your configuration)
    models_to_test = [
        "meta-llama/llama-3.2-3b-instruct:free",
        "nousresearch/hermes-3-llama-3.1-405b:free",
        "google/gemma-2-9b-it:free",
        "qwen/qwen-2-7b-instruct:free",
        "microsoft/phi-3-medium-128k-instruct:free",
    ]

    # Test prompts for different capabilities
    test_prompts = {
        "coding": """Write a Python function that takes a list of numbers and returns the average.
Include error handling for empty lists and non-numeric inputs.""",
        "reasoning": """A train travels from City A to City B at 60 mph. On the return trip,
it travels at 40 mph due to traffic. What is the average speed for the entire round trip?
Explain your reasoning step by step.""",
        "creativity": """Write a short story (100 words) about a robot that discovers music for the first time.
Focus on the robot's emotional journey and discovery.""",
        "analysis": """Analyze the potential security risks in this code:
```python
def login(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    return database.execute(query)
```
Identify vulnerabilities and suggest secure alternatives.""",
    }

    print(
        f"\nTesting {len(models_to_test)} models with {len(test_prompts)} different prompt types"
    )
    print("-" * 60)

    results = []

    async with aiohttp.ClientSession() as session:
        for model in models_to_test:
            print(f"\nTesting Model: {model}")
            print("-" * 40)

            model_results = {"model": model, "tests": {}}

            for test_type, prompt in test_prompts.items():
                print(f"  Running {test_type} test...")

                try:
                    # Make API request
                    start_time = time.time()

                    headers = {
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    }

                    data = {
                        "model": model,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 500,
                        "temperature": 0.7,
                    }

                    async with session.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers=headers,
                        json=data,
                        timeout=30,
                    ) as response:

                        execution_time = time.time() - start_time

                        if response.status == 200:
                            result_data = await response.json()

                            if (
                                "choices" in result_data
                                and len(result_data["choices"]) > 0
                            ):
                                content = result_data["choices"][0]["message"][
                                    "content"
                                ]
                                usage = result_data.get("usage", {})

                                tokens_used = usage.get("total_tokens", 0)
                                prompt_tokens = usage.get("prompt_tokens", 0)
                                completion_tokens = usage.get("completion_tokens", 0)

                                test_result = {
                                    "success": True,
                                    "response": content,
                                    "execution_time": execution_time,
                                    "tokens_used": tokens_used,
                                    "prompt_tokens": prompt_tokens,
                                    "completion_tokens": completion_tokens,
                                    "response_preview": (
                                        content[:150] + "..."
                                        if len(content) > 150
                                        else content
                                    ),
                                }

                                print(
                                    f"    SUCCESS - {execution_time:.2f}s, {tokens_used} tokens"
                                )
                                print(f"    Preview: {test_result['response_preview']}")

                            else:
                                test_result = {
                                    "success": False,
                                    "error": "No response in API result",
                                    "execution_time": execution_time,
                                }
                                print("    FAIL - No response in API result")

                        else:
                            error_text = await response.text()
                            test_result = {
                                "success": False,
                                "error": f"HTTP {response.status}: {error_text}",
                                "execution_time": execution_time,
                            }
                            print(f"    FAIL - HTTP {response.status}")

                except TimeoutError:
                    test_result = {
                        "success": False,
                        "error": "Request timeout",
                        "execution_time": time.time() - start_time,
                    }
                    print("    FAIL - Timeout")

                except Exception as e:
                    test_result = {
                        "success": False,
                        "error": str(e),
                        "execution_time": time.time() - start_time,
                    }
                    print(f"    FAIL - {str(e)}")

                model_results["tests"][test_type] = test_result

                # Small delay between requests
                await asyncio.sleep(1)

            results.append(model_results)

            # Calculate model summary
            successful_tests = sum(
                1 for test in model_results["tests"].values() if test["success"]
            )
            total_tests = len(model_results["tests"])
            avg_time = (
                sum(test["execution_time"] for test in model_results["tests"].values())
                / total_tests
            )
            total_tokens = sum(
                test.get("tokens_used", 0)
                for test in model_results["tests"].values()
                if test["success"]
            )

            print(f"  Model Summary: {successful_tests}/{total_tests} tests passed")
            print(f"  Average time: {avg_time:.2f}s, Total tokens: {total_tokens}")

    # Generate comprehensive report
    print("\n" + "=" * 60)
    print("COMPREHENSIVE TEST REPORT")
    print("=" * 60)

    # Overall statistics
    total_tests_per_type = len(test_prompts) * len(models_to_test)
    successful_overall = sum(
        sum(1 for test in model["tests"].values() if test["success"])
        for model in results
    )

    print("\nOVERALL STATISTICS:")
    print(f"Models tested: {len(models_to_test)}")
    print(f"Test types: {len(test_prompts)}")
    print(f"Total tests run: {total_tests_per_type}")
    print(f"Successful tests: {successful_overall}")
    print(f"Success rate: {(successful_overall/total_tests_per_type)*100:.1f}%")

    # Model rankings
    print("\nMODEL PERFORMANCE RANKINGS:")
    model_scores = []
    for model in results:
        successful = sum(1 for test in model["tests"].values() if test["success"])
        avg_time = sum(
            test["execution_time"] for test in model["tests"].values()
        ) / len(model["tests"])
        total_tokens = sum(
            test.get("tokens_used", 0)
            for test in model["tests"].values()
            if test["success"]
        )

        score = successful  # Higher is better
        model_scores.append((model["model"], successful, avg_time, total_tokens))

    # Sort by success rate (descending)
    model_scores.sort(key=lambda x: x[1], reverse=True)

    for i, (model, successful, avg_time, tokens) in enumerate(model_scores, 1):
        print(f"{i:2d}. {model}")
        print(f"    Success: {successful}/{len(test_prompts)} tests")
        print(f"    Avg time: {avg_time:.2f}s")
        print(f"    Tokens: {tokens}")

    # Test type performance
    print("\nTEST TYPE PERFORMANCE:")
    for test_type in test_prompts.keys():
        successful = sum(
            1
            for model in results
            if model["tests"].get(test_type, {}).get("success", False)
        )
        print(
            f"{test_type.title()}: {successful}/{len(models_to_test)} models successful"
        )

    # Save detailed results
    report_path = Path(__file__).parent / "model_test_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": time.time(),
                "models_tested": models_to_test,
                "test_types": list(test_prompts.keys()),
                "results": results,
                "summary": {
                    "total_models": len(models_to_test),
                    "total_tests": total_tests_per_type,
                    "successful_tests": successful_overall,
                    "success_rate": (successful_overall / total_tests_per_type) * 100,
                },
            },
            f,
            indent=2,
        )

    print(f"\nDetailed results saved to: {report_path}")


async def main():
    """Main function"""
    print("AI Model Testing Suite - Direct API Testing")
    print("=" * 50)
    print("Testing models directly via OpenRouter API")
    print("This provides real performance metrics and capabilities assessment.")
    print()

    await test_openrouter_models()

    print("\n" + "=" * 50)
    print("Model testing completed!")
    print("The report above shows real performance data for each model")
    print("across different types of tasks and capabilities.")


if __name__ == "__main__":
    asyncio.run(main())
