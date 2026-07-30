"""
Shared API key loader for model-calling scripts.

Reads API keys from environment variables first, then falls back to
~/.grok/config.toml. Never hardcodes keys.

Usage:
    from load_api_key import load_keys
    keys = load_keys()
    mistral_key = keys["mistral"]      # or None if not found
    nvidia_key = keys["nvidia"]        # or None if not found
    openrouter_key = keys["openrouter"] # or None if not found

Or for a specific provider:
    from load_api_key import get_api_key
    key = get_api_key("mistral")
"""
from __future__ import annotations

import os
import re
import tomllib
from pathlib import Path
from functools import lru_cache


def _get_config_path() -> Path:
    """Get config.toml path, cross-platform."""
    return Path.home() / ".grok" / "config.toml"


@lru_cache(maxsize=1)
def _read_config_toml() -> str:
    """Read config.toml content, return empty string if not found.

    Cached per-process to avoid re-reading on every API call.
    Clear cache with _read_config_toml.cache_clear() if config changes mid-run.
    """
    config_path = _get_config_path()
    if config_path.exists():
        return config_path.read_text(encoding="utf-8", errors="replace")
    return ""


@lru_cache(maxsize=1)
def _parse_config_keys() -> dict[str, str]:
    """Parse config.toml and extract api_key values grouped by provider prefix.

    Uses tomllib (Python 3.11+) for proper TOML parsing instead of fragile regex.
    Falls back to regex if tomllib is unavailable.

    Returns a dict mapping provider name -> api_key string.
    """
    config_path = _get_config_path()
    if not config_path.exists():
        return {}

    keys: dict[str, str] = {}

    # Try tomllib first (proper parsing)
    try:
        with open(config_path, "rb") as f:
            config = tomllib.load(f)
        # config.toml uses [model.<slug>] which tomllib parses as nested dict:
        # config["model"]["<slug>"] = { "api_key": "...", ... }
        model_sections = config.get("model", {})
        if not isinstance(model_sections, dict):
            model_sections = {}
        for slug, settings in model_sections.items():
            if not isinstance(settings, dict):
                continue
            api_key = settings.get("api_key")
            if not api_key or not isinstance(api_key, str):
                continue
            provider = _classify_provider(slug, api_key)
            if provider and provider not in keys:
                keys[provider] = api_key
        if keys:
            return keys
    except Exception:
        pass

    # Fallback: regex extraction
    config_text = _read_config_toml()
    if not config_text:
        return {}

    # Match [model.*] sections and extract api_key
    section_pattern = re.compile(
        r'\[model\.([^]]+)\].*?api_key\s*=\s*"([^"]+)"',
        re.DOTALL,
    )
    for m in section_pattern.finditer(config_text):
        model_name = m.group(1)
        api_key = m.group(2)
        provider = _classify_provider(model_name, api_key)
        if provider and provider not in keys:
            keys[provider] = api_key

    # Also match bare nvapi- keys (NVIDIA keys have a distinctive prefix)
    nv_match = re.search(r'(nvapi-[A-Za-z0-9]+)', config_text)
    if nv_match and "nvidia" not in keys:
        keys["nvidia"] = nv_match.group(1)

    return keys


def _classify_provider(model_name: str, api_key: str) -> str | None:
    """Classify a model section name + key into a provider bucket."""
    model_lower = model_name.lower()
    key_lower = api_key.lower()

    if key_lower.startswith("nvapi-"):
        return "nvidia"
    if "mistral" in model_lower:
        return "mistral"
    if "openrouter" in model_lower or "or-" in model_lower or key_lower.startswith("sk-or-"):
        return "openrouter"
    if "glm" in model_lower or "zai" in model_lower:
        return "glm"
    if "groq" in model_lower or key_lower.startswith("gsk_"):
        return "groq"
    return None


# Environment variable names to check first
_ENV_VARS = {
    "mistral": ["MISTRAL_API_KEY"],
    "nvidia": ["NVIDIA_API_KEY"],
    "openrouter": ["OPENROUTER_API_KEY"],
    "glm": ["ZAI_API_KEY", "ZAI_CODING_KEY"],
    "groq": ["GROQ_API_KEY"],
}


def get_api_key(provider: str) -> str | None:
    """Get an API key for a provider. Checks env first, then config.toml.

    Args:
        provider: one of "mistral", "nvidia", "openrouter", "glm", "groq"

    Returns:
        API key string, or None if not found.
    """
    provider = provider.lower()

    # 1. Check environment variables
    for env_var in _ENV_VARS.get(provider, []):
        val = os.environ.get(env_var)
        if val:
            return val

    # 2. Check config.toml (cached)
    keys = _parse_config_keys()
    return keys.get(provider)


def load_keys() -> dict[str, str | None]:
    """Load all known API keys. Returns dict with None for missing keys."""
    return {provider: get_api_key(provider) for provider in _ENV_VARS}


if __name__ == "__main__":
    keys = load_keys()
    for provider, key in keys.items():
        status = "LOADED" if key else "NOT FOUND"
        print(f"  {provider:15s}: {status}")
