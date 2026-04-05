# ADR-20260325: Self-Correcting Agent Loop — Reducing Human Intervention

**Status**: Proposed
**Date**: 2026-03-25
**Context**: Session transcript shows three distinct AI failure modes requiring human correction. The AI reaches apparent completion (does something) but not optimal completion (does the right thing correctly).

## Decision

**Implement a hybrid self-correcting agent loop with three redundant verification paths:**

1. **Context Detector** — Recognize follow-up queries vs standalone queries
2. **Tool Availability Check** — Verify tool works before calling it
3. **Self-Verification** — Validate results against external standards before declaring done

### Problem Statement

From the session transcript (2026-03-25), the AI exhibited **three failure modes** requiring human intervention:

| # | Failure Mode | What Happened | What Should Have Happened |
|---|-------------|---------------|--------------------------|
| 1 | **Context Blindness** | AI interpreted "if that's the best practice" as standalone research query | Recognize as context-dependent follow-up about hook path fix |
| 2 | **Tool Selection Error** | AI called `/research` skill despite infrastructure failures (HyDE import error, ZAI module missing) | Verify tool availability before calling |
| 3 | **Premature Closure** | AI declared fix correct without web research, said "yes that's correct" | Self-verify against external best practices automatically |

**Root Cause**: The AI optimizes for *apparent completion* (I did something) rather than *optimal completion* (I did the right thing correctly). There is no automatic self-correction loop.

### Solution Architecture

```
User Query
    ↓
[Context Detector] → Follow-up? → If yes, load prior context from session
    ↓
[Tool Availability Check] → Tool works? → If no, use fallback immediately
    ↓
[Execute Action]
    ↓
[Self-Verification] → Matches best practices? → If no, re-research with fallback
    ↓
[Completion with Evidence]
```

### Why Three Redundant Paths?

Each path addresses different failure modes:

- **Context Detector** → Prevents #1 (Context Blindness)
- **Tool Availability Check** → Prevents #2 (Tool Selection Error)
- **Self-Verification** → Prevents #3 (Premature Closure)

Redundancy is intentional because these are **different failure modes**, not overlapping concerns.

## What Exists Today

Before implementing, verify which components are new vs extensions:

| Component | File Exists? | Status | Notes |
|-----------|-------------|--------|-------|
| Context Detector | **NO** | **NEW** | `context_followup_detector.py` does not exist |
| Tool Availability Checker | **NO** | **NEW** | `tool_availability_checker.py` does not exist |
| Self-Verification Gate | **NO** | **EXTEND** | `self_verification_gate.py` does not exist — extend `StopHook_unverified_stance.py` |
| `PreToolUse_tool_check.py` | YES | **EXISTS BUT WRONG PURPOSE** | Currently does parameter validation, NOT tool availability |
| `UserPromptSubmit_sequential_thinking.py` | **NO** | **NOT FOUND** | Remove any claim about extending this |

**Existing hooks that partially cover the problem**:

| Hook | Phase | What It Actually Does |
|------|-------|----------------------|
| `Stop_completion_verification_guard.py` | Stop | Blocks 8 file/folder operation claim types without evidence |
| `StopHook_overconfidence_detector.py` | Stop | Catches scope mismatch (global claims from local evidence) |
| `StopHook_unverified_stance.py` | Stop | Blocks "fixed"/"tested"/"verified" without runtime evidence |
| `StopHook_cross_validator.py` | Stop | Fabrication detection |
| `verify_before_claim.py` | UserPromptSubmit | Injects verify-before-claiming reminder |

## Implementation

| Component | Type | Location | Purpose | Status |
|-----------|------|----------|---------|--------|
| **Context Detector** | UserPromptSubmit hook | `P:/.claude/hooks/context_followup_detector.py` | Detect follow-up vs standalone | **DOES NOT EXIST — NEW** |
| **Tool Availability Check** | PreToolUse hook | `P:/.claude/hooks/tool_availability_checker.py` | Verify tool works before calling | **DOES NOT EXIST — NEW** |
| **Self-Verification** | PostToolUse hook | `P:/.claude/hooks/self_verification_gate.py` | Validate against external standards | **DOES NOT EXIST — EXTEND `StopHook_unverified_stance.py`** |

### Component Details

