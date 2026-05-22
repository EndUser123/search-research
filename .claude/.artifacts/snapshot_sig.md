# snapshot_sig.md

**PACK INFO**
- **Target**: `P:\packages\snapshot`
- **Date**: 2026-05-13
- **Files**: 100
- **Output**: Signature-only (no full source)

**HOW TO USE**
1. Review SIGNATURE TOC for API overview
2. Use FILE INDEX to locate specific modules
3. For full implementation, see `snapshot_full.md`

---

## SIGNATURE TOC

### `assets\banners\generate_banner.py`
  def create_gradient_background(width, height, color_start, color_end)
  def main()

### `core\hooks\__init__.py`
  class CoreHooksFinder
    def find_spec(self, fullname: str, path, target)
  class CoreHooksLoader
    def create_module(self, spec)
    def exec_module(self, module)

### `examples\basic_usage.py`
  def example_basic_handoff()
  def example_checkpoint_chain()
  def example_serialization()

### `scripts\checkpoint_chain.py`
  class HandoffCheckpointRef
    def from_task_metadata(cls, task_id: str, metadata: dict[str, Any]) -> HandoffCheckpointRef
  class CheckpointChain
    def __init__(self, task_tracker_dir: Path, terminal_id: str)
    def _get_task_file_path(self) -> Path
    def _load_all_checkpoints(self) -> list[HandoffCheckpointRef]
    def _get_or_migrate_handoff(self, task_id: str, handoff: dict[str, Any]) -> dict[str, Any]
    def _process_task_metadata(self, task_id: str, task: dict[str, Any]) -> HandoffCheckpointRef | None
    def get_chain(self, chain_id: str) -> list[HandoffCheckpointRef]
    def get_latest(self, chain_id: str) -> HandoffCheckpointRef | None
    def get_previous(self, checkpoint_id: str) -> HandoffCheckpointRef | None
    def get_chain_length(self, chain_id: str) -> int
    def invalidate_cache(self, chain_id: str | None) -> None
    def get_next(self, checkpoint_id: str) -> HandoffCheckpointRef | None

### `scripts\checkpoint_ops.py`
  class PendingOperation
    def __post_init__(self) -> None
    def _validate_target(target: str) -> None
    def to_dict(self) -> dict[str, Any]
    def transition_to(self, new_state: str) -> None
    def from_dict(cls, data: dict[str, Any]) -> PendingOperation

### `scripts\cli.py`
  def cmd_capture(args: argparse.Namespace) -> int
  def cmd_restore(args: argparse.Namespace) -> int
  def cmd_list(args: argparse.Namespace) -> int
  def cmd_debug(args: argparse.Namespace) -> int
  def cmd_health(args: argparse.Namespace) -> int
  def cmd_cleanup(args: argparse.Namespace) -> int
  def main() -> int

### `scripts\config.py`
  def get_handoff_dir(project_root: Path | None) -> Path
  def ensure_directories() -> None
  def utcnow_iso() -> str
  def load_json_file(file_path: Path) -> dict[str, Any] | None
  def save_json_file(file_path: Path, data: dict[str, Any]) -> bool
  def cleanup_old_handoffs(project_root: Path | None) -> int
  def _cleanup_resolve_project_root() -> Path

### `scripts\fix_test_imports.py`
  def fix_test_file(test_path: Path) -> bool
  def main()

### `scripts\hooks\PreCompact_commitment_tracker.py`
  def run(data: dict) -> dict | None
  def main() -> None
  def _extract_terminal_id(data: dict) -> str
  def _extract_session_id(data: dict) -> str
  def _extract_transcript(data: dict) -> list[dict]

### `scripts\hooks\PreCompact_snapshot_capture.py`
  def _find_project_root(start: Path) -> Path
  def detect_session_type(user_message: str, active_files: list[str]) -> tuple[str, str]
  def detect_task_mode(user_message: str, active_files: list[str]) -> str
  def detect_lifecycle_phase(blockers: list[dict[str, Any]], active_files: list[str], pending_operations: list[dict[str, Any]], goal: str, task_mode: str) -> str
  def detect_planning_session(user_message: str, active_files: list[str]) -> dict[str, Any] | None
  def _read_hook_input() -> dict[str, Any]
  def _extract_active_files(parser: TranscriptParser) -> list[str]
  def _normalize_pending_operations(parser: TranscriptParser) -> list[dict[str, Any]]
  def _extract_slash_command_goal(raw_last_user: str | None, active_files: list[str]) -> tuple[str, str] | None
  def _extract_last_assistant_text(parser: TranscriptParser) -> str
  def _infer_next_step(last_assistant_text: str, pending_operations: list[dict[str, Any]], goal: str) -> str
  def _is_decision_noise(text: str) -> bool
  def _build_decisions(parser: TranscriptParser, transcript_evidence_id: str) -> list[dict[str, Any]]
  def _resolve_evidence_path(path: str, project_root: Path) -> Path
  def _make_portable_path(resolved_path: Path, project_root: Path) -> str
  def _build_evidence_index(project_root: Path, transcript_path: str, active_files: list[str]) -> list[dict[str, Any]]
  def _estimate_progress(blockers: list[dict[str, Any]], pending_operations: list[dict[str, Any]], goal: str) -> int
  def run(input_data: dict[str, Any]) -> dict[str, Any]
  def main() -> None

### `scripts\hooks\PreCompact_workflow_checkpoint.py`
  def _extract_terminal_id(data: dict) -> str
  def _sanitize_terminal_id(terminal_id: str) -> str
  def _get_state_dir(terminal_id: str) -> Path
  def _read_current_state(terminal_id: str) -> dict | None
  def main() -> None

### `scripts\hooks\SessionStart_snapshot_restore.py`
  def _read_hook_input() -> dict[str, Any]
  def _normalize_session_start_source(input_data: dict[str, Any]) -> str | None
  def _build_output(reason: str, additional_context: str | None) -> dict[str, Any]
  def _reject_if_possible(storage: SnapshotFileStorage, payload: dict[str, Any] | None) -> None
  def run(input_data: dict[str, Any]) -> dict[str, Any]
  def main() -> None

### `scripts\hooks\SessionStart_tldr.py`
  def _resolve_terminal_id(data: dict | None) -> str
  def _safe_id(value: str) -> str
  def _get_state_path(terminal_id: str) -> Path
  def _get_session_start_path(terminal_id: str) -> Path
  def _write_session_start(path: Path) -> None
  def _read_prior_summary(path: Path) -> str | None
  def extract_last_user_message(data: dict) -> str | None
  def _format_tldr_output(summary: str | None) -> str
  def run(data: dict) -> dict | None
  def main() -> int

### `scripts\hooks\__lib\architecture_capture.py`
  def capture_architectural_context(project_root: Path) -> dict | None
  def _find_adr_files(project_root: Path) -> list[str]
  def _parse_adr_files(project_root: Path, adr_files: list[str]) -> tuple[list[str], list[str]]
  def _clean_extracted_text(text: str) -> str

### `scripts\hooks\__lib\capture_cache.py`
  class CaptureCache
    def __init__(self, ttl: int) -> None
    def get(self, key: str) -> dict | None
    def set(self, key: str, value: dict) -> None
    def clear(self) -> None
    def generate_key(capture_type: str, project_root: str | Path, path_hash: str) -> str
    def hash_path(path: str | Path) -> str
    def hash_paths(paths: list[str | Path]) -> str

### `scripts\hooks\__lib\dependency_state.py`
  def capture_dependency_state(project_root: str) -> dict | None
  def _detect_package_manager(project_path: Path) -> str | None
  def _command_available(cmd: list[str]) -> bool
  def _get_installed_packages(package_manager: str, project_path: Path) -> list[dict]
  def _get_pip_packages() -> list[dict]
  def _get_poetry_packages(project_path: Path) -> list[dict]
  def _get_pipenv_packages(project_path: Path) -> list[dict]
  def _get_npm_packages(package_manager: str) -> list[dict]

