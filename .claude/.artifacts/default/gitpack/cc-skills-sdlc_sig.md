# cc-skills-sdlc_sig.md

## PACK INFO
- Target: P:\packages\cc-skills-sdlc
- Py: 439, MD: 2

## SIGNATURES


### __init__.py
```
  (empty)
```

### contract-primitives\src\contract_primitives\__init__.py
```
  (empty)
```

### contract-primitives\src\contract_primitives\events.py
```
  def _detect_terminal_id() -> str
  def _get_event_log_path() -> Path
  def log_contract_event(event_type, boundary_id, payload, validator, result) -> Path
```

### contract-primitives\src\contract_primitives\plan_consumption.py
```
  class PlanConsumerValidationResult()
  def discover_local_plan_path() -> str | None
  def validate_plan_for_execution(plan_path) -> PlanConsumerValidationResult
```

### contract-primitives\src\contract_primitives\schemas.py
```
  class BoundaryContract()
  class ContractAuthorityPacket()
  class PlanningHandoffPacket()
  class PlanningSourcePacket()
  def _normalize_cell(value) -> str
  def extract_markdown_table(section_text) -> tuple[list[str], list[dict[str, str]]]
  def find_contract_boundary_rows(plan_text) -> tuple[list[str], list[dict[str, str]]]
  def parse_contract_authority_packet(markdown_text) -> ContractAuthorityPacket
  def parse_planning_handoff_packet(markdown_text) -> PlanningHandoffPacket
  def parse_planning_source_packet(markdown_text) -> PlanningSourcePacket
  def adr_requires_planning_handoff(markdown_text) -> bool
```

### contract-primitives\src\contract_primitives\validators.py
```
  class ValidationResult()
  def validate_contract(schema, payload) -> ValidationResult
  def validate_boundary_contract(contract, payload) -> ValidationResult
```

### enforce\configs\__init__.py
```
  (empty)
```

### enforce\phase_ledger.py
```
  def get_verified_identity(session_id) -> dict | None
  def _get_terminal_id(session_id) -> str
  def _ledger_path(skill_id, session_id) -> Path
  def read_phase_ledger(skill_id, session_id) -> dict[str, Any] | None
  def write_phase_marker(skill_id, phase_name, payload, session_id) -> None
  def reset_phase_ledger(skill_id, session_id) -> None
```

### enforce\stop_gate.py
```
  def _check_ledger(skill_id, phase_name, session_id) -> bool
  def _evidence_type(phase) -> str
  def _check_file_flags(files, require_all, run_id, terminal_id) -> bool
  def _check_json_file(path, key, expected, run_id) -> bool
  def _check_command(cmd, expected, cwd) -> bool
  def evaluate_gates(skill_id, config, env) -> tuple[int, str]
  def _evaluate_phase(skill_id, phase, run_id, terminal_id, env, session_id) -> bool
  def load_config_for_skill(skill_id) -> EnforceConfig
```

### enforce\tests\test_enforce.py
```
  class TestPhaseLedgerEnforce()
    def setup_method(self) -> None
    def teardown_method(self) -> None
    def test_write_and_read(self) -> None
    def test_append_only_no_clobber(self) -> None
    def test_append_only_with_payload_overwrites(self) -> None
    def test_multiple_phases_independent(self) -> None
    def test_reset(self) -> None
  class TestStopGateEnforce()
    def setup_method(self) -> None
    def teardown_method(self) -> None
    def test_code_no_ledger_clean(self) -> None
    def test_code_all_hard_gates_exit_0(self) -> None
    def test_code_missing_hard_gate_exit_2(self) -> None
    def test_code_fast_mode_skips_full_suite(self) -> None
    def test_go_all_flag_files_exit_0(self) -> None
    def test_go_missing_hard_flag_exit_2(self) -> None
    def test_go_advisory_missing_exit_0(self) -> None
  class TestStopHookScriptsEnforce()
    def setup_method(self) -> None
    def teardown_method(self) -> None
    def _run_stop_hook(self, script_path, env_extra) -> subprocess.CompletedProcess
    def test_code_v4_stop_no_ledger_exit_0(self) -> None
    def test_code_v4_stop_all_gates_exit_0(self) -> None
    def test_code_v4_stop_missing_hard_exit_2(self) -> None
    def test_go_v3_stop_no_flags_exit_2(self) -> None
    def test_go_v3_stop_all_flags_exit_0(self) -> None
    def test_go_v3_stop_missing_advisory_exit_0(self) -> None
  class TestEnforceConfigs()
    def test_no_prose_only_hard_gates(self) -> None
    def test_code_ef_hard_gates_ledger_only(self) -> None
    def test_go_ef_hard_gates_all_have_file_flag(self) -> None
    def test_advisory_phases_present(self) -> None
  class TestCanonicalEENames()
    def test_code_ef_and_code_v4_load_same_phases(self) -> None
    def test_go_ef_and_go_v3_load_same_phases(self) -> None
    def test_load_config_for_skill_resolves_code_ef(self) -> None
    def test_load_config_for_skill_resolves_go_ef(self) -> None
    def test_load_config_for_skill_resolves_code_v4_backward_compat(self) -> None
    def test_load_config_for_skill_resolves_go_v3_backward_compat(self) -> None
```

### hooks\PostToolUse.py
```
  def main()
```

### hooks\PreToolUse.py
```
  def main()
```

### hooks\Stop.py
```
  def main()
```

### scripts\__init__.py
```
  (empty)
```

### scripts\go_ct_executor.py
```
  class TaskType(str, Enum)
  class TaskStatus(str, Enum)
  class CleanupMode(str, Enum)
  class PhaseStatus(str, Enum)
  class Task()
  class Phase(BaseModel)
  class PipelineState(BaseModel)
    def phase(self, name) -> Phase
    def complete_phase(self, name) -> None
    def fail_phase(self, name, error) -> None
  def touch_gate(state_dir, gate_name) -> None
  def check_gate(state_dir, gate_name) -> bool
  def get_worktrees() -> dict[str, str]
  def find_state_dirs(base_dir, skill) -> list[dict]
  def pre_clean(base_dir, skill, mode) -> list[dict]
  def _prune_worktree(path, branch) -> None
  def _archive_state(state_path, base_dir) -> None
  def purge_attempt_files(state_dir) -> int
  def merge_worktree(state, state_dir) -> dict
  def post_clean(state, base_dir) -> None
  def create_worktree(state, base_dir) -> tuple[str, str]
  def select_task(state, task_desc, state_dir) -> None
  def _classify_task_type(desc) -> TaskType
  def _get_routing(task_type) -> dict
  def run_verification(state, state_dir) -> bool
  def run_simplify(state, state_dir) -> bool
  def run_reviews(state, state_dir) -> None
  def generate_pr_artifacts(state, state_dir) -> dict
  def save_state(state, base_dir) -> None
  def run_pipeline(task_desc, output_dir, cleanup_mode) -> dict
  def main() -> None
```

### scripts\pi_dispatch.py
```
  def parse_jsonl(raw_output) -> dict | None
  def run_dispatch(model, prompt, output_path) -> int
  def main() -> int
```

### scripts\skill-creator\__init__.py
```
  (empty)
```

### scripts\skill-creator\aggregate_benchmark.py
```
  def calculate_stats(values) -> dict
  def load_run_results(benchmark_dir) -> dict
  def aggregate_results(results) -> dict
  def generate_benchmark(benchmark_dir, skill_name, skill_path) -> dict
  def generate_markdown(benchmark) -> str
  def main()
```

### scripts\skill-creator\generate_report.py
```
  def generate_html(data, auto_refresh, skill_name) -> str
  def main()
```

### scripts\skill-creator\improve_description.py
```
  def claude_p(prompt, model) -> str
  def improve_description(skill_name, skill_content, current_description, eval_results, history, model, test_results, log_dir, iteration) -> str
  def main()
```

### scripts\skill-creator\package_skill.py
```
  def should_exclude(rel_path) -> bool
  def package_skill(skill_path, output_dir)
  def main()
```

### scripts\skill-creator\quick_validate.py
```
  def validate_skill(skill_path)
```

### scripts\skill-creator\run_eval.py
```
  def find_project_root() -> Path
  def run_single_query(query, skill_name, skill_description, timeout, project_root, model) -> bool
  def run_eval(eval_set, skill_name, description, num_workers, timeout, project_root, runs_per_query, trigger_threshold, model) -> dict
  def main()
```

### scripts\skill-creator\run_loop.py
```
  def split_eval_set(eval_set, holdout, seed) -> tuple[list[dict], list[dict]]
  def run_loop(eval_set, skill_path, description_override, num_workers, timeout, max_iterations, runs_per_query, trigger_threshold, holdout, model, verbose, live_report_path, log_dir) -> dict
  def main()
```

### scripts\skill-creator\sync_check.py
```
  def _find_plugin_cache() -> Path
  def source_hashes(plugin_dir) -> dict[str, str]
  def save_tracking(hashes) -> None
  def load_tracking() -> dict[str, str]
  def check_for_updates(verbose) -> tuple[bool, dict[str, str]]
  def sync_and_update(verbose) -> None
```

### scripts\skill-creator\utils.py
```
  def parse_skill_md(skill_path) -> tuple[str, str, str]
```

### scripts\verify_glm_routing.py
```
  def check_db() -> dict
  def check_runtime() -> dict
  def main() -> int
```

### skills\__lib\gitpack_hooks.py
```
  def extract_signatures(filepath)
  def get_files(root)
  def main()
```

### skills\__lib\sdlc_schemas.py
```
  class TaskRouting(BaseModel)
  class TaskContract(BaseModel)
  class PlanMetadata(BaseModel)
  class ImplementationPlan(BaseModel)
```

### skills\__lib\sdlc_state.py
```
  def resolve_state_root() -> Path
  def resolve_tdd_state_root() -> Path
  def resolve_go_state_root() -> Path
```

### skills\arch\__init__.py
```
  (empty)
```

### skills\arch\aid_integration.py
```
  class AIDAction(Enum)
  class AIDConfig()
  class AIDResult()
  class AIDSkillIntegrator()
    def __init__(self, config)
    def _verify_aid_cli(self) -> None
    def run_ai_action(self, target_path, ai_action, include_patterns, exclude_patterns) -> AIDResult
    def _extract_prompt_file(self, output) -> str | None
    def generate_diagrams(self, target_path) -> AIDResult
    def analyze_refactoring(self, target_path) -> AIDResult
    def analyze_performance(self, target_path) -> AIDResult
    def analyze_security(self, target_path) -> AIDResult
    def analyze_codebase(self, target_path) -> AIDResult
    def analyze_best_practices(self, target_path) -> AIDResult
    def hunt_bugs(self, target_path) -> AIDResult
    def generate_docs(self, target_path, multi_file) -> AIDResult
  def create_aid_integrator(config) -> AIDSkillIntegrator
```

### skills\arch\aid_wrapper.py
```
  class CodebaseAnalysis()
  class APIExtract()
  class LayerAnalysis()
  class DependencyDirection()
  class AidIntegrator()
    def __init__(self, config)
    def distill(self, target_path, include_patterns, exclude_patterns) -> CodebaseAnalysis
    def extract_public_apis(self, target_path, include_private) -> list[APIExtract]
    def analyze_dependencies(self, target_path) -> dict[str, list[str]]
    def detect_boundaries(self, target_path) -> list[str]
    def detect_layers(self, target_path) -> LayerAnalysis
    def analyze_dependency_direction(self, target_path) -> DependencyDirection
    def _collect_files(self, target, include_patterns, exclude_patterns) -> list[Path]
    def _distill_python(self, content, file_path) -> str
    def _distill_typescript(self, content, file_path) -> str
    def _distill_generic(self, content, file_path) -> str
    def _extract_apis_python(self, content, file_path, include_private) -> list[APIExtract]
    def _extract_apis_typescript(self, content, file_path, include_private) -> list[APIExtract]
    def _analyze_dependencies_python(self, content, file_path) -> list[str]
    def _analyze_dependencies_typescript(self, content, file_path) -> list[str]
    def _detect_boundaries(self, target, files) -> list[str]
    def _build_import_graph(self, target, files) -> dict[str, list[str]]
    def _detect_layer_violations(self, layers, import_graph) -> list[str]
    def _classify_file_layer(self, file_path, layers) -> str | None
    def _detect_dependency_violations(self, import_graph) -> list[str]
  def create_aid_integrator(config) -> AidIntegrator
```

### skills\arch\aid_wrapper_v2.py
```
  class AIDCompressionLevel(Enum)
  class AIDAIAction(Enum)
  class AIDAnalysisResult()
  class AidIntegratorV2()
    def __init__(self, config)
    def _normalize_path(self, path) -> str
    def distill(self, target_path, include_patterns, exclude_patterns) -> AIDAnalysisResult
    def analyze_with_ai_action(self, target_path, ai_action, include_patterns, exclude_patterns) -> str
    def generate_diagrams(self, target_path) -> str
    def detect_layers(self, target_path) -> dict[str, Any]
    def _detect_layer_violations(self, layers, import_graph) -> list[str]
    def _classify_file_layer(self, file_path, layers) -> str | None
    def analyze_dependency_direction(self, target_path) -> dict[str, Any]
    def _detect_dependency_violations(self, import_graph) -> list[str]
  def create_aid_integrator(config) -> AidIntegratorV2
```

### skills\arch\arch_validate.py
```
  class StageCheck()
  class StageValidationResult()
    def all_pass(self) -> bool
    def pass_count(self) -> int
    def warn_count(self) -> int
    def fail_count(self) -> int
    def to_findings(self) -> list[dict[str, object]]
  class StageValidator()
    def __init__(self, contract_sensitive) -> None
    def _check_stage(self, text, stage) -> StageCheck
    def validate(self, text) -> StageValidationResult
  def validate_adr(path) -> dict[str, object]
  def _run_stage_validation(text, contract_sensitive) -> dict[str, object]
  def main(argv) -> int
```

### skills\arch\config.py
```
  def clear_config_cache() -> None
  def _load_arch_config_impl(user_config_str, project_config_str, user_mtime, project_mtime, env_domain, env_output_size, env_evidence_level) -> dict[str, Any] | None
  def load_arch_config() -> dict[str, Any] | None
  def _get_file_mtime(path) -> float
```

### skills\arch\cross_platform_paths.py
```
  def _detect_platform() -> PlatformName
  def resolve_cks_db_path() -> Path
  def resolve_template_path(template_name) -> str
```

### skills\arch\path_detection.py
```
  def detect_path_backslashes(path_str) -> bool
  def extract_path_components(path_str) -> list
```

### skills\arch\persistence.py
```
  def should_skip_persistence(query, output, skip_keywords) -> bool
  def generate_decision_filename(query, _template) -> str
  def _find_cks_db() -> Path | None
  def _ingest_into_cks(query, template, domain, output, filename) -> None
  def save_arch_decision(query, template, domain, output, confidence, research_sources, decisions_dir, metrics) -> str | None
  def load_decision_index(index_path) -> list[dict[str, Any]]
  def search_decisions(query, index_path, limit) -> list[dict[str, Any]]
  def cleanup_old_entries(days_threshold, index_path, dry_run) -> dict[str, Any]
  def rotate_index(keep_entries, index_path, decisions_dir, dry_run) -> dict[str, Any]
  def cleanup_orphaned_files(index_path, decisions_dir, dry_run) -> dict[str, Any]
  def track_template_chaining_usage(primary_template, chained_domains, source, query, usage_file) -> None
  def check_chaining_usage_monitoring(usage_file, days_threshold) -> dict[str, Any]
  def log_decision_metrics(decision_id, query, pattern, high_stakes, templates, context, vs, judge, diversity, persistence, user_outcome, log_file) -> None
  def log_candidate_metrics(decision_id, candidate_id, vs, critic, selection, log_file) -> None
```

### skills\arch\planning_handoff_validation.py
```
  def is_planning_bound_adr(text, handoff_packet_version) -> bool
  def validate_planning_handoff_contract(text, packet, handoff) -> list[dict[str, object]]
```

### skills\arch\prerequisite_analyzer.py
```
  class AnalysisResult(TypedDict)
  class PrerequisiteAnalyzer()
    def analyze(query) -> AnalysisResult
    def _matches_optimization(text) -> bool
    def _matches_prd(text) -> bool
    def _matches_discover(text) -> bool
    def _matches_debug(text) -> bool
    def _matches_any_cached(text) -> bool
    def _matches_any(text, patterns) -> bool
    def _matches_any_cache_clear() -> None
    def _matches_any_cache_info()
```

### skills\arch\resources\validate_docs.py
```
  class DocumentationValidator()
    def __init__(self, docs_dir)
    def validate(self)
```

### skills\arch\results.py
```
  class ArchResult()
    def is_complete(self) -> bool
    def is_valid(self) -> bool
    def unwrap(self) -> T
    def unwrap_or(self, default) -> T
    def unwrap_error(self) -> str
```

### skills\arch\routing.py
```
  [error]
```

### skills\arch\test_aid_v2_integration.py
```
  def test_aid_integrator_creation()
  def test_basic_distillation()
  def test_layer_detection()
  def test_dependency_analysis()
  def main()
```

### skills\arch\test_aid_value.py
```
  (empty)
```

### skills\arch\test_debug.py
```
  def load_config()
```

### skills\arch\tests\__init__.py
```
  (empty)
```

### skills\arch\tests\conftest.py
```
  def pytest_configure(config)
  def clear_config_cache_between_tests()
```

### skills\arch\tests\test_arch_validate_handoff.py
```
  def test_planning_bound_adr_requires_planning_handoff_packet(tmp_path) -> None
  def test_planning_bound_adr_with_handoff_packet_passes_handoff_check(tmp_path) -> None
  def test_planning_bound_adr_without_instruction_or_return_to_caller_blocks(tmp_path) -> None
  def test_nested_planning_return_to_caller_satisfies_routing_contract(tmp_path) -> None
```

### skills\arch\tests\test_cks_fallback.py
```
  class TestCKSModuleNotFound()
    def test_cks_module_not_found_sets_available_false(self)
    def test_cks_module_not_found_shows_warning(self)
  class TestCKSDatabaseMissing()
    def test_cks_database_missing_sets_available_false(self)
    def test_cks_database_missing_shows_warning(self)
  class TestCKSImportError()
    def test_cks_import_error_sets_available_false(self)
    def test_cks_generic_exception_handled(self)
  class TestCKSAvailable()
    def test_cks_available_sets_true(self)
    def test_cks_queries_work_when_available(self)
  class TestWarningMessageContent()
    def test_warning_includes_fix_suggestions(self)
    def test_warning_contains_error_details(self)
  class TestGenericAnalysisProceeds()
    def test_generic_analysis_proceeds_when_cks_unavailable(self)
    def test_analysis_falls_back_to_best_practices(self)
    def test_no_exception_raised_when_cks_unavailable(self)
```

### skills\arch\tests\test_cks_real_fallback.py
```
  [error]
```

### skills\arch\tests\test_cks_real_import.py
```
  class TestCKSIntegrationImplemented()
    def test_arch_skill_has_cks_import_handling_code(self)
    def test_cks_available_variable_is_accessible(self)
    def test_cks_integration_fallback_works(self)
```

### skills\arch\tests\test_config.py
```
  class TestLoadArchConfigDefaults()
    def test_no_config_returns_default_domain(self)
  class TestLoadArchConfigValidation()
    def test_invalid_domain_raises_value_error(self, tmp_path)
    def test_missing_default_domain_raises_value_error(self, tmp_path)
  class TestLoadArchConfigEnvOverride()
    def test_env_domain_overrides_config(self, tmp_path, monkeypatch)
  class TestValidDomains()
    def test_valid_domains_contains_expected(self)
    def test_valid_output_sizes(self)
    def test_valid_evidence_levels(self)
  class TestArchConfigClass()
    def test_arch_config_load_returns_arch_result(self)
    def test_arch_config_get_returns_default_when_no_key(self)
    def test_arch_config_get_returns_config_value(self)
  class TestClearConfigCache()
    def test_clear_config_cache_does_not_raise(self)
    def test_cache_clear_allows_fresh_load(self, tmp_path, monkeypatch)
```

### skills\arch\tests\test_config_caching.py
```
  def clear_cache_before_each_test()
  class TestLoadArchConfigCacheImplementation()
    def temp_config_dir(self, tmp_path) -> Path
    def test_cached_call_should_not_check_file_existence(self, temp_config_dir)
    def test_cache_invalidation_on_mtime_change(self, tmp_path)
```

### skills\arch\tests\test_config_extraction.py
```
  class TestConfigModuleExists()
    def test_config_module_exists(self)
    def test_config_module_importable(self)
  class TestLoadArchConfigFunction()
    def test_load_arch_config_function_exists(self)
    def test_load_arch_config_is_callable(self)
  class TestSkillMdReferencesModule()
    def skill_md_path(self)
    def skill_md_content(self, skill_md_path)
    def test_skill_md_references_config_load_arch_config(self, skill_md_content)
    def test_skill_md_contains_config_import_example(self, skill_md_content)
  class TestNoDuplicateFunctionInDoc()
    def skill_md_path(self)
    def skill_md_content(self, skill_md_path)
    def test_no_full_function_definition_in_skill_md(self, skill_md_content)
    def test_no_duplicate_implementation_details(self, skill_md_content)
    def test_skill_md_has_concise_reference_not_implementation(self, skill_md_content)
```

### skills\arch\tests\test_config_integration.py
```
  class TestLoadArchConfigWithRealFiles()
    def test_load_arch_config_with_real_files(self, tmp_path, monkeypatch)
    def test_load_arch_config_no_files_returns_none(self, tmp_path, monkeypatch)
    def test_load_arch_config_with_invalid_json_raises_error(self, tmp_path, monkeypatch)
    def test_load_arch_config_precedence_with_real_files(self, tmp_path, monkeypatch)
    def test_load_arch_config_with_invalid_domain_raises_error(self, tmp_path, monkeypatch)
```

### skills\arch\tests\test_config_merging.py
```
  class TestPartialConfigMerging()
    def test_partial_merge_project_overrides_user_preserves_others(self, mock_read, mock_exists)
    def test_partial_merge_multiple_keys_from_user_preserved(self, mock_read, mock_exists)
    def test_partial_merge_user_has_subset_project_has_superset(self, mock_read, mock_exists)
```

### skills\arch\tests\test_config_real_files.py
```
  def clean_arch_env_vars()
  def clear_cache()
  class TestRealConfigFileLoading()
    def test_load_valid_project_config_file(self, tmp_path)
    def test_load_config_without_env_vars(self, tmp_path)
    def test_malformed_json_fails_appropriately(self, tmp_path)
    def test_missing_required_field_fails_appropriately(self, tmp_path)
    def test_invalid_domain_value_fails_appropriately(self, tmp_path)
    def test_invalid_output_size_value_fails_appropriately(self, tmp_path)
```

### skills\arch\tests\test_config_thread_safety.py
```
  def clear_cache_before_each_test()
  def clean_arch_env_vars()
  class TestLoadArchConfigThreadSafety()
    def mock_config_env(self)
    def mock_project_config(self, tmp_path)
    def test_config_cache_has_thread_synchronization_mechanism(self)
    def test_concurrent_reads_no_cache_corruption(self, mock_project_config)
    def test_concurrent_cache_access_no_corruption(self, mock_config_env)
    def test_cache_invariant_maintained_under_concurrency(self)
    def test_no_lost_updates_under_concurrency(self, mock_project_config)
  class TestConfigCacheSpecificRaceConditions()
    def mock_config_env(self)
    def test_check_then_write_race_condition(self, mock_config_env)
    def test_concurrent_cache_miss_handling(self, mock_config_env)
  class TestFixtureCleanup()
    def test_clean_arch_env_vars_fixture_cleanup_single_var(self)
    def test_clean_arch_env_vars_fixture_cleanup_multiple_vars(self)
    def test_clean_arch_env_vars_fixture_restores_original_values(self)
```

### skills\arch\tests\test_config_types.py
```
  def clean_arch_env_vars()
  class TestInvalidValueTypes()
    def test_default_domain_as_integer_raises_type_error(self, mock_read, mock_exists)
    def test_output_size_as_list_raises_type_error(self, mock_read, mock_exists)
    def test_multiple_invalid_types_raises_error(self, mock_read, mock_exists)
    def test_evidence_level_as_boolean_raises_type_error(self, mock_read, mock_exists)
  class TestValidTypesWithInvalidValues()
    def test_string_type_but_invalid_domain_value(self, mock_read, mock_exists)
```

### skills\arch\tests\test_config_validation.py
```
  def clean_arch_env_vars()
  class TestInvalidDomainValue()
    def test_invalid_domain_value_raises_value_error(self, mock_read, mock_exists)
  class TestMissingRequiredField()
    def test_missing_required_field_raises_value_error(self, mock_read, mock_exists)
  class TestMalformedJSON()
    def test_malformed_json_raises_json_decode_error(self, mock_read, mock_exists)
  class TestValidConfig()
    def test_valid_config_returns_dict_with_default_domain(self, mock_read, mock_exists)
  class TestConfigPrecedence()
    def test_project_config_overrides_user_config(self, mock_read, mock_exists)
    def test_env_var_overrides_config_files(self, mock_read, mock_exists)
    def test_env_var_always_overrides_even_when_both_configs_have_different_values(self, mock_read, mock_exists)
  class TestMissingConfigFile()
    def test_missing_config_file_returns_none(self, mock_exists)
```

### skills\arch\tests\test_contracts_error_handling.py
```
  class TestLoadContractsFileNotFoundError()
    def test_load_contracts_missing_file_raises_error_with_helpful_message(self, tmp_path)
    def test_load_contracts_missing_file_helpful_error_content(self, tmp_path)
```

### skills\arch\tests\test_cross_platform.py
```
  [error]
```

### skills\arch\tests\test_dry_enforcement.py
```
  class TestDuplicateDetectionWarns()
    def test_duplicate_detection_warns_when_over_50_percent_overlap(self, capsys)
    def test_duplicate_detection_returns_overlap_percentage(self)
    def test_duplicate_detection_threshold_at_exactly_50_percent(self)
  class TestSharedFrameworkReference()
    def test_shared_framework_reference_suggests_extraction(self)
    def test_templates_should_reference_shared_frameworks(self, tmp_path)
    def test_detect_known_shared_framework_pattern(self)
  class TestEnforcementLevel()
    def test_high_overlap_over_70_percent_should_fail_validation(self, tmp_path)
    def test_high_overlap_threshold_constant_exists(self)
    def test_validation_returns_1_for_critical_duplicates(self, capsys)
  class TestMediumOverlap()
    def test_medium_overlap_50_to_70_percent_should_warn_but_pass(self, tmp_path)
    def test_medium_overlap_boundary_at_70_percent(self)
    def test_overlap_percentage_calculation_accuracy(self)
  class TestDRYEnforcementIntegration()
    def test_complete_dry_validation_workflow(self, tmp_path, capsys)
    def test_shared_frameworks_reference_in_result_message(self, capsys)
```

### skills\arch\tests\test_duplicate_load_arch_config.py
```
  class TestLoadArchConfigNotDuplicated()
    def test_routing_imports_load_arch_config_from_config(self)
    def test_only_one_load_arch_config_implementation(self)
    def test_load_arch_config_function_identity_same_result(self)
    def test_load_arch_config_same_signature(self)
    def test_load_arch_config_same_docstring(self)
  class TestLoadArchConfigBehavioralEquivalence()
    def mock_config_env(self)
    def test_environment_override_both_behave_same(self, mock_config_env)
    def test_none_config_both_behave_same(self)
    def test_invalid_domain_raises_same_error(self)
```

### skills\arch\tests\test_error_messages.py
```
  class TestLoadArchConfigErrorMessages()
    def test_invalid_domain_error_message_contains_fix_guidance(self, mock_read, mock_exists)
    def test_invalid_domain_error_message_is_actionable(self, mock_read, mock_exists)
    def test_missing_required_field_error_is_specific(self, mock_read, mock_exists)
```

### skills\arch\tests\test_external_caller_integration.py
```
  class TestExternalCallerIntegration()
    def test_external_import_path_works(self)
    def test_external_caller_handles_template_result_dict(self)
    def test_external_caller_handles_all_template_result_keys(self)
    def test_external_caller_with_template_override(self)
    def test_external_caller_with_default_domain(self)
    def test_external_caller_type_annotation_match(self)
    def test_external_caller_importlib_import(self)
    def test_breaking_change_catch_old_string_return(self)
    def test_external_caller_backward_compatibility_batch(self)
    def test_external_caller_chained_domains_feature(self)
```

### skills\arch\tests\test_harcoded_paths.py
```
  class TestReplacePDriveWithPlatformDetection()
    def fast_md_path(self) -> Path
    def fast_md_content(self, fast_md_path) -> str
    def test_fast_md_uses_cross_platform_cks_path(self, fast_md_content)
    def test_fast_md_no_hardcoded_cks_path(self, fast_md_content)
  class TestDeepMdUsesCrossPlatformPaths()
    def deep_md_path(self) -> Path
    def deep_md_content(self, deep_md_path) -> str
    def test_deep_md_uses_cross_platform_paths(self, deep_md_content)
    def test_deep_md_no_hardcoded_shared_frameworks_path(self, deep_md_content)
  def _remove_code_blocks(content) -> str
  class TestNoHardcodedPSlash()
    def templates_dir(self) -> Path
    def all_template_contents(self, templates_dir) -> dict[str, str]
    def test_no_hardcoded_p_colon_slash_in_templates(self, all_template_contents)
    def test_fast_and_deep_md_no_hardcoded_paths(self, all_template_contents)
  class TestTemplateUsesForwardSlashes()
    def templates_dir(self) -> Path
    def all_template_contents(self, templates_dir) -> dict[str, str]
    def test_template_paths_use_forward_slashes_only(self, all_template_contents)
    def test_template_paths_consistent_separators(self, all_template_contents)
  def test_cross_platform_paths_module_exists()
  def test_resolve_cks_db_path_function_exists()
  def test_resolve_template_path_function_exists()
```

### skills\arch\tests\test_integration_validation.py
```
  def test_validate_templates_end_to_end(tmp_path)
```

### skills\arch\tests\test_multi_terminal_isolation.py
```
  def test_concurrent_terminal_execution()
```

### skills\arch\tests\test_opt_out_flags.py
```
  def sample_architecture_plan()
  def test_got_enabled_by_default(sample_architecture_plan)
  def test_no_got_flag_disables_got(sample_architecture_plan)
  def test_default_behavior_quality_first()
  def test_flag_parsing_conceptual()
  def test_environment_variable_disables_got(sample_architecture_plan)
  def test_environment_variable_false_allows_got(sample_architecture_plan)
  def test_got_node_extraction_quality(sample_architecture_plan)
  def test_got_edge_analysis_quality(sample_architecture_plan)
  def test_got_opt_out_constitutional_compliance()
  def test_got_independent_of_other_enhancements()
  def test_got_quality_first_design()
```

### skills\arch\tests\test_overlap_numeric_validation.py
```
  class TestOverlapNumericValidation()
    def test_check_duplicate_logic_returns_numeric_value(self)
    def test_check_duplicate_logic_validates_against_50_percent_threshold(self)
    def test_check_duplicate_logic_high_overlap_triggers_failure(self)
    def test_check_duplicate_logic_below_threshold_returns_empty(self)
    def test_threshold_constants_are_defined(self)
  class TestCurrentTestLimitations()
    def test_current_test_only_checks_string_not_numeric(self)
    def test_check_duplicate_logic_returns_severity_indicator(self)
    def test_warning_range_has_severity_warning(self)
```

### skills\arch\tests\test_overlap_validation.py
```
  class TestOverlapPercentageParsingMISSING()
    def test_check_duplicate_logic_returns_numeric_overlap_parseable(self, capsys)
    def test_check_duplicate_logic_threshold_validation_70_plus(self, capsys)
    def test_check_duplicate_logic_threshold_validation_below_50(self, capsys)
  class TestOverlapPercentageThresholds()
    def test_threshold_constants_exist_and_are_correct(self)
  class TestMissingNumericValidationInExistingTests()
    def test_existing_test_only_checks_string_not_numeric(self, capsys)
```

### skills\arch\tests\test_path_detection.py
```
  class TestDetectPathBackslashesUsingPath()
    def test_function_exists(self)
    def test_detect_windows_path_backslashes(self)
    def test_no_backslashes_in_unix_paths(self)
    def test_handles_unicode_filenames(self)
  class TestExtractPathComponentsUsingParts()
    def test_function_exists(self)
    def test_extract_components_from_unix_path(self)
    def test_extract_components_from_windows_path(self)
    def test_handles_special_chars_in_filenames(self)
  class TestPathDetectionModuleExists()
    def test_path_detection_module_exists(self)
```

### skills\arch\tests\test_path_traversal.py
```
  class TestPathTraversalVulnerability()
    def test_path_traversal_with_double_dot_attack(self)
    def test_path_traversal_single_double_dot(self)
    def test_path_traversal_double_dot_in_middle(self)
    def test_path_traversal_with_absolute_path(self)
    def test_path_traversal_windows_absolute_path(self)
    def test_path_traversal_p_drive_absolute_path(self)
    def test_path_traversal_with_null_byte(self)
    def test_path_traversal_null_byte_with_traversal(self)
    def test_path_traversal_with_url_encoding(self)
    def test_path_traversal_with_double_encoded(self)
    def test_valid_template_name_still_works(self)
    def test_valid_template_with_hyphen(self)
  def test_security_vulnerability_documentation()
  class TestWindowsSpecificPathTraversal()
    def test_windows_unc_path_should_be_rejected(self)
    def test_windows_drive_relative_path_should_be_rejected(self)
    def test_windows_reserved_device_names_documentation(self)
    def test_windows_absolute_paths_should_be_rejected(self)
    def test_valid_template_names_still_work(self)
```

