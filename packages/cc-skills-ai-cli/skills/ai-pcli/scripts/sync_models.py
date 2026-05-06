#!/usr/bin/env python3
"""Sync pi models.json with free models from various providers.

Fetches available models from each provider's /v1/models endpoint, adds new
models, removes ones no longer available, and preserves user overrides.

Supports: OpenRouter (free + paid), NVIDIA NIM, Cerebras, Groq, z.ai, MiniMax.

API keys are resolved from ~/.pi/agent/auth.json first, then environment
variables.  Models with <128K context window or non-chat types (whisper, tts,
embedding, etc.) are automatically filtered out.

Usage:
    python sync_models.py                # sync all providers
    python sync_models.py --cerebras     # only Cerebras
    python sync_models.py --groq         # only Groq
    python sync_models.py --zai          # only z.ai (Zhipu)
    python sync_models.py --minimax      # only MiniMax
    python sync_models.py --openrouter   # only OpenRouter
    python sync_models.py --nvidia       # only NVIDIA NIM
    python sync_models.py --dry-run      # show changes without writing
    python sync_models.py --list         # just list current models per provider

Examples:
    # Preview what would change
    python sync_models.py --dry-run

    # Sync everything
    python sync_models.py

    # Sync only fast inference providers
    python sync_models.py --cerebras --groq

    # See what models are currently configured
    python sync_models.py --list
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
import urllib.error
import argparse
import textwrap
from pathlib import Path

MODELS_FILE = Path.home() / ".pi" / "agent" / "models.json"

# Defaults for new models
DEFAULTS = {
    "reasoning": True,
    "input": ["text"],
    "contextWindow": 131072,
    "maxTokens": 32768,
}

PROVIDERS = {
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/models",
        "baseUrl": "https://openrouter.ai/api/v1",
        "api": "openai-completions",
        "apiKey_env": "OPENROUTER_API_KEY",
        "authHeader": True,
        "compat": {
            "supportsDeveloperRole": True,
            "supportsReasoningEffort": True,
        },
        "description": "Free ($0) models + any manually-added paid models",
    },
    "nvidia-nim": {
        "url": "https://integrate.api.nvidia.com/v1/models",
        "baseUrl": "https://integrate.api.nvidia.com/v1",
        "api": "openai-completions",
        "apiKey_env": "NVIDIA_API_KEY",
        "apiKey_default": "nvidia",
        "authHeader": True,
        "description": "All models (free API)",
    },
    "cerebras": {
        "url": "https://api.cerebras.ai/v1/models",
        "baseUrl": "https://api.cerebras.ai/v1",
        "api": "openai-completions",
        "apiKey_env": "cerebras_API_KEY",
        "authHeader": True,
        "compat": {
            "supportsDeveloperRole": False,
            "supportsReasoningEffort": False,
        },
        "description": "Fast inference (free tier)",
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1/models",
        "baseUrl": "https://api.groq.com/openai/v1",
        "api": "openai-completions",
        "apiKey_env": "GROQ_API_KEY",
        "authHeader": True,
        "compat": {
            "supportsDeveloperRole": False,
            "supportsReasoningEffort": False,
        },
        "description": "Fast inference (free tier)",
    },
    "z-ai": {
        "url": "https://api.z.ai/api/coding/paas/v4/models",
        "baseUrl": "https://api.z.ai/api/coding/paas/v4",
        "api": "openai-completions",
        "apiKey_env": "Z_AI_API_KEY",
        "authHeader": True,
        "compat": {
            "supportsDeveloperRole": False,
            "supportsReasoningEffort": False,
        },
        "description": "GLM models via coding plan",
    },
    "minimax": {
        "url": "https://api.minimax.io/v1/models",
        "baseUrl": "https://api.minimax.io/anthropic",
        "api": "anthropic-messages",
        "apiKey_env": "MINIMAX_API_KEY",
        "authHeader": True,
        "compat": {
            "supportsDeveloperRole": False,
            "supportsReasoningEffort": False,
        },
        "description": "MiniMax models via token plan (Anthropic API format)",
    },
}

# Skip filter: model ID substrings to exclude (non-chat models)
SKIP_SUBSTRINGS = [
    "whisper", "tts", "speech", "guard", "embed", "tool-use",
    "canopy", "distil", "playai", "gemma-2", "allam",
]

# Minimum context window to include (models below this are filtered out)
MIN_CONTEXT_WINDOW = 128000


def fetch_json(url: str, headers: dict | None = None) -> dict:
    """Fetch JSON from a URL."""
    hdrs = {"User-Agent": "pi-sync-models/1.0"}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def get_api_key(provider_cfg: dict) -> str | None:
    """Resolve API key: auth.json -> env var -> default."""
    # First try auth.json
    auth_file = Path.home() / ".pi" / "agent" / "auth.json"
    if auth_file.exists():
        try:
            with open(auth_file, "r", encoding="utf-8") as f:
                auth = json.load(f)
            auth_key_map = {
                "openrouter": "openrouter",
                "nvidia-nim": "nvidia-nim",
                "cerebras": "cerebras",
                "groq": "groq",
                "z-ai": "zai",
                "minimax": "minimax",
            }
            provider_name = provider_cfg.get("_name", "")
            auth_name = auth_key_map.get(provider_name, provider_name)
            if auth_name in auth and isinstance(auth[auth_name], dict):
                key = auth[auth_name].get("key", "")
                if key:
                    return key
        except Exception:
            pass

    # Then try env var
    env_var = provider_cfg.get("apiKey_env", "")
    key = os.environ.get(env_var, "")
    if key:
        return key

    # Then default
    default = provider_cfg.get("apiKey_default")
    if default:
        return default
    return None


def should_skip(model_id: str, context_window: int | None = None) -> bool:
    """Check if a model should be skipped (non-chat or too small context)."""
    mid = model_id.lower()
    if any(s in mid for s in SKIP_SUBSTRINGS):
        return True
    if context_window is not None and context_window < MIN_CONTEXT_WINDOW:
        return True
    return False


# ---------------------------------------------------------------------------
# Provider-specific fetchers
# ---------------------------------------------------------------------------

def fetch_openrouter_models() -> list[dict]:
    """Fetch OpenRouter models - return only $0-cost ones."""
    cfg = PROVIDERS["openrouter"]
    api_key = get_api_key(cfg)
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    data = fetch_json(cfg["url"], headers=headers)

    results = []
    for m in data.get("data", []):
        pricing = m.get("pricing", {})
        prompt = float(pricing.get("prompt", "1") or "1")
        completion = float(pricing.get("completion", "1") or "1")
        if prompt != 0 or completion != 0:
            continue

        modalities = m.get("architecture", {}).get("input_modalities", ["text"])
        inputs = ["text"]
        if "image" in modalities:
            inputs.append("image")
        ctx = m.get("context_length") or m.get("top_provider", {}).get("context_length") or 131072
        max_tokens = m.get("top_provider", {}).get("max_completion_tokens") or 32768
        supported = m.get("supported_parameters", [])
        has_reasoning = "reasoning" in supported or "include_reasoning" in supported

        if should_skip(m["id"], ctx):
            continue

        results.append({
            "id": m["id"],
            "name": m.get("name", m["id"]),
            "reasoning": has_reasoning,
            "input": inputs,
            "contextWindow": ctx,
            "maxTokens": max_tokens,
        })
    return results


def fetch_generic_models(provider_name: str) -> list[dict]:
    """Fetch models from a generic OpenAI-compatible /v1/models endpoint."""
    cfg = PROVIDERS[provider_name]
    api_key = get_api_key(cfg)
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    data = fetch_json(cfg["url"], headers=headers)

    seen: set[str] = set()
    results: list[dict] = []
    for m in data.get("data", []):
        mid = m["id"]
        ctx = m.get("context_window") or m.get("context_length") or None
        if mid in seen or should_skip(mid, ctx):
            continue
        seen.add(mid)

        model_info: dict = {"id": mid}
        if ctx:
            model_info["contextWindow"] = ctx
        mt = m.get("max_completion_tokens")
        if mt:
            model_info["maxTokens"] = mt
        results.append(model_info)
    return results


def fetch_nvidia_models() -> list[dict]:
    return fetch_generic_models("nvidia-nim")


def fetch_cerebras_models() -> list[dict]:
    return fetch_generic_models("cerebras")


def fetch_groq_models() -> list[dict]:
    return fetch_generic_models("groq")


def fetch_zai_models() -> list[dict]:
    return fetch_generic_models("z-ai")


def fetch_minimax_models() -> list[dict]:
    return fetch_generic_models("minimax")


FETCHERS = {
    "openrouter": fetch_openrouter_models,
    "nvidia-nim": fetch_nvidia_models,
    "cerebras": fetch_cerebras_models,
    "groq": fetch_groq_models,
    "z-ai": fetch_zai_models,
    "minimax": fetch_minimax_models,
}

# Stamp provider name into each config for key resolution
for _pname in PROVIDERS:
    PROVIDERS[_pname]["_name"] = _pname


# ---------------------------------------------------------------------------
# Merge logic
# ---------------------------------------------------------------------------

def merge_models(
    existing_models: list[dict],
    api_models: list[dict],
    preserve_fields: set[str] | None = None,
) -> tuple[list[dict], list[str], list[str]]:
    """Merge API models into existing models list.

    Returns (merged_list, added_ids, removed_ids).
    """
    preserve_fields = preserve_fields or {"name", "compat", "cost", "api"}

    existing_by_id = {m["id"]: m for m in existing_models}
    api_by_id = {m["id"]: m for m in api_models}
    api_ids = set(api_by_id)
    existing_ids = set(existing_by_id)

    added_ids = sorted(api_ids - existing_ids)
    removed_ids = sorted(existing_ids - api_ids)

    merged: list[dict] = []
    for api_model in api_models:
        mid = api_model["id"]
        if mid in existing_by_id:
            existing = existing_by_id[mid]
            merged_model = dict(DEFAULTS)
            merged_model.update(api_model)
            for field in preserve_fields:
                if field in existing:
                    merged_model[field] = existing[field]
            merged.append(merged_model)
        else:
            merged_model = dict(DEFAULTS)
            merged_model.update(api_model)
            merged.append(merged_model)

    return merged, added_ids, removed_ids


# ---------------------------------------------------------------------------
# Sync & list commands
# ---------------------------------------------------------------------------

def sync_provider(config: dict, provider_name: str, api_models: list[dict]) -> tuple[int, int]:
    """Sync a single provider's models. Returns (added, removed) counts."""
    print(f"\n{'='*60}")
    print(f"Provider: {provider_name}")
    print(f"{'='*60}")

    cfg = PROVIDERS.get(provider_name, {})
    existing_models = config["providers"].get(provider_name, {}).get("models", [])

    is_openrouter = provider_name == "openrouter"
    merged, added, removed = merge_models(existing_models, api_models)

    if is_openrouter:
        free_ids = {m["id"] for m in api_models}
        paid_models = [
            m for m in existing_models
            if m["id"] not in free_ids
            and (m.get("contextWindow") or DEFAULTS["contextWindow"]) >= MIN_CONTEXT_WINDOW
        ]
        merged_ids = {m["id"] for m in merged}
        paid_ids_preserved: set[str] = set()
        for pm in paid_models:
            if pm["id"] not in merged_ids:
                merged.append(pm)
                paid_ids_preserved.add(pm["id"])
        if paid_models:
            print(f"  Preserved paid models: {len(paid_models)}")
            for pm in paid_models:
                print(f"    = {pm['id']}")
        removed = [r for r in removed if r not in paid_ids_preserved]

    # Ensure provider config exists
    if provider_name not in config["providers"]:
        config["providers"][provider_name] = {}

    provider_config = config["providers"][provider_name]
    if "baseUrl" not in provider_config and "baseUrl" in cfg:
        provider_config["baseUrl"] = cfg["baseUrl"]
    if "api" not in provider_config and "api" in cfg:
        provider_config["api"] = cfg["api"]

    api_key = get_api_key(cfg)
    if api_key:
        if "apiKey" not in provider_config:
            provider_config["apiKey"] = api_key
    elif "apiKey" not in provider_config and "apiKey_default" in cfg:
        provider_config["apiKey"] = cfg["apiKey_default"]

    if "authHeader" not in provider_config and cfg.get("authHeader"):
        provider_config["authHeader"] = True
    if "compat" not in provider_config and "compat" in cfg:
        provider_config["compat"] = cfg["compat"]

    provider_config["models"] = merged

    print(f"  API returned: {len(api_models)} models")
    print(f"  Added: {len(added)}")
    for a in added:
        print(f"    + {a}")
    print(f"  Removed: {len(removed)}")
    for r in removed:
        print(f"    - {r}")
    print(f"  Total: {len(merged)}")

    return len(added), len(removed)


