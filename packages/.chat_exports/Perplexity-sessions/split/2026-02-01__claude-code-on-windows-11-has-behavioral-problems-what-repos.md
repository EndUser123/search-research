---
title: "claude code on windows 11, has behavioral problems.  What repos exist that deal with enhancing the cognitive architectur"
date: "2026-02-01"
mode: "COPILOT"
uuid: "d3ebddf5-37d6-461f-bcf5-0282e91daac7"
entry_count: 8
---

## Human

claude code on windows 11, has behavioral problems.  What repos exist that deal with enhancing the cognitive architecture via claude code hooks?

## Assistant

Several GitHub repositories provide hooks and tools to enhance Claude Code's cognitive architecture, addressing behavioral issues like false claims, lazy thinking, and poor context handling on Windows 11. These focus on validation, mental models, and verification via PreToolUse, Stop, and PostToolUse hooks, which align with your P:/.claude/hooks setup and past troubleshooting.[1][2][3][4]

## Key Repositories

| Repo | Focus | Windows 11 Relevance | Key Features |
|------|--------|-----------------------|--------------|
| [disler/claude-code-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery) [3] | Full hook lifecycle for prompt validation and context injection | Cross-platform; tested on Windows | Covers all 8 hook events; blocks invalid prompts; adds structured context to reduce assumptions. |
| [smykla-labs/klaudiush](https://github.com/smykla-labs/klaudiush) [4][5] | PreToolUse validation dispatcher for command parsing and quality checks | Go-based; native Windows support | Parses bash chains; enforces git workflows, code quality (shellcheck); prevents bad file ops. |
| [PaulDuvall/claude-code](https://github.com/PaulDuvall/claude-code) [6] | AI commands with debugging and architecture agents | Modular scripts; Windows-compatible | Persistent context for debugging; root cause analysis; /xdebug reduces false claims. |
| [decider/claude-hooks](https://github.com/decider/claude-hooks) [7] | Quality enforcement and notifications | Python-based; portable to Windows | Pre/PostToolUse for code standards; package age checks; hierarchical configs. |
| [rinadelph/rins_hooks](https://github.com/rinadelph/rins_hooks) [8] | Auto-commit and formatting with context tracking | Explicit Windows 11 PowerShell support | Post-edit hooks for git commits; reduces session amnesia; cross-OS notifications. |

## Implementation Tips
These repos use hooks to enforce mental models like verification checklists and state validation, bypassing Claude Code's transcript timing issues on v2.1.29. Start with disler/claude-code-hooks-mastery for broad coverage, then layer klaudiush for tool validation—both integrate into ~/.claude/hooks without MCP overhead. Test in your multi-terminal Windows 11 setup via git worktrees, as they handle PowerShell and avoid Docker.[9][1][10][3][11]

## Human

Are these the most popular?

## Assistant

No, the listed repositories are specialized but not the absolute most popular in the Claude Code hooks ecosystem, which favors curated collections and ready-to-use kits over niche cognitive enhancements. Popularity metrics (stars, forks, Reddit mentions) highlight broader "awesome" lists and plug-and-play hook packs, though your targets like disler/claude-code-hooks-mastery remain highly relevant for behavioral fixes.[1][2][3][4]

## Top Popular Repos
These lead by GitHub stars (100s–1k+), community curation, and adoption in awesome lists.[2][5]

| Repo | Stars/Forks (est.) | Focus | Cognitive/Behavioral Fit |
|------|---------------------|--------|--------------------------|
| [hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code) [2] | High (curated top list) | Hooks, skills, orchestrators | Showcases Claude CodePro (quality hooks, memory), Context Priming (disler), TDD Guard. |
| [karanb192/claude-code-hooks](https://github.com/karanb192/claude-code-hooks) [1][6] | Leading (Reddit deep dive) | Safety, automation hooks | Notifications, validation; blocks bad behaviors pre-tool use. |
| [disler/claude-code-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery) [3][2] | Strong (featured in awesomes) | Full lifecycle mastery | Prompt validation, context injection; directly enhances cognition. |
| [cc-tools (Josh Symonds)](https://github.com topics from ) | High-performance Go hooks | Linting, testing | Minimal overhead quality gates reduce lazy outputs. |
| [Claude CodePro (Max Ritter)](https://github.com topics from ) | Feature-packed | TDD, memory, rules | Cross-session memory, semantic search for better state awareness. |

## Relevance to You
For Windows 11 behavioral issues (e.g., claim verification, hook staleness), start with awesome-claude-code's recommendations like disler and klaudiush—these overlap your prior explorations and outperform general hooks in validation depth. Popular kits like karanb192 integrate easily into P:/.claude/hooks without version conflicts.[7][8][9][2]

## Human

Please, I mean the most popular that deal with behavioral issues.

## Assistant

No, while the previously listed repos are effective for behavioral fixes, the most popular ones specifically targeting Claude Code issues like lazy thinking, false claims, and poor verification emphasize quality gates, TDD enforcement, and prompt validation via hooks. These gain traction through "awesome" lists (100s–1k+ stars), Reddit discussions, and Anthropic docs, outperforming niche cognitive repos in adoption.[1][2][3][4]

## Most Popular Behavioral Repos
Ranked by mentions in awesome lists, stars, and community buzz for validation/blocking behaviors.[4][1]

| Repo/Tool | Popularity Signals | Behavioral Fixes | Windows Fit |
|-----------|---------------------|------------------|-------------|
| [Claude CodePro (Max Ritter)](https://github.com via ) [1] | Top in awesome-claude-code; wide coverage | TDD enforcement, quality hooks, cross-session memory to curb laziness/false claims | Modular; script-based for Windows. |
| [claudekit (Carl Rannaberg)](https://github.com via ) [1][4] | 20+ subagents; featured heavily | Code-reviewer agent (6-aspect analysis), quality hooks, auto-checkpointing | CLI toolkit; native PowerShell support. |
| [TDD Guard (Nizar Selander)](https://github.com via ) [4] | 1.7k est. stars; real-time blocking | Monitors file ops, blocks TDD violations (prevents lazy/incomplete work) | Hooks-driven; cross-platform. |
| [disler/claude-code-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery) [5][1] | Frequent awesome mentions | Prompt validation, context injection, PreToolUse blocking | Full lifecycle; Windows-tested. |
| [TypeScript Quality Hooks (bartolli)](https://github.com via ) [4] | 158+ stars; <5ms perf | ESLint/Prettier auto-fix, compilation checks | Node.js focus; fast for your TS/Python mix. |

## Quick Integration
Copy hooks from these into P:/.claude/hooks, prioritizing Pre/PostToolUse for claim verification—e.g., TDD Guard blocks untested edits, directly fixing your v2.1.29 staleness issues. They use exit codes for blocking (non-zero prevents ops), bypassing transcript races. Test with your git worktrees for seamless Windows 11 multi-terminal use.[5][2][6][7]

## Human

What are the behavioral or cognitive domains that are addressed by the repos?

## Assistant

Repos targeting Claude Code behavioral issues primarily address domains like verification (false claims), diligence (lazy/incomplete work), context persistence (amnesia), and security (dangerous actions) through hooks that validate prompts, block bad tools, and enforce workflows. These map to cognitive shortcomings such as overconfidence, recency bias, and lack of self-checks, using PreToolUse/PostToolUse for real-time intervention.[1][2][3][4]

## Core Domains Addressed

| Domain | Description | Example Repos/Tools | Mechanisms |
|--------|-------------|---------------------|------------|
| Claim Verification | Detects/prevents false task completion claims or assumptions | disler/claude-code-hooks-mastery [1], smykla-labs/klaudiush [5] | PostToolUse result checks; Stop hook blocks unverified stops (exit code 2). |
| Diligence Enforcement | Counters lazy thinking/incomplete work via TDD/quality gates | TDD Guard [6], TypeScript Quality Hooks [6], Claude CodePro [2] | PreToolUse blocks non-TDD edits; ESLint/Prettier auto-fixes; test pass validation. |
| Context Persistence | Reduces session amnesia/recency bias with priming/memory | Context Priming (disler) [2], Claude Session Restore [3], claudekit [2] | SessionStart loads git history/CLAUDE.md; semantic search over transcripts. |
| Security/Guardrails | Blocks dangerous commands (rm -rf, sudo) proactively | PreToolUse in disler [1], CC Notify [3] | Pattern matching on tool_input; JSON "decision: block" with reasons. |
| Completion Control | Forces continuation until tasks truly done (Ralph loops) | Stop/SubagentStop hooks [1], Ralph Orchestrator [3] | Exit 2 on incomplete markers; feeds reasons back to Claude. |

## Usage Notes
Hooks like UserPromptSubmit inject mental models (e.g., checklists) pre-generation, while PreCompact backs up transcripts to avoid data loss—directly fixing your Windows 11 hook staleness. Popular awesome lists validate these as top patterns for behavioral reliability. Integrate via .claude/hooks/ with uv scripts for your Python/PowerShell setup.[2][3][7][1]

## Human

What are the behavioral complaints people have most often with ai-assisted coding?

## Assistant

AI-assisted coding tools like Claude Code face frequent complaints about overconfidence, inconsistency, and quality shortfalls, based on Reddit, HN, and dev forums. These stem from context handling flaws and lack of rigor, often labeled "lazy dev syndrome."[1][2][3][4][5]

## Top Complaints
- **False claims of completion**: AI asserts tasks done despite bugs, non-compiling code, or missing tests; ignores evidence like failing builds.[4][1]
- **Lazy/incomplete work**: Skips steps, marks ~70% done as finished, or generates placeholders instead of real tests/solutions.[6][3][5]
- **Ignores instructions**: Drifts from prompts despite corrections; requires 3+ reiterations; bypasses CLAUDE.md rules.[2][1]
- **Hallucinations & bad code**: Confident errors, non-functional code, or suboptimal/clunky implementations that smell "AI-generated."[7][8][9]
- **Context pollution/amnesia**: Recency bias floods attention with noise over docs; long sessions degrade performance.[3][5]

## Fixes in Practice
Hooks from repos like disler/claude-code-hooks-mastery enforce verification gates (e.g., block untested edits), directly tackling these on Windows 11. Communities recommend compacting transcripts early and using checklists to counter bias.[5][10][11][1]

## Human

Please review the file, and let me know what gaps or opportunties we have, when compared against the cognitive domains and top complaints.

## Assistant

You already cover most of the major behavioral/cognitive complaints extremely well; the remaining gaps are mostly around *proactive* planning quality, *human-facing UX*, and *explicit load-shedding / scope control* rather than more gates.[1][2]

## Mapping to top complaints

Using the common complaints we just outlined (false claims, lazy/incomplete work, ignored instructions, hallucinations/bad code, context amnesia), here’s how your CSF catalog lines up.[3][4][1]

- False claims of completion / overconfidence  
  - Strong coverage via Stop-layer truth & evidence hooks: `StopHook_overconfidence_detector.py`, `stop_success_validator.py`, `StopHook_cross_validator.py`, `empirical_claims_gate.py`, `verify_claims_transcript.py`, plus PostToolUse evidence trackers.[4][1]
  - **Gap:** Most of this is *stop-time*, not *plan-time*; there’s little that scores the *initial plan* for feasibility/coverage before work begins (cf. “plan reviewers” in Claude CodePro/claudekit).[5]

- Lazy / incomplete work (“lazy dev syndrome”)  
  - Good coverage: TDD gates (`pretooluse_tdd_gate.py`, `PostToolUse_tdd_state.py`), lazy-closure detectors and behavioral quality gate at Stop, investigation gates (`PreToolUse_investigation_gate.py`, `StopHook_investigation_required.py`).[6][1]
  - **Gap:** No explicit “minimum work” heuristics on *per-edit* basis (e.g., forbidding trivial diffs that don’t address the stated defect, or scoring PR-sized changes like TDD Guard does).[7]

- Ignores instructions / drifts from prompt  
  - Partial coverage: `skill_enforcement` + `skill_enforcement_gate.py`, `subagent_enforcer`, and `StopHook_skill_execution_gate.py` enforce workflows; `cognitive_framework` and `unified_injector` inject goals and solo-dev framing.[1]
  - **Gap:** Nothing explicitly monitors *instruction adherence over time* (e.g., tracking a structured checklist derived from the user request and blocking when items remain unchecked), which is a common pattern in popular repos.[8][9]

- Hallucinations / bad or clunky code  
  - You have syntax and some structural quality: `PreToolUse_syntax_gate.py`, `PostToolUse_code_verification_gate.py`, `PostToolUse_lint_router.py`, plus falsification hooks and `PostToolUse_truth_validator.py`.[1]
  - **Gaps:**
    - No language-specific *semantic quality* checks (e.g., TypeScript/pytest-focused “does this actually test behavior X?” like TS Quality Hooks / TDD Guard).[7]
    - No explicit “complexity/maintainability” heuristics for generated code (cyclomatic complexity, long functions, obvious duplication) to counter “AI smell” complaints.[10]

- Context amnesia / recency bias  
  - Very strong behavior: CKS system (`SessionStart_cks_decision_load.py`, `cks_context`, `auto_cks_storage.py`, `Stop_cks_decision_capture.py`) and session restore; `post_compact_reminder.py`, `session_change_tracker.py`, semantic compression.[1]
  - **Gap:** No explicit *session length / drift* governor that says “this transcript is now dirty, start a fresh session and re-derive a clean plan,” which shows up in community best-practices and “lazy dev” fixes.[11][4]

## Cognitive domains you already cover well

From your own “By Functional Domain” section, plus the community domains:

- Truth & evidence enforcement – extremely rich; this is your strongest domain (investigation ledger, empirical gates, speculation gates, cross-validation, evidence tracking).[12][1]
- Quality & behavioral gates – strong: overconfidence, sycophancy, lazy closure, behavioral quality gate, success validator.[1]
- Investigation & research – strong: vague-directive gate, investigation gate, speculation detector, pre-generation library registry.[1]
- Path & file safety – strong: path orchestrator, file locking, shell complexity/unparseable gates, semantic routing.[1]
- Task & session management – strong: task trackers, artifact gates, automatic checkpoints and CKS storage.[1]
- Cognitive frameworks – strong: solo-dev/goal anchor, diagnostic injection, strategy frameworks (4-horizon, etc.).[1]

Relative to popular repos, you’re *ahead* on: truth, evidence, path-safety, and investigation (you’re basically “hooks-mastery++”).[9][8]

## Gaps / opportunities by domain

Here are the main opportunities where community tools focus but your catalog is thinner.[5][7][1]

1. **Plan-time cognitive review (pre-generation, not just pre-tool/stop)**  
   - Missing: hooks that *score and revise the plan itself* before any tools run (coverage, risk hotspots, dependency checks), similar to claudekit’s architecture-review and multi-agent plan reviewers.[5]
   - Opportunity: a `UserPromptSubmit_plan_reviewer.py` or extension to `plan_context_injector` that:
     - Derives a checklist from the plan.  
     - Flags missing tests/migrations/rollback steps.  
     - Writes a “plan contract” that Stop hooks later enforce.

2. **Instruction adherence & checklist tracking across the whole task**  
   - Missing: persistent “requirements checklist” derived from the original user request, actively referenced by hooks.[13][9]
   - Opportunity:
     - `SessionStart_requirements_contract.py`: parse initial task spec into explicit obligations.  
     - `PostToolUse_requirements_progress.py`: map edits/tests back to that list.  
     - `Stop_requirements_gate.py`: block completion while unchecked items remain.

3. **Semantic code quality (beyond syntax/formatting)**  
   - Missing: domain-specific semantic checks like:
     - Tests that don’t assert anything meaningful.  
     - Silent failure paths, duplicated logic, or fragile patterns.  
   - Opportunity:
     - Language-aware PostToolUse hooks (Python, TS) that:
       - Run static analyzers / domain linters tuned to “AI smell.”[10]
       - Reject trivial or non-behavioral tests when a bugfix was requested.

4. **User-experience & cognitive load management**  
   - You have some UX detection (`concern_detection`, notifications), but not much around *interaction cost* or *frustration loops* over time.[2][1]
   - Opportunity:
     - A “frustration budget” tracker: after N blocked attempts / repeated clarifications, surface a different interaction mode (“switch to smaller scoped subtask?”).  
     - A hook that suggests *session reset* when drift metrics cross thresholds (many reversions, repeated failure patterns).

5. **Explicit scope management and load shedding**  
   - Missing: hooks that detect “mega-scope” tasks and force decomposition before proceeding, a common pain point in agentic tools.[14][12]
   - Opportunity:
     - `UserPromptSubmit_scope_analyzer.py`: detect multi-project/multi-domain prompts and suggest `/plan` + task splitting.  
     - Stop gate that blocks closure if the scope was never broken down (e.g., no TaskMaster items created for a project-scale request).

6. **Human-facing rationale / transparency layer**  
   - You log decisions (`hook_decisions_*.jsonl`) but don’t expose much human-readable “why was I blocked?” beyond whatever the hook prints.[1]
   - Opportunity:
     - A unified `decision_explainer` that aggregates active gates and presents a simple 3–line explanation + next best action, reducing frustration from “mysterious” refusals.

## Net assessment

- You are already at or beyond what popular repos do for **verification**, **truth**, **safety**, and **behavioral gating**; your Stop and PostToolUse layers are richer than most public kits.[8][9][1]
- The biggest remaining leverage is in **shaping the plan and interaction loop up front** (checklists, scope governance, plan reviewers) and **semantic quality checks** that look like a senior dev, not just a compiler.[2][10]

If you want, next step could be: design one “plan-time” hook trio (contract generator, progress tracker, closure gate) that plugs into your existing CKS + investigation ledger without fighting the Stop-hook timing constraints you’ve already uncovered.

## Human

Assuming I was going to rebuild my system, and address all the gaps & opportunities, what systems in what order would we want to start refactoring?

## Assistant

To rebuild and cover the gaps, refactor in layers, starting where you get the biggest behavioral leverage with the least risk: planning, scope, and adherence—then move into deeper quality semantics and UX.[1][2]

## 1. Plan-time system (before any tools run)

**Goal:** Turn “vibes-based” planning into a first-class artifact that downstream hooks can enforce.[3][4]

Refactor first:
- Add/extend a **Plan Contract generator** at UserPromptSubmit (or right after `/plan`):  
  - Derive acceptance criteria, explicit checklist items, and file/component touch list from the initial request.  
  - Store in session_data (JSON) + optional `plan.md`.[1][3]
- Add a **Plan validator** (pre-tool, non-blocking at first):  
  - Check for missing tests, rollout/rollback steps, and high-risk changes before any Write/Bash.[5][3]
- Wire Stop-layer gates to this contract:  
  - New `Stop_plan_contract_gate.py` that blocks completion if contract items remain unchecked, instead of only validating ad-hoc claims.[1]

Rationale: this directly attacks false-completion and ignores-instructions complaints, and everything else (TDD, falsification, CKS) can plug into this contract.[6][7]

## 2. Instruction adherence & checklist tracking

**Goal:** Make “did we do what the human actually asked?” a first-class metric across the whole session.[8][9]

Refactor second:
- Build a **Requirements extractor** at first UserPromptSubmit:  
  - Parse the user’s request into a normalized requirements/AC list; tie each to tags (files, endpoints, tests).[4][3]
- Add a **Progress tracker** in PostToolUse:  
  - Map each edit/test to the requirement IDs; keep a live checklist in session_data (and optional status file).[1]
- Add a **Stop_requirements_checker** gate:  
  - Block success if any requirements are unaddressed or only “hand-waved” without code/tests.

Rationale: this covers the “ignores instructions” and “implements only 70%” complaints more directly than your current evidence/overconfidence gates alone.[10][11]

## 3. Semantic code quality / “AI smell” layer

**Goal:** Move from “does it compile + lint?” to “does this look like something a senior dev would accept?”.[12][5]

Refactor third:
- Extend PostToolUse for **language-aware quality checks**:  
  - For Python/TS, plug in semantic analyzers that flag: no-assert tests, dead branches, huge functions, duplicated logic.[13][1]
- Add a **Quality score & heuristic gate**:  
  - Don’t necessarily block writes at first; start as a scoring/reporting hook that surfaces “AI smell” and suggests refactors, then optionally promote to blocking for critical paths.[2]
- Integrate with your existing `strategy_escalation_tracker.py` so low scores escalate strategy (e.g., require manual review or narrower scope).[1]

Rationale: addresses “bad/clunky code” and logic-bug risk that slips past syntax-only gates.[14][5]

## 4. Scope & session-governance system

**Goal:** Automatically manage scope explosions and dirty sessions to prevent “lazy dev syndrome” degradation.[7][15]

Refactor fourth:
- Add a **Scope analyzer** on UserPromptSubmit:  
  - Detect multi-project / multi-service / multi-tech-stack prompts and recommend or enforce decomposition into subtasks or tickets.[16][4]
- Add **Session drift and fatigue metrics**:  
  - Use your `session_change_tracker.py`, investigation ledger, and failure recorder to derive a “session health” score (reversions, repeated failures, compactions).[1]
- Add a **Session reset governor**:  
  - When health is poor, hooks suggest or require starting a fresh session with a summarized context rather than continuing degraded behavior.[7]

Rationale: this implements the community advice of “one major task per session” and combats the recency-bias/garbage-context spiral.[9][2]

## 5. Human-facing rationale & UX layer

**Goal:** Reduce frustration by making the system’s behavior legible and actionable when it blocks or nudges.[17][6]

Refactor fifth:
- Add a **Unified decision explainer**:  
  - A small shared lib that all gates call to log: which hook fired, why, and what next step the human/agent should take; surface a concise summary in the Stop message.[1]
- Implement a **frustration / interaction-cost tracker**:  
  - Use `concern_detection`, failure counts, and repeated-block patterns to adjust behavior (fewer nags, more concrete suggestions, or switching to step-by-step mode).[6][1]

Rationale: keeps your dense hook lattice from feeling like a hostile black box and aligns with “hooks as hint layer first, gates second.”[18][2]

## 6. Consolidation and simplification

**Goal:** After adding the new systems, simplify and de-duplicate to keep the mental and performance load manageable.[18][1]

Refactor last:
- Merge overlapping Stop gates (several overconfidence/empirical/behavioral gates) into fewer, more interpretable composites, now backed by plan/requirements/quality scores instead of ad-hoc heuristics.[1]
- Revisit router architecture and env toggles:  
  - Group by *layer* (Plan, Execute, Validate, Close) instead of only by event, so you can selectively disable whole cognitive layers when debugging or doing small tasks.[2]

If you’d like, we can next sketch a concrete “Plan Contract” data model and the three hooks you’d need (contract generator, progress tracker, closure gate) so you can start the rebuild with one small, high-impact subsystem.

## Human

Can we reorder to deal with the behavioral problems first, the ones that are most infuriating?

## Assistant

Yes. Focusing purely on what feels infuriating, I’d reorder the refactor around *behavioral pain* rather than architecture.

## 1. Stop lying / fake “done” (false completion, overconfidence)

Target complaints: “Says it’s done when it’s not”, “claims tests passed that never ran”, “fix isn’t actually applied.”[1][2]

Refactor first:
- Promote a **Plan/Requirements Contract** and wire it *directly* into Stop:  
  - For each major task, generate a minimal contract (requirements + acceptance criteria) and store it.  
  - Add a `Stop_plan_contract_gate.py` that checks: “Are the promised files, tests, and checks actually present and touched this session?” and blocks if not.
- Tighten existing Stop gates to use this contract:  
  - Teach `stop_success_validator.py`, `StopHook_cross_validator.py`, `empirical_claims_gate.py` to consult the contract instead of only ad-hoc heuristics.[3]

Reason: this directly attacks the “lying about done” behavior that’s most rage-inducing.

## 2. Lazy / incomplete work (lazy dev syndrome)

Target complaints: “Does 60–70% then gives up”, “bare-minimum edits,” “writes placeholder tests.”[4][5]

Refactor second:
- Make **TDD and investigation gates bite harder**:  
  - Strengthen `pretooluse_tdd_gate.py` and `PreToolUse_investigation_gate.py` so they *block* when trying to patch without reading or when skipping test phases for code that already has tests.[3]
- Add a **“minimum change” semantic check**:  
  - In PostToolUse, detect trivial diffs that don’t address the described bug/feature (e.g., comment or log-only changes) and require another pass before Stop can succeed.

Reason: you already have the skeleton; this turns “suggestions” into hard rails against lazy closure.

## 3. Ignoring instructions / drifting from what you asked

Target complaints: “I told it three times”, “it ignores CLAUDE.md / rules”, “it wanders off.”[6][7]

Refactor third:
- Build a **Requirements/Instruction Tracker**:  
  - On first UserPromptSubmit, parse your request into a canonical checklist.  
  - After each tool call (PostToolUse), map what happened back to checklist items and mark progress.
- Add a **Stop_instruction_adherence_gate.py**:  
  - If any high-priority instructions are untouched or contradicted (e.g., “don’t touch X” but X was edited), block completion and surface a specific violation message.

Reason: this directly converts “ignoring me” into a concrete, enforceable notion of adherence.

## 4. “AI-smell” / bad or unsafe code

Target complaints: “Clunky code”, “tests that assert nothing”, “security/quality regressions.”[8][9]

Refactor fourth:
- Extend PostToolUse with **semantic quality checks**:  
  - For Python/TS, add language-aware checks for: non-asserting tests, unused branches, very long functions, obvious duplication.  
  - Integrate with existing `PostToolUse_code_verification_gate.py` and `PostToolUse_lint_router.py` so they become “quality gates,” not just syntax/formatting.[3]
- Optional: add simple **security heuristics** (dangerous patterns in Bash / web calls) on top of your existing path/shell gates.[9]

Reason: this addresses “I can’t trust the code it writes” beyond compilation.

## 5. Session degeneration / “it gets worse the longer I use it”

Target complaints: “Works at first then degrades”, “feels brain-dead after a while.”[2][10]

Refactor fifth:
- Use your existing trackers (`session_change_tracker.py`, `failure_recorder.py`, CKS logs) to compute a **session health score**.[3]
- Add a **Session reset governor**:  
  - When health is bad (many reversions, repeated failures, lots of compaction), suggest or require: “Start a fresh session; here’s a summarized context.”

Reason: this reduces long-session frustration and keeps other behavioral fixes effective.

## 6. UX / “why did you block me?” friction

Target complaints: “The system is fighting me”, “I don’t know why it refused.”[11][1]

Refactor last:
- Add a **unified decision explainer** that every gate calls, so you always get a short, concrete explanation and next action when something is blocked.  
- Tune `concern_detection` + a simple frustration metric to reduce nagging when you clearly want to push through.[3]

If you want, we can now pick step 1 and sketch the small Plan/Requirements Contract data structure plus the Stop gate contract check that would give you immediate relief on “fake done.”
