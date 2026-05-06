# snapshot — SIGNATURE TOC

Generated: 2026-05-05T07:38:20.608721
Files: 97


## __lib


### core\hooks\__lib\__init__.py


### scripts\hooks\__lib\__init__.py


### scripts\hooks\__lib\architecture_capture.py

- def capture_architectural_context(project_root) -> dict | None
- def _find_adr_files(project_root) -> list[str]
- def _parse_adr_files(project_root, adr_files) -> tuple[list[str], list[str]]
- def _clean_extracted_text(text) -> str

### scripts\hooks\__lib\capture_cache.py

- class CaptureCache(attrs=[], methods=['__init__', 'get', 'set', 'clear', 'generate_key', 'hash_path', 'hash_paths'])
- def __init__(self, ttl) -> None
- def get(self, key) -> dict | None
- def set(self, key, value) -> None
- def clear(self) -> None
- def generate_key(capture_type, project_root, path_hash) -> str
- def hash_path(path) -> str
- def hash_paths(paths) -> str

### scripts\hooks\__lib\dependency_state.py

- def capture_dependency_state(project_root) -> dict | None
- def _detect_package_manager(project_path) -> str | None
- def _command_available(cmd) -> bool
- def _get_installed_packages(package_manager, project_path) -> list[dict]
- def _get_pip_packages() -> list[dict]
- def _get_poetry_packages(project_path) -> list[dict]
- def _get_pipenv_packages(project_path) -> list[dict]
- def _get_npm_packages(package_manager) -> list[dict]

### scripts\hooks\__lib\dynamic_sections.py

- def _get_session_id_from_env() -> str
- def load_air_gaps() -> list[dict[str, Any]]
- def has_problem(session_data) -> bool
- def has_actions(session_data) -> bool
- def has_decisions(session_data) -> bool
- def has_tasks(session_data) -> bool
- def has_air_gaps(session_data) -> bool
- def has_learning(session_data) -> bool
- def build_premortem_section(session_data) -> str
- def build_context_section(session_data) -> str
- def build_problem_section(session_data) -> str
- def build_analysis_section(session_data) -> str
- def build_solution_section(session_data) -> str
- def build_lessons_section(session_data) -> str
- def build_actions_section(session_data) -> str
- def build_decisions_section(session_data) -> str
- def build_tasks_section(session_data) -> str
- def build_quick_argument_section(session_data) -> str
- def generate_handoff_content(session_data) -> str
- def calculate_quality_score_dynamic(session_data) -> float

### scripts\hooks\__lib\error_capture.py

- def capture_recent_errors(transcript, project_root) -> dict | None
- def _extract_errors(transcript) -> list[dict]
- def _classify_error(error_message) -> str
- def _filter_terminal_specific_errors(errors) -> list[dict]

### scripts\hooks\__lib\git_state.py

- def capture_git_state(project_root) -> dict | None
- def _get_current_branch(project_path) -> str
- def _has_uncommitted_changes(project_path) -> bool
- def _get_last_commit(project_path) -> dict | None

### scripts\hooks\__lib\handover.py

- class HandoverData(attrs=['decisions', 'patterns_learned', 'controversial_decisions', 'session_objectives'], methods=[])
- class HandoverBuilder(attrs=[], methods=['__init__', '_extract_session_objectives', 'build'])
- def __init__(self, project_root, transcript_parser) -> 
- def _extract_session_objectives(objectives_file, max_objectives) -> list[str]
- def build(self, task_name) -> dict[str, Any]

### scripts\hooks\__lib\hook_input_validation.py

- class HookInputError(attrs=[], methods=['__init__'])
- def validate_hook_input(input_data, hook_type) -> None
- def __init__(self, message, field_name) -> 

### scripts\hooks\__lib\hook_schema.py

- def validate_hook_output(output, hook_type) -> list[str]
- def assert_valid_hook_output(output, hook_type) -> None

### scripts\hooks\__lib\parallel_capture.py

- def capture_all_parallel(project_root, transcript) -> dict
- def _capture_git_state(project_root) -> dict | None
- def _capture_dependency_state(project_root) -> dict | None
- def _capture_test_state(project_root) -> dict | None
- def _capture_architectural_context(project_root, transcript) -> dict | None

### scripts\hooks\__lib\project_root.py

- def detect_project_root(transcript_path, current_dir, max_depth, strict) -> Path

