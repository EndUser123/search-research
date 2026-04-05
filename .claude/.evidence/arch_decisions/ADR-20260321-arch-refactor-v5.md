# ADR-20260321: `/arch` Skill Refactor — Unified Result Type, Fail-Fast Gates, Atomic Persistence

**Date:** 2026-03-21
**Status:** Proposed
**Decision Maker:** Solo developer

---

## Context and Problem Statement

The `/arch` skill (v4.4, `P:/packages/arch`) has 43 Python modules and 87% test coverage, but exhibits three architectural deficiencies:

1. **Inconsistent return types** — each module returns different dict structures (`config.py` returns `ArchConfig`, `routing.py` returns implicit dicts, `persistence.py` returns mixed `str | None`). Callers must handle heterogeneous types.

2. **Non-fail-fast validation** — `validate_templates()` in `validate_templates.py` checks all templates before reporting any failure. If a file is missing, expensive duplicate detection still runs.

3. **Non-atomic persistence writes** — `persistence.py:315` uses direct `write_text()` which can leave truncated JSON if a write is interrupted (e.g., crash, Ctrl-C, disk full). There's no schema versioning or corruption recovery.

The skill is Python 3.12+, used in a solo-dev, Windows 11, CLI-centric, multi-terminal environment. These deficiencies create unnecessary complexity and risk for an LLM-orchestrated tool where the code is a deterministic co-processor.

---

## Decision

Implement four coordinated changes to tighten the `/arch` orchestration model without changing its core semantics:

1. **`arch/results.py` (new)** — Unified `ArchResult[T]` dataclass with `is_success`, `value`, `error`, `templates_used`, `metadata` fields. All public functions return this type.

2. **`TemplateValidator.validate_templates()` (fail-fast gate)** — Ordered check chain: `file_exists` → `duplicates` → `permissions`. Early return on first failure with `metadata["stage"]`.

3. **`DecisionStore` with atomic writes** — `persistence.py` wrapped in a class using `os.replace()` for atomic temp-file+rename. Add `SCHEMA_VERSION = 1` to decision JSON. Add `load_arch_decision()` with corruption detection (returns `ArchResult` with `error="corrupt_decision_file"`).

   **YAML injection fix (CRITICAL — SEC-001):** All frontmatter fields (query, template, domain, confidence) must be YAML-escaped via `yaml.safe_dump()`. Additionally, the `output` decision text written after the `---` delimiter must be YAML-escaped — user-controlled content (especially `query`) can contain YAML-special characters (`---`, `:`, `#`) that would corrupt or inject into the frontmatter structure. Apply `yaml.safe_dump()` to the output field before writing it raw after the delimiter.

4. **Function/class duality** — Existing functions (`load_arch_config`, `route_query`, `validate_templates`, `save_arch_decision`) become thin wrappers around classes (`ArchConfig`, `RoutingEngine`, `TemplateValidator`, `DecisionStore`).

---

## Rationale

**Evidence:**
- Current modules use inconsistent dict returns (`persistence.py:233` returns `str | None`, `routing.py` returns implicit dicts)
- `persistence.py:315` uses non-atomic `write_text()` directly
- `validate_templates.py` has no ordering or early-return semantics

**Why not collapse to one class (Perplexity proposal)?**
The Perplexity-generated "ArchOptimizer" flatpack (~150 LOC single class) throws away the intentional separation of concerns. The `/arch` skill is LLM-orchestrated — the code exposes a deterministic API the LLM calls. Collapsing it defeats the purpose of having a clear capability interface.

**Why these four changes specifically?**
- `ArchResult`: Eliminates heterogeneous return types across modules
- Fail-fast gates: Avoids unnecessary computation on early failures
- Atomic writes: Prevents corruption from interrupted writes (critical for decision archival)
- Function/class duality: Maintains the convenience API while enabling richer class-based internals

**Python 3.14 target rationale:**
3.14 has ~299 bugfixes in 3.14.3 alone, dict performance improvements, and template string literals — all relevant for config/path-heavy code. The current README specifies 3.12+; this ADR proposes updating to 3.14.

---

## Alternatives Considered

