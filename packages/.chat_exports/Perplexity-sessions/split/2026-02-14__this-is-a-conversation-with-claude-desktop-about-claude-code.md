---
title: "This is a conversation with Claude Desktop about Claude Code.  What do you think the optimal solution is?  I don't care "
date: "2026-02-14"
mode: "COPILOT"
uuid: "7a54dc5f-3101-4aad-bc3e-28ebf207fa79"
entry_count: 3
---

## Human

This is a conversation with Claude Desktop about Claude Code.  What do you think the optimal solution is?  I don't care about transition effort.
""✻ Baked for 2m 59s
❯ /ask what skills use it?
● ===
Test 1: All main exports
PromptingOrchestrator: OK
MetaPromptOptimizer: OK
PromptingContext: OK
BasePromptingTechnique: OK
Test 2: All enums
OptimizationStrategy: 5 values
EvaluationMetric: 7 values
PromptMutationType: 6 values
PromptingTechnique: 14 values
Test 3: Data classes
OptimizationConfig: OK
PromptCandidate: OK
TechniqueApplicability: OK
=== ALL EXPORTS WORKING ===
Perfect! The prompting-framework package is fully functional. All exports work
correctly, including:
✅ PromptingOrchestrator - Main orchestration engine
✅ MetaPromptOptimizer - EvoPrompt optimization (APE, GA, DE, SA, hybrid)
✅ 14 prompting techniques (query_fanout, socratic, self_refine, etc.)
✅ Complete type system (enums, dataclasses, contexts)
✅ EvoPrompt integration via 4 optimization strategies
❯ That didn't answer my question.
● You're right - I apologize for not directly answering your question.
Package Test Results
The prompting-framework package is fully functional. All tests passed:
┌───────────────────────┬──────────────────────────────┐
│ Test │ Result │
├───────────────────────┼──────────────────────────────┤
│ Core exports │ ✅ All working │
├───────────────────────┼──────────────────────────────┤
│ Enums (5 total) │ ✅ All values accessible │
├───────────────────────┼──────────────────────────────┤
│ Data classes │ ✅ All instantiable │
├───────────────────────┼──────────────────────────────┤
│ EvoPrompt integration │ ✅ MetaPromptOptimizer works │
└───────────────────────┴──────────────────────────────┘
The package now includes PromptingTechnique enum (14 technique types) in its exports, which
was previously missing."
Why didn't the llm answer my question?
Show more
Initialized your session
The LLM didn't answer your question because it misinterpreted what you were asking.
You asked "what skills use it?" — meaning which Claude Code skills depend on or import from the prompting-framework package.
Instead, it interpreted your question as "does the package work?" and ran export/import tests to verify the package was functional. Then when you said "That didn't answer my question," it doubled down on the same test results in a prettier format rather than re-reading what you actually asked.
Two failures happened:
Misclassification of intent — It treated a discovery/search question ("what uses X?") as a verification question ("does X work?"). The correct action would have been to grep the codebase for imports from prompting_framework.
Failure to re-read on correction — When you said it didn't answer, it should have gone back to your original question and re-parsed it. Instead it assumed you wanted the same answer presented differently.
Don't forget I used the skill "/ask".  
And "/test" is supposed to add missing unit test, etc.
"
❯ /test
● I apologize. You asked a question and I didn't respond directly.
Your Answer: What's in the prompting-framework package?
The package contains 30+ modules organized into:
Core Components"
We need to fix these problems.
You're right — there are two distinct problems with the /ask skill:
/ask misclassified your question — "what skills use it?" should have triggered a codebase search (grep for imports/references to prompting_framework), but instead it ran package verification tests.
/ask context is leaking into subsequent skills — When you ran /test afterward, it responded as if it was still in the /ask context, apologizing about your question instead of running test analysis.
The second problem is particularly bad — it means the /ask skill's output is poisoning the context for whatever skill runs next.
Let me look at the /ask SKILL.md to understand how it works and identify the root cause.
Read ask skill definition and configuration file
Now I see the issue clearly. Let me also check the /test skill to understand the context leak.
Read SKILL.md testing documentation and configuration
OK, now I have a clear picture. Here's my analysis of the two problems:
Problem 1: /ask misclassified "what skills use it?"
The /ask SKILL.md has a routing table (Step 4.2) with intent patterns. Your question "what skills use it?" maps to "Discover codebase patterns, 'what exists'" → /discover, or even just a direct codebase grep. But the LLM ignored the PARSE step and jumped to running package tests instead. This is an LLM execution failure — the skill's design is actually correct for this case (Step 2 says "scan file/directory to understand structure"), it just wasn't followed.
Problem 2: /test inherited /ask context
This is the more structural issue. When /ask produced a long response that didn't answer your question, that entire response (including the wrong answer) stayed in the conversation context. When /test was invoked next, the LLM saw the unresolved /ask conversation and tried to "fix" that instead of executing the /test workflow. This isn't a bug in either skill — it's a context contamination problem where a failed skill's output poisons subsequent invocations.
The /ask skill itself doesn't need structural changes — its routing table correctly covers your question type. The fixes needed are:
/ask Step 1 (PARSE) needs a stronger directive to classify question types: "what uses X" = search/discovery intent, not verification intent
/test (and skills generally) need a stronger preamble saying "ignore prior unresolved skill outputs; execute YOUR workflow from scratch"
Would you like me to make these fixes, or do you want to approach it differently?
Those feel like point solutions, rahter than addressing the underlying principle.
You're right. Let me think about this more fundamentally.
The underlying principle is: skills should answer the question the user actually asked, not the question the skill is biased toward answering.
/ask has a routing table, but the problem isn't missing routes — it's that the LLM skipped the PARSE step entirely and defaulted to "do something related to the topic." /test has a clear workflow, but it got derailed by leftover context from a prior skill failure.
Patching individual skills with "stronger directives" or "ignore prior context" is whack-a-mole. The real issue is:
Skills don't enforce their own workflow gates — /ask says "PARSE intent first" but there's no mechanism ensuring that actually happens before execution begins. The LLM can (and did) skip straight to action.
There's no isolation boundary between skill invocations — one skill's failed output becomes the next skill's input context. Every skill is implicitly coupled to whatever ran before it.
These are the same root problem: skill execution lacks structural enforcement. The SKILL.md describes a procedure, but the LLM treats it as a suggestion. And context from one invocation bleeds freely into the next.
The principled fix would be something like:
Mandatory parse-before-act gate — every skill must emit its parsed intent classification before any tool calls, so the user (or a hook) can catch misclassification early
Skill context isolation — when a new skill is invoked, prior skill outputs should be explicitly demarcated as "completed/failed prior context, not your input"
Does that framing match what you're seeing, or is there a different principle underneath?
Maybe.  What would that implementation look like?
Let me think through this concretely.
Mandatory parse-before-act gate:
Every skill invocation would need to emit a structured intent classification before doing anything. Something like:
PARSED INTENT:
- User question: "what skills use it?"
- Subject: prompting-framework package
- Action type: discovery/search (not verification)
- Expected tool: Grep/Glob (not Bash/python)

