---
title: "Refactoring discipline: TDD, parallel seams, and verification gates — /refactor vs /go design validation"
created: 2026-07-30
source: session-2026-07-30 (/www research on how /refactor takes advantage of TDD, task decomposition, checks/reviews vs /go)
tags: [refactoring, tdd, characterization-testing, parallel-execution, verification-gates, skill-design, refactor-skill, go-skill, dsm, semantic-conflict]
agent: grok
host: both
cognitive_load: 4
verification: multi-source-verified
summary: >
  External research validates three design decisions in our /refactor and /go
  skills: (1) /refactor's "when practical" TDD is the correct discipline for
  behavior-preserving refactoring — characterization tests (green-starting),
  not red-first, are what refactoring theory prescribes; (2) parallel seam
  execution is safe when seams are verified independent via dependency/DSM
  analysis, but semantic conflicts (not just file-level) are the hidden risk;
  (3) our verification gates are solid but have identifiable gaps for
  legacy/untested code. The integration path /go refactor → loads /refactor +
  layers horsepower is externally validated: serial is safest for moderate
  changes, parallel adds value for multi-file independent seams with worktree
  isolation.
relations:
  - target: wiki/concepts/parallel-safe-solution-decomposition
    type: extends
  - target: wiki/concepts/agentic-sdlc-skill-lifecycle-architecture
    type: related
  - target: wiki/concepts/code-verification-pipeline-gaps
    type: extends
  - target: wiki/concepts/verification-before-completion-principle
    type: related
---

## Decision context

**The problem:** The operator asked "how will /refactor take advantage of TDD, agent task decomposition, built-in checks and reviews?" after a session where /refactor was recommended over /go for a multi-file refactoring plan. The prior self-assessment concluded /refactor has lighter discipline than /go (no mandatory TDD red, no parallel fan-out, no multi-lens reasoning, no check-work). The question was whether this is a design flaw or domain-correct.

**What alternatives were explored:**
- Whether /refactor's "when practical" TDD is too weak (should it be mandatory like /go's plan-execute?)
- Whether serial seam execution is a bottleneck that /go's H4 parallelism should always replace
- Whether /refactor's verification gates are sufficient or missing critical checks

**What the research changed:** Confirmed that /refactor's lighter TDD is domain-correct (not a flaw), validated that parallel execution is the real gap worth closing, and identified specific verification gate gaps for legacy code. The conclusion that `/go refactor` is the stronger choice for multi-file plans was confirmed — but for a different reason than the transcript stated (not "TDD," but "parallel execution + multi-lens reasoning").

## Finding 1: "When practical" TDD is the CORRECT discipline for refactoring

**Confidence: [HIGH]** — 5 independent sources agree, disconfirmation pass found no refuting evidence.

The key distinction the research surfaced:

| Testing discipline | When to use | Test start state |
|---|---|---|
| **TDD red-green-refactor** | Adding NEW behavior (feature implementation) | RED (write failing test first) |
| **Characterization tests** (Feathers) | Refactoring EXISTING code to preserve behavior | GREEN (capture current behavior, keep green throughout) |
| **Golden-master / snapshot** | Refactoring code with complex/unknown outputs | GREEN (capture output snapshot, diff after refactor) |

Michael Feathers' "Working Effectively with Legacy Code" is the canonical source: characterization tests start **green** because they document what the code currently does, not what it should do. For a pure structural extract (no behavior change), there is nothing to "go red" on — the test suite should stay green before, during, and after the refactor.

**Implication for our skills:**
- `/refactor` Step 6.3 ("fail-then-pass when practical; pure extract: suite green") is **correct** — it matches Feathers' characterization-testing discipline.
- `/go` plan-execute profile ("skipping red is a verify FAIL") is correct **for feature implementation**, but would be **wrong** to apply to pure refactoring. The mandatory-red rule is domain-specific to TDD-for-features, not TDD-for-refactoring.
- The transcript's framing that /refactor's TDD is "lighter" than /go's is misleading — it's not lighter, it's a **different discipline** appropriate to a different task type.

**Sources:** Feathers (characterization tests), cloudamite.com/characterization-testing, blog.nimblepros.com (snapshot testing), drcodes.com (Feathers feasibility analysis), learnixo.io (TDD critique for pure refactors).

## Finding 2: Parallel seam execution — safe when verified independent, with a hidden risk

**Confidence: [HIGH]** — 7 sources agree on the safety conditions; disconfirmation surfaced one qualification (semantic conflicts).

The research identified a clear decision framework for serial vs parallel refactoring:

### When parallel is safe

