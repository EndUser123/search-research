# SIGNATURES

## scripts/core/__init__.py

  (no Python definitions)
## scripts/core/main.py

  def get_version([]) -> ?
## scripts/core/sync.py

  def get_source_version([]) -> str
  def update_plugin_json(['version']) -> bool
  def update_readme(['version']) -> bool
  def validate_sync(['version']) -> bool
  def main([]) -> int
## scripts/create_github_repo.py

  def log_info(['msg']) -> None
  def log_success(['msg']) -> None
  def log_warning(['msg']) -> None
  def log_error(['msg']) -> None
  def run_command(['cmd', 'cwd', 'check']) -> subprocess.CompletedProcess
  def check_gh_cli([]) -> bool
  def get_github_username([]) -> str
  def create_with_gh_cli(['package_name', 'target_dir', 'description']) -> bool
  def show_manual_instructions(['package_name', 'target_dir', 'description']) -> None
  def verify_repository(['package_name']) -> bool
  def main([]) -> ?
## scripts/extract_from_monorepo.py

  def log_info(['msg']) -> None
  def log_success(['msg']) -> None
  def log_warning(['msg']) -> None
  def log_error(['msg']) -> None
  def run_command(['cmd', 'cwd', 'check']) -> subprocess.CompletedProcess
  def check_monorepo(['target_dir']) -> bool
  def get_package_path(['target_dir']) -> Optional[str]
  def extract_subtree_split(['target_dir', 'package_name']) -> bool
  def extract_fresh_init(['target_dir', 'package_name']) -> bool
  def main([]) -> ?
## scripts/finalize_github_repo.py

  def log_info(['msg']) -> None
  def log_success(['msg']) -> None
  def log_warning(['msg']) -> None
  def log_error(['msg']) -> None
  def run_command(['cmd', 'cwd', 'check']) -> subprocess.CompletedProcess
  def check_gh_cli([]) -> bool
  def get_github_username([]) -> str
  def get_package_topics(['package_type']) -> list[str]
  def enable_github_pages(['package_name', 'target_dir']) -> bool
  def create_initial_release(['package_name', 'target_dir', 'version', 'generate_notes']) -> bool
  def add_repository_topics(['package_name', 'package_type']) -> bool
  def generate_codeowners(['package_name', 'target_dir', 'username']) -> bool
  def generate_security_md(['package_name', 'target_dir']) -> bool
  def push_updates(['target_dir']) -> bool
  def verify_finalization(['package_name']) -> dict[str, bool]
  def main([]) -> ?
## scripts/scan_package_quality.py

  def log_info(['msg']) -> None
  def log_success(['msg']) -> None
  def log_warning(['msg']) -> None
  def log_error(['msg']) -> None
  def run_command(['cmd', 'cwd', 'check']) -> subprocess.CompletedProcess
  def check_tool_installed(['tool']) -> bool
  def run_bandit_scan(['target_dir', 'fix']) -> dict[str, any]
  def run_safety_scan(['target_dir']) -> dict[str, any]
  def run_pip_audit(['target_dir']) -> dict[str, any]
  def validate_badges(['target_dir']) -> dict[str, any]
  def check_code_quality_metrics(['target_dir']) -> dict[str, any]
  def generate_report(['target_dir', 'bandit_results', 'safety_results', 'audit_results', 'badge_results', 'quality_metrics']) -> dict
  def save_report(['report', 'target_dir']) -> None
  def main([]) -> ?
## scripts/upload_github_videos.py

  class GitHubVideoUploader:
    def get_page_content(['self', 'page']) -> str
    def upload_video(['self', 'page', 'video_path']) -> str
    def run(['self', 'headless']) -> ?
    def generate_readme_update(['self']) -> ?
  def main([]) -> ?
  def __init__(['self', 'repo_url', 'readme_path', 'video_dir', 'session_file']) -> ?
  def get_page_content(['self', 'page']) -> str
  def upload_video(['self', 'page', 'video_path']) -> str
  def run(['self', 'headless']) -> ?
  def generate_readme_update(['self']) -> ?
## scripts/upload_via_issue.py

  def upload_video_via_issue(['video_path', 'repo_url', 'session_file']) -> ?
  def main([]) -> ?
## scripts/upload_via_issue_simple.py

  def main([]) -> ?
