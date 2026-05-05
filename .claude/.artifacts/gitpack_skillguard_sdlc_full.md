# GitPack: skill-guard + cc-skills-sdlc hooks
**Generated:** 2026-05-04T11:12:38.503346
**Purpose:** Debug hook firing and manual skill invocation issues

## HOOK REGISTRATION OVERVIEW

```
  skill-guard: 41 file(s) in P:/packages/skill-guard/src/skill_guard
  sdlc/code_v3.0/hooks: 5 file(s) in P:/packages/cc-skills-sdlc/skills/code_v3.0/hooks
  sdlc/rca/hooks: 10 file(s) in P:/packages/cc-skills-sdlc/skills/rca/hooks
  sdlc/refactor/hooks: 6 file(s) in P:/packages/cc-skills-sdlc/skills/refactor/hooks
  sdlc/design/hooks: 2 file(s) in P:/packages/cc-skills-sdlc/skills/design/hooks
  sdlc/pre-mortem/hooks: 2 file(s) in P:/packages/cc-skills-sdlc/skills/pre-mortem/hooks
  sdlc/hooks.json: P:/packages/cc-skills-sdlc/hooks
    ERROR: [Errno 13] Permission denied: 'P:/packages/cc-skills-sdlc/hooks'
```

## skill-guard
**Path:** `P:/packages/skill-guard/src/skill_guard`
**Files (41):**

### `__init__.py` (3,227 bytes)
```python

```

### `_skill_frontmatter_loader.py` (12,410 bytes)
```python
def _normalize_string_list(value): list[str]
def _infer_contract_type(frontmatter): str
def _load_skill_frontmatter(skill_name): dict[str, Any] | None
def _validate_skill_frontmatter(skill_name): list[str]
```

### `__init__.py` (1,597 bytes)
```python

```

### `cache.py` (8,712 bytes)
```python
class BreadcrumbStateCache:
    def __init__(self, max_size, ...): None
    def _get_cache_key(self, skill_name, ...): str
    def get_state(self, skill_name, ...): dict[str, Any] | None
    def update_state(self, skill_name, state, ...): None
    def _load_from_log(self, skill_name, ...): dict[str, Any] | None
    def _evict_if_needed(self, ...): None
    def snapshot_all(self, ...): None
    def _snapshot_state(self, skill_name, state, ...): None
    def invalidate(self, skill_name, ...): None
    def clear_all(self, ...): None
    def get_stats(self, ...): dict[str, Any]
def __init__(self, max_size): None
def _get_cache_key(self, skill_name): str
def get_state(self, skill_name): dict[str, Any] | None
def update_state(self, skill_name, state): None
def _load_from_log(self, skill_name): dict[str, Any] | None
def _evict_if_needed(self): None
def snapshot_all(self): None
def _snapshot_state(self, skill_name, state): None
def invalidate(self, skill_name): None
def clear_all(self): None
def get_stats(self): dict[str, Any]
```

### `database.py` (9,397 bytes)
```python
def _is_connection_valid(conn): bool
def get_connection(db_path): sqlite3.Connection | None
def close_connection(db_path): None
def _get_schema_version(conn): int
def _run_migrations(conn, from_version): None
def initialize_schema(conn): None
```

### `enforcement.py` (9,418 bytes)
```python
class EnforcementLevel:
    def __str__(self, ...): str
def get_enforcement_level(skill_name): EnforcementLevel
def _normalize_workflow_step_ids(workflow_steps): list[str]
def verify_with_enforcement(skill_name, trail, duration_seconds, tool_count): tuple[bool, str]
def _verify_minimal(workflow_steps, completed_steps, duration_seconds, tool_count): tuple[bool, str]
def _verify_standard(workflow_steps, completed_steps, duration_seconds, tool_count): tuple[bool, str]
def _verify_strict(workflow_steps, completed_steps, duration_seconds, tool_count, steps): tuple[bool, str]
def __str__(self): str
```

### `PostToolUse_breadcrumb_tracker.py` (4,628 bytes)
```python
def _get_current_skill(data): str | None
def run(data): dict | None
```

### `UserPromptSubmit_breadcrumb_init.py` (4,067 bytes)
```python
def _extract_skill_name(prompt): str | None
def initialize_breadcrumb_for_skill(skill_name): bool
def process_prompt_for_breadcrumbs(prompt, data): str | None
```

