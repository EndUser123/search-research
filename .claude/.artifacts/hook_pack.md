# HOOK SIGNATURE PACK

## PACK INFO
Generated: 2026-05-22
Scope: All global hooks + plugin hooks + package hooks

### P:/.claude/hooks/.archive/PostToolUse_drift_detector.py
  def get_parent_pid(0 params) -> int
  def get_goal_from_state(0 params) -> ?
  def check_alignment(2 params) -> dict
  def write_drift_status(2 params) -> ?
  def get_recent_actions(1 params) -> ?
  def get_transcript_excerpt(0 params) -> str

### P:/.claude/hooks/.claudeskillsgtohooks/gto_failure_capture.py
  def main(0 params) -> int

### P:/.claude/hooks/.git-hooks/install_pycache_hook.py
  def main(0 params) -> int

### P:/.claude/hooks/__lib/air_gap_classifier.py
  def _get_session_id(1 params) -> str
  def _get_terminal_id(0 params) -> str
  def _get_transcript_path(0 params) -> ?
  def _capture_git_diff(1 params) -> dict
  def _get_cwd(1 params) -> str
  def classify_gap(3 params) -> ?

### P:/.claude/hooks/__lib/anti_lazy_policy.py
  def extract_topic_keywords(1 params) -> ?
  def load_investigation_ledger(0 params) -> ?
  def check_topic_relevant_investigation(1 params) -> bool
  def check_investigation_in_ledger(0 params) -> bool
  def is_diagnostic_topic(1 params) -> bool

### P:/.claude/hooks/__lib/api_breakage_detector.py
  class Severity (0 methods)
  class BreakingChange (1 methods)
  class BreakageReport (2 methods)
  class APIBreakageDetector (7 methods)
  def compare_characterizations(2 params) -> BreakageReport
  def to_dict(1 params) -> ?

### P:/.claude/hooks/__lib/argument_forwarding_validator.py
  class ValidationResult (1 methods)
  class ArgumentForwardingValidator (5 methods)
  class PythonArgumentForwardingValidator (5 methods)
  class PowerShellArgumentForwardingValidator (8 methods)
  def __str__(1 params) -> str
  def __init__(2 params) -> ?

### P:/.claude/hooks/__lib/artifact_grounder.py
  def _safe_id(1 params) -> str
  def _resolve_session_id(1 params) -> str
  def extract_command_tokens(2 params) -> ?
  def ground_blocked_command(3 params) -> dict
  def ground_git_safety_block(3 params) -> dict

### P:/.claude/hooks/__lib/artifact_ledger.py
  def _path(1 params) -> Path
  def record(4 params) -> ?
  def load(1 params) -> dict
  def find_matches(2 params) -> ?

### P:/.claude/hooks/__lib/bash_allowlist_validator.py
  def _is_safe_command(1 params) -> bool
  def _is_python_script_invocation(2 params) -> bool
  def validate_command_segments(1 params) -> ?
  def is_command_allowed(1 params) -> bool

### P:/.claude/hooks/__lib/behavioral_protocol.py
  class EvidenceTier (0 methods)
  class ConfidenceCeiling (1 methods)
  def calculate_confidence_ceiling(1 params) -> float
  def get_evidence_tier(1 params) -> ?
  def requires_high_stakes_evidence(1 params) -> bool
  def should_flag_unverified(1 params) -> bool

### P:/.claude/hooks/__lib/behavioral_state.py
  class GoalScope (0 methods)
  class GoalAnchor (4 methods)
  class UserGoal (3 methods)
  def get_session_id(0 params) -> str
  def get_terminal_id(0 params) -> str
  def load_behavioral_state(2 params) -> ?

### P:/.claude/hooks/__lib/binary_assertions.py
  class AssertionResult (1 methods)
  class AssertionFramework (6 methods)
  def check_artifacts_exist(3 params) -> ?
  def check_directory_accessible(1 params) -> ?
  def check_git_valid(1 params) -> ?
  def __str__(1 params) -> str

### P:/.claude/hooks/__lib/characterization_engine.py
  def safe_unparse(1 params) -> str
  class FunctionSignature (3 methods)
  class ClassDefinition (1 methods)
  class ImportInfo (0 methods)
  class CharacterizationData (5 methods)
  class SinglePassASTVisitor (11 methods)

### P:/.claude/hooks/__lib/circuit_breaker.py
  class CircuitBreaker (6 methods)
  def get_iteration_count(1 params) -> int
  def increment_iteration(1 params) -> ?
  def reset_iteration(1 params) -> ?
  def should_allow_continue(3 params) -> bool
  def check_and_reset_on_acceptance(2 params) -> bool

### P:/.claude/hooks/__lib/claim_classifier.py
  def classify_claim_text(1 params) -> ClaimKind
  def is_marked_as_hypothesis(1 params) -> bool
  def is_promoted_fact(1 params) -> bool
  def is_test_report_context(1 params) -> bool
  def mentions_history_or_blame(1 params) -> bool
  def summarize_response_claim_kinds(1 params) -> ?

### P:/.claude/hooks/__lib/claim_layer_map.py
  def classify_claim(1 params) -> str
  def get_required_artifacts(1 params) -> ?
  def get_block_message(1 params) -> ?

### P:/.claude/hooks/__lib/claim_patterns.py
  def _has_behavioral_assertion(1 params) -> bool
  def has_document_claim(1 params) -> bool
  def has_action_claim(1 params) -> bool
  def has_external_claim(1 params) -> bool
  def has_error_characterization(1 params) -> bool

### P:/.claude/hooks/__lib/claim_type.py
  def _safe_id(1 params) -> str
  def _read_claim_type(1 params) -> ?
  def get_claim_type(1 params) -> ?

### P:/.claude/hooks/__lib/cognitive_tag_helper.py
  def get_active_tags_for_prompt(1 params) -> ?
  def format_tags_for_instruction(1 params) -> str
  def get_cognitive_tag_instruction(1 params) -> str

### P:/.claude/hooks/__lib/commitment_tracker.py
  class TrackedCommitment (0 methods)
  class CommitmentTracker (11 methods)
  def __init__(2 params) -> ?
  def _validate_terminal_id(1 params) -> str
  def _get_state_path(2 params) -> Path
  def _get_checkpoint_path(2 params) -> Path

### P:/.claude/hooks/__lib/contract_health.py
  class HealthSummary (2 methods)
  def _load_jsonl(1 params) -> ?
  def _last_n(2 params) -> ?
  def _stale_timestamp(2 params) -> bool
  def _check_contract_lookup_failures(2 params) -> ?
  def _check_stderr_import_failures(2 params) -> ?

### P:/.claude/hooks/__lib/dx_tools_locking.py
  def _get_package_lock_path(2 params) -> Path
  def _acquire_lock(2 params) -> bool
  def _release_lock(2 params) -> ?
  def with_cache_lock(2 params) -> ?
  class CacheLockContext (3 methods)
  def decorator(1 params) -> Callable

### P:/.claude/hooks/__lib/dx_tools_observability.py
  class DXToolsMetrics (7 methods)
  class DXToolsHealth (4 methods)
  def get_metrics(0 params) -> DXToolsMetrics
  def __init__(2 params) -> ?
  def record_event(4 params) -> ?
  def start_timer(2 params) -> ?

### P:/.claude/hooks/__lib/enforcement_rate_limiter.py
  def _get_session_id(0 params) -> str
  def _get_state_path(0 params) -> Path
  def _load_state(0 params) -> ?
  def _save_state(1 params) -> ?
  def should_show_warning(2 params) -> bool
  def record_warning_shown(3 params) -> ?

### P:/.claude/hooks/__lib/enforcement_telemetry.py
  def _get_db_path(0 params) -> Path
  def _ensure_table(0 params) -> ?
  def log_enforcement_event(8 params) -> bool
  def get_advisory_compliance_rate(2 params) -> ?
  def detect_warning_fatigue(2 params) -> ?
  def reset_db_path(0 params) -> ?

### P:/.claude/hooks/__lib/epistemic_applicability.py
  def is_substantive_reasoning_turn(1 params) -> bool
  class EpistemicClassification (0 methods)
  def classify_epistemic_response(1 params) -> EpistemicClassification
  class EpistemicApplicabilityDecision (3 methods)
  def determine_epistemic_applicability(1 params) -> EpistemicApplicabilityDecision
  def is_simple_epistemic_response(1 params) -> bool

### P:/.claude/hooks/__lib/evidence_collector.py
  def _extract_paths_from_code(1 params) -> ?
  def _extract_test_names_from_command(1 params) -> ?
  def _extract_paths_from_git(1 params) -> ?
  def collect_from_turn(1 params) -> dict
  def accumulate(2 params) -> dict
  def files_overlap_with_contract(2 params) -> bool

### P:/.claude/hooks/__lib/external_judge.py
  class JudgeConfig (0 methods)
  class Verdict (0 methods)
  def get_config(0 params) -> JudgeConfig
  def load_rubric(0 params) -> str
  def _get_terminal_id(0 params) -> str
  def _get_state_path(0 params) -> Path

### P:/.claude/hooks/__lib/file_lock.py
  class FileLock (3 methods)
  def __init__(3 params) -> ?
  def __enter__(1 params) -> FileLock
  def __exit__(4 params) -> ?

### P:/.claude/hooks/__lib/git_guard_config.py
  class DangerOp (0 methods)

### P:/.claude/hooks/__lib/git_helper.py
  class GitHelper (13 methods)
  def create_git_helper(1 params) -> GitHelper
  def __init__(2 params) -> ?
  def repo(1 params) -> ?
  def is_git_repo(1 params) -> bool
  def has_uncommitted_changes(1 params) -> bool

### P:/.claude/hooks/__lib/hook_cache.py
  def measure_performance(1 params) -> ?
  def wrapper(0 params) -> Any

### P:/.claude/hooks/__lib/hook_diagnostic_wrapper.py
  def main(0 params) -> ?
  def extract_hook_type_from_cmd_args(1 params) -> ?
  def should_log_to_file_stderr(2 params) -> bool
  def log_to_hook_stderr_file(3 params) -> Path

### P:/.claude/hooks/__lib/hook_feedback_summary.py
  def format_blocking_summary(1 params) -> str
  def _get_guidance_for_hook(1 params) -> str

### P:/.claude/hooks/__lib/hook_importer.py
  class HookImporter (7 methods)
  def create_hook_importer(1 params) -> HookImporter
  def __init__(2 params) -> ?
  def _fallback_log_diag(3 params) -> ?
  def _extract_context(1 params) -> ?
  def _log_anomaly(7 params) -> ?

### P:/.claude/hooks/__lib/hook_ledger.py
  def _utcnow(0 params) -> str
  def _safe_terminal_key(1 params) -> str
  def _log_anomaly(2 params) -> ?
  def _write_turn_marker(3 params) -> bool
  def _canonical_json(1 params) -> str
  def _transcript_tail_bytes(0 params) -> int

### P:/.claude/hooks/__lib/hook_platform.py
  def run_platform_hook(4 params) -> ?
  def scope_guard_check(3 params) -> ?

### P:/.claude/hooks/__lib/hook_runner.py
  class _NoWindowPopen (1 methods)
  def _failsafe_log(1 params) -> ?
  def _error_class_and_code(4 params) -> ?
  def _log_error(4 params) -> ?
  def _output_error(1 params) -> ?
  def _safe_stderr_print(1 params) -> ?

### P:/.claude/hooks/__lib/hook_validator.py
  def validate_hook_file(1 params) -> ?
  def validate_all_hooks(1 params) -> ?

### P:/.claude/hooks/__lib/import_resolver.py
  def _read_file_safe(1 params) -> str
  def extract_import_specs(1 params) -> ?
  def collect_attribute_bases(1 params) -> ?
  def candidate_module_paths(2 params) -> ?
  def resolve_local_imports(4 params) -> ?
  def get_git_status_map(1 params) -> ?

### P:/.claude/hooks/__lib/judge_feedback.py
  def load_recent_judge_verdicts(1 params) -> ?
  def summarize_judge_activity(1 params) -> dict
  def format_session_start_judge_summary(1 params) -> ?
  def should_inject_first_query_advisory(2 params) -> bool
  def build_first_query_advisory(1 params) -> ?
  def mark_advisory_shown(1 params) -> ?

### P:/.claude/hooks/__lib/location_optimizer.py
  def infer_optimal_location(4 params) -> ?
  def _get_file_category(1 params) -> str
  def _is_hook_imported_module(1 params) -> bool
  def _categorize_hidden_directory(1 params) -> str
  def _infer_python_module_location(3 params) -> ?
  def _infer_config_location(2 params) -> ?

### P:/.claude/hooks/__lib/log_rotation.py
  def get_hooks_dir(0 params) -> Path
  def rotate_diagnostic_logs(4 params) -> ?
  def _rotate_single_log(6 params) -> ?
  def _count_jsonl_entries(1 params) -> int
  def _truncate_jsonl(2 params) -> ?
  def _should_compress(2 params) -> bool

### P:/.claude/hooks/__lib/memory_monitor.py
  def check_memory_limit(1 params) -> ?
  def get_memory_stats(1 params) -> ?

### P:/.claude/hooks/__lib/migrate_legacy_state.py
  def log_migration(4 params) -> ?
  def backup_file(1 params) -> ?
  def migrate_intent_state_file(1 params) -> dict
  def migrate_pending_command_intent_files(1 params) -> dict
  def migrate_session_data_files(1 params) -> dict
  def rollback_migration(0 params) -> dict

### P:/.claude/hooks/__lib/migrate_to_hook_base.py
  class MigrationResult (1 methods)
  def is_hook_file(1 params) -> bool
  def check_already_migrated(1 params) -> bool
  def check_has_main_function(1 params) -> bool
  def check_syntax(1 params) -> ?
  def verify_hook_runs(1 params) -> ?

### P:/.claude/hooks/__lib/path_classifier.py
  def classify_path(2 params) -> ?
  def get_cached_classification(2 params) -> ?
  def clear_cache(1 params) -> ?
  def is_test_file(2 params) -> bool
  def is_exempt_path(2 params) -> bool
  def file_exists(2 params) -> bool

### P:/.claude/hooks/__lib/path_utils.py
  def normalize_project_path(2 params) -> Path
  def get_hooks_dir(0 params) -> Path
  def get_state_dir(0 params) -> Path
  def get_benchmarks_dir(0 params) -> Path

### P:/.claude/hooks/__lib/path_validator.py
  class DirectoryPolicy (20 methods)
  class PathValidator (24 methods)
  class DirectoryValidator (5 methods)
  class CleanupPromptGenerator (2 methods)
  class DocumentationGenerator (3 methods)
  def main(0 params) -> ?

### P:/.claude/hooks/__lib/phase_machine.py
  def can_transition(2 params) -> bool
  def is_terminal(1 params) -> bool
  def should_enforce_outputs(2 params) -> bool
  def infer_phase_from_context(3 params) -> str
  def format_phase_history(1 params) -> str

### P:/.claude/hooks/__lib/pre_tool_use_logic.py
  def get_session_file(0 params) -> ?
  def load_failures(0 params) -> ?
  def compute_command_hash(1 params) -> ?
  def get_prescriptive_directive(3 params) -> str
  def check_recursive_failure(1 params) -> ?
  def check_syntax(1 params) -> ?

### P:/.claude/hooks/__lib/pretooluse_observability.py
  def truncate_text(2 params) -> str
  def safe_id(1 params) -> str
  def resolve_session_id(1 params) -> str
  def resolve_terminal_id(1 params) -> str
  def extract_tool_fields(1 params) -> ?
  def append_jsonl(2 params) -> ?

### P:/.claude/hooks/__lib/prompt_choice_state.py
  def _get_session_id(2 params) -> str
  def _get_state_file(2 params) -> Path
  def save_prompt_choice(5 params) -> ?
  def get_pending_choice(2 params) -> ?
  def clear_prompt_choice(2 params) -> ?
  def get_chosen_prompt(0 params) -> ?

### P:/.claude/hooks/__lib/prompt_session_state.py
  def _safe_id(1 params) -> str
  def resolve_session_id(1 params) -> str
  def resolve_terminal_id(1 params) -> str
  def _iter_state_dirs(0 params) -> ?
  def _state_name(2 params) -> str
  def _state_paths(2 params) -> ?

### P:/.claude/hooks/__lib/protected_paths.py
  class BrokenEntry (0 methods)
  def _normalize(1 params) -> str
  def _glob_match(2 params) -> bool
  def is_protected_path(1 params) -> bool
  def set_file_broken(2 params) -> ?
  def is_file_broken(1 params) -> bool

### P:/.claude/hooks/__lib/protection_state.py
  def _file_lock(2 params) -> ?
  class StateManager (20 methods)
  def save_characterization(2 params) -> Path
  def load_characterization(2 params) -> Any
  def has_characterization(2 params) -> bool
  def get_cached_checksum(2 params) -> ?

### P:/.claude/hooks/__lib/python_cache_manager.py
  def _clear_package_cache_impl(1 params) -> dict
  def clear_package_cache(1 params) -> dict
  def pre_install_cache_clean(1 params) -> bool
  def with_cache_lock(2 params) -> ?
  def _locked_clear(0 params) -> ?
  def decorator(1 params) -> ?

### P:/.claude/hooks/__lib/quality_log.py
  def get_quality_log_path(1 params) -> Path
  def log_quality_skill(4 params) -> bool
  def read_quality_log(3 params) -> ?
  def get_last_run(2 params) -> ?
  def get_skills_not_run_recently(2 params) -> ?

### P:/.claude/hooks/__lib/response_intent.py
  def _strip_region(3 params) -> str
  def _strip_code_blocks(1 params) -> str
  def _strip_inline_elements(1 params) -> str
  class IntentClass (0 methods)
  def _strip_quoted(1 params) -> str
  def classify_response_intent(2 params) -> str

### P:/.claude/hooks/__lib/rsn_formatter.py
  class RSNFinding (1 methods)
  class RSNSection (3 methods)
  class RSNResult (4 methods)
  class RSNFormatter (10 methods)
  def format_rsn(2 params) -> str
  def __post_init__(1 params) -> ?

### P:/.claude/hooks/__lib/runtime_claims.py
  class RuntimeClaimType (0 methods)
  class ArtifactSource (0 methods)
  class RuntimeClaimConfig (0 methods)
  class ArtifactLookupResult (0 methods)
  def classify_runtime_claim(1 params) -> ?
  def _find_log_file(2 params) -> ?

### P:/.claude/hooks/__lib/runtime_env.py
  def ledger_available(0 params) -> bool
  def get_terminal_id(1 params) -> str
  def get_active_turn_id(1 params) -> ?

### P:/.claude/hooks/__lib/semantic_matcher_llm.py
  def classify_task_relation(4 params) -> SemanticRelation
  def _get_relation_from_context(4 params) -> SemanticRelation
  def classify_trivial_same_task(1 params) -> bool
  def extract_subject_tokens(1 params) -> ?

### P:/.claude/hooks/__lib/sequential_state.py
  def _get_state_path(2 params) -> Path
  def create_state(4 params) -> dict
  def load_state(2 params) -> ?
  def update_state(3 params) -> ?
  def delete_state(2 params) -> ?
  def add_intermediate_answer(3 params) -> ?

### P:/.claude/hooks/__lib/session_constraints.py
  def _session_file(1 params) -> Path
  def _ensure_dir(0 params) -> ?
  def detect_corrections(1 params) -> ?
  def detect_revocations(1 params) -> ?
  def save_constraints(3 params) -> ?
  def load_constraints(1 params) -> ?

