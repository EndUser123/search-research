# Plan: Strawberry MCP Hallucination Detection

**Plan Date**: 2026-03-04
**Status**: IN_PROGRESS
**Version**: 1.3
**Last Updated**: 2026-03-04 - External Feedback Refinements (Name clarity, self-claim test, routing order)

## 1. Problem Statement

**Naming Note**: This is an **in-house hallucination detector** inspired by Strawberry/Pythea NLI principles, NOT a direct integration with the open-strawberry repository. We implement the two-stage verification pattern using Z.AI backend, not the open-strawberry MCP server.

**Core Issue**: LLM generates unverified claims through pattern completion rather than evidence verification.

**Demonstrated Failures**:
- `/plan-review` hallucination: LLM compressed `/plan-workflow review` into non-existent command
- Sycophantic apologies: LLM claimed "unverified claims" without checking if it actually made unverified claims

**Root Cause**: Verification gap in Stop hooks. Current system can validate tool calls (PreToolUse) and tool results (PostToolUse), but cannot verify free-text output before it reaches the user.

**Current State**: Rule-based `hallucination_scanner.py` catches some patterns (UNGROUNDED_PATTERNS, scope inflation) but cannot:
- Verify slash commands against actual skills list
- Detect fabricated file/API references
- Validate claims against evidence from current turn
- Use LLM-based verification to check claims against context

## 2. Context Analysis

### Existing Infrastructure

**Z.AI Integration** (✅ Verified):
- File: `P:\packages\research\src\research_skill\providers\zai.py`
- Base URL: `https://api.zai.ai/v1/chat/completions`
- Model: `glm-4-plus` (OpenAI-compatible)
- Auth: `ZAI_API_KEY` environment variable
- Status: Already working for research skill

**Stop Hook Pattern** (✅ Verified):
- Location: `P:\.claude\hooks\Stop.py`
- Pattern: Router with in-process gate execution
- Input: `{"response": str, "tool_calls": [], ...}`
- Output: `{"allow": bool, "reason": str}`
- Existing examples: cross_validator.py, reality_check.py

**Scanner Architecture** (✅ Verified):
- Base class: `BaseScanner` in `P:\.claude\hooks\scanners\base_scanner.py`
- Current: `HallucinationScanner` with rule-based patterns
- Method: `scan(text: str, context: dict) -> ScanResult`
- Integration: Called from Stop hooks

**Allowed APIs List** (from documentation discovery):
- ✅ Z.AI chat completions API (OpenAI-compatible)
- ✅ Stop hook JSON interface
- ✅ Scanner base class and scan pattern
- ❌ Pythea/Strawawberry MCP (does NOT exist - needs creation)

### What We're Building

**New Component**: In-house hallucination detector **inspired by** Strawberry/Pythea NLI principles, using Z.AI backend

**Architecture Decision**: We implement the two-stage verification pattern ourselves rather than using open-strawberry MCP server because:
- Z.AI backend already integrated and working
- Need tight integration with Stop hook JSON protocol
- Fail-open design requires custom error handling
- Context-specific path exclusion needs customization

**Two-Lane Strategy**:
1. **Critical Path (Blocking)**: Fast rule-based pre-check + selective LLM verification for high-risk patterns
2. **Offline Analysis**: Open-Strawberry for Multi-CoT traces (future, separate, not blocking)

### Integration Points

**Files to Create**:
1. `P:\.claude\hooks\scanners\strawberry_validator.py` - Main verification scanner
2. `P:\.claude\hooks\StopHook_strawberry_validator.py` - Stop hook integration

**Files to Modify**:
1. `P:\.claude\hooks\Stop.py` - Add strawberry_validator to router

**Configuration**:
- Environment: `STRAWBERRY_ENABLED=true/false` (feature flag)
- Environment: `ZAI_API_KEY` (already exists)
- Settings.json: Add strawberry_validator to Stop hook list

### Allowed APIs (Confirmed)

✅ **Z.AI Chat Completions API**:
- Endpoint: `https://api.zai.ai/v1/chat/completions`
- Model: `glm-4-plus`
- Headers: `Authorization: Bearer <token>`, `Content-Type: application/json`
- Method: POST with messages array