### `inference.py` (6,252 bytes)
```python
def _infer_step_from_tool(tool_name, tool_input): str | None
def _normalize_step_name(step): str
def infer_step_from_tool_use(tool_name, tool_input): str | None
def get_supported_tools(): list[str]
def add_tool_mapping(tool_name, step_name): None
def remove_tool_mapping(tool_name): None
def clear_custom_mappings(): None
```

### `log.py` (7,903 bytes)
```python
def _get_log_dir(): Path
def _get_log_file(skill_name): Path
class AppendOnlyBreadcrumbLog:
    def __init__(self, skill_name, ...): None
    def append(self, entry, ...): None
    def replay(self, ...): list[dict[str, Any]]
    def _rotate_log(self, ...): None
    def clear(self, ...): None
def cleanup_old_log_dirs(age_days): dict[str, list[str]]
def __init__(self, skill_name): None
def append(self, entry): None
def replay(self): list[dict[str, Any]]
def _rotate_log(self): None
def clear(self): None
```

### `migration.py` (17,613 bytes)
```python
def validate_jsonl_files(terminal_id): tuple[bool, list[str]]
def validate_json_state(terminal_id): tuple[bool, list[str]]
def migrate_jsonl_to_events(terminal_id, db_path): bool
def migrate_json_state_to_trails(terminal_id, db_path): bool
def _ensure_schema(db_path): bool
def migrate_terminal(terminal_id, db_path): bool
def migrate_all_terminals(db_path): tuple[int, int]
def rollback_migration(terminal_id, db_path): bool
def cli_migrate(db_path, terminal_id): int
def cli_migrate_all(db_path): int
def cli_rollback(db_path, terminal_id): int
```

### `sqlite_backend.py` (11,483 bytes)
```python
def create_trail(db_path, skill, terminal_id, workflow_steps, steps): str
def update_trail(db_path, run_id, completed_steps, current_step, steps): None
def append_event(db_path, trail_id, event_type, event_data): None
def get_active_trails(db_path, terminal_id): list[dict[str, Any]]
def get_trail_by_run_id(db_path, run_id): dict[str, Any] | None
def delete_trail(db_path, run_id): bool
def clear_terminal_trails(db_path, terminal_id): int
```

### `tracker.py` (33,179 bytes)
```python
def _ensure_database_initialized(): bool
def _append_ledger_event(event_type, payload): None
def _get_breadcrumb_dir(): Path
def _get_breadcrumb_file(skill_name): Path
def _load_workflow_steps(skill_name): WorkflowStepsResult
def _regex_workflow_steps_fallback(content, defaults): list[dict]
def initialize_breadcrumb_trail(skill_name, force): None
def set_breadcrumb(skill_name, step_name, evidence): None
def _windows_safe_unlink(path): None
def get_breadcrumb_trail(skill_name): dict[str, Any] | None
def verify_breadcrumb_trail(skill_name): tuple[bool, str]
def clear_breadcrumb_trail(skill_name): None
def clear_all_breadcrumb_trails(): None
def cleanup_session_breadcrumbs(): int
def cleanup_stale_breadcrumbs(): int
def verify_session_isolation(trail): bool
def get_active_breadcrumb_trails(): list[dict[str, Any]]
def format_breadcrumb_status(trail): str
```

### `exceptions.py` (673 bytes)
```python

```

### `execution_hooks.py` (9,613 bytes)
```python
def _extract_slash_command(prompt): str | None
def _artifact_written(tool_name, tool_input): bool
def handle_pre_tool_use(data, runtime): dict[str, Any]
def _parse_transcript_for_response(transcript_path): str
def handle_stop(data): dict[str, Any]
def pre_tool_use_main(): 
def stop_main(): 
```

### `execution_run.py` (6,103 bytes)
```python
class ExecutionEvent:
    def to_jsonable(self, ...): dict[str, Any]
    def from_jsonable(cls, d, ...): ExecutionEvent
class ExecutionRun:
    def to_jsonable(self, ...): dict[str, Any]
    def from_jsonable(cls, d, ...): ExecutionRun
    def new(cls, skill_name, contract_type, terminal_id, session_id, ...): ExecutionRun
def to_jsonable(self): dict[str, Any]
def from_jsonable(cls, d): ExecutionEvent
def to_jsonable(self): dict[str, Any]
def from_jsonable(cls, d): ExecutionRun
def new(cls, skill_name, contract_type, terminal_id, session_id, required_artifacts): ExecutionRun
```

