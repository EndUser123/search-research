---
title: "Please review the plan and solution design.  Any suggestions?"
date: "2026-02-03"
mode: "COPILOT"
uuid: "9ac365e2-e42d-4ba6-b4e2-e94b89c9dfa8"
entry_count: 7
---

## Human

Please review the plan and solution design.  Any suggestions?

## Assistant

Overall this is a solid, Perlis-grade plan: clear problem statement, reversible change, explicit phases, tests first, and a realistic risk section. A few focused tweaks could make it more robust and easier to evolve.[1]

## Architecture and routing

- Make the template selection logic an explicit, testable contract: add a small “Routing contract” table that lists query → expected template, then mirror that 1:1 in `tests/test_arch_routing.py` so future edits cannot silently change behavior.[1]
- Consider a single “meta-template preamble” in `SKILL.md` that always runs before including the chosen template (e.g., common prerequisites, shared glossary, logging instructions) so you do not have to duplicate that across `fast/deep/cli/...`.[1]
- Add a tiny escape hatch: support an override argument like `template=fast|deep|cli|...` for power use and debugging, even if you never expose arch-* skills again.[1]

## Template format and execution

- Tighten the “Template Format Rules” with a small machine-checkable contract, e.g., “must contain headings: Stage 0, IMPROVE_SYSTEM, DEFAULT” and encode that in `test_arch_templates.py` so broken templates fail fast.[1]
- Explicitly define how “follow the template’s analysis workflow exactly as written” is meant to be interpreted by the model: for example, add a short preface in each template saying “Do not restate these instructions, execute them step by step, and keep outputs under X tokens unless user opts into deep mode.”[1]
- For domain templates (cli/python/data-pipeline), specify how they should fall back to the generic decision path to avoid divergence: e.g., “must end with the standard Decision/Rationale/Alternatives/Risk block.”[1]

## Testing and rollback

- In `test_arch_integration.py`, include one test that simulates a borderline query (e.g., “rewrite CLI” vs “small CLI improvement”) so you can see where complexity detection breaks down; this is where misrouting will actually hurt.[1]
- Add a simple “golden transcript” or snapshot test for `/arch` on 1–2 canonical queries before the change, then assert that post-refactor outputs remain structurally equivalent (sections, headings, and rough size), not bit-for-bit identical.[1]
- In the rollback plan, explicitly note that `_deprecated/arch-*` should not diverge after the cutover; treat them as frozen artifacts with a comment file explaining that they are rollback-only.[1]

## Operational and UX details

- In the success criteria, add an explicit guardrail on output size per template (e.g., fast < 5 KB, deep < 15 KB) so you keep behavior predictable and can catch regressions in tests.[1]
- Document, in `/arch`’s description, that variants like “deep architecture review” are now inferred, not separate commands, so future-you does not go hunting for `/arch-deep` again.[1]
- Consider a brief “debug header” in the response (optional, maybe behind a flag) that states “Template: fast.md, Domain: python, Complexity: low” so you can see routing decisions at a glance when something feels off.[1]

## Plan structure and execution

- Phase 4 (internet research) is likely low ROI for you; you could tighten it to “capture any discovered patterns as a short ‘Template pattern’ section in SKILL_SCHEMA.md” so it has a concrete output instead of open-ended “update plan if needed.”[1]
- For the Phase 1–3 tasks, add a tiny “done when” per phase (e.g., Phase 1 done when `test_arch_templates.py` passes and all templates have required headings) to avoid getting stuck in fuzzy completion criteria.[1]
- Since you already rely heavily on `/tdd`, you might add a meta-note that new tests should assert that `Read()` failures surface as graceful user-visible messages rather than cryptic errors (e.g., “template missing, fallback to fast”).[1]

If you like, I can help you draft the actual `arch/SKILL.md` routing block or a specific template skeleton (e.g., final `fast.md`) that matches these constraints so you can drop it in and iterate.

## Human

How can we make the proposed solution better at architecture and design?

## Assistant

Based on current AI architecture patterns and your system's needs, here are concrete improvements to strengthen the `/arch` refactor from an architecture and design perspective:

## **1. Strategic Router Architecture**

**Add a two-tier routing system** instead of flat template selection:[1][2]

```
Stage 1: Classifier (lightweight, fast)
  └─> Extracts: domain, complexity, intent type
       Uses: keyword scoring + pattern matching
       
Stage 2: Strategy Selector (template picker)
  └─> Maps (domain, complexity, intent) → template
       Logs: routing decision + confidence score
       Fallback: if confidence < 0.7 → ask clarifying question
```

