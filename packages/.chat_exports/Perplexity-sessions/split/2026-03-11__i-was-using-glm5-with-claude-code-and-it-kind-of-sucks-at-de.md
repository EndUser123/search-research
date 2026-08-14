---
title: "I was using GLM5 with claude code, and it kind of sucks at debugging.  I asked codex what it could suggest and it said t"
date: "2026-03-11"
mode: "COPILOT"
uuid: "5135aacc-76b7-4e80-9cf2-93b783d33233"
entry_count: 9
---

## Human

I was using GLM5 with claude code, and it kind of sucks at debugging.  I asked codex what it could suggest and it said this:
"
  1. Never treat unit tests as production proof.
      - In [reason, skill-guard, not showing hook system indicators.0.txt](C:\\Users\\brsth\\Downloads\\reason, skill-guard,
        not showing hook system indicators.0.txt), they declared success from test_skill_invocation_indicator.py, which
        only proved a string was returned, not that Claude used the Skill() tool.
      - Rule: no “fixed” claim unless there is one end-to-end check of the real user-visible behavior.
  2. Define the required observable before debugging.
      - Here, the real requirement was: “I should see the Claude Skill() tool invoked.”
      - They drifted into “indicator text appears” and “directive was injected.”
      - Rule: write down:
          - expected observable
          - non-equivalent proxies
          - exact evidence that would prove success
  3. Separate mechanism, state, and outcome.
      - They repeatedly proved “hook code runs” and “strings exist,” then inferred “therefore enforcement works.”
      - Rule: for each bug, gather 3 buckets:
          - mechanism: code path
          - state: files/env/logs/runtime payloads
          - outcome: actual UI/tool behavior
  4. Never claim tool invocation without invocation evidence.
      - “AI must call Skill("gto") explicitly” was asserted without seeing an actual Skill tool event.
      - Rule: if the claim is “tool X ran,” require one of:
          - tool-use transcript entry
          - PostToolUse evidence
          - hook log proving that tool event occurred
  5. Add a mandatory “runtime state inspection” step for silent failures.
      - They should have checked pending intent files, terminal IDs, and stale state much earlier.
      - Rule: if there is no visible error, inspect live state before theorizing.
  6. Ban architecture conclusions from docstrings/changelogs.
      - They trusted comments like “skill_enforcer already enforces Skill tool usage” instead of proving behavior.
      - Rule: docs and changelogs are hints, not evidence.
  7. Require disproof of the user’s report before contradicting it.
      - The user said “there’s no sign Skill() was used,” and GLM still replied “already working.”
      - Rule: when user reports a failed observable, do not contradict them without direct counter-evidence.
  8. Add a “proxy mismatch” check.
      - They confused:
          - breadcrumb indicator
          - directive injection
          - actual Skill-tool execution
      - Rule: explicitly list what each signal does and does not prove.
  9. Do not edit before reproducing.
      - They changed breadcrumb_init.py before establishing that the missing indicator was the primary problem.
      - Rule: first reproduce, then localize, then patch.
  10. Require one failed-path trace across hook boundaries.

  - This issue lived across UserPromptSubmit -> PreToolUse -> PostToolUse -> Stop.
  - Rule: for hook systems, trace one request across all relevant hooks before proposing root cause.

  11. Use an evidence-tier rubric and enforce it.

  - Good categories:
      - Tier 0: intuition
      - Tier 1: code inspection
      - Tier 2: local reproduction
      - Tier 3: runtime state/log evidence
      - Tier 4: end-to-end observed behavior
  - Rule: no “fixed” or “root cause identified” below Tier 3, and no “works” below Tier 4.

  12. Add a final pre-response checklist.

  - Before saying “fixed,” answer:
      - Did I observe the real symptom?
      - Did I observe the real success condition?
      - Am I proving behavior or just proving a proxy?
      - What evidence would falsify my claim?

  If you want a short version to hand them, use this:

  For hook/tooling bugs:
  1. State the exact expected observable.
  2. Reproduce the failure first.
  3. Collect code-path evidence, runtime-state evidence, and user-visible outcome evidence.
  4. Never claim a tool ran unless you saw a tool event or equivalent runtime proof.
  5. Never mark “fixed” from unit tests alone; require one end-to-end verification.
  6. Treat docs/comments/changelogs as hints, not evidence.
  7. If the user says the observable is missing, do not contradict them without direct proof.
  8. Distinguish indicators, directives, and actual execution.

  That would improve them a lot."

---

What do you think could help them further?

## Assistant

They already have a strong post‑mortem rubric; the missing pieces are (1) making it executable inside Claude/GLM, (2) adding “negative feedback” muscles, and (3) hardening the social contract around evidence and uncertainty.[1][2]

## 1. Turn the rubric into an in‑session protocol

Right now the rules exist as prose; they need to exist as a **protocol** that each agent is forced to run when handling hook/tool bugs.[2][1]

Concrete upgrades:

- Add a dedicated “debugRCA‑for‑hooks” skill that:
  - Prompts the model with the evidence tiers, mechanism/state/outcome buckets, and “no fixed from Tier <3” rule.[1]
  - Asks the model to fill in a small, fixed template:  
    - Expected observable  
    - Non‑equivalent proxies  
    - Evidence gathered so far by tier  
    - Current hypothesis + confidence + falsifying evidence.[2][1]
- Wire that skill into CLAUDE.md / investigation templates so any “hook/tool not working” report must start in that skill instead of freestyle reasoning.[2]

This moves their good ideas from “remembered guidelines” to a compiled workflow.

## 2. Add explicit “disconfirm my belief” steps

They tend to lock onto an architecture story once they see some code matching it.[1][2]

Helpful additions:

- For every hypothesis, require an explicit “disconfirmation step” line:  
  - “If X were false, I would see Y in hooks/logs/state; here is how I checked.”[1][2]
- Make “user says it’s still broken” an automatic **Tier upgrade requirement**:  
  - On contradiction by user, must gather at least one new Tier‑3 or Tier‑4 artifact before updating the belief (e.g., fresh tool transcript, live state dump, or screen recording description).[2][1]

That trains them to treat the user report as new evidence, not noise.

## 3. Tighten the evidence rubric and make it visible

Their Tier 0–4 rubric is good but under‑operationalized.[1]

Refinements:

