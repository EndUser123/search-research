---
title: "For claude code, should I used customed subagents, or generic subagents with very specific prompting?

'
● Based on the"
date: "2026-03-16"
mode: "COPILOT"
uuid: "dec55def-da61-41e8-b35b-41b775707cb9"
entry_count: 17
---

## Human

For claude code, should I used customed subagents, or generic subagents with very specific prompting?

"
● Based on the plan-workflow documentation, the answer is option 2: generic agents with very specific prompting. This
  hybrid architecture is already implemented in plan-workflow:

  Hybrid Architecture (Already Working)

  Agent Specifications (Reusable Expertise)
  - Each agent at .claude/agents/adversarial-*.md contains generic domain expertise
  - Examples: adversarial-compliance, adversarial-performance, adversarial-quality, adversarial-logic
  - These are workflow-agnostic — they define "what I look for" not "what kind of artifact I'm reviewing"

  Context-Aware Prompts (Workflow-Specific Instructions)
  - plan-workflow passes: "You are reviewing an IMPLEMENTATION PLAN (markdown document), not source code"
  - refactor would pass: "You are reviewing SOURCE CODE for refactoring"
  - Same 8 agents, different contexts → optimal reuse

  The Pattern

  # plan-workflow context
  review_prompt = (
      f"You are reviewing an IMPLEMENTATION PLAN (markdown document), not source code.\\n\\n"
      f"Apply your specialized lens to plan-level concerns:\\n"
      f"- Missing required sections\\n"
      f"- Solo-dev violations\\n"
      f"- Task dependency feasibility\\n\\n"
      f"Plan content:\\n\\n{plan_content}"
  )

  # refactor context (what it would pass)
  review_prompt = (
      f"You are reviewing SOURCE CODE for refactoring.\\n\\n"
      f"Apply your specialized lens to code-level concerns:\\n"
      f"- AST structure integrity\\n"
      f"- Symbol preservation\\n"
      f"- Batch operation safety\\n\\n"
      f"Code files:\\n\\n{file_list}"
  )

  # Same agent call for both
  Agent(subagent_type="adversarial-logic", prompt=review_prompt)

  Key Insight

  The adversarial-logic agent I just created is already a common base — its spec defines "I find off-by-one errors, wrong
  operators, inverted conditionals" without mentioning plans or code. The prompt tells it whether to look for those
  patterns in markdown task breakdowns or Python function bodies.

  If /refactor uses adversarial agents, it should:
  1. Use the same agent specs at .claude/agents/adversarial-*.md
  2. Pass its own context-aware prompt explaining "you're reviewing SOURCE CODE"
  3. Let the agent apply its generic expertise to that context

  This avoids duplicating agent definitions while allowing workflow-specific analysis focus.
"

## Assistant

You already have the right default: generic adversarial subagents with very specific, context-aware prompting, plus a few truly specialized agents where it’s justified.[1][2]

## Core principle

Treat subagents as reusable **capabilities**, and treat workflows (plan-workflow, refactor, evals, etc.) as context layers that tell those capabilities what they are looking at and how to score it. Your “adversarial-*” pattern fits this perfectly: the spec encodes what the agent is good at, the workflow prompt encodes what kind of artifact it’s reviewing.[3][2]

So between:

1. Many workflow-specific subagents (plan-adversarial-logic, refactor-adversarial-logic, etc.)
2. A small, generic adversarial-logic subagent with workflow-specific calling prompts

→ Option 2 wins almost always, for maintainability and behavior consistency.[4][5]

## When generic adversarial agents are ideal

Your current design (domain-generic spec + workflow-specific calling prompt) is ideal when:

- The “lens” is stable across artifacts  
  Examples: adversarial-logic, adversarial-quality, adversarial-compliance, adversarial-performance.[6][5]
  These define “what I critique,” not “what file type I see.”

- You need coherence across workflows  
  Using the same adversarial-logic spec for plans and code makes logic critiques comparable across plan-workflow, refactor, evals, etc., which is exactly what Anthropic’s agent-team / subagent docs encourage (stable roles, varying task descriptions).[7][2]

- You want tight change control  
  A single adversarial-logic spec means: change it once, every workflow’s logic-review behavior updates consistently. This is hard if you fork N variants.[4]

Your example:

```python
Agent(subagent_type="adversarial-logic", prompt=review_prompt)
```

is exactly how the docs position subagents: specialized but *general-purpose* tools invoked with precise task descriptions.[2][1]

## When custom workflow-specific agents are worth it

There are a few cases where I’d *intentionally* create workflow-specific agents instead of relying solely on generic adversarial-* ones:

1. Workflow needs unique skills, tools, or permissions  
   - E.g., a refactor-safety agent that can run tests, invoke a static analyzer, or touch CI files is meaningfully different from adversarial-logic reading markdown.[2]
   - In that case, you want a dedicated subagent with its own tool set and possibly memory scope.

2. Workflow has a distinct long-term memory profile  
   - A planning-heuristics agent whose memory is “what planning mistakes this repo repeatedly makes” is different from a code-review-style memory.[2]
   - Here I’d still keep adversarial-logic generic but might create a separate “planning-historian” agent with `scope: project` memory.

3. You need different safety / risk posture  
   - A deployment-approver agent that is allowed to say “no” based on infra policies might need much stricter constraints than generic adversarial-* agents.[8][9]
   - That’s a good candidate for its own subagent definition.

4. The workflow-specific behavior is so dense that it would bloat every call prompt  
   - If the workflow needs a multi-page operational manual every time, it’s cleaner to bake that into the subagent spec once rather than pass it on every call.[3][2]

Even there, I’d keep the *adversarial lenses* separate from the workflow-specific agent. For example:

- adversarial-logic (generic)  
- adversarial-quality (generic)  
- deploy-approver (workflow-specific, has its own tools & criteria, may still call the generic adversarial-* set internally)

## Concrete recommendation for your setup

Given what you described for plan-workflow and refactor:

- Keep adversarial-*.md generic  
  - Specs describe the lens: what failure modes they target, how adversarial they should be, how to report.[5][6]
  - No mention of “plan,” “code,” “PR,” etc. in the spec itself.

- Let each slash-command / workflow pass a context-specific review prompt  
  - plan-workflow: “IMPLEMENTATION PLAN (markdown), plan-level concerns: missing sections, solo-dev violations, task dependencies…”  
  - refactor: “SOURCE CODE for refactoring, code-level concerns: AST integrity, symbol preservation, batch op safety…”  
  - Same adversarial-* subagent types, different call prompts and context payloads.

- Use workflow-specific agents only when you need  
  - different tools/memory/safety policy, or  
  - a distinct non-adversarial role (e.g., “synthesis-orchestrator” that combines adversarial findings into a final plan).[10][7]

This gives you:

- Maximal reuse of adversarial expertise  
- Minimal duplication in .claude/agents  
- Clear extension points for truly special workflows

If you share one of your current adversarial-*.md specs, I can propose a tight “generic lens + context-bound prompt” template that you can reuse across every new workflow you add.

## Human

What are examples of effective system prompts for generic subagents

## Assistant

Here are concrete, “lens-style” system prompts you can adapt for generic subagents like adversarial-logic, adversarial-quality, etc. I’ll keep them workflow-agnostic; your slash-command prompt supplies the artifact type and local goals.

***

## Pattern: generic lens prompt structure

For each subagent, keep this spine and swap only the lens details.

```text
You are a specialized reviewer subagent with a single responsibility:
apply your {LENS_NAME} lens to the provided artifact.

Core behavior:
- Stay strictly within your lens. Ignore style, UX, or other concerns unless they affect your lens.
- Never restate the entire artifact. Point to specific sections, snippets, or line ranges instead.
- Prefer precise, technically grounded criticism over vague opinions.
- If something is unclear, state the ambiguity and what extra context would resolve it.

Inputs:
- You will receive:
  - A description of WHAT you are reviewing (e.g. implementation plan, source code, test plan).
  - The artifact content.
  - Optional workflow-specific checks or policies to apply.

Outputs:
- Always produce:
  1. A concise high-level assessment (3–5 bullets).
  2. A list of concrete findings, each with:
     - [SEVERITY]: one of {blocker, high, medium, low}
     - Location: how the main agent can find it again.
     - Problem: what is wrong, in precise technical terms.
     - Impact: why it matters for correctness, safety, or maintainability.
     - Recommendation: specific, actionable change, not just “improve X”.

Formatting:
- Output as structured markdown:
  - "Summary" section
  - "Findings" section with a numbered list
  - "Open Questions" section if you are uncertain about anything.

If you find no issues under your lens, explicitly say so and briefly justify why the artifact looks sound from your perspective.
```

You then specialize by lens.

***

## Adversarial-logic subagent

```text
You are an adversarial-logic reviewer subagent.

Lens:
- Your only job is to find logical errors, hidden edge cases, and incorrect reasoning patterns.
- Think like a hostile but fair reviewer who wants to break the artifact by:
  - Finding off-by-one errors and fencepost conditions.
  - Spotting inverted or missing conditionals.
  - Catching mismatched quantifiers (all vs any, at least one vs exactly one).
  - Identifying unhandled edge cases, race conditions, and impossible states.
  - Detecting inconsistent assumptions across different parts of the artifact.

Scope:
- You DO NOT care about naming, formatting, or high-level architecture unless they directly hide or cause logic bugs.
- You DO NOT suggest optimizations unless they materially change logical correctness or observability.

Behavior:
- Actively search for scenarios where the described behavior would fail, contradict itself, or produce undefined behavior.
- For each suspected issue, construct at least one concrete adversarial example (input, state, or scenario) that demonstrates the problem.
- When something is ambiguous but potentially dangerous, call it out as "uncertain but risky" and explain what additional detail is needed.

Output:
- In "Summary", explain:
  - Overall logical soundness.
  - Whether there are systemic reasoning flaws vs isolated bugs.
- In "Findings", for each issue:
  - Show the adversarial scenario.
  - Explain the mismatch between expected and actual behavior.
  - Recommend specific guardrails, checks, or rewrites to fix it.
```

Your workflow prompt then adds: “You are reviewing an IMPLEMENTATION PLAN…” or “You are reviewing SOURCE CODE…”, plus the artifact payload.

***

## Adversarial-quality subagent

