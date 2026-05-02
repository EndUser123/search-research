# skill-guard — Signatures

## Directory Index
```
.claude-plugin\plugin.json
CHANGELOG.md
hooks\hooks.json
pyproject.toml
README.md
src\skill_guard\__init__.py
src\skill_guard\breadcrumb\__init__.py
src\skill_guard\breadcrumb\cache.py
src\skill_guard\breadcrumb\database.py
src\skill_guard\breadcrumb\enforcement.py
src\skill_guard\breadcrumb\hooks\PostToolUse_breadcrumb_tracker.py
src\skill_guard\breadcrumb\hooks\UserPromptSubmit_breadcrumb_init.py
src\skill_guard\breadcrumb\inference.py
src\skill_guard\breadcrumb\log.py
src\skill_guard\breadcrumb\migration.py
src\skill_guard\breadcrumb\sqlite_backend.py
src\skill_guard\breadcrumb\tracker.py
src\skill_guard\exceptions.py
src\skill_guard\hook_compat.py
src\skill_guard\posttooluse\__init__.py
src\skill_guard\posttooluse\skill_execution_tracker.py
src\skill_guard\PreToolUse\__init__.py
src\skill_guard\PreToolUse\PreToolUse_context_sufficiency_gate.py
src\skill_guard\PreToolUse\PreToolUse_import_deletion_guard.py
src\skill_guard\PreToolUse\PreToolUse_skill_dir_gate.py
src\skill_guard\PreToolUse\PreToolUse_skill_pattern_gate.py
src\skill_guard\PreToolUse\PreToolUse_skill_question_gate.py
src\skill_guard\PreToolUse\PreToolUse_skill_script_path_gate.py
src\skill_guard\skill_auto_discovery.py
src\skill_guard\skill_execution_state.py
src\skill_guard\skill_forced_eval.py
src\skill_guard\skill_metadata_advisory.py
src\skill_guard\slash_command_observability.py
src\skill_guard\StopHook_skill_execution_gate.py
src\skill_guard\tdd_contract_auto_gate.py
src\skill_guard\turn_marker.py
src\skill_guard\utils\__init__.py
src\skill_guard\utils\terminal_detection.py
src\skill_guard\utils\terminal_id.py
tests\conftest.py
tests\test_audit.py
tests\test_auto_discovery_integration.py
tests\test_benchmark.py
tests\test_breadcrumb.py
tests\test_breadcrumb_extended.py
tests\test_breadcrumb_hooks_integration.py
tests\test_breadcrumb_isolation.py
tests\test_breadcrumb_log.py
tests\test_craft_lens_enforcer.py
tests\test_craft_router.py
tests\test_craft_state.py
tests\test_database.py
tests\test_enforcement.py
tests\test_eval_bridge.py
tests\test_exceptions.py
tests\test_fidelity_tracker.py
tests\test_frontmatter_validation.py
tests\test_load_tool_events_for_context.py
tests\test_log_rotation.py
tests\test_migration.py
tests\test_PreToolUse_context_sufficiency_gate.py
tests\test_PreToolUse_import_deletion_guard.py
tests\test_PreToolUse_skill_dir_gate.py
tests\test_PreToolUse_skill_pattern_gate.py
tests\test_PreToolUse_skill_question_gate.py
tests\test_skill_auto_discovery.py
tests\test_skill_command_hook_integration.py
tests\test_skill_execution_state.py
tests\test_skill_execution_tracker.py
tests\test_skill_forced_eval.py
tests\test_skill_invocation_indicator.py
tests\test_skill_metadata_advisory.py
tests\test_slash_command_observability.py
tests\test_sqlite_backend.py
tests\test_StopHook_skill_execution_gate.py
tests\test_t001_workflow_steps_required.py
tests\test_t002_breadcrumb_integration.py
tests\test_t003_breadcrumb_verifier.py
tests\test_t004_enforcement.py
tests\test_t005_tiered_verification.py
tests\test_t005_tracker_integration.py
tests\test_tdd_contract_auto_gate.py
tests\test_tool_inference.py
tests\test_tracker.py
tests\test_tracker_fixes.py
tests\test_turn_marker.py
tests\test_verification_reminder.py
tests\test_workflow_steps_parsing.py
```

## Signatures
### src\skill_guard\breadcrumb\cache.py
  class BreadcrumbStateCache():
  def __init__(self, max_size: int) -> None
  def _get_cache_key(self, skill_name: str) -> str
  def get_state(self, skill_name: str) -> dict[str, Any] | None
  def update_state(self, skill_name: str, state: dict[str, Any]) -> None
  def _load_from_log(self, skill_name: str) -> dict[str, Any] | None
  def _evict_if_needed(self) -> None
  def snapshot_all(self) -> None
  def _snapshot_state(self, skill_name: str, state: dict[str, Any]) -> None
  def invalidate(self, skill_name: str) -> None
  def clear_all(self) -> None
  def get_stats(self) -> dict[str, Any]

### src\skill_guard\breadcrumb\database.py
  def _is_connection_valid(conn: sqlite3.Connection) -> bool
  def get_connection(db_path: Path | None) -> sqlite3.Connection | None
  def close_connection(db_path: Path | None) -> None
  def _get_schema_version(conn: sqlite3.Connection) -> int
  def _run_migrations(conn: sqlite3.Connection, from_version: int) -> None
  def initialize_schema(conn: sqlite3.Connection) -> None

### src\skill_guard\breadcrumb\enforcement.py
  class EnforcementLevel(Enum):
  def get_enforcement_level(skill_name: str) -> EnforcementLevel
  def _normalize_workflow_step_ids(workflow_steps: list) -> list[str]
  def verify_with_enforcement(skill_name: str, trail: dict[str, Any] | None, duration_seconds: float, tool_count: int) -> tuple[bool, str]
  def _verify_minimal(workflow_steps: list[str], completed_steps: list[str], duration_seconds: float, tool_count: int) -> tuple[bool, str]
  def _verify_standard(workflow_steps: list[str], completed_steps: list[str], duration_seconds: float, tool_count: int) -> tuple[bool, str]
  def _verify_strict(workflow_steps: list[str], completed_steps: list[str], duration_seconds: float, tool_count: int, steps: dict[str, Any] | None) -> tuple[bool, str]
  def __str__(self) -> str

### src\skill_guard\breadcrumb\hooks\PostToolUse_breadcrumb_tracker.py
  def _get_current_skill(data: dict) -> str | None
  def run(data: dict) -> dict | None

### src\skill_guard\breadcrumb\hooks\UserPromptSubmit_breadcrumb_init.py
  def _extract_skill_name(prompt: str) -> str | None
  def initialize_breadcrumb_for_skill(skill_name: str) -> bool
  def process_prompt_for_breadcrumbs(prompt: str, data: dict) -> str | None

### src\skill_guard\breadcrumb\inference.py
  def _infer_step_from_tool(tool_name: str, tool_input: dict[str, Any]) -> str | None
  def _normalize_step_name(step: str) -> str
  def infer_step_from_tool_use(tool_name: str, tool_input: dict[str, Any]) -> str | None
  def get_supported_tools() -> list[str]
  def add_tool_mapping(tool_name: str, step_name: str) -> None
  def remove_tool_mapping(tool_name: str) -> None
  def clear_custom_mappings() -> None

### src\skill_guard\breadcrumb\log.py
  def _get_log_dir() -> Path
  def _get_log_file(skill_name: str) -> Path
  class AppendOnlyBreadcrumbLog():
  def cleanup_old_log_dirs(age_days: int) -> dict[str, list[str]]
  def __init__(self, skill_name: str) -> None
  def append(self, entry: dict[str, Any]) -> None
  def replay(self) -> list[dict[str, Any]]
  def _rotate_log(self) -> None
  def clear(self) -> None

