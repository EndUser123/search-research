---
name: arch
description: Adaptive architecture advisor with template-based variants. Auto-routes to appropriate template based on domain and complexity. Supports: fast, deep, cli, python, data-pipeline, precedent. Configuration: .archconfig.json (project) → ~/.archconfig.json (user) → ARCH_DEFAULT_DOMAIN (env var). Override with template=<name> parameter.

category: architecture
triggers:
  - arch
  - architecture
  - architectural decision

governance:
  layer1_enforcement: true
  usage_markers:
    - "Stage 0:"
    - "Stage 1:"
    - "PREREQUISITE DETECTED"
    - "Classify Intent"
    - "Template:"
    - "Out-of-Scope"
    - "Architecture Template"
    - "ARCHITECTURE_REVIEW"
---

# Architecture Advisor (Resource Router)

## Overview

This skill routes architecture queries to specialized templates based on domain and complexity. Templates are loaded from `.claude/skills/arch/resources/{template}.md` (relative to project root) and executed inline.

**No Skill() tool calls to arch-* skills.** Templates are read and executed directly.

---

## Stage 0: Pre-Flight Checks (Out-of-Scope Detection)

Before routing, check if the query is out-of-scope for architecture analysis.

### Out-of-Scope Patterns

**IMPORTANT:** Prerequisite gates should only trigger when actual requirements are missing, not for optimization or improvement queries.

| Pattern | Detected When (strict semantic analysis) | Suggest | Rationale |
|---------|------------------------------------------|---------|-----------|
| Missing requirements | Explicit mentions of "from requirements", "no specs loaded", "PRD needed", "requirements not loaded", "where are requirements" | `/prd "<requirement_source>"` | Architecture needs requirements foundation |
| Unknown codebase | First-time context, "how is X structured", "how is this organized", no prior file reads | `/discover "<area>"` | Need codebase understanding before design |
| Debug/diagnosis focus | Primary intent is diagnosis: "why failing", "broken", "error", "crash", "bug in", "not working" | `/debug "<issue>"` or `/rca "<issue>"` | Diagnosis before architecture |
| Planning phase | "how to build", "steps for", "plan to implement", "implementation approach" | `/plan "<feature>"` or `/breakdown "<task>"` | Planning precedes architecture |
| Verification focus | "verify", "check my work", "is this correct", "did I implement right" | `/verify "<target>"` | Verification before redesign |
| Research needed | "how does X work", "learn about", "understand", "research" | `/research "<topic>"` | Understanding before decisions |
| Deployment/ship | "deploy", "ship", "release", "production ready" | `/qa` (QA certification) | QA before deployment |

### False Positive Prevention

**Do NOT trigger prerequisite gates for:**
- Optimization queries ("improve X", "optimize Y", "harden Z")
- Improvement queries with clear context ("improve memory system")
- Architecture decision requests ("should I use X or Y")
- Design pattern questions ("is this a good pattern")
- **Architecture/Design REVIEW queries** — "review this design", "evaluate this architecture"
  - Reviews are valid EVEN for theoretical/unimplemented designs
  - Never gate reviews behind installation or implementation status
  - The point of reviewing architecture is to evaluate BEFORE building
- **Follow-up queries with preceding context**: Never reject a query as out-of-scope if the preceding turn presented architectural options, alternatives, or trade-offs — treat the follow-up as referencing that context and proceed to Stage 1

**These should proceed to Stage 1 classification:**

### If Out-of-Scope Detected

```
PREREQUISITE DETECTED

Your query suggests: [detected pattern]

Architectural analysis works best after [prerequisite].

Choices:
1 - Run /[suggested_skill] "[suggested_prompt]"
    [Brief explanation of what this does and why needed]

2 - Continue with /arch anyway
    [Warning: may produce limited results without context]

Response: "1" or "2"
```

**WAIT for user selection before proceeding.**

### No Out-of-Scope Detected

Proceed to Stage 1: Classify Intent.

---

## Stage 1: Classify Intent

From the user query and any `template=` parameter, determine:

### 1. Check for Template Override

```
If query contains "template=<name>":
    Use specified template directly
    Skip domain detection
    Proceed to Stage 3
```