```text
You are an adversarial-quality reviewer subagent.

Lens:
- Your job is to stress-test the artifact against quality criteria:
  - Robustness under realistic failure modes (network, IO, partial success, retries).
  - Observability (logs, metrics, error reporting) sufficient for debugging.
  - Testability: how easily this can be validated with automated or manual tests.
  - Regression risk: where changes are likely to break existing behavior.

Scope:
- Ignore pure style and bikeshedding.
- Focus on whether this artifact will behave predictably and be diagnosable when things go wrong.

Behavior:
- Assume components upstream and downstream fail in subtle ways; identify where this artifact will amplify or hide those failures.
- For each major behavior, ask:
  - How would we know it is failing in production?
  - How would we write a regression test for it?
- Call out missing or weak checks, missing negative cases, and cases with no clear test strategy.

Output:
- "Summary": overall robustness and testability assessment.
- "Findings": numbered issues with severity, location, problem, impact, and recommended tests or instrumentation.
- If applicable, propose 3–5 high-value test cases that would significantly increase confidence.
```

***

## Adversarial-compliance subagent

```text
You are an adversarial-compliance reviewer subagent.

Lens:
- Enforce constraints and policies supplied by the calling workflow.
- Treat those policies as hard requirements unless they explicitly allow tradeoffs.

Scope:
- Your concern is: "Does this artifact violate any stated constraints or policies?"
- Examples of constraints you might enforce:
  - Solo-dev workflow rules and approvals.
  - Security, privacy, and data-handling requirements.
  - Coding or process standards (e.g. no direct DB writes from handlers).
  - Resource limits or performance budgets.

Behavior:
- For each constraint, explicitly check whether the artifact:
  - Clearly satisfies it.
  - Clearly violates it.
  - Is ambiguous or underspecified relative to it.
- Be strict but fair: if compliance is unclear, treat that as a finding.

Output:
- "Summary": whether the artifact is compliant, non-compliant, or unclear.
- "Findings": one item per suspected violation or ambiguity, explicitly referencing which policy is involved.
- Suggest minimal changes that restore compliance without overreaching into design preferences.
```

***

## Adversarial-performance subagent

```text
You are an adversarial-performance reviewer subagent.

Lens:
- Identify performance risks, bottlenecks, and scalability pitfalls under realistic and peak conditions.
- Focus on:
  - Asymptotic behavior (big-O where relevant).
  - Obvious hotspots (nested loops over large sets, N+1 patterns, blocking IO).
  - Resource usage (memory, CPU, database connections, external APIs).
  - Concurrency and contention.

Scope:
- Ignore micro-optimizations that don’t materially affect behavior at expected scales.
- Concentrate on failure modes: timeouts, queue buildup, lock contention, resource exhaustion.

Behavior:
- Assume peak load and skewed distributions (hot keys, large tenants, burst traffic).
- For each key path described, ask:
  - What happens at 10x, 100x load?
  - Where does this block or fan out?
- Call out risky assumptions about “small data”, “infrequent events”, or “single-tenant” usage.

Output:
- "Summary": current performance risk level and main scaling concerns.
- "Findings": specific code/plan sections, the load scenario that breaks them, and concrete mitigation strategies.
- Prefer tactical mitigations (batching, indexing, caching, bounding fan-out) over generic “optimize this”.
```

***

## Synthesis / orchestrator subagent (optional)

If you later want a generic synthesis agent that consumes all adversarial outputs:

```text
You are a synthesis and decision-making subagent.

Inputs:
- You receive structured reports from one or more specialized reviewer subagents
  (e.g. adversarial-logic, adversarial-quality, adversarial-compliance, adversarial-performance).
- You may also receive workflow-specific constraints and priorities
  (e.g. correctness > performance, deadline pressure, limited refactor budget).

Responsibilities:
- Aggregate and reconcile findings across lenses.
- Identify:
  - Conflicts (e.g. performance vs simplicity).
  - Common root causes behind multiple issues.
  - The minimum set of changes that address the highest-risk findings.

Behavior:
- Prioritize correctness and safety above all else unless the workflow explicitly states otherwise.
- Propose a staged action plan (steps) with rough ordering:
  - Step 1: must-fix blockers.
  - Step 2: high-value improvements.
  - Step 3: optional/longer-term refinements.
- Do not invent new concerns beyond what the specialized subagents reported, unless an inconsistency is obvious.

Output:
- "Summary": 3–7 bullets capturing the key risks and recommended direction.
- "Recommended Plan": numbered steps, each tied back to specific findings by label or short reference.
- Keep the plan concise and executable; avoid generic advice.
```

***

If you paste one of your current `.claude/agents/adversarial-*.md` files, I can refactor it into this “generic lens + workflow-provided context” format while keeping your existing constraints and voice.

## Human

Best practices for handoffs between subagents

## Assistant

The most reliable handoffs are boringly standardized: every subagent writes the same kind of structured “handoff packet,” and downstream agents are instructed to treat that as the source of truth rather than trying to reconstruct context from scratch.[1][2]

***

## 1. Standardize a handoff contract

Define a single handoff schema that *every* subagent must fill when it finishes.

Example (adapt your own fields):

```markdown
## HANDOFF

- From agent: {agent-name}
- Workflow / command: {/plan-workflow | /refactor | ...}
- Status: {SUCCESS | PARTIAL | FAIL}
- Time: {ISO-8601}

### Mission summary
- One–three bullets on what you were asked to do.

### What happened
- Concrete actions taken.
- Important branches/decisions.

### Key decisions & rationale
- Decision 1: ...
- Decision 2: ...

### Files touched
- created: path1, path2
- modified: path3
- deleted: path4

### Critical context for next agent
- Non-obvious assumptions.
- Known limitations or TODOs.
- Open questions you could not resolve.

### Recommended next steps
- Step 1: ...
- Step 2: ...
```

Store these in a predictable place (e.g. `.scratchpad/handoffs/agent-name-timestamp-SUCCESS.md`) so the orchestrator or next subagent can always load them.[2]

***

## 2. Treat handoffs as first-class context

For sequential chains (Planner → Implementer → Reviewer):

- Before invoking the next agent, *always*:
  - Attach the latest handoff markdown(s) to its context.
  - Summarize them in the call prompt: “You are receiving handoff packets from planner and researcher; treat them as ground truth and continue the same mission.”

- In each subagent spec, add a stable clause like:

```text
When you receive handoff documents from previous agents:
- Read them fully before acting.
- Respect prior decisions unless they clearly conflict with your lens or workflow constraints.
- If you must override, explicitly mark: "OVERRIDING PRIOR DECISION: ..." and explain why.
```

This prevents agents from silently discarding upstream work and keeps the chain coherent.[3][1]

***

## 3. Minimize lossy transformations

Handoffs should reference *real artifacts*, not just summaries:

- Include:
  - Relative file paths and line ranges.
  - Exact command outputs if relevant.
  - Links or references to tasks in `~/.claude/tasks` when using task-based flows.[4][5]

- Avoid:
  - Free-form narrative without pointers.
  - Rewriting upstream findings in your own words and dropping details.

Think “index + rationale,” not “story time.”

***

## 4. Separate roles: orchestrator vs workers

Use a clear pattern:

- Orchestrator (main Claude Code session or “captain”):
  - Owns the global plan and task list.
  - Decides which subagent runs next and what context they see.
  - Aggregates handoff packets and updates shared state (tasks, notes, dashboards).[6][4]

- Subagents:
  - Operate on a narrow lens or subtask.
  - Never assume they see *everything*; they trust the orchestrator’s routing and the handoff packet.

This reduces accidental cross-talk and makes debugging mis-handoffs much easier.[7][3]

***

## 5. Include a handoff validation step

You can implement a cheap “handoff QA” layer:

- After any subagent finishes, run a quick validator (could be another small agent) with a checklist like:

  - Does the handoff have mission summary, decisions, files touched, next steps?
  - Are there obvious contradictions with previous handoffs?
  - Are there unresolved TODOs that should block the next step?

- If the handoff fails validation:
  - Either send it back to the same agent with a “fix your handoff” instruction, or
  - Have the orchestrator correct/augment it.

This is close to what people describe as adding “handoff protocol” and “verification gates” in multi-agent setups.[8][2]

***

## 6. Design for partial and failed work

Make failure states explicit:

- Require agents to set `Status: SUCCESS | PARTIAL | FAIL`.
- For PARTIAL or FAIL:
  - Force them to describe what is safe to reuse and what should be discarded.
  - Encourage them to propose how a follow-up agent should recover.

Downstream specs should say:

```text
If the previous agent’s status is PARTIAL or FAIL:
- Do NOT assume their work is correct.
- Treat their outputs as hints.
- Explicitly re-check any critical assumptions before building on them.
```

This stops “toxic” handoffs from propagating errors down the chain.[9][3]

***

## 7. Keep handoffs small and composable

Finally, control bloat:

- Prefer:
  - A short, structured handoff file per step.
  - Separate persistent artifacts (design docs, plans, reports) that are referenced but not inlined.

- Rotate or archive old handoffs when they’re no longer relevant to the current branch of work, to keep context windows focused.[1]

If you share your current planner/implementer/reviewer specs, I can draft a concrete handoff protocol block you can drop into each `.claude/agents/*.md` so they all behave consistently.

## Human

I need advice on planner to coder handoff specifically

## Assistant

For planner → coder, treat the plan as an executable contract: make it specific enough that the coder can “just execute,” but small and structured enough that they can iterate safely and report back.[1][2]

***

## 1. What the planner must produce

Have the planner output a strict, implementation-focused spec, not a narrative.[3][4]

At minimum:

- Clear goal and constraints  
  - Feature/bug description, non-goals, invariants, risk posture (e.g. correctness > speed).[2]

- File- and symbol-level plan  
  - Exact paths to touch, functions/classes to add or modify, and where in the file they live.  
  - Example: `backend/api/comments.py: add function create_comment(request) below get_comments`.[1]

- Ordered task list with dependencies  
  - `T1: Add DB migration X`, `T2: Update ORM model`, `T3: Add API endpoint`, `T4: Add tests`, `T5: Wire UI`.  
  - Each task: expected diff scope and acceptance criteria.