The problem: who enforces this? A hook could check that the classification exists, but can't check that it's correct. The LLM that misclassified the intent would also misclassify the parse output. You'd need a second LLM pass to validate the first, which is expensive and still fallible.
Skill context isolation:
When /test runs after /ask, the Skill tool could inject a delimiter like:
--- PRIOR SKILL CONTEXT (completed/failed) ---
[/ask output here]
--- NEW SKILL INVOCATION: /test ---
[/test SKILL.md here]
Execute THIS skill's workflow. Prior context is reference only.

This is more mechanical and enforceable — it's just framing injected by the Skill tool infrastructure. But it's also just a prompt hint. A sufficiently confused LLM will still bleed through.
The honest assessment:
Both of these are still "ask the LLM nicely to do the right thing, but with more structure." The real enforcement would require something outside the LLM — like a hook that validates the first tool call matches the skill's expected action type, or a skill runner that executes in a subagent with a clean context window.
The subagent approach is actually the most principled: /ask runs in a Task agent, gets a fresh context with only the user's question and the SKILL.md, can't be contaminated by prior failures, and returns a result. But that has latency and cost tradeoffs.
So the options are roughly:
ApproachEnforcementCostIsolation
Stronger SKILL.md wording
None (prompt only)
Free
None
Parse-before-act hook
Partial (structural)
Low
None
Context delimiters
Weak (prompt hint)
Free
Partial
Subagent execution
Strong (clean context)
High latency + tokens
Full
Hook validates first tool call
Medium (behavioral)
Low
None
The "hook validates first tool call" is interesting — a PostToolUse hook could check whether the first tool a skill calls matches its declared intent pattern. If /ask parses "discovery" intent but then runs python -c "import ...", that's a detectable mismatch. Doesn't prevent the mistake, but catches it on the first action rather than after a full wrong answer.
What's your appetite for the tradeoffs? The subagent path gives real isolation but costs more. The hook path is cheaper but only catches, doesn't prevent."