### P:/.claude/hooks/__lib/session_detection.py
  def get_session_id(0 params) -> str
  def detect_terminal_id(0 params) -> str
  def clear_caches(0 params) -> ?

### P:/.claude/hooks/__lib/session_manager.py
  def get_terminal_id(0 params) -> str
  def get_current_session_id(0 params) -> str
  def get_session_state_path(1 params) -> Path
  def load_session_state(1 params) -> dict
  def save_session_state(2 params) -> ?
  def set_current_session(2 params) -> ?

### P:/.claude/hooks/__lib/shared_helpers.py
  def is_meta_conversation(1 params) -> bool
  def is_self_referential(1 params) -> bool
  def is_user_intent_statement(1 params) -> bool
  def strip_non_claim_lines(1 params) -> str
  def is_question(1 params) -> bool
  def is_non_substantive_turn(1 params) -> bool

### P:/.claude/hooks/__lib/skill_guard_path.py
  def get_skill_guard_src(0 params) -> Path
  def ensure_skill_guard_in_syspath(0 params) -> ?

### P:/.claude/hooks/__lib/state_file_manager.py
  class StateFileManager (7 methods)
  def get_session_id(0 params) -> str
  def write_state_file(4 params) -> ?
  def read_state_file(3 params) -> ?
  def __init__(4 params) -> ?
  def get_state_file_path(1 params) -> Path

### P:/.claude/hooks/__lib/state_paths.py
  def _get_cached_dir(2 params) -> Path
  def clear_path_cache(0 params) -> ?
  def get_terminal_state_dir(1 params) -> Path
  def get_terminal_state_path(2 params) -> Path
  def get_session_state_dir(1 params) -> Path
  def get_session_state_path(2 params) -> Path

### P:/.claude/hooks/__lib/stop_gate_telemetry.py
  def log_gate_event(15 params) -> ?
  def clear_test_telemetry(0 params) -> ?
  def read_telemetry(0 params) -> ?
  def _is_recent(2 params) -> bool
  def get_recent_gate_summary(3 params) -> ?
  def get_runtime_claim_summary(2 params) -> ?

### P:/.claude/hooks/__lib/StopHook_consultation_loop_interrupt.py
  def _get_cks_queue_dir(0 params) -> Path
  def _get_state_file(2 params) -> Path
  def _load_state(2 params) -> dict
  def _save_state(3 params) -> ?
  def _extract_terminal_id(1 params) -> str
  def _extract_session_id(1 params) -> str

### P:/.claude/hooks/__lib/subprocess_helper.py
  def run(1 params) -> ?
  def Popen(1 params) -> ?

### P:/.claude/hooks/__lib/subprocess_patch.py
  class _NoWindowPopen (1 methods)
  def patch_subprocess(0 params) -> ?
  def unpatch_subprocess(0 params) -> ?
  def patch_subprocess_context(0 params) -> ?
  def __init__(1 params) -> ?

### P:/.claude/hooks/__lib/suggestion_utils.py
  def load_commands_registry(1 params) -> ?
  def extract_output_signals(1 params) -> ?
  def get_git_context(2 params) -> ?
  def _find_git_root(1 params) -> ?
  def _empty_git_context(0 params) -> ?
  def get_command_description(2 params) -> str

### P:/.claude/hooks/__lib/syntax_fixer.py
  def analyze_syntax_error(2 params) -> ?
  def format_suggestions(2 params) -> str

### P:/.claude/hooks/__lib/task_contract.py
  def _home(0 params) -> Path
  def _contract_path(1 params) -> Path
  def load_contract(1 params) -> ?
  def _migrate_to_v2(2 params) -> dict
  def _save_raw(2 params) -> ?
  def save_contract(1 params) -> ?

### P:/.claude/hooks/__lib/task_identity_manager.py
  class TaskMetadata (0 methods)
  class TaskIdentityManager (14 methods)
  def __init__(3 params) -> ?
  def get_current_task(1 params) -> ?
  def _from_env_var(1 params) -> ?
  def _from_session_file(1 params) -> ?

### P:/.claude/hooks/__lib/task_repository_client.py
  class TaskRepositoryClient (7 methods)
  def __init__(3 params) -> ?
  def is_available(1 params) -> bool
  def get_current_task(1 params) -> ?
  def create_checkpoint_restore_task(5 params) -> bool
  def get_checkpoint_restore_task(1 params) -> ?

### P:/.claude/hooks/__lib/task_self_doc_validator.py
  class ValidationResult (0 methods)
  def _check_category(2 params) -> bool
  def self_documentation_check(5 params) -> ValidationResult
  def is_task_self_documented(2 params) -> bool

### P:/.claude/hooks/__lib/terminal_detection.py
  def detect_console_host_terminal(0 params) -> ?
  def detect_terminal_id(0 params) -> str
  def resolve_terminal_key(1 params) -> str

### P:/.claude/hooks/__lib/terminal_id.py
  def normalize_terminal_id(2 params) -> str

### P:/.claude/hooks/__lib/token_budget.py
  class BudgetStatus (0 methods)
  class TokenBudget (10 methods)
  def __init__(3 params) -> ?
  def _init_budget_file(1 params) -> ?
  def _load_data(1 params) -> dict
  def _save_data(2 params) -> bool

### P:/.claude/hooks/__lib/trivial_turns.py
  def is_trivial_exchange(4 params) -> ?
  def log_trivial_skip(4 params) -> ?
  def log_non_trivial_classification(4 params) -> ?

### P:/.claude/hooks/__lib/ttl_utils.py
  def is_monotonic_timestamp(1 params) -> bool
  def write_monotonic_ts(0 params) -> float
  def write_wallclock_ts(0 params) -> float
  def get_elapsed(1 params) -> float
  def is_expired(2 params) -> bool
  def sanitize_future_ts(2 params) -> float

### P:/.claude/hooks/__lib/turn_mode.py
  def get_session_mode(1 params) -> SessionMode
  def _turn_kind_from_context(2 params) -> TurnMode
  def classify(1 params) -> TurnMode
  def _classify_from_prompt(2 params) -> TurnMode
  def _refine_report_mode(1 params) -> TurnMode
  def _classify_question_response(2 params) -> TurnMode

### P:/.claude/hooks/__lib/type_validator.py
  class TypeValidationError (3 methods)
  def get_file_category(1 params) -> str
  def _is_package_setup_file(1 params) -> bool
  def validate_config_whitelist_entries(2 params) -> ?
  def validate_python_whitelist_entries(2 params) -> ?
  def validate_all_policy_types(1 params) -> ?

### P:/.claude/hooks/__lib/unified_evidence_enforcer.py
  def check_response(1 params) -> ?
  def _normalize_tool_names(1 params) -> ?
  def _has_observation_tool(1 params) -> bool
  def _has_required_evidence_fields(1 params) -> bool
  def _has_claims_without_observation(2 params) -> bool
  def _is_diagnostic_without_evidence(2 params) -> bool

### P:/.claude/hooks/__lib/validation_cache.py
  def get_terminal_id(0 params) -> str
  def get_cwd_hash(0 params) -> str
  def get_config_hash(1 params) -> str
  def build_cache_key(5 params) -> str
  def get_cache_path(1 params) -> Path
  def is_cache_valid(1 params) -> bool

### P:/.claude/hooks/__lib/verification_visualizer.py
  class VerificationVisualizer (7 methods)
  def format_verification_warning(2 params) -> str
  def format_verification_success(2 params) -> str
  def format_advisory(5 params) -> str
  def format_verified(4 params) -> str
  def format_blocked(4 params) -> str

### P:/.claude/hooks/__lib/worktree_helper.py
  def get_current_worktree(1 params) -> Path
  def _get_worktree_from_git_list(1 params) -> Path
  def list_all_worktrees(1 params) -> ?
  def is_cross_worktree_access(3 params) -> bool
  def validate_git_command_for_worktree(2 params) -> ?

### P:/.claude/hooks/__lib/write_tool_error_signal.py
  def _tail_lines(2 params) -> str
  def _resolve_session_id(1 params) -> str
  def _resolve_terminal_id(0 params) -> str
  def _safe_filename_part(1 params) -> str
  def _expire_on_write(1 params) -> ?
  def write_tool_error_signal(6 params) -> ?

### P:/.claude/hooks/__lib__/correction_detector.py
  class CorrectionCheckResult (0 methods)
  def has_correction(1 params) -> bool
  def has_acknowledgment(1 params) -> bool
  def _find_correction_position(1 params) -> ?
  def check_correction_acknowledge(3 params) -> CorrectionCheckResult

### P:/.claude/hooks/__lib__/drift_sentinel.py
  def extract_paragraphs(1 params) -> ?
  def compute_drift(2 params) -> dict
  def _load_sklearn_objects(0 params) -> ?
  def detect_drift(2 params) -> dict

### P:/.claude/hooks/_archive_v1/PreToolUse_command_intent_gate.py
  def _get_session_id(0 params) -> str
  def _get_intent_state_file(0 params) -> Path
  def get_pending_intent(0 params) -> ?
  def clear_intent_state(0 params) -> ?
  def log_decision(5 params) -> ?
  def is_skill_execution(2 params) -> bool

### P:/.claude/hooks/_archived/StopHook_cite_evidence.py
  def extract_citations(1 params) -> ?
  def has_weak_markers(1 params) -> bool
  def has_hedges(1 params) -> bool
  def has_meta_statements(1 params) -> bool
  def detect_claim(1 params) -> ?
  def check_citation(2 params) -> ?

### P:/.claude/hooks/_cks_cache.py
  class CKSCache (7 methods)
  def get_cache(0 params) -> CKSCache
  def maybe_clear_cache(0 params) -> ?
  def __init__(2 params) -> ?
  def _load_cache(1 params) -> ?
  def _save_cache(1 params) -> ?

### P:/.claude/hooks/_legacy/epistemic_bindings.py
  def extract_commitments(1 params) -> ?
  def detect_time_scopes(1 params) -> ?
  def normalize_artifact_path(1 params) -> str
  def extract_root_cause_details(1 params) -> ?
  def is_section_empty(1 params) -> bool
  def extract_verification_items(1 params) -> ?

### P:/.claude/hooks/_legacy/StopHook_epistemic_contract.py
  class ValidationIssue (0 methods)
  class ValidationResult (1 methods)
  def validate_epistemic_answer(1 params) -> ValidationResult
  def _split_into_sections(2 params) -> tuple
  def _check_section_order(1 params) -> ?
  def _check_bullet_format(2 params) -> ?

### P:/.claude/hooks/adversarial_aggregator.py
  def discover_subagent_files(1 params) -> ?
  def aggregate_findings(1 params) -> ?
  def group_by_location(1 params) -> ?
  def calculate_consensus(1 params) -> dict
  def identify_blocking_issues(2 params) -> ?
  def format_summary(3 params) -> str

### P:/.claude/hooks/analysis/compatibility_matrix_implementation.py
  class CompatibilityMatrixEntry (0 methods)
  class CompatibilityMatrixMetadata (0 methods)
  def load_matrix_from_disk(0 params) -> ?
  def save_matrix_to_disk(2 params) -> bool
  def track_combination_usage(3 params) -> bool
  def validate_matrix_entry(4 params) -> ?

### P:/.claude/hooks/analyze_assumption_audit.py
  def get_current_terminal_id(0 params) -> str
  def matches_terminal(2 params) -> bool
  def analyze_logs(3 params) -> ?
  def extract_raw(1 params) -> str

### P:/.claude/hooks/analyze_audit_compliance.py
  def analyze(1 params) -> ?

### P:/.claude/hooks/analyze_audit_effectiveness.py
  def load_jsonl(1 params) -> list
  def get_all_decision_logs(0 params) -> list
  def main(0 params) -> int

### P:/.claude/hooks/analyze_blocked_claims.py
  def parse_log_entry(1 params) -> ?
  def load_entries(1 params) -> ?
  def show_statistics(1 params) -> ?
  def show_patterns(1 params) -> ?
  def show_weekly_trends(1 params) -> ?
  def export_format(2 params) -> str

### P:/.claude/hooks/analyze_blocks.py
  def get_tracking_files(0 params) -> ?
  def is_test_command(1 params) -> bool
  def get_last_review(0 params) -> ?
  def update_review_marker(0 params) -> ?
  def show_review_reminder(1 params) -> ?
  def analyze_blocks(0 params) -> ?

