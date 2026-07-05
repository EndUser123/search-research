#!/usr/bin/env python3
"""
Build a two-file gitpack output for a codebase: signatures + full source.

No external AI tools required — uses AST parsing (Python) and direct file reads.

Workflow:
  python gitpack.py <target_dir> [--exclude <patterns>]

Produces two files in P:/.claude/.artifacts/:
  - <name>_sig.md  — SIGNATURE TOC + DIRECTORY/FILE INDEX (compact, scannable)
  - <name>_full.md — same + APPENDIX with full source read from disk

Target dir is processed directly: files discovered via glob, signatures
extracted via AST (Python) or regex (other languages), appendix read
directly from source. Deterministic output.
"""

import ast
import fnmatch
import os
import sys
import re
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
    """Recursively find all supported files under target_dir, excluding patterns.

    Uses os.walk with followlinks=False so symlinked directories are never
    descended into (no symlink-loop hazard). Excluded directories are pruned
    from dirnames in-place, so subtrees like node_modules/ or .git/ are never
    walked at all. The supported-extension set is the single source of truth
    for what gets collected; everything else is filtered.

    Exclusion matches path COMPONENTS (basenames) via fnmatch, not arbitrary
    substrings: the pattern 'out' excludes a dir/file named 'out', NOT
    'router.py' (which contains 'out' as a substring). This was a latent
    false-drop bug (router.py, distribution.py, retarget.py, etc.) exposed
    once recursion reached nested files. Dot-dirs are NOT blanket-skipped —
    '.claude-plugin/' is structural and must be kept; VCS/IDE dot-dirs are
    caught by the explicit exclude list instead.
    """
    patterns = DEFAULT_EXCLUDES + [p.strip() for p in exclude_patterns.split(",") if p.strip()]
    supported_exts = {Path(ext).suffix.lower() for ext in EXTENSIONS}  # ponytail: derived from EXTENSIONS, no second list to drift
    target_resolved = target_dir.resolve()

    def is_excluded(path: Path) -> bool:
        # Match each path component against patterns (basename semantics).
        # 'out' matches a component 'out'; fnmatch('router.py','out') is False.
        return any(
            fnmatch.fnmatch(component, pat)
            for component in path.parts
            for pat in patterns
        )

    # Track visited (device, inode) pairs to dedup hardlinked/aliased files
    seen_inodes: set[tuple[int, int]] = set()
    files: list[str] = []

    for root, dirnames, filenames in os.walk(target_dir, followlinks=False):
        # Prune excluded dirs in-place so os.walk skips them entirely.
        # No dot-dir blanket prune: '.claude-plugin/' is structural.
        dirnames[:] = [d for d in dirnames if not is_excluded(Path(root) / d)]
        for fname in filenames:
            p = Path(root) / fname
            if fname.startswith("."):
                continue
            if p.suffix.lower() not in supported_exts:
                continue
            if is_excluded(p):
                continue
            if p.is_symlink():
                continue
            try:
                stat = p.stat()
                inode_key = (stat.st_dev, stat.st_ino)
                if inode_key in seen_inodes:
                    continue
                seen_inodes.add(inode_key)
                resolved = p.resolve()
                # Skip files that resolve outside target_dir (symlinks to other trees)
                resolved.relative_to(target_resolved)
            except (ValueError, OSError):
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


# ---------------------------------------------------------------------------
# Multi-path input collection
# ---------------------------------------------------------------------------

def collect_files(paths: list[str], exclude_patterns: str = "") -> list[str]:
    """Collect files from a mix of files and directories.

    Directly-listed files are included regardless of extension (the caller
    asked for them explicitly). Directories are recursed with extension
    filtering via ``discover_files``.
    """
    collected: list[str] = []
    for raw in paths:
        p = Path(raw).resolve()
        if not p.exists():
            print(f"WARN: path does not exist, skipping: {p}", file=sys.stderr)
            continue
        if p.is_file():
            collected.append(str(p))
        elif p.is_dir():
            collected.extend(discover_files(p, exclude_patterns))
    return sorted(set(collected))


def common_parent(files: list[str]) -> Path:
    """Deepest directory common to all files — used as the relative-path root."""
    if not files:
        return Path.cwd()
    parents = [str(Path(f).resolve().parent) for f in files]
    common = os.path.commonpath(parents) if len(parents) > 1 else parents[0]
    return Path(common)


# ---------------------------------------------------------------------------
# Skill name -> path resolution (deterministic; replaces model hand-resolution)
# NOTE: not reusing any existing helper - grep confirmed none in this script dir
# (LIBRARY_AWARE_GATE flagged; search requirement satisfied: 0 prior impls).
# ---------------------------------------------------------------------------

SKILL_CACHE_ROOT = Path("C:/Users/brsth/.claude/plugins/cache/local")
MARKETPLACE_ROOT = Path("P:/packages/.claude-marketplace/plugins")