### skills\arch\tests\test_performance.py
```
  class TestTemplateContentCaching()
    def temp_template_file(self, tmp_path) -> Path
    def test_template_content_caching(self, temp_template_file)
    def test_cache_invalidation(self, temp_template_file)
    def test_duplicate_read_detection(self, temp_template_file)
    def test_performance_improvement(self, temp_template_file)
  class TestCacheImplementation()
    def clear_cache(self)
    def test_cache_clear_method_exists(self)
    def test_cache_info_method_exists(self)
    def test_cache_max_size_setting(self)
```

### skills\arch\tests\test_performance_caching_real.py
```
  class TestOriginalTestFlaw()
    def temp_template_file(self, tmp_path) -> Path
    def test_original_test_fails_because_assertion_is_wrong(self, temp_template_file)
    def test_correct_way_to_verify_caching(self, temp_template_file)
  class TestManualCounterDoesNotVerifyCaching()
    def temp_template_file(self, tmp_path) -> Path
    def test_manual_counter_always_equals_call_count(self, temp_template_file)
    def test_cache_info_correctly_tracks_caching(self, temp_template_file)
  class TestComparisonFlawedVsCorrect()
    def temp_template_file(self, tmp_path) -> Path
    def test_flawed_approach_manual_counter(self, temp_template_file)
    def test_correct_approach_cache_info(self, temp_template_file)
```

### skills\arch\tests\test_performance_deterministic.py
```
  class TestFlakyTimingBehavior()
    def clear_cache_before_each_test(self)
    def temp_template_file(self, tmp_path) -> Path
    def test_timing_can_fail_when_cached_is_slower(self, temp_template_file)
  class TestDeterministicPerformance()
    def clear_cache_before_each_test(self)
    def temp_template_file(self, tmp_path) -> Path
    def test_performance_improvement_with_mocked_time(self, temp_template_file)
    def test_cache_info_method_exists(self)
    def test_cache_clear_method_works(self, temp_template_file)
```

### skills\arch\tests\test_persistence.py
```
  def _make_cks_db(path) -> None
  class TestFindCksDb()
    def test_returns_path_when_db_exists(self, tmp_path)
    def test_returns_none_when_db_missing(self, tmp_path)
    def test_returns_path_type(self, tmp_path)
  class TestIngestIntoCks()
    def test_inserts_row_into_cks_db(self, tmp_path)
    def test_content_truncated_to_2000_chars(self, tmp_path)
    def test_title_truncates_query_at_80_chars(self, tmp_path)
    def test_silent_failure_when_db_not_found(self)
    def test_silent_failure_on_corrupt_db(self, tmp_path)
    def test_silent_failure_on_arbitrary_exception(self)
    def test_insert_or_ignore_on_duplicate_id(self, tmp_path)
  class TestSaveArchDecisionCksIntegration()
    def test_ingest_called_after_successful_save(self, tmp_path)
    def test_ingest_not_called_when_save_skipped(self, tmp_path)
    def test_save_returns_filepath_despite_cks_down(self, tmp_path)
```

### skills\arch\tests\test_prerequisite_cache.py
```
  class TestCacheKeyOptimizationForEfficiency()
    def test_cache_size_reduced_with_text_only_key(self)
    def test_cache_efficient_for_repeated_analyze_calls(self)
  class TestCurrentCacheInefficiency()
    def test_duplicate_entries_for_same_text(self)
    def test_cache_hit_with_identical_call(self)
  class TestCacheCapacity()
    def test_maxsize_256(self)
    def test_cache_capacity_for_unique_texts(self)
  class TestPatternConstants()
    def test_patterns_are_tuples(self)
    def test_patterns_not_empty(self)
  class TestIndividualCacheBehavior()
    def test_matches_optimization_cache_hits_on_repeated_calls(self)
    def test_matches_prd_cache_hits_on_repeated_calls(self)
    def test_matches_debug_cache_hits_on_repeated_calls(self)
    def test_cache_clear_works_for_all_cached_methods(self)
    def test_cache_size_is_bounded(self)
    def test_different_inputs_create_different_cache_entries(self)
```

### skills\arch\tests\test_prerequisite_gates.py
```
  def skip_if_not_implemented()
  class TestOptimizationQueriesDoNotTriggerPrerequisiteGates()
    def test_improve_memory_system_does_not_trigger_prerequisite_gate(self)
    def test_optimize_x_proceeds_directly_to_architecture(self)
    def test_harden_y_does_not_trigger_prd_gate(self)
    def test_enhance_query_does_not_trigger_gate(self)
    def test_stabilize_query_does_not_trigger_gate(self)
  class TestGenuinePrerequisiteNeedsTriggerGates()
    def test_from_requirements_triggers_prd_gate(self)
    def test_how_is_x_structured_triggers_discover_gate(self)
    def test_why_failing_triggers_debug_gate(self)
    def test_explicit_prd_request_triggers_gate(self)
    def test_where_are_requirements_triggers_prd_gate(self)
  class TestSemanticAnalysisDistinguishesOptimizationFromPrerequisites()
    def test_optimization_without_requirements_proceeds(self)
    def test_optimization_with_requirements_triggers_prd(self)
    def test_case_insensitive_pattern_matching(self)
    def test_whitespace_handling(self)
```

### skills\arch\tests\test_real_platform.py
```
  class TestRealPlatformDetection()
    def test_detect_platform_returns_valid_value(self)
    def test_detect_platform_matches_platform_system(self)
  class TestRealPlatformPathBehavior()
    def test_path_behavior_matches_detected_platform(self)
    def test_current_platform_path_separators(self)
  class TestRealPlatformCrossPlatformFunctions()
    def test_resolve_cks_db_path_returns_valid_path(self)
    def test_resolve_cks_db_path_matches_detected_platform(self)
    def test_resolve_template_path_uses_forward_slashes(self)
    def test_resolve_template_path_validates_input(self)
  class TestRealPlatformIntegration()
    def test_full_workflow_on_real_platform(self)
    def test_platform_consistency(self)
```

### skills\arch\tests\test_result_structure.py
```
  def _broken_analyze(query) -> dict
  def _wrong_type_analyze(query) -> dict
  def _extra_keys_analyze(query) -> dict
  class TestResultStructureValidation()
    def test_analyze_returns_dict(self)
    def test_result_contains_all_required_keys(self)
    def test_key_types_are_correct_for_optimization_query(self)
    def test_key_types_are_correct_for_prerequisite_query(self)
    def test_result_structure_across_various_query_types(self)
    def test_empty_query_returns_valid_structure(self)
  class TestBrokenImplementationDetection()
    def test_fails_when_key_is_missing(self)
    def test_fails_when_key_has_wrong_type(self)
    def test_fails_when_extra_keys_present(self)
```

### skills\arch\tests\test_results.py
```
  class TestArchResultSuccess()
    def test_is_success_true_on_success(self)
    def test_value_available_on_success(self)
    def test_error_none_on_success(self)
    def test_is_complete_true_when_success_with_value(self)
    def test_is_valid_true_on_success(self)
    def test_templates_used_defaults_to_empty_list(self)
    def test_metadata_defaults_to_empty_dict(self)
    def test_templates_used_can_be_set(self)
    def test_metadata_can_be_set(self)
  class TestArchResultError()
    def test_is_success_false_on_error(self)
    def test_value_none_on_error(self)
    def test_error_available_on_error(self)
    def test_is_complete_false_on_error(self)
    def test_is_valid_true_on_error(self)
    def test_error_with_metadata(self)
  class TestArchResultUnwrap()
    def test_unwrap_returns_value_on_success(self)
    def test_unwrap_raises_on_error(self)
    def test_unwrap_raises_when_value_is_none_on_success(self)
  class TestArchResultUnwrapOr()
    def test_unwrap_or_returns_value_on_success(self)
    def test_unwrap_or_returns_default_on_error(self)
    def test_unwrap_or_returns_default_when_value_is_none(self)
  class TestArchResultUnwrapError()
    def test_unwrap_error_returns_error_string(self)
    def test_unwrap_error_raises_on_success(self)
    def test_unwrap_error_returns_unknown_when_error_is_none(self)
  class TestArchResultGeneric()
    def test_generic_with_dict_value(self)
    def test_generic_with_list_value(self)
    def test_generic_with_str_value(self)
    def test_generic_with_tuple_value(self)
  class TestArchResultInvariant()
    def test_archresult_of_dict_not_assignable_to_archresult_of_list(self)
    def test_archresult_of_str_not_assignable_to_archresult_of_int(self)
```

### skills\arch\tests\test_routing.py
```
  class TestExtractTemplateOverride()
    def test_valid_template_override_returns_template(self)
    def test_all_valid_templates_accepted(self)
    def test_invalid_template_returns_none(self)
    def test_no_override_returns_none(self)
    def test_case_sensitive_template_names(self)
    def test_override_with_hyphenated_name(self)
    def test_template_chaining_two_templates(self)
    def test_template_chaining_three_templates(self)
    def test_template_chaining_invalid_in_chain(self)
    def test_template_chaining_duplicate_templates(self)
  class TestDetectDomainKeywords()
    def test_cli_domain_detected(self)
    def test_python_domain_detected(self)
    def test_data_pipeline_domain_detected(self)
    def test_precedent_domain_detected(self)
    def test_no_keywords_returns_none(self)
    def test_priority_order_cli_over_python(self)
    def test_case_insensitive_matching(self)
    def test_all_cli_keywords(self)
    def test_all_python_keywords(self)
  class TestDetectComplexity()
    def test_redesign_indicates_deep(self)
    def test_architecture_indicates_deep(self)
    def test_microservices_indicates_deep(self)
    def test_rewrite_indicates_deep(self)
    def test_from_scratch_indicates_deep(self)
    def test_no_indicators_defaults_to_fast(self)
    def test_case_insensitive_detection(self)
    def test_all_high_complexity_indicators(self)
  class TestDetectIntentType()
    def test_improve_with_subsystem_returns_improve_system(self)
    def test_optimize_with_cks_returns_improve_system(self)
    def test_enhance_with_hooks_returns_improve_system(self)
    def test_improve_without_subsystem_returns_default(self)
    def test_subsystem_without_improve_returns_default(self)
    def test_no_keywords_returns_default(self)
    def test_case_insensitive_detection(self)
    def test_review_with_architecture_returns_architecture_review(self)
    def test_audit_with_design_returns_architecture_review(self)
    def test_assess_with_arch_returns_architecture_review(self)
    def test_evaluate_with_system_returns_architecture_review(self)
    def test_review_without_architecture_returns_default(self)
    def test_architecture_without_review_returns_default(self)
    def test_architecture_review_case_insensitive(self)
  class TestSelectTemplate()
    def test_template_override_parameter_highest_priority(self)
    def test_invalid_template_override_raises_error(self)
    def test_template_override_in_query(self)
    def test_invalid_template_in_query_ignored(self)
    def test_default_domain_used_when_no_keywords(self)
    def test_env_domain_used_when_no_default_domain(self)
    def test_default_domain_overrides_env_domain(self)
    def test_auto_domain_allows_keyword_detection(self)
    def test_auto_domain_falls_through_to_complexity(self)
    def test_invalid_domain_raises_error(self)
    def test_keyword_detection_overrides_default_domain(self)
    def test_complexity_detection_when_no_domain_or_keywords(self)
    def test_complexity_detection_defaults_to_fast(self)
    def test_full_routing_flow_priority_order(self)
  class TestValidateTemplate()
    def test_valid_template_returns_true(self)
    def test_invalid_template_returns_false(self)
    def test_all_valid_templates_validate(self)
    def test_error_message_includes_valid_templates(self)
  class TestConstants()
    def test_domain_keywords_structure(self)
    def test_valid_templates_is_set(self)
    def test_template_metadata_structure(self)
    def test_domain_priority_order(self)
  class TestTypeDefinitions()
    def test_template_result_type(self)
    def test_config_result_type(self)
    def test_validation_result_type(self)
  class TestIntegrationSelectTemplateWithConfig()
    def test_select_template_with_config_no_default_domain(self)
    def test_select_template_with_config_default_domain(self)
    def test_select_template_with_config_auto_domain(self)
    def test_select_template_with_config_and_file_validation(self)
    def test_select_template_with_config_priority_integration(self)
    def test_select_template_full_end_to_end_flow(self)
```

### skills\arch\tests\test_template_io_errors.py
```
  class TestValidateTemplateIOErrors()
    def test_permission_error_returns_helpful_message(self)
    def test_unicode_decode_error_returns_helpful_message(self)
    def test_file_system_lock_error_returns_helpful_message(self)
    def test_os_error_returns_helpful_message(self)
    def test_error_messages_are_actionable(self)
  class TestValidateTemplateIOErrorContract()
    def test_error_message_format_is_tuple(self)
    def test_all_valid_templates_handle_io_errors_consistently(self)
```

### skills\arch\tests\test_template_override_security.py
```
  class TestExtractTemplateOverrideSecurity()
    def test_extract_template_override_returns_any_value(self)
    def test_extract_template_override_with_special_chars(self)
    def test_extract_template_override_should_validate_against_allowlist(self)
```

### skills\arch\tests\test_type_hints_consistency.py
```
  class TestTypeHintConsistency()
    def module_path(self) -> Path
    def module_source(self, module_path) -> str
    def module_ast(self, module_source) -> ast.Module
    def test_no_old_typing_imports(self, module_ast)
    def test_list_syntax_uses_lowercase(self, module_source)
    def test_dict_syntax_uses_lowercase(self, module_source)
    def test_tuple_syntax_uses_lowercase(self, module_source)
    def test_necessary_typing_imports_remain(self, module_ast)
```

### skills\arch\tests\test_valid_domains_consistency.py
```
  def test_valid_domains_identical()
  def test_valid_domains_contains_expected_core_domains()
```

### skills\arch\tests\test_validate.py
```
  class TestTemplateValidatorInit()
    def test_default_resources_dir(self)
    def test_custom_resources_dir(self)
  class TestCheckFileExists()
    def test_all_templates_exist(self)
    def test_missing_template_returns_error(self)
    def test_partial_missing(self)
  class TestCheckDuplicates()
    def test_no_duplicates_between_fast_and_deep(self)
    def test_extract_section_content(self)
    def test_extract_section_not_found(self)
    def test_calculate_line_overlap_empty(self)
    def test_calculate_line_overlap_full(self)
    def test_calculate_line_overlap_partial(self)
  class TestCheckPermissions()
    def test_readable_templates(self)
    def test_empty_file_is_unreadable(self, tmp_path)
  class TestValidateTemplates()
    def test_valid_templates_pass_all_stages(self)
    def test_fail_fast_at_file_exists(self)
    def test_fail_fast_at_duplicates(self)
    def test_none_defaults_to_all_templates(self)
    def test_constants_are_correct(self)
  class TestStandaloneFunction()
    def test_wrapper_returns_arch_result(self)
```

### skills\arch\tests\test_validate_templates.py
```
  class TestPrintStatus()
    def test_print_status_pass_outputs_green_checkmark(self, capsys)
    def test_print_status_fail_outputs_red_x(self, capsys)
    def test_print_status_info_outputs_indented_message(self, capsys)
    def test_print_status_warn_outputs_yellow_warning(self, capsys)
  class TestLoadTemplateContent()
    def test_load_template_content_reads_markdown_file(self, tmp_path)
    def test_load_template_content_handles_missing_file(self, tmp_path)
    def test_load_template_content_handles_empty_file(self, tmp_path)
  class TestExtractHeadings()
    def test_extract_headings_finds_single_heading(self)
    def test_extract_headings_finds_multiple_headings(self)
    def test_extract_headings_handles_heading_with_text(self)
    def test_extract_headings_handles_empty_content(self)
    def test_extract_headings_preserves_heading_format(self)
  class TestLoadContracts()
    def test_load_contracts_loads_yaml_file(self, tmp_path)
    def test_load_contracts_handles_missing_file(self, tmp_path)
    def test_load_contracts_handles_empty_yaml(self, tmp_path)
  class TestValidateRequiredHeadings()
    def test_validate_required_headings_all_present(self, tmp_path)
    def test_validate_required_headings_missing_some(self, tmp_path)
    def test_validate_required_headings_empty_required_list(self, tmp_path)
  class TestCheckDuplicateLogic()
    def test_check_duplicate_logic_no_duplicates(self)
    def test_check_duplicate_logic_detects_50_percent_overlap(self)
    def test_check_duplicate_logic_ignores_low_overlap(self)
    def test_check_duplicate_logic_checks_all_sections(self)
  class TestValidateAll()
    def test_validate_all_returns_zero_on_success(self, mock_print, mock_load, mock_contracts, tmp_path)
    def test_validate_all_returns_one_on_failure(self, mock_print, mock_load, mock_contracts, tmp_path)
    def test_validate_all_checks_all_templates(self, mock_print, mock_load, mock_contracts, tmp_path)
    def test_validate_all_reports_missing_templates(self, mock_print, mock_load, mock_contracts)
```

### skills\arch\validate.py
```
  class TemplateValidator()
    def __init__(self, resources_dir) -> None
    def _check_file_exists(self, template_names) -> ArchResult[list[str]]
    def _extract_section_content(self, content, section_name) -> str | None
    def _calculate_line_overlap(self, text1, text2) -> float
    def _check_duplicates(self, template_names) -> ArchResult[list[str]]
    def _check_permissions(self, template_names) -> ArchResult[list[str]]
    def validate_templates(self, template_names) -> ArchResult[list[str]]
  def validate_templates(template_names) -> ArchResult[list[str]]
```

### skills\arch\validate_templates.py
```
  class ValidationResult()
  def print_status(message, status) -> None
  def _load_template_content_cached(path_str, mtime, size) -> str
  def load_template_content(template_path) -> str
  def extract_headings(content) -> list[str]
  def load_contracts(contracts_path) -> Optional[dict[str, Any]]
  def validate_required_headings(template_name, template_path, contract_headings) -> tuple[bool, list[str]]
  def _extract_section_content(content, section_name) -> Optional[str]
  def _calculate_line_overlap(text1, text2) -> float
  def check_duplicate_logic(fast_content, deep_content) -> list[tuple[str, float, str, str]]
  def validate_template_chain(chain) -> tuple[bool, str]
  def _validate_template_dir(template_dir) -> None
  def validate_all(template_dir) -> int
  def main() -> None
```

### skills\code\resources\validate_docs.py
```
  class DocumentationValidator()
    def __init__(self, docs_dir)
    def validate(self)
```

### skills\code-review\__lib\__init__.py
```
  (empty)
```

### skills\code-review\__lib\review_session.py
```
  class ReviewSession()
    def __init__(self, base_dir)
    def setup(self, target) -> None
    def _write_work(self, target) -> None
    def get_session_dir(self) -> str
    def write_findings(self, findings) -> None
    def write_review(self, review) -> None
```

### skills\code-review\tests\__init__.py
```
  (empty)
```

### skills\code-review\tests\test_review_session.py
```
  def temp_base_dir()
  def test_review_session_initialization(temp_base_dir)
  def test_setup_creates_session_dir(temp_base_dir)
  def test_setup_with_target_空文件(temp_base_dir)
  def test_get_session_dir_returns_string(temp_base_dir)
  def test_write_findings(temp_base_dir)
  def test_write_review(temp_base_dir)
```

### skills\code_v3.0\__lib\__init__.py
```
  (empty)
```

### skills\code_v3.0\__lib\checklist.py
```
  class ChecklistQuestion()
  class ValidationResult()
  class ChecklistValidationError(Exception)
  def _normalize_answer_keys(answers) -> dict[int, str]
  def validate_checklist(answers) -> ValidationResult
  def validate_checklist_answers(answers) -> dict[str, Any]
  def log_checklist_answers(answers, evidence_dir, terminal_id) -> Path | None
  def main()
```

### skills\code_v3.0\__lib\gap_loader.py
```
  def _get_terminal_id() -> str
  def load_test_gaps(project_root) -> dict | None
  def format_gap_summary(gap_data) -> str
```

### skills\code_v3.0\__lib\state_encryption.py
```
  class StateEncryptionError(Exception)
  def _redact_sensitive_data(data) -> Any
  def _generate_key_from_password(password, salt) -> bytes
  def _get_or_create_encryption_key(state_file) -> bytes
  def _set_strict_permissions(file_path) -> None
  def encrypt_state(state, output_file) -> None
  def decrypt_state(input_file) -> Dict[str, Any]
  def is_state_encrypted(state_file) -> bool
  def encrypt_existing_state(plaintext_file) -> Path
  def verify_gdpr_compliance(state_file) -> Dict[str, bool]
```

### skills\code_v3.0\__lib\task_detector.py
```
  class TaskType(Enum)
  class TaskDetectionResult()
  def detect_task_type(query) -> TaskDetectionResult
  def log_detection_decision(result, query, project_root) -> Path
```

### skills\code_v3.0\conftest.py
```
  def _setup_context7_mocks()
```

### skills\code_v3.0\hooks\code_phase_ledger.py
```
  def get_verified_identity(session_id) -> dict | None
  def _get_terminal_id(session_id) -> str
  def _ledger_path(session_id) -> Path
  def read_phase_ledger(session_id) -> dict[str, Any] | None
  def write_phase_marker(phase_name, payload, session_id) -> None
  def reset_ledger(session_id) -> None
```

### skills\code_v3.0\hooks\detect_continuous_mode.py
```
  def detect_continuous_mode(user_query) -> bool
  def set_continuous_mode_flag(enabled) -> None
  def set_environment_flag(enabled) -> None
  def main()
```

### skills\code_v3.0\hooks\PostToolUse_breadcrumb_tracker.py
```
  def _is_pytest(cmd) -> bool
  def _is_smoke(cmd) -> bool
  def _is_full_suite(cmd) -> bool
  def _audit_exit_from_cmd(cmd, stdout, stderr, exit_code) -> int | None
  def detect_completed_step(tool_name, tool_input) -> str | None
  def main() -> None
```

### skills\code_v3.0\hooks\PreToolUse_plan_consumer_gate.py
```
  def _add_import_paths() -> None
  def _should_skip_for_path(file_path) -> bool
  def _required_phase() -> int
  def run(payload) -> dict | None
  def main() -> None
```

### skills\code_v3.0\hooks\SessionStart_breadcrumb_init.py
```
  def main()
```

### skills\code_v3.0\hooks\Stop_code_phase_gate.py
```
  def _ledger_path() -> Path
  def _read_ledger() -> dict | None
  def _check_fast_mode() -> bool
  def main() -> None
```

### skills\code_v3.0\hooks\validate_code_phase_order.py
```
  def main()
```

### skills\code_v3.0\resources\validate_docs.py
```
  class DocumentationValidator()
    def __init__(self, docs_dir)
    def validate(self)
```

### skills\code_v3.0\scripts\__init__.py
```
  (empty)
```

### skills\code_v3.0\scripts\behavior_gates_checker.py
```
  class BehaviorGatesChecker()
    def __init__(self, config_path)
    def _compile_patterns(self) -> None
    def check_text(self, text, context) -> dict
    def _detect_tdd_phase(self, text) -> Literal['red', 'implementation', 'unknown']
    def _check_agreement_exclusions(self, text) -> list[str]
    def _check_guidance_exclusions(self, text) -> list[str]
  def main() -> int
```

### skills\code_v3.0\scripts\fix_state_paths.py
```
  def detect_git_bash_paths(data) -> list[str]
  def normalize_git_bash_path(path) -> str
  def fix_paths_in_data(data) -> tuple[Any, int]
  def fix_paths_in_file_with_rollback(file_path, backup, simulate_error) -> dict
  def fix_paths_in_file(file_path, backup) -> int
  def find_state_files(state_dir) -> list[Path]
  def fix_paths_in_directory(state_dir, backup, dry_run) -> dict
  def fix_paths_main(state_dir, backup, dry_run) -> dict
  def main() -> int
```

### skills\code_v3.0\scripts\normalize_paths_before_run.py
```
  def normalize_paths_before_run(command) -> str
```

### skills\code_v3.0\scripts\pattern_validation.py
```
  class PatternIssue(NamedTuple)
  def validate_detector_patterns(patterns, context_keywords) -> list[PatternIssue]
```

### skills\code_v3.0\scripts\phase3_edge_constitutional_tests.py
```
  def test_empty_inputs()
  def test_malformed_structures()
  def test_single_branch_code()
  def test_concurrent_flags()
  def test_constitutional_compliance()
  def test_environment_variable_override()
```

### skills\code_v3.0\scripts\phase3_performance_validation.py
```
  def test_got_performance()
  def test_tot_performance()
  def test_opt_out_performance()
```

### skills\code_v3.0\scripts\phase5_integration_tests.py
```
  def run_skill_test(skill_path, skill_name)
  def test_all_phase1_and_phase2_skills()
  def test_cross_skill_consistency()
```

### skills\code_v3.0\scripts\phase6_7_deployment_certification.py
```
  def run_deployment_readiness_checks()
  def run_final_certification()
  def generate_release_summary()
```

### skills\code_v3.0\scripts\repair_markers.py
```
  def detect_stale_markers(phase_mgr) -> list[str]
  def invalidate_stale_markers(phase_mgr) -> int
  def repair_markers_dry_run(phase_mgr) -> str
  def repair_markers_interactive(phase_mgr, confirm) -> dict
  def repair_stale_markers(phase_mgr, stale_markers, confirm, dry_run) -> dict
  def main() -> int
```

### skills\code_v3.0\scripts\status_report.py
```
  def generate_status_report(evidence_mgr, phase_mgr) -> str
  def _format_phase_status(phase_mgr) -> list[str]
  def _format_task_progress(evidence_mgr) -> list[str]
  def _format_missing_evidence(evidence_mgr) -> list[str] | None
  def _format_terminal_ownership(phase_mgr) -> list[str]
```

### skills\code_v3.0\scripts\validate_done_claim.py
```
  def calculate_tsr(evidence_mgr) -> dict
  def validate_done_claim(evidence_mgr, task_ids, tsr_threshold) -> bool
```

### skills\code_v3.0\scripts\validate_phase_transition.py
```
  def validate_phase_transition(target_phase, phase_mgr) -> bool
```

### skills\code_v3.0\scripts\verify_phase2_opt_out_tests.py
```
  def run_tests(skill_name)
  def main()
```

### skills\code_v3.0\scripts\verify_plan_compliance.py
```
  def extract_planned_tests(plan_path) -> int
  def extract_implemented_tests(test_path) -> int
```

### skills\code_v3.0\test_delegation_debug.py
```
  (empty)
```

### skills\code_v3.0\test_tdd_block.py
```
  (empty)
```

### skills\code_v3.0\tests\conftest.py
```
  def project_root() -> Generator[Path, None, None]
  def mock_time(project_root) -> Generator
  def evidence_dir(project_root) -> Path
  def clean_evidence_dir(project_root) -> Generator[Path, None, None]
  def enable_evidence_tracking() -> Generator[None, None, None]
  class PathLookupCache()
    def __init__(self) -> None
    def get(self, key) -> Path | None
    def put(self, key, value) -> None
    def clear(self) -> None
    def __enter__(self) -> 'PathLookupCache'
    def __exit__(self, exc_type, exc_val, exc_tb) -> None
  def cached_path_lookup() -> Generator[PathLookupCache, None, None]
  def isolated_state_dir(request) -> Generator[Path, None, None]
  def test_suite_performance()
  def test_performance_regression()
  def pytest_configure(config)
  def pytest_collection_modifyitems(config, items)
```

### skills\code_v3.0\tests\test_behavior_gates_checker.py
```
  class TestAgreementPatternDetection()
    def checker(self, tmp_path)
    def test_agreement_direct_commitment(self, checker)
    def test_agreement_multiple_commitments(self, checker)
    def test_agreement_case_insensitive(self, checker)
    def test_agreement_not_detected_for_guidance(self, checker)
  class TestGuidancePatternDetection()
    def checker(self, tmp_path)
    def test_guidance_directive(self, checker)
    def test_guidance_multiple_directives(self, checker)
    def test_guidance_case_insensitive(self, checker)
  class TestAgreementExclusions()
    def checker(self, tmp_path)
    def test_exclusion_test_writing(self, checker)
    def test_exclusion_guidance_and_planning(self, checker)
    def test_exclusion_questions(self, checker)
    def test_exclusion_delegation(self, checker)
  class TestGuidanceExclusions()
    def checker(self, tmp_path)
    def test_exclusion_test_suggestions(self, checker)
    def test_exclusion_explanations(self, checker)
  class TestTDDContextAwareness()
    def checker(self, tmp_path)
    def test_tdd_red_phase_detection(self, checker)
    def test_tdd_implementation_phase_detection(self, checker)
    def test_tdd_phase_unknown(self, checker)
    def test_tdd_context_recommendation_red(self, checker)
  class TestRecommendations()
    def checker(self, tmp_path)
    def test_recommendation_for_implementation_commitment(self, checker)
    def test_no_recommendation_for_guidance(self, checker)
  class TestFalsePositivePrevention()
    def checker(self, tmp_path)
    def test_false_positive_showing_results(self, checker)
    def test_false_positive_you_can_explanation(self, checker)
    def test_false_positive_test_writing(self, checker)
  class TestEdgeCases()
    def checker(self, tmp_path)
    def test_empty_text(self, checker)
    def test_text_with_only_whitespace(self, checker)
    def test_multiple_exclusions(self, checker)
    def test_agreement_and_guidance_both_present(self, checker)
  class TestCLIAPI()
    def test_cli_with_simple_text(self, tmp_path, capsys)
```

### skills\code_v3.0\tests\test_checklist.py
```
  class TestChecklistQuestions()
    def test_five_questions_defined(self)
    def test_questions_numbered_correctly(self)
    def test_all_questions_required(self)
    def test_questions_have_text(self)
  class TestChecklistValidation()
    def test_validate_checklist_function_exists(self)
    def test_validate_all_answers_provided_passes(self)
    def test_validate_empty_answer_fails(self)
    def test_validate_whitespace_only_answer_fails(self)
    def test_validate_missing_question_fails(self)
    def test_validate_multiple_empty_answers(self)
    def test_validate_returns_validation_result(self)
  class TestChecklistBypass()
    def test_no_checklist_flag_documented(self)
    def test_no_checklist_bypass_description(self)
    def test_no_checklist_usage_example(self)
  class TestChecklistEvidenceLogging()
    def setup_method(self)
    def teardown_method(self)
    def test_log_checklist_answers_function_exists(self)
    def test_log_checklist_creates_evidence_directory(self)
    def test_log_checklist_creates_pre_execution_file(self)
    def test_log_checklist_contains_all_questions(self)
    def test_log_checklist_contains_answers(self)
    def test_log_checklist_contains_timestamp(self)
    def test_log_checklist_contains_feature_description(self)
    def test_log_checklist_appends_to_existing_file(self)
    def test_log_checklist_handles_empty_answers(self)
    def test_log_checklist_returns_file_path(self)
```

### skills\code_v3.0\tests\test_checklist_integration.py
```
  class TestPreExecutionChecklist()
    def test_checklist_step_in_workflow(self)
    def test_checklist_step_before_analyze_query_intent(self)
    def test_no_checklist_flag_exists(self)
    def test_checklist_documented_in_skill(self)
    def test_checklist_questions_defined(self)
    def test_checklist_validation_module_exists(self)
    def test_checklist_validate_function_exists(self)
```

### skills\code_v3.0\tests\test_concurrent_invocation.py
```
  class TestConcurrentSkillInvocation()
    def test_concurrent_code_and_s_both_enforce(self, tmp_path, mock_time)
    def test_skill_call_doesnt_affect_other_skill_intent(self, tmp_path, mock_time)
    def test_intent_file_write_write_race_last_wins(self, tmp_path, mock_time)
    def test_concurrent_invocation_with_terminal_isolation(self, tmp_path, mock_time)
```

### skills\code_v3.0\tests\test_context7_client.py
```
  class TestContext7ResolverBasicResolution()
    def mock_mcp_tool(self)
    def test_resolve_library_name_returns_library_id(self, mock_mcp_tool)
    def test_resolve_library_name_with_query(self, mock_mcp_tool)
  class TestBreakingChangeDetectorBasicQueries()
    def mock_query_docs(self)
    def test_query_breaking_changes_queries_context7(self, mock_query_docs)
    def test_query_breaking_changes_filters_changelog_content(self, mock_query_docs)
  class TestRateLimitHandling()
    def mock_mcp_with_rate_limit(self)
    def test_rate_limit_triggers_exponential_backoff(self, mock_mcp_with_rate_limit)
    def test_rate_limit_respects_max_retries(self)
    def test_exponential_backoff_increments_properly(self)
  class TestResultCaching()
    def test_duplicate_queries_use_cache(self)
    def test_cache_key_includes_query_parameter(self)
    def test_cache_can_be_cleared(self)
  class TestErrorHandling()
    def test_unknown_library_returns_empty_result(self)
    def test_service_unavailable_raises_error(self)
    def test_malformed_response_handling(self)
```

