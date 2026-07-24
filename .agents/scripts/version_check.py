#!/usr/bin/env python3
"""Check installed Python packages against PyPI latest versions.

Shared utility for /web, /www, /crawl4ai, /wiki skills. Run before long
research sessions, before ingest pipelines, or as a periodic health check.

Usage:
    python P:/.agents/scripts/version_check.py --skill web
    python P:/.agents/scripts/version_check.py --skill www
    python P:/.agents/scripts/version_check.py --skill crawl4ai
    python P:/.agents/scripts/version_check.py --skill wiki
    python P:/.agents/scripts/version_check.py --all
    python P:/.agents/scripts/version_check.py ddgs exa_py tavily
    python P:/.agents/scripts/version_check.py --skill web --json

Exit codes:
    0: all packages up to date (or only PyPI fetch errors)
    1: at least one package behind or not installed
"""
from __future__ import annotations

import argparse
import concurrent.futures
import importlib.metadata
import json
import sys
import urllib.request
from typing import NamedTuple

PYPI_TIMEOUT_S = 10
PARALLEL_WORKERS = 6


class DepSpec(NamedTuple):
    """A dependency to check.

    import_name:    what you `import` (e.g. 'exa_py') — used to find the distribution
    pypi_name:      what goes in the PyPI JSON API URL (e.g. 'exa-py')
    display_name:   what shows in the output table (e.g. 'exa_py')
    min_supported:  optional minimum version tuple; below this = exit 2
    """
    import_name: str
    pypi_name: str
    display_name: str
    min_supported: tuple | None = None


# Skill → dependency specs.
# Each entry: (import_name, pypi_name, display_name, min_supported_or_None)
SKILL_DEPS: dict[str, list[DepSpec]] = {
    "web": [
        DepSpec("ddgs", "ddgs", "ddgs"),
        DepSpec("exa_py", "exa-py", "exa_py"),
        DepSpec("tavily", "tavily-python", "tavily"),
        DepSpec("requests", "requests", "requests"),
    ],
    "www": [
        DepSpec("ddgs", "ddgs", "ddgs"),
        DepSpec("exa_py", "exa-py", "exa_py"),
        DepSpec("tavily", "tavily-python", "tavily"),
        DepSpec("requests", "requests", "requests"),
        DepSpec("crawl4ai", "crawl4ai", "crawl4ai", min_supported=(0, 7, 0)),
        DepSpec("qmd", "qmd", "qmd"),
    ],
    "crawl4ai": [
        DepSpec("crawl4ai", "crawl4ai", "crawl4ai", min_supported=(0, 7, 0)),
        DepSpec("qmd", "qmd", "qmd"),
    ],
    "wiki": [
        DepSpec("qmd", "qmd", "qmd"),
    ],
}


def _find_distribution_name(import_name: str) -> str:
    """Map an import name (e.g. 'exa_py') to its pip distribution name (e.g. 'exa-py').

    Uses importlib.metadata.packages_distributions() which maps top-level
    package names to their installing distribution(s). Falls back to the
    import name itself if the mapping is unavailable.
    """
    try:
        # Python 3.10+
        from importlib.metadata import packages_distributions
        mapping = packages_distributions()
        if import_name in mapping and mapping[import_name]:
            return mapping[import_name][0]
    except Exception:
        pass
    return import_name


def get_installed_version(import_name: str) -> str | None:
    """Read installed version. Tries distribution name lookup + hyphen/underscore variants.

    Returns None if not installed.
    """
    dist_name = _find_distribution_name(import_name)
    # Try the mapped name, then hyphen↔underscore swap, then the raw import name
    candidates = [dist_name]
    if "-" in dist_name:
        candidates.append(dist_name.replace("-", "_"))
    elif "_" in dist_name:
        candidates.append(dist_name.replace("_", "-"))
    candidates.append(import_name)

    for candidate in dict.fromkeys(candidates):  # dedupe preserving order
        try:
            return importlib.metadata.version(candidate)
        except importlib.metadata.PackageNotFoundError:
            continue
        except Exception:
            continue
    return None


def get_pypi_latest(pypi_name: str) -> tuple[str | None, str | None]:
    """Fetch latest version from PyPI JSON API.

    Returns (version_string, error_message). On success, error is None.
    On failure, version is None and error describes why.
    """
    url = f"https://pypi.org/pypi/{pypi_name}/json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "version-check/1.0"})
        with urllib.request.urlopen(req, timeout=PYPI_TIMEOUT_S) as resp:
            if getattr(resp, "status", 200) != 200:
                return None, f"HTTP {resp.status}"
            data = json.loads(resp.read().decode("utf-8", errors="replace"))
        version = data.get("info", {}).get("version")
        if version:
            return version, None
        return None, "no version in PyPI response"
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def _parse_version(v: str):
    """Parse a PEP 440 version → packaging.version.Version. None on failure."""
    try:
        from packaging.version import Version, InvalidVersion
        return Version(v.strip())
    except (ImportError, InvalidVersion, AttributeError):
        return None


