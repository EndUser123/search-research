---
title: "After doing ai assisted coding, what questions should I ask?  I have this but I'm sure you can think of better:

did we "
date: "2025-12-07"
mode: "COPILOT"
uuid: "f52e15e5-0068-4a46-87b4-1ac8d4098701"
entry_count: 6
---

## Human

After doing ai assisted coding, what questions should I ask?  I have this but I'm sure you can think of better:

did we forget anything? any predictable issues?  
any gaps or opportunities?

## Assistant

## Core Verification Questions

Ask these to confirm the code works correctly and handles real-world scenarios. Does the code implement the intended functionality, including edge cases and error handling?  Are there unit tests covering key paths, and do they pass with real data patterns?  Does it align with business logic and project specifications?[1][2][3][4]

## Quality and Maintainability Checks

Evaluate structure, readability, and long-term viability. Is the code modular, with consistent naming and appropriate comments for complex logic?  Does it follow design patterns, avoid excessive complexity, and integrate cleanly with existing architecture?  Have deprecated APIs or hallucinated functions been removed?[5][3][1]

## Performance and Security Review

Probe for hidden issues in efficiency and safety. Are algorithms efficient, memory usage optimized, and performance bottlenecks absent?  Does it handle security concerns like input validation and access controls?  What predictable failure modes exist under load or adversarial inputs?[4][5][1]

## Opportunities and Gaps

Build on your questions with targeted follow-ups. Beyond gaps, ask: What refactoring improves ROI or reduces maintenance?  Are there architectural enhancements or missing features for scalability?  How does this fit your Claude Code workflows or subagent patterns?[5]

## Human

Ask the AI to explain the logic behind each generated function

## Assistant

## Prompt for Function Logic Explanation

Use this targeted prompt after AI generates code: "For each function in the generated code, explain its core logic step-by-step: 1) What problem does it solve? 2) Trace inputs through key decisions and transformations. 3) Identify assumptions or edge cases. 4) Justify why this approach over alternatives. Output as a numbered list per function with code snippets inline."[4][5]

## Why This Prompt Works

This structure elicits Chain-of-Thought reasoning, forcing the AI to break down black-box code into traceable steps, reducing hallucinations by referencing specific lines.  It catches subtle issues like unhandled edges or inefficient paths that blind reviews miss, aligning with your Claude Code verification workflows.  Analogies (e.g., "zipper for baskets") make explanations intuitive for quick mental validation.[2][5][4]

## Integration into Your Checklist

Add as a **Logic Verification** step post-generation, before testing. Chain it with your existing questions: After "Did we forget anything?", run this prompt, then probe "Any gaps in the explained logic?".  For subagents, prefix with "@architect Explain logic..." to leverage parallel review.  This boosts ROI by turning AI into a self-debugging teacher.[1][11]

## Human

How would I make the LLM make less logic and coding errors, before it even starts to write code?

## Assistant

## Pre-Coding Planning Prompts

Force upfront logic validation with a mandatory "Architecture Blueprint" phase before code generation. Prompt: "First, output a step-by-step pseudocode plan covering inputs/outputs, edge cases, error paths, and data flows. Validate: Does this solve [exact problem]? List 3 alternatives and justify the chosen one. Only after my approval, write code."  This catches 70% of logic errors early via Chain-of-Thought decomposition.[1][2]

## Technique Stack

- **Tree-of-Thoughts (ToT):** "Generate 3 divergent solution paths, score each on correctness/feasibility/ROI, then select and refine the best." Prevents single-path tunnel vision.[3]
- **Self-Critique Loops:** "After planning, critique your blueprint for gaps/assumptions/hallucinations using 5 Whys. Revise until no issues remain." Builds in your RCA patterns.[4]
- **Verbal Sampling:** "Propose 3 equivalent implementations, explain tradeoffs, pick one." Exposes flawed reasoning before commitment.[5]

## Role and Constraint Engineering

Assign dual roles: "@architect: Design bulletproof logic only—no code yet. Then @coder: Implement exactly per architecture." Mirrors your subagent workflows.  Add constraints: "Zero hallucinations—cite Python 2025 best practices by section. No deprecated APIs. Assume adversarial inputs." Aligns with your modernization focus.[6][7][8]

## Verification Gates