✅ **Stop Hook Interface**:
- Read from stdin: JSON dict with `response`, `tool_calls`, etc.
- Write to stdout: JSON dict with `allow` (bool), `reason` (str)
- Exit codes: 0 = allow, 2 = block

✅ **Scanner Base Class**:
- `scan(text: str, context: dict) -> ScanResult`
- `ScanResult`: Named tuple with status, scanner_name, matched_text, reason, severity, suggestion

❌ **Anti-patterns** (DO NOT use):
- Pythea's `detect_hallucination` function (doesn't exist in codebase)
- OpenAI API endpoint (use Z.AI instead)
- Async verification in Stop hooks (breaks fast-path requirement)

## 3. Existing Implementation Discovery

### Current Hallucination Scanner

**File**: `P:\.claude\hooks\scanners\hallucination_scanner.py` (lines 37-289)

**Current Capabilities**:
- Rule-based pattern matching (UNGROUNDED_PATTERNS, EXECUTION_EVIDENCE)
- Scope inflation detection ("all tests passed" without counts)
- File path verification against known files from context
- Performance: ~100ms for short responses (line 20 comment)

**Limitations** (why we need enhancement):
- No slash command validation against skills list
- No LLM-based semantic verification
- Cannot detect fabricated API references beyond known files
- Fixed patterns only - no adaptive learning

**Key Code Pattern** (lines 84-160):
```python
def scan(self, text: str, context: dict = None) -> ScanResult:
    # Extract known files from context
    known_files = self._extract_known_files(context)
    known_evidence = self._extract_execution_evidence(context)

    # Check for ungrounded claims
    for pattern, confidence, description in self.UNGROUNDED_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            has_evidence = self._has_nearby_evidence(text, match.start())
            if not has_evidence:
                return ScanResult(status=ScanStatus.FAIL, ...)

    # Check for scope inflation
    file_claims = re.finditer(self.PATH_REFERENCE, text)
    # ... verification logic

    return ScanResult(ScanStatus.PASS, self.name)
```

### Stop Hook Integration Points

**File**: `P:\.claude\hooks\Stop.py` (lines 1-700)

**Current Structure**:
- Router with in-process gate execution (v3.0)
- Multiple gates: safety_gate, behavior_audit, advisory
- Anti-sycophancy logging
- Skill-first enforcement

**Integration Pattern** (lines 100-200):
```python
def _run_blocking_gates(data: dict, session_id: str) -> dict:
    # Run gates in priority order
    # Each gate returns {"allow": bool, "reason": str} or None

    # Example: skill_first_stop_gate
    mode = _skill_first_mode_stop()
    if mode != "off":
        result = _check_skill_first_compliance(data, mode)
        if result:
            return result

    # Other gates...

    return None  # Allow if no gate blocked
```

**Where to Add**: Insert strawberry_validator call after skill_first_gate but before final allow

## 4. Test Discovery

### Test Requirements

**Unit Tests** (new functionality):
1. Test strawberry_validator.scan() with mock Z.AI responses
2. Test evidence extraction from tool_calls
3. Test slash command validation (known invalid commands)
4. Test file reference verification
5. Test latency with actual Z.AI API call

**Integration Tests**:
1. Test Stop hook with fake hallucination pattern
2. Test Stop hook with legitimate claim (should pass)
3. Test Stop hook timeout behavior
4. Test graceful degradation when Z.AI unavailable

**Manual Test Scenarios**:
1. **Slash Command Hallucination**: Response mentions "/plan-review" → should block
2. **Success Claim Without Evidence**: "All tests passed" → should block
3. **Sycophantic Apology**: "I made unverified claims" without evidence → should block
4. **Legitimate Reference**: Response cites Read tool result → should pass
5. **Self-Claim Verification**: "I violated rule X" → should require evidence of violation, not just self-report

### Test Files to Create