## scripts/validate_banner.py

  def log_info(['msg']) -> None
  def log_success(['msg']) -> None
  def log_warning(['msg']) -> None
  def log_error(['msg']) -> None
  class BannerValidator:
    def validate_basic_properties(['self', 'banner_path']) -> dict[str, Any]
    def validate_with_vision_api(['self', 'banner_path']) -> dict[str, Any]
    def validate(['self', 'banner_path']) -> dict[str, Any]
    def print_report(['self', 'results']) -> None
  def main([]) -> ?
  def __init__(['self', 'zai_api_key']) -> ?
  def validate_basic_properties(['self', 'banner_path']) -> dict[str, Any]
  def validate_with_vision_api(['self', 'banner_path']) -> dict[str, Any]
  def validate(['self', 'banner_path']) -> dict[str, Any]
  def print_report(['self', 'results']) -> None
## scripts/validate_media_assets.py

  def log_info(['msg']) -> None
  def log_success(['msg']) -> None
  def log_warning(['msg']) -> None
  def log_error(['msg']) -> None
  def log_manual(['msg']) -> None
  class AssetType:
    def from_path(['cls', 'path']) -> AssetType
  class QualityDomain:
    def description(['self']) -> str
    def tier(['self']) -> str
  class DomainCheckResult:
    def is_complete(['self']) -> bool
  class AssetValidationResult:
    def calculate_completion(['self']) -> None
    def is_ready(['self']) -> bool
    def get_pending_domains(['self']) -> list[QualityDomain]
    def get_failed_domains(['self']) -> list[QualityDomain]
  class MediaAssetValidator:
    def validate(['self', 'asset_path', 'asset_type']) -> AssetValidationResult
  def main([]) -> ?
  def from_path(['cls', 'path']) -> AssetType
  def description(['self']) -> str
  def tier(['self']) -> str
  def is_complete(['self']) -> bool
  def calculate_completion(['self']) -> None
  def is_ready(['self']) -> bool
  def get_pending_domains(['self']) -> list[QualityDomain]
  def get_failed_domains(['self']) -> list[QualityDomain]
  def __init__(['self', 'zai_api_key', 'domains']) -> ?
  def validate(['self', 'asset_path', 'asset_type']) -> AssetValidationResult
  def _validate_domain(['self', 'asset_path', 'asset_type', 'domain']) -> DomainCheckResult
  def _validate_automated(['self', 'asset_path', 'asset_type', 'domain']) -> DomainCheckResult
  def _validate_vision(['self', 'asset_path', 'asset_type', 'domain']) -> DomainCheckResult
  def _validate_manual(['self', 'asset_path', 'asset_type', 'domain']) -> DomainCheckResult
  def _check_platform_specs(['self', 'asset_path', 'asset_type']) -> DomainCheckResult
  def _check_accessibility(['self', 'asset_path']) -> DomainCheckResult
  def _check_performance(['self', 'asset_path']) -> DomainCheckResult
  def _check_maintainability(['self', 'asset_path', 'asset_type']) -> DomainCheckResult
  def _build_vision_prompt(['self', 'asset_type', 'domain']) -> str
  def _call_vision_api(['self', 'image_data', 'prompt']) -> dict[str, Any] | None
  def _parse_vision_response(['self', 'content']) -> dict[str, Any]
  def _print_domain_result(['self', 'result']) -> None
  def _print_summary(['self', 'result']) -> None
## skills/gitready/resources/create_github_repo_api.py

  def get_github_token([]) -> str
  def create_repo(['name', 'description', 'token', 'private']) -> dict
  def check_repo_exists(['name', 'token', 'owner']) -> dict
  def main([]) -> None
## skills/gitready/resources/phases/test_validate_pointers.py

  class TestValidatePointers:
    def test_valid_pointers_in_skill_md(['self']) -> None
    def test_missing_skill_md(['self']) -> None
    def test_broken_pointer_nonexistent_file(['self']) -> None
    def test_broken_pointer_empty_file(['self']) -> None
    def test_valid_pointer(['self']) -> None
    def test_multiple_pointers_all_valid(['self']) -> None
    def test_multiple_pointers_one_broken(['self']) -> None
  def test_valid_pointers_in_skill_md(['self']) -> None
  def test_missing_skill_md(['self']) -> None
  def test_broken_pointer_nonexistent_file(['self']) -> None
  def test_broken_pointer_empty_file(['self']) -> None
  def test_valid_pointer(['self']) -> None
  def test_multiple_pointers_all_valid(['self']) -> None
  def test_multiple_pointers_one_broken(['self']) -> None
