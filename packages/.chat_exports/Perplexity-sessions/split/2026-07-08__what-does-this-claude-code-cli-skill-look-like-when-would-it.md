---
title: "what does this claude code cli skill look like?  when would it be used in the sdlc?"
date: "2026-07-08"
mode: "COPILOT"
uuid: "f2a0dcc3-1596-4c92-9102-ed04f8da54b6"
entry_count: 6
---

## Human

what does this claude code cli skill look like?  when would it be used in the sdlc?

## Assistant

This Claude Code CLI skill is a modernization “mission control” for refactoring working codebases into a higher-quality, Python‑2025‑compliant, solo‑dev‑friendly architecture; in the SDLC it sits squarely in the evolution/maintenance phase, but is designed to be invoked repeatedly at key inflection points (pre‑feature, post‑incident, pre‑release) rather than just once at end‑of‑life.[1]

## What the skill looks like

- **Skill metadata and intent**  
  The skill is named `evolve`, version `1.0.3`, with description “Unified modernization workflow to transform working code into high-standard systems,” marked as `user-invocable: True` and categorized under `evolution`.[1]
  It is triggered by utterances like “evolve this”, “modernize this”, “technical debt”, “refactor for quality”, “code smell”, and “Python 2025 migration”, and expects a `targetdirectoryorfile` argument plus context about codebase structure, complexity metrics, project standards, and performance baseline.[1]

- **Position in the architect ecosystem**  
  In the `cc-skills-architect` hub, `evolve` is listed under “Meta-Development Toolbox” as “Modernization and technical debt refactoring,” alongside skills like `garden` (knowledge cleanup) and `usm` (master skill/plugin coordinator).[1]
  It depends on other skills such as `debug`, `rca`, `analysis-profile`, `analysis-audit`, `learn`, `llm-debate`, `brainstorm`, `tdd`, `aid`, and tools such as `python`, `radon`, `lizard`, `git`, `uv`, indicating it orchestrates a multi-skill, multi-tool modernization flow rather than doing a single refactor in isolation.[1]

- **Four‑phase modernization workflow**  
  The core of the skill is a 4‑phase process: AUDIT, STRATEGY, EXECUTE, HARDEN, with explicit STOP gates between each phase.[1]

  - Phase 1 – **AUDIT (Measure debt, baseline)**  
    Uses `refactor --churn` for churn × complexity hotspots, `analyze --focus quality --focus library` for structural quality and API drift, `profile --baseline` for performance baselines, and SATD scanning via ripgrep (`rg -n TODO|FIXME|HACK|DESIGN SMELL`). [1]  

  - Phase 2 – **STRATEGY (Design abstraction)**  
    Uses `brainstorm` to generate modernization paths, `design` and `llm-debate` for architectural pattern validation, and `plan refactor-goal --challenge` to break the work into small, checkpoint‑gated tasks, plus ADR auto‑drafting.[1]

  - Phase 3 – **EXECUTE (Transform, purge)**  
    Drives refactors via `refactor files|dir`, deep semantic analysis via `aid refactor` for high‑CC files, mandatory `analyze --focus dead-code` to purge orphans, and `checkpoint` for safety on multi‑file changes; optionally gates structural changes behind `tdd on`. [1]  

  - Phase 4 – **HARDEN (Certify, seal)**  
    Runs `profile --compare` to verify performance gains/regressions, logs complexity deltas into a debt ledger, invokes `verify --tier 1,2,3` for tests, and finally `learn` to sync the knowledge base and project constitution plus auto‑generated ADR records.[1]

  Each phase has its own objective, tools, and exit criteria, and the skill is explicit that AUDIT (validation) is separate from STRATEGY (generation), and EXECUTE (generation) is separate from HARDEN (validation).[1]

- **Constitutional constraints and solo‑dev focus**  
  The skill enforces a SoloDev “constitution”: no enterprise patterns (monitoring layers, circuit breakers, microservices, horizontal scalability as a default), and requires `SoloDevConstitutionalFilter` to check every proposed modernization action for violations before recommendations are accepted.[1]
  There is a hard rule that cyclomatic complexity (CC) ≥ 10 must be refactored regardless of whether the code is “legacy” or newly written; there is explicitly “no distinction between new and legacy code.”[1]

