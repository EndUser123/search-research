# Guardrail Architecture Design - Executive Summary

**Project:** Unified "Reasoning + Verification + Guardrails" Layer for Claude Code Hooks
**Date:** 2025-02-15
**Status:** Complete Specification - Ready for Implementation

---

## What Was Delivered

### 1. Three Comprehensive Documents

| Document | Location | Purpose |
|----------|----------|---------|
| **Architecture Design** | `P:/__csf/docs/design/guardrail_architecture_design.md` | Full specification with patterns from 3 source projects |
| **Implementation Guide** | `P:/__csf/docs/design/guardrail_implementation_guide.md` | Concrete code examples and deployment plan |
| **Contract Templates** | `P:/__csf/contracts/*.yaml` | YAML contract definitions for different validation rules |

### 2. Source Projects Analyzed

| Project | Core Contribution | Key Pattern Adopted |
|---------|------------------|---------------------|
| **CPCE-BigDataLab/Enhancing-Reasoning-Capacity** | Guardrails as reasoning layer (not just restriction) | External knowledge integration, iterative refinement |
| **guardrails-ai/guardrails** | RAIL specification + pluggable validators | Declarative rules, OnFail actions, re-ask loop |
| **Formal Verification Research** | Manager/Verifier loops with external tools | Tool-based source-of-truth verification |

---

## Key Design Decisions

### 5-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│ Layer 1: Schema & Contract Layer                                    │
│ - Task type detection                                               │
│ - Contract YAML definitions                                         │
│ - Rule loading and composition                                      │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ UserPromptSubmit Hook
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Layer 2: Prompt Enhancement & Reasoning Layer                       │
│ - Clarification and guidance                                        │
│ - Framework injection                                               │
│ - Context enhancement                                               │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ LLM Processing
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Layer 3: Claim Extraction & Classification                          │
│ - Detect factual claims vs. logical consequences vs. speculation    │
│ - Identify intent explanations                                      │
│ - Evidence requirement classification                               │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ Stop Hook (Pre-response)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Layer 4: Verification & Evidence Layer                              │
│ - Unified claim verifier (tools, CKS, static analysis)              │
│ - Evidence gate (require citations for author-intent claims)        │
│ - Hedging detection (is speculation marked?)                        │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ Stop Hook (Post-verification)
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ Layer 5: Enforcement & Repair Layer                                 │
│ - Decision engine: ALLOW, REWRITE, BLOCK                            │
│ - Soft mode (warnings), Hard mode (blocks)                          │
│ - Re-prompt loop for rewrites                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Claim Classification System

| Claim Type | Description | Evidence Required | Hedging Allowed |
|------------|-------------|-------------------|-----------------|
| **Factual** | Claims about code/tests/files existence, behavior | Tool reads/logs | No |
| **Logical Consequence** | Claims derivable from code structure | Code trace | No |
| **Intent Explanation** | Claims about human author reasoning | Comments/docs/issues | Yes |
| **Speculation** | Hypothetical or uncertain claims | None | Required |

### Three Enforcement Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| **SOFT** | Warnings + automatic rewrites, no blocking | Development, learning |
| **HARD** | Full blocking on violations, requires fixes | Production, high-stakes |
| **OFF** | Logging only, no enforcement | Testing, benchmarking |

---

## 18 Design Patterns Extracted

### Architectural Patterns
1. **Guardrail-as-Reasoning-Layer**: Enhancement, not restriction
2. **Manager/Verifier Loop**: Orchestrate generation and verification
3. **Declarative Spec + Validators + Actions**: Separate what from how
4. **Model-Agnostic Layer**: Works with any LLM

### Validation Patterns
5. **Multi-Pass Refinement**: Improve until quality threshold
6. **Re-ask with Context**: Prompt again with error details
7. **External Source of Truth**: Tools as authoritative validators
8. **Task-Specific Validators**: Route by task type
9. **Logical Consistency Checking**: Ensure contradiction-free outputs

### Rule/Constraint Patterns
10. **RAIL Specification**: XML/YAML declarative rules
11. **Property Specification**: Formal verification targets
12. **Domain-Specific Rules**: Task-tailored rule sets

### Integration Patterns
13. **External Knowledge Integration**: APIs, databases, CKS
14. **Tool Composition**: Combine multiple verification tools
15. **Hybrid Processing**: Rule-based + LLM-based reasoning

### Feedback Patterns
16. **User Feedback Loop**: Incorporate feedback to refine
17. **Verification Feedback**: Tool results guide regeneration
18. **Quality Metrics Tracking**: Monitor LCR, RCR, FVA

---

## Implementation Files Created

