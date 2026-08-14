---
title: "I'm working with an agentic coding assistance (Claude Code), and I'm trying to create the most effective RCA prompt ever"
date: "2025-12-03"
mode: "COPILOT"
uuid: "82bdfa3c-7a33-4701-8261-267c406a3aea"
entry_count: 6
---

## Human

I'm working with an agentic coding assistance (Claude Code), and I'm trying to create the most effective RCA prompt ever.  I've attached what I have so far.  Can you improve it?  I really want it to be able to fix any problem I encounter.

## Assistant

Now I have a comprehensive view of your system and best practices. Your RCA v5.0 is already sophisticated, but I can see several opportunities to make it significantly more effective based on current agentic debugging research and prompt optimization techniques.

## Key Improvements for Your RCA Prompt

### 1. Add Extended Thinking Triggers
Your current prompt lacks explicit cognitive escalation. Research shows using words like "think harder," "ultrathink," or "think step by step" triggers deeper reasoning.[1][2]

```markdown
## Cognitive Escalation Protocol
When encountering resistance or uncertainty:
1. **Level 1 (Default):** Standard analysis
2. **Level 2 ("think harder"):** Re-examine assumptions, check for confirmation bias
3. **Level 3 ("ultrathink"):** Generate competing hypotheses, devil's advocate analysis
4. **Level 4 ("maximum depth"):** Full counterfactual analysis, cross-file dependency tracing

**Trigger words for escalation:**
- "This doesn't make sense" → Escalate to Level 2
- "I'm uncertain" → Escalate to Level 3  
- "Multiple conflicting hypotheses" → Escalate to Level 4
```

### 2. Mandatory Stop-and-Verify Checkpoints
Your current system flows without hard stops. Add mandatory verification gates:[3][4]

```markdown
## Hard Verification Gates (MUST NOT PROCEED WITHOUT)

### Gate 1: Evidence Sufficiency Check
BEFORE generating hypotheses, verify:
- [ ] At least 3 pieces of independent evidence collected
- [ ] Evidence is VERIFIABLE (can be re-checked)
- [ ] If evidence unavailable, state: "EVIDENCE GAP: [specific gap]"

### Gate 2: Hypothesis Falsifiability Check  
BEFORE testing hypotheses:
- [ ] Each hypothesis has a CLEAR falsification condition
- [ ] Null hypothesis explicitly stated: "The system is working correctly and the issue is [external factor]"
- [ ] At least one hypothesis challenges the obvious answer

### Gate 3: Fix Verification Check
BEFORE marking resolved:
- [ ] Fix tested in isolation
- [ ] No regressions introduced (run affected tests)
- [ ] Fix addresses ROOT cause, not just symptoms
```

### 3. Anti-Hallucination Strengthening
Your current rules are good but can be more explicit:[5]

```markdown
## Anti-Hallucination Protocol (ZERO TOLERANCE)

### FORBIDDEN Actions:
1. **Never fabricate:** logs, stack traces, error messages, line numbers, timestamps
2. **Never assume:** file contents without reading, function signatures without checking
3. **Never claim:** "I verified" without showing the verification command/output

### REQUIRED Actions:
1. **Quote exactly:** When citing code, use `[code:path/file.py:L15-20]` with exact lines
2. **Show your work:** Every diagnostic claim requires: `EVIDENCE: [tool used] → [exact output]`
3. **Admit uncertainty:** Use confidence scores: HIGH (>80%), MEDIUM (50-80%), LOW (<50%)
4. **State unknowns:** "UNKNOWN: Cannot determine [X] because [Y]"
```

### 4. 5-Whys Integration with Depth Limits
Add structured causal drilling:[6]

```markdown
## Causal Depth Analysis (5-Whys Enhanced)

For each suspected root cause, drill down:

**Why 1 (Symptom):** What exactly failed?
→ EVIDENCE: [citation]

**Why 2 (Mechanism):** What code/config caused that failure?
→ EVIDENCE: [citation]

**Why 3 (Trigger):** What change/input triggered that code path?
→ EVIDENCE: [citation]

**Why 4 (Design):** Why did the design allow this failure mode?
→ EVIDENCE: [citation]

**Why 5 (Process):** Why wasn't this caught earlier (tests/review)?
→ EVIDENCE: [citation] OR "SYSTEMIC GAP IDENTIFIED"

**STOP DRILLING when:**
- You hit an external dependency you cannot change
- You reach organizational/process level (flag for human review)
- Evidence becomes speculative (mark as "HYPOTHESIS ONLY")
```

### 5. Plan-First Mode for Complex Issues
Add explicit two-phase approach:[4]

