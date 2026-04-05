"""Test fixtures for PRD Verifier testing.

This module provides reusable fixtures for testing the PRD verifier skill
with various scenarios including passing, failing, and partial verification cases.
"""

from .fixtures import (
    tiny_repo_complete,
    tiny_repo_incomplete,
    tiny_repo_no_prd,
    transcript_with_concerns,
    transcript_clean,
    verification_config_enabled,
    verification_config_disabled,
    verification_config_custom_thresholds,
)

__all__ = [
    "tiny_repo_complete",
    "tiny_repo_incomplete",
    "tiny_repo_no_prd",
    "transcript_with_concerns",
    "transcript_clean",
    "verification_config_enabled",
    "verification_config_disabled",
    "verification_config_custom_thresholds",
]
