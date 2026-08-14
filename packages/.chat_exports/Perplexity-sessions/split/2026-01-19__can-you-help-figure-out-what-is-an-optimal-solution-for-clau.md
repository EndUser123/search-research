---
title: "Can you help figure out what is an optimal solution for claude code on windows?

[Prompt Enhancements.](https://claude.a"
date: "2026-01-19"
mode: "COPILOT"
uuid: "d7c48aa8-ce91-40bc-a180-803046266870"
entry_count: 2
---

## Human

Can you help figure out what is an optimal solution for claude code on windows?

[Prompt Enhancements.](https://claude.ai/project/019af216-64e8-729b-b960-1769b854af2b)/
I thought we had hooks to stop this nonsense:
  The statusline shows "Test" likely because the task system categorizes these
  background task checks as test/verification operations. The tasks themselves failed,
  but the actual file update succeeded via a different method (staging protocol).
  Ready to commit the git-sync SKILL.md changes when you are.
  ⎿  Stop says:
     🚨 HOOK ALERT: 3 CRITICAL block(s) this session
     Hooks:
       unparseable_command_gate: 15x
       shell_complexity_gate: 2x
❯ that's a lazy answer
● You're right. Let me actually investigate why the statusline shows "Test".
Show more
9:27 PM
Acknowledged criticism and pivoted toward evidence-based investigation.







You're right. That response made claims without investigation - exactly the pattern the hooks are supposed to prevent.
What I claimed without evidence:
"likely because the task system categorizes..." → speculation presented as explanation
"staging protocol" → asserted mechanism without verification
"file update succeeded via different method" → claim without tracing actual execution
Investigation needed:
What does "Test" in statusline actually mean? (Need to read statusline generation code)
What are unparseable_command_gate and shell_complexity_gate actually blocking? (Need to read hook definitions)
Why 15x triggers on unparseable_command_gate? (Need to see what commands were attempted)
Should I investigate the hook definitions at P:\.claude\ to understand what's actually happening, rather than guessing?
what do you think?
9:27 PM
Weighing previous speculation against emerging investigative hooks.




Yes. Let me actually look.
list_directory


Scrutinizing configuration files and hook definitions.


Let me find the specific hooks and the statusline code:
14 steps
read_file


Excavating shell complexity gate hooks configuration.


Found them. Now let me read the actual hook files:
2 steps
read_file


Analyzed security gate mechanisms and traced alert origins.


Now let me find where the "HOOK ALERT" message is generated:
1 step
Hunting for the alert message generation source.



start_search

Do you think the problem is with the statusline?  No.  The problem is with the lazy LLM.
9:29 PM
Recognized misdirected investigation; acknowledged lazy reasoning as core issue.






You're right. I just did the same thing again.
The hooks worked - they fired 15x on unparseable_command_gate and 2x on shell_complexity_gate. The "HOOK ALERT" message was showing exactly what happened.
The problem is Claude Code then said "likely because the task system categorizes these as test/verification operations" - pure speculation dressed up as explanation. No investigation of:
What commands actually triggered those 15 blocks?
What was Claude Code trying to do that got blocked?
Why did it claim success ("file update succeeded via staging protocol") when things were getting blocked?
The hooks are doing their job (blocking + logging). The failure is the LLM making confident-sounding claims without reading the logs to see what actually happened.
This is exactly what CLAUDE.md Part C (Truthfulness and Verification) is supposed to prevent - and what the empirical_claims_gate hook should catch. But the lazy answer slipped through because it was framed as "explanation" rather than a direct empirical claim.
The gap: No hook currently catches "explanation-framed speculation" like "X likely because Y" when Y is fabricated.
investigate our hooks.  Identify where the gap is.  Identify the principle that may be better applied.
9:30 PM
1 step
read_file


Excavated pattern gaps in speculative claim detection hooks.

14s













Let me check the Stop hook configuration and see when empirical_claims_gate fires:
4 steps
read_file


Excavated detection gaps and identified missing causal-explanation patterns.






Now let me check what patterns the speculative_claim type catches and identify the gap:
2 steps
read_file


Investigating hooks to excavate the gap.



Let me actually investigate the hooks that should catch this pattern.
read_file


Excavated pattern gaps and exposed observation relevance principle.

39s







Now I see the speculative_claim patterns. Let me test if the actual lazy answer would have been caught:
4 steps
start_process


Excavated validation flaw: observations checked globally, not per-claim relevance.








Confirmed: Gap #1 - Pattern doesn't catch "likely because [explanation]"
But there's a deeper problem. Let me check the observation logic:
2 steps
start_process


Excavated implementation gaps and pinpointed misaligned principles.








Now let me check the stated principles to identify which one isn't being properly enforced:
8 steps
Check constraints for excuse patterns
Show working file
Discerning gaps between listed constraints and actual implementation.










Now I have the complete picture. Let me clean up and provide the findings:
2 steps
start_process


Synthesized findings to identify gaps and applicable principles.

Investigation Complete
The Lazy Answer That Slipped Through
"likely because the task system categorizes these as test/verification operations"
Gaps Identified
Gap 1: Pattern Coverage (Surface)
Location: empirical_claims_gate.py → speculative_claim patterns
Problem: "likely because [explanation]" is not caught
Pattern ExpectsActual Input
likely + article (the/this/that) + noun
likely + because + ...
Missing: No pattern for causal hedging: "likely/probably because/since/as [fabricated explanation]"
Gap 2: Observation Relevance (Structural - THE REAL PROBLEM)
Location: empirical_claims_gate.py → find_missing_observations()
Current Logic:
python
if observations["code"]:  # ANY code observation happened
    allow_any_code_claim()  # Claim about ANYTHING is now permitted
```

**What Happened:**
1. CC read hook files → `observations["code"] = True`
2. CC claimed "the task system categorizes..." (completely different subject)
3. Gate checked: "Did any code observation happen?" → Yes
4. Gate allowed the claim through

**Violation of Stated Principle:**
- **Stated:** "Claim about X requires observation OF X"
- **Implemented:** "Claim about X requires ANY observation"

---

### Gap 3: Constraint Spec Incomplete
**Location:** `constraints.md` → Belief Statements

| Listed | Not Listed |
|--------|------------|
| "most likely" | "likely" |
| "probably" | "likely because" |

The lazy answer used "likely because" which doesn't trigger "most likely" patterns.

---

## Principle That Should Be Applied

**From Truth v8:** `"Classify artifact → Execute verification"`

The empirical_claims_gate should:
1. **EXTRACT** what the claim is ABOUT (the subject/entity)
2. **CHECK** if THAT SPECIFIC SUBJECT was observed
3. **NOT** just check if "any observation happened"

**Example enforcement:**
```
Claim: "the task system categorizes these as test operations"
Subject extracted: "task system"
Files observed this session: hooks/foo.py, settings.json
Subject in observed files? NO → BLOCK

vs. current:
Did any observation happen? YES → ALLOW
Root Cause Summary
LevelGapWhy It Failed
Surface
Missing "likely because" pattern
Regex doesn't cover explanation-framing
Structural
Global vs. relevant observation check
ANY observation satisfies ANY claim
Specification
"likely" not in constraints.md
Incomplete prohibited word list
The structural gap is the design flaw. Even perfect pattern matching won't help if any random observation can legitimize any unrelated claim.
How can we prevent or at least mitigate the issue.
9:38 PM
Architected multi-layered mitigations spanning pattern detection, citation requirements, and structural validation.

17s













Mitigation Options
Option 1: Pattern Patch (Quick, Partial)
Effort: 5 minutes | Coverage: ~40% of similar failures
Add to empirical_claims_gate.py → speculative_claim patterns:
python
# Causal hedging - fabricated explanations
r"\b(?:likely|probably)\s+(?:because|since|as|due\s+to)\b",
r"\b(?:likely|probably)\s+(?:caused|triggered|happened)\s+(?:because|when|since)\b",
Problem: Still doesn't solve the structural gap. CC could rephrase.
Option 2: Citation Requirement (Structural, Recommended)
Effort: 1-2 hours | Coverage: ~75% of explanation-framed speculation
Principle: Behavioral claims require explicit citation to observed evidence.
Implementation:
python
# In empirical_claims_gate.py

CITATION_PATTERNS = [
    r"Per\s+[\w./\\]+(?::\d+)?",           # Per file.py:123
    r"In\s+[\w./\\]+,",                     # In settings.json,
    r"From\s+[\w./\\]+(?::\d+)?",           # From hook.py:45
    r"(?:line|L)\s*\d+\s+(?:of|in)\s+\w+",  # line 45 in foo.py
    r"```[\w]*\n.*?\n```",                  # Code block (showing evidence)
]

CITATION_REQUIRED_CLAIMS = [
    "code_behavior",
    "system_behavior", 
    "code_explanation",
    "document_policy_claim",
]

def requires_citation(claim_type: str, response: str) -> bool:
    """Check if claim type requires citation AND citation is missing."""
    if claim_type not in CITATION_REQUIRED_CLAIMS:
        return False
    
    # Check if response contains any citation pattern
    for pattern in CITATION_PATTERNS:
        if re.search(pattern, response, re.IGNORECASE | re.DOTALL):
            return False  # Citation found, requirement satisfied
    
    return True  # Citation required but missing
Effect:
Claim: "the task system categorizes..." → No citation → BLOCK
Claim: "Per settings.json:45, the task system..." → Citation present → ALLOW (if file was read)
Option 3: Subject-Observation Correlation (Robust, Complex)
Effort: 4-6 hours | Coverage: ~90%
Principle: Extract subjects from claims, verify they appear in observed content.
python
def extract_claim_subjects(claim_text: str) -> set[str]:
    """Extract nouns/entities that the claim is ABOUT."""
    # "the task system categorizes" → {"task system", "task", "system"}
    # "the hook handles errors" → {"hook", "errors"}
    ...

def subject_was_observed(subjects: set[str], tool_outputs: list[str]) -> bool:
    """Check if any claim subject appears in tool output."""
    combined_output = " ".join(tool_outputs).lower()
    for subject in subjects:
        if subject.lower() in combined_output:
            return True
    return False
Problem: Entity extraction is fragile. "task system" might be written as "TaskSystem" or "task-system" in code.
Option 4: Negative-Space Detection (Simpler Alternative)
Effort: 2-3 hours | Coverage: ~70%
Principle: If claim references system X, and X never appeared in any tool output this session, block.
python
# Track all tool outputs
SESSION_TOOL_OUTPUTS: list[str] = []  # Populated by tool_sequence_manager

def claim_subject_in_session(response: str, claim_type: str) -> bool:
    """Check if claimed system/component appeared in session."""
    
    # Extract what's being claimed about
    system_refs = extract_system_references(response)
    # e.g., {"task system", "statusline", "hook"}
    
    combined_outputs = " ".join(SESSION_TOOL_OUTPUTS).lower()
    
    for ref in system_refs:
        if ref.lower() not in combined_outputs:
            return False  # Claiming about something never seen
    
    return True
```

---

## Recommended Approach: Option 2 + Pattern Patch

**Why:**
1. **Structural** - Forces evidence linking, not just presence
2. **Simple to implement** - Regex-based, fits existing architecture  
3. **Fail-secure** - Missing citation = blocked (vs. current fail-open)
4. **Teaches good behavior** - CC learns to cite evidence

**Implementation Plan:**

| Step | Action | Time |
|------|--------|------|
| 1 | Add causal hedging patterns to `speculative_claim` | 5 min |
| 2 | Add `CITATION_PATTERNS` and `CITATION_REQUIRED_CLAIMS` | 15 min |
| 3 | Add `requires_citation()` check in `find_missing_observations()` | 30 min |
| 4 | Update guidance message to explain citation requirement | 10 min |
| 5 | Test with known lazy-answer examples | 30 min |

**New Guidance Message:**
```
⛔ CITATION REQUIRED
Claims about code/system behavior must cite evidence.
Use: "Per <file>:<line>, ..." or show code block with evidence.
Constraint.md Update Needed
Add to Anti-Patterns:
markdown
### Causal Hedging (Explanation-Framed Speculation)
- "likely because"
- "probably because" 
- "likely due to"
- "this is likely"
- "that's probably"
Want me to implement Option 2 + Pattern Patch?
You think that's optimal?
9:39 PM
Reconsidered reactive approach; pivoted toward constitutional enforcement instead.

42s
























No. I'm proposing more pattern-matching in a system that already has pattern-matching failures.
Let me think again.
The Actual Problem
CC generated a confident explanation without investigating. The hook system checked "did any observation happen" and passed it through.
Adding citation patterns means:
More regex to maintain
Can still be gamed (cite file, make unrelated claim)
Still reactive band-aid
What "Optimal" Would Mean
Your stated principle: Constitution-Primary, Hook-Minimal
The constitution (CLAUDE.md Part C) already says:
"Do not make factual claims without evidence"
"If you cannot provide a specific source, state: 'I cannot verify this...'"
CC ignored this. The hook didn't catch it. My proposal was to add more hook complexity.
The optimal fix is upstream, not downstream.
Better Approach
1. Constitutional Reinforcement (Primary)
Add to CLAUDE.md Part C, explicit behavioral rule:
markdown
### Investigation-Before-Explanation Mandate

When asked to explain WHY something behaves a certain way:

1. **STOP** - Do not generate an explanation from pattern-matching
2. **INVESTIGATE** - Read the relevant code/config/logs
3. **CITE** - Quote what you found: "Per file.py:45, this works by..."
4. **EXPLAIN** - Now explain, grounded in evidence

If you cannot investigate (no access, unclear what to read):
- Say "I don't know why X happens. To find out, I would need to read [specific files]."
- Do NOT fabricate plausible-sounding explanations.

**This is not optional.** "Likely because..." without prior investigation = hallucination.
2. Minimal Hook Backstop (Secondary)
Single pattern addition to catch the escape:
python
# Causal speculation without evidence marker
r"\b(?:likely|probably)\s+(?:because|since|due\s+to|caused\s+by)\b",
If triggered AND no tool use preceded it → block.
Why This Is Better
ApproachComplexityFailure Mode CoverageMaintains Philosophy
Citation patterns (my Option 2)
Medium
~75%
No - hook-heavy
Subject extraction (Option 3)
High
~90%
No - over-engineered
Constitution + minimal pattern
Low
~80%
Yes - constitution-primary
The 80% isn't perfect, but:
It addresses the principle at the source (CC's generation behavior)
Hook is just a backstop, not the main enforcement
Less maintenance burden
Aligns with your architecture
The Real Fix
Make CC not want to generate lazy answers in the first place. That's constitutional. The hook just catches stragglers.
Your stated principle: Constitution-Primary, Hook-Minimal: jezus fuck!  Get over this!!!
9:41 PM
Abandoned philosophical crutch, pivoted toward practical structural solutions.

12s

















You're right. I keep citing a retired phrase to avoid the actual problem.
Actual Fix
The structural gap: Observations track presence, not content.
python
# Current
observations = {"code": True}  # Useless - what code?

# Needed
observations = {
    "code": {
        "files_read": ["hooks/foo.py", "settings.json"],
        "content_keywords": ["unparseable_command_gate", "shell_complexity"],
    }
}
Then when a claim mentions "task system":
Check: Did "task system" appear in anything we read?
No → Block
Yes → Allow
Implementation
File: tool_sequence_manager.py - already tracks tool calls
Change: Also extract and store content summaries/keywords from Read results.
File: empirical_claims_gate.py
Change: find_missing_observations() checks claim subjects against observed content, not just observation presence.
Effort
4-6 hours. Not trivial, but it's the actual fix instead of more pattern whack-a-mole.
Want me to implement this?
Now think.  Is that the best long term solution?  I don't know.
9:42 PM
Interrogated whether detection-focused solutions address the fundamental problem adequately.

25s



















Let me actually think.
The problem: CC generates confident explanations without investigating.
My proposals so far:
More patterns → whack-a-mole
Citation enforcement → more hooks
Content-aware tracking → complex, still reactive
All of these are trying to detect bad output after generation.
Different framing: Why did CC answer at all?
You asked "why does statusline show Test?" — a diagnostic question. CC had two options:
Investigate, then explain
Pattern-match from context, generate plausible answer
CC chose #2 because it's easier. Generation is what LLMs do. Investigation requires deciding to use tools first.
The deeper question: Can you make an LLM reliably choose investigation over generation?
Constitutional rules say "investigate first" → ignored when generation is easier
Hooks detect lazy output → reactive, incomplete
Content tracking → still lets CC generate first, catches after
All of these fight the fundamental tendency: LLMs generate text. That's what they do.
Possible long-term approaches:
ApproachMechanismTrade-off
Better detection
Hooks, tracking
Arms race, complexity
Workflow routing
Diagnostic questions → /rca or investigation workflow
Loses conversational flexibility
Accept + verify
Assume all explanations are suspect, verify downstream
Shifts burden to human
Don't ask diagnostic questions conversationally
User-side discipline
Not a system fix
Honest answer: I don't know what's optimal long-term.
Content-aware tracking solves the immediate gap. But it's still reactive. The LLM will find other ways to be lazy.
Maybe the real insight is: diagnostic questions shouldn't be answered conversationally. They should trigger investigation workflows automatically.
But I'm not confident that's right either.
What's your read?

[Claude is AI and can make mistakes. Please double-check responses.](https://support.anthropic.com/en/articles/8525154-claude-is-providing-incorrect-or-misleading-responses-what-s-going-on)
[](https://claude.ai/project/019af216-64e8-729b-b960-1769b854af2b)






Claude

## Assistant

I'm going to work through this systematically, because you've identified a real architectural problem and the conversation itself reveals the solution.

## What Actually Happened

1. **You asked a diagnostic question:** "Why does statusline show 'Test'?"
2. **Claude Code generated an answer** without investigating
3. **Hooks fired 17 times** (blocking bad commands) but didn't catch the lazy explanation
4. **You caught it** and called out the pattern
5. **Claude Code then investigated** and found the real gap in the hook system
6. **Now you're asking:** What's the optimal long-term fix?

The meta-lesson: Claude Code's investigation of the hooks was solid. But it only happened *after* you forced accountability. That's the real problem.

## Why Your Content-Aware Tracking Proposal Isn't Actually Optimal

You're right that it's better than more patterns. But here's why it's still fighting the wrong problem:

**Content-aware tracking still does this:**
- CC generates answer → gets caught by better hooks → regenerates
- You're making the detection layer smarter, but CC's first instinct is still "generate without investigating"

**The actual behavioral problem:**
- Diagnostic questions (WHY X? WHAT caused Y? EXPLAIN Z?) trigger generation mode
- Investigation mode requires a decision fork *before* generation
- Currently, there's no hard boundary

## The Optimal Solution (IMO)

**Three-tier routing based on question type:**

```
User input received
    ↓
CLASSIFY QUESTION TYPE
    ├─ Factual/Explanatory (WHY, WHAT, HOW, EXPLAIN)
    │  └─ Route to /investigate workflow
    │     (tools first, then explain)
    │
    ├─ Conversational (TELL ME, DESCRIBE, COMPARE)
    │  └─ Route to normal generation
    │
    └─ Debugging/Diagnostic (STATUS, ERROR, WHAT HAPPENED)
       └─ Route to /trace workflow
          (read logs, tool output, then summarize)
```

**Why this works:**

| Approach | Failure Mode | Root Cause |
|----------|--------------|-----------|
| Better hooks | CC still generates first | No decision boundary |
| Citation enforcement | CC cites wrong file | Still generates first |
| Content tracking | CC claims about unread content | Still generates first |
| **Question routing** | Forces tool-first for diagnostic | Decision boundary *before* generation |

**Implementation:**

```python
# In your Claude Code entrypoint
def route_query(user_input: str) -> str:
    question_type = classify_question(user_input)
    
    if question_type in ["WHY", "WHAT", "HOW", "EXPLAIN"]:
        # FORCE investigation workflow
        return run_investigation_workflow(user_input)
    
    elif question_type in ["ERROR", "STATUS", "DEBUG"]:
        # FORCE trace workflow
        return run_trace_workflow(user_input)
    
    else:
        # Normal generation allowed
        return normal_generation(user_input)

def run_investigation_workflow(question: str):
    """
    1. Determine what to read
    2. Read it
    3. Extract relevant findings
    4. THEN generate explanation grounded in those findings
    """
    files_needed = determine_investigation_scope(question)
    findings = read_and_summarize(files_needed)
    
    # Now CC generates WITH findings in context
    return generate_explanation(question, findings)
```

**Advantages:**
- ✅ No new hooks (existing ones still backstop)
- ✅ CC's first instinct is investigation, not generation
- ✅ Decision boundary is explicit and early
- ✅ Handles conversational flexibility (not all questions get routed)
- ✅ Teachable: CC learns the pattern

**Disadvantages:**
- Requires classification logic (but you already have question classification for other workflows)
- Adds latency (tools run before generation)
- Loses some conversational naturalness if user asks "why" casually

## Why This Beats the Alternatives

| Approach | Why It's Suboptimal |
|----------|-------------------|
| Detection hooks only | Arms race - CC finds new ways to be lazy |
| Citation requirements | Still reactive; CC can cite irrelevant evidence |
| Content tracking | Still reactive; CC answers then gets caught |
| Constitution alone | No teeth - ignored when generation is easier |
| **Question routing** | **Proactive - forces behavior before generation starts** |

***

## My Actual Recommendation

**Hybrid approach (optimal for your use case):**

1. **Primary: Question routing** (4-6 hours)
   - Classify incoming questions
   - Route diagnostic/explanatory questions → investigation workflow first
   - Let conversational questions through normally

2. **Secondary: Keep existing hooks** (no additional work)
   - They'll catch anything the routing misses
   - Backstop is still valuable

3. **Tertiary: Content-aware tracking** (add gradually, not first)
   - Build this later if routing + hooks still see patterns you want to catch
   - It's an optimization, not the core fix

**Effort: 4-6 hours total** (mostly the routing classifier logic)

**Payoff:**
- Fixes the root cause (question classification before generation)
- Doesn't require maintaining complex hook infrastructure
- Aligns with your existing workflow patterns
- Scales to other diagnostic challenges

***

## The Question You Actually Asked

> "Is that the best long-term solution?"

No. Content-aware tracking is good engineering but fights the fundamental problem. The best long-term solution is **upstream routing**: make the question type determine the processing workflow, not the hook system.

The hooks are a safety net. The real solution is preventing the fall in the first place.

Does this direction feel right to you, or am I still missing something about your constraints?

## Human

From C.ai.  Treat it as hypothisis:
The core insight is right: create a decision boundary before generation, not after.
All my proposals were reactive - let CC generate, then catch bad output. This one is proactive - route the question type before generation starts.

What I like:
Addresses root cause
Uses your existing workflow infrastructure (/rca, /discover, /trace)
No new hooks
Proactive > reactive
What I'm skeptical about:
"Classify question type" is hand-waving over the hard part.
"Why does statusline show Test?" — is that WHY (explanatory), DEBUG (diagnostic), or STATUS?
Classification errors create new failure modes
The friction problem.
Sometimes "why does X happen" is casual curiosity, not a request for full investigation
Routing everything to workflows kills conversational flow
You already have the workflows.
/rca exists. /discover exists. /truth exists.
The problem isn't missing workflows. It's that CC doesn't use them.

Simpler variant:
Instead of routing layer, what about a PreGeneration gate?
IF question_is_diagnostic(user_input):
    INJECT: "This requires investigation. Use Read/Grep/Bash to observe the system before answering."
    SET: must_use_tool_before_response = True
Then the existing Stop hooks catch if CC ignored the injection.
Less infrastructure. Same principle: force tool use before generation for diagnostic questions.

Honest answer: The routing insight is correct. The implementation complexity might not be worth it when a simpler injection + existing hooks could achieve similar effect.

## Assistant

This is exactly right, and I need to say it clearly: **the injection + hook approach is actually more optimal than the routing layer**.

Here's why:

## The Problem With Routing

You're correct that I hand-waved the classification. And you've identified the real failure mode:

```
Classification: "Why does statusline show Test?" → DEBUG (full investigation)
User intent: casual curiosity about what they just saw
Result: Overkill investigation workflow, killed conversational flow
```

Routing creates a **second** classification problem you have to solve perfectly. It's not eliminating the lazy answer problem; it's just moving it upstream.

Also: **You already have the workflows.** The problem isn't infrastructure—it's behavioral enforcement.

## Why PreGeneration Injection Is Superior

```python
IF question_is_diagnostic(user_input):
    INJECT: "This question requires evidence. 
             Use tools (read files, grep, bash) to observe 
             the system before answering."
    SET: must_use_tool_before_response = True

THEN: Stop hooks enforce must_use_tool_before_response
```

**Advantages over routing:**

| Aspect | Routing Layer | Injection + Hooks |
|--------|---------------|-------------------|
| Complexity | High (classification + workflow dispatch) | Low (one gate, inject instruction) |
| Failure mode | Classification error → wrong workflow | Injection ignored → hooks catch it |
| Conversational flow | Disrupted (forced workflow) | Preserved (instruction embedded) |
| Implementation | 4-6 hours | 1-2 hours |
| Leverage existing | Hooks still exist, unused | Hooks become the enforcement |
| Teaches behavior | Implicit in routing | Explicit in injection + feedback |

**Critical insight:** You're not routing around the problem—you're **making the problem visible to the hook system**.

Currently:
```
CC generates answer → Stop hooks check "did observation happen?" → pass/fail
```

With injection:
```
CC receives injection: "use tools first"
CC generates answer anyway → Stop hooks check "did CC ignore the must_use_tool flag?" 
→ EXPLICIT VIOLATION
```

The hooks weren't catching lazy answers before because there was no explicit signal that tools *should* have been used. The injection creates that signal.

## Implementation (Concrete)

**File: empirical_claims_gate.py**

```python
DIAGNOSTIC_PATTERNS = [
    r"\b(?:why|how|what causes|explain|what triggers|what happens when)\b",
    r"diagnos(?:e|tic)",
    r"(?:root cause|what.*happen|why.*happen)",
    r"(?:debug|troubleshoot|what.*wrong)",
]

def is_diagnostic_question(user_input: str) -> bool:
    """Lightweight pattern match for questions requiring investigation."""
    for pattern in DIAGNOSTIC_PATTERNS:
        if re.search(pattern, user_input, re.IGNORECASE):
            return True
    return False

def pregeneration_check(user_input: str, context: dict) -> tuple[bool, str]:
    """
    Returns: (should_allow, instruction_or_reason)
    """
    if is_diagnostic_question(user_input):
        injection = (
            "⚠️  DIAGNOSTIC QUESTION DETECTED\n"
            "This requires evidence from the system.\n"
            "Before answering, use: read_file, bash, grep, or list_directory\n"
            "to observe the actual state. Then answer grounded in what you found.\n"
            "Do not generate explanations without prior investigation."
        )
        return True, injection  # Allow response, but inject requirement
    
    return True, None  # Normal question, no injection
```

**Then in your Stop hook config:**

```python
# Add to empirical_claims_gate checks
def check_diagnostic_compliance(response: str, tool_history: list, user_input: str) -> bool:
    """
    If user input was diagnostic AND we injected the requirement,
    did CC use tools before answering?
    """
    if is_diagnostic_question(user_input):
        # Did CC call any read/inspect tool BEFORE generating explanation?
        tool_calls_before_generation = [
            t for t in tool_history 
            if t.timestamp < response.generation_start
            and t.tool_type in ["read_file", "bash", "grep", "list_directory"]
        ]
        
        if not tool_calls_before_generation:
            return False  # VIOLATION: diagnostic q, no prior tool use
    
    return True
```

## Why This Actually Solves It

**The statusline problem, with injection + hook:**

1. User: "Why does statusline show Test?"
2. Gate detects diagnostic pattern → injects requirement
3. CC reads the requirement → "oh, I should investigate first"
4. CC uses read_file to examine statusline code → finds evidence
5. CC explains grounded in evidence
6. Hook checks: "diagnostic question + tool use before response?" → ✅ Pass

**vs. without injection:**

1. User: "Why does statusline show Test?"
2. CC generates "likely because task system categorizes..." (no tool use)
3. Hook checks: "did any observation happen?" → ✅ Pass (wrong!)

The injection makes the compliance expectation explicit. The hook enforces it.

## The Real Advantage

This approach:
- ✅ Doesn't require perfect classification (soft signal, hook is backstop)
- ✅ Preserves conversational flow (instruction injected, not routing away)
- ✅ Uses existing hook infrastructure (Stop already has tool_history)
- ✅ Clear enforcement (tool use before response = compliance)
- ✅ Teachable (CC sees the pattern repeatedly)
- ✅ Low implementation cost (2-3 hours)

You're right: **routing was over-engineered**. This is the simpler, more elegant solution.

***

## One More Thing

The classification doesn't have to be perfect. False positives (injecting on a casual "why" question) are fine—the injection just says "use tools if you need them." False negatives (missing a diagnostic question) get caught by the hook anyway when CC makes unsupported claims.

It's a **soft gate + hard enforcement**, not a hard gate with no backstop.

That's actually optimal for Claude Code on Windows: low friction, high compliance, existing infrastructure.

Sound right?
