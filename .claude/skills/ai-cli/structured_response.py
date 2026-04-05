#!/usr/bin/env python3
"""
Structured response format for /ai-cli skill.

Provides consistent JSON schema for LLM responses with:
- Standardized metadata (response time, token usage, model info)
- Quality gate findings structure
- Error handling and partial results
- Multi-CLI aggregation metadata
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TokenUsage:
    """Token usage metrics."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def to_dict(self) -> dict[str, int]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SourceMetadata:
    """Metadata about the source of a finding."""

    cli_name: str
    model_id: str | None = None
    confidence: int = 0
    line_reference: str | None = None


@dataclass
class Finding:
    """A single finding extracted from LLM output."""

    category: str  # "bug", "security", "performance", "best_practice", etc.
    severity: str  # "critical", "high", "medium", "low", "info"
    title: str
    description: str
    location: str | None = None  # File path or code location
    code_snippet: str | None = None
    source: SourceMetadata | None = None
    confidence: int = 0
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        d = asdict(self)
        if self.source:
            d["source"] = asdict(self.source)
        return d


@dataclass
class CliResponse:
    """Standardized response from a single CLI."""

    cli_name: str
    model_id: str | None = None
    success: bool = True
    output: str = ""
    error: str | None = None
    response_time_ms: int = 0
    token_usage: TokenUsage = field(default_factory=TokenUsage)
    findings: list[Finding] = field(default_factory=list)
    raw_output: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        d = asdict(self)
        d["token_usage"] = self.token_usage.to_dict()
        d["findings"] = [f.to_dict() if isinstance(f, Finding) else f for f in self.findings]
        return d


@dataclass
class QualityGateResult:
    """Result from quality gate filtering."""

    enabled: bool = False
    input_count: int = 0
    output_count: int = 0
    min_confidence: int = 80
    rejection_reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class AggregatedResponse:
    """Aggregated response from multiple CLIs."""

    query: str
    timestamp: str
    cli_responses: dict[str, CliResponse] = field(default_factory=dict)
    consensus: str | None = None
    agreement_level: float = 0.0  # 0.0 to 1.0
    quality_gate: QualityGateResult = field(default_factory=QualityGateResult)
    total_response_time_ms: int = 0
    context_files: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        d = asdict(self)
        d["cli_responses"] = {
            k: v.to_dict() if isinstance(v, CliResponse) else v
            for k, v in self.cli_responses.items()
        }
        d["quality_gate"] = self.quality_gate.to_dict()
        return d

    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


def extract_token_usage(output: str) -> TokenUsage:
    """Extract token usage from CLI output.

    Args:
        output: Raw CLI output

    Returns:
        TokenUsage with extracted metrics
    """
    usage = TokenUsage()

    # Common patterns for token usage in CLI outputs
    patterns = [
        r"(\d+)\s*prompt?\s*tokens?",
        r"(\d+)\s*completion?\s*tokens?",
        r"total:\s*(\d+)\s*tokens?",
        r"tokens:\s*(\d+)",
    ]

    output_lower = output.lower()

    for pattern in patterns:
        matches = re.findall(pattern, output_lower)
        if matches:
            if "prompt" in pattern:
                usage.prompt_tokens = int(matches[0])
            elif "completion" in pattern:
                usage.completion_tokens = int(matches[0])
            elif "total" in pattern:
                usage.total_tokens = int(matches[0])

    # Calculate total if not present but prompt/completion are
    if usage.total_tokens == 0 and usage.prompt_tokens > 0 and usage.completion_tokens > 0:
        usage.total_tokens = usage.prompt_tokens + usage.completion_tokens

    return usage


