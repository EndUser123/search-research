---
title: "please review the skill in this file, and tell me what we can do to improve it."
date: "2026-03-01"
mode: "COPILOT"
uuid: "4e088a45-ce59-4498-aa78-5fdad0554d06"
entry_count: 14
---

## Human

please review the skill in this file, and tell me what we can do to improve it.

## Assistant

The skill is already very strong; the biggest wins now are reducing friction, tightening invariants, and adding “safety rails” around the known issues and manual steps.[1]

Below are targeted improvements grouped by theme.

## 1. Close the Known-Issues Loop

You already have a solid Known Issues section; turn those into explicit design tasks.[1]

- Add rollback-aware markers  
  - Store the git commit hash (or a content hash) alongside each `code-*-complete.marker` in a small JSON (e.g., `.claude/state/code-phase-state.json`).[1]
  - On hook validation, compare current `HEAD` (or key files’ hashes) to the stored value; if changed, require re-running STATIC ANALYSIS/TRACE and delete or invalidate the marker.

- Enforce the completion guard at the hook level  
  - The completion guard is currently a behavioral expectation; encode it as state: track whether RED, GREEN, REFACTOR, VERIFY evidence exists for each task in the resume ledger, not just in narrative output.[1]
  - Have BUILD write structured evidence entries (per task) and add a guard that refuses SHIP if any task is missing one of the four evidence types.

- Make multi-terminal collisions impossible by default  
  - Persist `--task-list-id` in `.claude/state/build-state.json`, and refuse a second BUILD session unless it either:  
    - uses the same ID, or  
    - passes an explicit `--force-takeover` flag that is logged to the ledger.[1]

## 2. Reduce Manual / “Remember To Do X” Steps

There are several places where you rely on human discipline; push more into enforced protocol.[1]

- Make TRACE truly mandatory for code changes  
  - The docs say TRACE is optional for trivial changes, but your non‑negotiables and ROI story argue TRACE should be default for all code edits.[1]
  - Split the concept:  
    - `/code --phase=3.5 --mode=full` (default for any code delta).  
    - `/code --phase=3.5 --mode=light` only for clearly non-executable changes (e.g., Markdown), and still write a “no-op TRACE” record into the ledger so the SHIP guard is satisfied in a structured way.

- Auto-create and maintain the resume ledger  
  - Right now, resume-ledger updates are described as manual.[1]
  - Add a small helper script invoked by phases to append evidence; never rely on manual editing.  
  - Include: task id, phase (RED/GREEN/REFACTOR/VERIFY), timestamp, files touched, test command, result.

- Automatically normalize paths  
  - You already have `runtime_fingerprint.py` and path translation as manual workarounds.[1]
  - Add a small “path normalization” helper that:  
    - Detects Windows vs WSL vs native,  
    - Rewrites `P:\...` ↔ `/mnt/p/...`,  
    - Is called before running any verifier commands, so the skill always uses normalized paths internally.

## 3. Strengthen Phase & Evidence Modeling

You have excellent conceptual modeling (phases, markers, evidence types), but they are slightly under-specified at the data level.[1]

- Model phases and evidence as first-class data structures  
  - Define a small JSON schema:  
    - `phase_state.json`: current phase, prerequisites satisfied, markers, last commit hash.  
    - `evidence.json`: per-task evidence objects with fields for test commands, coverage numbers, and link to TRACE report.[1]
  - This makes it easier to build future tooling (dashboards, auto-resume, analytics).

- Add intra-phase progress markers  
  - Markers today are coarse-grained (“BUILD complete”).[1]
  - For long-running features, add sub-markers like `code-build-task-N-complete.marker` or just store this in `build-state.json`, so resuming is more precise and the hook can distinguish “BUILD never started” vs “BUILD partially done but incomplete”.

- Make SHIP’s “smart build verification” explicit  
  - Extract the SHIP checks into a clear checklist (tests passing, coverage threshold, no blocking findings) with machine-readable state, not only narrative log.[1]
  - Let SHIP append a final certification record with: commit hash, test summary, coverage, TRACE findings summary.

## 4. Improve UX and Failure Modes

The system is powerful but could feel heavy in daily use. You can keep guarantees while smoothing ergonomics.[1]

- Add a “status / introspect” command  
  - Provide `/code --status` that prints:  
    - Current phase, which markers exist, last TRACE run, unresolved evidence gaps, active task list id.[1]
  - This removes guesswork when you jump back into a feature days later.

- Provide guided recovery flows for common issues  
  - For rollback detection or path problems, instead of saying “manually delete markers” or “run runtime_fingerprint.py”, add a dedicated subcommand:  
    - `/code --repair-markers` to recompute or clear markers safely.  
    - `/code --fix-paths` to run the path normalization routine.[1]

- Make behavioral gate warnings more context-aware  
  - behavior_gates_config.json currently uses simple patterns with known false positives.[1]
  - Add:  
    - an allowlist of contexts where “you should modify” is acceptable (e.g., during planning phases),  
    - a “severity level” so benign matches produce a low-friction note instead of a blocking-style warning.

## 5. Tighten Documentation & Integration Points

Your review bundle is excellent; a few structural tweaks will make it easier for future you (or other agents) to plug into it.[1]

- Extract “non‑negotiables” into a machine- and human-readable contract  
  - Keep the textual list, but also add a small `non_negotiables.json` that enumerates:  
    - enforced order (BUILD → TRACE → SHIP),  
    - evidence requirements,  
    - TRACE mandatory criteria.[1]
  - Hooks and sub-tools can then reference this single source of truth.

- Provide minimal “quick start” and “advanced usage” views  
  - SKILL.md is dense because it encodes the whole methodology.[1]
  - Add a short “quick start” section: 10–15 lines for the common case (`/code "implement X"` with standard thresholds) and one table showing flags (`--phase`, `--task-list-id`, `--status`, etc.).  
  - Keep the detailed flow and case studies as appendices.

- Document extensibility contracts more formally  
  - For each integration point (custom validation rules, TRACE extensions, behavioral gates), specify:  
    - JSON schemas for stdin/stdout,  
    - expected exit codes,  
    - stability guarantees across versions.[1]
  - That will let you evolve v3+ without breaking existing hooks.

If you’d like, next step could be: pick one of these (e.g., rollback-safe markers or `/code --status`) and we can design the concrete JSON schema, hook logic, and test cases for it.

## Human

note that we are optimizing for claude code, so hooks should be skill based according to claude standards.

"Make multi-terminal collisions impossible by default", The standard pattern is to include the terminal/session ID in the filename to create  terminal-scoped state files.  STATE_FILE_PATTERN: Final = "cflo_state_{terminal_id}.json"

Make TRACE truly mandatory for code changes, yes

Auto-create and maintain the resume ledger, yes

Automatically normalize paths, yes, but we are always on Windows.


Actually, why do we want to track state?

## Assistant

State is there to enforce your non‑negotiables across time, terminals, and interruptions.[1]

### Why track any state at all?

You’ve already implicitly decided to track state via markers, build-state.json, build-runs.jsonl, and the resume ledger. The question is not “state vs no state” but “what is the minimum, high‑leverage state worth keeping?”[1]

You want state because:

- Phase gating is temporal by nature  
  - “Cannot TRACE before BUILD” and “Cannot SHIP before TRACE” only make sense if something persists between invocations to prove BUILD/TRACE actually ran.[1]
  - Without a durable trace of those completions, the hook can’t reliably block out‑of‑order phases.

- TDD evidence and TRACE are investments you don’t want to redo blindly  
  - Each TRACE run can be 30–60 minutes, and BUILD can involve multiple RED/GREEN/REFACTOR loops.[1]
  - Minimal state lets you know “this code, at this commit, has already paid that cost,” and when a significant change invalidates that guarantee.

- Multi‑terminal / multi‑session safety is fundamentally about identity over time  
  - “Collisions” are exactly two agents acting as if they own the same task.[1]
  - Terminal/session‑scoped state (e.g., `cflo_state_{terminal_id}.json`) is the standard Claude Code pattern to establish ownership and safely coordinate concurrent work.

- Resumability and observability are impossible without some memory  
  - You already describe “resume ledger” as the thing that enables resume after interruption and multi‑terminal coordination.[1]
  - If you drop that, resuming mid‑feature becomes guesswork; the skill can’t answer “what’s done, what’s missing, what evidence exists?”

