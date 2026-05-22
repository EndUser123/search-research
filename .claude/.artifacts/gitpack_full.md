# FULL SOURCE


## scripts\gitpack.py

#!/usr/bin/env python3
"""
Build a two-file gitpack output for a codebase: signatures + full source.

No external AI tools required — uses AST parsing (Python) and direct file reads.

Workflow:
  python gitpack.py <target_dir> [--exclude <patterns>]

Produces two files in .aid/<name>/:
  - <name>_sig.md  — SIGNATURE TOC + DIRECTORY/FILE INDEX (compact, scannable)
  - <name>_full.md — same + APPENDIX with full source read from disk

Target dir is processed directly: files discovered via glob, signatures
extracted via AST (Python) or regex (other languages), appendix read
directly from source. Deterministic output.
"""

import ast
import sys
import re
import glob as glob_module
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Signature extraction — Python
# ---------------------------------------------------------------------------

def extract_py_signatures(filepath: str) -> list[str]:
    """Extract function/class signatures from a Python file via AST."""
    try:
        source = Path(filepath).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
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

    if args.vararg:
        arg_parts.append(f"*{args.vararg.arg}")
    if args.kwarg:
        arg_parts.append(f"**{args.kwarg.arg}")

    return_annotation = _get_function_return_annotation(source, lineno)

    sig = f"{name}({', '.join(arg_parts)})"
    if return_annotation:
        sig += f" -> {return_annotation}"
    return sig


def _get_annotation_str(ann: ast.expr, source: str) -> str:
    """Get the string representation of an annotation from the source."""
    if isinstance(ann, ast.Name):
        return ann.id
    elif isinstance(ann, ast.Attribute):
        parts = []
        node = ann
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
        return ".".join(reversed(parts))
    elif isinstance(ann, ast.Subscript):
        base = _get_annotation_str(ann.value, source)
        if ann.slice:
            slice_str = _get_annotation_str(ann.slice, source)
            return f"{base}[{slice_str}]"
        return base
    elif isinstance(ann, ast.Constant):
        return repr(ann.value)
    elif isinstance(ann, ast.BinOp):
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
            if not stripped.startswith("class "):
                m = re.match(r"(async\s+)?def\s+(\w+)\(.*\)(?:\s*->\s*[^\s:]+)?\s*:", stripped)
                if m:
                    sigs.append(stripped.rstrip(":"))
            else:
                m = re.match(r"class\s+(\w+).*", stripped)
                if m:
                    sigs.append(stripped.rstrip(":"))
    return sigs


# ---------------------------------------------------------------------------
# Signature extraction — generic (non-Python)
# ---------------------------------------------------------------------------

def _remove_fenced_blocks(source: str) -> str:
    """Strip triple-backtick fenced code blocks from source before pattern matching."""
    return re.sub(r"```[^\n]*\n[\s\S]*?```", "", source)


def extract_powershell_signatures(filepath: str) -> list[str]:
    """Extract function/filter/ Workflow signatures from a PowerShell file via regex."""
    try:
        source = Path(filepath).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    sigs: list[str] = []
    seen: set[str] = set()

    # function <name> { ... }
    for m in re.finditer(r"^\s*(?:function|filter|Workflow)\s+([a-zA-Z0-9_-]+)", source, re.MULTILINE):
        line_text = m.group(0).strip()
        if line_text and line_text not in seen and len(sigs) < 100:
            seen.add(line_text)
            sigs.append(line_text)

    # param block: param([type]$Name, ...) at top of script/scriptblock
    for m in re.finditer(r"^\s*param\s*\([^)]*\)", source, re.MULTILINE):
        line_text = m.group(0).strip()
        if line_text and line_text not in seen and len(sigs) < 100:
            seen.add(line_text)
            sigs.append(line_text)

    return sigs


