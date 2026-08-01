---
title: "Predictable code problems: Python 3.14, AI-generated code, and detection methods"
created: 2026-07-25
source: session-019f94c9
tags: [code-quality, predictable-bugs, python-314, ai-generated-code, static-analysis, verification, code-review, testing]
summary: >
  Three categories of predictable code problems and how to detect them. (1) Detection
  methods: the toolchain from linters to behavioral testing. (2) Python 3.14 specific
  gotchas: deferred annotations, locals() semantics, removed features, GC reversion.
  (3) AI-generated code patterns: 5 recurring bug classes with 1.7x baseline defect rate.
  Each category has known detection strategies — the key insight is that different bug
  classes need different detection methods, and no single tool covers all.
agent: grok
host: grok
cognitive_load: 4
verification: multi-source-verified
sources:
  - https://nimbalyst.com/blog/bugs-ai-writes-patterns-in-ai-generated-code/
  - https://www.shiplight.ai/blog/ai-generated-code-has-more-bugs
  - https://blog.codercops.com/blog/python-3-14-whats-new-2026
  - https://docs.python.org/3/whatsnew/3.14.html
  - https://pub.towardsai.net/python-3-13-3-14-are-breaking-backward-compatibility-on-purpose-b6c7d7351336
  - https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report
  - https://www.gitclear.com/ai_assistant_code_quality_2025_research
  - https://arxiv.org/html/2512.05239v1
relations:
  - target: wiki/concepts/python-314-315-features-we-should-use.md
    type: complements
  - target: wiki/concepts/ai-agent-verification-orchestration-best-practices-2026.md
    type: related
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: related
---

# Predictable code problems: detection, Python 3.14, and AI-generated code

## Decision context

**Why this research was needed:** the operator asked "how do we find predictable problems in code?" with specific interest in Python 3.14 and AI-generated code. This page consolidates three independent research streams into a single reference for what to look for and how to catch it.

## Part 1: How to find predictable problems (the detection toolchain)

No single tool catches everything. Different bug classes need different detection methods:

| Bug class | Best detection method | Why |
|-----------|----------------------|-----|
| Type errors, undefined names | **Static type checker** (mypy, pyright) | Catches before runtime |
| Style violations, unused imports | **Linter** (ruff, pylint) | Fast, deterministic |
| Dead code, unreachable branches | **Static analysis** (vulture, ruff) | Structural, no execution needed |
| Security vulnerabilities | **SAST** (bandit, semgrep, CodeQL) | Pattern-matches known vuln classes |
| Logic errors, wrong behavior | **Behavioral/integration tests** | Must run the code |
| Contract violations | **Contract tests at boundaries** | Pins interfaces, not internals |
| AI-specific patterns (see Part 3) | **Code review at interfaces + behavioral tests** | Static tools miss these |

### The 2026 tool landscape (Python)

| Tool | Role | Speed | Python 3.14 | Key strength |
|------|------|-------|-------------|--------------|
| **Ruff** | Linter + formatter | Rust-fast, ~100x pylint | ✅ | Replaces flake8 + isort + pylint in one tool |
| **Pyright** | Type checker | Fast (Node.js) | ✅ | Best-in-class inference, VS Code integration |
| **mypy** | Type checker | Moderate | ✅ | Most mature, strict mode |
| **Astral type checker** | Type checker (new) | Rust-fast | TBD | Being built by ruff/uv team; not yet released |
| **Bandit** | Security scanner | Fast | ✅ | OWASP pattern matching |
| **Semgrep** | Pattern-based SAST | Fast | ✅ | Custom rules, multi-language |
| **Vulture** | Dead code finder | Fast | ✅ | Finds unreachable code |
| **SonarQube** | Enterprise quality platform | Slow | ✅ | Quality gates, technical debt tracking |

**Key trend (2026):** Ruff is consolidating the Python linter ecosystem. The Astral team (ruff + uv) is building a new type checker in Rust that may replace mypy/pyright for many use cases. The pattern mirrors what happened with linters — one fast, well-funded tool absorbing the fragmented ecosystem.

### The detection hierarchy (what to run when)

```
1. Linter (ruff)          — every save, <100ms
2. Type checker (pyright)  — every save, <1s
3. Unit tests              — every commit
4. Integration tests       — every PR
5. Security scan (semgrep) — every PR
6. Behavioral/E2E tests    — every PR (critical for AI-generated code)
7. Code review             — every PR (focus on interfaces, not internals)
```

The hierarchy is cost-ordered: cheap checks run first and catch the easy bugs. Expensive checks (E2E, human review) run last and catch what the cheap checks miss.

## Part 2: Python 3.14 predictable problems

### Breaking changes that cause silent failures

These are the highest-risk 3.14 changes because they don't produce errors — they change behavior:

**1. Deferred annotation evaluation (PEP 649/749)**
- **What changed:** annotations are no longer evaluated eagerly at class/function definition time. They're stored as deferred objects that evaluate lazily.
- **What breaks:** metaclass patterns that inspect annotations at class creation time. Code that does `typing.get_type_hints()` and expects immediate evaluation. Some Pydantic versions (pre-2.x) may fail.
- **Detection:** run `python -W error::DeprecationWarning` against your test suite on 3.12/3.13 first. Test `typing.get_type_hints()` on all models.
- **Failure mode:** lazy evaluation that doesn't error until the annotation is accessed, shifting when errors surface in your test suite.

