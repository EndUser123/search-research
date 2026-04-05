#!/usr/bin/env python3
"""
Auto-verify implementation plans v2 — strict readiness gating.

Checks performed:
1. Placeholder detection — FAIL if any placeholder residue found
2. Section completeness — all required sections present
3. Solo-dev violations — no team coordination patterns
4. RTM coverage — requirements mapped to tasks
5. Contradiction checks — FAIL if plan claims ready but has unresolved blockers
6. Disposition checks — every blocker/high finding has machine-readable disposition
7. Plan-purity checks — FAIL if plan contains raw findings tables or verification dumps
8. Status header — FAIL if status header missing or malformed
9. Stateful contract checks — FAIL if applicable plans leave identity, ordering,
   dedupe, invalidation, source-of-truth, or isolation semantics ambiguous, if
   tests contradict those contracts, or if the documented mechanisms cannot fire
   under the plan's own invariants
10. Contract matrix checks — FAIL if contract-sensitive plans omit required
    matrix fields, per-row packet references, or test bindings
11. Contract authority drift — FAIL if planning-owned boundary semantics drift
    from the active planning contract or use unrecognized phase-precondition
    metadata to claim readiness

Usage:
    python P:/.claude/skills/planning/__lib/auto_verify.py <plan_path>

Output:
    <plan_path>.review.result.json with verification results
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

# DEPTH RULE: When skills/ layer is added, increment parents[N] by 1.
# e.g. from planning/__lib__/: parents[2]→[3] (sdlc/ is 3 levels up from __lib__/)
_ROOT = Path(__file__).resolve()
_CONTRACT_PRIMITIVES_SRC = _ROOT.parents[3] / "contract-primitives" / "src"
if _CONTRACT_PRIMITIVES_SRC.exists() and str(_CONTRACT_PRIMITIVES_SRC) not in sys.path:
    sys.path.insert(0, str(_CONTRACT_PRIMITIVES_SRC))

from contract_primitives import (
    ACTIVE_PLAN_ARTIFACT_FAILURE_BEHAVIOR,
    PLACEHOLDER_BINDINGS,
    REQUIRED_PLAN_MATRIX_FIELDS,
    extract_markdown_table,
    find_contract_boundary_rows,
)

# Required plan sections (v2 canonical names, with legacy aliases accepted for compatibility)
SECTION_ALIASES = {
    "goal": ["Goal", "Problem", "Problem Statement"],
    "current_state": [
        "Current State with Evidence",
        "Current state with evidence",
        "Current State",
        "Context",
        "Context Analysis",
        "Background",
        "Existing Implementation",
        "Existing Implementation Discovery",
        "Current Implementation",
    ],
    "design_decisions": [
        "Design Decisions and Invariants",
        "Design Decisions",
        "Design",
        "Solution",
        "Proposed Solution",
        "Approach",
    ],
    "implementation_changes": [
        "Implementation Changes",
        "Implementation Plan",
        "Implementation Steps",
        "Steps",
        "Tasks",
    ],
    "test_matrix": ["Test Matrix", "Test Coverage", "Test Discovery", "Tests", "Testing"],
    "assumptions": [
        "Assumptions/Defaults",
        "Assumptions and Defaults",
        "Assumptions",
        "Defaults",
        "Risks, Success Criteria, Dependencies",
    ],
    "open_questions": ["Open Questions", "Open Issues", "Questions"],
    "contract_authority_reference": ["Contract Authority Reference", "Contract-Authority Reference"],
    "contract_boundary_matrix": ["Contract Boundary Matrix", "Contract-Boundary Matrix"],
    "state_model_contracts": ["State Model Contracts", "State-Model Contracts"],
}

REQUIRED_SECTIONS = [
    SECTION_ALIASES[key][0]
    for key in [
        "goal",
        "current_state",
        "design_decisions",
        "implementation_changes",
        "test_matrix",
        "assumptions",
        "open_questions",
    ]
]

SOLO_DEV_VIOLATIONS = [
    r"stakeholder\s+approval",
    r"team\s+coordination",
    r"consensus\s+required",
    r"team\s+review",
    r"collaborative\s+effort",
    r"multi-?\s*team",
    r"cross-?\s*team",
    r"team\s+lead\s+approval",
]

REQUIRED_ADVERSARIAL_AGENTS = [
    "adversarial-compliance",
    "adversarial-logic",
    "adversarial-testing",
    "adversarial-security",
    "adversarial-failure-modes",
    "adversarial-critic",
]

ARCH_REMEDIATION_CATEGORIES = {
    "contract_ambiguity",
    "state_model",
    "schema_consistency",
    "identity_boundary",
    "contract_test_coherence",
    "mechanism_triggerability",
    "authority_drift",
}

ARCH_REMEDIATION_IDS = {
    "STATE-002",
}

# Placeholder patterns that block readiness
PLACEHOLDER_PATTERNS = [
    r"\bTODO\b",
    r"\bTBD\b",
    r"Describe the problem",
    r"Add risk analysis",
    r"path/to/",
    r"Component A",
    r"Component B",
    r"Criteria one",
    r"Criteria two",
    r"Describe the solution",
    r"Add test coverage",
    r"\*Add .+\*",  # Italicized "Add ..." like "*Add risk analysis*"
    r"\[ \] .+",  # Unchecked checkbox placeholders
]

# Patterns that indicate raw findings/verification merged into plan
PLAN_PURITY_VIOLATIONS = [
    r"##\s*Adversarial Findings",
    r"##\s*Verification Results",
    r"##\s*Verification Status",
    r"\|\s*ID\s*\|\s*Severity\s*\|\s*Finding",  # Findings table
    r"###\s*BLOCKER",
    r"###\s*HIGH",
    r"auto_verify.*:\s*READY",
    r"auto_verify.*:\s*BLOCKED",
    r"##\s*Findings.*(?:compliance|logic|testing|security)",  # Raw findings headers
]

STATEFUL_PLAN_PATTERNS = [
    r"\bwatermark\b",
    r"\bdedupe\b",
    r"\bdedup\b",
    r"\binvalidation\b",
    r"\bstale[- ]data\b",
    r"\bstale data immunity\b",
    r"\bterminal_id\b",
    r"\bturn_id\b",
    r"\bsession_id\b",
    r"\bevent log\b",
    r"\breplay\b",
    r"\bsource of truth\b",
    r"\bhandoff\b",
    r"\bresume\b",
    r"\brestore(?:d)?\b.{0,40}\b(?:state|session|payload|artifact|flow|context|history|resume)\b",
    r"\bledger\b",
    r"\bmulti-terminal\b",
]

PROVIDER_STATEFUL_PATTERNS = [
    r"\bprovider_instance_id\b",
    r"\bprovider_id\b",
    r"\bmulti-provider\b",
    r"\bprovider failover\b",
    r"\bprovider routing\b",
    r"\bprovider selection\b",
    r"\bprovider cache\b",
    r"\bfallback chain\b",
]

STATELESS_DECLARATION_PATTERNS = [
    r"\bthis plan is not stateful\b",
    r"\bnot stateful\b",
    r"\bstateless\b",
    r"\bno shared mutable state\b",
    r"\bno persistence\b",
    r"\beach .* call is independent\b",
    r"\bcall-scoped isolation\b",
]

NOT_APPLICABLE_DECLARATION_PATTERNS = [
    r"\bnot applicable\b",
    r"\bnot contract-sensitive\b",
    r"\bcontract[- ]sensitive\b.{0,20}\bno\b",
]

STATEFUL_CONTRADICTION_PATTERNS = [
    r"\bprovider_instance_id\b",
    r"\bprovider_id\b",
    r"\bsession_id\b",
    r"\bturn_id\b",
    r"\bterminal_id\b",
    r"\bwatermark\b",
    r"\breplay\b",
    r"\bevent log\b",
    r"\bsource of truth\b",
    r"\bmulti-terminal\b",
    r"\bmulti-provider\b",
]

ACCEPTANCE_PLACEHOLDER_PATTERNS = [
    r"^\s*tbd\s*$",
    r"^\s*tba\s*$",
    r"^\s*todo\s*$",
    r"^\s*to be decided\s*$",
    r"^\s*to be determined\s*$",
    r"^\s*n/?a\s*$",
    r"^\s*none\s*$",
]

AMBIGUOUS_CONTRACT_PATTERNS = [
    (
        "ordering/watermark",
        [
            r"(?:either|one of).{0,80}(?:ordering|watermark)",
            r"(?:ordering|watermark).{0,80}\b(?:either|or)\b",
            r"Alternative:.*(?:ordering|watermark)",
            r"parse numeric IDs?.{0,120}zero-padded",
            r"zero-padded.{0,120}parse numeric IDs?",
        ],
    ),
    (
        "dedupe",
        [
            r"(?:either|one of).{0,80}(?:dedupe|dedup)",
            r"(?:dedupe|dedup).{0,80}\b(?:either|or)\b",
            r"Alternative:.*(?:dedupe|dedup)",
        ],
    ),
    (
        "identity/isolation",
        [
            r"(?:either|one of).{0,80}(?:identity|terminal_id|provider_instance_id|isolation)",
            r"(?:identity|terminal_id|provider_instance_id|isolation).{0,80}\b(?:either|or)\b",
            r"Alternative:.*(?:identity|terminal_id|provider_instance_id|isolation)",
        ],
    ),
    (
        "freshness/invalidation",
        [
            r"(?:either|one of).{0,80}(?:invalidation|freshness|stale)",
            r"(?:invalidation|freshness|stale).{0,80}\b(?:either|or)\b",
            r"Alternative:.*(?:invalidation|freshness|stale)",
        ],
    ),
]

OPEN_QUESTION_BLOCKERS = [
    r"source of truth",
    r"authoritative",
    r"ordering",
    r"watermark",
    r"dedupe",
    r"dedup",
    r"invalidation",
    r"stale",
    r"freshness",
    r"task event",
    r"event source",
    r"isolation",
    r"terminal_id",
    r"provider_instance_id",
]


def extract_section_content(plan: str, section_name: str) -> str:
    """Extract content of a specific section from plan."""
    aliases_to_check = [section_name]
    for canonical_name, alias_list in SECTION_ALIASES.items():
        if section_name == canonical_name:
            aliases_to_check = alias_list
            break
        elif section_name in alias_list:
            aliases_to_check = alias_list
            break

    for alias in aliases_to_check:
        pattern = rf"^##\s+{re.escape(alias)}.*?(?=^##\s|\Z)"
        match = re.search(pattern, plan, re.DOTALL | re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(0)
    return ""


def is_stateful_plan(plan: str) -> bool:
    """Heuristic detection for plans that need state/history/provider contract checks."""
    lowered = plan.lower()
    searchable_text = _strip_negative_declaration_sections(plan)
    frontmatter = parse_frontmatter(plan)
    explicit_stateful = frontmatter.get("stateful", "").strip().lower()
    if explicit_stateful in {"true", "yes"}:
        return True
    if explicit_stateful in {"false", "no", "stateless"}:
        return False

    state_model_section = extract_section_content(plan, "state_model_contracts")
    if state_model_section and _has_negative_declaration(state_model_section):
        return any(
            re.search(pattern, searchable_text, re.IGNORECASE)
            for pattern in [*STATEFUL_PLAN_PATTERNS, *PROVIDER_STATEFUL_PATTERNS]
        )

    return any(
        re.search(pattern, searchable_text, re.IGNORECASE)
        for pattern in [*STATEFUL_PLAN_PATTERNS, *PROVIDER_STATEFUL_PATTERNS]
    )


def parse_frontmatter(plan: str) -> dict[str, str]:
    """Parse simple YAML-like frontmatter into a flat key/value dict."""
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?", plan, re.DOTALL)
    if not match:
        return {}

    frontmatter = {}
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = value.strip()

    return frontmatter


def _parse_int_frontmatter(frontmatter: dict[str, str], key: str) -> int | None:
    value = frontmatter.get(key)
    if value is None:
        return None
    value = value.strip().strip('"').strip("'")
    if not re.fullmatch(r"\d+", value):
        return None
    return int(value)


def _has_negative_declaration(section_text: str) -> bool:
    lowered = section_text.lower()
    return any(
        re.search(pattern, lowered, re.IGNORECASE)
        for pattern in [*STATELESS_DECLARATION_PATTERNS, *NOT_APPLICABLE_DECLARATION_PATTERNS]
    )


def _strip_negative_declaration_sections(plan: str) -> str:
    searchable = plan.lower()
    for section_name in [
        "state_model_contracts",
        "contract_authority_reference",
        "contract_boundary_matrix",
    ]:
        section_text = extract_section_content(plan, section_name)
        if section_text and _has_negative_declaration(section_text):
            searchable = searchable.replace(section_text.lower(), " ")
    return searchable


def _extract_phase_headings(plan: str) -> list[int]:
    return sorted(
        {
            int(match)
            for match in re.findall(r"^#{2,6}\s+Phase\s+(\d+)\b", plan, re.IGNORECASE | re.MULTILINE)
        }
    )


def _extract_phase_precondition_blocks(frontmatter: dict[str, str]) -> list[int]:
    blocked: list[int] = []
    for key in frontmatter:
        match = re.fullmatch(r"phase(\d+)_preconditions", key)
        if not match:
            continue
        count = _parse_int_frontmatter(frontmatter, key) or 0
        if count > 0:
            blocked.append(int(match.group(1)))
    return blocked


def _extract_deferred_blocker_phases(plan: str) -> list[int]:
    match = re.search(r"^##\s+Deferred Blockers.*?(?=^##\s|\Z)", plan, re.IGNORECASE | re.MULTILINE | re.DOTALL)
    if not match:
        return []

    headers, rows = extract_markdown_table(match.group(0))
    if not headers or "Phase" not in headers:
        return []

    blocked: list[int] = []
    for row in rows:
        phase_cell = row.get("Phase", "")
        phase_match = re.search(r"\bPhase\s+(\d+)\b|\b(\d+)\b", phase_cell, re.IGNORECASE)
        if not phase_match:
            continue
        phase_value = phase_match.group(1) or phase_match.group(2)
        if phase_value:
            blocked.append(int(phase_value))
    return blocked


def infer_phase_ready_through(plan: str, frontmatter: dict[str, str] | None = None) -> int | None:
    """Infer bounded phase readiness from explicit metadata or deferred blockers.

    The verifier only infers bounded readiness when the plan names a later blocked
    phase explicitly. It does not infer "all phases ready" from headings alone.
    """

    frontmatter = frontmatter or parse_frontmatter(plan)
    explicit = _parse_int_frontmatter(frontmatter, "phase_ready_through")
    if explicit is not None and explicit > 0:
        return explicit

    blocked_phases = sorted(
        set(
            [
                *_extract_phase_precondition_blocks(frontmatter),
                *_extract_deferred_blocker_phases(plan),
            ]
        )
    )
    if not blocked_phases:
        return None

    earliest_blocked = blocked_phases[0]
    if earliest_blocked <= 1:
        return None

    phase_headings = _extract_phase_headings(plan)
    inferred = earliest_blocked - 1
    if phase_headings:
        inferred = min(inferred, max(phase_headings))
    return inferred if inferred > 0 else None


def _is_contract_sensitive(plan: str, frontmatter: dict[str, str] | None = None) -> bool:
    frontmatter = frontmatter or parse_frontmatter(plan)
    headers, rows = find_contract_boundary_rows(plan)
    if headers or rows:
        return True

    contract_sensitive = str(frontmatter.get("contract_sensitive", "")).strip().lower()
    if contract_sensitive in {"yes", "true", "1"}:
        return True
    if contract_sensitive in {"no", "false", "0"}:
        return False

    authority_section = extract_section_content(plan, "contract_authority_reference")
    if authority_section:
        if _has_negative_declaration(authority_section):
            return False
        return True

    boundary_section = extract_section_content(plan, "contract_boundary_matrix")
    if boundary_section and _has_negative_declaration(boundary_section):
        return False
    return False


def check_contract_sensitivity_contradictions(plan: str) -> list[dict[str, Any]]:
    """Fail when a plan declares itself non-contract-sensitive but still provides real boundary rows."""
    findings = []
    headers, rows = find_contract_boundary_rows(plan)
    if not headers and not rows:
        return findings

    frontmatter = parse_frontmatter(plan)
    contract_sensitive = str(frontmatter.get("contract_sensitive", "")).strip().lower()
    authority_section = extract_section_content(plan, "contract_authority_reference")
    explicitly_negative = contract_sensitive in {"no", "false", "0"} or (
        authority_section and _has_negative_declaration(authority_section)
    )
    if explicitly_negative:
        findings.append(
            {
                "id": "CONTRACT-DECL-001",
                "category": "schema_consistency",
                "priority": "HIGH",
                "title": "Plan declares itself non-contract-sensitive but includes boundary rows",
                "description": (
                    "A real Contract Boundary Matrix table is present, so the plan must be treated "
                    "as contract-sensitive. Remove the table or update the declaration."
                ),
            }
        )
    return findings


def extract_requirements(plan: str) -> list[dict[str, str]]:
    """Extract requirements from Goal section."""
    section = extract_section_content(plan, "Goal")
    if not section:
        return []

    requirements = []
    pattern = r"(?:^\s*\d+\.\s*|^\s*-\s*)(.+?)(?=(?:^\s*\d+\.\s*)|(?:^\s*-\s*)|\Z)"
    matches = re.findall(pattern, section, re.MULTILINE | re.DOTALL)

    for i, match in enumerate(matches, 1):
        text = match.strip()
        if text and len(text) > 10:
            requirements.append({"id": f"REQ-{i:03d}", "text": text[:200]})

    if requirements:
        return requirements

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", section) if p.strip()]
    for paragraph in paragraphs:
        if paragraph.startswith("#"):
            continue
        normalized = " ".join(line.strip() for line in paragraph.splitlines())
        if len(normalized) > 20:
            requirements.append({"id": "REQ-001", "text": normalized[:200]})
            break
    return requirements


def _strip_code_fences(text: str) -> str:
    """Remove triple-backtick code fences so ** inside them doesn't confuse block boundaries."""
    lines = text.splitlines()
    result: list[str] = []
    in_fence = False
    for line in lines:
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            result.append(line)
    return "\n".join(result)


