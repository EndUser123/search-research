#!/usr/bin/env python3
"""
launch_llm_chrome.py — Launch Chrome with the dedicated LLM profile and
create the DevToolsActivePort file that chrome-devtools-mcp's --autoConnect needs.

Chrome's chrome://inspect toggle enables remote debugging on port 9222 but
does not create the DevToolsActivePort file. This script:
1. Kills any existing Chrome (clean start)
2. Launches Chrome with the dedicated LLM profile
3. Waits for Chrome to bind port 9222
4. Writes the DevToolsActivePort file
5. Prints status

Usage:
    python P:/.agents/scripts/launch_llm_chrome.py
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


def kill_chrome():
    """Kill all existing Chrome processes."""
    try:
        subprocess.run(
            ["taskkill", "/F", "/IM", "chrome.exe", "/T"],
            capture_output=True, timeout=10
        )
        time.sleep(3)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass


def launch_chrome():
    """Launch Chrome with the dedicated LLM profile."""
    if not Path(CHROME_EXE).exists():
        print(f"ERROR: Chrome not found at {CHROME_EXE}", file=sys.stderr)
        sys.exit(1)

    subprocess.Popen(
        [CHROME_EXE, f"--user-data-dir={PROFILE_DIR}", "--new-window"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(4)


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


def is_port_listening(port):
    """Check if a TCP port is listening on localhost."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except OSError:
        return False


def wait_for_port(port, max_wait=15):
    """Wait for a port to start listening."""
    waited = 0
    while waited < max_wait:
        if is_port_listening(port):
            return True
        time.sleep(1)
        waited += 1
    return False


def write_devtools_active_port():
    """Write the DevToolsActivePort file."""
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    ws_path = "/devtools/browser"
    PORT_FILE.write_text(f"{PORT}\n{ws_path}", encoding="ascii")
    return PORT_FILE.exists()


def main():
    # Step 1: Kill existing Chrome
    existing = count_chrome_processes()
    if existing > 0:
        print(f"Killing {existing} existing Chrome processes...")
        kill_chrome()

    # Step 2: Launch Chrome with dedicated profile
    print(f"Launching Chrome with LLM profile: {PROFILE_DIR}")
    launch_chrome()

    alive = count_chrome_processes()
    if alive == 0:
        print("ERROR: Chrome failed to start", file=sys.stderr)
        sys.exit(1)
    print(f"Chrome running: {alive} processes")

    # Step 3: Wait for port 9222
    print(f"Checking port {PORT}...")
    if not wait_for_port(PORT):
        print(f"WARNING: Port {PORT} not listening after 15s.")
        print("Enable the toggle at chrome://inspect in the LLM profile, then re-run.")
        sys.exit(1)
    print(f"Port {PORT} is listening")

    # Step 4: Write DevToolsActivePort file
    if write_devtools_active_port():
        print(f"DevToolsActivePort created at {PORT_FILE}")
    else:
        print("ERROR: Failed to write DevToolsActivePort", file=sys.stderr)
        sys.exit(1)

    # Step 5: Summary
    print()
    print("Chrome LLM profile is ready.")
    print(f"  Profile: {PROFILE_DIR}")
    print(f"  Port: {PORT}")
    print(f"  DevToolsActivePort: {PORT_FILE}")
    print()
    print("Reload plugins (r) for the MCP server to connect.")


if __name__ == "__main__":
    main()