def extract_model_id(output: str, cli_name: str) -> str | None:
    """Extract model ID from CLI output.

    Args:
        output: Raw CLI output
        cli_name: Name of the CLI

    Returns:
        Model ID if found, None otherwise
    """
    # Common patterns for model identification
    patterns = [
        r"model:\s*([\w/.\-]+)",
        r"using\s+model\s+([\w/.\-]+)",
        r"model_id['\"]?\s*[:=]\s*['\"]?([\w/.\-]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, output, re.IGNORECASE)
        if match:
            return match.group(1)

    # Known model defaults by CLI
    known_models = {
        "qwen": "qwen/qwen3-235b",
        "gemini": "gemini-2.0-flash-exp",
        "codex": "deepseek/deepseek-r1",
        "vibe": "mistral/mistral-large",
        "opencode": "chutes/moonshotai/Kimi-K2.5-TEE",
        "glm-flash": "glm-4.7-flash",
    }

    return known_models.get(cli_name)


def extract_findings_from_text(
    output: str, cli_name: str, model_id: str | None = None
) -> list[Finding]:
    """Extract structured findings from text output.

    Args:
        output: Raw CLI output
        cli_name: Name of the CLI
        model_id: Optional model ID

    Returns:
        List of Finding objects
    """
    findings = []

    # Pattern for findings with severity markers
    # Look for lines with: [SEVERITY] or SEVERITY: patterns
    severity_pattern = r"\[(critical|high|medium|low|info)\]|(critical|high|medium|low|info):\s*"

    lines = output.split("\n")
    current_severity = "medium"
    current_description = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for severity marker
        severity_match = re.search(severity_pattern, line, re.IGNORECASE)
        if severity_match:
            # Save previous finding if exists
            if current_description:
                findings.append(
                    Finding(
                        category="general",
                        severity=current_severity,
                        title=current_description[0][:100] if current_description else "Finding",
                        description=" ".join(current_description),
                        source=SourceMetadata(
                            cli_name=cli_name,
                            model_id=model_id,
                            confidence=50,  # Default confidence for text extraction
                        ),
                    )
                )
                current_description = []

            current_severity = severity_match.group(1) or severity_match.group(2)
            # Remove severity marker from line for description
            line = re.sub(severity_pattern, "", line, flags=re.IGNORECASE).strip()

        if line:
            current_description.append(line)

    # Save last finding
    if current_description:
        findings.append(
            Finding(
                category="general",
                severity=current_severity,
                title=current_description[0][:100] if current_description else "Finding",
                description=" ".join(current_description),
                source=SourceMetadata(
                    cli_name=cli_name,
                    model_id=model_id,
                    confidence=50,
                ),
            )
        )

    return findings


def extract_findings_from_json(
    json_output: str | dict, cli_name: str, model_id: str | None = None
) -> list[Finding]:
    """Extract structured findings from JSON output.

    Args:
        json_output: JSON string or dict
        cli_name: Name of the CLI (used for source metadata)
        model_id: Optional model ID (used for source metadata)

    Returns:
        List of Finding objects
    """
    findings = []

    # cli_name and model_id are used when building Finding objects below
    _ = cli_name, model_id  # Mark as intentionally used

    try:
        data = json.loads(json_output) if isinstance(json_output, str) else json_output
    except (json.JSONDecodeError, TypeError):
        return []

    # Handle different JSON structures
    # Structure 1: {"findings": [...]}
    if isinstance(data, dict) and "findings" in data:
        for f in data["findings"]:
            if isinstance(f, dict):
                findings.append(
                    Finding(
                        category=f.get("category", "general"),
                        severity=f.get("severity", "medium"),
                        title=f.get("title", "Finding"),
                        description=f.get("description", ""),
                        location=f.get("location"),
                        code_snippet=f.get("code_snippet"),
                        confidence=f.get("confidence", 50),
                        tags=f.get("tags", []),
                    )
                )

    # Structure 2: [{"type": "finding", ...}, ...]
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                findings.append(
                    Finding(
                        category=item.get("category", "general"),
                        severity=item.get("severity", "medium"),
                        title=item.get("title", item.get("message", "Finding")[:100]),
                        description=item.get("description", item.get("message", "")),
                        location=item.get("location"),
                        confidence=item.get("confidence", 50),
                    )
                )

    return findings


def build_structured_response(
    cli_name: str,
    output: str,
    error: str | None = None,
    response_time_ms: int = 0,
    success: bool = True,
) -> CliResponse:
    """Build a structured CliResponse from raw CLI output.

    Args:
        cli_name: Name of the CLI
        output: Raw output string
        error: Error message if any
        response_time_ms: Response time in milliseconds
        success: Whether the CLI call succeeded

    Returns:
        CliResponse with structured data
    """
    model_id = extract_model_id(output, cli_name)
    token_usage = extract_token_usage(output)

    # Try to extract findings from JSON first, then text
    findings = []
    try:
        findings = extract_findings_from_json(output, cli_name, model_id)
    except (json.JSONDecodeError, TypeError):
        findings = extract_findings_from_text(output, cli_name, model_id)

    return CliResponse(
        cli_name=cli_name,
        model_id=model_id,
        success=success,
        output=output[:10000] if len(output) > 10000 else output,  # Truncate large outputs
        error=error,
        response_time_ms=response_time_ms,
        token_usage=token_usage,
        findings=findings[:50],  # Limit to 50 findings
        raw_output=output,
        metadata={
            "output_length": len(output),
            "truncated": len(output) > 10000,
            "findings_count": len(findings),
        },
    )


def calculate_agreement_level(responses: list[CliResponse]) -> float:
    """Calculate agreement level between CLI responses.

    Args:
        responses: List of CliResponse objects

    Returns:
        Agreement level from 0.0 (no agreement) to 1.0 (full agreement)
    """
    if not responses:
        return 0.0

    if len(responses) == 1:
        return 1.0

    # Simple agreement based on output similarity
    # Compare first 500 chars of each output
    outputs = [r.output[:500] for r in responses if r.output]

    if not outputs:
        return 0.0

    # Count similar pairs
    similar_pairs = 0
    total_pairs = 0

    for i in range(len(outputs)):
        for j in range(i + 1, len(outputs)):
            total_pairs += 1
            # Simple similarity check: overlap ratio
            words_a = set(outputs[i].lower().split())
            words_b = set(outputs[j].lower().split())

            if not words_a or not words_b:
                continue

            intersection = words_a & words_b
            union = words_a | words_b
            similarity = len(intersection) / len(union)

            if similarity > 0.5:  # 50% similarity threshold
                similar_pairs += 1

    return similar_pairs / total_pairs if total_pairs > 0 else 0.0


def format_structured_output(
    responses: dict[str, dict[str, Any]],
    query: str,
    context_files: list[str],
    total_time_ms: int,
) -> AggregatedResponse:
    """Format structured output from raw CLI results.

    Args:
        responses: Raw results dict from run_parallel_llm
        query: Original query
        context_files: List of context files used
        total_time_ms: Total execution time

    Returns:
        AggregatedResponse with structured data
    """
    cli_responses = {}

    for cli_name, cli_data in responses.items():
        if not isinstance(cli_data, dict):
            continue

        output = cli_data.get("output", "")
        error = cli_data.get("error")
        response_time = cli_data.get("response_time_ms", 0)
        success = not bool(error)

        cli_response = build_structured_response(
            cli_name=cli_name,
            output=output,
            error=error,
            response_time_ms=response_time,
            success=success,
        )

        cli_responses[cli_name] = cli_response

    # Calculate agreement
    response_list = list(cli_responses.values())
    agreement = calculate_agreement_level(response_list)

    # Build consensus from most common elements
    consensus = None
    if agreement > 0.7 and response_list:
        # High agreement - use first successful response as consensus
        for r in response_list:
            if r.success and r.output:
                consensus = r.output[:500]
                break

    return AggregatedResponse(
        query=query,
        timestamp=datetime.now().isoformat(),
        cli_responses=cli_responses,
        consensus=consensus,
        agreement_level=agreement,
        total_response_time_ms=total_time_ms,
        context_files=context_files,
        metadata={
            "cli_count": len(cli_responses),
            "successful_clis": sum(1 for r in response_list if r.success),
            "failed_clis": sum(1 for r in response_list if not r.success),
            "total_findings": sum(len(r.findings) for r in response_list),
        },
    )