### scripts\hooks\__lib\session_registry.py

- def query_registry() -> list[dict]

### scripts\hooks\__lib\snapshot_accumulator.py

- def _get_accumulator_path(terminal_id, project_root) -> Path
- def _append_event(path, event) -> None
- def _read_last_phase(accum_path) -> str
- def _detect_phase_transition(tool_name, tool_input, current_phase) -> str | None
- def run(data) -> dict[str, Any]

### scripts\hooks\__lib\snapshot_files.py

- class SnapshotFileStorage(attrs=[], methods=['__init__', '_validate_terminal_id', '_handoff_file_for_payload', 'save_handoff', 'load_handoff', 'load_raw_handoff', 'update_snapshot_status', 'update_snapshot_status_from_payload', 'read_accumulated_state', 'truncate_accumulated_state', 'delete_handoff'])
- def __init__(self, project_root, terminal_id) -> 
- def _validate_terminal_id(terminal_id) -> None
- def _handoff_file_for_payload(self, payload) -> Path
- def save_handoff(self, payload) -> Path | bool
- def load_handoff(self) -> dict[str, Any] | None
- def load_raw_handoff(self, exclude_session_id) -> dict[str, Any] | None
- def update_snapshot_status(self) -> bool
- def update_snapshot_status_from_payload(self, payload) -> bool
- def read_accumulated_state(self) -> list[dict[str, Any]]
- def truncate_accumulated_state(self) -> bool
- def delete_handoff(self) -> bool
- def _get_mtime(p) -> float

### scripts\hooks\__lib\snapshot_store.py

- class FileLock(attrs=[], methods=['__init__', '_try_acquire_lock_once', 'acquire', '_check_and_remove_stale_lock', 'release', '__enter__', '__exit__'])
- def atomic_write_with_retry(temp_path, target_path, max_retries) -> None
- def atomic_write_with_validation(data, target_path, max_retries) -> dict[str, Any]
- def _truncate_text_field(text, max_length) -> str
- def _truncate_list_with_marker(items, max_items) -> list[Any]
- def _truncate_list_keep_recent(items, max_items) -> list[Any]
- def _truncate_handover_section(handover) -> dict[str, Any]
- def _apply_last_resort_truncation(validated) -> dict[str, Any]
- def _validate_handoff_data_size(handoff_data, cached_json) -> dict[str, Any]
- def calculate_quality_score(handoff_data) -> float
- def get_quality_rating(score) -> str
- def compute_snapshot_checksum(snapshot_internal) -> str
- class SnapshotStore(attrs=[], methods=['__init__', '_validate_terminal_id', 'build_handoff_data', 'create_continue_session_task'])
- def __init__(self, lock_file_path, timeout, stale_age) -> 
- def _try_acquire_lock_once(self) -> bool
- def acquire(self) -> bool
- def _check_and_remove_stale_lock(self) -> None
- def release(self) -> None
- def __enter__(self) -> FileLock
- def __exit__(self, exc_type, exc_val, exc_tb) -> None
- def __init__(self, project_root, terminal_id) -> 
- def _validate_terminal_id(self, terminal_id) -> None
- def build_handoff_data(self, task_name, progress_pct, blocker, files_modified, next_steps, handover, modifications, calculate_quality, pending_operations) -> dict[str, Any]
- def create_continue_session_task(self, task_name, task_id, handoff_metadata) -> None
- def utcnow_iso() -> str
- def _create_empty_task_data() -> dict[str, Any]

### scripts\hooks\__lib\snapshot_v2.py