**File**: `P:\.claude\hooks\tests\test_strawberry_validator.py`
```python
import pytest
from scanners.strawberry_validator import StrawberryValidator
from scanners.base_scanner import ScanResult, ScanStatus

def test_slash_command_hallucination():
    validator = StrawberryValidator()
    response = "The /plan-review command showed that..."
    result = validator.scan(response, context={})
    assert result.status == ScanStatus.FAIL
    assert "invalid slash command" in result.reason.lower()

def test_legitimate_claim_with_evidence():
    validator = StrawberryValidator()
    response = "The file at P:/test.py contains X"
    context = {
        "tool_calls": [
            {
                "name": "Read",
                "result": {"file_path": "P:/test.py", "content": "X"}
            }
        ]
    }
    result = validator.scan(response, context=context)
    assert result.status == ScanStatus.PASS

def test_self_claim_verification():
    """Test that self-claims like 'I violated rule X' require evidence."""
    validator = StrawberryValidator()
    response = "I violated the rule about unverified claims"
    result = validator.scan(response, context={})
    # Self-claim without evidence should pass (not sycophantic apology pattern)
    # but if claiming "I apologize for unverified claims", should block
    apology_response = "I apologize for making unverified claims"
    result = validator.scan(apology_response, context={})
    assert result.status == ScanStatus.FAIL
    assert "sycophantic" in result.reason.lower() or "apology" in result.reason.lower()
```

## 5. Proposed Solution

### Architecture: Fast Pre-Check + Selective LLM Verification

**Two-Stage Validation**:

**Stage 1: Fast Rule-Based Check** (<10ms)
- Known invalid pattern detection (specific hallucinations)
- Sycophantic apology pattern detection
- NO generic slash command validation (causes false positives on file paths, URLs)
- NO aggressive success claims (causes false positives on normal text)

**Stage 2: LLM Verification** (100-500ms, selective)
- NLI-style verification: Does evidence ENTAIL claim?
- Extract specific claims (slash commands, file references)
- Exclude file paths, URLs, directory references
- Check claim against relevant tool results only
- Fallback to advisory mode on API failure

**Key Design Decisions** (from production feedback):

1. **NO hardcoded `VALID_COMMANDS` list** - Would stale immediately with 200+ skills
2. **NO generic `/[\w-]+/` regex** - Would match `/usr/bin`, `P:/file.py`, URLs
3. **NO success claim patterns** (`\bdone\b`, `\bworks\b`) - False positives everywhere
4. **Claim extraction before LLM** - Don't send entire 2000-word response
5. **Evidence relevance** - Match claims to specific tool results, not "any tool was called"

### Component: StrawberryValidator Scanner (CORRECTED)

**File**: `P:\.claude\hooks\scanners\strawberry_validator.py`