#### 1. Context Detector (UserPromptSubmit)

**Purpose**: Detect when a query is a follow-up to prior context vs a standalone query.

**Detection Logic**:
- Fragment patterns: "if that's", "what about", "also", "and the other"
- Pronoun references: "it", "that", "this" without prior noun clarification
- Implicit subject: Query lacks context that exists in prior turns

**Behavior on Detection**:
- Load prior turn context into working memory
- Set flag indicating follow-up mode
- Prevent standalone interpretation of fragment queries

#### 2. Tool Availability Checker (PreToolUse)

**Purpose**: Verify tool/skill works before executing it.

**Check Sequence**:
1. For skill invocations: Verify skill file exists and imports are valid
2. For bash commands: Verify command is in PATH
3. For MCP tools: Verify server is connected

**Behavior on Failure**:
- Immediately fall back to alternative tool
- Report unavailable tool with suggestion
- Do NOT proceed with known-broken tool

#### 3. Self-Verification Gate (PostToolUse)

**Purpose**: Validate results against external standards before declaring done.

**Verification Triggers** (automatic, not user-triggered):
- After implementing a fix: Check against official documentation
- After research query: Verify results against authoritative source
- After architectural decision: Validate against best practices

**Gap: Premature Completion Claims**

The Self-Verification Gate validates when the AI *knows* to verify. But the failure mode from the transcript shows AI declaring "yes that's correct" without triggering any verification — the AI stopped without realizing it hadn't verified.

**Existing Solution: Completion Claim Verification Hook**

This gap is already addressed by **existing hooks** that detect and block premature completion claims:

| Hook | File | Coverage |
|------|------|----------|
| `Stop_completion_verification_guard.py` | Stop | Blocks 8 file/folder operation claim types without evidence |
| `StopHook_overconfidence_detector.py` | Stop | Catches causal assertions, catastrophizing, scope mismatch (global claims from local evidence) |
| `StopHook_unverified_stance.py` | Stop | Extended with completion claim verification (blocks "fixed"/"tested"/"verified" without runtime evidence) |
| `StopHook_cross_validator.py` | Stop | Fabrication detection (fabricated tool usage, test results, research attempts) |
| `verify_before_claim.py` | UserPromptSubmit | Injects verify-before-claiming reminder for existence/absence queries |

**Optimal Solution: Extend Self-Verification Gate**

The Self-Verification Gate should integrate completion claim patterns from `StopHook_unverified_stance.py`:

```
Completion Claim Patterns (from existing implementation):
- "all (files|hooks|tests) pass"
- "✅ (complete|fixed|done)"
- "(issue|bug|problem) (is)? fixed"
- "test(s)? passed"
- "verified (and)? working"
- "working as intended"
- "system (works|is correct|is fine)"
```

**Runtime Evidence Requirements** (cross-validated against tool events):
- Bash execution (pytest, python, npm test, etc.)
- Read/Edit/Grep tool usage for verification
- Session-scoped evidence (multi-terminal safe)

**Behavior on Verification Failure**:
- If action was wrong: Loop back to research
- If tool was broken: Use fallback tool
- If completion claim unverified: Block with evidence requirement, do not allow "that's correct" to pass

## Multi-Terminal Safety

- **Safe**: Each component evaluates terminal-local state
- **No shared mutable state**: Each terminal's loop is independent
- **No cross-terminal propagation**: Context is terminal-isolated via `terminal_id`
- **State file pattern**: `state/followup_context_{terminal_id}.json` — uses `terminal_id` (not `session_id`) because session IDs change on every compaction

**Rationale**: The self-correcting loop operates within a single terminal's context. Session IDs change on compaction events — only `terminal_id` persists across compactions within the same terminal session.

## Constitutional Compliance

| Principle | Status | Evidence |
|-----------|--------|----------|
| **Multi-terminal isolation** | ✅ Safe | Terminal-scoped state via `terminal_id`, not `session_id` |
| **Hook design constraints** | ✅ Compliant | No external API calls in hot path |
| **Fail-open** | ⚠️ Needs design | Must not loop infinitely on verification failure |
| **Evidence-first** | ✅ Required | Self-verification requires external validation |

**Hook Constraint Note**: Tool Availability Checker must use local-only verification (file exists, import succeeds) — NOT external API calls. Self-verification may call external APIs but must have local fallback.