### src\skill_guard\breadcrumb\migration.py
  def validate_jsonl_files(terminal_id: str) -> tuple[bool, list[str]]
  def validate_json_state(terminal_id: str) -> tuple[bool, list[str]]
  def migrate_jsonl_to_events(terminal_id: str, db_path: str | Path) -> bool
  def migrate_json_state_to_trails(terminal_id: str, db_path: str | Path) -> bool
  def _ensure_schema(db_path: str | Path) -> bool
  def migrate_terminal(terminal_id: str, db_path: str | Path) -> bool
  def migrate_all_terminals(db_path: str | Path) -> tuple[int, int]
  def rollback_migration(terminal_id: str, db_path: str | Path) -> bool
  def cli_migrate(db_path: str, terminal_id: str | None) -> int
  def cli_migrate_all(db_path: str) -> int
  def cli_rollback(db_path: str, terminal_id: str | None) -> int

### src\skill_guard\breadcrumb\sqlite_backend.py
  def create_trail(db_path: Path, skill: str, terminal_id: str, workflow_steps: list[dict[str, Any]], steps: dict[str, dict[str, Any]]) -> str
  def update_trail(db_path: Path, run_id: str, completed_steps: list[str], current_step: str | None, steps: dict[str, dict[str, Any]]) -> None
  def append_event(db_path: Path, trail_id: int, event_type: str, event_data: dict[str, Any] | None) -> None
  def get_active_trails(db_path: Path, terminal_id: str) -> list[dict[str, Any]]
  def get_trail_by_run_id(db_path: Path, run_id: str) -> dict[str, Any] | None
  def delete_trail(db_path: Path, run_id: str) -> bool
  def clear_terminal_trails(db_path: Path, terminal_id: str) -> int

### src\skill_guard\breadcrumb\tracker.py
  def _ensure_database_initialized() -> bool
  def _append_ledger_event(event_type: str, payload: dict[str, Any]) -> None
  def _get_breadcrumb_dir() -> Path
  def _get_breadcrumb_file(skill_name: str) -> Path
  def _load_workflow_steps(skill_name: str) -> WorkflowStepsResult
  def _regex_workflow_steps_fallback(content: str, defaults: dict) -> list[dict]
  def initialize_breadcrumb_trail(skill_name: str, force: bool) -> None
  def set_breadcrumb(skill_name: str, step_name: str, evidence: dict[str, Any] | None) -> None
  def _windows_safe_unlink(path: Path) -> None
  def get_breadcrumb_trail(skill_name: str) -> dict[str, Any] | None
  def verify_breadcrumb_trail(skill_name: str) -> tuple[bool, str]
  def clear_breadcrumb_trail(skill_name: str) -> None
  def clear_all_breadcrumb_trails() -> None
  def cleanup_session_breadcrumbs() -> int
  def cleanup_stale_breadcrumbs() -> int
  def verify_session_isolation(trail: dict[str, Any]) -> bool
  def get_active_breadcrumb_trails() -> list[dict[str, Any]]
  def format_breadcrumb_status(trail: dict[str, Any]) -> str

### src\skill_guard\exceptions.py
  class SkillGuardError(Exception):
  class WorkflowStepsError(SkillGuardError):
  class BreadcrumbStateError(SkillGuardError):
  class DatabaseError(SkillGuardError):

### src\skill_guard\hook_compat.py
  class _HookResult():
  def _register_hook(name: str, priority: float) -> Callable[[Callable[..., Any]], Callable[..., Any]]
  def __init__(self, context: Any, tokens: int, priority: float, tokens_added: int | None) -> None
  def is_empty(self) -> bool
  classmethod def empty(cls) -> _HookResult
  def decorator(func: Callable[..., Any]) -> Callable[..., Any]

### src\skill_guard\posttooluse\skill_execution_tracker.py
  class SkillExecutionTracker(PostToolUseHook):
  def __init__(self)
  def _import_functions(self)
  def _load_workflow_steps(self, skill_name: str)
  def process(self, tool_name: str, tool_input: dict[str, Any], tool_response: dict[str, Any]) -> dict[str, Any]
  def _update_checkpoint_task_with_skill(self, skill_name: str) -> None
  def _extract_skill_name(self, tool_input: dict[str, Any] | str) -> str

### src\skill_guard\PreToolUse\PreToolUse_context_sufficiency_gate.py
  def _load_skill_autonomy_registry()
  def run(data: dict[str, Any]) -> dict[str, Any]

### src\skill_guard\PreToolUse\PreToolUse_import_deletion_guard.py
  def extract_import_symbols(text: str) -> set[str]
  def extract_removed_symbols(old_string: str, new_string: str) -> set[str]
  def has_symbol_search_this_turn(symbol: str, tool_events: list[dict]) -> bool
  def extract_module_name(import_line: str) -> str | None
  def has_investigation_evidence(old_string: str, removed_symbols: set[str], file_path: str, tool_events: list[dict]) -> bool
  def load_this_turn_events(session_id: str, terminal_id: str) -> list[dict] | None
  def has_bypass_flag(user_message: str) -> bool
  def _iter_candidate_edits(tool_name: str, tool_input: dict) -> list[tuple[str, str, str]]
  def evaluate(data: dict) -> dict | None
  def run(data: dict) -> dict | None
  def main() -> int
  def _command_mentions_symbol(command: str) -> bool

### src\skill_guard\PreToolUse\PreToolUse_skill_dir_gate.py
  def _safe_id(value: str) -> str
  def _skill_context_path(terminal_id: str) -> Path
  def _load_state(terminal_id: str) -> dict | None
  def _is_skill_dir_in_command(command: str, expected_dir: str) -> bool
  def _get_command_from_input(tool_name: str, tool_input: dict) -> str | None
  def run(data: dict) -> dict
  def main() -> None

### src\skill_guard\PreToolUse\PreToolUse_skill_pattern_gate.py
  def _clear_shadowed_hook_packages() -> None
  def _extract_command(tool_name: str, tool_input: dict) -> str
  def _check_regex(command: str, pattern: str) -> bool
  def _check_daemon_intent(command: str, skill: str, timeout: float) -> bool
  def _read_pending_state() -> dict | None
  def _read_pending_command_intent() -> dict | None
  def _log_disagreement(skill: str, command: str, regex_result: bool, daemon_result: bool | None, decision: str) -> None
  def _log_coherence_event(event: str, skill: str, tool_name: str, allowed: list[str], decision: str) -> None
  def _check_first_tool_coherence(tool_name: str, state: dict) -> dict
  def _check_first_command_pattern(tool_name: str, tool_input: dict, state: dict) -> dict
  def _load_frontmatter_execution_config(skill_name: str) -> dict
  def handle_pre_tool_use(data: dict) -> dict
  def _make_decision(skill: str, command: str, regex_match: bool, daemon_match: bool, intent_enabled: bool, pattern: str, hint: str) -> dict
  def main()

### src\skill_guard\PreToolUse\PreToolUse_skill_question_gate.py
  def _get_marker_path(session_id: str, prefix: str) -> Path
  def _load_json(path: Path) -> dict
  def _save_json(path: Path, data: dict) -> None
  def run(data: dict[str, Any]) -> dict[str, Any]

### src\skill_guard\PreToolUse\PreToolUse_skill_script_path_gate.py
  def _extract_script_path(command: str) -> str | None
  def run(data: dict) -> dict | None
  def main() -> None

### src\skill_guard\skill_auto_discovery.py
  def _normalize_list(value: object) -> list[str]
  def _infer_contract_type(frontmatter: dict, category: str, skill_name: str) -> str
  def discover_all_skills(skills_dir: str | Path) -> dict
  def _parse_skill_frontmatter(skill_md: Path) -> dict | None
  def get_skill_config(skill_name: str, explicit_registry: dict | None) -> dict
  def discover_hooks(skills_dir: str | Path) -> list[dict]
  def _parse_skill_hooks(skill_md: Path, skill_name: str) -> list[dict]
  def _detect_script_pattern(skill_name: str) -> str

