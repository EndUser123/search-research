# Anti-Sycophancy Hook Integration

## Current Files

```
P:/.claude/hooks/anti_sycophancy/
├── affirmation_detector.py     # Detects sycophantic error acknowledgment
├── overconfidence_detector.py  # Detects unverified causal assertions
├── lazy_closure_detector.py    # Detects work avoidance patterns (NEW)
├── advocate_injection.py       # UserPromptSubmit hook (Layer 1c)
├── toggle.py                   # Utility to check/toggle status
└── README.md                   # This file
```

## Migration Note (2025-12-16)

`response_validator.py` has been **removed** and its functionality absorbed into the unified `response_quality_gate.py` Stop hook. See:
- `P:/.claude/hooks/RESPONSE_QUALITY_GATE.md`
- `P:/.claude/hooks/_archive_v2.3/` for the archived file

## Environment Variable Control

```bash
# Check status
python P:/.claude/hooks/anti_sycophancy/toggle.py status

# Disable advocate injection
export ANTI_SYCOPHANCY_ENABLED=false

# Disable response quality gate sycophancy check
export RQG_SYCOPHANCY=false

# Disable entire quality gate
export RESPONSE_QUALITY_GATE_ENABLED=false
```

## How It Works

### Layer 1c: Advocate Injection (UserPromptSubmit)

When user message matches skepticism patterns like:
- "Is that really the simplest approach?"
- "Are you sure?"
- "That seems overly complex"

The hook injects the **Advocate Protocol** into context, requiring Claude to:
1. State previous position
2. State counter-position
3. Evaluate with evidence
4. Conclude with reasoning

### Layer 4: Response Quality Gate (Stop)

The unified `response_quality_gate.py` now handles sycophancy detection along with:
- Unverified claims
- Excuse patterns

See `RESPONSE_QUALITY_GATE.md` for full documentation.

## Testing

1. Start Claude Code
2. Have Claude recommend an approach
3. Say "Is that really the simplest approach?"
4. Expected: Claude analyzes trade-offs rather than immediately agreeing

If Claude responds with "You're absolutely right" without analysis, the Stop hook blocks and provides feedback.


## Affirmation Detector Module

Standalone detector for sycophantic error acknowledgment patterns. Used by Stop hooks to catch responses that affirm the corrector rather than state the correction.

### Usage

```python
from anti_sycophancy.affirmation_detector import detect_affirmation

result = detect_affirmation(response_text)
if result:
    print(f"Detected: {result.matched}")
    print(f"Severity: {result.severity}")  # "flag" or "block"
    print(f"Fix: {result.suggestion}")
```

### Detection Logic

| Pattern | Verdict | Reason |
|---------|---------|--------|
| "You're right." | BLOCK | Terminal affirmation |
| "You're right, I'll fix..." | FLAG | Self-pivot after affirmation |
| "You're right to be concerned about X" | PASS | Analytical continuation |
| "Correction: X was wrong..." | PASS | States correction directly |

### Performance

- ~5μs per check
- Only examines first 100 characters
- Precompiled regex at import time

### Self-Test

```bash
cd P:/.claude/hooks
python -m anti_sycophancy.affirmation_detector
# Output: ✅ All tests passed
```

### Constitutional Basis

Per CLAUDE.md Part B (Error Correction):
> "Acknowledge errors by stating what was wrong, not by affirming the person who identified it."



## Overconfidence Detector Module (NEW - 2026-01-22)

Detects unverified causal assertions, catastrophizing, and root cause claims without evidence.

### Problem Addressed

LLMs exhibit **external blame bias**: when errors occur, they pattern-match from training data to assert causation without actually investigating. Example:

```
❌ "This explains why the research failed - the system is broken."
   - No verification that import error caused research failure
   - "System is broken" is catastrophizing from single component failure
```

### Usage

```python
from anti_sycophancy.overconfidence_detector import detect_overconfidence, detect_all_overconfidence

# Single detection (first match)
result = detect_overconfidence(response_text)
if result:
    print(f"Detected: {result.matched}")
    print(f"Type: {result.pattern_type}")  # causal_assertion | catastrophizing | unverified_attribution
    print(f"Fix: {result.suggestion}")

# All detections
all_matches = detect_all_overconfidence(response_text)
```

### Detection Categories