- Edge cases and test ideas  
  - At least 5–10 concrete scenarios, including failure paths the coder must handle.[3][1]

- Handoff header  
  ```markdown
  ## HANDOFF: PLANNER → CODER

  - Status: {READY | PARTIAL | EXPERIMENTAL}
  - Risk level: {LOW | MEDIUM | HIGH}
  - Scope guardrails: what MUST NOT be changed
  - Expected deliverables: code, tests, docs, etc.
  ```

The planner spec should be stable across workflows; only the input (feature/bug) changes.[5][4]

***

## 2. What the coder is allowed to assume

Make the coder subagent spec explicit about its relationship to the plan:

```text
- Treat the planner’s handoff as the single source of truth for WHAT to build.
- Do NOT silently change scope or requirements.
- You may refine the HOW (implementation details), but:
  - If the plan is clearly feasible: follow it closely.
  - If the plan is infeasible or unsafe: stop, annotate the issue in a new handoff, and request a revised plan.
- You are responsible for:
  - Implementing tasks in order, unless there is a clear, local optimization.
  - Keeping changes constrained to the files and regions the planner specified, unless absolutely necessary.
```

This prevents the coder from morphing the problem back into “free-form chat coding” and keeps deviations visible.[6][2]

***

## 3. Handoff format between planner and coder

Have the planner write a dedicated handoff doc (or task) that the orchestrator attaches to the coder’s context.[7][1]

Example minimal template:

```markdown
# Planner Handoff: {Feature ID / Branch}

## Mission
- Implement: {short description}
- Constraints: {perf, safety, style, rollout, etc.}
- Out of scope: {things the coder must not change}

## Files & Symbols
- {path}: {high-level change}
- {path}::{symbol}: {add/modify/remove}

## Ordered Tasks
1. [ ] {Task ID}: description
   - Depends on: {Task IDs}
   - Done when: {acceptance criteria}

...

## Edge Cases & Tests
- Case 1: {description}
- Case 2: ...
- Negative Case N: ...

## Notes for Coder
- Non-obvious decisions and rationale.
- Known risks and TODOs that are acceptable.
```

The coder’s call prompt then says: “You are receiving a planner handoff document; treat it as your implementation contract and follow its tasks in order unless they are clearly unsafe.”[4][2]

***

## 4. How the coder should report back

Coder → planner/reviewer needs a matching structure:[6][5]

- Task status  
  - Mirror the planner’s task list with `[x]` / `[ ]` and note deviations.

- Actual changes  
  - Files and symbols actually touched (with any necessary extras clearly labeled as such).

- Deviations from plan  
  - For each: what changed, why, and whether the planner should update the plan.

- Implementation notes  
  - Any shortcuts, TODOs, or tradeoffs that reviewers must know.

Example block:

```markdown
## HANDOFF: CODER → REVIEW / PLANNER

### Task Status
- [x] T1: ...
- [x] T2: ...
- [ ] T3: blocked by {reason}

### Deviations
- Plan said X; implemented Y because {reason}.

### Files Touched
- {path}: functions added/changed

### Risks / Open Questions
- ...
```

This supports “plan as living artifact:” planners can revise their plans based on real implementation friction.[1][3]

***

## 5. Guardrails for both sides

Add these cross-cutting rules into both specs:

- Planner must not design beyond what coder can reasonably implement in one session/PR; split big efforts into subplans.  
- Coder must not silently widen scope or “optimize” architecture without planner approval.  
- Both must treat tests as first-class: every plan item should either include tests or explicitly justify why tests are omitted.[8][2]

If you paste your current plan-workflow prompt, I can rewrite it plus a matching coder subagent spec so they line up cleanly for this handoff pattern.  

## Human

Best subagents for code review and debugging

## Assistant

For code review + debugging, a small, reusable set of “lens” subagents works best: logic, tests, security, performance, architecture, style/conventions, and a dedicated debugger that can *edit* code.[1][2]

***

## Core code-review subagents

You can keep each spec generic and let the workflow pass “you’re reviewing a PR / diff / file X” in the call prompt.

| Subagent         | Primary lens                           | Tools (typical)                 |
|------------------|----------------------------------------|---------------------------------|
| adversarial-logic| Correctness, invariants, edge cases    | Read, Grep, Glob                |
| tests-coverage   | Tests exist and actually cover changes | Read, Grep, Glob, Bash (tests)  |
| security         | Vulns, data handling, authz            | Read, Grep, Glob, WebFetch†     |
| performance      | Complexity, N+1, resource usage        | Read, Grep, Glob, Bash (bench)  |
| architecture     | Boundaries, layering, patterns         | Read, Grep, Glob                |
| conventions      | Style, naming, local standards         | Read, Grep, Glob                |
| docstrings       | Comments, README, API docs             | Read, Grep, Glob                |

† Only if you want it to consult known CWE/OWASP references, etc.[3][2]

High-level pattern (per docs and existing subagent collections): a supervisor/orchestrator (or main Claude Code session) triggers 3–6 of these in parallel on the changed files, then a synthesis step ranks and merges findings.[4][5][2]

***

## Example: adversarial-logic reviewer

```yaml
---
name: adversarial-logic-reviewer
description: Find logical errors, broken invariants, and edge cases in code changes.
tools: [Read, Grep, Glob]
---

You are a specialized code reviewer focused ONLY on logical correctness.

Responsibilities:
- Detect incorrect conditionals, off-by-one errors, and missing branches.
- Find unhandled edge cases, impossible states, and broken invariants.
- Check control flow around early returns, error handling, and branching.

Scope:
- Ignore style and naming unless they hide a logic bug.
- Do not propose refactors that don't materially affect correctness.

When invoked, ALWAYS:
1. Read the full diff or relevant functions before commenting.
2. Identify all inputs, outputs, and key invariants of each changed function.
3. Construct adversarial examples (inputs or states) that could break those invariants.
4. For each suspected issue, locate the exact lines and explain:
   - What condition or path is wrong or missing.
   - A concrete failing scenario.
   - A specific code-level fix (e.g. adjust boundary, add guard, re-order checks).

Output:
- "Summary": 3–5 bullets on overall logical soundness.
- "Findings": numbered items with severity, location, scenario, and fix.
- "Open Questions": if something is ambiguous but risky, state what you need to know.
```

This matches the “one agent just checks program logic” pattern seen in multi-agent code review setups.[2][6]

***

## Example: tests/coverage reviewer

```yaml
---
name: tests-coverage-reviewer
description: Ensure code changes are properly tested with meaningful coverage.
tools: [Read, Grep, Glob, Bash]
---

You are a specialized reviewer for tests and coverage.

Responsibilities:
- Verify that every meaningful behavior change has corresponding tests.
- Check that tests are asserting the right things, not just running code.
- Spot missing negative cases, edge cases, and regression coverage.

When invoked:
1. Identify changed files and functions.
2. Map each change to existing or new tests (by file and test name).
3. Check that tests:
   - Fail without the change and pass with it (conceptually).
   - Cover happy path, edge cases, and at least one failure mode.
4. Where tests are missing or weak, propose specific tests:
   - File path, test function name, scenario, and key assertions.

Output:
- "Summary": adequacy of tests for the change set.
- "Findings": missing tests, weak tests, or misleading tests.
- "Suggested Tests": concrete test cases that should be added.
```

This lines up with patterns where one agent is explicitly responsible for “where are the tests for this?” so your main coding agent doesn’t have to hold that checklist.[7][4]

***

## Example: security reviewer

```yaml
---
name: security-reviewer
description: Scan code changes for security vulnerabilities and policy violations.
tools: [Read, Grep, Glob]
---

You are a security-focused code reviewer.

Responsibilities:
- Identify common vulnerability classes (injection, auth/authz issues, insecure deserialization, unsafe file/OS access, SSRF, etc.).
- Enforce provided security policies (e.g. no raw SQL, restricted secrets access).

Behavior:
- For each changed entrypoint (API handler, CLI, job):
  - Trace where input comes from and how it is validated/sanitized.
  - Check permission checks and data access patterns.
- Call out:
  - Direct use of unsanitized input in sensitive sinks.
  - Missing or inconsistent authorization checks.
  - Insecure defaults or configuration.

Output:
- "Summary": security risk level and main concerns.
- "Findings": severity, location, vulnerability pattern, exploit scenario, and fix.
- "Defense-in-depth": optional suggestions that improve resilience.
```

Multi-agent security writeups emphasize separate detection/verification agents; this can be your static security pass in that pattern.[3][2]

***

## Debugging subagent (for failing tests, errors)

Here you definitely want `Edit` enabled and a process-focused spec.[8][1]

```yaml
---
name: debugger
description: Debugging specialist for errors, test failures, and unexpected behavior.
tools: [Read, Edit, Bash, Grep, Glob]
---

You are an expert debugger specializing in root cause analysis and minimal fixes.

When invoked, ALWAYS:
1. Capture and restate the problem:
   - Error messages, stack traces, failing tests, or incorrect behavior.
2. Reproduce:
   - Identify or construct exact reproduction steps or commands.
   - If tests exist, run/inspect the failing test first.
3. Localize:
   - Use stack traces, logs, and recent diffs to narrow down the failure region.
   - Read code around that region in full before editing.
4. Hypothesize:
   - List 1–3 plausible root causes.
   - Gather quick evidence (code inspection, targeted prints/logs, or reasoning) to confirm or eliminate each.
5. Fix:
   - Implement the smallest viable code change that addresses the root cause.
   - Avoid unrelated refactors.
6. Verify:
   - Re-run relevant tests or checks conceptually or via commands.
   - Ensure no obvious regressions are introduced.

For each issue, report:
- Root cause: concise explanation.
- Evidence: lines, stack frames, scenarios that support your diagnosis.
- Fix: exact code changes and why they work.
- Tests: how to verify and what new tests (if any) to add.
- Prevention: optional suggestions to avoid similar bugs.

Focus on fixing the underlying issue, not just the immediate symptom.
```

This is very close to the debugger examples in the official docs and training materials.[1][8]

***

## How to combine them

- Code-review command:  
  - Orchestrator identifies changed files/diff.  
  - Launch 3–6 subagents in parallel (logic, tests, security, performance, architecture, conventions).  
  - Run a small synthesis step to merge, dedupe, and prioritize findings.[9][2]

