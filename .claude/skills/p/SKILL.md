---
name: p
version: 2.5.0
status: stable
agent: general-purpose
user-invocable: true
description: "Code Maturation Pipeline with ToT enhancement - auto-detects state and runs appropriate quality gates with branching scenario analysis. v2.5.0: Added model selection guidance for subagent phases (P2/P4/P5 require sonnet for reasoning). Added debug logging for fast-path activation detection (aids troubleshooting). v2.4.0: CRITICAL FIX - Added session-local state tracking to prevent trusting stale chat context (pre-tests RISK:9 failure mode)."
category: execution
triggers:
  - /p
  - "promote"
  - "mature"
aliases:
  - /p

suggest:
  - /p --quick
  - /p --publish
  - /p --dry-run

execution_hint: "Run inline as orchestrator. Dispatch each phase as an Agent subagent. Show phase start marker before dispatch, completion marker after. Never summarize or fabricate — every result must come from actual tool output. NOTE: Skill-first gate is OPTIONAL (SKILL_FIRST_MODE=off by default - no need to call Skill('p') first unless gate is enabled)."

hooks:
  PreToolUse:
    - matcher: "tool == 'Skill'"
      hooks:
        - type: command
          command: "python \"$CLAUDE_PROJECT_DIR/.claude/skills/p/hooks/validate_p_phase_order.py\""
          timeout: 5
  Stop:
    - matcher: ".*"
      hooks:
        - type: command
          command: "python \"$CLAUDE_PROJECT_DIR/.claude/skills/p/hooks/StopHook_p_halt_format_validator.py\""
          timeout: 5
        - type: command
          command: "python \"$CLAUDE_PROJECT_DIR/.claude/skills/p/hooks/StopHook_p_completion_validator.py\""
          timeout: 5
---

# /p - Code Maturation Pipeline Orchestrator

## Purpose

Intelligent orchestrator that automatically detects codebase state and runs appropriate quality gates. No flags required for normal workflow.

**Core principle:** The system figures out what to do -- you don't remember flags.

**This is a PROCEDURE-type skill** -- Claude reads this SKILL.md and executes the workflow manually. It does NOT delegate to an external CLI tool.

## Quick Reference

```
/p                    # Auto-detect and run what's needed
/p cleanup            # Target a skill directory (all files)
/p .claude/hooks/     # Explicit path target
/p --quick            # Only files from current session
/p --publish          # Halt on warnings
/p --phase=N          # Run specific phase (0-6)
/p --dry-run          # Preview without executing
/p --fix              # Auto-fix safe issues in P3
/p --fix-all          # Iterative fixing loop
/p --auto-fix         # Per-phase HALT-and-retry (ON by default)
/p --focus security   # Focus lens for review
/p --reverse          # Gap analysis (read-only)
/p --evidence <path>  # Write JSON evidence
/p --force            # Bypass validation (EMERGENCY ONLY)
```

See `references/flags-reference.md` for full flag documentation.

## Detection Table

| Priority | Signal | Phase | Rationale |
|----------|--------|-------|-----------|
| 1 | No pyproject.toml AND no SKILL.md AND no src/ AND no tests/ | P0 (Scaffold) | Truly empty project |
| **2** | **Test Status** (applies to ALL targets) | | |
| 2a | Tests failing or missing | P1 (Build) | Can't review broken code |
| 2b | Tests pass, never reviewed | P2 (Review) | Find problems before validating |
| 2c | Tests pass, files changed since review | P2 (Review) | Re-review after changes |
| 2d | Reviewed, never validated | P3 (Validate) | Prove it works |
| 2e | Validated, no README | P4 (Publish) | Make presentable |
| 2f | Published, never certified | P5 (Certify) | Final QA certification |
| 2g | Certified, never security scan | P6 (Security) | Security gate |
| 2h | Security scan passed | /portfolio | Add to portfolio |
| 2i | Everything complete, no changes | Report "Ready" | Nothing to do |
| **3** | **Project Type** (only if test status unclear) | | |
| 3a | SKILL.md in root, no pyproject.toml, scaffold incomplete | P0-Skill | Pure skill validation |
| 3b | Has pyproject.toml + skill/SKILL.md | Package + skill metadata check | Dual-nature |
| 3c | Has pyproject.toml / package.json / go.mod | Package pipeline (P1-P6) | Python/Node/Go package |
| 3d | None of the above | P0 (Scaffold) | Unknown project type |

See `references/detection-logic.md` for full scope inference and state detection details.

## Adaptive Depth

| Context | Depth | What Runs |
|---------|-------|-----------|
| Local iteration (uncommitted changes, failing tests) | Light | Fix tests, basic lint |
| Clean local state | Standard | Tests + review + validation |
| Release branch | Full | Everything including E2E, portfolio |

