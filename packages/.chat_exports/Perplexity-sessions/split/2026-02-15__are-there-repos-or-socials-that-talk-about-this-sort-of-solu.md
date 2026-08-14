---
title: "Are there repos or socials that talk about this sort of solution for claude code cli?
'
❯ Since this seems universal, w"
date: "2026-02-15"
mode: "COPILOT"
uuid: "58f38b69-970a-47b1-8451-04545a1fc8b6"
entry_count: 6
---

## Human

Are there repos or socials that talk about this sort of solution for claude code cli?
"
❯ Since this seems universal, we not use it as a hook instead of per skill?  next_step_question, unless
  I'm misunderstanding?

● You're asking a good architectural question. Let me clarify the distinction:

  Two Different Concepts

  1. Competence Layer (what we just built)

  - Per-task-type contracts: Different skills need different output fields
  - research tasks need sources, findings
  - implementation tasks need implementation_summary, testing_notes
  - planning tasks need next_step_question when intent is ambiguous
  - Taxonomy-based: 6 task types with different required fields

  2. Universal next_step_question (what you're suggesting)

  - A global conversational pattern that applies to ALL interactions
  - "Ask before assuming" - good practice regardless of task type
  - Could be a hook or universal template

  The Tension

  You're right that next_step_question is universally good practice. However:

  ┌──────────┬─────────────────────────────────────┬─────────────────────────┐
  │  Aspect  │          Competence Layer           │     Universal Hook      │
  ├──────────┼─────────────────────────────────────┼─────────────────────────┤
  │ Scope    │ Task-type specific                  │ Global to all responses │
  ├──────────┼─────────────────────────────────────┼─────────────────────────┤
  │ Trigger  │ Contract gate detects missing field │ Always injected         │
  ├──────────┼─────────────────────────────────────┼─────────────────────────┤
  │ Purpose  │ Ensure complete outputs             │ Prevent assumptions     │
  ├──────────┼─────────────────────────────────────┼─────────────────────────┤
  │ Best for │ Structured skill outputs            │ Conversational clarity  │
  └──────────┴─────────────────────────────────────┴─────────────────────────┘

  Recommendation: Both Could Coexist

  1. Keep Competence Layer for task-type-specific fields (sources, findings, implementation_summary)
  2. Add a Universal Hook that injects a lightweight "ask before assuming" template into ALL prompts

  The universal hook would be simpler - just a UserPromptSubmit hook that adds:

  ## Interaction Pattern
  If the user's intent is ambiguous or multiple interpretations exist:
  1. State your understanding
  2. Ask a clarifying question before proceeding

  Want me to create a simple universal "clarification pattern" hook that works alongside the competence layer?
"

## Assistant

Yes, several GitHub repositories and community discussions cover universal hooks in Claude Code CLI, particularly UserPromptSubmit hooks for injecting clarification patterns, context, or prompt improvements to handle ambiguous intents—aligning closely with your "ask before assuming" idea alongside task-specific competence layers.[1][2][3][4]

## Key Repositories

These repos demonstrate practical implementations of universal hooks that enhance all prompts or responses, often using UserPromptSubmit for pre-processing or Stop hooks for continuation checks.

| Repository | Focus | Relevance to Your Solution |
|------------|--------|----------------------------|
| [disler/claude-code-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery) [3] | Comprehensive hook lifecycle coverage (all 8 events), including UserPromptSubmit for prompt validation, logging, and context injection before Claude processes any input. | Directly supports universal "clarification pattern" via context addition (stdout injection) or blocking ambiguous prompts; includes Stop hooks to prevent completion if tasks unfinished—mirrors next_step_question logic.[1] |
| [severity1/claude-code-prompt-improver](https://github.com/severity1/claude-code-prompt-improver) [4] | UserPromptSubmit hook that enriches vague prompts, adds context from codebase/web research, and generates grounded clarifying questions. | Exact match for universal clarification: detects ambiguity, asks targeted questions before proceeding; available via Plugin Marketplace for easy install.[5] |
| [j0KZ/mcp-agents](https://github.com/j0KZ/mcp-agents) [6] | MCP agents with "two-iteration clarification pattern for vague requests" plus Git hooks. | Implements iterative clarification (state understanding + ask) universally, tested with Claude Code hooks. |

## Community Discussions

- Reddit r/ClaudeAI threads on UserPromptSubmit's `additionalContext` for injecting clarification templates into every prompt.[7][8]
- Official docs emphasize UserPromptSubmit for global patterns like "ask before assuming," with JSON output for `decision: "block"` + `reason` to force continuation.[2][1]

## Implementation Fit

Your coexistence idea (competence layer per-task + universal hook) matches these: Use UserPromptSubmit to inject lightweight "## Interaction Pattern: State understanding, then ask if ambiguous" into all prompts via `additionalContext` or stdout—runs globally without overriding skill-specific fields. For the hook script, adapt examples from disler repo's `user_prompt_submit.py` to output clarification instructions.[1]

## Human

Can you design a comprehensive solution with all the good ideas?

## Assistant

Here’s a full architecture that combines: (1) a universal clarification pattern, (2) a competence/contract layer per task type, and (3) smart skill + hook cooperation for Claude Code CLI.[1][2][3][4][5]

***

## High-level design

You wire three layers:

1. **Universal Clarification Hook (UserPromptSubmit)**  
   - Runs on every prompt.  
   - Detects ambiguity and either:  
     - injects a lightweight “state understanding + ask clarifying question” pattern, or  
     - blocks and shows a clarifying message if you want hard gating.[6][1]

2. **Competence / Contract Layer (per task-type)**  
   - Each skill or agent type has a contract: required fields like `sources`, `findings`, `implementation_summary`, `next_step_question`, etc.  
   - Post-task hooks validate outputs and enforce these contracts; if missing, they trigger an explicit follow‑up interaction.[7][8]

3. **Skill & Session Intelligence**  
   - A “prompt-improver” skill used behind a simple UserPromptSubmit hook for heavy ambiguity resolution, similar to the Severity1 design.[3][9]
   - SessionStart hook injects project context and your interaction norms into CLAUDE.md / additional context so the behavior is stable over long sessions.[10][1]

***

## Layer 1: Universal clarification hook

**Hook event**: `UserPromptSubmit`.[1][6]

**Behavior:**

- Inspect last N user+assistant turns from the transcript.  
- Apply a lightweight heuristic or LLM eval to classify prompt clarity.  
- If clear:  
  - Allow prompt; append a short clarification pattern to context via `additionalContext` (or stdout) so Claude always follows it.  
- If ambiguous:  
  - Option A (soft): allow, but inject explicit instructions to:  
    1) paraphrase intent, 2) ask 1–3 questions before doing work.  
  - Option B (hard): return `decision: "block"` with a concise explanation and your own clarifying questions.[6][1]

**Example JSON output (soft mode):**

```json
{
  "decision": "allow",
  "reason": "",
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "## Interaction Pattern\nIf the user's intent is ambiguous or multiple interpretations exist:\n1. Briefly state your understanding of their request.\n2. Ask targeted clarifying questions before proceeding.\n3. Only execute irreversible changes after the user confirms."
  }
}
```

Because `additionalContext` is concatenated with other hooks, this runs globally without fighting your skills.[1]

You can further upgrade this by delegating ambiguity detection to a **prompt-improver skill** (see Layer 3), exactly like the Severity1 project: the hook wraps the prompt with eval instructions, Claude scores clarity, and only when unclear does it fan out into questions.[9][3]

***

## Layer 2: Competence / contract layer

You enforce **task-type contracts** at the skill/agent level, not via the universal hook.

### 2.1 Task taxonomy

Define ~6 task types (or whatever you’ve already designed):

- `research`: requires `sources`, `findings`, maybe `open_questions`.  
- `implementation`: requires `implementation_summary`, `changed_files`, `testing_notes`.  
- `planning`: requires `plan_steps`, `risks`, `next_step_question` when ambiguity exists.  
- `debugging`, `refactor`, etc., each with their own fields.

Represent each as a JSON schema or a small internal contract file per skill: the competence layer just checks whether the final answer conforms.

### 2.2 Where contracts are enforced

Two options that combine well:

1. **Within skills (structured outputs)**  
   - Skills use a consistent “Result” section with markdown or JSON blobs.  
   - The skill prompt includes “always output all required fields, even if some are ‘none’.”

2. **Post-task hooks**  
   - Use a hook like `Stop` / `PostToolUse` to validate the last assistant turn against the contract.[8][7]
   - If fields are missing or malformed, the hook can:  
     - inject context telling Claude to repair its own output (“you forgot `testing_notes`, add them now”), or  
     - in strict mode, block and prompt *you* to retry the skill with a better instruction.

This keeps a clear separation:

- **Universal hook**: improves *conversation quality* and reduces assumption‑driven errors.  
- **Competence layer**: improves *artifact quality* and ensures structured completeness.

***

## Layer 3: Prompt improver + skills / session intelligence

This layer borrows directly from existing patterns that work well in practice.[4][5][10][3]

### 3.1 Prompt improver skill (heavy clarification)

Design a skill `prompt-improver` similar to Severity1’s:

- Input: current user prompt + conversation transcript summary.  
- Responsibilities:  
  - Evaluate clarity.  
  - If clear: do nothing special.  
  - If unclear:  
    - perform quick research in codebase / docs (via tools) to ground the questions,  
    - generate 1–6 focused clarifying questions,  
    - optionally propose an initial plan once questions are answered.[3][9]

You wire this via a **UserPromptSubmit hook in “forced eval” style**, like the skills‑activation trick that jumped from ~20% to >80% activation: the hook forces Claude to explicitly say YES/NO to “is prompt clear” and to call the skill when it’s not.[4]

### 3.2 SessionStart context

Use a `SessionStart` hook to inject:

- current project summary (from README, CLAUDE.md, open issues),  
- short description of your competence contracts,  
- the universal interaction pattern (so it’s reinforced even if UserPromptSubmit fails).[10][1]

You can write this into `additionalContext` or directly into `CLAUDE.md` via a hook script, as shown in self‑improving setups.[5][10]

***

## How all layers cooperate for one prompt

For a given user message:

1. **UserPromptSubmit hook fires**  
   - Checks clarity.  
   - If ambiguous: injects clarification pattern and possibly triggers prompt‑improver skill via forced eval.  
   - If clear: still injects a short reminder of the interaction pattern.[3][4][1]

2. **Skill selection + execution**  
   - Claude picks a skill (or not), with improved odds if you also have a “skills loader” pattern like in the 84% activation write‑up.[11][4]
   - Skills themselves know which task-type contract applies.

3. **Post-task / Stop hooks**  
   - Validate that all contract fields are present for the chosen task type.  
   - If something is missing, they nudge Claude to repair or ask a follow‑up question instead of silently returning an incomplete answer.[7][8]

4. **Ongoing sessions**  
   - SessionStart ensures the norms and contracts are re‑injected after compaction; you keep consistent behavior even in long marathon sessions.[2][12][10]

***

## Concrete pieces to implement

If you want, I can next:

- Draft a `UserPromptSubmit` hook script (bash or Python) with:  
  - JSON output using `additionalContext`,  
  - simple clarity heuristic and “soft mode” vs “hard mode” switches.[13][6]
- Sketch a contract file format (YAML/JSON) and a small validator hook that reads it and checks the last reply.  
- Outline a `prompt-improver` skill body aligned with your existing taxonomies and long‑session workflow.

## Human

Here's some info.  How would it change your solution if at all?

## Assistant

It mostly *confirms* and *sharpens* the architecture I suggested, but it changes the emphasis in three ways: treat your Prompt Enhancement Bridge as the primary Layer 1, keep /prompt_refiner manual at first, and explicitly coordinate with the competence layer using shared context/metrics.[1]

### 1. Alignments (no change needed)

- Three-layer stack is the same:  
  1) **Universal clarification** via UserPromptSubmit,  
  2) **Prompt enhancement framework** (technique selection / /prompt_refiner),  
  3) **Competence contracts** with Stop‑hook validation.[1]