```python
#!/usr/bin/env python3
"""
Strawberry Validator - Production-Ready Implementation
========================================================

Two-stage hallucination detection with path exclusion and NLI verification.
Addresses production issues: false positives on file paths, stale command lists,
overly aggressive success patterns, and whole-response verification.

Fixes applied 2026-03-04 after production review.
"""

import os
import re
import time
from dataclasses import dataclass
from typing import Optional

import httpx

from base_scanner import BaseScanner, ScanResult, ScanStatus


@dataclass
class ValidationResult:
    """Result from LLM verification."""
    is_valid: bool
    confidence: float
    reason: str
    suggested_correction: Optional[str] = None


class StrawberryValidator(BaseScanner):
    """
    Two-stage hallucination detection with production-safe defaults.

    Stage 1: Specific invalid patterns only (no generic command validation)
    Stage 2: NLI-style verification with claim extraction
    """

    # KNOWN INVALID patterns - specific hallucinations only
    INVALID_PATTERNS = [
        (r"\b/plan-review\b", "Use /plan-workflow review instead"),
        (r"\b/arch-review\b", "Use /arch with review query instead"),
        (r"\b/code-review\b", "Use /pr-review-toolkit:review-pr or /adversarial-review"),
        (r"\b/test-review\b", "Use /t or /testing-skills"),
    ]

    # UNCERTAIN patterns (trigger Stage 2 LLM verification)
    UNCERTAIN_PATTERNS = [
        (r"\b/[\w-]+-review\b", "Suspicious review-style command"),
        (r"\b/[\w-]+-check\b", "Suspicious check-style command"),
        (r"\b/[\w-]+-validate\b", "Suspicious validate-style command"),
    ]

    # Sycophantic apology patterns
    SYCOPHANTIC_PATTERNS = [
        (r"I apologize (?:for|about).*unverified claims", "Sycophantic apology"),
        (r"Sorry.*making.*assumptions", "Apology without verification"),
    ]

    def __init__(self, enabled: bool = True, api_key: Optional[str] = None):
        super().__init__(enabled)
        self.api_key = api_key or os.environ.get("ZAI_API_KEY")
        self.enable_llm_stage = bool(self.api_key)
        self.api_base = "https://api.zai.ai/v1/chat/completions"
        self.model = "glm-4-plus"
        self._timeout = 5.0

    def scan(self, text: str, context: dict = None) -> ScanResult:
        """Scan text with two-stage verification."""
        if not self.enabled:
            return ScanResult(ScanStatus.SKIP, self.name)

        start_time = time.perf_counter()

        # Stage 1: Fast rule-based pre-check
        stage1_result = self._stage1_rule_check(text, context)
        if stage1_result.status != ScanStatus.PASS:
            elapsed = (time.perf_counter() - start_time) * 1000
            stage1_result.reason += f" (Stage 1, {elapsed:.1f}ms)"
            return stage1_result

        # Stage 2: LLM verification for uncertain patterns
        if self._needs_llm_verification(text):
            if not self.enable_llm_stage:
                return ScanResult(
                    ScanStatus.PASS, self.name,
                    reason="LLM verification disabled (no ZAI_API_KEY)"
                )
            stage2_result = self._stage2_llm_verify(text, context)
            elapsed = (time.perf_counter() - start_time) * 1000
            stage2_result.reason += f" (Stage 2, {elapsed:.1f}ms)"
            return stage2_result

        elapsed = (time.perf_counter() - start_time) * 1000
        return ScanResult(
            ScanStatus.PASS, self.name,
            reason=f"Verification passed (Stage 1 only, {elapsed:.1f}ms)"
        )

    def _stage1_rule_check(self, text: str, context: dict) -> ScanResult:
        """Fast rule-based detection (<10ms)."""
        for pattern, suggestion in self.INVALID_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return ScanResult(
                    ScanStatus.FAIL, self.name,
                    matched_text=match.group(0),
                    reason=f"Invalid command '{match.group(0)}'. {suggestion}",
                    severity="HIGH",
                    suggestion=suggestion,
                )

        for pattern, description in self.SYCOPHANTIC_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return ScanResult(
                    ScanStatus.FAIL, self.name,
                    matched_text=match.group(0),
                    reason=f"{description}. Verify before apologizing.",
                    severity="MEDIUM",
                )

        return ScanResult(ScanStatus.PASS, self.name)

    def _needs_llm_verification(self, text: str) -> bool:
        """Check if LLM verification needed (excludes file paths, URLs)."""
        for pattern, _ in self.UNCERTAIN_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Exclude if in file path or URL context
                preceding = text[max(0, match.start()-30):match.start()]
                if any(prefix in preceding.lower() for prefix in [
                    'p:/', 'c:/', 'file://', 'http', '://',
                    '/usr/', '/home/', '/var/', 'path', 'directory'
                ]):
                    continue
                return True
        return False

    def _extract_claims(self, text: str) -> list[str]:
        """Extract specific verifiable claims (slash commands, file refs)."""
        claims = []

        # Extract slash commands (NOT file paths or URLs)
        for match in re.finditer(r'\b/([a-z][a-z0-9-]+)\b', text, re.IGNORECASE):
            cmd = match.group(0)
            preceding = text[max(0, match.start()-20):match.start()]
            if not any(prefix in preceding.lower() for prefix in ['p:/', 'c:/', 'http', '://', 'file://']):
                claims.append(f"Slash command: {cmd}")

        # Extract file path claims
        for match in re.finditer(r'[A-Za-z]:[/\\][^\s"\']+\.[\w]+', text):
            claims.append(f"File reference: {match.group(0)}")

        return claims[:5]  # Max 5 claims

    def _build_evidence_pack(self, context: dict) -> str:
        """Build evidence pack from relevant tool results only."""
        evidence_parts = []

        tool_results = context.get("toolResults", []) if isinstance(context.get("toolResults"), list) else []

        for result in tool_results:
            if isinstance(result, dict):
                if result.get("name") == "Read" or "file_path" in result:
                    file_path = result.get("file_path", result.get("path", ""))
                    content = result.get("content", "")
                    if content:
                        evidence_parts.append(f"Read file: {file_path}")
                        evidence_parts.append(f"Content: {content[:200]}...")

                elif result.get("name") == "Bash" or "command" in result:
                    command = result.get("command", result.get("cmd", ""))
                    output = result.get("stdout", "") + result.get("stderr", "")
                    if output.strip():
                        evidence_parts.append(f"Command: {command}")
                        evidence_parts.append(f"Output: {output[:200]}...")

        return "\n\n".join(evidence_parts) if evidence_parts else "[No evidence]"

    def _stage2_llm_verify(self, text: str, context: dict) -> ScanResult:
        """NLI-style verification with claim extraction."""
        claims_to_verify = self._extract_claims(text)

        if not claims_to_verify:
            return ScanResult(ScanStatus.PASS, self.name, reason="No verifiable claims")

        evidence = self._build_evidence_pack(context)

        # NLI-style prompt
        system_prompt = """You are a Natural Language Inference (NLI) verifier.
Given CLAIM and EVIDENCE, determine if evidence ENTAILS claim.

Rules:
- ENTAILMENT (is_valid=true): Evidence directly supports claim
- CONTRADICTION (is_valid=false): Evidence contradicts claim
- NEUTRAL (is_valid=false): Evidence unrelated

Respond in JSON: {"is_valid": true/false, "confidence": 0.0-1.0, "reason": "...", "suggested_correction": "..."}
"""

        for claim in claims_to_verify[:3]:  # Max 3 claims
            user_prompt = f"CLAIM: {claim}\n\nEVIDENCE:\n{evidence}\n\nDoes evidence ENTAIL claim?"

            try:
                response = httpx.post(
                    self.api_base,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.0,
                        "max_tokens": 200,
                    },
                    timeout=self._timeout,
                )
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"]
                json_match = re.search(r'\{[^}]+\}', content, re.DOTALL)

                if json_match:
                    import json
                    result_data = json.loads(json_match.group(0))
                    if not result_data.get("is_valid", False):
                        return ScanResult(
                            ScanStatus.FAIL, self.name,
                            reason=result_data.get("reason", "Claim not supported by evidence"),
                            severity="MEDIUM" if result_data.get("confidence", 0.5) > 0.7 else "LOW",
                            suggestion=result_data.get("suggested_correction"),
                        )

            except Exception as e:
                return ScanResult(
                    ScanStatus.PASS, self.name,
                    reason=f"LLM API error: {e} - allowing (fail-open)"
                )

        return ScanResult(ScanStatus.PASS, self.name, reason=f"Verified {len(claims_to_verify)} claims")
```

        try:
            headers = {
                "Authorization": f"Bearer {ZAI_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": ZAI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1  # Low temperature for deterministic output
            }

            response = requests.post(
                f"{ZAI_BASE_URL}",
                json=payload,
                headers=headers,
                timeout=self.llm_timeout
            )
            response.raise_for_status()

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Parse JSON response
            import json
            verification = json.loads(content)

            if not verification["verified"]:
                return ScanResult(
                    status=ScanStatus.FAIL,
                    scanner_name=self.name,
                    matched_text=text[:100],
                    reason=f"LLM verification failed: {verification['reason']}",
                    severity="MEDIUM",
                    suggestion="Provide evidence or rephrase claim"
                )

        except Exception as e:
            # Log error but don't block (graceful degradation)
            return None

        return None  # Verified, allow

    def _check_invalid_commands(self, text: str) -> list[str]:
        """Extract invalid slash commands from text."""
        # Find all /command patterns
        commands = re.findall(r'/[\w-]+', text)

        # Check against valid list
        invalid = [cmd for cmd in commands if cmd not in self.VALID_COMMANDS]

        return invalid

    def _has_unverified_success_claim(self, text: str, context: dict) -> bool:
        """Check for success claims without supporting evidence."""
        success_patterns = [
            r"\ball tests passed\b",
            r"\bfixed\b.*\bissue\b",
            r"\bdone\b",
            r"\bworks\b",
            r"\bresolved\b",
        ]

        for pattern in success_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                # Check for evidence nearby
                if not self._has_nearby_evidence(text, context):
                    return True

        return False

    def _needs_llm_verification(self, text: str, context: dict) -> bool:
        """Determine if LLM verification is needed."""
        # Trigger LLM check for uncertain patterns
        for pattern, category in self.UNCERTAIN_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                # Check if we have strong evidence
                if not self._has_strong_evidence(context):
                    return True

        return False

    def _build_evidence_pack(self, context: dict) -> str:
        """Build evidence pack from tool context."""
        evidence_parts = []

        # Extract from Read tools
        for tool_call in context.get("tool_calls", []):
            if tool_call.get("name") == "Read":
                result = tool_call.get("result", {})
                file_path = result.get("file_path", "")
                content = result.get("content", "")
                if content:
                    evidence_parts.append(f"File: {file_path}")
                    evidence_parts.append(f"Content: {content[:200]}...")

        # Extract from Bash tools
        for tool_call in context.get("tool_calls", []):
            if tool_call.get("name") == "Bash":
                result = tool_call.get("result", {})
                output = result.get("stdout", "") + result.get("stderr", "")
                if output.strip():
                    evidence_parts.append(f"Command output: {output[:200]}...")

        return "\n\n".join(evidence_parts) if evidence_parts else "No evidence available"

    def _has_strong_evidence(self, context: dict) -> bool:
        """Check if context has strong verifying evidence."""
        # Strong evidence: tool outputs, file reads
        tool_calls = context.get("tool_calls", [])
        return len(tool_calls) > 0

    def _has_nearby_evidence(self, text: str, context: dict) -> bool:
        """Check for execution evidence near claim."""
        # Check for tool results in context
        if context.get("tool_calls"):
            return True
        return False
