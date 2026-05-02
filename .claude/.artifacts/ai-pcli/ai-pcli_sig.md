# ai-pcli - SIGNATURES ONLY

## ai_cli.py
FunctionDef _load_ai_cli_config() -> ?
FunctionDef _save_ai_cli_config(clis,opencode_models) -> ?
FunctionDef _clear_ai_cli_config() -> ?
FunctionDef _substitute_gemini_model(cmd_list,model) -> ?
FunctionDef _get_repo_root() -> Path
FunctionDef _cleanup_old_cli_results(days_to_keep) -> ?
FunctionDef route_query_to_clis(query) -> ?
FunctionDef _apply_quality_gate_filter(results,query,min_confidence) -> ?
FunctionDef _resolve_opencode_model(model) -> str
FunctionDef get_glm_api_key() -> str
FunctionDef mask_api_key(key) -> str
FunctionDef _is_in_workspace(path_str) -> bool
FunctionDef _read_context_file(file_path,allowed_root) -> str
FunctionDef _add_datetime_suffix(file_path) -> str
FunctionDef _copy_to_tmp_if_needed(file_path) -> Path
FunctionDef _format_session_history(session_file,after_timestamp,max_entries) -> str
FunctionDef _find_session_by_marker(marker) -> ?
FunctionDef _get_auto_context() -> str
FunctionDef get_context(context_source,auto_context,cli_name) -> str
FunctionDef detect_session_context(wt_session) -> str
FunctionDef _read_multi_file_context(context_source,cli_name) -> str
FunctionDef generate_parallel_bash_commands(query,qwen_only,gemini_only,codex_only) -> ?
FunctionDef _parse_opencode_streaming_json(output) -> str
FunctionDef _determine_active_llms(qwen_only,gemini_only,codex_only,opencode_only,glm_flash_only,pi_m27_only,pi_glm_only,copilot_only) -> ?
FunctionDef _get_cli_preview(qwen_only,gemini_only,codex_only,opencode_only,glm_flash_only,opencode_models,pi_m27_only,pi_glm_only,copilot_only) -> str
FunctionDef _build_cli_commands(query,run_qwen,run_gemini,run_codex,run_opencode,opencode_models,run_pi_m27,run_pi_glm,run_copilot,context_file) -> ?
FunctionDef _execute_glm_api_mode(query,timeout,verbose) -> ?
FunctionDef _process_llm_results(raw_results) -> ?
FunctionDef run_parallel_llm(query,qwen_only,gemini_only,codex_only,opencode_only,glm_flash_only,pi_m27_only,pi_glm_only,copilot_only,timeout,output_format,verbose,opencode_models,context_file) -> ?
FunctionDef expand_prompt(query) -> str
FunctionDef show_prompt_options(expanded_prompt,original_prompt) -> str
FunctionDef prompt_with_expansion_option(original_query) -> str
FunctionDef _extract_issues_by_priority(outputs) -> ?
FunctionDef _format_progressive_selections(issues) -> str
FunctionDef format_results(results) -> str
FunctionDef _extract_qwen_answer(output) -> str
FunctionDef _extract_gemini_answer(output) -> str
FunctionDef _extract_codex_answer(output) -> str
FunctionDef _extract_answer(cli_name,output) -> str
FunctionDef format_summary(results) -> str
FunctionDef format_aggregate(results) -> str
FunctionDef format_complete(results) -> str
FunctionDef format_diff(results) -> str
FunctionDef format_quality_weighted(results) -> str
FunctionDef _detect_review_query(query) -> bool
FunctionDef _extract_file_paths_from_query(query) -> ?
FunctionDef _get_git_changed_files() -> ?
FunctionDef _smart_auto_context(query) -> ?
FunctionDef _build_query_context(args,query) -> ?
FunctionDef _create_tiered_reports(results) -> ?
FunctionDef _extract_finding_signature(content) -> str
FunctionDef _deduplicate_findings_cli(all_findings) -> ?
FunctionDef _deduplicate_findings(findings,priority_order) -> ?
FunctionDef _extract_all_findings(cli_data,cli_name,min_confidence) -> ?
FunctionDef _extract_text_findings_all(output,cli_name) -> ?
FunctionDef _extract_from_full_output(cli_name,output) -> ?
FunctionDef _write_output(results,args) -> ?
AsyncFunctionDef _run_domain_query(domain,query,context,refresh_benchmarks) -> ?
FunctionDef main() -> ?
AsyncFunctionDef run_all_parallel() -> ?
FunctionDef extract_recursive(obj,path) -> ?
AsyncFunctionDef run_model_with_native_cli_or_opencode(model_info) -> ?

## file_context.py
FunctionDef resolve_path(path_str) -> Path
FunctionDef collect_files_from_paths(paths,extensions,max_files) -> ?
FunctionDef _iter_files_recursive(directory,extensions) -> ?
FunctionDef read_file_content_safe(file_path,max_size) -> ?
FunctionDef create_repo_map(files) -> str
FunctionDef format_files_for_llm(files,use_repo_map) -> str
FunctionDef build_context_from_paths(paths,extensions,use_repo_map) -> ?
FunctionDef print_context_summary(metadata) -> ?

## performance_logger.py
(parse error)

## prompt_templates.py
FunctionDef build_prompt(query,task_type,context) -> str
FunctionDef _test_prompt_building() -> ?

## scripts\__init__.py

## scripts\analyze_security.py
FunctionDef analyze_file(file_path,output_file) -> str
FunctionDef main() -> ?

## scripts\cli.py
FunctionDef cmd_health(args) -> int
FunctionDef cmd_models(args) -> int
FunctionDef cmd_list(args) -> int
FunctionDef build_parser() -> ?
FunctionDef main() -> int

## scripts\cli_detector.py
FunctionDef _get_npm_root() -> Path
FunctionDef _get_npm_cli_path(cli_info) -> ?
FunctionDef _build_cli_command(cli_id,cli_info) -> ?
FunctionDef _run_cli_command(cli_id,command_parts,timeout) -> ?
FunctionDef _extract_version(output) -> ?
FunctionDef check_cli_installation(cli_id) -> ?
FunctionDef check_env_vars() -> ?
FunctionDef get_all_cli_status() -> ?
FunctionDef format_cli_status_table(status) -> str
FunctionDef format_env_var_status(env_status) -> str

## scripts\filter_models.py
FunctionDef get_cached_models() -> ?
FunctionDef save_to_cache(data) -> ?
FunctionDef fetch_models(force_refresh) -> str
FunctionDef main() -> ?

## scripts\parallel_llm.py
FunctionDef sanitize_error(error_msg) -> str
FunctionDef _save_cli_output(command,stdout_text,stderr_text) -> ?
AsyncFunctionDef _retry_request(coro_factory,max_retries,base_delay,verbose) -> ?
AsyncFunctionDef run_single_command(command,input_text,timeout,verbose,cwd) -> ?
FunctionDef _is_quota_error(error) -> bool
FunctionDef _check_gemini_quota_file() -> bool
AsyncFunctionDef run_parallel_commands(commands,timeout,input_text,verbose,fallback_commands,cwd) -> ?
AsyncFunctionDef run_glm_api(model,query,api_key,session,timeout,verbose) -> ?
AsyncFunctionDef run_parallel_glm(queries,api_key,timeout,verbose) -> ?
FunctionDef calc_timeout(context_size_kb) -> int
AsyncFunctionDef run_with_fallback(name,cmd_args,cmd_input,fallback_chain) -> ?
AsyncFunctionDef fetch_and_name(name,coro) -> ?
AsyncFunctionDef api_call_with_retry() -> ?

## structured_response.py
(parse error)

## task_classifier.py
(parse error)

## tests\test_ai_cli_critic_prompt.py
FunctionDef test_ai_cli_critic_prompt_contains_strict_guardrails() -> ?

## tests\test_opencode_model_aliases.py
(parse error)

## references\cli-reference.md
# CLI Reference

## CLI Characteristics

| CLI | Speed | Best For |
|-----|-------|----------|
| qwen | Fastest (~63s) | Code gen, debugging |
| gemini | Medium (~160s) | Concise answers |
| codex | Fast | Code reviews |
| opencode | Fast | Alternative perspectives |
| glm-4.7-flash | Fast (~60s API) | Additional perspective (requires ZAI_API_KEY) |

## OpenCode Zen Models

OpenCode Zen provides access to specialized models via model aliases:

| Alias | Model | Use Case |
|-------|-------|----------|
| `kimi` | Kimi K2.5 TEE | Long context (256K), multimodal, agent swarm, large codebase analysis |
| `minimax` | MiniMax M2.1 TEE | SOTA coding (74% SWE-bench), code generation, debugging, optimization |

**Usage:**
```bash
# Use alias instead of full model ID
/ai-cli "analyze this large codebase" --opencode-model kimi

# Full model ID also works
/ai-cli "review this code" --opencode-model "chutes/MiniMaxAI/MiniMax-M2.1-TEE"

# Note: Model IDs use exact case from chutes provider:
# - kimi: chutes/moonshotai/Kimi-K2.5-TEE (lowercase moonshotai)
# - minimax: chutes/MiniMaxAI/MiniMax-M2.1-TEE (uppercase MiniMaxAI)
```

**Model Details:**
- **Kimi K2.5**: 256K context, native multimodal, tool calling, free open-weight
- **MiniMax M2.1**: 74% SWE-bench Verified, multilingual coding, agentic workflows

## Setup

**External CLIs** (install separately):
```bash
npm install -g qwen-code gemini-cli @openai/codex opencode-ai
```

**Environment Variables:**
- `CHUTES_API_KEY` - Required for opencode
- `ZAI_API_KEY` - Optional, enables glm-4.7-flash in default execution

## Health Check CLI

```bash
# Check CLI tool availability
python "P:\.claude\skills\ai-cli\scripts\cli.py" list

# Check with sanity test (runs actual CLI commands)
python "P:\.claude\skills\ai-cli\scripts\cli.py" health --sanity

# Check specific CLI
python "P:\.claude\skills\ai-cli\scripts\cli.py" health --cli qwen
```

**Health checks:**
- Environment variables (CHUTES_API_KEY, ZAI_API_KEY)
- CLI installations (qwen-code, gemini-cli, codex-cli, opencode-ai)
- Optional sanity test (runs actual CLI with --version flag)

**Exit codes:** `0` = healthy, `1` = failed

## Known Limitations

**OpenCode Very Large Models (MiroThinker 235B, Nemotron Nano 30B):**

These models may return `[No output]` when invoked through `/ai-cli` due to:
- Extremely slow response times (5+ minutes for simple queries)
- Output streaming behavior that doesn't interact well with Python async subprocess PIPE on Windows

**Workaround:** Invoke these models directly via the opencode CLI:
```bash
opencode run -m "chutes/miromind-ai/MiroThinker-v1.5-235B" "your query here"
```

**Affected models:**
- `miro` (MiroThinker v1.5 235B)
- `nano` (NVIDIA Nemotron 3 Nano 30B)

**Unaffected models:** kimi, minimax, and all other CLIs work correctly through `/ai-cli`.

---

## Workflow Patterns

These patterns encode multi-agent orchestration techniques drawn from adversarial debate and autonomous loop research.

### Pattern 1: Adversarial Debate

Run multiple CLIs in parallel to surface disagreement between models — useful when you need to identify which approach has flaws.

```bash
/ai-cli "should I refactor X or replace it?" --aggregate --diff
```

**How it works:** `--aggregate` pools all CLI outputs; `--diff` highlights where CLIs disagree. Disagreement flags a decision point, not a bug.

**Use when:** Unclear which approach is correct, multiple reasonable options exist, or you want to catch subtle flaws before committing.

**Example:** "architectural decision: event-driven vs polling" → CLAs disagree → you investigate the disagreement.

### Pattern 2: Ralph-Loop (Autonomous Refinement)

Iterative CLI calls that feed output back as next input, bounded by timeout. Terminates when CLIs converge or timeout fires.

```bash
/ai-cli "fix the bug" --timeout 60
# Output becomes context for next call
/ai-cli "now apply that pattern to the other files" --timeout 60
```

**How it works:** Each iteration refines the output. Use `--summary` for faster iterations, `--complete` when you need full detail.

**Use when:** Large refactor across many files, architectural migration, or iterative improvement where each step builds on the last.

**Integration:** For stateful autonomous loops (Ralph pattern), see `/ralph` skill — it handles exit detection, state management, and loop bounding.

### Pattern 3: TDD Cycle (Red-Green-Refactor)

Use quality-gated output as a red-phase signal, then validate with a fresh prompt.

```bash
# Red: Get test failures via quality gate
/ai-cli "what tests will fail if I rename this function?" --quality-gate --summary

# Green: Apply the change, then verify
/ai-cli "I made the change. Which tests now pass?" --aggregate

# Refactor: If both pass, proceed
/ai-cli "the tests pass. Suggest cleanups that don't change behavior."
```

**How it works:** `--quality-gate` filters to high-confidence findings (confidence >= 80%). This reduces noise in the red phase.

**Use when:** Risky refactors, API changes, or any situation where you want test coverage before committing to a change.

---

## Cross-Skill References

| Pattern | Supporting Skill |
|---------|----------------|
| Autonomous loop state management | `/ralph` |
| Adversarial debate (multi-agent) | `/ai-cli --aggregate --diff` |
| TDD cycle (test-first) | `/ai-cli --quality-gate` |
| Codex single-task forwarder | `codex:codex-rescue` |
| Multi-provider API orchestration | `/ai-api` |


## SKILL.md
---
name: ai-pcli
version: "1.4.0"
status: stable
description: Parallel Multi-LLM Command with prompting-toolkit enhancement - Run qwen, gemini, codex, and opencode CLI tools in parallel
category: ai-llm
enforcement: strict
triggers:
  - /ai-pcli
workflow_steps:
  - Parse query and options
  - Build context from --context or auto-detection
  - Apply prompt enhancement (built-in or --prompt-toolkit)
  - Run parallel LLM CLIs
  - Aggregate outputs
  - Run ai-cli-critic unless --no-critic
---

# /ai-pcli

**Parallel multi-LLM command with prompting-toolkit:** `/ai-pcli` runs multiple CLI-backed model providers and aggregates their output.

## EXECUTION DIRECTIVE

**When invoked, check query type first:**

- If query is `"config"` (case-insensitive): Skip to Step 6
- Otherwise: Continue with Steps 1-4

**Step 1:** Run the CLI:
```bash
python "P:\packages\cc-skills-ai-cli\skills\ai-pcli\ai_cli.py" "{{user_query}}" {{options}}
```

**Step 2:** Wait for ALL model outputs to complete

**Step 3:** Report the aggregated CLI outputs verbatim

**Step 4:** Run `ai-cli-critic` on the combined output unless `--no-critic` is set

```text
Task(subagent_type="ai-cli-critic",
     description="Critic pass for /ai-cli outputs. Review the combined LLM outputs for unsupported claims, contradictions, overconfidence, and missing evidence. Use the saved JSON file if available, otherwise analyze the raw transcript.")
```

**Step 5:** If `--output-format json` is used, save the combined JSON to a datetime-suffixed output file and generate tiered YAML reports

**Step 6 (config query):** Read `P:/.claude/ai-cli-recipe.json` and display:
```
Active CLIs:
  Default:
    <cli1>
    <cli2>
    ...
  Aux / Enh:
    <cli> (<model>, failover to <failover>)
    ...
```
If no config file exists, display: `No saved configuration found`

**DO NOT:**
- Provide your own analysis instead of running the command
- Summarize this skill documentation
- Substitute your capabilities for the external LLM CLIs
- Consider the task complete until bash command output is captured
- Read files and analyze them yourself when user wants multi-LLM perspective

**DEFAULT (no arguments):**
```bash
python "P:\packages\cc-skills-ai-cli\skills\ai-pcli\ai_cli.py" --help
```

**If execution fails:** Report exact error message. Do NOT fabricate results or provide your own analysis as substitute.

---

## Quick Reference

| Option | Description |
|--------|-------------|
| `"<query>"` | Question or task (required, quoted) |
| `--context FILE` | File path to embed (RECOMMENDED for file analysis) |
| `--target FILE` | Target file to investigate (filters session context by relevance) |
| `--summary` | Brief key answers only |
| `--aggregate` | Consensus view showing agreement/disagreement |
| `--quality-weighted` | Quality-weighted output with consensus analysis and evidence validation |
| `--complete` | Full raw outputs |
| `--diff` | Show differences between CLI responses |
| `--quality-gate` | Apply 4-Layer Filter System Layer 4 (filters findings by confidence >= 80%) |
| `--output-format json` | Machine-readable JSON output |
| `--timeout N` | Max wait in seconds (default: auto-calculated) |
| `--output-file FILE` | Save JSON output to a datetime-suffixed file |
| `--no-critic` | Skip the post-run ai-cli critic subagent |
| `--prompt-toolkit` | Use prompting-toolkit AutomaticEnhancementSystem instead of built-in templates |
| `--qwen-only` | Run only qwen-cli |
| `--gemini-only` | Run only gemini-cli |
| `--codex-only` | Run only codex-cli |
| `--opencode-only` | Run only opencode (DeepSeek V3) |
| `--opencode-model MODEL` | OpenCode model or alias (kimi, minimax) |
| `--route` | Use rule-based routing (from llm-route) to select CLI by task keywords |
| `--doc-review` | Use document review prompt (from llm-doc_review) - prepends review questions |
| `--hide-prompt` | Suppress the enhanced prompt display (which is shown by default) |
| `-bash` | Show bash commands instead of executing (debug) |

---

## Critical Rules

1. **File context MUST use --context flag** - Piped stdin is ignored when auto-context detected
2. **Timeout protection:** Default auto-calculated (180s base + 1s per MB context)
3. **Individual failures don't abort others** - Report which CLIs succeeded/failed
4. **Empty responses are flagged as errors** - Don't silently accept blank output

---

## Output Display

For clean output format when using "config" query, see [references/output-template.md](references/output-template.md).

## References

| Topic | File |
|-------|------|
| Example invocations (basic, output modes, specific LLMs, advanced) | `references/examples.md` |
| 4-Layer Filter System / Quality Gate integration | `references/quality-gate.md` |
| Context handling best practices and auto-detection | `references/context-handling.md` |
| CLI characteristics, OpenCode models, setup, health check, limitations | `references/cli-reference.md` |
| Troubleshooting (errors, causes, fixes) | `references/troubleshooting.md` |
| Critic subagent for output sanity checks | `P:/.claude/agents/ai-cli-critic.md` |


## .aid\ai-pcli\ai-pcli_full.md
# ai-pcli — LLM-READY PACK

<!-- Generated by gitpack.py (pure Python) -->

## PACK INFO
- **Files:** 13 files
- **Mode:** signatures + full appendix
- **Generated:** 2026-04-27 18:13 UTC

## HOW TO USE THIS PACK

1. **SIGNATURE TOC** — scan all file signatures to find relevant code
2. **FILE INDEX** — jump to specific files by name
3. **APPENDIX: FULL IMPLEMENTATIONS** — read full implementation on demand

For token efficiency: start with the SIGNATURE TOC, pull full code from
the APPENDIX only when you need the implementation details.

## SIGNATURE TOC

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\ai_cli.py
```python
_load_ai_cli_config() -> dict[str, Any] | None
_save_ai_cli_config(clis: list[str], opencode_models: list[str]) -> None
_clear_ai_cli_config() -> None
_substitute_gemini_model(cmd_list: list[str], model: str) -> list[str]
_get_repo_root() -> Path
_cleanup_old_cli_results(days_to_keep: int) -> None
route_query_to_clis(query: str) -> list[str]
_apply_quality_gate_filter(results: dict[Any], query: str, min_confidence: int)
_resolve_opencode_model(model: str | None) -> str
get_glm_api_key() -> str
mask_api_key(key: str) -> str
_is_in_workspace(path_str: str) -> bool
_read_context_file(file_path: str, allowed_root: Path | None) -> str
_add_datetime_suffix(file_path: str) -> str
_copy_to_tmp_if_needed(file_path: Path) -> Path
_format_session_history(session_file: Path, after_timestamp: float | None, max_entries: int)
_find_session_by_marker(marker: str) -> str | None
_get_auto_context() -> str
get_context(context_source: str | None, auto_context: bool, cli_name: str | None)
detect_session_context(wt_session: str | None) -> str
_read_multi_file_context(context_source: str, cli_name: str | None) -> str
generate_parallel_bash_commands(query: str, qwen_only: bool, gemini_only: bool, codex_only: bool)
_parse_opencode_streaming_json(output: str) -> str
_determine_active_llms(qwen_only: bool, gemini_only: bool, codex_only: bool, opencode_only: bool, glm_flash_only: bool, pi_m27_only: bool, pi_glm_only: bool, copilot_only: bool)
_get_cli_preview(qwen_only: bool, gemini_only: bool, codex_only: bool, opencode_only: bool, glm_flash_only: bool, opencode_models: list[str], pi_m27_only: bool, pi_glm_only: bool, copilot_only: bool)
_build_cli_commands(query: str, run_qwen: bool, run_gemini: bool, run_codex: bool, run_opencode: bool, opencode_models: list[str], run_pi_m27: bool, run_pi_glm: bool, run_copilot: bool, context_file: str | None)
_execute_glm_api_mode(query: str, timeout: int, verbose: bool)
_process_llm_results(raw_results: dict[Any])
run_parallel_llm(query: str, qwen_only: bool, gemini_only: bool, codex_only: bool, opencode_only: bool, glm_flash_only: bool, pi_m27_only: bool, pi_glm_only: bool, copilot_only: bool, timeout: int, output_format: str, verbose: bool, opencode_models: list[str], context_file: str | None)
async run_all_parallel()
expand_prompt(query: str) -> str
show_prompt_options(expanded_prompt: str, original_prompt: str) -> str
prompt_with_expansion_option(original_query: str) -> str
_extract_issues_by_priority(outputs: list[str]) -> dict[str, list[str]]
_format_progressive_selections(issues: dict[Any]) -> str
format_results(results: dict[Any]) -> str
_extract_qwen_answer(output: str) -> str
_extract_gemini_answer(output: str) -> str
_extract_codex_answer(output: str) -> str
_extract_answer(cli_name: str, output: str) -> str
format_summary(results: dict[Any]) -> str
format_aggregate(results: dict[Any]) -> str
format_complete(results: dict[Any]) -> str
format_diff(results: dict[Any]) -> str
format_quality_weighted(results: dict[Any]) -> str
_detect_review_query(query: str) -> bool
_extract_file_paths_from_query(query: str) -> list[str]
_get_git_changed_files() -> list[str]
_smart_auto_context(query: str) -> str | None
_build_query_context(args: argparse.Namespace, query: str) -> tuple[str, str]
_create_tiered_reports(results: dict[Any]) -> None
_extract_finding_signature(content: str) -> str
_deduplicate_findings_cli(all_findings: list[dict]) -> tuple[list[dict], dict]
_deduplicate_findings(findings: list[dict], priority_order: dict[Any]) -> list[dict]
_extract_all_findings(cli_data: Any, cli_name: str, min_confidence: int) -> list[dict]
extract_recursive(obj: Any, path: str) -> None
_extract_text_findings_all(output: str, cli_name: str) -> list[dict]
_extract_from_full_output(cli_name: str, output: str) -> list[dict]
_write_output(results: dict[Any], args: argparse.Namespace) -> None
async _run_domain_query(domain: str, query: str, context: str | None, refresh_benchmarks: bool)
async run_model_with_native_cli_or_opencode(model_info: ModelInfo) -> dict[str, Any]
main()
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\file_context.py
```python
resolve_path(path_str: str) -> Path
collect_files_from_paths(paths: list[str], extensions: list[str] | None, max_files: int)
_iter_files_recursive(directory: Path, extensions: list[str] | None)
read_file_content_safe(file_path: Path, max_size: int)
create_repo_map(files: list[Path]) -> str
format_files_for_llm(files: list[Path], use_repo_map: bool)
build_context_from_paths(paths: list[str], extensions: list[str] | None, use_repo_map: bool)
print_context_summary(metadata: dict[Any]) -> None
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\performance_logger.py
```python
class CliExecutionRecord
to_jsonl(self) -> str
class CliPerformanceLogger
__init__(self, log_path: str | None)
log_execution(self, cli_name: str, task_type: TaskType, query: str, duration_seconds: float, outcome: Literal[Any], output_length: int, error_message: str | None)
get_all_records(self) -> list[CliExecutionRecord]
get_records_for_task(self, task_type: TaskType) -> list[CliExecutionRecord]
get_records_for_cli(self, cli_name: str) -> list[CliExecutionRecord]
get_performance_stats(self, task_type: TaskType | None) -> dict
_test_performance_logger()
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\prompt_templates.py
```python
build_prompt(query: str, task_type: TaskType, context: str | None)
_test_prompt_building()
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\__init__.py
```python
# (no public definitions)
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\analyze_security.py
```python
analyze_file(file_path: str, output_file: str) -> str
main()
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\cli.py
```python
cmd_health(args: argparse.Namespace) -> int
cmd_models(args: argparse.Namespace) -> int
cmd_list(args: argparse.Namespace) -> int
build_parser() -> argparse.ArgumentParser
main() -> int
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\cli_detector.py
```python
_get_npm_root() -> Path
_get_npm_cli_path(cli_info: dict[Any]) -> Path | None
_build_cli_command(cli_id: str, cli_info: dict[Any]) -> list[str]
_run_cli_command(cli_id: str, command_parts: list[str], timeout: int) -> dict[str, Any]
_extract_version(output: str) -> str | None
check_cli_installation(cli_id: str) -> dict[str, Any]
check_env_vars() -> dict[str, dict[str, Any]]
get_all_cli_status() -> dict[str, dict[str, Any]]
format_cli_status_table(status: dict[Any]) -> str
format_env_var_status(env_status: dict[Any]) -> str
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\filter_models.py
```python
get_cached_models() -> str | None
save_to_cache(data: str) -> None
fetch_models(force_refresh: bool) -> str
main()
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\structured_response.py
```python
class TokenUsage
to_dict(self) -> dict[str, int]
class SourceMetadata
class Finding
to_dict(self) -> dict[str, Any]
class CliResponse
to_dict(self) -> dict[str, Any]
class QualityGateResult
to_dict(self) -> dict[str, Any]
class AggregatedResponse
to_dict(self) -> dict[str, Any]
to_json(self, indent: int) -> str
extract_token_usage(output: str) -> TokenUsage
extract_model_id(output: str, cli_name: str) -> str | None
extract_findings_from_text(output: str, cli_name: str, model_id: str | None)
extract_findings_from_json(json_output: str | dict, cli_name: str, model_id: str | None)
build_structured_response(cli_name: str, output: str, error: str | None, response_time_ms: int, success: bool)
calculate_agreement_level(responses: list[CliResponse]) -> float
format_structured_output(responses: dict[Any], query: str, context_files: list[str], total_time_ms: int)
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\task_classifier.py
```python
class TaskType
class ClassificationResult
classify_task(query: str) -> ClassificationResult
_test_classification()
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\tests\test_ai_cli_critic_prompt.py
```python
test_ai_cli_critic_prompt_contains_strict_guardrails()
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\tests\test_opencode_model_aliases.py
```python
class TestOpenCodeModelAliases
test_kimi_alias_resolves(self)
test_minimax_alias_resolves(self)
test_full_model_id_passthrough(self)
test_none_returns_default(self)
test_empty_string_returns_default(self)
test_unknown_alias_returns_as_is(self)
```

## DIRECTORY INDEX

| Directory | Files |
|---------|-------|
| `ai-pcli/` | 6 |
| `scripts/` | 5 |
| `tests/` | 2 |

## FILE INDEX

| File | Description |
|------|-------------|
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\ai_cli.py` | ai cli |
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\file_context.py` | file context |
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\performance_logger.py` | performance logger |
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\prompt_templates.py` | prompt templates |
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\__init__.py` | Package: scripts |
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\analyze_security.py` | analyze security |
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\cli.py` | cli |
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\cli_detector.py` | cli detector |
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\filter_models.py` | filter models |
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\structured_response.py` | structured response |
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\task_classifier.py` | task classifier |
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\tests\test_ai_cli_critic_prompt.py` | test ai cli critic prompt |
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\tests\test_opencode_model_aliases.py` | test opencode model aliases |

---

## APPENDIX: FULL IMPLEMENTATIONS

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\ai_cli.py
```python
#!/usr/bin/env python3
"""
LLM CLI - Parallel Multi-LLM Command Invocation with Context Support

Run qwen, gemini, codex, and opencode CLIs in parallel, aggregate results.
Supports injecting context from chat history or files.
"""

from __future__ import annotations

# Standard library imports
import argparse
import asyncio
import concurrent.futures
import json
import os
import shlex
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Third-party imports
import yaml
from dotenv import load_dotenv

# Local imports
from file_context import (
    build_context_from_paths,
    print_context_summary,
)

# Module-level singleton for prompting-toolkit (preserves cache across calls)
_PROMPT_TOOLKIT_SYSTEM: "AutomaticEnhancementSystem | None" = None

# Config file for remembering last used CLI recipe
_AI_CLI_CONFIG = Path("P:/.claude/ai-pcli-recipe.json")


def _load_ai_cli_config() -> dict[str, Any] | None:
    """Load saved AI-CLI recipe config if it exists."""
    try:
        if _AI_CLI_CONFIG.exists():
            with open(_AI_CLI_CONFIG, encoding="utf-8") as f:
                raw = json.load(f)

            # New format: structured groups for config display.
            if isinstance(raw, dict) and ("default" in raw or "aux" in raw):
                return raw

            # Legacy format: flatten into the structure expected by the
            # config display branch so old recipe files still render.
            if isinstance(raw, dict):
                default_clis = []
                for cli in raw.get("clis", []):
                    if isinstance(cli, str) and cli and not cli.startswith("opencode:"):
                        default_clis.append({"name": cli})

                aux_clis = []
                for model in raw.get("opencode_models", []):
                    if isinstance(model, str) and model:
                        aux_clis.append(
                            {"name": "opencode", "model": _resolve_opencode_model(model)}
                        )

                return {
                    "default": {"clis": default_clis},
                    "aux": {"clis": aux_clis},
                    "clis": raw.get("clis", []),
                    "opencode_models": raw.get("opencode_models", []),
                }
    except Exception:
        pass
    return None


