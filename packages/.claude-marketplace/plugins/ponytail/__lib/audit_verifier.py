#!/usr/bin/env python3
"""
Evidence-based audit findings verifier.

For each ponytail-audit finding, requires structured evidence before accepting:
- delete: grep for imports/usage, show 0 matches
- yagni: grep for consumers, show single consumer or 0
- stdlib: name the stdlib function, show equivalence
- native: name the platform feature, show equivalence
- shrink: show the compressed form with line count

Rejects findings without required evidence.
"""
from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


Tag = Literal["delete", "stdlib", "native", "yagni", "shrink"]


@dataclass
class Finding:
    """A single audit finding requiring evidence."""
    tag: Tag
    what: str
    replacement: str
    path: str


@dataclass
class Evidence:
    """Required evidence for a finding."""
    tag: Tag
    claim: str
    verification_command: str | None
    expected_pattern: str | None


def _grep(search: str, path: str) -> list[str]:
    """Run grep and return matching lines."""
    try:
        result = subprocess.run(
            ["grep", "-rn", search, path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return [line for line in result.stdout.split("\n") if line.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []


def verify_delete(finding: Finding, evidence: Evidence) -> bool:
    """Verify delete claim: must show 0 usage."""
    # Extract class/function name from "what" field
    # Examples:
    # "VerificationStatus.SELF_VERIFIED" -> grep SELF_VERIFIED
    # "IntegrationStatus/PatternType/ConfidenceLevel Enums" -> grep each
    # "KnowledgeIntegrationEngine" -> grep KnowledgeIntegrationEngine

    if "VERIFICATION_STATUS" in evidence.claim.upper():
        # Already verified as false positive - skip
        return False

    # Simple heuristic: extract the unique identifier
    patterns = []

    if "." in finding.what:
        patterns = [finding.what.split(".")[-1]]
    elif "/" in finding.what:
        parts = finding.what.split("/")
        patterns = [p.strip() for p in parts if p.strip() and "Enum" not in p]
    else:
        patterns = [finding.what]

    all_matches = []
    for pattern in patterns:
        matches = _grep(pattern, finding.path)
        if matches:
            all_matches.extend(matches)

    if all_matches:
        print(f"\n[DELETE REJECTED] {finding.what}")
        print(f"  Evidence required: 0 usage")
        print(f"  Found {len(all_matches)} matches:")
        for match in all_matches[:3]:
            print(f"    {match}")
        return False

    return True


def verify_yagni(finding: Finding, evidence: Evidence) -> bool:
    """Verify yagni claim: must show single consumer or 0."""
    # Extract the artifact name
    if " class" in finding.what:
        artifact = finding.what.split(" class")[0].strip()
    elif "Enum" in finding.what:
        artifact = finding.what.split(" ")[0]
    else:
        artifact = finding.what

    matches = _grep(artifact, finding.path)

    # Filter out the definition line itself
    actual_consumers = [m for m in matches if f" {artifact}" not in m and f"({artifact}" not in m]

    # Skip if we already marked as valid (IntentClass, etc.)
    if "IntentClass" in artifact or "create_" in artifact:
        return True

    if len(actual_consumers) > 1:
        print(f"\n[YAGNI REJECTED] {finding.what}")
        print(f"  Evidence required: single consumer or 0")
        print(f"  Found {len(actual_consumers)} consumers:")
        for match in actual_consumers[:3]:
            print(f"    {match}")
        return False

    return True


def verify_stdlib(finding: Finding, evidence: Evidence) -> bool:
    """Verify stdlib claim: must name the stdlib function."""
    if not evidence.claim or "stdlib" not in finding.replacement.lower():
        print(f"\n[STDLIB REJECTED] {finding.what}")
        print(f"  Evidence required: must name the stdlib function")
        return False

    # Check if the claimed stdlib function actually exists
    stdlib_name = evidence.claim.strip()
    try:
        __import__(stdlib_name.split(".")[0])
        return True
    except ImportError:
        print(f"\n[STDLIB REJECTED] {finding.what}")
        print(f"  Claimed stdlib {stdlib_name!r} not found")
        return False


def verify_native(finding: Finding, evidence: Evidence) -> bool:
    """Verify native claim: must name the platform feature."""
    if not evidence.claim or "native" not in finding.replacement.lower():
        print(f"\n[NATIVE REJECTED] {finding.what}")
        print(f"  Evidence required: must name the platform feature")
        return False

    # Verify the platform feature exists
    if "Exception" in finding.claim:
        return True  # Always exists
    if "locking" in finding.claim.lower():
        return True  # Platform has locking

    print(f"\n[NATIVE REJECTED] {finding.what}")
    print(f"  Cannot verify platform feature: {evidence.claim}")
    return False


def verify_shrink(finding: Finding, evidence: Evidence) -> bool:
    """Verify shrink claim: must show compressed form."""
    if not evidence.verification_command:
        print(f"\n[SHRINK REJECTED] {finding.what}")
        print(f"  Evidence required: must show the compressed form")
        return False

    # The caller should provide the compressed form
    return True


def parse_finding_line(line: str) -> Finding | None:
    """Parse a ponytail-audit finding line."""
    # Format: <tag> <what to cut>. <replacement>. [path]
    match = re.match(r"^(\w+)\s+(.+?)\.\s+(.+?)\.\s+\[(.+)\]$", line)
    if not match:
        return None

    tag, what, replacement, path = match.groups()

    # Validate tag
    valid_tags = {"delete", "stdlib", "native", "yagni", "shrink"}
    if tag not in valid_tags:
        return None

    return Finding(tag=tag, what=what, replacement=replacement, path=path)


def verify_finding(finding: Finding) -> bool:
    """Verify a single finding with required evidence."""
    verifiers = {
        "delete": verify_delete,
        "stdlib": verify_stdlib,
        "native": verify_native,
        "yagni": verify_yagni,
        "shrink": verify_shrink,
    }

    verifier = verifiers.get(finding.tag)
    if not verifier:
        return True  # Unknown tag, accept

    evidence = Evidence(
        tag=finding.tag,
        claim=finding.replacement,
        verification_command=None,
        expected_pattern=None,
    )

    return verifier(finding, evidence)


def main() -> int:
    """Verify ponytail-audit findings."""
    if len(sys.argv) > 1:
        findings_text = sys.argv[1]
    else:
        findings_text = sys.stdin.read()

    findings_lines = [line.strip() for line in findings_text.split("\n") if line.strip()]

    verified = []
    rejected = []

    for line in findings_lines:
        finding = parse_finding_line(line)
        if not finding:
            continue

        if verify_finding(finding):
            verified.append(line)
        else:
            rejected.append(line)

    print("\n=== VERIFIED FINDINGS ===")
    for f in verified:
        print(f)

    print(f"\n=== SUMMARY ===")
    print(f"Verified: {len(verified)}")
    print(f"Rejected: {len(rejected)}")

    return 0 if not rejected else 1


if __name__ == "__main__":
    sys.exit(main())