**2. `locals()` semantics changed (PEP 667)**
- **What changed:** `locals()` now returns a real mapping that reflects current state, not a snapshot.
- **What breaks:** code that modified the `locals()` dict expecting no effect, or expected it to be a snapshot. Debuggers and profilers that relied on the old implementation-specific behavior.
- **Detection:** grep for `locals()` usage and audit each call site.

**3. `int()` no longer delegates to `__trunc__()`**
- **What changed:** `int(obj)` used to call `obj.__trunc__()` as a fallback. Now it requires `__int__()` or `__index__()`.
- **What breaks:** custom numeric classes that only implemented `__trunc__()`.
- **Detection:** grep for `__trunc__` in your codebase.

**4. `NotImplemented` in boolean context raises `TypeError`**
- **What changed:** `if x == y:` where `__eq__` returns `NotImplemented` now raises instead of falling through.
- **What breaks:** custom comparison methods that return `NotImplemented` and rely on truthiness checks.
- **Detection:** grep for `NotImplemented` in comparison contexts.

**5. Incremental GC reverted to generational (3.14.5+)**
- **What changed:** 3.14.0-3.14.4 had incremental GC (reduced pause times). 3.14.5+ reverted to generational GC due to memory pressure reports.
- **What breaks:** code tuned for incremental GC pause patterns may see different latency characteristics. Not a correctness issue, but a performance regression.
- **Detection:** benchmark on 3.14.5+, not 3.14.0.

**6. `pickle` default protocol changed to 5**
- **What changed:** default pickle protocol bumped from 4 to 5.
- **What breaks:** pickled data exchanged with older Python versions (3.7 and earlier) may fail to unpickle.
- **Detection:** test pickle round-trips against older Python versions if you exchange pickled data.

**7. Removed features from 3.10-3.12**
- Many long-deprecated features were removed. Run `python -W error::DeprecationWarning` on 3.12/3.13 before upgrading.
- C extensions may need recompilation — check wheel availability on PyPI.

**8. Free-threaded build (3.14t) overhead**
- The free-threaded build has 3-8% single-threaded overhead vs standard build.
- Not a bug, but a predictable performance regression for single-threaded workloads.
- Don't default-switch to `python3.14t` without benchmarking.

### Python 3.14 detection checklist

```bash
# 1. Check for deprecated features
python -W error::DeprecationWarning -m pytest

# 2. Check for __trunc__ usage
rg "__trunc__" --type py

# 3. Check for locals() modification
rg "locals\(\)" --type py

# 4. Check for NotImplemented in comparisons
rg "NotImplemented" --type py

# 5. Verify typing.get_type_hints() works on all models
python -c "import typing; typing.get_type_hints(MyModel)"

# 6. Check pickle compatibility
python -c "import pickle; pickle.loads(pickle.dumps(test_obj), protocol=4)"

# 7. Benchmark on 3.14.5+ (not 3.14.0)
```

## Part 3: AI-generated code predictable problems

### The data (2025-2026)

| Metric | AI code vs human code | Source |
|--------|-----------------------|--------|
| Overall issue rate | **1.7x more** issues per PR | CodeRabbit (470 PRs, Dec 2025) |
| Logic & correctness errors | **+75%** | CodeRabbit |
| Readability issues | **+3x** | CodeRabbit |
| Error handling gaps | **+2x** | CodeRabbit |
| Security vulnerabilities | **+2.74x** | CodeRabbit |
| Bug rate increase (Copilot) | **+41%** | Uplevel (800 developers) |
| Code duplication | **8x increase** | GitClear (211M lines) |
| Code churn (rewritten within 2 weeks) | **3.1% → 5.7%** | GitClear |
| "Looks correct but isn't reliable" | **61% of developers agree** | Multiple surveys |
| Silent failures (pass tests, wrong results) | **60% of AI code faults** | VentureBeat/ByteIota |

### The 5 predictable bug patterns

**Pattern 1: Plausible but wrong logic**
- AI optimizes for the happy path. Handles common cases; misses implicit conventions, timezone handling, null behavior, business rules.
- Example: date parsing uses US format (04/05 = April 5) when codebase convention is ISO 8601 (April 5 = 05/04). No error, just wrong data.
- **Detection:** review like reviewing code from a smart contractor who just joined — check assumptions about data formats, timezone, null/undefined, implicit business rules. Behavioral tests catch these; unit tests don't.

**Pattern 2: Confident refactoring that breaks callers**
- AI makes a module internally cleaner while subtly changing the contract. Renamed parameters, changed return types (returning None where it used to throw), modified defaults.
- The refactored module looks great in isolation. The bug is three files away.
- **Detection:** when reviewing a refactor, grep for every caller of the changed interface. Check error handling paths and default values. TypeScript/pyright catches signature changes; behavioral tests catch semantic changes.

