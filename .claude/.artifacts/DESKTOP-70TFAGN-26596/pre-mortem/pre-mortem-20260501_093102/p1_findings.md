## Triage Classification
code/hook — Hook budget coordination changes to 5 existing UPS pipeline modules

## Dispatched Specialists
- adversarial-logic: Budget decrement-before-return consistency across modules
- adversarial-compliance: SAFETY_MODULES variable scoping, exit code handling
- adversarial-quality: Maintainability, code structure, variable scoping bugs
- adversarial-testing: Test coverage gaps for budget flow, thresholds, trace logging

## Specialist Findings Summary

### adversarial-logic
**Domain:** Budget decrement-before-return consistency
**Key findings:**
- [HIGH] reasoning_mode_selector early return (lines 74-76) does NOT decrement budget, unlike cognitive_enhancers which DOES — creates inconsistent skip-cost behavior (source: adversarial-logic)
- [HIGH] reasoning_mode_selector "reasoning not required" path (line 103-105) also doesn't decrement budget even after consuming analysis budget (source: adversarial-logic)
- [MEDIUM] Three different skip-cost behaviors across modules makes final_budget unreliable for cost comparison (source: adversarial-logic)
- [LOW] Work.md line references don't match actual code line numbers (source: adversarial-logic)

### adversarial-compliance
**Domain:** Variable scoping, SAFETY_MODULES contract, hook registration
**Key findings:**
- [HIGH] **NameError bug**: `budget` assigned INSIDE `if _mod_name not in SAFETY_MODULES` block but used AFTER it at line ~158. If module IS in SAFETY_MODULES, budget is never defined → NameError. Same bug in all 3 modules (reasoning_mode_selector, cognitive_enhancers, testing_strategy_router) (source: adversarial-compliance)
- [HIGH] Same NameError bug in cognitive_enhancers.py (lines 437-480) (source: adversarial-compliance)
- [HIGH] Same NameError bug in testing_strategy_router.py (lines 98-114) (source: adversarial-compliance)
- [LOW] direct_answer_hint is set in context but no consumer module documented (source: adversarial-compliance)

### adversarial-quality
**Domain:** Code structure, variable scoping, maintainability
**Key findings:**
- [HIGH] **Undefined budget variable**: Same NameError root cause as COMP-001 — budget fetched inside guard conditional, used outside it (reasoning_mode_selector line 72 vs 158) (source: adversarial-quality)
- [HIGH] Same undefined budget in testing_strategy_router (lines 99, 114) (source: adversarial-quality)
- [MEDIUM] cognitive_enhancers has structurally inconsistent budget fetch (inside guard vs at decrement) — functionally correct but confusing (source: adversarial-quality)
- [MEDIUM] Budget trace logging silently swallows all exceptions with bare `except: pass` — operators get no indication of failure (source: adversarial-quality)

### adversarial-testing
**Domain:** Test coverage for budget coordination
**Key findings:**
- [HIGH] Missing integration test: no test covers full budget lifecycle: unified_detection → reasoning → cognitive → testing (source: adversarial-testing)
- [HIGH] No boundary tests: guards use `budget < 400` but no tests at exact threshold (399, 400, 401) (source: adversarial-testing)
- [HIGH] Budget trace logging has zero test coverage — if logging fails silently, operational diagnostics are lost (source: adversarial-testing)
- [MEDIUM] direct_answer_hint computed but never consumed — dead code in data flow (source: adversarial-testing)
- [MEDIUM] cognitive_enhancers injection length not verified against actual decrement amount (source: adversarial-testing)
- [MEDIUM] _is_actionable_prompt early-exit paths untested (source: adversarial-testing)
- [LOW] Tokenization ratio 4x assumed, not measured (source: adversarial-testing)
- [LOW] testing_strategy_router._classify_test_style has unreachable code path (line 59 early return bypasses regex checks) (source: adversarial-testing)

## Consolidated Findings

