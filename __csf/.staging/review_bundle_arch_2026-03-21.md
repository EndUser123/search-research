# Review Bundle: Architecture Advisor (`/arch`)

**Generated:** 2026-03-21
**Scope:** `P:/packages/arch`
**File Count:** 98 files (43 Python modules, 35 test files, 6 templates, 6 docs)
**Execution Mode:** Single-agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Package:** `arch` - Adaptive Architecture Advisor
- **Location:** `P:/packages/arch`
- **Version:** 4.4
- **License:** MIT

### Domain & Purpose

The `/arch` skill is a template-based architecture advisor that provides intelligent architecture guidance by analyzing user queries and routing them to specialized templates. It serves as a strategic decision-support tool for software architecture choices, featuring auto-routing to domain-specific templates (fast, deep, cli, python, data-pipeline, precedent) based on keyword detection, configuration files, and complexity analysis.

### Scale Metrics
- **Total Files:** 98
- **Python Modules:** 43
- **Test Files:** 35
- **Test Count:** 291 passed, 11 skipped
- **Test Coverage:** 87% (3494 lines, 471 uncovered)
- **Templates:** 6 domain-specific
- **Output:** ~5-30 KB depending on template

### Environment
- **Python:** 3.12+
- **Dependencies:** None (core is pure Python)
- **Optional:** LLM providers for custom recommendations
- **Dev Tools:** pytest, ruff, mypy

---

## 2. ARCHITECTURE OVERVIEW

```
                         ┌─────────────────────────────────────┐
                         │        /arch SKILL INVOCATION        │
                         └─────────────────┬───────────────────┘
                                           │
                      ┌────────────────────┼────────────────────┐
                      ▼                    ▼                    ▼
              ┌───────────────┐  ┌─────────────────┐  ┌─────────────────┐
              │   config.py   │  │  routing.py     │  │ persistence.py  │
              │  Configuration│  │  Template       │  │  Decision       │
              │  Loader with  │  │  Routing &      │  │  Archive        │
              │  Cascading    │  │  Validation     │  │  Persistence    │
              │  Priority     │  │  Logic          │  │                 │
              └───────┬───────┘  └────────┬────────┘  └────────┬────────┘
                      │                    │                    │
                      └────────────────────┼────────────────────┘
                                           ▼
              ┌─────────────────────────────────────────────────────┐
              │              TEMPLATE RESOURCES                     │
              │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐  │
              │  │ fast.md │ │ deep.md │ │ cli.md  │ │ python.md│  │
              │  │ 5-15min │ │40-90min │ │10-20min │ │15-25min  │  │
              │  │  ~5KB   │ │~15-30KB │ │  ~8KB   │ │  ~10KB   │  │
              │  └─────────┘ └─────────┘ └─────────┘ └──────────┘  │
              │  ┌─────────────────┐ ┌─────────────────┐            │
              │  │ data-pipeline.md│ │  precedent.md   │            │
              │  │   20-30min     │ │   60-90min      │            │
              │  │    ~12KB       │ │    ~20KB        │            │
              │  └─────────────────┘ └─────────────────┘            │
              └─────────────────────────────────────────────────────┘
                                           │
                      ┌────────────────────┼────────────────────┐
                      ▼                    ▼                    ▼
              ┌───────────────┐  ┌─────────────────┐  ┌─────────────────┐
              │  prerequisite │  │ validate_       │  │   aid_wrapper   │
              │  _analyzer.py │  │ templates.py    │  │ / aid_integration│
              │  Semantic     │  │ Template         │  │  AI Distiller   │
              │  Analysis     │  │ Validation       │  │  Integration    │
              │  Gates        │  │ & Duplicate      │  │                 │
              │               │  │ Detection        │  │                 │
              └───────────────┘  └─────────────────┘  └─────────────────┘
```

### Subsystem: Configuration System

| Component | Path | Responsibility |
|-----------|------|----------------|
| `config.py` | `skill/config.py` | Cascading config loader (project → user → env → keywords) |

### Subsystem: Template Routing

| Component | Path | Responsibility |
|-----------|------|----------------|
| `routing.py` | `skill/routing.py` | Template selection, validation, keyword detection |
| `prerequisite_analyzer.py` | `skill/prerequisite_analyzer.py` | Semantic gating for optimization queries |
| `validate_templates.py` | `skill/validate_templates.py` | Template validation, duplicate detection |

### Subsystem: Persistence & Integration

| Component | Path | Responsibility |
|-----------|------|----------------|
| `persistence.py` | `skill/persistence.py` | Decision archival to `.claude/arch_decisions/` |
| `aid_wrapper.py` | `skill/aid_wrapper.py` | AI Distiller integration |
| `aid_integration.py` | `skill/aid_integration.py` | External AI caller integration |