## Tradeoffs

| Quality | Improved | Degraded |
|---------|----------|----------|
| **Autonomy** | ✅ AI reaches optimal without prompting | ⚠️ Slight latency from verification steps |
| **Reliability** | ✅ Fewer human corrections | ⚠️ False positives may block valid queries |
| **Maintainability** | ✅ Clear separation of concerns | ⚠️ Three components to maintain |
| **Performance** | ⚠️ Verification adds overhead | ✅ But catches errors early |

## Failure Conditions

### Infinite Loop Risk
**Risk**: Self-verification fails → re-research → same result → loop

**Mitigation**:
- Maximum 2 re-research attempts per action
- If verification still fails after 2 loops, report failure with evidence
- User gets "cannot verify, manual review required" instead of silent loop

### False Positive Blocking
**Risk**: Context detector flags valid standalone query as follow-up

**Mitigation**:
- Conservative detection (require strong indicators)
- User can override with explicit "new topic" signal
- Log false positives for pattern tuning

### Tool Checker False Negatives
**Risk**: Tool passes availability check but fails at runtime

**Mitigation**:
- Runtime failures trigger fallback immediately
- Next invocation re-checks availability
- Accumulate failure history for smarter pre-checks

## Implementation Effort

| Task | Component | Time | Status |
|------|-----------|------|--------|
| Context Detector | UserPromptSubmit | 2-3 hours | **DOES NOT EXIST — net-new** |
| Tool Availability Checker | PreToolUse | 1-2 hours | **DOES NOT EXIST — net-new** |
| Self-Verification Gate | PostToolUse | 2 hours | **DOES NOT EXIST — extends `StopHook_unverified_stance.py`** |
| Completion Claim Integration | PostToolUse | 30 min | **Leverage existing** `Stop_completion_verification_guard.py` |
| Integration testing | All | 2 hours | — |
| **Total** | | **5.5-7.5 hours** | |

**Note**: Self-Verification Gate should extend `StopHook_unverified_stance.py` rather than creating new hook, leveraging its completion claim verification patterns. Context Detector is net-new — `UserPromptSubmit_sequential_thinking.py` does not exist in the codebase.

## Reversibility

**Score**: 1.5 (Moderate)

**Can revert by**:
- Disabling via environment variables (per-component toggle)
- Removing from hook sequence in `Stop_router.py`
- No permanent state changes

**Cannot revert if**: Hooks are removed from `settings.json` registration

## Edge Case Considerations

1. **All fallback tools fail**: Report failure with evidence, do not silently degrade
2. **Context detector conflicts with user intent**: User can say "new topic" to override
3. **Self-verification contradicts user belief**: Surface discrepancy, let user decide
4. **Tool checker blocks valid tool**: Graceful degradation to next attempt
5. **"Confidence without evidence" — AI declares correct without verification**: Addressed by existing `Stop_completion_verification_guard.py` and `StopHook_overconfidence_detector.py` (scope mismatch detection). Self-Verification Gate should integrate these patterns.
6. **All 3 verification paths fire simultaneously**: When Context Detector, Tool Availability Check, AND Self-Verification all flag the same response, this indicates a **systematic failure** — not a local error. Do not attempt to proceed. Surface a "multiple verification systems failed" error requiring human review. This compound case is qualitatively different from single-path failures.

## Why Not Just Hooks (Option A from analysis)?

Hook-only approach was rejected because:
- Hooks alone don't handle tool failures gracefully
- Tool checker requires PreToolUse, context requires UserPromptSubmit, verification requires PostToolUse
- These are **different hook phases**, not overlapping concerns

## Why Not Constitutional Prompts (Option B)?

Prompt-only approach was rejected because:

- **Prompts achieve only 70-90% compliance** under context pressure [16]
- Hooks achieve **100% compliance** — they execute at system level, outside LLM reasoning chain [16]
- AI can still bypass prompts with "helpful" deferrals
- Self-verification requires actual external validation, not just instructions
- Under long sessions or competing priorities, models eventually ignore instructions [16-18]

**Evidence**: "For anything that must happen, hooks are the enforcement mechanism." [16]

## Related Decisions

