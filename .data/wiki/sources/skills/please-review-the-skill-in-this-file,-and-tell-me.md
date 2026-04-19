<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# please review the skill in this file, and tell me what we can do to improve it.

The skill is already very strong; the biggest wins now are reducing friction, tightening invariants, and adding “safety rails” around the known issues and manual steps.[^1_1]

Below are targeted improvements grouped by theme.

## 1. Close the Known-Issues Loop

You already have a solid Known Issues section; turn those into explicit design tasks.[^1_1]

- Add rollback-aware markers
    - Store the git commit hash (or a content hash) alongside each `code-*-complete.marker` in a small JSON (e.g., `.claude/state/code-phase-state.json`).[^1_1]
    - On hook validation, compare current `HEAD` (or key files’ hashes) to the stored value; if changed, require re-running STATIC ANALYSIS/TRACE and delete or invalidate the marker.
- Enforce the completion guard at the hook level
    - The completion guard is currently a behavioral expectation; encode it as state: track whether RED, GREEN, REFACTOR, VERIFY evidence exists for each task in the resume ledger, not just in narrative output.[^1_1]
    - Have BUILD write structured evidence entries (per task) and add a guard that refuses SHIP if any task is missing one of the four evidence types.
- Make multi-terminal collisions impossible by default
    - Persist `--task-list-id` in `.claude/state/build-state.json`, and refuse a second BUILD session unless it either:
        - uses the same ID, or
        - passes an explicit `--force-takeover` flag that is logged to the ledger.[^1_1]


## 2. Reduce Manual / “Remember To Do X” Steps

There are several places where you rely on human discipline; push more into enforced protocol.[^1_1]

- Make TRACE truly mandatory for code changes
    - The docs say TRACE is optional for trivial changes, but your non‑negotiables and ROI story argue TRACE should be default for all code edits.[^1_1]
    - Split the concept:
        - `/code --phase=3.5 --mode=full` (default for any code delta).
        - `/code --phase=3.5 --mode=light` only for clearly non-executable changes (e.g., Markdown), and still write a “no-op TRACE” record into the ledger so the SHIP guard is satisfied in a structured way.
- Auto-create and maintain the resume ledger
    - Right now, resume-ledger updates are described as manual.[^1_1]
    - Add a small helper script invoked by phases to append evidence; never rely on manual editing.
    - Include: task id, phase (RED/GREEN/REFACTOR/VERIFY), timestamp, files touched, test command, result.
- Automatically normalize paths
    - You already have `runtime_fingerprint.py` and path translation as manual workarounds.[^1_1]
    - Add a small “path normalization” helper that:
        - Detects Windows vs WSL vs native,
        - Rewrites `P:\...` ↔ `/mnt/p/...`,
        - Is called before running any verifier commands, so the skill always uses normalized paths internally.


## 3. Strengthen Phase \& Evidence Modeling

You have excellent conceptual modeling (phases, markers, evidence types), but they are slightly under-specified at the data level.[^1_1]

- Model phases and evidence as first-class data structures
    - Define a small JSON schema:
        - `phase_state.json`: current phase, prerequisites satisfied, markers, last commit hash.
        - `evidence.json`: per-task evidence objects with fields for test commands, coverage numbers, and link to TRACE report.[^1_1]
    - This makes it easier to build future tooling (dashboards, auto-resume, analytics).
- Add intra-phase progress markers
    - Markers today are coarse-grained (“BUILD complete”).[^1_1]
    - For long-running features, add sub-markers like `code-build-task-N-complete.marker` or just store this in `build-state.json`, so resuming is more precise and the hook can distinguish “BUILD never started” vs “BUILD partially done but incomplete”.
- Make SHIP’s “smart build verification” explicit
    - Extract the SHIP checks into a clear checklist (tests passing, coverage threshold, no blocking findings) with machine-readable state, not only narrative log.[^1_1]
    - Let SHIP append a final certification record with: commit hash, test summary, coverage, TRACE findings summary.


## 4. Improve UX and Failure Modes

The system is powerful but could feel heavy in daily use. You can keep guarantees while smoothing ergonomics.[^1_1]

- Add a “status / introspect” command
    - Provide `/code --status` that prints:
        - Current phase, which markers exist, last TRACE run, unresolved evidence gaps, active task list id.[^1_1]
    - This removes guesswork when you jump back into a feature days later.
- Provide guided recovery flows for common issues
    - For rollback detection or path problems, instead of saying “manually delete markers” or “run runtime_fingerprint.py”, add a dedicated subcommand:
        - `/code --repair-markers` to recompute or clear markers safely.
        - `/code --fix-paths` to run the path normalization routine.[^1_1]
