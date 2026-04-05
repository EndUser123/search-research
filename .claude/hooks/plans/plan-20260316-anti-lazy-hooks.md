# Implementation Plan: Anti-Lazy Hooks for Template Update Enforcement

**Plan ID**: plan-20260316-anti-lazy-hooks
**Status**: DRAFT
**Created**: 2026-03-16
**Author**: Plan-workflow v3.0

---

## Status Summary

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: Quick Wins (PostToolUse + SessionStart) | ⏳ PENDING | Low-risk hooks, no blocking |
| Phase 2: Core Enforcement (UserPromptSubmit) | ⏳ PENDING | Behavior contract injection |
| Phase 3: Template Guarding (PreToolUse) | ⏳ PENDING | Requires whitelist logic for test/docs files |
| Phase 4: Multi-Terminal Coordination | ⏸️ DEFERRED | Optional enhancement |

---

## Problem Statement

### Behavioral Problems Identified

From `C:\Users\brsth\Downloads\advesarial.txt` transcript analysis:

1. **Declaration ≠ Execution**: LLM responds with intent ("I'll update the template") but stops at verbal agreement without invoking Write/Edit tools
2. **No Cross-Session Persistence**: Each conversation starts fresh; templates must be explicitly written during the session
3. **Missing Anti-Lazy Enforcement**: User enforcement ("you keep saying 'i'll do it', but then you will forget") successfully triggers execution
4. **Template Updates Are Write Operations**: Updating templates requires Read → Edit/Write → Verify sequence, often skipped

### Root Cause

LLM training favors conversational agreement over tool execution. Without enforcement, declarative responses ("I'll update the template") substitute for actual file operations.

### Evidence of Success

Lines 285-349 of adversarial.txt show successful template update after explicit user enforcement:
- User: "I didn't see you update your template in /arch"
- LLM: Read base.md, made the Edit, showed the diff

---

## Context Analysis

### Existing Hook Architecture

**Current Hook Routers**:
- `UserPromptSubmit.py` (Lean Router v2.0) - Modular registry pattern
- `PreToolUse.py` (Lean Router v2.2) - Dispatch chain with UNIVERSAL hooks
- `PostToolUse.py` (Lean Router v2.1) - In-process side-effect hooks

**Relevant Infrastructure**:
- Registry pattern: `UserPromptSubmit_modules/registry.py`
- State directory: `P:/.claude/state/`
- Session/terminal isolation: Terminal-scoped state files
- Evidence store: `evidence_store.py` for tool event tracking

### Multi-Terminal Constraints

**Constitutional Requirement** (from CLAUDE.md):
- Per-terminal state isolation
- Session-scoped state files
- Graceful degradation if coordination fails

**Implementation Implications**:
- State files must use terminal_id in filename
- No cross-terminal bleed of pending intent
- Fail-open if terminal detection fails

### User Preference

User explicitly stated: *"I find claude.md and prompting not usually great. Hooks seems to work OK. What hooks do we need to accomplish the same things?"*

**Decision**: Use hooks-only approach, no CLAUDE.md modifications.

---

## Existing Implementation Discovery

### Current Hook Files

| File | Purpose | Relevance |
|------|---------|-----------|
| `UserPromptSubmit.py` | Router for prompt hooks | **HIGH** - Will add behavior guard module |
| `PreToolUse.py` | Tool validation router | **HIGH** - Will add arch enforcer |
| `PostToolUse.py` | Post-execution monitoring | **HIGH** - Will add diff nudge |
| `UserPromptSubmit_modules/registry.py` | Module registration | **MEDIUM** - Need to register new module |
| `UserPromptSubmit_modules/skill_enforcer.py` | Pattern example | **LOW** - Reference for trigger patterns |

### Dispatch Chain Verification

**PreToolUse.py dispatch chain** (lines 11-28):
```
UNIVERSAL hooks:
  - PreToolUse_path_validator.py
  - PreToolUse/PreToolUse_skill_pattern_gate.py
  - PreToolUse_risk_tier_gate.py
  - PreToolUse_observe_before_act_gate.py
  - PreTool_multi_agent_reasoning.py

NOT in dispatch chain (do not edit):
  - PreToolUse_skill_first_gate.py
  - PreToolUse_workflow_steps_gate.py
```