def _has_non_placeholder_acceptance_text(text: str) -> bool:
    normalized = text.strip().strip("-").strip()
    if not normalized:
        return False
    return not any(
        re.fullmatch(pattern, normalized, re.IGNORECASE)
        for pattern in ACCEPTANCE_PLACEHOLDER_PATTERNS
    )


def _extract_acceptance_body(task_block: str) -> str:
    lines = task_block.splitlines()
    for idx, line in enumerate(lines):
        if re.search(r"\*\*Acceptance(?: Criteria)?(?::)?\*\*:?", line, re.IGNORECASE):
            inline = re.sub(
                r".*?\*\*Acceptance(?: Criteria)?(?::)?\*\*:?",
                "",
                line,
                flags=re.IGNORECASE,
            ).strip()
            collected: list[str] = []
            if inline:
                collected.append(inline)
            for follow in lines[idx + 1:]:
                if re.match(r"^\*\*(?:TASK|CHANGE)-", follow):
                    break
                if re.match(r"^##\s+", follow):
                    break
                if follow.strip().startswith("**") and not re.search(r"\*\*File\*\*", follow, re.IGNORECASE):
                    break
                if follow.strip():
                    collected.append(follow.strip())
            return "\n".join(collected)

        bullet_match = re.match(r"^(\s*)-\s+Acceptance(?: Criteria)?:\s*(.*)$", line, re.IGNORECASE)
        if bullet_match:
            indent, inline = bullet_match.groups()
            header_indent = len(indent)
            collected: list[str] = [inline.strip()] if inline.strip() else []
            for follow in lines[idx + 1:]:
                if not follow.strip():
                    continue
                current_indent = len(follow) - len(follow.lstrip(" "))
                if current_indent <= header_indent and re.match(r"^\s*-\s+", follow):
                    break
                if current_indent <= header_indent and re.match(r"^##\s+", follow):
                    break
                if current_indent <= header_indent and re.match(r"^\*\*(?:TASK|CHANGE)-", follow):
                    break
                collected.append(follow.strip())
            return "\n".join(collected)
    return ""