### `execution_runtime.py` (10,220 bytes)
```python
def validate_response_requirements(response_text, requirements): ResponseCheckResult
class ExecutionRuntime:
    def __init__(self, store, ...): 
    def _detect_terminal_id(self, ...): str
    def create_run(self, skill_name, contract_type, session_id, required_artifacts, ...): ExecutionRun
    def async_create_run(self, skill_name, contract_type, session_id, required_artifacts, ...): ExecutionRun
    def load_active_run(self, ...): ExecutionRun | None
    def record_tool_use(self, run, tool_name, allowed, reason, ...): None
    def record_artifact_created(self, run, path, ...): None
    def evaluate_completion(self, run, response_text, ...): str
    def finalize_run(self, run, status, ...): None
def __init__(self, store): 
def _detect_terminal_id(self): str
def create_run(self, skill_name, contract_type, session_id, required_artifacts, allowed_tools): ExecutionRun
def async_create_run(self, skill_name, contract_type, session_id, required_artifacts, allowed_tools): ExecutionRun
def load_active_run(self): ExecutionRun | None
def record_tool_use(self, run, tool_name, allowed, reason): None
def record_artifact_created(self, run, path): None
def evaluate_completion(self, run, response_text): str
def finalize_run(self, run, status): None
```

### `execution_store.py` (4,911 bytes)
```python
class ExecutionStore:
    def load_active_run(self, ...): ExecutionRun | None
    def save_run(self, run, ...): None
    def end_run(self, run, status, ...): None
    def append_event(self, event, ...): None
    def replay_events(self, ...): list[ExecutionEvent]
    def console_dir(self, ...): Path
class ArtifactsExecutionStore:
    def __init__(self, terminal_id, ...): 
    def console_dir(self, ...): Path
    def _state_path(self, ...): Path
    def _events_path(self, ...): Path
    def _atomic_write_json(self, path, data, ...): None
    def load_active_run(self, ...): ExecutionRun | None
    def save_run(self, run, ...): None
    def end_run(self, run, status, ...): None
    def append_event(self, event, ...): None
    def replay_events(self, ...): list[ExecutionEvent]
def load_active_run(self): ExecutionRun | None
def save_run(self, run): None
def end_run(self, run, status): None
def append_event(self, event): None
def replay_events(self): list[ExecutionEvent]
def console_dir(self): Path
def __init__(self, terminal_id): 
def console_dir(self): Path
def _state_path(self): Path
def _events_path(self): Path
def _atomic_write_json(self, path, data): None
def load_active_run(self): ExecutionRun | None
def save_run(self, run): None
def end_run(self, run, status): None
def append_event(self, event): None
def replay_events(self): list[ExecutionEvent]
```

### `hook_compat.py` (1,267 bytes)
```python
class _HookResult:
    def __init__(self, context, tokens, priority, tokens_added, ...): None
    def is_empty(self, ...): bool
    def empty(cls, ...): _HookResult
def _register_hook(name, priority): Callable[[Callable[..., Any]], Callable[..., Any]]
def __init__(self, context, tokens, priority, tokens_added): None
def is_empty(self): bool
def empty(cls): _HookResult
def decorator(func): Callable[..., Any]
```

### `phases.py` (784 bytes)
```python

```

### `__init__.py` (2,978 bytes)
```python
def __getattr__(name): 
```

### `skill_execution_tracker.py` (7,635 bytes)
```python
class SkillExecutionTracker:
    def __init__(self, ...): 
    def _import_functions(self, ...): 
    def _load_workflow_steps(self, skill_name, ...): 
    def process(self, tool_name, tool_input, tool_response, ...): dict[str, Any]
    def _update_checkpoint_task_with_skill(self, skill_name, ...): None
    def _extract_skill_name(self, tool_input, ...): str
def __init__(self): 
def _import_functions(self): 
def _load_workflow_steps(self, skill_name): 
def process(self, tool_name, tool_input, tool_response): dict[str, Any]
def _update_checkpoint_task_with_skill(self, skill_name): None
def _extract_skill_name(self, tool_input): str
```

### `__init__.py` (154 bytes)
```python

```

### `PreToolUse_context_sufficiency_gate.py` (3,316 bytes)
```python
def _load_skill_autonomy_registry(): 
def run(data): dict[str, Any]
```