**Pattern 3: Tests that test the implementation, not the behavior**
- AI writes tests that mirror the implementation — they pass by construction, not by correctness. Expected values copied from function output. Over-mocked tests that validate the mocking framework, not the code.
- **Detection:** for each test, ask: "would this fail if the function returned a hardcoded value?" If no, the test is useless. Favor integration tests over unit tests for AI-generated code.

**Pattern 4: Copy-paste drift across similar components**
- AI creates multiple similar components by copying the first. Small variations creep in: one validates input, the other doesn't. One handles errors, the other swallows them.
- Each component in isolation looks fine. The inconsistency is only visible side-by-side.
- **Detection:** when AI creates multiple similar things, diff them against each other. Any unintentional difference is a bug. Extract to shared abstraction.

**Pattern 5: Dependency and import sprawl**
- AI installs packages unnecessarily. Adds a full date library when the project already has one. Imports lodash for a one-liner.
- Creates duplicate functionality: two date libraries with slightly different APIs, leading to inconsistent behavior.
- **Detection:** review imports in AI-generated code. If a new dependency was added, check if the project already has one that does the same thing. Document preferred libraries in AGENTS.md/CLAUDE.md.

### The 4 failure modes (from CodeRabbit data)

| Failure mode | What happens | What catches it |
|-------------|-------------|-----------------|
| **Intent inversion** | Code does the literal opposite of requested | Behavioral tests (run the flow, check outcomes) |
| **Dropped safeguards** | Happy path clean, defensive logic silently removed | Re-verify every user flow the changed file touches |
| **Contextual mismatch** | Statistically likely code that doesn't fit your codebase | Code review at boundaries + linting for conventions |
| **Silent pass** | Passes every test AND is still wrong | Behavioral coverage, not line coverage |

### Detection strategy for AI-generated code

The key insight from all sources: **the missing feedback loop is the root cause.** When AI writes code, humans skip steps 2-4 (run locally, click through UI, verify behavior). The 1.7x bug multiplier comes from the missing verification, not from AI writing worse code in absolute terms.

```
Traditional flow:  write → run → click through → test → push
AI flow:           prompt → review diff → push
                     ^--- steps 2-4 vanished
```

**The fix is not "review harder." It's "automate the verification that humans skip":**

1. **Behavioral coverage over line coverage** — measure "did the user-facing behavior get verified?" not "did this line execute?"
2. **Re-verify on every AI diff, not just per PR** — every file the AI touches is untested until re-verified
3. **Contract tests at service boundaries** — pin interfaces so AI refactors can't silently change contracts
4. **Human review reserved for security and business logic** — automated tests handle functional correctness; humans handle what AI can't reason about (threat models, auth rules, compliance, business logic edge cases)
5. **Document everything** — conventions, data formats, preferred libraries, business rules. More documented context = fewer "plausible but wrong" bugs.

## What this means for our workspace

Our workspace already implements several of these detection strategies:
- `/check` and `/review` provide multi-concern verification
- `validate_verdict_consistency.py` and `validate_close_receipt.py` are mechanical enforcement gates
- AGENTS.md documents preferred tools and conventions
- The receipt rule catches fabricated claims
- `/tp` provides fresh-lens critique

**Gaps to consider:**
- No static analysis gate (ruff/pyright) in our workflow — we rely on manual review
- No behavioral testing framework — we test via `/check` subagents running code, which is closer to integration testing than unit testing
- No contract testing at skill boundaries — skill contracts are documented in SKILL.md but not mechanically enforced (except for `/check`'s output validator)
- The AI-generated code patterns (Part 3) apply to our own code — we are an AI generating code about AI code quality

## Sources

- [Nimbalyst: The Bugs AI Writes — 5 Patterns](https://nimbalyst.com/blog/bugs-ai-writes-patterns-in-ai-generated-code/) (Apr 2026)
- [Shiplight: AI-Generated Code Has 1.7x More Bugs](https://www.shiplight.ai/blog/ai-generated-code-has-more-bugs) (Jul 2026)
- [CodeRabbit: State of AI vs Human Code Generation](https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report) (Dec 2025, 470 PRs)
- [GitClear: AI Copilot Code Quality 2025](https://www.gitclear.com/ai_assistant_code_quality_2025_research) (211M lines)
- [Python 3.14 What's New](https://docs.python.org/3/whatsnew/3.14.html)
- [CoderCops: Python 3.14 What's New](https://blog.codercops.com/blog/python-3-14-whats-new-2026) (May 2026)
- [Towards AI: Python 3.13-3.14 Breaking Backward Compatibility](https://pub.towardsai.net/python-3-13-3-14-are-breaking-backward-compatibility-on-purpose-b6c7d7351336)
- [arXiv: A Survey of Bugs in AI-Generated Code](https://arxiv.org/html/2512.05239v1) (Dec 2025)
- [Uplevel: Copilot 41% bug increase](https://www.allsides.com/news/2024-10-02-1215/technology-study-developers-using-ai-coding-assistants-suffer-41-increase-bugs) (800 developers)
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
