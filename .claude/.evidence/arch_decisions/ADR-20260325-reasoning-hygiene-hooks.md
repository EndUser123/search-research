# ADR-20260325: Reasoning Hygiene Hooks

## Status

**Proposed**

## Context

Analysis of diagnostic reasoning sessions revealed five systemic thinking problems that cause suboptimal solutions:

| # | Problem | Pattern | Anti-Pattern | Fix |
|---|---------|---------|--------------|-----|
| 1 | "Good question" deflection | Answer directly, then analyze | Leading with acknowledgment before answer | Block or rephrase |
| 2 | Immediate vs optimal false equivalence | Recommend one with trade-offs stated | "works now" ≡ "optimal" | Recommend one with trade-offs stated |
| 3 | Root cause stated without verification | Test before stating | "root cause:" without preceding "Hypothesis:" + verification | Test before stating cause |
| 4 | Symptom treatment without root cause mapping | Map symptoms to shared cause first | Fixing 2+ issues without symptom-to-cause mapping | Map symptoms to shared cause |
| 5 | Surface verification before topic transitions | Show end-to-end evidence | "Looks correct" without evidence | Show end-to-end evidence |

### Why Stop Hooks?

**Core Problem: Verbal habits bypass content rules**

Constitutional constraints (CLAUDE.md) document the right behavior but cannot structurally enforce it. The gap:

| Approach | Enforcement Level | Why It Fails |
|----------|-----------------|--------------|
| Documentation (CLAUDE.md) | Advisory - depends on self-discipline | AI can talk around it, over-rule it, or simply ignore it when under pressure |
| Prompt engineering | Advisory - works until it doesn't | Patterns become formulaic; AI recognizes and performs the form without substance |
| Post-response feedback | Advisory - too late | AI has already moved cognitively; feedback arrives after the reasoning is set |
| **Stop hooks** | **Structural - intercepts before completion** | **Response is blocked before the reasoning pattern is finalized and sent** |

**Why Stop hooks work when documentation fails:**

1. **Timing**: Stop hooks fire AFTER generation but BEFORE response is shown. The AI has generated the response but hasn't received confirmation that it's "done." This is the moment of maximum receptivity to correction.

2. **Structural vs Content**: Content rules say "you should do X." Structural rules say "you cannot finish until you do X." The second type is enforceable because it creates a physical constraint, not just a suggestion.

3. **Habit interruption**: "Good question" deflection is a verbal habit, not a logical error. You cannot reason your way out of a habit - you need to interrupt the pattern at the execution level. Stop hooks provide that interruption.

**Why the 5-problem table led to Stop hooks:**

The diagnostic session revealed that these problems share a common structure:

```
Pattern: [Trigger] → [Premature conclusion] → [Missed verification]

Examples:
- "Good question" → Answer given → No evidence shown for answer
- "root cause:" → Cause stated → No hypothesis preceding it
- "let's move on" → Transition made → No verification shown for fix
```

This is not a knowledge problem - the AI knows the right behavior. It's a execution problem - the reasoning pattern completes before verification happens. Stop hooks address execution problems, not knowledge problems.

**Why not fix Problem 1 ("Good question") first?**

Sequential thinking (Problem 3 - hypothesis enforcement) was chosen as proof-of-concept because:
- **Clearest trigger pattern**: "root cause:" is unambiguous; "Good question" has legitimate uses
- **Highest impact on correctness**: Unverified hypotheses produce incorrect solutions
- **Most testable**: Verification evidence is binary (present/absent)
- **Least disruptive to normal conversation**: Blocks only diagnostic statements, not conversational acknowledgment

**Why sequential (pipeline) rather than parallel?**

| Pattern | Isolation | Complexity | Risk |
|---------|-----------|------------|------|
| Parallel (all 5 at once) | Poor - overlapping concerns | High - interactions between gates | False positives from interference |
| Sequential (pipeline) | Good - each gate is independent | Low - test one at a time | Misses issues while one gate is off |