def _keyword_set(text: str) -> set[str]:
    normalized = text.replace("_", " ").replace("-", " ")
    tokens = re.findall(r"\b[a-zA-Z]{4,}\b", normalized.lower())
    stems: set[str] = set()
    for token in tokens:
        stem = token
        if stem.endswith("ing") and len(stem) > 6:
            stem = stem[:-3]
        elif stem.endswith("ed") and len(stem) > 5:
            stem = stem[:-2]
        elif stem.endswith("es") and len(stem) > 5:
            stem = stem[:-2]
        elif stem.endswith("s") and len(stem) > 4:
            stem = stem[:-1]
        stems.add(stem)
    return stems


def extract_tasks(plan: str) -> list[dict[str, Any]]:
    """Extract changes/tasks from Implementation Changes section."""
    section = extract_section_content(plan, "Implementation Changes")
    if not section:
        return []

    tasks = []
    section_stripped = _strip_code_fences(section)
    header_pattern = re.compile(
        r"^(?:\*\*(?:TASK|CHANGE)-(\d+)[:\*\s]+([^\n]+)|#{1,6}\s+(?:TASK|CHANGE)-(\d+)[:\s]+([^\n]+)|(?:TASK|CHANGE)-(\d+)[:\s]+([^\n]+))",
        re.MULTILINE,
    )
    matches = list(header_pattern.finditer(section_stripped))

    for idx, match in enumerate(matches):
        groups = match.groups()
        task_num = groups[0] or groups[2] or groups[4]
        title = groups[1] or groups[3] or groups[5]
        task_id = f"TASK-{task_num}"
        title_text = title.strip()
        if not title_text:
            continue

        next_header_start = matches[idx + 1].start() if idx + 1 < len(matches) else len(section_stripped)
        task_block = section_stripped[match.start():next_header_start]

        # Acceptance criteria must be explicitly labeled; mentioning the word
        # "acceptance" in the task title does not count.
        has_acceptance_header = bool(
            re.search(
                r"\*\*Acceptance(?: Criteria)?(?::)?\*\*:?",
                task_block,
                re.IGNORECASE,
            )
            or re.search(r"^\s*-\s+Acceptance(?: Criteria)?:", task_block, re.IGNORECASE | re.MULTILINE)
        )
        acceptance_body = _extract_acceptance_body(task_block)
        acceptance_lines = [line for line in acceptance_body.splitlines() if line.strip()]
        has_acceptance_content = any(
            _has_non_placeholder_acceptance_text(line)
            for line in acceptance_lines
        )
        has_acceptance = has_acceptance_header and has_acceptance_content

        tasks.append(
            {"id": task_id, "title": title_text[:100], "has_acceptance_criteria": has_acceptance}
        )
    return tasks


def check_status_header(plan: str) -> list[dict[str, Any]]:
    """Check that status header is present and valid."""
    findings = []
    frontmatter = parse_frontmatter(plan)
    valid_statuses = {"draft", "in-review", "implementation-ready"}

    if not frontmatter:
        findings.append(
            {
                "id": "STATUS-001",
                "category": "status_header",
                "priority": "HIGH",
                "title": "Missing status frontmatter",
                "description": (
                    "Plan must begin with frontmatter containing status, source, and unresolved_blockers"
                ),
            }
        )
        return findings

    status = frontmatter.get("status")
    if status not in valid_statuses:
        findings.append(
            {
                "id": "STATUS-002",
                "category": "status_header",
                "priority": "HIGH",
                "title": "Missing or invalid status value",
                "description": (
                    "Frontmatter status must be one of: draft, in-review, implementation-ready"
                ),
            }
        )

    if "source" not in frontmatter:
        findings.append(
            {
                "id": "STATUS-003",
                "category": "status_header",
                "priority": "HIGH",
                "title": "Missing source metadata",
                "description": "Frontmatter must include source: <path or null>",
            }
        )

    unresolved_value = frontmatter.get("unresolved_blockers")
    if unresolved_value is None or not re.fullmatch(r"\d+", unresolved_value):
        findings.append(
            {
                "id": "STATUS-004",
                "category": "status_header",
                "priority": "HIGH",
                "title": "Missing or invalid unresolved_blockers metadata",
                "description": "Frontmatter must include unresolved_blockers: <non-negative integer>",
            }
        )

    phase_ready_value = frontmatter.get("phase_ready_through")
    if phase_ready_value is not None and not re.fullmatch(
        r"\d+", phase_ready_value.strip().strip('"').strip("'")
    ):
        findings.append(
            {
                "id": "STATUS-005",
                "category": "status_header",
                "priority": "HIGH",
                "title": "Invalid phase_ready_through metadata",
                "description": "phase_ready_through must be a positive integer when present.",
            }
        )

    return findings


def check_placeholders(plan: str) -> list[dict[str, Any]]:
    """FAIL if any placeholder pattern is found in the plan."""
    findings = []
    for pattern in PLACEHOLDER_PATTERNS:
        matches = re.findall(pattern, plan, re.IGNORECASE)
        if matches:
            # Deduplicate by pattern
            findings.append(
                {
                    "id": f"PLACEHOLDER-{len(findings) + 1:03d}",
                    "category": "placeholder",
                    "priority": "HIGH",
                    "title": f"Placeholder residue found: {pattern!r}",
                    "description": f"Pattern {pattern!r} matched {len(matches)} time(s). Replace with concrete content.",
                    "matched_count": len(matches),
                }
            )
    return findings