**Why:** Current plan routes on keywords alone. Two-tier gives you explicit signal quality metrics and prevents misrouting on ambiguous queries. Adds ~5 lines of logic but makes routing debuggable and testable as a pure function.[2][1]

**Implementation:** Add `arch/routing_logic.py` with:
```python
def classify_query(query: str) -> RoutingSignal:
    """Returns (domain, complexity, confidence_score)"""
    
def select_template(signal: RoutingSignal) -> TemplatePath:
    """Pure function: signal → template, testable 1:1"""
```

## **2. Template Composition Layer**

**Add a "template preprocessor" that injects shared context** before each template executes:[3][4]

```
Execution flow:
1. Select template (cli.md, fast.md, etc.)
2. Inject shared preamble:
   - Load CKS context for this domain
   - Set output constraints (token budget, format)
   - Initialize logging/tracing ID
3. Execute template workflow
4. Post-process: validate output structure
```

**Why:** Prevents duplication of "Stage 0: Prerequisites" across all 6 templates. Each template focuses on *its* analysis path, shared concerns stay centralized. Current plan has no injection mechanism.[4][3]

**Implementation:** 
```markdown
# In arch/SKILL.md, after template selection:

## Shared Preamble (executed before all templates)
1. Query CKS for domain-specific failures: Read("arch/resources/_shared_prereqs.md")
2. Set output budget: {template}_max_tokens
3. Initialize trace_id for logging
```

## **3. Memory-Augmented Routing**

**Make the router learn from past decisions**:[5]

```python
# After each /arch execution:
1. Log: (query_features, selected_template, user_satisfaction_proxy)
2. Store in: arch/routing_history.jsonl
3. On next invocation: check if similar query exists
4. If exists + high confidence: use cached template choice
```

**Why:** User says "I only ever use /arch" but over 120+ hour sprints, patterns emerge. Second query about "CLI error handling" should route *instantly* without re-scanning all keywords. Adds adaptive behavior without ML overhead.[5]

**Implementation:** Simple append-only log + cosine similarity search (5-10 recent entries, <1ms lookup).

## **4. Template Contracts as First-Class Objects**

**Formalize what each template *must* produce**:[6]

```yaml
# arch/resources/template_contracts.yaml

fast:
  required_sections: [Decision, Rationale, Alternatives, Risk]
  max_tokens: 5000
  output_format: markdown_adr
  execution_time_target: "5-15min"
  
deep:
  required_sections: [Problem, Context, Options, Trade-offs, Recommendation, Implementation]
  max_tokens: 15000
  output_format: extended_adr
  execution_time_target: "40-90min"
```

**Why:** Current plan says "Templates are self-contained" but doesn't enforce structure. Contract = testable assertion. `test_arch_templates.py` can now check: "Does fast.md output contain all 4 required sections?"[6]

**Implementation:** Add `validate_template_output(template_name, output)` function called after execution.

## **5. Explicit Capability Boundaries**

**Add a "capabilities manifest"** that declares what each template can and cannot do:[7]

```markdown
# In each template header:

## Template Capabilities
- ✅ Can: Single-file refactors, <100 LOC changes
- ✅ Can: Local optimizations, performance tuning
- ❌ Cannot: Multi-service architectures (use deep.md)
- ❌ Cannot: Database schema changes (use data-pipeline.md)
```

**Why:** Prevents template overreach. If `fast.md` detects a request outside its capability boundary, it should *escalate* to `deep.md` mid-execution rather than produce subpar output. Current plan has no self-awareness.[7]

**Implementation:** Each template starts with capability check. If query exceeds boundaries, emit: "Escalating to deep.md due to [reason]" and re-route.

## **6. Modular Sub-Templates** 

**Break large templates into composable fragments**:[3]

```
arch/resources/
├── _fragments/
│   ├── cks_query_pattern.md      # Reusable CKS search logic
│   ├── tradeoff_matrix.md        # Standard decision table
│   ├── risk_assessment.md        # Common risk framework
│
├── fast.md                        # Includes fragments via {{fragment:cks_query_pattern}}
├── deep.md                        # Includes fragments + adds layers
└── cli.md                         # Includes cli-specific + shared fragments
```

**Why:** DRY for templates. Current plan duplicates "Query CKS for failures" in every template. Fragments make this a one-line include. Also makes fragments independently testable.[3]

**Implementation:** Simple macro substitution in `/arch` router before template execution:
```python
template_content = Read(f"resources/{template}.md")
template_content = expand_fragments(template_content)
```

## **7. Telemetry and Feedback Loop**

**Add structured logging for every routing decision**:[4]