| Alternative | Description | Pros | Cons | Why Rejected |
|-------------|-------------|------|------|--------------|
| **Keep Status Quo (CHOSEN)** | Don't change | Zero migration risk, no test updates | Deficiencies remain | Not viable — deficiencies cause real problems |
| **Perplexity Flatpack** | Collapse to single ~150 LOC `ArchOptimizer` class | Simpler module count | Throws away separation of concerns, harder to test | Violates LLM-toolkit design principle |
| **Partial Fix (Result Only)** | Add `ArchResult` without atomic writes | Easier migration | Doesn't fix corruption risk | Corruption risk is the highest-impact deficiency |
| **Partial Fix (Atomic Only)** | Add atomic writes without `ArchResult` | Fixes biggest risk | Doesn't address inconsistent return types | Deficiencies are independent; fixing one without the other leaves partial improvement |

---

## Consequences

### Positive
- **Consistent API**: All public functions return `ArchResult[T]`, enabling uniform error handling by callers
- **Fail-fast performance**: Validation short-circuits on first failure, avoiding unnecessary checks
- **Corruption prevention**: Atomic writes ensure decision files are never partially written
- **Graceful degradation**: Corruption detection returns `ArchResult(is_success=False)` instead of raising

### Negative
- **Migration effort**: 291 existing tests assert on current return types; need updates to inspect `.value`/`.is_success`
- **New module added**: `arch/results.py` is a new dependency for all modules
- **API break**: Functions that returned `dict` now return `ArchResult` — callers must adapt

### Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Test migration incomplete | Medium | Tests fail after refactor | Write migration tests first; run existing suite before declaring done |
| `os.replace()` fails on Windows with locked files | Low | Write fails silently | Check return value; log warning on failure |
| Schema version mismatch on load | Low | Old decisions unreadable | Version check with fallback; never crash on old data |

---

## Implementation

### Phase 1: `ArchResult` Dataclass (1-2 hours)
- Create `arch/results.py` with `ArchResult` dataclass
- Add `is_complete` and `is_valid` properties
- Update `config.py`, `routing.py`, `persistence.py` to return `ArchResult`
- Update tests to inspect `.value`/`.is_success`

### Phase 2: Fail-Fast Validation Gate (1 hour)
- Refactor `validate_templates()` into `TemplateValidator.validate_templates()` class
- Implement ordered check chain with early return
- Add `metadata["stage"]` to indicate which gate failed
- Add tests for fail-fast order and stage reporting

### Phase 3: Atomic Persistence (2-3 hours)
- Create `DecisionStore` class wrapping `persistence.py` functions
- Implement `_write_atomic()` using temp file + `os.replace()`
- Add `SCHEMA_VERSION = 1` to decision JSON structure
- Implement `load_arch_decision()` with corruption detection
- Add tests: atomic write simulation, corrupt file recovery

### Phase 4: Function/Class Duality (1 hour)
- Wrap existing functions in thin class definitions
- Keep public functions as wrappers for backward compatibility
- Document the API surface for LLM orchestrator

**Total estimated effort:** 5-7 hours

---

## Rollback Strategy

Git revert each phase independently. Since phases are additive (results → validation → atomic writes → duality), rollback is straightforward:
- `git revert HEAD~1` undoes Phase 4 (duality)
- `git revert HEAD~2` undoes Phase 3 (atomic)
- etc.

**No data migration required** — the refactor doesn't change persisted data format (new `ArchResult` is a return-type change only).

---

## Success Criteria

### Phase 1-4 (Immediate)
- All 291 existing tests pass after migration (with updated assertions)
- 4 new tests added: `test_arch_result_properties`, `test_validate_templates_fail_fast_order`, `test_decision_store_atomic_write`, `test_corrupt_decision_file`
- Coverage maintained at 87%+
- No behavioral change to routing algorithm, config cascade, or template selection

### Phase 5 (Future Enhancement)
- New tests for Phase 5:
  - `test_prereq_contract_fields` — verifies all fields populated correctly
  - `test_prereq_contract_required_inputs_gate` — verifies `fast`-only restriction when inputs missing
  - `test_evidence_bundle_structure` — verifies graph/adr/summary/schema_version present
  - `test_build_evidence_bundle` — verifies helper constructs bundle from query+decision
  - `test_consistency_report_detection` — verifies contradictions/cycles detected in prior decisions
  - `test_supersede_candidate_identification` — verifies ADR supersession candidates surfaced
  - `test_governance_mode_warn` — verifies warnings surfaced but not blocking
  - `test_governance_mode_enforce_blocks` — verifies enforcement blocks when required
  - `test_governance_mode_enforce_persists` — verifies enforcement allows when issues resolved
  - `test_critical_review_produces_critique` — verifies CoT+Self-Refine produces `final_critique`
  - `test_uncertainty_channel_required_fields` — verifies assumptions/open_questions/confidence present
