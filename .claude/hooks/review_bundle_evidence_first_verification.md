# Review Bundle: Evidence-First & Verification Hooks

**Date:** 2026-02-08
**Purpose:** Document hooks implementing evidence-first contracts, chain-of-verification patterns, and source-bounded responses
**Comparison:** Discussion with another LLM about LLM guardrails frameworks

---

## Executive Summary

**Finding:** This codebase has extensive native implementations of all three patterns discussed. The hooks are more sophisticated than generic guardrails frameworks because they are:

1. **Tightly integrated** with Claude Code's hook protocol
2. **Constitutionally grounded** in CLAUDE.md principles
3. **Structurally enforced** (not just advisory warnings)
4. **Evidence-tiered** with confidence ceilings

**Key Difference:** External frameworks like Guardrails AI provide generic validation DSLs. These hooks provide domain-specific enforcement for solo development patterns.

---

## Pattern 1: Evidence-First Contracts

### Implementations

| Hook | Phase | Mechanism | Evidence Requirement |
|------|-------|-----------|---------------------|
| `PostToolUse_claimguard.py` | PostToolUse | Pattern-based claim extraction + verification against tool output | Claims must match actual tool output |
| `assumption_audit_v2.py` | Stop | Claim-entity extraction + evidence window with scoped invalidation | Claims need relevant observation tools |
| `StopHook_cross_validator.py` | Stop | "Fixed" claim detection + verification requirement | Success claims require test execution |
| `architecture_evidence_gate.py` | Stop | Architecture proposal detection + Tier 1 verification requirement | Design proposals need empirical testing |

### ClaimGuard Hook Details

**File:** `P:\.claude\hooks\PostToolUse_claimguard.py`

**Mechanism:**
```python
# Extracts claims from response using pattern matching
claims = extract_claims(response)

# Verifies each claim against actual tool output
for claim in claims:
    verification = verify_claim_against_output(claim, tool_output)

    if verification["verified"] is False:
        # Records false claim for metrics tracking
        record_claim(claim_type, claim_text, "FALSE", confidence)
```

**Evidence Tiers Enforced:**
- Tier 1 (95%): Execution artifacts, logs, test output
- Tier 2 (85%): Official docs, specs
- Tier 3 (75%): Static analysis, logical derivation
- Tier 4 (50%): Comments, unverified claims

**Remediation Message Format:**
```
⚠️ CLAIMGUARD: FALSE CLAIMS DETECTED

Your response contains N claim(s) that contradict actual tool output:

- "claim text..."
  Reason: [actual output shows otherwise]

**Before proceeding, you MUST:**
1. Quote the actual output - Show exact tool output, not paraphrasing
2. Cite your sources - Reference file:line or command output
3. Mark uncertainty - Use "tentative", "preliminary", "may be" if uncertain
```

### Settings.json Configuration

```json
{
  "env": {
    "CLAIM_VERIFICATION_ENABLED": "true",
    "CLAIM_VERIFICATION_MODE": "warn",
    "CLAIM_SCOPE_CHECK_ENABLED": "true",
    "CLAIM_COVERAGE_THRESHOLD": "0.5"
  }
}
```

---

## Pattern 2: Chain-of-Verification (CoVe)

### Implementations

| Hook | Phase | Verification Steps | Research Basis |
|------|-------|-------------------|----------------|
| `PostToolUse_system2.py` | PostToolUse | Error classification → Causal graph learning → Fix guidance | AutoDebugger pattern, Bayesian probability |
| `PostToolUse_falsification_assessor.py` | PostToolUse | Expectation recording → Outcome comparison → Mismatch detection | Falsification protocol |
| `speculation_gate.py` | Stop | Speculation detection → Tool-sequence verification → Evidence tier citation | Anti-speculation enforcement |
| `StopHook_cross_validator.py` | Stop | Claim detection → Verification check → Counterfactual requirement | Cross-validation research (Duke, MIT CSAIL) |

### System 2 Hook Details

**File:** `P:\.claude\hooks\PostToolUse_system2.py`