def cmd_sync(args: argparse.Namespace) -> int:
    """Sync models from provider APIs into models.json."""
    any_filter = any([
        args.openrouter, args.nvidia, args.cerebras,
        args.groq, args.zai, args.minimax,
    ])

    providers_to_sync: list[str] = []
    for name in FETCHERS:
        flag = getattr(args, name.replace("-", "_"), None)
        if name == "nvidia-nim" and args.nvidia:
            flag = True
        if not any_filter or flag:
            providers_to_sync.append(name)

    print(f"Loading {MODELS_FILE}...")
    with open(MODELS_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    if "providers" not in config:
        config["providers"] = {}

    total_added = 0
    total_removed = 0
    errors: list[str] = []

    for provider_name in providers_to_sync:
        try:
            api_models = FETCHERS[provider_name]()
            added, removed = sync_provider(config, provider_name, api_models)
            total_added += added
            total_removed += removed
        except Exception as e:
            print(f"\n  ERROR syncing {provider_name}: {e}")
            errors.append(provider_name)

    print(f"\n{'='*60}")
    print(f"Summary: {total_added} added, {total_removed} removed")
    if errors:
        print(f"Errors: {errors}")

    if args.dry_run:
        print("\n[DRY RUN] No changes written.")
    else:
        with open(MODELS_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"\nWritten to {MODELS_FILE}")

    print("Changes take effect next time you open /model (no restart needed).")
    return 1 if errors else 0


def _print_model_list(models: list[dict], existing_ids: set[str] | None = None) -> None:
    """Print a sorted list of models with context and modality info."""
    for m in sorted(models, key=lambda x: x["id"]):
        ctx = m.get("contextWindow", "?")
        ctx_str = f"{ctx // 1024}K" if isinstance(ctx, int) else str(ctx)
        img = "+img" if "image" in m.get("input", []) else ""
        name = m.get("name", "")
        status = ""
        if existing_ids is not None:
            if m["id"] not in existing_ids:
                status = "  [NEW]"
        label = f"  {m['id']}"
        if name and name != m["id"]:
            label += f"  ({name})"
        label += f"  [{ctx_str}{img}]"
        label += status
        print(label)


def cmd_list(args: argparse.Namespace) -> int:
    """List models live from provider APIs, showing diff vs current config."""
    if not MODELS_FILE.exists():
        print(f"No models file found at {MODELS_FILE}")
        return 1

    with open(MODELS_FILE, "r", encoding="utf-8") as f:
        config = json.load(f)

    providers = config.get("providers", {})
    if not providers:
        print("No providers configured.")
        return 0

    # Determine which providers to list
    any_filter = any([
        args.openrouter, args.nvidia, args.cerebras,
        args.groq, args.zai, args.minimax,
    ])
    providers_to_list: list[str] = []
    for name in sorted(FETCHERS):
        flag = getattr(args, name.replace("-", "_"), None)
        if name == "nvidia-nim" and args.nvidia:
            flag = True
        if not any_filter or flag:
            providers_to_list.append(name)

    total_current = 0
    total_api = 0
    total_new = 0
    total_removed = 0
    errors: list[str] = []

    for pname in providers_to_list:
        cfg = PROVIDERS.get(pname, {})
        desc = cfg.get("description", "")
        existing_models = providers.get(pname, {}).get("models", [])
        existing_ids = {m["id"] for m in existing_models}
        total_current += len(existing_models)

        print(f"\n{'='*60}")
        print(f"{pname}  {desc}")
        print(f"{'='*60}")

        try:
            api_models = FETCHERS[pname]()
            api_ids = {m["id"] for m in api_models}
            new_ids = sorted(api_ids - existing_ids)
            removed_ids = sorted(existing_ids - api_ids)

            total_api += len(api_models)
            total_new += len(new_ids)
            total_removed += len(removed_ids)

            _print_model_list(api_models, existing_ids)

            if new_ids:
                print(f"\n  ▲ {len(new_ids)} new (not yet synced): {', '.join(new_ids)}")
            if removed_ids:
                print(f"  ▼ {len(removed_ids)} removed from API: {', '.join(removed_ids)}")
            if not new_ids and not removed_ids:
                print("  ✓ Up to date")

        except Exception as e:
            # Fall back to showing local config if API fails
            print(f"  ⚠ API error: {e}")
            print(f"  Showing local config ({len(existing_models)} models):")
            _print_model_list(existing_models)
            errors.append(pname)

    print(f"\n{'='*60}")
    print(f"Live: {total_api} models  |  Local: {total_current}  |  "
          f"New: {total_new}  |  Gone: {total_removed}")
    if errors:
        print(f"API errors: {errors} (showed local config for those)")
    print("Run without --list to sync, or add --dry-run to preview.")
    return 0


def cmd_providers(args: argparse.Namespace) -> int:
    """Show configured providers and their endpoints."""
    for pname, cfg in sorted(PROVIDERS.items()):
        print(f"\n{pname}")
        print(f"  URL:     {cfg['url']}")
        print(f"  Base:    {cfg['baseUrl']}")
        print(f"  API:     {cfg['api']}")
        print(f"  Key:     {cfg.get('apiKey_env', 'N/A')} (env)")
        desc = cfg.get("description", "")
        if desc:
            print(f"  Info:    {desc}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="sync_models",
        description="Sync pi models.json with free models from various providers.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            examples:
              sync_models.py --dry-run          preview changes
              sync_models.py                    sync all providers
              sync_models.py --cerebras --groq  sync fast inference only
              sync_models.py --list             show current models
              sync_models.py --providers        show provider endpoints

            config:
              Models file:  ~/.pi/agent/models.json
              Auth keys:    ~/.pi/agent/auth.json  (checked first, then env vars)
              Min context:  128K (models below are filtered out)

            supported providers:
              openrouter   Free ($0) models + manually-added paid models
              nvidia-nim   All models (free API)
              cerebras     Fast inference (free tier)
              groq         Fast inference (free tier)
              z-ai         GLM models via coding plan
              minimax      MiniMax models via token plan (Anthropic API format)
        """),
    )

    sub = parser.add_subparsers(dest="command")

    # Default (no subcommand) = sync mode flags
    parser.add_argument("--openrouter", action="store_true", help="Only sync OpenRouter")
    parser.add_argument("--nvidia", action="store_true", help="Only sync NVIDIA NIM")
    parser.add_argument("--cerebras", action="store_true", help="Only sync Cerebras")
    parser.add_argument("--groq", action="store_true", help="Only sync Groq")
    parser.add_argument("--zai", action="store_true", help="Only sync z.ai (Zhipu)")
    parser.add_argument("--minimax", action="store_true", help="Only sync MiniMax")
    parser.add_argument("--dry-run", action="store_true", help="Show changes without writing")
    parser.add_argument("--list", action="store_true", help="List current models per provider")
    parser.add_argument("--providers", action="store_true", help="Show provider endpoints")

    args = parser.parse_args()

    if args.list:
        return cmd_list(args)
    if args.providers:
        return cmd_providers(args)
    return cmd_sync(args)


if __name__ == "__main__":
    sys.exit(main())
