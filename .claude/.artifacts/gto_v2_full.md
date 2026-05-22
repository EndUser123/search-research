# GTO_V2 — Full Source Pack

Generated: 2026-05-13 12:12:32
Files: 54

## FILE INDEX
- `__init__.py`
- `__lib/__init__.py`
- `__lib/assertions.py`
- `__lib/branch_awareness.py`
- `__lib/carryover.py`
- `__lib/changelog.py`
- `__lib/clustering.py`
- `__lib/completion_checker.py`
- `__lib/context.py`
- `__lib/context_boundaries.py`
- `__lib/coverage.py`
- `__lib/dedupe.py`
- `__lib/dependency_order.py`
- `__lib/detectors.py`
- `__lib/docs_followup.py`
- `__lib/evidence.py`
- `__lib/execution_contract_test.py`
- `__lib/freshness.py`
- `__lib/hook_health.py`
- `__lib/impact_radius.py`
- `__lib/invocation_tracker.py`
- `__lib/machine_render.py`
- `__lib/merge.py`
- `__lib/normalize.py`
- `__lib/render.py`
- `__lib/resolve.py`
- `__lib/route.py`
- `__lib/session_goal_detector.py`
- `__lib/session_outcome_detector.py`
- `__lib/state.py`
- `__lib/stuckness.py`
- `__lib/targeting.py`
- `__lib/transcript.py`
- `__lib/util.py`
- `__lib/verification_debt.py`
- `__lib/verify.py`
- `__lib/workflow_hygiene.py`
- `agents/__init__.py`
- `agents/action_normalizer.py`
- `agents/domain_analyzer.py`
- `agents/findings_reviewer.py`
- `agents/gap_reviewer.py`
- `agents/prompts.py`
- `agents/session_reviewer.py`
- `hooks/__init__.py`
- `hooks/common.py`
- `hooks/posttooluse.py`
- `hooks/pretooluse.py`
- `hooks/sessionstart.py`
- `hooks/stop.py`
- `models.py`
- `orchestrator.py`
- `settings.py`
- `test_context_boundaries.py`

## SIGNATURES

## __init__.py
  (no top-level functions/classes)


## __lib/__init__.py
  (no top-level functions/classes)


## __lib/assertions.py
  def main([]) -> None


## __lib/branch_awareness.py
  def get_current_branch(['root']) -> str | None
  def adjust_for_branch(['root', 'findings']) -> list[Finding]


## __lib/carryover.py
  def load_carryover(['artifacts_dir']) -> list[Finding]
  def save_carryover(['artifacts_dir', 'findings']) -> None
  def load_carryover_open_only(['artifacts_dir']) -> list[Finding]
  def apply_carryover_enrichment(['findings', 'changed_files']) -> list[Finding]
  def prune_carryover(['artifacts_dir', 'max_resolved']) -> None


## __lib/changelog.py
  def _matches_entry(['path', 'prefix', 'extension']) -> bool
  def classify_change_wave(['file_count', 'commit_count']) -> str
  def _base_skill(['skill']) -> str
  def get_changed_files(['root', 'prev_sha', 'curr_sha']) -> list[str]
  def get_commit_count(['root', 'prev_sha', 'curr_sha']) -> int
  def map_changed_files_to_skills(['changed_files']) -> dict[str, list[tuple[str, str]]]
  def _matches_pattern(['path', 'pattern']) -> bool
  def detect_changelog_findings(['root', 'prev_sha', 'curr_sha', 'terminal_id', 'session_id', 'git_sha']) -> list[Finding]


## __lib/clustering.py
  def _extract_dir(['file_path']) -> str | None
  def cluster_findings(['findings']) -> list[Finding]


## __lib/completion_checker.py
  def _turns_to_dicts(['transcript_path']) -> list[dict[str, str]]
  def _content_keywords(['content']) -> set[str]
  def _has_completion_evidence(['window_turns', 'outcome_keywords']) -> bool
  def check_completions(['transcript_path', 'items', 'window']) -> list[SessionOutcomeItem]


## __lib/context.py
  def get_git_sha(['root']) -> str | None
  def git_dirty(['root']) -> bool


## __lib/context_boundaries.py
  def detect_context_boundaries(['transcript_path']) -> list[WorkContext]
  def context_boundary_findings(['transcript_path', 'terminal_id', 'session_id', 'git_sha']) -> list[Finding]


## __lib/coverage.py
  def compute_coverage(['findings']) -> dict[str, Any]
  def compute_health_score(['findings', 'freshness']) -> dict[str, Any]


## __lib/dedupe.py
  def dedupe_findings(['findings']) -> list[Finding]


## __lib/dependency_order.py
  def _skill_order_rank(['skill']) -> int
  def order_findings(['findings']) -> list[Finding]


## __lib/detectors.py
  def run_basic_detectors(['root', 'terminal_id', 'session_id', 'git_sha']) -> list[Finding]
  def detect_marker_staleness(['root', 'terminal_id', 'session_id', 'git_sha']) -> list[Finding]
  def detect_missing_verification_evidence(['root', 'terminal_id', 'session_id', 'git_sha']) -> list[Finding]


## __lib/docs_followup.py
  def detect_docs_followup(['root', 'findings']) -> list[Finding]


## __lib/evidence.py
  def write_artifact(['artifact_path', 'artifact', 'findings']) -> Path
  def _artifact_to_dict(['artifact']) -> dict


## __lib/execution_contract_test.py
  def test_verify_artifact_with_rns_markers_valid([])
  def test_verify_artifact_missing_rns_d_marker_fails([])
  def test_verify_artifact_missing_rns_z_marker_fails([])
  def test_verify_artifact_invalid_json_fails([])
  def test_verify_artifact_missing_file_fails([])
  def test_sync_to_execution_state_writes_correct_shape([])
  def test_sync_to_execution_state_active_phase([])
  def test_run_state_skill_default_is_gto_v2([])


## __lib/freshness.py
  def classify_freshness([]) -> str


## __lib/hook_health.py
  def detect_hook_errors(['transcript_path', 'terminal_id', 'session_id', 'git_sha']) -> list[Finding]


## __lib/impact_radius.py
  def count_references(['root', 'file_path']) -> int
  def enrich_with_impact_radius(['root', 'findings']) -> list[Finding]


## __lib/invocation_tracker.py
  def extract_invoked_skills(['transcript_path']) -> set[str]
  def _normalize_skill(['skill']) -> str | None
  def check_invocations(['transcript_path', 'prev_recommendations', 'terminal_id', 'session_id', 'git_sha']) -> list[Finding]


## __lib/machine_render.py
  def _subletter(['idx']) -> str
  def _get_domain_def(['domain']) -> tuple[str, str]
  def _domain_sort_key(['domain', 'findings']) -> tuple[int, str]
  def _finding_file_ref(['f']) -> str
  def _render_finding_line(['f', 'opts']) -> str
  def render_actions(['findings', 'carryover', 'opts']) -> str
  def render_machine_format(['findings']) -> str


## __lib/merge.py
  def merge_findings(['deterministic', 'agent']) -> list[Finding]


## __lib/normalize.py
  def normalize_finding(['f']) -> Finding
  def normalize_findings(['findings']) -> list[Finding]


## __lib/render.py
  def render_finding(['f', 'index']) -> str
  def render_findings(['findings', 'header']) -> str


## __lib/resolve.py
  def resolve_findings(['findings', 'changed', 'root']) -> list[Finding]
  def _try_resolve(['f', 'changed', 'root']) -> Finding | None
  def _mark_resolved(['f', 'reason']) -> Finding
  def _detector_recheck(['f', 'root']) -> str | None
  def _evidence_count(['f']) -> int | None


## __lib/route.py
  def route_finding(['f']) -> Finding
  def route_findings(['findings']) -> list[Finding]


## __lib/session_goal_detector.py
  class SessionGoalDetector:
    def __init__(['project_root'])
    def detect_goal(['transcript_path']) -> SessionGoalResult
    def detect_goal_from_chain(['paths']) -> SessionGoalResult
    def is_question_style(['query']) -> bool
  def detect_session_goal(['transcript_path', 'project_root']) -> SessionGoalResult
  def __init__(['self', 'project_root'])
  def detect_goal(['self', 'transcript_path']) -> SessionGoalResult
  def detect_goal_from_chain(['self', 'paths']) -> SessionGoalResult
  def is_question_style(['self', 'query']) -> bool


## __lib/session_outcome_detector.py
  class SessionOutcomeResult:
    def to_gaps([]) -> list[dict]
  class SessionOutcomeDetector:
    def __init__(['project_root'])
    def _get_prior_outcomes_path(['terminal_id']) -> Path
    def _load_prior_outcomes(['terminal_id']) -> dict[str, bool]
    def _save_current_outcomes(['items', 'terminal_id']) -> None
    def _normalize_content(['content']) -> str
    def detect(['transcript_path', 'terminal_id']) -> SessionOutcomeResult
    def _scan_transcript(['transcript_path', 'session_age']) -> list[SessionOutcomeItem]
    def _get_current_handoff_path(['terminal_id']) -> Path | None
    def _get_prior_transcript_path(['handoff_path']) -> Path | None
    def _scan_prior_transcripts(['transcript_path', 'terminal_id', 'max_chain_depth']) -> list[SessionOutcomeItem]
  def detect_session_outcomes(['transcript_path', 'terminal_id', 'project_root']) -> SessionOutcomeResult
  def to_gaps(['self']) -> list[dict]
  def __init__(['self', 'project_root'])
  def _get_prior_outcomes_path(['self', 'terminal_id']) -> Path
  def _load_prior_outcomes(['self', 'terminal_id']) -> dict[str, bool]
  def _save_current_outcomes(['self', 'items', 'terminal_id']) -> None
  def _normalize_content(['content']) -> str
  def detect(['self', 'transcript_path', 'terminal_id']) -> SessionOutcomeResult
  def _scan_transcript(['self', 'transcript_path', 'session_age']) -> list[SessionOutcomeItem]
  def _get_current_handoff_path(['self', 'terminal_id']) -> Path | None
  def _get_prior_transcript_path(['self', 'handoff_path']) -> Path | None
  def _scan_prior_transcripts(['self', 'transcript_path', 'terminal_id', 'max_chain_depth']) -> list[SessionOutcomeItem]
  def _find_handoff_referencing(['self', 'transcript_path']) -> Path | None
  def _scan_prior_tldrs(['self', 'terminal_id']) -> list[SessionOutcomeItem]
  def _deduplicate(['self', 'items']) -> list[SessionOutcomeItem]
  def normalize(['content']) -> str
  def normalize(['content']) -> str


## __lib/state.py
  class RunState:
    def to_dict([]) -> dict
    def touch([]) -> None
  def load_state(['path']) -> RunState
  def save_state(['path', 'state']) -> None
  def sync_to_execution_state(['state', 'artifacts_dir']) -> None
  def to_dict(['self']) -> dict
  def touch(['self']) -> None


## __lib/stuckness.py
  def detect_stuckness(['root', 'chain', 'carryover_findings', 'terminal_id', 'session_id', 'git_sha']) -> list[Finding]


## __lib/targeting.py
  def resolve_target(['explicit_target', 'conversation_hint', 'artifact_target']) -> str


## __lib/transcript.py
  def read_turns(['transcript_path']) -> list[TranscriptTurn]
  def _extract_role_content(['entry']) -> tuple[str | None, str]
  def _flatten_content(['raw']) -> str
  def extract_edited_files(['transcript_path', 'root']) -> list[Path]


## __lib/util.py
  def atomic_write_text(['path', 'text']) -> None
  def atomic_write_json(['path', 'payload']) -> None


## __lib/verification_debt.py
  def detect_verification_debt(['transcript_path', 'terminal_id', 'session_id', 'git_sha']) -> list[Finding]


## __lib/verify.py
  def verify_artifact(['artifact_path']) -> dict[str, Any]
  def verify_state(['state_path']) -> dict[str, Any]


## __lib/workflow_hygiene.py
  def detect_workflow_hygiene(['root', 'terminal_id', 'session_id', 'git_sha']) -> list[Finding]


## agents/__init__.py
  def parse_agent_result(['path', 'agent_name']) -> AgentResult


## agents/action_normalizer.py
  def write_handoff(['path', 'findings']) -> None
  def read_result(['path']) -> AgentResult


## agents/domain_analyzer.py
  def write_handoff(['path', 'findings', 'project_context']) -> None
  def read_result(['path']) -> AgentResult


## agents/findings_reviewer.py
  def write_handoff(['path', 'findings']) -> None
  def read_result(['path']) -> AgentResult


## agents/gap_reviewer.py
  def write_handoff(['path', 'findings', 'session_outcomes', 'changed_files', 'session_context', 'detectors_ran', 'detectors_empty']) -> None
  def read_result(['path']) -> AgentResult


## agents/prompts.py
  (no top-level functions/classes)


## agents/session_reviewer.py
  def write_handoff(['path', 'outcomes', 'transcript_excerpts']) -> None
  def read_result(['path']) -> AgentResult


## hooks/__init__.py
  (no top-level functions/classes)


## hooks/common.py
  def get_terminal_id([]) -> str
  def get_project_root([]) -> Path
  def get_artifacts_root([]) -> Path
  def get_verified_identity(['session_id']) -> dict | None
  def gto_state_dir(['session_id']) -> Path
  def is_gto_active(['session_id']) -> bool
  def read_state(['session_id']) -> dict
  def write_state(['state']) -> None
  def read_hook_input([]) -> dict
  def write_hook_output(['data']) -> None


## hooks/posttooluse.py
  def run(['data']) -> dict | None
  def _is_failure(['output']) -> bool
  def _capture_failure(['tool_name', 'tool_input', 'output', 'session_id']) -> None
  def _record_file_change(['file_path', 'session_id']) -> None
  def main([]) -> None


## hooks/pretooluse.py
  def _matches_pattern(['tokens', 'pattern']) -> bool
  def run(['data']) -> dict | None
  def main([]) -> None


## hooks/sessionstart.py
  def _count_findings_in_artifact(['artifact_path']) -> int
  def _count_resolved_carryover(['state', 'session_id']) -> int
  def run(['data']) -> dict | None
  def main([]) -> None


## hooks/stop.py
  def run(['data']) -> dict | None
  def main([]) -> None


## models.py
  class Finding:
    def to_dict([]) -> dict[str, Any]
  class GTOArtifact:
    def empty(['cls', 'mode', 'terminal_id', 'session_id', 'target', 'git_sha']) -> GTOArtifact
  def to_dict(['self']) -> dict[str, Any]
  def empty(['cls', 'mode', 'terminal_id', 'session_id', 'target', 'git_sha']) -> GTOArtifact


## orchestrator.py
  def parse_args(['argv']) -> argparse.Namespace
  def _resolve_transcript_from_identity(['terminal_id']) -> Path | None
  def _load_session_chain(['terminal_id']) -> list[str]
  def _convert_outcome_findings(['outcome_result', 'terminal_id', 'session_id', 'git_sha']) -> list[Finding]
  def _extract_context(['transcript_path', 'items', 'window']) -> list[dict[str, str]]
  def run(['argv']) -> int


## settings.py
  class GTOSettings:
    def paths([]) -> GTOPaths
  def paths(['self']) -> property


## test_context_boundaries.py
  def snap_to_word(['remainder']) -> str
  def test_snaps_start_to_word([])
  def test_snaps_end_to_word([])
  def test_normal_content_unchanged([])
  def test_empty_remainder([])
  def test_already_word_boundary([])
  def test_path_mid_segment([])
  def test_hooks_di_corruption([])


## APPENDIX: FULL SOURCE


### __init__.py

```python
__all__ = ["models", "settings", "orchestrator"]

```


### __lib/__init__.py

```python

```


### __lib/assertions.py

```python
#!/usr/bin/env python3
"""CLI-runnable assertions for GTO artifact verification.

Usage:
    python -m skills.gto.__lib.assertions <artifact_path> [--state <state_path>]

Exit codes:
    0 — all assertions pass
    1 — one or more assertions failed (details on stderr)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    args = sys.argv[1:]
    if not args:
        print("Usage: assertions.py <artifact_path> [--state <state_path>]", file=sys.stderr)
        sys.exit(1)

    artifact_path = Path(args[0])
    state_path: Path | None = None

    if "--state" in args:
        idx = args.index("--state")
        if idx + 1 < len(args):
            state_path = Path(args[idx + 1])

    errors: list[str] = []

    # Verify artifact exists and is valid JSON
    if not artifact_path.exists():
        print(f"FAIL: artifact not found: {artifact_path}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"FAIL: cannot parse artifact: {exc}", file=sys.stderr)
        sys.exit(1)

    # Required fields
    required = ["artifact_version", "terminal_id", "session_id", "findings",
                "machine_output", "human_output"]
    for field in required:
        if field not in data:
            errors.append(f"missing field: {field}")

    # Machine output must have RNS format
    machine = data.get("machine_output", [])
    if isinstance(machine, list):
        if not any(isinstance(l, str) and l.startswith("RNS|D|") for l in machine):
            errors.append("machine_output missing RNS|D| header")
        if not any(isinstance(l, str) and l.startswith("RNS|Z|") for l in machine):
            errors.append("machine_output missing RNS|Z| terminator")

    # Findings must be a list
    findings = data.get("findings")
    if not isinstance(findings, list):
        errors.append("findings is not a list")

    # State verification if provided
    if state_path:
        if not state_path.exists():
            errors.append(f"state file not found: {state_path}")
        else:
            try:
                state = json.loads(state_path.read_text(encoding="utf-8"))
                if state.get("phase") != "completed":
                    errors.append(f"state phase is '{state.get('phase')}', expected 'completed'")
            except (json.JSONDecodeError, OSError) as exc:
                errors.append(f"cannot parse state: {exc}")

    if errors:
        for e in errors:
            print(f"FAIL: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"PASS: {artifact_path} ({len(findings or [])} findings)")
    sys.exit(0)


if __name__ == "__main__":
    main()

```


### __lib/branch_awareness.py

```python
"""Git branch awareness — adjusts recommendations based on current branch.

On feature branches, de-prioritize merge-time concerns (/docs, /deps)
and prioritize code quality checks (/sqa, /diagnose).
"""
from __future__ import annotations

import subprocess
from dataclasses import replace
from pathlib import Path

from ..models import Finding

# Skills to de-prioritize on feature branches
MERGE_TIME_SKILLS = {"/docs", "/deps"}

# Skills to prioritize on feature branches
QUALITY_SKILLS = {"/sqa", "/diagnose", "pytest"}


def get_current_branch(root: Path) -> str | None:
    """Get the current git branch name. Returns None on error."""
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "branch", "--show-current"],
            text=True,
        )
        return out.strip() or None
    except subprocess.CalledProcessError:
        return None


def adjust_for_branch(root: Path, findings: list[Finding]) -> list[Finding]:
    """Adjust finding priorities based on current git branch.

    On main/default branches, all priorities apply as-is.
    On feature branches:
    - Merge-time skills (/docs, /deps) get priority lowered
    - Quality skills (/sqa, /diagnose) stay at current priority
    """
    branch = get_current_branch(root)
    if not branch or branch in ("main", "master"):
        return findings

    # We're on a feature branch
    adjusted: list[Finding] = []
    for f in findings:
        if f.owner_skill in MERGE_TIME_SKILLS and f.priority != "low":
            adjusted.append(replace(
                f,
                priority="low",
                metadata={**f.metadata, "branch_adjusted": True, "branch": branch},
            ))
        else:
            adjusted.append(f)

    return adjusted

```


### __lib/carryover.py

```python
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from ..models import Finding, EvidenceRef
from .util import atomic_write_json

# Severity escalation ladder — each step bumps one level
SEVERITY_LADDER: dict[str, str] = {
    "low": "medium",
    "medium": "high",
    "high": "critical",
    "critical": "critical",
}


def load_carryover(artifacts_dir: Path) -> list[Finding]:
    """Load carryover findings from prior GTO runs in this terminal scope.

    Looks for `carryover.json` in the artifacts directory.
    Returns empty list if file doesn't exist or is unparseable.
    """
    path = artifacts_dir / "carryover.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []

    findings: list[Finding] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        evidence = [
            EvidenceRef(
                kind=e.get("kind", ""),
                value=e.get("value", ""),
                detail=e.get("detail"),
            )
            for e in item.get("evidence", [])
            if isinstance(e, dict)
        ]
        findings.append(
            Finding(
                id=item.get("id", "CARRY-???"),
                title=item.get("title", "Carryover finding"),
                description=item.get("description", ""),
                source_type="carryover",
                source_name="carryover",
                domain=item.get("domain", "other"),
                gap_type=item.get("gap_type", "carryover"),
                severity=item.get("severity", "medium"),
                evidence_level=item.get("evidence_level", "unverified"),
                action=item.get("action", "recover"),
                priority=item.get("priority", "medium"),
                status=item.get("status", "open"),
                scope=item.get("scope", "local"),
                owner_skill=item.get("owner_skill"),
                owner_reason=item.get("owner_reason"),
                file=item.get("file"),
                line=item.get("line"),
                symbol=item.get("symbol"),
                reversibility=item.get("reversibility"),
                effort=item.get("effort"),
                target=item.get("target"),
                depends_on=item.get("depends_on", []),
                evidence=evidence,
                tags=item.get("tags", []),
                terminal_id=item.get("terminal_id"),
                session_id=item.get("session_id"),
                git_sha=item.get("git_sha"),
                freshness=item.get("freshness"),
                unverified=item.get("unverified", True),
                metadata=item.get("metadata", {}),
            )
        )
    return findings


def save_carryover(artifacts_dir: Path, findings: list[Finding]) -> None:
    """Save findings as carryover for future runs.

    Persists open findings (to re-surface) and resolved findings (to suppress).
    Rejected findings are discarded. Increments _carry_count on open findings.
    """
    carryover: list[Finding] = []
    for f in findings:
        if f.status == "rejected":
            continue
        # Increment carry count on open findings so future runs can escalate/decay
        if f.status == "open":
            count = f.metadata.get("_carry_count", 0) + 1
            first_seen = f.metadata.get("_first_seen")
            if first_seen is None:
                from datetime import datetime, timezone
                first_seen = datetime.now(timezone.utc).isoformat()
            new_meta = {**f.metadata, "_carry_count": count, "_first_seen": first_seen}
            f = replace(f, metadata=new_meta)
        carryover.append(f)

    path = artifacts_dir / "carryover.json"
    data = [f.to_dict() for f in carryover]
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(path, data)


def load_carryover_open_only(artifacts_dir: Path) -> list[Finding]:
    """Load only open (unresolved) carryover findings."""
    return [f for f in load_carryover(artifacts_dir) if f.status == "open"]


def apply_carryover_enrichment(
    findings: list[Finding],
    changed_files: list[str] | None = None,
) -> list[Finding]:
    """Apply escalation and decay to carryover findings.

    Escalation: systemic/architectural findings carried 2+ times get severity bump
    and "RECURRING" prefix on title.

    Decay: local-scoped findings whose referenced file was changed get a staleness
    note — the context that produced the finding may no longer exist.
    """
    enriched: list[Finding] = []
    for f in findings:
        count: int = f.metadata.get("_carry_count", 0)

        if count >= 2 and f.scope in ("systemic", "architectural"):
            new_sev = SEVERITY_LADDER.get(f.severity, f.severity)
            title = f.title
            if not title.startswith("RECURRING"):
                title = f"RECURRING ({count}x): {title}"
            f = replace(f, severity=new_sev, priority=new_sev, title=title)

        elif count >= 3 and f.scope == "local" and f.file:
            if changed_files and f.file in changed_files:
                desc = f.description
                tag = "[context may have changed]"
                if tag not in desc:
                    desc = f"{desc} {tag} — file modified since finding created"
                f = replace(f, description=desc, evidence_level="unverified")

        enriched.append(f)
    return enriched


def prune_carryover(artifacts_dir: Path, max_resolved: int = 50) -> None:
    """Remove old resolved findings to prevent unbounded growth."""
    findings = load_carryover(artifacts_dir)
    open_findings = [f for f in findings if f.status != "resolved"]
    resolved_findings = [f for f in findings if f.status == "resolved"]
    if len(resolved_findings) <= max_resolved:
        return
    kept = resolved_findings[-max_resolved:]
    all_findings = open_findings + kept
    path = artifacts_dir / "carryover.json"
    data = [f.to_dict() for f in all_findings]
    path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(path, data)

```


### __lib/changelog.py