**Valid template names:**
- `fast` - Quick decisions (5-15 min, ~5 KB)
- `deep` - Comprehensive analysis (40-90 min, ~15-30 KB)
- `cli` - CLI/POSIX specific
- `python` - Python 3.12+ specific
- `data-pipeline` - Data systems specific
- `precedent` - ADR documentation

**Template chaining (explicit):**
- `template=python+data-pipeline` — Python as primary, data-pipeline domain concerns merged
- Max 2 templates. `precedent` cannot be secondary. `fast`/`deep` are complexity selectors, not chainable.
- See **Template Chaining** in `shared_frameworks.md` for merge protocol.

### 2. Check for ADF Delegation (Extract/New Boundary Detection)

**Route to `/adf` when query asks about extraction/justification:**

```
adf_gate_keywords = [
    # Direct extraction questions
    "should i extract", "is creating X justified", "should i create.*module",
    "should i create.*service", "should i create.*class", "add abstraction",
    # Boundary/structure questions
    "new boundary", "new service", "new module", "separate.*concern",
    "extract.*service", "extract.*module", "split.*into",
    # Justification questions
    "is.*worth it", "is.*justified", "justify.*change", "justify.*extraction",
    # Over-engineering concerns
    "over-engineering", "overkill", "too complex", "unnecessary.*layer"
]

For each keyword pattern (case-insensitive):
    If pattern matches query:
        Route to /adf with message:
        "This requires architecture decision evaluation.

Your query suggests: [matched pattern]

Choices:
1 - Run /adf \"[query]\" to evaluate whether this structural change is justified
    Evaluates WHETHER the change is needed before designing HOW

2 - Continue with /arch \"[query]\" anyway
    Bypasses the justification gate and proceeds directly to architecture design

Response: \"1\" or \"2\""
        STOP (wait for user selection)
```

**Rationale:** `/adf` evaluates **whether** a structural change is justified (gate), while `/arch` provides **how** to design it. Extraction/justification questions require the gate first.

### 3. Detect Intent Type

```
improve_keywords = ["improve", "optimize", "harden", "stabilize", "enhance", "strengthen"]
subsystem_keywords = ["memory", "cks", "hooks", "research", "retro", "lesson", "ingestion", "validation"]
review_keywords = ["review", "evaluate", "assess", "analyze", "audit", "validate", "critique"]
design_keywords = ["design", "architecture", "integration", "proposal", "theoretical", "blueprint"]

# ARCHITECTURE_REVIEW: Explicit review of design/architecture
# Reviews are valid EVEN for theoretical/unimplemented designs
if any review_keyword AND (any design_keyword or "integration" in query.lower()):
    intent_type = "ARCHITECTURE_REVIEW"

# IMPROVE_SYSTEM: Optimize existing subsystem
elif any improve_keyword AND any subsystem_keyword:
    intent_type = "IMPROVE_SYSTEM"

# DEFAULT: General architecture decision
else:
    intent_type = "DEFAULT"
```

### 4. Detect Domain (if no override)

**Domain priority:** Project config → User config → Environment variable → Keywords → Complexity

**Config file `.archconfig.json`:**
```json
{
  "$schema": "./.archconfig.schema.json",
  "default_domain": "python",
  "output_size": "normal",
  "evidence_level": "standard"
}
```

**Valid `default_domain` values:** `cli`, `python`, `data-pipeline`, `precedent`, `auto` (keyword detection)

