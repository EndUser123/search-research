#!/usr/bin/env python3
"""
Cross-file code analysis for /refactor's comprehensive analysis phase.

Performs static analysis across files and directories:
  1. Import graph + cycle detection (architecture smell)
  2. Dead code detection (via vulture)
  3. Complexity hotspots (via radon)
  4. Cross-file duplication (function-body similarity via AST)
  5. Test coverage gaps (via pytest --cov if available)

Output: JSON to stdout, structured for /refactor seams.json consumption.

Usage:
    python P:/.agents/scripts/code_analysis.py <directory> [--json|--text]
    python P:/.agents/scripts/code_analysis.py P:/packages/yt-is --json

Exit codes:
    0 = analysis completed (findings may or may not exist)
    1 = error (bad path, missing deps)
"""
import argparse
import ast
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


# ---------------------------------------------------------------------------
# 1. Import graph + cycle detection
# ---------------------------------------------------------------------------

def _extract_imports(filepath: Path, pkg_root: Path) -> list[str]:
    """Extract internal imports from a Python file via AST.

    Returns list of module names that are INTERNAL to the package
    (not stdlib or third-party).
    """
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"), filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return []

    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)

    # Filter to internal modules only (relative to package root)
    pkg_name = pkg_root.name
    internal = []
    for imp in imports:
        # Heuristic: internal if it starts with the package name
        # or is a sibling module (no dots, not in stdlib)
        if imp.startswith(pkg_name) or imp.startswith("."):
            internal.append(imp.lstrip("."))
        elif "." not in imp and imp not in sys.stdlib_module_names:
            # Could be a sibling module — check if file exists
            candidate = pkg_root / f"{imp}.py"
            if candidate.exists() or (pkg_root / imp).is_dir():
                internal.append(imp)

    return internal


def build_import_graph(target: Path) -> dict:
    """Build import graph and detect cycles.

    Returns:
        {
            "graph": {"module_a": ["module_b", "module_c"], ...},
            "cycles": [["module_a", "module_b", "module_a"], ...],
            "fan_in": {"module_a": 3, ...},
            "fan_out": {"module_a": 2, ...},
        }
    """
    pkg_root = target if target.is_dir() else target.parent
    py_files = list(pkg_root.rglob("*.py"))
    # Exclude tests, __pycache__, migrations
    py_files = [
        f for f in py_files
        if "__pycache__" not in str(f)
        and not f.name.startswith("test_")
        and "/tests/" not in str(f).replace("\\", "/")
        and "/migrations/" not in str(f).replace("\\", "/")
    ]

    graph = defaultdict(set)
    all_modules = set()

    for f in py_files:
        # Module name relative to pkg_root, without .py
        rel = f.relative_to(pkg_root)
        mod_name = str(rel).replace("\\", ".").replace("/", ".").removesuffix(".py")
        all_modules.add(mod_name)

        imports = _extract_imports(f, pkg_root)
        for imp in imports:
            # Normalize: strip package prefix for relative comparison
            imp_normalized = imp.removeprefix(f"{pkg_root.name}.")
            graph[mod_name].add(imp_normalized)

    # Convert sets to sorted lists
    graph_out = {k: sorted(v) for k, v in graph.items()}

    # Detect cycles via DFS
    cycles = []
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {m: WHITE for m in all_modules}

    def dfs(node: str, path: list[str]):
        color[node] = GRAY
        path.append(node)
        for neighbor in graph.get(node, []):
            if neighbor not in all_modules:
                continue  # external module
            if color.get(neighbor, WHITE) == GRAY:
                # Found a cycle — extract it
                cycle_start = path.index(neighbor)
                cycle = path[cycle_start:] + [neighbor]
                cycles.append(cycle)
            elif color.get(neighbor, WHITE) == WHITE:
                dfs(neighbor, path)
        path.pop()
        color[node] = BLACK

    for m in all_modules:
        if color[m] == WHITE:
            dfs(m, [])

    # Deduplicate cycles (same cycle from different starting points)
    seen_cycles = set()
    unique_cycles = []
    for c in cycles:
        # Normalize: rotate to start from smallest element
        core = c[:-1]  # remove trailing repeat
        if not core:
            continue
        min_idx = core.index(min(core))
        normalized = tuple(core[min_idx:] + core[:min_idx])
        if normalized not in seen_cycles:
            seen_cycles.add(normalized)
            unique_cycles.append(list(normalized) + [normalized[0]])

    # Compute fan-in / fan-out
    fan_in = defaultdict(int)
    fan_out = defaultdict(int)
    for src, targets in graph_out.items():
        fan_out[src] = len(targets)
        for t in targets:
            fan_in[t] += 1

    return {
        "graph": graph_out,
        "cycles": unique_cycles,
        "fan_in": dict(sorted(fan_in.items(), key=lambda x: -x[1])),
        "fan_out": dict(sorted(fan_out.items(), key=lambda x: -x[1])),
        "module_count": len(all_modules),
    }