- **Technical debt smell catalog and thresholds**  
  The pack includes a dedicated “Technical Debt Smell Patterns” section listing structural smells (circular imports, global path hacks, anemic models, large downloaders), Python 2025 antipatterns (legacy config via `os.getenv`/`configparser`, blocking async via `requests` in `async def`, manual `asyncio.create_task` without tracking, deprecated API usage), plus project‑specific debt such as SQLite locking and Rich console issues.[1]
  It codifies thresholds like “Function 50 lines,” “Class 300 lines,” and “CC 10” as clear signals that refactor work is required.[1]

- **GoT/ToT defaults and opt‑out flags**  
  The test file `C.claude-skills-architect1.0.23optoutflags.py` shows that the skill is designed with Graph‑of‑Thought (GoT) and Tree‑of‑Thought (ToT) analysis enabled by default (“quality‑first design”), with opt‑out via CLI flags `--no-got`, `--no-tot` or environment variables `EVOLVENOGOT`, `EVOLVENOTOT`.[1]
  Tests confirm flag independence (each can be disabled separately) and that disabling them does not bypass constitutional safety checks, indicating the skill is structured around multi‑path reasoning but still allows a simpler mode when desired.[1]

## Where it fits in the SDLC

- **Primary SDLC phase: maintenance/evolution**  
  Conceptually, `evolve` is an evolution/maintenance skill: it operates on “working but smelly” code and focuses on technical debt elimination, modernization to Python‑2025 standards, and structural quality improvements while preserving behavior.[1]
  It is not a greenfield design tool — it expects an existing codebase, complexity metrics, performance baselines, and SATD markers, and it updates the project constitution/CKS after changes.[1]

- **Secondary roles in design and pre‑implementation**  
  Phase 2 (STRATEGY) uses design, llm‑debate, and ADR drafting, so it also plays a role in architecture/design decisions when planning significant refactors or migrations, especially when the anticipated implementation time is ≥ ~2 hours.[1]
  The skill encourages multi‑agent debate (`architect`, `reviewer`, `performance optimizer`, `security expert`) before committing to modernization patterns, which aligns with design‑time decision making around refactors, migrations, and pattern adoption.[1]

- **Typical usage moments across the lifecycle**

  | SDLC moment | How `evolve` is used | Notes |
  |------------|----------------------|-------|
  | Post‑MVP / pre‑scaling | Run full AUDIT to map debt before adding major features | Uses churn+complexity, quality/dependency scan, baseline profiling. [1] |
  | Pre‑major refactor / migration | Use STRATEGY to design abstraction, debate patterns, draft ADRs | Validates Python 2025 patterns, solo‑dev viability, incremental plan. [1] |
  | During structural refactor | Use EXECUTE to orchestrate multi‑file refactors, deep analysis, dead‑code purge with checkpoints | Optional TDD gate, mandatory dead‑code analysis. [1] |
  | Pre‑release hardening | Use HARDEN to certify performance, run tests, update CKS and ADR | Enforces zero‑regression rule and standards compliance. [1] |
  | After incidents or regressions | Combine `debug`/`rca` with `evolve` to fix systemic flaws revealed by hotspots | Integrates with `rca` and `analysis-profile` for systemic debt fixes. [1] |

  In other words, you’d call this skill:

  - When you see accumulating technical debt and want a structured, evidence‑first modernization campaign rather than ad‑hoc refactors.[1]
  - When planning a migration to modern Python‑2025 APIs or async patterns and need both architectural validation and safe incremental execution.[1]
  - When you want to enforce solo‑dev constraints and prevent enterprise‑style over‑engineering in modernization suggestions.[1]
  - When you need modernizations tied into the project’s governance artifacts: complexity/performance ledgers, CKS, and ADRs.[1]

- **Interaction with other SDLC tooling**  
  The skill assumes surrounding test infrastructure (`verify --tier 1,2,3`), profiling and complexity tooling (`radon`, `lizard`, `profile` via `refactor --churn`), VCS (`git`/checkpoints), and a project constitution (CLAUDE.md / CKS) that it keeps in sync.[1]
  It deliberately forbids refactoring without baseline, editing without checkpoints, and modernization patterns that violate the solo‑dev constitutional constraints, so in your SDLC it acts as a guardrail layer on top of normal coding and testing workflows.[1]

My current read is high‑confidence for the skill’s structure and intent, and medium‑to‑high confidence for the exact SDLC positioning since that depends on how tightly you integrate these skills into your own lifecycle.

If you imagine your own projects, what’s the main trigger you’d want for invoking `evolve` — scheduled debt sprints (e.g., monthly), or event‑driven (after big features, incidents, or performance regressions)?

