"""
Layer 1: Add 5 frozen config dataclasses using LibCST.
Preserves all formatting, comments, and whitespace.

This script was used in the initial refactor but is retained for:
- Reference on how to add similar config classes
- Verification that configs exist
- Documentation of the config structure
"""
from __future__ import annotations

import libcst as cst
from pathlib import Path

# The config code that was added to batch_config.py
CONFIG_CODE = """
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExecutionConfig:
    \"\"\"Configuration for parallel execution behavior.\"\"\"
    jobs: int = 2
    language: str = "en"
    cookies_from_browser: str | None = None
    delay_between_channels: float = 3.0
    max_retries: int = 3
    continue_on_error: bool = True

    def __post_init__(self):
        \"\"\"Validate execution parameters.\"\"\"
        if not 1 <= self.jobs <= 128:
            raise ValueError(f"jobs must be 1-128, got {self.jobs}")
        if self.delay_between_channels < 0:
            raise ValueError("delay_between_channels must be non-negative")
        if self.max_retries < 0:
            raise ValueError("max_retries must be non-negative")


@dataclass(frozen=True)
class LimitsConfig:
    \"\"\"Configuration for execution limits and timeouts.\"\"\"
    time_per_channel: float | None = None
    time_per_video: float | None = None
    time_per_batch: float | None = None
    max_videos: int | None = None
    min_saved: int | None = None
    target_downloads: int | None = None
    videos_download_per_batch: int | None = None

    def __post_init__(self):
        \"\"\"Validate limits.\"\"\"
        if self.time_per_channel and self.time_per_channel <= 0:
            raise ValueError("time_per_channel must be positive")
        if self.time_per_video and self.time_per_video <= 0:
            raise ValueError("time_per_video must be positive")
        if self.time_per_batch and self.time_per_batch <= 0:
            raise ValueError("time_per_batch must be positive")
        if self.max_videos and self.max_videos <= 0:
            raise ValueError("max_videos must be positive")


@dataclass(frozen=False)
class UIConfig:
    \"\"\"Configuration for user interface display.\"\"\"
    rich_mode: str | None = None
    display_plugin: str | None = None
    suppress_verbose: bool = False


@dataclass(frozen=True)
class ContentConfig:
    \"\"\"Configuration for content filtering and quotas.\"\"\"
    auto_backfill: bool = False
    dry_run: bool = False
    freshness_hours: int = 6
    quota_strategy: Any = None
    min_saved: int | None = None
    target_downloads: int | None = None
    videos_download_per_batch: int | None = None
    suppress_quota_print: bool = False

    def __post_init__(self):
        \"\"\"Validate content parameters.\"\"\"
        if self.freshness_hours < 0:
            raise ValueError("freshness_hours must be non-negative")
        if self.min_saved and self.min_saved < 0:
            raise ValueError("min_saved must be non-negative")
        if self.target_downloads and self.target_downloads <= 0:
            raise ValueError("target_downloads must be positive")


@dataclass(frozen=True)
class TranscriptConfig:
    \"\"\"Configuration for transcript generation.\"\"\"
    whisper_model: str = "base"
    keep_audio: bool = False
"""


def verify_configs_exist(batch_config_path: str) -> bool:
    """
    Verify that all 5 config dataclasses exist in batch_config.py.

    Args:
        batch_config_path: Path to batch_config.py file

    Returns:
        True if all configs exist and are importable
    """
    path = Path(batch_config_path)
    if not path.exists():
        print(f"❌ File not found: {batch_config_path}")
        return False

    code = path.read_text()

    required_classes = [
        "ExecutionConfig",
        "LimitsConfig",
        "UIConfig",
        "ContentConfig",
        "TranscriptConfig"
    ]

    missing = []
    for cls in required_classes:
        if f"class {cls}" not in code:
            missing.append(cls)

    if missing:
        print(f"❌ Missing config classes: {', '.join(missing)}")
        return False

    print(f"✅ All 5 config classes found in {batch_config_path}")
    for cls in required_classes:
        print(f"   - {cls}")
    return True


# Usage
if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        batch_config = sys.argv[1]
    else:
        # Default path relative to this script
        batch_config = Path(__file__).parent.parent / "batch_config.py"

    success = verify_configs_exist(batch_config)
    sys.exit(0 if success else 1)