## skills/gitready/resources/phases/track_phases.py

  def find_changelog(['target_dir']) -> Path | None
  def parse_completed_phases(['changelog_path']) -> dict[str, str]
  def append_phase_completion(['changelog_path', 'phase_name', 'phase_desc', 'status']) -> None
  def get_package_type(['target_dir']) -> str | None
  def get_auto_skip_reasons(['target_dir']) -> dict[str, str]
  def print_status_report(['target_dir', 'changelog_path']) -> None
  def main([]) -> None
## skills/gitready/resources/phases/validate_pointers.py

  def sanitize_junction_name(['name']) -> str
  def validate_junction_name(['name']) -> list[str]
  def validate_pointers(['skill_md_path']) -> list[str]
  def main([]) -> int
## skills/gitready/tests/test_validate_pointers.py

  class TestValidatePointers:
    def test_valid_pointers_in_skill_md(['self']) -> None
    def test_missing_skill_md(['self']) -> None
    def test_broken_pointer_nonexistent_file(['self']) -> None
    def test_broken_pointer_empty_file(['self']) -> None
    def test_valid_pointer(['self']) -> None
    def test_multiple_pointers_all_valid(['self']) -> None
    def test_multiple_pointers_one_broken(['self']) -> None
  def test_valid_pointers_in_skill_md(['self']) -> None
  def test_missing_skill_md(['self']) -> None
  def test_broken_pointer_nonexistent_file(['self']) -> None
  def test_broken_pointer_empty_file(['self']) -> None
  def test_valid_pointer(['self']) -> None
  def test_multiple_pointers_all_valid(['self']) -> None
  def test_multiple_pointers_one_broken(['self']) -> None
## tests/__init__.py

  (no Python definitions)