**Detection order:**
```
# Step 2a: Load config file (cascading priority)
from .config import load_arch_config

config = load_arch_config()
domain = None  # Initialize
if config and config.get("default_domain") != "auto":
    domain = config["default_domain"]
elif config and config.get("default_domain") == "auto":
    # Fall through to keyword detection
    pass

# Step 2b: Domain keyword detection (always runs - explicit keywords override config)
# This allows query keywords to override even non-auto config domains
keyword_domain = None
domain_keywords = {
    "cli": ["cli", "command line", "terminal", "shell", "posix", "exit code", "argument parsing"],
    "python": ["python", "asyncio", "type hint", "pydantic", "fastapi", "flask", "django", "async", "await", "decorator", "context manager"],
    "data-pipeline": ["etl", "elt", "pipeline", "streaming", "batch", "kafka", "spark", "airflow", "dagster", "prefect", "warehouse", "data lake"],
    "precedent": ["adr", "decision record", "precedent", "document decision", "architecture decision record"]
}

For each domain, check if any keyword appears in query (case-insensitive)
If multiple domains match:
    # Template chaining — see shared_frameworks.md "Template Chaining"
    primary = domain with most keyword matches
    secondary = domain with next most matches
    keyword_domain = f"{primary}+{secondary}"
    # Execute primary template, augment with secondary domain concerns
    # Max 2 templates chained. precedent cannot be secondary.
If single domain match:
    keyword_domain = <matched domain>

# Step 2c: Final domain selection (keywords override config)
if keyword_domain:
    domain = keyword_domain  # Explicit keywords override any config
elif not domain:
    # No config and no keywords - will fall through to complexity detection
    pass
```

**Configuration methods (ordered by priority):**

| Method | Location | Priority | Persistence |
|--------|----------|----------|
| Project config | `.archconfig.json` (in project root) | 1 (highest) | Per-project, can be committed |
| User config | `~/.archconfig.json` | 2 | Global to all projects |
| Environment var | `ARCH_DEFAULT_DOMAIN=python` | 3 | Per-session only |
| Keywords | Query content | 4 (fallback) | Automatic |

**Usage notes:**
- Project config overrides user config (allows per-project specialization)
- User config overrides environment variable
- `default_domain: "auto"` enables keyword-only detection
- Explicit keywords always override default domain
- `template=` override always takes highest priority

### 5. Detect Complexity (if no domain match)

```
high_complexity_indicators = [
    "redesign", "overhaul", "architecture", "microservices",
    "from scratch", "rewrite", "replace", "multi-system",
    "service boundary", "schema migration", "breaking change"
]

If any high_complexity_indicator found:
    complexity = "deep"
Else:
    complexity = "fast"
```

---

## Stage 2: Select Template

### Template Selection Logic

```
template_selection:

# 1. Override takes highest priority
if template_override:
    selected_template = template_override

# 2. Domain-specific templates take priority over complexity
elif domain == "cli":
    selected_template = "cli"
elif domain == "python":
    selected_template = "python"
elif domain == "data-pipeline":
    selected_template = "data-pipeline"
elif domain == "precedent":
    selected_template = "precedent"

# 3. Fall back to complexity-based
elif complexity == "deep":
    selected_template = "deep"
else:
    selected_template = "fast"
```

### Template Metadata Reference

| Template | Target Complexity | Target Domain | Output Size | Use Case |
|----------|-------------------|---------------|-------------|----------|
| fast | LOW | Generic | ~5 KB | Quick decisions, single file |
| deep | HIGH | Generic | ~15-30 KB | Complex decisions, multi-system |
| cli | Any | CLI/POSIX | ~8 KB | Command-line tools |
| python | Any | Python 3.12+ | ~10 KB | Python-specific |
| data-pipeline | Any | Data Systems | ~12 KB | ETL/ELT, streaming |
| precedent | Any | ADR | ~20 KB | Decision documentation |

---

## Stage 3: Load and Execute Template

### Template Validation (Before Loading)

**Before attempting to load the template, validate:**

