---
title: "how can we solve for these types of problems in claude code cli?

'
❯ I'm not talking about state or evidence paths. I'"
date: "2026-03-27"
mode: "COPILOT"
uuid: "de5c8deb-efab-421a-9797-9592d023f496"
entry_count: 3
---

## Human

how can we solve for these types of problems in claude code cli?

"
❯ I'm not talking about state or evidence paths. I'm talking about the problems we
have with not implementing ADRs or plans properly.  How can we make the initial
implementation of the ADR OR plan more accurate? And then how can we also make sure we
 catch deviations more reliably so that we can then fix them?

● Ah — ADR/plan implementation drift. Let me think through this:

  Problem 1: Initial implementation accuracy

  The gap is typically that specs get written, accepted, then implemented without
  verification that implementation actually satisfies the acceptance criteria.

  Options:
  1. Formal verification gate before "Accepted" status — ADR stays pending until
  implementation is verified against criteria (not just written)
  2. Spec-linked regression tests — Acceptance criteria become automated tests that run
   post-implementation
  3. TDD against acceptance criteria — RED phase writes tests that match acceptance
  criteria before implementation starts

  Problem 2: Deviation detection

  Currently deviations are caught ad-hoc (adversarial review, manual audit) rather than
   systematically.

  Options:
  1. Periodic re-verification — Cron job that re-runs /verify against implemented ADRs
  2. Implementation audit trail — Each code change cites which ADR it implements; hooks
   detect uncited changes
  3. Diff-time ADR validation — When git diff shows changes to ADR-implemented files,
  prompt to verify ADR still matches

  The core issue: Plans/ADRs describe intent but don't structurally link to
  implementation. There's no mechanism that says "this line of code = this acceptance
  criterion."

  A structural fix would be: acceptance criteria in ADR have corresponding test
  functions that verify them. When tests pass, implementation is verified.
"

## Assistant

You can hard‑wire better ADR/plan implementation fidelity and drift detection into a **Claude Code CLI workflow** by treating ADRs as *spec‑to‑test* artifacts that are mechanically linked to the codebase and enforced via hooks + tooling.[1][2][3]

Below is a concrete, actionable pattern you can plug into your current setup (Git, test framework, and Claude Code CLI).

***

### 1. Make the initial ADR implementation accurate

Goal: minimize the gap between “approved ADR” and “working, verified code.”

#### A. ADR structure with testable acceptance criteria  
Keep ADRs in‑repo (e.g., `docs/adr/0001‑foo.md`) and enforce a schema like:

```markdown
## Decision
...

## Acceptance criteria
- AC1: [short, testable statement]
- AC2: ...
```

Each criterion must be machine‑readable enough to turn into a test name or scenario.[4][3]

Then define a **CLI / Claude command** that turns an ADR into a test stub:

```bash
/adr_to_tests 0001
```

Claude Code CLI:
- Parses `docs/adr/0001‑foo.md`.
- Generates a test file (e.g., `tests/adr/0001_foo_spec.py`) with skeleton tests for each AC (failing by default).
- Adds a lightweight schema to map `AC1 → test_foo_ac1()`.

This implements your “TDD against acceptance criteria” idea: every ADR effectively ships with a failing test suite.[1][4]

#### B. Gate ADR “Acceptance” with verification  
Add a linter / CLI step:

```bash
/verify_adr 0001
```

This tool:
- Finds the ADR file.
- Checks that:
  - A test file exists for that ADR.
  - All ACs either have a corresponding test or are explicitly marked as `#TODO` / `#OMIT`.
- Fails if any AC is missing a test.

Then integrate this into your flow:
- PR description points to ADR.
- Your CI and/or Claude‑driven pre‑commit checks `/verify_adr <id>` as a gate between “design” and “implementation.”[5][6]

This enforces your “formal verification gate before Accepted status”: ADR doesn’t move to “implemented” unless the tests exist and (at least) most ACs are covered.[3][1]

***

### 2. Catch deviations more reliably

Goal: automatically detect when the implementation drifts from the ADR and when new code is added without ADR linkage.

#### A. Link every change to an ADR (or “no‑ADR” escape hatch)  
Use **commit‑level hooks**:

1. Enforce ADR‑tagging in commit messages:
   - E.g., `git commit -m "feat: add foo\nADR-0001"`  
   - Pre‑commit hook that checks `git log -1 --pretty=%B` for a pattern like `ADR-\d+`.[6][5]

