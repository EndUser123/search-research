# Review Bundle: /design Skill
**Generated**: 2026-04-19
**Scope**: `P:/packages/cc-skills-sdlc/skills/design` — Architecture Advisor / Resource Router
**File Count**: 96 files (excluding cache)
**Execution Mode**: 4-agents (50+ files)

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Generated**: 2026-04-19
- **Scope**: `P:/packages/cc-skills-sdlc/skills/design` — Claude Code architecture advisory skill
- **File Count**: 96 non-cache files (SKILL.md, 18 Python modules, 11 reference MDs, 16 resource MDs, 47 test files)
- **Execution Mode**: 4-agents (50+ threshold exceeded)
- **Corrected from**: Wrong path `P:/.claude/skills/design` (not a junction; actual location is `P:/packages/cc-skills-sdlc/skills/design`)

### Domain & Purpose
`/design` is a template-based architecture advisor that routes queries to appropriate analysis templates based on domain and complexity. It auto-classifies intent (ARCHITECTURE_REVIEW, IMPROVE_SYSTEM, DEFAULT), evaluates multi-terminal concurrency safety, closes stateful contracts with Contract Authority Packets, and outputs ADR-formatted recommendations. Used by solo developers on Windows 11 for CLI-centric workflows.

### Scale Metrics
- **~1101 lines** in SKILL.md (main skill definition, v5.3)
- **18 Python modules** at root: routing, config, validate, results, persistence, prerequisite_analyzer, planning_handoff_validation, aid wrappers, arch_validate, cross_platform_paths
- **16 resource files**, **11 reference documents**, **47 test files**
- **Version**: 5.3 (from SKILL.md frontmatter)
- **Change frequency**: Active — version 5.3, CHANGELOG.md exists with recent entries

### Your Environment
- **OS**: Windows 11 Pro (bash shell, Unix-style paths)
- **Primary language**: Python 3.12+
- **Package managers**: pip
- **Key dependencies**: `fasteners` (InterProcessLock), `log_action` from csf_logging, CKS MCP server (optional)

---

## 2. ARCHITECTURE OVERVIEW

```
User query → /design
    │
    ├─ routing.py: select_template() ──► Template routing
    │   Priority: override → keyword → config → env → complexity
    │
    ├─ config.py: load_arch_config() ──► Cascading config (env → project → user)
    │
    └─ SKILL.md: Stage 0 → Stage 0.5 → Stage 1 → Stage 1.4-1.10 → Stage 2 → Stage 3
                   │
                   ├─ Stage 0: Pre-Flight (preset expansion, self-verification, bookend rule, out-of-scope)
                   ├─ Stage 0.5: Clarity Gate (follow-up detection, context inference)
                   ├─ Stage 1: Classify Intent + Domain + Complexity
                   ├─ Stage 1.4: Contract Sensitivity Classification
                   ├─ Stage 1.5: Contract Boundary Inventory
                   ├─ Stage 1.6: Contract Boundary Closure
                   ├─ Stage 1.7: Contract Authority Packet (CAP)
                   ├─ Stage 1.7b: Planning Handoff Packet
                   ├─ Stage 1.8: ADR Closure Consistency Check (4 gates)
                   ├─ Stage 1.9: ADR Critic Review (Gemini/Haiku conditional dispatch)
                   ├─ Stage 1.10: Intelligent Quality Check
                   ├─ Stage 2: Template Selection
                   └─ Stage 3: Execute Template → ADR output

Templates (resources/):
  base.md ── extended by ── fast.md, deep.md, cli.md, python.md, data-pipeline.md, precedent.md
```

### Subsystems

| Subsystem | Path | Purpose | Key Functions |
|---|---|---|---|
| **Routing** | `routing.py` (1099 lines) | Template selection | `select_template()`, `extract_template_override()`, `detect_domain_keywords()`, `detect_complexity()`, `detect_intent_type()`, `detect_follow_up_query()`, `retrieve_context_hint()`, `cks_semantic_search()` |
| **Config** | `config.py` (290 lines) | Cascading config | `load_arch_config()`, `clear_config_cache()`, `VALID_DOMAINS = {python, data-pipeline, precedent, cli, auto}` |
| **Validation** | `validate.py` (389 lines) | Template validation | `validate_template()` with 3-stage fail-fast pipeline |
| **Results** | `results.py` (106 lines) | ADR output structure | `ArchResult[T]` dataclass with unwrap methods |
| **Persistence** | `persistence.py` (1033 lines) | Auto-save to arch_decisions/ | `save_arch_decision()`, index rotation, CKS ingestion |
| **Prerequisite** | `prerequisite_analyzer.py` (366 lines) | Gap detection | Pattern-based gate triggering (PRD/Debug/Discover) |
| **Planning Handoff** | `planning_handoff_validation.py` (120 lines) | Plan validation | `validate_planning_handoff_contract()`, finding IDs ADR-003, ADR-HANDOFF-001 to 005 |
| **AID Integration** | `aid_wrapper.py`, `aid_wrapper_v2.py` | AID CLI wrapper | Wraps AID for code analysis |
| **Architecture Validation** | `arch_validate.py` (executable) | ADR validation | Validates ADR prose vs packet consistency |