- The idea that `next_step_question` is a universal conversational pattern rather than only a contract field is already baked into the “universal hook + per‑task contracts” split, so that core design stands unchanged.[1]

### 2. What I’d update in the solution

1. **Use your Prompt Enhancement Bridge as the universal hook implementation**  
   - Instead of a generic “clarification hook,” adopt your `enhance_prompt(prompt, cwd)` core algorithm and four enhancement levels (none, clarification, guidance, framework).[1]
   - Keep the explicit heuristics: domain, complexity tiers, ambiguity detection, and the *fail‑open* rule so the hook never hard‑blocks sessions.[1]

2. **Adopt the phased integration strategy**  
   - Phase 1: standalone `UserPromptSubmit_prompt_enhancement_bridge.py` with env‑flag control and soft clarification (inject questions, don’t block).[1]
   - Phase 2: move into `UserPromptSubmit/prompt_enhancement.py` with registry priorities, so it’s ordered cleanly among other hooks.  
   - Phase 3: only then wire in the prompting‑framework async orchestration; this is more conservative than my earlier “go straight to a prompt‑improver backend” suggestion.[1]

3. **Keep /prompt_refiner manual initially (Option B)**  
   - My earlier design leaned toward auto‑invoking a prompt‑improver skill for complex prompts; your doc recommends keeping it manual until data proves it’s worth auto‑triggering.[1]
   - So Layer 2 in the near term is *internal* framework selection for patterns (Socratic, CoVe, Self‑Refine), not automatic `/prompt_refiner` calls.