def _get_lang_schema(lang: str) -> str:
    """Return the appropriate regex pattern for a given language."""
    # (?m) must not appear inline — MULTILINE flag is passed at compile time
    schemas = {
        "markdown": (
            r"^#{1,6}\s+(.+)$|"  # headings
            r"^---+\s*$|"           # frontmatter separator
            r"^```\s*$|"            # code fence start
            r"^[ \t]*-[ \t]+(.+)$|"  # YAML list items (indented - key value)
            r"^\w[\w-]*:\s+(?!\s*$)"  # YAML keys (non-empty value)
        ),
        "javascript": (
            r"^(export\s+(default\s+)?(const|let|var|function|async\s+function|class))|"
            r"^(const|let|var)\s+(\w+)\s*=|"
            r"^function\s+(\w+)|"
            r"^async\s+function\s+(\w+)|"
            r"^class\s+(\w+)|"
            r"^export\s+\{[^}]+\}|"
            r"^import\s+.*from\s+['\"]"
        ),
        "typescript": (
            r"^(export\s+(default\s+)?(const|let|var|function|async\s+function|class|interface|type))|"
            r"^(const|let|var)\s+(\w+)\s*:|"
            r"^function\s+(\w+)|"
            r"^async\s+function\s+(\w+)|"
            r"^class\s+(\w+)|"
            r"^interface\s+(\w+)|"
            r"^type\s+(\w+)|"
            r"^export\s+\{[^}]+\}|"
            r"^import\s+.*from\s+['\"]"
        ),
        "html": (
            r"^<!--[\s\S]*?-->|"      # comments
            r"^<script[\s>]|"
            r"^<style[\s>]|"
            r"^<([a-z]+)[\s>]"
        ),
        "css": (
            r"^@[a-z-]+|"             # at-rules
            r"^[.#]?[a-z][\w-]*\s*\{|"
            r"^[a-z][\w-]*\s*:[^;]+;"
        ),
        "sql": (
            r"^(CREATE|ALTER|DROP|SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN)\s+|"
            r"^(TABLE|VIEW|INDEX|PROCEDURE|FUNCTION|TRIGGER)\s+(\w+)|"
            r"^--"
        ),
        "yaml": (
            r"^[\w-]+:\s*(?!\s*$)"
        ),
        "json": (
            r"^\s*\"[^\"]+\"\s*:"
        ),
        "default": (
            r"^(def|class|function|const|let|var|public\s+static|private\s+static)\s+\w+|"
            r"^(export|import)\s+"
        ),
    }
    return schemas.get(lang.lower(), schemas["default"])


def extract_generic_signatures(filepath: str, lang: str = "default") -> list[str]:
    """Extract top-level signatures from a non-Python file via regex."""
    try:
        source = Path(filepath).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return []

    if lang.lower() == "markdown":
        source = _remove_fenced_blocks(source)

    pattern = _get_lang_schema(lang)
    sigs: list[str] = []
    seen: set[str] = set()

    compiled = re.compile(pattern, re.MULTILINE)
    for match in compiled.finditer(source):
        line = source[:match.start()].count("\n") + 1
        line_text = source.splitlines()[line - 1].strip() if line <= len(source.splitlines()) else ""
        if line_text and line_text not in seen and len(sigs) < 100:
            seen.add(line_text)
            sigs.append(line_text)

    return sigs


def extract_signatures(filepath: str) -> list[str]:
    """Dispatch to the correct signature extractor based on file extension."""
    ext = Path(filepath).suffix.lower()
    lang_map = {
        ".py": "python",
        ".pyw": "python",
        ".js": "javascript",
        ".mjs": "javascript",
        ".cjs": "javascript",
        ".jsx": "typescript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".html": "html",
        ".htm": "html",
        ".css": "css",
        ".scss": "css",
        ".sql": "sql",
        ".md": "markdown",
        ".markdown": "markdown",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".json": "json",
    }
    lang = lang_map.get(ext, "default")
    if lang == "python":
        return extract_py_signatures(filepath)
    if lang == "powershell":
        return extract_powershell_signatures(filepath)
    return extract_generic_signatures(filepath, lang)


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

DEFAULT_EXCLUDES = [
    "__pycache__", "*.pyc", "*.pyo", "*.so", "*.dll", "*.exe",
    ".venv", "venv", "env", "site-packages",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox",
    ".git", ".hg", ".svn",
    "dist", "build", "out", "target", "egg-info",
    ".idea", ".vscode", ".DS_Store", "Thumbs.db",
    ".env", ".env.", "*.log", "*.min.js",
    "node_modules",
]

EXTENSIONS = ["*.py", "*.pyw", "*.js", "*.mjs", "*.cjs", "*.jsx", "*.ts", "*.tsx",
              "*.html", "*.htm", "*.css", "*.scss", "*.sql", "*.md", "*.markdown",
              "*.yaml", "*.yml", "*.json", "*.ps1", "*.psm1", "*.psd1"]