def _save_ai_cli_config(clis: list[str], opencode_models: list[str]) -> None:
    """Save AI-CLI recipe config."""
    try:
        default_clis = []
        for cli in clis:
            if isinstance(cli, str) and cli and not cli.startswith("opencode:"):
                default_clis.append({"name": cli})

        resolved_opencode_models = []
        for model in opencode_models:
            if not isinstance(model, str) or not model:
                continue
            resolved = _resolve_opencode_model(model)
            if resolved not in resolved_opencode_models:
                resolved_opencode_models.append(resolved)

        aux_clis = [{"name": "opencode", "model": model} for model in resolved_opencode_models]

        payload = {
            "default": {"clis": default_clis},
            "aux": {"clis": aux_clis},
            "clis": clis,
            "opencode_models": resolved_opencode_models,
        }

        with open(_AI_CLI_CONFIG, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception:
        pass


def _clear_ai_cli_config() -> None:
    """Clear saved AI-CLI recipe config."""
    try:
        if _AI_CLI_CONFIG.exists():
            _AI_CLI_CONFIG.unlink()
    except Exception:
        pass


def _substitute_gemini_model(cmd_list: list[str], model: str) -> list[str]:
    """Substitute the -m model flag in a gemini command list.

    Args:
        cmd_list: gemini command as list, e.g. ["node", "path/gemini.js", "-y", "-o", "text", "-p", "query"]
        model: new model name, e.g. "gemini-3.1-pro-preview"

    Returns:
        New list with the -m argument replaced.
    """
    result = list(cmd_list)
    for i, arg in enumerate(result):
        if arg == "-m" and i + 1 < len(result):
            result[i + 1] = model
            return result
    return result  # -m not found, return unchanged


# Add lib to path for parallel_llm import (COMP-RECHECK-002 fix: dynamic path)
# NOTE: This must be BEFORE parallel_llm import since it modifies sys.path
def _get_repo_root() -> Path:
    """Find git repository root by searching upward from current directory."""
    current = Path.cwd().resolve()
    if (current / ".git").exists():
        return current
    while True:
        parent = current.parent
        if parent == current:
            if (current / ".git").exists():
                return current
            return current
        if (parent / ".git").exists():
            return parent
        current = parent


_lib_path = Path("P:/__csf/lib")
if str(_lib_path) not in sys.path:
    sys.path.insert(0, str(_lib_path))

# Local imports (after sys.path modification for parallel_llm)
from parallel_llm import (  # noqa: E402
    calc_timeout,
    run_parallel_commands,
    run_parallel_glm,
)

# Import task classification, prompt engineering, and performance tracking modules
# Handle both module execution (relative imports) and standalone script execution (direct imports)
try:
    from .performance_logger import CliPerformanceLogger
    from .prompt_templates import build_prompt
    from .task_classifier import classify_task, TaskType
except ImportError:
    # Running as standalone script - use direct imports
    from performance_logger import CliPerformanceLogger
    from prompt_templates import build_prompt
    from task_classifier import classify_task, TaskType

# Load .env file from repo root (P:\)
_repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
load_dotenv(dotenv_path=os.path.join(_repo_root, ".env"))

# Add CSF src to path for dynamic model router
_CSF_SRC = Path(__file__).parent.parent.parent.parent / "__csf" / "src"
if _CSF_SRC.exists():
    sys.path.insert(0, str(_CSF_SRC))

# Import dynamic model router for domain-based routing
_DYNAMIC_ROUTER_AVAILABLE = False
try:
    from src.core.config.api_keys import APIKeyManager
    from src.csf.llm_providers.dynamic_model_router import Domain, get_router

    _DYNAMIC_ROUTER_AVAILABLE = True
except ImportError:
    pass

# Performance logger for CLI metrics
_PERFORMANCE_LOGGER = CliPerformanceLogger()


def _cleanup_old_cli_results(days_to_keep: int = 7) -> None:
    """Delete CLI result files older than specified days.

    Args:
        days_to_keep: Number of days to retain (default: 7)
    """
    try:
        repo_root = Path("P:/")
        temp_dir = repo_root / "__csf" / "temp" / "cli_results"

        if not temp_dir.exists():
            return

        cutoff_time = datetime.now().timestamp() - (days_to_keep * 86400)
        deleted_count = 0

        for json_file in temp_dir.glob("*.json"):
            if json_file.stat().st_mtime < cutoff_time:
                json_file.unlink()
                deleted_count += 1

        if deleted_count > 0:
            print(
                f"[Cleanup] Deleted {deleted_count} old CLI result files (older than {days_to_keep} days)",
                file=sys.stderr,
            )
    except Exception as e:
        print(f"[Cleanup] Warning: Could not clean old results: {e}", file=sys.stderr)


# ============================================================================
# Rule-Based Routing (from llm-route)
# ============================================================================

# Routing rules for selecting appropriate CLIs based on task keywords
ROUTING_RULES = {
    "codex": {
        "keywords": ["api", "function", "code", "implement", "refactor"],
        "description": "OpenRouter DeepSeek R1T2 Chimera (coding)",
        "flag": "--codex-only",
    },
    "qwen": {
        "keywords": ["analyze", "compare", "evaluate"],
        "description": "Chutes Qwen3 235B (analysis)",
        "flag": "--qwen-only",
    },
    "gemini": {
        "keywords": ["whole codebase", "entire project", "all files", "large context"],
        "description": "Google Gemini CLI (1M+ tokens)",
        "flag": "--gemini-only",
    },
    "opencode": {
        "keywords": ["plan", "strategy", "roadmap", "architecture", "creative", "write", "story"],
        "description": "OpenCode (planning/creative)",
        "flag": "--opencode-only",
    },
}


def route_query_to_clis(query: str) -> list[str]:
    """Route query to appropriate CLIs using rule-based keyword matching.

    This implements the llm-route logic: detect task type from keywords
    and return the CLI flags that should be used.

    Args:
        query: User query text

    Returns:
        List of CLI flags (e.g., ["--codex-only"] or empty for default all-CLIs mode)
    """
    query_lower = query.lower()

    # Find matching routing rules
    matched_clis = []
    for cli_name, rule in ROUTING_RULES.items():
        if any(keyword in query_lower for keyword in rule["keywords"]):
            matched_clis.append(cli_name)
            print(f"[Route] Rule '{rule['description']}' → {cli_name}", file=sys.stderr)

    if not matched_clis:
        print("[Route] No routing rules matched, using all CLIs", file=sys.stderr)
        return []

    # Return flags for matched CLIs
    # If multiple rules match, prefer the first one
    selected_cli = matched_clis[0]
    return [ROUTING_RULES[selected_cli]["flag"]]


# Quality Gate subagent integration (4-Layer Filter System, Layer 4)
_QUALITY_GATE_ENABLED = os.getenv("ASK_OLYMP_QUALITY_GATE", "false").lower() == "true"


def _apply_quality_gate_filter(
    results: dict[str, Any], query: str, min_confidence: int = 80
) -> tuple[dict[str, Any], dict]:
    """Apply 4-Layer Filter System Layer 4 (Quality Gate) to LLM findings.

    Filters LLM outputs by confidence ≥80%, removing false positives.

    4-Layer Filter System from /v:
    - Layer 1: Change Delta Gate (filters to changed files)
    - Layer 2: Architectural Pillar Enforcer (filters against pillars)
    - Layer 3: Aggregation (deduplicates findings)
    - Layer 4: Quality Gate (filters by confidence ≥80%) <- THIS FUNCTION

    Args:
        results: LLM results dict from run_parallel_llm
        query: Original query string for context
        min_confidence: Minimum confidence threshold (default: 80%)

    Returns:
        Tuple of (filtered_results, summary_dict)
        summary_dict contains {"input": N, "output": M, "rejection_reasons": [...]}
    """
    all_findings = []
    min_confidence_filter = min_confidence

    # Extract findings from all LLM outputs
    for cli_name, cli_data in results.items():
        if not isinstance(cli_data, dict):
            continue

        output = cli_data.get("output", "")
        if not output:
            continue

        try:
            cli_json = json.loads(output) if isinstance(output, str) else output
            findings = _extract_all_findings(cli_json, cli_name, min_confidence_filter)
            all_findings.extend(findings)
        except (json.JSONDecodeError, TypeError):
            findings = _extract_text_findings_all(output, cli_name)
            all_findings.extend(findings)

    if not all_findings:
        return results, {"input": 0, "output": 0, "rejection_reasons": ["No findings extracted"]}

    # Deduplicate findings across CLIs before confidence filter
    all_findings, dedup_metrics = _deduplicate_findings_cli(all_findings)

    print(
        f"[Dedup] Total: {dedup_metrics['total_findings']} → Unique: {dedup_metrics['unique_findings']} (removed {dedup_metrics['duplicates_found']} duplicates)"
    )

    # Apply confidence filter (≥80%)
    filtered_findings = []
    rejected_count = 0

    for finding in all_findings:
        conf = finding.get("confidence", 0)
        if conf >= min_confidence_filter:
            filtered_findings.append(finding)
        else:
            rejected_count += 1

    # Build summary
    summary = {
        "input": len(all_findings),
        "output": len(filtered_findings),
        "rejection_reasons": [f"Low confidence (<{min_confidence_filter}%): {rejected_count}"],
    }

    print(
        f"[Quality Gate Layer 4] Input: {summary['input']} findings, Output: {summary['output']} findings (≥{min_confidence_filter}% confidence)",
        file=sys.stderr,
    )

    # If no findings pass filter, return original results
    if not filtered_findings:
        print(
            "[Quality Gate Layer 4] No findings passed confidence filter - showing raw outputs",
            file=sys.stderr,
        )
        return results, summary

    # Create filtered results with only high-confidence findings
    # Rebuild findings JSON for output
    filtered_results = {}

    for cli_name, cli_data in results.items():
        if not isinstance(cli_data, dict):
            filtered_results[cli_name] = cli_data
            continue

        # Filter findings for this CLI
        cli_findings = [f for f in filtered_findings if f.get("source") == cli_name]

        if cli_findings:
            # Build filtered output JSON
            filtered_output = {
                "findings": cli_findings,
                "count": len(cli_findings),
                "quality_gate_filtered": True,
                "min_confidence": min_confidence_filter,
            }
            filtered_results[cli_name] = {"output": json.dumps(filtered_output, indent=2)}
        else:
            # No findings from this CLI passed filter - mark as filtered out
            filtered_results[cli_name] = {
                "output": json.dumps(
                    {
                        "findings": [],
                        "count": 0,
                        "quality_gate_filtered": True,
                        "filtered_out": "All findings below confidence threshold",
                    },
                    indent=2,
                )
            }

    return filtered_results, summary


# Default models
DEFAULT_OPENCODE_MODEL = "chutes/deepseek-ai/DeepSeek-V3-0324-TEE"


def _resolve_opencode_model(model: str | None) -> str:
    """Resolve model aliases to full OpenCode model IDs.

    Aliases provide convenient shortcuts for commonly-used models.
    Full model IDs are passed through unchanged.

    Args:
        model: Alias (e.g., "kimi") or full model ID

    Returns:
        Full OpenCode model ID string
    """
    aliases = {
        # User-preferred models
        "kimi": "chutes/moonshotai/Kimi-K2.5-TEE",
        "minimax": "chutes/MiniMaxAI/MiniMax-M2.1-TEE",
        "nemotron": "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
        "mimo": "chutes/XiaomiMiMo/MiMo-V2-Flash",
        "glm5": "zai/glm-5.1",
        "k2": "chutes/moonshotai/Kimi-K2.5-TEE",
        "deepseek-v3.2": "chutes/deepseek-ai/DeepSeek-V3.2-TEE",
        "deepseek-v3.2-tee": "chutes/deepseek-ai/DeepSeek-V3.2-TEE",
    }
    if model in aliases:
        return aliases[model]
    return model or DEFAULT_OPENCODE_MODEL


# Import q_context for session-based scope detection
try:
    from q_context import get_session_activity
except ImportError:
    get_session_activity = None


# Get Z.ai API key from environment or use default from proxy script
def get_glm_api_key() -> str:
    """Get Z.ai API key from environment variable with validation (SEC-001 fix)."""
    api_key = os.environ.get("ZAI_API_KEY", "")

    # Validation: key must exist and have valid format
    if not api_key:
        raise ValueError(
            "ZAI_API_KEY environment variable not set. Set it with: set ZAI_API_KEY=your-key"
        )

    # Validate expected format (common prefixes: sk-, zk-, etc.)
    if not api_key.startswith(("sk-", "zk-", "Bearer ")):
        # Allow bypass for non-standard formats but warn
        if len(api_key) < 20:
            raise ValueError(f"Invalid API key format (too short: {len(api_key)} chars)")

    return api_key


def mask_api_key(key: str) -> str:
    """Mask API key for safe logging (SEC-001 fix)."""
    if not key:
        return "****"
    if len(key) <= 8:
        return "****"
    # Show only first 4 and last 4 characters
    return f"{key[:4]}...{key[-4:]}"


# Global repo root (COMP-RECHECK-002 fix: single source of truth)
_REPO_ROOT = _get_repo_root()

# Default paths for conversation history
_CLAUDE_PROJECTS_DIR = Path.home() / ".claude" / "projects"
_REPO_PATH = _REPO_ROOT  # Use global _REPO_ROOT
# Handle special case for Windows drive roots (P: -> P--)
_REPO_NAME = (
    _REPO_PATH.name.replace(":", "-") + "-"
    if len(_REPO_PATH.name) == 1
    else _REPO_PATH.name.replace(":", "-")
)
if not _REPO_NAME:
    _REPO_NAME = "P--"
_SESSION_DIR = _CLAUDE_PROJECTS_DIR / _REPO_NAME

# Session file stat cache to avoid redundant filesystem calls (PERF-001 fix)
# Cache entries: {path_str: (mtime, timestamp)}
_SESSION_STAT_CACHE: dict[str, tuple[float, float]] = {}
_CACHE_TTL = 60  # seconds


def _is_in_workspace(path_str: str) -> bool:
    r"""Check if a path is within the repo workspace (COMP-RECHECK-002 fix: dynamic check).

    This function checks if a given path is within the repository workspace
    by comparing against the dynamic repo root. Replaces hardcoded "P:" check
    with flexible path resolution.

    The workspace check logic:
    1. Returns False for empty or None strings (short-circuit safety)
    2. Resolves the path string to absolute path
    3. Checks if the resolved path is within _REPO_ROOT

    Args:
        path_str: A path string to check. Can be absolute or relative.

    Returns:
        True if path is within the repo workspace, False otherwise.
    """
    if not path_str:
        return False
    try:
        resolved = Path(path_str).resolve()
        return resolved.is_relative_to(_REPO_ROOT)
    except (OSError, ValueError):
        return False


def _read_context_file(file_path: str, allowed_root: Path | None = None) -> str:
    """Read context file with path traversal protection (SEC-003 fix)."""
    path = Path(file_path).resolve()

    # If not found, try relative to cwd
    if not path.exists():
        path = (Path.cwd() / file_path).resolve()

    # Validate path is within allowed directories
    if allowed_root is None:
        allowed_root = Path.cwd().resolve()

    try:
        path.relative_to(allowed_root)
    except ValueError:
        raise PermissionError(f"Access denied: file outside allowed directory: {path}")

    # Additional check: must be a regular file
    if not path.is_file():
        raise PermissionError(f"Not a file: {path}")

    return path.read_text(encoding="utf-8", errors="ignore")


def _add_datetime_suffix(file_path: str) -> str:
    """Add a datetime suffix to an output filename.

    Transforms a filename into the format: <basename>_YYYYMMDD_HHMMSS_XXXXXX.<ext>

    The datetime suffix is inserted between the base filename and its extension.
    If no extension is present, '.json' is appended by default for consistency
    with the JSON output format used by this CLI tool.

    Format details:
        - YYYY: 4-digit year (e.g., 2025)
        - MM: 2-digit month (01-12)
        - DD: 2-digit day (01-31)
        - HH: 2-digit hour in 24-hour format (00-23)
        - MM: 2-digit minute (00-59)
        - SS: 2-digit second (00-59)
        - XXXXXX: 6-digit microseconds (000000-999999) for uniqueness

    Example transformations:
        "output.json"      -> "output_20250125_143022_123456.json"
        "data/results.txt" -> "data/results_20250125_143022_123456.txt"
        "logfile"          -> "logfile_20250125_143022_123456.json"

    Args:
        file_path: The original file path provided via the --output-file argument.
                   Can be an absolute path, relative path, or just a filename.

    Returns:
        A string representing the new file path with the datetime suffix inserted
        before the file extension. The directory component is preserved.

    Raises:
        None. This function handles all path manipulations using pathlib.Path
              and does not perform file I/O operations.

    Note:
        The datetime represents the moment this function is called. The microseconds
        component ensures uniqueness even for rapid consecutive calls within the same
        second, preventing file overwrites when used in the same directory.
    """
    # Parse the input path into components
    parsed_path = Path(file_path)

    # Generate current timestamp in sortable format (YYYYMMDD_HHMMSS_XXXXXX)
    # This format ensures chronological ordering when sorted alphabetically
    # and includes microseconds for uniqueness
    current_datetime = datetime.now()
    current_timestamp = current_datetime.strftime("%Y%m%d_%H%M%S_%f")

    # Extract the filename stem (without extension) and extension
    # stem: "output" from "output.json"
    # suffix: ".json" from "output.json"
    base_name = parsed_path.stem
    file_extension = parsed_path.suffix

    # Default to .json extension if none provided
    # This ensures consistent output format for the LLM CLI results
    if not file_extension:
        file_extension = ".json"

    # Construct the new filename with datetime suffix
    # Format: <basename>_<timestamp><extension>
    filename_with_suffix = f"{base_name}_{current_timestamp}{file_extension}"

    # Preserve the original directory structure
    # Reassemble the full path: <parent_dir>/<new_filename>
    output_path = parsed_path.parent / filename_with_suffix

    return str(output_path)


def _copy_to_tmp_if_needed(file_path: Path) -> Path:
    r"""Copy external files to P:/tmp/ if they are outside the P:\ workspace.

    This function ensures that files referenced from outside the P:\ workspace are
    copied to a temporary location within the workspace. This is necessary for
    consistent file access across different tools and contexts in the LLM CLI system.

    Copy behavior and skip conditions:
    - Skip if file is already in P:/tmp/ (no redundant copies)
    - Skip if file is anywhere within P:\ workspace (workspace files are accessible)
    - Copy if file is outside P:\ (external files need to be brought into workspace)

    The copy operation:
    - Creates P:/tmp/ directory if it doesn't exist
    - Uses shutil.copy2() to preserve file metadata (timestamps, permissions)
    - Returns the path to the copied file
    - Raises PermissionError if copy fails (permissions, I/O errors)

    Args:
        file_path: Path to the file to potentially copy. Can be absolute or
            relative; will be resolved to absolute path for processing.

    Returns:
        Path pointing to the copied location (if copied) or original path (if no copy).

    Raises:
        PermissionError: If the copy operation fails due to permissions, I/O errors,
            or other filesystem issues. Includes source and destination paths in message.
    """
    # Resolve to absolute path
    resolved_path = file_path.resolve()

    # Define workspace root (COMP-RECHECK-002 fix: use dynamic repo root)
    workspace_root = _REPO_ROOT

    # If file is already in P:/tmp/, skip copy
    if resolved_path.parent == workspace_root / "tmp":
        return resolved_path

    # If file is in P:\ workspace, no copy needed
    try:
        resolved_path.relative_to(workspace_root)
        return resolved_path
    except ValueError:
        # File is outside P:\ workspace, need to copy
        pass

    # Create P:/tmp/ if it doesn't exist
    tmp_dir = workspace_root / "tmp"
    tmp_dir.mkdir(exist_ok=True)

    # Copy file to P:/tmp/ using shutil.copy2() to preserve metadata
    dest_path = tmp_dir / resolved_path.name
    try:
        shutil.copy2(resolved_path, dest_path)
    except (PermissionError, OSError) as e:
        raise PermissionError(f"Failed to copy {resolved_path} to {dest_path}: {e}") from e

    return dest_path


def _format_session_history(
    session_file: Path, after_timestamp: float | None = None, max_entries: int = 100
) -> str:
    """Format session history with optimized filtering (PERF-001 fix)."""
    try:
        lines = session_file.read_text(encoding="utf-8", errors="ignore").strip().split("\n")
    except OSError:
        return ""

    entries = []
    # Process last max_entries lines
    for line in lines[-max_entries:]:
        # Quick pre-filter: skip lines without essential markers (avoid expensive JSON parse)
        if '"type"' not in line and '"role"' not in line:
            continue
        # Skip meta entries quickly
        if '"file-history-snapshot"' in line or '"isMeta":true' in line or '"isMeta": true' in line:
            continue

        try:
            entry = json.loads(line)
            entry_type = entry.get("type", "")

            # Filter out meta entries
            if entry_type == "file-history-snapshot" or entry.get("isMeta"):
                continue

            msg = entry.get("message", {})
            if not msg:
                continue

            # Filter by timestamp if specified
            if after_timestamp:
                timestamp_str = entry.get("timestamp", "")
                if timestamp_str:
                    try:
                        entry_ts = datetime.fromisoformat(
                            timestamp_str.replace("Z", "+00:00")
                        ).timestamp()
                        if entry_ts <= after_timestamp:
                            continue
                    except (ValueError, AttributeError):
                        pass

            role = msg.get("role", entry_type)
            content = msg.get("content", "")

            # Extract content from list format
            if isinstance(content, list):
                content_parts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            content_parts.append(block.get("text", ""))
                        elif block.get("type") == "tool_use":
                            content_parts.append(f"[Tool: {block.get('name', 'unknown')}]")
                        else:
                            content_parts.append(str(block))
                    else:
                        content_parts.append(str(block))
                content = "\n".join(content_parts)

            # Skip empty content
            if not content or content == "<command-stdout></command-stdout>":
                continue

            # Truncate and format
            timestamp = entry.get("timestamp", "")[:19]
            entries.append(f"[{timestamp}] {role.upper()}: {str(content)[:500]}")
        except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
            continue

    if not entries:
        return ""
    return "Context from session " + session_file.stem + ":\n" + "\n".join(entries)


def _find_session_by_marker(marker: str) -> str | None:
    """Find session by marker with optimized single-pass scanning (PERF-001 fix)."""
    if not _SESSION_DIR.exists():
        return None

    import time

    cache_time = time.time()

    session_files = list(_SESSION_DIR.glob("*.jsonl"))
    if not session_files:
        return None

    # Single pass: collect (mtime, file) tuples with caching
    files_with_mtime = []
    for session_file in session_files:
        path_str = str(session_file)
        # Check cache first
        if path_str in _SESSION_STAT_CACHE:
            cached_mtime, cached_time = _SESSION_STAT_CACHE[path_str]
            if cache_time - cached_time < _CACHE_TTL:
                files_with_mtime.append((cached_mtime, session_file))
                continue

        # Cache miss or expired - get mtime and cache it
        try:
            mtime = session_file.stat().st_mtime
            _SESSION_STAT_CACHE[path_str] = (mtime, cache_time)
            files_with_mtime.append((mtime, session_file))
        except OSError:
            files_with_mtime.append((0, session_file))

    # Sort by mtime (descending) - we already have mtimes, no more stat() calls

    # Check for marker in filename while we have the list
    for mtime, session_file in files_with_mtime:
        if marker in session_file.stem:
            content = _format_session_history(session_file)
            if content:
                return content

    # If no filename match, try timestamp-based search
    try:
        marker_dt = datetime.fromisoformat(marker.replace("Z", "+00:00"))
        marker_ts = marker_dt.timestamp()
    except ValueError:
        marker_ts = None

    if marker_ts is not None:
        for mtime, session_file in files_with_mtime:
            content = _format_session_history(session_file, after_timestamp=marker_ts)
            if content:
                return content

    return None


def _get_auto_context() -> str:
    if not _SESSION_DIR.exists():
        return ""
    session_files = list(_SESSION_DIR.glob("*.jsonl"))
    if not session_files:
        return ""
    latest = max(session_files, key=lambda p: p.stat().st_mtime)
    return _format_session_history(latest)


def get_context(
    context_source: str | None, auto_context: bool = False, cli_name: str | None = None
) -> str:
    """Get context for LLM query.

    Args:
        context_source: File path, session marker, or plain text context
        auto_context: If True, auto-load latest session history
        cli_name: CLI name (unused, kept for backward compatibility - all CLIs now use @file syntax)

    Returns:
        Context string. For file context, returns @file syntax (consistent across all CLIs).
        For auto-context and session context, returns embedded contents.
    """
    if auto_context:
        return _get_auto_context()
    if not context_source:
        return ""

    # Check for multi-file context (colon or comma separated paths)
    if ":" in context_source or "," in context_source:
        return _read_multi_file_context(context_source, cli_name=cli_name)

    # Single file check
    path = Path(context_source)
    if not path.exists():
        path = Path.cwd() / context_source

    if path.exists() and path.is_file():
        # Copy external files to P:/tmp/ if outside workspace, then return @file syntax
        final_path = _copy_to_tmp_if_needed(path)
        # Use forward slashes for @file syntax (cross-platform compatibility)
        return f"@{final_path.as_posix()}"
    if path.exists() and path.is_dir():
        # NEW: Use file_context module to handle directories
        # Collects all files recursively and formats with clear structure
        try:
            formatted_context, metadata = build_context_from_paths([context_source])
            print_context_summary(metadata)
            return formatted_context
        except Exception as e:
            print(f"[Warning: Error processing directory context: {e}]", file=sys.stderr)
            print("[Hint: Try specifying individual files instead]", file=sys.stderr)
            return ""

    # Session lookup
    session_content = _find_session_by_marker(context_source)
    if session_content:
        return session_content

    # Return as-is (plain text context)
    return context_source


def detect_session_context(wt_session: str | None = None) -> str:
    """Detect review context from session activity using q_context (PERF-012 fix: adds timeout)."""
    if not wt_session or not get_session_activity:
        return ""

    try:
        # Wrap in ThreadPoolExecutor to add timeout (PERF-012 fix)
        # Prevents indefinite hangs if q_context is slow or unresponsive
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(
                get_session_activity,
                wt_session=wt_session,
                minutes=30,
                operations=("write", "edit"),
            )
            # 10 second timeout for session activity detection
            session = future.result(timeout=10)
    except concurrent.futures.TimeoutError:
        # Session detection took too long - skip it
        return ""
    except Exception:
        return ""

    topic = session.get("topic", "")
    files = session.get("files_worked", [])

    if not files:
        return ""

    # Build context from session files
    context_parts = []
    if topic:
        context_parts.append(f"## Session Topic\n{topic}")

    context_parts.append("## Recent Files Modified")

    for file_path in files[:5]:  # Max 5 files
        path = Path(file_path)
        if path.exists():
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                # Truncate large files (first 2000 chars)
                preview = content[:2000]
                if len(content) > 2000:
                    preview += "\n... [truncated]"
                context_parts.append(f"\n### {path}\n{preview}")
            except Exception:
                context_parts.append(f"\n### {path}\n[Error reading file]")

    return "\n".join(context_parts)


def _read_multi_file_context(context_source: str, cli_name: str | None = None) -> str:
    """Read context from multiple files.

    Supports comma (,) as separator for cross-platform compatibility.
    Colon (:) is NOT used as separator to avoid conflicts with Windows drive letters.

    Args:
        context_source: Comma-separated file paths
        cli_name: CLI name (unused, kept for backward compatibility - all CLIs now use @file syntax)

    Returns:
        Space-separated @file references for all files (consistent behavior across codex, qwen, gemini)
    """
    import sys

    # Use comma separator only (colon conflicts with Windows drive letters like C:\)
    if "," in context_source:
        parts = context_source.split(",")
    else:
        # Single path (may contain colons like Windows paths)
        parts = [context_source]

    contexts = []
    at_file_refs = []

    for part in parts:
        part = part.strip()
        if not part:
            continue

        path = Path(part)
        if not path.exists():
            path = Path.cwd() / part

        if path.exists():
            # Copy to tmp if needed (for external files) and use the returned path
            path_to_use = _copy_to_tmp_if_needed(path)

            # All CLIs (codex, qwen, gemini) now use @file syntax for consistency
            # Use forward slashes for @file syntax (cross-platform compatibility)
            at_file_refs.append(f"@{path_to_use.as_posix()}")
        else:
            # Warn about missing file
            print(f"[Warning: File not found: {part}]", file=sys.stderr)

    # Return @file syntax for supported CLIs
    if at_file_refs:
        return " ".join(at_file_refs)

    return "\n\n".join(contexts)


# calc_timeout is now imported from lib.parallel_llm


def generate_parallel_bash_commands(
    query: str,
    qwen_only: bool = False,
    gemini_only: bool = False,
    codex_only: bool = False,
) -> list[str]:
    """Generate bash commands for parallel execution.

    Returns a list of bash commands that can be run in parallel.
    Each command pipes the query to stdin.
    """
    import shlex

    # Determine which LLMs to run
    if not qwen_only and not gemini_only and not codex_only:
        run_qwen = True
        run_gemini = True
        run_codex = True
    else:
        run_qwen = qwen_only
        run_gemini = gemini_only
        run_codex = codex_only

    commands = []

    # Use shlex.quote for ALL platforms to escape shell metacharacters
    # This prevents command injection via backticks, $(), pipes, etc.
    safe_query = shlex.quote(query)

    if run_qwen:
        commands.append(f"echo {safe_query} | qwen")
    if run_gemini:
        # Use stdin pipe (echo X | gemini) - do NOT also use -p with the same query
        # Gemini rejects "Cannot use both a positional prompt and the --prompt (-p) flag together"
        commands.append(f"echo {safe_query} | gemini -y -o text")
    if run_codex:
        # Codex exec takes query as argument (not stdin)
        commands.append(f'codex exec "{query}"')

    return commands


def _parse_opencode_streaming_json(output: str) -> str:
    """Parse OpenCode's streaming JSON format to extract text content.

    OpenCode returns multiple JSON objects (one per line) with different types:
    - {"type":"step_start",...} - Start of generation
    - {"type":"text","part":{"text":"content",...}} - Actual response text (text is inside part object)
    - {"type":"step_finish",...} - End of generation

    This function extracts and concatenates all text from "type":"text" objects.

    Args:
        output: Raw stdout from opencode CLI

    Returns:
        Extracted text content, or original output if parsing fails
    """
    import json

    try:
        texts = []
        # Handle both Windows (\r\n) and Unix (\n) line endings
        for line in output.strip().replace("\r\n", "\n").split("\n"):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                # OpenCode's streaming JSON has text inside the "part" object
                if obj.get("type") == "text":
                    part = obj.get("part", {})
                    if "text" in part:
                        texts.append(part["text"])
            except json.JSONDecodeError:
                # Skip non-JSON lines (like INFO log messages)
                continue
        return "".join(texts) if texts else output
    except Exception:
        return output


def _determine_active_llms(
    qwen_only: bool,
    gemini_only: bool,
    codex_only: bool,
    opencode_only: bool,
    glm_flash_only: bool,
    pi_m27_only: bool = False,
    pi_glm_only: bool = False,
    copilot_only: bool = False,
) -> dict[str, bool]:
    """Determine which LLMs to run based on flags.

    Args:
        qwen_only, gemini_only, codex_only, opencode_only, glm_flash_only: CLI flags
        pi_m27_only: Run only pi with minimax/MiniMax-M2.7
        pi_glm_only: Run only pi with zai/glm-5.1
        copilot_only: Run only GitHub Copilot CLI

    Returns:
        Dictionary with boolean flags for each LLM
    """
    has_cli_flags = (
        qwen_only or gemini_only or codex_only or opencode_only or pi_m27_only or pi_glm_only or copilot_only
    )

    if not has_cli_flags:
        return {
            "qwen": False,
            "gemini": True,
            "codex": True,
            "opencode": False,
            "glm_flash": False,
            "pi_m27": True,
            "pi_glm": True,
            "copilot": False,
        }
    return {
        "qwen": qwen_only,
        "gemini": gemini_only,
        "codex": codex_only,
        "opencode": opencode_only,
        "glm_flash": False,
        "pi_m27": pi_m27_only,
        "pi_glm": pi_glm_only,
        "copilot": copilot_only,
    }


def _get_cli_preview(
    qwen_only: bool,
    gemini_only: bool,
    codex_only: bool,
    opencode_only: bool,
    glm_flash_only: bool,
    opencode_models: list[str],
    pi_m27_only: bool = False,
    pi_glm_only: bool = False,
    copilot_only: bool = False,
) -> str:
    """Build a preview string showing which CLIs and LLMs will be used.

    Args:
        qwen_only, gemini_only, codex_only, opencode_only, glm_flash_only: CLI flags
        opencode_models: List of OpenCode model names
        pi_m27_only: Run only pi with minimax/MiniMax-M2.7
        pi_glm_only: Run only pi with zai/glm-5.1

    Returns:
        Formatted string listing all CLIs/LLMs that will be invoked
    """
    has_any_flag = (
        qwen_only or gemini_only or codex_only or opencode_only or glm_flash_only
        or pi_m27_only or pi_glm_only or copilot_only
    )

    # Collect items
    native_clis = []
    if qwen_only or not has_any_flag:
        native_clis.append("qwen")
    if gemini_only or not has_any_flag:
        native_clis.append("gemini")
    if codex_only or not has_any_flag:
        native_clis.append("codex")
    if copilot_only or not has_any_flag:
        native_clis.append("copilot")

    opencode_models_list = []
    if opencode_only or not has_any_flag:
        models = opencode_models if opencode_models else [DEFAULT_OPENCODE_MODEL]
        for m in models:
            # Handle "opencode:nemotron" style names from results
            if ":" in m:
                model_id = m.split(":", 1)[1]
            else:
                model_id = m
            # Shorten long model paths for display
            if "/" in model_id:
                parts = model_id.split("/")
                model_id = parts[-1]  # Just the model name, not the full path
            opencode_models_list.append(model_id)

    has_glm = glm_flash_only or (not has_any_flag and os.environ.get("ZAI_API_KEY"))

    # Build output
    lines = ["[CLI/LLM Preview]"]

    if native_clis:
        lines.append(f"  Native CLIs:")
        for m in native_clis:
            lines.append(f"    • {m}")

    if opencode_models_list:
        lines.append("")
        n = len(opencode_models_list)
        lines.append(f"  OpenCode ({n} parallel)")
        for m in opencode_models_list:
            lines.append(f"    • {m}")

    return "\n".join(lines)


def _build_cli_commands(
    query: str,
    run_qwen: bool,
    run_gemini: bool,
    run_codex: bool,
    run_opencode: bool,
    opencode_models: list[str],
    run_pi_m27: bool = False,
    run_pi_glm: bool = False,
    run_copilot: bool = False,
    context_file: str | None = None,
) -> list[tuple[str, str]]:
    """Build platform-specific CLI command list.

    Args:
        query: User query string
        run_qwen, run_gemini, run_codex, run_opencode: Boolean flags
        opencode_models: List of OpenCode model names (empty list = use default)
        run_pi_m27: Run pi with minimax/MiniMax-M2.7
        run_pi_glm: Run pi with zai/glm-5.1
        context_file: Optional file path for pi -p @filepath flag

    Returns:
        List of (name, command) tuples. Multiple opencode models get distinct
        names like "opencode:nemotron", "opencode:glm5".
    """
    ROOT_PREFIX = f"cd {_REPO_ROOT} && "
    npm_root = Path.home() / "AppData" / "Roaming" / "npm" / "node_modules"

    # Platform-specific command templates
    if sys.platform == "win32":
        qwen_cmd = f'{ROOT_PREFIX}node "{npm_root / "@qwen-code" / "qwen-code" / "cli.js"}"'
        gemini_cmd = (
            f'{ROOT_PREFIX}node "{npm_root / "@google" / "gemini-cli" / "bundle" / "gemini.js"}"'
        )
        # Codex companion wrapper (required - direct codex exec doesn't work)
        codex_companion = Path.home() / ".claude" / "plugins" / "cache" / "openai-codex" / "codex" / "1.0.3" / "scripts" / "codex-companion.mjs"
        codex_cmd = f'node "{codex_companion}" task --model gpt-5.4-mini'
    else:
        qwen_cmd = f"{ROOT_PREFIX}qwen"
        gemini_cmd = f"{ROOT_PREFIX}gemini"
        codex_cmd = f"{ROOT_PREFIX}codex exec --model gpt-5.4-mini"

    commands = []
    if run_qwen:
        commands.append(("qwen", qwen_cmd))
    if run_gemini:
        # Use -p flag with list format to avoid:
        # 1. Shell pipe issues on Windows (stdin conflicts)
        # 2. Positional argument conflicts (gemini rejects both -p AND positional)
        # Pass as list to create_subprocess_exec (not shell) so -p flag works correctly
        # On Windows, must use full node path since npm global commands aren't in PATH for exec
        if sys.platform == "win32":
            gemini_script = npm_root / "@google" / "gemini-cli" / "bundle" / "gemini.js"
            gemini_args = ["node", str(gemini_script), "-y", "-o", "text", "-p", query]
        else:
            gemini_args = ["gemini", "-y", "-o", "text", "-p", query]
        commands.append(("gemini", gemini_args))
    if run_codex:
        commands.append(("codex", codex_cmd))
    if run_opencode:
        if not opencode_models:
            opencode_models = [DEFAULT_OPENCODE_MODEL]
        for model in opencode_models:
            resolved = _resolve_opencode_model(model)
            if sys.platform == "win32":
                opencode_cmd = (
                    f'{ROOT_PREFIX}node "{npm_root / "opencode-ai" / "bin" / "opencode"}" run -m {resolved}'
                )
            else:
                opencode_cmd = f"{ROOT_PREFIX}opencode run -m {resolved}"
            name = f"opencode:{resolved.split('/')[-1]}"
            commands.append((name, opencode_cmd))

    # Pi agents (use list form to avoid shell escaping issues)
    if run_pi_m27:
        ctx_arg = ["-p", f"@{context_file}"] if context_file else []
        pi_m27_cmd = ["pi", "--model", "minimax/MiniMax-M2.7", *ctx_arg, query]
        commands.append(("pi-m27", pi_m27_cmd))
    if run_pi_glm:
        ctx_arg = ["-p", f"@{context_file}"] if context_file else []
        pi_glm_cmd = ["pi", "--model", "zai/glm-5.1", *ctx_arg, query]
        commands.append(("pi-glm", pi_glm_cmd))

    # GitHub Copilot CLI
    if run_copilot:
        copilot_cmd = ["copilot", "-p", query]
        commands.append(("copilot", copilot_cmd))

    return commands


def _execute_glm_api_mode(
    query: str,
    timeout: int,
    verbose: bool,
) -> dict[str, Any]:
    """Execute GLM API-only mode (when --glm-flash-only flag is set).

    Args:
        query: User query
        timeout: Request timeout in seconds
        verbose: Enable verbose output

    Returns:
        Dictionary of LLM results
    """
    import time

    glm_queries = [("glm-4.7-flash", query)]

    if verbose:
        for model, _ in glm_queries:
            print(f"[GLM-{model}] Queuing API request", flush=True)
        print(f"[PARALLEL] Running {len(glm_queries)} GLM API requests concurrently...", flush=True)
        start_all = time.time()

    api_key = get_glm_api_key()
    raw_results = asyncio.run(
        run_parallel_glm(glm_queries, api_key=api_key, timeout=timeout, verbose=verbose)
    )

    if verbose:
        elapsed_all = time.time() - start_all
        print(f"[PARALLEL] All GLM API requests completed in {elapsed_all:.1f}s", flush=True)

    results: dict[str, Any] = {}
    for name, result in raw_results.items():
        if result.get("error"):
            results[name] = {"error": result["error"], "output": ""}
        else:
            results[name] = {"output": result["output"], "error": None}

    return results


def _process_llm_results(
    raw_results: dict[str, Any],
) -> dict[str, Any]:
    """Process and format LLM results, filtering errors and parsing output.

    Args:
        raw_results: Raw results from run_parallel_commands

    Returns:
        Processed results with error filtering
    """
    results: dict[str, Any] = {}

    for name, result in raw_results.items():
        error = result.get("error", "")
        output = result.get("output", "")

        # Check for empty responses (silent CLI failures)
        if not output.strip() and not error:
            error = "Empty response - CLI may have failed silently"

        # Filter out INFO/DEBUG log messages from stderr (not actual errors)
        if error and not any(
            e in error.lower() for e in ["error", "fail", "exception", "http 4", "http 5"]
        ):
            # Error field contains only INFO/DEBUG logs - treat as success
            if name == "opencode":
                parsed_output = _parse_opencode_streaming_json(output)
                results[name] = {"output": parsed_output, "error": None}
            else:
                results[name] = {"output": output, "error": None}
        elif error:
            # Actual error - preserve it and clear output
            results[name] = {"error": error, "output": ""}
        # No error - process output normally
        elif name == "opencode":
            parsed_output = _parse_opencode_streaming_json(output)
            results[name] = {"output": parsed_output, "error": None}
        else:
            results[name] = {"output": output, "error": None}

    return results


def run_parallel_llm(
    query: str,
    qwen_only: bool = False,
    gemini_only: bool = False,
    codex_only: bool = False,
    opencode_only: bool = False,
    glm_flash_only: bool = False,
    pi_m27_only: bool = False,
    pi_glm_only: bool = False,
    copilot_only: bool = False,
    timeout: int = 180,
    output_format: str = "text",
    verbose: bool = False,
    opencode_models: list[str] = [],
    context_file: str | None = None,
) -> dict[str, Any]:
    """Run qwen, gemini, codex, pi-m27, pi-glm, and GLM-4.7-Flash via API in parallel.

    Uses asyncio for true parallel execution.
    """
    import asyncio
    import time

    # GLM API-only mode (when --glm-flash-only flag is set)
    if glm_flash_only:
        return _execute_glm_api_mode(query, timeout, verbose)

    # Determine which LLMs to run
    active = _determine_active_llms(
        qwen_only, gemini_only, codex_only, opencode_only, glm_flash_only,
        pi_m27_only, pi_glm_only, copilot_only,
    )

    # Build CLI command list
    commands = _build_cli_commands(
        query,
        active["qwen"],
        active["gemini"],
        active["codex"],
        active["opencode"],
        opencode_models,
        active["pi_m27"],
        active["pi_glm"],
        active["copilot"],
        context_file,
    )

    # Build gemini quota fallback chain: try different gemini models before falling back to pi agents
    # gemini model chain: auto (default) -> 3.1-pro-preview -> 3-flash-preview -> 3.1-flash-lite-preview -> pi-m27 -> pi-glm -> pi-elephant
    fallback_commands: dict[str, list[tuple[str, list[str]]]] = {}
    if active.get("gemini"):
        cmd_by_name = {name: cmd for name, cmd in commands}
        pi_m27_cmd = cmd_by_name.get("pi_m27")
        pi_glm_cmd = cmd_by_name.get("pi_glm")
        pi_elephant_cmd = cmd_by_name.get("pi_elephant")

        # Get the gemini command (list form on Windows, string form on Unix)
        gemini_cmd_list = None
        for name, cmd in commands:
            if name == "gemini" and isinstance(cmd, list):
                gemini_cmd_list = list(cmd)
                break

        if gemini_cmd_list:
            # Build model fallback chain by substituting -m flag
            # Chain: auto (default) -> 3.1-pro-preview -> 3-flash-preview -> 3.1-flash-lite-preview
            # If all gemini models exhausted, gemini slot is done — do NOT substitute pi agents
            gemini_models = [
                "gemini-3.1-pro-preview",
                "gemini-3-flash-preview",
                "gemini-3.1-flash-lite-preview",
            ]
            chain = []
            for model in gemini_models:
                fallback_cmd = _substitute_gemini_model(list(gemini_cmd_list), model)
                chain.append((f"gemini-{model}", fallback_cmd))
            fallback_commands["gemini"] = chain

    # Verbose output
    if verbose:
        for name, cmd in commands:
            print(f"[Agent-{name.upper()}] Spawning subprocess: {cmd}", flush=True)
        print(
            f"[PARALLEL] Running {len(commands)} agents concurrently via asyncio.gather()...",
            flush=True,
        )
        start_all = time.time()

    # Execute CLI commands and GLM API in parallel (single asyncio.gather)
    from parallel_llm import run_parallel_glm

    async def run_all_parallel():
        """Run CLI commands and GLM API in true parallel."""
        tasks = [
            run_parallel_commands(commands, timeout=timeout, input_text=query, verbose=verbose, cwd=str(_REPO_ROOT), fallback_commands=fallback_commands)
        ]

        # Add GLM API task if active
        if active["glm_flash"]:
            glm_queries = [("glm-4.7-flash", query)]
            api_key = get_glm_api_key()
            tasks.append(
                run_parallel_glm(glm_queries, api_key=api_key, timeout=timeout, verbose=verbose)
            )

        # Gather all results
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # First result is always CLI results
        raw_results = results[0]

        # Second result (if exists) is GLM results
        if active["glm_flash"] and len(results) > 1:
            glm_results = results[1]
            # Merge GLM results into CLI results
            for name, result in glm_results.items():
                raw_results[name] = result

        return raw_results

    raw_results = asyncio.run(run_all_parallel())

    if verbose:
        elapsed_all = time.time() - start_all
        print(f"[PARALLEL] All {len(commands)} agents completed in {elapsed_all:.1f}s", flush=True)

    # Process results
    return _process_llm_results(raw_results)


def expand_prompt(query: str) -> str:
    """Expand a simple query into a detailed prompt with specific requirements.

    Transforms natural language queries into detailed prompts with:
    - Citation requirements (require sources for claims)
    - Actionable recommendations (not "consider X")
    - Specific focus areas for reviews
    - Solo/AI-assisted work context (no team assignments)
    - Long-Term Thinking framework (Consequences & Opportunities)

    Args:
        query: Simple natural language string

    Returns:
        Expanded prompt with detailed instructions for the LLM
    """
    expanded = f"""Please respond to the following query with detailed, actionable guidance:

Query: {query}

Requirements:
1. CITATION: Provide specific citations for any claims, facts, or references. Include file paths, line numbers, or document sections where applicable.

2. ACTIONABLE: Provide specific, actionable recommendations rather than vague suggestions like "consider X". State exactly what should be done.

3. SPECIFIC: Focus on specific, concrete steps and examples. Avoid generic advice. For code reviews, focus on specific lines or functions.

4. SOLO DEVELOPER CONTEXT: This is for a solo developer working with AI assistance. Do not suggest team assignments, code reviews by others, or collaborative workflows that require multiple people.

5. LONG-TERM THINKING: Analyze recommendations through two dimensions:

   A. CONSEQUENCES: What happens downstream?
      - Maintenance burden: Who maintains this? Is it sustainable for one person?
      - Technical debt: Does this create future work or complexity?
      - Coupling: Does this lock in decisions prematurely or create dependencies?
      - Complexity: Is there a simpler path to the same outcome?

   B. OPPORTUNITIES: What else becomes possible?
      - Reusability: Can this solve other problems or be applied elsewhere?
      - Learning: Does this build valuable capability or understanding?
      - Extensibility: Can this grow without major rework?
      - Leverage: Does this multiply value elsewhere in the system?

Please structure your response clearly with the following format:
- Direct answer to the query
- Actionable recommendations (numbered steps)
- Consequences analysis for each recommendation (maintenance, debt, coupling, complexity)
- Opportunities analysis for each recommendation (reusability, learning, extensibility, leverage)
- Specific examples or code snippets where relevant
- Citations for any references made
"""
    return expanded


def show_prompt_options(expanded_prompt: str, original_prompt: str) -> str:
    """Display a menu of prompt options and get user selection.

    Args:
        expanded_prompt: The expanded/detailed prompt version
        original_prompt: The original simple query

    Returns:
        The selected prompt based on user input

    Raises:
        ValueError: If user enters invalid selection (not 1, 2, or 3)
    """
    print("\n=== Prompt Options ===")
    print(f"1. {expanded_prompt}")
    print(f"2. {original_prompt}")
    print("3. Custom prompt (user enters their own)")
    print()

    choice = input("Select option (1-3): ").strip()

    if choice == "1":
        return expanded_prompt
    if choice == "2":
        return original_prompt
    if choice == "3":
        custom = input("Enter your custom prompt: ").strip()
        return custom
    raise ValueError(f"Invalid selection: {choice}. Please select 1, 2, or 3.")


def prompt_with_expansion_option(original_query: str) -> str:
    """Prompt user to choose between expanded and original prompt.

    Args:
        original_query: The original simple query string

    Returns:
        The selected prompt (expanded, original, or custom)
    """
    expanded = expand_prompt(original_query)

    while True:
        try:
            return show_prompt_options(expanded, original_query)
        except ValueError as e:
            print(f"Invalid selection: {e}")
            print("Please try again.")


def _extract_issues_by_priority(outputs: list[str]) -> dict[str, list[str]]:
    """Extract issues from LLM outputs grouped by priority.

    Looks for patterns like CRIT-001, HIGH-001, MED-001, etc.
    and groups them by priority level.

    Args:
        outputs: List of LLM output strings

    Returns:
        Dict with keys 'critical', 'high', 'medium' containing lists of issue IDs
    """
    import re

    issues = {"critical": [], "high": [], "medium": []}

    # Pattern to match issue IDs like CRIT-001, HIGH-001, MED-001
    pattern = r"\b(CRIT|HIGH|MED)-\d{3}\b"

    for output in outputs:
        matches = re.findall(pattern, output, re.IGNORECASE)
        for match in matches:
            priority = match.lower()
            if priority == "crit":
                issues["critical"].append(match)
            elif priority == "high":
                issues["high"].append(match)
            elif priority == "med":
                issues["medium"].append(match)

    # Remove duplicates while preserving order
    for priority in issues:
        seen = set()
        issues[priority] = [x for x in issues[priority] if not (x in seen or seen.add(x))]

    return issues


def _format_progressive_selections(issues: dict[str, list[str]]) -> str:
    """Format progressive selection options for recommendations.

    Args:
        issues: Dict with 'critical', 'high', 'medium' lists of issue IDs

    Returns:
        Formatted string with progressive selection options (continuation list)
    """
    lines = []

    critical = issues["critical"]
    high = issues["high"]
    medium = issues["medium"]

    # Option 6: Critical only
    if critical:
        crit_list = (
            ", ".join(critical)
            if len(critical) <= 5
            else f"{', '.join(critical[:3])}, ... ({len(critical)} total)"
        )
        lines.append(f"6. Fix Critical issues only - {crit_list}")
    else:
        lines.append("6. ~~Fix Critical issues only~~ - No critical issues found")

    # Option 7: Critical + High
    crit_high = critical + high
    if crit_high:
        ch_list = (
            ", ".join(crit_high)
            if len(crit_high) <= 8
            else f"{', '.join(crit_high[:4])}, ... ({len(crit_high)} total)"
        )
        lines.append(f"7. Fix Critical+High issues - {ch_list}")
    else:
        lines.append("7. ~~Fix Critical+High issues~~ - No critical or high issues found")

    # Option 3: All issues
    all_issues = critical + high + medium
    if all_issues:
        all_list = (
            ", ".join(all_issues)
            if len(all_issues) <= 10
            else f"{', '.join(all_issues[:5])}, ... ({len(all_issues)} total)"
        )
        lines.append(f"x. Fix All issues - {all_list}")
    else:
        lines.append("x. ~~Fix All issues~~ - No issues found")

    return "\n".join(lines)


def format_results(results: dict[str, Any]) -> str:
    lines = []
    for name, data in results.items():
        lines.append(f"=== {name.upper()} RESULT ===")
        if data.get("error"):
            lines.append(f"ERROR: {data['error']}")
        else:
            lines.append(data.get("output", ""))
        lines.append("")

    lines.append("=== COMPARISON ===")
    for name, data in results.items():
        if data.get("output"):
            preview = data["output"][:200].replace("\n", " ")
            lines.append(f"- {name}: {preview}...")
        elif data.get("error"):
            err = data["error"]
            lines.append(f"- {name}: Error - {err[:200] if err else 'Unknown'}")
        else:
            lines.append(f"- {name}: [No output]")

    return "\n".join(lines)


def _extract_qwen_answer(output: str) -> str:
    """Extract answer from qwen CLI output (JSON array format)."""
    import json

    try:
        objects = json.loads(output)
        # Search backwards for last assistant message with text
        for obj in reversed(objects):
            if isinstance(obj, dict):
                # Look for result field first
                if "result" in obj:
                    return str(obj["result"])[:1000]
                # Look for assistant message content (LAST one wins)
                if obj.get("type") == "assistant":
                    content = obj.get("message", {})
                    if isinstance(content, dict):
                        items = content.get("content", [])
                        if isinstance(items, list):
                            for item in items:
                                if isinstance(item, dict) and "text" in item:
                                    text = item["text"]
                                    if text and text.strip():
                                        return text[:1000]
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
        pass

    # Fallback: find first line that looks like an answer
    for line in output.split("\n"):
        line = line.strip()
        if line and not line.startswith("{") and not line.startswith("["):
            return line[:200]

    return output[:200]


def _extract_gemini_answer(output: str) -> str:
    """Extract answer from gemini CLI output (JSON with response field)."""
    import json

    try:
        data = json.loads(output)
        if isinstance(data, dict):
            if "response" in data:
                return data["response"][:1000]
            # Fallback: look for nested content
            if "message" in data:
                msg = data["message"]
                if isinstance(msg, list):
                    # Search backwards for last text
                    for item in reversed(msg):
                        if isinstance(item, dict) and "text" in item:
                            return item["text"][:1000]
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
        pass

    return output[:200]


def _extract_codex_answer(output: str) -> str:
    """Extract answer from codex CLI output (JSONL format)."""
    import json
    import re

    try:
        # Search backwards for turn.completed (final turn)
        for line in reversed(output.split("\n")):
            obj = json.loads(line)
            if isinstance(obj, dict):
                if obj.get("type") == "turn.completed":
                    # This is the final turn summary
                    return "[Turn completed - see full output]"
                if obj.get("type") == "item.completed":
                    item = obj.get("item", {})
                    if isinstance(item, dict) and "text" in item:
                        text = item["text"]
                        # Only use if it's substantial (not just "Reading...")
                        if len(text) > 100:
                            return text[:1000]
    except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
        pass

    # Fallback: find first quoted string
    match = re.search(r'"text":\s*"([^"]+)"', output)
    if match:
        return match.group(1)

    return output[:200]


def _extract_answer(cli_name: str, output: str) -> str:
    """Extract the actual answer from a CLI's raw output.

    Each CLI returns data in different formats:
    - qwen: JSON array with system/assistant/result objects
    - gemini: JSON with response field
    - codex: JSONL lines (thread.started, turn.started, item.completed, turn.completed)
    - opencode: Plain text

    Dispatches to CLI-specific parser for each format.
    """
    output = output.strip()
    if not output:
        return "[No output]"

    # opencode: Plain text (no JSON parsing needed)
    if cli_name == "opencode":
        return output

    # Dispatch to CLI-specific parser
    parsers = {
        "qwen": _extract_qwen_answer,
        "gemini": _extract_gemini_answer,
        "codex": _extract_codex_answer,
    }

    parser = parsers.get(cli_name)
    if parser:
        return parser(output)

    # Fallback for unknown CLI: first meaningful line
    for line in output.split("\n"):
        line = line.strip()
        if (
            line
            and not line.startswith("{")
            and not line.startswith("[")
            and not line.startswith('"')
        ):
            return line[:200]

    return output[:200]


def format_summary(results: dict[str, Any]) -> str:
    """Brief summary showing only key answers extracted from outputs.

    Detects when extraction failed (large output, tiny extracted text)
    and prompts user to use --complete flag.
    """
    lines = ["## SUMMARY"]
    lines.append("")

    # Collect outputs for issue extraction
    all_outputs = []

    for name, data in results.items():
        if data.get("error"):
            lines.append(f"**{name}**: ERROR - {data['error']}")
        else:
            output = data.get("output", "")
            all_outputs.append(output)
            answer = _extract_answer(name, output)
            output_len = len(output)

            # Check if extraction was likely insufficient
            # (large output but tiny extracted text)
            if len(answer) < 200 and output_len > 5000:
                lines.append(
                    f"**{name}**: [Extraction incomplete - {output_len//1000}KB raw output]"
                )
                lines.append(f"   → Use `--complete` to see full output from {name}")
            elif "[No output]" in answer and output_len > 1000:
                lines.append(f"**{name}**: [Parsing failed - {output_len//1000}KB raw output]")
                lines.append(f"   → Use `--complete` to see full output from {name}")
            else:
                lines.append(f"**{name}**: {answer}")
        lines.append("")

    # Extract issues and add progressive selections
    issues = _extract_issues_by_priority(all_outputs)
    lines.append(_format_progressive_selections(issues))

    return "\n".join(lines)


def format_aggregate(results: dict[str, Any]) -> str:
    """Aggregated consensus view with comparison.

    Detects when extraction failed and prompts for --complete.
    """
    lines = ["## CONSENSUS VIEW"]
    lines.append("")

    # Extract answers from each CLI
    answers = {}
    for name, data in results.items():
        if data.get("error"):
            answers[name] = f"ERROR: {data['error']}"
        else:
            output = data.get("output", "")
            answer = _extract_answer(name, output)
            output_len = len(output)

            # Check if extraction failed and note it
            if len(answer) < 200 and output_len > 5000:
                answers[name] = (
                    f"[Extraction incomplete - see --complete for {output_len//1000}KB raw output]"
                )
            elif "[No output]" in answer and output_len > 1000:
                answers[name] = (
                    f"[Parsing failed - see --complete for {output_len//1000}KB raw output]"
                )
            else:
                answers[name] = answer

    # Check for consensus
    unique_answers = set(answers.values())
    if len(unique_answers) == 1 and all(not a.startswith("ERROR") for a in answers.values()):
        lines.append(f"**CONSENSUS**: {list(unique_answers)[0]}")
        lines.append(f"Agreement: {len(answers)}/{len(answers)} CLIs")
        lines.append("")
    else:
        lines.append(f"**PARTIAL AGREEMENT** ({len(unique_answers)} different responses)")
        lines.append("")

    # Show individual responses
    lines.append("### Individual Responses")
    lines.append("")
    for name, answer in answers.items():
        lines.append(f"- **{name}**: {answer}")

    return "\n".join(lines)


def format_complete(results: dict[str, Any]) -> str:
    """Complete raw outputs with full metadata.

    Large outputs (>10KB) are truncated with full output saved to JSON files.
    """
    # Chunk size threshold: 10KB
    CHUNK_THRESHOLD = 10 * 1024  # 10240 characters

    lines = []
    for name, data in results.items():
        lines.append(f"{'=' * 60}")
        lines.append(f"=== {name.upper()} (COMPLETE) ===")
        lines.append(f"{'=' * 60}")
        lines.append("")

        if data.get("error"):
            lines.append(f"ERROR: {data['error']}")
        else:
            output = data.get("output", "")
            output_size = len(output)

            # Large output handling: truncate with note
            if output_size > CHUNK_THRESHOLD:
                lines.append(f"[NOTE: Output is {output_size // 1024}KB - showing first 10KB]")
                lines.append(f"[Full output saved to: __csf/temp/cli_results/{name}_*.json]")
                lines.append("")
                lines.append(output[:CHUNK_THRESHOLD])
                lines.append("")
                lines.append(f"... [{output_size - CHUNK_THRESHOLD} characters truncated]")
            else:
                lines.append(output)
        lines.append("")
        lines.append("")

    return "\n".join(lines)


def format_diff(results: dict[str, Any]) -> str:
    """Show differences between CLI responses."""
    lines = ["## RESPONSE DIFFERENCES"]
    lines.append("")

    # Extract answers from each CLI
    answers = {}
    for name, data in results.items():
        if data.get("error"):
            answers[name] = f"ERROR: {data['error']}"
        else:
            answers[name] = _extract_answer(name, data.get("output", ""))

    # Group by unique responses
    response_groups: dict[str, list[str]] = {}
    for name, answer in answers.items():
        if answer not in response_groups:
            response_groups[answer] = []
        response_groups[answer].append(name)

    lines.append(f"### {len(response_groups)} unique response(s) from {len(answers)} CLI(s)")
    lines.append("")

    # Show each unique response with which CLIs gave it
    for i, (response, names) in enumerate(response_groups.items(), 1):
        lines.append(f"**Response {i}** (from {', '.join(names)}):")
        lines.append(f"  {response[:500]}{'...' if len(response) > 500 else ''}")
        lines.append("")

    # Highlight disagreements
    if len(response_groups) > 1:
        lines.append("### ⚠️ DISAGREEMENT DETECTED")
        lines.append(
            f"CLIs disagree on the answer. See {len(response_groups)} different responses above."
        )
    else:
        lines.append("### ✅ CONSENSUS")
        lines.append("All CLIs agree on the response.")

    return "\n".join(lines)


def format_quality_weighted(results: dict[str, Any]) -> str:
    """Quality-weighted output with consensus analysis and evidence validation.

    Pipeline:
    1. Extract answers from each CLI
    2. Build consensus matrix (who agrees with what)
    3. Annotate findings with consensus level
    4. Validate evidence citations (cite:file:line)
    5. Produce quality-weighted output

    Quality tiers:
    - HIGH: All CLIs agree + valid evidence citations
    - CONSENSUS: All CLIs agree (no evidence validation)
    - PARTIAL: Some CLIs agree
    - ALTERNATIVE: No consensus, minority views preserved
    """
    lines = ["## QUALITY-WEIGHTED FINDINGS"]
    lines.append("")

    # Step 1: Extract answers from each CLI
    cli_answers: dict[str, str] = {}
    for name, data in results.items():
        if data.get("error"):
            cli_answers[name] = f"ERROR: {data['error']}"
        else:
            output = data.get("output", "")
            answer = _extract_answer(name, output)
            cli_answers[name] = answer

    # Step 2: Build consensus matrix
    # Find unique answers and which CLIs agree on each
    answer_to_clis: dict[str, list[str]] = {}
    for cli, answer in cli_answers.items():
        if answer not in answer_to_clis:
            answer_to_clis[answer] = []
        answer_to_clis[answer].append(cli)

    total_clis = len(cli_answers)

    # Step 3: Classify findings by consensus level
    high_confidence = []  # All agree + has evidence
    consensus = []  # All agree (any answer)
    partial_agreements = []  # Some agree
    alternative_views = []  # No real consensus

    for answer, agreeing_clis in answer_to_clis.items():
        agreement_count = len(agreeing_clis)
        is_full_consensus = agreement_count == total_clis and all(
            not a.startswith("ERROR") for a in cli_answers.values()
        )

        finding = {
            "answer": answer,
            "agreeing_clis": agreeing_clis,
            "agreement_count": agreement_count,
            "agreement_pct": (agreement_count / total_clis) * 100,
            "has_evidence": "[source:" in answer.lower(),
        }

        if is_full_consensus:
            if finding["has_evidence"]:
                high_confidence.append(finding)
            else:
                consensus.append(finding)
        elif agreement_count > 1:
            partial_agreements.append(finding)
        else:
            alternative_views.append(finding)

    # Sort by agreement count descending
    partial_agreements.sort(key=lambda x: x["agreement_count"], reverse=True)
    alternative_views.sort(key=lambda x: x["agreement_count"], reverse=True)

    # Step 4: Build quality-weighted output
    if high_confidence:
        lines.append("### HIGH CONFIDENCE ✅")
        lines.append("*All CLIs agree + evidence citations verified*")
        lines.append("")
        for finding in high_confidence:
            clis = ", ".join(finding["agreeing_clis"])
            lines.append(f"- {finding['answer']}")
            lines.append(f"  *Agreeing: {clis}*")
        lines.append("")

    if consensus:
        lines.append("### CONSENSUS ✅")
        lines.append("*All CLIs agree (no evidence citations)*")
        lines.append("")
        for finding in consensus:
            clis = ", ".join(finding["agreeing_clis"])
            lines.append(f"- {finding['answer']}")
            lines.append(f"  *Agreeing: {clis}*")
        lines.append("")

    if partial_agreements:
        lines.append("### PARTIAL AGREEMENT ⚠️")
        lines.append("*Some CLIs agree, others disagree*")
        lines.append("")
        for finding in partial_agreements:
            clis = ", ".join(finding["agreeing_clis"])
            remaining = [c for c in cli_answers.keys() if c not in finding["agreeing_clis"]]
            lines.append(f"- {finding['answer']}")
            lines.append(f"  *Agreeing: {clis}*")
            if remaining:
                lines.append(f"  *Dissenting: {', '.join(remaining)}*")
        lines.append("")

    if alternative_views:
        lines.append("### ALTERNATIVE VIEWS 📎")
        lines.append("*No consensus - minority views preserved*")
        lines.append("")
        for finding in alternative_views:
            lines.append(f"- {finding['answer']}")
            lines.append(f"  *From: {', '.join(finding['agreeing_clis'])}*")
        lines.append("")

    # Summary
    lines.append("---")
    lines.append(f"*Consensus: {len(consensus) + len(high_confidence)} | Partial: {len(partial_agreements)} | Alternatives: {len(alternative_views)}*")

    return "\n".join(lines)


def _detect_review_query(query: str) -> bool:
    """Detect if query contains review/analyze keywords.

    Args:
        query: The query string to check

    Returns:
        True if query contains review-related keywords
    """
    review_keywords = ["review", "analyze", "audit", "gaps", "opportunities", "findings"]
    return any(keyword in query.lower() for keyword in review_keywords)


def _extract_file_paths_from_query(query: str) -> list[str]:
    """Extract file paths from query using smart pattern matching.

    Looks for:
    - Direct file paths: /path/to/file.py
    - File references: review ai_cli.py
    - File.py patterns: the hook.py
    - Extensions: .md, .py, .js, .ts, .json, .yaml, .yml

    Returns:
        List of detected file paths (empty if none found)
    """
    import re

    paths = []

    # Pattern 1: Windows/Unix absolute paths (e.g., C:/path/file.py or /home/user/file.py)
    abs_path_pattern = r"(?:[A-Za-z]:[\\/]|/)[\w\-./\\]+\.\w{2,4}"
    abs_matches = re.findall(abs_path_pattern, query)
    paths.extend(abs_matches)

    # Pattern 2: File references like "review ask_cli.py" or "investigate hook.py"
    # Look for word.ext patterns where ext is common code/doc extension
    file_ref_pattern = r"\b[\w-]+\.(?:py|js|ts|jsx|tsx|md|txt|json|yaml|yml|toml|cfg|ini|sh|bash)\b"
    file_matches = re.findall(file_ref_pattern, query)
    paths.extend(file_matches)

    # Pattern 3: Extensionless absolute paths that are directories
    # Matches paths like P:/packages/yt-is that have no file extension but exist as dirs
    dir_path_pattern = r"(?:[A-Za-z]:[/\\]|/)[/\w\-.]+"
    for match in re.findall(dir_path_pattern, query):
        # Skip if already captured by patterns 1 or 2 (has extension)
        if re.search(r"\.[\w]{2,4}$", match):
            continue
        p = Path(match)
        if not p.exists():
            p = Path.cwd() / match
        if p.exists() and p.is_dir():
            paths.append(match)

    # Resolve relative paths
    resolved_paths = []
    for path in paths:
        p = Path(path)
        if not p.exists():
            # Try current working directory
            p = Path.cwd() / path
        if p.exists() and (p.is_file() or p.is_dir()):
            resolved_paths.append(str(p))

    return list(set(resolved_paths))  # Dedupe


def _get_git_changed_files() -> list[str]:
    """Get list of changed files in git repository.

    Returns:
        List of changed file paths (empty if not a git repo or no changes)
    """
    try:
        import subprocess

        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=Path.cwd(),
        )
        if result.returncode == 0 and result.stdout.strip():
            files = []
            for line in result.stdout.strip().split("\n"):
                # git status --porcelain format: XY filename
                parts = line.split(maxsplit=1)
                if len(parts) == 2:
                    files.append(parts[1])
            return files
    except Exception:
        pass
    return []