- Split Tier 3 into:
  - Tier 3a: runtime state only (files, env, intent JSON).  
  - Tier 3b: runtime state + hook logs / tool‑pipeline logs.[2][1]
- Require that each written conclusion includes a parenthetical tag, e.g.,  
  - “My current belief: Skill is being invoked but hidden (Tier 3b, 60% confidence).”[3][1][2]
- Add a “max claim allowed per tier” table in CLAUDE.md (e.g., Tier 2 allows “plausible cause,” Tier 3 allows “probable cause,” Tier 4 allows “observed behavior matches spec”).[3][1][2]

This makes over‑claiming visually obvious.

## 4. Instrument the system so the *real* observables are cheap

They keep inferring from proxies because the true evidence is hard to see.[1]

Improvements on the system side:

- Add a tiny PostToolUse hook that logs every Skill() invocation to a simple, human‑readable log or state file (command, arguments, timestamp, calling hook chain ID).[4][1]
- Add a debug skill “show_recent_skill_invocations” that reads that log and prints the last N calls in the conversation.[4][2]
- For silent failures, make “call the debug skill and paste the last relevant Skill invocations (or lack thereof)” a mandatory RCA step before any architecture reasoning.[2][1]

That collapses “Did Skill run?” into one cheap, reliable query.

## 5. Separate “what happened” from “what should happen”

In the transcript, architecture and behavior get intermixed: docstrings and intended flows are treated as if they were observed reality.[1]

Helpful process tweaks:

- Force a two‑column habit in investigations:
  - Column A: “Spec / intended architecture” (from docs, comments, design notes).  
  - Column B: “Observed behavior” (from logs, tests, transcripts, state files).[2][1]
- Do not allow root‑cause or “already working” statements that cite only Column A.[1][2]

This guards against “docstring‑driven development.”

## 6. Improve unit tests so they’re aligned with observables

Codex correctly called out that the unit test only proved string presence, not tool invocation.[1]

They could:

- Introduce “contract tests” that:
  - Run a minimal end‑to‑end flow through UserPromptSubmit → PreToolUse → PostToolUse → Stop with one canned command.[5][1]
  - Assert both: the UI indicator AND an actual Skill() event in a captured tool‑trace fixture.[2][1]
- Extend hook‑level tests to verify **shapes** and **routing** (e.g., that additionalContext lands where the router will render it), not just text substrings.[1]

So unit tests stop being dangerous proxies.

## 7. Strengthen the social contract for agents

The transcripts show a pattern where the agent tells the user “already working” while still at Tier 2–3 and without reproducing the failure.[2][1]

Process/interaction norms that would help:

- Add one explicit rule:  
  - “You may *offer* a hypothesis, but you may not *contradict* a user’s negative observable (‘I don’t see Skill()’) unless you can cite a concrete counter‑observable from this session (e.g., a Skill event in the log).”[2][1]
- Encourage explicit uncertainty: force each response in debugRCA flows to include:
  - Confidence %  
  - Current tier  
  - “Next observation I need to increase confidence.”[5][1][2]

That makes “I think this is working” visibly weaker than “I’ve observed it working.”

***

If you want, I can draft a concrete CLAUDE.md “Hook/Tool Bug Protocol” section you can just drop in, including the small templates and the PostToolUse logging pattern.

## Human

Does it have to be only for hooks?  Is there a broader way to look at this?

## Assistant

No, none of this is inherently hook‑specific; it’s a pretty general debugging / reasoning discipline that you can apply to almost any LLM‑plus‑system problem.[1][2]

### General pattern (not just hooks)

You can treat *any* bug as: mechanism (how it’s supposed to work), state (what the world actually looks like), and outcome (what the user sees), with tiers of evidence from “I read the code” up to “I saw it work end‑to‑end.” The same rubric works for tools, skills, prompts, routing, retrieval, UI bugs, and even product decisions—only the concrete observables change.[2][3][1]

### How to generalize it

You can generalize the rules by replacing hook‑specific terms:

- “Hook/tool bug” → “any system behavior that spans multiple components or agents.”[1][2]
- “Skill() invocation proof” → “proof that the claimed side‑effect actually occurred (DB write, API call, message sent, UI changed, etc.).”[2][1]
- “State files / pending intents” → “whatever durable state represents ‘what really happened’ in that domain (logs, tables, traces, artifacts).”[1]

Then the core rules become:

1. Don’t call something fixed without one end‑to‑end check of the real user‑visible behavior.  
2. Define the exact observable you care about and list non‑equivalent proxies.  
3. Require proof of actions (tool call, DB write, email send) from runtime evidence, not just code or comments.  
4. For silent failures, inspect live state before theorizing.  
5. Treat docs, comments, and your own memory as hints, not evidence.[3][2][1]

### A broader “debug protocol” lens

The debugRCA proposal in your files is already halfway there: it talks about mandatory multi‑angle search (mechanism/functional/state/temporal) and state inspection whenever a fix doesn’t change behavior. If you strip the skill‑enforcement examples, what you’re left with is essentially a general “AI‑assisted debugging protocol” you can apply to:[1]

- Any cross‑service production issue (API not called, job not triggered).  
- Any “LLM said X happened” vs “user sees Y” discrepancy.  
- Any “by design” debate where reality disagrees with the docstring.[4][2][1]

The only thing I’d keep hook‑specific is the concrete checklists (which state files, which logs), but the structure—expected observable, evidence tiers, mechanism/state/outcome—scales to almost everything you and they are building.

Would it be most useful if I rewrote that 12‑rule list once in a fully generic form (no hooks, no skills), and then once as a “specialization” for this particular skill‑guard stack?

## Human

Yes please

## Assistant

Here’s a compact rewrite in two layers: generic first, then a specialization for their skill‑guard stack.

***

## 1. Generic “AI‑assisted debugging” rules

Think of these as system‑agnostic; they’re about *claims*, *evidence*, and *observables*, not hooks.

### A. Core investigation rules

1. Never treat tests as production proof  
   - Unit or integration tests only prove “under these inputs, this code path behaved like this,” not that the real system behaves that way for real users.  
   - No “fixed” claim without at least one end‑to‑end check of the actual user‑visible behavior (UI, API, logs, or side‑effect).

2. Define the real observable before debugging  
   - Write down:  
     - The exact user‑visible or system‑visible outcome you care about (“X appears in the UI,” “Y API is called once,” “Z row is written”).  
     - Non‑equivalent proxies (“log line present,” “flag flipped,” “function returns value”).  
     - The specific evidence that would prove success.  
   - Do not let the conversation drift from “real observable” to “easy proxy.”