---

## 3. EXECUTION AND DATA FLOW

### Stage Sequence (from execution-flow.md)

```
Phase 0: Entry
  └─ Multi-term/terminal/isolation preset expansion → Prerequisite gate check

Phase 1: Pre-Flight and Clarity
  ├─ Stage 0: Pre-Flight Checks (self-verification, out-of-scope, bookend rule)
  └─ Stage 0.5: Clarity Gate (follow-up detection, context inference)

Phase 2: Classification
  ├─ Template override (highest priority)
  ├─ ADF delegation check
  ├─ Intent type detection (ARCHITECTURE_REVIEW / IMPROVE_SYSTEM / DEFAULT)
  ├─ Domain detection (priority: config → env → keywords → complexity)
  └─ Complexity detection

Phase 3: Contract Closure (if contract-sensitive)
  ├─ Stage 1.4: Contract Sensitivity Classification
  ├─ Stage 1.5: Contract Boundary Inventory
  ├─ Stage 1.6: Contract Boundary Closure
  ├─ Stage 1.7: Contract Authority Packet
  └─ Stage 1.7b: Planning Handoff Packet

Phase 4: Consistency and Validation
  ├─ Stage 1.8: ADR Closure Consistency Check (4 gates: Safety, Router, Packet, Downstream)
  ├─ Stage 1.9: ADR Critic Review (conditional dispatch to Gemini or Haiku)
  └─ Stage 1.10: Intelligent Quality Check

Phase 5: Output
  └─ Stage 3: Execute Template → ADR output
```

### Template Execution

| Template | Extends | Complexity | Max Files | Output Size | Key Trait |
|---|---|---|---|---|---|
| `fast` | base | LOW | 3 | ~5KB | K=3 candidates, no GoT |
| `deep` | base + GoT + Lean | HIGH | 5 | ~15-30KB | K=4, GoT, adversarial, Lean |
| `cli` | base | Any | — | ~8KB | CLI-specific domain |
| `python` | base | Any | — | ~10KB | Python-specific domain |
| `data-pipeline` | base | Any | — | ~12KB | ETL/pipeline domain |
| `precedent` | base | Any | — | ~20KB | ADR-first output |

### Routing Priority (routing.py:select_template)
1. Explicit `template=<name>` override in query
2. Query-level template override (`template=X+Y+Z`)
3. Keyword detection (`cli`, `python`, `data-pipeline`, `precedent`)
4. Config file domain
5. Environment variable
6. Complexity-based fallback (deep vs fast)

### Constitutional Constraints (from SKILL.md)
- Multi-terminal safety evaluated on ALL decisions (constitutional-principles.md)
- Stateful contracts require: identity model, ordering, dedupe, freshness/invalidation, event source of truth, decision-closure status
- Producer/consumer boundaries require: boundary name, producer, consumer, input schema, output schema, freshness authority, invalidation trigger, failure behavior
- Contract Authority Packet mandatory for contract-sensitive designs before `/planning` handoff
- Schema-first authority: structured artifacts > prose; packet wins if packet vs prose disagree

### Fail-Closed Policy
- `unknown freshness` → block and reconstruct
- `schema mismatch` → reject and surface
- `validator timeout` → block or escalate
- `degrade/fail-open` → only if bounded blast radius named

---

## 4. COMPONENT INVENTORY

### Core Logic

