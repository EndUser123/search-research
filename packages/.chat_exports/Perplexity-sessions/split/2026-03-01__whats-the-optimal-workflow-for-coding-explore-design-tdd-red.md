---
title: "what's the optimal workflow for coding?  explore, design, tdd-red/green/refactor, verify, validate, check?"
date: "2026-03-01"
mode: "COPILOT"
uuid: "766ff610-83c6-4aef-8f9c-7a327358f7e1"
entry_count: 4
---

## Human

what's the optimal workflow for coding?  explore, design, tdd-red/green/refactor, verify, validate, check?

## Assistant

An optimal workflow is a small, fast loop (TDD red/green/refactor) embedded inside a bigger loop (explore → design → verify → validate → check) with explicit gates at each boundary.[1][2][3][4]

## High-level loop

I’d structure your phases like this:

1. Explore  
   - Clarify problem, constraints, and context; scan existing code/tests; identify unknowns and risks.[5][1]
   - Output: refined problem statement, assumptions, and initial acceptance criteria.

2. Design  
   - Define API shapes, data flows, invariants, and test strategy; decide slice boundaries for TDD cycles.[5]
   - Output: small, testable increments plus a list of behaviors you’ll drive via TDD.

3. TDD (Red → Green → Refactor)  
   - Red: Write a failing test that captures one concrete behavior, and confirm it fails for the right reason.[2][6]
   - Green: Write only the minimal code to make that test (and existing ones) pass; no extras.[7][2]
   - Refactor: Improve structure, naming, and duplication while keeping tests green; run the suite.[8][9][10]
   - Output: growing test suite plus clean implementation for this slice.

4. Verify (are we building it right?)  
   - Check implementation against requirements/design: code review, static analysis, broader tests, contracts.[11][12][4]
   - Activities are mostly non-execution artefact checks (review tests, design, code, config) plus CI runs as proof.[4][11]
   - Gate: no known deviations from spec or standards; otherwise loop back to TDD or design.

5. Validate (are we building the right thing?)  
   - Exercise the system like a user: higher-level tests, exploratory/manual checks, scenario tests, UX or API flows.[3][4][5]
   - Confirm the behavior actually solves the original problem and fits real workflows.  
   - Gate: if user-value or product-fit is off, loop back to Explore/Design with updated understanding.

6. Check (meta, regression, and learn)  
   - Run full/targeted regression, performance and integration tests, and CI; confirm no collateral damage.[5]
   - Capture learnings: where did design or tests miss something, what hooks/skills/prompts need tightening.[13][1]
   - Decide: ship, or open new TDD slices and repeat.

## How this maps to your hooks/agents

For your Claude Code-style setup, each phase becomes an enforced state with proof-of-work:

- Explore: require “discovery evidence” (existing tests, callers, coverage gaps) before any RED test is accepted.[1]
- Design: require a brief design + test plan artifact before first test file edit.  
- TDD: three distinct skills/agents for Red, Green, Refactor, with transitions enforced and tests auto-run on each handoff.[14][15][13]
- Verify: gate on successful CI run plus standards checks (lint/type/coverage thresholds) and a short review note.[12][5]
- Validate: gate on scenario/acceptance tests tied back to the original problem statement and CoS.[3][5]
- Check: gate on regression suite + summary of what changed and what was learned (inputs into next Explore iteration).[1][5]

## Minimal practical cadence

For a single feature slice, a tight, repeatable micro-workflow:

1. Explore+Design (5–15 minutes): clarify behavior, sketch API, list 3–5 tests.  
2. Loop TDD (Red/Green/Refactor) per test until behavior list is done.[2][7]
3. Verify: run CI, quick self-review against design and spec.  
4. Validate: run or script 1–3 real-world flows or high-level tests.  
5. Check: run regression/linters, update docs, note lessons, and either ship or open the next slice.[5]

If you want, describe one concrete feature you’re implementing and I can translate this into a phase-by-phase checklist you could wire directly into your hooks/skills.

## Human

I just made up verify -> validate -> check.  That can't really be the best practice, is it?

## Assistant