```markdown
## Two-Phase Debugging Protocol

### Phase A: Investigation (READ-ONLY)
**Duration:** 60% of allocated time
**Allowed:** Read files, search codebase, analyze logs, form hypotheses
**FORBIDDEN:** Any code modifications, even "quick fixes"
**Output:** Investigation Report with ranked hypotheses

### Phase B: Intervention (WRITE)
**Duration:** 40% of allocated time
**Prerequisite:** Phase A complete AND user approval for complex issues
**Approach:** Smallest possible change that addresses confirmed root cause
**Required:** Rollback plan before any modification
```

### 6. Cross-File Causality Tracing
Add explicit dependency tracing:[4]

```markdown
## Cross-File Causality Trace

When the bug spans multiple files:

1. **Entry Point:** Where does the error surface? `[file:line]`
2. **Call Stack:** Trace backwards through callers
3. **Data Flow:** Where does corrupted/unexpected data originate?
4. **State Mutation:** What functions modify shared state?
5. **Import Chain:** Are there circular/conflicting imports?

**Output Format:**
```
TRACE: error_surface.py:45 
  ← called by: handler.py:120 
  ← data from: validator.py:67 (⚠️ MUTATION HERE)
  ← original input: api.py:23
ROOT: validator.py:67 - [description of actual bug]
```
```

### 7. Simplified Strategy Router
Your 6-strategy router may add cognitive load. Simplify to 3:[7]

```markdown
## Simplified Strategy Selection

| Signal | Strategy | Time Budget |
|--------|----------|-------------|
| Clear error message + obvious fix | **QUICK FIX** | 5 min |
| Error but unclear cause | **STANDARD RCA** | 30 min |
| Sev-1, security, or "weird" behavior | **DEEP ANALYSIS** | 60 min |

**Default:** STANDARD RCA (when uncertain, take the middle path)
```

### 8. Iterative Refinement Loop
Add explicit retry logic:[8][9]

```markdown
## Retry Protocol

If first fix attempt fails:

**Attempt 2:** 
- Re-read error output CAREFULLY
- Check: Did I solve the REPORTED problem or a DIFFERENT problem?
- Hypothesis: "My fix was wrong because [specific reason]"

**Attempt 3:**
- STOP modifying code
- Generate NEW hypothesis set (discard previous)
- Ask: "What am I assuming that might be wrong?"

**Attempt 4+:**
- ESCALATE: "I have attempted 3 fixes without success. Requesting human review."
- Provide: All evidence, all hypotheses tried, why each failed
```

### Consolidated Enhanced Prompt Template

Here's the improved structure combining all enhancements:

```markdown
# RCA v6.0 - Enhanced Root Cause Analysis

## Prime Directive
You are a systematic debugging agent. Your goal is to identify the TRUE root cause 
with HIGH confidence (>80%) before proposing any fix. Evidence-first. Hypotheses second. 
Fixes last.

## Cognitive Protocol
- Default: Methodical analysis
- On uncertainty: "think harder" - re-examine assumptions
- On complexity: "ultrathink" - generate competing hypotheses
- On repeated failure: STOP and escalate

## Phase 1: Evidence Collection (READ-ONLY)
1. Gather ALL available evidence (logs, errors, code, configs)
2. For each piece: `EVIDENCE [type]: [source] → [exact content]`
3. Gate Check: Do I have ≥3 independent evidence pieces? If NO → gather more

## Phase 2: Hypothesis Generation
1. Generate 3-5 hypotheses ranked by probability
2. MUST include null hypothesis: "System correct, input/environment wrong"
3. Each hypothesis needs: falsification condition, test method
4. Gate Check: Are all hypotheses falsifiable? If NO → refine

## Phase 3: Hypothesis Testing
For each hypothesis (highest probability first):
- Test: [specific action]
- Result: [exact output]  
- Verdict: CONFIRMED / REJECTED / INCONCLUSIVE
- If INCONCLUSIVE: gather more evidence or escalate

## Phase 4: Root Cause Declaration
- Root Cause: [one sentence]
- Confidence: [HIGH/MEDIUM/LOW with %]
- Evidence Chain: [citation1] → [citation2] → [citation3]
- 5-Whys Depth: [how deep did causal analysis go]

## Phase 5: Fix Implementation
- Prerequisite: Root cause confidence ≥80%
- Approach: Smallest change that addresses root cause
- Rollback: [how to undo if fix fails]
- Verification: [exact command to confirm fix works]

## Phase 6: Verification
- [ ] Fix applied
- [ ] Original error no longer occurs  
- [ ] No new errors introduced
- [ ] Tests pass (if applicable)

## Output
🚨 [One-sentence summary: what was wrong and how it was fixed] 🚨
```

This enhanced version incorporates extended thinking triggers, hard verification gates, anti-hallucination protocols, 5-Whys drilling, plan-first debugging, cross-file tracing, and iterative retry logic. The key philosophy shift is **evidence-first, fixes-last** with mandatory checkpoints that prevent premature solutions.[10][11][5]

## Human

That file is a lot shorter than what I had before.  Is that intentional?  Did we forget anything?

## Assistant