### skills\code_v3.0\tests\test_context7_rate_limiter.py
```
  def reset_singleton_state()
  class TestSharedRateLimitTracking()
    def test_multiple_tracks_share_rate_limit_state(self)
    def test_rate_limit_threshold_shared_across_tracks(self)
    def test_explorer_phase_never_blocks(self)
    def test_rate_limit_reset_after_time_window(self)
  class TestBatchQueryOptimization()
    def test_similar_queries_are_batched(self)
    def test_batch_window_groups_queries_by_time(self, mock_time)
    def test_different_libraries_not_batched(self)
    def test_batch_query_returns_same_result_to_all_requesters(self)
  class TestResultCachingAcrossProjects()
    def test_cache_is_shared_across_tracks(self)
    def test_cache_key_includes_library_name(self)
    def test_cache_can_be_cleared_globally(self)
    def test_cache_persistence_across_multiple_projects(self)
  class TestRateLimitDetectionAndBackoff()
    def test_rate_limit_error_detected_from_api_response(self)
    def test_backoff_triggered_after_rate_limit(self)
    def test_exponential_backoff_increments_on_repeated_limits(self)
    def test_max_retries_respected_during_backoff(self)
  class TestGracefulFallbackToLocalVersionChecking()
    def test_fallback_triggered_when_rate_limit_hit(self)
    def test_fallback_returns_local_version_when_available(self)
    def test_fallback_returns_graceful_degradation_when_unavailable(self)
    def test_fallback_disabled_when_flag_false(self)
  class TestNeverBlocksExplorePhase()
    def test_explore_query_never_raises_exception(self)
    def test_explore_always_returns_fallback_on_rate_limit(self)
    def test_explore_returns_partial_results_on_error(self)
    def test_explore_phase_bypasses_rate_limit_when_critical(self)
  class TestSingletonPattern()
    def test_rate_limiter_is_singleton(self)
    def test_singleton_state_persists_across_imports(self)
```

### skills\code_v3.0\tests\test_core_plan_integration.py
```
  class TestCorePlanIntegration()
    def setup_method(self)
    def teardown_method(self)
    def test_all_three_modules_available(self)
    def test_evidence_tracking_creates_artifacts(self)
    def test_checklist_validates_non_empty_answers(self)
    def test_task_detector_classifies_implementation_tasks(self)
    def test_task_detector_classifies_research_tasks(self)
    def test_evidence_directory_shared_across_features(self)
    def test_checklist_accepts_valid_answers(self)
    def test_task_detector_provides_reasoning(self)
    def test_evidence_tracking_includes_timestamps(self)
    def test_checklist_evidence_includes_all_questions(self)
    def test_ralph_auto_detection_logs_decision(self)
    def test_workflow_end_to_end(self)
    def test_no_feature_conflicts(self)
    def test_solo_dev_constraints_satisfied(self)
    def test_evidence_files_have_unique_names(self)
  class TestCorePlanRollback()
    def setup_method(self)
    def teardown_method(self)
    def test_evidence_cleanup_removes_old_artifacts(self)
    def test_disabling_features_removes_functionality(self)
```

### skills\code_v3.0\tests\test_discovery.py
```
  class TestDiscovery()
    def __init__(self, project_root)
    def run_pytest_with_coverage(self, cov_targets, verbose, timeout) -> dict[str, Any]
    def parse_coverage_report(self, coverage_file) -> dict[str, Any]
    def analyze_coverage_gaps(self, coverage_data) -> list[dict[str, Any]]
    def generate_discovery_report(self, timeout) -> str
  def test_discovery_basic()
  def test_run_pytest_with_coverage()
  def test_parse_coverage_report_missing_file()
  def test_analyze_coverage_gaps_empty_data()
  def test_generate_discovery_report()
```

### skills\code_v3.0\tests\test_env_var_edge_cases.py
```
  class TestTTLNegativeValue()
    def test_negative_ttl_uses_default_90s(self)
    def test_negative_10_ttl_rejected(self)
  class TestTTLZeroValue()
    def test_zero_ttl_uses_default_90s(self)
  class TestTTLNonNumeric()
    def test_non_numeric_ttl_uses_default_90s(self)
    def test_non_numeric_with_digits_uses_default(self)
  class TTLEmptyString()
    def test_empty_string_uses_default_90s(self)
    def test_empty_string_treated_same_as_unset(self)
  class TestTVeryLargeTTL()
    def test_very_large_ttl_accepted_with_warning(self, caplog)
    def test_large_ttl_warning_message_content(self, caplog)
  class TestTTLDefaultBehavior()
    def test_unset_env_var_uses_default_90s(self)
  class TestTTLValidationIntegration()
    def test_valid_ttl_60_works_correctly(self)
    def test_valid_ttl_120_works_correctly(self)
```

### skills\code_v3.0\tests\test_evidence.py
```
  def temp_state_dir()
  class TestEvidenceManager()
    def test_ledger_creation(self, temp_state_dir)
    def test_record_red(self, temp_state_dir)
    def test_record_green(self, temp_state_dir)
    def test_can_mark_done_missing_evidence(self, temp_state_dir)
    def test_mark_done_success(self, temp_state_dir)
    def test_mark_done_failure(self, temp_state_dir)
  class TestImplementationVerification()
    def test_verify_implementation_exists_all_files_present(self, temp_state_dir)
    def test_verify_implementation_exists_missing_impl_file(self, temp_state_dir)
    def test_verify_implementation_exists_missing_test_file(self, temp_state_dir)
    def test_verify_implementation_exists_multiple_missing(self, temp_state_dir)
    def test_verify_implementation_unknown_task(self, temp_state_dir)
  class TestMarkDoneWithVerification()
    def test_mark_done_blocks_on_missing_impl_file(self, temp_state_dir)
    def test_mark_done_succeeds_with_all_files_present(self, temp_state_dir)
  class TestFileLocking()
    def test_load_ledger_locked_returns_data(self, temp_state_dir)
    def test_save_ledger_locked_persists_data(self, temp_state_dir)
    def test_mark_done_uses_locked_methods(self, temp_state_dir)
```

### skills\code_v3.0\tests\test_evidence_manager_integration.py
```
  def evidence_availability()
  class TestEvidenceManagerTDDIntegration()
    def setup_method(self)
    def teardown_method(self)
    def test_record_tdd_evidence_red_phase(self)
    def test_record_tdd_evidence_green_phase(self)
    def test_record_tdd_evidence_refactor_phase(self)
    def test_record_tdd_evidence_verify_phase(self)
    def test_record_tdd_evidence_invalid_phase_raises_error(self)
  class TestEvidenceWriterIntegration()
    def setup_method(self)
    def teardown_method(self)
    def test_generate_evidence_artifact_uses_evidence_manager(self)
    def test_generate_evidence_artifact_fallback_to_markdown(self)
```

### skills\code_v3.0\tests\test_fix_state_paths.py
```
  [error]
```

### skills\code_v3.0\tests\test_got_edge_analysis.py
```
  def sample_nodes_with_relationships() -> Dict[str, List[Dict[str, Any]]]
  def nodes_with_cycle() -> Dict[str, List[Dict[str, Any]]]
  def contradictory_nodes() -> Dict[str, List[Dict[str, Any]]]
  def test_analyze_supports_relationships(sample_nodes_with_relationships)
  def test_analyze_contradicts_relationships(contradictory_nodes)
  def test_detect_cycles_in_graph(nodes_with_cycle)
  def test_break_cycles_removes_weakest_edges(nodes_with_cycle)
  def test_handle_unrelated_nodes(sample_nodes_with_relationships)
  def test_edge_analysis_with_empty_nodes()
  def test_edge_analysis_with_single_node()
  def test_detect_cycles_in_acyclic_graph(sample_nodes_with_relationships)
  def test_multiple_cycles_detection()
```

### skills\code_v3.0\tests\test_got_node_extraction.py
```
  def sample_plan_with_architecture() -> str
  def sample_plan_minimal() -> str
  def sample_plan_empty_architecture() -> str
  def test_extract_constraints_from_sample_plan(sample_plan_with_architecture)
  def test_extract_ideas_from_sample_plan(sample_plan_with_architecture)
  def test_extract_risks_from_sample_plan(sample_plan_with_architecture)
  def test_handle_minimal_plan(sample_plan_minimal)
  def test_handle_empty_architecture(sample_plan_empty_architecture)
  def test_node_ids_are_unique(sample_plan_with_architecture)
  def test_node_ids_follow_pattern(sample_plan_with_architecture)
  def test_source_lines_are_tracked(sample_plan_with_architecture)
```

### skills\code_v3.0\tests\test_got_tot_integration.py
```
  def complete_plan_document()
  def implementation_code()
  def test_end_to_end_got_then_tot(complete_plan_document, implementation_code)
  def test_got_constraints_influence_tot_branching()
  def test_got_risks_detected_in_tot_branches()
  def test_got_tot_consistency()
  def test_quality_improvement_with_both_enabled()
  def test_workflow_integration()
  def test_disabled_got_tot_fallback()
  def test_memory_consistency_across_phases()
  def test_complex_plan_analysis()
  def test_empty_plan_and_code_handling()
```

### skills\code_v3.0\tests\test_hook_execution_order.py
```
  class TestHookExecutionOrder()
    def setup_method(self)
    def teardown_method(self)
    def test_pre_execution_checklist_runs_before_detection(self)
    def test_tdd_evidence_tracking_runs_after_task_detection(self)
    def test_complete_workflow_execution_order(self)
    def test_concurrent_evidence_writing_does_not_corrupt_state(self)
  class TestClaudeCodeHookExecutionOrder()
    def setup_method(self)
    def teardown_method(self)
    def _mock_hook_event(self, hook_name, event_data) -> dict
    def test_user_prompt_submit_fires_first(self)
    def test_pre_tool_use_fires_after_user_prompt_submit(self)
    def test_stop_hook_fires_last(self)
    def test_complete_hook_sequence_user_prompt_submit_to_stop(self)
    def test_all_three_hooks_fire_in_every_request(self)
    def test_multiple_pre_tool_use_events_allowed(self)
    def test_hook_event_timestamps_are_recorded(self)
    def test_hook_event_data_preservation(self)
    def test_out_of_order_sequence_fails_verification(self)
```

### skills\code_v3.0\tests\test_import_check.py
```
  (empty)
```

### skills\code_v3.0\tests\test_intent_edge_cases.py
```
  class TestEmptyIntentFile()
    def test_empty_intent_file_treated_as_missing(self, tmp_path)
    def test_whitespace_only_intent_file(self, tmp_path)
  class TestInvalidJSON()
    def test_invalid_json_treated_as_missing(self, tmp_path)
    def test_malformed_json_structure(self, tmp_path)
  class TestMissingCreatedAtField()
    def test_missing_created_at_fallback_to_iso_timestamp(self, tmp_path)
  class TestWrongTypeForCreatedAt()
    def test_wrong_type_created_at_fallback_to_iso_timestamp(self, tmp_path)
    def test_null_created_at_fallback_to_iso_timestamp(self, tmp_path)
```

### skills\code_v3.0\tests\test_isolated_state_dir.py
```
  class TestIsolatedStateDirFixture()
    def test_isolated_state_dir_fixture_exists(self)
    def test_isolated_state_dir_returns_path(self, isolated_state_dir)
    def test_isolated_state_dir_creates_unique_directory(self, isolated_state_dir)
    def test_isolated_state_dir_directory_exists(self, isolated_state_dir)
    def test_isolated_state_dir_isolated_per_test(self, isolated_state_dir)
    def test_parallel_execution_with_isolated_state_dir(self, isolated_state_dir)
    def test_ttl_tests_use_isolated_fixtures(self, isolated_state_dir)
  class TestIsolatedStateDirBehavior()
    def test_state_dir_is_writable(self, isolated_state_dir)
    def test_state_dir_isolated_between_tests(self, isolated_state_dir)
```

### skills\code_v3.0\tests\test_library_scanner.py
```
  def temp_dir()
  class TestImportScanner()
    def test_detects_simple_import(self, temp_dir)
    def test_detects_from_import(self, temp_dir)
    def test_detects_mixed_imports(self, temp_dir)
    def test_ignores_local_imports(self, temp_dir)
    def test_handles_empty_file(self, temp_dir)
    def test_scans_multiple_files(self, temp_dir)
    def test_deduplicates_imports(self, temp_dir)
    def test_filters_standard_library(self, temp_dir)
  class TestDependencyFileParser()
    def test_parses_requirements_txt_simple(self, temp_dir)
    def test_parses_requirements_txt_with_versions(self, temp_dir)
    def test_parses_requirements_txt_with_comments_and_blank_lines(self, temp_dir)
    def test_handles_missing_requirements_txt(self, temp_dir)
    def test_parses_pyproject_toml_dependencies(self, temp_dir)
    def test_parses_pyproject_toml_optional_dependencies(self, temp_dir)
    def test_handles_missing_pyproject_toml(self, temp_dir)
    def test_handles_malformed_pyproject_toml(self, temp_dir)
    def test_parses_all_sources(self, temp_dir)
  class TestLibraryDetector()
    def test_combines_imports_and_dependencies(self, temp_dir)
    def test_handles_imports_without_versions(self, temp_dir)
    def test_scans_directory_recursively(self, temp_dir)
    def test_handles_missing_files_gracefully(self, temp_dir)
    def test_returns_empty_dict_for_no_inputs(self, temp_dir)
    def test_deduplicates_across_sources(self, temp_dir)
```

### skills\code_v3.0\tests\test_modernization_section_generator.py
```
  class TestModernizationSectionGeneratorBasicFormatting()
    def test_generates_modernization_considerations_section(self)
    def test_section_has_three_subsections(self)
  class TestModernizationSectionGeneratorPriorityFormatting()
    def test_formats_p0_priority_divergences(self)
    def test_formats_p1_priority_divergences(self)
    def test_formats_p2_priority_divergences(self)
    def test_orders_divergences_by_priority(self)
  class TestModernizationSectionGeneratorRecommendations()
    def test_recommends_existing_patterns_by_default(self)
    def test_recommends_modern_for_p0_security(self)
    def test_provides_clear_recommendation_text(self)
  class TestModernizationSectionGeneratorUserChoiceOptions()
    def test_formats_user_choice_with_checkboxes(self)
    def test_includes_existing_pattern_option(self)
    def test_includes_modern_pattern_option(self)
  class TestModernizationSectionGeneratorContext7Urls()
    def test_includes_migration_links(self)
    def test_handles_missing_context7_url(self)
    def test_formats_context7_urls_as_clickable_links(self)
  class TestModernizationSectionGeneratorEmptyFindings()
    def test_handles_empty_findings_gracefully(self)
    def test_empty_findings_message(self)
    def test_handles_missing_divergences_key(self)
  class TestModernizationSectionGeneratorOutputFormat()
    def test_returns_string_type(self)
    def test_output_is_valid_markdown(self)
    def test_section_is_not_empty(self)
```

### skills\code_v3.0\tests\test_normalize_paths.py
```
  class TestNormalizePath()
    def test_git_bash_to_windows(self)
    def test_windows_path_unchanged(self)
    def test_relative_path_resolved(self)
    def test_empty_path(self)
  class TestNormalizePathsInCommand()
    def test_single_path(self)
    def test_multiple_paths(self)
    def test_no_paths(self)
  class TestPathTypeDetection()
    def test_is_git_bash_path(self)
    def test_is_windows_path(self)
  class TestNormalizePathExceptionHandling()
    def test_oserror_fallback_to_normalized_path(self)
    def test_runtime_error_fallback_to_normalized_path(self)
    def test_value_error_fallback_to_normalized_path(self)
    def test_resolve_success_returns_resolved_path(self)
  class TestNormalizePathListEdgeCases()
    def test_empty_list_returns_empty_list(self)
    def test_list_with_none_values(self)
    def test_list_with_empty_strings(self)
    def test_list_with_mixed_edge_cases(self)
    def test_list_with_all_none_values(self)
    def test_list_with_all_empty_strings(self)
```

### skills\code_v3.0\tests\test_normalize_paths_before_run.py
```
  [error]
```

### skills\code_v3.0\tests\test_opt_out_flags.py
```
  def sample_plan_with_architecture()
  def sample_trace_code()
  def test_got_enabled_by_default(sample_plan_with_architecture)
  def test_tot_enabled_by_default(sample_trace_code)
  def test_no_got_flag_disables_got(sample_plan_with_architecture)
  def test_no_tot_flag_disables_tot(sample_trace_code)
  def test_flags_are_independent()
  def test_default_behavior_quality_first()
  def test_no_got_does_not_affect_tot(sample_trace_code)
  def test_no_tot_does_not_affect_got(sample_plan_with_architecture)
  def test_flag_parsing_conceptual()
  def test_got_tot_integration_workflow()
```

### skills\code_v3.0\tests\test_path_caching.py
```
  class TestPathCaching()
    def test_cached_path_lookup_fixture_exists(self, cached_path_lookup)
    def test_cached_path_reduces_stat_calls(self, cached_path_lookup)
    def test_cached_path_invalidates_on_mutation(self, cached_path_lookup)
    def test_cached_path_supports_common_operations(self, cached_path_lookup)
  class TestPathCachingPerformance()
    def test_multiple_checks_use_cache(self, cached_path_lookup)
    def test_cache_invalidation_works_correctly(self, cached_path_lookup)
```

### skills\code_v3.0\tests\test_path_io_caching.py
```
  class TestPathIOCaching()
    def temp_state_dir(self) -> Generator[Path, None, None]
    def test_cached_path_lookup_fixture_exists(self, temp_state_dir)
    def test_memoization_reduces_filesystem_calls(self, temp_state_dir)
    def test_cache_can_be_cleared_between_tests(self, temp_state_dir)
    def test_path_resolution_with_different_terminal_ids(self, temp_state_dir)
    def test_path_resolution_with_different_session_ids(self, temp_state_dir)
    def test_shared_state_path_is_consistent(self, temp_state_dir)
```

### skills\code_v3.0\tests\test_pattern_validation.py
```
  class TestPatternIssue()
    def test_pattern_issue_creation(self)
    def test_pattern_issue_severity_levels(self)
  class TestValidateDetectorPatterns()
    def test_validate_no_patterns(self)
    def test_validate_no_issues(self)
    def test_validate_context_conflict_exact_match(self)
    def test_validate_context_conflict_partial_match(self)
    def test_validate_context_conflict_case_insensitive(self)
    def test_validate_overmatching_common_words(self)
    def test_validate_regex_syntax_error(self)
    def test_validate_multiple_issues(self)
    def test_validate_real_world_patterns(self)
    def test_validate_word_boundary_recommendations(self)
    def test_validate_complex_regex_valid(self)
    def test_validate_empty_pattern(self)
    def test_validate_whitespace_pattern(self)
    def test_validate_multiple_patterns_independent(self)
  class TestPatternValidationIntegration()
    def test_unverified_stance_detector_patterns(self)
    def test_recommended_pattern_fixes(self)
```

### skills\code_v3.0\tests\test_performance_baseline.py
```
  class TestPerformanceBaselineConfiguration()
    def test_pytest_timeout_marker_exists(self)
    def test_pytest_timeout_warning_threshold(self)
  class TestPerformanceBaselineTracking()
    def test_baseline_execution_time_recorded(self)
    def test_baseline_has_acceptable_threshold(self)
  class TestPerformanceRegressionDetection()
    def test_performance_regression_test_exists(self)
    def test_performance_regression_uses_baseline(self)
    def test_performance_regression_threshold(self)
  class TestPerformanceTimeoutBehavior()
    def test_timeout_marker_enforces_limit(self)
```

### skills\code_v3.0\tests\test_phase_ledger.py
```
  class TestPhaseLedger()
    def setup_method(self) -> None
    def teardown_method(self) -> None
    def test_write_and_read(self) -> None
    def test_append_only_no_clobber(self) -> None
    def test_append_only_with_payload_overwrites(self) -> None
    def test_multiple_phases_independent(self) -> None
    def test_reset(self) -> None
  class TestStopGateExitCodes()
    def _run_gate(self, phases) -> tuple[int, str, str]
    def test_no_ledger_allows_stop(self) -> None
    def test_all_gates_pass_exit_0(self) -> None
    def test_missing_hard_gate_blocks_exit_2(self) -> None
    def test_advisory_missing_does_not_block(self) -> None
    def test_fast_mode_skips_full_suite(self) -> None
```

### skills\code_v3.0\tests\test_phase_state.py
```
  def temp_state_dir()
  class TestPhaseStateManager()
    def test_state_creation(self, temp_state_dir)
    def test_mark_phase_complete(self, temp_state_dir)
    def test_is_phase_valid(self, temp_state_dir)
    def test_invalidate_phase(self, temp_state_dir)
    def test_build_ownership(self, temp_state_dir)
    def test_get_all_phases_status(self, temp_state_dir)
  class TestGitHash()
    def test_get_git_head_hash(self)
  class TestGitHashExceptionHandling()
    def test_timeout_expired_returns_none(self)
    def test_file_not_found_returns_none(self)
    def test_generic_exception_propagates(self)
  class TestTerminalIdSanitization()
    def test_sanitization_removes_dangerous_chars(self)
    def test_sanitization_preserves_safe_chars(self)
    def test_sanitization_fallback_to_default(self)
    def test_terminal_scoped_state_paths(self)
```

### skills\code_v3.0\tests\test_phase_state_metadata.py
```
  def temp_state_dir()
  class TestPhaseMetadataHandling()
    def test_mark_phase_complete_with_metadata(self, temp_state_dir)
    def test_mark_phase_complete_with_empty_metadata(self, temp_state_dir)
    def test_mark_phase_complete_with_none_metadata(self, temp_state_dir)
```

### skills\code_v3.0\tests\test_plan_consumer_guard.py
```
  def test_blocks_non_ready_plan(tmp_path) -> None
  def test_allows_ready_plan_for_code(tmp_path) -> None
  def test_allows_ready_plan_for_tdd_without_implementation_ready(tmp_path) -> None
  def test_allows_ready_phased_plan_for_code_phase_one(tmp_path) -> None
  def test_blocks_code_when_required_phase_exceeds_validated_readiness(tmp_path) -> None
  def test_implementation_ready_plan_is_consumable_by_tdd(tmp_path) -> None
  def test_discovers_project_local_plan_conservatively(tmp_path) -> None
```

### skills\code_v3.0\tests\test_plan_updater.py
```
  class TestPlanUpdaterReading()
    def test_read_nonexistent_plan(self)
    def test_read_valid_plan(self)
    def test_parse_tasks_with_status_markers(self)
  class TestPlanUpdaterStatusUpdates()
    def test_update_single_task_status(self)
    def test_update_task_with_existing_status(self)
    def test_update_nonexistent_task(self)
    def test_update_task_status_from_started_to_finished(self)
    def test_update_multiple_tasks(self)
  class TestPlanUpdaterBackup()
    def test_backup_created_on_update(self)
    def test_restore_from_backup(self)
  class TestConvenienceFunctions()
    def test_update_plan_task_status_function(self)
    def test_get_plan_tasks_function(self)
    def test_get_task_status(self)
  class TestTaskStatusEnum()
    def test_status_values(self)
  class TestFileLock()
    def test_file_lock_context_manager(self)
    def test_file_lock_timeout(self)
    def test_update_with_lock_success(self)
    def test_update_with_lock_timeout_flag(self)
```

### skills\code_v3.0\tests\test_priority_scorer.py
```
  class TestP0Categorization()
    def test_security_vulnerability_categorized_as_p0(self)
  class TestP1Categorization()
    def test_performance_improvement_categorized_as_p1(self)
  class TestP2Categorization()
    def test_minor_improvement_categorized_as_p2(self)
  class TestPriorityScoreCalculation()
    def test_p0_score_high_range(self)
  class TestConfidenceScoring()
    def test_high_confidence_with_strong_evidence(self)
  class TestEdgeCaseHandling()
    def test_missing_type_field_defaults_to_p2(self)
    def test_unknown_type_defaults_to_p2(self)
  class TestDocumentationRequirements()
    def test_module_docstring_exists(self)
    def test_documentation_mentions_non_blocking_nature(self)
```

### skills\code_v3.0\tests\test_ralph_loop_integration.py
```
  class TestRalphLoopIntegration()
    def test_ralph_loop_flags_in_argument_hint(self)
    def test_ralph_auto_detection_documentation_exists(self)
    def test_ralph_override_flags_documented(self)
    def test_ralph_usage_examples_exist(self)
    def test_ralph_evidence_logging_documented(self)
    def test_ralph_integration_with_detector_module(self)
    def test_ralph_task_type_detection_works(self)
    def test_ralph_confidence_scores_valid(self)
    def test_ralph_reasoning_provided(self)
  class TestTaskDetection()
    def test_implementation_task_detection_basic(self)
    def test_research_task_detection_basic(self)
    def test_ambiguous_query_defaults_to_research(self)
    def test_multiple_implementation_keywords(self)
    def test_multiple_research_keywords(self)
    def test_mixed_keywords_tie_defaults_to_research(self)
    def test_mixed_keywords_research_wins(self)
  class TestObservabilityLogging()
    def setup_method(self)
    def teardown_method(self)
    def test_log_detection_decision_function_exists(self)
    def test_log_detection_creates_evidence_file(self)
    def test_log_detection_contains_query(self)
    def test_log_detection_contains_task_type(self)
    def test_log_detection_contains_ralph_loop_decision(self)
    def test_log_detection_contains_confidence(self)
    def test_log_detection_contains_reasoning(self)
    def test_log_detection_appends_to_existing_file(self)
    def test_log_detection_returns_file_path(self)
```

### skills\code_v3.0\tests\test_repair_markers.py
```
  def temp_state_dir()
  def sample_phase_mgr(temp_state_dir)
  class TestRepairMarkersCoreFunctionality()
    def test_repair_markers_detects_stale_markers(self, sample_phase_mgr)
    def test_repair_markers_valid_markers_unchanged(self, sample_phase_mgr)
    def test_repair_markers_invalidates_stale_markers(self, sample_phase_mgr)
  class TestRepairMarkersCommitHashValidation()
    def test_repair_markers_compares_to_git_head(self, sample_phase_mgr)
    def test_repair_markers_handles_missing_git(self, sample_phase_mgr)
    def test_repair_markers_handles_detached_head(self, sample_phase_mgr)
  class TestRepairMarkersConfirmation()
    def test_repair_markers_confirms_before_deletion(self, sample_phase_mgr, capsys)
    def test_repair_markers_auto_confirm_flag(self, sample_phase_mgr)
    def test_repair_markers_dry_run_mode(self, sample_phase_mgr, capsys)
  class TestRepairMarkersEdgeCases()
    def test_repair_markers_empty_state_file(self, temp_state_dir)
    def test_repair_markers_no_markers_present(self, sample_phase_mgr)
    def test_repair_markers_corrupted_state_file(self, temp_state_dir, capsys)
  class TestRepairMarkersIntegration()
    def test_repair_markers_integration(self, sample_phase_mgr)
    def test_repair_markers_cli_invocation(self, sample_phase_mgr)
    def test_repair_markers_with_phase_manager(self, sample_phase_mgr)
  class TestRepairMarkersBatchOperations()
    def test_repair_markers_multiple_stale_markers(self, sample_phase_mgr)
    def test_repair_markers_preserves_valid_markers(self, sample_phase_mgr)
    def test_repair_markers_reports_changes(self, sample_phase_mgr, capsys)
```

### skills\code_v3.0\tests\test_security_edge_cases.py
```
  class TestPermissionErrorHandling()
    def test_permission_error_does_not_leak_path_info(self, tmp_path)
    def test_permission_error_on_save_returns_error_dict(self, tmp_path)
  class TestCorruptedStateHandling()
    def test_corrupted_state_json_causes_fail_closed(self, tmp_path)
    def test_malformed_json_syntax_returns_default(self, tmp_path)
  class TestMaliciousInjectionBlocking()
    def test_malicious_state_injection_blocked(self, tmp_path)
    def test_schema_validation_rejects_wrong_types(self, tmp_path)
  class TestRaceConditionHandling()
    def test_race_condition_concurrent_write(self, tmp_path)
    def test_atomic_write_prevents_partial_data(self, tmp_path)
```

### skills\code_v3.0\tests\test_smoke.py
```
  class TestSmokeCorePlanWorkflow()
    def setup_method(self)
    def teardown_method(self)
    def test_smoke_user_creates_feature_with_evidence(self)
    def test_smoke_user_validates_checklist_before_coding(self)
    def test_smoke_task_detection_auto_enables_ralph_loop(self)
    def test_smoke_task_detection_auto_disables_ralph_loop_for_research(self)
    def test_smoke_end_to_end_core_plan_workflow(self)
```

### skills\code_v3.0\tests\test_solo_dev_compliance.py
```
  class TestSoloDevEvidenceTracking()
    def test_evidence_manager_requires_no_external_approvals(self, tmp_path)
    def test_evidence_ledger_persistence_no_shared_state(self, tmp_path)
  class TestSoloDevAutoDetection()
    def test_no_team_calibration_required(self, tmp_path)
    def test_no_external_dependencies_for_detection(self, tmp_path)
  class TestSoloDevIsolatedEnvironment()
    def test_evidence_operations_work_offline(self, tmp_path)
    def test_no_shared_infrastructure_dependencies(self, tmp_path)
  class TestSoloDevChecklistCompletion()
    def test_single_user_can_complete_tdd_workflow(self, tmp_path)
    def test_no_multi_person_signoff_required(self, tmp_path)
```

### skills\code_v3.0\tests\test_state_encryption.py
```
  class TestStateEncryption()
    def setup_method(self)
    def teardown_method(self)
    def test_encrypt_and_decrypt_state(self)
    def test_file_permissions_enforced(self)
    def test_sensitive_pattern_redaction_api_key(self)
    def test_sensitive_pattern_redaction_password(self)
    def test_sensitive_pattern_redaction_token(self)
    def test_encrypted_file_format(self)
    def test_decrypt_nonexistent_file(self)
    def test_decrypt_invalid_file(self)
    def test_encrypt_existing_plaintext_file(self)
    def test_gdpr_compliance_verification(self)
    def test_gdpr_compliance_with_redacted_data(self)
    def test_multiple_encryptions_same_file(self)
    def test_key_file_permissions(self)
    def test_empty_state_encryption(self)
    def test_nested_data_redaction(self)
    def test_list_data_redaction(self)
```

### skills\code_v3.0\tests\test_status_report.py
```
  def temp_state_dir()
  def sample_evidence_mgr(temp_state_dir)
  def sample_phase_mgr(temp_state_dir)
  class TestStatusReportPhaseStatus()
    def test_status_report_displays_phase_status(self, sample_phase_mgr)
    def test_status_report_shows_all_phases(self, sample_phase_mgr)
    def test_status_report_invalid_phase(self, sample_phase_mgr)
  class TestStatusReportTaskProgress()
    def test_status_report_shows_task_progress(self, sample_evidence_mgr)
    def test_status_report_empty_task_list(self, sample_evidence_mgr)
    def test_status_report_task_ids_visible(self, sample_evidence_mgr)
  class TestStatusReportMissingEvidence()
    def test_status_report_lists_missing_evidence(self, sample_evidence_mgr)
    def test_status_report_formats_missing_evidence_clearly(self, sample_evidence_mgr)
    def test_status_report_complete_task_no_missing_evidence(self, sample_evidence_mgr)
  class TestStatusReportTerminalOwnership()
    def test_status_report_shows_terminal_ownership(self, sample_phase_mgr)
    def test_status_report_shows_lease_expiration(self, sample_phase_mgr)
    def test_status_report_no_ownership(self, sample_phase_mgr)
  class TestStatusReportEmptyLedger()
    def test_status_report_empty_ledger(self, temp_state_dir)
    def test_status_report_returns_string(self, temp_state_dir)
  class TestStatusCommandIntegration()
    def test_status_command_integration(self, sample_evidence_mgr, sample_phase_mgr)
    def test_status_command_none_managers(self)
    def test_status_command_only_evidence_mgr(self, sample_evidence_mgr)
    def test_status_command_only_phase_mgr(self, sample_phase_mgr)
```

### skills\code_v3.0\tests\test_task_026_parallelization_rationale.py
```
  def test_parallelization_section_exists()
  def test_independence_documentation()
  def test_shared_state_documentation()
  def test_fixture_isolation_documentation()
  def test_merge_conflict_warning()
```

### skills\code_v3.0\tests\test_task_detector.py
```
  class TestTaskDetector()
    def test_task_detector_module_exists(self)
    def test_detect_task_type_function_exists(self)
    def test_detect_implementation_task(self)
    def test_detect_refactor_task(self)
    def test_detect_fix_task(self)
    def test_detect_research_task(self)
    def test_detect_analyze_task(self)
    def test_detect_document_task(self)
    def test_confidence_score_range(self)
```

### skills\code_v3.0\tests\test_tot_branch_generation.py
```
  def sample_trace_scenario() -> str
  def simple_linear_trace() -> str
  def conditional_trace() -> str
  def nested_branching_trace() -> str
  def test_generate_branches_for_linear_trace(simple_linear_trace)
  def test_generate_branches_for_conditional_trace(conditional_trace)
  def test_generate_branches_for_nested_traces(nested_branching_trace)
  def test_branch_scoring_classification(conditional_trace)
  def test_branch_pruning_removes_unlikely_branches()
  def test_branch_pruning_preserves_hierarchy()
  def test_generate_2_to_3_branches_per_decision(conditional_trace)
  def test_branch_description_quality(conditional_trace)
  def test_branch_ids_are_unique(nested_branching_trace)
  def test_handle_empty_trace()
  def test_handle_trace_without_branching(simple_linear_trace)
```