### 3. Competence layer coordination tweaks

- Reuse the **domain/complexity/intent** analysis from the bridge in the competence layer so both share a single context model, instead of each re‑detecting task type independently.[1]
- Wire metrics from the competence layer (e.g., how often `next_step_question`, `recommendation`, `sources` are missing) back into the bridge’s thresholds and ambiguity detection over time, as your “feedback loop” section suggests.[1]

### 4. Operational details I’d now bake in

- Config via env vars (`PROMPT_ENHANCEMENT_*`) for on/off, min complexity, max tokens, timeout, and debug mode, so you can tune behavior per repo or per session.[1]
- Soft clarification as the default mode, with “hard block” only as a potential future option after you see logs and UX impact.  
- Clear observability: debug logging that shows which enhancement level fired and *why*, matching your “observable” principle.[1]

If you want, next step I can draft the actual `UserPromptSubmit_prompt_enhancement_bridge.py` scaffold that implements your design (env config + heuristic routing + JSON output) so you can drop it straight into `.claude/hooks`.

## Human

I thought I recalled additional features from the suggested repos.  We don't want anything from them?

## Assistant

Some of the repo patterns are worth explicitly pulling in; they’d extend your bridge + competence design rather than replace it.[1][2][3][4][5][6]

## 1. From Hooks Mastery: safety + control patterns

I would **adopt** these ideas from `claude-code-hooks-mastery` and related write‑ups:

- **Prompt validation & security filtering in UserPromptSubmit**  
  Add an early gate that can:  
  - block obviously dangerous commands,  
  - downgrade them to “dry‑run / explain plan first,”  
  - or force a clarification step when tools like `rm`, deployment scripts, or prod configs are involved.[7][2]

- **Permission-based tool access control**  
  Use PreToolUse hooks to enforce a simple policy layer (allowed tools per repo or per branch), independent of the competence layer.[2]
  This complements your clarification bridge by making “ask before assuming” *mandatory* around sensitive tools.

- **Better error handling for hooks**  
  Reuse their pattern where hook failures are logged and surfaced but don’t brick the CLI, aligning with your fail‑open principle.[7][2]

These slot into your architecture as *additional* hooks: your Prompt Enhancement Bridge stays the main UserPromptSubmit logic, but some of the Mastery repo idioms shape how you do validation, safety, and fallback.

## 2. From Prompt Improver: forced‑eval + research skill split

From the `claude-code-prompt-improver` posts, there are a few specific patterns I’d keep:

- **Forced-eval hook for clarity**  
  Don’t just heuristically mark prompts “ambiguous.” Wrap the prompt and require Claude to explicitly answer:  
  - “Is this clear enough to act safely without questions? YES/NO.”  
  - If NO, it *must* generate 1–6 grounded clarifying questions.[3][6]
  This can be your “Framework” level in the bridge: when complexity/ambiguity thresholds are crossed, switch from pure heuristics to this forced‑eval pattern.

- **Separate evaluation (hook) vs research (skill)**  
  Mirror their architecture:  
  - Hook = quick clarity assessment + decision.  
  - Skill = heavier research to form good questions and grounding, only when needed.[6][3]
  That matches your doc’s recommendation to keep `/prompt_refiner` manual for now but gives you a tested shape if you later auto‑wire a “prompt‑improver” skill as Level 4.

- **Token‑efficiency tricks**  
  Borrow their progressive disclosure idea: only include heavy research or long instructions when the eval says it’s warranted, keeping your enhancement bridge within the token budgets you outlined.[6]

## 3. From skills‑activation & OpenSkills: routing discipline

From the “skills activate 84%” and OpenSkills material:

- **Forced-eval for skill selection**  
  Use a similar pattern where your bridge sometimes asks Claude:  
  - “Should this go through a specialized skill / competence mode? YES/NO. If YES, which?”  
  This helps the competence layer reliably fire the right task‑type contract instead of hoping Claude notices the skill docs.[4][8]

- **Universal skills list as shared context**  
  The OpenSkills idea (a canonical `<available_skills>` block) is a nice companion to your SessionStart context: you can inject a short, structured skills list once, and let the bridge/competence layer refer to it rather than re‑enumerating skills every time.[5][9]

## 4. From multi‑agent observability: logging and feedback loop

Your design already wants metrics; the `claude-code-hooks-multi-agent-observability` repo gives you patterns to:

- Emit **structured hook events** (UserPromptSubmit + Stop + PreToolUse + PostToolUse) to a local server for live dashboards.[10][1]
- Use those events to measure:  
  - clarification rate,  
  - how often contracts fail (`next_step_question` missing, etc.),  
  - impact of tweaks to thresholds.

I’d keep your bridge’s metrics minimal at first, but follow their one‑way “hooks → HTTP POST → SQLite” architecture once you want richer dashboards.[1]

***

So the answer is: you *do* want features from those repos, but as **inspirations and patterns**, not as direct dependencies. The core of your system should still be your Prompt Enhancement Bridge + competence layer; the repos add:

- hardened safety/validation hooks,  
- a proven forced‑eval clarification pattern,  
- better skill routing discipline,  
- and an observability pipeline you can scale into later.

## Human

please create an optimal solution design

## Assistant

Here’s an end‑to‑end “optimal” design that combines your Prompt Enhancement Bridge, the competence layer, and the strongest patterns from Hooks Mastery, Prompt Improver, and skills‑activation work.[1][2][3][4][5]

