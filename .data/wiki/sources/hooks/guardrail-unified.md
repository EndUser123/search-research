# Unified Guardrail Layer for Claude Code Hooks

Design and implementation guide for integrating reasoning guardrails, CKS evidence, policy learning, creative-task contracts, and cognitive frameworks into Claude Code CLI.

---

## SOLUTION DESIGN

### Current State

Claude Code sessions can already use tools and hooks, and a basic guardrail layer exists that verifies some factual claims (e.g., about code state) against tool logs before answers are returned. However, several gaps remain:
- External knowledge (CKS, long-term memory, docs) is not consistently treated as a first-class evidence source.
- Guardrail policies are static: contracts and thresholds are hand-authored and rarely updated based on actual usage patterns or violations.
- The system treats all tasks similarly, so strict code-centric validators may over-constrain creative or speculative tasks (brainstorming, blue-sky design).
- Cognitive frameworks (*-of-thought, RCA protocols, design decision templates) are used ad hoc rather than as structured reasoning modes tied into the guardrail system.

The result is useful but limited verification: it can catch some dangerous or clearly unsupported claims, but it does not fully leverage existing knowledge systems or adapt over time.

### Target State

The target state is a unified "reasoning + verification + guardrails" layer that:
- Treats CKS and other long-term knowledge stores as first-class verifiers alongside tool logs.
- Learns and refines guardrail policies from actual usage data and violation logs, producing contract adjustments over time.
- Uses task-type-specific contracts, including permissive modes for creative/speculative tasks that avoid over-enforcement.
- Integrates cognitive frameworks (root-cause analysis, design decision RFCs, planning templates, tree-of-thought, branch-then-prune) into the Prompt Enhancement layer and validates that responses follow those frameworks where appropriate.
- Operates in soft, hard, or off modes, with reversible, observable behavior.

In this target state, the guardrail layer is not only preventing bad outputs but actively improving reasoning quality, consistency, and transparency during long Claude Code CLI sessions.

### Architecture Overview

High-level layers and data flow:

```text
User Prompt
   │
   ▼
UserPromptSubmit Hook (Layer 1 + 2)
   - Task type detection
   - Contract loading
   - Prompt enhancement + cognitive framework guidance
   │
   ▼
Claude Code + Tools
   - Normal tool calls (Read, Grep, search, tests, etc.)
   │
   ▼
PostToolUse Hook (Layer 4 evidence collection)
   - Capture tool results into evidence store
   │
   ▼
Stop Hook (Layers 3, 4, 5)
   - Claim extraction & classification
   - Verification using:
       - Tool logs
       - CKS via CKSIntegrator
       - Docs/comments/issues
   - Apply contracts + DecisionEngine
   - Actions: ALLOW, REWRITE, BLOCK
   │
   ▼
Final Answer Shown to User
```

Logical layer breakdown:

1. **Schema & Contract Layer (Layer 1)**
   - YAML contracts per task type (`code_explanation`, `investigation`, `creative_brainstorm`, `blue_sky_design`, etc.).
   - Defines validators, severities, and enforcement actions.

2. **Prompt Enhancement & Cognitive Framework Layer (Layer 2)**
   - Injects frameworks and guidance into prompts based on task type.
   - Attaches reasoning modes (chain-of-thought, tree-of-thought, branch-then-prune) to tasks.

3. **Claim Extraction & Classification Layer (Layer 3)**
   - Extracts factual, logical, speculative, and intent claims from responses.

4. **Verification & Evidence Layer (Layer 4)**
   - Validates claims using:
     - Tool logs (PostToolUse evidence store)
     - CKS (via `CKSIntegrator`)
     - Docs, comments, issues
   - Uses validators for factual claims, intent explanations, and structure.

5. **Enforcement & Repair Layer (Layer 5)**
   - DecisionEngine chooses ALLOW / REWRITE / BLOCK.
   - Rewrites responses in soft mode (e.g., adding hedging).
   - Blocks in hard mode for critical violations.
   - Logs decisions for policy learning.

### Key Changes

1. **CKS as First-Class Evidence Source**  
   Why: External, long-term knowledge must be used to support design/intent explanations and high-level reasoning.

2. **Policy Learning from Guardrail Logs**  
   Why: Contracts and severities should evolve based on observed violations, false positives, and actual developer behavior.

3. **Creative/Speculative Task Contracts**  
   Why: Avoid over-constraining brainstorming and blue-sky prompts with strict factual/intent validators designed for code.

4. **Cognitive Framework Integration**  
   Why: Inject explicit reasoning structures (RCA, design RFC, planning templates) to improve LLM reasoning quality and make outputs more predictable and checkable.

5. **Unified Logging and Health Checks**  
   Why: Enable systematic monitoring, health checks, and quick troubleshooting of the guardrail layer.

### Benefits & Metrics

- **Reasoning Quality**  
  - Fewer un-evidenced intent stories presented as fact.  
  - Increased proportion of responses that follow specified frameworks (RCA, design RFC, etc.).

- **Reliability & Safety**  
  - Reduced rate of unsupported factual claims about code/tests/files.  
  - Hard-mode blocks only for clearly critical issues (e.g., fabricated test results, non-existent code references).

- **Adaptivity**  
  - Contracts and severities tuned over time based on real usage logs.  
  - Creative tasks kept flexible while engineering tasks become stricter.

- **Developer Experience**  
  - Fewer disruptive blocks in normal development.  
  - Clear, actionable warnings and suggested rewrites when issues are detected.

Example metrics to track:
- Claim type distribution: factual vs intent vs speculative vs logical.
- Violation rates per validator and per task type.
- Rewrite vs block ratios in soft vs hard mode.
- False-positive rate on sampled blocked/rewritten responses.

### Trade-offs & Constraints

