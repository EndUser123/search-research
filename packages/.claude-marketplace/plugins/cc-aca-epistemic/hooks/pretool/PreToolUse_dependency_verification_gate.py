#!/usr/bin/env python3
"""
PreToolUse_dependency_verification_gate.py - External Dependency Verification v2.1
=====================================================================================

Blocks Bash commands that reference external packages (npm, pip, cargo)
without prior verification that the package exists.

WHY THIS EXISTS:
  Prevents "lazy errors" where AI assumes package names or makes
  configuration changes without verifying external dependencies first.

FAILURE MODE CAUGHT:
  "Changed config to use @modelcontextprotocol/server-exa"
  -> No verification that package exists
  -> Gate blocks and demands verification first

PATTERNS DETECTED:
  - npm install @scope/package
  - pip install package-name
  - cargo add crate-name

VERIFICATION REQUIREMENT:
  Before running install/config commands, run verification:
  - npm: npm view package-name or npm search package-name
  - pip: pip index versions package-name or pip search package-name
  - cargo: cargo search crate-name

v2.1 IMPROVEMENTS:
  - Terminal-based state tracking (uses terminal_detection module)
  - Bypass mechanism (--bypass-dependency-verification flag)
  - Word-boundary regex for robust verification detection
  - Autonomous recovery guidance (clear LLM can continue with verification)

v2 CHANGES:
  - Session state tracking (5-min TTL for verified packages)
  - Word-boundary regex for robust verification detection

LIFECYCLE: PreToolUse (blocking gate -- exits with code 2 to block)

Configuration:
  DEPENDENCY_VERIFICATION_ENABLED=true to enable (default: false)
  DEPENDENCY_VERIFICATION_MODE=bypass to bypass checks (default: block)

State Management:
  Uses terminal_detection.detect_terminal_id() for session isolation
  State files: dependency_verification_{terminal_id}.json
"""
from __future__ import annotations



# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


import json
import logging
import os
import re
import shlex
import sys
import time
from pathlib import Path

# Import terminal_detection for session isolation (aligns with hooks codebase pattern)
sys.path.insert(0, str(Path("P:/packages/skill-guard/src")))
from __lib.terminal_detection import detect_terminal_id

# Logging
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Configuration
ENABLED = os.environ.get("DEPENDENCY_VERIFICATION_ENABLED", "false").lower() == "true"
VERIFICATION_TTL = 5 * 60  # 5 minutes in seconds

# State directory
HOOK_DIR = Path(__file__).resolve().parent
STATE_DIR = HOOK_DIR / "state"

# Ensure state directory exists once at module load (PERF-002 fix)
STATE_DIR.mkdir(exist_ok=True)

# Pre-compiled regex patterns for performance
NPM_INSTALL_PATTERN = re.compile(
    r"npm\s+(?:install|add|i)\s+(@?[\w.-]+/[\w.-]+|[\w.-]+)",
    re.IGNORECASE,
)

PIP_INSTALL_PATTERN = re.compile(
    r"(?:^|&&|\|\|)\s*(?:uv\s+)?pip\s+install\s+(.+?)(?=(?:&&|\|\||;)|$)",
    re.IGNORECASE,
)

CARGO_ADD_PATTERN = re.compile(
    r"cargo\s+add\s+([\w.-]+)",
    re.IGNORECASE,
)

# Local package patterns (should be allowed)
LOCAL_PACKAGE_PATTERNS = [
    re.compile(r"npm\s+install\s+\.\/", re.IGNORECASE),
    re.compile(r"npm\s+install\s+\.\.\/", re.IGNORECASE),
    re.compile(r"npm\s+install\s+file:", re.IGNORECASE),
    re.compile(r"npm\s+install\s+[\w.-]+\.tgz", re.IGNORECASE),
    re.compile(r"npm\s+install\s+[\w.-]+\.tar\.gz", re.IGNORECASE),
]

# Verification command patterns (word-boundary for robustness)
VERIFICATION_PATTERNS = {
    "npm": re.compile(r"\bnpm\s+(?:view|search|show|info)\b", re.IGNORECASE),
    "pip": re.compile(r"\bpip\s+(?:(?:index\s+versions)|search)\b", re.IGNORECASE),
    "cargo": re.compile(r"\bcargo\s+search\b", re.IGNORECASE),
}


