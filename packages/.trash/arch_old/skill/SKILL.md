---
name: arch
description: "Adaptive architecture advisor with template-based variants. Auto-routes to appropriate template based on domain and complexity. Supports: fast, deep, cli, python, data-pipeline, precedent. Configuration: .archconfig.json (project) → ~/.archconfig.json (user) → ARCH_DEFAULT_DOMAIN (env var). Override with template=<name> parameter. Enhanced with Graph-of-Thought (GoT) for architecture alternatives analysis (v2.5)."

category: architecture
triggers:
  - arch
  - architecture
  - architectural decision
workflow_steps:
  - preflight_checks
  - classify_intent
  - select_template
  - load_template
  - execute_template_analysis
  - generate_architecture_review

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
  evidence_requirements:
    - codebase_reading: Read relevant files before suggesting changes
    - web_research: Use WebSearch + WebFetch for current best practices
    - framework_docs: Verify framework-specific patterns via /context7 (Next.js App Router, Django 5+, etc.)
    - confidence_scoring: Evidence-tiered confidence calibration
    - adversarial_review: Challenge weakest assumptions
  output_persistence: Auto-save to arch_decisions/
  cross_template_validation: Validate template chaining syntax before execution

---

# Architecture Advisor (Resource Router)

## Overview

This skill routes architecture queries to specialized templates based on domain and complexity. Templates are loaded from `.claude/skills/arch/resources/{template}.md` (relative to project root) and executed inline.

**No Skill() tool calls to arch-* skills.** Templates are read and executed directly.

---

## Context Contract (Hard Preconditions)

### Scope Constraints (HARD LIMITS)

**Context: Solo Developer, Windows 11, CLI-Centric Workflow**

`/arch` is optimized for:
- **Solo development** (single developer, no team collaboration overhead)
- **Windows 11 host** (local development, POSIX-compliant tools)
- **CLI-centric workflows** (terminal-based tools, not web/UX)
- **Multi-terminal safety required** (constitutional: per-terminal state isolation)

**Non-Goals (Out of Scope):**
- Multi-team governance patterns (team coordination, approval workflows)
- Solo-dev governance (constitutional self-binding: past-self setting rules for present-self) is IN SCOPE — Phase 5 enforce/warn modes are constitutional self-binding, not team coordination
- Cloud-native infrastructure design (AWS/Azure deployment patterns)
- Web application UX concerns
- Enterprise SLA compliance (ISO 27001, SOC 2, etc.)

**When query falls outside these constraints**, `/arch` will either:
1. Redirect to appropriate skill (`/plan` for team coordination, `/qa` for deployment)
2. Provide analogical guidance with explicit scope disclaimers
3. Reject with "out of scope" message if no analogical mapping exists

### Input Contract (Minimal Requirements)

**Expected Inputs for Optimal Results:**

| Input | Description | Example |
|-------|-------------|---------|
| **Current repo/workspace description** | What codebase are we working with? | "Python hooks system in P:/.claude/hooks/" |
| **Primary value goal(s)** | What matters most for THIS iteration? | "Improve multi-terminal isolation", "Reduce context bloat" |
| **Known constraints** | Hardware, tools, time, platform limits | "Windows-only, no external deps, stdlib preference" |
| **Risk tolerance** | Prefer robustness vs speed vs simplicity? | "Prefer robustness over iteration speed" |

**Risk tolerance maps loosely to ISO 25010 qualities:**
- **Prefer robustness** → Reliability, Security, Maintainability
- **Prefer speed** → Performance Efficiency, Time-to-Market
- **Prefer simplicity** → Maintainability, Portability

**Missing inputs?** `/arch` will infer from context or ask clarifying questions. For ambiguous queries, expect: "What's the primary goal for this architecture work?"

---

## When Not to Use `/arch`

`/arch` is **not appropriate** when:

| Scenario | Why Not | Use Instead |
|----------|---------|-------------|
| **Multi-team governance/compliance** | `/arch` assumes solo dev, no coordination overhead | `/plan` for team workflow design |
| **Managed cloud services architecture** | `/arch` targets local CLI tools, not cloud infra | Cloud provider's Well-Architected Framework |
| **Web/UX-dominated concerns** | `/arch` focuses on CLI ergonomics, not user interfaces | UX design specialists, web framework docs |
| **Deployment/production readiness** | `/arch` designs architecture, doesn't verify runtime readiness | `/qa` for production readiness checks |
| **Debug/diagnosis focus** | Architecture evaluation ≠ bug investigation | `/debug` or `/rca` for root cause analysis |

**When in doubt**, try `/arch` — it will redirect if another skill is better suited.

---

## Architectural Lenses

`/arch` applies 8 architectural lenses through the Lean System Design and GoT frameworks:

| Lens | Question It Asks | Industry Parallel |
|------|------------------|-------------------|
| **1. Value Lens** | Does this component advance core goals? | AWS Cost Optimization |
| **2. Consolidation Lens** | Are we duplicating mechanisms? | Azure Operational Excellence |
| **3. Dependency Lens** | MUST vs SHOULD vs MAY dependencies? | ATAM Sensitivity Analysis |
| **4. Contract Lens** | Are schemas/APIs defined first? | ISO Maintainability |
| **5. Multi-Terminal Lens** | Is this safe for concurrent terminals? | ISO Reliability (Co-existence) |
| **6. Evidence Lens** | What evidence supports this decision? | ATAM Utility Trees |
| **7. Systems Lens** | What are the systemic impacts? | AWS Reliability |
| **8. Distinctiveness & Tradeoff Lens** | Do options differ meaningfully? What tradeoffs exist? | ATAM Tradeoff Analysis |

### Lens 8: Distinctiveness & Tradeoff (Enhanced)

**Merged from Alternative Quality + Tradeoff Clarity**

Every architecture option must:
1. **Differ meaningfully** from other options (no fake alternatives)
2. **Articulate its tradeoffs explicitly**:

**Required for each option:**
```
- **Favored quality/goal**: What this optimizes (e.g., speed of iteration, reliability)
- **Degraded quality/goal**: What this sacrifices (e.g., flexibility, upfront cost)
- **Failure conditions**: Risk level + scenarios where this choice breaks
- **ISO 25010 mapping**: Which qualities this improves vs degrades (analogical, not enterprise)
```

