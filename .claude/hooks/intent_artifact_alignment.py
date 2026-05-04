"""Intent vs Artifacts alignment gate.

Detects when the assistant did adjacent work instead of modifying the
requested targets. Warns when:
1. User names specific file/command/skill targets for modification
2. Assistant's tool operations miss those targets
3. Response may be claiming completion on unmodified targets

Skipped for non-analysis turns via turn-mode quality suppression.

Quality gate classification: quality (respects turn-mode suppression).
"""

from __future__ import annotations

import re
from dataclasses import dataclass


# ---------------------------------------------------------------------------
# Target spec
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TargetSpec:
    kind: str   # "file" | "command" | "skill"
    value: str  # file path, command name, or skill name
    source: str  # "prompt"


# ---------------------------------------------------------------------------
# Extraction: targets from user prompt
# ---------------------------------------------------------------------------

# Modification verbs that create a target expectation
_MODIFICATION_VERB_RE = re.compile(
    r"(?P<verb>modify|edit|update|change|add|fix|create|write|implement"
    r"|refactor|patch)\b",
    re.IGNORECASE,
)

# Verb + file path  ("modify Stop.py", "add tests to test_foo.py")
_TARGET_EXTRACT_RE = re.compile(
    r"(?P<verb>modify|edit|update|change|add\s+(?:\w+\s+)*?to|fix|create|write|implement"
    r"|refactor|patch)\s+"
    r"(?:the\s+)?(?P<path>[\w./\\-]+\.\w+)",
    re.IGNORECASE,
)

# "... to <path>" after a verb context (e.g., "add the gate to Stop.py")
_TO_PATH_RE = re.compile(
    r"\bto\s+(?:the\s+)?(?P<path>[\w./\\-]+\.(?:py|md|json|yml|yaml|txt|sh|ps1|toml))",
    re.IGNORECASE,
)

# "in <path>" after a verb context
_IN_PATH_RE = re.compile(
    r"\bin\s+(?:the\s+)?(?P<path>[\w./\\-]+\.(?:py|md|json|yml|yaml|txt|sh|ps1|toml))",
    re.IGNORECASE,
)

# Command targets  ("run pytest", "execute the tests")
_COMMAND_TARGET_RE = re.compile(
    r"(?:run|execute|invoke|call)\s+(?:the\s+)?(?P<cmd>[\w][\w.\-]*)",
    re.IGNORECASE,
)

# Skill targets  ("use /rca", "invoke /bf")
_SKILL_TARGET_RE = re.compile(
    r"(?:use|invoke|run|call|execute)\s+(?:the\s+)?(?P<skill>/[\w\-]+)",
    re.IGNORECASE,
)

# Edit/Write tools indicate file modification
_MODIFICATION_TOOLS = {"Edit", "Write"}


def extract_targets_from_prompt(prompt: str) -> list[TargetSpec]:
    """Extract modification targets from user's prompt."""
    targets: list[TargetSpec] = []
    seen: set[tuple[str, str]] = set()

    def _add(kind: str, value: str) -> None:
        key = (kind, value.lower())
        if key not in seen:
            seen.add(key)
            targets.append(TargetSpec(kind=kind, value=value, source="prompt"))

    # File targets: verb + path
    for m in _TARGET_EXTRACT_RE.finditer(prompt):
        _add("file", m.group("path"))

    # File targets: "in <path>" when modification verbs present
    if _MODIFICATION_VERB_RE.search(prompt):
        for m in _IN_PATH_RE.finditer(prompt):
            _add("file", m.group("path"))
        for m in _TO_PATH_RE.finditer(prompt):
            _add("file", m.group("path"))

    # Command targets
    for m in _COMMAND_TARGET_RE.finditer(prompt):
        cmd = m.group("cmd")
        # Filter out common non-commands
        if cmd.lower() not in ("the", "a", "an", "this", "that", "it"):
            _add("command", cmd)

    # Skill targets
    for m in _SKILL_TARGET_RE.finditer(prompt):
        _add("skill", m.group("skill"))

    return targets


# ---------------------------------------------------------------------------
# Extraction: artifacts from tool events
# ---------------------------------------------------------------------------

def _extract_file_path(event: dict) -> str:
    """Extract file path from a tool event (flat or nested format)."""
    path = event.get("file_path", "")
    if path:
        return str(path)
    inp = event.get("input", {})
    if isinstance(inp, dict):
        path = inp.get("file_path", "")
        if path:
            return str(path)
    return ""


