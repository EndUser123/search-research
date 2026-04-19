# Complete /arch Template System
## With Frameworks, Cognitive Techniques, and Research Protocols

---

# arch/resources/fast.md
## Quick Architecture Decision (5-15 min, <3000 tokens)

**Target:** Single-file decisions, localized changes, immediate validation possible

---

## PREREQUISITE: Decision Pre-Qualification

**Do NOT proceed if:**
1. Query involves >2 loosely-coupled services → escalate to `deep.md`
2. Change is irreversible or breaks backwards compatibility → escalate to `precedent.md`
3. Requires database schema changes → escalate to `data-pipeline.md`
4. Affects system concurrency model → escalate to `python.md`
5. Multi-team coordination needed → escalate to `deep.md`

**Proceed if:** Changes are localized, reversible, single-service, and immediately testable.

---

## COGNITIVE FRAMEWORK: Decision Quality (Decision Intelligence Institute)

This template uses the **Decision Quality** framework[cite:22]:

### Phase 1: Frame the Problem
**What you're doing:** Establishing shared understanding

**Mental model: First Principles Thinking**[cite:23][cite:26]
- Strip away assumptions → What's the *actual* problem, not the symptom?
- Ask "Why?" 2-3 levels deeper
- Identify core constraint (Theory of Constraints)

**Steps:**
1. Read the user's query as stated
2. Ask: "What problem are they *actually* trying to solve?"
   - Is it performance? Maintainability? Correctness? Velocity?
3. Ask: "What's the root constraint?" (not the surface request)
   - Example: User asks "Should I add caching?" 
   - Root constraint: "Requests take 500ms, need <100ms"
   - Real decision: "Where should we cache to hit 100ms?"

**Output of Phase 1:** 1-2 sentence problem statement grounded in constraint

**Memory bank check:**
```
Search memory for:
  - "{domain} performance goals"
  - "{subsystem} latency targets"
  - "user expectations {feature}"
```

---

### Phase 2: Generate Alternatives
**What you're doing:** Exploring solution space (not brainstorming randomly)

**Mental model: Simplicity-First + Systems Thinking**[cite:17]
- Simplicity-First: Does this solution create *essential* vs *accidental* complexity?
- Systems Thinking: What ripple effects will this change create? What feedback loops?

**Structured Brainstorm (5 min max):**
1. **Obvious option:** What's the conventional choice? (layer caching, add queue, etc.)
2. **Opposite angle:** Invert the problem. Instead of "add caching," what if we "reduce cache churn"?
3. **Simplest option:** What's the minimal viable change? (worth exploring even if not chosen)
4. **Recent precedent:** Search CKS for similar decisions. Any patterns?

**Trade-off table for each option:**
```
| Option | Essential Complexity | Accidental Complexity | Reversible? | Team capacity? |
|--------|----------------------|----------------------|-------------|----------------|
| A      | Yes (must add caching) | No (simple Redis) | Yes (1 day) | Yes |
| B      | Partial (complex rules) | Yes (routing logic) | No (breaks API) | No |
```

**Mental discipline:** Reject Option B immediately if accidental complexity exists.

**Memory bank check:**
```
Search memory for:
  - "CKS {domain} {solution_type}"
  - "precedent similar decision"
  - "team velocity {feature_area}"
```

---

### Phase 3: Evaluate Alternatives
**What you're doing:** Scoring solutions against YOUR constraints (not generic criteria)

**Mental model: Attribute-Driven Design (ADD)**[cite:21]
- Quality attributes that matter to *your system*:
  1. **Latency/performance** (from CKS failure analysis)
  2. **Maintainability** (team size, onboarding burden)
  3. **Reversibility** (can we undo if wrong?)
  4. **Implementation cost** (your 120h sprint context)
  5. **Coupling** (does this entangle systems?)

**RICE Scoring (your fast-path engine):**
```
For each option:
  Reach = How many subsystems affected? (1-5 scale)
  Impact = How much does it reduce pain? (1-5 scale)
  Confidence = How sure this works? (0.5-1.0)
  Effort = Implementation hours (1-5 scale)
  
  Score = (Reach × Impact × Confidence) / Effort
```

**Decision rule:** Highest RICE score (if Effort ≤ 8 hours), OR lowest Effort if tied.

**Example:**
```
Option A (Redis caching):
  Reach: 3 (affects this service + metrics)
  Impact: 5 (eliminates 500ms bottleneck)
  Confidence: 0.95 (proven pattern)
  Effort: 2 (4-6 hours)
  Score = (3 × 5 × 0.95) / 2 = 7.125

Option B (Request batching):
  Reach: 4 (affects multiple callers)
  Impact: 4 (reduces by 200ms only)
  Confidence: 0.7 (needs careful sequencing)
  Effort: 4 (12-16 hours)
  Score = (4 × 4 × 0.7) / 4 = 2.8
  
→ Recommend Option A (higher score, lower effort)
```

