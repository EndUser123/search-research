#!/usr/bin/env python3
"""ACA classification table generator."""
from collections import defaultdict

classifications = [
    # === cc-aca-reasoning ===
    ("Start_reasoning_mode_selector.py", "UserPromptSubmit", "cc-aca-reasoning", "high", "no", "Selects reasoning mode at start of turn"),
    ("PreToolUse_sequential_thinking.py", "PreToolUse", "cc-aca-reasoning", "high", "yes: sequential_state", "Manages sequential thinking iteration count"),
    ("Stop_reasoning_quality_gate.py", "Stop", "cc-aca-reasoning", "high", "no", "Automatic reasoning quality gate at stop"),
    ("StopHook_sequential_thinking.py", "Stop", "cc-aca-reasoning", "high", "yes: sequential_state", "Sequential thinking iteration management at stop"),
    ("posttooluse_self_reflection_reminder.py", "PostToolUse", "cc-aca-reasoning", "medium", "no", "Self-reflection reminder after edits"),
    ("anti_lazy_diff_nudge.py", "PostToolUse", "cc-aca-reasoning", "medium", "no", "Anti-lazy nudge on trivial diffs"),

    # === cc-aca-epistemic ===
    ("PreToolUse_evidence_hierarchy_gate.py", "PreToolUse", "cc-aca-epistemic", "high", "no", "Enforces evidence hierarchy for search queries"),
    ("PreToolUse_stop_epistemic_contract.py", "PreToolUse", "cc-aca-epistemic", "high", "yes: investigation_state", "Enforces epistemic contract before tool use"),
    ("PostToolUse_claim_verifier_smoke.py", "PostToolUse", "cc-aca-epistemic", "high", "no", "Verifies claims against tool output evidence"),
    ("self_verification_gate.py", "PostToolUse", "cc-aca-epistemic", "high", "no", "Self-verification gate after edits"),
    ("SessionStart_cc_health.py", "SessionStart", "cc-aca-epistemic", "medium", "no", "Epistemic gate health surfacing at session start"),
    ("fact-guard_PreToolUse.py", "PreToolUse", "cc-aca-epistemic", "high", "no", "Blocks unsupported literals and contamination"),
    ("fact-guard_PostToolUse.py", "PostToolUse", "cc-aca-epistemic", "high", "yes: fact ledger", "Records observed facts from tool outputs"),
    ("provenance_verifier.py", "PreToolUse", "cc-aca-epistemic", "high", "no", "External M2.7 LLM provenance verification"),

    # === cc-aca-session ===
    ("SessionStart_verification_cleanup.py", "SessionStart", "cc-aca-session", "high", "yes: state files", "Verification state cleanup at session start"),
    ("SessionStart_breadcrumb_init.py", "SessionStart", "cc-aca-session", "high", "yes: breadcrumb state", "Initialize breadcrumb tracking for /tdd"),
    ("SessionEnd_cleanup.py", "SessionEnd", "cc-aca-session", "high", "yes: state files", "Minimal janitor cleanup at session end"),
    ("SessionEnd_breadcrumb_cleanup.py", "SessionEnd", "cc-aca-session", "high", "yes: breadcrumb state", "Breadcrumb trail cleanup at session end"),
    ("SessionEnd_tdd_cleanup.py", "SessionEnd", "cc-aca-session", "high", "yes: tdd state", "Terminal-isolated TDD state cleanup"),
    ("PreCompact.py", "PreCompact", "cc-aca-session", "high", "no", "PreCompact stub (deprecated)"),
    ("snapshot_PreCompact.py", "PreCompact", "cc-aca-session", "high", "yes: snapshot state", "Snapshot capture before compaction"),
    ("snapshot_SessionStart.py", "SessionStart", "cc-aca-session", "high", "yes: snapshot state", "Session resume via snapshot"),
    ("snapshot_SessionEnd_tldr.py", "SessionEnd", "cc-aca-session", "high", "no", "TLDR generation at session end"),
    ("snapshot_UserPromptSubmit.py", "UserPromptSubmit", "cc-aca-session", "high", "yes: snapshot state", "Snapshot context injection"),

    # === cc-aca-authority ===
    ("PreToolUse_authorization_gate.py", "PreToolUse", "cc-aca-authority", "high", "yes: auth state", "Blocks destructive commands without explicit authorization"),
    ("PreToolUse_command_intent_gate.py", "PreToolUse", "cc-aca-authority", "high", "yes: intent state", "Validates bash commands match slash-command intent"),
    ("PreToolUse_delegation_gate.py", "PreToolUse", "cc-aca-authority", "high", "yes: delegation state", "Manages delegation state for subagent workflows"),
    ("PreToolUse_skill_first_gate.py", "PreToolUse", "cc-aca-authority", "high", "yes: skill intent state", "Enforces skill-first mode gating"),
    ("PreToolUse_ask_first_tool_gate.py", "PreToolUse", "cc-aca-authority", "medium", "no", "Controls ask-first tool availability"),
    ("PreToolUse_plan_consumer_gate.py", "PreToolUse", "cc-aca-authority", "high", "yes: phase ledger", "Validates plan consumption before implementation"),
    ("stop_permission_stall.py", "Stop", "cc-aca-authority", "high", "no", "Detects permission-seeking stall patterns"),
    ("skill-guard_PreToolUse.py", "PreToolUse", "cc-aca-authority", "high", "yes: skill execution state", "Skill dispatch enforcement"),
    ("skill-guard_Stop.py", "Stop", "cc-aca-authority", "high", "yes: skill execution state", "Skill completion verification"),
    ("skill-guard_UserPromptSubmit.py", "UserPromptSubmit", "cc-aca-authority", "high", "yes: skill intent state", "Slash command routing and enforcement"),

    # === cc-aca-investigation ===
    ("PreToolUse_investigation_gate.py", "PreToolUse", "cc-aca-investigation", "high", "yes: investigation_state", "Blocks writes to uninvestigated files"),
    ("PreToolUse_discovery_tracker.py", "PreToolUse", "cc-aca-investigation", "high", "yes: discovery state", "Tracks codebase discovery coverage"),
    ("PreToolUse_git_state_capture.py", "PreToolUse", "cc-aca-investigation", "medium", "yes: git state", "Captures git status before modifications"),
    ("PreToolUse_implementation_default_gate.py", "PreToolUse", "cc-aca-investigation", "medium", "yes: intent state", "Gates implementation without investigation"),
    ("tool_availability_checker.py", "PreToolUse", "cc-aca-investigation", "medium", "no", "Checks tool availability before use"),
    ("PreToolUse_file_existence_guard.py", "PreToolUse", "cc-aca-investigation", "high", "no", "Guards against operating on non-existent files"),

    # === cc-aca-sdlc ===
    ("PostToolUse_tdd_state.py", "PostToolUse", "cc-aca-sdlc", "high", "yes: tdd state", "TDD phase state transitions"),
    ("PostToolUse_tdd_state_tracker.py", "PostToolUse", "cc-aca-sdlc", "high", "yes: tdd state", "TDD state persistence and tracking"),
    ("StopHook_tdd_continuation.py", "Stop", "cc-aca-sdlc", "high", "yes: tdd state", "Advisory reminder for incomplete TDD workflow"),
    ("PreToolUse_tdd_gate.py", "PreToolUse", "cc-aca-sdlc", "high", "yes: tdd state", "TDD workflow phase enforcement"),
    ("PreToolUse_refactor_transition.py", "PreToolUse", "cc-aca-sdlc", "high", "yes: refactor state", "Refactor workflow phase transitions"),
    ("PostToolUse_documentation_validator.py", "PostToolUse", "cc-aca-sdlc", "medium", "no", "Documentation quality validation"),
    ("post/PostToolWrite_doc_validator.py", "PostToolUse", "cc-aca-sdlc", "medium", "no", "Doc validation after writes"),
    ("PreToolUse_arch_first_enforcer.py", "PreToolUse", "cc-aca-sdlc", "medium", "yes: arch state", "Architecture-first enforcement"),
    ("cc-skills-sdlc_PreToolUse.py", "PreToolUse", "cc-aca-sdlc", "high", "yes: refactor state", "SDLC refactor transition dispatching"),
    ("cc-skills-sdlc_PostToolUse.py", "PostToolUse", "cc-aca-sdlc", "high", "yes: refactor state", "SDLC refactor validation dispatching"),
    ("cc-skills-sdlc_Stop.py", "Stop", "cc-aca-sdlc", "high", "yes: refactor state", "SDLC refactor verifier dispatching"),

    # === cc-aca-safety ===
    ("PreToolUse_destructive_git_guard.py", "PreToolUse", "cc-aca-safety", "high", "no", "Guards against destructive git operations"),
    ("PreToolUse_git_safety.py", "PreToolUse", "cc-aca-safety", "high", "no", "Git safety enforcement (forgettables, etc)"),
    ("PreToolUse_git_auto_stage.py", "PreToolUse", "cc-aca-safety", "high", "no", "Auto-stage files before risky operations"),
    ("PreToolUse_git_remote_check_order_guard.py", "PreToolUse", "cc-aca-safety", "high", "no", "Enforces local-first git remote checking"),
    ("PreToolUse_bulk_delete_gate.py", "PreToolUse", "cc-aca-safety", "high", "no", "Guards against bulk delete operations"),
    ("PreToolUse_directory_policy.py", "PreToolUse", "cc-aca-safety", "high", "no", "Directory access policy enforcement"),
    ("PreToolUse_secret_scanner.py", "PreToolUse", "cc-aca-safety", "high", "no", "Scans for secrets in tool inputs"),
    ("PreToolUse_powershell_validator.py", "PreToolUse", "cc-aca-safety", "high", "no", "PowerShell argument validation"),
    ("PostToolUse_bash_syntax_gate.py", "PostToolUse", "cc-aca-safety", "high", "no", "Bash syntax validation after tool use"),
    ("PreToolUse_dependency_verification_gate.py", "PreToolUse", "cc-aca-safety", "medium", "no", "Package dependency safety verification"),
    ("PreToolUse_bash_syntax_validator.py", "PreToolUse", "cc-aca-safety", "high", "no", "Bash command syntax pre-validation"),
    ("PreToolUse_ownership_colocation_gate.py", "PreToolUse", "cc-aca-safety", "high", "no", "Blocks infra at wrong directory level"),

    # === cc-aca-observability ===
    ("log_hook.py", "All", "cc-aca-observability", "high", "yes: log files", "Structured logging for all hook events"),
    ("PostToolUse_router.py", "PostToolUse", "cc-aca-observability", "high", "yes: artifact ledger", "Routes post-tool-use tracking and artifact recording"),
    ("PostToolUse_artifact_validator.py", "PostToolUse", "cc-aca-observability", "high", "yes: artifact ledger", "Artifact integrity validation"),
    ("PostToolUse_artifact_scraper.py", "PostToolUse", "cc-aca-observability", "high", "yes: artifact ledger", "Scrapes tool output for artifact extraction"),
    ("PostToolUse_artifact_access_tracker.py", "PostToolUse", "cc-aca-observability", "high", "yes: access log", "Tracks file access patterns"),
    ("PostToolUse_e2e_tracker.py", "PostToolUse", "cc-aca-observability", "high", "yes: e2e state", "End-to-end workflow tracking"),
    ("PostToolUse_breadcrumb_tracker.py", "PostToolUse", "cc-aca-observability", "high", "yes: breadcrumb state", "Breadcrumb trail updates after tool use"),
    ("PreToolUse_breadcrumb_gate.py", "PreToolUse", "cc-aca-observability", "high", "yes: breadcrumb state", "Breadcrumb progression validation"),
    ("PreToolUse_breadcrumb_verifier.py", "PreToolUse", "cc-aca-observability", "high", "yes: breadcrumb state", "Breadcrumb state verification"),
    ("PreToolUse_domain_tool_router.py", "PreToolUse", "cc-aca-observability", "medium", "no", "Advisory domain-specific search tool suggestions"),
    ("PostToolUse_p2_filter_gate.py", "PostToolUse", "cc-aca-observability", "medium", "no", "P2 evidence filtering"),
    ("PostToolUse_adversarial_aggregate.py", "PostToolUse", "cc-aca-observability", "medium", "no", "Aggregates adversarial review results"),
    ("PostToolUse_powershell_validator.py", "PostToolUse", "cc-aca-observability", "medium", "no", "PowerShell argument validation tracking"),
    ("PostToolUse_wrapper_validator.py", "PostToolUse", "cc-aca-observability", "medium", "no", "Wrapper pattern validation"),
    ("cjk_drift_detector.py", "Stop/SubagentStop/PostToolUse", "cc-aca-observability", "high", "yes: drift state", "CJK drift detection across turns"),
    ("Stop_diagnostic_analysis_quality_gate.py", "Stop", "cc-aca-observability", "medium", "no", "Diagnostic analysis quality metrics"),
    ("Notification_voice_hook.py", "Notification", "cc-aca-observability", "high", "no", "Voice notifications for hook events"),
    ("judge_feedback.py", "SessionStart", "cc-aca-observability", "high", "yes: judge state", "Judge feedback processing at session start"),

    # === cc-aca-core (shared infrastructure) ===
    ("PreToolUse.py", "PreToolUse", "cc-aca-core", "high", "yes: dispatch state", "Main PreToolUse dispatcher/router"),
    ("PostToolUse.py", "PostToolUse", "cc-aca-core", "high", "yes: dispatch state", "Main PostToolUse dispatcher"),
    ("Stop.py", "Stop", "cc-aca-core", "high", "yes: gate metadata", "Main Stop router with 44 gates"),
]

# Print grouped by ACA domain
by_domain = defaultdict(list)
for file, lifecycle, domain, conf, state, rationale in classifications:
    by_domain[domain].append((file, lifecycle, conf, state, rationale))

total = 0
for domain in sorted(by_domain.keys()):
    hooks = by_domain[domain]
    total += len(hooks)
    print(f"### {domain} ({len(hooks)} hooks)")
    for file, lifecycle, conf, state, rationale in sorted(hooks):
        print(f"  {file:<50} {lifecycle:<22} {conf:<8} {state[:40]:<42} {rationale}")
    print()

print(f"TOTAL: {total} hooks classified")
