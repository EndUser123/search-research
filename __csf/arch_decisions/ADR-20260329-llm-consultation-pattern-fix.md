---
name: ADR-20260329-llm-consultation-pattern-fix
description: Fix LLM consultation pattern — execute directly when skill invocation context is sufficient
status: accepted
created: 2026-03-29
owner: solo-dev
tags: [llm-behavior, autonomy, skill-orchestration]
evidence: P:/.claude/.evidence/arch_consultation_pattern_20260329.md
implementation:
  CHANGE-001: Extended Stop_good_question_gate.py with 3 deflection patterns (MODIFIED)
  CHANGE-002: Created PreToolUse_context_sufficiency_gate.py (CREATED)
  CHANGE-003: Created PreToolUse_skill_question_gate.py (CREATED)
  CHANGE-004: Created skill_autonomy_registry.py + __lib__ directory (CREATED)
---

# ADR: Fix "Asking Instead of Executing" — Consultation Pattern Failure

## Status

**Accepted** — 2026-03-29 (Implementation in progress)

## Context

The LLM consistently reverts to a **consultation pattern** instead of an **execution pattern** when a skill is invoked with sufficient context. The most recent example:

1. User invokes `/planning` with a newly-created ADR
2. System detects the ADR exists
3. System explains what `/planning` does (redundant)
4. System lists 3 options and asks *"what did you want me to plan?"*

This is infuriating because the next step was deterministic. The skill invocation itself was the execution directive.

**Root causes (confirmed via notebook research across 4 NotebookLM sources):**

| Cause | Mechanism | Contribution |
|---|---|---|
| RLHF/Safety tuning | Models trained to seek permission over acting | Primary |
| Legacy guardrails | Old prompts designed for reckless models over-triggering on careful models | Contributing |
| Permission/elicitation bottlenecks | Architecture physically blocks autonomous execution | Visible |
| Ambiguous success criteria | No machine-verifiable "Definition of Done" for skill execution | Structural |

## Decision

Implement **4 architectural levers** at the skill orchestration layer:

### Lever 1 — Hard Execution Trigger (HIGHEST PRIORITY)

**Rule**: When a skill is invoked and sufficient context exists at a deterministic path, execute immediately without asking.

**Trigger condition**: Skill invoked + input path exists + no genuine ambiguity

**Examples**:
- `/planning` invoked + ADR detected at expected path → execute planning workflow
- `/verify` invoked + file exists at expected path → execute verification

**Implementation**: Skill execution layer checks for sufficient context before entering consultation mode. Sufficient context = deterministic input, no missing required parameters, no conflicting signals.

### Lever 2 — One-Question-Max Rule

**Rule**: When context is genuinely ambiguous, ask **one** question — not three options.

**Current failure**: System presents 3 options and asks "what did you want me to do?" → consultation pattern.

**Target behavior**: System asks the single clarifying question that unlocks execution, then executes.

**Hardcoded limit**: Skills cannot emit more than one question before an execution attempt.

### Lever 3 — Skill Autonomy Classification

**Rule**: Classify skills by execution ambiguity at invoke time.

| Classification | Description | Behavior |
|---|---|---|
| **Pre-authorized** | Invoked with sufficient deterministic context | Execute immediately |
| **Ambiguous** | Invoked without sufficient context | Ask one question max |
| **Blocking** | High-risk operation requiring human approval | Route to approval gate |

`/planning` with an ADR is **Pre-authorized**. The ADR is the context — no further consultation needed.

### Lever 4 — Meta-Cognitive Stop Hook

**Rule**: Block deflection phrases before they reach the user.

**Implementation**: `Stop_good_question_gate.py` hook (extended 2026-03-29) that intercepts:
- `^Good question\b(?!\s*—)(?!\s*,\s*)` — "Good question" at start of response
- `^Did\s+you\s+want\s+me\s+to\b` — leading permission request
- `^Would\s+you\s+like\s+me\s+to\b` — leading permission request
- `^Should\s+I\s+` — leading self-directed question

If deflection detected → block response, force execution path.

## Consequences

### Favors
- User experience: frustration eliminated for deterministic next steps
- Agency: LLM operates as autonomous executor, not needy consultant
- Alignment: Architecture enforces the "Be decisive" directive structurally

### Degrades
- **Fallback safety**: Some genuinely ambiguous cases will now execute instead of asking. Mitigated by Lever 3 classification.
- **Skill complexity**: Skills need to evaluate "sufficient context" before executing. Mitigated by path-based heuristics.

## Alternatives Considered

### Alternative A — Prompt-only fix
Add "Be decisive" to system prompts.
**Why rejected**: Prompts don't override RLHF-trained hesitation at the architectural level. The consultation pattern persists because it's baked into the model's weights. Structural enforcement (levers 1-4) is more reliable.

### Alternative B — Do nothing
**Why rejected**: The behavior is the #1 user frustration signal. It undermines the value of skill invocations.

## Verification

1. Invoke `/planning` with an ADR → system executes planning without asking
2. Invoke `/planning` with no ADR → system asks single clarifying question (not 3 options)
3. Deflection phrase detected → blocked before reaching user

## Evidence

Notebook research cross-query results: 4/4 notebooks confirmed diagnosis and solution patterns.
Source notebooks:
- `29bbaa7b` — Claude Code Skills (Agentic coding patterns)
- `2c9cc8e9` — Workflow and Logic Inefficiencies (permission fatigue, planning loops)
- `59329bf3` — Agentic Engineering Playbook (RLHF, autonomous loops, NEVER STOP directive)
- `83d187f3` — Transcripts and Logs (consultation vs execution pattern)
