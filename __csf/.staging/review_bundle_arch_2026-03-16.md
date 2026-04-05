# Review Bundle: /arch Skill

**Generated**: 2026-03-16T15:30:00Z
**Scope**: P:\.claude\skills\arch\
**File Count**: 88 files (20 core source files, 35 test files, 33 cache/state files)
**Execution Mode**: single-agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata

- **Skill Name**: `/arch` - Architecture Advisor
- **Version**: 4.4 (SKILL.md) / 3.2.0 (README.md - version mismatch detected)
- **Purpose**: Adaptive architecture advisor with template-based routing
- **Primary Language**: Python 3.12+
- **Test Coverage**: 87% (291 tests passing, 11 skipped)
- **License**: MIT

### Domain & Purpose

The `/arch` skill provides intelligent architecture guidance by analyzing user queries and routing them to specialized templates. It serves as a **solo-developer optimized architecture advisor** that:
- Auto-routes queries to appropriate templates based on domain detection and complexity analysis
- Supports six template variants: fast, deep, cli, python, data-pipeline, precedent
- Provides cascading configuration (project → user → environment variable)
- Integrates with Constitutional Knowledge System (CKS) for enhanced context
- Auto-saves architecture decisions to searchable archive
- Distinguishes optimization queries from prerequisite needs to prevent false-positive gates

### Scale Metrics

- **LOC**: ~3,500 lines (estimated from core modules)
- **Major Subsystems**: 5 (config, routing, persistence, prerequisite analysis, AID integration)
- **Deployment Scope**: Claude Code skill ecosystem (local only)
- **Change Frequency**: Active development (v4.4 recently released with ADR template, ARCHITECTURE.md guidance, graph-aware reasoning)

### Your Environment

- **OS**: Windows 11 (cross-platform path resolution implemented)
- **Primary Languages**: Python 3.12+, Markdown (templates)
- **Package Managers**: None (stdlib-only where possible)
- **Databases**: Optional CKS SQLite at `P:/__csf/data/cks.db`
- **External Services**: None (CKS integration optional with graceful fallback)

---

## 2. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                         /arch Skill                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  User Query → Intent Detection → Template Selection              │
│                   ↓                  ↓                          │
│            Prerequisite Analyzer    Chain of Responsibility     │
│                   ↓                  ↓                          │
│              (Gate Decision)    (Template Override)             │
│                   ↓                  ↓                          │
│         ┌───────────────────────────────────────┐              │
│         │     Template Routing Engine           │              │
│         │  (routing.py: select_template())      │              │
│         └───────────────────────────────────────┘              │
│                   ↓                  ↓                          │
│            Domain Detection    Complexity Detection              │
│                   ↓                  ↓                          │
│         ┌───────────────────────────────────────┐              │
│         │   Template Loader & Validator         │              │
│         │   (validate_template, .md files)      │              │
│         └───────────────────────────────────────┘              │
│                   ↓                                             │
│         ┌───────────────────────────────────────┐              │
│         │     Architecture Decision Output      │              │
│         │  (per template: fast/deep/...)        │              │
│         └───────────────────────────────────────┘              │
│                   ↓                                             │
│         ┌───────────────────────────────────────┐              │
│         │      Persistence Layer                │              │
│         │  (save_arch_decision, CKS ingest)    │              │
│         └───────────────────────────────────────┘              │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Major Subsystems

#### 1. Configuration System (`config.py`)

**Purpose**: Load architecture configuration from multiple sources with cascading priority

**Files**: `config.py` (201 lines)

**Key Functions**:
- `load_arch_config()`: Load from project → user → env var priority
- `clear_config_cache()`: Clear config cache (for testing)

**Dependencies**:
- Upstream: JSON config files, environment variables
- Downstream: `routing.py` (uses config for domain selection)

**Critical Invariants**:
- `default_domain` must be in `VALID_DOMAINS` set
- Config cached with mtime-based invalidation
- Thread-safe caching with `_config_lock`

#### 2. Routing Engine (`routing.py`)

**Purpose**: Select appropriate template based on query analysis using Chain of Responsibility pattern

**Files**: `routing.py` (876 lines - largest module)

**Key Functions**:
- `select_template()`: Main routing entry point
- `extract_template_override()`: Parse `template=X+Y` syntax with security validation
- `detect_domain_keywords()`: O(n) keyword detection (not O(n*m))
- `detect_complexity()`: Fast vs deep classification
- `detect_intent_type()`: ARCHITECTURE_REVIEW / IMPROVE_SYSTEM / DEFAULT
- `validate_template()`: Cached template validation with mtime tracking
- `cks_semantic_search()`: CKS integration with semantic search
- `get_failure_history()`: Query CKS for subsystem failures