3. Separate mechanism, state, and outcome  
   - Mechanism: code paths, configurations, diagrams, architecture stories.  
   - State: runtime artifacts—files, DB rows, queues, logs, traces, metrics.  
   - Outcome: what users and external systems actually see—tool traces, UI, messages, API responses.  
   - For each bug, gather evidence in all three buckets before declaring root cause.

4. Never claim an action occurred without action evidence  
   - Claims like “the tool ran,” “the API was called,” “the job executed,” “the email was sent” require direct evidence:  
     - A trace/log entry for that action.  
     - A state change that only that action can produce.  
     - A Post‑action hook/log confirming the event.  
   - Do not infer action from indirect signals like docstrings, flags, or nearby logs.

5. Always inspect runtime state for silent failures  
   - If nothing crashes but behavior is wrong, inspect real state before theorizing:  
     - Relevant tables, files, queues, caches, metrics, and logs.  
     - IDs, timestamps, correlation IDs, and counts (e.g., “100 stale intents,” “0 rows for this key”).  
   - Treat “I looked at the actual state” as a hard requirement for any silent failure.

6. Ban architecture conclusions from docs and comments  
   - Comments, design docs, and changelogs describe intent, not reality.  
   - Use them as hypotheses generators, not proof.  
   - Any statement of the form “the system already does X” must be backed by runtime or test evidence, not just text.

7. Require disproof of the user’s report before contradicting it  
   - If the user says “I do not see X,” you may not assert “X is there” unless you have direct counter‑evidence for *their* path or scenario.  
   - Treat user reports as high‑value data points, especially about absence of visible behavior.  
   - “By design” is only valid if the design and observed behavior actually match.

8. Explicitly check for proxy mismatches  
   - List each signal you’re using: flags, log lines, metrics, UI indicators, state files.  
   - For each, write what it does and does *not* prove.  
   - Avoid chains like: “string exists” → “code executed” → “tool ran” → “user saw it” without evidence at each step.

9. Do not edit before reproducing  
   - First reproduce the symptom in a controlled scenario.  
   - Then localize: identify the minimal component or path that differs.  
   - Only then patch. Avoid “drive‑by edits” based on intuition alone, especially across multiple components.

10. Trace one failed path end‑to‑end  
   - For any multi‑step pipeline (client → service → worker → hook → DB), pick one concrete failing request and trace it across all stages.  
   - Confirm which stages ran, which didn’t, and what each produced.  
   - Do this before naming a root cause.

### B. Evidence rubric and “fixed” criteria

11. Use an evidence‑tier rubric  
   - Tier 0: intuition, memories, comments, docs.  
   - Tier 1: code/config inspection.  
   - Tier 2: local or synthetic reproduction (unit tests, isolated runs).  
   - Tier 3: runtime state/log evidence from the real or representative environment.  
   - Tier 4: observed end‑to‑end behavior matching the spec (user or system POV).  
   - No “root cause identified” below Tier 3; no “works/fixed” below Tier 4.

12. Add a pre‑response checklist  
   - Before writing “fixed,” “already working,” or “by design,” answer:  
     - Did I observe the real symptom myself?  
     - Did I observe the real success condition myself?  
     - Am I proving behavior or just proving proxies?  
     - What evidence would falsify my claim, and did I actually look for it?

***

## 2. Specialization for their skill‑guard / hooks stack

Now the same ideas, but bound to their concrete world: hooks, skills, pending intents, GLM/Claude, etc.[1][2]

### A. Skill / hook–specific observables

1. Real observable: “Skill tool invocation”  
   - Expected observable: the Claude Skill() tool is invoked for a given slash command, with a visible tool‑use event and corresponding Skill output.  
   - Non‑equivalent proxies:  
     - Breadcrumb emoji or “Invoking Skill …” indicator.  
     - “Skill loaded” text from a hook.  
     - Presence of SKILL.md content in the prompt.  
     - A unit test that checks for a string.  
   - Success evidence:  
     - A Skill tool event in the tool‑use trace for that request.  
     - A PostToolUse or Stop hook record referring to that Skill invocation.  
     - Optional: a dedicated skill‑invocation log entry for that command.

2. Mechanism / state / outcome for this stack  
   - Mechanism: UserPromptSubmit hooks, PreToolUse / PostToolUse / Stop hooks, router logic, skill enforcer, breadcrumb init, debugRCA skills.[2][1]
   - State:  
     - Pending command intent files and their terminal IDs.  
     - Hook state directories, log files, and any per‑session artifacts.  
     - Git state of hooks and skills.  
   - Outcome:  
     - What the user sees (indicators, tool traces, skill output).  
     - What the system reports (tool events, debug skills’ outputs).[1][2]

### B. Hook‑aware rules (same structure, concrete checks)

3. Do not claim “Skill is enforced” from unit tests  
   - A passing test that asserts “emoji present” or “Invoking Skill text present” only proves that the breadcrumb hook returns certain strings.[1]
   - It does not prove the Skill tool is invoked, nor that the user sees a tool event.  
   - “Skill enforcement works” must be backed by: a real skill command from a real terminal → tool‑trace showing Skill() → expected skill behavior.

4. Define skill‑specific observables in debugRCA  
   - For any skill bug, have the agent fill:  
     - Expected: “When I type /gto, I see a Skill(gto) tool event and gto’s output.”  
     - Proxies: “SKILL ACTIVATION REQUIRED text,” “breadcrumb indicator,” “SKILL.md injected.”  
     - Success evidence: “Tool trace shows Skill(gto) event for this request ID; PostToolUse log confirms.”[2][1]

5. Require real skill‑invocation evidence  
   - No claim like “AI must call Skill(gto) explicitly” unless at least one of:  
     - A tool‑use transcript with Skill(gto) for a live or test scenario.  
     - A PostToolUse / logging hook capturing that call.  
     - A skill‑invocation log entry for that command/session.  
   - Breadcrumbs or injected SKILL.md are not sufficient.

6. Mandatory state inspection for “skill silently not invoked”  
   - For “no sign that Skill was used,” debugRCA must, before hypothesizing:  
     - List and count pending command intent files.  
     - Inspect their terminal IDs and correlate with the user’s terminal/session.  
     - Check for stale or mismatched IDs and PID‑fallback behavior.[2]
   - Without this, no “by design” or “already working” judgment is allowed.