**Example:**
```
Option A: SQLite with WAL mode
- Optimizes: Reliability (crash recovery), Maintainability (single file)
- Sacrifices: Scalability (single-writer), Performance Efficiency (concurrent writes)
- Fails when: >10 concurrent writers, multi-region deployment
- ISO 25010: +Reliability, +Maintainability, -Scalability, -Performance Efficiency
```

---

## Quality Model Mapping

### ISO 25010 Characteristics (Analogical Use)

`/arch` maps reasoning to ISO 25010 characteristics **only insofar as they affect solo-dev Windows workflows**:

| ISO 25010 Characteristic | `/arch` Analogical Focus | NOT Targeting |
|--------------------------|------------------------|---------------|
| **Maintainability** | Can solo dev modify this safely? | Enterprise change management |
| **Reliability** | Does this work across terminal restarts? | High-availability SLAs |
| **Performance Efficiency** | Is this fast enough for local CLI use? | Cloud scale benchmarks |
| **Security** | Multi-terminal state safety, credential handling | Corporate compliance (SOC 2, etc.) |
| **Portability** | Works across Windows dev environments? | Cross-cloud deployment |

### Cloud Framework Pillars (Analogical Lenses)

AWS/Azure Well-Architected Framework pillars are used **purely as analogical lenses**, not infrastructure guidance:

| Cloud Pillar | `/arch` Analogical Meaning | Not Infrastructure |
|--------------|------------------------|-------------------|
| **Operational Excellence** | Local ops ergonomics, CLI workflow smoothness | CloudOps, DevOps pipelines |
| **Security** | Local state safety, credential hygiene | IAM roles, cloud security |
| **Reliability** | Terminal restart safety, graceful degradation | Multi-AZ redundancy |
| **Performance Efficiency** | CLI responsiveness, local resource usage | Auto-scaling, CDN optimization |
| **Cost Optimization** | Time/complexity/cognitive load | Cloud spend management |
| **Sustainability** | Code longevity, reduced churn | Energy efficiency |

**Example**: "This design improves Operational Excellence (local workflow) but degrades Cost Optimization (cognitive load from complexity)."

---

## Compliance Indicator

**MANDATORY**: When you execute, always start your response with:

📍 /arch [STANDARD enforcement]

This provides visible confirmation that the skill is active and its enforcement level.

---

## Constitutional Architecture Principles

**MANDATORY**: All architecture analysis MUST consider these foundational principles (from `CLAUDE.md`):

### Multi-Terminal Isolation & Stale Data Immunity (CONSTITUTIONAL)

**Principle**: Every architectural decision MUST be evaluated for multi-terminal concurrency safety and stale data immunity.

**What this means**:
- **Per-terminal state isolation**: Each Claude Code terminal gets its own state directory (no shared mutable state)
- **Stale data prevention**: State changes must propagate across terminals; no terminal should observe stale data
- **Concurrency safety**: Solutions must handle concurrent access from multiple terminals without data races or corruption
- **Graceful degradation**: If multi-terminal coordination fails, system should degrade safely (not corrupt state)

**When to evaluate**:
- **ALWAYS** - This is not optional. Every architecture recommendation must consider multi-terminal scenarios.
- Even if the immediate use case appears single-terminal, future use may involve multiple terminals.

**How to evaluate**:
1. **Identify shared state**: Does this design create or modify shared mutable state?
2. **Assess isolation**: Can multiple terminals execute this concurrently without interference?
3. **Check propagation**: How do state changes reach other terminals? Is there a risk of stale reads?
4. **Verify safety**: What happens if two terminals write simultaneously? Is there corruption risk?

**Red flags** (architecture that violates this principle):
- Shared mutable files without locking or atomic operations
- In-memory state without proper isolation mechanisms
- Assumptions of single-terminal execution
- File-based state without proper validation
- Global singletons without per-terminal scoping

**Evidence requirements**:
- Document multi-terminal safety in architecture output
- Explain how stale data is prevented
- Cite evidence from codebase analysis (files showing actual behavior)
- If solution is single-terminal only, explicitly document the limitation and migration path

**MANDATORY Edge Case Questioning**:
Every architecture output MUST include an "Edge Case Considerations" section that:
- Internally asks: "Are there other issues, conditions, or edge cases we should consider?"
- Documents the findings in the output (not asked to the user)
- Considers concurrency, failure modes, performance edge cases, and integration risks

**Rationale**: Internal self-reflection produces more comprehensive architecture analysis. The edge case section should demonstrate thorough consideration without requiring user input.

---

### Hook Design Constraints (CONSTITUTIONAL)

**Principle**: Any design that places code inside a Claude Code hook (PreCompact, SessionStart, PreToolUse, PostToolUse, Stop) MUST satisfy:

1. **No external API calls** — Hooks execute during framework events, often blocking the user's workflow. A network dependency means the hook degrades silently whenever the API is unavailable, slow, or rate-limited.
2. **Standalone operation** — Hooks must work with only local files, stdlib, and project-local utilities. No LLM calls, no HTTP calls, no subprocesses that require network access.
3. **Graceful degradation means local fallback only** — "Failing open" (try/except → continue) is valid only if the fallback uses local data of equivalent quality. Falling back from LLM-generated summary to no summary is a data quality regression, not graceful degradation.
4. **Defer to restore-time when possible** — If context can be injected at session restore using already-captured artifacts (e.g., transcript already in handoff envelope, checkpoint files), prefer that over capturing it at hook execution time.

**Red flags** (automatic architectural red flag — require a local-only alternative):
- `llm_client = get_llm_client()` inside any hook file
- `requests.get()`, `httpx.get()`, `urllib.request` inside any hook file
- `subprocess.run(["curl", ...])` or similar network calls inside any hook file
- "Graceful degradation" where the degraded path silently drops the data being captured

**Evaluation trigger**: If ANY option in the architecture alternatives contains a hook + external service call, that combination is a red flag. Evaluate a local-only alternative before recommending the external-service option.

**Why this constraint exists**: Hooks are framework-injected code that run synchronously during user workflows. A hook that calls an external API introduces: (1) network latency added to every hook event, (2) silent quality degradation when the API is down, (3) credential management complexity inside the hook runtime, (4) circular dependency risk (Claude hooks calling Claude API). The `transcript_path` is already captured in the handoff envelope — use it at restore-time rather than summarizing it at capture-time.

---

## Graph-of-Thought (GoT) Integration Features (NEW in v2.5)

/arch now integrates Graph-of-Thought (GoT) reasoning for enhanced architecture alternatives evaluation:

### 1. GoT Architecture Node Extraction

**What**: Automatically extract and categorize architecture nodes from design alternatives
**When**: Automatic enhancement during architecture review (enabled by default)
**Benefit**: Discover hidden relationships and circular dependencies in architecture alternatives

**Node Types Extracted**:
- **Constraints**: Requirements like "Must use JWT tokens", "API response time < 200ms"
- **Ideas**: Implementation approaches like "Use Redis for caching", "Implement OAuth 2.0"
- **Risks**: Potential issues like "Secret key management critical", "OAuth latency concerns"
- **Components**: System boundaries like "Service A", "Database B", "Cache C"
- **Data flows**: Communication paths like "API → Service → Database"

**Opt-out Flag**:
```bash
# Disable GoT enhancement
export ARCH_NO_GOT=true

# Or use --no-got flag in /arch invocation
```

### 2. GoT Edge Relationship Analysis

**What**: Analyze relationships between extracted architecture nodes
**When**: After node extraction, during architecture evaluation
**Benefit**: Detect contradictions, dependencies, and hidden risks

**Edge Types Detected**:
- **Supports**: One idea enables another (e.g., "Redis" supports "Token caching")
- **Contradicts**: One idea conflicts with another (e.g., "JWT" contradicts "Stateful sessions")
- **Unrelated**: No direct relationship
- **Depends**: Component dependencies (e.g., "Service A" depends on "Database B")

**Cycle Detection**:
- Detects circular dependencies (e.g., "A requires B, B requires A")
- Reports architectural deadlock risks
- Helps break circular reasoning patterns

### 3. Integration with Architecture Review Process

GoT enhancement integrates with the existing architecture review workflow:

**During Structured Analysis** (deep template):

1. **Extract nodes** from architecture alternatives
   - Parse proposed design for components and constraints
   - Identify requirements and implementation approaches
   - Extract risk factors and concerns

2. **Analyze edges** between nodes
   - Map component dependencies
   - Identify contradictory requirements
   - Detect circular dependencies

3. **Detect cycles** in the graph
   - Report circular dependencies
   - Identify deadlock risks
   - Recommend cycle-breaking strategies

4. **Document findings** in architecture review
   - Add "GoT Analysis" section to review output
   - List extracted nodes with categories
   - List edge relationships (supports, contradicts, unrelated)
   - Document any cycles found
   - Note architectural insights (e.g., "Constraint X contradicts Idea Y")

**Example Enhanced Architecture Review**:

```markdown
## Architecture Review: Microservices Authentication System

### GoT Analysis

**Extracted Nodes**:
- Constraints: ["Must use JWT", "Response time < 200ms", "Stateless required"]
- Ideas: ["Use Redis for token caching", "Implement OAuth 2.0", "Shared session store"]
- Risks: ["JWT secret management", "OAuth latency", "Cache consistency"]
- Components: ["API Gateway", "Auth Service", "User Service", "Redis Cache"]

**Edge Relationships**:
- "Use Redis" supports "Token caching" ✓
- "Must use JWT" contradicts "Shared session store" ⚠️
- "API Gateway" depends on "Auth Service"
- "Auth Service" depends on "User Service"

**Cycles Detected**: None

**Architectural Insights**:
- Contradiction: JWT (stateless) vs Shared session store (stateful) - resolve by removing session store
- Risk: OAuth latency may violate < 200ms constraint - consider token caching
```

### 4. Multi-Alternative Architecture Comparison

GoT enables systematic comparison of multiple architecture alternatives:

**Alternative A**: Microservices with API Gateway
- Nodes: [API Gateway, Service A, Service B, Load Balancer]
- Edges: [Gateway depends on Service A, Service A depends on Service B]

**Alternative B**: Monolithic with modular design
- Nodes: [Monolith, Module A, Module B, Shared Database]
- Edges: [Module A and B both access Shared Database]

**GoT Analysis**:
- Compare node complexity: Alternative A (5 nodes) vs Alternative B (4 nodes)
- Compare edge density: Alternative A (4 edges) vs Alternative B (3 edges)
- Detect contradictions: Each alternative analyzed for internal consistency
- Risk assessment: Cycle detection reveals hidden dependencies

**Recommendation**: Alternative A has higher complexity but better separation of concerns.

### 5. Integration Notes

- GoT enhancement is **enabled by default** (quality-first design)
- Use `--no-got` flag to disable for simple architecture decisions
- GoT findings complement manual architecture review (edges reveal hidden dependencies)
- For straightforward decisions (< 3 alternatives), GoT may be skipped with explicit note
- Works with all templates: fast, deep, cli, python, data-pipeline, precedent

### 6. GoT Controller Operations

The GoT system orchestrates thought generation and transformation through explicit controller operations:

#### Core Operations

| Operation | Description | When Applied |
|-----------|-------------|--------------|
| **Aggregate** | Combine architecture constraints from multiple sources | Multiple requirements, conflicting inputs |
| **Refine** | Iterate on design alternatives based on scoring | Initial design needs optimization |
| **Generate** | Create new nodes from edge analysis | Complex nodes need decomposition |
| **Split** | Decompose complex nodes into focused sub-architectures | Large components need separation |

#### Scoring Dimensions

Each generated thought is evaluated across three dimensions:

| Dimension | Definition | Evaluation Criteria |
|-----------|------------|---------------------|
| **Relevance** | Alignment with problem constraints | Does it address stated requirements? |
| **Accuracy** | Technical feasibility and correctness | Is it technically sound? |
| **Coherence** | Internal consistency of the architecture | Does it fit with other components? |

#### Controller Workflow

```
Input Query → Extract Nodes → Score → Transform (Aggregate/Refine/Generate/Split) → Re-score → Output
```

**Example**:
- **Input**: "Design async service"
- **Extract**: Nodes = [async framework, database, cache, API]
- **Score**: Relevance=High, Accuracy=Medium, Coherence=High
- **Transform** (Generate): Create node for "error handling strategy"
- **Re-score**: Updated architecture with error handling
- **Output**: Enhanced design recommendation

---

## Lean System Design Integration (NEW in v4.0)

/arch now integrates **Lean System Design** principles to generate lean, high-leverage system designs:

### What This Means

**Core Goals** (defined by your ecosystem):
- Cross-file/codebase-level understanding and validation
- Consolidation and simplification of skills/tools
- Runtime safety and correctness

### How /arch Applies Lean Principles