**Critical**: PreToolUse hook must be added to dispatch chain or registered in settings.json.

### Existing Pattern Detection

**skill_enforcer.py** trigger patterns (lines 40-50):
```python
trigger_phrases = [
    "you keep doing this",
    "same mistake",
    "again you did",
    "recurring",
    "update your template",
    "arch/",
]
```

This matches the behavioral problems we're solving.

---

## Proposed Solution

### Four-Hook Architecture

| Hook | Event | Purpose | Phase |
|------|-------|---------|-------|
| `anti_lazy_behavior_guard.py` | UserPromptSubmit | Inject behavior contract on trigger phrases | 2 |
| `anti_lazy_arch_enforcer.py` | PreToolUse | Block non-arch edits during recurring conversations | 3 |
| `anti_lazy_diff_nudge.py` | PostToolUse | Require diff + explanation for arch edits | 1 |
| `anti_lazy_preamble.py` | SessionStart | Seed template-driven identity | 1 |

### Hook Specifications

#### 1. anti_lazy_diff_nudge.py (PostToolUse)

**Purpose**: Enforce visibility for arch file edits

**Logic**:
```python
def main():
    data = json.load(sys.stdin)
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}

    if tool_name not in ("Write", "Edit"):
        return

    path = (tool_input.get("path") or "").replace("\\", "/")
    if not (path.startswith("arch/") or "/arch/" in path):
        return

    # Nudge for diff + explanation
    msg = f"""
    You just updated a template-like file under `arch/` ({path}).

    Now, for visibility and learning:
    - Show a unified diff of the changes you made to `{path}`.
    - In 1–2 sentences, state what recurring mistake or failure mode this change is intended to prevent.
    - If this change was triggered by user complaints about repeated mistakes,
      explicitly connect your explanation to that complaint.
    """

    output = {"hookSpecificOutput": {"additionalContext": msg}}
    print(json.dumps(output))
```

#### 2. anti_lazy_preamble.py (SessionStart)

**Purpose**: Seed template-driven identity without CLAUDE.md

**Logic**:
```python
def main():
    preamble = """
    You are working in a repository that uses `arch/` markdown files
    as behavior and process templates.

    Core principle: error-driven learning.
    - When you notice recurring mistakes or user complaints about repeated behavior,
      prefer updating the relevant `arch/` template over just apologizing.
    - Template updates must be visible: show diffs and explain what mistake the change prevents.
    """

    output = {"hookSpecificOutput": {"additionalContext": preamble}}
    print(json.dumps(output))
```

#### 3. anti_lazy_behavior_guard.py (UserPromptSubmit)

**Purpose**: Inject behavior contract when triggers detected

**Trigger Patterns**:
```python
TRIGGER_PHRASES = [
    "you keep doing this",
    "same mistake",
    "again you did",
    "recurring",
    "update your template",
    "arch/",
]
```

**Logic**:
```python
def process_prompt(data: dict) -> dict:
    prompt = data.get("prompt", "")

    if not any(phrase.lower() in prompt.lower() for phrase in TRIGGER_PHRASES):
        return {}

    contract = """
    You are currently failing at error-driven learning.

    When you fix a recurring mistake or broken behavior pattern in this session, you must:
    - Identify which template or behavior guideline in `arch/` should change.
    - Open the relevant file under `arch/` (start with `arch/behavior-template.md` if unsure).
    - Edit it to encode the new learning.
    - Show a unified diff of the change.
    - Explain in 1–2 sentences how this change will prevent repeating the mistake.

    Do not only state intent like "I'll remember this" or "I'll update the template later".
    You must perform the file edit now, in this session, and show the diff.
    """

    return {"additionalContext": contract}
```

#### 4. anti_lazy_arch_enforcer.py (PreToolUse)

**Purpose**: Block non-arch edits during recurring conversations