### src\skill_guard\skill_execution_state.py
  def _get_legacy_skill_metadata_cache()
  def _normalize_string_list(value: object) -> list[str]
  def _infer_contract_type(frontmatter: dict[str, Any]) -> str
  def detect_terminal_id() -> str
  def _atomic_write_json(path: Path, data: dict) -> None
  def sanitize_terminal_id(terminal_id: str) -> str
  def _get_state_file() -> Path
  def _get_state_dir() -> Path
  def _get_state_file_for_terminal(terminal_id: str) -> Path
  def _read_pending_state_file(terminal_id: str) -> dict[str, Any] | None
  def _write_pending_state_file(terminal_id: str, state: dict[str, Any]) -> bool
  def _clear_pending_state_file(terminal_id: str) -> None
  def _load_skill_frontmatter(skill_name: str) -> dict[str, Any]
  def _validate_skill_frontmatter(skill_name: str) -> list[str]
  def _get_active_turn_scope() -> tuple[str, str]
  def _get_ledger_module()
  def set_skill_loaded(skill_name: str, required_tools: list[str] | None, pattern: str | None, hint: str, intent_enabled: bool, prompt_fingerprint: str, task_id: str) -> None
  def record_tool_use(tool_name: str, tool_input: dict[str, Any]) -> None
  def transition_phase(to_state: str) -> bool
  def read_pending_state() -> dict | None
  def mark_first_tool_validated() -> None
  def mark_first_command_validated() -> None
  def update_workflow_stage(active_step: str, step_definition: str, done_criteria: list[str] | None, do_not_distract: list[str] | None, step_index: int | None, total_steps: int | None) -> None
  def clear_state() -> None
  def migrate_legacy_state() -> None
  def cleanup_stale_state_files(stale_timeout: int | None) -> int

### src\skill_guard\skill_forced_eval.py
  def _get_state_dir() -> Path
  def _get_terminal_id(context: HookContext) -> str
  def _safe_id(value: str) -> str
  def _discover_registered_skills() -> list[str]
  def _get_skill_frontmatter(skill_name: str) -> dict
  def _parse_frontmatter(skill_path: Path) -> dict
  def _get_all_skill_metadata() -> dict[str, dict]
  def _get_registered_skills() -> list[str]
  def _get_skill_metadata() -> dict[str, dict]
  def _clear_caches() -> None
  def _is_question_context(prompt: str) -> bool
  def _extract_slash_commands(prompt: str) -> list[str]
  def _get_matching_skills(prompt: str) -> list[str]
  def _format_skill_list(skills: list[str], metadata: dict[str, dict]) -> str
  def _detect_tool_conflicts(metadata: dict[str, dict], skills: list[str]) -> list[tuple[str, str]]
  def _format_conflict_report(conflicts: list[tuple[str, str]]) -> str
  def _save_eval_state(context: HookContext, invoked_skills: list[str], metadata: dict[str, dict]) -> None
  def _load_eval_state(context: HookContext) -> dict | None
  def _clear_eval_state(context: HookContext) -> None
  def _cleanup_stale_state_files() -> int
  register_hook('skill_forced_eval', priority=0.5) def skill_forced_eval_hook(context: HookContext) -> HookResult

### src\skill_guard\skill_metadata_advisory.py
  def _normalize_list(value: object) -> list[str]
  def _classify_contract(metadata: dict) -> str
  def _enhancement_reasons(metadata: dict) -> list[str]
  def _build_warning(skill_name: str, metadata: dict, reasons: list[str]) -> str
  def _build_notification_message(skill_name: str, reasons: list[str]) -> str
  def _get_session_id(context: Any) -> str
  def skill_metadata_advisory(context: Any) -> str | None
  register_hook('skill_metadata_advisory', priority=5.0) def skill_metadata_advisory_hook(context: Any) -> HookResult
  def add_notification(notification_type: str, message: str, source: str, priority: int, session_id: str) -> None
  def clear_by_type(notification_type: str, source: str | None, session_id: str | None) -> int

### src\skill_guard\slash_command_observability.py
  def _claude_dir() -> Path
  def _commands_dir() -> Path
  def _skills_dir() -> Path
  def _normalize_prompt(prompt: str) -> str
  def normalize_prompt(prompt: str) -> str
  def extract_slash_command(prompt: str) -> tuple[str | None, str]
  def extract_command_name(prompt: str) -> str | None
  def is_slash_prompt(prompt: str) -> bool
  lru_cache(maxsize=8) def _local_command_paths(commands_dir: str) -> dict[str, Path]
  lru_cache(maxsize=8) def _skill_paths(skills_dir: str) -> dict[str, Path]
  def _extract_backing_skill(command_path: Path) -> str
  def classify_slash_command(command_name: str) -> dict[str, str]
  def _resolve_session_id(context: Any) -> str
  def _resolve_terminal_id(context: Any) -> str
  def _resolve_turn_id(context: Any, session_id: str, terminal_id: str) -> str
  def _append_slash_event() -> bool
  def record_slash_request(context: Any, command_name: str, command_args: str) -> bool
  def record_slash_resolution(context: Any, command_name: str, command_args: str) -> bool
  def record_slash_outcome(context: Any, command_name: str, command_args: str) -> bool
  register_hook('slash_command_observability', priority=0.6) def slash_command_observability_hook(context: Any) -> HookResult
  def append_tool_event() -> bool
  def get_active_turn(session_id: str, terminal_id: str) -> str | None
  def resolve_session_id(explicit: str) -> str

### src\skill_guard\StopHook_skill_execution_gate.py
  def _extract_text_content(message_content: object) -> str
  def _extract_tool_use_content(message_content: object) -> list[dict]
  def _parse_transcript_snapshot(input_data: dict) -> dict
  def _get_transcript_snapshot(input_data: dict) -> dict
  def extract_user_prompt(input_data: dict) -> str
  def _extract_slash_command(prompt: str) -> str | None
  def log(msg: str) -> None
  def log_event(event: str, data: dict) -> None
  def _get_governance_state_file() -> Path
  def _read_governance_state() -> dict | None
  def _update_governance_retry(state: dict) -> None
  def _clear_governance_state() -> None
  def _normalize_tool_names(items: list) -> list[str]
  def extract_tools_used(input_data: dict) -> list[str]
  def _get_first_bash_command_from_transcript(input_data: dict) -> str | None
  def extract_response_text(input_data: dict) -> str
  def _check_governance_markers(input_data: dict) -> dict
  def _get_state_file() -> Path
  def _read_state() -> dict | None
  def _clear_state() -> None
  def _is_stale(state: dict) -> bool
  def _check_pattern_match(command: str, pattern: str) -> bool
  def _tool_mentions_artifact(tool_event: object, artifact_name: str) -> bool
  def _missing_required_phase_artifacts(state: dict, tool_history: list) -> list[str]
  def _normalize_list(value: object) -> list[str]
  def _contract_type(state: dict) -> str
  def _requires_execution_tools(state: dict) -> bool
  def validate_execution(state: dict, tool_history: list) -> dict
  def run(input_data: dict) -> dict | None
  def check_verification_reminder(steps: dict | None) -> dict[str, bool | str | None]
  hook_main def main()
  def _workflow_block(reason: str) -> dict
  def _is_help_only_request(prompt: str) -> bool
  def _log_slash_outcome(outcome: str, reason: str) -> None
  def record_slash_outcome()

### src\skill_guard\tdd_contract_auto_gate.py
  def _is_tdd_bypassed(prompt: str) -> bool
  def _extract_target_file(prompt: str, skill_name: str) -> str | None
  def _get_tdd_manager(context: Any)
  def tdd_contract_auto_gate(context: Any) -> bool
  register_hook('tdd_contract_auto_gate', priority=2.0) def tdd_contract_auto_gate_hook(context: Any) -> HookResult

### src\skill_guard\turn_marker.py
  def _resolve_context_value(context: Any, key: str, default: str) -> str
  def ensure_turn_marker(context: Any) -> str | None
  register_hook('turn_marker', priority=0.5) def write_turn_marker(context: Any) -> HookResult
  def get_active_turn(session_id: str, terminal_id: str) -> str | None
  def start_turn(session_id: str, terminal_id: str, prompt: str, transcript_path: str) -> str