### Logical Gaps & Inconsistencies
1.1. [HIGH] (source: adversarial-compliance, adversarial-quality) — NameError bug: `budget` defined at line 72 inside `if _mod_name not in SAFETY_MODULES:` but used at line 158 after the if-block exits. If module IS in SAFETY_MODULES, budget is never assigned. Fix: move `budget = context.data.get("remaining_budget", 20000)` BEFORE the safety check. Same bug in cognitive_enhancers.py (line 438 inside guard, used at 480) and testing_strategy_router.py (line 99 inside guard, used at 114).
1.2. [HIGH] (source: adversarial-logic) — reasoning_mode_selector early return at lines 74-76 does not decrement remaining_budget, unlike cognitive_enhancers which decrements before returning empty. Creates inconsistent skip-cost behavior: cognitive_enhancers charges its skip cost, reasoning_mode_selector does not.
1.3. [HIGH] (source: adversarial-logic) — reasoning_mode_selector "reasoning not required" path at lines 103-105 returns empty without decrementing budget, despite having consumed budget for analysis. testing_strategy_router always decrements on its path; reasoning_mode_selector never does.

### Hidden Assumptions & Fragile Dependencies
2.1. [MEDIUM] (source: adversarial-compliance) — direct_answer_hint is set in context.data but no module in the reviewed 5 files consumes it. If intended to gate modules or adjust budget, that logic is absent.
2.2. [MEDIUM] (source: adversarial-testing) — Tokenization ratio 4 chars/token is assumed but never measured. For technical content with long identifiers, actual ratio may differ significantly.
2.3. [LOW] (source: adversarial-logic) — Work.md section 4 claims "Budget decrement before return" for both CONDITIONAL_MIN modules, but only cognitive_enhancers actually implements it.

### Missing Obvious Actions / Best Practices
3.1. [HIGH] (source: adversarial-testing) — Add integration test covering full budget sequence: unified_detection initializes → each module decrements → trace logged. No single test exercises the end-to-end flow.
3.2. [HIGH] (source: adversarial-testing) — Add boundary value tests: budget=399 (should skip), budget=400 (should run), budget=401 (should run) for 400-char threshold.
3.3. [HIGH] (source: adversarial-testing) — Add test for budget trace logging: invoke main() with known input, verify ups_budget_trace.jsonl contains correct fields.
3.4. [MEDIUM] (source: adversarial-testing) — Add test that _build_injection returns known-length string and verifies budget decremented by exact amount.
3.5. [MEDIUM] (source: adversarial-quality) — Budget trace logging fails silently. Add warning to stderr so operators notice tracking failures without breaking the pipeline.

### Risks and Edge Cases
4.1. [HIGH] (source: adversarial-compliance) — If any of these 3 modules are ever added to SAFETY_MODULES, they will crash with NameError at the decrement site. Latent time bomb.
4.2. [MEDIUM] (source: adversarial-logic) — With budget=300: reasoning_mode_selector skips (no decrement), cognitive_enhancers skips (decrements), final_budget differs by injection length even though both skipped. Makes per-module cost comparison unreliable.
4.3. [MEDIUM] (source: adversarial-testing) — If skip_skills config changes (e.g., /search removed), no test alerts. Critical hooks could be bypassed unintentionally.

### Concrete Recommendations
5.1. [HIGH] (source: adversarial-compliance, adversarial-quality) — Fix budget scoping in all 3 modules: move `budget = context.data.get("remaining_budget", 20000)` outside the `if _mod_name not in SAFETY_MODULES:` block, before any conditional. Then change guard to: `if _mod_name not in SAFETY_MODULES and budget < min_chars:`.
5.2. [HIGH] (source: adversarial-logic) — Add `context.data["remaining_budget"] = budget` before early return at reasoning_mode_selector lines 74-76 to match cognitive_enhancers behavior.
5.3. [HIGH] (source: adversarial-testing) — Add integration test for full budget lifecycle.
5.4. [HIGH] (source: adversarial-testing) — Add boundary value tests for threshold checks.
5.5. [MEDIUM] (source: adversarial-quality) — Add stderr warning when budget trace logging fails: `print(f"[UserPromptSubmit] Budget trace failed: {e}", file=sys.stderr)` instead of bare `pass`.
5.6. [MEDIUM] (source: adversarial-testing) — Verify or remove direct_answer_hint consumer. If no consumer exists, remove the field or document its purpose.

### Open Questions / Unknowns
6.1. [MEDIUM] (source: adversarial-compliance) — Is it intentional that adding a module to SAFETY_MODULES would crash? The design intent seems to be that safety modules skip budget entirely — but the current code structure makes this untested and dangerous.
6.2. [MEDIUM] (source: adversarial-logic) — Should skipped modules bear a "skip cost" (decrement budget even with no injection) or be budget-neutral? Current implementation has three different answers.
6.3. [LOW] (source: adversarial-testing) — What tokenization ratio does the actual LLM use for technical prompts? 4x may be over- or under-estimating.
