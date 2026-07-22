#!/usr/bin/env python3
"""classify_change — map a unified diff to the check-run phases it triggers.

Module-level public entry: ``classify_diff(diff_text, diff_ref="HEAD")``.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Set, Tuple

HIGH_RISK_PATH_PREFIXES: Tuple[str, ...] = (
    "scripts/check/",
)
HIGH_RISK_SYMBOLS: Set[str] = {
    "abandon_run", "adopt_run", "check_continuation", "validate_run",
    "classify_diff", "detect_context", "start_check",
}
HIGH_RISK_TOKENS: Tuple[Tuple[str, str], ...] = (
    (r"\bsidecar.?lock\b", "sidecar lock pattern"),
    (r"\bactive.?operation\b", "active-operation state"),
    (r"\bstale.?owner\b", "stale owner replacement"),
    (r"\bepoch\b", "fencing epoch"),
    (r"\bidempoten[ct]\b", "idempotency"),
    (r"\bnonce\b", "nonce-based identity"),
    (r"\bdedup[lic]*\b", "deduplication"),
    (r"\bconcurrent\b", "concurrency"),
    (r"\bsingle.?writer\b", "writer exclusivity"),
    (r"\block.?recovery\b", "lock recovery"),
    (r"\bstale.?pointer\b", "stale pointer handling"),
)
ALL_PHASES: Tuple[str, ...] = ("baseline", "behavioral", "property", "subprocess", "mutation", "review")


@dataclass
class PhaseDisposition:
    name: str
    disposition: str           # "REQUIRED" | "ADVISORY" | "SKIP"
    reason_code: str
    reason: str
    matched_paths: List[str] = field(default_factory=list)
    matched_symbols: List[str] = field(default_factory=list)
    matched_tokens: List[Tuple[str, str]] = field(default_factory=list)


@dataclass
class ClassificationResult:
    diff_ref: str
    diff_hash: str
    summary: str
    required_phases: List[str]
    skipped_phases: List[str]
    matched_paths: List[str]
    matched_symbols: List[str]
    matched_tokens: List[Tuple[str, str]]
    has_high_risk_change: bool
    created_at: str


def _run_git_diff(diff_ref: str) -> str:
    try:
        out = subprocess.run(
            ["git", "diff", diff_ref, "--unified=3"],
            capture_output=True, text=True, timeout=30,
        )
        return out.stdout if out.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def _read_diff_file(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _changed_paths(diff_text: str) -> List[str]:
    paths: List[str] = []
    for line in diff_text.splitlines():
        if line.startswith("diff --git"):
            parts = line.split()
            if len(parts) >= 4:
                b_path = parts[3].lstrip("b/")
                paths.append(b_path)
    return paths


def _hunk_headers(diff_text: str) -> List[str]:
    return [line for line in diff_text.splitlines() if line.startswith("@@")]


def _symbols_in_hunks(diff_text: str) -> Set[str]:
    syms: Set[str] = set()
    in_hunk = False
    for line in diff_text.splitlines():
        if line.startswith("@@"):
            in_hunk = True
            continue
        if line.startswith("diff --git"):
            in_hunk = False
            continue
        if in_hunk and (line.startswith("+") or line.startswith("-")):
            for m in re.finditer(r"\b([a-zA-Z_][a-zA-Z0-9_]{2,})\b", line[1:]):
                syms.add(m.group(1))
    return syms


def _find_tokens(diff_text: str) -> List[Tuple[str, str]]:
    found: List[Tuple[str, str]] = []
    for pattern, label in HIGH_RISK_TOKENS:
        if re.search(pattern, diff_text, re.IGNORECASE):
            found.append((pattern, label))
    return found


def _strip_comments(text: str) -> str:
    out: List[str] = []
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        out.append(line)
    return "\n".join(out)


def _classify_phases(result: ClassificationResult) -> ClassificationResult:
    has_high = bool(result.matched_paths or result.matched_symbols or result.matched_tokens)
    if has_high:
        result.required_phases = ["baseline", "behavioral", "property", "subprocess", "mutation", "review"]
        result.has_high_risk_change = True
        result.summary = (
            f"high_risk_change=True required_phases={','.join(result.required_phases)}"
        )
    else:
        result.required_phases = ["baseline", "review"]
        result.has_high_risk_change = False
        result.summary = "high_risk_change=False required_phases=baseline,review"
    result.skipped_phases = [p for p in ALL_PHASES if p not in result.required_phases]
    return result


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def classify_diff(diff_text: str, diff_ref: str = "HEAD") -> ClassificationResult:
    paths = _changed_paths(diff_text)
    syms = sorted(_symbols_in_hunks(diff_text) & HIGH_RISK_SYMBOLS)
    matched_paths = [p for p in paths if any(p.startswith(pref) for pref in HIGH_RISK_PATH_PREFIXES)]
    matched_tokens = _find_tokens(_strip_comments(diff_text))
    sym_match = bool(syms)
    result = ClassificationResult(
        diff_ref=diff_ref,
        diff_hash="",
        summary="",
        required_phases=[],
        skipped_phases=[],
        matched_paths=matched_paths,
        matched_symbols=syms if sym_match else [],
        matched_tokens=matched_tokens,
        has_high_risk_change=False,
        created_at=_iso_now(),
    )
    return _classify_phases(result)


def main() -> int:
    diff_text = sys.stdin.read() if not sys.stdin.isatty() else ""
    diff_ref = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
    if not diff_text:
        diff_text = _run_git_diff(diff_ref)
    result = classify_diff(diff_text, diff_ref)
    print(json.dumps(asdict(result), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