```python
"""Changelog detector — reads git log since previous GTO run.

Compares current git_sha against the previous run's git_sha to identify
changed files, then emits findings for skills that may need re-running
based on those changes.
"""
from __future__ import annotations

import subprocess
from dataclasses import replace
from pathlib import Path

from ..models import EvidenceRef, Finding

# File pattern → skill recommendations for changed files.
# Each entry is (path_prefix, extension, skill, reason).
# A file matches if it starts with path_prefix and ends with extension.
FILE_SKILL_MAP: list[tuple[str, str, str, str]] = [
    ("skills/", "SKILL.md", "/sqa", "skill definition changed — quality check may find new issues"),
    ("skills/", ".py", "/sqa", "skill implementation changed — semantic layer may find defects"),
    (".claude/hooks/", ".py", "/sqa --layer=L7", "hook changed — operational verification needed"),
    ("tests/", ".py", "pytest", "test files changed — run test suite to verify"),
    ("", ".md", "/docs", "documentation changed — validate consistency"),
    ("", "pyproject.toml", "/deps", "dependency config changed — check for stale deps"),
    ("", "requirements", "/deps", "dependencies changed — check for CVEs and updates"),
]


def _matches_entry(path: str, prefix: str, extension: str) -> bool:
    """Check if path starts with prefix and ends with extension."""
    if prefix and not path.startswith(prefix):
        return False
    if extension and not path.endswith(extension):
        return False
    return True

# Domain for changelog findings
CHANGELOG_DOMAIN = "session"

# Staleness wave thresholds
WAVE_THRESHOLDS = (
    (10, "significant"),   # 10+ files changed
    (3, "moderate"),       # 3-9 files changed
    (0, "incremental"),    # 1-2 files changed
)


def classify_change_wave(file_count: int, commit_count: int) -> str:
    """Classify changelog volume for staleness wave reporting."""
    for threshold, label in WAVE_THRESHOLDS:
        if file_count >= threshold:
            return label
    return "incremental"


# Skill categories that can be anti-recommended (not needed)
# Maps a skill category to a descriptive label for anti-recommendations
SKILL_CATEGORIES: dict[str, str] = {
    "/sqa": "code quality checks",
    "pytest": "test suite",
    "/docs": "documentation validation",
    "/deps": "dependency auditing",
    "/sqa --layer=L7": "hook verification",
}


def _base_skill(skill: str) -> str:
    """Normalize skill variants to base skill for category comparison."""
    if skill.startswith("/sqa"):
        return "/sqa"
    return skill


def get_changed_files(root: Path, prev_sha: str, curr_sha: str) -> list[str]:
    """Return list of files changed between two git SHAs, relative to root."""
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "diff", "--name-only", f"{prev_sha}..{curr_sha}"],
            text=True,
        )
    except subprocess.CalledProcessError:
        return []
    return [line.strip() for line in out.strip().splitlines() if line.strip()]


def get_commit_count(root: Path, prev_sha: str, curr_sha: str) -> int:
    """Return number of commits between two SHAs."""
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "rev-list", "--count", f"{prev_sha}..{curr_sha}"],
            text=True,
        )
        return int(out.strip())
    except (subprocess.CalledProcessError, ValueError):
        return 0


def map_changed_files_to_skills(
    changed_files: list[str],
) -> dict[str, list[tuple[str, str]]]:
    """Map changed files to affected skills.

    Returns: {skill: [(file_path, reason), ...]}
    """
    skill_files: dict[str, list[tuple[str, str]]] = {}
    for fp in changed_files:
        for prefix, extension, skill, reason in FILE_SKILL_MAP:
            if _matches_entry(fp, prefix, extension):
                skill_files.setdefault(skill, []).append((fp, reason))
    return skill_files


def _matches_pattern(path: str, pattern: str) -> bool:
    """Match path against a glob pattern supporting ** (any depth)."""
    from pathlib import PurePosixPath
    return PurePosixPath(path).match(pattern)


def detect_changelog_findings(
    root: Path,
    prev_sha: str | None,
    curr_sha: str | None,
    terminal_id: str,
    session_id: str,
    git_sha: str | None,
) -> list[Finding]:
    """Detect findings from git changelog since previous GTO run.

    Returns findings recommending skill re-runs for changed files.
    Returns empty list if no previous SHA available or no changes detected.
    """
    if not prev_sha or not curr_sha or prev_sha == curr_sha:
        return []

    # Verify both SHAs exist in the repo
    for sha in (prev_sha, curr_sha):
        try:
            subprocess.check_output(
                ["git", "-C", str(root), "cat-file", "-t", sha],
                text=True,
            )
        except subprocess.CalledProcessError:
            return []

    changed = get_changed_files(root, prev_sha, curr_sha)
    if not changed:
        return []

    commit_count = get_commit_count(root, prev_sha, curr_sha)
    skill_map = map_changed_files_to_skills(changed)
    wave = classify_change_wave(len(changed), commit_count)

    findings: list[Finding] = []

    # One finding per affected skill
    for idx, (skill, file_reasons) in enumerate(
        sorted(skill_map.items()), start=1
    ):
        files = list({f for f, _ in file_reasons})
        reasons = list({r for _, r in file_reasons})
        description = (
            f"{commit_count} commits with {len(files)} files changed since last GTO run "
            f"affect {skill}: {', '.join(reasons[:3])}"
        )

        # Staleness wave: significant changes elevate severity
        base_severity = "medium"
        base_priority = "medium"
        if wave == "significant":
            base_severity = "high"
            base_priority = "high"

        findings.append(
            Finding(
                id=f"CHANGELOG-{idx:03d}",
                title=f"Changes affect {skill} — consider re-running",
                description=description,
                source_type="detector",
                source_name="changelog_detector",
                domain=CHANGELOG_DOMAIN,
                gap_type="stale_skill",
                severity=base_severity,
                evidence_level="verified",
                action="realize",
                priority=base_priority,
                owner_skill=skill,
                terminal_id=terminal_id,
                session_id=session_id,
                git_sha=git_sha,
                evidence=[
                    EvidenceRef(
                        kind="git_diff",
                        value=f"{prev_sha[:12]}..{curr_sha[:12]}",
                        detail=f"{commit_count} commits, {len(changed)} files, {len(files)} relevant, wave={wave}",
                    ),
                ],
            )
        )

    # If there are changed files that don't match any skill pattern,
    # emit a generic finding
    unmatched = []
    for fp in changed:
        if not any(_matches_entry(fp, prefix, ext) for prefix, ext, _, _ in FILE_SKILL_MAP):
            unmatched.append(fp)

    if unmatched and len(unmatched) <= 10:
        findings.append(
            Finding(
                id="CHANGELOG-UNMATCHED-001",
                title=f"{len(unmatched)} changed files not covered by skill patterns",
                description=(
                    f"Files changed since last run that don't map to known skill patterns: "
                    f"{', '.join(unmatched[:10])}"
                ),
                source_type="detector",
                source_name="changelog_detector",
                domain=CHANGELOG_DOMAIN,
                gap_type="untracked_changes",
                severity="low",
                evidence_level="verified",
                action="realize",
                priority="low",
                terminal_id=terminal_id,
                session_id=session_id,
                git_sha=git_sha,
                evidence=[
                    EvidenceRef(
                        kind="git_diff",
                        value=f"{prev_sha[:12]}..{curr_sha[:12]}",
                        detail=f"{len(unmatched)} unmatched files",
                    ),
                ],
            )
        )

    # Anti-recommendations: skills NOT affected by the changes.
    # Only emit when the change set is narrow enough to be confident.
    triggered_skills = {_base_skill(s) for s in skill_map}
    all_skills = {_base_skill(s) for _, _, s, _ in FILE_SKILL_MAP}
    untriggered = all_skills - triggered_skills

    if untriggered and wave in ("incremental", "moderate"):
        skipped = sorted(untriggered)
        skipped_labels = [SKILL_CATEGORIES.get(s, s) for s in skipped]
        findings.append(
            Finding(
                id="CHANGELOG-ANTI-001",
                title=f"Change wave '{wave}' — {len(skipped)} skill categories not needed",
                description=(
                    f"Changes since last run only affect {sorted(triggered_skills)}. "
                    f"The following are unlikely to find new issues: {', '.join(skipped_labels)}"
                ),
                source_type="detector",
                source_name="changelog_detector",
                domain=CHANGELOG_DOMAIN,
                gap_type="no_action_needed",
                severity="low",
                evidence_level="verified",
                action="skip",
                priority="low",
                terminal_id=terminal_id,
                session_id=session_id,
                git_sha=git_sha,
                evidence=[
                    EvidenceRef(
                        kind="anti_recommendation",
                        value=", ".join(skipped),
                        detail=f"wave={wave}, {len(changed)} files, {len(skipped)} skills unaffected",
                    ),
                ],
            )
        )

    return findings

```


### __lib/clustering.py

```python
"""Finding clustering — groups findings by directory or module prefix.

When multiple findings reference files in the same directory or module,
clusters them into a single recommendation for that area.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from pathlib import PurePosixPath

from ..models import Finding


def _extract_dir(file_path: str | None) -> str | None:
    """Extract directory prefix from a file path."""
    if not file_path:
        return None
    parts = PurePosixPath(file_path).parts
    if len(parts) <= 1:
        return None
    # Use first 2 path segments as cluster key
    return "/".join(parts[:2])


def cluster_findings(findings: list[Finding]) -> list[Finding]:
    """Cluster findings by directory and emit grouped recommendations.

    Findings without a file reference pass through unchanged.
    Findings with files in the same directory get merged into one
    clustered finding per directory per skill.

    Returns the original findings plus any cluster summary findings.
    """
    # Group by (directory, owner_skill)
    clusters: dict[tuple[str, str | None], list[Finding]] = defaultdict(list)
    unclustered: list[Finding] = []

    for f in findings:
        d = _extract_dir(f.file)
        if d:
            clusters[(d, f.owner_skill)].append(f)
        else:
            unclustered.append(f)

    # Only create cluster findings when 3+ findings share a directory+skill
    cluster_findings: list[Finding] = []
    for idx, ((directory, skill), group) in enumerate(
        sorted(clusters.items()), start=1
    ):
        if len(group) < 3:
            unclustered.extend(group)
            continue

        ids = [f.id for f in group]
        titles = list({f.title[:60] for f in group})
        severity = max(
            group,
            key=lambda f: {"critical": 3, "high": 2, "medium": 1, "low": 0}.get(f.severity, 0),
        ).severity

        cluster_findings.append(
            Finding(
                id=f"CLUSTER-{idx:03d}",
                title=f"{len(group)} findings cluster in {directory}/ — consider {skill or 'review'}",
                description=(
                    f"Clustered findings: {', '.join(ids[:5])}. "
                    f"Areas: {', '.join(titles[:3])}"
                ),
                source_type="detector",
                source_name="clustering",
                domain=group[0].domain,
                gap_type="clustered_findings",
                severity=severity,
                evidence_level="derived",
                action="realize",
                priority=severity,
                owner_skill=skill,
                file=directory,
                evidence=[],
                metadata={"clustered_ids": ids},
            )
        )

    return unclustered + cluster_findings

```


### __lib/completion_checker.py

```python
"""Completion checker — filters session outcomes that were actually completed.

For each detected outcome, reads the surrounding transcript context and checks
whether the goal was actually addressed during the session. This closes the gap
where the regex-based outcome detector can't distinguish:
  "I want to build X" → assistant builds X → user confirms (completed)
from:
  "I want to build X" → never addressed (genuine gap)
"""
from __future__ import annotations

import re
from pathlib import Path

from .session_outcome_detector import SessionOutcomeItem
from .transcript import read_turns

# Assistant completion signals — strong evidence the goal was addressed
ASSISTANT_COMPLETION_PATTERNS = [
    re.compile(r"(?:done|finished|completed)\s+(?:implementing|building|adding|creating|fixing)\b", re.IGNORECASE),
    re.compile(r"(?:implemented|built|added|created|fixed)\s+(?:the\s+)?\S", re.IGNORECASE),
    re.compile(r"successfully\s+(?:created|implemented|built|added|fixed|updated)", re.IGNORECASE),
]

# User confirmation signals — follows an assistant action, confirms completion
USER_CONFIRMATION_PATTERNS = [
    re.compile(r"(?:looks?\s+good|works?\s+(?:now|great|perfect)|that's?\s+it|perfect|great\s+job)", re.IGNORECASE),
    re.compile(r"(?:thanks?\s*(?:!|\.)|verified|confirmed|tested\s+and\s+it\s+works)", re.IGNORECASE),
]

# Weak signals — NOT enough to mark as completed (pass through for LLM review)
WEAK_SIGNALS = [
    re.compile(r"(?:started|began|working\s+on)\b", re.IGNORECASE),
]


def _turns_to_dicts(transcript_path: Path) -> list[dict[str, str]]:
    """Read transcript turns via shared reader, return as {role, content} dicts."""
    return [{"role": t.role, "content": t.content} for t in read_turns(transcript_path)]


def _content_keywords(content: str) -> set[str]:
    """Extract significant keywords from outcome content for matching."""
    # Remove stop words, keep substantive terms
    stop = {"the", "a", "an", "to", "for", "in", "on", "of", "and", "or", "is", "it", "with", "by"}
    words = re.findall(r"[a-z]{3,}", content.lower())
    return {w for w in words if w not in stop}


def _has_completion_evidence(
    window_turns: list[dict[str, str]],
    outcome_keywords: set[str],
) -> bool:
    """Check if the window turns contain strong completion evidence.

    Requires BOTH:
    1. An assistant completion signal (done implementing, built the X, etc.)
    2. Either keyword overlap with the outcome content OR a user confirmation
    """
    has_assistant_signal = False
    has_user_confirmation = False
    matched_keywords: set[str] = set()

    for turn in window_turns:
        role = turn["role"]
        content = turn["content"].lower()

        if role == "assistant":
            for pattern in ASSISTANT_COMPLETION_PATTERNS:
                if pattern.search(content):
                    has_assistant_signal = True
            # Check keyword overlap
            turn_words = set(re.findall(r"[a-z]{3,}", content))
            matched_keywords |= (turn_words & outcome_keywords)

        elif role == "user":
            for pattern in USER_CONFIRMATION_PATTERNS:
                if pattern.search(content):
                    has_user_confirmation = True

    if not has_assistant_signal:
        return False

    # Require keyword overlap with outcome content in all cases
    if matched_keywords & outcome_keywords:
        return True

    return False


def check_completions(
    transcript_path: Path | None,
    items: list[SessionOutcomeItem],
    window: int = 10,
) -> list[SessionOutcomeItem]:
    """Filter outcomes that were likely completed.

    For each detected outcome, reads the N turns after it in the transcript.
    If the surrounding context contains strong completion signals from the
    assistant (with keyword match or user confirmation), the item is removed.

    Returns the filtered list (completed items removed).
    """
    if not transcript_path or not transcript_path.exists() or not items:
        return items

    turns = _turns_to_dicts(transcript_path)
    if not turns:
        return items

    kept: list[SessionOutcomeItem] = []

    for item in items:
        turn_idx = item.turn_number - 1  # turn_number is 1-based
        if turn_idx < 0 or turn_idx >= len(turns):
            kept.append(item)
            continue

        # Extract window of turns after this item
        window_end = min(turn_idx + window + 1, len(turns))
        window_turns = turns[turn_idx + 1 : window_end]

        if not window_turns:
            kept.append(item)
            continue

        outcome_keywords = _content_keywords(item.content)

        if _has_completion_evidence(window_turns, outcome_keywords):
            continue  # Completed — filter out

        kept.append(item)

    return kept

```


### __lib/context.py

```python
from __future__ import annotations

from pathlib import Path
import subprocess


def get_git_sha(root: Path) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
        ).strip()
        return out or None
    except Exception:
        return None


def git_dirty(root: Path) -> bool:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "status", "--porcelain"], text=True
        )
        return bool(out.strip())
    except Exception:
        return False

```


### __lib/context_boundaries.py

```python
"""Work context boundary detection — detects context switches within a session.

Identifies when a user starts a new goal after already working on one,
indicating multiple work contexts that should be tracked separately.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from ..models import EvidenceRef, Finding
from .transcript import read_turns

# Goal-starting patterns that indicate a new work context
NEW_GOAL_PATTERNS = [
    re.compile(r"(?:now let's|also let's|next let's|I also want to|I also need to)\s+", re.IGNORECASE),
    re.compile(r"(?:let's (?:also |now )?(?:switch|move|pivot|start))\s+", re.IGNORECASE),
    re.compile(r"(?:actually,?\s+(?:let's|I want to|I need to))\s+", re.IGNORECASE),
    re.compile(r"(?:moving on to|switching to|pivoting to)\s+", re.IGNORECASE),
    re.compile(r"(?:one more thing|before I forget|also,?\s+(?:I|let's))\s+", re.IGNORECASE),
]


@dataclass
class WorkContext:
    """A single work context within a session."""
    start_turn: int
    goal_phrase: str | None
    is_complete: bool = False


def detect_context_boundaries(transcript_path: Path | None) -> list[WorkContext]:
    """Detect work context boundaries in a transcript.

    Returns a list of WorkContext objects, one per detected context switch.
    The first context (implicit, from session start) is not included.
    """
    if not transcript_path or not transcript_path.exists():
        return []

    turns = read_turns(transcript_path)
    contexts: list[WorkContext] = []

    for turn in turns:
        if turn.role != "user":
            continue
        for pattern in NEW_GOAL_PATTERNS:
            match = pattern.search(turn.content)
            if match:
                # Extract the goal phrase (rest of the sentence)
                remainder = turn.content[match.end():].strip()
                # Snap start AND end to word boundaries to avoid
                # mid-path/mid-word corruption when pattern ends mid-segment
                # or truncation cuts mid-word.
                start_r = re.search(r"\w", remainder)
                start_offset = start_r.start() if start_r else 0
                end_offset = start_offset + 100
                if end_offset < len(remainder):
                    pre_end = remainder[start_offset:end_offset]
                    # Find complete words (word followed by separator) in pre_end
                    last_match = None
                    for m in re.finditer(r"\w+(?=\W)", pre_end):
                        last_match = m
                    if last_match:
                        end_offset = start_offset + last_match.end()
                phrase = remainder[start_offset:end_offset]
                contexts.append(WorkContext(
                    start_turn=turn.turn_number,
                    goal_phrase=phrase,
                ))
                break  # One match per turn is enough

    return contexts


def context_boundary_findings(
    transcript_path: Path | None,
    terminal_id: str = "",
    session_id: str = "",
    git_sha: str | None = None,
) -> list[Finding]:
    """Emit findings for detected context switches."""
    contexts = detect_context_boundaries(transcript_path)
    if not contexts:
        return []

    findings: list[Finding] = []
    for idx, ctx in enumerate(contexts, start=1):
        findings.append(
            Finding(
                id=f"CONTEXT-SWITCH-{idx:03d}",
                title=f"Context switch at turn {ctx.start_turn}",
                description=(
                    f"User started a new work context: \"{ctx.goal_phrase}\". "
                    f"Prior work context may have unfinished items."
                ),
                source_type="detector",
                source_name="context_boundaries",
                domain="session",
                gap_type="context_switch",
                severity="low",
                evidence_level="verified",
                action="realize",
                priority="low",
                terminal_id=terminal_id,
                session_id=session_id,
                git_sha=git_sha,
                evidence=[
                    EvidenceRef(
                        kind="context_boundary",
                        value=f"turn={ctx.start_turn}",
                        detail=ctx.goal_phrase or "",
                    ),
                ],
            )
        )

    return findings

```


### __lib/coverage.py

```python
from __future__ import annotations

from typing import Any

from ..models import Finding


def compute_coverage(findings: list[Finding]) -> dict[str, Any]:
    """Compute coverage summary for a list of findings.

    Returns a dict with domain coverage, severity breakdown, and routing stats.
    """
    by_domain: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    by_action: dict[str, int] = {}
    routed = 0
    unrouted = 0
    verified = 0
    unverified_count = 0

    for f in findings:
        by_domain[f.domain] = by_domain.get(f.domain, 0) + 1
        by_severity[f.severity] = by_severity.get(f.severity, 0) + 1
        by_action[f.action] = by_action.get(f.action, 0) + 1
        if f.owner_skill:
            routed += 1
        else:
            unrouted += 1
        if f.unverified:
            unverified_count += 1
        else:
            verified += 1

    return {
        "total": len(findings),
        "by_domain": by_domain,
        "by_severity": by_severity,
        "by_action": by_action,
        "routed": routed,
        "unrouted": unrouted,
        "verified": verified,
        "unverified": unverified_count,
    }


def compute_health_score(findings: list[Finding], freshness: str = "fresh") -> dict[str, Any]:
    """Compute a session health score from findings and freshness.

    Score: 0-100 where 100 = no open findings, fresh artifact.
    Tracks resolved vs open to show improvement trajectory.
    """
    total = len(findings)
    if total == 0:
        return {"score": 100, "grade": "A", "freshness": freshness, "total": 0}

    resolved = sum(1 for f in findings if f.status == "resolved")
    open_count = sum(1 for f in findings if f.status == "open")
    critical = sum(1 for f in findings if f.severity == "critical" and f.status != "resolved")

    # Base score from resolution rate
    resolution_rate = resolved / total if total > 0 else 1.0
    base_score = resolution_rate * 80  # Max 80 from resolution

    # Bonus for freshness
    freshness_bonus = {"fresh": 20, "unknown": 10, "stale-git": 0, "stale-target": 0}
    bonus = freshness_bonus.get(freshness, 10)

    # Penalty for critical open findings
    critical_penalty = min(critical * 10, 30)

    score = max(0, min(100, int(base_score + bonus - critical_penalty)))

    grades = [(90, "A"), (75, "B"), (60, "C"), (40, "D"), (0, "F")]
    grade = next(g for threshold, g in grades if score >= threshold)

    return {
        "score": score,
        "grade": grade,
        "freshness": freshness,
        "total": total,
        "resolved": resolved,
        "open": open_count,
        "critical_open": critical,
        "resolution_rate": round(resolution_rate, 2),
    }

```


### __lib/dedupe.py

```python
from __future__ import annotations

from ..models import Finding


def dedupe_findings(findings: list[Finding]) -> list[Finding]:
    """Deduplicate findings by (domain, title, file).

    Keeps the first occurrence when duplicates are found.
    """
    seen: set[str] = set()
    result: list[Finding] = []
    for f in findings:
        key = f"{f.domain}|{f.title}|{f.file or ''}"
        if key not in seen:
            seen.add(key)
            result.append(f)
    return result

```


### __lib/dependency_order.py

```python
from __future__ import annotations

from ..models import Finding

SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
DOMAIN_RANK = {
    "security": 0,
    "quality": 1,
    "tests": 2,
    "performance": 3,
    "docs": 4,
    "deps": 5,
    "git": 6,
    "other": 7,
}

# Skill dependency ordering — run prerequisites first
# Maps skill → list of skills that should run before it
SKILL_PREREQUISITES: dict[str, list[str]] = {
    "/docs": ["/code", "/sqa"],
    "/deps": ["/sqa"],
    "/sqa --layer=L7": ["/sqa"],
}


def _skill_order_rank(skill: str | None) -> int:
    """Return ordering rank for a skill based on dependency graph.

    Lower = should run first. Skills not in the graph get rank 5.
    """
    if not skill:
        return 5
    # Base skills that others depend on come first
    base_skills = {"/code", "/diagnose", "/perf", "pytest", "/sqa"}
    if skill in base_skills:
        return 1
    if skill in SKILL_PREREQUISITES:
        return 3
    return 5


def order_findings(findings: list[Finding]) -> list[Finding]:
    """Order findings by severity, domain, and skill dependency."""
    return sorted(
        findings,
        key=lambda f: (
            SEVERITY_RANK.get(f.severity, 99),
            DOMAIN_RANK.get(f.domain, 99),
            _skill_order_rank(f.owner_skill),
            f.id,
        ),
    )

```


### __lib/detectors.py