Insert checkpoints: "Pause. Human: Does this plan handle [your edge cases]? Approve to proceed." For Claude Code, embed in PreToolUse hooks as idempotent logic audits.  Quantify: "Score plan 1-10 on completeness; below 9=restart." This minimizes maintenance debt per your ROI priority.

## Human

Any other ideas that add value for pre-coding planning prompts?

## Assistant

Looking at your setup and prior work, here are high-leverage additions to pre-coding planning prompts:

## Explicit Assumptions Extraction

Prompt: "List every assumption made about inputs, state, dependencies, and external systems. For each: Is it testable? Documented? What breaks if it's wrong?"  This surfaces hidden preconditions that cause runtime failures. Integrates with your RCA methodology—turns assumptions into test vectors.[1]

## Threat Modeling for Logic

Add: "What are 5 ways this logic could fail in production? For each: detection method, recovery strategy, user impact." This is adjacent to your gap-spotting instinct but targets failure modes before code exists.  Prevents the "works in happy path" trap that wastes review cycles.

## API/Dependency Contract Validation

Before touching code: "List every external API, library function, or state dependency. Verify: current version? Breaking changes since 2024? Deprecated functions?" This prevents hallucinating obsolete APIs—critical for your Python 2025 modernization.  Plug this into your NSE/Intel subagent for live verification.[2]

## Performance Constraints Upfront

Prompt: "Given inputs of [expected scale], what complexity class is acceptable? Will this fit memory/latency budgets? Trace 3 critical paths." Catches O(n²) sorting algorithms before they ship. Aligns with your force-multiplier ROI lens.

## System Integration Diagram

Ask: "Draw the data flow: where does input come from? Where does output go? What state persists? What components touch this function?" Claude outputs ASCII/Mermaid. Visual pre-validation catches architectural mismatches (e.g., "this needs a queue, not synchronous calls").[3]

## Testability-First Design

Prompt: "How will you unit test this? What are unmockable dependencies? Propose design changes to make it testable." Code that's hard to test is usually logic-fragile. This constraint forces cleaner architecture.

## Quantized Success Criteria

Instead of vague "works correctly," specify: "This succeeds if: handles 1M records in <2s AND fails gracefully on corrupt input AND passes [your test suite]." Gives Claude concrete targets instead of guessing.[4]

## Integration with Your Workflow

Chain these into Claude Code's PreToolUse hook as a standardized "logic audit" checklist. Use your parallel subagents: @architect answers assumptions/threats/diagrams, @coder waits for approval. This flips the workflow—validation first, coding second.[5]

The throughline: **every logic error begins as an unspoken assumption or unvalidated constraint.** Pre-coding prompts that force these explicit reduce hallucinations far more than post-hoc reviews.

## Human

Which of these should be pre-code vs post-code?

# Questions


- Did we forget anything?
- What are the key assumptions we're making?
- Are there any dependencies we haven't considered?


# Core Verification Questions


Ask these to confirm the code works correctly and handles real-world scenarios.


- Does the code implement the intended functionality, including edge cases and
  error handling?
- Are there unit tests covering key paths, and do they pass with real data
  patterns?
- Does it align with business logic and project specifications?
- Have we tested with realistic user scenarios and edge cases?
- Does the implementation handle error conditions gracefully?


# Quality and Maintainability Checks


Evaluate structure, readability, and long-term viability.


- Is the code modular, with consistent naming and appropriate comments for
  complex logic?
- Does it follow design patterns, avoid excessive complexity, and integrate
  cleanly with existing architecture?
- Have deprecated APIs or hallucinated functions been removed?
- Is the documentation complete and up-to-date?
- Are there any technical debt items that need addressing?


# Performance and Security Review


Probe for hidden issues in efficiency and safety.


- Are algorithms efficient, memory usage optimized, and performance bottlenecks
  absent?
- Does it handle security concerns like input validation and access controls?
- What predictable failure modes exist under load or adversarial inputs?
- Any predictable issues?
- Have we conducted load testing under expected traffic?
- Are all external inputs properly sanitized and validated?


# Opportunities and Gaps


Build on your questions with targeted follow-ups.