**Constraint injection (from user context):**
- 120+ hour sprints → *strongly favor* Effort ≤ 4
- Modular preference (ADR-7) → reject highly coupled options
- Event-driven pattern (ADR-23) → prefer async solutions
- No database changes (policy) → eliminate schema-change options

**Memory bank check:**
```
Search memory for:
  - "ADR {number} architectural principle"
  - "constraint {domain} {type}"
  - "CKS {solution} success failure rate"
```

---

## PATH 1: IMPROVE_SYSTEM (If CKS failures exist)

**Trigger:** User is not asking a hypothetical; they have an actual system experiencing problems

**Steps:**

### 1. Query CKS for Failure Patterns
```python
# Pseudo-code for what to do:
failures = search_cks(
    query=f"{domain} FAILURE performance crash deadlock timeout latency",
    limit=5,
    sort_by="recency"
)

# Extract signals from failures:
for failure in failures:
    - When did it happen? (is it recurring?)
    - What changed before it? (what was the trigger?)
    - What's the symptom? (what do users experience?)
    - Root cause from CKS entry?
```

**Mental model: Causal Loop Diagnosis**[cite:24]
- Don't treat each failure as isolated
- Map: What changed → What broke → What's the feedback loop?
- Example: "Added caching → cache invalidation race → stale data → user errors → added retry logic → cache thrashing"

### 2. Score Failure Severity
```
Severity = Frequency × Impact × Exploitability

Frequency: How often? (1-5, daily=5, monthly=2)
Impact: How bad? (1-5, system-down=5, slow UI=2)
Exploitability: Easy to trigger? (1-5, 1-click=5, rare race=1)
```

### 3. Propose Minimal Fix (Targeting Root Cause, Not Symptom)

**Critical cognitive technique: Root Cause Analysis via 5 Whys**
```
Symptom: "Requests timeout after 5 minutes"

Why 1: Queue backs up during peak load
Why 2: Cache misses cause database hammering
Why 3: Cache invalidation deletes too aggressively
Why 4: Timestamp comparison uses wall-clock time, not version numbers
Why 5: Design didn't account for clock skew in distributed system

ROOT CAUSE: Assumption that all servers have synchronized clocks
→ Recommendation: Switch to version-number-based invalidation
```

**NEVER propose:**
- Bandaid fixes (add timeout, add retry)
- Solutions that move the problem (add queue instead of fixing root)
- Complex solutions (if root is fixable simply)

**Recommendation should be:**
- 1-3 specific code/config changes
- Each change grounded in CKS entry + root cause
- Immediately testable (can run test suite after change)
- Reversible within 1 hour

**Output format:**
```
## Root Cause (from CKS analysis)
[Causal chain showing why problem exists]

## Recommendation
[1-3 specific changes]

## Validation
[How to test this works in <30 min]

## Rollback
[How to revert in <10 min if it breaks things]
```

**Memory bank update:**
```
Store:
  - "Fast decision: {problem} → {solution}"
  - "Reasoning: {root_cause_chain}"
  - "Validated: {test_result}"
```

---

## PATH 2: DEFAULT (Hypothetical/Design Question)

**Trigger:** User is designing something new or exploring alternatives

**Steps:**

### 1. Classify Decision Type
```
Decision taxonomy (what are we actually deciding?):
- Module boundary: "Where should X logic live?"
- Refactor scope: "Extract Y into its own service?"
- Pattern choice: "MVC vs event-driven vs layered?"
- Optimization point: "Cache at layer A or B?"
- Debt repayment: "Worth fixing Z now vs later?"
- Technology selection: "Which database/framework?"
```

**If decision type is not in this list → Escalate to deep.md**

### 2. Apply Decision Type Framework

**For PATTERN CHOICE:**
```
Mental model: C4 Model + Attribute-Driven Design[cite:21]

Step 1: What's the quality attribute you're optimizing for?
  - If latency-critical → event-driven or caching
  - If maintainability-first → layered or modular monolith
  - If scalability-critical → service-based
  
Step 2: What's your team's capacity?
  - If team <5 people → avoid distributed systems
  - If ops team is small → avoid complex deployment
  
Step 3: What does your precedent say?
  - Search ADRs: "pattern choice", "architecture style"
  - Stay consistent unless clear reason to diverge
  
Step 4: Map each pattern against YOUR constraints:
  - Performance requirement met?
  - Team can understand/operate it?
  - Follows precedent or documented reason to diverge?
  
Step 5: RICE score the patterns
```