- Make behavioral gate warnings more context-aware
    - behavior_gates_config.json currently uses simple patterns with known false positives.[^1_1]
    - Add:
        - an allowlist of contexts where “you should modify” is acceptable (e.g., during planning phases),
        - a “severity level” so benign matches produce a low-friction note instead of a blocking-style warning.


## 5. Tighten Documentation \& Integration Points

Your review bundle is excellent; a few structural tweaks will make it easier for future you (or other agents) to plug into it.[^1_1]

- Extract “non‑negotiables” into a machine- and human-readable contract
    - Keep the textual list, but also add a small `non_negotiables.json` that enumerates:
        - enforced order (BUILD → TRACE → SHIP),
        - evidence requirements,
        - TRACE mandatory criteria.[^1_1]
    - Hooks and sub-tools can then reference this single source of truth.
- Provide minimal “quick start” and “advanced usage” views
    - SKILL.md is dense because it encodes the whole methodology.[^1_1]
    - Add a short “quick start” section: 10–15 lines for the common case (`/code "implement X"` with standard thresholds) and one table showing flags (`--phase`, `--task-list-id`, `--status`, etc.).
    - Keep the detailed flow and case studies as appendices.
- Document extensibility contracts more formally
    - For each integration point (custom validation rules, TRACE extensions, behavioral gates), specify:
        - JSON schemas for stdin/stdout,
        - expected exit codes,
        - stability guarantees across versions.[^1_1]
    - That will let you evolve v3+ without breaking existing hooks.

If you’d like, next step could be: pick one of these (e.g., rollback-safe markers or `/code --status`) and we can design the concrete JSON schema, hook logic, and test cases for it.

<div align="center">⁂</div>

[^1_1]: review_bundle_code-skill_20260301.md


---

# note that we are optimizing for claude code, so hooks should be skill based according to claude standards.

"Make multi-terminal collisions impossible by default", The standard pattern is to include the terminal/session ID in the filename to create  terminal-scoped state files.  STATE_FILE_PATTERN: Final = "cflo_state_{terminal_id}.json"

Make TRACE truly mandatory for code changes, yes

Auto-create and maintain the resume ledger, yes

Automatically normalize paths, yes, but we are always on Windows.

Actually, why do we want to track state?

State is there to enforce your non‑negotiables across time, terminals, and interruptions.[^2_1]

### Why track any state at all?

You’ve already implicitly decided to track state via markers, build-state.json, build-runs.jsonl, and the resume ledger. The question is not “state vs no state” but “what is the minimum, high‑leverage state worth keeping?”[^2_1]

You want state because:

- Phase gating is temporal by nature
    - “Cannot TRACE before BUILD” and “Cannot SHIP before TRACE” only make sense if something persists between invocations to prove BUILD/TRACE actually ran.[^2_1]
    - Without a durable trace of those completions, the hook can’t reliably block out‑of‑order phases.
- TDD evidence and TRACE are investments you don’t want to redo blindly
    - Each TRACE run can be 30–60 minutes, and BUILD can involve multiple RED/GREEN/REFACTOR loops.[^2_1]
    - Minimal state lets you know “this code, at this commit, has already paid that cost,” and when a significant change invalidates that guarantee.
- Multi‑terminal / multi‑session safety is fundamentally about identity over time
    - “Collisions” are exactly two agents acting as if they own the same task.[^2_1]
    - Terminal/session‑scoped state (e.g., `cflo_state_{terminal_id}.json`) is the standard Claude Code pattern to establish ownership and safely coordinate concurrent work.
- Resumability and observability are impossible without some memory
    - You already describe “resume ledger” as the thing that enables resume after interruption and multi‑terminal coordination.[^2_1]
    - If you drop that, resuming mid‑feature becomes guesswork; the skill can’t answer “what’s done, what’s missing, what evidence exists?”

So the core rationale: **state is the minimum memory needed to turn a stateless chat into an enforceable workflow with guarantees about order, evidence, and ownership.** Without it, your BUILD→TRACE→SHIP and RED→GREEN→REFACTOR→VERIFY pillars become advisory, not enforced.

### How to keep state minimal and Claude‑friendly

Given the Claude Code optimization and Windows‑only constraint, you can keep this tight:

- Use only skill‑based hooks (PreToolUse) and skill‑local state files, per Claude standards.[^2_1]
- Scope runtime state by terminal/session ID in filenames, e.g. `cflo_state_{terminal_id}.json`, `resume_ledger_{terminal_id}.json`, to avoid collisions by construction.
- Keep global markers extremely small: just “phase X completed at commit Y” plus maybe a summary.[^2_1]
- Only track what you need to enforce:
    - Last BUILD/TRACE commit hash,
    - Whether each task has all four evidence types,
    - Which terminal/session currently owns the task list.

Everything else (logs, narratives) can remain ephemeral.

