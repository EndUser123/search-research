# Guardrail Architecture Design for Claude Code Hooks
## Unified "Reasoning + Verification + Guardrails" Layer

**Design Document Version:** 1.0
**Date:** 2025-02-15
**Status:** Draft Specification

---

## Executive Summary

This document synthesizes architectural patterns from three leading guardrail/reasoning projects into a unified design for Claude Code hooks. The design treats "guardrails as a reasoning layer" - not merely blocking outputs, but enhancing them through validation, verification, and iterative refinement.

### Source Projects Analyzed

| Project | Core Focus | Key Contribution |
|---------|-----------|------------------|
| **CPCE-BigDataLab/Enhancing-Reasoning-Capacity** | Guardrails as Reasoning Layer | Conceptual framework for guardrails that enhance rather than restrict |
| **guardrails-ai/guardrails** | RAIL Specification + Validators | Declarative rule language (XML-based) with pluggable validators |
| **Formal Verification Research** | Manager/Verifier Loops | External tool integration for formal verification of LLM outputs |

---

# Part 1: Deep Feature Extraction Per Repo

## 1.1 CPCE-BigDataLab - Guardrails as a Reasoning Layer

### Core Problem Solved
Traditional guardrails constrain LLM outputs for safety/compliance. This project reimagines guardrails as a **reasoning enhancement layer** that:
- Validates and refines outputs through logical frameworks
- Integrates external knowledge for factual accuracy
- Enables iterative improvement without model retraining

### Architectural Components

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Reasoning Layer (Guardrails)                 │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────────────┐ │
│  │ Output        │  │ External      │  │ Iterative           │ │
│  │ Validation    │  │ Knowledge     │  │ Refinement          │ │
│  │               │  │ Integration   │  │                     │ │
│  └───────────────┘  └───────────────┘  └─────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       LLM Engine                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Features

| Feature | Description | Implementation Notes |
|---------|-------------|---------------------|
| **Output Validation** | Analyzes LLM outputs for logical consistency and factual accuracy | Multi-pass validation with external cross-checks |
| **External Knowledge Integration** | Uses APIs, knowledge graphs, databases | Modular integration points for domain-specific knowledge |
| **Rule-Based Reasoning** | Applies domain-specific rules | Structured thinking enforcement |
| **Iterative Refinement** | Multiple validation passes until quality standards met | Configurable refinement loops |
| **Context Persistence** | Maintains context across multi-turn interactions | Essential for coherent long conversations |
| **Scenario Simulation** | Enables hypothetical reasoning | Combines LLM outputs with logical checks |

### Patterns for Cost/Latency Management

- **Multi-Pass Refinement**: Only refine when confidence is below threshold
- **Task-Specific Modules**: Route to appropriate validators based on task type
- **Hybrid Processing**: Combine rule-based (fast) with LLM-based (slow) reasoning selectively
- **Performance Monitoring**: Track accuracy vs. latency trade-offs

### Mini-Spec (12 Key Points)

1. **Separation Pattern**: Reasoning layer is model-agnostic; sits between user and LLM
2. **Validation Pipeline**: Input Analysis → LLM Query → Logical Validation → Iterative Refinement → Final Output
3. **External Sources**: Pluggable integration with APIs, knowledge graphs, databases
4. **Rule Engine**: Domain-specific rules enforced alongside statistical LLM outputs
5. **Context Management**: Persistent context across multi-turn interactions
6. **Metrics**: Logical Consistency Rate (LCR), Reasoning Completion Rate (RCR), Processing Time (PT)
7. **Iterative Loop**: Configurable max passes with quality thresholds
8. **Task Modules**: Specialized reasoning for different task types (math, ethical decision-making)
9. **Future-Proof Design**: Layer can adapt to new LLMs without core changes
10. **User Feedback Loop**: Integrates feedback to refine reasoning accuracy
11. **Evaluation Framework**: A/B testing against baseline LLMs, stress testing
12. **Transparency**: Explainable reasoning steps for user trust

---

## 1.2 guardrails-ai/guardrails

### Core Problem Solved
Provides a Python framework for:
1. **Input/Output Guards** that detect, quantify, and mitigate specific risks
2. **Structured Data Generation** from LLMs (JSON/XML/etc with guaranteed schema)

### Architectural Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        Guardrails Hub                           │
│                  (Pre-built Validator Registry)                 │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          Guard                                  │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────────────┐ │
│  │ Validators    │  │ Actions       │  │ Re-ask Loop         │ │
│  │ (pluggable)   │  │ (on fail)     │  │ (repair mechanism)  │ │
│  └───────────────┘  └───────────────┘  └─────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     RAIL Specification                          │
│                 (XML-based Declarative Rules)                   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Features

| Feature | Description |
|---------|-------------|
| **RAIL Language** | XML dialect for defining output structure, validation rules, corrective actions |
| **Validators** | Pluggable validation logic with on_fail actions (exception, fix, filter, reframe) |
| **Structured Output** | Ensures LLM outputs match Pydantic models or JSON schemas |
| **Re-ask Mechanism** | Automatically prompts LLM again when validation fails |
| **Guardrails Hub** | Pre-built validators for common risks (toxic language, competitor check, PII detection) |

### OnFail Actions (Corrective Actions)

```python
class OnFailAction:
    EXCEPTION = "exception"     # Raise validation error
    FIX = "fix"                 # Attempt to fix the output
    FILTER = "filter"           # Remove invalid portions
    REFRAIN = "refrain"         # Provide safe fallback response
    REASK = "reask"             # Ask LLM to try again
```

### RAIL Specification Structure

```xml
<rail version="0.1">
  <output>
    <object name="result" type="object">
      <string name="explanation" format="1-3 sentences" />
      <integer name="confidence" min="0" max="100" />
    </object>
  </output>

  <prompt>
    Generate a structured response with explanation and confidence.
  </prompt>

  <validators>
    <validator ref="ValidPython" on-fail="fix" />
    <validator ref="CompetitorCheck" competitors="Apple,Microsoft" on-fail="exception" />
  </validators>
</rail>
```