**For OPTIMIZATION POINT:**
```
Mental model: Theory of Constraints[cite:29]

Step 1: Where's the bottleneck?
  - Measure if possible (profile code, benchmark)
  - If not measurable, ask user where they *think* bottleneck is
  
Step 2: Can we optimize that point?
  - Cache at the bottleneck? (not above or below)
  - Batch operations? (parallelization?)
  - Reduce work? (early termination, filters?)
  
Step 3: Will optimization unblock downstream work?
  - If yes → proceed
  - If no → find next bottleneck
  
Example:
  User: "Should I cache at handler or database level?"
  Analysis: Profile shows DB queries take 80% of time
  → Recommend caching at DB level (closer to constraint)
```

**For REFACTOR SCOPE:**
```
Mental model: Coupling Analysis + Reversibility[cite:17]

Step 1: Count dependencies crossing the boundary
  - High coupling (>5 crossing dependencies) → hard to extract
  - Low coupling (<2 crossing dependencies) → easy to extract
  
Step 2: Is extraction reversible?
  - Can we revert in <1 day? → OK to proceed
  - Requires data migration? → escalate to deep.md
  
Step 3: Will extraction reduce accidental complexity?
  - Removes tangled logic → yes, do it
  - Just spreads same logic across 2 files → no, don't do it
```

### 3. Build Output in This Order

**DECISION** (1 sentence recommendation, as specific as possible)
```
Good: "Use Redis caching at the query layer, invalidate on writes"
Bad: "Consider caching"
```

**RATIONALE** (2-3 key reasons, each grounded)
```
1. [From CKS]: Your recent failures show DB hammering during spikes
2. [From constraint]: 5 minute operations need <1 second with caching
3. [From precedent]: ADR-23 established event-driven data flow
```

**ALTERNATIVES CONSIDERED** (briefly, with rejection reason)
```
- Option B (Application-level cache): Rejected because would require
  distributed cache coherence logic (accidental complexity)
- Option C (Read replicas): Rejected because doesn't address write bottleneck
```

**RISKS** (Specific to your system, NOT generic)
```
Real risks:
- Cache stampede on invalidation (mitigate: add jitter to TTL)
- Memory overhead on Redis instance (mitigate: benchmark + monitor)

Fake risks (don't list):
- "Cache might get out of sync" (covered by invalidation)
- "Could be complex to implement" (specific complexity threshold?)
```

**NEXT STEPS** (Concrete, 1-2 items)
```
1. Prototype caching layer (4-6 hours)
2. Load test with concurrent requests (2 hours)
3. Run integration tests, verify cache hit rate >85%
4. Merge if tests pass, monitor in staging for 1 day
```

---

## OUTPUT CONTRACT (Validation Checklist)

**Your response must contain:**
- ✅ Every claim cites CKS entry, ADR, or user constraint
- ✅ Decision is reversible OR risk explicitly acknowledged
- ✅ RICE score or root cause analysis shown (not hidden)
- ✅ Specific to user's system (not generic advice)
- ✅ Testable in <30 minutes
- ✅ Implementable in <8 hours

**If any ✗:** Escalate to deep.md immediately

---

## ESCALATION TRIGGERS (Stop and Redirect)

**Immediately escalate to DEEP.MD if:**
- Affects >2 services ✓ → needs multi-system analysis
- Requires breaking changes to API ✓ → needs precedent review
- Estimated implementation >8 hours ✓ → needs phased plan
- Root cause analysis reveals systemic issue ✓ → needs deep review
- User asks "Why do we have this problem?" repeatedly ✓ → systemic issue
- RICE score <2.0 on all options ✓ → no good solution in fast path
- Implementation would violate recent ADR ✓ → precedent conflict

**On escalation, output:**
```
## Escalating to deep.md

**Reason:** [specific trigger from list above]

**Analysis so far:** [what you discovered before escalating]

**Why deep analysis needed:** [what fast path cannot address]
```

Then *follow deep.md workflow entirely*.

---

## RESEARCH PROTOCOL (What to Search Before Recommending)

```python
# Internet research (if recommendation is uncertain):
searches = [
    "{technology} best practices {year}",
    "{technology} common failure modes",
    "{technology} performance benchmarks",
]

# Memory bank searches:
cks_queries = [
    f"{domain} FAILURE {symptom}",
    f"CKS {domain} {solution_type} success",
    f"constraint {domain} performance",
]

adrs = [
    f"precedent similar decision",
    f"ADR {number} {pattern}",
    f"architectural principle {domain}",
]

# If still uncertain after searches:
→ Escalate to deep.md (means question needs more depth)
```

---

