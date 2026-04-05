import argparse
import ast
import fnmatch
import json
import logging
import os
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console

# --- Configuration ---

# Output settings
OUTPUT_FILENAME_BASE = "_llm_context"
MAX_FILE_SIZE_MB = 10  # Skip files larger than this
MAX_OUTPUT_SIZE_MB = 50  # Warn if output exceeds this

# Files to always include
WHITELISTED_FILES = [
    "dev/vidrec_manifest.json",
    "dev/vidrec_state.json",
    "config.toml",
    "pyproject.toml",
    "README.md",
    "requirements.txt",
    "setup.py",
]

# Directories to scan
WHITELISTED_DIRS = ["src", "docs", "tests", "test", "yt_sync"]

# File extensions to include from whitelisted directories
INCLUDED_EXTENSIONS = [".py", ".md", ".json", ".toml", ".yaml", ".yml", ".txt", ".rst"]

# Patterns to exclude
BLACKLISTED_PATTERNS = [
    "*.pyc",
    "*.pyo",
    "*.db",
    "*.egg-info",
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".vscode",
    ".idea",
    ".archive",
    ".repomix",
    ".scratch",
    "logs",
    "models",
    "dist",
    "build",
    "venv",
    "env",
    ".env",
    f"{OUTPUT_FILENAME_BASE}_*.md",
    "**/context_builder.py",
    ".pytest-report.json",
    "*.log",
    "*.bak",
    "*.tmp",
    "*.swp",
]

# Report configuration
ENABLED_REPORTS = {
    "git": True,
    "state": True,
    "tests": True,
    "complexity": True,
    "architecture": True,
    "dependencies": True,
    "todos": True,
}

# Performance settings
CLEAN_WHITESPACE = True
INCLUDE_AST_SUMMARY = True

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Utility Functions ---


def format_size(size_bytes: int) -> str:
    """Format bytes to human readable size."""
    if size_bytes < 0:
        return "0 B"
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"


def is_binary_file(file_path: Path) -> bool:
    """Check if file is binary."""
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(8192)
            if not chunk:
                return False
            if b"\0" in chunk:
                return True
            text_chars = set(range(32, 127)) | {ord("\n"), ord("\r"), ord("\t")}
            non_text = sum(1 for b in chunk if b not in text_chars)
            if chunk:
                return (non_text / len(chunk)) > 0.3
            return False
    except Exception:
        return True


def clean_file_content(content: str) -> str:
    """Cleans up excessive whitespace from file content."""
    if not CLEAN_WHITESPACE:
        return content
    content = re.sub(r"\n{3,}", "\n\n", content)
    content = "\n".join(line.rstrip() for line in content.splitlines())
    return content.strip()


# --- Configuration Loading ---


def load_config(root_path: Path) -> dict:
    """Load configuration from context_builder_config.json if it exists."""
    config_path = root_path / "context_builder_config.json"
    if config_path.is_file():
        try:
            with open(config_path, encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"Error loading config: {e}")
    return {}


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Generate project context for LLM")
    parser.add_argument(
        "--disable-report",
        action="append",
        help="Disable specific reports (e.g., git, tests)",
    )
    parser.add_argument(
        "--add-whitelist",
        action="append",
        help="Add additional files or directories to whitelist",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without generating output",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed file inclusion messages",
    )
    return parser.parse_args()


# --- Report Generation Functions ---