def discover_files(target_dir: Path, exclude_patterns: str = "") -> list[str]:
    """Find all supported files in target_dir, excluding patterns."""
    patterns = DEFAULT_EXCLUDES + [p.strip() for p in exclude_patterns.split(",") if p.strip()]

    def is_excluded(path: Path) -> bool:
        path_str = str(path)
        for pattern in patterns:
            if pattern in path_str:
                return True
        return False

    # Track visited (device, inode) pairs to prevent symlink loops
    seen_inodes: set[tuple[int, int]] = set()

    files: list[str] = []
    for pattern in EXTENSIONS:
        for p in target_dir.glob(pattern):
            if is_excluded(p) or p.name.startswith("."):
                continue
            if p.is_symlink():
                continue
            if not p.is_file():
                continue
            try:
                stat = p.stat()
                inode_key = (stat.st_dev, stat.st_ino)
                if inode_key in seen_inodes:
                    continue
                seen_inodes.add(inode_key)
            except OSError:
                continue
            resolved = p.resolve()
            # Skip files that resolve outside target_dir (symlinks to other trees)
            try:
                resolved.relative_to(target_dir.resolve())
            except ValueError:
                continue
            files.append(str(resolved))

    return sorted(files)


# ---------------------------------------------------------------------------
# Markdown building
# ---------------------------------------------------------------------------

LANG_LABEL = {
    ".py": "python", ".pyw": "python",
    ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".jsx": "typescript", ".ts": "typescript", ".tsx": "typescript",
    ".html": "html", ".htm": "html",
    ".css": "css", ".scss": "css",
    ".sql": "sql",
    ".md": "markdown", ".markdown": "markdown",
    ".yaml": "yaml", ".yml": "yaml",
    ".json": "json",
    ".ps1": "powershell", ".psm1": "powershell", ".psd1": "powershell",
}


def build_signatures_section(filepaths: list[str]) -> list[str]:
    lines = ["## SIGNATURE TOC", ""]
    for fp in filepaths:
        sigs = extract_signatures(fp)
        ext = Path(fp).suffix.lower()
        lang = LANG_LABEL.get(ext, "text")
        lines.append(f"### {fp}")
        lines.append(f"```{lang}")
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


def build_tree(filepaths: list[str], target_dir: Path) -> list[str]:
    """Build a visual directory tree with file counts per folder."""
    tree: dict = {}
    for fp in filepaths:
        rel = Path(fp).relative_to(target_dir)
        parts = rel.parts
        node = tree
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = None

    def count_leaves(d: dict) -> int:
        return sum(1 if v is None else count_leaves(v) for v in d.values())

    total = count_leaves(tree)
    lines: list[str] = [f"{target_dir.name}/ ({total} files)"]
    MAX = 200
    truncated = False

    def render(d: dict, prefix: str) -> None:
        nonlocal truncated
        if truncated:
            return
        dirs = sorted([(k, v) for k, v in d.items() if isinstance(v, dict)])
        files = sorted([k for k, v in d.items() if v is None])
        items = [(n, v) for n, v in dirs] + [(f, None) for f in files]

        for i, (name, children) in enumerate(items):
            if len(lines) >= MAX:
                remaining = len(items) - i
                lines.append(f"{prefix}... ({remaining} more)")
                truncated = True
                return
            is_last = i == len(items) - 1
            c = "└── " if is_last else "├── "
            if children is None:
                lines.append(f"{prefix}{c}{name}")
            else:
                n = count_leaves(children)
                lines.append(f"{prefix}{c}{name}/ ({n})")
                ext = "    " if is_last else "│   "
                render(children, prefix + ext)

    render(tree, "")

    out = ["## DIRECTORY TREE", "", "```"]
    out.extend(lines)
    out.append("```")
    if truncated:
        out.append(f"\n> Truncated at {MAX} lines. See FILE INDEX for complete listing.")
    return out