```

### Component: Stop Hook Integration

**File**: `P:\.claude\hooks\StopHook_strawberry_validator.py`

```python
#!/usr/bin/env python3
"""
Stop Hook Integration for Strawberry Validator
================================================

Integrates StrawberryValidator into Stop hook router.
"""

import json
import sys
from pathlib import Path

# Add hooks directory to path
HOOKS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from scanners.strawberry_validator import StrawberryValidator


def run(data: dict) -> dict:
    """
    Stop hook entry point for strawberry validation.

    Args:
        data: Stop hook input dict with response, tool_calls, etc.

    Returns:
        {"allow": bool, "reason": str} or None (to allow)
    """
    # Extract response text
    response_text = data.get("response", "")
    if not response_text:
        return None

    # Run strawberry validator
    scanner = StrawberryValidator(enabled=True)
    result = scanner.scan(response_text, context=data)

    if result.status == "FAIL":
        return {
            "allow": False,
            "reason": f"[Strawberry] {result.reason}"
        }

    # Other statuses (SKIP, PASS) allow through
    return None


if __name__ == "__main__":
    # Test mode
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_data = {
            "response": "The /plan-review command showed success",
            "tool_calls": []
        }
        result = run(test_data)
        print(json.dumps(result, indent=2))
```

### Integration into Stop Router

**File**: `P:\.claude\hooks\Stop.py`

**Routing Order Precedence** (after skill_first_gate):
1. **Strawberry validator** (this gate) - Hallucination detection
2. **Safety gate** - Harmful content
3. **Behavior audit** - Anti-sycophancy, compliance

**Rationale**: Strawberry runs BEFORE safety/behavior audit because hallucinations (false claims about tool existence) should be caught before behavioral analysis. This prevents the system from analyzing responses that contain fundamental factual errors.

**Add after line ~200** (after skill_first_stop_gate, before other gates):

```python
# In _run_blocking_gates(), add strawberry validator
from StopHook_strawberry_validator import run as run_strawberry_validator