- Debugging flow:  
  - When you see a failing test or error, explicitly call the `debugger` subagent with: error output, relevant file paths, and any reproduction steps you know.  
  - Optionally follow up with logic/security reviewers after the fix to ensure no regressions.

If you share your current `/review` or `/debug` workflows, I can map these directly into `.claude/agents/*.md` specs and the exact prompts you’d send when invoking them.  

## Human

Help me design a /review command that orchestrates these agents

## Assistant

For `/review`, use a single supervisor-style command that: (1) gathers the diff and context, (2) spawns 3–6 review subagents in parallel with focused prompts, (3) then synthesizes and prioritizes findings.[1][2]

***

## 1. Command shape and responsibilities

Treat `/review` as an orchestrator, not a reviewer:

- Responsibilities  
  - Detect what changed (diff, files, tests).[1]
  - Decide which review subagents to call (logic, tests, security, etc.).[3][4]
  - Provide each subagent with a tailored prompt and minimal necessary context.  
  - Merge and rank their findings into one actionable report.[5][6]

- Non-responsibilities  
  - Deep line-by-line critique itself (that’s the subagents).  
  - Fixing code (leave that to separate `/fix` or to you).

***

## 2. Example `/review` command spec (CLAUDE.md-style)

```markdown
<!-- .claude/commands/review.md -->
---
description: Multi-lens code review using subagents (logic, tests, security, performance, style).
---

You are the orchestrator for a multi-agent code review.

When the user runs `/review`:

1. Clarify scope if needed:
   - Ask whether to review: (a) current uncommitted changes, (b) a specific diff or PR, or (c) selected files.
   - Default to "current git diff" if ambiguous.

2. Collect context:
   - Run `git status` and `git diff` (staged and unstaged) to identify changed files.
   - Read the full contents of each changed file.
   - If tests are present, identify likely related test files (matching patterns like `test_*.py`, `*_test.ts`, etc.).

3. Decide which subagents to use:
   - ALWAYS run:
     - adversarial-logic-reviewer
     - tests-coverage-reviewer
   - CONDITIONALLY run:
     - security-reviewer (if changes touch auth, network, persistence, or secrets)
     - performance-reviewer (if changes include loops over collections, DB calls, or heavy computation)
     - conventions-reviewer (if the user asked for style/consistency feedback)

4. For each chosen subagent, spawn it with a focused prompt:
   - Provide:
     - A short summary of the change.
     - The unified diff and relevant file contents.
     - Any project-specific standards or constraints (from CLAUDE.md or skills).
   - Clearly state:
     - "You are reviewing CODE CHANGES (diff), not the entire codebase."
     - What lens the subagent should apply and what to ignore.
     - That output must follow its own spec (Summary + Findings + etc.).

5. Run subagents in parallel where possible.
   - Do not wait for one reviewer to finish before starting another unless strictly necessary.

6. Aggregate results:
   - Collect all subagent reports.
   - De-duplicate overlapping findings (same issue reported by multiple reviewers).
   - Group by severity: Blockers, High, Medium, Low.
   - Within each group, preserve which subagent raised the issue.

7. Present the final report in this structure:
   - "Review Summary": 3–7 bullets overall.
   - "Blockers": numbered list with source agent and file/line.
   - "High": ...
   - "Medium": ...
   - "Low / Suggestions": ...
   - "Suggested Next Steps": concrete steps to address the most important items first.

8. When the user asks for deeper detail on a finding:
   - Either:
     - Resume the relevant subagent for a deeper dive on that file/issue, or
     - Expand the finding with more context and suggestions.
```

This matches the supervisor pattern and the way subagent orchestration is described in the docs and community examples.[7][8][5]

***

## 3. Concrete subagent invocation prompts

Assuming you have the subagents from our previous message, your orchestrator will build prompts like:

**Logic reviewer**

```text
Use the adversarial-logic-reviewer subagent.

Context:
- You are reviewing CODE CHANGES (git diff), not the entire repository.
- Focus ONLY on logical correctness, control flow, and edge cases.
- Ignore style and naming unless they hide a logic bug.

Inputs:
- Summary of change: {short summary}
- Diff: {unified diff for relevant files}
- Files: {full contents of changed files}

Task:
- Apply your adversarial-logic lens to these changes.
- Identify logical errors, missing branches, unhandled edge cases, and broken invariants.
- Follow your standard output format (Summary, Findings, Open Questions).
```

**Tests/coverage reviewer**

```text
Use the tests-coverage-reviewer subagent.

Context:
- You are reviewing CODE CHANGES and their TEST COVERAGE.
- Focus on whether behavior changes are properly tested.

Inputs:
- Summary of change: {short summary}
- Diff: {unified diff for code and test files}
- Files: {full contents of changed code and relevant test files}

Task:
- Map each significant behavior change to tests.
- Identify missing or weak tests and propose specific new tests.
- Follow your standard output format.
```

**Security, performance, conventions** follow the same pattern with lens-specific text.[9][10]

***

## 4. Aggregation/synthesis pattern

In the `/review` command instructions above, step 6 is effectively a “synthesis agent” running inside the orchestrator.[6][11]

You can make this explicit in the command spec:

```markdown
After all subagents return:

- Treat their reports as input to a synthesis step.
- Do NOT discard or rewrite their findings; instead:
  - Tag each finding with its source agent.
  - Merge obviously duplicate items.
  - Normalize severity terms into {BLOCKER, HIGH, MEDIUM, LOW}.
- If two agents disagree:
  - Call out the disagreement explicitly.
  - Prefer correctness and security over performance and style.
```

This gives you a deterministic final shape without losing the richness of per-lens reports.[4][12]

***

## 5. Optional: narrow-scope variants

You might also want:

- `/review file` – same orchestrator but only for the current file.  
- `/review quick` – run just adversarial-logic + conventions for speed.  
- `/review security` – run only security-reviewer + tests-coverage.[13][14]

These can be thin wrappers around the same orchestration logic with different subagent lists and prompts.

If you paste your current CLAUDE.md and any existing `/review`-like command, I can rewrite it to this multi-agent pattern with concrete YAML/markdown you can drop into `.claude/commands/review.md` and matching subagent names.  

## Human

I want a debugger spec tailored for Python and TypeScript

## Assistant

Here’s a single debugger subagent you can use for both Python and TypeScript, with language-aware behavior baked in.[1][2]

***

## Debugger subagent spec (Python + TypeScript)

```yaml
---
name: debugger
description: Debugging specialist for Python and TypeScript errors, test failures, and incorrect behavior.
tools: [Read, Edit, Bash, Grep, Glob]
---
You are an expert debugger for Python and TypeScript projects.
Your goal is root-cause analysis plus minimal, well-tested fixes.

Supported stacks:
- Python: pytest/unittest, CLI scripts, services.
- TypeScript: node/ts-node, jest/vitest, frontend tooling (vite/next), ESLint/TS errors.

General principles:
- Fix the root cause, not just silence the symptom.
- Prefer the smallest safe code change that passes tests and preserves intent.
- Avoid drive-by refactors unless they directly improve debuggability or correctness.
- Preserve types and public APIs unless the user explicitly allows breaking changes.

When invoked, ALWAYS follow this process:

1. Capture the problem
   - Identify and restate:
     - Error messages and stack traces (Python/TS).
     - Failing tests (names, files, assertions).
     - Incorrect behavior described by the user.
   - If the problem is underspecified, clearly state what is missing.

2. Reproduce (conceptually or via commands)
   - Infer or identify exact reproduction commands, for example:
     - Python: `pytest {path::test_name}`, `python path/to/script.py args`
     - TypeScript: `npm test`, `pnpm test path`, `npm run lint`, `npm run dev` + specific URL or action
   - If explicit commands are provided, treat them as ground truth.
   - Note all relevant env constraints (Python/Node version assumptions, OS-specific paths) when visible.

3. Localize the failure
   - Use stack traces to find the deepest relevant frame in user code (not library code).
   - Map failing tests to the functions, classes, or modules under test.
   - For TypeScript, pay special attention to:
     - Type errors from tsc.
     - Mismatches between declared types and runtime behavior.
   - For Python, pay special attention to:
     - Dynamic typing pitfalls.
     - Edge cases in control flow and data structures.

4. Form and test hypotheses
   - List 1–3 plausible root causes.
   - For each hypothesis:
     - Point to the specific lines/blocks that support it.
     - Use code inspection, targeted logging, or conceptual test runs to confirm or rule it out.
   - Prefer strong, evidence-backed single root causes over long speculative lists.

5. Implement a minimal fix
   - Make the smallest safe code change that resolves the confirmed root cause.
   - Rules:
     - Preserve function signatures and public types unless obviously incorrect.
     - In TypeScript, keep types accurate and strict; do NOT “fix” by using `any` unless the user explicitly allows it.
     - In Python, avoid clever one-liners that reduce clarity; favor explicit, readable logic.
   - If multiple fixes are possible, choose the one that:
     - Minimizes scope and risk.
     - Improves readability and future debuggability.

6. Verify the fix
   - Identify and conceptually run the most relevant tests/commands:
     - Original failing tests.
     - Targeted new tests if you add them.
   - Explain:
     - What should now pass that previously failed.
     - Why the fix is unlikely to introduce regressions.
   - If you cannot be confident (e.g. missing environment), be explicit about what remains uncertain.

Language-specific focus:

- For Python:
  - Watch for:
    - Off-by-one and boundary conditions in loops and slices.
    - Mutable default arguments, shared state, global variables.
    - Incorrect exception handling (overly broad except, swallowed errors).
    - Async pitfalls: missing `await`, event loop misuse.
  - Use logging or small helper checks when they greatly aid diagnosis.

- For TypeScript:
  - Watch for:
    - Type mismatches between definitions and actual values.
    - Incorrect narrowing, unreachable code, and misused union/discriminated unions.
    - Async/Promise handling errors (missing `await`, unhandled rejections).
    - Frontend-specific issues (state not updating, stale closures, dependency arrays in hooks).
  - Prefer type-safe fixes that improve the fidelity between the types and runtime behavior.

Output format (always):

```markdown
## Debug Summary
- Short bullet list of what was broken and what you fixed.

## Root Cause
- Concise explanation of the true underlying cause.
- Why it manifested as the observed error or failing test.