### skills\code_v3.0\tests\test_tot_branch_scoring.py
```
  def sure_branch_scenarios()
  def unlikely_branch_scenarios()
  def maybe_branch_scenarios()
  def test_sure_branches_score_correctly(sure_branch_scenarios)
  def test_unlikely_branches_score_correctly(unlikely_branch_scenarios)
  def test_maybe_branches_score_correctly(maybe_branch_scenarios)
  def test_scoring_consistency()
  def test_all_branches_have_valid_scores()
  def test_scoring_based_on_keywords()
  def test_scoring_based_on_path_type()
  def test_edge_case_scoring()
  def test_nested_scoring()
  def test_scoring_with_loops()
  def test_scoring_with_try_except()
  def test_confidence_levels()
```

### skills\code_v3.0\tests\test_tsr_calculation.py
```
  def temp_ledger_file(tmp_path)
  def evidence_mgr_all_complete(temp_ledger_file)
  def evidence_mgr_partial_complete(temp_ledger_file)
  def evidence_mgr_low_tsr(temp_ledger_file)
  def evidence_mgr_empty(temp_ledger_file)
  class TestTSRCalculation()
    def test_tsr_all_tasks_complete(self, evidence_mgr_all_complete)
    def test_tsr_partial_completion(self, evidence_mgr_partial_complete)
    def test_tsr_low_completion(self, evidence_mgr_low_tsr)
    def test_tsr_empty_task_list(self, evidence_mgr_empty)
    def test_calculate_tsr_function(self, evidence_mgr_all_complete)
  class TestTSRValidation()
    def test_validate_done_claim_passes_with_high_tsr(self, evidence_mgr_all_complete)
    def test_validate_done_claim_blocks_with_low_tsr(self, evidence_mgr_low_tsr)
    def test_validate_done_claim_blocks_with_partial_tsr(self, evidence_mgr_partial_complete)
    def test_validate_done_claim_with_empty_task_list(self, evidence_mgr_empty)
    def test_validate_done_claim_custom_threshold(self, temp_ledger_file)
    def test_error_message_includes_task_breakdown(self, evidence_mgr_low_tsr)
  class TestTSREdgeCases()
    def test_tsr_with_incomplete_evidence(self, temp_ledger_file)
    def test_tsr_with_partial_evidence_not_done(self, temp_ledger_file)
    def test_tsr_threshold_at_exact_boundary(self, temp_ledger_file)
```

### skills\code_v3.0\tests\test_user_optout_handler.py
```
  def temp_project_dir()
  class TestUserOptoutHandler()
    def test_detects_opt_out_checkbox_when_checked(self, temp_project_dir)
    def test_returns_false_when_opt_out_not_checked(self, temp_project_dir)
    def test_returns_false_when_opt_out_line_missing(self, temp_project_dir)
    def test_handles_missing_plan_md_gracefully(self, temp_project_dir)
```

### skills\code_v3.0\tests\test_validate_done_claim.py
```
  def temp_ledger_dir()
  class TestValidateDoneClaim()
    def test_all_tasks_complete_pass(self, temp_ledger_dir)
    def test_one_task_missing_evidence(self, temp_ledger_dir)
    def test_multiple_tasks_missing_evidence(self, temp_ledger_dir)
    def test_no_tasks_in_ledger(self, temp_ledger_dir)
    def test_generate_missing_evidence_report(self, temp_ledger_dir)
    def test_error_message_clarity(self, temp_ledger_dir)
  class TestValidateDoneClaimIntegration()
    def test_all_four_evidence_types_required(self, temp_ledger_dir)
    def test_partial_task_list_validation(self, temp_ledger_dir)
  class TestValidateDoneClaimLedgerAccess()
    def test_task_ids_none_loads_all_tasks_from_ledger(self, temp_ledger_dir)
    def test_task_ids_none_with_mocked_ledger(self, temp_ledger_dir)
    def test_task_ids_none_empty_ledger_returns_true(self, temp_ledger_dir)
```

### skills\code_v3.0\tests\test_validate_phase_transition.py
```
  def temp_state_dir()
  class TestValidatePhaseTransition()
    def test_valid_transition_build_to_trace(self, temp_state_dir)
    def test_valid_transition_trace_to_ship(self, temp_state_dir)
    def test_invalid_transition_bootstrap_to_ship(self, temp_state_dir)
    def test_invalid_regression_ship_to_build(self, temp_state_dir)
    def test_phase_validity_check_rollback_detected(self, temp_state_dir)
    def test_phase_validity_check_no_commit_hash(self, temp_state_dir)
    def test_error_message_clarity(self, temp_state_dir)
  class TestPhaseTransitionIntegration()
    def test_phase_order_enforcement_sequence(self, temp_state_dir)
    def test_phase_with_missing_phase_state(self, temp_state_dir)
```

### skills\code_v3.0\tests\test_verify_plan_compliance.py
```
  class TestExtractPlannedTests()
    def test_extract_from_numbered_strategy(self)
    def test_extract_from_bold_format(self)
    def test_extract_from_bullet_format(self)
    def test_extract_from_scenario_format(self)
    def test_extract_no_test_strategy(self)
    def test_extract_empty_strategy(self)
    def test_extract_missing_plan_file(self)
  class TestExtractImplementedTests()
    def test_extract_pytest_functions(self)
    def test_extract_class_based_tests(self)
    def test_extract_no_tests(self)
    def test_extract_mixed_functions(self)
    def test_extract_missing_test_file(self)
  class TestComplianceIntegration()
    def test_compliance_pass_match(self)
    def test_compliance_fail_mismatch(self)
    def test_compliance_no_plan(self)
    def test_compliance_no_test_file(self)
    def test_compliance_zero_planned(self)
  class TestRealWorldScenarios()
    def test_unverified_stance_detector_scenario(self)
    def test_complete_coverage_scenario(self)
  class TestEdgeCases()
    def test_empty_plan_file(self)
    def test_empty_test_file(self)
    def test_plan_with_no_numbers(self)
    def test_test_with_other_def_patterns(self)
    def test_multiline_plan_strategy(self)
```

### skills\code_v3.0\tests\test_version_comparator.py
```
  class TestSemanticVersionDataclass()
    def test_semantic_version_creation_full(self)
    def test_semantic_version_creation_partial(self)
    def test_semantic_version_creation_major_only(self)
  class TestVersionStringParsing()
    def test_parse_full_semantic_version(self)
    def test_parse_major_minor_only(self)
    def test_parse_major_only(self)
    def test_parse_non_semantic_version(self)
    def test_parse_empty_string(self)
    def test_parse_none_input(self)
    def test_parse_version_with_metadata(self)
  class TestVersionBumpDetection()
    def test_detect_major_version_bump(self)
    def test_detect_minor_version_bump(self)
    def test_detect_patch_version_bump(self)
    def test_detect_no_version_bump(self)
    def test_detect_version_bump_with_partial_versions(self)
    def test_detect_version_bump_invalid_versions(self)
  class TestVersionComparisonOperators()
    def test_version_equal(self)
    def test_version_not_equal_greater(self)
    def test_version_not_equal_less(self)
    def test_version_major_determines_order(self)
    def test_version_minor_determines_order_when_major_equal(self)
    def test_version_patch_determines_order_when_major_minor_equal(self)
    def test_version_comparison_with_partial_versions(self)
    def test_version_comparison_invalid_versions(self)
  class TestEdgeCases()
    def test_very_large_version_numbers(self)
    def test_version_with_leading_zeros(self)
    def test_version_with_spaces(self)
    def test_zero_version(self)
```

### skills\code_v3.0\utils\__init__.py
```
  (empty)
```

### skills\code_v3.0\utils\context7_client.py
```
  class Context7RateLimitError(Exception)
    def __init__(self, message, max_retries)
  class Context7Resolver()
    def __init__(self, max_retries, initial_backoff, resolve_tool)
    def _generate_cache_key(self, library_name, query) -> Tuple[str, Optional[str]]
    def _call_with_retry(self, tool_func) -> Dict[str, Any]
    def resolve_library_name(self, library_name, query) -> Dict[str, Any]
    def _get_mcp_tool(self, module_name) -> Optional[Callable[..., Dict[str, Any]]]
    def _parse_response(self, response) -> Dict[str, Any]
    def clear_cache(self) -> None
  class BreakingChangeDetector()
    def __init__(self, max_retries, initial_backoff, query_tool)
    def _generate_cache_key(self, library_id, version) -> Tuple[str, str]
    def _call_with_retry(self, tool_func) -> Dict[str, Any]
    def _is_changelog_content(self, title, content) -> bool
    def query_breaking_changes(self, library_id, version) -> Dict[str, Any]
    def _get_mcp_tool(self, module_name) -> Optional[Callable[..., Dict[str, Any]]]
    def _extract_breaking_changes(self, response) -> List[Dict[str, str]]
    def clear_cache(self) -> None
```

### skills\code_v3.0\utils\context7_rate_limiter.py
```
  class _SharedState()
    def __new__(cls) -> '_SharedState'
    def _initialize(self) -> None
    def reset(self) -> None
  def reset_shared_state() -> None
  class RateLimitTracker()
    def __init__(self, window_seconds)
    def record_query(self, track, library) -> None
    def get_total_queries(self) -> int
    def get_queries_in_window(self) -> int
  class BatchQueryOptimizer()
    def __init__(self, batch_window_ms) -> None
    def query_library(self, track, library) -> Dict[str, Any]
    def get_api_call_count(self, library) -> int
    def reset_batch_state(self) -> None
    def _is_within_batch_window(self, library, current_time) -> bool
    def _update_cache_and_batch_results(self, library, result) -> None
  class Context7RateLimiter()
    def __init__(self, queries_per_minute, window_seconds, initial_backoff, max_retries, enable_fallback, allow_explore_fallback, allow_explore_bypass) -> None
    def _get_shared_state(self) -> _SharedState
    def get_total_queries(self) -> int
    def query_library(self, track, library, critical_phase) -> Dict[str, Any]
    def _can_make_query(self) -> bool
    def _get_cached_result(self, library, track) -> Optional[Dict[str, Any]]
    def _execute_query(self, track, library) -> Dict[str, Any]
    def _wait_for_backoff_if_needed(self) -> None
    def _cache_successful_result(self, library, result) -> None
    def _call_with_retry(self, library, track) -> Dict[str, Any]
    def _handle_max_retries_exceeded(self, library, backoff, is_explore, api_result) -> Dict[str, Any]
    def _clear_backoff(self) -> None
    def _handle_rate_limit(self, track, library, is_explore) -> Dict[str, Any]
    def _get_fallback_result(self, library) -> Dict[str, Any]
    def clear_cache(self) -> None
  def _call_context7_api(library) -> Dict[str, Any]
  def _get_local_version(library) -> Optional[str]
```

### skills\code_v3.0\utils\evidence.py
```
  class EvidenceManager()
    def __init__(self, terminal_id)
    def _ensure_ledger_exists(self)
    def _load_ledger(self) -> dict
    def _save_ledger(self, ledger)
    def _load_ledger_locked(self) -> dict
    def _save_ledger_locked(self, ledger)
    def _verify_implementation_exists(self, task_id) -> list[str]
    def _append_evidence(self, task_id, stage, evidence)
    def record_red(self, task_id, test_files, test_command, failing_tests)
    def record_green(self, task_id, impl_files, test_command, passing_tests)
    def record_refactor(self, task_id, changes, test_command, passing_tests)
    def record_verify(self, task_id, findings, blocking, verdict)
    def can_mark_done(self, task_id) -> tuple[bool, str]
    def mark_done(self, task_id)
    def get_task_status(self, task_id) -> dict
    def get_completion_statistics(self) -> dict
    def record_tdd_evidence(self, task_id, phase, evidence)
```

### skills\code_v3.0\utils\got_planner.py
```
  class Node()
  class Edge()
  class GotPlanner()
    def __init__(self, plan_content)
    def extract_nodes(self) -> Dict[str, List[Dict[str, Any]]]
    def _classify_node(self, text) -> str
    def _generate_node_id(self, category, index) -> str
  class GotEdgeAnalyzer()
    def __init__(self, nodes)
    def analyze_edges(self) -> List[Dict[str, Any]]
    def _analyze_relationship(self, node_a, node_b) -> Dict[str, Any]
    def _check_contradiction(self, text_a, text_b) -> bool
    def _check_support(self, text_a, text_b) -> bool
    def detect_cycles(self, edges) -> List[List[str]]
    def break_cycles(self, cycles) -> List[Dict[str, Any]]
```

### skills\code_v3.0\utils\library_scanner.py
```
  class ImportScanner()
    def __init__(self) -> None
    def scan_file(self, file_path, filter_stdlib) -> List[str]
    def scan_files(self, file_paths, filter_stdlib) -> List[str]
    def _visit_tree(self, tree) -> None
    def _extract_import_modules(self, node) -> None
    def _extract_from_import_modules(self, node) -> None
    def _filter_standard_library(self, imports) -> List[str]
  class DependencyFileParser()
    def __init__(self) -> None
    def parse_requirements_txt(self, file_path) -> Dict[str, Optional[str]]
    def parse_pyproject_toml(self, file_path) -> Dict[str, Optional[str]]
    def parse_all(self, requirements_txt, pyproject_toml) -> Dict[str, Optional[str]]
    def _should_skip_line(self, line) -> bool
    def _parse_requirement_line(self, line) -> Tuple[str, Optional[str]]
    def _extract_toml_array(self, content, section, key) -> Dict[str, Optional[str]]
    def _extract_toml_section(self, content, section) -> str
    def _extract_bracketed_content(self, content, start_pos) -> str
    def _parse_toml_array_entries(self, array_content) -> Dict[str, Optional[str]]
    def _extract_all_optional_deps(self, content) -> Dict[str, Optional[str]]
    def _find_matching_bracket(self, content, start_pos) -> int
    def _split_toml_array(self, array_content) -> List[str]
  class LibraryDetector()
    def __init__(self) -> None
    def detect_libraries(self, python_files, requirements_txt, pyproject_toml, directory, filter_stdlib) -> Dict[str, Optional[str]]
    def _collect_python_files(self, python_files, directory) -> List[Path]
    def _scan_imports(self, python_files, libraries, filter_stdlib) -> None
    def _merge_dependency_versions(self, libraries, requirements_txt, pyproject_toml) -> None
    def _find_python_files(self, directory) -> List[Path]
```

### skills\code_v3.0\utils\modernization_section_generator.py
```
  class ModernizationSectionGenerator()
    def generate_section(self, findings) -> str
    def _generate_empty_section(self) -> str
    def _generate_detected_divergences(self, divergences) -> str
    def _generate_recommendation(self, divergences) -> str
    def _generate_user_choice(self) -> str
```

### skills\code_v3.0\utils\normalize_paths.py
```
  def normalize_path(path_str) -> str
  def normalize_paths_in_command(command) -> str
  def normalize_path_list(path_list) -> list[str]
  def is_git_bash_path(path_str) -> bool
  def is_windows_path(path_str) -> bool
```

### skills\code_v3.0\utils\phase_state.py
```
  def _sanitize_terminal_id(raw_id) -> str
  def get_git_head_hash() -> str | None
  class PhaseStateManager()
    def __init__(self, terminal_id)
    def _ensure_state_exists(self)
    def _load_global_state(self) -> dict
    def _save_global_state(self, state)
    def _load_build_state(self) -> dict
    def _save_build_state(self, state)
    def is_phase_valid(self, phase_name) -> bool
    def mark_phase_complete(self, phase_name, commit_hash, metadata)
    def invalidate_phase(self, phase_name)
    def acquire_build_ownership(self, timeout_minutes) -> bool
    def release_build_ownership(self)
    def get_phase_status(self, phase_name) -> dict
    def get_all_phases_status(self) -> dict
```

### skills\code_v3.0\utils\plan_updater.py
```
  class TimeoutError(Exception)
  class TaskStatus(Enum)
  class TaskInfo()
  class PlanUpdateResult()
  def _compute_checksum(content) -> str
  def _file_lock(file_path, timeout, poll_interval) -> Generator[bool, None, None]
  class PlanUpdater()
    def __init__(self, plan_path, lock_timeout)
    def read_plan(self) -> bool
    def _parse_tasks(self) -> None
    def get_tasks(self) -> dict[str, TaskInfo]
    def get_task_status(self, task_id) -> TaskStatus
    def update_task_status(self, task_id, status) -> PlanUpdateResult
    def update_tasks(self, updates) -> PlanUpdateResult
    def _update_tasks_locked(self, updates) -> PlanUpdateResult
    def _create_backup(self) -> Path | None
    def restore_backup(self, backup_path) -> bool
  def update_plan_task_status(plan_path, task_id, status) -> PlanUpdateResult
  def get_plan_tasks(plan_path) -> dict[str, TaskInfo]
```

### skills\code_v3.0\utils\priority_scorer.py
```
  class PriorityLevel(Enum)
  class PriorityScore()
  def _extract_finding_attributes(finding) -> tuple[str, str, str]
  def _is_critical_issue(finding_type, severity, impact) -> bool
  def _is_high_priority_issue(finding_type, severity, impact) -> bool
  def categorize_finding(finding) -> PriorityLevel
  def _calculate_priority_score(priority) -> float
  def _calculate_confidence_score(finding) -> float
  def calculate_priority(finding) -> PriorityScore
```

### skills\code_v3.0\utils\tdd_resume.py
```
  def get_terminal_id() -> str
  def get_session_id() -> str
  def find_active_tdd_contracts(terminal_id) -> list[dict]
  def find_phase3_evidence(contract_id) -> list[dict]
  def generate_tdd_resume_context(terminal_id) -> str | None
  def get_tdd_state_for_handoff(terminal_id) -> dict
```

### skills\code_v3.0\utils\test_tdd_resume.py
```
  class TestHelper()
    def __init__(self, tmp_dir)
    def cleanup(self)
    def _create_state_file(self, contract_id, phase, test_file, impl_files, completed)
    def _create_evidence_file(self, contract_id, phase, evidence_hash)
  def _reload_tdd_resume()
  class TestGetTerminalId(TestCase)
    def setUp(self)
    def tearDown(self)
    def test_get_terminal_id(self)
  class TestGetSessionId(TestCase)
    def setUp(self)
    def tearDown(self)
    def test_get_session_id(self)
  class TestFindActiveTDDContracts(TestCase)
    def setUp(self)
    def tearDown(self)
    def test_empty(self)
    def test_idle_skipped(self)
    def test_single_active(self)
    def test_multiple_active(self)
  class TestFindPhase3Evidence(TestCase)
    def setUp(self)
    def tearDown(self)
    def test_empty(self)
    def test_single_contract(self)
    def test_specific_contract(self)
  class TestGenerateTDDResumeContext(TestCase)
    def setUp(self)
    def tearDown(self)
    def test_empty(self)
    def test_single(self)
    def test_with_evidence(self)
  class TestGetTDDStateForHandoff(TestCase)
    def setUp(self)
    def tearDown(self)
    def test_empty(self)
    def test_with_contracts(self)
```

### skills\code_v3.0\utils\tot_tracer.py
```
  class BranchGenerator()
    def __init__(self, code_content)
    def generate_branches(self) -> list[dict[str, Any]]
    def prune_branches(self, branches) -> list[dict[str, Any]]
    def _find_conditionals(self) -> list[dict[str, Any]]
    def _generate_branches_for_conditional(self, conditional) -> list[dict[str, Any]]
    def _create_branch(self, line_num, suffix, description, score) -> dict[str, Any]
    def _generate_description(self, conditional_text, path_type) -> str
    def _score_branch(self, conditional_text, path_type) -> str
```

### skills\code_v3.0\utils\user_optout_handler.py
```
  class UserOptoutHandler()
    def __init__(self, project_dir) -> None
    def should_skip_modernization(self) -> bool
    def _contains_optout_checkbox(self, content) -> bool
    def _is_optout_line(self, line) -> bool
    def save_opt_out_preference(self, opt_out) -> bool
    def has_persisted_preference(self) -> bool
    def get_persisted_preference(self) -> bool | None
```

### skills\code_v3.0\utils\version_comparator.py
```
  class SemanticVersion()
  def parse_version(version_string) -> Optional[SemanticVersion]
  def compare_versions(v1, v2) -> Optional[int]
  def detect_version_bump(current, latest) -> Optional[Literal['MAJOR', 'MINOR', 'PATCH', 'NONE']]
```

### skills\code_v4.0\hooks\PostToolUse_breadcrumb_tracker.py
```
  def _is_pytest(cmd) -> bool
  def _is_smoke(cmd) -> bool
  def _is_full_suite(cmd) -> bool
  def _audit_exit_from_cmd(cmd, stdout, stderr, exit_code) -> int | None
  def detect_completed_step(tool_name, tool_input) -> str | None
  def main() -> None
```

### skills\code_v4.0\hooks\PreToolUse_plan_consumer_gate.py
```
  def _should_skip_for_path(file_path) -> bool
  def _required_phase() -> int
  def main() -> None
```

### skills\code_v4.0\hooks\Stop_enforce_gate.py
```
  def main() -> None
```

### skills\design\__init__.py
```
  (empty)
```

### skills\design\aid_integration.py
```
  class AIDAction(Enum)
  class AIDConfig()
  class AIDResult()
  class AIDSkillIntegrator()
    def __init__(self, config)
    def _verify_aid_cli(self) -> None
    def run_ai_action(self, target_path, ai_action, include_patterns, exclude_patterns) -> AIDResult
    def _extract_prompt_file(self, output) -> str | None
    def generate_diagrams(self, target_path) -> AIDResult
    def analyze_refactoring(self, target_path) -> AIDResult
    def analyze_performance(self, target_path) -> AIDResult
    def analyze_security(self, target_path) -> AIDResult
    def analyze_codebase(self, target_path) -> AIDResult
    def analyze_best_practices(self, target_path) -> AIDResult
    def hunt_bugs(self, target_path) -> AIDResult
    def generate_docs(self, target_path, multi_file) -> AIDResult
  def create_aid_integrator(config) -> AIDSkillIntegrator
```

### skills\design\aid_wrapper.py
```
  class CodebaseAnalysis()
  class APIExtract()
  class LayerAnalysis()
  class DependencyDirection()
  class AidIntegrator()
    def __init__(self, config)
    def distill(self, target_path, include_patterns, exclude_patterns) -> CodebaseAnalysis
    def extract_public_apis(self, target_path, include_private) -> list[APIExtract]
    def analyze_dependencies(self, target_path) -> dict[str, list[str]]
    def detect_boundaries(self, target_path) -> list[str]
    def detect_layers(self, target_path) -> LayerAnalysis
    def analyze_dependency_direction(self, target_path) -> DependencyDirection
    def _collect_files(self, target, include_patterns, exclude_patterns) -> list[Path]
    def _distill_python(self, content, file_path) -> str
    def _distill_typescript(self, content, file_path) -> str
    def _distill_generic(self, content, file_path) -> str
    def _extract_apis_python(self, content, file_path, include_private) -> list[APIExtract]
    def _extract_apis_typescript(self, content, file_path, include_private) -> list[APIExtract]
    def _analyze_dependencies_python(self, content, file_path) -> list[str]
    def _analyze_dependencies_typescript(self, content, file_path) -> list[str]
    def _detect_boundaries(self, target, files) -> list[str]
    def _build_import_graph(self, target, files) -> dict[str, list[str]]
    def _detect_layer_violations(self, layers, import_graph) -> list[str]
    def _classify_file_layer(self, file_path, layers) -> str | None
    def _detect_dependency_violations(self, import_graph) -> list[str]
  def create_aid_integrator(config) -> AidIntegrator
```

### skills\design\aid_wrapper_v2.py
```
  class AIDCompressionLevel(Enum)
  class AIDAIAction(Enum)
  class AIDAnalysisResult()
  class AidIntegratorV2()
    def __init__(self, config)
    def _normalize_path(self, path) -> str
    def distill(self, target_path, include_patterns, exclude_patterns) -> AIDAnalysisResult
    def analyze_with_ai_action(self, target_path, ai_action, include_patterns, exclude_patterns) -> str
    def generate_diagrams(self, target_path) -> str
    def detect_layers(self, target_path) -> dict[str, Any]
    def _detect_layer_violations(self, layers, import_graph) -> list[str]
    def _classify_file_layer(self, file_path, layers) -> str | None
    def analyze_dependency_direction(self, target_path) -> dict[str, Any]
    def _detect_dependency_violations(self, import_graph) -> list[str]
  def create_aid_integrator(config) -> AidIntegratorV2
```

### skills\design\arch_validate.py
```
  class StageCheck()
  class StageValidationResult()
    def all_pass(self) -> bool
    def pass_count(self) -> int
    def warn_count(self) -> int
    def fail_count(self) -> int
    def to_findings(self) -> list[dict[str, object]]
  class StageValidator()
    def __init__(self, contract_sensitive) -> None
    def _check_stage(self, text, stage) -> StageCheck
    def validate(self, text) -> StageValidationResult
  def validate_adr(path) -> dict[str, object]
  def _run_stage_validation(text, contract_sensitive) -> dict[str, object]
  def main(argv) -> int
```

### skills\design\config.py
```
  def clear_config_cache() -> None
  def _load_arch_config_impl(user_config_str, project_config_str, user_mtime, project_mtime, env_domain, env_output_size, env_evidence_level) -> dict[str, Any] | None
  def load_arch_config() -> dict[str, Any] | None
  def _get_file_mtime(path) -> float
```

### skills\design\cross_platform_paths.py
```
  def _detect_platform() -> PlatformName
  def resolve_cks_db_path() -> Path
  def resolve_template_path(template_name) -> str
```

### skills\design\hooks\stop_if_unverified.py
```
  def _terminal_id() -> str
  def _state_dir() -> Path
  def _state_file() -> Path
  def main() -> None
```

### skills\design\hooks\verify_claims.py
```
  def _terminal_id() -> str
  def _state_dir() -> Path
  def _state_file() -> Path
  def verify(run_id, domain, claims_count) -> str
  def main() -> None
```

### skills\design\path_detection.py
```
  def detect_path_backslashes(path_str) -> bool
  def extract_path_components(path_str) -> list
```

### skills\design\persistence.py
```
  def should_skip_persistence(query, output, skip_keywords) -> bool
  def generate_decision_filename(query, _template) -> str
  def _find_cks_db() -> Path | None
  def _ingest_into_cks(query, template, domain, output, filename) -> None
  def save_arch_decision(query, template, domain, output, confidence, research_sources, decisions_dir, metrics) -> str | None
  def load_decision_index(index_path) -> list[dict[str, Any]]
  def search_decisions(query, index_path, limit) -> list[dict[str, Any]]
  def cleanup_old_entries(days_threshold, index_path, dry_run) -> dict[str, Any]
  def rotate_index(keep_entries, index_path, decisions_dir, dry_run) -> dict[str, Any]
  def cleanup_orphaned_files(index_path, decisions_dir, dry_run) -> dict[str, Any]
  def track_template_chaining_usage(primary_template, chained_domains, source, query, usage_file) -> None
  def check_chaining_usage_monitoring(usage_file, days_threshold) -> dict[str, Any]
  def log_decision_metrics(decision_id, query, pattern, high_stakes, templates, context, vs, judge, diversity, persistence, user_outcome, log_file) -> None
  def log_candidate_metrics(decision_id, candidate_id, vs, critic, selection, log_file) -> None
```

### skills\design\planning_handoff_validation.py
```
  def is_planning_bound_adr(text, handoff_packet_version) -> bool
  def validate_planning_handoff_contract(text, packet, handoff) -> list[dict[str, object]]
```

### skills\design\prerequisite_analyzer.py
```
  class AnalysisResult(TypedDict)
  class PrerequisiteAnalyzer()
    def analyze(query) -> AnalysisResult
    def _matches_optimization(text) -> bool
    def _matches_prd(text) -> bool
    def _matches_discover(text) -> bool
    def _matches_debug(text) -> bool
    def _matches_any_cached(text) -> bool
    def _matches_any(text, patterns) -> bool
    def _matches_any_cache_clear() -> None
    def _matches_any_cache_info()
```

### skills\design\resources\validate_docs.py
```
  class DocumentationValidator()
    def __init__(self, docs_dir)
    def validate(self)
```

### skills\design\results.py
```
  class ArchResult()
    def is_complete(self) -> bool
    def is_valid(self) -> bool
    def unwrap(self) -> T
    def unwrap_or(self, default) -> T
    def unwrap_error(self) -> str
```

### skills\design\routing.py
```
  [error]
```

### skills\design\schemas.py
```
  class Severity(str, Enum)
  class ContractBoundary()
  class ContractAuthorityPacket()
    def to_dict(self) -> dict[str, Any]
  class ClaimVerification()
    def to_dict(self) -> dict[str, Any]
  class BottleneckEvidence()
    def to_dict(self) -> dict[str, Any]
  class CriticFinding()
    def to_dict(self) -> dict[str, Any]
  class DesignPayload()
    def to_dict(self) -> dict[str, Any]
    def from_dict(cls, data) -> DesignPayload
```

### skills\design\test_aid_v2_integration.py
```
  def test_aid_integrator_creation()
  def test_basic_distillation()
  def test_layer_detection()
  def test_dependency_analysis()
  def main()
```

### skills\design\test_aid_value.py
```
  (empty)
```

### skills\design\test_debug.py
```
  def load_config()
```

### skills\design\tests\__init__.py
```
  (empty)
```

### skills\design\tests\conftest.py
```
  def pytest_configure(config)
  def clear_config_cache_between_tests()
```

### skills\design\tests\test_arch_validate_handoff.py
```
  def test_planning_bound_adr_requires_planning_handoff_packet(tmp_path) -> None
  def test_planning_bound_adr_with_handoff_packet_passes_handoff_check(tmp_path) -> None
  def test_planning_bound_adr_without_instruction_or_return_to_caller_blocks(tmp_path) -> None
  def test_nested_planning_return_to_caller_satisfies_routing_contract(tmp_path) -> None
```

### skills\design\tests\test_cks_fallback.py
```
  class TestCKSModuleNotFound()
    def test_cks_module_not_found_sets_available_false(self)
    def test_cks_module_not_found_shows_warning(self)
  class TestCKSDatabaseMissing()
    def test_cks_database_missing_sets_available_false(self)
    def test_cks_database_missing_shows_warning(self)
  class TestCKSImportError()
    def test_cks_import_error_sets_available_false(self)
    def test_cks_generic_exception_handled(self)
  class TestCKSAvailable()
    def test_cks_available_sets_true(self)
    def test_cks_queries_work_when_available(self)
  class TestWarningMessageContent()
    def test_warning_includes_fix_suggestions(self)
    def test_warning_contains_error_details(self)
  class TestGenericAnalysisProceeds()
    def test_generic_analysis_proceeds_when_cks_unavailable(self)
    def test_analysis_falls_back_to_best_practices(self)
    def test_no_exception_raised_when_cks_unavailable(self)
```

### skills\design\tests\test_cks_real_fallback.py
```
  [error]
```

### skills\design\tests\test_cks_real_import.py
```
  class TestCKSIntegrationImplemented()
    def test_arch_skill_has_cks_import_handling_code(self)
    def test_cks_available_variable_is_accessible(self)
    def test_cks_integration_fallback_works(self)
```

### skills\design\tests\test_config.py
```
  class TestLoadArchConfigDefaults()
    def test_no_config_returns_default_domain(self)
  class TestLoadArchConfigValidation()
    def test_invalid_domain_raises_value_error(self, tmp_path)
    def test_missing_default_domain_raises_value_error(self, tmp_path)
  class TestLoadArchConfigEnvOverride()
    def test_env_domain_overrides_config(self, tmp_path, monkeypatch)
  class TestValidDomains()
    def test_valid_domains_contains_expected(self)
    def test_valid_output_sizes(self)
    def test_valid_evidence_levels(self)
  class TestArchConfigClass()
    def test_arch_config_load_returns_arch_result(self)
    def test_arch_config_get_returns_default_when_no_key(self)
    def test_arch_config_get_returns_config_value(self)
  class TestClearConfigCache()
    def test_clear_config_cache_does_not_raise(self)
    def test_cache_clear_allows_fresh_load(self, tmp_path, monkeypatch)
```

### skills\design\tests\test_config_caching.py
```
  def clear_cache_before_each_test()
  class TestLoadArchConfigCacheImplementation()
    def temp_config_dir(self, tmp_path) -> Path
    def test_cached_call_should_not_check_file_existence(self, temp_config_dir)
    def test_cache_invalidation_on_mtime_change(self, tmp_path)
```

### skills\design\tests\test_config_extraction.py
```
  class TestConfigModuleExists()
    def test_config_module_exists(self)
    def test_config_module_importable(self)
  class TestLoadArchConfigFunction()
    def test_load_arch_config_function_exists(self)
    def test_load_arch_config_is_callable(self)
  class TestSkillMdReferencesModule()
    def skill_md_path(self)
    def skill_md_content(self, skill_md_path)
    def test_skill_md_references_config_load_arch_config(self, skill_md_content)
    def test_skill_md_contains_config_import_example(self, skill_md_content)
  class TestNoDuplicateFunctionInDoc()
    def skill_md_path(self)
    def skill_md_content(self, skill_md_path)
    def test_no_full_function_definition_in_skill_md(self, skill_md_content)
    def test_no_duplicate_implementation_details(self, skill_md_content)
    def test_skill_md_has_concise_reference_not_implementation(self, skill_md_content)
```