### src\skill_guard\utils\terminal_detection.py
  def _detect_console_window() -> str
  def _read_from_state_file() -> str | None
  def detect_terminal_id() -> str
  def detect_terminal_id_with_source() -> tuple[str, str]

### src\skill_guard\utils\terminal_id.py
  def normalize_terminal_id(raw_id: str, source: str) -> str

### tests\conftest.py
  pytest.fixture(autouse=True) def mock_detect_terminal_id(request)
  pytest.fixture(autouse=True) def patch_workflow_steps_for_test_skills()
  pytest.fixture(autouse=True) def clean_breadcrumb_state_and_logs()
  pytest.fixture(autouse=True) def clear_breadcrumb_cache()
  def patched_load(skill_name: str)
  def do_cleanup()

### tests\test_audit.py
  def test_audit_exists()

### tests\test_benchmark.py
  class TestLogReplayPerformance():
  class TestConcurrentAccessPerformance():
  class TestHybridSystemPerformance():
  def test_replay_performance_small_log(self)
  def test_replay_performance_medium_log(self)
  def test_replay_performance_large_log(self)
  def test_concurrent_write_performance(self)
  def test_end_to_end_performance(self)
  def test_memory_usage_active_session(self)
  def test_write_performance(self)

### tests\test_breadcrumb.py
  pytest.fixture def cleanup_test_state()
  pytest.fixture(autouse=True) def set_strict_enforcement(monkeypatch)
  def test_initialize_trail(cleanup_test_state)
  def test_set_breadcrumb(cleanup_test_state)
  def test_verify_complete_trail(cleanup_test_state)
  def test_verify_incomplete_trail(cleanup_test_state)
  def test_invalid_step(cleanup_test_state)
  def test_no_workflow_steps(cleanup_test_state)
  def test_format_status(cleanup_test_state)
  def test_session_isolation(cleanup_test_state)
  def test_cleanup_session_breadcrumbs(cleanup_test_state)
  def test_cleanup_stale_breadcrumbs(cleanup_test_state)
  def run_all_tests()

### tests\test_breadcrumb_extended.py
  pytest.fixture def mock_skills_dir(tmp_path)
  class TestLoadWorkflowStepsStringFormat():
  class TestLoadWorkflowStepsDictFormat():
  class TestLoadWorkflowStepsMixedFormat():
  class TestLoadWorkflowStepsEdgeCases():
  class TestInitializeBreadcrumbRunId():
  class TestInitializeBreadcrumbStepsDict():
  class TestSetBreadcrumbEvidence():
  def mock_path_impl(path_str)
  def test_load_workflow_steps_string_format(self, mock_skills_dir)
  def test_load_workflow_steps_empty_string_list(self, mock_skills_dir)
  def test_load_workflow_steps_dict_format(self, mock_skills_dir)
  def test_load_workflow_steps_dict_defaults(self, mock_skills_dir)
  def test_load_workflow_steps_mixed_format(self, mock_skills_dir)
  def test_load_workflow_steps_missing_skill_file(self, mock_skills_dir)
  def test_load_workflow_steps_invalid_yaml(self, mock_skills_dir)
  def test_load_workflow_steps_dict_without_id(self, mock_skills_dir)
  def test_initialize_breadcrumb_generates_run_id(self, mock_skills_dir, tmp_path)
  def test_initialize_breadcrumb_creates_steps_dict(self, mock_skills_dir, tmp_path)
  def test_initialize_breadcrumb_preserves_string_steps(self, mock_skills_dir, tmp_path)
  def test_initialize_breadcrumb_empty_workflow_steps(self, mock_skills_dir, tmp_path)
  def test_set_breadcrumb_with_evidence(self, mock_skills_dir, tmp_path)
  def test_set_breadcrumb_without_evidence(self, mock_skills_dir, tmp_path)
  def test_set_breadcrumb_preserves_existing_evidence(self, mock_skills_dir, tmp_path)
  def test_set_breadcrumb_invalid_step(self, mock_skills_dir, tmp_path)
  def mock_get_breadcrumb_dir()
  def mock_terminal_id()
  def mock_get_breadcrumb_dir()
  def mock_terminal_id()
  def mock_get_breadcrumb_dir()
  def mock_terminal_id()
  def mock_get_breadcrumb_dir()
  def mock_terminal_id()
  def mock_get_breadcrumb_dir()
  def mock_terminal_id()
  def mock_get_breadcrumb_dir()
  def mock_terminal_id()
  def mock_get_breadcrumb_dir()
  def mock_terminal_id()
  def mock_get_breadcrumb_dir()
  def mock_terminal_id()

### tests\test_breadcrumb_hooks_integration.py
  class TestPreToolUseGateWithNewFormat():
  class TestStopHookVerificationReminder():
  class TestPostToolUseEvidenceTracking():
  class TestEndToEndIntegration():
  def test_blocks_when_skill_not_used_first_dict_format(self, tmp_path)
  def test_allows_after_skill_tool_used_dict_format(self, tmp_path)
  def test_verification_reminder_emits_when_incomplete(self, tmp_path)
  def test_verification_reminder_no_reminder_when_complete(self, tmp_path)
  def test_verification_reminder_handles_gracefully(self, tmp_path)
  def test_set_breadcrumb_with_evidence_stores_correctly(self, tmp_path)
  def test_set_breadcrumb_without_evidence_preserves(self, tmp_path)
  def test_evidence_overwrites_on_subsequent_calls(self, tmp_path)
  def test_full_workflow_with_verification_steps(self, tmp_path)

### tests\test_breadcrumb_isolation.py
  class TestBreadcrumbIsolation():
  def test_different_terminals_create_separate_dirs(self)
  def test_breadcrumb_files_are_terminal_scoped(self)
  def test_verify_session_isolation_checks_terminal_id(self)
  def test_get_breadcrumb_trail_rejects_wrong_terminal(self)
  def test_clear_only_affects_current_terminal(self)
  def test_concurrent_terminals_dont_interfere(self)
  def test_path_traversal_blocked_in_file_operations(self)
  def test_cleanup_session_breadcrumbs_only_clears_current_terminal(self)
  def test_cleanup_stale_breadcrumbs_preserves_current_terminal(self)

### tests\test_breadcrumb_log.py
  class TestAppendOnlyBreadcrumbLog():
  def test_append_creates_jsonl_file(self)
  def test_append_multiple_entries(self)
  def test_replay_returns_newest_first(self)
  def test_replay_empty_when_no_file(self)
  def test_replay_handles_malformed_lines(self)
  def test_append_augments_with_metadata(self)
  def test_clear_removes_log_file(self)
  def test_clear_on_nonexistent_file(self)
  def test_path_traversal_blocked(self)
  def test_terminal_scoped_paths(self)
  def test_concurrent_logs_dont_interfere(self)

### tests\test_craft_lens_enforcer.py
  def test_craft_lens_enforcer_exists()

### tests\test_craft_router.py
  def test_route_finding_routes_trigger_to_creator()
  def test_route_finding_routes_second_person_to_development()
  def test_route_finding_routes_wrong_scope_to_audit()
  def test_route_finding_routes_missing_test_to_ship()
  def test_route_finding_defaults_to_source_skill()
  def test_run_craft_against_gitready_completes()
  def test_run_craft_fidelity_measured()
  def test_run_craft_cert_gate_results()
  def test_run_craft_loops_up_to_max()
  def test_run_craft_no_healthy_exit()
  def test_run_craft_fidelity_score_populated()

### tests\test_craft_state.py
  def test_craft_state_exists()