```python
from __future__ import annotations

import json
import os
from pathlib import Path

from ..models import EvidenceRef, Finding


def run_basic_detectors(
    root: Path, terminal_id: str, session_id: str, git_sha: str | None
) -> list[Finding]:
    findings: list[Finding] = []

    if not (root / ".git").exists():
        findings.append(
            Finding(
                id="GIT-001",
                title="Repository metadata missing",
                description="Target directory does not contain a .git directory.",
                source_type="detector",
                source_name="basic_detectors",
                domain="git",
                gap_type="invalidrepo",
                severity="high",
                evidence_level="verified",
                scope="systemic",
                terminal_id=terminal_id,
                session_id=session_id,
                git_sha=git_sha,
                evidence=[EvidenceRef(kind="path", value=str(root / ".git"))],
            )
        )

    readme = root / "README.md"
    if not readme.exists():
        findings.append(
            Finding(
                id="DOC-001",
                title="README missing",
                description="Project root does not contain a README.md.",
                source_type="detector",
                source_name="basic_detectors",
                domain="docs",
                gap_type="missingdocs",
                severity="medium",
                evidence_level="verified",
                scope="local",
                terminal_id=terminal_id,
                session_id=session_id,
                git_sha=git_sha,
                evidence=[EvidenceRef(kind="path", value=str(readme))],
            )
        )

    return findings


def detect_marker_staleness(
    root: Path, terminal_id: str, session_id: str, git_sha: str | None
) -> list[Finding]:
    """Detect stale session markers persisting from previous runs.

    Checks:
    - carryover.json git_sha mismatches current git_sha
    - handoff JSON entries with mismatched terminal_id or session_id
    - identity.json session_id mismatches actual session
    """
    findings: list[Finding] = []
    artifacts_root = Path(os.environ.get("CLAUDE_ARTIFACTS_ROOT", root / ".claude/.artifacts"))
    term_dir = artifacts_root / terminal_id / "gto"

    # Check carryover.json for git_sha staleness
    carryover_path = term_dir / "carryover.json"
    if carryover_path.exists():
        try:
            with open(carryover_path, encoding="utf-8") as f:
                data = json.load(f)
            entries = data if isinstance(data, list) else data.get("findings", [])
            for entry in entries:
                stored_sha = entry.get("git_sha") or entry.get("metadata", {}).get("git_sha")
                if stored_sha and git_sha and stored_sha != git_sha:
                    finding_id = entry.get("id", "CARRYOVER-001")
                    findings.append(
                        Finding(
                            id=f"QUALITY-marker_staleness-{finding_id[:16]}",
                            title="Carryover finding has stale git_sha",
                            description=f"Carryover entry '{finding_id}' references git_sha '{stored_sha}' which differs from current run's '{git_sha}'. This indicates the finding was captured in a prior session and may not reflect current codebase state.",
                            source_type="detector",
                            source_name="marker_staleness_detector",
                            domain="quality",
                            gap_type="marker_staleness",
                            severity="medium",
                            evidence_level="verified",
                            action="recover",
                            priority="medium",
                            terminal_id=terminal_id,
                            session_id=session_id,
                            git_sha=git_sha,
                            evidence=[
                                EvidenceRef(kind="artifact", value=str(carryover_path), detail=f"entry_id={finding_id}, stored_sha={stored_sha}, current_sha={git_sha}"),
                            ],
                        )
                    )
        except (json.JSONDecodeError, OSError):
            pass

    # Check gap_reviewer_handoff.json for terminal_id / session_id mismatches
    handoff_path = term_dir / "gap_reviewer_handoff.json"
    if handoff_path.exists():
        try:
            with open(handoff_path, encoding="utf-8") as f:
                hdata = json.load(f)
            ctx = hdata.get("session_context", {})
            h_terminal_id = ctx.get("terminal_id")
            h_git_sha = ctx.get("git_sha")
            if h_terminal_id and h_terminal_id != terminal_id:
                findings.append(
                    Finding(
                        id="QUALITY-marker_staleness-handoff-terminal",
                        title="Gap reviewer handoff has mismatched terminal_id",
                        description=f"Handoff references terminal_id '{h_terminal_id}' but current terminal is '{terminal_id}'. This suggests the handoff was generated for a different terminal session.",
                        source_type="detector",
                        source_name="marker_staleness_detector",
                        domain="quality",
                        gap_type="marker_staleness",
                        severity="high",
                        evidence_level="verified",
                        action="recover",
                        priority="high",
                        terminal_id=terminal_id,
                        session_id=session_id,
                        git_sha=git_sha,
                        evidence=[
                            EvidenceRef(kind="artifact", value=str(handoff_path), detail=f"handoff_terminal={h_terminal_id}, current_terminal={terminal_id}"),
                        ],
                    )
                )
            if h_git_sha and git_sha and h_git_sha != git_sha:
                findings.append(
                    Finding(
                        id="QUALITY-marker_staleness-handoff-sha",
                        title="Gap reviewer handoff has stale git_sha",
                        description=f"Handoff references git_sha '{h_git_sha}' which differs from current run's '{git_sha}'. Detector evidence may be stale.",
                        source_type="detector",
                        source_name="marker_staleness_detector",
                        domain="quality",
                        gap_type="marker_staleness",
                        severity="medium",
                        evidence_level="verified",
                        action="recover",
                        priority="medium",
                        terminal_id=terminal_id,
                        session_id=session_id,
                        git_sha=git_sha,
                        evidence=[
                            EvidenceRef(kind="artifact", value=str(handoff_path), detail=f"handoff_sha={h_git_sha}, current_sha={git_sha}"),
                        ],
                    )
                )
        except (json.JSONDecodeError, OSError):
            pass

    return findings


def detect_missing_verification_evidence(
    root: Path, terminal_id: str, session_id: str, git_sha: str | None
) -> list[Finding]:
    """Detect when findings cite hooks/telemetry mechanisms without supporting evidence.

    Checks:
    - Findings citing hook paths → verify the hook script exists and has test coverage
    - Findings citing telemetry → verify telemetry event traces exist in session artifacts
    - Findings citing session state → verify the state file exists
    """
    findings: list[Finding] = []
    artifacts_root = Path(os.environ.get("CLAUDE_ARTIFACTS_ROOT", root / ".claude/.artifacts"))
    term_dir = artifacts_root / terminal_id / "gto"

    # Read current run's artifact to get finding evidence references
    artifact_path = term_dir / "outputs" / "artifact.json"
    if not artifact_path.exists():
        return findings

    try:
        with open(artifact_path, encoding="utf-8") as f:
            artifact = json.load(f)
    except (json.JSONDecodeError, OSError):
        return findings

    findings_data = artifact.get("findings", [])

    for f in findings_data:
        evidence_list = f.get("evidence", [])
        for ev in evidence_list:
            kind = ev.get("kind", "")
            value = ev.get("value", "")

            # Check hook path references for test coverage
            if kind == "path" and ("hook" in value.lower() or "stop" in value.lower() or "pretool" in value.lower()):
                hook_path = root / value if not Path(value).is_absolute() else Path(value)
                if hook_path.exists():
                    # Check for corresponding test file
                    test_variants = [
                        hook_path.parent / "tests" / f"test_{hook_path.name}",
                        hook_path.parent / f"test_{hook_path.name}",
                        hook_path.parent.parent / "tests" / f"test_{hook_path.stem}_py",
                    ]
                    has_test = any(t.exists() for t in test_variants)
                    if not has_test:
                        findings.append(
                            Finding(
                                id=f"QUALITY-unverified_implementation_claim-{f.get('id', 'FINDING')[:16]}",
                                title="Finding cites hook without test coverage",
                                description=f"Finding '{f.get('id')}' references hook '{value}' but no test file was found. The implementation claim (hook fires correctly, handles all cases) is unverified.",
                                source_type="detector",
                                source_name="missing_verification_detector",
                                domain="quality",
                                gap_type="unverified_implementation_claim",
                                severity="medium",
                                evidence_level="unverified",
                                action="recover",
                                priority="medium",
                                terminal_id=terminal_id,
                                session_id=session_id,
                                git_sha=git_sha,
                                evidence=[
                                    EvidenceRef(kind="path", value=value, detail="hook cited without test coverage"),
                                    EvidenceRef(kind="path", value=str(test_variants[0].parent / "tests"), detail="checked test locations, none found"),
                                ],
                            )
                        )

            # Check telemetry references
            if kind == "telemetry" or "telemetry" in value.lower():
                telemetry_marker = term_dir / "telemetry_events.jsonl"
                if not telemetry_marker.exists():
                    findings.append(
                        Finding(
                            id=f"QUALITY-unverified_implementation_claim-telemetry-{f.get('id', 'FINDING')[:16]}",
                            title="Finding cites telemetry without event traces",
                            description=f"Finding '{f.get('id')}' references telemetry mechanism but no telemetry event log was found in this session. The behavioral claim is unverified.",
                            source_type="detector",
                            source_name="missing_verification_detector",
                            domain="quality",
                            gap_type="unverified_implementation_claim",
                            severity="low",
                            evidence_level="unverified",
                            action="recover",
                            priority="low",
                            terminal_id=terminal_id,
                            session_id=session_id,
                            git_sha=git_sha,
                            evidence=[
                                EvidenceRef(kind="artifact", value=str(telemetry_marker), detail="telemetry event log not found"),
                            ],
                        )
                    )

    return findings


# Export all detectors for orchestrator use
DETECTOR_REGISTRY = {
    "basic_detectors": run_basic_detectors,
    "marker_staleness_detector": detect_marker_staleness,
    "missing_verification_detector": detect_missing_verification_evidence,
}

```


### __lib/docs_followup.py

```python
from __future__ import annotations

from pathlib import Path

from ..models import Finding, EvidenceRef


def detect_docs_followup(root: Path, findings: list[Finding]) -> list[Finding]:
    """Add documentation follow-up findings when code changes lack doc updates.

    Only triggers when:
    - There are quality/test/security findings with file references
    - The referenced file lacks corresponding documentation updates
    """
    doc_findings: list[Finding] = []
    seen_files: set[str] = set()

    for f in findings:
        if not f.file or f.file in seen_files:
            continue
        if f.domain not in ("quality", "tests", "security"):
            continue
        seen_files.add(f.file)

        filepath = root / f.file
        if not filepath.exists():
            continue

        # Check if a nearby doc file exists (convention: same dir, README or docs/)
        doc_candidates = [
            filepath.parent / "README.md",
            filepath.parent / "docs" / f"{filepath.stem}.md",
        ]
        has_doc = any(d.exists() for d in doc_candidates)

        if not has_doc and f.severity in ("critical", "high"):
            doc_findings.append(
                Finding(
                    id=f"DOC-FOLLOWUP-{len(doc_findings) + 1:03d}",
                    title=f"Missing docs for {f.file}",
                    description=f"High-severity finding in {f.file} but no documentation found nearby.",
                    source_type="detector",
                    source_name="docs_followup",
                    domain="docs",
                    gap_type="missingdocs",
                    severity="low",
                    evidence_level="derived",
                    action="prevent",
                    priority="low",
                    file=f.file,
                    evidence=[EvidenceRef(kind="path", value=str(filepath))],
                )
            )

    return doc_findings

```


### __lib/evidence.py

```python
from __future__ import annotations

import json
from pathlib import Path

from ..models import GTOArtifact, Finding
from .machine_render import render_machine_format
from .render import render_findings
from .util import atomic_write_json


def write_artifact(
    artifact_path: Path,
    artifact: GTOArtifact,
    findings: list[Finding],
) -> Path:
    """Write the GTO artifact JSON file with machine and human output.

    Returns the path written.
    """
    machine_lines = render_machine_format(findings).splitlines()
    human_output = render_findings(findings)

    artifact.findings = findings
    artifact.machine_output = machine_lines
    artifact.human_output = human_output

    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(artifact_path, _artifact_to_dict(artifact))
    return artifact_path


def _artifact_to_dict(artifact: GTOArtifact) -> dict:
    return {
        "artifact_version": artifact.artifact_version,
        "mode": artifact.mode,
        "created_at": artifact.created_at,
        "terminal_id": artifact.terminal_id,
        "session_id": artifact.session_id,
        "target": artifact.target,
        "git_sha": artifact.git_sha,
        "health_score": artifact.health_score,
        "freshness": artifact.freshness,
        "findings": [f.to_dict() for f in artifact.findings],
        "summary": artifact.summary,
        "machine_output": artifact.machine_output,
        "human_output": artifact.human_output,
        "verification": artifact.verification,
        "coverage": artifact.coverage,
        "metadata": artifact.metadata,
    }

```


### __lib/execution_contract_test.py

```python
"""Tests for gto_v2 execution-contract integration.

Mechanical tests for:
- RNS marker verification in artifacts
- path isolation (gto_v2 vs gto)
- sync_to_execution_state output shape
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from skills.gto_v2.__lib.state import RunState, sync_to_execution_state
from skills.gto_v2.__lib.verify import verify_artifact


def test_verify_artifact_with_rns_markers_valid():
    """Artifact with both RNS|D| and RNS|Z| markers passes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "artifact.json"
        path.write_text(json.dumps({
            "artifact_version": "1.0.0",
            "mode": "full",
            "terminal_id": "test",
            "session_id": "test",
            "target": "test",
            "findings": [{"id": "TEST-001"}],
            "machine_output": [
                "RNS|D|test",
                "TEST-001 [low] some finding",
                "RNS|Z|",
            ],
            "human_output": "",
            "verification": {},
            "coverage": {},
        }), encoding="utf-8")

        result = verify_artifact(path)
        assert result["valid"] is True
        assert result["errors"] == []


def test_verify_artifact_missing_rns_d_marker_fails():
    """Artifact missing RNS|D| marker fails if it has findings."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "artifact.json"
        path.write_text(json.dumps({
            "artifact_version": "1.0.0",
            "mode": "full",
            "terminal_id": "test",
            "session_id": "test",
            "target": "test",
            "findings": [{"id": "TEST-001"}],
            "machine_output": [
                "some line",
                "RNS|Z|",
            ],
            "human_output": "",
            "verification": {},
            "coverage": {},
        }), encoding="utf-8")

        result = verify_artifact(path)
        assert result["valid"] is False
        assert any("RNS|D|" in e for e in result["errors"])


def test_verify_artifact_missing_rns_z_marker_fails():
    """Artifact missing RNS|Z| marker fails."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "artifact.json"
        path.write_text(json.dumps({
            "artifact_version": "1.0.0",
            "mode": "full",
            "terminal_id": "test",
            "session_id": "test",
            "target": "test",
            "findings": [{"id": "TEST-001"}],
            "machine_output": [
                "RNS|D|test",
                "TEST-001 [low] some finding",
            ],
            "human_output": "",
            "verification": {},
            "coverage": {},
        }), encoding="utf-8")

        result = verify_artifact(path)
        assert result["valid"] is False
        assert any("RNS|Z|" in e for e in result["errors"])


def test_verify_artifact_invalid_json_fails():
    """Artifact with invalid JSON fails."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "artifact.json"
        path.write_text("not valid json {{{", encoding="utf-8")

        result = verify_artifact(path)
        assert result["valid"] is False
        assert any("Cannot parse" in e for e in result["errors"])


def test_verify_artifact_missing_file_fails():
    """Artifact file that does not exist fails."""
    path = Path("/tmp/does_not_exist_12345.json")

    result = verify_artifact(path)
    assert result["valid"] is False
    assert any("not found" in e for e in result["errors"])


def test_sync_to_execution_state_writes_correct_shape():
    """sync_to_execution_state produces the expected execution-state.json structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir) / "console_test" / "gto_v2"
        base.mkdir(parents=True)
        (base / "outputs").mkdir()

        state = RunState(
            skill="gto_v2",
            run_id="test-run-001",
            phase="completed",
            current_target="P:\\\\\\test",
            git_sha="abc123",
            last_artifact=str(base / "outputs" / "artifact.json"),
            expected_artifacts=[],
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:01:00Z",
        )

        sync_to_execution_state(state, base)

        exec_path = base.parent / "execution-state.json"
        assert exec_path.exists(), "execution-state.json not written"

        data = json.loads(exec_path.read_text(encoding="utf-8"))

        assert data["run_id"] == "test-run-001"
        assert data["skill_name"] == "gto_v2"
        assert data["contract_type"] == "workflow-execution"
        assert data["phase"] == "completed"
        assert data["status"] == "complete"
        assert str(base / "outputs" / "artifact.json") in data["required_artifacts"]
        assert data["completed_artifacts"] == [str(base / "outputs" / "artifact.json")]
        assert data["missing_requirements"] == []
        assert "Bash" in data["allowed_tools_now"]
        assert "Read" in data["allowed_tools_now"]


def test_sync_to_execution_state_active_phase():
    """sync_to_execution_state sets status=active when phase is not completed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir) / "console_test" / "gto_v2"
        base.mkdir(parents=True)

        state = RunState(
            skill="gto_v2",
            run_id="test-run-002",
            phase="running",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:30Z",
        )

        sync_to_execution_state(state, base)

        exec_path = base.parent / "execution-state.json"
        data = json.loads(exec_path.read_text(encoding="utf-8"))

        assert data["phase"] == "running"
        assert data["status"] == "active"


def test_run_state_skill_default_is_gto_v2():
    """RunState defaults skill to gto_v2."""
    state = RunState()
    assert state.skill == "gto_v2"

```


### __lib/freshness.py

```python
from __future__ import annotations


def classify_freshness(
    *,
    artifact_git_sha: str | None,
    current_git_sha: str | None,
    artifact_target: str | None,
    current_target: str | None,
) -> str:
    # If either target is missing, we can't determine freshness reliably
    if artifact_target is None or current_target is None:
        return "unknown"
    if artifact_target != current_target:
        return "stale-target"
    # Targets match — check git SHA
    if artifact_git_sha is not None and current_git_sha is not None:
        if artifact_git_sha != current_git_sha:
            return "stale-git"
        return "fresh"
    # Targets match but git SHA unavailable
    return "unknown"

```


### __lib/hook_health.py

```python
"""Hook health detector — scans transcript for hook execution errors.

Detects hook attachment entries with non-zero exit codes, indicating
hook failures that may have been silently suppressed (non-blocking errors).

What it detects:
- Hook executions with non-zero exit codes (errors, warnings)
- Hooks that consistently fail across sessions (via carryover)
- SessionStart hook failures that may affect session setup

What it does NOT detect:
- PreToolUse exit(2) blocks (these are intentional, not errors)
- Hook performance issues (that's a separate concern)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..models import EvidenceRef, Finding

# PreToolUse exit(2) is intentional blocking — not a health issue
_BLOCKING_HOOK_PREFIXES = ("PreToolUse:", "UserPromptSubmit:")

# Hooks where non-zero exit is expected behavior
_EXPECTED_NONZERO_HOOKS = frozenset({
    "PreToolUse:edit", "PreToolUse:write", "PreToolUse:bash",
    "PreToolUse:read", "PreToolUse:agent", "PreToolUse:skill",
})


def detect_hook_errors(
    transcript_path: Path | None,
    terminal_id: str = "",
    session_id: str = "",
    git_sha: str | None = None,
) -> list[Finding]:
    """Scan transcript for hook execution errors.

    Reads raw JSONL to find attachment entries with non-zero exit codes,
    filtering out intentional PreToolUse blocks.

    Returns:
        List of findings for genuine hook errors.
    """
    if not transcript_path or not transcript_path.exists():
        return []

    errors: list[dict[str, Any]] = []

    try:
        with open(transcript_path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                att = entry.get("attachment")
                if not isinstance(att, dict):
                    continue

                att_type = att.get("type", "")
                if "hook" not in att_type:
                    continue

                hook_name = att.get("hookName", "")
                exit_code = att.get("exitCode", 0)
                stderr = (att.get("stderr") or "").strip()

                # Skip intentional PreToolUse blocks
                if exit_code == 2 and any(
                    hook_name.startswith(p) for p in _BLOCKING_HOOK_PREFIXES
                ):
                    continue

                # Skip expected non-zero hooks
                if hook_name.lower() in _EXPECTED_NONZERO_HOOKS and exit_code == 2:
                    continue

                # Only flag actual errors (non-zero, non-2 exit codes)
                if exit_code not in (0, 2):
                    errors.append({
                        "hook_name": hook_name,
                        "exit_code": exit_code,
                        "stderr": stderr[:300],
                        "type": att_type,
                        "duration_ms": att.get("durationMs"),
                    })
    except (OSError, PermissionError):
        return []

    if not errors:
        return []

    # Deduplicate by hook_name — keep the most recent error per hook
    seen_hooks: dict[str, dict[str, Any]] = {}
    for err in errors:
        seen_hooks[err["hook_name"]] = err

    findings: list[Finding] = []
    for idx, (hook_name, err) in enumerate(seen_hooks.items()):
        # Classify severity by hook type
        severity = "high" if "SessionStart" in hook_name else "medium"

        stderr_preview = err["stderr"][:150] if err["stderr"] else "no stderr output"
        findings.append(
            Finding(
                id=f"HOOK-{idx + 1:03d}",
                title=f"Hook error: {hook_name}",
                description=(
                    f"Hook '{hook_name}' exited with code {err['exit_code']}. "
                    f"stderr: {stderr_preview}"
                ),
                source_type="detector",
                source_name="hook_health_detector",
                domain="quality",
                gap_type="runtime_error",
                severity=severity,
                evidence_level="verified",
                action="recover",
                priority=severity,
                scope="local",
                terminal_id=terminal_id,
                session_id=session_id,
                git_sha=git_sha,
                evidence=[
                    EvidenceRef(
                        kind="hook_error",
                        value=hook_name,
                        detail=f"exit_code={err['exit_code']}, stderr={stderr_preview[:100]}",
                    ),
                ],
            )
        )

    return findings

```


### __lib/impact_radius.py

```python
"""Impact radius estimation — count import references for changed files.

When a file changes, count how many other files import or reference it.
A finding with impact radius 20 is more urgent than one with radius 1.
"""
from __future__ import annotations

import subprocess
from dataclasses import replace
from pathlib import Path

from ..models import Finding


def count_references(root: Path, file_path: str) -> int:
    """Count how many files import or reference the given file.

    Uses git grep to count references. Returns 0 on error.
    """
    # Extract module name from path (e.g., "skills/gto/__lib/changelog.py" → "changelog")
    stem = Path(file_path).stem
    if stem.startswith("__"):
        return 0

    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "grep", "-r", "--count", "-w", stem, "--", "*.py"],
            text=True,
        )
        # git grep --count outputs "file:count" lines
        total = 0
        for line in out.strip().splitlines():
            if ":" in line:
                parts = line.rsplit(":", 1)
                if parts[-1].isdigit() and parts[0] != file_path:
                    total += int(parts[-1])
        return total
    except subprocess.CalledProcessError:
        return 0


def enrich_with_impact_radius(
    root: Path,
    findings: list[Finding],
) -> list[Finding]:
    """Add impact radius metadata to findings that have file references.

    For each finding with a file reference, counts how many other files
    reference it and stores the count in metadata. Findings with high
    impact radius get elevated severity.
    """
    enriched: list[Finding] = []
    for f in findings:
        if not f.file:
            enriched.append(f)
            continue

        radius = count_references(root, f.file)
        if radius == 0:
            enriched.append(f)
            continue

        new_meta = {**f.metadata, "impact_radius": radius}

        # High impact radius elevates severity one step
        severity = f.severity
        priority = f.priority
        if radius >= 10 and f.severity == "medium":
            severity = "high"
            priority = "high"

        enriched.append(replace(
            f,
            severity=severity,
            priority=priority,
            metadata=new_meta,
            description=f"{f.description} [impact radius: {radius}]",
        ))

    return enriched

```


### __lib/invocation_tracker.py