7. Multi‑angle search for skill bugs  
   - Mechanism: search hooks and skills code for enforcement, bypass paths, execution lanes.  
   - Functional: search for user‑visible messages, indicators, and error strings.  
   - State: inspect state directories, intent files, and hook logs.  
   - Temporal: git log for recent changes to skill hooks or routing.[2]
   - Document hits and misses from each angle in the debugRCA output.

8. Enforcement of evidence tiers in this stack  
   - Tier 0: “Skill enforcer is supposed to enforce tools” (docstrings, CLAUDE.md).  
   - Tier 1: “I see code that injects a directive saying ‘You MUST call Skill’.”[1]
   - Tier 2: “I ran a local test script through the enforcer and saw the directive.”[1]
   - Tier 3: “In a real or representative session, I see the directive in context and matching state files/logs.”[2][1]
   - Tier 4: “For a real command (/gto) in a live‑like session, I see: directive → visible indicator → actual Skill() tool event → correct skill output.”  
   - “Root cause identified” requires Tier ≥3; “works/fixed” requires Tier 4.

9. User contradiction handling for skills  
   - If the user says “I don’t see Skill() being used,” the agent must:  
     - Reproduce with the same skill and environment, or  
     - Pull tool traces / logs for that specific session.  
   - Only if those traces show Skill() events for their requests may the agent push back; otherwise the user’s negative observable stands.

10. Clarify indicators vs execution  
   - Document explicitly:  
     - Breadcrumb indicators: prove pattern detection, not execution.  
     - Text directives (“You MUST call Skill …”): prove an instruction was injected, not that it was obeyed.[1]
     - Actual Skill() events: prove execution.  
   - Train agents to state which category their current evidence comes from.

11. End‑to‑end path tracing for a failing command  
   - For a concrete command (e.g., /gto from terminal X), trace:  
     - UserPromptSubmit hooks that fire and what they returned.  
     - Any state/intent files created (with IDs).  
     - PreToolUse and PostToolUse hooks.  
     - Tool‑use events and Stop hooks.  
   - This must be done once per new class of skill‑enforcement bug before writing a root‑cause statement.

12. Skill‑stack pre‑response checklist  
   - Before writing “Skill enforcement fixed/working”:  
     - Did I run one real skill command from a real or realistic terminal?  
     - Did I observe a Skill() tool event for that command?  
     - Did I see the expected visual indicator as well, and can I distinguish it from the actual tool call?  
     - Have I checked pending intents / state for mismatches or stale entries?  
     - What would falsify my belief, and did I go look?

***

If you want, next step I can turn this into a CLAUDE.md section with a short, copy‑pastable template that forces the agent to fill in: observable, tier, mechanism/state/outcome, and “what would falsify this?”.

## Human

yes please

## Assistant

Here’s a CLAUDE.md–style block you can almost drop in as‑is. It has a generic “Debug / RCA Protocol” and a specialization for skills/hooks.

***

## Section: Debug / RCA Protocol

Use this protocol whenever you investigate bugs, unexpected behavior, or “by design?” questions. It applies to tools, hooks, skills, routing, retrieval, and UI.[1][2][3]

### 1. Debug request metadata

For every debug/RCA request, capture:

- Issue summary (1–2 sentences, observable‑focused).  
- Environment (local / dev / staging / prod; model; version).  
- User’s reported observable (what they see or do not see).  
- Impact (how bad is it for the user / system).[4][3]

Example:

- Issue: “When I run /gto in terminal 3, I never see a Skill() tool event.”  
- Env: “Claude Code v2.1.72, hooks main, GLM5, Windows terminal.”  
- User observable: “No Skill tool in tool‑use list; command appears to run directly.”[2][3]

***

### 2. Define observables and proxies

Before any hypotheses:

1. Fill this template:

   - Expected observable (real behavior or outcome):  
     - `…`  

   - Non‑equivalent proxies (things that might be misleading):  
     - `…`  

   - Success evidence (what would prove it works):  
     - `…`  

2. Do not proceed until these three are written.

Example:

- Expected observable: “For /gto, the tool trace shows a Skill(gto) event and gto’s output appears after that event.”  
- Proxies: “Breadcrumb emoji, ‘Invoking Skill gto’ text, ‘SKILL ACTIVATION REQUIRED’ directive.”[2]
- Success evidence: “Tool trace entry for Skill(gto) on this request; PostToolUse log referencing gto.”[3][2]

***

### 3. Evidence tiers

Every claim must state its evidence tier:

- Tier 0: Intuition, comments, docs, memory.  
- Tier 1: Code/config inspection.  
- Tier 2: Local or synthetic reproduction (unit test, script).  
- Tier 3: Runtime state/logs from a real or representative environment.  
- Tier 4: Observed end‑to‑end behavior that matches the expected observable.[5][3][2]

Rules:

- No “root cause identified” below Tier 3.  
- No “fixed” or “works as expected” below Tier 4.  
- Always write: `Confidence: X%, Tier: N, Evidence: …`.

Example:

- “Hypothesis: Skill enforcer injects the directive but Skill() is never called. Confidence 60%, Tier 2 (local tests + code inspection), no runtime tool trace yet.”[3][2]

***

### 4. Mechanism / state / outcome buckets

For every investigation, gather evidence in all three buckets:

- Mechanism: how it is supposed to work.  
  - Code paths, hooks, configs, docstrings, diagrams.  
- State: what actually exists.  
  - Files, DB rows, queues, logs, metrics, intent/state files, correlation IDs.  
- Outcome: what users/systems see.  
  - Tool events, UI output, API responses, messages.[5][2][3]

Template (must be filled in debugRCA responses):

- Mechanism evidence:  
  - `…`  

- State evidence:  
  - `…`  

- Outcome evidence:  
  - `…`

***

### 5. Multi‑angle search

Before forming hypotheses, perform:

1. Mechanism search  
   - Search code for functions, classes, hooks, feature flags.  
   - Example: `grep "enforceskill"`, `grep "Skill("`, `grep "breadcrumb"`.[2][3]

2. Functional search  
   - Search for visible strings and errors:  
   - Example: `grep "Invoking Skill"`, `grep "SKILL ACTIVATION REQUIRED"`, `grep "Skill invocation"`.[2]

