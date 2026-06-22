# Claude Code Hooks - Behavior Domain Graph

## Overview

This document maps all hooks by their behavioral domain, showing what each hook enforces and typical use cases.

## Hook Event Flow

```
SessionStart → UserPromptSubmit → PreToolUse → Tool Execution → PostToolUse → Stop
     ↓              ↓                ↓                           ↓              ↓
 Initialize     Validate          Block                      Analyze        Verify
 Context        Input             Action                      Output         Claims
```

## Domain Map

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           HOOK BEHAVIOR DOMAINS                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐               │
│  │  AUTHORITY     │  │  SAFETY        │  │  QUALITY       │               │
│  │  GATES        │  │  NET           │  │  ENFORCEMENT   │               │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘               │
│           │                   │                    │                          │
│           ▼                   ▼                    ▼                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐               │
│  │  VERIFICATION   │  │  STATE         │  │  MONITORING    │               │
│  │  ORACLES       │  │  MANAGEMENT    │  │  & OBSERVABILITY│              │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

## Domain 1: AUTHORITY GATES

**Purpose**: Ensure proper planning and authorization before actions.

| Hook | Event | What It Does | Use Cases |
|-------|-------|---------------|------------|
| `PreToolUse_authorization_gate.py` | PreToolUse | Detects planning mode, blocks direct implementation without plan | User asks "implement X" without planning first |
| `PreToolUse_investigation_gate.py` | PreToolUse | Requires investigation before modification | Debugging without root cause analysis |
| `PreToolUse_vague_directive_gate.py` | PreToolUse | Blocks vague directives like "improve" or "optimize" | Open-ended requests without scope |

**Typical Flow**:
```
User: "Improve the code"
    ↓
vague_directive_gate: BLOCK → "Please specify what to improve"
    ↓
User: "Fix the login bug"
    ↓
investigation_gate: BLOCK → "Investigate root cause first"
    ↓
User: (provides investigation)
    ↓
authorization_gate: BLOCK → "Create implementation plan first"
    ↓
User: (creates plan)
    ↓
Action allowed
```

---

## Domain 2: SAFETY NET

**Purpose**: Prevent destructive actions and security issues.

| Hook | Event | What It Does | Use Cases |
|-------|-------|---------------|------------|
| `PreToolUse_directory_policy.py` | PreToolUse | Blocks writes to protected paths | Attempting to edit system files |
| `PreToolUse_credential_filter.py` | PreToolUse | Redacts credentials in tool inputs | Accidentally including API keys in prompts |
| `PreToolUse_secret_scanner.py` | PreToolUse | Scans files for secrets before operations | Committing files with embedded secrets |
| `PostToolUse_output_sanitizer.py` | PostToolUse | Redacts secrets from tool output | Tool returns sensitive data |
| `recursive_failure_detector.py` | UserPromptSubmit | Detects Catch-22 situations | "Can't test without login, can't login without test" |
| `runaway_session_detector.py` | Stop | Detects excessive loop iterations | Infinite loops in tool usage |

**Typical Flow**:
```
User: "Edit C:\Windows\system32\drivers\etc\hosts"
    ↓
deny_root_write: BLOCK → "Protected path"
    ↓
User: "Check credentials.txt"
    ↓
secret_scanner: SCAN → (secrets found)
    ↓
credential_filter: REDACT → "****" in output
```

---

## Domain 3: QUALITY ENFORCEMENT

**Purpose**: Enforce development standards and testing practices.

| Hook | Event | What It Does | Use Cases |
|-------|-------|---------------|------------|
| `PreToolUse_tdd_gate.py` | PreToolUse | Requires tests before implementation | Writing code without test coverage |
| `PreToolUse_hook_edit_gate.py` | PreToolUse | Requires testing before editing hooks | Modifying hook files without verification |
| `PreToolUse_skill_pattern_gate.py` | PreToolUse | Validates skill execution patterns | Running skills with deprecated syntax |
| `skill-guard plugin: StopHook_skill_execution_gate.py` | Stop | Late violation safety net for skills (plugin-hosted) | Skill execution bypassed earlier checks |

