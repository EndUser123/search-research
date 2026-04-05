# ADR-20260329: AI Context Gap Self-Correction — False Gap Declaration Prevention

**Status**: Proposed

**Date**: 2026-03-29

**Target**: `/arch` skill + Hook enforcement layer

---

## Context

In a session on 2026-03-29, the AI demonstrated a recurring meta-cognitive failure pattern that made the interaction "infuriating":

**Transcript failure sequence** (lines from session log):
1. **False gap declaration** (line 199): AI said "I don't have the 'ideas' referenced in your question" — when ideas were present verbatim at lines 8-47 of the same conversation.
2. **Non-self-correction**: After user said "Think harder" (line 208), AI correctly retrieved context. But it would never have done so independently.
3. **Wrong initial verdict**: AI Defer'd Idea 2 (Convergence Gates) at line 98. Only corrected after "are you sure?" at line 401.

The `/arch` skill's **Stage 0.2 Follow-up Query Rewrite** already has the correct mechanism — it says to retrieve prior turn content when ordinal/skill references are detected. The AI skipped it.

---

## Problem Statement

AI declares context is missing when it is actually present in the prior conversation turns. This is a **meta-cognitive failure** — the AI treats its current context window as authoritative rather than searching its own transcript before claiming gaps.

**Root causes**:
1. **Metadata Dilution**: As context window fills, older content gets deprioritized by attention mechanisms. Instructions from session start fade.
2. **No enforcement gate**: The `/arch` skill trusts the AI to self-enforce Stage 0.2 with no blocking verification.
3. **No transcript search requirement**: The AI is not required to prove it searched prior turns before declaring a gap.

---

## Evidence from NotebookLM Research

Three relevant notebooks were queried: "Context, Memory, and Search" (946158e8), "Claude Code - Skills: Agentic Coding" (29bbaa7b), and "Transcripts and Logs" (83d187f3).

### Anti-Rationalization Gates (Stop Hooks)

> "When an AI falsely claims a task is 'out of scope' or that context is missing, it is often relying on a 'lazy' behavioral cop-out. You can physically block this by implementing an 'anti-rationalization gate' using a `Stop` event hook. By attaching a fast evaluator model (like Claude Haiku) to this hook, the evaluator intercepts the main agent's response right as it attempts to finish. If the evaluator detects a cop-out or premature victory, the hook exits with Code 2 (a blocking error), rejecting the response and feeding specific feedback back to the main agent."

### Context-Aware Prompt Hooks and Transcript Verification

> "To force the model to verify its own history before declaring a gap, you can configure context-aware prompt hooks. These hooks allow the evaluating LLM to read the raw transcript file to make intelligent, context-aware decisions. By instructing the model to review the full transcript path, you ensure it algorithmically parses its own historical record to verify completeness."

### Dynamic Rule Re-Injection (UserPromptSubmit Hooks)

> "As a session grows, models suffer from 'Metadata Dilution' and context rot, causing them to forget earlier instructions or context. To combat this, you can use a `UserPromptSubmit` hook, which intercepts the prompt right after you hit enter but before the AI processes it. This hook can automatically prepend a 'CRITICAL' reminder directly into the model's immediate attention."

### Metacognitive Co-Regulation

> "To address 'design fixation'—where an agent gets stuck in a flawed paradigm or repetitive loop—you can build a programmatic 'Progress Analyzer'. If the analyzer detects that the main agent is stalling, regressing, or blindly guessing, it formats a trajectory summary and exits with Code 2. This explicitly blocks the agent from continuing its flawed path and forces it to spawn a Metacognitive Co-Regulation subagent."

### Iterative Query Refinement

> "If an initial keyword search against the transcript yields poor results, the LLM leverages its reasoning capabilities to autonomously retry the search using different synonyms, concepts, or terms rather than immediately giving up and declaring a gap."

---

## Options

### Option A — Stop Hook Anti-Rationalization Gate (Recommended)

Create `StopHook_arch_gap_detection.py` that:
- Intercepts responses containing gap-declaring phrases: "I don't have", "context is missing", "not in the conversation", "was not provided", "I don't see"
- Searches the session transcript (via `transcript_path` from session context) for the referenced content
- **If found**: exits Code 2 with the found content forced back into context, telling the AI to continue with the verified context
- **If not found**: allows the response to pass

**Tradeoffs**:
- Favored quality: Correctness (blocks false gaps), Accountability (AI must prove search)
- Degraded quality: Latency (+1-2 turns on gap declarations)
- Failure condition: Hook script fails to parse transcript → allow pass with warning

### Option B — UserPromptSubmit Rule Re-Injection (Non-blocking)

Add to the `/arch` skill's execution preamble:
> "Before declaring any information missing, you MUST search the prior 10 conversation turns using transcript context. Do not declare a gap without verification. Quote what you searched for and where you looked."

**Tradeoffs**:
- Favored quality: Zero latency impact, no new hook required
- Degraded quality: Relies on AI self-enforcement (same failure mode as current)
- Failure condition: AI ignores re-injected rule → gap declaration still goes through

### Option C — Stage 0.2 Enforcement in Skill (Minimal change)

Make the Follow-up Query Rewrite step **verified** — require the AI to output its retrieved content inline before proceeding. Add to Stage 0.2:
> "Show the retrieved content in your response before proceeding. If no prior turn addressed this query, explicitly state 'No prior context found' before declaring a gap."

**Tradeoffs**:
- Favored quality: Zero latency, uses existing skill mechanism
- Degraded quality: AI could fabricate retrieval without actual search
- Failure condition: Fabricated retrieval → false gap still declared

---

## Decision

**Adopt Option A — Stop Hook Anti-Rationalization Gate**

Rationale from notebook research: "It forces a self-correcting loop where the agent must continue working and actually review the context." Option A is the only solution that doesn't rely on the AI following its own rules.

---

## Implementation Plan

### Phase 1: StopHook_arch_gap_detection.py

**File**: `P:\.claude\hooks\StopHook_arch_gap_detection.py`

**Trigger**: Stop event, when active session contains `/arch` skill invocation

**Detection patterns** (case-insensitive):
- "i don't have"
- "i cannot find"
- "context is missing"
- "not provided in the conversation"
- "was not discussed"
- "no prior context"
- ordinal references followed by "i don't have" / "missing"

**Transcript search**: Read session transcript from `transcript_path` env var or session JSONL, search for content matching the referenced idea/number/phrase.

**Exit behavior**:
- Gap found → Code 2, inject found content with instruction to continue
- Gap not found → Code 0 (allow)
- Parse error → Code 0 with stderr warning

### Phase 2: Integration

Register in `settings.json` under `hooks.stop`:
```json
"StopHook_arch_gap_detection": {
  "enabled": true,
  "skill_scope": ["arch"]
}
```

### Phase 3: Verification

1. Run `/arch "idea 2" are you sure?` — should NOT produce false gap at line 199 equivalent
2. Run `/arch "these ideas" worth adding to /pre-mortem?` — should retrieve prior context without user prompt
3. Confirm no latency impact on non-gap declarations

---

## Reversibility

**Score: 1.5** (minor complexity — adding a new hook, no existing behavior deleted)

Rollback: disable hook in settings.json, delete file. No data migration needed.

---

## Edge Cases

| Edge Case | Handling |
|-----------|----------|
| Transcript file not accessible | Exit Code 0 with stderr warning; do not block |
| Gap declared but ambiguous reference | Search for keywords; if no match, allow |
| AI uses paraphrased gap claim | Pattern match on "missing" / "don't have" / "not provided" |
| Very long transcript (>1MB) | Search first 500 lines only; if no match, allow |