***

## 1. Architecture overview

Four cooperating layers:

1. **Prompt Enhancement Bridge (Layer 1 – your core)**  
   - UserPromptSubmit hook that runs for every prompt.  
   - Does domain/complexity/ambiguity analysis; chooses enhancement level: none, clarification, guidance, or framework.[5]

2. **Forced‑eval Clarification & Skill Router (Layer 2)**  
   - Uses a forced‑evaluation pattern (inspired by Prompt Improver + skill‑activation hook) to:  
   - Explicitly decide: “is this clear?” and “do we need a specific skill / task type?”.[3][6][4]

3. **Competence / Contract Layer (Layer 3 – already yours)**  
   - Task‑type detection (research, implementation, planning, etc.).  
   - Contract injection + Stop‑hook validation for required fields (sources, findings, implementation_summary, next_step_question, recommendation…).[5]

4. **Governance & Observability (Layer 4)**  
   - Safety filters, permission‑based tool access, builder/validator patterns, and structured logging, following Hooks Mastery + multi‑agent observability.[2][7][8][1]

All four are **fail‑open**: if any enhancement fails or times out, Claude still sees the original prompt (maybe with less help).[9][5]

***

## 2. Layer 1 – Prompt Enhancement Bridge (UserPromptSubmit)

**Hook:** `UserPromptSubmit_prompt_enhancement_bridge.py` (Phase 1), later moved into `UserPromptSubmit/prompt_enhancement.py` with priority ordering.[5]

### 2.1 Core algorithm (from your doc, tightened)

- Inputs: `prompt`, `cwd`, recent transcript.  
- Quick analysis (<10–20 ms in normal cases):  
  - `domain = detect_domain(prompt, cwd)` (paths + keywords).  
  - `complexity = assess_complexity(prompt)` (simple / moderate / complex / expert via length + patterns).  
  - `intent = detect_intent(prompt)` (ask, explain, design, implement, debug…).  
  - `needs_clarification = check_ambiguity(prompt)` (short, vague pronouns, “fix it / make it better” etc.).[5]

### 2.2 Enhancement levels

- **None** (simple prompts): return `decision: "allow"` with no `additionalContext`.[5]
- **Clarification** (ambiguity detected):  
  - Inject 1–3 targeted clarifying questions tailored to domain; soft mode (do not block).[5]
- **Guidance** (moderate complexity):  
  - Inject a short domain‑specific response pattern (e.g., for implementation: analyze, plan, patch, diff, test).[5]
- **Framework** (complex/expert):  
  - Wrap prompt with a small framework header that will be interpreted by Layer 2 (forced eval), and optionally select a cognitive pattern (Socratic, evidence‑gathering, verification) from your prompting framework.[10][5]

### 2.3 Output format

Use advanced JSON with `additionalContext` and a debug flag:

```json
{
  "decision": "allow",
  "reason": "",
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "## Interaction Pattern\nIf intent is ambiguous or multiple interpretations exist:\n1. Briefly state your understanding.\n2. Ask targeted clarifying questions before acting.\n3. For irreversible changes, show a plan and wait for confirmation.",
    "debug": {
      "domain": "security",
      "complexity": "complex",
      "ambiguity": true,
      "enhancement_level": "Clarification"
    }
  }
}
```

Configurable via env vars from your appendix (enabled flag, min complexity, max tokens, timeout, debug).[5]

***

## 3. Layer 2 – Forced‑eval clarifier and skill router

This layer implements the high‑leverage bits from Prompt Improver and the skill‑activation research.[11][6][4][3]

### 3.1 Forced‑eval clarity check

In **Framework** level, the bridge adds a short pre‑amble:

> Evaluate the prompt and conversation history.\  
> 1. Is this clear enough to act safely without clarification? Answer `CLEAR` or `UNCLEAR`.\  
> 2. If `UNCLEAR`, ask 1–6 focused questions rooted in available context (code, docs, etc.) and then stop.\  
> 3. Do not perform the task until questions are answered.

This mirrors Prompt Improver’s flow (hook evaluates clarity; if unclear, ask researched questions) but stays local to your setup.[4][11]

### 3.2 Skill selection forced‑eval

Combine with the skills‑activation pattern:

> For each relevant task type or skill, decide whether it should be activated. For each, respond with `YES` or `NO` and a one‑sentence justification. Once you write `YES` for a skill, you must use it.

You keep the list of potential skills / task types small and context‑aware (from domain + competence layer), avoiding multi‑skill prompt explosion.[6][3]

Output from this reasoning is then used by Claude Code to:

- choose a skill/tool, or  
- stay in general mode but still obey the competence contract for the selected task type.

***

## 4. Layer 3 – Competence / contract layer

This is mostly as you already have it, but **fed by Layer 1+2 context**.[5]

### 4.1 Task‑type contracts

Example contracts:

- **research**: `sources[]`, `findings`, `confidence`, `open_questions`.  
- **implementation**: `implementation_summary`, `changed_files`, `testing_notes`, `risk_notes`.  
- **planning**: `plan_steps[]`, `assumptions`, `risks`, `next_step_question` when intent is ambiguous.  
- **debugging**, **refactor**, etc., with appropriate fields.

Contracts live in JSON/YAML; your competence layer knows this taxonomy and ensures every final response for that task type fills all required fields.[5]

### 4.2 Stop‑hook validation

A Stop (or post‑planning/post‑tool) hook:

- Reads: last assistant message, selected task type, contract schema.  
- Validates: Are all required fields present and non‑empty?  
- On failure:  
  - injects a “self‑repair” instruction (“You omitted `testing_notes`; add them now in a short bullet section.”), or  
  - if repeated failures, prompts you to escalate (e.g., manually call `/prompt_refiner`).[12][2][5]

The competence layer can also share its **domain/complexity classification** back to Layer 1 for logging, closing the loop.

***

## 5. Layer 4 – Governance, safety, and observability

This layer pulls ideas straight from Hooks Mastery, Prompt Improver tests, and observability setups.[13][8][1][2]

### 5.1 Safety & permissions

- **Prompt validation & security filtering (UserPromptSubmit + PreToolUse)**  
  - Block obviously dangerous commands (`rm -rf`, direct edits to protected paths, production deploy scripts) or downgrade them to “plan‑only” mode.[7][2]
  - Combine with your clarification bridge: if a dangerous action isn’t clearly requested, force clarification before allowing the tool.