## MENTAL MODEL CHECKLIST (Use Before Committing to Answer)

Before finalizing your recommendation, verify you've applied:

- ✅ **First Principles:** Boiled down to root constraint (not symptom)?
- ✅ **Simplicity-First:** Solution creates essential complexity only?
- ✅ **Systems Thinking:** Traced ripple effects and feedback loops?
- ✅ **Causal Loop Diagnosis:** Root cause identified (5 Whys)?
- ✅ **Attribute-Driven Design:** Quality attributes ranked?
- ✅ **RICE Scoring:** Trade-offs quantified?
- ✅ **Theory of Constraints:** Optimizing the actual bottleneck?
- ✅ **C4 Model:** Clear on scope (service/component/layer)?

**If any ✗:** Escalate or do more analysis before committing.

---

---

# arch/resources/deep.md
## Comprehensive Architecture Analysis (40-90 min, <12000 tokens)

**Target:** Multi-system designs, breaking changes, strategic decisions, 1-6 month payoff

---

## PREREQUISITE: Depth Justification

**You're in deep.md because:**
1. ✓ Decision affects >2 services, OR
2. ✓ Implementation >8 hours, OR
3. ✓ Breaking changes required, OR
4. ✓ Systemic architectural issue, OR
5. ✓ Escalated from fast.md

**Do NOT proceed if:**
- This is a quick optimization (use fast.md)
- Decision is simple pattern choice without multi-system impact (use fast.md)
- Escalation reason doesn't match above list (use appropriate template)

---

## COGNITIVE FRAMEWORK: Multi-Dimensional Analysis

**Primary framework: Attribute-Driven Design (ADD) at scale**[cite:21]

This template applies sophisticated decision analysis across multiple quality attributes and time horizons.

---

## STAGE 1: Deep Problem Framing

### Sub-stage 1.1: Systems Thinking - Map the System

**Mental model: Systems Thinking + Causal Loop Diagrams**[cite:17][cite:24]

Step 1: Identify all affected components (C4 Model)
```
Context level: What external systems interact?
Container level: What's inside our system boundary?
Component level: How do components within containers interact?
```

Step 2: Map dependencies and feedback loops
```
Example causal loop:
High load → Long queue → Timeouts → Retries → Higher load → [feedback]

Question: Is this a virtuous or vicious loop?
- Vicious: Retries amplify load → collapse
- Virtuous: Backpressure reduces load → stabilizes
```

Step 3: Identify "closely coupled" tasks (potential failure points)
```
From escalation research[cite:28]:
  Which decisions are tightly dependent on other decisions?
  Which data flows are hard to sync?
  Which assumptions are fragile?
  
These are your bottlenecks in the decision process.
```

**Memory bank search:**
```
cks.search("system behavior {domain} under load")
cks.search("dependency {system_A} {system_B}")
cks.search("failure cascade {root_cause}")
```

### Sub-stage 1.2: Reframe via Inversion

**Mental model: Inversion (think backwards)**

Instead of: "How do we improve X?"
Ask: "What would make X fail catastrophically?"

Then reverse that failure mode → get your design constraint.

```
Example:
  Naive question: "Should we use microservices?"
  Inversion: "What would make microservices fail for us?"
    - Distributed tracing complexity exceeds team skills
    - Deployment pipeline not mature enough
    - Network latency between services causes cascades
  Reversed: "We need mature DevOps + observability before microservices"
  → Real question: "Do we have operational maturity for this change?"
```

**Output:** Reframed problem statement that surfaces hidden constraints

---

## STAGE 2: Generate Strategic Alternatives

**NOT brainstorming; structured exploration with architectural patterns**[cite:21]

### Sub-stage 2.1: Map Architectural Patterns

For your domain, list established patterns:
```
Data pipeline architecture:
  - Lambda (batch + streaming)
  - Kappa (streaming only)
  - Event sourcing (immutable log)
  - CDC (Change Data Capture)
  
Microservices patterns:
  - API gateway + services
  - Event-driven orchestration
  - Saga pattern (distributed transactions)
  - CQRS (Command/Query segregation)
  
Scaling patterns:
  - Horizontal scaling (add replicas)
  - Caching tiers
  - Database sharding
  - Read replicas + eventual consistency
```

**Selection rule:** Choose 3-5 patterns that address your reframed problem.

**Memory bank search:**
```
cks.search("pattern {domain} {pattern_name}")
cks.search("precedent ADR architectural style")
cks.search("attempted {pattern_name} {success_or_failure}")
```

### Sub-stage 2.2: Build Implementation Scenarios

For each pattern, answer:
```
1. What's the implementation path? (phases, timeline)
2. What gets built in phase 1? (MVP)
3. What's deferred to phase 2-3?
4. What's the migration strategy from current state?
5. What's the rollback plan if it fails?
```