If you like, next step could be: define a concrete schema for `cflo_state_{terminal_id}.json` and the auto‑maintained resume ledger so they’re just enough to support mandatory TRACE, TDD evidence, and collision‑free multi‑terminal use.

<div align="center">⁂</div>

[^2_1]: review_bundle_code-skill_20260301.md


---

# please create a solution doc I can take to the other LLM.

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

---

# What can we do to improve outcomes?

Three levers will most improve outcomes: stronger enforcement of invariants, better feedback to you, and tighter fit to how Claude actually behaves.[^4_1]

### 1) Make guarantees hard, not soft

These turn your design intent into enforced behavior.[^4_1]

- Mandatory TRACE for all code changes
    - Remove “trivial-change” escape hatches; use full vs light TRACE modes but always require a TRACE completion before SHIP.[^4_1]
- Evidence-based DONE, not vibes-based
    - Enforce the four evidence types (RED/GREEN/REFACTOR/VERIFY) via the ledger and block SHIP if any task is missing one.[^4_1]
- Rollback-aware phase markers
    - Tie BUILD/STATIC_ANALYSIS/TRACE markers to commit hashes and invalidate them on HEAD change so you never rely on stale verification.[^4_1]


### 2) Reduce cognitive + friction cost

These make it easy for future-you to stay on the rails without thinking about the machinery.[^4_1]

- Auto-maintain everything the skill depends on
    - Resume ledger, phase state, and terminal-scoped state files should all be written by utilities, never edited by hand.[^4_1]
    - Normalize Windows paths automatically before any verification/TRACE step so you never debug path nonsense again.[^4_1]
- Add fast introspection and recovery
    - `/code --status` so you always know “where am I, what’s done, what’s missing?” in one shot.[^4_1]
    - `/code --repair-markers` and `--fix-paths` so common failure modes are one-command fixes, not ad-hoc surgery.[^4_1]


### 3) Align tightly with Claude Code’s actual runtime

These increase the chance that the agent does what you intend instead of something “nearby.”[^4_1]

- Skill-based hooks and terminal-scoped state
    - Use the standard `cflo_state_{terminal_id}.json`-style pattern so multi-terminal behavior is predictable and collisions become structurally impossible.[^4_1]
- Behavior gates tuned to your execution models
    - Refine `behavior_gates_config.json` so it understands when “you should modify X” is planning guidance vs an implementation promise, reducing false positives while still catching real violations.[^4_1]

If you want something concrete to move the needle fastest, I’d prioritize: (1) rollback-aware markers, (2) auto evidence ledger + SHIP guard, (3) `/code --status`; those three alone will materially improve reliability and debuggability of your runs.

<div align="center">⁂</div>

[^4_1]: review_bundle_code-skill_20260301.md


---

# Do popular repos have any ideas that can improve our outcomes?

Yes—several emerging tools and writeups suggest patterns you can steal to push outcomes even further.[^5_1][^5_2][^5_3][^5_4]

### 1) Encode more of the workflow *in-repo*

Popular setups put AI-facing standards directly in the repo (e.g., `CLAUDE.md` or similar) so every session, branch, and tool sees the same ground rules.[^5_2][^5_3]

- Add a short, repo-level “AI contract” file alongside SKILL.md with:
    - TDD rules, TRACE requirements, and evidence expectations.
    - Standard commands for tests, lint, typecheck, TRACE entry points.
- This matches the pattern where teams codify AI usage rules in a project file that assistants read automatically, reducing variance and “drift” between sessions.[^5_3][^5_2]


### 2) Tighten CI / PR integration around AI work

Several workflows wire AI use into CI and PR templates to keep humans firmly in control of what merges.[^5_5][^5_4][^5_3]

- Add a minimal PR checklist (template) aligned with your phases:
    - “AI-generated or AI-assisted,” “tests added/updated,” “TRACE report attached/linked,” “risk notes.”[^5_3]
- Run / enforce parts of your `/code` guarantees in CI:
    - Require tests + static analysis on every PR.[^5_4][^5_3]
    - Optionally run a lightweight AI reviewer focused on diffs, but make it advisory—not authoritative.[^5_6][^5_5]


### 3) Borrow from dedicated AI–TDD tools

AI-TDD CLIs and frameworks lean hard into “you write tests, AI writes code until green,” which is exactly your philosophy.[^5_7][^5_1]

- Make the “spec → tests → implementation → refactor” path the *fastest* path in `/code`, not just the most correct:
    - Provide short, ready-made prompts/commands for “generate tests only” and “implementation only from failing tests,” similar to AI-TDD tools.[^5_7][^5_3]
- Consider a small “AITDD mode” in `/code` that:
    - Refuses to write production code until RED exists.
    - Refuses to refactor until GREEN is stable.