# ---------------------------------------------------------------------------
# 2. Dead code detection (via vulture)
# ---------------------------------------------------------------------------

def detect_dead_code(target: Path) -> list[dict]:
    """Run vulture to find dead code."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "vulture", str(target), "--min-confidence", "60"],
            capture_output=True, text=True, timeout=30
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    findings = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        # Parse vulture output: path:line: name (confidence%)
        parts = line.split(":", 2)
        if len(parts) >= 3:
            filepath, lineno, rest = parts[0], parts[1], parts[2]
            findings.append({
                "file": filepath.strip(),
                "line": int(lineno.strip()) if lineno.strip().isdigit() else 0,
                "detail": rest.strip(),
                "category": "dead_code",
            })
    return findings


# ---------------------------------------------------------------------------
# 3. Complexity hotspots (via radon)
# ---------------------------------------------------------------------------

def detect_complexity_hotspots(target: Path, threshold: str = "C") -> list[dict]:
    """Run radon cc to find complexity hotspots (grade C or worse = 10+)."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "radon", "cc", str(target), "-s", "-n", threshold],
            capture_output=True, text=True, timeout=30
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    findings = []
    current_file = None
    for line in result.stdout.split("\n"):
        if not line:
            continue
        if line.endswith(".py"):
            current_file = line.strip()
        elif current_file and "complexity" in line.lower():
            findings.append({
                "file": current_file,
                "detail": line.strip(),
                "category": "complexity_hotspot",
            })
    return findings


# ---------------------------------------------------------------------------
# 4. Cross-file duplication (AST-based function similarity)
# ---------------------------------------------------------------------------

def _extract_function_bodies(filepath: Path) -> dict[str, ast.AST]:
    """Extract function name → AST body mapping."""
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"), filename=str(filepath))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return {}

    funcs = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            funcs[node.name] = node
    return funcs


def detect_duplication(target: Path, min_lines: int = 5) -> list[dict]:
    """Detect cross-file function duplication via AST structure comparison.

    Compares function bodies by normalizing (stripping names) and
    comparing the AST dump. Functions with identical structure across
    files are flagged as duplication.
    """
    pkg_root = target if target.is_dir() else target.parent
    py_files = [
        f for f in pkg_root.rglob("*.py")
        if "__pycache__" not in str(f) and not f.name.startswith("test_")
    ]

    # Collect all functions grouped by name
    functions_by_name: dict[str, list[tuple[Path, ast.AST]]] = defaultdict(list)

    for f in py_files:
        funcs = _extract_function_bodies(f)
        for name, node in funcs.items():
            # Only consider functions with enough body lines
            end_line = getattr(node, "end_lineno", node.lineno)
            if end_line - node.lineno >= min_lines:
                functions_by_name[name].append((f, node))

    findings = []
    for name, occurrences in functions_by_name.items():
        if len(occurrences) < 2:
            continue
        # Same function name in 2+ files — check if bodies are similar
        files = [str(f.relative_to(pkg_root)) for f, _ in occurrences]
        # Compare AST dumps (normalized)
        dumps = []
        for _, node in occurrences:
            # Normalize: replace all Name nodes with placeholder
            for n in ast.walk(node):
                if isinstance(n, ast.Name):
                    n.id = "_VAR_"
            dumps.append(ast.dump(node))

        # Check if any pair is identical
        for i in range(len(dumps)):
            for j in range(i + 1, len(dumps)):
                if dumps[i] == dumps[j]:
                    findings.append({
                        "category": "duplication",
                        "function": name,
                        "files": [files[i], files[j]],
                        "detail": f"Function '{name}' has identical AST structure in {files[i]} and {files[j]}",
                    })

    return findings


# ---------------------------------------------------------------------------
# 5. Test coverage gaps
# ---------------------------------------------------------------------------

