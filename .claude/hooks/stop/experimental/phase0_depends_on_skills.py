#!/usr/bin/env python3
"""
Phase 0 depends_on_skills gate.

Extracted from Stop_router.py (lines 141–264). Original author: Stop_router.py.

CLASSIFICATION: Integrate as blocking gate (production candidate)
ORIGIN: stop/experimental/ — router-derived validator

Purpose:
    Phase 0 gate that enforces skill dependency chains. Skills declaring
    depends_on_skills in SKILL.md frontmatter must have step-1 evidence
    present before they are considered ready.

    BLOCKS if:
      - Skill has depends_on_skills
      - Step-1 evidence file is missing, empty, or corrupt

    PASSES (returns None) if:
      - Gate disabled via DEPENDS_ON_SKILLS_GATE_ENABLED=false
      - No skill detected in transcript
      - Skill has no depends_on_skills
      - No terminal_id resolvable
      - Step-1 evidence file exists and is valid JSONL

Evidence file format:
    ~/.claude/.evidence/{skill}-{terminal}/step_{step1_name}.jsonl
    Must be non-empty and have a valid JSON line as first entry.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_HOOKS_DIR = Path(__file__).resolve().parent.parent
_HOOKS_ROOT_DIR = _HOOKS_DIR.parent
_EVIDENCE_ROOT = Path.home() / ".claude" / ".evidence"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_enabled(env_var: str, default_enabled: bool) -> bool:
    raw = os.environ.get(env_var)
    if raw is None:
        return default_enabled
    return raw.strip().lower() not in {"0", "false", "no", "off"}


def _detect_skill_from_transcript(transcript_entries: list[dict[str, Any]]) -> str | None:
    """Scan transcript for skill invocation patterns like /retro, /gto, etc.

    Transcript entries have structure:
        {"type": "user", "message": {"role": "user", "content": "..."}}
    where content contains XML-style command tags:
        <command-name>/skillname</command-name>
        <command-args>args</command-args>
    """
    command_pattern = re.compile(r"<command-name>(/[^<]+)</command-name>")
    for entry in reversed(transcript_entries[-10:]):  # Last 10 entries
        entry_text = ""
        if "text" in entry:
            entry_text = entry["text"]
        elif isinstance(entry.get("message"), dict):
            content = entry["message"].get("content", "")
            if isinstance(content, str):
                entry_text = content
        match = command_pattern.search(entry_text)
        if match:
            return match.group(1).lstrip("/")
    return None


def _get_depends_on_skills(skill_name: str) -> list[str] | None:
    """Read skill's SKILL.md and return depends_on_skills list or None."""
    skills_dirs = [
        _HOOKS_ROOT_DIR / "skills",
        Path.home() / ".claude" / "skills",
    ]
    for skills_dir in skills_dirs:
        skill_md = skills_dir / skill_name / "SKILL.md"
        if skill_md.exists():
            try:
                content = skill_md.read_text(encoding="utf-8")
            except OSError:
                continue
            match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
            if match:
                frontmatter = match.group(1)
                try:
                    data = yaml.safe_load(frontmatter)
                    deps = data.get("depends_on_skills", [])
                    if deps:
                        return [deps.strip()] if isinstance(deps, str) else [str(d).strip() for d in deps]
                except yaml.YAMLError:
                    continue
    return None


def _get_evidence_dir_for_skill(skill_name: str, terminal_id: str) -> Path:
    """Resolve evidence directory for a skill+terminal pair with path sanitization."""
    safe_skill = re.sub(r"[^a-z0-9_-]", "", skill_name.lower())
    safe_terminal = re.sub(r"[^a-z0-9_-]", "", terminal_id.lower())
    return _EVIDENCE_ROOT / f"{safe_skill}-{safe_terminal}"


def _check_step1_evidence(evidence_dir: Path, step1_name: str) -> tuple[bool, str]:
    """Check if step-1 evidence file exists, is non-empty, and valid JSONL.

    Returns (True, "step-1 evidence valid") on success.
    Returns (False, "reason") on failure.
    """
    step_file = evidence_dir / f"step_{step1_name}.jsonl"
    if not step_file.exists():
        return False, f"step-1 evidence missing: {step_file}"
    if step_file.stat().st_size == 0:
        return False, f"step-1 evidence empty: {step_file}"
    try:
        first_line = step_file.read_text(encoding="utf-8").split("\n")[0]
        json.loads(first_line)
        return True, "step-1 evidence valid"
    except (json.JSONDecodeError, IndexError):
        return False, f"step-1 evidence corrupted: {step_file}"


# ---------------------------------------------------------------------------
# Gate
# ---------------------------------------------------------------------------

def run(data: dict[str, Any]) -> dict[str, Any] | None:
    """Phase 0 gate: verify step-1 evidence exists for depends_on_skills skills.

    Input contract:
        transcript_entries: list of dicts (from Stop.py payload)
        terminal_id: str (from Stop.py payload)

    Returns None (pass) if:
        - DEPENDS_ON_SKILLS_GATE_ENABLED is false
        - Skill has no depends_on_skills
        - Skill name or terminal_id cannot be resolved (bypass)
        - Evidence file exists and is valid JSONL

    Returns {"decision": "block", "reason": ..., "metadata": {...}} if:
        - Skill has depends_on_skills but step-1 evidence is missing/empty/corrupt

    Metadata fields:
        skill: str — name of the skill with depends_on_skills
        depends_on: list[str] — the depends_on_skills chain
        missing_step: str — the step that is missing evidence
        evidence_dir: str — resolved evidence directory path
        evidence_checked: list[str] — evidence paths checked
        step_file: str — the step file that was checked and failed
        failure_reason: str — why the check failed (missing/empty/corrupt)
    """
    if not _is_enabled("DEPENDS_ON_SKILLS_GATE_ENABLED", True):
        return None

    transcript_entries: list[dict[str, Any]] = data.get("transcript_entries", [])
    if not transcript_entries:
        return None

    skill_name = _detect_skill_from_transcript(transcript_entries)
    if not skill_name:
        return None

    depends_on = _get_depends_on_skills(skill_name)
    if not depends_on:
        return None

    terminal_id = str(data.get("terminal_id", "")).strip()
    if not terminal_id:
        return None

    step1_name = depends_on[0]
    evidence_dir = _get_evidence_dir_for_skill(skill_name, terminal_id)
    step_file = evidence_dir / f"step_{step1_name}.jsonl"
    exists, reason = _check_step1_evidence(evidence_dir, step1_name)
    if not exists:
        return {
            "decision": "block",
            "reason": f"Phase 0: step-1 evidence required for depends_on_skills workflow. {reason}",
            "blocking_hook": "phase0_depends_on_skills",
            "metadata": {
                "skill": skill_name,
                "depends_on": depends_on,
                "missing_step": step1_name,
                "evidence_dir": str(evidence_dir),
                "evidence_checked": [str(step_file)],
                "step_file": str(step_file),
                "failure_reason": reason,
            },
        }
    return None


def main() -> None:
    """CLI entry point for standalone testing."""
    import sys
    try:
        raw = sys.stdin.read().strip()
        input_data = json.loads(raw) if raw else {}
    except Exception:
        input_data = {}
    result = run(input_data)
    if result:
        print(json.dumps(result))
        sys.exit(1)
    print("{}")


if __name__ == "__main__":
    main()