- **ADR-20260324**: Autonomy Gate — Enforcing explicit execution directives
- **ADR-20260323**: Cross-turn evidence carryforward — Prior context preservation
- **ADR-20260312**: Skill enforcement enhancement — Three-layer defense against bypass

## Research: NotebookLM Best Practices

Research from NotebookLM ("ClaudeFast and Claude Code Workflow Automation Guide", 292 sources) validates and extends this architecture with proven patterns from the Ralph Wiggum loop methodology.

### Key Findings

| Pattern | Source | Validation |
|---------|--------|------------|
| **Fresh Context Windows** | Ralph Wiggum Loop | ✅ Confirms need for context rotation per iteration |
| **Deterministic Hooks** | Hook Architecture | ✅ Hooks achieve 100% compliance vs 70-90% for prompts |
| **Completion Promises** | Ralph Exit Codes | ✅ `<promise>COMPLETE</promise>` with Exit Code 2 |
| **TDD as Oracle** | TDD + Agents | ✅ Tests create external oracle unaffected by context rot |
| **Circuit Breakers** | Cost Management | ✅ `--max-iterations`, token counters, cost limits |
| **Cold Code Review** | OctopusGarden | ✅ Blinded reviewer prevents sycophancy |
| **Demand-Driven Context** | DDC Methodology | ✅ Agent failure signals knowledge gaps |

### 1. Fresh Context Windows (Context Rot Prevention)

From Ralph Wiggum research [1-4]:

> "Each iteration of the loop should run in a completely fresh context window. Because the context is wiped clean each cycle, **state must be externalized to the file system**."

**Context layers across iterations**:

| Layer | Role | Persistence |
|-------|------|-------------|
| Short-term | Working memory for tool execution | Flushed per iteration |
| Intermediate | Current implementation state | Git history + progress.txt |
| Structural | Task list, requirements | prd.json |
| External | Project conventions, gotchas | AGENTS.md |

**Implication for this ADR**: The Self-Verification Gate must account for context degradation in long sessions. Verification evidence should be re-checked in fresh context.

### 2. Deterministic Lifecycle Hooks (100% Compliance)

From hook architecture research [16-20]:

> "Prompts achieve 70-90% compliance. Hooks achieve 100% compliance. They execute at the system level, outside the LLM's reasoning chain."

**Hook FSM roles**:

| Hook Event | FSM Role | Blocking Mechanism | Primary Use |
|------------|----------|-------------------|-------------|
| PreToolUse | Preventive Gate | Prevents tool execution | Blocking destructive commands |
| PostToolUse | Immediate Validator | Signals error after action | Auto-formatting, linting checks |
| **Stop** | **Final Gatekeeper** | **Blocks session termination** | **Ensuring tests pass before exit** |
| SubagentStop | Delegated Gate | Blocks subagent completion | Validating parallel task completion |

**Exit Code 2** is reserved for blocking errors that must be fed back to the agent. When a hook exits with code 2, stderr is injected into agent context as an error message, forcing a "Repair Turn" [24-26].

**Implication for this ADR**: Self-Verification Gate should use Stop hook for final completion verification, not PostToolUse.

### 3. Completion Promises

From Ralph pattern [30-36]:

The `<promise>COMPLETE</promise>` pattern:
- Completion promise is **static** (set once at loop start)
- Stop hook checks for exact string match
- Exit codes: 0=COMPLETE, 1=MAX_ITERATIONS, 2=BLOCKED, 3=DECIDE

```
Ralph Loop Exit Codes:
- Exit 0: All tasks finished successfully
- Exit 1: MAX_ITERATIONS reached
- Exit 2: BLOCKED - Needs human help
- Exit 3: DECIDE - Needs human decision
```

**Implication for this ADR**: Self-Verification Gate should emit Exit Code 2 when verification fails, forcing continuation.

### 4. TDD as Optimal Agentic Coding Strategy

From TDD research [37-39]:

> "Tests create an external oracle that stays accurate regardless of how long the session has been running. Each red-to-green cycle gives Claude unambiguous feedback, and it can iterate through the entire suite without human intervention."

**Implication for this ADR**: Self-verification should require passing tests, not just documentation checks.

### 5. Circuit Breakers (Cost Management)

From cost protection rules [54-58]:

> "Cost Protection Rules: Always set --max-iterations. Start conservative. Use lower limits first, increase if needed. Monitor spending."

**Stop Conditions**:
- `iterationCountIs(n)`: Stop after n iterations
- `tokenCountIs(n)`: Stop when total token usage exceeds n
- `costIs(maxCost, rates?)`: Stop when estimated cost exceeds maxCost

**Real-world costs**:
- 14-hour upgrade session: ~$50-100 in API costs
- 30-iteration React migration: ~$30-40
- 80-iteration refactor: ~$80-150

**Implication for this ADR**: Add explicit cost budgets to Self-Verification Gate to prevent runaway loops.

### 6. Cold Code Review (Adversarial Subagents)

From OctopusGarden/Cold Code Review [44-48]:

**Contract Specification**:
- **Scope Blindness**: Reviewer provided only final code diff + PRD acceptance criteria
- **Independent Reasoning**: Must evaluate "from cold" without Coder's thought process
- **Catch Rate**: Primary KPI is percentage of valid defects identified
- **Feedback Protocol**: Structured comments mapped to specific line numbers

**Implication for this ADR**: Add blinded reviewer requirement to Self-Verification for architectural decisions.

### 7. Demand-Driven Context (DDC)

From DDC research [49-53]:

> "Agent failure is a reliable signal for identifying knowledge gaps... Instead of curating knowledge and hoping it is useful, DDC gives agents real problems, lets them demand the context they need, and curates only the minimum knowledge required to succeed."

**Loop-Pause Trigger**: When agent encounters knowledge gap:
1. Loop pauses
2. Human expert provides minimum viable context
3. Knowledge graduated to permanent knowledge base

**Convergence hypothesis**: 20-30 DDC cycles produce sufficient knowledge base for a domain role.

**Implication for this ADR**: Self-Verification should trigger knowledge capture when encountering unknown patterns.

## References

- Source transcript: Session 2026-03-25 (hook path fix analysis)
- Problem manifestation: AI required 3 human corrections in single session
- Autonomy target: 80% reduction in human intervention corrections
- NotebookLM research: "ClaudeFast and Claude Code Workflow Automation Guide" (292 sources)

## Appendix: Existing Hooks Addressing "Confidence Without Evidence"

The "confidence without evidence" pattern was already identified and addressed in existing hooks. This ADR extends those patterns into the unified Self-Verification Gate.

### Confidence Scope Mismatch (Solution C from `StopHook_overconfidence_detector.py`)

**Problem**: AI makes global/system-wide claims ("working as intended") from single-file local evidence.

**Detection**:
```python
_GLOBAL_SCOPE_PATTERNS = re.compile(
    r"\b(?:"
    r"working\s+as\s+intended"
    r"|all\s+(?:cases?|instances?|tests?)\s+(?:pass|work|handled?)"
    r"|(?:the\s+)?system\s+(?:works?|is\s+(?:working|correct|fine))"
    r"|every(?:where|thing|one)\s+(?:works?|is\s+(?:handled?|correct))"
    r"|(?:no|zero)\s+(?:issues?|problems?|errors?)\s+(?:found|detected|exist)"
    r"|always\s+(?:works?|handles?|returns?)"
    r")\b", re.IGNORECASE)
```

**Trigger**: Response contains global scope claim AND only local Read/Skill tools used (no Bash).

**Fix**: Scope the claim to specific file, run Bash for runtime verification, or add uncertainty hedging.

### Completion Claim Verification (from `StopHook_unverified_stance.py`)

**Problem**: AI declares "fixed", "verified", "working" without runtime testing evidence.

**Detection Patterns**:
- "all (files|hooks|tests) pass"
- "✅ (complete|fixed|done)"
- "(issue|bug|problem) (is)? fixed"
- "test(s)? passed"
- "verified (and)? working"

**Evidence Requirements**: Bash tool execution (pytest, python -m pytest, npm test, etc.) in session history.

### Causal Assertion Detection (from `StopHook_overconfidence_detector.py`)

**Problem**: AI asserts causal relationships without evidence ("this explains why...").

**Patterns**:
- "this explains why..."
- "the root cause is..."
- "definitely/clearly the cause"
- "the hook correctly blocked..."

**Exemptions**: Evidence markers in response (`[Tier 1]:`, "logs show", "verified").