def generate_complexity_report(py_files: list[Path], root_path: Path) -> str:
    if not ENABLED_REPORTS.get("complexity", True):
        return ""

    header = "## Code Complexity Hotspots (Radon)\n"
    src_files = [str(p) for p in py_files if "src" in p.parts]
    if not src_files:
        return f"{header}*No Python files found in src/ to analyze.*\n"

    try:
        result = subprocess.run(
            [sys.executable, "-m", "radon", "cc", "--min", "C", *src_files],
            capture_output=True,
            text=True,
            cwd=root_path,
            check=False,
            encoding="utf-8",
        )

        if result.returncode != 0 and "No files specified" not in result.stderr:  # type: ignore
            if "No module named radon" in result.stderr:
                return f"{header}*`radon` is not installed. Run `pip install radon`.*\n"
            return f"{header}*Radon encountered an error: {result.stderr[:200]}*\n"

        output = result.stdout.strip()
        if not output or "No functions found" in output:  # type: ignore
            return f"{header}*No functions with high complexity (rank C or worse) found. Good job!* ✨\n"

        return f"{header}```\n{output}\n```\n"
    except Exception as e:
        logging.error(f"Error generating complexity report: {e}")
        return f"{header}*Error: {type(e).__name__}*\n"


def generate_test_summary(root_path: Path) -> str:
    if not ENABLED_REPORTS.get("tests", True):
        return ""

    header = "## Pytest Test Suite Summary\n"
    report_path = root_path / ".pytest-report.json"
    test_dirs = [d for d in ["tests", "test"] if (root_path / d).exists()]

    if not test_dirs:
        return f"{header}*No test directory found.*\n"

    try:
        env = os.environ.copy()
        python_paths = [str(root_path)]
        src_path = root_path / "src"
        if src_path.exists():
            python_paths.append(str(src_path))
        env["PYTHONPATH"] = (
            os.pathsep.join(python_paths) + os.pathsep + env.get("PYTHONPATH", "")
        )

        command = [
            sys.executable,
            "-m",
            "pytest",
            *test_dirs,
            "--tb=short",
            "--json-report",
            f"--json-report-file={report_path}",
            "-v",
        ]

        result = subprocess.run(
            command, env=env, capture_output=True, text=True, cwd=root_path, check=False
        )

        if result.returncode != 0 and not report_path.is_file():  # type: ignore
            stderr_output = result.stderr.strip()
            if "ImportError" in stderr_output or "ModuleNotFoundError" in stderr_output:
                return f"""{header}*Import error during test collection.*

**Suggested fixes:**
1. Ensure `src/__init__.py` exists (even if empty).
2. Use absolute imports in your code (`from src.module import ...`).

**Error details:**
```
{stderr_output}
```
"""
            return f"{header}*Pytest failed during collection.*\n```\n{result.stderr or result.stdout}\n```\n"

        if not report_path.is_file():  # type: ignore
            return f"{header}*Could not generate test report. Ensure `pytest-json-report` is installed.*\n"

        with open(report_path, encoding="utf-8") as f:  # type: ignore
            data = json.load(f)

        summary = data.get("summary", {})
        total = summary.get("total", 0)

        # Make the "no tests" message smarter
        if total == 0:
            test_py_files = [
                p
                for p in root_path.rglob("*.py")
                if any(d in p.parts for d in test_dirs)
            ]
            if not test_py_files:
                return f"{header}*No Python test files found in `tests/` or `test/` directories.*\n"
            else:
                return (
                    f"{header}*Pytest ran but failed to collect any tests from the {len(test_py_files)} "
                    f"existing test file(s).*\n*This often indicates a syntax error or import problem "
                    f"within those files.*\n"
                )

        passed = summary.get("passed", 0)
        failed_count = summary.get("failed", 0)
        skipped = summary.get("skipped", 0)
        errors = summary.get("error", 0)

        summary_lines = []
        if failed_count > 0 or errors > 0:
            summary_lines.append("- **Test Suite Status:** FAILED ❌")
        else:
            summary_lines.append("- **Test Suite Status:** PASSED ✅")

        summary_lines.append(f"- **Total Tests:** {total}")
        if passed:
            summary_lines.append(f"- **Passed:** {passed} ✅")
        if failed_count:
            summary_lines.append(f"- **Failed:** {failed_count} ❌")
        if skipped:
            summary_lines.append(f"- **Skipped:** {skipped} ⏭️")
        if errors:
            summary_lines.append(f"- **Errors:** {errors} 🚨")

        if failed_count > 0 and "tests" in data:
            summary_lines.append("\n**Failed Tests:**")
            for test in data["tests"]:
                if test.get("outcome") == "failed":
                    node_id = test.get("nodeid", "Unknown Test")
                    longrepr = test.get("longrepr", {})
                    error_msg = longrepr.get("reprcrash", {}).get(
                        "message", str(longrepr)
                    )
                    summary_lines.append(f"  - **{node_id}**")
                    summary_lines.append("    " + error_msg.split("\n")[0])

        return f"{header}" + "\n".join(summary_lines) + "\n"

    except Exception as e:
        return f"{header}*Unexpected error during test execution: {e}*\n"
    finally:
        if report_path.is_file():  # type: ignore
            try:
                os.remove(report_path)  # type: ignore
            except OSError:
                pass