| File | Purpose | Key Functions |
|---|---|---|
| `routing.py` (1099 lines) | Template selection logic | `select_template()`, `extract_template_override()`, `detect_domain_keywords()`, `detect_complexity()`, `detect_intent_type()`, `detect_follow_up_query()`, `cks_semantic_search()` |
| `config.py` (290 lines) | Cascading config (env→project→user) | `load_arch_config()`, `clear_config_cache()`, `VALID_DOMAINS` |
| `validate.py` (389 lines) | Template validation 3-stage pipeline | `_check_file_exists()`, `_check_duplicates()`, `_check_permissions()` |
| `results.py` (106 lines) | ADR result generation | `ArchResult[T]` dataclass with `unwrap()`, `unwrap_or()`, `unwrap_error()` |
| `persistence.py` (1033 lines) | Auto-save drafts | `save_arch_decision()`, index rotation (1000→500), CKS ingestion, metrics logging |
| `prerequisite_analyzer.py` (366 lines) | Prerequisite gate detection | Pattern categories: OPTIMIZATION (no gate), PRD (/prd), DISCOVER (/discover), DEBUG (/debug) |
| `planning_handoff_validation.py` (120 lines) | Planning handoff validation | `validate_planning_handoff_contract()`, finding IDs ADR-003, ADR-HANDOFF-001 to 005 |
| `cross_platform_paths.py` (executable) | Cross-platform path handling | Path normalization for Windows |
| `path_detection.py` (executable) | Path detection | Detects project structure |
| `arch_validate.py` (executable) | ADR validation | Validates prose vs packet consistency |

### Templates (resources/)

| File | Size | Purpose |
|---|---|---|
| `base.md` | 29,410 | Shared stages foundation — Stage 0 through Stage 3 for all templates |
| `fast.md` | 3,368 | Lightweight: K=3 candidates, 1-2 searches, ~5KB output |
| `deep.md` | 5,692 | Heavyweight: K=4 candidates, GoT, Lean, adversarial, ~15-30KB |
| `cli.md` | 8,055 | CLI domain template |
| `python.md` | 8,447 | Python 3.12+ domain template |
| `data-pipeline.md` | 11,820 | ETL/pipeline domain template |
| `precedent.md` | 9,609 | ADR-first template |
| `shared_frameworks.md` | 39,985 | Reusable: Lean, CKS, adversarial, evidence system, template contracts |
| `evidence_system.md` | 8,917 | Evidence tier system for confidence claims |
| `hook_registration_consistency.md` | 10,050 | Hook registration consistency check |
| `template_contracts.yaml` | 5,596 | YAML-based template validation contracts |

### References

| File | Purpose |
|---|---|
| `scope-and-contract.md` | Scope constraints, input contract, "when not to use" routing |
| `constitutional-principles.md` | Full constitutional principles including multi-terminal safety |
| `execution-flow.md` | Execution flow diagrams and state machine |
| `got-integration.md` | Graph-of-Thought node types (DECISION/CONSTRAINT/DEPENDENCY/RISK/TRADEOFF), edge analysis (SUPPORTS/CONTRADICTS/DEPENDS/MITIGATES) |
| `lean-system-design.md` | Lean principles: value optimization, core vs extended plans, dependency pruning |
| `quality-model.md` | 8 architectural lenses, ISO 25010 mapping |
| `routing-contract.md` | Input-to-template routing contract |
| `adr-and-enhancements.md` | ADR template, graph-aware reasoning |
| `gemini-adr-critic-prompt.md` | Gemini prompt for Stage 1.9 ADR critic |
| `state-machine.md` | Core states for architecture |

### Infrastructure

| File | Purpose |
|---|---|
| `aid_wrapper.py` (32KB) | AID CLI integration for codebase analysis |
| `aid_wrapper_v2.py` (23KB) | AID wrapper v2 implementation |
| `aid_integration.py` | AID integration logic |
| `tests/` (47 files) | Comprehensive test suite with 291 tests, 87% coverage |
| `architecture/metrics.md` | Decision metrics tracking (invariant protection, option diversity, tail exploration, judge vetoes) |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars
1. **Template-based routing**: Domain + complexity → appropriate template
2. **Schema-first authority**: Structured artifacts (CAP) > prose
3. **Multi-terminal safety**: Every decision evaluates concurrent safety
4. **Contract closure before handoff**: CAP mandatory before `/planning`
5. **Evidence-grounded**: WebSearch + CKS + codebase reading before conclusions
6. **ADR-first output**: Default concise ADR format; verbose opt-in

### Template Chaining Rules
- Max 2 templates chained
- `precedent` cannot be secondary
- `fast`/`deep` are complexity selectors, not chainable
- All parts must be in VALID_DOMAINS allowlist

### Decision Policy Modes
- `balanced` (default): reliability 1.0x, flexibility 1.0x
- `risk_averse`: reliability 2.0x, flexibility 0.5x — for data safety, release decisions
- `exploratory`: reliability 0.5x, flexibility 2.0x — for prototyping