Sequential is correct because:
1. Each problem has distinct detection logic
2. Gates can be disabled individually (env var per gate)
3. Debugging is tractable - one gate, one behavior
4. Order matters: hypothesis enforcement should fire before optimality check (need facts before tradeoffs)

**Why 5 separate files rather than 1?**

| Approach | Testability | Maintainability | Debugging |
|----------|-------------|-----------------|----------|
| One file with all 5 | Hard - entangled logic | Hard - fear of breaking other gates | Hard - which rule triggered? |
| Five files (pipeline) | Easy - test one gate at a time | Easy - change one without touching others | Easy - which file blocked? |

Lean principle: each hook does one thing. The "one thing" for Stop_hypothesis_enforcement is hypothesis-before-conclusion. Adding "Good question" detection would make a second problem someone has to understand when reading the file.

## Decision

Implement a **Hybrid Stop Hook Pipeline** with five sequential gates using two handler types:

```
Stop Hook Pipeline (sequential):
1. [PROMPT HOOK] Stop_good_question_gate      — LLM self-evaluation (semantic, context-dependent)
2. [CMD HOOK]   Stop_hypothesis_enforcement    — regex (binary, unambiguous trigger)
3. [CMD HOOK]   Stop_fix_verification_enforcer — regex (binary, evidence check)
4. [CMD HOOK]   Stop_optimality_check          — regex (pattern detection)
5. [CMD HOOK]   Stop_symptom_map               — regex (counting + mapping)
```

**Handler type rationale**:

| Gate | Handler | Why |
|------|---------|-----|
| Good question | Prompt (LLM) | Context-dependent — "Good question" has legitimate uses; needs semantic understanding |
| Hypothesis enforcement | Command (regex) | Binary trigger — "root cause:" is unambiguous; regex sufficient |
| Fix verification | Command (regex) | Binary trigger — evidence shown vs not; regex sufficient |
| Optimality check | Command (regex) | Pattern detection — "I recommend", "we should" sufficient |
| Symptom mapping | Command (regex) | Counting + structural — pattern sufficient |

**Latency budget**: Prompt hooks add 1-5s LLM inference; applied only to Gate 1 (~20% of responses). Gates 2-5 are <1ms.

### 1. Stop_good_question_gate (Prompt Hook)

**Purpose**: Block "Good question" deflection — direct answers first, then analyze.

**Handler Type**: `prompt` (Claude Code LLM self-evaluation)

**Prompt Template**:
```
Evaluate this response for reasoning hygiene violations:

{response}

Check for:
1. "Good question" deflection: Does response LEAD with acknowledgment before answering?
2. Direct answer: Does the response answer the question directly FIRST, then analyze?

Respond: CLEAN or VIOLATION + specific issue
```

**Block Message**:
```
DEFLECTION DETECTED

You began with "Good question" before answering.

Direct answers first, then analyze:
  "X is broken because..." not "Good question, let me explain..."

To disable: export REASONING_HYGIENE_ENABLED=false
```

### 2. Stop_hypothesis_enforcement.py

**Purpose**: Block "root cause:" statements without preceding "Hypothesis:" + verification.

**Detection Pattern**:
```python
_ROOT_CAUSE_PATTERN = re.compile(
    r"(?i)\broot\s+cause\s*[:]",
    re.IGNORECASE
)

_HYPOTHESIS_PATTERN = re.compile(
    r"(?i)\bhypothesis\s*[:]",
    re.IGNORECASE
)

# Check: Was "Hypothesis:" stated BEFORE "root cause:"?
# Check: Was verification evidence shown?
```

**Block Message**:
```
UNVERIFIED HYPOTHESIS DETECTED

You stated "root cause:" without:
1. Preceding "Hypothesis:" statement
2. Verification evidence (tool output, test results, file read)

Structure your reasoning:
  Hypothesis: X might be broken because Y
  Evidence: [tool output showing Y]
  Conclusion: Confirmed — root cause is Y

To disable: export REASONING_HYGIENE_ENABLED=false
```

### 3. Stop_fix_verification_enforcer.py

**Purpose**: Block topic transitions without explicit fix verification evidence.