**Typical Flow**:
```
User: "Add a new function to utils.py"
    ↓
tdd_gate: BLOCK → "Write test first"
    ↓
User: (writes test)
    ↓
Action allowed
    ↓
User: "Edit hook file"
    ↓
hook_edit_gate: BLOCK → "Test hook behavior first"
```

---

## Domain 4: VERIFICATION ORACLES

**Purpose**: Require empirical evidence for claims.

| Hook | Event | What It Does | Use Cases |
|-------|-------|---------------|------------|
| `StopHook_cross_validator.py` | Stop | Blocks "fixed" claims without verification (with meta-exemption) | Claims "bug is fixed" without test output |
| `StopHook_reality_check.py` | Stop | Validates claims against actual file state | Claims about code that doesn't exist |
| `StopHook_truth_evidence_gate.py` | Stop | Enforces evidence for factual claims | Making claims without supporting evidence |
| `StopHook_claim_consistency_tracker.py` | Stop | Tracks claim consistency across session | Contradicting previous claims |
| `verify_claims_transcript.py` | Stop | Verifies claims against full transcript | Cross-referencing claims with conversation history |
| `speculation_gate.py` | Stop | Blocks error/explanation claims without verification | Explaining errors without diagnostic evidence |
| `architecture_evidence_gate.py` | Stop | Blocks architecture proposals without evidence | Design suggestions without observational backing |
| `assumption_audit_v2.py` | Stop | Audits retrospective claims against tool evidence | Claims exceeding available evidence tiers |

**Typical Flow**:
```
User: "I fixed the bug"
    ↓
cross_validator: BLOCK → "Show test output"
    ↓
User: (shows pytest output)
    ↓
claim_consistency_tracker: LOG → Claim verified
    ↓
Action completes
```

**Meta-Conversation Exemption**:
- Self-referential statements skip verification: "I did not use TDD", "I only ran py_compile"
- External claims still require evidence: "The fix works", "Tests passed"

---

## Domain 5: STATE MANAGEMENT

**Purpose**: Maintain session state, context, and handoff.

| Hook | Event | What It Does | Use Cases |
|-------|-------|---------------|------------|
| `PreCompact_handoff_capture.py` | SessionStart | Captures session state before compaction | Preserving context across compactions |
| `PreCompact_handoff_router.py` | SessionStart | Routes handoff capture (in-process/subprocess) | Choosing execution mode for handoff |
| `SessionStart_initializer.py` | SessionStart | Initializes session state | First hook to run on session start |
| `SessionStart_semantic_daemon.py` | SessionStart | Auto-starts semantic search daemon | Enabling semantic search capabilities |

**Typical Flow**:
```
Session starts
    ↓
SessionStart_initializer: INIT → Create state directories
    ↓
SessionStart_semantic_daemon: START → Launch daemon
    ↓
PreCompact_handoff_router: ROUTE → Choose execution mode
    ↓
PreCompact_handoff_capture: CAPTURE → Save session state
```

---

## Domain 6: MONITORING & OBSERVABILITY

**Purpose**: Track hook performance, errors, and behavior.

| Hook | Event | What It Does | Use Cases |
|-------|-------|---------------|------------|
| `PostToolUse_system2.py` | PostToolUse | Monitors system2 thinking time | Tracking analysis phase duration |
| `PostToolUse_edit_verifier.py` | PostToolUse | Verifies file edits succeeded | Edit claimed success but file unchanged |
| `investigate_before_explain.py` | Stop | Ensures investigation before explanation | Explaining without diagnosing |
| `user_prompt_submit_concern_detection.py` | UserPromptSubmit | Detects user concerns in prompts | User expresses frustration or confusion |

**Typical Flow**:
```
Tool execution completes
    ↓
PostToolUse_system2: LOG → Thinking time recorded
    ↓
PostToolUse_edit_verifier: CHECK → File exists on disk?
    ↓
If fail: Alert user
```

---

## Domain 7: SPECIFICATION COMPLIANCE

**Purpose**: Ensure implementation matches specification.

