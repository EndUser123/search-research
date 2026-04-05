#!/usr/bin/env python3
"""
Fetch free models from OpenRouter catalog and write to file.

Cache expires at 00:00 and 12:00 UTC (twice daily).
Automatically refreshes when expired. Notifies when the model list changes.

Usage:
    OPENROUTER_API_KEY=xxx python fetch-free-models.py
    python fetch-free-models.py <output_file>
    python fetch-free-models.py --fresh  # force refresh
    python fetch-free-models.py --check-stale  # exit 1 if expired
"""

import argparse
import datetime as dt
import json
import os
import sys
import time
from pathlib import Path

# Refresh times: 00:00 and 12:00 UTC
REFRESH_HOURS = (0, 12)


def next_refresh_time() -> float:
    """Calculate Unix timestamp of next refresh time (00:00 or 12:00 UTC)."""
    now = dt.datetime.now(dt.timezone.utc)
    today = now.date()

    # Get today's refresh times
    midnight = dt.datetime.combine(today, dt.time(0, 0), tzinfo=dt.timezone.utc)
    noon = dt.datetime.combine(today, dt.time(12, 0), tzinfo=dt.timezone.utc)

    # Find next refresh time
    for refresh in (midnight, noon):
        if refresh > now:
            return refresh.timestamp()

    # Both passed, next is tomorrow midnight
    tomorrow_midnight = midnight + dt.timedelta(days=1)
    return tomorrow_midnight.timestamp()


def is_expired(cache_data: dict) -> bool:
    """Check if cache has passed its next refresh time."""
    if not cache_data:
        return True

    next_refresh = cache_data.get("next_refresh")
    if next_refresh is None:
        return True

    return time.time() > next_refresh


def is_free_model(pricing: dict | None) -> bool:
    """Check if all pricing fields are null or "0"."""
    if pricing is None:
        return True
    return all(
        pricing.get(key) in (None, "0", 0) for key in ("prompt", "completion", "request", "image")
    )


def fetch_free_models(api_key: str) -> list[dict]:
    """Query OpenRouter catalog and filter free models."""
    import urllib.request

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/models", headers={"Authorization": f"Bearer {api_key}"}
    )

    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read())

    free_models = [m for m in data.get("data", []) if is_free_model(m.get("pricing"))]

    return free_models


def load_cache(output_path: Path) -> dict | None:
    """Load existing cache data."""
    if not output_path.exists():
        return None
    try:
        return json.loads(output_path.read_text())
    except (OSError, json.JSONDecodeError):
        return None


def write_cache(models: list[dict], output_path: Path) -> dict:
    """Write free models to cache file. Returns the cache data written."""
    cache_data = {
        "count": len(models),
        "fetched_at": time.time(),
        "next_refresh": next_refresh_time(),
        "models": [{"id": m["id"], "name": m.get("name", m["id"])} for m in models],
    }
    output_path.write_text(json.dumps(cache_data, indent=2) + "\n")
    return cache_data


def compare_models(old: list[dict], new: list[dict]) -> dict:
    """Compare old and new model lists. Returns dict with added/removed models."""
    old_ids = {m["id"] for m in old}
    new_ids = {m["id"] for m in new}

    added = new_ids - old_ids
    removed = old_ids - new_ids

    # Resolve names
    added_models = [(m["id"], m["name"]) for m in new if m["id"] in added]
    removed_models = [(m["id"], m["name"]) for m in old if m["id"] in removed]

    return {
        "added": sorted(added_models),
        "removed": sorted(removed_models),
        "count_changed": len(old) != len(new),
    }


def format_diff(diff: dict) -> str:
    """Format model diff for display."""
    if not diff["added"] and not diff["removed"]:
        return ""

    lines = []
    if diff["added"]:
        lines.append("Added models:")
        for model_id, name in diff["added"]:
            lines.append(f"  + {model_id}")
    if diff["removed"]:
        lines.append("Removed models:")
        for model_id, name in diff["removed"]:
            lines.append(f"  - {model_id}")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch and cache free models from OpenRouter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "output",
        nargs="?",
        default="free-models.json",
        help="Output file path (default: free-models.json)",
    )
    parser.add_argument(
        "--check-stale",
        action="store_true",
        help="Check if cache is expired. Exit 1 if expired, 0 if fresh.",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Force refresh even if cache is fresh.",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress progress messages (stderr).",
    )

    args = parser.parse_args()
    output_path = Path(args.output)
    api_key = os.environ.get("OPENROUTER_API_KEY")

    # Load existing cache
    cache = load_cache(output_path)
    expired = is_expired(cache or {})

    # Check staleness only (no fetch)
    if args.check_stale:
        if expired:
            if not args.quiet:
                if cache is not None:
                    next_r = cache.get("next_refresh", 0)
                    hours_until = (next_r - time.time()) / 3600
                    print(
                        f"Cache expired (next refresh was {abs(hours_until):.1f}h ago)",
                        file=sys.stderr,
                    )
                else:
                    print("Cache missing", file=sys.stderr)
            sys.exit(1)
        if not args.quiet:
            next_r = cache.get("next_refresh", 0) if cache else 0
            hours_until = (next_r - time.time()) / 3600
            print(f"Cache fresh (refresh in {hours_until:.1f}h)", file=sys.stderr)
        sys.exit(0)

    # Need API key for fetch
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)

    # Skip fetch if fresh and not forcing
    if not args.fresh and not expired:
        if not args.quiet:
            next_r = cache.get("next_refresh", 0) if cache else 0
            hours_until = (next_r - time.time()) / 3600
            print(
                f"Cache fresh (refresh in {hours_until:.1f}h). Use --fresh to force update.",
                file=sys.stderr,
            )
        sys.exit(0)

    # Fetch new models
    if not args.quiet:
        print("Fetching free models from OpenRouter...", file=sys.stderr)

    free_models = fetch_free_models(api_key)
    old_models = cache.get("models", []) if cache else []

    # Write cache
    new_cache = write_cache(free_models, output_path)

    # Check for changes
    diff = compare_models(old_models, free_models)
    if diff["added"] or diff["removed"] or diff["count_changed"]:
        print(
            f"\n⚠️  Free model list changed! ({len(old_models)} → {len(free_models)} models)",
            file=sys.stderr,
        )
        print(format_diff(diff), file=sys.stderr)
    elif not args.quiet:
        print(f"No changes ({len(free_models)} free models)", file=sys.stderr)

    if not args.quiet:
        next_refresh_dt = dt.datetime.fromtimestamp(new_cache["next_refresh"], tz=dt.timezone.utc)
        print(f"Next refresh: {next_refresh_dt.strftime('%Y-%m-%d %H:%M:%S UTC')}", file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