### 4) Embrace spec-first, plan-in-file flows

People getting good results with AI-assisted coding tend to push plans and specs into first-class markdown artifacts in the repo.[^5_8][^5_4]

- Lean harder into `plan.md` / `flows/*.md` as the canonical spec:
    - Ensure `/code` always updates the plan with current task status, evidence summaries, and risk notes, similar to “plans/<date>-plan-name.md” patterns.[^5_9][^5_8]
- This keeps AI work auditable and makes it trivial to reconstruct context across terminals and days.


### 5) Add a “delta-focused” review / TRACE mode

Popular AI code review flows focus strictly on diffs (PR changeset) rather than whole files, which tends to reduce noise and missed issues.[^5_10][^5_6][^5_5]

- Add a “TRACE-on-diff” mode:
    - Use git diff to narrow TRACE to only changed functions/regions.
    - Still require full TRACE for high-risk patterns (I/O, locks, concurrency), but allow diff-focused TRACE for low-risk areas to reduce time cost.
- Similarly, let `/code` drive an “AI review this diff only” step that produces a short, structured finding list you can feed into TRACE.


### 6) Instrument and measure

Teams reporting strong results treat AI workflows as systems they instrument, not just habits.[^5_2][^5_4][^5_3]

- Start capturing simple metrics per run in your existing `build-runs.jsonl`:
    - Phase durations, number of TRACE findings by severity, number of times TRACE caught bugs tests missed.[^5_11][^5_2]
- Use those metrics to tune: when TRACE is overkill, where tests are weak, and which parts of `/code` cause most friction.

If you’d like, I can propose a small “v3.0 outcome ramp”: a 3–5 item changeset that specifically pulls in (a) diff-focused TRACE, (b) repo-level AI contract, and (c) CI/PR hooks, so you can trial them on one feature and see if defect rate and friction actually drop.
<span style="display:none">[^5_12][^5_13][^5_14][^5_15][^5_16]</span>

<div align="center">⁂</div>

[^5_1]: https://pyshine.com/Top-AI-Coding-Assistant-Frameworks-Build-Your-Own/

[^5_2]: https://www.raftlabs.com/blog/test-driven-development-with-ai/

[^5_3]: https://rootstack.com/en/blog/llm-best-practices-developers-how-use-ai-software-development-without-losing-control

[^5_4]: https://addyosmani.com/blog/ai-coding-workflow/

[^5_5]: https://graphite.com/guides/integrate-ai-code-review-github

[^5_6]: https://dev.to/daveturissini/build-your-own-ai-code-review-agent-in-5-minutes-with-github-actions-2kcg

[^5_7]: https://github.com/di-sukharev/AI-TDD

[^5_8]: https://www.randalolson.com/2025/11/24/three-phases-ai-assisted-coding/

[^5_9]: https://www.reddit.com/r/ClaudeCode/comments/1qd64xx/tdd_workflows_with_claude_code_whats_actually/

[^5_10]: https://docs.github.com/en/copilot/tutorials/review-ai-generated-code

[^5_11]: review_bundle_code-skill_20260301.md

[^5_12]: https://www.augmentcode.com/tools/13-best-ai-coding-tools-for-complex-codebases

[^5_13]: https://www.youtube.com/watch?v=23x2xsRer9c

[^5_14]: https://www.linkedin.com/posts/alexbunardzic_i-usually-develop-software-by-following-tdd-activity-7385134793803513856-8yVP

[^5_15]: https://kiro.dev

[^5_16]: https://docs.github.com/en/copilot/how-tos/use-copilot-agents/request-a-code-review/configure-automatic-review


---

# Best prompts for Claude Code TDD workflow

Try AI-TDD CLI in our project

Here’s a concise setup you can drop into Claude Code plus a way to experiment with AI-TDD in your repo.[^6_1][^6_2][^6_3]

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

This matches the “test-first prompting” pattern where you explicitly lock the model into generating tests only.[^6_4][^6_3]

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

You can encode these as `.claude/commands` or skill phases (`/red`, `/green`, `/refactor`, `/verify`) similar to the AAID-style workflows.[^6_2][^6_3]

## 2. Trying AI-TDD CLI in your project

AI-TDD gives you a dedicated “you write the test, AI writes the code” loop. You can pilot it on a submodule and keep `/code` as the orchestrator.[^6_5][^6_1]

### 2.1 Basic setup

In a Python/TypeScript project:

1. Install AI-TDD globally or in a venv:
    - `pip install aitdd` (if published) or `pipx install` / clone + `pip install -e .` from the repo.[^6_1]
2. Configure it to use your preferred model/provider (you’ll likely need to adapt its OpenAI wiring to your Claude endpoint or run it only for “proof of concept”).

### 2.2 Minimal workflow in your repo