### Mini-Spec (14 Key Points)

1. **RAIL Specification**: XML-based declarative language for rules
2. **Validator Pattern**: Base class for pluggable validators with validate() method
3. **Guard Composition**: Multiple validators combined into a single Guard
4. **OnFail Actions**: EXCEPTION, FIX, FILTER, REFRAIN, REASK for flexible response to violations
5. **Pydantic Integration**: Structured output via BaseModel classes
6. **Function Calling**: For LLMs that support it (OpenAI)
7. **Prompt Optimization**: Schema added to prompt for non-function-calling LLMs
8. **Guardrails Hub**: Registry of pre-built validators
9. **Re-ask Loop**: Automatic re-prompting with error context on validation failure
10. **Server Mode**: Can run as standalone service (Flask/FastAPI)
11. **Multi-language**: Python and JavaScript support
12. **Telemetry**: Performance tracking for validators
13. **Custom Validators**: Template for creating new validators
14. **Streaming Support**: Validates streaming outputs

### File References
- `guardrails/validator_base.py`: Base validator class
- `guardrails/guard.py`: Main Guard orchestration
- `guardrails/validators/`: Built-in validator implementations
- `guardrails/actions/`: OnFail action implementations

---

## 1.3 Formal Verification Research (Manager/Verifier Pattern)

### Core Problem Solved
Integrates formal verification tools (Infer, KLEE, Z3) with LLM-generated code to:
- Verify correctness properties mathematically
- Provide source-of-truth validation beyond heuristic checks
- Enable predictable verification systems

### Architectural Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        Manager                                  │
│                  (Orchestration Layer)                          │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────────────┐ │
│  │ Code Gen      │  │ Compilation   │  │ Pipeline Control    │ │
│  │ (LLM)         │  │               │  │                     │ │
│  └───────────────┘  └───────────────┘  └─────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Verifier                                 │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────────────┐ │
│  │ Infer         │  │ KLEE          │  │ Z3/SMT Solvers      │ │
│  │ (static)      │  │ (symbolic)    │  │ (constraint)        │ │
│  └───────────────┘  └───────────────┘  └─────────────────────┘ │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Result Synthesis                            │
│              (Verification Report + Feedback)                   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Features

| Feature | Description |
|---------|-------------|
| **Manager/Verifier Loop** | Structured pipeline: CodeGen → Compilation → Verification → Feedback |
| **External Tools as Source of Truth** | Formal tools provide definitive correctness proofs |
| **Property Specification** | Mathematical properties to verify (e.g., "no null pointer dereference") |
| **Feedback to LLM** | Verification results guide re-generation |
| **4/δ Bound** | Predictable bounds on verification complexity |

### Mini-Spec (10 Key Points)

1. **Structured Pipeline**: CodeGen, Compilation, Verification, Result stages
2. **Multiple Verifiers**: Infer (static analysis), KLEE (symbolic execution), Z3 (SMT)
3. **Property Specification**: Formal properties expressed as verification targets
4. **Manager Orchestration**: Coordinates LLM and external tools
5. **Source of Truth**: External tools provide authoritative validation
6. **Feedback Loop**: Verification failures inform LLM re-generation
7. **Predictable Bounds**: 4/δ bound on verification complexity
8. **Repair Mechanism**: LLM can attempt fixes based on verification feedback
9. **Incremental Verification**: Re-verify only changed portions
10. **Error Localization**: Pinpoint specific code locations causing failures

---

# Part 2: Cross-Repo Comparison and Pattern Mining

## 2.1 Comparison Table

| Design Aspect | CPCE-BigDataLab | guardrails-ai/guardrails | Formal Verification |
|--------------|-----------------|-------------------------|---------------------|
| **Output Schema & Validation** | Logical consistency checks | RAIL XML + Pydantic schemas | Formal property verification |
| **External Tools** | APIs, knowledge graphs, databases | None (LLM-based validation) | Infer, KLEE, Z3 (formal tools) |
| **Repair Loop** | Iterative refinement with quality thresholds | Re-ask with error context | Manager-driven regeneration with feedback |
| **Rule Representation** | Domain-specific rules (code/config) | RAIL XML specification | Mathematical properties (SMT/logic) |
| **Cost Control** | Task-specific modules, hybrid processing | Validator composition | Incremental verification, 4/δ bound |
| **Reasoning Layer** | Explicit separate layer | Implicit in Guard validation | Verifier as reasoning layer |
| **Corrective Actions** | Refine output until quality met | OnFail actions (FIX, REASK, etc.) | Regenerate with feedback |
| **Evidence Requirements** | External knowledge cross-checks | Validator-defined | Formal proof from external tools |
| **Base LLM Separation** | Model-agnostic layer | Wraps any LLM | LLM generates, tools verify |
| **Validator Extensibility** | Module-based | Validator base class | Tool integration interface |

## 2.2 Design Patterns Distilled (18 Patterns)

### Architectural Patterns

1. **Guardrail-as-Reasoning-Layer**: Treat validation as enhancement, not restriction (CPCE)
2. **Manager/Verifier Loop**: Orchestrate between generation and external verification (Formal)
3. **Declarative Spec + Validators + Actions**: Separate what from how (RAIL/Guardrails)
4. **Model-Agnostic Layer**: Reasoning layer works with any underlying LLM (All three)

### Validation Patterns

5. **Multi-Pass Refinement**: Iteratively improve until quality threshold met (CPCE)
6. **Re-ask with Context**: On failure, prompt again with error details (Guardrails)
7. **External Source of Truth**: Use tools as authoritative validators (Formal)
8. **Task-Specific Validators**: Route to appropriate validators based on task type (CPCE, Guardrails)
9. **Logical Consistency Checking**: Ensure outputs are contradiction-free (CPCE)