def clean_package_name(package: str) -> str:
    """Clean extracted package name by removing shell metacharacters.

    Args:
        package: Raw package name from command string

    Returns:
        Cleaned package name without quotes or shell metacharacters
    """
    # Remove trailing quotes, backslashes, and shell metacharacters
    package = package.rstrip("\"'`\\")
    # Remove leading quotes if present
    package = package.lstrip("\"'`")
    return package


def validate_package_name(package: str, manager: str) -> bool:
    """Validate package name against manager-specific naming rules.

    Args:
        package: Cleaned package name to validate
        manager: Package manager name (npm, pip, cargo)

    Returns:
        True if package name is valid for the manager, False otherwise
    """
    if not package or len(package) > 214:
        return False

    # Manager-specific validation patterns
    validation_patterns = {
        "npm": r"^@[\w.-]+/[\w.-]+$|^[\w.-]+$",  # Scoped or unscoped
        "pip": r"^[a-zA-Z0-9](?:[a-zA-Z0-9._-]*[a-zA-Z0-9])?$",  # Must start/end with alphanumeric
        "cargo": r"^[a-z][a-z0-9_-]*$",  # Must start with lowercase, max 64 chars
    }

    pattern = validation_patterns.get(manager)
    if not pattern:
        return False

    import re

    if not re.match(pattern, package):
        return False

    # Cargo-specific length check
    if manager == "cargo" and len(package) > 64:
        return False

    return True


# Verification command extraction patterns (to get package names)
# Manager-specific patterns based on official naming rules
VERIFICATION_EXTRACTION_PATTERNS = {
    "npm": re.compile(
        r"\bnpm\s+(?:view|search|show|info)\s+(@[\w.-]+/[\w.-]+|[\w.-]+)", re.IGNORECASE
    ),
    "pip": re.compile(
        r"\bpip\s+(?:(?:index\s+versions)|search)\s+([a-zA-Z0-9._-]+)", re.IGNORECASE
    ),
    "cargo": re.compile(r"\bcargo\s+search\s+([a-z][a-z0-9_-]*)", re.IGNORECASE),
}

PIP_OPTIONS_WITH_VALUES = {
    "--constraint",
    "--editable",
    "-e",
    "--extra-index-url",
    "--find-links",
    "--index-url",
    "-i",
    "--no-binary",
    "--only-binary",
    "--platform",
    "--python-version",
    "--requirement",
    "-r",
    "--src",
    "--target",
    "--trusted-host",
}


def parse_stdin() -> tuple[str, dict]:
    """Parse stdin JSON to extract tool_name and tool_input.

    Returns:
        tuple of (tool_name, tool_input)
    """
    try:
        data = json.load(sys.stdin)
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})
        return tool_name, tool_input
    except (json.JSONDecodeError, ValueError, OSError):
        # If we can't parse, allow the operation
        return "", {}


def get_terminal_id(tool_input: dict) -> str:
    """Get terminal ID for state tracking using terminal_detection module.

    Uses canonical utility from terminal_detection module for consistent
    session isolation across all hooks. This aligns with the established
    pattern used by 12+ other hooks in the codebase.

    Priority (handled by detect_terminal_id):
    1. tool_input["terminal_id"] (explicit from Claude runtime)
    2. CLAUDE_TERMINAL_ID env var
    3. detect_terminal_id() (console handle / project state / etc.)

    Args:
        tool_input: Tool input dict from hook

    Returns:
        Terminal ID string (normalized format: {source}_{id})
    """
    explicit_terminal = str(
        tool_input.get("terminal_id")
        or tool_input.get("terminalId")
        or os.environ.get("CLAUDE_TERMINAL_ID", "")
    ).strip()
    if explicit_terminal:
        return explicit_terminal

    # Missing terminal identity disables stateful enforcement. Do not invent a
    # fallback identity, because that risks cross-terminal bleed.
    if "detect_terminal_id" not in globals():
        try:
            from __lib.terminal_detection import detect_terminal_id as _dt

            return (_dt() or "").strip()
        except ImportError:
            return ""

    return (detect_terminal_id() or "").strip()


def get_state_path(terminal_id: str) -> Path:
    """Get state file path for terminal.

    Args:
        terminal_id: Terminal ID string

    Returns:
        Path to state file
    """
    return STATE_DIR / f"dependency_verification_{terminal_id}.json"


def load_verification_state(terminal_id: str) -> dict:
    """Load verification state from file.

    Args:
        terminal_id: Terminal ID string

    Returns:
        Dict with verified packages and timestamps
    """
    state_path = get_state_path(terminal_id)

    if not state_path.exists():
        return {"verified_packages": {}}

    try:
        with state_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # Corrupted state file, start fresh
        return {"verified_packages": {}}


