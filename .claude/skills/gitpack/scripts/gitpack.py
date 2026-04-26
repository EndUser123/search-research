#!/usr/bin/env python3
"""
Build a two-file gitpack output for a Python codebase: signatures + full source.

No external AI tools required — uses AST parsing and direct file reads.

Workflow:
  python gitpack.py <target_dir> [--exclude <patterns>]

Produces two files in .aid/<name>/:
  - <name>_sig.md  — SIGNATURE TOC + DIRECTORY/FILE INDEX (compact, scannable)
  - <name>_full.md — same + APPENDIX with full source read from disk

Target dir is processed directly: .py files discovered via glob, signatures
extracted via AST, appendix read directly from source. Deterministic output.
"""

import ast
import sys
import re
import glob as glob_module
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Signature extraction
# ---------------------------------------------------------------------------

def extract_py_signatures(filepath: str) -> list[str]:
    """Extract function/class signatures from a Python file via AST."""
    try:
        source = Path(filepath).read_text(encoding="utf-8")
    except Exception:
        return []

    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        # Fall back to line-based extraction for files with syntax errors
        return _fallback_signature_extraction(source)

    lines_by_node: dict[int, str] = {}
    signatures: list[str] = []

    class SignatureExtractor(ast.NodeVisitor):
        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            lines_by_node[node.lineno] = _format_func(node.name, node.args, source, node.lineno)
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
            lines_by_node[node.lineno] = f"async {_format_func(node.name, node.args, source, node.lineno)}"
            self.generic_visit(node)

        def visit_ClassDef(self, node: ast.ClassDef) -> None:
            lines_by_node[node.lineno] = f"class {node.name}"
            self.generic_visit(node)

    SignatureExtractor().visit(tree)

    for lineno in sorted(lines_by_node):
        signatures.append(lines_by_node[lineno])

    return signatures


def _format_func(name: str, args: ast.arguments, source: str, lineno: int) -> str:
    """Format a function signature from AST args + any type annotations on the def line."""
    arg_parts = []
    for arg in args.args:
        ann = arg.annotation
        if ann:
            ann_str = _get_annotation_str(ann, source)
            arg_parts.append(f"{arg.arg}: {ann_str}")
        else:
            arg_parts.append(arg.arg)

    # Handle *args and **kwargs
    if args.vararg:
        arg_parts.append(f"*{args.vararg.arg}")
    if args.kwarg:
        arg_parts.append(f"**{args.kwarg.arg}")

    # Get return annotation from the function def line if present
    return_annotation = _get_function_return_annotation(source, lineno)

    sig = f"{name}({', '.join(arg_parts)})"
    if return_annotation:
        sig += f" -> {return_annotation}"
    return sig


def _get_annotation_str(ann: ast.expr, source: str) -> str:
    """Get the string representation of an annotation from the source."""
    # For simple names, we can just use the name
    if isinstance(ann, ast.Name):
        return ann.id
    elif isinstance(ann, ast.Attribute):
        # Walk the attribute chain
        parts = []
        node = ann
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
        return ".".join(reversed(parts))
    elif isinstance(ann, ast.Subscript):
        # Generic types like List[int], Dict[str, Any]
        base = _get_annotation_str(ann.value, source)
        if ann.slice:
            slice_str = _get_annotation_str(ann.slice, source)
            return f"{base}[{slice_str}]"
        return base
    elif isinstance(ann, ast.Constant):
        return repr(ann.value)
    elif isinstance(ann, ast.BinOp):
        # Union types: X | Y
        left = _get_annotation_str(ann.left, source)
        right = _get_annotation_str(ann.right, source)
        return f"{left} | {right}"
    return "Any"


def _get_function_return_annotation(source: str, lineno: int) -> str:
    """Check the def line for a return type annotation."""
    lines = source.splitlines()
    if lineno < 1 or lineno > len(lines):
        return ""
    line = lines[lineno - 1].strip()
    # Look for "-> Type" at the end before the colon
    m = re.search(r"->\s*([\w\[\]\|\s.,]+)\s*:\s*$", line)
    if m:
        return m.group(1).strip()
    return ""


