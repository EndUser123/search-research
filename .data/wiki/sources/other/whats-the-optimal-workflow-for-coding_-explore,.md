<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# what's the optimal workflow for coding?  explore, design, tdd-red/green/refactor, verify, validate, check?

An optimal workflow is a small, fast loop (TDD red/green/refactor) embedded inside a bigger loop (explore → design → verify → validate → check) with explicit gates at each boundary.[^1_1][^1_2][^1_3][^1_4]

## High-level loop

I’d structure your phases like this:

1. Explore
    - Clarify problem, constraints, and context; scan existing code/tests; identify unknowns and risks.[^1_5][^1_1]
    - Output: refined problem statement, assumptions, and initial acceptance criteria.
2. Design
    - Define API shapes, data flows, invariants, and test strategy; decide slice boundaries for TDD cycles.[^1_5]
    - Output: small, testable increments plus a list of behaviors you’ll drive via TDD.
3. TDD (Red → Green → Refactor)
    - Red: Write a failing test that captures one concrete behavior, and confirm it fails for the right reason.[^1_2][^1_6]
    - Green: Write only the minimal code to make that test (and existing ones) pass; no extras.[^1_7][^1_2]
    - Refactor: Improve structure, naming, and duplication while keeping tests green; run the suite.[^1_8][^1_9][^1_10]
    - Output: growing test suite plus clean implementation for this slice.
4. Verify (are we building it right?)
    - Check implementation against requirements/design: code review, static analysis, broader tests, contracts.[^1_11][^1_12][^1_4]
    - Activities are mostly non-execution artefact checks (review tests, design, code, config) plus CI runs as proof.[^1_4][^1_11]
    - Gate: no known deviations from spec or standards; otherwise loop back to TDD or design.
5. Validate (are we building the right thing?)
    - Exercise the system like a user: higher-level tests, exploratory/manual checks, scenario tests, UX or API flows.[^1_3][^1_4][^1_5]
    - Confirm the behavior actually solves the original problem and fits real workflows.
    - Gate: if user-value or product-fit is off, loop back to Explore/Design with updated understanding.
6. Check (meta, regression, and learn)
    - Run full/targeted regression, performance and integration tests, and CI; confirm no collateral damage.[^1_5]
    - Capture learnings: where did design or tests miss something, what hooks/skills/prompts need tightening.[^1_13][^1_1]
    - Decide: ship, or open new TDD slices and repeat.

## How this maps to your hooks/agents

For your Claude Code-style setup, each phase becomes an enforced state with proof-of-work:

- Explore: require “discovery evidence” (existing tests, callers, coverage gaps) before any RED test is accepted.[^1_1]
- Design: require a brief design + test plan artifact before first test file edit.
- TDD: three distinct skills/agents for Red, Green, Refactor, with transitions enforced and tests auto-run on each handoff.[^1_14][^1_15][^1_13]
- Verify: gate on successful CI run plus standards checks (lint/type/coverage thresholds) and a short review note.[^1_12][^1_5]
- Validate: gate on scenario/acceptance tests tied back to the original problem statement and CoS.[^1_3][^1_5]
- Check: gate on regression suite + summary of what changed and what was learned (inputs into next Explore iteration).[^1_1][^1_5]


## Minimal practical cadence

For a single feature slice, a tight, repeatable micro-workflow:

1. Explore+Design (5–15 minutes): clarify behavior, sketch API, list 3–5 tests.
2. Loop TDD (Red/Green/Refactor) per test until behavior list is done.[^1_2][^1_7]
3. Verify: run CI, quick self-review against design and spec.
4. Validate: run or script 1–3 real-world flows or high-level tests.
5. Check: run regression/linters, update docs, note lessons, and either ship or open the next slice.[^1_5]

If you want, describe one concrete feature you’re implementing and I can translate this into a phase-by-phase checklist you could wire directly into your hooks/skills.
<span style="display:none">[^1_16][^1_17]</span>