### Subsystem: Cross-Platform Support

| Component | Path | Responsibility |
|-----------|------|----------------|
| `cross_platform_paths.py` | `skill/cross_platform_paths.py` | Path resolution across OS |
| `path_detection.py` | `skill/path_detection.py` | Template path detection |

### Templates

| Template | Use Case | Output | Time |
|----------|----------|--------|------|
| `fast` | Quick decisions | ~5 KB | 5-15 min |
| `deep` | Complex multi-system | ~15-30 KB | 40-90 min |
| `cli` | CLI/POSIX specific | ~8 KB | 10-20 min |
| `python` | Python 3.12+ specific | ~10 KB | 15-25 min |
| `data-pipeline` | Data systems | ~12 KB | 20-30 min |
| `precedent` | ADR documentation | ~20 KB | 60-90 min |

---

## 3. EXECUTION AND DATA FLOW

### Template Selection Flow

```
User Query
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. Configuration Cascading Priority                          │
│    Project .archconfig.json → User ~/.archconfig.json →     │
│    Env ARCH_DEFAULT_DOMAIN → Keywords                       │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Prerequisite Analysis                                    │
│    prerequisite_analyzer.analyze(query)                     │
│    → is_optimization query? → may skip deep analysis       │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Template Selection                                      │
│    routing.select_template(query, override)                │
│    → Domain detection via keywords                          │
│    → Template chaining support (max 2)                     │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Template Validation                                     │
│    routing.validate_template(template)                      │
│    → File existence check                                  │
│    → Duplicate detection                                   │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Persistence Decision                                    │
│    persistence.should_skip_persistence(query, output)      │
│    → Save to .claude/arch_decisions/                      │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
                         OUTPUT
```

### Configuration Cascade

| Priority | Source | Example |
|----------|--------|---------|
| 1 | Project | `.archconfig.json` in project root |
| 2 | User | `~/.archconfig.json` |
| 3 | Environment | `ARCH_DEFAULT_DOMAIN=python` |
| 4 | Keywords | Auto-detected from query |

---

## 4. COMPONENT INVENTORY

### Core Logic

| Module | Path | Responsibility | Key Functions |
|--------|------|----------------|----------------|
| `config.py` | `skill/config.py` | Configuration loading | `load_arch_config()`, `VALID_DOMAINS` |
| `routing.py` | `skill/routing.py` | Template selection | `select_template()`, `validate_template()` |
| `persistence.py` | `skill/persistence.py` | Decision archival | `save_arch_decision()`, `should_skip_persistence()` |
| `prerequisite_analyzer.py` | `skill/prerequisite_analyzer.py` | Semantic gating | `PrerequisiteAnalyzer.analyze()` |
| `validate_templates.py` | `skill/validate_templates.py` | Template validation | `validate_templates()`, `detect_duplicate_templates()` |

### Utilities/Helpers

| Module | Path | Responsibility |
|--------|------|----------------|
| `cross_platform_paths.py` | `skill/cross_platform_paths.py` | OS-agnostic path resolution |
| `path_detection.py` | `skill/path_detection.py` | Template file discovery |
| `aid_wrapper.py` | `skill/aid_wrapper.py` | AI Distiller wrapper |
| `aid_integration.py` | `skill/aid_integration.py` | External AI integration |

### Resources (Templates)

| Template | Path | Purpose |
|----------|------|---------|
| `fast.md` | `skill/resources/fast.md` | Quick decisions template |
| `deep.md` | `skill/resources/deep.md` | Comprehensive analysis template |
| `cli.md` | `skill/resources/cli.md` | CLI/POSIX specific guidance |
| `python.md` | `skill/resources/python.md` | Python 3.12+ specific guidance |
| `data-pipeline.md` | `skill/resources/data-pipeline.md` | Data systems guidance |
| `precedent.md` | `skill/resources/precedent.md` | ADR documentation template |
| `shared_frameworks.md` | `skill/resources/shared_frameworks.md` | Common template frameworks |

### Tests (35 files)

| Category | Count | Coverage |
|----------|-------|----------|
| Config tests | 8 | Merging, types, validation, caching, integration, thread-safety, real-files |
| Routing tests | 3 | Template routing, overlap validation |
| Persistence tests | 1 | Decision archival |
| Performance tests | 3 | Deterministic, caching, real |
| Security tests | 4 | Path traversal, dry enforcement, template override |
| Integration tests | 6 | CKS fallback, real import, config integration, external caller |
| Platform tests | 2 | Cross-platform, real platform |
| Other tests | 8 | Type hints, error messages, result structure, etc. |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars

1. **Template-Based, Not LLM-Generated:** Same inputs → same architecture recommendations for reproducibility
2. **Auditability:** Clear mapping from requirements to pattern selection
3. **Speed Over Generality:** Instant recommendations vs LLM generation latency
4. **Cascading Configuration:** Project → User → Environment → Keywords priority

### Technology Constraints
- **Python 3.12+** required
- **No external dependencies** for core (LLM providers optional)
- **Cross-platform:** Windows, macOS, Linux path handling

### Performance SLAs
- **Template Selection:** <100ms (deterministic)
- **Configuration Loading:** <50ms with caching
- **Prerequisite Analysis:** <20ms

### Things That Must NOT Change
- **Template routing algorithm:** Keyword → domain → template mapping
- **Configuration cascade priority:** Project > User > Env > Keywords
- **Persistence location:** `.claude/arch_decisions/` for searchability
- **Chaining limit:** Maximum 2 templates combined

---

## 6. KNOWN ISSUES

### Issue 1: Test Coverage Gap (13% uncovered)

**Scenario:** 471 lines remain uncovered out of 3494 total.

**Expected:** >85% coverage maintained
**Actual:** 87% current, some edge cases in error handling uncovered
**Impact:** Rare error paths may have undetected bugs
**Workaround:** Additional tests for error handling paths needed

### Issue 2: CKS Integration Fallback

**Scenario:** CKS (Constitutional Knowledge System) integration uses fallback on import failure.

**Expected:** Graceful degradation when CKS unavailable
**Actual:** Tests verify fallback behavior rather than real CKS
**Impact:** Architecture advice may lack constitutional context when CKS down
**Workaround:** `test_cks_fallback.py` validates degraded mode

### Issue 3: Path Detection Edge Cases

**Scenario:** `path_detection.py` may fail on non-standard project layouts.

**Expected:** Template detection across varied project structures
**Actual:** Tests cover standard layouts; edge cases not fully tested
**Impact:** May not find templates in unusual project configurations
**Workaround:** Explicit config override available

---

## 7. INTEGRATION POINTS

### CLI Invocation
```bash
/arch "improve memory system"           # Auto-detect
/arch "redesign api" template=deep     # Force template
/arch "async data pipeline" template=python+data-pipeline  # Chain
```

### Python API
```python
from arch.config import load_arch_config
from arch.routing import select_template, validate_template
from arch.persistence import save_arch_decision

config = load_arch_config()
result = select_template("improve memory system")
validation = validate_template("fast")
save_arch_decision(query="...", output="...", template="fast")
```

### Configuration Schema
```json
{
  "$schema": "./.archconfig.schema.json",
  "default_domain": "python",
  "output_size": "normal",
  "evidence_level": "standard"
}
```

### Valid Domains
- `cli` - CLI/POSIX architecture
- `python` - Python 3.12+ architecture
- `data-pipeline` - Data systems architecture
- `precedent` - ADR documentation
- `auto` - Keyword-based detection

---

## 8. APPENDIX: KEY METRICS

| Metric | Value |
|--------|-------|
| Version | 4.4 |
| Total Files | 98 |
| Python Modules | 43 |
| Test Files | 35 |
| Tests Passed | 291 |
| Tests Skipped | 11 |
| Test Coverage | 87% |
| Templates | 6 |
| Valid Domains | 5 |

### ADR One-Page Template (v4.4)

```markdown
# ADR-XXXX: [Decision Title]

**Status:** Proposed | Accepted | Superseded by ADR-YYYY
**Date:** YYYY-MM-DD
**Context:** [What problem does this solve?]

### Decision
[One-line decision statement]

### Rationale
[Why this approach - brief, 2-3 sentences]

### Tradeoffs
| Quality | Improved | Degraded |
|---------|----------|----------|
| [ISO 25010] | [Benefit] | [Cost] |

### Multi-Terminal Safety
- [Safe / Single-terminal only / Needs investigation]

### Implementation
- [What changes: files, APIs, structures]
- [Testing approach]
- [Rollback: how to undo]

### Consequences
- **Positive:** [Benefits]
- **Negative:** [Costs/risks with mitigations]
```

### Graph.txt Format (Optional)

```txt
# Architecture Graph: [System Name]

# Components
[ComponentA]
  depends_on: [ComponentB, ComponentC]
  provides: [ServiceX, ServiceY]
  risks: [SinglePointOfFailure]

# Relationships
ComponentA → ComponentB: synchronous_call

# Contradictions
ConstraintA contradicts IdeaB: [Explanation]

# Cycles Detected
[None] or [Cycle: ComponentA → ComponentB → ComponentA]
```
