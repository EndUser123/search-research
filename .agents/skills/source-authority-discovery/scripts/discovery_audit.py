"""Evidence-producing source, authority, and conflict inventory for Codex."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

SCHEMA_VERSION = "source-discovery.v1"
TEXT_SUFFIXES = {
    ".json", ".jsonl", ".md", ".py", ".ps1", ".sh", ".toml", ".yaml", ".yml",
    ".txt", ".ini", ".cfg", ".xml", ".js", ".ts",
}
SKIP_DIRS = {
    ".git", "__pycache__", ".pytest_cache", "node_modules", ".ruff_cache",
    ".mypy_cache", ".tox", "dist", "build",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _safe_text(path: Path, limit: int = 2_000_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def _walk_files(scopes: Iterable[Path], max_files: int) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    errors: list[str] = []
    for scope in scopes:
        if not scope.exists():
            errors.append(f"missing_scope:{scope}")
            continue
        if scope.is_file():
            files.append(scope)
            continue
        try:
            for path in scope.rglob("*"):
                if any(part in SKIP_DIRS for part in path.parts):
                    continue
                if path.is_file():
                    files.append(path)
                    if len(files) >= max_files:
                        errors.append(f"file_limit_reached:{max_files}")
                        return files, errors
        except OSError as exc:
            errors.append(f"walk_error:{scope}:{type(exc).__name__}:{exc}")
    return files, errors


def _classification(path: Path) -> str:
    text = str(path).replace("\\", "/").lower()
    if "/plugins/cache/" in text or "/.claude/plugins/cache/" in text:
        return "cache"
    if "/.worktrees/" in text or "/worktrees/" in text:
        return "worktree"
    if "/.evidence/" in text or "/test" in text:
        return "test_or_evidence"
    if "/.artifacts/" in text or "/state/" in text:
        return "runtime_state"
    if "/docs/" in text or text.endswith(".md"):
        return "documentation_or_plan"
    return "candidate_source"


def _is_authority_candidate(classification: str) -> bool:
    """Return whether a file can establish an implementation/default conflict.

    Documentation and tests are intentionally reported as references, but they
    must not be counted as competing runtime owners.  Otherwise this audit
    would manufacture conflicts from its own instructions and fixtures.

    Worktrees, generated artifacts (.artifacts/), caches, evidence dumps,
    and test_or_evidence paths are explicitly excluded — they are derived
    copies, not authoritative sources.  Including them inflates the conflict
    count and makes every audit return `blocked` when the real sources are
    already in canonical locations.

    Only `candidate_source` (real, hand-authored code under P:/.claude,
    P:/packages, P:/.agents, P:/docs, P:/scripts, etc.) can establish a
    conflict against another candidate_source entry.  Runtime state is
    still reported in the packet for visibility but cannot itself
    manufacture a conflict.
    """
    return classification in {"candidate_source"}


def _git_root(path: Path) -> str | None:
    start = path if path.is_dir() else path.parent
    try:
        result = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=False,
        )
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def _git_snapshot(path: Path) -> dict[str, object]:
    root = _git_root(path)
    if not root:
        return {"path": str(path), "git_root": None}
    def run(*args: str) -> str:
        result = subprocess.run(
            ["git", "-C", root, *args], capture_output=True, text=True, check=False,
        )
        return result.stdout.strip()
    return {
        "path": str(path),
        "git_root": root,
        "head": run("rev-parse", "HEAD"),
        "branch": run("branch", "--show-current"),
        "status": run("status", "--short"),
        "worktrees": run("worktree", "list", "--porcelain"),
    }


def audit(*, scopes: list[str], targets: list[str], max_files: int = 20_000) -> dict[str, object]:
    scope_paths = [Path(item).expanduser().resolve() for item in scopes]
    normalized_targets = [item.lower() for item in targets]
    files, walk_errors = _walk_files(scope_paths, max_files)
    matching: list[dict[str, object]] = []
    active_plans: list[dict[str, object]] = []
    default_hits: list[dict[str, object]] = []
    role_counts: dict[str, int] = {}
    role_candidates: dict[str, list[dict[str, str]]] = {}

    for path in files:
        name = path.name.lower()
        text = _safe_text(path) if path.suffix.lower() in TEXT_SUFFIXES else ""
        classification = _classification(path)
        name_hits = [target for target in normalized_targets if target in name]
        content_hits = [target for target in normalized_targets if target in text.lower()]
        if name_hits or content_hits:
            # Only filename matches in authority-bearing files count as
            # candidate implementations. Content references in docs/tests are
            # useful evidence but are not competing runtime owners.
            if name_hits and _is_authority_candidate(classification):
                for role in name_hits:
                    role_counts[role] = role_counts.get(role, 0) + 1
                    role_candidates.setdefault(role, []).append({
                        "path": str(path),
                        "classification": classification,
                    })
            matching.append({
                "path": str(path),
                "classification": classification,
                "name_hits": sorted(set(name_hits)),
                "content_hits": sorted(set(content_hits)),
                "git_root": _git_root(path),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.stat().st_size < 20_000_000 else "too_large",
            })
        if name == "active-plan.json" or ".planning" in {part.lower() for part in path.parts}:
            plan_text = text.lower()
            if any(target in name or target in plan_text for target in normalized_targets):
                active_plans.append({"path": str(path), "classification": classification})
        for marker in ("GO_WORKTREE_ROOT", "GO_MANAGED_WORKTREE_ROOT", "P:/worktrees", "P:/.worktrees"):
            if marker.lower() in text.lower():
                default_hits.append({
                    "path": str(path),
                    "marker": marker,
                    "classification": classification,
                    "authority_candidate": _is_authority_candidate(classification),
                })

    conflicts: list[dict[str, object]] = []
    for role, count in sorted(role_counts.items()):
        if count > 1:
            conflicts.append({
                "kind": "multiple_role_candidates",
                "role": role,
                "count": count,
                "candidates": role_candidates[role],
            })
    if active_plans:
        conflicts.append({"kind": "overlapping_active_plan", "plans": active_plans})
    if any(
        item["authority_candidate"]
        for item in default_hits
    ):
        conflicts.append({"kind": "configuration_or_lifecycle_default_requires_full_reader_writer_audit", "hits": default_hits})

    missing_scopes = [str(path) for path in scope_paths if not path.exists()]
    if walk_errors or missing_scopes:
        decision = "blocked"
    elif conflicts:
        decision = "needs_review"
    else:
        decision = "proceed_with_discovery"
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at": _now(),
        "scopes": [{"path": str(path), "exists": path.exists()} for path in scope_paths],
        "targets": normalized_targets,
        "matching_files": sorted(matching, key=lambda item: str(item["path"]).lower()),
        "active_plans": active_plans,
        "default_hits": default_hits,
        "git_snapshots": [_git_snapshot(path) for path in scope_paths],
        "walk_errors": walk_errors,
        "conflicts": conflicts,
        "decision": decision,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a source-authority discovery packet")
    parser.add_argument("--scope", action="append", required=True)
    parser.add_argument("--target", action="append", required=True)
    parser.add_argument("--output")
    parser.add_argument("--max-files", type=int, default=20_000)
    parser.add_argument("--fail-on-conflict", action="store_true")
    args = parser.parse_args(argv)
    report = audit(scopes=args.scope, targets=args.target, max_files=args.max_files)
    encoded = json.dumps(report, indent=2) + "\n"
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    if report["decision"] == "blocked":
        return 3
    if args.fail_on_conflict and report["decision"] == "needs_review":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