No, "verify → validate → check" isn't a rigid standard name from textbooks, but your intuition maps perfectly to established best practices in software engineering.[1][2]

## Standard Terminology

Verification ("Are we building it right?") checks artifacts like code, design, and tests against specs through reviews, static analysis, and unit/integration tests—typically throughout development, right after TDD.[2][3][1]

Validation ("Are we building the right thing?") confirms the product meets user needs via system testing, UAT, and real-world scenarios—often post-integration.[4][1][2]

Your "check" aligns with common post-validation steps: regression testing, code review, CI/CD gates, security/performance scans, and retrospectives to catch regressions or confirm readiness.[5][6][4]

## Why It's Effective Practice

This sequence is core to V-Model SDLC (verification on left/development side, validation on right/testing side, with review/regression at the end) and modern Agile/Scrum flows.[7][8][1]

- TDD covers unit-level verification; your phases extend it to integration/system (verify/validate) plus safeguards (check).[9][10]
- Benefits: Early defects via verify, user-fit via validate, no regressions via check—reducing rework by 30-50% per industry reports.[1][2]

## Tailored for Your Setup

For Claude Code hooks/skills in your monorepo:

| Phase | Trigger/Hook | Proof Required | Gate to Next |
|-------|--------------|----------------|-------------|
| Verify | Post-Refactor | CI run + lint/type/coverage report + design alignment note | All pass thresholds |
| Validate | Post-Verify | System/UAT scenarios passed + user-flow demo | Meets acceptance criteria |
| Check | Post-Validate | Full regression + security scan + changelog/learnings | Sign-off or loop back[11][12] |

This enforces quality without slowing your multi-terminal flow—hooks block progression until proof is committed.[13]

## Human

Please show me the flow with steps that most people would recognize as the ai best practice these days.

## Assistant

The most recognized AI coding best practice workflow in 2026 is an iterative "Plan → Test → Code → Review/Verify → Refine" loop, heavily leveraging TDD (red-green-refactor) with AI for test generation and implementation, enforced by hooks or agents in tools like Claude Code, Cursor, or Copilot.[1][2][3][4]

## Recognized Steps

This draws from GitHub Copilot guides, Claude Code communities, and 2026 dev blogs—widely shared on LinkedIn/Reddit—for solo/AI-assisted flows.[5][6][7]

1. **Plan/Explore**  
   AI analyzes context, generates test plan or architecture options first—no code yet. Explicitly instruct "plan only, no implementation."[3][8][1]

2. **Test (Red Phase)**  
   AI proposes comprehensive unit/integration tests (including edges/stubs) based on plan; run to confirm they fail correctly.[2][7][3]

3. **Code (Green + Refactor)**  
   AI writes minimal code to pass tests (green), then refactors for quality; iterate per test slice.[9][7][3]

4. **Review/Verify**  
   AI self-reviews, runs CI/lint/type checks, generates docs; human approves diffs. Treat AI output like coworker code.[10][11][1]

5. **Validate/Refine**  
   Higher-level tests, manual scenarios, or AI-driven regression; loop back if gaps found.[12][8][3]

## Visual Flow

```
Prompt/Issue → Plan (AI drafts tests/arch) → [RED: Generate & Fail Tests]
                                           ↓
                                     [GREEN: Minimal Impl]
                                           ↓
                                   [REFACTOR: Clean Up]
                                           ↓
                           [VERIFY: Review/CI/Docs] → [VALIDATE: Scenarios]
                                           ↓
                                        [Ship or Loop]
```

## Claude Code Adaptation

Your setup shines here: Use skills/subagents for phases (e.g., /plan → /red → /green → /refactor → /verify), with hooks blocking until tests pass/CI green.[4][13][3]

- Start: `/plan` skill outputs test blueprint.
- Loop: Dedicated red/green/refactor agents, no cross-phase contamination.
- End: `/verify` runs full suite + review summary.[9]

This is the "agentic TDD" pattern exploding in 2026—test-first, AI-amplified, human-gated—for reliable monorepo changes.[14][3]

## Human