def check_plan_purity(plan: str) -> list[dict[str, Any]]:
    """FAIL if plan contains raw findings tables or verification dumps."""
    findings = []
    for pattern in PLAN_PURITY_VIOLATIONS:
        if re.search(pattern, plan, re.IGNORECASE | re.MULTILINE):
            findings.append(
                {
                    "id": f"PURITY-{len(findings) + 1:03d}",
                    "category": "plan_purity",
                    "priority": "HIGH",
                    "title": "Raw findings or verification output merged into plan",
                    "description": f"Pattern {pattern!r} suggests raw review output is in the plan artifact. Findings must live in separate files.",
                }
            )
    return findings


def check_section_completeness(plan: str) -> list[dict[str, Any]]:
    """Check that all required sections are present."""
    findings = []
    for section in REQUIRED_SECTIONS:
        if not extract_section_content(plan, section):
            findings.append(
                {
                    "id": f"SECTION-{len(findings) + 1:03d}",
                    "category": "structure",
                    "priority": "HIGH",
                    "title": f"Missing section: {section}",
                    "description": f"Required section '{section}' not found in plan",
                }
            )

    return findings


def check_ambiguous_contracts(plan: str) -> list[dict[str, Any]]:
    """Fail stateful plans that leave core mechanics as competing alternatives."""
    findings = []
    if not is_stateful_plan(plan):
        return findings

    lowered = _strip_negative_declaration_sections(plan)
    for contract_name, patterns in AMBIGUOUS_CONTRACT_PATTERNS:
        for pattern in patterns:
            match = re.search(pattern, lowered, re.IGNORECASE | re.DOTALL)
            if match:
                # Skip if match is in SQL command context (e.g., "INSERT OR IGNORE")
                # Only skip for specific SQL COMMAND OR patterns, not incidental SQL keywords
                matched_text = match.group(0).lower()
                if re.search(r"\b(insert|update|delete|replace|abort|rollback)\s+or\b", matched_text):
                    continue
                findings.append(
                    {
                        "id": f"AMBIGUITY-{len(findings) + 1:03d}",
                        "category": "contract_ambiguity",
                        "priority": "HIGH",
                        "title": f"Ambiguous {contract_name} contract",
                        "description": (
                            f"Stateful plans must choose one mandatory {contract_name} rule. "
                            "Mutually exclusive alternatives remain in the plan."
                        ),
                    }
                )
                break  # One finding per contract category
    return findings


def check_state_model_completeness(plan: str) -> list[dict[str, Any]]:
    """Require explicit state-model contracts for stateful/history/provider plans."""
    findings = []
    if not is_stateful_plan(plan):
        return findings

    lowered = plan.lower()

    # Contract-domain identity models: if present, the plan is using domain-specific
    # identity keys (transcript_path, finding_id, task_id, skill_name+step+terminal_id)
    # that are equally valid for contract-sensitive plans even if they don't match the
    # generic provider/ingest terminology (provider_id, source_id, turn_id).
    has_contract_identity_model = any(
        term in lowered
        for term in [
            "transcript_path",
            "finding_id",
            "task_id",
            "skill_name",
        ]
    ) and (
        "terminal_id" in lowered
        or "snapshot_id" in lowered
    )

    required_contracts = {
        "identity model": [
            ["provider_id", "source_id", "session_id", "terminal_id", "turn_id"],
        ],
        "ordering contract": [
            ["ordering contract"],
            ["watermark ordering"],
            ["ordering", "watermark"],
            ["monotonic", "ordering"],
        ],
        "dedupe contract": [
            ["dedupe contract"],
            ["dedupe key"],
            ["dedupe"],
            ["dedup"],
        ],
        "freshness/invalidation contract": [
            ["invalidation contract"],
            ["freshness contract"],
            ["invalidation", "replay"],
            ["stale data", "invalidation"],
            ["stale-data", "invalidation"],
        ],
        "event source of truth": [
            ["event source of truth"],
            ["source of truth"],
            ["authoritative event source"],
        ],
    }

    missing = []
    for contract_name, keyword_groups in required_contracts.items():
        # Skip generic provider/ingest identity model check if the plan uses contract-domain
        # identity keys (transcript_path, finding_id, task_id, skill_name) that are equally
        # valid for contract-sensitive plans.
        if contract_name == "identity model" and has_contract_identity_model:
            continue
        if not any(all(keyword in lowered for keyword in group) for group in keyword_groups):
            missing.append(contract_name)

    has_isolation_boundary = (
        "terminal-private" in lowered
        or "workspace-shared" in lowered
        or "isolation boundary" in lowered
        or "provider_instance_id" in lowered
    )
    if not has_isolation_boundary:
        missing.append("isolation boundary")

    if missing:
        findings.append(
            {
                "id": "STATE-001",
                "category": "state_model",
                "priority": "HIGH",
                "title": "Missing required state-model contracts",
                "description": (
                    "Stateful/history/provider plans must explicitly define these contracts: "
                    + ", ".join(missing)
                ),
            }
        )
    return findings


def check_stateless_contradictions(plan: str) -> list[dict[str, Any]]:
    """Fail when a plan declares itself stateless but still encodes stateful semantics."""
    findings = []
    state_model_section = extract_section_content(plan, "state_model_contracts")
    if not state_model_section:
        return findings

    lowered_section = state_model_section.lower()
    if not _has_negative_declaration(state_model_section):
        return findings

    meaningful_section_text = "\n".join(
        line.lower()
        for line in state_model_section.splitlines()
        if "not applicable" not in line.lower()
    )
    searchable_text = plan.lower().replace(lowered_section, " ") + "\n" + meaningful_section_text

    contradiction_terms: list[str] = []
    for pattern in STATEFUL_CONTRADICTION_PATTERNS:
        term_label = pattern.strip(r"\b").replace("\\", "")
        for match in re.finditer(pattern, searchable_text, re.IGNORECASE):
            prefix = searchable_text[max(0, match.start() - 24):match.start()]
            if re.search(r"\b(no|not|without)\s+$", prefix, re.IGNORECASE):
                continue
            line_start = searchable_text.rfind("\n", 0, match.start()) + 1
            line_end = searchable_text.find("\n", match.end())
            if line_end == -1:
                line_end = len(searchable_text)
            line_text = searchable_text[line_start:line_end]
            if re.search(
                rf"\b(no|not|without)\b.{{0,30}}{re.escape(term_label)}",
                line_text,
                re.IGNORECASE,
            ):
                continue
            contradiction_terms.append(term_label)
            break
    contradiction_terms = sorted(set(contradiction_terms))
    if contradiction_terms:
        findings.append(
            {
                "id": "STATE-004",
                "category": "state_model",
                "priority": "HIGH",
                "title": "Plan declares itself stateless but still encodes stateful semantics",
                "description": (
                    "The plan says it is stateless, but these stateful signals remain present: "
                    + ", ".join(contradiction_terms)
                ),
            }
        )
    return findings


def check_unresolved_core_decisions(plan: str) -> list[dict[str, Any]]:
    """Fail stateful plans whose Open Questions still contain implementation-shaping decisions."""
    findings = []
    if not is_stateful_plan(plan):
        return findings

    open_questions = extract_section_content(plan, "Open Questions")
    if not open_questions:
        return findings

    lowered = open_questions.lower()
    blockers = [
        keyword
        for keyword in OPEN_QUESTION_BLOCKERS
        if re.search(rf"\b{keyword}\b", lowered, re.IGNORECASE)
    ]
    if blockers:
        findings.append(
            {
                "id": "STATE-002",
                "category": "open_questions",
                "priority": "HIGH",
                "title": "Open Questions contains unresolved core state-model decisions",
                "description": (
                    "Implementation-shaping questions remain open for: "
                    + ", ".join(sorted(set(blockers)))
                ),
            }
        )
    return findings


def check_boundary_overload(plan: str) -> list[dict[str, Any]]:
    """Fail when terminal_id is overloaded as a non-terminal identity."""
    findings = []
    if not is_stateful_plan(plan):
        return findings

    lowered = plan.lower()
    overload_patterns = [
        r"terminal_id.{0,120}(?:derived from|synthesized from|derived via).{0,120}(?:workspace|session|conversation|provider)",
        r"synthetic terminal_id",
        r"providers? that do not expose a real terminal",
    ]
    if (
        "terminal_id" in lowered
        and any(
            re.search(pattern, lowered, re.IGNORECASE | re.DOTALL) for pattern in overload_patterns
        )
        and "provider_instance_id" not in lowered
    ):
        findings.append(
            {
                "id": "STATE-003",
                "category": "identity_boundary",
                "priority": "HIGH",
                "title": "terminal_id is overloaded as a synthetic provider/session boundary",
                "description": (
                    "Use a separate provider_instance_id or equivalent field when no real terminal "
                    "exists. terminal_id cannot be the generic fallback identity."
                ),
            }
        )
    return findings