### `scripts\hooks\__lib\dynamic_sections.py`
  def _get_session_id_from_env() -> str
  def load_air_gaps() -> list[dict[str, Any]]
  def has_problem(session_data: dict[str, Any]) -> bool
  def has_actions(session_data: dict[str, Any]) -> bool
  def has_decisions(session_data: dict[str, Any]) -> bool
  def has_tasks(session_data: dict[str, Any]) -> bool
  def has_air_gaps(session_data: dict[str, Any]) -> bool
  def has_learning(session_data: dict[str, Any]) -> bool
  def build_premortem_section(session_data: dict[str, Any]) -> str
  def build_context_section(session_data: dict[str, Any]) -> str
  def build_problem_section(session_data: dict[str, Any]) -> str
  def build_analysis_section(session_data: dict[str, Any]) -> str
  def build_solution_section(session_data: dict[str, Any]) -> str
  def build_lessons_section(session_data: dict[str, Any]) -> str
  def build_actions_section(session_data: dict[str, Any]) -> str
  def build_decisions_section(session_data: dict[str, Any]) -> str
  def build_tasks_section(session_data: dict[str, Any]) -> str
  def build_quick_argument_section(session_data: dict[str, Any]) -> str
  def generate_handoff_content(session_data: dict[str, Any]) -> str
  def calculate_quality_score_dynamic(session_data: dict[str, Any]) -> float

### `scripts\hooks\__lib\error_capture.py`
  def capture_recent_errors(transcript: str, project_root: Path) -> dict | None
  def _extract_errors(transcript: str) -> list[dict]
  def _classify_error(error_message: str) -> str
  def _filter_terminal_specific_errors(errors: list[dict]) -> list[dict]

### `scripts\hooks\__lib\git_state.py`
  def capture_git_state(project_root: str) -> dict | None
  def _get_current_branch(project_path: Path) -> str
  def _has_uncommitted_changes(project_path: Path) -> bool
  def _get_last_commit(project_path: Path) -> dict | None

### `scripts\hooks\__lib\handover.py`
  class HandoverData
  class HandoverBuilder
    def __init__(self, project_root: Path, transcript_parser: TranscriptParser)
    def _extract_session_objectives(objectives_file: Path, max_objectives: int) -> list[str]
    def build(self, task_name: str) -> dict[str, Any]

### `scripts\hooks\__lib\hook_input_validation.py`
  class HookInputError
    def __init__(self, message: str, field_name: str | None)
  def validate_hook_input(input_data: dict[str, Any], hook_type: str) -> None

### `scripts\hooks\__lib\hook_schema.py`
  def validate_hook_output(output: dict[str, Any], hook_type: str) -> list[str]
  def assert_valid_hook_output(output: dict[str, Any], hook_type: str) -> None

### `scripts\hooks\__lib\parallel_capture.py`
  def capture_all_parallel(project_root: Path, transcript: str) -> dict
  def _capture_git_state(project_root: Path) -> dict | None
  def _capture_dependency_state(project_root: Path) -> dict | None
  def _capture_test_state(project_root: Path) -> dict | None
  def _capture_architectural_context(project_root: Path, transcript: str) -> dict | None

### `scripts\hooks\__lib\project_root.py`
  def detect_project_root(transcript_path: str | None, current_dir: Path | None, max_depth: int, strict: bool) -> Path

### `scripts\hooks\__lib\session_registry.py`
  def query_registry() -> list[dict]

### `scripts\hooks\__lib\snapshot_accumulator.py`
  def _get_accumulator_path(terminal_id: str, project_root: Path) -> Path
  def _append_event(path: Path, event: dict[str, Any]) -> None
  def _read_last_phase(accum_path: Path) -> str
  def _detect_phase_transition(tool_name: str, tool_input: dict[str, Any], current_phase: str) -> str | None
  def run(data: dict[str, Any]) -> dict[str, Any]

### `scripts\hooks\__lib\snapshot_files.py`
  class SnapshotFileStorage
    def __init__(self, project_root: Path, terminal_id: str)
    def _validate_terminal_id(terminal_id: str) -> None
    def _handoff_file_for_payload(self, payload: dict[str, Any]) -> Path
    def save_handoff(self, payload: dict[str, Any]) -> Path | bool
    def load_handoff(self) -> dict[str, Any] | None
    def load_raw_handoff(self, exclude_session_id: str | None) -> dict[str, Any] | None
    def update_snapshot_status(self) -> bool
    def update_snapshot_status_from_payload(self, payload: dict[str, Any]) -> bool
    def read_accumulated_state(self) -> list[dict[str, Any]]
    def truncate_accumulated_state(self) -> bool
    def delete_handoff(self) -> bool

### `scripts\hooks\__lib\snapshot_store.py`
  class FileLock
    def __init__(self, lock_file_path: Path, timeout: float, stale_age: float)
    def _try_acquire_lock_once(self) -> bool
    def acquire(self) -> bool
    def _check_and_remove_stale_lock(self) -> None
    def release(self) -> None
    def __enter__(self) -> FileLock
    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None
  def atomic_write_with_retry(temp_path: str, target_path: str | Path, max_retries: int) -> None
  def atomic_write_with_validation(data: dict[str, Any], target_path: str | Path, max_retries: int) -> dict[str, Any]
  def _truncate_text_field(text: str, max_length: int) -> str
  def _truncate_list_with_marker(items: list[Any], max_items: int) -> list[Any]
  def _truncate_list_keep_recent(items: list[Any], max_items: int) -> list[Any]
  def _truncate_handover_section(handover: dict[str, Any]) -> dict[str, Any]
  def _apply_last_resort_truncation(validated: dict[str, Any]) -> dict[str, Any]
  def _validate_handoff_data_size(handoff_data: dict[str, Any], cached_json: str | None) -> dict[str, Any]
  def calculate_quality_score(handoff_data: dict[str, Any]) -> float
  def get_quality_rating(score: float) -> str
  def compute_snapshot_checksum(snapshot_internal: dict[str, Any]) -> str
  class SnapshotStore
    def __init__(self, project_root: Path, terminal_id: str)
    def _validate_terminal_id(self, terminal_id: str) -> None
    def build_handoff_data(self, task_name: str, progress_pct: int, blocker: dict[str, Any] | None, files_modified: list[str], next_steps: list[str], handover: dict[str, Any], modifications: list[dict[str, Any]], calculate_quality: bool, pending_operations: list[dict[str, Any]] | None) -> dict[str, Any]
    def create_continue_session_task(self, task_name: str, task_id: str, handoff_metadata: dict[str, Any]) -> None

### `scripts\hooks\__lib\snapshot_v2.py`
  class SnapshotValidationError
  class RestoreDecision
  def utcnow() -> datetime
  def iso_now() -> str
  def parse_iso8601(value: str) -> datetime
  def make_decision_id() -> str
  def make_evidence_id() -> str
  def _normalize_for_checksum(payload: dict[str, Any]) -> dict[str, Any]
  def compute_checksum(payload: dict[str, Any]) -> str
  def compute_file_content_hash(path: str | Path) -> str | None
  def _format_snapshot_item(entry: Any) -> str
  def _build_restore_state(snapshot: dict[str, Any], decisions_by_id: dict[str, dict[str, Any]]) -> dict[str, Any]
  def _render_restore_state_lines(state: dict[str, Any]) -> list[str]
  def _render_restore_message_verbose(state: dict[str, Any]) -> str
  def _render_restore_message_compact(state: dict[str, Any]) -> str
  def _require_fields(obj: dict[str, Any], fields: list[str], prefix: str) -> None
  def validate_envelope(payload: dict[str, Any]) -> None
  def build_resume_snapshot() -> dict[str, Any]
  def build_envelope() -> dict[str, Any]
  def mark_snapshot_status(payload: dict[str, Any]) -> dict[str, Any]
  def evaluate_for_restore(payload: dict[str, Any]) -> RestoreDecision
  def verify_evidence_freshness(payload: dict[str, Any]) -> str | None
  def build_restore_message(payload: dict[str, Any]) -> str
  def build_restore_message_compact(payload: dict[str, Any]) -> str
  def build_restore_message_dynamic(payload: dict[str, Any]) -> str
  def build_stale_hint(payload: dict[str, Any], reason: str) -> str
  def build_no_snapshot_hint(reason: str) -> str
  def short_task_name(goal: str) -> str
  def ensure_progress_state(blockers: list[dict[str, Any]], pending_operations: list[dict[str, Any]]) -> str
  def _extract_and_format_user_context(transcript_path: str, max_messages: int) -> str | None