## Evidence
- Key stack frames, test names, and code snippets (with file paths and line ranges) that support your diagnosis.

## Fix
- Description of the changes you made.
- File-by-file breakdown with rationale for each edit.

## Verification
- Tests or commands you conceptually ran (or recommend running).
- What success looks like and any remaining risks.

## Prevention
- Optional suggestions: tests, assertions, type refinements, or guardrails to avoid similar bugs in the future.
```

If the issue cannot be fully resolved with available information:
- Clearly mark the current best hypothesis.
- List the minimal additional data (logs, inputs, environment details) needed to reach a confident fix.
- Provide interim mitigations if possible.
```

If you show me one or two real error cases (Python + TS) you commonly hit, I can tighten this spec further with language- and stack-specific heuristics (e.g. FastAPI + pytest, Next.js + Vitest) that match your codebase.  

## Human

how should claude code invoke these subagents?  often the LLM wants to try and use python.

## Assistant

You control this in two places: the subagent definitions (`tools`/`disallowedTools`) and your command/orchestrator prompts. The goal is to whitelist only the tools each subagent genuinely needs and to tell Claude explicitly *not* to spin up Python unless debugging truly requires it.[1][2]

***

## 1. Restrict tools per subagent (don’t inherit everything)

By default, subagents inherit all tools the main thread has, including Python/CLI-like tools, so they happily reach for them. To prevent that, always set `tools` in the subagent frontmatter instead of leaving it empty.[2][1]

Example for a read-only reviewer:

```yaml
---
name: adversarial-logic-reviewer
description: Logic-only reviewer for code changes.
tools: [Read, Grep, Glob]  # No Bash, no Python, no Edit
---
```

Example for debugger (where you *do* want Bash but maybe not Python REPL):

```yaml
---
name: debugger
description: Debugging specialist for Python and TypeScript.
tools: [Read, Edit, Bash, Grep, Glob]  # Omit Python tool if you don't want REPL-style runs
---
```

If you ever see it over-using a particular tool that still needs to exist for other agents, you can also use `disallowedTools` at the subagent level.[3][1]

***

## 2. Teach the orchestrator which tools to expose

In your `/review` or `/debug` command logic, you decide which subagents to call and what tools are visible in that context.[4][1]

Patterns:

- For pure review flows (`/review`):
  - Never expose Python or other execution tools to reviewers.  
  - Only list read-only tools for those subagents (Read/Grep/Glob and maybe very constrained Bash if you really need it).

- For debugging flows (`/debug`):
  - Explicitly expose the debugger subagent with Bash and Edit (and optionally Python), but *don’t* include other “exploration” agents that might spawn extra execution.[5][1]

And in the command prompt, say something like:

```markdown
You must NOT run arbitrary Python or shell commands in this review.
Limit yourself to static analysis using the tools available to this subagent.
Execution-based debugging is only allowed when the user runs /debug.
```

This aligns with guidance that you should scope tool access to the task and avoid giving the agent more tools than it needs.[6][2]

***

## 3. Put negative guidance into each subagent’s spec

Add a “When NOT to use tools” block to each subagent.[7][4]

For reviewers:

```text
When NOT to use tools:
- Do NOT run Python or shell commands to execute code.
- Do NOT modify files.
- Your job is static analysis of the provided diff and files only.
- If execution would help, suggest a specific command to the user or to the debugger subagent instead of running it yourself.
```

For debugger:

```text
Tool usage rules:
- Prefer reading code, test output, and logs first.
- Only run Bash commands that the user could safely run locally (e.g. the failing test, a simple script).
- Avoid exploratory commands that scan the whole repo or install dependencies.
- Only suggest Python REPL-style exploration if necessary and clearly explain what to run.
```

Negative guidance like this is called out as useful in real-world subagent collections and best-practices writeups.[4][5]

***

## 4. Make `/debug` the only place that “feels like Python”

Since Claude wants to “just run Python,” give it a designated sandbox:

- `/review`:
  - Specs and tools are read-only.
  - Prompts say “static review, no code execution.”

- `/debug`:
  - The debugger subagent is allowed Bash (and optionally a Python tool).
  - Prompt: “You may run the *exact* failing test command the user provided, but nothing else without explaining why.”

This “execution lives in `/debug` only” pattern is effectively how people separate plan/review from execute phases in multi-agent systems.[6][5][4]

***

## 5. If it still insists on Python…

If you see it still trying to use Python or other tools inappropriately:

- Tighten `tools` on the subagent (whitelist only the essentials).  
- Add explicit “When NOT to use” and “Forbidden behaviors” bullets to the spec.  
- Optionally disable specific tools globally for that agent via settings (deny list).[1][2]

If you paste one of your existing subagent YAML blocks that keeps trying to “run some Python,” I can rewrite its `tools` and guidance so that behavior becomes much less likely.  

## Human

you misunderstood.  When using the subagent orchestration, it wants to use python to invoke the subagents and control the orchestration.

## Assistant

Claude Code’s bias toward “let’s write a Python orchestrator” is mostly a prompting/role issue: you want the *current session* to act as a high-level coordinator that uses the **built‑in subagent mechanism**, not as a dev writing Python code to call the API. The fix is to make the orchestration declarative and to ban “write Python to call agents” explicitly in your command and CLAUDE.md.[1][2]

***

## 1. Tell it what orchestration *means* in this context

In CLAUDE.md and in your `/review` or `/debug` command, define “orchestrate subagents” as an *internal control flow pattern*, not code it should implement:

```markdown
When I say "orchestrate subagents" in this IDE:

- I do NOT want you to write Python, TypeScript, or API client code to call agents.
- You are already running inside Claude Code with built-in support for subagents.
- "Call a subagent" means: internally start that named subagent with a focused prompt and the context I provided (files, diffs, errors).
- All orchestration should happen through your own internal multi-agent capabilities, not by generating new programs.
```

Reinforce this in the `/review` and `/debug` command descriptions:

```markdown
You are NOT writing orchestration code.
You are the orchestrator.
Use Claude Code's native subagent features to spawn and coordinate the named agents.
Never respond with Python or TypeScript that calls subagents.
```

People hit exactly this problem when they mix “agent orchestration” examples from SDK docs (which *do* use Python/TS) with Claude Code, where orchestration is built in.[3][4]

***

## 2. Make the command behavior declarative, not “implement this in code”

Avoid language that sounds like an implementation task (“write”, “implement”, “build a Python script that…”). Use behavior rules instead:

Bad (triggers “I should write code”):

> “Implement a multi-agent code review orchestrator that calls these subagents…”

Better:

```markdown
Behavior of /review:

- Identify changed files and diffs.
- For each relevant lens, internally:
  - Start the corresponding subagent with a focused prompt.
  - Provide only the necessary context (summaries, diffs, file contents).
- Wait for their reports and then synthesize a final review.
- Present the result directly to the user in this chat.
- Do not output any orchestration code; only output human-readable review results.
```

You’re effectively writing state-machine instructions, not asking it to generate an SDK client.[2][5]

***

## 3. Add hard “do NOT write Python to orchestrate agents” rules

Be explicit in the global spec and in each orchestration command:

```markdown
Forbidden behaviors:

- Do NOT propose writing Python/TypeScript scripts that call Claude or its subagents.
- Do NOT output code snippets that "show how to orchestrate these agents" unless the user explicitly asks to see SDK code.
- For /review and /debug, all orchestration must be done by you, inside this session, using built-in subagent support.
```

This kind of negative constraint is exactly how people curb unwanted tool choices and behaviors in Claude Code.[6][2]

***

## 4. When you *do* want SDK code, isolate it

You sometimes *will* want real Python/TS orchestration (e.g., external agents or CI bots). To keep that from bleeding into your IDE flows:

- Create a separate command like `/sdk-orchestrator-example` whose *only* purpose is “show me how to write Python/TS that calls these subagents via the API.”  
- In CLAUDE.md, say:

  ```markdown
  Only discuss Python/TypeScript orchestration code when the user:
  - Explicitly mentions SDK, API, or CI integration, or
  - Uses the /sdk-orchestrator-example command.

  Otherwise, assume orchestration should happen natively inside Claude Code without external code.
  ```

That prevents it from generalizing Python SDK examples into your normal `/review` and `/debug` flows.[4][7]

***

## 5. If it still tries to “code the orchestrator”

If after these changes it still responds with Python/TS:

- Immediately interrupt and say (once, so it learns your environment norm):

  > “You’re already inside Claude Code. Don’t write Python to call subagents; use the built-in subagent orchestration internally and give me the review/debug output directly.”

- Then add that exact sentence into your CLAUDE.md under “Environment assumptions.”

This pattern—correcting once and baking the correction into the system prompt—is how experienced users get Claude Code to drop bad habits like “let me build a Python wrapper for this.”[8][9]

***

If you paste your current `/review` command and the CLAUDE.md block where you mention “orchestrate subagents,” I can rewrite those texts so they strongly bias toward native orchestration and away from “write Python to call the API.”

## Human

do we have to say anything about make multiple task tool calls in one message in order to get parallel subagents to work?

## Assistant

You don’t *have* to mention it, but being explicit about “multiple Task calls in one message” measurably increases the chance that Claude actually parallelizes the subagents.[1][2]

***

## How to phrase it

Add something like this to your CLAUDE.md and to any orchestration command (`/review`, `/plan-workflow`, etc.):

```markdown
When you dispatch subagents for independent work:

- Start multiple subagents in PARALLEL by emitting multiple Task tool calls in a SINGLE message.
- Do not wait for one Task to finish before creating the next when the work is independent.
- Example: for separate files or lenses, create one Task per subagent in the same step, then wait for all results and synthesize.
```

This aligns with community experience that “run multiple Task invocations in a SINGLE message” is the magic phrase that flips it from sequential to parallel in many setups.[2][3]

***

## When to *not* push parallel

Also encode the guardrail:

```markdown
Only parallelize when:
- Subagents work on independent files or concerns (logic vs security vs tests) that don’t write to the same region.
- They don’t depend on each other’s output.

Otherwise, prefer sequential Tasks to avoid conflicts.
```

That matches the best-practices guidance (parallel for independent domains, sequential when there are dependencies or shared writes).[4][5]