```python
"""Skill invocation tracker — checks whether GTO recommendations were actioned.

Reads the session transcript for slash-command invocations, then compares
against the previous GTO artifact's owner_skill recommendations to determine
which were actioned and which were not.
"""
from __future__ import annotations

import json
import re
from dataclasses import replace
from pathlib import Path

from ..models import EvidenceRef, Finding
from .transcript import read_turns

# Pattern to match slash-command invocations in transcript text
# Matches "/skill", "/skill --flag", "/skill arg1 arg2"
SLASH_COMMAND_RE = re.compile(r"(?:^|\s)(/[a-z][\w-]*(?:\s+[\w=.-]+)*)", re.MULTILINE)


def extract_invoked_skills(transcript_path: Path | None) -> set[str]:
    """Extract slash-command invocations from a transcript.

    Returns a set of base skill names (e.g., {"/sqa", "/docs", "/deps"}).
    """
    if not transcript_path or not transcript_path.exists():
        return set[str]()

    turns = read_turns(transcript_path)
    skills: set[str] = set()
    for turn in turns:
        if turn.role != "user":
            continue
        for match in SLASH_COMMAND_RE.finditer(turn.content):
            command = match.group(1).strip().split()[0]  # Take just the /command part
            skills.add(command)
    return skills


def _normalize_skill(skill: str | None) -> str | None:
    """Normalize a skill name for comparison.

    "/sqa --layer=L7" → "/sqa", "pytest" → "pytest"
    """
    if not skill:
        return None
    return skill.split()[0].split("--")[0].rstrip()


def check_invocations(
    transcript_path: Path | None,
    prev_recommendations: list[Finding],
    terminal_id: str = "",
    session_id: str = "",
    git_sha: str | None = None,
) -> list[Finding]:
    """Check which previous GTO recommendations were actioned.

    Compares the set of invoked skills against the owner_skill of previous
    recommendations. Emits findings for unactioned recommendations.

    Returns actioned/unactioned findings.
    """
    invoked = extract_invoked_skills(transcript_path)

    if not prev_recommendations:
        return []

    findings: list[Finding] = []
    unactioned: list[Finding] = []

    for rec in prev_recommendations:
        base = _normalize_skill(rec.owner_skill)
        if not base:
            continue

        # Check if the skill was invoked (match /sqa against both /sqa and /sqa --layer=L7)
        was_invoked = any(
            inv.startswith(base) or base.startswith(inv)
            for inv in invoked
        )

        if was_invoked:
            findings.append(replace(
                rec,
                status="resolved",
                metadata={**rec.metadata, "invocation_tracked": True},
            ))
        else:
            unactioned.append(rec)

    # Emit a single finding listing unactioned recommendations
    if unactioned:
        skills_list = sorted({
            _normalize_skill(f.owner_skill) or "unknown"
            for f in unactioned
        })
        findings.append(
            Finding(
                id="INVOCATION-UNACTIONED-001",
                title=f"{len(unactioned)} previous recommendations not actioned",
                description=(
                    f"Skills recommended by prior GTO run but not invoked this session: "
                    f"{', '.join(skills_list)}"
                ),
                source_type="detector",
                source_name="invocation_tracker",
                domain="session",
                gap_type="unactioned_recommendation",
                severity="low",
                evidence_level="verified" if invoked else "unverified",
                action="realize",
                priority="low",
                terminal_id=terminal_id,
                session_id=session_id,
                git_sha=git_sha,
                evidence=[
                    EvidenceRef(
                        kind="invocation_check",
                        value=", ".join(skills_list),
                        detail=f"{len(invoked)} skills invoked, {len(unactioned)} unactioned",
                    ),
                ],
            )
        )

    return findings

```


### __lib/machine_render.py

```python
from __future__ import annotations

from dataclasses import dataclass

from ..models import Finding

# Domain definitions matching RNS render.py DOMAIN_MAP
DOMAIN_MAP: dict[str, tuple[str, str]] = {
    "quality": ("🔧", "QUALITY"),
    "code_quality": ("🔧", "QUALITY"),
    "tests": ("🧪", "TESTS"),
    "testing": ("🧪", "TESTS"),
    "docs": ("📄", "DOCS"),
    "documentation": ("📄", "DOCS"),
    "security": ("🔒", "SECURITY"),
    "performance": ("⚡", "PERFORMANCE"),
    "git": ("🐙", "GIT"),
    "deps": ("📦", "DEPS"),
    "dependencies": ("📦", "DEPS"),
    "session": ("💬", "SESSION"),
    "other": ("📌", "OTHER"),
}

ACTION_ORDER = ("recover", "prevent", "realize")
ACTION_LABELS: dict[str, str] = {
    "recover": "Recovery",
    "prevent": "Preserve",
    "realize": "Future",
}
PRIORITY_ORDER = ("critical", "high", "medium", "low")

PRIORITY_DOT_MAP: dict[str, str] = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🔵",
}


def _subletter(idx: int) -> str:
    """Return Excel-style column label for 1-based index: 1→a, 26→z, 27→aa."""
    result: list[str] = []
    n = idx - 1
    while True:
        n, rem = divmod(n, 26)
        result.append(chr(ord("a") + rem))
        if n == 0:
            break
    return "".join(reversed(result))


def _get_domain_def(domain: str) -> tuple[str, str]:
    return DOMAIN_MAP.get(domain, ("📌", domain.upper()))


def _domain_sort_key(domain: str, findings: list[Finding]) -> tuple[int, str]:
    """Sort domains: explicit order first, then by count descending."""
    explicit_order = {
        "quality": 0, "code_quality": 0,
        "tests": 1, "testing": 1,
        "docs": 2, "documentation": 2,
        "security": 3,
        "performance": 4,
        "git": 5,
        "deps": 6, "dependencies": 6,
        "session": 7,
        "other": 8,
    }
    return (explicit_order.get(domain, 99), -len(findings), domain)


# ---------------------------------------------------------------------------
# Human-readable renderer
# ---------------------------------------------------------------------------


@dataclass
class RenderOptions:
    show_file_refs: bool = True
    show_effort: bool = True
    show_owner: bool = True
    show_done: bool = True
    unverified_marker: str = "[UNVERIFIED]"
    max_description_chars: int | None = None


DEFAULT_OPTIONS = RenderOptions()


def _finding_file_ref(f: Finding) -> str:
    if f.file:
        return f"{f.file}:{f.line}" if f.line else f.file
    return ""


def _render_finding_line(f: Finding, opts: RenderOptions) -> str:
    """Render a single Finding as a compact line with priority dot and annotations."""
    dot = PRIORITY_DOT_MAP.get(f.priority, "⚪")
    parts = [f"{dot} "]

    desc = f.description
    if opts.max_description_chars and len(desc) > opts.max_description_chars:
        desc = desc[:opts.max_description_chars].rstrip() + "…"
    parts.append(desc)

    if opts.show_effort and f.effort:
        parts.append(f"[E:{f.effort}]")

    if f.unverified:
        parts.append(opts.unverified_marker)

    if opts.show_owner and f.owner_skill:
        parts.append(f"{{{f.owner_skill}}}")

    if opts.show_file_refs:
        ref = _finding_file_ref(f)
        if ref:
            parts.append(f"@ {ref}")

    return " ".join(parts)


def render_actions(
    findings: list[Finding],
    carryover: list[Finding] | None = None,
    opts: RenderOptions | None = None,
) -> str:
    """Render findings as human-readable RNS output with domain grouping.

    Adapted from RNS render.py render_actions(). Groups by domain, then by
    action type (recover/prevent/realize), with priority dots and annotations.
    """
    opts = opts or DEFAULT_OPTIONS
    carryover = carryover or []

    done_items = [f for f in findings if f.status == "resolved"] if opts.show_done else []
    pending = [f for f in findings if f.status != "resolved"]

    groups: dict[str, list[Finding]] = {}
    for f in pending:
        groups.setdefault(f.domain, []).append(f)

    lines: list[str] = []
    domain_num = 0

    for domain_key, domain_findings in sorted(
        groups.items(),
        key=lambda kv: _domain_sort_key(kv[0], kv[1]),
    ):
        domain_num += 1
        emoji, label = _get_domain_def(domain_key)
        lines.append(f"{domain_num} {emoji} {label} ({len(domain_findings)})")

        action_groups: dict[str, list[Finding]] = {}
        for f in domain_findings:
            action_groups.setdefault(f.action, []).append(f)

        item_counter = 0
        for action_key in ACTION_ORDER:
            if action_key not in action_groups:
                continue
            subgroup = action_groups[action_key]
            sorted_subgroup = sorted(
                subgroup,
                key=lambda f: (
                    PRIORITY_ORDER.index(f.priority) if f.priority in PRIORITY_ORDER else len(PRIORITY_ORDER),
                ),
            )
            label = ACTION_LABELS.get(action_key, action_key.title())
            lines.append(f"  {label} ({len(sorted_subgroup)} items)")

            prev_priority = None
            for f in sorted_subgroup:
                if prev_priority is not None and f.priority != prev_priority:
                    lines.append("")
                item_counter += 1
                sub = _subletter(item_counter)
                lines.append(f"    {domain_num}{sub} {_render_finding_line(f, opts)}")
                prev_priority = f.priority

        lines.append("")

    # Carryover section
    if carryover:
        co_num = domain_num + 1
        lines.append(f"{co_num} 📌 CARRYOVER ({len(carryover)} items)")
        for idx, f in enumerate(carryover, start=1):
            sub = _subletter(idx)
            lines.append(f"  {co_num}{sub} {_render_finding_line(f, opts)}")
        lines.append("")

    # Done section
    if done_items and opts.show_done:
        done_num = domain_num + (1 if carryover else 0) + 1
        lines.append(f"{done_num} ✓ DONE ({len(done_items)} items)")
        for idx, f in enumerate(done_items, start=1):
            sub = _subletter(idx)
            line = _render_finding_line(f, opts)
            # Strikethrough description
            parts = line.split(" ", 1)
            if len(parts) > 1:
                line = parts[0] + " ~~" + parts[1] + "~~"
            lines.append(f"  {done_num}{sub} {line}")
        lines.append("")

    # Do-all footer
    total = len(pending) + len(carryover)
    if total > 0:
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append(f"0 — Do ALL Recommended Next Actions ({total} items)")

    return "\n".join(lines).strip()


# ---------------------------------------------------------------------------
# Machine-format renderer
# ---------------------------------------------------------------------------


def render_machine_format(findings: list[Finding]) -> str:
    """Render findings in RNS-compatible machine-parseable pipe-delimited format.

    Format matches RNS render.py render_machine_format():
        RNS|D|{num}|{emoji}|{label}
        RNS|A|{num}{sub}|{domain}|E:{effort}|{action}/{priority}|{desc}|{file_ref}|owner={owner}|done={done}|caused_by={caused_by}|blocks={blocks}|unverified={unverified}
        RNS|Z|0|NONE

    This is the authoritative machine output contract for GTO artifacts.
    """
    lines: list[str] = ["<!-- format: machine -->"]

    # Group findings by domain
    groups: dict[str, list[Finding]] = {}
    for f in findings:
        groups.setdefault(f.domain, []).append(f)

    domain_num = 0
    for domain_key, domain_findings in groups.items():
        domain_num += 1
        emoji, label = _get_domain_def(domain_key)
        lines.append(f"RNS|D|{domain_num}|{emoji}|{label}")

        for idx, f in enumerate(domain_findings, start=1):
            sub = _subletter(idx)
            effort = f.effort or "?"
            desc = f.description.replace("|", "\\|")
            file_ref = _finding_file_ref(f)
            owner = f.owner_skill or ""
            done = "1" if f.status == "resolved" else "0"
            caused_by = ""
            blocks = ""
            unverified = "1" if f.unverified else "0"
            lines.append(
                f"RNS|A|{domain_num}{sub}|{f.domain}|"
                f"E:{effort}|{f.action}/{f.priority}|"
                f"{desc}|{file_ref}|owner={owner}|done={done}|"
                f"caused_by={caused_by}|blocks={blocks}|unverified={unverified}"
            )

    lines.append("RNS|Z|0|NONE")
    return "\n".join(lines)

```


### __lib/merge.py

```python
from __future__ import annotations

from ..models import Finding


def merge_findings(deterministic: list[Finding], agent: list[Finding]) -> list[Finding]:
    """Merge deterministic detector findings with agent findings.

    Agent findings that duplicate a deterministic finding (same domain+gap_type+title)
    are dropped in favor of the deterministic version, which has higher evidence level.
    Agent findings with the same domain+gap_type but different titles are kept —
    they describe distinct gaps.
    """
    deterministic_keys = {(f.domain, f.gap_type, f.title) for f in deterministic}
    merged = list(deterministic)
    for f in agent:
        if (f.domain, f.gap_type, f.title) not in deterministic_keys:
            merged.append(f)
    return merged

```


### __lib/normalize.py

```python
from __future__ import annotations

from dataclasses import replace

from ..models import Finding

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
VALID_SEVERITIES = set(SEVERITY_ORDER)
VALID_ACTIONS = {"recover", "prevent", "realize"}
VALID_PRIORITIES = {"critical", "high", "medium", "low"}

DOMAIN_ALIASES: dict[str, str] = {
    "code_quality": "quality",
    "testing": "tests",
    "documentation": "docs",
    "dependencies": "deps",
}


def normalize_finding(f: Finding) -> Finding:
    """Normalize a finding's domain, severity, action, and priority."""
    domain = DOMAIN_ALIASES.get(f.domain, f.domain)
    severity = f.severity if f.severity in VALID_SEVERITIES else "medium"
    action = f.action if f.action in VALID_ACTIONS else "recover"
    priority = f.priority if f.priority in VALID_PRIORITIES else "medium"
    return replace(f, domain=domain, severity=severity, action=action, priority=priority)


def normalize_findings(findings: list[Finding]) -> list[Finding]:
    return [normalize_finding(f) for f in findings]

```


### __lib/render.py

```python
from __future__ import annotations

from ..models import Finding

SEVERITY_ICONS = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🔵",
}

DOMAIN_ICONS: dict[str, str] = {
    "quality": "🔧",
    "tests": "🧪",
    "docs": "📄",
    "security": "🔒",
    "performance": "⚡",
    "git": "🐙",
    "deps": "📦",
    "other": "📌",
}


def render_finding(f: Finding, index: int) -> str:
    """Render a single finding as a human-readable line."""
    icon = SEVERITY_ICONS.get(f.severity, "⚪")
    domain_icon = DOMAIN_ICONS.get(f.domain, "📌")
    parts = [f"{index}. {icon} [{f.severity.upper()}] {f.title}"]
    parts.append(f"   Domain: {domain_icon} {f.domain} | Gap: {f.gap_type}")
    parts.append(f"   {f.description}")
    if f.file:
        line_ref = f":{f.line}" if f.line else ""
        parts.append(f"   @ {f.file}{line_ref}")
    if f.owner_skill:
        parts.append(f"   → {f.owner_skill}")
    if f.unverified:
        parts.append("   [UNVERIFIED]")
    return "\n".join(parts)


def render_findings(findings: list[Finding], header: str = "GTO Findings") -> str:
    """Render all findings as a human-readable report."""
    if not findings:
        return f"{header}\nNo findings."

    lines = [f"{header} ({len(findings)} items)", ""]
    for i, f in enumerate(findings, 1):
        lines.append(render_finding(f, i))
        lines.append("")

    # Summary
    by_severity: dict[str, int] = {}
    for f in findings:
        by_severity[f.severity] = by_severity.get(f.severity, 0) + 1

    summary_parts = [f"{SEVERITY_ICONS.get(s, '⚪')} {s}: {c}" for s, c in sorted(by_severity.items())]
    lines.append(f"Summary: {' | '.join(summary_parts)}")
    return "\n".join(lines)

```


### __lib/resolve.py

```python
"""Finding resolution checker for GTO.

Determines which findings have been addressed by comparing against
session-scoped file changes and re-running detector checks.
"""
from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from ..models import EvidenceRef, Finding


def resolve_findings(
    findings: list[Finding],
    changed: set[str],
    root: Path,
) -> list[Finding]:
    """Check findings against session changes and mark resolved.

    Returns a new list with status and evidence updated for resolved findings.
    Three resolution signals:
      1. File edit match — finding targets a file that was edited this session
      2. Already resolved — finding carried over with status="resolved"
      3. Detector re-check — known detector conditions no longer hold
    """
    result: list[Finding] = []
    for f in findings:
        resolved = _try_resolve(f, changed, root)
        result.append(resolved if resolved else f)
    return result


def _try_resolve(
    f: Finding, changed: set[str], root: Path
) -> Finding | None:
    """Attempt to resolve a single finding. Returns updated Finding or None."""
    # Signal 2: already resolved
    if f.status == "resolved":
        return f

    # Signal 1: file edit match
    if f.file:
        normalized = f.file.replace("\\", "/")
        if normalized in changed:
            return _mark_resolved(f, f"file_edited: {f.file}")

    # Signal 3: detector re-check
    detector_check = _detector_recheck(f, root)
    if detector_check:
        return _mark_resolved(f, detector_check)

    return None


def _mark_resolved(f: Finding, reason: str) -> Finding:
    """Return a copy of the finding with resolved status and evidence."""
    evidence = list(f.evidence) + [
        EvidenceRef(kind="auto_resolved", value=reason)
    ]
    return replace(f, status="resolved", evidence=evidence)


def _detector_recheck(f: Finding, root: Path) -> str | None:
    """Re-run specific detector checks. Returns reason if resolved, None otherwise."""
    if f.id == "DOC-001":
        # README missing — check if it exists now
        if (root / "README.md").exists():
            return "README.md now exists"
        return None

    if f.id == "GIT-001":
        # .git missing — check if it exists now
        if (root / ".git").exists():
            return ".git directory now exists"
        return None

    return None


def _evidence_count(f: Finding) -> int | None:
    """Extract the numeric count from a finding's count evidence, if any."""
    for e in f.evidence:
        if e.kind == "count":
            try:
                return int(e.value)
            except (ValueError, TypeError):
                return None
    return None

```


### __lib/route.py

```python
from __future__ import annotations

from dataclasses import replace

from ..models import Finding

# Maps gap_type prefixes to owning skills.
# Findings not matching any route remain unrouted (owner_skill=None).
GAP_TYPE_ROUTES: dict[str, str] = {
    "missingdocs": "/docs",
    "techdebt": "/code",
    "runtime_error": "/diagnose",
    "bug": "/diagnose",
    "security": "/security",
    "perf": "/perf",
    "invalidrepo": "/git",
    "staledeps": "/deps",
}


def route_finding(f: Finding) -> Finding:
    """Route a single finding to an owning skill based on gap_type."""
    owner = GAP_TYPE_ROUTES.get(f.gap_type)
    if owner:
        return replace(
            f,
            owner_skill=owner,
            owner_reason=f"routed by gap_type '{f.gap_type}'",
        )
    return f


def route_findings(findings: list[Finding]) -> list[Finding]:
    return [route_finding(f) for f in findings]

```


### __lib/session_goal_detector.py

```python
"""SessionGoalDetector - Extract stated session goal from oldest transcript.

Priority: P1 (runs during scope discovery, after Chain Integrity Check)
Purpose: Extract stated session goal from oldest transcript

Goal phrase patterns:
- "today I want to", "the goal is", "I need to"
- "let's build", "let's fix", "let's refactor"
- "I'm trying to", "we need to", "my goal today", "this session I want"

Behavior:
- Goal found → store as session_goal string in scope result
- Not found → session_goal = null (not an error)

Question-style intent patterns:
- "what are we doing", "what's the status", "what's needed next"
- "what were we working on", "how's it going", "how is it going"
- These trigger subagent path for chain-based session comprehension
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .transcript import read_turns


@dataclass
class SessionGoalResult:
    """Result of session goal detection."""

    session_goal: str | None  # Detected goal phrase or null
    source_turn: int | None  # Turn number where goal was found
    confidence: float  # 0.0 to 1.0 confidence score


class SessionGoalDetector:
    """
    Extract stated session goal from oldest transcript.

    Uses pattern matching on user messages to find goal statements.
    """

    # Goal phrase patterns with confidence weights
    GOAL_PATTERNS = [
        (r"today I want to\s+(.+?)[.!?]?$", 0.9),
        (r"the goal is\s+(?:to\s+)?(.+?)[.!?]?$", 0.9),
        (r"I need to\s+(.+?)[.!?]?$", 0.8),
        (r"let's (?:build|fix|refactor|implement|create|add)\s+(.+?)[.!?]?$", 0.9),
        (r"I'm trying to\s+(.+?)[.!?]?$", 0.7),
        (r"we need to\s+(.+?)[.!?]?$", 0.7),
        (r"my goal today is\s+(?:to\s+)?(.+?)[.!?]?$", 0.9),
        (r"this session I want to\s+(.+?)[.!?]?$", 0.9),
    ]

    # Question-style intent patterns - trigger subagent path
    QUESTION_PATTERNS = [
        r"what are we doing",
        r"what's the status",
        r"what's needed next",
        r"what were we working on",
        r"how's it going",
        r"how is it going",
    ]

    def __init__(self, project_root: Path | None = None):
        """Initialize detector with project root.

        Args:
            project_root: Project root directory (defaults to cwd)
        """
        self.project_root = project_root or Path.cwd()

    def detect_goal(self, transcript_path: Path) -> SessionGoalResult:
        """
        Extract session goal from transcript.

        Args:
            transcript_path: Path to transcript JSONL file

        Returns:
            SessionGoalResult with detected goal (or null)
        """
        if not transcript_path.exists():
            return SessionGoalResult(session_goal=None, source_turn=None, confidence=0.0)

        turns = read_turns(transcript_path)

        for turn in turns:
            if turn.role != "user":
                continue

            for pattern, confidence in self.GOAL_PATTERNS:
                match = re.search(pattern, turn.content, re.IGNORECASE)
                if match:
                    goal = match.group(1).strip()
                    return SessionGoalResult(
                        session_goal=goal,
                        source_turn=turn.turn_number,
                        confidence=confidence,
                    )

        # No goal found
        return SessionGoalResult(session_goal=None, source_turn=None, confidence=0.0)

    def detect_goal_from_chain(self, paths: list[str]) -> SessionGoalResult:
        """
        Extract session goal from oldest transcript in chain.

        Args:
            paths: List of transcript paths (ordered oldest to newest)

        Returns:
            SessionGoalResult with detected goal from oldest transcript
        """
        if not paths:
            return SessionGoalResult(session_goal=None, source_turn=None, confidence=0.0)

        # Check oldest transcript (first in list)
        oldest_path = Path(paths[0])
        return self.detect_goal(oldest_path)

    def is_question_style(self, query: str) -> bool:
        """Check if query is a question-style intent (triggers subagent path).

        Args:
            query: User query string to check

        Returns:
            True if query matches question-style patterns, False otherwise
        """
        query_lower = query.lower()
        return any(re.search(p, query_lower) for p in self.QUESTION_PATTERNS)


# Convenience function
def detect_session_goal(
    transcript_path: Path, project_root: Path | None = None
) -> SessionGoalResult:
    """
    Quick session goal detection.

    Args:
        transcript_path: Path to transcript file
        project_root: Project root directory

    Returns:
        SessionGoalResult with detected goal
    """
    detector = SessionGoalDetector(project_root)
    return detector.detect_goal(transcript_path)

```


### __lib/session_outcome_detector.py