**Mechanism - Causal Graph Learning:**
```python
# Bayesian probability adjustment based on observed outcomes
CAUSAL_GRAPHS: Final = {
    "command_not_found": [
        {
            "cause_id": "unix_tool_not_available",
            "base_probability": 0.85,
            "evidence_checks": ["is_unix_tool", "has_python_alternative"],
            "fix_strategy": "suggest_python_alternative"
        },
        # ... more causes
    ]
}

# Load learned probabilities from previous outcomes
causal_state = _load_causal_learning()
if error_type in causal_state:
    learned = causal_state[error_type]
    for cause in causes:
        # Apply learned probability instead of base
        cause["adjusted_probability"] = learned[cause_id]["adjusted_probability"]
```

**Research Integration:**
- Causal graphs for suspect narrowing (AutoDebugger pattern)
- Bayesian probability adjustment based on observed outcomes
- Windows tool alternatives mapping
- High-confidence (70%+) immediate fix guidance
- Low-confidence (<70%) ReAct mode suggestion

### Falsification Assessor Details

**File:** `P:\.claude\hooks\PostToolUse_falsification_assessor.py`

**Protocol:**
```python
# TWO PROTOCOLS IN ONE HOOK:

# 1. Falsification Assessment
def detect_unexpected_outcome(tool_response):
    """Detect if outcome doesn't match expectation"""
    # Compare expected vs actual to detect hidden assumptions

# 2. Post-Action Verification
def should_show_verification(tool_name, tool_response, exit_code):
    """Determine if verification reminder should be shown"""
    # Only when issues detected (non-zero exit, errors in output)
```

**Post-Action Verification Protocol:**
- Prevents "I executed but didn't verify" gap
- Triggers verification reminders when:
  - Exit code != 0
  - Error patterns in output
- Reminds to Read file after Edit/Write
- Reminds to verify bash output matches intent

---

## Pattern 3: Source/Domain-Bounded Responses

### Implementations

| Hook | Phase | Bounding Mechanism | Domain |
|------|-------|-------------------|--------|
| `PreToolUse_investigation_gate.py` | PreToolUse | Blocks modifications without observation tools first | All modifications |
| `UserPromptSubmit_subagent_enforcer.py` | UserPromptSubmit | Detects non-trivial tasks → Requires subagent delegation | Task complexity |
| `PreToolUse_vague_directive_gate.py` | PreToolUse | Vague directive detection → Requires architecture first | Design/architecture |
| `PreToolUse_skill_pattern_gate.py` | PreToolUse | Regex + daemon validation for skill execution | Skill invocation |

### Investigation Gate Details

**File:** `P:\.claude\hooks\PreToolUse_investigation_gate.py`

**Constitutional Basis:** CLAUDE.md "Investigation before diagnosis"

**Mechanism:**
- Blocks Read/Grep/WebFetch when intent is diagnostic
- Requires full investigation before modification
- Error explanation patterns without verification trigger blocks
- Structural verification via ToolSequenceManager

**Blocked Patterns:**
```python
ERROR_EXPLANATION_PATTERNS = [
    r"(?:can't|cannot|couldn't|unable to) access",
    r"workspace restrict(?:ion)?s?",
    r"permission denied",
    r"(?:path|file|directory) (?:doesn't|does not|isn't|is not) exist",
    r"no such file or directory",
]
```

### Subagent Enforcer Details

**File:** `P:\.claude\hooks\UserPromptSubmit_subagent_enforcer.py`

**Mechanism:**
- Detects non-trivial tasks via pattern matching
- Requires subagent delegation (Task tool with specialized subagents)
- Bypasses for simple, direct tasks

**Task Complexity Signals:**
- Multi-step implementation
- Multiple files requiring coordination
- Complex decision-making
- Architecture decisions

---

## Settings.json Hook Configuration

### Evidence Hooks Registration

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python P:/.claude/hooks/UserPromptSubmit_router.py --timeout 15.0",
            "timeout": 15
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python P:/.claude/hooks/PostToolUse_router.py",
            "timeout": 8
          }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python P:/.claude/hooks/Stop_router.py --timeout 5.0",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Router Pattern