- Phase 5 cumulative coverage target: 85%+ (governance code is harder to test fully)

---

## Multi-Terminal Isolation Assessment

**State sharing:** YES — decision archival writes to `.claude/arch_decisions/` which is shared across terminals.

**Concurrency safety:**
- Atomic writes (`os.replace()`) ensure that simultaneous writes from two terminals don't corrupt files — the OS guarantees atomic rename on both POSIX and Windows
- JSONL index append (`open(..., "a")`) is safe for concurrent appends — each line is independent

**Stale data immunity:**
- Index reads use `load_decision_index()` which reloads from disk each call
- Decision files are immutable once written (no in-place updates)
- No in-memory state that could become stale across terminals

**Red flags addressed:**
- `persistence.py:315` used direct `write_text()` — now wrapped in atomic write
- No file locking assumed (atomic rename is the isolation mechanism)

---

## Related Decisions

- **ADR-20260321-gto-v3-architecture:** Uses similar `ArchResult` pattern for GTO v3
- **ADR-20260321-multi-task-context-safety:** Addresses context compaction; orthogonal to this refactor

---

## Phase 5: Governance Engine (Evidence + Consistency + Complexity)

Phase 5 transforms `/arch` from a per-query advisor into an architecture governance engine. It builds on Phases 1-4 and adds six sub-phases (5.0 Orchestrator/Sub-Agent Roles, 5.1 Complexity Contract, 5.2 Evidence Engine, 5.3 Consistency Engine, 5.4 Critical Review, 5.5 Governance Tunability) executed in dependency order.

---

### Phase 5.0: Orchestrator and Sub-Agent Roles

Phase 5 introduces an explicit agent architecture. The **Orchestrator Agent** (the primary Claude instance invoking `/arch`) orchestrates a set of **sub-agent roles** implemented as specialized prompts and call patterns within the same LLM — not separate processes. The Orchestrator is the only entity that directly calls `arch` Python functions; sub-agents shape how it interprets results and decides what to call next.

#### 5.0.1 Agent Definitions

| Agent | Role | Spec File |
|-------|------|-----------|
| **Orchestrator Agent** | Primary architect/coordinator | *(no spec — is the /arch SKILL.md session itself)* |
| **Prerequisite Agent** | Requirements elicitation | `P:/.claude/agents/arch-prerequisite.md` |
| **Design Synthesis Agent** | Decision drafting | `P:/.claude/agents/arch-design-synthesis.md` |
| **Evidence Agent** | Structural evidence construction | `P:/.claude/agents/arch-evidence.md` |
| **Consistency/Judge Agent** | Governance verdict | `P:/.claude/agents/arch-consistency.md` |
| **Critical Review Agent** | Quality gate (CoT + Self-Refine) | `P:/.claude/agents/arch-critical-review.md` |

All sub-agent spec files live in `P:/.claude/agents/` and are invoked by the Orchestrator via prompt injection within the active `/arch` session. Sub-agents are not separate processes — they are activated as specialized roles within the Orchestrator's context.

#### 5.0.2 Responsibilities of Each Agent

**Orchestrator Agent**
- Calls deterministic `arch` APIs:
  - `analyze_prerequisites(query) -> ArchResult[PrereqContract]`
  - Routing / template selection functions
  - `build_evidence_bundle(query, decision, prereq_contract) -> ArchResult[EvidenceBundle]`
  - `list_arch_decisions(system_id)`, `compute_consistency_report(decisions, new_graph, new_adr)`
  - `save_arch_decision(...)` via `DecisionStore`
- Enforces `governance_mode` (`off | warn | enforce`) and flags (`evidence_required`, `consistency_required`, `review_required`)
- Decides when to activate each sub-agent role

**Prerequisite Agent**
- Interprets `PrereqContract` fields: `required_inputs`, `risk_flags`, `missing_best_practices`, `assumptions`, `confidence`
- Asks user clarifying questions to fill `required_inputs` when non-empty
- Explains risk flags and missing best practices; suggests what user should provide
- Returns an updated, clarified `PrereqContract` for downstream phases