### `PreToolUse_import_deletion_guard.py` (14,084 bytes)
```python
def extract_import_symbols(text): set[str]
def extract_removed_symbols(old_string, new_string): set[str]
def has_symbol_search_this_turn(symbol, tool_events): bool
def extract_module_name(import_line): str | None
def has_investigation_evidence(old_string, removed_symbols, file_path, tool_events): bool
def load_this_turn_events(session_id, terminal_id): list[dict] | None
def has_bypass_flag(user_message): bool
def _iter_candidate_edits(tool_name, tool_input): list[tuple[str, str, str]]
def evaluate(data): dict | None
def run(data): dict | None
def main(): int
def _command_mentions_symbol(command): bool
```

### `PreToolUse_skill_dir_gate.py` (4,958 bytes)
```python
def _safe_id(value): str
def _skill_context_path(terminal_id): Path
def _load_state(terminal_id): dict | None
def _is_skill_dir_in_command(command, expected_dir): bool
def _get_command_from_input(tool_name, tool_input): str | None
def run(data): dict
def main(): None
```

### `PreToolUse_skill_pattern_gate.py` (44,376 bytes)
```python
def _clear_shadowed_hook_packages(): None
def _extract_command(tool_name, tool_input): str
def _check_regex(command, pattern): bool
def _check_daemon_intent(command, skill, timeout): bool
def _read_pending_state(): dict | None
def _read_pending_command_intent(): dict | None
def _log_disagreement(skill, command, regex_result, daemon_result, decision): None
def _log_coherence_event(event, skill, tool_name, allowed, decision): None
def _check_first_tool_coherence(tool_name, state): dict
def _check_first_command_pattern(tool_name, tool_input, state): dict
def _load_frontmatter_execution_config(skill_name): dict
def _check_workflow_steps(tool_name, tool_input, slash_command): dict
def _check_state_file_intent(tool_name): dict
def _check_topic_drift(tool_name, tool_input, user_message, state): dict
def _check_knowledge_skill(skill, state): dict
def _check_execution_pattern(tool_name, tool_input, skill, state): dict
def handle_pre_tool_use(data): dict
def _make_decision(skill, command, regex_match, daemon_match, intent_enabled, pattern): dict
def main(): 
```

### `PreToolUse_skill_question_gate.py` (4,421 bytes)
```python
def _get_marker_path(session_id, prefix): Path
def _load_json(path): dict
def _save_json(path, data): None
def run(data): dict[str, Any]
```

### `PreToolUse_skill_script_path_gate.py` (2,694 bytes)
```python
def _extract_script_path(command): str | None
def run(data): dict | None
def main(): None
```

### `skill_auto_discovery.py` (14,291 bytes)
```python
def _normalize_list(value): list[str]
def _infer_contract_type(frontmatter, category, skill_name): str
def discover_all_skills(skills_dir): dict
def _parse_skill_frontmatter(skill_md): dict | None
def get_skill_config(skill_name, explicit_registry): dict
def discover_hooks(skills_dir): list[dict]
def _parse_skill_hooks(skill_md, skill_name): list[dict]
def _detect_script_pattern(skill_name): str
```

### `skill_execution_state.py` (28,295 bytes)
```python
def _get_legacy_skill_metadata_cache(): 
def detect_terminal_id(): str
def _atomic_write_json(path, data): None
def sanitize_terminal_id(terminal_id): str
def _get_state_file(): Path
def _get_state_dir(): Path
def _get_state_file_for_terminal(terminal_id): Path
def _read_pending_state_file(terminal_id): dict[str, Any] | None
def _write_pending_state_file(terminal_id, state): bool
def _clear_pending_state_file(terminal_id): None
def _load_skill_frontmatter(skill_name): dict[str, Any] | None
def _get_active_turn_scope(): tuple[str, str]
def _get_ledger_module(): 
def set_skill_loaded(skill_name, required_tools, pattern, hint, intent_enabled, prompt_fingerprint): None
def record_tool_use(tool_name, tool_input): None
def transition_phase(to_state): bool
def read_pending_state(): dict | None
def mark_first_tool_validated(): None
def mark_first_command_validated(): None
def update_workflow_stage(active_step, step_definition, done_criteria, do_not_distract, step_index, total_steps): None
def clear_state(): None
def migrate_legacy_state(): None
def cleanup_stale_state_files(stale_timeout): int
```

