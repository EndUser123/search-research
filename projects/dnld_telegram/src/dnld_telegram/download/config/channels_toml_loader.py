from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import tomllib
else:
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib


def _load_binary(path: Path) -> bytes:
    with path.open("rb") as f:
        return f.read()


def load_telegram_channels(path: Path | None = None) -> dict[str, Any]:
    """Load telegram channels from TOML file with proper error handling."""
    root = Path(__file__).resolve().parents[2]
    p = path or (root / "channels.toml")
    if not p.exists():
        raise FileNotFoundError(f"channels.toml not found at {p}")

    data = _load_binary(p)
    if tomllib:
        parsed = tomllib.loads(data.decode("utf-8"))
    else:
        parsed = {}

    # Return the TELEGRAM_CHANNELS section or fall back to legacy format
    if "TELEGRAM_CHANNELS" in parsed:
        return parsed["TELEGRAM_CHANNELS"]
    elif "channels" in parsed:
        # Support new format if available
        channels = parsed["channels"]
        if not isinstance(channels, list):
            raise ValueError("channels.toml must define a [channels] array")
        return parsed
    else:
        raise ValueError(
            "channels.toml must define either [TELEGRAM_CHANNELS] or [channels] section"
        )


def get_channels() -> dict[str, Any]:
    return load_telegram_channels()
