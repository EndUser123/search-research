#!/usr/bin/env python3
"""
OpenRouter CLI - Model discovery with specialization columns.

Shows models categorized by capabilities: coding, reasoning, vision, tools, speed.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import api_key as api_key_module


def detect_specializations(model: dict) -> dict[str, str]:
    """Detect model specializations from model metadata."""
    name = model.get("name", "").lower()
    model_id = model.get("id", "").lower()
    description = model.get("description", "").lower()
    context_length = model.get("context_length", 0)

    # Architecture hints
    architecture = model.get("architecture", {})
    modality = architecture.get("modality", "text+text")

    specializations = {
        "coding": "",
        "reasoning": "",
        "vision": "",
        "tools": "",
        "speed": "",
    }

    # Coding specialization
    coding_keywords = [
        "code",
        "coder",
        "codex",
        "deepseek-coder",
        "star-coder",
        "code-llama",
        "codegen",
        "wizardcoder",
    ]
    if any(k in name or k in model_id for k in coding_keywords):
        specializations["coding"] = "✓"
    elif "claude-3.5-sonnet" in model_id or "claude-3.7-sonnet" in model_id:
        specializations["coding"] = "✓"
    elif "gpt-4o" in model_id:
        specializations["coding"] = "✓"

    # Reasoning specialization
    reasoning_keywords = [
        "o1",
        "o3",
        "reasoning",
        "reason",
        "think",
        "claude-3.7",
        "gemini-2.5",
        "gemini-2.0",
        "deepseek-r1",
    ]
    if any(k in model_id or k in name for k in reasoning_keywords):
        specializations["reasoning"] = "✓"
    elif "claude-3.5-sonnet" in model_id or "claude-3-opus" in model_id:
        specializations["reasoning"] = "✓"
    elif "gpt-4" in model_id and "mini" not in model_id:
        specializations["reasoning"] = "✓"

    # Vision specialization (multimodal)
    if "vision" in description or "image" in description:
        specializations["vision"] = "✓"
    elif "image" in modality or "video" in modality:
        specializations["vision"] = "✓"
    elif any(k in model_id for k in ["vision", "multimodal", "mm"]):
        specializations["vision"] = "✓"
    elif any(k in model_id for k in ["gpt-4o", "gpt-4.1", "claude-3.5", "claude-3.7", "gemini-2"]):
        specializations["vision"] = "✓"

    # Tools/Function calling specialization
    tools_keywords = ["tools", "function", "agent"]
    if any(k in description for k in tools_keywords):
        specializations["tools"] = "✓"
    elif "claude" in model_id or "gpt-4" in model_id:
        specializations["tools"] = "✓"

    # Speed specialization (fast models)
    speed_keywords = ["flash", "turbo", "haiku", "mini", "fast", "lite", "nano"]
    if any(k in model_id or k in name for k in speed_keywords):
        specializations["speed"] = "✓"
    elif context_length > 1000000:  # Large context often means optimized for speed
        specializations["speed"] = "~"

    return specializations


def get_provider_from_id(model_id: str) -> str:
    """Extract provider name from model ID."""
    parts = model_id.split("/")
    if len(parts) > 1:
        return parts[0]
    return "openrouter"


def format_price(pricing: dict | None, key: str) -> str:
    """Format price from pricing dict."""
    if pricing is None:
        return "-"
    value = pricing.get(key)
    if value is None or value == "0" or value == 0:
        return "Free"
    if float(value) < 0.01:
        return f"${float(value) * 1000:.2f}/M"
    return f"${float(value):.2f}"


def format_context(context_length: int) -> str:
    """Format context length for display."""
    if context_length >= 1000000:
        return f"{context_length // 1000000}M"
    elif context_length >= 1000:
        return f"{context_length // 1000}k"
    return str(context_length)


# ==================== CACHE INTEGRATION ====================


def get_cache_path() -> Path:
    """Get the path to the free models cache file."""
    return Path(__file__).parent.parent / "free-models.json"


def load_free_models_cache() -> dict | None:
    """Load the free models cache. Returns None if missing or expired."""
    cache_path = get_cache_path()

    if not cache_path.exists():
        return None

    try:
        cache_data = json.loads(cache_path.read_text())
        next_refresh = cache_data.get("next_refresh")
        if next_refresh is None:
            return None

        if time.time() > next_refresh:
            return None  # Cache expired

        return cache_data
    except (OSError, json.JSONDecodeError):
        return None


def get_cached_model_ids() -> set[str] | None:
    """Get set of free model IDs from cache. Returns None if cache unavailable."""
    cache = load_free_models_cache()
    if cache is None:
        return None
    return {m["id"] for m in cache.get("models", [])}


# ==================== TABLE FORMATTING ====================


def print_table(
    models: list[dict],
    filter_specialization: str | None = None,
    max_rows: int = 50,
) -> None:
    """Print models as a formatted table."""
    if not models:
        print("No models found.")
        return

    # Filter by specialization if requested
    if filter_specialization:
        filter_specialization = filter_specialization.lower()
        models = [m for m in models if detect_specializations(m).get(filter_specialization) == "✓"]
        if not models:
            print(f"No models found with '{filter_specialization}' specialization.")
            return

    # Limit rows
    models = models[:max_rows]

    # Define columns
    columns = [
        "Model",
        "Provider",
        "Ctx",
        "Code",
        "Reason",
        "Vis",
        "Tools",
        "Speed",
        "Prompt",
        "Compl",
    ]
    col_widths = [35, 12, 6, 5, 6, 4, 5, 5, 8, 8]

    # Print header
    header_parts = []
    for col, width in zip(columns, col_widths):
        header_parts.append(col.ljust(width))
    print("".join(header_parts))
    print("-" * sum(col_widths))

    # Print rows
    for model in models:
        model_id = model.get("id", "")
        name = model.get("name", model_id)

        # Truncate model name for display
        display_name = name[:34] if len(name) > 34 else name

        provider = get_provider_from_id(model_id)
        provider_display = provider[:11]

        pricing = model.get("pricing", {})
        prompt_price = format_price(pricing, "prompt")
        completion_price = format_price(pricing, "completion")

        specializations = detect_specializations(model)

        row_parts = [
            display_name.ljust(35),
            provider_display.ljust(12),
            format_context(model.get("context_length", 0)).ljust(6),
            specializations["coding"].ljust(5),
            specializations["reasoning"].ljust(6),
            specializations["vision"].ljust(4),
            specializations["tools"].ljust(5),
            specializations["speed"].ljust(5),
            prompt_price.ljust(8),
            completion_price.ljust(8),
        ]
        print("".join(row_parts))

    if len(models) == max_rows:
        print(f"\nShowing {max_rows} models. Use --all to show all models.")


def fetch_models(api_key: str | None) -> list[dict]:
    """Fetch models from OpenRouter API."""
    url = "https://openrouter.ai/api/v1/models"
    headers = {}

    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())
            return data.get("data", [])
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("Error: Invalid API key", file=sys.stderr)
        else:
            print(f"Error: HTTP {e.code}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error fetching models: {e}", file=sys.stderr)
        sys.exit(1)


# ==================== COMMAND HANDLERS ====================


def show_top_free_models(models: list[dict]) -> None:
    """Show top free models by category (190K+ context only)."""

    # Filter for free models with 190K+ context
    def is_free(m: dict) -> bool:
        pricing = m.get("pricing", {})
        return all(
            pricing.get(k) in (None, "0", 0) for k in ("prompt", "completion", "request", "image")
        )

    free_models = [m for m in models if is_free(m) and m.get("context_length", 0) >= 190000]

    if not free_models:
        print("No free models with 190K+ context found.")
        return

    # Categorize by specialization
    categories = {
        "coding": [],
        "reasoning": [],
        "vision": [],
        "speed": [],
        "tools": [],
    }

    for model in free_models:
        specs = detect_specializations(model)
        for category in categories:
            if specs.get(category) == "✓":
                categories[category].append(model)

    # Display top picks per category
    print("\n=== TOP FREE MODELS (190K+ Context) ===\n")

    for category, cat_models in categories.items():
        if not cat_models:
            continue

        # Sort by context length (descending) and pick top 3
        cat_models.sort(key=lambda m: m.get("context_length", 0), reverse=True)
        top_models = cat_models[:3]

        print(f"\n{category.upper()}")
        print("-" * 50)
        for model in top_models:
            name = model.get("name", model["id"])
            ctx = format_context(model.get("context_length", 0))
            provider = get_provider_from_id(model["id"])
            print(f"  {name[:40]}")
            print(f"    Provider: {provider} | Context: {ctx}")

    print()


def cmd_list(args: argparse.Namespace) -> int:
    """List models with specialization table."""
    api_key = api_key_module.get_api_key()

    # Show top free models if requested
    if args.top_free:
        api_key = api_key_module.require_api_key()  # Will exit if not set
        models = fetch_models(api_key)
        show_top_free_models(models)
        return 0

    # For free model filtering, try to use cache
    free_model_ids = None
    if not args.include_paid:
        free_model_ids = get_cached_model_ids()
        if free_model_ids is None:
            # Cache unavailable - need API key
            if not api_key_module.is_api_key_available():
                print(
                    "Cache unavailable. Set OPENROUTER_API_KEY or run:\n"
                    "  OPENROUTER_API_KEY=xxx python fetch-free-models.py",
                    file=sys.stderr,
                )
                return 1

    # Fetch models (if cache available, we can still fetch without API key for non-free)
    if not api_key_module.is_api_key_available() and not free_model_ids:
        print("Warning: No OPENROUTER_API_KEY set. Showing limited results.", file=sys.stderr)

    models = fetch_models(api_key)

    # Filter to free models using cache
    if not args.include_paid:
        if free_model_ids is not None:
            original_count = len(models)
            models = [m for m in models if m.get("id") in free_model_ids]
            cache_info = load_free_models_cache()
            if cache_info:
                next_refresh = cache_info.get("next_refresh", 0)
                hours_until = (next_refresh - time.time()) / 3600
                print(f"Showing {len(models)} free models (cache refresh in {hours_until:.1f}h)\n")
            else:
                print(f"Showing {len(models)} free models\n")
        else:
            # No cache - filter by pricing (slow, requires API)
            def is_free(m: dict) -> bool:
                pricing = m.get("pricing", {})
                return all(
                    pricing.get(k) in (None, "0", 0)
                    for k in ("prompt", "completion", "request", "image")
                )

            original_count = len(models)
            models = [m for m in models if is_free(m)]
            print(f"Showing {len(models)} free models (no cache - run fetch-free-models.py)\n")

    # Filter by provider if specified
    if args.provider:
        models = [m for m in models if get_provider_from_id(m["id"]) == args.provider.lower()]

    # Filter by specialization if specified
    filter_spec = args.filter if hasattr(args, "filter") else None

    print_table(
        models,
        filter_specialization=filter_spec,
        max_rows=args.limit if not args.all else 1000,
    )

    return 0


def cmd_info(args: argparse.Namespace) -> int:
    """Show detailed info about a specific model."""
    api_key = api_key_module.get_api_key()
    models = fetch_models(api_key)

    # Find model by ID
    target = args.model.lower()
    model = None
    for m in models:
        if m.get("id", "").lower() == target or m.get("name", "").lower() == target:
            model = m
            break

    if not model:
        print(f"Model '{args.model}' not found.", file=sys.stderr)
        return 1

    # Display model info
    print(f"Model: {model.get('name', model['id'])}")
    print(f"ID: {model.get('id')}")
    print(f"Provider: {get_provider_from_id(model.get('id', ''))}")
    print(f"Context: {format_context(model.get('context_length', 0))} tokens")

    pricing = model.get("pricing", {})
    print("\nPricing:")
    print(f"  Prompt: {format_price(pricing, 'prompt')}")
    print(f"  Completion: {format_price(pricing, 'completion')}")

    specializations = detect_specializations(model)
    print("\nSpecializations:")
    for spec, value in specializations.items():
        if value:
            print(f"  {spec.capitalize()}: {value}")

    description = model.get("description", "")
    if description:
        print(f"\nDescription:\n  {description}")

    return 0


def cmd_providers(_args: argparse.Namespace) -> int:
    """List all available providers."""
    api_key = api_key_module.get_api_key()
    models = fetch_models(api_key)

    providers = {}
    for m in models:
        provider = get_provider_from_id(m.get("id", ""))
        providers[provider] = providers.get(provider, 0) + 1

    print("Available providers:")
    for provider, count in sorted(providers.items(), key=lambda x: x[1], reverse=True):
        print(f"  {provider}: {count} models")

    return 0


def cmd_health(args: argparse.Namespace) -> int:
    """Check OpenRouter API health and connectivity.

    Validates API key, tests connectivity, and optionally runs a sanity check
    with a free model. Returns exit code 0 if healthy, 1 if any check fails.
    """
    all_healthy = True
    status = {}

    # 1. Check API key
    print("🔑 Checking API key...", end=" ")
    api_key = api_key_module.get_api_key()
    if not api_key:
        print("[FAIL]")
        print("  ❌ OPENROUTER_API_KEY not set")
        print("  Get your key at: https://openrouter.ai/keys")
        return 1
    print("[OK]")
    status["api_key"] = "present"

    # 2. Test connectivity to models endpoint
    print("🌐 Testing API connectivity...", end=" ")
    try:
        url = "https://openrouter.ai/api/v1/models"
        headers = {"Authorization": f"Bearer {api_key}"}
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=10) as response:
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
            print("  Verify your key at: https://openrouter.ai/keys")
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

    # 3. Optional sanity check with free model
    if args.sanity:
        print("🧪 Testing inference...", end=" ")
        try:
            # Use a known free model for sanity check
            sanity_model = "google/gemma-2-9b-it:free"
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:3000",
                "X-OpenRouter-Title": "ai-openrouter-health-check",
            }
            data = json.dumps(
                {
                    "model": sanity_model,
                    "messages": [{"role": "user", "content": "OK"}],
                    "max_tokens": 5,
                }
            ).encode()

            req = urllib.request.Request(url, data=data, headers=headers)

            with urllib.request.urlopen(req, timeout=30) as response:
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
        print("✅ OpenRouter API is healthy")
    else:
        print("❌ OpenRouter API health check failed")
        print("\nStatus details:")
        for key, value in status.items():
            print(f"  {key}: {value}")

    return 0 if all_healthy else 1


def cmd_quota(_args: argparse.Namespace) -> int:
    """Check OpenRouter account credit balance.

    Returns exit code 0 if successful, 1 if API key error.
    """
    api_key = api_key_module.get_api_key()
    if not api_key:
        print("❌ OPENROUTER_API_KEY not set")
        print("Get your key at: https://openrouter.ai/keys")
        return 1

    print("💰 Checking OpenRouter credits...")

    try:
        url = "https://openrouter.ai/api/v1/credits"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://api.openrouter.ai/",
        }
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read())
                total_credits = data.get("data", {}).get("total_credits", 0)
                total_usage = data.get("data", {}).get("total_usage", 0)
                credits_remaining = max(0, total_credits - total_usage)

                print("\n✅ OpenRouter Credits:")
                print(f"   Remaining: ${credits_remaining:.2f}")
                print(f"   Total: ${total_credits:.2f}")
                print(f"   Used: ${total_usage:.2f}")

                if credits_remaining < 10:
                    print("\n⚠️  Low credits warning!")
                elif credits_remaining < 1:
                    print("\n❌ Credits exhausted!")

                return 0
            elif response.status == 401:
                print("❌ Invalid API key (401 Unauthorized)")
                print("Verify your key at: https://openrouter.ai/keys")
                return 1
            else:
                print(f"❌ Unexpected status: {response.status}")
                return 1

    except urllib.error.HTTPError as e:
        print(f"❌ HTTP error: {e.code}")
        return 1
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return 1


# ==================== MAIN CLI ====================


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser."""
    parser = argparse.ArgumentParser(
        prog="openrouter",
        description="OpenRouter CLI - Model discovery with specializations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  openrouter list                    List top 50 free models (default)
  openrouter list --include-paid     List all models including paid
  openrouter list --all              Show unlimited results
  openrouter list --top-free         Show top free models by category
  openrouter list --filter coding    Show coding-specialized models
  openrouter list --provider anthropic  Show Anthropic models
  openrouter list --limit 20         Show 20 models
  openrouter info claude-3.5-sonnet  Show model details
  openrouter providers               List all providers

Specialization columns:
  Code   - Code generation and programming
  Reason - Complex reasoning and analysis
  Vis    - Vision/image understanding
  Tools  - Function/tool calling support
  Speed  - Fast/low-latency models
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # list command
    list_parser = subparsers.add_parser("list", help="List models with specializations")
    list_parser.add_argument(
        "--all", "-a", action="store_true", help="Show all models (not limited)"
    )
    list_parser.add_argument(
        "--include-paid",
        action="store_true",
        help="Include paid models (default: free only)",
    )
    list_parser.add_argument(
        "--filter",
        choices=["coding", "reasoning", "vision", "tools", "speed"],
        help="Filter by specialization",
    )
    list_parser.add_argument(
        "--provider", "-p", help="Filter by provider (e.g., anthropic, openai)"
    )
    list_parser.add_argument(
        "--limit", "-l", type=int, default=50, help="Max models to show (default: 50)"
    )
    list_parser.add_argument(
        "--top-free",
        action="store_true",
        help="Show top free models by category (190K+ context only)",
    )

    # info command
    info_parser = subparsers.add_parser("info", help="Show detailed model information")
    info_parser.add_argument("model", help="Model ID or name")

    # providers command
    subparsers.add_parser("providers", help="List all providers")

    # health command
    health_parser = subparsers.add_parser("health", help="Check API health and connectivity")
    health_parser.add_argument(
        "--sanity",
        action="store_true",
        help="Run inference sanity check with free model",
    )

    # quota command
    subparsers.add_parser("quota", help="Check account credit balance")

    return parser


def main() -> int:
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "list":
        return cmd_list(args)
    elif args.command == "info":
        return cmd_info(args)
    elif args.command == "providers":
        return cmd_providers(args)
    elif args.command == "health":
        return cmd_health(args)
    elif args.command == "quota":
        return cmd_quota(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
