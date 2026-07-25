#!/usr/bin/env python3
"""Wiki save gate — shared deterministic checker for skill wiki-save steps.

Per wiki concept `code-orchestrates-model-judges-skill-scale`: the save gate
is a deterministic node (LangGraph conditional edge). It checks whether a
skill that should have saved findings to the wiki actually did. The model
cannot bypass a failed gate by rationalizing.

Usage:
    python wiki_save_gate.py --artifact <run-artifact-path> --skill <name>
                              [--session <sid>] [--verbose]

Exit codes:
    0 = pass (wiki concept written OR explicit no-findings marker present)
    1 = fail (expected a wiki concept, none found, no explicit no-findings)
    2 = n/a (no wiki-worthy findings expected — skill produced nothing systemic)
    3 = error (invalid invocation)

The gate reads the skill's run artifact (findings.json, AAR report, telemetry
output, etc.) and checks:
  1. Did the artifact claim systemic/architectural findings?
  2. If yes, was a wiki concept written for this skill+session?
  3. If no concept, was an explicit "no wiki-worthy findings" marker written?

The "explicit no-findings marker" is a sidecar file the skill writes when it
ran the save step but found nothing qualifying. This is the structural fix
for closure-pressure bypass: the model cannot just silently skip the save —
it must either write a concept OR write the marker.

Sidecar file path: <artifact_dir>/._wiki_save_status.json
  {"status": "saved" | "no_findings", "reason": "<one line>", "skill": "<name>"}
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

WIKI_CONCEPTS = Path("P:/.data/wiki/concepts")
WIKI_LOG = Path("P:/.data/wiki/log.md")
SIDECAR_NAME = "._wiki_save_status.json"

# Patterns that indicate a finding worth saving
SYSTEMIC_MARKERS = [
    r"\bARCHITECTURE\b",
    r"\bSYSTEMIC\b",
    r"\bPROBLEM_CLASS\b",
    r"\bstructural\s+fix\b",
    r"\bcross-session\b",
    r"\broot\s+cause\b.*\barchitectural\b",
    r"severity.*?(?:BLOCK|CRITICAL|HIGH)",
    r"class.*?architectural",
]

# Compile once
SYSTEMIC_RE = [re.compile(p, re.IGNORECASE) for p in SYSTEMIC_MARKERS]


def read_artifact(artifact_path: Path) -> str:
    """Read the skill's run artifact as text."""
    if not artifact_path.exists():
        return ""
    if artifact_path.suffix == ".json":
        try:
            data = json.loads(artifact_path.read_text(encoding="utf-8"))
            return json.dumps(data, indent=2)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return artifact_path.read_text(encoding="utf-8", errors="replace")
    return artifact_path.read_text(encoding="utf-8", errors="replace")


def has_systemic_findings(artifact_text: str) -> bool:
    """Check whether the artifact contains systemic/architectural findings."""
    if not artifact_text:
        return False
    return any(regex.search(artifact_text) for regex in SYSTEMIC_RE)


def read_sidecar(artifact_path: Path) -> dict | None:
    """Read the sidecar status file if it exists."""
    sidecar = artifact_path.parent / SIDECAR_NAME
    if not sidecar.exists():
        return None
    try:
        return json.loads(sidecar.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def check_wiki_concept_written(skill: str, session: str | None, artifact_mtime: float) -> bool:
    """Check whether a wiki concept was written after the artifact was created.

    Looks for concepts with the skill name in the source/timeline, or concepts
    created within a short window after the artifact's mtime.
    """
    if not WIKI_CONCEPTS.exists():
        return False

    # Window: artifact mtime to now + small buffer
    window_start = artifact_mtime - 60  # 1 min before (clock skew)
    window_end = datetime.now().timestamp() + 60

    # Also check the wiki log for a recent entry mentioning the skill
    log_text = ""
    if WIKI_LOG.exists():
        try:
            log_text = WIKI_LOG.read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass

    for concept in WIKI_CONCEPTS.glob("*.md"):
        try:
            stat = concept.stat()
            mtime = stat.st_mtime
            # Was this concept written in the window?
            if window_start <= mtime <= window_end:
                # Does it reference this skill?
                content = concept.read_text(encoding="utf-8", errors="replace")
                skill_match = skill.lower() in content.lower()
                session_match = bool(session and f"session-{session[:8]}" in content)
                if skill_match or session_match:
                    return True
                # Or does the wiki log have a recent entry for this skill?
                if skill.lower() in log_text.lower()[-2000:]:
                    return True
        except (OSError, PermissionError):
            continue

    return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Wiki save gate — check whether a skill saved its findings to the wiki"
    )
    parser.add_argument("--artifact", required=True, help="Path to the skill's run artifact (findings.json, report, etc.)")
    parser.add_argument("--skill", required=True, help="Skill name (e.g., 'aar', 'review', 'tp')")
    parser.add_argument("--session", default=None, help="Session ID (for provenance matching)")
    parser.add_argument("--verbose", action="store_true", help="Print diagnostic detail")
    args = parser.parse_args()

    artifact_path = Path(args.artifact)
    if not artifact_path.exists():
        if args.verbose:
            print(f"GATE: artifact not found: {artifact_path}", file=sys.stderr)
        return 2  # n/a — no artifact means no findings to save

    # Read the artifact
    artifact_text = read_artifact(artifact_path)
    artifact_mtime = artifact_path.stat().st_mtime

    # Did the skill produce systemic findings?
    systemic = has_systemic_findings(artifact_text)

    if not systemic:
        if args.verbose:
            print(f"GATE: no systemic findings in artifact — nothing to save", file=sys.stderr)
        return 2  # n/a

    # Was a wiki concept written?
    concept_written = check_wiki_concept_written(args.skill, args.session, artifact_mtime)

    if concept_written:
        if args.verbose:
            print(f"GATE: PASS — wiki concept written for skill '{args.skill}'", file=sys.stderr)
        return 0

    # Was an explicit no-findings marker written?
    sidecar = read_sidecar(artifact_path)
    if sidecar and sidecar.get("status") in ("saved", "no_findings"):
        if sidecar.get("status") == "saved":
            # Skill claims it saved but gate didn't find the concept — discrepancy
            if args.verbose:
                print(f"GATE: FAIL — sidecar claims 'saved' but no concept found matching skill '{args.skill}'", file=sys.stderr)
            return 1
        else:
            # Explicit no_findings — skill ran the gate and decided nothing qualified
            if args.verbose:
                print(f"GATE: PASS — explicit no_findings marker: {sidecar.get('reason', '(no reason)')}", file=sys.stderr)
            return 0

    # Fail: systemic findings, no concept, no explicit marker
    if args.verbose:
        print(
            f"GATE: FAIL — systemic findings in artifact, but no wiki concept written "
            f"and no explicit no_findings marker. Skill '{args.skill}' skipped the save step.",
            file=sys.stderr,
        )
    print(
        f"⚠️ WIKI SAVE GATE FAILED for '{args.skill}': the artifact contains systemic findings "
        f"but no wiki concept was written and no explicit no-findings marker exists. "
        f"Either write a concept to P:/.data/wiki/concepts/ or write a sidecar "
        f"'{SIDECAR_NAME}' with status='no_findings' and a reason.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