**Critical: Build *implementation scenarios*, not just architectural diagrams**

---

## STAGE 3: Evaluate via Multi-Dimensional Trade-off Matrix

**Mental model: Attribute-Driven Design + Constraint propagation**[cite:21]

### Sub-stage 3.1: Define Quality Attributes (for THIS system)

Not generic attributes; specific to your situation:

```
From user context (120h sprints, distributed team, 100K LOC):
1. VELOCITY: Can we implement this in <3 months?
2. REVERSIBILITY: Can we undo if it breaks?
3. TEAM_CAPACITY: Does our team have the skills?
4. OPERATIONAL_BURDEN: How much ops complexity added?
5. PERFORMANCE: Does it hit latency targets?
6. SCALABILITY: Does it scale to 10x current load?
7. MAINTAINABILITY: Will future devs understand this?
8. CONSISTENCY: Breaks with established patterns?
```

### Sub-stage 3.2: Build Trade-off Matrix

```
| Attribute | Pattern A | Pattern B | Pattern C | Weight |
|-----------|-----------|-----------|-----------|--------|
| Velocity | 4/5 (2mo) | 2/5 (4mo) | 1/5 (6mo) | 9 |
| Reversible | 5/5 | 2/5 | 1/5 | 8 |
| Team capacity | 4/5 | 3/5 | 2/5 | 8 |
| Operational | 3/5 | 2/5 | 1/5 | 7 |
| Performance | 3/5 | 5/5 | 5/5 | 6 |
| Scalability | 2/5 | 4/5 | 5/5 | 6 |
| Maintainability | 4/5 | 3/5 | 2/5 | 7 |
| Consistency | 5/5 | 3/5 | 2/5 | 5 |

Weighted score:
  A: (4×9 + 5×8 + 4×8 + 3×7 + 3×6 + 2×6 + 4×7 + 5×5) / 56 = 3.8/5
  B: (2×9 + 2×8 + 3×8 + 2×7 + 5×6 + 4×6 + 3×7 + 3×5) / 56 = 3.1/5
  C: (1×9 + 1×8 + 2×8 + 1×7 + 5×6 + 5×6 + 2×7 + 2×5) / 56 = 2.9/5

Recommendation: Pattern A (highest score)
```

**But:** If score is close, discuss top 2-3 patterns in detail.

### Sub-stage 3.3: Stress-Test via Scenarios

For top 2 options, war-game:

```
Scenario 1: "What if load grows 10x?"
  Pattern A: Can add caching layer, scales horizontally
  Pattern B: Requires database resharding, risky

Scenario 2: "What if key engineer leaves?"
  Pattern A: Remaining team can operate (simple pattern)
  Pattern B: Requires distributed systems expertise, team can't support

Scenario 3: "What if we get 24h to rollback?"
  Pattern A: Revert in 2 hours (feature flag)
  Pattern B: Requires data migration reversal (12+ hours)
  
→ Scenarios reveal hidden risks
```

**Memory bank search:**
```
cks.search("failure scenario {pattern} {failure_mode}")
cks.search("recovery time {pattern} {incident_type}")
```

---

## STAGE 4: Implementation Planning

**Mental model: Phased implementation + risk staged rollout**[cite:25]

### Sub-stage 4.1: Break into Phases

```
Phase 1 (Weeks 1-3): MVP
  - What's the smallest version that proves the concept?
  - Can we test in staging without production impact?
  - What are the done-done criteria?
  
Phase 2 (Weeks 4-8): Expand
  - Migrate 10-20% production traffic
  - Monitor for 1-2 weeks
  - If successful, ramp to 50%
  
Phase 3 (Weeks 9-12): Full rollout
  - Move remaining traffic
  - Decommission old system
  - Document lessons learned
```

### Sub-stage 4.2: Risk Escalation Protocol

**Use structured escalation matrix**[cite:25]:

```
Risk: Database resharding fails
  Severity: CRITICAL (data loss possible)
  Threshold: Escalate if >5% data loss
  Authority: Requires VP-level decision
  Rollback: Pre-test rollback procedure weekly
  
Risk: Performance degradation
  Severity: HIGH (user impact)
  Threshold: Escalate if latency >2x baseline
  Authority: On-call engineer can trigger rollback
  Rollback: <10 minutes
  
Risk: Team capacity overwhelmed
  Severity: MEDIUM (schedule slip)
  Threshold: Escalate if team capacity <20% buffer
  Authority: Tech lead reallocates work
  Rollback: Pause migration, continue with old system
```

---

## STAGE 5: Risk & Mitigation Deep Dive