- **Latency Overhead**: CKS queries and multi-pass validators add latency; mitigated by per-response caps and task-type routing.
- **Complexity**: More contracts and validators increase complexity; mitigated by clear module boundaries and tests.
- **Partial Coverage**: Creative/blue-sky contracts intentionally avoid strict validation, so they do not provide the same safety guarantees as code-focused tasks.
- **Manual Policy Review**: Policy learning produces suggestions, not automatic changes, to keep human control.

---

## IMPLEMENTATION

This section assumes a Windows 11 environment with PowerShell 7.5+, Claude Code CLI, and an existing monorepo with `.claude/hooks` already in use.

### Files Required

```text
P:/__csf/
├── contracts/
│   ├── factualclaims.yaml
│   ├── intentexplanation.yaml
│   ├── logicalconsequences.yaml
│   └── taskcontracts/
│       ├── code_explanation.yaml
│       ├── investigation.yaml
│       ├── creative_brainstorm.yaml
│       └── blue_sky_design.yaml
│
├── hooks/
│   ├── UserPromptSubmit.py
│   ├── PostToolUse.py
│   ├── Stop.py
│   └── guardrail_layer/
│       ├── __init__.py
│       ├── claimextractor.py
│       ├── validators/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── intentexplanation.py
│       │   └── factualclaim.py
│       ├── verification/
│       │   ├── __init__.py
│       │   └── cks_integrator.py
│       └── enforcement/
│           ├── __init__.py
│           └── decisionengine.py
│
├── prompt_enhancements/
│   ├── debug_root_cause.yaml
│   └── design_decision.yaml
│
├── tools/
│   └── guardrail_refine_policies.py
│
└── .claude/
    └── config/
        └── guardrail_defaults.yaml
```

You can adjust paths to match your existing layout, but keep relative structure consistent.

### Configuration Reference

Core configuration file: `P:/__csf/.claude/config/guardrail_defaults.yaml`

```yaml
enforcement:
  mode: soft            # soft | hard | off
  max_rewrites: 2
  rewrite_timeout_sec: 30

verification:
  enable_cks_integration: true
  enable_tool_log_analysis: true
  evidence_confidence_threshold: 0.7
  max_cks_queries_per_response: 2

claim_extraction:
  enable_intent_detection: true
  enable_factual_detection: true
  min_confidence: 0.5

logging:
  enable_guardrail_logs: true
  log_claims: true
  log_violations: true
  log_rewrites: true
  log_path: "~/.claude/guardrail_logs.jsonl"
```

| Variable | Type | Default | Purpose |
|----------|------|---------|---------|
| `enforcement.mode` | enum | `soft` | Overall behavior: warnings vs blocking |
| `verification.enable_cks_integration` | bool | `true` | Use CKS as evidence source |
| `verification.max_cks_queries_per_response` | int | `2` | Cap CKS lookups for latency control |
| `claim_extraction.min_confidence` | float | `0.5` | Threshold for keeping extracted claims |
| `logging.log_path` | string | `~/.claude/guardrail_logs.jsonl` | Location of guardrail event log |

### Contract Files

`P:/__csf/contracts/factualclaims.yaml`

```yaml
name: "Factual Claims Contract"
version: "1.0"

validators:
  factual_claims:
    class: FactualClaimValidator
    rules:
      - "Claims about code existence must be backed by tool reads."
      - "Claims about function behavior must cite code or tests."
      - "Claims about file structure must use Glob/ls."
    evidence_sources:
      - tool_logs: ["Read", "Grep", "Glob", "find_symbol"]
    on_violation:
      severity: error
      action: rewrite
```

`P:/__csf/contracts/intentexplanation.yaml`

```yaml
name: "Intent Explanation Contract"
version: "1.0"

validators:
  intent_explanation:
    class: IntentExplanationValidator
    rules:
      - "Author intent claims require evidence from comments/docs/issues."
      - "Without evidence, use hedging (e.g., 'may', 'might', 'possibly')."
      - "Design rationale claims need citations or clear hedging."
    evidence_sources:
      - comments: ["#", "//", "/*", "<!--"]
      - docs: ["README.md", "DESIGN.md", "ARCHITECTURE.md", "docs/"]
      - issues: ["issue", "pull request", "PR"]
    hedging_patterns:
      - "may"
      - "might"
      - "possibly"
      - "appears to"
      - "suggests"
    on_violation:
      severity: warning
      action: rewrite
```

`P:/__csf/contracts/logicalconsequences.yaml`

```yaml
name: "Logical Consequences Contract"
version: "1.0"

validators:
  logical_consequences:
    class: LogicalConsequenceValidator
    rules:
      - "Claims about code behavior must trace to actual code."
      - "Inference chains must be explicit."
    allows_inference: true
    requires_code_trace: true
    on_violation:
      severity: error
      action: rewrite
```

Task-specific contracts (examples):

`P:/__csf/contracts/taskcontracts/code_explanation.yaml`

```yaml
name: "Code Explanation Contract"
version: "1.0"

applies_to:
  task_types: ["code_explanation", "code_read", "refactor_design"]

validators:
  - id: "factual_claims"
    class: FactualClaimValidator

  - id: "intent_explanation"
    class: IntentExplanationValidator

  - id: "logical_consequences"
    class: LogicalConsequenceValidator

enforcement:
  default_severity: error
  mode: soft
```

`P:/__csf/contracts/taskcontracts/investigation.yaml`

```yaml
name: "Investigation Contract"
version: "1.0"

applies_to:
  task_types: ["investigation", "rca"]

reasoning_mode: "tree_of_thought"

validators:
  - id: "factual_claims"
    class: FactualClaimValidator
  - id: "intent_explanation"
    class: IntentExplanationValidator

enforcement:
  default_severity: warning
  mode: soft
```

`P:/__csf/contracts/taskcontracts/creative_brainstorm.yaml`

```yaml
name: "Creative Brainstorm Contract"
version: "1.0"

applies_to:
  task_types: ["creative_brainstorm", "naming", "ideation", "fiction"]

validators:
  - id: "safety"
    class: SafetyValidator
    config:
      enabled: true

  - id: "factual_claims"
    class: FactualClaimValidator
    config:
      enabled: false

  - id: "intent_explanation"
    class: IntentExplanationValidator
    config:
      enabled: false

enforcement:
  default_severity: info
  mode: soft
```