## Human

claude code has it's own verify command doesn't it?  how does it work?  when would I use it?

## Assistant

Yes: Claude Code has its own **verify** command, but in your packs it shows up as a verification pattern and schema rather than a single monolithic skill; operationally it’s the “run verification commands and parse their output before you’re allowed to claim ‘done’.”[1][2]

## What the verify command is

- **Dedicated verification skill for “before completion”**  
  The `verification-before-completion` pack declares a skill named `verification-before-completion` whose description is “Use when about to claim work is complete, fixed, or passing, before committing or creating PRs – requires running verification commands and confirming output before making any success claims.”[1]
  This skill sits in the `cc-skills-sdlc` suite and is wired into the `go` orchestrator and stop/continuation gates, making verification a first‑class SDLC step rather than an ad‑hoc test run.[1]

- **Verification result schema (tiers, outcomes)**  
  Both `refactor-deps-test` and `verification-before-completion` packs include a JSON schema for `GoVerificationResult`, with fields like `status` (`pending`, `passed`, `failed`, `blocked`, `waived`), `prready` (boolean), an array of `verificationcommands` (each with `command`, `exitcode`, `passed`), and a `simplify` field summarizing verification outcome (`passed`, `failed`, `skipped`).[3][1]
  It also models test verification (`tdd` receipts), mutation testing (`mutation` block with `mutationscore`, `killed`, `survived`), integration verification receipts, and an optional `capabilityaudit` when the task involved command consolidation or routing changes.[3][1]

- **CLI‑oriented verify patterns (CLI and server)**  
  The dedicated `verify` pack (`verify_sig.md`) contains example patterns for “Verifying a CLI change” and “Verifying a server/API change,” demonstrating how to structure verification commands and what failure modes look like.[2]

  For CLI changes, it calls out:  

  - Unknown flags (e.g. `--json`) not wired up → indicates stale build or missing implementation.  
  - Output not valid JSON (e.g. `jq` errors) → serialization bug.  
  - Tool status flags not reflecting the change → regression in the business logic.  
  - JSON fields differing from expectations → claim/code mismatch, destructive behavior, or incorrect I/O.[2]

  For server/API changes, failures include:  

  - Header absent → diff didn’t take effect or you’re hitting the wrong deploy.  
  - Header present but NaN/invalid value → bug in the implementation.  
  - Only 200s with no changed behavior → your verification path never actually exercised the new code.[2]

- **Integration with `go` orchestrator and SDLC gates**  
  The `go` skill is described as an “Evidence‑First SDLC Orchestrator,” with completion tokens like `promisePRREADY`, `promiseBLOCKED`, etc., and an explicit rule that completion must be proven via executable `donewhen` commands (e.g. `pytest tests/test_auth.py`).[3][1]
  Verification is wired via stop gates (`Stopenforcegate.py`) and continuation gates (`gocontinuationgate.py`), which check phase ledgers and verification artifacts before allowing `go` to emit “PR‑ready / Fixed.Done.Verified.” They explicitly forbid emitting those completion tokens when there is no supporting verification evidence.[1][3]

## How verify actually works

Conceptually, “verify” is a combination of:

1. **Running the right commands**  
   The verification skill/orchestrator runs one or more verification commands (tests, linters, mutation testing, API probes) defined in the task contract (`donewhen`) or in default verification policies.[3][1]
   For refactor tasks, you see patterns like:

   - `pytest` suites in RED/GREEN/REGRESSION phases for TDD.[4][3]
   - Mutation testing via `mutmut 3.x` for critical modules.[1][3]
   - Tool‑specific output validators like `refactorverifier.py` and `refactorvalidator.py` that parse tool stdout/stderr and normalize it into verification state.[4][3]

2. **Parsing and normalizing results into a structured artifact**  
   The harness modules (e.g. `C.claude-skills-sdlc1.0.178.py` in the verification pack, `C.claude-skills-sdlc1.0.176.py` in refactor) write verification artifacts into a state directory and then synthesize them into a `GoVerificationResult` JSON document.[3][1]
   That artifact records:

   - Commands executed and whether they passed.  
   - Whether the verification phase state is “green”, “red”, or “refactor” (indicating more work required).  
   - Additional signals (mutation score, health score from synthesis, capability audit results).[4][1][3]