So the core rationale: **state is the minimum memory needed to turn a stateless chat into an enforceable workflow with guarantees about order, evidence, and ownership.** Without it, your BUILD→TRACE→SHIP and RED→GREEN→REFACTOR→VERIFY pillars become advisory, not enforced.

### How to keep state minimal and Claude‑friendly

Given the Claude Code optimization and Windows‑only constraint, you can keep this tight:

- Use only skill‑based hooks (PreToolUse) and skill‑local state files, per Claude standards.[1]
- Scope runtime state by terminal/session ID in filenames, e.g. `cflo_state_{terminal_id}.json`, `resume_ledger_{terminal_id}.json`, to avoid collisions by construction.  
- Keep global markers extremely small: just “phase X completed at commit Y” plus maybe a summary.[1]
- Only track what you need to enforce:  
  - Last BUILD/TRACE commit hash,  
  - Whether each task has all four evidence types,  
  - Which terminal/session currently owns the task list.

Everything else (logs, narratives) can remain ephemeral.

If you like, next step could be: define a concrete schema for `cflo_state_{terminal_id}.json` and the auto‑maintained resume ledger so they’re just enough to support mandatory TRACE, TDD evidence, and collision‑free multi‑terminal use.

## Human

please create a solution doc I can take to the other LLM.

## Assistant

I've created a comprehensive solution document (`code-skill-improvements.md`) that you can take to the other LLM for implementation.

## What's in the document:

**1. State Management Rationalization**
- Clear explanation of *why* state is needed (enforcing temporal guarantees)
- Design constraints aligned with Claude Code standards and Windows-only environment

**2. Improved State Schemas**
- `code_phase_state.json` - Global phase tracking with commit-aware rollback detection
- `code_evidence_{terminal_id}.json` - Terminal-scoped TDD evidence ledger
- `code_build_state_{terminal_id}.json` - Terminal-scoped build ownership

**3. Mandatory TRACE Enforcement**
- Full TRACE mode (default for code changes)
- Light TRACE mode (only for non-executable configs/docs)
- No exemptions for "trivial" changes

**4. Path Normalization**
- Windows-only path handling (`P:\...` format)
- Automatic normalization before verification commands
- No WSL/Git Bash translation needed

**5. Auto-Maintained Evidence Ledger**
- `EvidenceManager` class with auto-append methods
- Workflow integration examples
- Completion guard enforcement

**6. Enhanced Phase Order Hook**
- Rollback detection via commit hash comparison
- Clear error messages for phase violations
- Fail-closed enforcement

**7. UX Improvements**
- `/code --status` - Introspection command
- `/code --repair-markers` - Guided recovery from rollbacks
- `/code --fix-paths` - Automatic path normalization

**8. Implementation Checklist**
- 6 phases: State Schema → Utilities → Hook → Workflow → UX → Documentation

**9. Migration Strategy**
- Detect old state format
- Auto-migrate to new format
- Keep backups for 30 days

**10. Success Metrics**
- Issue resolution tracking
- Manual step reduction
- Code quality improvements

The document is implementation-ready with concrete schemas, code examples, and a clear execution path. You can hand this directly to the other LLM and say "implement this solution."

## Human

What can we do to improve outcomes?

## Assistant

Three levers will most improve outcomes: stronger enforcement of invariants, better feedback to you, and tighter fit to how Claude actually behaves.[1]

### 1) Make guarantees hard, not soft

These turn your design intent into enforced behavior.[1]

- Mandatory TRACE for all code changes  
  - Remove “trivial-change” escape hatches; use full vs light TRACE modes but always require a TRACE completion before SHIP.[1]

- Evidence-based DONE, not vibes-based  
  - Enforce the four evidence types (RED/GREEN/REFACTOR/VERIFY) via the ledger and block SHIP if any task is missing one.[1]

- Rollback-aware phase markers  
  - Tie BUILD/STATIC_ANALYSIS/TRACE markers to commit hashes and invalidate them on HEAD change so you never rely on stale verification.[1]

### 2) Reduce cognitive + friction cost

These make it easy for future-you to stay on the rails without thinking about the machinery.[1]

- Auto-maintain everything the skill depends on  
  - Resume ledger, phase state, and terminal-scoped state files should all be written by utilities, never edited by hand.[1]
  - Normalize Windows paths automatically before any verification/TRACE step so you never debug path nonsense again.[1]

- Add fast introspection and recovery  
  - `/code --status` so you always know “where am I, what’s done, what’s missing?” in one shot.[1]
  - `/code --repair-markers` and `--fix-paths` so common failure modes are one-command fixes, not ad-hoc surgery.[1]

### 3) Align tightly with Claude Code’s actual runtime

These increase the chance that the agent does what you intend instead of something “nearby.”[1]

- Skill-based hooks and terminal-scoped state  
  - Use the standard `cflo_state_{terminal_id}.json`-style pattern so multi-terminal behavior is predictable and collisions become structurally impossible.[1]

- Behavior gates tuned to your execution models  
  - Refine `behavior_gates_config.json` so it understands when “you should modify X” is planning guidance vs an implementation promise, reducing false positives while still catching real violations.[1]

If you want something concrete to move the needle fastest, I’d prioritize: (1) rollback-aware markers, (2) auto evidence ledger + SHIP guard, (3) `/code --status`; those three alone will materially improve reliability and debuggability of your runs.

## Human

Do popular repos have any ideas that can improve our outcomes?

## Assistant

Yes—several emerging tools and writeups suggest patterns you can steal to push outcomes even further.[1][2][3][4]

### 1) Encode more of the workflow *in-repo*

Popular setups put AI-facing standards directly in the repo (e.g., `CLAUDE.md` or similar) so every session, branch, and tool sees the same ground rules.[2][3]

- Add a short, repo-level “AI contract” file alongside SKILL.md with:  
  - TDD rules, TRACE requirements, and evidence expectations.  
  - Standard commands for tests, lint, typecheck, TRACE entry points.  
- This matches the pattern where teams codify AI usage rules in a project file that assistants read automatically, reducing variance and “drift” between sessions.[3][2]

### 2) Tighten CI / PR integration around AI work

Several workflows wire AI use into CI and PR templates to keep humans firmly in control of what merges.[5][4][3]

- Add a minimal PR checklist (template) aligned with your phases:  
  - “AI-generated or AI-assisted,” “tests added/updated,” “TRACE report attached/linked,” “risk notes.”[3]
- Run / enforce parts of your `/code` guarantees in CI:  
  - Require tests + static analysis on every PR.[4][3]
  - Optionally run a lightweight AI reviewer focused on diffs, but make it advisory—not authoritative.[6][5]

### 3) Borrow from dedicated AI–TDD tools

AI-TDD CLIs and frameworks lean hard into “you write tests, AI writes code until green,” which is exactly your philosophy.[7][1]

- Make the “spec → tests → implementation → refactor” path the *fastest* path in `/code`, not just the most correct:  
  - Provide short, ready-made prompts/commands for “generate tests only” and “implementation only from failing tests,” similar to AI-TDD tools.[7][3]
- Consider a small “AITDD mode” in `/code` that:  
  - Refuses to write production code until RED exists.  
  - Refuses to refactor until GREEN is stable.

### 4) Embrace spec-first, plan-in-file flows

People getting good results with AI-assisted coding tend to push plans and specs into first-class markdown artifacts in the repo.[8][4]

- Lean harder into `plan.md` / `flows/*.md` as the canonical spec:  
  - Ensure `/code` always updates the plan with current task status, evidence summaries, and risk notes, similar to “plans/<date>-plan-name.md” patterns.[9][8]
- This keeps AI work auditable and makes it trivial to reconstruct context across terminals and days.

### 5) Add a “delta-focused” review / TRACE mode

Popular AI code review flows focus strictly on diffs (PR changeset) rather than whole files, which tends to reduce noise and missed issues.[10][6][5]

- Add a “TRACE-on-diff” mode:  
  - Use git diff to narrow TRACE to only changed functions/regions.  
  - Still require full TRACE for high-risk patterns (I/O, locks, concurrency), but allow diff-focused TRACE for low-risk areas to reduce time cost.  
- Similarly, let `/code` drive an “AI review this diff only” step that produces a short, structured finding list you can feed into TRACE.

### 6) Instrument and measure

Teams reporting strong results treat AI workflows as systems they instrument, not just habits.[2][4][3]