### tests\test_database.py
  class TestDatabaseConnection():
  class TestSchemaInitialization():
  class TestConnectionPooling():
  class TestGracefulDegradation():
  def get_connection_for_test(db_path: Path) -> sqlite3.Connection
  def test_get_connection_returns_valid_connection(self)
  def test_get_connection_enables_wal_mode(self)
  def test_get_connection_sets_busy_timeout(self)
  def test_get_connection_handles_invalid_path_gracefully(self)
  def test_initialize_schema_creates_breadcrumb_trails_table(self)
  def test_initialize_schema_creates_breadcrumb_events_table(self)
  def test_initialize_schema_creates_indexes(self)
  def test_initialize_schema_is_idempotent(self)
  def test_connection_pool_returns_same_connection_for_same_thread(self)
  def test_connection_pool_handles_multiple_database_paths(self)
  def test_database_unavailable_returns_none_or_raises_clear_error(self)

### tests\test_enforcement.py
  pytest.fixture(autouse=True) def set_minimal_enforcement(monkeypatch)
  def test_enforcement_level_enum()
  def test_enforcement_level_str()
  def test_verify_with_enforcement_no_trail()
  def test_verify_with_enforcement_minimal_duration_short(monkeypatch)
  def test_verify_with_enforcement_minimal_tool_count_low(monkeypatch)
  def test_verify_with_enforcement_strict_missing_steps(monkeypatch)
  def test_verify_with_enforcement_strict_missing_evidence(monkeypatch)
  def test_verify_with_enforcement_strict_complete(monkeypatch)

### tests\test_eval_bridge.py
  class TestEvalResultDataclass():
  class TestLoopResultDataclass():
  class TestAggregateBenchmark():
  class TestEvalBridgeJsonParsing():
  def test_fields_populated(self)
  def test_raw_preserved(self)
  def test_fields_populated(self)
  def test_optional_test_score_none(self)
  def test_empty_list_returns_zeros(self)
  def test_single_run(self)
  def test_multiple_runs(self)
  def test_all_fail(self)
  def test_zero_total_guards_divide_by_zero(self)
  def test_eval_output_structure(self)
  def test_eval_output_partial_trigger(self)
  def test_loop_output_structure(self)

### tests\test_exceptions.py
  def test_exceptions_exist()
  def test_exception_inheritance()

### tests\test_fidelity_tracker.py
  class TestDiscoverEvalSet():
  class TestStructuralOutcomeScore():
  class TestMeasureStructural():
  class TestMeasureFidelity():
  class TestStructuralOutcomeEdgeCases():
  def test_finds_local_eval_set(self, tmp_path)
  def test_returns_none_when_no_eval_set(self, tmp_path)
  def test_missing_skill_dir(self, tmp_path)
  def test_perfect_imperative_form(self, tmp_path)
  def test_second_person_reduces_score(self, tmp_path)
  def test_no_skill_md_returns_zero(self, tmp_path)
  def test_trigger_accuracy_full_desc(self, tmp_path)
  def test_trigger_accuracy_short_desc(self, tmp_path)
  def test_trigger_accuracy_missing_desc(self, tmp_path)
  def test_missing_skill_md_returns_zero(self, tmp_path)
  def test_uses_eval_set_when_present(self, tmp_path)
  def test_default_config_values(self, tmp_path)
  def test_degradation_delta_with_baseline(self, tmp_path)
  def test_passed_false_when_below_threshold(self, tmp_path)
  def test_empty_body(self, tmp_path)
  def test_only_second_person(self, tmp_path)
  def test_mixed_imperative_and_second_person(self, tmp_path)

### tests\test_frontmatter_validation.py
  class TestValidateSkillFrontmatter():
  class TestSkillLoadedIncludesFrontmatterWarnings():
  def _make_skill_md(self, skill_name: str, frontmatter: str) -> Path
  def test_validate_returns_empty_for_complete_frontmatter(self, tmp_path: Path) -> None
  def test_validate_warns_missing_enforcement(self, tmp_path: Path) -> None
  def test_validate_warns_missing_name(self, tmp_path: Path) -> None
  def test_validate_warns_missing_description(self, tmp_path: Path) -> None
  def test_validate_warns_missing_version(self, tmp_path: Path) -> None
  def test_validate_warns_missing_multiple_fields(self, tmp_path: Path) -> None
  def test_validate_returns_empty_for_nonexistent_skill(self, tmp_path: Path) -> None
  def test_validate_invalid_enforcement_value(self, tmp_path: Path) -> None
  def test_validate_accepts_all_valid_enforcement_values(self, tmp_path: Path) -> None
  def test_validate_warns_missing_required_first_command_patterns(self, tmp_path: Path) -> None
  def _make_skill_md(self, skill_name: str, frontmatter: str) -> None
  def _cleanup(self, skill_name: str) -> None
  def test_set_skill_loaded_includes_frontmatter_warnings(self, tmp_path: Path, monkeypatch: pytest) -> None
  def test_set_skill_loaded_no_warnings_for_complete_frontmatter(self, tmp_path: Path, monkeypatch: pytest) -> None
  def test_set_skill_loaded_includes_first_command_warning(self, tmp_path: Path, monkeypatch: pytest) -> None
  def mock_append_event() -> None
  def mock_append_event() -> None
  def mock_append_event() -> None

### tests\test_load_tool_events_for_context.py
  def load_tool_events_for_context(transcript_path: Path, terminal_id: str | None, turn_start_event_id: int) -> list[dict[str, Any]]
  class TestLoadToolEventsTerminalScoping():
  def test_two_terminals_same_session_return_only_own_events(self, tmp_path)
  def test_missing_terminal_id_returns_empty_list_fail_safe(self, tmp_path)
  def test_turn_start_event_id_filters_events(self, tmp_path)

### tests\test_log_rotation.py
  class TestLogRotation():
  def test_log_rotation_when_size_exceeded(self)
  def test_archive_filename_has_timestamp(self)
  def test_replay_works_after_rotation(self)
  def test_multiple_rotations_create_multiple_archives(self)
  def test_rotation_does_not_corrupt_data(self)
  def test_rotation_with_concurrent_access(self)

### tests\test_migration.py
  pytest.fixture def temp_state_dir(tmp_path: Path) -> Path
  pytest.fixture def temp_db_path(tmp_path: Path) -> Path
  pytest.fixture def sample_jsonl_data(temp_state_dir: Path) -> dict[str, Any]
  pytest.fixture def sample_json_state(temp_state_dir: Path) -> dict[str, Any]
  pytest.fixture def initialized_database(temp_db_path: Path) -> sqlite3.Connection
  class TestMigrationValidation():
  class TestJsonlMigration():
  class TestJsonMigration():
  class TestTransactionalMigration():
  class TestRollback():
  class TestCLI():
  def test_validate_jsonl_files_valid(self, sample_jsonl_data: dict[str, Any], temp_state_dir: Path) -> None
  def test_validate_jsonl_files_missing_dir(self, temp_state_dir: Path) -> None
  def test_validate_jsonl_files_corrupted_data(self, temp_state_dir: Path) -> None
  def test_validate_json_state_valid(self, sample_json_state: dict[str, Any], temp_state_dir: Path) -> None
  def test_validate_json_state_missing_dir(self, temp_state_dir: Path) -> None
  def test_validate_json_state_corrupted_data(self, temp_state_dir: Path) -> None
  def test_migrate_jsonl_to_events(self, sample_jsonl_data: dict[str, Any], temp_db_path: Path, initialized_database: sqlite3.Connection, temp_state_dir: Path) -> None
  def test_migrate_jsonl_to_events_no_files(self, temp_db_path: Path, initialized_database: sqlite3.Connection, temp_state_dir: Path) -> None
  def test_migrate_jsonl_preserves_data_integrity(self, sample_jsonl_data: dict[str, Any], temp_db_path: Path, initialized_database: sqlite3.Connection, temp_state_dir: Path) -> None
  def test_migrate_json_state_to_trails(self, sample_json_state: dict[str, Any], temp_db_path: Path, initialized_database: sqlite3.Connection, temp_state_dir: Path) -> None
  def test_migrate_json_state_no_files(self, temp_db_path: Path, initialized_database: sqlite3.Connection, temp_state_dir: Path) -> None
  def test_migrate_json_preserves_trail_integrity(self, sample_json_state: dict[str, Any], temp_db_path: Path, initialized_database: sqlite3.Connection, temp_state_dir: Path) -> None
  def test_migration_is_transactional(self, sample_jsonl_data: dict[str, Any], sample_json_state: dict[str, Any], temp_db_path: Path, initialized_database: sqlite3.Connection, temp_state_dir: Path) -> None
  def test_migration_rollback_on_error(self, temp_db_path: Path, initialized_database: sqlite3.Connection, temp_state_dir: Path) -> None
  def test_migration_validation_failure(self, temp_db_path: Path, initialized_database: sqlite3.Connection, temp_state_dir: Path) -> None
  def test_rollback_migration(self, sample_jsonl_data: dict[str, Any], sample_json_state: dict[str, Any], temp_db_path: Path, initialized_database: sqlite3.Connection, temp_state_dir: Path) -> None
  def test_rollback_nonexistent_migration(self, temp_db_path: Path, initialized_database: sqlite3.Connection) -> None
  def test_migrate_cli_command(self, sample_jsonl_data: dict[str, Any], sample_json_state: dict[str, Any], temp_db_path: Path, temp_state_dir: Path) -> None
  def test_migrate_cli_command_validation_error(self, temp_db_path: Path, temp_state_dir: Path) -> None
  def test_migrate_cli_all_terminals(self, sample_jsonl_data: dict[str, Any], sample_json_state: dict[str, Any], temp_db_path: Path, temp_state_dir: Path) -> None
  def test_rollback_cli_command(self, temp_db_path: Path, temp_state_dir: Path) -> None