2. In your Claude Code CLI session:
   - When editing a file covered by ADR‑linked tests, Claude is prompted:
     - “You are modifying files governed by ADR‑0001. Please ensure acceptance criteria AC1–AC3 are still satisfied.”
   - You can codify this as a **project rule** in `.cursor` or `.claude/rules` that warns if a file is changed without a referenced ADR.[7][1]

#### B. Periodic re‑verification and drift‑guard  
Implement:

```bash
/verify_all_adrs
```

This CLI:
- Walks all ADRs in `docs/adr/`.
- For each:
  - Runs its corresponding test file.
  - Reports:
    - passes (implementation still matches ACs).
    - fails (implementation no longer matches = “ADR drift”).
- Optionally, also diffs the ADR content vs. code annotations (e.g., `# ADR-0001 AC1`) to catch “schema‑level” drift.[8][9]

Set this as:
- A nightly cron or CI job.
- A manual step run before major releases.

This realizes your “periodic re‑verification” and “implementation audit trail” ideas.[8][3]

#### C. Diff‑time ADR validation (hook + Claude)  
Use a **pre‑push / PR‑generation hook** that:

1. Detects which ADR‑governed files changed:
   - E.g., changes in `src/foo/` tracked as belonging to ADR‑0001.[5]
2. Triggers:
   - Run `pytest tests/adr/0001_*` (or equivalent).
   - If tests fail, either:
     - Block the push (strict version), or
     - Generate a PR comment:  
       > “This change affects ADR‑0001. The following ACs no longer pass: AC1, AC3. Please update tests or the ADR.”

In your Claude Code CLI, you can then run:

```bash
/adr_analyze_diff
```

Which:
- Reads the staged changes.
- Summarizes which ADRs are affected.
- Suggests which ACs need to be revisited or which tests are now failing.

This implements your “diff‑time ADR validation” pattern.[2][8]

***

### 3. Structural “this line of code = this AC” mapping

You noted the core issue: no structural link between code and ACs. Fix this incrementally:

#### A. Annotation‑based linking  
Require that critical functions are annotated:

```python
# ADR-0001 AC3
def foo_handler(request):
    ...
```

Or, in strongly typed code:

```python
@adr("0001", "AC3")
def foo_handler(request):
    ...
```

Then:
- ADR‑to‑test tooling can:
  - Parse these annotations.
  - Ensure that each AC has at least one function or test path tagged.
- A drift‑detector tool can:
  - Compare `ADR‑0001`’s AC list → set of tagged functions.
  - Warn if ACs are present but no corresponding tag, or vice versa.

This gives you the “this line of code = this acceptance criterion” property you wanted.[3][8]

#### B. Cross‑check with coverage  
In CI:

- Run coverage on ADR‑specific tests.
- Fail if a critical ADR‑related module is not covered by at least one ADR‑linked test.

You can even expose this to Claude via:

```bash
/adr_coverage_report
```

Which emits JSON‑ish structure that Claude can reason about in subsequent sessions.

***

### 4. How to plug this into Claude Code CLI today

Assume you already have:
- In‑repo ADRs under `docs/adr/`.
- A test framework (pytest, Jest, etc.).
- Git hooks (local or via `pre-commit`).

Steps:

1. **Define a minimal ADR schema** with `Acceptance criteria` and `Status` fields.[2][3]
2. **Add CLI commands**:
   - `/adr_to_tests <id>` → generate skeleton tests.
   - `/verify_adr <id>`, `/verify_all_adrs` → check AC ↔ test linkage.
3. **Add a commit‑lint hook** that demands `ADR-XXX` in the commit if touching ADR‑governed files.[6][5]
4. **Add rules** in `.claude/rules` or `.cursor/rules` that:
   - Remind Claude to reference ADRs when editing those files.
   - Prompt to run `/verify_adr` after a PR‑like change.
5. **Integrate a nightly `/verify_all_adrs` job** (CI or cron) that surfaces ADR drift.[9][8]


***

If you tell me your stack (Python/TS/Go, repo layout, and whether you use `.cursor` vs bare Claude Code CLI), I can give you concrete rule templates and CLI implementations for your exact setup.

## Human

