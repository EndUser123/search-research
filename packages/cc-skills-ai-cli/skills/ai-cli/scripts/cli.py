#!/usr/bin/env python3
"""
AI-CLI Health Check - CLI tool availability and configuration checks.

Provides health and list subcommands for checking CLI tool status.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# Flexible import for cli_detector - handles both module and direct execution
try:
    from . import cli_detector  # When run as module
except ImportError:
    # When run directly, add scripts dir to path
    scripts_dir = Path(__file__).parent
    sys.path.insert(0, str(scripts_dir))
    import cli_detector


def cmd_health(args: argparse.Namespace) -> int:
    """Check CLI tool health and availability.

    Returns exit code 0 if all checked CLIs are healthy, 1 if any fail.
    """
    # Get CLI status
    cli_status = cli_detector.get_all_cli_status()
    env_status = cli_detector.check_env_vars()

    # Determine what to check
    if args.cli:
        # Check specific CLI
        clis_to_check = [args.cli]
        if args.cli not in cli_detector.CLI_TOOLS:
            print(f"❌ Unknown CLI: {args.cli}", file=sys.stderr)
            print(f"Available CLIs: {', '.join(cli_detector.CLI_TOOLS.keys())}", file=sys.stderr)
            return 1
    else:
        # Check all CLIs
        clis_to_check = list(cli_detector.CLI_TOOLS.keys())

    all_healthy = True
    results = {}

    # Check each CLI
    for cli_id in clis_to_check:
        status = cli_status[cli_id]
        cli_def = cli_detector.CLI_TOOLS[cli_id]

        if args.sanity and status["installed"]:
            # Run sanity check with actual CLI
            print(f"🔍 Checking {cli_def['name']}...", end=" ")

            # Use the platform-specific command from status detection
            # For npm CLIs on Windows, this is ["node", "path/to/script.js"]
            # For other CLIs, this is ["command"]
            sanity_command = status["command"]
            if isinstance(sanity_command, str):
                sanity_command = sanity_command.split()

            try:
                result = subprocess.run(
                    sanity_command + ["--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    version = (
                        result.stdout.strip().split("\n")[0] if result.stdout.strip() else "OK"
                    )
                    print(f"[OK] ({version})")
                    results[cli_id] = "healthy"
                else:
                    print("[FAIL]")
                    print(f"  ❌ Exit code {result.returncode}")
                    results[cli_id] = "failed"
                    all_healthy = False
            except subprocess.TimeoutExpired:
                print("[TIMEOUT]")
                print("  ⚠️  Timeout after 10s")
                results[cli_id] = "timeout"
                all_healthy = False
            except FileNotFoundError:
                print("[NOT FOUND]")
                cmd_display = (
                    sanity_command[0] if isinstance(sanity_command, list) else sanity_command
                )
                print(f"  ❌ {cmd_display} not found")
                results[cli_id] = "not_found"
                all_healthy = False
            except Exception as e:
                print("[ERROR]")
                print(f"  ❌ {e}")
                results[cli_id] = "error"
                all_healthy = False
        else:
            # Just check installation status
            if status["installed"]:
                results[cli_id] = "installed"
            else:
                results[cli_id] = "not_installed"
                all_healthy = False

    # Print summary
    print()
    if all_healthy:
        print("✅ All checked CLIs are healthy")
    else:
        print("❌ Some CLIs failed health check")
        print("\nStatus:")
        for cli_id, status in results.items():
            status_icon = "✅" if status in ("healthy", "installed") else "❌"
            print(f"  {status_icon} {cli_id}: {status}")

    # Check environment variables
    print()
    print("🔑 Environment Variables:")
    for var_name, info in env_status.items():
        icon = "✅" if info["set"] else "❌"
        status_text = "is set" if info["set"] else "not set"
        print(f"  {icon} {var_name}: {status_text}")

    return 0 if all_healthy else 1


def cmd_models(args: argparse.Namespace) -> int:
    """Show available models for each CLI."""
    # OpenCode model aliases (from ai_cli.py)
    aliases = {
        "kimi": "chutes/moonshotai/Kimi-K2.5-TEE",
        "minimax": "chutes/MiniMaxAI/MiniMax-M2.1-TEE",
        "nemotron": "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
        "mimo": "chutes/XiaomiMiMo/MiMo-V2-Flash",
        "glm5": "zai-coding-plan/glm-5.1",
        "k2": "chutes/moonshotai/Kimi-K2.5-TEE",
        "deepseek-v3.2": "chutes/deepseek-ai/DeepSeek-V3.2-TEE",
        "deepseek-v3.2-tee": "chutes/deepseek-ai/DeepSeek-V3.2-TEE",
    }
    default_model = "chutes/deepseek-ai/DeepSeek-V3-0324-TEE"

    # Get CLI status for versions
    cli_status = cli_detector.get_all_cli_status()

    lines = []
    lines.append("🤖 AI-CLI Models")
    lines.append("")
    lines.append("OpenCode (configurable)")
    lines.append(f"  default   {default_model}")
    for alias, model in aliases.items():
        lines.append(f"  {alias:<8} {model}")

    lines.append("")
    lines.append("Fixed (no model selection)")
    for cli_id in ["qwen", "gemini", "codex", "vibe"]:
        status = cli_status[cli_id]
        version = status.get("version") or "unknown"
        cli_def = cli_detector.CLI_TOOLS[cli_id]
        name = cli_def["name"]
        # Strip tool name from version if it appears (e.g., "codex-cli 0.118.0" -> "0.118.0")
        if name in version:
            version = version.replace(name, "").strip()
        lines.append(f"  {cli_id:<6} {name} {version}")

    print("\n".join(lines))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List available CLI tools and their status."""
    # Get CLI and environment status
    cli_status = cli_detector.get_all_cli_status()
    env_status = cli_detector.check_env_vars()

    # Print CLI status table
    print(cli_detector.format_cli_status_table(cli_status))

    # Print environment variable status
    print(cli_detector.format_env_var_status(env_status))

    # Print summary
    installed_count = sum(1 for s in cli_status.values() if s["installed"])
    total_count = len(cli_status)
    print(f"Summary: {installed_count}/{total_count} CLIs installed")

    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser."""
    parser = argparse.ArgumentParser(
        prog="ai-cli",
        description="AI-CLI Health Check - Verify CLI tool availability and configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m .claude.skills.ai-cli.scripts.cli health
  python -m .claude.skills.ai-cli.scripts.cli health --sanity
  python -m .claude.skills.ai-cli.scripts.cli health --cli qwen
  python -m .claude.skills.ai-cli.scripts.cli list

Environment Variables:
  CHUTES_API_KEY        OpenCode API access (for opencode)
  ZAI_API_KEY           GLM-4.7-Flash API access (optional)

CLI Tools:
  qwen      qwen-code - Chutes Qwen3 235B (analysis)
  gemini    gemini-cli - Google Gemini CLI (1M+ tokens)
  codex     codex-cli - OpenRouter DeepSeek R1T2 Chimera (coding)
  vibe      @mistralai/vibe - Mistral AI Vibe (Python tasks)
  opencode  opencode-ai - OpenCode (planning/creative, 300+ models)

Installation:
  npm install -g qwen-code
  npm install -g gemini-cli
  pip install codex-cli
  npm install -g @mistralai/vibe
  npm install -g opencode-ai

Resources:
  /ai-cli    - Main skill for parallel LLM execution
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # health command
    health_parser = subparsers.add_parser("health", help="Check CLI tool health")
    health_parser.add_argument(
        "--cli",
        choices=list(cli_detector.CLI_TOOLS.keys()),
        help="Check specific CLI (default: all CLIs)",
    )
    health_parser.add_argument(
        "--sanity",
        action="store_true",
        help="Run sanity check with actual CLI execution",
    )

    # list command
    subparsers.add_parser("list", help="List all CLI tools and their status")

    # models command
    subparsers.add_parser("models", help="Show available models for each CLI")

    return parser


def main() -> int:
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "health":
        return cmd_health(args)
    elif args.command == "list":
        return cmd_list(args)
    elif args.command == "models":
        return cmd_models(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
