# Hook Architecture v2.6.0

> Extracted from settings.json for reference. Not runtime configuration.

## Design Philosophy

**Core Principle:** Structural enforcement beats instruction injection. Blocking bad actions beats convincing against them.

### Decision Framework

| Strategy | When to Use |
|----------|-------------|
| **PreToolUse_block** | Action is programmatically detectable BEFORE execution (e.g., wrong path, missing skill invocation) |
| **Stop_block** | Violation is detectable in output AFTER generation (e.g., success claim without execution) |
| **Constitutional_text** | Judgment/context required, not programmatically determinable |
| **Prompt_injection** | Advisory only - reminders of existing capability, easily ignored |

### History
- v1 (2024): Used 500+ token injection per prompt
- v2 (2025): Shifted to blocking hooks after finding injection easily ignored
- Jan 2026: Phrase 'constitution_primary_hook_minimal' retired - was causing confusion

## Design Principles

1. Minimal injection, maximal validation
2. Goal anchoring not context flooding
3. Conditional activation for bloat guard
4. Post-generation truth checking
5. Structural enforcement over instruction injection
6. Sequential agent chains with structured handoff
7. Command directive injection over advisory reminders

## Token Budget

| Component | Tokens | Breakdown |
|-----------|--------|-----------|
| command_directive | 200 | 150 directive + 50 anti-pattern warnings |
| goal_anchor | 130 | 80 solo-dev context + 50 goal anchor |
| cks_injection | 150 | memories + worktree guidance |
| bloat_guard (when active) | 100 | ~5% activation rate |
| **total_default** | 480 | |
| **total_code_gen** | 580 | |
| **total_with_command** | 680 | |

## Layer Reference

### Layer -2: Speculation Gate
- **Purpose:** Block diagnostic claims without source verification (PART C.2)
- **Strategy:** Detect speculation patterns, require Read() before root cause claims
- **Capabilities:** speculation_marker_detection, high_confidence_without_tier_check, root_cause_without_source_detection, premature_confirmation_detection

### Layer 0: Command Directive
- **Purpose:** Inject actual command directive content, not just reminder
- **Strategy:** Read command file, extract EXECUTION DIRECTIVE, inject as critical context
- **Replaces:** UserPromptSubmit_command_reminder.py (advisory-only)

### Layer 0: Subagent Enforcer
- **Purpose:** Enforce subagent-first execution for substantive tasks (PART H)
- **Strategy:** Detect complexity indicators, inject execution mode directive
- **Rationale:** CLAUDE.md PART H competes with training priors; structural enforcement needed

### Layer 0a: Speculation Detector
- **Purpose:** Early warning for speculation during investigation (PART C.2)
- **Strategy:** Detect speculation patterns in PostToolUse, inject guidance
- **Rationale:** Fires before Stop hook to allow course correction

### Layer 1: Goal Anchor
- **Purpose:** Anti-goal displacement + solo-dev terminology prevention
- **Strategy:** Inject solo-dev context + Extract goal, sandwich at top+bottom

### Layer 1a: Bloat Guard
- **Purpose:** Solo-dev compliance
- **Strategy:** Detect code gen patterns, inject constraints
- **Activation:** ~5% of prompts (conditional)

### Layer 3a: Truth Validation
- **Purpose:** Catch escapes from constitution
- **Strategy:** High-precision detection only, constitution is primary defense
- **Capabilities:** critical_lazy_claims (context-aware), excuse_patterns, sycophancy

### Layer 3a/3b: Extended Enforcement
- **3a_bloat_extended:** Catch enterprise patterns from subagent output
- **3b_handoff_validation:** Enforce structured agent-to-agent communication

### Layer 4: Command Execution
- **Purpose:** Validate slash command was executed, not described
- **Capabilities:** description_pattern_detection, do_not_rule_validation, command_specific_rules, execution_evidence_check

### Layer 4a: Execution Evidence
- **Purpose:** STRUCTURAL enforcement for success claims (PART L)
- **Strategy:** Block success signals unless Bash execution occurred after last Write/Edit
- **Design:** structural_enforcement_over_semantic_detection
- **Rationale:** Structural check (did you execute?) is deterministic. Semantic check (did you claim success?) is brittle regex.

### Layer 4b: Entity Correlation
- **Purpose:** Validate entity claims have corresponding file observations
- **Strategy:** If response mentions [entity X] AND no reads of [X-related files], block
- **Added:** 2026-01-11
- **Closes gap:** Conditional speculation escaping empirical_claims_gate

## Migration History

### v1 → v2 Migration
**Archived:**
- user_prompt_submit.py (500+ token injection)
- constitutional_preprocessor.py
- adaptive_task_enforcement.py
- post_tool_use.py (4000-line quality gates - no evidence of value)

**Preserved:**
- PreToolUse_directory_policy.py (path protection)
- PreToolUse_safety_gate.py (TDD enforcement)
- UserPromptSubmit_truth_validator.py (excuse pattern detection)

**Archive location:** `.claude/hooks/_archive_v1`

### v2.4 → v2.5 Migration (2025-12-22)
**Reason:** Fix slash command execution bypass - commands being described instead of executed

**Changes:**
- UserPromptSubmit_command_reminder.py → UserPromptSubmit_command_directive_injector.py
- Added command_execution_validator.py (Stop hook)

**Root cause:** Advisory text injection easily ignored; no post-generation validation

**Fix strategy:** Pre-gen: inject actual directive content. Post-gen: validate execution evidence, block descriptions.
