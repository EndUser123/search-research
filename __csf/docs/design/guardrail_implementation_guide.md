# Guardrail Layer Implementation Guide
## Concrete Implementation for Claude Code Hooks

**Version:** 1.0
**Date:** 2025-02-15
**Status:** Implementation Ready

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Module Implementations](#module-implementations)
3. [Hook Integration](#hook-integration)
4. [Testing Strategy](#testing-strategy)
5. [Deployment Checklist](#deployment-checklist)

---

## 1. Quick Start

### 1.1 Installation Steps

```bash
# 1. Create directory structure
mkdir -p P:/__csf/hooks/guardrail_layer/{validators,verification,enforcement,contracts,config}
mkdir -p P:/__csf/contracts/task_contracts
mkdir -p P:/__csf/tests/guardrail_layer

# 2. Create __init__ files
touch P:/__csf/hooks/guardrail_layer/__init__.py
touch P:/__csf/hooks/guardrail_layer/validators/__init__.py
touch P:/__csf/hooks/guardrail_layer/verification/__init__.py
touch P:/__csf/hooks/guardrail_layer/enforcement/__init__.py
touch P:/__csf/hooks/guardrail_layer/contracts/__init__.py
```

### 1.2 Configuration Files

**`config/defaults.yaml`**

```yaml
# Default configuration for guardrail layer
enforcement:
  mode: soft  # soft | hard
  max_rewrites: 2
  rewrite_timeout: 30

verification:
  enable_cks_integration: true
  enable_tool_log_analysis: true
  evidence_confidence_threshold: 0.7

claim_extraction:
  enable_intent_detection: true
  enable_factual_detection: true
  min_confidence: 0.5

logging:
  log_claims: true
  log_violations: true
  log_rewrites: true
```

---

## 2. Module Implementations

### 2.1 Base Validator (`validators/base.py`)

```python
"""
Base Validator Class
Pattern: guardrails-ai/guardrails validator_base.py
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

class ValidationStatus(Enum):
    """Status of validation result."""
    PASS = "pass"
    WARNING = "warning"
    VIOLATION = "violation"
    BLOCK = "block"

class Severity(Enum):
    """Severity level for violations."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationResult:
    """Result of a validation check."""
    status: ValidationStatus
    message: str = ""
    suggested_rewrite: str = ""
    citations: List[str] = field(default_factory=list)
    severity: Severity = Severity.WARNING
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_blocking(self) -> bool:
        """Check if this result should block the response."""
        return self.status in (ValidationStatus.BLOCK, ValidationStatus.VIOLATION)

    def requires_rewrite(self) -> bool:
        """Check if this result requires a rewrite."""
        return (
            self.status in (ValidationStatus.WARNING, ValidationStatus.VIOLATION)
            and bool(self.suggested_rewrite)
        )

@dataclass
class Claim:
    """A claim extracted from an LLM response."""
    text: str
    span: tuple[int, int]  # (start, end) in response
    confidence: float

    def __post_init__(self):
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")

@dataclass
class FactualClaim(Claim):
    """A claim about factual matters (code, files, tests)."""
    claim_type: str = "factual"
    requires_verification: bool = True
    verification_source: Optional[str] = None  # Tool name or evidence source

@dataclass
class IntentClaim(Claim):
    """A claim about author intent or design rationale."""
    claim_type: str = "intent"
    claimed_intent: str = ""
    has_evidence: bool = False
    is_hedged: bool = False
    evidence_sources: List[str] = field(default_factory=list)

class BaseValidator(ABC):
    """
    Base class for all validators.

    Pattern: Guardrails Validator class with validate() method
    and on_fail actions.
    """

    name: str = "base_validator"
    description: str = ""

    @abstractmethod
    def validate(self, claim: Claim, context: "ValidationContext") -> ValidationResult:
        """
        Validate a claim.

        Args:
            claim: The claim to validate
            context: Validation context with tool logs, contract, etc.

        Returns:
            ValidationResult with status and optional rewrite suggestion
        """
        pass

    def can_validate(self, claim: Claim) -> bool:
        """Check if this validator can handle the given claim type."""
        return True

    def get_evidence_sources(self) -> List[str]:
        """Return list of evidence sources this validator uses."""
        return []
```

### 2.2 Intent Explanation Validator (`validators/intent_explanation.py`)

```python
"""
Intent Explanation Validator

Validates claims about author intent and design rationale.
Pattern: CPCE reasoning layer + Guardrails re-ask loop
"""

import re
from typing import List, Optional
from dataclasses import dataclass

from .base import BaseValidator, Claim, IntentClaim, ValidationResult, ValidationStatus, Severity

# Patterns for detecting intent explanations
INTENT_PATTERNS = [
    r"the author (added|wrote|designed|created|implemented) .+ because",
    r"this (was|is) (added|written|designed|created|implemented) to",
    r"the (reason|purpose|intent) .+ (is|was)",
    r"this pattern (was|is) chosen (for|to|because)",
    r"(presumably|likely|clearly) the author",
    r"the (developer|programmer|maintainer) (intended|wanted|meant)",
]

# Hedging patterns that indicate speculation
HEDGING_PATTERNS = [
    r"\b(may|might|could|possibly|perhaps)\b",
    r"\b(one possibility|it appears|seems|suggests|indicates)\b",
    r"\b(potentially|conceivably|arguably)\b",
]

@dataclass
class ValidationContext:
    """Context provided during validation."""
    tool_logs: List[Any]
    contract: Any
    cks_client: Optional[Any] = None
    response_text: str = ""

class IntentExplanationValidator(BaseValidator):
    """
    Validates claims about author intent and design rationale.

    Rules:
    1. Intent claims require evidence from comments/docs/issues OR
    2. Intent claims must use hedging language if no evidence
    3. Clear speculation (no hedging, no evidence) is a violation
    """

    name = "intent_explanation"
    description = "Validates author intent and design rationale claims"

    # Evidence sources to search
    EVIDENCE_SOURCES = {
        "comments": ["#", "//", "/*", "*", "<!--"],
        "docs": ["README", "DESIGN", "ARCHITECTURE", "CONTRIBUTING"],
        "issues": ["issue", "pull request", "PR"],
        "commits": ["git log", "commit message"],
    }

    def validate(self, claim: Claim, context: ValidationContext) -> ValidationResult:
        """Validate an intent explanation claim."""
        if not isinstance(claim, IntentClaim):
            claim = self._convert_to_intent_claim(claim)

        # Check for hedging
        is_hedged = self._has_hedging(claim.text)

        # Search for evidence
        evidence = self._search_evidence(claim, context)

        # Decision logic
        if evidence:
            return ValidationResult(
                status=ValidationStatus.PASS,
                message="Intent claim has supporting evidence",
                citations=[e.source for e in evidence],
                metadata={"evidence_count": len(evidence)}
            )

        if is_hedged:
            return ValidationResult(
                status=ValidationStatus.PASS,
                message="Speculation properly hedged",
                severity=Severity.INFO,
                metadata={"hedged": True}
            )

        # No evidence AND no hedging - violation
        suggested_rewrite = self._add_hedging(claim.text)
        return ValidationResult(
            status=ValidationStatus.WARNING,
            message=(
                "Author intent claim lacks evidence. "
                "Either cite source (comment/doc/issue) or use hedging language."
            ),
            suggested_rewrite=suggested_rewrite,
            severity=Severity.WARNING,
            metadata={"suggested_hedging": suggested_rewrite}
        )

    def can_validate(self, claim: Claim) -> bool:
        """Check if this is an intent claim."""
        text_lower = claim.text.lower()
        return any(re.search(pattern, text_lower, re.IGNORECASE) for pattern in INTENT_PATTERNS)

    def _convert_to_intent_claim(self, claim: Claim) -> IntentClaim:
        """Convert a Claim to an IntentClaim with extracted intent."""
        intent = self._extract_intent(claim.text)
        return IntentClaim(
            text=claim.text,
            span=claim.span,
            confidence=claim.confidence,
            claimed_intent=intent,
            is_hedged=self._has_hedging(claim.text)
        )

    def _has_hedging(self, text: str) -> bool:
        """Check if text contains hedging language."""
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in HEDGING_PATTERNS)

    def _extract_intent(self, text: str) -> str:
        """Extract the intent being claimed."""
        # Simplified extraction - returns the relevant clause
        for pattern in INTENT_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return text[match.start():]
        return text

    def _add_hedging(self, text: str) -> str:
        """Add hedging language to un-hedged intent claim."""
        # Common transformations
        hedging_prefixes = [
            "This may suggest that ",
            "It appears that ",
            "One possible explanation is that ",
        ]

        # Detect sentence start and add appropriate hedging
        for pattern in INTENT_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                # Find the actual claim
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    before = text[:match.start()]
                    after = text[match.start():]
                    return f"{before}{hedging_prefixes[0].lower()}{after[0].lower()}{after[1:]}"

        return f"{hedging_prefixes[0].lower()}{text[0].lower()}{text[1:]}"

    def _search_evidence(self, claim: IntentClaim, context: ValidationContext) -> List[Any]:
        """Search for evidence in tool logs and CKS."""
        evidence = []

        # Check tool logs for relevant reads
        for log in context.tool_logs:
            if hasattr(log, 'tool') and log.tool in ["Read", "Grep"]:
                if self._intent_mentioned(claim.claimed_intent, log):
                    evidence.append(type('Evidence', (), {
                        'source': log.tool,
                        'location': getattr(log, 'file_path', 'unknown'),
                        'content': getattr(log, 'output', '')[:200]
                    })())

        # Query CKS if available
        if context.cks_client:
            try:
                cks_results = context.cks_client.search(claim.claimed_intent, limit=5)
                for result in cks_results:
                    if self._is_relevant_intent(claim, result):
                        evidence.append(type('Evidence', (), {
                            'source': 'CKS',
                            'location': result.get('id', ''),
                            'content': result.get('content', '')[:200]
                        })())
            except Exception as e:
                # CKS query failed - continue without it
                pass

        return evidence

    def _intent_mentioned(self, intent: str, log: Any) -> bool:
        """Check if intent is mentioned in log output."""
        output = getattr(log, 'output', '')
        if not output:
            return False
        # Simple keyword matching
        intent_words = set(re.findall(r'\w+', intent.lower()))
        output_words = set(re.findall(r'\w+', str(output).lower()))
        return len(intent_words & output_words) >= 2

    def _is_relevant_intent(self, claim: IntentClaim, cks_result: dict) -> bool:
        """Check if CKS result is relevant to the intent claim."""
        content = cks_result.get('content', '').lower()
        claim_lower = claim.claimed_intent.lower()
        return any(word in content for word in re.findall(r'\w+', claim_lower)[:3])

    def get_evidence_sources(self) -> List[str]:
        """Return evidence sources for documentation."""
        return ["comments", "docs", "issues", "tool_logs", "cks"]
```

### 2.3 Factual Claim Validator (`validators/factual_claim.py`)

```python
"""
Factual Claim Validator

Validates factual claims about code, tests, and files.
Pattern: Manager/Verifier with tool logs as source of truth
"""

import re
from typing import List, Optional, Set
from dataclasses import dataclass
from enum import Enum

from .base import BaseValidator, Claim, FactualClaim, ValidationResult, ValidationStatus, Severity

class FactualClaimType(Enum):
    """Types of factual claims."""
    FUNCTION_EXISTS = "function_exists"
    TEST_EXISTS = "test_exists"
    FILE_EXISTS = "file_exists"
    CALL_GRAPH = "call_graph"
    BEHAVIOR = "behavior"
    UNCONDITIONAL = "unconditional"  # "all", "every", "never"

# Patterns for detecting factual claims
FACTUAL_PATTERNS = {
    FactualClaimType.FUNCTION_EXISTS: [
        r"(?:this function|the function \w+) (is never called|has no callers|is not used)",
        r"there (?:is|are) no (?:calls|references) to \w+",
        r"\w+ (?:is not|isn't) (?:called|referenced|used)",
    ],
    FactualClaimType.TEST_EXISTS: [
        r"(?:there is no|this doesn't have|no) (?:test|tests|spec|specs)",
        r"(?:untested|no test coverage|not covered by tests)",
        r"(?:lacks|missing) (?:test|tests|spec|specs)",
    ],
    FactualClaimType.FILE_EXISTS: [
        r"(?:there is no|this doesn't have|no) (?:file|module|class) (?:named )?",
        r"(?:the file|the module) \w+ (?:doesn't exist|is not present|is missing)",
    ],
    FactualClaimType.CALL_GRAPH: [
        r"(?:calls|invokes|uses) (?:only|just|merely)",
        r"(?:is called by|is invoked from|is used in)",
    ],
    FactualClaimType.BEHAVIOR: [
        r"(?:this function|the function \w+) (?:returns|yields|outputs|produces)",
        r"(?:when|if|once) \w+ (?:is called|is invoked|runs)",
    ],
    FactualClaimType.UNCONDITIONAL: [
        r"\b(?:all|every|each|any) .+ (?:function|class|method|variable)",
        r"\b(?:no|none|never|nothing|nowhere) .+ (?:function|class|method|call)",
    ],
}

class FactualClaimValidator(BaseValidator):
    """
    Validates factual claims about code, tests, and files.

    Rules:
    1. Factual claims must be backed by tool evidence
    2. Suggest appropriate tool for verification if no evidence
    3. Flag unconditional claims (all/never) for extra scrutiny
    """

    name = "factual_claim"
    description = "Validates factual claims about code and files"

    TOOL_SUGGESTIONS = {
        FactualClaimType.FUNCTION_EXISTS: "find_referencing_symbols or Grep",
        FactualClaimType.TEST_EXISTS: "Glob for test files (test_*.py, *_test.py, *.test.ts)",
        FactualClaimType.FILE_EXISTS: "Glob or ls",
        FactualClaimType.CALL_GRAPH: "find_referencing_symbols",
        FactualClaimType.BEHAVIOR: "Read the function code",
        FactualClaimType.UNCONDITIONAL: "Grep with careful pattern matching",
    }

    def validate(self, claim: Claim, context: "ValidationContext") -> ValidationResult:
        """Validate a factual claim."""
        if not isinstance(claim, FactualClaim):
            claim = self._convert_to_factual_claim(claim)

        claim_type = self._classify_factual_claim(claim.text)

        # Check for evidence in tool logs
        evidence = self._find_evidence_in_logs(claim, context.tool_logs)

        if evidence:
            return ValidationResult(
                status=ValidationStatus.PASS,
                message=f"Claim verified by {evidence['source']}",
                citations=[evidence['source']],
                metadata={"evidence": evidence}
            )

        # Special handling for unconditional claims
        if claim_type == FactualClaimType.UNCONDITIONAL:
            return ValidationResult(
                status=ValidationStatus.WARNING,
                message=(
                    "Unconditional claim (all/every/never) requires verification. "
                    "These claims are often incorrect."
                ),
                suggested_rewrite=self._add_qualification(claim.text),
                severity=Severity.WARNING,
                metadata={"claim_type": "unconditional"}
            )

        # No evidence - suggest verification
        suggested_tool = self.TOOL_SUGGESTIONS.get(claim_type, "appropriate search tool")
        suggested_action = self._suggest_verification_action(claim, claim_type)

        return ValidationResult(
            status=ValidationStatus.WARNING,
            message=(
                f"Factual claim requires verification. "
                f"Use {suggested_tool} to verify."
            ),
            suggested_action=suggested_action,
            severity=Severity.WARNING,
            metadata={"suggested_tool": suggested_tool}
        )

    def can_validate(self, claim: Claim) -> bool:
        """Check if this is a factual claim."""
        return self._classify_factual_claim(claim.text) is not None

    def _convert_to_factual_claim(self, claim: Claim) -> FactualClaim:
        """Convert a Claim to a FactualClaim."""
        claim_type = self._classify_factual_claim(claim.text)
        return FactualClaim(
            text=claim.text,
            span=claim.span,
            confidence=claim.confidence,
            claim_type=claim_type.value if claim_type else "factual",
            requires_verification=True
        )

    def _classify_factual_claim(self, text: str) -> Optional[FactualClaimType]:
        """Classify the type of factual claim."""
        text_lower = text.lower()

        for claim_type, patterns in FACTUAL_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return claim_type

        return None

    def _find_evidence_in_logs(self, claim: FactualClaim, tool_logs: List[Any]) -> Optional[dict]:
        """Search for supporting evidence in tool logs."""
        for log in tool_logs:
            if not hasattr(log, 'tool'):
                continue

            tool = log.tool
            output = str(getattr(log, 'output', ''))
            input_data = getattr(log, 'input', {})

            # Check if log supports the claim
            if self._log_supports_claim(claim.text, tool, output, input_data):
                return {
                    'source': tool,
                    'location': input_data.get('file_path', 'unknown'),
                    'content': output[:200]
                }

        return None

    def _log_supports_claim(self, claim_text: str, tool: str, output: str, input_data: dict) -> bool:
        """Check if a tool log supports the factual claim."""
        claim_lower = claim_text.lower()

        # Function existence claims
        if tool == "find_referencing_symbols" and "call" in claim_lower:
            return len(output) > 0 if "no" not in claim_lower else "[]'" not in output

        # Grep for existence
        if tool == "Grep":
            has_matches = "content" in output.lower() or len(output) > 100
            return has_matches if "no" not in claim_lower else not has_matches

        # Read for behavior
        if tool == "Read" and "behavior" in claim_lower or "return" in claim_lower:
            # Check if claimed elements appear in the read content
            claim_words = set(re.findall(r'\w+', claim_lower))
            content_words = set(re.findall(r'\w+', output.lower()))
            return len(claim_words & content_words) >= 2

        return False

    def _add_qualification(self, text: str) -> str:
        """Add qualification to unconditional claims."""
        # Transform "all X are Y" to "most X appear to be Y"
        qualifiers = {
            r"\ball\b": "many",
            r"\bevery\b": "most",
            r"\bnone\b": "few or no",
            r"\bnever\b": "rarely",
        }

        result = text
        for pattern, replacement in qualifiers.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        return result

    def _suggest_verification_action(self, claim: FactualClaim, claim_type: FactualClaimType) -> str:
        """Generate a verification action to add to the response."""
        actions = {
            FactualClaimType.FUNCTION_EXISTS: (
                "Let me verify this claim by searching for references to the function."
            ),
            FactualClaimType.TEST_EXISTS: (
                "Let me check for test files covering this code."
            ),
            FactualClaimType.FILE_EXISTS: (
                "Let me verify the file structure."
            ),
            FactualClaimType.CALL_GRAPH: (
                "Let me examine the call graph for this function."
            ),
            FactualClaimType.BEHAVIOR: (
                "Let me read the function code to verify this behavior."
            ),
            FactualClaimType.UNCONDITIONAL: (
                "Let me verify this claim with a comprehensive search."
            ),
        }

        return actions.get(claim_type, "Let me verify this claim.")

    def get_evidence_sources(self) -> List[str]:
        """Return evidence sources for documentation."""
        return ["tool_logs", "find_referencing_symbols", "Grep", "Glob", "Read"]
```

### 2.4 Decision Engine (`enforcement/decision_engine.py`)

```python
"""
Decision Engine for Enforcement

Decides whether to ALLOW, REWRITE, or BLOCK a response based on
verification results.

Pattern: Guardrails OnFail actions + Manager/Verifier orchestration
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from collections import Counter

from ..validators.base import ValidationResult, ValidationStatus, Severity

class Action(Enum):
    """Enforcement actions."""
    ALLOW = "allow"
    REWRITE = "rewrite"
    BLOCK = "block"

class EnforcementMode(Enum):
    """Enforcement strictness levels."""
    SOFT = "soft"      # Warnings + rewrites, no blocking
    HARD = "hard"      # Full enforcement including blocking

@dataclass
class EnforcementAction:
    """Action to take based on verification results."""
    action: Action
    explanation: str = ""
    rewritten_response: str = ""
    warnings: List[str] = field(default_factory=list)
    violations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

class DecisionEngine:
    """
    Decides enforcement action based on verification results.

    Decision Logic:
    1. CRITICAL severity -> always BLOCK (in HARD mode)
    2. ERROR severity -> BLOCK in HARD mode, REWRITE in SOFT mode
    3. WARNING severity -> REWRITE if suggested_rewrite available
    4. INFO severity -> always ALLOW (just log)
    """

    def __init__(self, mode: EnforcementMode = EnforcementMode.SOFT):
        self.mode = mode
        self.max_rewrites = 2

    def decide(
        self,
        results: List[ValidationResult],
        response: str,
        contract: Any
    ) -> EnforcementAction:
        """
        Decide what action to take based on verification results.

        Args:
            results: List of validation results
            response: Original LLM response
            contract: Active contract with enforcement settings

        Returns:
            EnforcementAction with decision and details
        """
        # Group results by severity
        by_severity = self._group_by_severity(results)

        # Count blocking issues
        blocking_count = (
            len(by_severity[Severity.CRITICAL]) +
            len(by_severity[Severity.ERROR])
        )

        # Check for hard blocks
        if self._should_block(by_severity):
            return EnforcementAction(
                action=Action.BLOCK,
                explanation=self._format_blocking_message(by_severity),
                violations=[r.message for r in results if r.is_blocking()],
                metadata={
                    "blocking_count": blocking_count,
                    "severity_breakdown": {s.name: len(v) for s, v in by_severity.items()}
                }
            )

        # Check for rewrites
        if self._should_rewrite(by_severity):
            rewritten = self._apply_rewrites(response, results)
            warnings = [r.message for r in results if r.requires_rewrite()]

            return EnforcementAction(
                action=Action.REWRITE,
                explanation=f"Applied {len([r for r in results if r.requires_rewrite()])} rewrites for compliance.",
                rewritten_response=rewritten,
                warnings=warnings,
                metadata={
                    "rewrite_count": len([r for r in results if r.requires_rewrite()]),
                    "warnings": warnings
                }
            )

        # Allow with info if any
        info_messages = [r.message for r in results if r.severity == Severity.INFO]
        return EnforcementAction(
            action=Action.ALLOW,
            warnings=info_messages,
            metadata={"all_passed": True}
        )

    def _group_by_severity(self, results: List[ValidationResult]) -> Dict[Severity, List[ValidationResult]]:
        """Group validation results by severity."""
        grouped = {severity: [] for severity in Severity}
        for result in results:
            grouped[result.severity].append(result)
        return grouped

    def _should_block(self, by_severity: Dict[Severity, List[ValidationResult]]) -> bool:
        """Determine if response should be blocked."""
        if self.mode == EnforcementMode.SOFT:
            # Soft mode only blocks on CRITICAL
            return len(by_severity[Severity.CRITICAL]) > 0

        # Hard mode blocks on CRITICAL and ERROR
        return (
            len(by_severity[Severity.CRITICAL]) > 0 or
            len(by_severity[Severity.ERROR]) > 0
        )

    def _should_rewrite(self, by_severity: Dict[Severity, List[ValidationResult]]) -> bool:
        """Determine if response should be rewritten."""
        rewrite_candidates = (
            by_severity[Severity.WARNING] +
            (by_severity[Severity.ERROR] if self.mode == EnforcementMode.SOFT else [])
        )
        return any(r.suggested_rewrite for r in rewrite_candidates)

    def _format_blocking_message(self, by_severity: Dict[Severity, List[ValidationResult]]) -> str:
        """Format a user-facing blocking message."""
        issues = []

        if by_severity[Severity.CRITICAL]:
            issues.append(f"{len(by_severity[Severity.CRITICAL])} critical issue(s)")

        if by_severity[Severity.ERROR]:
            issues.append(f"{len(by_severity[Severity.ERROR])} error(s)")

        return (
            f"Response blocked due to: {', '.join(issues)}. "
            "Please revise to address these issues before proceeding."
        )

    def _apply_rewrites(self, response: str, results: List[ValidationResult]) -> str:
        """
        Apply suggested rewrites to the response.

        Applies rewrites from end to start to maintain correct positions.
        """
        # Filter results that have rewrites
        rewrite_results = [r for r in results if r.suggested_rewrite]

        if not rewrite_results:
            return response

        # Sort by position (end to start) for correct replacement
        # Assuming claims have span information
        rewrite_results.sort(key=lambda r: getattr(r, 'position', [0, 0])[1], reverse=True)

        rewritten = response
        for result in rewrite_results:
            if hasattr(result, 'original_text') and result.suggested_rewrite:
                rewritten = rewritten.replace(
                    result.original_text,
                    result.suggested_rewrite,
                    1  # Replace only first occurrence
                )

        return rewritten
```

---

## 3. Hook Integration

### 3.1 Stop Hook Implementation (`hooks/Stop.py`)

```python
"""
Stop Hook: Claim Verification and Enforcement

Runs after LLM generates response but before showing to user.
Performs claim extraction, validation, and enforcement.

Pattern: Manager/Verifier loop + CPCE reasoning layer
"""

import sys
import os

# Add guardrail_layer to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'guardrail_layer'))

from claim_extractor import ClaimExtractor
from validators.intent_explanation import IntentExplanationValidator, ValidationContext
from validators.factual_claim import FactualClaimValidator
from enforcement.decision_engine import DecisionEngine, EnforcementMode, Action
from contracts.registry import ContractRegistry

@stop_hook
def verify_claims_and_intents(response: str, context: StopContext) -> StopAction:
    """
    Stop hook that validates claims and enforces contracts.

    Args:
        response: The LLM's generated response
        context: Stop context with tool logs, session info, etc.

    Returns:
        StopAction: allow(), modify(), or block()
    """

    # Check if guardrail layer is enabled
    if not context.config.get("guardrail_layer_enabled", True):
        return StopAction.allow()

    # Get enforcement mode
    mode_str = context.config.get("enforcement_mode", "soft")
    mode = EnforcementMode.HARD if mode_str == "hard" else EnforcementMode.SOFT

    # Get contract for task type
    task_type = detect_task_type(context.prompt, context.tool_logs)
    contract = ContractRegistry.get_contract(task_type)

    # Layer 3: Claim Extraction
    extractor = ClaimExtractor()
    claims = extractor.extract(response)

    if not claims:
        return StopAction.allow()

    # Layer 4: Verification
    validators = get_validators_for_contract(contract)
    validation_context = ValidationContext(
        tool_logs=context.tool_logs,
        contract=contract,
        cks_client=get_cks_client(),
        response_text=response
    )

    results = []
    for claim in claims:
        for validator in validators:
            if validator.can_validate(claim):
                result = validator.validate(claim, validation_context)
                results.append(result)

    # Layer 5: Enforcement
    engine = DecisionEngine(mode=mode)
    action = engine.decide(results, response, contract)

    # Handle the enforcement action
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

    if action.warnings:
        # Allow but show warnings
        return StopAction.allow(warnings=action.warnings)

    return StopAction.allow()


def detect_task_type(prompt: str, tool_logs: list) -> str:
    """Detect the type of task from prompt and tool usage."""
    prompt_lower = prompt.lower()

    if any(word in prompt_lower for word in ["explain", "what does", "how does"]):
        return "code_explanation"

    if any(word in prompt_lower for word in ["refactor", "clean up", "improve"]):
        return "refactor"

    if any(word in prompt_lower for word in ["fix", "debug", "error"]):
        return "bug_fix"

    if any(word in prompt_lower for word in ["investigate", "find", "search"]):
        return "investigation"

    return "general"


def get_validators_for_contract(contract: Any) -> list:
    """Get validators specified in the contract."""
    validators = [
        IntentExplanationValidator(),
        FactualClaimValidator(),
    ]

    # Filter based on contract configuration
    enabled_validators = contract.get("enabled_validators", validators)
    return enabled_validators


def get_cks_client():
    """Get CKS client for evidence search."""
    try:
        from cks import CKSClient
        return CKSClient()
    except ImportError:
        return None
```

### 3.2 PostToolUse Enhancement (`hooks/PostToolUse.py`)

```python
"""
PostToolUse Hook: Evidence Collection

Collects evidence from tool runs for use in verification.
"""

@post_tool_use_hook
def collect_evidence(tool_result: ToolResult, context: PostToolUseContext):
    """
    Collect evidence from tool runs for later verification.
    """
    # Store tool results in context for Stop hook to use
    if not hasattr(context, 'evidence_store'):
        context.evidence_store = []

    # Extract relevant information
    evidence = {
        'tool': tool_result.tool,
        'input': tool_result.input,
        'output': tool_result.output,
        'timestamp': tool_result.timestamp,
    }

    context.evidence_store.append(evidence)
```

### 3.3 UserPromptSubmit Enhancement (`hooks/UserPromptSubmit.py`)

```python
"""
UserPromptSubmit Hook: Contract Loading and Prompt Enhancement

Enhances prompt with contract-based guidance.
"""

@user_prompt_submit_hook
def load_contract_and_enhance(prompt: str, context: UserPromptSubmitContext) -> str:
    """
    Load applicable contract and enhance prompt with guidance.
    """
    # Detect task type
    task_type = detect_task_type_from_prompt(prompt)

    # Load contract
    contract = ContractRegistry.get_contract(task_type)

    if not contract or contract.get("skip_enhancement", False):
        return prompt

    # Add guidance based on contract
    guidance = contract.get("prompt_guidance", "")

    if guidance:
        enhanced = f"""{prompt}

---
**Response Guidelines:**
{guidance}
"""
        return enhanced

    return prompt
```

---

## 4. Testing Strategy

### 4.1 Unit Tests (`tests/guardrail_layer/test_validators.py`)

```python
"""
Unit tests for validators
"""

import pytest
from hooks.guardrail_layer.validators.intent_explanation import IntentExplanationValidator, ValidationContext, IntentClaim, ValidationResult, ValidationStatus
from hooks.guardrail_layer.validators.factual_claim import FactualClaimValidator

class TestIntentExplanationValidator:
    """Tests for IntentExplanationValidator."""

    def test_detects_intent_claim(self):
        """Test detection of intent claims."""
        validator = IntentExplanationValidator()
        claim = Claim(text="The author added this function to handle edge cases.", span=(0, 50), confidence=0.9)

        assert validator.can_validate(claim)

    def test_hedged_claim_passes(self):
        """Test that properly hedged claims pass."""
        validator = IntentExplanationValidator()
        claim = IntentClaim(
            text="This may suggest the author added this for performance.",
            span=(0, 60),
            confidence=0.9,
            is_hedged=True
        )
        context = ValidationContext(tool_logs=[], contract=None)

        result = validator.validate(claim, context)

        assert result.status == ValidationStatus.PASS

    def test_unhedged_claim_without_evidence_fails(self):
        """Test that unhedged claims without evidence fail."""
        validator = IntentExplanationValidator()
        claim = IntentClaim(
            text="The author added this to handle edge cases.",
            span=(0, 45),
            confidence=0.9,
            is_hedged=False,
            has_evidence=False
        )
        context = ValidationContext(tool_logs=[], contract=None)

        result = validator.validate(claim, context)

        assert result.status == ValidationStatus.WARNING
        assert result.suggested_rewrite

    def test_adds_hedging_to_unhedged_claim(self):
        """Test that validator can add hedging."""
        validator = IntentExplanationValidator()

        original = "The author added this function to improve performance."
        hedged = validator._add_hedging(original)

        assert "may" in hedged.lower() or "appears" in hedged.lower() or "suggests" in hedged.lower()

class TestFactualClaimValidator:
    """Tests for FactualClaimValidator."""

    def test_detects_function_existence_claim(self):
        """Test detection of function existence claims."""
        validator = FactualClaimValidator()
        claim = Claim(text="This function is never called anywhere.", span=(0, 35), confidence=0.9)

        assert validator.can_validate(claim)

    def test_detects_unconditional_claim(self):
        """Test detection of unconditional (all/never) claims."""
        validator = FactualClaimValidator()
        claim = Claim(text="All functions in this module use this pattern.", span=(0, 50), confidence=0.9)

        assert validator.can_validate(claim)

    def test_adds_qualification_to_unconditional(self):
        """Test that validator adds qualification to unconditional claims."""
        validator = FactualClaimValidator()

        original = "All functions use this pattern."
        qualified = validator._add_qualification(original)

        assert "all" not in qualified.lower()
        assert "many" in qualified.lower() or "most" in qualified.lower()
```

### 4.2 Integration Tests

```python
"""
Integration tests for full guardrail pipeline
"""

import pytest
from hooks.guardrail_layer.claim_extractor import ClaimExtractor
from hooks.guardrail_layer.validators.intent_explanation import IntentExplanationValidator, ValidationContext
from hooks.guardrail_layer.enforcement.decision_engine import DecisionEngine, EnforcementMode

class TestGuardrailPipeline:
    """Integration tests for the full pipeline."""

    def test_full_pipeline_with_intent_violation(self):
        """Test full pipeline with an intent violation."""
        response = "The author added this function to improve performance. The implementation uses caching."

        # Extract claims
        extractor = ClaimExtractor()
        claims = extractor.extract(response)

        # Validate
        validator = IntentExplanationValidator()
        context = ValidationContext(tool_logs=[], contract=None)

        results = []
        for claim in claims:
            if validator.can_validate(claim):
                result = validator.validate(claim, context)
                results.append(result)

        # Decide
        engine = DecisionEngine(mode=EnforcementMode.SOFT)
        from hooks.guardrail_layer.validators.base import Claim
        contract = type('Contract', (), {'get_severity': lambda x: 'warning'})()
        action = engine.decide(results, response, contract)

        assert action.action == Action.REWRITE
        assert action.warnings

    def test_soft_mode_allows_with_warning(self):
        """Test that soft mode allows responses with warnings."""
        response = "This may suggest the author intended this for error handling."

        # Should pass due to hedging
        extractor = ClaimExtractor()
        claims = extractor.extract(response)

        validator = IntentExplanationValidator()
        context = ValidationContext(tool_logs=[], contract=None)

        results = []
        for claim in claims:
            if validator.can_validate(claim):
                result = validator.validate(claim, context)
                results.append(result)

        engine = DecisionEngine(mode=EnforcementMode.SOFT)
        contract = type('Contract', (), {'get_severity': lambda x: 'warning'})()
        action = engine.decide(results, response, contract)

        assert action.action == Action.ALLOW
```

---

## 5. Deployment Checklist

### Phase 1: Setup
- [ ] Create directory structure
- [ ] Implement base classes
- [ ] Set up configuration files
- [ ] Create sample contracts

### Phase 2: Core Implementation
- [ ] Implement ClaimExtractor
- [ ] Implement IntentExplanationValidator
- [ ] Implement FactualClaimValidator
- [ ] Implement DecisionEngine

### Phase 3: Hook Integration
- [ ] Implement Stop.py hook
- [ ] Enhance PostToolUse.py
- [ ] Enhance UserPromptSubmit.py
- [ ] Add contract loading

### Phase 4: Testing
- [ ] Write unit tests for all validators
- [ ] Write integration tests for pipeline
- [ ] Test with sample prompts
- [ ] Measure false positive rate

### Phase 5: Deployment
- [ ] Deploy in soft mode with logging
- [ ] Monitor metrics for 1 week
- [ ] Collect user feedback
- [ ] Adjust thresholds based on data

### Phase 6: Hard Mode Rollout
- [ ] Enable hard mode for opt-in users
- [ ] Monitor block rate and user satisfaction
- [ ] Iterate on based on feedback

---

**End of Implementation Guide**

For questions or issues, refer to the main architecture document:
`P:/__csf/docs/design/guardrail_architecture_design.md`
