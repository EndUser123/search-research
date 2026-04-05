# Hooks Catalog v3 (Runtime Truth)

Last updated: 2026-03-03  
Scope: what is actively wired in `P:/.claude/settings.json` and what each active router actually executes.

## 1) Active Hook Entry Points (settings.json)

Only these hook commands are registered today:

- `UserPromptSubmit`:
  - `python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/UserPromptSubmit.py --timeout 15.0`
- `PreToolUse`: (matcher: `.*`)
  - `python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/PreToolUse.py --timeout 15.0`
- `PostToolUse`:
  - `python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/PostToolUse_router.py`
- `Notification`:
  - `powershell -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File .claude/hooks/voice_notifications.ps1`
- `Stop`:
  - `python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/Stop.py --timeout 5.0`
- `PreCompact`:
  - `python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/PreCompact.py`
- `SessionStart`:
  - `python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/SessionStart.py --timeout 30.0`
- `SessionEnd`:
  - no hooks configured

## 2) UserPromptSubmit Router (`UserPromptSubmit.py`)

Router model: modular registry (`UserPromptSubmit/registry.py`) + pushback + next-step menu handling.

Registered local modules:

- `active_command_writer` (priority `1.0`)
- `competence_injector` (`7.0`)
- `anti_sycophancy_injector` (`9.0`)
- `skill_enforcer` (`10.0`)
- `plan_injector` (`10.1`)
- `diagnostic_guard` (`10.2`)
- `unified_injector` (`11.0`)

Also attempts to load external package hook:

- `prompt_enhancement.hook` (if package import succeeds)

## 3) PreToolUse Router (`PreToolUse.py`)

Global pre-gate:

- in-process skill-first gate (`_check_skill_first_gate`) before all tool hooks
- terminal pinning (`_pin_terminal_env`) for multi-terminal scope stability

Universal hook list:

- `PreToolUse_path_validator.py`

Tool-specific hook lists:

- `Write`:
  - `PreToolUse_directory_policy.py`
  - `PreToolUse_syntax_gate.py`
  - `recursive_failure_detector.py`
  - `PreToolUse_git_safety.py`
- `Edit`:
  - `PreToolUse_directory_policy.py`
  - `recursive_failure_detector.py`
  - `PreToolUse_git_safety.py`
- `MultiEdit`:
  - `PreToolUse_directory_policy.py`
- `Bash`:
  - `PreToolUse_destructive_git_guard.py`
  - `PreToolUse_authorization_gate.py`
  - `PreToolUse_bulk_delete_gate.py`
  - `PreToolUse_python_c_validator.py`
  - `recursive_failure_detector.py`
  - `PreToolUse_command_intent_gate.py`
- `Task`:
  - `PreToolUse_authorization_gate.py`

In-process optimizations currently mapped:

- `PreToolUse_path_validator.py`
- `PreToolUse_directory_policy.py`
- `PreToolUse_bulk_delete_gate.py`
- `PreToolUse_destructive_git_guard.py`
- `PreToolUse_syntax_gate.py` (via `pre_tool_use_logic`)
- `recursive_failure_detector.py` (via `pre_tool_use_logic`)
- `PreToolUse_python_c_validator.py` (via `pre_tool_use_logic`)

## 4) PostToolUse Router (`PostToolUse_router.py`)

Top-level router behavior:

- session/terminal context pinning
- evidence/tool tracking (best effort)
- skill-handshake state clearing
- contract auto-seed on successful `Skill(...)` (`_ensure_contract_after_skill_load`)
- error signal write (`P:/.claude/state/signals/last_tool_error.json`)
- auto-commit side effect for non-read-only tools

In-process posttooluse registry (`posttooluse.create_registry()`):

- `fix_validator`
- `falsification_assessor`
- `semantic_compress`
- `error_attribution_tracker`
- `skill_execution_tracker`
- `investigation_tracker`
- `evidence_tracker`
- `failure_recorder`
- `system2`
- `file_activity_tracker`
- `speculation_detector`
- `inherited_choice`
- `truth_validator`
- `strategy_escalation`
- `change_propagation`
- `outcome_validator`
- `error_attribution`
- `task_tracker`
- `task_unresolved_suggester`
- `lint`

## 5) Stop Router (`Stop.py`)

In-process gate sequence (`IN_PROCESS_GATES`, order matters):

- `safety_gate`
- `skill_first_stop_gate`
- `behavior_audit`
- `behavior_gates_agreement`
- `behavior_gates_guidance`
- `behavior_gates_blacklist`
- `narrative_intent`
- `anti_sycophancy_quality`
- `command_execution_validator`
- `advisory`
- `reflect_integration`
- `existence_gate`

Non-blocking subprocess side effects (`SIDE_EFFECTS`):

- `conversation_storage.py`
- `auto_cks_storage.py`
- `Stop_cks_decision_capture.py`

## 6) SessionStart Router (`SessionStart.py`)

Setup sequence (`SETUP_SEQUENCE`):

- `SessionStart_terminal_id.py`
- `SessionStart_hook_health_check.py`
- `SessionStart_handoff_restore.py`
- `SessionStart_task_identity.py`
- `SessionStart_timeline.py`
- `SessionStart_constraint_display.py`

Also runs retention cleanup inline before sequence:

- `session_data_retention.cleanup()`

## 7) PreCompact Router (`PreCompact.py`)

Sequence:

- `PreCompact_handoff_capture.py`

## 8) Notification Hook

- `voice_notifications.ps1`

## 9) SessionEnd

- No active hook commands configured.

## 10) Notes

- This v3 catalog is intentionally runtime-scoped. It excludes archived, legacy, disabled, and merely present-on-disk hooks.
- If `settings.json` changes, this file must be regenerated/updated from active wiring, not from historical docs.
