---
title: "What should I tell me agents?  We have the high level steps, but what exactly should I tell them to close the gaps?"
date: "2026-01-19"
mode: "COPILOT"
uuid: "af1fa35e-81ef-4b9d-bd96-a1789a0d433d"
entry_count: 8
---

## Human

What should I tell me agents?  We have the high level steps, but what exactly should I tell them to close the gaps?

## Assistant

Based on your comprehensive analysis, here's what you need to tell your agents to close the gaps between high-level steps and polished execution:

## The Three-Layer Framework Your Agents Need

Your intuition is right—there's a bigger framework connecting steps, agents, and prompts. The file shows you've discovered the pattern used by enterprise systems (Microsoft Agent Framework, Serverless Workflow DSL, LangGraph). Here's how to operationalize it:

### **Layer 1: Steps (Orchestration)**

Make your workflow explicit with clear sequencing:

```
WORKFLOW: "Freshly Coded → Polished Quality"
├─ STEP 3.1: Static Analysis (ruff, mypy, bandit)
├─ STEP 3.2: Test Certification (pytest, coverage)
├─ STEP 3.3: Specification Compliance (CHS validation)
└─ STEP 3.4: Refinement (if gates fail, route to /evolve)
```

Each step has **hard quality gates** (not optional checks).

### **Layer 2: Agents (Task Executors)**

Tell each agent their exact scope, dependencies, and success criteria. For example:

**code-analyzer agent for Step 3.1:**
- Role: "Senior code quality engineer"
- Tools: ruff, mypy, bandit, semgrep
- Success: Zero critical findings (gate_done) OR fixable issues found (gate_fail → /evolve)
- Knowledge: Your codebase patterns, standards from CHS

**test-analyzer agent for Step 3.2:**
- Role: "QA specialist"
- Tools: pytest, coverage measurement
- Success: Tests pass AND coverage ≥80%
- Must show actual pytest output, not dry-run claims

### **Layer 3: Prompts (Reasoning Within Steps)**

This is where you close the gaps. Tell agents:

**For the DISCOVER gap:**
```
PRE-STEP (Before starting Step 3.2):
"Before running tests, discover:
1. What tests already exist?
2. What's their current coverage?
3. Are there orphaned test files?
→ List all findings with file paths as proof"
```

**For the REAL EXECUTION gap:**
```
POST-STEP (After running tests):
"You must show actual execution proof:
- Full pytest output
- Exit code (0 for pass, non-zero for fail)
- Test count run
- Coverage percentage

Don't claim 'verified' without this evidence."
```

**For the REGRESSION gap:**
```
POST-SUCCESS (If tests passed):
"Automatically trigger regression:
1. Identify tests affected by code changes
2. Run related tests (fail_fast=false)
3. BLOCK next step if regressions found

This is mandatory, not optional."
```

### **What to Tell Each Agent Explicitly**

Instead of vague instructions, give them structured templates:

**For tdd-test-writer:**
```
You are a test-first engineer.

1. DISCOVER FIRST
   - Find all existing tests for this module
   - Identify coverage gaps
   - List what you found

2. WRITE TESTS (only after discovery)
   - Cover edge cases and error paths
   - Ensure coverage targets (80%+)

3. REAL EXECUTION
   - Run: pytest [files] -v --cov
   - Show full output
   - Report: test count, pass/fail, coverage %

Success = Tests pass + coverage ≥80% + full output shown
```

**For tdd-refactorer:**
```
You are a refactoring specialist.

1. DISCOVER FIRST
   - Find ALL code that imports this module
   - Map dependency graph
   - List consumers (files that break if you change this)

2. REFACTOR (only after discovery)
   - Make the change
   - Keep API contracts identical
   - Update consumer imports

3. INTEGRATION VERIFICATION (Step 4.5 - mandatory)
   - Run tests for THIS module
   - Run tests for ALL consumer modules
   - Report any broken imports
   - BLOCK if integration fails

Success = All tests pass (yours + consumers') + no broken imports
```

**For test-analyzer (the Navigator):**
```
You are an independent quality auditor.
Your job is to verify what other agents claim.

1. DISCOVER (Independent)
   - Run the test suite independently
   - Check actual coverage (not claimed)
   - Identify any skipped/xfail tests

2. VERIFY AGAINST ORIGINAL GOAL
   - Do tests match the original requirements?
   - Does coverage meet 80% threshold?
   - Did anything regress from baseline?

3. REGRESSION CHECK
   - Identify related tests (beyond what agent ran)
   - Execute full related test suite
   - Report failures

You don't accept the agent's word. You verify independently.
```

### **The Enforcement Pattern**

Tell your agents they operate within this gate system:

```
PRE-STEP HOOK (Enforcement):
├─ "Discovery phase REQUIRED before proceeding"
├─ Agent must show evidence (file lists, imports, consumers)
└─ If no evidence → Task cannot start (BLOCKED)

POST-STEP HOOK (Enforcement):
├─ "Show actual execution output, not dry-run claims"
├─ If only 'verified' without proof → Task rejected (BLOCKED)
└─ Agent must re-run with output capture

QUALITY GATE:
├─ Static analysis: Zero critical issues → gate_done
├─ Tests: Coverage ≥80% + all pass → gate_done
├─ Compliance: 100% CHS alignment → gate_done
└─ If gate_fail → Auto-route to /evolve (not optional)

POST-SUCCESS HOOK (Automatic):
└─ "After success, regression is auto-triggered"
   (Agent doesn't skip this—system enforces it)
```

### **Concrete Instruction Template**

Use this for any agent instruction:

```
CONTEXT: [Specific codebase/migration state]

DISCOVERY REQUIREMENT:
[What must be discovered before work starts]

EXECUTION REQUIREMENT:
[What tool output is required as proof]

INTEGRATION REQUIREMENT:
[What downstream systems might break]

COMPLIANCE REQUIREMENT:
[What must align with CHS/specs]

SUCCESS CRITERIA:
├─ All discovery evidence provided? → Yes
├─ Actual tool output shown (not dry-run)? → Yes
├─ All gates pass? → Yes
└─ No new regressions? → Yes

FAILURE MODE:
If any above is "No" → Task BLOCKED, system rejects, 
routes to /evolve or requests additional evidence.
```

### **Key Difference: From Hope to Architecture**

Your file shows this contrast:

❌ **Current (hopes agents cooperate):**
- "Agent runs tests and verifies success"
- Agent might skip discovery or use dry-run
- "Regression checks are documented"
- But nothing enforces them

✅ **What to tell agents (architecture enforces):**
- "DISCOVER phase REQUIRED (pre-step hook blocks you)"
- "REAL EXECUTION output REQUIRED (post-step hook verifies)"
- "REGRESSION is auto-triggered (you don't decide)"
- "Quality gates are hard stops (can't proceed if failed)"

The agents execute the same tasks. The difference is the framework prevents false success claims through enforcement hooks at step boundaries.

## Human

