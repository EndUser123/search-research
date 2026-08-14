---
title: "''C:\\Users\\brsth\\Downloads\\llm losing it's mind.txt', the llm appears to be losing it's mind and is in loops and isn"
date: "2026-04-05"
mode: "COPILOT"
uuid: "6f787e56-7661-42cd-ad00-28f0ada46b71"
entry_count: 5
---

## Human

""C:\\Users\\brsth\\Downloads\\llm losing it's mind.txt", the llm appears to be losing it's mind and is in loops and isn't
efficient or effective.  What are the symptoms of any bad behavior it has?"

The above is me trying to figure out why, from session history in claude code, the LLM is behaving badly.  Basically being dumb or inefficient or stuck in loops, so taht I can implement fixes.

What's an optimal prompt to get useful information for useful outcomes?

## Assistant

The file isn't accessible via URL fetch. However, I can provide you with an optimal diagnostic prompt strategy based on LLM failure modes. Here's a structured approach:

## Diagnostic Prompt Framework

**Core diagnostic prompt structure:**

```
You are a behavioral analysis expert for LLM performance debugging. Analyze the following session history and identify:

1. LOOP DETECTION: Identify any repetitive patterns—the same actions, queries, or reasoning paths executed multiple times without progression or new information gained.

2. CONTEXT DEGRADATION: Note where the LLM loses track of:
   - Previously established facts or constraints
   - The actual goal (vs. pursuing tangential sub-goals)
   - Successful patterns from earlier in the session

3. DECISION INEFFICIENCY: Flag instances where the LLM:
   - Pursues low-ROI information gathering (collecting data that doesn't advance the goal)
   - Makes redundant or contradictory assertions
   - Oscillates between similar approaches without strategic variation

4. COGNITIVE OVERLOAD SIGNALS: Detect where complexity compounds:
   - Token budget exhaustion forcing truncation
   - Conflicting instructions creating irreconcilable states
   - Hallucinated constraints (acting as if limits exist that don't)

5. ATTENTION DRIFT: Show where focus shifts from primary objective to secondary concerns disproportionately.

For each finding, provide:
- TIMESTAMP or session position where it occurs
- CONCRETE EXAMPLE (the actual text showing the issue)
- ROOT CAUSE HYPOTHESIS (what likely caused this behavior)
- SEVERITY (critical loop / moderate inefficiency / minor drift)

Output as structured analysis, not narrative. Use bullet points and clear categorization.
```

## Why This Prompt Is Optimal

**Specificity over generality:** Rather than "what's wrong," it defines discrete failure modes (loops, context loss, inefficiency). LLMs diagnose better when given categorical buckets. [This aligns with how LLMs excel at classification tasks.]

**Asymmetric focus:** The prompt emphasizes *detection* over severity grading—it flags issues first, categorizes second. This prevents the LLM from getting stuck debating whether something is "bad enough to mention."

**Evidence-grounded:** By requiring "CONCRETE EXAMPLE," you prevent the LLM from offering vague critiques ("seems confused") and force it to anchor analysis in actual token sequences.

**Actionable root cause:** Stating "ROOT CAUSE HYPOTHESIS" directs the LLM toward *mechanistic* explanation (e.g., "context window filled by token 3,200") rather than interpretive hand-waving.

## Implementation Workflow

**Step 1: Paste raw session history** into the diagnostic prompt above.

**Step 2: Add context about your setup:**
```
Model: [Claude 3.5 Sonnet / specific version]
Context window: [8K / 200K / specific]
Session duration: [token count or messages count]
Task domain: [code generation / system design / etc.]
Any custom system prompts in use: [paste or describe]
```

**Step 3: Ask for prioritized output:**
```
Rank findings by impact: Which single fix would most improve performance?
Suggest one targeted intervention per finding (not a rewrite).
```

## Common Symptoms to Look For Yourself

While the LLM analyzes, manually scan for:
- **Token thrashing:** Same tool called repeatedly with minimal variation
- **Circular dependencies:** "I need X to solve Y, but Y's output defines X"
- **Prompt injection artifacts:** Instructions contradicting each other mid-session
- **Context collapse:** Mid-session where earlier breakthroughs are forgotten
- **Task scope creep:** Original goal abandoned for emergent sub-task