**Design Synthesis Agent**
- Uses the clarified `PrereqContract` and selected templates (`fast`, `deep`, `cli`, `python`, `data-pipeline`, `precedent`)
- Drafts the decision text that will be persisted as `DecisionRecord.query`/`output` and used by `build_evidence_bundle`

**Evidence Agent**
- Given draft decision and `PrereqContract`, constructs `EvidenceBundle`:
  - `graph`: valid `graph.txt` format with explicit components, dependencies, risks, contradictions, cycles
  - `adr`: filled ADR one-pager from `precedent.md`
  - `summary`: 2-3 sentence narrative coherent with `PrereqContract` and decision
  - `open_questions`, `assumptions`, `confidence`: populated consistently
- Guarantees `EvidenceBundle` is structurally parseable by the consistency engine

**Consistency/Judge Agent**
- Calls `list_arch_decisions(system_id)` and `compute_consistency_report(prior_decisions, new_graph, new_adr)` via the Orchestrator
- Interprets `ConsistencyReport` into a governance verdict:
  - Is this decision consistent with prior ones for the same system?
  - Which prior ADRs might need supersession?
- Returns narrative summary for Orchestrator to incorporate into final answer and stored metadata

**Critical Review Agent**
- Uses `arch/resources/critical_review.md` with two-stage CoT + Self-Refine (spec: `arch-critical-review.md`)
- Runs against: decision text, `EvidenceBundle` (graph, ADR, summary, prereq_contract)
- Produces `final_critique: str` stored in `EvidenceBundle.final_critique`
- Orchestrator may apply one refinement pass before persistence (single self-refine loop, not unbounded)

#### 5.0.3 Agent-Aware Orchestration Sequence

**Note:** Phase 5.0.3 Steps 1-7 define the Master Orchestration flow. Phase 5.2.4 (Evidence Engine) and Phase 5.3.4 (Consistency Engine) define separate sub-workflows with their own Step 1-N numbering. These are distinct workflows — not conflicting versions.

```
Step 1: Orchestrator calls analyze_prerequisites(query)
        → Prerequisite Agent activates: interact with user, fill required_inputs,
          confirm assumptions and risk_flags
        → Returns clarified PrereqContract

Step 2: Orchestrator routes to templates (existing routing algorithm + config cascade)
        → Design Synthesis Agent activates: draft decision using selected templates + PrereqContract

Step 3: Orchestrator activates Evidence Agent
        → Calls build_evidence_bundle(query, decision, prereq_contract)
        → Ensures EvidenceBundle is well-formed

Step 4: Orchestrator activates Consistency/Judge Agent (governance_mode in ("warn", "enforce"))
        → Calls list_arch_decisions(system_id)
        → Calls compute_consistency_report(prior_decisions, new_evidence_bundle.graph)
        → Interprets ConsistencyReport
        → Proposes supersession; explains contradictions to user

Step 5: Orchestrator (governance_mode == "warn" or "enforce"):
        → Critical Review Agent activates
        → Loads critical_review.md; runs CoT + Self-Refine on evidence_bundle
        → Stores final_critique in EvidenceBundle.final_critique

Step 6: Orchestrator optionally applies one refinement pass based on
        ConsistencyReport and final_critique

Step 7: Orchestrator enforces governance_mode rules BEFORE calling save_arch_decision():
        - In "off" mode: calls save_arch_decision() directly
        - In "warn"/"enforce" mode: evidence complete, consistency satisfied or acknowledged, review run when required
        → In "enforce" mode: blocks if enforcement checks fail; does NOT call save_arch_decision() until resolved
```

#### 5.0.4 Constraints

- Sub-agents are **roles/prompts within the Orchestrator LLM**, not separate services or processes
- The Orchestrator is the only entity that directly calls `arch` Python functions
- Sub-agents do not access files, network, or tools independently — they shape how the Orchestrator calls functions and interprets results
- Each sub-agent spec file lives at `P:/.claude/agents/arch-<name>.md`
- Core deterministic APIs, template system, routing algorithm, configuration cascade, and max 2 template chaining are **unchanged**

---

### Phase 5.1: Complexity Contract via `prerequisite_analyzer.py`

**Priority:** 1st (cheapest, highest leverage per hour)