### `scripts\hooks\__lib\task_identity_manager.py`
  class TaskMetadata
  class TaskIdentityManager
    def __init__(self, project_root: Path | None, terminal_id: str | None) -> None
    def _require_stateful_terminal(self) -> bool
    def _is_metadata_fresh(timestamp_str: str, max_age_seconds: int) -> bool
    def get_current_task(self) -> str | None
    def _is_valid_task_name(self, task_name: str | None) -> bool
    def _from_env_var(self) -> str | None
    def _from_session_file(self) -> str | None
    def _from_compact_metadata(self) -> str | None
    def _ask_user(self) -> str | None
    def set_current_task(self, task_name: str) -> bool
    def store_compact_metadata(self, task_name: str, handoff_id: str) -> bool
    def register_task_worktree_mapping(self, task_name: str, branch: str) -> bool
    def record_active_command(self, command: str, phase: str, metadata: dict[str, object] | None) -> bool
    def clear_active_command(self) -> bool
    def _get_transient_task_id(self) -> str | None
    def cleanup_stale_terminal_files(self, max_age_hours: int) -> int

### `scripts\hooks\__lib\terminal_detection.py`
  def get_verified_identity(session_id: str | None) -> dict | None
  def _try_import_skill_guard() -> None
  def _lookup_terminal_from_registry(session_id: str | None, cwd: str | None) -> str
  def _fallback_detect_terminal_id(session_id: str | None) -> str
  def detect_terminal_id(session_id: str | None) -> str
  def resolve_terminal_key(terminal_id: str | None, session_id: str | None) -> str

### `scripts\hooks\__lib\terminal_file_registry.py`
  class TerminalFileRegistry
    def __init__(self, project_root: Path, terminal_id: str, ttl_hours: int)
    def _validate_terminal_id(terminal_id: str) -> None
    def record_access(self, file_path: str) -> None
    def get_recent_files(self, max_files: int) -> list[str]
    def _load_registry(self) -> dict[str, Any]
    def _save_registry(self, registry: dict[str, Any]) -> None
    def cleanup_expired(self) -> int

### `scripts\hooks\__lib\test_state.py`
  def capture_test_state(project_root: Path) -> dict | None
  def _find_test_files(project_root: Path) -> list[str]
  def _parse_test_results(project_root: Path, test_files: list[str]) -> dict[str, int]
  def _get_coverage(project_root: Path) -> float | None
  def _is_pytest_project(project_root: Path, test_files: list[str]) -> bool
  def _is_jest_project(project_root: Path, test_files: list[str]) -> bool
  def _is_cargo_project(project_root: Path, test_files: list[str]) -> bool

### `scripts\hooks\__lib\transcript.py`
  def _contains_non_ascii(text: str) -> bool
  def detect_message_intent(message: str) -> MessageIntent
  class StructureInfo
  class BlockerDef
  class MessageDict
  class GoalExtractionResult
  def extract_topic_from_content(content: str, task_name: str) -> Annotated[str, 'max_length=80']
  def _get_table_indicators() -> list[str]
  def _get_assessment_indicators() -> list[str]
  def _get_comparison_indicators() -> list[str]
  def _check_for_table_structure(content: str) -> bool
  def _check_for_assessment(content_lower: str) -> bool
  def _check_for_comparison(content_lower: str) -> bool
  def _extract_search_keys(content_lower: str, max_keys: int) -> list[str]
  def _determine_structure_type(has_table: bool, has_assessment: bool, has_comparison: bool, search_keys: list[str]) -> StructureInfo | None
  def detect_structure_type(content: str) -> StructureInfo | None
  def is_meta_instruction(message: str) -> bool
  def is_meta_discussion(message: str) -> bool
  def is_correction_message(message: str) -> bool
  def is_clarification_message(message: str) -> bool
  def is_directive_message(message: str) -> bool
  def is_same_topic(message1: str, message2: str, threshold: float) -> bool
  def detect_session_boundary(entry: dict, prev_entry: dict | None) -> bool
  def gather_context_with_boundaries(transcript_path: str | Path, max_messages: int) -> list[dict]
  def extract_last_substantive_user_message(transcript_path: str | Path) -> GoalExtractionResult
  def extract_preceding_message(transcript_path: str | Path, goal: str) -> str | None
  class TranscriptLines
    def __init__(self, path: str | None) -> None
    def _ensure_length(self) -> int
    def __len__(self) -> int
    def __getitem__(self, key: int) -> str
    def __getitem__(self, key: slice) -> list[str]
    def __getitem__(self, key: int | slice) -> str | list[str]
    def _load_line(self, index: int) -> str
    def _load_range(self, start: int, stop: int) -> list[str]
    def __iter__(self) -> Iterator[str]
  class TranscriptParser
    def __init__(self, transcript_path: str | None) -> None
    def _build_user_message_description(message: str, max_length: int) -> dict[str, Any]
    def _is_substantial_user_message(text: str, min_length: int) -> bool
    def _get_transcript_lines(self) -> Sequence[str]
    def _iter_transcript_lines(self) -> Iterator[str]
    def _get_parsed_entries(self) -> list[dict[str, Any]]
    def _extract_text_from_entry(self, entry: dict[str, Any]) -> str
    def _filter_entries_by_type(self, entries: list[dict[str, Any]], entry_type: str) -> list[dict[str, Any]]
    def extract_current_blocker(self) -> dict[str, Any] | None
    def extract_modifications(self, limit: int) -> list[dict[str, Any]]
    def extract_open_conversation_context(self) -> dict[str, Any] | None
    def extract_session_decisions(self, task_name: str) -> list[dict[str, Any]]
    def extract_session_patterns(self) -> list[str]
    def extract_controversial_decisions(self) -> list[dict[str, Any]]
    def extract_visual_context(self) -> dict[str, Any] | None
    def extract_last_user_message(self) -> str | None
    def get_transcript_timestamp(self) -> str | None
    def get_transcript_offset(self) -> int
    def get_transcript_entry_count(self) -> int
    def extract_pending_operations(self) -> list[dict[str, Any]]
    def extract_skill_invocations(self) -> list[dict[str, Any]]
    def _extract_skill_context(self, skill_entry: dict, all_entries: list[dict]) -> str
    def extract_last_skill_output(self, max_length: int) -> dict[str, Any] | None
  def extract_user_message_from_blocker(blocker: BlockerDef | str | None) -> str | None
  def filter_valid_messages(messages: list[MessageDict]) -> list[MessageDict]
  def extract_transcript_from_messages(messages: list[MessageDict]) -> str

### `scripts\hooks\__lib\user_intent.py`
  def capture_pending_questions(transcript: str) -> dict | None
  def _extract_questions(transcript: str) -> list[dict]
  def _categorize_question(question: str) -> str

### `scripts\hooks\__lib\validation_utils.py`
  def validate_terminal_id(terminal_id: str) -> None

### `scripts\hooks\snapshot_PreCompact.py`
  def main()

### `scripts\hooks\snapshot_SessionEnd_tldr.py`
  def _redact_secrets(text: str) -> str
  def _resolve_terminal_id(data: dict | None) -> str
  def _safe_id(value: str) -> str
  def _get_state_path(terminal_id: str) -> Path
  def _get_session_start_path(terminal_id: str) -> Path
  def _calculate_duration(start_iso: str | None) -> str | None
  def _get_ended_at() -> str
  def _collect_session_activity_from_handoff() -> dict
  def _collect_session_activity() -> dict
  def _atomic_write(path: Path, content: str) -> None
  def _write_summary(terminal_id: str, start_iso: str | None, ended_at: str, activity: dict) -> None
  def main() -> int

### `scripts\hooks\snapshot_SessionStart.py`
  def main()

### `scripts\hooks\snapshot_UserPromptSubmit.py`
  def _locate_hooks_state_dir(terminal_id: str) -> Path
  def _get_terminal_id(context: HookContext) -> str
  def _marker_path(terminal_id: str) -> Path
  def _load_marker(terminal_id: str) -> dict | None
  def _clear_marker(terminal_id: str) -> None
  def _smoke_path(terminal_id: str) -> Path
  def write_restore_smoke_marker(terminal_id: str, session_id: str) -> None
  def check_restore_smoke_marker(terminal_id: str, current_session_id: str) -> bool
  def _load_envelope(handoff_path: str) -> dict | None
  def _build_recovery_message(envelope: dict) -> str
  def handoff_task_injector_hook(context: HookContext) -> HookResult