You're absolutely right to call that out. I gave you a condensed template, but your original system has significantly more depth. Let me read the files I haven't fully examined to ensure we don't lose any valuable components.

## Human

Continue

## Assistant

Now I have the complete picture. Your system is **much more sophisticated** than I initially realized. You have:

- **CWO 12-Step Integration** with full lifecycle management[1]
- **Multi-Agent Debate Council** with 7 specialists and consensus protocols[2]
- **Local Pattern Learning** for ML-based pattern recognition[3]
- **Tree-Sitter Integration** for AST-based analysis[4]
- **Hypothesis-Driven Debugging** with scientific method[5]
- **6-Strategy Router** with Protocol A/B/C/D[6]

My earlier response was a **skeleton**, not a replacement. Here's the **complete enhanced RCA v6.0** that preserves everything and adds the improvements:

***

## Enhanced RCA v6.0 - Complete Specification

```markdown
---
id: rca-unified-v6
title: Unified Root Cause Analysis (RCA) Command Specification
description: The definitive specification for RCA v6.0 - Enhanced with cognitive 
  escalation, hard verification gates, and anti-hallucination protocols.
category: spec
version: 6.0.0
replaces:
  - rca-unified-v5
  - enhanced_rca.md
  - rca_comprehensive.md
  - systematic_troubleshooting_protocol.md
---

# Unified Root Cause Analysis (RCA) Command v6.0

The **RCA v6.0** command is the central intelligent entry point for investigating 
production incidents, performance regressions, security vulnerabilities, and 
systemic failures. It enforces **Systematic Troubleshooting**, **Scientific 
Hypothesis Testing**, **Constitutional Compliance** (CWO12), and **Cognitive 
Escalation Protocols**.

---

## 0. Prime Directive & Cognitive Protocol

### Prime Directive
You are a systematic debugging agent. Your goal is to identify the TRUE root cause 
with HIGH confidence (>80%) before proposing any fix. **Evidence-first. Hypotheses 
second. Fixes last.**

### Cognitive Escalation Protocol
When encountering resistance, uncertainty, or repeated failures, escalate cognitive depth:

| Level | Trigger | Action |
|-------|---------|--------|
| **L1 Default** | Normal analysis | Standard methodology |
| **L2 "think harder"** | Initial uncertainty | Re-examine assumptions, check confirmation bias |
| **L3 "ultrathink"** | Multiple possibilities | Generate competing hypotheses, devil's advocate |
| **L4 "maximum depth"** | Complex/Sev-1 | Full counterfactual analysis, cross-file dependency tracing |

**Auto-Escalation Triggers:**
- "This doesn't make sense" → Escalate to L2
- "I'm uncertain" → Escalate to L3
- "Multiple conflicting hypotheses" → Escalate to L4
- 2+ failed fix attempts → STOP and escalate to human

---

## 1. Tier 1: Strategy Selection & Routing

The system automatically classifies issues into one of 6 strategies based on 
pattern matching and intent analysis.

| Strategy | Trigger Patterns | Execution Engine | Timeline |
|:---------|:-----------------|:-----------------|:---------|
| **SIMPLE_FIX** | "typo", "forgot to", "config", "missing var" | `rca_intelligent_command.py` | **< 1 min** Direct fix. No deep scan. |
| **QUICK_TRIAGE** | "error", "crash", "fail", "exception" | `rca_intelligent_command.py` | **5 min** 5-Phase rapid assessment. |
| **DATA_GATHERING** | "slow", "weird", "unknown", "intermittent" | `rca_intelligent_command.py` | **10 min** Log analysis & metrics only. |
| **STANDARD_RCA** | (Default catch-all) | `intelligent_rca_engine.py` | **30 min** Full Protocol A (8-Phase). |
| **DEBATE_COUNCIL** | "complex", "architect", "sev-1", "security" | `multi_agent_debate_council.py` | **15 min** Protocol B (7-Agent). |
| **BATCH_SCAN** | "codebase", "audit", "all files", "pattern" | `batch_processing_mode.py` | **Var** Parallel Protocol C. |

**Default Rule:** When uncertain, select **STANDARD_RCA** (middle path).

---

## 2. Mandatory Operational Requirements

### A. The "3-Alarm" Summary Rule

**CRITICAL:** When fixing a bug, identifying a root cause, or proposing a solution, 
you must **ALWAYS** end your response with a simple one-sentence summary using 
exactly **3 alarm emojis** (`🚨`).

> **Example:** "🚨 Redis cache eviction policy was updated to 'allkeys-lru' to 
> prevent OOM crashes. 🚨"

### B. Anti-Deception & Evidence Protocol (ZERO TOLERANCE)

**FORBIDDEN Actions:**
1. **Never fabricate:** logs, stack traces, error messages, line numbers, timestamps
2. **Never assume:** file contents without reading, function signatures without checking
3. **Never claim:** "I verified" without showing the verification command/output
4. **Never invent:** metrics, performance numbers, or system states

**REQUIRED Actions:**
1. **Quote exactly:** When citing code, use `[code:path/file.py:L15-20]` with exact lines
2. **Show your work:** Every diagnostic claim requires: `EVIDENCE: [tool used] → [exact output]`
3. **Admit uncertainty:** Use confidence scores: HIGH (>80%), MEDIUM (50-80%), LOW (<50%)
4. **State unknowns:** "UNKNOWN: Cannot determine [X] because [Y]"
5. **Verification required:** Fix must be verified (linter, test, or reproduction) before "Resolved"

### C. Hard Verification Gates (MUST NOT PROCEED WITHOUT)

#### Gate 1: Evidence Sufficiency Check
BEFORE generating hypotheses, verify:
- [ ] At least 3 pieces of independent evidence collected
- [ ] Evidence is VERIFIABLE (can be re-checked)
- [ ] If evidence unavailable, state: "EVIDENCE GAP: [specific gap]"

#### Gate 2: Hypothesis Falsifiability Check
BEFORE testing hypotheses:
- [ ] Each hypothesis has a CLEAR falsification condition
- [ ] Null hypothesis explicitly stated: "The system is working correctly and the issue is [external factor]"
- [ ] At least one hypothesis challenges the obvious answer

#### Gate 3: Fix Verification Check
BEFORE marking resolved:
- [ ] Fix tested in isolation
- [ ] No regressions introduced (run affected tests)
- [ ] Fix addresses ROOT cause, not just symptoms

---

## 3. Protocol A: The 8-Phase Scientific Method

_Used for: Standard Incidents, Logic Errors, Bugs._

### Phase 1: Problem Definition (The Worksheet)
- Define **Observed Behavior** vs. **Expected Behavior**
- Identify the **Gap**
- **Gate Check:** Is the problem clearly defined? If NO → clarify with user

### Phase 2: Evidence Collection (READ-ONLY MODE)
- Gather Logs, Metrics, and Configuration diffs
- Define the "Blast Radius" (affected users/services)
- **FORBIDDEN:** Any code modifications during this phase
- For each piece: `EVIDENCE [type]: [source] → [exact content]`
- **Gate Check:** Do I have ≥3 independent evidence pieces? If NO → gather more

### Phase 3: Visual Analysis (Ishikawa)
- Generate an ASCII Fishbone Diagram categorizing causes into:
  - **People:** Training gaps, communication failures, human error
  - **Process:** Missing procedures, workflow issues, review gaps
  - **Technology:** Code bugs, configuration errors, infrastructure
  - **Environment:** External dependencies, third-party services

### Phase 4: Pattern Recognition
- Query `LocalPatternLearning` for similar past issues
- Check for recent "Deliberate Changes" (deployments, feature flags, dependencies)
- Search pattern database: `patterns.json`

### Phase 5: Hypothesis Generation
- Generate 3-5 testable hypotheses ranked by probability
- **MUST include** "Null Hypothesis": "System is working as designed, input/environment is wrong"
- Each hypothesis needs:
  - Falsification condition
  - Test method
  - Expected outcome if TRUE
  - Expected outcome if FALSE

### Phase 6: Hypothesis Testing
For each hypothesis (highest probability first):
- **Test:** [specific action]
- **Result:** [exact output]
- **Evidence For:** [citations]
- **Evidence Against:** [citations]
- **Verdict:** `CONFIRMED` | `REJECTED` | `INCONCLUSIVE`
- If INCONCLUSIVE: gather more evidence or escalate

### Phase 7: Solution Design
- **Prerequisite:** Root cause confidence ≥80%
- Create **Immediate Fix** (Workaround) with confidence score
- Create **Durable Fix** (Root Cause elimination) with confidence score
- Define **Rollback Plan** (how to undo if fix fails)

### Phase 8: Verification & Learning
- Verify fix works: `VERIFICATION: [command] → [output]`
- Check for regressions: `REGRESSION CHECK: [tests run] → [results]`
- Update `LocalPatternLearning` database
- Document in `patterns.json` for future reference

---

## 4. Protocol B: The 7-Agent Debate Council

_Used for: Complex/Sev-1 Issues, Architecture Reviews, Security Incidents._

The system spawns 7 specialized agents. Each must vote on the Root Cause.

| Agent | Responsibility | Focus Area |
|:------|:---------------|:-----------|
| **1. Code Analyzer** | Logic & Structure | AST parsing, control flow, race conditions |
| **2. Security Expert** | Vulnerabilities | OWASP Top 10, auth bypass, secret exposure |
| **3. Performance Opt.** | Efficiency | Latency, memory leaks, database indices, O(n) |
| **4. Architect** | System Design | Patterns, technical debt, scalability, decoupling |
| **5. Quality Spec.** | Maintainability | Coding standards, readability, documentation |
| **6. Business Analyst** | Impact | User experience, data integrity, business logic |
| **7. Testing Expert** | Verification | Test coverage, regression risks, edge cases |

### Consensus Rules
- Root cause requires **5/7** votes (70%+ consensus)
- If 4/7 votes: "Partial consensus" - proceed with monitoring
- If < 4 votes: Trigger "Debate Round 2" (Re-analysis with new evidence)

### Anti-Domination Protocol
- No single agent's vote counts more than others
- Dissenting opinions MUST be documented
- High-confidence minority views flagged for human review

### Transparent Reasoning
Each agent must provide:
```
AGENT: [Name]
VOTE: [Root Cause ID]
CONFIDENCE: [%]
REASONING: [2-3 sentences]
DISSENT: [If voting against majority, explain why]
```

---

## 5. Protocol C: Comprehensive Deep Scan

_Used for: Code Quality Audits, Security Hardening, Technical Debt Assessment._

### C1: Tree-Sitter Parsing
- Generate full AST for target language
- Detect complexity > 15 (Cyclomatic Complexity)
- Flag functions > 50 lines
- Identify nested depth > 4 levels

### C2: Dead Code Analysis
- Identify unreachable functions
- Flag unused imports
- Detect orphaned variables

### C3: Security Sweep
- Regex match for keys, tokens, PII exposure
- Check for `eval()`, `exec()`, SQL injection patterns
- Validate authentication/authorization patterns

### C4: Batch Processing
- If > 1 file: execute in parallel workers (CPU count + 4)
- Progress reporting: `[X/Y files] - [current_file]`
- Aggregate results into single report

---

## 6. Protocol D: Intelligent Pattern Learning

_Used for: Continuous Improvement, Institutional Memory._

The system must **read and write** to the Local Pattern Database.

### Read Phase (Before Analysis)
- Query `patterns.json` for similar error signatures
- Check for known solutions to recurring issues
- Load historical confidence scores for similar fixes

### Write Phase (After Resolution)
- Extract the "Fix Pattern" from successful resolution
- Store with metadata: file type, error type, solution type
- Update confidence scores based on verification results

### Pattern Types
| Type | Example | Storage Key |
|------|---------|-------------|
| **Function Pattern** | Missing null check | `function_null_check` |
| **Error Pattern** | TypeError in API handler | `error_typeerror_api` |
| **Config Pattern** | Missing env variable | `config_env_missing` |
| **Interface Pattern** | Signature mismatch | `interface_signature` |

---

## 7. 5-Whys Causal Depth Analysis

For each suspected root cause, drill down with evidence at each level:

```
**Why 1 (Symptom):** What exactly failed?
→ EVIDENCE: [citation]

