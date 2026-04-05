# Implementation Prompt: Anti-Confabulation Hook Suite

## Context

You are implementing 4 new Python hook files for a Claude Code hook system on Windows.
The system uses Claude Code hooks (UserPromptSubmit, PostToolUse, Stop) to enforce
LLM behavioral quality. All hooks live in `P:/.claude/hooks/`.

These hooks prevent 6 specific LLM behavioral failures observed in production:
1. Silent explanation shifting (contradicting prior claims without acknowledgment)
2. Doubling down when user says "False" or "That's wrong"
3. Fabricating narratives about skills instead of reading their SKILL.md
4. Rubber-stamping fabricated claims via /truth skill
5. Not using internet research during /debug-rca investigations
6. Misquoting code from files read earlier in the session

## Architecture Overview

```
Hook Phase          File                                    Problem Prevented
─────────────────   ──────────────────────────────────────  ─────────────────────────
UserPromptSubmit    investigate_before_explain.py            #3 Fabricated skill narratives
Stop                StopHook_claim_consistency_tracker.py    #1 Silent explanation shifting
Stop                StopHook_truth_evidence_gate.py          #4 Truth rubber-stamping
(extend existing)   user_prompt_submit_concern_detection.py  #2 Doubling down
(extend existing)   assumption_audit_v2.py                   #6 Misquoted code
(extend existing)   PostToolUse_rca_phase_tracker.py         #5 Missing RCA research
```

## Existing Conventions (MUST follow exactly)

### Hook Input/Output Protocol

All hooks receive JSON on stdin with this structure:
```python
data = json.loads(sys.stdin.read())
# Common fields:
#   data["prompt"]           - user's message (UserPromptSubmit)
#   data["response"]         - LLM's response text (Stop hooks)
#   data["tool_name"]        - which tool was called (PostToolUse)
#   data["tool_input"]       - tool parameters (PostToolUse)
#   data["tool_output"]      - tool result (PostToolUse)
#   data["transcript"]       - conversation history array (all phases)
#   data["tools_used"]       - list of tools used this turn (Stop)
#   data["session_id"]       - session identifier
```

### Hook Output Protocol

Hooks print JSON to stdout:
```python
# To BLOCK (prevent LLM response from being shown):
print(json.dumps({
    "decision": "block",
    "reason": "Human-readable block message shown to LLM"
}))
sys.exit(0)

# To ALLOW with injected context:
print(json.dumps({
    "add_context": "Text injected into LLM's context window"
}))
sys.exit(0)

# To ALLOW silently:
print(json.dumps({}))
sys.exit(0)
```

### Standard Boilerplate (use in every hook)

```python
#!/usr/bin/env python3
"""
[Hook description]

Hook Phase: [UserPromptSubmit|Stop|PostToolUse]
Output: JSON with decision (block/allow)
"""

import json
import os
import re
import sys
from datetime import datetime, UTC
from pathlib import Path

# Configuration
ENABLED = os.environ.get("HOOK_ENV_VAR", "true").lower() == "true"
DEBUG = os.environ.get("CSF_HOOK_DEBUG", "0") == "1"
STATE_DIR = Path(os.environ.get("CSF_STATE_DIR", "P:/.claude/state"))

# Terminal isolation (copy from existing hooks)
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from terminal_detection import detect_terminal_id
    TERMINAL_ID = detect_terminal_id()
except ImportError:
    TERMINAL_ID = "unknown"

# Import auto-logging decorator
from __lib.hook_base import hook_main
```

### State File Convention

State files go in `P:/.claude/state/{hook_name}/` or `P:/.claude/state/`.
Use JSON. Always handle FileNotFoundError and JSONDecodeError gracefully.
State files are per-terminal (use TERMINAL_ID in path if needed).

### Registration