### `scripts\migrate.py`
  def migrate_old_handoff_to_checkpoint(old_handoff: dict[str, Any]) -> dict[str, Any]
  def compute_metadata_checksum(handoff_data: dict[str, Any]) -> str
  def load_handoff_json(json_path: Path) -> dict[str, Any] | None
  def _build_handoff_metadata(migrated_handoff: dict[str, Any]) -> dict[str, Any]
  def handoff_to_task(handoff_data: dict[str, Any], terminal_id: str) -> dict[str, Any]
  def _create_task_file_structure(terminal_id: str) -> dict[str, Any]
  def _load_or_create_task_file(task_file_path: Path, terminal_id: str) -> dict[str, Any]
  def _write_task_file_atomic(task_file_path: Path, task_data: dict[str, Any]) -> bool
  def _initialize_migration_results() -> dict[str, Any]
  def _collect_handoff_files(handoff_dir: Path) -> list[Path] | None
  def _load_handoff_with_validation(json_path: Path, results: dict[str, Any]) -> dict[str, Any] | None
  def _handle_dry_run_migration(json_path: Path, results: dict[str, Any]) -> None
  def _migrate_handoff_to_task_file(json_path: Path, task: dict[str, Any], task_file_path: Path, terminal_id: str, results: dict[str, Any]) -> None
  def _process_single_handoff(json_path: Path, task_tracker_dir: Path, terminal_id: str, dry_run: bool, results: dict[str, Any]) -> None
  def migrate_handoffs(handoff_dir: Path, task_tracker_dir: Path, terminal_id: str | None, dry_run: bool) -> dict[str, Any]
  def _truncate_active_files(handoff_data: dict[str, Any]) -> None
  def _truncate_next_steps(handoff_data: dict[str, Any]) -> None
  def _truncate_handover_lists(handoff_data: dict[str, Any]) -> None
  def _truncate_list_keep_recent(handoff_data: dict[str, Any], field_name: str, max_entries: int) -> None
  def _warn_if_oversized(handoff_data: dict[str, Any], max_bytes: int) -> None
  def validate_handoff_size(handoff_data: dict[str, Any]) -> dict[str, Any]
  def _validate_checkpoint_chain_field_types(handoff_data: dict[str, Any]) -> None
  def _add_missing_checkpoint_chain_fields(handoff_data: dict[str, Any]) -> None
  def migrate_checkpoint_chain_fields(handoff_data: dict[str, Any]) -> dict[str, Any]
  def main() -> int

### `scripts\models.py`
  class HandoffCheckpoint
    def _validate_progress_percent(progress_percent: int) -> None
    def _validate_checksum(checksum: str) -> None
    def to_dict(self) -> dict[str, Any]
    def from_dict(cls, data: dict[str, Any]) -> HandoffCheckpoint

### `scripts\protocol.py`
  class HandoffStorage
    def save_handoff(self, task_name: str, terminal_id: str, data: dict[str, Any]) -> Path
    def load_handoff(self, task_name: str, terminal_id: str, strict: bool) -> dict[str, Any] | None
    def list_handoffs(self, task_name: str, terminal_id: str) -> list[Path]
    def delete_handoff(self, task_name: str, terminal_id: str, version: int) -> bool

### `scripts\tests\conftest.py`
  def handoff_test_root(tmp_path, monkeypatch)

### `scripts\tests\test_handoff_hooks.py`
  def _write_transcript(path: Path, entries: list[dict]) -> None
  def test_detect_session_type_prefers_planning_keywords()
  def test_detect_planning_session_creates_approval_blocker()
  def test_precompact_hook_writes_v2_envelope(tmp_path, monkeypatch)

### `scripts\tests\test_hook_manifest_naming.py`
  def test_snapshot_hooks_use_namespaced_entrypoints() -> None

### `scripts\tests\test_hook_schema_validation.py`
  class TestHookSchemaConstants
    def test_approve_value_is_string(self)
    def test_block_value_is_string(self)
    def test_valid_decisions_set_contains_constants(self)
    def test_valid_decisions_only_contains_known_values(self)
  class TestSchemaValidation
    def test_approve_decision_is_valid(self)
    def test_block_decision_is_valid(self)
    def test_allow_decision_is_invalid(self)
    def test_unknown_decision_is_invalid(self)
    def test_missing_decision_is_valid(self)
    def test_assert_valid_raises_on_invalid(self)
  class TestActualHookOutputSchema
    def mock_transcript(self, tmp_path: Path) -> Path
    def test_precompact_hook_output_is_schema_valid(self, tmp_path: Path, mock_transcript: Path)
    def test_session_start_hook_output_is_schema_valid(self, tmp_path: Path, mock_transcript: Path)
  class TestNoMagicStringsInHooks
    def test_precompact_uses_approve_constant(self)
    def test_session_start_uses_approve_constant(self)

### `scripts\tests\test_ups_task_injector.py`
  def _write_handoff(handoff_dir: Path, terminal_id: str, goal: str, next_step: str | None, status: str, age_minutes: int) -> None
  def _context(tmp_path: Path) -> dict
  def test_build_injection_with_next_step()
  def test_build_injection_without_next_step()
  def test_build_injection_contains_resume_warning()

### `skills\track\track.py`
  def _ensure_track_dir() -> Path
  def _current_thread_file_for_terminal(terminal_id: str) -> Path
  def _threads_dir() -> Path
  def _detect_terminal_id() -> str
  def _normalize_id(raw_id: str, source: str) -> str
  def _make_thread_id(intent: str) -> str
  def _get_current_thread_id() -> str | None
  def _set_current_thread(thread_id: str | None) -> None
  def _load_thread(thread_id: str) -> dict[str, Any]
  def _save_thread(thread_id: str, data: dict[str, Any]) -> None
  def _list_threads(include_archived: bool) -> list[dict[str, Any]]
  def _reconstruct_from_terminal() -> dict[str, Any] | None
  def _reconstruct() -> dict[str, Any]
  def cmd_brief() -> None
  def _show_brief(data: dict[str, Any]) -> None
  def cmd_capture(intent: str) -> None
  def cmd_next(step: str) -> None
  def cmd_done(checkpoint: str) -> None
  def cmd_blocker(blocker: str) -> None
  def cmd_list() -> None
  def cmd_info() -> None
  def cmd_archive() -> None
  def cmd_prune(older_than_days: int) -> None
  def main() -> None

### `sub_agent_invocation_example.py`
  class SubAgentTask
    def format_for_task_tool(self) -> dict
    def to_yaml_comment_block(self) -> str
  def create_discovery_orchestrator_task(goal, search_paths, constraints, relevant_patterns)
  def create_investigation_task(target, investigation_type, context)

### `tests\conftest.py`
  def real_transcript_sample()
  def make_transcript_entry(tool_name: str, file_path: str, tool_use_id: str)
  def handoff_test_root(tmp_path, monkeypatch)
  def pytest_sessionstart(session)

### `tests\test_canonical_goal_extraction.py`
  def create_test_transcript(entries, output_path)
  def test_case_1_skip_meta_instructions()
  def test_case_2_skip_side_question()
  def test_case_3_session_boundary()
  def test_is_meta_instruction()
  def test_is_same_topic()
  def test_detect_session_boundary()
  def test_performance_1000_entries()
  def test_case_4_same_topic_returns_newest()
  def test_case_5_skip_conversational_question()
  def test_is_meta_discussion()

### `tests\test_conflict_detection.py`
  def _get_current_head_short(project_root: Path) -> str | None
  def _build_restore_message_with_conflict_check(envelope: dict, project_root: Path) -> str
  class TestConflictDetection
    def test_no_environment_context(self)
    def test_env_context_but_no_git_state(self)
    def test_git_state_but_no_last_commit(self)
    def test_matching_hash_no_warning(self)
    def test_different_hash_produces_warning(self)
    def test_empty_hash_string_no_warning(self)
    def test_non_string_hash_no_warning(self)
    def test_non_dict_env_context_no_warning(self)
    def test_non_git_directory_graceful(self, tmp_path)

### `tests\test_context_gathering_boundaries.py`
  def test_gather_context_basic()
  def test_gather_context_stops_at_session_boundary()
  def test_gather_context_stops_on_topic_shift()
  def test_gather_context_respects_max_messages()
  def test_detect_session_boundary_new_session()
  def test_detect_session_boundary_same_session()
  def test_is_same_topic_related_messages()
  def test_is_same_topic_different_messages()
  def test_gather_context_empty_transcript()

### `tests\test_continuation_rule.py`
  def test_continuation_rule_frames_goal_as_inference()
  def test_continuation_rule_prevents_passive_aggressive_deflection()
  def test_previous_session_does_not_leak_path()
  def test_n_2_transcript_path_none_is_handled()
  def test_restore_message_surfaces_session_identity_work_state_and_questions()
  def test_transcript_chain_preserves_full_path_in_envelope()
  def test_transcript_chain_walks_via_n_2_transcript_path()
  def test_compact_restore_format_unchanged()

