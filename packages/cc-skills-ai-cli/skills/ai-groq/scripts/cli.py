#!/usr/bin/env python3
"""
Groq API CLI - Health checks using OpenAI SDK.

Provides CLI tools for checking health of Groq API access.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import api_key as api_key_module

# Cache directory and file
CACHE_DIR = Path.home() / ".claude" / "cache" / "ai-groq"
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


def fetch_models_from_api(provider: str, config: dict, api_key: str) -> list | None:
    """Fetch models from provider's /models endpoint."""
    try:
        from openai import OpenAI

        client = OpenAI(base_url=config["base_url"], api_key=api_key)
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


def get_models(provider: str = "groq", force_refresh: bool = False) -> list:
    """Get models from cache or API."""
    config = PROVIDERS.get(provider)
    if not config:
        return []

    api_key = api_key_module.get_api_key(provider)
    if not api_key:
        print(f"❌ No API key for {provider}", file=sys.stderr)
        return []

    # Try cache first
    if not force_refresh:
        cached = load_cached_models()
        if cached and provider in cached:
            return cached[provider]

    # Fetch from API
    models = fetch_models_from_api(provider, config, api_key)
    if models:
        save_cached_models({provider: models})
        return models

    # Fallback to empty list if API fails
    return []


# Provider configurations
PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
        "name": "Groq",
    },
}


def cmd_health(args: argparse.Namespace) -> int:
    """Check provider API health using OpenAI SDK.

    Returns exit code 0 if all checked providers are healthy, 1 if any fail.
    """
    # Determine which providers to check
    if args.provider:
        providers_to_check = [args.provider]
        if args.provider not in PROVIDERS:
            print(f"❌ Unknown provider: {args.provider}", file=sys.stderr)
            print(f"Available providers: {', '.join(PROVIDERS.keys())}", file=sys.stderr)
            return 1
    else:
        # Check all providers with available API keys
        providers_to_check = api_key_module.get_available_providers()
        if not providers_to_check:
            print("❌ No provider API keys found", file=sys.stderr)
            print("Set one or more of:", file=sys.stderr)
            for env_key in api_key_module.PROVIDER_ENV_KEYS.values():
                print(f"  {env_key}", file=sys.stderr)
            return 1

    all_healthy = True
    results = {}

    for provider in providers_to_check:
        config = PROVIDERS[provider]
        api_key = api_key_module.get_api_key(provider)

        if not api_key:
            results[provider] = "no_api_key"
            continue

        print(f"🔍 Checking {config['name']}...", end=" ")

        try:
            from openai import OpenAI

            client = OpenAI(base_url=config["base_url"], api_key=api_key)

            if args.sanity:
                # Run inference sanity check
                response = client.chat.completions.create(
                    model=config["default_model"],
                    messages=[{"role": "user", "content": "Say OK"}],
                    max_tokens=5,
                )
                content = response.choices[0].message.content
                print(f"[OK] ({config['default_model']})")
                print(f"  Response: {content.strip()[:50]}")
                results[provider] = "healthy"
            else:
                # Just test connectivity
                response = client.chat.completions.create(
                    model=config["default_model"],
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=1,
                )
                print("[OK]")
                results[provider] = "healthy"

        except ImportError:
            print("[MISSING DEP]")
            print("  ❌ OpenAI SDK not installed. Run: pip install openai")
            results[provider] = "missing_openai"
            all_healthy = False
        except Exception as e:
            error_str = str(e)
            if "401" in error_str or "authentication" in error_str.lower():
                print("[AUTH FAIL]")
                print("  ❌ Invalid API key")
            elif "429" in error_str:
                print("[RATE LIMIT]")
                print("  ⚠️  Rate limited")
            elif "connection" in error_str.lower() or "network" in error_str.lower():
                print("[CONN FAIL]")
                print(f"  ❌ Connection error: {e}")
            else:
                print("[FAIL]")
                print(f"  ❌ {e}")
            results[provider] = "failed"
            all_healthy = False

    # Summary
    print()
    if all_healthy:
        print("✅ All checked providers are healthy")
    else:
        print("❌ Some providers failed health check")
        print("\nStatus:")
        for provider, status in results.items():
            status_icon = "✅" if status == "healthy" else "❌"
            print(f"  {status_icon} {provider}: {status}")

    return 0 if all_healthy else 1


def cmd_list(args: argparse.Namespace) -> int:
    """List available models from provider (cached or live)."""
    print(f"📋 {args.provider or 'groq'} Models:")

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
    models = get_models(args.provider or "groq", force_refresh=args.refresh)

    if not models:
        print("❌ No models found")
        print("   Check your API key and network connection")
        return 1

    # Display models
    print(f"Found {len(models)} models:")
    print()

    # Group models by type for better display
    production_models = []
    preview_models = []
    other_models = []

    for model in models:
        model_id = model.get("id", "")
        if "-preview" in model_id or "preview" in model_id.lower():
            preview_models.append(model)
        elif "systems" in model_id or "guard" in model_id or "tool" in model_id:
            other_models.append(model)
        else:
            production_models.append(model)

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

    print_models(production_models, "Production")
    print_models(preview_models, "Preview")
    print_models(other_models, "System/Tool")

    # Cache info
    print(f"Cache file: {CACHE_FILE}")
    print(f"Refresh interval: {CACHE_TTL_HOURS} hours")
    print("Use --refresh to force cache update")

    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser."""
    parser = argparse.ArgumentParser(
        prog="ai-groq",
        description="Groq API - Ultra-fast LLM inference with OpenAI SDK",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ai-groq health               Check Groq API health
  ai-groq health --sanity      Run with inference sanity check
  ai-groq list                 List all available models (uses cache)
  ai-groq list --refresh       Force refresh model list from API
  ai-groq list --verbose       Show detailed model information

Environment Variables:
  GROQ_API_KEY          Groq API key

Resources:
  https://console.groq.com/docs
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # health command
    health_parser = subparsers.add_parser("health", help="Check provider health")
    health_parser.add_argument(
        "--provider",
        choices=list(PROVIDERS.keys()),
        help="Check specific provider (default: groq)",
    )
    health_parser.add_argument(
        "--sanity",
        action="store_true",
        help="Run inference sanity check",
    )

    # list command
    list_parser = subparsers.add_parser("list", help="List available models from provider")
    list_parser.add_argument(
        "--provider",
        choices=list(PROVIDERS.keys()),
        help="List models from specific provider (default: groq)",
    )
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
    elif args.command == "list":
        return cmd_list(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