### P:/.claude/hooks/analyze_compatibility_matrix.py
  def get_current_terminal_id(0 params) -> str
  def analyze_compatibility_usage(3 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/analyze_debug_payloads.py
  def analyze_jsonl(1 params) -> dict
  def main(0 params) -> ?

### P:/.claude/hooks/analyze_decision_patterns.py
  def load_logs(2 params) -> ?
  def analyze_distribution(1 params) -> ?
  def analyze_option_rates(1 params) -> ?
  def analyze_response_lengths(1 params) -> ?
  def compare_to_expectations(2 params) -> ?
  def print_report(1 params) -> ?

### P:/.claude/hooks/analyze_enforcement_replay.py
  def _parse_ts(1 params) -> ?
  def _event_log_candidates(0 params) -> ?
  def _load_events(1 params) -> ?
  def _current_terminal_id(0 params) -> ?
  def _filter_terminal(2 params) -> ?
  def _pct(2 params) -> float

### P:/.claude/hooks/analyze_error_attribution.py
  def analyze(1 params) -> ?

### P:/.claude/hooks/analyze_hooks.py
  def get_log_files(1 params) -> ?
  def load_jsonl(3 params) -> ?
  def analyze_system(5 params) -> dict
  def print_summary(2 params) -> ?
  def print_detailed(4 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/analyze_missing_response.py
  def analyze_today(0 params) -> ?
  def analyze_recent_days(1 params) -> ?

### P:/.claude/hooks/analyze_reasoning_profiles.py
  def _parse_iso(1 params) -> ?
  def analyze(1 params) -> int
  def main(0 params) -> int

### P:/.claude/hooks/analyze_speculation.py
  def get_constructional_blocks_files(0 params) -> ?
  def analyze_sqlite(2 params) -> ?
  def analyze_jsonl(2 params) -> ?
  def calculate_compliance_rate(1 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/anti_lazy_diff_nudge.py
  def main(0 params) -> ?
  def _is_arch_file(1 params) -> bool
  def _generate_nudge(1 params) -> str

### P:/.claude/hooks/anti_sycophancy/advocate_injection.py
  def main(0 params) -> ?

### P:/.claude/hooks/anti_sycophancy/affirmation_detector.py
  class PraiseMatch (0 methods)
  def _normalize(1 params) -> str
  def _extract_opener(2 params) -> ?
  def _check_praise_starter(1 params) -> ?
  def _check_flattery_phrase(1 params) -> ?
  def _check_you_affirmation(1 params) -> ?

### P:/.claude/hooks/anti_sycophancy/destructive_cleanup_detector.py
  class CleanupMatch (0 methods)
  def detect_destructive_cleanup(1 params) -> ?
  def detect_all_destructive_cleanup(1 params) -> ?

### P:/.claude/hooks/anti_sycophancy/hypothesis_as_fact_detector.py
  class ClaimType (0 methods)
  class RiskDomain (0 methods)
  class RawClaim (0 methods)
  class HypothesisAsFactDetector (14 methods)
  def __init__(1 params) -> ?
  def _compile_patterns(1 params) -> ?

### P:/.claude/hooks/anti_sycophancy/lazy_closure_detector.py
  def _get_terminal_id(0 params) -> str
  def _capitulation_state_path(0 params) -> Path
  def _load_capitulation_state(0 params) -> dict
  def _save_capitulation_state(1 params) -> ?
  def _check_capitulation_escalation(0 params) -> bool
  def reset_capitulation_counter(0 params) -> ?

### P:/.claude/hooks/anti_sycophancy/overconfidence_detector.py
  def _infer_structural_subject(1 params) -> ?
  def _has_comparison_evidence(2 params) -> bool
  class OverconfidenceMatch (0 methods)
  def _has_evidence_marker(1 params) -> bool
  def _is_explanatory_prose(2 params) -> bool
  def _find_pattern(2 params) -> ?

### P:/.claude/hooks/anti_sycophancy/response_structure_detector.py
  class StructureMatch (0 methods)
  def _matches_any(2 params) -> ?
  def _find_correction_marker(1 params) -> ?
  def _is_exempt_unchanged(1 params) -> bool
  def _find_unchanged_marker(1 params) -> ?
  def _extract_correction_sections(1 params) -> ?

### P:/.claude/hooks/anti_sycophancy/toggle.py
  def get_status(0 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/anti_sycophancy/unverified_stance_detector.py
  class StanceMatch (0 methods)
  def _normalize(1 params) -> str
  def _extract_tools_used(1 params) -> ?
  def _extract_user_message(1 params) -> str
  def _has_factual_claim(1 params) -> bool
  def _strip_quoted_and_hook_blocks(1 params) -> str

### P:/.claude/hooks/artifact_claims.py
  class ArtifactClaim (0 methods)
  def _split_sentences(1 params) -> ?
  def _is_meta_or_self_ref(1 params) -> bool
  def extract_artifact_claims(1 params) -> ?
  def _find_artifact_in_text(1 params) -> ?
  def find_concrete_observation(2 params) -> ?

### P:/.claude/hooks/assumption_audit_v2.py
  def debug_log(1 params) -> ?
  def resolve_session_id(1 params) -> str
  def load_tool_events(3 params) -> ?
  def get_bash_command_name(1 params) -> str
  def is_trivial_bash_command(1 params) -> bool
  def is_weak_evidence_command(1 params) -> bool

### P:/.claude/hooks/auto_commit_hook.py
  def get_session_id_for_commit(0 params) -> str
  def run_git_command(2 params) -> ?
  def has_uncommitted_changes(1 params) -> bool
  def is_git_repo(1 params) -> bool
  def is_worktree(1 params) -> bool
  def add_duf_notification(0 params) -> ?

### P:/.claude/hooks/autonomy_gate.py
  def _similar(2 params) -> float
  def is_autonomy_signal(1 params) -> bool
  def response_defers_decision(1 params) -> bool
  def evaluate(1 params) -> ?
  def run(1 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/backup_manager.py
  class BackupManager (5 methods)
  def __init__(3 params) -> ?
  def _backup_path(2 params) -> Path
  def rotate_backups(1 params) -> ?
  def find_latest_backup(1 params) -> ?
  def restore_from_backup(2 params) -> ?

### P:/.claude/hooks/baselines/measure_baseline.py
  class TimingResult (0 methods)
  class BaselineMetrics (0 methods)
  def time_hook(3 params) -> TimingResult
  def calculate_metrics(1 params) -> BaselineMetrics
  def measure_cognitive_enhancers(0 params) -> ?
  def measure_reasoning_mode_selector(0 params) -> ?

### P:/.claude/hooks/baselines/measure_cross_category_baseline.py
  def measure_m1_cross_category_usage(0 params) -> ?
  def measure_m2_performance_overhead(0 params) -> ?
  def measure_m3_matrix_entry_count(0 params) -> ?
  def measure_s1_cks_query_rate(0 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/baselines/TASK_020_performance_verification.py
  class PerformanceMetrics (0 methods)
  class BaselineComparison (0 methods)
  class RegressionCheck (0 methods)
  class TestSuiteResults (0 methods)
  class FinalPerformanceReport (0 methods)
  def measure_detection_performance(0 params) -> PerformanceMetrics

### P:/.claude/hooks/benchmarks/measure_hook_latency.py
  def measure_subprocess_latency(3 params) -> ?
  def measure_in_process_latency(2 params) -> ?
  def benchmark_hook(2 params) -> dict
  def main(0 params) -> ?

### P:/.claude/hooks/block_protocol.py
  def block_response(3 params) -> ?
  def allow_response(1 params) -> ?
  def conditional_block(4 params) -> ?
  def make_block_result(2 params) -> dict
  def make_allow_result(1 params) -> dict
  def is_block_result(1 params) -> bool

### P:/.claude/hooks/cc_diagnostic_logger.py
  def _get_connection(0 params) -> ?
  def _init_schema(0 params) -> ?
  def _meta_get(1 params) -> ?
  def _meta_set(2 params) -> ?
  def _maybe_cleanup_importer_diagnostics(0 params) -> ?
  def _get_buffered_logger(1 params) -> ?

### P:/.claude/hooks/cc_health.py
  def _get_session_mode(0 params) -> str
  def main(0 params) -> ?

### P:/.claude/hooks/change_analyzer.py
  def is_in_merge(1 params) -> bool
  def get_cached_changes(1 params) -> ?
  def changelog_already_changed(1 params) -> bool
  def detect_performance_change(2 params) -> ?
  def analyze_changes(1 params) -> dict
  def update_changelog(3 params) -> bool

### P:/.claude/hooks/cjk_drift_detector.py
  def _strip_quoted(1 params) -> str
  def detect_cjk(1 params) -> ?
  def _last_assistant_text(1 params) -> str
  def _posttooluse_text(1 params) -> str
  def main(0 params) -> int

### P:/.claude/hooks/clean_dependency_verification_state.py
  def main(0 params) -> ?

### P:/.claude/hooks/cleanup_verification_state.py
  def is_corrupted_package_name(1 params) -> bool
  def cleanup_state_file(1 params) -> dict
  def cleanup_old_state_files(1 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/command_execution_validator.py
  def _get_terminal_id(0 params) -> str
  def _get_scoped_state_file(0 params) -> Path
  def _get_fallback_scoped_state_file(0 params) -> Path
  def _get_state_candidates(0 params) -> ?
  def load_command_state(0 params) -> ?
  def clear_command_state(0 params) -> ?

### P:/.claude/hooks/commit_message_parser.py
  class FileInfo (0 methods)
  class DiffData (0 methods)
  def parse_git_diff(1 params) -> ?
  def detect_file_type(1 params) -> str
  def detect_scope(1 params) -> ?
  def detect_commit_type(1 params) -> str

### P:/.claude/hooks/competence/task_type_registry.py
  def load_registry(0 params) -> ?
  def get_task_type_for_skill(2 params) -> ?
  def get_output_contract(1 params) -> ?
  def get_required_fields(1 params) -> ?
  def get_optional_fields(1 params) -> ?
  def get_enforcement_mode(1 params) -> str

### P:/.claude/hooks/comprehensive_hook_health_check.py
  def test_hook(2 params) -> dict
  def test_stale_lock_files(0 params) -> dict
  def test_think_trigger_profile_consistency(0 params) -> dict
  def main(0 params) -> ?

### P:/.claude/hooks/config/daemon_config.py
  def get_daemon_config(1 params) -> ?

### P:/.claude/hooks/constitution_cache.py
  class ConstitutionalRule (0 methods)
  def _determine_category(1 params) -> str
  def _parse_rules(2 params) -> ?
  def load_constitution(1 params) -> dict
  def get_mandatory(2 params) -> ?
  def get_forbidden(2 params) -> ?

### P:/.claude/hooks/constitutional_enforcer.py
  class Severity (0 methods)
  class RuleCategory (0 methods)
  class Violation (0 methods)
  class ForbiddenValidator (4 methods)
  class TruthValidator (7 methods)
  class SuccessValidator (2 methods)

### P:/.claude/hooks/csf_nip_path_validator.py
  class CSFNIPPathValidator (6 methods)
  def main(0 params) -> ?
  def __init__(2 params) -> ?
  def _build_csf_validation_rules(1 params) -> ?
  def validate_csf_nip_operation(2 params) -> ?
  def get_all_allowed_directories(1 params) -> ?

### P:/.claude/hooks/csftracker.py
  def increment(2 params) -> ?
  def get(2 params) -> int
  def get_all(0 params) -> ?
  def reset(1 params) -> ?
  def save_metrics(0 params) -> bool
  def load_metrics(0 params) -> bool

### P:/.claude/hooks/damage-control/bash-tool-damage-control.py
  def normalize_path_for_matching(1 params) -> str
  def escape_for_regex(1 params) -> str
  def is_glob_pattern(1 params) -> bool
  def glob_to_regex(1 params) -> str
  def has_shell_separators(1 params) -> bool
  def matches_allowlist(2 params) -> bool

### P:/.claude/hooks/damage-control/edit-tool-damage-control.py
  def is_glob_pattern(1 params) -> bool
  def normalize_case_slash(1 params) -> str
  def normalize_path(1 params) -> str
  def normalize_glob(1 params) -> str
  def match_path(2 params) -> bool
  def get_config_path(0 params) -> Path

### P:/.claude/hooks/damage-control/merge-patterns.py
  def load_yaml(1 params) -> ?
  def item_key(1 params) -> str
  def merge_list(2 params) -> ?
  def merge_patterns(2 params) -> ?
  def check_out_of_date(2 params) -> bool
  def main(0 params) -> int

### P:/.claude/hooks/damage-control/write-tool-damage-control.py
  def is_glob_pattern(1 params) -> bool
  def normalize_case_slash(1 params) -> str
  def normalize_path(1 params) -> str
  def normalize_glob(1 params) -> str
  def match_path(2 params) -> bool
  def get_config_path(0 params) -> Path

### P:/.claude/hooks/dependency_chain_guard.py
  def _flatten_transcript(1 params) -> str
  def _build_context_text(1 params) -> str
  def _normalize_token(1 params) -> str
  def _extract_entities(1 params) -> ?
  def _extract_dependency_pairs(1 params) -> ?
  def _mentions_any(2 params) -> bool

### P:/.claude/hooks/disler_utils/constants.py
  def get_session_log_dir(1 params) -> Path
  def ensure_session_log_dir(1 params) -> Path

### P:/.claude/hooks/disler_utils/hitl.py
  class HITLRequest (5 methods)
  def ask_question(3 params) -> ?
  def ask_permission(3 params) -> bool
  def ask_choice(4 params) -> ?
  def __init__(6 params) -> ?
  def _find_free_port(1 params) -> int

### P:/.claude/hooks/disler_utils/llm/anth.py
  def prompt_llm(1 params) -> ?
  def generate_completion_message(0 params) -> ?
  def generate_agent_name(0 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/disler_utils/llm/oai.py
  def prompt_llm(1 params) -> ?
  def generate_completion_message(0 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/disler_utils/model_extractor.py
  def get_model_from_transcript(3 params) -> str
  def extract_model_from_transcript(1 params) -> str

### P:/.claude/hooks/disler_utils/summarizer.py
  def generate_event_summary(1 params) -> ?

### P:/.claude/hooks/disler_utils/tts/elevenlabs_tts.py
  def main(0 params) -> ?

### P:/.claude/hooks/disler_utils/tts/openai_tts.py
  def main(0 params) -> ?

### P:/.claude/hooks/disler_utils/tts/pyttsx3_tts.py
  def main(0 params) -> ?

### P:/.claude/hooks/dreaming_aggregator.py
  class InsightsGenerator (5 methods)
  def __init__(2 params) -> ?
  def add_event(2 params) -> ?
  def _prune_old_events(1 params) -> ?
  def _get_window_timedelta(1 params) -> Any
  def generate_insights(1 params) -> ?

### P:/.claude/hooks/dreaming_config.py
  def load_config(1 params) -> dict

### P:/.claude/hooks/dreaming_daemon.py
  def _check_for_zombie_daemon(1 params) -> bool
  def _setup_signal_handlers(0 params) -> ?
  def _cleanup_on_exit(0 params) -> ?
  def _load_config_async(0 params) -> dict
  def _update_heartbeat_and_state_async(3 params) -> ?
  def _read_events_async(1 params) -> ?

### P:/.claude/hooks/dreaming_insights.py
  class PrincipleStats (0 methods)
  class Pattern (0 methods)
  class DreamingInsights (1 methods)
  def to_markdown(1 params) -> str

### P:/.claude/hooks/dreaming_mutex.py
  def acquire_singleton(4 params) -> ?
  def release_singleton(1 params) -> ?
  def is_instance_running(1 params) -> bool
  def _create_windows_mutex(1 params) -> ?
  def _atomic_write_pid(2 params) -> ?
  def _is_process_running(1 params) -> bool

### P:/.claude/hooks/dreaming_state.py
  class DreamingState (0 methods)
  def _validate_state(1 params) -> bool
  def _preserve_corrupted_file(1 params) -> ?
  def load_state(1 params) -> DreamingState
  def _load_state_file(1 params) -> ?
  def save_state(2 params) -> ?

### P:/.claude/hooks/dreaming_tailer.py
  class JSONLTailer (9 methods)
  def __init__(5 params) -> ?
  def _load_state(1 params) -> ?
  def _save_state(1 params) -> ?
  def _detect_rotation(1 params) -> bool
  def read_new_events(1 params) -> ?

### P:/.claude/hooks/dreaming_writer.py
  def write_insights(2 params) -> ?
  def _write_json_atomic(2 params) -> ?
  def _write_markdown_atomic(2 params) -> ?

### P:/.claude/hooks/empirical_claims_gate.py
  def _has_doc_status_proxy(1 params) -> bool
  def _has_impl_claim(1 params) -> bool
  def _has_code_evidence(1 params) -> bool
  def _has_verification_language(1 params) -> bool
  def _has_verif_near_claim(1 params) -> bool
  def check_empirical_claims(1 params) -> ?

### P:/.claude/hooks/enhanced_path_validator.py
  class EnhancedPathValidator (5 methods)
  def validate_file_with_context(3 params) -> ?
  def validate_operation_with_context(3 params) -> ?
  def show_context_status_simple(0 params) -> ?
  class ToolOperationValidator (3 methods)
  def __init__(3 params) -> ?

### P:/.claude/hooks/entity_extraction/extractor.py
  class ExtractedEntity (2 methods)
  class ExtractionResult (2 methods)
  class EntityExtractor (6 methods)
  def extract_entities(2 params) -> ?
  def __hash__(1 params) -> ?
  def __eq__(2 params) -> ?

### P:/.claude/hooks/entity_extraction/migrate.py
  def _get_extractor(0 params) -> ?
  def extract_entities_from_text(1 params) -> ?
  def extract_entities_from_claims(2 params) -> ?
  def extract_entities_from_evidence(1 params) -> ?
  def check_entity_overlap(3 params) -> ?

### P:/.claude/hooks/entity_extraction/patch.py
  def apply_patch(0 params) -> ?
  def is_patched(0 params) -> bool

### P:/.claude/hooks/entity_extraction/strategies.py
  class ExtractionStrategy (2 methods)
  class StructuralStrategy (3 methods)
  class HeuristicStrategy (4 methods)
  class SemanticStrategy (6 methods)
  def extract(2 params) -> ?
  def _passes_length_check(2 params) -> bool

### P:/.claude/hooks/epistemic_validator.py
  class ClaimKind (0 methods)
  class TurnKind (0 methods)
  def _classify_claim_kind(1 params) -> ClaimKind
  def _turn_kind_from_context(2 params) -> TurnKind
  def _turn_kind_from_response_type(2 params) -> TurnKind
  def get_epistemic_policy(2 params) -> ?

### P:/.claude/hooks/evidence/__init__.py
  class EvidenceValidity (0 methods)
  class EvidenceValidator (6 methods)
  def __init__(2 params) -> ?
  def _compute_file_hash_uncached(2 params) -> str
  def _file_hash(2 params) -> str
  def validate_claim_evidence(5 params) -> EvidenceValidity

### P:/.claude/hooks/evidence/migrate.py
  def load_old_cache(1 params) -> ?
  def migrate_hash_cache(3 params) -> ?
  def backup_old_state(1 params) -> ?
  def main(0 params) -> ?
  def log_hook_event(1 params) -> ?

### P:/.claude/hooks/evidence_scope.py
  def _dedupe_events(1 params) -> ?
  def _extract_artifact_path(1 params) -> ?
  def _is_event_fresh_for_mutable_artifact(1 params) -> bool
  def load_scoped_tool_events(0 params) -> ?

### P:/.claude/hooks/evidence_store.py
  def _ensure_dir(0 params) -> ?
  def normalize_session_id(1 params) -> str
  def _connect(0 params) -> ?
  def init_db(0 params) -> ?
  def _load_current_max_event_id(3 params) -> int
  def start_turn(4 params) -> str

### P:/.claude/hooks/file_lock_manager.py
  def _cleanup_temp_files(0 params) -> ?
  def _get_session_id(0 params) -> str
  def _get_session_lock_dir(0 params) -> Path
  def _get_lock_path(1 params) -> Path
  def _read_lock_safe(1 params) -> ?
  def acquire_lock(1 params) -> ?

### P:/.claude/hooks/frameguard_stop.py
  def evaluate_frameguard(1 params) -> ?
  def main(0 params) -> ?
  def frameguard_blocked_inc(0 params) -> ?
  def frameguard_unhandled_inc(0 params) -> ?

### P:/.claude/hooks/gto_failure_capture.py
  def main(0 params) -> int

### P:/.claude/hooks/hook_audit_dashboard.py
  def get_current_terminal_id(0 params) -> str
  def run_script(2 params) -> bool
  def dashboard(3 params) -> ?
  def blocks(3 params) -> ?
  def stats(6 params) -> ?
  def ups_stats(3 params) -> ?

### P:/.claude/hooks/hook_diagnostics.py
  def check_hook_stderr_violations(0 params) -> bool
  def main(0 params) -> ?

### P:/.claude/hooks/hook_observability_rollup.py
  def iso_now(0 params) -> str
  def ts_to_iso(2 params) -> str
  def ensure_db(1 params) -> ?
  def insert_row(2 params) -> ?
  def reason_from_error_text(1 params) -> str
  def decision_from_event_kind(2 params) -> str

### P:/.claude/hooks/hook_state_manager.py
  def _home(0 params) -> Path
  def get_state_dir(1 params) -> Path
  def _safe_id(1 params) -> str
  def _is_stale(2 params) -> bool
  def read_state(2 params) -> ?
  def write_state(3 params) -> ?

### P:/.claude/hooks/hook_tracker.py
  def _get_session_start(0 params) -> datetime
  def is_hook_self_operation(1 params) -> bool
  def is_bypass_enabled(0 params) -> bool
  def is_scoped_bypass(1 params) -> bool
  def is_test_pattern(1 params) -> bool
  def log_block(5 params) -> ?

### P:/.claude/hooks/intent_artifact_alignment.py
  class TargetSpec (0 methods)
  def extract_targets_from_prompt(1 params) -> ?
  def _extract_file_path(1 params) -> str
  def _extract_path_from_command(1 params) -> ?
  def extract_modified_paths(1 params) -> ?
  def extract_executed_commands(1 params) -> ?

### P:/.claude/hooks/investigation-ledger/guidance_generator.py
  def generate_guidance(1 params) -> ?
  def format_guidance_for_display(1 params) -> str

### P:/.claude/hooks/investigation-ledger/ledger.py
  def _sanitize_terminal_key(1 params) -> str
  def _resolve_terminal_id(0 params) -> str
  def _get_terminal_id(0 params) -> str
  def file_lock(2 params) -> Any
  def _get_empty_ledger(0 params) -> LedgerDict
  def _load_ledger(0 params) -> LedgerDict

### P:/.claude/hooks/investigation-ledger/PostToolUse_investigation_tracker.py
  def extract_tool_data(1 params) -> tuple
  def handle_file_read(2 params) -> bool
  def handle_search(2 params) -> bool
  def handle_execution(2 params) -> bool
  def main(0 params) -> ?

### P:/.claude/hooks/investigation-ledger/react_looper.py
  class ReActLooper (6 methods)
  def __init__(3 params) -> ?
  def _load_state(1 params) -> dict
  def _save_state(1 params) -> ?
  def _clear_state(1 params) -> ?
  def run(1 params) -> ?

### P:/.claude/hooks/investigation-ledger/Stop_investigation_validator.py
  def main(0 params) -> ?

### P:/.claude/hooks/investigation-ledger/validate_claims.py
  def _contains_claims(1 params) -> ?
  def _has_valid_evidence(2 params) -> ?
  def _extract_referenced_topics(1 params) -> ?
  def _normalize_topics_for_comparison(1 params) -> ?
  def validate_claims(1 params) -> Dict

### P:/.claude/hooks/investigation-ledger/validate_confidence.py
  def _extract_explicit_confidence(1 params) -> ?
  def _extract_verbal_confidence(1 params) -> ?
  def _detect_unhedged_assertions(1 params) -> bool
  def _get_max_confidence_in_text(1 params) -> ?
  def validate_confidence(1 params) -> Dict

### P:/.claude/hooks/log_hook.py
  def _is_windows_reserved_path(1 params) -> bool
  class LockRetryExhausted (1 methods)
  def _retry_on_locked(1 params) -> ?
  def get_lock(1 params) -> ?
  def release_lock(1 params) -> ?
  def _append_log(2 params) -> ?

### P:/.claude/hooks/meta_explanation_detector.py
  def is_meta_explanation(1 params) -> bool

### P:/.claude/hooks/monitor.py
  def load_telemetry(1 params) -> ?
  def load_approval_states(0 params) -> ?
  def analyze_gate(2 params) -> dict
  def print_summary(3 params) -> ?
  def export_csv(3 params) -> ?
  def export_png(3 params) -> ?

### P:/.claude/hooks/narrative_intent_detector.py
  def load_tool_events(2 params) -> ?
  def detect_intent_narratives(1 params) -> ?
  def _sentence_has_hedge(1 params) -> bool
  def _sentence_has_citation(1 params) -> bool
  def _citation_backed_by_evidence(2 params) -> bool
  def _build_evidence_entities(1 params) -> ?

### P:/.claude/hooks/notification_queue.py
  class Notification (0 methods)
  def _get_cleared_time(1 params) -> ?
  def _set_cleared_time(2 params) -> ?
  def mark_cleared(1 params) -> ?
  def add_notification(5 params) -> ?
  def get_notifications(1 params) -> ?

### P:/.claude/hooks/Notification_voice_hook.py
  def _extract_message(1 params) -> str
  def _pythonw_executable(0 params) -> str
  def main(0 params) -> int

### P:/.claude/hooks/optimizations/revert_optimizations.py
  def revert_tdd_eval(0 params) -> ?
  def revert_cks_timeout(0 params) -> ?
  def revert_hook_timeouts(0 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/path_suggester.py
  class PathSuggester (7 methods)
  def __init__(1 params) -> ?
  def suggest_appropriate_location(5 params) -> ?
  def get_directory_mapping(1 params) -> ?
  def _fallback_suggestion(3 params) -> ?
  def _print_routing_suggestion(3 params) -> ?

### P:/.claude/hooks/path_utils.py
  def normalize_path(1 params) -> str
  def normalize_path_preserve_case(1 params) -> str
  def to_windows_path(1 params) -> str
  def is_workspace_path(1 params) -> bool
  def is_csf_nip_path(1 params) -> bool
  def is_claude_path(1 params) -> bool

### P:/.claude/hooks/performance_tracker.py
  def track_hook_performance(3 params) -> Callable
  def get_default_timeout(1 params) -> int
  def set_default_timeout(2 params) -> ?
  def decorator(1 params) -> Callable
  def wrapper(0 params) -> Any

### P:/.claude/hooks/post/PostToolWrite_doc_validator.py
  def validate_post_tool_write(3 params) -> dict
  def main(0 params) -> ?

### P:/.claude/hooks/posttooluse/__init__.py
  def create_registry(0 params) -> HookRegistry

### P:/.claude/hooks/posttooluse/agent_contract_validator.py
  def _parse_frontmatter(1 params) -> ?
  def _get_agent_name(1 params) -> ?
  def validate_agent_contract(2 params) -> dict
  class AgentContractValidator (1 methods)
  def main(0 params) -> ?
  def process(4 params) -> dict

### P:/.claude/hooks/posttooluse/artifact_scraper.py
  class ArtifactScraperHook (1 methods)
  def process(4 params) -> ?

### P:/.claude/hooks/posttooluse/base.py
  def is_block_result(1 params) -> bool
  class PostToolUseHook (7 methods)
  class HookRegistry (4 methods)
  def __init__(1 params) -> ?
  def _normalize_tool_input(1 params) -> ?
  def _normalize_tool_response(1 params) -> ?

### P:/.claude/hooks/posttooluse/breadcrumb_tracker_hook.py
  class BreadcrumbTrackerHook (3 methods)
  def __init__(1 params) -> ?
  def tool_matcher(1 params) -> ?
  def process(4 params) -> ?

### P:/.claude/hooks/posttooluse/change_propagation_hook.py
  def _load_state(0 params) -> dict
  def _save_state(1 params) -> ?
  class ChangePropagationHook (4 methods)
  def process(4 params) -> ?
  def _detect_change(4 params) -> ?
  def _record_verification(4 params) -> ?

### P:/.claude/hooks/posttooluse/change_verification.py
  class ChangeVerification (5 methods)
  def __init__(1 params) -> ?
  def process(4 params) -> ?
  def _extract_file_path(3 params) -> ?
  def _save_pending_verification(2 params) -> ?
  def _load_pending_verifications(1 params) -> ?

### P:/.claude/hooks/posttooluse/characterization_capture_hook.py
  class CharacterizationCaptureHook (3 methods)
  def __init__(1 params) -> ?
  def process(4 params) -> ?
  def _is_hook_file(2 params) -> bool

### P:/.claude/hooks/posttooluse/cleanup_tracker_hook.py
  class CleanupTrackerHook (2 methods)
  def process(4 params) -> ?
  def _cleanup_stale_files(3 params) -> ?

### P:/.claude/hooks/posttooluse/completion_validator.py
  class CompletionValidator (6 methods)
  def __init__(1 params) -> ?
  def process(4 params) -> ?
  def _extract_file_path(3 params) -> ?
  def _extract_module_name(2 params) -> ?
  def _verify_module_registered(2 params) -> bool

### P:/.claude/hooks/posttooluse/e2e_tracker_hook.py
  class E2ETrackerHook (2 methods)
  def process(4 params) -> ?
  def _detect_workflow_type(3 params) -> str

### P:/.claude/hooks/posttooluse/edit_verifier.py
  def get_excerpt(4 params) -> str
  def record_observation(2 params) -> bool
  def is_failed_operation(1 params) -> bool
  def validate_path(1 params) -> ?
  def verify_write(2 params) -> ?
  def verify_edit(3 params) -> ?

### P:/.claude/hooks/posttooluse/effects/base_effect.py
  class EffectVerificationResult (2 methods)
  class BaseEffectVerifier (7 methods)
  def is_valid(1 params) -> bool
  def to_dict(1 params) -> dict
  def __init__(2 params) -> ?
  def name(1 params) -> str

### P:/.claude/hooks/posttooluse/effects/logging_effect.py
  class LoggingEffectVerifier (5 methods)
  def __init__(2 params) -> ?
  def detect_config(3 params) -> ?
  def verify_config(3 params) -> EffectVerificationResult
  def detect(4 params) -> bool
  def verify(5 params) -> EffectVerificationResult

### P:/.claude/hooks/posttooluse/enforcement_tier_validator.py
  def validate_enforcement_tier(2 params) -> dict
  class EnforcementTierValidator (1 methods)
  def main(0 params) -> ?
  def process(4 params) -> dict

### P:/.claude/hooks/posttooluse/error_attribution_hook.py
  class ErrorAttributionHook (6 methods)
  def process(4 params) -> ?
  def _get_recent_mods(1 params) -> ?
  def _extract_error_files(1 params) -> ?
  def _find_related(2 params) -> ?
  def _create_injection(3 params) -> str

### P:/.claude/hooks/posttooluse/error_attribution_tracker.py
  class ErrorAttributionTracker (7 methods)
  def __init__(1 params) -> ?
  def process(4 params) -> ?
  def _is_excluded_file(2 params) -> bool
  def _extract_error_source(3 params) -> ?
  def _log_attribution(3 params) -> ?

### P:/.claude/hooks/posttooluse/evidence_tracker_hook.py
  class EvidenceTrackerHook (2 methods)
  def run(2 params) -> ?
  def process(4 params) -> ?

### P:/.claude/hooks/posttooluse/failure_recorder_hook.py
  class FailureRecorderHook (2 methods)
  def _import_detector_functions(1 params) -> ?
  def process(4 params) -> ?

### P:/.claude/hooks/posttooluse/falsification_assessor.py
  class FalsificationAssessor (8 methods)
  def __init__(1 params) -> ?
  def process(4 params) -> ?
  def _detect_unexpected_outcome(2 params) -> ?
  def _extract_expected_outcome(3 params) -> str
  def _format_actual_outcome(2 params) -> str

### P:/.claude/hooks/posttooluse/falsification_assessor_hook.py
  class FalsificationAssessorHook (1 methods)
  def process(4 params) -> ?

### P:/.claude/hooks/posttooluse/file_activity_tracker_hook.py
  class FileActivityTrackerHook (2 methods)
  def process(4 params) -> ?
  def _extract_file_path(1 params) -> ?

### P:/.claude/hooks/posttooluse/file_invalidation_tracker.py
  class FileInvalidationTrackerHook (1 methods)
  def process(4 params) -> ?

### P:/.claude/hooks/posttooluse/fix_validator.py
  class FixValidator (11 methods)
  def __init__(1 params) -> ?
  def process(4 params) -> ?
  def _is_code_file(2 params) -> bool
  def _check_syntax(3 params) -> ?
  def _extract_new_calls(3 params) -> ?

### P:/.claude/hooks/posttooluse/implementation_verifier.py
  class ImplementationVerifier (1 methods)
  def process(4 params) -> ?

### P:/.claude/hooks/posttooluse/inherited_choice_hook.py
  def _extract_text(1 params) -> str
  class InheritedChoiceHook (1 methods)
  def process(4 params) -> ?

### P:/.claude/hooks/posttooluse/integration_verifier.py
  class IntegrationVerifier (12 methods)
  def __init__(1 params) -> ?
  def _mode(1 params) -> str
  def process(4 params) -> ?
  def _extract_file_path(3 params) -> ?
  def _extract_skill_name(2 params) -> ?

### P:/.claude/hooks/posttooluse/investigation_tracker.py
  class InvestigationTracker (2 methods)
  def _get_ledger(1 params) -> ?
  def process(4 params) -> ?

### P:/.claude/hooks/posttooluse/lint_hook.py
  class LintHook (5 methods)
  def __init__(1 params) -> ?
  def process(4 params) -> dict
  def _get_extension(2 params) -> str
  def _is_linter_available(2 params) -> bool
  def _run_linter(3 params) -> ?

### P:/.claude/hooks/posttooluse/observable_effect_verifier.py
  class ObservableEffectVerifier (3 methods)
  def __init__(1 params) -> ?
  def process(4 params) -> ?
  def _extract_file_path(3 params) -> ?

### P:/.claude/hooks/posttooluse/outcome_validator_hook.py
  class OutcomeValidatorHook (4 methods)
  def process(4 params) -> ?
  def _load_json(1 params) -> dict
  def _save_json(2 params) -> ?
  def _clear(1 params) -> ?

### P:/.claude/hooks/posttooluse/posttooluse_sqa_phase_tracker.py
  def _get_state_dir(0 params) -> Path
  def _get_terminal_id(0 params) -> str
  def _get_layer_marker_path(0 params) -> Path
  def _get_invocation_state_path(0 params) -> Path
  def _is_sqa_invocation(1 params) -> bool
  def _extract_layer_from_marker(0 params) -> ?

### P:/.claude/hooks/posttooluse/python_syntax_checker.py
  class PythonSyntaxChecker (3 methods)
  def process(4 params) -> ?
  def _track_broken_state(3 params) -> ?
  def _clear_broken_state(2 params) -> ?

### P:/.claude/hooks/posttooluse/reflexion_verifier.py
  class DeferredEdit (0 methods)
  class ReflexionVerifier (25 methods)
  def __init__(1 params) -> ?
  def process(4 params) -> ?
  def _is_binary_file(2 params) -> bool
  def _is_code_file(2 params) -> bool

### P:/.claude/hooks/posttooluse/semantic_compress.py
  class SemanticCompress (7 methods)
  def __init__(1 params) -> ?
  def process(4 params) -> ?
  def _estimate_tokens(2 params) -> int
  def _should_compress(3 params) -> bool
  def _compress_output_async(3 params) -> ?

### P:/.claude/hooks/posttooluse/skill_command_hook.py
  class SkillCommandHook (3 methods)
  def __init__(6 params) -> ?
  def matches_tool(2 params) -> bool
  def process(4 params) -> ?

### P:/.claude/hooks/posttooluse/skill_execution_tracker.py
  class SkillExecutionTracker (6 methods)
  def __init__(1 params) -> ?
  def _import_functions(1 params) -> ?
  def _load_workflow_steps(2 params) -> ?
  def process(4 params) -> ?
  def _update_checkpoint_task_with_skill(2 params) -> ?

### P:/.claude/hooks/posttooluse/skill_invocation_logger_hook.py
  class SkillInvocationLoggerHook (3 methods)
  def process_prompt(1 params) -> dict
  def __init__(1 params) -> ?
  def _ensure_log_directory(1 params) -> ?
  def process(4 params) -> ?

### P:/.claude/hooks/posttooluse/speculation_detector_hook.py
  def _flatten_text(1 params) -> str
  class SpeculationDetectorHook (1 methods)
  def process(4 params) -> ?

### P:/.claude/hooks/posttooluse/strategy_escalation_hook.py
  def _target_hash(2 params) -> str
  def _is_structural_failure(1 params) -> bool
  def _load_ring(0 params) -> ?
  def _save_ring(1 params) -> ?
  class StrategyEscalationHook (1 methods)
  def process(4 params) -> ?

### P:/.claude/hooks/posttooluse/system2_hook.py
  def _get_tool_output(1 params) -> str
  def _detect_error_patterns(1 params) -> ?
  def _classify_error_with_confidence(1 params) -> ?
  def _classify_severity(1 params) -> str
  class System2Hook (1 methods)
  def process(4 params) -> ?

### P:/.claude/hooks/posttooluse/task_unresolved_suggester_hook.py
  def _detect_terminal_id(0 params) -> str
  def _load_detector_func(0 params) -> ?
  def _extract_tasks(1 params) -> ?
  class TaskUnresolvedSuggesterHook (1 methods)
  def process(4 params) -> ?

### P:/.claude/hooks/posttooluse/tdd95_autoscaffold_hook.py
  def should_scaffold_for(2 params) -> ?
  def find_best_test_path(2 params) -> ?
  def scaffold_test_file(2 params) -> ?
  def check_critical_hook_tests(2 params) -> ?
  def process_write(2 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/posttooluse/tdd_state_hook.py
  class TDDStateHook (6 methods)
  def _has_active_state_files(1 params) -> bool
  def _looks_like_test_command(2 params) -> bool
  def _looks_like_test_file(2 params) -> bool
  def _get_tdd_updated_at(2 params) -> ?
  def _get_updated_at_for_operation(3 params) -> ?

### P:/.claude/hooks/posttooluse/verification_tracker.py
  def _get_terminal_id(0 params) -> str
  def _get_state_file(0 params) -> Path
  def _create_default_state(1 params) -> dict
  class VerificationTracker (4 methods)
  def get_verification_state(0 params) -> dict
  def clear_verification_state(0 params) -> ?

### P:/.claude/hooks/posttooluse/workflow_completion_tracker.py
  class WorkflowCompletionTracker (7 methods)
  def __init__(1 params) -> ?
  def _import_functions(1 params) -> ?
  def process(4 params) -> ?
  def _extract_output_text(2 params) -> str
  def _get_workflow_tools(1 params) -> ?

### P:/.claude/hooks/PostToolUse.py
  def _resolve_session_id_for_intent(1 params) -> str
  def _resolve_terminal_id_for_intent(1 params) -> str
  def _clear_pending_skill_intent(1 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/PostToolUse_adversarial_aggregate.py
  def aggregate_subagent_results(3 params) -> dict

### P:/.claude/hooks/PostToolUse_artifact_access_tracker.py
  def _get_log_path(1 params) -> Path
  def _extract_file_paths(2 params) -> ?
  def track_tool_use(4 params) -> ?

### P:/.claude/hooks/PostToolUse_artifact_scraper.py
  def run(1 params) -> ?

### P:/.claude/hooks/PostToolUse_artifact_validator.py
  def _safe_id(1 params) -> str
  def _resolve_session_id(1 params) -> str
  def _resolve_terminal_id(1 params) -> str
  def _artifact_candidates(1 params) -> ?
  def _artifact_path(1 params) -> ?
  def _read_grounded_artifact(1 params) -> ?

### P:/.claude/hooks/PostToolUse_bash_syntax_gate.py
  def _get_terminal_id(0 params) -> str
  def _get_session_id(0 params) -> str
  def _load_pre_state(0 params) -> ?
  def run(1 params) -> ?

### P:/.claude/hooks/PostToolUse_breadcrumb_tracker.py
  def _get_current_skill(1 params) -> ?
  def run(1 params) -> ?

### P:/.claude/hooks/PostToolUse_claim_verifier_smoke.py
  def _enabled(0 params) -> bool
  def _normalize_path(1 params) -> str
  def _extract_paths(3 params) -> ?
  def _is_relevant_path(1 params) -> bool
  def _tail(2 params) -> str
  def _run_pytest(0 params) -> ?

### P:/.claude/hooks/PostToolUse_documentation_validator.py
  def _generate_deduplication_key(2 params) -> str
  def _filter_deduplicated_warnings(3 params) -> ?
  def _load_seen_warnings(1 params) -> ?
  def _save_seen_warnings(2 params) -> ?
  def run(1 params) -> dict
  def _is_markdown_file(1 params) -> bool

### P:/.claude/hooks/PostToolUse_e2e_tracker.py
  def _validate_session_id(1 params) -> str
  def _validate_workflow_fields(1 params) -> ?
  def _rotate_log_if_needed(2 params) -> ?
  def _cleanup_expired_sessions(1 params) -> ?
  def track_workflow(7 params) -> ?
  def post_tool_use_hook(4 params) -> ?

### P:/.claude/hooks/PostToolUse_p2_filter_gate.py
  def check_for_filtering_evidence(1 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/PostToolUse_powershell_validator.py
  class ValidationResult (1 methods)
  class PowerShellArgumentValidator (10 methods)
  def run(1 params) -> ?
  def __str__(1 params) -> str
  def __init__(3 params) -> ?
  def validate_file(2 params) -> ValidationResult

### P:/.claude/hooks/PostToolUse_router.py
  def log(1 params) -> ?
  def _resolve_session_from_payload(1 params) -> str
  def _set_session_terminal_context(1 params) -> str
  def _handle_tracking_error(3 params) -> ?
  def _resolve_session_id_for_intent(1 params) -> str
  def _resolve_terminal_id_for_intent(0 params) -> str

### P:/.claude/hooks/posttooluse_self_reflection_reminder.py
  def count_session_writes(1 params) -> int
  def check_risky_patterns(2 params) -> ?
  def generate_advisor(2 params) -> str
  def main(0 params) -> ?

### P:/.claude/hooks/PostToolUse_tdd_state.py
  def handle_test_file_write(2 params) -> ?
  def handle_test_run(4 params) -> ?
  def handle_impl_file_write(2 params) -> ?
  def log_tdd_phase_transition(5 params) -> ?
  def get_phase_enforcement_tier(1 params) -> str
  def is_evidence_tracking_enabled(0 params) -> bool

### P:/.claude/hooks/PostToolUse_tdd_state_tracker.py
  def _get_state_file(0 params) -> Path
  def check_explicit_marker(1 params) -> ?
  def check_evidence(4 params) -> bool
  def read_state(0 params) -> dict
  def write_state(1 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/PostToolUse_wrapper_validator.py
  def run(1 params) -> ?

### P:/.claude/hooks/pre/PreToolUse_tool_check.py
  def validate_tool_use(2 params) -> dict
  def main(0 params) -> ?

### P:/.claude/hooks/pre-commit-deadcode-check.py
  def check_dead_code_with_grep(1 params) -> ?
  def main(0 params) -> int

### P:/.claude/hooks/pre_tool_use_constitutional_check.py
  def check_constitutional_compliance(3 params) -> ?
  def read_constitutional_constraints(1 params) -> ?
  def check_constraints(3 params) -> ?
  def pre_tool_use(2 params) -> ?

### P:/.claude/hooks/PreCompact.py
  def main(0 params) -> ?

### P:/.claude/hooks/preflight_require_tdd.py
  def main(0 params) -> ?

### P:/.claude/hooks/PreToolUse/debugrca_tool_gate.py
  def check_tool_availability(0 params) -> ?
  def handle_pre_tool_use(1 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/PreToolUse/secret_scanner.py
  def read_stdin(0 params) -> ?
  def get_secret_patterns(0 params) -> ?
  def get_whitelist_patterns(0 params) -> ?
  def is_test_file(1 params) -> ?
  def get_non_scanned_extensions(0 params) -> ?
  def should_scan_file(1 params) -> ?

### P:/.claude/hooks/PreToolUse.py
  def _validate_intent_ttl(1 params) -> int
  def _env_bool(2 params) -> bool
  def _skill_first_mode_pretool(0 params) -> str
  def _log_skill_first_event(5 params) -> ?
  def _safe_id(1 params) -> str
  def _parse_iso_timestamp(1 params) -> ?

### P:/.claude/hooks/PreToolUse_arch_first_enforcer.py
  def _is_arch_file(1 params) -> bool
  def _get_state_file(1 params) -> Path
  def _store_declaration_state(2 params) -> ?
  def _load_declaration_state(1 params) -> ?
  def _clear_declaration_state(1 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/PreToolUse_ask_first_tool_gate.py
  def _is_ask_invocation(1 params) -> bool
  def _has_routing_decision(1 params) -> bool
  def _is_first_tool_blocked(1 params) -> bool
  def evaluate(3 params) -> ?

### P:/.claude/hooks/PreToolUse_authorization_gate.py
  def _model_ready_fallback(0 params) -> bool
  def _remove_shell_comments(1 params) -> str
  def _extract_python_c_match(1 params) -> ?
  def _contains_subprocess_call(1 params) -> bool
  def extract_actual_command(1 params) -> str
  def _check_destructive_patterns(1 params) -> ?

### P:/.claude/hooks/PreToolUse_bash_syntax_validator.py
  def _validator_mode(0 params) -> str
  def _parse_with_timeout(2 params) -> ?
  def _extract_python_c_code(1 params) -> ?
  def _normalize_shell_escaped_code(2 params) -> str
  def validate_python_c(2 params) -> ?
  def validate_bash_paths(1 params) -> ?

### P:/.claude/hooks/PreToolUse_breadcrumb_gate.py
  def _get_step_kind_from_tool(1 params) -> ?
  def _get_expected_next_step(1 params) -> ?
  def _is_valid_progression(2 params) -> bool
  def _get_skill_from_context(1 params) -> ?
  def run(1 params) -> dict

### P:/.claude/hooks/PreToolUse_breadcrumb_verifier.py
  def main(0 params) -> int

### P:/.claude/hooks/PreToolUse_bulk_delete_gate.py
  def extract_delete_target(1 params) -> ?
  def is_safe_target(1 params) -> bool
  def count_files(1 params) -> ?
  def create_git_tag(1 params) -> ?
  def run(1 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/PreToolUse_command_intent_gate.py
  def _get_session_id(0 params) -> str
  def _get_intent_state_files(0 params) -> ?
  def get_pending_intent(0 params) -> ?
  def clear_intent_state(0 params) -> ?
  def log_decision(5 params) -> ?
  def is_skill_execution(2 params) -> bool

### P:/.claude/hooks/PreToolUse_delegation_gate.py
  def _get_artifacts_dir(1 params) -> Path
  def _detect_terminal_id(0 params) -> str
  def _is_expired(2 params) -> bool
  def _load_delegation_state(1 params) -> ?
  def _clear_delegation_state(1 params) -> ?
  def _log_gate_event(3 params) -> ?

### P:/.claude/hooks/PreToolUse_dependency_verification_gate.py
  def clean_package_name(1 params) -> str
  def validate_package_name(2 params) -> bool
  def parse_stdin(0 params) -> ?
  def get_terminal_id(1 params) -> str
  def get_state_path(1 params) -> Path
  def load_verification_state(1 params) -> dict

### P:/.claude/hooks/PreToolUse_destructive_git_guard.py
  def check_bash_command(1 params) -> ?
  def check_git_command(1 params) -> ?
  def check_gh_command(1 params) -> ?
  def get_affected_files(1 params) -> ?
  def main(0 params) -> ?
  def run(1 params) -> ?

### P:/.claude/hooks/PreToolUse_directory_policy.py
  def _validate_directory_policy_schema(2 params) -> ?
  def is_allowed_external_path(1 params) -> bool
  def check_csf_nip_path(1 params) -> ?
  def _is_interpreter_script_path(2 params) -> bool
  def extract_paths_from_bash(1 params) -> ?
  def check_content_size(2 params) -> ?

### P:/.claude/hooks/PreToolUse_discovery_tracker.py
  def get_session_id(1 params) -> ?
  def write_state_atomic(2 params) -> ?
  def main(1 params) -> ?

### P:/.claude/hooks/PreToolUse_domain_tool_router.py
  def detect_chat_history(1 params) -> bool
  def detect_web_source(1 params) -> bool
  def detect_knowledge(1 params) -> bool
  def detect_combined_search(1 params) -> bool
  def classify_query(1 params) -> ?
  def build_suggestion(2 params) -> str

### P:/.claude/hooks/PreToolUse_evidence_hierarchy_gate.py
  def _extract_query(1 params) -> str
  def _get_session_id(1 params) -> ?
  def run(1 params) -> ?

### P:/.claude/hooks/PreToolUse_file_existence_guard.py
  def parse_stdin(0 params) -> ?
  def extract_file_path(1 params) -> ?
  def file_exists(1 params) -> bool
  def read_file_content(1 params) -> ?
  def extract_new_content(2 params) -> ?
  def content_matches(2 params) -> bool

### P:/.claude/hooks/PreToolUse_git_auto_stage.py
  def run_git_cmd(2 params) -> ?
  def find_git_root(1 params) -> ?
  def is_tracked_by_git(2 params) -> bool
  def should_skip_path(1 params) -> bool
  def should_never_stage(1 params) -> bool
  def extract_delete_targets(1 params) -> ?

### P:/.claude/hooks/PreToolUse_git_remote_check_order_guard.py
  def _env_value(2 params) -> str
  def _session_id(0 params) -> str
  def _terminal_id(0 params) -> str
  def _state_dir(0 params) -> Path
  def _session_state_path(0 params) -> Path
  def _load_state(0 params) -> dict

### P:/.claude/hooks/PreToolUse_git_safety.py
  def ensure_fresh_index(1 params) -> ?
  def run_git_cmd(1 params) -> ?
  def get_git_status(0 params) -> dict
  def check_forgettables(1 params) -> ?
  def check_suspicious(1 params) -> ?
  def check_untracked_tests(1 params) -> ?

### P:/.claude/hooks/PreToolUse_git_state_capture.py
  def _get_terminal_id(0 params) -> str
  def _get_session_id(0 params) -> str
  def _could_modify_py_files(1 params) -> bool
  def _capture_git_status(1 params) -> dict
  def run(1 params) -> ?

### P:/.claude/hooks/PreToolUse_implementation_default_gate.py
  def _get_trigger_label(1 params) -> str
  def _has_implementation_intent(1 params) -> bool
  def _get_state_path(0 params) -> ?
  def _set_intent_allowed(4 params) -> ?
  def _is_intent_allowed(3 params) -> ?
  def _clear_intent_state(3 params) -> ?

### P:/.claude/hooks/PreToolUse_investigation_gate.py
  def sanitize_path(1 params) -> str
  def _safe_id_str(1 params) -> str
  def _is_compaction_scenario(2 params) -> bool
  def _reconstruct_files_read_from_input(1 params) -> ?
  def get_cks_cache(0 params) -> ?
  def _load_cks_preload(0 params) -> ?

### P:/.claude/hooks/PreToolUse_mcp_full_read_guard.py
  def _check_url(1 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/PreToolUse_observe_before_act_gate.py
  def _is_skill_tool(1 params) -> bool
  def _is_read_tool(1 params) -> bool
  def _is_bash_tool(1 params) -> bool
  def _canonical_skill_name(1 params) -> str
  def _is_readonly_bash_command(1 params) -> bool
  def _loaded_skill_name(0 params) -> str

### P:/.claude/hooks/PreToolUse_ownership_colocation_gate.py
  def _log_block(2 params) -> ?
  def _normalize(1 params) -> str
  def _extract_path(2 params) -> str
  def _matches(2 params) -> bool
  def _prompt_has_bypass(1 params) -> bool
  def main(0 params) -> ?

### P:/.claude/hooks/PreToolUse_package_import_gate.py
  def _is_package_python_file(1 params) -> bool
  def _get_package_root(1 params) -> ?
  def _verify_imports(3 params) -> ?
  def _verify_imports_from_content(2 params) -> ?
  def run(1 params) -> ?

### P:/.claude/hooks/PreToolUse_parent_directory_creator.py
  def ensure_parent_directory(1 params) -> bool
  def run(1 params) -> ?
  def test_case(3 params) -> ?

### P:/.claude/hooks/PreToolUse_path_validator.py
  class EnhancedPathValidator (5 methods)
  def validate_file_with_context(3 params) -> ?
  def validate_operation_with_context(3 params) -> ?
  def show_context_status_simple(0 params) -> ?
  class ToolOperationValidator (3 methods)
  def run(1 params) -> ?

### P:/.claude/hooks/PreToolUse_protected_file_recovery_gate.py
  def _resolve_hooks_dir(0 params) -> str
  def _is_recovery_for_file(2 params) -> bool
  def run(1 params) -> dict
  def main(0 params) -> ?

### P:/.claude/hooks/PreToolUse_python_import_gate.py
  def is_hook_directory(1 params) -> bool
  def validate_syntax(1 params) -> ?
  def extract_imports(1 params) -> ?
  def extract_used_names(1 params) -> ?
  def detect_missing_imports(2 params) -> ?
  def is_critical_missing_import(1 params) -> bool

### P:/.claude/hooks/PreToolUse_referent_scope_gate.py
  def _get_terminal_id(1 params) -> str
  def _read_state(1 params) -> ?
  def _write_state(2 params) -> ?
  def _get_tool_text(1 params) -> str
  def _check_overlap(2 params) -> ?
  def _build_block_message(2 params) -> str

### P:/.claude/hooks/PreToolUse_repo_visibility_guard.py
  def is_protected_path(1 params) -> bool
  def is_allowed_public_path(1 params) -> bool
  def detect_visibility_change(1 params) -> ?
  def get_current_repo_path(0 params) -> ?
  def run(1 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/PreToolUse_require_plan_for_features.py
  def is_refactor(1 params) -> bool
  def is_bug_fix(1 params) -> bool
  def is_crud_or_simple(1 params) -> bool
  def get_ready_for_implementation_plans(0 params) -> ?
  def has_active_plan_review_state(0 params) -> bool
  def plan_exists(0 params) -> bool

### P:/.claude/hooks/PreToolUse_risk_tier_gate.py
  def classify_command(2 params) -> ?
  def handle_advisory(2 params) -> ?
  def get_last_user_message(1 params) -> ?
  def handle_confirm(2 params) -> ?
  def handle_deny(2 params) -> dict
  def run(1 params) -> ?

### P:/.claude/hooks/PreToolUse_sequential_thinking.py
  def pre_tool_use(1 params) -> dict
  def _format_hypothesis_context(1 params) -> str
  def _find_active_session(1 params) -> ?

### P:/.claude/hooks/PreToolUse_session_id_capture.py
  def _write_session_file(1 params) -> bool
  def _main(0 params) -> ?

### P:/.claude/hooks/PreToolUse_settings_backup.py
  def backup_settings_json(1 params) -> ?
  def validate_json_syntax(1 params) -> ?
  def run(1 params) -> ?

### P:/.claude/hooks/PreToolUse_syntax_gate.py
  def main(0 params) -> ?

### P:/.claude/hooks/PreToolUse_task_self_doc_gate.py
  def _get_bypass(0 params) -> bool
  def _is_task_gate_eligible(1 params) -> ?
  def _validate_task_doc(2 params) -> ?
  def _auto_correct_params(2 params) -> ?
  def run(1 params) -> ?
  def main(0 params) -> int

### P:/.claude/hooks/PreToolUse_tdd95_gate.py
  def _extract_function_names_from_code(1 params) -> ?
  def _extract_function_names_regex(1 params) -> ?
  def _extract_function_from_edit(1 params) -> ?
  def _get_functions_tested_by_file(1 params) -> ?
  def _check_function_coverage(3 params) -> ?
  def _find_best_test_path(2 params) -> ?

### P:/.claude/hooks/PreToolUse_tdd_contract_gate.py
  def _is_test_file(1 params) -> bool
  def _get_impl_for_test(1 params) -> Path
  def _get_state_manager(2 params) -> TDDPhaseStateManager
  def process_hook(2 params) -> ?

### P:/.claude/hooks/PreToolUse_type_validator.py
  def _get_workspace_root(0 params) -> str
  def _load_policy(0 params) -> dict
  def _get_allowed_config_extensions(1 params) -> ?
  def _has_code_extension_in_segments(1 params) -> bool
  def _is_in_hooks_dir(1 params) -> bool
  def check_type_mismatch(1 params) -> dict

### P:/.claude/hooks/PreToolUse_user_delegation_gate.py
  def _safe_id_str(1 params) -> str
  def _get_terminal_id(0 params) -> str
  def _has_user_delegation_signal(1 params) -> bool
  def run(1 params) -> ?

### P:/.claude/hooks/PreToolUse_verification_modules/investigation_verification.py
  def check_bypass_flag(1 params) -> bool
  def _log_bypass_usage(1 params) -> ?
  def has_investigation_keywords(1 params) -> bool
  def run(1 params) -> ?

### P:/.claude/hooks/PreToolUse_verification_router.py
  def load_verification_modules(1 params) -> ?
  def _run_single_module(2 params) -> ?
  def run_verification_modules(1 params) -> ?
  def _needs_verification(1 params) -> bool
  def sanitize_input(1 params) -> ?
  def normalize_input_fields(1 params) -> ?

### P:/.claude/hooks/PreToolUse_win32_path_gate.py
  def run(1 params) -> ?
  def check(3 params) -> ?

### P:/.claude/hooks/PreToolUse_windows_path_unicode_gate.py
  def _has_escape_issue(1 params) -> bool
  def _extract_c_string_body(1 params) -> ?
  def _is_windows_path_unicode_issue(1 params) -> ?
  def process(1 params) -> ?

### P:/.claude/hooks/principle_monitor.py
  def has_evidence_citation(1 params) -> bool
  def detect_change_without_evidence(1 params) -> bool
  def detect_context_grounding_violation(1 params) -> bool
  def detect_redundant_broad_question(1 params) -> bool
  def detect_opaque_uncertainty(1 params) -> bool
  def load_state(0 params) -> dict

### P:/.claude/hooks/reasoning_quality_gate_monitor.py
  def _resolve_log_path(0 params) -> Path
  def load_logs(1 params) -> ?
  def calculate_statistics(1 params) -> Dict
  def show_statistics(1 params) -> ?
  def check_health(1 params) -> int
  def show_recent(2 params) -> ?

### P:/.claude/hooks/recursive_failure_detector.py
  def is_investigation_loop_advisory_mode(0 params) -> bool
  def log_investigation_loop_warning(3 params) -> ?
  def get_session_file(0 params) -> Path
  def load_failures(0 params) -> list
  def save_failure(3 params) -> ?
  def compute_command_hash(1 params) -> str

### P:/.claude/hooks/refactor_validation.py
  def validate_python_syntax(1 params) -> ?
  def validate_with_pytest(1 params) -> ?
  def validate_and_exit(3 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/reflect_performance_monitor.py
  def check_performance(1 params) -> ?

### P:/.claude/hooks/repositories/base_repository.py
  def _retry_sqlite_transient(2 params) -> ?
  class RepositoryResult (0 methods)
  class BaseRepository (9 methods)
  def decorator(1 params) -> ?
  def __init__(2 params) -> ?
  def conn(1 params) -> ?

### P:/.claude/hooks/repositories/doc_cks_ingester.py
  def on_file_written(2 params) -> ?
  def should_ingest(1 params) -> bool
  def is_docs_path(1 params) -> bool
  def trigger_cks_ingest(1 params) -> ?

### P:/.claude/hooks/repositories/project_context_repository.py
  class ProjectContext (1 methods)
  class ProjectContextRepository (11 methods)
  def to_dict(1 params) -> ?
  def initialize_schema(1 params) -> bool
  def create(5 params) -> ?
  def get_by_tsk_id(2 params) -> ?

### P:/.claude/hooks/repositories/task_repository.py
  class Task (3 methods)
  class TaskRepository (15 methods)
  def to_dict(1 params) -> ?
  def has_checkpoint(1 params) -> bool
  def is_stale_compact(2 params) -> bool
  def initialize_schema(1 params) -> bool

### P:/.claude/hooks/research_router.py
  def load_config(0 params) -> ?
  def log_decision(3 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/rotate_logs.py
  def main(0 params) -> ?

### P:/.claude/hooks/scanners/agreement_consistency_scanner.py
  class AgreementConsistencyScanner (1 methods)
  def scan(3 params) -> ScanResult

### P:/.claude/hooks/scanners/base_scanner.py
  class ScanStatus (0 methods)
  class ScanResult (2 methods)
  class BaseScanner (6 methods)
  def is_valid(1 params) -> bool
  def to_dict(1 params) -> dict
  def __init__(2 params) -> ?

### P:/.claude/hooks/scanners/hallucination_scanner.py
  class AtomicFact (0 methods)
  class HallucinationScanner (8 methods)
  def __init__(3 params) -> ?
  def scan(3 params) -> ScanResult
  def _extract_known_files(2 params) -> ?
  def _extract_execution_evidence(2 params) -> ?

### P:/.claude/hooks/scanners/intent_drift_scanner.py
  class IntentDriftScanner (12 methods)
  def __init__(3 params) -> ?
  def scan(3 params) -> ScanResult
  def _get_current_goal(2 params) -> ?
  def _extract_action(2 params) -> ?
  def _classify_action(2 params) -> str

### P:/.claude/hooks/scanners/pii_scanner.py
  class PIIScanner (3 methods)
  def scan_for_pii(2 params) -> bool
  def __init__(3 params) -> ?
  def scan(3 params) -> ScanResult
  def get_pattern_count(1 params) -> int

### P:/.claude/hooks/scanners/reflexion_validator.py
  class ValidationResult (0 methods)
  class ReflexionValidator (10 methods)
  def __init__(3 params) -> ?
  def validation_history(1 params) -> ?
  def clear_history(1 params) -> ?
  def scan(3 params) -> ScanResult

### P:/.claude/hooks/scripts/check_orphaned_stop_modules.py
  class ModuleInfo (0 methods)
  def _read_docstring(1 params) -> str
  def _check_wired(2 params) -> bool
  def _check_docstring_markers(1 params) -> ?
  def _scan_modules(1 params) -> ?
  def _orphaned(1 params) -> ?

### P:/.claude/hooks/scripts/cks/cleanup_cks.py
  def calculate_entry_quality(1 params) -> float
  def find_low_quality_entries(2 params) -> list
  def delete_entries(1 params) -> int
  def print_cleanup_report(2 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/scripts/cks/ingest_memory_to_cks.py
  def chunk_by_headers(2 params) -> ?
  def ingest_memory_file(3 params) -> dict
  def main(0 params) -> ?

### P:/.claude/hooks/scripts/diagnostics/dx_tools_analyze_blocks.py
  def parse_arguments(0 params) -> ?
  def load_blocks(2 params) -> ?
  def analyze_blocks(1 params) -> ?
  def print_report(2 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/scripts/hook-dev/audit_hook_wrappers.py
  def audit_hooks(0 params) -> ?
  def print_report(3 params) -> ?
  def main(0 params) -> int

### P:/.claude/hooks/scripts/hook-dev/batch_add_hook_main.py
  def add_hook_main_decorator(1 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/scripts/hook-dev/hook_health_check.py
  def parse_log_entry(1 params) -> ?
  def analyze_log_file(1 params) -> dict
  def get_configured_hooks(0 params) -> set
  def get_log_directory_size(0 params) -> float
  def main(0 params) -> ?

### P:/.claude/hooks/scripts/hook-dev/verify_hook_registration.py
  def extract_hook_registrations(1 params) -> ?
  def extract_subprocess_hooks(1 params) -> ?
  def find_duplicates_within_list(1 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/scripts/hook-dev/wrap_all_hooks.py
  def wrap_command(2 params) -> str
  def main(0 params) -> ?

### P:/.claude/hooks/scripts/logs/find_errors.py
  def parse_duration(1 params) -> timedelta
  def load_jsonl(1 params) -> ?
  def search_errors(5 params) -> ?
  def format_error(1 params) -> str
  def main(0 params) -> ?
  def get_ts(1 params) -> ?

### P:/.claude/hooks/scripts/logs/rotate_logs.py
  def main(2 params) -> ?

### P:/.claude/hooks/scripts/migrations/measure_baseline.py
  def measure_baseline(0 params) -> ?
  def main(0 params) -> int

### P:/.claude/hooks/scripts/migrations/migrate_cognitive_config.py
  def load_legacy_config(1 params) -> dict
  def create_unified_config(1 params) -> dict
  def backup_config(1 params) -> Path
  def write_unified_config(2 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/scripts/migrations/monitor_progress.py
  def record_metric(4 params) -> ?
  def generate_summary_report(0 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/scripts/migrations/setup_monitoring.py
  def create_monitoring_database(0 params) -> ?
  def create_monitoring_config(0 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/scripts/tune_subagent_gate.py
  def load_telemetry(2 params) -> ?
  def analyze_prospector(1 params) -> ?
  def analyze_opportunity(1 params) -> ?
  def get_agent_usage(1 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/scripts/verification/analyze_post_skill_prose_metrics.py
  def parse_log_file(1 params) -> ?
  def filter_post_skill_events(1 params) -> ?
  def filter_by_time_window(2 params) -> ?
  def calculate_metrics(1 params) -> dict
  def format_report(2 params) -> str
  def main(0 params) -> ?

### P:/.claude/hooks/scripts/verification/analyze_verification_telemetry.py
  def load_jsonl_logs(1 params) -> ?
  def filter_by_week(2 params) -> ?
  def analyze_blocked_claims(1 params) -> dict
  def calculate_false_positive_rate(1 params) -> dict
  def analyze_tier_distribution(1 params) -> dict
  def analyze_tool_usage(1 params) -> dict

### P:/.claude/hooks/scripts/verification/monitor_hook_outcomes.py
  def load_violations(1 params) -> ?
  def compute_trend(2 params) -> str
  def print_report(1 params) -> int
  def main(0 params) -> int

### P:/.claude/hooks/scripts/verification/weekly_verification_analysis.py
  def generate_weekly_report(2 params) -> ?
  def _analyze_false_positives(1 params) -> ?
  def _generate_recommendations(2 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/seed_compatibility_matrix.py
  def main(0 params) -> ?

### P:/.claude/hooks/self_verification_gate.py
  def _get_response_text(1 params) -> str
  def _get_tool_events(1 params) -> ?
  def _get_session_context(1 params) -> dict
  def _check_completion_claim_with_events(2 params) -> ?
  def _detect_completion_claims(1 params) -> ?
  def _check_claim_verified(2 params) -> ?

### P:/.claude/hooks/session_data/migrate_event_key.py
  def migrate(0 params) -> ?

### P:/.claude/hooks/session_data_retention.py
  def _try_acquire_cleanup_lock(0 params) -> bool
  def _release_cleanup_lock(0 params) -> ?
  def _cleanup_stale_locks(1 params) -> ?
  def _cleanup_state_files(1 params) -> ?
  def _cleanup_session_data(1 params) -> ?
  def _cleanup_logs(1 params) -> ?

### P:/.claude/hooks/session_file_cache.py
  class SessionFileCache (9 methods)
  def __init__(2 params) -> ?
  def get(3 params) -> Any
  def _is_cache_valid(4 params) -> bool
  def _read_file(3 params) -> Any
  def _update_cache(5 params) -> ?

### P:/.claude/hooks/SessionEnd_breadcrumb_cleanup.py
  def run(1 params) -> dict

### P:/.claude/hooks/SessionEnd_cleanup.py
  def _safe_id(1 params) -> str
  def _resolve_session_id(1 params) -> str
  def _resolve_terminal_id(1 params) -> str
  def _delete_if_exists(1 params) -> ?
  def _terminal_cleanup_keys(1 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/SessionEnd_tdd_cleanup.py
  def cleanup_expired_tdd_states(1 params) -> dict
  def main(0 params) -> ?
  def detect_terminal_id(0 params) -> str

### P:/.claude/hooks/SessionStart/registry.py
  def register_session_hook(2 params) -> ?
  def run_session_hooks(1 params) -> ?
  def decorator(1 params) -> ?

### P:/.claude/hooks/SessionStart.py
  def _extract_contexts(1 params) -> ?
  def run_setup_task(2 params) -> ?
  def main(0 params) -> ?
  def process_start(1 params) -> dict

### P:/.claude/hooks/SessionStart_breadcrumb_init.py
  def main(0 params) -> ?

### P:/.claude/hooks/SessionStart_cc_health.py
  def _telemetry_enabled(0 params) -> bool
  def _get_session_mode(0 params) -> str
  def main(0 params) -> int

### P:/.claude/hooks/SessionStart_characterization_check.py
  def _get_hook_files(0 params) -> ?
  def _run_drift_check(0 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/SessionStart_chs_delta_reindex.py
  def _resolve_terminal_id(1 params) -> str
  def _safe_id(1 params) -> str
  def _get_state_path(1 params) -> Path
  def _read_last_line_count(1 params) -> int
  def _write_last_line_count(2 params) -> ?
  def extract_text_content(1 params) -> str

### P:/.claude/hooks/SessionStart_commitment_tracker.py
  def main(0 params) -> ?
  def _format_commitments(1 params) -> str
  def _extract_terminal_id(1 params) -> str

### P:/.claude/hooks/SessionStart_constraint_display.py
  def display_constraints_banner(0 params) -> ?
  def format_constraint_banner(1 params) -> str
  def main(0 params) -> ?

### P:/.claude/hooks/SessionStart_contract_health.py
  def main(0 params) -> int

### P:/.claude/hooks/SessionStart_dreaming_daemon.py
  def get_project_root(0 params) -> Path
  def measure_latency(1 params) -> ?
  def is_daemon_healthy(1 params) -> bool
  def check_upstream_health(1 params) -> ?
  def acquire_startup_mutex(0 params) -> ?
  def release_startup_mutex(1 params) -> ?

### P:/.claude/hooks/SessionStart_folder_context.py
  def get_recent_activity(1 params) -> ?
  def extract_files_and_queries(1 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/SessionStart_hook_health_check.py
  def _check_file(1 params) -> ?
  def _snake_to_filename(1 params) -> str
  def _extract_hook_targets(1 params) -> ?
  def _collect_wired_hook_files(0 params) -> ?
  def _collect_router_hooks(0 params) -> ?
  def _collect_orphan_hooks(1 params) -> ?

### P:/.claude/hooks/SessionStart_hook_import_health.py
  def check_import(1 params) -> ?
  def check_registry(0 params) -> ?
  def check_naming_conflict(0 params) -> ?
  def run_health_checks(0 params) -> ?
  def main(0 params) -> int

### P:/.claude/hooks/SessionStart_log_rotation.py
  def _should_run_rotation(0 params) -> bool
  def _update_throttle_timestamp(0 params) -> ?
  def _rotate_adversarial_files(0 params) -> int
  def main(0 params) -> ?

### P:/.claude/hooks/SessionStart_memory_cks_auto.py
  def acquire_lock(0 params) -> bool
  def release_lock(0 params) -> ?
  def get_last_ingestion_timestamp(0 params) -> ?
  def save_ingestion_timestamp(1 params) -> ?
  def get_memory_files(0 params) -> ?
  def check_files_need_ingestion(1 params) -> bool

### P:/.claude/hooks/SessionStart_memory_monitor.py
  def main(0 params) -> ?
  def check_memory_limit(1 params) -> ?

### P:/.claude/hooks/SessionStart_search_daemon.py
  def get_project_root(0 params) -> Path
  def measure_latency(1 params) -> ?
  def is_daemon_healthy(1 params) -> bool
  def acquire_startup_mutex(0 params) -> ?
  def release_startup_mutex(1 params) -> ?
  def start_daemon(3 params) -> ?

### P:/.claude/hooks/SessionStart_semantic_daemon.py
  def get_project_root(0 params) -> Path
  def is_daemon_running(0 params) -> bool
  def kill_stale_daemons(1 params) -> ?
  def start_daemon(1 params) -> ?
  def check_daemon_health(1 params) -> bool
  def wait_for_daemon_discovery(2 params) -> bool

### P:/.claude/hooks/SessionStart_symlink_check.py
  def main(0 params) -> ?

### P:/.claude/hooks/SessionStart_task_identity.py
  def ensure_state_files(1 params) -> ?
  def _get_git_executable(0 params) -> str
  def infer_task_from_context(1 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/SessionStart_terminal_id.py
  def _normalize_id(2 params) -> str
  def get_session_id(0 params) -> str
  def write_terminal_id_to_shared_file(1 params) -> bool
  def write_session_start_file(1 params) -> bool
  def persist_terminal_id_to_project(2 params) -> bool
  def cleanup_stale_terminal_state(2 params) -> int

### P:/.claude/hooks/SessionStart_timeline.py
  def get_last_checkpoint(0 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/SessionStart_universal_skills_manager.py
  def load_skillsmp_config(0 params) -> ?

### P:/.claude/hooks/SessionStart_verification_cleanup.py
  def cleanup_old_file_existence_decisions(1 params) -> int
  def cleanup_old_verification_states(1 params) -> int
  def cleanup_old_observe_before_act(1 params) -> int
  def cleanup_old_anti_sycophancy_injector(1 params) -> int
  def cleanup_old_grounded_artifacts(1 params) -> int
  def cleanup_old_pretool_degraded(1 params) -> int

### P:/.claude/hooks/shared/intent_classifier.py
  def _load_or_compute_embeddings(0 params) -> ?
  def _get_model(0 params) -> ?
  def classify_intent(1 params) -> IntentCategory

### P:/.claude/hooks/shared_utils.py
  def ensure_dirs(0 params) -> ?
  def load_state(1 params) -> dict
  def save_state(3 params) -> ?
  def _save_state_immediate(2 params) -> ?
  def _flush_state_buffer(0 params) -> ?
  def flush_all_states(0 params) -> ?

### P:/.claude/hooks/skill_execution_state.py
  def _get_legacy_skill_metadata_cache(0 params) -> ?
  def _get_state_file(0 params) -> Path
  def _load_skill_frontmatter(1 params) -> ?
  def _get_active_turn_scope(0 params) -> ?
  def set_skill_loaded(7 params) -> ?
  def record_tool_use(2 params) -> ?

### P:/.claude/hooks/Start_reasoning_mode_selector.py
  def _resolve_reasoning_package(0 params) -> Path
  def analyze_query(1 params) -> ?
  def process_prompt(1 params) -> dict

### P:/.claude/hooks/stop/archived/Stop_tdd_refactor_gate.py
  def _get_session_id(0 params) -> str
  def _get_block_count_path(0 params) -> Path
  def _load_block_count(0 params) -> int
  def _save_block_count(1 params) -> ?
  def _check_active_refactor(0 params) -> ?
  def _has_refactor_evidence(1 params) -> bool

### P:/.claude/hooks/stop/evidence_verification_gate.py
  class EvidenceVerificationGate (3 methods)
  def process(2 params) -> dict
  def _extract_task_id(2 params) -> ?
  def _run_python_tests(2 params) -> ?
  def process(3 params) -> dict

### P:/.claude/hooks/stop/experimental/evidence_verification_gate.py
  class EvidenceVerificationGate (3 methods)
  def process(2 params) -> dict
  def _extract_task_id(2 params) -> ?
  def _run_python_tests(2 params) -> ?
  def process(3 params) -> dict

### P:/.claude/hooks/stop/experimental/phase0_depends_on_skills.py
  def _is_enabled(2 params) -> bool
  def _detect_skill_from_transcript(1 params) -> ?
  def _get_depends_on_skills(1 params) -> ?
  def _get_evidence_dir_for_skill(2 params) -> Path
  def _check_step1_evidence(2 params) -> ?
  def run(1 params) -> ?

### P:/.claude/hooks/stop/experimental/Stop_tdd_refactor_gate.py
  def _get_session_id(0 params) -> str
  def _get_block_count_path(0 params) -> Path
  def _load_block_count(0 params) -> int
  def _save_block_count(1 params) -> ?
  def _check_active_refactor(0 params) -> ?
  def _has_refactor_evidence(1 params) -> bool

### P:/.claude/hooks/stop/Stop_verification_gate.py
  def _check_claim_patterns(2 params) -> ?
  def _check_solution_jump_patterns(2 params) -> ?
  def _parse_hypotheses_from_text(1 params) -> ?
  def _detect_urgency(1 params) -> bool
  def _format_structured_feedback(3 params) -> str
  def _has_verification_tools_this_turn(2 params) -> bool

### P:/.claude/hooks/Stop.py
  def _env_bool(2 params) -> bool
  def _skill_first_mode_stop(0 params) -> str
  def _log_skill_first_stop_event(4 params) -> ?
  def _log_stop_block_event(3 params) -> ?
  def _resolve_anti_sycophancy_log_path(0 params) -> Path
  def _anti_sycophancy_log_candidates(0 params) -> ?

### P:/.claude/hooks/Stop_acknowledgment_loop.py
  def run_acknowledgment_loop(1 params) -> ?
  def on_load(0 params) -> ?

### P:/.claude/hooks/Stop_advisory.py
  def _safe_id(1 params) -> str
  def _coach_note_path(0 params) -> Path
  def _write_coach_note(1 params) -> ?
  def _clear_coach_note(0 params) -> ?
  def read_and_clear_coach_note(0 params) -> ?
  def check_advisories(1 params) -> ?

### P:/.claude/hooks/Stop_aggregator.py
  def _aggregation_enabled(0 params) -> bool
  class RawHookResult (0 methods)
  class AggregatedIssue (0 methods)
  def _normalize_hook_name(1 params) -> str
  def classify_result(2 params) -> ?
  def _find_collapse_root(1 params) -> RootIssue

### P:/.claude/hooks/Stop_approval_gate.py
  def _terminal_id(0 params) -> str
  def _approval_file(0 params) -> Path
  def _check_approval(0 params) -> ?
  def _block(1 params) -> dict
  def run(1 params) -> ?

### P:/.claude/hooks/Stop_artifact_enforcement.py
  def _get_tool_use_log_path(1 params) -> Path
  def _read_tool_use_log(1 params) -> ?
  def _check_artifact_access(2 params) -> bool
  def _check_claim_keywords(1 params) -> ?
  def run(1 params) -> ?
  def _resolve_scope_ids(1 params) -> ?

### P:/.claude/hooks/Stop_behavior_gates.py
  def _are_gates_enabled(0 params) -> bool
  def _get_gates_mode(0 params) -> str
  def _load_project_blacklist(1 params) -> ?
  def _verify_telemetry_dirs(0 params) -> ?
  def _log_gate_violation(6 params) -> ?
  def _extract_tools_used(1 params) -> ?

### P:/.claude/hooks/Stop_cks_correction_anchor.py
  def _get_ingest(0 params) -> ?
  def _get_write_signal_client(0 params) -> ?
  def _send_write_signal(4 params) -> ?
  def run(1 params) -> ?

### P:/.claude/hooks/Stop_cks_decision_capture.py
  def _get_write_signal_client(0 params) -> ?
  def _send_write_signal_batch(2 params) -> ?
  def main(0 params) -> int
  def _allow(2 params) -> int

### P:/.claude/hooks/Stop_cleanup_verifier.py
  def run(1 params) -> ?
  def _load_tool_history(1 params) -> ?
  def detect_work_type(1 params) -> ?
  def check_cleanup_requirements(4 params) -> list

### P:/.claude/hooks/Stop_commit_gate.py
  def _terminal_id(0 params) -> str
  def _approval_file(0 params) -> Path
  def _check_commit_approval(0 params) -> ?
  def run(1 params) -> ?

### P:/.claude/hooks/Stop_comparative_claim_guard.py
  def _scope_mode(0 params) -> str
  def _scope_key(0 params) -> str
  def _ttl_seconds(0 params) -> ?
  def _extract_file(1 params) -> ?
  def _skill_aliases_for_path(1 params) -> ?
  def _add_verified_aliases(2 params) -> ?

### P:/.claude/hooks/Stop_contract_status.py
  def _load_events(1 params) -> ?
  def _load_log(1 params) -> ?
  def _age_hours(1 params) -> float
  def _green(1 params) -> str
  def _yellow(1 params) -> str
  def _red(1 params) -> str

### P:/.claude/hooks/Stop_deletion_verification_guard.py
  def _sanitize_for_log(1 params) -> str
  def _validate_path_boundary(2 params) -> bool
  def _extract_file_paths(1 params) -> ?
  def _normalize_path(1 params) -> Path
  def _check_path_with_timeout(1 params) -> ?
  def _verify_deletion_claim(1 params) -> ?

### P:/.claude/hooks/Stop_diagnostic_analysis_quality_gate.py
  def _is_enabled(0 params) -> bool
  def _gate_mode(0 params) -> str
  def _is_diagnostic_turn(1 params) -> bool
  def _check_competing_hypotheses(1 params) -> ?
  def _check_discriminating_test(1 params) -> ?
  def _check_baseline_comparison(1 params) -> ?

### P:/.claude/hooks/Stop_fake_done_detector.py
  def run_fake_done_detector(1 params) -> ?
  def on_load(0 params) -> ?

### P:/.claude/hooks/Stop_git_diff_reground.py
  def _state_path(1 params) -> Path
  def _load_warned(1 params) -> ?
  def _save_warned(2 params) -> ?
  def _make_relative(1 params) -> str
  def _parse_ts(1 params) -> float
  def load_tool_events(2 params) -> ?

### P:/.claude/hooks/Stop_lazy_workaround_gate.py
  def _check_duplicate_acceptance_proximity(1 params) -> ?
  def _has_investigation_intent(1 params) -> bool
  def _strip_quoted_blocks(1 params) -> str
  def check_lazy_workarounds(1 params) -> dict
  def main(0 params) -> ?

### P:/.claude/hooks/Stop_meta_analysis_trap.py
  def run_meta_analysis_trap(1 params) -> ?
  def on_load(0 params) -> ?

### P:/.claude/hooks/Stop_meta_conversation_loop.py
  def _get_state_dir(0 params) -> Path
  def _state_path(1 params) -> Path
  def _load_state(1 params) -> dict
  def _save_state(2 params) -> ?
  def _is_productive_turn(1 params) -> bool
  def _classify_turn(2 params) -> bool

### P:/.claude/hooks/stop_permission_stall.py
  def _get_state_dir(0 params) -> Path
  def _state_path(1 params) -> Path
  def _load_state(1 params) -> dict
  def _save_state(2 params) -> ?
  def _has_permission_seeking(1 params) -> bool
  def _has_authorization_signal(1 params) -> bool

### P:/.claude/hooks/Stop_proposal_decision_scanner.py
  def _extract_decision_claims(1 params) -> ?
  def _extract_rejections(1 params) -> ?
  def _normalize_option(1 params) -> str
  def _check_response_for_conflation(2 params) -> ?
  def check(1 params) -> ?
  def run(1 params) -> ?

### P:/.claude/hooks/Stop_ralph_loop.py
  def process_hook(2 params) -> ?

### P:/.claude/hooks/Stop_reasoning_quality_gate.py
  def _resolve_reasoning_package(0 params) -> ?
  def _resolve_log_path(1 params) -> Path
  def detect_overconfidence_without_evidence(1 params) -> ?
  def detect_workaround(1 params) -> ?
  def should_apply_reflection(1 params) -> ?
  def apply_self_reflection(1 params) -> ?

### P:/.claude/hooks/Stop_recommendation_gate.py
  def _has_option_list(1 params) -> bool
  def _has_delegation(1 params) -> bool
  def _has_recommendation(1 params) -> bool
  def _safe_id(1 params) -> str
  def _resolve_session_id(1 params) -> str
  def _resolve_terminal_id(1 params) -> str

### P:/.claude/hooks/Stop_reflect_integration.py
  def _get_suggestion_path(0 params) -> Path
  def _get_lock_path(0 params) -> Path
  def _acquire_lock(1 params) -> bool
  def _release_lock(0 params) -> ?
  def _log(1 params) -> ?
  def _merge_signals(2 params) -> dict

### P:/.claude/hooks/Stop_repetition_blocker.py
  def run_repetition_blocker(1 params) -> ?
  def on_load(0 params) -> ?

### P:/.claude/hooks/Stop_safety_gate.py
  def check_secrets(1 params) -> ?
  def check_forbidden(1 params) -> ?
  def check_protocol(2 params) -> ?
  def check_catch_block_hygiene(1 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/Stop_self_reflection_gate.py
  def _response_has_evidence(1 params) -> bool
  def _extract_unsupported_claims(2 params) -> ?
  def _find_contradictions(1 params) -> ?
  def _find_incomplete_promises(1 params) -> ?
  def _normalize(1 params) -> str
  def _is_from_doc_block(2 params) -> bool

### P:/.claude/hooks/Stop_semantic_critic.py
  class SemanticCriticResult (0 methods)
  def _session_key(1 params) -> str
  def _build_critic_user_message(2 params) -> str
  def _detect_critic_profile(2 params) -> str
  def _build_remediation_message(2 params) -> str
  def parse_semantic_critic_response(1 params) -> ?

### P:/.claude/hooks/Stop_skill_dir_correlation_gate.py
  def _is_enabled(0 params) -> bool
  def _extract_content_text(1 params) -> str
  def _get_user_skill_from_conversation(1 params) -> ?
  def _extract_accessed_skills(1 params) -> ?
  def run(1 params) -> ?

### P:/.claude/hooks/Stop_skill_question_marker.py
  def _get_marker_path(2 params) -> Path
  def _load_json(1 params) -> dict
  def _save_json(2 params) -> ?
  def run(1 params) -> ?

### P:/.claude/hooks/Stop_subagent_opportunity.py
  def _safe_id(1 params) -> str
  def _get_terminal_id(1 params) -> str
  def _get_session_id(1 params) -> str
  def _load_session_opportunities(2 params) -> dict
  def _save_session_opportunities(3 params) -> ?
  def _log_opportunity_event(4 params) -> ?

### P:/.claude/hooks/Stop_task_completion_gate.py
  def _get_task_state_path(1 params) -> ?
  def _load_task_data(1 params) -> ?
  def _is_task_completion(1 params) -> ?
  def check(1 params) -> ?
  def run(1 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/Stop_tilldone_gate.py
  def _find_plan_file(0 params) -> ?
  def _count_plan_tasks(1 params) -> ?
  def _check_false_completion(3 params) -> int
  def _is_exempt(1 params) -> bool
  def _has_valid_done_claim(2 params) -> bool
  def _has_premature_stop_phrase(1 params) -> ?

### P:/.claude/hooks/StopHook_cited_content_guard.py
  def _is_enabled(0 params) -> bool
  def _get_mode(0 params) -> str
  def _extract_identifiers(1 params) -> ?
  def _extract_following_code(2 params) -> str
  def _load_read_events(2 params) -> ?
  def _find_read_events_for_basename(2 params) -> ?

### P:/.claude/hooks/StopHook_commitment_tracker.py
  def run(1 params) -> dict
  def _extract_terminal_id(1 params) -> str
  def _extract_session_id(1 params) -> str
  def _extract_transcript(1 params) -> ?

### P:/.claude/hooks/StopHook_correction_acknowledgment.py
  def run(1 params) -> ?

### P:/.claude/hooks/StopHook_cross_validator.py
  def load_tool_events(2 params) -> ?
  def verify_document_claim(1 params) -> ?
  def verify_action_claim(1 params) -> ?
  def verify_error_characterization(1 params) -> ?
  def run(1 params) -> ?

### P:/.claude/hooks/StopHook_drift_sentinel.py
  def load_tool_events(2 params) -> ?
  def _load_source_texts(1 params) -> ?
  def _should_run_drift_check(2 params) -> bool
  def _detect_drift(2 params) -> ?
  def run(1 params) -> ?

### P:/.claude/hooks/StopHook_perf_attribution_gate.py
  def _detect_perf_claims(1 params) -> bool
  def _timing_code_was_read(1 params) -> bool
  def _parse_payload(0 params) -> ?
  def _get_response_text(1 params) -> str
  def _get_stop_hook_active(1 params) -> bool
  def run(1 params) -> ?

### P:/.claude/hooks/StopHook_rca_contract.py
  class BandAidState (0 methods)
  def _get_logger(0 params) -> ?
  def _get_current_turn_tools(1 params) -> ?
  def _load_turn_scoped_tool_events(2 params) -> ?
  def _has_verification_this_turn(1 params) -> bool
  def _contains_transcript_only_claim(1 params) -> bool

### P:/.claude/hooks/StopHook_rca_reflector.py
  def _get_state_file(2 params) -> Path
  def _load_state(2 params) -> dict
  def _save_state(3 params) -> ?
  def _cleanup_stale_state_files(0 params) -> ?
  def _detect_premature_convergence(2 params) -> ?
  def _is_catch22_spiral(3 params) -> bool

### P:/.claude/hooks/StopHook_sequential_thinking.py
  def _resolve_phase_key(3 params) -> str
  def _extract_hypotheses_from_response(1 params) -> list
  def _format_investigation_feedback(2 params) -> str
  def _strip_seq_blocks(1 params) -> str
  def stop(1 params) -> dict
  def _find_active_session(1 params) -> ?

### P:/.claude/hooks/StopHook_step_header_verifier.py
  def _find_skill_file(1 params) -> ?
  def _parse_workflow_steps(1 params) -> ?
  def _extract_skill_name(1 params) -> ?
  def _normalize_step_name(1 params) -> str
  def _verify_step_headers(2 params) -> ?
  def run(1 params) -> dict

### P:/.claude/hooks/StopHook_tdd_continuation.py
  def _get_state_file(0 params) -> Path
  def read_state(0 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/StopHook_unverified_stance.py
  def _get_gate_enabled(0 params) -> bool
  def _get_gate_mode(0 params) -> str
  def load_tool_events_for_context(0 params) -> ?
  def load_tool_events(2 params) -> ?
  def _should_block_claim(3 params) -> bool
  def _is_control_turn(1 params) -> bool

### P:/.claude/hooks/tdd/cold_code_review_dispatch.py
  class ColdReviewResult (0 methods)
  def should_dispatch_review(3 params) -> bool
  def build_review_context(3 params) -> ?
  def build_blinded_prompt(2 params) -> str
  def extract_findings_from_result(1 params) -> ColdReviewResult
  def dispatch_cold_code_review(4 params) -> ColdReviewResult

### P:/.claude/hooks/tdd/contract_cleanup.py
  class CleanupResult (0 methods)
  def get_completed_contracts(2 params) -> ?
  def cleanup_completed_contract(3 params) -> ?
  def cleanup_all_completed_contracts(3 params) -> ?
  def get_cleanup_stats(1 params) -> ?

### P:/.claude/hooks/tdd/enforcement_tiers.py
  class EnforcementTier (0 methods)
  class TierConfig (0 methods)
  class EnforcementTierManager (7 methods)
  def get_enforcement_tier(1 params) -> EnforcementTier
  def should_enforce(1 params) -> bool
  def __init__(3 params) -> ?

### P:/.claude/hooks/tdd/gto_assertions.py
  class AssertionResult (0 methods)
  class GTOAssertionRunner (8 methods)
  def __init__(2 params) -> ?
  def run_assertion(2 params) -> AssertionResult
  def _check_file_exists(2 params) -> AssertionResult
  def _check_test_passes(2 params) -> AssertionResult

### P:/.claude/hooks/tdd/phase_transition_logger.py
  class PhaseTransition (0 methods)
  def compute_evidence_hash(3 params) -> str
  def log_phase_transition(8 params) -> PhaseTransition
  def _write_evidence_file(4 params) -> ?
  def get_transition_history(2 params) -> ?
  def validate_transition_sequence(1 params) -> ?

### P:/.claude/hooks/tdd/ralph_loop_engine.py
  class ContractState (2 methods)
  class RalphLoopStateData (2 methods)
  class RalphLoopEngine (13 methods)
  def to_dict(1 params) -> dict
  def from_dict(2 params) -> ContractState
  def to_dict(1 params) -> dict

### P:/.claude/hooks/tdd/tdd_phase_state.py
  class TDDPhaseState (4 methods)
  class FilePhaseState (2 methods)
  class TDDPhaseStateData (2 methods)
  class TDDPhaseStateManager (13 methods)
  def compute_file_hash(1 params) -> str
  def verify_file_hash(2 params) -> bool

### P:/.claude/hooks/tdd/three_file_contract.py
  def _compute_file_hash(1 params) -> ?
  class ThreeFileContract (5 methods)
  def __post_init__(1 params) -> ?
  def _safe_hash_compare(3 params) -> bool
  def verify_immutability(1 params) -> bool
  def to_dict(1 params) -> dict

### P:/.claude/hooks/tdd95_core.py
  def canonicalize_path(1 params) -> Path
  def path_to_posix(1 params) -> str
  def path_from_posix(1 params) -> Path
  def path_matches_tier(2 params) -> bool
  def load_config(0 params) -> dict
  def in_maintenance_mode(0 params) -> bool

### P:/.claude/hooks/tdd_core.py
  def _lock_file_lockfile(2 params) -> ?
  def debug_log(1 params) -> ?
  def is_tdd_enabled(0 params) -> bool
  def normalize_path(1 params) -> str
  def find_project_root(1 params) -> ?
  def find_test_file(1 params) -> ?

### P:/.claude/hooks/tdd_diagnostics.py
  class TDDDiagnostics (6 methods)
  def run_diagnostics(0 params) -> dict
  def main(0 params) -> ?
  def __init__(1 params) -> ?
  def log_event(3 params) -> ?
  def check_block_then_implement(2 params) -> bool

### P:/.claude/hooks/telemetry/verification_metrics.py
  def sanitize_metric_entry(1 params) -> ?
  class VerificationMetrics (2 methods)
  def collect_verification_metric(5 params) -> ?
  def get_metrics_summary(1 params) -> ?
  def _set_secure_permissions(1 params) -> ?
  def __init__(2 params) -> ?

### P:/.claude/hooks/tests/analyze_hook_environment.py
  def analyze_hooks(0 params) -> ?

### P:/.claude/hooks/tests/benchmark_evidence_validation.py
  class TestHashComputationPerformance (4 methods)
  class TestValidationThroughput (3 methods)
  class TestCacheHitRate (2 methods)
  class TestCachePerformance (2 methods)
  def test_hash_uncached_performance(3 params) -> ?
  def test_hash_cached_performance(3 params) -> ?

### P:/.claude/hooks/tests/demo_load_tool_events_for_context.py
  def main(0 params) -> ?

### P:/.claude/hooks/tests/demo_verification_visualization.py
  def demo_unverified_stance(0 params) -> ?
  def demo_integration_warning(0 params) -> ?
  def demo_observable_effect_warning(0 params) -> ?
  def demo_completion_claim(0 params) -> ?
  def demo_verified_claim(0 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/tests/fixtures/evidence_store_fixture.py
  def temp_evidence_db(1 params) -> ?
  def synthetic_session_context(0 params) -> ?
  def synthetic_bash_result(0 params) -> ?
  def synthetic_skill_invocation_result(0 params) -> ?
  def empty_evidence_db(1 params) -> ?

### P:/.claude/hooks/tests/got_tot_baseline/performance_benchmark.py
  class PerformanceBenchmark (5 methods)
  def main(0 params) -> ?
  def __init__(2 params) -> ?
  def run_pytest_with_timing(2 params) -> ?
  def benchmark_all_skills(1 params) -> ?
  def save_baseline(2 params) -> Path

### P:/.claude/hooks/tests/got_tot_baseline/python_version_validator.py
  class FeatureUsage (0 methods)
  class PythonVersionValidator (8 methods)
  def main(0 params) -> ?
  def __init__(2 params) -> ?
  def get_minimum_python_version(1 params) -> str
  def scan_file_for_features(2 params) -> ?

### P:/.claude/hooks/tests/validate_authorization_gate.py
  def run_hook(1 params) -> dict
  def test_case(3 params) -> bool
  def make_input(2 params) -> dict
  def main(0 params) -> ?

### P:/.claude/hooks/tests/validate_vague_directive.py
  def test_case(3 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/tool_availability_checker.py
  def _get_tool_name(1 params) -> str
  def _get_skill_name_from_params(1 params) -> ?
  def _get_bash_command_from_params(1 params) -> ?
  def _check_skill_available(1 params) -> ?
  def _check_bash_command_available(1 params) -> ?
  def _check_mcp_server_available(1 params) -> ?

### P:/.claude/hooks/tool_sequence_manager.py
  class FileLock (5 methods)
  class ToolSequenceManager (7 methods)
  def load_tool_sequence(0 params) -> ?
  def load_tool_sequence_filtered(3 params) -> ?
  def get_recent_tool_sequence(1 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/tools/contract-telemetry-queries.py
  def _load_log(1 params) -> ?
  def _age_hours(1 params) -> float
  def _fmt_age(1 params) -> str
  def _green(1 params) -> str
  def _yellow(1 params) -> str
  def _red(1 params) -> str

### P:/.claude/hooks/turn_scoped_evidence.py
  def load_turn_scoped_events(0 params) -> ?

### P:/.claude/hooks/unified_claim_verifier.py
  def _is_plausible_claim_line(1 params) -> bool
  def _segments(1 params) -> ?
  def _find_suspicious_existence_sentences(1 params) -> ?
  def _event_matches_target(3 params) -> bool
  def _resource_was_fetched(2 params) -> bool
  def _has_external_resource(1 params) -> bool

### P:/.claude/hooks/UserPromptSubmit.py
  def _safe_id(1 params) -> str
  def _get_challenge_marker_paths(1 params) -> ?
  def _marker_matches_scope(2 params) -> bool
  def _normalize_context_block(1 params) -> str
  def _dict_context_blocks(1 params) -> ?
  def _split_visible_tag_header(1 params) -> ?

### P:/.claude/hooks/UserPromptSubmit_approval.py
  def _approval_file(0 params) -> Path
  def _register_hooks(0 params) -> ?
  def process_prompt(1 params) -> ?

### P:/.claude/hooks/UserPromptSubmit_claim_classifier.py
  def _safe_id(1 params) -> str
  def _get_claim_type_path(1 params) -> Path
  def _run(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_cognitive_tags.py
  def _is_non_substantive_turn(1 params) -> bool
  def cognitive_tags(1 params) -> HookResult
  def get_active_tags_for_prompt(1 params) -> ?
  def format_tags_for_instruction(1 params) -> str

### P:/.claude/hooks/UserPromptSubmit_discovery_block.py
  def get_session_id(1 params) -> ?
  def is_discovery_tool(1 params) -> ?
  def check_discovery_state(1 params) -> ?
  def extract_topic_from_prompt(1 params) -> ?
  def main(1 params) -> ?

### P:/.claude/hooks/UserPromptSubmit_modules/abstraction_clarity_gate.py
  def _is_ambiguous_question(1 params) -> bool
  def process_prompt(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/analysis_protocol_gate.py
  def _load_config(0 params) -> dict
  def _extract_skill_name(1 params) -> ?
  def _is_actionable_prompt(2 params) -> bool
  def _tokenize_lower(1 params) -> ?
  def _concept_cluster_match(1 params) -> bool
  def cosine_similarity(2 params) -> float

### P:/.claude/hooks/UserPromptSubmit_modules/anti_sycophancy_injector.py
  def _is_enabled(0 params) -> bool
  def _safe_id(1 params) -> str
  def _resolve_scope(1 params) -> ?
  def _state_dirs(0 params) -> ?
  def _state_file_candidates(2 params) -> ?
  def _load_state(1 params) -> dict

### P:/.claude/hooks/UserPromptSubmit_modules/base.py
  class HookResult (5 methods)
  class HookContext (0 methods)
  def __init__(5 params) -> ?
  def is_empty(1 params) -> bool
  def empty(1 params) -> HookResult
  def __eq__(2 params) -> bool

### P:/.claude/hooks/UserPromptSubmit_modules/behavior_contract.py
  def _read_contract(0 params) -> str
  def build_behavior_contract(0 params) -> str
  def append_behavior_contract(1 params) -> str
  def contract_clauses(0 params) -> ?
  def _should_inject(1 params) -> bool
  def _is_enabled(0 params) -> bool

### P:/.claude/hooks/UserPromptSubmit_modules/breadcrumb_init.py
  def breadcrumb_init_hook(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/cks_context.py
  def _should_inject_recent_corrections(1 params) -> bool
  def _query_semantic_corrections(3 params) -> ?
  def _query_recent_corrections(3 params) -> ?
  def _query_hybrid_corrections(3 params) -> ?
  def _query_knowledge_base(2 params) -> ?
  def _format_knowledge_context(2 params) -> str

### P:/.claude/hooks/UserPromptSubmit_modules/claim_risk_router.py
  def _should_fire(1 params) -> bool
  def _build_injection(1 params) -> str
  def claim_risk_router(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/coach_note_reader.py
  def _load_config(0 params) -> dict
  def coach_note_reader(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/cognitive_enhancers.py
  class Enhancer (0 methods)
  def _load_config(0 params) -> dict
  def _validate_config(1 params) -> ?
  def _extract_skill_name(1 params) -> ?
  def _is_actionable_prompt(2 params) -> bool
  def _detect_intent(1 params) -> ?

### P:/.claude/hooks/UserPromptSubmit_modules/cognitive_guardrails.py
  def cognitive_guardrails(1 params) -> HookResult
  def process_prompt(1 params) -> ?

### P:/.claude/hooks/UserPromptSubmit_modules/competence_injector.py
  def _detect_task_type_from_prompt(1 params) -> ?
  def _detect_context_signals(2 params) -> ?
  def is_trivial_prompt(2 params) -> bool
  def get_user_skill_name(1 params) -> ?
  def _write_detected_task_type(2 params) -> ?
  def process_skill_load(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/config_loader.py
  class CognitiveFrameworkConfig (0 methods)
  class ReasoningModeConfig (0 methods)
  class ThinkProfileConfig (0 methods)
  class CognitiveReasoningConfig (6 methods)
  def load_config(1 params) -> CognitiveReasoningConfig
  def get_config(0 params) -> CognitiveReasoningConfig

### P:/.claude/hooks/UserPromptSubmit_modules/conflict_arbiter.py
  class ArbiterResult (0 methods)
  def resolve_conflict(5 params) -> ArbiterResult

### P:/.claude/hooks/UserPromptSubmit_modules/consultation_awareness.py
  def _get_state_file(2 params) -> Path
  def _load_state(2 params) -> dict
  def _save_state(3 params) -> ?
  def _is_directive(1 params) -> bool
  def _is_question_response(1 params) -> bool
  def _near_match(2 params) -> bool

### P:/.claude/hooks/UserPromptSubmit_modules/context_followup_detector.py
  def _get_terminal_id(1 params) -> str
  def _normalize_terminal_id(1 params) -> str
  def _get_state_file_path(1 params) -> Path
  def _load_prior_context(1 params) -> ?
  def _save_prior_context(2 params) -> ?
  def _is_followup_query(2 params) -> ?

### P:/.claude/hooks/UserPromptSubmit_modules/context_summary.py
  def _should_trigger(1 params) -> bool
  def _read_transcript(2 params) -> ?
  def _extract_key_facts(1 params) -> ?
  def _format_summary(1 params) -> str
  def context_summary_hook(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/continuation_spine.py
  def is_short_affirmative(1 params) -> bool
  def get_last_assistant_message(1 params) -> ?
  def is_concrete_proposal(1 params) -> bool
  def continuation_spine(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/convert_to_absolute_imports.py
  def convert_relative_imports(1 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/UserPromptSubmit_modules/declaration_reminder.py
  def _get_terminal_id(1 params) -> str
  def _get_state_file(1 params) -> Path
  def _extract_arch_path(1 params) -> ?
  def _store_declaration_state(2 params) -> ?
  def _detect_template_declaration(1 params) -> bool
  def declaration_reminder_hook(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/delegation_prospector.py
  def _get_terminal_id(0 params) -> str
  def _get_state_dir(0 params) -> Path
  def _redact_sensitive(1 params) -> str
  def _extract_skill_name(1 params) -> ?
  def _detect_delegation_opportunity(1 params) -> ?
  def _get_terminal_id_from_context(1 params) -> str

### P:/.claude/hooks/UserPromptSubmit_modules/diagnostic_guard.py
  def detect_speculative_claim(1 params) -> bool
  def count_confidence_words(1 params) -> int
  def check_high_confidence_without_evidence(2 params) -> bool
  def build_speculative_claim_warning(0 params) -> str
  def run_diagnostic_guard(1 params) -> ?
  def estimate_tokens(1 params) -> int

### P:/.claude/hooks/UserPromptSubmit_modules/discovery_block.py
  def get_session_id(1 params) -> ?
  def is_discovery_tool(1 params) -> ?
  def check_discovery_state(1 params) -> ?
  def extract_topic_from_prompt(1 params) -> ?
  def process_prompt(1 params) -> ?
  def discovery_block_hook(1 params) -> ?

### P:/.claude/hooks/UserPromptSubmit_modules/edit_consent.py
  def _create_hook_dev_session(2 params) -> ?
  def _end_hook_dev_session(2 params) -> ?
  def run_edit_consent(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/error_investigation_gate.py
  def _get_session_flag_path(1 params) -> Path
  def _session_has_injection(1 params) -> bool
  def _mark_session_injected(1 params) -> ?
  def _is_error_inquiry(1 params) -> bool
  def error_investigation_gate(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/evidence_grounding_reminder.py
  def _get_counter(1 params) -> int
  def _inc_counter(1 params) -> int
  def _advance(1 params) -> int
  def evidence_grounding_reminder(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/failure_context_injector.py
  def _tail_lines(2 params) -> str
  def failure_context_injector(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/file_immediate_read.py
  def _extract_paths(1 params) -> ?
  def _readable_files_in_dir(2 params) -> ?
  def _is_readable_file(1 params) -> bool
  def _expand_path(1 params) -> ?
  def file_immediate_read(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/frameguard_classifier.py
  def frameguard_classifier(1 params) -> HookResult
  def process_prompt(1 params) -> ?
  def frameguard_triggers_inc(0 params) -> ?

### P:/.claude/hooks/UserPromptSubmit_modules/handoff_context_injector.py
  def _extract_terminal_id(1 params) -> ?
  def load_handoff_envelope(1 params) -> ?
  def build_injection_message(1 params) -> str
  def handoff_context_injector_hook(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/intent_classifier.py
  def is_topic_inquiry(1 params) -> bool
  def intent_classifier_hook(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/intent_extractor.py
  def _get_session_id(1 params) -> str
  def parse_work_intent(1 params) -> dict
  def extract_target(1 params) -> str
  def extract_problem(1 params) -> str
  def save_intent_state(2 params) -> ?
  def intent_extractor_hook(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/judge_first_query_advisory.py
  def _process_prompt_impl(1 params) -> HookResult
  def _estimate_tokens(1 params) -> int
  def load_recent_judge_verdicts(1 params) -> ?
  def summarize_judge_activity(1 params) -> ?
  def should_inject_first_query_advisory(2 params) -> ?
  def build_first_query_advisory(1 params) -> ?

### P:/.claude/hooks/UserPromptSubmit_modules/language_lock.py
  def _is_enabled(0 params) -> bool
  def _get_interval(0 params) -> int
  def _artifacts_dir(1 params) -> Path
  def _counter_path(1 params) -> Path
  def _increment_and_check(2 params) -> bool
  def language_lock(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/memory_size.py
  def check_memory_size(0 params) -> ?
  def memory_size_hook(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/migrations/add_performance_indexes.py
  def migrate(1 params) -> ?
  def verify_indexes(1 params) -> ?

### P:/.claude/hooks/UserPromptSubmit_modules/observability.py
  class CognitiveSelectionEvent (0 methods)
  class ReasoningModeEvent (0 methods)
  class TagEmissionEvent (0 methods)
  def log_cognitive_selection(4 params) -> ?
  def log_reasoning_mode(4 params) -> ?
  def log_tag_emission(6 params) -> ?

### P:/.claude/hooks/UserPromptSubmit_modules/operating_rules.py
  def _should_fire(1 params) -> bool
  def _is_enabled(0 params) -> bool
  def operating_rules(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/ownership_colocation_nudge.py
  def _has_placement_intent(1 params) -> bool
  def ownership_colocation_nudge_hook(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/path_syntax_corrector.py
  def fix_windows_path(1 params) -> str
  def path_syntax_corrector(1 params) -> HookResult
  def _calculate_confidence(1 params) -> int
  def _detect_and_offer_correction(2 params) -> HookResult
  def _handle_choice_response(2 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/performance_monitor.py
  def get_thresholds(0 params) -> ?
  def _get_perf_connection(0 params) -> ?
  def _init_perf_schema(0 params) -> ?
  def _get_session_id(0 params) -> str
  def _get_terminal_id(0 params) -> str
  def log_detection_performance(2 params) -> ?

### P:/.claude/hooks/UserPromptSubmit_modules/plan_injector.py
  def extract_explicit_plan_path(1 params) -> ?
  def detect_plan_command(1 params) -> bool
  def references_implicit_execution_plan(1 params) -> bool
  def detect_plan_reference(1 params) -> bool
  def get_disambiguation_question(1 params) -> ?
  def extract_plan_name(1 params) -> str

### P:/.claude/hooks/UserPromptSubmit_modules/plan_mode_schema.py
  def plan_mode_schema(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/questioning_integration.py
  class QuestioningPattern (0 methods)
  class DebuggingHeuristic (0 methods)
  class QuestioningMatch (0 methods)
  def detect_questioning_patterns(1 params) -> QuestioningMatch
  def get_pattern_context(1 params) -> ?
  def get_debugging_guidance(1 params) -> ?

### P:/.claude/hooks/UserPromptSubmit_modules/rca_schema_injector.py
  def _is_rca_intent(1 params) -> bool
  def _load_schema_template(0 params) -> str
  def rca_schema_injector_hook(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/reasoning_contract.py
  def _contract_lines(0 params) -> ?
  def build_reasoning_contract(0 params) -> str
  def append_reasoning_contract(1 params) -> str
  def contract_clauses(0 params) -> ?
  def mark_reasoning_contract_applied(2 params) -> ?
  def reasoning_contract_already_applied(1 params) -> bool

### P:/.claude/hooks/UserPromptSubmit_modules/reasoning_mode_selector.py
  def _map_unified_result_to_legacy_format(1 params) -> ?
  def reasoning_mode_selector(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/referent_anchor.py
  def _extract_table_rows(1 params) -> ?
  def _extract_bullet_items(1 params) -> ?
  def _normalize_term(1 params) -> str
  def _has_referential_language(1 params) -> bool
  def _has_expansion_language(1 params) -> bool
  def _has_investigative_verb(1 params) -> bool

### P:/.claude/hooks/UserPromptSubmit_modules/registry.py
  def _extract_model_from_transcript(1 params) -> ?
  def _rotate_hook_error_log(0 params) -> ?
  def _log_execution_trace(8 params) -> ?
  def _log_final_results(4 params) -> ?
  def register_hook(2 params) -> ?
  def register_hook_function(3 params) -> ?

### P:/.claude/hooks/UserPromptSubmit_modules/sequential_thinking.py
  def _find_hooks_dir(0 params) -> Path
  def _should_trigger_semantic(1 params) -> ?
  def _extract_trigger_phrase(2 params) -> str
  def _matches_negative_pattern(1 params) -> bool
  def _has_technical_depth(1 params) -> bool
  def _create_sequential_state(4 params) -> ?

### P:/.claude/hooks/UserPromptSubmit_modules/sequential_thinking_semantic_client.py
  def _get_daemon_client(0 params) -> DaemonClient
  def _get_trigger_embeddings(0 params) -> ?
  def _compute_embedding_via_daemon(1 params) -> ?
  def _compute_embedding_direct(1 params) -> ?
  def _compute_trigger_embeddings_direct(0 params) -> ?
  def _cosine_similarity(2 params) -> float

### P:/.claude/hooks/UserPromptSubmit_modules/skill_compliance_indicator.py
  def _extract_skill_name(1 params) -> ?
  def _read_skill_frontmatter(1 params) -> dict
  def _get_breadcrumb_trail(1 params) -> dict
  def _get_historical_completion_rate(2 params) -> ?
  def _format_compliance_indicator(4 params) -> str
  def skill_compliance_indicator_hook(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/skill_context_writer.py
  def _safe_id(1 params) -> str
  def _skill_context_path(1 params) -> Path
  def _extract_skill_from_prompt(1 params) -> ?
  def _write_atomic(2 params) -> ?
  def _delete_if_exists(1 params) -> ?
  def skill_context_writer(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/subagent_enforcer.py
  def _detect_subagent_context(1 params) -> bool
  def _get_terminal_id(1 params) -> str
  def _get_session_id(1 params) -> str
  def _log_subagent_event(4 params) -> ?
  def subagent_enforcer_hook(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/synergy_detector.py
  class SynergyRule (0 methods)
  class SynergyMatch (0 methods)
  def detect_synergies(2 params) -> SynergyMatch
  def synergy_detector_hook(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/tag_emission.py
  class Tag (2 methods)
  class TagCollection (3 methods)
  def validate_tag(1 params) -> bool
  def emit_tag(3 params) -> str
  def emit_tags(2 params) -> str
  def emit_detection_tags(6 params) -> str

### P:/.claude/hooks/UserPromptSubmit_modules/tag_registry.py
  class TagDefinition (0 methods)
  def get_tag_definition(1 params) -> ?
  def validate_tag(1 params) -> bool
  def validate_tag_emission(2 params) -> ?
  def get_all_framework_tags(0 params) -> ?
  def get_framework_tags_for_enhancer(1 params) -> ?

### P:/.claude/hooks/UserPromptSubmit_modules/task_detector.py
  def _get_contract_state(0 params) -> ?
  def is_substantive_task(1 params) -> bool
  def should_clear_contract(1 params) -> bool
  def detect_task_pivot(2 params) -> bool
  def process_prompt(1 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/UserPromptSubmit_modules/task_start_contract_writer.py
  def _get_telemetry_log_path(0 params) -> ?
  def _log_telemetry(3 params) -> ?
  class TaskType (0 methods)
  def _classify_task_type(1 params) -> TaskType
  def _detect_task_class(1 params) -> ?
  def _compute_task_id(1 params) -> str

### P:/.claude/hooks/UserPromptSubmit_modules/tdd_contract_auto_gate.py
  def _is_tdd_bypassed(1 params) -> bool
  def _extract_target_file(2 params) -> ?
  def _get_tdd_manager(1 params) -> ?
  def tdd_contract_auto_gate(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/think_trigger.py
  class ThinkProfile (0 methods)
  def _stem(2 params) -> str
  def _is_self_referential_prompt(1 params) -> bool
  def _is_meta_think_prompt(1 params) -> bool
  def _detect_profile(1 params) -> ?
  def _parse_think(1 params) -> ?

### P:/.claude/hooks/UserPromptSubmit_modules/truthfulness_gate.py
  def detect_completion_query(1 params) -> bool
  def truthfulness_gate(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/turn_marker.py
  def write_turn_marker(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/unified_detection.py
  class UnifiedDetectionResult (0 methods)
  def ensure_unified_detection_result(1 params) -> UnifiedDetectionResult
  def _stem(2 params) -> str
  def _classify_intent(1 params) -> ?
  def _detect_synergies(2 params) -> ?
  def detect_prompt(1 params) -> UnifiedDetectionResult

### P:/.claude/hooks/UserPromptSubmit_modules/unified_injector.py
  def _strip_quoted_text(1 params) -> str
  def detect_command(1 params) -> ?
  def extract_command_name(1 params) -> ?
  def build_command_injection(2 params) -> str
  def extract_goal(1 params) -> ?
  def build_goal_injection(1 params) -> str

### P:/.claude/hooks/UserPromptSubmit_modules/verify_before_claim.py
  def _safe_id(1 params) -> str
  def _cooldown_path(2 params) -> Path
  def _is_on_cooldown(2 params) -> bool
  def _record_fired(2 params) -> ?
  def _matches_existence_query(1 params) -> bool
  def verify_before_claim(1 params) -> HookResult

### P:/.claude/hooks/UserPromptSubmit_modules/workflow_tier_tagging.py
  def _find_skill_file(1 params) -> ?
  def _parse_workflow_steps(1 params) -> ?
  def _generate_tier_directive(2 params) -> str
  def workflow_tier_tagging_hook(1 params) -> HookResult

### P:/.claude/hooks/utils/correction_ranker.py
  class ScoredCorrection (0 methods)
  def score_correction(5 params) -> ScoredCorrection
  def rank_corrections(6 params) -> ?
  def rank_corrections_with_scores(6 params) -> ?

### P:/.claude/hooks/utils/question_extractor.py
  class PendingQuestion (1 methods)
  def extract_text_from_message(1 params) -> str
  def is_substantive_answer(1 params) -> bool
  def has_context_pronoun(1 params) -> bool
  def extract_pending_questions(2 params) -> ?
  def to_dict(1 params) -> ?

### P:/.claude/hooks/utils/reminder_state.py
  def _find_memory_md(0 params) -> Path
  def artifacts_dir(1 params) -> Path
  def read_compaction_state(1 params) -> ?
  def write_compaction_state(3 params) -> bool
  def _write_with_retry(3 params) -> ?
  def score_as_correction_heuristic(1 params) -> ?

### P:/.claude/hooks/validators/anti_lazy_verification.py
  class AntiLazyVerification (2 methods)
  def verify_system_claim(3 params) -> dict
  def block_lazy_analysis(1 params) -> bool

### P:/.claude/hooks/validators/arch_v2_validator.py
  def validate_arch_output(1 params) -> ?

### P:/.claude/hooks/validators/core_validator.py
  class ValidationResult (1 methods)
  class CoreValidator (6 methods)
  def validate_file(2 params) -> int
  def __init__(6 params) -> ?
  def __init__(2 params) -> ?
  def _load_config(1 params) -> ?

### P:/.claude/hooks/validators/data_processor_v2_validator.py
  def validate_json(1 params) -> ?
  def validate_yaml(1 params) -> ?
  def validate_csv(1 params) -> ?
  def main(0 params) -> ?

### P:/.claude/hooks/validators/evidence_integrator.py
  class TDDEvidenceIntegrator (6 methods)
  def __init__(1 params) -> ?
  def _ensure_evidence_db(1 params) -> ?
  def store_tdd_evidence(7 params) -> str
  def _generate_evidence_id(3 params) -> str
  def _get_file_size(2 params) -> int

### P:/.claude/hooks/validators/rbw_validator.py
  class ReadBeforeWriteValidator (9 methods)
  def __init__(1 params) -> ?
  def validate_read_before_write(4 params) -> ?
  def _is_code_file(2 params) -> bool
  def _detect_anti_patterns(2 params) -> ?
  def _detect_trial_and_error(2 params) -> ?

### P:/.claude/hooks/validators/rca_v2_validator.py
  def _extract_response_from_stdin(0 params) -> str
  def _detect_strict_flag(1 params) -> bool

### P:/.claude/hooks/validators/tdd_validator.py
  class EnforcementTier (0 methods)
  class FileCategory (0 methods)
  class TDDViolationType (0 methods)
  class TDDEnforcementAction (0 methods)
  class TDDValidationResult (1 methods)
  class TestFileValidator (16 methods)

### P:/.claude/hooks/variable_naming.py
  def extract_variable_names(1 params) -> ?
  def compute_confusability_score(2 params) -> float
  def detect_confusable_names(2 params) -> VariableList
  def suggest_better_names(1 params) -> ?
  def check_variable_naming(4 params) -> CheckResult

### P:/.claude/hooks/variable_semantics.py
  class VariableSemanticsChecker (4 methods)
  def get_variable_semantics_checker(1 params) -> VariableSemanticsChecker
  def _find_project_root_for_file(1 params) -> Path
  def check_variable_semantics(4 params) -> CheckResult
  def __init__(2 params) -> ?
  def load_yaml_contracts(1 params) -> ?

### P:/.claude/hooks/verification/claims.py
  def _strip_ascii_art(1 params) -> str
  class Claim (0 methods)
  def _detect_outcome_attribution_claims(1 params) -> ?
  def _detect_folder_create_claims(1 params) -> ?
  def _split_sentences(1 params) -> ?
  def extract_claims(1 params) -> ?

### P:/.claude/hooks/verification/coverage.py
  class CoverageDimension (0 methods)
  class CoverageReport (0 methods)
  def assess_coverage(4 params) -> CoverageReport
  def _check_peer_coverage(3 params) -> CoverageDimension
  def _check_direct_vs_indirect(2 params) -> CoverageDimension
  def _check_staleness(2 params) -> CoverageDimension

### P:/.claude/hooks/verification/decomposition.py
  class SubClaim (0 methods)
  class DecompositionResult (0 methods)
  def should_decompose(2 params) -> bool
  def decompose_claim(1 params) -> DecompositionResult
  def _status_value(1 params) -> str
  def _split_conjunctions(1 params) -> ?

### P:/.claude/hooks/verification/engine.py
  class VerificationStatus (0 methods)
  class VerificationVerdict (0 methods)
  class ToolEventView (0 methods)
  def build_verdicts(2 params) -> ?
  def match_claim_to_events(2 params) -> VerificationStatus
  def _verify_rule_claim(2 params) -> VerificationStatus

### P:/.claude/hooks/verification/hook_adapter.py
  class ClaimMatch (0 methods)
  def create_claim_from_match(2 params) -> Claim
  def verify_claim_with_engine(2 params) -> VerificationStatus
  def verify_claims_batch(2 params) -> ?
  def load_turn_scoped_events(3 params) -> ?
  def check_verification_status(5 params) -> VerificationStatus

### P:/.claude/hooks/verification/recommendation_rubric.py
  class RecommendationAssessment (0 methods)
  def assess_recommendation(1 params) -> RecommendationAssessment

### P:/.claude/hooks/verification/upstream_types.py
  class DecompositionHint (0 methods)
  def format_decomposition_hint(1 params) -> ?
  def format_coverage_summary(1 params) -> str

### P:/.claude/hooks/verification_audit_logger.py
  class VerificationAuditLogger (6 methods)
  def get_audit_logger(0 params) -> VerificationAuditLogger
  def log_verification_bypass(4 params) -> ?
  def check_verification_enabled(0 params) -> bool
  def __init__(2 params) -> ?
  def _ensure_log_directory(1 params) -> ?

### P:/.claude/hooks/verify_claims.py
  def run_theater_detection(2 params) -> dict
  def run_semantic_matching(2 params) -> dict
  def run_evidence_window_check(3 params) -> dict
  def run_claim_specificity_check(1 params) -> dict
  def calculate_final_score(2 params) -> dict
  def main(0 params) -> ?

### P:/.claude/hooks/verify_hook_wiring.py
  def _extract_python_target(1 params) -> ?
  def main(0 params) -> int

### P:/.claude/hooks/verify_task002_completion.py
  def slow_load(2 params) -> ?

### P:/.claude/hooks/violation_reporter.py
  class ViolationReporter (12 methods)
  def __init__(2 params) -> ?
  def _get_allowed_root_patterns(1 params) -> ?
  def _get_violation_tracker(1 params) -> ?
  def report_violation(6 params) -> bool
  def _log_violation_to_stderr(4 params) -> ?

### P:/.claude/hooks/voice_notifications_worker.py
  def _select_voice(1 params) -> ?
  def main(0 params) -> int
  def main(0 params) -> ?
  def main(0 params) -> ?
  def main(0 params) -> ?
  def main(0 params) -> ?
  def main(0 params) -> ?
  def _call_m2_7_verifier(4 params) -> list
  def verify_with_m2_7(3 params) -> dict

---
END OF PACK