**1. Value Optimization**
- Every design recommendation explicitly states how it advances core goals
- Components that don't advance these goals are cut or marked "optional"
- Before finalizing: "For each subsystem, how does it advance [cross-file understanding / consolidation / runtime safety]?"

**2. Merge Duplicate Mechanisms**
- Compares new proposals against existing hooks/policies before suggesting them
- If overlap exists: designs merged system, recommends removing weaker one
- No parallel rule systems without strong justification
- Adds "Consolidation & Gaps" section to all designs

**3. Ruthless Dependency Pruning**
- Classifies all dependencies: MUST / SHOULD / MAY
- Designs v1 using only MUST-level dependencies
- SHOULD/MAY moved to "Optional Enhancements" with clear triggers
- Adds "Dependency Audit" section

**4. Contract-First Design**
- Defines schemas/APIs before generating task lists
- Uses concrete field names, types, and realistic examples
- All tasks build on shared contracts (no ad-hoc structures)
- Adds "Core Contracts" section before any implementation plan

**5. Core vs Extended Plan**
- **Core Plan (v1):** 5-10 tasks delivering ~80% value
- **Extended Plan:** Optional ceremony/features (clearly marked)
- Assumes sharp cutover, not multi-phase enterprise rollout

**6. Environment Alignment**
- Respects: Solo dev, Windows 11, Python 3.14, stdlib-only hooks
- Prefers: "One powerful engine + slim adapters" over "many overlapping skills"
- Adds "Environment & Preference Fit" section

### Framework Location

Full Lean System Design framework: `.claude/skills/arch/resources/shared_frameworks.md`

Referenced by all templates during design/planning stages.

### Integration Notes

- Lean principles are **applied automatically** (quality-first design)
- Use `--no-lean` flag to disable for speculative/exploratory architecture
- Lean analysis complements GoT node extraction (value-focused vs relationship-focused)
- For simple decisions (<3 alternatives, <5 components), lean analysis may be abbreviated
- Works with all templates: fast, deep, cli, python, data-pipeline, precedent

---

## Stage 0: Pre-Flight Checks (Out-of-Scope Detection)

Before routing, check if query is out-of-scope for architecture analysis.

### Step 0.1: Quick Preset Expansion (Shorthand Aliases)

**Before any processing**, check if query matches a predefined preset alias and expand it to the full query text.

**Available Presets**:

| Alias | Full Query |
|-------|-----------|
| `multi-term`, `multi-terminal`, `terminal-isolation` | "what's the optimal long term fix in our multi terminal isolation and immune to stale data environment?" |

**Expansion Logic**:
```python
# Quick preset expansion (before all other processing)
QUICK_PRESETS = {
    "multi-term": "what's the optimal long term fix in our multi terminal isolation and immune to stale data environment?",
    "multi-terminal": "what's the optimal long term fix in our multi terminal isolation and immune to stale data environment?",
    "terminal-isolation": "what's the optimal long term fix in our multi terminal isolation and immune to stale data environment?",
}

# Check if query matches a preset
if query.lower().strip() in QUICK_PRESETS:
    query = QUICK_PRESETS[query.lower().strip()]
    # Continue with expanded query through normal routing
```

**Important**: Preset expansion happens BEFORE:
- Out-of-scope checks
- Intent classification
- Domain detection
- Template selection

This ensures aliases work exactly like typing the full query, with no side effects on existing functionality.

---

### Step 0.2: Self-Verification Check (Meta-Pattern)

**Before making architectural suggestions**, verify the gap actually exists.

**Pattern Source**: `packages/reflect-system/skill/scripts/premortem.py:369-443` (Step 3.8 applied to self)

**Why This Matters**:
- "Split into services" → Verify services don't already exist
- "Add abstraction layer" → Verify abstraction isn't already there
- "Extract to utility" → Verify utility doesn't already exist
- "Missing error handling" → Verify error handling is actually missing

**Implementation**:
```python
from skills.shared.self_verification import verify_architectural_suggestion

# Before suggesting architectural change:
result = verify_architectural_suggestion(
    suggestion="Extract to repository layer",
    codebase_context={
        "current_architecture_analyzed": True,  # Did we analyze current code?
        "dependencies_mapped": True,            # Did we check existing patterns?
    }
)

if not result.verified:
    # BLOCK: Gather evidence first
    # Use Glob/Grep to find existing patterns before suggesting
```

**Required Evidence Before Suggesting**:
1. **Current architecture analyzed** - Read relevant files
2. **Dependencies mapped** - Grep for existing patterns
3. **Gap confirmed** - Evidence that X is actually missing

**Meta-Note**: Suggestions about architecture principles themselves (e.g., "should add verification") receive HIGH severity scrutiny.

---

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

**Template chaining (NEW):**
Syntax: `template=X+Y+Z` where:
- **First template (X)** = Primary template (output structure, analysis depth)
- **Additional templates (Y, Z)** = Domain context layering (merged into analysis)

**How it works - Primary Template + Domain Context Layering:**
1. Primary template determines output structure and analysis depth
2. Chained templates provide domain-specific context that's layered into the analysis
3. All chained domains are validated against the allowlist before processing

**Examples:**
```bash
# Primary: deep template, Additional: python + cli domain context
/arch "redesign api" template=deep+python+cli

# Primary: python template, Additional: data-pipeline domain context
/arch "build kafka streaming" template=python+data-pipeline

# Primary: cli template, Additional: precedent domain context
/arch "document terminal behavior" template=cli+precedent
```

**When to use chaining:**
- **Cross-domain concerns**: System involves multiple domains (e.g., Python async + CLI exit codes)
- **Layered requirements**: Need deep analysis but with specific domain patterns
- **Documentation + analysis**: Capture ADR while applying domain-specific context

**Validation rules:**
- All templates must be in VALID_TEMPLATES allowlist
- `precedent` cannot be a chained (secondary) template
- `fast`/`deep` are complexity selectors, not domain templates (can be primary but not chained)
- No limit on number of chained templates (unlike the old 2-template limit)

**Security:**
- Template values validated against allowlist before processing
- Invalid template names in chain are rejected (returns None, falls through to keyword detection)
- Regex restriction: `template=([a-zA-Z0-9-]+(?:\+[a-zA-Z0-9-]+)*)`

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
1 - Run /adf \"[query]\"
    Evaluates WHETHER the change is needed before designing HOW

2 - Continue with /arch \"[query]\" anyway
    Bypasses the justification gate and proceeds directly to architecture design

