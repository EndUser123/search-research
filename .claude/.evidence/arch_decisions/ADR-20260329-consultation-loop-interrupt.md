# ADR-20260329-consultation-loop-interrupt: Consultation Loop Detection and Interrupt

**Status:** Accepted
**Date:** 2026-03-29
**Context:** LLM repeatedly asks "which do you want?" after user has already decided. Root cause: consultation mode persists even when user directive is complete. The LLM treats "consider all of them, what has positive ROI?" as a question requiring another analysis, not a delegation signal. Pattern confirmed from commitment.txt transcript: user produced 13 ideas in NotebookLM, LLM re-digested them, asked "which should we do first?", user had to repeat the decision implicitly by saying "save the solution as an ADR."

### Decision

Implement a two-part solution:

1. **Stop Hook — Consultation Loop Detector** (`StopHook_consultation_loop_interrupt.py`)
   - Fires at session end or response completion
   - Scans transcript for consultation loop pattern: user directive → LLM asks clarifying question → user repeats directive → LLM asks another question
   - Logs detected loops to CKS as a pattern entry
   - If loop detected at session end, injects awareness into next session via session state

2. **UserPromptSubmit — Directive Recognition Injector** (`UserPromptSubmit_consultation_awareness.py`)
   - On each prompt, checks if prior LLM response ended with questions
   - Checks if current prompt is a repeat/continuation of a prior directive
   - If pattern matched: inject context reminding LLM the decision was already made
   - Does NOT block — only injects awareness

### Rationale

The consultation loop is a recognized failure mode in LLM assistants. Research from NotebookLM notebooks identifies several contributing factors:

- **Action Classification**: The LLM treats every user utterance as a planning request rather than recognizing delegation signals. The user saying "consider all of them" is not asking for another analysis — it's giving a directive that should trigger ranked execution.

- **Bounded Autonomy**: The system lacks a mechanism to classify "this is a decision the user already made, act on it." Without explicit action classification, the LLM defaults to consultation mode.

- **Consultation Mode Default**: The LLM optimizes for being helpful by asking questions. When the user has already decided, this becomes a friction loop instead of helpful.

The two-part approach is minimal and constitutional:
- Stop hook: Read-only analysis, no blocking, multi-terminal safe
- UserPromptSubmit: Advisory injection only, never blocks user input

### Alternatives Considered

| Option | Description | Pros | Cons | Why Rejected |
|--------|-------------|------|------|--------------|
| **Chosen** | Stop hook + UserPromptSubmit advisory | Minimal, non-blocking, constitutional | Advisory only, no hard enforcement | Best balance |
| PreToolUse hard block | Block tool execution when loop detected | Forces action | PreToolUse can't see LLM text output; wrong event for this | Architectural mismatch |
| ExitPlanMode interrupt | Interrupt plan mode after 1 iteration | Directly addresses plan-ask cycle | Requires detecting LLM reasoning state, not just tool calls | Hard to implement reliably |
| Settings change | `approval_policy = "never"` for low-risk actions | Simple | All-or-nothing, too aggressive | Would bypass legitimate confirmations |
| Dead Man's Switch | Cron-triggered autonomous execution | Solves continuity problem | User is present and interactive; wrong context | Not applicable |

### Multi-Terminal Safety

- **Stop hook**: Read-only transcript analysis. No shared state written. Multi-terminal safe.
- **UserPromptSubmit**: Injects context only, no blocking. No shared state. Multi-terminal safe.
- **CKS logging**: Pattern entries are append-only. No read/write conflicts.

### Edge Case Considerations

- **False positive — user genuinely asking a new question**: The UserPromptSubmit injector only fires when current prompt matches a prior directive pattern (exact or near-match). Genuinely new questions won't match and won't trigger injection.

- **False negative — user is genuinely undecided**: The system only injects when prior directive exists AND current prompt matches it. If user changes their mind, no injection fires.

- **CKS storage grows unbounded**: CKS has its own eviction policy. The consultation loop entry is just another data point.

- **Injected context is ignored**: The advisory injection provides awareness but doesn't force action. If LLM ignores it and asks again, Stop hook logs it for next session improvement.

### Clarification: Stop Hook Blocking Capability

