#!/usr/bin/env python3
"""
NVIDIA NIM CLI - Model discovery and health checks.

Provides CLI tools for interacting with NVIDIA NIM API.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request

import api_key as api_key_module

# ==================== COMMAND HANDLERS ====================


def cmd_health(args: argparse.Namespace) -> int:
    """Check NVIDIA NIM API health and connectivity.

    Validates API key, tests connectivity, and optionally runs a sanity check.
    Returns exit code 0 if healthy, 1 if any check fails.
    """
    all_healthy = True
    status = {}

    # 1. Check API key
    print("🔑 Checking API key...", end=" ")
    api_key = api_key_module.get_api_key()
    if not api_key:
        print("[FAIL]")
        print("  ❌ NVIDIA_API_KEY not set")
        print("  Get your key at: https://build.nvidia.com/")
        return 1
    print("[OK]")
    status["api_key"] = "present"

    # 2. Test connectivity to NVIDIA NIM API
    print("🌐 Testing API connectivity...", end=" ")
    try:
        # Test connectivity with a simple models list request
        url = "https://integrate.api.nvidia.com/v1/models"
        headers = {
            "Authorization": f"Bearer {api_key}",
        }

        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status == 200:
                print("[OK]")
                status["connectivity"] = "working"
            else:
                print(f"[HTTP {response.status}]")
                print(f"  ⚠️  Unexpected status code: {response.status}")
                all_healthy = False
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("[AUTH FAIL]")
            print("  ❌ Invalid API key (401 Unauthorized)")
            print("  Verify your key at: https://build.nvidia.com/")
        elif e.code == 429:
            print("[RATE LIMIT]")
            print("  ⚠️  Rate limited - please wait and retry")
        else:
            print(f"[HTTP {e.code}]")
            print(f"  ❌ HTTP error: {e.code}")
        all_healthy = False
        status["connectivity"] = f"http_{e.code}"
    except Exception as e:
        print("[FAIL]")
        print(f"  ❌ Connection failed: {e}")
        all_healthy = False
        status["connectivity"] = "failed"

    # 3. Optional sanity check with inference
    if args.sanity:
        print("🧪 Testing inference...", end=" ")
        try:
            # Use a free model for sanity check
            sanity_model = "nvidia/llama-3.1-nemotron-70b-instruct"
            url = "https://integrate.api.nvidia.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
            data = json.dumps(
                {
                    "model": sanity_model,
                    "messages": [{"role": "user", "content": "Say OK"}],
                    "max_tokens": 5,
                }
            ).encode()

            req = urllib.request.Request(url, data=data, headers=headers)

            with urllib.request.urlopen(req, timeout=60) as response:
                if response.status == 200:
                    result = json.loads(response.read())
                    if "choices" in result and len(result["choices"]) > 0:
                        content = result["choices"][0]["message"]["content"]
                        print(f"[OK] ({sanity_model})")
                        print(f"  Response: {content.strip()[:50]}")
                        status["inference"] = "working"
                    else:
                        print("[UNEXPECTED]")
                        print("  ⚠️  Unexpected response format")
                        all_healthy = False
                        status["inference"] = "unexpected_format"
                else:
                    print(f"[HTTP {response.status}]")
                    print(f"  ⚠️  Inference failed with status {response.status}")
                    all_healthy = False
                    status["inference"] = f"http_{response.status}"
        except urllib.error.HTTPError as e:
            if e.code == 401:
                print("[AUTH FAIL]")
                print("  ❌ Invalid API key (401 Unauthorized)")
            elif e.code == 429:
                print("[RATE LIMIT]")
                print("  ⚠️  Rate limited - please wait and retry")
            else:
                print(f"[HTTP {e.code}]")
                print(f"  ❌ HTTP error: {e.code}")
            all_healthy = False
            status["inference"] = f"http_{e.code}"
        except Exception as e:
            print("[FAIL]")
            print(f"  ❌ Inference failed: {e}")
            all_healthy = False
            status["inference"] = "failed"
    else:
        status["inference"] = "skipped"

    # 4. Summary
    print()
    if all_healthy:
        print("✅ NVIDIA NIM API is healthy")
    else:
        print("❌ NVIDIA NIM API health check failed")
        print("\nStatus details:")
        for key, value in status.items():
            print(f"  {key}: {value}")

    return 0 if all_healthy else 1


def cmd_quota(_args: argparse.Namespace) -> int:
    """Check NVIDIA NIM account status.

    Returns exit code 0 if successful, 1 if API key error.
    """
    api_key = api_key_module.get_api_key()
    if not api_key:
        print("❌ NVIDIA_API_KEY not set")
        print("Get your key at: https://build.nvidia.com/")
        return 1

    print("📊 Checking NVIDIA NIM account status...")

    try:
        # Check API health and model access
        url = "https://integrate.api.nvidia.com/v1/models"
        headers = {
            "Authorization": f"Bearer {api_key}",
        }
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read())
                model_count = len(data.get("data", []))

                # Determine account status based on model access
                if model_count > 100:
                    account_status = "✅ Premium"
                elif model_count > 50:
                    account_status = "✅ Standard"
                elif model_count > 0:
                    account_status = "✅ Free Tier"
                else:
                    account_status = "❌ No Access"

                print(f"\n{account_status} NVIDIA NIM Account:")
                print(f"   Available Models: {model_count}")
                print("   API Endpoint: https://integrate.api.nvidia.com/v1")

                # Show some popular models
                popular_models = [
                    "nvidia/llama-3.1-nemotron-70b-instruct",
                    "meta/llama-3.1-405b-instruct",
                    "google/gemma-3-27b-it",
                ]

                available_models = [m["id"] for m in data.get("data", [])]

                print("\n   Popular Model Access:")
                for model in popular_models:
                    status_icon = "✅" if model in available_models else "❌"
                    print(f"   {status_icon} {model}")

                return 0
            elif response.status == 401:
                print("❌ Invalid API key (401 Unauthorized)")
                print("Verify your key at: https://build.nvidia.com/")
                return 1
            else:
                print(f"❌ Unexpected status: {response.status}")
                return 1

    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("❌ Invalid API key (401 Unauthorized)")
            print("Verify your key at: https://build.nvidia.com/")
        else:
            print(f"❌ HTTP error: {e.code}")
        return 1
    except Exception as e:
        # Fallback: show that account tracking may be unavailable
        print(f"⚠️  Unable to fetch account status: {e}")
        print("\nNVIDIA NIM Free Tier: Access to 200+ models")
        print("For exact usage, visit: https://build.nvidia.com/")
        return 1


# ==================== MAIN CLI ====================


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser."""
    parser = argparse.ArgumentParser(
        prog="nvidia-nim",
        description="NVIDIA NIM CLI - Model discovery and health checks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  nvidia-nim health                    Check API health and connectivity
  nvidia-nim health --sanity           Run with inference sanity check

Environment Variables:
  NVIDIA_API_KEY                       Your NVIDIA NIM API key

Model ID Format:
  provider/model
  Example: nvidia/llama-3.1-nemotron-70b-instruct

Popular Models:
  nvidia/llama-3.1-nemotron-70b-instruct     General purpose, 128K context
  nvidia/llama-3.3-nemotron-super-49b-v1.5  Fast reasoning
  nvidia/nemotron-4-340b-instruct           SOTA performance
  meta/llama-3.1-405b-instruct              Large scale reasoning
  google/gemma-3-27b-it                      Efficient general purpose

Resources:
  https://docs.nvidia.com/ai-enterprise/nim-llm-api-intro.html
  https://build.nvidia.com/
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # health command
    health_parser = subparsers.add_parser("health", help="Check API health and connectivity")
    health_parser.add_argument(
        "--sanity",
        action="store_true",
        help="Run inference sanity check",
    )

    # quota command
    quota_parser = subparsers.add_parser("quota", help="Check account status")

    return parser


def main() -> int:
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "health":
        return cmd_health(args)
    elif args.command == "quota":
        return cmd_quota(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