**Logic**:
```python
def main():
    data = json.load(sys.stdin)
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}

    if tool_name not in ("Write", "Edit"):
        print("{}")
        sys.exit(0)

    path = (tool_input.get("path") or "").replace("\\", "/")

    # Allow arch/ edits
    if path.startswith("arch/") or "/arch/" in path:
        print("{}")
        sys.exit(0)

    # WHITELIST: Allow test files, documentation, temporary files
    WHITELIST_PATTERNS = [
        "test", "spec", ".test.", ".spec.",
        "README", "CHANGELOG", ".md",
        ".tmp", ".temp", "/tmp/",
    ]
    if any(pattern in path.lower() for pattern in WHITELIST_PATTERNS):
        print("{}")
        sys.exit(0)

    # Check for recurring conversation context
    if not _is_recurring_context(data):
        print("{}")
        sys.exit(0)

    # Block with explanation
    msg = """
    PreToolUse guard: You are about to respond to a recurring mistake without
    updating any `arch/` templates.

    Instead of only editing task-local files, first:
    - Open or create an appropriate file under `arch/`
      (e.g. `arch/behavior-template.md`).
    - Encode the new learning there.
    - Show a unified diff of that change.
    - After updating `arch/`, you may proceed with other edits.
    """

    output = {"continue": False, "reason": msg}
    print(json.dumps(output))
    sys.exit(2)
```

**Critical**: Whitelist logic prevents blocking of:
- Test files (`test_*.py`, `*_test.py`, `conftest.py`)
- Documentation files (`README`, `CHANGELOG`, `.md` files)
- Temporary files (`.tmp`, `.temp`, `/tmp/`)

### Multi-Terminal Safety

**State File Naming**:
```python
# UserPromptSubmit: Store trigger detection state
state_file = f"P:/.claude/state/anti_lazy_trigger_{terminal_id}.json"

# PreToolUse: Check for recurring context
context_file = f"P:/.claude/state/anti_lazy_context_{terminal_id}.json"
```

**Isolation Guarantees**:
- Each terminal has isolated state
- No cross-terminal contamination
- Graceful degradation if terminal_id unavailable

---

## Test Discovery

### Existing Hook Test Patterns

From `P:\.claude/hooks/CLAUDE.md`:

**Testing Protocol**:
```bash
# Run hook diagnostics
python P:\.claude/hooks/hook_diagnostics.py

# Run pytest suite
pytest P:\.claude/hooks/tests/ -v
```

**Expected Exit Codes**:
| Hook Event | Exit 0 | Exit 2 |
|------------|--------|--------|
| PreToolUse | Allow/pass-through | **Block** (correct) |
| PostToolUse | Always exit 0 | Advisory only |
| UserPromptSubmit | Always exit 0 | N/A |
| SessionStart | Always exit 0 | N/A |

### Test Coverage Requirements

**Unit Tests** (per hook):
1. Trigger detection accuracy
2. Path filtering logic
3. State file operations
4. Multi-terminal isolation
5. Whitelist pattern matching

**Integration Tests**:
1. End-to-end workflow (trigger → block → update → diff)
2. Multi-terminal concurrent sessions
3. State file cleanup and TTL

**Performance Baseline**:
- UserPromptSubmit: <50ms
- PreToolUse: <100ms
- PostToolUse: <50ms
- SessionStart: <100ms

---

## Implementation Plan

### Phase 1: Quick Wins (PostToolUse + SessionStart)

**Tasks**:

**TASK-001**: Create anti_lazy_diff_nudge.py (PostToolUse)
- File: `P:\.claude/hooks/anti_lazy_diff_nudge.py`
- Action: Create PostToolUse hook for arch file edit nudges
- Acceptance:
  - Detects Write/Edit operations on arch/ files
  - Outputs diff + explanation nudge
  - Returns exit 0 (advisory only)
- Effort: S (1-2 hours)
- Prerequisites: None

**TASK-002**: Create anti_laky_preamble.py (SessionStart)
- File: `P:\.claude/hooks/anti_lazy_preamble.py`
- Action: Create SessionStart hook for identity seeding
- Acceptance:
  - Outputs template-driven identity preamble
  - Returns exit 0
- Effort: S (1 hour)
- Prerequisites: None

**TASK-003**: Register PostToolUse hook
- File: `P:\.claude/settings.json`
- Action: Add anti_lazy_diff_nudge.py to PostToolUse hooks
- Acceptance:
  - Hook registered in settings.json
  - Hook executes on Write/Edit events
- Effort: S (30 minutes)
- Prerequisites: TASK-001

