#!/usr/bin/env python3
"""
plugin-audit-and-fix.py
Comprehensive audit and auto-fix for Claude Code plugin manifests.
Handles plugin.json, hooks.json, marketplace.json, and source path scanning.

Usage:
    python plugin-audit-and-fix.py                  # Default audit
    python plugin-audit-and-fix.py --auto-fix       # Auto-fix manifest issues
    python plugin-audit-and-fix.py --scan-paths     # Scan source for hardcoded paths
    python plugin-audit-and-fix.py --auto-fix --scan-paths  # Full audit + fix
    python plugin-audit-and-fix.py --delete-hooks   # Delete hooks.json instead of fixing
    python plugin-audit-and-fix.py --marketplace-root /path/to/marketplace  # Override path

Path resolution (auto-detected):
    $CLAUDE_PLUGIN_ROOT  — preferred, set by Claude Code at runtime
    Script location      — fallback, derived from this script's path
    --marketplace-root  — override
"""

import argparse
import json
import os
import re
import sys
import ast
from pathlib import Path
from typing import Optional


def _detect_marketplace_root(script_path: Path, cli_root: str | None) -> Path:
    """Auto-detect marketplace root from env, script location, or explicit arg."""
    if cli_root:
        return Path(cli_root)

    env_root = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env_root:
        # $CLAUDE_PLUGIN_ROOT points to the plugin root (e.g. .../plugins/plugin-installer)
        # Marketplace is at the sibling .claude-marketplace folder
        root = Path(env_root)
        # If we're inside a plugin, walk up to find .claude-marketplace
        # plugin-installer/scripts/plugin-audit-and-fix.py -> plugin-installer/.claude-marketplace
        for parent in [root, root.parent]:
            mp = parent / ".claude-marketplace"
            if mp.exists():
                return mp
        return root

    # Fallback: derive from script location
    # plugin-installer/scripts/plugin-audit-and-fix.py
    # -> plugin-installer/scripts/ -> plugin-installer/ -> .claude-marketplace/
    plugin_root = script_path.parent  # scripts/
    marketplace_root = plugin_root.parent.parent / ".claude-marketplace"
    if marketplace_root.exists():
        return marketplace_root

    # Last resort: assume plugin root is also marketplace root
    return plugin_root.parent


def _load_json(path: Path) -> dict | None:
    """Load and parse JSON file, return None on failure."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _save_json(path: Path, data: dict) -> None:
    """Save data as JSON."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# === PART 1: Manifest audit ===