Does this seem resonable?  Any gaps or opportunities?
"
● Yes, exactly. The long-term fix requires modifying /planning and /code to generate
  the correct artifacts at the right time in the workflow.

  Here's the minimal set:

  /planning changes

  What it creates today: A plan markdown with checklist items

  What it should also create: An ADR test file stub when an ADR is accepted

  Files to modify:
  - P:/.claude/skills/planning/SKILL.md — add a step after "accept ADR" that runs
  /adr_to_tests <id>
  - P:/.claude/skills/planning/scripts/plan_builder.py (or wherever plans are
  generated) — emit the test stub file alongside the plan

  The ADR already has acceptance criteria (AC) in prose. The skill should parse those
  ACs and generate tests/adr/ADR_<id>_<name>.py with test_<ac_name>() skeleton
  functions that fail until implemented.

  /code changes

  What it does today: Implements plan tasks, runs quality checks

  What it should also do: Annotate code with ADR linkage, ensure ADR tests pass

  Files to modify:
  - P:/.claude/skills/code/SKILL.md — add ADR coverage verification to the AUDIT phase
  (after tests pass, verify ADR ACs are still satisfied)
  - P:/.claude/skills/code/utils/ — add ADR annotation helpers (or a new
  utils/adr_linker.py)

  This means when /code completes a task that touches ADR-governed files, it runs the
  corresponding ADR tests as part of the AUDIT step.

  /verify changes

  What it does today: 4-tier verification of skills/hooks/features

  What it should also do: Run verify_adr <id> and verify_all_adrs

  Files to modify:
  - P:/.claude/skills/verify/SKILL.md — add verify adr:<id> trigger
  - P:/.claude/skills/verify/tiers/ — add ADR verification tier (or extend
  tier1_component.py to discover ADR tests)

  New supporting files

  - P:/__csf/scripts/adr_to_tests.py — parses ADR markdown, emits pytest skeleton
  - P:/__csf/scripts/verify_adr.py — checks AC-to-test linkage
  - P:/__csf/scripts/verify_all_adrs.py — walks all ADRs, runs corresponding tests
  - A hook PostToolUse_adr_deviation_check.py that runs ADR tests when ADR-governed
  files change

  Bottom line

  ┌─────────────┬─────────────────────────────────────────────────────┐
  │    Skill    │                    What it owns                     │
  ├─────────────┼─────────────────────────────────────────────────────┤
  │ /planning   │ ADR → test stub generation at acceptance time       │
  ├─────────────┼─────────────────────────────────────────────────────┤
  │ /code       │ ADR annotation enforcement + ADR test pass in AUDIT │
  ├─────────────┼─────────────────────────────────────────────────────┤
  │ /verify     │ verify adr:<id> for on-demand checking              │
  ├─────────────┼─────────────────────────────────────────────────────┤
  │ New scripts │ adr_to_tests, verify_adr, verify_all_adrs           │
  ├─────────────┼─────────────────────────────────────────────────────┤
  │ New hook    │ deviation detection on file changes                 │
  └─────────────┴─────────────────────────────────────────────────────┘

  The core insight from that guide is right: the ADR acceptance criteria must become
  failing tests at the moment the ADR is accepted, not retroactively when someone
  remembers to write them. That's what closes the gap between "ADR says X" and
  "implementation actually does X."

  Want me to implement this? I'd start with the adr_to_tests script + the /planning
  integration, then wire in the /code AUDIT step.

✻ Crunched for 35s

❯ /critique

● Skill(critique)
  ⎿  Successfully loaded skill

● Bash(python -c "
      from pathlib import Path…)
  ⎿  P:\\.claude\\.evidence\\critique\\critique-20260327_110359

  Read 2 files (ctrl+o to expand)

● The work is a plan — an architectural design proposal for an ADR verification system.
   I'll dispatch two specialists for Phase 1: adversarial-critic (reasoning quality,
  feasibility) and adversarial-compliance (completeness, alignment with existing
  patterns).

● Bash(mkdir -p "P:/.claude/.evidence/critique/critique-20260327_110359/specialists")
  ⎿  PreToolUse:Bash hook returned blocking   ⎿  🚫 ROOT WRITE BLOCKED: specialists
      error
                                                 Slash command? →
                                                 P:/.claude/skills/{filename}
                                                 Framework code? →
                                                 P:/__csf/src/[feature]/{filename}
                                                 Project file? →
                                                 P:/projects/[name]/{filename}
                                                 Staging/temp? →
                                                 P:/__csf/.staging/{filename}

                                                 💡 Keep features self-contained with
                                                 their configs
                                                 ⚠️  Scan session: Other misplaced
                                                 files?

                                                 ===HOOK_CORRECTION===
                                                 BLOCKED: P:/.claude/.evidence/critique
                                                 /critique-20260327_110359/specialists
                                                 USE_INSTEAD:
                                                 P:/__csf/.staging/specialists
                                                 ACTION: Retry write operation with
                                                 USE_INSTEAD path. Do NOT retry with
                                                 BLOCKED path.
                                                 ===END_CORRECTION===
  ⎿  Error: 🚫 ROOT WRITE BLOCKED: specialists

     Slash command? → P:/.claude/skills/{filename}
     Framework code? → P:/__csf/src/[feature]/{filename}
     Project file? → P:/projects/[name]/{filename}
     Staging/temp? → P:/__csf/.staging/{filename}

     💡 Keep features self-contained with their configs
     ⚠️  Scan session: Other misplaced files?

     … +5 lines (ctrl+o to see all)

