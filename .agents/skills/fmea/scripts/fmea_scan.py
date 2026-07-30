"""FMEA scanner — identifies I/O boundaries in Python pipelines and generates failure-mode tables.

Usage:
    python fmea_scan.py <pipeline-path> [--json]
    python fmea_scan.py <file.py>

Walks the target directory for .py files, uses AST analysis to find I/O
boundaries (file ops, globs, subprocess calls, external APIs, state files,
shared directories), generates failure modes with S×O×D ratings and RPN.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Boundary:
    """An I/O boundary found in a script."""
    file: str
    line: int
    boundary_type: str  # file_read, file_write, glob, subprocess, external_api, state_file, shared_dir
    detail: str         # what the call does
    raw_code: str       # the source line


@dataclass
class FailureMode:
    """A failure mode derived from a boundary."""
    component: str       # script name
    failure_mode: str    # what can go wrong
    cause: str           # why
    effect: str          # what happens
    severity: int        # 1-10
    occurrence: int      # 1-10
    detection: int       # 1-10 (higher = harder to detect)
    rpn: int            # S × O × D
    boundary: Boundary   # source evidence


# --- AST visitor to find I/O boundaries ---

class BoundaryVisitor(ast.NodeVisitor):
    """Walks an AST and collects I/O boundary calls."""

    # Patterns that indicate I/O boundaries
    FILE_READ_METHODS = {"read_text", "read_bytes", "read", "readline", "readlines"}
    FILE_WRITE_METHODS = {"write_text", "write_bytes", "write", "writelines"}
    GLOB_METHODS = {"rglob", "glob", "iterdir"}
    SUBPROCESS_FUNCS = {"run", "Popen", "call", "check_call", "check_output"}

    # Shared directory path patterns
    SHARED_DIR_PATTERNS = [
        re.compile(r"/tmp/|/Temp/|\\\\tmp\\\\", re.IGNORECASE),
        re.compile(r"/\.data/|/\.state/", re.IGNORECASE),
        re.compile(r"os\.environ.*TEMP|tempfile", re.IGNORECASE),
    ]

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.boundaries: list[Boundary] = []

    def _add(self, node: ast.AST, btype: str, detail: str, raw: str):
        self.boundaries.append(Boundary(
            file=self.filepath,
            line=getattr(node, "lineno", 0),
            boundary_type=btype,
            detail=detail,
            raw_code=raw.strip()[:200],
        ))

    def visit_Call(self, node: ast.Call):
        # Get the function name being called
        func_name = self._get_func_name(node.func)

        # Check for file read/write via Path methods or open()
        if func_name in self.FILE_READ_METHODS:
            self._add(node, "file_read", f"File read via .{func_name}()", ast.unparse(node))
        elif func_name in self.FILE_WRITE_METHODS:
            self._add(node, "file_write", f"File write via .{func_name}()", ast.unparse(node))
        elif func_name == "open":
            self._add(node, "file_read", "open() call", ast.unparse(node))

        # Check for directory globs
        if func_name in self.GLOB_METHODS:
            self._add(node, "glob", f"Directory scan via .{func_name}()", ast.unparse(node))

        # Check for subprocess calls
        if func_name in self.SUBPROCESS_FUNCS or (isinstance(node.func, ast.Attribute) and
                                                   isinstance(node.func.value, ast.Name) and
                                                   node.func.value.id == "subprocess"):
            self._add(node, "subprocess", f"Subprocess call: {func_name}", ast.unparse(node))

        # Check for os.replace / os.rename (atomic-ish ops)
        if func_name in ("replace", "rename") and isinstance(node.func, ast.Attribute) and \
           isinstance(node.func.value, ast.Name) and node.func.value.id == "os":
            self._add(node, "file_write", f"os.{func_name}() atomic file op", ast.unparse(node))

        # Check for sqlite3 / database connections
        if func_name in ("connect", "Connection") and isinstance(node.func, ast.Attribute) and \
           isinstance(node.func.value, ast.Name) and node.func.value.id in ("sqlite3", "db"):
            self._add(node, "state_file", "Database connection", ast.unparse(node))

        # Check string args for shared directory patterns
        try:
            unparsed = ast.unparse(node)
            for pattern in self.SHARED_DIR_PATTERNS:
                if pattern.search(unparsed):
                    self._add(node, "shared_dir", "Shared/temp directory access", unparsed)
                    break
        except Exception:
            pass

        self.generic_visit(node)

    def _get_func_name(self, func: ast.expr) -> str:
        """Extract function name from various AST node shapes."""
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            return func.attr
        return ""


# --- Failure mode generation ---

def generate_failure_modes(boundaries: list[Boundary], script_name: str) -> list[FailureMode]:
    """Generate failure modes from identified boundaries."""

    # Rating heuristics by boundary type
    RATINGS = {
        "glob": {
            "fm": "Reads files outside intended scope (no filter on shared directory)",
            "cause": "Directory glob without identity filter",
            "effect": "Cross-contamination, wrong data processed, 0-page or corrupted output",
            "S": 9, "O": 8, "D": 8,  # RPN 576
        },
        "shared_dir": {
            "fm": "Other processes delete/modify files in shared directory",
            "cause": "Working files in non-durable location (P:/tmp/, shared data dir)",
            "effect": "Files disappear, script crashes or produces wrong results",
            "S": 7, "O": 7, "D": 6,  # RPN 294
        },
        "file_write": {
            "fm": "Write to wrong location or non-atomic write (torn write on crash)",
            "cause": "Direct write without tmp+rename pattern, or wrong path",
            "effect": "Corrupted file, partial data, downstream failures",
            "S": 6, "O": 5, "D": 7,  # RPN 210
        },
        "subprocess": {
            "fm": "External command fails, hangs, or returns unexpected output",
            "cause": "Unstable CLI, auth expiry, rate limiting, env not set",
            "effect": "Pipeline stalls, empty results, silent failures",
            "S": 7, "O": 6, "D": 5,  # RPN 210
        },
        "state_file": {
            "fm": "Database/state file locked, corrupted, or stale",
            "cause": "Concurrent access, schema drift, no migration",
            "effect": "State loss, crashes, inconsistent data",
            "S": 6, "O": 4, "D": 4,  # RPN 96
        },
        "file_read": {
            "fm": "File missing, wrong encoding, or stale data",
            "cause": "File deleted by other process, path changed, encoding mismatch",
            "effect": "Crash or empty output",
            "S": 5, "O": 4, "D": 3,  # RPN 60
        },
    }

    modes = []
    for b in boundaries:
        rating = RATINGS.get(b.boundary_type)
        if not rating:
            continue

        # Skip duplicates from same file+line (AST visits can double-count)
        if any(m.boundary.line == b.line and m.boundary.file == b.file and
               m.boundary.boundary_type == b.boundary_type for m in modes):
            continue

        s, o, d = rating["S"], rating["O"], rating["D"]
        modes.append(FailureMode(
            component=script_name,
            failure_mode=rating["fm"],
            cause=rating["cause"],
            effect=rating["effect"],
            severity=s,
            occurrence=o,
            detection=d,
            rpn=s * o * d,
            boundary=b,
        ))

    return modes


def scan_file(filepath: Path) -> list[FailureMode]:
    """Scan a single Python file for failure modes."""
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError as e:
        print(f"warning: parse error in {filepath}: {e}", file=sys.stderr)
        return []

    visitor = BoundaryVisitor(str(filepath.name))
    visitor.visit(tree)

    return generate_failure_modes(visitor.boundaries, filepath.name)


def scan_pipeline(pipeline_path: Path) -> list[FailureMode]:
    """Scan all Python files in a pipeline directory."""
    all_modes = []

    if pipeline_path.is_file() and pipeline_path.suffix == ".py":
        return scan_file(pipeline_path)

    for pyfile in sorted(pipeline_path.rglob("*.py")):
        # Skip __pycache__, tests, and __init__
        if "__pycache__" in str(pyfile) or pyfile.name.startswith("test_"):
            continue
        modes = scan_file(pyfile)
        all_modes.extend(modes)

    # Sort by RPN descending
    all_modes.sort(key=lambda m: m.rpn, reverse=True)
    return all_modes


def format_table(modes: list[FailureMode]) -> str:
    """Format failure modes as a markdown table."""
    if not modes:
        return "No I/O boundaries detected. Pipeline appears clean."

    lines = [
        "| Component | Failure mode | Cause | Effect | S | O | D | RPN | Source |",
        "|-----------|-------------|-------|--------|---|---|---|-----|--------|",
    ]

    for m in modes[:50]:  # cap at 50 rows
        b = m.boundary
        source = f"{b.file}:{b.line}"
        lines.append(
            f"| {m.component} | {m.failure_mode} | {m.cause} | {m.effect} | "
            f"{m.severity} | {m.occurrence} | {m.detection} | **{m.rpn}** | {source} |"
        )

    return "\n".join(lines)


def _target_hash(pipeline_path: Path) -> str:
    """Stable hash for a target path (for cache keying)."""
    return hashlib.md5(str(pipeline_path.resolve()).encode()).hexdigest()[:12]


def _collect_file_mtimes(pipeline_path: Path) -> dict:
    """Collect mtimes of all .py files in the target (for freshness check)."""
    mtimes = {}
    if pipeline_path.is_file():
        files = [pipeline_path]
    else:
        files = [f for f in pipeline_path.rglob("*.py")
                 if "__pycache__" not in str(f) and not f.name.startswith("test_")]
    for f in files:
        try:
            mtimes[str(f)] = f.stat().st_mtime
        except OSError:
            pass
    return mtimes


def _check_cache(cache_dir: Path, target_hash: str) -> dict | None:
    """Check for a fresh cached FMEA result. Returns cached data or None."""
    cache_file = cache_dir / f"fmea-{target_hash}.json"
    if not cache_file.exists():
        return None
    try:
        cached = json.loads(cache_file.read_text(encoding="utf-8"))
        return cached
    except (json.JSONDecodeError, OSError):
        return None


def _is_cache_fresh(cached: dict, pipeline_path: Path) -> tuple[bool, list[str]]:
    """Check if cached results are still fresh (no .py files modified since scan).

    Returns (is_fresh, changed_files).
    """
    cached_mtimes = cached.get("file_mtimes", {})
    current_mtimes = _collect_file_mtimes(pipeline_path)

    changed = []
    for fpath, current_mtime in current_mtimes.items():
        cached_mtime = cached_mtimes.get(fpath)
        if cached_mtime is None or current_mtime != cached_mtime:
            changed.append(fpath)

    # Also check for deleted files (fewer files now = stale)
    deleted = [f for f in cached_mtimes if f not in current_mtimes]

    is_fresh = len(changed) == 0 and len(deleted) == 0
    return is_fresh, changed


def _write_cache(cache_dir: Path, target_hash: str, modes: list[FailureMode],
                 pipeline_path: Path, file_mtimes: dict):
    """Write FMEA results to cache."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"fmea-{target_hash}.json"
    cache_data = {
        "target": str(pipeline_path),
        "scanned_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "failure_mode_count": len(modes),
        "high_rpn_count": len([m for m in modes if m.rpn >= 400]),
        "file_mtimes": file_mtimes,
        "modes": [asdict(m) for m in modes],
    }
    cache_file.write_text(json.dumps(cache_data, indent=2, default=str), encoding="utf-8")