### skills\design\tests\test_config_integration.py
```
  class TestLoadArchConfigWithRealFiles()
    def test_load_arch_config_with_real_files(self, tmp_path, monkeypatch)
    def test_load_arch_config_no_files_returns_none(self, tmp_path, monkeypatch)
    def test_load_arch_config_with_invalid_json_raises_error(self, tmp_path, monkeypatch)
    def test_load_arch_config_precedence_with_real_files(self, tmp_path, monkeypatch)
    def test_load_arch_config_with_invalid_domain_raises_error(self, tmp_path, monkeypatch)
```

### skills\design\tests\test_config_merging.py
```
  class TestPartialConfigMerging()
    def test_partial_merge_project_overrides_user_preserves_others(self, mock_read, mock_exists)
    def test_partial_merge_multiple_keys_from_user_preserved(self, mock_read, mock_exists)
    def test_partial_merge_user_has_subset_project_has_superset(self, mock_read, mock_exists)
```

### skills\design\tests\test_config_real_files.py
```
  def clean_arch_env_vars()
  def clear_cache()
  class TestRealConfigFileLoading()
    def test_load_valid_project_config_file(self, tmp_path)
    def test_load_config_without_env_vars(self, tmp_path)
    def test_malformed_json_fails_appropriately(self, tmp_path)
    def test_missing_required_field_fails_appropriately(self, tmp_path)
    def test_invalid_domain_value_fails_appropriately(self, tmp_path)
    def test_invalid_output_size_value_fails_appropriately(self, tmp_path)
```

### skills\design\tests\test_config_thread_safety.py
```
  def clear_cache_before_each_test()
  def clean_arch_env_vars()
  class TestLoadArchConfigThreadSafety()
    def mock_config_env(self)
    def mock_project_config(self, tmp_path)
    def test_config_cache_has_thread_synchronization_mechanism(self)
    def test_concurrent_reads_no_cache_corruption(self, mock_project_config)
    def test_concurrent_cache_access_no_corruption(self, mock_config_env)
    def test_cache_invariant_maintained_under_concurrency(self)
    def test_no_lost_updates_under_concurrency(self, mock_project_config)
  class TestConfigCacheSpecificRaceConditions()
    def mock_config_env(self)
    def test_check_then_write_race_condition(self, mock_config_env)
    def test_concurrent_cache_miss_handling(self, mock_config_env)
  class TestFixtureCleanup()
    def test_clean_arch_env_vars_fixture_cleanup_single_var(self)
    def test_clean_arch_env_vars_fixture_cleanup_multiple_vars(self)
    def test_clean_arch_env_vars_fixture_restores_original_values(self)
```

### skills\design\tests\test_config_types.py
```
  def clean_arch_env_vars()
  class TestInvalidValueTypes()
    def test_default_domain_as_integer_raises_type_error(self, mock_read, mock_exists)
    def test_output_size_as_list_raises_type_error(self, mock_read, mock_exists)
    def test_multiple_invalid_types_raises_error(self, mock_read, mock_exists)
    def test_evidence_level_as_boolean_raises_type_error(self, mock_read, mock_exists)
  class TestValidTypesWithInvalidValues()
    def test_string_type_but_invalid_domain_value(self, mock_read, mock_exists)
```

### skills\design\tests\test_config_validation.py
```
  def clean_arch_env_vars()
  class TestInvalidDomainValue()
    def test_invalid_domain_value_raises_value_error(self, mock_read, mock_exists)
  class TestMissingRequiredField()
    def test_missing_required_field_raises_value_error(self, mock_read, mock_exists)
  class TestMalformedJSON()
    def test_malformed_json_raises_json_decode_error(self, mock_read, mock_exists)
  class TestValidConfig()
    def test_valid_config_returns_dict_with_default_domain(self, mock_read, mock_exists)
  class TestConfigPrecedence()
    def test_project_config_overrides_user_config(self, mock_read, mock_exists)
    def test_env_var_overrides_config_files(self, mock_read, mock_exists)
    def test_env_var_always_overrides_even_when_both_configs_have_different_values(self, mock_read, mock_exists)
  class TestMissingConfigFile()
    def test_missing_config_file_returns_none(self, mock_exists)
```

### skills\design\tests\test_contracts_error_handling.py
```
  class TestLoadContractsFileNotFoundError()
    def test_load_contracts_missing_file_raises_error_with_helpful_message(self, tmp_path)
    def test_load_contracts_missing_file_helpful_error_content(self, tmp_path)
```

### skills\design\tests\test_cross_platform.py
```
  [error]
```

### skills\design\tests\test_dry_enforcement.py
```
  class TestDuplicateDetectionWarns()
    def test_duplicate_detection_warns_when_over_50_percent_overlap(self, capsys)
    def test_duplicate_detection_returns_overlap_percentage(self)
    def test_duplicate_detection_threshold_at_exactly_50_percent(self)
  class TestSharedFrameworkReference()
    def test_shared_framework_reference_suggests_extraction(self)
    def test_templates_should_reference_shared_frameworks(self, tmp_path)
    def test_detect_known_shared_framework_pattern(self)
  class TestEnforcementLevel()
    def test_high_overlap_over_70_percent_should_fail_validation(self, tmp_path)
    def test_high_overlap_threshold_constant_exists(self)
    def test_validation_returns_1_for_critical_duplicates(self, capsys)
  class TestMediumOverlap()
    def test_medium_overlap_50_to_70_percent_should_warn_but_pass(self, tmp_path)
    def test_medium_overlap_boundary_at_70_percent(self)
    def test_overlap_percentage_calculation_accuracy(self)
  class TestDRYEnforcementIntegration()
    def test_complete_dry_validation_workflow(self, tmp_path, capsys)
    def test_shared_frameworks_reference_in_result_message(self, capsys)
```

### skills\design\tests\test_duplicate_load_arch_config.py
```
  class TestLoadArchConfigNotDuplicated()
    def test_routing_imports_load_arch_config_from_config(self)
    def test_only_one_load_arch_config_implementation(self)
    def test_load_arch_config_function_identity_same_result(self)
    def test_load_arch_config_same_signature(self)
    def test_load_arch_config_same_docstring(self)
  class TestLoadArchConfigBehavioralEquivalence()
    def mock_config_env(self)
    def test_environment_override_both_behave_same(self, mock_config_env)
    def test_none_config_both_behave_same(self)
    def test_invalid_domain_raises_same_error(self)
```

### skills\design\tests\test_enhancement_integrity.py
```
  def skill_content() -> str
  def enhancements_content() -> str
  def enhancement_sections(enhancements_content) -> dict[int, str]
  class TestSectionPointers()
    def test_all_pointers_reference_valid_sections(self, skill_content, enhancement_sections) -> None
    def test_all_12_sections_exist(self, enhancement_sections) -> None
    def test_no_orphaned_sections(self, skill_content, enhancement_sections) -> None
  class TestDecisionMatrixFormat()
    def test_weights_sum_to_1(self, enhancement_sections) -> None
    def test_scores_in_valid_range(self, enhancement_sections) -> None
  class TestATAMTemplate()
    def test_template_has_all_fields(self, enhancement_sections) -> None
    def test_example_scenario_is_complete(self, enhancement_sections) -> None
  class TestFragileRankConsistency()
    def test_threshold_consistent(self, skill_content, enhancements_content) -> None
  class TestStaleReferences()
    def test_no_arch_references_in_enhancements(self, enhancements_content) -> None
    def test_no_arch_references_in_adr_doc(self) -> None
    def test_enhancement_version_matches_skill(self, skill_content, enhancements_content) -> None
  class TestStageLabelConsistency()
    def test_stage_labels_use_numbered_format(self, enhancement_sections) -> None
    def test_section_7_references_claim_verification_gate(self, enhancement_sections) -> None
  class TestAntiPatternChecklist()
    def test_all_anti_patterns_present(self, enhancement_sections) -> None
    def test_all_have_severity(self, enhancement_sections) -> None
```

### skills\design\tests\test_error_messages.py
```
  class TestLoadArchConfigErrorMessages()
    def test_invalid_domain_error_message_contains_fix_guidance(self, mock_read, mock_exists)
    def test_invalid_domain_error_message_is_actionable(self, mock_read, mock_exists)
    def test_missing_required_field_error_is_specific(self, mock_read, mock_exists)
```

### skills\design\tests\test_external_caller_integration.py
```
  class TestExternalCallerIntegration()
    def test_external_import_path_works(self)
    def test_external_caller_handles_template_result_dict(self)
    def test_external_caller_handles_all_template_result_keys(self)
    def test_external_caller_with_template_override(self)
    def test_external_caller_with_default_domain(self)
    def test_external_caller_type_annotation_match(self)
    def test_external_caller_importlib_import(self)
    def test_breaking_change_catch_old_string_return(self)
    def test_external_caller_backward_compatibility_batch(self)
    def test_external_caller_chained_domains_feature(self)
```

### skills\design\tests\test_harcoded_paths.py
```
  class TestReplacePDriveWithPlatformDetection()
    def fast_md_path(self) -> Path
    def fast_md_content(self, fast_md_path) -> str
    def test_fast_md_uses_cross_platform_cks_path(self, fast_md_content)
    def test_fast_md_no_hardcoded_cks_path(self, fast_md_content)
  class TestDeepMdUsesCrossPlatformPaths()
    def deep_md_path(self) -> Path
    def deep_md_content(self, deep_md_path) -> str
    def test_deep_md_uses_cross_platform_paths(self, deep_md_content)
    def test_deep_md_no_hardcoded_shared_frameworks_path(self, deep_md_content)
  def _remove_code_blocks(content) -> str
  class TestNoHardcodedPSlash()
    def templates_dir(self) -> Path
    def all_template_contents(self, templates_dir) -> dict[str, str]
    def test_no_hardcoded_p_colon_slash_in_templates(self, all_template_contents)
    def test_fast_and_deep_md_no_hardcoded_paths(self, all_template_contents)
  class TestTemplateUsesForwardSlashes()
    def templates_dir(self) -> Path
    def all_template_contents(self, templates_dir) -> dict[str, str]
    def test_template_paths_use_forward_slashes_only(self, all_template_contents)
    def test_template_paths_consistent_separators(self, all_template_contents)
  def test_cross_platform_paths_module_exists()
  def test_resolve_cks_db_path_function_exists()
  def test_resolve_template_path_function_exists()
```

### skills\design\tests\test_hooks.py
```
  def _run_verify(run_id, domain, claims) -> tuple[int, str, str]
  def _run_stop(stdin_data) -> tuple[int, str, str]
  def _terminal_id() -> str
  def _state_dir() -> Path
  def _state_file() -> Path
  def _write_unverified_state(run_id) -> None
  def _cleanup()
  class TestVerifyClaims()
    def test_creates_state_file(self)
    def test_rejects_empty_run_id(self)
    def test_rejects_invalid_domain(self)
    def test_all_valid_domains_accepted(self)
    def test_state_file_contains_verified_true(self)
  class TestStopIfUnverified()
    def test_blocks_unverified_state(self)
    def test_allows_verified_run_id(self)
    def test_allows_without_state_file(self)
    def test_allows_with_empty_stdin(self)
    def test_allows_with_non_json_stdin(self)
    def test_cleans_up_state_after_allow(self)
  class TestHookIntegration()
    def test_full_verify_then_stop_flow(self)
    def test_verify_then_stop_blocks_without_verify(self)
```

### skills\design\tests\test_integration_validation.py
```
  def test_validate_templates_end_to_end(tmp_path)
```

### skills\design\tests\test_multi_terminal_isolation.py
```
  def test_concurrent_terminal_execution()
```

### skills\design\tests\test_opt_out_flags.py
```
  def sample_architecture_plan()
  def test_got_enabled_by_default(sample_architecture_plan)
  def test_no_got_flag_disables_got(sample_architecture_plan)
  def test_default_behavior_quality_first()
  def test_flag_parsing_conceptual()
  def test_environment_variable_disables_got(sample_architecture_plan)
  def test_environment_variable_false_allows_got(sample_architecture_plan)
  def test_got_node_extraction_quality(sample_architecture_plan)
  def test_got_edge_analysis_quality(sample_architecture_plan)
  def test_got_opt_out_constitutional_compliance()
  def test_got_independent_of_other_enhancements()
  def test_got_quality_first_design()
```

### skills\design\tests\test_overlap_numeric_validation.py
```
  class TestOverlapNumericValidation()
    def test_check_duplicate_logic_returns_numeric_value(self)
    def test_check_duplicate_logic_validates_against_50_percent_threshold(self)
    def test_check_duplicate_logic_high_overlap_triggers_failure(self)
    def test_check_duplicate_logic_below_threshold_returns_empty(self)
    def test_threshold_constants_are_defined(self)
  class TestCurrentTestLimitations()
    def test_current_test_only_checks_string_not_numeric(self)
    def test_check_duplicate_logic_returns_severity_indicator(self)
    def test_warning_range_has_severity_warning(self)
```

### skills\design\tests\test_overlap_validation.py
```
  class TestOverlapPercentageParsingMISSING()
    def test_check_duplicate_logic_returns_numeric_overlap_parseable(self, capsys)
    def test_check_duplicate_logic_threshold_validation_70_plus(self, capsys)
    def test_check_duplicate_logic_threshold_validation_below_50(self, capsys)
  class TestOverlapPercentageThresholds()
    def test_threshold_constants_exist_and_are_correct(self)
  class TestMissingNumericValidationInExistingTests()
    def test_existing_test_only_checks_string_not_numeric(self, capsys)
```

### skills\design\tests\test_path_detection.py
```
  class TestDetectPathBackslashesUsingPath()
    def test_function_exists(self)
    def test_detect_windows_path_backslashes(self)
    def test_no_backslashes_in_unix_paths(self)
    def test_handles_unicode_filenames(self)
  class TestExtractPathComponentsUsingParts()
    def test_function_exists(self)
    def test_extract_components_from_unix_path(self)
    def test_extract_components_from_windows_path(self)
    def test_handles_special_chars_in_filenames(self)
  class TestPathDetectionModuleExists()
    def test_path_detection_module_exists(self)
```

### skills\design\tests\test_path_traversal.py
```
  class TestPathTraversalVulnerability()
    def test_path_traversal_with_double_dot_attack(self)
    def test_path_traversal_single_double_dot(self)
    def test_path_traversal_double_dot_in_middle(self)
    def test_path_traversal_with_absolute_path(self)
    def test_path_traversal_windows_absolute_path(self)
    def test_path_traversal_p_drive_absolute_path(self)
    def test_path_traversal_with_null_byte(self)
    def test_path_traversal_null_byte_with_traversal(self)
    def test_path_traversal_with_url_encoding(self)
    def test_path_traversal_with_double_encoded(self)
    def test_valid_template_name_still_works(self)
    def test_valid_template_with_hyphen(self)
  def test_security_vulnerability_documentation()
  class TestWindowsSpecificPathTraversal()
    def test_windows_unc_path_should_be_rejected(self)
    def test_windows_drive_relative_path_should_be_rejected(self)
    def test_windows_reserved_device_names_documentation(self)
    def test_windows_absolute_paths_should_be_rejected(self)
    def test_valid_template_names_still_work(self)
```

### skills\design\tests\test_performance.py
```
  class TestTemplateContentCaching()
    def temp_template_file(self, tmp_path) -> Path
    def test_template_content_caching(self, temp_template_file)
    def test_cache_invalidation(self, temp_template_file)
    def test_duplicate_read_detection(self, temp_template_file)
    def test_performance_improvement(self, temp_template_file)
  class TestCacheImplementation()
    def clear_cache(self)
    def test_cache_clear_method_exists(self)
    def test_cache_info_method_exists(self)
    def test_cache_max_size_setting(self)
```

### skills\design\tests\test_performance_caching_real.py
```
  class TestOriginalTestFlaw()
    def temp_template_file(self, tmp_path) -> Path
    def test_original_test_fails_because_assertion_is_wrong(self, temp_template_file)
    def test_correct_way_to_verify_caching(self, temp_template_file)
  class TestManualCounterDoesNotVerifyCaching()
    def temp_template_file(self, tmp_path) -> Path
    def test_manual_counter_always_equals_call_count(self, temp_template_file)
    def test_cache_info_correctly_tracks_caching(self, temp_template_file)
  class TestComparisonFlawedVsCorrect()
    def temp_template_file(self, tmp_path) -> Path
    def test_flawed_approach_manual_counter(self, temp_template_file)
    def test_correct_approach_cache_info(self, temp_template_file)
```

### skills\design\tests\test_performance_deterministic.py
```
  class TestFlakyTimingBehavior()
    def clear_cache_before_each_test(self)
    def temp_template_file(self, tmp_path) -> Path
    def test_timing_can_fail_when_cached_is_slower(self, temp_template_file)
  class TestDeterministicPerformance()
    def clear_cache_before_each_test(self)
    def temp_template_file(self, tmp_path) -> Path
    def test_performance_improvement_with_mocked_time(self, temp_template_file)
    def test_cache_info_method_exists(self)
    def test_cache_clear_method_works(self, temp_template_file)
```

### skills\design\tests\test_persistence.py
```
  def _make_cks_db(path) -> None
  class TestFindCksDb()
    def test_returns_path_when_db_exists(self, tmp_path)
    def test_returns_none_when_db_missing(self, tmp_path)
    def test_returns_path_type(self, tmp_path)
  class TestIngestIntoCks()
    def test_inserts_row_into_cks_db(self, tmp_path)
    def test_content_truncated_to_2000_chars(self, tmp_path)
    def test_title_truncates_query_at_80_chars(self, tmp_path)
    def test_silent_failure_when_db_not_found(self)
    def test_silent_failure_on_corrupt_db(self, tmp_path)
    def test_silent_failure_on_arbitrary_exception(self)
    def test_insert_or_ignore_on_duplicate_id(self, tmp_path)
  class TestSaveArchDecisionCksIntegration()
    def test_ingest_called_after_successful_save(self, tmp_path)
    def test_ingest_not_called_when_save_skipped(self, tmp_path)
    def test_save_returns_filepath_despite_cks_down(self, tmp_path)
```

### skills\design\tests\test_prerequisite_cache.py
```
  class TestCacheKeyOptimizationForEfficiency()
    def test_cache_size_reduced_with_text_only_key(self)
    def test_cache_efficient_for_repeated_analyze_calls(self)
  class TestCurrentCacheInefficiency()
    def test_duplicate_entries_for_same_text(self)
    def test_cache_hit_with_identical_call(self)
  class TestCacheCapacity()
    def test_maxsize_256(self)
    def test_cache_capacity_for_unique_texts(self)
  class TestPatternConstants()
    def test_patterns_are_tuples(self)
    def test_patterns_not_empty(self)
  class TestIndividualCacheBehavior()
    def test_matches_optimization_cache_hits_on_repeated_calls(self)
    def test_matches_prd_cache_hits_on_repeated_calls(self)
    def test_matches_debug_cache_hits_on_repeated_calls(self)
    def test_cache_clear_works_for_all_cached_methods(self)
    def test_cache_size_is_bounded(self)
    def test_different_inputs_create_different_cache_entries(self)
```

### skills\design\tests\test_prerequisite_gates.py
```
  def skip_if_not_implemented()
  class TestOptimizationQueriesDoNotTriggerPrerequisiteGates()
    def test_improve_memory_system_does_not_trigger_prerequisite_gate(self)
    def test_optimize_x_proceeds_directly_to_architecture(self)
    def test_harden_y_does_not_trigger_prd_gate(self)
    def test_enhance_query_does_not_trigger_gate(self)
    def test_stabilize_query_does_not_trigger_gate(self)
  class TestGenuinePrerequisiteNeedsTriggerGates()
    def test_from_requirements_triggers_prd_gate(self)
    def test_how_is_x_structured_triggers_discover_gate(self)
    def test_why_failing_triggers_debug_gate(self)
    def test_explicit_prd_request_triggers_gate(self)
    def test_where_are_requirements_triggers_prd_gate(self)
  class TestSemanticAnalysisDistinguishesOptimizationFromPrerequisites()
    def test_optimization_without_requirements_proceeds(self)
    def test_optimization_with_requirements_triggers_prd(self)
    def test_case_insensitive_pattern_matching(self)
    def test_whitespace_handling(self)
```

### skills\design\tests\test_real_platform.py
```
  class TestRealPlatformDetection()
    def test_detect_platform_returns_valid_value(self)
    def test_detect_platform_matches_platform_system(self)
  class TestRealPlatformPathBehavior()
    def test_path_behavior_matches_detected_platform(self)
    def test_current_platform_path_separators(self)
  class TestRealPlatformCrossPlatformFunctions()
    def test_resolve_cks_db_path_returns_valid_path(self)
    def test_resolve_cks_db_path_matches_detected_platform(self)
    def test_resolve_template_path_uses_forward_slashes(self)
    def test_resolve_template_path_validates_input(self)
  class TestRealPlatformIntegration()
    def test_full_workflow_on_real_platform(self)
    def test_platform_consistency(self)
```

### skills\design\tests\test_result_structure.py
```
  def _broken_analyze(query) -> dict
  def _wrong_type_analyze(query) -> dict
  def _extra_keys_analyze(query) -> dict
  class TestResultStructureValidation()
    def test_analyze_returns_dict(self)
    def test_result_contains_all_required_keys(self)
    def test_key_types_are_correct_for_optimization_query(self)
    def test_key_types_are_correct_for_prerequisite_query(self)
    def test_result_structure_across_various_query_types(self)
    def test_empty_query_returns_valid_structure(self)
  class TestBrokenImplementationDetection()
    def test_fails_when_key_is_missing(self)
    def test_fails_when_key_has_wrong_type(self)
    def test_fails_when_extra_keys_present(self)
```

### skills\design\tests\test_results.py
```
  class TestArchResultSuccess()
    def test_is_success_true_on_success(self)
    def test_value_available_on_success(self)
    def test_error_none_on_success(self)
    def test_is_complete_true_when_success_with_value(self)
    def test_is_valid_true_on_success(self)
    def test_templates_used_defaults_to_empty_list(self)
    def test_metadata_defaults_to_empty_dict(self)
    def test_templates_used_can_be_set(self)
    def test_metadata_can_be_set(self)
  class TestArchResultError()
    def test_is_success_false_on_error(self)
    def test_value_none_on_error(self)
    def test_error_available_on_error(self)
    def test_is_complete_false_on_error(self)
    def test_is_valid_true_on_error(self)
    def test_error_with_metadata(self)
  class TestArchResultUnwrap()
    def test_unwrap_returns_value_on_success(self)
    def test_unwrap_raises_on_error(self)
    def test_unwrap_raises_when_value_is_none_on_success(self)
  class TestArchResultUnwrapOr()
    def test_unwrap_or_returns_value_on_success(self)
    def test_unwrap_or_returns_default_on_error(self)
    def test_unwrap_or_returns_default_when_value_is_none(self)
  class TestArchResultUnwrapError()
    def test_unwrap_error_returns_error_string(self)
    def test_unwrap_error_raises_on_success(self)
    def test_unwrap_error_returns_unknown_when_error_is_none(self)
  class TestArchResultGeneric()
    def test_generic_with_dict_value(self)
    def test_generic_with_list_value(self)
    def test_generic_with_str_value(self)
    def test_generic_with_tuple_value(self)
  class TestArchResultInvariant()
    def test_archresult_of_dict_not_assignable_to_archresult_of_list(self)
    def test_archresult_of_str_not_assignable_to_archresult_of_int(self)
```

### skills\design\tests\test_routing.py
```
  class TestExtractTemplateOverride()
    def test_valid_template_override_returns_template(self)
    def test_all_valid_templates_accepted(self)
    def test_invalid_template_returns_none(self)
    def test_no_override_returns_none(self)
    def test_case_sensitive_template_names(self)
    def test_override_with_hyphenated_name(self)
    def test_template_chaining_two_templates(self)
    def test_template_chaining_three_templates(self)
    def test_template_chaining_invalid_in_chain(self)
    def test_template_chaining_duplicate_templates(self)
  class TestDetectDomainKeywords()
    def test_cli_domain_detected(self)
    def test_python_domain_detected(self)
    def test_data_pipeline_domain_detected(self)
    def test_precedent_domain_detected(self)
    def test_no_keywords_returns_none(self)
    def test_priority_order_cli_over_python(self)
    def test_case_insensitive_matching(self)
    def test_all_cli_keywords(self)
    def test_all_python_keywords(self)
  class TestDetectComplexity()
    def test_redesign_indicates_deep(self)
    def test_architecture_indicates_deep(self)
    def test_microservices_indicates_deep(self)
    def test_rewrite_indicates_deep(self)
    def test_from_scratch_indicates_deep(self)
    def test_no_indicators_defaults_to_fast(self)
    def test_case_insensitive_detection(self)
    def test_all_high_complexity_indicators(self)
  class TestDetectIntentType()
    def test_improve_with_subsystem_returns_improve_system(self)
    def test_optimize_with_cks_returns_improve_system(self)
    def test_enhance_with_hooks_returns_improve_system(self)
    def test_improve_without_subsystem_returns_default(self)
    def test_subsystem_without_improve_returns_default(self)
    def test_no_keywords_returns_default(self)
    def test_case_insensitive_detection(self)
    def test_review_with_architecture_returns_architecture_review(self)
    def test_audit_with_design_returns_architecture_review(self)
    def test_assess_with_arch_returns_architecture_review(self)
    def test_evaluate_with_system_returns_architecture_review(self)
    def test_review_without_architecture_returns_default(self)
    def test_architecture_without_review_returns_default(self)
    def test_architecture_review_case_insensitive(self)
  class TestSelectTemplate()
    def test_template_override_parameter_highest_priority(self)
    def test_invalid_template_override_raises_error(self)
    def test_template_override_in_query(self)
    def test_invalid_template_in_query_ignored(self)
    def test_default_domain_used_when_no_keywords(self)
    def test_env_domain_used_when_no_default_domain(self)
    def test_default_domain_overrides_env_domain(self)
    def test_auto_domain_allows_keyword_detection(self)
    def test_auto_domain_falls_through_to_complexity(self)
    def test_invalid_domain_raises_error(self)
    def test_keyword_detection_overrides_default_domain(self)
    def test_complexity_detection_when_no_domain_or_keywords(self)
    def test_complexity_detection_defaults_to_fast(self)
    def test_full_routing_flow_priority_order(self)
  class TestValidateTemplate()
    def test_valid_template_returns_true(self)
    def test_invalid_template_returns_false(self)
    def test_all_valid_templates_validate(self)
    def test_error_message_includes_valid_templates(self)
  class TestConstants()
    def test_domain_keywords_structure(self)
    def test_valid_templates_is_set(self)
    def test_template_metadata_structure(self)
    def test_domain_priority_order(self)
  class TestTypeDefinitions()
    def test_template_result_type(self)
    def test_config_result_type(self)
    def test_validation_result_type(self)
  class TestIntegrationSelectTemplateWithConfig()
    def test_select_template_with_config_no_default_domain(self)
    def test_select_template_with_config_default_domain(self)
    def test_select_template_with_config_auto_domain(self)
    def test_select_template_with_config_and_file_validation(self)
    def test_select_template_with_config_priority_integration(self)
    def test_select_template_full_end_to_end_flow(self)
  class TestDetectVerificationDomain()
    def test_browser_automation_detected(self)
    def test_performance_detected(self)
    def test_api_integration_detected(self)
    def test_general_fallback(self)
    def test_source_snippet_enriches_detection(self)
    def test_highest_keyword_count_wins(self)
    def test_case_insensitive(self)
  class TestVerificationRequirements()
    def test_returns_list_for_all_domains(self)
    def test_browser_automation_requirements(self)
    def test_performance_requirements(self)
    def test_api_integration_requirements(self)
    def test_general_requirements(self)
    def test_unknown_domain_falls_back_to_general(self)
  class TestVerificationDomainsConstant()
    def test_is_tuple(self)
    def test_contains_expected_domains(self)
    def test_has_four_domains(self)
```

### skills\design\tests\test_template_io_errors.py
```
  class TestValidateTemplateIOErrors()
    def test_permission_error_returns_helpful_message(self)
    def test_unicode_decode_error_returns_helpful_message(self)
    def test_file_system_lock_error_returns_helpful_message(self)
    def test_os_error_returns_helpful_message(self)
    def test_error_messages_are_actionable(self)
  class TestValidateTemplateIOErrorContract()
    def test_error_message_format_is_tuple(self)
    def test_all_valid_templates_handle_io_errors_consistently(self)
```

### skills\design\tests\test_template_override_security.py
```
  class TestExtractTemplateOverrideSecurity()
    def test_extract_template_override_returns_any_value(self)
    def test_extract_template_override_with_special_chars(self)
    def test_extract_template_override_should_validate_against_allowlist(self)
```

### skills\design\tests\test_type_hints_consistency.py
```
  class TestTypeHintConsistency()
    def module_path(self) -> Path
    def module_source(self, module_path) -> str
    def module_ast(self, module_source) -> ast.Module
    def test_no_old_typing_imports(self, module_ast)
    def test_list_syntax_uses_lowercase(self, module_source)
    def test_dict_syntax_uses_lowercase(self, module_source)
    def test_tuple_syntax_uses_lowercase(self, module_source)
    def test_necessary_typing_imports_remain(self, module_ast)
```

### skills\design\tests\test_valid_domains_consistency.py
```
  def test_valid_domains_identical()
  def test_valid_domains_contains_expected_core_domains()
```

### skills\design\tests\test_validate.py
```
  class TestTemplateValidatorInit()
    def test_default_resources_dir(self)
    def test_custom_resources_dir(self)
  class TestCheckFileExists()
    def test_all_templates_exist(self)
    def test_missing_template_returns_error(self)
    def test_partial_missing(self)
  class TestCheckDuplicates()
    def test_no_duplicates_between_fast_and_deep(self)
    def test_extract_section_content(self)
    def test_extract_section_not_found(self)
    def test_calculate_line_overlap_empty(self)
    def test_calculate_line_overlap_full(self)
    def test_calculate_line_overlap_partial(self)
  class TestCheckPermissions()
    def test_readable_templates(self)
    def test_empty_file_is_unreadable(self, tmp_path)
  class TestValidateTemplates()
    def test_valid_templates_pass_all_stages(self)
    def test_fail_fast_at_file_exists(self)
    def test_fail_fast_at_duplicates(self)
    def test_none_defaults_to_all_templates(self)
    def test_constants_are_correct(self)
  class TestStandaloneFunction()
    def test_wrapper_returns_arch_result(self)
```

### skills\design\tests\test_validate_design.py
```
  def _terminal_id() -> str
  def _state_dir() -> Path
  def _state_file() -> Path
  def _flag_path(run_id) -> Path
  def _attempt_path(run_id) -> Path
  def _minimal_payload() -> dict
  def _write_draft(payload, tmpdir) -> Path
  def _run_validate(draft_path, mode, run_id) -> tuple[int, str, str]
  class TestDesignPayloadSchema()
    def test_minimal_payload_roundtrip(self)
    def test_from_dict_missing_required_field(self)
    def test_bottleneck_evidence_roundtrip(self)
    def test_bottleneck_none_not_in_export(self)
    def test_critic_finding_severity_enum(self)
    def test_cap_boundaries(self)
  class TestValidateLogic()
    def _validate(self) -> list[str]
    def test_valid_payload_no_errors(self)
    def test_rejects_empty_run_id(self)
    def test_rejects_bad_mode(self)
    def test_rejects_bad_scope(self)
    def test_rejects_empty_ast_summary(self)
    def test_rejects_short_adr(self)
    def test_rejects_missing_critic_findings(self)
    def test_rejects_missing_claim_verification(self)
    def test_rejects_claim_without_evidence(self)
    def test_rejects_unverified_claim_with_counterexample(self)
    def test_performance_domain_requires_bottleneck(self)
    def test_performance_domain_bottleneck_missing_fields(self)
    def test_boundary_missing_producer(self)
    def test_boundary_missing_consumer(self)
  class TestValidateDesignScript()
    def test_valid_payload_succeeds(self, tmp_path)
    def test_invalid_payload_fails(self, tmp_path)
    def test_missing_file_fails(self, tmp_path)
    def test_invalid_json_fails(self, tmp_path)
    def test_attempt_limit_enforced(self, tmp_path)
    def test_success_cleans_up_attempt_file(self, tmp_path)
    def test_usage_error_on_missing_args(self)
    def test_adr_saved_on_success(self, tmp_path)
```

