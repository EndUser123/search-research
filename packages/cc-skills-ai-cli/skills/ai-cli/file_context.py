#!/usr/bin/env python3
"""
File context handling for LLM CLI tools.

Implements patterns from Aider, Cursor, and other agentic CLI tools:
- Directory support (recursive file collection)
- Absolute path resolution
- Structured file content formatting
- Repo map generation for large file sets
"""

from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from pathlib import Path

# Default configuration
DEFAULT_MAX_FILES = 20  # Threshold for repo map generation
DEFAULT_MAX_FILE_SIZE = 100_000  # 100KB max per file


def resolve_path(path_str: str) -> Path:
    """Resolve a path string to an absolute Path.

    Args:
        path_str: Path string (can be relative or absolute)

    Returns:
        Resolved absolute Path object

    Examples:
        >>> resolve_path("src/file.py")
        Path('/project/src/file.py')
        >>> resolve_path("../config.yaml")
        Path('/project/config.yaml')
    """
    path = Path(path_str)

    # If relative, resolve from current working directory
    if not path.is_absolute():
        path = Path.cwd() / path

    # Resolve to absolute path (eliminates symlinks, .., .)
    return path.resolve()


def collect_files_from_paths(
    paths: list[str],
    extensions: list[str] | None = None,
    max_files: int = DEFAULT_MAX_FILES,
) -> list[Path]:
    """Collect files from a list of paths (files or directories).

    Args:
        paths: List of file/directory path strings
        extensions: Optional file extension filter (e.g., ['.py', '.ts'])
        max_files: Maximum files to collect (for token budgeting)

    Returns:
        List of absolute Path objects

    Examples:
        >>> collect_files_from_paths(['src/'], extensions=['.py'])
        [Path('/project/src/main.py'), Path('/project/src/utils.py')]
        >>> collect_files_from_paths(['README.md'])
        [Path('/project/README.md')]
    """
    collected = []

    for path_str in paths:
        path = resolve_path(path_str)

        if not path.exists():
            print(f"[Warning: Path not found: {path_str}]", file=sys.stderr)
            continue

        if path.is_file():
            collected.append(path)
        elif path.is_dir():
            # Recursively collect files from directory
            for item in _iter_files_recursive(path, extensions):
                collected.append(item)
                if len(collected) >= max_files:
                    print(
                        f"[Warning: Reached max files ({max_files}), stopping collection]",
                        file=sys.stderr,
                    )
                    break

        if len(collected) >= max_files:
            break

    return collected


def _iter_files_recursive(
    directory: Path,
    extensions: list[str] | None = None,
) -> Iterator[Path]:
    """Iterate over files in a directory recursively.

    Args:
        directory: Directory path to scan
        extensions: Optional file extension filter

    Yields:
        Path objects for each file
    """
    for root, dirs, files in os.walk(directory):
        root_path = Path(root)

        # Skip common ignore directories
        dirs[:] = [
            d
            for d in dirs
            if d
            not in {
                "__pycache__",
                "node_modules",
                ".git",
                ".venv",
                "venv",
                "env",
                ".env",
                "dist",
                "build",
                ".tox",
                "mypy_cache",
                ".pytest_cache",
                "htmlcov",
            }
        ]

        for filename in files:
            file_path = root_path / filename

            # Skip hidden files
            if filename.startswith("."):
                continue

            # Apply extension filter if specified
            if extensions:
                if not any(file_path.suffix == ext for ext in extensions):
                    continue

            yield file_path


def read_file_content_safe(
    file_path: Path,
    max_size: int = DEFAULT_MAX_FILE_SIZE,
) -> str | None:
    """Read file content safely with size limit.

    Args:
        file_path: Path to file
        max_size: Maximum file size in bytes

    Returns:
        File content as string, or None if error/too large
    """
    try:
        if file_path.stat().st_size > max_size:
            print(
                f"[Warning: File too large ({file_path.stat().st_size} bytes), skipping: {file_path.name}]",
                file=sys.stderr,
            )
            return None

        return file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(
            f"[Warning: Error reading file {file_path.name}: {e}]",
            file=sys.stderr,
        )
        return None