### `skill_forced_eval.py` (21,194 bytes)
```python
def _get_state_dir(): Path
def _get_terminal_id(context): str
def _safe_id(value): str
def _discover_registered_skills(): list[str]
def _get_skill_frontmatter(skill_name): dict
def _parse_frontmatter(skill_path): dict
def _get_all_skill_metadata(): dict[str, dict]
def _get_registered_skills(): list[str]
def _get_skill_metadata(): dict[str, dict]
def _clear_caches(): None
def _is_question_context(prompt): bool
def _extract_slash_commands(prompt): list[str]
def _get_matching_skills(prompt): list[str]
def _format_skill_list(skills, metadata): str
def _detect_tool_conflicts(metadata, skills): list[tuple[str, str]]
def _format_conflict_report(conflicts): str
def _save_eval_state(context, invoked_skills, metadata): None
def _load_eval_state(context): dict | None
def _clear_eval_state(context): None
def _cleanup_stale_state_files(): int
def skill_forced_eval_hook(context): HookResult
```

### `skill_metadata_advisory.py` (10,359 bytes)
```python
def _normalize_list(value): list[str]
def _classify_contract(metadata): str
def _enhancement_reasons(metadata): list[str]
def _build_warning(skill_name, metadata, reasons): str
def _build_notification_message(skill_name, reasons): str
def _get_session_id(context): str
def skill_metadata_advisory(context): str | None
def skill_metadata_advisory_hook(context): HookResult
def add_notification(notification_type, message, source, priority, session_id): None
def clear_by_type(notification_type, source, session_id): int
```

### `slash_command_observability.py` (11,149 bytes)
```python
def _claude_dir(): Path
def _commands_dir(): Path
def _skills_dir(): Path
def _normalize_prompt(prompt): str
def normalize_prompt(prompt): str
def extract_slash_command(prompt): tuple[str | None, str]
def extract_command_name(prompt): str | None
def is_slash_prompt(prompt): bool
def _local_command_paths(commands_dir): dict[str, Path]
def _skill_paths(skills_dir): dict[str, Path]
def _extract_backing_skill(command_path): str
def classify_slash_command(command_name): dict[str, str]
def _resolve_session_id(context): str
def _resolve_terminal_id(context): str
def _resolve_turn_id(context, session_id, terminal_id): str
def _append_slash_event(): bool
def record_slash_request(context, command_name, command_args): bool
def record_slash_resolution(context, command_name, command_args): bool
def record_slash_outcome(context, command_name, command_args): bool
def slash_command_observability_hook(context): HookResult
def append_tool_event(): bool
def get_active_turn(session_id, terminal_id): str | None
def resolve_session_id(explicit): str
```

### `StopHook_skill_execution_gate.py` (56,288 bytes)
```python
def _extract_text_content(message_content): str
def _extract_tool_use_content(message_content): list[dict]
def _parse_transcript_snapshot(input_data): dict
def _get_transcript_snapshot(input_data): dict
def extract_user_prompt(input_data): str
def _extract_slash_command(prompt): str | None
def log(msg): None
def log_event(event, data): None
def _get_governance_state_file(): Path
def _read_governance_state(): dict | None
def _update_governance_retry(state): None
def _clear_governance_state(): None
def _normalize_tool_names(items): list[str]
def extract_tools_used(input_data): list[str]
def _get_first_bash_command_from_transcript(input_data): str | None
def extract_response_text(input_data): str
def _check_governance_markers(input_data): dict
def _get_state_file(): Path
def _read_state(): dict | None
def _clear_state(): None
def _is_stale(state): bool
def _check_pattern_match(command, pattern): bool
def _tool_mentions_artifact(tool_event, artifact_name): bool
def _missing_required_phase_artifacts(state, tool_history): list[str]
def _normalize_list(value): list[str]
def _contract_type(state): str
def _requires_execution_tools(state): bool
def validate_execution(state, tool_history): dict
def run(input_data): dict | None
def check_verification_reminder(steps): dict[str, bool | str | None]
def main(): 
def _workflow_block(reason): dict
def _is_help_only_request(prompt): bool
def _log_slash_outcome(outcome, reason): None
def record_slash_outcome(): 
```

### `tdd_contract_auto_gate.py` (3,781 bytes)
```python
def _is_tdd_bypassed(prompt): bool
def _extract_target_file(prompt, skill_name): str | None
def _get_tdd_manager(context): 
def tdd_contract_auto_gate(context): bool
def tdd_contract_auto_gate_hook(context): HookResult
```

