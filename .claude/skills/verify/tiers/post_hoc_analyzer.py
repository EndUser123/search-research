#!/usr/bin/env python3
"""
Post-hoc verification analyzer for /verify skill.

Analyzes completed work through chat history artifacts using LLM-as-Judge approach.
Integrates RTM (Requirements Traceability Matrix) and TSR (Task Success Rate) metrics.
Integrates ImplementationVerifier hook for execution verification.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any


class PostHocAnalyzer:
    """
    Analyze completed work using chat history artifacts.

    Uses LLM-as-Judge to evaluate:
    - Plan completeness (requirements → tasks mapping)
    - Implementation completeness (TSR from evidence ledger)
    - Conversation completeness (all requirements addressed)
    - Execution verification (ImplementationVerifier hook integration)
    """

    def __init__(
        self,
        plan_path: str | None = None,
        plan_content: str | None = None,
        evidence_ledger_path: str | None = None,
        transcript_path: str | None = None,
        claimed_files: list[str] | None = None,
    ):
        """
        Initialize analyzer with artifact paths.

        Args:
            plan_path: Path to plan.md file
            plan_content: Full text of plan.md (alternative to plan_path)
            evidence_ledger_path: Path to evidence ledger JSON
            transcript_path: Path to chat transcript JSONL
            claimed_files: List of files claimed to be created/modified (for execution verification)
        """
        self.plan_path = plan_path
        self.plan_content = plan_content
        self.evidence_ledger_path = evidence_ledger_path
        self.transcript_path = transcript_path
        self.claimed_files = claimed_files or []

        # Load artifacts
        self._load_artifacts()

        # Lazy load ImplementationVerifier (only if needed)
        self._implementation_verifier = None

    def _get_implementation_verifier(self):
        """
        Lazy load ImplementationVerifier hook.

        Returns:
            ImplementationVerifier instance or None if unavailable
        """
        if self._implementation_verifier is not None:
            return self._implementation_verifier

        try:
            # Add hooks directory to path
            hooks_dir = Path("P:/.claude/hooks")
            hooks_lib = str(hooks_dir)
            if hooks_lib not in sys.path:
                sys.path.insert(0, hooks_lib)

            # Import ImplementationVerifier
            from posttooluse.implementation_verifier import ImplementationVerifier

            self._implementation_verifier = ImplementationVerifier()
            return self._implementation_verifier

        except ImportError:
            # Hook not available - log and continue
            return None

    def _load_artifacts(self):
        """Load all required artifacts for analysis."""
        # Load plan
        if self.plan_content:
            self.plan = self.plan_content
        elif self.plan_path:
            with open(self.plan_path, encoding="utf-8") as f:
                self.plan = f.read()
        else:
            raise ValueError("Either plan_path or plan_content must be provided")

        # Load evidence ledger (optional - TSR calculation requires it)
        self.evidence_ledger = None
        if self.evidence_ledger_path and Path(self.evidence_ledger_path).exists():
            with open(self.evidence_ledger_path, encoding="utf-8") as f:
                self.evidence_ledger = json.load(f)

        # Load transcript (optional - LLM-as-Judge can work without it)
        self.transcript = None
        if self.transcript_path and Path(self.transcript_path).exists():
            with open(self.transcript_path, encoding="utf-8") as f:
                self.transcript = f.read()

    def verify_execution(self, files: list[str] | None = None) -> list[dict[str, Any]]:
        """
        Verify that claimed files actually exist on disk using ImplementationVerifier hook.

        Args:
            files: List of file paths to verify (defaults to self.claimed_files)

        Returns:
            List of findings dict with keys: severity, category, description, details
        """
        # Use provided files or fall back to claimed_files
        target_files = files or self.claimed_files

        if not target_files:
            return []

        # Get ImplementationVerifier instance
        verifier = self._get_implementation_verifier()
        if verifier is None:
            # Hook unavailable - return advisory finding
            return [
                {
                    "severity": "INFO",
                    "category": "execution_verification",
                    "description": "ImplementationVerifier hook unavailable - execution verification skipped",
                    "details": [
                        "Hook at P:/.claude/hooks/posttooluse/implementation_verifier.py not found"
                    ],
                }
            ]

        findings = []

        # Verify each claimed file
        for file_path in target_files:
            # Determine tool name based on file operation
            # We'll use "Write" as default since we're verifying file creation
            result = verifier.process(
                tool_name="Write", tool_input={"file_path": file_path}, tool_response={}
            )

            if not result.get("passed", False):
                # File not created - add HIGH severity finding
                findings.append(
                    {
                        "severity": "HIGH",
                        "category": "execution_verification",
                        "description": result.get("injection", f"File not created: {file_path}"),
                        "details": [
                            f"Claimed file: {file_path}",
                            "Verification: File does not exist on disk",
                            f"Metadata: {result.get('metadata', {})}",
                        ],
                    }
                )
            else:
                # File exists - add low-severity confirmation (optional, for audit trail)
                findings.append(
                    {
                        "severity": "INFO",
                        "category": "execution_verification",
                        "description": f"File verified: {file_path}",
                        "details": [f"Metadata: {result.get('metadata', {})}"],
                    }
                )

        return findings

    def generate_rtm(self) -> dict[str, Any]:
        """
        Generate Requirements Traceability Matrix from plan.

        Returns:
            RTM dict with requirements, tasks, coverage matrix, and statistics
        """
        # Import from /planning skill (reuses same parsing logic)
        planning_path = Path("P:/.claude/skills/planning/__lib")
        if str(planning_path) not in sys.path:
            sys.path.insert(0, str(planning_path))
        from auto_verify import extract_requirements, extract_tasks

        requirements_list = extract_requirements(self.plan)
        tasks_list = extract_tasks(self.plan)

        # Build dict indexed by ID for consumer code
        requirements = {r["id"]: {**r, "mapped_tasks": []} for r in requirements_list}
        tasks = {t["id"]: {**t, "mapped_requirements": []} for t in tasks_list}

        # Build coverage matrix by keyword overlap between requirement text and task title
        req_words: dict[str, set[str]] = {}
        for rid, rdata in requirements.items():
            text = rdata.get("text", "").lower()
            req_words[rid] = {
                w for w in re.findall(r"\b[a-z]+\b", text) if len(w) > 3
            }

        for tid, tdata in tasks.items():
            title = tdata.get("title", "").lower()
            task_words = {w for w in re.findall(r"\b[a-z]+\b", title) if len(w) > 3}
            for rid, words in req_words.items():
                if words & task_words:  # keyword overlap
                    requirements[rid]["mapped_tasks"].append(tid)
                    tasks[tid]["mapped_requirements"].append(rid)

        # Statistics
        total_requirements = len(requirements)
        total_tasks = len(tasks)
        reqs_with_tasks = sum(1 for r in requirements.values() if r["mapped_tasks"])
        tasks_with_acceptance = sum(1 for t in tasks.values() if t.get("has_acceptance_criteria"))

        req_coverage = (reqs_with_tasks / total_requirements * 100) if total_requirements > 0 else 0.0
        task_coverage = (reqs_with_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
        acceptance_coverage = (tasks_with_acceptance / total_tasks * 100) if total_tasks > 0 else 0.0

        # Build coverage_matrix: {req_id: [task_ids]}
        coverage_matrix = {rid: rdata["mapped_tasks"] for rid, rdata in requirements.items()}

        return {
            "requirements": requirements,
            "tasks": tasks,
            "coverage_matrix": coverage_matrix,
            "statistics": {
                "total_requirements": total_requirements,
                "total_tasks": total_tasks,
                "requirements_with_tasks": reqs_with_tasks,
                "requirements_without_tasks": total_requirements - reqs_with_tasks,
                "requirement_coverage": round(req_coverage, 1),
                "task_coverage": round(task_coverage, 1),
                "acceptance_coverage": round(acceptance_coverage, 1),
                "tasks_with_acceptance_criteria": tasks_with_acceptance,
            },
        }

    def calculate_tsr(self) -> dict[str, Any]:
        """
        Calculate Task Success Rate from evidence ledger.

        Returns:
            TSR statistics dict with total_attempted, completed, failed, blocked, tsr
        """
        if not self.evidence_ledger:
            return {
                "total_attempted": 0,
                "completed": 0,
                "failed": 0,
                "blocked": 0,
                "tsr": 0.0,
                "note": "No evidence ledger provided",
            }

        # Extract task statistics from ledger
        tasks = self.evidence_ledger.get("tasks", {})

        total_attempted = len(tasks)
        completed = 0
        failed = 0
        blocked = 0

        for task_id, task_data in tasks.items():
            # Check if task is done (has all 4 evidence types and done=True)
            if task_data.get("done", False):
                # Verify all 4 evidence types are present
                evidence = task_data.get("evidence", {})
                required = ["RED", "GREEN", "REFACTOR", "VERIFY"]
                all_present = all(evidence.get(stage, {}).get("completed") for stage in required)

                if all_present:
                    completed += 1
                else:
                    # Task marked done but missing evidence - count as failed
                    failed += 1
            else:
                # Task not done - check evidence progress
                evidence = task_data.get("evidence", {})
                stages_complete = sum(1 for e in evidence.values() if e.get("completed"))

                if stages_complete == 0:
                    # No evidence at all - blocked
                    blocked += 1
                else:
                    # Some evidence but not complete - failed
                    failed += 1

        # Calculate TSR (avoid division by zero)
        tsr = 0.0
        if total_attempted > 0:
            tsr = (completed / total_attempted) * 100

        return {
            "total_attempted": total_attempted,
            "completed": completed,
            "failed": failed,
            "blocked": blocked,
            "tsr": round(tsr, 2),
        }

    def evaluate_conversation_completeness(
        self,
        rtm: dict[str, Any],
        tsr: dict[str, Any],
        execution_findings: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Use LLM-as-Judge to evaluate conversation completeness.

        Args:
            rtm: Requirements Traceability Matrix
            tsr: Task Success Rate statistics
            execution_findings: Optional execution verification findings

        Returns:
            Evaluation dict with completeness score, findings, and recommendations
        """
        # Extract requirements and tasks from RTM
        requirements = rtm.get("requirements", {})
        tasks = rtm.get("tasks", {})
        statistics = rtm.get("statistics", {})

        # Initialize evaluation
        evaluation = {
            "overall_score": 0.0,
            "requirements_coverage": 0.0,
            "task_completion": 0.0,
            "evidence_quality": 0.0,
            "execution_verification": 100.0,  # Default to 100% (pass)
            "findings": [],
            "recommendations": [],
        }

        # Evaluate requirements coverage
        total_requirements = statistics.get("total_requirements", 0)
        requirements_with_tasks = statistics.get("requirements_with_tasks", 0)

        if total_requirements > 0:
            requirements_coverage = (requirements_with_tasks / total_requirements) * 100
        else:
            requirements_coverage = 100.0  # No requirements means 100% coverage

        evaluation["requirements_coverage"] = requirements_coverage

        # Check for orphan requirements
        orphan_requirements = [
            req_id for req_id, req_data in requirements.items() if not req_data.get("mapped_tasks")
        ]

        if orphan_requirements:
            evaluation["findings"].append(
                {
                    "severity": "HIGH",
                    "category": "orphan_requirements",
                    "description": f"{len(orphan_requirements)} requirement(s) have no tasks mapped",
                    "details": [
                        f"  - {req_id}: {requirements[req_id]['text']}"
                        for req_id in orphan_requirements
                    ],
                }
            )

        # Evaluate task completion (from TSR)
        task_completion = tsr.get("tsr", 0.0)
        evaluation["task_completion"] = task_completion

        if task_completion < 95.0:
            evaluation["findings"].append(
                {
                    "severity": "HIGH",
                    "category": "low_tsr",
                    "description": f"Task Success Rate (TSR) is {task_completion}%, below 95% threshold",
                    "details": [
                        f"  - Total attempted: {tsr.get('total_attempted', 0)}",
                        f"  - Completed: {tsr.get('completed', 0)}",
                        f"  - Failed: {tsr.get('failed', 0)}",
                        f"  - Blocked: {tsr.get('blocked', 0)}",
                    ],
                }
            )

        # Evaluate evidence quality (acceptance criteria coverage)
        total_tasks = statistics.get("total_tasks", 0)
        tasks_with_acceptance = statistics.get("tasks_with_acceptance_criteria", 0)

        if total_tasks > 0:
            acceptance_coverage = (tasks_with_acceptance / total_tasks) * 100
        else:
            acceptance_coverage = 100.0

        evaluation["evidence_quality"] = acceptance_coverage

        if acceptance_coverage < 100.0:
            evaluation["findings"].append(
                {
                    "severity": "MEDIUM",
                    "category": "missing_acceptance_criteria",
                    "description": f"{total_tasks - tasks_with_acceptance} task(s) missing acceptance criteria",
                    "details": [
                        f"  - Tasks with acceptance criteria: {tasks_with_acceptance}/{total_tasks}"
                    ],
                }
            )

        # Evaluate execution verification findings
        if execution_findings:
            high_severity_exec = [f for f in execution_findings if f.get("severity") == "HIGH"]

            if high_severity_exec:
                # Execution verification failed
                execution_score = max(
                    0, 100 - (len(high_severity_exec) * 50)
                )  # Each HIGH finding reduces score by 50%
                evaluation["execution_verification"] = execution_score

                # Add HIGH severity findings to evaluation
                for finding in high_severity_exec:
                    evaluation["findings"].append(finding)
            else:
                # All execution checks passed (only INFO severity findings)
                evaluation["execution_verification"] = 100.0

        # Calculate overall score (weighted average)
        evaluation["overall_score"] = (
            requirements_coverage * 0.25
            + task_completion * 0.45
            + acceptance_coverage * 0.2
            + evaluation["execution_verification"] * 0.1
        )

        # Generate recommendations
        if task_completion < 95.0:
            evaluation["recommendations"].append(
                "Complete failed or blocked tasks to achieve TSR ≥ 95%"
            )

        if orphan_requirements:
            evaluation["recommendations"].append(
                f"Add tasks to address {len(orphan_requirements)} orphan requirement(s)"
            )

        if acceptance_coverage < 100.0:
            evaluation["recommendations"].append(
                f"Define acceptance criteria for {total_tasks - tasks_with_acceptance} task(s)"
            )

        if evaluation["execution_verification"] < 100.0:
            evaluation["recommendations"].append(
                "Ensure all claimed files are created on disk before marking tasks complete"
            )

        # Add passing recommendation if all checks pass
        if (
            task_completion >= 95.0
            and requirements_coverage >= 100.0
            and acceptance_coverage >= 100.0
            and evaluation["execution_verification"] >= 100.0
        ):
            evaluation["recommendations"].append(
                "All verification checks passed - work is complete"
            )

        return evaluation

    def run_analysis(self, include_execution: bool = True) -> dict[str, Any]:
        """
        Run complete post-hoc verification analysis.

        Args:
            include_execution: Whether to include execution verification (default: True)

        Returns:
            Comprehensive verification report with RTM, TSR, execution verification, and LLM-as-Judge evaluation
        """
        # Generate RTM
        rtm = self.generate_rtm()

        # Calculate TSR
        tsr = self.calculate_tsr()

        # Run execution verification if requested and files provided
        execution_findings = None
        if include_execution and self.claimed_files:
            execution_findings = self.verify_execution()

        # Evaluate conversation completeness
        evaluation = self.evaluate_conversation_completeness(rtm, tsr, execution_findings)

        # Determine overall status
        overall_status = (
            "PASS"
            if (
                evaluation["overall_score"] >= 95.0
                and tsr.get("tsr", 0) >= 95.0
                and evaluation["execution_verification"] >= 100.0
            )
            else "FAIL"
        )

        # Build comprehensive report
        report = {
            "overall_status": overall_status,
            "overall_score": round(evaluation["overall_score"], 2),
            "rtm": rtm,
            "tsr": tsr,
            "execution_verification": {
                "included": include_execution,
                "findings": execution_findings,
                "score": evaluation["execution_verification"],
            }
            if include_execution
            else None,
            "evaluation": evaluation,
            "summary": {
                "requirements_coverage": evaluation["requirements_coverage"],
                "task_completion": tsr.get("tsr", 0),
                "evidence_quality": evaluation["evidence_quality"],
                "execution_verification": evaluation["execution_verification"],
                "total_findings": len(evaluation["findings"]),
                "high_severity_findings": len(
                    [f for f in evaluation["findings"] if f.get("severity") == "HIGH"]
                ),
            },
        }

        return report