- class SnapshotValidationError(attrs=[], methods=[])
- class RestoreDecision(attrs=['ok', 'reason', 'envelope'], methods=[])
- def utcnow() -> datetime
- def iso_now() -> str
- def parse_iso8601(value) -> datetime
- def make_decision_id() -> str
- def make_evidence_id() -> str
- def _normalize_for_checksum(payload) -> dict[str, Any]
- def compute_checksum(payload) -> str
- def compute_file_content_hash(path) -> str | None
- def _format_snapshot_item(entry) -> str
- def _build_restore_state(snapshot, decisions_by_id) -> dict[str, Any]
- def _render_restore_state_lines(state) -> list[str]
- def _render_restore_message_verbose(state) -> str
- def _render_restore_message_compact(state) -> str
- def _require_fields(obj, fields, prefix) -> None
- def validate_envelope(payload) -> None
- def build_resume_snapshot() -> dict[str, Any]
- def build_envelope() -> dict[str, Any]
- def mark_snapshot_status(payload) -> dict[str, Any]
- def evaluate_for_restore(payload) -> RestoreDecision
- def verify_evidence_freshness(payload) -> str | None
- def build_restore_message(payload) -> str
- def build_restore_message_compact(payload) -> str
- def build_restore_message_dynamic(payload) -> str
- def build_stale_hint(payload, reason) -> str
- def build_no_snapshot_hint(reason) -> str
- def short_task_name(goal) -> str
- def ensure_progress_state(blockers, pending_operations) -> str
- def _extract_and_format_user_context(transcript_path, max_messages) -> str | None

### scripts\hooks\__lib\task_identity_manager.py

- class TaskMetadata(attrs=['task_name', 'task_id', 'started', 'checksum', 'source'], methods=[])
- class TaskIdentityManager(attrs=[], methods=['__init__', '_require_stateful_terminal', '_is_metadata_fresh', 'get_current_task', '_is_valid_task_name', '_from_env_var', '_from_session_file', '_from_compact_metadata', '_ask_user', 'set_current_task', 'store_compact_metadata', 'register_task_worktree_mapping', 'record_active_command', 'clear_active_command', '_get_transient_task_id', 'cleanup_stale_terminal_files'])
- def __init__(self, project_root, terminal_id) -> None
- def _require_stateful_terminal(self) -> bool
- def _is_metadata_fresh(timestamp_str, max_age_seconds) -> bool
- def get_current_task(self) -> str | None
- def _is_valid_task_name(self, task_name) -> bool
- def _from_env_var(self) -> str | None
- def _from_session_file(self) -> str | None
- def _from_compact_metadata(self) -> str | None
- def _ask_user(self) -> str | None
- def set_current_task(self, task_name) -> bool
- def store_compact_metadata(self, task_name, handoff_id) -> bool
- def register_task_worktree_mapping(self, task_name, branch) -> bool
- def record_active_command(self, command, phase, metadata) -> bool
- def clear_active_command(self) -> bool
- def _get_transient_task_id(self) -> str | None
- def cleanup_stale_terminal_files(self, max_age_hours) -> int

### scripts\hooks\__lib\terminal_detection.py

- def _try_import_skill_guard() -> None
- def _fallback_detect_terminal_id() -> str
- def detect_terminal_id() -> str
- def resolve_terminal_key(terminal_id) -> str

### scripts\hooks\__lib\terminal_file_registry.py

- class TerminalFileRegistry(attrs=[], methods=['__init__', '_validate_terminal_id', 'record_access', 'get_recent_files', '_load_registry', '_save_registry', 'cleanup_expired'])
- def __init__(self, project_root, terminal_id, ttl_hours) -> 
- def _validate_terminal_id(terminal_id) -> None
- def record_access(self, file_path) -> None
- def get_recent_files(self, max_files) -> list[str]
- def _load_registry(self) -> dict[str, Any]
- def _save_registry(self, registry) -> None
- def cleanup_expired(self) -> int

### scripts\hooks\__lib\test_state.py

- def capture_test_state(project_root) -> dict | None
- def _find_test_files(project_root) -> list[str]
- def _parse_test_results(project_root, test_files) -> dict[str, int]
- def _get_coverage(project_root) -> float | None
- def _is_pytest_project(project_root, test_files) -> bool
- def _is_jest_project(project_root, test_files) -> bool
- def _is_cargo_project(project_root, test_files) -> bool

### scripts\hooks\__lib\transcript.py