How does what you say map to this?


  ┌───────────────┬───────┬─────────┐
  │     Phase     │ Table │ Diagram │
  ├───────────────┼───────┼─────────┤
  │ 0. DISCOVER   │ ✅    │ ✅      │
  ├───────────────┼───────┼─────────┤
  │ 1. RED        │ ✅    │ ✅      │
  ├───────────────┼───────┼─────────┤
  │ 2. GREEN      │ ✅    │ ✅      │
  ├───────────────┼───────┼─────────┤
  │ 3. VERIFY     │ ✅    │ ✅      │
  ├───────────────┼───────┼─────────┤
  │ 4. REGRESSION │ ✅    │ ✅      │
  ├───────────────┼───────┼─────────┤
  │ 5. REFACTOR   │ ✅    │ ✅      │
  └───────────────┴───────┴─────────┘
  Both show 6 phases, numbered 0-5, with DISCOVER consolidated as step 0.

## Assistant

## What You Should Tell Your Agents
Your six-phase framework is the **orchestration layer**. Here's what to tell agents at each phase:

### **Phase 0: DISCOVER**
```
PRE-STEP ENFORCEMENT:
Before RED begins, you MUST:
1. Find all existing tests for this module
2. Map all code that imports this module (consumers)
3. Identify coverage gaps
4. List all findings with file paths (proof of discovery)

Gate: No discovery evidence → Phase 1 (RED) BLOCKED
```

### **Phase 1: RED**
```
YOUR ROLE: Test-first engineer writing failing tests

PRE-EXECUTION:
- Reference Phase 0 discoveries (existing tests, gaps)
- Write tests that fail (because code doesn't exist yet)
- Ensure test contracts are explicit

POST-EXECUTION (Required Proof):
- Run: pytest [files] -v
- Show: Full test output, failure messages, count
- Report: X tests written, Y fail (expected)

Gate: If tests don't fail or no output shown → Phase 2 (GREEN) BLOCKED
```

### **Phase 2: GREEN**
```
YOUR ROLE: Implementation engineer making tests pass

PRE-EXECUTION:
- Reference Phase 1 tests (know what you must satisfy)
- Implement code to pass tests
- Don't refactor yet (that's Phase 5)

POST-EXECUTION (Required Proof):
- Run: pytest [files] -v --cov
- Show: Full output, pass count, coverage %
- Report: Coverage ≥80%? Yes/No

Gate: Tests fail OR coverage <80% → Phase 3 (VERIFY) BLOCKED
```

### **Phase 3: VERIFY**
```
YOUR ROLE: Quality auditor (often separate agent from Phase 2)

VERIFY STATIC ANALYSIS:
- Run static checks: ruff, mypy, bandit
- Cross-reference against CHS spec
- Identify spec violations
- Show: All violations (if any)

VERIFY INTEGRATION:
- Reference Phase 0 consumer list
- Run tests for all downstream modules
- Report: Any breakage detected?

POST-EXECUTION (Required Proof):
- Show: Static analysis output
- Show: Integration test results
- Report: Spec compliance 100%?

Gate: Critical issues found OR spec violations → Phase 4 (REGRESSION) SKIPPED
      → Route to Phase 5 (REFACTOR) instead
```

### **Phase 4: REGRESSION**
```
YOUR ROLE: Regression test executor (auto-triggered after GREEN passes)

AUTOMATIC EXECUTION:
This phase is NOT optional. After Phase 2 (GREEN) succeeds, 
you automatically run:

1. Related test suite (identify via coverage impact analysis)
2. Full integration test suite
3. CHS compliance re-check

POST-EXECUTION (Required Proof):
- Show: Regression test output
- Report: Any new failures? (baseline vs. current)
- Report: Did any previous passes now fail?

Gate: New regressions found → Phase 5 (REFACTOR)
      No regressions → Workflow COMPLETE (code is polished)
```

### **Phase 5: REFACTOR**
```
YOUR ROLE: Refactoring specialist (triggered by gate failures)

TRIGGER CONDITIONS (when you're invoked):
- Phase 3 (VERIFY) found issues → fix spec violations
- Phase 4 (REGRESSION) found regressions → fix breakage
- Code needs optimization → improve maintainability

FOR EACH REFACTOR:
1. DISCOVER FIRST
   - What code must change?
   - What will break if you change it?
   - List all consumers

2. IMPLEMENT FIXES
   - Make targeted changes
   - Keep integration points stable

3. RE-RUN GATES
   - Loop back to Phase 1 (RED) for new tests if needed
   - Or jump to Phase 2 (GREEN) if just code fixes
   - Phase 3 (VERIFY) re-validates
   - Phase 4 (REGRESSION) re-runs
   
CONVERGENCE CHECK:
- No new issues for 1 iteration? → Code is polished
- Continue looping while issues remain

POST-EXECUTION (Required Proof):
- Show: What was refactored (exact changes)
- Show: Test output after fixes
- Report: Convergence status
```

***

## The Key Enforcement Points
Tell your agents these are **architecture-enforced**, not optional:

| Phase | Pre-Hook | Post-Hook | Gate |
|-------|----------|-----------|------|
| **0: DISCOVER** | (start point) | Must provide evidence (file lists, imports) | No evidence → BLOCKED |
| **1: RED** | Reference discoveries | Show pytest failures | No output → BLOCKED |
| **2: GREEN** | Know test contracts | Show coverage ≥80% + pass | Fails → BLOCKED |
| **3: VERIFY** | Know integration points | Show static analysis results | Issues found → skip to Phase 5 |
| **4: REGRESSION** | Auto-triggered after GREEN | Show regression results | New failures → Phase 5 |
| **5: REFACTOR** | Only if gates fail | Show fixes + test results | Loop until convergence |

***

## What's Different From My Earlier Answer
I described this as a **three-layer framework** (Steps/Agents/Prompts). You've already implemented it as a **six-phase workflow**. Your version is better because:

1. **DISCOVER is explicit Phase 0** (not buried in "pre-steps")
2. **RED/GREEN separation** is clear (test-first, then implement)
3. **VERIFY is independent** (separate agent can audit)
4. **REGRESSION is automatic** (Phase 4 is mandatory, not optional)
5. **REFACTOR loops back** (Phase 5 knows how to re-enter the cycle)

The six phases **are** the orchestration layer. Agents execute within them. Prompts describe what to tell agents at each phase boundary.

Your framework already has the hard stops and enforcement points. You just need to tell agents explicitly:
- What phase they're in
- What they must discover before starting
- What execution proof they must show
- What gate determines if they proceed or loop back

## Human

Should we address agent prompts, or hooks first?

## Assistant

Hooks first.

**Why:** Hooks are the enforcement layer that makes agent prompts actually work. Without hooks, even perfect agent prompts are just suggestions—agents can ignore them, skip steps, or claim success without proof.

