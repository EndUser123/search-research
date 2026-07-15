#!/usr/bin/env python3
"""Reap orphaned OpenCode red-team processes via marker/deadline scanning.

Scans the marker directory for expired markers left behind when the Python
supervisor was terminated before it could clean up. For each expired marker:

1. Verify the PID still exists.
2. Verify the process creation time matches (detect PID reuse).
3. Verify the current command line fingerprint matches.
4. Refuse to kill interactive OpenCode sessions.
5. Kill the process tree with taskkill.exe /PID <pid> /T /F.
6. Remove the marker only after the process tree is confirmed gone.

Usage:
  python reap_red_team_processes.py
  python reap_red_team_processes.py --dry-run
  python reap_red_team_processes.py --marker-dir P:/custom/path
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import red_team_markers as markers


def scan_and_reap(marker_dir: Path, dry_run: bool = False, now: float | None = None) -> dict:
    """Scan markers and reap expired processes.

    Returns a summary dict with counts:
      scanned: total marker files found
      skipped_not_expired: deadline hasn't passed
      skipped_malformed: invalid marker JSON
      skipped_interactive: command looks like an interactive OpenCode session
      skipped_pid_dead: PID no longer exists (stale marker)
      skipped_pid_mismatch: PID reused (creation time differs)
      skipped_cmdline_mismatch: command line no longer matches
      killed: process tree killed successfully
      failed: kill attempt failed
      markers_removed: markers cleaned up
    """
    if now is None:
        now = time.time()

    summary = {
        "scanned": 0,
        "skipped_not_expired": 0,
        "skipped_malformed": 0,
        "skipped_interactive": 0,
        "skipped_pid_dead": 0,
        "skipped_pid_mismatch": 0,
        "skipped_cmdline_mismatch": 0,
        "killed": 0,
        "failed": 0,
        "markers_removed": 0,
    }

    details = []

    if not marker_dir.exists():
        return {"summary": summary, "details": details}

    for marker_file in sorted(marker_dir.glob("*.json")):
        summary["scanned"] += 1
        task_id = marker_file.stem

        marker = markers.read_marker(marker_file)
        if marker is None:
            summary["skipped_malformed"] += 1
            details.append({"task_id": task_id, "action": "skipped_malformed"})
            continue

        if not markers.is_marker_expired(marker, now):
            summary["skipped_not_expired"] += 1
            details.append({"task_id": task_id, "action": "skipped_not_expired"})
            continue

        root_pid = marker.get("root_pid")
        if root_pid is None:
            summary["skipped_malformed"] += 1
            details.append({"task_id": task_id, "action": "skipped_malformed"})
            continue

        if not markers.is_process_alive(root_pid):
            summary["skipped_pid_dead"] += 1
            # Process is gone — clean up the stale marker.
            try:
                marker_file.unlink()
                summary["markers_removed"] += 1
            except Exception:
                pass
            details.append({"task_id": task_id, "action": "skipped_pid_dead"})
            continue

        if markers.is_interactive_opencode(marker):
            summary["skipped_interactive"] += 1
            details.append({"task_id": task_id, "action": "skipped_interactive"})
            continue

        expected_creation_time = marker.get("process_creation_time")
        if not markers.verify_pid_creation_time(root_pid, expected_creation_time):
            summary["skipped_pid_mismatch"] += 1
            details.append({"task_id": task_id, "action": "skipped_pid_mismatch"})
            continue

        expected_fingerprint = marker.get("command_fingerprint", "")
        if not markers.verify_command_fingerprint(root_pid, expected_fingerprint):
            summary["skipped_cmdline_mismatch"] += 1
            details.append({"task_id": task_id, "action": "skipped_cmdline_mismatch"})
            continue

        if dry_run:
            details.append({"task_id": task_id, "pid": root_pid, "action": "would_kill"})
            continue

        kill_result = markers.kill_process_tree(root_pid)
        if kill_result["ok"]:
            summary["killed"] += 1
        else:
            summary["failed"] += 1

        # Wait briefly, then verify the process is gone before removing the marker.
        time.sleep(1)
        if not markers.is_process_alive(root_pid):
            try:
                marker_file.unlink()
                summary["markers_removed"] += 1
            except Exception:
                pass

        details.append(
            {
                "task_id": task_id,
                "pid": root_pid,
                "action": "killed" if kill_result["ok"] else "failed",
                "kill_error": kill_result["error"],
            }
        )

    return {"summary": summary, "details": details}


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    marker_dir = markers.MARKER_DIR
    for i, arg in enumerate(sys.argv):
        if arg == "--marker-dir" and i + 1 < len(sys.argv):
            marker_dir = Path(sys.argv[i + 1])

    result = scan_and_reap(marker_dir, dry_run=dry_run)
    s = result["summary"]

    mode = "DRY RUN" if dry_run else "LIVE"
    print(f"Red-team process reaper ({mode})")
    print(f"Marker directory: {marker_dir}")
    print(f"  Scanned:             {s['scanned']}")
    print(f"  Skipped (not expired): {s['skipped_not_expired']}")
    print(f"  Skipped (malformed):   {s['skipped_malformed']}")
    print(f"  Skipped (interactive): {s['skipped_interactive']}")
    print(f"  Skipped (PID dead):    {s['skipped_pid_dead']}")
    print(f"  Skipped (PID mismatch):{s['skipped_pid_mismatch']}")
    print(f"  Skipped (cmdline):     {s['skipped_cmdline_mismatch']}")
    print(f"  Killed:                {s['killed']}")
    print(f"  Failed:                {s['failed']}")
    print(f"  Markers removed:       {s['markers_removed']}")

    if result["details"]:
        print("\nDetails:")
        for d in result["details"]:
            print(f"  {d}")

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
