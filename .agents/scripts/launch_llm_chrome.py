#!/usr/bin/env python3
"""
launch_llm_chrome.py — Ensure Chrome with the dedicated LLM profile is
running with remote debugging, and the DevToolsActivePort file exists.

Smart lifecycle:
1. If port 9222 is already listening → just ensure DevToolsActivePort exists, done.
2. If Chrome with LLM profile is running but port not listening → prompt to enable toggle.
3. If Chrome with LLM profile is NOT running → launch it, wait for port.

Non-destructive: does NOT kill existing Chrome unless --kill flag is passed.

Usage:
    python P:/.agents/scripts/launch_llm_chrome.py          # smart start
    python P:/.agents/scripts/launch_llm_chrome.py --kill    # force restart
"""

import socket
import subprocess
import sys
import time
from pathlib import Path

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE_DIR = Path(r"P:\.data\chrome-llm-profile")
PORT_FILE = PROFILE_DIR / "DevToolsActivePort"
PORT = 9222


def count_chrome_processes():
    """Count running chrome.exe processes."""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq chrome.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.count("chrome.exe")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return 0


def is_llm_profile_running():
    """Check if Chrome is running with our dedicated LLM profile."""
    try:
        result = subprocess.run(
            ["wmic", "process", "where", "name='chrome.exe'", "get", "commandline"],
            capture_output=True, text=True, timeout=5
        )
        return "chrome-llm-profile" in result.stdout.lower()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def is_port_listening(port):
    """Check if a TCP port is listening on localhost."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except OSError:
        return False


def wait_for_port(port, max_wait=20):
    """Wait for a port to start listening."""
    waited = 0
    while waited < max_wait:
        if is_port_listening(port):
            return True
        time.sleep(1)
        waited += 1
    return False


def kill_chrome():
    """Kill all Chrome processes."""
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "chrome.exe", "/T"],
            capture_output=True, timeout=10
        )
        time.sleep(3)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass


def launch_chrome():
    """Launch Chrome as a detached process (survives parent exit)."""
    if not Path(CHROME_EXE).exists():
        print(f"ERROR: Chrome not found at {CHROME_EXE}", file=sys.stderr)
        sys.exit(1)

    # Use DETACHED_PROCESS flag so Chrome survives this script exiting
    subprocess.Popen(
        [CHROME_EXE, f"--user-data-dir={PROFILE_DIR}", "--new-window"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.DETACHED_PROCESS,
    )
    time.sleep(4)


def write_devtools_active_port():
    """Write the DevToolsActivePort file."""
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    ws_path = "/devtools/browser"
    PORT_FILE.write_text(f"{PORT}\n{ws_path}", encoding="ascii")
    return PORT_FILE.exists()


def main():
    force_kill = "--kill" in sys.argv

    # Step 0: Handle --kill flag
    if force_kill:
        existing = count_chrome_processes()
        if existing > 0:
            print(f"--kill: Stopping {existing} Chrome processes...")
            kill_chrome()

    # Step 1: If port is already listening, we're almost done
    if is_port_listening(PORT):
        if write_devtools_active_port():
            print(f"Port {PORT} already listening. DevToolsActivePort written.")
        else:
            print("ERROR: Failed to write DevToolsActivePort", file=sys.stderr)
            sys.exit(1)
        print_ready()
        return

    # Step 2: Is Chrome with LLM profile already running?
    profile_running = is_llm_profile_running()

    if profile_running:
        # Chrome is up but toggle isn't enabled — wait for operator to turn it on
        print("Chrome LLM profile is running but port 9222 is not listening.")
        print("Waiting for remote debugging toggle (enable at chrome://inspect)...")
        if wait_for_port(PORT, max_wait=60):
            if write_devtools_active_port():
                print(f"Port {PORT} is now listening. DevToolsActivePort written.")
                print_ready()
                return
            else:
                print("ERROR: Failed to write DevToolsActivePort", file=sys.stderr)
                sys.exit(1)
        else:
            print("TIMEOUT: Port 9222 not available after 60s.")
            print("Enable the toggle at chrome://inspect in the LLM profile, then re-run.")
            sys.exit(1)

    # Step 3: Chrome with LLM profile is NOT running — launch it
    print("Chrome LLM profile not running. Launching...")
    launch_chrome()

    alive = count_chrome_processes()
    if alive == 0:
        print("ERROR: Chrome failed to start", file=sys.stderr)
        sys.exit(1)
    print(f"Chrome running: {alive} processes")

    # Wait for port (toggle may auto-enable if it was on last session)
    print(f"Checking port {PORT}...")
    if wait_for_port(PORT, max_wait=20):
        print(f"Port {PORT} is listening")
        if write_devtools_active_port():
            print(f"DevToolsActivePort created at {PORT_FILE}")
            print_ready()
            return
        else:
            print("ERROR: Failed to write DevToolsActivePort", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Port {PORT} not listening after 20s.")
        print("Enable the toggle at chrome://inspect in the LLM profile, then re-run.")
        sys.exit(1)


def print_ready():
    """Print the ready summary."""
    print()
    print("Chrome LLM profile is ready.")
    print(f"  Profile: {PROFILE_DIR}")
    print(f"  Port: {PORT}")
    print(f"  DevToolsActivePort: {PORT_FILE}")
    print()
    print("Reload plugins (r) for the MCP server to connect.")


if __name__ == "__main__":
    main()
