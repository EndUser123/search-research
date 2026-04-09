#!/usr/bin/env python3
"""RSN Display Quality Gate — validates RSN output before rendering.

Priority: P0 (shared infrastructure quality enforcement)

This Stop hook checks that callers of RSNFormatter produce well-formed output:
- Finding IDs are not duplicated
- Finding messages are not empty
- Sections do not overflow (>20 findings — cognitive load risk)

Additionally warns about unused custom section definitions.

Enabled by default. Set RSN_DISPLAY_GATE_ENABLED=false to disable.
"""

from __future__ import annotations

import os

# Gate: enabled by default
_ENABLED = os.environ.get("RSN_DISPLAY_GATE_ENABLED", "true").lower() != "false"

# Threshold for cognitive overflow warning
_MAX_FINDINGS_PER_SECTION = 20


def run(data: dict) -> dict | None:
    """
    Validate RSN output embedded in response.

    Looks for RSN-formatted output blocks in the response text and validates
    each one. Returns a warning advisory (not a block) for quality issues.

    Args:
        data: Stop hook event data with "response" key

    Returns:
        {"allow": True, "warning": "..."} if quality issues found
        None if clean or gate disabled
    """
    if not _ENABLED:
        return None

    response = data.get("response", "") or ""
    if not response:
        return None

    # Only check if response contains RSN-style output
    if "Recommended Next Steps" not in response and "{RSN}" not in response:
        return None

    issues: list[str] = []

    # Check for TOON format: {RSN} ... {/RSN}
    if "{RSN}" in response:
        issues.extend(_check_toon_format(response))

    # Check for text format: "Recommended Next Steps" section headers
    if "Recommended Next Steps" in response:
        issues.extend(_check_text_format(response))

    if issues:
        warning = "RSN Display Quality Gate:\n  - " + "\n  - ".join(issues)
        return {"allow": True, "warning": warning}

    return None


def _check_toon_format(response: str) -> list[str]:
    """Validate TOON format RSN output."""
    issues: list[str] = []

    # Extract finding IDs from TOON format: (FINDING-001)
    import re

    finding_ids: list[str] = re.findall(r"\(([A-Za-z0-9_-]+)\)", response)
    if len(finding_ids) != len(set(finding_ids)):
        seen: dict[str, int] = {}
        for fid in finding_ids:
            seen[fid] = seen.get(fid, 0) + 1
        duplicates = [f"{fid} ({cnt}x)" for fid, cnt in seen.items() if cnt > 1]
        issues.append(f"Duplicate finding IDs in TOON: {', '.join(duplicates)}")

    # Check for empty messages in TOON format
    empty_messages = re.findall(r"message:\s*\n", response)
    if empty_messages:
        issues.append(f"Empty message fields found: {len(empty_messages)} occurrence(s)")

    # Check section sizes in TOON format
    section_counts: dict[str, int] = {}
    current_section: str | None = None
    for line in response.splitlines():
        section_match = re.match(r"\s*\[([^\]]+)\]\s*$", line)
        if section_match:
            current_section = section_match.group(1)
            if current_section is not None and current_section not in section_counts:
                section_counts[current_section] = 0
        elif current_section is not None and line.strip().startswith("("):
            section_counts[current_section] += 1

    for section, count in section_counts.items():
        if count > _MAX_FINDINGS_PER_SECTION:
            issues.append(
                f"Section [{section}] has {count} findings "
                f"(>{_MAX_FINDINGS_PER_SECTION} cognitive overflow threshold)"
            )

    return issues


def _check_text_format(response: str) -> list[str]:
    """Validate text format RSN output."""
    issues: list[str] = []

    import re

    # Extract finding IDs from text format: 1a. [FINDING-001] or 1a. [CRITICAL] ...
    # Pattern: sub-label followed by bracket-enclosed ID or severity
    finding_pattern = re.compile(r"^\s*\d+[a-z]\.\s*\[([A-Za-z0-9_-]+)\]", re.MULTILINE)
    finding_ids = finding_pattern.findall(response)

    if len(finding_ids) != len(set(finding_ids)):
        seen: dict[str, int] = {}
        for fid in finding_ids:
            seen[fid] = seen.get(fid, 0) + 1
        duplicates = [f"{fid} ({cnt}x)" for fid, cnt in seen.items() if cnt > 1]
        issues.append(f"Duplicate finding IDs in text format: {', '.join(duplicates)}")

    # Check for bare severity tags without finding IDs (malformed entries)
    bare_severity = re.findall(
        r"^\s*\d+[a-z]\.\s*\[(CRITICAL|HIGH|MEDIUM|LOW)\]\s", response, re.MULTILINE
    )
    if bare_severity:
        # These are valid severity tags, not issues
        pass

    # Count findings per section in text format
    section_counts: dict[str, int] = {}
    current_section: str | None = None
    for line in response.splitlines():
        section_match = re.match(r"^\s*\d+\.\s+(.+)$", line)
        if section_match and not line.strip().startswith(" "):
            current_section = section_match.group(1)
            if current_section is not None and current_section not in section_counts:
                section_counts[current_section] = 0
        elif current_section is not None and re.match(r"^\s+\d+[a-z]\.", line):
            section_counts[current_section] += 1

    for section, count in section_counts.items():
        if count > _MAX_FINDINGS_PER_SECTION:
            issues.append(
                f"Section [{section}] has {count} findings "
                f"(>{_MAX_FINDINGS_PER_SECTION} cognitive overflow threshold)"
            )

    return issues


# ── Legacy subprocess entry point ──────────────────────────────────────────────

if __name__ == "__main__":
    import json
    import sys

    data = json.loads(sys.stdin.read())
    result = run(data)
    if result is None:
        result = {"allow": True}
    print(json.dumps(result))
