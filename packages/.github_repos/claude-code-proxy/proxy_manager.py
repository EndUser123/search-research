#!/usr/bin/env python3
"""
Proxy Manager -- manages claude-code-proxy instances independently of terminal sessions.

Processes survive Claude Code session exits. No console window flash on Windows.

Usage:
    python proxy_manager.py start <name>    Start proxy (e.g. anthropic, glm, m27)
    python proxy_manager.py stop <name>     Stop proxy
    python proxy_manager.py restart <name>  Stop then start proxy
    python proxy_manager.py status          Show status of all configured instances
    python proxy_manager.py stop-all        Stop all running proxies

Config files are named config-<name>.yaml. Port is read from server.port in the YAML.
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# Windows process creation flags
# DETACHED_PROCESS: child has no console attachment -- survives parent exit
# CREATE_NEW_PROCESS_GROUP: child in own process group (clean signal handling)
# CREATE_NO_WINDOW: suppresses the console flash on Windows
_DETACHED_PROCESS = 0x00000008
_CREATE_NEW_PROCESS_GROUP = 0x00000200
_CREATE_NO_WINDOW = 0x08000000

# Flags for spawning the long-running Go proxy (detached + silent)
_SPAWN_FLAGS = _DETACHED_PROCESS | _CREATE_NEW_PROCESS_GROUP | _CREATE_NO_WINDOW

# Flags for short-lived helper calls (taskkill) -- silent only
_SILENT_FLAGS = _CREATE_NO_WINDOW

SCRIPT_DIR = Path(__file__).parent
PID_DIR = SCRIPT_DIR / ".pids"
LOG_DIR = SCRIPT_DIR / ".logs"
PROXY_EXE = SCRIPT_DIR / "proxy" / "claude-code-proxy.exe"

STARTUP_POLL_INTERVAL = 0.5
STARTUP_MAX_WAIT = 5.0


def _config_file(name: str) -> Path:
    return SCRIPT_DIR / f"config-{name}.yaml"


def _pid_file(name: str) -> Path:
    return PID_DIR / f"proxy-{name}.pid"


def _log_file(name: str) -> Path:
    return LOG_DIR / f"proxy-{name}.log"


def _discover_configs() -> list[str]:
    """Return sorted list of config names from config-*.yaml files."""
    names = []
    for p in sorted(SCRIPT_DIR.glob("config-*.yaml")):
        name = p.stem[len("config-") :]  # strip "config-" prefix
        names.append(name)
    return names


def _read_port(config_path: Path) -> Optional[int]:
    """Read server.port from config YAML. Returns None if unreadable."""
    try:
        import yaml  # type: ignore[import]

        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        port_val = data.get("server", {}).get("port")
        return int(port_val) if port_val is not None else None
    except Exception:
        return None


def _is_running(pid: int) -> bool:
    """Return True if the process is alive. Windows-safe."""
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        # Process exists but we lack permission to signal it -- still running.
        return True
    except OSError:
        # WinError 87 (invalid parameter) can occur for Go/native processes on Windows.
        # Fall back to tasklist, which is always reliable.
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            capture_output=True,
            text=True,
            creationflags=_SILENT_FLAGS,
        )
        return str(pid) in result.stdout


def _read_pid(name: str) -> Optional[int]:
    """Read PID from file; return None if absent or corrupt."""
    try:
        return int(_pid_file(name).read_text(encoding="utf-8").strip())
    except (FileNotFoundError, ValueError, OSError):
        return None


def _write_pid(name: str, pid: int) -> None:
    PID_DIR.mkdir(parents=True, exist_ok=True)
    _pid_file(name).write_text(str(pid), encoding="utf-8")


def _remove_pid(name: str) -> None:
    try:
        _pid_file(name).unlink()
    except FileNotFoundError:
        pass


def _read_dotenv(path: Path) -> dict[str, str]:
    """Parse a .env file and return key=value pairs. Ignores comments and blanks."""
    result: dict[str, str] = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key:
                result[key] = value
    except (FileNotFoundError, OSError):
        pass
    return result


def _load_env(name: str, port: int) -> dict[str, str]:
    """Build env dict: inherit current env, inject credentials from P:\\.env."""
    env = os.environ.copy()

    # Read credentials from the project-root .env file (P:\\.env).
    # godotenv inside the Go binary looks one level up from the proxy/ dir,
    # which is the claude-code-proxy/ directory -- not P:\\ -- so it won't find
    # P:\\.env at all. We read it here and inject explicitly.
    dot_env = _read_dotenv(Path("P:/.env"))

    # Inject ZHIPU_API_KEY as ZAI_API_KEY so the Go config can pick it up
    # via os.Getenv("ZAI_API_KEY") regardless of what's already in the system env.
    zhipu_key = dot_env.get("ZHIPU_API_KEY") or env.get("ZHIPU_API_KEY")
    if zhipu_key:
        env["ZAI_API_KEY"] = zhipu_key

    # Inject other common keys from .env if not already set in the environment.
    for key_name in (
        "OPENAI_API_KEY",
        "OPENROUTER_API_KEY",
        "MINIMAX_API_KEY",
        "GEMINI_FREE_API_KEY",
        "GEMINI_PAID_API_KEY",
    ):
        if not env.get(key_name) and dot_env.get(key_name):
            env[key_name] = dot_env[key_name]

    env["ANTHROPIC_BASE_URL"] = f"http://localhost:{port}"

    # Auto-inject ANTHROPIC_PROVIDER_API_KEY when the anthropic.base_url in the
    # config points to a non-Anthropic endpoint (z.ai or MiniMax).
    # The Go binary reads this env var and sets cfg.Providers.Anthropic.APIKey,
    # which replaces the x-api-key header forwarded to the provider.
    config_path = _config_file(name)
    if config_path.exists():
        try:
            import yaml  # type: ignore[import]

            cfg_data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            anthropic_url: str = (
                cfg_data.get("providers", {}).get("anthropic", {}).get("base_url") or ""
            )
            if "z.ai" in anthropic_url:
                provider_key = dot_env.get("ZHIPU_API_KEY") or env.get(
                    "ZHIPU_API_KEY", ""
                )
                if provider_key:
                    env["ANTHROPIC_PROVIDER_API_KEY"] = provider_key
            elif "minimax" in anthropic_url:
                provider_key = dot_env.get("MINIMAX_API_KEY") or env.get(
                    "MINIMAX_API_KEY", ""
                )
                if provider_key:
                    env["ANTHROPIC_PROVIDER_API_KEY"] = provider_key
        except Exception:
            pass  # yaml not installed or config unreadable -- skip silently

    return env


def _wait_for_alive(pid: int) -> bool:
    """Poll until process is confirmed alive or startup window expires."""
    deadline = time.monotonic() + STARTUP_MAX_WAIT
    while time.monotonic() < deadline:
        if _is_running(pid):
            return True
        time.sleep(STARTUP_POLL_INTERVAL)
    return False


def cmd_start(name: str) -> int:
    """Start proxy for config name. Returns exit code."""
    config = _config_file(name)
    if not config.exists():
        print(f"Error: config file not found: {config}", file=sys.stderr)
        print(f"Create with: cp config.yaml.example config-{name}.yaml")
        return 1

    if not PROXY_EXE.exists():
        print(f"Error: proxy executable not found: {PROXY_EXE}", file=sys.stderr)
        print("Build with: cd proxy && go build -o claude-code-proxy.exe ./cmd/proxy")
        return 1

    port = _read_port(config)
    if port is None:
        print(f"Error: could not read server.port from {config}", file=sys.stderr)
        return 1

    existing_pid = _read_pid(name)
    if existing_pid is not None and _is_running(existing_pid):
        print(f"Proxy '{name}' already running (PID {existing_pid}, port {port})")
        return 0

    if existing_pid is not None:
        _remove_pid(name)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = _log_file(name)
    env = _load_env(name, port)

    print(f"Starting proxy '{name}' (port {port})...")

    # Open log in append mode. subprocess duplicates the handle for the child;
    # closing our side after Popen returns is safe on Windows.
    with open(log_path, "a", encoding="utf-8") as log_fh:
        proc = subprocess.Popen(
            [str(PROXY_EXE), "--config", str(config)],
            env=env,
            stdout=log_fh,
            stderr=log_fh,
            # CWD = directory containing the proxy binary.
            # Agent paths and db_path are expressed as absolute paths in config files.
            cwd=str(PROXY_EXE.parent),
            creationflags=_SPAWN_FLAGS,
        )

    _write_pid(name, proc.pid)

    if _wait_for_alive(proc.pid):
        print(f"  PID:    {proc.pid}")
        print(f"  Port:   {port}")
        print(f"  Config: {config.name}")
        print(f"  Log:    {log_path}")
        return 0
    else:
        _remove_pid(name)
        print(f"  Failed to start -- check log: {log_path}", file=sys.stderr)
        return 1


def cmd_stop(name: str) -> int:
    """Stop proxy for config name. Returns exit code."""
    pid = _read_pid(name)
    if pid is None:
        print(f"Proxy '{name}': not running (no PID file)")
        return 0

    if not _is_running(pid):
        print(f"Proxy '{name}': stale PID {pid} -- cleaning up")
        _remove_pid(name)
        return 0

    print(f"Stopping proxy '{name}' (PID {pid})...")
    result = subprocess.run(
        ["taskkill", "/F", "/PID", str(pid)],
        capture_output=True,
        text=True,
        creationflags=_SILENT_FLAGS,
    )
    _remove_pid(name)

    if result.returncode == 0 or not _is_running(pid):
        print("  Stopped.")
        return 0

    print(
        f"  Warning: taskkill exit {result.returncode}: {result.stderr.strip()}",
        file=sys.stderr,
    )
    return 1


def cmd_restart(name: str) -> int:
    """Stop then start proxy for config name."""
    cmd_stop(name)
    time.sleep(1)
    return cmd_start(name)


def cmd_status() -> int:
    """Print status table of all configured proxy instances."""
    names = _discover_configs()

    if not names:
        print("No proxy configurations found.")
        print("Create config files: cp config.yaml.example config-anthropic.yaml")
        return 0

    print(f"{'Config':<14} {'Port':<8} {'Status':<10} {'PID':<10} Log")
    print("-" * 58)

    any_running = False
    for name in names:
        pid = _read_pid(name)
        config = _config_file(name)
        port = _read_port(config)
        port_str = str(port) if port is not None else "?"
        log = _log_file(name)

        if pid is not None and _is_running(pid):
            status, pid_str, any_running = "running", str(pid), True
        else:
            if pid is not None:
                _remove_pid(name)
            status, pid_str = "stopped", "-"

        log_str = log.name if log.exists() else "-"
        print(f"{name:<14} {port_str:<8} {status:<10} {pid_str:<10} {log_str}")

    if not any_running:
        print("\n(no proxies running)")
    return 0


def cmd_stop_all() -> int:
    """Stop all running proxy instances."""
    stopped = 0
    for name in _discover_configs():
        pid = _read_pid(name)
        if pid is not None and _is_running(pid):
            if cmd_stop(name) == 0:
                stopped += 1
    if stopped == 0:
        print("No proxies were running.")
    else:
        print(f"\nStopped {stopped} proxy instance(s).")
    return 0


def _parse_config_name(args: list[str], default: str = "anthropic") -> str:
    if args:
        return args[0]
    return default


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    command = sys.argv[1].lower()
    rest = sys.argv[2:]

    if command in ("-h", "--help", "help"):
        print(__doc__)
        return 0

    dispatch = {
        "start": lambda: cmd_start(_parse_config_name(rest)),
        "stop": lambda: cmd_stop(_parse_config_name(rest)),
        "restart": lambda: cmd_restart(_parse_config_name(rest)),
        "status": cmd_status,
        "stop-all": cmd_stop_all,
    }

    if command not in dispatch:
        print(f"Unknown command: {command!r}", file=sys.stderr)
        print(__doc__)
        return 1

    return dispatch[command]()


if __name__ == "__main__":
    sys.exit(main())