#### 5.1.1 `PrereqContract` Dataclass

**File:** `arch/prerequisite_analyzer.py`

```python
from dataclasses import dataclass, field
from typing import Literal

@dataclass
class PrereqContract:
    is_optimization: bool
    estimated_complexity: Literal["low", "medium", "high"]
    required_inputs: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)
    missing_best_practices: list[str] = field(default_factory=list)
    confidence: float = 0.8  # 0.0-1.0, calibration signal
    assumptions: list[str] = field(default_factory=list)
```

**Field semantics:**
| Field | Description | Example |
|-------|-------------|---------|
| `is_optimization` | True if query asks to improve existing system | "improve memory system" |
| `estimated_complexity` | Heuristic based on query features | "high" for multi-system redesign |
| `required_inputs` | Inputs missing but needed for precision | ["latency SLOs", "data volume ranges"] |
| `risk_flags` | Regulatory/multi-tenant/safety flags | ["multi-tenant", "regulated", "PII"] |
| `missing_best_practices` | Obvious actions team should do but isn't | ["add circuit breaker", "add timeout"] |
| `confidence` | Calibrated certainty (0.0-1.0) | 0.6 for underspecified query |
| `assumptions` | What must be true for recommendation to hold | ["single-region deployment"] |

#### 5.1.2 `analyze_prerequisites()` Function

```python
def analyze_prerequisites(query: str) -> ArchResult[PrereqContract]:
    """
    Returns a structured complexity contract for the given query.

    Deterministic heuristics (no LLM required):
    - Complexity: count keyword features (async, multi-region, data volume, SLOs)
    - Domain heuristics: data-pipeline + multi-tenant → medium+
    - Required inputs: missing latency SLO if latency mentioned without SLO
    - Risk flags: multi-tenant/regulated/PII terms detected → flag
    - Missing best practices: common patterns not mentioned in query
    """
```

#### 5.1.3 Orchestration Rules (Update to SKILL.md)

**Stage 1 (Classify Intent) is amended to:**

```
Step 1: Call analyze_prerequisites(query)
Step 2: If PrereqContract.required_inputs is non-empty:
          - Surface missing inputs to user
          - Offer: (a) provide missing inputs, (b) continue with fast template only
Step 3: If PrereqContract.risk_flags is non-empty:
          - Set internal flag to invoke CKS/constitutional checks
Step 4: Proceed to routing with PrereqContract passed as context
```

**Gating behavior:**
- If `required_inputs` is non-empty and user does not provide them: only `fast` template allowed
- `deep` template requires all `required_inputs` satisfied
- `risk_flags` trigger CKS invocation but do not block routing

---

### Phase 5.2: Architecture Evidence Engine

**Priority:** 2nd (requires Phase 5.1 context; extends Phase 3 persistence)

#### 5.2.1 `EvidenceBundle` Dataclass

**File:** `arch/evidence.py` (new)

```python
from dataclasses import dataclass, field

@dataclass
class EvidenceBundle:
    graph: str                          # Filled graph.txt format
    adr: str                            # Filled ADR one-pager from precedent.md
    summary: str                        # 2-3 sentence narrative
    schema_version: int = 1
    open_questions: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    confidence: float = 0.8             # 0.0-1.0
    final_critique: str | None = None  # Populated by Phase 5.4
```

**`graph` format (graph.txt style):**
```
# Architecture Graph: {system_id}

# Components
[ComponentA]
  depends_on: [ComponentB, ComponentC]
  provides: [ServiceX, ServiceY]
  risks: [SinglePointOfFailure]

[ComponentB]
  depends_on: [DatabaseD]
  provides: [DataAccess]

# Relationships
ComponentA → ComponentB: synchronous_call

# Contradictions
ConstraintA contradicts IdeaB: [Explanation]

# Cycles Detected
[None] or [Cycle: ComponentA → ComponentB → ComponentA]
```

#### 5.2.2 `build_evidence_bundle()` Helper

```python
def build_evidence_bundle(
    query: str,
    decision: str,
    prereq_contract: PrereqContract,
    context: dict | None = None
) -> ArchResult[EvidenceBundle]:
    """
    Constructs an EvidenceBundle from query + decision output.

    LLM orchestrator calls this after generating the decision.
    Populates:
    - graph: parsed from decision components/relationships/risks
    - adr: filled from precedent.md template
    - summary: 2-3 sentence TL;DR
    - open_questions: copied from PrereqContract.required_inputs
    - assumptions: copied from PrereqContract.assumptions + new ones
    - confidence: copied from PrereqContract.confidence
    """
```