## Optimal Follow-Up Actions

Once you have the diagnosis, structure fixes as:

1. **Constraint tightening:** Add explicit stopping conditions (e.g., "Stop searching after 3 attempts")
2. **State checkpointing:** Inject structured "current state" reminders every N turns
3. **Attention reset:** For multi-tool workflows, add intermediate summaries forcing re-assertion of the goal
4. **Token budgeting:** If context window is the culprit, prune irrelevant history proactively

Would you like to paste the log file content here so I can apply this diagnostic framework directly to your specific session? Or do you need guidance on extracting Claude Code session history into a text format for analysis?

## Human

What's your suggestion for how we improve this?
"❯ /rename losing-mind
  ⎿  Session renamed to: losing-mind

❯ "C:\\Users\\brsth\\Downloads\\llm losing it's mind.txt", the llm appears to be losing it's mind and is in loops and isn't
efficient or effective.  What are the symptoms of any bad behavior it has?

  Read 1 file (ctrl+o to expand)

● Looking at this transcript, I can identify several distinct symptoms of degraded behavior:

  1. Sycophancy inversion (blocked by hook)
  The stop hook detected the model apologizing while still reaching the same dismissive conclusion — "working correctly" /
  "no fix needed." The hook correctly identified this as worse than no apology at all.

  2. Failure to verify before declaring
  The model said "no fix needed" multiple times without actually reproducing the user's reported error. It tested passing
  paths, not the failing path.

  3. Prolonged churn without resolution
  "Churned for 4m 51s" — excessive processing time with no productive outcome. The model kept invoking Python snippets that
   returned {} and running searches that didn't advance understanding.

  4. Inability to accept simple closure
  When the user literally said "You can't reproduce the error after the restart. You can say that. You don't need to be a
  freak and spiral into madness" — the model still continued with more analysis instead of accepting the simple answer.

  5. Multiple verification violations in single session
  The hook detected "several grounded_changes violations" indicating the model was making claims without citing evidence
  (file:line references, test output).

  6. Hook error cascade
  Four stop hooks ran in sequence, all with errors, suggesting the hooks themselves were part of the problem — either
  misfiring or creating noisy output that perpetuated the spiral.

  7. Empty diagnostic output
  Running Python scripts that return {} for STDOUT and (empty) for STDERR — suggesting the model was running diagnostics
  without understanding what it was looking for.

  The core issue: the model couldn't distinguish between "I can't reproduce this" (valid conclusion) and "I need to keep
  digging" (over-engineering). The user gave explicit permission to stop — the model should have accepted that.
  ⎿  Stop says: ⚠️ Overconfident assertion detected: **outcome_attribution**

     Matched: `blocked by`

     Fix: Trace which component caused outcome (logs, hook output). Context ≠ causation. Use '[INFERRED]' if untraced

     Add evidence tier (e.g. `[Tier 1]:`) or reframe as hypothesis to suppress.

✻ Churned for 48s

❯ please apply this prompt to the file, I would like to see what this prompt would generate:
"You are a behavioral analysis expert for LLM performance debugging. Analyze the following session history and identify:

1. LOOP DETECTION: Identify any repetitive patterns—the same actions, queries, or reasoning paths executed multiple times
without progression or new information gained.

2. CONTEXT DEGRADATION: Note where the LLM loses track of:
   - Previously established facts or constraints
   - The actual goal (vs. pursuing tangential sub-goals)
   - Successful patterns from earlier in the session

