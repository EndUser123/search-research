# Graph-of-Thought (GoT) and Tree-of-Thought (ToT) Integration

## Graph-of-Thought (GoT) Integration (v2.2)

/r integrates GoT reasoning for enhanced memory refinement analysis.

### GoT Memory Node Extraction

**What**: Automatically extract and categorize memory nodes from forgotten items and deterministic improvements
**When**: Automatic enhancement during memory refinement analysis (enabled by default)
**Benefit**: Discover hidden relationships between forgotten items and improvement suggestions

**Node Types Extracted**:
- **Forgotten Items**: Omissions detected (e.g., "Missing error handling", "No tests for edge case")
- **Constraints**: Requirement limitations (e.g., "Must handle timeouts", "Budget constraint")
- **Ideas**: Improvement suggestions (e.g., "Extract method", "Add caching layer")
- **Risks**: Potential issues (e.g., "Missing validation could crash", "Race condition risk")
- **Improvements**: Deterministic refinements (e.g., "Refactor function", "Add type hints")
- **Context Items**: Related context for downstream skills

**Relationship Types Detected**:
- **Supports**: One improvement enables another (e.g., "Add caching" supports "Performance fix")
- **Contradicts**: One improvement conflicts with another (e.g., "Simplify" vs "Add feature")
- **Depends**: One improvement requires another (e.g., "Extract class" depends on "Identify boundary")
- **Unrelated**: No direct relationship between improvements

**Opt-out Flag**:
```bash
# Disable GoT enhancement
export R_NO_GOT=true
```

### GoT Finding Categorization Analysis

**Integration Point**: Memory refinement and deterministic improvement analysis

**Workflow**:
```
/r deterministic pass
  |
Collect findings (forgotten_items, deterministic_improvements, solo_dev_violations)
  |
GotPlanner extracts finding nodes
  |
GotEdgeAnalyzer detects relationships between findings
  |
Cycle detection warns about circular improvement dependencies
  |
Enhanced categorization into must_fix_now vs can_do_soon
```

**Example Output**:
```
GoT Analysis: Memory Refinement
=================================

Nodes extracted: 12
  - Forgotten items: 4 (Missing error handling, No tests, etc.)
  - Constraints: 2 (Budget limit, Timeline constraint)
  - Ideas: 3 (Extract method, Add caching, Refactor function)
  - Risks: 2 (Race condition, Missing validation)
  - Improvements: 1 (Add type hints)

Relationships detected: 7
  - Supports: 4 pairs (Add caching -> Performance fix, etc.)
  - Contradicts: 1 pair (Simplify vs Add feature - CONFLICT)
  - Depends: 2 pairs (Extract class depends on Identify boundary)

Cycles detected: 0

Categorization:
  - must_fix_now: 3 items (Missing validation, Race condition, Missing error handling)
  - can_do_soon: 6 items (Extract method, Add caching, Refactor function, etc.)
  - deferred: 3 items (low priority, blocked by other items)
```

**What This Catches**:
- Hidden dependencies between forgotten items
- Conflicting improvement suggestions
- Circular dependency risks in improvement execution
- Optimal sequencing of improvements (do X before Y)

---

## Tree-of-Thought (ToT) Integration (v2.2)

/r integrates ToT reasoning for enhanced reflection path analysis.

### ToT Reflection Path Branching

**What**: Automatically generate branching scenarios for reflection decisions
**When**: Automatic enhancement during reflection path analysis (enabled by default)
**Benefit**: Discover alternative reflection strategies beyond linear remember/refine

**Reflection Branch Types**:

**Memory Branching**:
- **sure**: Remember context for future sessions (standard case)
- **maybe**: Partial memory (key findings only) - large session, low signal
- **unlikely**: Skip memory (noise only, no value) - trivial session

**Refinement Branching**:
- **sure**: Propose improvements (standard deterministic pass)
- **maybe**: Minimal refinement (only critical issues, skip optimizations)
- **unlikely**: No refinement (code is sound, focus on omissions only)

**Escalation Branching**:
- **sure**: Handle locally (within /r skill scope)
- **maybe**: Escalate to /s (conflicting options, strategic decision needed)
- **unlikely**: Defer to later (not urgent, can wait)

