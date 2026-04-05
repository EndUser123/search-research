# Overconfidence Detector

**File:** `StopHook_overconfidence_detector.py`  
**Module:** `anti_sycophancy/overconfidence_detector.py`  
**Event:** `Stop`  
**Version:** 1.1.0 (2026-01-25)

---

## Purpose

Detects and challenges claims made without traced evidence, with particular focus on **post-hoc attribution errors** where Claude observes an outcome during testing and incorrectly infers causation.

**Core problem:** Correlation (testing X, Y happened) ≠ causation (X caused Y). Multiple hooks/systems run simultaneously; contextual plausibility is not traced evidence.

---

## Failure Mode Example

```
User: Test the /v hooks
Claude: [runs command] → command gets blocked
Claude: "The /v skill hooks correctly blocked the python -c command"

WRONG: Actually blocked by unparseable_command_gate.py (different hook entirely)
```

**Why this happens:**
- Claude was testing /v hooks
- A block occurred during the test
- Claude inferred "/v hooks caused the block" without tracing
- Actual cause was a different hook in the Stop_router sequence

---

## Detection Patterns

### Outcome Attribution (New in v1.1.0)

| Pattern | Regex | Example |
|---------|-------|---------|
| Correct/successful action | `correctly\s+(?:blocked\|handled\|...)` | "correctly blocked" |
| Passive attribution | `(?:blocked\|handled\|...)\s+by` | "blocked by the hook" |
| Responsibility claim | `is\s+responsible\s+for` | "is responsible for" |
| Component attribution | `the\s+\w+\s+(?:hook\|gate\|...)\s+(?:blocked\|caught\|...)` | "The TDD hook caught this" |

### Root Cause Claims

| Pattern | Example |
|---------|---------|
| `the root cause (?:is\|was)` | "the root cause is X" |
| `this (?:explains\|shows) why` | "this explains why it failed" |
| `(?:proves\|demonstrates) that` | "this proves that X" |

### Certainty Markers

| Pattern | Example |
|---------|---------|
| `\bdefinitely\b` | "definitely caused by" |
| `\bcertainly\b` | "certainly the issue" |
| `\bclearly (?:shows\|indicates)` | "clearly shows that" |

---

## How It Works

### Architecture

```
Response text
    ↓
Stop_router.py executes HOOK_SEQUENCE
    ↓
StopHook_overconfidence_detector.py
    ↓
Imports anti_sycophancy.overconfidence_detector
    ↓
detect_all_overconfidence(response)
    ↓
Returns list of OverconfidenceMatch objects
    ↓
generate_self_prompt() creates reflection prompt
    ↓
Two modes:
  - Soft: Inject prompt → LLM self-corrects
  - Hard: Block response → Exit with decision: block
    ↓
log_block() → logs/constructional_blocks.jsonl
```

### Self-Prompt Generation

When attribution patterns are detected, the hook injects a self-assessment prompt:

```
**Outcome attribution without trace:** "correctly blocked"

Answer honestly:
1. Did you TRACE which component caused this outcome (hook logs, execution output)?
   Or did you INFER from context (testing X, Y happened, therefore X caused Y)?

2. Multiple hooks/systems run simultaneously. Did you verify WHICH ONE actually matched?
   Example: "unparseable_command_gate blocked" vs "/v hooks blocked" - very different!

3. If untraced, reframe as: "[INFERRED] The X hook may have caused this (50% confidence ceiling)"

Post-hoc attribution fallacy: Observing outcome during test of X ≠ proof that X caused outcome.
```

---

## Configuration

```bash
# Enable/disable the hook
OVERCONFIDENCE_DETECTOR_ENABLED=true    # default

# Soft mode (default): Inject self-prompt for reflection
OVERCONFIDENCE_DETECTOR_BLOCK=false

# Hard mode: Block response until claim is qualified
OVERCONFIDENCE_DETECTOR_BLOCK=true
```

---

## Integration with /hook-audit

All detections are logged to `logs/constructional_blocks.jsonl`:

```json
{
  "timestamp": "2026-01-25T16:30:19.123456",
  "hook_name": "overconfidence_detector",
  "tool": "Stop",
  "command": "correctly blocked...",
  "reason": "outcome_attribution: Trace which component caused outcome. Context ≠ causation",
  "severity": "WARN"
}
```

View with:
```bash
/hook-audit              # Full dashboard
/hook-audit blocks       # Blocking events
python analyze_blocks.py # Direct analysis
```

---

## Constitutional Basis

From `P:/.claude/CLAUDE.md` (lines 88-132):

> **Attribution Claims (Causal)**
> 
> When asserting that a specific component caused an observed outcome, the claim requires Tier 1 evidence (execution artifacts showing the causal chain).
> 
> **Required verification:**
> - Trace which component actually caused the outcome
> - Hook logs, execution output, or explicit causation evidence
> - NOT: "I was testing X, Y happened, therefore X caused Y"

---

## Testing

### Unit Tests

```bash
cd P:/.claude/hooks
python -m anti_sycophancy.overconfidence_detector
```

### Detection Test

```bash
python -c "
from anti_sycophancy.overconfidence_detector import detect_overconfidence
result = detect_overconfidence('The /v skill hooks correctly blocked the command')
print(f'Detected: {result.pattern_type} -> {result.matched}' if result else 'NOT DETECTED')
"
# Output: Detected: outcome_attribution -> correctly blocked
```

### End-to-End Test

```bash
echo '{"response": "The hook correctly blocked the python -c command"}' | \
  python StopHook_overconfidence_detector.py
```

---

## Relationship to Other Hooks

| Hook | Focus | Overlap |
|------|-------|---------|
| **Overconfidence Detector** | Causal attribution, certainty markers | — |
| **Sycophancy Agreement** | Unwarranted agreement ("you're right") | Complementary |
| **Success Validator** | Claims task is complete | Different trigger |
| **Empirical Claims Gate** | Testable factual claims | Different scope |

The anti_sycophancy module (`anti_sycophancy/overconfidence_detector.py`) is a **pure detection module** that can be imported by any hook. Currently only used by Stop phase because attribution errors appear in response text, not tool output.

---

## Limitations

1. **Pattern-based** — May miss novel phrasing of attribution claims
2. **No semantic understanding** — Can't verify if claim is actually correct
3. **Soft mode dependency** — Relies on LLM honesty in self-assessment
4. **Single-phase only** — Only catches errors at response time, not during generation

---

## Changelog

### v1.1.0 (2026-01-25)
- Added outcome attribution patterns (`correctly blocked`, `handled by`, etc.)
- Added self-prompt generation for attribution claims
- Fixed audit logging (was calling non-existent `record_violation()`)
- Integrated with hook_tracker.log_block()

### v1.0.0 (Initial)
- Root cause claim detection
- Certainty marker detection
- Basic self-prompt injection

---

_Evidence Tier: 2 (empirical testing) | Confidence: 80%_
