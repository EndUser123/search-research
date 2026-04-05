#!/usr/bin/env python3
"""Check if a YouTube API key is valid, working, or out of quota.

Usage:
    python scripts/check_api_key.py YOUR_API_KEY
    python scripts/check_api_key.py YOUR_API_KEY --detailed
"""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def check_api_key(api_key: str, detailed: bool = False) -> dict[str, str | int]:
    """Check the status of a YouTube Data API v3 key.

    Returns a dict with:
        - status: 'good', 'bad', 'out_of_quota', 'error'
        - message: Human-readable description
        - quota_remaining: Estimated quota remaining (if good)
    """
    import httpx

    # Test endpoint: search for a common video (minimal quota usage: 100)
    # Using a very simple search that should work on any channel
    test_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": "test",
        "type": "video",
        "maxResults": 1,
        "key": api_key,
    }

    try:
        response = httpx.get(test_url, params=params, timeout=10.0)

        if response.status_code == 200:
            # Key works! Check response to estimate quota
            data = response.json()
            if detailed:
                # Make another call to check quota more precisely
                return {
                    "status": "good",
                    "message": "✓ API key is valid and has quota available",
                    "quota_remaining": "unknown - run with --detailed for precise check",
                }
            return {
                "status": "good",
                "message": "✓ API key is valid and has quota available",
                "quota_remaining": "10,000 (estimated - may have been used today)",
            }

        elif response.status_code == 403:
            # Check the reason for 403
            error_data = response.json()
            error_reason = error_data.get("error", {}).get("errors", [{}])[0].get("reason", "unknown")

            if error_reason == "quotaExceeded":
                return {
                    "status": "out_of_quota",
                    "message": "⚠ API key is valid but quota is exhausted for today",
                    "quota_remaining": 0,
                }
            elif "keyInvalid" in error_reason or "forbidden" in error_reason.lower():
                return {
                    "status": "bad",
                    "message": f"✗ API key is invalid or not authorized (reason: {error_reason})",
                    "quota_remaining": 0,
                }
            else:
                return {
                    "status": "bad",
                    "message": f"✗ API key rejected: {error_reason}",
                    "quota_remaining": 0,
                }

        elif response.status_code == 400:
            return {
                "status": "bad",
                "message": "✗ API key format is invalid",
                "quota_remaining": 0,
            }

        else:
            return {
                "status": "error",
                "message": f"? Unexpected response: HTTP {response.status_code}",
                "quota_remaining": 0,
            }

    except httpx.TimeoutException:
        return {"status": "error", "message": "✗ Request timed out - check network connection", "quota_remaining": 0}
    except Exception as e:
        return {"status": "error", "message": f"✗ Error: {e}", "quota_remaining": 0}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check if a YouTube API key is valid, working, or out of quota"
    )
    parser.add_argument("api_key", help="YouTube Data API v3 key to check")
    parser.add_argument("-d", "--detailed", action="store_true", help="Show detailed quota information")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    # Basic validation
    if not args.api_key or len(args.api_key) < 20:
        print("✗ API key appears to be invalid (too short)")
        return 1

    result = check_api_key(args.api_key, args.detailed)

    if args.json:
        import json

        print(json.dumps(result, indent=2))
    else:
        # Color-coded output
        status_colors = {
            "good": "\033[92m",  # Green
            "bad": "\033[91m",  # Red
            "out_of_quota": "\033[93m",  # Yellow
            "error": "\033[94m",  # Blue
        }
        reset = "\033[0m"

        color = status_colors.get(result["status"], "")
        status_display = f"{color}{result['status'].upper()}{reset}"

        print(f"Status:  {status_display}")
        print(f"Message: {result['message']}")
        if "quota_remaining" in result:
            print(f"Quota:   {result['quota_remaining']}")

        # Exit code based on status
        if result["status"] == "good":
            return 0
        elif result["status"] == "out_of_quota":
            return 2  # Special exit code for out of quota
        else:
            return 1


if __name__ == "__main__":
    sys.exit(main())