- **Permission‑based tool access**  
  - For each repo or branch, define which tools are allowed; PreToolUse hook enforces this.[2]
  - This sits orthogonal to competence: even a valid contract cannot bypass environment policy.

### 5.2 Builder/validator pattern (optional but powerful)

For higher‑risk operations:

- **Builder agent** (normal Claude Code flow) generates plan or code.  
- **Validator agent** (via a hook‑triggered secondary call, à la Hooks Mastery) reviews it against checklists (tests, security, style) before commands/files are applied.[1][7]
- If validator is unhappy, the hook blocks execution and requests revisions.

You can scope this to specific domains (security, migrations, infra) where you want extra rigor.

### 5.3 Observability pipeline

Adopt a simple version of the multi‑agent observability approach:

- Hooks emit structured JSON logs for:  
  - prompt analysis (domain, complexity, ambiguity, enhancement level),  
  - forced‑eval decisions (CLEAR/UNCLEAR; skill YES/NO),  
  - contract validation passes/fails,  
  - blocked commands / dangerous ops.[8][14]
- A tiny local HTTP collector or file‑based log ingester writes into SQLite or similar for dashboards and offline analysis.[13][8]

This lets you empirically tune:

- ambiguity heuristics and complexity thresholds,  
- which clarification patterns work,  
- where contracts are frequently violated (`next_step_question`, `sources`, `recommendation` gaps).[5]

***

## 6. Operational strategy

- **Phase 1**: Implement Prompt Enhancement Bridge as standalone soft‑clarification hook + basic metrics; keep `/prompt_refiner` manual.[5]
- **Phase 2**: Integrate forced‑eval clarity and skill selection, and wire competence contracts to share the same context; start basic safety filters.[3][4][2]
- **Phase 3**: Add builder/validator flows and richer observability dashboards; optionally auto‑wire a prompt‑improver‑style skill for expert/critical prompts only.[4][8][1]

If you’d like, I can next sketch concrete file layouts and example hook JSON/Python stubs for each layer so you can paste them into `.claude/hooks` and iterate from there.

## Human

Is this missing too many high value features?
"
❯ Counter-Proposal: Three-Layer Design, agreed.  please enhance the solution but don't implement yet.