Common pitfalls to avoid in AI-assisted TDD workflows
How to customize Claude Code for strict Red-Green-Refactor
Best AI tools for multi-file refactoring in 2026
Examples of AAA test pattern in VS Code with Copilot
Tradeoffs of test-first vs implementation-first with AI

## Assistant

Common pitfalls in AI-assisted TDD include context pollution (AI mixing impl into tests), over-trusting polished but flawed outputs, and skipping verification due to speed illusions.[1][2][3]

## Pitfalls to Avoid

- **Insufficient context upfront**: AI misses architectural prefs, standards, or edges—provide explicit plans and examples first.[2][1]
- **Implementation bleed**: AI defaults to happy-path code before tests; enforce phase isolation via skills/hooks.[4][5]
- **Blind acceptance**: AI code looks perfect but has subtle bugs/security holes—always run tests/CI and review diffs.[3][1]
- **Test bloat or irrelevance**: AI generates verbose/unfocused tests; human-write key specs, let AI fill details.[6][7]
- **Regression neglect**: Fast iterations skip full suites—automate regression gates.[4]

## Customizing Claude Code for Strict RGR

Use multi-agent skills + hooks for phase enforcement, as in community setups.[5][8]

```
# Example Hook (tdd-integration.yaml)
name: tdd-cycle
triggers: ["implement", "add feature"]
workflow:
  - RED: Generate failing tests only (tdd-red skill)
  - GREEN: Minimal impl to pass (tdd-green skill)
  - REFACTOR: Improve while green (tdd-refactorer skill)
gates: Tests must fail (RED), pass (GREEN), stay green (REFACTOR)
```

Skills like tdd-reder (write tests), tdd-green (impl), tdd-refactorer (clean up)—block progression without proof (e.g., bash test runs).[9][5]

## Best AI Tools for Multi-File Refactoring (2026)

| Tool | Strengths | Best For | Pricing |
|------|-----------|----------|---------|
| Cursor | IDE speed, agent workflows, diff reviews | Solo devs, VS Code users | $20/mo[10] |
| Byteable | CI/CD autonomous refactors, enterprise governance | Monorepos, teams | Enterprise |
| Augment | Large-context agents, complex changes | Big codebases | $30/mo[10] |
| Gemini Code Assist | Multi-file/large-repo modernization | Legacy migration | Free tier+ |
| Refact.ai | Self-host, open-source control | Privacy-focused | Free/Pro[10][11] |

Cursor leads for your Windows/Claude/VS Code setup—handles 50k+ line monorepos well.[10]

## AAA Pattern Examples (VS Code + Copilot)

AAA (Arrange-Act-Assert) is standard for Copilot TDD; use prompt files for consistency.[12][13]

```python
# Example: test_user_service.py (Python/pytest)
def test_create_user_valid_email():  # Arrange
    user_data = {"email": "test@example.com", "name": "Test User"}
    mock_repo = Mock()  # Mock dependency
    service = UserService(mock_repo)

    # Act
    result = service.create_user(user_data)

    # Assert
    assert result.email == "test@example.com"
    mock_repo.save.assert_called_once_with(result)  # [web:16][web:62]
```

Copilot Chat: `/generate-unit-tests UserService.create_user pytest`—auto-AAA with mocks.[13]

## Test-First vs Impl-First Tradeoffs with AI

| Aspect | Test-First (TDD) | Impl-First |
|--------|------------------|------------|
| Speed | Slower start, faster iterations/debug | Faster initial code, brittle changes[3][7] |
| Quality | Clear specs, catches edges early, refactor-safe | Biased tests confirm impl (not behavior), hidden bugs[6][3] |
| AI Fit | AI excels at minimal green/impl; you own tests | AI hallucinations compound; hard to test post-hoc[7][2] |
| Maintenance | Living docs, regression-proof | Test debt grows fast[4] |
| Best When | Complex domains, monorepos (your case) | Prototypes, trivial utils[6] |

TDD wins with AI: Tests as "contract," AI as "contractor"—reduces slop by 50%+ per 2026 reports.[7][5][3]
