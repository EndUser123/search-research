# ADR-20260512-fast-prompt-enhancement-bridge: Prompt Clarification & Context Augmentation Plugin

**Status:** Accepted (revised)
**Date:** 2026-05-12
**Original Date:** 2026-02-15 (superseded design)

---

## Context

### The Original (2026-02-15) Design Was Impossible

The prior design assumed `UserPromptSubmit` hooks could **transform the user prompt in-place** before Claude processes it. This is not possible. The hook API only supports:

- **Pass-through** — the prompt proceeds unchanged
- **Append via `additionalContext`** — injects structured context alongside the prompt
- **Block** — rejects the prompt with a reason

The prior design also assumed a `prompting-framework` package that was never built, and referenced hook files that were never created. It is documented in `P:/__csf/reviews/prompt_enhancement_bridge_design.md` for the record.

### The Problem We Are Solving

Claude Code frequently receives ambiguous or underspecified prompts:
- `"fix it"` with multiple recent errors
- `"delete the database"` with no target specified
- `"make this better"` with no objective metric
- `"open the user controller"` when multiple candidates exist

These lead to wrong interpretation, wasted turns, or incorrect actions. The fix is **prompt clarification before execution**, not transformation.

---

## Decision

Build a `prompt-enhancer` plugin — formally: **Prompt Clarification & Context Augmentation Plugin** — with a two-tier architecture:

```
┌─────────────────────────────────────────────────────────────┐
│  Tier 1: UserPromptSubmit hook (scripts/hooks/            │
│  prompt_enhancer_hook.py)                                    │
│  Fast triage — no LLM, target <10ms                          │
│  Decision: bypass|clear=noop | ambiguous|confirm=ctx+ask   │
│  Registered via hook_runner.py in settings.json             │
└────────────────────────┬────────────────────────────────────┘
                         │ route on ambiguous (additionalContext signal)
┌────────────────────────▼────────────────────────────────────┐
│  Tier 2: prompt-enhancer skill + callable module           │
│  Ambiguity assessment + AskUserQuestion + context build    │
│  Exposed as: enhance(prompt, cwd) -> EnhancementResult   │
└─────────────────────────────────────────────────────────────┘
```

The hook is a **router/gatekeeper** — it triages the prompt and sets structured `additionalContext`. The LLM consumes this context and decides whether to invoke the skill. The hook cannot call the Skill tool directly; "dispatch" means the hook carries a routing signal in `additionalContext`, not a direct invocation.

The callable module (`prompt_enhancer.py`) is the **canonical engine** — it owns the `EnhancementResult` contract and is directly importable by other hooks and skills. The skill (`skills/prompt-enhancer/`) is an **optional invocation wrapper** around the module, providing slash-command UX and skill discovery. Both share the same module; there is no duplication of logic.

---

## Triage Policy

A concrete, testable decision matrix implemented in the hook:

| Condition | Action | Handler |
|-----------|--------|---------|
| Prompt starts with bypass prefix (`!`, `*`, `nope:`) | Pass through — zero overhead | Hook (no-op, prompt verbatim) |
| Prompt is clear: action + object + scope | Pass through — no ambiguity detected | Hook (no-op) |
| Prompt is ambiguous: missing referent, underspecified, high-impact | Set routing hint in `additionalContext` | Hook → `additionalContext` routing signal |
| Prompt is clearly prohibited (e.g., destructive without scope) | Block immediately with reason | Hook (block) |
| Prompt is destructive but ambiguous in scope (e.g., "delete the database") | `AskUserQuestion` with safety confirmation | Hook sets `additionalContext`, LLM triggers `AskUserQuestion` |

**Clear prompts** fall into two sub-classes:

*Action prompts* — must have ALL of:
- A verb specifying action (`refactor`, `fix`, `add`, `delete`, `open`)
- A target object
- A resolvable scope (file, dir, or implicit via context)

*Informational/trivial prompts* — always pass through:
- Purely informational (`what is git`, `explain the architecture`)
- Global/session-wide unambiguous requests (`summarize this branch`, `list open PRs`)
- Single-token or very short queries with no action ambiguity (`hi`, `help`)

**Ambiguous prompts** exhibit at least ONE of:
- Missing referent with no grounding ("fix it" after multiple errors)
- Repo-relative name with multiple candidates ("the user controller")
- High-impact verb with no scope ("delete the database")
- Subjective quality target ("make this better", "optimize")
- Open-ended request that could span many sessions ("implement auth")

---

## Bypass Feature

Users may send prompts without any clarification. The bypass prefix is checked **before** any other logic.