For one feature directory (e.g., `src/auth`):

1. Write or extend a failing test:
    - `tests/test_auth_login.py` or equivalent.
2. Run AI-TDD in that scope:
    - `aitdd run` from the project root or configured path.[^6_1]
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
<span style="display:none">[^6_10][^6_11][^6_12][^6_13][^6_14][^6_15][^6_6][^6_7][^6_8][^6_9]</span>

<div align="center">⁂</div>

[^6_1]: https://github.com/di-sukharev/AI-TDD

[^6_2]: https://dev.to/dawiddahl/aaid-augmented-ai-development-50c9

[^6_3]: https://github.com/FlorianBruniaux/claude-code-ultimate-guide/blob/main/guide/workflows/tdd-with-claude.md

[^6_4]: https://www.endorlabs.com/learn/test-first-prompting-using-tdd-for-secure-ai-generated-code

[^6_5]: https://dev.to/disukharev/aitdd-ai-cli-for-tdd-you-write-the-test-ai-makes-it-green-32bn

[^6_6]: https://dev.to/disukharev/top-3-open-source-ai-tools-for-programmers-4oed

[^6_7]: https://www.linkedin.com/posts/devsmranjan_ai-tdd-softwaredevelopment-activity-7365454832779882497-TEig

[^6_8]: https://www.reddit.com/r/ClaudeAI/comments/1lnbcb5/code_claude_how_can_i_create_a_workflow_tdd_it/

[^6_9]: https://galileo.ai/blog/tdd-ai-system-architecture

[^6_10]: https://github.com/readme/guides/github-copilot-automattic

[^6_11]: https://alexop.dev/posts/custom-tdd-workflow-claude-code-vue/

[^6_12]: https://www.youtube.com/watch?v=_JjQRZEOOY8

[^6_13]: https://www.reddit.com/r/PromptEngineering/comments/1dk1zmi/introducing_promptml_cli_write_and_execute/

[^6_14]: https://github.com/di-sukharev/AI-TDD/actions

[^6_15]: https://agentic-design.ai/ai-driven-dev/prompt-libraries


---

# what about ways to improve the trace or analysis to make sure we have written good code?

You’ll get the biggest lift by making TRACE more evidence-driven, more risk-focused, and more structured around known failure modes.[^7_1][^7_2][^7_3]

## 1) Make TRACE “evidence-first”, not commentary-first

Instead of “walk the code and see what you notice,” package concrete signals and require specific outputs.[^7_3][^7_1]

- Always feed TRACE with an evidence bundle:
    - Relevant tests and their names (especially ones that exercise the traced code).
    - Recent failures (stack traces, logs, fuzzing outputs if any).
    - Risk tier for this change (e.g., touches I/O, money flow, auth, locks).[^7_4][^7_1][^7_3]
- Require a structured TRACE report:
    - Table of scenarios (happy path, each error path, concurrency scenarios), listing: inputs, preconditions, expected outcomes, actual code path taken, resource state at exit.[^7_2][^7_3]
    - Explicit “evidence links”: which tests cover which scenario, and which scenarios currently have no tests.

This shifts TRACE from “general reasoning about code” to “explain how each important scenario behaves and what proves it,” which matches evidence-first review patterns.[^7_1][^7_2]

## 2) Hard-code checklists for specific risk classes

Your TRACE_CHECKLIST already has categories; tighten it with domain-specific micro-checklists and require filling them.[^7_5][^7_6][^7_3]

Examples:

- For resource management / I/O:
    - For each opened resource (file handle, DB connection, lock), list all possible exit paths and confirm where it is closed/released, or flagged as a bug.
    - Check for “hidden” allocations (temp files, large in-memory buffers) and verify bounded lifetime.[^7_5][^7_2][^7_3]
- For locking / concurrency:
    - Require an explicit table of lock acquisition order across functions to detect potential deadlocks.
    - For each lock: identify contention risks, timeouts, and behavior under failure (what if the lock can’t be acquired?).[^7_6][^7_7][^7_3]
- For security-sensitive paths (auth, payments):
    - Require checks for auth/authorization at every entry point, input validation, and output encoding/sanitization.[^7_4][^7_2][^7_5]

You can bake these into TRACE templates so each high-risk change type has its own mini-protocol rather than one generic checklist.[^7_3][^7_5]

## 3) Diff-focused TRACE + anti-pattern sweeps

Borrow from modern AI code-review practice: focus TRACE on deltas and known anti-patterns.[^7_8][^7_9][^7_10]

- TRACE on the diff first:
    - Use `git diff` to constrain TRACE to changed functions/blocks; require a “diff coverage” section: what changed, old behavior vs new behavior, and why it’s safer/better.[^7_10][^7_11]