FMEA_CACHE_DIR = Path("P:/.artifacts/fmea-cache")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="FMEA scanner — find component-level failure modes in Python pipelines")
    parser.add_argument("path", help="pipeline directory or .py file to scan")
    parser.add_argument("--json", action="store_true", help="output as JSON")
    parser.add_argument("--no-cache", action="store_true",
                        help="force re-scan, ignore cache")
    parser.add_argument("--cache-dir", default=str(FMEA_CACHE_DIR),
                        help=f"cache directory (default: {FMEA_CACHE_DIR})")
    args = parser.parse_args()

    pipeline_path = Path(args.path)
    if not pipeline_path.exists():
        print(f"error: path not found: {pipeline_path}", file=sys.stderr)
        return 1

    use_cache = not args.no_cache
    cache_dir = Path(args.cache_dir)
    target_hash = _target_hash(pipeline_path)

    # Check cache freshness
    cached_source = False
    if use_cache:
        cached = _check_cache(cache_dir, target_hash)
        if cached:
            is_fresh, changed = _is_cache_fresh(cached, pipeline_path)
            if is_fresh:
                # Cache is fresh — use it
                cached_source = True
                # Reconstruct modes from cached data
                modes = []
                for m_data in cached.get("modes", []):
                    b_data = m_data.get("boundary", {})
                    b = Boundary(
                        file=b_data.get("file", ""),
                        line=b_data.get("line", 0),
                        boundary_type=b_data.get("boundary_type", ""),
                        detail=b_data.get("detail", ""),
                        raw_code=b_data.get("raw_code", ""),
                    )
                    modes.append(FailureMode(
                        component=m_data.get("component", ""),
                        failure_mode=m_data.get("failure_mode", ""),
                        cause=m_data.get("cause", ""),
                        effect=m_data.get("effect", ""),
                        severity=m_data.get("severity", 0),
                        occurrence=m_data.get("occurrence", 0),
                        detection=m_data.get("detection", 0),
                        rpn=m_data.get("rpn", 0),
                        boundary=b,
                    ))
                cache_age = cached.get("scanned_at", "unknown")
            else:
                # Cache exists but stale — re-scan
                modes = scan_pipeline(pipeline_path)
                file_mtimes = _collect_file_mtimes(pipeline_path)
                _write_cache(cache_dir, target_hash, modes, pipeline_path, file_mtimes)
        else:
            # No cache — scan and cache
            modes = scan_pipeline(pipeline_path)
            file_mtimes = _collect_file_mtimes(pipeline_path)
            _write_cache(cache_dir, target_hash, modes, pipeline_path, file_mtimes)
    else:
        modes = scan_pipeline(pipeline_path)

    if args.json:
        print(json.dumps([asdict(m) for m in modes], indent=2, default=str))
    else:
        source_note = f" (cached from {cache_age})" if cached_source else ""
        print(f"# FMEA Report: {pipeline_path.name}{source_note}\n")
        print(f"**Scanned:** {pipeline_path}")
        print(f"**Failure modes found:** {len(modes)}")
        print(f"**High RPN (≥400):** {len([m for m in modes if m.rpn >= 400])}")
        print(f"**Medium RPN (100-399):** {len([m for m in modes if 100 <= m.rpn < 400])}")
        print(f"**Low RPN (<100):** {len([m for m in modes if m.rpn < 100])}")
        print()
        print(format_table(modes))

    return 0


if __name__ == "__main__":
    sys.exit(main())