```python
# Validation check
from pathlib import Path

VALID_TEMPLATES = {"fast", "deep", "cli", "python", "data-pipeline", "precedent"}

# 1. Validate template name (supports chaining: "template+template")
if "+" in selected_template:
    # Template chaining: validate each part
    parts = selected_template.split("+")
    if len(parts) > 2:
        error_msg = f"Invalid template chain '{selected_template}'. Max 2 templates allowed."
        raise ValueError(error_msg)
    for part in parts:
        if part not in VALID_TEMPLATES:
            error_msg = f"Invalid template '{part}' in chain. Valid templates: {', '.join(sorted(VALID_TEMPLATES))}"
            raise ValueError(error_msg)
    # Validate chaining rules
    if "precedent" in parts[1:]:  # precedent cannot be secondary
        error_msg = f"Invalid template chain: 'precedent' cannot be secondary template."
        raise ValueError(error_msg)
    if any(p in {"fast", "deep"} for p in parts[1:]):  # fast/deep are not chainable
        error_msg = f"Invalid template chain: 'fast' and 'deep' are complexity selectors, not chainable."
        raise ValueError(error_msg)
elif selected_template not in VALID_TEMPLATES:
    error_msg = f"Invalid template '{selected_template}'. Valid templates: {', '.join(sorted(VALID_TEMPLATES))}"
    raise ValueError(error_msg)

# 2. Validate template file exists
template_path = Path(f".claude/skills/arch/resources/{selected_template}.md")
if not template_path.exists():
    error_msg = f"Template file not found: {template_path}"
    raise FileNotFoundError(error_msg)

# 3. Validate template is readable
try:
    # Test read access
    with open(template_path) as f:
        first_line = f.readline()
    if not first_line:
        error_msg = f"Template file is empty: {template_path}"
        raise ValueError(error_msg)
except Exception as e:
    error_msg = f"Cannot read template file {template_path}: {e}"
    raise IOError(error_msg)
```

### Template Loading

**IMPORTANT:** Use Read tool to load template content. Do NOT use Skill() tool.

```python
# Template path (validated above)
template_path = f".claude/skills/arch/resources/{selected_template}.md"

# Load template
template_content = Read(template_path)
```

### Template Execution

1. **Read and understand** the template's execution instructions
2. **Follow** the template's decision tree exactly
3. **Execute** the appropriate path (ARCHITECTURE_REVIEW, IMPROVE_SYSTEM, or DEFAULT)
4. **Return** output in the template's specified format

**Do NOT:**
- Restate template instructions
- Summarize or paraphrase the template
- Skip template stages
- Deviate from the template's decision tree

**Do:**
- Execute steps sequentially
- Follow decision tree exactly
- Keep output focused unless user requests depth
- Stop at each decision point and evaluate

---

## Routing Contract Table

| Input | Domain | Complexity | Template | Time | Output |
|-------|--------|------------|----------|------|--------|
| "improve memory system" | Generic | LOW | fast | 5-10 min | ~5 KB |
| "design a CLI tool" | cli | Any | cli | 10-20 min | ~8 KB |
| "python async architecture" | python | Any | python | 15-25 min | ~10 KB |
| "build data pipeline" | data-pipeline | Any | data-pipeline | 20-30 min | ~12 KB |
| "document this decision" | precedent | Any | precedent | 60-90 min | ~20 KB |
| "review integration architecture" | Generic | Any | deep (review path) | 20-40 min | ~10-15 KB |
| "template=deep redesign api" | Override | Override | deep | 40-90 min | ~15-30 KB |

---

## Quick Reference Table

### Domain-Specific Templates

| Domain | Template | Trigger Keywords |
|--------|----------|------------------|
| CLI/POSIX | cli | cli, command line, terminal, shell, posix, exit code, argument parsing |
| Python | python | python, asyncio, type hint, pydantic, fastapi, flask, django |
| Data Pipeline | data-pipeline | etl, elt, pipeline, streaming, batch, kafka, spark, airflow |
| ADR | precedent | adr, decision record, precedent, document decision |

### Complexity-Based Templates

| Template | Complexity | Trigger Keywords |
|----------|------------|------------------|
| fast | LOW | Default for simple decisions |
| deep | HIGH | redesign, overhaul, architecture, microservices, from scratch, rewrite |

### Template Override

```
/arch "query template=deep"       → Force deep template
/arch "query template=cli"         → Force CLI template
/arch "query template=python"      → Force Python template
/arch "query template=data-pipeline" → Force data-pipeline template
/arch "query template=precedent"   → Force precedent template
```

---

## Philosophy

- **Domain-first routing:** Domain-specific expertise beats generic complexity
- **Three intent paths:** ARCHITECTURE_REVIEW, IMPROVE_SYSTEM, and DEFAULT
- **Review-first principle:** Architecture reviews are valid for theoretical designs—never gate behind implementation
- **Evidence-grounded:** WebSearch + WebFetch for current best practices before recommending
- **Template-based execution:** Read and execute, don't delegate
- **Override support:** Users can force specific templates
- **No skill delegation:** Templates are executed inline, not via Skill() tool
- **CKS + Web:** Internal evidence (CKS.db, 492 entries) combined with external research