def check_claim_schema_consistency(plan: str) -> list[dict[str, Any]]:
    """Catch prose/schema mismatches for stateful plan mechanics."""
    findings = []
    if not is_stateful_plan(plan):
        return findings

    lowered = plan.lower()
    schema_mentions_native_id_key = bool(
        re.search(
            r"(?:primary key|unique(?:\s+key|\s+constraint)?|schema).{0,160}"
            r"provider_id.{0,80}source_id.{0,80}native_event_id.{0,80}content_hash",
            lowered,
            re.IGNORECASE | re.DOTALL,
        )
    )
    prose_claims_content_hash_dedupe = bool(
        re.search(
            r"(?:new|different).{0,40}native_event_id.{0,140}(?:dedupe|dedup|deduplicat).{0,80}content_hash",
            lowered,
            re.IGNORECASE | re.DOTALL,
        )
        or re.search(
            r"content_hash.{0,140}(?:dedupe|dedup|deduplicat).{0,100}(?:new|different).{0,40}native_event_id",
            lowered,
            re.IGNORECASE | re.DOTALL,
        )
    )
    if schema_mentions_native_id_key and prose_claims_content_hash_dedupe:
        findings.append(
            {
                "id": "STATE-004",
                "category": "schema_consistency",
                "priority": "HIGH",
                "title": "Dedupe schema does not match stated content-hash behavior",
                "description": (
                    "The plan claims content-hash dedupe across changing native_event_id values, "
                    "but the described key shape still treats native_event_id as part of identity."
                ),
            }
        )
    return findings


def check_contract_test_coherence(plan: str) -> list[dict[str, Any]]:
    """Fail when the test matrix asserts behavior that contradicts a named contract."""
    findings = []
    if not is_stateful_plan(plan):
        return findings

    design = extract_section_content(plan, "Design Decisions and Invariants").lower()
    tests = extract_section_content(plan, "Test Matrix").lower()
    if not design or not tests:
        return findings

    dedupe_contract_collapses_bucket_duplicates = bool(
        "bucket_seconds = 10" in design
        and "assumed duplicates" in design
        and "only the first is retained" in design
    )
    dedupe_test_retains_bucket_duplicates = bool(
        "same 10s bucket" in tests and "both retained" in tests
    )
    if dedupe_contract_collapses_bucket_duplicates and dedupe_test_retains_bucket_duplicates:
        findings.append(
            {
                "id": "STATE-005",
                "category": "contract_test_coherence",
                "priority": "HIGH",
                "title": "Test matrix contradicts dedupe fallback contract",
                "description": (
                    "The dedupe contract says same-bucket events without a stable ID collapse to "
                    "one retained row, but the test matrix expects both events retained."
                ),
            }
        )

    return findings


def check_open_question_blockers(plan: str) -> list[dict[str, Any]]:
    """Fail plans whose Open Questions still contain explicit blocker markers."""
    findings = []
    open_questions = extract_section_content(plan, "Open Questions")
    if not open_questions:
        return findings

    blocker_lines = []
    for line in open_questions.splitlines():
        lowered = line.lower()
        if "blocker" in lowered or "**blocker" in lowered:
            blocker_lines.append(line.strip())

    if blocker_lines:
        findings.append(
            {
                "id": "OPEN-QUESTION-002",
                "category": "open_questions",
                "priority": "HIGH",
                "title": "Open Questions contains explicit blocker items",
                "description": (
                    "Open Questions still contains blocker-marked items. Resolve, reclassify, "
                    "or defer them through recognized workflow state before claiming readiness."
                ),
                "examples": blocker_lines[:3],
            }
        )

    return findings


def check_contract_boundary_matrix(plan: str) -> list[dict[str, Any]]:
    """Validate matrix shape and per-row requirements for contract-sensitive plans."""
    findings = []
    frontmatter = parse_frontmatter(plan)
    if not _is_contract_sensitive(plan, frontmatter):
        return findings

    headers, rows = find_contract_boundary_rows(plan)
    if not headers:
        findings.append(
            {
                "id": "CONTRACT-MATRIX-001",
                "category": "schema_consistency",
                "priority": "HIGH",
                "title": "Missing contract boundary matrix table",
                "description": (
                    "Contract-sensitive plans must include a markdown Contract Boundary Matrix "
                    "with the required per-row contract fields."
                ),
            }
        )
        return findings

    missing_columns = [field for field in REQUIRED_PLAN_MATRIX_FIELDS if field not in headers]
    if missing_columns:
        findings.append(
            {
                "id": "CONTRACT-MATRIX-002",
                "category": "schema_consistency",
                "priority": "HIGH",
                "title": "Contract boundary matrix is missing required columns",
                "description": "Missing required columns: " + ", ".join(missing_columns),
            }
        )
        return findings

    claimed_status = frontmatter.get("status", "draft")
    for row in rows:
        boundary = row.get("Boundary", "").strip() or "UNKNOWN"
        packet_ref = row.get("Contract authority packet", "").strip()
        test_binding = row.get("Test Binding", "").strip()
        packet_alignment = row.get("Packet Alignment", "").strip()

        if not packet_ref:
            findings.append(
                {
                    "id": f"CONTRACT-MATRIX-{boundary}-PACKET",
                    "category": "schema_consistency",
                    "priority": "HIGH",
                    "title": f"Boundary row '{boundary}' is missing a per-row Contract authority packet reference",
                    "description": (
                        "Each boundary row must name the packet id/version/path or boundary_id "
                        "it derives from."
                    ),
                }
            )

        if not test_binding:
            findings.append(
                {
                    "id": f"CONTRACT-MATRIX-{boundary}-TEST",
                    "category": "contract_test_coherence",
                    "priority": "HIGH",
                    "title": f"Boundary row '{boundary}' is missing Test binding",
                    "description": "Each boundary row must name the test/trace that proves the contract.",
                }
            )
        elif claimed_status == "implementation-ready" and test_binding.lower() in PLACEHOLDER_BINDINGS:
            findings.append(
                {
                    "id": f"CONTRACT-MATRIX-{boundary}-TEST-PLACEHOLDER",
                    "category": "contract_test_coherence",
                    "priority": "HIGH",
                    "title": f"Boundary row '{boundary}' uses placeholder Test binding",
                    "description": (
                        "Implementation-ready plans cannot keep placeholder test bindings. "
                        "Name the proving test or keep the plan in-review."
                    ),
                }
            )

        if packet_alignment.lower().startswith("exact match") and not packet_ref:
            findings.append(
                {
                    "id": f"CONTRACT-MATRIX-{boundary}-ALIGNMENT",
                    "category": "schema_consistency",
                    "priority": "HIGH",
                    "title": f"Boundary row '{boundary}' claims exact packet alignment without a row-level packet reference",
                    "description": "Exact alignment claims must name the referenced packet boundary explicitly.",
                }
            )

    return findings


def check_planning_contract_authority_drift(plan: str) -> list[dict[str, Any]]:
    """Catch stale plan-artifact semantics copied from older CAP/ADR revisions."""
    findings = []
    if not _is_contract_sensitive(plan):
        return findings

    headers, rows = find_contract_boundary_rows(plan)
    if not headers or "Boundary" not in headers or "Failure behavior" not in headers:
        return findings

    for row in rows:
        if row.get("Boundary", "").strip() != "plan-artifact":
            continue

        failure_behavior = row.get("Failure behavior", "")
        packet_alignment = row.get("Packet alignment", "")
        if "/planning" not in failure_behavior.lower() or "blocking" not in failure_behavior.lower():
            findings.append(
                {
                    "id": "AUTHORITY-DRIFT-001",
                    "category": "authority_drift",
                    "priority": "HIGH",
                    "title": "plan-artifact boundary semantics drift from the active /planning contract",
                    "description": (
                        "The plan-artifact row must reflect the active planning contract, which "
                        "treats packet consumption and contradictions as blocking before "
                        "implementation-ready."
                    ),
                    "expected_failure_behavior": ACTIVE_PLAN_ARTIFACT_FAILURE_BEHAVIOR,
                    "actual_failure_behavior": failure_behavior,
                    "packet_alignment": packet_alignment,
                }
            )
        break

    return findings