3. **Gate enforcement before completion claims**  
   Stop gate and continuation gate code (`enforcegate.py`, `gocontinuationgate.py`) use phase ledgers and verification artifacts to decide whether the task can be marked complete.[1][3]

   - If verification is incomplete or failed, they emit a blocked status and prevent `go` from reporting PR‑ready or “Fixed.Done.Verified.”[3][1]
   - They explicitly forbid “false completion”: no `promisePRREADY` or “all verification green” if any relevant suite covering the changed surface is still red, and require accurate scoping (e.g., “intent=mixed – report tests X pass, but Y remain failing”).[1][3]

4. **Policy around language and over‑claim**  
   The verification‑before‑completion skill is explicit about language patterns: it treats any phrases like “should”, “probably”, “seems to”, or enthusiastic completion statements (“Great!”, “Perfect!”, “Done!”) without verification as red flags.[1]
   It forces a verification run whenever you’re about to commit, push, create PRs, or claim task completion, and has logic to detect over‑claims in text (e.g., “all tests green”) that aren’t backed by actual evidence artifacts.[3][1]

## When you would use verify

In practice, you’d use the verify command/skill in three main situations:

- **Immediately before any “done” or “fixed” claim**  
  The pack’s core rule is “evidence before assertions”: you invoke verification before committing code, before creating a PR, and before telling yourself or a tool that work is complete.[1]
  That applies whether the change was a feature, bugfix, refactor, or configuration tweak – if you’re about to say “this is fixed/passing,” verification must have run and succeeded.

- **As part of orchestrated SDLC flows (`go`, `refactor`, `evolve`)**  
  In `refactor`, the workflow includes test generation, RED/GREEN/REGRESSION phases, and a `Stop refactor verifier` hook; verification is mandatory before the refactor phase completes.[4][3]
  In `evolve`, Phase 4 (HARDEN) explicitly calls `verify` and `profile --compare` as part of certifying excellence; completion criteria include all tests passing and performance metrics checked.[5]
  In `go`, verification is tied to `donewhen` commands: the orchestrator runs them and only emits completion tokens when those commands succeed and produce a valid verification artifact.[3][1]

- **For targeted verification of specific changes (CLI, API, routing, capability claims)**  
  The `verify` examples for CLI and server changes show how to apply the command when you’ve changed:

  - CLI surfaces: flags, output format, status codes. You’d run the CLI with specific flags, pipe through `jq` or other validators, and check that the diff actually changed output semantics in the way you expect.[2]
  - API behavior: headers, payload fields, status codes. You’d craft request sequences that exercise the changed path and verify both presence and correctness of new headers/fields, and that you actually hit the changed code.[2]
  - Command surfaces or routing: when you consolidate commands or change routing, verification includes a `capabilityaudit` block ensuring that every non‑deferred claim is backed by real implementation paths (no overclaims like “this command is wired” when no backend exists).[3][1]

### Quick SDLC table

| Moment in SDLC | How to use verify | Why it matters |
|----------------|-------------------|----------------|
| Before commit / PR | Run verification‑before‑completion; execute `donewhen` commands and ensure GoVerificationResult.status = `passed` | Prevents shipping changes that “seem fine” but never had tests or checks run. [1][3] |
| After refactor | Use `refactor`’s verifier hooks plus `verify` in HARDEN; ensure RED/GREEN/REGRESSION phases are complete | Avoids refactors that introduce subtle regressions or leave tests broken. [3][4] |
| After feature / API change | Use CLI/server verify patterns: targeted commands that exercise the changed path and check outputs | Ensures the diff is actually live and correct in production‑like flows. [2] |
| Before declaring “all green” | Use verification artifact + scoped reporting rules; never claim global green when related suites are red | Prevents over‑claiming and hides residual failures; supports honest status. [1][3] |

Confidence: high for the existence and behavior of verification skills and schemas in your packs; medium for how they’re wired in your local Claude Code install, since that depends on your specific plugin/hook setup.

Would you prefer to wire `verify` as a single explicit CLI subcommand (e.g. `cc verify <target>`) that wraps these packs, or keep it implicit inside `go`/`refactor` flows and just enforce that every task has a `donewhen` command?  

## Human

why wouldn't we also have it as part of '/go'?

## Assistant

Including verification inside `/go` is actually required in your packs; the interesting design question is whether you *also* expose a separate `/verify` surface, and the main reasons to keep it inside `/go` are about determinism, contract enforcement, and avoiding “false done.”[1][2]

## Why verify is already part of `go`