- Add an anti-pattern checklist:
    - For TDD: tests that assert too many things, brittle sequencing, hidden dependencies, overly broad mocks.[^7_12][^7_8]
    - For general code: enumerator/sequencer patterns, catch-all exceptions, feature flags with dead branches, etc.[^7_8][^7_10]

Have TRACE explicitly mark “found/not found” for a short anti-pattern list so you can systematically eliminate classes of issues over time.[^7_10][^7_8]

## 4) Strengthen alignment with intent and spec

A lot of AI-generated bugs are “spec drift”: code is clean but not what was asked.[^7_2][^7_4]

- Always include original intent:
    - Attach the relevant `plan.md` section or user story to TRACE and require an “intent match” section:
        - What the spec promised.
        - How each function/endpoint implements it.
        - Any discrepancies or ambiguities.[^7_4][^7_3]
- Track important prompts / instructions as inputs:
    - For high-risk changes, include the key Claude prompts that produced the code and have TRACE verify that the implementation still matches the original intent (no extra side effects, no dropped constraints).[^7_1][^7_4]

This addresses the “confidently incomplete” pattern where the code looks fine but silently omits business rules.[^7_2][^7_4]

## 5) Close the loop with tests and CI

Finally, treat TRACE as something that should spawn tests and be checked later, not just a moment-in-time review.[^7_13][^7_5][^7_3]

- Require TRACE to propose at least one additional test per non-trivial change, then either:
    - Add it, or
    - Explicitly log why it’s not worth adding (so future you can revisit).[^7_13][^7_12][^7_5]
- Tie TRACE to CI:
    - For high-risk areas, add a CI job that fails if new code in those directories landed without a corresponding TRACE report marker or without new/updated tests.[^7_14][^7_12][^7_3]

Together, these tweaks turn TRACE into a structured, evidence-backed, risk-aware review step that systematically finds the kinds of bugs AI code is prone to, instead of being a generic pass over the code.
<span style="display:none">[^7_15][^7_16][^7_17][^7_18][^7_19]</span>

<div align="center">⁂</div>

[^7_1]: https://www.propelcode.ai/blog/evidence-first-ai-code-review

[^7_2]: https://brightsec.com/blog/5-best-practices-for-reviewing-and-approving-ai-generated-code/

[^7_3]: review_bundle_code-skill_20260301.md

[^7_4]: https://www.kluster.ai/blog/best-code-review-practices

[^7_5]: https://owasp.org/www-project-web-security-testing-guide/v41/2-Introduction/

[^7_6]: https://www.linkedin.com/posts/leslie-tsai-18845a25a_my-notes-for-db-lock-usages-i-am-still-learning-activity-7372283020256415745-luaO

[^7_7]: https://www.collectionscanada.gc.ca/obj/thesescanada/vol2/002/MR38272.PDF?is_thesis=1\&oclc_number=642437298

[^7_8]: https://www.codurance.com/publications/tdd-and-anti-patterns-chapter-4

[^7_9]: https://dev.to/lymah/building-effective-prompts-and-workflows-for-code-review-with-goose-51m1

[^7_10]: https://roadmap.sh/code-review-best-practices

[^7_11]: https://dev.to/daveturissini/build-your-own-ai-code-review-agent-in-5-minutes-with-github-actions-2kcg

[^7_12]: https://github.com/readme/guides/github-copilot-automattic

[^7_13]: https://www.linkedin.com/posts/adenfraser_ai-isnt-breaking-code-review-culture-shipping-activity-7420027542033670144-awnE

[^7_14]: https://graphite.com/guides/integrate-ai-code-review-github

[^7_15]: https://www.reddit.com/r/ClaudeAI/comments/1lb1tsa/how_are_you_guys_able_to_carefully_review_and/

[^7_16]: https://aipromptsx.com/prompts/frameworks/trace

[^7_17]: https://graphite.com/guides/ai-code-review-implementation-best-practices

[^7_18]: https://github.com/fluidfocuschannel/ai-code-review-prompts

[^7_19]: https://www.microsoft.com/en-us/research/publication/trace-is-the-new-autodiff-unlocking-efficient-optimization-of-computational-workflows/


---

# Example prompts from ai-code-review-prompts repo for Claude

How to implement evidence packs in TDD traces
Common TDD anti-patterns to catch in analysis
Best ways to verify AI code matches prompt intent
Tools for automating trace verification in Claude workflows

Here are concrete patterns you can lift directly into your `/code` + TRACE workflow.

***

## 1) Example Claude-style review prompts (from ai-code-review-prompts–style repos)