<div align="center">⁂</div>

[^1_1]: https://www.perplexity.ai/search/1ba63fae-1271-4785-8f2f-41c42e853b84

[^1_2]: https://www.testrail.com/blog/test-driven-development/

[^1_3]: https://www.scrum.org/resources/blog/doing-right-thing-right-validation-and-verification

[^1_4]: https://www.baeldung.com/cs/testing-verification-vs-validation

[^1_5]: https://www.linkedin.com/pulse/practical-guide-implement-development-workflow-focused-garcía

[^1_6]: https://full-time.learnhowtoprogram.com/c-and-net/tdd-and-debugging/review-the-red-green-refactor-workflow-and-testing-best-practices

[^1_7]: https://www.practitest.com/resource-center/article/tdd-guide/

[^1_8]: https://monday.com/blog/rnd/test-driven-development-tdd/

[^1_9]: https://www.codecademy.com/article/tdd-red-green-refactor

[^1_10]: https://martinfowler.com/bliki/TestDrivenDevelopment.html

[^1_11]: https://www.geeksforgeeks.org/software-engineering/differences-between-verification-and-validation/

[^1_12]: https://www.docuwriter.ai/posts/code-review-best-practices-streamlining-workflow

[^1_13]: https://www.perplexity.ai/search/4b07855a-5dfe-47a8-b88f-a203f22d7455

[^1_14]: https://code.visualstudio.com/docs/copilot/guides/test-driven-development-guide

[^1_15]: https://lobehub.com/skills/pramoddutta-qaskills-tdd-red-green-refactor

[^1_16]: https://developer.ibm.com/articles/5-steps-of-test-driven-development/

[^1_17]: https://lobehub.com/skills/rootcastleco-rei-skills-tdd-workflows-tdd-cycle


---

# I just made up verify -> validate -> check.  That can't really be the best practice, is it?

No, "verify → validate → check" isn't a rigid standard name from textbooks, but your intuition maps perfectly to established best practices in software engineering.[^2_1][^2_2]

## Standard Terminology

Verification ("Are we building it right?") checks artifacts like code, design, and tests against specs through reviews, static analysis, and unit/integration tests—typically throughout development, right after TDD.[^2_2][^2_3][^2_1]

Validation ("Are we building the right thing?") confirms the product meets user needs via system testing, UAT, and real-world scenarios—often post-integration.[^2_4][^2_1][^2_2]

Your "check" aligns with common post-validation steps: regression testing, code review, CI/CD gates, security/performance scans, and retrospectives to catch regressions or confirm readiness.[^2_5][^2_6][^2_4]

## Why It's Effective Practice

This sequence is core to V-Model SDLC (verification on left/development side, validation on right/testing side, with review/regression at the end) and modern Agile/Scrum flows.[^2_7][^2_8][^2_1]

- TDD covers unit-level verification; your phases extend it to integration/system (verify/validate) plus safeguards (check).[^2_9][^2_10]
- Benefits: Early defects via verify, user-fit via validate, no regressions via check—reducing rework by 30-50% per industry reports.[^2_1][^2_2]


## Tailored for Your Setup

For Claude Code hooks/skills in your monorepo:


| Phase | Trigger/Hook | Proof Required | Gate to Next |
| :-- | :-- | :-- | :-- |
| Verify | Post-Refactor | CI run + lint/type/coverage report + design alignment note | All pass thresholds |
| Validate | Post-Verify | System/UAT scenarios passed + user-flow demo | Meets acceptance criteria |
| Check | Post-Validate | Full regression + security scan + changelog/learnings | Sign-off or loop back[^2_11][^2_12] |

This enforces quality without slowing your multi-terminal flow—hooks block progression until proof is committed.[^2_13]
<span style="display:none">[^2_14][^2_15][^2_16][^2_17][^2_18][^2_19]</span>

<div align="center">⁂</div>

[^2_1]: https://www.scrum.org/resources/blog/doing-right-thing-right-validation-and-verification