### `tests\test_correction_message_detection.py`
  class TestIsCorrectionMessage
    def test_no_task_is_not_about_detected(self)
    def test_thats_not_what_i_asked_detected(self)
    def test_you_did_wrong_task_detected(self)
    def test_you_are_wrong_about_detected(self)
    def test_i_didnt_ask_for_detected(self)
    def test_thats_incorrect_detected(self)
    def test_losing_mind_making_stuff_up_detected(self)
    def test_thats_not_what_i_meant_detected(self)
    def test_not_about_teaching_detected(self)
    def test_task_is_not_about_detected(self)
    def test_legitimate_task_not_filtered(self)
    def test_normal_task_with_negative_word_not_filtered(self)
    def test_mid_message_corrections_detected(self)
    def test_ai_state_criticism_detected(self)
    def test_general_correction_indicators_detected(self)
  class TestGoalExtractionWithCorrections
    def create_test_transcript(self, entries, output_path)
    def test_correction_heavy_conversation(self)
    def test_correction_then_task(self)
    def test_only_correction_messages(self)
    def test_normal_conversation_unchanged(self)

### `tests\test_dependency_state.py`
  def temp_dir(tmp_path: Path) -> Path
  def python_project(tmp_path: Path) -> Path
  def python_project_poetry(tmp_path: Path) -> Path
  def node_project(tmp_path: Path) -> Path
  def test_capture_dependency_state_no_package_manager(temp_dir: Path) -> None
  def test_capture_dependency_state_python_requirements(python_project: Path) -> None
  def test_capture_dependency_state_python_poetry(python_project_poetry: Path) -> None
  def test_capture_dependency_state_node(node_project: Path) -> None
  def test_capture_dependency_state_invalid_path() -> None
  def test_capture_dependency_state_subprocess_timeout(python_project: Path) -> None
  def test_capture_dependency_state_subprocess_error(python_project: Path) -> None
  def test_capture_dependency_state_prefers_poetry_over_pip(python_project_poetry: Path) -> None
  def test_capture_dependency_state_installed_packages_format(python_project: Path) -> None
  def test_capture_dependency_state_empty_directory(temp_dir: Path) -> None

### `tests\test_deterministic_checksums.py`
  def _payload()
  def test_compute_checksum_is_stable_for_same_payload()
  def test_compute_checksum_ignores_mutable_status_metadata()
  def test_compute_checksum_changes_when_core_payload_changes()

### `tests\test_edge_case_transcripts.py`
  def _write_transcript(path: Path, entries: list[dict]) -> None
  def test_empty_transcript_returns_unknown()
  def test_single_substantive_message()
  def test_single_meta_message()
  def test_single_correction_message()
  def test_single_very_short_message()
  def test_all_meta_transcript()
  def test_all_correction_transcript()
  def test_all_very_short_messages()
  def test_non_english_message_blocked()
  def test_malformed_transcript_entry_missing_type()
  def test_malformed_transcript_entry_missing_message()
  def test_malformed_transcript_entry_missing_content()
  def test_malformed_transcript_entry_content_not_array()
  def test_assistant_messages_only()
  def test_tool_use_messages_only()
  def test_question_then_instruction()
  def test_clarification_then_task()

### `tests\test_envelope_schema_validation.py`
  def _make_minimal_valid_envelope(tmp_path)
  def test_validate_envelope_accepts_valid_envelope(tmp_path)
  def test_validate_envelope_rejects_non_dict()
  def test_validate_envelope_rejects_missing_top_level_fields()
  def test_validate_envelope_rejects_wrong_top_level_types(tmp_path)
  def test_validate_envelope_rejects_missing_snapshot_fields()
  def test_validate_envelope_rejects_invalid_snapshot_status(tmp_path)
  def test_validate_envelope_rejects_invalid_progress_percent(tmp_path)
  def test_validate_envelope_rejects_invalid_decision_kind(tmp_path)
  def test_validate_envelope_rejects_invalid_evidence_type(tmp_path)
  def test_validate_envelope_rejects_broken_decision_refs(tmp_path)
  def test_validate_envelope_rejects_broken_evidence_refs(tmp_path)
  def test_validate_envelope_rejects_missing_checksum(tmp_path)
  def test_validate_envelope_rejects_checksum_mismatch(tmp_path)
  def test_validate_envelope_accepts_all_valid_statuses(tmp_path)
  def test_validate_envelope_accepts_all_valid_message_intents(tmp_path)
  def test_validate_envelope_accepts_all_valid_decision_kinds(tmp_path)
  def test_validate_envelope_accepts_all_valid_evidence_types(tmp_path)

### `tests\test_git_state.py`
  def non_git_dir(tmp_path: Path) -> Path
  def git_dir(tmp_path: Path) -> Path
  def git_repo_with_commit(git_dir: Path) -> Path
  def git_repo_with_uncommitted_changes(git_repo_with_commit: Path) -> Path
  def test_capture_git_state_non_git_directory(non_git_dir: Path) -> None
  def test_capture_git_state_clean_repo(git_repo_with_commit: Path) -> None
  def test_capture_git_state_with_uncommitted_changes(git_repo_with_uncommitted_changes: Path) -> None
  def test_capture_git_state_with_untracked_files(git_repo_with_commit: Path) -> None
  def test_capture_git_state_invalid_path() -> None
  def test_capture_git_state_subprocess_timeout(git_dir: Path) -> None
  def test_capture_git_state_subprocess_error(git_dir: Path) -> None
  def test_capture_git_state_detached_head(git_repo_with_commit: Path) -> None
  def test_capture_git_state_multiple_branches(git_repo_with_commit: Path) -> None
  def test_capture_git_state_staged_changes(git_repo_with_commit: Path) -> None

### `tests\test_handoff_context_preservation.py`
  def _write_transcript(path: Path, entries: list[dict]) -> None
  def test_context_extraction_with_multiple_user_messages()
  def test_context_extraction_stops_at_session_boundary()
  def test_context_extraction_truncates_long_messages()
  def test_context_extraction_handles_missing_transcript()
  def test_context_extraction_handles_empty_transcript()
  def test_build_restore_message_includes_context()
  def test_context_extraction_with_complex_message_format()
  def test_context_extraction_shows_last_5_when_more_than_5_messages()
  def test_context_extraction_filters_non_user_messages()

### `tests\test_handoff_full_integration.py`
  def _write_transcript(path: Path, entries: list[dict]) -> None
  def _make_simple_envelope(tmp_path: Path, session_id: str, goal: str) -> tuple[dict, str]
  def test_full_flow_session_compaction_to_restore(tmp_path)
  def test_full_flow_expired_envelope_rejected(tmp_path)
  def test_full_flow_envelope_checksum_validation(tmp_path)
  def test_full_flow_missing_state_graceful(tmp_path)

### `tests\test_handoff_integration.py`
  def _write_transcript(path: Path, entries: list[dict]) -> None
  def _run_hook(script_name: str, payload: dict) -> dict
  def _capture_v2_snapshot(tmp_path, monkeypatch, terminal_id: str, transcript_path: Path | None) -> tuple[Path, HandoffFileStorage]
  def test_full_compact_restore_cycle_consumes_snapshot(tmp_path, monkeypatch)
  def test_session_start_generic_startup_does_not_consume_snapshot(tmp_path, monkeypatch)
  def test_stale_snapshot_is_rejected_with_metadata_only_hint(tmp_path, monkeypatch)
  def test_tasks_snapshot_flows_through_handoff_pipeline(tmp_path, monkeypatch)
  def test_invalid_checksum_is_rejected_without_task_context(tmp_path, monkeypatch)
  def test_changed_transcript_rejects_restore_as_stale_snapshot(tmp_path, monkeypatch)
  def test_load_raw_handoff_exclude_session_id(tmp_path, monkeypatch)
  def test_transcript_chain_precompact_reads_prior_from_previous_handoff(tmp_path, monkeypatch)

### `tests\test_handoff_meta_discussion.py`
  class TestIsMetaDiscussion
    def test_so_youre_question_detected(self)
    def test_dont_understand_question_detected(self)
    def test_system_question_detected(self)
    def test_are_there_more_detected(self)
    def test_do_you_hate_detected(self)
    def test_legitimate_task_not_filtered(self)
    def test_skill_definition_detected(self)
    def test_meta_instruction_also_detected(self)
  class TestDecisionExtractionIntegration
    def test_conversational_fragment_not_decision(self)
    def test_legitimate_constraint_still_captured(self)

