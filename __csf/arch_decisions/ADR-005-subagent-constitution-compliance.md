# ADR-005: Subagent Constitution Compliance Gap

**Status**: Proposed
**Date**: 2026-04-11
**Type**: Architecture Gap — Constitutional Enforcement
**Severity**: MEDIUM

---

## Context

GTO SuspicionDetector flagged GAP-0000-SUSPICION:
> "We need to follow our constitution tree. How can we make sure the subagents comply with it?" (confidence: 80%)

This is a **stateful, resumable, multi-terminal** system with constitutional hooks enforcing behavioral constraints on the primary agent. Subagents are spawned via the Agent tool as independent LLM calls.

---

## The Gap

**Subagents do not inherit constitutional constraints.**

When the primary agent spawns a subagent via `Agent(...)`, the subagent:
- Receives only its explicit `prompt` parameter
- Has **no access** to the parent session's hooks
- Has **no visibility** into constitutional rules (truthfulness, evidence-first, anti-sycophancy)
- Operates with only its own system context (model-specific defaults)
- Is **not tracked** by the hook system's telemetry

The `subagent_enforcer` hook that was supposed to address this has been **archived and removed** from the codebase. The HOOKS_CATALOG.md still references it at priority 13, but the module does not exist in `UserPromptSubmit_modules/` or anywhere in the hooks directory.

---

## Evidence

| Source | Finding |
|--------|---------|
| `UserPromptSubmit_modules/` (47 files) | No `subagent_enforcer.py` module exists |
| `HOOKS_CATALOG.md:79` | References `subagent_enforcer` at priority 13 as "Execution mode enforcement" |
| `analyze_hooks.py:63` | References `subagent_enforcer.jsonl` in telemetry catalog |
| GTO artifact | GAP-0000-SUSPICION flagged by SuspicionDetector — conversational misalignment |

---

## Analysis

### Current Enforcement Scope

Constitutional hooks (CLAUDE.md) enforce on the **primary agent only**:

| Hook | Event | What It Enforces |
|------|-------|-----------------|
| `PreToolUse_skill_pattern_gate.py` | PreToolUse | Skill workflow steps, parallel validation |
| `StopHook_skill_execution_gate.py` | Stop | Skill bypass detection |
| `StopHook_cross_validator.py` | Stop | Fabrication claims |
| `StopHook_unverified_stance.py` | Stop | Sycophancy detection |
| `constitutional_enforcer.py` | Stop | FORBIDDEN/TRUTH/SUCCESS/EVIDENCE categories |

**All enforcement is parent-agent-only.** Subagents spawned via `Agent(...)` are blind to all of this.

### Why This Matters

The constitutional principles (truthfulness, evidence-first, anti-fabrication) are core to the system's reliability. If subagents don't share these constraints, a subagent could:
- Fabricate evidence and present it as fact to the parent
- Make confident claims without verification
- Bypass skill-first execution patterns
- Ignore truthfulness constraints

The GTO SuspicionDetector caught this exact concern: the constitution tree is not being followed by subagents.

### What subagent_enforcer Was Supposed to Do

Based on the archived reference in HOOKS_CATALOG.md, `subagent_enforcer` at priority 13 was intended to enforce "execution mode" on subagents. Without the module, we cannot determine what specific enforcement it provided or why it was removed.

---

## Options

### Option A: Restore subagent_enforcer (RECOMMENDED)

**Re-implement the subagent constitutional injection hook.**

Location: `UserPromptSubmit_modules/subagent_enforcer.py`

Behavior:
1. Detect when prompt contains subagent spawning context (Agent tool calls, explicit subagent directives)
2. Inject constitutional constraints into the subagent's prompt
3. Track subagent invocations in telemetry

This is **advisory-only** — the hook can inject constraints but cannot force a subagent to comply, since the subagent runs as an independent LLM call. The effectiveness depends on the subagent reading and respecting the injected context.

**Pros**: Restores lost functionality, low implementation cost
**Cons**: Advisory only, cannot force compliance, hook behavior depends on subagent cooperation

### Option B: Accept Subagent Blind Spot

**Document that subagent constitutional compliance is out-of-scope for hooks.**

The Agent tool spawns independent LLM calls; constitutional enforcement is parent-agent-only. Subagent quality depends on prompt engineering.

**Pros**: No implementation cost
**Cons**: Constitutional gap persists, fabrications from subagents can pollute parent session

### Option C: Subagent Prompt Template with Constitutional Injection

**Create a shared `subagent_constitutional_context` template that all subagent prompts must include.**

When spawning subagents, inject:
```
CONSTITUTIONAL CONSTRAINTS (non-negotiable):
- Truthfulness: Do not fabricate evidence or claim unverified facts
- Evidence-first: Cite sources for all factual claims
- No sycophancy: Do not agree without independent verification
- Skill-first: Use Skill tool before direct implementation
```

**Pros**: Explicit, visible, auditable
**Cons**: Requires discipline — no mechanical enforcement

---

## Decision

**Option A + C** — Restore subagent_enforcer (for telemetry and advisory injection) AND use a shared constitutional template for explicit subagent prompt construction.

**Rationale**: The GTO SuspicionDetector correctly identified real risk. Option B is unacceptable because fabrications from subagents contaminate the parent session's artifacts (handoff envelopes, decision registers). Option C alone lacks observability. Combining both gives us both injection and tracking.

---

## Implementation

| Step | Action | File |
|------|--------|------|
| 1 | Restore `subagent_enforcer.py` in `UserPromptSubmit_modules/` | `UserPromptSubmit_modules/subagent_enforcer.py` |
| 2 | Add to `registry.py` hook priority | `UserPromptSubmit_modules/registry.py` |
| 3 | Create shared constitutional injection template | `__lib/subagent_constitutional_context.py` |
| 4 | Update HOOKS_CATALOG.md to reflect active state | `HOOKS_CATALOG.md` |
| 5 | Add telemetry logging to track subagent invocations | `subagent_enforcer.py` |

---

## Contract Authority Packet

**For the subagent constitutional injection boundary:**

| Field | Value |
|-------|-------|
| Boundary ID | `subagent-constitutional-injection` |
| Producer | `subagent_enforcer` hook (UserPromptSubmit) |
| Consumer | Subagent LLM calls via Agent tool |
| Input Schema | `{prompt: str, subagent_type: str}` |
| Output Schema | `{injected_prompt: str, constitutional_context: str}` |
| Required Fields | `prompt` |
| Optional Fields | `subagent_type` |
| Freshness Authority | Parent session — re-evaluate each turn |
| Invalidation Trigger | Session compaction, terminal restart |
| Failure Behavior | Degrade to plain prompt (no constitutional injection) |
| Validator Owner | `subagent_enforcer` telemetry |
| Proof Owner | Telemetry log at `logs/subagent_enforcer.jsonl` |

---

## Open Questions

1. Why was `subagent_enforcer` removed? No git history or deprecation record found.
2. Does the Agent tool support prompt injection into subagent system context, or only user-level prompts?
3. Should subagent constitutional compliance be **blocking** (hard enforcement) or **advisory** (injection + telemetry)?

---

## References

- GTO artifact: `P:/packages/handoff/.evidence/gto-outputs/gto-artifact-20260411_183740.json` (GAP-0000-SUSPICION)
- HOOKS_CATALOG.md: `subagent_enforcer` reference at priority 13
- CLAUDE.md: Constitutional hooks (PreToolUse, Stop events)
- `constitutional_enforcer.py`: Current Stop event constitutional enforcement