The codebase uses **consolidated routers** to reduce overhead:

- `UserPromptSubmit_router.py` - Consolidates multiple prompt hooks
- `PostToolUse_router.py` - Consolidates post-execution hooks
- `Stop_router.py` - Consolidates stop-phase hooks

Each router dispatches to specialized hooks based on:
- Tool name (for PreToolUse/PostToolUse)
- Response content patterns (for Stop)
- Intent classification (for UserPromptSubmit)

---

## Comparison: Native vs. External Frameworks

### Guardrails AI Comparison

| Feature | Guardrails AI | Native Hooks |
|---------|---------------|--------------|
| Integration | PostToolUse wrapper | Native Claude Code protocol |
| Validation | .rail files (DSL) | Python + regex patterns |
| Enforcement | Re-ask, fail, filter | Block, warn, inject context |
| State | Session-based | Terminal-isolated state files |
| Metrics | Basic | Comprehensive (metrics_tracker.py) |
| Evidence tracking | No | Yes (evidence_store.py) |

### Advantages of Native Implementation

1. **Deeper Integration:** Hooks have full access to tool inputs/outputs, conversation history, and session state

2. **Structural Enforcement:** Can block at PreToolUse (before action) not just PostToolUse (after generation)

3. **Terminal Isolation:** State is isolated per terminal/worktree to prevent cross-session bleed

4. **Constitutional Grounding:** Rules derive from CLAUDE.md principles, not generic safety

5. **Domain-Specific:** Patterns target solo-dev workflows (e.g., verification theater detection)

### Disadvantages

1. **Maintenance Burden:** Custom code vs. framework updates
2. **DSL Availability:** No visual .rail file editor
3. **Documentation:** Framework has official docs; this has inline comments

---

## Complete Hook Catalog

### Evidence-First Hooks

```python
# PostToolUse_claimguard.py (lines 1-438)
- Auto-verify factual claims about tool outputs
- Pattern-based claim detection
- Verification against actual tool output
- Warning/block based on severity
- Integration with metrics_tracker for KPI tracking

# assumption_audit_v2.py (lines 1-1510)
- BLOCKS responses with unverified claims
- Claim-entity extraction + scope verification
- Evidence window with scoped invalidation
- Verification theater detection (v2.4.0)
- Claim-local scope (v2.5.0)

# StopHook_cross_validator.py (lines 1-474)
- Detect "fixed" claims without empirical verification
- Separation of generation and verification
- Evidence access tracking
- Counterfactual requirement

# architecture_evidence_gate.py (lines 1-258)
- Blocks architecture/design proposals without observation tools
- Logs warnings for proposals lacking Tier 1 verification
- Enforces standards.md Pre-Architecture Verification Gate
```

### Chain-of-Verification Hooks

```python
# PostToolUse_system2.py (lines 1-694)
- Error classification with confidence scoring
- Causal graph learning from outcomes
- High-confidence: immediate fix guidance
- Low-confidence: ReAct mode suggestion
- Causal graphs for suspect narrowing

# PostToolUse_falsification_assessor.py (lines 1-502)
- Expectation recording before action
- Outcome comparison after action
- Mismatch detection with learning
- Post-action verification reminders

# speculation_gate.py (lines 1-283)
- Blocks unverified diagnostic claims
- Tool-sequence verification (v2.1.0)
- Evidence tier citation requirement
- Root cause claim validation
```

### Source-Bounded Hooks

```python
# PreToolUse_investigation_gate.py
- Blocks modifications without observation
- Error explanation without verification → block
- Structural verification via ToolSequenceManager

# UserPromptSubmit_subagent_enforcer.py
- Detects non-trivial tasks
- Requires Task tool with specialized subagents
- Bypass for simple direct tasks

# PreToolUse_vague_directive_gate.py
- Vague directive → architecture first
- CKS pattern retrieval integration
- Advisory suggestions from constitutional knowledge

# PreToolUse_skill_pattern_gate.py
- Regex + daemon validation
- Parallel pattern execution
- Intent-specific routing
```

---

## State Management Architecture

### Evidence Store