def check_mechanism_triggerability(plan: str) -> list[dict[str, Any]]:
    """Fail when a stateful mechanism cannot trigger under the plan's stated invariants."""
    findings = []
    if not is_stateful_plan(plan):
        return findings

    design = extract_section_content(plan, "Design Decisions and Invariants").lower()
    tests = extract_section_content(plan, "Test Matrix").lower()
    if not design:
        return findings

    stale_check_uses_occurred_vs_cached = "occurred_at > cached_at" in design
    cached_at_equals_occurred_at = bool(
        re.search(
            r"cached_at.{0,40}set to.{0,40}occurred_at.{0,40}ingest time",
            design,
            re.IGNORECASE | re.DOTALL,
        )
    )
    archive_marked_immutable = (
        "append-only and immutable once written" in design
        or "archive files are append-only and immutable once written" in design
    )
    stale_check_uses_archive_mtime = "raw_payload_path" in design and "mtime" in design
    test_mutates_source_file = "mutate source file" in tests

    if (
        stale_check_uses_occurred_vs_cached
        and cached_at_equals_occurred_at
        and archive_marked_immutable
        and stale_check_uses_archive_mtime
    ):
        findings.append(
            {
                "id": "STATE-006",
                "category": "mechanism_triggerability",
                "priority": "HIGH",
                "title": "Freshness / invalidation trigger cannot fire under stated invariants",
                "description": (
                    "The plan sets cached_at = occurred_at at ingest time and also treats archive "
                    "files as immutable, so neither documented stale trigger is reachable."
                    + (
                        " The test matrix mutates the source file rather than the watched archive "
                        "artifact."
                        if test_mutates_source_file
                        else ""
                    )
                ),
            }
        )

    return findings


def check_solo_dev_violations(plan: str) -> list[dict[str, Any]]:
    """Check for team coordination patterns that violate solo-dev constraints."""
    findings = []
    negation_pattern = r"(?:no|without|avoid|not|lacking|minus|excluding)\s+"

    for pattern in SOLO_DEV_VIOLATIONS:
        matches = re.findall(pattern, plan, re.IGNORECASE)
        for match in matches:
            match_pos = plan.lower().find(match.lower())
            if match_pos > 0:
                context_before = plan[max(0, match_pos - 20) : match_pos].lower()
                if re.search(negation_pattern, context_before):
                    continue
            findings.append(
                {
                    "id": f"SOLO-{len(findings) + 1:03d}",
                    "category": "solo_dev_constraint",
                    "priority": "HIGH",
                    "title": f"Solo-dev violation: {match}",
                    "description": f"Pattern '{match}' indicates team coordination, not allowed in solo-dev",
                }
            )
    return findings