● Write(P:/__csf/.staging/critique-20260327_110359_p1_findings.md)
  ⎿  Wrote 64 lines to
     ..\\..\\__csf\\.staging\\critique-20260327_110359_p1_findings.md
       1 ## Triage Classification
       2
       3 **plan** — Architectural design proposal for ADR verification system sp
         anning /planning, /code, /verify modifications plus new scripts and a h
         ook.
       4
       5 ## Dispatched Specialists
       6
       7 - **adversarial-critic**: Reasoning quality, feasibility, implementatio
         n completeness
       8 - **adversarial-compliance**: Schema alignment, spec completeness, arch
         itectural pattern compliance
       9
      10 ## Specialist Findings Summary
     … +54 lines (ctrl+o to expand)

  Read 2 files (ctrl+o to expand)

● Write(P:/__csf/.staging/critique-20260327_110359_p2.md)
  ⎿  Wrote 41 lines to ..\\..\\__csf\\.staging\\critique-20260327_110359_p2.md
      1 ## Cross-Agent Contradictions
      2
      3 1.1. [none] — No direct contradictions between specialists. Both flagged
         the missing ADR schema, from different angles (reasoning vs. compliance
        ) — consistent, not contradictory.
      4
      5 ## Severity Calibration Issues
      6
      7 1.1. [MEDIUM calibration gap] — **AUDIT phase undefined** was rated MEDI
        UM, but **ADR markdown schema missing** was rated HIGH. Both are prerequ
        isite-blocking issues — without the schema, `adr_to_tests` cannot work;
        without the AUDIT mechanism specified, `/code` cannot integrate ADR veri
        fication. Severity should be equivalent (both HIGH). The AUDIT mechanism
         is arguably more critical since it's the integration point.
      8
      9 ## Missed Blind Spots
     … +31 lines (ctrl+o to expand)

  Searched for 3 patterns, read 2 files (ctrl+o to expand)

❯ /rename auditing
  ⎿  Session renamed to: auditing

● Write(P:/__csf/.staging/critique-20260327_110359_p3.md)
  ⎿  Wrote 134 lines to ..\\..\\__csf\\.staging\\critique-20260327_110359_p3.md
      1 ## Intent Summary
      2
      3 Design proposal for an ADR verification system that creates automated te
        st coverage from Architecture Decision Records, linking architectural de
        cisions to implementation via pytest tests and deviation detection hooks
        . Spans modifications to `/planning`, `/code`, `/verify` skills plus new
         scripts and a hook.
      4
      5 ## Health Score: 50% — Warning
      6
      7 The proposal addresses a real architectural gap but has 2 HIGH-severity
        prerequisite blockers and 1 MEDIUM calibration issue. The design is dire
        ctionally sound but not yet implementable without resolving foundational
         schema issues first.
      8
      9 ---
     … +124 lines (ctrl+o to expand)

  Read 1 file (ctrl+o to expand)