**Detection Pattern**:
```python
_TOPIC_TRANSITION_PATTERNS = [
    r"(?i)moving\s+on",
    r"(?i)next\s+issue",
    r"(?i)let'?s\s+(?:talk\s+about|move\s+to)",
    r"(?i)changing\s+subject",
]
# Check: Was verification evidence shown for previous topic?
```

**Block Message**:
```
TOPIC TRANSITION WITHOUT VERIFICATION

You're moving to a new topic without verifying the fix for the previous issue.

Before transitioning:
1. Show evidence the fix works: tool output, test results
2. State what was verified
3. Then transition

To disable: export REASONING_HYGIENE_ENABLED=false
```

### 4. Stop_optimality_check.py

**Purpose**: Block solution recommendations without optimality assessment.

**Detection Pattern**:
```python
_SOLUTION_RECOMMENDATION_PATTERNS = [
    r"(?i)we\s+should",
    r"(?i)i\s+recommend",
    r"(?i)the\s+(?:best|correct)\s+approach",
]
# Check: Does response include "long_term_alternative" or "optimal_enough" assessment?
```

**Block Message**:
```
OPTIMALITY ASSESSMENT REQUIRED

When recommending a solution, assess alternatives:

Immediate: "do X" (works now, may not scale)
Optimal: "do Y" (better long-term, trade-offs documented)
Minimum: "do Z" (acceptable, known limitations)

Your recommendation must include:
- Which category (immediate/optimal/minimum)
- Key trade-offs vs alternatives
- Why this is "optimal enough" for the current context

To disable: export REASONING_HYGIENE_ENABLED=false
```

### 5. Stop_symptom_map.py

**Purpose**: Block fixes for 2+ symptoms without symptom-to-cause mapping.

**Detection Pattern**:
```python
# When user describes 2+ issues:
# Check: Did you identify shared root cause before fixing?
# Check: Did you state "symptoms of X" before treating symptoms?
```

**Block Message**:
```
SYMPTOM MAPPING REQUIRED

You described N issues without mapping them to a shared cause.

Before treating symptoms:
1. Identify: Are these N issues manifestations of ONE root cause?
2. State: "These symptoms all point to X"
3. Fix: Address X, not individual symptoms

If no shared cause exists, explain why these are independent issues.

To disable: export REASONING_HYGIENE_ENABLED=false
```

## Rationale

Full reasoning in "Why Stop Hooks?" section above. Summary:

1. **Timing** — Stop hooks intercept after generation but before response shown, when the AI is maximally receptive to correction
2. **Structural vs advisory** — Creates a hard constraint ("you cannot finish until X") rather than a suggestion ("you should do X")
3. **Habit interruption** — These are verbal habits, not logical errors; requires execution-level interruption, not reasoning-level explanation
4. **Sequential pipeline** — Each gate isolated for testability; order matters (hypothesis before optimality)
5. **Incremental via Proof-of-Concept** — Problem 3 (hypothesis enforcement) has clearest trigger, highest correctness impact, most testable

## Alternatives Considered

### Hook Handler Modalities

Claude Code supports three hook handler types, each with distinct tradeoffs:

| Handler Type | Evaluation Style | Speed | Cost | Latency | External API? |
|-------------|-----------------|-------|------|---------|--------------|
| `command` | Binary (regex/pass/fail) | Fast | Zero | <1ms | No |
| `prompt` | LLM self-evaluation | Medium | Low | 1-5s | **No** |
| `agent` | Reasoning + tools | Slow | High | 5-30s | No |

**Key insight**: All three handler types run within Claude Code's infrastructure. The `prompt` type uses Claude Code's own LLM for single-turn evaluation — no external API calls, no Ollama, no network latency beyond the LLM inference itself.

### Alternative 1: Command Hooks Only (Regex)

**Approach**: Pure regex pattern matching on response text.

```json
{
  "matcher": ".*",
  "hooks": [{
    "type": "command",
    "command": "python Stop_hypothesis_enforcement.py"
  }]
}
```

**Pros**: Fast (<1ms), zero cost, no latency impact
**Cons**: Brittle patterns, high false positive/negative rate, can't understand semantic meaning

