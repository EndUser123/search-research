"""
Context7 Client - Programmatic API Access
Fetches up-to-date documentation from Context7 API.
"""
import os
import sys
import json
import argparse
import urllib.request
import urllib.error
import urllib.parse
import hashlib
import time
from pathlib import Path
from typing import Optional, Dict, List, Any

API_BASE = "https://context7.com/api/v2"
CACHE_DIR = Path(".claude/cache/context7")


def get_api_key() -> str:
    """Retrieves API key from environment variable."""
    key = os.environ.get("CONTEXT7_API_KEY")
    if not key:
        print("⚠️  CONTEXT7_API_KEY not found in environment.")
        print("   Please get a key from https://context7.com/dashboard")
        print("   and set it via: export CONTEXT7_API_KEY='ctx7sk_...'")
        sys.exit(1)
    return key


def get_cache_path(key_seed: str) -> Path:
    """Returns path to cache file for a given key seed."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    file_hash = hashlib.md5(key_seed.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{file_hash}.json"


def read_cache(cache_path: Path, max_age_hours: int = 24) -> Optional[Any]:
    """Reads from cache if valid."""
    if not cache_path.exists():
        return None

    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
        timestamp = data.get("_timestamp", 0)
        age_hours = (time.time() - timestamp) / 3600

        if age_hours > max_age_hours:
            return None  # Expired

        return data.get("payload")
    except Exception:
        return None


def write_cache(cache_path: Path, payload: Any) -> None:
    """Writes payload to cache with timestamp."""
    try:
        data = {
            "_timestamp": time.time(),
            "payload": payload
        }
        cache_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except Exception as e:
        print(f"⚠️ Failed to write cache: {e}")


def make_request(
    endpoint: str,
    params: Dict[str, str],
    api_key: str
) -> Dict[str, Any]:
    """Makes a GET request to the Context7 API."""
    query_string = urllib.parse.urlencode(params)
    url = f"{API_BASE}{endpoint}?{query_string}"

    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("X-Context7-Source", "claude-code-skill")

    try:
        with urllib.request.urlopen(req) as response:
            if response.status != 200:
                print(f"Error: API returned status {response.status}")
                sys.exit(1)
            return json.loads(response.read().decode("utf-8"))  # type: ignore
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        if e.code == 401:
            print("Invalid API Key.")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Network Error: {e.reason}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected Error: {e}")
        sys.exit(1)


def search_library(
    query: str,
    library_name: Optional[str],
    api_key: str,
    force: bool = False
) -> List[Dict[str, Any]]:
    """Searches for a library ID."""
    cache_path = get_cache_path(f"search:{query}:{library_name}")

    if not force:
        cached = read_cache(cache_path)
        if cached:
            print("📦 Using cached search results.")
            return cached  # type: ignore

    params = {"query": query}
    if library_name:
        params["libraryName"] = library_name

    print(f"🔍 Searching Context7 for: '{library_name or query}'...")
    data = make_request("/libs/search", params, api_key)
    results = data.get("results", [])

    write_cache(cache_path, results)
    return results


def fetch_context(
    query: str,
    library_id: str,
    api_key: str,
    force: bool = False
) -> str:
    """Fetches documentation context for a library."""
    cache_path = get_cache_path(f"fetch:{library_id}:{query}")

    if not force:
        cached = read_cache(cache_path)
        if cached:
            print("📦 Using cached documentation context.")
            return str(cached)

    print(f"📚 Fetching context for ID: {library_id}...")
    params = {
        "query": query,
        "libraryId": library_id
    }

    query_string = urllib.parse.urlencode(params)
    url = f"{API_BASE}/context?{query_string}"

    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("X-Context7-Source", "claude-code-skill")

    try:
        with urllib.request.urlopen(req) as response:
            content = response.read().decode("utf-8")
            write_cache(cache_path, content)
            return content
    except Exception as e:
        print(f"Error fetching context: {e}")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Context7 API Client")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore cache and force fetch"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Search Command
    search_parser = subparsers.add_parser(
        "search",
        help="Search for a library"
    )
    search_parser.add_argument("query", help="Search query or library name")

    # Fetch Command
    fetch_parser = subparsers.add_parser(
        "fetch",
        help="Fetch context for a query"
    )
    fetch_parser.add_argument(
        "library_id",
        help="Library ID (e.g. @upstash/redis)"
    )
    fetch_parser.add_argument("query", help="Natural language question")

    args = parser.parse_args()
    api_key = get_api_key()

    if args.command == "search":
        results = search_library(args.query, args.query, api_key, args.force)
        if not results:
            print("No libraries found.")
        else:
            print(f"Found {len(results)} libraries:")
            for lib in results[:5]:  # Show top 5
                print(f"- {lib['id']}")
                desc = lib.get('description', 'No description')[:100]
                print(f"  {desc}...")
                print()

            # Print the ID of the first result for easy piping
            print(f"Top Result ID: {results[0]['id']}")

    elif args.command == "fetch":
        context = fetch_context(
            args.query,
            args.library_id,
            api_key,
            args.force
        )
        print("\n=== Context7 Documentation ===\n")
        print(context)
        print("\n==============================\n")


if __name__ == "__main__":
    main()