- Start capturing simple metrics per run in your existing `build-runs.jsonl`:  
  - Phase durations, number of TRACE findings by severity, number of times TRACE caught bugs tests missed.[11][2]
- Use those metrics to tune: when TRACE is overkill, where tests are weak, and which parts of `/code` cause most friction.

If you’d like, I can propose a small “v3.0 outcome ramp”: a 3–5 item changeset that specifically pulls in (a) diff-focused TRACE, (b) repo-level AI contract, and (c) CI/PR hooks, so you can trial them on one feature and see if defect rate and friction actually drop.

## Human

Best prompts for Claude Code TDD workflow
Try AI-TDD CLI in our project

## Assistant

Here’s a concise setup you can drop into Claude Code plus a way to experiment with AI-TDD in your repo.[1][2][3]

## 1. Core Claude Code TDD prompts

### 1.1 RED: tests only

Use as a command/skill description or direct prompt:

> You are a strict TDD assistant.  
> Current task: **[short task name]**.  
> Context: **[link/quote spec, plan.md section, relevant files]**.  
>   
> Your job in this step is **tests only (RED)**.  
> - Propose a concise test plan (bullet list) that covers happy path, edge cases, and error paths.  
> - Then write test code files only (no production code, no stubs beyond what the test framework requires).  
> - Use the existing test framework and patterns in this repo.  
> - Mark each test with a short comment explaining the behavior it guards.  
>   
> Do **not** write or change any non-test code.  
> Stop after the tests and show how to run them (exact command).

This matches the “test-first prompting” pattern where you explicitly lock the model into generating tests only.[4][3]

### 1.2 GREEN: make tests pass, minimally

> Continue TDD for **[short task name]**.  
> The tests for this task are now **failing**; your job is the **GREEN** step.  
>   
> Constraints:  
> - Only modify the minimum code needed to make the existing tests pass.  
> - Prefer the simplest naive implementation that satisfies the tests.  
> - Do not add new tests in this step.  
> - Preserve existing behavior outside the tested surface.  
>   
> Output:  
> - Updated implementation files.  
> - A brief note per file explaining what changed and why.  
> - The exact command to re-run the tests.

### 1.3 REFACTOR: clean up with tests green

> We are now in the **REFACTOR** step for **[short task name]**.  
> All tests are currently passing.  
>   
> Goals:  
> - Improve readability, structure, and duplication without changing observable behavior.  
> - Keep tests passing at all times.  
> - Apply local improvements only (no architecture-wide rewrites).  
>   
> For each change:  
> - Explain the intent quickly.  
> - Show the diff or updated code.  
> - Reaffirm which tests should be re-run.

### 1.4 VERIFY: independent check against spec

> Final **VERIFY** step for **[short task name]**.  
> Inputs: the original spec, the test code, and the implementation.  
>   
> Tasks:  
> - Cross-check implementation against spec and test cases; list any missing cases.  
> - Identify risk areas (resource handling, error paths, concurrency, security) and propose additional tests if needed.  
> - If you propose more tests, write them but **do not** change production code in this step.  
>   
> Output a short verification report:  
> - “Covers:” (bullets)  
> - “Missing or under-tested:” (bullets)  
> - “Next tests to add:” (if any).

You can encode these as `.claude/commands` or skill phases (`/red`, `/green`, `/refactor`, `/verify`) similar to the AAID-style workflows.[2][3]

## 2. Trying AI-TDD CLI in your project

AI-TDD gives you a dedicated “you write the test, AI writes the code” loop. You can pilot it on a submodule and keep `/code` as the orchestrator.[5][1]

### 2.1 Basic setup

In a Python/TypeScript project:

1. Install AI-TDD globally or in a venv:
   - `pip install aitdd` (if published) or `pipx install` / clone + `pip install -e .` from the repo.[1]
2. Configure it to use your preferred model/provider (you’ll likely need to adapt its OpenAI wiring to your Claude endpoint or run it only for “proof of concept”).

### 2.2 Minimal workflow in your repo

For one feature directory (e.g., `src/auth`):

1. Write or extend a failing test:
   - `tests/test_auth_login.py` or equivalent.
2. Run AI-TDD in that scope:
   - `aitdd run` from the project root or configured path.[1]
3. Let AI-TDD generate implementation changes until tests pass.
4. Feed the diff and resulting code back through your `/code` TRACE + VERIFY phases.

Conceptually:

- `/code` still owns: planning, execution model, TRACE, SHIP.  
- AI-TDD is an inner loop tool you call during BUILD to automate GREEN for specific tests.

### 2.3 Integration points with `/code`

You can add a narrow prompt/command in SKILL.md:

- For RED:
  - Use Claude Code with the RED prompt above to generate tests inside your repo.
- For GREEN:
  - Option A: Use Claude Code with the GREEN prompt.  
  - Option B: If you want to experiment, invoke AI-TDD on the changed test file(s) and then return to `/code` for REFACTOR + VERIFY.

This gives you a clean experiment: compare outcomes and time-to-green between Claude-only GREEN and AI-TDD GREEN on one or two tasks, without changing your overall `/code` architecture.

## Human

what about ways to improve the trace or analysis to make sure we have written good code?

## Assistant

You’ll get the biggest lift by making TRACE more evidence-driven, more risk-focused, and more structured around known failure modes.[1][2][3]

## 1) Make TRACE “evidence-first”, not commentary-first

Instead of “walk the code and see what you notice,” package concrete signals and require specific outputs.[3][1]

- Always feed TRACE with an evidence bundle:  
  - Relevant tests and their names (especially ones that exercise the traced code).  
  - Recent failures (stack traces, logs, fuzzing outputs if any).  
  - Risk tier for this change (e.g., touches I/O, money flow, auth, locks).[4][1][3]

- Require a structured TRACE report:  
  - Table of scenarios (happy path, each error path, concurrency scenarios), listing: inputs, preconditions, expected outcomes, actual code path taken, resource state at exit.[2][3]
  - Explicit “evidence links”: which tests cover which scenario, and which scenarios currently have no tests.

This shifts TRACE from “general reasoning about code” to “explain how each important scenario behaves and what proves it,” which matches evidence-first review patterns.[1][2]

## 2) Hard-code checklists for specific risk classes

Your TRACE_CHECKLIST already has categories; tighten it with domain-specific micro-checklists and require filling them.[5][6][3]

Examples:

- For resource management / I/O:  
  - For each opened resource (file handle, DB connection, lock), list all possible exit paths and confirm where it is closed/released, or flagged as a bug.  
  - Check for “hidden” allocations (temp files, large in-memory buffers) and verify bounded lifetime.[5][2][3]

- For locking / concurrency:  
  - Require an explicit table of lock acquisition order across functions to detect potential deadlocks.  
  - For each lock: identify contention risks, timeouts, and behavior under failure (what if the lock can’t be acquired?).[6][7][3]

- For security-sensitive paths (auth, payments):  
  - Require checks for auth/authorization at every entry point, input validation, and output encoding/sanitization.[4][2][5]

You can bake these into TRACE templates so each high-risk change type has its own mini-protocol rather than one generic checklist.[3][5]

## 3) Diff-focused TRACE + anti-pattern sweeps

Borrow from modern AI code-review practice: focus TRACE on deltas and known anti-patterns.[8][9][10]

- TRACE on the diff first:  
  - Use `git diff` to constrain TRACE to changed functions/blocks; require a “diff coverage” section: what changed, old behavior vs new behavior, and why it’s safer/better.[10][11]

- Add an anti-pattern checklist:  
  - For TDD: tests that assert too many things, brittle sequencing, hidden dependencies, overly broad mocks.[12][8]
  - For general code: enumerator/sequencer patterns, catch-all exceptions, feature flags with dead branches, etc.[8][10]

Have TRACE explicitly mark “found/not found” for a short anti-pattern list so you can systematically eliminate classes of issues over time.[10][8]

## 4) Strengthen alignment with intent and spec

A lot of AI-generated bugs are “spec drift”: code is clean but not what was asked.[2][4]

- Always include original intent:  
  - Attach the relevant `plan.md` section or user story to TRACE and require an “intent match” section:  
    - What the spec promised.  
    - How each function/endpoint implements it.  
    - Any discrepancies or ambiguities.[4][3]

- Track important prompts / instructions as inputs:  
  - For high-risk changes, include the key Claude prompts that produced the code and have TRACE verify that the implementation still matches the original intent (no extra side effects, no dropped constraints).[1][4]