```python
"""SessionOutcomeDetector - Surface incomplete items from chat history.

Priority: P1 (runs during gap detection)
Purpose: Detect conversation-level outstanding items from session transcripts

What it detects:
- Stated goals that weren't completed ("I want to build X" where X wasn't done)
- Identified tasks that weren't actioned ("we need to fix Y" where Y wasn't touched)
- Open questions from prior sessions
- Deferred items that haven't been revisited

What it is NOT:
- NOT code markers (TODO:, FIXME:) — use detect_unfinished_business for those
- NOT task list items — user explicitly excluded those
- NOT file-level gaps — those come from other detectors

The key distinction: this detector looks at WHAT WAS SAID in conversation,
cross-referenced against WHAT WAS DONE, to surface unmet commitments.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .transcript import read_turns


@dataclass
class SessionOutcomeItem:
    """A single outcome item found in session history."""

    category: Literal["uncompleted_goal", "identified_task", "open_question", "deferred_item"]
    content: str
    turn_number: int
    session_age: int  # 0 = current session, 1+ = prior sessions
    confidence: float  # 0.0 to 1.0
    source: str = "transcript"  # "transcript" or "tldr"
    recurrence_count: int = 1  # How many times this item appeared across transcript turns
    acknowledged: bool = False  # True if this gap was seen in a prior session but not resolved


@dataclass
class SessionOutcomeResult:
    """Result of session outcome detection."""

    items: list[SessionOutcomeItem]
    total_count: int
    current_session_items: list[SessionOutcomeItem] = field(default_factory=list)
    prior_session_items: list[SessionOutcomeItem] = field(default_factory=list)

    def to_gaps(self) -> list[dict]:
        """Convert items to GTO gap format for RSN integration."""
        gaps = []
        for idx, item in enumerate(self.items):
            gap_id = f"SESSION-{item.category[:4].upper()}-{idx + 1:03d}"
            # Recurrence-aware severity: items appearing multiple times are higher priority
            base_severity_map = {
                "uncompleted_goal": "medium",
                "identified_task": "medium",
                "open_question": "low",
                "deferred_item": "low",
            }
            base_severity = base_severity_map.get(item.category, "low")
            # Bump severity to high if item recurred across multiple turns
            severity = "high" if item.recurrence_count >= 2 else base_severity
            category_display = {
                "uncompleted_goal": "Uncompleted Goal",
                "identified_task": "Identified Task",
                "open_question": "Open Question",
                "deferred_item": "Deferred Item",
            }
            gaps.append(
                {
                    "id": gap_id,
                    "type": f"session_outcome_{item.category}",
                    "severity": severity,
                    "message": f"[{category_display.get(item.category, item.category)}] {item.content}",
                    "file_path": None,
                    "line_number": None,
                    "confidence": item.confidence,
                    "effort_estimate_minutes": 15,  # Default estimate for session items
                    "theme": "session_outcomes",
                    "metadata": {
                        "category": item.category,
                        "session_age": item.session_age,
                        "source": item.source,
                        "recurrence_count": item.recurrence_count,
                        "acknowledged": item.acknowledged,
                    },
                }
            )
        return gaps


class SessionOutcomeDetector:
    """
    Detect incomplete items from conversation history.

    Cross-references what was stated (goals, tasks, questions) against
    what was actually done to surface unmet commitments.
    """

    # Task-intent patterns: phrases that signal user stated an intention
    TASK_INTENT_PATTERNS = [
        # Direct goal statements
        (r"I want to\s+([^\.]{10,80})", 0.8),
        (r"I need to\s+([^\.]{10,80})", 0.8),
        (r"I'd like to\s+([^\.]{10,80})", 0.8),
        # Collaborative task statements
        (r"let's\s+(?:add|build|fix|create|implement|update)\s+([^\.]{10,80})", 0.85),
        (r"we should\s+(?:add|build|fix|create|implement|update)\s+([^\.]{10,80})", 0.8),
        (r"we need to\s+([^\.]{10,80})", 0.8),
        # Future-oriented task markers
        (
            r"(?:next|tomorrow|later)\s+(?:we'll|I'll|I'll)\s+(?:add|build|fix)\s+([^\.]{10,80})",
            0.7,
        ),
        # Open question patterns (questions that may indicate unresolved issues)
        (
            r"(?:how|what|why|when|where|should|could)\s+(?:do\s+)?(?:we|I|you)\s+([^\?]{10,60})\?",
            0.6,
        ),
    ]

    # Question patterns that signal open issues
    QUESTION_PATTERNS = [
        (r"(?:not sure|could be|maybe|probably)\s+(.{10,50})", 0.6),
        (r"(?:need to|should)\s+(?:check|verify|look at|investigate)\s+([^\.]{10,60})", 0.75),
    ]

    # Deferred patterns (high confidence — kept as deterministic findings)
    DEFERRED_PATTERNS = [
        (r"(?:for now|for the moment|temporarily)\s+([^\.]{10,60})", 0.6),
        (r"(?:come back to|defer|postpone)\s+([^\.]{10,60})", 0.65),
        (r"skip(?:ping|ped)?\s+(?:this|that|it)\s+([^\.]{10,50})", 0.5),
    ]

    # Candidate patterns (low confidence — flagged for LLM session reviewer)
    # Intentionally over-sensitive; the subagent filters noise.
    CANDIDATE_PATTERNS = [
        (r"\bcan\s+(?:be\s+)?(?:deleted|removed|cleaned?\s*up?)\s+later\b", 0.4),
        (r"\bnot\s+in\s+scope\b", 0.4),
        (r"\b(?:shelve|park|table|put\s+on\s+hold)\b", 0.45),
        (r"\b(?:can|could)\s+(?:wait|stay)\s+[^\.]{0,20}(?:later|after|until)\b", 0.4),
        (r"\b(?:revisit|come\s+back)\s+[^\.]{0,30}?(?:after|later|next)\b", 0.45),
        (r"\b(?:after|once)\s+[^\.]{5,30}\s+(?:is|are)\s+(?:done|complete|finished)\b", 0.4),
        (r"\b(?:skip|leave)\s+(?:for\s+now|it\s+for\s+now)\b", 0.4),
        (r"\bcan\s+(?:stay|remain)\s*[^\.]*\b(?:deleted|removed|cleaned)\s+later\b", 0.4),
        (r"\bout\s+of\s+scope\b", 0.35),
        (r"\b(?:will|we'll)\s+(?:deal\s+with|handle|address)\s+[^\.]{5,30}\s+later\b", 0.4),
    ]

    # Patterns that indicate the item was LIKELY completed (to filter out)
    COMPLETION_SIGNALS = [
        r"(?:done|finished|completed|implemented|fixed|added|created)",
        r"(?:let's start|now let's|next let's)",
        r"(?:moving on|on to|turning to)",
    ]

    def __init__(self, project_root: Path | None = None):
        """Initialize detector.

        Args:
            project_root: Project root directory (defaults to cwd)
        """
        self.project_root = project_root or Path.cwd()

    # ── Prior outcomes persistence ─────────────────────────────────────────────

    def _get_prior_outcomes_path(self, terminal_id: str | None) -> Path:
        """Return the path for prior session outcome state.

        Stored in ~/.claude/.evidence/gto-outcomes-{terminal_id}.json
        """
        evidence_base = Path.home() / ".claude" / ".evidence"
        tid_suffix = f"-{terminal_id}" if terminal_id else ""
        return evidence_base / f"gto-outcomes{tid_suffix}.json"

    def _load_prior_outcomes(self, terminal_id: str | None) -> dict[str, bool]:
        """Load prior session outcome items as {normalized_content: acknowledged}.

        Items in the prior outcomes file that are NOT in the current session's
        detected items are "acknowledged but unresolved" — they persisted across
        sessions without being resolved.

        Items that ARE in the current session are re-marked as acknowledged=True
        (they appeared again, meaning they weren't resolved).
        """
        path = self._get_prior_outcomes_path(terminal_id)
        if not path.exists():
            return {}
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            # data: {"items": [{"content": "...", "acknowledged": bool}, ...]}
            items = data.get("items", []) if isinstance(data, dict) else data
            return {
                self._normalize_content(item["content"]): bool(item.get("acknowledged", False))
                for item in items
            }
        except (OSError, json.JSONDecodeError, PermissionError):
            return {}

    def _save_current_outcomes(
        self,
        items: list[SessionOutcomeItem],
        terminal_id: str | None,
    ) -> None:
        """Save current session outcome items for next session's acknowledgment check."""
        path = self._get_prior_outcomes_path(terminal_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "items": [
                {
                    "content": item.content,
                    "acknowledged": item.acknowledged,
                    "category": item.category,
                }
                for item in items
            ]
        }
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass  # Non-critical — evidence is still in transcript

    @staticmethod
    def _normalize_content(content: str) -> str:
        """Normalize content for cross-session comparison."""
        return re.sub(r"[^\w\s]", "", content.lower())[:80]

    def detect(
        self, transcript_path: Path | None, terminal_id: str | None = None
    ) -> SessionOutcomeResult:
        """
        Detect incomplete items from current and prior sessions.

        Args:
            transcript_path: Path to current session transcript JSONL
            terminal_id: Terminal identifier for finding prior session TLDRs

        Returns:
            SessionOutcomeResult with all detected items
        """
        items: list[SessionOutcomeItem] = []

        # 0. Load prior session outcomes for acknowledgment tracking
        prior_outcomes = self._load_prior_outcomes(terminal_id)

        # 1. Scan current transcript for stated intentions
        if transcript_path and transcript_path.exists():
            current_items = self._scan_transcript(transcript_path, session_age=0)
            items.extend(current_items)

        # 2. Follow handoff chain and scan prior session transcripts
        if transcript_path and terminal_id:
            prior_items = self._scan_prior_transcripts(transcript_path, terminal_id)
            items.extend(prior_items)

        # 3. Deduplicate items that appear in both current and prior
        items = self._deduplicate(items)

        # 4. Mark items as acknowledged if they appeared in a prior session
        # (i.e., they are still unresolved — user has seen them before)
        for item in items:
            key = self._normalize_content(item.content)
            if key in prior_outcomes:
                item.acknowledged = True

        # 5. Save current outcomes for next session's acknowledgment check
        self._save_current_outcomes(items, terminal_id)

        # 6. Categorize items
        current_session_items = [i for i in items if i.session_age == 0]
        prior_session_items = [i for i in items if i.session_age > 0]

        return SessionOutcomeResult(
            items=items,
            total_count=len(items),
            current_session_items=current_session_items,
            prior_session_items=prior_session_items,
        )

    def _scan_transcript(self, transcript_path: Path, session_age: int) -> list[SessionOutcomeItem]:
        """Scan a transcript file for outcome items.

        Args:
            transcript_path: Path to transcript JSONL
            session_age: 0 for current, 1+ for prior sessions

        Returns:
            List of detected SessionOutcomeItem
        """
        items: list[SessionOutcomeItem] = []

        turns = read_turns(transcript_path)

        completion_re = re.compile("|".join(self.COMPLETION_SIGNALS), re.IGNORECASE)

        # First pass: count occurrences of each normalized content
        content_counts: dict[str, int] = {}

        for turn in turns:
            # Only check user messages (they contain stated intentions)
            if turn.role != "user":
                continue

            content = turn.content

            # Skip very short messages (can't contain meaningful task intent)
            if len(content.strip()) < 20:
                continue

            # Detect candidate patterns FIRST — low-confidence, sent to LLM reviewer.
            # These run before the completion-signal skip because candidates like
            # "revisit X after Y is done" contain "done" but are genuine deferrals.
            for pattern, confidence in self.CANDIDATE_PATTERNS:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    candidate_content = match.group(0).strip()
                    # Use surrounding sentence context when group(1) unavailable
                    if len(candidate_content) < 10:
                        start = max(0, match.start() - 40)
                        end = min(len(content), match.end() + 40)
                        candidate_content = content[start:end].strip()
                    items.append(
                        SessionOutcomeItem(
                            category="deferred_item",
                            content=candidate_content,
                            turn_number=turn.turn_number,
                            session_age=session_age,
                            confidence=confidence,
                            source="transcript",
                        )
                    )

            # Skip remaining high-confidence scans if the turn signals completion
            if completion_re.search(content):
                continue

            # Detect task intent patterns
            for pattern, confidence in self.TASK_INTENT_PATTERNS:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    task_content = match.group(1).strip()
                    # Filter trivially short or generic content
                    if len(task_content) < 10:
                        continue
                    items.append(
                        SessionOutcomeItem(
                            category="uncompleted_goal",
                            content=task_content,
                            turn_number=turn.turn_number,
                            session_age=session_age,
                            confidence=confidence,
                            source="transcript",
                        )
                    )

            # Detect open question patterns
            for pattern, confidence in self.QUESTION_PATTERNS:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    question_content = match.group(1).strip()
                    if len(question_content) < 10:
                        continue
                    items.append(
                        SessionOutcomeItem(
                            category="open_question",
                            content=question_content,
                            turn_number=turn.turn_number,
                            session_age=session_age,
                            confidence=confidence,
                            source="transcript",
                        )
                    )

            # Detect deferred patterns
            for pattern, confidence in self.DEFERRED_PATTERNS:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    deferred_content = match.group(1).strip()
                    if len(deferred_content) < 10:
                        continue
                    items.append(
                        SessionOutcomeItem(
                            category="deferred_item",
                            content=deferred_content,
                            turn_number=turn.turn_number,
                            session_age=session_age,
                            confidence=confidence,
                            source="transcript",
                        )
                    )

        # Count occurrences of each normalized content
        def normalize(content: str) -> str:
            return re.sub(r"[^\w\s]", "", content.lower())[:80]

        for item in items:
            key = normalize(item.content)
            content_counts[key] = content_counts.get(key, 0) + 1

        # Attach recurrence counts to items
        for item in items:
            key = normalize(item.content)
            item.recurrence_count = content_counts.get(key, 1)

        return items

    def _get_current_handoff_path(self, terminal_id: str) -> Path | None:
        """Find the current session's handoff file.

        Handoff files are stored at ~/.claude/state/handoff/ using two possible
        naming conventions:
        - console_{terminal_id}_handoff.json (legacy/convention)
        - {hostname}-{pid}_handoff.json (StateManager format)

        The terminal_id parameter may be in either format.
        """
        state_base = Path.home() / ".claude" / "state" / "handoff"
        if not state_base.exists():
            return None

        # Normalize: strip console_ prefix if present to get the raw ID
        raw_id = terminal_id
        if terminal_id.startswith("console_"):
            raw_id = terminal_id[8:]

        # Try both naming patterns
        candidates = [
            state_base / f"console_{terminal_id}_handoff.json",
            state_base / f"{terminal_id}_handoff.json",
        ]
        # Also try with stripped console_ prefix
        if raw_id != terminal_id:
            candidates.extend([
                state_base / f"console_{raw_id}_handoff.json",
                state_base / f"{raw_id}_handoff.json",
            ])

        for handoff_path in candidates:
            if handoff_path.exists():
                return handoff_path

        # Try glob patterns as last resort
        for pattern in [f"console_{terminal_id}_*handoff*.json", f"{terminal_id}_*handoff*.json"]:
            for p in state_base.glob(pattern):
                return p
        return None

    def _get_prior_transcript_path(self, handoff_path: Path) -> Path | None:
        """Extract prior session transcript path from handoff file.

        The handoff file contains resume_snapshot.transcript_path which points
        to the prior session's transcript JSONL.
        """
        try:
            with open(handoff_path) as f:
                data = json.load(f)
            transcript_path_str = data.get("resume_snapshot", {}).get("transcript_path")
            if transcript_path_str:
                path = Path(transcript_path_str)
                if path.exists():
                    return path
        except (OSError, json.JSONDecodeError, PermissionError):
            pass
        return None

    def _scan_prior_transcripts(
        self, transcript_path: Path, terminal_id: str, max_chain_depth: int = 10
    ) -> list[SessionOutcomeItem]:
        """Scan prior session transcripts by following the handoff chain.

        Each session's handoff file (at ~/.claude/state/handoff/) contains
        resume_snapshot.transcript_path pointing to the prior session's transcript.
        This forms a linked list we can follow to scan all prior transcripts.

        Args:
            transcript_path: Current session's transcript path (start of chain)
            terminal_id: Terminal identifier for finding handoff files
            max_chain_depth: Maximum number of prior sessions to scan

        Returns:
            List of detected SessionOutcomeItem from prior sessions
        """
        items: list[SessionOutcomeItem] = []

        # Find the handoff file that references the current transcript.
        # This works for active sessions (no handoff yet for current terminal) because
        # it scans ALL handoff files looking for one whose transcript_path matches.
        # Falls back to terminal_id-based lookup if no matching handoff found.
        handoff_path = self._find_handoff_referencing(transcript_path)
        if not handoff_path and terminal_id:
            handoff_path = self._get_current_handoff_path(terminal_id)
        if not handoff_path:
            return items

        # Follow the chain
        session_age = 1
        visited: set[str] = set()

        while session_age <= max_chain_depth:
            prior_transcript = self._get_prior_transcript_path(handoff_path)
            if not prior_transcript or prior_transcript in visited:
                break
            visited.add(str(prior_transcript.resolve()))

            # Scan this prior transcript
            prior_items = self._scan_transcript(prior_transcript, session_age=session_age)
            items.extend(prior_items)

            # Move to next in chain - find the prior session's handoff file
            # The prior session's terminal_id is embedded in its handoff filename
            # We need to find any handoff file that references this transcript as its source
            handoff_path = self._find_handoff_referencing(prior_transcript)
            if not handoff_path:
                break

            session_age += 1

        return items

    def _find_handoff_referencing(self, transcript_path: Path) -> Path | None:
        """Find handoff file that has transcript_path as its source (prior session)."""
        state_base = Path.home() / ".claude" / "state" / "handoff"
        if not state_base.exists():
            return None
        transcript_str = str(transcript_path)
        for handoff_file in state_base.glob("console_*_handoff.json"):
            try:
                with open(handoff_file) as f:
                    data = json.load(f)
                if data.get("resume_snapshot", {}).get("transcript_path") == transcript_str:
                    return handoff_file
            except (OSError, json.JSONDecodeError, PermissionError):
                continue
        return None

    def _scan_prior_tldrs(self, terminal_id: str | None) -> list[SessionOutcomeItem]:
        """Scan prior session TLDR summaries for open items.

        Prior session summaries are written by SessionEnd_tldr.py hook and stored
        in terminal-scoped state directories with an 'open_items' field.

        NOTE: This method scans TLDR summaries which contain aggregated open_items.
        For full transcript scanning, use _scan_prior_transcripts() which follows
        the handoff chain to scan actual conversation content.

        Args:
            terminal_id: Terminal identifier for finding state files

        Returns:
            List of detected SessionOutcomeItem from prior sessions
        """
        items: list[SessionOutcomeItem] = []

        if not terminal_id:
            return items

        # Find prior TLDR/state files for this terminal
        state_base = Path.home() / ".claude" / "hooks" / "state"
        if not state_base.exists():
            return items

        # Find all tldr files for this terminal
        tldr_files = sorted(
            state_base.glob(f"SessionEnd_tldr_{terminal_id}_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        # Process up to 5 most recent prior sessions
        for tldr_file in tldr_files[:5]:
            try:
                with open(tldr_file) as f:
                    tldr_data = json.load(f)
            except (OSError, json.JSONDecodeError, PermissionError):
                continue

            # Extract open_items from TLDR
            open_items = tldr_data.get("open_items", [])
            if not open_items:
                continue

            # Session age: older files = higher age
            session_age = 1  # Default for prior sessions

            for item in open_items:
                if isinstance(item, str) and len(item.strip()) >= 10:
                    items.append(
                        SessionOutcomeItem(
                            category="identified_task",
                            content=item.strip(),
                            turn_number=0,  # No turn number for prior session items
                            session_age=session_age,
                            confidence=0.75,  # Prior session items have reasonable confidence
                            source="tldr",
                        )
                    )
                elif isinstance(item, dict):
                    content = item.get("content", "") or item.get("text", "")
                    if content and len(content) >= 10:
                        items.append(
                            SessionOutcomeItem(
                                category="identified_task",
                                content=content,
                                turn_number=0,
                                session_age=session_age,
                                confidence=item.get("confidence", 0.75),
                                source="tldr",
                            )
                        )

        return items

    def _deduplicate(self, items: list[SessionOutcomeItem]) -> list[SessionOutcomeItem]:
        """Remove duplicate items based on content similarity.

        Args:
            items: List of items to deduplicate

        Returns:
            Deduplicated list
        """
        if not items:
            return items

        # Normalize content for comparison
        def normalize(content: str) -> str:
            return re.sub(r"[^\w\s]", "", content.lower())[:80]

        seen: dict[str, SessionOutcomeItem] = {}
        result: list[SessionOutcomeItem] = []

        for item in items:
            key = normalize(item.content)
            if key not in seen:
                seen[key] = item
                result.append(item)
            else:
                # Keep the one with higher confidence, but preserve highest recurrence_count
                existing = seen[key]
                if item.confidence > existing.confidence:
                    existing.recurrence_count = max(
                        existing.recurrence_count, item.recurrence_count
                    )
                    seen[key] = item
                    # Update in result list
                    for i, r in enumerate(result):
                        if normalize(r.content) == key:
                            result[i] = item
                            break
                else:
                    # Keep existing but update recurrence if higher
                    existing.recurrence_count = max(
                        existing.recurrence_count, item.recurrence_count
                    )

        return result


# Convenience function
def detect_session_outcomes(
    transcript_path: Path | None,
    terminal_id: str | None = None,
    project_root: Path | None = None,
) -> SessionOutcomeResult:
    """
    Quick session outcome detection.

    Args:
        transcript_path: Path to current session transcript
        terminal_id: Terminal identifier for prior session lookup
        project_root: Project root directory

    Returns:
        SessionOutcomeResult with detected items
    """
    detector = SessionOutcomeDetector(project_root)
    return detector.detect(transcript_path, terminal_id)

```


### __lib/state.py

```python
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timezone
import json

from .util import atomic_write_json


@dataclass
class RunState:
    skill: str = "gto_v2"
    run_id: str = ""
    phase: str = "initialized"
    verification_required: bool = False
    verification_status: str = "pending"
    current_target: str | None = None
    git_sha: str | None = None
    last_artifact: str | None = None
    expected_artifacts: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "skill": self.skill,
            "run_id": self.run_id,
            "phase": self.phase,
            "verification_required": self.verification_required,
            "verification_status": self.verification_status,
            "current_target": self.current_target,
            "git_sha": self.git_sha,
            "last_artifact": self.last_artifact,
            "expected_artifacts": self.expected_artifacts,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()


def load_state(path: Path) -> RunState:
    if not path.exists():
        return RunState()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return RunState(
            skill=data.get("skill", "gto_v2"),
            run_id=data.get("run_id", ""),
            phase=data.get("phase", "initialized"),
            verification_required=data.get("verification_required", False),
            verification_status=data.get("verification_status", "pending"),
            current_target=data.get("current_target"),
            git_sha=data.get("git_sha"),
            last_artifact=data.get("last_artifact"),
            expected_artifacts=data.get("expected_artifacts", []),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )
    except (json.JSONDecodeError, KeyError):
        return RunState()


def save_state(path: Path, state: RunState) -> None:
    state.touch()
    atomic_write_json(path, state.to_dict())


def sync_to_execution_state(state: RunState, artifacts_dir: Path) -> None:
    """Write execution-state.json for the skill-guard contract runtime.

    Writes atomically to {artifacts_base}/{terminal_id}/execution-state.json.
    This enables the execution runtime to track phase and artifact completion
    independently of GTO's own run_state.json.
    """
    exec_state = {
        "run_id": state.run_id,
        "skill_name": "gto_v2",
        "contract_type": "workflow-execution",
        "phase": state.phase,
        "status": "active" if state.phase != "completed" else "complete",
        "terminal_id": artifacts_dir.name,
        "created_at": state.created_at,
        "updated_at": state.updated_at,
        "required_artifacts": [
            str(artifacts_dir / "outputs" / "artifact.json"),
        ],
        "completed_artifacts": [state.last_artifact] if state.last_artifact else [],
        "missing_requirements": [],
        "allowed_tools_now": [
            "Bash", "Read", "Grep", "Glob", "AskUserQuestion",
            "Skill", "Agent", "WebSearch", "WebFetch", "Write",
            "Edit", "Task",
        ],
        "blocked_tools": [],
    }
    exec_path = artifacts_dir.parent / "execution-state.json"
    tmp = exec_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(exec_state, indent=2, ensure_ascii=False), encoding="utf-8")
    if exec_path.exists():
        exec_path.unlink()
    tmp.rename(exec_path)

```


### __lib/stuckness.py

```python
"""Session velocity / stuckness detection — detects repeated goals across sessions.

Reads the session chain to detect when the same goal or carryover finding
appears across multiple consecutive sessions, indicating the user may be stuck.
"""
from __future__ import annotations

from pathlib import Path

from ..models import EvidenceRef, Finding
from .session_goal_detector import SessionGoalDetector


def detect_stuckness(
    root: Path,
    chain: list[str],
    carryover_findings: list[Finding],
    terminal_id: str = "",
    session_id: str = "",
    git_sha: str | None = None,
) -> list[Finding]:
    """Detect stuckness from repeated goals or carryover across sessions.

    Returns findings if the same goal appears in 3+ consecutive sessions
    or the same carryover finding persists across runs.
    """
    if not chain or len(chain) < 2:
        return []

    findings: list[Finding] = []

    # Check for repeated goals across sessions
    detector = SessionGoalDetector(root)
    goals: list[str | None] = []
    for transcript_path in chain:
        try:
            result = detector.detect_goal_from_chain([transcript_path])
            goals.append(result.session_goal)
        except Exception:
            goals.append(None)

    # Count consecutive identical non-None goals
    non_none_goals = [g for g in goals if g]
    if len(non_none_goals) >= 2:
        # Check if the last 3+ goals are the same
        recent = non_none_goals[-3:] if len(non_none_goals) >= 3 else non_none_goals
        if len(set(g.lower().strip()[:50] for g in recent)) == 1 and len(recent) >= 2:
            goal_text = recent[0]
            findings.append(
                Finding(
                    id="STUCK-001",
                    title=f"Same goal across {len(recent)} sessions — may be stuck",
                    description=(
                        f"Goal \"{goal_text[:80]}\" has appeared in {len(recent)} consecutive sessions. "
                        f"Consider escalating approach, breaking the task down differently, "
                        f"or running a diagnostic skill."
                    ),
                    source_type="detector",
                    source_name="stuckness_detector",
                    domain="session",
                    gap_type="stuckness",
                    severity="high",
                    evidence_level="verified",
                    action="recover",
                    priority="high",
                    terminal_id=terminal_id,
                    session_id=session_id,
                    git_sha=git_sha,
                    evidence=[
                        EvidenceRef(
                            kind="stuckness",
                            value=f"{len(recent)} sessions",
                            detail=goal_text[:100] if goal_text else "",
                        ),
                    ],
                )
            )

    # Check for carryover findings that have been around for many runs
    recurring_carryover = [
        f for f in carryover_findings
        if f.metadata.get("_carry_count", 0) >= 3
    ]
    if recurring_carryover:
        ids = [f.id for f in recurring_carryover]
        titles = [f.title[:60] for f in recurring_carryover]
        findings.append(
            Finding(
                id="STUCK-CARRYOVER-001",
                title=f"{len(recurring_carryover)} findings carried 3+ runs without resolution",
                description=(
                    f"Persistent findings that haven't been resolved: {', '.join(titles[:5])}. "
                    f"Consider running a targeted skill or changing approach."
                ),
                source_type="detector",
                source_name="stuckness_detector",
                domain="session",
                gap_type="stuckness",
                severity="medium",
                evidence_level="verified",
                action="recover",
                priority="medium",
                terminal_id=terminal_id,
                session_id=session_id,
                git_sha=git_sha,
                evidence=[
                    EvidenceRef(
                        kind="carryover_stuckness",
                        value=", ".join(ids[:5]),
                        detail=f"{len(recurring_carryover)} recurring carryover findings",
                    ),
                ],
            )
        )

    return findings

```