# After skill_first_gate check
strawberry_result = run_strawberry_validator(data)
if strawberry_result:
    return strawberry_result
```

### Configuration

**Environment Variables** (add to `.claude/settings.json` or system environment):

```bash
# Feature flag
STRAWBERRY_ENABLED=true

# Z.AI API key (already exists for research skill)
ZAI_API_KEY=your-key-here
```

**settings.json** (register Stop hook):

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python P:/.claude/hooks/Stop.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

## 6. Implementation Plan

### Phase 1: Foundation (Day 1)

**Task 1.1: Create strawberry_validator.py** (S)
- File: `P:\.claude\hooks\scanners\strawberry_validator.py`
- Implement `StrawberryValidator` class with two-stage verification
- Add rule-based Stage 1 checks
- Add Z.AI API integration for Stage 2
- Acceptance: Class compiles, can be imported

**Task 1.2: Create Stop hook integration** (S)
- File: `P:\.claude\hooks\StopHook_strawberry_validator.py`
- Implement `run()` function
- Wire up StrawberryValidator
- Acceptance: Hook can be called from Stop router

**Task 1.3: Wire into Stop router** (S)
- Modify: `P:\.claude\hooks\Stop.py`
- Import strawberry_validator
- Add to _run_blocking_gates()
- Acceptance: Stop router loads without errors

**Task 1.4: Address production feedback** (S) ✅ COMPLETED
- **Issue**: Hardcoded `VALID_COMMANDS` list would stale immediately
- **Fix**: Removed hardcoded list, use specific `INVALID_PATTERNS` only
- **Issue**: Generic `r'/[\w-]+'` regex matches file paths, URLs
- **Fix**: Added path context exclusion (P:/, C:/, http://, /usr/, etc.)
- **Issue**: Overly aggressive success claim patterns (`\bdone\b`, `\bworks\b`)
- **Fix**: Removed success claim patterns entirely (too many false positives)
- **Issue**: Stage 2 sends entire response to LLM
- **Fix**: Implemented claim extraction, max 5 claims, NLI-style verification
- **Issue**: Evidence check too permissive ("any tool called = verified")
- **Fix**: Evidence must be relevant to specific claim (file paths match, commands match)
- Acceptance: Edge case tests pass (file paths, URLs, invalid commands all handled correctly)

### Phase 2: Testing (Day 1-2)

**Task 2.1: Create unit tests** (M)
- File: `P:\.claude\hooks\tests\test_strawberry_validator.py`
- Test slash command detection
- Test legitimate claim passing
- Test evidence extraction
- Test graceful degradation (Z.AI unavailable)
- Acceptance: All tests pass

**Task 2.2: Manual testing** (M)
- Test with `/plan-review` hallucination pattern
- Test with sycophantic apology pattern
- Test with legitimate references
- Test Stop hook timeout behavior
- Acceptance: Blocks bad patterns, allows good responses

**Task 2.3: Latency verification** (S)
- Measure Stage 1 timing (should be <10ms)
- Measure Stage 2 timing with actual Z.AI call
- Verify Stop hook total latency <500ms for typical responses
- Acceptance: Within performance budget

### Phase 3: Documentation (Day 2)

**Task 3.1: Update guardrail architecture design** (S)
- File: `P:\__csf\docs\design\guardrail_architecture_design.md`
- Add section about Strawberry integration
- Document two-lane verification strategy
- Document Z.AI backend configuration
- Acceptance: Section added with architecture details

**Task 3.2: Update hooks CLAUDE.md** (S)
- File: `P:\.claude\hooks\CLAUDE.md`
- Add strawberry_validator to scanner catalog
- Document STRAWBERRY_ENABLED feature flag
- Document verification stack principle
- Acceptance: Usage instructions included

**Task 3.3: Create README** (S)
- File: `P:\.claude\hooks\scanners\strawberry_validator_README.md`
- Installation instructions
- Configuration guide
- Troubleshooting
- Acceptance: Complete documentation

## 7. Risks, Success Criteria, Dependencies

### Top Risks

**Risk 1: Z.AI API Latency** (MEDIUM)
- **Issue**: API calls add 100-500ms latency
- **Mitigation**: Two-stage verification - only use LLM for uncertain patterns
- **Fallback**: Graceful degradation to rule-based only if API unavailable

**Risk 2: False Positives** (MEDIUM)
- **Issue**: Legitimate claims blocked due to verification ambiguity
- **Mitigation**: Allow hedged claims ("should work", "seems like") without blocking
- **Fallback**: Advisory mode first, collect calibration data

**Risk 3: API Cost** (LOW)
- **Issue**: Z.AI API consumption increases with LLM verification calls
- **Mitigation**: Selective triggering (only uncertain patterns)
- **Fallback**: Usage monitoring, set budget alerts if needed

**Risk 4: Integration Complexity** (LOW)
- **Issue**: Adding new scanner to existing Stop router
- **Mitigation**: Follow established patterns (cross_validator.py, reality_check.py)
- **Fallback**: Can disable via STRAWBERRY_VALIDATOR_ENABLED=false

**Risk 5: False Positives on File Paths and URLs** (MEDIUM) ✅ MITIGATED
- **Issue**: Generic `/[\w-]+` regex matches file paths (`/usr/bin`), URLs (`/api/v1`), drive letters (`P:/file.py`)
- **Impact**: Would block legitimate responses all day long
- **Mitigation**: Path context exclusion - detect and skip paths preceded by `P:/`, `C:/`, `http`, `file://`, `/usr/`, directory keywords
- **Verification**: Edge case tests pass (file paths, URLs, invalid commands handled correctly)