def generate_architecture_lint_report(root_path: Path) -> str:
    if not ENABLED_REPORTS.get("architecture", True):
        return ""

    header = "## Architecture Lint Report\n"
    config_path = root_path / ".importlinter"
    if not config_path.is_file():
        return f"{header}*No `.importlinter` config found.*\n"

    try:
        result = subprocess.run(
            [sys.executable, "-m", "importlinter.cli"],
            capture_output=True,
            text=True,
            cwd=root_path,
            check=False,
        )
        if result.returncode == 0:
            return f"{header}*No violations found.* ✅\n"

        report = result.stdout.strip()
        if "is a namespace package" in report:
            report += "\n\n**Recommendation:** Create an empty `src/__init__.py` file to resolve this."

        return f"{header}**Violations:**\n```\n{report}\n```\n"
    except Exception as e:
        return f"{header}*Error: {type(e).__name__}*\n"


def generate_git_summary(root_path: Path) -> str:
    if not ENABLED_REPORTS.get("git", True):
        return ""

    header = "## Git Commit History (Last 15)\n"
    if not (root_path / ".git").is_dir():
        return f"{header}*Not a Git repository.*\n"

    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--graph", "-n", "15"],
            capture_output=True,
            text=True,
            cwd=root_path,
            check=True,
            encoding="utf-8",
        )
        return f"{header}```\n{result.stdout.strip()}\n```\n"
    except Exception as e:
        return f"{header}*Error: {type(e).__name__}*\n"


def generate_todo_report(files: list[Path], root_path: Path) -> str:
    if not ENABLED_REPORTS.get("todos", True):
        return ""

    header = "## TODO/FIXME Report\n"
    keywords = ["TODO", "FIXME", "NOTE", "HACK", "XXX"]
    report_items = []
    script_path = Path(__file__).resolve()

    for file_path in files:
        if (
            file_path.resolve() == script_path
            or file_path.suffix not in INCLUDED_EXTENSIONS
        ):
            continue
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                for i, line in enumerate(f, 1):
                    for keyword in keywords:
                        if keyword in line.upper():
                            rel_path = file_path.relative_to(root_path).as_posix()
                            match = re.search(
                                f"{keyword}:?\\s*(.+)", line, re.IGNORECASE
                            )
                            comment = (
                                (match.group(1).strip()[:60] + "...")
                                if (match and len(match.group(1)) > 60)
                                else (match.group(1).strip() if match else "")
                            )
                            report_items.append((rel_path, i, keyword, comment))
                            break
        except Exception:
            continue

    if not report_items:
        return f"{header}*No TODOs found.*\n"

    by_keyword = defaultdict(list)
    for path, line, keyword, comment in report_items:
        by_keyword[keyword].append(f"- `{path}:{line}`: {comment}")

    output = [header]
    for keyword in keywords:
        if by_keyword[keyword]:
            output.append(f"\n**{keyword}s:**")
            output.extend(by_keyword[keyword][:10])
            if len(by_keyword[keyword]) > 10:
                output.append(f"... and {len(by_keyword[keyword]) - 10} more")
    return "\n".join(output) + "\n"