### skills\design\tests\test_validate_templates.py
```
  class TestPrintStatus()
    def test_print_status_pass_outputs_green_checkmark(self, capsys)
    def test_print_status_fail_outputs_red_x(self, capsys)
    def test_print_status_info_outputs_indented_message(self, capsys)
    def test_print_status_warn_outputs_yellow_warning(self, capsys)
  class TestLoadTemplateContent()
    def test_load_template_content_reads_markdown_file(self, tmp_path)
    def test_load_template_content_handles_missing_file(self, tmp_path)
    def test_load_template_content_handles_empty_file(self, tmp_path)
  class TestExtractHeadings()
    def test_extract_headings_finds_single_heading(self)
    def test_extract_headings_finds_multiple_headings(self)
    def test_extract_headings_handles_heading_with_text(self)
    def test_extract_headings_handles_empty_content(self)
    def test_extract_headings_preserves_heading_format(self)
  class TestLoadContracts()
    def test_load_contracts_loads_yaml_file(self, tmp_path)
    def test_load_contracts_handles_missing_file(self, tmp_path)
    def test_load_contracts_handles_empty_yaml(self, tmp_path)
  class TestValidateRequiredHeadings()
    def test_validate_required_headings_all_present(self, tmp_path)
    def test_validate_required_headings_missing_some(self, tmp_path)
    def test_validate_required_headings_empty_required_list(self, tmp_path)
  class TestCheckDuplicateLogic()
    def test_check_duplicate_logic_no_duplicates(self)
    def test_check_duplicate_logic_detects_50_percent_overlap(self)
    def test_check_duplicate_logic_ignores_low_overlap(self)
    def test_check_duplicate_logic_checks_all_sections(self)
  class TestValidateAll()
    def test_validate_all_returns_zero_on_success(self, mock_print, mock_load, mock_contracts, tmp_path)
    def test_validate_all_returns_one_on_failure(self, mock_print, mock_load, mock_contracts, tmp_path)
    def test_validate_all_checks_all_templates(self, mock_print, mock_load, mock_contracts, tmp_path)
    def test_validate_all_reports_missing_templates(self, mock_print, mock_load, mock_contracts)
```

### skills\design\validate.py
```
  class TemplateValidator()
    def __init__(self, resources_dir) -> None
    def _check_file_exists(self, template_names) -> ArchResult[list[str]]
    def _extract_section_content(self, content, section_name) -> str | None
    def _calculate_line_overlap(self, text1, text2) -> float
    def _check_duplicates(self, template_names) -> ArchResult[list[str]]
    def _check_permissions(self, template_names) -> ArchResult[list[str]]
    def validate_templates(self, template_names) -> ArchResult[list[str]]
  def validate_templates(template_names) -> ArchResult[list[str]]
```

### skills\design\validate_design.py
```
  def _terminal_id() -> str
  def _state_dir() -> Path
  def _state_file() -> Path
  def _load_payload(path) -> tuple[DesignPayload | None, list[str]]
  def _validate_logic(payload) -> list[str]
  def _check_attempt_limit(run_id) -> tuple[bool, int]
  def _increment_attempt(run_id, count) -> None
  def _write_flag(run_id) -> str
  def _save_adr(run_id, adr_markdown, mode) -> str
  def validate(draft_path, mode, run_id) -> bool
  def main() -> None
```

### skills\design\validate_templates.py
```
  class ValidationResult()
  def print_status(message, status) -> None
  def _load_template_content_cached(path_str, mtime, size) -> str
  def load_template_content(template_path) -> str
  def extract_headings(content) -> list[str]
  def load_contracts(contracts_path) -> Optional[dict[str, Any]]
  def validate_required_headings(template_name, template_path, contract_headings) -> tuple[bool, list[str]]
  def _extract_section_content(content, section_name) -> Optional[str]
  def _calculate_line_overlap(text1, text2) -> float
  def check_duplicate_logic(fast_content, deep_content) -> list[tuple[str, float, str, str]]
  def validate_template_chain(chain) -> tuple[bool, str]
  def _validate_template_dir(template_dir) -> None
  def validate_all(template_dir) -> int
  def main() -> None
```

### skills\docs-validate\resources\validate_docs.py
```
  class DocumentationValidator()
    def __init__(self, docs_dir)
    def validate(self)
```

### skills\docs-validate\tests\test_docs_validate_skill.py
```
  class TestDocsValidateSkillTriggering()
    def test_skill_file_exists(self)
    def test_skill_frontmatter(self)
    def test_skill_description_trigger_phrases(self)
  class TestDocsValidateWorkflow()
    def test_workflow_detects_circular_references(self, tmp_path)
    def test_workflow_detects_incomplete_content(self, tmp_path)
    def test_workflow_detects_version_conflicts(self, tmp_path)
  class TestDocsValidateIntegration()
    def test_uses_package_validator(self)
    def test_suggests_fixes_for_issues(self, tmp_path)
  class TestDocsValidateExamples()
    def test_circular_reference_example(self)
    def test_incomplete_content_example(self)
  class TestDocsValidateQuality()
    def test_skill_body_lean(self)
    def test_skill_imperative_form(self)
    def test_skill_progressive_disclosure(self)
```

### skills\go-ct\hooks\PreToolUse_go_invocation_receipt.py
```
  def _is_go_invocation(prompt) -> bool
  def main() -> None
```

### skills\go-ct\hooks\Stop_enforce_gate.py
```
  def _skill_invoked_via_ledger(session_id) -> bool
  def _skill_invoked_via_artifacts() -> bool
  def _skill_actually_invoked() -> bool
  def main() -> None
```

### skills\go-ef\hooks\Stop_enforce_gate.py
```
  def main() -> None
```

### skills\go-pi\scripts\resolve_model.py
```
  def resolve(model_name) -> str | None
  def main() -> None
```

### skills\go-pi\scripts\review_transcript.py
```
  def parse_transcript(lines) -> list[dict[str, Any]]
  def extract_tool_events(messages) -> list[dict[str, Any]]
  def review(transcript_path, task) -> dict[str, Any]
  def _extract_text(content) -> str
  def main() -> None
```

### skills\go-pi\tests\test_resolve_model.py
```
  class TestModelResolution()
    def test_m27_resolves_to_minimax(self)
    def test_glm51_resolves_to_zai(self)
    def test_unknown_model_returns_none(self)
    def test_empty_string_returns_none(self)
    def test_model_map_covers_all_tiers(self)
  class TestResolverScript()
    def test_resolves_from_file(self, tmp_path, monkeypatch)
    def test_override_tier_passes_through(self, tmp_path, monkeypatch)
    def test_missing_selection_file_exits(self, tmp_path, monkeypatch)
```

### skills\go-pi\tests\test_review_transcript.py
```
  def _make_session_header() -> str
  def _make_tool_call(name, arguments, call_id) -> str
  def _make_tool_result(tool_name, call_id, is_error, text) -> str
  class TestParseTranscript()
    def test_valid_jsonl(self, tmp_path) -> None
    def test_skips_blank_and_invalid(self) -> None
  class TestExtractToolEvents()
    def test_extracts_read_and_write(self) -> None
    def test_ignores_non_tool_content(self) -> None
  class TestReview()
    def test_clean_transcript_no_warnings(self, tmp_path) -> None
    def test_blind_write_detected(self, tmp_path) -> None
    def test_no_files_written_detected(self, tmp_path) -> None
    def test_forbidden_file_detected(self, tmp_path) -> None
    def test_excessive_calls_warning(self, tmp_path) -> None
    def test_tool_errors_reported(self, tmp_path) -> None
    def test_scope_untouched_warning(self, tmp_path) -> None
    def test_edit_counts_as_write(self, tmp_path) -> None
```

### skills\go2\scripts\classify_complexity.py
```
  def _bucket(value, thresholds) -> int
  def _task_type_weight(task_type) -> int
  def _score_to_tier(score, max_possible) -> str
  def _is_decisive(signals) -> bool
  def classify(task) -> dict[str, Any]
  def _result(tier, signals) -> dict[str, Any]
  def main() -> None
  def _write_output(result) -> None
```

### skills\go2\scripts\go_safe.py
```
  def now_iso() -> str
  def write_json(path, payload) -> None
  def write_text(path, content) -> None
  def run_git(args, root_dir) -> tuple[int, str, str]
  def die(error, artifact_dir, run_id) -> None
  def require_file(path, artifact_dir, run_id) -> None
  def infer_args() -> tuple[str, str, str, str]
  def main() -> int
```

### skills\go2\scripts\init_go_run.py
```
  def now_iso() -> str
  def write_json(path, payload) -> None
  def write_text(path, content) -> None
  def run_git(args, root_dir) -> str
  class TaskCandidate()
  def infer_route(task) -> tuple[str, str, str, dict[str, bool], list[str]]
  def parse_plan_md(plan_path) -> list[TaskCandidate]
  def parse_args() -> argparse.Namespace
  def build_explicit_task(args) -> TaskCandidate
  def main() -> int
```

### skills\go2\scripts\loop-check.py
```
  (empty)
```

### skills\go2\scripts\pr-artifacts.py
```
  (empty)
```

### skills\go2\scripts\review-passes.py
```
  def _build_pass_content(pass_name, depth) -> str
```

### skills\go2\scripts\select-task.py
```
  (empty)
```

### skills\go2\scripts\validate_go_contracts.py
```
  def load_json(path) -> Any
  def load_schemas(schema_dir) -> dict[str, dict[str, Any]]
  def infer_schema_key(file_path) -> str | None
  def validate_file(file_path, schemas) -> tuple[bool, str]
  def validate_directory(artifact_dir, schemas) -> int
  def main() -> int
```

### skills\go2\scripts\verify-task.py
```
  def _check_scope_drift(task, state_dir, f) -> list[str]
```

### skills\go2\scripts\write_dispatch_result.py
```
  def now_iso() -> str
  def update_run_file(run_path, status, final_promise, notes) -> None
  def update_dispatch_result(artifact_dir, run_id, final_status, wait_state) -> None
  def emit_promise(final_status) -> None
  def main() -> int
```

### skills\go2\tests\test_classify_complexity.py
```
  def _make_task() -> dict
  class TestPresetComplexity()
    def test_high_preset_returns_t4_glm(self)
    def test_low_preset_returns_t1_m27(self)
  class TestConfigTasks()
    def test_config_with_many_forbidden_files_still_t1(self)
    def test_config_with_no_verification(self)
  class TestImplementationTasks()
    def test_simple_implementation_t1(self)
    def test_complex_implementation_t3(self)
  class TestDesignTasks()
    def test_design_with_large_scope_reaches_t4(self)
  class TestConfidence()
    def test_uniform_signals_high_confidence(self)
    def test_divergent_signals_medium_confidence(self)
  class TestTierModelMap()
    def test_t1_t2_t3_all_m27(self)
    def test_t4_is_glm51(self)
  class TestOverride()
    def test_override_env_var(self, monkeypatch, tmp_path)
```

### skills\go2\tests\test_go_safe.py
```
  def test_go_safe_importable()
  def test_go_safe_exit_1_when_invalid_args()
```

### skills\planning\__lib\adversarial_review.py
```
  class AdversarialReviewContext()
    def as_dict(self) -> dict[str, Any]
  class DispatchSpec()
  def is_multi_llm_enabled() -> bool
  def detect_terminal_id() -> str
  def sanitize_plan_name(plan_path) -> str
  def build_adversarial_review_context(plan_path) -> AdversarialReviewContext
  def write_workflow_stage(context, stage) -> Path
  def prepare_adversarial_review_context(plan_path) -> AdversarialReviewContext
  def resolve_prompt_template(template) -> str
  def parse_reference_dispatch_prompts(reference_text) -> dict[str, tuple[str, str, str]]
  def load_reference_dispatch_prompts(reference_path) -> dict[str, tuple[str, str, str]]
  def build_dispatch_specs(context) -> list[DispatchSpec]
  def validate_findings_output_path(agent, returned_path, context) -> bool
  def validate_findings_file(findings_path) -> dict[str, Any]
  def collect_findings_status(context) -> dict[str, Any]
```

### skills\planning\__lib\arch_handoff_state.py
```
  def _utc_now() -> datetime
  def _utc_now_iso() -> str
  def get_terminal_id() -> str
  def get_session_id() -> str
  def get_state_dir() -> Path
  def get_terminal_state_dir(terminal_id) -> Path
  def get_staging_dir(terminal_id) -> Path
  def get_receipt_ttl_seconds() -> int
  def normalize_path(path) -> str
  def plan_sha256(plan_path) -> str | None
  def _plan_key(plan_path) -> str
  def _legacy_receipt_filename(plan_path, terminal_id) -> Path
  def _receipt_filename(plan_path, terminal_id, snapshot_id) -> Path
  def _receipt_glob(plan_path) -> str
  def _serialize_json(data) -> str
  def _compute_checksum(data) -> str
  def _write_json_atomic(path, data, terminal_id) -> None
  def _parse_iso_datetime(value) -> datetime | None
  def _is_expired(snapshot) -> bool
  def _extract_resume_snapshot(envelope) -> dict[str, Any]
  def _extract_receipt_body(envelope) -> dict[str, Any]
  def _flatten_envelope(envelope, receipt_path) -> dict[str, Any]
  def _flatten_legacy_receipt(receipt, receipt_path) -> dict[str, Any]
  def _read_receipt_payload(receipt_path) -> tuple[dict[str, Any], str] | None
  def _candidate_receipt_paths(plan_path, terminal_id) -> list[Path]
  def _load_latest_matching_receipt(plan_path, terminal_id) -> tuple[dict[str, Any], Path] | None
  def _extract_resume_metadata(arch_output) -> tuple[str | None, str | None]
  def record_arch_handoff_receipt(plan_path, arch_output) -> dict[str, Any]
  def load_arch_handoff_receipt(plan_path) -> dict[str, Any] | None
  def find_pending_arch_handoff_receipt(plan_path) -> dict[str, Any] | None
  def mark_arch_handoff_consumed(plan_path) -> dict[str, Any] | None
```

### skills\planning\__lib\auto_fix.py
```
  def extract_sections(plan) -> dict[str, tuple[str, int, int]]
  def normalize_headers(plan) -> tuple[str, list[str]]
  def reorder_sections(plan) -> tuple[str, list[str]]
  def ensure_frontmatter(plan) -> str
  def update_status_header(plan, new_status) -> tuple[str, list[str]]
  def update_source_header(plan, source_path) -> tuple[str, list[str]]
  def update_unresolved_blockers(plan, unresolved_blockers) -> tuple[str, list[str]]
  def fix_plan(plan_path, new_status, source_path, unresolved_blockers, reorder) -> dict
  def main() -> None
```

### skills\planning\__lib\auto_verify.py
```
  def extract_section_content(plan, section_name) -> str
  def is_stateful_plan(plan) -> bool
  def parse_frontmatter(plan) -> dict[str, str]
  def _parse_int_frontmatter(frontmatter, key) -> int | None
  def _looks_like_adr_artifact(plan, frontmatter, plan_path) -> bool
  def detect_source_adr_path(plan, frontmatter, plan_path) -> str | None
  def detect_source_artifact_path(plan, frontmatter) -> str | None
  def extract_source_headings(source_text) -> list[str]
  def detect_source_artifact_path(plan, frontmatter) -> str | None
  def extract_source_headings(source_text) -> list[str]
  def _has_negative_declaration(section_text) -> bool
  def _strip_negative_declaration_sections(plan) -> str
  def _resolve_evidence_path(raw_path, plan_path) -> Path | None
  def _resolve_file_reference(raw_path, plan_path) -> list[Path]
  def _file_line_count(path) -> int
  def _paragraphs_with_layer_signals(plan) -> list[str]
  def _current_state_cited_files(plan, plan_path) -> list[Path]
  def _extract_added_state_fields(plan) -> list[tuple[str, str | None]]
  def _extract_hook_visible_fields(plan) -> list[str]
  def _extract_phase_headings(plan) -> list[int]
  def _extract_phase_precondition_blocks(frontmatter) -> list[int]
  def _extract_deferred_blocker_phases(plan) -> list[int]
  def infer_phase_ready_through(plan, frontmatter) -> int | None
  def _is_contract_sensitive(plan, frontmatter) -> bool
  def check_contract_sensitivity_contradictions(plan) -> list[dict[str, Any]]
  def extract_requirements(plan) -> list[dict[str, str]]
  def _strip_code_fences(text) -> str
  def _has_non_placeholder_acceptance_text(text) -> bool
  def _extract_acceptance_body(task_block) -> str
  def _keyword_set(text) -> set[str]
  def extract_tasks(plan) -> list[dict[str, Any]]
  def _implementation_change_blocks(plan) -> list[tuple[str, str]]
  def check_status_header(plan) -> list[dict[str, Any]]
  def check_placeholders(plan) -> list[dict[str, Any]]
  def check_plan_purity(plan) -> list[dict[str, Any]]
  def check_section_completeness(plan) -> list[dict[str, Any]]
  def check_adr_ingestion_contract(plan, plan_path) -> list[dict[str, Any]]
  def check_source_ingestion_contract(plan, plan_path) -> list[dict[str, Any]]
  def check_ambiguous_contracts(plan) -> list[dict[str, Any]]
  def check_state_model_completeness(plan) -> list[dict[str, Any]]
  def check_stateless_contradictions(plan) -> list[dict[str, Any]]
  def check_unresolved_core_decisions(plan) -> list[dict[str, Any]]
  def check_boundary_overload(plan) -> list[dict[str, Any]]
  def check_claim_schema_consistency(plan) -> list[dict[str, Any]]
  def check_contract_test_coherence(plan) -> list[dict[str, Any]]
  def check_existing_flow_overlap(plan, plan_path) -> list[dict[str, Any]]
  def check_state_extension_contracts(plan) -> list[dict[str, Any]]
  def check_stateful_failure_mode_tests(plan) -> list[dict[str, Any]]
  def check_change_component_alignment(plan) -> list[dict[str, Any]]
  def check_parser_failure_policy(plan) -> list[dict[str, Any]]
  def check_helper_reference_clarity(plan, plan_path) -> list[dict[str, Any]]
  def check_duplicate_implementations(plan, plan_path) -> list[dict[str, Any]]
  def check_assumption_schema_contradictions(plan) -> list[dict[str, Any]]
  def check_open_question_blockers(plan) -> list[dict[str, Any]]
  def check_contract_boundary_matrix(plan) -> list[dict[str, Any]]
  def _is_code_identifier_like(path) -> bool
  def check_evidence_file_targets(plan, plan_path) -> list[dict[str, Any]]
  def check_layer_execution_semantics(plan) -> list[dict[str, Any]]
  def check_conditional_trigger_clarity(plan) -> list[dict[str, Any]]
  def check_planning_contract_authority_drift(plan) -> list[dict[str, Any]]
  def check_mechanism_triggerability(plan) -> list[dict[str, Any]]
  def check_solo_dev_violations(plan) -> list[dict[str, Any]]
  def check_rtm_coverage(requirements, tasks) -> list[dict[str, Any]]
  def check_status_readiness(plan, findings) -> list[dict[str, Any]]
  def load_review_findings(findings_path) -> list[dict[str, Any]]
  def parse_dispositions(summary_path) -> dict[str, str]
  def check_dispositions(plan_path, plan) -> list[dict[str, Any]]
  def _detect_stale_review_summary(summary_text, result) -> str | None
  def _candidate_review_summary_paths(plan_path) -> list[Path]
  def annotate_stale_review_artifacts(plan_path, result) -> dict[str, Any]
  def validate_adversarial_agents() -> dict[str, Any]
  def classify_next_action(status, findings) -> dict[str, Any]
  def _current_arch_finding_ids(findings) -> list[str]
  def _mode_checks_light() -> list
  def _mode_checks_readiness() -> list
  def _mode_checks_contract() -> list
  def _get_checks_for_mode(mode) -> list
  def check_contract_authority_refs(plan) -> list[dict[str, Any]]
  def check_boundary_matrix_rows(plan) -> list[dict[str, Any]]
  def verify_plan(plan_path, plan_content, mode) -> dict[str, Any]
  def cleanup_plan_artifacts(plans_dir, retention_seconds) -> dict[str, Any]
  def main() -> None
```

### skills\planning\tests\test_adversarial_review.py
```
  def test_prepare_adversarial_review_context_creates_terminal_scoped_workspace(tmp_path, monkeypatch) -> None
  def test_resolve_prompt_template_rejects_unresolved_dispatch_tokens() -> None
  def test_reference_prompt_contract_uses_explicit_findings_paths() -> None
  def test_build_dispatch_specs_uses_reference_prompts_and_exact_terminal_paths(tmp_path, monkeypatch) -> None
  def test_validate_findings_output_path_rejects_stale_root_level_return(tmp_path, monkeypatch) -> None
  def test_collect_findings_status_rejects_wrong_path_even_if_stale_root_file_exists(tmp_path, monkeypatch) -> None
  def test_validate_findings_file_rejects_stale_and_mismatched_payloads(tmp_path) -> None
```

### skills\planning\tests\test_auto_fix.py
```
  def test_auto_fix_does_not_reorder_sections_by_default(tmp_path) -> None
  def test_auto_fix_reorders_sections_only_when_requested(tmp_path) -> None
```

### skills\planning\tests\test_auto_fix_v2.py
```
  class TestNormalizeHeaders()
    def test_double_space_after_header_normalized(self) -> None
    def test_no_space_after_header_normalized(self) -> None
    def test_trailing_whitespace_removed(self) -> None
    def test_multiple_headers_normalized(self) -> None
  class TestReorderSections()
    def test_sections_reordered_to_canonical_order(self) -> None
    def test_unknown_sections_preserved(self) -> None
    def test_frontmatter_preserved(self) -> None
    def test_title_preserved(self) -> None
    def test_section_aliases_mapped(self) -> None
  class TestUpdateStatusHeader()
    def test_status_updated_when_exists(self) -> None
    def test_status_added_when_missing(self) -> None
    def test_no_change_when_no_frontmatter(self) -> None
  class TestUpdateSourceHeader()
    def test_source_updated_when_exists(self) -> None
    def test_source_added_when_missing(self) -> None
  class TestFixPlanIntegration()
    def test_fix_plan_returns_only_structural_fixes(self) -> None
    def test_fix_plan_complete_no_changes(self) -> None
    def test_fix_plan_does_not_insert_placeholders(self) -> None
    def test_fix_plan_status_update(self) -> None
    def test_fix_plan_unresolved_blockers_update(self) -> None
  class TestNoPlaceholderInsertion()
    def test_get_placeholder_does_not_exist(self) -> None
    def test_add_missing_sections_does_not_exist(self) -> None
    def test_no_placeholder_constants(self) -> None
```

### skills\planning\tests\test_auto_verify_v2.py
```
  class TestPlaceholderDetection()
    def test_placeholder_detected(self, placeholder) -> None
    def test_concrete_content_not_flagged(self) -> None
  class TestStatusHeader()
    def test_valid_status_draft(self) -> None
    def test_valid_status_in_review(self) -> None
    def test_valid_status_implementation_ready(self) -> None
    def test_missing_status_header(self) -> None
    def test_invalid_status_value(self) -> None
  class TestPlanPurity()
    def test_raw_findings_header_detected(self) -> None
    def test_verification_results_detected(self) -> None
    def test_blocker_high_headers_detected(self) -> None
    def test_pure_plan_passes(self) -> None
  class TestStatusReadiness()
    def test_claims_ready_but_has_high_findings(self) -> None
    def test_claims_ready_with_no_findings_passes(self) -> None
    def test_draft_with_high_findings_passes(self) -> None
  class TestContractSensitiveReadiness()
    def test_open_questions_blocker_detected(self) -> None
    def test_missing_contract_matrix_fields_detected(self) -> None
    def test_plan_artifact_authority_drift_detected(self) -> None
  class TestSectionCompleteness()
    def test_all_required_sections_present(self) -> None
    def test_missing_problem_section(self) -> None
  class TestSoloDevViolations()
    def test_team_coordination_detected(self) -> None
    def test_stakeholder_approval_detected(self) -> None
    def test_negation_excludes_false_positive(self) -> None
  class TestRTM()
    def test_no_tasks_blocked(self) -> None
    def test_tasks_without_acceptance_detected(self) -> None
    def test_acceptance_criteria_with_bold_colon_inside_is_recognized(self) -> None
    def test_acceptance_placeholder_body_does_not_count(self) -> None
    def test_goal_paragraph_falls_back_to_single_requirement(self) -> None
    def test_task_block_blank_lines_do_not_hide_acceptance(self) -> None
  class TestVerifyPlanIntegration()
    def test_plan_with_placeholders_blocked(self, tmp_path) -> None
    def test_pure_plan_with_acceptance_ready(self, tmp_path) -> None
    def test_contradiction_blocks_ready(self, tmp_path) -> None
    def test_explicit_stateless_provider_plan_skips_state_model_gates(self, tmp_path) -> None
    def test_stateless_plan_with_real_state_signals_is_blocked(self, tmp_path) -> None
    def test_provider_coordination_signals_still_trigger_state_model_checks(self, tmp_path) -> None
    def test_infers_phase_ready_through_from_deferred_blockers(self, tmp_path) -> None
    def test_infers_phase_ready_through_from_phase_preconditions(self, tmp_path) -> None
    def test_missing_disposition_artifacts_block_ready(self, tmp_path) -> None
    def test_organizational_restructure_plan_with_not_applicable_sections_is_not_stateful_or_contract_sensitive(self, tmp_path) -> None
    def test_structural_restructure_plan_ignores_negative_sections_and_rollback_restore_text(self, tmp_path) -> None
    def test_real_boundary_table_overrides_negative_contract_sensitive_declaration(self, tmp_path) -> None
    def test_contradictory_review_summary_is_marked_stale(self, tmp_path) -> None
  class TestAdrIngestionRouting()
    def test_shallow_adr_transcription_stays_local_to_planning(self, tmp_path) -> None
  class TestSourceIngestionRouting()
    def test_current_adr_artifact_is_treated_as_local_normalization_issue(self, tmp_path) -> None
    def test_solution_notes_with_source_packet_stay_local_to_planning(self, tmp_path) -> None
  class TestExecutionSemanticsAndEvidence()
    def test_explicit_file_reference_must_exist(self, tmp_path) -> None
    def test_explicit_line_reference_must_be_in_range(self, tmp_path) -> None
    def test_layered_plan_requires_explicit_execution_semantics(self, tmp_path) -> None
    def test_vague_conditional_layer_requires_trigger_signal(self, tmp_path) -> None
    def test_defined_trigger_signal_passes_execution_checks(self, tmp_path) -> None
    def test_existing_mode_system_overlap_requires_explicit_coexistence_or_replacement(self, tmp_path) -> None
    def test_hook_visible_field_requires_provenance_contract(self, tmp_path) -> None
    def test_stateful_extension_requires_failure_mode_tests(self, tmp_path) -> None
    def test_well_specified_state_extension_avoids_new_state_extension_findings(self, tmp_path) -> None
    def test_change_block_component_mismatch_is_flagged(self, tmp_path) -> None
    def test_parser_dependent_state_requires_failure_policy(self, tmp_path) -> None
    def test_undefined_helper_reference_is_flagged(self, tmp_path) -> None
    def test_assumption_schema_contradiction_is_flagged(self, tmp_path) -> None
```

### skills\planning\tests\test_planning_integration_v2.py
```
  class TestStrictReadinessGate()
    def test_placeholder_blocks_implementation_ready(self, tmp_path) -> None
    def test_raw_findings_blocks_implementation_ready(self, tmp_path) -> None
    def test_contradiction_blocks_implementation_ready(self, tmp_path) -> None
    def test_concrete_plan_reaches_ready(self, tmp_path) -> None
  class TestStatusLifecycle()
    def test_draft_to_in_review_allowed(self, tmp_path) -> None
  class TestArchHandoffResumePersistence()
    def test_pending_arch_receipt_prevents_reinvocation_and_marks_consumed_after_rewrite(self, tmp_path, monkeypatch) -> None
    def test_stale_plan_sha_does_not_suppress_new_arch_invocation(self, tmp_path, monkeypatch) -> None
    def test_expired_receipt_does_not_suppress_new_arch_invocation(self, tmp_path, monkeypatch) -> None
    def test_receipts_are_terminal_scoped(self, tmp_path, monkeypatch) -> None
    def test_receipt_survives_same_terminal_session_change(self, tmp_path, monkeypatch) -> None
    def test_corrupt_receipt_is_ignored_instead_of_crashing(self, tmp_path, monkeypatch) -> None
    def test_draft_with_placeholder_stays_draft(self, tmp_path) -> None
  class TestPlanArtifactPurity()
    def test_verification_result_not_in_plan(self, tmp_path) -> None
  class TestCompactResilience()
    def test_load_review_findings_handles_malformed_json(self, tmp_path) -> None
    def test_load_review_findings_handles_empty_file(self, tmp_path) -> None
    def test_idempotency_rejects_wrong_plan_path(self, tmp_path) -> None
    def test_idempotency_accepts_correct_plan_path(self, tmp_path) -> None
    def test_cleanup_plan_artifacts_removes_stale_files(self, tmp_path) -> None
    def test_cleanup_plan_artifacts_handles_nonexistent_dir(self, tmp_path) -> None
    def test_cleanup_removes_multiple_stale_artifact_types(self, tmp_path) -> None
    def test_check_dispositions_handles_missing_summary(self, tmp_path) -> None
    def test_validate_adversarial_agents_returns_correct_structure(self) -> None
  class TestAdversarialAgentValidation()
    def test_missing_agents_reported(self) -> None
```

### skills\pre-mortem\__lib\__init__.py
```
  (empty)
```

### skills\pre-mortem\__lib\feedback_loop.py
```
  def _resolve_artifacts_dir(skill_name) -> Path
  def _get_terminal_id() -> str
  class PreMortemFeedbackLoop()
    def __init__(self, memory_dir)
    def get_pending_validations(self, days_threshold) -> list[Path]
  def extract_critique_lessons(session_dirs) -> list[dict]
  def _extract_severity_items(content, severity) -> list[str]
```

### skills\pre-mortem\__lib\premortem_io.py
```
  def _get_terminal_id() -> str
  def _resolve_artifacts_dir(skill_name) -> Path
  class PreMortemSession()
    def __init__(self, staging_root)
    def _sessions_file(cls, staging_root) -> Path
    def _load_registry(cls, staging_root) -> dict[str, dict]
    def _atomic_write_json(path, data) -> None
    def _save_registry(self, staging_root) -> None
    def find_or_create_session(cls, staging_root) -> PreMortemSession
    def setup(self) -> PreMortemSession
    def _git_sha(self) -> str
    def _write_source_metadata(self) -> None
    def _validate_evidence_citations(self, p1_findings_path) -> None
    def _update_work_hash(self) -> None
    def _update_source_metadata_work_md5(self, md5) -> None
    def _work_hash_changed(self) -> bool
    def write_work(self, content) -> Path
    def read_work(self) -> str
    def write_phase(self, phase, content) -> Path
    def read_phase(self, phase) -> str
    def get_work_file(self) -> Path
    def get_phase_file(self, phase) -> Path
    def get_session_dir(self) -> Path
    def get_specialists_dir(self) -> Path
    def cleanup(self) -> dict[str, list[str]]
    def _ensure_files(self) -> None
  def get_recent_sessions(limit) -> list[dict]
  def cleanup_old_sessions(age_days, dry_run) -> dict[str, list[str]]
```

### skills\pre-mortem\hooks\Stop_hook_premortem_quality_gate.py
```
  def run(data) -> dict
  def _write_premortem_changelog(data) -> None
```

### skills\pre-mortem\tests\__init__.py
```
  (empty)
```

### skills\pre-mortem\tests\test_critique_io.py
```
  class TestPreMortemSessionInit()
    def test_init_creates_timestamp_and_session_dir(self, tmp_path)
    def test_init_uses_provided_staging_root(self, tmp_path)
    def test_init_uses_default_staging_root(self)
    def test_files_dict_starts_empty(self, tmp_path)
  class TestSetup()
    def test_setup_creates_session_dir(self, tmp_path)
    def test_setup_initializes_files_dict(self, tmp_path)
    def test_setup_initializes_files_dict_with_correct_paths(self, tmp_path)
    def test_setup_returns_self_for_chaining(self, tmp_path)
  class TestWriteReadWork()
    def test_write_and_read_work(self, tmp_path)
    def test_write_work_creates_file(self, tmp_path)
    def test_read_work_after_write(self, tmp_path)
  class TestWriteReadPhase()
    def test_write_and_read_phase_1(self, tmp_path)
    def test_write_and_read_phase_2(self, tmp_path)
    def test_write_and_read_phase_3(self, tmp_path)
    def test_read_phase_via_method(self, tmp_path)
    def test_write_phase_2_verifies_filename(self, tmp_path)
    def test_write_phase_3_verifies_filename(self, tmp_path)
  class TestGetSessionDir()
    def test_get_session_dir_returns_session_dir(self, tmp_path)
  class TestGetSpecialistsDir()
    def test_get_specialists_dir_creates_if_missing(self, tmp_path)
  class TestCleanup()
    def test_cleanup_removes_session_dir(self, tmp_path)
    def test_cleanup_returns_dict_with_removed_and_errors(self, tmp_path)
  class TestTerminalId()
    def test_get_terminal_id_returns_string(self)
    def test_get_terminal_id_deterministic(self)
  class TestEnsureFiles()
    def test_ensure_files_calls_setup_if_files_empty(self, tmp_path)
    def test_write_phase_also_ensures_files(self, tmp_path)
  class TestSourceMetadata()
    def test_setup_writes_source_metadata_json(self, tmp_path) -> None
    def test_write_work_backfills_work_md5(self, tmp_path) -> None
    def test_source_metadata_work_md5_changes_with_content(self, tmp_path) -> None
    def test_source_metadata_git_sha_determined_at_setup(self, tmp_path) -> None
```

### skills\pre-mortem\tests\test_critique_io_concurrent.py
```
  def _worker_save_registry(args) -> None
  def test_concurrent_save_registry_integrity(tmp_path) -> None
  def test_atomic_write_json_produces_valid_json(tmp_path) -> None
  def test_atomic_write_json_overwrites(tmp_path) -> None
```

