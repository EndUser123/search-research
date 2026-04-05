#!/usr/bin/env python3
"""
Model Testing Script with Delays (Clean Version)
Tests models with proper rate limiting handling and delays between requests
"""

import asyncio
import json
import os
import time
from pathlib import Path

import aiohttp


async def test_with_delays():
    """Test models with delays to avoid rate limiting"""
    print("Model Testing with Delays")
    print("=" * 40)
    print("Testing previously rate-limited models with delays")
    print("Minimum 1 second delay between requests")
    print()

    # Get OpenRouter API key
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not found in environment")
        return

    print(f"OpenRouter API Key: {api_key[:12]}...{api_key[-4:]}")

    # Focus on the previously rate-limited models
    rate_limited_models = [
        "meta-llama/llama-3.2-3b-instruct:free",
        "nousresearch/hermes-3-llama-3.1-405b:free",
    ]

    # Test prompts (focusing on the ones that were rate limited)
    test_prompts = {
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
        f"Testing {len(rate_limited_models)} rate-limited models with {len(test_prompts)} test types"
    )
    print("Using 1-2 second delays between requests")
    print("-" * 60)

    results = []

    async with aiohttp.ClientSession() as session:
        for model in rate_limited_models:
            print(f"\nTesting Model: {model}")
            print("-" * 50)

            model_results = {"model": model, "tests": {}}

            for test_type, prompt in test_prompts.items():
                print(f"  Running {test_type} test with delay...")

                # Add delay before each request (minimum 1.5 seconds)
                await asyncio.sleep(1.5)

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
                        timeout=60,  # Increased timeout
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
                                        content[:200] + "..."
                                        if len(content) > 200
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
                    print("    TIMEOUT")

                except Exception as e:
                    test_result = {
                        "success": False,
                        "error": str(e),
                        "execution_time": time.time() - start_time,
                    }
                    print(f"    ERROR - {str(e)}")

                model_results["tests"][test_type] = test_result

                # Add extra delay after each test
                print("    Waiting 2 seconds before next test...")
                await asyncio.sleep(2.0)

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

            # Longer delay between different models
            if rate_limited_models.index(model) < len(rate_limited_models) - 1:
                print("  Waiting 5 seconds before next model...")
                await asyncio.sleep(5.0)

    # Generate comprehensive report
    print("\n" + "=" * 60)
    print("DELAYED TESTING RESULTS")
    print("=" * 60)

    # Overall statistics
    total_tests_per_type = len(test_prompts) * len(rate_limited_models)
    successful_overall = sum(
        sum(1 for test in model["tests"].values() if test["success"])
        for model in results
    )

    print("\nOVERALL STATISTICS:")
    print(f"Models tested: {len(rate_limited_models)} (previously rate-limited)")
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
        status_emoji = (
            "SUCCESS"
            if successful == len(test_prompts)
            else "PARTIAL" if successful > 0 else "FAILED"
        )
        print(f"{i:2d}. {status_emoji}: {model}")
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
            f"{test_type.title()}: {successful}/{len(rate_limited_models)} models successful"
        )

    # Compare with previous results
    print("\nCOMPARISON WITH PREVIOUS RUN:")
    print("Previous success rate: 5.0% (1/20 tests)")
    print(
        f"Current success rate: {(successful_overall/total_tests_per_type)*100:.1f}% ({successful_overall}/{total_tests_per_type} tests)"
    )

    improvement = successful_overall - 1  # Previous had 1 success
    if improvement > 0:
        print(f"IMPROVEMENT: +{improvement} additional successful tests!")
    elif improvement == 0:
        print("SAME: No improvement in successful tests")
    else:
        print(f"WORSE: {-improvement} fewer successful tests")

    # Save detailed results
    report_path = Path(__file__).parent / "reports" / "delayed_test_results.json"

    # Ensure reports directory exists
    report_path.parent.mkdir(exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": time.time(),
                "test_type": "delayed_testing",
                "models_tested": rate_limited_models,
                "test_types": list(test_prompts.keys()),
                "delay_between_requests": "1.5-2.0 seconds",
                "results": results,
                "comparison_with_previous": {
                    "previous_success_rate": 5.0,
                    "current_success_rate": (successful_overall / total_tests_per_type)
                    * 100,
                    "improvement": improvement,
                },
                "summary": {
                    "total_models": len(rate_limited_models),
                    "total_tests": total_tests_per_type,
                    "successful_tests": successful_overall,
                    "success_rate": (successful_overall / total_tests_per_type) * 100,
                },
            },
            f,
            indent=2,
        )

    print(f"\nDetailed results saved to: {report_path}")

    return results


async def main():
    """Main function"""
    print("Model Testing with Delays")
    print("=" * 30)
    print("Retesting previously rate-limited models")
    print("Using delays to avoid rate limiting issues")
    print()

    await test_with_delays()

    print("\n" + "=" * 30)
    print("Delayed model testing completed!")
    print("Check if the delays helped overcome rate limiting.")


if __name__ == "__main__":
    asyncio.run(main())