#### 5.2.3 Extended `DecisionRecord` Schema

**File:** `arch/persistence.py` — `DecisionStore` updated to store:

```python
@dataclass
class DecisionRecord:
    id: str                           # UUID
    timestamp: str                     # ISO 8601
    query: str
    templates: list[str]              # primary + chained
    system_id: str | None             # e.g., "arch", "hooks", "myapp"
    evidence_bundle: EvidenceBundle   # Phase 5.2 addition
    prereq_contract: PrereqContract   # Phase 5.1 addition
    schema_version: int = 2           # Incremented from Phase 3's SCHEMA_VERSION=1
```

**Migration:** Old records (schema_version=1) load with `evidence_bundle=None`, `prereq_contract=None`. Graceful degradation applies.

#### 5.2.4 Orchestration Rules

**After routing, before output:**
```
Step 1: Call analyze_prerequisites(query) [from Phase 5.1]
Step 2: Execute template, generate decision
Step 3: Call build_evidence_bundle(query, decision, prereq_contract)
Step 4: Merge evidence_bundle into DecisionRecord
Step 5: Proceed to persistence
```

---

### Phase 5.3: Consistency Engine

**Priority:** 3rd (requires Phase 5.2 evidence bundles; builds on Phase 3 `DecisionStore`)

#### 5.3.1 New Module `arch/consistency.py`

```python
from dataclasses import dataclass, field
from arch.results import ArchResult

@dataclass
class ConsistencyReport:
    is_consistent: bool
    contradictions: list[str] = field(default_factory=list)
    cycles: list[str] = field(default_factory=list)
    supersede_candidates: list[str] = field(default_factory=list)
    evidence_gaps: list[str] = field(default_factory=list)  # e.g., "EvidenceBundle.graph missing relationships section"

@dataclass
class DecisionRecord:
    id: str
    timestamp: str
    query: str
    templates: list[str]
    system_id: str | None
    evidence_bundle: EvidenceBundle | None
    prereq_contract: PrereqContract | None
    schema_version: int
```

#### 5.3.2 `list_arch_decisions()` Function

```python
def list_arch_decisions(system_id: str | None = None) -> ArchResult[list[DecisionRecord]]:
    """
    Load all decision records, optionally filtered by system_id.

    - If system_id is None: return all decisions
    - If system_id is provided: return only decisions where decision.system_id == system_id
    - Returns ArchResult wrapping list; error field set if load fails
    """
```

#### 5.3.3 `compute_consistency_report()` Function

```python
def compute_consistency_report(
    decisions: list[DecisionRecord],
    new_graph: str,
    new_adr: str | None = None
) -> ArchResult[ConsistencyReport]:
    """
    Detects contradictions and cycles between existing decisions and new input.

    Algorithm:
    1. Parse new_graph for: components, relationships, contradictions, cycles
    2. For each prior DecisionRecord with evidence_bundle.graph:
       a. Parse prior_graph for components and relationships
       b. Detect: same component with different depends_on → contradiction
       c. Detect: A→B→C→A cycle → cycle
       d. Check: new component contradicts prior constraint
    3. Check new_adr against prior ADRs for same system:
       - Same problem, different solution → supersede candidate
    4. Return ConsistencyReport with all findings
    """
```

#### 5.3.4 Orchestration Rules

**Pre-persistence workflow (amended):**
```
Step 1: Call analyze_prerequisites(query) [Phase 5.1]
Step 2: Execute template, generate decision
Step 3: Call build_evidence_bundle() [Phase 5.2]
Step 4: Load prior decisions via list_arch_decisions(system_id)
Step 5: Call compute_consistency_report(prior_decisions, new_evidence_bundle.graph)
Step 6: If ConsistencyReport.is_consistent is False:
          a. Surface contradictions to user
          b. List supersede candidates
          c. Ask: (a) acknowledge and proceed, (b) propose ADR supersession
Step 7: If ConsistencyReport.evidence_gaps non-empty:
          a. Warn that evidence bundle is incomplete
          b. Proceed only if governance_mode != "enforce"
Step 8: Persist decision with consistency report attached
```

