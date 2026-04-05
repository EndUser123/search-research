#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

GREEN, RED, YELLOW, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[0m"

SIGNALS_DIR = Path.home() / ".claude" / "signals"

def print_test_result(name: str, passed: bool, details: str | None = None) -> None:
    status = f"{GREEN}PASS{RESET}" if passed else f"{RED}FAIL{RESET}"
    print(f"  [{status}] {name}")
    if details:
        print(f"       {details}")

def cleanup_signals() -> None:
    """Remove all signal files."""
    if SIGNALS_DIR.exists():
        for f in SIGNALS_DIR.glob("*.json"):
            try:
                f.unlink()
            except:
                pass

def test_signals_directory_exists() -> bool:
    """Signals directory should be created."""
    return SIGNALS_DIR.exists()

def test_hook_writes_signal_file() -> bool:
    """Hook should write a signal file for planning mode."""
    cleanup_signals()

    hook_path = Path(__file__).resolve().parent / "authority-check.py"
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps({"prompt": "How should I design this?"}),
        capture_output=True,
        text=True,
        timeout=5
    )

    # Check if a signal file was created
    signals = list(SIGNALS_DIR.glob("*.json"))
    return len(signals) > 0

def test_signal_file_format() -> bool:
    """Signal files should have correct format."""
    cleanup_signals()

    hook_path = Path(__file__).resolve().parent / "authority-check.py"
    subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps({"prompt": "What's the best approach?"}),
        capture_output=True,
        text=True,
        timeout=5
    )

    signals = list(SIGNALS_DIR.glob("*.json"))
    if not signals:
        return False

    with open(signals[0]) as f:
        data = json.load(f)

    # Check required fields
    required = {"type", "action", "source", "timestamp"}
    return required.issubset(data.keys())

def test_signal_has_action_show() -> bool:
    """Planning mode signal should have action='show'."""
    cleanup_signals()

    hook_path = Path(__file__).resolve().parent / "authority-check.py"
    subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps({"prompt": "How should I structure this?"}),
        capture_output=True,
        text=True,
        timeout=5
    )

    signals = list(SIGNALS_DIR.glob("*.json"))
    if not signals:
        return False

    with open(signals[0]) as f:
        data = json.load(f)

    return data.get("action") == "show"

def test_authorization_clears_signal() -> bool:
    """Authorization keyword should create a clear signal."""
    cleanup_signals()

    hook_path = Path(__file__).resolve().parent / "authority-check.py"
    subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps({"prompt": "implement the feature"}),
        capture_output=True,
        text=True,
        timeout=5
    )

    # After authorization, signals should indicate clear
    signals = list(SIGNALS_DIR.glob("*.json"))
    for sig_file in signals:
        with open(sig_file) as f:
            data = json.load(f)
            if data.get("action") == "clear":
                return True
    return False

def test_old_signals_auto_expire() -> bool:
    """Old signal files should be cleaned up (TTL)."""
    cleanup_signals()

    # Create an old signal file
    old_signal = SIGNALS_DIR / "old_test.json"
    SIGNALS_DIR.mkdir(parents=True, exist_ok=True)

    # Write a signal with old timestamp (more than 5 minutes ago)
    old_time = time.time() - 600  # 10 minutes ago
    with open(old_signal, 'w') as f:
        json.dump({
            "type": "test",
            "action": "show",
            "timestamp": old_time
        }, f)

    # Run cleanup function
    # Note: This will be implemented in the signal module
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from signal_queue import cleanup_old_signals
        cleanup_old_signals(ttl=300)  # 5 minute TTL
    except ImportError:
        # Module doesn't exist yet - expected for RED phase
        old_signal.unlink()
        return False

    # Check if old signal was removed
    return not old_signal.exists()

def main() -> int:
    print("=" * 60)
    print("Signal-Based Notification Tests")
    print("=" * 60)

    results = []

    print(f"\n{YELLOW}SECTION 1: Signal Directory{RESET}")
    r = test_signals_directory_exists()
    print_test_result("Signals directory exists", r)
    results.append(r)

    print(f"\n{YELLOW}SECTION 2: Hook Signal Writing{RESET}")
    r = test_hook_writes_signal_file()
    print_test_result("Hook writes signal file", r)
    results.append(r)
    r = test_signal_file_format()
    print_test_result("Signal file has correct format", r)
    results.append(r)
    r = test_signal_has_action_show()
    print_test_result("Planning mode signal has action='show'", r)
    results.append(r)

    print(f"\n{YELLOW}SECTION 3: Signal Clearing{RESET}")
    r = test_authorization_clears_signal()
    print_test_result("Authorization creates clear signal", r)
    results.append(r)

    print(f"\n{YELLOW}SECTION 4: TTL/Cleanup{RESET}")
    r = test_old_signals_auto_expire()
    print_test_result("Old signals auto-expire", r)
    results.append(r)

    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    pct = (passed / total) * 100
    if passed == total:
        print(f"{GREEN}ALL {total}/{total} TESTS PASSED ({pct:.0f}%){RESET}")
    else:
        print(f"{RED}TESTS FAILED: {passed}/{total} passed ({pct:.0f}%){RESET}")
    print("=" * 60)

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