def generate_dependency_graph(py_files: list[Path], root_path: Path) -> str:
    if not ENABLED_REPORTS.get("dependencies", True):
        return ""

    header = "## Module Dependency Graph\n"
    graph = defaultdict(set)
    src_path = root_path / "src"

    all_modules = {}
    for file_path in py_files:
        if file_path.stem != "__init__":
            try:
                rel_path = file_path.relative_to(
                    src_path if src_path in file_path.parents else root_path
                )
                module_name = ".".join(rel_path.parts[:-1] + (rel_path.stem,))
                all_modules[module_name] = file_path
            except ValueError:
                continue

    for module_name, file_path in all_modules.items():
        try:
            with open(file_path, encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in all_modules:
                            graph[module_name].add(alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    if node.module in all_modules:
                        graph[module_name].add(node.module)
        except Exception:
            continue

    if not graph:
        return f"{header}*No dependencies found.*\n"

    mermaid_lines = ["```mermaid", "graph TD;"]
    all_nodes = set(graph.keys()) | {dep for deps in graph.values() for dep in deps}
    for node in sorted(all_nodes):
        simple_name = node.split(".")[-1]
        mermaid_lines.append(f'    {node.replace(".", "_")}["{simple_name}"];')
    for module, deps in sorted(graph.items()):
        for dep in sorted(deps):
            if dep != module:
                mermaid_lines.append(
                    f"    {module.replace('.', '_')} --> {dep.replace('.', '_')};"
                )
    mermaid_lines.append("```\n")
    return f"{header}\n" + "\n".join(mermaid_lines)


def generate_state_summary(root_path: Path) -> str:
    """Generates a stylized summary of the state file."""
    if not ENABLED_REPORTS.get("state", True):
        return ""

    HEADER_TEXT = "## State File Summary"
    STATUS_EMOJIS = {
        "DONE": "✅",
        "IN_PROGRESS": "🔄",
        "TO_DO": "📋",
        "BLOCKED": "🚫",
        "UNKNOWN": "❓",
    }

    state_file = root_path / "dev" / "vidrec_state.json"
    if not state_file.is_file():
        return f"{HEADER_TEXT}\n*`dev/vidrec_state.json` not found.*\n"

    try:
        duplicate_keys_found = []

        def find_duplicates_hook(pairs: list[tuple[str, Any]]) -> dict:
            """A hook for json.load to detect duplicate keys at the top level."""
            keys = [k for k, _ in pairs]
            counts = Counter(keys)
            for key, count in counts.items():
                if count > 1 and key not in duplicate_keys_found:
                    duplicate_keys_found.append(key)
            return dict(pairs)

        with open(state_file, encoding="utf-8") as f:  # type: ignore
            data = json.load(f, object_pairs_hook=find_duplicates_hook)

        tasks = data.get("tasks", [])

        report_lines = [HEADER_TEXT]

        if duplicate_keys_found:
            keys_str = "`, `".join(sorted(duplicate_keys_found))
            report_lines.append(f"**Warning:** Duplicate keys found: `{keys_str}`")

        report_lines.append(f"- **Total Tasks:** {len(tasks)}")
        report_lines.append("")  # Blank line for spacing

        status_counts = Counter(task.get("status", "UNKNOWN") for task in tasks)
        for status, count in sorted(status_counts.items()):
            emoji = STATUS_EMOJIS.get(status.upper(), "❓")
            report_lines.append(f"- **{status.upper()}:** {count} {emoji}")

        return "\n".join(report_lines) + "\n"

    except (json.JSONDecodeError, OSError) as e:
        return f"{HEADER_TEXT}\n*Error reading or parsing state file: {type(e).__name__}*\n"


def generate_ast_summary(source_code: str, file_path: str) -> str:
    if not INCLUDE_AST_SUMMARY:
        return ""

    summary = ["**Structure:**"]
    try:
        tree = ast.parse(source_code, filename=file_path)
        imports = sum(
            1
            for n in ast.iter_child_nodes(tree)
            if isinstance(n, (ast.Import, ast.ImportFrom))
        )
        functions = [
            n.name
            for n in ast.iter_child_nodes(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        classes = [
            n.name for n in ast.iter_child_nodes(tree) if isinstance(n, ast.ClassDef)
        ]

        if imports:
            summary.append(f"- Imports: {imports}")
        if functions:
            func_list = ", ".join(f"`{f}`" for f in functions[:5])
            if len(functions) > 5:
                func_list += f" +{len(functions) - 5} more"
            summary.append(f"- Functions: {func_list}")
        if classes:
            summary.append(f"- Classes: {', '.join(f'`{c}`' for c in classes)}")
        line_count = source_code.count("\n") + 1
        summary.append(f"- Lines: {line_count}")
    except Exception:
        summary.append("- *Syntax error*")
    return "\n".join(summary) if len(summary) > 1 else ""


# --- File Discovery Functions ---


def read_gitignore_patterns(root_path: Path) -> list:
    """Read .gitignore patterns."""
    gitignore_path = root_path / ".gitignore"
    patterns = []
    if gitignore_path.is_file():
        try:
            with open(gitignore_path, encoding="utf-8") as f:  # type: ignore
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if line.endswith("/"):
                            patterns.append(line[:-1])
                            patterns.append(f"{line[:-1]}/**")
                        else:
                            patterns.append(line)
        except Exception:
            pass
    return patterns


def is_ignored(path: Path, root_path: Path, ignore_patterns: list) -> bool:
    """Check if path should be ignored."""
    try:
        relative_path = path.relative_to(root_path)
        relative_str = relative_path.as_posix()
        for p in ignore_patterns:
            if fnmatch.fnmatch(relative_str, p) or any(
                fnmatch.fnmatch(part, p) for part in relative_path.parts
            ):
                return True
        return False
    except ValueError:
        return True


def should_include_file(path: Path, root_path: Path, whitelisted_dirs: list) -> bool:
    """Determine if file should be included."""
    try:
        if not path.is_file() or not path.resolve().is_relative_to(root_path.resolve()):
            return False
    except (
        OSError,
        ValueError,
    ):  # Catches issues with resolving paths (e.g., on network drives)
        return False

    if (
        path.stat().st_size > MAX_FILE_SIZE_MB * 1024 * 1024
        or is_binary_file(path)
        or path.suffix not in INCLUDED_EXTENSIONS
    ):
        return False
    return any(
        dir_name in path.relative_to(root_path).parts for dir_name in whitelisted_dirs
    )


def generate_tree_structure(
    root_path: Path, ignore_patterns: list, max_depth: int = 4
) -> str:
    """Generate project tree structure."""
    tree_lines = ["## Project Tree Structure\n\n```", f"\n{root_path.name}/"]
    file_count = dir_count = 0

    def recurse_tree(current_path: Path, prefix: str = "", depth: int = 0):
        nonlocal file_count, dir_count
        if depth > max_depth:
            tree_lines.append(f"{prefix}...")
            return
        try:
            items = sorted(
                [
                    p
                    for p in current_path.iterdir()
                    if not is_ignored(p, root_path, ignore_patterns)
                ],
                key=lambda p: (p.is_file(), p.name.lower()),
            )
        except OSError:
            return
        for i, path in enumerate(items):
            connector = "└── " if i == len(items) - 1 else "├── "
            new_prefix = prefix + ("    " if i == len(items) - 1 else "│   ")
            if path.is_file():
                try:
                    tree_lines.append(
                        f"{prefix}{connector}{path.name} ({format_size(path.stat().st_size)})"
                    )
                    file_count += 1
                except OSError:
                    continue
            else:
                tree_lines.append(f"{prefix}{connector}{path.name}/")
                dir_count += 1
                recurse_tree(path, new_prefix, depth + 1)

    recurse_tree(root_path)
    tree_lines.append(f"\n({file_count} files, {dir_count} directories)")
    tree_lines.append("```\n")
    return "\n".join(tree_lines)


# --- Main Execution ---


def main():
    """Main execution function."""
    project_root = Path.cwd()
    args = parse_args()

    # --- NEW: Setup Rich Console ---
    console = Console()

    # --- Load and apply configuration (no changes here) ---
    config = load_config(project_root)
    global WHITELISTED_FILES, WHITELISTED_DIRS, ENABLED_REPORTS
    ENABLED_REPORTS.update(config.get("enabled_reports", {}))
    WHITELISTED_FILES = config.get("whitelisted_files", WHITELISTED_FILES)
    WHITELISTED_DIRS = config.get("whitelisted_dirs", WHITELISTED_DIRS)

    # --- Apply command-line overrides (no changes here) ---
    if args.disable_report:
        for report in args.disable_report:
            if report in ENABLED_REPORTS:
                ENABLED_REPORTS[report] = False
    if args.add_whitelist:
        for item in args.add_whitelist:
            path = Path(item)
            if path.is_file():
                WHITELISTED_FILES.append(item)
            elif path.is_dir():
                WHITELISTED_DIRS.append(item)

    # --- REPLACED SPINNER with rich.status ---
    reports = {}
    sorted_files = []
    output_filename = ""

    try:
        with console.status("[bold blue]Building context...", spinner="dots") as status:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # --- NEW: Define and create the output directory ---
            output_dir = project_root / "dev" / "llm_context"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_filename = f"{OUTPUT_FILENAME_BASE}_{timestamp}.md"
            output_path = output_dir / output_filename
            all_ignore_patterns = BLACKLISTED_PATTERNS + read_gitignore_patterns(
                project_root
            )

            status.update("Discovering files...")
            all_files = [
                p
                for p in project_root.rglob("*")
                if p.is_file() and not is_ignored(p, project_root, all_ignore_patterns)
            ]
            py_files = [p for p in all_files if p.suffix == ".py"]
            files_to_include = {
                project_root / f
                for f in WHITELISTED_FILES
                if (project_root / f).exists()
            } | {
                p
                for p in all_files
                if should_include_file(p, project_root, WHITELISTED_DIRS)
            }
            sorted_files = sorted(list(files_to_include))

            status.update("Analyzing code and generating reports...")
            report_funcs = {
                "git": (generate_git_summary, (project_root,)),
                "state": (generate_state_summary, (project_root,)),
                "tests": (generate_test_summary, (project_root,)),
                "complexity": (generate_complexity_report, (py_files, project_root)),
                "architecture": (generate_architecture_lint_report, (project_root,)),
                "dependencies": (generate_dependency_graph, (py_files, project_root)),
                "todos": (generate_todo_report, (all_files, project_root)),
            }

            status.update("[bold blue]Analyzing project and generating reports...[/]")
            reports = {
                name: func(*f_args)
                for name, (func, f_args) in report_funcs.items()
                if ENABLED_REPORTS.get(name, False)
            }

        console.print("[bold green][ Building Context ] ✓ Analysis complete!")

        # --- Build the output content (no changes here) ---
        output_content = [
            f"""# AI Context File: {project_root.name}
*Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*

**Project:** `{project_root.name}`
**Location:** `{project_root}`
**Files Included:** {len(sorted_files)}

---
""",
            "# Project Analysis\n" + "".join(reports.values()) if reports else "",
            generate_tree_structure(project_root, all_ignore_patterns),
            "\n---\n\n# Source Files\n",
        ]

        for file_path in sorted_files:
            rel_path = file_path.relative_to(project_root).as_posix()
            lang = {
                ".py": "python",
                ".md": "markdown",
                ".json": "json",
                ".toml": "toml",
                ".yaml": "yaml",
            }.get(file_path.suffix, "")
            try:
                with open(file_path, encoding="utf-8", errors="ignore") as f:
                    content = clean_file_content(f.read())
                ast_sum = (
                    generate_ast_summary(content, str(file_path))
                    if lang == "python" and content.strip()
                    else ""
                )
                if ast_sum:
                    output_content.append(
                        f"\n---\n\n## File: `{rel_path}`\n{ast_sum}\n```{lang}\n{content}\n```"
                    )
                else:
                    output_content.append(
                        f"\n---\n\n## File: `{rel_path}`\n```{lang}\n{content}\n```"
                    )
            except Exception as e:
                output_content.append(
                    f"\n---\n\n## File: `{rel_path}`\n*Error: {type(e).__name__}*\n"
                )

        final_content = "\n".join(output_content)

        if args.dry_run:
            console.print(
                f"Dry run: Would generate {output_filename} with {len(sorted_files)} files."
            )
            return

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(final_content)

        # --- NEW: Build and print the final summary panel ---
        issue_keywords = [
            "Warning:",
            "violations detected:",
            "Failed:",
            "error occurred",
            "No tests",
            "ImportError",
        ]
        issues = {
            name: content
            for name, content in reports.items()
            if any(k in content for k in issue_keywords)
        }

        # --- Build and print a clean, professional report card ---
        success_icon = "✅" if not issues else "⚠️"

        console.print(
            f"[bold green]{success_icon} Context Build Complete![/bold green]"
        )
        console.print()
        console.print(
            f"   📄 [bold]Output File[/bold]:    {output_path.relative_to(project_root).as_posix()}"
        )
        console.print(f"   📝 [bold]Files Included[/bold]: {len(sorted_files)}")
        console.print(f"   📍 [bold]Project Root[/bold]:   {str(project_root)}")

        if issues:
            console.print("\n   " + "─" * 20 + " ⚠️ ISSUES DETECTED " + "─" * 20)

            for name, content in issues.items():
                console.print(
                    f"\n   [bold]{name.replace('_', ' ').title()} Report[/bold]"
                )
                # Custom, cleaner formatting for specific reports
                if name == "state":
                    warnings, status_lines, total_str = [], [], "0"
                    for line in content.splitlines():
                        clean_line = re.sub(r"[*`#]", "", line).strip()
                        if "Warning" in clean_line and ":" in clean_line:
                            warnings.append(clean_line)
                        elif "Total Tasks" in clean_line and ":" in clean_line:
                            total_str = clean_line.split(":")[1].strip()
                        elif (
                            any(emoji in clean_line for emoji in "✅🔄📋🚫")
                            and ":" in clean_line
                        ):
                            status_lines.append(clean_line)
                    for warning in warnings:
                        console.print(f"     • {warning}")
                    console.print(f"     • [bold]Total Tasks[/bold]: {total_str}")
                    for line in sorted(status_lines):
                        label, value = line.split(":", 1)
                        console.print(
                            f"       - {label.replace('_', ' ').title()}: {value.strip()}"
                        )
                elif name == "tests":
                    # Use the new, smarter message if it exists
                    smarter_line = next(
                        (
                            line
                            for line in content.splitlines()
                            if "Pytest ran but failed" in line
                        ),
                        None,
                    )
                    if smarter_line:
                        console.print(
                            f"     • {re.sub(r'[*`#]', '', smarter_line).strip()}"
                        )
                        console.print(
                            f"       {next((line for line in content.splitlines() if 'This often indicates' in line), '').strip().replace('*', '')}"
                        )
                else:
                    for line in content.splitlines()[:3]:
                        console.print(f"     • {re.sub(r'[-*`#]', '', line).strip()}")

        # --- Optionally print verbose file list ---
        if args.verbose:
            console.print("\n[bold]Included Files:[/bold]")
            for file_path in sorted_files:
                rel_path = file_path.relative_to(project_root).as_posix()
                console.print(f"- {rel_path}")

    except Exception:
        console.print_exception()
    # The `finally` block for the spinner thread is no longer needed


if __name__ == "__main__":
    main()
