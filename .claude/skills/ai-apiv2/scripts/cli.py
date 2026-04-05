#!/usr/bin/env python3
"""
Multi-Provider API CLI - Health checks using OpenAI SDK.

Provides CLI tools for checking health across 5 OpenAI-compatible providers.
"""

from __future__ import annotations

import argparse
import sys

import api_key as api_key_module

# Provider configurations
PROVIDERS = {
    "chutes": {
        "base_url": "https://llm.chutes.ai/v1",
        "default_model": "chutes/moonshotai/Kimi-K2.5-TEE",
        "name": "Chutes",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "anthropic/claude-3.5-sonnet",
        "name": "OpenRouter",
    },
    "nvidia": {
        "base_url": "https://integrate.api.nvidia.com/v1",
        "default_model": "nvidia/llama-3.1-nemotron-70b-instruct",
        "name": "NVIDIA NIM",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "default_model": "gemini-2.5-flash",
        "name": "Gemini",
    },
    "zai": {
        "base_url": "https://api.z.ai/api/coding/paas/v4",
        "default_model": "glm-4.7",
        "name": "z.ai",
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
                # Just test connectivity via models list (if available) or minimal request
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


def cmd_list(_args: argparse.Namespace) -> int:
    """List available providers and their API key status."""
    print("📋 Provider Status:")
    print()

    for provider, config in PROVIDERS.items():
        api_key = api_key_module.get_api_key(provider)
        has_key = api_key is not None

        icon = "✅" if has_key else "❌"
        print(f"  {icon} {provider:12} ({config['name']})")
        print(f"     Base URL: {config['base_url']}")
        print(f"     Model:    {config['default_model']}")
        if has_key:
            env_key = api_key_module.PROVIDER_ENV_KEYS[provider]
            print(f"     Key:      {env_key} is set")
        print()

    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser."""
    parser = argparse.ArgumentParser(
        prog="ai-apiv2",
        description="Multi-Provider LLM API - OpenAI SDK unified interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ai-apiv2 health                    Check all providers with API keys
  ai-apiv2 health --provider chutes  Check specific provider
  ai-apiv2 health --sanity           Run with inference sanity check
  ai-apiv2 list                      Show all providers and status

Environment Variables:
  CHUTES_API_KEY        Chutes API key
  OPENROUTER_API_KEY    OpenRouter API key
  NVIDIA_API_KEY        NVIDIA NIM API key
  GEMINI_API_KEY        Gemini API key
  ZAI_API_KEY           z.ai API key

Providers:
  chutes      Chutes.ai - 256K context, SOTA coding
  openrouter  OpenRouter - 300+ models, intelligent routing
  nvidia      NVIDIA NIM - GPU acceleration, 128K context
  gemini      Google Gemini - 2M context, fast
  zai         z.ai (Zhipu) - GLM-4.7, coding focus

Resources:
  /ai-chutes   - Chutes-specific documentation
  /ai-openrouter - OpenRouter-specific documentation
  /ai-nvidia   - NVIDIA NIM-specific documentation
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # health command
    health_parser = subparsers.add_parser("health", help="Check provider health")
    health_parser.add_argument(
        "--provider",
        choices=list(PROVIDERS.keys()),
        help="Check specific provider (default: all with API keys)",
    )
    health_parser.add_argument(
        "--sanity",
        action="store_true",
        help="Run inference sanity check",
    )

    # list command
    subparsers.add_parser("list", help="List all providers and status")

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