If you show me your current `/review` spec, I can splice in the exact 2–3 lines to encourage “multi Task in one message” without bloating the prompt.

## Human

What exact prompt phrasing triggers parallel subagent execution
How to handle merging results from parallel subagents
Limitations of parallel tool calls in Claude Code

## Assistant

Here’s what’s known and what actually works in practice.

***

## 1. Prompt phrasing that *tends* to trigger parallel subagents

There is no single magic string, but two patterns appear consistently in Claude Code + Task tool usage: (a) ask for **multiple tasks in one step**, and (b) be explicit that they are **independent** and should be started **in parallel**.[1][2][3]

Concrete wording you can drop into CLAUDE.md and orchestration commands:

```markdown
When dispatching subagents for independent work:

- Create multiple Task tool calls in a SINGLE step so they can run in PARALLEL.
- Do NOT create one Task, wait, then create the next if the work is independent.
- Example: "Start N Tasks in parallel, one per lens/file, then wait for all to finish and synthesize the results."
```

And more task-specific phrasing:

```markdown
For code review:

- Spawn separate Tasks in parallel:
  - one for adversarial-logic,
  - one for tests-coverage,
  - one for security,
  - one for performance (if applicable).
- Each Task should run as its own subagent with a focused prompt and the same diff context.
- Emit all these Task calls in a single message so they can run concurrently.
```

From reports and guides, phrases like “**spawn N Tasks in parallel**”, “**create multiple Task invocations in one turn**”, and “**don’t serialize these**” noticeably increase parallel tool use probability, though the model still has autonomy.[2][3][1]

***

## 2. How to handle merging results from parallel subagents

The merge is just another (sequential) reasoning step by the main agent once all Tasks finish.[4][1]

Best practice:

- In your orchestrator / command prompt, define a very explicit merge protocol:

```markdown
After all subagent Tasks complete:

1. Collect each subagent's report:
   - Include: agent name, scope (files/lens), and findings.

2. Normalize findings:
   - Map severities into {BLOCKER, HIGH, MEDIUM, LOW}.
   - Ensure each finding includes: source agent, file/path, brief title, and details.

3. De-duplicate:
   - If multiple agents report the same underlying issue:
     - Merge into a single finding.
     - Note all contributing agents, e.g. "Reported by logic + tests".

4. Resolve conflicts:
   - If agents disagree (e.g., performance vs readability):
     - Call out the disagreement explicitly.
     - Prioritize correctness and security over performance and style.

5. Present a unified report:
   - "Summary": 3–7 bullets.
   - Sections: Blockers, High, Medium, Low, each a numbered list.
   - "Next Steps": ordered list of concrete actions.
```

The key is: treat each subagent output as input data and tell Claude exactly how to aggregate it, rather than letting it improvise merging logic every time.[5][1][4]

***

## 3. Limitations of parallel tool calls in Claude Code

From docs + real-world writeups, there are several important constraints.[6][7][8][1][2]

1. **Model decides, you can’t force**  
   - Even with “multiple Tasks in one message” language, Claude may still choose sequential calls, especially on Sonnet variants that are more conservative with tools.[1][2]
   - You can *bias* but not guarantee.

2. **Shared-resource conflict risk**  
   - Parallel subagents work best for read-only tasks or logically isolated domains.[9][4]
   - If two Tasks both edit the same file/region, you can get conflicts or lost changes; patterns/experiences explicitly warn that **parallel only works safely when agents touch different files or operate read-only**.[7][4]

3. **One main conversation turn at a time**  
   - Claude Code UX: you still see one main thread; subagents run “in the background” and report back.[10][9]
   - You don’t get true multi-core orchestration control; you’re asking the model/server to schedule internal Tasks.

4. **Token + latency tradeoffs**  
   - Parallelizing 8 review agents on a small change burns more tokens and may not be faster overall due to overhead.[5][9]
   - Guides recommend 3–6 agents for medium changes and scaling up only for large PRs.[5]

5. **Buggy / evolving Task behavior**  
   - There are reports of models only emitting 1 Task per message in some builds and of duplicated tool calls with certain configs.[8][11]
   - In other words, behavior is not perfectly stable; some of this is still “tune and observe” territory.

So: parallel subagents are powerful, but you should constrain them to independent, mostly read-only work and treat parallelism as best-effort, not guaranteed.

***

If you share your current `/review` or `/plan-workflow` prompt, I can inject an exact “parallel Tasks + merge protocol” block tuned to your agents and file boundaries.

## Human

How to integrate parallel subagents with git worktrees

## Assistant

You combine them at two levels: (1) worktree isolation so agents don’t clobber each other’s files, and (2) Task‑based parallel subagents inside those worktrees. Git worktrees give you *process isolation*; Tasks give you *reasoning/tool parallelism* within each isolated copy.[1][2]

***

## 1. Basic pattern: one worktree per “parallel unit”

Use worktrees to separate anything that will *write* code:

- For parallel features / tickets:  
  - Create one worktree per ticket (manually or via a command/skill).  
  - Start a Claude Code session in each worktree, so each session is its own agent working on its own branch.[3][2][4]

- For heavy multi-agent runs on the *same* feature:  
  - Option A: one worktree, multiple subagents, **read‑only reviewers** in parallel, single writer (debugger/implementer) sequentially.  
  - Option B: one worktree per “candidate implementation” (e.g., exploring 3 different refactor strategies in parallel), each with its own internal subagents.[5][6][7]

Within a given worktree, your parallel subagents should mostly read and comment, not all call `Edit` on the same files simultaneously.

***

## 2. Enabling worktree isolation for subagents

Claude Code now supports worktree isolation directly in subagents:[2][1]

- In each subagent that should run in its own worktree:

```yaml
---
name: refactor-worker
description: Experimental refactor subagent working in its own isolated worktree.
tools: [Read, Edit, Bash, Grep, Glob]
isolation: worktree
---
```

Effects:

- Claude automatically creates a temporary git worktree for that subagent under something like `.claude/worktrees/<agent-id>` and uses a dedicated branch.[1][2]
- When the subagent finishes with no changes, the worktree is auto-cleaned; if there are commits/changes, you’re prompted what to do (merge, cherry-pick, etc.).[8][2]

This is ideal for:

- Batch code mods / migrations where multiple agents *write* to different areas in parallel.  
- Hedge‑your‑bets development: several agents attempt the same task different ways in isolated branches.[6][9][5]

For pure reviewers (logic/quality/security), you usually *don’t* need `isolation: worktree`—they can just read the main worktree and run in parallel with read‑only tools.

***

## 3. Using parallel Tasks inside each worktree

Inside a given worktree/session, you can then use the parallel Task pattern you’re already designing:

- Orchestrator (`/review`, `/debug`, `/plan-workflow`) runs in that worktree.  
- It spawns *multiple Tasks in one step* for independent review subagents (logic, tests, security, performance, etc.) with read‑only tools.[10][11][12]
- Because they’re in the same directory, all see the same code, but you avoid write conflicts by keeping them read‑only (no `Edit`, no heavy Bash that mutates files).

If you need *writers* in parallel (e.g., N refactor agents): give those writer subagents `isolation: worktree` so each gets a distinct branch/directory and cannot stomp on each other.[13][2][1]

***

## 4. Merging worktree outputs back to main

Once parallel worktrees/subagents finish, you still have to reconcile branches.[14][2][13]

Typical patterns:

- **Single chosen candidate** (e.g., 3 alternative implementations):  
  - You manually inspect the branches (or ask a reviewer subagent in each worktree).  
  - Choose one, merge or cherry‑pick into your main branch/worktree.

- **Sharded edits** (e.g., large migration split across files/directories):  
  - Each worktree branch modifies disjoint paths.  
  - You merge them back sequentially into your main branch; conflicts are rare if you sharded cleanly.

It’s often worth adding a small “merge helper” command/skill that:

- Lists active worktree branches and their diffs.  
- Summarizes what each agent changed.  
- Proposes a merge order and flags potential conflicts.

***

## 5. When to combine vs. separate

Use this rule of thumb:

- **Parallel subagents, single worktree**  
  - For review, analysis, planning, and other read‑heavy tasks.  
  - Only one writer (or writers working in clearly separate files) at a time.

- **Parallel worktrees, possibly with their own parallel subagents**  
  - For genuinely independent tasks/tickets.  
  - For multiple writer agents whose changes would otherwise collide.  
  - For “N candidate solutions” patterns.[15][7][6]

If you show me your current git worktree layout and how you run Claude (CLI flags or terminal setup), I can sketch a concrete workflow: which tasks stay in one worktree with parallel reviewers, and where to spin up extra worktrees plus `isolation: worktree` subagents.  

## Human

Show me a concrete CLI and config setup for N worktrees with agents

## Assistant

You can treat each worktree as “one ticket, one Claude Code agent (with its own subagents)”, wired by a tiny shell wrapper plus a few conventions in CLAUDE.md.[1][2]

***

## 1. Shell helpers: create N worktrees + sessions

Assume:

- Main repo at `~/dev/monorepo`
- Base branch `main`
- Tickets like `PROJ-123`, `PROJ-124`, etc.

### Script: create a worktree for a ticket

```bash
# ~/bin/ctree (chmod +x)

#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: ctree TICKET_ID" >&2
  exit 1
fi

TICKET="$1"
REPO_ROOT="${REPO_ROOT:-$HOME/dev/monorepo}"
cd "$REPO_ROOT"

BRANCH="ticket/${TICKET}"
WORKTREE_DIR=".worktrees/${TICKET}"

mkdir -p .worktrees

# Create branch if it doesn't exist
if ! git show-ref --verify --quiet "refs/heads/${BRANCH}"; then
  git branch "${BRANCH}" origin/main
fi

# Create worktree if it doesn't exist
if [ ! -d "${WORKTREE_DIR}" ]; then
  git worktree add "${WORKTREE_DIR}" "${BRANCH}"
fi

echo "Worktree ready:"
echo "  branch:    ${BRANCH}"
echo "  worktree:  ${REPO_ROOT}/${WORKTREE_DIR}"
```

### Script: open Claude Code in that worktree

Assuming `claude` CLI:

```bash
# ~/bin/cc-ticket (chmod +x)

#!/usr/bin/env bash
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: cc-ticket TICKET_ID" >&2
  exit 1
fi

TICKET="$1"
REPO_ROOT="${REPO_ROOT:-$HOME/dev/monorepo}"
WORKTREE_DIR="${REPO_ROOT}/.worktrees/${TICKET}"

if [ ! -d "$WORKTREE_DIR" ]; then
  echo "Worktree not found for ${TICKET}. Run: ctree ${TICKET}" >&2
  exit 1
fi

cd "$WORKTREE_DIR"
echo "Starting Claude Code in $(pwd) for ticket ${TICKET}"
claude code .
```

Usage:

```bash
ctree PROJ-123
ctree PROJ-124

cc-ticket PROJ-123  # Claude session A
cc-ticket PROJ-124  # Claude session B
```

Each session now operates on its own branch/worktree; inside, you still have subagents and Tasks available.[2][1]

***

## 2. Per-worktree CLAUDE.md conventions

In your repo root, keep a single `CLAUDE.md` with global rules. Inside each worktree, add a tiny worktree-local override file (or use the same CLAUDE.md but with a section that’s parameterized by env).

Example top of `CLAUDE.md`:

```markdown
# Claude Code Project Config

Environment:

- You are always operating inside a git worktree of the main monorepo.
- The current worktree corresponds to a single ticket/branch.
- Do NOT modify files outside this worktree.
- Assume the branch name and ticket ID can be inferred from `git rev-parse --abbrev-ref HEAD`.

Ticket isolation:

- Treat each Claude Code session as owning ONE ticket.
- Do not reference or modify other tickets' branches or worktrees.
- If a change clearly belongs to another ticket, add a NOTE instead of changing it.
```

If you want the ticket ID surfaced, you can add a tiny note file in each worktree, e.g. `.claude/ticket-id` that contains `PROJ-123`, and instruct agents to read it when they start.

***

## 3. Subagent config inside each worktree

Your `.claude/agents/*.md` live in the repo and are shared across worktrees. For writer vs reviewer isolation:

- **Reviewers** (logic, tests, security, etc.) – read-only in each worktree:

```yaml
---
name: adversarial-logic-reviewer
description: Logic-only reviewer for code changes in this worktree.
tools: [Read, Grep, Glob]
---
```

- **Implementers / debuggers** – writers bound to *this* worktree:

```yaml
---
name: debugger
description: Debugger for code in the CURRENT worktree only.
tools: [Read, Edit, Bash, Grep, Glob]
---
You must only modify files under the current worktree directory.
Never touch parent repo directories directly.
```

Claude Code sees the current dir as the project root for that session, so “current worktree only” is enforced by the OS path boundary—not just by prompt.[3][4]

If you want *auto-created ephemeral* worktrees (e.g. experimental refactors per agent) instead of manual `git worktree` calls, also use `isolation: worktree` on those specific subagents, as in the previous answer.[4][3]

***

## 4. N-way parallel workflow in practice

Putting it together:

1. For N tickets:

```bash
ctree PROJ-101
ctree PROJ-102
ctree PROJ-103

cc-ticket PROJ-101
cc-ticket PROJ-102
cc-ticket PROJ-103
```

2. In each Claude session:

- Use `/plan-workflow` → `/implement` → `/review` as usual, with your multi-agent setups.  
- Review subagents run in parallel inside the worktree via Tasks.  
- Implementers/editors operate only on that branch.

3. Merging back:

- From main repo:

```bash
cd ~/dev/monorepo
git fetch origin

git checkout main
git merge --no-ff ticket/PROJ-101
git merge --no-ff ticket/PROJ-102
...
```

Or open PRs per ticket branch.

This matches the pattern described in multi-worktree + AI workflows: “one worktree per slice of work, each with its own AI agent(s), then merge branches like normal Git.”[5][6][2]

***

If you share your current repo layout and how you normally start Claude Code (exact CLI invocation), I can adjust these scripts and prompts to your paths and shell.

## Human

We have had subagents dump tones of context and halted claude code because it ran out of memory.  I believe the answer is to write to file, and then use grep or /search for the main orchestrator to get the data.  Is that correct?  What's all the info I should tell Claude code so they can write the agents and skills optimally?

## Assistant

Writing to files and reloading targeted slices (via Grep/Glob/Read or a search skill) is exactly the right pattern; you want subagents to emit **compact artifacts** and let the orchestrator **pull** what it needs, instead of pushing giant transcripts into one context.[1][2][3][4]

Below is the info I’d bake into CLAUDE.md, agents, and skills so Claude Code adopts that pattern by default.

***

## 1. Core architecture principle

Tell Claude explicitly:

```markdown
Context management rule:

- Subagents MUST NOT dump large raw outputs directly into the main conversation.
- For large analyses, they MUST:
  - Write results to structured files (e.g. under .scratchpad/ or .reports/),
  - Return only a concise summary + file paths.
- The orchestrator (this session) will later:
  - Use Grep/Read or search skills to pull only the relevant parts when needed.
```

This matches how subagents are described: each has its own context window, and the main agent only gets a compact “return value,” not the full transcript.[4][1]

***

## 2. File layout and conventions

Define a simple, predictable layout:

```markdown
Scratchpad and report files:

- .scratchpad/plan/: planner outputs and task lists
- .scratchpad/review/: code review reports per file/PR
- .scratchpad/debug/: debugging logs, hypotheses, and root-cause analyses
- .scratchpad/memory/: distilled notes worth long-term reuse

Filename conventions:
- plan-{ticket or short id}.md
- review-{branch or PR}-{lens}.md  (lens = logic, tests, security, perf)
- debug-{error-signature or test-name}.md
```

Tell agents:

```markdown
When you do a substantial analysis, write it into one of these files and then:
- Return a short human-readable summary (3–7 bullets).
- List the files you wrote and what they contain.
- Do NOT inline the full report into the chat.
```

This aligns with “use files as scratchpads / checklists instead of blowing up the conversation context.”[3][5]

***

## 3. Guidance for subagents

In each subagent spec (planner, reviewers, debugger, memory-ingest), add a **Context & I/O** section:

```text
Context & I/O:

- You have your own context window; you can read files, run grep, and think extensively there.
- When you finish:
  - Save detailed results to a file under .scratchpad/{area}/...
  - Return only:
    - A short "Summary" section.
    - A "Artifacts" section listing file paths and a one-line description per file.
- Never paste large code sections, logs, or full analyses into the main conversation if they can be read from files instead.
```

For example, a review agent might end with:

```markdown
## Summary
- 3 blockers, 4 high, 2 medium issues found.

## Artifacts
- .scratchpad/review/review-branch-login-logic.md — logic review details
- .scratchpad/review/review-branch-login-tests.md — tests/coverage review
```

This keeps the main context small and lets the orchestrator retrieve details on demand.[6][1][3]

***

## 4. Guidance for the orchestrator (main session)

/plan-workflow, /review, /debug, etc. should all say something like:

```markdown
Orchestration and context:

- When you need detailed information from subagents:
  - First check their "Artifacts" section for file paths.
  - Use Grep/Read or a search skill to load only the relevant parts.
- Do NOT ask subagents to paste their entire report back into this chat.
- Prefer this pattern:
  1) Subagent writes file(s) + returns summary.
  2) You Grep or Read specific sections when needed.
```

If you have a dedicated `grep-and-read` skill or similar, mention it as the primary way to fetch data efficiently.[2][7]

***

## 5. Skill design for efficient retrieval

Add at least one skill that’s explicitly for “load from file, not from chat.” For example, a Grep + Read combo:[7][2]

```yaml
---
name: scratchpad-search
description: Efficiently search and load content from .scratchpad files.
tools: [Grep, Read, Glob]
---
You are the primary way to retrieve detailed info saved by other agents.

Process:
1. Use Glob to list files under .scratchpad/** that match the requested area.
2. Use Grep to narrow to relevant lines/chunks.
3. Use Read to fetch only the necessary blocks.
4. Return a concise extract with file:line references.
```

And in CLAUDE.md:

```markdown
When you need older analysis or review details, prefer calling `scratchpad-search`
instead of asking agents to restate or re-run work.
```

This avoids redoing expensive reasoning and prevents giant context dumps.[1][2][4]

***

## 6. Explicit anti-patterns to forbid

Tell Claude what **not** to do:

```markdown
Forbidden patterns:

- Do NOT dump full grep outputs, logs, test runs, or long code listings into the main chat.
- Do NOT copy entire .scratchpad reports back into the conversation.
- Do NOT keep extending the conversation with repeated long summaries of older work.
- Instead:
  - Save detailed info to files.
  - Refer to them by path.
  - Reload specific parts when needed using search tools or skills.
```

This is exactly the failure mode that leads to compaction, degraded reasoning, and OOMs.[8][9][6]

***

## 7. Subagent–orchestrator contract for “returns”

Finally, define a simple “return contract” for subagents so you don’t get surprises:

```markdown
Subagent return contract:

Every subagent MUST:

1. Keep the returned content under a few hundred tokens when possible.
2. Use this structure:
   - "Summary": 3–7 bullets.
   - "Key Findings" or "Key Decisions": briefly listed.
   - "Artifacts": list of file paths + one-line descriptions.
3. Never include full raw tool outputs in the return; only references to files where those outputs are stored.
```

You can even add: “If you think your return will exceed ~1,000 tokens, stop and write the rest to a file instead, then reference it.”

This matches how people successfully avoid context blowups with subagents: each agent’s big context remains local; the orchestrator sees compressed returns + file handles.[10][4][1]

***

If you paste one of your current “noisy” subagent specs (the ones that previously dumped too much context), I can rewrite its I/O section and add a small scratchpad-search skill tailored to your repo layout so you can drop them in immediately.

## Human

I seem to have lost the advesarial logic subagent spec.  Can you show what you think is the best implementation?

## Assistant

Here’s a self-contained adversarial-logic subagent spec, tuned for reuse across plans and code, and for multi-agent / scratchpad workflows you described.[1][2]

***

## adversarial-logic subagent spec (generic lens)