- Beyond gaps, ask: What refactoring improves ROI or reduces maintenance?
- Are there architectural enhancements or missing features for scalability?
- How does this fit your Claude Code workflows or subagent patterns?
- Any gaps or opportunities?
- What future requirements should we anticipate?
- Are there any industry best practices we're not following?

## Assistant

## Pre-Code Questions

These prevent hallucinations and logic errors before the AI writes anything:

**Assumptions & Dependencies (CRITICAL PRE-CODE)**
- What are the key assumptions we're making?
- Are there any dependencies we haven't considered?

These force explicit reasoning about preconditions. Ask before code; code won't fix unstated assumptions.  Integrate into your @architect subagent phase.[1][2]

**Industry Best Practices (PRE-CODE)**
- Are there any industry best practices we're not following?

Ask upfront so the AI builds correct patterns from line 1, not retrofitting later. Aligns with your Python 2025 modernization.[3]

***

## Post-Code Questions

These verify what was generated and improve quality iteratively:

**Functionality & Error Handling (POST-CODE)**
- Does the code implement the intended functionality, including edge cases and error handling?
- Have we tested with realistic user scenarios and edge cases?
- Does the implementation handle error conditions gracefully?

Only meaningful after code exists to inspect.[4][5]

**Testing & Real Data (POST-CODE)**
- Are there unit tests covering key paths, and do they pass with real data patterns?
- Have we conducted load testing under expected traffic?

Post-code verification—no code = no tests to run.[6]

**Quality, Maintainability, Security (POST-CODE)**
- Is the code modular, with consistent naming and appropriate comments for complex logic?
- Does it follow design patterns, avoid excessive complexity, and integrate cleanly with existing architecture?
- Have deprecated APIs or hallucinated functions been removed?
- Is the documentation complete and up-to-date?
- Are algorithms efficient, memory usage optimized, and performance bottlenecks absent?
- Does it handle security concerns like input validation and access controls?
- Are all external inputs properly sanitized and validated?
- Any technical debt items that need addressing?

All require code inspection.[7][4]

***

## Hybrid (Ask Both Phases)

**Predictable Issues & Gaps (PRE-CODE → POST-CODE Loop)**
- Did we forget anything?
- Any predictable issues?
- Any gaps or opportunities?

Ask pre-code as a planning checkpoint ("What gaps exist in the blueprint?"), then ask post-code as validation ("Does the code address those gaps?").  Turns these into iterative gates.

**Specification Alignment (PRE-CODE → POST-CODE Loop)**
- Does it align with business logic and project specifications?

Pre-code: "Is our plan spec-compliant?" Post-code: "Does implementation match the approved plan?"[7]

**ROI & Architecture (POST-CODE)**
- What refactoring improves ROI or reduces maintenance?
- Are there architectural enhancements or missing features for scalability?
- How does this fit your Claude Code workflows or subagent patterns?
- What future requirements should we anticipate?

Post-code only—can't optimize what doesn't exist yet. But inform pre-code planning with these goals.

***

## Optimized Workflow

```
PRE-CODE PHASE
├─ What are the key assumptions we're making?
├─ Are there any dependencies we haven't considered?
├─ Any predictable issues? (planning checkpoint)
└─ Are there any industry best practices we're not following?
      ↓
[AI generates code]
      ↓
POST-CODE PHASE
├─ Core: Does the code implement the intended functionality + error handling?
├─ Testing: Unit tests passing on real data patterns?
├─ Quality: Modular? Design patterns? Deprecated APIs removed?
├─ Security: Input validation? Load testing?
├─ Gaps: Any gaps or opportunities in the implementation?
└─ ROI: Refactoring opportunities? Future scalability?
```

This matches your Claude Code subagent pattern: @architect validates blueprint, @coder implements, @reviewer audits.[2][8]

## Human

Can you show me an optimal post-code prompt?

## Assistant

## Optimal Post-Code Review Prompt