[^2_2]: https://www.browserstack.com/guide/verification-and-validation-in-testing

[^2_3]: https://www.virtuosoqa.com/post/test-driven-development

[^2_4]: https://www.virtuosoqa.com/post/software-qa-process

[^2_5]: https://www.practitest.com/resource-center/blog/software-testing-best-practices-checklist/

[^2_6]: https://teachingagile.com/sdlc/testing

[^2_7]: https://www.youtube.com/watch?v=ezlM5EMD_aU

[^2_8]: https://www.geeksforgeeks.org/software-engineering/software-engineering-sdlc-v-model/

[^2_9]: https://code.visualstudio.com/docs/copilot/guides/test-driven-development-guide

[^2_10]: https://moldstud.com/articles/p-fast-feedback-loops-how-tdd-streamlines-net-core-development-for-enhanced-productivity

[^2_11]: https://www.perplexity.ai/search/1ba63fae-1271-4785-8f2f-41c42e853b84

[^2_12]: https://www.docuwriter.ai/posts/code-review-best-practices-streamlining-workflow

[^2_13]: https://www.perplexity.ai/search/4b07855a-5dfe-47a8-b88f-a203f22d7455

[^2_14]: preferences.workflow_design

[^2_15]: https://www.technologia.com/en/blog/articles/4-test-phases-to-follow

[^2_16]: https://testrigor.com/blog/verification-and-validation-in-software-testing/

[^2_17]: https://dvcon-proceedings.org/wp-content/uploads/applying-test-driven-development-methods-to-design-verification-software-in-uvm-e.pdf

[^2_18]: http://www.gvpcew.ac.in/LN-CSE-IT-22-32/CSE-IT/3-Year/32-ST/ST-KNSC-UNIT-2.pdf

[^2_19]: https://argondigital.com/blog/product-management/verification-and-validation/


---

# Please show me the flow with steps that most people would recognize as the ai best practice these days.

The most recognized AI coding best practice workflow in 2026 is an iterative "Plan → Test → Code → Review/Verify → Refine" loop, heavily leveraging TDD (red-green-refactor) with AI for test generation and implementation, enforced by hooks or agents in tools like Claude Code, Cursor, or Copilot.[^3_1][^3_2][^3_3][^3_4]

## Recognized Steps

This draws from GitHub Copilot guides, Claude Code communities, and 2026 dev blogs—widely shared on LinkedIn/Reddit—for solo/AI-assisted flows.[^3_5][^3_6][^3_7]

1. **Plan/Explore**
AI analyzes context, generates test plan or architecture options first—no code yet. Explicitly instruct "plan only, no implementation."[^3_3][^3_8][^3_1]
2. **Test (Red Phase)**
AI proposes comprehensive unit/integration tests (including edges/stubs) based on plan; run to confirm they fail correctly.[^3_2][^3_7][^3_3]
3. **Code (Green + Refactor)**
AI writes minimal code to pass tests (green), then refactors for quality; iterate per test slice.[^3_9][^3_7][^3_3]
4. **Review/Verify**
AI self-reviews, runs CI/lint/type checks, generates docs; human approves diffs. Treat AI output like coworker code.[^3_10][^3_11][^3_1]
5. **Validate/Refine**
Higher-level tests, manual scenarios, or AI-driven regression; loop back if gaps found.[^3_12][^3_8][^3_3]

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

Your setup shines here: Use skills/subagents for phases (e.g., /plan → /red → /green → /refactor → /verify), with hooks blocking until tests pass/CI green.[^3_4][^3_13][^3_3]

- Start: `/plan` skill outputs test blueprint.
- Loop: Dedicated red/green/refactor agents, no cross-phase contamination.
- End: `/verify` runs full suite + review summary.[^3_9]

This is the "agentic TDD" pattern exploding in 2026—test-first, AI-amplified, human-gated—for reliable monorepo changes.[^3_14][^3_3]
<span style="display:none">[^3_15][^3_16][^3_17][^3_18][^3_19]</span>