### Rule/Constraint Patterns

10. **RAIL Specification**: XML-based declarative rule language (Guardrails)
11. **Property Specification**: Formal properties as verification targets (Formal)
12. **Domain-Specific Rules**: Task-tailored rule sets (CPCE)

### Integration Patterns

13. **External Knowledge Integration**: APIs, databases, knowledge graphs (CPCE)
14. **Tool Composition**: Combine multiple verification tools (Formal)
15. **Hybrid Processing**: Rule-based + LLM-based reasoning (CPCE)

### Feedback Patterns

16. **User Feedback Loop**: Incorporate feedback to refine reasoning (CPCE)
17. **Verification Feedback**: Tool results guide regeneration (Formal)
18. **Quality Metrics Tracking**: Monitor LCR, RCR, FVA, etc. (CPCE)

---

# Part 3: Claude Code Hook System Architecture

## 3.1 Layer Architecture (5 Layers)

```
┌─────────────────────────────────────────────────────────────────────┐
│ Layer 1: Schema & Contract Layer                                    │
│ - Task type detection                                               │
│ - Contract YAML definitions (what claims require evidence)          │
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

## 3.2 Layer Details

### Layer 1: Schema & Contract Layer
**Responsibilities:**
- Detect task type (code change, documentation, investigation, design)
- Load applicable contracts for task type
- Compose validators based on contract

**Inputs:**
- User prompt
- Existing contract YAML files
- Task type classifier output

**Outputs:**
- Active contract set
- Validator pipeline configuration
- Evidence requirements

**Example Contract YAML:**

```yaml
# contracts/code_explanation.yaml
name: "Code Explanation Contract"
version: "1.0"
applies_to:
  task_types: [code_read, code_explanation, refactor_design]

validators:
  - id: factual_claims
    class: FactualClaimValidator
    config:
      require_tool_reads: true
      allowed_sources: [Read, Grep, Glob, find_symbol]

  - id: intent_explanation
    class: IntentExplanationValidator
    config:
      require_evidence: true
      allow_hedging: true
      evidence_sources: [comments, docs, issues]
      block_if_no_evidence: false  # Soft mode

  - id: logical_consequences
    class: LogicalConsequenceValidator
    config:
      allow_inference: true
      require_code_trace: true

on_fail:
  severity: warning  # warning | error | block
  action: rewrite    # rewrite | block | allow
```

**Pattern Sources:**
- RAIL specification (Guardrails)
- Task-specific modules (CPCE)

### Layer 2: Prompt Enhancement & Reasoning Layer
**Responsibilities:**
- Enhance prompt with clarifications
- Inject reasoning frameworks
- Add context from knowledge sources

**Inputs:**
- Original user prompt
- Context from CKS/docs
- Applicable frameworks

**Outputs:**
- Enhanced prompt for LLM
- Active reasoning framework

**Example Enhancement:**

```yaml
# prompt_enhancements/code_review.yaml
framework: "Code Review Protocol"
context_sources:
  - cks: "code review patterns"
  - docs: "CONTRIBUTING.md"
guidance:
  - "Distinguish factual claims from logical consequences"
  - "Cite evidence for author-intent explanations"
  - "Use hedging language for speculation"
```

**Pattern Sources:**
- Prompt optimization (Guardrails)
- Reasoning layer (CPCE)
- Input analysis (CPCE)

### Layer 3: Claim Extraction & Classification
**Responsibilities:**
- Extract claims from LLM response
- Classify claim type (factual, logical, speculative)
- Identify intent explanations
- Flag potential issues

**Inputs:**
- LLM response text
- Tool logs from session
- Active contract

**Outputs:**
- Claim objects with classifications
- Issue flags
- Evidence requirements

**Data Structure:**

```python
@dataclass
class Claim:
    text: str
    claim_type: ClaimType  # FACTUAL | LOGICAL | SPECULATIVE | INTENT
    span: Tuple[int, int]  # Location in response
    confidence: float

    @dataclass
    class EvidenceRequirement:
        requires_tool_evidence: bool
        requires_citation: bool
        allows_hedging: bool
        severity: ViolationSeverity

@dataclass
class IntentExplanation(Claim):
    claimed_intent: str  # "the author added this because..."
    has_evidence: bool
    is_hedged: bool
    evidence_sources: List[str]  # Where to look for evidence
```

**Pattern Sources:**
- Output validation (CPCE)
- Validator pattern (Guardrails)

### Layer 4: Verification & Evidence Layer
**Responsibilities:**
- Verify factual claims against tool logs
- Check for citations in intent explanations
- Validate hedging on speculation
- Cross-reference with CKS/docs

**Inputs:**
- Claim objects from Layer 3
- Session tool logs
- CKS queries
- Static analysis results

**Outputs:**
- Verification results per claim
- Evidence citations
- Violation report

**Example Validator Logic:**

```python
class IntentExplanationValidator:
    def validate(self, claim: IntentExplanation, context: ValidationContext) -> ValidationResult:
        # Check if speculation is properly hedged
        if claim.claim_type == ClaimType.SPECULATIVE:
            if not self._has_hedging_language(claim.text):
                return ValidationResult(
                    status=ValidationStatus.VIOLATION,
                    message="Speculation about author intent requires hedging language",
                    suggested_rewrite=self._add_hedging(claim.text)
                )

        # Check if intent claim has evidence
        if claim.claim_type == ClaimType.INTENT:
            evidence = self._search_for_evidence(claim, context)
            if not evidence:
                severity = context.contract.get_severity("intent_explanation")
                if severity == ViolationSeverity.BLOCK:
                    return ValidationResult(
                        status=ValidationStatus.BLOCK,
                        message="Author intent claim requires evidence from comments/docs/issues"
                    )
                else:
                    return ValidationResult(
                        status=ValidationStatus.WARNING,
                        message="No evidence found for author intent claim",
                        suggested_rewrite=self._add_hedging(claim.text)
                    )

        return ValidationResult(status=ValidationStatus.PASS)