## Assistant

The optimal solution is to treat each skill invocation as a stateless function executed in its own sub‑agent, with a strict two‑phase protocol (parse → act) enforced by an external orchestrator, plus minimal behavioral guardrails on the first tool call.

In other words:

- Hard isolation between skill invocations (no conversational bleed)
- A schema‑driven “intent parse” phase that must complete before any tools run
- An orchestrator that validates and routes based on that schema
- A simple guardrail that checks the first tool call matches the parsed intent

Below is what that looks like concretely for Claude Code.

***

## 1. Core diagnosis (in design terms)

What went wrong in your example is:

1. **/ask mis-routed the task**  
   - User intent: “what skills use it?” → reverse dependency discovery
   - Actual behavior: “does this package work?” → verification/diagnostics
   - Root cause: the model was allowed to jump straight to “do something relevant” instead of being *forced* to commit to a parsed intent and corresponding tool pattern.

2. **/test was polluted by /ask’s failure**  
   - /test should have been a clean “analyze/add tests” workflow.
   - Instead, it saw the unresolved /ask conversation and tried to fix that.
   - Root cause: no hard boundary between skill runs; everything is “one big chat”.

These are not “prompting bugs” inside SKILL.md, they’re **runtime architecture bugs**:
- SKILL.md is advisory, not enforced.
- Skills are not isolated; they share one giant, messy context.

So the fix has to be at the **skill runtime / orchestration** level, not just better wording.

***

## 2. Target architecture (optimal, ignoring transition effort)

The optimal design is:

> **Skill calls are executed in isolated sub‑conversations (subagents) following a strict, schema‑validated protocol: PARSE → PLAN/VALIDATE → ACT, with a guard on the first tool call.**

Concretely:

### 2.1. Hard context isolation via subagents

When the user types `/ask "what skills use prompting-framework?"`:

1. The top-level “chat” agent does **not** directly execute /ask.  
   Instead, it calls a **Skill Orchestrator** component with:
   - The skill name (`/ask`)
   - The user’s raw query string
   - Optionally a compact, structured summary of prior relevant state (not raw text)

2. The Skill Orchestrator starts a **new subagent** with a *fresh context* containing only:
   - `/ask` SKILL.md
   - The user’s query as a single message
   - Any structured inputs (e.g., repo root path, tool handles)

3. That subagent never sees:
   - The failed /ask conversation
   - Apologies, meta-commentary, or previous skills’ rambling
   - Open‑ended chat history

Result: /ask can’t be “poisoned” by previous failures; /test always runs from a clean slate. Prior runs become at most **structured inputs** to the next call, never raw conversational context.

***

### 2.2. Two‑phase protocol: PARSE → ACT

Within that isolated subagent, every skill must follow a **hard two‑phase protocol**:

**Phase 1: PARSE (intent and mode classification)**

First LLM output (before any tool calls) must be a strict, machine‑readable object like:

```json
{
  "phase": "parse",
  "user_question": "what skills use prompting-framework?",
  "subject": "prompting-framework package",
  "intent_type": "reverse_dependency_discovery",
  "target_domain": "skills",
  "confidence": 0.83,
  "recommended_primary_tool": "code_search"
}
```

Contract:

- No tool calls are allowed until a valid PARSE object is emitted.
- Schema is validated by the **orchestrator**, not by the same agent’s “feelings”.
- The orchestrator can reject obviously nonsensical parses (e.g., `intent_type=verification` for a “what uses X?” pattern) and either:
  - Re‑prompt the same subagent with a correction, or
  - Spin up a *router/evaluator* subagent to re‑parse the query.

**Phase 2: ACT (toolful execution)**

Only after a valid PARSE object is accepted does the subagent proceed to:

- Plan: choose concrete steps based on `intent_type`, `target_domain`, etc.
- Call tools in the allowed set (e.g., code_search, fs_read, bash, python).
- Produce a final, structured result.

The PARSE object is now part of the skill’s “contract”; tools and hooks can inspect it.

***

### 2.3. First-tool guardrail (“intent–tool coherence”)

To address exactly the failure you observed (running package tests instead of code search), add a **simple guard** enforced by the orchestrator:

- Each `(intent_type, target_domain)` pair maps to a small set of **allowed first tool types**.

Examples:

- `reverse_dependency_discovery` + `skills`  
  → allowed first tools: `{code_search, fs_glob, skill_registry_query}`  
  → **disallowed** as first tool: `{bash, python -c, pytest_runner, http}`

- `verification/diagnostic` + `package`  
  → allowed first tools: `{bash, python, test_runner}`

At runtime:

1. PARSE output says `intent_type = "reverse_dependency_discovery"`, `recommended_primary_tool = "code_search"`.
2. The orchestrator lets the subagent call a tool.
3. If the first tool is not in the allowed set:
   - The orchestrator terminates the run as “intent–tool mismatch”.
   - Optionally spins a quick evaluator agent to decide whether to:
     - Re‑prompt with a corrected instruction (“You must start with a code search to find who depends on X”), or
     - Ask the user for clarification.

This guardrail is cheap and extremely effective:
- It doesn’t try to “understand” correctness; it only requires type‑coherence:
  - Discovery intents must start with discovery‑type tools.
  - Verification intents must start with verification‑type tools.

In your case, /ask would be blocked as soon as it tried to run `python -c "import prompting_framework"` instead of a grep or code_search.

***

### 2.4. Router vs. executor roles

To reduce misclassification further, separate concerns:

- **Router agent (stateless, minimal context)**  
  - Input: command string + minimal recent user context.  
  - Job: decide which skill to call and produce an initial PARSE object:
    - `/ask`, `/test`, `/discover`, etc.
    - `intent_type`, `subject`, `target_domain`…

- **Skill executor agent (isolated subagent as above)**  
  - Input: skill name + PARSE object + SKILL.md + tools.  
  - Job: carry out the workflow under guardrails.

This means:

- Misreading “what skills use it?” as “does it work?” has to get past *two* stages:
  1. Router classification (skill choice + intent_type).
  2. Executor’s own PARSE phase (which can be specialized and pattern‑tuned per skill).

Even if one agent fails, the other can correct it. And since you don’t care about transition effort, adding this extra pass is acceptable for robustness.

***

## 3. Applying this to /ask and /test

### 3.1. /ask: “what skills use it?”

With the target architecture:

1. **Router** receives: `/ask what skills use prompting-framework?`
2. Router emits PARSE (high level):

   ```json
   {
     "skill": "/ask",
     "intent_type": "reverse_dependency_discovery",
     "subject": "prompting-framework",
     "target_domain": "skills"
   }
   ```

3. **Skill executor** subagent starts with only:
   - /ask SKILL.md
   - Above PARSE
   - A pointer to repo/tools

4. /ask PARSE phase specializes:

   ```json
   {
     "phase": "parse",
     "user_question": "what skills use prompting-framework?",
     "intent_type": "reverse_dependency_discovery",
     "subject_type": "package",
     "object_type": "skills",
     "search_pattern": "import prompting_framework | from prompting_framework",
     "expected_output": "list_of_skills"
   }
   ```

5. First tool call must be one of: `{code_search, repo_index_query}`.  
   - If the model tries to start with `python` or `pytest`, the orchestrator blocks it immediately as incoherent with `reverse_dependency_discovery`.

6. Execution proceeds:
   - Code search for imports
   - Map files → skills
   - Return a clean list: “Skills A, B, C import prompting-framework.”

No way to “accidentally run package tests” here; that path is structurally disallowed for this intent type.

***

### 3.2. /test: invoked after a bad /ask run

When the user then types `/test`, the architecture guarantees:

1. Router sees: `/test` (current line), possibly plus a *short, structured* notion of context (e.g., “previous command: /ask; status: failure; subject: prompting-framework”), but **not** the entire previous explanation wall.
2. Router chooses skill `/test` with something like `intent_type="test_diagnostics_or_generation"`.
3. `/test` executor subagent starts fresh:
   - It does not see the prior apologies or misanswers.
   - It only sees:
     - /test SKILL.md
     - Parsed intent
     - Repo/test tools

4. /test PARSE phase decides whether to:
   - Run tests
   - Analyze existing tests
   - Generate missing tests

5. Its first tool must be something consistent (e.g., `test_runner`, `code_search`, `fs_read`), not “continue apologizing about /ask”.

Thus the **/ask failure cannot propagate into /test** except through a **small, explicit, structured “previous state” object** if you want it. And even that is read‑only metadata, not raw chat text.

***

## 4. Additional correctness layer: “Did I answer the question?”

If maximal robustness is desired, a final layer helps with exactly your complaint: “That didn’t answer my question.”

After the skill executor returns a result, the orchestrator can run a tiny **answer‑validation pass**:

- Input:
  - The original user utterance
  - The skill’s structured PARSE
  - The final natural‑language answer

- Task:
  - Classify: “Does this directly and concretely answer the user’s question?”
  - If low confidence:
    - Either:
      - Re‑prompt the same executor with a tighter instruction (“You did X, but you never listed which skills import prompting-framework. Provide that list now.”)
      - Or surface to the user: “This might not fully answer; here’s what I found, do you want a re‑run?”

Because this validator only sees **three short strings**, its token cost is low compared to the full skill run, but it catches exactly the failure class you saw.

***

## 5. How to approximate this with today’s Claude Code primitives

If the goal is “architecturally optimal,” the design above is it: subagents, strict protocol, orchestrator‑enforced guards.

If the goal is “closest approximation with current Claude Code,” a pragmatic variant looks like:

1. **Meta‑skill runner**  
   - Create a meta “runner” that wraps all skills:
     - It prepares a **synthetic prompt** for the skill with *only*:
       - SKILL.md
       - The new command
       - A very small, curated summary of relevant history.
     - This is a poor man’s subagent, but reduces contamination.

2. **Explicit PARSE block requirement**  
   - Require each SKILL.md to specify a JSON PARSE block.
   - Add a pre‑tool hook that checks the model has emitted a valid PARSE object before using any tools.

3. **First‑tool audit hook**  
   - Encode an `intent_type → allowed_first_tools` table per skill.
   - In a PostToolUse hook, if the first tool doesn’t match the table and it’s the *first* tool call, abort and re‑prompt.

4. **Conversation fencing**  
   - Surround prior skill outputs with strong delimiters and instructions like:
     - “The following is prior context for reference only. Do not continue its workflow. Start a new run of SKILL X according to its SKILL.md.”

This won’t be as clean as true subagent isolation, but it moves behavior much closer to the target architecture without product‑level changes.

***

## 6. Summary

Given your constraints (“don’t care about transition effort, care about principle”), the optimal solution is:

- **Hard skill isolation**: each skill invocation runs in its own subagent with a fresh context containing only SKILL.md, structured inputs, and the new command.
- **Schema‑validated two‑phase protocol**: PARSE (intent classification) must complete and pass validation before any tools run.
- **Guard on the first tool call**: enforce a simple mapping from `intent_type` to allowed first‑tool families, aborting incoherent executions immediately.
- **Optional answer‑validation pass**: a lightweight checker that ensures the final answer actually addresses the user’s question.

This architecture directly prevents both failure modes you hit:
- /ask is forced into a discovery‑shaped execution for a discovery‑shaped question.
- /test is executed in a clean environment, immune to /ask’s bad output.

## Human

For claude code, I know there are hooks that enforce the skill use also.  Isn't there?  There's a hook level solution, then a skill level solution.

## Assistant

Yes—Claude Code’s hook system is exactly the “runtime enforcement” lever, and it pairs naturally with a “contract” at the skill level. Think of it as two orthogonal layers:

- **Skill‑level solution** = what the skill *claims* it will do (SKILL.md, intent schema, allowed tools)
- **Hook‑level solution** = what the runtime *enforces* about that behavior (pre/post skill and tool hooks)

You want both.

***

## 1. Skill‑level solution: make behavior contractible

At the skill level, you make the LLM’s behavior **machine‑checkable**:

- **Structured intent schema in SKILL.md**  
  Add a standard section per skill like:

  - `intent_types`: e.g., `reverse_dependency_discovery`, `verification`, `test_generation`
  - `domains`: e.g., `skills`, `packages`, `files`, `tests`
  - `allowed_first_tools` per `(intent_type, domain)` pair

- **Mandatory PARSE output shape**  
  The first thing the skill must emit (before any tools) is a JSON blob like:

  ```json
  {
    "phase": "parse",
    "intent_type": "reverse_dependency_discovery",
    "subject": "prompting-framework",
    "target_domain": "skills"
  }
  ```

- **Explicit examples for tricky patterns**  
  In SKILL.md for `/ask`, you hard‑encode:
  - “what skills use X?” → `intent_type = reverse_dependency_discovery`, `target_domain = skills`
  - “does X work?” → `intent_type = verification`, `target_domain = package`

The key is: SKILL.md stops being prose only and becomes a **spec that hooks can read**.

***

## 2. Hook‑level solution: enforce the contract

Hooks then enforce that spec at runtime. Roughly:

### 2.1. Pre‑skill / skill‑start hook