<div align="center">⁂</div>

[^3_1]: https://www.linkedin.com/pulse/best-ai-coding-practices-actually-work-2026-big-pixel-llc-thz7c

[^3_2]: https://code.visualstudio.com/docs/copilot/guides/test-driven-development-guide

[^3_3]: https://alexop.dev/posts/custom-tdd-workflow-claude-code-vue/

[^3_4]: https://www.perplexity.ai/search/4b07855a-5dfe-47a8-b88f-a203f22d7455

[^3_5]: https://www.linkedin.com/posts/addyosmani_ai-programming-softwareengineering-activity-7407683628396298240-G0hd

[^3_6]: https://www.reddit.com/r/ClaudeCode/comments/1qd64xx/tdd_workflows_with_claude_code_whats_actually/

[^3_7]: https://github.com/readme/guides/github-copilot-automattic

[^3_8]: https://newsletter.systemdesign.one/p/ai-coding-workflow

[^3_9]: https://www.reddit.com/r/ClaudeAI/comments/1lnbcb5/code_claude_how_can_i_create_a_workflow_tdd_it/

[^3_10]: https://interviewing.io/blog/how-to-use-ai-in-meta-s-ai-assisted-coding-interview-with-real-prompts-and-examples

[^3_11]: https://www.pragmaticcoders.com/resources/ai-developer-tools

[^3_12]: https://akiflow.com/blog/best-ai-tools-developers/

[^3_13]: https://www.perplexity.ai/search/1ba63fae-1271-4785-8f2f-41c42e853b84

[^3_14]: preferences.workflow_design

[^3_15]: https://dev.to/austinwdigital/ai-assisted-development-in-2026-best-practices-real-risks-and-the-new-bar-for-engineers-3fom

[^3_16]: work.dev_environment

[^3_17]: https://www.reddit.com/r/datascience/comments/1q85xuw/whats_your_2026_data_science_coding_stack_ai/

[^3_18]: https://zencoder.ai/blog/how-to-use-ai-in-coding

[^3_19]: https://www.youtube.com/watch?v=arn6hqERKn4


---

# Common pitfalls to avoid in AI-assisted TDD workflows

How to customize Claude Code for strict Red-Green-Refactor
Best AI tools for multi-file refactoring in 2026
Examples of AAA test pattern in VS Code with Copilot
Tradeoffs of test-first vs implementation-first with AI

Common pitfalls in AI-assisted TDD include context pollution (AI mixing impl into tests), over-trusting polished but flawed outputs, and skipping verification due to speed illusions.[^4_1][^4_2][^4_3]

## Pitfalls to Avoid

- **Insufficient context upfront**: AI misses architectural prefs, standards, or edges—provide explicit plans and examples first.[^4_2][^4_1]
- **Implementation bleed**: AI defaults to happy-path code before tests; enforce phase isolation via skills/hooks.[^4_4][^4_5]
- **Blind acceptance**: AI code looks perfect but has subtle bugs/security holes—always run tests/CI and review diffs.[^4_3][^4_1]
- **Test bloat or irrelevance**: AI generates verbose/unfocused tests; human-write key specs, let AI fill details.[^4_6][^4_7]
- **Regression neglect**: Fast iterations skip full suites—automate regression gates.[^4_4]


## Customizing Claude Code for Strict RGR

Use multi-agent skills + hooks for phase enforcement, as in community setups.[^4_5][^4_8]

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

Skills like tdd-reder (write tests), tdd-green (impl), tdd-refactorer (clean up)—block progression without proof (e.g., bash test runs).[^4_9][^4_5]

## Best AI Tools for Multi-File Refactoring (2026)

