#!/usr/bin/env python3
"""CLI detection utilities for /ai-cli health checks.

Provides functions to detect and validate CLI tool installations.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

# Platform detection
IS_WINDOWS = sys.platform == "win32"

# CLI definitions with platform-specific invocation patterns
CLI_TOOLS = {
    "qwen": {
        "name": "qwen-code",
        "command": "qwen",
        "description": "Chutes Qwen3 235B (analysis)",
        "install": "npm install -g qwen-code",
        "npm_package": "@qwen-code/qwen-code",
        "npm_script": "cli.js",
        "type": "npm",
    },
    "gemini": {
        "name": "gemini-cli",
        "command": "gemini",
        "description": "Google Gemini CLI (1M+ tokens)",
        "install": "npm install -g gemini-cli",
        "npm_package": "@google/gemini-cli",
        "npm_script": "dist/index.js",
        "type": "npm",
    },
    "codex": {
        "name": "codex-cli",
        "command": "codex",
        "description": "OpenRouter DeepSeek R1T2 Chimera (coding)",
        "install": "npm install -g @openai/codex",
        "npm_package": "@openai/codex",
        "npm_script": "bin/codex.js",
        "type": "npm",
    },
    "vibe": {
        "name": "vibe",
        "command": "vibe",
        "description": "Mistral AI Vibe (Python tasks)",
        "install": "npm install -g @mistralai/vibe",
        "npm_package": "@mistralai/vibe",
        "npm_script": "dist/index.js",
        "type": "npm",
    },
    "pi": {
        "name": "pi-coding-agent",
        "command": "pi",
        "description": "Pi coding agent (multi-provider)",
        "install": "npm install -g @mariozechner/pi-coding-agent",
        "npm_package": "@mariozechner/pi-coding-agent",
        "npm_script": "dist/cli.js",
        "type": "npm",
    },
}

# Environment variable requirements
ENV_VARS = {
    "CHUTES_API_KEY": "OpenCode API access",  # pragma: allowlist secret
    "ZAI_API_KEY": "GLM-4.7-Flash API access (optional)",  # pragma: allowlist secret
}


def _get_npm_root() -> Path:
    """Get the npm root directory for global packages."""
    if IS_WINDOWS:
        return Path.home() / "AppData" / "Roaming" / "npm" / "node_modules"
    else:
        return Path.home() / ".npm-global" / "lib" / "node_modules"


def _get_npm_cli_path(cli_info: dict[str, Any]) -> Path | None:
    """Get the path to an npm-installed CLI script.

    Args:
        cli_info: CLI tool definition dictionary

    Returns:
        Path to the CLI script or None
    """
    if cli_info["type"] != "npm":
        return None

    npm_root = _get_npm_root()
    npm_package = cli_info["npm_package"]
    npm_script = cli_info["npm_script"]

    # Try the package directory
    package_path = npm_root / npm_package / npm_script
    if package_path.exists():
        return package_path

    # Try alternative locations (some CLIs have different structures)
    # For vibe, try the dist directory
    if cli_info["command"] == "vibe":
        alt_path = npm_root / "@mistralai/vibe" / "dist" / "index.js"
        if alt_path.exists():
            return alt_path

    # For gemini, the CLI is in bundle/ not dist/
    if cli_info["command"] == "gemini":
        alt_path = npm_root / "@google/gemini-cli/bundle/gemini.js"
        if alt_path.exists():
            return alt_path

    return None


def _build_cli_command(cli_id: str, cli_info: dict[str, Any]) -> list[str]:
    """Build the platform-specific command to invoke a CLI.

    Args:
        cli_id: CLI identifier
        cli_info: CLI tool definition dictionary

    Returns:
        List of command parts (e.g., ["node", "path/to/cli.js", "--version"])
    """
    if cli_info["type"] == "npm" and IS_WINDOWS:
        # Windows npm CLI: use node with script path
        script_path = _get_npm_cli_path(cli_info)
        if script_path:
            return ["node", str(script_path)]
        else:
            # Fallback: try the command directly
            return [cli_info["command"]]
    else:
        # Unix or pip-installed: use command directly
        return [cli_info["command"]]


def _run_cli_command(cli_id: str, command_parts: list[str], timeout: int = 10) -> dict[str, Any]:
    """Run a CLI command and capture the result.

    Args:
        cli_id: CLI identifier
        command_parts: List of command parts
        timeout: Timeout in seconds

    Returns:
        Dictionary with success, stdout, stderr, exit_code
    """
    try:
        result = subprocess.run(
            command_parts + ["--version"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Timeout after {timeout}s",
            "exit_code": -1,
        }
    except FileNotFoundError:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Command not found",
            "exit_code": -2,
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "exit_code": -3,
        }


def _extract_version(output: str) -> str | None:
    """Extract version from CLI output.

    Args:
        output: stdout from --version command

    Returns:
        Version string or None
    """
    if not output:
        return None

    # Take first non-empty line
    for line in output.strip().split("\n"):
        line = line.strip()
        if line:
            return line

    return None


def check_cli_installation(cli_id: str) -> dict[str, Any]:
    """Check if a CLI tool is installed and accessible.

    Args:
        cli_id: CLI identifier (qwen, gemini, codex, vibe, opencode)

    Returns:
        Dictionary with keys:
            - installed: bool
            - version: str | None
            - path: str | None
            - error: str | None
            - command: str (the command used to invoke the CLI)
    """
    if cli_id not in CLI_TOOLS:
        return {
            "installed": False,
            "version": None,
            "path": None,
            "error": f"Unknown CLI: {cli_id}",
            "command": None,
        }

    cli_info = CLI_TOOLS[cli_id]

    # Build the platform-specific command
    command_parts = _build_cli_command(cli_id, cli_info)
    command_str = " ".join(command_parts)

    # Try to run --version
    result = _run_cli_command(cli_id, command_parts)

    if result["success"]:
        version = _extract_version(result["stdout"])
        return {
            "installed": True,
            "version": version,
            "path": command_str,
            "error": None,
            "command": command_str,
        }
    else:
        # Check if the files exist even if --version failed
        path_exists = False
        cli_path = None

        if cli_info["type"] == "npm":
            script_path = _get_npm_cli_path(cli_info)
            if script_path:
                path_exists = True
                cli_path = str(script_path)
        else:
            cmd_path = shutil.which(cli_info["command"])
            if cmd_path:
                path_exists = True
                cli_path = cmd_path

        error_msg = result["stderr"] if result["stderr"] else "Unknown error"

        if path_exists:
            return {
                "installed": False,
                "version": None,
                "path": cli_path,
                "error": f"Found at {cli_path} but not working: {error_msg}",
                "command": command_str,
            }
        else:
            return {
                "installed": False,
                "version": None,
                "path": None,
                "error": f"Not installed: {error_msg}",
                "command": command_str,
            }


def check_env_vars() -> dict[str, dict[str, Any]]:
    """Check environment variable status.

    Returns:
        Dictionary with env var names as keys, each containing:
            - set: bool
            - description: str
    """
    result = {}
    for var_name, description in ENV_VARS.items():
        result[var_name] = {
            "set": bool(os.environ.get(var_name)),
            "description": description,
        }
    return result


def get_all_cli_status() -> dict[str, dict[str, Any]]:
    """Get status of all CLI tools.

    Returns:
        Dictionary with CLI IDs as keys, containing installation status
    """
    result = {}
    for cli_id in CLI_TOOLS:
        result[cli_id] = check_cli_installation(cli_id)
    return result


def format_cli_status_table(status: dict[str, dict[str, Any]]) -> str:
    """Format CLI status as a readable table.

    Args:
        status: Dictionary from get_all_cli_status()

    Returns:
        Formatted table string
    """
    lines = []
    lines.append("📋 CLI Tool Status:")
    lines.append("")

    for cli_id, info in status.items():
        cli_def = CLI_TOOLS[cli_id]
        installed = info["installed"]
        version = info.get("version")
        path = info.get("path")
        error = info.get("error")
        command = info.get("command")

        icon = "✅" if installed else "❌"
        lines.append(f"  {icon} {cli_id:12} ({cli_def['name']})")
        lines.append(f"     Description: {cli_def['description']}")

        if installed:
            if version:
                lines.append(f"     Version:     {version}")
            if command:
                lines.append(f"     Command:     {command}")
            if path and path != command:
                lines.append(f"     Path:        {path}")
        else:
            if error:
                lines.append(f"     Status:      {error}")
            lines.append(f"     Install:     {cli_def['install']}")

        lines.append("")

    return "\n".join(lines)


def format_env_var_status(env_status: dict[str, dict[str, Any]]) -> str:
    """Format environment variable status as a readable table.

    Args:
        env_status: Dictionary from check_env_vars()

    Returns:
        Formatted table string
    """
    lines = []
    lines.append("🔑 Environment Variables:")
    lines.append("")

    for var_name, info in env_status.items():
        icon = "✅" if info["set"] else "❌"
        status_text = "is set" if info["set"] else "not set"
        lines.append(f"  {icon} {var_name}")
        lines.append(f"     Description: {info['description']}")
        lines.append("")

    return "\n".join(lines)