### __lib/targeting.py

```python
from __future__ import annotations


def resolve_target(
    explicit_target: str | None,
    conversation_hint: str | None,
    artifact_target: str | None,
) -> str:
    for candidate in (explicit_target, conversation_hint, artifact_target):
        if candidate and candidate.strip():
            return candidate.strip()
    return "current-project"

```


### __lib/transcript.py

```python
"""Shared transcript reader handling all Claude Code JSONL formats.

Claude Code stores transcripts in three formats:
- Simple: {"role": "user", "content": "text"}
- Old:    {"sender": "user", "text": "text"} or {"sender": "user", "content": "text"}
- New:    {"type": "user", "message": {"content": "text" | [{"type":"text","text":"..."}]}}

All 6 transcript-reading call sites in GTO previously used only the simple format.
This module handles all three, adapted from RNS chain.py.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class TranscriptTurn:
    role: str  # "user" | "assistant"
    content: str
    turn_number: int  # 1-based line number in JSONL


def read_turns(
    transcript_path: Path,
    *,
    max_age_days: int | None = None,
) -> list[TranscriptTurn]:
    """Read transcript JSONL handling all Claude Code formats.

    Args:
        transcript_path: Path to transcript JSONL file.
        max_age_days: If set, skip files older than this many days.

    Returns:
        List of TranscriptTurn with role, content, and 1-based turn_number.
    """
    if not transcript_path.exists():
        return []

    if max_age_days is not None:
        try:
            mtime = os.path.getmtime(transcript_path)
            age_days = (datetime.now(timezone.utc).timestamp() - mtime) / 86400
            if age_days > max_age_days:
                return []
        except OSError:
            return []

    turns: list[TranscriptTurn] = []
    try:
        with open(transcript_path, encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, start=1):
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                role, content = _extract_role_content(entry)
                if role and content:
                    turns.append(TranscriptTurn(
                        role=role,
                        content=content,
                        turn_number=line_num,
                    ))
    except (OSError, PermissionError):
        pass

    return turns


def _extract_role_content(entry: dict) -> tuple[str | None, str]:
    """Extract (role, content) from a single JSONL entry.

    Returns (None, "") for non-message entries (system, tool_use, etc).
    """
    # New format: {"type": "user"|"assistant", "message": {"content": ...}}
    etype = entry.get("type", "")
    if etype in ("user", "assistant"):
        msg = entry.get("message", {})
        if not isinstance(msg, dict):
            return None, ""
        raw = msg.get("content", "")
        text = _flatten_content(raw)
        return etype, text

    # Old format: {"sender": "user"|"assistant", "text": "..."}
    sender = entry.get("sender", "")
    if sender in ("user", "assistant"):
        text = entry.get("text", "") or entry.get("content", "")
        if isinstance(text, list):
            text = _flatten_content(text)
        return sender, str(text)

    # Simple format: {"role": "user"|"assistant", "content": "..."}
    role = entry.get("role", "")
    if role in ("user", "assistant"):
        raw = entry.get("content", "")
        text = _flatten_content(raw)
        return role, text

    return None, ""


def _flatten_content(raw: str | list) -> str:
    """Flatten content that may be a string or list of content blocks."""
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list):
        return " ".join(
            block.get("text", "")
            for block in raw
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return str(raw) if raw else ""


_FILE_EDIT_TOOLS = frozenset({"Edit", "Write", "NotebookEdit"})


def extract_edited_files(transcript_path: Path, root: Path | None = None) -> list[Path]:
    """Extract unique file paths from Edit/Write/NotebookEdit tool calls in a transcript.

    Scans assistant turns for tool_use blocks targeting file-editing tools,
    returning deduplicated absolute paths. If root is given, only files under
    root are included.

    Args:
        transcript_path: Path to transcript JSONL file.
        root: Optional project root to filter results.

    Returns:
        Deduplicated list of edited file paths, in order of first appearance.
    """
    if not transcript_path.exists():
        return []

    seen: set[str] = set()
    files: list[Path] = []

    try:
        with open(transcript_path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # New format: assistant message with content blocks
                if entry.get("type") != "assistant":
                    continue
                msg = entry.get("message", {})
                content = msg.get("content", [])
                if not isinstance(content, list):
                    continue
                for block in content:
                    if not isinstance(block, dict):
                        continue
                    if block.get("type") != "tool_use":
                        continue
                    if block.get("name") not in _FILE_EDIT_TOOLS:
                        continue
                    fp = (block.get("input") or {}).get("file_path", "")
                    if not fp or fp in seen:
                        continue
                    resolved = Path(fp).resolve()
                    if root is not None:
                        try:
                            resolved.relative_to(root)
                        except ValueError:
                            continue
                    seen.add(fp)
                    files.append(resolved)
    except (OSError, PermissionError):
        pass

    return files

```


### __lib/util.py

```python
from __future__ import annotations

from pathlib import Path
import json
import os
import tempfile


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def atomic_write_json(path: Path, payload: dict | list) -> None:
    atomic_write_text(path, json.dumps(payload, indent=2, ensure_ascii=False))

```


### __lib/verification_debt.py

```python
"""Verification debt detector — detects edits without test verification.

Scans transcript for Edit/Write tool calls that weren't followed by a
test execution (pytest, unittest) within a reasonable window. This flags
code changes that lack regression proof.

What it detects:
- File edits with no test run in the surrounding N turns
- Multiple edits to test files (test fixes) without a re-run
- Edits to production code with no test invocation at all

What it does NOT detect:
- Edits to config/docs/non-code files (those don't need tests)
- Edits where the user explicitly says "no test needed"
"""
from __future__ import annotations

import json
from pathlib import Path

from ..models import EvidenceRef, Finding

# Tools that modify files
_EDIT_TOOLS = frozenset({"Edit", "Write"})

# Bash commands that count as test verification
_TEST_COMMAND_PATTERNS = ("pytest", "unittest", "test", "npm test", "cargo test")

# Window of turns after an edit to look for test verification
_VERIFICATION_WINDOW = 40

# File patterns that don't need test verification
_SKIP_SUFFIXES = (".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini", ".rst")

_MAX_FINDINGS = 50


def detect_verification_debt(
    transcript_path: Path | None,
    terminal_id: str = "",
    session_id: str = "",
    git_sha: str | None = None,
) -> list[Finding]:
    """Detect edits that weren't followed by test verification.

    Scans transcript for file edits, then checks if a test command
    was run within a window of turns after the edit.

    Returns:
        Findings for unverified edits.
    """
    if not transcript_path or not transcript_path.exists():
        return []

    # Parse all entries to find edit events and test runs
    entries: list[dict] = []
    try:
        with open(transcript_path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except (OSError, PermissionError):
        return []

    # Track edit events and test run positions
    edit_events: list[dict] = []  # {file_path, line_number}
    test_run_positions: list[int] = []  # line numbers where test commands ran

    for line_idx, entry in enumerate(entries):
        # Find test runs in Bash tool results
        if entry.get("type") == "assistant":
            msg = entry.get("message", {})
            content = msg.get("content", [])
            if not isinstance(content, list):
                continue
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") != "tool_use":
                    continue
                if block.get("name") == "Bash":
                    cmd = (block.get("input") or {}).get("command", "")
                    if any(p in cmd.lower() for p in _TEST_COMMAND_PATTERNS):
                        test_run_positions.append(line_idx)

                # Find file edits
                if block.get("name") in _EDIT_TOOLS:
                    fp = (block.get("input") or {}).get("file_path", "")
                    if fp and not fp.endswith(_SKIP_SUFFIXES):
                        edit_events.append({"file_path": fp, "line_idx": line_idx})

    if not edit_events:
        return []

    # Check which edits have no test verification within the window
    unverified_edits: list[dict] = []
    for edit in edit_events:
        edit_pos = edit["line_idx"]
        # Look for a test run within the window after this edit
        has_verification = any(
            test_pos > edit_pos and test_pos <= edit_pos + _VERIFICATION_WINDOW
            for test_pos in test_run_positions
        )
        if not has_verification:
            unverified_edits.append(edit)

    if not unverified_edits:
        return []

    # Deduplicate by file path (keep last edit per file)
    seen_files: dict[str, dict] = {}
    for edit in unverified_edits:
        seen_files[edit["file_path"]] = edit

    # Limit to prevent noise
    files_to_report = list(seen_files.keys())[:_MAX_FINDINGS]
    extra = len(seen_files) - _MAX_FINDINGS

    file_list = ", ".join(f.split("/")[-1] for f in files_to_report)
    extra_text = f" (+{extra} more)" if extra > 0 else ""

    return [
        Finding(
            id="VERIFY-001",
            title=f"{len(seen_files)} file edit(s) without test verification",
            description=(
                f"Code edits detected without a subsequent test run: "
                f"{file_list}{extra_text}. "
                f"Consider running tests to verify these changes."
            ),
            source_type="detector",
            source_name="verification_debt_detector",
            domain="tests",
            gap_type="missingtests",
            severity="medium",
            evidence_level="verified",
            action="prevent",
            priority="medium",
            scope="local",
            terminal_id=terminal_id,
            session_id=session_id,
            git_sha=git_sha,
            evidence=[
                EvidenceRef(
                    kind="transcript_analysis",
                    value="unverified_edits",
                    detail=file_list[:200],
                ),
            ],
        )
    ]

```


### __lib/verify.py

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..models import GTOArtifact


def verify_artifact(artifact_path: Path) -> dict[str, Any]:
    """Verify a GTO artifact file has the required structure.

    Returns a dict with 'valid' (bool) and 'errors' (list of strings).
    """
    result: dict[str, Any] = {"valid": True, "errors": []}

    if not artifact_path.exists():
        result["valid"] = False
        result["errors"].append(f"Artifact file not found: {artifact_path}")
        return result

    try:
        data = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        result["valid"] = False
        result["errors"].append(f"Cannot parse artifact JSON: {exc}")
        return result

    required_fields = [
        "artifact_version",
        "mode",
        "terminal_id",
        "session_id",
        "target",
        "findings",
        "machine_output",
        "human_output",
        "verification",
        "coverage",
    ]

    for field in required_fields:
        if field not in data:
            result["valid"] = False
            result["errors"].append(f"Missing required field: {field}")

    # Verify machine_output has RNS format lines
    machine = data.get("machine_output", [])
    if isinstance(machine, list):
        has_rns_d = any(isinstance(line, str) and line.startswith("RNS|D|") for line in machine)
        has_rns_z = any(isinstance(line, str) and line.startswith("RNS|Z|") for line in machine)
        has_findings = len(data.get("findings", [])) > 0
        if not has_rns_d and has_findings:
            result["valid"] = False
            result["errors"].append("machine_output missing RNS|D| domain header")
        if not has_rns_z:
            result["valid"] = False
            result["errors"].append("machine_output missing RNS|Z| terminator")

    return result


def verify_state(state_path: Path) -> dict[str, Any]:
    """Verify run state has completed all expected phases."""
    result: dict[str, Any] = {"valid": True, "errors": []}

    if not state_path.exists():
        result["valid"] = False
        result["errors"].append(f"State file not found: {state_path}")
        return result

    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        result["valid"] = False
        result["errors"].append(f"Cannot parse state JSON: {exc}")
        return result

    if data.get("phase") != "completed":
        result["valid"] = False
        result["errors"].append(f"State phase is '{data.get('phase')}', expected 'completed'")

    return result

```


### __lib/workflow_hygiene.py

```python
"""Workflow hygiene detector — detects uncommitted changes and dirty state.

Checks git working tree for uncommitted modifications that indicate
work-in-progress that hasn't been persisted. This is a gap detector
because uncommitted work is at risk of loss.

What it detects:
- Modified tracked files (unstaged or staged)
- Deleted tracked files
- Untracked files in key directories (packages/, .claude/)

What it does NOT detect:
- Stashed changes (git stash list)
- Unpushed commits (that's a separate concern)
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from ..models import EvidenceRef, Finding

# Maximum findings to prevent noise from large untracked sets
_MAX_FINDINGS = 5

# Directories where untracked files are noteworthy
_NOTEWORTHY_DIRS = ("packages/", ".claude/hooks/", ".claude/skills/")


def detect_workflow_hygiene(
    root: Path,
    terminal_id: str = "",
    session_id: str = "",
    git_sha: str | None = None,
) -> list[Finding]:
    """Check git working tree for uncommitted changes.

    Returns:
        Findings for uncommitted work in the working tree.
    """
    if not (root / ".git").exists():
        return []

    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=str(root),
        )
        if result.returncode != 0:
            return []
        porcelain = result.stdout.strip()
    except (subprocess.TimeoutExpired, OSError):
        return []

    if not porcelain:
        return []

    lines = porcelain.splitlines()

    # Categorize changes
    modified: list[str] = []
    deleted: list[str] = []
    untracked_noteworthy: list[str] = []

    for line in lines:
        if len(line) < 4:
            continue
        status = line[:2]
        filepath = line[3:].strip()

        # Untracked
        if "??" in status:
            if any(filepath.startswith(d) for d in _NOTEWORTHY_DIRS):
                untracked_noteworthy.append(filepath)
            continue

        # Deleted
        if "D" in status:
            deleted.append(filepath)
            continue

        # Modified (staged or unstaged)
        if "M" in status or "A" in status or "R" in status or "C" in status:
            modified.append(filepath)

    findings: list[Finding] = []

    if modified:
        file_list = ", ".join(modified[:_MAX_FINDINGS])
        extra = f" (+{len(modified) - _MAX_FINDINGS} more)" if len(modified) > _MAX_FINDINGS else ""
        findings.append(
            Finding(
                id="WORKFLOW-001",
                title=f"{len(modified)} uncommitted modified file(s)",
                description=f"Working tree has modified files not yet committed: {file_list}{extra}",
                source_type="detector",
                source_name="workflow_hygiene_detector",
                domain="git",
                gap_type="techdebt",
                severity="low",
                evidence_level="verified",
                action="recover",
                priority="low",
                scope="local",
                terminal_id=terminal_id,
                session_id=session_id,
                git_sha=git_sha,
                evidence=[
                    EvidenceRef(kind="git_status", value="modified", detail=file_list[:200]),
                ],
            )
        )

    if deleted:
        file_list = ", ".join(deleted[:_MAX_FINDINGS])
        findings.append(
            Finding(
                id="WORKFLOW-002",
                title=f"{len(deleted)} deleted file(s) not committed",
                description=f"Files deleted from working tree not yet committed: {file_list}",
                source_type="detector",
                source_name="workflow_hygiene_detector",
                domain="git",
                gap_type="techdebt",
                severity="medium",
                evidence_level="verified",
                action="recover",
                priority="medium",
                scope="local",
                terminal_id=terminal_id,
                session_id=session_id,
                git_sha=git_sha,
                evidence=[
                    EvidenceRef(kind="git_status", value="deleted", detail=file_list[:200]),
                ],
            )
        )

    if untracked_noteworthy:
        file_list = ", ".join(untracked_noteworthy[:_MAX_FINDINGS])
        findings.append(
            Finding(
                id="WORKFLOW-003",
                title=f"{len(untracked_noteworthy)} untracked file(s) in key directories",
                description=f"Untracked files in packages/ or .claude/: {file_list}",
                source_type="detector",
                source_name="workflow_hygiene_detector",
                domain="git",
                gap_type="techdebt",
                severity="low",
                evidence_level="verified",
                action="prevent",
                priority="low",
                scope="local",
                terminal_id=terminal_id,
                session_id=session_id,
                git_sha=git_sha,
                evidence=[
                    EvidenceRef(kind="git_status", value="untracked", detail=file_list[:200]),
                ],
            )
        )

    return findings

```


### agents/__init__.py

```python
from __future__ import annotations

import json
from pathlib import Path

from ..models import Finding, EvidenceRef, AgentResult


def parse_agent_result(path: Path, agent_name: str) -> AgentResult:
    """Read and parse an agent result file into an AgentResult.

    Handles both bare JSON arrays ``[{...}, ...]`` and wrapped
    ``{"findings": [...], "notes": "..."}`` formats.
    """
    if not path.exists():
        return AgentResult(agent=agent_name, findings=[], success=False)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return AgentResult(agent=agent_name, findings=[], success=False)

    if isinstance(data, list):
        items, notes = data, ""
    elif isinstance(data, dict):
        items, notes = data.get("findings", []), data.get("notes", "")
    else:
        return AgentResult(agent=agent_name, findings=[], success=False)

    findings: list[Finding] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("status") == "rejected":
            continue
        evidence = [
            EvidenceRef(kind=e.get("kind", ""), value=e.get("value", ""))
            for e in item.get("evidence", [])
            if isinstance(e, dict)
        ]
        findings.append(
            Finding(
                id=item.get("id", f"{agent_name[:4].upper()}-???"),
                title=item.get("title", "Agent finding"),
                description=item.get("description", ""),
                source_type="agent",
                source_name=agent_name,
                domain=item.get("domain", "other"),
                gap_type=item.get("gap_type", "unknown"),
                severity=item.get("severity", "medium"),
                evidence_level=item.get("evidence_level", "unverified"),
                action=item.get("action", "recover"),
                priority=item.get("priority", "medium"),
                file=item.get("file"),
                line=item.get("line"),
                effort=item.get("effort"),
                unverified=item.get("unverified", True),
                evidence=evidence,
            )
        )

    return AgentResult(
        agent=agent_name,
        findings=findings,
        raw_notes=notes if isinstance(data, dict) else "",
        success=True,
    )

```


### agents/action_normalizer.py

```python
"""Action Normalizer Agent — converts findings into canonical RNS action items.

Ensures each finding has valid domain, severity, action, priority, effort,
and evidence_level fields suitable for RNS rendering. Runs as a Claude Code subagent.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import parse_agent_result
from ..models import AgentResult, Finding