### `turn_marker.py` (2,599 bytes)
```python
def _resolve_context_value(context, key, default): str
def ensure_turn_marker(context): str | None
def write_turn_marker(context): HookResult
def get_active_turn(session_id, terminal_id): str | None
def start_turn(session_id, terminal_id, prompt, transcript_path): str
```

### `user_prompt_submit_hook.py` (7,192 bytes)
```python
def _map_contract_type(config_contract): str
def _get_allowed_tools(skill_name): list[str]
def _get_required_artifacts(skill_name): list[str]
def _get_response_requirements(skill_name): dict
def handle_user_prompt_submit(data): dict
def user_prompt_submit_main(): 
```

### `__init__.py` (594 bytes)
```python

```

### `terminal_detection.py` (5,937 bytes)
```python
def _detect_console_window(): str
def _read_from_state_file(): str | None
def detect_terminal_id(): str
def detect_terminal_id_with_source(): tuple[str, str]
```

### `terminal_id.py` (1,821 bytes)
```python
def normalize_terminal_id(raw_id, source): str
```

## sdlc/code_v3.0/hooks
**Path:** `P:/packages/cc-skills-sdlc/skills/code_v3.0/hooks`
**Files (5):**

### `detect_continuous_mode.py` (4,830 bytes)
```python
def detect_continuous_mode(user_query): bool
def set_continuous_mode_flag(enabled): None
def set_environment_flag(enabled): None
def main(): 
```

### `PostToolUse_breadcrumb_tracker.py` (2,844 bytes)
```python
def detect_completed_step(tool_name, tool_input): str | None
def main(): 
```

### `PreToolUse_plan_consumer_gate.py` (3,247 bytes)
```python
def _add_import_paths(): None
def _should_skip_for_path(file_path): bool
def _required_phase(): int
def main(): None
```

### `SessionStart_breadcrumb_init.py` (1,411 bytes)
```python
def main(): 
```

### `validate_code_phase_order.py` (4,620 bytes)
```python
def main(): 
```

## sdlc/rca/hooks
**Path:** `P:/packages/cc-skills-sdlc/skills/rca/hooks`
**Files (10):**

### `hook_error_rca.py` (44,480 bytes)
```python
def get_settings_file(): Path
def get_hooks_dir(): Path
def validate_state_dir(state_dir): Path
def validate_hook_path(hook_path, hooks_dir): bool
def validate_diagnostics_dir(diagnostics_dir, hooks_dir): Path
def get_state_dir(): Path
def get_cc_errors(): Path
def _load_settings(): dict
def resolve_hook_file(command): Path | None
def validate_matcher_pattern(matcher, tool_name): tuple[bool, str]
def enumerate_registrations(event_type, tool_name): list[HookRegistration]
def _load_cc_errors_entries(): list[dict]
def _extract_hook_from_error_type(error_type): str
def _is_timeout_entry(entry): bool
def build_diagnostic_sweep(registrations, cc_errors_entries, hours): dict
def build_signal_source_verification(test_results, registrations): dict
def check_recent_errors(hook_name, hours, use_regex, return_metadata, _cached_entries): list[dict] | dict
def test_hook_isolated(reg, tool_name): HookTestResult
def _stage1_enumerate(event_type, tool_name): list[HookRegistration]
def _stage2_test(registrations, tool_name): tuple[list[HookTestResult], dict[str, list]]
def _stage3_classify(test_results, registrations, tool_name, event_type, error_log_evidence): list[str]
def _save_state(event_type, tool_name, registrations, test_results, root_causes, error_log_evidence): dict
def run_full_investigation(event_type, tool_name): dict
def _get_verdict(result): str
def _get_hook_file(result): str
def no_handwave_gate(test_results, root_cause_statement): tuple[bool, str]
def main(): 
```

### `PostToolUse_rca_action_tracker.py` (9,153 bytes)
```python
def get_current_terminal_id(): str
def get_action_file_path(session_id): Path
def truncate_for_preview(text, max_length): str
def sanitize_tool_input(tool_input): dict
def load_actions_graph(session_id, terminal_id): dict
def save_actions_graph(graph, session_id): None
def record_action(graph, action_type, tool_used, tool_input, tool_output, phase): dict
def check_divergence(graph, expected_path): dict | None
def main(): 
```