- def _contains_non_ascii(text) -> bool
- def detect_message_intent(message) -> MessageIntent
- class StructureInfo(attrs=['type', 'search_keys'], methods=[])
- class BlockerDef(attrs=['description'], methods=[])
- class MessageDict(attrs=['role', 'content'], methods=[])
- class GoalExtractionResult(attrs=['goal', 'message_intent', 'messages_scanned', 'corrections_skipped', 'meta_skipped', 'session_boundary_hit', 'topic_shift_hit', 'scan_pattern'], methods=[])
- def extract_topic_from_content(content, task_name) -> Annotated[str, 'max_length=80']
- def _get_table_indicators() -> list[str]
- def _get_assessment_indicators() -> list[str]
- def _get_comparison_indicators() -> list[str]
- def _check_for_table_structure(content) -> bool
- def _check_for_assessment(content_lower) -> bool
- def _check_for_comparison(content_lower) -> bool
- def _extract_search_keys(content_lower, max_keys) -> list[str]
- def _determine_structure_type(has_table, has_assessment, has_comparison, search_keys) -> StructureInfo | None
- def detect_structure_type(content) -> StructureInfo | None
- def is_meta_instruction(message) -> bool
- def is_meta_discussion(message) -> bool
- def is_correction_message(message) -> bool
- def is_clarification_message(message) -> bool
- def is_directive_message(message) -> bool
- def is_same_topic(message1, message2, threshold) -> bool
- def detect_session_boundary(entry, prev_entry) -> bool
- def gather_context_with_boundaries(transcript_path, max_messages) -> list[dict]
- def extract_last_substantive_user_message(transcript_path) -> GoalExtractionResult
- def extract_preceding_message(transcript_path, goal) -> str | None
- class TranscriptLines(attrs=[], methods=['__init__', '_ensure_length', '__len__', '__getitem__', '__getitem__', '__getitem__', '_load_line', '_load_range', '__iter__'])
- class TranscriptParser(attrs=[], methods=['__init__', '_build_user_message_description', '_is_substantial_user_message', '_get_transcript_lines', '_iter_transcript_lines', '_get_parsed_entries', '_extract_text_from_entry', '_filter_entries_by_type', 'extract_current_blocker', 'extract_modifications', 'extract_open_conversation_context', 'extract_session_decisions', 'extract_session_patterns', 'extract_controversial_decisions', 'extract_visual_context', 'extract_last_user_message', 'get_transcript_timestamp', 'get_transcript_offset', 'get_transcript_entry_count', 'extract_pending_operations', 'extract_skill_invocations', '_extract_skill_context', 'extract_last_skill_output'])
- def extract_user_message_from_blocker(blocker) -> str | None
- def filter_valid_messages(messages) -> list[MessageDict]
- def extract_transcript_from_messages(messages) -> str
- def __init__(self, path) -> None
- def _ensure_length(self) -> int
- def __len__(self) -> int
- def __getitem__(self, key) -> str
- def __getitem__(self, key) -> list[str]
- def __getitem__(self, key) -> str | list[str]
- def _load_line(self, index) -> str
- def _load_range(self, start, stop) -> list[str]
- def __iter__(self) -> Iterator[str]
- def __init__(self, transcript_path) -> None
- def _build_user_message_description(message, max_length) -> dict[str, Any]
- def _is_substantial_user_message(text, min_length) -> bool
- def _get_transcript_lines(self) -> Sequence[str]
- def _iter_transcript_lines(self) -> Iterator[str]
- def _get_parsed_entries(self) -> list[dict[str, Any]]
- def _extract_text_from_entry(self, entry) -> str
- def _filter_entries_by_type(self, entries, entry_type) -> list[dict[str, Any]]
- def extract_current_blocker(self) -> dict[str, Any] | None
- def extract_modifications(self, limit) -> list[dict[str, Any]]
- def extract_open_conversation_context(self) -> dict[str, Any] | None
- def extract_session_decisions(self, task_name) -> list[dict[str, Any]]
- def extract_session_patterns(self) -> list[str]
- def extract_controversial_decisions(self) -> list[dict[str, Any]]
- def extract_visual_context(self) -> dict[str, Any] | None
- def extract_last_user_message(self) -> str | None
- def get_transcript_timestamp(self) -> str | None
- def get_transcript_offset(self) -> int
- def get_transcript_entry_count(self) -> int
- def extract_pending_operations(self) -> list[dict[str, Any]]
- def extract_skill_invocations(self) -> list[dict[str, Any]]
- def _extract_skill_context(self, skill_entry, all_entries) -> str
- def extract_last_skill_output(self, max_length) -> dict[str, Any] | None
- def append_text(value) -> None

### scripts\hooks\__lib\user_intent.py

- def capture_pending_questions(transcript) -> dict | None
- def _extract_questions(transcript) -> list[dict]
- def _categorize_question(question) -> str

### scripts\hooks\__lib\validation_utils.py

- def validate_terminal_id(terminal_id) -> None