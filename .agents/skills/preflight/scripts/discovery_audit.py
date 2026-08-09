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
    # build / packaging output
    "node_modules", "site-packages", "__pycache__", "dist", "build",
    "target", "out", "htmlcov",
    # virtualenvs
    ".venv", "venv", "env",
    # linter / test caches
    ".pytest_cache", ".ruff_cache", ".mypy_cache", ".tox", ".nox", ".coverage",
    # workspace runtime / session / telemetry
    ".session", "sessions", "session_data", ".state", "state", "logs",
    "memtrace", ".tmp", "tmp", ".locks", ".benchmarks", ".deepeval",
    "marketplace-cache", "relocations", "plugin-data", "implement-memory",
    "vendor", "exports",
    # vcs / ide
    ".git", ".idea", ".vscode", ".codex",
}

# Dotted directory names that are WORKSPACE SCOPE ROOTS, not derived state.
# Everything else starting with "." is treated as cache/config/state. This is
# the durable backstop: new tooling-introduced hidden dirs (.cache, .newtool)
# are non-authoritative without per-dir maintenance. Workspace roots are a
# finite, stable set and are exempted here.
_DOT_SCOPE_ROOTS = frozenset({
    ".claude", ".grok", ".agents", ".data", ".claude-marketplace",
})

# Non-dotted directory component names that are derived runtime state or build
# output. Enumerated from a filesystem scan of this workspace; kept in sync
# with SKIP_DIRS. Used by _classification so that files inside these dirs are
# never treated as authority candidates even if they slip past the walk prune.
_DERIVED_COMPONENTS = frozenset({
    "node_modules", "site-packages", "__pycache__", "dist", "build",
    "target", "out", "htmlcov", "venv", "env",
    "sessions", "session_data", "state", "logs", "memtrace",
    "tmp", "vendor", "exports",
    "marketplace-cache", "relocations", "plugin-data", "implement-memory",
    "worktrees",
})


def _is_derived_component(part: str) -> bool:
    """Whether a path component marks the file as non-authoritative derived state."""
    if part in _DERIVED_COMPONENTS:
        return True
    # Durable backstop: any hidden directory (dot-prefix) that is NOT a known
    # workspace scope root is cache/config/state. Catches future tooling dirs
    # (.cache, .nox, .mypy_cache, .newtool) without per-dir maintenance.
    if part.startswith(".") and part != "." and part not in _DOT_SCOPE_ROOTS:
        return True
    return False


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
    cap_hit = False
    for scope in scopes:
        if not scope.exists():
            errors.append(f"missing_scope:{scope}")
            continue
        if scope.is_file():
            files.append(scope)
            continue
        try:
            for path in scope.rglob("*"):
                if cap_hit:
                    break
                # Unified prune: any derived component (state/cache/venv/worktree/
                # dot-dir-backstop) is skipped at walk time, keeping the walk and
                # the classifier on the same source of truth so they cannot drift.
                if any(_is_derived_component(part.lower()) for part in path.parts):
                    continue
                if not path.is_file():
                    continue
                # Suffix-filter at enqueue: non-text files (binaries, lockfiles,
                # images, .pyc, .so) cannot be inspected as text and cannot
                # define a default. Skipping them prevents derived trees
                # (venvs, build output) from exhausting the file cap and
                # causing silent inventory loss of later scopes.
                if path.suffix.lower() not in TEXT_SUFFIXES:
                    continue
                files.append(path)
                if len(files) >= max_files:
                    errors.append(f"file_limit_reached:{max_files}")
                    cap_hit = True
                    break
        except OSError as exc:
            errors.append(f"walk_error:{scope}:{type(exc).__name__}:{exc}")
    return files, errors


def _classification(path: Path) -> str:
    parts = [p.lower() for p in path.parts]
    text = str(path).replace("\\", "/").lower()
    # Specific derived labels (kept for packet readability)
    if "/plugins/cache/" in text or "/.claude/plugins/cache/" in text:
        return "cache"
    if "/.worktrees/" in text or "/worktrees/" in text:
        return "worktree"
    # Any derived component (state, cache, venv, session, dot-dir-backstop)
    # routes to runtime_state so it can never manufacture a conflict.
    if any(_is_derived_component(p) for p in parts):
        if "/.evidence/" in text or "/test" in text:
            return "test_or_evidence"
        return "runtime_state"
    if "/.evidence/" in text or "/test" in text:
        return "test_or_evidence"
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
                    role_candidates.setdefault(role, [])
                    # Deduplicate by file path — overlapping targets (e.g.
                    # "quality-gate" and "quality-gate.json") can match the
                    # same file, which is target overlap, not a role conflict.
                    if not any(c["path"] == str(path) for c in role_candidates[role]):
                        role_candidates[role].append({
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
    # Recompute role_counts from deduplicated candidates so overlapping
    # targets (e.g. "quality-gate" and "quality-gate.json") matching the
    # same file don't produce a false multiple_role_candidates conflict.
    role_counts = {role: len(cands) for role, cands in role_candidates.items()}
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
    # Lifecycle-default conflict: only flag when two or more DISTINCT
    # authority-candidate source files reference the SAME marker — that
    # pattern suggests competing definitions of a default (e.g. two hooks
    # both setting GO_WORKTREE_ROOT). A single source file mentioning a
    # marker is not a conflict; it is the file doing its job (a hook that
    # handles worktree paths will legitimately contain "P:/.worktrees").
    # Non-authoritative files (logs, state, worktree copies) never count.
    auth_hits_by_marker: dict[str, set[str]] = {}
    for item in default_hits:
        if not item["authority_candidate"]:
            continue
        auth_hits_by_marker.setdefault(item["marker"], set()).add(item["path"])
    competing = {m: paths for m, paths in auth_hits_by_marker.items() if len(paths) > 1}
    if competing:
        conflicts.append({
            "kind": "configuration_or_lifecycle_default_requires_full_reader_writer_audit",
            "competing_markers": {m: sorted(paths) for m, paths in competing.items()},
            "hits": default_hits,
        })

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