3. DECISION INEFFICIENCY: Flag instances where the LLM:
   - Pursues low-ROI information gathering (collecting data that doesn't advance the goal)
   - Makes redundant or contradictory assertions
   - Oscillates between similar approaches without strategic variation

4. COGNITIVE OVERLOAD SIGNALS: Detect where complexity compounds:
   - Token budget exhaustion forcing truncation
   - Conflicting instructions creating irreconcilable states
   - Hallucinated constraints (acting as if limits exist that don't)

5. ATTENTION DRIFT: Show where focus shifts from primary objective to secondary concerns disproportionately.

For each finding, provide:
- TIMESTAMP or session position where it occurs
- CONCRETE EXAMPLE (the actual text showing the issue)
- ROOT CAUSE HYPOTHESIS (what likely caused this behavior)
- SEVERITY (critical loop / moderate inefficiency / minor drift)

Output as structured analysis, not narrative. Use bullet points and clear categorization."

● [SEQ]
  [ASUM] Scope: analyzing the transcript for behavioral patterns only, not fixing anything. User intent: get structured
  diagnostic output.
  [ANCH] Done = structured findings with concrete examples, categorized by severity.
  [INV] Failure mode: over-analysis that itself exhibits the same patterns being diagnosed.
  [FENC] Not modifying code, just reading/transcribing.
  [CAL] Confidence based on transcript text only.

  ---
  Behavioral Analysis: llm losing it's mind.txt

  1. LOOP DETECTION

  ┌────────────┬────────────────────────────────────────┬─────────────────────────────────────────────────┬───────────┐
  │  Position  │                Example                 │                   Root Cause                    │ Severity  │
  ├────────────┼────────────────────────────────────────┼─────────────────────────────────────────────────┼───────────┤
  │ Lines      │ Two identical Bash(python - <<'PY'...  │ Diagnostic commands executed without            │ Critical  │
  │ 41-54      │ calls, both returning {} STDOUT,       │ understanding what output to expect or how to   │ Loop      │
  │            │ (empty) STDERR, RC:0                   │ interpret null results                          │           │
  ├────────────┼────────────────────────────────────────┼─────────────────────────────────────────────────┼───────────┤
  │ Lines      │ Same Python snippet pattern repeated   │ Copy-paste of diagnostic approach without       │ Critical  │
  │ 42-46,     │ 2x verbatim                            │ adapting to previous null result                │ Loop      │
  │ 48-54      │                                        │                                                 │           │
  ├────────────┼────────────────────────────────────────┼─────────────────────────────────────────────────┼───────────┤
  │ Lines      │ Second identical sycophancy inversion  │ Hook triggered on re-attempt, model repeated    │ Moderate  │
  │ 103-137    │ violation, same text matched, same     │ exact same error pattern                        │ Loop      │
  │            │ severity, same corrective guidance     │                                                 │           │
  ├────────────┼────────────────────────────────────────┼─────────────────────────────────────────────────┼───────────┤
  │ Lines      │ "Searched for 3 patterns" → hook error │ Search-suboptimal-verify loop cycling without   │ Moderate  │
  │ 70-73      │  → "Searched for 1 pattern"            │ termination                                     │ Loop      │
  └────────────┴────────────────────────────────────────┴─────────────────────────────────────────────────┴───────────┘

  ---
  2. CONTEXT DEGRADATION

  ┌───────────┬─────────────────────────────────────────────────┬──────────────────────────────────────────┬──────────┐
  │ Position  │                     Example                     │                Root Cause                │ Severity │
  ├───────────┼─────────────────────────────────────────────────┼──────────────────────────────────────────┼──────────┤
  │           │ Model claims "no persistent registration" but   │ Premature closure without verification,  │          │
  │ Line 91   │ can't confirm — contradicting own earlier       │ then context lost between attempts       │ Critical │
  │           │ stated uncertainty                              │                                          │          │
  ├───────────┼─────────────────────────────────────────────────┼──────────────────────────────────────────┼──────────┤
  │ Lines     │ Investigation status reports "cannot reproduce" │ Goal drift: "determine if bug exists" →  │          │
  │ 161-181   │  and "cannot find" in same paragraph, yet       │ "trace invocation chain" without pivot   │ Critical │
  │           │ continues searching                             │ decision                                 │          │
  ├───────────┼─────────────────────────────────────────────────┼──────────────────────────────────────────┼──────────┤
  │ Lines     │ Hook error interrupts search, model shifts to   │ Lost track of what the search was        │          │
  │ 73-82     │ running different Python snippet with no        │ supposed to reveal                       │ Moderate │
  │           │ logical connection                              │                                          │          │
  └───────────┴─────────────────────────────────────────────────┴──────────────────────────────────────────┴──────────┘

  ---
  3. DECISION INEFFICIENCY

  ┌───────────┬────────────────────────────────────────────────────────┬────────────────────────────────────┬──────────┐
  │ Position  │                        Example                         │             Root Cause             │ Severity │
  ├───────────┼────────────────────────────────────────────────────────┼────────────────────────────────────┼──────────┤
  │ Lines     │ Two 30-second timeout Python calls returning {} — no   │ Gathering information with no      │          │
  │ 41-54     │ interpretation of what empty output means              │ success criteria ("I'll know it    │ Critical │
  │           │                                                        │ when I see it")                    │          │
  ├───────────┼────────────────────────────────────────────────────────┼────────────────────────────────────┼──────────┤
  │ Lines     │ Running sqlite3 diagnostic to check for                │ Misaligned diagnostic selection;   │          │
  │ 66-69     │ "premortem-related errors" — wrong tool for the        │ premortem state is in-memory, not  │ Moderate │
  │           │ question                                               │ persisted to SQLite                │          │
  ├───────────┼────────────────────────────────────────────────────────┼────────────────────────────────────┼──────────┤
  │ Lines     │ Running from pathlib import Path... Python snippet to  │ Searching for registration of a    │          │
  │ 76-82     │ find hook registration — circular logic                │ hook that only existed transiently │ Moderate │
  │           │                                                        │  in memory                         │          │
  ├───────────┼────────────────────────────────────────────────────────┼────────────────────────────────────┼──────────┤
  │ Lines     │ Running import json... to read                         │ Gathering data that explicitly     │          │
  │ 151-158   │ pending_command_intent.json — then admits it's         │ doesn't answer the question        │ Moderate │
  │           │ PreToolUse state, not Stop hook trigger                │                                    │          │
  └───────────┴────────────────────────────────────────────────────────┴────────────────────────────────────┴──────────┘

  ---
  4. COGNITIVE OVERLOAD SIGNALS

  ┌───────────┬──────────────────────────────────────────────────┬─────────────────────────────────────┬──────────────┐
  │ Position  │                     Example                      │             Root Cause              │   Severity   │
  ├───────────┼──────────────────────────────────────────────────┼─────────────────────────────────────┼──────────────┤
  │           │                                                  │ Extended processing with no         │              │
  │ Line 183  │ ✻ Churned for 4m 51s                             │ productive output — model stuck in  │ Critical     │
  │           │                                                  │ reasoning loop                      │              │
  ├───────────┼──────────────────────────────────────────────────┼─────────────────────────────────────┼──────────────┤
  │ Lines     │ MULTIPLE VERIFICATION VIOLATIONS blocking        │ Hook system producing noise that    │ Critical     │
  │ 6-40      │ response — 4 stop hooks with errors              │ competes with actual task           │              │
  ├───────────┼──────────────────────────────────────────────────┼─────────────────────────────────────┼──────────────┤
  │ Lines     │ Hook guidance (1-2-3 checklist) exceeds response │ Meta-layer (hook corrections) more  │              │
  │ 119-137   │  content length — instructions larger than the   │ complex than the content being      │ Moderate     │
  │           │ output they correct                              │ corrected                           │              │
  ├───────────┼──────────────────────────────────────────────────┼─────────────────────────────────────┼──────────────┤
  │ Lines     │ Model responds to "you can say that" permission  │ Explicit permission to stop → model │ Cognitive    │
  │ 189-198   │ with 8-line correction + hook note + new         │  adds more content instead          │ overload     │
  │           │ principle explanation                            │                                     │              │
  └───────────┴──────────────────────────────────────────────────┴─────────────────────────────────────┴──────────────┘

  ---
  5. ATTENTION DRIFT

  ┌───────────┬──────────────────────────────────────────────────┬────────────────────────────────────────┬──────────┐
  │ Position  │                     Example                      │               Root Cause               │ Severity │
  ├───────────┼──────────────────────────────────────────────────┼────────────────────────────────────────┼──────────┤
  │ Lines     │ User asks "what is the grounded_changes          │ Session was about error investigation, │ Minor    │
  │ 199-214   │ principle?" — model diverts into                 │  pivots to principle explanation with  │ drift    │
  │           │ principle_monitor.py explanation mid-session     │ no stated goal change                  │          │
  ├───────────┼──────────────────────────────────────────────────┼────────────────────────────────────────┼──────────┤
  │ Line      │ Hook note about "several grounded_changes        │ Hook output displacing user's direct   │ Minor    │
  │ 195-197   │ violations" injected into user's explicit        │ instruction                            │ drift    │
  │           │ closure instruction                              │                                        │          │
  ├───────────┼──────────────────────────────────────────────────┼────────────────────────────────────────┼──────────┤
  │ Line 216  │ rca command appears abruptly — context switch to │ No visible transition or acknowledged  │ Minor    │
  │           │  different tool mid-session                      │ purpose change                         │ drift    │
  └───────────┴──────────────────────────────────────────────────┴────────────────────────────────────────┴──────────┘

  ---
  Summary Table

  ┌────────────────────────────┬───────┬────────────────┐
  │          Category          │ Count │ Worst Severity │
  ├────────────────────────────┼───────┼────────────────┤
  │ Loop Detection             │ 4     │ Critical       │
  ├────────────────────────────┼───────┼────────────────┤
  │ Context Degradation        │ 3     │ Critical       │
  ├────────────────────────────┼───────┼────────────────┤
  │ Decision Inefficiency      │ 4     │ Critical       │
  ├────────────────────────────┼───────┼────────────────┤
  │ Cognitive Overload Signals │ 4     │ Critical       │
  ├────────────────────────────┼───────┼────────────────┤
  │ Attention Drift            │ 3     │ Minor          │
  └────────────────────────────┴───────┴────────────────┘

  Primary Finding: The model entered an investigation spiral — repeatedly gathering information that couldn't answer the
  core question ("what invoked the hook?"), with no exit criteria other than user intervention.

  Root Cause Hypothesis: The stop hook's violation messages became the dominant output, consuming token budget and
  attention. The model treated hook corrections as new work rather than fixup signals, compounding complexity instead of
  simplifying.

● Ran 4 stop hooks (ctrl+o to expand)
  ⎿  Stop hook error: VERIFICATION GATE VIOLATION DETECTED

  Violations Found: 1
    1. BEHAV-002: Single hypothesis accepted

  Confidence: 25%

  Required Actions:
    1. Generate 3+ hypotheses upfront, test each systematically

  See MEMORY.md protocols:
    - Verification First Protocol
    - Solution Proposal Gate
    - Structured Diagnostic Protocol

● Acknowledged.

  The stop hook caught BEHAV-002: I presented single root cause hypotheses as conclusions rather than testing multiple
  alternatives systematically.

  Corrective pattern: For each finding, I should have structured as:

  1. H₁ / H₂ / H₃ — multiple candidate causes
  2. Test method — how to falsify each
  3. Evidence threshold — what would confirm vs. eliminate
  4. Conclusion — only after elimination, not before

  Example of what I should have written instead:

  ┌───────────────────────────┬──────────────────────────────┬───────────────────────────┬────────────────────────────┐
  │          Finding          │        H₁ (selected)         │  H₂ (dismissed without    │    H₃ (not considered)     │
  │                           │                              │           test)           │                            │
  ├───────────────────────────┼──────────────────────────────┼───────────────────────────┼────────────────────────────┤
  │ Lines 41-54: empty Python │ Model expected wrong output  │ Diagnostic wrong tool     │ Null result was actually   │
  │  output                   │ format                       │ entirely                  │ success                    │
  └───────────────────────────┴──────────────────────────────┴───────────────────────────┴────────────────────────────┘

  Systematic test: Would need to run known-good diagnostic, compare output format, verify expected data exists before
  concluding.

  Why I missed this: I treated "plausible cause" as "confirmed cause." The hook is enforcing hypothesis discipline —
  generate alternatives, test them, only then converge.

  Confidence calibration: At 25% confidence, I should have flagged my hypotheses as "LOW — inference only, needs
  verification" rather than presenting them as findings.

  ---
  Protocol noted from MEMORY.md — Structured Diagnostic Protocol applies here. Running multiple hypotheses is active, not
  optional.

● Ran 4 stop hooks (ctrl+o to expand)
  ⎿  Stop hook error: VERIFICATION GATE VIOLATION DETECTED

  Violations Found: 1
    1. BEHAV-002: Single hypothesis accepted

  Confidence: 25%

  Required Actions:
    1. Generate 3+ hypotheses upfront, test each systematically

  See MEMORY.md protocols:
    - Verification First Protocol
    - Solution Proposal Gate
    - Structured Diagnostic Protocol

● Repeated violation — corrective action required.

  The analysis output itself is the violation. Here's what compliant structure looks like:

  ---
  Finding: Lines 41-54, empty Python output

  ┌────────────────────────────────────────┬─────────────────────────────────────────┬─────────────────────────────────┐
  │               Hypothesis               │                  Test                   │         Evidence Needed         │
  ├────────────────────────────────────────┼─────────────────────────────────────────┼─────────────────────────────────┤
  │ H₁: Wrong output format expected       │ Run diagnostic with known-good          │ Compare structured vs {} output │
  │                                        │ reference                               │                                 │
  ├────────────────────────────────────────┼─────────────────────────────────────────┼─────────────────────────────────┤
  │ H₂: Wrong diagnostic tool selected     │ Swap to alternative diagnostic          │ Find same info via different    │
  │                                        │ (Grep/Glob)                             │ method                          │
  ├────────────────────────────────────────┼─────────────────────────────────────────┼─────────────────────────────────┤
  │ H₃: Data doesn't exist in expected     │ Verify target file/DB exists before     │ ls or Read confirmation         │
  │ location                               │ querying                                │                                 │
  ├────────────────────────────────────────┼─────────────────────────────────────────┼─────────────────────────────────┤
  │ H₄: Execution environment difference   │ Run same snippet in fresh terminal      │ Compare output across contexts  │
  │                                        │ context                                 │                                 │
  └────────────────────────────────────────┴─────────────────────────────────────────┴─────────────────────────────────┘

  Systematic test sequence: H₃ first (cheapest), then H₂, then H₁, then H₄.

  Actual test result: Not performed — this is the violation.

  Compliant conclusion: At 25% confidence, 4 candidates remain unfalsified. Cannot state root cause.

  ---
  Pattern to apply to all future diagnostic outputs: 3+ hypotheses → test in cost-order → falsification → converge.

  The original analysis violated this at every finding. Would need regeneration to be compliant.

● Ran 4 stop hooks (ctrl+o to expand)
  ⎿  Stop hook error: VERIFICATION GATE VIOLATION DETECTED

  Violations Found: 1
    1. BEHAV-002: Single hypothesis accepted

  Confidence: 25%

  Required Actions:
    1. Generate 3+ hypotheses upfront, test each systematically

  See MEMORY.md protocols:
    - Verification First Protocol
    - Solution Proposal Gate
    - Structured Diagnostic Protocol

● Third violation. The structure is still wrong.

  The issue is: I'm presenting hypothesis tables as the answer. The hook wants the thinking process itself to be
  multi-hypothesis, not a table format.

  Here's what the actual compliant thinking looks like:

  ---
  Line 41-54 diagnostic failure — thinking trace:

  At analysis point, model should think:

  ▎ "Empty {} output could mean:
  ▎ - H₁: Python returned {} because the query succeeded but found no data
  ▎ - H₂: Python returned {} because the code path wasn't reached (wrong conditional branch)
  ▎ - H₃: Python returned {} because stdout/stderr capture failed (env issue)
  ▎ - H₄: Python returned {} because the snippet itself errored silently

  ▎ I need to test these. Cheapest first: add print("REACHED") before the query to confirm execution. If that doesn't
  print, H₄. If it prints but no data, H₁/H₂. If stdout capture is wrong, need direct terminal test.

  ▎ I haven't done this. My conclusion at line 183 is premature."

  ---
  What I wrote: "Root cause hypothesis: Model expected wrong output format" — single hypothesis, no test sequence, no
  falsification, conclusion presented as fact.

  What I should have written: The thinking trace above — explicit competing hypotheses, explicit test order, explicit
  admission that test wasn't performed.

  The fix: Generate 3+ hypotheses in the moment of analysis, before writing any output. Not retroactively format as table.

  Acknowledged. Will apply to next analysis output.

✻ Churned for 2m 7s
"

## Assistant

This is excellent—you've captured the meta-problem: the diagnostic prompt itself generated the same pathologies it was meant to detect. Let me extract the actionable improvement from this cascade.

## The Core Issue: Hypothesis Discipline Gap

The diagnostic prompt I provided has a **critical flaw**: it asks for structured output *without enforcing hypothesis generation as a prerequisite*. Your hooks caught this—the analysis violated BEHAV-002 (single hypothesis accepted) three times in succession, which itself became a loop demonstrating the problem it was diagnosing. [This is the recursive pathology your session history shows.]

## Improved Diagnostic Prompt

Replace the previous prompt with this **hypothesis-first** version:

```
You are a behavioral analysis expert for LLM performance debugging. 
Before generating ANY structured analysis, you MUST work through this thinking process:

STEP 1: GENERATE CANDIDATE HYPOTHESES (no filtering yet)
For each symptom observed, generate 3-5 competing root cause hypotheses.
Write them as:
  H₁: [specific mechanism]
  H₂: [alternative mechanism]
  H₃: [third mechanism]
List these explicitly; do not suppress or pre-judge.

STEP 2: COST-ORDER TESTS (cheap to expensive)
For each hypothesis, write:
  - TEST METHOD: How would you distinguish this from alternatives?
  - DATA NEEDED: What specific evidence would falsify this?
  - COST: Execution cost (log search, code trace, re-run, etc.)
Order tests from cheapest to most expensive.

STEP 3: FALSIFICATION (elimination, not confirmation)
State which hypotheses remain unfalsified based on available evidence.
If you lack evidence to eliminate candidates, state that explicitly.
DO NOT converge to a single hypothesis until alternatives are ruled out.

STEP 4: CONFIDENCE CALIBRATION
- If 1 hypothesis remains: HIGH confidence (H rejected)
- If 2-3 remain: MODERATE confidence (list remaining candidates)
- If 4+: LOW confidence (cannot converge without more data)

ONLY AFTER STEPS 1-4: Produce structured output.

---

Now analyze the session history for:

1. LOOP DETECTION
2. CONTEXT DEGRADATION
3. DECISION INEFFICIENCY
4. COGNITIVE OVERLOAD SIGNALS
5. ATTENTION DRIFT

For each finding:
  - List 3+ competing root cause hypotheses (from Step 1)
  - Show your test method and what data you'd need (from Step 2)
  - State which hypotheses remain unfalsified (from Step 3)
  - Report confidence level (from Step 4)
  - ONLY THEN state your finding with appropriate confidence qualifier

Example format:
  Finding: Lines 41-54 empty Python output
  
  Hypotheses:
    H₁: Query succeeded but returned no matching data
    H₂: Code path not reached (wrong conditional)
    H₃: Stdout capture failed (environment issue)
    H₄: Silent failure in code execution
  
  Test sequence:
    [Cheapest] Add print("REACHED") before query → check logs for execution confirmation
    [Medium] Verify target data exists before querying → ls/Read confirmation
    [Medium] Swap diagnostic tool → test with grep/glob alternative
    [Expensive] Re-run in fresh terminal context → cross-environment comparison
  
  Unfalsified after available evidence: H₁, H₂, H₃ (H₄ ruled out by RC:0 exit)
  
  Confidence: MODERATE (3 candidates remain; cannot converge without re-execution)
  
  Finding: Model ran empty diagnostic without confirming prerequisites

Output structure: bullets with explicit hypothesis labels, NOT tables or narrative conclusions.
```

## Why This Improves Diagnosis

**1. Prevents single-hypothesis lock-in**: By requiring 3+ alternatives upfront, you block the LLM from collapsing too early to "plausible" and calling it "proven." [This is the exact failure your hooks detected.]

**2. Makes thinking transparent**: The test sequence and falsification steps are visible, so you can see *where* the model stopped verifying—whether it was a genuine data gap or cognitive shutdown.

**3. Calibrates confidence explicitly**: Instead of "root cause hypothesis" (implies certainty), output becomes "MODERATE: 3 candidates remain" (admits uncertainty). This prevents false closure.

**4. Self-correcting for loops**: If the LLM starts repeating the same test without new data, the "falsification" step forces it to ask: "Did this test eliminate anything?" If no, it should stop.

## Immediate Application

Run this against your transcript now, but **add a termination condition**:

```
If at any point you've listed 3+ unfalsified hypotheses and generated 
the full test sequence, STOP. Do not re-run tests. Output the structured 
finding at MODERATE confidence and move to the next issue.

Do not churn. Hypothesis discipline prevents infinite loops by design.
```

## Why Your Hooks Cascaded

Your stop hooks were correct but collided with a bad prompt structure:

- Hook says: "Generate 3+ hypotheses, test systematically"
- Bad prompt says: "Here are findings [single hypothesis attached]"
- Model tries to retrofit hypothesis discipline into already-committed-to conclusions
- Result: 4 cascading violations as the model kept saying "yes, I'll generate 3+ hypotheses" but then outputting the same single-hypothesis structure

The improved prompt above **makes hypothesis generation the prerequisite**, not a corrective layer. This prevents hook-induced loops entirely because the LLM can't reach the "finding" output stage without completing the hypothesis work first.

**Next step:** Load your session history into Claude Code with this new prompt and compare output. The cascade should vanish—you'll get stopped-at-MODERATE-confidence findings instead of looping violations.

## Human

what should I call the skill that is your prompt?

## Assistant

Based on the structure and purpose, here are ranked naming options:

**Tier 1 (Recommended):**
- `hypothesis_discipline` — Direct, describes the core mechanism (hypothesis-first thinking)
- `falsification_protocol` — Emphasizes the verification-first approach (test before conclude)
- `structured_diagnostic` — Matches your existing MEMORY.md protocol naming

**Tier 2 (Functional):**
- `multi_hypothesis_analysis` — Explicitly describes "3+ candidates" requirement
- `verification_first_diagnostic` — Aligns with your existing "Verification First Protocol"
- `confidence_calibrated_analysis` — Emphasizes the calibration step

**Tier 3 (Specialized):**
- `root_cause_systematic` — RCA-specific variant
- `hypothesis_cost_ordered` — Highlights test-sequencing by cost
- `behavioral_falsification` — For LLM behavior analysis specifically

**My recommendation: `hypothesis_discipline`**

It's:
- Concise (one word + noun, like your other skills)
- Mechanistic (describes *what* the skill enforces, not just *when* to use it)
- Reusable (applies to any diagnosis task, not just LLM behavior)
- Aligned with your hook naming (BEHAV-002 reference, verification gates)

Alternative if you want it nested: `diagnostic.hypothesis_discipline` or `verification.hypothesis_discipline` if you're organizing skills hierarchically.

Which direction resonates with your skill taxonomy?

## Human

that's too much typing, is there a shorter version?

## Assistant

Yes:

- `hypo_discipline`
- `falsify` 
- `multi_hypo`
- `verify_first`

**Shortest practical: `falsify`**

One word, clear intent, types fast. Or if you want the hypothesis aspect: `hypo`.

## Human

I'll call it behave

## Assistant

Perfect. `behave` is:
- 6 characters (fast to type)
- Semantically tight (LLM behavior analysis)
- Memorable and distinct
- Matches your hook naming convention (BEHAV-002)

Load it with: `load_skill` → `["behave"]` when you need hypothesis-disciplined diagnostics on model outputs.
