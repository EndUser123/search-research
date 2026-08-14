#!/usr/bin/env python3
"""CKS Validation Configuration CLI.

Manage validation configuration for blocking mode and auto-detection.

Usage:
    python config_cli.py show              # Show current config
    python config_cli.py enable-blocking   # Enable blocking mode
    python config_cli.py disable-blocking  # Disable blocking mode
    python config_cli.py enable-auto       # Enable auto-detection
    python config_cli.py disable-auto      # Disable auto-detection
"""

from pathlib import Path

# Add parent to path for imports
parent = Path(__file__).parent

from features.config import get_config, set_config


def cmd_show(args) -> None:
    """Show current configuration."""
    config = get_config()
    print("📋 CKS Validation Configuration:")
    print(f"   Blocking Mode: {'🔴 ENABLED' if config.blocking_mode else '🟢 Disabled'}")
    print(
        f"   Auto-Detect Context: {'✅ Enabled' if config.auto_detect_context else '❌ Disabled'}"
    )
    print(f"   Require Confirmation: {'✅ Yes' if config.require_confirmation else '❌ No'}")
    print()
    print("Environment override: CKS_BLOCKING_MODE=true/false")


def cmd_enable_blocking(args) -> None:
    """Enable blocking mode."""
    config = get_config()
    config.blocking_mode = True
    config.to_file()
    set_config(config)
    print("✅ Blocking mode ENABLED")
    print("   Operations that don't match active context will be blocked")
    print("   Use 'disable-blocking' to disable")


def cmd_disable_blocking(args) -> None:
    """Disable blocking mode."""
    config = get_config()
    config.blocking_mode = False
    config.to_file()
    set_config(config)
    print("✅ Blocking mode DISABLED")
    print("   Context mismatches will generate warnings only")
    print("   Use 'enable-blocking' to enable")


def cmd_enable_auto(args) -> None:
    """Enable auto-detection."""
    config = get_config()
    config.auto_detect_context = True
    config.to_file()
    set_config(config)
    print("✅ Auto-detection ENABLED")


def cmd_disable_auto(args) -> None:
    """Disable auto-detection."""
    config = get_config()
    config.auto_detect_context = False
    config.to_file()
    set_config(config)
    print("✅ Auto-detection DISABLED")


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="CKS Validation Configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python config_cli.py show              # Show current config
    python config_cli.py enable-blocking   # Enable blocking mode
    python config_cli.py disable-blocking  # Disable blocking mode
        """,
    )

    parser.add_argument(
        "action",
        choices=[
            "show",
            "enable-blocking",
            "disable-blocking",
            "enable-auto",
            "disable-auto",
        ],
        help="Action to perform",
    )

    args = parser.parse_args()

    if args.action == "show":
        cmd_show(args)
    elif args.action == "enable-blocking":
        cmd_enable_blocking(args)
    elif args.action == "disable-blocking":
        cmd_disable_blocking(args)
    elif args.action == "enable-auto":
        cmd_enable_auto(args)
    elif args.action == "disable-auto":
        cmd_disable_auto(args)


if __name__ == "__main__":
    main()