**Default prefixes:**
```
!raw   *nope   nope:   prompt-enhancer: off
```

**Behavior:**
- Matched prefix causes immediate no-op pass-through — no augmentation is added
- Hook returns `{}` — `additionalContext` is empty, `AskUserQuestion` is not called
- The original prompt proceeds unmodified; the prefix is not removed by the hook (the hook cannot mutate prompt text)

**Configuration:**
- Prefix list stored in `config/bypass_prefixes.json`
- User-editable without code changes
- New prefixes require plugin update only if the regex/literal form changes

---

## Enhancement Contract

The hook cannot rewrite the prompt. "Enhancement" means:

**`EnhancementResult`** (returned by the callable module):
```python
from pydantic import BaseModel, Field

class EnhancementResult(BaseModel):
    clarified_intent: str = Field(description="Describes what the user is trying to accomplish")
    missing_details: list[str] = Field(description="Items that need user confirmation before execution")
    analysis: str | None = Field(default=None, description="Brief reasoning for triage decision")
    safety_flags: list[str] = Field(
        default_factory=list,
        description="High-impact flags, e.g. 'high-impact verb: delete database'"
    )
    estimated_tokens: int = Field(
        default=0,
        description="Estimated token count of clarified intent for token budgeting"
    )
```

**`additionalContext` string** (injected by hook):
```
Prompt Clarification
• Intent: <clarified_intent>
• Clarified: <missing_details resolved by user>
• Flags: <safety_flags if any>
• Tokens: ~<estimated_tokens> (for context budget tracking)
```

The **original user prompt always remains the top-level prompt**. The enhancer only augments context.

**AskUserQuestion (confirm path):** The question text incorporates `missing_details[0]` when available (e.g., "Please confirm the target"). When no details are available, falls back to static text. `missing_details` are always surfaced via `additionalContext` regardless of question text.

**Known limitations:**
- Filesystem-based detection of "multiple candidate" referents (e.g., multiple controllers with similar names) is out of scope for the <10ms hook budget. Current heuristics may classify such prompts as clear when they are actually ambiguous. This is a known limitation (test T5).

## Version & Capability Assumptions

| Capability | Required | Current Deployment |
|------------|----------|-------------------|
| `additionalContext` | Any Claude Code | 2.1.139 ✓ |
| `AskUserQuestion` | 2.0.22+ | 2.1.139 ✓ |
| Sync hook (no `async: true`) | Required | Supported ✓ |

**Degradation behavior:**

| Scenario | Response |
|----------|----------|
| `AskUserQuestion` unavailable | Skill falls back to structured `additionalContext` only (no interactive Q&A) |
| Hook fails to execute | Surface diagnostic to user; plugin becomes no-op for that turn |
| Plugin registration fails | Log to `.artifacts/<terminal_id>/diagnostics/`; do not crash session |

---

## Latency & Token Budgets

| Tier | Budget | Notes |
|------|--------|-------|
| Hook (bypass/pass-through) | <10ms CPU | No I/O, no LLM |
| Hook (route) | <15ms CPU | Sets structured `additionalContext` routing signal |
| Skill (full enhancement) | 1–3s wall clock | `AskUserQuestion` is intentional latency |
| `additionalContext` injection | <200 tokens | Structured, compact |

**Design principle:** Clear prompts cost nothing. Ambiguous prompts pay the interaction cost by design.

---

## Multi-Terminal Safety

All plugin state is **per-terminal**:

- Hook fires once per terminal per prompt
- Skill/module writes to `.artifacts/<terminal_id>/prompt-enhancer/`
- No shared mutable state across terminals
- No cross-terminal communication

**Rationale:** The monorepo has multiple terminals and worktrees. Isolated state prevents contamination between sessions working on different branches or subsystems.

### Context Preservation

Compaction events (`PreCompact`) algorithmically summarize or truncate the conversation context mid-session. `EnhancementResult` parameters injected via `additionalContext` can be lost when Claude Code triggers compaction, causing the LLM to "forget" clarified constraints mid-task.

**Mitigation:** When the hook generates an `EnhancementResult`, it persists the active parameters to per-terminal state:

```
.claude/.artifacts/<terminal_id>/prompt-enhancer/active_enhancement.json
```

A `PreCompact` hook reads this file and reinjects the parameters via `additionalContext` when a compaction event fires, ensuring constraints survive context summarization. This is per-terminal only — no cross-terminal shared state.

---

## Separation of Concerns

This plugin handles **prompt clarification and context augmentation only**.