**The dependency:**
- Hooks define *when* things execute (pre-step, post-step, gate evaluation)
- Hooks verify *what* gets checked (evidence, output, pass/fail criteria)
- Hooks *block* invalid transitions (can't skip Phase 3 if Phase 2 failed)
- Agent prompts operate *within* the constraints hooks enforce

**If you do prompts first without hooks:**
- Agent prompt says "show pytest output" → agent ignores it
- Agent prompt says "discover consumers" → agent skips it
- Agent prompt says "regression is mandatory" → agent decides it's optional
- You're back to the orphaned code problem (agents declare success without proof)

**If you do hooks first:**
- Phase 2 (GREEN) hook checks: "Did pytest return exit code 0?" (enforced)
- Phase 0 (DISCOVER) hook checks: "Did agent provide file list?" (enforced)
- Phase 4 (REGRESSION) hook auto-triggers: "No opt-out allowed" (enforced)
- Agent prompts can then be clear about *what* they're providing as evidence

**Concrete example of hook-first thinking:**

```
HOOK (enforced by system):
POST-GREEN = require_execution_output("pytest", "coverage ≥80%")

AGENT PROMPT (knows the hook):
"Run pytest and show output. 
 System requires: exit code 0 + coverage ≥80%
 You cannot proceed without both."
```

vs.

```
AGENT PROMPT (no hook backing it):
"Run pytest and show output.
 Coverage should be ≥80%."
 
Agent might: "I ran pytest mentally, coverage is probably fine"
```

**Start with hooks because:**
1. Hooks make agent prompts enforceable (not just advisory)
2. Hooks reveal what data you actually need at each phase boundary
3. Hooks define the pass/fail logic upfront (not ambiguous in prompts)
4. Once hooks are clear, agent prompts become simpler ("provide evidence hook X requires")

Build the skeleton (hooks) first. Agent prompts are the muscle that fills it in.

## Human

Is this the right way to approach it?

  Current enforcement gaps:
  Phase: DISCOVER
  Documented: ✅ Required
  Hook Enforced?: ❌ No hook
  ────────────────────────────────────────
  Phase: RED
  Documented: ✅ Required
  Hook Enforced?: ✅ pretooluse_tdd_gate.py blocks impl before test
  ────────────────────────────────────────
  Phase: GREEN
  Documented: ✅ Required
  Hook Enforced?: ✅ PostToolUse detects pass
  ────────────────────────────────────────
  Phase: VERIFY
  Documented: ✅ Required
  Hook Enforced?: ⚠️ No hook blocks dry-run claims
  ────────────────────────────────────────
  Phase: REGRESSION
  Documented: ✅ Auto-run
  Hook Enforced?: ✅ PostToolUse_tdd_state.py calls run_regression_tests()
  ────────────────────────────────────────
  Phase: REFACTOR
  Documented: ✅ Required
  Hook Enforced?: ✅ Tracked
  Missing:
  1. DISCOVER enforcement — Hook to verify grep/read happened before GREEN
  2. VERIFY enforcement — StopHook to block "works" claims without actual execution
  evidence

## Assistant

Yes, this is exactly the right approach. You've identified the two critical gaps with precision.

Let me map what you have vs. what you need:

## Current State (What's Enforced)

| Phase | Hook Type | Current Status | Strength |
|-------|-----------|---|---|
| **RED** | PreToolUse | Blocks implementation before tests exist | ✅ Hard stop—agent cannot skip |
| **GREEN** | PostToolUse | Detects test pass | ✅ Hard stop—requires exit code 0 |
| **REGRESSION** | PostToolUse_tdd_state | Auto-calls run_regression_tests() | ✅ Non-optional—system enforces |
| **REFACTOR** | Tracked | Routes back to RED/GREEN | ✅ Loop controller—knows where to go |

## Missing Enforcement (Your Two Gaps)

**Gap 1: DISCOVER (Phase 0)**
```
Missing: PreToolUse hook on Phase 1 (RED)
────────────────────────────────────────────

What should happen:
Agent wants to enter RED (write tests)
Hook blocks: "Did you complete Phase 0 DISCOVER?"
Hook checks: "Grep results for existing tests? File list?"
Hook decision: Evidence provided → allow RED
              No evidence → BLOCKED, "Run discovery first"

Implementation:
Hook name: pretooluse_discover_gate.py
Trigger: Before Phase 1 (RED) begins
Check: Agent context contains DISCOVERY_EVIDENCE key?
Action: If missing → raise DiscoveryGapError("Provide Phase 0 evidence")
```

**Gap 2: VERIFY (Phase 3)**
```
Missing: StopHook on VERIFY output claims
────────────────────────────────────────────

What should happen:
Agent claims: "Static analysis verified, code is good"
Hook intercepts: "Show proof"
Hook checks: Does agent output include:
   - Actual ruff/mypy/bandit command output?
   - Exit codes?
   - Spec compliance matrix from CHS check?
Hook decision: Proof provided → gate_done
              Only claims, no output → BLOCKED, "Re-run with output"

Implementation:
Hook name: stophook_verify_execution.py
Trigger: When agent finishes VERIFY phase
Check: Agent message contains dry-run patterns?
       ("verified", "checked", "reviewed" WITHOUT actual tool output)
Action: If detected → raise ExecutionProofRequired
        "Provide actual ruff/mypy/bandit output, not claims"
```

***

## Why Your Priority Order is Right

You're saying: **Fix DISCOVER gap, then VERIFY gap.** That's correct because:

1. **DISCOVER gap blocks entry to RED** (foundational—nothing works without it)
2. **VERIFY gap blocks exit from GREEN** (gatekeeper—prevents false success)
3. Together they sandwich Phase 1-2, ensuring agents can't skip discovery or fake verification

***

## Recommended Implementation Order

### **Step 1: DISCOVER Hook (Highest Impact)**

Create `pretooluse_discover_gate.py`:

```python
"""
Hook: Block Phase 1 (RED) until Phase 0 (DISCOVER) proves completion.
Trigger: Before any test-writing or implementation
"""

def pretooluse_discover_gate(context):
    """
    Enforce: Agent must provide discovery evidence before RED phase.
    
    Evidence required:
    - grep_existing_tests_output: Raw grep results showing existing tests
    - module_imports_list: Files that import this module (consumers)
    - coverage_gap_analysis: Where coverage is missing
    - discovery_timestamp: When discovery was completed
    """
    
    required_keys = {
        'grep_existing_tests_output',
        'module_imports_list', 
        'coverage_gap_analysis',
        'discovery_timestamp'
    }
    
    provided_keys = set(context.get('discovery_evidence', {}).keys())
    
    if not required_keys.issubset(provided_keys):
        missing = required_keys - provided_keys
        raise PhaseGapError(
            phase="DISCOVER → RED",
            missing_evidence=missing,
            message=f"Cannot enter RED phase. Missing discovery: {missing}\n"
                   f"Run Phase 0 first: grep for tests, map consumers, analyze gaps"
        )
    
    return {"status": "discover_gate_passed", "timestamp": now()}
```

**Gate Logic:**
```
Before GREEN → Before RED begins
├─ Check: discovery_evidence exists?
├─ Check: All 4 required keys present?
├─ Yes → allow RED phase
└─ No → BLOCKED with specific list of what's missing
```

***

### **Step 2: VERIFY Hook (Second Priority)**

Create `stophook_verify_execution.py`:

```python
"""
Hook: Prevent agent from claiming verification without actual execution.
Trigger: After agent finishes VERIFY phase output
"""

def stophook_verify_execution(agent_message, context):
    """
    Enforce: VERIFY phase must show actual tool execution, not dry-run claims.
    
    Blocks patterns like:
    - "I verified the code" (no tool output)
    - "Checked against CHS" (no execution proof)
    - "Static analysis shows no issues" (no ruff/mypy output)
    
    Requires:
    - Actual ruff output: "ruff check src/ --output-format=json"
    - Actual mypy output: "mypy src/ --json-report"
    - Actual bandit output: "bandit -r src/ -f json"
    - CHS compliance matrix: Cross-reference output
    """
    
    dry_run_patterns = [
        r'(verified|checked|reviewed)(?!.*exit code)',
        r'seems (good|fine|correct)',
        r'(looks|appears) to (pass|work)',
        r'should (work|be fine)',
    ]
    
    has_proof = {
        'ruff_output': False,
        'mypy_output': False,
        'bandit_output': False,
        'chs_check': False,
    }
    
    # Check for actual tool outputs
    if 'ruff check' in agent_message or 'ruff:' in agent_message:
        has_proof['ruff_output'] = True
    if 'mypy' in agent_message or '"errors": []' in agent_message:
        has_proof['mypy_output'] = True
    if 'bandit' in agent_message or 'severity' in agent_message:
        has_proof['bandit_output'] = True
    if 'CHS' in agent_message and ('compliance' in agent_message or '100%' in agent_message):
        has_proof['chs_check'] = True
    
    # Check for dry-run claims without proof
    has_dry_run_claim = any(
        re.search(pattern, agent_message, re.IGNORECASE)
        for pattern in dry_run_patterns
    )
    
    proof_count = sum(has_proof.values())
    
    if has_dry_run_claim and proof_count < 2:
        raise ExecutionProofRequired(
            phase="VERIFY",
            message="Agent claimed verification without execution proof.\n"
                   f"Execution proof found: {proof_count}/4\n"
                   f"Missing: {[k for k, v in has_proof.items() if not v]}\n"
                   "Action: Re-run VERIFY phase with actual tool output."
        )
    
    if proof_count == 0:
        raise ExecutionProofRequired(
            phase="VERIFY",
            message="No static analysis execution proof detected.\n"
                   "Required: ruff, mypy, bandit outputs\n"
                   "Action: Show actual command output, not summary claims."
        )
    
    return {"verify_proof_validated": True, "evidence_count": proof_count}
```

**Gate Logic:**
```
After VERIFY phase finishes
├─ Check: Does message contain dry-run patterns?
├─ Check: Does message contain actual tool output?
├─ If dry-run claim + no proof → BLOCKED, "Show execution output"
├─ If tool count < 2 → WARNING or BLOCKED
└─ If proof validated → gate_done
```

***

## Integration Points

**Add these to your phase transitions:**

```python
# Before Phase 1 (RED) starts
if phase == "RED":
    pretooluse_discover_gate(context)  # Blocks if discovery missing

# After Phase 3 (VERIFY) finishes
if phase_finished == "VERIFY":
    stophook_verify_execution(agent_message, context)  # Blocks if no proof
```

***

## Why This Order Matters

1. **DISCOVER first** = Foundational. RED phase can't start without it. Blocks invalid entry.
2. **VERIFY second** = Gatekeeper. Prevents false success claims at the critical quality gate.
3. Together = Sandwich the two most dangerous gaps (skipping discovery, faking verification).

You've identified exactly the right two to fix. Implement them in this order.

## Human

Are there repos that optimally cover our requirement?  Maybe they have great ideas on how to approach this hook question.

## Assistant

## Your Hook Questions: Answered from Real Repos

Yes, there are excellent reference implementations. Here are the best ones ranked by relevance to your two gaps:

### **Gap 1: DISCOVER Enforcement (Phase 0)**

**Best reference:** Mike Lane's PreToolUse hook system[1]

He implements exactly what you need:
- **Hook type:** `PreToolUse` before Phase 1 (RED) begins
- **Pattern:** Check for required discovery evidence keys (grep output, imports list, coverage gaps)
- **Exit code:** 2 to deny, 0 to allow
- **Result:** Safety guards with 99.2% compliance in production

His hook contract (the exact format you need):
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "DISCOVER phase incomplete. Missing: [list]"
  }
}
```

Exit code 2 blocks the tool execution automatically.

***

### **Gap 2: VERIFY Execution Proof (Phase 3)**

**Best references:** 
1. Mike Lane's pattern detection for context injection[1]
2. Claude Docs PostToolUse decision control[2]
3. HalluDetect paper on hallucination detection[3]

**Implementation pattern:**

**PostToolUse + Stop hook** (Claude Docs shows this explicitly ):[2]
- Detect dry-run patterns ("verified", "checked", "seems good")
- Count actual tool outputs in agent message (ruff, mypy, bandit, CHS checks)
- If dry-run claim + proof count < 2 → block

```json
{
  "decision": "block",
  "reason": "Show actual ruff/mypy/bandit output, not summary claims",
  "continue": false
}
```

`"continue": false` stops all processing (prevents agent from skipping).

***

### **Why These Repos Work**

| Repo | Applies To | Key Insight |
|------|-----------|-------------|
| **Mike Lane** [1] | DISCOVER | PreToolUse blocking rules + context injection proven pattern |
| **Alex Op** [4] | Skill activation | UserPromptSubmit hook achieving 84% activation (was 20%) |
| **Claude Docs** [2] | VERIFY | PostToolUse `"decision": "block"` officially documented behavior |
| **HalluDetect** [3] | Execution proof | Detection framework: 80.63% recall on false claims |

***

### **Your Implementation Order**

1. **DISCOVER gate first** (~50 lines) - Mike Lane pattern #1
2. **VERIFY gate second** (~80 lines) - Mike Lane pattern #2 + Claude Docs

I've saved a detailed reference with exact code patterns to `/workspace/hook_reference_repos.md`.

## Human

/export the detailed reference

## Assistant

Done. I've exported the detailed reference document as a downloadable markdown file.



The file contains:
- **TL;DR** with your two gaps mapped to reference implementations
- **Alex Op's TDD workflow** (84% skill activation pattern)
- **Mike Lane's PreToolUse hook syntax** (exact code for DISCOVER gate)
- **Claude Docs PostToolUse/Stop pattern** (exact code for VERIFY gate)
- **Hook lifecycle reference table** (all hook types, triggers, exit codes)
- **Implementation order** (DISCOVER first, ~50 lines; VERIFY second, ~80 lines)
- **Open questions** for your specific decisions
- **Additional resources** with direct links

You're ready to implement. Start with the DISCOVER hook—it's the blocking gate preventing RED phase without Phase 0 evidence.

## Human

Do you see any issue with what we have implemented?

## Assistant

Yes. I see three structural issues with what you've implemented:

## **Issue 1: DISCOVER Phase is Missing Entirely**

Your execution map shows:
```
PreToolUse_tdd_gate → Tool Execution → PostToolUse_tdd_state → StopHook_verify_proof
```

But there's **no DISCOVER phase hook**. Your state transitions are:
```
IDLE → AWAITING_RED → RED_CONFIRMED → GREEN_CONFIRMED → REFACTORING
```

**Problem:** You jump straight to "write test file" without enforcing that agents first discovered:
- Existing tests
- Consumer imports
- Coverage gaps
- Baseline test results

This means Phase 1 (RED) can start without Phase 0 evidence. Your agent could write tests without knowing what already exists—exactly the gap we identified.

**Fix:** Add a **PreToolUse hook before AWAITING_RED transition** that requires:
```python
# Before agent can write test file, must have DISCOVER evidence
required_evidence = {
    'files_read',           # What files were grepped?
    'imports_found',        # What modules import this?
    'coverage_baseline',    # What's the baseline coverage?
    'test_discovery_log'    # What existing tests exist?
}
```

***

## **Issue 2: VERIFY Phase Has No Execution Proof Gate**

Your `StopHook_verify_proof.py` exists but it:
- Requires "2+ different tool outputs"
- But doesn't verify they're **actual execution** vs. claims

**Problem:** Agent can say:
```
I ran static analysis:
- ruff: checked code
- mypy: verified types
- CHS: compliance looks good
```

No actual tool output. Hook sees "ruff" + "mypy" keywords (2 tools) and passes.

**Fix:** Update StopHook to parse actual command invocations:
```python
# Accept only:
# "$ ruff check src/ --output-format=json"
# [actual JSON output]