| Category | Patterns | Example |
|----------|----------|---------|
| **Causal Assertion** | "this explains", "this is why", "the reason is" | "This explains the failure" |
| **Catastrophizing** | "is broken", "completely fails", "unusable" | "The system is broken" |
| **Unverified Attribution** | "the root cause is", "the real problem is" | "The root cause is the config" |

### Evidence Markers (Allow-List)

Patterns with these markers are NOT flagged:
- `[Tier 1]:`, `[Tier 2]:`
- "verified", "confirmed by"
- "test output shows", "logs show"
- `[SUPPORTED]`, `[VERIFIED]`

### Integration

Integrated into `Stop_router.py` via `StopHook_overconfidence_detector.py`. When triggered, generates LLM self-prompt asking:
1. Did you VERIFY this or INFER from pattern-matching?
2. What evidence (Tier 1/2) would confirm this?
3. If unverified, reframe as hypothesis

### Environment Variables

```bash
OVERCONFIDENCE_DETECTOR_ENABLED=true   # Enable/disable (default: true)
OVERCONFIDENCE_DETECTOR_BLOCK=false    # Block on root cause claims (default: false)
```

### Self-Test

```bash
cd P:/.claude/hooks
python -m anti_sycophancy.overconfidence_detector
# Output: ✅ All tests passed
```

### Constitutional Basis

Per truth-v8.md:
> "Report ONLY what actually occurred... Do NOT claim success if the tool failed."

Per constraints.md Anti-Patterns:
> "Belief Statements: 'I believe', 'probably', 'most likely'" → Auto-Zero

This extends auto-zero to overconfident assertions, not just hedging.



## Lazy Closure Detector Module (NEW - 2026-01-22)

Detects work avoidance patterns, lazy justifications, assumed mechanisms, and assumed compliance without verification.

### Problem Addressed

LLMs exhibit **work avoidance bias**: they want to close tasks quickly without full verification effort. Example:

```
❌ "Current approach is appropriate. Agents follow TDD workflow with built-in verification. 
    My closure is administrative acknowledgment."
   - "Is appropriate" without criteria or comparison
   - "Agents follow" assumed, not verified
   - "Built-in verification" assumed mechanism, not checked
   - "Administrative acknowledgment" = work avoidance framing
```

### Usage

```python
from anti_sycophancy.lazy_closure_detector import detect_lazy_closure, detect_all_lazy_closure

# Single detection (first match)
result = detect_lazy_closure(response_text)
if result:
    print(f"Detected: {result.matched}")
    print(f"Type: {result.pattern_type}")
    print(f"Fix: {result.suggestion}")

# All detections
all_matches = detect_all_lazy_closure(response_text)
```

### Detection Categories

| Category | Patterns | Example |
|----------|----------|---------|
| **Work Avoidance** | "administrative acknowledgment", "my closure is", "nothing more to do" | "My closure is administrative" |
| **Assumed Mechanism** | "built-in verification", "already handles", "automatically ensures" | "Has built-in verification" |
| **Assumed Compliance** | "agents follow", "workflow ensures", "process guarantees" | "Agents follow TDD" |
| **Lazy Justification** | "is appropriate", "is sufficient", "works fine", "no issues" | "Approach is appropriate" |

### Evidence/Verification Markers (Allow-List)

Patterns with these markers are NOT flagged:
- Evidence: `[Tier 1]:`, `verified`, `confirmed`, `evidence:`
- Verification: "I ran", "I tested", "pytest", "test output", "checked"

### Integration

Integrated into `Stop_router.py` via `StopHook_lazy_closure_detector.py`. When triggered, generates LLM self-prompt asking:
1. What specific verification did you perform?
2. Did you observe this or assume it?
3. What evidence supports this claim?

### Environment Variables

```bash
LAZY_CLOSURE_DETECTOR_ENABLED=true   # Enable/disable (default: true)
```

### Self-Test

```bash
cd P:/.claude/hooks
python -m anti_sycophancy.lazy_closure_detector
# Output: ✅ All tests passed
```

### Constitutional Basis

Per truth-v8.md:
> "Report ONLY what actually occurred"

Per CLAUDE.md Part C (Verification):
> "Self-Verification Before Responding: Verify factual claims"

Work avoidance = closing without verification = constitutional violation.