● Now let me log the skill coverage:

  ▎ Target: ADR verification system design: proposed changes to /planning, /code,
  /verify skills plus new adr_to_tests, verify_adr, verify_all_adrs scripts and
  PostToolUse_adr_deviation_check hook

  Intent Summary

  Design proposal for an ADR verification system that creates automated test coverage
  from Architecture Decision Records, linking architectural decisions to implementation
   via pytest tests and deviation detection hooks. Spans modifications to /planning,
  /code, /verify skills plus new scripts and a hook.

  Health Score: 50% — Warning

  The proposal addresses a real architectural gap but has 2 HIGH-severity prerequisite
  blockers and 1 MEDIUM calibration issue. The design is directionally sound but not
  yet implementable without resolving foundational schema issues first.

  ---
  Logical Gaps & Inconsistencies

  1.1. [HIGH] No ADR markdown schema (source: adversarial-compliance)
  - The existing ADR at
  P:/__csf/arch_decisions/2025-03-08_python_tree_sitter_integration.md has no ##
  Acceptance Criteria section — only prose rationale and architectural decisions. The
  proposal assumes ## Acceptance Criteria with parseable - AC1: testable statement
  format, but no ADR in the repo uses this format.
  - Without this schema, adr_to_tests cannot extract ACs from any existing ADR. Only
  future ADRs would benefit.
  - Verification:
  P:/__csf/arch_decisions/2025-03-08_python_tree_sitter_integration.md:1-60 — no
  structured AC section exists.

  1.2. [HIGH] AUDIT phase mechanism unspecified (source: adversarial-critic)
  - /code Phase 7 AUDIT (P:/.claude/skills/code/SKILL.md:1798) runs ruff, mypy, pylint
  — no ADR verification exists. The proposal says "verify ADR ACs are still satisfied"
  but gives no execution mechanism.
  - Must choose: (a) subprocess pytest, (b) /verify adr:<id> invocation, (c) direct
  import. This is a prerequisite-blocking integration decision.

  ---
  Hidden Assumptions & Fragile Dependencies

  2.1. [MEDIUM] Prose ACs cannot be parsed into pytest (source: adversarial-critic)
  - The existing ADR's criteria are architectural rationale ("Use
  tree-sitter-language-pack over alternatives"), not testable assertions. These cannot
  become failing tests without manual translation.

  2.2. [MEDIUM] /planning trigger mechanism undefined (source: adversarial-critic,
  Phase 2 recall failure)
  - "At acceptance time" implies automatic generation, but /planning has no step that
  generates test stubs. The ADR-aware behavior (/planning SKILL.md lines 145-160)
  creates a plan from an ADR but emits no test file.

  2.3. [LOW] ADR version lifecycle undefined (source: adversarial-critic)
  - When an ADR is revised, should old tests be overwritten, archived, or kept? No
  protocol specified.

  ---
  Missing Obvious Actions / Best Practices

  3.1. [HIGH] Existing ADRs retroactively unparseable (source: Phase 2 recall failure)
  - The 3 existing ADRs in P:/__csf/arch_decisions/ use prose criteria. For these to
  have ADR test coverage, someone must manually convert prose to testable ACs. The
  proposal offers no path for this.

  3.2. [MEDIUM] Commit-level ADR ID linking absent (source: Phase 2 recall failure)
  - The proposal mentions "ADR-to-code linking in commit messages" but doesn't specify
  format. Without ADR-0001 in commit footers, there is no audit trail connecting code
  changes to architectural decisions.

  ---
  Risks and Edge Cases

  4.1. [MEDIUM] ADR test maintenance overhead for solo dev (source: adversarial-critic)
  - Every ADR with test coverage becomes an ongoing maintenance obligation. For a solo
  dev, this could become burdensome with many ADRs.

  4.2. [LOW] Circular dependency in file tracking (source: adversarial-compliance)
  - ADR registry and test infrastructure files should be excluded from "ADR-covered
  files" to avoid self-referential triggers.

  ---
  Concrete Recommendations

  5.1. [HIGH] Define ADR markdown schema first (source: adversarial-compliance)
  - Create P:/__csf/docs/adr_schema.md with required ## Acceptance Criteria format and
  pytest naming convention.
  - Require AC numbering and imperative mood. Non-compliant ADRs cannot be processed by
   adr_to_tests.

  5.2. [HIGH] Specify /planning test stub generation trigger (source:
  adversarial-critic)
  - Choose one: (a) explicit command after ADR acceptance, (b) automatic on status
  change, (c) explicit step in /planning workflow. Recommend (c) — add a step after
  implementation-ready status is set.

  5.3. [HIGH] Define AUDIT phase integration mechanism (source: adversarial-critic)
  - Recommend: invoke /verify adr:<id> from /code AUDIT phase when plan has ADR-linked
  tasks. This reuses existing /verify infrastructure.

  5.4. [MEDIUM] Schema-validate ADR_REGISTRY.json (source: adversarial-compliance)
  - Add JSON Schema as inline comment header in the registry file, not a separate doc.

  5.5. [MEDIUM] ADR deprecation protocol (source: adversarial-compliance)
  - On deprecation: rename test file to test_adr_<id>_DEPRECATED.py, add
  @pytest.mark.skip("ADR deprecated"). Do not delete.

  ---
  Open Questions / Unknowns

  6.1. [LOW] ADR test location — tests/adr/ at repo root vs. alongside ADR file?
  Recommend repo root P:/__csf/tests/adr/.

  6.2. [LOW] Fallback for unparseable ACs — Emit skeleton with @pytest.mark.skip("TODO:
   manual AC") rather than failing.

  6.3. [LOW] Threshold for ADR test coverage — Only when ACs are objectively testable
  (not architectural rationale).

  ---
  Recommended Next Steps

  Recommended Next Steps

  1 (SCHEMA) - ADR format must be defined before any script can be built
  - 1a: Create P:/__csf/docs/adr_schema.md with required ## Acceptance Criteria format
  and pytest naming convention → Manual - this is the prerequisite for everything else
  - 1b: Convert existing ADRs to compliant format (or mark as "prose-only, manual
  verification required") → Manual - existing ADRs at P:/__csf/arch_decisions/ need
  triage

  2 (PLANNING INTEGRATION) - Define how /planning triggers test stub generation
  - 2a: Decide trigger mechanism: explicit command vs automatic status change vs
  workflow step → Manual - /planning SKILL.md modification depends on this decision
  - 2b: Add test stub generation step to /planning workflow after implementation-ready
  → Manual - P:/.claude/skills/planning/SKILL.md

  3 (CODE INTEGRATION) - Define how /code AUDIT phase runs ADR verification
  - 3a: Choose execution model: pytest subprocess vs /verify adr:<id> skill invocation
  → Manual - recommend /verify reuse per 5.3
  - 3b: Modify /code AUDIT phase to invoke ADR verification when plan has ADR-linked
  tasks → Manual - P:/.claude/skills/code/SKILL.md

  4 (SCRIPTS) - Build the three core scripts
  - 4a: Implement adr_to_tests at P:/__csf/scripts/adr_to_tests.py → Manual - parse ADR
   markdown, emit pytest skeleton
  - 4b: Implement verify_adr at P:/__csf/scripts/verify_adr.py → Manual - check
  AC-to-test linkage
  - 4c: Implement verify_all_adrs at P:/__csf/scripts/verify_all_adrs.py → Manual -
  walk all ADRs, run corresponding tests

  5 (REGISTRY) - Define and implement ADR registry
  - 5a: Define ADR_REGISTRY.json schema (inline JSON comment header) → Manual -
  P:/__csf/arch_decisions/ADR_REGISTRY.json
  - 5b: Implement ADR deprecation protocol (skip markers, not deletion) → Manual -
  P:/__csf/scripts/adr_to_tests.py

  6 (HOOK) - Deviation detection on file changes
  - 6a: Implement PostToolUse_adr_deviation_check.py hook → Manual -
  P:/.claude/hooks/PostToolUse_adr_deviation_check.py
  - 6b: Add commit-msg hook for ADR ID in commit messages → Manual - git commit message
   convention

  7 (VERIFY) - Integrate ADR mode into /verify skill
  - 7a: Add verify adr:<id> trigger to /verify SKILL.md → Manual -
  P:/.claude/skills/verify/SKILL.md
  - 7b: Add ADR verification tier to /verify workflow → Manual -
  P:/.claude/skills/verify/tiers/

  0 — Begin Implementing ALL Recommended Next Steps"

## Assistant

Yes, this is **conceptually sound and directionally excellent**; it directly targets the ADR–implementation gap and drift. The critique you surfaced is mostly **valid**, and actually sharpens the plan rather than invalidating it.[1][2][3]

Below is a compact “gap/opportunity” map plus a few tweaks to tighten the design.

***

### What’s solid / well‑aligned

1. **Skill‑level separation of concerns**  
   - `/planning` owns ADR → test stubs at acceptance time.  
   - `/code` owns ADR‑aware implementation and ADR test pass in AUDIT.  
   - `/verify` owns on‑demand `adr:<id>` and batch `/verify_all_adrs`.  
   This pushes the ADR–test linkage into the *workflow*, not retroactively into CI.[4][1]

2. **Mechanical ADR → test**  
   - Turning ACs into failing test stubs at ADR acceptance is a **clear “Definition of Done”** for the ADR and aligns with ATDD‑style acceptance‑test‑driven development.[2][3]

3. **AUDIT‑phase ADR checks**  
   - Running ADR tests as part of the `/code` AUDIT step (or via `/verify`) is a good fit for your current pipeline; it localizes the “implementation must match ADR” check to the same skill that implements the plan.[3][5]

4. **Drift via hook + cron**  
   - `PostToolUse_adr_deviation_check.py` plus `verify_all_adrs` is the right structural pattern:  
     - hooks for fine‑grained deviations,  
     - cron / CI for periodic “ADR‑to‑code” sanity checks.[5][3]

***

### Key gaps / blockers (consistent with the critique)

1. **No enforced ADR schema yet**  
   - You assume `## Acceptance criteria` in a parseable format, but current ADRs don’t have that.[6][1]
   - **Gap:** `adr_to_tests` can’t work end‑to‑end until you define and enforce a schema.  
   - **Opportunity:**  
     - Define `P:/__csf/docs/adr_schema.md` that prescribes:
       - Mandatory `## Acceptance criteria` in a list.
       - Imperative, testable language (e.g., “The system must …” instead of “We prefer…”).[7][2]
     - Add a pre‑ADR lint that rejects ADRs without a valid AC section.  

2. **AUDIT mechanistic implementation unspecified**  
   - Proposal says “verify ADR ACs are still satisfied” but doesn’t pick a concrete mechanism.[3]
   - **Gap:** it’s unclear if AUDIT runs tests via subprocess, imports them, or calls `/verify adr:<id>`.  
   - **Opportunity:**  
     - Choose one primary path (e.g., `/verify adr:<id>` invocation from AUDIT) and keep subprocess calls for CI.  
     - This keeps the ADR verification logic in one place, rather than duplicating it in `/code` and `/verify`.  

3. **Retro‑compatibility with existing prose‑only ADRs**  
   - Existing ADRs are rationale‑heavy and not testable; they can’t be auto‑converted to tests.[8][1]
   - **Gap:**  
     - No plan for “legacy ADRs” vs “new ADRs with testable ACs”.  
   - **Opportunity:**  
     - Add a triage step:
       - Mark ADRs as:
         - `testable` (ACs are machine‑parseable and get test stubs).
         - `manual` (prose only, no auto‑test, but may be audited in reviews).[4][5]
     - Tooling can skip `manual` ADRs in `verify_all_adrs` unless explicitly requested.  

4. **ADR‑code linkage via commits not integrated**  
   - Proposal mentions “ADR‑ID in commit messages” but doesn’t wire it into skill or hook logic.[5][7]
   - **Gap:** there’s no audit trail Feld is asking for.  
   - **Opportunity:**  
     - Add a lightweight `commit_msg_schema` rule in your Git hooks that:
       - Requires `ADR-0001` in the commit body when touching ADR‑governed files.  
     - Make `/code` awareness of this convention so that when it generates commits, it tags the right ADRs.  

5. **ADR versioning and deprecation not modeled**  
   - No answer yet on what happens when an ADR is revised or deprecated.[1][4]
   - **Gap:** tests can become stale or misleading.  
   - **Opportunity:**  
     - Define a simple lifecycle:
       - `proposed` → `accepted` → `deprecated`/`superseded`.  
     - When deprecating:
       - Do not delete the test file; instead, mark it as `@pytest.mark.skip("ADR deprecated")`.[1][4]

***

### Smaller opportunities / refinements

- **ADR‑to‑test failure mode**  
  - The current plan assumes every AC can be parsed into a test.[2][3]
  - **Opportunity:** allow `adr_to_tests` to emit `@pytest.mark.skip("TODO: manual AC")` when ACs are not testable, so you still get a stub without blocking the workflow.  

- **ADR coverage threshold**  
  - You’ll want to avoid forcing ADR tests for every trivial decision.[4][5]
  - **Opportunity:**  
    - Define a “ADR‑testable” flag in the schema;  
    - Only ADRs that are “architecturally significant” get test stubs.  

- **ADR registry + schema**  
  - The critique nudges you toward an `ADR_REGISTRY.json`.[9][10]
  - **Opportunity:**  
    - Store:
      - `id`, `status`, `testable`, `test_file`, `deprecated_reason`.  
    - Enforce this registry’s schema with JSON Schema (inline comment header) so tooling can trust it.[10][11]

***

### How to preserve your plan but harden it

Your original plan is **good enough to implement**; you just need to front‑load the schema and lifecycle decisions:

1. **Do schema first**  
   - Define `P:/__csf/docs/adr_schema.md` and validate incoming ADRs against it.[1][4]

2. **Triange existing ADRs**  
   - Convert or tag the current ADRs (`testable` vs `manual`).[6][8]

3. **Pick one AUDIT mechanism**  
   - Prefer: `/code` runs `/verify adr:<id>` for ADR‑linked tasks, keeping the verification logic in `/verify`.[3][5]

4. **Add ADR‑aware commit‑linting**  
   - Add a simple `commit_msg` rule and make `/code` respect it.[7][5]

5. **Implement the scripts and hooks**  
   - Your bullet list (`adr_to_tests`, `verify_adr`, `verify_all_adrs`, `PostToolUse_adr_deviation_check.py`) is solid; just align them with the schema and lifecycle rules above.[5][3]

***

If you want, next step can be:  
- Sketch the **exact markdown schema** for ADRs (with `## Acceptance criteria` format) and the **JSON schema** for the registry, tailored to your current ADRs.

## Human

how should this be updated?

## Assistant

This ADR document is already **strong and comprehensive**—it incorporates most critique gaps (schema, lifecycle, registry, phased implementation).  No major rewrites needed, but **tighten it by adding specificity, closing open questions, and formalizing schemas**.[1][2][3][4]

Here's a **minimal update plan** (3 concrete changes, 0 deletions). Apply these to make it **implementable as‑is**.

***

## 1. Add **concrete schemas** (closes HIGH gap: schema enforcement)

The document defines schema conceptually but lacks **exact formats**. Add these under `## Schema` section:

### ADR Markdown Schema (new subsection)
```
## Acceptance Criteria
- AC1: [Imperative, testable statement, e.g. "Store data in PostgreSQL, not SQLite"]
- AC2: [Must use imperative mood, no prose opinions]
- AC3: [...]

Rules:
- ACs must be imperative ("Must X", "Use Y over Z").
- ACs must be testable (assertable boolean outcomes).
- Numbered sequentially: AC1, AC2, ...
- If no testable ACs: Mark `status: prose-only` in registry.
```

### ADR_REGISTRY.json Schema (new subsection)
Inline JSON Schema header for `.claude/adr/ADR_REGISTRY.json`:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "id": {"type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}_.*$"},
      "covers": {"type": "array", "items": {"type": "string"}},  // glob patterns, e.g. ["src/search/**"]
      "testfile": {"type": "string"},  // "tests/adr/test_adr_2026-03-27_verification.py"
      "status": {"enum": ["proposed", "accepted", "implementation-ready", "deprecated", "prose-only"]},
      "deprecated_by": {"type": "string", "nullable": true}
    },
    "required": ["id", "covers", "status"]
  }
}
```

**Why:** Enables `adr_to_tests` and `verify_adr` to parse reliably. Existing ADRs get retroactively tagged `prose-only`.[2][4]

***

## 2. Close **open questions** (add resolved answers)

Replace the `## Open Questions` section with:

```
## Resolved Questions
1. **Threshold for ADR test coverage**: Only ADRs with objectively testable ACs (not architectural rationale). Prose‑heavy ADRs → `prose-only` status.
2. **ADR ID in commit messages**: Yes, enforce via `commit-msg` hook: `ADR-<id>` in footer for commits touching `covers` files.
3. **ADR test maintenance**: Use `deprecated` status + `pytest.mark.skip("ADR deprecated")` to pause maintenance without deletion.
4. **ADR test location**: `P:/__csf/tests/adr/test_adr_<id>_<slug>.py` (repo root).
5. **AUDIT mechanism**: `/code` AUDIT invokes `/verify adr:<id>` (reuses `/verify` infra).
6. **Fallback for unparseable ACs**: `adr_to_tests` emits `@pytest.mark.skip("TODO: manual AC")`.
```

**Why:** Removes ambiguity; makes the ADR self‑contained and executable.[3][5]

***

## 3. Specify **AUDIT integration mechanism** (closes critique HIGH)

Under `## Decision` → point 4, replace vague "AUDIT phase verifies ADR tests pass" with:

```
4. `/code` AUDIT integration:
   - When plan has `adr:<id>` tasks:
     - Run `/verify adr:<id>` (invokes `verify_adr.py` → pytest on `testfile`).
   - Fail AUDIT if ADR tests fail.
   - Modify: `P:/.claude/skills/code/SKILL.md` (AUDIT phase, line ~1800).
```