## tests/test_create_github_repo.py

  class TestRunCommand:
    def test_run_command_success(['self', 'mock_run']) -> None
    def test_run_command_failure_raises(['self', 'mock_log', 'mock_run']) -> None
    def test_run_command_check_false(['self', 'mock_run']) -> None
  class TestLogging:
    def test_log_info(['self', 'mock_print']) -> None
    def test_log_success(['self', 'mock_print']) -> None
    def test_log_warning(['self', 'mock_print']) -> None
    def test_log_error(['self', 'mock_print']) -> None
  class TestCheckGhCli:
    def test_check_gh_cli_available_and_authenticated(['self', 'mock_run']) -> None
    def test_check_gh_cli_not_authenticated(['self', 'mock_run']) -> None
    def test_check_gh_cli_not_installed(['self', 'mock_run']) -> None
  class TestGetGithubUsername:
    def test_get_github_username_success(['self', 'mock_run']) -> None
    def test_get_github_username_failure(['self', 'mock_run']) -> None
    def test_get_github_username_exception(['self', 'mock_run']) -> None
  class TestCreateWithGhCli:
    def test_create_with_gh_cli_new_repo(['self', 'mock_succ', 'mock_info', 'mock_run', 'mock_check', 'mock_user', 'tmp_path']) -> None
    def test_create_with_gh_cli_repo_exists(['self', 'mock_succ', 'mock_warn', 'mock_run', 'mock_check', 'mock_user', 'tmp_path']) -> None
    def test_create_with_gh_cli_not_available(['self', 'mock_check', 'tmp_path']) -> None
    def test_create_with_gh_cli_create_fails(['self', 'mock_log', 'mock_run', 'mock_check', 'mock_user', 'tmp_path']) -> None
  class TestShowManualInstructions:
    def test_show_manual_instructions_content(['self', 'mock_log', 'mock_print', 'mock_user', 'tmp_path']) -> None
  class TestVerifyRepository:
    def test_verify_repository_success(['self', 'mock_warn', 'mock_succ', 'mock_info', 'mock_run', 'mock_check', 'mock_user']) -> None
    def test_verify_repository_no_gh(['self', 'mock_warn', 'mock_info', 'mock_check']) -> None
    def test_verify_repository_not_found(['self', 'mock_warn', 'mock_info', 'mock_run', 'mock_check', 'mock_user']) -> None
    def test_verify_repository_private(['self', 'mock_warn', 'mock_succ', 'mock_info', 'mock_run', 'mock_check', 'mock_user']) -> None
  class TestMain:
    def test_main_success(['self', 'mock_exit', 'mock_succ', 'mock_verify', 'mock_create', 'tmp_path']) -> None
    def test_main_gh_cli_fallback(['self', 'mock_exit', 'mock_info', 'mock_manual', 'mock_create', 'tmp_path']) -> None
    def test_main_not_git_repo(['self', 'mock_exit', 'mock_log', 'tmp_path']) -> None
  class TestArgparse:
    def test_positional_args(['self', 'mock_exit', 'mock_succ', 'mock_verify', 'mock_create', 'tmp_path']) -> None
    def test_default_description(['self', 'mock_exit', 'mock_succ', 'mock_verify', 'mock_create', 'tmp_path']) -> None
  def test_run_command_success(['self', 'mock_run']) -> None
  def test_run_command_failure_raises(['self', 'mock_log', 'mock_run']) -> None
  def test_run_command_check_false(['self', 'mock_run']) -> None
  def test_log_info(['self', 'mock_print']) -> None
  def test_log_success(['self', 'mock_print']) -> None
  def test_log_warning(['self', 'mock_print']) -> None
  def test_log_error(['self', 'mock_print']) -> None
  def test_check_gh_cli_available_and_authenticated(['self', 'mock_run']) -> None
  def test_check_gh_cli_not_authenticated(['self', 'mock_run']) -> None
  def test_check_gh_cli_not_installed(['self', 'mock_run']) -> None
  def test_get_github_username_success(['self', 'mock_run']) -> None
  def test_get_github_username_failure(['self', 'mock_run']) -> None
  def test_get_github_username_exception(['self', 'mock_run']) -> None
  def test_create_with_gh_cli_new_repo(['self', 'mock_succ', 'mock_info', 'mock_run', 'mock_check', 'mock_user', 'tmp_path']) -> None
  def test_create_with_gh_cli_repo_exists(['self', 'mock_succ', 'mock_warn', 'mock_run', 'mock_check', 'mock_user', 'tmp_path']) -> None
  def test_create_with_gh_cli_not_available(['self', 'mock_check', 'tmp_path']) -> None
  def test_create_with_gh_cli_create_fails(['self', 'mock_log', 'mock_run', 'mock_check', 'mock_user', 'tmp_path']) -> None
  def test_show_manual_instructions_content(['self', 'mock_log', 'mock_print', 'mock_user', 'tmp_path']) -> None
  def test_verify_repository_success(['self', 'mock_warn', 'mock_succ', 'mock_info', 'mock_run', 'mock_check', 'mock_user']) -> None
  def test_verify_repository_no_gh(['self', 'mock_warn', 'mock_info', 'mock_check']) -> None
  def test_verify_repository_not_found(['self', 'mock_warn', 'mock_info', 'mock_run', 'mock_check', 'mock_user']) -> None
  def test_verify_repository_private(['self', 'mock_warn', 'mock_succ', 'mock_info', 'mock_run', 'mock_check', 'mock_user']) -> None
  def test_main_success(['self', 'mock_exit', 'mock_succ', 'mock_verify', 'mock_create', 'tmp_path']) -> None
  def test_main_gh_cli_fallback(['self', 'mock_exit', 'mock_info', 'mock_manual', 'mock_create', 'tmp_path']) -> None
  def test_main_not_git_repo(['self', 'mock_exit', 'mock_log', 'tmp_path']) -> None
  def test_positional_args(['self', 'mock_exit', 'mock_succ', 'mock_verify', 'mock_create', 'tmp_path']) -> None
  def test_default_description(['self', 'mock_exit', 'mock_succ', 'mock_verify', 'mock_create', 'tmp_path']) -> None
  def run_side_effect(['cmd']) -> ?
  def run_side_effect(['cmd']) -> ?
  def run_side_effect(['cmd']) -> ?