**File:** `P:\.claude\hooks\evidence_store.py`

**Purpose:** Durable session-scoped evidence storage for claim verification

**API:**
```python
from evidence_scope import SCOPE_SESSION_FRESH, load_scoped_tool_events
from evidence_store import resolve_session_id

session_id = resolve_session_id(session_id)
events = load_scoped_tool_events(
    session_id=session_id,
    scope=SCOPE_SESSION_FRESH,
    limit=500,
)
```

### Terminal Isolation

**Purpose:** Prevent cross-terminal bleed between concurrent sessions

**Implementation:**
```python
# terminal_detection.py
def detect_terminal_id():
    """Generate terminal-specific ID for state isolation"""
    # Uses process ID + timestamp for unique identification

# State directory per terminal
STATE_DIR = Path("P:/.claude/state/cross_validation") / TERMINAL_ID
```

### Metrics Tracking

**File:** `P:\__csf\src\rca\metrics_tracker.py`

**KPIs Tracked:**
- Claim verdict (TRUE/FALSE/UNVERIFIED)
- Confidence scores
- Evidence tier distribution
- Hook performance (latency)
- Block/warning ratios

---

## Deployment Recommendations

### For External Framework Adoption

**If adopting Guardrails AI:**

1. **Hybrid Approach:** Keep native hooks for domain-specific enforcement (verification theater, solo-dev patterns), use Guardrails for generic safety (PII, secrets)

2. **Wrapper Integration:** Call Guardrails from `PostToolUse_output_sanitizer.py` rather than replacing existing hooks

3. **Migration Path:**
   - Phase 1: Add Guardrails as additional validation layer
   - Phase 2: Evaluate overlap, consolidate where redundant
   - Phase 3: Retain native hooks for patterns Guardrails can't express

### For Native Enhancement

**Recommended additions based on external frameworks:**

1. **Visual DSL Editor:** Create .rail-like format for hook patterns
   - Benefit: Easier pattern maintenance
   - Complexity: Python → JSON compilation layer

2. **Unified Dashboard:** Aggregate all hook metrics
   - Currently: Scattered across SQLite, JSON logs
   - Target: Single observability UI

3. **Pattern Versioning:** Track pattern evolution with A/B testing
   - Currently: Git-based
   - Target: Experimental feature flags

---

## Appendix: Hook Protocol Summary

### Hook Events

| Event | Trigger | Capability | Evidence Access |
|-------|---------|------------|-----------------|
| SessionStart | CLI session begins | Initialize context | Full session history |
| UserPromptSubmit | Before prompt processing | Inject context, validate input | Prompt text only |
| PreToolUse | Before tool execution | **Block** actions, enforce prerequisites | Tool input only |
| PostToolUse | After tool completion | Analyze output, detect failures | Tool input + output |
| Stop | Response complete | Validate success claims, enforce verification | Full response + tools |

### Output Formats

```python
# UserPromptSubmit: Raw text (injected into context)
print(injection_content)

# PreToolUse: {"continue": bool, "reason": "..."}
print(json.dumps({"continue": False, "reason": "Investigation required"}))

# PostToolUse: {"warning": "..."} or {}
print(json.dumps({"warning": "Claim verification failed"}))

# Stop: {"allow": bool, "reason": "..."}
print(json.dumps({"decision": "block", "reason": "Unverified claim"}))
```

---

## Conclusion

This codebase implements **all three patterns** discussed with external frameworks:

1. **Evidence-First Contracts:** ClaimGuard, assumption_audit_v2, cross_validator
2. **Chain-of-Verification:** system2, falsification_assessor, speculation_gate
3. **Source/Domain-Bounded:** investigation_gate, subagent_enforcer, skill_pattern_gate

**Key Differentiator:** These hooks are **constitutionally grounded** in solo development principles rather than generic AI safety. They enforce domain-specific patterns (verification theater, investigation-before-diagnosis, show-don't-summarize) that generic frameworks cannot express.

**Recommendation:** Maintain native implementation for domain-specific patterns. Consider external frameworks only for generic safety (secrets, PII) where they provide proven, maintained implementations.
