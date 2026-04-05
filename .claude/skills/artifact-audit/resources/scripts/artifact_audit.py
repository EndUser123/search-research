"""
/artifact-audit command
Shows pending artifact updates for current project.
"""
import argparse
from pathlib import Path
import sys

# Import from shared artifact skill directory
# artifact-audit is at: skills/artifact-audit/resources/scripts/artifact_audit.py
# We need to go to: skills/artifact/resources/scripts/
# So: parent.parent.parent = skills/ then /artifact/resources/scripts
artifact_skill_dir = Path(__file__).parent.parent.parent.parent / "artifact" / "resources" / "scripts"
sys.path.insert(0, str(artifact_skill_dir))

from artifact_core import get_pending_items, find_project_root
from artifact_init import ensure_schema


def audit(args=None) -> int:
    """
    Show pending artifact updates.

    Returns:
        0 if no pending items, 1 if pending items exist (for exit code usage)
    """
    parser = argparse.ArgumentParser(description="Show pending artifact updates")
    parser.add_argument("--project-root", type=str, help="Project directory")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parsed = parser.parse_args(args)

    # Ensure schema exists
    ensure_schema()

    # Find project root
    project_root = Path(parsed.project_root) if parsed.project_root else find_project_root()
    if not project_root:
        print("Error: Could not find project root (no .git, pyproject.toml, etc)")
        return 0

    items = get_pending_items(project_root)

    if parsed.json:
        import json
        print(json.dumps(items, indent=2))
    else:
        if not items:
            print("No pending artifact updates.")
            return 0

        # Group by severity
        by_severity = {"critical": [], "standard": [], "low": []}
        for item in items:
            by_severity[item["severity"]].append(item)

        for severity in ["critical", "standard", "low"]:
            if not by_severity[severity]:
                continue
            items_list = by_severity[severity]
            print(f"\n{severity.upper()} ({len(items_list)})")
            print("-" * 50)

            for item in items_list:
                status_icons = {
                    "pending": "⏳",
                    "confirm": "?",
                    "done": "",
                    "n/a": "-",
                }
                artifacts = " ".join(
                    f"{status_icons.get(s, '?')}{k}"
                    for k, s in item.get("artifacts", {}).items()
                    if s != "done" and s != "n/a"
                )

                print(f"  {item['item_id']}: {item['summary']}")
                if artifacts:
                    print(f"    {artifacts}")

        print()
        return 1 if items else 0


if __name__ == "__main__":
    raise SystemExit(audit())
