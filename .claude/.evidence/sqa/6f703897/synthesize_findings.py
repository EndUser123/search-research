#!/usr/bin/env python3
"""Synthesize specialist findings into unified L0 findings list."""

import json
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any, Tuple, Set

# Read all specialist files
specialist_files = [
    "adversarial-io-validation-findings.json",
    "adversarial-state-machine-findings.json",
    "adversarial-performance-findings.json",
    "adversarial-logic-findings.json",
    "adversarial-security-findings.json",
    "adversarial-qa-findings.json",
    "adversarial-quality-findings.json",
    "adversarial-failure-modes-findings.json"
]

all_findings = []
for fname in specialist_files:
    fpath = Path(fname)
    if not fpath.exists():
        print(f"Warning: {fname} not found, skipping")
        continue
    with open(fpath) as f:
        data = json.load(f)
        findings = data.get("findings", [])
        for finding in findings:
            finding["_specialist"] = data.get("handoff", {}).get("agent_name", "unknown")
        all_findings.extend(findings)

print(f"Total findings from {len([f for f in specialist_files if Path(f).exists()])} specialists: {len(all_findings)}")

# Group by (file, line, category) for deduplication
grouped = defaultdict(list)
for finding in all_findings:
    location = finding.get("location", "")
    # Parse location to get file:line
    if ":" in location:
        file_part = location.split(":")[0]
        line_part = location.split(":")[1] if len(location.split(":")) > 1 else ""
        # Extract line number if present
        line_match = line_part.split("-")[0] if "-" in line_part else line_part
        try:
            line_num = int(line_match) if line_match.isdigit() else 0
        except:
            line_num = 0
    else:
        file_part = location
        line_num = 0

    # Normalize file path
    if file_part.startswith("P:"):
        file_part = file_part.replace("P:/packages/intelligence-stream/", "")
    elif "/" in file_part and not file_part.startswith("csf/"):
        file_part = "csf/" + file_part.split("/")[-1]

    category = finding.get("id", "")[:4]  # e.g., "IO-0", "PERF", etc.
    key = (file_part, line_num, category)
    grouped[key].append(finding)

print(f"\nDeduped to {len(grouped)} unique locations")

# Detect consensus (2+ specialists agree on same location)
consensus_items = []
duplicates = []
for key, findings_list in grouped.items():
    if len(findings_list) > 1:
        file_part, line_num, category = key
        # Check if different specialists
        specialists = set(f.get("_specialist") for f in findings_list)
        if len(specialists) > 1:
            consensus_items.append({
                "location": key,
                "count": len(findings_list),
                "specialists": list(specialists),
                "findings": findings_list
            })
        else:
            duplicates.append({
                "location": key,
                "count": len(findings_list),
                "findings": findings_list
            })

print(f"Consensus items (2+ specialists): {len(consensus_items)}")
print(f"Duplicate findings from same specialist: {len(duplicates)}")

# Build unified findings list
unified_findings = []
finding_id_counter = 1