### `tests\test_handoff_regression_skill_capture.py`
  def _create_transcript(tmp_path: Path, entries: list[dict]) -> str
  class TestRegressionSkillDefinitionCaptureBug
    def test_regression_722_line_skill_definition_not_captured(self, tmp_path: Path) -> None
    def test_regression_mixed_skill_and_user_content(self, tmp_path: Path) -> None
    def test_regression_fallback_goal_does_not_capture_skill(self, tmp_path: Path) -> None
    def test_regression_user_goal_preserved_after_compaction(self, tmp_path: Path) -> None
  class TestRegressionSkillDefinitionEdgeCases
    def test_regression_multiple_skills_in_sequence(self, tmp_path: Path) -> None
    def test_regression_skill_definition_with_tool_use(self, tmp_path: Path) -> None

### `tests\test_handoff_skill_definition_filter.py`
  class TestIsMetaInstructionSkillDefinitions
    def test_skill_definition_detected_as_meta(self) -> None
    def test_skill_definition_variations(self) -> None
    def test_legitimate_user_message_not_filtered(self) -> None
  class TestBuildDecisionsSkillFilter
    def test_skill_definition_not_captured_as_decision(self) -> None
    def test_legitimate_constraint_captured_as_decision(self) -> None
  class TestGoalExtractionSkillFilter
    def test_fallback_goal_filters_skill_definition(self) -> None
    def test_skill_definition_in_goal_replaced_with_context(self) -> None
  class TestRegressionSkillCapture
    def test_skill_definition_not_captured_as_goal(self) -> None
    def test_skill_constraints_not_captured_as_decisions(self) -> None

### `tests\test_handoff_task_injector.py`
  def _make_envelope(goal: str, current_task: str, active_files: list[str] | None, pending_ops: list[dict] | None, next_step: str, n_1_transcript_path: str, n_2_transcript_path: str | None, progress_state: str, progress_percent: int) -> dict
  def _make_marker(handoff_path: str, terminal_id: str, age: float) -> dict
  class TestNoMarker
    def test_no_marker_returns_empty(self) -> None
  class TestExpiredMarker
    def test_expired_marker_returns_empty(self) -> None
  class TestMissingHandoffFile
    def test_missing_handoff_returns_empty_clears_marker(self) -> None
  class TestSuccessfulRecovery
    def _setup_valid_state(self, tmp: Path, terminal_id: str, envelope: dict) -> tuple[Path, Path]
    def test_valid_marker_injects_context(self) -> None
    def test_context_contains_goal(self) -> None
    def test_marker_cleared_after_injection(self) -> None
    def test_context_uses_compact_format_no_raw_transcript_path(self) -> None
    def test_context_contains_current_task(self) -> None
  class TestKillSwitch
    def test_disabled_by_env_var(self) -> None
  class TestTerminalScoping
    def test_different_terminals_use_different_markers(self) -> None
    def test_marker_name_sanitizes_special_chars(self) -> None

### `tests\test_handoff_ttl.py`
  def _write_envelope(path: Path, created_at: float | None) -> None
  def test_fresh_envelope_is_loaded(tmp_path)
  def test_expired_envelope_is_rejected(tmp_path)
  def test_boundary_envelope_at_ttl_limit(tmp_path)
  def test_missing_file_returns_none(tmp_path)

### `tests\test_intent_classification.py`
  class TestDetectMessageIntent
    def test_question_ends_with_question_mark(self)
    def test_question_starts_with_question_word(self)
    def test_instruction_default(self)
    def test_instruction_with_question_mark_polite_command(self)
    def test_question_word_in_instruction(self)
    def test_correction_detected(self)
    def test_meta_detected(self)
    def test_empty_returns_instruction(self)
    def test_none_returns_instruction(self)
    def test_various_whitespace_returns_instruction(self)
    def test_non_english_blocked(self)
    def test_english_messages_not_blocked(self)
  class TestIntentPrefixes
    def test_question_prefix(self)
    def test_instruction_prefix(self)
    def test_backward_compat_missing_intent_field(self)
    def test_backward_compat_none_intent(self)
    def test_invalid_intent_falls_back_to_default(self)
  class TestChecksumExclusion
    def test_message_intent_excluded_from_checksum(self)
    def test_old_handoff_validates_without_message_intent(self)
    def test_all_intent_values_produce_same_checksum(self)
  class TestMessageTypeValidation
    def test_invalid_intent_raises_error_in_snapshot_build(self)
  class TestIntentDetectionPerformance
    def test_intent_detection_performance_1000_messages(self)
    def test_goal_extraction_with_intent_performance(self)

### `tests\test_intent_integration.py`
  def create_test_transcript_with_message(message: str, temp_dir: Path, filename: str) -> Path
  def create_envelope_with_goal(goal: str, message_intent: str) -> dict
  class TestADRMotivatingScenario
    def test_adr_motivating_scenario(self)
  class TestPreCompactHookIntegration
    def test_precompact_captures_intent(self)
    def test_precompact_instruction_intent(self)
  class TestConcurrentHandoffCreation
    def test_concurrent_intent_detection(self)
    def test_concurrent_same_message_intent(self)
  class TestChecksumExclusionIntegration
    def test_all_intent_values_produce_same_checksum(self)
  class TestMessageTypeValidation
    def test_unsupported_language_uses_blocked_prefix(self)

### `tests\test_last_substantive_message_integration.py`
  def _write_transcript(path: Path, entries: list[dict]) -> None
  def test_bug_scenario_correction_message_then_task()
  def test_bug_scenario_topic_shift()
  def test_bug_scenario_multiple_substantive_messages_same_topic()
  def test_bug_scenario_all_messages_filtered()
  def test_message_intent_present_in_result()

### `tests\test_last_user_message.py`
  def test_last_user_message_full_transcript()
  def test_last_user_message_skips_meta_tags()
  def test_last_user_message_untruncated()
  def test_last_user_message_skips_dict_items()

### `tests\test_lifecycle_phase.py`
  class TestLifecyclePhaseConstants
    def test_valid_lifecycle_phases(self) -> None
    def test_lifecycle_phase_in_optional_fields(self) -> None
  class TestLifecyclePhaseValidation
    def test_valid_phases_accepted(self) -> None
    def test_invalid_phase_rejected(self) -> None
    def test_backward_compat_no_phase(self) -> None
  class TestDetectLifecyclePhase
    def test_planning_with_awaiting_approval_blocker(self) -> None
    def test_implementing_with_pending_operations(self) -> None
    def test_discussing_with_question_goal(self) -> None
    def test_implementing_with_task_mode_override(self) -> None
    def test_discussing_no_signals(self) -> None
  class TestDetectTaskMode
    def test_create_mode(self) -> None
    def test_implement_mode(self) -> None
    def test_none_mode(self) -> None
  class TestDynamicSectionsLifecycle
    def test_build_lifecycle_directive(self) -> None
    def test_directive_in_generate_for_non_implementing(self) -> None
    def test_no_directive_for_implementing(self) -> None
  class TestRestoreMessageLifecycleDirective
    def _make_envelope(self, lifecycle_phase: str | None) -> dict[str, Any]
    def test_restore_message_includes_directive_for_discussing(self) -> None
    def test_restore_message_no_directive_for_implementing(self) -> None
    def test_dynamic_restore_includes_lifecycle_phase(self) -> None
  class TestAccumulator
    def test_run_returns_empty_dict(self) -> None
    def test_run_no_error_on_failure(self) -> None
    def test_append_creates_file(self, tmp_path: Path) -> None
    def test_read_last_phase_default(self, tmp_path: Path) -> None
    def test_read_last_phase_from_jsonl(self, tmp_path: Path) -> None
    def test_phase_transition_approved_to_implementing(self) -> None
    def test_no_transition_from_implementing(self) -> None
  class TestHandoffFilesAccumulatedState
    def test_read_missing_file(self, tmp_path: Path) -> None
    def test_read_valid_jsonl(self, tmp_path: Path) -> None
    def test_read_corrupt_line_skipped(self, tmp_path: Path) -> None
    def test_truncate_removes_file(self, tmp_path: Path) -> None
    def test_truncate_nonexistent_ok(self, tmp_path: Path) -> None
  class TestEmptyGoalEdgeCases
    def test_empty_string_goal(self) -> None
    def test_whitespace_only_goal(self) -> None
    def test_empty_goal_with_active_files(self) -> None
  class TestInterspersedCorruptLines
    def test_read_mixed_valid_corrupt(self, tmp_path: Path) -> None
  class TestLifecyclePhaseChecksumRoundtrip
    def test_phase_in_envelope_validates(self) -> None
  class TestAccumulatorConcurrentAppends
    def test_concurrent_appends_no_corruption(self, tmp_path: Path) -> None
  class TestAccumulatedPhasePreference
    def test_accumulated_phase_overrides_inference(self, tmp_path: Path) -> None
    def test_no_accumulated_events_falls_back_to_implementing(self, tmp_path: Path) -> None