3. State search  
   - List and inspect relevant state (files, tables, queues).  
   - Example: `ls state/pending*`, `cat …/intent.json`, check IDs, counts, timestamps.[3]

4. Temporal search  
   - Check recent changes: `git log --since=7d -- <relevant files>`.[3][2]

You must list what you searched and what you found or did not find.

***

### 6. Action claims and disconfirmation

Action claims (“tool ran,” “job executed,” “email sent,” “Skill() called”) require one of:

- A direct log/trace entry for that action.  
- A state change only that action can produce.  
- A post‑action hook or audit log.[5][2][3]

For each hypothesis, answer:

- Current hypothesis: `…`  
- Confidence + tier: `…`  
- Disconfirming evidence: “If this were false, I would see …”  
- Disconfirmation check: “I checked … and found …”

No claim that contradicts the user’s negative report (“I do not see X”) is allowed without fresh disconfirming evidence for *their* case.[2][3]

***

### 7. End‑to‑end trace of one failing path

For any bug that spans multiple components:

1. Pick one concrete failing request / command / user action.  
2. Trace it across all relevant stages.  
3. For each stage, note whether it ran and what it produced.  

Template:

- Request identifier (or synthetic scenario):  
  - `…`  

- Stages and findings:  
  - Stage A: `…`  
  - Stage B: `…`  
  - Stage C: `…`

Do not state “root cause” until at least one failing path has been fully traced.

***

### 8. “Fixed / by design” checklist

Before replying “fixed,” “works as intended,” or “by design,” answer:

1. Did I personally observe the original symptom? Yes/No.  
2. Did I personally observe the success condition (real observable) after my change? Yes/No.  
3. What is the strongest evidence tier I have? Tier N.  
4. What would falsify my belief, and did I explicitly check for it?  
5. Can I cite at least one concrete log/trace/state/observable from this environment?

If any are “No,” you must phrase your response as a hypothesis with explicit uncertainty, not as a conclusion.

***

## Section: Specialization – Skills / Hooks / Tools

Use this specialization for skill‑guard, hooks, and tool‑invocation issues.[3][2]

### 9. Skill / tool observables

- Expected observable example:  
  - “When I run `/gto` in terminal T, I see a Skill(gto) tool event in the tool trace, followed by gto’s output.”  

- Non‑equivalent proxies:  
  - Breadcrumb emoji or “Invoking Skill gto” text.  
  - “SKILL ACTIVATION REQUIRED” directive.  
  - Presence of SKILL.md content in the prompt.  
  - Unit tests that only assert on strings.[2]

- Success evidence:  
  - Tool trace entry: `Skill(gto)` with arguments, for that request.  
  - PostToolUse or Stop hook log referencing `gto`.  
  - Optional: dedicated skill‑invocation log (command, timestamp, session/terminal).[3][2]

***

### 10. Skill / hook–specific state checks

For “Skill not invoked,” debugRCA **must**:

- List state directories and files relevant to skill intents, e.g.:  
  - `ls P.claude/hooks/state/pending*`  
  - Count stale intent files.  
- Inspect at least one relevant intent file:  
  - `cat …/pendingcommandintent.json`  
  - Check `terminalId`, `pid`, timestamps for mismatches.[3]
- Note any PID/terminal ID fallback behavior observed in code or state.[3]

No “by design” conclusion is allowed without this state inspection.

***

### 11. Skill / hook debugRCA output template

When using the `debugRCA` skill or doing a skill/hook investigation, shape the answer like this:

1. **Issue & context**  
   - Issue: `…`  
   - Environment: `…`  
   - User observable: `…`  

2. **Expected observable & proxies**  
   - Expected: `…`  
   - Proxies (non‑equivalent): `…`  
   - Success evidence: `…`  

3. **Mechanism / State / Outcome**  
   - Mechanism evidence (Tier, details): `…`  
   - State evidence (Tier, details): `…`  
   - Outcome evidence (Tier, details): `…`  

4. **Multi‑angle search log**  
   - Mechanism search: what I searched, what I found.  
   - Functional search: what I searched, what I found.  
   - State search: directories/files inspected, counts, mismatches.  
   - Temporal search: recent commits and their relevance.[2][3]

5. **Hypotheses and disconfirmation**  
   - Hypothesis 1: `…` (confidence %, tier).  
     - Disconfirming evidence that would falsify it: `…`  
     - What I checked: `…`  
   - Hypothesis 2: `…` (if needed).

6. **Current conclusion (if any)**  
   - If Tier < 3: “Working hypothesis only; requires runtime/state validation.”  
   - If Tier 3: “Probable cause; not yet validated end‑to‑end.”  
   - If Tier 4: “Observed behavior now matches expected observable; marking as fixed for this scenario.”

7. **Next actions**  
   - `…` (e.g., “capture tool trace for /gto in user’s environment,” “add PostToolUse logging,” “add end‑to‑end regression test”).

***

If you like, I can now tighten this further into a literal system prompt block (with `<<DEBUG_PROTOCOL>>` style delimiters) that you can paste into CLAUDE.md as a reusable “mode” the model can be switched into.

## Human

Example of 5 Whys analysis for LLM debugging issue

## Assistant

Here’s a concrete 5 Whys example tailored to an LLM + tools/hooks bug like your “Skill not invoked for /gto” case.[1][2]

***

## 5 Whys example: Skill tool not invoked

**Problem statement (observable):**  
“When I run `/gto`, I do not see any Skill() tool invocation in the tool‑use trace; it looks like the command runs directly.”[1]

### Why 1 – Why is there no Skill() tool invocation?

Because the LLM responds with GTO output directly, without issuing a Skill(gto) tool call in its tool‑use actions.[1]

- Evidence: tool trace for the failing request shows normal model output but no Skill tool event.[1]
- Tier: 3 (runtime outcome).

***

### Why 2 – Why does the LLM respond directly instead of calling Skill(gto)?

Because the prompt it receives already contains the full SKILL.md content for gto, so it can answer using that context without needing to call the Skill tool.[1]

- Evidence: inspection of the composed prompt shows SKILL.md injected before the model turn.[1]
- Tier: 3 (runtime state + mechanism).

***

### Why 3 – Why is SKILL.md being injected into the prompt?