def check_rtm_coverage(
    requirements: list[dict[str, str]], tasks: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Check RTM coverage."""
    findings = []

    if not tasks:
        findings.append(
            {
                "id": "RTM-005",
                "category": "traceability",
                "priority": "HIGH",
                "title": "No tasks detected",
                "description": "Implementation Plan contains no tasks.",
            }
        )
        return findings

    if not requirements:
        findings.append(
            {
                "id": "RTM-000",
                "category": "traceability",
                "priority": "MEDIUM",
                "title": "No requirements detected",
                "description": "Could not detect requirements in Goal section",
            }
        )

    tasks_without_acceptance = [t for t in tasks if not t["has_acceptance_criteria"]]
    if tasks_without_acceptance:
        findings.append(
            {
                "id": "RTM-003",
                "category": "traceability",
                "priority": "HIGH",
                "title": f"Missing acceptance criteria: {len(tasks_without_acceptance)} task(s)",
                "description": "Tasks without acceptance criteria:\n"
                + "\n".join(f"  - {t['id']}: {t['title'][:100]}" for t in tasks_without_acceptance),
            }
        )

    if requirements:
        orphan_requirements = []
        for req in requirements:
            req_keywords = _keyword_set(req["text"])
            mapped = False
            for task in tasks:
                task_keywords = _keyword_set(task["title"])
                if req_keywords & task_keywords:
                    mapped = True
                    break
            if not mapped:
                orphan_requirements.append(req)

        if orphan_requirements:
            findings.append(
                {
                    "id": "RTM-001",
                    "category": "traceability",
                    "priority": "HIGH",
                    "title": f"Orphan requirements: {len(orphan_requirements)} not mapped to tasks",
                    "description": "Requirements without corresponding tasks:\n"
                    + "\n".join(f"  - {r['id']}: {r['text'][:100]}" for r in orphan_requirements),
                }
            )

    return findings


def check_status_readiness(plan: str, findings: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """FAIL if plan claims implementation-ready but has unresolved blocker/high findings."""
    result_findings = []
    frontmatter = parse_frontmatter(plan)

    claimed_status = frontmatter.get("status", "draft")
    unresolved_blockers = int(frontmatter.get("unresolved_blockers", "0") or "0")

    if claimed_status == "implementation-ready":
        high_priority = [f for f in findings if f.get("priority") == "HIGH"]
        if high_priority:
            result_findings.append(
                {
                    "id": "CONTRADICTION-001",
                    "category": "contradiction",
                    "priority": "HIGH",
                    "title": "Contradiction: plan claims implementation-ready but has unresolved HIGH findings",
                    "description": f"Status is 'implementation-ready' but {len(high_priority)} HIGH priority issue(s) remain. "
                    f"Fix all HIGH findings or defer them with rationale before marking implementation-ready.",
                    "blocking_findings": [f["id"] for f in high_priority],
                }
            )

        if unresolved_blockers != 0:
            result_findings.append(
                {
                    "id": "CONTRADICTION-002",
                    "category": "contradiction",
                    "priority": "HIGH",
                    "title": "Contradiction: implementation-ready plan reports unresolved blockers",
                    "description": (
                        "Frontmatter unresolved_blockers must be 0 before a plan can be marked "
                        "implementation-ready."
                    ),
                }
            )

        phase_preconditions = [
            (key, _parse_int_frontmatter(frontmatter, key) or 0)
            for key in frontmatter
            if re.fullmatch(r"phase\d+_preconditions", key)
        ]
        active_phase_preconditions = [item for item in phase_preconditions if item[1] > 0]
        if active_phase_preconditions and "phase_ready_through" not in frontmatter:
            formatted = ", ".join(f"{key}={value}" for key, value in active_phase_preconditions)
            result_findings.append(
                {
                    "id": "CONTRADICTION-003",
                    "category": "contradiction",
                    "priority": "HIGH",
                    "title": "implementation-ready plan uses unrecognized phase-precondition metadata",
                    "description": (
                        "Phase-specific preconditions are present ("
                        + formatted
                        + "), but no recognized readiness vocabulary such as phase_ready_through "
                          "was declared."
                    ),
                }
            )

    return result_findings


def load_review_findings(findings_path: Path) -> list[dict[str, Any]]:
    """Load blocker/high findings from flexible review-findings JSON structures."""
    if not findings_path.exists():
        return []

    try:
        payload = json.loads(findings_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    def flatten(value: Any) -> list[dict[str, Any]]:
        if isinstance(value, list):
            collected = []
            for item in value:
                collected.extend(flatten(item))
            return collected
        if isinstance(value, dict):
            if "id" in value and ("severity" in value or "priority" in value):
                return [value]
            collected = []
            for nested in value.values():
                collected.extend(flatten(nested))
            return collected
        return []

    return flatten(payload)


def parse_dispositions(summary_path: Path) -> dict[str, str]:
    """Parse finding dispositions from a markdown summary table.

    Handles 5-column format (| Finding | Source | Severity | Disposition | Rationale |)
    used in review summaries, where Disposition may be bold (e.g., **ACCEPTED**).
    Also handles 4-column format (| ID | SEVERITY | disposition | rationale |)
    and 2-column format (| ID | disposition |).
    """
    if not summary_path.exists():
        return {}

    dispositions = {}
    for line in summary_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("| Finding") or line.startswith("|--------"):
            continue

        parts = [p.strip() for p in line.split("|")]
        # parts[0] is empty (leading |), parts[1] = Finding, parts[2] = Source,
        # parts[3] = Severity, parts[4] = Disposition, parts[5] = Rationale
        if len(parts) >= 5:
            finding_field = parts[1]
            disposition_field = parts[4] if len(parts) >= 5 else ""
            # Extract ID from finding field (e.g., "VIOLATION-1: MCP call in Stop hook" -> "VIOLATION-1")
            # IDs may contain hyphens (e.g., "CRITIC-ADVISORY-GHOST", "R1-COUNTER-STATE", "SEC-CKS-LEAK")
            id_match = re.match(r"^([A-Za-z0-9]+(?:-[A-Za-z0-9]+)*)", finding_field)
            if not id_match:
                continue
            finding_id = id_match.group(1)
            # Strip bold markdown from disposition (e.g., "**ACCEPTED**" -> "ACCEPTED")
            disp_clean = re.sub(
                r"^\*\*(.+)\*\*$", r"\1", disposition_field, flags=re.IGNORECASE
            ).lower()
            if disp_clean in ("accepted", "rejected", "deferred"):
                dispositions[finding_id] = disp_clean
                continue

        # Fallback: 4-column or 2-column regex patterns
        # 4-column: | ID | SEVERITY | disposition | rationale |
        match = re.match(
            r"^\|\s*([A-Za-z0-9_-]+)\s*\|\s*(?:BLOCKER|HIGH|MEDIUM|LOW|CRITICAL)\s*\|\s*(accepted|rejected|deferred)\s*\|",
            line,
            re.IGNORECASE,
        )
        if match:
            dispositions[match.group(1)] = match.group(2).lower()
            continue
        # 2-column: | ID | disposition |
        match = re.match(
            r"^\|\s*([A-Za-z0-9_-]+)\s*\|\s*(accepted|rejected|deferred)\s*\|",
            line,
            re.IGNORECASE,
        )
        if match:
            dispositions[match.group(1)] = match.group(2).lower()
    return dispositions


def check_dispositions(plan_path: str | None, plan: str) -> list[dict[str, Any]]:
    """Require review artifacts and blocker/high dispositions before implementation-ready."""
    findings = []
    frontmatter = parse_frontmatter(plan)
    claimed_status = frontmatter.get("status", "draft")
    if claimed_status != "implementation-ready":
        return findings

    if not plan_path:
        findings.append(
            {
                "id": "DISPOSITION-001",
                "category": "disposition",
                "priority": "HIGH",
                "title": "Cannot verify implementation-ready status without plan path",
                "description": (
                    "Implementation-ready verification requires a plan path so sidecar review "
                    "artifacts can be inspected."
                ),
            }
        )
        return findings

    findings_path = Path(plan_path).with_suffix(".review.findings.json")
    summary_path = Path(plan_path).with_suffix(".review.summary.md")

    if not findings_path.exists():
        findings.append(
            {
                "id": "DISPOSITION-002",
                "category": "disposition",
                "priority": "HIGH",
                "title": "Missing review findings artifact",
                "description": (
                    "Implementation-ready plans must have a sibling .review.findings.json artifact."
                ),
            }
        )
        return findings

    if not summary_path.exists():
        findings.append(
            {
                "id": "DISPOSITION-003",
                "category": "disposition",
                "priority": "HIGH",
                "title": "Missing review summary artifact",
                "description": (
                    "Implementation-ready plans must have a sibling .review.summary.md artifact "
                    "with finding dispositions."
                ),
            }
        )
        return findings

    review_findings = load_review_findings(findings_path)
    blocking_ids = []
    for finding in review_findings:
        severity = str(finding.get("severity") or finding.get("priority") or "").upper()
        if severity in {"BLOCKER", "HIGH", "CRITICAL"}:
            finding_id = finding.get("id")
            if finding_id:
                blocking_ids.append(str(finding_id))

    # Use JSON as authoritative disposition source (structured, machine-readable).
    # The summary table may use human-readable titles instead of IDs.
    dispositions = {}
    for f in review_findings:
        disp = f.get("disposition", "").lower().strip()
        if disp in ("accepted", "rejected", "deferred"):
            dispositions[f["id"]] = disp

    missing = [finding_id for finding_id in blocking_ids if finding_id not in dispositions]
    if missing:
        findings.append(
            {
                "id": "DISPOSITION-004",
                "category": "disposition",
                "priority": "HIGH",
                "title": "Missing blocker/high finding dispositions",
                "description": (
                    "Every blocker/high finding must be dispositioned in .review.summary.md. "
                    f"Missing: {', '.join(sorted(missing))}"
                ),
            }
        )

    return findings


def _detect_stale_review_summary(summary_text: str, result: dict[str, Any]) -> str | None:
    lowered = summary_text.lower()
    status = result.get("status")
    claimed_status = result.get("claimed_status")
    high_priority = result.get("summary", {}).get("high_priority", 0)

    if status == "READY" and (
        "blocked by auto_verify" in lowered
        or "auto_verify returns `blocked`" in lowered
        or "auto_verify returns blocked" in lowered
        or "false positives" in lowered
    ):
        return "Summary claims the plan is blocked or false-positive limited, but current verification is READY."

    if status == "BLOCKED" and (
        "ready for implementation" in lowered or "this plan is ready for implementation" in lowered
    ):
        return "Summary claims the plan is ready for implementation, but current verification is BLOCKED."

    if claimed_status != "implementation-ready" and "ready for implementation" in lowered:
        return (
            "Summary claims implementation readiness, but the current frontmatter status is not "
            "implementation-ready."
        )

    if high_priority > 0 and "0 findings" in lowered:
        return "Summary claims zero findings, but current verification reports HIGH findings."

    return None


def _candidate_review_summary_paths(plan_path: str) -> list[Path]:
    plan = Path(plan_path)
    candidates = [plan.with_suffix(".review.summary.md")]

    plans_roots = [plan.parent, Path.home() / ".claude" / "plans", Path("P:/.claude/plans")]
    for plans_dir in plans_roots:
        adversarial_dir = plans_dir / "adversarial"
        if adversarial_dir.exists():
            candidates.extend(adversarial_dir.glob(f"{plan.stem}.review.summary.md"))
            nested_dir = adversarial_dir / plan.stem
            if nested_dir.exists():
                candidates.extend(nested_dir.glob("**/*.review.summary.md"))

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate.resolve()) if candidate.exists() else str(candidate)
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def annotate_stale_review_artifacts(plan_path: str | None, result: dict[str, Any]) -> dict[str, Any]:
    """Mark contradictory review summaries as stale so they stop acting authoritative."""
    if not plan_path:
        return {"stale_review_summary": False, "reason": None, "paths": []}

    stale_paths: list[str] = []
    reasons: list[str] = []
    unreadable: list[str] = []

    for summary_path in _candidate_review_summary_paths(plan_path):
        if not summary_path.exists():
            continue

        try:
            summary_text = summary_path.read_text(encoding="utf-8")
        except OSError:
            unreadable.append(str(summary_path))
            continue

        reason = _detect_stale_review_summary(summary_text, result)
        if not reason:
            continue

        stale_prefix = "> STALE REVIEW ARTIFACT:"
        if stale_prefix not in summary_text:
            verified_at = int(result.get("artifact_freshness", {}).get("verified_at", time.time()))
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(verified_at))
            banner = (
                f"{stale_prefix} auto_verify at {timestamp} returned "
                f"{result.get('status')} ({result.get('summary', {}).get('high_priority', 0)} HIGH findings). "
                f"{reason} Regenerate adversarial review artifacts before treating this summary as authoritative.\n\n"
            )
            try:
                summary_path.write_text(banner + summary_text, encoding="utf-8")
            except OSError:
                unreadable.append(str(summary_path))
                continue

        stale_paths.append(str(summary_path))
        reasons.append(reason)

    return {
        "stale_review_summary": bool(stale_paths),
        "reason": reasons[0] if reasons else ("unreadable" if unreadable else None),
        "paths": stale_paths,
        "unreadable_paths": unreadable,
    }


def validate_adversarial_agents() -> dict[str, Any]:
    """Validate that all required adversarial agents are available."""
    missing = []
    available = []
    # Also check the .claude/agents relative to this module's location
    # (handles cases where cwd differs from project root, e.g. test environments)
    # Walk upward; when we find a directory named "skills", the sibling ../agents
    # is the agents directory (since .claude/skills is the project layout)
    module_dir = Path(__file__).resolve().parent
    claude_agents = None
    for _ in range(6):
        module_dir = module_dir.parent
        if module_dir.name == "skills" and (module_dir.parent / "agents").exists():
            claude_agents = module_dir.parent / "agents"
            break
    # Build list with all candidates
    agents_dirs = [
        Path.cwd() / ".claude" / "agents",
        Path.home() / ".claude" / "agents",
    ]
    # Also check P:\.claude\agents explicitly (P: drive is not home directory on Windows)
    p_drive_claude = Path("P:/") / ".claude" / "agents"
    if p_drive_claude.exists():
        agents_dirs.append(p_drive_claude)
    if claude_agents:
        agents_dirs.append(claude_agents)

    for agent_name in REQUIRED_ADVERSARIAL_AGENTS:
        agent_file = f"{agent_name}.md"
        found = any((agents_dir / agent_file).exists() for agents_dir in agents_dirs)
        if found:
            available.append(agent_name)
        else:
            missing.append(agent_name)

    return {"valid": len(missing) == 0, "missing": missing, "available": available}


def classify_next_action(status: str, findings: list[dict[str, Any]]) -> dict[str, Any]:
    """Choose the next workflow action from verifier results."""
    if status == "READY":
        return {
            "type": "launch_adversarial_review",
            "reason": "Plan passed verification",
            "must_follow": True,
            "authoritative_source": "latest_auto_verify",
        }

    arch_findings = [
        finding
        for finding in findings
        if finding.get("category") in ARCH_REMEDIATION_CATEGORIES
        or finding.get("id") in ARCH_REMEDIATION_IDS
    ]
    if arch_findings:
        blocking_categories = sorted({str(finding.get("category")) for finding in arch_findings})
        return {
            "type": "invoke_arch_then_rewrite_plan",
            "reason": (
                f"Resolve {len(arch_findings)} architecture blocker(s) via /arch, "
                "then rewrite the plan and re-run verification"
            ),
            "must_follow": True,
            "authoritative_source": "latest_auto_verify",
            "recommended_skill": "/arch",
            "arch_blocker_ids": [str(finding.get("id")) for finding in arch_findings],
            "blocking_categories": blocking_categories,
            "ownership": "planning_rewrites_plan",
        }

    high_priority = [finding for finding in findings if finding.get("priority") == "HIGH"]
    return {
        "type": "fix_issues",
        "reason": f"Fix {len(high_priority)} HIGH priority issue(s)",
        "must_follow": True,
        "authoritative_source": "latest_auto_verify",
    }


def verify_plan(plan_path: str | None = None, plan_content: str | None = None) -> dict[str, Any]:
    """Verify plan structure with strict readiness gating.

    Args:
        plan_path: Path to plan file
        plan_content: Plan content string (alternative to path)

    Returns:
        Verification result dict with status, action_items, and next_action.
        next_action.type is one of:
        - launch_adversarial_review
        - invoke_arch_then_rewrite_plan
        - fix_issues
    """
    try:
        if plan_content:
            plan = plan_content
        elif plan_path:
            with open(plan_path, encoding="utf-8") as f:
                plan = f.read()
        else:
            return {
                "status": "BLOCKED",
                "action_items": [
                    {
                        "id": "ERROR-001",
                        "category": "error",
                        "priority": "HIGH",
                        "title": "Invalid arguments",
                        "description": "Either plan_path or plan_content must be provided",
                    }
                ],
                "summary": {"total_findings": 1, "high_priority": 1},
                "next_action": {"type": "fix_issues", "reason": "Invalid arguments"},
            }
    except FileNotFoundError:
        return {
            "status": "BLOCKED",
            "plan_path": plan_path,
            "action_items": [
                {
                    "id": "ERROR-002",
                    "category": "error",
                    "priority": "HIGH",
                    "title": f"Plan file not found: {plan_path}",
                    "description": str(Exception()),
                }
            ],
            "summary": {"total_findings": 1, "high_priority": 1},
            "next_action": {"type": "fix_issues", "reason": f"File not found: {plan_path}"},
        }
    except Exception as e:
        return {
            "status": "BLOCKED",
            "plan_path": plan_path,
            "action_items": [
                {
                    "id": "ERROR-003",
                    "category": "error",
                    "priority": "HIGH",
                    "title": f"Unexpected error: {type(e).__name__}",
                    "description": str(e),
                }
            ],
            "summary": {"total_findings": 1, "high_priority": 1},
            "next_action": {"type": "fix_issues", "reason": f"Error reading plan: {e}"},
        }

    # Run all checks
    all_findings = []

    # 1. Status header
    all_findings.extend(check_status_header(plan))

    # 2. Placeholder detection (blocks READY)
    all_findings.extend(check_placeholders(plan))

    # 3. Plan purity (blocks READY)
    all_findings.extend(check_plan_purity(plan))

    # 4. Section completeness
    all_findings.extend(check_section_completeness(plan))

    # 5. Stateful contract readiness
    all_findings.extend(check_stateless_contradictions(plan))
    all_findings.extend(check_ambiguous_contracts(plan))
    all_findings.extend(check_state_model_completeness(plan))
    all_findings.extend(check_unresolved_core_decisions(plan))
    all_findings.extend(check_open_question_blockers(plan))
    all_findings.extend(check_boundary_overload(plan))
    all_findings.extend(check_claim_schema_consistency(plan))
    all_findings.extend(check_contract_test_coherence(plan))
    all_findings.extend(check_mechanism_triggerability(plan))
    all_findings.extend(check_contract_sensitivity_contradictions(plan))
    all_findings.extend(check_contract_boundary_matrix(plan))
    all_findings.extend(check_planning_contract_authority_drift(plan))

    # 6. Solo-dev violations
    all_findings.extend(check_solo_dev_violations(plan))

    # 7. RTM coverage
    requirements = extract_requirements(plan)
    tasks = extract_tasks(plan)
    all_findings.extend(check_rtm_coverage(requirements, tasks))

    # 8. Review dispositions (before claimed implementation-ready can pass)
    all_findings.extend(check_dispositions(plan_path, plan))

    # 9. Adversarial agent availability
    agent_validation = validate_adversarial_agents()
    if not agent_validation["valid"]:
        all_findings.append(
            {
                "id": "AGENT-001",
                "category": "agent_availability",
                "priority": "HIGH",
                "title": "Missing adversarial agents",
                "description": f"Cannot launch adversarial review. Missing: {', '.join(agent_validation['missing'])}",
            }
        )

    # 10. Contradiction check (after findings so we can check against HIGH findings)
    all_findings.extend(check_status_readiness(plan, all_findings))

    # Determine overall status
    high_priority = [f for f in all_findings if f.get("priority") == "HIGH"]
    status = "BLOCKED" if high_priority else "READY"

    # Extract claimed status for result
    claimed_status = parse_frontmatter(plan).get("status", "draft")

    frontmatter = parse_frontmatter(plan)
    inferred_phase_ready_through = infer_phase_ready_through(plan, frontmatter)

    result = {
        "status": status,
        "claimed_status": claimed_status,
        "plan_path": plan_path,
        "plan_sha256": hashlib.sha256(plan.encode("utf-8")).hexdigest(),
        "readiness": {
            "phase_ready_through": inferred_phase_ready_through,
            "unresolved_blockers": _parse_int_frontmatter(frontmatter, "unresolved_blockers"),
        },
        "action_items": all_findings,
        "agent_validation": agent_validation,
        "summary": {
            "total_findings": len(all_findings),
            "high_priority": len(high_priority),
            "requirements_found": len(requirements),
            "tasks_found": len(tasks),
        },
        "next_action": classify_next_action(status, all_findings),
        "artifact_freshness": {
            "verified_at": int(time.time()),
            "plan_mtime": int(Path(plan_path).stat().st_mtime) if plan_path else None,
            "instruction": (
                "If the plan file or sibling artifacts change after this timestamp, rerun "
                "auto_verify.py and discard the previous blocker model."
            ),
        },
    }

    if plan_path:
        result["artifact_consistency"] = annotate_stale_review_artifacts(plan_path, result)
        result_path = Path(plan_path).with_suffix(".review.result.json")
        with open(result_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

    # GTO skill coverage logging (lazy import to avoid blocking when GTO has import errors)
    try:
        import sys as _sys

        _gto_lib = Path("P:/.claude/skills")
        if str(_gto_lib) not in _sys.path:
            _sys.path.insert(0, str(_gto_lib))
        from gto.lib.skill_coverage_detector import _append_skill_coverage

        _append_skill_coverage(
            target_key="skills/planning",
            skill="/planning",
            terminal_id="cli",
            git_sha=None,
        )
    except Exception:
        pass

    return result


def cleanup_plan_artifacts(
    plans_dir: str | Path | None = None, retention_seconds: int = 604800
) -> dict[str, Any]:
    """Remove stale review artifacts older than retention period (default: 7 days).

    Concurrent-session safe: uses atomic unlink, skips files that can't be removed.

    Args:
        plans_dir: Root plans directory. Defaults to ~/.claude/plans
        retention_seconds: Age threshold in seconds (default 7 days = 604800s)

    Returns:
        Dict with removed count, errors, and list of removed files
    """
    if plans_dir is None:
        plans_dir = Path.home() / ".claude" / "plans"
    else:
        plans_dir = Path(plans_dir)

    if not plans_dir.exists():
        return {"removed": [], "errors": [], "total_removed": 0}

    cutoff = time.time() - retention_seconds
    removed: list[str] = []
    errors: list[str] = []

    # Pattern matches all review artifact types (findings, summary, result)
    # Also matches per-plan subdirectory artifacts
    for pattern in [
        "**/*.review.findings.json",
        "**/*.review.summary.md",
        "**/*.review.result.json",
    ]:
        for artifact_path in plans_dir.glob(pattern):
            try:
                if artifact_path.stat().st_mtime >= cutoff:
                    continue  # Skip files within retention window
                # Atomic unlink — fails fast if file is held open by another process
                artifact_path.unlink()
                removed.append(str(artifact_path))
            except OSError as e:
                errors.append(f"{artifact_path}: {e}")

    return {"removed": removed, "errors": errors, "total_removed": len(removed)}


def main() -> None:
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python auto_verify.py <plan_path>")
        sys.exit(1)

    plan_path = sys.argv[1]
    result = verify_plan(plan_path)
    print(json.dumps(result, indent=2))
    sys.exit(0 if result["status"] == "READY" else 1)


if __name__ == "__main__":
    main()