### tests\test_PreToolUse_context_sufficiency_gate.py
  def test_PreToolUse_context_sufficiency_gate_exists()

### tests\test_PreToolUse_import_deletion_guard.py
  def test_PreToolUse_import_deletion_guard_exists()

### tests\test_PreToolUse_skill_dir_gate.py
  def test_PreToolUse_skill_dir_gate_exists()

### tests\test_PreToolUse_skill_pattern_gate.py
  def test_handle_pre_tool_use_exists()
  def _base_skill_state() -> dict
  def test_handle_pre_tool_use_allows_required_first_command()
  def test_handle_pre_tool_use_blocks_wrong_first_command()

### tests\test_PreToolUse_skill_question_gate.py
  def test_PreToolUse_skill_question_gate_exists()

### tests\test_skill_auto_discovery.py
  def test_skill_auto_discovery_module_importable()

### tests\test_skill_command_hook_integration.py
  pytest.fixture def skills_dir(tmp_path: Path) -> Path
  pytest.fixture def minimal_skill_md(skills_dir: Path) -> Path
  pytest.fixture def skill_md_with_hooks(skills_dir: Path) -> Path
  pytest.fixture def skill_md_with_broken_yaml(skills_dir: Path) -> Path
  class TestParseSkillFrontmatter():
  class TestDiscoverAllSkills():
  class TestParseSkillHooks():
  class TestDiscoverHooks():
  class TestSkillCommandHookIntegration():
  class TestDiscoveredHooksEndToEnd():
  class TestGracefulDegradation():
  def test_parses_minimal_frontmatter(self, minimal_skill_md: Path) -> None
  def test_has_execution_true_for_development(self, minimal_skill_md: Path) -> None
  def test_has_execution_false_for_knowledge_category(self, skills_dir: Path) -> None
  def test_returns_none_for_missing_frontmatter(self, skills_dir: Path) -> None
  def test_returns_none_for_empty_file(self, skills_dir: Path) -> None
  def test_strips_quotes_from_values(self, skills_dir: Path) -> None
  def test_returns_empty_dict_for_nonexistent_dir(self) -> None
  def test_discovers_single_skill(self, minimal_skill_md: Path) -> None
  def test_skips_directories_without_skill_md(self, tmp_path: Path) -> None
  def test_parses_posttooluse_hook(self, skill_md_with_hooks: Path) -> None
  def test_hook_has_required_fields(self, skill_md_with_hooks: Path) -> None
  def test_invalid_yaml_returns_empty_list(self, skill_md_with_broken_yaml: Path) -> None
  def test_returns_empty_list_for_nonexistent_dir(self) -> None
  def test_discovers_hooks_from_skill_md(self, skill_md_with_hooks: Path) -> None
  def test_hook_command_is_not_shell_expanded(self, skill_md_with_hooks: Path) -> None
  def test_hook_runner_import(self) -> None
  def test_skill_command_hook_instantiation(self) -> None
  def test_matches_tool_with_valid_pattern(self) -> None
  def test_matches_tool_with_none_pattern(self) -> None
  def test_matches_tool_with_invalid_regex(self) -> None
  def test_process_executes_command_successfully(self) -> None
  def test_process_returns_warning_on_nonzero_exit(self) -> None
  def test_process_returns_warning_on_timeout(self) -> None
  def test_process_disabled_hook_returns_empty(self) -> None
  def test_discover_hooks_finds_all_declared_hooks(self, skill_md_with_hooks: Path) -> None
  def test_hooks_have_unique_names(self, skill_md_with_hooks: Path) -> None
  def test_missing_yaml_module_does_not_crash(self, skill_md_with_hooks: Path) -> None

### tests\test_skill_execution_state.py
  def test_skill_execution_state_exists()

### tests\test_skill_execution_tracker.py
  def test_skill_execution_tracker_class_exists()

### tests\test_skill_forced_eval.py
  class TestSafeId():
  class TestExtractSlashCommands():
  class TestGetMatchingSkills():
  class TestFormatSkillList():
  class TestDetectToolConflicts():
  class TestCleanupStaleStateFiles():
  class TestClearCaches():
  class TestQuestionContextDetection():
  class TestSymlinkIntegrity():
  class TestHookPriorityOrdering():
  class TestImportChain():
  class TestUserPromptSubmitContract():
  class TestClockSkewTTL():
  class TestPathHomeResolution():
  class TestTOCTOURaceCondition():
  class TestSysPathShadowing():
  pytest.mark.parametrize('input_val,expected', [('normal_id', 'normal_id'), ('id-with-dots.and.dashes', 'id-with-dots.and.dashes'), ('ID WITH SPACES', 'ID_WITH_SPACES'), ('id!@#$%^&*()', 'id_'), ('UPPERCASE', 'UPPERCASE'), ('123numeric', '123numeric')]) def test_safe_id_various_inputs(self, input_val: str, expected: str) -> None
  def test_safe_id_empty_string(self) -> None
  def test_single_command(self) -> None
  def test_multiple_commands(self) -> None
  def test_command_at_start(self) -> None
  def test_command_at_end(self) -> None
  def test_no_commands(self) -> None
  def test_case_insensitive(self) -> None
  patch.object(sfe, '_get_registered_skills', return_value={'gto', 'code', 'docs'}) def test_returns_matching_registered(self, mock_registered) -> None
  patch.object(sfe, '_get_registered_skills', return_value=set()) def test_empty_when_no_registered(self, mock_registered) -> None
  def test_empty_skills(self) -> None
  def test_single_skill_no_tools(self) -> None
  def test_no_conflicts(self) -> None
  def test_bash_vs_readonly_conflict(self) -> None
  def test_cleanup_removes_stale_files(self, tmp_path: Path) -> None
  def test_cleanup_preserves_fresh_files(self, tmp_path: Path) -> None
  def test_cleanup_throttle(self, tmp_path: Path) -> None
  def test_clears_global_caches(self) -> None
  def test_question_about_skill_returns_true(self) -> None
  def test_question_with_what_returns_true(self) -> None
  def test_invocation_returns_false(self) -> None
  def test_invocation_with_args_returns_false(self) -> None
  def test_bare_skill_returns_false(self) -> None
  def test_skill_execution_state_symlink_valid(self) -> None
  def test_skill_forced_eval_runs_before_skill_enforcer(self) -> None
  def test_registry_can_import_skill_forced_eval(self) -> None
  patch.object(sfe, '_cleanup_stale_state_files', return_value=0) patch.object(sfe, '_save_eval_state') patch.object(sfe, '_get_skill_metadata', return_value={'rca': {'allowed_tools': ['Skill']}}) patch.object(sfe, '_get_registered_skills', return_value=['rca']) patch.object(sfe, '_get_matching_skills', return_value=['rca']) def test_hook_returns_additional_context_dict(self, mock_matching_skills, mock_registered_skills, mock_skill_metadata, mock_save_eval_state, mock_cleanup) -> None
  def test_monotonic_time_never_decreases(self) -> None
  def test_path_home_returns_expected_location(self) -> None
  def test_state_write_with_fallback_on_dir_deletion(self, tmp_path: Path) -> None
  def test_exact_string_check_prevents_duplicate_insert(self) -> None