The Stop hook CAN physically block session end via exit code 2 (the host catches this and forces continuation). The RCA enforcement hook uses this pattern. However, blocking is inappropriate for consultation loops because: (1) it prevents the user from ending the session when they choose — frustrating UX; (2) the user can simply start a new session to escape the loop. Advisory injection informs the LLM without depriving user control. CKS logging provides calibration data for future sessions.

### Implementation

**Stop Hook — `StopHook_consultation_loop_interrupt.py`**

Detection patterns:
```python
# User said something directive-like
DIRECTIVE_PATTERNS = [
    r"(?i)\b(?:consider all|implement|do|execute|start|begin|proceed)\b",
    r"(?i)\b(?:save the? |write an? )\b",
    r"(?i)\b(?:which (?:should |has )?(?:we|i) )\b",  # "which should we do"
]

# LLM responded with questions
QUESTION_RESPONSE_PATTERNS = [
    r"\?\s*$",  # ends with question
    r"which (?:would you|do you|should I|should we|do we|i)\b",
    r"(?:would you|should i|do you want|what do you)\b.*\?",
]

# Loop: user directive → LLM question → user repeats → LLM question
# Pattern: 2+ consecutive LLM question responses to same/similar directive
```

State tracking:
- Per-session, track `consecutive_question_responses` counter
- On directive detected: reset counter
- On question response after directive: increment counter
- If counter >= 2 and directive was in same session: log to CKS

Output: Advisory block message (not blocking stop):
```
CONSULTATION LOOP DETECTED

You appear to be repeating a directive that the LLM answered with questions:
  Directive: "consider all of them, what has positive ROI?"
  LLM response: Questions asking which to prioritize...

The LLM should recognize this as a delegation signal and proceed with ranked execution.
Consider: "Implementing the top-ranked item now." + action.

This pattern has been logged to CKS for calibration.
```

**UserPromptSubmit — `UserPromptSubmit_consultation_awareness.py`**

Detection (on each prompt):
1. Check if prior LLM response ended with question
2. Check if current prompt contains directive patterns (exact or near-match to prior)
3. If both true and directive was NOT yet acted upon: inject awareness

Injection:
```
DIRECTIVE-RECOGNITION: The user appears to be repeating a prior directive
("save the solution as an adr"). This is a DELEGATION signal — the decision
was already made. Proceed with execution immediately. Do not re-present options.

If you are uncertain what to do, begin implementing the highest-priority item
from the prior analysis rather than asking another clarifying question.
```

Registration: Both hooks registered via router pattern in Stop_router.py and UserPromptSubmit_router.py.

### Evidence Basis

- NotebookLM notebook research: "Agents often get trapped in infinite planning loops where they endlessly deliberate without executing" — ef1ea987 source
- Autonomous Escape Hatch pattern: "The human becomes a reviewer, not a trigger" — 25ca3293 source
- Cost-Aware Cascade: "only escalating to a human expert as an absolute last resort" — 52a2e1aa source
- Action-Biased Prompting: "take the simplest action that makes progress" works better than "think carefully about all possibilities" — ef1ea987 source
- Transcript evidence: commitment.txt shows exact pattern — user directive → LLM questions → user frustration

### Consequences

**Positive:**
- Consultation loops are surfaced rather than silently wasting time
- Pattern logging to CKS enables long-term calibration improvement
- Advisory injection reduces loop recurrence without blocking

**Negative:**
- Advisory only — LLM may still ask questions if context is compelling
- Two new hooks to maintain
- False positive injection could be annoying if directive matching is too loose

**Mitigation for false positives:**
- Use strict matching (exact/near-match, not fuzzy) to avoid triggering on new questions
- Counter threshold of 2+ ensures single-question responses don't trigger
- Logging provides feedback loop — if false positive rate is high, pattern thresholds can be tightened

### Confidence

Evidence basis:
- Direct transcript evidence from commitment.txt (Tier 1)
- NotebookLM research from 4 sources confirming consultation loop as recognized LLM failure mode (Tier 2)
- Hook architecture already supports Stop + UserPromptSubmit advisory pattern (existing hooks)

Confidence: 70% — advisory-only approach may not fully close the gap; hard enforcement would require architectural changes to LLM interaction model that aren't possible via hooks.

### Related Decisions

- **ADR-20260329-premortem-v6-enhancements**: Pre-mortem v6 enhancement portfolio (separate track, consultation loop affects it indirectly)
- **ADR-20260328-intelligence-stream-source-enumeration**: Existing ADR — unrelated domain