**Mental model: Pre-mortem + FRAM analysis**[cite:28]

### Sub-stage 5.1: Pre-mortem (Imagine failure, work backward)

```
Imagine it's 3 months from now.
The implementation FAILED catastrophically.
What happened?

Common post-mortems:
1. "Team underestimated scope → shipped incomplete"
2. "Operational burden exceeded capacity → on-call team burned out"
3. "Broke backwards compatibility → client escalations"
4. "Performance regression → users complained"
5. "Couldn't rollback → stuck with broken system"

For each, identify how to detect + prevent.
```

### Sub-stage 5.2: Functional Resonance Analysis (FRAM)

**Identify tightly-coupled tasks** (where small changes cause cascades)[cite:28]:

```
Example (data migration):
Task 1: Copy data from old DB
Task 2: Synchronize writes (dual-write pattern)
Task 3: Verify consistency
Task 4: Migrate reader traffic
Task 5: Shut down old DB

Tightly-coupled pairs:
  - Task 2 ↔ Task 3 (consistency check depends on dual-write)
  - Task 3 ↔ Task 4 (can't move readers until verified)
  
→ These are your fragility points. Plan extra testing here.
```

### Sub-stage 5.3: Mitigation Strategy

```
For each pre-mortem + FRAM finding:

Risk: Team underestimated scope
  Mitigation 1: Weekly scope reviews (catch early)
  Mitigation 2: Buffer 30% of timeline for unknowns
  Mitigation 3: Kill-switch: Can pause and roll back if >3 weeks behind
  
Risk: Operational burden
  Mitigation 1: Shadow old system during phase 2 (build runbooks)
  Mitigation 2: Train 2 people on each critical component
  Mitigation 3: Automated health checks + alerting (catch issues <5 min)
```

---

## STAGE 6: Decision & Recommendation

### Output Format: Extended ADR[cite:21]

```markdown
# Decision Record: [Title]

## Status
PROPOSED / ACCEPTED / IMPLEMENTED / DEPRECATED

## Context
[Problem statement from Stage 1]
[System constraints]
[Business drivers]

## Decision
We will [implement pattern X] with [phased rollout] over [timeline].

## Rationale
1. [Highest weighted score in trade-off matrix]
2. [Addresses primary constraint from problem framing]
3. [Team has capacity for implementation]
4. [Reversible within [timeframe] if needed]

## Consequences

### Positive
- [Upside 1, quantified]
- [Upside 2, quantified]

### Negative
- [Downside 1, risk mitigation strategy]
- [Downside 2, risk mitigation strategy]

## Implementation Plan
Phase 1: [MVP definition + timeline]
Phase 2: [Expansion + monitoring]
Phase 3: [Full rollout + decommissioning]

## Rollback Plan
[Specific steps to revert, estimated time, decision authority]

## Validation Criteria
- Metric 1: [target] by [date]
- Metric 2: [target] by [date]
- Metric 3: [target] by [date]

## Related ADRs
[Links to precedent decisions]
```

---

## RESEARCH PROTOCOL (Deep Dive)

Before finalizing recommendation, conduct:

### Internet Research (2-3 searches max)
```
searches = [
    f"{pattern_name} implementation best practices {year}",
    f"{pattern_name} common pitfalls failure modes",
    f"{pattern_name} benchmark {your_scale} users",
]

For each search result:
  - Source quality? (established company/researcher?)
  - Applies to your scale? (benchmarks at 10K users, you have 100M)
  - Recent enough? (changed in last 6-12 months?)
  
→ If findings contradict your analysis, update decision matrix
```

### Memory Bank Deep Search
```
cks.search(f"pattern {pattern_name} success failure rate")
cks.search(f"implementation {pattern_name} lessons learned")
cks.search(f"team velocity {pattern_name} {team_size}")
cks.search(f"operational burden {pattern_name} {scale}")

For each result:
  - Extract: "When {pattern} worked / failed"
  - Store: "Because {reason}"
  - Link: "Related to decision: {pattern_choice}"
```

### Precedent Review (ADR Analysis)
```
Related ADRs:
  - ADR-7: "Prefer modular over monolithic"
    → This pattern consistent? Why yes/no?
  - ADR-23: "Event-driven for data pipelines"
    → This pattern extends ADR-23? Or contradicts?
  - ADR-42: "Async Python preferred"
    → Implementation aligned with async constraints?

If contradiction found:
  Option 1: Diverge + document why (new ADR)
  Option 2: Change recommendation to align with precedent
```

---

## OUTPUT CONTRACT (Validation Checklist)