def _fallback_signature_extraction(source: str) -> list[str]:
    """Fallback when AST parsing fails — use regex on lines."""
    sigs: list[str] = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith("def ") or stripped.startswith("async def ") or stripped.startswith("class "):
            # Stop at first line that looks like implementation (no colon at end or has body)
            if not stripped.startswith("class "):
                m = re.match(r"(async\s+)?def\s+(\w+)\(.*\)(?:\s*->\s*[^\s:]+)?\s*:", stripped)
                if m:
                    prefix = "async " if stripped.startswith("async def ") else ""
                    sigs.append(stripped.rstrip(":"))
            else:
                m = re.match(r"class\s+(\w+).*", stripped)
                if m:
                    sigs.append(stripped.rstrip(":"))
    return sigs


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def discover_python_files(target_dir: Path, exclude_patterns: str = "") -> list[str]:
    """Find all .py files in target_dir, excluding patterns."""
    patterns = [p.strip() for p in exclude_patterns.split(",") if p.strip()]

    def is_excluded(path: Path) -> bool:
        path_str = str(path)
        for pattern in patterns:
            if pattern in path_str:
                return True
        return False

    files: list[str] = []
    for pattern in ["**/*.py", "**/*.pyw"]:
        for p in target_dir.glob(pattern):
            if is_excluded(p) or p.name.startswith("."):
                continue
            # Only include files, not directories
            if p.is_file():
                files.append(str(p.resolve()))

    return sorted(files)


# ---------------------------------------------------------------------------
# Markdown building
# ---------------------------------------------------------------------------

def build_signatures_section(filepaths: list[str]) -> list[str]:
    lines = ["## SIGNATURE TOC", ""]
    for fp in filepaths:
        sigs = extract_py_signatures(fp)
        lines.append(f"### {fp}")
        lines.append("```python")
        if sigs:
            lines.extend(sigs)
        else:
            lines.append("# (no public definitions)")
        lines.append("```")
        lines.append("")
    return lines


