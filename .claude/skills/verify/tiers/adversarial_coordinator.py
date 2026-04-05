#!/usr/bin/env python3
"""
Adversarial Review Coordinator - 9-agent stress-test system.

Coordinates parallel dispatch of 7 specialized review agents plus
1 meta-analyzer (adversarial-critic) for comprehensive code review.

Uses Result Envelope pattern to prevent context overflow during
subagent adversarial review.
"""

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal


@dataclass
class ResultEnvelope:
    """Result envelope for subagent output to prevent context overflow.

    Attributes:
        status: Overall status ("done", "blocked", "retry")
        artifact: Relative path to output file with detailed results
        summary: ≤3 short lines — no code, no diffs
        metrics: Dictionary with artifact metadata (bytes, files read, etc.)
    """

    status: Literal["done", "blocked", "retry"]
    artifact: str
    summary: str
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "status": self.status,
            "artifact": self.artifact,
            "summary": self.summary,
            "metrics": self.metrics,
        }


class AdversarialCoordinator:
    """Coordinator for 9-agent adversarial review system.

    Dispatches 7 specialized reviewers in parallel, then runs
    adversarial-critic meta-analysis on their findings.

    Agents:
    1. adversarial-compliance: Specification violations, solo-dev constraints
    2. adversarial-performance: Bottlenecks, scalability concerns
    3. adversarial-quality: Maintainability, technical debt
    4. adversarial-security: Data exposure, access control
    5. adversarial-testing: Coverage gaps, brittle tests
    6. code-critic: General code review patterns
    7. qa-engineer: QA verification standards
    8. adversarial-critic: Meta-analysis (consensus, blind spots, bias, contradiction)
    """

    # The 7 specialized reviewers (excluding meta-analyzer)
    REVIEWER_AGENTS = [
        "adversarial-compliance",
        "adversarial-performance",
        "adversarial-quality",
        "adversarial-security",
        "adversarial-testing",
        "code-critic",
        "qa-engineer",
    ]

    # Meta-analyzer that processes reviewer results
    META_ANALYZER = "adversarial-critic"

    def __init__(self, artifact_dir: Path | None = None):
        """Initialize coordinator with artifact directory.

        Args:
            artifact_dir: Directory for storing agent result artifacts.
                         Defaults to project-scoped `.claude/artifacts/adversarial/{terminal_id}/`
        """
        if artifact_dir is None:
            # Use terminal-scoped artifacts directory for multi-terminal isolation
            project_root = self._find_project_root()
            terminal_id = self._get_terminal_id()
            artifact_dir = project_root / ".claude" / "artifacts" / "adversarial" / terminal_id

        self.artifact_dir = Path(artifact_dir)
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

        # Track all envelopes from a review run
        self.envelopes: dict[str, ResultEnvelope] = {}

    def _get_timestamp(self) -> str:
        """Get timestamp for artifact filenames."""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _get_terminal_id(self) -> str:
        """Get terminal ID for multi-terminal isolation.

        Uses WT_SESSION environment variable (Windows Terminal) or
        generates a fallback ID for multi-terminal safety.

        Returns:
            Terminal ID string (never empty)
        """
        # Priority 1: WT_SESSION (Windows Terminal - most reliable)
        wt_session = os.environ.get("WT_SESSION")
        if wt_session:
            # Use last 12 characters of WT_SESSION for brevity
            return f"wt_{wt_session[-12:]}"

        # Priority 2: Fallback to session-based ID
        # This ensures different terminals get different IDs

        hostname = os.environ.get("COMPUTERNAME", "localhost")
        pid = os.getpid()
        hash_input = f"{hostname}_{pid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        return f"term_{hashlib.md5(hash_input.encode()).hexdigest()[:12]}"

    def _find_project_root(self) -> Path:
        """Find the project root directory by searching for markers.

        Searches upward from CWD for common project markers:
        - .git directory
        - CLAUDE.md file
        - pyproject.toml file
        - .claude directory

        Returns:
            Path to project root (falls back to CWD if no markers found)
        """
        cwd = Path.cwd()
        markers = [".git", "CLAUDE.md", "pyproject.toml", ".claude"]

        # Search upward from CWD for project markers
        current = cwd
        while current != current.parent:
            for marker in markers:
                if (current / marker).exists():
                    return current
            current = current.parent

        # Fallback to CWD if no markers found
        return cwd

    def _create_review_prompt(
        self, agent_type: str, target_type: str, content: str, context: dict[str, Any]
    ) -> str:
        """Create context-aware review prompt for an agent.

        Args:
            agent_type: Type of agent (e.g., "adversarial-compliance")
            target_type: Type of target ("code" or "plan")
            content: Content to review
            context: Additional context (file paths, metadata, etc.)

        Returns:
            Prompt string for the agent
        """
        is_code = target_type == "code"
        target_label = "CODE" if is_code else "AN IMPLEMENTATION PLAN"
        review_focus = "code quality and logic" if is_code else "plan-level concerns"
        code_examples = (
            "- Logic errors, race conditions, resource leaks\n"
            "- Security vulnerabilities, data exposure"
        )
        plan_examples = (
            "- Missing required sections, solo-dev violations\n"
            "- Task dependency feasibility and risks"
        )

        # Agent-specific guidance
        agent_guidance = self._get_agent_guidance(agent_type, is_code)

        prompt = (
            f"You are reviewing {target_label} for verification purposes.\n\n"
            f"Apply your specialized lens ({agent_type}) to {review_focus}:\n"
            f"{code_examples if is_code else plan_examples}\n\n"
            f"{agent_guidance}\n\n"
            f"Target content:\n\n{content}\n\n"
            f"Context: {json.dumps(context, indent=2)}\n\n"
            f"IMPORTANT: Respond ONLY with valid JSON matching this schema:\n"
            f'{{"status": "pass"|"fail"|"skip", "findings": ["..."], "severity": "critical"|"high"|"medium"|"low"}}\n'
        )
        return prompt

    def _get_agent_guidance(self, agent_type: str, is_code: bool) -> str:
        """Get agent-specific guidance text.

        Args:
            agent_type: Type of agent
            is_code: Whether reviewing code or a plan

        Returns:
            Guidance text specific to the agent
        """
        guidance_map = {
            "adversarial-compliance": (
                "Check for:\n"
                "- Solo-dev constraints violations (no shared state, multi-terminal safety)\n"
                "- Specification violations (CLAUDE.md requirements, constitutional rules)\n"
                "- Missing required sections or documentation"
            ),
            "adversarial-performance": (
                "Check for:\n"
                "- Performance bottlenecks (inefficient loops, unnecessary I/O)\n"
                "- Scalability concerns (memory leaks, resource exhaustion)\n"
                "- Algorithmic complexity issues (O(n²) where O(n) possible)"
            ),
            "adversarial-quality": (
                "Check for:\n"
                "- Maintainability issues (code duplication, unclear names)\n"
                "- Technical debt indicators (TODO comments, temporary hacks)\n"
                "- Code organization (separation of concerns, modularity)"
            ),
            "adversarial-security": (
                "Check for:\n"
                "- Data exposure (sensitive data in logs, error messages)\n"
                "- Access control issues (missing authz checks)\n"
                "- Input validation (SQL injection, XSS, path traversal)"
            ),
            "adversarial-testing": (
                "Check for:\n"
                "- Test coverage gaps (uncovered code paths)\n"
                "- Brittle tests (implementation coupling, flaky assertions)\n"
                "- Missing edge case scenarios (boundary conditions, error paths)"
            ),
            "code-critic": (
                "Check for:\n"
                "- General code review patterns (readability, idioms)\n"
                "- Python/TypeScript best practices (per language standards)\n"
                "- Universal principles (DRY, YAGNI, separation of concerns)"
            ),
            "qa-engineer": (
                "Check for:\n"
                "- QA verification standards (acceptance criteria, validation)\n"
                "- Test completeness (positive/negative cases, edge cases)\n"
                "- Evidence quality (clear pass/fail criteria)"
            ),
        }

        return guidance_map.get(agent_type, "Apply your specialized lens to identify issues.")

    def _write_agent_artifact(
        self, agent_type: str, timestamp: str, content: dict[str, Any]
    ) -> str:
        """Write agent result to artifact file.

        Args:
            agent_type: Type of agent that produced the result
            timestamp: Timestamp for unique filename
            content: Result content to write

        Returns:
            Relative path to the created artifact file (from CWD)
        """
        filename = f"adversarial_{timestamp}_{agent_type}.json"
        artifact_path = self.artifact_dir / filename

        with open(artifact_path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2)

        # Return relative path from CWD for portability
        try:
            return str(artifact_path.relative_to(Path.cwd()))
        except ValueError:
            # If artifact_dir is not relative to CWD (e.g., temp dir in tests),
            # return the absolute path
            return str(artifact_path)

    def _create_summary_from_content(self, content: dict[str, Any]) -> str:
        """Create ≤3 line summary from agent result content.

        Args:
            content: Agent result content

        Returns:
            Summary string (≤3 lines, no code/diffs)
        """
        status = content.get("status", "unknown")
        findings = content.get("findings", [])
        severity = content.get("severity", "medium")

        finding_count = len(findings)
        if finding_count == 0:
            return f"Status: {status}, no findings"

        # Get first finding as representative (avoid code/diffs)
        first_finding = findings[0] if findings else "No specific issues"
        # Truncate long findings
        if len(first_finding) > 60:
            first_finding = first_finding[:57] + "..."

        return (
            f"Status: {status}, severity: {severity}, "
            f"{finding_count} finding(s). "
            f"Example: {first_finding}"
        )

    def dispatch_reviewers(
        self, target_type: str, content: str, context: dict[str, Any]
    ) -> dict[str, ResultEnvelope]:
        """Dispatch 7 specialized reviewers in parallel.

        NOTE: This is a stub implementation. The actual parallel dispatch
        requires the Agent tool which is only available in the Claude Code
        runtime environment. This method provides the interface and structure
        for integration.

        Args:
            target_type: Type of target ("code" or "plan")
            content: Content to review
            context: Additional context (file paths, metadata, etc.)

        Returns:
            Dictionary mapping agent names to their ResultEnvelope objects
        """
        timestamp = self._get_timestamp()
        envelopes = {}

        # In the actual Claude Code environment, this would use:
        # Agent(subagent_type=agent_type, prompt=review_prompt)
        # for each agent in a single message (parallel dispatch pattern)

        # For now, provide a mock implementation that creates envelopes
        # with placeholder results
        for agent_type in self.REVIEWER_AGENTS:
            # Create prompt for this agent
            prompt = self._create_review_prompt(agent_type, target_type, content, context)

            # Mock result (in actual use, this comes from Agent tool)
            mock_result = {
                "status": "pass",
                "findings": [],
                "severity": "low",
                "agent_type": agent_type,
                "timestamp": timestamp,
            }

            # Write artifact
            artifact_path = self._write_agent_artifact(agent_type, timestamp, mock_result)

            # Create envelope
            envelopes[agent_type] = ResultEnvelope(
                status="done",
                artifact=artifact_path,
                summary=self._create_summary_from_content(mock_result),
                metrics={
                    "agent_type": agent_type,
                    "timestamp": timestamp,
                    "artifact_bytes": len(json.dumps(mock_result)),
                },
            )

        self.envelopes.update(envelopes)
        return envelopes

    def run_meta_analysis(
        self, reviewer_envelopes: dict[str, ResultEnvelope], context: dict[str, Any]
    ) -> ResultEnvelope:
        """Run adversarial-critic meta-analysis on reviewer results.

        NOTE: This is a stub implementation. The actual meta-analysis
        requires the Agent tool with adversarial-critic subagent_type.

        Args:
            reviewer_envelopes: Results from the 7 reviewers
            context: Additional context

        Returns:
            ResultEnvelope with meta-analysis findings
        """
        timestamp = self._get_timestamp()

        # Collect summaries from all reviewers
        reviewer_summaries = {
            agent: envelope.summary for agent, envelope in reviewer_envelopes.items()
        }

        # In actual use, this would dispatch adversarial-critic agent:
        # Agent(
        #     subagent_type="adversarial-critic",
        #     prompt=f"Analyze these review results: {reviewer_summaries}"
        # )

        # Mock result
        mock_result = {
            "status": "pass",
            "consensus": "all reviewers agree",
            "blind_spots": [],
            "calibration": "consistent",
            "timestamp": timestamp,
        }

        artifact_path = self._write_agent_artifact("critic", timestamp, mock_result)

        envelope = ResultEnvelope(
            status="done",
            artifact=artifact_path,
            summary="Meta-analysis: consensus, no blind spots detected",
            metrics={
                "agent_type": "adversarial-critic",
                "timestamp": timestamp,
                "reviewers_analyzed": len(reviewer_envelopes),
                "artifact_bytes": len(json.dumps(mock_result)),
            },
        )

        self.envelopes["adversarial-critic"] = envelope
        return envelope

    def run_full_review(
        self, target_type: str, content: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Run complete 9-agent adversarial review.

        Args:
            target_type: Type of target ("code" or "plan")
            content: Content to review
            context: Additional context (file paths, metadata, etc.)

        Returns:
            Dictionary with:
                - envelopes: All 9 ResultEnvelope objects
                - summaries_only: List of summaries for main context
                - overall_status: Combined status from all agents
        """
        # Step 1: Dispatch 7 reviewers
        reviewer_envelopes = self.dispatch_reviewers(target_type, content, context)

        # Step 2: Run meta-analysis
        critic_envelope = self.run_meta_analysis(reviewer_envelopes, context)

        # Step 3: Extract summaries for main context
        summaries_only = [
            f"{agent}: {envelope.summary}" for agent, envelope in self.envelopes.items()
        ]

        # Step 4: Determine overall status
        all_statuses = [env.status for env in self.envelopes.values()]
        if any(s == "blocked" for s in all_statuses):
            overall_status = "blocked"
        elif any(s == "retry" for s in all_statuses):
            overall_status = "retry"
        else:
            overall_status = "done"

        return {
            "envelopes": self.envelopes,
            "summaries_only": summaries_only,
            "overall_status": overall_status,
            "timestamp": self._get_timestamp(),
            "artifact_dir": str(self.artifact_dir),
        }


# Convenience function for direct use
def adversarial_review(
    target_type: str,
    content: str,
    context: dict[str, Any] | None = None,
    artifact_dir: Path | None = None,
) -> dict[str, Any]:
    """Run adversarial review with default coordinator.

    Args:
        target_type: Type of target ("code" or "plan")
        content: Content to review
        context: Additional context (file paths, metadata, etc.)
        artifact_dir: Optional custom artifact directory

    Returns:
        Full review results with envelopes, summaries, and status
    """
    coordinator = AdversarialCoordinator(artifact_dir)
    return coordinator.run_full_review(
        target_type=target_type, content=content, context=context or {}
    )
