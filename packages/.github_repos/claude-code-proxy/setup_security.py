#!/usr/bin/env python3
"""
Security setup script for claude-code-proxy.

Configures secure file permissions, log encryption, and automated cleanup.
Run this once during initial setup.

Usage:
    python setup_security.py
"""

import os
import secrets
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# ANSI color codes for terminal output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def print_success(msg: str):
    print(f"{Colors.GREEN}✓{Colors.RESET} {msg}")


def print_error(msg: str):
    print(f"{Colors.RED}✗{Colors.RESET} {msg}", file=sys.stderr)


def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {msg}")


def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {msg}")


def set_file_permissions(filepath: str, mode: int) -> bool:
    """Set file permissions (Unix-style, Windows equivalent via icacls)."""
    if not os.path.exists(filepath):
        print_warning(f"File does not exist: {filepath}")
        return False

    if sys.platform == "win32":
        # Windows: Use icacls to grant Full Control only to current user
        try:
            # Get current user
            result = subprocess.run(["whoami"], capture_output=True, text=True, check=True)
            username = result.stdout.strip()

            # Grant Full Control to current user, deny everyone else
            subprocess.run(
                ["icacls", filepath, "/grant", f"{username}:F", "/inheritance:r"],
                capture_output=True,
                check=True,
            )
            print_success(f"Set permissions: {filepath} (owner-only)")
            return True
        except Exception as e:
            print_error(f"Failed to set permissions on {filepath}: {e}")
            return False
    else:
        # Unix: Use chmod
        try:
            os.chmod(filepath, mode)
            print_success(f"Set permissions: {filepath} ({oct(mode)})")
            return True
        except Exception as e:
            print_error(f"Failed to set permissions on {filepath}: {e}")
            return False


def generate_encryption_key() -> str:
    """Generate a secure encryption key for log encryption."""
    return secrets.token_urlsafe(32)


def setup_log_encryption() -> bool:
    """Set up environment variable for log encryption."""
    # Check if key already exists
    if os.environ.get("LOG_ENCRYPTION_KEY"):
        print_info("LOG_ENCRYPTION_KEY already set in environment")
        return True

    # Generate new key
    key = generate_encryption_key()

    # Create .env file with encryption key
    env_file = Path(".env")
    env_file_exists = env_file.exists()

    try:
        with open(env_file, "a") as f:
            if not env_file_exists:
                f.write("# claude-code-proxy security configuration\n")
                f.write(f"# Generated: {datetime.now().isoformat()}\n\n")
            f.write("# Log encryption key (AES-256-GCM)\n")
            f.write(f"LOG_ENCRYPTION_KEY={key}\n")

        print_success("Generated LOG_ENCRYPTION_KEY in .env")
        return True
    except Exception as e:
        print_error(f"Failed to create .env: {e}")
        return False


def create_cleanup_script() -> bool:
    """Create automated log cleanup script."""
    script_content = """#!/usr/bin/env python3
\"\"\"
Automated log cleanup script for claude-code-proxy.

Deletes log files older than RETENTION_DAYS days.
Run via cron or scheduled task.
\"\"\"

import os
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

# Configuration
RETENTION_DAYS = 7
LOG_EXTENSIONS = [".log", ".txt"]

def cleanup_old_logs():
    \"\"\"Remove log files older than RETENTION_DAYS.\"\"\"
    cutoff = datetime.now() - timedelta(days=RETENTION_DAYS)
    deleted_count = 0

    for log_file in Path(".").rglob("*"):
        if log_file.suffix in LOG_EXTENSIONS:
            # Check file modification time
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if mtime < cutoff:
                try:
                    log_file.unlink()
                    print(f"Deleted old log: {log_file}")
                    deleted_count += 1
                except Exception as e:
                    print(f"Failed to delete {log_file}: {e}", file=sys.stderr)

    if deleted_count == 0:
        print("No old logs to clean up")
    else:
        print(f"Cleanup complete: deleted {deleted_count} old log file(s)")

if __name__ == "__main__":
    cleanup_old_logs()
"""

    script_path = Path("cleanup_logs.py")
    try:
        with open(script_path, "w") as f:
            f.write(script_content)

        # Make executable on Unix
        if sys.platform != "win32":
            os.chmod(script_path, 0o755)

        print_success("Created cleanup_logs.py (run manually or schedule via cron)")
        return True
    except Exception as e:
        print_error(f"Failed to create cleanup script: {e}")
        return False


def create_scheduled_task() -> bool:
    """Create Windows scheduled task for log cleanup."""
    if sys.platform != "win32":
        print_info("Scheduled task setup is Windows-only (skipped on Unix)")
        return True

    script_path = Path("cleanup_logs.py").resolve()
    python_exe = sys.executable

    try:
        # Create scheduled task (runs daily at 2 AM)
        task_name = "claude-code-proxy-log-cleanup"
        task_cmd = f'schtasks /create /tn "{task_name}" /tr "python \\"{script_path}\\"" /sc daily /st 02:00'

        subprocess.run(task_cmd, shell=True, check=True, capture_output=True)
        print_success(f"Created scheduled task: {task_name}")
        return True
    except subprocess.CalledProcessError as e:
        print_warning(f"Failed to create scheduled task (may require admin): {e}")
        print_info("Run manually: python cleanup_logs.py")
        return False
    except Exception as e:
        print_error(f"Unexpected error creating scheduled task: {e}")
        return False


def verify_gitignore() -> bool:
    """Verify .gitignore excludes sensitive files."""
    gitignore_path = Path(".gitignore")
    required_patterns = ["*.env", "*.key", "config-*.yaml", "credentials.env", "*.log"]

    if not gitignore_path.exists():
        print_error(".gitignore not found")
        return False

    with open(gitignore_path) as f:
        gitignore_content = f.read()

    missing = []
    for pattern in required_patterns:
        if pattern not in gitignore_content:
            missing.append(pattern)

    if missing:
        print_warning(f".gitignore missing patterns: {', '.join(missing)}")
        return False

    print_success(".gitignore verified (all sensitive patterns excluded)")
    return True


def main():
    print("\n" + "=" * 60)
    print("claude-code-proxy Security Setup")
    print("=" * 60 + "\n")

    steps = [
        ("Verify .gitignore", verify_gitignore),
        ("Set up log encryption", setup_log_encryption),
        ("Create cleanup script", create_cleanup_script),
        ("Create scheduled task", create_scheduled_task),
    ]

    results = []
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        result = step_func()
        results.append((step_name, result))

    # Set permissions on existing sensitive files
    print("\n\nSetting secure permissions on sensitive files...")
    sensitive_patterns = ["*.env", "*.key", "*.db"]
    for pattern in sensitive_patterns:
        for filepath in Path(".").glob(pattern):
            set_file_permissions(str(filepath), 0o600)

    # Summary
    print("\n" + "=" * 60)
    print("Setup Summary")
    print("=" * 60)

    for step_name, result in results:
        status = (
            f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
        )
        print(f"  {status}: {step_name}")

    print("\nNext steps:")
    print("  1. Store API keys: python credential_manager.py set OPENAI_API_KEY sk-...")
    print("  2. Create terminal config: cp config.yaml.example config-terminal1.yaml")
    print("  3. Edit config: Set port, subagent mappings")
    print("  4. Start proxy: .\\run.sh (Windows) or ./run.sh (Unix)")
    print("  5. Run cleanup: python cleanup_logs.py (manual or scheduled)")
    print("")


if __name__ == "__main__":
    main()