## tests/test_extract_from_monorepo.py

  class TestRunCommand:
    def test_run_command_success(['self', 'mock_run']) -> None
    def test_run_command_with_cwd(['self', 'mock_run']) -> None
    def test_run_command_failure_raises(['self', 'mock_log', 'mock_run']) -> None
    def test_run_command_check_false(['self', 'mock_run']) -> None
  class TestLogging:
    def test_log_info(['self', 'mock_print']) -> None
    def test_log_success(['self', 'mock_print']) -> None
    def test_log_warning(['self', 'mock_print']) -> None
    def test_log_error(['self', 'mock_print']) -> None
  class TestCheckMonorepo:
    def test_check_monorepo_not_git_repo(['self', 'mock_run', 'tmp_path']) -> None
    def test_check_monorepo_p_git_remote(['self', 'mock_run', 'tmp_path']) -> None
    def test_check_monorepo_monorepo_in_remote(['self', 'mock_run', 'tmp_path']) -> None
    def test_check_monorepo_packages_directory(['self', 'mock_run', 'tmp_path']) -> None
    def test_check_monorepo_windows_packages_path(['self', 'mock_run', 'tmp_path']) -> None
    def test_check_monorepo_standalone_repo(['self', 'mock_run', 'tmp_path']) -> None
  class TestGetPackagePath:
    def test_get_package_path_success(['self', 'mock_run', 'tmp_path']) -> None
    def test_get_package_path_git_failure(['self', 'mock_log', 'mock_run', 'tmp_path']) -> None
  class TestExtractFreshInit:
    def test_extract_fresh_init_new_repo(['self', 'mock_warn', 'mock_succ', 'mock_info', 'mock_run', 'tmp_path']) -> None
    def test_extract_fresh_init_backups_existing_git(['self', 'mock_warn', 'mock_run', 'tmp_path', 'tmp_path_factory']) -> None
    def test_extract_fresh_init_empty_repo(['self', 'mock_warn', 'mock_succ', 'mock_info', 'mock_run', 'tmp_path']) -> None
  class TestExtractSubtreeSplit:
    def test_extract_subtree_split_success(['self', 'mock_succ', 'mock_info', 'mock_run', 'mock_pkg_path', 'tmp_path']) -> None
    def test_extract_subtree_split_no_package_path(['self', 'mock_log', 'mock_run', 'mock_pkg_path', 'tmp_path']) -> None
    def test_extract_subtree_split_no_subtree(['self', 'mock_log', 'mock_run', 'mock_pkg_path', 'tmp_path']) -> None
    def test_extract_subtree_split_fails(['self', 'mock_warn', 'mock_log', 'mock_run', 'mock_pkg_path', 'tmp_path']) -> None
  class TestMain:
    def test_main_fresh_init_flag(['self', 'mock_succ', 'mock_info', 'mock_exit', 'mock_extract', 'mock_check', 'tmp_path']) -> None
    def test_main_standalone_no_extraction(['self', 'mock_succ', 'mock_info', 'mock_exit', 'mock_run', 'mock_check', 'tmp_path']) -> None
    def test_main_target_not_exists(['self', 'mock_exit', 'mock_log']) -> None
    def test_main_extraction_failure(['self', 'mock_exit', 'mock_log', 'mock_extract', 'mock_check', 'tmp_path']) -> None
  class TestArgparse:
    def test_positional_args(['self', 'mock_exit', 'mock_extract', 'mock_check', 'tmp_path']) -> None
    def test_fresh_init_default_false(['self', 'mock_warn', 'mock_exit', 'mock_fresh', 'mock_subtree', 'mock_check', 'tmp_path']) -> None
  def test_run_command_success(['self', 'mock_run']) -> None
  def test_run_command_with_cwd(['self', 'mock_run']) -> None
  def test_run_command_failure_raises(['self', 'mock_log', 'mock_run']) -> None
  def test_run_command_check_false(['self', 'mock_run']) -> None
  def test_log_info(['self', 'mock_print']) -> None
  def test_log_success(['self', 'mock_print']) -> None
  def test_log_warning(['self', 'mock_print']) -> None
  def test_log_error(['self', 'mock_print']) -> None
  def test_check_monorepo_not_git_repo(['self', 'mock_run', 'tmp_path']) -> None
  def test_check_monorepo_p_git_remote(['self', 'mock_run', 'tmp_path']) -> None
  def test_check_monorepo_monorepo_in_remote(['self', 'mock_run', 'tmp_path']) -> None
  def test_check_monorepo_packages_directory(['self', 'mock_run', 'tmp_path']) -> None
  def test_check_monorepo_windows_packages_path(['self', 'mock_run', 'tmp_path']) -> None
  def test_check_monorepo_standalone_repo(['self', 'mock_run', 'tmp_path']) -> None
  def test_get_package_path_success(['self', 'mock_run', 'tmp_path']) -> None
  def test_get_package_path_git_failure(['self', 'mock_log', 'mock_run', 'tmp_path']) -> None
  def test_extract_fresh_init_new_repo(['self', 'mock_warn', 'mock_succ', 'mock_info', 'mock_run', 'tmp_path']) -> None
  def test_extract_fresh_init_backups_existing_git(['self', 'mock_warn', 'mock_run', 'tmp_path', 'tmp_path_factory']) -> None
  def test_extract_fresh_init_empty_repo(['self', 'mock_warn', 'mock_succ', 'mock_info', 'mock_run', 'tmp_path']) -> None
  def test_extract_subtree_split_success(['self', 'mock_succ', 'mock_info', 'mock_run', 'mock_pkg_path', 'tmp_path']) -> None
  def test_extract_subtree_split_no_package_path(['self', 'mock_log', 'mock_run', 'mock_pkg_path', 'tmp_path']) -> None
  def test_extract_subtree_split_no_subtree(['self', 'mock_log', 'mock_run', 'mock_pkg_path', 'tmp_path']) -> None
  def test_extract_subtree_split_fails(['self', 'mock_warn', 'mock_log', 'mock_run', 'mock_pkg_path', 'tmp_path']) -> None
  def test_main_fresh_init_flag(['self', 'mock_succ', 'mock_info', 'mock_exit', 'mock_extract', 'mock_check', 'tmp_path']) -> None
  def test_main_standalone_no_extraction(['self', 'mock_succ', 'mock_info', 'mock_exit', 'mock_run', 'mock_check', 'tmp_path']) -> None
  def test_main_target_not_exists(['self', 'mock_exit', 'mock_log']) -> None
  def test_main_extraction_failure(['self', 'mock_exit', 'mock_log', 'mock_extract', 'mock_check', 'tmp_path']) -> None
  def test_positional_args(['self', 'mock_exit', 'mock_extract', 'mock_check', 'tmp_path']) -> None
  def test_fresh_init_default_false(['self', 'mock_warn', 'mock_exit', 'mock_fresh', 'mock_subtree', 'mock_check', 'tmp_path']) -> None
  def run_side_effect(['cmd']) -> ?
  def run_side_effect(['cmd']) -> ?
  def run_side_effect(['cmd']) -> ?
  def run_side_effect(['cmd']) -> ?
  def run_side_effect(['cmd']) -> ?