def write_handoff(
    path: Path,
    findings: list[Finding],
) -> None:
    """Write findings for the action normalizer agent."""
    handoff = {
        "role": "action_normalizer",
        "findings": [f.to_dict() for f in findings],
        "output_path": str(path.parent / "action_normalizer_result.json"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(handoff, indent=2), encoding="utf-8")


def read_result(path: Path) -> AgentResult:
    """Read the action normalizer result."""
    return parse_agent_result(path, "action_normalizer")

```


### agents/domain_analyzer.py

```python
"""Domain Analyzer Agent — enriches findings with project domain context.

Reads initial findings from deterministic detectors and session analysis,
then enriches them with domain-specific health assessments. The agent runs
as a Claude Code subagent (spawned by the LLM following SKILL.md instructions)
and writes structured JSON to the artifact directory.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import parse_agent_result
from ..models import AgentResult, Finding


def write_handoff(
    path: Path,
    findings: list[Finding],
    project_context: dict,
) -> None:
    """Write findings + project context for the domain analyzer agent."""
    handoff = {
        "role": "domain_analyzer",
        "project": project_context,
        "findings": [f.to_dict() for f in findings],
        "output_path": str(path.parent / "domain_analyzer_result.json"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(handoff, indent=2), encoding="utf-8")


def read_result(path: Path) -> AgentResult:
    """Read the domain analyzer result."""
    return parse_agent_result(path, "domain_analyzer")

```


### agents/findings_reviewer.py

```python
"""Findings Reviewer Agent — validates findings for quality and accuracy.

Reviews findings for missing evidence, duplication, false positives,
and severity misclassification. Runs as a Claude Code subagent.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import parse_agent_result
from ..models import AgentResult, Finding


def write_handoff(
    path: Path,
    findings: list[Finding],
) -> None:
    """Write findings for the reviewer agent."""
    handoff = {
        "role": "findings_reviewer",
        "findings": [f.to_dict() for f in findings],
        "output_path": str(path.parent / "findings_reviewer_result.json"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(handoff, indent=2), encoding="utf-8")


def read_result(path: Path) -> AgentResult:
    """Read the findings reviewer result."""
    return parse_agent_result(path, "findings_reviewer")

```


### agents/gap_reviewer.py

```python
"""Gap Reviewer Agent — structured gap-to-opportunity review with context injection.

Receives pre-populated detector evidence (findings, changed files, session outcomes,
absence signals) and produces a structured FACT/INFERENCE/UNKNOWN/RECOMMENDATION review
plus any new gaps discovered during the review.

This is the "adaptive" layer: one stable prompt lens + deterministic context injection,
so the review is automatically tailored to each session's actual state without N
domain-specific prompt variants.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import parse_agent_result
from ..models import AgentResult, EvidenceRef, Finding


def write_handoff(
    path: Path,
    findings: list[Finding],
    session_outcomes: list[dict] | None = None,
    changed_files: list[str] | None = None,
    session_context: dict | None = None,
    detectors_ran: list[str] | None = None,
    detectors_empty: list[str] | None = None,
) -> None:
    """Write context-enriched handoff for the gap reviewer agent.

    Args:
        path: Handoff file path (result path derived from sibling).
        findings: Current findings from the deterministic pipeline.
        session_outcomes: Session outcome items (from session_outcome_detector).
        changed_files: Files changed since last GTO run.
        session_context: Terminal/session/git metadata.
        detectors_ran: Names of detectors that produced findings.
        detectors_empty: Names of detectors that ran but found nothing (absence signals).
    """
    detected_facts: list[dict[str, str]] = []

    for f in findings:
        fact = {"claim": f.title, "source": f.source_name or "detector"}
        if f.file:
            fact["source"] += f" @ {f.file}"
            if f.line:
                fact["source"] += f":{f.line}"
        detected_facts.append(fact)

    if session_outcomes:
        for item in session_outcomes:
            detected_facts.append({
                "claim": f"Session outcome: {item.get('content', '')}",
                "source": f"session_outcome_detector ({item.get('category', 'unknown')})",
            })

    if changed_files:
        for cf in changed_files[:20]:
            detected_facts.append({"claim": f"File changed: {cf}", "source": "changelog_detector"})

    signals_absent: list[dict[str, str]] = []
    for det in (detectors_empty or []):
        signals_absent.append({
            "detector": det,
            "result": "no findings produced",
        })

    handoff = {
        "role": "gap_reviewer",
        "detected_facts": detected_facts,
        "signals_absent": signals_absent,
        "session_context": session_context or {},
        "findings": [f.to_dict() for f in findings],
        "detectors_ran": detectors_ran or [],
        "output_path": str(path.parent / "gap_reviewer_result.json"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(handoff, indent=2), encoding="utf-8")


def read_result(path: Path) -> AgentResult:
    """Read the gap reviewer result.

    The reviewer outputs both a structured review and optional new findings.
    We extract findings from the "findings" array; the review text is preserved
    in raw_notes for display.
    """
    if not path.exists():
        return AgentResult(agent="gap_reviewer", findings=[], success=False)

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return AgentResult(agent="gap_reviewer", findings=[], success=False)

    if not isinstance(data, dict):
        return parse_agent_result(path, "gap_reviewer")

    review = data.get("review", {})
    notes_parts: list[str] = []
    for section in ("facts", "inferences", "unknowns", "recommendations"):
        items = review.get(section, [])
        if items:
            notes_parts.append(f"[{section.upper()}]")
            for item in items:
                if isinstance(item, dict):
                    notes_parts.append(f"- {item}")
                else:
                    notes_parts.append(f"- {item}")

    raw_notes = "\n".join(notes_parts)

    raw_findings = data.get("findings", [])
    if isinstance(raw_findings, list):
        findings: list[Finding] = []
        for item in raw_findings:
            if not isinstance(item, dict):
                continue
            if item.get("status") == "rejected":
                continue
            evidence = [
                EvidenceRef(kind=e.get("kind", ""), value=e.get("value", ""))
                for e in item.get("evidence", [])
                if isinstance(e, dict)
            ]
            findings.append(
                Finding(
                    id=item.get("id", "GAPR-???"),
                    title=item.get("title", "Gap reviewer finding"),
                    description=item.get("description", ""),
                    source_type="agent",
                    source_name="gap_reviewer",
                    domain=item.get("domain", "other"),
                    gap_type=item.get("gap_type", "unknown"),
                    severity=item.get("severity", "medium"),
                    evidence_level=item.get("evidence_level", "unverified"),
                    action=item.get("action", "recover"),
                    priority=item.get("priority", "medium"),
                    file=item.get("file"),
                    line=item.get("line"),
                    effort=item.get("effort"),
                    unverified=item.get("unverified", True),
                    evidence=evidence,
                )
            )
        return AgentResult(agent="gap_reviewer", findings=findings, success=True, raw_notes=raw_notes)

    return AgentResult(agent="gap_reviewer", findings=[], success=False, raw_notes=raw_notes)

```


### agents/prompts.py

```python
from __future__ import annotations

DOMAIN_ANALYZER_SYSTEM = """You are a domain-specific code gap analyzer. Your job is to find real, actionable gaps in the target codebase.

Rules:
- Only report gaps you have direct evidence for (file path, line number, or behavior)
- Classify each gap by domain: quality, tests, docs, security, performance, deps, git
- Assign severity: critical, high, medium, low
- Assign action: recover (fix existing bug), prevent (stop future regression), realize (new capability)
- Mark unverified=True if you inferred the gap without direct file evidence
- Output findings as JSON array

Schema per finding:
{
  "id": "AGENT-{domain}-{number}",
  "title": "short title",
  "description": "what's wrong and why it matters",
  "domain": "quality|tests|docs|security|performance|deps|git",
  "gap_type": "descriptive gap type",
  "severity": "critical|high|medium|low",
  "action": "recover|prevent|realize",
  "priority": "critical|high|medium|low",
  "file": "relative path or null",
  "line": line_number_or_null,
  "effort": "estimated effort like ~5min",
  "unverified": true_or_false,
  "evidence": [{"kind": "path|pattern|behavior", "value": "description"}]
}
"""

FINDINGS_REVIEWER_SYSTEM = """You are a findings quality reviewer. Your job is to validate and refine a list of code gap findings.

For each finding, evaluate:
1. Is the severity appropriate? (not over- or under-stated)
2. Is the action classification correct?
3. Is the domain assignment accurate?
4. Is there sufficient evidence?
5. Are there duplicates or near-duplicates?

Output a JSON array of validated findings with the same schema, plus:
- Add "review_notes" field with your assessment
- Change severity/priority if you disagree (explain in review_notes)
- Reject findings that lack evidence by setting status to "rejected"
- Keep at most 15 findings total, prioritized by severity
"""

ACTION_NORMALIZER_SYSTEM = """You are an action item normalizer. Your job is to convert raw findings into normalized action items.

Ensure each finding:
- Has a valid domain (quality, tests, docs, security, performance, deps, git, other)
- Has a valid severity (critical, high, medium, low)
- Has a valid action (recover, prevent, realize)
- Has a valid priority (critical, high, medium, low)
- Has a meaningful description (not just an ID or single word)
- Has effort estimate if missing (infer from severity: critical=~30min, high=~15min, medium=~5min, low=~2min)
- Has appropriate evidence_level (verified if file evidence exists, unverified otherwise)

Output the same JSON array with normalized fields.
"""

GAP_REVIEW_SYSTEM = """You are a gap-to-opportunity reviewer. You receive pre-populated detector evidence and produce a structured review.

You receive a handoff JSON with:
- detected_facts: concrete observations from deterministic detectors (findings, changed files, session outcomes)
- signals_absent: detectors that ran but found nothing (absence as evidence)
- session_context: terminal_id, session_id, git_sha, files edited this session

Your job is to produce a structured review in this exact format:

Return a JSON object with two fields:

1. "review": an object with these sections:
   - "facts": list of concrete observations grounded in the detector evidence. Each entry is {"claim": "...", "source": "detector_name or file:line"}
   - "inferences": list of hypotheses about failure modes or friction points. Each entry is {"hypothesis": "...", "confidence": "low|medium|high", "evidence": "what supports this"}
   - "unknowns": list of important questions that cannot be answered from the evidence. Each entry is {"question": "...", "why_it_matters": "..."}
   - "recommendations": list of specific next actions, ranked by impact. Produce as many as the evidence supports. Each entry is {"action": "...", "goal": "...", "assumption": "...", "rationale": "..."}

2. "findings": a JSON array of any NEW gaps you discovered that are NOT already in the input findings, following the standard finding schema:
   {"id": "GAPR-{domain}-{number}", "title": "...", "description": "...", "domain": "...", "gap_type": "...", "severity": "...", "action": "realize", "priority": "...", "evidence": [...]}

Rules:
- Do not duplicate findings already present in the input
- Prefer issues predictable from system structure (overlapping validators, mode flags, format constraints)
- Do not propose large refactors without a concrete pain point from the evidence
- Mark confidence honestly — do not inflate inferences to facts
- If the session was exploratory with no clear trajectory, say so rather than forcing predictions
- Frame recommendations as actions the user can take, not obligations

## Reasoning Failure Patterns to Detect

The following three patterns cause downstream failures. Actively look for them in the evidence:

### 1. Ambiguity Collapse (premature agreement)
What it looks like: The transcript shows a user question that was ambiguous or unverified, followed immediately by agreement or confirmation from the LLM before any verification was run.

Detection signal: Look for phrases like "You're right", "Makes sense", "Exactly" appearing in the SAME TURN as the question — not after evidence was gathered.

What to surface: A finding with domain=quality, gap_type="premature_agreement", action=recover. The finding should cite the ambiguous question and the unverified claim that followed it. Even if the claim turned out to be correct, the session skipped the verification step — that's the gap.

Rule: Don't claim the agreement was wrong. Claim the reasoning process skipped a step.

### 2. Stale Data Claims
What it looks like: The transcript or findings reference data (API docs, package versions, file timestamps, line numbers) that is plausibly stale — no freshness evidence accompanies the claim.

Detection signal: No timestamp, no cache age, no "as of" qualifier on data references. Cross-reference against the session transcript's `captured_at` or `git_sha`. If the referenced data was captured before a relevant change, it's stale.

What to surface: A finding with domain=quality, gap_type="stale_data_dependency", action=prevent. The finding should name the specific data reference and the gap in staleness verification.

### 3. Challenge Marker Contamination
What it looks like: Session markers or state identifiers from a PREVIOUS session persist into the current session's artifacts. Markers include: carryover.json IDs that don't match current detectors, handoff.json entries with stale git_sha, identity.json with session_id that doesn't match transcript sessionId.

Detection signal: Check if findings in carryover or handoff files have git_sha that differs from the current run's git_sha. Check if terminal_id in artifacts doesn't match the actual WT_SESSION terminal.

What to surface: A finding with domain=quality, gap_type="marker_staleness", action=recover. The finding should cite the specific artifact and the mismatched field.

These three patterns are systemic — they appear consistently across sessions and cause real downstream failures (false positive findings, missed gaps, incorrect routing). Surface them as findings when detected.

### 4. Unverified Implementation Claims
What it looks like: A gap finding is based on code inspection or stated capability, but the actual hook wiring, telemetry parsing, once-per-session state, hidden-context injection, or test coverage has not been verified against runtime evidence.

Detection signal: Finding cites a mechanism (hook, telemetry, state gate, context injection) without evidence that it actually fires, parses, gates, or injects. Look for absence of: hook execution logs, telemetry event traces, session-boundary state checks, test files covering the mechanism.

What to surface: A finding with domain=quality, gap_type="unverified_implementation_claim", action=recover. The finding should name the claimed mechanism and the missing verification step.

Rule: Code structure alone is not evidence of behavior. If the finding describes what a hook SHOULD do, it must also cite evidence of what it ACTUALLY does.
"""

SESSION_REVIEWER_SYSTEM = """You are a session outcome reviewer. Your job is to classify ambiguous transcript excerpts.

You receive a list of outcome candidates with surrounding context. For each candidate:
1. Read the surrounding context (5 turns before/after)
2. Classify as one of: "confirmed_deferral", "confirmed_open", "rejected" (incidental mention, not a deferral)
3. If confirmed, provide a clean content description

Output a JSON array:
[
  {
    "original_content": "...",
    "classification": "confirmed_deferral|confirmed_open|rejected",
    "content": "clean description if confirmed, null if rejected",
    "reason": "brief explanation"
  }
]

Key distinctions:
- "can be deleted later" -> confirmed_deferral (action deferred to future)
- "later versions of Python" -> rejected (incidental usage of temporal word)
- "let's skip that for now" -> confirmed_deferral (explicit deferral)
- "we should check that later" -> confirmed_deferral (action with temporal marker)
- "I used to work there later" -> rejected (temporal usage, not deferral)
"""

```


### agents/session_reviewer.py

```python
"""Session Reviewer Agent — reviews session outcomes for completion status.

Takes detected session outcomes (uncompleted goals, open questions, deferred items)
along with surrounding transcript context, and produces a filtered set where
goals that were actually completed during the session are marked as resolved.

This is the only gap where LLM judgment beats deterministic regex: distinguishing
"I want to build X" → assistant builds X → user confirms (completed)
from "I want to build X" → never addressed (genuine gap).
"""
from __future__ import annotations

import json
from pathlib import Path

from . import parse_agent_result
from ..models import AgentResult
from ..__lib.session_outcome_detector import SessionOutcomeItem


def write_handoff(
    path: Path,
    outcomes: list[SessionOutcomeItem],
    transcript_excerpts: list[dict[str, str]],
) -> None:
    """Write session outcomes + transcript context for the reviewer agent.

    Args:
        path: Handoff file path (result path derived from sibling).
        outcomes: Detected session outcome items to review.
        transcript_excerpts: Surrounding transcript context as
            [{"role": "user/assistant", "content": "..."}] pairs.
    """
    handoff = {
        "role": "session_reviewer",
        "outcomes": [
            {
                "category": item.category,
                "content": item.content,
                "confidence": item.confidence,
                "recurrence_count": item.recurrence_count,
                "session_age": item.session_age,
            }
            for item in outcomes
        ],
        "transcript_context": transcript_excerpts,
        "output_path": str(path.parent / "session_reviewer_result.json"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(handoff, indent=2), encoding="utf-8")


def read_result(path: Path) -> AgentResult:
    """Read the session reviewer result."""
    return parse_agent_result(path, "session_reviewer")

```


### hooks/__init__.py

```python
from __future__ import annotations

```


### hooks/common.py

```python
"""Shared utilities for GTO hooks.

Scope guard: determines if GTO is active by checking for state artifacts,
NOT marker files. A state file in the terminal-scoped artifacts directory
means GTO is running.

Terminal ID resolution matches the canonical pattern from /id skill:
1. CLAUDE_TERMINAL_ID env var (highest priority)
2. WT_SESSION (Windows Terminal session UUID, normalized with console_ prefix)
3. PID+timestamp hash fallback
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def get_terminal_id() -> str:
    """Get the current terminal ID using canonical resolution.

    Priority matches /id skill and recap skill:
    1. CLAUDE_TERMINAL_ID (set by SessionStart hook)
    2. WT_SESSION (Windows Terminal UUID, normalized to console_ prefix)
    3. PID+timestamp hash fallback
    """
    # Priority 1: explicit env override
    value = os.environ.get("CLAUDE_TERMINAL_ID", "").strip()
    if value:
        return value

    # Priority 2: Windows Terminal session UUID
    wt_session = os.environ.get("WT_SESSION", "").strip()
    if wt_session:
        return f"console_{wt_session}"

    # Priority 3: PID+timestamp hash (stable within session)
    pid = os.getpid()
    ts = int(datetime.now(timezone.utc).timestamp())
    unique = f"{pid}_{ts}".encode()
    return hashlib.sha1(unique).hexdigest()[:12]


def get_project_root() -> Path:
    """Get the project root directory.

    Priority:
    1. CLAUDE_PROJECT_DIR env var (set by Claude Code)
    2. Walk up from cwd to find .git
    """
    # Priority 1: Claude Code sets this
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "").strip()
    if project_dir:
        return Path(project_dir)

    # Priority 2: walk up from cwd to find .git
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".git").exists():
            return parent
    return cwd


def get_artifacts_root() -> Path:
    """Get the root for terminal-scoped GTO-v2 artifacts.

    Priority:
    1. CLAUDE_ARTIFACTS_ROOT env var (for testing)
    2. Drive-root .claude directory (e.g. P:\\\\\\.claude/.artifacts/)

    Uses drive-root rather than project-scoped so artifacts survive
    across projects within the same terminal session.
    """
    override = os.environ.get("CLAUDE_ARTIFACTS_ROOT", "").strip()
    if override:
        return Path(override)
    drive_root = Path(get_project_root().anchor)
    return drive_root / ".claude" / ".artifacts"


def get_verified_identity(session_id: str | None = None) -> dict | None:
    """Read and verify the global identity cache for the current terminal.

    This implements a 'Handshake' pattern: we only trust the cached identity
    if it matches our live session_id. This prevents using stale data from
    a previous session in the same terminal.
    """
    # 1. Start with the fastest heuristic-based ID (WT_SESSION)
    terminal_id = get_terminal_id()
    if not terminal_id:
        return None

    # 2. Locate the identity.json file
    safe_tid = terminal_id.replace("/", "-").replace("\\", "-").replace(":", "-")
    identity_file = get_artifacts_root() / safe_tid / "identity.json"

    if not identity_file.exists():
        return None

    # 3. THE HANDSHAKE: Verify against live session_id
    try:
        identity = json.loads(identity_file.read_text(encoding="utf-8"))
        if session_id:
            cached_sid = identity.get("claude", {}).get("session_id")
            if cached_sid and cached_sid != session_id:
                # Stale data: identity file belongs to a DIFFERENT session
                return None
        return identity
    except (json.JSONDecodeError, OSError):
        return None


def gto_state_dir(session_id: str | None = None) -> Path:
    """Get the GTO-v2 state directory for the current terminal."""
    # Opportunistic Handshake: use identity.json if verified
    identity = get_verified_identity(session_id)
    if identity:
        terminal_id = identity.get("terminal", {}).get("id")
    else:
        terminal_id = get_terminal_id()

    return get_artifacts_root() / terminal_id / "gto_v2" / "state"


def is_gto_active(session_id: str | None = None) -> bool:
    """Check if GTO is currently active in this terminal.

    GTO is active if a state file exists in the terminal-scoped artifacts dir.
    """
    state_dir = gto_state_dir(session_id)
    state_file = state_dir / "run_state.json"
    return state_file.exists()


def read_state(session_id: str | None = None) -> dict:
    """Read the current GTO run state. Returns empty dict if not active."""
    state_file = gto_state_dir(session_id) / "run_state.json"
    if not state_file.exists():
        return {}
    try:
        return json.loads(state_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def write_state(state: dict) -> None:
    """Write GTO run state."""
    state_dir = gto_state_dir()
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "run_state.json"
    state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def read_hook_input() -> dict:
    """Read hook input from stdin (Claude Code hook protocol)."""
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        return {}


def write_hook_output(data: dict) -> None:
    """Write hook output to stdout (Claude Code hook protocol)."""
    json.dump(data, sys.stdout, ensure_ascii=False)
    sys.stdout.write("\n")
    sys.stdout.flush()

```


### hooks/posttooluse.py

```python
#!/usr/bin/env python3
"""GTO-v2 PostToolUse hook — failure capture and file-change logging.

Artifact validation (JSON validity, RNS markers) is owned by hooks/stop.py.
This hook handles local logging only.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from .common import gto_state_dir, write_hook_output


def run(data: dict) -> dict | None:
    """In-process hook entry point."""
    session_id = data.get("session_id")
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    tool_output = data.get("tool_output", "")

    # Capture failures during GTO-v2 runs
    if _is_failure(tool_output):
        _capture_failure(tool_name, tool_input, tool_output, session_id)

    # Record file changes for session-scoped tracking
    if tool_name in ("Write", "Edit"):
        file_path = tool_input.get("file_path", "")
        if file_path:
            _record_file_change(file_path, session_id)

    return None


def _is_failure(output: str) -> bool:
    """Check if tool output indicates a failure."""
    if not output:
        return False
    failure_signals = ["Error:", "error:", "FAILED", "Traceback", "Exception"]
    return any(s in output for s in failure_signals)


def _capture_failure(tool_name: str, tool_input: dict, output: str, session_id: str | None = None) -> None:
    """Append a failure capture entry to the GTO-v2 logs."""
    logs_dir = gto_state_dir(session_id).parent / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    log_file = logs_dir / "failures.jsonl"

    entry = {
        "tool": tool_name,
        "input_summary": str(tool_input.get("command", tool_input.get("file_path", "")))[:200],
        "output_snippet": output[:500],
    }
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _record_file_change(file_path: str, session_id: str | None = None) -> None:
    """Append a file change record to the session changes log."""
    artifacts_dir = gto_state_dir(session_id).parent
    log_path = artifacts_dir / "session_changes.jsonl"
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "tool": "file-edit",
        "file": file_path,
        "session_id": session_id or os.environ.get("CLAUDE_SESSION_ID", ""),
    }
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def main() -> None:
    """CLI entry point."""
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        data = {}

    result = run(data)
    if result is not None:
        write_hook_output(result)
    else:
        write_hook_output({"decision": "allow"})
    sys.exit(0)


if __name__ == "__main__":
    main()

```


### hooks/pretooluse.py

```python
#!/usr/bin/env python3
"""GTO PreToolUse hook — optional gates during GTO runs.

Claude Code hook protocol: reads JSON from stdin, outputs JSON to stdout.

During GTO runs, this hook can:
- Warn if tool usage might conflict with artifact generation
- Block destructive operations during active analysis
"""
from __future__ import annotations

import json
import sys

from .common import is_gto_active, read_state, write_hook_output

# Tools that should be warned about during active GTO runs
WARN_TOOLS = {"Bash"}

# Token sequences that indicate destructive commands.
# Matched as ordered token subsequences to avoid false positives
# (e.g., "echo 'rm -rf'" in a string should not trigger).
BLOCK_PATTERNS: list[list[str]] = [
    ["rm", "-rf"],
    ["rm", "-r", "-f"],
    ["git", "reset", "--hard"],
    ["git", "checkout", "--"],
    ["git", "clean", "-f"],
]


def _matches_pattern(tokens: list[str], pattern: list[str]) -> bool:
    """Check if pattern tokens appear as an ordered subsequence in tokens."""
    if len(pattern) > len(tokens):
        return False
    for i in range(len(tokens) - len(pattern) + 1):
        if tokens[i:i + len(pattern)] == pattern:
            return True
    return False


def run(data: dict) -> dict | None:
    """In-process hook entry point."""
    session_id = data.get("session_id")
    if not is_gto_active(session_id):
        return None

    state = read_state(session_id)
    if state.get("phase") != "running":
        return None

    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if tool_name not in WARN_TOOLS:
        return None

    # Check for destructive commands using tokenized matching
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        tokens = command.split()
        for pattern in BLOCK_PATTERNS:
            if _matches_pattern(tokens, pattern):
                return {
                    "decision": "block",
                    "reason": f"GTO: blocking destructive command during active run: '{' '.join(pattern)}'",
                }

    return None


def main() -> None:
    """CLI entry point."""
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        data = {}

    result = run(data)
    if result is not None:
        write_hook_output(result)
        if result.get("decision") == "block":
            sys.exit(2)
    else:
        write_hook_output({"decision": "allow"})
    sys.exit(0)


if __name__ == "__main__":
    main()

```


### hooks/sessionstart.py

```python
#!/usr/bin/env python3
"""GTO SessionStart hook — restore state and show prior diagnosis.

Claude Code hook protocol: reads JSON from stdin, outputs JSON to stdout.

If GTO state exists for this terminal, shows a brief summary of the
last run's findings so the user can pick up where they left off.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from .common import is_gto_active, read_state, write_hook_output


def _count_findings_in_artifact(artifact_path: str) -> int:
    """Count findings in an artifact JSON file. Returns 0 on any failure."""
    try:
        data = json.loads(Path(artifact_path).read_text(encoding="utf-8"))
        return len(data.get("findings", []))
    except (json.JSONDecodeError, OSError, ValueError):
        return 0


def _count_resolved_carryover(state: dict, session_id: str | None = None) -> int:
    """Count resolved findings in carryover.json for this terminal."""
    try:
        from .common import gto_state_dir
        carryover_path = gto_state_dir(session_id).parent / "carryover.json"
        if not carryover_path.exists():
            return 0
        data = json.loads(carryover_path.read_text(encoding="utf-8"))
        return sum(1 for f in data if isinstance(f, dict) and f.get("status") == "resolved")
    except (json.JSONDecodeError, OSError):
        return 0


def run(data: dict) -> dict | None:
    """In-process hook entry point. Returns None to allow, dict to modify."""
    session_id = data.get("session_id")
    if not is_gto_active(session_id):
        return None

    state = read_state(session_id)
    if not state:
        return None

    phase = state.get("phase", "")
    target = state.get("current_target", "unknown")

    # Count actual findings from the artifact, not artifact paths
    findings_count = sum(
        _count_findings_in_artifact(p)
        for p in state.get("expected_artifacts", [])
    )

    if phase == "completed":
        msg = f"GTO: prior run completed for '{target}'. {findings_count} findings available."
        # Report resolved findings from carryover
        resolved = _count_resolved_carryover(state, session_id)
        if resolved:
            msg += f" ({resolved} findings resolved since last run)"
    elif phase in ("initialized", "running"):
        msg = f"GTO: prior run was '{phase}' for '{target}'. Consider re-running /gto."
    else:
        return None

    return {"decision": "allow", "reason": msg}


def main() -> None:
    """CLI entry point for Claude Code hook protocol."""
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        data = {}

    result = run(data)
    if result is not None:
        write_hook_output(result)
    else:
        write_hook_output({"decision": "allow"})
    sys.exit(0)


if __name__ == "__main__":
    main()

```


### hooks/stop.py

```python
#!/usr/bin/env python3
"""GTO-v2 Stop hook — mechanical artifact verification only.

This hook performs ONLY mechanical checks. The skill-guard execution runtime
evaluates the contract (phase, required_artifacts completion) separately.

Checks:
1. Artifact file exists at expected path
2. Artifact is valid JSON
3. Machine output has RNS|D| and RNS|Z| markers

Returns None (allow) on pass, {"decision": "warn"} with reason on failure.
Does NOT block — skill-guard Stop is the contract authority.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from .common import gto_state_dir, write_hook_output


def run(data: dict) -> dict | None:
    """In-process hook entry point."""
    session_id = data.get("session_id")
    state_dir = gto_state_dir(session_id)
    artifact_path = state_dir.parent / "outputs" / "artifact.json"

    if not artifact_path.exists():
        return {
            "decision": "warn",
            "reason": f"gto-v2: artifact not found at {artifact_path}",
        }

    try:
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return {
            "decision": "warn",
            "reason": f"gto-v2: artifact not valid JSON: {exc}",
        }

    machine = artifact.get("machine_output", [])
    if isinstance(machine, list):
        has_d = any(isinstance(l, str) and l.startswith("RNS|D|") for l in machine)
        has_z = any(isinstance(l, str) and l.startswith("RNS|Z|") for l in machine)
        if not has_d or not has_z:
            return {
                "decision": "warn",
                "reason": "gto-v2: artifact machine_output missing RNS|D| or RNS|Z| markers",
            }

    return None


def main() -> None:
    """CLI entry point."""
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except (json.JSONDecodeError, OSError):
        data = {}

    result = run(data)
    if result is not None:
        write_hook_output(result)
    else:
        write_hook_output({"decision": "allow"})
    sys.exit(0)


if __name__ == "__main__":
    main()

```


### models.py

```python
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Literal

EvidenceLevel = Literal["verified", "unverified", "derived"]
FindingStatus = Literal["open", "mapped", "rejected", "deferred", "resolved", "stale"]
FindingScope = Literal["local", "systemic", "architectural"]
FindingSourceType = Literal["detector", "agent", "hook", "artifact", "carryover", "user"]


@dataclass
class EvidenceRef:
    kind: str
    value: str
    detail: str | None = None


@dataclass
class Finding:
    id: str
    title: str
    description: str
    source_type: FindingSourceType
    source_name: str
    domain: str
    gap_type: str
    severity: str
    evidence_level: EvidenceLevel
    action: str = "recover"
    priority: str = "medium"
    status: FindingStatus = "open"
    scope: FindingScope = "local"
    owner_skill: str | None = None
    owner_reason: str | None = None
    file: str | None = None
    line: int | None = None
    symbol: str | None = None
    reversibility: float | None = None
    effort: str | None = None
    target: str | None = None
    depends_on: list[str] = field(default_factory=list)
    evidence: list[EvidenceRef] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    terminal_id: str | None = None
    session_id: str | None = None
    git_sha: str | None = None
    freshness: str | None = None
    unverified: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentResult:
    agent: str
    findings: list[Finding]
    raw_notes: str = ""
    success: bool = True


@dataclass
class GTOArtifact:
    artifact_version: str
    mode: str
    created_at: str
    terminal_id: str
    session_id: str
    target: str
    git_sha: str | None
    health_score: int | None
    freshness: str
    findings: list[Finding]
    summary: dict[str, Any]
    machine_output: list[str]
    human_output: str
    verification: dict[str, Any]
    coverage: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def empty(
        cls,
        mode: str,
        terminal_id: str,
        session_id: str,
        target: str,
        git_sha: str | None,
    ) -> GTOArtifact:
        return cls(
            artifact_version="1.0.0",
            mode=mode,
            created_at=datetime.now(timezone.utc).isoformat(),
            terminal_id=terminal_id,
            session_id=session_id,
            target=target,
            git_sha=git_sha,
            health_score=None,
            freshness="unknown",
            findings=[],
            summary={},
            machine_output=[],
            human_output="",
            verification={},
            coverage={},
            metadata={},
        )

```


### orchestrator.py

```python
#!/usr/bin/env python3
"""GTO Orchestrator — main entry point for session-aware gap analysis.

Usage:
    python orchestrator.py [options]

Runs deterministic detectors, session transcript analysis, carryover resolution,
and produces RNS-compatible machine output.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


from .models import GTOArtifact, Finding, EvidenceRef
from .settings import GTOSettings
from .__lib.context import get_git_sha
from .__lib.detectors import run_basic_detectors
from .__lib.carryover import load_carryover_open_only, save_carryover, prune_carryover, apply_carryover_enrichment
from .__lib.resolve import resolve_findings
from .__lib.session_goal_detector import SessionGoalDetector
from .__lib.session_outcome_detector import SessionOutcomeDetector, SessionOutcomeResult
from .__lib.transcript import read_turns, extract_edited_files
from .__lib.docs_followup import detect_docs_followup
from .__lib.normalize import normalize_findings
from .__lib.dedupe import dedupe_findings
from .__lib.merge import merge_findings
from .__lib.route import route_findings
from .__lib.dependency_order import order_findings
from .__lib.freshness import classify_freshness
from .__lib.targeting import resolve_target
from .__lib.coverage import compute_coverage, compute_health_score
from .__lib.evidence import write_artifact
from .__lib.state import RunState, load_state, save_state, sync_to_execution_state
from .__lib.verify import verify_artifact
from .__lib.changelog import detect_changelog_findings
from .__lib.invocation_tracker import check_invocations
from .__lib.clustering import cluster_findings
from .__lib.context_boundaries import context_boundary_findings
from .__lib.impact_radius import enrich_with_impact_radius
from .__lib.branch_awareness import adjust_for_branch
from .__lib.stuckness import detect_stuckness
from .__lib.hook_health import detect_hook_errors
from .__lib.workflow_hygiene import detect_workflow_hygiene
from .__lib.verification_debt import detect_verification_debt


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="GTO Gap Analysis Orchestrator")
    parser.add_argument("--target", help="Target directory or project to analyze")
    parser.add_argument("--terminal-id", default="default")
    parser.add_argument("--session-id", default="")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    return parser.parse_args(argv)