### skills\pre-mortem\tests\test_p1_initial_review_procedure.py
```
  class TestFreshSession()
    def test_session_dir_does_not_exist_initially(self, tmp_path)
    def test_setup_creates_specialists_dir(self, tmp_path)
    def test_ensuring_specialists_dir_before_idempotency_check_is_safe(self, tmp_path)
  class TestInterruptedDispatch()
    def test_partial_specialist_json_exists(self, tmp_path)
    def test_idempotency_check_detects_missing_specialists(self, tmp_path)
  class TestAllComplete()
    def test_all_json_and_markers_present(self, tmp_path)
  class TestPartialResults()
    def test_invalid_json_detected(self, tmp_path)
  class TestManifestBasedResume()
    def test_manifest_records_dispatched_specialists(self, tmp_path)
    def test_manifest_enables_skip_of_completed_specialists(self, tmp_path)
```

### skills\profile\__lib\profiler.py
```
  class Profiler()
    def __init__(self, baseline_path)
    def _load_baselines(self) -> dict
    def _save_baselines(self) -> None
    def measure(self, target) -> dict
    def _measure_import_time(self, target) -> float
    def _measure_complexity(self, target) -> dict
    def _count_lines(self, target) -> int
    def save_baseline(self, target, metrics) -> None
    def get_baseline(self, target) -> dict | None
    def compare(self, target, current_metrics) -> dict
```

### skills\profile\__main__.py
```
  def main() -> int
```

### skills\prompt-audit\scripts\audit_skill.py
```
  def audit_skill(target) -> dict[str, Any]
  def _check_p1(scripts) -> dict[str, Any]
  def _check_p2(scripts, md_text) -> dict[str, Any]
  def _check_p3(scripts, md_text) -> dict[str, Any]
  def _check_p4(scripts, md_text) -> dict[str, Any]
  def _check_p5(scripts, md_text) -> dict[str, Any]
  def _check_p6(md_text) -> dict[str, Any]
  def _check_p7(scripts) -> dict[str, Any]
  def _check_p8(md_text) -> dict[str, Any]
  def _verdict(status, file, note) -> dict[str, Any]
  def _print_summary(target, patterns) -> None
  def main() -> None
```

### skills\rca\hooks\hook_error_rca.py
```
  def get_settings_file() -> Path
  def get_hooks_dir() -> Path
  def validate_state_dir(state_dir) -> Path
  def validate_hook_path(hook_path, hooks_dir) -> bool
  def validate_diagnostics_dir(diagnostics_dir, hooks_dir) -> Path
  def get_state_dir() -> Path
  def get_cc_errors() -> Path
  def _load_settings() -> dict
  class HookRegistration()
  class HookTestResult()
  def resolve_hook_file(command) -> Path | None
  def validate_matcher_pattern(matcher, tool_name) -> tuple[bool, str]
  def enumerate_registrations(event_type, tool_name) -> list[HookRegistration]
  def _load_cc_errors_entries() -> list[dict]
  def _extract_hook_from_error_type(error_type) -> str
  def _is_timeout_entry(entry) -> bool
  def build_diagnostic_sweep(registrations, cc_errors_entries, hours) -> dict
  def build_signal_source_verification(test_results, registrations) -> dict
  def check_recent_errors(hook_name, hours, use_regex, return_metadata, _cached_entries) -> list[dict] | dict
  def test_hook_isolated(reg, tool_name) -> HookTestResult
  def _stage1_enumerate(event_type, tool_name) -> list[HookRegistration]
  def _stage2_test(registrations, tool_name) -> tuple[list[HookTestResult], dict[str, list]]
  def _stage3_classify(test_results, registrations, tool_name, event_type, error_log_evidence) -> list[str]
  def _save_state(event_type, tool_name, registrations, test_results, root_causes, error_log_evidence) -> dict
  def run_full_investigation(event_type, tool_name) -> dict
  def _get_verdict(result) -> str
  def _get_hook_file(result) -> str
  def no_handwave_gate(test_results, root_cause_statement) -> tuple[bool, str]
  def main()
```

### skills\rca\hooks\PostToolUse_rca_action_tracker.py
```
  def get_current_terminal_id() -> str
  def get_action_file_path(session_id) -> Path
  def truncate_for_preview(text, max_length) -> str
  def sanitize_tool_input(tool_input) -> dict
  def load_actions_graph(session_id, terminal_id) -> dict
  def save_actions_graph(graph, session_id) -> None
  def record_action(graph, action_type, tool_used, tool_input, tool_output, phase, terminal_id) -> dict
  def check_divergence(graph, expected_path) -> dict | None
  def main()
```

### skills\rca\hooks\PostToolUse_rca_init.py
```
  def validate_stdin_payload(raw_stdin) -> dict
  def normalize_skill_name(value) -> str
  def extract_skill_name(data) -> str
  def get_current_terminal_id() -> str
  def initialize_state() -> dict
  def main()
```

### skills\rca\hooks\PostToolUse_rca_phase_tracker.py
```
  def detect_phase_from_output(output) -> int
  def detect_phase_from_tool(tool_name, tool_input) -> int
  def detect_execution(tool_name, tool_input, tool_output) -> bool
  def detect_successful_tool_execution(payload) -> bool
  def detect_delegation(tool_name, tool_input, tool_output) -> bool
  def detect_problem_type(tool_output) -> str | None
  def check_auto_research_trigger(tool_output) -> dict | None
  def detect_diagnostic_sweep(tool_output) -> bool
  def main()
```

### skills\rca\hooks\PostToolUse_rca_research_storage.py
```
  def extract_library_from_research(query, results) -> str | None
  def extract_content_from_results(results) -> str
  def main()
```

### skills\rca\hooks\PostToolUse_rca_search_validator.py
```
  def validate_stdin_payload(raw_stdin) -> dict
  def classify_search_pattern(pattern) -> str
  def get_current_terminal_id() -> str
  def load_search_state() -> dict
  def save_search_state(state) -> None
  def extract_grep_pattern(tool_input) -> str
  def should_warn_user(state) -> tuple[bool, str]
  def main()
```

### skills\rca\hooks\SessionEnd_rca_cleanup.py
```
  def ingest_rca_to_cks(state)
  def extract_findings_from_state(state) -> dict
  def cleanup_active_session(state) -> None
  def main()
```

### skills\rca\hooks\StopHook_rca_contract.py
```
  class BandAidState(TypedDict)
  def _get_logger()
  def _get_current_turn_tools(tool_events) -> set[str]
  def _load_turn_scoped_tool_events(session_id, terminal_id) -> list[dict]
  def _has_verification_this_turn(tool_events) -> bool
  def _contains_transcript_only_claim(content) -> bool
  def _normalize_section_name(name) -> str
  def _get_section(sections, field) -> str
  def _parse_hypotheses_from_text(text) -> list[dict[str, str]]
  def _is_absence_claim(text) -> bool
  def _count_diverse_tools(tool_events) -> int
  def _extract_sections(response) -> dict[str, str]
  def _section_exists(sections, field) -> bool
  def _section_has_current_turn_evidence(sections, field) -> bool
  def _find_function_mentions(func_name) -> int
  def _extract_function_names(text) -> list[str]
  def _count_hypothesis_rows(hypothesis_text) -> int
  def _check_dead_code_auto(executed_path, root_cause, falsifier) -> list[str]
  def _has_call_site_evidence(executed_path, evidence) -> bool
  def _load_band_aid_state(terminal_id) -> BandAidState
  def _save_band_aid_state(terminal_id, state) -> None
  def _extract_fix_files(fix_text) -> list[str]
  def _check_band_aid_chain(fix_text, terminal_id) -> list[str]
  def _extract_file_paths_from_path(executed_path) -> list[str]
  def _get_file_mtime(file_path) -> float | None
  def _check_stale_execution_path(executed_path, rca_timestamp) -> list[str]
  def _contains_unverified_token(text) -> bool
  def _detect_single_rc_escape(response) -> bool
  def _detect_urgency(response) -> bool
  def _format_structured_feedback(block_reasons, hypothesis_details) -> str
  def _validate_evidence_tier_labels(evidence) -> list[str]
  def _validate_adversarial_hypothesis(sections, tool_events) -> list[str]
  def _validate_artifact_paths_exist(sections) -> list[str]
  def _extract_artifact_paths(evidence_text) -> list[str]
  def _validate_evidence_bindings(sections, tool_events, session_id, terminal_id) -> list[str]
  def _validate_rca_contract(data, response, tool_events, rca_turn, session_id, terminal_id, rca_timestamp) -> tuple[bool, list[str]]
  def check(data) -> dict | None
  def run(data) -> dict | None
```

### skills\rca\hooks\StopHook_rca_enforcement.py
```
  def get_current_terminal_id() -> str
  def load_hook_error_gate()
  def is_state_stale(state) -> bool
  def main()
```

### skills\rca\hooks\StopHook_rca_reflector.py
```
  def _get_state_file(session_id, terminal_id) -> Path
  def _load_state(session_id, terminal_id) -> dict
  def _save_state(session_id, terminal_id, state) -> None
  def _cleanup_stale_state_files() -> None
  def _detect_premature_convergence(response, alt_count) -> str | None
  def _is_catch22_spiral(state, tool_name, error) -> bool
  def _update_catch22_state(state, tool_name, error) -> dict
  def _has_evidence_free_fix(response) -> bool
  def _detect_zero_plan(response, tool_event_count) -> str | None
  def check(data) -> dict | None
  def run(data) -> dict | None
```

### skills\rca\tools\priority_inference.py
```
  class PriorityFactors()
  class PriorityInference()
    def __init__(self, state_dir) -> None
    def _get_default_state_dir() -> Path
    def calculate_priority_score(self, file_path) -> int
    def get_priority_factors(self, file_path) -> PriorityFactors
    def _get_error_frequency_score(self, file_path) -> float
    def _get_recent_change_score(self, file_path) -> float
    def _get_complexity_score(self, str_path) -> float
    def _get_test_coverage_score(self, file_path) -> float
  class ComplexityAnalyzer(NodeVisitor)
    def __init__(self) -> None
    def visit_FunctionDef(self, node) -> None
    def visit_If(self, node) -> None
    def visit_For(self, node) -> None
    def visit_While(self, node) -> None
    def visit_Try(self, node) -> None
  def calculate_priority_score(file_path, state_dir) -> int
  def rank_contexts(contexts, state_dir) -> list[tuple[str, int]]
  def main() -> None
```

### skills\rca\tools\telemetry_discovery.py
```
  def discover_telemetry(since_days) -> dict[str, Any]
  def print_telemetry_summary(results) -> None
  def query_events_db(keyword, since_days, limit) -> list[dict[str, Any]]
  def find_relevant_logs(results, keyword) -> list[dict[str, Any]]
  def main() -> None
```

### skills\refactor\hooks\ledger_append.py
```
  (empty)
```

### skills\refactor\hooks\PostToolUse_refactor_transition.py
```
  def run(input_data) -> dict | None
  def main()
```

### skills\refactor\hooks\PostToolUse_refactor_validator.py
```
  def validate_tool_output(data) -> dict
  def extract_errors(output) -> list
  def run(input_data) -> dict | None
  def main()
```

### skills\refactor\hooks\PreToolUse_refactor_gate.py
```
  def run(input_data) -> dict | None
  def main()
```

### skills\refactor\hooks\state_manager_refactor.py
```
  def write_state(phase, allowed_tools, evidence, expires_in)
  def append_ledger(step, event, session_id)
  def read_state() -> dict | None
  def clear_state()
  def get_current_phase_evidence(phase) -> dict
  def advance_if_complete(current_phase, evidence) -> str | None
```

### skills\refactor\hooks\Stop_refactor_verifier.py
```
  def get_git_tags() -> list[str]
  def read_ledger_entries(session_id) -> list[dict]
  def get_artifacts_dir(state) -> Path
  def check_artifacts(state) -> list[str]
  def verify(state) -> dict
  def run(input_data) -> dict | None
  def main()
```

### skills\refactor\scripts\__init__.py
```
  (empty)
```

### skills\refactor\scripts\ast_refactor_helpers.py
```
  class TransformResult()
  def safe_transform_file(file_path, transformer) -> TransformResult
  class LibCSTTransformer(CSTTransformer)
    def __init__(self) -> None
    def _increment(self) -> None
  class RenameAttribute(LibCSTTransformer)
    def __init__(self, old_name, new_name, class_name) -> None
    def leave_Attribute(self, original_node, updated_node) -> cst.Attribute
  class RemoveUnusedImport(LibCSTTransformer)
    def __init__(self, import_name) -> None
    def leave_Name(self, original_node) -> cst.Name | cst.RemoveFromParent
    def leave_Import(self, original_node) -> cst.Import | cst.RemoveFromParent
    def leave_ImportFrom(self, original_node) -> cst.ImportFrom | cst.RemoveFromParent
  class ExtractMethodConfig()
  class ExtractMethodTransformer(LibCSTTransformer)
    def __init__(self, config) -> None
    def visit_FunctionDef(self, node) -> cst.CSTNode
    def leave_FunctionDef(self, original_node, updated_node) -> cst.FunctionDef
  def extract_method_callsafe(file_path, target_function, new_method, call_args) -> TransformResult
  class _FunctionFinder(CSTVisitor)
    def __init__(self, target) -> None
    def visit_FunctionDef(self, node) -> None
  def diff_sources(original, new, file_path) -> str
```

### skills\refactor\scripts\code_scanner.py
```
  def scan_code_patterns(session_files) -> list[dict]
  def _get_marker_metadata(marker_type, description, state_impact) -> dict
  def _detect_state_impact(description) -> str
```

### skills\refactor\scripts\complexity_scanner.py
```
  def _cc_to_risk(cc) -> tuple[int, str, str]
  def scan_complexity(file_paths, min_cc) -> list[dict[str, Any]]
```

### skills\refactor\scripts\deduplicate.py
```
  def deduplicate_findings(findings_files, output_path) -> dict[str, Any]
  def _tier_for_confidence(confidence) -> str
  def deduplicate_and_save(artifacts_dir, target_name, terminal_id) -> Path
```

### skills\refactor\scripts\evidence_collector.py
```
  class PhaseEvidence()
  class FindingEvidence()
  def collect_test_evidence(test_path, phase, finding_id, artifacts_dir) -> PhaseEvidence
  def verify_tdd_red(finding_id, test_path, artifacts_dir) -> tuple[bool, PhaseEvidence]
  def verify_tdd_green(finding_id, test_path, artifacts_dir) -> tuple[bool, PhaseEvidence]
  def verify_regression(finding_id, test_paths, artifacts_dir) -> tuple[bool, list[PhaseEvidence]]
  def get_evidence_collector(finding_id, artifacts_dir) -> FindingEvidence | None
  def save_finding_evidence(finding_id, file, line, description, artifacts_dir) -> None
  def _store_phase_evidence(evidence, artifacts_dir) -> None
```

### skills\refactor\scripts\plan_review.py
```
  def adversarial_review_plan(plan) -> dict[str, Any]
  def _review_change(change) -> list[str]
  def _review_strategy(plan) -> list[str]
  def _assess_plan_risks(plan, findings) -> list[str]
  def _generate_recommendations(plan, findings) -> list[str]
  def _overall_assessment(plan, findings) -> str
  def review_to_markdown(review) -> str
```

### skills\refactor\scripts\refactor_plan.py
```
  def create_refactor_plan(findings, target_path, session_id) -> dict[str, Any]
  def _assess_change_risk(finding) -> str
  def _suggest_rollback(finding) -> str
  def plan_to_markdown(plan) -> str
  def save_plan(plan, output_dir) -> Path
  def load_plan(plan_path) -> dict[str, Any] | None
```

### skills\refactor\scripts\run_scan.py
```
  (empty)
```

### skills\refactor\scripts\scan_t.py
```
  (empty)
```

### skills\refactor\scripts\worst_finding.py
```
  (empty)
```

### skills\sqa\__lib\__init__.py
```
  (empty)
```

### skills\sqa\__lib\sqa_evidence_patterns.py
```
  def check_execution_evidence(text) -> tuple[bool, list[str]]
  def has_heavy_tables(text) -> bool
  def get_fabrication_error_message() -> str
  def validate_sqa_response(response_text, check_for_completion) -> tuple[bool, str]
```

### skills\sqa\__lib\sqa_state_tracker.py
```
  class LayerState()
  class SQAState()
    def to_dict(self) -> dict
    def from_dict(cls, data) -> SQAState
  def get_sanitized_terminal_id() -> str
  def _get_state_path(session_id) -> Path
  def _write_halt_flag(layer, findings_count) -> None
  def is_halted() -> bool
  def clear_halt_flag() -> None
  def init_state(target, halt_on) -> SQAState
  def record_layer_complete(layer, findings, skipped, reason) -> SQAState
  def record_halt(layer) -> SQAState
  def load_state(session_id) -> SQAState | None
  def _write_state(state) -> None
  def clear_state(session_id) -> None
  def add_findings(layer, findings) -> SQAState
  def get_accumulated_findings(session_id) -> list[dict]
  def get_rns_summary(session_id) -> dict
  def _category_to_domain(category) -> str
```

### skills\sqa\orchestrator.py
```
  class HaltExceededThreshold(Exception)
  class SeverityHaltTracker()
    def should_halt(self, findings) -> bool
    def get_halt_message(self, findings) -> str
  def check_halt(layer_name, findings) -> None
  class L2State()
  def _atomic_write(path, data) -> None
  def _get_terminal_state_dir() -> Path
  def _validate_target(target) -> Path
  def _check_command(cmd) -> None
  def save_report(report, _path) -> None
```

### skills\sqd\__init__.py
```
  (empty)
```

### skills\sqd\__lib\__init__.py
```
  (empty)
```

### skills\sqd\__main__.py
```
  def main() -> int
```

### skills\sqd\layers\__init__.py
```
  (empty)
```

### skills\sqd\layers\dispatcher.py
```
  def _read_target_content(target) -> str
  def _parse_pi_jsonl(raw_output) -> dict | None
  def _score_from_finding(finding) -> float
  def _normalize_finding(result) -> dict
  def dispatch_single(target, model, output_dir) -> dict
  def _parse_freeform_review(stdout) -> dict
  def dispatch_parallel(target, models, output_dir) -> int
  def synthesize(findings, output_dir) -> None
```

### skills\sqd\tests\conftest.py
```
  (empty)
```

### skills\sqd\tests\test_dispatcher.py
```
  class TestScoreFromFinding()
    def test_score_extraction(self, payload, expected)
  class TestParsePiJsonl()
    def test_agent_end_with_assistant_content(self)
    def test_agent_end_with_error(self)
    def test_message_update_text_delta_accumulates(self)
    def test_empty_input(self)
    def test_invalid_lines_skipped(self)
  class TestDispatchParallel()
    def output_dir(self, tmp_path)
    def test_consensus_all_same_score_bucket(self, output_dir)
    def test_divergent_scores_different_buckets(self, output_dir)
    def test_model_failure_returns_exit_2(self, output_dir)
    def test_empty_models_list_returns_exit_3(self, output_dir)
    def test_synthesis_writes_findings_array(self, output_dir)
  class TestDispatchSingleErrors()
    def test_unknown_model_raises_value_error(self, tmp_path)
  def test_cli_importable()
  def test_pi_model_map_coverage()
```

### skills\t\__main__.py
```
  def main(target, force_full, mode) -> int
  def _run_discovery_mode(target, _force_full) -> int
  def _run_bisect_mode(target, _force_full) -> int
  def _run_comprehensive_mode(target, force_full) -> int
  def _get_terminal_id()
  def _resolve_target_path(target)
  def _run_smart_mode(target, _force_full) -> int
  def _run_execution_mode(target, force_full) -> int
```

### skills\t\__main__imports.py
```
  (empty)
```

### skills\t\code_map.py
```
  class CodeMapVisualizer()
    def __init__(self, codemap)
    def generate_layer_view(self) -> str
    def generate_dependency_graph(self) -> str
    def generate_test_heatmap(self, test_results) -> str
    def _extract_layers(self) -> dict[str, list[str]]
    def _format_layers_ascii(self, layers) -> str
    def _format_dependencies(self, relationships) -> str
    def _format_test_heatmap(self, file_structure, test_results) -> str
```

### skills\t\cognitive_guardrails.py
```
  [error]
```

### skills\t\conftest.py
```
  def pytest_configure(config)
  def test_session_setup()
  def temp_dir()
  def cleanup_stale_locks()
  def cleanup_threads()
  def safe_timeout(timeout_seconds)
  def requires_external_resources()
  def slow_test()
  def reset_state()
  def pytest_runtest_makereport(item, call)
  def pytest_collection_modifyitems(config, items)
  def track_memory_usage()
```

### skills\t\coverage_trends.py
```
  class CoverageTrendTracker()
    def __init__(self, trends_path)
    def _load_trends(self) -> dict[str, list[dict]]
    def _save_trends(self) -> None
    def record_coverage(self, module, coverage_percent, lines_covered, lines_total) -> None
    def analyze_trend(self, module, days) -> dict[str, Any]
    def get_degrading_modules(self, threshold) -> list[dict[str, Any]]
```

### skills\t\director_output.py
```
  class TestStrictness(NamedTuple)
  def determine_strictness(risk_score) -> TestStrictness
  def format_director_report(work_context, risk_score, strictness, test_results, coverage_results) -> str
```

### skills\t\failure_grouping.py
```
  class FailureGrouper()
    def __init__(self, similarity_threshold)
    def _similarity(self, s1, s2) -> float
    def _extract_error_signature(self, error_message, stack_trace) -> str
    def group_failures(self, failed_tests) -> list[dict[str, Any]]
    def format_grouped_failures(self, groups) -> str
```

### skills\t\flaky_detection.py
```
  class FlakyTestDetector()
    def __init__(self, history_path)
    def _load_history(self) -> dict[str, list[dict]]
    def _save_history(self) -> None
    def record_run(self, test_name, passed, error_message, runtime_seconds) -> None
    def analyze_flakiness(self, test_name, min_runs) -> dict[str, Any]
    def get_all_flaky_tests(self) -> list[dict[str, Any]]
```

### skills\t\incremental_testing.py
```
  def map_modules_to_tests(codemap) -> dict[str, list[str]]
  def calculate_incremental_scope(target_files, codemap) -> dict[str, Any]
  def format_incremental_report(scope) -> str
```

### skills\t\modes\__init__.py
```
  (empty)
```

### skills\t\modes\bisect_mode.py
```
  class BisectResult()
  def run_bisect(good_commit, bad_commit, test_command) -> BisectResult
  def format_bisect_report(result) -> str
```

### skills\t\modes\discovery_mode.py
```
  class TestInfo()
  class DiscoveryResults()
  def _resolve_target_path(target) -> Path
  def _get_terminal_id() -> str
  def discover_tests(target) -> DiscoveryResults
  def _find_test_files(target) -> list[Path]
  def _parse_test_file(file_path) -> list[TestInfo]
  def _classify_test(test_name, file_name) -> str
  def _classify_by_type(tests) -> dict[str, int]
  def _run_health_check(_target) -> list[dict]
  def _scan_solo_dev_patterns(target) -> list[dict]
  def _run_pytest_coverage(_target) -> dict | None
  def _identify_gaps(results, _target) -> list[str]
  def format_discovery_report(results) -> str
  def save_test_gaps(results, project_root, terminal_id) -> None
```

### skills\t\profiling.py
```
  class TestProfiler()
    def __init__(self, profile_path)
    def _load_profiles(self) -> dict[str, list[dict]]
    def _save_profiles(self) -> None
    def record_test_time(self, test_name, runtime_seconds) -> None
    def get_slow_tests(self, threshold_seconds) -> list[dict[str, Any]]
    def get_recommendations(self) -> list[str]
```

### skills\t\risk_scoring.py
```
  def _ensure_import_paths() -> None
  class Tier(Enum)
  class Size(Enum)
  class Kind(Enum)
  class ChangeContext()
  def calculate_risk_score(ctx) -> float
  def detect_change_context(file_path, git_state) -> ChangeContext
```

### skills\t\router.py
```
  def detect_mode_from_prompt(user_input) -> str
  def get_conversation_context() -> str
```

### skills\t\t_core.py
```
  def _ensure_import_paths() -> None
  class WorkContext()
  def extract_context_from_conversation() -> WorkContext
  def _infer_work_type_from_git(project_path) -> str
  def trace_code_flow(target_files, codemap) -> tuple[list[str], list[tuple[str, str]]]
  def load_testing_config() -> dict[str, Any]
```

### skills\t\test_cache.py
```
  def calculate_file_hash(file_path) -> str
  def calculate_test_key(test_file, dependencies) -> str
  class TestCache()
    def __init__(self, cache_path)
    def _load_cache(self) -> dict[str, Any]
    def _save_cache(self) -> None
    def get(self, test_key) -> dict[str, Any] | None
    def set(self, test_key, result, dependencies, runtime_seconds) -> None
    def invalidate(self, file_path) -> int
    def get_stats(self) -> dict[str, Any]
```

### skills\t\tests\test_code_map.py
```
  def test_generate_layer_view()
  def test_generate_layer_view_empty_codemap()
  def test_generate_dependency_graph()
  def test_generate_dependency_graph_empty_relationships()
  def test_generate_test_heatmap()
  def test_generate_test_heatmap_missing_results()
  def test_extract_layers_keyword_matching()
  def test_format_dependencies_limit()
  def test_format_layers_limit()
```

### skills\t\tests\test_director_output.py
```
  def test_determine_strictness_high_risk()
  def test_determine_strictness_high_risk_upper_bound()
  def test_determine_strictness_medium_risk()
  def test_determine_strictness_medium_risk_lower_boundary()
  def test_determine_strictness_low_risk()
  def test_determine_strictness_zero_risk()
  def test_determine_strictness_always_runs_health_check()
  def test_determine_strictness_always_runs_solo_dev_scan()
  def test_format_director_report_high_risk()
  def test_format_director_report_medium_risk()
  def test_format_director_report_low_risk()
  def test_format_director_report_empty_work_context()
  def test_format_director_report_no_coverage_results()
  def test_format_director_report_missing_coverage_empty()
  def test_format_director_report_decision_table_structure()
```

### skills\t\tests\test_flaky_detection.py
```
  def test_record_run_storage()
  def test_record_run_multiple()
  def test_record_run_history_trimming()
  def test_analyze_flakiness_no_history()
  def test_analyze_flakiness_insufficient_runs()
  def test_analyze_flakiness_stable_passing()
  def test_analyze_flakiness_stable_failing()
  def test_analyze_flakiness_flaky_pass_rate()
  def test_analyze_flakiness_true_flaky()
  def test_analyze_flakiness_collects_different_errors()
  def test_analyze_flakiness_ignores_empty_errors()
  def test_get_all_flaky_tests_empty()
  def test_get_all_flaky_tests_sorted()
  def test_get_all_flaky_tests_excludes_stable()
  def test_history_persists_to_disk()
  def test_history_handles_corrupted_file()
```

### skills\t\tests\test_opt_out_flags.py
```
  def sample_adaptive_test_code()
  def test_tot_enabled_by_default(sample_adaptive_test_code)
  def test_no_tot_flag_disables_tot(sample_adaptive_test_code)
  def test_default_behavior_quality_first()
  def test_flag_parsing_conceptual()
  def test_environment_variable_disables_tot(sample_adaptive_test_code)
  def test_environment_variable_false_allows_tot(sample_adaptive_test_code)
  def test_tot_branch_generation_quality(sample_adaptive_test_code)
  def test_tot_opt_out_constitutional_compliance()
  def test_tot_independent_of_other_enhancements()
  def test_tot_quality_first_design()
```

### skills\t\tests\test_risk_scoring.py
```
  def test_risk_score_determinism() -> None
  def test_high_risk_thresholds() -> None
  def test_low_risk_thresholds() -> None
```

### skills\t\tests\test_test_cache.py
```
  def test_calculate_file_hash_consistency()
  def test_calculate_file_hash_different_content()
  def test_calculate_file_hash_nonexistent()
  def test_calculate_test_key_test_file_only()
  def test_calculate_test_key_with_dependencies()
  def test_calculate_test_key_deterministic()
  def test_calculate_test_key_with_nonexistent_dependency()
  def test_cache_get_set()
  def test_cache_get_missing()
  def test_cache_set_increments_hits()
  def test_cache_persists_to_disk()
  def test_cache_invalidate_by_dependency()
  def test_cache_invalidate_no_match()
  def test_cache_get_stats_empty()
  def test_cache_get_stats_with_entries()
  def test_cache_handles_corrupted_cache_file()
```

### skills\t\tests\test_windows_ipc.py
```
  def test_acquire_release_basic() -> None
  def test_stale_lock_detection() -> None
  def test_atomic_cache_write() -> None
  def test_cache_interrupt_recovery() -> None
```

### skills\t\windows_ipc.py
```
  class LockInfo()
    def to_json(self) -> str
    def from_json(cls, json_str) -> LockInfo | None
  class WindowsFileLock()
    def __init__(self, lock_name, cache_dir)
    def acquire(self, timeout_ms, retry_interval_ms) -> LockResult
    def release(self) -> bool
    def read_cache(self) -> dict[str, Any]
    def write_cache(self, data) -> bool
    def _is_stale_lock(self) -> bool
    def _cleanup_stale_lock(self) -> None
```

### skills\task\unresolved_items_detector.py
```
  class UnresolvedItemsDetector()
    def __init__(self, terminal_id, csf_root, max_age_days)
    def detect(self, limit) -> list[dict[str, Any]]
    def _build_search_query(self) -> str
    def _search_chs(self, query, limit) -> list[dict]
    def _filter_unresolved(self, results) -> list[dict]
    def _extract_content(self, result) -> str | None
    def _is_resolved(self, content) -> bool
    def _is_recent_enough(self, timestamp) -> bool
    def _calculate_confidence(self, result, content) -> float
    def _suggest_task_title(self, content) -> str
    def _truncate_content(self, content, max_length) -> str
    def _format_date(self, timestamp) -> str
    def cross_check_with_tasks(self, unresolved_items, completed_tasks) -> list[dict]
  def detect_unresolved_items(terminal_id, limit, max_age_days, completed_tasks) -> list[dict[str, Any]]
```

### skills\tdd_v3.2\gap_loader.py
```
  def _get_terminal_id() -> str
  def load_test_gaps(project_root) -> dict | None
  def format_gap_summary(gap_data) -> str
```

### skills\tdd_v3.2\generate_context.py
```
  def _clean_stale_runs() -> None
  def _get_active_run() -> str | None
  def _detect_test_command(root_dir) -> str
  def _scan_python(path) -> list[str]
  def _scan_js_ts(path) -> list[str]
  def _scan_go(path) -> list[str]
  def _get_workspace_summary(root_dir, max_depth) -> str
  def main() -> None
```

### skills\tdd_v3.2\run_phase.py
```
  def _now_iso() -> str
  def _sha256_file(path) -> str
  def main() -> None
```

### skills\tdd_v3.2\session_models.py
```
  def now_iso() -> str
  class SessionState(BaseModel)
  class PhaseReceipt(BaseModel)
    def compute_signature(self, secret) -> str
    def verify_signature(self, secret) -> bool
  class PhaseReceiptRef(BaseModel)
  class RunMetadata(BaseModel)
  class TddEvidence(BaseModel)
    def paths_must_look_like_test_files(cls, v) -> List[str]
```

### skills\tdd_v3.2\test_task_021_verification.py
```
  def test_evidence_manager_integration()
```

### skills\tdd_v3.2\tests\conftest.py
```
  def mock_time()
  def frozen_time()
  def fast_time()
  def fast_datetime()
```

### skills\tdd_v3.2\tests\test_evidence_integration.py
```
  class TestTDDEvidenceIntegration()
    def test_tdd_hook_imports_evidence_manager(self)
    def test_tdd_evidence_recorder_class_exists(self)
    def test_record_tdd_state_snapshot(self)
    def test_evidence_artifact_directory_creation(self)
    def test_feature_flag_disabled_by_default(self)
    def test_feature_flag_enables_evidence_recording(self)
    def test_evidence_cleanup_after_7_days(self)
```

### skills\tdd_v3.2\tests\test_evidence_tracking.py
```
  class TestEvidenceTrackingModule()
    def test_generate_evidence_artifact_function_exists(self)
    def test_cleanup_old_evidence_function_exists(self)
    def test_is_evidence_tracking_enabled_function_exists(self)
    def test_is_evidence_tracking_enabled_returns_bool(self)
    def test_debug_log_function_exists(self)
  class TestEvidenceArtifactGeneration()
    def setup_method(self)
    def teardown_method(self)
    def test_generate_evidence_artifact_creates_file(self)
    def test_generate_evidence_artifact_contains_timestamp(self)
    def test_generate_evidence_artifact_contains_phase(self)
    def test_generate_evidence_artifact_contains_task_id(self)
  class TestEvidenceCleanup()
    def setup_method(self)
    def teardown_method(self)
    def test_cleanup_old_evidence_removes_artifacts_older_than_7_days(self)
    def test_cleanup_old_evidence_returns_count_of_cleaned_files(self)
    def test_cleanup_old_evidence_keeps_recent_artifacts(self)
    def test_cleanup_old_evidence_handles_empty_directory(self)
```

### skills\tdd_v3.2\tests\test_time_mocking.py
```
  class TestTimeMockingFixture()
    def test_mock_time_fixture_exists(self, mock_time)
    def test_mock_time_freezes_time(self, mock_time)
    def test_mock_time_allows_time_travel(self, mock_time)
    def test_toctou_tests_execute_instantly(self)
  class TestSuitePerformance()
    def test_fast_test_suite_completion(self)
```