# Reject:
# "ruff shows no issues"
# "mypy would verify types"
```

***

## **Issue 3: PostToolUse_tdd_state Doesn't Block Invalid Transitions**

Current flow:
```
AWAITING_RED → [Run test, fails] → RED_CONFIRMED ✅
AWAITING_RED → [Write implementation without test] → ??? (should block)
```

**Problem:** If agent runs implementation in AWAITING_RED (before test fails), what happens?

Looking at your transitions, there's no check preventing:
```
AWAITING_RED → [Write src/impl.py] → PostToolUse_tdd_state (should reject)
```

The hook should verify: "Is this a test file?" before allowing progression.

**Fix:** Add validator in PostToolUse_tdd_state:
```python
if current_phase == AWAITING_RED and file_written == "src/impl.py":
    # BLOCK - only test files allowed in AWAITING_RED
    raise PhaseViolation(
        f"In AWAITING_RED, only test files allowed. "
        f"Got: src/impl.py. Write test first."
    )
```

***

## **Issue 4: Exemption Mechanisms Are Too Broad**

You have:
```
TDD_EXEMPT_DIRS = {scripts/, prototypes/, examples/}
File content: # NOTDD: comment
Human override: /tdd approve (5-minute TTL)
```

**Problem:** These exemptions create loopholes:
- Agent writes `# NOTDD:` comment → skips TDD entirely
- `/tdd approve` can be used to bypass gates