def audit_plugins(plugins_dir: Path, marketplace_root: Path) -> list[dict]:
    """Audit all plugins in marketplace, return list of issues."""
    issues = []

    for plugin_link in plugins_dir.iterdir():
        if plugin_link.is_symlink() and not plugin_link.exists():
            issues.append({
                "plugin": plugin_link.name,
                "issue": "Broken symlink (target does not exist)",
                "severity": "ERROR",
            })
            continue
        if plugin_link.is_symlink():
            plugin_dir = plugin_link.resolve()
        elif plugin_link.is_dir():
            plugin_dir = plugin_link
        else:
            continue

        manifest_path = plugin_dir / ".claude-plugin" / "plugin.json"
        hooks_path = plugin_dir / "hooks" / "hooks.json"

        # Check plugin.json
        if not manifest_path.exists():
            issues.append({
                "plugin": plugin_link.name,
                "issue": "No .claude-plugin/plugin.json found",
                "severity": "WARNING",
            })
            continue

        manifest = _load_json(manifest_path)
        if manifest is None:
            issues.append({
                "plugin": plugin_link.name,
                "issue": "plugin.json is not valid JSON",
                "severity": "ERROR",
            })
            continue

        if not manifest.get("name"):
            issues.append({
                "plugin": plugin_link.name,
                "issue": "Missing required field: name",
                "severity": "ERROR",
            })
        else:
            # Validate name format (kebab-case, lowercase, starts with letter)
            name = manifest["name"]
            if not re.match(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$", name):
                issues.append({
                    "plugin": plugin_link.name,
                    "issue": f"Plugin name '{name}' must be kebab-case (lowercase, hyphens, starts with letter)",
                    "severity": "ERROR",
                })

        # Validate version format (semver)
        version = manifest.get("version", "")
        if version and not re.match(r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$", version):
            issues.append({
                "plugin": plugin_link.name,
                "issue": f"Version '{version}' should be semver (MAJOR.MINOR.PATCH)",
                "severity": "WARNING",
            })

        # Validate description length
        desc = manifest.get("description", "")
        if desc:
            if len(desc) < 50:
                issues.append({
                    "plugin": plugin_link.name,
                    "issue": f"Description ({len(desc)} chars) is short (< 50 chars recommended)",
                    "severity": "WARNING",
                })
            elif len(desc) > 200:
                issues.append({
                    "plugin": plugin_link.name,
                    "issue": f"Description ({len(desc)} chars) exceeds 200 char marketplace limit",
                    "severity": "WARNING",
                })

        # Check for marketplace-only fields in plugin.json
        bad_fields = []
        for field in ("source", "category"):
            if field in manifest:
                bad_fields.append(field)
        if "keywords" in manifest and not manifest["keywords"]:
            bad_fields.append("keywords (empty)")
        if bad_fields:
            issues.append({
                "plugin": plugin_link.name,
                "issue": f"Non-plugin fields in plugin.json: {', '.join(bad_fields)}",
                "severity": "WARNING",
            })

        # Check skills field
        if "skills" in manifest:
            skills_value = manifest["skills"]
            if isinstance(skills_value, list):
                has_names = any(
                    isinstance(s, str) and not s.startswith("./")
                    for s in skills_value
                )
                if has_names:
                    issues.append({
                        "plugin": plugin_link.name,
                        "issue": "Invalid skills array (names not paths)",
                        "severity": "ERROR",
                    })
            elif isinstance(skills_value, str):
                if not skills_value.startswith("./"):
                    issues.append({
                        "plugin": plugin_link.name,
                        "issue": f"skills path missing './': {skills_value}",
                        "severity": "ERROR",
                    })

        # Check hooks.json
        if hooks_path.exists():
            hooks_json = _load_json(hooks_path)
            if hooks_json is None:
                issues.append({
                    "plugin": plugin_link.name,
                    "issue": "hooks.json is not valid JSON",
                    "severity": "ERROR",
                })
            elif isinstance(hooks_json, list):
                issues.append({
                    "plugin": plugin_link.name,
                    "issue": "hooks.json is an array, not an object (should be { 'hooks': {...} })",
                    "severity": "ERROR",
                })
            elif hooks_json.get("hooks") is None:
                issues.append({
                    "plugin": plugin_link.name,
                    "issue": "hooks.json missing top-level 'hooks' key",
                    "severity": "ERROR",
                })

        # Check agents/ directory
        agents_dir = plugin_dir / "agents"
        if agents_dir.is_dir():
            for agent_file in agents_dir.glob("*.md"):
                agent_issues = _audit_agent_file(agent_file, plugin_link.name, plugin_dir)
                issues.extend(agent_issues)

        # Check commands/ directory
        commands_dir = plugin_dir / "commands"
        if commands_dir.is_dir():
            for cmd_file in commands_dir.glob("*.md"):
                cmd_issues = _audit_command_file(cmd_file, plugin_link.name, plugin_dir)
                issues.extend(cmd_issues)

        # Check for components incorrectly nested inside .claude-plugin/
        claude_plugin_dir = plugin_dir / ".claude-plugin"
        for component_type in ("commands", "agents", "skills", "hooks"):
            bad_dir = claude_plugin_dir / component_type
            if bad_dir.exists() and bad_dir.is_dir():
                issues.append({
                    "plugin": plugin_link.name,
                    "issue": f"Component directory '{component_type}/' must be at plugin root, not inside .claude-plugin/",
                    "severity": "ERROR",
                })

        # Check hooks.json event structure and prompt/timeouts
        if hooks_path.exists():
            hooks_json = _load_json(hooks_path)
            if hooks_json and isinstance(hooks_json, dict) and hooks_json.get("hooks"):
                hooks_block = hooks_json["hooks"]
                supported_prompt_events = {"Stop", "SubagentStop", "UserPromptSubmit", "PreToolUse"}
                timeout_required_events = {"PreToolUse", "PostToolUse", "UserPromptSubmit"}
                for event_name, event_handlers in hooks_block.items():
                    if not isinstance(event_handlers, list):
                        continue
                    for handler in event_handlers:
                        if not isinstance(handler, dict):
                            continue
                        for hook in handler.get("hooks", []):
                            if not isinstance(hook, dict):
                                continue
                            hook_type = hook.get("type", "")
                            # Prompt hooks only supported on certain events
                            if hook_type == "prompt" and event_name not in supported_prompt_events:
                                issues.append({
                                    "plugin": plugin_link.name,
                                    "issue": f"Hook type 'prompt' is not supported on '{event_name}' event (supported: {', '.join(sorted(supported_prompt_events))})",
                                    "severity": "ERROR",
                                })
                            # Command hooks on sync events should have timeout
                            if hook_type == "command" and event_name in timeout_required_events:
                                if "timeout" not in hook:
                                    issues.append({
                                        "plugin": plugin_link.name,
                                        "issue": f"Command hook on '{event_name}' is missing 'timeout' field (may hang session)",
                                        "severity": "WARNING",
                                    })

        # Check skills/ directories for missing SKILL.md and nesting issues
        skills_dir = plugin_dir / "skills"
        skill_skip_dirs = SKIP_DIRS | {".claude", ".aid"}
        if skills_dir.is_dir():
            for skill_dir in skills_dir.iterdir():
                if skill_dir.is_dir() and skill_dir.name not in skill_skip_dirs:
                    top_level_skill_md = (skill_dir / "SKILL.md").exists()
                    nested_skill_md_files = [f for f in skill_dir.rglob("SKILL.md") if f != skill_dir / "SKILL.md"]
                    has_nested_skills_dir = (skill_dir / "skills").is_dir()

                    if not top_level_skill_md and not nested_skill_md_files:
                        issues.append({
                            "plugin": plugin_link.name,
                            "issue": f"Skill directory '{skill_dir.name}/' has no SKILL.md (auto-discovery requires it)",
                            "severity": "WARNING",
                        })
                    elif nested_skill_md_files and not top_level_skill_md:
                        issues.append({
                            "plugin": plugin_link.name,
                            "issue": f"Skill '{skill_dir.name}/' has SKILL.md only in nested subdirectory (non-standard structure)",
                            "severity": "WARNING",
                        })
                    elif has_nested_skills_dir:
                        issues.append({
                            "plugin": plugin_link.name,
                            "issue": f"Skill '{skill_dir.name}/' has nested 'skills/' subdirectory (inverted structure — SKILL.md should be at top level)",
                            "severity": "WARNING",
                        })

    return issues


def _audit_agent_file(agent_path: Path, plugin_name: str, plugin_dir: Path) -> list[dict]:
    """Audit a single agent .md file for frontmatter issues."""
    issues = []
    try:
        content = agent_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return issues

    if not content.startswith("---"):
        issues.append({
            "plugin": plugin_name,
            "file": str(agent_path.relative_to(plugin_dir)) if plugin_dir in agent_path.parents else agent_path.name,
            "issue": f"agent file missing YAML frontmatter",
            "severity": "WARNING",
        })
        return issues

    # Extract frontmatter block
    parts = content.split("---", 2)
    if len(parts) < 3:
        return issues

    fm_text = parts[1]
    fm = {}
    for line in fm_text.strip().split("\n"):
        if ":" in line:
            key, val = line.split(":", 1)
            fm[key.strip()] = val.strip().strip('"').strip("'")

    # Check required fields
    name = fm.get("name", "")
    if name:
        if len(name) < 3 or len(name) > 50:
            issues.append({
                "plugin": plugin_name,
                "file": agent_path.name,
                "issue": f"agent name '{name}' must be 3-50 chars (lowercase, numbers, hyphens)",
                "severity": "ERROR",
            })
        if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$", name):
            issues.append({
                "plugin": plugin_name,
                "file": agent_path.name,
                "issue": f"agent name '{name}' must be lowercase/hyphens only, start/end with alphanumeric",
                "severity": "ERROR",
            })
    else:
        issues.append({
            "plugin": plugin_name,
            "file": agent_path.name,
            "issue": "agent missing required 'name' field in frontmatter",
            "severity": "ERROR",
        })

    # Check model field
    model = fm.get("model", "")
    valid_models = {"inherit", "sonnet", "opus", "haiku"}
    if model and model not in valid_models:
        issues.append({
            "plugin": plugin_name,
            "file": agent_path.name,
            "issue": f"agent model '{model}' must be one of: {', '.join(valid_models)}",
            "severity": "ERROR",
        })
    elif not model:
        issues.append({
            "plugin": plugin_name,
            "file": agent_path.name,
            "issue": "agent missing required 'model' field in frontmatter",
            "severity": "ERROR",
        })

    # Check color field
    color = fm.get("color", "")
    valid_colors = {"blue", "cyan", "green", "yellow", "magenta", "red"}
    if color and color not in valid_colors:
        issues.append({
            "plugin": plugin_name,
            "file": agent_path.name,
            "issue": f"agent color '{color}' must be one of: {', '.join(valid_colors)}",
            "severity": "ERROR",
        })
    elif not color:
        issues.append({
            "plugin": plugin_name,
            "file": agent_path.name,
            "issue": "agent missing required 'color' field in frontmatter",
            "severity": "ERROR",
        })

    # Check description for <example> blocks
    desc = fm.get("description", "")
    if desc and "<example>" not in desc:
        issues.append({
            "plugin": plugin_name,
            "file": agent_path.name,
            "issue": "agent description missing <example> blocks (required for trigger detection)",
            "severity": "WARNING",
        })

    return issues


def _audit_command_file(cmd_path: Path, plugin_name: str, plugin_dir: Path) -> list[dict]:
    """Audit a single command .md file for frontmatter and format issues."""
    issues = []
    try:
        content = cmd_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return issues

    # Extract frontmatter if present
    fm = {}
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    fm[key.strip()] = val.strip().strip('"').strip("'")

    # Check allowed-tools if present (should be valid tool names or patterns)
    allowed_tools = fm.get("allowed-tools", "")
    if allowed_tools:
        # Accept array format or string — just warn if it looks malformed
        if allowed_tools.startswith("[") and not allowed_tools.endswith("]"):
            issues.append({
                "plugin": plugin_name,
                "file": cmd_path.name,
                "issue": "allowed-tools may be malformed (should be array or string)",
                "severity": "WARNING",
            })

    # Check model if present
    model = fm.get("model", "")
    valid_models = {"inherit", "sonnet", "opus", "haiku"}
    if model and model not in valid_models:
        issues.append({
            "plugin": plugin_name,
            "file": cmd_path.name,
            "issue": f"command model '{model}' should be one of: {', '.join(valid_models)}",
            "severity": "WARNING",
        })

    # Check argument-hint is present for commands with parameters
    argument_hint = fm.get("argument-hint", "")
    desc = fm.get("description", "")
    if desc and "$1" in content and not argument_hint:
        issues.append({
            "plugin": plugin_name,
            "file": cmd_path.name,
            "issue": "command uses positional args ($1/$2) but missing argument-hint in frontmatter",
            "severity": "WARNING",
        })

    return issues


def audit_marketplace(marketplace_root: Path) -> list[dict]:
    """Audit marketplace.json, return list of issues."""
    issues = []
    mp_manifest = marketplace_root / ".claude-plugin" / "marketplace.json"

    if not mp_manifest.exists():
        issues.append({
            "plugin": "(marketplace)",
            "issue": ".claude-plugin/marketplace.json not found",
            "severity": "ERROR",
        })
        return issues

    mp_data = _load_json(mp_manifest)
    if mp_data is None:
        issues.append({
            "plugin": "(marketplace)",
            "issue": "marketplace.json is not valid JSON",
            "severity": "ERROR",
        })
        return issues

    if not mp_data.get("name"):
        issues.append({
            "plugin": "(marketplace)",
            "issue": "marketplace.json missing 'name' field",
            "severity": "ERROR",
        })

    plugins_list = mp_data.get("plugins", [])
    if not isinstance(plugins_list, list):
        issues.append({
            "plugin": "(marketplace)",
            "issue": "marketplace.json plugins is not an array",
            "severity": "ERROR",
        })
        return issues

    for entry in plugins_list:
        pname = entry.get("name", "(unnamed)")
        source = entry.get("source", "")

        if source and not source.startswith("./"):
            issues.append({
                "plugin": pname,
                "issue": f"source does not start with './': {source}",
                "severity": "WARNING",
            })

        if source:
            source_path = marketplace_root / source.replace("./", "")
            if not source_path.exists():
                issues.append({
                    "plugin": pname,
                    "issue": f"source path does not resolve: {source}",
                    "severity": "ERROR",
                })

    return issues


# === PART 2: Source path scan ===

# Patterns that indicate hardcoded absolute paths (not $CLAUDE_PLUGIN_ROOT or relative)
PATH_PATTERNS = [
    (re.compile(r"P:[/\\]"), "Hardcoded P:/ drive path — use $CLAUDE_PLUGIN_ROOT", "ERROR"),
    (re.compile(r"C:[/\\]Users[/\\]"), "Hardcoded Windows user profile — use $env:HOME or $env:USERPROFILE", "ERROR"),
    (re.compile(r"\$HOME[/\\]packages"), "Hardcoded $HOME/packages path — use $CLAUDE_PLUGIN_ROOT", "ERROR"),
    (re.compile(r"/p/packages/"), "Hardcoded /p/packages/ path — use $CLAUDE_PLUGIN_ROOT", "ERROR"),
    (re.compile(r"/p\\packages\\", re.IGNORECASE), "Hardcoded /p/packages/ path (backslashes) — use $CLAUDE_PLUGIN_ROOT", "ERROR"),
    (re.compile(r"~[/\\]packages"), "Hardcoded ~/packages path — use $CLAUDE_PLUGIN_ROOT", "ERROR"),
    (re.compile(r"/home/"), "Hardcoded Unix home path — use $env:HOME", "WARNING"),
    (re.compile(r"\\\\{2,}[A-Za-z]:"), "Double-backslash absolute path — malformed", "WARNING"),
]

# Directories to skip during path scan
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "tests", "examples", "docs", "assets", "badges", ".github", ".benchmarks"}

# File extensions to scan
SCAN_EXTENSIONS = {".md", ".py", ".sh", ".ps1", ".json", ".txt", ".yml", ".yaml"}


def scan_hardcoded_paths(plugins_dir: Path) -> list[dict]:
    """Scan plugin source files for hardcoded paths."""
    path_issues = []

    for plugin_link in plugins_dir.iterdir():
        if plugin_link.is_symlink() and not plugin_link.exists():
            continue
        if plugin_link.is_symlink():
            plugin_dir = plugin_link.resolve()
        elif plugin_link.is_dir():
            plugin_dir = plugin_link
        else:
            continue

        if plugin_link.name in SKIP_DIRS:
            continue

        for root, dirs, files in os.walk(plugin_dir):
            # Prune skip dirs in-place
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

            rel_root = Path(root).relative_to(plugin_dir)
            if rel_root.parts and rel_root.parts[0] in SKIP_DIRS:
                continue

            for file in files:
                ext = Path(file).suffix.lower()
                if ext not in SCAN_EXTENSIONS:
                    continue
                file_path = Path(root) / file
                try:
                    content = file_path.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue

                for pattern, reason, severity in PATH_PATTERNS:
                    if pattern.search(content):
                        rel_path = str(file_path.relative_to(plugin_dir))
                        path_issues.append({
                            "plugin": plugin_link.name,
                            "file": file,
                            "path": rel_path,
                            "issue": reason,
                            "severity": severity,
                            "pattern": pattern.pattern,
                        })

    return path_issues


# === PART 2b: Python import/module verification ===

def _parse_py_ast(file_path: Path) -> Optional[ast.AST]:
    """Parse a Python file, return AST or None on failure."""
    try:
        with open(file_path, encoding="utf-8") as f:
            source = f.read()
        return ast.parse(source, filename=str(file_path))
    except (SyntaxError, OSError):
        return None


def _get_module_path(parent_dir: Path, import_path: str) -> Optional[Path]:
    """Resolve a dotted import path to a .py file relative to parent_dir.

    e.g. parent_dir="scripts/hooks/__lib/", import_path="snapshot_v2"
    looks for scripts/hooks/__lib/snapshot_v2.py
    """
    parts = import_path.split(".")
    candidate = parent_dir / Path(*parts).with_suffix(".py")
    if candidate.exists():
        return candidate
    # Also check package __init__ (e.g. package.submodule -> package/__init__.py)
    if len(parts) > 1:
        candidate = parent_dir / Path(*parts[:-1]) / "__init__.py"
        if candidate.exists():
            return candidate
    return None


def _extract_class_names(file_path: Path) -> set[str]:
    """Extract all Python class names defined in a file."""
    classes = set()
    tree = _parse_py_ast(file_path)
    if tree is None:
        return classes
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.add(node.name)
    return classes


def _extract_imports(file_path: Path) -> list[tuple[str, str]]:
    """Extract (module_path, names) from 'from X import Y, Z' and 'import X.Y'.

    Returns list of (module_path, imported_name).
    e.g. 'from scripts.hooks.__lib.snapshot_v2 import compute_checksum'
         -> ('scripts.hooks.__lib.snapshot_v2', 'compute_checksum')
    """
    imports = []
    tree = _parse_py_ast(file_path)
    if tree is None:
        return imports

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.module is None:
                continue
            for alias in node.names:
                imports.append((node.module, alias.name))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                # 'import os.path' -> module='os.path', name='os.path'
                imports.append((alias.name, alias.name.split(".")[-1]))

    return imports


def scan_python_imports(plugins_dir: Path) -> list[dict]:
    """Scan Python files for import-to-module mismatches.

    Detects:
    - Imports from modules that don't exist within the plugin (renamed modules)
    - Class/function imports where the symbol isn't defined in the source module
    - Relative imports that can't resolve

    Skips: stdlib modules, __future__, and third-party packages (pip-installed).
    Only flags imports that reference plugin-internal modules that don't exist.
    """
    # Complete stdlib module list — skip these as they're not plugin-internal issues
    STDLIB_MODULES = {
        # Built-in
        "os", "sys", "json", "re", "logging", "pathlib", "datetime", "typing",
        "collections", "contextlib", "copy", "io", "iobuiltins", "builtins",
        "stat", " tempfile", "warnings", "weakref", "gc", " threading", "multiprocessing",
        "queue", "marshal", "platform", "errno", "signal", "socket", "ssl",
        "select", "selectors", "asyncio", "concurrent", "concurrent.futures",
        "subprocess", "sched", "contextvars", "dataclasses", "enum", "graphlib",
        "zoneinfo", "zoneinfo.available", "pprint", "copyreg", "shelve", "pickle",
        "struct", "csv", "configparser", "tomllib", "urllib", "urllib.request",
        "urllib.parse", "urllib.error", "urllib.robotparser", "http", "http.client",
        "http.server", "http.cookies", "http.cookiejar", "html", "html.parser",
        "xml", "xml.etree", "xml.etree.ElementTree", "xml.dom", "xml.dom.minidom",
        "xml.dom.pulldom", "xml.sax", "xml.sax.reader", "xml.sax.handler",
        "xml.sax.utils", "xml.sax.xmlreader", "xml.dom.expattrib",
        "cryptography", "zipfile", "tarfile", "gzip", "bz2", "lzma", "zipimport",
        "pkgutil", "modulefinder", "runpy", "importlib", "importlib.abc",
        "importlib.machinery", "importlib.resources", "importlib.util",
        "__future__", "ast", "sysconfig", "types", "functools", "inspect",
        "dis", "opcode", "tokenize", "keyword", "astutil", "symtable", "token",
        "linecache", "textwrap", "unicodedata", "string", "stringprep",
        "locale", "curses", "curses.panel", "difflib", "heapq", "bisect",
        "array", "collections.abc", "reprlib", "types", "typing_extensions",
        "filepath", "fnmatch", "glob", "tempfile", "shutil", "argparse",
        "getopt", "logging", "logging.config", "logging.handlers", "mailbox",
        "mmap", "msvcrt", "ncurses", "tty", "tty.template", "termios",
        "fcntl", "resource", "nis", "optparse", "os.path", "pathlib",
        "pdb", "bdb", "cmd", "shlex", "pexpect", "pty", "tty", "pty.template",
        "wave", "chunk", "imghdr", "sndhdr", "ossaudiodev", "machin",
        "MacOS", "msilib", "winreg", "winsound", "posix", "pwd", "spwd",
        "grp", "grp.nis", "tty", "termios", "pty", "fcntl", "pwd",
        "resource", "syslog", "sysv_msgsnd", "sysv_msg", "sysv_sem",
        "sysv_shm", "sem", "shm", "termios", "types", "hashlib", "hmac",
        "md5", "sha1", "sha256", "sha512", "blake2", "blake2b", "blake2s",
        "crypt", "passlib", "secrets", "uuid", "secrets", "random", "math",
        "cmath", "decimal", "fractions", "numbers", "random", "statistics",
        "itertools", "product", "combinations", "permutations", "accumulate",
        "groupby", "sliding_window", "compress", "count", "cycle", "dropwhile",
        "filterfalse", "flatten", "islice", "pairwise", "tee", "takewhile",
        "zip_longest", "operator", "itemgetter", "attrgetter", "methodcaller",
        "pathlib", "posixpath", "ntpath", "macpath", "os.path",
        "time", "zoneinfo", "calendar", "timeit", "traceback", "tracemalloc",
        "gc", "sys", "sys.monitoring", "sys.setrecursionlimit", "sys.settrace",
        "atexit", "faulthandler", "tests", "ctypes", "ctypes.util", "ctypes.macholib",
        "uuid", "os", "re", "difflib",
        # pip-installed common packages — skip these too as they're not plugin-internal
        "litellm", "dotenv", "yaml", "jsonschema", "pydantic", "pydantic_core",
        "fastapi", "starlette", "requests", "httpx", "aiohttp", "websockets",
        "tenacity", "tiktoken", "anthropic", "openai", "google", "mistral",
        "groq", "together", "ai21", "cohere", "instructor", "ragas",
        "pandas", "numpy", "polars", "duckdb", "sqlalchemy", "psycopg2",
        "redis", "memcache", "pymongo", "elasticsearch",
        "pytest", "pytest_asyncio", "pytest_mock", "coverage", "ruff", "mypy",
        "black", "isort", "pre_commit", "tox", "nox",
        "flask", "django", "fastapi", "starlette", "streamlit", "gradio",
        "notebook", "jupyter", "ipython", "ipykernel",
        "browser_use", "playwright", "selenium", "beautifulsoup4", "lxml",
        "pillow", "opencv-python", "numpy", "scipy", "sklearn",
        "transformers", "torch", "tensorflow", "onnx",
    }

    issues = []

    for plugin_link in plugins_dir.iterdir():
        if plugin_link.is_symlink() and not plugin_link.exists():
            continue
        if plugin_link.is_symlink():
            plugin_dir = plugin_link.resolve()
        elif plugin_link.is_dir():
            plugin_dir = plugin_link
        else:
            continue

        if plugin_link.name in SKIP_DIRS:
            continue

        # Build a map: file_path -> set of class names it defines
        all_files: dict[Path, set[str]] = {}

        for root, dirs, files in os.walk(plugin_dir):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            rel_root = Path(root).relative_to(plugin_dir)
            if rel_root.parts and rel_root.parts[0] in SKIP_DIRS:
                continue

            for file in files:
                if not file.endswith(".py"):
                    continue
                file_path = Path(root) / file
                all_files[file_path] = _extract_class_names(file_path)

        # Now check each Python file for import issues
        for file_path, defined_classes in all_files.items():
            file_imports = _extract_imports(file_path)
            parent_dir = file_path.parent

            for module_path, imported_name in file_imports:
                # Skip: stdlib, __future__, and third-party packages
                root_module = module_path.split(".")[0]
                if root_module in STDLIB_MODULES or module_path in STDLIB_MODULES:
                    continue

                # Resolve module path relative to plugin root
                # Always search from plugin_dir since all plugin packages are under it
                try:
                    rel_file = file_path.relative_to(plugin_dir)
                except ValueError:
                    continue

                # Use plugin root as search base for all internal imports
                search_base = plugin_dir

                # Convert module_path to file path and check
                module_file = _get_module_path(search_base, module_path)

                if module_file is None:
                    # Check if maybe the file exists but with different name
                    possible = search_base / Path(module_path.replace(".", "/") + ".py")
                    if not possible.exists():
                        issues.append({
                            "plugin": plugin_link.name,
                            "file": str(rel_file),
                            "symbol": imported_name,
                            "issue": f"imports '{module_path}' which does not exist (module renamed or deleted?)",
                            "severity": "ERROR",
                            "module": module_path,
                        })
                    continue

                # Check if the imported symbol is actually defined in the target module
                actual_classes = _extract_class_names(module_file)
                tree = _parse_py_ast(module_file)
                functions = set()
                if tree:
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            functions.add(node.name)
                if imported_name not in actual_classes and imported_name not in functions:
                    issues.append({
                        "plugin": plugin_link.name,
                        "file": str(rel_file),
                        "symbol": imported_name,
                        "issue": f"imports '{imported_name}' from '{module_path}' but it is not defined there (class/function renamed or deleted?)",
                        "severity": "ERROR",
                        "module": module_path,
                    })

    return issues


# === PART 3: Auto-fix ===

def auto_fix_plugins(plugins_dir: Path, delete_hooks: bool) -> list[dict]:
    """Auto-fix manifest issues, return list of fixed plugins."""
    fixed = []

    for plugin_link in plugins_dir.iterdir():
        if plugin_link.is_symlink() and not plugin_link.exists():
            continue
        if plugin_link.is_symlink():
            plugin_dir = plugin_link.resolve()
        elif plugin_link.is_dir():
            plugin_dir = plugin_link
        else:
            continue

        manifest_path = plugin_dir / ".claude-plugin" / "plugin.json"
        hooks_path = plugin_dir / "hooks" / "hooks.json"
        changed = False

        if manifest_path.exists():
            manifest = _load_json(manifest_path)
            if manifest is not None:
                # Fix 1: Remove invalid skills array
                if "skills" in manifest and isinstance(manifest["skills"], list):
                    has_names = any(
                        isinstance(s, str) and not s.startswith("./")
                        for s in manifest["skills"]
                    )
                    if has_names:
                        del manifest["skills"]
                        changed = True

                # Fix 2: Remove marketplace-only fields
                for field in ("source", "category"):
                    if field in manifest:
                        del manifest[field]
                        changed = True

                if changed:
                    _save_json(manifest_path, manifest)
                    fixed.append(plugin_link.name)

        # Fix 3: Delete or fix hooks.json
        if hooks_path.exists():
            if delete_hooks:
                hooks_path.unlink()
                fixed.append(f"{plugin_link.name} (hooks.json deleted)")
            else:
                hooks_json = _load_json(hooks_path)
                if hooks_json is None or not isinstance(hooks_json, dict) or hooks_json.get("hooks") is None:
                    _save_json(hooks_path, {"hooks": {}})
                    fixed.append(f"{plugin_link.name} (hooks.json fixed)")

    return fixed


# === OUTPUT ===

def green(msg: str) -> str:
    return f"\033[92m{msg}\033[0m"


def yellow(msg: str) -> str:
    return f"\033[93m{msg}\033[0m"


def red(msg: str) -> str:
    return f"\033[91m{msg}\033[0m"


def cyan(msg: str) -> str:
    return f"\033[96m{msg}\033[0m"


def report_issues(issues: list[dict], title: str) -> None:
    errors = [i for i in issues if i["severity"] == "ERROR"]
    warnings = [i for i in issues if i["severity"] == "WARNING"]

    print(cyan(f"\n=== {title} ==="))
    if not issues:
        print(green("  No issues found"))
        return

    print(yellow(f"  ERRORS: {len(errors)} | WARNINGS: {len(warnings)}"))
    for issue in issues:
        color = red if issue["severity"] == "ERROR" else yellow
        print(f"  [{issue['severity']:8}] {issue['plugin']}: {issue['issue']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit and auto-fix Claude Code plugin manifests.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python plugin-audit-and-fix.py                      Default manifest audit
  python plugin-audit-and-fix.py --auto-fix           Auto-fix manifest issues
  python plugin-audit-and-fix.py --scan-paths          Scan source for hardcoded paths
  python plugin-audit-and-fix.py --check-imports       Check Python import/module consistency
  python plugin-audit-and-fix.py --scan-paths --check-imports  Full source audit
  python plugin-audit-and-fix.py --delete-hooks        Delete hooks.json instead of fixing
        """,
    )
    parser.add_argument(
        "--marketplace-root",
        help="Override marketplace root path",
    )
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Automatically fix manifest issues",
    )
    parser.add_argument(
        "--delete-hooks",
        action="store_true",
        help="Delete hooks.json files instead of fixing structure",
    )
    parser.add_argument(
        "--scan-paths",
        action="store_true",
        help="Scan plugin source files for hardcoded absolute paths",
    )
    parser.add_argument(
        "--check-imports",
        action="store_true",
        help="Verify Python import statements resolve to existing modules/classes",
    )
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    mp_root = _detect_marketplace_root(script_path, args.marketplace_root)
    plugins_dir = mp_root / "plugins"

    print(cyan("=== Claude Code Plugin Audit & Fix ==="))
    print(f"Marketplace: {mp_root}")

    if not plugins_dir.exists():
        print(red(f"ERROR: plugins directory not found at {plugins_dir}"))
        sys.exit(1)

    # Part 1: Manifest audit
    print(cyan("\nPART 1: Auditing manifests..."))
    plugin_issues = audit_plugins(plugins_dir, mp_root)
    mp_issues = audit_marketplace(mp_root)
    all_issues = plugin_issues + mp_issues

    errors = [i for i in all_issues if i["severity"] == "ERROR"]
    warnings = [i for i in all_issues if i["severity"] == "WARNING"]

    if not all_issues:
        print(green("  All manifests valid"))
    else:
        print(yellow(f"  ERRORS: {len(errors)} | WARNINGS: {len(warnings)}"))
        for issue in all_issues:
            color = red if issue["severity"] == "ERROR" else yellow
            print(f"  [{issue['severity']:8}] {issue['plugin']}: {issue['issue']}")

    # Part 2: Source path scan
    if args.scan_paths:
        print(cyan("\nPART 2: Scanning for hardcoded paths..."))
        path_issues = scan_hardcoded_paths(plugins_dir)
        if not path_issues:
            print(green("  No hardcoded paths found"))
        else:
            path_errors = [p for p in path_issues if p["severity"] == "ERROR"]
            path_warns = [p for p in path_issues if p["severity"] == "WARNING"]
            print(yellow(f"  Hardcoded paths: ERRORS: {len(path_errors)} | WARNINGS: {len(path_warns)}"))
            for pi in path_issues:
                color = red if pi["severity"] == "ERROR" else yellow
                print(f"  [{pi['severity']:8}] {pi['plugin']}/{pi['file']}: {pi['issue']}")
            all_issues.extend(path_issues)

    # Part 2b: Python import verification
    if args.check_imports:
        print(cyan("\nPART 2b: Verifying Python imports..."))
        import_issues = scan_python_imports(plugins_dir)
        if not import_issues:
            print(green("  All imports valid"))
        else:
            imp_errors = [p for p in import_issues if p["severity"] == "ERROR"]
            print(yellow(f"  Import issues: ERRORS: {len(imp_errors)}"))
            for pi in import_issues:
                print(f"  [{pi['severity']:8}] {pi['plugin']}/{pi['file']}: {pi['issue']}")
            all_issues.extend(import_issues)

    # Part 3: Auto-fix
    if args.auto_fix:
        print(cyan("\nPART 3: Auto-fixing issues..."))
        fixed = auto_fix_plugins(plugins_dir, args.delete_hooks)
        if fixed:
            for f in fixed:
                print(f"  Fixed: {f}")
        else:
            print(yellow("  Nothing to fix"))

    # Summary
    print(cyan("\n=== Summary ==="))
    final_errors = [i for i in all_issues if i["severity"] == "ERROR"]
    final_warnings = [i for i in all_issues if i["severity"] == "WARNING"]
    if not final_errors:
        print(green(f"  All checks passed ({len(final_warnings)} warnings)"))
    else:
        print(red(f"  {len(final_errors)} errors, {len(final_warnings)} warnings — run with --auto-fix"))

    print(cyan("\n=== Next Steps ==="))
    if final_errors or final_warnings:
        print("  1. Run with --auto-fix to automatically fix safe issues")
        print("  2. Run with --scan-paths to check source files")
        print("  3. Update marketplace: /plugin marketplace update local")
    else:
        print("  1. Update marketplace: /plugin marketplace update local")


if __name__ == "__main__":
    main()