`P:/__csf/contracts/taskcontracts/blue_sky_design.yaml`

```yaml
name: "Blue Sky Design Contract"
version: "1.0"

applies_to:
  task_types: ["blue_sky_design", "speculative_arch"]

validators:
  - id: "intent_explanation"
    class: IntentExplanationValidator
    config:
      require_evidence: false
      allow_hedging: true
      hedging_patterns:
        - "might"
        - "could"
        - "possible"
        - "hypothetical"

  - id: "factual_claims"
    class: FactualClaimValidator
    config:
      restrict_to:
        domains: ["current_repo_state"]

enforcement:
  default_severity: info
  mode: soft
```

### Prompt Enhancement Frameworks

`P:/__csf/prompt_enhancements/debug_root_cause.yaml`

```yaml
framework: "Root Cause Analysis"
reasoning_mode: "tree_of_thought"

steps:
  - "Restate the observed symptom in your own words."
  - "List 3–5 plausible causes without committing to one."
  - "For each cause, list evidence for and against from the code or tools."
  - "Converge on the most likely cause and explicitly state remaining uncertainty."

guidance:
  - "Distinguish factual claims from logical consequences."
  - "Cite evidence (files, tests, tool outputs) for each factual claim."
  - "Use clear hedging for speculation about intent or unknowns."
```

`P:/__csf/prompt_enhancements/design_decision.yaml`

```yaml
framework: "Design Decision RFC"
reasoning_mode: "branch_then_prune"

sections:
  - "Context and constraints"
  - "Options considered (at least 3)"
  - "Pros and cons per option"
  - "Recommendation with rationale and trade-offs"

guidance:
  - "Separate facts, assumptions, and hypotheses."
  - "Call out trade-offs explicitly."
  - "Avoid presenting speculation as fact; hedge or label it as hypothetical."
```

### Hook Implementations

`P:/__csf/hooks/UserPromptSubmit.py`

```python
import os
import yaml

CONFIG_PATH = os.path.expanduser("~/.claude/config/guardrail_defaults.yaml")
PROMPT_ENHANCEMENTS_DIR = os.path.join("P:/__csf", "prompt_enhancements")


def _load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def _detect_task_type(prompt: str) -> str:
    pl = prompt.lower()
    if any(w in pl for w in ["brainstorm", "ideas for", "names for", "story about"]):
        return "creative_brainstorm"
    if any(w in pl for w in ["imagine", "what if in 5 years", "vision for"]):
        return "blue_sky_design"
    if any(w in pl for w in ["refactor", "clean up", "improve this code"]):
        return "refactor_design"
    if any(w in pl for w in ["investigate", "why is", "root cause"]):
        return "investigation"
    if any(w in pl for w in ["explain", "what does this do", "how does this work"]):
        return "code_explanation"
    return "general"


def _load_prompt_framework(task_type: str) -> dict:
    mapping = {
        "investigation": "debug_root_cause.yaml",
        "rca": "debug_root_cause.yaml",
        "refactor_design": "design_decision.yaml",
    }
    filename = mapping.get(task_type)
    if not filename:
        return {}
    path = os.path.join(PROMPT_ENHANCEMENTS_DIR, filename)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# Claude Code entry point

def load_contract_and_enhance_prompt(prompt: str, context) -> str:
    """UserPromptSubmit hook: detect task type, load contract, inject framework guidance."""
    cfg = _load_config()
    task_type = _detect_task_type(prompt)
    context.task_type = task_type

    framework_cfg = _load_prompt_framework(task_type)
    if not framework_cfg:
        return prompt

    guidance_lines = []
    framework_name = framework_cfg.get("framework")
    reasoning_mode = framework_cfg.get("reasoning_mode")

    if framework_name:
        guidance_lines.append(f"Use the '{framework_name}' framework.")
    if reasoning_mode:
        guidance_lines.append(f"Reasoning mode: {reasoning_mode}.")

    steps = framework_cfg.get("steps") or framework_cfg.get("sections") or []
    if steps:
        guidance_lines.append("Follow these steps:")
        for idx, step in enumerate(steps, start=1):
            guidance_lines.append(f"{idx}. {step}")

    extra_guidance = framework_cfg.get("guidance") or []
    if extra_guidance:
        guidance_lines.append("Additional guidelines:")
        for g in extra_guidance:
            guidance_lines.append(f"- {g}")

    guidance_block = "\n".join(guidance_lines)

    enhanced = (
        f"{prompt}\n\n"
        f"---\n"
        f"Guardrail Framework Guidance (auto-injected)\n"
        f"{guidance_block}\n"
    )
    return enhanced
```

`P:/__csf/hooks/PostToolUse.py`

```python
# Collects evidence from tool runs for later verification.


def collect_evidence(tool_result, context):
    """PostToolUse hook: store tool results in context for Stop hook to use."""
    if not hasattr(context, "evidence_store"):
        context.evidence_store = []

    evidence = {
        "tool": getattr(tool_result, "tool", None),
        "input": getattr(tool_result, "input", None),
        "output": getattr(tool_result, "output", None),
        "timestamp": getattr(tool_result, "timestamp", None),
    }
    context.evidence_store.append(evidence)
```

`P:/__csf/hooks/Stop.py`