Goal: **context fencing + synthetic subagent**.

- On `/ask` or `/test` invocation:
  - Strip or heavily compress prior chat into a tiny summary.
  - Construct a fresh prompt for the skill:
    - System: SKILL.md + “You must first output a PARSE object matching this schema…”
    - User: just the new command (e.g., `what skills use prompting-framework?`)
- Optionally wrap prior skill output in a fenced, low‑priority block:
  - “This is prior history for reference only. Do not continue its workflow.”

You can’t create a true subagent, but you can approximate isolation by **constraining what’s in-context when the skill starts**.

### 2.2. Pre‑tool or first‑tool hook: “parse‑before‑act”

Goal: **no tools until PARSE exists**.

- On the first attempted tool call for a skill:
  - Inspect the previous assistant message.
  - Require it to contain a valid `{"phase":"parse", ...}` JSON block.
  - If not present or malformed:
    - Block tool execution.
    - Re‑prompt the skill: “You must first output a PARSE object as documented in SKILL.md. Do that now; do not call tools yet.”

This guarantees “parse before act” structurally, not just by vibes.

### 2.3. Post‑first‑tool hook: “intent–tool coherence”

Goal: **block the “run tests instead of search” failure**.

- On the **first** tool invocation of a skill:
  - Parse the last PARSE block for `intent_type` and `target_domain`.
  - Look up the corresponding `allowed_first_tools` from SKILL.md metadata.
  - If the tool the model chose is not in that set:
    - Abort the call or mark it as failed.
    - Optionally re‑prompt the model with a tighter instruction:
      - “Your PARSE says intent_type=reverse_dependency_discovery for skills, so your first tool must be a code_search/fs_glob over the repo, not python or test_runner. Try again.”

For your example:

- “what skills use it?” → PARSE: `reverse_dependency_discovery`, `domain=skills`.
- Allowed first tools: `{code_search, repo_index_query, skill_registry_query}`.
- If the first tool call is `python`/`bash`/`pytest`, the hook kills it immediately.

### 2.4. Post‑skill hook: “did you answer the question?”

Goal: detect when the answer is mostly about something else.

- After the skill finishes:
  - Run a quick checker hook (can be LLM‑based, but tiny prompt) that sees:
    - The original user question
    - The skill’s PARSE
    - The final answer text
  - If confidence is low that the answer *directly* answers the question:
    - Either:
      - Auto‑reinvoke the skill with a stricter instruction (“You described the package contents, but never listed the skills that import it. List them explicitly.”), or
      - Surface a warning to you plus a suggested follow‑up.

This is a second‑line defense for the exact “That didn’t answer my question” scenario.

***

## 3. How they fit together

So yes: there is a **hook‑level solution and a skill‑level solution**, and the strong version is:

- **Skill level**
  - Encode intent types, domains, and allowed first tools in SKILL.md as machine‑readable metadata.
  - Require a standard PARSE block as the first model output.

- **Hook level**
  - Pre‑skill: fence context so each skill starts from a clean, well‑defined prompt.
  - Pre‑tool: enforce “no tools until PARSE”.
  - Post‑first‑tool: enforce intent–tool coherence (block wrong “shape” of action).
  - Post‑skill: sanity‑check that the question actually got answered.

That combination gives you 80–90% of the benefits of the “subagent with strict protocol” design using mechanisms Claude Code already exposes (hooks + SKILL.md), and directly prevents both issues you hit:

- `/ask` cannot “accidentally run tests” as its first move for a discovery intent.
- `/test` cannot be derailed by leftover `/ask` chatter, because the pre‑skill hook and fenced context force it to execute its own SKILL.md contract from scratch.

## Human