This addresses the “confidently incomplete” pattern where the code looks fine but silently omits business rules.[2][4]

## 5) Close the loop with tests and CI

Finally, treat TRACE as something that should spawn tests and be checked later, not just a moment-in-time review.[13][5][3]

- Require TRACE to propose at least one additional test per non-trivial change, then either:  
  - Add it, or  
  - Explicitly log why it’s not worth adding (so future you can revisit).[13][12][5]

- Tie TRACE to CI:  
  - For high-risk areas, add a CI job that fails if new code in those directories landed without a corresponding TRACE report marker or without new/updated tests.[14][12][3]

Together, these tweaks turn TRACE into a structured, evidence-backed, risk-aware review step that systematically finds the kinds of bugs AI code is prone to, instead of being a generic pass over the code.

## Human

Example prompts from ai-code-review-prompts repo for Claude
How to implement evidence packs in TDD traces
Common TDD anti-patterns to catch in analysis
Best ways to verify AI code matches prompt intent
Tools for automating trace verification in Claude workflows

## Assistant

Here are concrete patterns you can lift directly into your `/code` + TRACE workflow.

***

## 1) Example Claude-style review prompts (from ai-code-review-prompts–style repos)

Repos like `ai-code-review-prompts` and `awesome-reviewers` use long, structured prompts that you can adapt for Claude Code.[1][2]

### General “deep review” prompt skeleton

> You are a **senior {LANGUAGE}/{FRAMEWORK} engineer and TDD practitioner**.  
> Review the following code and tests as if you were doing a **blocking code review** on a high-risk change.  
>  
> **Context**  
> - Project: {brief description}  
> - Change type: {bugfix/feature/refactor}  
> - Risk areas: {e.g., auth, money movement, locking, external I/O}  
>  
> **Your tasks**  
> 1. **Correctness & spec alignment**  
>    - Does the code clearly implement the described behavior?  
>    - Identify any missing edge cases or error paths.  
> 2. **TDD quality**  
>    - Are the tests sufficient, focused, and deterministic?  
>    - Point out any TDD anti-patterns (liars, excessive setup, giants, slow pokes, etc.).  
> 3. **Security & robustness** (if applicable)  
>    - Highlight potential vulnerabilities or unsafe patterns.  
> 4. **Performance & maintainability**  
>    - Note obvious performance issues and design smells.  
>  
> **Output format (markdown)**  
> - `Summary` (2–3 bullets, include overall risk level)  
> - `Issues` (table: severity, location, description, suggestion)  
> - `TDD findings` (table: test name, smell/anti-pattern, fix)  
> - `Suggested follow-up tests` (list)

You can specialize by language or framework, similar to `java/spring-boot-comprehensive.md` in that repo.[2]

***

## 2) Evidence packs in TDD traces

Borrowing from “evidence-first” review ideas: make TRACE consume and produce explicit evidence bundles.[3][4]

### Structure of an evidence pack

For each unit of work (task/function/module), define an evidence pack:

- **Inputs**  
  - Spec snippet / user story ID  
  - Changed files & git diff for this change  
  - List of tests that exercise this code (names + paths)  
  - Test results (pass/fail, coverage if available)

- **TRACE artifacts**  
  - Scenario table (happy path and key error/concurrency scenarios)  
  - Variable/resource state snapshots at key lines  
  - Explicit mapping: scenario → test(s) that cover it (or mark “no test”)  

- **Findings**  
  - Defects (with severity)  
  - Gaps in tests  
  - Follow-up tasks/tests

Implementation-wise, your TRACE phase prompt becomes:

> For the following code change, you are a **TRACE reviewer**.  
> You are given an *evidence pack*:  
> - Spec excerpt: …  
> - Diff: …  
> - Tests: …  
> - Test results: …  
>  
> 1. Build a **scenario table** (columns: scenario name, inputs, expected outcome, actual code path, resources on exit, tests covering it).  
> 2. Identify any scenarios that have **no test coverage**.  
> 3. Flag any resource leaks, error-handling gaps, or concurrency hazards.  
> 4. Propose at least one additional test if you find any gap.

Over time you can persist these evidence packs alongside `build-runs.jsonl` so they become part of the audit trail.[4][3]

***

## 3) TDD anti-patterns to check in analysis

Summarizing from common lists (Carr, Codurance, Marabesi, quii):[5][6][7][8]

Have TRACE (or a dedicated “TDD review” step) explicitly check for:

- **The Liar**  
  - Tests that pass even when the code is clearly wrong (over-mocked, asserting the wrong thing, assertions that don’t touch the behavior under review).[7][5]

- **Excessive Setup / Giant**  
  - Tests with huge setup blocks, many collaborators, or “god” fixtures—these hide the behavior under a lot of noise and signal poor design.[6][5]

- **Slow Poke**  
  - Tests that are slow due to hitting real networks, disk, or heavy DB operations; they make the suite too slow to run in tight TDD loops.[5][7]

- **Hidden Dependency / Mockery**  
  - Tests that only verify mocks/stubs interactions instead of real behavior, leading to false confidence when interfaces change.[8][7][5]

Prompt addition:

> As part of this review, explicitly check for common TDD anti-patterns: the Liar, Excessive Setup, the Giant, Slow Poke, Hidden Dependency, Mockery.  
> For each test file, output a table: `test / anti-pattern / why / suggested refactor`.

***

## 4) Verifying AI code matches prompt intent

This is about making “intent vs implementation” an explicit diff.[9][10][11]

Add a dedicated “intent alignment” step:

> You are an **intent alignment reviewer**.  
>  
> **Inputs**:  
> - Original AI prompt or user story (what was requested).  
> - Any constraints (e.g., must be idempotent, must not log PII, must handle cancellations).  
> - The generated code and tests.  
>  
> **Tasks**:  
> 1. Extract a bullet list of explicit requirements and constraints from the prompt/spec.  
> 2. For each requirement, state whether the code **fully implements**, **partially implements**, or **does not implement** it, citing specific functions/lines.  
> 3. Identify any **implicit side effects** or behaviors that were *not* requested but appear in the code.  
> 4. Suggest additional tests to confirm the most critical requirements and guard against unwanted behaviors.

This catches “looks good but doesn’t do what I asked” failures and implicitly drives better test coverage.[11][9]

***

## 5) Tools / patterns to automate trace verification in Claude workflows

Within Claude Code, you don’t have external tools, but you can simulate “automation” via:

- **Skill-based hooks**  
  - PreToolUse hooks that block `/code --phase=4` unless an evidence pack and TRACE report exist for the current commit.[4]

- **Standardized prompts as files**  
  - Store your review/TRACE prompts as `.prompt` or `.md` files (like `ai-code-review-prompts` and `prompt-file-examples` do) and have SKILL.md reference them by name or snippet.[12][2]

- **Checklists encoded as JSON**  
  - Put your TDD anti-patterns and risk-specific checklists into a small JSON (e.g., `trace_checklists.json`), then have your prompts say “walk this checklist and mark each item yes/no with justification,” which increases consistency across sessions.[13][2][4]

Outside Claude Code, other tools that illustrate useful patterns (even if you don’t adopt them directly):

- **Prompt libraries** like `awesome-reviewers` and `ai-code-review-prompts` for specialized reviewers (security, performance, framework-specific).[1][2]
- **Prompt-file runners** (like Continue’s `.prompt` files and similar) that treat prompts as code, enabling reuse and versioning of review flows.[14][12]

If you want, next step could be: I can draft a concrete `TRACE_REVIEW.prompt.md` file tailored to your `/code` skill that bakes in evidence packs, TDD anti-pattern checks, and intent-alignment in one reusable template.

## Human

yes please

## Assistant

Here’s a reusable template you can drop into your repo as `TRACE_REVIEW.prompt.md` and point Claude Code at.

***

## TRACE_REVIEW.prompt.md

> You are a **senior engineer and TDD practitioner** performing a **TRACE review** of AI-assisted code changes.  
> Your goal is to **confirm correctness, safety, and intent alignment**, not to rewrite everything.  
>  
> Work in **small, verifiable steps**, and follow this structure strictly.

***

### 1. Inputs (filled in by caller)

- **Change summary**:  
  - {1–3 bullet summary of what changed and why}
- **Spec / intent**:  
  - {paste relevant `plan.md` section, user story, or prompt}
- **Diff / code**:  
  - {paste git diff or full functions/modules that changed}
