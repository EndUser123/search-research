#!/usr/bin/env python3
"""Filter opencode models by context and pricing."""

import argparse
import json
import subprocess
from pathlib import Path

# Cache settings
CACHE_DIR = Path.home() / ".cache" / "ai-cli"
CACHE_FILE = CACHE_DIR / "opencode_models.txt"
CACHE_TTL_HOURS = 12

# Known broken/deprecated models that don't actually work
BROKEN_MODELS = {
    "openrouter/openrouter/sherlock-dash-alpha",
    "openrouter/openrouter/sherlock-think-alpha",
    "openrouter/openrouter/hunter-alpha",
}


def get_cached_models() -> str | None:
    """Get cached models data if available and fresh."""
    if not CACHE_FILE.exists():
        return None

    # Check cache age
    import time

    cache_age = time.time() - CACHE_FILE.stat().st_mtime
    max_age_seconds = CACHE_TTL_HOURS * 3600

    if cache_age > max_age_seconds:
        return None

    return CACHE_FILE.read_text()


def save_to_cache(data: str) -> None:
    """Save models data to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(data)


def fetch_models(force_refresh: bool = False) -> str:
    """Fetch models from opencode CLI."""
    # Check cache first (unless force refresh)
    if not force_refresh:
        cached = get_cached_models()
        if cached is not None:
            return cached

    # Fetch fresh data
    result = subprocess.run(
        "opencode models --verbose",
        capture_output=True,
        text=True,
        shell=True,
    )

    # Save to cache
    save_to_cache(result.stdout)
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description="Filter opencode models by context and pricing")
    parser.add_argument("--refresh", action="store_true", help="Force cache refresh")
    parser.add_argument(
        "--context", type=int, default=190000, help="Minimum context window (default: 190000)"
    )
    args = parser.parse_args()

    # Get verbose model data (cached or fresh)
    models_output = fetch_models(force_refresh=args.refresh)
    lines = models_output.strip().split("\n")

    min_context = args.context
    results = []
    current_model_id = None
    json_lines = []

    brace_count = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # If we're inside a JSON block, accumulate all lines
        if json_lines:
            json_lines.append(line)
            # Count braces to find the end of the JSON
            brace_count += line.count("{") - line.count("}")

            # When brace count returns to 0, we've closed the outermost object
            if brace_count == 0:
                # Parse the accumulated JSON
                try:
                    json_text = "\n".join(json_lines)
                    model_data = json.loads(json_text)

                    # Skip known broken/deprecated models
                    if current_model_id in BROKEN_MODELS:
                        json_lines = []
                        brace_count = 0
                        current_model_id = None
                        continue

                    # Filter: Exclude OpenRouter paid models
                    # (Only show free OpenRouter models, like the ai-openrouter skill)
                    provider_id = model_data.get("providerID", "")
                    cost_in = model_data.get("cost", {}).get("input", -1)
                    cost_out = model_data.get("cost", {}).get("output", -1)

                    if provider_id == "openrouter" and (cost_in != 0 or cost_out != 0):
                        # OpenRouter model with non-zero cost - skip it
                        json_lines = []
                        brace_count = 0
                        current_model_id = None
                        continue

                    context = model_data.get("limit", {}).get("context", 0)
                    cost_in = model_data.get("cost", {}).get("input", -1)
                    cost_out = model_data.get("cost", {}).get("output", -1)

                    if context > min_context:
                        name = model_data.get("name", "Unknown")
                        is_free = cost_in == 0 and cost_out == 0
                        results.append(
                            {
                                "id": current_model_id,
                                "name": name,
                                "context": context,
                                "free": is_free,
                                "cost_in": cost_in,
                                "cost_out": cost_out,
                            }
                        )
                except Exception:
                    pass

                # Reset for next model
                json_lines = []
                brace_count = 0
                current_model_id = None
        elif line.startswith("{"):
            # Start of a new JSON block
            json_lines.append(line)
            brace_count = line.count("{") - line.count("}")
        else:
            # This is a model ID (before the JSON block)
            current_model_id = line

    # Sort: free first, then by context descending
    results.sort(key=lambda x: (not x["free"], -x["context"]))

    print(f"Models with >{min_context:,} context (FREE first, then by context):")
    print()

    if not results:
        print(f"No models found with >{min_context:,} context.")
        print()
        # Check what the maximum context is
        max_ctx = 0
        for model_block in results:
            if model_block["context"] > max_ctx:
                max_ctx = model_block["context"]
        print(f"Maximum context found: {max_ctx:,} tokens")
    else:
        for r in results:
            if r["free"]:
                free_tag = "FREE    "
            else:
                free_tag = f"${r['cost_in']:.2f}/${r['cost_out']:.2f}M"
            print(f"{free_tag:12} {r['context']:>10,} ctx  {r['id']}")


if __name__ == "__main__":
    main()