| Tool | Strengths | Best For | Pricing |
| :-- | :-- | :-- | :-- |
| Cursor | IDE speed, agent workflows, diff reviews | Solo devs, VS Code users | \$20/mo[^4_10] |
| Byteable | CI/CD autonomous refactors, enterprise governance | Monorepos, teams | Enterprise |
| Augment | Large-context agents, complex changes | Big codebases | \$30/mo[^4_10] |
| Gemini Code Assist | Multi-file/large-repo modernization | Legacy migration | Free tier+ |
| Refact.ai | Self-host, open-source control | Privacy-focused | Free/Pro[^4_10][^4_11] |

Cursor leads for your Windows/Claude/VS Code setup—handles 50k+ line monorepos well.[^4_10]

## AAA Pattern Examples (VS Code + Copilot)

AAA (Arrange-Act-Assert) is standard for Copilot TDD; use prompt files for consistency.[^4_12][^4_13]

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

Copilot Chat: `/generate-unit-tests UserService.create_user pytest`—auto-AAA with mocks.[^4_13]

## Test-First vs Impl-First Tradeoffs with AI

| Aspect | Test-First (TDD) | Impl-First |
| :-- | :-- | :-- |
| Speed | Slower start, faster iterations/debug | Faster initial code, brittle changes[^4_3][^4_7] |
| Quality | Clear specs, catches edges early, refactor-safe | Biased tests confirm impl (not behavior), hidden bugs[^4_6][^4_3] |
| AI Fit | AI excels at minimal green/impl; you own tests | AI hallucinations compound; hard to test post-hoc[^4_7][^4_2] |
| Maintenance | Living docs, regression-proof | Test debt grows fast[^4_4] |
| Best When | Complex domains, monorepos (your case) | Prototypes, trivial utils[^4_6] |

TDD wins with AI: Tests as "contract," AI as "contractor"—reduces slop by 50%+ per 2026 reports.[^4_7][^4_5][^4_3]
<span style="display:none">[^4_14][^4_15][^4_16][^4_17]</span>

<div align="center">⁂</div>

[^4_1]: https://dev.to/austinwdigital/ai-assisted-development-in-2026-best-practices-real-risks-and-the-new-bar-for-engineers-3fom

[^4_2]: https://8thlight.com/insights/tdd-effective-ai-collaboration

[^4_3]: https://www.linkedin.com/pulse/developers-compass-why-tdd-only-way-survive-ai-gold-rush-david-burns-5mkqe

[^4_4]: https://codemanship.wordpress.com/2026/01/09/why-does-test-driven-development-work-so-well-in-ai-assisted-programming/

[^4_5]: https://alexop.dev/posts/custom-tdd-workflow-claude-code-vue/

[^4_6]: https://www.linkedin.com/posts/kevinborders_test-driven-development-is-worse-than-writing-activity-7406525336051531777-1ES_

[^4_7]: https://www.linkedin.com/posts/jacek-smolak_ai-powered-tdd-why-tests-first-makes-ai-activity-7374385454889975808-EWe3

[^4_8]: https://www.perplexity.ai/search/4b07855a-5dfe-47a8-b88f-a203f22d7455

[^4_9]: https://claude-plugins.dev/skills/@NTCoding/claude-skillz/tdd-process

[^4_10]: https://www.byteable.ai/blog/top-ai-code-refactoring-tools-for-tackling-technical-debt-in-2026

[^4_11]: https://www.secondtalent.com/resources/ai-tools-for-code-refactoring-and-optimization/

[^4_12]: work.dev_environment

[^4_13]: https://code.visualstudio.com/docs/copilot/guides/test-driven-development-guide

[^4_14]: https://docs.github.com/en/copilot/tutorials/customization-library/prompt-files/generate-unit-tests

[^4_15]: https://absoluteapplabs.com/blog/ai-in-software-development-lifecycle/

[^4_16]: https://www.linkedin.com/posts/antonymarcano_aiassistedcoding-aistrategy-aiproductivity-activity-7413915230172311552-fiOE

[^4_17]: https://redolentech.com/top-5-enterprise-ai-adoption-pitfalls-in-2026/