## Semantic Checks Decomposition

`/p` orchestrates semantic checks only through `/p*` phases. It does not invoke `/q`, `/r`, or `/s`.

| Function | Owner Phase | Enforcement |
|----------|-------------|-------------|
| API auth/csrf/rate-limit intent checks | `/p --phase=2` | Findings + fix loop |
| DB FK-index relevance, ETL backfill intent | `/p --phase=2` | Findings + fix loop |
| Migration rollback parity, DAG timeout defaults | `/p --phase=3` | Validation gate (blocking/warn) |
| Env default safety, license-header context | `/p --phase=3` | Validation gate (warn; blocking with `--publish`) |
| Cloud/deploy metadata alignment | `/p --phase=4` | Publish readiness gate |
| Residual semantic risk certification | `/p --phase=5` | Certification verdict |

## HALT Rules

**/p HALTS when a phase encounters blocking errors.**

| Phase | HALT If... | Rationale |
|-------|-----------|-----------|
| P1 (Build) | Tests fail after TDD loop | Can't review broken code |
| P2 (Review) | CRITICAL/HIGH findings remain | Must fix before validation |
| P3 (Validate) | Blocking stage fails OR (with --publish: any warning) | Unsafe to proceed |
| P4 (Publish) | N/A | Documentation generation |
| P5 (Certify) | N/A | Final phase |

**On HALT:**
1. Report the phase and specific error/findings
2. Provide next action (e.g., `/tdd Fix <finding-id>`)
3. Do NOT proceed to next phase until current phase passes
4. User re-invokes `/p` to continue after fixes

**With --publish flag:** P3 treats non-blocking warnings as blocking (halts on any warning).

## Your Workflow

When `/p` is invoked:

### Step 0: Scope Inference (Chat-Context First)

Infer scope from: (1) explicit argument, (2) chat context last 10 turns, (3) session ledger, (4) ask user. See `references/detection-logic.md` for full inference logic.

### Step 1: Detect Current State (PARALLEL)

Launch 2 parallel Agent subagents (`subagent_type="general-purpose"`, `model="haiku"`):
- **Subagent 1:** Test detection (pytest --collect-only, pytest --version)
- **Subagent 2:** File & marker detection (README, LICENSE, pyproject.toml, SKILL.md)

**Fast path:** If chat context is fresh (tests run this session, no edits after), skip detection and use context directly. See `references/session-state-tracking.md` for state management.

**Agent tool parameters:** See `references/agent-tool-reference.md` for correct parameter usage. **Never use `subagent_type="haiku"`** -- haiku is a model, not an agent type.

### Step 2: Determine Next Action

Use the Detection Table above. Check priorities in order: (1) empty project, (2) test status, (3) project type. See `references/detection-logic.md` for full priority system.

### Step 3: Emit Phase Boundary Markers

Before each phase: `[P{N}] Starting {Phase Name}...`
After each phase: `[P{N}] Complete: {Phase Name} -- {1-line summary}`

### Step 4: Dispatch Phase Subagent

Read the phase file and dispatch as Agent subagent:
- Phase 0-6 -> `P:/.claude/skills/p/phases/p{N}.md`
- `--phase=N` flag: Read `phases/pN.md` directly (skip detection)

Dispatch with scope, flags, and "End your response with the PHASE_RESULT block" instruction.

Parse last 20 lines for `PHASE_RESULT:`. If not found, treat as HALT.

### Step 4.5: Validate Exit Criteria (MANDATORY)

After EVERY phase (P1-P5), run actual verification commands BEFORE trusting PHASE_RESULT. This prevents phases incorrectly reporting PASS.

See `references/exit-criteria-validation.md` for validation functions and integration.

**Bypass:** Use `--force` flag (EMERGENCY ONLY).

### Step 5: Check for Blocking Errors

After phase execution, check HALT conditions. If HALT:
- If `--auto-fix` enabled (default): Attempt Layer 1 fix (imports, style) then Layer 2 (LLM + context), retry up to 3 times
- If disabled: Wait for user to fix and re-invoke `/p`

See `references/next-steps-logic.md` for dual-nature validation and completion detection.

### Step 5.5: Dual-Nature Skill Metadata Validation

After P2 only, if target has both `pyproject.toml` AND `skill/SKILL.md`, run non-blocking skill metadata validation. See `references/next-steps-logic.md`.

### Step 5.75: Check for Completion

Before showing Next Steps, check if work is actually complete. See `references/next-steps-logic.md`.

### Step 6: Report What's Next

Emit pipeline summary with phase progress and context-aware next steps. See `references/output-formats.md` for HALT and COMPLETE formats. See `references/next-steps-template.md` for the domain-organized next steps pattern.

