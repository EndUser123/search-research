"""Shared import resolution utilities for hook and skill consumption.

Extracted from PreToolUse_investigation_gate.py for reuse by:
- PreToolUse_investigation_gate.py (original consumer)
- /refactor skill step 8.5 (blast radius scan)
- /tdd skill REFACTOR phase (blast radius scan)

All functions are stateless — pure functions of (source_text, file_path, git_status).
This makes them inherently multi-terminal safe and compaction resilient.
"""

import ast
import subprocess
import sys
from pathlib import Path
from typing import Any


def _read_file_safe(filepath: Path) -> str:
    """Read file content, returning empty string on any failure."""
    try:
        return filepath.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def extract_import_specs(source_text: str) -> list[dict[str, Any]]:
    """Parse import statements and return candidate local module specs."""
    if not source_text.strip():
        return []

    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return []

    specs: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name:
                    specs.append({"spec": alias.name, "kind": "import"})
        elif isinstance(node, ast.ImportFrom):
            prefix = "." * node.level + (node.module or "")
            if prefix:
                specs.append({"spec": prefix, "kind": "from"})
            for alias in node.names:
                if not alias.name or alias.name == "*":
                    continue
                if not node.module and node.level:
                    specs.append({"spec": f"{'.' * node.level}{alias.name}", "kind": "from_relative"})
                else:
                    specs.append({"spec": alias.name, "kind": "from"})

    unique: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in specs:
        spec = str(entry["spec"])
        if spec not in seen:
            seen.add(spec)
            unique.append(entry)
    return unique


def collect_attribute_bases(tree: ast.AST) -> set[str]:
    """Collect names used as attribute bases, e.g. tracing.QueryTracer."""
    bases: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            bases.add(node.value.id)
    return bases


def candidate_module_paths(spec: str, target_path: Path) -> list[Path]:
    """Generate possible on-disk paths for a module spec."""
    spec = spec.strip()
    if not spec:
        return []

    relative_depth = len(spec) - len(spec.lstrip("."))
    module_name = spec.lstrip(".")
    module_parts = [part for part in module_name.split(".") if part]
    if not module_parts:
        return []

    base_dirs: list[Path] = []
    target_parent = target_path.resolve(strict=False).parent
    if relative_depth:
        base = target_parent
        for _ in range(max(relative_depth - 1, 0)):
            if base.parent == base:
                break
            base = base.parent
        base_dirs.append(base)
    else:
        base_dirs.append(target_parent)
        base_dirs.extend(list(target_parent.parents))

    candidates: list[Path] = []
    for base in base_dirs:
        module_path = base.joinpath(*module_parts)
        candidates.append(module_path.with_suffix(".py"))
        candidates.append(module_path / "__init__.py")

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def resolve_local_imports(
    target_path: Path, repo_root: Path, status_map: dict[str, str], source_text: str
) -> dict[str, Any]:
    """Resolve local imports and identify tombstones or staged dependency targets."""
    import_specs = extract_import_specs(source_text)
    try:
        tree = ast.parse(source_text) if source_text.strip() else None
    except SyntaxError:
        tree = None
    attribute_bases = collect_attribute_bases(tree) if tree is not None else set()
    from_import_aliases: list[tuple[str, str]] = []
    if tree is not None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                prefix = "." * node.level + (node.module or "")
                if not prefix:
                    continue
                for alias in node.names:
                    if alias.name and alias.name != "*":
                        from_import_aliases.append((prefix, alias.name))
    local_import_specs: list[str] = []
    resolved_local_imports: list[dict[str, str]] = []
    unresolved_local_imports: list[str] = []
    deleted_or_staged_import_targets: list[str] = []

    stdlib_modules = getattr(sys, "stdlib_module_names", set())
    target_ancestry_names = {part.name for part in [target_path.parent, *target_path.parent.parents]}

    for entry in import_specs:
        spec = entry["spec"]
        top_level = spec.lstrip(".").split(".", 1)[0]
        if not top_level:
            continue
        if top_level not in stdlib_modules or spec.startswith("."):
            local_import_specs.append(spec)

        candidates = candidate_module_paths(spec, target_path)
        resolved_candidate = next((candidate for candidate in candidates if candidate.exists()), None)
        if resolved_candidate is not None:
            try:
                rel_candidate = resolved_candidate.resolve(strict=False).relative_to(repo_root.resolve())
                rel_key = rel_candidate.as_posix()
            except Exception:
                rel_key = resolved_candidate.as_posix()
            resolved_local_imports.append({"spec": spec, "path": rel_key})
            continue

        localish = spec.startswith(".") or top_level in target_ancestry_names
        candidate_hits: list[str] = []
        for candidate in candidates:
            try:
                rel_candidate = candidate.resolve(strict=False).relative_to(repo_root.resolve())
                rel_key = rel_candidate.as_posix()
            except Exception:
                rel_key = candidate.as_posix().replace("\\", "/")
            status = status_map.get(rel_key)
            if status and (status[0] == "D" or status[1] == "D" or "U" in status):
                candidate_hits.append(rel_key)

        if candidate_hits:
            unresolved_local_imports.append(spec)
            deleted_or_staged_import_targets.extend(candidate_hits)
        elif localish:
            unresolved_local_imports.append(spec)

    for prefix, alias_name in from_import_aliases:
        if alias_name not in attribute_bases:
            continue
        module_like_spec = f"{prefix}.{alias_name}"
        if module_like_spec in local_import_specs:
            continue
        local_import_specs.append(module_like_spec)
        candidates = candidate_module_paths(module_like_spec, target_path)
        resolved_candidate = next((candidate for candidate in candidates if candidate.exists()), None)
        if resolved_candidate is not None:
            try:
                rel_candidate = resolved_candidate.resolve(strict=False).relative_to(repo_root.resolve())
                rel_key = rel_candidate.as_posix()
            except Exception:
                rel_key = resolved_candidate.as_posix()
            resolved_local_imports.append({"spec": module_like_spec, "path": rel_key})
        else:
            unresolved_local_imports.append(module_like_spec)

    return {
        "local_import_specs": local_import_specs,
        "resolved_local_imports": resolved_local_imports,
        "unresolved_local_imports": list(dict.fromkeys(unresolved_local_imports)),
        "deleted_or_staged_import_targets": list(dict.fromkeys(deleted_or_staged_import_targets)),
        "local_import_count": len(local_import_specs),
    }