Repos like `ai-code-review-prompts` and `awesome-reviewers` use long, structured prompts that you can adapt for Claude Code.[^8_1][^8_2]

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
> 1. **Correctness \& spec alignment**
>    - Does the code clearly implement the described behavior?
>    - Identify any missing edge cases or error paths.
> 2. **TDD quality**
>    - Are the tests sufficient, focused, and deterministic?
>    - Point out any TDD anti-patterns (liars, excessive setup, giants, slow pokes, etc.).
> 3. **Security \& robustness** (if applicable)
>    - Highlight potential vulnerabilities or unsafe patterns.
> 4. **Performance \& maintainability**
>    - Note obvious performance issues and design smells.
>
> **Output format (markdown)**
> - `Summary` (2–3 bullets, include overall risk level)
> - `Issues` (table: severity, location, description, suggestion)
> - `TDD findings` (table: test name, smell/anti-pattern, fix)
> - `Suggested follow-up tests` (list)

You can specialize by language or framework, similar to `java/spring-boot-comprehensive.md` in that repo.[^8_2]

***

## 2) Evidence packs in TDD traces

Borrowing from “evidence-first” review ideas: make TRACE consume and produce explicit evidence bundles.[^8_3][^8_4]

### Structure of an evidence pack

For each unit of work (task/function/module), define an evidence pack:

- **Inputs**
    - Spec snippet / user story ID
    - Changed files \& git diff for this change
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

Over time you can persist these evidence packs alongside `build-runs.jsonl` so they become part of the audit trail.[^8_4][^8_3]

***

## 3) TDD anti-patterns to check in analysis

Summarizing from common lists (Carr, Codurance, Marabesi, quii):[^8_5][^8_6][^8_7][^8_8]

Have TRACE (or a dedicated “TDD review” step) explicitly check for:

- **The Liar**
    - Tests that pass even when the code is clearly wrong (over-mocked, asserting the wrong thing, assertions that don’t touch the behavior under review).[^8_7][^8_5]
- **Excessive Setup / Giant**
    - Tests with huge setup blocks, many collaborators, or “god” fixtures—these hide the behavior under a lot of noise and signal poor design.[^8_6][^8_5]
- **Slow Poke**
    - Tests that are slow due to hitting real networks, disk, or heavy DB operations; they make the suite too slow to run in tight TDD loops.[^8_5][^8_7]
- **Hidden Dependency / Mockery**
    - Tests that only verify mocks/stubs interactions instead of real behavior, leading to false confidence when interfaces change.[^8_8][^8_7][^8_5]

Prompt addition:

> As part of this review, explicitly check for common TDD anti-patterns: the Liar, Excessive Setup, the Giant, Slow Poke, Hidden Dependency, Mockery.
> For each test file, output a table: `test / anti-pattern / why / suggested refactor`.

***

## 4) Verifying AI code matches prompt intent

This is about making “intent vs implementation” an explicit diff.[^8_9][^8_10][^8_11]

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

This catches “looks good but doesn’t do what I asked” failures and implicitly drives better test coverage.[^8_11][^8_9]

***

## 5) Tools / patterns to automate trace verification in Claude workflows

Within Claude Code, you don’t have external tools, but you can simulate “automation” via:

- **Skill-based hooks**
    - PreToolUse hooks that block `/code --phase=4` unless an evidence pack and TRACE report exist for the current commit.[^8_4]
- **Standardized prompts as files**
    - Store your review/TRACE prompts as `.prompt` or `.md` files (like `ai-code-review-prompts` and `prompt-file-examples` do) and have SKILL.md reference them by name or snippet.[^8_12][^8_2]
- **Checklists encoded as JSON**
    - Put your TDD anti-patterns and risk-specific checklists into a small JSON (e.g., `trace_checklists.json`), then have your prompts say “walk this checklist and mark each item yes/no with justification,” which increases consistency across sessions.[^8_13][^8_2][^8_4]

Outside Claude Code, other tools that illustrate useful patterns (even if you don’t adopt them directly):

- **Prompt libraries** like `awesome-reviewers` and `ai-code-review-prompts` for specialized reviewers (security, performance, framework-specific).[^8_1][^8_2]
- **Prompt-file runners** (like Continue’s `.prompt` files and similar) that treat prompts as code, enabling reuse and versioning of review flows.[^8_14][^8_12]

If you want, next step could be: I can draft a concrete `TRACE_REVIEW.prompt.md` file tailored to your `/code` skill that bakes in evidence packs, TDD anti-pattern checks, and intent-alignment in one reusable template.
<span style="display:none">[^8_15][^8_16][^8_17][^8_18][^8_19]</span>

<div align="center">⁂</div>

[^8_1]: https://github.com/baz-scm/awesome-reviewers

[^8_2]: https://github.com/fluidfocuschannel/ai-code-review-prompts

[^8_3]: https://www.propelcode.ai/blog/evidence-first-ai-code-review

[^8_4]: review_bundle_code-skill_20260301.md