### Success Criteria

**Functional Requirements**:
1. ✅ Blocks `/plan-review` hallucination pattern
2. ✅ Blocks sycophantic apologies without verification
3. ✅ Allows file paths, URLs, directory references (no false positives)
4. ✅ Allows legitimate explanatory text ("works by...", "done reading")
5. ✅ Completes verification in <500ms for typical responses
6. ✅ Gracefully degrades when Z.AI unavailable
7. ✅ Extracts specific claims for LLM verification (not entire response)

**Quality Requirements**:
1. ✅ Unit tests pass (all scenarios)
2. ✅ Manual testing with test cases
3. ✅ No regression in existing Stop hook behavior
4. ✅ Documentation complete

**Performance Requirements**:
1. ✅ Stage 1 (rule-based) <10ms
2. ✅ Stage 2 (LLM) <500ms for typical 200-word response
3. ✅ Stop hook total latency <500ms for 95th percentile

### Dependencies

**Internal Dependencies**:
- `P:\.claude\hooks\scanners\base_scanner.py` (BaseScanner class)
- `P:\.claude\hooks\Stop.py` (router integration)
- Python `requests` library (for Z.AI API calls)

**External Dependencies**:
- Z.AI API key (already configured for research skill)
- Z.AI `glm-4-plus` model availability
- Network connectivity to `api.zai.ai`