### `PostToolUse_rca_init.py` (10,640 bytes)
```python
def validate_stdin_payload(raw_stdin): dict
def normalize_skill_name(value): str
def extract_skill_name(data): str
def get_current_terminal_id(): str
def initialize_state(): dict
def main(): 
class FileLock:
    def __init__(self, lock_path, timeout, ...): 
    def __enter__(self, ...): 
    def __exit__(self, ...): 
def __init__(self, lock_path, timeout): 
def __enter__(self): 
def __exit__(self): 
class FileLock:
    def __init__(self, lock_path, timeout, ...): 
    def __enter__(self, ...): 
    def __exit__(self, ...): 
def __init__(self, lock_path, timeout): 
def __enter__(self): 
def __exit__(self): 
```

### `PostToolUse_rca_phase_tracker.py` (17,692 bytes)
```python
def detect_phase_from_output(output): int
def detect_phase_from_tool(tool_name, tool_input): int
def detect_execution(tool_name, tool_input, tool_output): bool
def detect_successful_tool_execution(payload): bool
def detect_delegation(tool_name, tool_input, tool_output): bool
def detect_problem_type(tool_output): str | None
def check_auto_research_trigger(tool_output): dict | None
def detect_diagnostic_sweep(tool_output): bool
def main(): 
class FileLock:
    def __init__(self, lock_path, timeout, ...): 
    def __enter__(self, ...): 
    def __exit__(self, ...): 
def __init__(self, lock_path, timeout): 
def __enter__(self): 
def __exit__(self): 
class FileLock:
    def __init__(self, lock_path, timeout, ...): 
    def __enter__(self, ...): 
    def __exit__(self, ...): 
def __init__(self, lock_path, timeout): 
def __enter__(self): 
def __exit__(self): 
```

### `PostToolUse_rca_research_storage.py` (7,173 bytes)
```python
def extract_library_from_research(query, results): str | None
def extract_content_from_results(results): str
def main(): 
```

### `PostToolUse_rca_search_validator.py` (12,997 bytes)
```python
def validate_stdin_payload(raw_stdin): dict
def classify_search_pattern(pattern): str
def get_current_terminal_id(): str
def load_search_state(): dict
def save_search_state(state): None
def extract_grep_pattern(tool_input): str
def should_warn_user(state): tuple[bool, str]
def main(): 
class FileLock:
    def __init__(self, lock_path, timeout, ...): 
    def __enter__(self, ...): 
    def __exit__(self, ...): 
def __init__(self, lock_path, timeout): 
def __enter__(self): 
def __exit__(self): 
class FileLock:
    def __init__(self, lock_path, timeout, ...): 
    def __enter__(self, ...): 
    def __exit__(self, ...): 
def __init__(self, lock_path, timeout): 
def __enter__(self): 
def __exit__(self): 
```

### `SessionEnd_rca_cleanup.py` (9,982 bytes)
```python
def ingest_rca_to_cks(state): 
def extract_findings_from_state(state): dict
def cleanup_active_session(state): None
def main(): 
class FileLock:
    def __init__(self, lock_path, timeout, ...): 
    def __enter__(self, ...): 
    def __exit__(self, ...): 
def __init__(self, lock_path, timeout): 
def __enter__(self): 
def __exit__(self): 
class FileLock:
    def __init__(self, lock_path, timeout, ...): 
    def __enter__(self, ...): 
    def __exit__(self, ...): 
def __init__(self, lock_path, timeout): 
def __enter__(self): 
def __exit__(self): 
```