[^8_5]: https://marabesi.com/tdd/tdd-anti-patterns.html

[^8_6]: https://www.codurance.com/publications/tdd-anti-patterns-chapter-1

[^8_7]: https://www.madetech.com/blog/5-tdd-antipatterns/

[^8_8]: https://github.com/quii/learn-go-with-tests/blob/main/anti-patterns.md

[^8_9]: https://www.youtube.com/watch?v=3TIeWruecqc

[^8_10]: https://www.cognativ.com/blogs/post/prompt-engineering-best-practices-for-effective-ai-responses/512

[^8_11]: https://www.kluster.ai/blog/best-code-review-practices

[^8_12]: https://github.com/continuedev/prompt-file-examples/blob/main/code-review.prompt

[^8_13]: https://graphite.com/guides/effective-prompt-engineering-ai-code-reviews

[^8_14]: https://www.reddit.com/r/PromptEngineering/comments/1dk1zmi/introducing_promptml_cli_write_and_execute/

[^8_15]: https://github.com/x1xhlol/system-prompts-and-models-of-ai-tools

[^8_16]: https://www.reddit.com/r/ChatGPTCoding/comments/1f51y8s/a_collection_of_prompts_for_generating_high/

[^8_17]: https://projectdiscovery.io/blog/ai-code-review-vs-neo

[^8_18]: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices

[^8_19]: https://aipositive.substack.com/p/my-ai-code-reviewer-needed-a-project


---

# yes please

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
- **Tests \& results**:
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
| :-- | :-- | :-- | :-- | :-- | :-- |

- Include at least:
    - 1–2 **happy paths**
    - All important **error paths** (exceptions, invalid input, timeouts)
    - Any relevant **concurrency scenarios** (if risk profile includes locks/async)
- In “Tests Covering It”, list specific test names or mark `NONE`.

***

### 3. TDD \& test quality check

> Evaluate how well tests guard the traced scenarios and look for TDD anti-patterns.

3.1 **Coverage by scenario**

- For each scenario in the table, state whether coverage is:
    - `Well Covered`, `Partially Covered`, or `Not Covered`.
- Note any **behavior that is only asserted indirectly** (e.g., via mocks).

3.2 **TDD anti-patterns**

Use this table:


| Test (file::name) | Anti-pattern | Why It’s a Problem | Suggested Fix |
| :-- | :-- | :-- | :-- |

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
| :-- | :-- | :-- | :-- |

- Extract explicit requirements and constraints from the spec/prompt.
- For each, map to functions/lines or mark as `Missing` or `Unclear`.

5.2 **Unrequested behaviors**

- List any behaviors or side effects **not requested** in the spec/prompt (e.g., extra logging, caching, retries, additional data writes).
- For each, state whether it seems **safe**, **risky**, or **undesired**.

***

### 6. Findings \& recommended actions

> Summarize what you found and what to do next.

6.1 **Findings table**


| Severity (P0–P3) | Area (Scenario/Test/Risk/Intent) | Description | Recommended Change |
| :-- | :-- | :-- | :-- |

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

---

# what about sequential thinking or chain of though versions or mental models, so they have a place in our code skill, in any way?

Yes—sequential thinking is already implicit in your phases; you can make it explicit by baking a few lightweight “thinking scripts” into SKILL.md.[^10_1]

### 1) RED/Green/Refactor as explicit mental scripts

Add short “thinking macros” for each TDD step so Claude walks the same internal sequence every time.[^10_1]

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

Document these as small, numbered checklists in SKILL.md under the BUILD phase so Claude’s “chain of thought” is constrained and repeatable without requiring verbose reasoning.[^10_1]

### 2) TRACE mental model: scenario-first, path-second

For TRACE, define a mental model like:

1) List scenarios (happy path, each error path, each concurrency scenario).
2) For each scenario: follow the code line by line, track key variables/resources.
3) For each step: ask “what can go wrong here?” and “who cleans this up?”
4) Only then summarize findings.

You’ve already got templates; adding this 3–4 step “how to think” block at the top of TRACE_TEMPLATES.md tells Claude *how* to walk the code, not just *what* to output.[^10_1]

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

These can be small bullets in Phase 1–2 sections and become the “chain of thought” Claude follows before touching code.[^10_1]

### 4) Skill-level guidance on “thinking, then acting”

Finally, at the top of SKILL.md, add a short global rule for Claude:

- Always:

1) Restate the current phase and goal in one sentence.
2) List 3–5 steps you’ll follow.
3) Execute them in order, checking back to the list before moving on.

That gives you sequential thinking baked into the workflow without flooding outputs, and it fits naturally into your existing 7-phase / TDD / TRACE structure.[^10_1]

<div align="center">⁂</div>

[^10_1]: review_bundle_code-skill_20260301.md