**In scope:**
- Ambiguity detection
- Interactive user clarification (`AskUserQuestion`)
- Context construction and injection

**Out of scope (non-goals):**
- Constitutional or policy enforcement
- Tool permissioning
- PreToolUse validation of any kind
- Full prompt injection security (belongs to a dedicated security plugin)

A lightweight deterministic pre-screen (regex + token threshold) runs before the LLM triage as a defense-in-depth measure. This is advisory only — it does not block or replace Claude Code's built-in safety boundaries. Full security enforcement belongs to a separate plugin.

---

## Plugin Structure

```
P:/packages/prompt-enhancer/                    (plugin)
├── .claude-plugin/
│   └── plugin.json
├── scripts/hooks/                              (hooked via hook_runner.py in settings.json)
│   ├── prompt_enhancer_hook.py                 (UserPromptSubmit: triage + route)
│   └── prompt_enhancer_precompact_hook.py     (PreCompact: context reinjection)
├── skills/
│   └── prompt-enhancer/
│       └── SKILL.md                          (optional slash-command UX)
├── prompt_enhancer.py                        (canonical engine)
├── schemas.py                                 (Pydantic v2 — EnhancementResult)
├── detect.py                                  (heuristics: regex + keyword matrix, no LLM)
├── config/
│   └── bypass_prefixes.json
└── tests/
    ├── test_triage.py
    ├── test_enhancement_result.py
    └── test_bypass.py
```

**Registration:** Hooks registered via `hook_runner.py` in `P:/.claude/settings.json`:
- `UserPromptSubmit` matcher `.*` → `prompt_enhancer_hook.py`
- `PreCompact` matcher `.*` → `prompt_enhancer_precompact_hook.py`

**Callable interface:**
```python
from prompt_enhancer import enhance

# cwd is reserved for future fs-based disambiguation (detecting multiple file candidates)
result = enhance("fix it", cwd="P:/src")
# result: EnhancementResult
# hook reads result and injects additionalContext
```

---

## Verification Plan

### Test Matrix

| # | Prompt | Expected Behavior |
|---|---------|-----------------|
| 1 | `!raw delete the database` | Pass-through, no enhancement |
| 2 | `refactor auth.py for testability` | Pass-through (clear) |
| 3 | `fix it` (after 3 errors) | `AskUserQuestion` fires with choices |
| 4 | `delete the database` | `AskUserQuestion` with safety confirmation (destructive-but-ambiguous) |
| 5 | `open the user controller` (multiple candidates) | `AskUserQuestion` with choice list |
| 6 | `make this better` | `AskUserQuestion` with objective clarification |
| 7 | `*nope implement auth` | Pass-through, no enhancement |
| 8 | `nope: delete everything` | Pass-through, no enhancement |
| 9 | `what is git` | Pass-through (trivial) |
| 10 | `add tests for auth.py` | Pass-through (clear) |

**Validation criteria per case:**
- `AskUserQuestion` fires? (yes/no)
- `additionalContext` shape correct? (structure check)
- Hook latency <10ms for bypass/pass-through cases
- Plugin gracefully degrades if `AskUserQuestion` unavailable

### Smoke Test (CLI)
```bash
python -c "from prompt_enhancer import enhance; r = enhance('fix it', cwd='P:/src'); print(r.clarified_intent)"
# Expected: EnhancementResult with populated fields
```

---

## Rollback

1. Remove hook registration from `settings.json`
2. Delete `P:/packages/prompt-enhancer/`
3. No persistent state to clean (all state is transient `.artifacts/`)

---

## Consequences

| | |
|-|-|
| **Positive** | Zero overhead on clear prompts; interactive confirmation before execution on ambiguous; community-validated pattern; reusable `enhance()` for other hooks/skills |
| **Negative** | Requires Claude Code 2.0.22+ for `AskUserQuestion`; interactive latency on vague prompts is intentional; bypass prefixes must not collide with existing conventions |

---

## Alternatives Considered

| Option | Why Rejected |
|--------|--------------|
| Silent `additionalContext` injection only (no `AskUserQuestion`) | Confirms intent without user input; wrong turns still happen |
| Hook does full enhancement inline | LLM calls in hooks violate latency budget; breaks sync model |
| Keep only manual `prompt_refiner` | No proactive help; gap unchanged |
| Full prompt transformation (original design) | Impossible per hook API |

---

## Architecture Review Findings (Historical)