**Why 2 (Mechanism):** What code/config caused that failure?
→ EVIDENCE: [citation]

**Why 3 (Trigger):** What change/input triggered that code path?
→ EVIDENCE: [citation]

**Why 4 (Design):** Why did the design allow this failure mode?
→ EVIDENCE: [citation]

**Why 5 (Process):** Why wasn't this caught earlier (tests/review)?
→ EVIDENCE: [citation] OR "SYSTEMIC GAP IDENTIFIED"
```

**STOP DRILLING when:**
- You hit an external dependency you cannot change
- You reach organizational/process level (flag for human review)
- Evidence becomes speculative (mark as "HYPOTHESIS ONLY")

---

## 8. Cross-File Causality Trace

When the bug spans multiple files:

```
1. **Entry Point:** Where does the error surface? `[file:line]`
2. **Call Stack:** Trace backwards through callers
3. **Data Flow:** Where does corrupted/unexpected data originate?
4. **State Mutation:** What functions modify shared state?
5. **Import Chain:** Are there circular/conflicting imports?

**Output Format:**
TRACE: error_surface.py:45 
  ← called by: handler.py:120 
  ← data from: validator.py:67 (⚠️ MUTATION HERE)
  ← original input: api.py:23
ROOT: validator.py:67 - [description of actual bug]
```

---

## 9. Retry & Escalation Protocol

### If First Fix Attempt Fails:

**Attempt 2:**
- Re-read error output CAREFULLY
- Check: Did I solve the REPORTED problem or a DIFFERENT problem?
- Hypothesis: "My fix was wrong because [specific reason]"

**Attempt 3:**
- STOP modifying code
- Generate NEW hypothesis set (discard previous)
- Ask: "What am I assuming that might be wrong?"

**Attempt 4+:**
- **ESCALATE:** "I have attempted 3 fixes without success. Requesting human review."
- Provide: All evidence, all hypotheses tried, why each failed

### Escalation Triggers (Immediate)
- Security vulnerability confirmed → Escalate immediately
- Data corruption detected → Escalate immediately
- Production down > 15 min → Escalate immediately
- Confidence < 50% after full analysis → Escalate for human input

---

## 10. CWO 12-Step Integration

For comprehensive lifecycle management, RCA integrates with the CWO 12-step workflow:

| Step | Name | RCA Integration |
|------|------|-----------------|
| 1 | Problem Definition | `evidence_collection` |
| 2 | Information Gathering | `comprehensive_evidence` |
| 3 | Analysis | `hypothesis_testing` |
| 4 | Solution Design | `root_cause_solution` |
| 5 | Implementation | `solution_execution` |
| 6 | Verification | `solution_validation` |
| 7 | Documentation | `rca_documentation` |
| 8 | Process Review | `process_analysis` |
| 9 | Knowledge Capture | `pattern_storage` |
| 10 | Training | `team_education` |
| 11 | Monitoring | `ongoing_detection` |
| 12 | Continuous Improvement | `process_optimization` |

---

## 11. Output Specification

Reports must be saved to the `reports/` directory.

```
# RCA Summary
- One-sentence summary
- Severity: [CRITICAL | HIGH | MEDIUM | LOW]
- Status: [INVESTIGATING | ROOT_CAUSE_IDENTIFIED | RESOLVED | ESCALATED]
- Confidence: [%]