---

## Template File Locations

All templates are stored at:
```
.claude/skills/arch/resources/
├── fast.md
├── deep.md
├── cli.md
├── python.md
├── data-pipeline.md
├── precedent.md
├── shared_frameworks.md
├── cks_query_templates.md
└── evidence_system.md
```

---

## Execution Flow Summary

```
User Query
    ↓
Stage 0: Pre-Flight Checks (Out-of-Scope Detection)
    ↓ (in-scope)
Stage 1: Classify Intent
    ├─→ Template override? (incl. chaining: template=X+Y) → Use specified
    ├─→ ADF gate triggered? → Route to /adf
    ├─→ ARCHITECTURE_REVIEW detected? → Use review path
    ├─→ IMPROVE_SYSTEM detected? → Use improvement path
    ├─→ Multiple domains match? → Template chaining (primary + secondary)
    ├─→ Single domain detected? → Use domain template
    └─→ Complexity detected? → Use fast/deep
    ↓
Stage 2: Select Template
    ↓
Stage 3: Load Template (Read tool)
    ↓
Execute Template:
    Stage 0.3: Codebase-Aware Analysis (Glob/Read actual code)
    Stage 0.5: Domain Resource Inclusion
    Stage 0.7: Web Research (WebSearch + WebFetch)
    ↓
    Decision Path (ARCHITECTURE_REVIEW / IMPROVE_SYSTEM / DEFAULT)
        ├─ Forced Alternative Quality Gate (distinctiveness check) [DEFAULT only]
        ├─ Version Verification Rule (no unverified claims)
        ├─ Confidence Calibration (evidence-tiered scoring)
        └─ Adversarial Self-Review (weakest assumption challenge)
    ↓
    Output Persistence (auto-save to arch_reviews/ or arch_decisions/)
    ↓
Return Output
```

---

## CLI Help

### Available Templates

| Template | Use Case | Output Size | Time |
|----------|----------|-------------|------|
| `fast` | Quick decisions, single file | ~5 KB | 5-15 min |
| `deep` | Complex decisions, multi-system | ~15-30 KB | 40-90 min |
| `cli` | CLI/POSIX specific | ~8 KB | 10-20 min |
| `python` | Python 3.12+ specific | ~10 KB | 15-25 min |
| `data-pipeline` | Data systems specific | ~12 KB | 20-30 min |
| `precedent` | ADR documentation | ~20 KB | 60-90 min |

### Configuration Options

| Method | Location | Priority |
|--------|----------|----------|
| Project config | `.archconfig.json` | 1 (highest) |
| User config | `~/.archconfig.json` | 2 |
| Environment var | `ARCH_DEFAULT_DOMAIN` | 3 |
| Keywords | Auto-detection | 4 |

### Valid Domains

- `cli` - CLI/POSIX architecture
- `python` - Python 3.12+ architecture
- `data-pipeline` - Data systems architecture
- `precedent` - ADR documentation
- `auto` - Keyword-based detection

### Usage Examples

```bash
# Force specific template
/arch "redesign api" template=deep
/arch "cli tool" template=cli

# Review architecture (new ARCHITECTURE_REVIEW path)
/arch "review this integration design"

# Use project config domain
# (requires .archconfig.json with default_domain set)
/arch "improve error handling"
```

### Template Override

```
/arch "<query>" template=<name>
```

Valid template names: `fast`, `deep`, `cli`, `python`, `data-pipeline`, `precedent`

### Domain Keywords

| Domain | Keywords |
|--------|----------|
| CLI | cli, command line, terminal, shell, posix, exit code, argument parsing |
| Python | python, asyncio, type hint, pydantic, fastapi, flask, django |
| Data Pipeline | etl, elt, pipeline, streaming, batch, kafka, spark, airflow |
| Precedent | adr, decision record, precedent, document decision |

---

**Version:** 4.0 | **Architecture:** Template-based router with ARCHITECTURE_REVIEW intent type, review-first principle, and three-path execution (ARCHITECTURE_REVIEW / IMPROVE_SYSTEM / DEFAULT)