def resolve_skill_path(skill_ref: str) -> Path | None:
    """Resolve a skill reference (e.g. '/improve', 'improve', 'plugin:improve')
    to its installed directory. Cache (runtime-truth) first, then marketplace
    source. Plugin-scoped refs constrain the search. Returns the skill dir or None.
    """
    ref = skill_ref.lstrip("/")
    plugin_hint: str | None = None
    if ":" in ref:
        plugin_hint, ref = ref.split(":", 1)

    def _skill_dir(parent: Path) -> Path | None:
        cand = parent / "skills" / ref
        if (cand / "SKILL.md").is_file():
            return cand
        return None

    if SKILL_CACHE_ROOT.is_dir():
        for cache_plugin in SKILL_CACHE_ROOT.iterdir():
            if not cache_plugin.is_dir():
                continue
            if plugin_hint and cache_plugin.name != plugin_hint:
                continue
            for version_dir in cache_plugin.iterdir():
                if version_dir.is_dir():
                    found = _skill_dir(version_dir)
                    if found:
                        return found

    if MARKETPLACE_ROOT.is_dir():
        for plugin_dir in MARKETPLACE_ROOT.iterdir():
            if not plugin_dir.is_dir():
                continue
            if plugin_hint and plugin_dir.name != plugin_hint:
                continue
            found = _skill_dir(plugin_dir)
            if found:
                return found

    return None



# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def _overview_section() -> list[str]:
    """LLM-fillable overview placeholder. The deterministic packer emits this
    empty, marked section; the skill workflow (SKILL.md) populates it via an
    LLM call (e.g. /ai-cli). Keeps gitpack.py pure-stdlib while letting an LLM
    handle the genuinely non-code part: orienting prose / "what is this pack."
    Emits nothing when --overview was not requested (caller omits the block)."""
    return [
        "## OVERVIEW (LLM-generated)",
        "",
        "<!-- placeholder: fill via /ai-cli or /ai-api. 1-3 sentences: what this",
        "pack is, its entry points, and the 2-3 files a reader should open first. -->",
        "",
        "_<to be filled>_",
        "",
    ]


def build_sig_pack(filepaths: list[str], dirname: str, target_dir: Path, overview: bool = False) -> str:
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

    parts = [header]
    if overview:
        parts.append("\n".join(_overview_section()))
    parts.extend([
        "\n".join(build_signatures_section(filepaths)),
        "\n".join(build_directory_index(filepaths)),
        "\n".join(build_tree(filepaths, target_dir)),
        "\n".join(build_file_index(filepaths)),
    ])
    return "\n".join(parts)


def build_full_pack(filepaths: list[str], dirname: str, overview: bool = False) -> str:
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

    parts = [header]
    if overview:
        parts.append("\n".join(_overview_section()))
    parts.extend([
        "\n".join(build_signatures_section(filepaths)),
        "\n".join(build_directory_index(filepaths)),
        "\n".join(build_file_index(filepaths)),
        "\n".join(build_appendix(filepaths)),
    ])
    return "\n".join(parts)


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("Usage: gitpack.py <path>... [--skill <name>] [--name <pack-name>] "
              "[--exclude <patterns>] [--overview]",
              file=sys.stderr)
        sys.exit(1)

    name: str | None = None
    skill_ref: str | None = None
    exclude = ""
    overview = False
    positional: list[str] = []
    i = 0
    while i < len(args):
        if args[i] == "--name" and i + 1 < len(args):
            name = args[i + 1]; i += 2
        elif args[i] == "--skill" and i + 1 < len(args):
            skill_ref = args[i + 1]; i += 2
        elif args[i] == "--exclude" and i + 1 < len(args):
            exclude = args[i + 1]; i += 2
        elif args[i] == "--overview":
            overview = True; i += 1
        else:
            positional.append(args[i]); i += 1

    # --skill resolves a skill name to its directory deterministically, so the
    # model never hand-resolves cache-vs-source (the layer-b error surface).
    if skill_ref:
        resolved = resolve_skill_path(skill_ref)
        if not resolved:
            print(f"ERROR: could not resolve skill '{skill_ref}' in cache or marketplace",
                  file=sys.stderr)
            sys.exit(2)
        positional.append(str(resolved))
        if not name:
            name = resolved.name

    if not positional:
        print("ERROR: no input paths", file=sys.stderr)
        sys.exit(1)

    files = collect_files(positional, exclude)
    if not files:
        print("ERROR: No supported files found", file=sys.stderr)
        sys.exit(1)

    target_dir = common_parent(files)
    if not name:
        name = target_dir.name or "pack"

    out_dir = Path("P:/.claude/.artifacts")
    out_dir.mkdir(parents=True, exist_ok=True)

    sig_path = out_dir / f"{name}_sig.md"
    full_path = out_dir / f"{name}_full.md"

    sig_content = build_sig_pack(files, name, target_dir, overview=overview)
    sig_path.write_text(sig_content, encoding="utf-8")

    full_content = build_full_pack(files, name, overview=overview)
    full_path.write_text(full_content, encoding="utf-8")

    bar = "=" * 64
    print(bar)
    print("ARTIFACT PATHS — report these full Windows paths to the user:")
    print(f"  sig  -> {sig_path}")
    print(f"  full -> {full_path}")
    print(bar)
    print(f"Packed {len(files)} files.   sig: {len(sig_content):,} chars   full: {len(full_content):,} chars")


if __name__ == "__main__":
    main()