**Your response must contain:**
- ✅ Systems Thinking analysis (dependencies, feedback loops, fragile points)
- ✅ Trade-off matrix with weighted scores
- ✅ Top 3 patterns evaluated (not just one)
- ✅ Stress tests (3+ scenarios covering edge cases)
- ✅ Pre-mortem analysis (what could go wrong?)
- ✅ FRAM analysis (tightly-coupled task identification)
- ✅ Phased implementation plan (phases, timelines, done-done criteria)
- ✅ Escalation matrix (risks + authorities + thresholds)
- ✅ Rollback procedure (specific steps, timeline, decision authority)
- ✅ Quantified payoff (time saved, capacity freed, reliability improved)
- ✅ Every claim cites: CKS entry, research, ADR, or scenario analysis
- ✅ Implementation timeline realistic for your team (respects 120h sprint context)

**If any ✗:** Flag it before finalizing recommendation.

---

## ESCALATION TRIGGERS (Kick upstairs)

**Escalate to precedent.md if:**
- Recommendation contradicts established ADR without strong justification
- Decision affects team structure or hiring

**Escalate to external stakeholder if:**
- Requires >6 month timeline (VP approval)
- Has company-wide architectural implications
- Impacts customer contract commitments

---

## MENTAL MODEL CHECKLIST (Deep Version)

Before finalizing, verify:

- ✅ **Systems Thinking:** Mapped all dependencies and feedback loops?
- ✅ **Inversion:** What would catastrophically fail? Addressed?
- ✅ **Attribute-Driven:** All quality attributes weighted for YOUR context?
- ✅ **RICE/Weighted Scoring:** Trade-offs quantified?
- ✅ **Scenario Analysis:** Stress-tested against 3+ realistic failures?
- ✅ **Pre-mortem:** Identified 3+ ways this could fail?
- ✅ **FRAM:** Found tightly-coupled tasks and tested them extra?
- ✅ **Escalation Protocol:** Clear decision authorities and thresholds?
- ✅ **Reversibility:** Can we undo this? How long? Cost?

**If any ✗:** Rework before committing.

---

---

# arch/resources/_shared_preamble.md
## Pre-Template Execution (All templates run this first)

**This preamble runs before fast.md or deep.md**

---

## STEP 1: Load Context From User + Memory

### 1.1 Extract User Context From Query

```python
# What type of query is this?
intent_type = classify(query)  # "improvement", "design", "troubleshooting"
domain = extract_domain(query)  # "python", "cli", "data-pipeline", etc.
urgency = detect_urgency(query)  # "blocking", "high", "medium", "low"
```

### 1.2 Load From Memory Bank (CKS)

```python
# What's the user's recent context?
cks_failures = search_cks(
    f"{domain} FAILURE recent",
    limit=3
)

cks_constraints = search_cks(
    f"constraint {domain} latency performance capacity",
    limit=5
)

cks_precedent = search_cks(
    f"ADR {domain} architectural decision pattern",
    limit=3
)

# Load from precedent.md what decisions already made in this domain
adrs = load_adr_summary(domain)
```

**Memory bank searches (per template):**
- fast.md: Focus on recent failures + quick wins from CKS
- deep.md: Focus on precedent (ADRs) + performance requirements

---

## STEP 2: Set Output Budget

```python
template = route_to_template(query)

# Token budgets:
if template == "fast.md":
    max_tokens = 3000
    max_time = "15 minutes"
elif template == "deep.md":
    max_tokens = 12000
    max_time = "90 minutes"
```

**Why:** Prevents sprawl. Fast answers should be fast.

---

## STEP 3: Initialize Logging/Tracing

```python
trace_id = generate_uuid()
log_event("arch_query_started", {
    "trace_id": trace_id,
    "query": query[:100],  # truncate for privacy
    "domain": domain,
    "template": template,
    "timestamp": now()
})
```

**Why:** Enables post-hoc analysis. Which queries lead to good decisions? Which ones get reworked?

---

## STEP 4: Pre-flight Checks

```python
# Is the user asking something outside /arch scope?
if is_syntax_question(query):
    respond: "That's a /code question. Use /code instead."
    exit()

if is_debugging_specific_error(query):
    respond: "That looks like a specific debug session. Use /debug instead."
    exit()

# Does the query have enough context?
if insufficient_context(query):
    ask_clarifying_questions([
        "What's the current system state?",
        "What are you trying to achieve?",
        "What's the timeline/urgency?",
    ])
    exit()
```

**Why:** Fail fast on out-of-scope questions instead of forcing them into architecture analysis.

---

## STEP 5: Constraint Injection