| Condition | Evidence |
|---|---|
| Seams touch **different files** with no shared symbols | SANER 2019 empirical study (3000 Java repos) — different-file changes have low conflict rates |
| Seams are **commutative** (order doesn't matter, deterministic end-state) | Fowler's ParallelChange pattern |
| Dependency matrix (DSM) shows **no edges** between seams | Steward's DSM partitioning (MIT) |
| Each seam operates in its own **worktree** with branch isolation | Cursor 2026 parallel subagents; our grok-parallel skill |

### When serial is required

| Condition | Evidence |
|---|---|
| Seams share the **same import graph** or module | understandlegacycode.com — concurrent changes to same module must be serial |
| One seam's output is another's **input** (e.g., create shared module → then migrate files to import it) | DSM: sequential dependency edge |
| Seams perform **method extraction, class moving, or renaming** in overlapping areas | SANER 2019 — these operations have highest merge-conflict rates |

### The hidden risk: semantic conflicts (not just file conflicts)

**This is the qualification the disconfirmation pass surfaced.** Two seams can touch different files and still conflict semantically:

- Seam A adds a new import to `__init__.py`; Seam B also adds a different import to the same `__init__.py` — text-merge succeeds but both changes must be present.
- Seam A changes a function signature; Seam B calls that function from a different file — text-merge succeeds but the call breaks at runtime.
- Seam A extracts a class to a new module; Seam B's file imports from the old location — breaks silently.

Text-based git merge cannot detect these. Semantic conflict detection tools (TIM, semantic-git-conflict-resolver) exist precisely for this gap. For our fleet: **parallel seams must be checked for semantic dependencies (shared imports, shared symbols, caller-callee relationships), not just file-level non-overlap.**

### Applied to the operator's C1 case (7 files → shared imports)

The transcript said "7 independent file migrations could run as parallel subagents." The research validates this — **with one prerequisite**: the shared import module must be created FIRST (sequential), then the 7 migrations can parallelize IF each file is truly independent (no migrating file imports from another migrating file).

This is a DSM-identified sequential dependency: `create_shared_module → [parallel: migrate_file_1, migrate_file_2, ..., migrate_file_7]`.

**Sources:** Fowler ParallelChange, SANER 2019 (merge conflicts in refactoring), sarahnadi.org (operation-based refactoring-aware merging), understandlegacycode.com, mindstudio.ai (parallel agentic development with worktrees), softwareengineering.stackexchange.com, semantic-git-conflict-resolver (GitHub).

## Finding 3: Verification gates — solid foundation, identifiable gaps

**Confidence: [MEDIUM]** — gates are well-documented in literature; applicability to our context is conditional on risk class.

### What /refactor already has (validated as sufficient for S/M-risk seams)

| Gate | /refactor step | External validation |
|---|---|---|
| Per-seam verify commands | Step 6.6 | Industry standard — every source agrees tests must run after each change |
| Definition completeness (grep callers) | Step 6.5 | Catches the #1 LLM refactoring failure: missing callers (Ottenhof et al. 2026) |
| Complexity check (radon cc) | Step 6.5 | Unique strength — most tools don't check complexity regression |
| Stale re-check (re-read before edit) | Step 6.2 | Addresses the multi-agent shared-filesystem hazard |
| End-to-end verification for I/O | Step 6.6b | Catches unit-test-passes-but-integration-breaks |

### Gaps worth closing (conditional on risk class)

| Gap | When it matters | Effort | Priority |
|---|---|---|---|
| **Characterization tests for untested modules** | L-risk seams on legacy code without unit tests | Medium — generate characterization tests before refactoring | High for legacy; skip for tested code |
| **Mutation testing** (mutmut, cosmic-ray) | When you need to verify tests actually exercise changed paths | High — slow, compute-intensive | Low for routine; high for safety-critical |
| **Static analysis regression detection** (AST/CFG diff) | When refactor changes API surface, signatures, or types | Medium — pyright/mypy can catch type-level regressions | Medium — already partially covered by pyright in CI |
| **Test Impact Analysis** (run only affected tests) | Large test suites where full run is slow | Medium — requires coverage data | Low — our suites are fast enough |
| **Coverage threshold enforcement** | Preventing coverage regression during refactoring | Low — `pytest --cov-fail-under` | Medium — cheap to add |

**The 40-60% failure rate stat:** "Research shows that organizations refactoring legacy systems without proper testing strategies experience 40-60% higher failure rates" (legacy system testing source). This supports adding characterization tests as a mandatory gate for L-risk seams on untested code.

## Finding 4: AI agent refactoring landscape — our seam-based design is above the industry baseline

**Confidence: [MEDIUM]** — based on one empirical study + tool comparisons.

Ottenhof et al. 2026 ("How do Agents Refactor?") analyzed 1,278 agent-generated PRs across Claude Code, Copilot, Cursor, Devin, Codex:
- **90% of agent refactorings are annotation changes** (comments, docstrings, type hints) — not structural
- Agents perform fewer structural refactorings than humans
- Agent refactorings can introduce modest increases in code smells (especially Cursor)

Our `/refactor` skill does **structural** refactoring (seam extraction, dual-path removal, import migration) — placing it above the industry baseline for AI-assisted refactoring. The seam-based serial discipline with per-seam verification is more rigorous than what most AI tools provide.

**LLM refactoring failure modes** (the gates our skill must guard against):
1. Hallucinated behavior preservation ("I changed it but it still works the same" — when it doesn't)
2. Missing callers (extracted/moved function, forgot to update imports in dependent files)
3. Broken imports (moved module, import paths not updated)
4. Scope creep (refactor expands beyond the seam boundary)

Our existing gates (definition completeness grep, end-to-end verification, complexity check) directly address #2, #3, and #4. Gap #1 (hallucinated behavior preservation) is the hardest — characterization tests and mutation testing are the external best-practice mitigations.

**Sources:** Ottenhof et al. 2026 (arxiv 2601.20160), arxiv 2511.19933 (LLM failure modes), devtoollab.com (AI refactoring tools comparison), claude-world.com (Claude Code TDD skill), cursor.com/docs (parallel subagents).

## Synthesis: answering the operator's original question

The operator asked: "how will /refactor take advantage of TDD, agent task decomposition, built-in checks and reviews?"

| Capability | /refactor has it? | Is the gap a flaw? | External evidence |
|---|---|---|---|
| **TDD** | Partial ("when practical") | **No** — characterization tests (green-starting) are the correct discipline for refactoring, not red-first. /go's mandatory red is for features, not refactoring. | Feathers, Fowler, 5 sources |
| **Task decomposition** | No (serial, one seam inline) | **Yes, for multi-file independent seams** — parallel fan-out is safe with DSM verification + worktree isolation. This is the real gap. | Fowler ParallelChange, SANER 2019, Cursor 2026 |
| **Multi-lens reasoning** | No (goes straight to implementation) | **Partially** — H1 Think Pack (5-lens) would catch framing errors before implementation. Worth layering for L-risk seams. | General reasoning best practice |
| **Parallel execution** | No (serial) | **Yes, for independent seams** — same as task decomposition. | DSM partitioning, worktree isolation |
| **check-work** | No (has verify, not check) | **Marginal** — verify per seam is sufficient for S/M-risk. check-work adds cross-seam verification for L-risk. | Conditional |

**The transcript's conclusion was directionally correct but misframed.** It said "/go refactor is the stronger choice for multi-file seams" — TRUE. But the reason is NOT that /go has better TDD (it doesn't — it has feature-TDD, which is wrong for refactoring). The reason is that /go has **parallel execution (H4) and multi-lens reasoning (H1)**, which /refactor lacks. The integration path `/go refactor → loads /refactor + layers H1/H4/H6` gives you the best of both: domain-correct characterization-testing discipline from /refactor + parallel execution and multi-lens reasoning from /go.

## Falsifier

This research is wrong if, within 6 months:
- Evidence emerges that mandatory red-first TDD improves refactoring safety for behavior-preserving changes (would overturn Finding 1)
- Our fleet encounters merge conflicts or semantic conflicts from parallel seam execution that worktree isolation doesn't prevent (would qualify Finding 2)
- Characterization tests prove insufficient as a safety net and mutation testing becomes necessary for routine refactoring (would overturn Finding 3's "sufficient for S/M-risk" claim)

## What this means for skill design

**No changes needed to /refactor's TDD discipline** — "when practical" is correct. Forcing mandatory red-first on pure refactoring would be a regression, not an improvement.

**Consider adding to /refactor (optional, not blocking):**
1. **Parallel seam detection** — when `seams.json` has ≥3 seams with `depends_on: []` and no shared files, suggest `/go refactor` or fan-out execution
2. **Semantic dependency check** — before parallelizing, verify no two parallel seams share imports, symbols, or caller-callee relationships
3. **Characterization test gate for L-risk seams** — if a seam touches untested legacy code and risk_of_change is L, require characterization tests before implementation

**The /go → /refactor integration path is the right design.** `/go refactor` loads /refactor's skill body (domain-correct refactoring discipline) and layers /go's horsepower (H1 think, H4 parallel, H6 verify). This is not redundancy — it's specialization + orchestration.