**TASK-004**: Register SessionStart hook
- File: `P:\.claude/settings.json`
- Action: Add anti_lazy_preamble.py to SessionStart hooks
- Acceptance:
  - Hook registered in settings.json
  - Hook executes on session start
- Effort: S (30 minutes)
- Prerequisites: TASK-002

**TASK-005**: Integration test Phase 1 hooks
- File: `P:\.claude/hooks/tests/test_anti_lazy_phase1.py`
- Action: Create integration tests for PostToolUse + SessionStart
- Acceptance:
  - Test arch file edit nudge
  - Test session start preamble
  - All tests pass
- Effort: M (2-3 hours)
- Prerequisites: TASK-001, TASK-002, TASK-003, TASK-004

### Phase 2: Core Enforcement (UserPromptSubmit)

**Tasks**:

**TASK-006**: Create anti_lazy_behavior_guard.py (UserPromptSubmit)
- File: `P:\.claude/hooks/UserPromptSubmit_modules/anti_lazy_behavior_guard.py`
- Action: Create UserPromptSubmit module for behavior contract injection
- Acceptance:
  - Detects trigger phrases in prompts
  - Injects behavior contract
  - Exports process_prompt() function
- Effort: M (2-3 hours)
- Prerequisites: TASK-005

**TASK-007**: Register UserPromptSubmit module
- File: `P:\.claude/hooks/UserPromptSubmit_modules/registry.py`
- Action: Add anti_lazy_behavior_guard to registry
- Acceptance:
  - Module imported in import_hook()
  - Added to HOOK_PRIORITY and HOOK_DISPATCH
- Effort: M (1-2 hours)
- Prerequisites: TASK-006

**TASK-008**: Integration test UserPromptSubmit
- File: `P:\.claude/hooks/tests/test_anti_lazy_behavior_guard.py`
- Action: Create unit tests for behavior guard
- Acceptance:
  - Test trigger phrase detection
  - Test contract injection
  - Test non-trigger pass-through
  - All tests pass
- Effort: M (2-3 hours)
- Prerequisites: TASK-007

### Phase 3: Template Guarding (PreToolUse)

**Tasks**:

**TASK-009**: Create anti_lazy_arch_enforcer.py (PreToolUse)
- File: `P:\.claude/hooks/PreToolUse/anti_lazy_arch_enforcer.py`
- Action: Create PreToolUse hook for arch edit enforcement
- Acceptance:
  - Detects recurring conversation context
  - Blocks non-arch edits with whitelist exceptions
  - Returns exit 2 on block, exit 0 on allow
- Effort: M (3-4 hours)
- Prerequisites: TASK-008

**TASK-010**: Implement whitelist logic
- File: `P:\.claude/hooks/PreToolUse/anti_lazy_arch_enforcer.py` (extend)
- Action: Add whitelist pattern matching for test/docs/temp files
- Acceptance:
  - WHITELIST_PATTERNS defined
  - should_allow() function implemented
  - Test files pass through
  - Documentation files pass through
- Effort: M (2-3 hours)
- Prerequisites: TASK-009

**TASK-011**: Register PreToolUse hook
- File: `P:\.claude/hooks/PreToolUse.py` or `P:\.claude/settings.json`
- Action: Add anti_lazy_arch_enforcer to dispatch chain or settings
- Acceptance:
  - Hook in UNIVERSAL list or settings.json
  - Hook executes on Write/Edit events
- Effort: M (1-2 hours)
- Prerequisites: TASK-010

**TASK-012**: Integration test PreToolUse
- File: `P:\.claude/hooks/tests/test_anti_lazy_arch_enforcer.py`
- Action: Create unit tests for arch enforcer
- Acceptance:
  - Test arch file allow
  - Test non-arch block during recurring
  - Test whitelist pass-through
  - Test multi-terminal isolation
  - All tests pass
- Effort: M (3-4 hours)
- Prerequisites: TASK-011

### Phase 4: Multi-Terminal Coordination (OPTIONAL)

**Tasks**:

**TASK-013**: Implement state file coordination
- File: `P:\.claude/hooks/__lib/anti_lazy_state.py`
- Action: Create shared state management for multi-terminal coordination
- Acceptance:
  - Terminal-scoped state files
  - TTL-based cleanup
  - Graceful degradation