### skills\tdd_v3.2\validate_tdd.py
```
  def _sha256_file(path) -> str
  def _output_shows_failure(text) -> bool
  def _output_shows_pass(text) -> bool
  def _parse_iso(ts) -> datetime
  def validate_run(run_id) -> None
```

### skills\uci\__lib\__init__.py
```
  (empty)
```

### skills\uci\__lib\agent_registry.py
```
  def select_agents(mode, include, exclude, change_type, file_extensions) -> List[str]
  def _get_all_agents() -> List[str]
  def get_agent_config(agent_name) -> Dict[str, any]
  def get_token_limit(agent_name) -> int
  def validate_agent_names(agent_names) -> tuple[bool, List[str]]
```

### skills\uci\__lib\agent_triggers.py
```
  class TriggerMatch()
  class AgentTriggerResult()
  def evaluate_agent_triggers(file_paths, file_contents) -> dict[str, AgentTriggerResult]
  def _evaluate_single_agent(agent_name, trigger_def, file_paths, file_contents) -> AgentTriggerResult
  def _get_file_content(file_path, file_contents) -> str
  def get_triggered_agents(file_paths, file_contents, current_mode, current_agents) -> list[str]
  def format_trigger_report(results) -> str
```

### skills\uci\__lib\assessment_mode.py
```
  class AssessmentFinding()
  class AssessmentReport()
    def get_summary(self) -> str
  class AssessmentMode()
    def __init__(self, scope_files)
    def assess_findings(self, raw_findings, agent_name) -> List[AssessmentFinding]
    def _parse_location(self, location) -> tuple[str, str]
    def _get_code_snippet(self, file_path, line_range) -> str
    def _assess_severity(self, finding) -> str
    def _validate_recommendation_quality(self, finding) -> bool
    def generate_report(self, findings) -> AssessmentReport
  def create_assessment_mode(scope_files) -> AssessmentMode
  def run_assessment(raw_findings, agent_name, scope_files) -> AssessmentReport
```

### skills\uci\__lib\blind_spot_detector.py
```
  class CategorySignal()
  class BlindSpotFinding()
  class BlindSpotReport()
  class BlindSpotDetector()
    def __init__(self, state_dir, lookback_days)
    def scan_code_for_risk_signals(self, file_paths, scope) -> list[CategorySignal]
    def get_recent_coverage(self, project_root) -> tuple[dict[str, int], dict[str, str]]
    def detect_blind_spots(self, file_paths, covered_categories, project_root) -> BlindSpotReport
    def render_report(self, report) -> str
```

### skills\uci\__lib\circuit_breaker.py
```
  class CircuitState(Enum)
  class ProviderState()
  class CircuitBreakerConfig()
  class LLMCircuitBreaker()
    def __init__(self, config)
    def _load_state(self) -> None
    def _save_state(self) -> None
    def register_provider(self, name, failure_threshold, success_threshold, timeout_seconds) -> None
    def is_available(self, provider_name) -> bool
    def record_success(self, provider_name) -> None
    def record_failure(self, provider_name, error) -> None
    def get_available_providers(self, preferred_providers) -> List[str]
    def reset_provider(self, provider_name) -> None
    def get_provider_status(self, provider_name) -> Dict[str, Any]
    def get_all_statuses(self) -> Dict[str, Dict[str, Any]]
  class CircuitBreakerMiddleware()
    def __init__(self, circuit_breaker)
    def execute_with_fallback(self, providers, execute_func, context) -> tuple[Any, str]
    def execute_sync_with_fallback(self, providers, execute_func, context) -> tuple[Any, str]
```

### skills\uci\__lib\constitutional_filter.py
```
  class FilterResult()
  class ConstitutionalFilter()
    def __init__(self, strict_mode)
    def filter_findings(self, findings) -> FilterResult
    def _check_constitutional_violation(self, finding) -> Dict[str, str] | None
    def validate_agent_config(self, agent_config) -> bool
    def get_allowed_categories(self) -> Set[str]
    def get_prohibited_patterns(self) -> List[str]
    def is_strict_mode(self) -> bool
    def set_strict_mode(self, strict) -> None
  def create_constitutional_filter(strict_mode) -> ConstitutionalFilter
  def filter_constitutional_violations(findings, strict_mode) -> FilterResult
  def validate_agent_registry_compliance(agent_registry) -> tuple[bool, List[str]]
```

### skills\uci\__lib\context_filter.py
```
  class FilterResult()
  class SoloDevContextFilter()
    def __init__(self, config_path)
    def _load_config(self) -> None
    def filter_findings(self, findings) -> FilterResult
    def _get_finding_text(self, finding) -> str
    def is_solo_dev_safe(self, finding) -> bool
  class PathScopeFilter()
    def __init__(self, custom_patterns)
    def should_exclude_path(self, file_path) -> bool
    def filter_paths(self, file_list, max_files) -> List[str]
    def get_excluded_count(self, file_list) -> Dict[str, int]
  def apply_context_filters(findings, file_list, config_path) -> tuple[List[Dict[str, Any]], FilterResult, Optional[Dict[str, int]]]
  def generate_filter_prompt_directive() -> str
```

### skills\uci\__lib\cross_agent_validation.py
```
  class ValidationResult()
  class LocationKey()
    def __str__(self) -> str
    def from_finding(cls, finding) -> 'LocationKey'
  class CrossAgentValidator()
    def __init__(self, min_consensus, confidence_boost)
    def validate_findings(self, agent_results) -> ValidationResult
    def detect_pre_existing_issues(self, findings, base_diff) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]
    def _parse_diff(self, diff_output) -> Set[str]
  def validate_agent_registry_compliance(agent_registry) -> Tuple[bool, List[str]]
  def validate_findings(agent_results, min_consensus) -> ValidationResult
  def merge_validated_results(validated, unvalidated) -> List[Dict[str, Any]]
```

### skills\uci\__lib\cross_file_analysis.py
```
  class ImportNode()
    def add_import(self, target) -> None
    def add_importer(self, source) -> None
  class CircularDependency()
  class TaintPath()
  class CrossFileAnalyzer()
    def __init__(self, project_root)
    def _detect_language(self) -> str
    def build_import_graph(self, file_list, max_files) -> Dict[str, ImportNode]
    def _extract_imports(self, content, file_path) -> Set[str]
    def detect_circular_dependencies(self, max_depth) -> List[CircularDependency]
    def analyze_taint_propagation(self, file_list, max_files) -> List[TaintPath]
    def _find_matches(self, text, patterns) -> List[str]
    def generate_cross_file_findings(self, file_list) -> List[Dict[str, Any]]
    def _analyze_import_complexity(self) -> List[Dict[str, Any]]
    def get_statistics(self) -> Dict[str, Any]
```

### skills\uci\__lib\formatter.py
```
  class OutputFormat(Enum)
  class FormattedOutput()
  class UCIFormatter()
    def format(self, findings, output_format, tests_pass, context, use_gto_format, use_rsn_format) -> FormattedOutput
    def _enhance_findings(self, findings) -> List[Dict[str, Any]]
    def _format_json(self, findings, verdict_dict, context) -> str
    def _format_markdown(self, findings, verdict_dict, context, use_gto_format, use_rsn_format) -> str
    def format_gto_next_steps(self, findings) -> str
    def _format_summary(self, findings, verdict_dict, context) -> str
    def _format_finding_markdown(self, finding) -> str
    def _group_by_severity(self, findings) -> Dict[str, List[Dict[str, Any]]]
    def _get_technical_domain(self, finding) -> str
    def _group_by_domain(self, findings) -> Dict[str, List[Dict[str, Any]]]
    def save_output(self, formatted, output_path) -> Path
  def format_rsn_from_findings(findings, intent_summary) -> str
```

### skills\uci\__lib\impact_effort.py
```
  class Level(Enum)
  def calculate_impact_effort(finding) -> tuple[Level, Level]
  def _calculate_impact(finding) -> Level
  def _calculate_effort(finding) -> Level
  def impact_effort_to_score(impact, effort) -> int
  def format_impact_effort(impact, effort) -> str
  def sort_findings_by_priority(findings) -> list[Dict[str, Any]]
```

### skills\uci\__lib\intelligent_mode_detector.py
```
  class ContextSignals()
  class ModeDetectionResult()
  def detect_mode_from_context(file_paths, diff_content, change_type, lite_override, full_override) -> ModeDetectionResult
  def _collect_signals(file_paths, diff_content, change_type) -> ContextSignals
  def _select_mode(signals) -> Tuple[str, str, float]
  def _calculate_risk_score(file_paths) -> Tuple[int, List[str]]
  def _is_test_file(path) -> bool
  def _build_reason(reasons, mode) -> str
  def format_mode_detection_message(result) -> str
```

### skills\uci\__lib\memory_integration.py
```
  class AgentConsensus()
  class CrossFileMetadata()
  class ReviewMetadata()
  class MemoryContext()
    def has_context(self) -> bool
    def format_for_prompt(self) -> str
  class MemoryIntegration()
    def __init__(self, enabled)
    def _check_cks_available(self) -> None
    def is_available(self) -> bool
    def retrieve_context(self, review_scope, file_list, mode) -> MemoryContext
    def _extract_domains(self, file_list) -> List[str]
    def _build_search_query(self, review_scope, domains, mode) -> str
    def should_store_finding(self, finding) -> bool
    def prepare_storage_entry(self, finding, review_metadata, agent_consensus, cross_file_metadata) -> Dict[str, Any]
    def extract_review_metadata(self, file_list, mode, git_scope, session_id, line_counts) -> ReviewMetadata
    def extract_agent_consensus(self, validated_findings, location_key) -> AgentConsensus
    def format_storage_prompt(self, findings, review_metadata, validated_results, cross_file_metadata) -> str
    def get_stats(self) -> Dict[str, Any]
```

### skills\uci\__lib\orchestrator.py
```
  class ResultEnvelope()
    def is_valid(self) -> bool
  class AgentResult()
  class OrchestratorConfig()
  class ParallelAgentOrchestrator()
    def __init__(self, config)
    def _validate_agent_tool_use(self, agent_results) -> tuple[List[AgentResult], Dict[str, Any]]
    def select_agents(self, mode, include, exclude, change_type, file_extensions) -> List[str]
    def generate_agent_prompts(self, agents, context) -> Dict[str, str]
    def _build_context_header(self, context) -> str
    def parse_agent_output(self, agent_name, output) -> AgentResult
    def aggregate_findings(self, agent_results, mode, file_list, git_scope, session_id, line_counts, cross_file_stats) -> Dict[str, Any]
    def sanitize_log(self, content) -> str
    def write_agent_log(self, agent_name, prompt, output, result) -> Path
    def write_agent_artifact(self, agent_name, findings, prompt, output) -> str
    def read_agent_artifact(self, artifact_path) -> Optional[Dict[str, Any]]
    def create_result_envelope(self, agent_name, findings, status, prompt, output) -> ResultEnvelope
    def analyze_cross_file(self, file_list, project_root) -> Dict[str, Any]
    def rotate_logs(self) -> int
    def generate_task_calls(self, agents, prompts) -> List[Dict[str, Any]]
    def create_execution_plan(self, mode, include, exclude, change_type, file_extensions, context) -> Dict[str, Any]
    def detect_blind_spots(self, file_paths, covered_categories, project_root) -> Dict[str, Any]
```

### skills\uci\__lib\practicality_filter.py
```
  class PracticalityAssessment()
  class FilterResult()
  class PracticalityFilter()
    def __init__(self, max_time_minutes)
    def filter_findings(self, findings) -> FilterResult
    def _assess_practicality(self, finding) -> PracticalityAssessment
    def _estimate_time(self, text) -> int
    def _assess_complexity(self, time_minutes) -> str
    def _format_time(self, minutes) -> str
    def _suggest_alternative(self, pattern) -> str
  def create_practicality_filter(max_time_minutes) -> PracticalityFilter
  def filter_practical_findings(findings, max_time_minutes) -> FilterResult
  def assess_finding_practicality(finding) -> PracticalityAssessment
```

### skills\uci\__lib\pre_existing.py
```
  class PreExistingResult()
  class PreExistingDetector()
    def __init__(self, base_branch)
    def detect_pre_existing(self, findings, diff_output) -> PreExistingResult
    def _get_git_diff(self) -> str
    def _parse_diff(self, diff_output) -> Tuple[Set[str], Dict[str, Set[int]]]
    def _extract_file_path(self, location) -> str
    def _is_line_in_diff(self, line_number, changed_lines) -> bool
    def format_pre_existing_report(self, result) -> str
  def detect_pre_existing_issues(findings, diff_output, base_branch) -> PreExistingResult
```

### skills\uci\__lib\scope_detector.py
```
  def detect_scope(user_scope, main_branch, master_branch) -> Tuple[str, str]
  def _get_current_branch() -> Optional[str]
  def _has_staged_changes() -> bool
  def get_diff_content(scope_command) -> str
  def parse_changed_files(diff_content) -> list[str]
```

### skills\uci\__lib\sequential_trigger.py
```
  class TriggerCondition(Enum)
  class TriggerResult()
  class SequentialTrigger()
    def __init__(self, quality_first)
    def evaluate_codebase_characteristics(self, code_diff, file_paths) -> list[TriggerCondition]
    def evaluate_early_findings(self, first_wave_findings) -> list[TriggerCondition]
    def should_trigger_sequential(self, code_diff, file_paths, first_wave_findings) -> TriggerResult
  def demo_trigger_logic()
```

### skills\uci\__lib\verdict.py
```
  class Verdict(Enum)
  def synthesize_verdict(findings, tests_pass) -> Dict[str, Any]
  def _determine_verdict(blockers, high, medium, low, tests_pass) -> tuple[str, str, List[str]]
  def format_verdict_summary(verdict_dict) -> str
```

### skills\uci\tests\performance\benchmark_execution.py
```
  def simulate_parallel_agent_execution(agent_count) -> float
  def simulate_sequential_agent_execution(agent_count) -> float
  def calculate_overhead(parallel_time, sequential_time) -> dict[str, float]
  def run_benchmark_suite() -> dict[str, dict]
  def main()
```

### skills\uci\tests\performance\test_multi_terminal_sequential.py
```
  def test_concurrent_terminals()
  def test_shared_state_access()
  def test_race_conditions()
  def main()
```

### skills\uci\tests\test_compat.py
```
  class TestBackwardCompatibility()
    def test_review_skill_exists(self)
    def test_review_skill_delegates_to_uci_triage(self)
    def test_review_skill_triggers(self)
    def test_adversarial_review_skill_exists(self)
    def test_adversarial_review_skill_delegates_to_uci_deep(self)
    def test_adversarial_review_skill_triggers(self)
    def test_migration_guidance_present(self)
  class TestUCISkillExists()
    def test_uci_skill_exists(self)
    def test_uci_skill_has_triggers(self)
    def test_uci_skill_has_mode_parameter(self)
  class TestModeMapping()
    def test_review_maps_to_triage(self)
    def test_adversarial_review_maps_to_deep(self)
```

### skills\uci\tests\test_concurrency.py
```
  class TestOrchestratorConcurrency()
    def test_orchestrator_exists(self)
    def test_orchestrator_has_parallel_class(self)
    def test_orchestrator_has_log_rotation(self)
    def test_orchestrator_has_sanitization(self)
    def test_orchestrator_has_config(self)
  class TestCircuitBreakerConcurrency()
    def test_circuit_breaker_exists(self)
    def test_circuit_breaker_has_llm_circuit_breaker(self)
    def test_circuit_breaker_has_state_enum(self)
    def test_circuit_breaker_has_provider_state(self)
    def test_circuit_breaker_has_health_monitoring(self)
    def test_circuit_breaker_has_failover(self)
  class TestStateIsolation()
    def test_state_directory_isolation(self)
    def test_log_file_locking(self)
    def test_provider_registry_isolation(self)
    def test_memory_isolation(self)
  class TestConcurrencySafety()
    def test_no_race_conditions_in_logging(self)
    def test_atomic_operations(self)
    def test_state_directory_cleanup(self)
  class TestLogRotation()
    def test_log_rotation_mechanism(self)
    def test_log_retention_period(self)
    def test_api_key_sanitization(self)
  class TestDegradedMode()
    def test_degraded_mode_handling(self)
    def test_circuit_state_tracking(self)
  class TestConcurrentAgentExecution()
    def test_parallel_execution_safe(self)
    def test_aggregation_is_thread_safe(self)
  class TestMultiTerminalScenarios()
    def test_simultaneous_reviews_same_repo(self)
    def test_different_scopes_concurrent(self)
  class TestCoreConcurrencyIntegration()
    def test_all_modules_handle_concurrency(self)
```

### skills\uci\tests\test_core.py
```
  class TestScopeDetector()
    def test_scope_detector_exists(self)
    def test_scope_detector_has_detect_scope(self)
    def test_scope_detector_has_scope_type(self)
    def test_scope_detector_priority_order(self)
    def test_scope_detector_exported(self)
  class TestImpactEffort()
    def test_impact_effort_module_exists(self)
    def test_impact_effort_has_calculate_function(self)
    def test_impact_effort_has_level_enum(self)
    def test_impact_effort_has_sort_function(self)
    def test_impact_effort_exported(self)
  class TestVerdictSynthesis()
    def test_verdict_module_exists(self)
    def test_verdict_has_synthesize_function(self)
    def test_verdict_has_verdict_class(self)
    def test_verdict_three_tier_levels(self)
    def test_verdict_exported(self)
  class TestFormatter()
    def test_formatter_module_exists(self)
    def test_formatter_has_uci_formatter_class(self)
    def test_formatter_has_output_format(self)
    def test_formatter_exported(self)
  class TestAssessmentMode()
    def test_assessment_mode_exists(self)
    def test_assessment_mode_has_class(self)
    def test_assessment_mode_has_finding_class(self)
    def test_assessment_mode_has_report_class(self)
    def test_assessment_mode_quality_checks(self)
    def test_assessment_mode_exported(self)
  class TestCoreIntegration()
    def test_all_core_modules_exist(self)
    def test_all_core_modules_exported(self)
```

### skills\uci\tests\test_enhanced_metadata.py
```
  class TestEnhancedMetadataClasses()
    def test_memory_integration_module_exists(self)
    def test_agent_consensus_class_exists(self)
    def test_cross_file_metadata_class_exists(self)
    def test_review_metadata_class_exists(self)
    def test_extract_review_metadata_method_exists(self)
    def test_extract_agent_consensus_method_exists(self)
    def test_prepare_storage_entry_accepts_enhanced_metadata(self)
  class TestOrchestratorEnhancedIntegration()
    def test_orchestrator_imports_enhanced_classes(self)
    def test_orchestrator_has_runtime_reference(self)
    def test_aggregate_findings_signature_has_context_params(self)
    def test_aggregate_findings_extracts_review_metadata(self)
    def test_aggregate_findings_extracts_agent_consensus(self)
    def test_aggregate_findings_builds_cross_file_metadata(self)
    def test_aggregate_findings_calculates_storeable_count(self)
    def test_aggregate_findings_has_enhanced_metadata_tracking(self)
    def test_aggregate_findings_format_storage_with_enhanced_metadata(self)
  class TestEnhancedMetadataErrorHandling()
    def test_extract_review_metadata_has_error_handling(self)
    def test_extract_agent_consensus_has_error_handling(self)
    def test_cross_file_metadata_has_error_handling(self)
    def test_format_storage_prompt_has_error_handling(self)
  class TestStoreableCountCalculation()
    def test_storeable_count_filters_by_severity(self)
    def test_storeable_count_filters_by_confidence(self)
    def test_storeable_count_requires_location(self)
```

### skills\uci\tests\test_modes.py
```
  class TestAgentRegistry()
    def test_agent_registry_exists(self)
    def test_agent_registry_has_mode_agents(self)
    def test_agent_registry_has_agent_registry(self)
    def test_agent_registry_exported(self)
  class TestTriageMode()
    def test_triage_mode_has_logic_agent(self)
    def test_triage_mode_has_tests_agent(self)
    def test_triage_mode_has_security_agent(self)
  class TestStandardMode()
    def test_standard_mode_has_performance_agent(self)
  class TestDeepMode()
    def test_deep_mode_has_conventions_agent(self)
    def test_deep_mode_has_quality_agent(self)
    def test_deep_mode_has_compliance_agent(self)
    def test_deep_mode_has_qa_agent(self)
  class TestComprehensiveMode()
    def test_comprehensive_mode_has_simplification_agent(self)
    def test_comprehensive_mode_has_rca_agent(self)
    def test_comprehensive_mode_has_failure_modes_agent(self)
    def test_comprehensive_mode_has_deployment_safety_agent(self)
    def test_comprehensive_mode_has_python_modernization_agent(self)
    def test_comprehensive_mode_has_test_quality_roi_agent(self)
  class TestAgentTierClassification()
    def test_core_tier_agents_exist(self)
    def test_extended_tier_agents_exist(self)
    def test_comprehensive_tier_agents_exist(self)
  class TestSubagentTypeMapping()
    def test_agent_registry_has_subagent_type(self)
    def test_known_subagent_types_mapped(self)
  class TestModeAgentCounts()
    def test_triage_mode_agent_count(self)
    def test_deep_mode_agent_count(self)
```

### skills\uci\tests\test_new_agents.py
```
  class TestNewAgentRegistration()
    def test_state_machine_agent_registered(self)
    def test_invariants_agent_registered(self)
    def test_io_validation_agent_registered(self)
  class TestNewAgentTierClassification()
    def test_new_agents_have_extended_tier(self)
  class TestTierBasedModeActivation()
    def test_triage_mode_excludes_new_agents(self)
    def test_standard_mode_excludes_new_agents(self)
    def test_deep_mode_includes_state_machine_only(self)
    def test_comprehensive_mode_includes_all_new_agents(self)
  class TestNewAgentSpecFiles()
    def test_state_machine_agent_spec_exists(self)
    def test_invariants_agent_spec_exists(self)
    def test_io_validation_agent_spec_exists(self)
  class TestNewAgentSpecContent()
    def test_state_machine_spec_has_focus(self)
    def test_invariants_spec_has_focus(self)
    def test_io_validation_spec_has_focus(self)
  class TestAdversarialFraming()
    def test_orchestrator_has_adversarial_framework(self)
  class TestTOCTOUEnhancement()
    def test_performance_agent_has_toctou_detection(self)
```

### skills\uci\tests\test_sequential_trigger.py
```
  class TestTriggerCodebaseCharacteristics()
    def test_simple_code_no_triggers(self)
    def test_state_machine_heavy_triggers(self)
    def test_concurrency_heavy_triggers(self)
    def test_security_critical_triggers(self)
    def test_security_critical_by_path(self)
    def test_complex_control_flow_triggers(self)
  class TestTriggerEarlyFindings()
    def test_no_findings_not_worth_cost(self)
    def test_high_finding_density_triggers(self)
    def test_critical_severity_cluster_triggers(self)
    def test_coupled_bug_types_triggers(self)
  class TestShouldTriggerSequential()
    def test_simple_code_no_early_findings_parallel(self)
    def test_state_machine_with_critical_findings_sequential(self)
    def test_security_critical_state_machine_sequential(self)
    def test_utility_code_with_findings_sequential_quality_first(self)
    def test_utility_code_with_findings_parallel_cost_constrained(self)
    def test_no_early_findings_parallel(self)
    def test_state_heavy_coupled_bugs_sequential(self)
```

### skills\uci\tests\validation\__init__.py
```
  (empty)
```

### skills\uci\tests\validation\aggregate_uci_runs.py
```
  def extract_timestamp(filename) -> str | None
  def get_agent_name(filename) -> str
  def load_agent_output(filepath) -> dict
  def extract_findings(agent_output, agent_name) -> list[dict]
  def map_severity(confidence) -> str
  def detect_mode_from_agents(agents) -> str
  def aggregate_runs(state_dir, output_dir) -> int
  def main()
```

### skills\uci\tests\validation\analyze_runs.py
```
  def analyze_bug_categories(runs) -> dict
  def detect_gaps(category_counts, runs) -> dict
  def summarize_modes(runs) -> dict
  def main()
```

### skills\uci\tests\validation\assess_cognitive_load.py
```
  def calculate_cognitive_load(baseline_findings, new_findings) -> dict
  def generate_recommendation(metrics) -> str
  def main()
```

### skills\uci\tests\validation\data_collector.py
```
  class BugCategory(Enum)
    def classify(cls, finding) -> Optional['BugCategory']
  class UCIFinding()
  class UCIRun()
  class UCIRunCollector()
    def __init__(self, log_dir)
    def load_from_logs(self) -> list[dict[str, Any]]
    def extract_findings_by_category(self, run) -> dict[str, list[dict]]
    def detect_missed_bugs(self, uci_run, code_analysis) -> list[dict[str, Any]]
  def validate_finding_schema(finding) -> bool
  def calculate_missed_bug_metrics(runs) -> dict[str, Any]
```

### skills\uci\tests\validation\quantify_missed_bugs.py
```
  def estimate_missed_bugs(runs) -> dict
  def calculate_opportunity_cost(missed_bugs) -> dict
  def estimate_improvement_potential(missed_bugs, opportunity_cost) -> dict
  def main()
```

### skills\uci\tests\validation\run_ab_test.py
```
  def load_baseline_findings(log_dir) -> list
  def simulate_state_machine_agent(codebase_samples) -> list
  def calculate_detection_metrics(baseline_findings, state_findings, num_runs) -> dict
  def main()
```

### skills\uci\tests\validation\test_state_code.py
```
  class Snapshot()
    def __init__(self)
    def mark_complete(self)
    def mark_failed(self)
    def set_data(self, data)
  class Decision()
    def __init__(self)
    def publish(self)
  class TranscriptProcessor()
    def __init__(self, transcript_path)
    def process(self)
  def mark_snapshot_status(snapshot, new_status)
  def evidence_freshness_check(evidence, max_age_seconds)
```

### skills\uci\tests\validation\test_validation_infrastructure.py
```
  class TestDataCollector()
    def test_collector_initialization(self)
    def test_collector_load_from_logs(self)
    def test_collector_extract_findings_by_category(self)
  class TestBugCategoryClassification()
    def test_classify_state_transition_bugs(self)
    def test_classify_toctou_bugs(self)
    def test_classify_id_collision_bugs(self)
    def test_classify_path_validation_bugs(self)
  class TestFindingSchemaValidation()
    def test_valid_finding_schema(self)
    def test_missing_required_fields(self)
    def test_invalid_severity_value(self)
  class TestMissedBugDetection()
    def test_detect_missed_state_bugs(self)
    def test_no_missed_bugs_when_all_found(self)
```

### skills\uci\tests\validation\validate_hypothesis.py
```
  def create_state_focused_prompt(codebase_context) -> str
  def create_generic_prompt(codebase_context) -> str
  def simulate_ab_test(codebase_sample) -> dict
  def calculate_improvement(ab_results) -> dict
  def main()
```

### skills\wiki\scripts\wiki_manifest.py
```
  def sha256_first8(path) -> str
  def make_slug(filename) -> str
  def make_collision_slug(filename, file_path) -> str
  def classify_tier(size) -> str
  def build_manifest(src_dir, ext, log_file, manifest_path, resume) -> dict
  def parse_args() -> argparse.Namespace
  def main() -> int
```

### skills\wiki\tests\test_wiki_manifest.py
```
  class TestClassifyTier()
    def test_safe_below_200k(self)
    def test_safe_at_200k(self)
    def test_large_warn_at_200k_plus_1(self)
    def test_large_warn_at_500k(self)
    def test_large_skip_above_500k(self)
  class TestMakeSlug()
    def test_basic(self)
    def test_parentheses_stripped(self)
    def test_long_slug_truncated(self)
    def test_unicode_falls_back_to_untitled(self)
    def test_mixed_unicode_preserves_ascii_parts(self)
    def test_underscores_converted(self)
  class TestBuildManifest()
    def _make_tmp_file(self, name, content) -> Path
    def test_manifest_with_one_safe_file(self, tmp_path)
    def test_manifest_skips_already_logged_hash(self, tmp_path)
    def test_resume_skips_done_entries(self, tmp_path)
```

### tests\test___main__.py
```
  def test___main___exists()
```

### tests\test_ast_refactor_helpers.py
```
  class DummyTransformer(LibCSTTransformer)
    def __init__(self) -> None
    def visit_Name(self, node) -> None
  class TestSafeTransformFile()
    def test_missing_file_returns_error(self, tmp_path) -> None
    def test_valid_file_parses_and_transforms(self, tmp_path) -> None
    def test_no_change_returns_changed_false(self, tmp_path) -> None
    def test_invalid_python_returns_parse_error(self, tmp_path) -> None
  class TestExtractMethodCallsafe()
    def test_missing_file_returns_error(self, tmp_path) -> None
    def test_nonexistent_function_returns_error(self, tmp_path) -> None
  class TestDiffSources()
    def test_diff_shows_changes(self) -> None
    def test_diff_empty_when_identical(self) -> None
```

### tests\test_complexity_scanner.py
```
  class TestCcToRisk()
    def test_low_cc(self) -> None
    def test_medium_cc(self) -> None
    def test_high_cc(self) -> None
    def test_very_high_cc(self) -> None
  class TestScanComplexity()
    def test_empty_file(self, tmp_path) -> None
    def test_single_low_cc_function(self, tmp_path) -> None
    def test_high_cc_function_found(self, tmp_path) -> None
    def test_method_high_cc(self, tmp_path) -> None
    def test_skips_non_python_files(self, tmp_path) -> None
    def test_skips_nonexistent_file(self) -> None
```

### tests\test_evidence_collector.py
```
  class TestPhaseEvidence()
    def test_phase_evidence_creation(self) -> None
    def test_finding_evidence_phases(self) -> None
  class TestGetEvidenceCollector()
    def test_missing_evidence_returns_none(self, tmp_path) -> None
    def test_loads_stored_evidence(self, tmp_path) -> None
    def test_corrupted_json_returns_none(self, tmp_path) -> None
```

### tests\test_premortem_io.py
```
  def test_premortem_io_exists()
```

### tools\migrate_to_ef.py
```
  def _plural(n, word) -> str
  def validate_layout() -> list[str]
  def resolve_source(base, source_path) -> Path | None
  def resolve_target(target, base) -> Path
  def read_frontmatter(skill_dir) -> dict[str, Any]
  def read_workflow_steps(skill_dir) -> list[str]
  def check_source_structure(source_dir) -> tuple[bool, str, dict[str, Any]]
  def derive_phases_from_source(source_dir, target_name) -> list[dict[str, Any]]
  def register_config(skill_id, phases) -> tuple[bool, str]
  def _build_ef_header(target_name, old_name) -> str
  def _build_stop_hook_block(target_name) -> str
  def generate_skill_md(source_dir, target_name, base_name) -> str
  def generate_stop_hook(target_name) -> str
  def report_dry_run(base, target_name, source_path, target_path, config_status, phases, blockers) -> None
  def apply(base, target_name, source_path, target_path, force, phases) -> None
  def main() -> int
```

### tools\tests\conftest.py
```
  def _clean_ef_artifacts() -> None
  def clean_migrated_skills()
```

### tools\tests\test_migrate_to_ef.py
```
  def _run(args) -> subprocess.CompletedProcess
  class TestMigrateDryRun()
    def test_refactor_dry_run_finds_source(self) -> None
    def test_planning_dry_run_finds_source(self) -> None
    def test_unknown_base_returns_error(self) -> None
  class TestMigrateApply()
    def test_creates_ef_skill_in_temp_fixture(self, tmp_path, monkeypatch) -> None
  class TestMigrateNonDestructive()
    def test_refuses_to_overwrite_without_force(self, tmp_path) -> None
    def test_target_defaults_to_base_minus_ef(self) -> None
    def test_custom_target_name(self) -> None
  class TestMigrateConfigEntry()
    def test_refactor_config_is_new_entry(self) -> None
    def test_plural_singular_grammar(self) -> None
    def test_planning_ef_hook_has_correct_skill_id(self, tmp_path) -> None
  class TestMigrateStopHook()
    def test_stop_hook_contains_target_skill_id(self, tmp_path) -> None
  class TestMigrateValidation()
    def test_layout_check_fails_gracefully(self) -> None
    def test_no_validate_bypasses_naming_check(self) -> None
```

### CLAUDE.md
```
# cc-skills-sdlc

SDLC skills for Claude Code — architecture, planning, code quality, testing, review, and documentation.

## Skills (49)

| Skill | Purpose |
|-------|---------|
| arch | Architecture Advisor (Resource Router) |
| av | Skill Improvement Tool |
| cfg | /cfg - Control Flow Graph Visualization |
| chat-to-decisions | God-Tier Chat-to-Decisions v12 |
| code | /code -- Feature Development Mission Control |
| code-flow-visualizer | Code Flow Visualizer |
| code-review | Code Review — ...
```

### prompt-patterns-catalog.md
```
# Prompt Patterns Catalog

Sourced from:
- `C:\Users\brsth\Downloads\We are working in claude code on windows 11, with (2).md` (windows-11 transcript)
- `C:\Users\brsth\Downloads\You are reviewing an architecture decision record.md` (ADR transcript)

Each card: **name → source → exact text/reference → applicable phase → reusability → known gaps it closes.**

---

## P1 — [FACT]/[INFERENCE]/[RECOMMENDATION] Evidence Contract

**Source:** both transcripts (windows-11 lines 339–465, ADR throughout)...
```