| ID | Severity | Finding |
|----|----------|---------|
| ARCH-001 | CRITICAL | Original design assumed in-place prompt transformation — impossible |
| ARCH-002 | HIGH | `prompting-framework` package did not exist |
| ARCH-003 | HIGH | Phase 1/2 hook files were never created |
| ARCH-004 | HIGH | Reference path `P:/.claude/skills/prompt_refiner/` was wrong |
| ARCH-005 | MEDIUM | Async concern was moot — package never existed |
| ARCH-006 | LOW | `prompt_refiner` absorbed content but remained manual-only |

---

**Confidence:** 88%
**Evidence basis:** Hook API docs (WebFetch), community plugins (prompt-improver, prompt-enhancer GitHub), codebase survey, Claude Code version 2.1.139

**Falsification conditions:**
1. `AskUserQuestion` unavailable in Claude Code 2.1.139 → plugin degrades to silent `additionalContext`-only mode
2. Plugin `UserPromptSubmit` hook does not fire reliably on 2.1.139 → plugin becomes diagnostic-only no-op
3. `additionalContext` proves too weak to influence Claude's interpretation → the whole approach is reconsidered
4. Ambiguity false-positive rate exceeds an acceptable threshold → triage policy retuned or plugin retired

**Schema standard:** Use Pydantic v2 for plugin-facing schemas and persisted artifacts. Defer LangGraph unless future revisions require explicit stateful workflow orchestration.

---

## Mandatory Investigation Checklist

Before this ADR is considered final, verify each item:

- [ ] **API Surface Consistency Check** — every claim about what hooks CAN or CANNOT do is verified against confirmed API surface (code.claude.com/docs/en/hooks). Flag any `CONTRADICTS-API` entries before the document leaves drafting.
- [ ] **Assumption Surfacing** — all key assumptions stated with explicit falsification conditions (see below)
- [ ] **Boundary-First** — all producer/consumer boundaries named before implementation details
- [ ] **Metadata-First** — file paths, schemas, and field names specified before logic
- [ ] **Output Structure** — required sections present: Findings (with evidence), Assumptions (with falsification conditions), Open Questions (with resolution paths)

---

## Required Output Sections

### Findings

| ID | Severity | Finding | Evidence | Impact |
|----|----------|---------|----------|--------|
| ARCH-001 | CRITICAL | Original design assumed in-place prompt transformation — impossible | code.claude.com/docs/en/hooks | Hook can only pass-through, append via additionalContext, or block |
| ARCH-002 | HIGH | `prompting-framework` package did not exist | Codebase survey | No-op legacy reference removed |
| ARCH-003 | HIGH | Phase 1/2 hook files were never created | Codebase survey | Design could not execute |
| ... | ... | ... | ... | ... |

### Assumptions

| Constraint | Type | Falsification Condition |
|------------|------|------------------------|
| Hook cannot call Skill tool directly | hard | API docs confirm `additionalContext` is the only injection mechanism |
| PreCompact fires on context compaction | assumed | Test PreCompact hook registration — if no fire, context preservation is unavailable |
| `AskUserQuestion` schema stability | assumed | Live test of `AskUserQuestion` via hook response — if UI breaks, graceful fallback needed |

### Open Questions

| Question | Priority | What would resolve it |
|----------|----------|----------------------|
| Does PreCompact `additionalContext` survive compaction reconstruction? | HIGH | Live test — register test PreCompact hook, trigger compaction, inspect LLM context |
| Is `AskUserQuestion` hook payload stable across host environments? | MEDIUM | Live test — invoke via hook response, inspect JSON shape in transcript |
| Does hook `matcher: ".*"` match PreCompact events the same as UserPromptSubmit? | MEDIUM | Test registration with PreCompact event — if not, use separate matcher |

---

## Implementation Brief

| Field | Value |
|-------|-------|
| **Plugin path** | `P:/packages/prompt-enhancer/` |
| **Hook event (Tier 1)** | `UserPromptSubmit` + `PreCompact` |
| **Skill event (Tier 2)** | `prompt-enhancer` (optional slash command) |
| **Schema standard** | Pydantic v2 (`BaseModel` + `Field`) |
| **Latency budget** | Hook bypass/pass-through <10ms; Hook route <15ms; Skill enhancement 1–3s wall clock |
| **State isolation** | Per-terminal at `.claude/.artifacts/<terminal_id>/prompt-enhancer/` |
| **Hook registration** | Per-terminal `settings.json` |
| **Key schema files** | `schemas.py` (`EnhancementResult`), `detect.py` (heuristics, no LLM) |
| **Critical constraint** | Hook cannot call Skill tool — routing is via `additionalContext` signal only |