- **Tests & results**:  
  - {list of test files and commands, plus last run result}
- **Risk profile** (check all that apply):  
  - [ ] File / network I/O  
  - [ ] Locks / concurrency / async  
  - [ ] Auth / permissions / security-sensitive  
  - [ ] External services / APIs  
  - [ ] Performance-critical path  

***

### 2. Scenario TRACE table

> Build a **scenario-level TRACE** for the changed behavior.

Produce a markdown table:

| Scenario | Inputs / Preconditions | Expected Behavior (from spec) | Actual Code Path (functions/branches) | Resource State on Exit (files/locks/conns) | Tests Covering It |
|---------|------------------------|--------------------------------|----------------------------------------|--------------------------------------------|-------------------|

- Include at least:
  - 1–2 **happy paths**  
  - All important **error paths** (exceptions, invalid input, timeouts)  
  - Any relevant **concurrency scenarios** (if risk profile includes locks/async)  
- In “Tests Covering It”, list specific test names or mark `NONE`.

***

### 3. TDD & test quality check

> Evaluate how well tests guard the traced scenarios and look for TDD anti-patterns.

3.1 **Coverage by scenario**

- For each scenario in the table, state whether coverage is:
  - `Well Covered`, `Partially Covered`, or `Not Covered`.  
- Note any **behavior that is only asserted indirectly** (e.g., via mocks).

3.2 **TDD anti-patterns**

Use this table:

| Test (file::name) | Anti-pattern | Why It’s a Problem | Suggested Fix |
|-------------------|-------------|--------------------|---------------|

Check explicitly for:

- **The Liar** – tests that pass even if core behavior is wrong.  
- **Excessive Setup / Giant** – huge fixtures / many collaborators.  
- **Slow Poke** – slow tests hitting real external systems.  
- **Hidden Dependency / Mockery** – tests that only verify mocks, not behavior.

***

### 4. Risk-focused checks

> Run targeted checks based on the risk profile.

4.1 **Resource management / I/O** (if applicable)

Answer briefly:

- For each opened resource (file handle, DB connection, lock):  
  - Where is it acquired?  
  - List all exit paths; where is it released in each?  
  - Any paths where it is **not** released or may double-release?

4.2 **Concurrency / locking** (if applicable)

- List any locks / synchronization primitives used.  
- Describe lock acquisition order across functions.  
- Identify risks of:
  - Deadlocks  
  - Lost wakeups / missed notifications  
  - Contended locks or unbounded waits

4.3 **Security / auth** (if applicable)

- Where are **authentication** and **authorization** checks performed?  
- Are inputs validated and outputs sanitized?  
- Any secrets or sensitive data logged or exposed?

***

### 5. Intent alignment

> Ensure the code actually does what the spec / prompt intended.

5.1 **Requirement mapping**

Create a table:

| Requirement (from spec/prompt) | Implementation Location(s) | Status (Full / Partial / Missing) | Notes |
|--------------------------------|----------------------------|------------------------------------|-------|

- Extract explicit requirements and constraints from the spec/prompt.  
- For each, map to functions/lines or mark as `Missing` or `Unclear`.

5.2 **Unrequested behaviors**

- List any behaviors or side effects **not requested** in the spec/prompt (e.g., extra logging, caching, retries, additional data writes).  
- For each, state whether it seems **safe**, **risky**, or **undesired**.

***

### 6. Findings & recommended actions

> Summarize what you found and what to do next.

6.1 **Findings table**

| Severity (P0–P3) | Area (Scenario/Test/Risk/Intent) | Description | Recommended Change |
|------------------|-----------------------------------|-------------|--------------------|

- P0 = must fix before shipping  
- P1 = should fix soon  
- P2 = nice-to-have  
- P3 = nit

6.2 **Follow-up tests to add**

List concrete tests you recommend adding, with file and test-name suggestions:

- `tests/...::test_...` – what scenario it covers and why it matters.

***

### 7. Final judgment

End with a short section:

- **Go / No-Go** for shipping this change as-is.  
- If **Go**, note any P1/P2 issues and why they’re acceptable for now.  
- If **No-Go**, list the top 3 blocking issues.

***

You can wire this into `/code`’s TRACE phase by:

- Having the skill collect the inputs (spec excerpt, diff, tests, risk flags).  
- Dropping them into this template as context for Claude Code.  
- Storing the resulting TRACE report next to your existing TRACE artifacts.

## Human

what about sequential thinking or chain of though versions or mental models, so they have a place in our code skill, in any way?

## Assistant

Yes—sequential thinking is already implicit in your phases; you can make it explicit by baking a few lightweight “thinking scripts” into SKILL.md.[1]

### 1) RED/Green/Refactor as explicit mental scripts

Add short “thinking macros” for each TDD step so Claude walks the same internal sequence every time.[1]

- RED script:  
  1) Restate the requirement in one sentence.  
  2) List behaviors and edge cases.  
  3) Map each behavior → one test name.  
  4) Only then write the tests, one behavior at a time.

- GREEN script:  
  1) Identify which behavior/test you’re making pass.  
  2) Sketch the simplest data flow for that behavior.  
  3) Implement just enough code for that behavior.  
  4) Re-check other tests for unintended breakage.

- REFACTOR script:  
  1) List pain points in the current code (duplication, naming, nesting).  
  2) Propose refactor steps in order.  
  3) Apply one refactor at a time and re-run tests conceptually after each.

Document these as small, numbered checklists in SKILL.md under the BUILD phase so Claude’s “chain of thought” is constrained and repeatable without requiring verbose reasoning.[1]

### 2) TRACE mental model: scenario-first, path-second

For TRACE, define a mental model like:

1) List scenarios (happy path, each error path, each concurrency scenario).  
2) For each scenario: follow the code line by line, track key variables/resources.  
3) For each step: ask “what can go wrong here?” and “who cleans this up?”  
4) Only then summarize findings.

You’ve already got templates; adding this 3–4 step “how to think” block at the top of TRACE_TEMPLATES.md tells Claude *how* to walk the code, not just *what* to output.[1]

### 3) Planning and ALIGN: intent and risk models

For ALIGN/DESIGN, introduce simple mental models instead of generic “brainstorm”:

- Intent model:  
  1) State the user’s goal.  
  2) State what must be true when we’re done.  
  3) State what must never happen (invariants, “no-regrets” list).  

- Risk model:  
  1) Enumerate risk categories (data loss, security, concurrency, performance).  
  2) Mark which ones are in play for this feature.  
  3) Note 1–2 mitigation ideas per active category.

These can be small bullets in Phase 1–2 sections and become the “chain of thought” Claude follows before touching code.[1]

### 4) Skill-level guidance on “thinking, then acting”

Finally, at the top of SKILL.md, add a short global rule for Claude:

- Always:  
  1) Restate the current phase and goal in one sentence.  
  2) List 3–5 steps you’ll follow.  
  3) Execute them in order, checking back to the list before moving on.

That gives you sequential thinking baked into the workflow without flooding outputs, and it fits naturally into your existing 7-phase / TDD / TRACE structure.[1]

## Human

Does this help improve the skill?  Does it include the points and ideas you made above?
"Key Improvements to the Claude Coding Skill
Enhance TDD Enforcement: Make RED-GREEN-REFACTOR-VERIFY strictly mandatory with AI-assisted test generation first, reducing hallucinations and ensuring verifiable code; this aligns with evidence showing AI-TDD workflows achieve 75% merge-ready code but require human-led tests for the final polish.
Advanced State Management: Add terminal-scoped JSON for dynamic ownership and auto-invalidation on code changes, preventing collisions and stale verifications; best practices emphasize version control and clear governance to maintain trust in AI outputs.
Improved TRACE and Review: Introduce diff-focused, evidence-packed prompts for TRACE, incorporating anti-pattern checks and intent alignment; this can catch 17% more comprehension gaps in AI-generated code compared to manual coding.
UX and Automation Boosts: Expand commands like --status with metrics dashboards and add subagent skills for specialized tasks (e.g., bug debugging), saving hours on context switching.
Integration with Modern Tools: Embed MCP for external APIs only when needed, and use skills for reusable workflows like PR reviews, potentially speeding development by 2x while maintaining quality.
These changes build on the existing solution document by incorporating real-world AI-TDD patterns, reducing friction further, and adding measurable safeguards. Research suggests such structured AI workflows can improve code quality by 20-30% while halving debugging time, though they require ongoing human oversight to avoid over-reliance.
Updated Phase Structure
Refine phases to include AI-specific prompts and sub-skills:
BUILD: AI generates code only after human-approved tests (RED phase).
TRACE: Mandatory diff-based review with structured output tables.
SHIP: Auto-generates PR with embedded review checklist.
New Features Overview
Subagent Skills: Delegate to specialized agents for reviews or path fixes.
Metrics Tracking: Log phase durations and finding severities in build-runs.jsonl.
Prompt Templates: Embed best-practice prompts to ensure consistency.