● I'll enhance the three-layer design with more technical detail while keeping it as a proposal (no
  implementation).

  ---
  Enhanced Three-Layer Design

  Date: 2026-02-15
  Status: Enhanced Proposal - Ready for Review
  Scope: Solo development workflow, fail-open, token-efficient

  ---
  Layer 1: Prompt Enhancement Bridge

  Purpose

  Detect ambiguity and inject appropriate enhancement before Claude processes the prompt.

  Input/Output Contract

  # Input (from UserPromptSubmit hook event)
  {
      "prompt": str,
      "cwd": str,
      "transcript": list[dict],  # Recent conversation turns
      "session_id": str,
      "terminal_id": str
  }

  # Output (via additionalContext)
  {
      "decision": "allow",
      "hookSpecificOutput": {
          "additionalContext": str,  # Enhancement text or empty
          "debug": {
              "domain": str,
              "complexity": str,
              "ambiguity_score": float,
              "enhancement_applied": str
          }
      }
  }

  Analysis Algorithms

  Domain Detection (Enhanced)

  # Priority order: path hints > keyword patterns > fallback

  def detect_domain(prompt: str, cwd: str) -> str:
      # 1. Path-based detection (highest confidence)
      path_signals = {
          "security": ["sec", "auth", "identity", "access", "crypto"],
          "architecture": ["arch", "design", "pattern", "struct"],
          "performance": ["perf", "optim", "cache", "db"],
          "debugging": ["bug", "fix", "issue", "err"],
          "testing": ["test", "spec", "mock", "cov"],
      }

      # 2. Keyword detection with domain scoring
      keyword_signals = {
          "security": ["vulnerability", "xss", "injection", "auth", "encrypt"],
          "architecture": ["scalable", "microservice", "coupling", "pattern"],
          # ...
      }

      # 3. Return highest scoring domain or "general"

  Complexity Assessment (Refined)

  def assess_complexity(prompt: str) -> tuple[str, float]:
      """
      Returns (complexity_level, confidence_score)

      Complexity levels:
      - simple: ≤10 words, "what is X" patterns
      - moderate: 10-30 words, "explain/compare X"
      - complex: 30-60 words, "design/implement X", multi-clause
      - expert: 60+ words, "framework/paradigm X", abstract concepts
      """

      word_count = len(prompt.split())

      # Base score from word count
      base_score = min(1.0, word_count / 60)

      # Adjust for structural complexity
      structural_indicators = [
          (r"\\bbecause\\b, \\balthough\\b, \\bhowever\\b", 0.1),  # Subordination
          (r"\\band\\b.*\\band\\b.*\\band\\b", 0.15),              # Compound complexity
          (r"\\b(?:therefore|thus|consequently)\\b", 0.1),      # Logical flow
      ]

      # Adjust for technical density
      technical_terms = count_technical_terms(prompt)
      technical_bonus = min(0.2, technical_terms * 0.05)

      final_score = base_score + structural_bonus + technical_bonus

      if final_score < 0.2:
          return "simple", final_score
      elif final_score < 0.5:
          return "moderate", final_score
      elif final_score < 0.8:
          return "complex", final_score
      return "expert", final_score

  Ambiguity Detection (Nuanced)

  def check_ambiguity(prompt: str, transcript: list[dict]) -> tuple[bool, list[str], float]:
      """
      Returns (is_ambiguous, indicators, ambiguity_score)

      Ambiguity indicators:
      - Pronouns without antecedent ("it", "that", "this")
      - Vague verbs ("fix", "optimize", "improve" without target)
      - Missing context ("make it better")
      - Short prompts with implicit assumptions
      - Conflicting signals from transcript
      """

      indicators = []
      score = 0.0

      # 1. Pronoun antecedent check
      pronouns = ["it", "that", "this", "they", "them"]
      for pronoun in pronouns:
          if prompt.lower().count(pronoun) > 1:
              # Multiple uses without clear referent
              indicators.append(f"unclear antecedent: '{pronoun}'")
              score += 0.2

      # 2. Vague action verb check
      vague_actions = {
          "fix": "what is broken?",
          "optimize": "what metric?",
          "improve": "what aspect?",
          "implement": "what specification?",
          "add": "where and what?",
      }
      for verb, question in vague_actions.items():
          if f" {verb} " in prompt.lower():
              # Check if target follows verb
              target_pattern = rf"{verb}\\s+(\\w+)"
              if not re.search(target_pattern, prompt, re.IGNORECASE):
                  indicators.append(f"vague action: '{verb}' ({question})")
                  score += 0.3

      # 3. Length-based ambiguity
      if len(prompt.split()) <= 5:
          indicators.append("very brief - lacks context")
          score += 0.15

      # 4. Transcript coherence check
      if transcript:
          recent_topics = extract_recent_topics(transcript[-3:])
          if not has_topic_continuity(prompt, recent_topics):
              indicators.append("topic shift without context")
              score += 0.1

      is_ambiguous = score >= 0.3 or len(indicators) >= 2
      return is_ambiguous, indicators, score

  Enhancement Templates

  Clarification Template (Ambiguous)

  ## Clarification Needed

  Your request contains some ambiguity. Please address:

  {questions}

  **Current Understanding**: {understanding_statement}

  **Before proceeding**: Confirm your intent so I can provide the most helpful response.

  Question generation rules:
  - Security → ask about threat model, assets, requirements
  - Architecture → ask about constraints, existing patterns, scale
  - Debugging → ask about error messages, reproduction steps, context
  - Performance → ask about baseline, target metrics, profiling data
  - General → ask about goal, context, constraints

  Guidance Template (Moderate Complexity)

  ## Response Context

  **Domain**: {domain}
  **Task Type**: {task_type}

  Provide a structured response that includes:
  - Analysis of the request
  - Recommended approach with alternatives
  - Considerations for {domain}
  - Next steps or confirmation needed

  Framework Template (Complex/Expert)

  ## Enhanced Analysis Mode

  **Domain**: {domain}
  **Complexity**: {complexity}
  **Intent**: {intent}

  This request benefits from structured analysis. Consider:

  {technique_specific_guidance}

  **Output Requirements**:
  - Systematic breakdown of the problem
  - Evaluation of multiple approaches
  - Clear recommendation with rationale
  - Identification of risks and assumptions

  Technique-specific guidance:
  - Socratic: "Ask and answer clarifying questions before concluding"
  - Chain-of-Verification: "Verify each claim; cite sources for factual statements"
  - Self-Refine: "Propose solution, then critique and improve it"

  Performance Targets

  ┌───────────────────────────────┬─────────┬───────────────────────────────┐
  │            Metric             │ Target  │           Rationale           │
  ├───────────────────────────────┼─────────┼───────────────────────────────┤
  │ Simple prompts (pass-through) │ < 10ms  │ Overhead should be negligible │
  ├───────────────────────────────┼─────────┼───────────────────────────────┤
  │ Moderate prompts (guidance)   │ < 30ms  │ Quick pattern matching        │
  ├───────────────────────────────┼─────────┼───────────────────────────────┤
  │ Complex prompts (framework)   │ < 100ms │ Full analysis acceptable      │
  ├───────────────────────────────┼─────────┼───────────────────────────────┤
  │ Timeout fallback              │ 500ms   │ Fail-fast to avoid blocking   │
  └───────────────────────────────┴─────────┴───────────────────────────────┘

  Configuration

  # Environment variables
  PROMPT_ENHANCEMENT_ENABLED=true
  PROMPT_ENHANCEMENT_AMBIGUITY_THRESHOLD=0.3  # Score triggering clarification
  PROMPT_ENHANCEMENT_COMPLEXITY_THRESHOLD=0.5  # Score triggering framework
  PROMPT_ENHANCEMENT_DEBUG=false                # Enable debug output
  PROMPT_ENHANCEMENT_SOFT_MODE=true             # Don't block on ambiguity

  ---
  Layer 2: Task-Type Detection & Contract Injection

  Purpose

  Determine the task type and inject the appropriate output contract template.

  Task Type Taxonomy (Enhanced)

  TASK_TYPES = {
      "research": {
          "description": "Investigate and synthesize information",
          "triggers": ["research", "investigate", "find out about", "what is"],
          "required_fields": ["sources", "findings", "confidence", "open_questions"],
          "optional_fields": ["methodology", "limitations"],
          "synonyms": {"analyze": "research", "explore": "research"},
      },
      "implementation": {
          "description": "Write or modify code",
          "triggers": ["implement", "add", "create", "write", "build"],
          "required_fields": ["implementation_summary", "changed_files", "testing_notes"],
          "optional_fields": ["risk_notes", "alternatives_considered"],
          "synonyms": {"code": "implementation", "develop": "implementation"},
      },
      "planning": {
          "description": "Design or plan approach",
          "triggers": ["plan", "design", "architecture", "approach"],
          "required_fields": ["plan_steps", "assumptions", "risks"],
          "conditional_fields": {
              "next_step_question": "ambiguity_detected"
          },
          "synonyms": {"architecture": "planning", "strategy": "planning"},
      },
      "debugging": {
          "description": "Diagnose and fix issues",
          "triggers": ["debug", "fix", "broken", "error", "not working"],
          "required_fields": ["root_cause", "fix_description", "verification_steps"],
          "optional_fields": ["prevention_measures"],
          "synonyms": {"troubleshoot": "debugging", "repair": "debugging"},
      },
      "validation": {
          "description": "Verify or review work",
          "triggers": ["verify", "validate", "review", "check", "test"],
          "required_fields": ["validation_summary", "issues_found", "recommendations"],
          "optional_fields": ["coverage_details"],
          "synonyms": {"review": "validation", "audit": "validation"},
      },
      "meta": {
          "description": "Meta-operations (no contract)",
          "triggers": ["/", "help", "status", "list"],
          "required_fields": [],
          "skip_contract": True,
      }
  }

  Detection Algorithm

  def detect_task_type(prompt: str, domain: str, complexity: str) -> str:
      """
      Multi-factor task type detection:

      1. Explicit triggers (keyword matching)
      2. Domain context (security → validation/research)
      3. Complexity bias (simple → implementation, complex → planning)
      4. Skill invocation (/command → meta)
      """

      # 1. Skill/command check (highest priority)
      if prompt.strip().startswith("/"):
          return "meta"

      # 2. Explicit trigger keywords
      prompt_lower = prompt.lower()
      task_scores = {}

      for task_type, config in TASK_TYPES.items():
          if config.get("skip_contract"):
              continue

          score = 0
          for trigger in config["triggers"]:
              if trigger in prompt_lower:
                  score += 1

          if score > 0:
              task_scores[task_type] = score

      if task_scores:
          # Return highest-scoring task type
          return max(task_scores, key=task_scores.get)

      # 3. Domain-based inference
      domain_defaults = {
          "security": "research",      # Security requires analysis
          "debugging": "debugging",    # Explicit domain
          "testing": "validation",     # Testing is validation
      }

      if domain in domain_defaults:
          return domain_defaults[domain]

      # 4. Complexity-based default
      if complexity in ["simple", "moderate"]:
          return "implementation"  # Assume doing
      return "planning"  # Assume designing

  Contract Injection Template

  ## Output Contract: {task_type}

  Your response must include these sections:

  {required_sections}

  {conditional_sections}

  {optional_sections_note}

  Example for implementation:

  ## Output Contract: Implementation

  Your response must include:

  ### Implementation Summary
  - Brief description of what was implemented and why

  ### Changed Files
  - List of files modified or created with brief notes

  ### Testing Notes
  - How the implementation was tested
  - Any known limitations or edge cases

  {if_ambiguous}
  ### Next Steps
  - Clarifying question about what to do next
  {/if}

  Synonym Handling

  def normalize_field_names(output: dict, task_type: str) -> dict:
      """
      Normalize output fields to match contract requirements.

      Handles synonyms and variations:
      - "code" → "implementation_summary"
      - "files" → "changed_files"
      - "tests" → "testing_notes"
      """

      config = TASK_TYPES[task_type]
      synonyms = config.get("synonyms", {})

      normalized = {}
      for field, value in output.items():
          # Check if field is a synonym for a required field
          matched = False
          for canonical, syn in synonyms.items():
              if field.lower() == syn.lower():
                  normalized[canonical] = value
                  matched = True
                  break

          if not matched:
              normalized[field] = value

      return normalized

  ---
  Layer 3: Observability & Continuous Improvement

  Purpose

  Collect data to tune the system and detect patterns.

  Event Schema

  {
      "timestamp": "2026-02-15T10:30:00Z",
      "session_id": "abc123",
      "terminal_id": "env_456",
      "event_type": "prompt_analysis",

      # Input
      "prompt_length": 45,
      "prompt_hash": "sha256...",

      # Analysis
      "detected_domain": "security",
      "detected_complexity": "moderate",
      "detected_task_type": "implementation",
      "ambiguity_score": 0.35,
      "ambiguity_indicators": ["vague action: 'implement'"],

      # Action taken
      "enhancement_applied": "clarification",
      "enhancement_tokens": 120,
      "clarification_questions": ["What specification?", "Where should this fit?"],

      # Outcome (filled at Stop hook)
      "contract_compliant": true,
      "missing_fields": [],
      "user_satisfied": null,  # Could be inferred from follow-up
  }

  Metrics to Track

  ┌──────────────────────────┬────────────────────────────────────────────────┬───────────────────────────┐
  │          Metric          │                    Purpose                     │     Action Threshold      │
  ├──────────────────────────┼────────────────────────────────────────────────┼───────────────────────────┤
  │ Ambiguity detection rate │ How often we ask for clarification             │ > 40% → lower threshold   │
  ├──────────────────────────┼────────────────────────────────────────────────┼───────────────────────────┤
  │ Contract compliance rate │ How often outputs meet contracts               │ < 70% → improve templates │
  ├──────────────────────────┼────────────────────────────────────────────────┼───────────────────────────┤
  │ Most missing fields      │ Which fields are consistently omitted          │ Top 3 → fix template      │
  ├──────────────────────────┼────────────────────────────────────────────────┼───────────────────────────┤
  │ Enhancement timeout rate │ How often analysis times out                   │ > 5% → optimize algorithm │
  ├──────────────────────────┼────────────────────────────────────────────────┼───────────────────────────┤
  │ Domain accuracy          │ How often domain detection matches user intent │ < 80% → improve patterns  │
  └──────────────────────────┴────────────────────────────────────────────────┴───────────────────────────┘

  Feedback Loops

  # At Stop hook: validate and log
  def validate_contract(output: str, task_type: str) -> dict:
      """
      Check if output contains all required fields.
      Returns validation result and logs gaps.
      """

      required = TASK_TYPES[task_type]["required_fields"]
      present = extract_sections(output)

      missing = [f for f in required if f not in present]

      log_event({
          "event_type": "contract_validation",
          "task_type": task_type,
          "required_fields": required,
          "present_fields": list(present.keys()),
          "missing_fields": missing,
          "contract_compliant": len(missing) == 0,
      })

      return {
          "compliant": len(missing) == 0,
          "missing": missing,
          "message": build_repair_message(missing) if missing else ""
      }

  Dashboard Queries (SQLite)

  -- Most ambiguous domains
  SELECT domain, AVG(ambiguity_score) as avg_ambiguity, COUNT(*) as freq
  FROM events
  WHERE event_type = 'prompt_analysis'
  GROUP BY domain
  ORDER BY avg_ambiguity DESC;

  -- Contract compliance by task type
  SELECT task_type,
      AVG(CASE WHEN contract_compliant THEN 1 ELSE 0 END) as compliance_rate,
      COUNT(*) as total
  FROM events
  WHERE event_type = 'contract_validation'
  GROUP BY task_type
  ORDER BY compliance_rate ASC;

  -- Most missing fields
  SELECT json_each(missing_fields).value as field, COUNT(*) as freq
  FROM events
  WHERE event_type = 'contract_validation' AND json_array_length(missing_fields) > 0
  GROUP BY field
  ORDER BY freq DESC;

  Adaptive Thresholds

  def adjust_thresholds(metrics: dict) -> dict:
      """
      Adjust detection thresholds based on performance metrics.
      """

      current = get_current_thresholds()
      adjustments = {}

      # Ambiguity threshold
      ambiguity_rate = metrics.get("ambiguity_detection_rate", 0)
      if ambiguity_rate > 0.4:
          adjustments["ambiguity_threshold"] = current["ambiguity_threshold"] + 0.1
      elif ambiguity_rate < 0.1:
          adjustments["ambiguity_threshold"] = current["ambiguity_threshold"] - 0.05

      # Complexity threshold
      timeout_rate = metrics.get("enhancement_timeout_rate", 0)
      if timeout_rate > 0.05:
          # Reduce framework usage to avoid timeouts
          adjustments["complexity_threshold"] = current["complexity_threshold"] + 0.1

      return adjustments

  ---
  Integration Points

  With Existing Systems

  ┌──────────────────┬───────────────────────────────────────────────────────────────────────────┐
  │ Existing System  │                            Integration Method                             │
  ├──────────────────┼───────────────────────────────────────────────────────────────────────────┤
  │ Competence Layer │ Share task type detection; use same contract definitions                  │
  ├──────────────────┼───────────────────────────────────────────────────────────────────────────┤
  │ Semantic Daemon  │ Query for context about recent work in this domain                        │
  ├──────────────────┼───────────────────────────────────────────────────────────────────────────┤
  │ CKS/CHS          │ Retrieve relevant patterns when building clarification questions          │
  ├──────────────────┼───────────────────────────────────────────────────────────────────────────┤
  │ Skills System    │ Skip enhancement for /skill invocations (skills handle their own prompts) │
  └──────────────────┴───────────────────────────────────────────────────────────────────────────┘

  Hook Registration (Proposed)

  {
    "hooks": {
      "UserPromptSubmit": [
        {
          "matcher": ".*",
          "hooks": [
            {
              "type": "command",
              "command": "python P:/.claude/hooks/UserPromptSubmit_prompt_enhancement.py --timeout 1.0",
              "timeout": 1
            }
          ]
        }
      ],
      "Stop": [
        {
          "matcher": ".*",
          "hooks": [
            {
              "type": "command",
              "command": "python P:/.claude/hooks/Stop_contract_validator.py --timeout 0.5",
              "timeout": 1
            }
          ]
        }
      ]
    },
    "env": {
      "PROMPT_ENHANCEMENT_ENABLED": "true",
      "PROMPT_ENHANCEMENT_SOFT_MODE": "true",
      "CONTRACT_VALIDATION_ENABLED": "true"
    }
  }

  ---
  Phased Rollout

  Phase 1: Core Enhancement (1-2 days)

  - Layer 1: Ambiguity detection + clarification injection
  - Layer 2: Task type detection + basic contract injection
  - Layer 3: Basic logging (file-based)

  Success criteria:
  - Ambiguity correctly identified in >70% of test cases
  - No noticeable latency for simple prompts
  - Logs show expected data capture

  Phase 2: Refinement (1 week)

  - Fine-tune detection thresholds based on metrics
  - Enhance templates based on missing field patterns
  - Add domain-specific clarification patterns

  Success criteria:
  - Contract compliance >80%
  - Ambiguity rate <30% (not annoying users)
  - Most missing fields addresses by template improvements

  Phase 3: Advanced Features (optional)

  - Integration with prompting-framework for complex queries
  - Adaptive thresholds based on metrics
  - Dashboard for observability

  ---
  Open Questions for Decision

  1. Soft vs Hard clarification: Soft (inject questions, continue) vs Hard (stop and wait)?
    - Recommendation: Soft initially, can add hard mode for dangerous operations
  2. Contract enforcement: Warn only vs Block vs Self-repair injection?
    - Recommendation: Warn only during Phase 1, consider self-repair for Phase 2
  3. Logging retention: How long to keep event logs?
    - Recommendation: 30 days rolling window, aggregate metrics retained longer
  4. Metric visibility: Dashboard vs CLI queries vs periodic reports?
    - Recommendation: CLI queries via simple Python script initially
  5. Framework integration: Is the async complexity worth it for complex queries?
    - Recommendation: Defer until Phase 3; measure if lightweight guidance is sufficient

  ---
  This is the enhanced proposal. Ready for your review and decisions on implementation approach."