def _smart_auto_context(query: str) -> str | None:
    """Automatically detect context from query and environment.

    Smart detection priority:
    1. File paths mentioned in query
    2. Git changed files (if in git repo)
    3. Session activity (WT_SESSION)

    Args:
        query: The user's query

    Returns:
        Context string or None if no context detected
    """
    # Priority 1: Extract file paths from query
    file_paths = _extract_file_paths_from_query(query)
    if file_paths:
        # Use the first (most relevant) file found
        context_path = file_paths[0]
        context = get_context(context_path, auto_context=False)
        if context:
            print(f"[Auto-detected file from query: {context_path}]", file=sys.stderr)
            return context

    # Priority 2: Git changed files
    # Skip for conceptual queries - they have no specific target file
    conceptual_keywords = [
        "what ideas", "how should", "should we", "could we", "ways to",
        "ideas for", "enhance", "improve", "design", "architect",
        "concept", "approach", "strategy", "thoughts on",
    ]
    is_conceptual = any(kw in query.lower() for kw in conceptual_keywords)
    if not is_conceptual:
        git_files = _get_git_changed_files()
        if git_files:
            # Use most recently modified file
            for file_path in git_files:
                p = Path(file_path)
                if p.exists() and p.is_file():
                    context = get_context(str(p), auto_context=False)
                    if context:
                        print(f"[Auto-detected git changed file: {file_path}]", file=sys.stderr)
                        return context

    # Priority 3: Session activity (already handled by WT_SESSION check below)
    return None