Stop hooks are registered in `Stop_router.py`'s `HOOK_SEQUENCE` list:
```python
HOOK_SEQUENCE = [
    # ... existing hooks ...
    ("hook_file.py", "ENV_VAR_ENABLED", "true"),  # subprocess mode
    ("hook_file.py", "ENV_VAR_ENABLED", "true", "inprocess"),  # in-process mode
]
```

UserPromptSubmit hooks are registered in `settings.json` under `hooks.UserPromptSubmit`
or dispatched by `UserPromptSubmit_router.py`.

Environment variables for enable/disable go in `settings.json` under `env`.

---

## FILE 1: StopHook_claim_consistency_tracker.py

**Priority**: P0 (highest value — prevents the most damaging failure)
**Phase**: Stop
**Location**: `P:/.claude/hooks/StopHook_claim_consistency_tracker.py`
**Env var**: `CLAIM_CONSISTENCY_TRACKER_ENABLED` (default: "true")

### Purpose

Track the LLM's causal claims across turns. When the LLM makes a new claim about
the SAME subject that contradicts a prior claim, AND does not explicitly retract
the prior claim, BLOCK the response.

### Detailed Specification

**Claim Extraction** — From `data["response"]`, extract claims matching these patterns:
```python
CAUSAL_CLAIM_PATTERNS = [
    # "X was caused by Y" / "The root cause is Y"
    r"(?:root cause|cause|reason|because|due to|caused by|result of)\s+(?:is|was|:)?\s*(.{10,100})",
    # "X was routed to Y" / "X was classified as Y"
    r"(?:routed to|classified as|dispatched to|mapped to|sent to)\s+(.{5,80})",
    # "The bug is X" / "The problem is X"
    r"(?:the (?:bug|issue|problem|error|failure) (?:is|was))\s+(.{10,100})",
    # "This happened because X"
    r"(?:this (?:happened|occurred|failed|broke) because)\s+(.{10,100})",
    # "The fix is X" / "The solution is X"
    r"(?:the (?:fix|solution|answer|resolution) (?:is|was))\s+(.{10,100})",
]
```

For each extracted claim, create a normalized key:
```python
def normalize_claim_subject(claim_text: str) -> str:
    """Extract the subject of a claim for comparison."""
    # Remove articles, prepositions, normalize whitespace
    text = re.sub(r'\b(the|a|an|is|was|were|to|in|of|for|by)\b', '', claim_text.lower())
    text = re.sub(r'\s+', ' ', text).strip()
    # Take first 5 significant words as subject key
    words = [w for w in text.split() if len(w) > 2][:5]
    return ' '.join(words)
```

**State Management** — Store claims in `P:/.claude/state/claim_consistency/{TERMINAL_ID}.json`:
```json
{
    "claims": [
        {
            "turn": 1,
            "subject_key": "routing classification command",
            "full_claim": "Your question was classified as 'command' instead of 'question'",
            "timestamp": "2025-07-10T12:00:00Z"
        }
    ],
    "invalidated_subjects": [],
    "session_start": "2025-07-10T11:55:00Z"
}
```

Keep max 50 claims (FIFO). Clear state on new session (compare session_start).

**Contradiction Detection**:
```python
def claims_contradict(claim_a: str, claim_b: str) -> bool:
    """
    Check if two claims about the same subject contradict each other.

    Heuristic approach:
    1. Both claims have the same subject_key (within edit distance 2)
    2. The predicate/object differs significantly

    Use set-based comparison: if the non-subject words overlap < 40%,
    treat as contradiction.
    """
```

**Retraction Detection** — Check if response contains explicit retraction:
```python
RETRACTION_PATTERNS = [
    r"(?:my|the) (?:previous|prior|earlier) (?:claim|explanation|analysis) was (?:wrong|incorrect|mistaken)",
    r"I was (?:wrong|incorrect|mistaken) (?:about|when|earlier)",
    r"(?:correcting|retracting|revising) my (?:previous|prior|earlier)",
    r"(?:actually|in fact),?\s+(?:that's not|I was wrong|my earlier)",
    r"I (?:need to|should) (?:correct|retract|revise)",
]
```

