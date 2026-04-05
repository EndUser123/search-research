import json
from datetime import datetime
from pathlib import Path

FINDINGS_FILE = Path("assessment_findings.json")


def load_findings():
    return (
        json.loads(FINDINGS_FILE.read_text())
        if FINDINGS_FILE.exists()
        else {"findings": []}
    )


def add_finding(finding_id: str, description: str, severity: str, file_path: str = ""):
    """Add new finding to track."""
    data = load_findings()
    data["findings"].append(
        {
            "id": finding_id,
            "description": description,
            "severity": severity,
            "file_path": file_path,
            "status": "pending",
            "test_coverage": [],
            "created_date": datetime.now().isoformat(),
        }
    )
    FINDINGS_FILE.write_text(json.dumps(data, indent=2))
    print(f"Added finding: {finding_id}")


def resolve_finding(finding_id: str, test_names: list[str]):
    """Mark finding as resolved with test coverage."""
    data = load_findings()
    for finding in data["findings"]:
        if finding["id"] == finding_id:
            finding["status"] = "resolved"
            finding["test_coverage"] = test_names
            finding["resolved_date"] = datetime.now().isoformat()
            FINDINGS_FILE.write_text(json.dumps(data, indent=2))
            print(f"Resolved finding: {finding_id}")
            return
    print(f"Finding {finding_id} not found")


def get_pending_high_severity():
    """Get pending high-severity findings for CI gates."""
    data = load_findings()
    return [
        f
        for f in data["findings"]
        if f["status"] == "pending" and f["severity"] == "high"
    ]


# CLI usage:
# python scripts/track_findings.py add SEC-001 "SQL injection in search" high
# python scripts/track_findings.py resolve SEC-001 test_search_sql_injection