### Alternative 2: Prompt Hooks (LLM Self-Evaluation)

**Approach**: Use Claude Code's built-in `prompt` hook type for LLM-based evaluation.

```json
{
  "matcher": ".*",
  "hooks": [{
    "type": "prompt",
    "prompt": "Evaluate this reasoning for hygiene violations:\n\n{response}\n\nCheck for:\n1. 'root cause:' without preceding 'Hypothesis:' + evidence\n2. 'Good question' deflection before answering\n3. Topic transition without fix verification\n4. Solution recommended without optimality assessment\n\nRespond CLEAN or VIOLATION + specific issue.",
    "timeout": 30
  }]
}
```

**Pros**:
- Uses Claude Code's own LLM — no external calls
- Semantic understanding — catches nuanced violations regex misses
- Same LLM evaluating its own output — maximally informed critique

**Cons**:
- Latency: 1-5s per response (LLM inference time)
- Sync only — blocks until evaluation completes

### Alternative 3: Hybrid (Command + Prompt)

**Approach**: Fast regex filter first, LLM critique only when uncertain.

```
Response generated
    ↓
[Command hook: regex check] → Clean response → Allow
    ↓ (uncertain)
[Prompt hook: LLM critique] → Violation found → Block + remediate
```

**Pros**:
- ~95% of responses: <1ms latency (regex passes)
- ~5% uncertain cases: LLM catches nuanced violations
- Best of both worlds: speed + accuracy

**Cons**:
- More complex architecture
- Two failure modes (regex failure, LLM failure)

### Decision: Hybrid (Command + Prompt)

The ADR's Stop hook pipeline (command hooks with regex) is the correct **starting point** because:

1. **Proof-of-concept value**: Regex catches obvious violations, validates the approach
2. **Minimal latency impact**: 99% of responses unaffected
3. **Iterative improvement**: Add Prompt hooks for high-value gates after measuring false positive rate

**Future enhancement**: After Phase 1-3, evaluate adding Prompt hooks for gates where regex false positive rate is unacceptable (particularly Problem 1 "Good question" detection where context matters).

## Implementation

### Phase 1: Stop_hypothesis_enforcement.py (Proof of Concept)

**Files to create**:
- `P:/.claude/hooks/Stop_hypothesis_enforcement.py`
- `P:/.claude/hooks/tests/test_stop_hypothesis_enforcement.py`

**Tests to pass**:
- Block "root cause:" without preceding "Hypothesis:"
- Allow "root cause:" after "Hypothesis:" + verification evidence
- Allow "root cause:" when verification evidence shown in same turn

### Phase 2: Stop_good_question_gate.py

**Files to create**:
- `P:/.claude/hooks/Stop_good_question_gate.py`
- `P:/.claude/hooks/tests/test_stop_good_question_gate.py`

### Phase 3: Remaining Gates

Implement in order of impact:
- Stop_fix_verification_enforcer.py
- Stop_optimality_check.py
- Stop_symptom_map.py

## Configuration

```json
{
  "env": {
    "REASONING_HYGIENE_ENABLED": "true",
    "REASONING_HYGIENE_MODE": "block"
  }
}
```

## Edge Cases

| Edge Case | Handling |
|-----------|----------|
| Legitimate "Good question" usage | Allow if answer follows immediately |
| Pre-verified root causes | Allow if evidence exists in conversation |
| Rapid-fire questions | Allow topic transition after brief verification |
| Independent symptoms | Explain independence before treating separately |

## Success Criteria

- [ ] Stop_hypothesis_enforcement.py implemented and tested
- [ ] Block message quality verified by user
- [ ] No false positives on legitimate reasoning patterns
- [ ] Sequential pipeline integrated (all 5 gates)

## Related Documents

- `vs_candidates_meta_cognitive_fix.md` — Original analysis
- `ADR-20260321-stale-state-file-cleanup.md` — Stop hook patterns

## Notes

**Implementation priority**: Start with Stop_hypothesis_enforcement.py (Problem 3) as it has the clearest trigger pattern and highest impact on reasoning quality.