### tests\test_skill_invocation_indicator.py
  def test_skill_invocation_indicator()

### tests\test_skill_metadata_advisory.py
  class _Context():
  def test_skill_metadata_advisory_flags_undercontracted_skill(monkeypatch)
  def test_skill_metadata_advisory_clears_hardened_skill(monkeypatch)
  def __init__(self, prompt: str, session_id: str) -> None

### tests\test_slash_command_observability.py
  def test_classify_local_command_frontend(tmp_path, monkeypatch)
  def test_classify_skill_and_builtin(tmp_path, monkeypatch)
  def test_extract_command_name_and_prompt_normalization()
  def test_record_slash_request_emits_event(monkeypatch)
  class Context():

### tests\test_sqlite_backend.py
  pytest.fixture def temp_db_path(tmp_path: Path) -> Path
  pytest.fixture def mock_terminal_id() -> str
  pytest.fixture def sample_trail() -> dict[str, Any]
  class TestDatabaseModule():
  class TestSQLiteBackend():
  class TestAPICompatibility():
  class TestPerformance():
  class TestTerminalIsolation():
  def test_database_initialization(self, temp_db_path: Path, mock_terminal_id: str) -> None
  def test_wal_mode_enabled(self, temp_db_path: Path) -> None
  def test_create_trail(self, temp_db_path: Path, sample_trail: dict[str, Any]) -> None
  def test_update_trail(self, temp_db_path: Path, sample_trail: dict[str, Any]) -> None
  def test_append_event(self, temp_db_path: Path, sample_trail: dict[str, Any]) -> None
  def test_get_active_trails(self, temp_db_path: Path, sample_trail: dict[str, Any]) -> None
  def test_cache_integration(self, temp_db_path: Path, sample_trail: dict[str, Any]) -> None
  def test_create_trail_signature(self) -> None
  def test_update_trail_signature(self) -> None
  def test_append_event_signature(self) -> None
  def test_get_active_trails_signature(self) -> None
  def test_create_trail_performance(self, temp_db_path: Path, sample_trail: dict[str, Any]) -> None
  def test_update_trail_performance(self, temp_db_path: Path, sample_trail: dict[str, Any]) -> None
  def test_append_event_performance(self, temp_db_path: Path, sample_trail: dict[str, Any]) -> None
  def test_get_active_trails_performance(self, temp_db_path: Path, sample_trail: dict[str, Any]) -> None
  def test_terminal_isolation(self, temp_db_path: Path, sample_trail: dict[str, Any]) -> None

### tests\test_StopHook_skill_execution_gate.py
  def test_StopHook_skill_execution_gate_exists()

### tests\test_t001_workflow_steps_required.py
  class TestT001WorkflowStepsRequired():
  pytest.mark.parametrize('skill_name', ['code', 'arch']) def test_critical_skills_must_have_workflow_steps(self, skill_name)
  def test_code_skill_workflow_steps_content(self)
  def test_trace_skill_workflow_steps_content(self)
  def test_arch_skill_workflow_steps_content(self)
  def test_workflow_steps_parsing_integration(self)

### tests\test_t002_breadcrumb_integration.py
  class TestBreadcrumbIntegration():
  def test_sessionstart_hooks_exist(self)
  def test_posttooluse_hooks_exist(self)
  def test_sessionstart_hook_executes_successfully(self)
  def test_posttooluse_hook_executes_successfully(self)
  def test_breadcrumb_imports_in_tdd_hook(self)
  def test_breadcrumb_calls_in_tdd_hook(self)
  def test_workflow_steps_loaded_for_critical_skills(self)
  def test_breadcrumb_files_created_in_terminal_scoped_dirs(self)
  def test_set_breadcrumb_creates_trail_if_not_exists(self)
  def test_set_breadcrumb_marks_steps_complete(self)
  def test_verify_breadcrumb_trail_function(self)
  def test_set_breadcrumb_to_verify_end_to_end(self)
  def test_cleanup_fixture_removes_files(self)

### tests\test_t003_breadcrumb_verifier.py
  class TestT003BreadcrumbVerifier():
  def test_hook_file_exists(self)
  def test_hook_executes_successfully(self)
  def test_warn_mode_shows_warning_for_incomplete_trail(self)
  def test_block_mode_blocks_incomplete_trail(self)
  def test_complete_trail_allows_execution(self)
  def test_non_completion_tools_skipped(self)
  def test_disabled_hook_allows_all(self)

### tests\test_t004_enforcement.py
  class TestT004EnforcementLevel():
  def test_enforcement_level_enum(self)
  def test_get_enforcement_level_default(self)
  def test_get_enforcement_level_env_override(self)
  def test_verify_minimal_level(self)
  def test_verify_minimal_level_fails_duration(self)
  def test_verify_minimal_level_fails_tool_count(self)
  def test_verify_standard_level(self)
  def test_verify_standard_level_fails_no_verification(self)
  def test_verify_strict_level(self)
  def test_verify_strict_level_fails_incomplete(self)
  def test_verify_with_enforcement_no_trail(self)
  def test_verify_with_enforcement_no_workflow_steps(self)

### tests\test_t005_tiered_verification.py
  class TestT005TieredVerification():
  def _create_test_trail(self, skill: str, workflow_steps: list[str], tool_count: int, age_seconds: float) -> None
  def test_minimal_level_pass(self)
  def test_minimal_level_fails_duration(self)
  def test_standard_level_pass(self)
  def test_strict_level_pass(self)
  def test_strict_level_fails_incomplete(self)

### tests\test_t005_tracker_integration.py
  pytest.fixture def temp_db_path(tmp_path: Path) -> Path
  pytest.fixture def mock_terminal_id() -> str
  pytest.fixture def sample_workflow_steps() -> list[dict[str, Any]]
  pytest.fixture def initialized_database(temp_db_path: Path) -> None
  class TestTrackerAPICompatibility():
  class TestCacheDatabaseIntegration():
  class TestTerminalIsolation():
  class TestEventLogging():
  class TestPerformanceBaseline():
  def test_initialize_breadcrumb_trail_creates_db_record(self, temp_db_path: Path, mock_terminal_id: str, sample_workflow_steps: list[dict], initialized_database: None) -> None
  def test_set_breadcrumb_updates_database_record(self, temp_db_path: Path, mock_terminal_id: str, sample_workflow_steps: list[dict], initialized_database: None) -> None
  def test_get_active_breadcrumb_trails_returns_db_records(self, temp_db_path: Path, mock_terminal_id: str, sample_workflow_steps: list[dict], initialized_database: None) -> None
  def test_clear_breadcrumb_trail_removes_db_record(self, temp_db_path: Path, mock_terminal_id: str, sample_workflow_steps: list[dict], initialized_database: None) -> None
  def test_cache_falls_back_to_database(self, temp_db_path: Path, mock_terminal_id: str, sample_workflow_steps: list[dict], initialized_database: None) -> None
  def test_cache_and_database_synchronization(self, temp_db_path: Path, mock_terminal_id: str, sample_workflow_steps: list[dict], initialized_database: None) -> None
  def test_trails_from_different_terminals_isolated(self, temp_db_path: Path, sample_workflow_steps: list[dict], initialized_database: None) -> None
  def test_clear_terminal_trails_only_affects_one_terminal(self, temp_db_path: Path, sample_workflow_steps: list[dict], initialized_database: None) -> None
  def test_trail_initialization_creates_event(self, temp_db_path: Path, mock_terminal_id: str, sample_workflow_steps: list[dict], initialized_database: None) -> None
  def test_step_complete_creates_event(self, temp_db_path: Path, mock_terminal_id: str, sample_workflow_steps: list[dict], initialized_database: None) -> None
  def test_events_ordered_by_timestamp(self, temp_db_path: Path, mock_terminal_id: str, sample_workflow_steps: list[dict], initialized_database: None) -> None
  def test_create_trail_performance_baseline(self, temp_db_path: Path, mock_terminal_id: str, sample_workflow_steps: list[dict], initialized_database: None) -> None
  def test_update_trail_performance_baseline(self, temp_db_path: Path, mock_terminal_id: str, sample_workflow_steps: list[dict], initialized_database: None) -> None
  def test_get_active_trails_performance_baseline(self, temp_db_path: Path, mock_terminal_id: str, sample_workflow_steps: list[dict], initialized_database: None) -> None
  def test_cache_hit_performance_baseline(self, temp_db_path: Path, mock_terminal_id: str, sample_workflow_steps: list[dict], initialized_database: None) -> None