### Critical Invariants
1. Only `fast`, `deep`, `cli`, `python`, `data-pipeline`, `precedent` are valid templates
2. Contract Authority Packet supersedes prose if they disagree
3. Unknown freshness → block (not fail-open)
4. No handoff to `/planning` without closed CAP
5. Config cache uses mtime-based invalidation; only one config combo cached (`maxsize=1`)

### Bookend Rule (Stage 0, Item 6)
Added 2026-04-19 after H2 false positive in yt-is nlm_batch.py review:
- **Location**: SKILL.md lines 336-362
- **Trigger**: Diagnosis concludes "X is not cleaned up before Y" or "no cleanup before Z"
- **Rule**: Read to natural boundary (end of function/try-finally/call chain) before concluding
- **Falsification**: "This check would be wrong if the function is not always called sequentially (async, threaded, or signal-handler context)"
- **Reference case**: Prevents "no `cleanup()` before `_add_sources_in_subbatches`" false positive (finally block at line 1195 fires after extraction, before next batch)

---

## 6. KNOWN ISSUES

1. **Config cache collision**: `maxsize=1` LRU cache means only one config combination is cached; changing env vars mid-session may not invalidate cache as expected.
2. **CKS dependency**: Semantic search falls back to keyword search if CKS unavailable; no offline mode causes degraded evidence quality.
3. **H2 false positive (RESOLVED)**: "no cleanup before add" in nlm_batch.py was wrong — `finally: cleanup()` at line 1195 fires after extraction. Resolved by adding bookend rule to Stage 0.

---

## 7. INTEGRATION POINTS

### Entry Contract
- **Trigger**: `/design <query>` or `/arch <query>`
- **Query parsing**: `template=<name>`, `template=X+Y+Z`, preset keywords (`multi-term`, `multi-terminal`, `terminal-isolation`)
- **Output**: ADR format to stdout, auto-save draft to `arch_decisions/`

### Downstream Handoff
- `/design` → `/planning`: Requires closed Planning Handoff Packet
- `/design` → `/verify`: For "does architecture still hold" queries
- `/design` → `/qr`: Stage 1.10 for strategic quality check

### External Dependencies
- **CKS MCP server**: Optional semantic search (graceful degradation if unavailable)
- **AID CLI**: Optional codebase analysis via `aid_wrapper.py`
- **log_action()**: Structured logging via `csf_logging`
- **fasteners.InterProcessLock**: Cross-process locking for config cache

### Config Cascade
```
Environment vars (highest priority)
    ↓
Project config (.archconfig.json)
    ↓
User config (~/.archconfig.json)
    ↓
Defaults (lowest)
```

---

## 8. INPUT/OUTPUT CONTRACT

### Per-Phase Data Flow