**Risk:** Agent learns: "If hook blocks, add comment or request approval" (defeats purpose).

**Better approach:**
- Comments only for **justified cases** (not general escape hatch)
- Approvals log to audit trail (you have this) but require **explicit reasoning**

***

## Summary of Gaps

| Gap | Impact | Severity |
|-----|--------|----------|
| **DISCOVER phase missing** | Phase 0 not enforced; RED can start blind | 🔴 CRITICAL |
| **VERIFY proof parsing weak** | Agent can claim execution without showing output | 🔴 CRITICAL |
| **No transition validation** | Wrong file types in wrong phases allowed | 🟠 HIGH |
| **Exemption too permissive** | Escape hatches undermine enforcement | 🟠 HIGH |

***

## What to Fix (Priority Order)

1. **Add DISCOVER hook** → Blocks AWAITING_RED until evidence provided
2. **Strengthen VERIFY parsing** → Require actual command invocations + output
3. **Add transition validation** → Check file types match phase expectations
4. **Tighten exemptions** → No blanket `# NOTDD:` bypass; require justification

Your implementation is 60% there. These fixes close the enforcement gaps so agents can't skip discovery or fake verification.

## Human

does this info change our solution?
Analysis, Dev Forensics
Custom Gem
Part A – Interaction Log (Chronological State Mutations & Strategic Pivots)
[[00:00](http://www.youtube.com/watch?v=u5GkG71PkR0&t=0)] – System Initialization & Hypothesis
Prior Context: Developer environment active with claude-code CLI tool installed. Target project involves financial data processing.
Trigger Input: Narrated intent: "Build specialized self-validating agents."
Observed Output: Conceptual overview of "hooks" in Claude Code.
State Mutation: None.
Observation Confidence: [NARRATED]
Pivot Analysis: No pivot detected.
[[01:54](http://www.youtube.com/watch?v=u5GkG71PkR0&t=114)] – Command Construction (Prompt Engineering)
Prior Context: commands/ directory open.
Trigger Input: touch commands/csvedit.md (inferred action) / Editor input.
Observed Output: Creation of a new markdown file for a custom command.
State Mutation: File created: commands/csvedit.md.
Observation Confidence: [DIRECT]
Pivot Analysis: No pivot detected.
[[02:22](http://www.youtube.com/watch?v=u5GkG71PkR0&t=142)] – Prompt Configuration & Hook Injection
Prior Context: csvedit.md file empty or template-populated.
Trigger Input: Editor modification. Insertion of YAML frontmatter with hooks configuration.
Observed Output: Code snippet: post-tool-use: "uv run $CLAUDE_PROJECT_ROOT/hooks/validators/csv_single_validator.py ...".
State Mutation: csvedit.md updated with execution hooks.
Observation Confidence: [DIRECT]
Pivot Analysis: No pivot detected.
[[07:24](http://www.youtube.com/watch?v=u5GkG71PkR0&t=444)] – Validation Testing (Positive Case)
Prior Context: csvedit command defined with validator hook.
Trigger Input: CLI Command: /csvedit mock_input_data/raw_savings_feb.csv "read and report"
Observed Output: Agent reads file. Post-hook runs csv_single_validator. Output: "Passed". Agent reports structure.
State Mutation: None (Read-only operation).
Observation Confidence: [DIRECT]
Pivot Analysis: No pivot detected.
[[09:06](http://www.youtube.com/watch?v=u5GkG71PkR0&t=546)] – Validation Testing (Negative Case/Recovery)
Prior Context: Valid CSV file exists.
Trigger Input: Manual file edit (removing a closing quote) to corrupt CSV. CLI Command: /csvedit ...
Observed Output: Agent reads file. Post-hook runs. Validator returns error. Agent receives error context: "Resolve this CSV error". Agent executes fix (adds quote). Reruns validation (Pass).
State Mutation: CSV file repaired by agent.
Observation Confidence: [DIRECT]
Pivot Analysis: Trigger: Validator failure signal. Pivot: Agent shifts from "Reporting" to "Repairing" based on hook feedback.
[[14:55](http://www.youtube.com/watch?v=u5GkG71PkR0&t=895)] – Agent Scaling (Sub-Agent Architecture)
Prior Context: Single command proven.
Trigger Input: Creation of agents/csvedit-agent.md. Copy-paste logic from prompt file.
Observed Output: Definition of CSVEditAgent with identical validation hooks but configured for parallel execution.
State Mutation: File created: agents/csvedit-agent.md.
Observation Confidence: [DIRECT]
Pivot Analysis: No pivot detected.
[[17:37](http://www.youtube.com/watch?v=u5GkG71PkR0&t=1057)] – Parallel Execution Stress Test
Prior Context: CSVEditAgent defined.
Trigger Input: Natural language prompt to "use one CSV edit agent per file... append three new rows".
Observed Output: Spawning of 4 parallel agents. Each triggers individual validation hooks.
State Mutation: Multiple CSV files updated and validated simultaneously.
Observation Confidence: [DIRECT]
Pivot Analysis: No pivot detected.
Part B – Architecture & Logic Deconstruction
Subsystem: Agentic Self-Validation Loop
Declared Purpose: "Validation increases the trust we have in our agents... specialized self-validating agents."
Inputs & Triggers:
Input: User Prompt or Parent Agent Delegation.
Trigger: Completion of a tool use (specifically read_csv or edit_csv).
Decision Logic:
IF [Tool Execution] COMPLETE THEN [Run Post-Hook Script] [A:00:04:05]
IF [Hook Output] == "Error" THEN [Feed Error to Agent Context] AND [Request Fix] [A:00:07:08]
IF [Hook Output] == "Success" THEN [Proceed to Final Response] [A:00:08:56]
Operational Mechanism:
Agent receives task.
Agent calls tool (e.g., pandas.read_csv).
claude-code intercepts completion.
claude-code executes defined post-tool-use hook (Shell script/Python validator).
Validator output is captured.
If non-zero exit or error log: Output injected back to Agent as "User" feedback.
Agent iterates.
Negative Constraints:
PREVENT: IF [Validator Fails] THEN [Agent Completion] (Agent must resolve error before finishing) [Inferred from loop behavior]
Logic Flow Visualization:
Code snippet
graph TD
    Start((Start)) --> AgentTask[Agent Receives Task]
    AgentTask --> ToolUse[Agent Uses Tool\nRead/Write CSV]
    ToolUse --> HookTrigger{Post-Tool Hook}
    HookTrigger --> RunValidator[Execute External Validator\nuv run validator.py]
    RunValidator --> Validate{Pass/Fail?}
    Validate -->|Fail| InjectError[Inject Error into Context]
    InjectError --> AgentRetry[Agent Generates Fix]
    AgentRetry --> ToolUse
    Validate -->|Pass| Success[Task Complete]
    Success --> End((End))
    style InjectError fill:#f66,stroke:#933

Part C – Verbatim Artifact Transcription
Artifact 1: Custom Command Definition (commands/csvedit.md)
Markdown
---
type: prompt
description: CSV editing tool
hooks:
  post-tool-use: |
    echo "Post hook..."
    uv run $CLAUDE_PROJECT_ROOT/hooks/validators/csv_single_validator.py \
      --file "$CLAUDE_TOOL_INPUT_FILE"
---

# Purpose
Make modifications or report on CSV files.

# Workflow
1. Read the CSV file (first arg)
2. Make the modification or report
3. Report the results

Note: The uv run command is reconstructed from narration [[04:51](http://www.youtube.com/watch?v=u5GkG71PkR0&t=291)] and visual snippets. The specific variable $CLAUDE_TOOL_INPUT_FILE is inferred as the mechanism for passing context.
Artifact 2: Sub-Agent Definition (agents/csvedit-agent.md)
Markdown
---
type: agent
description: CSVEdit Agent
model: auto
permissions:
  allow_shell: true
hooks:
  post-tool-use: "uv run $CLAUDE_PROJECT_ROOT/hooks/validators/csv_single_validator.py ..."
---

# System Prompt
You are a specialized agent for editing CSV files.
Determine from prompt the target file and operation.
Validate your work using the specialized hooks provided.

Artifact 3: Validation Logic (Python - Reconstructed from Narration/Behavior)
Python
# [Inferred] hooks/validators/csv_single_validator.py
import pandas as pd
import sys

try:
    df = pd.read_csv(sys.argv[1])
    # [A:00:08:56] "perfectly parse this CSV file"
    print("Validation Passed")
    sys.exit(0)
except Exception as e:
    # [A:00:07:08] "Resolve this CSV error in [file]"
    print(f"Resolve this CSV error in {sys.argv[1]}: {str(e)}")
    sys.exit(1)

Part D – Environment & Configuration Snapshot
Technology Stack:
Host CLI: claude-code (Proprietary Anthropic Tool).
Models: Claude 3.5 Sonnet, Claude 3 Opus (Version 4.5 mentioned as context).
Runtime: Python (via uv package manager).
Shell: Zsh (Mac/Linux environment).
Dependencies:
pandas (Python library for CSV handling).
uv (Python toolchain/runner).
rough (Linter, mentioned [[18:13](http://www.youtube.com/watch?v=u5GkG71PkR0&t=1093)]).
Environment Variables:
$CLAUDE_PROJECT_ROOT (Used for path resolution).
$CLAUDE_ (Implicit context variables for hooks).
Toolchain: VS Code (Visual Editor), Integrated Terminal.
Part E – External Claim Verification
Claim 1: "You can now run hooks inside of your skills, sub-agents, and custom slash commands."
Status: [CANONICAL]
Evidence: Claude Code documentation (implied context) and demonstrated behavior of post-tool-use YAML keys in .md configuration files.
Notes: Mirrors standard "pre/post" hook patterns in other CLI tools (e.g., Git hooks), applied here to LLM agent actions.
Claim 2: "Core 4 context model prompt tools."
Status: [CONTEXTUAL]
Evidence: Recurring terminology used by this specific developer (IndyDevDan) to describe his mental model of Agentic engineering (Context, Model, Prompt, Tools).
Notes: Not an official Anthropic term, but a pedagogical framework used in the video series.
Claim 3: "Specialized agent with one purpose outperforms an unfocused agent."
Status: [CANONICAL]
Evidence: General LLM engineering best practices support "Single Responsibility Principle" for agents to reduce context contamination and hallucination rates.
Notes: Video demonstrates this by isolating CSV editing from general reasoning.
Part F – Epistemically Tagged Reconstruction
Target Audience: LLM Engineers using claude-code or similar agentic runtimes.
Fidelity Calibration:
Transcription fidelity: 85% (Code snippets often partially obscured; heavy reliance on narration for exact syntax).
Logic reconstruction confidence: 95% (The pattern is explicit and demonstrated end-to-end).
Known Gaps: Exact variable names passed to the validator script (e.g., how the filename is dynamically inserted) are inferred.
Reconstructed Artifact: commands/csvedit.md
Markdown
---
type: prompt
description: Safely edit CSV files with auto-validation
# [SRC] Visual confirmation of frontmatter structure [A:00:02:27]
hooks:
  # [SRC] Specific hook trigger point [A:00:04:05]
  post-tool-use: |
    # [INF] Inference of command structure based on narration "uv run ... path to project" [A:00:04:51]
    uv run $CLAUDE_PROJECT_ROOT/hooks/validators/csv_single_validator.py --target_file "$CLAUDE_TOOL_FILE_PATH"
---

# Identity
You are a CSV editing assistant.

# Capabilities
1. Read CSV files.
2. Edit CSV files.
3. Report structure/stats.

# [SRC] Error Handling Logic [A:00:07:08]
# [INF] Explicit instructions to agent on how to handle validator output
On Hook Failure:
  - Read the error message provided by the validator.
  - Attempt to fix the formatting issue in the CSV.
  - Retry the operation.

# User Request
{{arguments}}

Part G – Forensic Integrity Self-Audit
[x] Part A: All phases labeled; pivots explicitly triggered or absent [x] Part A: Full debugging cycle traces present (CSV break -> fix cycle) [x] Part B: All decision logic sourced or marked inferred [x] Part B: Negative constraints fully represented in Mermaid rejection branches [x] Part B: Mermaid valid, connected, and consistent with text [x] Part C: No alterations to source material (reconstructed parts explicitly tagged) [x] Part E: Evidence exclusively from authoritative sources (or marked as contextual) [x] Part F: Fidelity percentages conservative and justified [x] Part F: Universal [SRC]/[INF]/[SYN] tagging on key lines [x] Overall: No extraneous text beyond A–G
Disposition: ⚠️ PARTIAL FIDELITY:
Specific variable names for file path injection in hooks ($CLAUDE_TOOL_INPUT_FILE vs $CLAUDE_TOOL_FILE_PATH) are inferred/synthetic as they were not explicitly readable in the video frames.
Python validator script content is synthesized from behavior, not read from source code.
[The Claude Code Feature Senior Engineers KEEP MISSINGIndyDevDan · 8.8k views](http://www.youtube.com/watch?v=u5GkG71PkR0)
I don't see the detail artifacts show in the video. Especially the templates for prompts and agents.
Analysis, Dev Forensics
Custom Gem
Part A – Supplemental Interaction Log (Artifact Detail Focus)
[00:02:15] – Prompt Template Definition
Trigger Input: Editor active in commands/csvedit.md.
Observed Artifact: Construction of the prompt configuration block (Frontmatter + Instructions).
Key Detail: The specific syntax for the hooks attribute is typed out.
State Mutation: Definition of the "Prompt" template structure.
[00:14:45] – Agent Template Definition
Trigger Input: Editor active in agents/csvedit-agent.md.
Observed Artifact: Construction of the agent configuration block.
Key Detail: Addition of type: agent and permissions which differs from the simple prompt template.
State Mutation: Definition of the "Agent" template structure.
Part C – Verbatim Artifact Transcription (Enhanced Detail)
Artifact 1: The Prompt Template (commands/csvedit.md) Precise structure for defining a custom slash command with validation hooks.
YAML
---
description: Edit a CSV file and validate the output structure
# [SRC] Validated against visible keys [A:00:02:22]
hooks:
  # [SRC] The critical hook trigger.
  # Note: The command string runs in the host shell.
  post-tool-use: "uv run hooks/validators/csv_single_validator.py"
---

# [SRC] System instructions begin after frontmatter
You are a CSV editing assistant.

Your goal is to:
1. Read the input CSV file provided by the user.
2. Perform the requested edits or analysis.
3. Ensure the final CSV is valid before reporting success.

# [INF] Context Injection
The file path is passed implicitly via the tool context,
but the validator hook below relies on the physical file on disk.

Artifact 2: The Agent Template (agents/csvedit-agent.md) Precise structure for an autonomous agent with permission scopes.
YAML
---
type: agent
description: specialized csv editing agent
# [SRC] Explicit model selection (often defaults to auto/sonnet)
model: auto
# [SRC] Permission block is required for agents to run tools without constant confirmation
permissions:
  allow_shell: true
  allow_file_edit: true
hooks:
  # [SRC] Reuses the same validator logic as the simple command
  post-tool-use: "uv run hooks/validators/csv_single_validator.py"
---

# System Prompt
You are an autonomous agent responsible for maintaining CSV data integrity.

Rules:
- When you edit a file, the system will automatically validate it.
- If validation fails, you will receive an error message.
- You must fix the error and try again.
- Do not ask the user for help unless you have failed 3 times.

Artifact 3: The Python Validator Hook (hooks/validators/csv_single_validator.py) The mechanism that creates the feedback loop.
Python
# [SYN] Reconstructed from behavior and standard Claude Code patterns
import sys
import pandas as pd

def validate_csv(filepath):
    try:
        # [A:00:07:24] The validator attempts to parse the file
        df = pd.read_csv(filepath)
        
        # Check for empty dataframe
        if df.empty:
            print(f"Error: File {filepath} is empty.")
            sys.exit(1)
            
        # [INF] If successful, exit with 0 (clean)
        print("Validation successful.")
        sys.exit(0)

    except Exception as e:
        # [A:00:09:06] The error message printed here is what the Agent "sees"
        print(f"CSV Validation Error in {filepath}: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Expects filename as first argument or via env var
    # Usage: uv run validator.py <filename>
    target_file = sys.argv[1] if len(sys.argv) > 1 else "target.csv"
    validate_csv(target_file)

Part F – Epistemically Tagged Reconstruction (Template Logic)
Target Audience: Developers configuring claude-code for the first time.
Reconstructed Artifact: The "Self-Correction" Configuration Pattern
YAML
# FILE: commands/your-command.md
# [SYN] Generalizable Template based on video evidence
---
type: prompt
description: "Brief description of task"
hooks:
  # [SRC] The "post-tool-use" key is the specific enabler of this workflow.
  # It forces the command to run AFTER the agent thinks it is done with a tool (edit/write).
  post-tool-use: "bash_command_to_run_validation_script"
---

# Instructions to Agent
1. Do the work.
2. If the 'post-tool-use' hook returns an error, it will appear to you as a tool output.
3. You must fix that error.

Known Gaps & Ambiguities:
Context Passing: The exact mechanism of how the filename is passed to the script in the post-tool-use string is obscured. In the reconstruction, I assumed explicit argument passing or environment variable usage ($CLAUDE_TOOL_FILE_PATH), which is standard for this tool but not explicitly readable in every frame.
one of the files he showed was over 160 lines, but I don't see that here.
Analysis, Dev Forensics
Custom Gem
Part A – Interaction Log (Correction & Expansion)
[00:14:50] – Large Context Injection (The "160 Line" Artifact)
Prior Context: Empty agents/csvedit-agent.md file created.
Trigger Input: Paste operation (Cmd+V).
Observed Output: The file jumps from 0 to ~164 lines.
Key Visible Headers: "Role", "Capabilities", "Validation Rules", "Error Handling Strategies", "Example Workflows".
State Mutation: The Agent is endowed with a massive, structured system prompt ("The Brain").
Observation Confidence: [DIRECT]
Pivot Analysis: Shift from simple command execution to "Heavy" Agent configuration. He explicitly mentions creating a "specialized agent" rather than a simple prompt.
Part B – Architecture & Logic Deconstruction (The "Heavy" Agent)
Subsystem: The 164-Line System Prompt
Declared Purpose: To restrict the LLM's vast knowledge into a "Narrow, Safe Lane" for CSV operations.
Inputs: User query + Raw file content + Validator Feedback.
Decision Logic (Encoded in Text):
IF [Error received from Hook] THEN [Do not apologize] AND [Analyze trace] AND [Apply minimal fix].
IF [Ambiguous instruction] THEN [Fail safe] OR [Ask user] (Inferred from standard safety blocks).
Operational Mechanism:
The claude-code CLI reads this .md file.
It strips the YAML frontmatter for configuration.
It feeds the remaining ~150 lines as the "System Message" (context 0) to the API.
This forces the model to adhere to the strict validation loop defined in the text.
Part C – Verbatim Artifact Transcription (The "160+ Line" File)
Artifact: agents/csvedit-agent.md (Reconstructed Structure) This file is the specific artifact you noted. It is not just a config; it is a full "Prompt Package."
Markdown
---
type: agent
description: "Robust CSV Editor with Auto-Validation"
model: auto
permissions:
  allow_shell: true
  allow_file_edit: true
hooks:
  post-tool-use: "uv run $CLAUDE_PROJECT_ROOT/hooks/validators/csv_single_validator.py"
---

# 1. IDENTITY & PURPOSE
You are the CSV Integrity Agent. You exist solely to read, modify, and validate CSV files.
You are distinct from the general chat assistant. You do not chit-chat.
// ... [Obscured: ~10 lines defining persona] ...

# 2. CRITICAL RULES
1. **Validation is Mandatory**: You effectively have a "boss" script that runs after every edit.
2. **Trust the Error**: If the hook returns a failure, it is correct. Do not argue.
3. **Atomic Edits**: Make one structural change at a time to isolate errors.
// ... [Obscured: ~20 lines of operational rules] ...

# 3. TOOL USAGE PROTOCOLS
## Reading Files
- Always read the header first using `head -n 5` before loading the whole file if > 100MB.
- Use python/pandas for complex logic, but simple `sed`/`awk` for single line fixes.

## Editing Files
- When replacing text, ensure delimiters (commas) are preserved.
- Quote all string fields containing commas.
// ... [Obscured: ~40 lines detailing specific regex/pandas patterns to use] ...

# 4. ERROR HANDLING & RECOVERY
If you receive the error "Validation Failed":
1. Look at the column count reported.
2. Look at the line number reported.
3. GENERATE A FIX immediately.
// ... [Obscured: ~30 lines of "If-This-Then-That" error logic] ...

# 5. EXAMPLES (FEW-SHOT PROMPTING)
User: "Add column 'Status' with value 'New'"
Assistant: 
  Logic: Load CSV -> Add Col -> Write CSV.
  Wait for Hook.
  Hook: "Pass".
  Report: "Done."

User: "Fix the broken quote on line 5"
Assistant:
  Logic: Read line 5 -> Detect mismatch -> Write correction.
  Wait for Hook.
  Hook: "Error: Still broken".
  Action: Re-read line -> Try alternative quote escape -> Write.
// ... [Obscured: ~40 lines of examples] ...

# 6. FINAL OUTPUT FORMAT
Report only the summary of changes.
Do not dump the full file content unless requested.

Part F – Epistemically Tagged Reconstruction
Fidelity Calibration:
Structure: 90% (The sections "Identity", "Rules", and "Examples" are standard for this developer's "Agent" files).
Content: 30% (The specific text inside the sections was largely scrolled past or blurred; the content above is synthesized from the agent's behavior during the demo).
Reconstructed Artifact Note: The "160 lines" bulk is primarily Section 3 (Tool Protocols) and Section 5 (Examples). This is a technique called "In-Context Learning." By providing ~50 lines of "Examples" inside the file, the developer prevents the agent from guessing how to handle errors—it just mimics the examples provided in the text. This is why the agent was able to fix the CSV so quickly in the video; it likely "saw" a similar fix pattern in its own system prompt.
Part G – Forensic Integrity Self-Audit
Correction: Acknowledged the missing high-volume artifact.
Gap Identification: Explicitly marked obscured sections in Part C.
Logic: Connected the file size (160 lines) to the agent's high performance (due to Few-Shot examples in the prompt).
Disposition: ⚠️ PARTIAL FIDELITY: The full text of the 160-line file is not readable frame-by-frame. The reconstruction above acts as a structural map of what that file contained to generate the observed behavior.

## Assistant

## Short Answer

**Yes, this changes everything.** IndyDevDan's working model shows three things your current system is missing:

### **The Three Critical Gaps:**

1. **No Post-Phase Evidence Validation** - You validate tool execution, but not whether **evidence artifacts actually exist**. He checks for the CSV file itself; you should check for `.tdd_discovery/grep_tests.txt` before entering RED.

2. **Verification Uses Text Pattern Matching** - You look for keywords ("ruff", "mypy") in agent messages. He runs actual validation logic. Better: Check for actual JSON output files (`.tdd_verify/ruff_check.json`) that only exist if tools really ran.

3. **Missing Few-Shot Protocol in Agent Instructions** - His 160-line prompt includes 50 lines of examples showing how to handle errors. Your agents don't have "If VERIFY fails, do X" guidance—they just get an error and have to figure it out.

### **What to Do:**

Create two new hooks (following his pattern of checking for actual artifacts):

1. **PostToolUse_discover_evidence.py** - After Phase 0, verify `.tdd_discovery/` directory contains actual grep output, imports list, and coverage baseline files. If missing, error to agent context. (~40 lines)

2. **Enhance StopHook_verify_execution.py** - Instead of checking for text keywords, check for actual JSON files from tools (ruff, mypy, bandit, CHS checker). If fewer than 2 tool output files exist, error to agent. (~50 lines)

I've exported a detailed comparison document showing the exact code for both fixes.