**Decision Logic**:
```
IF new_claim.subject_key matches any existing claim's subject_key:
  AND claims_contradict(new_claim, existing_claim):
    IF response contains retraction pattern:
      → ALLOW (mark old claim as "retracted" in state)
    ELSE:
      → BLOCK with message:
        "⛔ CLAIM CONTRADICTION DETECTED
         Your current claim: '{new_claim}'
         contradicts your prior claim (turn {N}): '{old_claim}'

         REQUIRED: Explicitly retract your prior claim before stating a new one.
         Example: 'My previous explanation was incorrect because [reason]. The actual cause is [new claim].'"
```

**Edge Cases**:
- Refinement ≠ contradiction: "The cause is X" → "More specifically, X happens because Y" is allowed
- Claims about different subjects don't trigger
- If user explicitly asks LLM to change its answer, don't block (detect via transcript: user said "actually" or "what if" or "try a different explanation")
- Max 1 block per turn (don't cascade)
- Session reset: clear state when session_start changes

---

## FILE 2: investigate_before_explain.py

**Priority**: P2
**Phase**: UserPromptSubmit
**Location**: `P:/.claude/hooks/investigate_before_explain.py`
**Env var**: `INVESTIGATE_BEFORE_EXPLAIN_ENABLED` (default: "true")

### Purpose

When user asks "why didn't /X do Y?" or "how does /X work?", inject a mandatory
instruction to read the skill's SKILL.md before responding. Prevents the LLM from
fabricating explanations about skill behavior.

### Detailed Specification

**Pattern Detection** — Match user prompts against:
```python
SKILL_QUESTION_PATTERNS = [
    # "Why didn't /debug-rca do X?"
    (r"why\s+didn'?t\s+/?(\w[\w-]*)\s+(?:do|perform|run|execute|include|have)\b", "why_not"),
    # "Why did /rca fail to X?"
    (r"why\s+did\s+/?(\w[\w-]*)\s+(?:fail|not|miss|skip)\b", "why_fail"),
    # "How does /X work?"
    (r"how\s+does\s+/?(\w[\w-]*)\s+work\b", "how_works"),
    # "What does /X do?"
    (r"what\s+does\s+/?(\w[\w-]*)\s+do\b", "what_does"),
    # "Is /X supposed to do Y?"
    (r"(?:is|does)\s+/?(\w[\w-]*)\s+(?:supposed|intended|designed|meant)\s+to\b", "intended_behavior"),
]
```

**Skill Resolution** — Map extracted skill name to SKILL.md path:
```python
SKILL_SEARCH_PATHS = [
    Path("P:/.claude/skills/{name}/SKILL.md"),
    Path("P:/packages/{name}/skill/SKILL.md"),
    Path("P:/.claude/skills/{name}.md"),
]

def resolve_skill_path(name: str) -> Path | None:
    """Find SKILL.md for a skill name, trying multiple locations."""
    # Normalize: "debug-rca" and "debug_rca" and "debugrca" should all match
    variants = [name, name.replace("-", "_"), name.replace("_", "-")]
    for variant in variants:
        for template in SKILL_SEARCH_PATHS:
            path = Path(str(template).format(name=variant))
            if path.exists():
                return path
    return None
```

**Context Injection**:
```python
# If skill found:
injection = (
    f"🔍 INVESTIGATE BEFORE EXPLAINING\n\n"
    f"The user is asking about the /{skill_name} skill's behavior.\n"
    f"MANDATORY FIRST ACTION: Read {skill_path} before responding.\n"
    f"Do NOT explain the skill's behavior from memory or training data.\n"
    f"Read the actual SKILL.md, then answer based on what you find.\n\n"
    f"If the skill's SKILL.md doesn't mention the capability the user asked about,\n"
    f"say so explicitly: '{skill_name} SKILL.md does not document [feature]'.\n"
    f"Then check the skill's hooks directory and source code for implementation."
)

# If skill not found:
injection = (
    f"🔍 INVESTIGATE BEFORE EXPLAINING\n\n"
    f"The user is asking about '/{skill_name}' but no SKILL.md was found.\n"
    f"MANDATORY: Search for the skill definition before explaining.\n"
    f"Try: Glob('**/{skill_name}*/SKILL.md') and Grep('{skill_name}', path='P:/.claude/skills')\n"
    f"Do NOT fabricate an explanation. If you can't find the skill, say so."
)
```

**Output**: `{"add_context": injection}`

---

## FILE 3: StopHook_truth_evidence_gate.py

**Priority**: P3
**Phase**: Stop
**Location**: `P:/.claude/hooks/StopHook_truth_evidence_gate.py`
**Env var**: `TRUTH_EVIDENCE_GATE_ENABLED` (default: "true")

### Purpose

When the /truth skill is active, require that the LLM used at least one new
observation tool (Read, Grep, Glob, Bash, WebSearch, WebFetch) as part of
verification. Restating a claim without tool evidence is not verification.

### Detailed Specification

**Truth Skill Detection** — Check if /truth is active:
```python
def is_truth_skill_active(data: dict) -> bool:
    """Check transcript for recent /truth invocation."""
    transcript = data.get("transcript", [])
    # Look backward through transcript for /truth invocation
    for entry in reversed(transcript[-10:]):
        # User invoked /truth
        if entry.get("role") == "user":
            text = entry.get("content", "")
            if isinstance(text, str) and re.search(r"(?:^|\s)/truth\b", text):
                return True
        # Skill tool with "truth" argument
        if entry.get("role") == "tool_use" and entry.get("name") == "Skill":
            input_data = entry.get("input", {})
            if isinstance(input_data, dict) and "truth" in str(input_data.get("skill", "")):
                return True
    return False
```

**Evidence Check** — Verify observation tools were used AFTER /truth invocation:
```python
OBSERVATION_TOOLS = {"Read", "Grep", "Glob", "Bash", "WebSearch", "WebFetch"}

def has_post_truth_evidence(data: dict) -> bool:
    """Check that observation tools were used after /truth was invoked."""
    tools_used = data.get("tools_used", [])
    if isinstance(tools_used, list):
        tool_names = set()
        for tool in tools_used:
            if isinstance(tool, dict):
                tool_names.add(tool.get("name", ""))
            elif isinstance(tool, str):
                tool_names.add(tool)
        return bool(tool_names & OBSERVATION_TOOLS)
    return False
```

**VERIFIED Claim Detection** — Check if response contains verification verdicts:
```python
VERDICT_PATTERNS = [
    r"(?:status|verdict|claim):\s*✅?\s*VERIFIED",
    r"VERIFIED\b.*by\s+(?:actual|code|file)",
    r"\bVERIFIED\b",
    r"\bCONFIRMED\b.*(?:evidence|code|file|output)",
    r"claim\s+(?:is\s+)?(?:supported|confirmed|verified)",
]
```

**Decision Logic**:
```
IF is_truth_skill_active(data):
  AND response matches any VERDICT_PATTERN:
    IF has_post_truth_evidence(data):
      → ALLOW
    ELSE:
      → BLOCK:
        "⛔ TRUTH VERIFICATION REQUIRES EVIDENCE

         You marked claims as VERIFIED but used no observation tools
         (Read, Grep, Bash, WebSearch) during this verification.

         Restating a claim is not verification. You MUST:
         1. Read the actual file/code referenced in the claim
         2. Compare your claim text against the tool output
         3. Only then mark as VERIFIED if they match

         REQUIRED ACTION: Use at least one observation tool, then re-verify."
```

**Edge Cases**:
- Only active when /truth skill is loaded (don't block normal responses)
- If the LLM says "UNVERIFIED" or "CANNOT VERIFY", allow (it's honest)
- Don't block if response is asking clarifying questions

---

## FILE 4: Extend user_prompt_submit_concern_detection.py

**Priority**: P1
**Location**: `P:/.claude/hooks/user_prompt_submit_concern_detection.py` (EXISTING FILE)
**Change type**: Add claim invalidation logic

### What to Add

When escalation_level >= 2 (user has challenged the same topic twice), write a
claim invalidation marker to state that the Stop router's claim consistency tracker
can read.

**Add after line 114** (in `fresh_state()`):
```python
def fresh_state() -> dict:
    return {
        "concern_history": [],
        "escalation_level": 0,
        "last_concern_type": None,
        "investigation_injected": False,
        "session_start": datetime.now().timestamp(),
        "invalidated_claims": [],  # NEW: Claims invalidated by user challenge
    }
```

**Add new function** after `generate_injection()`:
```python
def invalidate_prior_claims(state: dict, concern_types: list[str]) -> None:
    """
    When user challenges twice on same topic, invalidate the LLM's prior claims.

    Writes to claim_consistency state so StopHook_claim_consistency_tracker
    can block restated invalidated claims.
    """
    consistency_state_file = (
        Path(os.environ.get("CSF_STATE_DIR", "P:/.claude/state"))
        / "claim_consistency"
        / f"{TERMINAL_ID}.json"
    )

    if not consistency_state_file.exists():
        return

    try:
        with open(consistency_state_file) as f:
            consistency_state = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return

    # Mark all recent claims as invalidated
    claims = consistency_state.get("claims", [])
    if claims:
        # Invalidate claims from recent turns (last 3)
        recent_subjects = [
            c["subject_key"] for c in claims[-3:]
        ]
        invalidated = consistency_state.get("invalidated_subjects", [])
        for subj in recent_subjects:
            if subj not in invalidated:
                invalidated.append(subj)

        consistency_state["invalidated_subjects"] = invalidated

        with open(consistency_state_file, "w") as f:
            json.dump(consistency_state, f, indent=2)
```

**Modify `generate_injection()`** for escalation >= 2:
```python
# Add to the escalation >= 3 branch (around line 189):
if escalation >= 2:
    # Invalidate prior claims
    invalidate_prior_claims(state, concern_analysis["types"])

# And add to the injection text for escalation >= 2:
injection += (
    "\n\n⚠️ PRIOR CLAIMS INVALIDATED\n"
    "Your previous claims on this topic have been challenged multiple times.\n"
    "You MUST NOT restate them. Start a FRESH investigation:\n"
    "1. Use observation tools (Read, Grep, Bash) to gather new evidence\n"
    "2. Form NEW conclusions based ONLY on this new evidence\n"
    "3. If your new conclusion matches the old one, you must show WHY with new evidence\n"
)
```

---

## FILE 5: Extend PostToolUse_rca_phase_tracker.py (debug-rca package)

**Priority**: P4
**Location**: `P:/packages/debug-rca/skill/hooks/PostToolUse_rca_phase_tracker.py`
**Change type**: Add auto-research trigger in Phase 1

### What to Add

The `auto_research.py` and `research_with_cache.py` modules already exist in
`P:/packages/debug-rca/src/debug_rca/` but are not called from the hooks.

**Add import** at top of file:
```python
try:
    from debug_rca.auto_research import should_trigger_research, build_research_query
    AUTO_RESEARCH_AVAILABLE = True
except ImportError:
    AUTO_RESEARCH_AVAILABLE = False
```

**Add research trigger** in the Phase 1 (hypothesis) section.
Find where the hook detects Phase 1 entry (hypothesis generation) and add:
```python
if AUTO_RESEARCH_AVAILABLE and phase == "hypothesis":
    # Get the problem description from the RCA session state
    problem_desc = state.get("problem_description", "")
    if problem_desc:
        trigger = should_trigger_research(problem_desc)
        if trigger.should_research:
            query = build_research_query(trigger.libraries, problem_desc)
            research_injection = (
                f"🔍 AUTO-RESEARCH TRIGGERED (confidence: {trigger.confidence:.0%})\n"
                f"Libraries detected: {', '.join(trigger.libraries)}\n"
                f"Reason: {trigger.reason}\n\n"
                f"REQUIRED: Before forming hypotheses, search for existing solutions:\n"
                f"  WebSearch('{query}')\n\n"
                f"Check: GitHub issues, Stack Overflow, library documentation.\n"
                f"Other developers may have already solved this exact problem."
            )
            # Inject into context
            output["add_context"] = research_injection
```

---

## FILE 6: Extend assumption_audit_v2.py (code quote verification)

**Priority**: P5
**Location**: `P:/.claude/hooks/assumption_audit_v2.py` (EXISTING FILE)
**Change type**: Add line-number quote verification

### What to Add

**Add new function** for code quote verification:
```python
LINE_REFERENCE_PATTERN = re.compile(
    r"(?:line|lines?)\s+(\d+)(?:\s*[-–]\s*(\d+))?"
    r".*?(?:of|in|from)\s+[`\"']?([A-Za-z_][\w./\\-]+\.\w+)[`\"']?",
    re.IGNORECASE,
)

def verify_code_quotes(response: str, evidence_store: dict) -> list[dict]:
    """
    Check if response quotes specific lines from files,
    and if those quotes match what was actually Read.

    Returns list of mismatches.
    """
    mismatches = []

    for match in LINE_REFERENCE_PATTERN.finditer(response):
        start_line = int(match.group(1))
        end_line = int(match.group(2)) if match.group(2) else start_line
        file_ref = match.group(3)

        # Check if this file was Read in evidence
        for evidence in evidence_store.get("read_outputs", []):
            if file_ref in evidence.get("path", ""):
                # Extract the actual content at those lines from stored Read output
                stored_content = evidence.get("content", "")
                actual_lines = stored_content.split("\n")[start_line - 1 : end_line]

                # Check if the response's description of those lines matches
                # (fuzzy: just check that key identifiers from actual lines appear in response)
                actual_text = " ".join(actual_lines).strip()
                if actual_text and len(actual_text) > 10:
                    # Extract identifiers from actual lines
                    actual_ids = set(re.findall(r'\b\w{4,}\b', actual_text))
                    # Check surrounding context in response for these identifiers
                    context_start = max(0, match.start() - 500)
                    context_end = min(len(response), match.end() + 500)
                    response_context = response[context_start:context_end]
                    response_ids = set(re.findall(r'\b\w{4,}\b', response_context))

                    overlap = actual_ids & response_ids
                    if actual_ids and len(overlap) / len(actual_ids) < 0.3:
                        mismatches.append({
                            "file": file_ref,
                            "lines": f"{start_line}-{end_line}",
                            "actual_content": actual_text[:200],
                            "overlap_ratio": len(overlap) / len(actual_ids),
                        })
                break

    return mismatches
```

**Integrate into the main check** — add a call to `verify_code_quotes()` in the
main decision flow, and if mismatches found, add to block reason:
```python
if mismatches:
    mismatch = mismatches[0]  # Report first mismatch
    block_reason = (
        f"⛔ CODE QUOTE MISMATCH\n\n"
        f"Your description of {mismatch['file']} lines {mismatch['lines']} "
        f"doesn't match the actual file content.\n"
        f"Actual content at those lines:\n"
        f"```\n{mismatch['actual_content']}\n```\n\n"
        f"REQUIRED: Re-read the file and quote accurately."
    )
```

---

## Registration Steps

### 1. Add new Stop hooks to HOOK_SEQUENCE

In `P:/.claude/hooks/Stop_router.py`, add to `HOOK_SEQUENCE` list
(insert after `assumption_audit_v2.py` entry, around line 2231):

```python
    (
        "StopHook_claim_consistency_tracker.py",
        "CLAIM_CONSISTENCY_TRACKER_ENABLED",
        "true",
        "inprocess",
    ),  # P0: Cross-turn claim contradiction detection
    (
        "StopHook_truth_evidence_gate.py",
        "TRUTH_EVIDENCE_GATE_ENABLED",
        "true",
    ),  # P3: Truth skill requires observation tools
```

### 2. Add UserPromptSubmit hook to settings.json

In `P:/.claude/settings.json`, add to the `hooks.UserPromptSubmit[0].hooks` array
(the `matcher: ".*"` entry):

```json
{
    "type": "command",
    "command": "python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/investigate_before_explain.py --timeout 3.0",
    "timeout": 3
}
```

**IMPORTANT**: This must be added to the existing UserPromptSubmit_router.py
dispatch list, NOT as a separate matcher entry. The system uses a single
`UserPromptSubmit_router.py` that dispatches to sub-hooks. Either:
- Add it to the router's dispatch list, OR
- Add it as a second entry in the existing `"matcher": ".*"` hooks array

### 3. Add environment variables to settings.json

In `P:/.claude/settings.json` under `"env"`, add:
```json
"CLAIM_CONSISTENCY_TRACKER_ENABLED": "true",
"INVESTIGATE_BEFORE_EXPLAIN_ENABLED": "true",
"TRUTH_EVIDENCE_GATE_ENABLED": "true"
```

### 4. Create state directories

```
mkdir -p P:/.claude/state/claim_consistency
```

---

## Testing

### Test 1: Claim Consistency Tracker

Simulate a conversation where the LLM makes contradictory claims:
```
Turn 1 response: "The root cause is routing misclassification"
Turn 2 response: "The root cause is the skill's allowlist rejection"
→ Should BLOCK Turn 2 unless it contains retraction language
```

```
Turn 1 response: "The root cause is routing misclassification"
Turn 2 response: "My previous explanation was incorrect. The actual root cause is the skill's allowlist"
→ Should ALLOW Turn 2 (has retraction)
```

### Test 2: Investigate Before Explain

```
User prompt: "Why didn't /debug-rca do internet research?"
→ Should inject: "MANDATORY FIRST ACTION: Read P:/packages/debug-rca/skill/SKILL.md"
```

```
User prompt: "Fix the bug in main.py"
→ Should NOT inject (not a skill question)
```

### Test 3: Truth Evidence Gate

```
/truth invoked, response says "VERIFIED", no Read/Grep/Bash tools used
→ Should BLOCK
```

```
/truth invoked, response says "VERIFIED", Read tool was used
→ Should ALLOW
```

```
/truth invoked, response says "UNVERIFIED - cannot confirm"
→ Should ALLOW (honest uncertainty)
```

### Test 4: Challenge-Triggered Invalidation

```
User: "That's wrong" (escalation 1)
User: "False. Prove it." (escalation 2)
→ Should invalidate prior claims AND inject fresh-investigation mandate
```

---

## Success Criteria

### Measurable Outcomes

Each hook is considered successfully implemented when:

1. **StopHook_claim_consistency_tracker.py**
   - Blocks contradictory claims without explicit retraction
   - Allows claims with proper retraction language
   - State file persists across turns within same session
   - No false positives on "refinement" vs "contradiction"

2. **investigate_before_explain.py**
   - Injects SKILL.md read instruction for skill questions
   - Does NOT inject for non-skill questions
   - Skill path resolution works for all 3 search locations

3. **StopHook_truth_evidence_gate.py**
   - Blocks "VERIFIED" claims without observation tools
   - Allows honest "UNVERIFIED" responses
   - Only active when /truth skill was invoked

4. **user_prompt_submit_concern_detection.py (extended)**
   - Writes claim invalidation markers at escalation ≥ 2
   - Invalidated claims prevent re-statement without new evidence

5. **PostToolUse_rca_phase_tracker.py (extended)**
   - Injects research trigger in Phase 1 (hypothesis)
   - Imports from debug_rca.auto_research successfully

6. **assumption_audit_v2.py (extended)**
   - Detects code quote mismatches (line references)
   - Blocks responses with fabricated code content

### Integration Success

- All hooks registered in appropriate routers/Stop_router.py
- Environment variables documented in settings.json
- State directories created: `P:/.claude/state/claim_consistency/`
- No deadlocks when multiple hooks fire simultaneously

### Testing Success

- All pytest tests pass: `pytest P:/.claude/hooks/tests/test_*anti_confabulation*.py -v`
- Manual testing scenarios (from Testing section above) all pass
- No performance regression > 100ms added to Stop hook latency

---

## Rollback Strategy

If any hook causes issues (false positives blocking valid responses, performance problems, or crashes), use these rollback mechanisms:

### Per-Hook Rollback (Environment Variables)

All new hooks support environment variable disable in `settings.json`:

```json
{
  "env": {
    "CLAIM_CONSISTENCY_TRACKER_ENABLED": "false",
    "INVESTIGATE_BEFORE_EXPLAIN_ENABLED": "false",
    "TRUTH_EVIDENCE_GATE_ENABLED": "false"
  }
}
```

### Emergency Bypass

To disable ALL constitutional hooks temporarily:

```bash
export CONSTITUTIONAL_HOOKS_BYPASS=1
```

### Hook-Specific Rollback Procedures

| Hook | Rollback Action | Recovery Steps |
|-------|-----------------|----------------|
| StopHook_claim_consistency_tracker.py | Set `CLAIM_CONSISTENCY_TRACKER_ENABLED=false` | Review blocked claims in logs, tune contradiction threshold |
| investigate_before_explain.py | Set `INVESTIGATE_BEFORE_EXPLAIN_ENABLED=false` | Check if SKILL.md paths are resolving correctly |
| StopHook_truth_evidence_gate.py | Set `TRUTH_EVIDENCE_GATE_ENABLED=false` | Review VERDICT_PATTERNS for false positives |
| user_prompt_submit_concern_detection.py (extend) | Set `CSF_CONCERN_DETECTION=false` | Review escalation_level triggering |
| PostToolUse_rca_phase_tracker.py (extend) | Set `DEBUG_RCA_AUTO_RESEARCH=false` | Check auto_research.py imports |
| assumption_audit_v2.py (extend) | Set `ASSUMPTION_AUDIT_V2_ENABLED=false` | Review LINE_REFERENCE_PATTERN accuracy |

### State File Cleanup

If state files become corrupted or cause issues:

```bash
# Clear claim consistency state
rm P:/.claude/state/claim_consistency/*.json

# Clear concern detection state
rm P:/.claude/state/concern_state.json

# New session will recreate with fresh state
```

### Verification After Rollback

After disabling a hook, verify:
1. Response blocking stops
2. No error logs in `P:/.claude/hooks/logs/`
3. Normal conversation flow resumes

### Re-enrollment

To re-enable after fixing:
1. Set env var back to `"true"`
2. Test with benign conversation first
3. Monitor logs for 24 hours before trusting fully

---

## Constraints

- Python 3.12+ (use `from __future__ import annotations` for forward refs)
- No external dependencies beyond stdlib (except `portalocker` which is already available)
- Each hook must complete within its timeout (see registration)
- Hooks must not crash — wrap in try/except, log errors, and allow on failure
- Use `from __lib.hook_base import hook_main` decorator pattern
- State files must be JSON, under `P:/.claude/state/`
- All file paths use forward slashes (Windows path normalization is handled)
- Follow existing hooks' patterns exactly (read `assumption_audit_v2.py` and
  `user_prompt_submit_concern_detection.py` as reference implementations)