## tests/test_finalize_github_repo.py

  class TestColors:
    def test_colors_defined(['self']) -> ?
  class TestLoggingFunctions:
    def test_log_info(['self', 'capsys']) -> ?
    def test_log_success(['self', 'capsys']) -> ?
    def test_log_warning(['self', 'capsys']) -> ?
    def test_log_error(['self', 'capsys']) -> ?
  class TestRunCommand:
    def test_run_command_success(['self']) -> ?
    def test_run_command_failure(['self']) -> ?
  class TestCheckGhCli:
    def test_check_gh_cli_available(['self', 'mock_run']) -> ?
    def test_check_gh_cli_not_available(['self', 'mock_run']) -> ?
  class TestGetGithubUsername:
    def test_get_username_success(['self', 'mock_run']) -> ?
    def test_get_username_failure(['self', 'mock_run']) -> ?
  class TestGetPackageTopics:
    def test_plugin_topics(['self']) -> ?
    def test_skill_topics(['self']) -> ?
    def test_mcp_topics(['self']) -> ?
    def test_library_topics(['self']) -> ?
  class TestGenerateCodeowners:
    def test_generate_codeowners_new_file(['self', 'tmp_path']) -> ?
    def test_generate_codeowners_existing_file(['self', 'tmp_path']) -> ?
    def test_generate_codeowners_default_username(['self', 'tmp_path']) -> ?
  class TestGenerateSecurityMd:
    def test_generate_security_md_new_file(['self', 'tmp_path']) -> ?
    def test_generate_security_md_existing_file(['self', 'tmp_path']) -> ?
  class TestEnableGithubPages:
    def test_enable_pages_success(['self', 'mock_run', 'mock_check', 'tmp_path']) -> ?
    def test_enable_pages_no_gh(['self', 'mock_check']) -> ?
  class TestCreateInitialRelease:
    def test_create_release_success(['self', 'mock_run', 'mock_check']) -> ?
    def test_create_release_exists(['self', 'mock_run', 'mock_check', 'tmp_path']) -> ?
  class TestAddRepositoryTopics:
    def test_add_topics_success(['self', 'mock_run', 'mock_check']) -> ?
    def test_add_topics_no_gh(['self', 'mock_check']) -> ?
  class TestVerifyFinalization:
    def test_verify_all_success(['self', 'mock_run', 'mock_check']) -> ?
    def test_verify_no_gh(['self', 'mock_check']) -> ?
  class TestMain:
    def test_main_verify_mode(['self']) -> ?
    def test_main_full_flow(['self', 'mock_check']) -> ?
    def test_main_not_git_repo(['self']) -> ?
  def test_colors_defined(['self']) -> ?
  def test_log_info(['self', 'capsys']) -> ?
  def test_log_success(['self', 'capsys']) -> ?
  def test_log_warning(['self', 'capsys']) -> ?
  def test_log_error(['self', 'capsys']) -> ?
  def test_run_command_success(['self']) -> ?
  def test_run_command_failure(['self']) -> ?
  def test_check_gh_cli_available(['self', 'mock_run']) -> ?
  def test_check_gh_cli_not_available(['self', 'mock_run']) -> ?
  def test_get_username_success(['self', 'mock_run']) -> ?
  def test_get_username_failure(['self', 'mock_run']) -> ?
  def test_plugin_topics(['self']) -> ?
  def test_skill_topics(['self']) -> ?
  def test_mcp_topics(['self']) -> ?
  def test_library_topics(['self']) -> ?
  def test_generate_codeowners_new_file(['self', 'tmp_path']) -> ?
  def test_generate_codeowners_existing_file(['self', 'tmp_path']) -> ?
  def test_generate_codeowners_default_username(['self', 'tmp_path']) -> ?
  def test_generate_security_md_new_file(['self', 'tmp_path']) -> ?
  def test_generate_security_md_existing_file(['self', 'tmp_path']) -> ?
  def test_enable_pages_success(['self', 'mock_run', 'mock_check', 'tmp_path']) -> ?
  def test_enable_pages_no_gh(['self', 'mock_check']) -> ?
  def test_create_release_success(['self', 'mock_run', 'mock_check']) -> ?
  def test_create_release_exists(['self', 'mock_run', 'mock_check', 'tmp_path']) -> ?
  def test_add_topics_success(['self', 'mock_run', 'mock_check']) -> ?
  def test_add_topics_no_gh(['self', 'mock_check']) -> ?
  def test_verify_all_success(['self', 'mock_run', 'mock_check']) -> ?
  def test_verify_no_gh(['self', 'mock_check']) -> ?
  def test_main_verify_mode(['self']) -> ?
  def test_main_full_flow(['self', 'mock_check']) -> ?
  def test_main_not_git_repo(['self']) -> ?
  def side_effect([]) -> ?
  def side_effect([]) -> ?
