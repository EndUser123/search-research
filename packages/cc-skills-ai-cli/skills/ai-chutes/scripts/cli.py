#!/usr/bin/env python3
"""
Chutes CLI - Model discovery and health checks.

Provides CLI tools for interacting with Chutes.ai API.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

import api_key as api_key_module

# Cache directory and file
CACHE_DIR = Path.home() / ".claude" / "cache" / "ai-chutes"
CACHE_FILE = CACHE_DIR / "models.json"
CACHE_TTL_HOURS = 24  # Refresh cache daily


def load_cached_models() -> dict | None:
    """Load models from cache if fresh."""
    if not CACHE_FILE.exists():
        return None

    try:
        with open(CACHE_FILE) as f:
            data = json.load(f)

        # Check cache age
        cached_at = datetime.fromisoformat(data.get("cached_at", ""))
        if datetime.now() - cached_at < timedelta(hours=CACHE_TTL_HOURS):
            return data.get("models", {})
    except (json.JSONDecodeError, ValueError, KeyError):
        pass

    return None


def save_cached_models(models: dict) -> None:
    """Save models to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    data = {
        "cached_at": datetime.now().isoformat(),
        "models": models,
    }

    with open(CACHE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def fetch_models_from_api(api_key: str) -> list | None:
    """Fetch models from Chutes /models endpoint.

    Chutes uses litellm-compatible API which exposes /models endpoint.
    """
    try:
        from openai import OpenAI

        client = OpenAI(base_url="https://llm.chutes.ai/v1", api_key=api_key)
        models_response = client.models.list()

        # Convert to list of model info dicts
        models = []
        for model in models_response.data:
            models.append(
                {
                    "id": model.id,
                    "created": model.created,
                    "owned_by": getattr(model, "owned_by", "unknown"),
                }
            )

        return models
    except Exception as e:
        print(f"  ⚠️  Failed to fetch models: {e}", file=sys.stderr)
        return None


def get_models(force_refresh: bool = False) -> list:
    """Get models from cache or API."""
    api_key = api_key_module.get_api_key()
    if not api_key:
        print("❌ No API key for chutes", file=sys.stderr)
        return []

    # Try cache first
    if not force_refresh:
        cached = load_cached_models()
        if cached and "chutes" in cached:
            return cached["chutes"]

    # Fetch from API
    models = fetch_models_from_api(api_key)
    if models:
        save_cached_models({"chutes": models})
        return models

    # Fallback to empty list if API fails
    return []


# ==================== COMMAND HANDLERS ====================


def cmd_health(args: argparse.Namespace) -> int:
    """Check Chutes API health and connectivity.

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
        print("  ❌ CHUTES_API_KEY not set")
        print("  Get your key at: https://chutes.ai")
        return 1
    print("[OK]")
    status["api_key"] = "present"  # pragma: allowlist secret

    # 2. Test connectivity to Chutes API
    print("🌐 Testing API connectivity...", end=" ")
    try:
        # Test connectivity with a simple chat completions request
        url = "https://llm.chutes.ai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        data = json.dumps(
            {
                "model": "chutes/moonshotai/Kimi-K2.5-TEE",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1,
            }
        ).encode()

        req = urllib.request.Request(url, data=data, headers=headers)

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
            print("  Verify your key at: https://chutes.ai")
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
            sanity_model = "chutes/moonshotai/Kimi-K2.5-TEE"
            url = "https://llm.chutes.ai/v1/chat/completions"
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
        print("✅ Chutes API is healthy")
    else:
        print("❌ Chutes API health check failed")
        print("\nStatus details:")
        for key, value in status.items():
            print(f"  {key}: {value}")

    return 0 if all_healthy else 1


def cmd_quota(_args: argparse.Namespace) -> int:
    """Check Chutes daily request quota.

    Returns exit code 0 if successful, 1 if API key error.
    """
    api_key = api_key_module.get_api_key()
    if not api_key:
        print("❌ CHUTES_API_KEY not set")
        print("Get your key at: https://chutes.ai")
        return 1

    print("📊 Checking Chutes daily quota...")

    try:
        # Try the quota usage endpoint first
        url = "https://api.chutes.ai/users/me/quota_usage/me"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read())
                daily_limit = data.get("quota", 300)
                requests_used = int(data.get("used", 0))
                requests_remaining = max(0, daily_limit - requests_used)
                usage_percentage = (requests_used / daily_limit) * 100

                # Determine quota status
                if requests_remaining >= 100:
                    quota_status = "✅ Healthy"
                elif requests_remaining >= 50:
                    quota_status = "⚠️ Moderate"
                elif requests_remaining > 0:
                    quota_status = "❌ Low"
                else:
                    quota_status = "❌ Exhausted"

                print(f"\n{quota_status} Chutes Daily Quota:")
                print(f"   Remaining: {requests_remaining} / {daily_limit}")
                print(f"   Used: {requests_used} ({usage_percentage:.1f}%)")

                if requests_remaining < 50:
                    print("\n⚠️  Running low on daily requests!")

                return 0
            elif response.status == 401:
                print("❌ Invalid API key (401 Unauthorized)")
                print("Verify your key at: https://chutes.ai")
                return 1
            else:
                print(f"❌ Unexpected status: {response.status}")
                return 1

    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("❌ Invalid API key (401 Unauthorized)")
            print("Verify your key at: https://chutes.ai")
        else:
            print(f"❌ HTTP error: {e.code}")
        return 1
    except Exception as e:
        # Fallback: show that quota tracking may be unavailable
        print(f"⚠️  Unable to fetch quota: {e}")
        print("\nChutes free tier: 300 requests per day")
        print("For exact usage, visit: https://chutes.ai/dashboard")
        return 1


def cmd_list(args: argparse.Namespace) -> int:
    """List available models from Chutes API (cached or live).

    Returns exit code 0 if successful, 1 if API key error.
    """
    print("📋 Chutes Models:")

    # Check cache status
    cache_status = ""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE) as f:
                data = json.load(f)
            cached_at = datetime.fromisoformat(data.get("cached_at", ""))
            age = datetime.now() - cached_at
            if age < timedelta(hours=CACHE_TTL_HOURS):
                cache_status = f" (cached {age.seconds // 60} min ago)"
            else:
                cache_status = " (cache expired, refreshing...)"
        except (json.JSONDecodeError, ValueError, KeyError):
            cache_status = " (cache invalid, refreshing...)"
    else:
        cache_status = " (no cache, fetching...)"

    print(f"{cache_status}")
    print()

    # Fetch models
    models = get_models(force_refresh=args.refresh)

    if not models:
        print("❌ No models found")
        print("   Check your API key and network connection")
        return 1

    # Display models
    print(f"Found {len(models)} models:")
    print()

    # Group models by type for better display
    large_context_models = []
    code_models = []
    reasoning_models = []
    other_models = []

    for model in models:
        model_id = model.get("id", "")
        if "Kimi" in model_id or "MiniMax" in model_id:
            large_context_models.append(model)
        elif "Coder" in model_id or "Qwen" in model_id:
            code_models.append(model)
        elif "Hermes" in model_id or " reasoning" in model_id.lower():
            reasoning_models.append(model)
        else:
            other_models.append(model)

    def print_models(models_list: list, title: str) -> None:
        if models_list:
            print(f"{title}:")
            for model in models_list:
                model_id = model.get("id", "")
                owned_by = model.get("owned_by", "unknown")
                print(f"  • {model_id}")
                if args.verbose:
                    print(f"    Owner: {owned_by}")
            print()

    print_models(large_context_models, "Large Context (256K)")
    print_models(code_models, "Code Generation")
    print_models(reasoning_models, "Reasoning")
    print_models(other_models, "Other")

    # Cache info
    print(f"Cache file: {CACHE_FILE}")
    print(f"Refresh interval: {CACHE_TTL_HOURS} hours")
    print("Use --refresh to force cache update")

    return 0


# ==================== MAIN CLI ====================


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser."""
    parser = argparse.ArgumentParser(
        prog="chutes",
        description="Chutes CLI - Model discovery and health checks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  chutes health                    Check API health and connectivity
  chutes health --sanity           Run with inference sanity check
  chutes list                     List all available models (uses cache)
  chutes list --refresh           Force refresh model list from API
  chutes list --verbose           Show detailed model information
  chutes quota                    Check daily request quota

Environment Variables:
  CHUTES_API_KEY                    Your Chutes API key

Model ID Format:
  chutes/{Provider}/{Model}
  Example: chutes/moonshotai/Kimi-K2.5-TEE

Popular Models:
  chutes/moonshotai/Kimi-K2.5-TEE               256K context, multimodal
  chutes/MiniMaxAI/MiniMax-M2.1-TEE             SOTA coding (74% SWE-bench)
  chutes/NousResearch/Hermes-4-70B-Lite-TE      Fast reasoning
  chutes/Qwen/Qwen3-Coder-480B-A35B-Instruct-FP8-TEE  Code generation

Resources:
  https://chutes.ai/docs
  https://chutes.ai/models
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
    subparsers.add_parser("quota", help="Check daily request quota")

    # list command
    list_parser = subparsers.add_parser("list", help="List available models from provider")
    list_parser.add_argument(
        "--refresh",
        action="store_true",
        help="Force refresh from API (bypass cache)",
    )
    list_parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed model information",
    )

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
    elif args.command == "list":
        return cmd_list(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