```yaml
---
name: adversarial-logic-reviewer
description: Finds logical errors, broken assumptions, and edge cases in plans and code.
tools: [Read, Grep, Glob]
---
You are an adversarial LOGIC reviewer.

Lens:
- Your ONLY concern is logical correctness and consistency.
- You look for:
  - Wrong or inverted conditions.
  - Off-by-one and boundary errors.
  - Missing or impossible branches.
  - Unhandled edge cases and inconsistent assumptions.
  - Contradictions between different parts of the artifact.

Scope:
- You do NOT care about style, naming, formatting, or architecture unless they directly cause or hide logic bugs.
- You do NOT propose performance or UX improvements unless they change correctness.
- You can be used on:
  - Implementation PLANS (markdown, task breakdowns, sequences of steps).
  - SOURCE CODE (Python, TypeScript, etc.).
- The calling workflow will tell you what kind of artifact you are reviewing.

Context & I/O:
- You have your own context window and can freely:
  - Read files with Read.
  - Search with Grep and Glob.
- When your analysis is large:
  - Write detailed findings to a file under .scratchpad/review/.
  - Return only a concise summary plus the file path(s).
- NEVER dump long code listings, grep output, or full reports into the main conversation if they can be loaded from files instead.

Process (always follow):

1. Understand the artifact and its claims
   - Identify:
     - What the artifact is (plan vs code) based on the calling prompt.
     - The main behaviors, invariants, or guarantees it intends to provide.
   - For plans:
     - Extract the sequence of steps and dependencies.
   - For code:
     - Identify the changed functions, inputs, outputs, and key branches.

2. Enumerate assumptions and invariants
   - List the key assumptions the artifact appears to make (about inputs, state, environment, and ordering).
   - List any invariants that must always hold for correctness.
   - Note where assumptions are implicit or unclear.

3. Construct adversarial scenarios
   - Systematically look for inputs, states, or sequences that might break those invariants.
   - For each relevant function/step:
     - Consider boundary values (empty, zero, max/min, None/null, unexpected types).
     - Consider ordering and concurrency issues (out-of-order, repeated, or skipped steps).
     - Consider error paths (exceptions, failed calls, partial writes).

4. Identify concrete logic issues
   - For each suspected issue, pinpoint:
     - Location: file and line range or plan section.
     - Condition or branch that is wrong, missing, or ambiguous.
     - A concrete adversarial scenario that would cause incorrect behavior.
   - Classify:
     - [BLOCKER]: clearly wrong behavior or high-risk bug.
     - [HIGH]: likely bug or severe edge case.
     - [MEDIUM]: plausible bug or confusing logic.
     - [LOW]: minor inconsistency or unclear reasoning.

5. Propose minimal, precise fixes
   - For each issue, propose the SMALLEST change that repairs the logical problem:
     - Adjusted condition or branch.
     - Added guard, assertion, or branch.
     - Reordered steps or clarified dependency.
   - Keep fixes tightly scoped and avoid unrelated refactors.

Output format (returned to caller):

- Keep the returned content compact. When in doubt, move details to a file.

```markdown
## Summary
- 3–7 bullets describing overall logical soundness and major risks.

## Findings
1. [SEVERITY] Short title
   - Location: {file/section and line/heading}
   - Problem: clear description of the logic issue.
   - Scenario: concrete adversarial example (inputs/state/sequence).
   - Impact: why this matters for correctness.
   - Recommendation: specific minimal fix.

2. ...

## Open Questions
- Any ambiguities or missing information that block full analysis.

## Artifacts (if any)
- .scratchpad/review/review-{context}-logic.md — full detailed findings
```

Behavior across workflows:

- When reviewing IMPLEMENTATION PLANS:
  - Focus on task ordering, dependencies, missing branches, and impossible sequences.
  - Look for steps that assume state that is never established, or tasks that can deadlock or be skipped.

- When reviewing SOURCE CODE:
  - Focus on control flow, conditions, and state transitions.
  - Look for unreachable branches, inconsistent checks, and unhandled edge cases.

Forbidden behaviors:

- Do NOT execute code or tests; you are a static logical reviewer.
- Do NOT modify files; report issues and fixes instead.
- Do NOT widen your remit to style, architecture, or performance.
```

If you tell me how you name your scratchpad files (and whether you want separate specs like `adversarial-logic-plan` vs `adversarial-logic-code` that share this base), I can generate those variants too.

## Human

Does this look ok?

## Assistant

High level: yes, this note looks solid and consistent with how Claude Code + subagents actually behave; I’d keep it with a few small clarifications and TODOs.

***

## What looks good

- Clear snapshot of current state  
  - You captured actual code changes (adding `"logic"` to `SUBAGENTS`) and their intent, which will help future you understand why it’s there.[1]
  - You documented the constitutional filter design (post‑aggregation, transparency, centralized filter), which matches good practice for “adversarial but policy‑bounded” workflows.[1]

- Accurate identification of broken wiring  
  - You correctly flagged missing subagent implementations (`adversarial-qa`, `adversarial-failure-modes`) and the impact on `/adversarial-review` Task calls.[1]
  - You also captured the doc vs reality path mismatch between `.claude/skills/.../SKILL.md` and `.claude/agents/...md`, which is exactly the kind of thing that bites later.[1]

- Good separation of “issues” vs “next steps”  
  - Priority 1/2/3 lists are clear and actionable: fix docs, create/trim missing agents, standardize architecture.[1]
  - The “Decision needed: all agents vs all skills vs hybrid” line makes the architectural fork explicit.

- Parallel subagent phrasing is on point  
  - The recorded prompt snippets (“Create multiple Task tool calls in a SINGLE step…”, “Spawn separate Tasks in parallel…”) are exactly the formulations that current users report as effective for nudging parallelism.[2][1]

***

## Minor improvements worth adding

You don’t need to rewrite the file, but I’d consider:

1. Explicitly choose an architecture direction  
   - At the end of “Standardize Architecture”, add one line that says which way you intend to go (e.g., “Preferred: keep adversarial-* as .claude/agents, use skills *only* as thin wrappers, not as subagent types”).  
   - That prevents future confusion around things like `adversarial-rca` being half skill / half agent.[1]

2. Record how you want missing subagents treated  
   - Under “Critical: Missing Subagent Implementations”, add: “Temporary policy: if a named adversarial-* subagent doesn’t exist, the aggregator should skip it with a warning, not crash.”  
   - This gives you a behavior spec for hooks and avoids brittle Task failures.[1]

3. Note the scratchpad / file‑based pattern you decided on  
   - Append a short “Context Management” section noting: “Subagents must write detailed reports to `.scratchpad/adversarial-*.md` and only return summaries + file paths to avoid OOM/context blowup.”  
   - That ties this note into your more recent decision about not dumping huge context into the orchestrator.

***

## My verdict

- For a session note, this is **good enough to keep as-is** and reference from your CLAUDE.md / SKILL.md work.  
- The only crucial follow‑ups are:
  - Implement or remove `adversarial-qa` and `adversarial-failure-modes`.  
  - Fix the `agents` vs `skills` location and invocation pattern.  
  - Encode the parallel Task phrasing and context‑management rules into the actual specs/prompts, not just this note.

Do you want help next with the concrete `adversarial-rca` spec + correct Task/Skill invocation pattern to resolve that architecture inconsistency?

## Human

How else do you think it should reduce the number of tokens needed?

## Assistant

The big levers beyond “write to file, then grep” are: constrain scope, compress aggressively, avoid repetition, and keep each agent’s view narrow.

***

## 1. Constrain what each subagent sees

- Narrow file sets  
  - In orchestrator prompts, always pass a **small, explicit list of files** per subagent (e.g., just changed files or one module), not the whole repo.  
  - Use `Glob`/`Grep` first in the orchestrator to select relevant files, then call subagents on that subset only.

- Narrow tasks  
  - Make each subagent’s mission single‑purpose (“logic on this diff”, “tests for this function”), not “review the entire system”.  
  - For large features, shard the work into multiple smaller Tasks instead of one huge context.

***

## 2. Summaries on top of raw artifacts

- Prefer “summary + pointer”  
  - When a subagent reads a big file or many tests, have it:
    - Write detailed notes to `.scratchpad/...`  
    - Return a **short summary** plus file/section pointers.  
  - For follow‑ups, tell Claude: “Use your previous summary and only re‑open file sections that are needed.”

- Rolling summaries  
  - For long-running reviews/debug sessions, keep a single `session-notes` file with a **rolling, compressed summary**, and overwrite/append to it rather than re-explaining history in the chat.

***

## 3. Avoid re-sending unchanged context

- Diff-based reviews  
  - For `/review`, only include the **git diff** + minimal surrounding context, not full files, especially once a file has already been seen earlier in the session.  
  - If you need full file content again, have Claude call `Read` instead of you pasting it via prompt.

- Stable instructions via files  
  - Put long policy docs, coding standards, and architecture notes into versioned files (e.g. `docs/standards/*.md`) and tell agents to `Read` them when needed, instead of inlining the whole policy in every prompt.

***

## 4. De-duplicate across agents and turns

- Subagent outputs  
  - In the aggregator, instruct: “If two subagents report the same issue, merge into one finding instead of repeating the full explanation twice.”  
  - You can keep a small in-memory map of `(file, line-range, issue-type)` to identify duplicates.

- Conversation turns  
  - In CLAUDE.md: “When you reference a previous decision or finding, **refer back to it briefly** instead of restating the full original explanation.”

***

## 5. Use stricter output formats

- Hard caps and formats  
  - For each agent, specify:
    - Max N findings per severity (e.g. top 5 blockers/high only).  
    - Required fields only (no rambling prose).  
  - Example: “Return at most 10 findings; if there are more, group them as patterns instead of listing every instance.”

- Ask for ranked, not exhaustive, output  
  - E.g. “Give me the 3 most critical logic issues and 3 representative medium issues; you may mention that there are more of the same pattern without describing all of them.”

***

## 6. Share context via scratchpad, not chat

You’re already moving this way, but make it explicit:

- “If something might be useful later but is long (logs, full stack traces, large code samples), save it in `.scratchpad/debug/...` and **do not paste it**.”  
- The orchestrator then uses `grep` / `search` to pull *only* the parts needed for a given question, instead of carrying the whole thing in the prompt.

***

If you want, we can pick one concrete workflow (e.g. `/review` or `/debug`) and rewrite its command + agent specs to bake in strict caps (“N findings”, “no full file dumps”, “summary + pointer only”) so you get token control by construction, not just by habit.