### `tests\test_p0_characterization.py`
  class TestP001_FileLockTOCTOU
    def test_file_exists_and_contains_toctou_pattern(self)
  class TestP002_GitSubprocessTimeout
    def test_git_state_contains_sequential_subprocess_calls(self)
  class TestP003_StaleLockCleanupTOCTOU
    def test_handoff_store_contains_stale_lock_cleanup(self)
  class TestP004_ValidateEnvelopeTOCTOU
    def test_handoff_v2_contains_validate_envelope(self)
  class TestP005_VerifyEvidenceFreshnessTOCTOU
    def test_handoff_v2_contains_verify_evidence_freshness(self)
  class TestP006_FileDescriptorLeak
    def test_terminal_registry_contains_save_registry(self)
  class TestP007_TempFileLeak
    def test_handoff_store_contains_atomic_write_with_retry(self)

### `tests\test_p0_filelock_toctou.py`
  class TestFileLockTOCTOUCharacterization
    def temp_lock_file(self, tmp_path: Path) -> Path
    def test_characterization_file_opens_before_lock(self, temp_lock_file: Path) -> None
    def test_characterization_lock_fd_set_only_after_lock_success(self, temp_lock_file: Path) -> None
    def test_characterization_gap_between_open_and_lock(self, temp_lock_file: Path) -> None
    def test_current_implementation_windows_uses_separate_calls(self) -> None
    def test_current_implementation_unix_uses_separate_calls(self) -> None
    def test_expected_behavior_atomic_lock_needed(self, temp_lock_file: Path) -> None
    def _verify_atomic_lock_used(self, lock: FileLock) -> None

### `tests\test_pending_operations_extraction.py`
  def make_tool_use_entry(tool_name: str, tool_input: dict) -> dict
  class TestPendingOperationsToolUseDetection
    def test_detect_read_operation(self, tmp_path)
    def test_detect_grep_investigation(self, tmp_path)
    def test_detect_glob_investigation(self, tmp_path)
    def test_detect_edit_operation(self, tmp_path)
    def test_detect_bash_test_operation(self, tmp_path)
    def test_detect_skill_operation(self, tmp_path)
  class TestPendingOperationsKeywordFallback
    def test_detect_review_keywords(self, tmp_path)
    def test_detect_analyze_keywords(self, tmp_path)
    def test_detect_investigate_keywords(self, tmp_path)
    def test_detect_debug_keywords(self, tmp_path)
    def test_detect_search_keywords(self, tmp_path)
  class TestPendingOperationsPriority
    def test_tool_use_over_keywords(self, tmp_path)
  class TestPendingOperationsLimits
    def test_max_five_operations(self, tmp_path)
    def test_empty_transcript(self, tmp_path)
    def test_no_pending_operations(self, tmp_path)
  class TestInvestigationOperationDetails
    def test_investigation_with_file_target(self, tmp_path)
    def test_grep_with_pattern_target(self, tmp_path)
  class TestPendingOperationsCompletedExclusion
    def _make_tool_result_entry(self, tool_use_id: str) -> dict
    def test_completed_read_excluded(self, tmp_path)
    def test_completed_ops_excluded_in_progress_kept(self, tmp_path)
    def test_all_completed_yields_empty(self, tmp_path)
  class TestPendingOperationsReverseOrder
    def test_most_recent_first(self, tmp_path)

### `tests\test_performance_canonical_goal.py`
  def create_synthetic_transcript(entry_count: int, output_path: Path) -> None
  def test_performance_baseline_100_entries(tmp_path: Path) -> None
  def test_performance_baseline_1000_entries(tmp_path: Path) -> None

### `tests\test_precompact_capture_improvements.py`
  def _create_test_transcript(tmp_path: Path, entries: list[dict]) -> str
  def test_active_files_accepts_paths_without_extensions(tmp_path)
  def test_active_files_rejects_urls(tmp_path)
  def test_decisions_limited_to_recent_entries(tmp_path)
  def test_decisions_filters_noise_from_current_session(tmp_path)
  def test_active_files_cap_at_10_entries(tmp_path)

### `tests\test_restoration_message.py`
  def _sample_payload()
  def test_build_restore_message_contains_core_sections()
  def test_build_stale_hint_exposes_only_metadata()

### `tests\test_skill_invocation_goal_drift.py`
  class TestSlashCommandSkip
    def test_slash_command_with_args_is_meta(self)
    def test_slash_command_with_flags_is_meta(self)
    def test_slash_command_alone_not_meta(self)
    def test_slash_command_uppercase_with_args_is_meta(self)
    def test_regular_sentence_not_meta(self)
  class TestRestoreMessageSkillWarning
    def _build_payload(self, pending_operations)
    def test_in_progress_skill_triggers_warning_continuation(self)
    def test_completed_skill_no_warning(self)
    def test_no_pending_operations_standard_rule(self)
    def test_other_operation_types_no_warning(self)
  class TestDefensiveFallback
    def test_fallback_skips_when_preceding_is_none(self, tmp_path)
    def test_fallback_skips_when_preceding_is_meta_invocation(self)
    def test_fallback_uses_valid_preceding_message(self)
    def test_fallback_handles_whitespace_only_preceding(self)

### `tests\test_state_transition_validation.py`
  def _pending_snapshot() -> dict
  def test_valid_transition_pending_to_consumed()
  def test_valid_transition_pending_to_rejected_stale()
  def test_valid_transition_pending_to_rejected_invalid()
  def test_invalid_transition_from_consumed_to_pending()
  def test_invalid_transition_from_rejected_stale_to_consumed()
  def test_invalid_transition_to_unknown_status()
  def test_double_rejection_is_invalid()

### `tests\test_task_identity_manager_terminal_scope.py`
  def test_global_task_name_env_var_is_ignored(monkeypatch, tmp_path)
  def test_active_command_is_terminal_scoped(tmp_path)
  def test_legacy_shared_active_command_file_is_ignored(tmp_path)

### `tests\test_terminal_detection_registry_fallback.py`
  def isolated_registry(tmp_path, monkeypatch)
  def _write_entry(registry_path: Path) -> None
  class TestRegistryLookupBySessionId
    def test_returns_matching_terminal_id(self, isolated_registry)
    def test_returns_most_recent_when_session_id_repeats(self, isolated_registry)
    def test_unknown_session_returns_empty(self, isolated_registry)
  class TestRegistryLookupByCwd
    def test_returns_matching_cwd_terminal(self, isolated_registry, tmp_path)
    def test_session_id_takes_precedence_over_cwd(self, isolated_registry, tmp_path)
  class TestFallbackChainOrder
    def test_synthetic_only_when_all_sources_fail(self, isolated_registry)
    def test_registry_match_preempts_synthetic(self, isolated_registry)
    def test_empty_session_id_returns_empty_string(self, isolated_registry)
  class TestRegistryFailureModes
    def test_missing_registry_file_returns_empty(self, tmp_path, monkeypatch)
    def test_corrupt_lines_are_skipped(self, isolated_registry)

### `tests\test_terminal_isolation.py`
  def _payload(terminal_id: str) -> dict
  def test_storage_keeps_terminals_separate(tmp_path)
  def test_storage_rejects_wrong_terminal_file_contents(tmp_path)
  class TestFallbackTerminalDetection
    def test_fallback_returns_env_when_available(self, monkeypatch)
    def test_fallback_returns_session_id_derived_when_all_sources_fail(self, monkeypatch)
    def test_fallback_returns_empty_when_no_session_id_and_all_sources_fail(self, monkeypatch)
    def test_resolve_terminal_key_uses_session_id_fallback(self, monkeypatch)

### `tests\test_three_message_iteration.py`
  def _write_transcript(path: Path, entries: list[dict]) -> None
  def test_three_substantive_messages_returns_last_one()