# Process consensus items first
for item in consensus_items:
    file_part, line_num, category = item["location"]
    findings_list = item["findings"]

    # Resolve severity: use highest (CRITICAL > HIGH > MEDIUM > LOW)
    severity_order = {"CRITICAL": 4, "BLOCKER": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    max_severity = max(findings_list, key=lambda f: severity_order.get(f.get("severity", "LOW").upper(), 0))

    # Merge specialists
    specialists_who_reported = list(set(f.get("_specialist") for f in findings_list))

    unified_findings.append({
        "id": f"L0-{finding_id_counter:03d}",
        "severity": max_severity.get("severity", "MEDIUM").upper(),
        "location": f"{file_part}:{line_num}" if line_num > 0 else file_part,
        "title": max_severity.get("title") or max_severity.get("problem") or max_severity.get("description", ""),
        "description": max_severity.get("description", ""),
        "specialists": specialists_who_reported,
        "consensus_count": len(specialists_who_reported),
        "category": category,
        "impact": max_severity.get("impact") or max_severity.get("adversarial_scenario") or "",
        "recommendation": max_severity.get("recommendation", {}).get("action") if isinstance(max_severity.get("recommendation"), dict) else max_severity.get("recommendation", "")
    })
    finding_id_counter += 1

# Process non-consensus items
for key, findings_list in grouped.items():
    if len(findings_list) == 1:
        finding = findings_list[0]
        location = finding.get("location", "")

        # Parse location
        if ":" in location:
            file_part = location.split(":")[0]
            line_part = location.split(":")[1] if len(location.split(":")) > 1 else ""
            line_match = line_part.split("-")[0] if "-" in line_part else line_part
            try:
                line_num = int(line_match) if line_match.isdigit() else 0
            except:
                line_num = 0
        else:
            file_part = location
            line_num = 0

        # Normalize file path
        if file_part.startswith("P:"):
            file_part = file_part.replace("P:/packages/intelligence-stream/", "")
        elif "/" in file_part and not file_part.startswith("csf/"):
            file_part = "csf/" + file_part.split("/")[-1]

        category = finding.get("id", "")[:4]

        unified_findings.append({
            "id": f"L0-{finding_id_counter:03d}",
            "severity": finding.get("severity", "MEDIUM").upper(),
            "location": f"{file_part}:{line_num}" if line_num > 0 else file_part,
            "title": finding.get("title") or finding.get("problem") or finding.get("description", ""),
            "description": finding.get("description", ""),
            "specialists": [finding.get("_specialist", "unknown")],
            "consensus_count": 1,
            "category": category,
            "impact": finding.get("impact") or finding.get("adversarial_scenario") or "",
            "recommendation": finding.get("recommendation", {}).get("action") if isinstance(finding.get("recommendation"), dict) else finding.get("recommendation", "")
        })
        finding_id_counter += 1

# Sort by severity then by ID
severity_order = {"CRITICAL": 0, "BLOCKER": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
unified_findings.sort(key=lambda f: (severity_order.get(f["severity"], 99), f["id"]))

# Build metadata
specialist_summary = {}
for finding in all_findings:
    spec = finding.get("_specialist", "unknown")
    if spec not in specialist_summary:
        specialist_summary[spec] = {"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0}
    specialist_summary[spec]["total"] += 1
    sev = finding.get("severity", "MEDIUM").lower()
    if sev in ["critical", "blocker"]:
        specialist_summary[spec]["critical"] += 1
    elif sev == "high":
        specialist_summary[spec]["high"] += 1
    elif sev == "medium":
        specialist_summary[spec]["medium"] += 1
    elif sev == "low":
        specialist_summary[spec]["low"] += 1

# Build final output
synthesis = {
    "metadata": {
        "synthesis_type": "L0_unified_findings",
        "timestamp": "2026-04-09T12:00:00Z",
        "session_id": "6f703897",
        "specialists_analyzed": len([f for f in specialist_files if Path(f).exists()]),
        "total_raw_findings": len(all_findings),
        "deduped_findings": len(unified_findings),
        "consensus_items": len(consensus_items),
        "specialist_breakdown": specialist_summary
    },
    "findings": unified_findings
}

# Write output
output_path = Path("P:/.claude/.evidence/sqa/6f703897/L0_synthesis.json")
output_path.parent.mkdir(parents=True, exist_ok=True)
with open(output_path, "w") as f:
    json.dump(synthesis, f, indent=2)

print(f"\nSynthesis complete:")
print(f"  Total unified findings: {len(unified_findings)}")
print(f"  Consensus items (2+ specialists): {len(consensus_items)}")
print(f"  Output: {output_path}")

# Print severity breakdown
severity_counts = defaultdict(int)
for f in unified_findings:
    severity_counts[f["severity"]] += 1
print(f"\nSeverity breakdown:")
for sev in ["CRITICAL", "BLOCKER", "HIGH", "MEDIUM", "LOW"]:
    if sev in severity_counts:
        print(f"  {sev}: {severity_counts[sev]}")