**Scope Classification Branching**:
- **sure**: Trivial scope (1-2 files, clear changes)
- **maybe**: Moderate scope (3-10 files, some complexity)
- **unlikely**: Significant/Major scope (10+ files, high complexity)

**Value Completeness Branching**:
- **sure**: HIGH value (always disclose, user-facing impact)
- **maybe**: MEDIUM value (disclose when 3+ items grouped)
- **unlikely**: LOW value (optional disclosure, internal optimization)

**Opt-out Flag**:
```bash
# Disable ToT enhancement
export R_NO_TOT=true
```

### ToT Decision Flow Analysis

**Integration Point**: Mode decision and escalation analysis

**Branch Types by Decision Point**:

**Mode Decision** (Step 3: Scope classification):
```
Trivial Branch (sure): Fast-track checks, light analysis
  |
Moderate Branch (maybe): Full deterministic pass, moderate analysis
  |
Significant/Major Branch (unlikely): Deep analysis, /s escalation considered
```

**Escalation Decision** (Step 17):
```
Local Handling Branch (sure): /r can handle (deterministic improvements available)
  |
Escalation Branch (maybe): /s needed (conflicting options, strategic tradeoff)
  |
Deferral Branch (unlikely): Defer decision (not urgent, can handle later)
```

**Example Output**:
```
ToT Analysis: Reflection Paths
==================================

Memory Decision:
  Branch 1 (sure): Remember all findings (125 items) - 70% confidence
  Branch 2 (maybe): Remember key findings only (25 items) - 25% confidence
  Branch 3 (unlikely): Skip memory (no value) - 5% confidence

Selected: Branch 1 (sure)

Refinement Decision:
  Branch 1 (sure): Full deterministic pass - 85% confidence
  Branch 2 (maybe): Minimal refinement (critical only) - 10% confidence
  Branch 3 (unlikely): No refinement (code sound) - 5% confidence

Selected: Branch 1 (sure)

Escalation Decision:
  Branch 1 (sure): Handle locally (deterministic improvements sufficient) - 80% confidence
  Branch 2 (maybe): Escalate to /s (conflicting options need resolution) - 15% confidence
  Branch 3 (unlikely): Defer to later (not urgent) - 5% confidence

Selected: Branch 1 (sure)

Scope Classification: Moderate (6 files, medium complexity)
Value Completeness: HIGH (3 items, user-facing impact)
```

**What This Catches**:
- Alternative memory strategies (what to remember vs skip)
- Refinement depth scenarios (full pass vs minimal)
- Escalation triggers (when to involve /s vs handle locally)
- Scope classification confidence (trivial vs moderate vs significant)
- Value disclosure scenarios (what to always disclose vs group vs optional)

---

## Combined GoT + ToT Integration

**Synergistic Benefits**:

1. **GoT guides memory organization** -- Extract and analyze finding relationships
2. **ToT guides reflection paths** -- Branch scenarios for memory/refinement decisions
3. **Shared opt-out flags** -- Independent control over each enhancement
4. **Complementary coverage** -- GoT for relationships, ToT for decision paths

**When both enhancements are enabled** (default):
- Forgotten items analyzed for hidden relationships (GoT)
- Reflection decisions explored for branching strategies (ToT)
- Comprehensive memory refinement with optimal improvement sequencing

**Example Integration Flow**:
```
/r deterministic pass
  |
Q1: Read /q context if available
  |
Q2: Build omission checklist from session
  |
Q3: Classify change scope
  +-- ToT: Scope classification branching (trivial/moderate/significant)
  |
Q4-Q14: Run deterministic DUF checks
  +-- /slc: Solo-dev compliance
  +-- /read-before-write: SRPI protocol
  +-- /library-first: Existing solution checks
  +-- /investigate: Evidence verification
  |
Q15: Context-aware filtering
  |
GoT: Extract finding nodes -> Analyze relationships -> Detect cycles
  |
ToT: Reflection path branching -> Escalation decision branching -> Mode decision
  |
Q16: Generate deterministic improvements
  |
Q17: Emit escalation decision + next commands
```