## Assistant

It’s already very feature‑dense; what’s “missing” are mostly optional advanced layers (safety, explicit skill routing, and multi‑agent validation), not core high‑value pieces.[1][2][3][4]

### What you already have (high‑value)

Your proposal already includes several top‑tier features:

- Sophisticated **domain / complexity / ambiguity analysis** with scores and indicators.[1]
- **Clarification / guidance / framework templates** that adapt by domain and intent.[1]
- A solid **task‑type taxonomy + contract injection** (research, implementation, planning, debugging, validation, meta) with required/optional/conditional fields and synonym normalization.[1]
- A real **observability layer**: structured events, key metrics, SQL queries, and adaptive threshold logic.[1]
- **Phased rollout** and config via env vars, with soft mode and fail‑open behavior.[1]

This already covers most of what the Hooks Mastery & Prompt Improver ecosystems treat as “core” for reliability and clarity.[2][4][5]

### High‑value extras you might still add

If you want to push toward “maximal,” the main missing categories are:

1. **Safety & permissions layer**  
   - Add a small UserPromptSubmit/PreToolUse policy that:  
     - detects dangerous actions (e.g., destructive commands, prod config edits) and forces **hard clarification** for those, even if global mode is soft.[6][2]
     - enforces repo/branch‑specific tool permissions (what tools can be used where).[2]

2. **Explicit skill routing / forced eval**  
   - On complex/expert prompts, add a lightweight forced‑eval pattern:  
     - “Is this clear? CLEAR/UNCLEAR. Do we need a specialized task type/skill? YES/NO (which one?).”[3][7]
   - That makes task‑type detection partly model‑driven instead of purely heuristic, improving match with your competence layer.

3. **Builder/validator pattern for critical domains**  
   - For security, migrations, infra, etc., use a second “validator” call triggered by Stop hook to review plans/patches before execute, as in Hooks Mastery + multi‑agent observability setups.[4][8][9]

4. **Optional prompt‑improver integration**  
   - Keep your current design, but note a future Phase 3 option where “framework level + expert complexity” can auto‑call a prompt‑improver‑style flow for very high‑stakes prompts only.[5][10]

### Bottom line

Your enhanced three‑layer proposal already captures most high‑leverage features for clarity, structure, and learning over time. Adding a thin **safety/permissions layer**, **explicit skill routing**, and a **validator pass for risky tasks** would round it out into a near “maximal” system without bloating the core.