def _build_query_context(args: argparse.Namespace, query: str) -> tuple[str, str]:
    """Build the query with context from various sources.

    Priority:
    1. Explicit --context file
    2. Smart auto-detection from query (file paths, git changes, session)
    3. --auto-context flag
    4. Auto-detect from WT_SESSION
    5. Plain query (no context)

    Args:
        args: Parsed command-line arguments
        query: The original query string

    Returns:
        Tuple of (final_query, context_string)
    """
    # Start with explicit context or smart auto-detection
    if args.context:
        context = get_context(args.context, args.auto_context)
    elif not args.auto_context:
        # Try smart auto-detection before falling back to WT_SESSION
        context = _smart_auto_context(query)
    else:
        context = None

    # Check stdin FIRST before auto-context detection
    stdin_has_content = not sys.stdin.isatty()

    # Only auto-detect session context if: no explicit context AND no stdin content
    if not context and not args.context and not args.auto_context and not stdin_has_content:
        wt_session = os.environ.get("WT_SESSION")
        if wt_session:
            detected = detect_session_context(wt_session)
            if detected:
                context = detected
                print("[Auto-detected context from session activity]", file=sys.stderr)

    if context:
        # Enhanced prompt with clarification instruction and solo-dev constraints
        solo_dev_constraints = """

CONSTRAINTS (Solo Development Environment):
- Single developer - NO team assignments, code reviews, or collaborative workflows requiring multiple people
- Prefer SIMPLE solutions over enterprise patterns (JSON > databases, local > distributed)
- Pragmatic over comprehensive (ROI > risk-aversion, working > perfect)
- Local testing over CI infrastructure
- Avoid over-engineering for scalability (single user, low concurrency)
"""
        final_query = (
            "--- Context ---\n"
            + context
            + "\n---\n"
            + "Question: "
            + query
            + "\n\n"
            + "IMPORTANT: If the question is unclear about WHAT to investigate, ask for clarification. "
            + "Do not assume the most recent file in context is the target."
            + solo_dev_constraints
        )
        print(f"[Context loaded: {len(context)} characters]", file=sys.stderr)
    # Even without context, add solo-dev constraints for reviews
    elif any(
        word in query.lower() for word in ["review", "analyze", "audit", "gaps", "opportunities"]
    ):
        final_query = (
            query
            + """

CONSTRAINTS (Solo Development Environment):
- Single developer - NO team assignments, code reviews, or collaborative workflows requiring multiple people
- Prefer SIMPLE solutions over enterprise patterns (JSON > databases, local > distributed)
- Pragmatic over comprehensive (ROI > risk-aversion, working > perfect)
- Local testing over CI infrastructure
- Avoid over-engineering for scalability (single user, low concurrency)
"""
        )
    else:
        final_query = query

    return final_query, context or ""


def _create_tiered_reports(results: dict[str, Any]) -> None:
    """Create priority-based YAML reports with deduplication and aggregation.

    Reads individual CLI JSON files, extracts findings, deduplicates by content,
    aggregates sources/confidences/priorities, then groups by final priority.

    Creates priority-based YAML files:
      - critical.yaml: Critical priority findings (100KB max)
      - high.yaml: High priority findings (100KB max)
      - medium.yaml: Medium priority findings (100KB max)

    Args:
        results: The LLM results dictionary with CLI outputs
    """
    temp_dir = Path("P:/__csf/temp/cli_results")
    if not temp_dir.exists():
        return

    # Priority order (for determining highest priority)
    PRIORITY_ORDER = {"critical": 3, "high": 2, "medium": 1}
    min_confidence = 80
    max_size = 100 * 1024

    # Step 1: Extract ALL findings from all CLIs
    all_findings = []

    for cli_name, cli_data in results.items():
        if not isinstance(cli_data, dict):
            continue

        output = cli_data.get("output", "")
        if not output:
            continue

        try:
            cli_json = json.loads(output) if isinstance(output, str) else output
            findings = _extract_all_findings(cli_json, cli_name, min_confidence)
            all_findings.extend(findings)

        except (json.JSONDecodeError, TypeError):
            findings = _extract_text_findings_all(output, cli_name)
            all_findings.extend(findings)

    # Step 2: Deduplicate and aggregate findings
    aggregated = _deduplicate_findings(all_findings, PRIORITY_ORDER)

    # Step 3: Group by final priority
    by_priority = {"critical": [], "high": [], "medium": []}

    for item in aggregated:
        final_priority = item["final_priority"]
        by_priority[final_priority].append(item)

    # Step 4: Write YAML files
    for priority, items in by_priority.items():
        if not items:
            continue

        # Sort by agreement count (desc), then avg confidence (desc)
        items.sort(key=lambda x: (x["agreement_count"], x.get("avg_confidence", 0)), reverse=True)

        # Build YAML structure
        yaml_data = {
            "priority": priority,
            "min_confidence": f"{min_confidence}%",
            "count": len(items),
            "findings": items,
        }

        try:
            yaml_content = yaml.dump(
                yaml_data, sort_keys=False, default_flow_style=False, allow_unicode=True
            )

            if len(yaml_content.encode("utf-8")) <= max_size:
                report_file = temp_dir / f"{priority}.yaml"
                report_file.write_text(yaml_content, encoding="utf-8")
                print(f"[Report] Created {priority}.yaml: {len(items)} items", file=sys.stderr)
            else:
                # Truncate to fit
                print(
                    f"[Report] {priority}.yaml would exceed size limit, truncating", file=sys.stderr
                )
                while len(items) > 0:
                    items.pop()
                    yaml_data["count"] = len(items)
                    yaml_data["findings"] = items
                    yaml_data["_truncated"] = True
                    yaml_content = yaml.dump(
                        yaml_data, sort_keys=False, default_flow_style=False, allow_unicode=True
                    )
                    if len(yaml_content.encode("utf-8")) <= max_size:
                        break
                report_file = temp_dir / f"{priority}.yaml"
                report_file.write_text(yaml_content, encoding="utf-8")
                print(f"[Report] Truncated {priority}.yaml to {len(items)} items", file=sys.stderr)

        except Exception as e:
            print(f"[Report] Error creating {priority}.yaml: {e}", file=sys.stderr)


# ============================================================================
# Semantic Finding Deduplication (from llm-api)
# ============================================================================


def _extract_finding_signature(content: str) -> str:
    """Extract a unique signature from a finding for semantic deduplication.

    A finding signature is based on:
    - File paths mentioned (e.g., "src/main.py") - line numbers stripped for normalization
    - Issue type keywords (e.g., "SQL injection", "null pointer")
    - Function/class names if mentioned (excludes common words)

    Returns a normalized signature string for comparison.
    """
    import hashlib
    import re

    # Extract file paths and strip line numbers for normalization
    # Pattern: file.py or file.py:123 -> both become "file.py"
    file_patterns = re.findall(
        r"[\w/]+\.(?:py|js|ts|java|go|rs|cpp|c|h|md|yaml|yml|json|txt)", content
    )
    files = sorted(set(file_patterns))

    # Extract issue type keywords
    # Note: Generic terms like "vulnerability", "bug", "error", "warning" are excluded
    # because they add no specificity - "SQL injection" is specific, "SQL injection vulnerability" is not
    issue_keywords = [
        "sql injection",
        "xss",
        "csrf",
        "buffer overflow",
        "null pointer",
        "memory leak",
        "race condition",
        "deadlock",
        "infinite loop",
        "type error",
        "value error",
        "index error",
        "key error",
        "missing import",
        "unused variable",
        "undefined variable",
    ]

    content_lower = content.lower()
    found_issues = sorted({kw for kw in issue_keywords if kw in content_lower})

    # Extract function/class names (common patterns: def foo, class Bar, etc.)
    # Exclude common English words to avoid false matches
    code_patterns = re.findall(r"(?:def|class|function|interface)\s+(\w+)", content)
    common_words = {
        "at",
        "in",
        "on",
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
    }
    code_refs = sorted(
        {ref for ref in code_patterns if ref.lower() not in common_words and len(ref) > 2}
    )

    # Build signature
    signature_parts = []
    if files:
        signature_parts.append(f"files:{','.join(files[:3])}")  # Limit to 3 files
    if found_issues:
        signature_parts.append(f"issues:{','.join(found_issues[:2])}")  # Limit to 2 issues
    if code_refs:
        signature_parts.append(f"refs:{','.join(code_refs[:2])}")  # Limit to 2 refs

    if not signature_parts:
        # Fallback: use first 100 chars of content hashed
        return hashlib.md5(content[:100].encode()).hexdigest()[:16]

    return "|".join(signature_parts)


def _deduplicate_findings_cli(all_findings: list[dict]) -> tuple[list[dict], dict]:
    """Deduplicate findings across CLIs using semantic signatures.

    Args:
        all_findings: List of finding dicts with 'source', 'finding'/'content', 'confidence'

    Returns:
        Tuple of (deduplicated_findings, dedup_metrics)
    """
    if not all_findings:
        return [], {
            "total_findings": 0,
            "unique_findings": 0,
            "duplicates_found": 0,
            "dedup_ratio": 0.0,
        }

    seen_signatures = {}
    unique_findings = []

    for finding in all_findings:
        # Get content from either 'finding' or 'content' field
        content = finding.get("finding") or finding.get("content", "")
        signature = _extract_finding_signature(content)

        if signature not in seen_signatures:
            # First occurrence of this finding
            seen_signatures[signature] = finding
            finding["signature"] = signature
            finding["is_duplicate"] = False
            unique_findings.append(finding)
        else:
            # Duplicate finding - mark it but track which CLI also found it
            finding["signature"] = signature
            finding["is_duplicate"] = True
            finding["duplicate_of"] = seen_signatures[signature].get("source", "unknown")
            unique_findings.append(finding)

    # Separate truly unique from duplicates
    truly_unique = [f for f in unique_findings if not f["is_duplicate"]]
    duplicates = [f for f in unique_findings if f["is_duplicate"]]

    metrics = {
        "total_findings": len(all_findings),
        "unique_findings": len(truly_unique),
        "duplicates_found": len(duplicates),
        "dedup_ratio": len(truly_unique) / len(all_findings) if all_findings else 0.0,
        "signatures_seen": len(seen_signatures),
    }

    return unique_findings, metrics


# Original fuzzy deduplication (kept for compatibility)
def _deduplicate_findings(findings: list[dict], priority_order: dict[str, int]) -> list[dict]:
    """Deduplicate findings by fuzzy matching and aggregate sources.

    Args:
        findings: List of finding dicts with finding, source, priority, confidence
        priority_order: Dict mapping priority name to rank (higher = more important)

    Returns:
        List of aggregated finding dicts with deduplication applied
    """
    import difflib

    if not findings:
        return []

    # Sort findings by priority rank (highest first) to establish canonical order
    findings.sort(
        key=lambda x: (
            priority_order.get(x.get("priority", "medium"), 0),
            x.get("confidence", 0) if isinstance(x.get("confidence"), (int, float)) else 0,
        ),
        reverse=True,
    )

    aggregated = []
    finder = difflib.SequenceMatcher()

    for finding in findings:
        finding_text = finding.get("finding", "")
        if not finding_text:
            continue

        # Try to match with existing aggregated findings
        matched = False

        for agg in aggregated:
            # Use fuzzy matching to detect duplicates
            finder.set_seqs(finding_text.lower(), agg["finding"].lower())
            ratio = finder.ratio()

            if ratio >= 0.7:  # 70% similarity threshold
                # Aggregate: add source, confidence, priority vote
                if finding["source"] not in agg["sources"]:
                    agg["sources"].append(finding["source"])
                    agg["agreement_count"] += 1

                # Track confidence scores
                conf = finding.get("confidence")
                if isinstance(conf, (int, float)):
                    agg["confidence_scores"].append(conf)

                # Track priority votes
                priority = finding.get("priority", "medium")
                agg["priority_votes"][priority] = agg["priority_votes"].get(priority, 0) + 1

                matched = True
                break

        if not matched:
            # New finding - initialize aggregation structure
            conf = finding.get("confidence")
            priority = finding.get("priority", "medium")

            aggregated.append(
                {
                    "finding": finding_text,
                    "sources": [finding["source"]],
                    "agreement_count": 1,
                    "confidence_scores": [conf] if isinstance(conf, (int, float)) else [],
                    "priority_votes": {priority: 1},
                    "final_priority": priority,
                }
            )

    # Compute final fields
    for agg in aggregated:
        # Average confidence (only for numeric values)
        numeric_confs = [c for c in agg["confidence_scores"] if isinstance(c, (int, float))]
        if numeric_confs:
            agg["avg_confidence"] = round(sum(numeric_confs) / len(numeric_confs), 1)
        else:
            agg["avg_confidence"] = "unknown"

        # Final priority: highest priority voted
        # Priority order: critical > high > medium
        for priority in ["critical", "high", "medium"]:
            if agg["priority_votes"].get(priority, 0) > 0:
                agg["final_priority"] = priority
                break

        # Clean up internal tracking
        del agg["priority_votes"]

    return aggregated


def _extract_all_findings(cli_data: Any, cli_name: str, min_confidence: int) -> list[dict]:
    """Extract ALL findings with priority and confidence from JSON output.

    Args:
        cli_data: Parsed JSON output from CLI
        cli_name: Name of the CLI source
        min_confidence: Minimum confidence threshold (0-100)

    Returns:
        List of finding dicts with priority and confidence
    """
    findings = []

    def extract_recursive(obj: Any, path: str = "") -> None:
        """Recursively search for priority-scored items."""
        if isinstance(obj, dict):
            # Check for priority field (various naming conventions)
            priority = (
                obj.get("priority") or obj.get("impact") or obj.get("severity") or obj.get("level")
            )

            # Normalize priority string
            priority_norm = None
            if isinstance(priority, str):
                priority_norm = priority.lower().strip()
                # Map common variations to standard priorities
                if priority_norm in ("critical", "crit", "urgent", "emergency"):
                    priority_norm = "critical"
                elif priority_norm in ("high", "important", "major"):
                    priority_norm = "high"
                elif priority_norm in ("medium", "moderate", "normal"):
                    priority_norm = "medium"

            # Only process if has a priority (findings without priority are skipped)
            if priority_norm:
                # Get confidence score
                confidence = obj.get("confidence") or obj.get("score")

                # Critical items: preserve regardless of confidence (safety valve)
                # Other priorities: require 80%+ confidence
                try:
                    conf_val = float(confidence) if confidence is not None else min_confidence
                    meets_threshold = (
                        priority_norm == "critical"  # Always include critical
                        or conf_val >= min_confidence
                    )

                    if meets_threshold:
                        findings.append(
                            {
                                "source": cli_name,
                                "priority": priority_norm,
                                "confidence": conf_val,
                                "path": path,
                                "finding": obj.get("text")
                                or obj.get("content")
                                or obj.get("description")
                                or str(obj),
                            }
                        )
                except (ValueError, TypeError):
                    # No valid confidence, include only if critical
                    if priority_norm == "critical":
                        findings.append(
                            {
                                "source": cli_name,
                                "priority": priority_norm,
                                "confidence": "unknown",
                                "path": path,
                                "finding": obj.get("text") or obj.get("content") or str(obj),
                            }
                        )

            # Recurse into nested structures
            for key, value in obj.items():
                extract_recursive(value, f"{path}/{key}" if path else key)

        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                extract_recursive(item, f"{path}[{i}]")

    extract_recursive(cli_data)
    return findings


def _extract_text_findings_all(output: str, cli_name: str) -> list[dict]:
    """Extract ALL findings with priority from text output when JSON parsing fails.

    Uses regex to find priority markers in text (Critical:, High:, Medium:, etc.).

    Args:
        output: Raw text output from CLI
        cli_name: Name of the CLI source

    Returns:
        List of finding dicts with priority
    """
    findings = []

    # Priority markers to search for (case-insensitive)
    # Supports: "## Critical Issues", "Critical:", "- **Critical:**", etc.
    priority_patterns = {
        "critical": r"##\s*Critical\s*(?:Issues|\(must fix\)|:)|^\s*[-•*]\s*\*\*Critical\s*(?:Issues?|:)?\*\*|^\s*(?:CRITICAL|Critical|crit:|critical:)\s*:?",
        "high": r"##\s*(?:High|Important)\s*(?:Issues?\s*\(?:should fix\)|:)|^\s*[-•*]\s*\*\*(?:High|Important)\s*:?\*\*|^\s*(?:HIGH|High|high:)\s*:?",
        "medium": r"##\s*(?:Medium|Suggestions?|Nice to have)\s*:|^\s*[-•*]\s*\*\*(?:Medium|Suggestions?|Nice to have)\s*:?\*\*|^\s*(?:MEDIUM|Medium|medium:)\s*:?",
    }

    import re

    # Track current priority while parsing
    current_priority = None
    priority_section_pattern = r"^##\s*(Critical|High|Important|Medium|Suggestions?|Nice to holy)"

    for line in output.split("\n"):
        # Check for section headers
        section_match = re.search(priority_section_pattern, line, re.IGNORECASE)
        if section_match:
            section_text = section_match.group(1).lower()
            if "critical" in section_text:
                current_priority = "critical"
            elif section_text in ("high", "important"):
                current_priority = "high"
            else:
                current_priority = "medium"
            continue

        # Check for inline priority markers in bullet points
        for priority, pattern in priority_patterns.items():
            if re.search(pattern, line, re.IGNORECASE):
                current_priority = priority
                break

        # Extract finding from bullet points
        bullet_match = re.match(r"^\s*[-•*]\s*\*?\*?(.+?)\*?\*?\s*:\s*(.+)", line)
        if bullet_match and current_priority:
            title = bullet_match.group(1).strip()
            content = bullet_match.group(2).strip()

            # Clean up markdown formatting
            finding_text = re.sub(r"\*\*([^*]+)\*\*", r"\1", f"{title}: {content}")
            finding_text = re.sub(r"`([^`]+)`", r"\1", finding_text)

            if len(finding_text) >= 20:  # Minimum content threshold
                findings.append(
                    {
                        "source": cli_name,
                        "priority": current_priority,
                        "confidence": 85
                        if current_priority == "critical"
                        else 70,  # Estimate confidence from priority
                        "path": "text",
                        "finding": finding_text,
                    }
                )

    return findings if findings else []


def _extract_from_full_output(cli_name: str, output: str) -> list[dict]:
    """Fallback: Treat entire output as a single finding (UNUSED - skipped).

    Findings without explicit priority are now excluded to avoid
    misclassifying unstructured text as medium-priority findings.

    Args:
        cli_name: Name of the CLI source
        output: Full text output

    Returns:
        Empty list (findings without priority are skipped)
    """
    return []


def _write_output(results: dict[str, Any], args: argparse.Namespace) -> None:
    """Write output in the selected format.

    Handles JSON output with file saving, or text output with formatters.

    Args:
        results: The LLM results dictionary
        args: Parsed command-line arguments with output format flags
    """
    # Report CLI status prominently
    successful = [name for name, result in results.items() if not result.get("error")]
    failed = [name for name, result in results.items() if result.get("error")]

    print("=" * 50, file=sys.stderr)
    print("CLI STATUS:", file=sys.stderr)
    print(
        f"  ✅ Success ({len(successful)}): {', '.join(successful) if successful else 'None'}",
        file=sys.stderr,
    )
    print(
        f"  ❌ Failed ({len(failed)}): {', '.join(failed) if failed else 'None'}", file=sys.stderr
    )
    print("=" * 50, file=sys.stderr)

    # Show error details for failed CLIs
    if failed:
        print("Error Details:", file=sys.stderr)
        for name in failed:
            error = results[name].get("error", "Unknown error")
            print(f"  {name}: {error[:100]}...", file=sys.stderr)
        print("", file=sys.stderr)

    # JSON output - individual CLI files saved by parallel_llm.py
    if args.output_format == "json":
        output_json = json.dumps(results, indent=2)
        print(output_json)

        # Persist the combined JSON when requested.
        # The filename always gets a datetime suffix so repeated runs do not collide.
        output_file = getattr(args, "output_file", None)
        if output_file is None:
            output_file = "output.json"

        output_path = Path(_add_datetime_suffix(output_file))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output_json + "\n", encoding="utf-8")

        # Create tiered YAML reports from individual CLI results
        _create_tiered_reports(results)
    # Text output - select formatter based on flags
    elif getattr(args, "summary", False):
        print(format_summary(results))
    elif getattr(args, "aggregate", False):
        print(format_aggregate(results))
    elif getattr(args, "quality_weighted", False):
        print(format_quality_weighted(results))
    elif getattr(args, "complete", False):
        print(format_complete(results))
    elif getattr(args, "diff", False):
        print(format_diff(results))
    else:
        print(format_results(results))


