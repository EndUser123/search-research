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
from pathlib import Path


def _read_config_toml() -> str:
    """Read config.toml content, return empty string if not found."""
    config_path = Path(os.environ.get("USERPROFILE", "")) / ".grok" / "config.toml"
    if config_path.exists():
        return config_path.read_text(encoding="utf-8", errors="replace")
    return ""


# Maps provider name -> list of (regex_pattern, group_index) tuples to try
# Patterns match api_key = "..." lines in [model.*] sections
_PROVIDER_PATTERNS = {
    "mistral": [
        (r'\[model\.mistral-medium-latest\].*?api_key\s*=\s*"([^"]+)"', 1),
    ],
    "nvidia": [
        (r'nvapi-([A-Za-z0-9]+)', 0),
    ],
    "openrouter": [
        (r'openrouter[_\s]*api[_\s]*key\s*=\s*"([^"]+)"', 1),
        (r'OPENROUTER_API_KEY\s*=\s*"([^"]+)"', 1),
    ],
    "glm": [
        (r'zai[_\s]*coding[_\s]*key\s*=\s*"([^"]+)"', 1),
        (r'ZAI_API_KEY\s*=\s*"([^"]+)"', 1),
    ],
    "groq": [
        (r'groq[_\s]*api[_\s]*key\s*=\s*"([^"]+)"', 1),
        (r'GROQ_API_KEY\s*=\s*"([^"]+)"', 1),
    ],
}

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

    # 2. Check config.toml
    config = _read_config_toml()
    if not config:
        return None

    for pattern, group in _PROVIDER_PATTERNS.get(provider, []):
        m = re.search(pattern, config, re.DOTALL)
        if m:
            # For nvapi- patterns, reconstruct the full key
            if group == 0:
                return m.group(0)
            return m.group(group)

    return None


def load_keys() -> dict[str, str | None]:
    """Load all known API keys. Returns dict with None for missing keys."""
    return {provider: get_api_key(provider) for provider in _PROVIDER_PATTERNS}


if __name__ == "__main__":
    keys = load_keys()
    for provider, key in keys.items():
        status = f"{key[:8]}..." if key else "NOT FOUND"
        print(f"  {provider:15s}: {status}")
