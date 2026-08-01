#!/usr/bin/env python3
"""
scheduled_checks.py — Run scheduled maintenance checks for /maintain.

Reads P:/.data/scheduled-checks.json, filters to items that haven't been
checked today, runs the check, updates last_checked + status. Returns
structured output for /maintain to display.

Check types:
  - github_issue: checks if a GitHub issue/PR is closed or merged

Usage:
    python scheduled_checks.py              # run due checks, print results
    python scheduled_checks.py --json       # JSON output
    python scheduled_checks.py --list       # show all registered checks
    python scheduled_checks.py --add <json> # add a new check item

State file: P:/.data/scheduled-checks.json
"""

import json
import subprocess
from datetime import date
from pathlib import Path

REGISTRY_PATH = Path("P:/.data/scheduled-checks.json")


def load_registry():
    if not REGISTRY_PATH.exists():
        return []
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def save_registry(items):
    tmp = REGISTRY_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, indent=2), encoding="utf-8")
    tmp.replace(REGISTRY_PATH)


def is_due(item):
    """Check if an item needs running today."""
    if item.get("status") != "pending":
        return False
    today = date.today().isoformat()
    return item.get("last_checked") != today


def check_github_issue(args):
    """Check if a GitHub issue/PR is closed or merged."""
    repo = args["repo"]
    issue = args["issue"]
    look_for = args.get("look_for", "closed")

    cmd = [
        "gh", "issue", "view", str(issue),
        "--repo", repo,
        "--json", "state,title,closedAt,stateReason",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode != 0:
            return {"resolved": False, "error": result.stderr.strip()[:200]}

        data = json.loads(result.stdout)
        state = data.get("state", "").upper()

        if look_for == "closed" and state == "CLOSED":
            return {
                "resolved": True,
                "detail": f"Issue #{issue} is {state}",
                "title": data.get("title", ""),
                "closed_at": data.get("closedAt", ""),
            }
        if look_for == "merged" and state == "CLOSED":
            reason = data.get("stateReason", "")
            return {
                "resolved": True,
                "detail": f"Issue #{issue} closed ({reason})",
                "title": data.get("title", ""),
                "closed_at": data.get("closedAt", ""),
            }

        return {
            "resolved": False,
            "detail": f"Issue #{issue} state: {state}",
            "title": data.get("title", ""),
        }
    except FileNotFoundError:
        return {"resolved": False, "error": "gh CLI not found"}
    except subprocess.TimeoutExpired:
        return {"resolved": False, "error": "gh command timed out"}
    except json.JSONDecodeError:
        return {"resolved": False, "error": "gh returned invalid JSON"}


CHECK_HANDLERS = {
    "github_issue": check_github_issue,
}


def run_checks():
    """Run all due checks, update the registry, return results."""
    items = load_registry()
    results = []
    changed = False

    for item in items:
        if not is_due(item):
            results.append({
                "id": item["id"],
                "description": item["description"],
                "status": "skipped",
                "reason": "Already checked today or not pending",
            })
            continue

        check_type = item.get("check_type")
        handler = CHECK_HANDLERS.get(check_type)

        if not handler:
            results.append({
                "id": item["id"],
                "description": item["description"],
                "status": "error",
                "reason": f"Unknown check_type: {check_type}",
            })
            continue

        check_result = handler(item.get("check_args", {}))

        item["last_checked"] = date.today().isoformat()
        changed = True

        if check_result.get("resolved"):
            item["status"] = "resolved"
            results.append({
                "id": item["id"],
                "description": item["description"],
                "status": "resolved",
                "detail": check_result.get("detail", ""),
                "action": item.get("action_on_found", ""),
            })
        else:
            results.append({
                "id": item["id"],
                "description": item["description"],
                "status": "pending",
                "detail": check_result.get("detail", check_result.get("error", "Not resolved yet")),
            })

    if changed:
        save_registry(items)

    return results


def print_results(results):
    """Human-readable output for /maintain integration."""
    resolved = [r for r in results if r["status"] == "resolved"]
    pending = [r for r in results if r["status"] == "pending"]
    skipped = [r for r in results if r["status"] == "skipped"]
    errors = [r for r in results if r["status"] == "error"]

    if not results:
        print("  No scheduled checks registered.")
        return

    if resolved:
        print("  ✅ RESOLVED since last check:")
        for r in resolved:
            print(f"     • {r['description']}: {r.get('detail', '')}")
            if r.get("action"):
                print(f"       → {r['action']}")

    if pending:
        print(f"  ⏳ Still pending ({len(pending)}):")
        for r in pending:
            print(f"     • {r['description']}: {r.get('detail', 'Not resolved')}")

    if errors:
        print(f"  ⚠️ Errors ({len(errors)}):")
        for r in errors:
            print(f"     • {r['description']}: {r.get('reason', 'Unknown error')}")

    if skipped and not (resolved or pending or errors):
        total = len(skipped)
        print(f"  All {total} check(s) already ran today — no updates.")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Scheduled maintenance checks")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--list", action="store_true", help="List all registered checks")
    args = parser.parse_args()

    if args.list:
        items = load_registry()
        for item in items:
            status = item.get("status", "unknown")
            last = item.get("last_checked", "never")
            print(f"  {status:>8} | {item['id']:<35} | last: {last}")
        return

    results = run_checks()

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_results(results)


if __name__ == "__main__":
    main()