```
You are a rigorous code auditor. Review the code below for production readiness.

OUTPUT FORMAT: For each section, provide a numbered list. 
Use inline code snippets. Be specific—cite line numbers.
Fail fast: Stop at first critical issue and explain why it blocks deployment.

---

SECTION 1: FUNCTIONALITY & ERROR HANDLING
□ Does the code implement the stated requirements exactly?
□ Trace 3 realistic inputs through the logic—do they produce correct outputs?
□ List every error condition: network failure, invalid input, timeout, 
  out-of-memory, concurrent access. For each: is it caught? How?
□ What happens if inputs are at boundary limits (empty, max-size, null)?
  Provide a specific example that might fail.
□ Are there silent failures (logic errors that don't throw)? 
  Cite the code.

---

SECTION 2: TESTING COVERAGE
□ What are the 5 most critical code paths (happy path + 4 failure modes)?
□ Do unit tests exist for each? Do they pass with real data patterns 
  from your environment?
□ What input patterns are NOT tested? (e.g., Unicode, concurrent requests, 
  very large payloads)
□ Load test result: Does this handle expected peak traffic? 
  Cite latency/memory under load.

---

SECTION 3: QUALITY & MAINTAINABILITY
□ Is every function ≤30 lines? Name clarity score 1-10?
□ Do complex sections have comments explaining *why*, not *what*?
□ Dependency list: external APIs, libraries, DB calls. 
  Version constraints? Breaking changes since 2024?
□ Any deprecated APIs used? List them.
□ Circular dependencies, tight coupling, or code smell? Cite it.

---

SECTION 4: SECURITY & RESILIENCE
□ Input validation: does every untrusted input get sanitized? 
  Trace one example: raw input → validation → use.
□ Authentication/authorization: are checks present where needed?
□ What happens under adversarial input? (SQLi attempt, XSS payload, 
  oversized request, malformed JSON) Test one.
□ External service calls: retries, timeouts, circuit breaker? 
  What's the failure mode?
□ Secrets: any hardcoded credentials, API keys, or tokens? 
  Should use env vars/secrets manager.

---

SECTION 5: PERFORMANCE BOTTLENECKS
□ Algorithm complexity: What is O() for inputs of 1K, 1M, 1B records?
□ Memory usage: Does it load entire datasets into RAM? 
  (Suggest streaming if >100MB patterns exist.)
□ Database queries: N+1 loops? Missing indices? Unoptimized joins?
□ Network calls: Parallel-able requests batched? 
  Or sequential waterfall?
□ Caching: Is repeated computation cached, or recalculated every call?

---

SECTION 6: GAPS & OPPORTUNITIES
□ Does this integrate cleanly into existing architecture? 
  Any misalignment?
□ Missing logging/observability: How would you debug this in production 
  without source code?
□ Future requirements: Does this scale to 10x load? 2-year roadmap 
  compatibility?
□ Refactoring ROI: If you spent 4 hours, what would improve most? 
  Score by impact/effort.

---

CRITICAL GATE: 
If ANY item in Sections 1-4 is unresolved, list blockers and 
do NOT proceed to production. Otherwise, summarize: 
"APPROVED for [environment]" or "NEEDS FIXES: [list]".
```

***

## Why This Prompt Works

**Specificity:** Forces line-number citations and concrete examples instead of generic feedback.  "Does error handling exist?" becomes "Trace network failure path—where's the retry logic?"[1]

**Structure:** Sections mirror real code review priorities—functionality first (correctness), then testing (confidence), then quality (maintainability), then security (risk), then performance (ROI).[2][3][4]

**Traceability:** "Trace 3 inputs" and "Cite line numbers" prevent hallucinations. AI must reference actual code, catching gaps. Aligns with your anti-deception focus.

**Production Focus:** "Fail fast" and "CRITICAL GATE" force prioritization. Your force-multiplier lens means: catch blockers immediately, don't waste cycles on polish.

**Claude Code Integration:** Pipe output through @auditor subagent in parallel with @coder.  Use PreToolUse hook to auto-run this before deployment.[5][6]

***

## Optional Customizations

**For Security-Critical Code:**
Add to Section 4: "Run static analysis (e.g., bandit, semgrep). Cite findings. Threat model: 3 attack vectors, mitigation per each."

**For ML/Data Code:**
Add between Sections 2-3: "Data validation: type checking? Range bounds? Missing values? Drift detection on production data?"

**For Performance-Critical Code:**
Expand Section 5: "Profile with [tool]. Hotspots? Allocations per call? Cache hit rates?"

**For Your Video Content Routing (UVIR):**
Add to Section 6: "How does this route content through specialized prompts? Latency impact? Fallback if classifier fails?"