```python
import os
import json
import yaml
from datetime import datetime

from hooks.guardrail_layer.claimextractor import ClaimExtractor
from hooks.guardrail_layer.validators.intentexplanation import (
    IntentExplanationValidator,
    ValidationContext,
)
from hooks.guardrail_layer.validators.factualclaim import FactualClaimValidator
from hooks.guardrail_layer.enforcement.decisionengine import (
    DecisionEngine,
    EnforcementMode,
    Action,
)
from hooks.guardrail_layer.verification.cks_integrator import CKSIntegrator

CONFIG_PATH = os.path.expanduser("~/.claude/config/guardrail_defaults.yaml")


def _load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def _get_cks_client():
    try:
        from cks import CKSClient

        return CKSClient()
    except Exception:
        return None


def _detect_task_type(prompt: str, tool_logs: list) -> str:
    # Fallback detection if UserPromptSubmit did not set task_type
    pl = prompt.lower()
    if any(w in pl for w in ["brainstorm", "ideas for", "names for", "story about"]):
        return "creative_brainstorm"
    if any(w in pl for w in ["imagine", "what if in 5 years", "vision for"]):
        return "blue_sky_design"
    if any(w in pl for w in ["refactor", "clean up", "improve this code"]):
        return "refactor_design"
    if any(w in pl for w in ["investigate", "why is", "root cause"]):
        return "investigation"
    if any(w in pl for w in ["explain", "what does this do", "how does this work"]):
        return "code_explanation"
    return "general"


def _log_guardrail_event(context, claims, results, action, cfg):
    logging_cfg = cfg.get("logging", {})
    if not logging_cfg.get("enable_guardrail_logs", True):
        return

    log_path = os.path.expanduser(logging_cfg.get("log_path", "~/.claude/guardrail_logs.jsonl"))
    record = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "task_type": getattr(context, "task_type", None),
        "mode": getattr(context, "mode", None),
        "claims": [
            {
                "text": c.text,
                "type": getattr(c, "claim_type", None),
                "confidence": getattr(c, "confidence", None),
            }
            for c in claims
        ],
        "results": [
            {
                "status": getattr(r, "status", None),
                "severity": getattr(r, "severity", None),
                "message": getattr(r, "message", None),
            }
            for r in results
        ],
        "action": getattr(action, "action", None),
    }

    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


# Claude Code entry point

def verify_claims_and_intents(response: str, context):
    """Stop hook: validate claims and enforce contracts before showing response."""
    cfg = _load_config()

    # Determine enforcement mode
    mode_str = cfg.get("enforcement", {}).get("mode", "soft").lower()
    mode = EnforcementMode.HARD if mode_str == "hard" else EnforcementMode.SOFT

    # Task type detection
    task_type = getattr(context, "task_type", None) or _detect_task_type(
        getattr(context, "prompt", ""), getattr(context, "evidence_store", [])
    )
    context.task_type = task_type
    context.mode = mode.value

    # Short-circuit for creative tasks
    if task_type in ("creative_brainstorm", "blue_sky_design"):
        return {"action": "allow"}

    # Extract claims
    extractor = ClaimExtractor()
    claims = extractor.extract(response)
    if not claims:
        return {"action": "allow"}

    # Build validation context
    cks_client = _get_cks_client() if cfg.get("verification", {}).get("enable_cks_integration", True) else None
    cks_integrator = CKSIntegrator(cks_client) if cks_client else None

    validation_context = ValidationContext(
        toollogs=getattr(context, "evidence_store", []),
        contract=None,  # contracts can be wired later if needed per-task
        cksclient=cks_integrator,
        responsetext=response,
    )

    # Validators
    validators = [IntentExplanationValidator(), FactualClaimValidator()]

    # Run validators
    results = []
    for claim in claims:
        for validator in validators:
            if validator.canvalidate(claim):
                result = validator.validate(claim, validation_context)
                results.append(result)

    # Decide enforcement action
    engine = DecisionEngine(mode=mode)
    action = engine.decide(results, response, contract=None)

    # Log
    _log_guardrail_event(context, claims, results, action, cfg)

    # Map to Claude Code StopAction-like dict
    if action.action == Action.BLOCK:
        return {
            "action": "block",
            "message": action.explanation,
            "suggestion": "Please revise your response to address these issues.",
        }
    if action.action == Action.REWRITE:
        return {
            "action": "modify",
            "content": action.rewrittenresponse,
            "warnings": action.warnings,
        }
    if action.warnings:
        return {
            "action": "allow",
            "warnings": action.warnings,
        }
    return {"action": "allow"}
```

### Guardrail Layer Modules

`P:/__csf/hooks/guardrail_layer/__init__.py`

```python
# Guardrail layer package marker
```

`P:/__csf/hooks/guardrail_layer/claimextractor.py`

```python
import re
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple


class ClaimType(Enum):
    FACTUAL = "factual"
    LOGICAL = "logical"
    SPECULATIVE = "speculative"
    INTENT = "intent"


@dataclass
class Claim:
    text: str
    claim_type: ClaimType
    span: Tuple[int, int]
    confidence: float


class ClaimExtractor:
    """Extract and classify claims from LLM responses using regex heuristics."""

    def extract(self, response: str) -> List[Claim]:
        claims: List[Claim] = []
        sentences = re.split(r"(?<=[.!?])\s+", response)
        offset = 0
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                offset += 1
                continue
            start = response.find(sentence, offset)
            end = start + len(sentence)
            claim_type = self.classify(sentence)
            if claim_type:
                claims.append(
                    Claim(
                        text=sentence,
                        claim_type=claim_type,
                        span=(start, end),
                        confidence=0.9,
                    )
                )
            offset = end
        return claims

    def classify(self, text: str) -> ClaimType:
        tl = text.lower()
        # Very simple heuristics, extend as needed
        if any(p in tl for p in ["the author", "the developer", "intended", "wanted", "added this because"]):
            return ClaimType.INTENT
        if any(p in tl for p in ["is never called", "there are no tests", "does not exist", "all functions"]):
            return ClaimType.FACTUAL
        if any(p in tl for p in ["might", "may", "could", "possibly", "hypothetically"]):
            return ClaimType.SPECULATIVE
        if any(p in tl for p in ["therefore", "so", "thus", "as a result"]):
            return ClaimType.LOGICAL
        return ClaimType.FACTUAL  # default for now
```

`P:/__csf/hooks/guardrail_layer/validators/__init__.py`

```python
# Validators package marker
```