def save_verification_state(terminal_id: str, state: dict) -> None:
    """Save verification state to file.

    Args:
        terminal_id: Terminal ID string
        state: State dict to save
    """
    state_path = get_state_path(terminal_id)

    try:
        with state_path.open("w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except OSError:
        # Fail gracefully - state file is optional
        pass


def is_package_verified(package: str, state: dict) -> bool:
    """Check if package is already verified (within TTL).

    Args:
        package: Package name
        state: Verification state dict

    Returns:
        True if package verified within TTL, False otherwise
    """
    verified = state.get("verified_packages", {})
    if package not in verified:
        return False

    timestamp = verified[package]
    return (time.time() - timestamp) < VERIFICATION_TTL


def mark_package_verified(package: str, state: dict) -> dict:
    """Mark package as verified with current timestamp.

    Args:
        package: Package name
        state: Verification state dict

    Returns:
        Updated state dict
    """
    if "verified_packages" not in state:
        state["verified_packages"] = {}

    state["verified_packages"][package] = time.time()
    return state


def is_bypass_enabled(command: str) -> bool:
    """Check if bypass flag is present in command.

    Args:
        command: Bash command string

    Returns:
        True if bypass flag detected, False otherwise
    """
    return "--bypass-dependency-verification" in command


def is_verification_command(command: str) -> bool:
    """Check if command is a verification attempt (allowed).

    Uses word-boundary regex for robust detection.

    Args:
        command: Bash command string

    Returns:
        True if this is a verification command, False otherwise
    """
    # Check each package manager's verification patterns
    for pattern in VERIFICATION_PATTERNS.values():
        if pattern.search(command):
            return True

    return False


def is_local_package_install(command: str) -> bool:
    """Check if command installs a local package (allowed).

    Args:
        command: Bash command string

    Returns:
        True if this is a local package install, False otherwise
    """
    for pattern in LOCAL_PACKAGE_PATTERNS:
        if pattern.search(command):
            return True
    return False


def check_npm_install(command: str) -> str | None:
    """Check if command is an npm install without verification.

    Args:
        command: Bash command string

    Returns:
        Package name if unverified install detected, None otherwise
    """
    # Check for local package installs first
    if is_local_package_install(command):
        return None

    match = NPM_INSTALL_PATTERN.search(command)
    if match:
        raw_package = match.group(1)
        # Skip if preceded by quote - inside string literal, not a real install
        start = match.start()
        if start > 0 and command[start - 1] in ("'", '"'):
            return None
        package = clean_package_name(raw_package)

        # Skip if it's a file: protocol or local path
        if (
            package.startswith(("file:", "./", "../", "."))
            or "/" not in package
            and package.startswith(".")
        ):
            return None

        return package
    return None


def _extract_pip_install_packages(command: str) -> list[str]:
    """Extract candidate pip packages from a pip install command segment."""
    match = PIP_INSTALL_PATTERN.search(command)
    if not match:
        return []

    try:
        tokens = shlex.split(match.group(1), posix=False)
    except ValueError:
        tokens = match.group(1).split()

    packages: list[str] = []
    skip_next = False
    for token in tokens:
        if skip_next:
            skip_next = False
            continue

        cleaned = clean_package_name(token)
        if not cleaned:
            continue

        if cleaned.startswith("-"):
            if cleaned in PIP_OPTIONS_WITH_VALUES:
                skip_next = True
            continue

        if cleaned in {"&&", "||", ";"}:
            break

        if cleaned.startswith(("./", "../", ".", "file:", "git+", "http://", "https://")):
            continue

        packages.append(cleaned)

    return packages


def check_pip_install(command: str) -> list[str]:
    """Check if command is a pip install without verification.

    Args:
        command: Bash command string

    Returns:
        Candidate package names if unverified install detected, [] otherwise
    """
    return _extract_pip_install_packages(command)


def check_cargo_add(command: str) -> str | None:
    """Check if command is a cargo add without verification.

    Args:
        command: Bash command string

    Returns:
        Crate name if unverified add detected, None otherwise
    """
    match = CARGO_ADD_PATTERN.search(command)
    if match:
        raw_package = match.group(1)
        return clean_package_name(raw_package)
    return None


def create_block_payload(
    manager: str,
    packages: list[str],
    command: str,
    state: dict | None = None,
) -> dict:
    """Create user-friendly error message with verification guidance.

    Args:
        manager: Package manager name (npm, pip, cargo)
        packages: Package names
        command: Original command
        state: Verification state dict (for enhanced messages)

    Returns:
        Dict with block decision and recovery guidance
    """
    primary_package = packages[0]

    # Determine verification command
    if manager == "npm":
        verify_cmds = [f"npm view {package}" for package in packages]
    elif manager == "pip":
        verify_cmds = [f"pip index versions {package}" for package in packages]
    elif manager == "cargo":
        verify_cmds = [f"cargo search {package}" for package in packages]
    else:
        verify_cmds = [f"# Verify {manager} package '{primary_package}'"]

    package_label = (
        f"{manager} package '{primary_package}'"
        if len(packages) == 1
        else f"{manager} packages: {', '.join(repr(package) for package in packages)}"
    )

    # Enhanced error message with expiration info
    lines = [
        "Package installation blocked.",
        f"Package: {package_label}",
        "Issue: package not verified to exist before installation.",
        f"Blocked command: {command}",
    ]

    # Check if package was previously verified (expired)
    if state:
        verified = state.get("verified_packages", {})
        expired_packages = [package for package in packages if package in verified]
        if expired_packages:
            newest_seen = max(verified[package] for package in expired_packages)
            age_seconds = time.time() - newest_seen
            age_minutes = age_seconds / 60

            lines.append(
                f"Note: previously verified package data expired {age_minutes:.1f} minutes ago "
                f"(TTL is {VERIFICATION_TTL // 60} minutes)."
            )
    lines.append("You can continue by verifying the package first:")
    for index, verify_cmd in enumerate(verify_cmds, start=1):
        lines.append(f"{index}. Verify package exists: {verify_cmd}")
    lines.extend(
        [
            f"{len(verify_cmds) + 1}. Then retry: {command}",
            "Why this block exists: prevents wasted time on typos or non-existent packages.",
            "If bypass is required, add --bypass-dependency-verification to the command.",
        ]
    )

    return {
        "decision": "block",
        "reason": "\n".join(lines),
        "blocking_hook": "PreToolUse_dependency_verification_gate.py",
        "continue": False,
        "autonomous_recovery": True,
        "next_action": verify_cmds[0],
        "next_actions": verify_cmds,
        "packages": packages,
        "manager": manager,
    }


def evaluate_request(data: dict) -> dict | None:
    """Evaluate a hook payload and return a block payload or None."""
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if tool_name != "Bash" or not isinstance(tool_input, dict):
        return None

    command = tool_input.get("command", "")
    if not command or is_bypass_enabled(command):
        return None

    terminal_id = get_terminal_id(tool_input)
    if not terminal_id:
        logger.warning("Dependency verification skipped: missing terminal_id")
        return None

    state = load_verification_state(terminal_id)

    if is_verification_command(command):
        for manager, pattern in VERIFICATION_EXTRACTION_PATTERNS.items():
            match = pattern.search(command)
            if not match:
                continue

            raw_package = match.group(1)
            package = clean_package_name(raw_package)
            if not validate_package_name(package, manager):
                logger.warning(
                    "Invalid %s package name during verification: %s", manager, raw_package
                )
                return None

            state = mark_package_verified(package, state)
            save_verification_state(terminal_id, state)
            break
        return None

    package = check_npm_install(command)
    if package:
        if is_package_verified(package, state):
            return None
        return create_block_payload("npm", [package], command, state)

    packages = check_pip_install(command)
    if packages:
        unverified_packages = [
            package for package in packages if not is_package_verified(package, state)
        ]
        if not unverified_packages:
            return None
        return create_block_payload("pip", unverified_packages, command, state)

    package = check_cargo_add(command)
    if package:
        if is_package_verified(package, state):
            return None
        return create_block_payload("cargo", [package], command, state)

    return None


def run(data: dict) -> dict | None:
    """In-process entry point for PreToolUse router execution."""
    return evaluate_request(data)


def main() -> None:
    """PreToolUse hook for dependency verification."""
    # Check if enabled
    if not ENABLED:
        sys.exit(0)

    # Check bypass mode (runtime check, not import-time)
    mode = os.environ.get("DEPENDENCY_VERIFICATION_MODE", "block").lower()
    if mode == "bypass":
        sys.exit(0)

    tool_name, tool_input = parse_stdin()
    payload = evaluate_request(
        {
            "tool_name": tool_name,
            "tool_input": tool_input,
        }
    )
    if payload:
        print(payload.get("reason", "Package installation blocked."), file=sys.stderr)
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