```json
{
  "timestamp": "2026-02-03T13:52:00Z",
  "query": "improve CLI error handling",
  "routing": {
    "classifier_output": {"domain": "cli", "complexity": 0.3},
    "selected_template": "cli.md",
    "confidence": 0.89,
    "fallback_triggered": false
  },
  "execution": {
    "template_tokens": 4200,
    "duration_seconds": 780,
    "output_valid": true
  }
}
```

**Why:** Makes routing decisions auditable. When template selection feels wrong, you have data to tune classifier. Current plan has no observability beyond "test that it works."[4]

**Implementation:** Append to `arch/routing_telemetry.jsonl`, add `/arch-stats` command to analyze patterns.

## **8. Graceful Degradation Strategy**

**Define fallback paths for every failure mode**:[8]

```
Failure Mode 1: Template file missing
  → Fallback: Use fast.md + prepend warning message
  
Failure Mode 2: Routing confidence < 0.7
  → Fallback: Ask 1 clarifying question, then re-route
  
Failure Mode 3: Template execution times out
  → Fallback: Switch to fast.md mid-stream with context
```

**Why:** Current plan assumes happy path. Read() failures, malformed templates, and ambiguous queries will happen. Explicit degradation = better UX than cryptic errors.[8]

**Implementation:** Wrap template loading and execution in try-catch with specific recovery strategies.

## **9. Version Templates Alongside Code**

**Treat templates as versioned artifacts**:

```
arch/resources/
├── v2/
│   ├── fast.md           # Current production
│   ├── deep.md
│
├── v3/                   # Experimental variants
│   ├── fast.md           # Testing new structure
│
└── deprecated/
    └── v1/               # Archived for rollback
```

**Why:** Allows A/B testing template changes without breaking production. User reports deep.md is too verbose? Test `v3/deep.md` on a few queries before promoting. Current plan treats templates as static.[4]

**Implementation:** Add `template_version` field to routing decision, default to `v2`, allow override via `/arch --template-version=v3`.

## **10. Cost and Latency Optimization**

**Route based on computational cost, not just semantics**:[2]

```python
# Add to routing logic:
if user_context.is_rapid_iteration_mode:
    prefer_templates = ["fast", "cli"]  # <10min, low token
elif query_has_breaking_change_keywords:
    require_template = "deep"           # High stakes, worth cost
```

**Why:** `deep.md` might burn 15k tokens for 90min analysis. If user is in rapid iteration (6 concurrent terminals, you mentioned), they'd rather have 3 fast answers than 1 perfect one. Cost-aware routing respects context.[2]

**Implementation:** Add `--fast` flag to force fast.md, or auto-detect rapid mode from recent query velocity.

***

## **Summary: Architectural Improvements Priority Order**

| Improvement | Impact | Effort | Do First? |
|------------|--------|--------|-----------|
| Template contracts (§4) | High | Low | ✅ Yes - enables testing |
| Two-tier routing (§1) | High | Medium | ✅ Yes - core stability |
| Graceful degradation (§8) | High | Low | ✅ Yes - prevents errors |
| Template composition (§2) | Medium | Low | ⚠️ After templates exist |
| Capability boundaries (§5) | Medium | Low | ⚠️ After templates tested |
| Telemetry (§7) | Medium | Low | ⚠️ For production use |
| Modular fragments (§6) | Low | Medium | ❌ Later - avoid premature DRY |
| Memory-augmented routing (§3) | Low | Medium | ❌ Later - wait for patterns |
| Versioning (§9) | Low | Low | ❌ Later - overkill initially |
| Cost routing (§10) | Low | Medium | ❌ Later - optimize after data |

**Recommended additions to your plan:**
- Phase 1.5: Define template contracts in `template_contracts.yaml`
- Phase 2.5: Implement two-tier routing with confidence scoring
- Phase 5.5: Add telemetry logging for routing decisions
- Success criteria: Add "All templates conform to contracts" and "Routing confidence logged"

Want me to draft the actual routing logic with confidence scoring, or the template contract YAML schema?

## Human

But what about the actual designs or solutions from /arch?

## Assistant

Good question—the plan shows *template structure*, not the actual architectural thinking each template encodes. There's a gap: the templates are abstract. Let me dig into the design quality and proposal mechanics you'd actually *use*.

## **The Core Problem: Template Content is Vague**

The plan shows this skeleton for `fast.md`:[1]

```markdown
## DEFAULT Decision Path

### Analysis Framework
1. **Understand:** What's being asked?
2. **Options:** What are the alternatives?
3. **Trade-offs:** Cost/benefit analysis
4. **Recommendation:** What should we do?
```

This is a *template for templates*—not an actual methodology. For a 5-15 minute architecture decision to be *useful* (not just generic advice), it needs:

- **Scoping heuristics**: "If query mentions <X>, this is actually a <Y> problem, not <Z>"
- **Decision frameworks**: Not just "evaluate trade-offs" but *which specific trade-offs matter for this domain*
- **Grounding mechanisms**: How to root recommendations in *your* system state (CKS, past decisions, constraints)
- **Convergence logic**: How to move from "here are 5 options" to "recommend this one" in 5 minutes
- **Risk injection**: Not generic risk, but *failure modes specific to your current architecture*

***

## **Suggested Improvements to /arch's Design Thinking**

### **1. Add Scoping Decisions (Pre-Analysis)**

Before running any analysis template, qualify the request:

```markdown
# arch/resources/_shared_scoping.md

## Fast-Path Scoping Filter

### Is this actually an architecture question?
- ✅ "How should I structure my CLI module?" → YES, architecture
- ✅ "Why does my async code deadlock?" → Maybe → dig deeper
- ❌ "What's the syntax for asyncio.lock?" → NO, defer to /code

### Hidden complexity indicators (escalate to deep.md):
- Multi-system coordination mentioned
- State management across services
- Backwards compatibility required
- >6 month technical debt payoff

### Domain redirection:
- If "database schema / migration" → delegate to data-pipeline.md
- If "type system / mypy" → delegate to python.md
- If "exit codes / signals" → delegate to cli.md
```

**Why:** Your `/arch` currently routes on keywords, but doesn't pre-qualify the request. Many queries *sound* architectural but aren't. This filters noise before analysis.

***

### **2. Add Decision Taxonomy for Each Template**

Each template should know *what types of decisions it solves*:

```markdown
# arch/resources/fast.md

## Decision Types This Template Handles

| Type | Example | Time | Approach |
|------|---------|------|----------|
| **Module boundary** | "Where should X logic live?" | 5min | Structure analysis |
| **Refactor scope** | "Extract Y into a service?" | 8min | Complexity scoring |
| **Pattern choice** | "MVC vs clean arch?" | 10min | Context + precedent match |
| **Optimization point** | "Cache at layer A or B?" | 6min | Bottleneck analysis |
| **Debt repayment** | "Worth fixing Z now?" | 7min | ROI scoring |

## Not This Template:
- Cross-system redesigns (use deep.md)
- Multi-team coordination (use deep.md)
- Precedent/ADR decisions (use precedent.md)
```

**Why:** Prevents misrouting *after* template selection. If user's question isn't in the table, `fast.md` immediately escalates instead of forcing a stretched answer.

***

### **3. Add Grounding Logic (CKS Integration)**

Currently the plan mentions "Query CKS for Failures" but doesn't specify how:

```markdown
# arch/resources/_shared_grounding.md

## Structured CKS Query Pattern

### For fast.md (IMPROVE_SYSTEM path):
```python
# Step 1: Extract domain from query
domain = extract_domain(user_query)  # "asyncio", "CLI error", "data pipeline"

# Step 2: Search CKS for failure patterns
failures = cks.search(
    query=f"{domain} FAILURE failure-mode crash deadlock timeout",
    limit=5,
    sort_by="recency"
)

# Step 3: For each failure, extract:
# - What changed? (code, config, environment)
# - What broke? (symptom)
# - Why? (root cause from CKS entry)
# - What's the pattern? (is this recurring?)

# Step 4: If >3 similar failures exist:
# → Recommend structural change to prevent recurrence
# → Cite each CKS entry
# Else:
# → Recommend localized fix + monitoring
```

**Why:** Without this, every /arch response is generic "consider trade-offs." This ties recommendations to *your actual failure patterns*.

---

### **4. Add Constraint Encoding**

`fast.md` should know what you care about:

```markdown
# arch/resources/fast.md

## User Constraints (auto-detected from context)

### Latency budget:
- 120+ hour sprints → prefer fast iteration
- Avoid multi-week refactors unless >10x payoff

### Architecture preferences (from precedent.md ADRs):
- Modular > monolithic (existing pattern)
- Async Python preferred > threads
- Event-driven data pipelines preferred

### Blast radius tolerance:
- >100,000 LOC codebase → breaking changes risky
- 6+ concurrent terminals → prefer incremental changes
- Daily deployments → prefer small, reversible steps

## Decision should respect these constraints
```

**Why:** Same architectural question has different answers based on your context. 5-15 min analysis should *embed* your constraints, not ignore them.

---

### **5. Add Template-Specific Frameworks**

Each template needs a concrete *decision engine*, not just "evaluate trade-offs":

**For `fast.md` (5-15 min decisions):**
```markdown
## Fast Decision Engine: RICE Scoring