```

**Pattern Sources:**
- External knowledge integration (CPCE)
- Manager/Verifier loop (Formal)
- Re-ask with context (Guardrails)

### Layer 5: Enforcement & Repair Layer
**Responsibilities:**
- Decide action based on verification results
- Execute rewrites in soft mode
- Block responses in hard mode
- Trigger re-prompt loop if needed

**Inputs:**
- Verification results
- Contract enforcement settings
- User configuration (soft/hard mode)

**Outputs:**
- Final action (ALLOW, REWRITE, BLOCK)
- Rewritten response (if applicable)
- User-facing explanation

**Decision Logic:**

```python
def decide_action(
    results: List[ValidationResult],
    contract: Contract,
    mode: EnforcementMode
) -> EnforcementAction:
    blocking_violations = [r for r in results if r.severity == ViolationSeverity.BLOCK]
    warning_violations = [r for r in results if r.severity == ViolationSeverity.WARNING]

    if blocking_violations and mode == EnforcementMode.HARD:
        return EnforcementAction(
            action=Action.BLOCK,
            explanation=self._format_blocking_violations(blocking_violations)
        )

    if warning_violations:
        if mode == EnforcementMode.SOFT:
            rewritten = self._apply_rewrites(results)
            return EnforcementAction(
                action=Action.REWRITE,
                response=rewritten,
                warnings=[r.message for r in warning_violations]
            )

    return EnforcementAction(action=Action.ALLOW)
```

**Pattern Sources:**
- OnFail actions (Guardrails)
- Re-ask loop (Guardrails)
- Iterative refinement (CPCE)

## 3.3 Hook Mapping

| Hook | Layer(s) | Responsibility |
|------|----------|----------------|
| **UserPromptSubmit** | 1, 2 | Task classification, contract loading, prompt enhancement |
| **PostToolUse** | 4 | Collect evidence from tool runs, update verification context |
| **Stop** | 3, 4, 5 | Claim extraction, verification, enforcement |

---

# Part 4: Intent-Explanation and Factual-Claim Control

## 4.1 Problem Definition

LLMs commonly generate un-evidenced claims about:
1. **Author Intent**: "The author added this because users forget X"
2. **Design Rationale**: "This pattern was chosen for performance"
3. **Factual Claims**: "This function is never called" (without checking)

These claims may be:
- Pure speculation (hallucinated reasoning)
- Logically inferred but not verified
- Actually true (but un-cited)

## 4.2 Claim Classification

| Claim Type | Description | Evidence Required | Hedging Allowed |
|------------|-------------|-------------------|-----------------|
| **Factual** | Claims about code/tests/files existence, behavior | Tool reads/logs | No |
| **Logical Consequence** | Claims derivable from code structure | Code trace | No |
| **Intent Explanation** | Claims about human author reasoning | Comments/docs/issues | Yes |
| **Speculation** | Hypothetical or uncertain claims | None | Required |

## 4.3 Contract Schema

```yaml
# contracts/factual_claims.yaml
name: "Factual Claims Contract"
version: "1.0"

validators:
  factual_claims:
    class: FactualClaimValidator
    rules:
      - "Claims about code existence must be backed by tool reads"
      - "Claims about function behavior must cite code or tests"
      - "Claims about file structure must use Glob/ls"
    evidence_sources:
      - tool_logs: [Read, Grep, Glob, find_symbol]
      - test_results: [pytest, cargo test, npm test]
    on_violation:
      severity: error
      action: rewrite

  intent_explanation:
    class: IntentExplanationValidator
    rules:
      - "Author intent claims require evidence from comments/docs/issues"
      - "Without evidence, use hedging: 'This may suggest...', 'Possible reason...'"
      - "Design rationale claims need citations or clear hedging"
    evidence_sources:
      - comments: #, /*, //
      - docs: README.md, DESIGN.md, docs/
      - issues: GitHub issues, PR discussions
      - commit_messages: git log
    hedging_patterns:
      - "may"
      - "might"
      - "possibly"
      - "appears to"
      - "suggests"
    on_violation:
      severity: warning
      action: rewrite  # Add hedging if no evidence

  logical_consequences:
    class: LogicalConsequenceValidator
    rules:
      - "Claims about code behavior must trace to actual code"
      - "Inference chains must be explicit"
    allows_inference: true
    requires_code_trace: true
    on_violation:
      severity: error
      action: rewrite