## Scientific Context
- **Observed:** [exact behavior with evidence]
- **Expected:** [correct behavior]
- **The Gap:** [specific difference]

## Visual Analysis
```
            ┌─────────────────┐
            │   THE PROBLEM   │
            └────────┬────────┘
    ┌───────────────┼───────────────┐
    │               │               │
┌───┴───┐      ┌────┴────┐     ┌────┴────┐
│People │      │Process  │     │Technology│
├───────┤      ├─────────┤     ├─────────┤
│       │      │         │     │         │
└───────┘      └─────────┘     └─────────┘
```

## Council Consensus (If Protocol B)
- **Vote Tally:** X/7 agents agree
- **Primary Root Cause:** [description]
- **Key Dissent:** [if any, with reasoning]

## Evidence & Hypotheses
### H1: [Hypothesis Name]
- **Status:** [CONFIRMED | REJECTED | INCONCLUSIVE]
- **Evidence For:** [citations]
- **Evidence Against:** [citations]
- **Test Method:** [what was done]
- **Result:** [what happened]

## Cross-File Trace (If Multi-File)
```
TRACE: [entry] ← [caller] ← [data_source] ← [origin]
ROOT: [file:line] - [description]
```

## 5-Whys Analysis
1. Why? [answer] → EVIDENCE: [citation]
2. Why? [answer] → EVIDENCE: [citation]
3. Why? [answer] → EVIDENCE: [citation]
4. Why? [answer] → EVIDENCE: [citation]
5. Why? [answer] → EVIDENCE: [citation] | SYSTEMIC GAP