---

### Phase 5.4: Critical Review (CoT + Self-Refine)

**Priority:** 4th (final quality gate; runs on completed EvidenceBundle before persistence)

#### 5.4.1 Critical Review Prompt Template

**File:** `arch/resources/critical_review.md` (new template)

```markdown
## Task: Critical Review of Architecture Decision

### Input
- Query: {query}
- Decision: {decision}
- Evidence Bundle:
  - Graph: {graph}
  - ADR: {adr}
  - Summary: {summary}
- Prereq Contract: {prereq_contract}

## Stage 1: Initial Critique (Chain of Thought)

### 1.1 Intent Summarization
Restate the decision's intent in one sentence.

### 1.2 Logical Gaps
List specific logical gaps in the reasoning. Be concrete:
- Which assumptions are not justified?
- What evidence is missing?
- What constraints were ignored?

### 1.3 Hidden Assumptions
List assumptions that were made but not stated:
- What must be true for this recommendation to hold?
- What would change the verdict?

### 1.4 Missing Obvious Actions
List things the team should do but isn't:
- Not mentioned in the decision
- Standard practice for this type of system
- Low-cost/high-value items

### 1.5 Risks and Edge Cases
List specific risks:
- What could go wrong with this approach?
- What edge cases were not considered?
- What is the failure mode?

### 1.6 Concrete Recommendations
List specific, actionable recommendations:
- Priority: critical / important / nice-to-have
- Each recommendation should be implementable in ≤2 hours

### 1.7 Open Questions
List questions that remain unanswered:
- Information needed for better decision
- Stakeholders who should review
- Conditions that would change the recommendation

## Stage 2: Self-Refine (Review of the Review)

### 2.1 Critique Quality Assessment
- Did Stage 1 find the root cause or just surface symptoms?
- Are recommendations specific or vague?
- Are risks concrete or hypothetical?

### 2.2 Missed Issues
List issues that Stage 1 missed:
- What did the initial review overlook?
- What would an adversarial reviewer find?

### 2.3 Weak Points
List weak points in the critique itself:
- Where is the reasoning thin?
- What needs stronger evidence?

### 2.4 Refined Critique
Incorporate Stage 2 findings into an improved critique.
```

#### 5.4.2 `final_critique` Field

After CoT + Self-Refine, the LLM produces a `final_critique: str` stored in `EvidenceBundle.final_critique`.

#### 5.4.3 Orchestration Rules (Amended)

**Pre-persistence final step:**
```
Step N: If governance_mode == "review" or "enforce":
          Load critical_review.md template
          Execute CoT + Self-Refine on evidence_bundle
          Store result in evidence_bundle.final_critique
```

---

### Phase 5.5: Governance Tunability

**Priority:** 5th (configuration layer over Phases 5.1-5.4)

#### 5.5.1 `.archconfig.json` Extensions

```json
{
  "$schema": "./.archconfig.schema.json",
  "governance": {
    "mode": "off",           // "off" | "warn" | "enforce"
    "evidence_required": false,
    "consistency_required": false,
    "review_required": false
  }
}
```

**Mode semantics:**

| Mode | Evidence | Consistency | Review | Behavior |
|------|----------|-------------|--------|----------|
| `off` | Optional | Optional | Optional | Full flexibility; no governance |
| `warn` | Computed | Computed | Optional | Surface warnings; do not block |
| `enforce` | Required | Required | Required | Block finalization until issues resolved |

#### 5.5.2 Enforcement Behavior by Mode

**governance_mode: "off"**
- `build_evidence_bundle()` called if LLM requests it; not required
- `compute_consistency_report()` skipped
- No review step
- `evidence_bundle` may be None in stored records

**governance_mode: "warn"**
- `build_evidence_bundle()` always called; warnings if missing fields
- `compute_consistency_report()` always called; warnings surfaced but not blocking
- Review optional; warnings if skipped
- Decision persists regardless of warnings

**governance_mode: "enforce"**
- `build_evidence_bundle()` must return non-None with all required fields
- `compute_consistency_report()` must return `is_consistent=True` OR user explicitly acknowledges
- Critical review must run and `final_critique` must be non-empty
- If any enforcement check fails: decision NOT persisted; user prompted to resolve

---

### Phase 5 Effort Estimate