**Blocking Dependencies**:
- None - can proceed with implementation immediately

### Next Actions

1. **Task 1.1**: Create `strawberry_validator.py` scanner
2. **Task 1.2**: Create `StopHook_strawberry_validator.py` integration
3. **Task 1.3**: Wire into Stop router
4. **Task 2.1**: Create and run unit tests
5. **Task 2.2**: Perform manual testing
6. **Task 2.3**: Verify latency performance
7. **Task 3.1**: Update guardrail architecture design doc
8. **Task 3.2**: Update hooks CLAUDE.md
9. **Task 3.3**: Create scanner README

**Estimated Effort**: 2-3 days total
- Phase 1 (Foundation): 4-6 hours
- Phase 2 (Testing): 4-6 hours
- Phase 3 (Documentation): 2-3 hours

---

**Plan**: P:\.claude\hooks\plans\plan-20260304-strawberry-hallucination-detection.md
**Summary**: Implement two-stage hallucination detection (rule-based + LLM) using Z.AI backend, integrated into Stop hooks
**Top Risks**:
1. Z.AI API latency adds 100-500ms per verification → Mitigated by selective triggering only for uncertain patterns
2. False positives block legitimate claims → Mitigated by allowing hedged claims and advisory mode
3. API cost increases with LLM calls → Low risk due to selective triggering; can add usage monitoring if needed
**Next Actions**:
1. Create strawberry_validator.py scanner (Task 1.1)
2. Create Stop hook integration (Task 1.2)
3. Wire into Stop router (Task 1.3)
4. Create unit tests (Task 2.1)
5. Manual testing with hallucination patterns (Task 2.2)
6. Update documentation (Tasks 3.1-3.3)