| Phase | Reads | Writes | Key Constraint |
|---|---|---|---|
| Stage 0 | SKILL.md, relevant source files for gap verification | None | Must read files before claiming gap exists; bookend rule requires reading to natural boundary |
| Stage 0.5 | `routing.py:detect_follow_up_query()`, session transcript | None | Follow-up is retrieval signal, not gap |
| Stage 1 | Query text, routing.py config | None | Template routing decision |
| Stage 1.4–1.7 | Relevant source files for boundary analysis | Contract Authority Packet (if contract-sensitive) | CAP required before planning handoff |
| Stage 1.8 | Generated ADR draft | Consistency check report | 4 gates must pass before output |
| Stage 1.9 | `gemini-adr-critic-prompt.md`, ADR draft | Critic JSON to `arch_validate.json` | Blocks on HIGH severity |
| Stage 1.10 | ADR draft | `/qr` strategic quality output | Loops back on Critical |
| Stage 2–3 | Template file (resources/*.md) | Final ADR output | Must read template before executing |

### Agent Read Sources
N/A — `/design` does not dispatch parallel agents. It runs as a single synchronous skill with internal template loading.

### Quality Gates

| Gate | Checks | Does NOT Check |
|---|---|---|
| Stage 1.8 Safety Policy | Contract boundaries not fail-open by default | Content accuracy |
| Stage 1.8 Router | Router activation/bypass/failure criteria explicit | Routing correctness |
| Stage 1.8 Packet | CAP shape matches schema, summary vs packet consistency | Prose quality |
| Stage 1.8 Downstream | ADR claims about `/planning`/`/code`/`/verify` match skill contracts | Future contract changes |
| Stage 1.9 Critic | 5 defect classes: Safety, Router, Packet, Downstream, Unresolved | Stylistic preference |
| Stage 1.10 `/qr` | Strategic quality: soundness, pattern fit, tech fit, engineering balance | Detailed implementation |

---

## 9. AGENT DISPATCH DEFINITIONS

Not applicable — `/design` does not dispatch parallel agents. It runs as a single synchronous skill with internal template loading.

Stage 1.9 uses a conditional external dispatch to Gemini (via `ai_cli.py`) or Haiku fallback, but this is a single sequential call within Stage 1.9, not a parallel agent dispatch.

---

## 10. FAILURE SCENARIOS

### Scenario 1: Partial Read → False Gap Claim
- **Trigger**: Stage 0.2 self-verification reads file A, concludes "X is missing", but file B (not read) contains the missing behavior
- **Propagation**: False gap becomes architecture recommendation
- **Detection**: Stage 1.8 ADR consistency check catches contradictions
- **Root cause**: Reading only the call site, not the natural boundary (e.g., reading line X but not the `finally` at line Y)
- **Fix applied**: Bookend rule (Stage 0 item 6) — mandates reading to natural boundary before "missing cleanup" conclusions

### Scenario 2: Stale CAP → Downstream Mismatch
- **Trigger**: ADR references `/planning` contract behavior from outdated file state
- **Propagation**: `/planning` receives inconsistent handoff, builds on wrong assumption
- **Detection**: Stage 1.8 downstream alignment gate (requires rereading cited files)
- **Root cause**: Cached evidence used as current evidence
- **Fix**: Gate requires fresh file reads for cited evidence

### Scenario 3: Template File Missing → Silent Fallback
- **Trigger**: `resources/<template>.md` doesn't exist or has syntax error
- **Propagation**: Template validation (`validate.py`) should catch this; graceful degradation may produce wrong template
- **Detection**: `validate_templates.py` test suite
- **Root cause**: File existence check without schema validation

### Scenario 4: CKS Unavailable → Degraded Evidence
- **Trigger**: CKS MCP server not configured or unavailable
- **Propagation**: `cks_semantic_search()` falls back to keyword search; semantic results unavailable
- **Detection**: CKS unavailable flag (`CKS_AVAILABLE`) — graceful degradation, no hard failure
- **Root cause**: External dependency not enforced

### Scenario 5: Config Cache Stale After Env Change
- **Trigger**: User changes `ARCH_DEFAULT_DOMAIN` env var after config already cached
- **Propagation**: `load_arch_config()` returns stale cached config (maxsize=1 means only first call cached)
- **Detection**: `clear_config_cache()` must be called manually
- **Root cause**: No env-var change detection in LRU cache

---

## 11. APPENDIX: KEY FILE LOCATIONS

```
P:/packages/cc-skills-sdlc/skills/design/
├── SKILL.md                          # Main skill definition (v5.3, 1101 lines)
├── routing.py                        # Template routing logic (1099 lines)
├── config.py                        # Cascading config loader (290 lines)
├── validate.py                      # Template validation (389 lines)
├── results.py                       # ADR output generation (106 lines)
├── persistence.py                    # Auto-save drafts (1033 lines)
├── prerequisite_analyzer.py           # Prerequisite gate detection (366 lines)
├── planning_handoff_validation.py   # Handoff packet validation (120 lines)
├── cross_platform_paths.py          # Windows path handling
├── path_detection.py                # Project path detection
├── arch_validate.py                 # ADR validation (executable)
├── aid_wrapper.py / aid_wrapper_v2.py  # AID CLI integration
├── validate_templates.py            # Template validation script
├── resources/
│   ├── base.md                      # Shared template foundation (29KB)
│   ├── fast.md                      # Lightweight template (3KB)
│   ├── deep.md                      # Heavyweight template (6KB)
│   ├── cli.md / python.md / data-pipeline.md / precedent.md
│   ├── shared_frameworks.md          # Lean, CKS, adversarial (40KB)
│   ├── evidence_system.md           # Confidence tier system
│   ├── hook_registration_consistency.md
│   └── template_contracts.yaml      # Template validation
├── references/
│   ├── execution-flow.md            # Stage sequence diagrams
│   ├── got-integration.md            # Graph-of-Thought (node types, edge analysis)
│   ├── lean-system-design.md        # Lean principles
│   ├── quality-model.md             # 8 architectural lenses
│   ├── scope-and-contract.md        # Scope constraints
│   ├── constitutional-principles.md   # Multi-terminal safety rules
│   ├── routing-contract.md           # Routing table
│   ├── adr-and-enhancements.md       # ADR format
│   ├── gemini-adr-critic-prompt.md  # Critic prompt
│   └── state-machine.md             # Core states
├── architecture/
│   └── metrics.md                   # Decision metrics tracking
└── tests/                           # 47 test files, 291 tests, 87% coverage
```