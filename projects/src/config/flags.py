"""
Feature Flags Configuration using Flagsmith.

This module initializes the Flagsmith client for feature flag management.
"""

import os
from functools import lru_cache

from flagsmith import Flagsmith

# Initialize Flagsmith with environment variable
# Defaults to offline mode if key not present to prevent crash during dev
_API_KEY = os.getenv("FLAGSMITH_API_KEY", "ser.offline_key")

flagsmith = Flagsmith(
    environment_key=_API_KEY,
    # enable_local_evaluation=True,  # optimal for server-side
)


@lru_cache(maxsize=128)
def get_flag(feature_key: str, default: bool = False) -> bool:
    """
    Get a feature flag status with safe default.

    Args:
        feature_key: The unique key for the flag.
        default: Default value if flag is missing or error occurs.

    Returns:
        bool: True if feature is enabled.
    """
    try:
        if _API_KEY == "ser.offline_key":
            return default

        flags = flagsmith.get_environment_flags()
        return flags.is_feature_enabled(feature_key)
    except Exception as e:
        print(f"Warning: Flagsmith error for {feature_key}: {e}")
        return default


def get_trait(identity: str, trait_key: str) -> str:
    """Get a user trait for progressive rollout logic."""
    try:
        # Implementation would go here
        return "default"
    except Exception:
        return "error"