def build_file_index(files: list[str]) -> list[str]:
    lines = ["", "## FILE INDEX", "", "| File | Language | Description |", "|------|-------------|"]
    for filepath in sorted(files):
        name = Path(filepath).stem
        parts = filepath.replace("\\", "/").split("/")
        ext = Path(filepath).suffix.lower()
        lang = LANG_LABEL.get(ext, "text")
        if name in ("__init__", "index", "main"):
            desc = f"Package: {parts[-2]}" if len(parts) > 1 else filepath
        else:
            desc = name.replace("_", " ").replace("-", " ")
        lines.append(f"| `{filepath}` | {lang} | {desc} |")
    return lines


def build_appendix(filepaths: list[str]) -> list[str]:
    lines = ["", "---", "", "## APPENDIX: FULL IMPLEMENTATIONS", ""]
    for fp in sorted(filepaths):
        ext = Path(fp).suffix.lower()
        lang = LANG_LABEL.get(ext, "text")
        lines.append(f"### {fp}")
        lines.append(f"```{lang}")
        try:
            lines.append(Path(fp).read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            lines.append(f"# <binary file — skipped>")
        except OSError as ex:
            lines.append(f"# Error reading file: {ex}")
        lines.append("```")
        lines.append("")
    return lines


def append_markdown_files(content: str, target_dir: Path, included_filepaths: list[str] | None = None) -> str:
    """Append top-level markdown files from target directory, skipping already-included files."""
    md_files: list[Path] = []
    for p in target_dir.glob("*.md"):
        md_files.append(p)
    for p in target_dir.glob("*.MD"):
        md_files.append(p)

    if not md_files:
        return content

    # Skip markdown files already included in the appendix (identified by filename match)
    skip_names: set[str] = set()
    if included_filepaths:
        for fp in included_filepaths:
            skip_names.add(Path(fp).name.lower())

    md_lines = ["", "---", "", "## ADDITIONAL FILES (markdown)"]
    for md_path in sorted(md_files):
        if md_path.name.lower() in skip_names:
            continue
        md_lines.append("")
        md_lines.append(f"### {md_path.name}")
        md_lines.append("```markdown")
        try:
            md_lines.append(md_path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            md_lines.append(f"# <binary file — skipped>")
        except OSError as ex:
            md_lines.append(f"# Error reading file: {ex}")
        md_lines.append("```")

    if len(md_lines) == 5:  # only the header was added, nothing to append
        return content

    return content + "\n" + "\n".join(md_lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_sig_pack(filepaths: list[str], dirname: str, target_dir: Path) -> str:
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
        "\n".join(build_tree(filepaths, target_dir)),
        "\n".join(build_file_index(filepaths)),
    ])


def build_full_pack(filepaths: list[str], dirname: str) -> str:
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

    files = discover_files(target, exclude)
    if not files:
        print("ERROR: No supported files found", file=sys.stderr)
        sys.exit(1)

    sig_path = out_dir / f"{name}_sig.md"
    full_path = out_dir / f"{name}_full.md"

    sig_content = build_sig_pack(files, name, target)
    sig_content = append_markdown_files(sig_content, target, files)
    sig_path.write_text(sig_content, encoding="utf-8")

    full_content = build_full_pack(files, name)
    full_content = append_markdown_files(full_content, target, files)
    full_path.write_text(full_content, encoding="utf-8")

    print(f"Signatures: {sig_path} — {len(sig_content):,} chars")
    print(f"Full:       {full_path} — {len(full_content):,} chars")
    print(f"Files: {len(files)} files")


if __name__ == "__main__":
    main()


## scripts\gitpack_structured.py

#!/usr/bin/env python3
"""
Build a two-file gitpack output: signatures-only + full implementations.

Workflow:
  1. Run aid --quick  → signatures-only output
  2. python gitpack_structured.py <sig_output.md> <dirname> [target_dir]

Produces two files:
  - <name>_sig.md  — SIGNATURE TOC + DIRECTORY/FILE INDEX (small, scannable)
  - <name>_full.md — same + APPENDIX with full source code read from disk

Source files are read directly from disk for the APPENDIX to avoid aid's
markdown corruption.
"""

import re
import sys
import glob as glob_module
from datetime import datetime, timezone
from pathlib import Path


def parse_aid_output(content: str) -> dict[str, dict[str, str]]:
    """Parse aid output into {filepath: {"sig": "...", "body": "..."}}.

    Each file section looks like:
        ### path/to/file.py

        ```python
        ...code...
        ```
    """
    # Match "### path/to/file.py" at start of line
    file_pattern = re.compile(r"^###\s+(.+?\.\w+)\s*$", re.MULTILINE)

    sections: dict[str, dict[str, str]] = {}
    matches = list(file_pattern.finditer(content))

    for i, m in enumerate(matches):
        filepath = m.group(1).strip()
        # Content starts after the header line
        start = m.end() + 1  # skip the newline
        # End is start of next header, or end of file
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        section_text = content[start:end].strip()
        sections[filepath] = {"raw": section_text}
    return sections


def append_markdown_files(content: str, target_dir: str) -> str:
    """Append markdown files from target directory as additional sections.

    aid does not process .md files, so they must be appended raw after structuring.
    """
    md_files = []
    for pattern in ["*.md", "*.MD"]:
        md_files.extend(glob_module.glob(str(Path(target_dir) / pattern)))

    if not md_files:
        return content

    md_lines = ["", "---", "", "## ADDITIONAL FILES (markdown)"]
    for md_path in sorted(md_files):
        # Skip SKILL.md in subdirectories (only include top-level)
        rel = Path(md_path).resolve().relative_to(Path(target_dir).resolve())
        if len(rel.parts) > 1:
            continue  # skip subdir markdown (likely README in subdir)
        md_lines.append("")
        md_lines.append(f"### {rel}")
        md_lines.append("```markdown")
        try:
            text = Path(md_path).read_text(encoding="utf-8")
            md_lines.append(text)
        except Exception as ex:
            md_lines.append(f"# Error reading file: {ex}")
        md_lines.append("```")

    return content + "\n" + "\n".join(md_lines)


def extract_signature(filepath: str, raw_section: str) -> str:
    """Extract the signature portion from a raw aid section.

    For --quick mode output: section IS the signature - just extract clean code block.
    For full mode: need to extract def/class/async def lines before implementation body.
    """
    lines = raw_section.splitlines()
    sig_lines = []
    in_code = False
    brace_depth = 0
    has_def_lines = False

    # Pre-check: does this look like full mode (has def/class lines)?
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("def ") or stripped.startswith("class ") or stripped.startswith("async def "):
            has_def_lines = True
            break

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            if stripped.startswith("```python") or stripped.startswith("```"):
                in_code = True
            else:
                in_code = False
            continue
        if not in_code:
            continue

        if has_def_lines:
            # Full mode: collect def/class/async def lines + imports
            if any(stripped.startswith(kw) for kw in ["def ", "class ", "async def "]):
                sig_lines.append(line)
            elif stripped.startswith("import ") or stripped.startswith("from "):
                sig_lines.append(line)
            elif sig_lines:
                # Stop at first non-def, non-import, non-annotation after signatures start
                if not stripped.endswith(":") and not stripped.startswith("@") and not stripped.startswith('"""'):
                    # Likely implementation body
                    break
        else:
            # --quick mode: collect all signature lines (look like "func(args) -> type")
            if stripped.startswith("import ") or stripped.startswith("from "):
                continue  # skip imports
            if "(" in stripped or "->" in stripped:
                sig_lines.append(line)

    return "\n".join(sig_lines).strip()


def group_by_dir(files: list[str]) -> dict[str, list[str]]:
    """Group files by top-level directory."""
    groups: dict[str, list[str]] = {}
    for filepath in files:
        parts = filepath.replace("\\", "/").split("/")
        top = parts[0] if parts else filepath
        groups.setdefault(top, []).append(filepath)
    return groups


def _build_header(dirname: str, total: int, mode: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return "\n".join([
        f"# {dirname} — LLM-READY PACK",
        "",
        "<!-- Generated by gitpack_structured.py -->",
        "",
        "## PACK INFO",
        f"- **Files:** {total} files",
        f"- **Mode:** {mode}",
        f"- **Generated:** {stamp}",
        "",
    ])


def _build_toc(sig_sections: dict) -> list[str]:
    lines = ["## SIGNATURE TOC", ""]
    for filepath in sorted(sig_sections):
        sig = extract_signature(filepath, sig_sections.get(filepath, {}).get("raw", ""))
        lines.append(f"### {filepath}")
        lines.append("```python")
        lines.append(sig)
        lines.append("```")
        lines.append("")
    return lines


def _build_indexes(all_files: list[str]) -> tuple[list[str], list[str]]:
    groups = group_by_dir(all_files)
    dir_lines = ["## DIRECTORY INDEX", "", "| Directory | Files |", "|---------|-------|"]
    for dir_name in sorted(groups):
        dir_lines.append(f"| `{dir_name}/` | {len(groups[dir_name])} |")

    file_lines = ["", "## FILE INDEX", "", "| File | Description |", "|------|-------------|"]
    for filepath in sorted(all_files):
        name = Path(filepath).stem
        parts = filepath.replace("\\", "/").split("/")
        if name in ("__init__", "index", "main"):
            desc = f"Package: {parts[0]}" if len(parts) > 1 else filepath
        else:
            desc = name.replace("_", " ").replace("-", " ")
        file_lines.append(f"| `{filepath}` | {desc} |")
    return dir_lines, file_lines


def _lang_for(filepath: str) -> str:
    ext = Path(filepath).suffix.lower()
    return {
        ".py": "python", ".pyw": "python",
        ".js": "javascript", ".mjs": "javascript", ".cjs": "javascript",
        ".jsx": "typescript", ".ts": "typescript", ".tsx": "typescript",
        ".html": "html", ".htm": "html",
        ".css": "css", ".scss": "css",
        ".sql": "sql",
        ".md": "markdown", ".markdown": "markdown",
        ".yaml": "yaml", ".yml": "yaml",
        ".json": "json",
    }.get(ext, "text")


def _build_appendix(all_files: list[str], full_sections: dict) -> list[str]:
    lines = ["", "---", "", "## APPENDIX: FULL IMPLEMENTATIONS", ""]
    for filepath in sorted(all_files):
        source_path = Path(filepath)
        if source_path.exists():
            raw = source_path.read_text(encoding="utf-8")
        else:
            raw = full_sections.get(filepath, {}).get("raw", f"# {filepath}\n# (not found)")
        lang = _lang_for(filepath)
        lines.append(f"### {filepath}")
        lines.append(f"```{lang}")
        lines.append(raw)
        lines.append("```")
        lines.append("")
    return lines


def build_sig_pack(sig_sections: dict, dirname: str) -> str:
    """Signatures-only pack: TOC + indexes. No implementations."""
    all_files = list(sig_sections.keys())
    total = len(all_files)
    dir_lines, file_lines = _build_indexes(all_files)
    return "\n".join([
        _build_header(dirname, total, "signatures only"),
        "",
        "## HOW TO USE",
        "",
        "This is the signatures-only pack. For full implementations, see the",
        "corresponding `_full.md` file.",
        "",
        "\n".join(_build_toc(sig_sections)),
        "\n".join(dir_lines),
        "\n".join(file_lines),
    ])


def build_full_pack(sig_sections: dict, full_sections: dict, dirname: str) -> str:
    """Full pack: TOC + indexes + appendix with full source."""
    all_files = list(sig_sections.keys())
    total = len(all_files)
    dir_lines, file_lines = _build_indexes(all_files)
    return "\n".join([
        _build_header(dirname, total, "signatures + full appendix"),
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
        "\n".join(_build_toc(sig_sections)),
        "\n".join(dir_lines),
        "\n".join(file_lines),
        "\n".join(_build_appendix(all_files, full_sections)),
    ])


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: gitpack_structured.py <sig_output.md> <dirname> [target_dir]", file=sys.stderr)
        sys.exit(1)

    sig_path = Path(sys.argv[1])
    dirname = sys.argv[2]
    target_dir = sys.argv[3] if len(sys.argv) > 3 else dirname

    if not sig_path.exists():
        print(f"ERROR: Signature file not found: {sig_path}", file=sys.stderr)
        sys.exit(1)

    sig_content = sig_path.read_text(encoding="utf-8")
    sig_sections = parse_aid_output(sig_content)

    sig_count = len(sig_sections)
    if sig_count == 0:
        print("WARNING: No file signatures found in --quick output", file=sys.stderr)
        sys.exit(1)

    # Derive full pack path: _sig.md → _full.md
    full_path = sig_path.parent / sig_path.name.replace("_sig.", "_full.")

    # Build and write signatures-only pack
    sig_pack = build_sig_pack(sig_sections, dirname)
    sig_pack = append_markdown_files(sig_pack, target_dir)
    sig_path.write_text(sig_pack, encoding="utf-8")

    # Build and write full pack (signatures + appendix)
    full_pack = build_full_pack(sig_sections, {}, dirname)
    full_pack = append_markdown_files(full_pack, target_dir)
    full_path.write_text(full_pack, encoding="utf-8")

    source_reads = sum(1 for f in sig_sections if Path(f).exists())
    print(f"Sig pack:  {sig_path} — {len(sig_pack):,} chars")
    print(f"Full pack: {full_path} — {len(full_pack):,} chars")
    print(f"Files: {sig_count} ({source_reads} from source)")


if __name__ == "__main__":
    main()


## scripts\gitpack_toc.py

#!/usr/bin/env python3
"""Prepend a structured TOC/index to an aid distillation output."""

import re
import sys
from datetime import datetime, timezone
from pathlib import Path


def extract_files(content: str) -> list[tuple[str, str]]:
    """Extract (filepath, description) pairs from aid output.

    Each file in aid output looks like:
        ### P:\\\\\\\path\\to\\file.py

        ```python
        ...code...
        ```
    """
    pattern = r"^### (.+?\.(?:py|ts|js|go|rs|java|cs|kt|cpp|c|h|php|rb|swift))$"
    files: list[tuple[str, str]] = []
    for line in content.splitlines():
        m = re.match(pattern, line.strip())
        if m:
            filepath = m.group(1).strip()
            # Build a description from the first non-empty line after the header
            files.append((filepath, _describe_file(filepath)))
    return files


def _describe_file(filepath: str) -> str:
    """Infer a brief description from the filepath."""
    name = Path(filepath).stem
    parts = filepath.split("\\")[-1].split("/")[-2:]
    if name in ("__init__", "index", "main"):
        return f"Package: {parts[0]}" if len(parts) > 1 else filepath
    return name.replace("_", " ").replace("-", " ")


def group_by_dir(files: list[tuple[str, str]]) -> dict[str, list[str]]:
    """Group files by top-level directory."""
    groups: dict[str, list[str]] = {}
    for filepath, desc in files:
        parts = filepath.replace("\\", "/").split("/")
        top = parts[0] if parts else filepath
        groups.setdefault(top, []).append(filepath)
    return groups


def build_toc(files: list[tuple[str, str]], dirname: str, mode: str) -> str:
    """Build the TOC section."""
    groups = group_by_dir(files)
    total = len(files)

    lines = [
        f"# {dirname} — LLM-READY PACK",
        "",
        "<!-- TOC is prepended by gitpack_toc.py -->",
        "",
        "## PACK INFO",
        f"- **Files:** {total} files distilled",
        f"- **Mode:** {mode}",
        f"- **Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## HOW TO USE THIS PACK",
        "",
        "This file is organized by directory. Use your LLM's search or jump-to-section",
        "to find the relevant code. Each `### path/to/file.py` header is a jump anchor.",
        "",
        "For token efficiency: read only the sections relevant to your task.",
        "",
        "## DIRECTORY INDEX",
        "",
        "| Directory | Files |",
        "|---------|-------|",
    ]

    for dir_name in sorted(groups.keys()):
        lines.append(f"| `{dir_name}/` | {len(groups[dir_name])} |")

    lines += [
        "",
        "## FILE INDEX",
        "",
        "| File | Description |",
        "|------|-------------|",
    ]

    for filepath, desc in sorted(files, key=lambda x: x[0]):
        lines.append(f"| `{filepath}` | {desc} |")

    lines += [
        "",
        "---",
        "",
    ]

    return "\n".join(lines)


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: gitpack_toc.py <aid_output.md> <dirname> [mode]", file=sys.stderr)
        sys.exit(1)

    aid_output = Path(sys.argv[1])
    dirname = sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else "full fidelity"

    content = aid_output.read_text(encoding="utf-8")
    files = extract_files(content)

    if not files:
        print("WARNING: No files found in aid output — TOC may be empty", file=sys.stderr)
        toc = build_toc([], dirname, mode)
    else:
        toc = build_toc(files, dirname, mode)

    # Prepend TOC to content
    new_content = toc + "\n" + content

    aid_output.write_text(new_content, encoding="utf-8")

    total = len(files)
    print(f"TOC prepended: {total} files indexed in {len(content)} chars of content")


if __name__ == "__main__":
    main()