```

## 4.4 Validator Logic Sketches

### Intent Explanation Validator

```python
class IntentExplanationValidator(BaseValidator):
    """
    Validates claims about author intent and design rationale.
    Pattern: Guardrails validator + CPCE external knowledge + Formal verification
    """

    INTENT_PATTERNS = [
        r"the author (added|wrote|designed) .+ because",
        r"this (was|is) (added|written|designed) to",
        r"the (reason|purpose) .+ (is|was)",
        r"this pattern (was|is) chosen",
    ]

    HEDGING_PATTERNS = [
        r"may (suggest|indicate|mean)",
        r"possibly (added|written|designed)",
        r"one (possibility|explanation) (is|might be)",
        r"appears to",
    ]

    def validate(self, claim: Claim, context: ValidationContext) -> ValidationResult:
        # 1. Detect if this is an intent explanation
        if not self._is_intent_claim(claim.text):
            return ValidationResult.passed()

        # 2. Check for hedging language
        has_hedging = self._has_hedging(claim.text)
        intent_match = self._extract_intent(claim.text)

        # 3. Search for evidence in sources
        evidence = self._search_evidence(
            intent_claim=intent_match,
            sources=context.contract.evidence_sources,
            tool_logs=context.tool_logs
        )

        # 4. Apply decision logic
        if evidence:
            return ValidationResult.passed(citations=evidence)

        if has_hedging:
            # Properly hedged speculation is OK in soft mode
            return ValidationResult.passed(
                note="Speculation properly hedged"
            )

        # No evidence AND no hedging
        return ValidationResult.failed(
            message=f"Author intent claim lacks evidence. "
                   f"Either cite source (comment/doc/issue) or use hedging language.",
            suggested_rewrite=self._add_hedging(claim.text),
            severity=Severity.WARNING
        )

    def _search_evidence(self, intent_claim: str, sources: List[str],
                        tool_logs: List[ToolLog]) -> Optional[List[Evidence]]:
        """Search for evidence in configured sources."""
        evidence = []

        # Check tool logs for relevant reads
        for log in tool_logs:
            if log.tool in ["Read", "Grep"]:
                if self._intent_mentioned(intent_claim, log.output):
                    evidence.append(Evidence(
                        source=log.tool,
                        location=log.input.get("file_path"),
                        content=log.output
                    ))

        # Search CKS for relevant design docs
        cks_results = context.cks.search(intent_claim)
        for result in cks_results:
            if self._is_relevant_intent(intent_claim, result):
                evidence.append(Evidence(
                    source="CKS",
                    location=result.id,
                    content=result.content
                ))

        return evidence if evidence else None

    def _add_hedging(self, text: str) -> str:
        """Add hedging language to an un-hedged intent claim."""
        # Transform "The author added X because Y"
        # to "This may suggest the author added X because Y"
        return f"This may suggest {text[0].lower()}{text[1:]}"
```

### Factual Claim Validator

```python
class FactualClaimValidator(BaseValidator):
    """
    Validates factual claims about code/tests/files.
    Pattern: Manager/Verifier with tool logs as source of truth
    """

    FACTUAL_PATTERNS = [
        r"(this function|the function \w+) (is never called|has no callers)",
        r"(there is no|this doesn't have) .+ (test|tests)",
        r"this (file|module|class) (doesn't exist|is not present)",
        r"(all|every|no) .+ (function|class|variable)",
    ]

    def validate(self, claim: Claim, context: ValidationContext) -> ValidationResult:
        # 1. Detect factual claim type
        claim_type = self._classify_factual_claim(claim.text)

        # 2. Check tool logs for supporting evidence
        evidence = self._find_evidence_in_logs(claim, claim_type, context.tool_logs)

        if evidence:
            return ValidationResult.passed(
                citations=evidence,
                note=f"Claim verified by {evidence.source}"
            )

        # 3. If no evidence in logs, claim is unsubstantiated
        return ValidationResult.failed(
            message=f"Factual claim requires tool verification. "
                   f"Use {self._suggest_tool(claim_type)} to verify.",
            suggested_action=self._suggest_verification_action(claim, claim_type),
            severity=Severity.ERROR
        )

    def _suggest_tool(self, claim_type: FactualClaimType) -> str:
        """Suggest appropriate tool for verification."""
        suggestions = {
            FactualClaimType.FUNCTION_EXISTS: "Grep or find_symbol",
            FactualClaimType.TEST_EXISTS: "Glob for test files or run test suite",
            FactualClaimType.FILE_EXISTS: "Glob or ls",
            FactualClaimType.CALL_GRAPH: "find_referencing_symbols"
        }
        return suggestions.get(claim_type, "appropriate search tool")

    def _suggest_verification_action(self, claim: Claim,
                                     claim_type: FactualClaimType) -> str:
        """Generate a verification action to append to response."""
        if claim_type == FactualClaimType.FUNCTION_EXISTS:
            return f"Let me verify this claim by searching for references to the function."
        # ... more cases
```

## 4.5 Stop Hook Integration

```python
# Stop hook implementation sketch

@stop_hook
def verify_claims_and_intents(response: str, context: StopContext) -> StopAction:
    """
    Stop hook that validates claims and enforces contracts.
    Pattern: Manager/Verifier loop from formal verification + CPCE reasoning layer
    """

    # Layer 3: Claim Extraction
    claims = ClaimExtractor.extract(response)

    # Layer 4: Verification
    contract = ContractRegistry.get_contract(context.task_type)
    results = []

    for claim in claims:
        validators = contract.get_validators_for_claim(claim)
        for validator in validators:
            result = validator.validate(claim, context)
            results.append(result)

    # Layer 5: Enforcement
    action = EnforcementEngine.decide(results, contract, context.mode)

    if action.action == Action.BLOCK:
        return StopAction.block(
            message=action.explanation,
            suggestion="Please revise your response to address these issues."
        )

    if action.action == Action.REWRITE:
        return StopAction.modify(
            content=action.rewritten_response,
            warnings=action.warnings
        )

    return StopAction.allow()
```

## 4.6 The Verification Circuit: Evidence-Based Claim Enforcement

### Core Principle

**We are not choosing a tool; we are enforcing a circuit:**

```
Generate → Gather Evidence → Verify → Only then speak as if something is true
```

**Goal**: Reduce unverified pattern completion, not "never act unless web search succeeds."

The model must recognize **you and your local context as part of the verification stack**. When the user provides a file path, URL, or statement, that counts as valid evidence.

### What Counts as Valid Evidence

| Evidence Type | Valid Sources | Examples |
|---------------|---------------|----------|
| **User Context** | User-provided URLs, file paths, explicit statements | "Check /path/to/file", "The docs at X say..." |
| **Local Artifacts** | Files read via Read tool, tool outputs, test results | Read results, Bash output, pytest runs |
| **Codebase Facts** | SKILL.md, CLAUDE.md, project documentation | "SKILL.md says to use /plan-workflow review" |
| **Tool Results** | Grep, Glob, find_symbol results | "Grep shows no such function exists" |
| **External Sources** | Web search, fetched URLs (optional) | WebFetch results, documentation |

### Failure Mode: "Unverified Pattern Completion"

**The problem**: LLM generates text based on **pattern completion** rather than **evidence verification**.

**Examples**:
- Says "/plan-review" because it sounds like a command (pattern) → doesn't check if it exists (evidence)
- Apologizes for "unverified claims" because it sounds like a self-correction (pattern) → doesn't verify what it actually claimed (evidence)

**Root cause**: Model optimizes for **fluency** (what sounds right) over **accuracy** (what is true).

**The fix**: Enforce the verification circuit so every claim passes through evidence gathering before being spoken as true.

### Implementation: Two-Lane Verification Strategy

#### Lane 1: Critical Path (Blocking) - Pythea/Strawberry

**Purpose**: Catch high-risk hallucinations in Stop hook before user sees them.

**Target patterns**:
- Slash command references (`/plan-review`, `/arch-review`)
- Success claims ("fixed", "done", "works") without tool evidence
- API/file path references without Read verification

**Integration**:
```python
# StopHook_strawberry_validator.py
from strawberry.cot_detector import detect_hallucination

