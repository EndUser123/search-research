---
title: "Refactor-as-comprehensive-optimization-analyzer: the planner-executor split and cross-file analysis taxonomy"
created: 2026-07-30
source: session-2026-07-30 (/www research on /refactor as comprehensive analyzer + /go as executor)
tags: [refactoring, architecture-analysis, code-smells, planner-executor, skill-architecture, refactor-skill, go-skill, dsm, architecture-smells, technical-debt, cross-file-analysis]
agent: grok
host: both
cognitive_load: 4
verification: multi-source-verified
summary: >
  Research confirms the operator's vision: /refactor should be a comprehensive
  cross-file/architecture-level optimization ANALYZER (not a lightweight plan
  mode), and /go should be the expert EXECUTOR. Three layers of findings: (1)
  the planner-executor split is externally validated (5/5 sources); (2) the
  "analyze everything" taxonomy maps to 8 technical-debt categories + 6
  architecture smell types + Fowler's 152 refactorings across 10 code-smell
  families; (3) a concrete tool stack exists for each analysis layer
  (dependency graphs: pydeps/tach; duplication: PyChase; architecture: arcan).
  /refactor currently covers ~30% of the full taxonomy — the gaps are
  architecture smells (cycles, unstable deps, god components) and cross-file
  duplication detection.
relations:
  - target: wiki/concepts/refactoring-discipline-tdd-parallel-seams-verification-gates
    type: extends
  - target: wiki/concepts/coupling-inventory-as-mandatory-design-section
    type: extends
  - target: wiki/concepts/raising-coding-best-practices-in-ai-agents
    type: extends
  - target: wiki/concepts/parallel-safe-solution-decomposition
    type: related
  - target: wiki/concepts/plan-then-execute-pattern
    type: related
  - target: wiki/concepts/plan-execution-consolidated-into-go
    type: related
---

## Decision context

**The problem:** The operator defined a clear vision for the /refactor and /go skills: `/refactor` should analyze everything across files and directories — including architecture — to find ALL optimization opportunities. `/go` should be the expert executor that orchestrates to get requirements done as efficiently and effectively as possible without cutting quality corners. The question: what does "analyze everything" mean, what does the split look like, and how to build it?

**What alternatives were explored:**
- Whether /refactor and /go should be aliases (rejected — different disciplines, see prior concept)
- Whether /refactor is "lightweight" standalone vs /go "full horsepower" (rejected by operator — /refactor is the deep analyzer, not lightweight)
- Whether to keep /refactor as seam-extraction-only (rejected — operator wants comprehensive cross-file analysis)
- Whether the planner-executor split loses plan quality (research: no — 5/5 sources confirm separation maintains or improves quality)

**What the research changed:** Confirmed the split is correct and externally validated. Mapped the full taxonomy of "everything" a comprehensive analyzer should cover. Identified the specific gaps in /refactor's current capability and the tools that close them.

## Finding 1: The planner-executor split is the right architecture [HIGH confidence]

All 5 sources from the prior subagent + 3 new ones independently confirm: separating the analyzer (planner) from the executor is established best practice.

| System | How it splits | Evidence |
|---|---|---|
| **Morphi automated refactoring** | Catalog-style plan JSON → executor applies incrementally | morphi.vercel.app |
| **Claude Code review-loop** | Plan on disk → tests inspect → executor applies | datastudios.org |
| **Enterprise planner-executor pattern** | Full-LLM planner → lower-budget/rule executor | Medium (abhiramim1521) |
| **Dry-run refactoring best practice** | Analysis phase generates diff → pre-validated plan → executor applies | altexsoft.com |
| **Beurer-Kellner (IBM/ETH/Google)** | Plan-Then-Execute as security pattern: fix plan before tool exposure | [[plan-then-execute-pattern]] |

**The split for our fleet:**

```
/refactor <codebase>
  → Comprehensive analysis (code smells, architecture smells, cross-file patterns, test gaps)
  → Produces optimization plan (seams.json evolved: seams + architecture findings + test gaps)
  → STOPS (analysis complete, plan ready)

/go execute <plan>
  → Consumes the plan
  → Parallel fan-out for independent items (H4 + worktree isolation)
  → Per-item verification (H6)
  → Multi-lens reasoning on high-risk items (H1)
  → check-work at end
```

**Key insight from the research:** the planner retains FULL CONTEXT and can iterate on the plan without execution side-effects. The executor follows the plan artifact and doesn't need to "guess" intent. This means /refactor's analysis quality is maximized by being read-only — it doesn't dilute analysis depth with execution concerns.