## tests/test_main.py

  def test_get_version([]) -> ?
  def test_version_format([]) -> ?
## tests/test_mermaid_compat.py

  def _read_text(['path']) -> str
  def test_readme_mermaid_uses_github_compatible_subset([]) -> ?
  def test_diagram_sources_use_github_compatible_subset([]) -> ?
  def test_mermaid_init_directives_use_standard_closing_marker([]) -> ?
## tests/test_scan_package_quality.py

  class TestColors:
    def test_colors_defined(['self']) -> ?
  class TestLoggingFunctions:
    def test_log_info(['self', 'capsys']) -> ?
    def test_log_success(['self', 'capsys']) -> ?
    def test_log_warning(['self', 'capsys']) -> ?
    def test_log_error(['self', 'capsys']) -> ?
  class TestRunCommand:
    def test_run_command_success(['self']) -> ?
    def test_run_command_failure(['self']) -> ?
  class TestCheckToolInstalled:
    def test_check_tool_installed_true(['self', 'mock_run']) -> ?
    def test_check_tool_installed_false(['self', 'mock_run']) -> ?
  class TestRunBanditScan:
    def test_bandit_not_installed(['self', 'mock_check']) -> ?
    def test_bandit_no_issues(['self', 'mock_run', 'mock_check', 'tmp_path']) -> ?
    def test_bandit_with_issues(['self', 'mock_run', 'mock_check']) -> ?
    def test_bandit_no_python_files(['self', 'mock_run', 'mock_check', 'tmp_path']) -> ?
  class TestRunSafetyScan:
    def test_safety_not_installed(['self', 'mock_check']) -> ?
    def test_safety_no_vulnerabilities(['self', 'mock_run', 'mock_check', 'tmp_path']) -> ?
    def test_safety_with_vulnerabilities(['self', 'mock_run', 'mock_check', 'tmp_path']) -> ?
  class TestRunPipAudit:
    def test_pip_audit_not_installed(['self', 'mock_check']) -> ?
    def test_pip_audit_no_vulnerabilities(['self', 'mock_run', 'mock_check']) -> ?
    def test_pip_audit_with_vulnerabilities(['self', 'mock_run', 'mock_check']) -> ?
  class TestValidateBadges:
    def test_validate_badges_with_badges(['self', 'tmp_path']) -> ?
    def test_validate_badges_no_readme(['self', 'tmp_path']) -> ?
    def test_validate_badges_missing_workflow(['self', 'tmp_path']) -> ?
  class TestCheckCodeQualityMetrics:
    def test_quality_metrics_with_files(['self', 'tmp_path']) -> ?
    def test_quality_metrics_no_files(['self', 'tmp_path']) -> ?
  class TestGenerateReport:
    def test_generate_report(['self', 'tmp_path']) -> ?
  class TestSaveReport:
    def test_save_report(['self', 'tmp_path']) -> ?
  class TestMain:
    def test_main_success(['self']) -> ?
    def test_main_with_issues(['self']) -> ?
    def test_main_invalid_directory(['self']) -> ?
  def test_colors_defined(['self']) -> ?
  def test_log_info(['self', 'capsys']) -> ?
  def test_log_success(['self', 'capsys']) -> ?
  def test_log_warning(['self', 'capsys']) -> ?
  def test_log_error(['self', 'capsys']) -> ?
  def test_run_command_success(['self']) -> ?
  def test_run_command_failure(['self']) -> ?
  def test_check_tool_installed_true(['self', 'mock_run']) -> ?
  def test_check_tool_installed_false(['self', 'mock_run']) -> ?
  def test_bandit_not_installed(['self', 'mock_check']) -> ?
  def test_bandit_no_issues(['self', 'mock_run', 'mock_check', 'tmp_path']) -> ?
  def test_bandit_with_issues(['self', 'mock_run', 'mock_check']) -> ?
  def test_bandit_no_python_files(['self', 'mock_run', 'mock_check', 'tmp_path']) -> ?
  def test_safety_not_installed(['self', 'mock_check']) -> ?
  def test_safety_no_vulnerabilities(['self', 'mock_run', 'mock_check', 'tmp_path']) -> ?
  def test_safety_with_vulnerabilities(['self', 'mock_run', 'mock_check', 'tmp_path']) -> ?
  def test_pip_audit_not_installed(['self', 'mock_check']) -> ?
  def test_pip_audit_no_vulnerabilities(['self', 'mock_run', 'mock_check']) -> ?
  def test_pip_audit_with_vulnerabilities(['self', 'mock_run', 'mock_check']) -> ?
  def test_validate_badges_with_badges(['self', 'tmp_path']) -> ?
  def test_validate_badges_no_readme(['self', 'tmp_path']) -> ?
  def test_validate_badges_missing_workflow(['self', 'tmp_path']) -> ?
  def test_quality_metrics_with_files(['self', 'tmp_path']) -> ?
  def test_quality_metrics_no_files(['self', 'tmp_path']) -> ?
  def test_generate_report(['self', 'tmp_path']) -> ?
  def test_save_report(['self', 'tmp_path']) -> ?
  def test_main_success(['self']) -> ?
  def test_main_with_issues(['self']) -> ?
  def test_main_invalid_directory(['self']) -> ?