### `StopHook_rca_contract.py` (36,251 bytes)
```python
def _get_logger(): 
def _get_current_turn_tools(tool_events): set[str]
def _load_turn_scoped_tool_events(session_id, terminal_id): list[dict]
def _has_verification_this_turn(tool_events): bool
def _contains_transcript_only_claim(content): bool
def _normalize_section_name(name): str
def _get_section(sections, field): str
def _parse_hypotheses_from_text(text): list[dict[str, str]]
def _is_absence_claim(text): bool
def _count_diverse_tools(tool_events): int
def _extract_sections(response): dict[str, str]
def _section_exists(sections, field): bool
def _section_has_current_turn_evidence(sections, field): bool
def _find_function_mentions(func_name): int
def _extract_function_names(text): list[str]
def _count_hypothesis_rows(hypothesis_text): int
def _check_dead_code_auto(executed_path, root_cause, falsifier): list[str]
def _has_call_site_evidence(executed_path, evidence): bool
def _load_band_aid_state(terminal_id): BandAidState
def _save_band_aid_state(terminal_id, state): None
def _extract_fix_files(fix_text): list[str]
def _check_band_aid_chain(fix_text, terminal_id): list[str]
def _extract_file_paths_from_path(executed_path): list[str]
def _get_file_mtime(file_path): float | None
def _check_stale_execution_path(executed_path, rca_timestamp): list[str]
def _contains_unverified_token(text): bool
def _detect_single_rc_escape(response): bool
def _detect_urgency(response): bool
def _format_structured_feedback(block_reasons, hypothesis_details): str
def _validate_evidence_tier_labels(evidence): list[str]
def _validate_adversarial_hypothesis(sections, tool_events): list[str]
def _validate_artifact_paths_exist(sections): list[str]
def _extract_artifact_paths(evidence_text): list[str]
def _validate_evidence_bindings(sections, tool_events, session_id, terminal_id): list[str]
def _validate_rca_contract(data, response, tool_events, rca_turn, session_id, terminal_id): tuple[bool, list[str]]
def check(data): dict | None
def run(data): dict | None
```

### `StopHook_rca_enforcement.py` (12,403 bytes)
```python
def get_current_terminal_id(): str
def load_hook_error_gate(): 
def is_state_stale(state): bool
def main(): 
```

### `StopHook_rca_reflector.py` (7,458 bytes)
```python
def _get_state_file(session_id, terminal_id): Path
def _load_state(session_id, terminal_id): dict
def _save_state(session_id, terminal_id, state): None
def _cleanup_stale_state_files(): None
def _detect_premature_convergence(response, alt_count): str | None
def _is_catch22_spiral(state, tool_name, error): bool
def _update_catch22_state(state, tool_name, error): dict
def _has_evidence_free_fix(response): bool
def _detect_zero_plan(response, tool_event_count): str | None
def check(data): dict | None
def run(data): dict | None
```

## sdlc/refactor/hooks
**Path:** `P:/packages/cc-skills-sdlc/skills/refactor/hooks`
**Files (6):**

### `ledger_append.py` (546 bytes)
```python

```

### `PostToolUse_refactor_transition.py` (3,101 bytes)
```python
def main(): 
```

### `PostToolUse_refactor_validator.py` (2,211 bytes)
```python
def validate_tool_output(data): dict
def extract_errors(output): list
def main(): 
```

### `PreToolUse_refactor_gate.py` (892 bytes)
```python
def main(): 
```

### `state_manager_refactor.py` (6,203 bytes)
```python
def write_state(phase, allowed_tools, evidence, expires_in): 
def append_ledger(step, event, session_id): 
def read_state(): dict | None
def clear_state(): 
def get_current_phase_evidence(phase): dict
def advance_if_complete(current_phase, evidence): str | None
```

### `Stop_refactor_verifier.py` (4,856 bytes)
```python
def get_git_tags(): list[str]
def read_ledger_entries(session_id): list[dict]
def get_artifacts_dir(state): Path
def check_artifacts(state): list[str]
def verify(state): dict
def main(): 
```

## sdlc/design/hooks
**Path:** `P:/packages/cc-skills-sdlc/skills/design/hooks`
**Files (2):**

### `stop_if_unverified.py` (2,419 bytes)
```python
def _terminal_id(): str
def _state_dir(): Path
def _state_file(): Path
def main(): None
```

### `verify_claims.py` (2,616 bytes)
```python
def _terminal_id(): str
def _state_dir(): Path
def _state_file(): Path
def verify(run_id, domain, claims_count): str
def main(): None
```

## sdlc/pre-mortem/hooks
**Path:** `P:/packages/cc-skills-sdlc/skills/pre-mortem/hooks`
**Files (2):**

### `hooks.json` (2 bytes)
```json
{}
```
### `Stop_hook_premortem_quality_gate.py` (3,572 bytes)
```python
def run(data): dict
def _write_premortem_changelog(data): None
```

## sdlc/hooks.json
**Path:** `P:/packages/cc-skills-sdlc/hooks`
**Files (1):**

### `hooks.json` (14 bytes)
```json
{
  "hooks": {}
}
```


## FULL SOURCE APPENDIX