def verify_critical_claims(response: str, evidence: dict) -> dict:
    """
    Fast verification for high-risk patterns using Strawberry (pythea).

    Blocks: slash commands, success claims, file references without evidence.
    Allows: Hedged claims ("should work", "seems like"), questions, meta-talk.
    """
    result = detect_hallucination(response, evidence)
    if result.get("flagged"):
        return {"allow": False, "reason": f"Hallucination detected: {result['summary']}"}
    return {"allow": True}
```

**Latency management**:
- Fast path: Rule-based pre-check (regex patterns) < 10ms
- Slow path: LLM verification (Strawberry) 100-500ms
- Selective: Only trigger on high-risk patterns

#### Lane 2: Offline Analysis (Advisory) - Open-Strawberry

**Purpose**: Deep Multi-CoT reasoning traces for model training or heavy analysis.

**Usage**: Dev-only MCP/CLI, not critical path.

**When to use**:
- Post-session analysis: "Generate trace of this conversation"
- Fine-tuning data: "Harvest CoT examples from this session"
- Complex debugging: "Show reasoning path for this failure"

**Integration**: Separate from Stop hook. Call explicitly:
```bash
# Dev workflow, not automatic
/mcp open-strawberry generate_trace "Analyze /plan-review error"
```

#### Lane 3: Implementation - Strawberry Validator (2026-03-04)

**Status**: ✅ Implemented and tested (27 unit tests, all passing)

**Location**: `P:\.claude\hooks\scanners\strawberry_validator.py`

**Architecture**:

Two-stage hallucination detection based on NLI (Natural Language Inference) principles:

1. **Stage 1 - Fast Rule-Based Check** (<10ms)
   - Known invalid pattern detection via regex
   - Specific hallucinations: `/plan-review`, `/arch-review`, `/code-review`, `/test-review`
   - Sycophantic apology patterns
   - Path context exclusion (file paths, URLs, Unix directories)

2. **Stage 2 - LLM Verification** (100-500ms, selective)
   - Z.AI backend (glm-4-plus model)
   - NLI-style verification: CLAIM vs EVIDENCE → ENTAILMENT check
   - Only triggered for uncertain patterns (`/-review`, `/-check`, `/-validate`)
   - Fail-open design: Graceful degradation when API unavailable

**Detection Capabilities**:

| Pattern Type | Example | Action |
|--------------|---------|--------|
| Invalid slash commands | `/plan-review command showed...` | BLOCK with suggestion |
| Sycophantic apologies | `I apologize for unverified claims` | BLOCK (severity MEDIUM) |
| Legitimate paths | `P:/test.py contains config` | ALLOW |
| URLs | `https://api.zai.ai/v1` | ALLOW |
| Unix paths | `/usr/local/bin/python` | ALLOW |
| Uncertain commands | `/security-check command needs...` | LLM verify |

**Integration Pattern**:

```python
from scanners.strawberry_validator import StrawberryValidator
from scanners.base_scanner import ScanStatus

validator = StrawberryValidator(enabled=True, api_key=os.environ.get("ZAI_API_KEY"))

def stop_hook(response: str, context: dict) -> dict:
    result = validator.scan(response, context)

    if result.status == ScanStatus.FAIL:
        return {
            "allow": False,
            "reason": result.reason,
            "suggestion": result.suggestion
        }

    return {"allow": True}
```

**Configuration**:

```bash
# Required for Stage 2 LLM verification
export ZAI_API_KEY="your-zai-api-key"

# Optional: Disable Stage 2 (rule-based only)
export ZAI_API_KEY=""  # Empty to disable
```

**Performance Characteristics**:

- Stage 1 (rule-based): 0.01ms average, 0.05ms max (well under 10ms target)
- Stage 2 (LLM verification): 100-500ms with actual API call
- Fail-open: Returns PASS if API unavailable (timeout, error, no key)

**Evidence Building**:

The scanner automatically builds an evidence pack from context:

```python
def _build_evidence_pack(self, context: dict) -> str:
    """Extracts relevant tool outputs that could verify claims."""

    # From tool results:
    # - Read tool: file_path + content preview
    # - Bash tool: command + output

    return evidence_text  # Used as EVIDENCE in NLI verification
```

**NLI Verification Prompt**:

```
Given a CLAIM and EVIDENCE, determine if the evidence ENTAILS the claim.

Rules:
- ENTAILMENT (is_valid=true): Evidence directly supports the claim
- CONTRADICTION (is_valid=false): Evidence contradicts the claim
- NEUTRAL (is_valid=false): Evidence is unrelated to claim

For slash commands:
- If command matches a known valid pattern exactly: ENTAILMENT
- If command is unknown BUT evidence shows it was just used: ENTAILMENT
- If command is unknown AND no evidence of usage: CONTRADICTION
```

**Test Coverage**:

- 27 unit tests in `P:\.claude\hooks\tests\test_strawberry_validator.py`
- Test classes: Stage1, Stage2, EvidenceExtraction, Integration, PathExclusion
- All tests passing (100% pass rate)
- Manual testing verified: 6/6 scenarios passed

**Documentation**:

- Scanner README: `P:\.claude\hooks\scanners\README.md`
- Hooks CLAUDE.md: Added "Scanners" section with catalog
- Plan: `P:\.claude\hooks\plans\plan-20260304-strawberry-hallucination-detection.md`

**Related Systems**:

- Based on Pythea/Strawberry NLI principles: https://github.com/leochlon/pythea
- Z.AI backend: https://api.zai.ai/v1/chat/completions (OpenAI-compatible)
- Model: glm-4-plus (Chinese LLM with strong reasoning)

**Next Steps** (if needed):

- Add usage monitoring for API cost tracking
- Implement caching for repeated claim verification
- Add confidence calibration based on historical accuracy
- Extend to detect more hallucination patterns

### Prompt Architecture Fix

**Current issue**: Model says "don't trust unverified stuff" but fails to recognize local context as verification.

**Fix**: Add to CLAUDE.md and hook READMEs:

```markdown
## Verification Stack

You are part of a distributed verification system. These count as verified evidence:

1. **User statements**: What the user tells you is true
2. **Tool results**: Read, Grep, Glob outputs are ground truth
3. **Local files**: SKILL.md, CLAUDE.md are authoritative
4. **Previous turns**: Your own tool calls from this session count as evidence

**Before claiming X exists/works/is true**: Check if you have evidence from this turn.
```

**Key distinction**: The goal is "reduce unverified pattern completion," not "never act unless web search succeeds."

---

# Part 5: Implementation-Ready Outline

## 5.1 File/Module Layout

```
P:/__csf/
├── contracts/                          # Contract definitions (RAIL-like)
│   ├── factual_claims.yaml
│   ├── intent_explanation.yaml
│   ├── logical_consequences.yaml
│   └── task_contracts/
│       ├── code_read.yaml
│       ├── refactor.yaml
│       └── investigation.yaml
│
├── hooks/
│   ├── UserPromptSubmit.py             # Existing: enhance with contract loading
│   ├── PostToolUse.py                  # Existing: enhance with evidence collection
│   ├── Stop.py                         # New: claim verification and enforcement
│   │
│   └── guardrail_layer/                # New: reasoning layer implementation
│       ├── __init__.py
│       ├── claim_extractor.py          # Layer 3: Extract and classify claims
│       ├── validators/                 # Layer 4: Validator implementations
│       │   ├── __init__.py
│       │   ├── base.py                 # Base validator class
│       │   ├── factual_claim.py
│       │   ├── intent_explanation.py
│       │   └── logical_consequence.py
│       │
│       ├── verification/               # Layer 4: Evidence gathering
│       │   ├── __init__.py
│       │   ├── evidence_collector.py   # Gather from tool logs
│       │   └── cks_integrator.py       # Query CKS for evidence
│       │
│       ├── enforcement/                # Layer 5: Decision and action
│       │   ├── __init__.py
│       │   ├── decision_engine.py      # Decide ALLOW/REWRITE/BLOCK
│       │   └── rewriter.py             # Generate rewrites
│       │
│       ├── contracts/                  # Layer 1: Contract loading
│       │   ├── __init__.py
│       │   ├── registry.py             # Contract registry
│       │   └── loader.py               # YAML loader
│       │
│       └── config/                     # Configuration
│           ├── defaults.yaml           # Default settings
│           └── modes.yaml              # Soft/hard mode configs
│
├── tests/
│   ├── test_claim_extractor.py
│   ├── test_validators.py
│   ├── test_enforcement.py
│   └── fixtures/
│       ├── sample_claims.yaml
│       └── sample_responses.yaml
│
└── docs/
    ├── guardrail_architecture_design.md  # This document
    └── implementation_guide.md
```

## 5.2 Core Module Interfaces

### claim_extractor.py

```python
"""
Claim Extraction and Classification
Pattern: Output validation from CPCE
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Tuple

class ClaimType(Enum):
    FACTUAL = "factual"           # Claims about code existence/behavior
    LOGICAL = "logical"           # Logical consequences from code
    SPECULATIVE = "speculative"   # Hypothetical claims
    INTENT = "intent"             # Author/design intent claims

@dataclass
class Claim:
    """A claim extracted from LLM response."""
    text: str
    claim_type: ClaimType
    span: Tuple[int, int]
    confidence: float

@dataclass
class IntentExplanation(Claim):
    """Author intent claim with evidence requirements."""
    claimed_intent: str
    has_evidence: bool = False
    is_hedged: bool = False
    suggested_hedging: str = ""

class ClaimExtractor:
    """Extract and classify claims from LLM responses."""

    def extract(self, response: str) -> List[Claim]:
        """Extract all claims from response."""
        # Implementation using regex and NLP patterns
        pass

    def classify(self, claim_text: str) -> ClaimType:
        """Classify claim type."""
        # Implementation using pattern matching
        pass
```

### validators/base.py

```python
"""
Base Validator Class
Pattern: Guardrails validator_base.py + CPCE external validation
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, List

class ValidationStatus(Enum):
    PASS = "pass"
    WARNING = "warning"
    VIOLATION = "violation"
    BLOCK = "block"

@dataclass
class ValidationResult:
    """Result of validation."""
    status: ValidationStatus
    message: str = ""
    suggested_rewrite: str = ""
    citations: List[str] = None
    severity: str = "warning"

class BaseValidator:
    """Base class for all validators."""

    def validate(self, claim: Claim, context: ValidationContext) -> ValidationResult:
        """Validate a claim. Subclasses implement."""
        raise NotImplementedError
```

### enforcement/decision_engine.py

