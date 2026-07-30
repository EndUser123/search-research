#!/usr/bin/env python3
"""Advisory vulture pre-check for /check Step 0.9.

Policy (VULT-01, 2026-07-28):
  - ADVISORY only for /check — never blocks CHECK PASS/FAIL by itself.
  - Soft-fail if vulture is not installed (status=skipped).
  - Filters common framework false positives (Textual, reactive watchers,
    pytest fixtures, CLI entry points).

Usage:
  python vulture_precheck.py --paths path1.py path2.py [--min-confidence 80]
  python vulture_precheck.py --paths path1.py --output out.json

Exit codes:
  0 — always (advisory; missing tool is skipped, not failure)
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

# Names / message patterns that are almost always framework or dynamic-dispatch FPs.
# Applied after vulture runs so real unused helpers still surface.
_FP_NAME_EXACT = frozenset(
    {
        "compose",
        "on_mount",
        "on_unmount",
        "CSS",
        "CSS_PATH",
        "BINDINGS",
        "TITLE",
        "SUB_TITLE",
        "DEFAULT_CSS",
        "COMPONENT_CLASSES",
        "cursor_type",
        "zebra_stripes",
        "display",
        "disabled",
    }
)

# message or name contains these → drop as framework FP
_FP_SUBSTRINGS = (
    "watch_",
    "action_",
    "unused method 'compose'",
    "unused method 'on_",
    "unused method '_on_",
    "unused method 'action_",
    "unused variable 'CSS'",
    "unused variable 'BINDINGS'",
    "unused variable 'TITLE'",
    "unused variable 'SUB_TITLE'",
    "unused variable 'CSS_PATH'",
)

# vulture line format: path:line: message (NN% confidence)
# Windows paths contain drive colons (D:\...) — take the LAST :digits: before message.
_LINE_RE = re.compile(
    r"^(?P<path>.+):(?P<line>\d+):\s*(?P<message>.+?)\s*\((?P<confidence>\d+)%\s*confidence\)\s*$"
)


def _extract_name(message: str) -> str | None:
    # "unused method 'foo'" / "unused variable 'BAR'" / "unused function 'x'"
    m = re.search(r"'([^']+)'", message)
    return m.group(1) if m else None


def _is_framework_fp(message: str, name: str | None) -> bool:
    if name and name in _FP_NAME_EXACT:
        return True
    if name and (name.startswith("watch_") or name.startswith("action_")):
        return True
    if name and name.startswith("_on_"):
        # Textual @on(Button.Pressed) handlers often named _on_*
        return True
    lower = message.lower()
    for s in _FP_SUBSTRINGS:
        if s.lower() in lower:
            return True
    return False


def _decorated_handler_names(path: str) -> set[str]:
    """Names of methods preceded by @on / @work (Textual dynamic dispatch)."""
    names: set[str] = set()
    try:
        lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return names
    deco_window = 0
    for line in lines:
        stripped = line.strip()
        if (stripped.startswith("@on(")
                or stripped.startswith("@work(")
                or stripped.startswith("@work ")):
            deco_window = 6
            continue
        if deco_window > 0:
            deco_window -= 1
            m = re.match(r"def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", stripped)
            if m:
                names.add(m.group(1))
                deco_window = 0
    return names


def run_vulture(
    paths: list[str],
    min_confidence: int,
) -> dict[str, Any]:
    vulture_bin = shutil.which("vulture")
    if not vulture_bin:
        return {
            "status": "skipped",
            "reason": "vulture_not_installed",
            "advisory": True,
            "blocks_check": False,
            "findings": [],
            "filtered_framework_fp": [],
            "paths": paths,
            "min_confidence": min_confidence,
        }

    existing = [p for p in paths if Path(p).is_file()]
    missing = [p for p in paths if not Path(p).is_file()]
    if not existing:
        return {
            "status": "skipped",
            "reason": "no_existing_py_files",
            "advisory": True,
            "blocks_check": False,
            "findings": [],
            "filtered_framework_fp": [],
            "paths": paths,
            "missing": missing,
            "min_confidence": min_confidence,
        }

    cmd = [vulture_bin, *existing, f"--min-confidence={min_confidence}"]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        return {
            "status": "error",
            "reason": str(e),
            "advisory": True,
            "blocks_check": False,
            "findings": [],
            "filtered_framework_fp": [],
            "paths": existing,
            "min_confidence": min_confidence,
        }

    # Cache decorator-based handler names per file (Textual @on / @work)
    deco_cache: dict[str, set[str]] = {}

    findings: list[dict[str, Any]] = []
    filtered: list[dict[str, Any]] = []
    for raw in (proc.stdout or "").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        m = _LINE_RE.match(raw)
        if not m:
            # keep unparseable lines as advisory noise at low priority
            findings.append(
                {
                    "raw": raw,
                    "path": None,
                    "line": None,
                    "message": raw,
                    "confidence": None,
                    "name": None,
                    "framework_fp": False,
                }
            )
            continue
        name = _extract_name(m.group("message"))
        fpath = m.group("path")
        if fpath not in deco_cache:
            deco_cache[fpath] = _decorated_handler_names(fpath)
        is_fp = _is_framework_fp(m.group("message"), name)
        if not is_fp and name and name in deco_cache[fpath]:
            is_fp = True
        item = {
            "raw": raw,
            "path": fpath,
            "line": int(m.group("line")),
            "message": m.group("message"),
            "confidence": int(m.group("confidence")),
            "name": name,
            "framework_fp": is_fp,
        }
        if item["framework_fp"]:
            filtered.append(item)
        else:
            findings.append(item)

    return {
        "status": "ok",
        "advisory": True,
        "blocks_check": False,
        "policy": "advisory_only_for_check",
        "command": cmd,
        "vulture_returncode": proc.returncode,
        "paths": existing,
        "missing": missing,
        "min_confidence": min_confidence,
        "findings": findings,
        "finding_count": len(findings),
        "filtered_framework_fp": filtered,
        "filtered_count": len(filtered),
        "stderr": (proc.stderr or "").strip()[:2000],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Advisory vulture pre-check for /check"
    )
    parser.add_argument(
        "--paths",
        nargs="+",
        required=True,
        help="Python file paths to scan",
    )
    parser.add_argument(
        "--min-confidence",
        type=int,
        default=80,
        help="vulture min confidence (default 80)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default=None,
        help="Write JSON result to this path (also prints summary to stdout)",
    )
    args = parser.parse_args(argv)

    result = run_vulture(args.paths, args.min_confidence)
    text = json.dumps(result, indent=2)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(text + "\n", encoding="utf-8")

    # Human summary for orchestrator logs
    status = result.get("status")
    n = result.get("finding_count", len(result.get("findings") or []))
    fp = result.get("filtered_count", 0)
    if status == "skipped":
        print(f"VULTURE_PRECHECK: skipped ({result.get('reason')}) advisory=True")
    elif status == "error":
        print(f"VULTURE_PRECHECK: error ({result.get('reason')}) advisory=True")
    else:
        print(
            f"VULTURE_PRECHECK: ok findings={n} framework_fp_filtered={fp} "
            f"advisory=True blocks_check=False min_confidence={args.min_confidence}"
        )
        for f in (result.get("findings") or [])[:20]:
            print(f"  ADVISORY: {f.get('raw') or f.get('message')}")
        if n > 20:
            print(f"  ... +{n - 20} more")

    return 0


if __name__ == "__main__":
    sys.exit(main())