def group_by_dir(files: list[str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for filepath in files:
        parts = filepath.replace("\\", "/").split("/")
        top = parts[-2] if len(parts) > 1 else parts[0] if parts else filepath
        groups.setdefault(top, []).append(filepath)
    return groups


def build_directory_index(files: list[str]) -> list[str]:
    groups = group_by_dir(files)
    lines = ["## DIRECTORY INDEX", "", "| Directory | Files |", "|---------|-------|"]
    for dir_name in sorted(groups):
        lines.append(f"| `{dir_name}/` | {len(groups[dir_name])} |")
    return lines


def build_file_index(files: list[str]) -> list[str]:
    lines = ["", "## FILE INDEX", "", "| File | Description |", "|------|-------------|"]
    for filepath in sorted(files):
        name = Path(filepath).stem
        parts = filepath.replace("\\", "/").split("/")
        if name in ("__init__", "index", "main"):
            desc = f"Package: {parts[-2]}" if len(parts) > 1 else filepath
        else:
            desc = name.replace("_", " ").replace("-", " ")
        lines.append(f"| `{filepath}` | {desc} |")
    return lines


def build_appendix(filepaths: list[str]) -> list[str]:
    lines = ["", "---", "", "## APPENDIX: FULL IMPLEMENTATIONS", ""]
    for fp in sorted(filepaths):
        lines.append(f"### {fp}")
        lines.append("```python")
        try:
            lines.append(Path(fp).read_text(encoding="utf-8"))
        except Exception as ex:
            lines.append(f"# Error reading file: {ex}")
        lines.append("```")
        lines.append("")
    return lines


def append_markdown_files(content: str, target_dir: Path) -> str:
    """Append top-level markdown files from target directory."""
    md_files: list[Path] = []
    for p in target_dir.glob("*.md"):
        md_files.append(p)
    for p in target_dir.glob("*.MD"):
        md_files.append(p)

    if not md_files:
        return content

    md_lines = ["", "---", "", "## ADDITIONAL FILES (markdown)"]
    for md_path in sorted(md_files):
        md_lines.append("")
        md_lines.append(f"### {md_path.name}")
        md_lines.append("```markdown")
        try:
            md_lines.append(md_path.read_text(encoding="utf-8"))
        except Exception as ex:
            md_lines.append(f"# Error reading file: {ex}")
        md_lines.append("```")

    return content + "\n" + "\n".join(md_lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_sig_pack(filepaths: list[str], dirname: str) -> str:
    groups = group_by_dir(filepaths)
    total = len(filepaths)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    header = "\n".join([
        f"# {dirname} — LLM-READY PACK",
        "",
        "<!-- Generated by gitpack.py (pure Python) -->",
        "",
        "## PACK INFO",
        f"- **Files:** {total} files",
        f"- **Mode:** signatures only",
        f"- **Generated:** {stamp}",
        "",
        "## HOW TO USE",
        "",
        "This is the signatures-only pack. For full implementations, see the",
        "corresponding `_full.md` file.",
        "",
    ])

    return "\n".join([
        header,
        "\n".join(build_signatures_section(filepaths)),
        "\n".join(build_directory_index(filepaths)),
        "\n".join(build_file_index(filepaths)),
    ])


def build_full_pack(filepaths: list[str], dirname: str) -> str:
    groups = group_by_dir(filepaths)
    total = len(filepaths)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    header = "\n".join([
        f"# {dirname} — LLM-READY PACK",
        "",
        "<!-- Generated by gitpack.py (pure Python) -->",
        "",
        "## PACK INFO",
        f"- **Files:** {total} files",
        f"- **Mode:** signatures + full appendix",
        f"- **Generated:** {stamp}",
        "",
        "## HOW TO USE THIS PACK",
        "",
        "1. **SIGNATURE TOC** — scan all file signatures to find relevant code",
        "2. **FILE INDEX** — jump to specific files by name",
        "3. **APPENDIX: FULL IMPLEMENTATIONS** — read full implementation on demand",
        "",
        "For token efficiency: start with the SIGNATURE TOC, pull full code from",
        "the APPENDIX only when you need the implementation details.",
        "",
    ])

    return "\n".join([
        header,
        "\n".join(build_signatures_section(filepaths)),
        "\n".join(build_directory_index(filepaths)),
        "\n".join(build_file_index(filepaths)),
        "\n".join(build_appendix(filepaths)),
    ])


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: gitpack.py <target_dir> [--exclude <patterns>]", file=sys.stderr)
        sys.exit(1)

    target = Path(sys.argv[1]).resolve()
    if not target.is_dir():
        print(f"ERROR: Not a directory: {target}", file=sys.stderr)
        sys.exit(1)

    exclude = ""
    if "--exclude" in sys.argv:
        idx = sys.argv.index("--exclude")
        exclude = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else ""

    name = target.name
    out_dir = target / ".aid" / name
    out_dir.mkdir(parents=True, exist_ok=True)

    py_files = discover_python_files(target, exclude)
    if not py_files:
        print("ERROR: No .py files found", file=sys.stderr)
        sys.exit(1)

    sig_path = out_dir / f"{name}_sig.md"
    full_path = out_dir / f"{name}_full.md"

    sig_content = build_sig_pack(py_files, name)
    sig_content = append_markdown_files(sig_content, target)
    sig_path.write_text(sig_content, encoding="utf-8")

    full_content = build_full_pack(py_files, name)
    full_content = append_markdown_files(full_content, target)
    full_path.write_text(full_content, encoding="utf-8")

    print(f"Signatures: {sig_path} — {len(sig_content):,} chars")
    print(f"Full:       {full_path} — {len(full_content):,} chars")
    print(f"Files: {len(py_files)} Python files")


if __name__ == "__main__":
    main()