Response: \"1\" or \"2\"
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
if any review_keyword AND (any design_keyword or "integration" in query):
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
    # Max 2 templates chained. precedent cannot be secondary. fast/deep are complexity selectors.
If single domain match:
    keyword_domain = <matched domain>

# Step 2c: Final domain selection (keywords override config)
if keyword_domain:
    domain = keyword_domain  # Explicit keywords override any config
elif not domain:
    # No config and no keywords - will fall through to complexity detection
    pass
```

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

**Architecture Template Hierarchy (Superset Pattern):**
- **base.md** - Shared stages for all templates (Stage 0-0.7, decision paths)
- **fast.md** - Extends base with fast-specific config (3 files, 1-2 searches, ~5 KB)
- **deep.md** - Extends base with deep-specific additions (5 files, 3-5 searches, GoT/Lean analysis, ~15-30 KB)

| Template | Type | Target Complexity | Output Size | Extends |
|----------|------|-------------------|-------------|---------|
| **base** | Shared | N/A | N/A | None (base template) |
| fast | Extends base | LOW | ~5 KB | base + minimal config |
| deep | Extends base | HIGH | ~15-30 KB | base + GoT + Lean analysis |
| cli | Domain | Any | ~8 KB | base + CLI-specific |
| python | Domain | Any | ~10 KB | base + Python 3.12+ |
| data-pipeline | Domain | Any | ~12 KB | base + ETL/streaming |
| precedent | Domain | Any | ~20 KB | base + ADR format |

**Key design principle:** `deep.md = fast.md + additional depth`. Changes to shared stages (base.md) automatically apply to all extending templates.

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
    if any(p in {"fast", "deep"} for p in parts[1:]):  # fast/deep not chainable
        error_msg = f"Invalid template chain: 'fast' and 'deep' are complexity selectors, not chainable."
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
|-------|--------|------------|-------|------|--------|
| "improve memory system" | Generic | LOW | fast | 5-10 min | ~5 KB |
| "design a CLI tool" | cli | Any | cli | 10-20 min | ~8 KB |
| "python async architecture" | python | Any | python | 15-25 min | ~10 KB |
| "build data pipeline" | data-pipeline | Any | data-pipeline | 20-30 min | ~12 KB |
| "document this decision" | precedent | Any | precedent | 60-90 min | ~20 KB |
| "review integration architecture" | Generic | deep | 20-40 min | ~10-15 KB |
| "template=deep redesign api" | Override | Override | deep | 40-90 min | ~15-30 KB |

---

## Quick Reference Table

### Domain-Specific Templates

| Domain | Template | Trigger Keywords |
|--------|----------|------------------|
| CLI/POSIX | cli | cli, command line, terminal, shell, posix, exit code, argument parsing |
| Python | python | python, asyncio, type hint, pydantic, fastapi, flask, django, async, await, decorator, context manager |
| Data Pipeline | data-pipeline | etl, elt, pipeline, streaming, batch, kafka, spark, airflow, warehouse, data lake |
| ADR | precedent | adr, decision record, precedent, document decision, architecture decision record |

### Complexity-Based Templates

| Template | Complexity | Trigger Keywords |
|----------|------------|------------------|
| fast | LOW | Default for simple decisions |
| deep | HIGH | redesign, overhaul, architecture, microservices, from scratch, rewrite, replace, multi-system, service boundary, schema migration, breaking change |

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

- **Constitutional first:** All architecture decisions MUST evaluate multi-terminal isolation and stale data immunity (no exceptions)
- **Domain-first routing:** Domain-specific expertise beats generic complexity
- **Three intent paths:** ARCHITECTURE_REVIEW, IMPROVE_SYSTEM, and DEFAULT
- **Review-first principle:** Architecture reviews are valid for theoretical designs—never gate behind implementation
- **Evidence-grounded:** WebSearch + WebFetch for current best practices; /context7 for framework-specific patterns
- **Template-based execution:** Read and execute, don't delegate
- **Override support:** Users can force specific templates
- **No skill delegation:** Templates are executed inline, not via Skill() tool
- **CKS + Web:** Internal evidence (CKS.db, 492 entries) combined with external research
- **Edge case awareness:** Every output must explicitly ask about other issues or edge cases

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
    Stage 0.1: Constitutional Compliance Check (MANDATORY)
        ├─ Multi-terminal isolation evaluation (ALWAYS REQUIRED)
        ├─ Identify shared mutable state
        ├─ Assess concurrency safety
        └─ Document edge cases
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
    Output Requirements (MANDATORY):
        ├─ Multi-terminal implications documented
        └─ Edge case considerations explicitly stated (internal self-reflection)
    ↓
    Output Persistence (auto-save to arch_reviews/ or arch_decisions/)
    ↓
Return Output
```

---

## /arch State Machine (Detailed)

The /arch skill implements a finite state machine for processing architecture queries. This section documents all states, transitions, and conditions.

### State Diagram

```
                    ┌─────────────────────────────────────┐
                    │          INPUT STATE                │
                    │  (User query received, raw input)  │
                    └─────────────────┬───────────────────┘
                                      │
                                      ▼
                    ┌─────────────────────────────────────┐
                    │      PREREQ_ANALYZE_STATE           │
                    │  (Check for prerequisite gates)     │
                    └─────────────────┬───────────────────┘
                                      │
                     ┌────────────────┴────────────────┐
                     │                                 │
                     │ Prerequisite detected            │ No prerequisite
                     │                                  │
                     ▼                                  ▼
          ┌──────────────────┐              ┌─────────────────────┐
          │  PREREQ_GATE     │              │ ROUTE_TEMPLATE_STATE│
          │  (Offer /adf or  │              │  (Domain+Complexity │
          │   continue)      │              │   detection)        │
          └──────────────────┘              └──────────┬──────────┘
                                                │
                                                ▼
                                    ┌───────────────────────────────┐
                                    │   CONTEXT_BUILD_STATE          │
                                    │  (Load template, execute       │
                                    │   Stage 0.1-0.8)               │
                                    └───────────────┬───────────────┘
                                                    │
                                                    ▼
                                    ┌───────────────────────────────┐
                                    │   VS_DESIGN_STATE             │
                                    │  (Verbalized Sampling:        │
                                    │   Generate K=3-4 candidates)  │
                                    └───────────────┬───────────────┘
                                                    │
                                                    ▼
                                    ┌───────────────────────────────┐
                                    │   CRITIC_EVAL_STATE           │
                                    │  (Critic: Invariant check,    │
                                    │   risk/complexity scoring)    │
                                    └───────────────┬───────────────┘
                                                    │
                                                    ▼
                                    ┌───────────────────────────────┐
                                    │   CANDIDATE_FILTER_STATE      │
                                    │  (Filter: Lens diversity,     │
                                    │   probability banding)        │
                                    └───────────────┬───────────────┘
                                                    │
                                                    ▼
                                    ┌───────────────────────────────┐
                                    │   DECISION_COMPOSE_STATE      │
                                    │  (Select best candidate,      │
                                    │   apply confidence scoring)   │
                                    └───────────────┬───────────────┘
                                                    │
                                                    ▼
                                    ┌───────────────────────────────┐
                                    │   PERSIST_STATE               │
                                    │  (Save to arch_decisions/,     │
                                    │   log metrics, CKS ingest)    │
                                    └───────────────┬───────────────┘
                                                    │
                                                    ▼
                                    ┌───────────────────────────────┐
                                    │   EXIT_STATE                  │
                                    │  (Return output to user)      │
                                    └───────────────────────────────┘
```