```python
"""
Decision Engine for Enforcement
Pattern: OnFail actions from Guardrails + Manager/Verifier from Formal
"""

from enum import Enum

class Action(Enum):
    ALLOW = "allow"
    REWRITE = "rewrite"
    BLOCK = "block"

class EnforcementMode(Enum):
    SOFT = "soft"      # Warnings + rewrites
    HARD = "hard"      # Blocking on violations

@dataclass
class EnforcementAction:
    """Action to take based on verification results."""
    action: Action
    explanation: str = ""
    rewritten_response: str = ""
    warnings: List[str] = None

class DecisionEngine:
    """Decide enforcement action based on verification results."""

    def decide(
        self,
        results: List[ValidationResult],
        contract: Contract,
        mode: EnforcementMode
    ) -> EnforcementAction:
        """Decide what action to take."""
        # Implementation logic
        pass
```

## 5.3 Phased Rollout Plan

### Phase 1: Logging + Soft Warnings (Week 1-2)
**Goal**: Observe claim patterns without disruption

- Implement claim extraction (Layer 3)
- Log all detected claims with classifications
- Add soft warnings for violations (no rewrites)
- Collect metrics on:
  - Claim type distribution
  - Violation frequency
  - False positive rate

**Exit Criteria**:
- Claim extractor >90% precision on sample set
- <5% false positive rate on intent detection

### Phase 2: Targeted Rewrites (Week 3-4)
**Goal**: Automatic correction for clear violations

- Implement intent explanation validator
- Add hedging rewrites for un-evidenced intent claims
- Implement factual claim validator
- Request verification for unsubstantiated facts

**Exit Criteria**:
- Rewrites improve quality (manual review)
- <2% rewrite degradation rate

### Phase 3: Hard Blocking for High-Risk (Week 5-6)
**Goal**: Prevent egregious hallucinations

- Implement hard blocking for:
  - Fabricated test results
  - Non-existent code references
  - Dangerous misinformation
- User override capability with acknowledgment

**Exit Criteria**:
- Zero false positive blocks
- User satisfaction >80%

### Phase 4: Full Rollout (Week 7+)
**Goal**: Production deployment

- All validators active
- Hard mode available as opt-in
- Continuous monitoring and refinement
- User feedback integration

## 5.4 Implementation Checklist

### Setup
- [ ] Create `hooks/guardrail_layer/` directory structure
- [ ] Create `contracts/` directory with YAML templates
- [ ] Set up test fixtures and sample data

### Layer 1: Schema & Contract
- [ ] Implement `contracts/registry.py`
- [ ] Implement `contracts/loader.py`
- [ ] Create base contract YAML templates
- [ ] Implement task type detection

### Layer 2: Prompt Enhancement
- [ ] Extend `UserPromptSubmit.py` with contract loading
- [ ] Add contract-based guidance injection
- [ ] Implement context source integration

### Layer 3: Claim Extraction
- [ ] Implement `claim_extractor.py`
- [ ] Add regex patterns for claim detection
- [ ] Implement claim classification logic
- [ ] Add unit tests for extractor

### Layer 4: Verification
- [ ] Implement `validators/base.py`
- [ ] Implement `validators/intent_explanation.py`
- [ ] Implement `validators/factual_claim.py`
- [ ] Implement `verification/evidence_collector.py`
- [ ] Implement CKS integration
- [ ] Add validator tests

### Layer 5: Enforcement
- [ ] Implement `enforcement/decision_engine.py`
- [ ] Implement `enforcement/rewriter.py`
- [ ] Create `Stop.py` hook
- [ ] Add soft/hard mode logic
- [ ] Implement user feedback loop

### Testing
- [ ] Unit tests for all validators
- [ ] Integration tests for full pipeline
- [ ] End-to-end tests with sample prompts
- [ ] Performance benchmarks
- [ ] False positive analysis

### Documentation
- [ ] Implementation guide
- [ ] Contract authoring guide
- [ ] Validator development guide
- [ ] User-facing documentation

### Monitoring
- [ ] Metrics collection (claim types, violations, rewrites)
- [ ] Performance monitoring (latency impact)
- [ ] User feedback mechanisms
- [ ] Continuous evaluation

---

# Appendix: Pattern Mapping Summary

| Our Design | Source Pattern | Project |
|------------|----------------|---------|
| Contract YAML | RAIL Specification | Guardrails |
| Validator Base Class | validator_base.py | Guardrails |
| OnFail Actions | on_fail (EXCEPTION, FIX, REASK) | Guardrails |
| Claim Extraction | Output Validation | CPCE |
| Evidence Collection | External Knowledge Integration | CPCE |
| Tool Log Verification | Manager/Verifier Loop | Formal |
| Decision Engine | Manager Orchestration | Formal |
| Re-prompt Loop | Re-ask with Context | Guardrails |
| Iterative Refinement | Multi-Pass Refinement | CPCE |
| Task-Specific Validators | Task Modules | CPCE |
| Hedging Detection | Logical Consistency | CPCE |
| Soft/Hard Mode | Severity Levels | Guardrails |
| CKS Integration | Knowledge Graphs | CPCE |
| Performance Metrics | LCR, RCR, PT | CPCE |
| User Feedback Loop | Feedback Integration | CPCE |
| Evidence Gate | Source of Truth | Formal |
| Rewrite Engine | OnFail=FIX | Guardrails |

---

# References

1. **CPCE-BigDataLab/Enhancing-Reasoning-Capacity-in-LLMs-with-Guardrails-as-a-Reasoning-Layer**
   - GitHub Repository
   - Core Concepts: Reasoning layer, external knowledge integration, iterative refinement

2. **guardrails-ai/guardrails**
   - GitHub Repository: https://github.com/guardrails-ai/guardrails
   - Core Concepts: RAIL specification, validators, on_fail actions, Guardrails Hub

3. **Formal Verification Research**
   - Papers on LLM code verification
   - Core Concepts: Manager/Verifier loop, external tools as source of truth

---

**Document Status:** Draft Specification - Ready for Implementation Planning