- **Task contract: `donewhen` + verification**  
  The `go` skill defines a task contract where `acceptancecriteria` is human‑readable (“tests pass, no regressions, docs updated”) and `donewhen` is a single executable command the orchestrator runs to *prove* completion (e.g. `pytest tests/test_auth.py`).[2][1]
  Verification is not optional here; `go` is required to execute `donewhen` and only emit completion tokens like `promisePRREADY` or “Fixed.Done.Verified.” when those commands succeed and a verification artifact is written.[1][2]

- **Evidence‑first SDLC orchestrator**  
  `go` is explicitly described as an “Evidence‑First SDLC Orchestrator Dispatch Contract,” with rules like “Do NOT emit `promisePRREADY` or Fixed.Done.Verified for that run” when verification hasn’t been performed or is incomplete.[2][1]
  It ties completion status to a `GoVerificationResult` artifact (status `passed/failed/blocked/waived`, commands run, TDD receipts, mutation results, capability audit), so verification is structurally part of how `/go` decides whether a task is done.[1][2]

- **Stop/continuation gates enforcing verify before completion**  
  The stop gate (`Stopenforcegate.py`) and continuation gate (`gocontinuationgate.py`) read phase ledgers and verification artifacts from the `GOSTATEDIR` to decide if the current run can move from “in progress” to “completed.”[2][1]
  They explicitly prevent `go` from emitting completion tokens when verification artifacts show red or missing state, and they enforce scoped reporting (no claiming “all green” when some relevant suites are still failing).[1][2]

- **Verification‑before‑completion skill is wired as a gate around completion language**  
  The `verification-before-completion` skill is designed to run when you’re “about to claim work is complete, fixed, or passing, before committing or creating PRs,” and it’s integrated into `go` via hooks and gates rather than as a completely separate workflow.[1]
  It monitors language (“should”, “probably”, “seems to”, “Done!”) and forces verification before `/go` is allowed to finalize and report success, which is exactly “verify as part of `go`.”[2][1]

## Why you *want* verify inside `go` (not only as a separate command)

- **Prevent “verify drift” between what was changed and what gets checked**  
  When verification is part of `/go`, the orchestrator has access to the task’s scope, files touched, and `donewhen` commands, so it can ensure that verification is aligned with the actual change.[2][1]
  If verify were only a separate command, there’s a risk of running generic checks that don’t exercise the changed surfaces, then claiming completion anyway; embedding it in `/go` ties verification to the task plan and change set.

- **Single source of truth for completion semantics**  
  `/go` is the place where you decide “is this task done?” and the packs make completion semantics dependent on verification artifacts (`GoVerificationResult`, phase ledgers).[1][2]
  Putting verify outside `/go` would duplicate completion logic: you’d need another place to interpret verification results and decide whether to mark tasks complete, increasing the chance of divergence or bugs.

- **Better automation and multi‑agent orchestration**  
  `go` already classifies task complexity and execution tier, chooses models, and handles delegation (PI harness, Claude subagents, local verification runs).[2][1]
  Having verify inside `/go` lets the orchestrator automatically decide:

  - Which verification commands to run (unit tests, mutation tests, CLI checks, API probes).  
  - How to interpret results (pass/fail/blocked/waived).  
  - Whether to pause for authorization, spawn a subagent, or block the run.[1][2]

  Doing that in a standalone `/verify` would require replicating all of this orchestration or rely on manual configuration per invocation.

- **Consistent evidence ledger and audit trail**  
  The packs use phase ledgers and artifacts under `GOSTATEDIR` to record verification evidence and decisions, and `/go` is the orchestrator that writes and reads these.[2][1]
  Keeping verify inside `/go` ensures every task’s verification history is consistently logged, auditable, and tied to task IDs and terminal/session IDs; a separate `verify` command could write artifacts that aren’t connected to task ledgers unless you duplicate that plumbing.

## Why you might *also* expose a separate `/verify` surface

Even though verify is already part of `/go`, there are still good reasons to have an explicit `/verify` command:

- **Ad‑hoc or exploratory verification**  
  When you’re experimenting or doing manual edits outside a `go` task, an explicit `/verify` lets you run “verification‑before‑completion” on a target (CLI, API, module) without going through full task orchestration.[3]
  The `verify` examples (CLI change, server change) are exactly this: they teach patterns a developer can run directly, not only via `go`.[3]