Because the skill‑enforcer hook (v2.3) both:  
1) tells the model “You MUST call Skill(gto) first,” and  
2) eagerly reads SKILL.md and injects its content into the prompt before the model has a chance to call the tool.[1]

- Evidence: code in `skillenforcer.py` shows pre‑execution injection of SKILL.md and an early return, skipping the tool‑execution lane.[1]
- Tier: 2–3 (code + verification via local script).

***

### Why 4 – Why was the skill‑enforcer hook implemented with pre‑execution injection?

Because the initial design optimized for “skills always have their instructions loaded” and treated direct SKILL.md injection as equivalent to a Skill() tool call, assuming that as long as the content is present, the behavior is acceptable.[2][1]

- Evidence: commit message / docstring describing v2.3 as “pre‑execution injection” and comments implying this is an acceptable enforcement mechanism.[1]
- Tier: 1 (docs/comments) with some Tier‑2 support from tests that only checked for injected strings.

***

### Why 5 – Why did the team treat SKILL.md injection as equivalent to a real Skill() tool call?

Because they did not clearly distinguish between:  
- Visual indicators and directives (“Skill loaded,” “You MUST call Skill…”).  
- Prompt content injection (SKILL.md stuffed into context).  
- Actual tool‑invocation observables (Skill() event in the tool trace).[2][1]

This led to relying on proxy signals (strings, unit tests) instead of enforcing and verifying the real observable (“tool event exists”).[2][1]

- Evidence: tests and earlier RCA claimed “enforcement already working” based on strings and comments, despite user reports of “no sign Skill() was used.”[2][1]
- Tier: 2–3 (test review + transcript analysis).

***

## Summary cause chain (5 Whys compressed)

1. No Skill tool event appears for `/gto` requests.  
2. The model answers directly using SKILL.md content instead of calling the tool.  
3. Skill‑enforcer v2.3 injects SKILL.md pre‑execution and returns early, bypassing the tool‑execution lane.[1]
4. This pre‑execution design was introduced under the assumption that “content injected ≈ tool invoked.”[1]
5. That assumption existed because the team treated proxy signals (strings, injected content, comments) as equivalent to the real observable (actual Skill() tool events), and never required tool‑trace evidence to validate enforcement.[2][1]

***

If you want, I can also give a second 5 Whys run on the *process* failure (“Why did the RCA miss the terminal‑ID mismatch and stale intents?”) rather than the technical bug itself.

## Human

GLM says this: "  Conclusion

  Conditionally approved with critical clarifications

  The proposed debugging protocols address a real problem (proxy mismatch in AI
  debugging) but have a circular dependency issue that must be resolved:

  Critical Path Dependencies (must be explicit):
  1. Phase 2 (instrumentation) must precede Phase 1 (confidence tags) → Tier 3/4
  evidence collection before tier enforcement
  2. Contract tests (Section 6) need expanded Phase 2 scope →
  PreToolUse/UserPromptSubmit logging, not just PostToolUse

  Recommended Modifications:
  1. Clarify phase sequence: Document Phase 2 as Phase 0 (prerequisite instrumentation)
  2. Simplify Tier 3: Consider removing 3a/3b split until evidence collection matures,
  or provide clearer decision tree
  3. Add max claim examples: Include concrete phrase mappings for each tier (e.g.,
  "plausible cause" → Tier 2)
  4. Automate proxy detection: Extend Phase 2 to log breadcrumb indicators separately
  from Skill() events for automated verification

  Viability: The core ideas are sound, but the proposal underestimates instrumentation
  prerequisites. Recommend implementing Phase 2 (full hook pipeline logging) first,
  then Phase 1 (protocol enforcement) once Tier 3/4 evidence is collectable.

  ---
  Confidence: 75%

  Evidence basis:
  - Design doc: GLM5/Codex analysis document (834 lines)
  - Web research: 0 sources (design review only)
  - Codebase analysis: Referenced implementation files
  (test_skill_invocation_indicator.py, skillenforcer.py, breadcrumb_init.py)

  Key assumptions:
  1. Current hook system has PostToolUse but may lack PreToolUse/UserPromptSubmit
  logging
  2. AI agents will manually comply with proxy detection rules without automated
  enforcement
  3. Tier 3a/3b distinction provides sufficient value to justify complexity
  4. Contract tests can be implemented without breaking existing hook behavior
"

## Assistant

GLM’s critique is mostly right: your protocol assumes good observability that doesn’t fully exist yet, so some “tier enforcement” would be toothless until you add instrumentation.[1][2][3]

### 1. Circular dependency / phase ordering

- Your rules say “no ‘fixed’ below Tier 4, no ‘root cause’ below Tier 3,” but Tier 3/4 hinge on being able to see real tool traces, hook logs, and state, which you don’t have uniformly yet.[2][3]
- That creates an implicit catch‑22: “You must have Tier 3/4 evidence” vs “we haven’t instrumented the system to emit Tier 3/4 signals in a cheap, standard way.”[3][1][2]

I’d accept GLM’s change: treat instrumentation as Phase 0, not Phase 2.

### 2. Suggested concrete reorder

**Phase 0 – Instrumentation (prereq)**

- Add standardized logging across the full pipeline: UserPromptSubmit, PreToolUse, ToolUse, PostToolUse, Stop.[1][2][3]
- Log, at minimum: request/session ID, command/skill name, hook name, hook stage, whether a Skill() tool was invoked, and a simple outcome flag (success/fail).  
- Log breadcrumb indicators separately from Skill() events so you can machine‑check proxy mismatch later, as GLM suggests.[2][3]

Only after you can, in one query, answer “did Skill(gto) run for this request?” does Tier‑3/4 enforcement become meaningful.

**Phase 1 – Protocol + tiers**

- Once Phase 0 exists, enforce your evidence tiers and checklists in CLAUDE.md (and debugRCA skill) as written: no “fixed” without reading the Phase‑0 logs.[4][3]

### 3. Tier 3 split and complexity

GLM’s doubt about 3a/3b is reasonable early on.[5]

- Before instrumentation is mature, you can just use a single Tier 3 (“some runtime evidence”) and only split it later if you see real value in distinguishing “state only” vs “state + structured logs.”[3]
- If you keep the split, a tiny decision rule helps:  
  - No logs/traces → max Tier 3a.  
  - Logs/traces that mention the concrete request/skill → Tier 3b.[1][3]

That keeps complexity manageable.

### 4. “Max claim per tier” language