**Why:** Picks the concrete path (`/verify` invocation over subprocess); aligns with your existing `/verify` tier structure.[5][1]

***

## 4. Minor tweaks (optional, polish)

| Section | Current | Update |
|---------|---------|--------|
| **Status** | `PROPOSED` | `ACCEPTED` (after schema review) |
| **Consequences → Sad Path** | Lists failure modes | Add: "Hook warns → human triage (update ADR or suppress)" |
| **Files table** | Good | Add row: `.claude/hooks/commit-msg` (enforce ADR in commits) |
| **References** | Good | Add: `[web:16]` MADR template, `[web:21]` JSON Schema |

**Why:** Makes it production‑ready without changing intent.[4][2]

***

## Updated file structure preview

After changes:
```
2026-03-27_adr-verification-system.md
├── Context / Problem (unchanged)
├── Decision (AUDIT specifics)
├── Schema
│   ├── ADR Markdown Schema ← NEW
│   ├── ADR_REGISTRY.json Schema ← NEW
│   └── Lifecycle States (unchanged)
├── Files table (+ commit-msg hook)
├── Resolved Questions ← REPLACED
└── References (+ schema links)
```

**Total changes:** ~150 lines added, 30 lines edited. **Impact:** 100% implementable now.

**Next step:** Apply these → run `/planning` on this updated ADR → generate first `adr_to_tests` stub.[1]

Want me to output the **full updated markdown** as a diff/patch?