def detect_test_gaps(target: Path) -> list[dict]:
    """Detect files with no corresponding test file."""
    if not target.is_dir():
        return []

    py_files = [
        f for f in target.rglob("*.py")
        if "__pycache__" not in str(f)
        and not f.name.startswith("test_")
        and not f.name.startswith("__")
        and f.name != "setup.py"
    ]

    findings = []
    test_dirs = [target / "tests", target / "test"]

    for f in py_files:
        # Check for corresponding test file
        test_name = f"test_{f.name}"
        has_test = False
        for test_dir in test_dirs:
            if (test_dir / test_name).exists():
                has_test = True
                break
        # Also check same directory
        if (f.parent / test_name).exists():
            has_test = True

        if not has_test:
            rel = str(f.relative_to(target))
            findings.append({
                "file": rel,
                "category": "test_gap",
                "detail": f"No test file found for {rel}",
            })

    return findings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_analysis(target: str) -> dict:
    """Run all analysis dimensions and return structured findings."""
    target_path = Path(target).resolve()
    if not target_path.exists():
        print(json.dumps({"error": f"Path not found: {target_path}"}), file=sys.stderr)
        sys.exit(1)

    print(f"Analyzing: {target_path}", file=sys.stderr)

    # 1. Import graph + cycles
    print("  [1/5] Import graph + cycle detection...", file=sys.stderr)
    import_data = build_import_graph(target_path)

    # 2. Dead code
    print("  [2/5] Dead code detection (vulture)...", file=sys.stderr)
    dead_code = detect_dead_code(target_path)

    # 3. Complexity hotspots
    print("  [3/5] Complexity hotspots (radon)...", file=sys.stderr)
    complexity = detect_complexity_hotspots(target_path)

    # 4. Cross-file duplication
    print("  [4/5] Cross-file duplication detection...", file=sys.stderr)
    duplication = detect_duplication(target_path)

    # 5. Test coverage gaps
    print("  [5/5] Test coverage gap detection...", file=sys.stderr)
    test_gaps = detect_test_gaps(target_path)

    # Architecture smells from import graph
    arch_smells = []
    for cycle in import_data.get("cycles", []):
        arch_smells.append({
            "category": "architecture_smell",
            "type": "cyclic_dependency",
            "modules": cycle,
            "detail": f"Circular dependency: {' → '.join(cycle)}",
        })

    # God component detection (high fan-in + high fan-out)
    for mod, fin in import_data.get("fan_in", {}).items():
        fout = import_data.get("fan_out", {}).get(mod, 0)
        if fin >= 5 and fout >= 5:
            arch_smells.append({
                "category": "architecture_smell",
                "type": "god_component",
                "module": mod,
                "fan_in": fin,
                "fan_out": fout,
                "detail": f"Module '{mod}' has high coupling (fan-in={fin}, fan-out={fout})",
            })

    return {
        "target": str(target_path),
        "analysis_type": "comprehensive",
        "summary": {
            "modules": import_data.get("module_count", 0),
            "cycles": len(import_data.get("cycles", [])),
            "dead_code_items": len(dead_code),
            "complexity_hotspots": len(complexity),
            "duplication_clusters": len(duplication),
            "test_gaps": len(test_gaps),
            "architecture_smells": len(arch_smells),
        },
        "import_graph": import_data,
        "findings": {
            "architecture_smells": arch_smells,
            "dead_code": dead_code,
            "complexity_hotspots": complexity,
            "duplication": duplication,
            "test_gaps": test_gaps,
        },
    }


def main():
    parser = argparse.ArgumentParser(
        description="Cross-file code analysis for /refactor comprehensive analysis phase"
    )
    parser.add_argument("target", help="Directory or file to analyze")
    parser.add_argument("--text", action="store_true", help="Human-readable output instead of JSON")
    args = parser.parse_args()

    result = run_analysis(args.target)

    if args.text:
        print(f"\n{'='*60}")
        print(f"ANALYSIS: {result['target']}")
        print(f"{'='*60}")
        s = result["summary"]
        print(f"Modules: {s['modules']} | Cycles: {s['cycles']} | Dead code: {s['dead_code_items']}")
        print(f"Complexity hotspots: {s['complexity_hotspots']} | Duplication: {s['duplication_clusters']}")
        print(f"Test gaps: {s['test_gaps']} | Architecture smells: {s['architecture_smells']}")

        for cat, items in result["findings"].items():
            if items:
                print(f"\n--- {cat.upper()} ({len(items)}) ---")
                for item in items[:20]:  # cap display
                    print(f"  {item.get('detail', item)}")
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
