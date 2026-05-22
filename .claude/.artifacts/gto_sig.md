# GTO — Signature Pack

Generated: 2026-05-13 12:12:32
Files: 53

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
- `orchestrator_fixed.py`
- `settings.py`

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
  def _validate_artifact_write(['file_path']) -> dict | None
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
  def _verify_completion(['state']) -> list[str]
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


## orchestrator_fixed.py
  (no top-level functions/classes)


## settings.py
  class GTOSettings:
    def paths([]) -> GTOPaths
  def paths(['self']) -> property


## APPENDIX: FULL SOURCE (see _full.md)