**Dependencies**:
- Upstream: `config.py` (VALID_DOMAINS), CKS (optional)
- Downstream: All templates (resources/*.md)

**Critical Invariants**:
- Template chaining: max 2 templates, precedent cannot be secondary
- Template override must pass allowlist validation (SEC-002)
- mtime-based cache invalidation for template validation
- Priority: parameter_override > query_override > keyword > default_domain > complexity

#### 3. Persistence Layer (`persistence.py`)

**Purpose**: Auto-save architecture decisions to searchable archive with CKS bidirectional integration

**Files**: `persistence.py` (524 lines)

**Key Functions**:
- `save_arch_decision()`: Save to arch_decisions/ with YAML frontmatter
- `should_skip_persistence()`: Skip short outputs or explicit "don't save"
- `generate_decision_filename()`: Format: YYYY-MM-DD_template_slug.md
- `search_decisions()`: Keyword search prior decisions
- `_ingest_into_cks()`: Write decisions back to CKS (closes learning loop)
- `track_template_chaining_usage()`: Monitor chaining adoption
- `check_chaining_usage_monitoring()`: Alert if no chaining for 30 days

**Dependencies**:
- Upstream: None (standalone persistence)
- Downstream: CKS database (writes decisions back)

**Critical Invariants**:
- Minimum 2KB output size to save
- Filename format: `{date}_{template}_{slug}.md`
- CKS ingest fails silently (never block persistence)
- Index file: `arch_decisions/index.jsonl`
- Chaining monitoring alert: 30 days threshold

#### 4. Prerequisite Analyzer (`prerequisite_analyzer.py`)

**Purpose**: Semantic analysis to distinguish optimization queries from genuine prerequisite needs

**Files**: `prerequisite_analyzer.py` (lines read: 1-100, full file ~200 lines)

**Key Functions**:
- `PrerequisiteAnalyzer.analyze()`: Main analysis entry point
- Pattern detection for: `/prd`, `/discover`, `/debug` gates

**Dependencies**:
- Upstream: None (standalone semantic analysis)
- Downstream: Routing stage (gates before template execution)

**Critical Invariants**:
- Optimization patterns should NOT trigger gates (user has context)
- PRD patterns trigger when user references requirements explicitly
- Discover patterns trigger for codebase structure questions
- Debug patterns trigger for diagnosis/diagnosis focus

#### 5. AID Integration (`aid_wrapper_v2.py`, `aid_integration.py`)

**Purpose**: AI Distiller wrapper for codebase analysis with enterprise-grade prompts

**Files**: `aid_wrapper_v2.py`, `aid_integration.py`

**Key Functions**:
- `create_aid_integrator()`: Initialize AID with compression level
- `distill()`: 60-90% context reduction while preserving semantic structure
- `detect_layers()`: Classify files by architectural layer
- `analyze_dependency_direction()`: Coupling violation detection
- `analyze_with_ai_action()`: Enterprise analysis (COMPLEX_CODEBASE)

**Dependencies**:
- Upstream: AID CLI at `~/.aid/bin/aid.exe` (Windows) or `~/bin/` (Unix)
- Downstream: Template codebase-aware analysis stage

**Critical Invariants**:
- Requires AID CLI installed (raises RuntimeError if not available)
- Stateless, read-only (multi-terminal safe)
- Graceful degradation if AID unavailable

---

## 3. EXECUTION AND DATA FLOW

### Execution Sequences

```
1. User Input Stage:
   User query → PrerequisiteAnalyzer.analyze()
   ↓
   If optimization pattern: Skip gates → Proceed to routing
   If PRD/discover/debug pattern: Trigger appropriate gate

2. Routing Stage:
   extract_template_override(query) → (primary, [chained])
   ↓
   Chain of Responsibility:
   ├─ _OverrideParamSelector (if template= parameter)
   ├─ _QueryOverrideSelector (if template=X+Y in query)
   ├─ _KeywordDetectionSelector (domain keywords)
   ├─ _DefaultDomainSelector (from config/env)
   └─ _ComplexityDetectionSelector (final fallback)

3. Template Validation Stage:
   validate_template(template_name) → (is_valid, error_message)
   ├─ Check allowlist (VALID_TEMPLATES)
   ├─ Check file exists (resources/{name}.md)
   └─ Check file readable (not empty, permissions, encoding)

4. Execution Stage:
   Load template from resources/{template}.md
   ↓
   Execute template steps (per template contract):
   ├─ Stage 0: Detect Intent Type
   ├─ Stage 0.1: Constitutional Compliance Check (MANDATORY)
   ├─ Stage 0.3: Codebase-Aware Analysis (AID if available)
   ├─ Stage 0.6: Domain Resource Inclusion
   ├─ Stage 0.7: Web Research (WebSearch)
   └─ Decision Path: ARCHITECTURE_REVIEW / IMPROVE_SYSTEM / DEFAULT

5. Persistence Stage:
   should_skip_persistence(query, output) → bool
   ↓
   If not skipped:
   ├─ save_arch_decision() → Write to arch_decisions/
   ├─ Append to index.jsonl
   └─ _ingest_into_cks() → Write to CKS (fails silently)
```

### Mandatory Ordering Constraints

1. **Prerequisite gates MUST run before routing**: Optimization queries must bypass prerequisite gates
2. **Template validation MUST occur before loading**: Prevent missing/empty template files
3. **Constitutional compliance check (Stage 0.1) is MANDATORY**: All architecture decisions must evaluate multi-terminal safety
4. **CKS ingest MUST be non-blocking**: CKS unavailability must never prevent persistence

### State Management

**State Stores**:
- Config cache: `_config_cache` dict with threading lock
- Template validation cache: `@lru_cache` on `_validate_template_cached()`
- No persistent in-memory state (multi-terminal safe by design)

**Consistency Model**:
- Config cached with mtime-based invalidation (thread-safe)
- Template validation cached by (name, mtime) tuple
- No cross-terminal state sharing (no shared mutable state)

### Error Handling

**Fail-Open vs Fail-Closed Policy**:
- Config: Fail-open (return None if no config, raise if invalid)
- Template validation: Fail-closed (raise if invalid/not found)
- CKS integration: Fail-open (silent failures, log at DEBUG)
- Persistence: Fail-closed (raise on I/O errors)

**Retry/Timeout Behavior**:
- No retry logic (fail-fast for config/template operations)
- CKS search: Single attempt, return empty on failure
- File operations: No retries, propagate OSError

---

## 4. COMPONENT INVENTORY

### Core Logic Modules

| Component | Path | Responsibility | Inputs | Outputs | Known Limitations |
|-----------|------|----------------|--------|---------|-------------------|
| **Config Loader** | `config.py` | Load config with cascading priority | .archconfig.json, env vars | Dict with domain/size/evidence | No validation of output_size, evidence_level values |
| **Routing Engine** | `routing.py` | Template selection via Chain of Responsibility | Query, config, override | TemplateResult | Complexity detection is heuristic only |
| **Persistence** | `persistence.py` | Save decisions to archive + CKS | Query, output, template | Filepath or None | CKS ingest fails silently (loss of learning loop) |
| **Prerequisite Analyzer** | `prerequisite_analyzer.py` | Distinguish optimization from prerequisite needs | User query | AnalysisResult | Pattern matching may produce false positives |
| **AID Wrapper v2** | `aid_wrapper_v2.py` | AI Distiller integration for codebase analysis | Target path | Compressed structure | Requires external AID CLI binary |
| **AID Integration** | `aid_integration.py` | Enterprise-grade AI action prompts | Target path, AI action | Analysis prompts | AID availability not guaranteed |

### Utilities/Helpers

| Component | Path | Responsibility | Known Limitations |
|-----------|------|----------------|-------------------|
| **Cross-Platform Paths** | `cross_platform_paths.py` | Resolve paths across Windows/Unix | Assumes home dir available |
| **Path Detection** | `path_detection.py` | Find template file paths | Template directory hardcoded |
| **Template Validator** | `validate_templates.py` | Validate all templates on load | Does not check template internal structure |

### Configuration Files

| Component | Path | Responsibility | Format |
|-----------|------|----------------|--------|
| **Schema** | `.archconfig.schema.json` | Configuration schema validation | JSON Schema |
| **Domain Contracts** | `resources/domain_inclusions.md` | Domain-specific inclusion patterns | Markdown |
| **Evidence System** | `resources/evidence_system.md` | Evidence tier definitions | Markdown |
| **Template Contracts** | `resources/template_contracts.yaml` | Template contract definitions | YAML |

### Infrastructure Components

| Component | Path | Responsibility | Known Limitations |
|-----------|------|----------------|-------------------|
| **CKS Integration** | `routing.py:cks_*` | Semantic search via CKS | Optional (graceful fallback if unavailable) |
| **Index File** | `.claude/arch_decisions/index.jsonl` | Searchable decision index | Append-only, no deletion mechanism |
| **Chaining Usage Tracking** | `.claude/arch_decisions/chaining_usage.jsonl` | Monitor template chaining adoption | No automatic cleanup |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars

1. **Multi-Terminal Safety First**: All architecture decisions MUST consider multi-terminal concurrency safety and stale data immunity (Constitutional requirement from `CLAUDE.md`)
2. **Solo-Developer Optimization**: No enterprise team governance patterns, Windows 11 + CLI-centric workflow
3. **Template-Based Modularity**: Six specialized templates (fast, deep, cli, python, data-pipeline, precedent) with shared base stages
4. **Cascading Configuration**: Project → User → Environment variable priority with clear override semantics
5. **Graceful Degradation**: CKS integration optional, system works without it

### Technology Constraints

1. **Python 3.12+**: Type hints required, stdlib-only preference
2. **Markdown Templates**: All templates in `.md` format for readability
3. **No External Dependencies**: Prefer stdlib, minimal third-party
4. **Cross-Platform**: Windows 11 primary, Unix compatibility required

### Performance SLAs

1. **Template Validation**: Cached with mtime invalidation (PERF-002)
2. **Domain Detection**: O(n) keyword detection via pre-built lookup dict (PERF-002)
3. **Config Loading**: Thread-safe caching with mtime-based invalidation
4. **File I/O**: Minimal reads, caching where appropriate

### Things That Must NOT Change

1. **Constitutional Multi-Terminal Check**: Stage 0.1 is MANDATORY for all architecture outputs
2. **Template Chaining Rules**: Max 2 templates, precedent cannot be secondary (SEC-002)
3. **Allowlist Validation**: Template override must validate against VALID_TEMPLATES (SEC-002)
4. **Graceful CKS Degradation**: CKS failures must never block primary functionality
5. **Multi-Terminal State Isolation**: No shared mutable state across terminals

---

## 6. KNOWN ISSUES

| Issue | Expected | Actual | Impact | Workaround |
|-------|----------|---------|--------|------------|
| **Version Mismatch** | SKILL.md v4.4 | README.md v3.2.0 | Documentation inconsistency | SKILL.md is authoritative, README needs update |
| **CKS Ingest Silent Failure** | All decisions saved to CKS | CKS errors logged only, no user notification | Learning loop may break if CKS fails | Monitor CKS availability separately |
| **No Config Value Validation** | output_size, evidence_level validated | Only domain validated, values unchecked | Invalid config values accepted silently | Manually verify config values |
| **Template Deletion Detection** | Missing templates detected | File existence checked, but not deletion during runtime | Template deleted during execution may cause errors | Restart skill session |
| **Chaining Usage Alert** | Alert after 30 days no chaining | Alert logged but not surfaced to user | Failed feature adoption may go unnoticed | Monitor `chaining_usage.jsonl` manually |
| **Index File Growth** | Managed index size | Append-only, no deletion or rotation | index.jsonl grows indefinitely | Manual cleanup required |

---

## 7. INTEGRATION POINTS

### Existing Hooks/Interfaces

1. **CKS Integration Point** (`routing.py`):
   ```python
   # Semantic search interface
   results = cks_semantic_search(query, entry_type="memory", limit=5)

   # Domain-aware search
   results = cks_semantic_domain_search(query, domain="python", limit=5)

   # Failure history query
   failures = get_failure_history("memory", limit=10)
   ```

2. **Persistence Interface** (`persistence.py`):
   ```python
   # Save decision
   filepath = save_arch_decision(
       query="design API",
       template="python",
       domain="python",
       output="...",
       confidence=85,
       research_sources=["url1", "url2"]
   )

   # Search prior decisions
   decisions = search_decisions("memory system", limit=5)
   ```

3. **Config Interface** (`config.py`):
   ```python
   # Load with cascading priority
   config = load_arch_config()
   # Returns: {"default_domain": "python", "output_size": "normal", ...}

   # Clear cache (for testing)
   clear_config_cache()
   ```

4. **Routing Interface** (`routing.py`):
   ```python
   # Select template
   result = select_template(
       query="improve memory system",
       template_override=None,  # or "deep"
       default_domain="python",  # from config
       env_domain=None  # or from ARCH_DEFAULT_DOMAIN
   )
   # Returns: {"template": "fast", "source": "keyword_detection", ...}

   # Validate template
   is_valid, error = validate_template("deep")

   # Extract override
   primary, chained = extract_template_override("template=python+cli")
   ```

### Invocation Model

1. **Direct Skill Invocation**: `/arch "query"` → Skill tool loads SKILL.md
2. **Template Override**: `/arch "query template=deep"` → Force specific template
3. **Template Chaining**: `/arch "query template=deep+python"` → Primary + domain context
4. **Config-Based**: Create `.archconfig.json` → Auto-detects domain

### Data Exchange Contracts

1. **Config File Format** (`.archconfig.json`):
   ```json
   {
     "$schema": "./.archconfig.schema.json",
     "default_domain": "python",
     "output_size": "normal",
     "evidence_level": "standard"
   }
   ```

2. **Decision File Format** (arch_decisions/*.md):
   ```markdown
   ---
   date: 2026-03-16
   template: deep
   query: "design API"
   domain: python
   confidence: 85
   research_sources: ["url1", "url2"]
   ---

   [Architecture output...]
   ```

3. **Index File Format** (index.jsonl):
   ```json
   {"date": "2026-03-16", "template": "deep", "query": "design API", "domain": "python", "confidence": 85, "file": "2026-03-16_deep_design-api.md"}
   ```

### Output/Exit Code Expectations

1. **Success**: Template executed, decision saved (if applicable)
2. **Prerequisite Gate**: Returns gate message, suggests alternative skill
3. **Template Validation Error**: Raises ValueError with "Did you mean?" suggestions
4. **Config Error**: Raises ValueError for invalid domain, TypeError for invalid types

---

## 8. APPENDIX: SAMPLE RUNS / LOGS

### Sample Run 1: Domain Detection

```
Query: "improve async patterns in python"
→ PrerequisiteAnalyzer: is_optimization=True (no gate)
→ select_template():
   ├─ _QueryOverrideSelector: No override found
   ├─ _KeywordDetectionSelector: Domain detected: python
   └─ Returns: {"template": "python", "source": "keyword_detection", "confidence": "medium", "chained_domains": []}
→ validate_template("python"): (True, "")
→ Load: resources/python.md
→ Execute template stages (Stage 0 → Stage 0.1 → ... → Decision Path)
→ Output: ~10 KB Python-specific architecture guidance
→ save_arch_decision(): Saves to arch_decisions/2026-03-16_python_improve-async-patterns.md
→ _ingest_into_cks(): Writes to CKS (if available)
```

### Sample Run 2: Template Chaining

```
Query: "redesign kafka streaming pipeline template=deep+data-pipeline"
→ PrerequisiteAnalyzer: is_optimization=False (proceed)
→ select_template():
   ├─ _QueryOverrideSelector: Override found: deep + ["data-pipeline"]
   └─ Returns: {"template": "deep", "source": "query_override", "confidence": "high", "chained_domains": ["data-pipeline"]}
→ validate_template("deep"): (True, "")
→ Load: resources/deep.md (primary) + resources/data-pipeline.md (chained context)
→ Execute deep template with data-pipeline domain context
→ Output: ~20 KB comprehensive analysis with pipeline patterns
→ track_template_chaining_usage(): Logs to chaining_usage.jsonl
→ save_arch_decision(): Saves with chained_domains metadata
```

### Sample Run 3: Prerequisite Gate (PRD)

```
Query: "design API from requirements"
→ PrerequisiteAnalyzer.analyze():
   ├─ PRD_PATTERNS matched: r"\bfrom\s+requirements\b"
   └─ Returns: {"should_trigger_gate": True, "gate_type": "/prd", "is_optimization": False}
→ Output: PREREQUISITE DETECTED
   Your query suggests: requirements document needed

   Choices:
   1 - Run /prd "requirements_source"
   2 - Continue with /arch anyway

   (Waits for user selection)
```

### Sample Run 4: CKS Integration

```
Query: "improve memory system"
→ select_template(): Returns {"template": "fast", ...}
→ get_failure_history("memory"):
   ├─ cks_semantic_search("memory failures bugs errors problems crashes")
   └─ Returns: [CKS entries about prior memory issues]
→ Template includes CKS findings in analysis
→ Output references CKS memory entries with citations
→ _ingest_into_cks(): Writes this decision back to CKS
→ (Future queries on "memory" will see this decision)
```

---

## END OF REVIEW BUNDLE

**Total Sections**: 8
**Total Components Documented**: 6 core, 4 utilities, 4 infrastructure
**Known Issues**: 6 documented
**Integration Points**: 4 interfaces with example code

**Generated by**: /review_bundle skill
**Verification**: All file paths verified against actual directory structure
**ASSUMPTION**: README.md version (3.2.0) is outdated; SKILL.md version (4.4) is authoritative