def extract_modified_paths(tool_events: list[dict]) -> set[str]:
    """Extract file paths that were modified via Edit/Write."""
    modified: set[str] = set()
    for event in tool_events:
        if not isinstance(event, dict):
            continue
        name = event.get("name", "")
        if name in _MODIFICATION_TOOLS:
            path = _extract_file_path(event)
            if path:
                modified.add(path)
    return modified


def extract_executed_commands(tool_events: list[dict]) -> set[str]:
    """Extract command strings from Bash tool events."""
    commands: set[str] = set()
    for event in tool_events:
        if not isinstance(event, dict):
            continue
        if event.get("name") == "Bash":
            cmd = event.get("command", "")
            if cmd:
                commands.add(str(cmd))
    return commands


def extract_invoked_skills(tool_events: list[dict]) -> set[str]:
    """Extract skill names from Skill tool events."""
    skills: set[str] = set()
    for event in tool_events:
        if not isinstance(event, dict):
            continue
        if event.get("name") == "Skill":
            skill = event.get("skill", "")
            if not skill:
                inp = event.get("input", {})
                if isinstance(inp, dict):
                    skill = inp.get("skill", "")
            if skill:
                skills.add(str(skill))
    return skills


# ---------------------------------------------------------------------------
# Path normalization
# ---------------------------------------------------------------------------

def _normalize_path(path: str) -> str:
    """Normalize a path for loose comparison."""
    return path.replace("\\", "/").lower().rstrip("/")


def _paths_match(target: str, candidate: str) -> bool:
    """Check if two paths refer to the same file (loose matching)."""
    t = _normalize_path(target)
    c = _normalize_path(candidate)
    if t == c:
        return True
    # Suffix match: "Stop.py" matches "P:/.claude/hooks/Stop.py"
    if c.endswith(t) or t.endswith(c):
        return True
    # Basename match
    if t.split("/")[-1] == c.split("/")[-1]:
        return True
    return False


def _command_matches(target: str, command: str) -> bool:
    """Check if a command string contains the target command."""
    return target.lower() in command.lower()


def _skill_matches(target: str, skill: str) -> bool:
    """Check if a skill invocation matches the target."""
    # "/rca" matches "rca" or "/rca"
    t = target.lstrip("/").lower()
    s = skill.lstrip("/").lower()
    return t == s or t in s


# ---------------------------------------------------------------------------
# Alignment check
# ---------------------------------------------------------------------------

# Completion claim patterns (escalate warn → block when present)
_COMPLETION_CLAIM_RE = re.compile(
    r"(?i)(?:(?:done|complete|finished|implemented|updated|added|fixed|ready)"
    r"|(?:✅|all\s+(?:tests?\s+)?pass))",
)


def check_alignment(
    prompt: str,
    tool_events: list[dict],
    response: str = "",
) -> dict | None:
    """Check if modification targets align with actual tool operations.

    Returns None if aligned or no targets detected.
    Returns dict with warning info if misalignment detected.
    """
    targets = extract_targets_from_prompt(prompt)
    if not targets:
        return None

    modified_files = extract_modified_paths(tool_events)
    executed_commands = extract_executed_commands(tool_events)
    invoked_skills = extract_invoked_skills(tool_events)

    missed: list[TargetSpec] = []
    for t in targets:
        if t.kind == "file":
            if not any(_paths_match(t.value, f) for f in modified_files):
                missed.append(t)
        elif t.kind == "command":
            if not any(_command_matches(t.value, c) for c in executed_commands):
                missed.append(t)
        elif t.kind == "skill":
            if not any(_skill_matches(t.value, s) for s in invoked_skills):
                missed.append(t)

    if not missed:
        return None

    claims_completion = bool(response and _COMPLETION_CLAIM_RE.search(response))
    severity = "block" if claims_completion else "warn"

    missed_desc = [f"{t.value} ({t.kind})" for t in missed]
    touched_desc = list(modified_files) or ["(none)"]

    return {
        "decision": severity,
        "reason": (
            f"INTENT-ARTIFACT MISALIGNMENT: User asked to modify "
            f"{', '.join(missed_desc)} but these targets were not touched. "
            f"Assistant modified: {', '.join(touched_desc)}. "
            f"{'Response claims completion. ' if claims_completion else ''}"
            f"Apply changes to the requested targets."
        ),
        "systemMessage": (
            f"INTENT-ARTIFACT MISALIGNMENT\n\n"
            f"Missed targets: {', '.join(missed_desc)}\n"
            f"Files modified: {', '.join(touched_desc)}\n"
            f"{'⚠️ Completion claimed but targets not touched. ' if claims_completion else ''}"
            f"Apply changes to the requested targets before claiming completion."
        ),
        "missed_targets": [t.value for t in missed],
        "modified_files": list(modified_files),
        "claims_completion": claims_completion,
    }