### `tests\test_tool_result_skipping.py`
  class TestToolResultSkipping
    def test_skip_tool_result_only_entries(self, tmp_path)
    def test_extract_real_user_message_after_tool_result(self, tmp_path)
    def test_tool_result_with_teammate_messages(self, tmp_path)
    def test_command_message_not_treated_as_tool_result(self, tmp_path)

### `tests\test_transcript_extract.py`
  class TestExtractUserMessageFromBlocker
    def test_dict_with_prefix(self) -> None
    def test_dict_with_prefix_extra_whitespace(self) -> None
    def test_string_with_prefix(self) -> None
    def test_dict_without_prefix(self) -> None
    def test_string_without_prefix(self) -> None
    def test_none_blocker(self) -> None
    def test_empty_dict(self) -> None
    def test_dict_with_empty_description(self) -> None
    def test_dict_missing_description_field(self) -> None
    def test_empty_string(self) -> None
    def test_prefix_only_empty_after(self) -> None
    def test_invalid_type(self) -> None
    def test_long_message_with_prefix(self) -> None
    def test_multiline_description(self) -> None
    def test_prefix_case_sensitive(self) -> None
    def test_partial_prefix_match(self) -> None
    def test_unicode_characters(self) -> None
    def test_real_compaction_example(self) -> None

### `tests\test_uci_fixes.py`
  def temp_project_root(tmp_path: Path) -> Path
  def valid_transcript(temp_project_root: Path) -> Path
  def valid_v2_payload(valid_transcript: Path) -> dict
  class TestPERF001_ChecksumFromMemory
    def test_checksum_validated_from_memory_before_write(self, temp_project_root: Path, valid_v2_payload: dict) -> None
    def test_checksum_mismatch_detected_before_write(self, temp_project_root: Path, valid_v2_payload: dict) -> None
  class TestLOGIC001_TOCTOU_Fix
    def test_temp_file_verified_before_atomic_move(self, temp_project_root: Path, valid_v2_payload: dict) -> None
    def test_checksum_mismatch_from_memory(self, temp_project_root: Path, valid_v2_payload: dict) -> None
  class TestLOGIC002_MissingChecksum
    def test_missing_checksum_rejected_in_validation(self, temp_project_root: Path, valid_transcript: Path) -> None
    def test_save_without_checksum_fails(self, temp_project_root: Path, valid_transcript: Path) -> None
  class TestSEC001_PathTraversal
    def test_path_traversal_via_dot_dot_rejected(self, temp_project_root: Path, valid_transcript: Path) -> None
    def test_valid_project_path_accepted(self, temp_project_root: Path, valid_v2_payload: dict) -> None
    def test_restore_uses_explicit_project_root_for_evidence_validation(self, temp_project_root: Path) -> None
  class TestSEC002_SanitizedErrorMessages
    def test_transcript_error_sanitized(self, temp_project_root: Path) -> None
  class TestQUAL002_ConsistentLogLevels
    def test_checksum_mismatch_logs_error(self, temp_project_root: Path, valid_v2_payload: dict, caplog) -> None
  class TestLOGIC003_TestDetectionFix
    def test_test_transcript_detection(self, temp_project_root: Path) -> None
  class TestQUAL005_TestWarningLevel
    def test_test_transcript_error_level(self) -> None
  class TestWalkUpBoundary
    def test_transcript_beyond_walkup_limit_rejected(self, tmp_path: Path) -> None
    def test_transcript_within_walkup_limit_accepted(self, tmp_path: Path) -> None
    def test_env_root_overrides_walkup(self, tmp_path: Path) -> None
  class TestIntegration_ChecksumFlow
    def test_end_to_end_checksum_flow(self, temp_project_root: Path, valid_transcript: Path) -> None
    def test_concurrent_safety(self, temp_project_root: Path, valid_transcript: Path) -> None

### `tests\test_variable_shadowing_fix.py`
  class TestVariableShadowingFix
    def test_blocker_dict_remains_intact_after_extraction(self) -> None
    def test_string_blocker_also_works(self) -> None
    def test_none_blocker_handling(self) -> None
    def test_real_compaction_scenario(self) -> None
    def test_handoff_workflow_integrity(self) -> None

### `tests\test_visual_context.py`
  def test_extract_visual_context()
  def test_extract_visual_context_from_screenshot_reference()

### `tests\verify_field_name_fix.py`
  def test_field_access()

## DIRECTORY / FILE INDEX

- `./`
  - `sub_agent_invocation_example.py`
- `assets\banners/`
  - `generate_banner.py`
- `core/`
  - `__init__.py`
- `core\hooks/`
  - `__init__.py`
- `core\hooks\__lib/`
  - `__init__.py`
- `examples/`
  - `basic_usage.py`
- `scripts/`
  - `__init__.py`
  - `checkpoint_chain.py`
  - `checkpoint_ops.py`
  - `cli.py`
  - `config.py`
  - `fix_test_imports.py`
  - `migrate.py`
  - `models.py`
  - `protocol.py`
- `scripts\hooks/`
  - `PreCompact_commitment_tracker.py`
  - `PreCompact_snapshot_capture.py`
  - `PreCompact_workflow_checkpoint.py`
  - `SessionStart_snapshot_restore.py`
  - `SessionStart_tldr.py`
  - `__init__.py`
  - `precompact_imports_patch.py`
  - `snapshot_PreCompact.py`
  - `snapshot_SessionEnd_tldr.py`
  - `snapshot_SessionStart.py`
  - `snapshot_UserPromptSubmit.py`
- `scripts\hooks\__lib/`
  - `__init__.py`
  - `architecture_capture.py`
  - `capture_cache.py`
  - `dependency_state.py`
  - `dynamic_sections.py`
  - `error_capture.py`
  - `git_state.py`
  - `handover.py`
  - `hook_input_validation.py`
  - `hook_schema.py`
  - `parallel_capture.py`
  - `project_root.py`
  - `session_registry.py`
  - `snapshot_accumulator.py`
  - `snapshot_files.py`
  - `snapshot_store.py`
  - `snapshot_v2.py`
  - `task_identity_manager.py`
  - `terminal_detection.py`
  - `terminal_file_registry.py`
  - `test_state.py`
  - `transcript.py`
  - `user_intent.py`
  - `validation_utils.py`
- `scripts\tests/`
  - `__init__.py`
  - `conftest.py`
  - `test_handoff_hooks.py`
  - `test_hook_manifest_naming.py`
  - `test_hook_schema_validation.py`
  - `test_ups_task_injector.py`
- `skills\track/`
  - `track.py`
- `tests/`
  - `add_non_english_tests.py`
  - `conftest.py`
  - `test_canonical_goal_extraction.py`
  - `test_conflict_detection.py`
  - `test_context_gathering_boundaries.py`
  - `test_continuation_rule.py`
  - `test_correction_message_detection.py`
  - `test_dependency_state.py`
  - `test_deterministic_checksums.py`
  - `test_edge_case_transcripts.py`
  - `test_envelope_schema_validation.py`
  - `test_git_state.py`
  - `test_handoff_context_preservation.py`
  - `test_handoff_full_integration.py`
  - `test_handoff_integration.py`
  - `test_handoff_meta_discussion.py`
  - `test_handoff_regression_skill_capture.py`
  - `test_handoff_skill_definition_filter.py`
  - `test_handoff_task_injector.py`
  - `test_handoff_ttl.py`
  - `test_intent_classification.py`
  - `test_intent_integration.py`
  - `test_last_substantive_message_integration.py`
  - `test_last_user_message.py`
  - `test_lifecycle_phase.py`
  - `test_p0_characterization.py`
  - `test_p0_filelock_toctou.py`
  - `test_pending_operations_extraction.py`
  - `test_performance_canonical_goal.py`
  - `test_precompact_capture_improvements.py`
  - `test_restoration_message.py`
  - `test_skill_invocation_goal_drift.py`
  - `test_state_transition_validation.py`
  - `test_task_identity_manager_terminal_scope.py`
  - `test_terminal_detection_registry_fallback.py`
  - `test_terminal_isolation.py`
  - `test_three_message_iteration.py`
  - `test_tool_result_skipping.py`
  - `test_transcript_extract.py`
  - `test_uci_fixes.py`
  - `test_variable_shadowing_fix.py`
  - `test_visual_context.py`
  - `verify_field_name_fix.py`

---

*Generated by /gitpack - 2026-05-13*