async def _run_domain_query(
    domain: str, query: str, context: str | None, refresh_benchmarks: bool = False
) -> dict[str, Any]:
    """Run query using dynamic model router for domain-based model comparison.

    Runs top 2 models in parallel:
    - Uses native CLI tools when available (qwen, gemini, codex)
    - Falls back to opencode for models without native CLIs

    Args:
        domain: Domain string (e.g., "code_generation", "code_review")
        query: Query/question for the LLM
        context: Optional context string to prepend to query
        refresh_benchmarks: Force refresh benchmark data from internet

    Returns:
        Dict with comparison results from top 2 models
    """
    if not _DYNAMIC_ROUTER_AVAILABLE:
        return {
            "domain": domain,
            "error": "Dynamic router not available (CSF NIP not found)",
            "results": [],
        }

    # Map domain string to Domain enum
    domain_map = {
        "code_generation": Domain.CODE_GENERATION,
        "code_review": Domain.CODE_REVIEW,
        "architecture": Domain.ARCHITECTURE,
        "testing": Domain.TESTING,
        "documentation": Domain.DOCUMENTATION,
        "debugging": Domain.DEBUGGING,
    }

    domain_enum = domain_map.get(domain)
    if not domain_enum:
        return {
            "domain": domain,
            "error": f"Unknown domain: {domain}",
            "results": [],
        }

    # Load API keys for router
    api_manager = APIKeyManager()
    groq_key = api_manager.get_provider("groq")
    chutes_key = api_manager.get_provider("chutes")
    openrouter_key = api_manager.get_provider("openrouter")

    import time

    start_time = time.time()

    try:
        # Get router with current provider data
        router = await get_router(
            groq_key.api_key if groq_key else None,
            chutes_key.api_key if chutes_key else None,
            openrouter_key.api_key if openrouter_key else None,
            refresh_benchmarks=refresh_benchmarks,
        )

        # Get top 2 models for domain
        recommendation = router.get_recommendation(domain_enum)
        if not recommendation:
            return {
                "domain": domain,
                "error": f"No models available for domain: {domain}",
                "results": [],
            }

        # Display model selection with both benchmark and local data
        router.display_model_selection_with_both_sources(domain_enum, query)

        # Ask for user confirmation
        print()
        response = input("Continue with recommended models? (Y/n): ").strip().lower()
        if response and response != "y":
            return {
                "domain": domain,
                "error": "User cancelled",
                "results": [],
                "cancelled": True,
            }

        print()  # Spacing before execution output

        # Extract models (use primary and fallback)
        models_to_run = []
        if recommendation.primary:
            models_to_run.append(recommendation.primary.info)
        if recommendation.fallback:
            models_to_run.append(recommendation.fallback.info)

        if len(models_to_run) == 0:
            return {
                "domain": domain,
                "error": f"No qualified models found for domain: {domain}",
                "results": [],
            }

        # Limit to 2 models for efficiency
        models_to_run = models_to_run[:2]

        # Build full query with context
        full_query = f"{context}\n\n{query}" if context else query

        # Import native CLI detection
        # Run models in parallel (native CLI or opencode)
        import asyncio

        from src.csf.llm_providers.dynamic_model_router import _has_native_cli

        async def run_model_with_native_cli_or_opencode(model_info: ModelInfo) -> dict[str, Any]:
            """Run model using native CLI if available, otherwise opencode."""
            # Check if model has a native CLI tool
            native_cli = _has_native_cli(model_info)

            model_start = time.time()

            if native_cli:
                # Use native CLI tool (qwen, gemini, codex)
                cmd = [native_cli]

                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                try:
                    stdout, stderr = await proc.communicate(
                        input=full_query.encode(),
                        timeout=120,  # 2 minute timeout
                    )

                    latency_ms = (time.time() - model_start) * 1000

                    if proc.returncode != 0:
                        return {
                            "model": {
                                "id": model_info.id,
                                "name": model_info.name,
                                "provider": model_info.provider,
                                "cli": native_cli,
                            },
                            "error": f"Exit code {proc.returncode}: {stderr.decode() if stderr else 'Unknown error'}",
                            "output": None,
                            "latency_ms": latency_ms,
                        }

                    # Native CLI output is plain text
                    return {
                        "model": {
                            "id": model_info.id,
                            "name": model_info.name,
                            "provider": model_info.provider,
                            "cli": native_cli,
                        },
                        "output": stdout.decode(),
                        "error": None,
                        "latency_ms": latency_ms,
                    }

                except TimeoutError:
                    proc.kill()
                    return {
                        "model": {
                            "id": model_info.id,
                            "name": model_info.name,
                            "provider": model_info.provider,
                            "cli": native_cli,
                        },
                        "error": "Timeout after 120 seconds",
                        "output": None,
                        "latency_ms": 120000,
                    }
            else:
                # Use opencode for models without native CLI
                npm_root = Path.home() / "AppData" / "Roaming" / "npm" / "node_modules"
                opencode_path = npm_root / "opencode-ai" / "bin" / "opencode"

                cmd = [
                    "node",
                    str(opencode_path),
                    "run",
                    "-m",
                    model_info.id,
                ]

                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                try:
                    stdout, stderr = await proc.communicate(
                        input=full_query.encode(),
                        timeout=120,  # 2 minute timeout
                    )

                    latency_ms = (time.time() - model_start) * 1000

                    if proc.returncode != 0:
                        return {
                            "model": {
                                "id": model_info.id,
                                "name": model_info.name,
                                "provider": model_info.provider,
                                "cli": "opencode",
                            },
                            "error": f"Exit code {proc.returncode}: {stderr.decode() if stderr else 'Unknown error'}",
                            "output": None,
                            "latency_ms": latency_ms,
                        }

                    # Parse opencode streaming JSON output
                    output = _parse_opencode_streaming_json(stdout.decode())
                    return {
                        "model": {
                            "id": model_info.id,
                            "name": model_info.name,
                            "provider": model_info.provider,
                            "cli": "opencode",
                        },
                        "output": output,
                        "error": None,
                        "latency_ms": latency_ms,
                    }

                except TimeoutError:
                    proc.kill()
                    return {
                        "model": {
                            "id": model_info.id,
                            "name": model_info.name,
                            "provider": model_info.provider,
                            "cli": "opencode",
                        },
                        "error": "Timeout after 120 seconds",
                        "output": None,
                        "latency_ms": 120000,
                    }

        # Run models in parallel
        tasks = [run_model_with_native_cli_or_opencode(model) for model in models_to_run]
        results_raw = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        results = []
        for result in results_raw:
            if isinstance(result, Exception):
                results.append(
                    {
                        "model": {"error": f"Exception: {str(result)}"},
                        "output": None,
                    }
                )
            else:
                results.append(result)

        total_latency_ms = (time.time() - start_time) * 1000

        return {
            "domain": domain,
            "results": results,
            "total_latency_ms": total_latency_ms,
        }

    except Exception as e:
        total_latency_ms = (time.time() - start_time) * 1000
        return {
            "domain": domain,
            "error": str(e),
            "results": [],
            "total_latency_ms": total_latency_ms,
        }


