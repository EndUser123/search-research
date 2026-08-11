---
title: "Python-orchestrated skill build pattern: study-replicate-test"
created: 2026-08-10
source: session-019fee3d (close-py v1.0 build from ship-py pattern)
tags: [skill-design, python-orchestration, vmao-pattern, transferable-technique, anti-fabrication, code-orchestrates-model-judges, phase-registry]
summary: >
  Technique for building a new Python-orchestrated skill by replicating an
  existing one. Study the source architecture thoroughly (all source files,
  not just SKILL.md), replicate the structural pattern (_shared.py state
  management + _registry.py PhaseSpec + phases/*.py + orchestrator CLI +
  receipt validator), adapt phases to the new domain, write tests alongside
  code, and verify. Proven across ship-py (verify-and-publish) and close-py
  (session close). The study-first approach produced zero design rework
  across 18 files on the close-py build.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/code-mode-as-self-improvement-strategy.md
    type: extends — the study-replicate-test pattern is the skill-scale application of code-mode
  - target: wiki/concepts/go-structural-transformation-code-orchestration-2026.md
    type: complements — /go is exploring the same pattern for a non-pipeline orchestrator
  - target: wiki/concepts/making-llm-agents-honestly-execute-skills-solution-stack.md
    type: related — the anti-fabrication architecture both skills share
  - target: wiki/concepts/pipeline-orchestration-and-transport-reliability.md
    type: related — ship-py's specific pipeline design
  - target: wiki/concepts/liveness-vs-timeout-for-agent-pipeline-polling-loops.md
    type: related — the polling-loop pattern both skills use
---

# Python-orchestrated skill build pattern: study-replicate-test

## Decision context

**Why this knowledge was needed:** the workspace has one proven Python-orchestrated skill (ship-py) and needs more (close-py for session close, potentially /go for engineering orchestration). Building each from scratch would re-derive the same architecture decisions. Building by copying without understanding would produce cargo-cult code that breaks on edge cases the original solved. The question: what is the reliable technique for building a new Python-orchestrated skill from an existing one?

**The session that proved it:** close-py v1.0 was built by studying ship-py's source (8 files read before writing any code), then replicating the structural pattern adapted to /close's domain. Result: 18 files, 20 tests, zero design rework.

## The pattern (5 steps)

### 1. Study the source architecture (before writing any code)

Read **all** source files of the existing skill, not just SKILL.md:

- `SKILL.md` — phase list, gate matrix, invocation patterns
- `__lib/<name>_orchestrator.py` — CLI entry point, subcommand dispatch, session-id validation
- `__lib/phases/_shared.py` — state management, gate logic, tamper-evident chain, session isolation
- `__lib/phases/_registry.py` — PhaseSpec declarations (single source of truth for phase metadata)
- `__lib/phases/run_all.py` — the polling loop (how pause phases work)
- `__lib/phases/verdict.py` — how the final verdict is mechanically derived from evidence
- `__lib/phases/detect.py` — the entry phase (session scoping, file detection)
- `__lib/<name>_receipt.py` — mechanical verification (what the validator checks)

**Receipt:** session 019fee3d read these 8 files (ship-py SKILL.md, _shared.py, _registry.py, run_all.py, verdict.py, detect.py + /close SKILL.md + close_accounting.py API) before writing the first close-py file.

**Why this matters:** the load-modify-save chain semantics, the lazy import pattern in _registry.py, and the inter-phase gate logic are all non-obvious. Reading only SKILL.md would miss these. Reading _shared.py:save_state reveals that the tamper-evident chain only extends on load-modify-save cycles — a detail the test assertions initially got wrong.

### 2. Replicate the structural pattern

Copy the file structure and adapt the domain logic:

```
~/.grok/skills/<new-skill>/
  SKILL.md                           # adapted from source SKILL.md
  __lib/
    <new-skill>_orchestrator.py      # CLI entry point (adapt subcommands)
    <new-skill>_receipt.py           # mechanical verification (adapt validation)
    phases/
      _shared.py                     # near-identical (change ARTIFACTS_ROOT, REQUIRED_PRIOR)
      _registry.py                   # adapt PhaseSpec list to new domain
      detect.py                      # adapt session scoping
      <domain-phases>.py             # new phases specific to the domain
      run_all.py                     # near-identical (change env var prefixes)
      verdict.py                     # adapt verdict derivation
      abort.py                       # near-identical
  tests/
    conftest.py                      # near-identical
    test_state_and_chain.py          # near-identical
    test_verdict.py                  # adapt to new verdict logic
```

**What stays the same across skills:**
- State management (`load_state`, `save_state`, `_atomic_write_json`)
- Tamper-evident transition chain (`_transition_chain`, `validate_transition_chain`)
- Inter-phase gate logic (`_check_phase_gate`, `REQUIRED_PRIOR`)
- Session isolation (`_session_id` validation, `_get_session_files`, `_get_session_start_time`)
- Polling loop pattern (pause phases, `poll_interval`, `poll_timeout`, aggregate ceiling)
- Phase registry dataclass (`PhaseSpec`, `PhaseType`, `_build_registry`)
- Abort phase

**What changes per skill:**
- `ARTIFACTS_ROOT` — e.g., `P:/.artifacts/ship-py/` vs `P:/.artifacts/close-py/`
- `REQUIRED_PRIOR` — the phase dependency graph
- Phase implementations — domain-specific logic
- Verdict derivation — what evidence the verdict derives from
- Receipt validation — what the mechanical verifier checks
- Env var prefixes — `SHIP_PY_*` vs `CLOSE_PY_*`

### 3. Adapt phases to the new domain

This is where the study pays off. Understanding the source's phase structure lets you map the new domain's workflow onto the same pipeline shape:

| ship-py (source) | close-py (replicated) | Pattern role |
|------------------|----------------------|-------------|
| detect | detect | Identify scope, consume upstream signals |
| refactor-scan, skill-dev, auto-fix, secret-scan | scan | Domain-specific analysis |
| review, risk, fix | resolve, handoff-resolve, accounting | LLM judgment (pause phases) |
| verify, trace, doc-check | coverage, git-state | Mechanical verification |
| verdict | verdict | Derive terminal verdict from evidence |
| merge, publish, babysit | (none — close has no post-verdict) | Optional post-verdict phases |

**Key decision: how many pause phases?** ship-py has 1 pause phase (fix). close-py has 3 (resolve, handoff-resolve, accounting). The number depends on how many phases require genuine LLM judgment vs deterministic code.

### 4. Write tests alongside code

Test the structural patterns (state, chain, gates) with near-identical tests from the source skill. Test the domain-specific logic (verdict derivation, receipt validation) with new tests adapted to the new domain.

**Critical chain semantics to test:**
- The tamper-evident chain only extends on `state = load_state(id); state["x"] = y; save_state(id, state)` cycles — NOT on `save_state(id, {"fresh": "dict"})` calls
- Direct state writes (bypassing `save_state`) break the chain and are detectable
- Inter-phase gates check `completed_phases`, not the `phase` field

**Receipt:** session 019fee3d wrote 20 tests for close-py. 3 failed on the first run because the test assertions didn't match the chain semantics — the tests assumed fresh-dict saves extend the chain, but they don't.

### 5. Verify (ruff, tests, CLI, integration)

- `ruff check` — lint all Python files
- `python -m pytest tests/ -v` — run all tests
- `python <orchestrator>.py --help` — verify CLI entry point
- `python -c "from phases._registry import REGISTRY, PHASE_ORDER, PAUSE_PHASES"` — verify registry builds
- Run `detect` on a real session to verify integration with domain scanners

## What this means for our workspace

1. **Future Python-orchestrated skills can be built in one session** by following this 5-step pattern. The structural code (_shared.py, _registry.py, run_all.py, abort.py) is near-identical; only the domain phases change.

2. **The phase registry pattern is the key structural innovation.** Adding a phase = one PhaseSpec entry in _registry.py. No other file changes. This is proven across ship-py (20 phases) and close-py (8 phases).

3. **Anti-fabrication architecture is portable.** The tamper-evident chain, inter-phase gates, and mechanical verdict derivation work identically regardless of domain. They enforce "Python controls the loop, LLM handles judgment" without domain-specific logic.

4. **The shared module extraction is deferred to v2.** When a 3rd Python-orchestrated skill confirms the pattern, extract `_shared.py` + receipt patterns to `~/.grok/__lib/__anti_fabrication__`. Until then, duplication is safer than premature abstraction.

## Close-py design decisions (worked example)

Four architectural decisions were made during the close-py build:

| Decision | Rationale | Steelman (rejected alternative) | Falsifier |
|----------|-----------|--------------------------------|-----------|
| **Coexist with /close** | Both import the same /close scanners; operator chooses which to invoke | Replace /close: would force all existing /close users to migrate; no benefit since both use the same scanners | If operators consistently choose one over the other, the unused one should be retired |
| **ship-py verdict is optional** | Doesn't block close when ship-py didn't run; notes as advisory | Required when code changed: would force ship-py dependency for doc-only sessions | If missing ship-py verdict consistently leads to close-py declaring COMPLETE on buggy code, make it required |
| **Duplicate for v1** | Avoid premature abstraction; extract when pattern is proven by 3rd skill | Extract now: would require touching ship-py (active skill with open bugs) to refactor shared code | If a 3rd skill builds using the same pattern, extract at that point |
| **8-phase pipeline** | Python-controlled phase ordering prevents LLM skipping phases | Fewer phases (merge resolve+coverage): would lose the separation between gate resolution and coverage checking | If phases consistently pass without work (all pre_satisfied on first scan), merge them |

## Receipts

Implementation paths for mechanism claims in this concept:

- **State management + tamper-evident chain:** `~/.grok/skills/ship-py/__lib/phases/_shared.py:save_state()` (lines 228-265), `validate_transition_chain()` (lines 278-321). Replicated at `~/.grok/skills/close-py/__lib/phases/_shared.py:save_state()`, `validate_transition_chain()`.
- **Load-modify-save chain semantics:** `~/.grok/skills/close-py/__lib/phases/_shared.py:save_state()` — the chain entry is appended from `state.get("_transition_chain", [])` which is only populated when the state dict was previously loaded via `load_state()`. Fresh dicts passed to `save_state()` produce a genesis entry but don't extend an existing chain. Verified by test `test_chain_valid_after_normal_save` in `~/.grok/skills/close-py/tests/test_state_and_chain.py`.
- **Phase registry (single source of truth):** `~/.grok/skills/ship-py/__lib/phases/_registry.py:_PHASE_SPECS` (lines 48-310), `_build_registry()` (lines 314-365). Replicated at `~/.grok/skills/close-py/__lib/phases/_registry.py:_PHASE_SPECS`, `_build_registry()`.
- **Inter-phase gate logic:** `~/.grok/skills/close-py/__lib/phases/_shared.py:_check_phase_gate()` — checks `state.get("completed_phases", [])` against `REQUIRED_PRIOR[current_phase]`. The `phase` field tracks the NEXT phase and cannot be used for gating.
- **Polling loop (run-all):** `~/.grok/skills/ship-py/__lib/phases/run_all.py:cmd_run_all()` (lines 69-399). Replicated at `~/.grok/skills/close-py/__lib/phases/run_all.py:cmd_run_all()`.
- **Mechanical verdict derivation:** `~/.grok/skills/close-py/__lib/phases/verdict.py:cmd_verdict()` — derives CLOSE COMPLETE / CLOSE INCOMPLETE from gate states, coverage results, git checks, and accounting. Does not accept self-declared verdicts.
- **close-py full implementation:** commit `b6434f8` on `~/.grok` main, session 019fee3d (2026-08-10).
- **close-py tests:** `~/.grok/skills/close-py/tests/test_state_and_chain.py` (12 tests), `~/.grok/skills/close-py/tests/test_verdict.py` (8 tests). All 20 passing.

## Falsifier
- A 3rd Python-orchestrated skill requires fundamentally different architecture (e.g., the domain doesn't fit the detect→scan→resolve→verdict pipeline shape)
- The duplicated _shared.py files drift so far apart that extraction becomes impossible (the copy-paste tax exceeds the abstraction cost)
- The study-first approach doesn't scale — for larger source skills, reading all files becomes impractical

**When to re-evaluate:** after building a 3rd Python-orchestrated skill, or when ship-py's _shared.py diverges from close-py's by >50 lines.

## Sources

- Session 019fee3d (2026-08-10) — close-py v1.0 build. Commit `b6434f8` (~/.grok).
- [[code-mode-as-self-improvement-strategy]] — the skill-scale application of code-mode
- [[pipeline-orchestration-and-transport-reliability]] — ship-py's specific pipeline design
- [[making-llm-agents-honestly-execute-skills-solution-stack]] — anti-fabrication architecture both skills share
- [[liveness-vs-timeout-for-agent-pipeline-polling-loops]] — polling-loop design
- [[polling-loop-continuation-controller-design-decision]] — why polling loop was chosen over daemon/Rhai/HMAC

