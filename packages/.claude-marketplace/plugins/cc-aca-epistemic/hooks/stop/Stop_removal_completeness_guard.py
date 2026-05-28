#!/usr/bin/env python3
"""
Stop_removal_completeness_guard.py - Removal Completeness Verification Guard
=============================================================================

Blocks responses claiming removal/cleanup is complete WITHOUT verifying
no remaining imports or references to the removed module exist.

WHY THIS EXISTS:
  AI agents declare "cleanup complete" or "fully removed" while import
  statements, registration entries, or references to the removed module
  still exist in the codebase. Stop_deletion_verification_guard checks
  filesystem state; this guard checks reference completeness.

FAILURE MODE CAUGHT:
  "Cleanup complete - all Judge files removed"
  -> `import external_judge` still present in 3 files
  -> Guard blocks and lists the remaining references.

VERIFICATION METHOD:
  Extracts module names from the response (file paths, explicit module
  mentions), then walks .py files under CLAUDE_PROJECT_DIR searching for
  `import <module>` or `from <module>` statements.

LIFECYCLE: Stop (blocking guard -- exits with code 2 to block)
"""
from __future__ import annotations



# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P

def _normalize_stdout(data: dict) -> dict:
    if data.get('decision') == 'allow':
        return {'decision': 'approve'}
    if data.get('decision') == 'block':
        return {'decision': 'block', 'reason': data.get('reason', '')}
    if 'allow' in data:
        if data['allow'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'continue' in data:
        if data['continue'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'ok' in data:
        return {'decision': 'approve'}
    return data

_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


import json
import logging
import os
import re
import sys
from pathlib import Path

# Import path extraction from sibling guard (same directory, same plugin)
_stop_dir = _P(__file__).resolve().parent
if str(_stop_dir) not in _s.path: _s.path.insert(0, str(_stop_dir))
from Stop_deletion_verification_guard import _extract_file_paths

# --- Configuration Constants -------------------------------------------------

MAX_MODULE_NAMES = 10
MAX_FILES_TO_SCAN = 500
MAX_RESULTS = 10

HOOKS_DIR = _hooks_dir
LOG_DIR = HOOKS_DIR / "state" / "logs"

# --- Logging ----------------------------------------------------------------

LOG_DIR.mkdir(parents=True, exist_ok=True)
_logger = logging.getLogger("removal_completeness_guard")
_handler = logging.FileHandler(LOG_DIR / "removal_completeness_guard.log", encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(logging.DEBUG)


# --- Patterns: Removal Completion Claims ------------------------------------

REMOVAL_COMPLETION_PATTERNS = re.compile(
    r"\bcleanup\s+(?:is\s+)?complete\b"
    r"|\b(?:fully|completely)\s+(?:removed|deleted|cleaned)\b"
    r"|\bremoval\s+(?:is\s+)?complete\b"
    r"|\b(?:all|zero)\s+(?:remaining\s+)?(?:references?|imports?|usages?)\s+(?:removed|deleted|gone)\b"
    r"|\bno\s+(?:remaining|more)\s+(?:references?|imports?|usages?)\b"
    r"|\b(?:zero|no)\s+remaining\s+(?:references?|imports?|usages?)\b",
    re.IGNORECASE,
)

# Allowlist: code-edit and hypothetical contexts that aren't filesystem removals
COMPLETION_ALLOWLIST = re.compile(
    r"\b(?:fully|completely)\s+removed\s+(?:the\s+)?(?:marker|condition|check|guard|rule|flag|qualifier|constraint)\b"
    r"|\b(?:fully|completely)\s+removed\s+.*(?:from\s+(?:the\s+)?(?:regex|pattern|constraint|schema|section))\b"
    r"|\b(?:fully|completely)\s+removed\s+(?:the\s+)?(?:duplicate|entry|alias|line|item|value|setting)\b"
    r"|\bif\b[^.]*\bcleanup\s+complete\b"
    r"|\b(?:should|would|could|will|plan)\s+.*\bcleanup\s+complete\b",
    re.IGNORECASE,
)

# Module name extraction: word before "module/system/plugin"
MODULE_EXPLICIT_PATTERNS = re.compile(
    r"(\w[\w-]*)\s+(?:module|system|plugin|package|library)\b",
    re.IGNORECASE,
)


# --- Module name extraction -------------------------------------------------


def _extract_module_names(response: str) -> list[str]:
    """Extract module names from response via file paths and explicit mentions."""
    names: list[str] = []
    seen: set[str] = set()

    # Source 1: File path stems
    file_paths = _extract_file_paths(response)
    for fp in file_paths:
        stem = Path(fp).stem
        if stem and len(stem) >= 3 and stem not in seen:
            seen.add(stem)
            names.append(stem)

    # Source 2: Explicit module/system/plugin mentions
    for match in MODULE_EXPLICIT_PATTERNS.finditer(response):
        name = match.group(1).replace("-", "_")
        if name not in seen and len(name) >= 3:
            seen.add(name)
            names.append(name)

    return names[:MAX_MODULE_NAMES]


# --- Reference search -------------------------------------------------------


def _search_remaining_references(
    module_names: list[str], project_dir: Path
) -> list[str]:
    """Walk .py files under project_dir, search for import/from statements."""
    results: list[str] = []

    if not project_dir.is_dir():
        return results

    escaped_names = [re.escape(name) for name in module_names]
    combined = "|".join(escaped_names)
    import_re = re.compile(
        rf"^\s*(?:import\s+(?:{combined})|from\s+(?:{combined})\s+import)",
        re.IGNORECASE | re.MULTILINE,
    )

    files_scanned = 0
    skip_dirs = {".git", "__pycache__", "node_modules", ".mypy_cache", ".pytest_cache"}

    try:
        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith(".")]

            for fname in files:
                if not fname.endswith(".py"):
                    continue

                if files_scanned >= MAX_FILES_TO_SCAN:
                    _logger.warning("hit MAX_FILES_TO_SCAN (%d)", MAX_FILES_TO_SCAN)
                    return results

                files_scanned += 1
                fpath = Path(root) / fname

                try:
                    content = fpath.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue

                for match in import_re.finditer(content):
                    line_num = content[:match.start()].count("\n") + 1
                    line_text = match.group(0).strip()
                    try:
                        rel_path = str(fpath.relative_to(project_dir))
                    except ValueError:
                        rel_path = str(fpath)
                    results.append(f"{rel_path}:{line_num}: {line_text}")

                    if len(results) >= MAX_RESULTS:
                        return results
    except OSError:
        pass

    return results


# --- Decision logic ---------------------------------------------------------


def check(data: dict) -> dict | None:
    """Core guard logic. Returns block dict or None (allow)."""
    response = data.get("assistant_response", "") or data.get("response", "")
    if not response:
        return None

    if COMPLETION_ALLOWLIST.search(response):
        _logger.debug("matched completion allowlist - skipping")
        return None

    if not REMOVAL_COMPLETION_PATTERNS.search(response):
        return None

    _logger.info("removal completion claim detected")

    module_names = _extract_module_names(response)
    if not module_names:
        _logger.debug("no module names extracted - fail open")
        return None

    _logger.info("extracted module names: %s", module_names)

    project_dir_env = os.environ.get("CLAUDE_PROJECT_DIR", "").strip()
    project_dir = Path(project_dir_env) if project_dir_env else Path(".")

    remaining = _search_remaining_references(module_names, project_dir)

    if remaining:
        _logger.warning(
            "BLOCK: %d remaining reference(s) for: %s",
            len(remaining), module_names,
        )
        lines = ["**Incomplete Removal Detected**\n"]
        lines.append("Claim: removal/cleanup complete\n")
        lines.append(f"Module names checked: {', '.join(module_names)}\n")
        lines.append("Remaining references found:\n")
        for ref in remaining:
            lines.append(f"  - {ref}")
        lines.append("\n")
        lines.append(
            "Before declaring removal complete, verify ALL imports and "
            "references to the removed module have been deleted."
        )
        return {
            "decision": "block",
            "reason": "\n".join(lines),
            "blocking_hook": "Stop_removal_completeness_guard",
        }

    _logger.info("removal completeness verified - no remaining references")
    return None


def run(data: dict) -> dict | None:
    """In-process validator protocol for Stop_router."""
    result = check(data)
    if result and result.get("decision") == "block":
        return {
            "block": True,
            "reason": result.get("reason", ""),
            "blocking_hook": result.get("blocking_hook", "Stop_removal_completeness_guard"),
        }
    return result


# --- Main ------------------------------------------------------------------


def main() -> None:
    try:
        raw = sys.stdin.read().strip()
        if not raw:
            sys.exit(0)
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    result = check(data)
    if result:
        print(json.dumps(_normalize_stdout(result)))
        if result.get("decision") == "block":
            sys.exit(2)


if __name__ == "__main__":
    main()