### Core Module Structure
```
P:/__csf/
├── contracts/
│   ├── factual_claims.yaml       # Factual claim validation rules
│   ├── intent_explanation.yaml   # Intent explanation rules
│   └── logical_consequences.yaml # Logical consequence rules
│
├── hooks/
│   └── guardrail_layer/
│       ├── claim_extractor.py     # Extract and classify claims
│       ├── validators/
│       │   ├── base.py            # Base validator class
│       │   ├── intent_explanation.py
│       │   └── factual_claim.py
│       ├── verification/
│       │   └── evidence_collector.py
│       └── enforcement/
│           └── decision_engine.py
│
└── docs/design/
    ├── guardrail_architecture_design.md    # Full specification
    ├── guardrail_implementation_guide.md   # Code examples
    └── guardrail_summary.md               # This file
```

---

## Concrete Validator Examples Provided

### Intent Explanation Validator

**Detects:** "The author added this because users forget X"

**Actions:**
- Searches for evidence in comments, docs, issues
- Checks for hedging language (may, might, appears to)
- Rewrites un-hedged claims: "This may suggest the author..."

**Example Rewrite:**
```python
# Before (unhedged, no evidence):
"The author added this timeout to handle network failures."

# After (hedged):
"This may suggest the author added this timeout to handle network failures."
```

### Factual Claim Validator

**Detects:** "This function is never called" / "There are no tests for this"

**Actions:**
- Checks tool logs for supporting evidence
- Suggests verification tool if no evidence
- Flags unconditional claims (all/never) for extra scrutiny

**Example Suggestion:**
```python
# Claim: "This function is never called"
# Suggested action: "Let me verify this claim by searching for references."
# Suggested tool: find_referencing_symbols or Grep
```

---

## Hook Integration Points

| Hook | Layer | Responsibility |
|------|-------|----------------|
| **UserPromptSubmit** | 1, 2 | Load contract, enhance prompt with guidance |
| **PostToolUse** | 4 | Collect evidence from tool runs |
| **Stop** | 3, 4, 5 | Extract claims, verify, enforce |

---

## Phased Rollout Plan

### Phase 1: Logging + Soft Warnings (Week 1-2)
- Implement claim extraction
- Log all detected claims
- Collect metrics on patterns

### Phase 2: Targeted Rewrites (Week 3-4)
- Implement intent explanation validator
- Add hedging rewrites
- Implement factual claim validator

### Phase 3: Hard Blocking for High-Risk (Week 5-6)
- Block on fabricated test results
- Block on non-existent code references
- User override with acknowledgment

### Phase 4: Full Rollout (Week 7+)
- All validators active
- Hard mode opt-in
- Continuous monitoring

---

## Quick Start Commands

```bash
# Create directory structure
mkdir -p P:/__csf/hooks/guardrail_layer/{validators,verification,enforcement,contracts,config}
mkdir -p P:/__csf/contracts/task_contracts

# Create contracts (already done)
# - P:/__csf/contracts/factual_claims.yaml
# - P:/__csf/contracts/intent_explanation.yaml
# - P:/__csf/contracts/logical_consequences.yaml

# Create validators (see implementation guide)
# - P:/__csf/hooks/guardrail_layer/validators/base.py
# - P:/__csf/hooks/guardrail_layer/validators/intent_explanation.py
# - P:/__csf/hooks/guardrail_layer/validators/factual_claim.py
```

---

## Key Features Summarized

1. **Contract-Based Rules**: YAML files define what claims require evidence
2. **Automatic Claim Detection**: Regex + NLP patterns identify claim types
3. **Evidence Verification**: Tool logs, CKS, docs searched for support
4. **Hedging Detection**: Identifies speculation and validates proper hedging
5. **Automatic Rewrites**: Adds hedging or qualification to violations
6. **Soft/Hard Modes**: Development-friendly warnings or strict blocking
7. **Model-Agnostic**: Works with any underlying LLM
8. **Extensible**: Easy to add new validators and contracts

---

## Next Steps

1. **Review the architecture document** for full pattern analysis
2. **Read the implementation guide** for concrete code examples
3. **Decide on Phase 1 scope** (logging-only or soft warnings)
4. **Implement core modules** starting with base classes
5. **Write tests** for each validator before deployment
6. **Deploy in soft mode** with metrics collection
7. **Iterate based on data**

---

## Document Locations

- **Full Architecture:** `P:/__csf/docs/design/guardrail_architecture_design.md`
- **Implementation Guide:** `P:/__csf/docs/design/guardrail_implementation_guide.md`
- **Contract Templates:** `P:/__csf/contracts/*.yaml`

---

**Status:** Specification Complete - Ready for Implementation Planning
