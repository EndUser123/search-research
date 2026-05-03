#!/usr/bin/env python3
"""gitpack for doc-compiler skill."""
import ast
from pathlib import Path

TARGET = Path("P:/packages/cc-skills-meta/skills/doc-compiler")
OUT_DIR = Path("P:/.claude/.artifacts")
NAME = "doc-compiler"

EXCLUDE = {
    "__pycache__", ".pyc", ".pyo", ".so", ".dll", ".exe",
    ".venv", "venv", "env", "site-packages",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", ".tox",
    ".git", ".hg", ".svn",
    "dist", "build", "out", "target", "egg-info",
    ".idea", ".vscode", ".DS_Store", "Thumbs.db",
    ".env", ".log",
}


def should_exclude(p: Path) -> bool:
    parts = p.parts
    name = p.name
    for exc in EXCLUDE:
        if exc in name or exc in parts:
            return True
    return False


def get_signature(file_path: Path) -> str:
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except Exception:
        return ""
    sigs = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            args = [a.arg for a in node.args.args]
            ret = ast.unparse(node.returns) if node.returns else ""
            sigs.append(f"def {node.name}({','.join(args)}) -> {ret}")
        elif isinstance(node, ast.ClassDef):
            methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
            sigs.append(f"class {node.name}({','.join(methods) if methods else '# no methods'})")
    return "\n".join(sigs)


py_files = []
for p in TARGET.rglob("*.py"):
    if should_exclude(p):
        continue
    py_files.append(p.relative_to(TARGET))

md_files = list(TARGET.glob("*.md"))

sig_lines = [f"# {NAME}_sig.md", f"## PACK INFO", f"Target: {TARGET}", f"Files: {len(py_files)}", "", f"## SIGNATURE TOC", ""]
for p in sorted(py_files):
    sigs = get_signature(TARGET / p)
    sig_lines.append(f"### {p}")
    if sigs:
        for s in sigs.split("\n"):
            sig_lines.append(f"  {s}")
    else:
        sig_lines.append("  (no top-level def/class)")
    sig_lines.append("")

sig_lines += ["", "## DIRECTORY INDEX", ""]
sig_lines.append("| Path | Type |")
sig_lines.append("|------|------|")
for p in sorted(py_files):
    size = (TARGET / p).stat().st_size
    sig_lines.append(f"| {p} | .py ({size}b) |")
for p in sorted(md_files):
    size = p.stat().st_size
    sig_lines.append(f"| {p.name} | .md ({size}b) |")

full_lines = sig_lines + ["", "## FULL IMPLEMENTATIONS", ""]
for p in sorted(py_files):
    full_lines.append(f"### {p}")
    full_lines.append("```python")
    try:
        full_lines.append((TARGET / p).read_text(encoding="utf-8"))
    except Exception:
        full_lines.append("(read error)")
    full_lines.append("```")
    full_lines.append("")

OUT_DIR.mkdir(parents=True, exist_ok=True)
(OUT_DIR / f"{NAME}_sig.md").write_text("\n".join(sig_lines), encoding="utf-8")
(OUT_DIR / f"{NAME}_full.md").write_text("\n".join(full_lines), encoding="utf-8")
print(f"Written: {OUT_DIR}/{NAME}_sig.md  ({len(py_files)} py, {len(md_files)} md)")
print(f"Written: {OUT_DIR}/{NAME}_full.md")