## The Full Pipeline

```
/p (Intelligent)
  +---> Detects: "No project structure"  -> Runs P0 (Scaffold)
  +---> Detects: "No tests"             -> Runs P1 (Build)
  +---> Detects: "Tests pass"           -> Runs P2 (Review)
  +---> Detects: "Reviewed"             -> Runs P3 (Validate)
  +---> Detects: "Validated"            -> Runs P4 (Publish)
  +---> Detects: "Certified"            -> Runs P5 (Certify)
  +---> Detects: "Regression"           -> Demotes and re-runs appropriate phase
  +---> Detects: "Complete"             -> Reports "Ready"
```

## Phase Prerequisites

| Phase | Prerequisite |
|-------|-------------|
| P0 (Scaffold) | None (entry point) |
| P1-P5 | Hook-based enforcement prevents skipping phases |
| P6 (Security) | No prerequisite (optional final gate) |

## Focus Lenses

Apply via `--focus <lens>` to emphasize specific concerns during P2/P3.

| Lens | P2 Effect | P3 Effect |
|------|-----------|-----------|
| `risk` | Pre-mortem failure analysis | Report failure modes |
| `gaps` | Completeness check | Check requirements coverage |
| `security` | Prioritize security findings | Prioritize security stages |
| `complexity` | Flag high-CC functions | Lower CC threshold |
| `duplicates` | Run duplicate detection | Prioritize duplication stage |
| `quality` | Emphasize quality agent | Prioritize quality stages |
| `performance` | Prioritize performance findings | Run with profiling awareness |
| `architecture` | Add architectural perspective | Add cross-module check |
| `test` | Focus on test quality | Prioritize test stages |
| `library` | Add dependency analysis | Prioritize CVE stages |
| `comprehensive` | ALL lenses | All stages elevated to blocking |

## --auto-fix (Per-Phase HALT-and-Retry)

**ON by default.** When a phase HALTs, auto-fix attempts resolution:

| Layer | Confidence | Fix Type | Guardrails |
|-------|------------|----------|------------|
| Layer 1 | HIGH | Imports, style, pyupgrade | No guardrails needed |
| Layer 2 | MEDIUM | LLM with findings + context | "Don't break functionality" |
| Layer 3 | LOW | Final LLM attempt | Full characterization + git safety net |

Retry loop: max 3 attempts per phase. `git restore` available as safety net.

See `references/flags-reference.md` for full flag details including --fix, --fix-all, --reverse, --dry-run, --force.

## Shell Compatibility (Windows)

| Tool | Use For |
|------|---------|
| Bash tool | Unix-style commands (pytest, git, grep, ls) |
| pwsh skill | PowerShell cmdlets (Select-String, Get-ChildItem) |

Match command syntax to tool. Never mix PowerShell cmdlets with Bash tool.

## What This Does NOT Do

- Does NOT require flags for normal workflow
- Does NOT run everything every time -- only what's needed
- Does NOT skip gates -- each phase must pass before advancing
- Does NOT continue past blocking errors -- HALTS on critical issues
- Does NOT replace manual phase invocation -- use `/p --phase=N` for specific phases

## Reference Files

| File | Contents |
|------|----------|
| `references/detection-logic.md` | Scope inference, state detection, priority system |
| `references/session-state-tracking.md` | Fast-path state management, staleness detection |
| `references/agent-tool-reference.md` | Agent tool parameters, common mistakes |
| `references/exit-criteria-validation.md` | Step 4.5 validation functions |
| `references/next-steps-logic.md` | Completion detection, dual-nature validation, context-aware options |
| `references/next-steps-template.md` | Domain-organized next steps pattern |
| `references/output-formats.md` | HALT, COMPLETE, and phase boundary marker formats |
| `references/flags-reference.md` | Full flag documentation (--fix, --fix-all, --reverse, --dry-run, --force, --focus) |
| `references/example-sessions.md` | Example session transcripts (P1-P5 success and HALT) |
| `references/tot-integration.md` | Tree-of-Thought branching scenarios |

## Python Regex Best Practices

When writing regex patterns with character classes containing quotes, match the outer delimiter:
- Pattern has `"` inside: use `r'...'` (single-quoted raw string)
- Pattern has `'` inside: use `r"..."` (double-quoted raw string)
- Always compile with `re.compile()` to catch syntax errors early.

## Code Editing Patterns

For Python code editing patterns and anti-patterns, query CKS:
- `/search "ThreadPoolExecutor KeyboardInterrupt immediate cleanup"`
- `/search "string manipulation AST LibCST code editing"`

Reflect automatically propagates code editing learnings to /p.