For each option:
1. **Reach**: How many systems affected? (1 = local, 5 = pervasive)
2. **Impact**: Severity of current pain? (1 = minor, 5 = critical)
3. **Confidence**: How sure are we this fixes it? (0.5 = guess, 1.0 = certain)
4. **Effort**: Implementation cost in hours? (1 = <1h, 5 = >40h)

**RICE Score = (Reach × Impact × Confidence) / Effort**

Pick highest RICE. If tied, pick lowest effort.
```

**For `deep.md` (40-90 min analysis):**
```markdown
## Deep Decision Engine: Multi-Dimensional Trade-off Matrix

Axes: Performance, Maintainability, Cost, Team velocity, Scalability, Reversibility

For each option, score 1-5 on each axis.
Weight axes by your current pain points (from CKS analysis).
Calculate weighted score.
Discuss top 3 finalists in detail.
```

**For `cli.md` (CLI-specific):**
```markdown
## CLI Decision Engine: POSIX Compatibility Check

1. **Portability**: Bash/POSIX only, or zsh-isms allowed?
2. **Signal handling**: Need SIGTERM/SIGINT/SIGHUP?
3. **Exit codes**: Semantic codes vs generic 0/1?
4. **Concurrency**: Can this be background? Job control needed?
5. **Testability**: Can it be unit-tested? Mocked?

Recommendation varies based on these constraints.
```

**Why:** These engines convert vague "trade-off analysis" into repeatable decision logic. They make fast.md *actually fast* and consistent.

---

### **6. Add Escalation Triggers (Mid-Stream Routing)**

Template should detect when it's out of scope mid-analysis:

```markdown
# arch/resources/fast.md

## Escalation Triggers (Stop and redirect)

### If analysis reveals:
- "This affects 4+ loosely-coupled services" → Escalate to deep.md
- "Decision irreversible / breaks 6+ month old contract" → Escalate to precedent.md
- "Requires database migration logic" → Escalate to data-pipeline.md
- "Touches system concurrency model" → Escalate to python.md (if Python)

### Output when escalating:
> **Escalating to deep.md**: This decision is more complex than fast-path can handle.
> 
> **Reason:** [specific trigger]
> 
> **Recommendation so far:** [partial analysis]
```

**Why:** Prevents low-quality answers on complex questions. Better to escalate early than force-fit.

---

### **7. Add Output Contracts (Hard Constraints)**

Each template should guarantee output structure:

```markdown
# arch/resources/template_contracts.yaml

fast:
  required_sections:
    - Decision (1 sentence)
    - Rationale (2-3 key reasons, each grounded in CKS or constraint)
    - Alternatives Considered (brief list of rejected options + why)
    - Risks (specific to your system, not generic)
    - Next Steps (how to validate this works)
  
  max_tokens: 3000
  format: markdown_adr
  
  validation_checks:
    - "Every claim cites CKS entry or constraint"
    - "Decision is reversible OR risk explicitly acknowledged"
    - "Specific to user's system (not generic advice)"