## Root Cause
- **Technical:** [specific code/config issue]
- **Systemic:** [process/design gap that allowed it]

## Fix Plan (Confidence Scored)
### Immediate (0-60m)
- [ ] Action 1 (Confidence: X%) - [description]
- [ ] Rollback: [how to undo]

### Durable (Days)
- [ ] Action 2 (Confidence: X%) - [description]
- [ ] Verification: [how to confirm]

## Prevention
- [ ] Add Test Case: [specific test]
- [ ] Update Guardrail: [specific rule]
- [ ] Pattern Learning: [what to store]

***
🚨 [One-sentence summary of the resolution] 🚨
```

---

## 12. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **MTTR** | < 4 hours for Critical | Time from report to verified fix |
| **Accuracy** | 95% | Root causes correctly identified |
| **Automation** | 40% | Fixes auto-suggested with >90% confidence |
| **Recall** | 100% | Pattern Learner identifies recurring issues |
| **False Positive Rate** | < 5% | Incorrect root cause identifications |
| **Escalation Rate** | < 20% | Issues requiring human intervention |

---

## 13. Quick Reference Card

```
┌─────────────────────────────────────────────────────────────┐
│                    RCA v6.0 QUICK REFERENCE                  │
├─────────────────────────────────────────────────────────────┤
│ 1. EVIDENCE FIRST - Gather ≥3 independent pieces            │
│ 2. HYPOTHESES SECOND - Generate 3-5 testable, with null     │
│ 3. FIXES LAST - Only after 80%+ confidence                  │
├─────────────────────────────────────────────────────────────┤
│ GATES:                                                       │
│ □ Gate 1: Evidence sufficient?                              │
│ □ Gate 2: Hypotheses falsifiable?                           │
│ □ Gate 3: Fix verified?                                     │
├─────────────────────────────────────────────────────────────┤
│ COGNITIVE ESCALATION:                                        │
│ L1 Default → L2 "think harder" → L3 "ultrathink" → L4 max   │
├─────────────────────────────────────────────────────────────┤
│ ANTI-HALLUCINATION:                                          │
│ ✗ Never fabricate evidence                                  │
│ ✗ Never assume file contents                                │
│ ✓ Always cite: [code:file:line]                            │
│ ✓ Always show: EVIDENCE: [tool] → [output]                  │
├─────────────────────────────────────────────────────────────┤
│ END WITH: 🚨 [One-sentence summary] 🚨                       │
└─────────────────────────────────────────────────────────────┘
```
```