### State Definitions

| State | Description | Entry Conditions | Exit Conditions |
|-------|-------------|-------------------|-----------------|
| **INPUT** | Initial state, raw user query | Skill invocation | Query parsed and normalized |
| **PREREQ_ANALYZE** | Check for prerequisite gates (missing requirements, unknown codebase, etc.) | Input state complete | Either prerequisite detected → PREREQ_GATE, or no prerequisite → ROUTE_TEMPLATE |
| **PREREQ_GATE** | Offer user choice to run suggested skill or continue with /arch | Prerequisite detected | User selects "1" (delegate) or "2" (continue) |
| **ROUTE_TEMPLATE** | Detect domain and complexity, select template | No prerequisite detected | Template selected and validated |
| **CONTEXT_BUILD** | Execute template stages 0.1-0.8 (constitutional check, codebase analysis, web research) | Template loaded | All context gathered, K candidates generated via VS |
| **VS_DESIGN** | Verbalized Sampling: Generate diverse architecture options | Context build complete | K=3-4 candidates with probabilities, lenses, and tradeoffs |
| **CRITIC_EVAL** | Evaluate candidates against invariants, compute risk/complexity | VS design complete | All candidates scored, invariants checked |
| **CANDIDATE_FILTER** | Filter candidates by lens diversity, probability banding | Critic evaluation complete | 1-3 survivors selected for recommendation |
| **DECISION_COMPOSE** | Select best candidate, apply confidence calibration, adversarial self-review | Filter complete | Final output composed with confidence and evidence |
| **PERSIST** | Save decision to disk, log metrics, ingest to CKS | Decision composed | Persistence complete (or skipped) |
| **EXIT** | Return output to user, cleanup | Persistence complete | Skill execution complete |

### Transition Conditions

| From State | To State | Condition |
|------------|----------|-----------|
| INPUT | PREREQ_ANALYZE | Query received and parsed |
| PREREQ_ANALYZE | PREREQ_GATE | Prerequisite pattern detected (missing requirements, unknown codebase, debug focus, etc.) |
| PREREQ_ANALYZE | ROUTE_TEMPLATE | No prerequisite patterns detected |
| PREREQ_GATE | EXIT | User selected "1" to delegate to another skill |
| PREREQ_GATE | ROUTE_TEMPLATE | User selected "2" to continue with /arch |
| ROUTE_TEMPLATE | ROUTE_TEMPLATE | Template override with chaining (e.g., `template=deep+python+cli`) |
| ROUTE_TEMPLATE | CONTEXT_BUILD | Template selected and validated |
| CONTEXT_BUILD | VS_DESIGN | Stage 0.8 (Verbalized Sampling) complete |
| VS_DESIGN | CRITIC_EVAL | K candidates generated with required fields |
| CRITIC_EVAL | CANDIDATE_FILTER | All candidates evaluated |
| CANDIDATE_FILTER | DECISION_COMPOSE | Survivors selected, quality gate passed |
| DECISION_COMPOSE | PERSIST | Final output composed |
| PERSIST | EXIT | Persistence complete or skipped |

### State Machine Invariants

1. **Multi-terminal isolation is ALWAYS evaluated** (Stage 0.1) — even in fast template
2. **VS must generate at least K candidates** before proceeding to CRITIC_EVAL
3. **CRITIC_EVAL must check all invariants** before filtering
4. **PERSIST failures never block EXIT** — persistence is best-effort
5. **PREREQ_GATE is user-cancellable** — user can always choose to continue

### Error Handling

| Error Type | State | Recovery Strategy |
|------------|-------|-------------------|
| Template not found | ROUTE_TEMPLATE | Fall back to fast template, log warning |
| VS generates < K candidates | VS_DESIGN | Log error, fall through with available candidates |
| All candidates rejected by critic | CRITIC_EVAL | Log warning, proceed with least-bad option |
| Persistence failure | PERSIST | Log error, continue to EXIT (non-critical) |
| CKS ingest failure | PERSIST | Log warning, do not block EXIT |

### Metrics Logged Per Decision

Each decision that reaches PERSIST state logs:

**decisions.jsonl:**
- `timestamp`, `id`, `query`, `pattern`, `high_stakes`
- `templates`: primary + chained
- `context`: graph_nodes_considered, precedent_count, cks_used
- `vs`: k_generated, k_survivors, lens_survivors, has_tail_candidate
- `judge`: any_candidate_invariant_violation, recommended_would_violate_without_judge, all_candidates_rejected
- `diversity`: min_structural_distance, mean_structural_distance (optional)
- `persistence`: saved, filepath, cks_ingest_attempted, cks_ingest_ok

**candidates.jsonl (per candidate):**
- `decision_id`, `candidate_id`
- `vs`: probability, lens, changes, is_tail
- `critic`: invariants_ok, violated_invariants, risk_score, complexity_score
- `selection`: survivor, recommended

---

---

## CLI Help

### Output Format Control

**DEFAULT OUTPUT:** ADR format (concise decision document)
- Shows: Context, Decision, Rationale, Alternatives, Consequences
- Hides: Verbose analysis stages (Stage 0.7, 0.8, Candidates, etc.)

**VERBOSE MODE:** Full analysis with intermediate stages
- Use `--verbose` or `-v` flag to show all stages
- Shows: Web research, Verbalized Sampling, Candidates, Decision Path, etc.