### tests\test_tdd_contract_auto_gate.py
  class _Context():
  class _Manager():
  def test_tdd_contract_auto_gate_sets_red_phase(monkeypatch)
  def test_tdd_contract_auto_gate_honors_bypass(monkeypatch)
  def __init__(self, prompt: str) -> None
  def __init__(self) -> None
  def get_phase(self, target_file: str)
  def set_phase(self, target_file: str, phase: str)

### tests\test_tool_inference.py
  class TestToolInference():
  def test_research_tools_mapped_to_research(self)
  def test_requirements_tools_mapped_to_requirements(self)
  def test_tdd_tools_mapped_to_tdd(self)
  def test_verification_tools_mapped_to_verification(self)
  def test_planning_tools_mapped_to_planning(self)
  def test_agent_tools_mapped_to_agent_coordination(self)
  def test_unmapped_tool_returns_none(self)
  def test_step_name_normalization(self)
  def test_custom_tool_mapping(self)
  def test_get_supported_tools(self)
  def test_tool_input_ignored_for_basic_tools(self)
  def test_pattern_based_inference_for_search_tools(self)
  def test_pattern_based_inference_for_read_tools(self)
  def test_pattern_based_inference_for_edit_tools(self)
  def test_exact_match_takes_precedence_over_pattern(self)
  def test_inference_with_mcp_prefix(self)

### tests\test_tracker.py
  def test_tracker_exists()

### tests\test_tracker_fixes.py
  def test_import_from_utils_submodule()
  def test_no_import_error_warnings()
  def test_valid_skill_names_accepted()
  def test_path_traversal_blocked()
  def test_empty_skill_name_allowed()
  def test_whitespace_skill_name()
  def test_registry_load_without_sys_path()
  def test_registry_fallback_to_empty_dict()
  def test_no_file_operations_on_import()
  def test_migration_still_works_explicitly()
  def test_docstring_no_ttl_contradiction()
  def test_max_trail_age_constant_exists()

### tests\test_turn_marker.py
  class _Context():
  def test_ensure_turn_marker_creates_and_stores_turn(monkeypatch)
  def test_ensure_turn_marker_skips_without_terminal()
  def __init__(self) -> None

### tests\test_verification_reminder.py
  def create_step(step_id: str, kind: str, status: str) -> Dict[str, Any]
  class TestCheckVerificationReminderFunctionExists():
  class TestVerificationStepFiltering():
  class TestStatusNotDoneFiltering():
  class TestNeverBlocksBehavior():
  class TestReminderMessageContent():
  class TestMissingStepsDictHandling():
  class TestReturnFormat():
  def test_function_exists(self)
  def test_function_accepts_steps_dict(self)
  def test_filters_by_kind_verification(self)
  def test_ignores_non_verification_steps(self)
  def test_reminds_on_pending_status(self)
  def test_reminds_on_in_progress_status(self)
  def test_no_reminder_for_done_status(self)
  def test_always_returns_allow_true(self)
  def test_never_returns_allow_false(self)
  def test_reminder_includes_pending_step_names(self)
  def test_optional_verification_steps_recognized(self)
  def test_handles_none_steps_gracefully(self)
  def test_handles_empty_dict(self)
  def test_handles_missing_step_fields(self)
  def test_handles_non_dict_steps(self)
  def test_returns_dict_with_allow_key(self)
  def test_returns_dict_with_reminder_key(self)
  def test_reminder_is_string_when_present(self)

### tests\test_workflow_steps_parsing.py
  class TestWorkflowStepsParsing():
  def test_load_workflow_steps_from_code_skill(self)
  def test_load_workflow_steps_from_trace_skill(self)
  def test_load_workflow_steps_from_arch_skill(self)
  def test_load_workflow_steps_from_nonexistent_skill(self)
  def test_load_workflow_steps_from_malformed_frontmatter(self, tmp_path)

## Config Files
### hooks\hooks.json
```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python \"$CLAUDE_PLUGIN_ROOT/src/skill_guard/StopHook_skill_execution_gate.py\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### .claude-plugin\plugin.json
```json
{
  "name": "skill-guard",
  "description": "Universal skill auto-discovery and enforcement for Claude Code",
  "version": "2.1.0"
}
```

### pyproject.toml
```json
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "skill-guard"
version = "1.0.0"
description = "Universal skill auto-discovery and enforcement for Claude Code"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [
    {name = "CSF NIP", email = "noreply@csf.nip"},
]
keywords = [
    "claude-code",
    "claude-plugin",
    "claude-skill",
    "auto-discovery",
    "enforcement",
]
classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

dependencies = [
    "pyyaml",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-timeout>=2.0.0",
    "ruff>=0.1.0",
]
test = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-timeout>=2.0.0",
]
all = ["skill-guard[dev,test]"]

[project.urls]
Homepage = "https://github.com/yourusername/skill-guard"
Documentation = "https://github.com/yourusername/skill-guard#readme"
Repository = "https://github.com/yourusername/skill-guard"
Issues = "https://github.com/yourusername/skill-guard/issues"

[tool.hatch.build.targets.wheel]
packages = ["src/skill_guard"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "-v --cov=src/skill_guard --cov-report=term-missing --timeout=30"

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
ignore = ["E501"]  # Line length handled by formatter

[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

## Documentation
### README.md (truncated)
# skill-guard

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Version](https://img.shields.io/badge/version-2.0.0-brightgreen)
![Tests](https://img.shields.io/badge/tests-10%20passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-36%25-yellow)

**Python Library: Skill execution enforcement with breadcrumb-based verification**

> **⚠️ IMPORTANT**: This is a **Python library**, NOT a user-facing skill. You cannot invoke `/skill-guard` as a command. This package is used **internally by Claude Code hooks** to enforce skill execution patterns when users invoke skills.

Enforces skill execution patterns through breadcrumb tracking, ensuring skills follow their documented workflows and providing self-verification.

## 📚 What This Is

**This is NOT a Claude skill** - it's a Python library that hooks import:

```python
# In your hooks:
...

### CHANGELOG.md (truncated)
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **skill_forced_eval Hook**: Skill forced-evaluation hook migrated from `UserPromptSubmit_modules/` to package
  - Enumerates all skills with YES/NO when slash command detected
  - Multi-terminal isolation via terminal-scoped state files
  - TTL-based stale data cleanup (300 seconds)
  - Tool conflict detection (Bash vs read-only skills)
  - Canonical location: `src/skill_guard/skill_forced_eval.py`
  - Symlink: `P:/.claude/hooks/UserPromptSubmit_modules/skill_forced_eval.py`

## [2.0.0] - 2026-03-14

...