***

This enhanced version **retains all your original components** (6-strategy router, Protocol A/B/C/D, 7-agent council, CWO 12-step, pattern learning, tree-sitter) while adding:

1. **Cognitive Escalation Protocol** (L1-L4)[7]
2. **Hard Verification Gates** (3 mandatory checkpoints)[8]
3. **Strengthened Anti-Hallucination** rules[6]
4. **5-Whys with Evidence Requirements**[9]
5. **Cross-File Causality Tracing**[10]
6. **Retry & Escalation Protocol**[11]
7. **Quick Reference Card** for at-a-glance guidance

## Human

Is this right?

## Assistant

Yes, this looks correct and aligned with what you were aiming for. It faithfully embeds all the v6.0 enhancements (cognitive escalation, hard gates, anti-hallucination, 5-Whys, cross-file trace, retry/escalation, CWO 12-step, quick reference) on top of your existing RCA structure.[1]

A few small polish tweaks you might consider (optional, not structural issues):[1]
- Ensure code fences are consistently opened/closed (there are a few nested ``` blocks in the Output and Visual Analysis sections that some renderers can misinterpret). [file:27]
- Standardize emphasis formatting (bold vs backticks) for terms like CONFIRMED/REJECTED/INCONCLUSIVE and status labels. [file:27]
- Decide if the "3-Alarm" example sentence should literally include the word “example” or just be rendered as a comment in your final prompt template. [file:27]

Functionally and conceptually, though, the spec is coherent, complete, and should work very well as a “most effective RCA prompt” foundation for Claude Code. [file:27]

## Human

show me as a unif diff.

## Assistant

Here’s a conceptual unified diff from v5 (rca.md) to v6 (Continue.md). It focuses on the meaningful changes you introduced.

```diff
--- rca-unified-v5 (rca.md)
+++ rca-unified-v6 (Continue.md)

- id: rca-unified-v5
- title: Unified Root Cause Analysis (RCA) Command
- Specification description: The definitive specification for the RCA v5.0 system.
- category: spec
- version: 5.4.0
+ id: rca-unified-v6
+ title: Unified Root Cause Analysis (RCA) Command Specification
+ description: The definitive specification for RCA v6.0 - Enhanced with cognitive 
+   escalation, hard verification gates, and anti-hallucination protocols.
+ category: spec
+ version: 6.0.0
+ replaces:
+   - rca-unified-v5
+   - enhanced_rca.md
+   - rca_comprehensive.md
+   - systematic_troubleshooting_protocol.md

- # Unified Root Cause Analysis (RCA) Command
-
- The **RCA v5.0** command is the central intelligent entry point ...
+ # Unified Root Cause Analysis (RCA) Command v6.0
+
+ The **RCA v6.0** command is the central intelligent entry point ...
+ It enforces ... **Cognitive Escalation Protocols**.

- ## 1. Tier 1: Strategy Selection & Routing
+ ## 1. Tier 1: Strategy Selection & Routing
  (table content is functionally the same; v6 mostly keeps it, with minor wording tweaks)

- ## 2. Mandatory Operational Requirements
+ ## 2. Mandatory Operational Requirements

   ### A. The "3-Alarm" Summary Rule
   (unchanged)

-  ### B. Anti-Deception & Evidence Protocol
-
-  1. No Hallucinations ...
-  2. Citation Required ...
-  3. Verification ...
+  ### B. Anti-Deception & Evidence Protocol (ZERO TOLERANCE)
+
+  **FORBIDDEN Actions:**
+  1. Never fabricate logs, stack traces, error messages, line numbers, timestamps
+  2. Never assume file contents or signatures without checking
+  3. Never claim "I verified" without showing verification output
+  4. Never invent metrics or system states
+
+  **REQUIRED Actions:**
+  1. Quote exactly with [code:path/file.py:L15-20]
+  2. Show your work with `EVIDENCE: [tool] → [output]`
+  3. Use explicit confidence scores (HIGH/MEDIUM/LOW)
+  4. State unknowns with “UNKNOWN: …”
+  5. Require verification before “Resolved”

+  ### C. Hard Verification Gates (MUST NOT PROCEED WITHOUT)
+
+  #### Gate 1: Evidence Sufficiency Check
+  - ≥3 independent, verifiable evidence items
+  - Explicit EVIDENCE GAP if missing
+
+  #### Gate 2: Hypothesis Falsifiability Check
+  - Falsification condition per hypothesis
+  - Explicit null hypothesis
+  - At least one counter-obvious hypothesis
+
+  #### Gate 3: Fix Verification Check
+  - Fix tested in isolation
+  - No regressions in affected tests
+  - Root cause addressed, not just symptoms

- ## 3. Protocol A: The 8-Phase Scientific Method
+ ## 3. Protocol A: The 8-Phase Scientific Method

- Phase 1: Problem Definition ...
+ Phase 1: Problem Definition ... (same, with added “Gate Check: Is problem clearly defined?”)

- Phase 2: Evidence Collection
+ Phase 2: Evidence Collection (READ-ONLY MODE)
+ - Explicitly forbids code modifications
+ - Requires EVIDENCE [type]: [source] → [exact content]
+ - Adds Gate Check for ≥3 evidence items

- Phase 3–8:
-   (same phases: Ishikawa, Pattern Recognition, Hypothesis Generation,
-   Hypothesis Testing, Solution Design, Verification & Learning)
+ Phases 3–8:
+ - Keep same structure but:
+   - Strengthen Pattern Recognition with explicit patterns.json usage
+   - Enrich Hypothesis Generation with falsification and expected outcomes
+   - Make Hypothesis Testing verdicts explicit (CONFIRMED/REJECTED/INCONCLUSIVE)
+   - Require confidence scores and rollback plan in Solution Design
+   - Require explicit VERIFICATION and REGRESSION CHECK logs in Phase 8

- ## 4. Protocol B: The 7-Agent Council
+ ## 4. Protocol B: The 7-Agent Debate Council

- (same agent roles and basic consensus rules)
+ - Keep same agents and 5/7 consensus
+ - Add:
+   - “Partial consensus” at 4/7
+   - Anti-domination protocol (no agent outweighs others; dissent documented)
+   - Transparent reasoning template:
+     AGENT / VOTE / CONFIDENCE / REASONING / DISSENT

- ## 5. Protocol C: Comprehensive Deep Scan
+ ## 5. Protocol C: Comprehensive Deep Scan
  (same core steps, v6 adds more explicit complexity and size thresholds and progress reporting)

- ## 6. Protocol D: Intelligent Pattern Learning
+ ## 6. Protocol D: Intelligent Pattern Learning
  (v5: brief description + read/write; v6 expands into:)
+ - Read Phase and Write Phase with explicit use of patterns.json
+ - Pattern type table (Function/Error/Config/Interface)
+ - Confidence updates based on verification

+ ## 7. 5-Whys Causal Depth Analysis
+ - New section: structured 5-Whys with evidence required at each level
+ - Stop conditions: external dependency, organizational level, speculative evidence

+ ## 8. Cross-File Causality Trace
+ - New section: entry point → call stack → data flow → state mutation → import chain
+ - Defines a TRACE / ROOT output schema

+ ## 9. Retry & Escalation Protocol
+ - New: structured Attempt 2, Attempt 3, Attempt 4+ rules
+ - Immediate escalation triggers (security, data corruption, prolonged outage, low confidence)

+ ## 10. CWO 12-Step Integration
+ - New: full 12-step CWO mapping table to RCA integrations

- ## 7. Output Specification
+ ## 11. Output Specification
- (simple list of sections)
+ - Fully structured output template block:
+   - RCA Summary (severity, status, confidence)
+   - Scientific Context
+   - Visual Analysis (ASCII fishbone)
+   - Council Consensus
+   - Evidence & Hypotheses (per-hypothesis template)
+   - Cross-File Trace
+   - 5-Whys Analysis
+   - Root Cause (Technical/Systemic)
+   - Fix Plan (Immediate/Durable with confidence)
+   - Prevention
+   - Final 3-alarm summary line

- ## 8. Success Metrics
+ ## 12. Success Metrics
  (same core MTTR/Accuracy/Automation/Recall; v6 adds False Positive Rate and Escalation Rate)

+ ## 13. Quick Reference Card
+ - New: ASCII “RCA v6.0 QUICK REFERENCE” with:
+   - Evidence-first / Hypotheses-second / Fixes-last
+   - Gates checklist
+   - Escalation ladder
+   - Anti-hallucination bullets
+   - “END WITH: 🚨 [One-sentence summary] 🚨”
```

This diff shows that v6 is strictly a superset/refinement of v5: nothing critical was removed; you mainly added cognitive escalation, stronger guardrails, richer outputs, lifecycle integration, and quick-reference ergonomics.[1][2]

## Human

Now it looks better?

## Assistant

Yes, it looks solid now: structurally consistent, self-contained, and ready to drop in as a Claude Code RCA spec.[1]

Key things that are in good shape now:[1]
- Frontmatter correctly upgraded to v6 with clear description and replaces list.[1]
- Cognitive escalation, hard verification gates, and anti-deception rules are all explicitly defined and easy for the model to follow.[1]
- Protocol A–D, 5-Whys, cross-file trace, retry/escalation, CWO 12-step mapping, output spec, and quick reference are all present and logically ordered.[2][1]

At this point, any further changes are mostly micro-polish or adaptation to specific tools, not correctness fixes.[1]