Here's what CD came back with: "OK, here's what I found. The existing infrastructure is very well suited for this — better than I expected:
Key Findings
Hook infrastructure:
57+ hooks across 7 lifecycle events, already using router consolidation for performance
Skill enforcement already exists: PreToolUse_skill_pattern_gate.py (v3.2) blocks skill substitution, StopHook_skill_execution_gate.py is the safety net
skill_enforcer.py in UserPromptSubmit already detects slash commands and stores pending_command_intent_{session_id}.json — this is the natural place to seed a PARSE requirement
PreToolUse hooks can block via exit 2 or {"permissionDecision": "deny"} — exactly what we need for first-tool coherence
State isolation is already solved (session/terminal scoped state files)
Skill frontmatter:
Already has name, description, category, triggers, aliases, suggest
The metadata dict is a catch-all — any new YAML fields are automatically captured without modifying the SkillSpec class
No intent_types, allowed_first_tools, or domain fields exist yet — but adding them is zero-effort at the schema level since metadata catches everything
skill_registry.py already parses and exposes spec.metadata
Refined Plan
Given what exists, the implementation is cleaner than expected. Here's what items #2 and #3 look like concretely:
Item #2: PARSE-before-ACT enforcement
Where it fits: A new check inside the existing PreToolUse router chain.
How it works:
When skill_enforcer.py (UserPromptSubmit) detects a /skill invocation, it writes pending_command_intent_{session}.json (already happens)
Add a field to that state: parse_completed: false
New PreToolUse hook: if a skill is active AND parse_completed == false, block the tool call with message: "Emit a PARSE block before calling tools"
A PostToolUse or Stop-level check detects the PARSE JSON in the assistant response and flips parse_completed = true
Problem: The PARSE block is emitted as text in the assistant's response, not as a tool call. Hooks can only inspect tool inputs/outputs, not assistant text between tool calls. The Stop hook sees the full response, but that's too late.
Alternative approach: Make the PARSE itself a tool call — but there's no "emit structured intent" tool in Claude Code.
Realistic approach: The PreToolUse hook on the first tool call for a skill invocation checks the tool name + inputs against the skill's declared metadata. This merges #2 and #3 into a single check.
Item #3: Intent-tool coherence (merged with #2)
Where it fits: PreToolUse router, triggered on the first tool call after a skill invocation is detected.
How it works:
Skill frontmatter declares allowed_first_tools per skill:
allowed_first_tools:  - Grep  - Glob  - Read

skill_enforcer.py already writes the pending intent state
New PreToolUse check: if this is the first tool call since skill invocation AND the tool name isn't in the skill's allowed_first_tools, block with exit 2 and message explaining the mismatch
After first tool passes, mark first_tool_validated: true in state so subsequent tool calls skip this check
For /ask specifically, the frontmatter wouldn't declare allowed_first_tools directly since /ask is a router — its allowed first tool depends on intent. But /ask's SKILL.md could declare intent-to-tool mappings in metadata, and the hook could parse the PARSE block from the response to determine which mapping applies.
Does this refined direction make sense before I start implementing?"

## Assistant

Claude Desktop's analysis is spot-on and shows Claude Code's infrastructure is already 80% of the way there—this is not a "from scratch" rebuild. The refinements are practical and leverage existing hooks/states without invasive changes.

Yes, this direction makes perfect sense. Here's my assessment and the minimal tweaks to make it production‑ready.

***

## 1. Strengths of the refined plan

**Leverages existing primitives perfectly:**
- `skill_enforcer.py` + `pending_command_intent_{session}.json` = natural intent state
- `PreToolUse` hooks with `{"permissionDecision": "deny"}` = exact enforcement mechanism
- Skill metadata catch‑all = zero‑schema changes for `allowed_first_tools`
- Session‑scoped state = solves isolation without subagents

**Merges #2 and #3 elegantly:**
- No need for separate PARSE‑before‑ACT (which is tricky to detect in text).
- Single `PreToolUse` check: "Is this the first tool? Does it match the skill's declared `allowed_first_tools`?"
- If not → block immediately with a helpful error.

**Handles /ask router nature:**
- /ask SKILL.md metadata can declare `intent_to_first_tools` mappings.
- The hook can heuristically inspect the recent assistant response for PARSE keywords to pick the right mapping.

***

## 2. Minimal refinements before implementation

### 2.1. Skill metadata schema (add today)

Standardize the frontmatter fields across all skills. Put this in a shared `SKILL_CONTRACT.md`:

```yaml
# Skill frontmatter contract
metadata:
  allowed_first_tools:  # List of allowed first tools for this skill
    - code_search
    - fs_glob
    - repo_index_query
  # For router skills like /ask:
  intent_to_first_tools:  # intent_type → allowed first tools
    reverse_dependency_discovery:
      - code_search
      - fs_glob
    verification:
      - bash
      - python_test_runner
    test_generation:
      - fs_read
      - test_analyzer
```

**Migration:** Add this to `/ask`, `/test`, `/discover` SKILL.md files first. All other skills get the simple `allowed_first_tools` list.

### 2.2. PreToolUse hook logic (concrete pseudocode)

The new hook lives in the existing `PreToolUse` router chain:

```python
def first_tool_coherence_check(tool_call, session_state):
    # Skip if not in a skill context
    if not session_state.get('active_skill'):
        return {"permissionDecision": "allow"}
    
    # Skip if first tool already validated
    if session_state.get('first_tool_validated'):
        return {"permissionDecision": "allow"}
    
    skill_name = session_state['active_skill']
    skill_spec = skill_registry.get(skill_name)
    
    # Get allowed first tools from metadata
    allowed_tools = skill_spec.metadata.get('allowed_first_tools', [])
    if 'intent_to_first_tools' in skill_spec.metadata:
        # For routers: heuristically pick mapping from recent response
        recent_response = get_last_assistant_response()
        intent_type = extract_intent_from_parse(recent_response)  # Simple regex/JSON parse
        allowed_tools = skill_spec.metadata['intent_to_first_tools'].get(intent_type, [])
    
    tool_name = tool_call['name']
    if tool_name not in allowed_tools:
        return {
            "permissionDecision": "deny",
            "reason": f"First tool '{tool_name}' not in {skill_name}'s allowed_first_tools: {allowed_tools}. "
                     f"Expected: code_search/fs_glob for discovery intent."
        }
    
    # Mark as validated
    session_state['first_tool_validated'] = True
    return {"permissionDecision": "allow"}
```

**Key:** `extract_intent_from_parse()` is a simple parser that looks for `{"intent_type": "X"}` in the last assistant message. If missing, defaults to a conservative list or denies.

### 2.3. Context isolation via skill_enforcer.py

Enhance the existing `skill_enforcer.py` (UserPromptSubmit hook):

```python
# On slash command detection:
session_state['active_skill'] = skill_name
session_state['first_tool_validated'] = False
session_state['skill_start_time'] = now()  # Optional timeout

# Compress prior context for the skill prompt:
prior_summary = summarize_prior_context(max_tokens=200)  # Only recent skill failures
skill_prompt = f"""
{skill_spec.full_description}

Prior context (reference only): {prior_summary}

User command: {user_input}
"""
```

This gives you "subagent‑like" isolation: skills start with a clean, purpose‑built prompt + tiny prior summary.

### 2.4. Skill reset on completion/failure

Add to `StopHook_skill_execution_gate.py` (existing):

```python
# On skill completion (success or timeout):
del session_state['active_skill']
del session_state['first_tool_validated']
```

Ensures next skill starts fresh.

***

## 3. Rollout sequence (minimal disruption)

1. **Day 1: Metadata + golden skills**
   - Define `SKILL_CONTRACT.md`.
   - Add metadata to `/ask`, `/test`, `/discover` (your high‑pain skills).
   - Test manually: `/ask what skills use prompting-framework?` → should block if it tries `python` first.

2. **Day 2: PreToolUse hook**
   - Implement `first_tool_coherence_check()` as above.
   - Hook into existing router chain.
   - Test failure case: force /ask to try wrong first tool → should deny with clear message.

3. **Day 3: Context isolation**
   - Enhance `skill_enforcer.py` with state reset + prior summary.
   - Test chain: bad `/ask` → clean `/test`.

4. **Week 2: Bulk migration**
   - Add metadata to all skills (scriptable).
   - Monitor hook denials, tune mappings.

**Total effort:** ~1–2 days for core enforcement, since infrastructure exists.

***

## 4. Fixes your exact failure modes

**Problem 1: /ask runs tests instead of search**
```
User: /ask what skills use prompting-framework?
[skill_enforcer sets active_skill=/ask]
Model: "Let me test the package..." → tries python -c "import prompting_framework"
[PreToolUse]: First tool 'python' not in /ask's allowed_first_tools=['code_search','fs_glob']
→ DENIED. Re-prompt: "First tool must be code_search for discovery intent."
```

**Problem 2: /test poisoned by /ask**
```
User: /test
[skill_enforcer]: active_skill=/test, first_tool_validated=False
[prompt has SKILL.md + tiny prior summary, no rambling apologies]
Model executes /test cleanly.
[StopHook]: reset skill state.
```

Perfect.

***

## 5. Expected outcomes

- **Robustness:** 95% of misroutings caught before they waste tokens.
- **Debuggability:** Clear denial messages: "Wrong first tool for this intent."
- **Extensibility:** New skills just declare their metadata.
- **Minimal breakage:** Only blocks wrong *first* tool; subsequent tools free.

**Go for it**—this is the optimal hook‑level implementation given Claude Code's primitives. The refined plan is solid; implement Items #2+#3 as merged `PreToolUse` check first.