| Sub-phase | Effort | Dependencies |
|-----------|--------|--------------|
| 5.0 Orchestrator & Sub-Agent Roles | — | All prior phases (structural only, no new code) |
| 5.1 Complexity Contract | 1-2 hours | Phase 1 (ArchResult) |
| 5.2 Evidence Engine | 2-3 hours | Phase 3 (DecisionStore), Phase 5.1 |
| 5.3 Consistency Engine | 2 hours | Phase 5.2 (graph parsing) |
| 5.4 Critical Review | 1-2 hours | Phase 5.2 (EvidenceBundle) |
| 5.5 Governance Tunability | 1 hour | Phase 5.1–5.4 |

**Cumulative total (Phases 1-5):** 10-14 hours

---

### Why These Together?

These sub-phases form a governance pipeline:

```
Query → PrereqContract (5.1) → EvidenceBundle (5.2) → ConsistencyReport (5.3) → Persistence
```

Each phase feeds the next. Skipping a phase weakens the next phase's output. The complexity contract gates template depth; evidence bundle structures the output; consistency engine detects drift over time.

---

## Adversarial Review Findings

### Round 2 Findings (2026-03-22) — Applied

| Finding | Severity | Resolution |
|---------|----------|-----------|
| LOGIC-101: Step 7 "proceed to Step 8" undefined | BLOCKER | Fixed: Step 7 now says "call save_arch_decision() inline" for off mode |
| LOGIC-102: Three conflicting Step N sequences | BLOCKER | Fixed: Added note clarifying Phase 5.0.3, 5.2.4, 5.3.4 are separate workflows |
| LOGIC-103: Steps 4-6 missing governance_mode guards | HIGH | Fixed: Step 4 now guarded with `if governance_mode in ("warn", "enforce")` |
| LOGIC-104: Enforce mode user acknowledgment interaction unclear | HIGH | Fixed: Added note that user acknowledgment satisfies Phase 5.5.2 enforce requirement |
| LOGIC-105: Phase 3 atomic spec contradicts line 224 | MEDIUM | Fixed: Line 224 updated to clarify temp-file+rename required for index append |
| SEC-001 (incomplete): YAML injection fix omits `output` field | CRITICAL | Fixed: Added `output` field to yaml.safe_dump() requirement in Decision item 3 |
| Phase 5.0.3 Step 4 missing governance guard | HIGH | Fixed: Step 4 now shows `(governance_mode in ("warn", "enforce"))` guard |

### Decision (COMP-002)

**COMP-002**: Phase 5 governance modes conflict with SKILL.md Non-Goal — SELECTED: **Option (A)**

Self-imposed blocking (`enforce` mode) is not a team coordination pattern. It is constitutional self-binding — past-self setting quality rules that present-self must satisfy. This is discipline, not governance overhead. The blocking is appropriate for solo-dev self-governance.

SKILL.md Non-Goals will be updated to scope-limit governance to solo-dev patterns when Phase 5 is implemented.

### Prior Round 1 BLOCKERs — Fixed

| Finding | Resolution |
|---------|-----------|
| LOGIC-001: `os.replace()` exception handling | Phase 3 now specifies try/except OSError, temp file deletion on failure |
| LOGIC-002: Phase 5.2 orchestration omits consistency check | Phase 5.2.4 Steps 4-10 now include consistency check |
| LOGIC-003: Consistency/Judge Agent violates Phase 5.0.4 constraint | Consistency/Judge Agent now "recommends to Orchestrator" |
| LOGIC-006: Python boolean error `("warn" or "enforce")` | Changed to explicit `if governance_mode in ("warn", "enforce"):` |
| FM-004: Unhandled PermissionError on Windows locking | Phase 3 specifies try/except around os.replace() |
| FM-005: load_arch_decision() corruption detection missing | Phase 3 specifies explicit corruption types and validation |
| FM-006: Index rewrite race with concurrent append | File locking protocol added for all index modifications |
| SEC-001 (partial): YAML frontmatter injection | Phase 3 requires yaml.safe_dump() for frontmatter fields |

---

## References

- `P:/packages/arch/skill/persistence.py` — current implementation (line 315: non-atomic write)
- `P:/packages/arch/skill/validate_templates.py` — current validation (no ordering)
- Perplexity analysis (internal) — original proposal document

---

**Confidence:** 90%

**Review status:** Pending