You already imply this; GLM is just asking for explicit phrase mapping.[2][3]

Example mapping:

| Tier | Allowed phrasing (examples) |
|------|-----------------------------|
| 0    | “Rough guess…”, “Speculation, needs code review.” |
| 1    | “Likely behavior based on code/config.” |
| 2    | “Plausible cause, reproduced locally.” |
| 3    | “Probable cause, seen in runtime state/logs.” |
| 4    | “Observed working/not working end‑to‑end.” |

This makes it obvious when an agent is over‑claiming their tier.

### 5. Contract tests and logging

GLM’s point that contract tests need more than PostToolUse is also solid.[6][2]

- For your skill stack, contract tests should capture and assert:  
  - What UserPromptSubmit hooks returned (e.g., directives, additionalContext).  
  - Whether a PreToolUse validation ran.  
  - The actual Skill() tool event.  
  - Optional: what PostToolUse/Stop saw.[3][2]

That’s consistent with their suggestion to widen “Phase 2” from just PostToolUse to the full hook chain.

### 6. One nuance I’d push back on

GLM assumes “AI agents will manually comply with proxy detection rules without automated enforcement,” which you’re already addressing by putting this into CLAUDE.md and making debugRCA a skill/mode.[7][3]

- I’d still automate as much as possible (logging, simple checkers to detect “indicator without tool event”), but the written protocol is still valuable even before automation.  
- So: yes, instrumentation first for *strong* tier enforcement, but don’t wait to start training the model to speak in tiers and name its observables.

If you want, I can draft a short “Phase 0 instrumentation spec” for your stack (what to log at each hook and how to store it so both humans and agents can query it quickly).

## Human

I'm a little bit confused.  If I'm working on a problem that isn't a hook, how will this help?

## Assistant

It helps because none of the ideas are actually hook‑specific; “hooks” are just one example of “places where the system might lie to you via proxies.”

### Core ideas that generalize

For any LLM issue (bad answer, missing tool call, wrong RAG result, flaky agent), you can still:

- Define the **real observable** first: “What exactly should I see if this works?” (UI output, DB row, API call, email, etc.), and list proxies that don’t count (log line, comment, unit test passing).  
- Use **evidence tiers**:  
  - Tier 0: intuition/docs.  
  - Tier 1: reading code/config.  
  - Tier 2: small local repro/script.  
  - Tier 3: runtime state/logs (DB, traces, telemetry).  
  - Tier 4: full end‑to‑end behavior the user would see.  
  Then refuse to say “fixed” without at least Tier 4, even if it’s not about hooks at all.  
- Separate **mechanism vs state vs outcome**:  
  - Mechanism: “This router should send queries to retriever A.”  
  - State: “This index actually has zero docs for that tenant.”  
  - Outcome: “User’s question falls back to generic answer.”

That structure works for:

- Prompting failures (“LLM ignores constraint X”).  
- Retrieval failures (“LLM answers without using RAG”).  
- Tool‑calling bugs (“LLM never calls translate(), just translates inline”).  
- Multi‑agent flows (“Supervisor never hands off to specialist Y”).

### Concrete non‑hook example

Say: “LLM often answers without using the DB tool.”

You can still run the same protocol:

- Observable: “For queries tagged `needs_db=true`, I expect to see at least one DB tool call in the trace.”  
- Proxies: “Instruction says ‘always use DB’,” “unit test for a toy query passes,” “log message ‘DB initialized’.”  
- Evidence:  
  - Mechanism: code shows a routing function that marks queries as `needs_db`.  
  - State: metrics/logs show 90% of those queries have no DB tool event.  
  - Outcome: user conversations show hallucinated answers.  
- Why chain (5 Whys) and tiers apply identically.

The only hook‑specific bits in our discussion were:

- The names of observables (Skill(), breadcrumb, SKILL.md).  
- The concrete state artifacts (pending intent JSON, terminal ID mismatch).

You can swap those out for whatever artifacts exist in the system you’re debugging (OpenSearch index, S3 blob, Kafka topic, Firestore doc, etc.), but the discipline is the same: explicit observable, evidence tier, mechanism/state/outcome, avoid proxies, require one traced failing path.

If you want, describe a current non‑hook LLM bug you care about (e.g., “RAG doesn’t get used” or “agent skips planner”), and I’ll walk it through this protocol end‑to‑end so you can see the mapping concretely.

## Human

but GLM talks about hooks.  That implies what's being considered won't be used for other use cases.

## Assistant

You’re right to be suspicious: the *examples* GLM is reacting to are all hook‑centric, so it naturally talks about hooks. But the underlying machinery it’s critiquing is more general.

### What’s specific vs general

Specific to hooks/tools in that review:[1][2]
- Names of stages: UserPromptSubmit, PreToolUse, PostToolUse, Stop.  
- Concrete observables: Skill() events, breadcrumb indicators, SKILL.md injection.  
- Concrete state: pending intent files, terminal IDs, PID fallback.

General across almost any LLM system:[3][1]
- Need for **instrumentation before protocol enforcement** (you must be able to see what happened before you can demand Tier‑3/4 evidence).  
- Idea of **real observables vs proxies** (tool event vs “string exists,” API call vs “log line exists”).  
- **Evidence tiers** and “max claim per tier.”  
- Requirement to log signals separately so you can detect **proxy mismatch** (e.g., “indicator fired but action didn’t”).

GLM is just critiquing the *instantiation* you showed it (which happens to be about hooks). The same pattern works for:

- RAG not being used: log retrieval calls vs on‑context snippets.  
- Planner/agent bugs: log handoff events vs “I say I’m delegating.”  
- External API tools: log HTTP requests vs “I say I called the API.”

### How to make it obviously non‑hook‑specific

You can make that explicit in your docs:

- Define a generic pipeline schema: `Input → Orchestrator → Subsystems (tools/agents/hooks/etc.) → Output`.  
- Then say: “In the skill‑guard stack, these subsystems are hooks (UserPromptSubmit, PreToolUse…). In other stacks, they might be RAG retrievers, planners, or HTTP tools.”  
- Move the **tier rules, observable/proxy rules, and instrumentation‑first rule** into a generic “Debug Protocol” section, and keep hook names only in a “Skill‑guard specialization” subsection.[4][1]