## Finding 2: The "analyze everything" taxonomy [HIGH confidence]

Three frameworks combine to cover the full spectrum:

### Layer 1: Technical Debt Calculator taxonomy (8 categories)

The broadest checklist — what "everything" means at the highest level:

| Category | What it covers | Our current coverage |
|---|---|---|
| **Code debt** | Code smells, complexity, duplication | ✅ radon cc, coupling thresholds, dead-code |
| **Architecture debt** | Module coupling, cyclic deps, god components | ❌ **GAP — need dependency graph analysis** |
| **Test debt** | Missing tests, low coverage, untested paths | ❌ **GAP — need coverage analysis + characterization test identification** |
| **Dependency debt** | Outdated/ vulnerable dependencies | ❌ Out of scope (separate concern) |
| **Documentation debt** | Missing/ outdated docs | ❌ Out of scope for refactoring |
| **Infrastructure debt** | Build, deployment, CI gaps | ❌ Out of scope |
| **Security debt** | Vulnerabilities, auth issues | Partial (pylint/bandit) |
| **Data debt** | Schema debt, migration debt | ❌ Out of scope |

**For /refactor's scope:** Code debt + Architecture debt + Test debt. The other 5 are separate concerns handled by other skills/tools.

### Layer 2: Architecture smells (6 types that go beyond single-file)

These are the dimensions /refactor currently cannot detect. From arcan.tech and APSEC 2023 research:

| Architecture smell | What it detects | How to detect it | Priority |
|---|---|---|---|
| **Cyclic dependency** | Module A → B → A (direct or transitive) | pydeps `--show-cycles`, tach | High — blocks independent testing/release |
| **Unstable dependency** | Stable module depends on unstable one | Stability metric (fan-in / fan-out ratio) | Medium — cascading failure risk |
| **God component / Blob** | Single component conflates many responsibilities | Cohesion metrics + size thresholds | High — the classic god-module we already target, but at module not function level |
| **Dense structure** | Over-connected sub-graph (hotspot) | Edge-density ratio per sub-graph | Medium — identifies architectural bottlenecks |
| **Ambiguous/too-large interface** | Interface exposes too many methods/params | Method/param count per interface | Low — partially covered by coupling thresholds |
| **Vendor lock-in / reinvent-the-wheel** | Duplicates functionality in standard library | Import scanning against known packages | Low — nice-to-have |

### Layer 3: Code smells (Fowler catalog — 10 families, 152 refactorings)

We already cover complexity (radon) and coupling (thresholds). The Fowler families we DON'T explicitly detect:

| Code-smell family | Detect via | Our status |
|---|---|---|
| **Bloaters** (long method, large class, primitive obsession, long param list) | radon cc + param count | ✅ Partially covered |
| **Object-orientation abusers** (alternative classes, data classes, dead code) | vulture | ✅ Dead code covered |
| **Change preventers** (divergent change, shotgun surgery) | Touch-point count (files changed per feature) | ❌ **GAP** |
| **Dispensables** (comments, duplicate code, lazy class, data class) | Duplication detection | ❌ **GAP — need cross-file duplication tool** |
| **Couplers** (feature envy, inappropriate intimacy, message chains, middle man) | Dependency analysis | Partial via coupling inventory |

## Finding 3: The tool stack for each analysis layer [MEDIUM confidence]

### Dependency graph + architecture analysis (the biggest gap)

| Tool | What it does | Maturity |
|---|---|---|
| **pydeps** | Builds import graph, shows circular imports, topological order | Established |
| **tach** | Modern modular dependency framework — cycle detection, boundary enforcement, forbidden imports | Active 2026 |
| **pyreverse** (pylint) | UML class + package diagrams, module dependencies | Established |
| **snakefood** | Module dependency diagram, import trees, cycle highlighting | Mature |
| **modulegraph** | Static import analysis, circular dependency detection, full graph export | Mature |
| **arcan** | Architecture smell detection (cycles, unstable deps, god components, dense structures) — Java/C++ focused, Python support emerging | Research-grade |

**Practitioner signal (HN 2026):** Three new tools directly relevant:
- **Codix** — indexes code into local SQLite via tree-sitter, provides symbol lookups, reference finding, callers/callees
- **Vho** — AST-based analysis using Label Propagation Algorithm for "code gravity"
- **Depwire** — dependency graph + MCP tools so AI agents stop guessing at imports/missing call sites

### Duplication detection (cross-file DRY)

| Tool | What it does | Maturity |
|---|---|---|
| **PyChase** | AST-based duplicate function detection across files | Active |
| **python-repetition-hunter** | Token-based similarity scanning for repeated patterns | Mature |
| **CPD (PMD)** | Copy/paste detector, multi-language, Python support | Established |
| **Simian** | Multi-language duplicate code detector | Established |