`P:/__csf/hooks/guardrail_layer/validators/base.py`

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ValidationStatus(Enum):
    PASS = "pass"
    WARNING = "warning"
    VIOLATION = "violation"
    BLOCK = "block"


class Severity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    status: ValidationStatus
    message: str = ""
    suggestedrewrite: str = ""
    citations: List[str] = field(default_factory=list)
    severity: Severity = Severity.WARNING
    metadata: Dict[str, Any] = field(default_factory=dict)

    def isblocking(self) -> bool:
        return self.status in (ValidationStatus.BLOCK, ValidationStatus.VIOLATION)

    def requiresrewrite(self) -> bool:
        return self.status in (ValidationStatus.WARNING, ValidationStatus.VIOLATION) and bool(
            self.suggestedrewrite
        )


@dataclass
class ValidationContext:
    toollogs: List[Any]
    contract: Any
    cksclient: Any
    responsetext: str


@dataclass
class ClaimBase:
    text: str
    span: tuple
    confidence: float


class BaseValidator:
    name: str = "basevalidator"

    def validate(self, claim: Any, context: ValidationContext) -> ValidationResult:
        raise NotImplementedError

    def canvalidate(self, claim: Any) -> bool:
        return True

    def getevidencesources(self) -> List[str]:
        return []
```

`P:/__csf/hooks/guardrail_layer/validators/intentexplanation.py`

```python
import re
from dataclasses import dataclass
from typing import List, Any

from .base import BaseValidator, ValidationResult, ValidationStatus, Severity, ValidationContext
from ..claimextractor import Claim, ClaimType


INTENT_PATTERNS = [
    r"the author (added|wrote|designed|created|implemented).+because",
    r"this (was|is) (added|written|designed|created|implemented) to",
    r"the (reason|purpose|intent).+(is|was)",
    r"this pattern (was|is) chosen",
    r"the developer (intended|wanted|meant)",
]

HEDGING_PATTERNS = [
    r"may",
    r"might",
    r"could",
    r"possibly",
    r"perhaps",
    r"one possibility",
    r"it appears",
    r"it seems",
    r"suggests",
]


@dataclass
class IntentClaim(Claim):
    claimedintent: str = ""
    hasevidence: bool = False
    ishedged: bool = False