### Available Templates

| Template | Use Case | Output Size | Time |
|----------|-----------|-------------|------|
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
| Keywords | Auto-detection | 4 (fallback) |

### Valid Domains

- `cli` - CLI/POSIX architecture
- `python` - Python 3.12+ architecture
- `data-pipeline` - Data systems architecture
- `precedent` - ADR documentation
- `auto` - Keyword-based detection

### Quick Presets (Shorthand Aliases)

Common architecture questions have shorthand aliases to save typing:

```bash
# Multi-terminal isolation and stale data immunity
/arch multi-term
/arch multi-terminal
/arch terminal-isolation

# All three expand to the same full query:
# "what's the optimal long term fix in our multi terminal isolation and immune to stale data environment?"
```

**How presets work**:
- Aliases expand to full queries BEFORE routing
- Works with all templates and domains
- Can combine with template overrides: `/arch multi-term template=deep`

### Usage Examples

```bash
# Default: ADR format (concise)
/arch "how should I fix this PostToolUse verification gap?"

# Verbose mode: Show all analysis stages
/arch "how should I fix this PostToolUse verification gap?" --verbose
/arch "how should I fix this PostToolUse verification gap?" -v

# Force specific template
/arch "redesign api" template=deep
/arch "cli tool" template=cli

# Use project config domain
# (requires .archconfig.json with default_domain set)
/arch "improve error handling"

# Review architecture (new ARCHITECTURE_REVIEW intent)
/arch "review this integration design"
/arch "evaluate proposed architecture"

# Template chaining - Primary + Domain Context Layering
# Deep analysis with Python domain patterns
/arch "design async service" template=deep+python

# Python template with data-pipeline domain context
/arch "build kafka streaming" template=python+data-pipeline

# CLI template with precedent (ADR) documentation
/arch "document terminal behavior" template=cli+precedent

# Cross-domain: Deep analysis with CLI + Python context
/arch "redesign command api" template=deep+python+cli
```

### When to Use Template Chaining

**Cross-domain systems:**
- System involves multiple domains (e.g., Python async + CLI exit codes)
- Need domain-specific patterns from multiple areas

**Layered requirements:**
- Need deep analysis but with specific domain context
- Want comprehensive output with specialized considerations

**Documentation + analysis:**
- Capture ADR while applying domain-specific patterns
- Document decision with technical depth in specific area

**Examples of chaining value:**
```bash
# Microservice with async Python + CLI management interface
/arch "microservice architecture" template=deep+python+cli

# Data pipeline with Python + precedent documentation
/arch "kafka streaming etl" template=python+data-pipeline+precedent

# CLI tool with Python patterns
/arch "build command line tool" template=cli+python
```

### Template Override

```
/arch "<query>" template=<name>
```

Valid template names: `fast`, `deep`, `cli`, `python`, `data-pipeline`, `precedent`

---

## Error Recovery Playbooks

### Case 1: Architecture Rejection

**Symptom:** `/arch` flags solution as "High Risk" or "Violation".
**Recovery:**
1. Document rejected option in analysis notes
2. Consider alternative approaches (different patterns, technologies)
3. Re-run `/arch` on alternative with lessons learned

### Case 2: Evidence Gaps

**Symptom:** Insufficient evidence for confident recommendation.
**Recovery:**
1. Run `/research` for best practices
2. Use `/search` for codebase patterns
3. Re-run `/arch` with evidence gathered

### Case 3: Template Mismatch

**Symptom:** Selected template doesn't fit query complexity.
**Recovery:**
1. Use `template=deep` for complex multi-system decisions
2. Use `template=fast` for quick single-file decisions
3. Use domain-specific templates (cli, python, data-pipeline) for specialized needs

---

## Recent Enhancements

### ADR Documentation Format (v4.1)

---

**Version:** 4.5 | **Architecture:** Template-based router with GoT Controller operations, ADR-first default output, verbose mode flag, one-page ADR template, ARCHITECTURE.md guidance, graph-aware reasoning prompts, ARCHITECTURE_REVIEW intent type, review-first principle, three-path execution (ARCHITECTURE_REVIEW / IMPROVE_SYSTEM / DEFAULT), enhanced Context Contract, Tradeoff Articulation, and Quality Model Mapping
**Enhanced Architecture Decision Records based on industry best practices:**

**New ADR fields:**
- **Decomposed by**: Track when an ADR supersedes/replaces another decision
- **Multi-terminal isolation assessment**: Required per constitutional compliance
- **Alternatives table**: Structured pros/cons/rejection rationale comparison
- **Implementation plan**: Phased rollout with effort estimates
- **Rollback strategy**: How to undo the decision if needed
- **Risk assessment**: Likelihood/impact/mitigation table
- **Evidence sources**: Cite web research, standards, best practices

**Optional ADR output** (all templates):
- Auto-generated when decision meets complexity criteria
- Available via `template=precedent` or template chaining (e.g., `template=deep+precedent`)
- Persists to `P:/.claude/arch_decisions/` with ADR-XXXX naming

**ADR trigger criteria:**
- Decision establishes a pattern for future work
- Choice has significant trade-offs or risks
- Decision contradicts or supersedes prior ADR
- User explicitly requests ADR format

**See:** `precedent.md` for full ADR template, `base.md` Stage 5 for optional ADR output guidance

### GoT Controller Operations (v4.2)

**Explicit Graph-of-Thought controller documentation for enhanced transparency:**

**Core Operations** (Aggregate, Refine, Generate, Split):
- **Aggregate**: Combine architecture constraints from multiple sources
- **Refine**: Iterate on design alternatives based on scoring
- **Generate**: Create new nodes from edge analysis
- **Split**: Decompose complex nodes into focused sub-architectures

**Scoring Dimensions** (Relevance, Accuracy, Coherence):
- **Relevance**: Alignment with problem constraints
- **Accuracy**: Technical feasibility and correctness
- **Coherence**: Internal consistency of the architecture

**Controller Workflow**: `Input Query → Extract Nodes → Score → Transform → Re-score → Output`

**See:** SKILL.md lines 230-260 for full GoT Controller documentation

---

## Lightweight ADR Template (NEW in v4.4)

### One-Page ADR for Solo Dev

For architecturally significant changes, `/arch` recommends a lightweight one-page ADR format:

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
| [ISO 25010 quality] | [Benefit] | [Cost] |