def main():
    """Main entry point for ai-cli CLI.

    Orchestrates argument parsing, context building, LLM execution,
    and output formatting.
    """
    parser = argparse.ArgumentParser(
        description="Run multiple LLM CLIs in parallel. Full docs: llm_cli.md",
        epilog="""Examples:
  # Basic query (auto-detects session context if available)
  llm_cli.py "explain recursion"

  # Pass file as context (RECOMMENDED for file analysis)
  llm_cli.py "Review this plan" --context path/to/file.md

  # Auto-include latest session history
  llm_cli.py "continue" --auto-context

  # Run specific LLM only
  llm_cli.py "debug this" --qwen-only

CONTEXT HANDLING:
  --context FILE     Read and embed file content (recommended for file analysis)
  --auto-context      Auto-load latest session history
  (no flag)          Auto-detect from WT_SESSION environment variable

  WARNING: Piped stdin input is IGNORED when auto-context is detected.
           Use --context flag explicitly to pass file content.

Session IDs: ls ~/.claude/projects/P--/*.jsonl""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("query", help="Question or task for the LLMs")
    parser.add_argument("--qwen-only", action="store_true", help="Run only qwen-cli")
    parser.add_argument("--gemini-only", action="store_true", help="Run only gemini-cli")
    parser.add_argument("--codex-only", action="store_true", help="Run only codex-cli")
    parser.add_argument("--opencode-only", action="store_true", help="Run only opencode-cli")
    parser.add_argument("--pi-m27-only", action="store_true", help="Run only pi with minimax/MiniMax-M2.7")
    parser.add_argument("--pi-glm-only", action="store_true", help="Run only pi with zai/glm-5.1")
    parser.add_argument("--copilot-only", action="store_true", help="Run only GitHub Copilot CLI")
    parser.add_argument(
        "--glm-flash-only", action="store_true", help="Run only GLM-4.7-Flash (via API)"
    )
    parser.add_argument(
        "--route",
        action="store_true",
        help="Use rule-based routing (from llm-route) to select CLI based on task keywords",
    )
    parser.add_argument(
        "--doc-review",
        action="store_true",
        help="Use document review prompt (from llm-doc_review) - prepends 'Please review. Does it make sense? Any gaps/opportunities/questions?'",
    )
    parser.add_argument(
        "--opencode-model",
        type=str,
        nargs="*",
        default=[],
        help=f"OpenCode model(s) (default: {DEFAULT_OPENCODE_MODEL}). Aliases: kimi, minimax. Multiple models run in parallel.",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show parallel execution progress"
    )
    parser.add_argument(
        "-bash",
        "--parallel-bash",
        action="store_true",
        help="Spawn separate Bash tools (shows 4 distinct bash invocations)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=None,
        help="Max wait time in seconds (default: auto-calculate based on context size)",
    )
    parser.add_argument(
        "--output-format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--output-file",
        type=str,
        default=None,
        help="Save JSON output to file (auto-generated if not specified with --output-format json)",
    )
    parser.add_argument(
        "--summary", action="store_true", help="Show brief summary (key answers only)"
    )
    parser.add_argument("--aggregate", action="store_true", help="Show aggregated/consensus view")
    parser.add_argument(
        "--quality-weighted",
        action="store_true",
        help="Quality-weighted output with consensus analysis and evidence validation",
    )
    parser.add_argument("--complete", action="store_true", help="Show complete raw outputs")
    parser.add_argument(
        "--diff", action="store_true", help="Show differences between CLI responses"
    )
    parser.add_argument(
        "--quality-gate",
        action="store_true",
        help="Apply 4-Layer Filter System Layer 4 (Quality Gate) - filters findings by confidence >=80%%",
    )
    parser.add_argument(
        "--domain",
        choices=[
            "code_generation",
            "code_review",
            "architecture",
            "testing",
            "documentation",
            "debugging",
        ],
        help="Use domain-based routing with dynamic model router (quality-first)",
    )
    parser.add_argument(
        "--refresh-benchmarks",
        action="store_true",
        help="Force refresh benchmark data from internet before domain routing",
    )
    parser.add_argument(
        "--context",
        type=str,
        default=None,
        help="Context: file path to read and embed (RECOMMENDED for file analysis)",
    )
    parser.add_argument(
        "--auto-context", action="store_true", help="Auto-include latest session history"
    )
    parser.add_argument(
        "--target",
        type=str,
        default=None,
        help="Target: file path to investigate (filters session context by relevance)",
    )
    parser.add_argument(
        "--hide-prompt",
        action="store_true",
        help="Don't print the enhanced prompt before sending to CLIs (suppresses default behavior)",
    )
    parser.add_argument(
        "--no-critic",
        action="store_true",
        help="Skip the post-run ai-cli critic subagent",
    )
    parser.add_argument(
        "--prompt-toolkit",
        action="store_true",
        help="Use prompting-toolkit AutomaticEnhancementSystem instead of built-in prompt templates",
    )

    args = parser.parse_args()

    # Simple logic tree: "config" query just shows saved config and exits
    if args.query.strip().lower() == "config":
        saved = _load_ai_cli_config()
        default_clis = []
        aux_clis = []
        if saved:
            default_clis = saved.get("default", {}).get("clis", [])
            aux_clis = saved.get("aux", {}).get("clis", [])

        if default_clis or aux_clis:
            print("Active CLIs:")
            for i, (group_name, group_data) in enumerate(
                [("Default", {"clis": default_clis}), ("Aux / Enh", {"clis": aux_clis})]
            ):
                clis = group_data.get("clis", [])
                if not clis:
                    continue
                if i > 0:
                    print()
                print(f"  {group_name}:")
                for idx, cli in enumerate(clis):
                    is_last_cli = (idx == len(clis) - 1)
                    name = cli.get("name", "")
                    model = cli.get("model", "")
                    failover = cli.get("failover", "")

                    top_connector = "└── " if is_last_cli else "├── "

                    print(f"    {top_connector}{name}")

                    if model:
                        # Model is a child of CLI
                        model_is_last = not failover
                        model_connector = "└── " if model_is_last else "├── "
                        if is_last_cli and not failover:
                            prefix = "        "
                        else:
                            prefix = "    │   "
                        print(f"{prefix}{model_connector}{model}")

                        if failover:
                            failovers = [f.strip() for f in failover.split(",")]
                            for fi, fb in enumerate(failovers):
                                is_last_fb = (fi == len(failovers) - 1)
                                fb_connector = "└── " if is_last_fb else "├── "
                                fb_prefix = "    │   │   "
                                print(f"{fb_prefix}{fb_connector}{fb}")
        else:
            print("No saved configuration found")
        return

    # Classify task type for intelligent prompt engineering and performance tracking
    classification = classify_task(args.query)
    if classification.confidence > 0.0:
        print(
            f"[Task classified: {classification.task_type.value} (confidence: {classification.confidence:.0%})]",
            file=sys.stderr,
        )

    # Auto-detect review queries and default to complete output
    _has_format_flag = (
        getattr(args, "summary", False)
        or getattr(args, "aggregate", False)
        or getattr(args, "complete", False)
        or getattr(args, "diff", False)
    )
    if _detect_review_query(args.query) and not _has_format_flag and args.output_format == "text":
        args.complete = True
        print(
            "[Review query detected - showing complete outputs. Use --summary or --aggregate for brief views.]",
            file=sys.stderr,
        )

    # Build query with context and task-specific prompt
    query, context = _build_query_context(args, args.query)

    # Apply task-specific prompt engineering for better LLM responses
    if getattr(args, "prompt_toolkit", False):
        # Use prompting-toolkit AutomaticEnhancementSystem
        try:
            import sys as _sys_local

            sys.path.insert(0, "P:/packages/prompting-toolkit/packages/framework/src")
            from prompting_framework.automatic_enhancement_system import (
                AutomaticEnhancementSystem,
            )

            if _PROMPT_TOOLKIT_SYSTEM is None:
                _PROMPT_TOOLKIT_SYSTEM = AutomaticEnhancementSystem(
                    max_enhancement_time=2.0,
                    min_quality_threshold=0.5,
                    enable_parallel_processing=True,
                    cache_decisions=True,
                )
            result = asyncio.run(
                _PROMPT_TOOLKIT_SYSTEM.apply_automatic_enhancement(query, context=context)
            )
            enhanced_query = result.enhanced_query
            if enhanced_query != query:
                query = enhanced_query
                frameworks = [f.value for f in result.applied_frameworks]
                if frameworks:
                    print(
                        f"[Applied prompting-toolkit: {frameworks}] "
                        f"+{result.improvement_percentage:.0f}% quality, "
                        f"{result.processing_time:.2f}s",
                        file=_sys_local.stderr,
                    )
                # else: enhancement was skipped silently, no log needed
        except (ImportError, AttributeError, asyncio.RuntimeError) as e:
            print(f"[prompting-toolkit unavailable: {e}], using built-in templates", file=_sys_local.stderr)
            # Override PLANNING -> BRAINSTORM when context is empty and query is conceptual
            # Conceptual queries without files are brainstorm tasks, not planning tasks
            if not context and classification.task_type == TaskType.PLANNING:
                conceptual_starters = (
                    "what ideas", "how should", "should we", "could we", "ways to",
                    "ideas for", "how could", "what's the best", "how can we",
                )
                query_lower = args.query.lower().strip()
                if any(query_lower.startswith(s) for s in conceptual_starters):
                    classification.task_type = TaskType.BRAINSTORM
                    print(f"[Conceptual query without context - overriding to brainstorm]", file=sys.stderr)
            enhanced_query = build_prompt(query, classification.task_type, context)
            if enhanced_query != query:
                query = enhanced_query
                print(f"[Applied {classification.task_type.value} prompt template]", file=sys.stderr)
    else:
        # Override PLANNING -> BRAINSTORM when context is empty and query is conceptual
        # Conceptual queries without files are brainstorm tasks, not planning tasks
        if not context and classification.task_type == TaskType.PLANNING:
            conceptual_starters = (
                "what ideas", "how should", "should we", "could we", "ways to",
                "ideas for", "how could", "what's the best", "how can we",
            )
            query_lower = args.query.lower().strip()
            if any(query_lower.startswith(s) for s in conceptual_starters):
                classification.task_type = TaskType.BRAINSTORM
                print(f"[Conceptual query without context - overriding to brainstorm]", file=sys.stderr)
        enhanced_query = build_prompt(query, classification.task_type, context)
        if enhanced_query != query:
            query = enhanced_query
            print(f"[Applied {classification.task_type.value} prompt template]", file=sys.stderr)

    # Show the enhanced prompt by default (--hide-prompt to suppress)
    # Print to stderr and skip when JSON output is requested to avoid corrupting JSON stream
    if not getattr(args, "hide_prompt", False) and getattr(args, "output_format", None) != "json":
        print("\n=== ENHANCED PROMPT ===", file=sys.stderr)
        print(query, file=sys.stderr)
        print("=== END PROMPT ===\n", file=sys.stderr)

    # Auto-detect document review context (from llm-doc_review)
    doc_keywords = ["review", "critique", "evaluate", "assess", "feedback"]
    is_doc_context = context and any(
        context.endswith(ext) for ext in [".md", ".txt", ".rst", ".doc", ".docx"]
    )
    is_doc_query = any(kw in query.lower() for kw in doc_keywords)

    # Enable doc-review mode if auto-detected OR explicitly requested
    if is_doc_query and is_doc_context:
        args.doc_review = True
        print("[Auto-detected document review context]", file=sys.stderr)

    # Apply document review prompt if requested (from llm-doc_review)
    if getattr(args, "doc_review", False):
        doc_review_prompt = (
            "Please review. Does it make sense? Any gaps/opportunities/questions?\n\n"
        )
        query = doc_review_prompt + query
        print("[Applied document review prompt template]", file=sys.stderr)

    # Calculate timeout based on context size if not specified
    if args.timeout is None:
        context_size_kb = len(context.encode("utf-8")) // 1024 if context else 0
        args.timeout = calc_timeout(context_size_kb)
        print(f"[Timeout: {args.timeout}s based on {context_size_kb}KB context]", file=sys.stderr)

    # Cleanup old CLI results (older than 7 days)
    _cleanup_old_cli_results(days_to_keep=7)

    # Track execution start time for performance logging
    import time

    execution_start_time = time.time()

    # Apply rule-based routing if requested (from llm-route)
    if getattr(args, "route", False):
        routed_flags = route_query_to_clis(query)
        # Set the appropriate CLI flag based on routing
        for flag in routed_flags:
            if flag == "--qwen-only":
                args.qwen_only = True
            elif flag == "--gemini-only":
                args.gemini_only = True
            elif flag == "--codex-only":
                args.codex_only = True
            elif flag == "--opencode-only":
                args.opencode_only = True

    # Parallel bash mode: print commands instead of executing
    if getattr(args, "parallel_bash", False):
        print("# Run these 4 bash commands in parallel:", file=sys.stderr)
        bash_commands = generate_parallel_bash_commands(
            query=query,
            qwen_only=args.qwen_only,
            gemini_only=args.gemini_only,
            codex_only=args.codex_only,
        )
        for cmd in bash_commands:
            print(cmd)
        return

    # Domain-based routing using dynamic model router
    if getattr(args, "domain", None) and _DYNAMIC_ROUTER_AVAILABLE:
        domain = args.domain
        print(f"[Using domain-based routing: {domain}]", file=sys.stderr)

        # Run domain query
        result = asyncio.run(
            _run_domain_query(domain, query, context, refresh_benchmarks=args.refresh_benchmarks)
        )

        # Format output
        if args.output_format == "json":
            print(json.dumps(result, indent=2))
        else:
            # Text output
            if result.get("error"):
                print(f"Error: {result['error']}", file=sys.stderr)
                return

            model_info = result.get("model_info", {})
            print(f"[Domain: {result['domain']}]", file=sys.stderr)
            print(f"[Model: {model_info.get('name', 'Unknown')}]", file=sys.stderr)
            print(f"[Provider: {model_info.get('provider', 'Unknown')}]", file=sys.stderr)
            print(f"[Model ID: {model_info.get('id', 'Unknown')}]", file=sys.stderr)
            print(f"[Latency: {result.get('latency_ms', 0):.0f}ms]", file=sys.stderr)
            print()
            print(result.get("response", ""))
        return

    # Load saved recipe if no opencode_models specified on command line
    opencode_models = args.opencode_model
    if not opencode_models:
        saved = _load_ai_cli_config()
        if saved:
            opencode_models = saved.get("opencode_models", [])

    # Context file for pi agents
    context_file = args.context

    # Show CLI/LLM preview before execution
    cli_preview = _get_cli_preview(
        qwen_only=args.qwen_only,
        gemini_only=args.gemini_only,
        codex_only=args.codex_only,
        opencode_only=args.opencode_only,
        glm_flash_only=args.glm_flash_only,
        opencode_models=opencode_models,
    )
    print(cli_preview, file=sys.stderr)

    # Execute parallel LLM queries
    results = run_parallel_llm(
        query=query,
        qwen_only=args.qwen_only,
        gemini_only=args.gemini_only,
        codex_only=args.codex_only,
        opencode_only=args.opencode_only,
        glm_flash_only=args.glm_flash_only,
        pi_m27_only=getattr(args, "pi_m27_only", False),
        pi_glm_only=getattr(args, "pi_glm_only", False),
        copilot_only=getattr(args, "copilot_only", False),
        timeout=args.timeout,
        output_format=args.output_format,
        verbose=getattr(args, "verbose", False),
        opencode_models=opencode_models,
        context_file=context_file,
    )

    # Log performance metrics for each CLI execution
    execution_duration = time.time() - execution_start_time
    for cli_name, cli_result in results.items():
        error = cli_result.get("error", "")
        output = cli_result.get("output", "")

        # Determine outcome
        if error:
            outcome = "error"
        elif not output.strip():
            outcome = "empty_output"
        else:
            outcome = "success"

        # Log execution
        _PERFORMANCE_LOGGER.log_execution(
            cli_name=cli_name,
            task_type=classification.task_type,
            query=args.query,
            duration_seconds=execution_duration,
            outcome=outcome,
            output_length=len(output),
            error_message=error if error else None,
        )

    # Apply 4-Layer Filter System Layer 4 (Quality Gate) if enabled
    # Filters findings by confidence ≥80% to reduce false positives
    quality_gate_enabled = _QUALITY_GATE_ENABLED or getattr(args, "quality_gate", False)
    if quality_gate_enabled:
        print("[Quality Gate Layer 4] Applying confidence filter (≥80%)...", file=sys.stderr)
        results, qg_summary = _apply_quality_gate_filter(results, query)
        print(
            f"[Quality Gate Layer 4] Filtered {qg_summary['input']} → {qg_summary['output']} findings",
            file=sys.stderr,
        )

    # Write output in selected format
    _write_output(results, args)

    # Save recipe config (CLIs used + opencode models) for future runs
    active_clis = list(results.keys())
    _save_ai_cli_config(active_clis, opencode_models)


if __name__ == "__main__":
    main()

```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\file_context.py
```python
#!/usr/bin/env python3
"""
File context handling for LLM CLI tools.

Implements patterns from Aider, Cursor, and other agentic CLI tools:
- Directory support (recursive file collection)
- Absolute path resolution
- Structured file content formatting
- Repo map generation for large file sets
"""

from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from pathlib import Path

# Default configuration
DEFAULT_MAX_FILES = 20  # Threshold for repo map generation
DEFAULT_MAX_FILE_SIZE = 100_000  # 100KB max per file


def resolve_path(path_str: str) -> Path:
    """Resolve a path string to an absolute Path.

    Args:
        path_str: Path string (can be relative or absolute)

    Returns:
        Resolved absolute Path object

    Examples:
        >>> resolve_path("src/file.py")
        Path('/project/src/file.py')
        >>> resolve_path("../config.yaml")
        Path('/project/config.yaml')
    """
    path = Path(path_str)

    # If relative, resolve from current working directory
    if not path.is_absolute():
        path = Path.cwd() / path

    # Resolve to absolute path (eliminates symlinks, .., .)
    return path.resolve()


def collect_files_from_paths(
    paths: list[str],
    extensions: list[str] | None = None,
    max_files: int = DEFAULT_MAX_FILES,
) -> list[Path]:
    """Collect files from a list of paths (files or directories).

    Args:
        paths: List of file/directory path strings
        extensions: Optional file extension filter (e.g., ['.py', '.ts'])
        max_files: Maximum files to collect (for token budgeting)

    Returns:
        List of absolute Path objects

    Examples:
        >>> collect_files_from_paths(['src/'], extensions=['.py'])
        [Path('/project/src/main.py'), Path('/project/src/utils.py')]
        >>> collect_files_from_paths(['README.md'])
        [Path('/project/README.md')]
    """
    collected = []

    for path_str in paths:
        path = resolve_path(path_str)

        if not path.exists():
            print(f"[Warning: Path not found: {path_str}]", file=sys.stderr)
            continue

        if path.is_file():
            collected.append(path)
        elif path.is_dir():
            # Recursively collect files from directory
            for item in _iter_files_recursive(path, extensions):
                collected.append(item)
                if len(collected) >= max_files:
                    print(
                        f"[Warning: Reached max files ({max_files}), stopping collection]",
                        file=sys.stderr,
                    )
                    break

        if len(collected) >= max_files:
            break

    return collected


def _iter_files_recursive(
    directory: Path,
    extensions: list[str] | None = None,
) -> Iterator[Path]:
    """Iterate over files in a directory recursively.

    Args:
        directory: Directory path to scan
        extensions: Optional file extension filter

    Yields:
        Path objects for each file
    """
    for root, dirs, files in os.walk(directory):
        root_path = Path(root)

        # Skip common ignore directories
        dirs[:] = [
            d
            for d in dirs
            if d
            not in {
                "__pycache__",
                "node_modules",
                ".git",
                ".venv",
                "venv",
                "env",
                ".env",
                "dist",
                "build",
                ".tox",
                "mypy_cache",
                ".pytest_cache",
                "htmlcov",
            }
        ]

        for filename in files:
            file_path = root_path / filename

            # Skip hidden files
            if filename.startswith("."):
                continue

            # Apply extension filter if specified
            if extensions:
                if not any(file_path.suffix == ext for ext in extensions):
                    continue

            yield file_path


def read_file_content_safe(
    file_path: Path,
    max_size: int = DEFAULT_MAX_FILE_SIZE,
) -> str | None:
    """Read file content safely with size limit.

    Args:
        file_path: Path to file
        max_size: Maximum file size in bytes

    Returns:
        File content as string, or None if error/too large
    """
    try:
        if file_path.stat().st_size > max_size:
            print(
                f"[Warning: File too large ({file_path.stat().st_size} bytes), skipping: {file_path.name}]",
                file=sys.stderr,
            )
            return None

        return file_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(
            f"[Warning: Error reading file {file_path.name}: {e}]",
            file=sys.stderr,
        )
        return None


def create_repo_map(files: list[Path]) -> str:
    """Create a high-level repository map (like Aider's repo map).

    Provides a structural overview without full file contents.

    Args:
        files: List of file paths

    Returns:
        Formatted repo map string
    """
    lines = ["# Repository Map", ""]

    # Group by directory
    by_dir: dict[str, list[Path]] = {}
    for file in files:
        dir_name = str(file.parent) if file.parent != Path.cwd() else "."
        if dir_name not in by_dir:
            by_dir[dir_name] = []
        by_dir[dir_name].append(file)

    # List files by directory
    for dir_name in sorted(by_dir.keys()):
        lines.append(f"## {dir_name}/")
        for file in sorted(by_dir[dir_name]):
            lines.append(f"  - {file.name}")
        lines.append("")

    # Count summary
    lines.append(f"**Total: {len(files)} files**")

    return "\n".join(lines)


def format_files_for_llm(
    files: list[Path],
    use_repo_map: bool = False,
) -> str:
    """Format file contents for LLM consumption.

    Args:
        files: List of file paths
        use_repo_map: If True, create repo map instead of full contents

    Returns:
        Formatted string with file contents
    """
    if use_repo_map or len(files) > DEFAULT_MAX_FILES:
        return create_repo_map(files)

    parts = []

    for file_path in files:
        content = read_file_content_safe(file_path)
        if content is None:
            continue

        # Use forward slashes for cross-platform compatibility
        relative_path = file_path.relative_to(Path.cwd()).as_posix()

        parts.append(f"### {relative_path}")
        parts.append("```")  # Start code block
        parts.append(content)
        parts.append("```")  # End code block
        parts.append("")  # Blank line separator

    return "\n".join(parts)


def build_context_from_paths(
    paths: list[str],
    extensions: list[str] | None = None,
    use_repo_map: bool = False,
) -> tuple[str, dict[str, Any]]:
    """Build LLM context from file/directory paths.

    This is the main entry point that implements the recommended pattern:
    1. Accept both file paths and directories
    2. Resolve to absolute paths
    3. Collect files (recursively for directories)
    4. Format with clear delimiters
    5. Generate repo map if too many files

    Args:
        paths: List of file/directory path strings
        extensions: Optional file extension filter
        use_repo_map: Force repo map generation

    Returns:
        Tuple of (formatted_context_string, metadata_dict)

    Examples:
        >>> context, meta = build_context_from_paths(['src/'], extensions=['.py'])
        >>> print(context)
        ### src/main.py
        ...
        >>> print(meta['file_count'])
        15
    """
    files = collect_files_from_paths(paths, extensions)

    metadata = {
        "file_count": len(files),
        "total_size": sum(f.stat().st_size for f in files if f.exists()),
        "files": [str(f.relative_to(Path.cwd())) for f in files],
    }

    # Generate repo map if too many files or explicitly requested
    if len(files) > DEFAULT_MAX_FILES or use_repo_map:
        formatted = create_repo_map(files)
        metadata["mode"] = "repo_map"
    else:
        formatted = format_files_for_llm(files)
        metadata["mode"] = "full_content"

    return formatted, metadata


def print_context_summary(metadata: dict[str, Any]) -> None:
    """Print a summary of loaded context.

    Args:
        metadata: Metadata dict from build_context_from_paths
    """
    mode = metadata.get("mode", "unknown")
    count = metadata.get("file_count", 0)
    size_kb = metadata.get("total_size", 0) / 1024

    print(f"\n[Context loaded: {count} files, {size_kb:.1f} KB, mode={mode}]")

    if metadata.get("files"):
        print("[Files included:]")
        for file_path in metadata["files"][:10]:  # Show first 10
            print(f"  - {file_path}")
        if len(metadata["files"]) > 10:
            print(f"  ... and {len(metadata['files']) - 10} more")
        print()

```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\performance_logger.py
```python
"""CLI performance logger for tracking execution metrics.

Thread-safe append-only JSONL logging for CLI performance tracking.
Multi-terminal safe: no shared state, no TTL caches, immune to stale data.
"""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

from task_classifier import TaskType


@dataclass
class CliExecutionRecord:
    """Single CLI execution record.

    Attributes:
        timestamp: ISO format timestamp of execution
        cli_name: CLI identifier (qwen, gemini, codex, opencode, glm-4.7-flash)
        task_type: Classified task type
        query_preview: First 100 chars of query (for storage efficiency)
        duration_seconds: Execution time in seconds
        outcome: Execution outcome (success, timeout, error, empty_output)
        output_length: Response character count
        error_message: Error message if outcome is "error"
        quality_score: Optional 1-5 manual rating (future enhancement)
    """

    timestamp: str
    cli_name: str
    task_type: str
    query_preview: str
    duration_seconds: float
    outcome: Literal["success", "timeout", "error", "empty_output"]
    output_length: int
    error_message: str | None = None
    quality_score: int | None = None

    def to_jsonl(self) -> str:
        """Convert record to JSONL line string.

        Returns:
            JSON-formatted string suitable for append-only file writing
        """
        return json.dumps(asdict(self))


class CliPerformanceLogger:
    """Thread-safe append-only logger for CLI performance tracking.

    Uses JSONL format for simplicity and git-friendliness.
    Thread-safe for multi-terminal concurrent access via threading.Lock.

    Design principles:
    - Append-only: No read-modify-write operations
    - Thread-safe: threading.Lock() for concurrent writes
    - No TTL: No caching, immune to stale data issues
    - Multi-terminal: Each terminal writes independently, no shared state

    Log format: One JSON object per line (JSONL)
    """

    def __init__(self, log_path: str | None = None):
        """Initialize logger with optional custom log path.

        Args:
            log_path: Path to JSONL log file. Defaults to P:/__csf/data/llm_cli_performance.jsonl
        """
        if log_path is None:
            log_path = "P:/__csf/data/llm_cli_performance.jsonl"

        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()  # Thread-safe writes

    def log_execution(
        self,
        cli_name: str,
        task_type: TaskType,
        query: str,
        duration_seconds: float,
        outcome: Literal["success", "timeout", "error", "empty_output"],
        output_length: int,
        error_message: str | None = None,
    ) -> None:
        """Log a CLI execution record.

        Thread-safe for concurrent writes from multiple terminals.

        Args:
            cli_name: CLI identifier (qwen, gemini, codex, opencode, glm-4.7-flash)
            task_type: Classified task type
            query: Original query (truncated to 100 chars for storage)
            duration_seconds: Execution time
            outcome: Execution outcome
            output_length: Response character count
            error_message: Error message if outcome is "error"
        """
        record = CliExecutionRecord(
            timestamp=datetime.now().isoformat(),
            cli_name=cli_name,
            task_type=task_type.value,
            query_preview=query[:100],
            duration_seconds=duration_seconds,
            outcome=outcome,
            output_length=output_length,
            error_message=error_message,
        )

        # Thread-safe append (critical for multi-terminal safety)
        with self._lock:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(record.to_jsonl() + "\n")

    def get_all_records(self) -> list[CliExecutionRecord]:
        """Read all records from log file.

        Returns:
            List of CliExecutionRecord objects (empty list if file doesn't exist)
        """
        if not self.log_path.exists():
            return []

        records = []
        with open(self.log_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    records.append(CliExecutionRecord(**data))
                except (json.JSONDecodeError, TypeError):
                    # Skip corrupt lines (graceful degradation)
                    continue

        return records

    def get_records_for_task(self, task_type: TaskType) -> list[CliExecutionRecord]:
        """Get all records for a specific task type.

        Args:
            task_type: Task type to filter by

        Returns:
            List of records for this task type
        """
        all_records = self.get_all_records()
        return [r for r in all_records if r.task_type == task_type.value]

    def get_records_for_cli(self, cli_name: str) -> list[CliExecutionRecord]:
        """Get all records for a specific CLI.

        Args:
            cli_name: CLI name to filter by (qwen, gemini, codex, etc.)

        Returns:
            List of records for this CLI
        """
        all_records = self.get_all_records()
        return [r for r in all_records if r.cli_name == cli_name]

    def get_performance_stats(self, task_type: TaskType | None = None) -> dict:
        """Calculate performance statistics for CLI execution.

        Args:
            task_type: Optional task type filter. If None, stats for all tasks.

        Returns:
            Dictionary with performance metrics:
            {
                "cli_name": {
                    "total_executions": int,
                    "success_rate": float (0-1),
                    "avg_duration": float (seconds),
                    "avg_output_length": int,
                }
            }
        """
        records = self.get_records_for_task(task_type) if task_type else self.get_all_records()

        if not records:
            return {}

        stats = {}
        for cli in ["qwen", "gemini", "codex", "opencode", "glm-4.7-flash"]:
            cli_records = [r for r in records if r.cli_name == cli]
            if not cli_records:
                continue

            successful = [r for r in cli_records if r.outcome == "success"]
            stats[cli] = {
                "total_executions": len(cli_records),
                "success_rate": len(successful) / len(cli_records),
                "avg_duration": sum(r.duration_seconds for r in cli_records) / len(cli_records),
                "avg_output_length": sum(r.output_length for r in cli_records) / len(cli_records),
            }

        return stats


# Test function for development
def _test_performance_logger():
    """Test performance logger functionality."""
    import os
    import tempfile

    # Create temporary log file for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        test_log = os.path.join(tmpdir, "test_performance.jsonl")
        logger = CliPerformanceLogger(test_log)

        print("Performance Logger Tests:")
        print("=" * 80)

        # Test 1: Log some executions
        print("\n1. Logging test executions...")
        logger.log_execution(
            cli_name="qwen",
            task_type=TaskType.CODE_REVIEW,
            query="review this code for bugs",
            duration_seconds=63.5,
            outcome="success",
            output_length=1500,
        )

        logger.log_execution(
            cli_name="gemini",
            task_type=TaskType.PLANNING,
            query="create a plan for X",
            duration_seconds=160.2,
            outcome="success",
            output_length=2300,
        )

        logger.log_execution(
            cli_name="codex",
            task_type=TaskType.DEBUG,
            query="debug this error",
            duration_seconds=45.0,
            outcome="error",
            output_length=0,
            error_message="Connection timeout",
        )

        print("   ✓ Logged 3 test records")

        # Test 2: Read all records
        print("\n2. Reading all records...")
        records = logger.get_all_records()
        print(f"   ✓ Read {len(records)} records")

        # Test 3: Filter by task type
        print("\n3. Filtering by task type...")
        code_review_records = logger.get_records_for_task(TaskType.CODE_REVIEW)
        print(f"   ✓ Found {len(code_review_records)} code_review records")

        # Test 4: Calculate stats
        print("\n4. Calculating performance stats...")
        stats = logger.get_performance_stats()
        for cli, metrics in stats.items():
            print(f"   {cli}:")
            print(f"     - Total executions: {metrics['total_executions']}")
            print(f"     - Success rate: {metrics['success_rate']:.1%}")
            print(f"     - Avg duration: {metrics['avg_duration']:.1f}s")
            print(f"     - Avg output length: {metrics['avg_output_length']:.0f} chars")

        # Test 5: Verify JSONL format
        print("\n5. Verifying JSONL format...")
        with open(test_log) as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                try:
                    data = json.loads(line)
                    assert "timestamp" in data
                    assert "cli_name" in data
                    assert "task_type" in data
                except (json.JSONDecodeError, AssertionError) as e:
                    print(f"   ✗ Line {i} failed: {e}")
                    return
        print(f"   ✓ All {len(records)} lines are valid JSON")

        print("\n" + "=" * 80)
        print("All tests passed!")


if __name__ == "__main__":
    _test_performance_logger()

```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\prompt_templates.py
```python
"""Prompt template system for task-specific LLM prompts.

Provides specialized prompts for different task types (code review, planning, brainstorm, etc.)
to improve LLM output quality and relevance.
"""

from __future__ import annotations

from task_classifier import TaskType

# Base solo-dev constraints (applied to all prompts)
SOLO_DEV_CONSTRAINTS = """

CONSTRAINTS (Solo Development Environment):
- Single developer - NO team assignments, code reviews, or collaborative workflows requiring multiple people
- Prefer SIMPLE solutions over enterprise patterns (JSON > databases, local > distributed)
- Pragmatic over comprehensive (ROI > risk-aversion, working > perfect)
- Local testing over CI infrastructure
- Avoid over-engineering for scalability (single user, low concurrency)
"""


# Task-specific prompt templates
PROMPT_TEMPLATES = {
    TaskType.CODE_REVIEW: """You are performing a CODE REVIEW for a solo developer.

Focus on:
- Security vulnerabilities (OWASP Top 10 - injection, XSS, auth issues, etc.)
- Performance issues (inefficient algorithms, N+1 queries, unnecessary complexity)
- Code quality (readability, maintainability, naming conventions)
- Logic errors and edge cases (null checks, bounds, error handling)
- Solo-dev appropriateness (avoid enterprise patterns, team workflows, over-engineering)

Output format:
## Critical Issues (must fix)
- [Issue description with file:line reference]

## Important Issues (should fix)
- [Issue description with file:line reference]

## Suggestions (nice to have)
- [Improvement suggestions]

Be specific and actionable. Include file:line references when applicable.
If you're unsure about something, state the uncertainty explicitly.
""",
    TaskType.PLANNING: """You are creating an IMPLEMENTATION PLAN for a solo developer.

Focus on:
- Clear phased approach (what to do first, second, third - in logical order)
- Dependencies and blockers (what must be done before what)
- Risk mitigation (what could go wrong and how to prevent it)
- Testing strategy (how to verify it works at each phase)
- Rollback plan (how to revert if something goes wrong)

Output format:
## Phase 1: [Name]
- Tasks: [specific actionable steps]
- Success criteria: [specific measurable outcomes]
- Dependencies: [what must exist first]

## Phase 2: [Name]
...

## Risks and Mitigation
- [Risk] → [Mitigation strategy]

## Testing Strategy
- [How to verify each phase works]

Be concrete and actionable. Avoid vague "consider X" statements.
Each task should be something you can immediately execute.
""",
    TaskType.BRAINSTORM: """You are BRAINSTORMING ideas for a solo developer.

Focus on:
- Diverse perspectives (technical, user experience, architectural alternatives)
- Practical ideas (feasible to implement by one person)
- Innovation (novel approaches, not just obvious solutions)
- Trade-offs (pros and cons of each idea - effort vs value)

Output format:
## Idea 1: [Name]
- Description: [what it is in 1-2 sentences]
- Pros: [benefits]
- Cons: [drawbacks]
- Effort: [S/M/L] - estimated implementation effort
- Value: [Low/Medium/High] - expected impact

## Idea 2: [Name]
...

Be creative but realistic. Prioritize actionable ideas that one person can implement.
Avoid suggestions that require team coordination or enterprise infrastructure.
""",
    TaskType.RESEARCH: """You are conducting RESEARCH to answer a question.

Focus on:
- Accurate information (cite sources when possible - official docs, well-known blogs)
- Completeness (cover all aspects of the question)
- Clarity (explain technical concepts clearly for a developer audience)
- Actionability (how to use this information in practice)

Output format:
## Summary
[2-3 sentence overview of the answer]

## Details
[comprehensive answer with examples and explanations]

## References
[sources, official docs, or "general knowledge" if no specific sources]

## Practical Application
[how to actually use this information in real code/projects]

Be thorough. If you're unsure about something, state the uncertainty explicitly.
If information is rapidly changing (e.g., specific version details), mention that.
""",
    TaskType.DEBUG: """You are DEBUGGING a code issue for a solo developer.

Focus on:
- Root cause analysis (what's actually broken, not just symptoms)
- Diagnostic steps (how to verify the cause - specific commands/tests)
- Fix options (different approaches to solve it, with trade-offs)
- Prevention (how to avoid this issue in the future)

Output format:
## Diagnosis
[What's broken and why - be specific]

## Verification Steps
[How to confirm the diagnosis - commands to run, logs to check]

## Fix Options
1. [Option 1] - [description]
   - Pros: [benefits]
   - Cons: [drawbacks]
   - Risk: [what could go wrong]

2. [Option 2] - [description]
   - Pros: [benefits]
   - Cons: [drawbacks]
   - Risk: [what could go wrong]

## Prevention
[How to avoid this issue in the future]

Be methodical. Start with most likely causes. Suggest specific commands to run.
If you need more information (logs, error messages, code), say what specifically.
""",
    TaskType.REFACTOR: """You are REFACTORING code for a solo developer.

Focus on:
- Code quality improvements (readability, maintainability, naming)
- Performance optimizations (reduce complexity, improve efficiency)
- Simplification (remove unnecessary complexity, over-engineering)
- Testing (how to verify refactored code works correctly)

Output format:
## Issues Found
[Specific problems with current code - be precise]

## Refactoring Plan
[Step-by-step improvements in logical order]

### Step 1: [Action]
- What to change: [specific code changes]
- Why: [benefit]
- Risk: [what could break]

### Step 2: [Action]
...

## Verification
[Specific tests to run to verify refactored code works]

Be conservative. Only change what needs improvement.
Avoid "big rewrites" - prefer incremental improvements.
If refactoring is risky, say so explicitly.
""",
    TaskType.GENERAL: """You are answering a question for a solo developer.

Provide a clear, accurate, and actionable response.
Be specific and practical. Avoid unnecessary theory unless requested.
If you need more information to answer well, say what specifically.
""",
}


def build_prompt(
    query: str,
    task_type: TaskType,
    context: str | None = None,
) -> str:
    """Build task-specific prompt with context injection.

    Args:
        query: User query
        task_type: Classified task type
        context: Optional context (file contents, session history, etc.)

    Returns:
        Formatted prompt string with task-specific instructions and solo-dev constraints
    """
    template = PROMPT_TEMPLATES.get(task_type, PROMPT_TEMPLATES[TaskType.GENERAL])

    # Check if query already contains --- Context --- (added by _build_query_context)
    # If so, don't wrap in another --- Context --- to avoid nesting issues that confuse gemini CLI
    query_has_context = "--- Context ---" in query

    if context and not query_has_context:
        prompt = f"""--- Context ---
{context}

---

{template}

## Question
{query}
"""
    else:
        prompt = f"""{template}

## Question
{query}
"""

    # Apply solo-dev constraints to all task types
    return prompt + SOLO_DEV_CONSTRAINTS


# Test function for development
def _test_prompt_building():
    """Test prompt building for all task types."""
    test_cases = [
        ("review this code for bugs", TaskType.CODE_REVIEW),
        ("create a plan for X", TaskType.PLANNING),
        ("brainstorm ideas for Y", TaskType.BRAINSTORM),
        ("research best practices", TaskType.RESEARCH),
        ("debug this error", TaskType.DEBUG),
        ("refactor this function", TaskType.REFACTOR),
        ("what is 12 + 12?", TaskType.GENERAL),
    ]

    print("Prompt Template Tests:")
    print("=" * 80)
    for query, expected_type in test_cases:
        result = build_prompt(query, expected_type, context=None)
        print(f"\nQuery: {query}")
        print(f"Task Type: {expected_type.value}")
        print(f"Prompt Length: {len(result)} chars")
        print(
            f"Contains solo-dev constraints: {'SOLO_DEV' in result or 'Solo Development' in result}"
        )
        print("-" * 80)


if __name__ == "__main__":
    _test_prompt_building()

```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\__init__.py
```python
"""Health check CLI for /ai-cli skill.

Provides health and list subcommands for checking CLI tool availability.
"""

from __future__ import annotations

```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\analyze_security.py
```python
#!/usr/bin/env python3
"""Security analysis tool that writes results to a file."""

import argparse
import json
import subprocess
from pathlib import Path
import tempfile
import sys

def analyze_file(file_path: str, output_file: str = None) -> str:
    """Analyze a Python file for security vulnerabilities and write results to a file."""
    
    # Read the file content
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return f"Error reading file: {e}"
    
    # Perform security analysis (simplified version)
    issues = []
    lines = content.split('\n')
    
    # Check for common security issues
    for i, line in enumerate(lines, 1):
        line_num = i
        
        # 1. Command injection vulnerability
        if 'subprocess.run' in line and 'shell=True' in line:
            issues.append({
                'line': line_num,
                'severity': 'CRITICAL',
                'issue': 'Command Injection Vulnerability',
                'description': 'Uses shell=True which can lead to arbitrary command execution',
                'code': line.strip()
            })
        
        # 2. Insecure cache handling
        if 'mkdir' in line and 'exist_ok=True' in line and 'mode=' not in line:
            issues.append({
                'line': line_num,
                'severity': 'HIGH',
                'issue': 'Insecure Cache Permissions',
                'description': 'Cache directory created without explicit permission restrictions',
                'code': line.strip()
            })
        
        # 3. Broad exception handling
        if line.strip() == 'except Exception:' or line.strip().startswith('except Exception:'):
            issues.append({
                'line': line_num,
                'severity': 'MEDIUM',
                'issue': 'Broad Exception Handling',
                'description': 'Catches all exceptions without specific handling',
                'code': line.strip()
            })
        
        # 4. Hardcoded sensitive data
        if 'BROKEN_MODELS' in line or 'HARDCODED_' in line:
            issues.append({
                'line': line_num,
                'severity': 'MEDIUM',
                'issue': 'Hardcoded Security Data',
                'description': 'Security-related data is hardcoded instead of being dynamic',
                'code': line.strip()
            })
    
    # Determine output file
    if output_file is None:
        # Create a temp file in the same directory as the input file
        input_dir = Path(file_path).parent
        output_file = input_dir / f"security_analysis_{Path(file_path).stem}.json"
    else:
        output_file = Path(output_file)
    
    # Write results to file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'file': file_path,
                'issues_found': len(issues),
                'issues': issues,
                'analysis_complete': True
            }, f, indent=2)
        return str(output_file)
    except Exception as e:
        return f"Error writing output: {e}"

def main():
    parser = argparse.ArgumentParser(description='Analyze Python files for security vulnerabilities')
    parser.add_argument('file', help='Python file to analyze')
    parser.add_argument('-o', '--output', help='Output file path (default: auto-generated in input directory)')
    args = parser.parse_args()
    
    result = analyze_file(args.file, args.output)
    print(result)  # Only the filename is printed to stdout

if __name__ == '__main__':
    main()
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\cli.py
```python
#!/usr/bin/env python3
"""
AI-CLI Health Check - CLI tool availability and configuration checks.

Provides health and list subcommands for checking CLI tool status.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

# Flexible import for cli_detector - handles both module and direct execution
try:
    from . import cli_detector  # When run as module
except ImportError:
    # When run directly, add scripts dir to path
    scripts_dir = Path(__file__).parent
    sys.path.insert(0, str(scripts_dir))
    import cli_detector


def cmd_health(args: argparse.Namespace) -> int:
    """Check CLI tool health and availability.

    Returns exit code 0 if all checked CLIs are healthy, 1 if any fail.
    """
    # Get CLI status
    cli_status = cli_detector.get_all_cli_status()
    env_status = cli_detector.check_env_vars()

    # Determine what to check
    if args.cli:
        # Check specific CLI
        clis_to_check = [args.cli]
        if args.cli not in cli_detector.CLI_TOOLS:
            print(f"❌ Unknown CLI: {args.cli}", file=sys.stderr)
            print(f"Available CLIs: {', '.join(cli_detector.CLI_TOOLS.keys())}", file=sys.stderr)
            return 1
    else:
        # Check all CLIs
        clis_to_check = list(cli_detector.CLI_TOOLS.keys())

    all_healthy = True
    results = {}

    # Check each CLI
    for cli_id in clis_to_check:
        status = cli_status[cli_id]
        cli_def = cli_detector.CLI_TOOLS[cli_id]

        if args.sanity and status["installed"]:
            # Run sanity check with actual CLI
            print(f"🔍 Checking {cli_def['name']}...", end=" ")

            # Use the platform-specific command from status detection
            # For npm CLIs on Windows, this is ["node", "path/to/script.js"]
            # For other CLIs, this is ["command"]
            sanity_command = status["command"]
            if isinstance(sanity_command, str):
                sanity_command = sanity_command.split()

            try:
                result = subprocess.run(
                    sanity_command + ["--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    version = (
                        result.stdout.strip().split("\n")[0] if result.stdout.strip() else "OK"
                    )
                    print(f"[OK] ({version})")
                    results[cli_id] = "healthy"
                else:
                    print("[FAIL]")
                    print(f"  ❌ Exit code {result.returncode}")
                    results[cli_id] = "failed"
                    all_healthy = False
            except subprocess.TimeoutExpired:
                print("[TIMEOUT]")
                print("  ⚠️  Timeout after 10s")
                results[cli_id] = "timeout"
                all_healthy = False
            except FileNotFoundError:
                print("[NOT FOUND]")
                cmd_display = (
                    sanity_command[0] if isinstance(sanity_command, list) else sanity_command
                )
                print(f"  ❌ {cmd_display} not found")
                results[cli_id] = "not_found"
                all_healthy = False
            except Exception as e:
                print("[ERROR]")
                print(f"  ❌ {e}")
                results[cli_id] = "error"
                all_healthy = False
        else:
            # Just check installation status
            if status["installed"]:
                results[cli_id] = "installed"
            else:
                results[cli_id] = "not_installed"
                all_healthy = False

    # Print summary
    print()
    if all_healthy:
        print("✅ All checked CLIs are healthy")
    else:
        print("❌ Some CLIs failed health check")
        print("\nStatus:")
        for cli_id, status in results.items():
            status_icon = "✅" if status in ("healthy", "installed") else "❌"
            print(f"  {status_icon} {cli_id}: {status}")

    # Check environment variables
    print()
    print("🔑 Environment Variables:")
    for var_name, info in env_status.items():
        icon = "✅" if info["set"] else "❌"
        status_text = "is set" if info["set"] else "not set"
        print(f"  {icon} {var_name}: {status_text}")

    return 0 if all_healthy else 1


def cmd_models(args: argparse.Namespace) -> int:
    """Show available models for each CLI."""
    # OpenCode model aliases (from ai_cli.py)
    aliases = {
        "kimi": "chutes/moonshotai/Kimi-K2.5-TEE",
        "minimax": "chutes/MiniMaxAI/MiniMax-M2.1-TEE",
        "nemotron": "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
        "mimo": "chutes/XiaomiMiMo/MiMo-V2-Flash",
        "glm5": "zai/glm-5.1",
        "k2": "chutes/moonshotai/Kimi-K2.5-TEE",
        "deepseek-v3.2": "chutes/deepseek-ai/DeepSeek-V3.2-TEE",
        "deepseek-v3.2-tee": "chutes/deepseek-ai/DeepSeek-V3.2-TEE",
    }
    default_model = "chutes/deepseek-ai/DeepSeek-V3-0324-TEE"

    # Get CLI status for versions
    cli_status = cli_detector.get_all_cli_status()

    lines = []
    lines.append("🤖 AI-CLI Models")
    lines.append("")
    lines.append("OpenCode (configurable)")
    lines.append(f"  default   {default_model}")
    for alias, model in aliases.items():
        lines.append(f"  {alias:<8} {model}")

    lines.append("")
    lines.append("Fixed (no model selection)")
    for cli_id in ["qwen", "gemini", "codex"]:
        status = cli_status[cli_id]
        version = status.get("version") or "unknown"
        cli_def = cli_detector.CLI_TOOLS[cli_id]
        name = cli_def["name"]
        # Strip tool name from version if it appears (e.g., "codex-cli 0.118.0" -> "0.118.0")
        if name in version:
            version = version.replace(name, "").strip()
        lines.append(f"  {cli_id:<6} {name} {version}")

    print("\n".join(lines))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    """List available CLI tools and their status."""
    # Get CLI and environment status
    cli_status = cli_detector.get_all_cli_status()
    env_status = cli_detector.check_env_vars()

    # Print CLI status table
    print(cli_detector.format_cli_status_table(cli_status))

    # Print environment variable status
    print(cli_detector.format_env_var_status(env_status))

    # Print summary
    installed_count = sum(1 for s in cli_status.values() if s["installed"])
    total_count = len(cli_status)
    print(f"Summary: {installed_count}/{total_count} CLIs installed")

    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build argument parser."""
    parser = argparse.ArgumentParser(
        prog="ai-cli",
        description="AI-CLI Health Check - Verify CLI tool availability and configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m .claude.skills.ai-cli.scripts.cli health
  python -m .claude.skills.ai-cli.scripts.cli health --sanity
  python -m .claude.skills.ai-cli.scripts.cli health --cli qwen
  python -m .claude.skills.ai-cli.scripts.cli list

Environment Variables:
  CHUTES_API_KEY        OpenCode API access (for opencode)
  ZAI_API_KEY           GLM-4.7-Flash API access (optional)

CLI Tools:
  qwen      qwen-code - Chutes Qwen3 235B (analysis)
  gemini    gemini-cli - Google Gemini CLI (1M+ tokens)
  codex     codex-cli - OpenRouter DeepSeek R1T2 Chimera (coding)
  opencode  opencode-ai - OpenCode (planning/creative, 300+ models)

Installation:
  npm install -g qwen-code
  npm install -g gemini-cli
  pip install codex-cli
  npm install -g opencode-ai

Resources:
  /ai-cli    - Main skill for parallel LLM execution
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # health command
    health_parser = subparsers.add_parser("health", help="Check CLI tool health")
    health_parser.add_argument(
        "--cli",
        choices=list(cli_detector.CLI_TOOLS.keys()),
        help="Check specific CLI (default: all CLIs)",
    )
    health_parser.add_argument(
        "--sanity",
        action="store_true",
        help="Run sanity check with actual CLI execution",
    )

    # list command
    subparsers.add_parser("list", help="List all CLI tools and their status")

    # models command
    subparsers.add_parser("models", help="Show available models for each CLI")

    return parser


def main() -> int:
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "health":
        return cmd_health(args)
    elif args.command == "list":
        return cmd_list(args)
    elif args.command == "models":
        return cmd_models(args)
    else:
        print(f"Unknown command: {args.command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\cli_detector.py
```python
#!/usr/bin/env python3
"""CLI detection utilities for /ai-cli health checks.

Provides functions to detect and validate CLI tool installations.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

# Platform detection
IS_WINDOWS = sys.platform == "win32"

# CLI definitions with platform-specific invocation patterns
CLI_TOOLS = {
    "qwen": {
        "name": "qwen-code",
        "command": "qwen",
        "description": "Chutes Qwen3 235B (analysis)",
        "install": "npm install -g qwen-code",
        "npm_package": "@qwen-code/qwen-code",
        "npm_script": "cli.js",
        "type": "npm",
    },
    "gemini": {
        "name": "gemini-cli",
        "command": "gemini",
        "description": "Google Gemini CLI (1M+ tokens)",
        "install": "npm install -g gemini-cli",
        "npm_package": "@google/gemini-cli",
        "npm_script": "dist/index.js",
        "type": "npm",
    },
    "codex": {
        "name": "codex-cli",
        "command": "codex",
        "description": "OpenRouter DeepSeek R1T2 Chimera (coding)",
        "install": "npm install -g @openai/codex",
        "npm_package": "@openai/codex",
        "npm_script": "bin/codex.js",
        "type": "npm",
    },
    "pi": {
        "name": "pi-coding-agent",
        "command": "pi",
        "description": "Pi coding agent (multi-provider)",
        "install": "npm install -g @mariozechner/pi-coding-agent",
        "npm_package": "@mariozechner/pi-coding-agent",
        "npm_script": "dist/cli.js",
        "type": "npm",
    },
}

# Environment variable requirements
ENV_VARS = {
    "CHUTES_API_KEY": "OpenCode API access",  # pragma: allowlist secret
    "ZAI_API_KEY": "GLM-4.7-Flash API access (optional)",  # pragma: allowlist secret
}


def _get_npm_root() -> Path:
    """Get the npm root directory for global packages."""
    if IS_WINDOWS:
        return Path.home() / "AppData" / "Roaming" / "npm" / "node_modules"
    else:
        return Path.home() / ".npm-global" / "lib" / "node_modules"


def _get_npm_cli_path(cli_info: dict[str, Any]) -> Path | None:
    """Get the path to an npm-installed CLI script.

    Args:
        cli_info: CLI tool definition dictionary

    Returns:
        Path to the CLI script or None
    """
    if cli_info["type"] != "npm":
        return None

    npm_root = _get_npm_root()
    npm_package = cli_info["npm_package"]
    npm_script = cli_info["npm_script"]

    # Try the package directory
    package_path = npm_root / npm_package / npm_script
    if package_path.exists():
        return package_path

    # For gemini, the CLI is in bundle/ not dist/
    if cli_info["command"] == "gemini":
        alt_path = npm_root / "@google/gemini-cli/bundle/gemini.js"
        if alt_path.exists():
            return alt_path

    return None


def _build_cli_command(cli_id: str, cli_info: dict[str, Any]) -> list[str]:
    """Build the platform-specific command to invoke a CLI.

    Args:
        cli_id: CLI identifier
        cli_info: CLI tool definition dictionary

    Returns:
        List of command parts (e.g., ["node", "path/to/cli.js", "--version"])
    """
    if cli_info["type"] == "npm" and IS_WINDOWS:
        # Windows npm CLI: use node with script path
        script_path = _get_npm_cli_path(cli_info)
        if script_path:
            return ["node", str(script_path)]
        else:
            # Fallback: try the command directly
            return [cli_info["command"]]
    else:
        # Unix or pip-installed: use command directly
        return [cli_info["command"]]


def _run_cli_command(cli_id: str, command_parts: list[str], timeout: int = 10) -> dict[str, Any]:
    """Run a CLI command and capture the result.

    Args:
        cli_id: CLI identifier
        command_parts: List of command parts
        timeout: Timeout in seconds

    Returns:
        Dictionary with success, stdout, stderr, exit_code
    """
    try:
        result = subprocess.run(
            command_parts + ["--version"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "exit_code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Timeout after {timeout}s",
            "exit_code": -1,
        }
    except FileNotFoundError:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Command not found",
            "exit_code": -2,
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "exit_code": -3,
        }


def _extract_version(output: str) -> str | None:
    """Extract version from CLI output.

    Args:
        output: stdout from --version command

    Returns:
        Version string or None
    """
    if not output:
        return None

    # Take first non-empty line
    for line in output.strip().split("\n"):
        line = line.strip()
        if line:
            return line

    return None


def check_cli_installation(cli_id: str) -> dict[str, Any]:
    """Check if a CLI tool is installed and accessible.

    Args:
        cli_id: CLI identifier (qwen, gemini, codex, opencode)

    Returns:
        Dictionary with keys:
            - installed: bool
            - version: str | None
            - path: str | None
            - error: str | None
            - command: str (the command used to invoke the CLI)
    """
    if cli_id not in CLI_TOOLS:
        return {
            "installed": False,
            "version": None,
            "path": None,
            "error": f"Unknown CLI: {cli_id}",
            "command": None,
        }

    cli_info = CLI_TOOLS[cli_id]

    # Build the platform-specific command
    command_parts = _build_cli_command(cli_id, cli_info)
    command_str = " ".join(command_parts)

    # Try to run --version
    result = _run_cli_command(cli_id, command_parts)

    if result["success"]:
        version = _extract_version(result["stdout"])
        return {
            "installed": True,
            "version": version,
            "path": command_str,
            "error": None,
            "command": command_str,
        }
    else:
        # Check if the files exist even if --version failed
        path_exists = False
        cli_path = None

        if cli_info["type"] == "npm":
            script_path = _get_npm_cli_path(cli_info)
            if script_path:
                path_exists = True
                cli_path = str(script_path)
        else:
            cmd_path = shutil.which(cli_info["command"])
            if cmd_path:
                path_exists = True
                cli_path = cmd_path

        error_msg = result["stderr"] if result["stderr"] else "Unknown error"

        if path_exists:
            return {
                "installed": False,
                "version": None,
                "path": cli_path,
                "error": f"Found at {cli_path} but not working: {error_msg}",
                "command": command_str,
            }
        else:
            return {
                "installed": False,
                "version": None,
                "path": None,
                "error": f"Not installed: {error_msg}",
                "command": command_str,
            }


def check_env_vars() -> dict[str, dict[str, Any]]:
    """Check environment variable status.

    Returns:
        Dictionary with env var names as keys, each containing:
            - set: bool
            - description: str
    """
    result = {}
    for var_name, description in ENV_VARS.items():
        result[var_name] = {
            "set": bool(os.environ.get(var_name)),
            "description": description,
        }
    return result


def get_all_cli_status() -> dict[str, dict[str, Any]]:
    """Get status of all CLI tools.

    Returns:
        Dictionary with CLI IDs as keys, containing installation status
    """
    result = {}
    for cli_id in CLI_TOOLS:
        result[cli_id] = check_cli_installation(cli_id)
    return result


def format_cli_status_table(status: dict[str, dict[str, Any]]) -> str:
    """Format CLI status as a readable table.

    Args:
        status: Dictionary from get_all_cli_status()

    Returns:
        Formatted table string
    """
    lines = []
    lines.append("📋 CLI Tool Status:")
    lines.append("")

    for cli_id, info in status.items():
        cli_def = CLI_TOOLS[cli_id]
        installed = info["installed"]
        version = info.get("version")
        path = info.get("path")
        error = info.get("error")
        command = info.get("command")

        icon = "✅" if installed else "❌"
        lines.append(f"  {icon} {cli_id:12} ({cli_def['name']})")
        lines.append(f"     Description: {cli_def['description']}")

        if installed:
            if version:
                lines.append(f"     Version:     {version}")
            if command:
                lines.append(f"     Command:     {command}")
            if path and path != command:
                lines.append(f"     Path:        {path}")
        else:
            if error:
                lines.append(f"     Status:      {error}")
            lines.append(f"     Install:     {cli_def['install']}")

        lines.append("")

    return "\n".join(lines)


def format_env_var_status(env_status: dict[str, dict[str, Any]]) -> str:
    """Format environment variable status as a readable table.

    Args:
        env_status: Dictionary from check_env_vars()

    Returns:
        Formatted table string
    """
    lines = []
    lines.append("🔑 Environment Variables:")
    lines.append("")

    for var_name, info in env_status.items():
        icon = "✅" if info["set"] else "❌"
        status_text = "is set" if info["set"] else "not set"
        lines.append(f"  {icon} {var_name}")
        lines.append(f"     Description: {info['description']}")
        lines.append("")

    return "\n".join(lines)

```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\filter_models.py
```python
#!/usr/bin/env python3
"""Filter opencode models by context and pricing."""

import argparse
import json
import subprocess
from pathlib import Path

# Cache settings
CACHE_DIR = Path.home() / ".cache" / "ai-cli"
CACHE_FILE = CACHE_DIR / "opencode_models.txt"
CACHE_TTL_HOURS = 12

# Known broken/deprecated models that don't actually work
BROKEN_MODELS = {
    "openrouter/openrouter/sherlock-dash-alpha",
    "openrouter/openrouter/sherlock-think-alpha",
    "openrouter/openrouter/hunter-alpha",
}


def get_cached_models() -> str | None:
    """Get cached models data if available and fresh."""
    if not CACHE_FILE.exists():
        return None

    # Check cache age
    import time

    cache_age = time.time() - CACHE_FILE.stat().st_mtime
    max_age_seconds = CACHE_TTL_HOURS * 3600

    if cache_age > max_age_seconds:
        return None

    return CACHE_FILE.read_text()


def save_to_cache(data: str) -> None:
    """Save models data to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(data)


def fetch_models(force_refresh: bool = False) -> str:
    """Fetch models from opencode CLI."""
    # Check cache first (unless force refresh)
    if not force_refresh:
        cached = get_cached_models()
        if cached is not None:
            return cached

    # Fetch fresh data
    result = subprocess.run(
        "opencode models --verbose",
        capture_output=True,
        text=True,
        shell=True,
    )

    # Save to cache
    save_to_cache(result.stdout)
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description="Filter opencode models by context and pricing")
    parser.add_argument("--refresh", action="store_true", help="Force cache refresh")
    parser.add_argument(
        "--context", type=int, default=190000, help="Minimum context window (default: 190000)"
    )
    args = parser.parse_args()

    # Get verbose model data (cached or fresh)
    models_output = fetch_models(force_refresh=args.refresh)
    lines = models_output.strip().split("\n")

    min_context = args.context
    results = []
    current_model_id = None
    json_lines = []

    brace_count = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # If we're inside a JSON block, accumulate all lines
        if json_lines:
            json_lines.append(line)
            # Count braces to find the end of the JSON
            brace_count += line.count("{") - line.count("}")

            # When brace count returns to 0, we've closed the outermost object
            if brace_count == 0:
                # Parse the accumulated JSON
                try:
                    json_text = "\n".join(json_lines)
                    model_data = json.loads(json_text)

                    # Skip known broken/deprecated models
                    if current_model_id in BROKEN_MODELS:
                        json_lines = []
                        brace_count = 0
                        current_model_id = None
                        continue

                    # Filter: Exclude OpenRouter paid models
                    # (Only show free OpenRouter models, like the ai-openrouter skill)
                    provider_id = model_data.get("providerID", "")
                    cost_in = model_data.get("cost", {}).get("input", -1)
                    cost_out = model_data.get("cost", {}).get("output", -1)

                    if provider_id == "openrouter" and (cost_in != 0 or cost_out != 0):
                        # OpenRouter model with non-zero cost - skip it
                        json_lines = []
                        brace_count = 0
                        current_model_id = None
                        continue

                    context = model_data.get("limit", {}).get("context", 0)
                    cost_in = model_data.get("cost", {}).get("input", -1)
                    cost_out = model_data.get("cost", {}).get("output", -1)

                    if context > min_context:
                        name = model_data.get("name", "Unknown")
                        is_free = cost_in == 0 and cost_out == 0
                        results.append(
                            {
                                "id": current_model_id,
                                "name": name,
                                "context": context,
                                "free": is_free,
                                "cost_in": cost_in,
                                "cost_out": cost_out,
                            }
                        )
                except Exception:
                    pass

                # Reset for next model
                json_lines = []
                brace_count = 0
                current_model_id = None
        elif line.startswith("{"):
            # Start of a new JSON block
            json_lines.append(line)
            brace_count = line.count("{") - line.count("}")
        else:
            # This is a model ID (before the JSON block)
            current_model_id = line

    # Sort: free first, then by context descending
    results.sort(key=lambda x: (not x["free"], -x["context"]))

    print(f"Models with >{min_context:,} context (FREE first, then by context):")
    print()

    if not results:
        print(f"No models found with >{min_context:,} context.")
        print()
        # Check what the maximum context is
        max_ctx = 0
        for model_block in results:
            if model_block["context"] > max_ctx:
                max_ctx = model_block["context"]
        print(f"Maximum context found: {max_ctx:,} tokens")
    else:
        for r in results:
            if r["free"]:
                free_tag = "FREE    "
            else:
                free_tag = f"${r['cost_in']:.2f}/${r['cost_out']:.2f}M"
            print(f"{free_tag:12} {r['context']:>10,} ctx  {r['id']}")


if __name__ == "__main__":
    main()

```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\structured_response.py
```python
#!/usr/bin/env python3
"""
Structured response format for /ai-cli skill.

Provides consistent JSON schema for LLM responses with:
- Standardized metadata (response time, token usage, model info)
- Quality gate findings structure
- Error handling and partial results
- Multi-CLI aggregation metadata
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TokenUsage:
    """Token usage metrics."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def to_dict(self) -> dict[str, int]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SourceMetadata:
    """Metadata about the source of a finding."""

    cli_name: str
    model_id: str | None = None
    confidence: int = 0
    line_reference: str | None = None


@dataclass
class Finding:
    """A single finding extracted from LLM output."""

    category: str  # "bug", "security", "performance", "best_practice", etc.
    severity: str  # "critical", "high", "medium", "low", "info"
    title: str
    description: str
    location: str | None = None  # File path or code location
    code_snippet: str | None = None
    source: SourceMetadata | None = None
    confidence: int = 0
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        d = asdict(self)
        if self.source:
            d["source"] = asdict(self.source)
        return d


@dataclass
class CliResponse:
    """Standardized response from a single CLI."""

    cli_name: str
    model_id: str | None = None
    success: bool = True
    output: str = ""
    error: str | None = None
    response_time_ms: int = 0
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    findings: list[Finding] = field(default_factory=list)
    raw_output: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        d = asdict(self)
        d["token_usage"] = self.token_usage.to_dict()
        d["findings"] = [f.to_dict() if isinstance(f, Finding) else f for f in self.findings]
        return d


@dataclass
class QualityGateResult:
    """Result from quality gate filtering."""

    enabled: bool = False
    input_count: int = 0
    output_count: int = 0
    min_confidence: int = 80
    rejection_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class AggregatedResponse:
    """Aggregated response from multiple CLIs."""

    query: str
    timestamp: str
    cli_responses: dict[str, CliResponse] = field(default_factory=dict)
    consensus: str | None = None
    agreement_level: float = 0.0  # 0.0 to 1.0
    quality_gate: QualityGateResult = field(default_factory=QualityGateResult)
    total_response_time_ms: int = 0
    context_files: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        d = asdict(self)
        d["cli_responses"] = {
            k: v.to_dict() if isinstance(v, CliResponse) else v
            for k, v in self.cli_responses.items()
        }
        d["quality_gate"] = self.quality_gate.to_dict()
        return d

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


def extract_token_usage(output: str) -> TokenUsage:
    """Extract token usage from CLI output.

    Args:
        output: Raw CLI output

    Returns:
        TokenUsage with extracted metrics
    """
    usage = TokenUsage()

    # Common patterns for token usage in CLI outputs
    patterns = [
        r"(\d+)\s*prompt?\s*tokens?",
        r"(\d+)\s*completion?\s*tokens?",
        r"total:\s*(\d+)\s*tokens?",
        r"tokens:\s*(\d+)",
    ]

    output_lower = output.lower()

    for pattern in patterns:
        matches = re.findall(pattern, output_lower)
        if matches:
            if "prompt" in pattern:
                usage.prompt_tokens = int(matches[0])
            elif "completion" in pattern:
                usage.completion_tokens = int(matches[0])
            elif "total" in pattern:
                usage.total_tokens = int(matches[0])

    # Calculate total if not present but prompt/completion are
    if usage.total_tokens == 0 and usage.prompt_tokens > 0 and usage.completion_tokens > 0:
        usage.total_tokens = usage.prompt_tokens + usage.completion_tokens

    return usage


def extract_model_id(output: str, cli_name: str) -> str | None:
    """Extract model ID from CLI output.

    Args:
        output: Raw CLI output
        cli_name: Name of the CLI

    Returns:
        Model ID if found, None otherwise
    """
    # Common patterns for model identification
    patterns = [
        r"model:\s*([\w/.\-]+)",
        r"using\s+model\s+([\w/.\-]+)",
        r"model_id['\"]?\s*[:=]\s*['\"]?([\w/.\-]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            return match.group(1)

    # Known model defaults by CLI
    known_models = {
        "qwen": "qwen/qwen3-235b",
        "gemini": "gemini-2.0-flash-exp",
        "codex": "deepseek/deepseek-r1",
        "opencode": "chutes/moonshotai/Kimi-K2.5-TEE",
        "glm-flash": "glm-4.7-flash",
    }

    return known_models.get(cli_name)


def extract_findings_from_text(
    output: str, cli_name: str, model_id: str | None = None
) -> list[Finding]:
    """Extract structured findings from text output.

    Args:
        output: Raw CLI output
        cli_name: Name of the CLI
        model_id: Optional model ID

    Returns:
        List of Finding objects
    """
    findings = []

    # Pattern for findings with severity markers
    # Look for lines with: [SEVERITY] or SEVERITY: patterns
    severity_pattern = r"\[(critical|high|medium|low|info)\]|(critical|high|medium|low|info):\s*"

    lines = output.split("\n")
    current_severity = "medium"
    current_description = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for severity marker
        severity_match = re.search(severity_pattern, line, re.IGNORECASE)
        if severity_match:
            # Save previous finding if exists
            if current_description:
                findings.append(
                    Finding(
                        category="general",
                        severity=current_severity,
                        title=current_description[0][:100] if current_description else "Finding",
                        description=" ".join(current_description),
                        source=SourceMetadata(
                            cli_name=cli_name,
                            model_id=model_id,
                            confidence=50,  # Default confidence for text extraction
                        ),
                    )
                )
                current_description = []

            current_severity = severity_match.group(1) or severity_match.group(2)
            # Remove severity marker from line for description
            line = re.sub(severity_pattern, "", line, flags=re.IGNORECASE).strip()

        if line:
            current_description.append(line)

    # Save last finding
    if current_description:
        findings.append(
            Finding(
                category="general",
                severity=current_severity,
                title=current_description[0][:100] if current_description else "Finding",
                description=" ".join(current_description),
                source=SourceMetadata(
                    cli_name=cli_name,
                    model_id=model_id,
                    confidence=50,
                ),
            )
        )

    return findings


def extract_findings_from_json(
    json_output: str | dict, cli_name: str, model_id: str | None = None
) -> list[Finding]:
    """Extract structured findings from JSON output.

    Args:
        json_output: JSON string or dict
        cli_name: Name of the CLI (used for source metadata)
        model_id: Optional model ID (used for source metadata)

    Returns:
        List of Finding objects
    """
    findings = []

    # cli_name and model_id are used when building Finding objects below
    _ = cli_name, model_id  # Mark as intentionally used

    try:
        data = json.loads(json_output) if isinstance(json_output, str) else json_output
    except (json.JSONDecodeError, TypeError):
        return []

    # Handle different JSON structures
    # Structure 1: {"findings": [...]}
    if isinstance(data, dict) and "findings" in data:
        for f in data["findings"]:
            if isinstance(f, dict):
                findings.append(
                    Finding(
                        category=f.get("category", "general"),
                        severity=f.get("severity", "medium"),
                        title=f.get("title", "Finding"),
                        description=f.get("description", ""),
                        location=f.get("location"),
                        code_snippet=f.get("code_snippet"),
                        confidence=f.get("confidence", 50),
                        tags=f.get("tags", []),
                    )
                )

    # Structure 2: [{"type": "finding", ...}, ...]
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                findings.append(
                    Finding(
                        category=item.get("category", "general"),
                        severity=item.get("severity", "medium"),
                        title=item.get("title", item.get("message", "Finding")[:100]),
                        description=item.get("description", item.get("message", "")),
                        location=item.get("location"),
                        confidence=item.get("confidence", 50),
                    )
                )

    return findings


def build_structured_response(
    cli_name: str,
    output: str,
    error: str | None = None,
    response_time_ms: int = 0,
    success: bool = True,
) -> CliResponse:
    """Build a structured CliResponse from raw CLI output.

    Args:
        cli_name: Name of the CLI
        output: Raw output string
        error: Error message if any
        response_time_ms: Response time in milliseconds
        success: Whether the CLI call succeeded

    Returns:
        CliResponse with structured data
    """
    model_id = extract_model_id(output, cli_name)
    token_usage = extract_token_usage(output)

    # Try to extract findings from JSON first, then text
    findings = []
    try:
        findings = extract_findings_from_json(output, cli_name, model_id)
    except (json.JSONDecodeError, TypeError):
        findings = extract_findings_from_text(output, cli_name, model_id)

    return CliResponse(
        cli_name=cli_name,
        model_id=model_id,
        success=success,
        output=output[:10000] if len(output) > 10000 else output,  # Truncate large outputs
        error=error,
        response_time_ms=response_time_ms,
        token_usage=token_usage,
        findings=findings[:50],  # Limit to 50 findings
        raw_output=output,
        metadata={
            "output_length": len(output),
            "truncated": len(output) > 10000,
            "findings_count": len(findings),
        },
    )


def calculate_agreement_level(responses: list[CliResponse]) -> float:
    """Calculate agreement level between CLI responses.

    Args:
        responses: List of CliResponse objects

    Returns:
        Agreement level from 0.0 (no agreement) to 1.0 (full agreement)
    """
    if not responses:
        return 0.0

    if len(responses) == 1:
        return 1.0

    # Simple agreement based on output similarity
    # Compare first 500 chars of each output
    outputs = [r.output[:500] for r in responses if r.output]

    if not outputs:
        return 0.0

    # Count similar pairs
    similar_pairs = 0
    total_pairs = 0

    for i in range(len(outputs)):
        for j in range(i + 1, len(outputs)):
            total_pairs += 1
            # Simple similarity check: overlap ratio
            words_a = set(outputs[i].lower().split())
            words_b = set(outputs[j].lower().split())

            if not words_a or not words_b:
                continue

            intersection = words_a & words_b
            union = words_a | words_b
            similarity = len(intersection) / len(union)

            if similarity > 0.5:  # 50% similarity threshold
                similar_pairs += 1

    return similar_pairs / total_pairs if total_pairs > 0 else 0.0


def format_structured_output(
    responses: dict[str, dict[str, Any]],
    query: str,
    context_files: list[str],
    total_time_ms: int,
) -> AggregatedResponse:
    """Format structured output from raw CLI results.

    Args:
        responses: Raw results dict from run_parallel_llm
        query: Original query
        context_files: List of context files used
        total_time_ms: Total execution time

    Returns:
        AggregatedResponse with structured data
    """
    cli_responses = {}

    for cli_name, cli_data in responses.items():
        if not isinstance(cli_data, dict):
            continue

        output = cli_data.get("output", "")
        error = cli_data.get("error")
        response_time = cli_data.get("response_time_ms", 0)
        success = not bool(error)

        cli_response = build_structured_response(
            cli_name=cli_name,
            output=output,
            error=error,
            response_time_ms=response_time,
            success=success,
        )

        cli_responses[cli_name] = cli_response

    # Calculate agreement
    response_list = list(cli_responses.values())
    agreement = calculate_agreement_level(response_list)

    # Build consensus from most common elements
    consensus = None
    if agreement > 0.7 and response_list:
        # High agreement - use first successful response as consensus
        for r in response_list:
            if r.success and r.output:
                consensus = r.output[:500]
                break

    return AggregatedResponse(
        query=query,
        timestamp=datetime.now().isoformat(),
        cli_responses=cli_responses,
        consensus=consensus,
        agreement_level=agreement,
        total_response_time_ms=total_time_ms,
        context_files=context_files,
        metadata={
            "cli_count": len(cli_responses),
            "successful_clis": sum(1 for r in response_list if r.success),
            "failed_clis": sum(1 for r in response_list if not r.success),
            "total_findings": sum(len(r.findings) for r in response_list),
        },
    )

```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\task_classifier.py
```python
"""Task type classifier for LLM CLI queries.

Classifies user queries into task types (code_review, planning, brainstorm, etc.)
using keyword matching. Provides confidence scoring and matched keywords for analysis.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TaskType(Enum):
    """LLM task types for classification and routing.

    Each task type maps to specific prompt templates for better LLM responses.
    """

    CODE_REVIEW = "code_review"
    PLANNING = "planning"
    BRAINSTORM = "brainstorm"
    RESEARCH = "research"
    DEBUG = "debug"
    REFACTOR = "refactor"
    GENERAL = "general"


@dataclass
class ClassificationResult:
    """Result of task classification.

    Attributes:
        task_type: The classified task type
        confidence: Confidence score 0.0 to 1.0 based on keyword matches
        matched_keywords: List of keywords that triggered this classification
        reasoning: Human-readable explanation of the classification
    """

    task_type: TaskType
    confidence: float
    matched_keywords: list[str]
    reasoning: str


# Keyword patterns for each task type
# Based on /llm-route documented patterns and enhanced for comprehensive coverage
TASK_PATTERNS = {
    TaskType.CODE_REVIEW: [
        "review",
        "analyze",
        "audit",
        "gaps",
        "opportunities",
        "findings",
        "inspect",
        "examine",
        "assess",
        "evaluate code",
        "code review",
        "what's wrong with",
        "improve this code",
    ],
    TaskType.PLANNING: [
        "plan",
        "strategy",
        "roadmap",
        "architecture",
        "design",
        "approach",
        "outline",
        "structure",
        "organize",
        "implementation plan",
        "steps to",
        "how should i implement",
    ],
    TaskType.BRAINSTORM: [
        "brainstorm",
        "ideas",
        "suggest",
        "creative",
        "innovative",
        "explore",
        "what if",
        "alternatives",
        "options",
        "come up with",
        "think of",
        "different ways to",
    ],
    TaskType.RESEARCH: [
        "research",
        "investigate",
        "find information",
        "lookup",
        "search",
        "explain",
        "what is",
        "how does",
        "compare",
        "tell me about",
        "describe",
        "documentation",
    ],
    TaskType.DEBUG: [
        "debug",
        "fix",
        "error",
        "bug",
        "issue",
        "problem",
        "not working",
        "broken",
        "failure",
        "crash",
        "why is this failing",
        "what's wrong",
        "troubleshoot",
    ],
    TaskType.REFACTOR: [
        "refactor",
        "improve",
        "optimize",
        "clean up",
        "simplify",
        "restructure",
        "reorganize",
        "make better",
        "make this more readable",
        "reduce complexity",
    ],
}


def classify_task(query: str) -> ClassificationResult:
    """Classify query into task type using keyword matching.

    Uses deterministic keyword matching (not ML-based) to ensure
    consistent, explainable classifications. Logs all matched keywords
    for performance analysis.

    Args:
        query: User query string

    Returns:
        ClassificationResult with task type, confidence, and reasoning
    """
    query_lower = query.lower()

    # Score each task type by keyword matches
    scores = {}
    matched = {}
    for task_type, keywords in TASK_PATTERNS.items():
        matches = [kw for kw in keywords if kw in query_lower]
        if matches:
            scores[task_type] = len(matches)
            matched[task_type] = matches

    if not scores:
        return ClassificationResult(
            task_type=TaskType.GENERAL,
            confidence=0.0,
            matched_keywords=[],
            reasoning="No task type keywords detected",
        )

    # Return highest-scoring task type
    best_task = max(scores.items(), key=lambda x: x[1])[0]
    match_count = scores[best_task]

    # Confidence: 0.2 per keyword match, max 1.0 at 5+ matches
    confidence = min(match_count * 0.2, 1.0)

    return ClassificationResult(
        task_type=best_task,
        confidence=confidence,
        matched_keywords=matched[best_task],
        reasoning=f"Matched {match_count} keywords for {best_task.value}: {', '.join(matched[best_task][:3])}{'...' if len(matched[best_task]) > 3 else ''}",
    )


# Test function for development
def _test_classification():
    """Test task classification with sample queries."""
    test_queries = [
        ("review this code for bugs", TaskType.CODE_REVIEW),
        ("create a plan for implementing X", TaskType.PLANNING),
        ("brainstorm ideas for feature Y", TaskType.BRAINSTORM),
        ("research best practices for Z", TaskType.RESEARCH),
        ("debug this error in module.py", TaskType.DEBUG),
        ("refactor this function for clarity", TaskType.REFACTOR),
        ("what is 12 + 12?", TaskType.GENERAL),
    ]

    print("Task Classification Tests:")
    print("-" * 60)
    for query, expected in test_queries:
        result = classify_task(query)
        status = "✓" if result.task_type == expected else "✗"
        print(f"{status} {query}")
        print(f"  → {result.task_type.value} (confidence: {result.confidence:.2f})")
        print(f"  → {result.reasoning}")
        print()


if __name__ == "__main__":
    _test_classification()

```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\tests\test_ai_cli_critic_prompt.py
```python
"""Regression tests for the ai-cli critic prompt guardrails."""

from __future__ import annotations

from pathlib import Path


def test_ai_cli_critic_prompt_contains_strict_guardrails():
    prompt = Path("P:/.claude/agents/ai-cli-critic.md").read_text(encoding="utf-8")

    assert "hallucinated file paths, flags, APIs, or facts" in prompt
    assert "Treat consensus as a signal only, never as proof" in prompt
    assert "Do not downgrade unsupported claims just because multiple models agreed" in prompt
    assert "Do not accept invented file paths, line numbers, or flags" in prompt
    assert "grounding_status" in prompt

```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\tests\test_opencode_model_aliases.py
```python
"""Tests for OpenCode model alias resolution."""

from ai_cli import DEFAULT_OPENCODE_MODEL, _resolve_opencode_model


class TestOpenCodeModelAliases:
    """Test model alias resolution function."""

    def test_kimi_alias_resolves(self):
        """Kimi alias resolves to full Kimi K2.5 TEE model ID."""
        result = _resolve_opencode_model("kimi")
        assert result == "chutes/moonshotai/Kimi-K2.5-TEE"

    def test_minimax_alias_resolves(self):
        """MiniMax alias resolves to full MiniMax M2.1 TEE model ID."""
        result = _resolve_opencode_model("minimax")
        assert result == "chutes/MiniMaxAI/MiniMax-M2.1-TEE"

    def test_full_model_id_passthrough(self):
        """Full model ID is passed through unchanged."""
        custom_id = "chutes/custom/model"
        result = _resolve_opencode_model(custom_id)
        assert result == custom_id

    def test_none_returns_default(self):
        """None input returns DEFAULT_OPENCODE_MODEL."""
        result = _resolve_opencode_model(None)
        assert result == DEFAULT_OPENCODE_MODEL

    def test_empty_string_returns_default(self):
        """Empty string input returns DEFAULT_OPENCODE_MODEL."""
        result = _resolve_opencode_model("")
        assert result == DEFAULT_OPENCODE_MODEL

    def test_unknown_alias_returns_as_is(self):
        """Unknown alias values are returned as-is (fallback behavior)."""
        unknown = "some_unknown_alias"
        result = _resolve_opencode_model(unknown)
        # Should return the input as-is when not in aliases dict and not empty/None
        assert result == unknown

```


---

## ADDITIONAL FILES (markdown)

### SKILL.md
```markdown
---
name: ai-pcli
version: "1.4.0"
status: stable
description: Parallel Multi-LLM Command with prompting-toolkit enhancement - Run qwen, gemini, codex, and opencode CLI tools in parallel
category: ai-llm
enforcement: strict
triggers:
  - /ai-pcli
workflow_steps:
  - Parse query and options
  - Build context from --context or auto-detection
  - Apply prompt enhancement (built-in or --prompt-toolkit)
  - Run parallel LLM CLIs
  - Aggregate outputs
  - Run ai-cli-critic unless --no-critic
---

# /ai-pcli

**Parallel multi-LLM command with prompting-toolkit:** `/ai-pcli` runs multiple CLI-backed model providers and aggregates their output.

## EXECUTION DIRECTIVE

**When invoked, check query type first:**

- If query is `"config"` (case-insensitive): Skip to Step 6
- Otherwise: Continue with Steps 1-4

**Step 1:** Run the CLI:
```bash
python "P:\.claude\skills\ai-cli\ai_cli.py" "{{user_query}}" {{options}}
```

**Step 2:** Wait for ALL model outputs to complete

**Step 3:** Report the aggregated CLI outputs verbatim

**Step 4:** Run `ai-cli-critic` on the combined output unless `--no-critic` is set

```text
Task(subagent_type="ai-cli-critic",
     description="Critic pass for /ai-cli outputs. Review the combined LLM outputs for unsupported claims, contradictions, overconfidence, and missing evidence. Use the saved JSON file if available, otherwise analyze the raw transcript.")
```

**Step 5:** If `--output-format json` is used, save the combined JSON to a datetime-suffixed output file and generate tiered YAML reports

**Step 6 (config query):** Read `P:/.claude/ai-cli-recipe.json` and display:
```
Active CLIs:
  Default:
    <cli1>
    <cli2>
    ...
  Aux / Enh:
    <cli> (<model>, failover to <failover>)
    ...
```
If no config file exists, display: `No saved configuration found`

**DO NOT:**
- Provide your own analysis instead of running the command
- Summarize this skill documentation
- Substitute your capabilities for the external LLM CLIs
- Consider the task complete until bash command output is captured
- Read files and analyze them yourself when user wants multi-LLM perspective

**DEFAULT (no arguments):**
```bash
python "P:\.claude\skills\ai-cli\ai_cli.py" --help
```

**If execution fails:** Report exact error message. Do NOT fabricate results or provide your own analysis as substitute.

---

## Quick Reference

| Option | Description |
|--------|-------------|
| `"<query>"` | Question or task (required, quoted) |
| `--context FILE` | File path to embed (RECOMMENDED for file analysis) |
| `--target FILE` | Target file to investigate (filters session context by relevance) |
| `--summary` | Brief key answers only |
| `--aggregate` | Consensus view showing agreement/disagreement |
| `--quality-weighted` | Quality-weighted output with consensus analysis and evidence validation |
| `--complete` | Full raw outputs |
| `--diff` | Show differences between CLI responses |
| `--quality-gate` | Apply 4-Layer Filter System Layer 4 (filters findings by confidence >= 80%) |
| `--output-format json` | Machine-readable JSON output |
| `--timeout N` | Max wait in seconds (default: auto-calculated) |
| `--output-file FILE` | Save JSON output to a datetime-suffixed file |
| `--no-critic` | Skip the post-run ai-cli critic subagent |
| `--prompt-toolkit` | Use prompting-toolkit AutomaticEnhancementSystem instead of built-in templates |
| `--qwen-only` | Run only qwen-cli |
| `--gemini-only` | Run only gemini-cli |
| `--codex-only` | Run only codex-cli |
| `--opencode-only` | Run only opencode (DeepSeek V3) |
| `--opencode-model MODEL` | OpenCode model or alias (kimi, minimax) |
| `--route` | Use rule-based routing (from llm-route) to select CLI by task keywords |
| `--doc-review` | Use document review prompt (from llm-doc_review) - prepends review questions |
| `--hide-prompt` | Suppress the enhanced prompt display (which is shown by default) |
| `-bash` | Show bash commands instead of executing (debug) |

---

## Critical Rules

1. **File context MUST use --context flag** - Piped stdin is ignored when auto-context detected
2. **Timeout protection:** Default auto-calculated (180s base + 1s per MB context)
3. **Individual failures don't abort others** - Report which CLIs succeeded/failed
4. **Empty responses are flagged as errors** - Don't silently accept blank output

---

## Output Display

For clean output format when using "config" query, see [references/output-template.md](references/output-template.md).

## References

| Topic | File |
|-------|------|
| Example invocations (basic, output modes, specific LLMs, advanced) | `references/examples.md` |
| 4-Layer Filter System / Quality Gate integration | `references/quality-gate.md` |
| Context handling best practices and auto-detection | `references/context-handling.md` |
| CLI characteristics, OpenCode models, setup, health check, limitations | `references/cli-reference.md` |
| Troubleshooting (errors, causes, fixes) | `references/troubleshooting.md` |
| Critic subagent for output sanity checks | `P:/.claude/agents/ai-cli-critic.md` |

```

### SKILL.md
```markdown
---
name: ai-pcli
version: "1.4.0"
status: stable
description: Parallel Multi-LLM Command with prompting-toolkit enhancement - Run qwen, gemini, codex, and opencode CLI tools in parallel
category: ai-llm
enforcement: strict
triggers:
  - /ai-pcli
workflow_steps:
  - Parse query and options
  - Build context from --context or auto-detection
  - Apply prompt enhancement (built-in or --prompt-toolkit)
  - Run parallel LLM CLIs
  - Aggregate outputs
  - Run ai-cli-critic unless --no-critic
---

# /ai-pcli

**Parallel multi-LLM command with prompting-toolkit:** `/ai-pcli` runs multiple CLI-backed model providers and aggregates their output.

## EXECUTION DIRECTIVE

**When invoked, check query type first:**

- If query is `"config"` (case-insensitive): Skip to Step 6
- Otherwise: Continue with Steps 1-4

**Step 1:** Run the CLI:
```bash
python "P:\.claude\skills\ai-cli\ai_cli.py" "{{user_query}}" {{options}}
```

**Step 2:** Wait for ALL model outputs to complete

**Step 3:** Report the aggregated CLI outputs verbatim

**Step 4:** Run `ai-cli-critic` on the combined output unless `--no-critic` is set

```text
Task(subagent_type="ai-cli-critic",
     description="Critic pass for /ai-cli outputs. Review the combined LLM outputs for unsupported claims, contradictions, overconfidence, and missing evidence. Use the saved JSON file if available, otherwise analyze the raw transcript.")
```

**Step 5:** If `--output-format json` is used, save the combined JSON to a datetime-suffixed output file and generate tiered YAML reports

**Step 6 (config query):** Read `P:/.claude/ai-cli-recipe.json` and display:
```
Active CLIs:
  Default:
    <cli1>
    <cli2>
    ...
  Aux / Enh:
    <cli> (<model>, failover to <failover>)
    ...
```
If no config file exists, display: `No saved configuration found`

**DO NOT:**
- Provide your own analysis instead of running the command
- Summarize this skill documentation
- Substitute your capabilities for the external LLM CLIs
- Consider the task complete until bash command output is captured
- Read files and analyze them yourself when user wants multi-LLM perspective

**DEFAULT (no arguments):**
```bash
python "P:\.claude\skills\ai-cli\ai_cli.py" --help
```

**If execution fails:** Report exact error message. Do NOT fabricate results or provide your own analysis as substitute.

---

## Quick Reference

| Option | Description |
|--------|-------------|
| `"<query>"` | Question or task (required, quoted) |
| `--context FILE` | File path to embed (RECOMMENDED for file analysis) |
| `--target FILE` | Target file to investigate (filters session context by relevance) |
| `--summary` | Brief key answers only |
| `--aggregate` | Consensus view showing agreement/disagreement |
| `--quality-weighted` | Quality-weighted output with consensus analysis and evidence validation |
| `--complete` | Full raw outputs |
| `--diff` | Show differences between CLI responses |
| `--quality-gate` | Apply 4-Layer Filter System Layer 4 (filters findings by confidence >= 80%) |
| `--output-format json` | Machine-readable JSON output |
| `--timeout N` | Max wait in seconds (default: auto-calculated) |
| `--output-file FILE` | Save JSON output to a datetime-suffixed file |
| `--no-critic` | Skip the post-run ai-cli critic subagent |
| `--prompt-toolkit` | Use prompting-toolkit AutomaticEnhancementSystem instead of built-in templates |
| `--qwen-only` | Run only qwen-cli |
| `--gemini-only` | Run only gemini-cli |
| `--codex-only` | Run only codex-cli |
| `--opencode-only` | Run only opencode (DeepSeek V3) |
| `--opencode-model MODEL` | OpenCode model or alias (kimi, minimax) |
| `--route` | Use rule-based routing (from llm-route) to select CLI by task keywords |
| `--doc-review` | Use document review prompt (from llm-doc_review) - prepends review questions |
| `--hide-prompt` | Suppress the enhanced prompt display (which is shown by default) |
| `-bash` | Show bash commands instead of executing (debug) |

---

## Critical Rules

1. **File context MUST use --context flag** - Piped stdin is ignored when auto-context detected
2. **Timeout protection:** Default auto-calculated (180s base + 1s per MB context)
3. **Individual failures don't abort others** - Report which CLIs succeeded/failed
4. **Empty responses are flagged as errors** - Don't silently accept blank output

---

## Output Display

For clean output format when using "config" query, see [references/output-template.md](references/output-template.md).

## References

| Topic | File |
|-------|------|
| Example invocations (basic, output modes, specific LLMs, advanced) | `references/examples.md` |
| 4-Layer Filter System / Quality Gate integration | `references/quality-gate.md` |
| Context handling best practices and auto-detection | `references/context-handling.md` |
| CLI characteristics, OpenCode models, setup, health check, limitations | `references/cli-reference.md` |
| Troubleshooting (errors, causes, fixes) | `references/troubleshooting.md` |
| Critic subagent for output sanity checks | `P:/.claude/agents/ai-cli-critic.md` |

```

## .aid\ai-pcli\ai-pcli_sig.md
# ai-pcli — LLM-READY PACK

<!-- Generated by gitpack.py (pure Python) -->

## PACK INFO
- **Files:** 13 files
- **Mode:** signatures only
- **Generated:** 2026-04-27 18:13 UTC

## HOW TO USE

This is the signatures-only pack. For full implementations, see the
corresponding `_full.md` file.

## SIGNATURE TOC

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\ai_cli.py
```python
_load_ai_cli_config() -> dict[str, Any] | None
_save_ai_cli_config(clis: list[str], opencode_models: list[str]) -> None
_clear_ai_cli_config() -> None
_substitute_gemini_model(cmd_list: list[str], model: str) -> list[str]
_get_repo_root() -> Path
_cleanup_old_cli_results(days_to_keep: int) -> None
route_query_to_clis(query: str) -> list[str]
_apply_quality_gate_filter(results: dict[Any], query: str, min_confidence: int)
_resolve_opencode_model(model: str | None) -> str
get_glm_api_key() -> str
mask_api_key(key: str) -> str
_is_in_workspace(path_str: str) -> bool
_read_context_file(file_path: str, allowed_root: Path | None) -> str
_add_datetime_suffix(file_path: str) -> str
_copy_to_tmp_if_needed(file_path: Path) -> Path
_format_session_history(session_file: Path, after_timestamp: float | None, max_entries: int)
_find_session_by_marker(marker: str) -> str | None
_get_auto_context() -> str
get_context(context_source: str | None, auto_context: bool, cli_name: str | None)
detect_session_context(wt_session: str | None) -> str
_read_multi_file_context(context_source: str, cli_name: str | None) -> str
generate_parallel_bash_commands(query: str, qwen_only: bool, gemini_only: bool, codex_only: bool)
_parse_opencode_streaming_json(output: str) -> str
_determine_active_llms(qwen_only: bool, gemini_only: bool, codex_only: bool, opencode_only: bool, glm_flash_only: bool, pi_m27_only: bool, pi_glm_only: bool, copilot_only: bool)
_get_cli_preview(qwen_only: bool, gemini_only: bool, codex_only: bool, opencode_only: bool, glm_flash_only: bool, opencode_models: list[str], pi_m27_only: bool, pi_glm_only: bool, copilot_only: bool)
_build_cli_commands(query: str, run_qwen: bool, run_gemini: bool, run_codex: bool, run_opencode: bool, opencode_models: list[str], run_pi_m27: bool, run_pi_glm: bool, run_copilot: bool, context_file: str | None)
_execute_glm_api_mode(query: str, timeout: int, verbose: bool)
_process_llm_results(raw_results: dict[Any])
run_parallel_llm(query: str, qwen_only: bool, gemini_only: bool, codex_only: bool, opencode_only: bool, glm_flash_only: bool, pi_m27_only: bool, pi_glm_only: bool, copilot_only: bool, timeout: int, output_format: str, verbose: bool, opencode_models: list[str], context_file: str | None)
async run_all_parallel()
expand_prompt(query: str) -> str
show_prompt_options(expanded_prompt: str, original_prompt: str) -> str
prompt_with_expansion_option(original_query: str) -> str
_extract_issues_by_priority(outputs: list[str]) -> dict[str, list[str]]
_format_progressive_selections(issues: dict[Any]) -> str
format_results(results: dict[Any]) -> str
_extract_qwen_answer(output: str) -> str
_extract_gemini_answer(output: str) -> str
_extract_codex_answer(output: str) -> str
_extract_answer(cli_name: str, output: str) -> str
format_summary(results: dict[Any]) -> str
format_aggregate(results: dict[Any]) -> str
format_complete(results: dict[Any]) -> str
format_diff(results: dict[Any]) -> str
format_quality_weighted(results: dict[Any]) -> str
_detect_review_query(query: str) -> bool
_extract_file_paths_from_query(query: str) -> list[str]
_get_git_changed_files() -> list[str]
_smart_auto_context(query: str) -> str | None
_build_query_context(args: argparse.Namespace, query: str) -> tuple[str, str]
_create_tiered_reports(results: dict[Any]) -> None
_extract_finding_signature(content: str) -> str
_deduplicate_findings_cli(all_findings: list[dict]) -> tuple[list[dict], dict]
_deduplicate_findings(findings: list[dict], priority_order: dict[Any]) -> list[dict]
_extract_all_findings(cli_data: Any, cli_name: str, min_confidence: int) -> list[dict]
extract_recursive(obj: Any, path: str) -> None
_extract_text_findings_all(output: str, cli_name: str) -> list[dict]
_extract_from_full_output(cli_name: str, output: str) -> list[dict]
_write_output(results: dict[Any], args: argparse.Namespace) -> None
async _run_domain_query(domain: str, query: str, context: str | None, refresh_benchmarks: bool)
async run_model_with_native_cli_or_opencode(model_info: ModelInfo) -> dict[str, Any]
main()
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\file_context.py
```python
resolve_path(path_str: str) -> Path
collect_files_from_paths(paths: list[str], extensions: list[str] | None, max_files: int)
_iter_files_recursive(directory: Path, extensions: list[str] | None)
read_file_content_safe(file_path: Path, max_size: int)
create_repo_map(files: list[Path]) -> str
format_files_for_llm(files: list[Path], use_repo_map: bool)
build_context_from_paths(paths: list[str], extensions: list[str] | None, use_repo_map: bool)
print_context_summary(metadata: dict[Any]) -> None
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\performance_logger.py
```python
class CliExecutionRecord
to_jsonl(self) -> str
class CliPerformanceLogger
__init__(self, log_path: str | None)
log_execution(self, cli_name: str, task_type: TaskType, query: str, duration_seconds: float, outcome: Literal[Any], output_length: int, error_message: str | None)
get_all_records(self) -> list[CliExecutionRecord]
get_records_for_task(self, task_type: TaskType) -> list[CliExecutionRecord]
get_records_for_cli(self, cli_name: str) -> list[CliExecutionRecord]
get_performance_stats(self, task_type: TaskType | None) -> dict
_test_performance_logger()
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\prompt_templates.py
```python
build_prompt(query: str, task_type: TaskType, context: str | None)
_test_prompt_building()
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\__init__.py
```python
# (no public definitions)
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\analyze_security.py
```python
analyze_file(file_path: str, output_file: str) -> str
main()
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\cli.py
```python
cmd_health(args: argparse.Namespace) -> int
cmd_models(args: argparse.Namespace) -> int
cmd_list(args: argparse.Namespace) -> int
build_parser() -> argparse.ArgumentParser
main() -> int
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\cli_detector.py
```python
_get_npm_root() -> Path
_get_npm_cli_path(cli_info: dict[Any]) -> Path | None
_build_cli_command(cli_id: str, cli_info: dict[Any]) -> list[str]
_run_cli_command(cli_id: str, command_parts: list[str], timeout: int) -> dict[str, Any]
_extract_version(output: str) -> str | None
check_cli_installation(cli_id: str) -> dict[str, Any]
check_env_vars() -> dict[str, dict[str, Any]]
get_all_cli_status() -> dict[str, dict[str, Any]]
format_cli_status_table(status: dict[Any]) -> str
format_env_var_status(env_status: dict[Any]) -> str
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\filter_models.py
```python
get_cached_models() -> str | None
save_to_cache(data: str) -> None
fetch_models(force_refresh: bool) -> str
main()
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\structured_response.py
```python
class TokenUsage
to_dict(self) -> dict[str, int]
class SourceMetadata
class Finding
to_dict(self) -> dict[str, Any]
class CliResponse
to_dict(self) -> dict[str, Any]
class QualityGateResult
to_dict(self) -> dict[str, Any]
class AggregatedResponse
to_dict(self) -> dict[str, Any]
to_json(self, indent: int) -> str
extract_token_usage(output: str) -> TokenUsage
extract_model_id(output: str, cli_name: str) -> str | None
extract_findings_from_text(output: str, cli_name: str, model_id: str | None)
extract_findings_from_json(json_output: str | dict, cli_name: str, model_id: str | None)
build_structured_response(cli_name: str, output: str, error: str | None, response_time_ms: int, success: bool)
calculate_agreement_level(responses: list[CliResponse]) -> float
format_structured_output(responses: dict[Any], query: str, context_files: list[str], total_time_ms: int)
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\task_classifier.py
```python
class TaskType
class ClassificationResult
classify_task(query: str) -> ClassificationResult
_test_classification()
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\tests\test_ai_cli_critic_prompt.py
```python
test_ai_cli_critic_prompt_contains_strict_guardrails()
```

### P:\packages\cc-skills-ai-cli\skills\ai-pcli\tests\test_opencode_model_aliases.py
```python
class TestOpenCodeModelAliases
test_kimi_alias_resolves(self)
test_minimax_alias_resolves(self)
test_full_model_id_passthrough(self)
test_none_returns_default(self)
test_empty_string_returns_default(self)
test_unknown_alias_returns_as_is(self)
```

## DIRECTORY INDEX

| Directory | Files |
|---------|-------|
| `ai-pcli/` | 6 |
| `scripts/` | 5 |
| `tests/` | 2 |
## DIRECTORY TREE

```
ai-pcli/ (13 files)
├── scripts/ (5)
│   ├── __init__.py
│   ├── analyze_security.py
│   ├── cli.py
│   ├── cli_detector.py
│   └── filter_models.py
├── tests/ (2)
│   ├── test_ai_cli_critic_prompt.py
│   └── test_opencode_model_aliases.py
├── ai_cli.py
├── file_context.py
├── performance_logger.py
├── prompt_templates.py
├── structured_response.py
└── task_classifier.py
```

## FILE INDEX

| File | Description |
|------|-------------|
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\ai_cli.py` | ai cli |
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\file_context.py` | file context |
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\performance_logger.py` | performance logger |
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\prompt_templates.py` | prompt templates |
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\__init__.py` | Package: scripts |
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\analyze_security.py` | analyze security |
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\cli.py` | cli |
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\cli_detector.py` | cli detector |
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\scripts\filter_models.py` | filter models |
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\structured_response.py` | structured response |
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\task_classifier.py` | task classifier |
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\tests\test_ai_cli_critic_prompt.py` | test ai cli critic prompt |
| `P:\packages\cc-skills-ai-cli\skills\ai-pcli\tests\test_opencode_model_aliases.py` | test opencode model aliases |

---

## ADDITIONAL FILES (markdown)

### SKILL.md
```markdown
---
name: ai-pcli
version: "1.4.0"
status: stable
description: Parallel Multi-LLM Command with prompting-toolkit enhancement - Run qwen, gemini, codex, and opencode CLI tools in parallel
category: ai-llm
enforcement: strict
triggers:
  - /ai-pcli
workflow_steps:
  - Parse query and options
  - Build context from --context or auto-detection
  - Apply prompt enhancement (built-in or --prompt-toolkit)
  - Run parallel LLM CLIs
  - Aggregate outputs
  - Run ai-cli-critic unless --no-critic
---

# /ai-pcli

**Parallel multi-LLM command with prompting-toolkit:** `/ai-pcli` runs multiple CLI-backed model providers and aggregates their output.

## EXECUTION DIRECTIVE

**When invoked, check query type first:**

- If query is `"config"` (case-insensitive): Skip to Step 6
- Otherwise: Continue with Steps 1-4

**Step 1:** Run the CLI:
```bash
python "P:\.claude\skills\ai-cli\ai_cli.py" "{{user_query}}" {{options}}
```

**Step 2:** Wait for ALL model outputs to complete

**Step 3:** Report the aggregated CLI outputs verbatim

**Step 4:** Run `ai-cli-critic` on the combined output unless `--no-critic` is set

```text
Task(subagent_type="ai-cli-critic",
     description="Critic pass for /ai-cli outputs. Review the combined LLM outputs for unsupported claims, contradictions, overconfidence, and missing evidence. Use the saved JSON file if available, otherwise analyze the raw transcript.")
```

**Step 5:** If `--output-format json` is used, save the combined JSON to a datetime-suffixed output file and generate tiered YAML reports

**Step 6 (config query):** Read `P:/.claude/ai-cli-recipe.json` and display:
```
Active CLIs:
  Default:
    <cli1>
    <cli2>
    ...
  Aux / Enh:
    <cli> (<model>, failover to <failover>)
    ...
```
If no config file exists, display: `No saved configuration found`

**DO NOT:**
- Provide your own analysis instead of running the command
- Summarize this skill documentation
- Substitute your capabilities for the external LLM CLIs
- Consider the task complete until bash command output is captured
- Read files and analyze them yourself when user wants multi-LLM perspective

**DEFAULT (no arguments):**
```bash
python "P:\.claude\skills\ai-cli\ai_cli.py" --help
```

**If execution fails:** Report exact error message. Do NOT fabricate results or provide your own analysis as substitute.

---

## Quick Reference

| Option | Description |
|--------|-------------|
| `"<query>"` | Question or task (required, quoted) |
| `--context FILE` | File path to embed (RECOMMENDED for file analysis) |
| `--target FILE` | Target file to investigate (filters session context by relevance) |
| `--summary` | Brief key answers only |
| `--aggregate` | Consensus view showing agreement/disagreement |
| `--quality-weighted` | Quality-weighted output with consensus analysis and evidence validation |
| `--complete` | Full raw outputs |
| `--diff` | Show differences between CLI responses |
| `--quality-gate` | Apply 4-Layer Filter System Layer 4 (filters findings by confidence >= 80%) |
| `--output-format json` | Machine-readable JSON output |
| `--timeout N` | Max wait in seconds (default: auto-calculated) |
| `--output-file FILE` | Save JSON output to a datetime-suffixed file |
| `--no-critic` | Skip the post-run ai-cli critic subagent |
| `--prompt-toolkit` | Use prompting-toolkit AutomaticEnhancementSystem instead of built-in templates |
| `--qwen-only` | Run only qwen-cli |
| `--gemini-only` | Run only gemini-cli |
| `--codex-only` | Run only codex-cli |
| `--opencode-only` | Run only opencode (DeepSeek V3) |
| `--opencode-model MODEL` | OpenCode model or alias (kimi, minimax) |
| `--route` | Use rule-based routing (from llm-route) to select CLI by task keywords |
| `--doc-review` | Use document review prompt (from llm-doc_review) - prepends review questions |
| `--hide-prompt` | Suppress the enhanced prompt display (which is shown by default) |
| `-bash` | Show bash commands instead of executing (debug) |

---

## Critical Rules

1. **File context MUST use --context flag** - Piped stdin is ignored when auto-context detected
2. **Timeout protection:** Default auto-calculated (180s base + 1s per MB context)
3. **Individual failures don't abort others** - Report which CLIs succeeded/failed
4. **Empty responses are flagged as errors** - Don't silently accept blank output

---

## Output Display

For clean output format when using "config" query, see [references/output-template.md](references/output-template.md).

## References

| Topic | File |
|-------|------|
| Example invocations (basic, output modes, specific LLMs, advanced) | `references/examples.md` |
| 4-Layer Filter System / Quality Gate integration | `references/quality-gate.md` |
| Context handling best practices and auto-detection | `references/context-handling.md` |
| CLI characteristics, OpenCode models, setup, health check, limitations | `references/cli-reference.md` |
| Troubleshooting (errors, causes, fixes) | `references/troubleshooting.md` |
| Critic subagent for output sanity checks | `P:/.claude/agents/ai-cli-critic.md` |

```

### SKILL.md
```markdown
---
name: ai-pcli
version: "1.4.0"
status: stable
description: Parallel Multi-LLM Command with prompting-toolkit enhancement - Run qwen, gemini, codex, and opencode CLI tools in parallel
category: ai-llm
enforcement: strict
triggers:
  - /ai-pcli
workflow_steps:
  - Parse query and options
  - Build context from --context or auto-detection
  - Apply prompt enhancement (built-in or --prompt-toolkit)
  - Run parallel LLM CLIs
  - Aggregate outputs
  - Run ai-cli-critic unless --no-critic
---

# /ai-pcli

**Parallel multi-LLM command with prompting-toolkit:** `/ai-pcli` runs multiple CLI-backed model providers and aggregates their output.

## EXECUTION DIRECTIVE

**When invoked, check query type first:**

- If query is `"config"` (case-insensitive): Skip to Step 6
- Otherwise: Continue with Steps 1-4

**Step 1:** Run the CLI:
```bash
python "P:\.claude\skills\ai-cli\ai_cli.py" "{{user_query}}" {{options}}
```

**Step 2:** Wait for ALL model outputs to complete

**Step 3:** Report the aggregated CLI outputs verbatim

**Step 4:** Run `ai-cli-critic` on the combined output unless `--no-critic` is set

```text
Task(subagent_type="ai-cli-critic",
     description="Critic pass for /ai-cli outputs. Review the combined LLM outputs for unsupported claims, contradictions, overconfidence, and missing evidence. Use the saved JSON file if available, otherwise analyze the raw transcript.")
```

**Step 5:** If `--output-format json` is used, save the combined JSON to a datetime-suffixed output file and generate tiered YAML reports

**Step 6 (config query):** Read `P:/.claude/ai-cli-recipe.json` and display:
```
Active CLIs:
  Default:
    <cli1>
    <cli2>
    ...
  Aux / Enh:
    <cli> (<model>, failover to <failover>)
    ...
```
If no config file exists, display: `No saved configuration found`

**DO NOT:**
- Provide your own analysis instead of running the command
- Summarize this skill documentation
- Substitute your capabilities for the external LLM CLIs
- Consider the task complete until bash command output is captured
- Read files and analyze them yourself when user wants multi-LLM perspective

**DEFAULT (no arguments):**
```bash
python "P:\.claude\skills\ai-cli\ai_cli.py" --help
```

**If execution fails:** Report exact error message. Do NOT fabricate results or provide your own analysis as substitute.

---

## Quick Reference

| Option | Description |
|--------|-------------|
| `"<query>"` | Question or task (required, quoted) |
| `--context FILE` | File path to embed (RECOMMENDED for file analysis) |
| `--target FILE` | Target file to investigate (filters session context by relevance) |
| `--summary` | Brief key answers only |
| `--aggregate` | Consensus view showing agreement/disagreement |
| `--quality-weighted` | Quality-weighted output with consensus analysis and evidence validation |
| `--complete` | Full raw outputs |
| `--diff` | Show differences between CLI responses |
| `--quality-gate` | Apply 4-Layer Filter System Layer 4 (filters findings by confidence >= 80%) |
| `--output-format json` | Machine-readable JSON output |
| `--timeout N` | Max wait in seconds (default: auto-calculated) |
| `--output-file FILE` | Save JSON output to a datetime-suffixed file |
| `--no-critic` | Skip the post-run ai-cli critic subagent |
| `--prompt-toolkit` | Use prompting-toolkit AutomaticEnhancementSystem instead of built-in templates |
| `--qwen-only` | Run only qwen-cli |
| `--gemini-only` | Run only gemini-cli |
| `--codex-only` | Run only codex-cli |
| `--opencode-only` | Run only opencode (DeepSeek V3) |
| `--opencode-model MODEL` | OpenCode model or alias (kimi, minimax) |
| `--route` | Use rule-based routing (from llm-route) to select CLI by task keywords |
| `--doc-review` | Use document review prompt (from llm-doc_review) - prepends review questions |
| `--hide-prompt` | Suppress the enhanced prompt display (which is shown by default) |
| `-bash` | Show bash commands instead of executing (debug) |

---

## Critical Rules

1. **File context MUST use --context flag** - Piped stdin is ignored when auto-context detected
2. **Timeout protection:** Default auto-calculated (180s base + 1s per MB context)
3. **Individual failures don't abort others** - Report which CLIs succeeded/failed
4. **Empty responses are flagged as errors** - Don't silently accept blank output

---

## Output Display

For clean output format when using "config" query, see [references/output-template.md](references/output-template.md).

## References

| Topic | File |
|-------|------|
| Example invocations (basic, output modes, specific LLMs, advanced) | `references/examples.md` |
| 4-Layer Filter System / Quality Gate integration | `references/quality-gate.md` |
| Context handling best practices and auto-detection | `references/context-handling.md` |
| CLI characteristics, OpenCode models, setup, health check, limitations | `references/cli-reference.md` |
| Troubleshooting (errors, causes, fixes) | `references/troubleshooting.md` |
| Critic subagent for output sanity checks | `P:/.claude/agents/ai-cli-critic.md` |

```

## .aid\ai-pcli.md
# ai-pcli — distilled (11 files, 74 kB → 18 kB, 75.6% compression)

## ai_cli.py

```python
# Core execution
run_parallel_llm(query: str, qwen_only=False, gemini_only=False, codex_only=False,
    opencode_only=False, glm_flash_only=False, pi_m27_only=False, pi_glm_only=False,
    copilot_only=False, timeout=180, output_format="text", verbose=False,
    opencode_models=[], context_file=None) -> dict[str, Any]
route_query_to_clis(query: str) -> list[str]
expand_prompt(query: str) -> str
format_results / format_summary / format_aggregate / format_complete / format_diff / format_quality_weighted(results: dict) -> str

# Routing rules
ROUTING_RULES = {
    "codex":  ["api", "function", "code", "implement", "refactor"],
    "qwen":   ["analyze", "compare", "evaluate"],
    "gemini": ["whole codebase", "entire project", "all files", "large context"],
    "opencode": ["plan", "strategy", "roadmap", "architecture", "creative", "write", "story"],
}
```

## file_context.py

```python
build_context_from_paths(paths: list[str], extensions=None, use_repo_map=False)
    -> tuple[str, dict[str, Any]]  # (context_str, metadata)
collect_files_from_paths(paths, extensions=None, max_files=20) -> list[Path]
format_files_for_llm(files: list[Path], use_repo_map=False) -> str
```

## performance_logger.py

```python
@dataclass CliExecutionRecord:
    timestamp, cli_name, task_type, query_preview, duration_seconds, outcome, output_length
class CliPerformanceLogger:
    log_execution(cli_name, task_type, query, duration_seconds, outcome, output_length, error_message=None)
    get_all_records() / get_records_for_task(task_type) / get_records_for_cli(cli_name)
    get_performance_stats(task_type=None) -> dict
```

## prompt_templates.py

```python
class TaskType(Enum):
    CODE_REVIEW, PLANNING, BRAINSTORM, RESEARCH, DEBUG, REFACTOR, GENERAL

SOLO_DEV_CONSTRAINTS = "solo-dev environment: single developer, simple>enterprise,
    pragmatic>comprehensive, local>CI, avoid over-engineering"

PROMPT_TEMPLATES: dict[TaskType, str]  # per-task prompt with output format specs
build_prompt(query: str, task_type: TaskType, context: str | None = None) -> str
```

## task_classifier.py

```python
class TaskType(Enum): CODE_REVIEW, PLANNING, BRAINSTORM, RESEARCH, DEBUG, REFACTOR, GENERAL
classify_task(query: str) -> ClassificationResult  # (task_type, confidence, matched_keywords, reasoning)
```

## structured_response.py

```python
@dataclass Finding: category, severity, title, description
@dataclass CliResponse: cli_name
@dataclass AggregatedResponse: query, timestamp
extract_findings_from_text/json(output, cli_name, model_id=None) -> list[Finding]
build_structured_response(cli_name, output, error=None, response_time_ms=0, success=True) -> CliResponse
calculate_agreement_level(responses: list[CliResponse]) -> float
format_structured_output(responses, query, context_files, total_time_ms) -> AggregatedResponse
```

## cli_detector.py

```python
CLI_TOOLS = {  # npm-based: qwen, gemini, codex, pi
    "qwen":   {"command": "qwen",    "install": "npm install -g qwen-code"},
    "gemini": {"command": "gemini",   "install": "npm install -g @google/gemini-cli"},
    "codex":  {"command": "codex",   "install": "npm install -g @openai/codex"},
    "pi":     {"command": "pi",      "install": "npm install -g @mariozechner/pi-coding-agent"},
}
ENV_VARS = {"CHUTES_API_KEY", "ZAI_API_KEY"}
check_cli_installation(cli_id) / check_env_vars() / get_all_cli_status() -> dict
```

## scripts/cli.py

```python
cmd_health / cmd_models / cmd_list(args) -> int
build_parser() -> argparse.ArgumentParser
```

## scripts/filter_models.py

```python
BROKEN_MODELS = {"openrouter/openrouter/sherlock-dash-alpha", ...}
CACHE_FILE = ~/.cache/ai-cli/opencode_models.txt (12h TTL)
get_cached_models() / save_to_cache(data) / fetch_models(force_refresh=False) -> str
```

## scripts/analyze_security.py

```python
analyze_file(file_path: str, output_file: str = None) -> str
```