class IntentExplanationValidator(BaseValidator):
    name: str = "intentexplanation"

    def canvalidate(self, claim: Any) -> bool:
        if isinstance(claim, IntentClaim):
            return True
        if isinstance(claim, Claim) and claim.claim_type in (ClaimType.INTENT, ClaimType.SPECULATIVE):
            return True
        return False

    def validate(self, claim: Any, context: ValidationContext) -> ValidationResult:
        if not isinstance(claim, IntentClaim):
            claim = self._convert_to_intent_claim(claim)

        has_hedging = self._has_hedging(claim.text)
        evidence = self._search_evidence(claim, context)

        if evidence:
            return ValidationResult(
                status=ValidationStatus.PASS,
                message="Intent claim has supporting evidence.",
                citations=[e["source"] for e in evidence],
                severity=Severity.INFO,
                metadata={"evidence_count": len(evidence)},
            )

        if has_hedging:
            return ValidationResult(
                status=ValidationStatus.PASS,
                message="Speculation about intent is properly hedged.",
                severity=Severity.INFO,
            )

        suggested = self._add_hedging(claim.text)
        return ValidationResult(
            status=ValidationStatus.WARNING,
            message=(
                "Author intent claim lacks evidence. Either cite a source (comment/doc/issue) "
                "or use hedging language."
            ),
            suggestedrewrite=suggested,
            severity=Severity.WARNING,
            metadata={"suggested_hedging": suggested},
        )

    def _convert_to_intent_claim(self, claim: Claim) -> IntentClaim:
        intent_text = self._extract_intent(claim.text)
        return IntentClaim(
            text=claim.text,
            claim_type=claim.claim_type,
            span=claim.span,
            confidence=claim.confidence,
            claimedintent=intent_text,
        )

    def _has_hedging(self, text: str) -> bool:
        return any(re.search(p, text, re.IGNORECASE) for p in HEDGING_PATTERNS)

    def _extract_intent(self, text: str) -> str:
        for pattern in INTENT_PATTERNS:
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                return text[m.start() :]
        return text

    def _search_evidence(self, claim: IntentClaim, context: ValidationContext) -> List[dict]:
        evidence: List[dict] = []
        # Tool logs
        for log in context.toollogs:
            tool = log.get("tool")
            output = str(log.get("output") or "").lower()
            if tool in ("Read", "Grep") and self._intent_mentioned(claim.claimedintent, output):
                evidence.append(
                    {
                        "source": tool,
                        "location": (log.get("input") or {}).get("file_path", "unknown"),
                    }
                )
        # CKS
        if context.cksclient is not None:
            try:
                best = context.cksclient.best_match(claim.claimedintent)
                if best:
                    evidence.append(
                        {
                            "source": "CKS",
                            "location": best.id,
                        }
                    )
            except Exception:
                pass
        return evidence

    def _intent_mentioned(self, intent: str, text: str) -> bool:
        iw = set(re.findall(r"\w+", intent.lower()))
        tw = set(re.findall(r"\w+", text.lower()))
        return len(iw & tw) >= max(2, len(iw) // 2)

    def _add_hedging(self, text: str) -> str:
        prefixes = [
            "This may suggest that ",
            "It appears that ",
            "One possible explanation is that ",
        ]
        prefix = prefixes[0]
        return f"{prefix}{text[0].lower()}{text[1:]}"

    def getevidencesources(self) -> List[str]:
        return ["comments", "docs", "issues", "toollogs", "cks"]
```

`P:/__csf/hooks/guardrail_layer/validators/factualclaim.py`

```python
import re
from typing import List, Any

from .base import BaseValidator, ValidationResult, ValidationStatus, Severity, ValidationContext
from ..claimextractor import Claim, ClaimType


class FactualClaimType:
    FUNCTION_EXISTS = "function_exists"
    TEST_EXISTS = "test_exists"
    FILE_EXISTS = "file_exists"
    CALL_GRAPH = "call_graph"
    BEHAVIOR = "behavior"
    UNCONDITIONAL = "unconditional"


FACTUAL_PATTERNS = {
    FactualClaimType.FUNCTION_EXISTS: [
        r"this function is never called",
        r"the function \w+ is never called",
        r"there (is|are) no calls to",
    ],
    FactualClaimType.TEST_EXISTS: [
        r"there (is|are) no tests",
        r"this has no tests",
        r"untested",
    ],
    FactualClaimType.FILE_EXISTS: [
        r"this file does not exist",
        r"there is no file",
    ],
    FactualClaimType.UNCONDITIONAL: [
        r"all ",
        r"every ",
        r"none ",
        r"never ",
    ],
}


class FactualClaimValidator(BaseValidator):
    name: str = "factualclaim"

    def canvalidate(self, claim: Any) -> bool:
        if not isinstance(claim, Claim):
            return False
        return claim.claim_type in (ClaimType.FACTUAL, ClaimType.LOGICAL)

    def validate(self, claim: Claim, context: ValidationContext) -> ValidationResult:
        claim_type = self._classify(claim.text)
        evidence = self._find_evidence_in_logs(claim.text, claim_type, context.toollogs)

        if evidence:
            return ValidationResult(
                status=ValidationStatus.PASS,
                message=f"Claim verified by {evidence['source']}",
                citations=[evidence["source"]],
                severity=Severity.INFO,
                metadata={"evidence": evidence},
            )

        if claim_type == FactualClaimType.UNCONDITIONAL:
            qualified = self._add_qualification(claim.text)
            return ValidationResult(
                status=ValidationStatus.WARNING,
                message="Unconditional claim (all/never) requires verification.",
                suggestedrewrite=qualified,
                severity=Severity.WARNING,
                metadata={"claim_type": claim_type},
            )

        suggested_action = self._suggest_verification_action(claim_type)
        return ValidationResult(
            status=ValidationStatus.WARNING,
            message=(
                "Factual claim requires verification. "
                f"Use {suggested_action} to verify before asserting as fact."
            ),
            suggestedrewrite=claim.text,
            severity=Severity.WARNING,
            metadata={"claim_type": claim_type, "suggested_tool": suggested_action},
        )

    def _classify(self, text: str) -> str:
        tl = text.lower()
        for ctype, patterns in FACTUAL_PATTERNS.items():
            for p in patterns:
                if re.search(p, tl):
                    return ctype
        return FactualClaimType.BEHAVIOR

    def _find_evidence_in_logs(self, text: str, claim_type: str, logs: List[Any]) -> Any:
        for log in logs:
            tool = log.get("tool")
            output = str(log.get("output") or "").lower()
            if tool in ("Grep", "find_symbol", "find_referencing_symbols"):
                if "no" in text.lower() or "never" in text.lower():
                    # match absence: no evidence
                    continue
                if any(tok in output for tok in text.lower().split()):
                    return {"source": tool, "output": output}
        return None

    def _add_qualification(self, text: str) -> str:
        replacements = {
            r"all ": "most ",
            r"every ": "many ",
            r"never ": "rarely ",
            r"none ": "few ",
        }
        result = text
        for pattern, repl in replacements.items():
            result = re.sub(pattern, repl, result, flags=re.IGNORECASE)
        return result

    def _suggest_verification_action(self, claim_type: str) -> str:
        mapping = {
            FactualClaimType.FUNCTION_EXISTS: "find_referencing_symbols or Grep",
            FactualClaimType.TEST_EXISTS: "Glob for test files or run the test suite",
            FactualClaimType.FILE_EXISTS: "Glob or directory listing",
            FactualClaimType.CALL_GRAPH: "find_referencing_symbols",
            FactualClaimType.BEHAVIOR: "Read the function code and tests",
            FactualClaimType.UNCONDITIONAL: "Comprehensive Grep and symbol search",
        }
        return mapping.get(claim_type, "appropriate search tool")

    def getevidencesources(self) -> List[str]:
        return ["toollogs", "Grep", "Glob", "find_referencing_symbols"]
```

`P:/__csf/hooks/guardrail_layer/verification/__init__.py`

```python
# Verification package marker
```

`P:/__csf/hooks/guardrail_layer/verification/cks_integrator.py`

```python
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CKSEvidence:
    source: str
    id: str
    title: str
    snippet: str
    score: float


class CKSIntegrator:
    def __init__(self, client):
        self.client = client

    def search_intent(self, intent_text: str, limit: int = 5) -> List[CKSEvidence]:
        if not self.client:
            return []
        results = self.client.search(intent_text, limit=limit)
        out: List[CKSEvidence] = []
        for r in results:
            out.append(
                CKSEvidence(
                    source="CKS",
                    id=r.get("id", ""),
                    title=r.get("title", ""),
                    snippet=(r.get("content", "") or "")[:400],
                    score=float(r.get("score", 0.0)),
                )
            )
        return out

    def best_match(self, intent_text: str, threshold: float = 0.6) -> Optional[CKSEvidence]:
        candidates = self.search_intent(intent_text, limit=3)
        if not candidates:
            return None
        best = max(candidates, key=lambda c: c.score)
        return best if best.score >= threshold else None
```

`P:/__csf/hooks/guardrail_layer/enforcement/__init__.py`

```python
# Enforcement package marker
```

`P:/__csf/hooks/guardrail_layer/enforcement/decisionengine.py`

```python
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any

from ..validators.base import ValidationResult, Severity


class Action(Enum):
    ALLOW = "allow"
    REWRITE = "rewrite"
    BLOCK = "block"


class EnforcementMode(Enum):
    SOFT = "soft"
    HARD = "hard"


@dataclass
class EnforcementAction:
    action: Action
    explanation: str = ""
    rewrittenresponse: str = ""
    warnings: List[str] = field(default_factory=list)
    violations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DecisionEngine:
    def __init__(self, mode: EnforcementMode = EnforcementMode.SOFT):
        self.mode = mode

    def decide(self, results: List[ValidationResult], response: str, contract: Any) -> EnforcementAction:
        by_severity: Dict[Severity, List[ValidationResult]] = {s: [] for s in Severity}
        for r in results:
            by_severity[r.severity].append(r)

        if self._should_block(by_severity):
            explanation = self._format_blocking_message(by_severity)
            violations = [r.message for sev, lst in by_severity.items() for r in lst if sev in (Severity.ERROR, Severity.CRITICAL)]
            return EnforcementAction(
                action=Action.BLOCK,
                explanation=explanation,
                violations=violations,
                metadata={"severity_breakdown": {s.name: len(lst) for s, lst in by_severity.items()}},
            )

        if self._should_write(by_severity):
            rewritten = self._apply_rewrites(response, results)
            warnings = [r.message for r in results if r.requiresrewrite()]
            return EnforcementAction(
                action=Action.REWRITE,
                explanation=f"Applied {len(warnings)} guardrail rewrite(s) for compliance.",
                rewrittenresponse=rewritten,
                warnings=warnings,
            )

        warnings = [r.message for r in results if r.severity == Severity.INFO]
        return EnforcementAction(action=Action.ALLOW, warnings=warnings)

    def _should_block(self, by_severity: Dict[Severity, List[ValidationResult]]) -> bool:
        critical = len(by_severity[Severity.CRITICAL])
        errors = len(by_severity[Severity.ERROR])
        if self.mode == EnforcementMode.SOFT:
            return critical > 0
        return critical > 0 or errors > 0

    def _should_write(self, by_severity: Dict[Severity, List[ValidationResult]]) -> bool:
        candidates = by_severity[Severity.WARNING] + by_severity[Severity.ERROR]
        return any(r.suggestedrewrite for r in candidates)

    def _format_blocking_message(self, by_severity: Dict[Severity, List[ValidationResult]]) -> str:
        parts = []
        if by_severity[Severity.CRITICAL]:
            parts.append(f"{len(by_severity[Severity.CRITICAL])} critical issues")
        if by_severity[Severity.ERROR]:
            parts.append(f"{len(by_severity[Severity.ERROR])} errors")
        if not parts:
            return "Response blocked due to guardrail policy violations."
        return "Response blocked due to " + ", ".join(parts) + "."

    def _apply_rewrites(self, response: str, results: List[ValidationResult]) -> str:
        rewritten = response
        # For simplicity, replace original text with suggestedrewrite when available.
        # In production, track spans and apply from end to start.
        for r in results:
            original = r.metadata.get("original_text") if hasattr(r, "metadata") else None
            if r.suggestedrewrite and original and original in rewritten:
                rewritten = rewritten.replace(original, r.suggestedrewrite, 1)
        return rewritten
```

### Policy Learning Script

`P:/__csf/tools/guardrail_refine_policies.py`

```python
import json
import os
from collections import Counter, defaultdict

LOG_PATH = os.path.expanduser("~/.claude/guardrail_logs.jsonl")


def load_logs():
    if not os.path.exists(LOG_PATH):
        print("No guardrail log file found.")
        return []
    records = []
    with open(LOG_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except Exception:
                continue
    return records


def summarize(records):
    by_task = defaultdict(Counter)
    for r in records:
        task = r.get("task_type") or "unknown"
        action = (r.get("action") or "").split(".")[-1]
        by_task[task][action] += 1
    print("Guardrail action summary by task type:\n")
    for task, counter in by_task.items():
        print(task, dict(counter))


if __name__ == "__main__":
    recs = load_logs()
    summarize(recs)
    # Extend this to emit contract tuning suggestions as needed.
```

### Step-by-Step Setup

All commands below are PowerShell-friendly.

1. **Create directory structure**

```powershell
# Adjust P: path if needed
New-Item -ItemType Directory -Force -Path "P:/__csf/contracts/taskcontracts" | Out-Null
New-Item -ItemType Directory -Force -Path "P:/__csf/hooks/guardrail_layer/validators" | Out-Null
New-Item -ItemType Directory -Force -Path "P:/__csf/hooks/guardrail_layer/verification" | Out-Null
New-Item -ItemType Directory -Force -Path "P:/__csf/hooks/guardrail_layer/enforcement" | Out-Null
New-Item -ItemType Directory -Force -Path "P:/__csf/prompt_enhancements" | Out-Null
New-Item -ItemType Directory -Force -Path "P:/__csf/tools" | Out-Null
New-Item -ItemType Directory -Force -Path "$HOME/.claude/config" | Out-Null
```

2. **Create configuration file**

Copy the `guardrail_defaults.yaml` content into:

```powershell
Set-Content -Path "$HOME/.claude/config/guardrail_defaults.yaml" -Value @"
[PASTE guardrail_defaults.yaml CONTENT HERE]
"@
```

3. **Create contract and prompt enhancement files**

Use your editor or `Set-Content`/`Add-Content` to create the YAML files in `contracts/` and `prompt_enhancements/` with the content above.

4. **Create hook scripts and guardrail modules**

Create the `.py` files under `hooks/` and `hooks/guardrail_layer/` with the exact code shown above.

5. **Wire hooks in Claude Code config**

Ensure your Claude Code CLI is configured so that:
- `UserPromptSubmit` points to `load_contract_and_enhance_prompt` in `UserPromptSubmit.py`.
- `PostToolUse` points to `collect_evidence` in `PostToolUse.py`.
- `Stop` points to `verify_claims_and_intents` in `Stop.py`.

6. **Restart Claude Code CLI**

Restart any running Claude Code CLI processes so they pick up new hooks.

```powershell
# Example: if using a custom launcher script
Stop-Process -Name "claude-code" -ErrorAction SilentlyContinue
Start-Process "claude-code" -ArgumentList "--project P:/__csf"
```

### Testing Patterns

- **Test 1: Intent Explanation Hedging**
  - Prompt: "Explain why the author added this function, without reading any comments or docs."  
  - If the answer says "The author added this to handle edge cases" with no hedging or evidence, the Stop hook should suggest a rewrite like "This may suggest that the author added this to handle edge cases." and either rewrite automatically (soft mode) or warn.

- **Test 2: Factual Claim Verification**
  - Prompt: "Tell me if this function is never called anywhere."  
  - If Claude claims "This function is never called" without running search tools, the FactualClaimValidator should flag it and suggest verifying with `find_referencing_symbols` or Grep.

- **Test 3: Creative Brainstorm Exemption**
  - Prompt: "Brainstorm 10 app ideas that combine LLMs and home automation."  
  - Task type should be `creative_brainstorm` and Stop hook should allow the response without running strict intent/factual validators.

- **Test 4: CKS Evidence Usage**
  - After you have CKS entries about design rationale, ask: "Why was the auth module split into three services?"  
  - Stop hook should let IntentExplanationValidator pull evidence from CKS and treat intent claims as supported when it finds matching entries.

- **Test 5: Logging & Policy Summary**
  - Use the system normally for a day, then run the policy script:

```powershell
python P:/__csf/tools/guardrail_refine_policies.py
```

  - Inspect summary of actions per task type and adjust contracts manually if needed.

### Troubleshooting

#### Issue: Guardrail layer appears to do nothing

**Symptom:** No warnings, rewrites, or logs, even when making obviously bad claims.

**Solution:**
- Verify hook wiring in Claude Code CLI config.
- Confirm that `verify_claims_and_intents` is being called by inserting a temporary log or print.
- Ensure `enforcement.mode` is not set to `off` in `guardrail_defaults.yaml`.
- Check that `logging.enable_guardrail_logs` is `true` and that the log file path is writable.

#### Issue: Responses are blocked too aggressively

**Symptom:** Many answers are blocked for relatively minor issues.

**Solution:**
- Switch to soft mode in `guardrail_defaults.yaml`:

```yaml
enforcement:
  mode: soft
```

- Lower severities in contract YAMLs where appropriate (e.g., from `error` to `warning`).
- Use the policy script to understand which validators trigger most often and adjust contracts.

#### Issue: Latency too high due to CKS queries

**Symptom:** Noticeable delay before responses appear when many intent claims are present.

**Solution:**
- Reduce `max_cks_queries_per_response` in `guardrail_defaults.yaml`.
- Temporarily set `verification.enable_cks_integration: false` to isolate the effect.
- Restrict CKS usage to specific task types in `Stop.py` if needed.

#### Issue: Creative tasks still feel over-constrained

**Symptom:** Brainstorming or blue-sky prompts still trigger warnings.

**Solution:**
- Confirm `detect_task_type` correctly classifies creative prompts.
- Ensure creative contracts disable `FactualClaimValidator` and `IntentExplanationValidator`.
- Consider adding additional creative-specific contracts if needed.

---

## STEADY-STATE OPERATION

### Daily Workflows

- **Normal Coding & Debugging Sessions**
  - Use Claude Code CLI as usual for code explanations, refactors, and bugfixes.
  - The Prompt Enhancement hook injects RCA or design frameworks when task types match.
  - The guardrail layer runs in soft mode, rewriting un-hedged intent claims and flagging unsupported factual claims without blocking.

- **Creative & Design Sessions**
  - For ideation, naming, and fiction, rely on creative/blue-sky task types to keep guardrails light.
  - For speculative architecture, use the `blue_sky_design` contract, which encourages hedged speculation but does not require evidence for future-looking statements.

- **Periodic Policy Review**
  - Once per day or week, review guardrail logs and summaries:

```powershell
python P:/__csf/tools/guardrail_refine_policies.py
```

  - Adjust contract YAMLs where specific validators are too chatty or too lenient.

### On-Demand Health Checks

Run these checks when guardrail behavior seems off.

```powershell
# Check that log file is being updated
Get-Content -Path "$HOME/.claude/guardrail_logs.jsonl" -Tail 10

# Verify configuration
Get-Content -Path "$HOME/.claude/config/guardrail_defaults.yaml"

# Quick dry-run summary of logs
python P:/__csf/tools/guardrail_refine_policies.py
```

Expected healthy state:
- Recent log lines present with `task_type`, `mode`, `claims`, `results`, and `action`.
- Policy summary shows mostly `allow` and `rewrite` in soft mode, with `block` rare and concentrated in high-risk tasks.

### Common Operational Tasks

- **Adjust Enforcement Mode**

```powershell
# Switch to hard mode for critical work
(Get-Content "$HOME/.claude/config/guardrail_defaults.yaml") -replace 'mode: soft', 'mode: hard' |`
  Set-Content "$HOME/.claude/config/guardrail_defaults.yaml"
```

Restart Claude Code CLI to apply.

- **Temporarily Disable Guardrails**

```powershell
# Turn guardrails off (for troubleshooting)
(Get-Content "$HOME/.claude/config/guardrail_defaults.yaml") -replace 'mode: soft', 'mode: off' |`
  Set-Content "$HOME/.claude/config/guardrail_defaults.yaml"
```

Re-enable after debugging by restoring `mode: soft` or `mode: hard`.

- **Rotate Logs**

```powershell
$log = "$HOME/.claude/guardrail_logs.jsonl"
if (Test-Path $log) {
  $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
  Copy-Item $log "$log.$timestamp.bak"
  Clear-Content $log
}
```

- **Update Contracts Safely**
  - Before editing any contract YAML, create a backup copy.

```powershell
Copy-Item "P:/__csf/contracts" "P:/__csf/contracts.backup" -Recurse -Force
```

  - After edits, run a few known prompts to ensure behavior matches expectations.

---

This single Markdown file is intended to be copy-paste ready. Save it as `guardrail_unified_design.md` in your docs directory and follow the setup steps to bring the full guardrail layer online.