### Multi-Terminal Safety
- [Safe / Single-terminal only / Needs investigation]
- [How concurrent terminals are handled]

### Implementation
- [What changes: files, APIs, structures]
- [Testing approach]
- [Rollback: how to undo]

### Consequences
- **Positive:** [Benefits]
- **Negative:** [Costs/risks with mitigations]
```

**When to create an ADR:**
- Decision establishes a pattern for future work
- Choice has significant trade-offs or risks
- Decision contradicts or supersedes prior ADR
- User explicitly requests ADR format (`/arch "query" template=precedent`)

**Location:** `P:/.claude/arch_decisions/ADR-YYYYMMDD-[slug].md`

---

## ARCHITECTURE.md Guidance (NEW in v4.4)

### Repository-Level Architecture Documentation

For projects that benefit from architecture documentation, `/arch` recommends a simple `ARCHITECTURE.md` at the repository root:

### Content Norms

```markdown
# Architecture

## Components
[Key system components - brief descriptions]

## Invariants
[Core invariants - what must always be true]

## Pointers
- ADRs: `./.claude/arch_decisions/`
- Hooks: `./.claude/hooks/`
- Skills: `./.claude/skills/`
```

### Maintenance Principles

1. **Co-locate docs with code** - ADRs live in repo, not external wiki
2. **Prefer ARCHITECTURE.md over scattered docs** - Single source of truth
3. **Update ARCHITECTURE.md after major changes** - Keep it current
4. **Link to ADRs for context** - Pointers to detailed decisions

### When to Use ARCHITECTURE.md

- **Multi-component systems** - 3+ significant subsystems
- **Evolving architecture** - Active refactoring or growth
- **Onboarding need** - New contributors need architecture overview

### Single Best Practice Recommendation

**"Every major design change gets a one-page ADR"** — Preferred over maintaining a single ARCHITECTURE.md as source of truth.

**Rationale:**
- ADRs capture decisions incrementally (less maintenance burden)
- ADRs provide historical context (why vs what)
- ARCHITECTURE.md can become stale or misleading
- ADRs scale better with project growth

**Hybrid Approach:** Maintain both:
- `ARCHITECTURE.md` = Current state snapshot (components, invariants, pointers)
- `arch_decisions/` = Historical record of why decisions were made

---

## Graph-Aware Reasoning Prompts (NEW in v4.4)

### Internal Graph-Based Thinking

When evaluating architecture, `/arch` applies graph-based reasoning prompts:

#### 1. Node Extraction Prompts

- **What are the components?** (Service boundaries, modules, data stores)
- **What are the constraints?** (Requirements, invariants, non-negotiables)
- **What are the risks?** (Failure modes, security concerns, performance cliffs)

#### 2. Edge Relationship Prompts

- **What depends on what?** (Component dependencies, data flows)
- **What contradicts what?** (Conflicting requirements, technical tensions)
- **What supports what?** (Enabling patterns, infrastructure needs)

#### 3. Cycle Detection Prompts

- **Are there circular dependencies?** (A → B → A deadlock risks)
- **Can components be layered?** (Dependency direction analysis)
- **Where are the coupling points?** (High-fan-in or high-fan-out nodes)

#### 4. Failure Mode Analysis

- **What happens if component X fails?** (Cascading failure paths)
- **What are the single points of failure?** (Critical nodes without redundancy)
- **How does the system degrade?** (Graceful degradation vs catastrophic failure)

### Integration with GoT

These graph-aware prompts are integrated into the existing GoT Controller operations:
- **Extract nodes** → Component/Constraint/Risk extraction
- **Analyze edges** → Dependency/Contradiction/Support analysis
- **Detect cycles** → Circular dependency detection
- **Score alternatives** → Multi-dimensional comparison (Relevance/Accuracy/Coherence)

### Optional Graph.txt Format

For visual learners or documentation purposes, `/arch` can optionally output a simple text-based adjacency list format:

```txt
# Architecture Graph: [System Name]

# Components
[ComponentA]
  depends_on: [ComponentB, ComponentC]
  provides: [ServiceX, ServiceY]
  risks: [SinglePointOfFailure, ScalabilityLimit]

[ComponentB]
  depends_on: [DatabaseD]
  provides: [DataAccess]
  invariants: [AtomicWrites, ReadYourWrites]

# Relationships
ComponentA → ComponentB: synchronous_call
ComponentA → ComponentC: async_event
ComponentB → DatabaseD: tcp_connection

# Contradictions
ConstraintA contradicts IdeaB: [Explanation]

# Cycles Detected
[None] or [Cycle: ComponentA → ComponentB → ComponentA]
```

**When to use graph.txt:**
- Architecture has >5 components with complex dependencies
- Visual documentation needed for onboarding
- Decision involves refactoring with high coupling risk

**Location:** `./ARCHITECTURE.graph.txt` (optional, alongside ARCHITECTURE.md)

---

## Recent Enhancements

### ADR-First Default Output (v4.5)

**ADR format is now the DEFAULT output for all /arch queries:**

**Changes:**
- **DEFAULT OUTPUT: ADR format** (concise decision document)
  - Shows: Context, Decision, Rationale, Alternatives, Tradeoffs, Implementation, Consequences
  - Hides: Verbose analysis stages (Stage 0.7, 0.8, Candidates, Decision Path, etc.)

- **VERBOSE MODE: Full analysis** (with `--verbose` or `-v` flag)
  - Use `--verbose` or `-v` to show all intermediate stages
  - Shows: Web research, Verbalized Sampling, Candidates, Decision Path, etc.

**Rationale:** Users want useful info without being flooded. ADR format provides the decision context clearly without pages of verbose analysis text.

**Usage:**
```bash
# Default: ADR format (concise)
/arch "how should I fix this?"

# Verbose mode: Show all analysis stages
/arch "how should I fix this?" --verbose
```

**See:** `base.md` DEFAULT Decision Path for updated output structure

### ADR Documentation Format (v4.1)

---

**Version:** 4.5 | **Architecture:** Template-based router with GoT Controller operations, ADR-first default output, verbose mode flag, one-page ADR template, ARCHITECTURE.md guidance, graph-aware reasoning prompts, ARCHITECTURE_REVIEW intent type, review-first principle, three-path execution (ARCHITECTURE_REVIEW / IMPROVE_SYSTEM / DEFAULT), enhanced Context Contract, Tradeoff Articulation, and Quality Model Mapping