def get_git_status_map(repo_root: Path) -> dict[str, str]:
    """Build a git status map from ``git status --porcelain``.

    Returns a dict mapping POSIX-relative paths to their XY status codes.
    Stateless — fresh subprocess each call, inherently multi-terminal safe.
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=10,
        )
        status_map: dict[str, str] = {}
        for line in result.stdout.strip().splitlines():
            if len(line) >= 4:
                xy = line[:2]
                path = line[3:].strip()
                # Handle rename syntax: "old -> new"
                if " -> " in path:
                    path = path.split(" -> ", 1)[1]
                status_map[path] = xy
        return status_map
    except (subprocess.TimeoutExpired, OSError, ValueError):
        return {}


def scan_blast_radius(
    changed_files: list[str | Path],
    repo_root: Path,
    status_map: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Scan changed files for import breakage risk in their consumers.

    For each changed file, find all files that import it and check whether
    the import would still resolve after the change.

    This is the cross-file blast radius scan — the capability missing from
    the existing 4 import hooks, which only check the file being edited.

    Args:
        changed_files: Files that were modified.
        repo_root: Repository root for path resolution.
        status_map: Optional pre-built git status map. If None, a fresh one
            is built via ``git status --porcelain``.

    Returns:
        Dict with ``at_risk_consumers``, ``safe_consumers``, and ``scan_errors``.
    """
    if status_map is None:
        status_map = get_git_status_map(repo_root)

    # Build a set of changed file stems for matching
    changed_set: set[str] = set()
    for f in changed_files:
        p = Path(f)
        # Store both the full relative path and just the module stem
        try:
            rel = p.resolve(strict=False).relative_to(repo_root.resolve())
            changed_set.add(rel.as_posix())
        except Exception:
            changed_set.add(str(p).replace("\\", "/"))

    at_risk: list[dict[str, str]] = []
    safe: list[dict[str, str]] = []
    errors: list[str] = []

    # Walk repo for Python files that might import the changed files
    for py_file in repo_root.rglob("*.py"):
        # Skip __pycache__, .git, hidden dirs
        parts = py_file.parts
        if any("__pycache__" in p or p.startswith(".") for p in parts):
            continue

        source = _read_file_safe(py_file)
        if not source.strip():
            continue

        try:
            rel_py = py_file.resolve(strict=False).relative_to(repo_root.resolve())
            rel_key = rel_py.as_posix()
        except Exception:
            continue

        resolution = resolve_local_imports(py_file, repo_root, status_map, source)

        # Check if any resolved import points to a changed file
        for imp in resolution.get("resolved_local_imports", []):
            imp_path = imp.get("path", "")
            if imp_path in changed_set:
                # This consumer imports a changed file — check if still resolvable
                spec = imp.get("spec", "")
                candidates = candidate_module_paths(spec, py_file)
                still_exists = any(c.exists() for c in candidates)
                if still_exists:
                    safe.append({
                        "consumer": rel_key,
                        "import_spec": spec,
                        "target": imp_path,
                    })
                else:
                    at_risk.append({
                        "consumer": rel_key,
                        "import_spec": spec,
                        "target": imp_path,
                    })

        # Also flag unresolved imports that match changed file ancestry
        for spec in resolution.get("unresolved_local_imports", []):
            top = spec.lstrip(".").split(".", 1)[0]
            for changed in changed_set:
                changed_stem = Path(changed).stem
                if top == changed_stem:
                    at_risk.append({
                        "consumer": rel_key,
                        "import_spec": spec,
                        "target": changed,
                    })

    return {
        "at_risk_consumers": at_risk,
        "safe_consumers": safe,
        "scan_errors": errors,
        "files_scanned": sum(1 for _ in repo_root.rglob("*.py")
                           if not any("__pycache__" in p or p.startswith(".")
                                    for p in Path(_).parts)),
    }