def check_one(spec: DepSpec) -> dict:
    """Check a single dependency. Returns a result dict."""
    result: dict = {
        "name": spec.display_name,
        "import_name": spec.import_name,
        "installed": None,
        "latest": None,
        "behind": None,
        "below_min": False,
        "status": "unknown",
        "fetch_error": None,
    }

    installed = get_installed_version(spec.import_name)
    result["installed"] = installed

    if installed is None:
        result["status"] = "missing"
        # Still try to fetch latest so the user knows what they'd get
        latest, err = get_pypi_latest(spec.pypi_name)
        result["latest"] = latest
        result["fetch_error"] = err
        return result

    latest, err = get_pypi_latest(spec.pypi_name)
    result["latest"] = latest
    result["fetch_error"] = err

    if latest is None:
        result["status"] = "fetch_error"
        return result

    inst_v = _parse_version(installed)
    latest_v = _parse_version(latest)
    if inst_v and latest_v:
        result["behind"] = inst_v < latest_v
    elif installed != latest:
        # Fallback: string inequality (less precise but catches major diffs)
        result["behind"] = True
    else:
        result["behind"] = False

    if result["behind"]:
        result["status"] = "behind"
    else:
        result["status"] = "current"

    # Min-supported check
    if spec.min_supported and inst_v:
        try:
            inst_tuple = inst_v.release[:3]
            if inst_tuple < spec.min_supported:
                result["below_min"] = True
        except Exception:
            pass

    return result


def format_table(results: list[dict]) -> str:
    """Format results as a human-readable table."""
    name_w = max(len(r["name"]) for r in results) + 2
    inst_w = max(len(str(r["installed"] or "")) for r in results) + 2
    latest_w = max(len(str(r["latest"] or "")) for r in results) + 2

    header = f"{'Package':<{name_w}} {'Installed':<{inst_w}} {'Latest':<{latest_w}} Status"
    lines = [header, "-" * len(header)]

    for r in results:
        status_label = {
            "current": "[OK]",
            "behind": "[BEHIND]",
            "missing": "[MISSING]",
            "fetch_error": "[?]",
            "unknown": "[?]",
        }.get(r["status"], "[?]")
        inst = str(r["installed"] or "—")
        latest = str(r["latest"] or "—")
        if r.get("fetch_error") and r["latest"] is None:
            latest = f"(fetch err)"
        line = f"{r['name']:<{name_w}} {inst:<{inst_w}} {latest:<{latest_w}} {status_label}"
        if r.get("below_min"):
            line += "  [BELOW MIN]"
        lines.append(line)

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check installed Python packages against PyPI latest.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("packages", nargs="*", help="Package import names to check (e.g. ddgs exa_py)")
    parser.add_argument("--skill", choices=list(SKILL_DEPS.keys()),
                        help="Check a skill's known dependency set")
    parser.add_argument("--all", action="store_true",
                        help="Check all skills' combined dependency set (deduped)")
    parser.add_argument("--json", action="store_true",
                        help="Machine-readable JSON output (for CI/scripts)")
    args = parser.parse_args()

    # Resolve which deps to check
    if args.all:
        deps: list[DepSpec] = []
        seen: set[str] = set()
        for skill_deps in SKILL_DEPS.values():
            for dep in skill_deps:
                if dep.import_name not in seen:
                    deps.append(dep)
                    seen.add(dep.import_name)
    elif args.skill:
        deps = list(SKILL_DEPS[args.skill])
    elif args.packages:
        deps = [DepSpec(p, p, p) for p in args.packages]
    else:
        parser.print_help(sys.stderr)
        sys.exit(2)

    # Check all in parallel (network-bound)
    results: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as pool:
        futures = {pool.submit(check_one, dep): dep for dep in deps}
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    # Sort to match input order
    order = {dep.display_name: i for i, dep in enumerate(deps)}
    results.sort(key=lambda r: order.get(r["name"], 99))

    # Output
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(format_table(results))
        print()

        any_behind = any(r["status"] == "behind" for r in results)
        any_missing = any(r["status"] == "missing" for r in results)
        any_below_min = any(r.get("below_min") for r in results)

        if any_missing:
            missing_names = [r["name"] for r in results if r["status"] == "missing"]
            print(f"Install missing:  pip install {' '.join(missing_names)}")
        if any_behind:
            behind_names = [r["name"] for r in results if r["status"] == "behind"]
            print(f"Upgrade outdated: pip install -U {' '.join(behind_names)}")
        if any_below_min:
            below_names = [r["name"] for r in results if r.get("below_min")]
            print(f"BELOW MINIMUM:    {' '.join(below_names)} — upgrade required, not optional")
        if not any_behind and not any_missing:
            print("All checked packages are up to date.")

    # Exit code
    if any(r.get("below_min") for r in results):
        sys.exit(2)  # below minimum = critical
    if any(r["status"] in ("behind", "missing") for r in results):
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    sys.exit(main())