- **Human‑centric workflows (e.g. local hacking, pre‑commit)**  
  In a solo‑dev CLI, you might want `cc verify <path>` or `cc verify cli` as a quick guardrail before `git commit` or `gh pr create`, even when you’re not using `go` to drive the task.[3][1]
  That’s less about orchestrated SDLC and more about developer ergonomics; the packs clearly care about this (“Verification Before Completion – use when about to claim work is complete, fixed, or passing”) so a standalone command fits that mental model.[1]

- **Specialized verification scenarios**  
  Some verification flows (mutation testing, capability audits for command/routing changes) might be heavy enough that you want to run them selectively, not every time `/go` completes a small task.[2][1]
  An explicit `/verify` lets you choose which verification tiers to run, whereas `/go` can keep a minimal baseline for fast tasks and escalate when the task contract demands it.

### How they complement each other

You can think of it like this:

- `/go` = “SDLC orchestrator”: plan → implement → verify → report, with verification as an internal phase wired to `donewhen` and gates.[1][2]
- `/verify` = “verification lens”: run targeted verification for a change or surface (CLI, API, module) and produce a `GoVerificationResult` or similar artifact, which `/go` can later consume if invoked as part of a task.[3][1]

Given your architecture, the main risk of *not* having verify as part of `/go` would be allowing `go` to mark tasks complete based only on model output or human assertions, which your packs explicitly forbid.

Does your ideal UX lean more toward “every `/go` task must have a `donewhen` and `/go` always runs verify,” with `/verify` reserved for ad‑hoc checks, or would you rather keep verification optional per task and rely on `/verify` only when you explicitly ask for it?  

## Human

to many words in your question.  so we need verify in go and as a separate skill.  what's the optimal implementation?

## Assistant

Optimal implementation: **make `/go` the mandatory verifier of completion, and make `/verify` a reusable verification engine + ad‑hoc entrypoint that `/go` calls internally**. That gives you one verification core, two surfaces, and zero duplicated logic.[1][2]

## Architecture

Use a **single verification runtime** with two callers:

- `/go` uses it automatically before any completion token, because `go` already has `donewhen`, phase ledgers, stop gates, and `GoVerificationResult` semantics.[2][1]
- `/verify` calls the same runtime directly for ad‑hoc checks, pre‑commit/pre‑PR use, or validating work done outside a `go` task.[3][1]

That means:
- One artifact schema: `GoVerificationResult`.[1][2]
- One command planner/executor/parser.
- One gate policy for pass/fail/blocked/waived.
- Two UX surfaces only.

## Best design

Model it as a layered system:

1. **Verification core**  
   Pure engine that accepts:
   - target/scope
   - verification profile
   - commands
   - expected outputs / parsers
   - task metadata (`runid`, `taskid`, `terminalid`, optional)[2][1]

   Returns:
   - normalized `GoVerificationResult`
   - artifact paths
   - plain‑English summary[1][2]

2. **`/go` integration layer**  
   `/go` must:
   - require `donewhen` for implementation/refactor tasks
   - invoke verification core before any `promisePRREADY`
   - fail closed on missing or red verification for changed surface[2][1]

3. **`/verify` entry layer**  
   `/verify` should:
   - infer verification profile from change type: CLI, API, refactor, routing, migration
   - run without full plan orchestration
   - optionally attach to an existing `go` run if `--runid` is supplied[3][1]

## Command behavior

I’d implement these surfaces:

| Surface | Purpose | Required? |
|---|---|---|
| `/go` | Execute SDLC task and verify completion before success | Yes for implementation/refactor flows. [1][2] |
| `/verify` | Run verification directly on a target/change | Yes as explicit tool. [1][3] |
| shared `verify_runner` | Internal engine used by both | Yes. |

Suggested CLI shape:

- `cc go ...`
- `cc verify <target>`
- `cc verify <target> --profile cli|api|refactor|routing|mixed`
- `cc verify <target> --runid <id>`
- `cc verify <target> --command "pytest tests/test_auth.py"`
- `cc verify <target> --json`

Use `/go` for task completion; use `/verify` for spot checks, preflight, and manual validation. That separation matches the packs: `go` is orchestration, `verify` is evidence gathering.[3][1]

## Policy rules

Make these rules hard, not advisory:

- **Rule 1:** `/go` cannot mark implementation or refactor tasks done without verification evidence.[1][2]
- **Rule 2:** `/verify` writes the same result schema as `/go` uses.[2][1]
- **Rule 3:** no separate pass/fail logic in `/go`; it consumes the core verifier result only.  
- **Rule 4:** scoped reporting only, never “all green” if only a subset was run. This is explicitly required by the `go` pack.[1][2]
- **Rule 5:** capability claims need capability audit when commands/routing/backends changed.[2][1]