| Hook | Event | What It Does | Use Cases |
|-------|-------|---------------|------------|
| `Stop/contract_validator.py` | Stop | Validates contract compliance | Implementation violates contract terms |
| `StopHook_spec_compliance.py` | Stop | Detects deviation from spec | Implementation differs from requirements |
| `constitutional_enforcer.py` | Stop | Prevents sycophantic behavior | Agreeing with user corrections that are wrong |

**Typical Flow**:
```
User: "Implement per spec.md"
    ↓
(Claude implements differently)
    ↓
StopHook_spec_compliance: BLOCK → "Deviation from spec"
    ↓
User: (aligns with spec)
    ↓
Action completes
```

---

## Router Pattern Hooks

**Purpose**: Consolidate multiple hooks for efficiency.

| Router | Event | Consolidated Hooks |
|---------|-------|-------------------|
| `UserPromptSubmit_router.py` | UserPromptSubmit | concern_detection, CKS decision load |
| `PreToolUse_write_router.py` | PreToolUse | file_lock, syntax validation, lib protection |
| `PreToolUse_bash_router.py` | PreToolUse | shell complexity, unparseable commands, recursive failure |
| `PostToolUse_router.py` | PostToolUse | 19 in-process hooks (monitoring, validation, tracking) |
| `PostToolUse_lint_router.py` | PostToolUse | Auto-formatting (ruff, prettier) |
| `PostToolUse_write_router.py` | PostToolUse | Post-write verification routing |
| `PostToolUse_task_router.py` | PostToolUse | Task tool operations |
| `Stop_router.py` | Stop | Validation sub-hooks |
| `SessionStart_router.py` | SessionStart | Initialization routing |
| `semantic_file_router.py` | PreToolUse | Semantic file operation routing |
| `path_resolution_orchestrator.py` | PreToolUse | Path protection and symlink blocking |
| `UserPromptSubmit_skill_router.py` | UserPromptSubmit | Skill auto-suggestion |

---

## Quick Reference: What Gets Blocked

| Category | Examples | Hook Domain |
|----------|-----------|--------------|
| **No plan** | "Just implement it" | Authority |
| **Vague directive** | "Improve the code" | Authority |
| **No investigation** | "Fix this bug" (without diagnosis) | Authority |
| **Protected paths** | "Edit C:\Windows\..." | Safety |
| **Secrets in output** | API key visible | Safety |
| **No test first** | Writing code before tests | Quality |
| **Unverified external claim** | "Fixed it", "Tests passed" (no evidence) | Verification |
| **Process/self-talk** | "I did not use TDD" | **Skipped** (meta-exemption) |

### Meta-Conversation Exemption

The following statements **do NOT** trigger cross-validation:

| Pattern | Example | Treatment |
|----------|-------------|------------|
| TDD status | "I did not use TDD" | Skip (allow) |
| Process description | "I only ran py_compile" | Skip (allow) |
| File operations | "I created X, modified Y" | Skip (allow) |
| Testing status | "No tests written yet" | Skip (allow) |
| Apologies | "Sorry, I misread" | Skip (allow) |

The following statements **STILL REQUIRE** verification:

| Pattern | Example | Treatment |
|----------|-------------|------------|
| Fix works | "The fix works now" | Block (require evidence) |
| Tests passed | "All tests passed" | Block (require evidence) |
| Hook success | "Hook returns {'ok': true}" | Block (require evidence) |
| File location | "File is at C:\path" | Block (require evidence) |

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `CONSTITUTIONAL_HOOKS_BYPASS` | 0 | Disable all constitutional hooks |
| `CROSS_VALIDATION_HOOK_ENABLED` | false | Block unverified "fixed" claims |
| `CROSS_VALIDATION_VERBOSE` | false | Warn instead of block |
| `HOOK_EDIT_VERIFICATION_ENABLED` | false | Require testing before hook edits |
| `HANDOFF_CAPTURE_INPROCESS` | 1 | Use in-process handoff capture |
| `CSF_HOOK_DEBUG` | 0 | Enable debug logging |