- Effort: L (4-6 hours)
- Prerequisites: TASK-012

**TASK-014**: Cross-terminal signaling
- File: `P:\.claude/hooks/__lib/anti_lazy_signaling.py`
- Action: Implement signal file sharing across terminals
- Acceptance:
  - Broadcast template updates
  - Detect conflicts
  - Merge state safely
- Effort: L (5-8 hours)
- Prerequisites: TASK-013

**TASK-015**: Multi-terminal integration tests
- File: `P:\.claude/hooks/tests/test_anti_lazy_multiterminal.py`
- Action: Create tests for concurrent terminal scenarios
- Acceptance:
  - Test concurrent terminal isolation
  - Test state propagation
  - Test conflict resolution
  - All tests pass
- Effort: L (4-6 hours)
- Prerequisites: TASK-014

---

## Risks, Success Criteria, Dependencies

### Top Risks

1. **PreToolUse whitelist gaps** - May block legitimate work on test/docs files
   - **Mitigation**: Comprehensive whitelist testing, bypass flag `--allow-non-arch`

2. **False trigger detection** - UserPromptSubmit may inject contract inappropriately
   - **Mitigation**: Conservative trigger phrases, opt-out via env var

3. **Multi-terminal state corruption** - Concurrent terminals may corrupt state files
   - **Mitigation**: File locking, atomic writes, graceful degradation

4. **Performance degradation** - Hook overhead on every tool call
   - **Mitigation**: <100ms target, early exit patterns

### Success Criteria

**Behavioral**:
- LLM updates arch templates when fixing recurring mistakes
- Diffs shown for all template changes
- "I'll update" responses replaced with actual file edits

**Technical**:
- All hooks exit within performance baselines
- Test coverage >80% for critical paths
- Multi-terminal isolation verified
- Zero false blocks on whitelisted file types

**User Experience**:
- Transparent enforcement (clear block messages)
- Easy bypass (env vars, flags)
- No regression in existing workflows

### Dependencies

**Required**:
- Existing hook infrastructure (UserPromptSubmit.py, PreToolUse.py, PostToolUse.py)
- Registry pattern (UserPromptSubmit_modules/registry.py)
- State directory (P:/.claude/state/)
- Terminal detection (skill_guard/utils/terminal_detection.py)

**Optional**:
- Evidence store (evidence_store.py) - For advanced tracking
- Semantic daemon - For improved trigger detection

**Blocked By**:
- None (all dependencies available)

### Configuration

**Environment Variables**:
```bash
# Enable/disable hooks
ANTI_LAZY_ENABLED=true                    # Master switch
ANTI_LAZY_BEHAVIOR_GUARD_ENABLED=true    # UserPromptSubmit
ANTI_LAZY_ARCH_ENFORCER_ENABLED=true    # PreToolUse
ANTI_LAZY_DIFF_NUDGE_ENABLED=true       # PostToolUse
ANTI_LAZY_PREAMBLE_ENABLED=true         # SessionStart

# Bypass flags
ANTI_LAZY_BYPASS=false                   # Bypass all enforcement
ANTI_LAZY_ALLOW_NON_ARCH=false           # Bypass arch-only requirement

# Multi-terminal
ANTI_LAZY_STATE_TTL=300                  # State TTL in seconds (5 min)
ANTI_LAZY_COORDINATION_ENABLED=false     # Phase 4: cross-terminal signaling
```

### Rollback Strategy

**If hooks cause issues**:
1. Set `ANTI_LAZY_ENABLED=false` to disable all
2. Remove hooks from settings.json
3. Delete state files in `P:/.claude/state/anti_lazy_*.json`

**Git revert**:
```bash
git revert <commit-hash>
# Or reset to pre-implementation commit
git reset --hard <pre-implementation-commit>
```

---

## Next Actions

1. Review this plan and approve implementation approach
2. Run `/plan-workflow review` to execute auto-verify.py and adversarial review
3. Address any HIGH/MEDIUM priority findings from verification
4. Begin Phase 1 implementation (TASK-001 through TASK-005)

---

**Plan Status**: DRAFT - Pending verification and approval
**Next Review**: After auto-verify.py and adversarial review completion