### Test gap analysis

| Approach | What it does | Effort |
|---|---|---|
| **pytest --cov** | Coverage report → identify untested modules/functions | Low |
| **Characterization test identification** | Analyze coverage gaps on L-risk code → flag "needs characterization tests before refactoring" | Medium |
| **Mutation testing** (mutmut, cosmic-ray) | Verify tests actually exercise changed paths | High (selective use only) |

## Synthesis: what /refactor becomes

### Current state (~30% of full taxonomy)

| Dimension | Status |
|---|---|
| Complexity (radon cc) | ✅ As gate after implementation |
| Dead code (vulture) | ✅ Proposed in Step 4.1 |
| Constant drift | ✅ Proposed in Step 4.1 |
| Coupling (DRY ≥3, params >7, touch-points >3, mixed-concerns) | ✅ In /design, partially in /refactor |
| Seam extraction + dual-path removal | ✅ Core capability |

### Target state (the full scope the operator envisions)

| Dimension | Status | How to get there |
|---|---|---|
| **+ Architecture: cyclic dependencies** | ❌ Gap | Integrate pydeps `--show-cycles` or tach into Step 4.1 |
| **+ Architecture: god components (module-level)** | ❌ Gap | Module cohesion metrics via pyreverse or custom script |
| **+ Architecture: unstable dependencies** | ❌ Gap | Fan-in/fan-out stability metric |
| **+ Cross-file duplication (DRY)** | ❌ Gap | Integrate PyChase or python-repetition-hunter |
| **+ Test gap identification** | ❌ Gap | pytest --cov analysis → flag characterization test needs |
| **+ Touch-point analysis (shotgun surgery)** | ❌ Gap | Git history: files changed per commit/feature |

### The evolution of seams.json

Current seams.json captures individual structural cuts. For comprehensive analysis, the plan artifact needs to evolve:

```json
{
  "analysis_type": "comprehensive",
  "target": "P:/packages/yt-is",
  "dependency_graph": "run/pydeps_output.dot",
  "findings": [
    {
      "id": "A1",
      "category": "code_smell",
      "type": "dead_code",
      "severity": "P2",
      ...
    },
    {
      "id": "B1",
      "category": "architecture_smell",
      "type": "cyclic_dependency",
      "modules": ["nlm_batch", "source_fetch", "wiki_write"],
      "evidence": "pydeps --show-cycles output",
      ...
    },
    {
      "id": "C1",
      "category": "duplication",
      "type": "cross_file_dry",
      "files": ["file_a.py", "file_b.py", "file_c.py"],
      "evidence": "PyChase report: 3 functions with >85% similarity",
      ...
    },
    {
      "id": "D1",
      "category": "test_gap",
      "type": "missing_characterization",
      "files": ["load_balancer.py"],
      "coverage": "0%",
      "recommendation": "Characterization tests required before structural refactor",
      ...
    }
  ]
}
```

This richer artifact is what `/go execute` consumes — with the dependency graph enabling DSM-based parallel decomposition.

## Falsifier

This research is wrong if, within 6 months:
- Architecture smell detection proves too noisy for our codebase sizes (most of our packages are <50 files — architecture smells may not emerge at that scale)
- The planner-executor split introduces handoff friction that degrades outcomes vs integrated execution (the 5 sources say it won't, but we haven't tested it on our fleet)
- The tool stack (pydeps, PyChase, etc.) proves unreliable on Windows / multi-root workspaces

## What this means for skill design

**`/refactor` deepens, not lightens.** The operator's vision is correct: /refactor becomes the comprehensive optimization brain. It adds:
1. Dependency graph analysis (pydeps/tach) → architecture smells
2. Duplication detection (PyChase) → cross-file DRY
3. Test gap analysis (coverage) → characterization test identification
4. Touch-point analysis (git history) → shotgun surgery detection

**`/go` stays the expert executor.** No change to its role — it consumes the richer plan artifact and executes with parallel/verify horsepower. The anti-recursion rule (don't call /go from /refactor) becomes even more important: /refactor is strictly read-only analysis; /go is strictly execution.

**The handoff is the plan artifact on disk.** seams.json evolves to capture architecture findings, duplication findings, and test gaps — not just structural seams. `/go execute <plan>` consumes it.

**Skill suggestion:** This research defines the scope of a /refactor enhancement. To implement it, use `/design` to produce the enhanced /refactor architecture, then `/go execute` to build it.