## Implementation details

Minimal implementation plan:

- **Extract or formalize** a `verify_runner` module around the existing verification artifact flow and `GoVerificationResult` schema.[1][2]
- **Have `/go` always call** `verify_runner` after execution and before completion token emission.[2][1]
- **Add `/verify` wrapper** that builds a synthetic task context when no `runid` exists, then calls the same runner.  
- **Support profiles**:
  - `cli`: flags, stdout/stderr, JSON validity, exit codes.[3]
  - `api`: headers, payload fields, status codes, changed-path exercise.[3]
  - `refactor`: targeted tests, regression suite, optional mutation, dead-surface checks.[4][2]
  - `routing`: backend existence, visible surface reduction, routing completeness.[1][2]

Best storage model:
- If called from `/go`, write under `GOSTATEDIR`.
- If called standalone, write under a compatible standalone state dir, but still emit the same schema so `/go` or other tooling can consume it later.[2][1]

## Recommendation

**FACT:** the packs already make verification integral to `/go`, with `donewhen`, stop gates, continuation gates, and `GoVerificationResult` artifacts.[1][2]
**CONSENSUS:** the cleanest design is one verifier engine with two entrypoints, not two separate verification implementations.  
**SPECULATION, high confidence:** if you split logic between `/go` verification and `/verify` verification, drift will appear fast—in pass criteria, output shape, and completion semantics.

Concrete next step:
- implement `verify_runner.run(context) -> GoVerificationResult`
- refactor `/go` to consume it
- add thin `/verify` wrapper over the same function

Shortest UX:
- `/go` = do work + verify
- `/verify` = just verify

## Human

again too many words.  give me a prompt to pass to the implementing LLM to make the best verify.

## Assistant

Design and implement a **single verification core** that is used both by the `/go` orchestrator and by an explicit `/verify` command.

### Goals

- Evidence‑first: no “done” or “fixed” claims without verification.
- One verification engine, two entrypoints (`go` and `verify`), no duplicated logic.
- Structured artifacts (`GoVerificationResult`‑style) with clear pass/fail/blocked semantics.
- Support profiles: CLI, API, refactor, routing, mixed.

***

### Prompt for the implementing LLM

You are implementing the verification system for a Claude‑Code‑style CLI.

**High‑level requirement**

Create a **verification subsystem** with:

1. A core module (library) that runs verification commands, parses their results, and emits a structured verification artifact.
2. Integration into the `/go` orchestrator so every implementation/refactor task is verified before being marked complete.
3. A standalone `/verify` CLI command that reuses the same core module for ad‑hoc verification.

***

**Core verification module**

Implement a module (e.g. `verify_runner`) with a single main API:

- Input:
  - `target`: path, service name, or logical component being verified.
  - `profile`: one of `cli`, `api`, `refactor`, `routing`, `mixed`.
  - `commands`: list of shell commands to run for verification (tests, probes, linters, mutation runs, etc.).
  - `context`:
    - `runid` (optional, for orchestrated tasks),
    - `taskid` (optional),
    - `terminalid` (optional),
    - paths for state/artifacts.
- Behavior:
  - Executes commands in order.
  - Captures `exitcode`, `stdout`, `stderr` for each.
  - Applies profile‑specific checks:
    - CLI: flag wiring, JSON validity, status changes.
    - API: headers/fields present and valid, changed code path exercised.
    - Refactor: RED/GREEN/REGRESSION tests, optional mutation testing, regression detection.
    - Routing: backend existence, visible surface reduction, routing completeness.
  - Aggregates results into a single structured verification artifact.
- Output:
  - `VerificationResult` object with fields such as:
    - `runid`, `taskid`, `terminalid`
    - `status`: `passed`, `failed`, `blocked`, `waived`, `pending`
    - `prready`: boolean
    - `verificationCommands`: list of `{command, exitcode, passed}`
    - `phaseState`: `green`, `red`, `refactor`, `none`
    - optional blocks:
      - `tdd`: test receipts / suite summary
      - `mutation`: mutation score, killed/survived counts
      - `capabilityAudit`: verified/overclaim/deferred/notchecked for command/routing changes
    - `findingsSummary`: short human‑readable summary.

Make this module **pure** (no CLI parsing inside, no `/go` semantics) so both `go` and `verify` can call it.