def create_repo_map(files: list[Path]) -> str:
    """Create a high-level repository map (like Aider's repo map).

    Provides a structural overview without full file contents.

    Args:
        files: List of file paths

    Returns:
        Formatted repo map string
    """
    lines = ["# Repository Map", ""]

    # Group by directory
    by_dir: dict[str, list[Path]] = {}
    for file in files:
        dir_name = str(file.parent) if file.parent != Path.cwd() else "."
        if dir_name not in by_dir:
            by_dir[dir_name] = []
        by_dir[dir_name].append(file)

    # List files by directory
    for dir_name in sorted(by_dir.keys()):
        lines.append(f"## {dir_name}/")
        for file in sorted(by_dir[dir_name]):
            lines.append(f"  - {file.name}")
        lines.append("")

    # Count summary
    lines.append(f"**Total: {len(files)} files**")

    return "\n".join(lines)


def format_files_for_llm(
    files: list[Path],
    use_repo_map: bool = False,
) -> str:
    """Format file contents for LLM consumption.

    Args:
        files: List of file paths
        use_repo_map: If True, create repo map instead of full contents

    Returns:
        Formatted string with file contents
    """
    if use_repo_map or len(files) > DEFAULT_MAX_FILES:
        return create_repo_map(files)

    parts = []

    for file_path in files:
        content = read_file_content_safe(file_path)
        if content is None:
            continue

        # Use forward slashes for cross-platform compatibility
        relative_path = file_path.relative_to(Path.cwd()).as_posix()

        parts.append(f"### {relative_path}")
        parts.append("```")  # Start code block
        parts.append(content)
        parts.append("```")  # End code block
        parts.append("")  # Blank line separator

    return "\n".join(parts)


def build_context_from_paths(
    paths: list[str],
    extensions: list[str] | None = None,
    use_repo_map: bool = False,
) -> tuple[str, dict[str, Any]]:
    """Build LLM context from file/directory paths.

    This is the main entry point that implements the recommended pattern:
    1. Accept both file paths and directories
    2. Resolve to absolute paths
    3. Collect files (recursively for directories)
    4. Format with clear delimiters
    5. Generate repo map if too many files

    Args:
        paths: List of file/directory path strings
        extensions: Optional file extension filter
        use_repo_map: Force repo map generation

    Returns:
        Tuple of (formatted_context_string, metadata_dict)

    Examples:
        >>> context, meta = build_context_from_paths(['src/'], extensions=['.py'])
        >>> print(context)
        ### src/main.py
        ...
        >>> print(meta['file_count'])
        15
    """
    files = collect_files_from_paths(paths, extensions)

    metadata = {
        "file_count": len(files),
        "total_size": sum(f.stat().st_size for f in files if f.exists()),
        "files": [str(f.relative_to(Path.cwd())) for f in files],
    }

    # Generate repo map if too many files or explicitly requested
    if len(files) > DEFAULT_MAX_FILES or use_repo_map:
        formatted = create_repo_map(files)
        metadata["mode"] = "repo_map"
    else:
        formatted = format_files_for_llm(files)
        metadata["mode"] = "full_content"

    return formatted, metadata


def print_context_summary(metadata: dict[str, Any]) -> None:
    """Print a summary of loaded context.

    Args:
        metadata: Metadata dict from build_context_from_paths
    """
    mode = metadata.get("mode", "unknown")
    count = metadata.get("file_count", 0)
    size_kb = metadata.get("total_size", 0) / 1024

    print(f"\n[Context loaded: {count} files, {size_kb:.1f} KB, mode={mode}]")

    if metadata.get("files"):
        print("[Files included:]")
        for file_path in metadata["files"][:10]:  # Show first 10
            print(f"  - {file_path}")
        if len(metadata["files"]) > 10:
            print(f"  ... and {len(metadata['files']) - 10} more")
        print()
