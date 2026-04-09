"""File Immediate Read — UserPromptSubmit hook that reads file paths before reasoning.

Detects file paths in the user's prompt and reads the file contents immediately,
injecting them into context before any reasoning or response generation.

This prevents semantic satisficing — substituting a plausible reconstruction
for direct file reading when the file path is the subject of the question.

Trigger conditions:
  - Prompt contains a file path (Windows absolute, relative, or ~-prefixed)
  - File exists and is readable
  - File is NOT already fully contained in prompt context

Anti-sycophancy rationale: "file path in prompt" = "read immediately" = "reason from contents"
rather than "reason from label" (filename matching against loaded context).
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from .base import HookContext, HookResult
from .registry import register_hook

# File size limit: 500KB max (same threshold as Gemini CLI stdin piping)
_MAX_FILE_SIZE = 500 * 1024

# Patterns for Windows and Unix file paths
_PATH_PATTERNS = [
    # Windows absolute: C:\... or P:\...
    # Trailing \b ensures we stop at word boundary (e.g. space after .md)
    re.compile(r"\b([A-Za-z]:[^\s<>|\"]+)\b"),
    # Unix absolute: /home/, /Users/, /mnt/, /tmp/
    # Group 1 = prefix with trailing slash, Group 2 = remainder (includes / chars)
    re.compile(r"(?:^|(?<=\s))(/home/|/Users/|/mnt/|/tmp/|/var/|/opt/)([^\s<>|\"]+)"),
    # Tilde expansion: ~/
    re.compile(r"(?:^|(?<=\s))(~/[^\s<>|\"]+)"),
    # Relative paths with extension: ./foo.py, ../bar.md, src/main.ts
    re.compile(r"(?:\.\./|\./)[^\s<>|\"]+\.[a-zA-Z0-9]{1,10}"),
]

# Extensions that indicate code/doc files (readable text)
_READABLE_EXTENSIONS = frozenset({
    ".py", ".md", ".txt", ".yaml", ".yml", ".json", ".toml", ".ini", ".cfg",
    ".sh", ".bash", ".ps1", ".bat", ".cmd", ".sql", ".html", ".css", ".js",
    ".ts", ".tsx", ".jsx", ".go", ".rs", ".java", ".c", ".cpp", ".h",
    ".hpp", ".cs", ".rb", ".php", ".swift", ".kt", ".scala", ".lua",
    ".r", ".m", ".mm", ".F", ".f", ".for", ".v", ".vhd", ".vhdl",
    ".pkl", ".pickle", ".csv", ".tsv", ".xml", ".env", ".gitignore",
    ".dockerignore", ".editorconfig", ".prettierrc", ".eslintrc",
})

# Binary/non-readable extensions to skip
_BINARY_EXTENSIONS = frozenset({
    ".exe", ".dll", ".so", ".dylib", ".bin", ".o", ".a", ".obj",
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg", ".webp",
    ".mp3", ".mp4", ".avi", ".mov", ".mkv", ".wav", ".flac",
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".pyc", ".pyo", ".pyw", ".class", ".jar", ".war",
    ".db", ".sqlite", ".sqlite3", ".mdf", ".ldf",
    ".ttf", ".otf", ".woff", ".woff2", ".eot",
})


def _extract_paths(text: str) -> list[str]:
    """Extract all plausible file paths from text."""
    paths = []
    for pattern in _PATH_PATTERNS:
        for match in pattern.finditer(text):
            groups = match.groups()
            if len(groups) == 2:
                # Two-group pattern: concat prefix + remainder
                path = groups[0] + groups[1]
            else:
                path = groups[0] if groups else match.group(0)
            # Normalize ~ to home directory
            if path.startswith("~"):
                path = os.path.expanduser(path)
            paths.append(path)
    return paths


def _is_readable_file(path: str) -> bool:
    """Check if path points to a readable text file."""
    p = Path(path)
    if not p.exists() or not p.is_file():
        return False
    suffix = p.suffix.lower()
    if suffix in _BINARY_EXTENSIONS:
        return False
    if suffix and suffix not in _READABLE_EXTENSIONS:
        if suffix:
            return False
    return True


def _expand_path(path: str) -> Path | None:
    """Resolve path, handling relative and absolute forms."""
    p = Path(path)
    if not p.exists():
        # Try relative to P: drive (common workspace)
        p_p = Path("P:") / path
        if p_p.exists():
            return p_p.resolve()
        # Try relative to current dir
        p_cwd = Path.cwd() / path
        if p_cwd.exists():
            return p_cwd.resolve()
        return None
    return p.resolve()


@register_hook("file_immediate_read", priority=9.5)
def file_immediate_read(context: HookContext) -> HookResult:
    """Detect file paths in prompt and read their contents before reasoning.

    Priority 9.5 — before most cognitive hooks (11.0+) to ensure
    file contents are available in context before reasoning.
    """
    prompt = context.prompt or ""

    # Extract paths from prompt
    raw_paths = _extract_paths(prompt)
    if not raw_paths:
        return HookResult(context=None, tokens=0, priority=9.5)

    results: list[str] = []

    for raw_path in raw_paths:
        resolved = _expand_path(raw_path)
        if resolved is None:
            continue

        if not _is_readable_file(str(resolved)):
            continue

        # Check file size
        try:
            size = resolved.stat().st_size
            if size > _MAX_FILE_SIZE:
                results.append(f"[FILE: {resolved}] (too large: {size // 1024}KB > 500KB limit — skipping)")
                continue
        except OSError:
            continue

        # Read file contents
        try:
            content = resolved.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError):
            results.append(f"[FILE: {resolved}] (read error)")
            continue

        # Truncate very long files at 100 lines for context injection
        lines = content.splitlines()
        if len(lines) > 100:
            content = "\n".join(lines[:100])
            truncation_note = f"\n[...{len(lines) - 100} lines truncated...]"
        else:
            truncation_note = ""

        results.append(
            f"[FILE: {resolved}]\n"
            f"{content}"
            f"{truncation_note}"
        )

    if not results:
        return HookResult(context=None, tokens=0, priority=9.5)

    injected = (
        "FILE CONTENTS — IMMEDIATE READ:\n"
        + "\n\n".join(results)
    )
    tokens = len(injected) // 4

    return HookResult(context=injected, tokens=tokens, priority=9.5)