***

**Integration into `/go`**

Modify `/go` so:

- Every implementation/refactor task must provide a `donewhen` command: a concrete shell command that proves completion (e.g. `pytest tests/test_auth.py`).
- When `/go` finishes the implementation part of a task, it:
  1. Assembles a verification profile from the task type and metadata:
     - implementation/refactor → `refactor`
     - CLI changes → `cli`
     - API changes → `api`
     - routing/capability consolidation → `routing`
  2. Calls `verify_runner.run(...)` with:
     - `target` (task’s target path or service),
     - selected `profile`,
     - `commands` list including at least `donewhen` and any extra configured verification commands.
- Based on the returned `VerificationResult`:
  - If `status != "passed"`:
    - do **not** emit any completion tokens like `PRREADY`, `Fixed.Done.Verified`.
    - mark the task as `blocked` or `failed` and attach the verification artifact.
  - If `status == "passed"`:
    - emit completion tokens as usual,
    - attach the artifact as the evidence ledger for that task.

Enforce:

- `/go` **cannot** mark implementation or refactor tasks complete without a successful `VerificationResult`.
- `/go` must do **scoped reporting**: never claim “all tests green” if only a subset was run; mention which suites ran and which remain failing or unrun.

***

**Standalone `/verify` command**

Implement a `cc verify` CLI that wraps the same `verify_runner`:

- Syntax examples:
  - `cc verify <target>`
  - `cc verify <target> --profile cli|api|refactor|routing|mixed`
  - `cc verify <target> --command "pytest tests/test_auth.py"`
  - `cc verify <target> --runid <id>` (attach to an existing `go` task if present)
- Behavior:
  1. Parse arguments and construct:
     - `target`
     - `profile` (default based on flags or file type: CLI, API, etc.)
     - `commands` list (from `--command`, profile defaults, or config).
  2. Call `verify_runner.run(...)`.
  3. Print:
     - high‑level status (`PASSED` / `FAILED` / `BLOCKED` / `WAIVED`)
     - list of commands and pass/fail per command
     - any key findings (e.g. missing header, invalid JSON, failing tests, surviving mutations)
  4. Write the same structured verification artifact to disk, in a location compatible with `/go`’s state/ledger layout.

This command is for:

- pre‑commit / pre‑PR verification,
- ad‑hoc checking of a CLI or API change,
- manual verification when you’re not using `/go` to orchestrate the task.

***

**Policy and safety**

Encode these rules:

- No **“probably”, “should”, or “seems fine”** in automated output. Only concrete verification facts (commands run, exit codes, parsed results).
- No global “green” claims: always scope the claim to the exact suites or checks that were executed.
- Capability changes (commands, routing) must include capability audit and over‑claim detection.
- Treat `waived` as an explicit state with rationale, not as `passed`.

***

**Deliverables**

- Library module: `verify_runner` (or equivalent) implementing the verification core.
- Data structure: `VerificationResult` (JSON‑serializable).
- `/go` integration changes:
  - mandatory `donewhen` for relevant tasks,
  - call into verification core,
  - completion gating based on `VerificationResult`.
- New CLI command: `cc verify` that reuses the same core and emits human‑readable plus JSON output.

Focus on **deterministic verification**, clear result structure, and minimal duplication between `go` and `verify`.

## Human

Can you create a short description of the evolve package and what we should do with it?

## Assistant

**Short description**

`evolve` is a Claude Code modernization package that turns a working but messy codebase into a high‑standard, Python‑2025‑compliant system using a strict four‑phase workflow: AUDIT, STRATEGY, EXECUTE, and HARDEN.[1]

**What we should do with it**

Use `evolve` as the **mission control** for technical‑debt work:

- Run it whenever you want to **modernize** or **refactor** code, not just fix a single bug.[1]
- Let Phase 1 (AUDIT) map complexity, performance, and debt before you change anything.[1]
- Use Phase 2 (STRATEGY) to design the refactor or migration, validate patterns, and draft an ADR.[1]
- Use Phase 3 (EXECUTE) to drive safe, checkpointed, multi‑file refactors and dead‑code purges.[1]
- Use Phase 4 (HARDEN) to verify tests, performance, and standards, then update the project constitution/CKS so the improvements become part of the official norms.[1]

In practice: **route any “modernize / clean up / refactor this” request through `evolve` instead of ad‑hoc editing**, and make it the default entrypoint for planned debt sprints and pre‑release hardening.[1]