```python
# User context (from memory + query):
user_constraints = {
    "sprint_model": "120+ hour intensive sprints",
    "team_size": 1,
    "codebase_size": "100K LOC",
    "deployment_frequency": "daily",
    "current_pain_points": [
        "Context loss over long sessions",
        "Rate limiting on APIs",
        "Integration complexity"
    ]
}

# Architectural preferences (from ADRs):
arch_preferences = {
    "modularity": "modular over monolithic" (ADR-7),
    "async_model": "async Python preferred" (ADR-42),
    "data_flow": "event-driven pipelines" (ADR-23),
}

# These constraints + preferences shape every recommendation.
# Example: Fast.md will strongly prefer options with effort ≤ 4 hours
#          because of 120-hour sprint model + context loss.
```

**Why:** Prevents generic advice. Recommendation respects your real constraints.

---

## STEP 6: Determine Template + Path

```python
# Route to correct template (done by /arch SKILL.md routing logic)
# Determine internal path: IMPROVE_SYSTEM vs DEFAULT

if has_real_system_failures(query):
    path = "IMPROVE_SYSTEM"
    # User has actual problem in live system
    # Ground analysis in failure patterns from CKS
else:
    path = "DEFAULT"
    # User is designing/exploring alternatives
    # Use decision frameworks on hypothetical choices
```

---

## SHARED: Decision Frameworks (Available to All Templates)

### Framework 1: First Principles Thinking[cite:23][cite:26]

```
When stuck, use this:
1. What's the assumption I'm making?
2. Is that assumption true? (or just conventional wisdom?)
3. What would happen if I inverted it?

Example:
  Assumption: "Caching always helps"
  Question: "When does caching hurt?" (cache coherence, staleness, memory)
  Inverted: "What if we *never* cache? What breaks?"
  → Discover that we only need caching for expensive queries, not all queries
```

### Framework 2: Simplicity-First[cite:17]

```
When evaluating options, ask:
1. Does this option add ESSENTIAL complexity?
   (Required by the problem domain)
2. Or ACCIDENTAL complexity?
   (Introduced by our solution design)

ALWAYS prefer options with less accidental complexity.

Example:
  Option A: Add Redis caching
    Essential: Need to reduce DB load (essential)
    Accidental: Redis adds operational complexity (can we reduce this?)
    Question: Can we use in-memory cache + eventual consistency instead?
```

### Framework 3: Systems Thinking[cite:17][cite:24]

```
When proposing a change, trace ripples:
1. What component changes?
2. What depends on that component?
3. What depends on those dependents?
4. Are there feedback loops? (Does change amplify itself?)

Example:
  Change: Add request batching to reduce DB queries
  Ripple 1: Batched requests have higher latency
  Ripple 2: Higher latency causes some callers to timeout
  Ripple 3: Timeouts trigger retries
  Ripple 4: Retries amplify batch sizes
  → Feedback loop: Change could make things worse!
  → Mitigation: Add timeout adjustment + retry backoff
```

### Framework 4: Theory of Constraints[cite:29]

```
System output is limited by its one bottleneck.

When optimizing, ask:
1. What's the actual bottleneck?
2. Can I optimize AT the bottleneck (not around it)?
3. If I remove this bottleneck, what's the NEXT bottleneck?

Example:
  You think: "Add caching to speed up requests"
  Reality: Profile shows network round-trip is bottleneck, not DB
  Optimization: Batch queries or reduce network calls
  → Caching won't help much until network is solved
```

---

## SHARED: CKS Query Templates

Copy-paste these CKS searches before responding:

```python
# For any domain-specific recommendation:
cks.search(f"{domain} FAILURE {failure_mode}")

# For performance claims:
cks.search(f"{solution} performance benchmark {scale}")

# For pattern advice:
cks.search(f"precedent {pattern} success failure rate")

# For team/capacity concerns:
cks.search(f"team velocity {feature_area} {team_size}")

# For historical context:
cks.search(f"decision timeline {feature_area} years")
```

---

## SHARED: ADR Linking

Every recommendation should link to related ADRs:

```markdown
## Related Precedent
- ADR-7: Prefer modular architecture → Aligns
- ADR-23: Event-driven data flow → Extends
- ADR-42: Async Python preferred → Respected

Status: This decision is CONSISTENT with precedent.
(Or: This decision DIVERGES from ADR-X because [reason], consider new ADR)
```

---

## SHARED: Uncertainty Handling

**If you're uncertain about something:**

Option 1: Search CKS (fast)
Option 2: Do 1-2 internet searches (medium)
Option 3: Recommend lower-risk option (safer)
Option 4: **Escalate to deeper analysis** (most honest)

**NEVER guess or present uncertainty as confidence.**

Better to say: "This needs deep.md analysis" than force a weak answer.

---

## End of Preamble

Proceed to your assigned template (fast.md or deep.md) with context loaded.