Comprehensive Upgrade to the Claude Coding Skill
This detailed survey expands on the provided documents by integrating insights from AI-TDD workflows, prompt engineering, state best practices, and Claude-specific skill examples. The goal is to evolve the "/code" skill into a more robust, agentic system that minimizes errors, enforces quality, and scales for complex projects. We'll mimic professional articles by covering rationale, updated designs, implementation details, and validation strategies.
Rationale for Further Improvements
The original skill excels in phased TDD but faces challenges like inconsistent AI outputs, manual oversights, and limited adaptability. From analyzed sources, AI-assisted TDD shines when humans write tests first (achieving up to 75% merge-ready code), but AI often skips RED phases without explicit constraints. State management in AI tools should prioritize "human-in-the-loop" governance to avoid blind trust, with versioned files preventing collisions. Claude skills enable modular workflows, reducing prompt repetition and token waste. Tracing benefits from structured, evidence-first prompts that flag anti-patterns, closing gaps where AI code scores 17% lower in comprehension quizzes. Overall, these upgrades aim for 20-30% better code quality, as seen in hybrid AI-human workflows, while addressing Windows-specific quirks.
Enhanced State Management
Building on the solution document's schemas, incorporate best practices like aggressive version control and automated backups. Add metrics for analytics, enabling data-driven tuning (e.g., if TRACE often finds P0 issues, flag weak GREEN phases).
Updated code_phase_state.json Schema (Global, with Metrics):
JSON
{
  "version": "2.0",
  "last_updated": "2026-03-01T14:20:00-07:00",
  "phases": {
    "BUILD": {
      "completed": true,
      "completed_at": "2026-03-01T12:00:00-07:00",
      "commit_hash": "a1b2c3d4",
      "terminal_id": "term_abc123",
      "metrics": {
        "duration_minutes": 45,
        "tasks_completed": 3,
        "test_coverage": 85
      }
    },
    // ... similar for other phases
  },
  "current_phase": "TRACE",
  "overall_metrics": {
    "total_findings": {"P0": 0, "P1": 2},
    "ai_hallucinations_detected": 1
  }
}
New Logic: Auto-invalidate on diff detection (use git diff in hooks). Backup old states via code_phase_state.json.bak on changes.
Best Practice Integration: Emphasize "fail-closed" with human prompts for overrides, aligning with governance policies that require logging AI decisions.
Terminal-Scoped Evidence Ledger (code_evidence_{terminal_id}.json):
Add anti-pattern flags and subagent logs for traceability.
JSON
{
  // ... existing fields
  "tasks": {
    "task_1": {
      // ... existing evidence
      "anti_patterns": ["Liar Test", "Slow Poke"],
      "subagent_logs": ["reviewer_agent: Fixed race condition"]
    }
  }
}
Auto-Maintenance: Use EvidenceManager to append metrics post-phase, e.g., record_metrics(duration, coverage).
Mandatory TRACE with Diff-Focus and Prompts
Make TRACE fully evidence-driven, borrowing from "evidence-first" reviews. Always use full mode for code; light for docs. Integrate diff-focus to reduce noise, as popular AI reviews emphasize changeset analysis.
TRACE Modes Table:
ModeTriggerRequirementsOutput
Full
Any code file change
Scenario table, anti-pattern check, intent map
Structured MD report with findings table
Light
Docs/config only
Syntax check, no secrets
Minimal record: "No executable changes"
Best Prompt for TRACE (Embed in TRACE_REVIEW.prompt.md):
You are a senior TDD practitioner performing a TRACE review. Inputs: [spec], [diff], [tests/results], [risks].
Build scenario table: Scenario | Inputs | Expected | Code Path | Resources | Tests Covering.
Check TDD anti-patterns: Table with Test | Pattern (Liar/Giant/Slow) | Fix.
Risk checks: Resources (leaks), Concurrency (deadlocks), Security (auth).
Intent alignment: Requirement | Location | Status (Full/Partial/Missing).
Findings: Severity | Description | Fix. Propose 1+ new tests. Final: Go/No-Go with top issues.
This prompt reduces false positives by 15-20% in reviews, per code review best practices.
BUILD Phase: Strict AI-TDD Integration
Enforce human-led RED: User writes/approves tests; AI implements GREEN minimally. Add REFACTOR with cleanup checklist.
Prompt for RED (Tests Only):
Strict TDD: Task [name]. Context [spec/files]. Propose test plan (bullets: happy/edge/error). Write tests only (no code). Use repo framework. Comment each test. Command to run.
GREEN Prompt:
GREEN for [task]. Tests failing. Modify minimal code to pass. Simple implementation. No new tests. Output: Files changed, notes, re-run command.
This hybrid yields 2x faster iterations with fewer bugs.
UX Enhancements and Subagents
Add /code --metrics for dashboards:
text
📈 Metrics Dashboard
- Avg Phase Duration: BUILD 45min, TRACE 30min
- Findings Trend: P1 down 20% over 5 runs
Integrate Claude subagents as skills:
Reviewer Subagent: For PR checks, using prompt: "Review diff for bugs/security/performance. Table: Severity | Issue | Fix."
Debugger Subagent: "Analyze stack trace: Hypotheses ranked, fixes."
Subagent Schema Table:
SubagentPurposeTriggerTools Needed
Reviewer
Code/PR review
Post-BUILD
Git diff, MCP for external scans
PathFixer
Normalize paths
--fix-paths
Local scripts
MetricLogger
Track runs
Post-phase
JSON append
Implementation Roadmap
Schema Updates: Migrate to v2.0 with metrics (use migration strategy from doc).
Prompt Integration: Store as MD files in .claude/prompts; load dynamically.
Hook Expansions: Add subagent calls in validate_code_phase_order.py.
Testing: Simulate rollbacks, multi-terminals; measure pre/post quality (e.g., bug rate).
Validation: Run A/B tests: Old vs new skill on sample features, tracking time-to-ship and findings.
This upgraded skill turns "/code" into an agentic powerhouse, blending TDD discipline with AI speed while safeguarding quality.
Key Citations:
[AI Native Compass: Workflow with TDD and AI Agents](https://ainativecompass.substack.com/p/workflow-with-tdd-and-ai-agents)
[Codemanship: Why TDD Works Well in AI-Assisted Programming](https://codemanship.wordpress.com/2026/01/09/why-does-test-driven-development-work-so-well-in-ai-assisted-programming)
[Medium: 7 AI Prompts for Code Review and Security Audits](https://medium.com/data-science-collective/youre-using-ai-to-write-code-you-re-not-using-it-to-review-code-728e5ec2576e)
[QuantumByte: Claude Code Prompts Best Templates](https://quantumbyte.ai/articles/claude-code-prompts)
[Google Cloud: Five Best Practices for AI Coding Assistants](https://cloud.google.com/blog/topics/developers-practitioners/five-best-practices-for-using-ai-coding-assistants)
[Anthropic: How AI Assistance Impacts Coding Skills](https://www.anthropic.com/research/AI-assistance-coding-skills)
[Towards Data Science: Claude Skills and Subagents](https://towardsdatascience.com/claude-skills-and-subagents-escaping-the-prompt-engineering-hamster-wheel)"

## Assistant

It helps, but I’d tighten it: some claims are too hand-wavy, and a few key ideas from your design aren’t clearly wired into behavior.

### Does it improve the skill?

Yes, at a high level it reinforces several good directions:

- Stronger TDD enforcement and AI‑TDD integration, aligned with your RED→GREEN→REFACTOR→VERIFY pillars.[1]
- Advanced, terminal‑scoped state to avoid collisions and stale markers, which maps to your state/marker design and multi‑terminal constraints.[1]
- Diff‑focused, evidence‑driven TRACE with anti‑pattern checks and intent alignment, which fits your TRACE templates + checklist concept.[1]
- UX additions like `--status` and metrics in `build-runs.jsonl`, consistent with your existing analytics file.[1]

So conceptually, yes: it pushes in the same direction as the solution doc and can help drive better outcomes.

### Does it include the earlier points?

It covers some, but not all, and some are only mentioned vaguely:

- Included reasonably well:  
  - Mandatory TRACE (it implies “TRACE: diff-based, mandatory” in updated phases).  
  - Evidence packs / structured TRACE (scenario tables, anti‑patterns, intent mapping).  
  - Metrics logging and dashboards.  

- Only lightly covered or missing:  
  - **Rollback-aware markers**: your doc called for commit‑hash‑bound phase validity and auto‑invalidation; here it just says “auto‑invalidate on diff detection” without specifying the BUILD→TRACE→SHIP guard behavior.[1]
  - **Completion guard**: four evidence types per task as a hard SHIP gate is not explicitly described (it just mentions TDD in general).[1]
  - **Terminal‑scoped ownership rules**: it mentions terminal‑scoped JSON, but not the concrete ownership semantics (e.g., “one terminal per task_list_id unless force-takeover”).[1]
  - **Windows path normalization**: not mentioned, even though path translation errors are a known issue in your environment.[1]
  - **Concrete hooks and commands**: `--repair-markers`, `--fix-paths`, and the precise `/code --status` behavior are not referenced, even though they were key to lowering friction.[1]

Also, many numeric claims (75% merge‑ready, 17% more comprehension gaps, 20–30% better code quality, 2x speed, 15–20% fewer false positives) are unattributed and not clearly grounded in the materials you’re actually using.[2][3]

### How I’d tighten it

If you want to keep this text as a “preface” or design overview, I’d tweak it:

- Make a short “Non‑negotiable mechanisms” bullet list:  
  - Rollback‑aware phase markers tied to git commit; BUILD/TRACE invalidated on HEAD change.[1]
  - Completion guard: SHIP refuses if any task lacks RED/GREEN/REFACTOR/VERIFY evidence in the ledger.[1]
  - Terminal‑scoped state: `cflo_state_{terminal_id}.json` with explicit ownership over `task_list_id` to prevent multi‑terminal collisions.[1]
  - Windows path normalization: all state and commands normalized to Windows paths to avoid verifier failures.[1]

- Tone down or drop specific percentages unless you have a specific study or internal metric to point at; keep them qualitative (“reduces false positives”, “improves code quality”) rather than quantified.

- Explicitly reference how MCP/subagents are optional add‑ons, not on the critical path, so they don’t distract from the core BUILD→TRACE→SHIP and TDD enforcement mechanics.[1]

If you’d like, I can rewrite that whole introduction so it’s shorter, more precise, and directly aligned with your actual solution doc (including the crucial guardrails and Windows/Claude‑Code specifics), so you can paste it in without the hand‑wavy metrics.

## Human

Please create a prompt I can give to an implementing simpler LLM, to update the code skill to what you consider would be the best version.

## Assistant

Here’s a prompt you can paste into another (simpler) LLM to implement the upgrades.

***

### Prompt for Implementing LLM

You are a coding assistant.  
Your task is to **update my existing `/code` Claude Code skill** to a new, stricter version with better TDD enforcement, TRACE, and state management.

I will describe the current system and the required changes.  
**Follow the requirements exactly. Do not invent extra features.**

***

## 1. Context (read carefully)

- The `/code` skill is my “mission control” for AI‑assisted feature development. It already has:  
  - Phases: 0 BOOTSTRAP, 1 ALIGN, 2 DESIGN, 3 BUILD, 3.4 STATIC ANALYSIS, 3.5 TRACE, 4 SHIP.[1]
  - TDD loop in BUILD: RED → GREEN → REFACTOR → VERIFY.[1]
  - TRACE phase with templates and checklist for manual trace-through.[1]
  - Phase order enforcement hook `hooks/validate_code_phase_order.py` that uses marker files in `.claude/state`.[1]
  - State files: `.claude/state/*.marker`, `build-state.json`, `resume-ledger.json`, `build-runs.jsonl`.[1]

- Environment:  
  - Claude Code skill, skill-based hooks only (PreToolUse).  
  - Windows 11, always Windows paths.  
  - Git repo, Python 3.12+.

Assume the **existing review bundle** (design doc) is correct and already implemented; your job is to **upgrade it** according to the changes below.[1]

***

## 2. High‑level goals

Update the `/code` skill so that:

1. **TDD is strictly enforced**  
   - No task can be “DONE” without RED, GREEN, REFACTOR, VERIFY evidence.  
   - SHIP refuses if any task is missing evidence.

2. **TRACE is mandatory and evidence-driven**  
   - Every code change must go through TRACE (full or light mode).  
   - TRACE uses structured, diff-focused, scenario-based review.

3. **State is robust and minimal**  
   - Terminal‑scoped JSON state for ownership and evidence.  
   - Rollback-aware phase markers tied to git commit to avoid stale verification.  
   - Windows path normalization is automatic.

4. **UX is improved**  
   - `/code --status` shows current phase, markers, task evidence status.  
   - `/code --repair-markers` and `/code --fix-paths` provide guided recovery.  

Only implement what is specified below.

***

## 3. State management changes

### 3.1 New global phase state file

Create/upgrade `.claude/state/code_phase_state.json` with this structure:

- Top level:
  - `version`: string, set to `"2.0"`.
  - `last_updated`: ISO timestamp.
  - `phases`: object keyed by phase name: `"BUILD"`, `"STATIC_ANALYSIS"`, `"TRACE"`, `"SHIP"`.
  - `current_phase`: string name of current phase (e.g. `"BUILD"`).

- Each phase object (e.g. `phases.BUILD`) must contain:
  - `completed`: boolean.
  - `completed_at`: ISO timestamp or null.
  - `commit_hash`: git HEAD hash when phase was completed.
  - `terminal_id`: string ID of the terminal that completed it.

Implementation details:

- Provide a small **Python helper module** (e.g. `utils/phase_state_manager.py`) that has functions like:
  - `load_phase_state() -> dict`
  - `save_phase_state(state: dict) -> None`
  - `mark_phase_completed(phase_name: str, terminal_id: str, commit_hash: str) -> None`
  - `is_phase_valid(phase_name: str, current_commit_hash: str) -> bool`

- `is_phase_valid` must return `False` if:
  - The phase is not marked completed, or  
  - The stored `commit_hash` differs from current git HEAD.

### 3.2 Terminal‑scoped evidence ledger

Create/upgrade `.claude/state/code_evidence_{terminal_id}.json`:

- Top level:
  - `version`: `"1.0"`.
  - `terminal_id`: string.
  - `task_list_id`: string or null.
  - `created_at`, `last_updated`: ISO timestamps.
  - `tasks`: object keyed by `task_id`.

- Each `task` object:
  - `description`: brief string.
  - `evidence`: object with keys `RED`, `GREEN`, `REFACTOR`, `VERIFY`.  
    Each stage contains:
    - `completed`: boolean.
    - `timestamp`: ISO timestamp or null.
    - Optional metadata (test files, test_command, passing/failing counts, checks, etc.).
  - `status`: `"NOT_STARTED" | "IN_PROGRESS" | "DONE"`.
  - `marked_done_at`: ISO timestamp or null.

Provide a **Python `EvidenceManager` class** (e.g. `utils/evidence_manager.py`) with at least:

- Constructor: `EvidenceManager(terminal_id: str)`:
  - Ensures the ledger file exists.
- Methods:
  - `record_red(task_id, test_files, test_command, failing_tests)`
  - `record_green(task_id, impl_files, test_command, passing_tests)`
  - `record_refactor(task_id, refactored_files, test_command, passing_tests)`
  - `record_verify(task_id, checks_dict)`
  - `can_mark_done(task_id) -> (bool, str)`  
    - Returns False if any of RED/GREEN/REFACTOR/VERIFY is not `completed`.
  - `mark_done(task_id)`  
    - Only succeeds if `can_mark_done` is True; otherwise raises.

### 3.3 Terminal‑scoped build state

Create/upgrade `.claude/state/code_build_state_{terminal_id}.json`:

- Stores:  
  - `terminal_id`, `task_list_id`, `owner`, `started_at`, `last_activity`, `status`, `execution_model`, `file_count`, `current_task`.

Implement a function `acquire_build_ownership(terminal_id, task_list_id) -> (bool, str)` that:

- Scans `.claude/state/code_build_state_*.json`.  
- If another terminal has the same `task_list_id` with `status == "ACTIVE"`, returns `(False, message)`.  
- Otherwise, writes/updates this terminal’s `code_build_state_{terminal_id}.json` and returns `(True, "Ownership acquired")`.

***

## 4. Hooks: phase order & rollback

Update `hooks/validate_code_phase_order.py` to:

- Use `code_phase_state.json` instead of raw marker files.
- Determine the requested phase from `--phase=` argument. Support:
  - `"3"`, `"BUILD"`
  - `"3.4"`, `"STATIC_ANALYSIS"`
  - `"3.5"`, `"TRACE"`
  - `"4"`, `"SHIP"`

Behavior:

- BUILD: always allowed.
- STATIC_ANALYSIS (3.4): require valid BUILD (via `is_phase_valid("BUILD", current_hash)`).
- TRACE (3.5): require valid BUILD.
- SHIP (4): require valid BUILD and valid TRACE.

If a required phase is invalid (either never completed or commit hash mismatch):

- Return `{"continue": false, "reason": "<clear message about needing to re-run BUILD/TRACE>"}` and exit with code 2.

Also:

- If no `--phase` is given, allow (auto-detect mode).
- On any unexpected error, **fail-open** (log a warning in the JSON, but set `continue: true`).

***

## 5. TRACE: mandatory, diff-focused, evidence-driven

Make TRACE **mandatory for all code changes**:

- Full TRACE:
  - When any changed file has a code extension (e.g. `.py`, `.ts`, `.js`, `.go`, `.rs`, `.c`, `.cpp`, `.java`).
- Light TRACE:
  - For non-executable changes only (docs/config like `.md`, `.txt`, `.json`, `.yaml`, `.toml`).

Implementation:

- Ensure Phase 3.5 (TRACE) in SKILL.md explicitly states:
  - Full TRACE is required for code changes.
  - Light TRACE is acceptable only if no executable code changed.

TRACE behavior:

- Use a structured prompt/template (like the `TRACE_REVIEW.prompt.md` we designed) that asks for:
  - Scenario table (happy + error + concurrency scenarios).  
  - Mapping scenarios → tests.  
  - TDD anti-pattern check (Liar, Excessive Setup/Giant, Slow Poke, Hidden Dependency/Mockery).  
  - Risk checks (resource management, concurrency, security) based on flags.  
  - Intent alignment table (Requirement → Implementation → Status).  
  - Findings with severity and recommended fixes.

- Ensure TRACE output is saved as a markdown file under `.claude/trace/` (e.g. `trace_report_<timestamp>.md`).

- After successful TRACE:
  - Update `code_phase_state.json` to mark `TRACE` as completed for current git HEAD and terminal_id.

***

## 6. TDD enforcement (completion guard)

Integrate the `EvidenceManager` into BUILD phase steps in SKILL.md:

- After RED (tests added and confirmed failing), call `record_red(...)`.
- After GREEN (tests pass), call `record_green(...)`.
- After REFACTOR (tests still pass), call `record_refactor(...)`.
- After VERIFY (manual checks done), call `record_verify(...)`.

Before marking a task DONE:

- Call `can_mark_done(task_id)` and only proceed if all four evidence stages are completed.  
- If not, surface the reason and **do not** mark the task as done.

Before SHIP:

- Ensure **every task in the task list** either:
  - Is DONE with all four evidence types, or  
  - Is explicitly documented as out-of-scope in the plan (you can assume this is handled in plan.md, just gate on evidence for tasks considered in-scope).

***

## 7. UX commands

Add the following commands/behaviors to SKILL.md:

### `/code --status`

Show:

- Current phase (`current_phase` from `code_phase_state.json`).  
- For each main phase (BUILD, STATIC_ANALYSIS, TRACE, SHIP): completed? when? at which commit? which terminal_id?  
- For the current terminal’s evidence ledger:
  - Count of tasks by status (NOT_STARTED / IN_PROGRESS / DONE).  
  - For each task: which evidence stages are missing (if any).

### `/code --repair-markers`

Behavior:

- Load `code_phase_state.json`.  
- Compute current git HEAD.  
- For each phase with a stored `commit_hash`:
  - If mismatch with HEAD, prompt (text) to clear it (you can describe the prompt and effect in SKILL.md; actual interactive prompt may be manual).  
  - Clearing a phase means setting `completed: false`, `completed_at: null`, and optionally clearing its `commit_hash`.

### `/code --fix-paths`

Even though we’re on Windows, we want consistent Windows-style paths:

- Scan key state files in `.claude/state/*.json` for paths.  
- Normalize any paths into Windows format (`P:\...`) using `pathlib.Path` on Windows.  
- Rewrite the JSON files with normalized paths.

You don’t need a perfect regex; just show a reasonable implementation using Python and `Path`.

***

## 8. Implementation style

- Use **clear, small Python modules** under the skill’s directory: `utils/phase_state_manager.py`, `utils/evidence_manager.py`, `utils/path_utils.py`, etc.
- Avoid unnecessary dependencies; stick to standard library.
- Keep SKILL.md instructions concise but precise; describe the behavior, not internal implementation details.

***

## 9. What to output

Produce:

1. The updated **Python modules** (new or modified) as code blocks.  
2. The updated **hook file** `hooks/validate_code_phase_order.py`.  
3. The SKILL.md changes as markdown snippets showing:
   - Updated BUILD section with evidence usage.  
   - Updated TRACE section with mandatory modes and structured review.  
   - New sections for `/code --status`, `/code --repair-markers`, `/code --fix-paths`.

Do **not** change unrelated parts of the skill.

## Human

should pre-mortem be part of our workflow?  or is that too heavy for this skill intent?

## Assistant

Yes, but only as a **very light, optional pattern** inside ALIGN/DESIGN, not as a full extra phase.

### Why not a full pre-mortem phase?

- The skill is already heavy: 7 phases, strict TDD, STATIC ANALYSIS, TRACE, SHIP.[1]
- Your design explicitly keeps planning phases flexible and lightweight, with strictness reserved for verification (3.4, 3.5, 4).[1]
- A formal pre‑mortem phase with its own artifacts would add more overhead and friction than it’s likely to repay for a solo dev workflow.

### Where it *does* make sense

Bake a **mini pre-mortem checklist** into ALIGN or DESIGN as a short mental model, for medium/high‑risk features:

In Phase 1 (ALIGN), add something like:

- “If risk is medium/high, briefly list:  
  - 2–3 ways this feature could fail badly (data loss, security, concurrency, perf).  
  - For each, one mitigation (extra tests, TRACE focus, logging/guardrails).”

Then:

- Feed these “failure modes” into:  
  - Test planning in BUILD (make sure there’s at least one test per scary scenario).  
  - Scenario selection in TRACE (ensure each pre-mortem scenario appears as a row in the TRACE scenario table).

That way you get the benefit of pre‑mortem thinking without turning `/code` into a project‑management tool.

## Human

What are the main topics in this conversation?

## Assistant

Main topics covered:

- **Current `/code` skill architecture and issues**  
  - Phases (0–4), TDD loop, STATIC ANALYSIS, TRACE, SHIP, phase-order hook, markers, state files, known issues (no rollback detection, multi-terminal collisions, TRACE optionality, path problems).[1]

- **Improvements to the skill**  
  - Stronger TDD enforcement (mandatory RED/GREEN/REFACTOR/VERIFY), mandatory TRACE, rollback-aware markers, terminal-scoped state, auto-resume ledger, Windows path normalization, UX commands (`--status`, `--repair-markers`, `--fix-paths`).[1]

- **Prompts, TRACE, and analysis quality**  
  - TDD prompts for Claude Code, TRACE_REVIEW prompt template, evidence packs, TDD anti-pattern checks, intent-alignment review, diff-focused TRACE and code review ideas.[1]

- **State, mental models, and workflow design**  
  - Rationale for state tracking; phase/evidence schemas; sequential-thinking / chain-of-thought scripts for phases; light pre-mortem integrated into ALIGN/DESIGN rather than a separate phase.[1]

- **Implementation handoffs to other LLMs/tools**  
  - A solution document for upgrading the skill, an implementation prompt for a simpler LLM, discussion of AI-TDD CLI trials, subagents, metrics logging, and integration with modern AI coding practices.[1]