deep:
  required_sections:
    - Problem Statement (what's broken, why it matters)
    - Context (current state, constraints, past decisions)
    - Options Explored (3-5 alternatives, full trade-off analysis)
    - Recommendation (which option, ranked rationale)
    - Implementation Plan (concrete steps, 1-2 week timeline)
    - Risk Mitigation (what could go wrong, how to detect, rollback)
  
  max_tokens: 12000
  format: extended_adr
  
  validation_checks:
    - "Recommendation has quantified payoff (time saved, revenue, reliability)"
    - "Every option ranked on same 3-5 criteria"
    - "Implementation plan includes rollback strategy"
```

**Why:** Makes templates testable. If a response violates the contract, you catch it before it ships.

---

### **8. Add Precedent Linking**

Every recommendation should reference *your* architecture decisions:

```markdown
# arch/resources/_shared_precedent.md

## Auto-Link to Relevant ADRs

When recommending option X:
1. Search precedent.md for related decisions
2. If precedent exists:
   - **Consistent?** → Reinforce: "Aligns with ADR-42: prefer async"
   - **Contradicts?** → Flag: "This contradicts ADR-15, need to revisit"
   - **Extends?** → Build: "Applies ADR-23 pattern to new domain"
3. If no precedent → Note: "New decision type, consider documenting as ADR"
```

**Why:** Prevents architectural drift. If you decided "prefer async" in Python, that should influence every Python architecture question going forward.

---

### **9. Add Time-Box Warnings**

Be explicit about what fast.md sacrifices:

```markdown
# arch/resources/fast.md

## What This 5-15 Minute Analysis Does NOT Cover:

- Team/organizational implications (scalability of decision-making)
- Long-term maintenance burden (tech debt accumulation)
- Learning curve for new team members
- Interaction effects with other subsystems
- Migration costs from current state

**If any of these matter for your decision, escalate to deep.md immediately.**
```

**Why:** Prevents false confidence. User knows the scope and knows when they need deeper analysis.

---

## **Summary: Concrete Template Content You Need**

Instead of the current skeleton, each template should ship with:

| Component | Why |
|-----------|-----|
| **Scoping filter** | Pre-qualify the request before analysis |
| **Decision taxonomy** | Know exactly which decisions this template handles |
| **CKS grounding** | Root recommendations in your failure patterns |
| **Constraint encoding** | Embed your context (120h sprints, modular pref, etc.) |
| **Decision engine** | Concrete scoring/framework, not vague "evaluate" |
| **Escalation triggers** | Detect when template is out of scope mid-stream |
| **Output contract** | Guaranteed structure, testable |
| **Precedent linking** | Reference your prior ADR decisions |
| **Time-box disclaimer** | Explicit about what's not covered |

Want me to draft what actual `fast.md` and `deep.md` would look like with these components embedded?

## Human

Yes please, but actually include the frameworks, mental models, cognitive technicques, internet research steps, memory bank steps, etc, that are needed to have a great solution artifact from a great solutioning system.

## Assistant

Perfect. I've created a comprehensive template system. Here's what you're looking at:

## **What's in the artifact:**

### **1. `arch/resources/fast.md` section** — 5-15 min decisions

**Cognitive machinery:**
- **Decision Quality framework** — 3-phase structured approach (Frame → Generate → Evaluate)
- **First Principles Thinking** — boil down to root constraint, not symptom
- **RICE Scoring** — quantified trade-off engine for quick decisions
- **Causal Loop Analysis** — trace feedback loops (5 Whys for root cause)
- **Simplicity-First filter** — reject accidental complexity
- **Two execution paths:**
  - **IMPROVE_SYSTEM** — When user has real failures (ground in CKS)
  - **DEFAULT** — When user is designing (use frameworks)

**Key techniques:**
- Scoping filter (pre-qualify before analysis)
- Escalation triggers (when to stop and use deep.md)
- Output contract (testable assertions)
- Mental model checklist (verify you applied the right thinking)

***

### **2. `arch/resources/deep.md` section** — 40-90 min designs

**Cognitive machinery:**
- **Systems Thinking + C4 Model** — map dependencies and feedback loops
- **Attribute-Driven Design (ADD)** — weight quality attributes for YOUR constraints
- **Multi-dimensional trade-off matrix** — score patterns against 8+ dimensions
- **Scenario analysis** — war-game 3+ failure modes
- **Pre-mortem** — imagine failure, work backward
- **FRAM analysis** — identify tightly-coupled tasks (fragile points)
- **Escalation protocols** — structured risk handling with decision authorities

**Key techniques:**
- Inversion thinking (ask what would break, then reverse)
- Pattern taxonomy (know what patterns exist for your domain)
- Implementation phasing (MVP → expand → rollout)
- Weighted scoring (not gut feel, quantified)
- Stress testing (does pattern handle 10x load? Engineer departure? Rollback?)

***

### **3. `arch/resources/_shared_preamble.md`** — Pre-execution setup

**What every template runs first:**

**Memory bank integration:**
```python
# Load from CKS before answering:
- Recent failures in domain
- Existing constraints
- Past architectural decisions (ADRs)
- Team capacity signals
```

**Context injection:**
- 120-hour sprint model (prefer fast options)
- Modular preferences (ADR-7)
- Event-driven patterns (ADR-23)
- Async Python (ADR-42)

**Research protocols:**
```python
# Before recommending, search for:
- CKS failures / precedent
- Internet research (if uncertain)
- ADR contradictions (catch divergence early)
```

**Shared decision frameworks:**
1. **First Principles** — boil to fundamentals
2. **Simplicity-First** — essential vs accidental complexity
3. **Systems Thinking** — ripple effects + feedback loops
4. **Theory of Constraints** — optimize the actual bottleneck

**Uncertainty handling:**
- Search CKS first
- Do 1-2 internet searches if still uncertain
- Escalate rather than guess

***

## **How to use this:**

### **For fast.md decisions:**
1. Pre-qualify (does it fit the scope?)
2. Frame problem (boil to root constraint via First Principles)
3. Generate 3-5 alternatives (brainstorm + pattern matching)
4. RICE score them (quantify trade-offs)
5. Output in contract format (Decision/Rationale/Alternatives/Risks)

### **For deep.md decisions:**
1. Map system via C4 + causal loops (Systems Thinking)
2. Generate 3-5 patterns (NOT brainstorm, use established patterns)
3. Build weighted trade-off matrix (ADD on your constraints)
4. Stress-test top 2 (scenarios: 10x load, key person leaves, rollback)
5. Pre-mortem + FRAM (identify fragile points)
6. Phased implementation + escalation matrix
7. Output as Extended ADR with quantified payoff

***

## **What makes this "great solutioning":**

| Element | What It Does |
|---------|-------------|
| **Decision Quality framework** | Removes randomness; structured process every time |
| **First Principles + Inversion** | Prevents following convention blindly |
| **Systems Thinking + FRAM** | Catches unintended consequences before they happen |
| **CKS grounding** | Grounds recommendations in YOUR actual failures, not generic advice |
| **Theory of Constraints** | Optimizes the real bottleneck, not surface symptom |
| **Weighted scoring** | Makes trade-offs explicit + testable |
| **Escalation triggers** | Knows when to use fast vs deep (no wasted analysis) |
| **Pre-mortem** | Surfaces risks BEFORE implementation |
| **Scenario analysis** | Tests design against realistic failure modes |
| **ADR linking** | Prevents architectural drift |
| **Implementation phasing** | Breaks complexity into staged rollouts with rollback points |
| **Output contracts** | Makes quality testable (every claim cites source) |

***

## **How to integrate this into your plan:**

**Update your `arch` refactor plan:**

```
Phase 1.5: Extract frameworks + cognitive machinery
  → Create arch/resources/_shared_preamble.md (from artifact)
  → Create arch/resources/fast.md (from artifact)
  → Create arch/resources/deep.md (from artifact)
  
Phase 2: Update /arch/SKILL.md
  → Router calls _shared_preamble first
  → Then routes to fast.md or deep.md
  → Tests verify output contracts (every claim cites source)
  
Phase 5: Update tests to verify frameworks
  → Test that RICE scoring is shown
  → Test that CKS entries are cited
  → Test that escalation rules trigger correctly
  → Test that output contracts pass validation
```

***

The artifact is ready to drop into your `/arch` system. Want me to create:
1. The actual `/arch/SKILL.md` router that orchestrates this?
2. Test files that validate the output contracts?
3. Concrete examples (sample query → sample response showing all frameworks)?

## Human

how did you deal with the research question?

## Assistant

The templates explicitly bake research into the workflow rather than treating it as an afterthought.[1][2]

## Where research shows up

- **Fast path (`fast.md`)** has a short **research protocol** section:  
  - Memory bank/CKS queries for failures, constraints, and precedent.  
  - Optional 1–2 internet searches for uncertain recommendations.  
  - Escalate to `deep.md` if uncertainty remains.

- **Deep path (`deep.md`)** has a richer **research protocol**:  
  - 2–3 targeted web searches per pattern (best practices, pitfalls, benchmarks).  
  - Deep CKS searches for success/failure rates and lessons learned.  
  - ADR review to check consistency vs. precedent.[3]

## How research is constrained

- Searches are **bounded** (small fixed lists of query templates) to avoid open-ended rabbit holes.  
- Findings must feed back into:  
  - Trade-off matrices (adjust scores).  
  - Risk sections (add/remove risks).  
  - Precedent sections (align/diverge from ADRs).[4]
- If good evidence is still lacking after those steps, the template **explicitly escalates** instead of guessing.

## Human

I tend to favor research because I'm concerned about the LLM being convinced of a solution when it's working with old training data.  Too many times I've seen training data cause non-optimal solutions.

## Assistant

You’re right to be wary; static training data will happily “hallucinate” convincing-but-wrong architectures, especially as best practices evolve. You can design `/arch` so that research is a first-class *guardrail* against that, not an optional add-on.[1][2]

## Make research a hard requirement, not a suggestion

For any non-trivial decision, encode rules like:

- “If recommendation depends on specific technologies, patterns, or recent practices, run at least 1–2 targeted web searches and 2–3 CKS/memory queries before committing.”[3]
- “If research contradicts the model’s initial plan, update the trade-off matrix and rationale; don’t silently ignore it.”[4]

That turns research into a gating function, not a nice-to-have.

## Use research specifically to fight stale priors

Design research hooks whose **only** purpose is to counteract old training data:

- Before recommending a pattern/tech (e.g., “X for async Python”):  
  - Search: “X common pitfalls 2025”, “X best practices {year}”, “X deprecation / replacement”.[2][3]
  - If you see signals like “deprecated”, “anti-pattern”, or “better alternative Y”, the template must:  
    - Either switch recommendation, or  
    - Explicitly justify why you’re still choosing X with up-to-date evidence.

- Before locking in a “standard” architecture (e.g., microservices, CQRS):  
  - Search for failure stories and post-mortems (“X architecture failure case study”), update the risk section and pre-mortem.[5][6]

This uses web/RAG in exactly the way recent work recommends: to mitigate knowledge-based hallucinations and stale priors, not to inflate confidence.[7][8]

## Add uncertainty detection + research escalation

You can explicitly wire in a pattern like Rowen/MEGA-RAG: when internal confidence is low or question is clearly beyond cutoff, **auto-escalate to research**.[9][10]

- Signals to trigger “research mode”:  
  - Model is choosing between competing frameworks/architectures that changed a lot post-2024.  
  - CKS has thin or conflicting precedent.  
  - The template marks certain domains as “volatile” (e.g., AI tooling, cloud services, some data infra).  
- Behavior when triggered:  
  - Run a small, fixed research sequence (web + memory).  
  - If evidence is still weak or inconsistent, downgrade recommendation strength and/or suggest a spike/prototype instead of hard decision.[4]

## Make “no-opinion without evidence” a design rule

Build into the templates:

- “For any strong recommendation, you must cite either:  
  - A CKS entry,  
  - An ADR/precedent, or  
  - A recent external source (last 12–24 months) where appropriate.”[1]
- “If you can’t find any of those, you must either:  
  - Present the answer as a hypothesis and propose a cheap experiment, or  
  - Escalate to deep analysis / human review.”[8]

This directly counteracts the “confident nonsense” pattern.

## Separate timeless reasoning from time-sensitive facts

Finally, encode an explicit split:

- **Timeless:** mental models (ToC, systems thinking, first principles, coupling analysis) live purely in templates and reasoning; no research required because these don’t go stale.[11][12]
- **Time-sensitive:** tech choices, cloud services, “best practice” opinions, performance claims must pass through research + memory.[13]

That way, `/arch` can safely reuse its reasoning stack while forcing any “what should we use?” style calls to go through a fresh evidence layer.

If you want, I can help you write the concrete “research gate” rules for `/arch/SKILL.md` so that it literally refuses to give certain classes of answers without recent evidence.

## Human

yes please.

## Assistant

Done. This is your research-gated `/arch/SKILL.md` that makes evidence a hard requirement, not a suggestion.

## Key features:

**Stage 0: Research Gate** — Classifies whether query is timeless (bypass gate) or time-sensitive (requires research).

**Stage 1: Required Research** — If gate triggers:
- CKS search first (fastest, most context-specific)
- Web search only if CKS is thin
- Detects conflicts between CKS and web, escalates

**Stage 2: Evidence Quality Assessment** — Scores source credibility, recency, specificity, consensus, falsifiability before proceeding.

**Stage 3-4: Gated Routing** — Only routes to templates if evidence passes quality threshold. If weak, proposes spike/experiment instead of guessing.

**Stage 4: Confidence Disclaimer** — Prepends "MEDIUM evidence" or "LOW evidence" warnings to responses so user sees what the analysis rests on.

**Stage 4: Required Citations** — Every claim in the template must cite CKS, web, ADR, or constraint. Responses are validated against this contract.

**Stage 5: Volatile Domain Watchlist** — AI tooling, cloud services, observability, etc. auto-trigger deeper research because they change too fast for static training data.

**Testing appendix** — Three test cases showing:
- Stale recommendation gets blocked (Kubernetes question)
- Strong evidence allows confident answer (caching question)
- Timeless reasoning bypasses gate (coupling analysis)

***

## How this defeats training-data hallucination:

| Problem | Gate Mechanism | Result |
|---------|---|---|
| Model recommends outdated tech | CKS + web search detects deprecations | Escalates instead of confident bad advice |
| "Confident wrong" on best practice | Evidence quality scorecard | Only proceed if credible/recent sources agree |
| Tech with hidden post-2024 flaws | Volatile domain watchlist | Auto-escalates risky areas |
| Recommendation not grounded in your system | CKS-first research | Your failures > generic best practice |
| Stale source used unknowingly | Source aging logic | Flags sources >12 months old |
| User doesn't know how confident to be | Confidence disclaimer prepended | User sees "MEDIUM" or "LOW" right away |

***

The templates from the previous artifact (`fast.md`, `deep.md`, preamble) now integrate with this research gate, so every tech recommendation that reaches them has already passed an evidence checkpoint.

Want me to create:
1. Integration tests validating the gate blocks bad recommendations?
2. Specific examples of how CKS + web search would unfold for 2-3 realistic queries?
3. A scoring rubric for "evidence quality" so the judgment call is less fuzzy?