def _resolve_transcript_from_identity(terminal_id: str) -> Path | None:
    """Resolve transcript path from identity.json (hook-captured, no scanning)."""
    artifacts_root = Path(os.environ.get("CLAUDE_ARTIFACTS_ROOT", "P:\\\\\\.claude/.artifacts"))
    identity_file = artifacts_root / terminal_id / "identity.json"
    if not identity_file.exists():
        return None
    try:
        data = json.loads(identity_file.read_text(encoding="utf-8"))
        tp = data.get("claude", {}).get("transcript_path", "")
        if tp and Path(tp).exists():
            return Path(tp)
    except (json.JSONDecodeError, OSError):
        pass
    return None


def _load_session_chain(terminal_id: str) -> list[str]:
    """Load session transcript paths from session registry for this terminal."""
    registry_path = Path("P:\\\\\\.claude/.artifacts/session_registry.jsonl")
    if not registry_path.exists():
        return []
    try:
        import sys as _sys
        sys.path.insert(0, "P:\\\\\\packages/snapshot/scripts/hooks/__lib")
        from session_registry import query_registry
    except ImportError:
        return []
    entries = query_registry(terminal_id=terminal_id, limit=20)
    # Deduplicate by session_id, keep most recent per session, oldest-first order
    seen: set[str] = set()
    result: list[str] = []
    for e in reversed(entries):
        sid = e.get("session_id", "")
        tp = e.get("transcript_path", "")
        if sid and sid not in seen and tp and Path(tp).exists():
            seen.add(sid)
            result.append(tp)
    return list(reversed(result))


def _convert_outcome_findings(
    outcome_result: object,
    terminal_id: str,
    session_id: str,
    git_sha: str | None,
) -> list[Finding]:
    """Convert SessionOutcomeResult items to GTO Finding objects."""
    findings: list[Finding] = []
    items = getattr(outcome_result, "items", [])
    if not items:
        return findings

    category_domain_map = {
        "uncompleted_goal": "session",
        "identified_task": "session",
        "open_question": "session",
        "deferred_item": "session",
    }
    category_severity_map = {
        "uncompleted_goal": "medium",
        "identified_task": "medium",
        "open_question": "low",
        "deferred_item": "low",
    }

    for idx, item in enumerate(items):
        category = getattr(item, "category", "identified_task")
        content = getattr(item, "content", "")
        confidence = getattr(item, "confidence", 0.5)
        recurrence = getattr(item, "recurrence_count", 1)
        acknowledged = getattr(item, "acknowledged", False)

        severity = "high" if recurrence >= 2 else category_severity_map.get(category, "low")

        findings.append(
            Finding(
                id=f"SESSION-{category[:4].upper()}-{idx + 1:03d}",
                title=content[:120],
                description=f"Session outcome: {category} (recurrence={recurrence}, acknowledged={acknowledged})",
                source_type="detector",
                source_name="session_outcome_detector",
                domain=category_domain_map.get(category, "session"),
                gap_type=f"session_{category}",
                severity=severity,
                evidence_level="verified" if confidence >= 0.7 else "unverified",
                action="recover",
                priority=severity,
                terminal_id=terminal_id,
                session_id=session_id,
                git_sha=git_sha,
                evidence=[
                    EvidenceRef(kind="session_outcome", value=category, detail=f"confidence={confidence}"),
                ],
            )
        )

    return findings


def _extract_context(
    transcript_path: Path | None,
    items: list[object],
    window: int = 5,
) -> list[dict[str, str]]:
    """Extract transcript turns surrounding each outcome item for LLM review."""
    if not transcript_path or not transcript_path.exists() or not items:
        return []
    turns = read_turns(transcript_path)
    if not turns:
        return []
    excerpts: list[dict[str, str]] = []
    for item in items:
        turn_num = getattr(item, "turn_number", 0)
        if turn_num <= 0:
            continue
        idx = turn_num - 1
        start = max(0, idx - window)
        end = min(len(turns), idx + window + 1)
        for t in turns[start:end]:
            excerpts.append({"role": t.role, "content": t.content})
    return excerpts


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()

    settings = GTOSettings(
        terminal_id=args.terminal_id,
        session_id=args.session_id,
        git_sha=get_git_sha(root),
        root=root,
        mode="full",
    )

    paths = settings.paths
    paths.state_dir.mkdir(parents=True, exist_ok=True)
    paths.outputs_dir.mkdir(parents=True, exist_ok=True)

    # Initialize state
    state_file = paths.state_dir / "run_state.json"
    state = load_state(state_file)
    prev_git_sha = state.git_sha  # capture before overwrite
    state.run_id = f"{args.terminal_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    state.phase = "running"
    state.current_target = resolve_target(args.target, None, None)
    state.git_sha = settings.git_sha
    state.verification_required = True
    state.verification_status = "pending"
    save_state(state_file, state)
    sync_to_execution_state(state, paths.artifacts_dir)

    # Phase 1: Deterministic detectors
    findings = run_basic_detectors(root, args.terminal_id, args.session_id, settings.git_sha)

    # Phase 1.2: Marker staleness — detect stale session markers from prior runs
    from .__lib.detectors import detect_marker_staleness, detect_missing_verification_evidence
    marker_findings = detect_marker_staleness(root, args.terminal_id, args.session_id, settings.git_sha)
    findings.extend(marker_findings)

    # Phase 1.3: Missing verification evidence — detect findings citing hooks/telemetry without test coverage
    verification_findings = detect_missing_verification_evidence(root, args.terminal_id, args.session_id, settings.git_sha)
    findings.extend(verification_findings)

    # Phase 1.4: Changelog detection — files changed since previous GTO run
    changelog_findings = detect_changelog_findings(
        root, prev_git_sha, settings.git_sha,
        args.terminal_id, args.session_id, settings.git_sha,
    )
    findings.extend(changelog_findings)

    # Capture changed files for carryover decay check
    from .__lib.changelog import get_changed_files as _get_changed_files
    changed_files_for_decay = (
        _get_changed_files(root, prev_git_sha, settings.git_sha)
        if prev_git_sha and settings.git_sha and prev_git_sha != settings.git_sha
        else []
    )

    # Phase 1.5: Resolve transcript from identity.json (hook-captured, no scanning)
    transcript_path = _resolve_transcript_from_identity(args.terminal_id)

    # Phase 1.6: Extract files edited this session from transcript tool calls
    session_edited_files = extract_edited_files(transcript_path, root) if transcript_path else []

    # Phase 1.7: Build session chain from session registry
    chain = _load_session_chain(args.terminal_id)

    # Phase 1.8: Detect session goals from transcript chain
    goal_result = None
    if chain:
        goal_result = SessionGoalDetector(root).detect_goal_from_chain(chain)

    # Phase 1.9: Detect session outcomes (uncompleted goals, open questions, deferred items)
    outcome_detector = SessionOutcomeDetector(root)
    outcome_result = outcome_detector.detect(transcript_path, args.terminal_id)
    session_findings = _convert_outcome_findings(outcome_result, args.terminal_id, args.session_id, settings.git_sha)

    # Phase 1.10: Filter outcomes that were actually completed during the session
    if outcome_result.items and transcript_path:
        from .__lib.completion_checker import check_completions
        filtered_items = check_completions(transcript_path, outcome_result.items)
        if len(filtered_items) < len(outcome_result.items):
            filtered_result = SessionOutcomeResult(
                items=filtered_items, total_count=len(filtered_items)
            )
            session_findings = _convert_outcome_findings(
                filtered_result, args.terminal_id, args.session_id, settings.git_sha
            )
        # Write handoff for optional LLM review of remaining ambiguous items
        # Low-confidence deferred candidates (confidence < 0.5) are included
        # for the session reviewer subagent to classify as confirmed/rejected.
        if filtered_items:
            from .agents.session_reviewer import write_handoff
            write_handoff(
                paths.artifacts_dir / "session_reviewer_handoff.json",
                filtered_items,
                _extract_context(transcript_path, filtered_items),
            )

    findings.extend(session_findings)

    # Phase 1.12: Context boundary detection — context switches within this session
    boundary_findings = context_boundary_findings(
        transcript_path, args.terminal_id, args.session_id, settings.git_sha,
    )
    findings.extend(boundary_findings)

    # Phase 1.13: Skill invocation tracking — were previous recommendations actioned?
    invocation_findings = check_invocations(
        transcript_path, changelog_findings,
        args.terminal_id, args.session_id, settings.git_sha,
    )
    findings.extend(invocation_findings)

    # Phase 1.14: Hook health detection — hook execution errors from transcript
    hook_error_findings = detect_hook_errors(
        transcript_path, args.terminal_id, args.session_id, settings.git_sha,
    )
    findings.extend(hook_error_findings)

    # Phase 1.15: Workflow hygiene — uncommitted changes in working tree
    hygiene_findings = detect_workflow_hygiene(
        root, args.terminal_id, args.session_id, settings.git_sha,
    )
    findings.extend(hygiene_findings)

    # Phase 1.16: Verification debt — edits without test verification
    verification_findings = detect_verification_debt(
        transcript_path, args.terminal_id, args.session_id, settings.git_sha,
    )
    findings.extend(verification_findings)

    # Phase 1.11: Write agent handoffs for LLM enrichment
    if findings:
        project_context = {
            "root": str(root),
            "git_sha": settings.git_sha,
            "terminal_id": args.terminal_id,
            "has_readme": (root / "README.md").exists(),
            "has_git": (root / ".git").exists(),
        }
        from .agents.domain_analyzer import write_handoff as write_domain_handoff
        write_domain_handoff(
            paths.artifacts_dir / "domain_analyzer_handoff.json",
            findings,
            project_context,
        )

    # Phase 2: Load carryover (open only — resolved findings stay suppressed)
    carryover = load_carryover_open_only(paths.artifacts_dir)
    if carryover:
        # Apply escalation/decay based on carry count and file changes
        carryover = apply_carryover_enrichment(carryover, changed_files_for_decay)
        # Drop carryover findings superseded by a current-run finding with the same ID
        current_ids = {f.id for f in findings}
        carryover = [f for f in carryover if f.id not in current_ids]
        findings.extend(carryover)

    # Phase 4: Merge, normalize, dedupe, route, order
    all_findings = merge_findings(findings, [])
    all_findings = normalize_findings(all_findings)

    # Docs follow-up detection
    docs_findings = detect_docs_followup(root, all_findings)
    all_findings.extend(docs_findings)

    all_findings = dedupe_findings(all_findings)

    # Phase 4.5: Resolve findings based on session edits
    edited_file_set: set[str] = set()
    for fp in session_edited_files:
        try:
            edited_file_set.add(str(fp.relative_to(root)).replace("\\", "/"))
        except ValueError:
            edited_file_set.add(str(fp).replace("\\", "/"))
    all_findings = resolve_findings(all_findings, edited_file_set, root)

    # Split: display excludes resolved, carryover includes them
    carryover_findings = list(all_findings)
    all_findings = [f for f in all_findings if f.status != "resolved"]

    # Phase 4.7: Read agent enrichment results (written by LLM-spawned subagents)
    from .agents.domain_analyzer import read_result as read_domain
    from .agents.findings_reviewer import read_result as read_reviewer
    from .agents.action_normalizer import read_result as read_normalizer

    domain_result = read_domain(paths.artifacts_dir / "domain_analyzer_result.json")
    if domain_result.success and domain_result.findings:
        all_findings.extend(domain_result.findings)
        all_findings = dedupe_findings(all_findings)

    reviewer_result = read_reviewer(paths.artifacts_dir / "findings_reviewer_result.json")
    if reviewer_result.success and reviewer_result.findings:
        # Replace findings with reviewed versions (reviewer may reject/adjust)
        reviewed_ids = {f.id for f in reviewer_result.findings}
        all_findings = [f for f in all_findings if f.id not in reviewed_ids]
        all_findings.extend(reviewer_result.findings)

    normalizer_result = read_normalizer(paths.artifacts_dir / "action_normalizer_result.json")
    if normalizer_result.success and normalizer_result.findings:
        # Replace with normalized versions
        normalized_ids = {f.id for f in normalizer_result.findings}
        all_findings = [f for f in all_findings if f.id not in normalized_ids]
        all_findings.extend(normalizer_result.findings)

    # Read gap reviewer result — structured review + any new findings
    from .agents.gap_reviewer import read_result as read_gap
    gap_result = read_gap(paths.artifacts_dir / "gap_reviewer_result.json")
    if gap_result.success and gap_result.findings:
        gap_ids = {f.id for f in gap_result.findings}
        all_findings = [f for f in all_findings if f.id not in gap_ids]
        all_findings.extend(gap_result.findings)

    # Write findings_reviewer and action_normalizer handoffs for next agent pass
    if all_findings:
        from .agents.findings_reviewer import write_handoff as write_reviewer_handoff
        from .agents.action_normalizer import write_handoff as write_normalizer_handoff
        from .agents.gap_reviewer import write_handoff as write_gap_handoff
        write_reviewer_handoff(
            paths.artifacts_dir / "findings_reviewer_handoff.json",
            all_findings,
        )
        write_normalizer_handoff(
            paths.artifacts_dir / "action_normalizer_handoff.json",
            all_findings,
        )
        # Gap reviewer: context-enriched handoff with detector evidence + absence signals
        detectors_ran = list({f.source_name for f in all_findings if f.source_name})
        # Only list a detector as "empty" if it produced NO findings this run.
        # invocation_tracker always emits at least INVOCATION-UNACTIONED-001, so never
        # list it in detectors_empty (avoids schema contradiction: GAPR-pipeline-1).
        invocation_ran = any(f.source_name == "invocation_tracker" for f in all_findings)
        _detectors_empty = [
            "session_goal_detector", "context_boundary_detector",
            "stuckness_detector",
            "hook_health_detector", "workflow_hygiene_detector",
            "verification_debt_detector",
        ]
        if not invocation_ran:
            _detectors_empty.append("invocation_tracker")
        # Filter: remove detectors that actually produced findings
        detectors_empty = [d for d in _detectors_empty if d not in detectors_ran]
        outcome_dicts = [
            {"category": getattr(i, "category", ""), "content": getattr(i, "content", "")}
            for i in (outcome_result.items if outcome_result else [])
        ]
        write_gap_handoff(
            paths.artifacts_dir / "gap_reviewer_handoff.json",
            all_findings,
            session_outcomes=outcome_dicts,
            changed_files=changed_files_for_decay,
            session_context={
                "terminal_id": args.terminal_id,
                "session_id": args.session_id,
                "git_sha": settings.git_sha,
                "root": str(root),
            },
            detectors_ran=detectors_ran,
            detectors_empty=detectors_empty,
        )

    all_findings = route_findings(all_findings)
    all_findings = order_findings(all_findings)

    # Phase 4.8: Impact radius enrichment
    all_findings = enrich_with_impact_radius(root, all_findings)

    # Phase 4.9: Finding clustering
    all_findings = cluster_findings(all_findings)

    # Phase 4.10: Branch-aware priority adjustment
    all_findings = adjust_for_branch(root, all_findings)

    # Phase 4.11: Stuckness detection from session chain
    stuckness_findings = detect_stuckness(
        root, chain, carryover,
        args.terminal_id, args.session_id, settings.git_sha,
    )
    all_findings.extend(stuckness_findings)

    # Phase 5: Compute coverage + health score
    coverage = compute_coverage(all_findings)

    # Phase 6: Determine freshness
    freshness = classify_freshness(
        artifact_git_sha=prev_git_sha,
        current_git_sha=settings.git_sha,
        artifact_target=state.current_target,
        current_target=state.current_target,
    )

    health = compute_health_score(all_findings, freshness)

    # Phase 7: Build and write artifact
    artifact = GTOArtifact.empty(
        mode="full",
        terminal_id=args.terminal_id,
        session_id=args.session_id,
        target=state.current_target,
        git_sha=settings.git_sha,
    )
    artifact.freshness = freshness
    artifact.coverage = coverage
    artifact.summary = {
        "total_findings": len(all_findings),
        "by_severity": coverage.get("by_severity", {}),
        "by_domain": coverage.get("by_domain", {}),
        "health": health,
    }

    artifact_path = paths.outputs_dir / "artifact.json"
    write_artifact(artifact_path, artifact, all_findings)

    # Phase 8: Save carryover for future runs (includes resolved for dedup)
    save_carryover(paths.artifacts_dir, carryover_findings)
    prune_carryover(paths.artifacts_dir)

    # Phase 9: Update state
    state.phase = "completed"
    state.verification_status = "pending"
    state.last_artifact = str(artifact_path)
    state.expected_artifacts = [str(artifact_path)]
    save_state(state_file, state)
    sync_to_execution_state(state, paths.artifacts_dir)

    # Phase 10: Verify
    verification = verify_artifact(artifact_path)
    state.verification_status = "pass" if verification["valid"] else "fail"
    save_state(state_file, state)
    sync_to_execution_state(state, paths.artifacts_dir)

    # Output summary
    print(f"GTO complete: {len(all_findings)} findings", file=sys.stderr)
    print(f"Artifact: {artifact_path}", file=sys.stderr)
    print(f"Freshness: {freshness}", file=sys.stderr)

    return 0 if verification["valid"] else 1


if __name__ == "__main__":
    sys.exit(run())

```


### settings.py

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class GTOPaths:
    root: Path
    artifacts_dir: Path
    state_dir: Path
    inputs_dir: Path
    outputs_dir: Path
    logs_dir: Path


@dataclass(frozen=True)
class GTOSettings:
    terminal_id: str
    session_id: str
    git_sha: str | None
    root: Path
    mode: str = "full"

    @property
    def paths(self) -> GTOPaths:
        override = os.environ.get("CLAUDE_ARTIFACTS_ROOT", "").strip()
        if override:
            artifacts_base = Path(override)
        else:
            artifacts_base = Path(self.root.anchor) / ".claude" / ".artifacts"
        base = artifacts_base / self.terminal_id / "gto_v2"
        return GTOPaths(
            root=self.root,
            artifacts_dir=base,
            state_dir=base / "state",
            inputs_dir=base / "inputs",
            outputs_dir=base / "outputs",
            logs_dir=base / "logs",
        )

```


### test_context_boundaries.py

```python
"""Tests for context_boundaries word-boundary snap fix."""
from __future__ import annotations

import re


def snap_to_word(remainder: str) -> str:
    """Snap start AND end of remainder to word boundaries, capped at ~100 chars."""
    r = re.search(r"\w", remainder)
    start_offset = r.start() if r else 0
    end_offset = start_offset + 100
    if end_offset < len(remainder):
        pre_end = remainder[start_offset:end_offset]
        # Find complete words (word followed by separator) in pre_end
        last_match = None
        for m in re.finditer(r"\w+(?=\W)", pre_end):
            last_match = m
        if last_match:
            end_offset = start_offset + last_match.end()
    return remainder[start_offset:end_offset]


def test_snaps_start_to_word():
    """Start must not be mid-path — `:diagnostics` should snap past `:`."""
    remainder = ":diagnostics/P:/.claude/hooks"
    phrase = snap_to_word(remainder)
    assert phrase[0].isalpha() or phrase[0] == "_", f"Got: {phrase!r}"


def test_snaps_end_to_word():
    """End must not be mid-word — sentence truncates mid-word, snaps to last complete word."""
    # Sentence is 100+ chars. Cut at 100 lands mid-word on "thing".
    # Last complete word before cutoff is "other". Snap to that.
    remainder = "work on the hooks module and this other thing" + "x" * 200
    phrase = snap_to_word(remainder)
    assert phrase.endswith("other"), f"Got mid-word end: {phrase!r}"


def test_normal_content_unchanged():
    """Normal sentence snaps cleanly to full words."""
    remainder = " work on the hooks module."
    phrase = snap_to_word(remainder)
    assert phrase.startswith("work"), f"Got: {phrase!r}"
    assert phrase.endswith("module."), f"Got: {phrase!r}"


def test_empty_remainder():
    """Empty remainder must not crash."""
    assert snap_to_word("") == ""


def test_already_word_boundary():
    """Already clean start/end stays unchanged."""
    remainder = "work on the hooks module."
    phrase = snap_to_word(remainder)
    assert phrase.startswith("work")


def test_path_mid_segment():
    """.claude/hooks/SomeFile.py — end snaps to `SomeFile`."""
    remainder = ".claude/hooks/SomeFile.py and continue."
    phrase = snap_to_word(remainder)
    assert phrase.startswith("claude") or phrase.startswith("SomeFile")


def test_hooks_di_corruption():
    """The actual bug: path remainder snaps to word boundaries."""
    # After pattern match ends mid-segment, remainder starts mid-path
    remainder = "ostics/P:/.claude/hooks"
    phrase = snap_to_word(remainder)
    # Start must be a word char (snap past leading /)
    assert phrase[0].isalpha(), f"Got: {phrase!r}"
    # End should be clean (not mid-word)
    # Path is 23 chars, under 100 limit — no truncation, returned unchanged
    assert phrase == "ostics/P:/.claude/hooks", f"Got: {phrase!r}"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])

```