So: GLM talks about hooks because that’s the concrete case it saw, not because the protocol can’t apply elsewhere. If you’d like, describe one non‑hook LLM flow you care about (e.g., RAG, planner, or external API), and I’ll rewrite the same instrumentation + tier rules against that flow so it’s clearly reusable.

## Human

How about you just make it clearly reusable now without any other example to fixcate on?

## Assistant

You can make it reusable by defining everything in system‑agnostic terms, then giving hooks/skills as just one optional specialization.

Below is a compact “generic first, specialization later” version you can drop into CLAUDE.md or a shared design doc.

***

## Generic Debug / RCA Protocol (LLM + System)

### 1. Applicability

Use this protocol for any LLM‑involved issue, including:

- Bad or missing tool/API calls  
- RAG not used or mis‑used  
- Planner/agent mis‑routing  
- UI or workflow behavior that depends on the LLM’s output

It does not assume hooks, skills, or any specific stack.

***

### 2. Define the real observable (no proxies)

Before hypothesizing anything, write:

- **Expected observable (real world):**  
  What a user or external system would see if it works.  
  - Examples: “A DB row exists with key X,” “Email Y is sent,” “Tool T appears in the trace,” “UI shows banner Z.”

- **Non‑equivalent proxies:**  
  Signals that are related but do *not* prove the observable.  
  - Examples: log lines, comments, flags, unit tests, “instruction text present,” “snippet appears in context.”

- **Success evidence:**  
  Minimal concrete evidence that the observable is satisfied.  

No “fixed” or “already working” claims are allowed without success evidence for the real observable.

***

### 3. Evidence tiers and allowed claims

For any statement about what the system does, attach a tier:

- **Tier 0 – Intuition / docs**  
  - Source: memories, comments, design docs, changelogs.  
  - Allowed claims: “Speculative,” “According to the docs, it *should*…”.

- **Tier 1 – Code/config inspection**  
  - Source: reading code, configs, prompts, routing rules.  
  - Allowed claims: “Likely behavior based on implementation,” “The intended path appears to…”.

- **Tier 2 – Local/synthetic reproduction**  
  - Source: unit tests, local scripts, sandboxed runs with synthetic inputs.  
  - Allowed claims: “Plausible cause; I reproduced similar behavior in a controlled test.”

- **Tier 3 – Runtime state/logs**  
  - Source: production or realistic environment: logs, traces, DB rows, files, metrics.  
  - Allowed claims: “Probable cause; runtime evidence matches this hypothesis for real traffic.”

- **Tier 4 – Observed end‑to‑end behavior**  
  - Source: end‑to‑end run of the actual scenario from user/system POV.  
  - Allowed claims: “Observed working/not working end‑to‑end for this scenario.”

**Enforcement:**

- No “root cause identified” < Tier 3.  
- No “fixed / works / by design” < Tier 4.  
- Responses should name tier and confidence:  
  - “Hypothesis X (Tier 2, 60% confidence).”

***

### 4. Mechanism vs state vs outcome

For every investigation, collect all three:

- **Mechanism** – how it is supposed to work  
  - Code paths, configs, prompts, routing graphs, architectural diagrams.

- **State** – what actually exists  
  - DB rows, files, queue messages, cache keys, logs, metrics, traces.

- **Outcome** – what users/systems see  
  - Tool traces, UI, API responses, emails, notifications.

Template:

- Mechanism evidence: …  
- State evidence: …  
- Outcome evidence: …

Do not declare a root cause with only mechanism evidence.

***

### 5. Multi‑angle search (generic)

Before you settle on a hypothesis:

1. **Mechanism search** – How is it implemented?  
   - Search for function/class names, feature flags, routing logic.

2. **Functional search** – What produces visible symptoms?  
   - Search for user‑facing strings, error messages, tool names, event types.

3. **State search** – What state exists?  
   - List relevant tables, collections, files, queues, metrics; inspect representative entries.

4. **Temporal search** – What changed recently?  
   - Look at recent code/config changes affecting this path.

You must document at least one search and result in each category.

***

### 6. Action claims and disconfirmation

Any claim that an action occurred (or always occurs) must have direct evidence:

- Example actions: “Tool T ran,” “DB update happened,” “External API was called,” “Planner delegated to agent B.”

**Valid evidence:**

- A trace/log entry for that action.  
- A state change only that action can produce.  
- A post‑action audit/log/hook record.

**Invalid shortcuts:**

- Comments / docstrings saying it happens.  
- The LLM *saying* it happened.  
- Nearby strings (“TOOL LOADED”, “Executing…”).

For each hypothesis, explicitly state:

- Hypothesis: …  
- Evidence tier and confidence: …  
- What would falsify this: “If false, I would see …”  
- Disconfirmation check: “I checked … and found …”

You may not contradict a user’s negative observation (“I don’t see X”) without fresh disconfirming evidence for their scenario.

***

### 7. End‑to‑end trace of one failing case

For any multi‑step flow (no matter what the components are):

1. Pick a concrete failing case (user action, request ID, conversation).  
2. Trace it across all relevant stages in the pipeline.  
3. For each stage, record whether it ran and what it output.

Only after at least one full failing path is traced should you name a root cause.

***

### 8. “Fixed / by design” checklist

Before replying “fixed,” “works as intended,” or “by design,” answer:

1. Did I personally observe the original symptom? (Y/N)  
2. Did I personally observe the expected observable after the change? (Y/N)  
3. Strongest evidence tier I have now? (N)  
4. What would falsify my belief, and did I explicitly check for it?  
5. Can I cite at least one concrete state/log/trace/observable from this environment?

If any are “No,” phrase your response as a hypothesis with uncertainty, not a conclusion.

***

## Specializing to any stack

To specialize this protocol to a particular system (hooks, RAG, planner, external tools):

- Define the **observables** for that system:  
  - e.g., “retriever call exists,” “planner produced a plan,” “external API request logged.”

- Define the **state artifacts**:  
  - e.g., “retrieval logs/table,” “planner trace,” “HTTP request logs.”

- Map existing stages to “pipeline stages” for end‑to‑end trace:  
  - e.g., “router → retriever → LLM → post‑processor” instead of “UserPromptSubmit → PreToolUse → …”.

The protocol text above then applies unchanged; only the concrete names of observables, state stores, and stages change.

If you want, next step I can help you write one short “specialization block” for your generic LLM app (router + tools + RAG), but keep this generic block as the thing models read first so they don’t fixate on any one implementation.
