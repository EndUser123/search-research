#!/usr/bin/env python3
"""
Core verification orchestrator.

Combines /trace + /testing-skills into unified 4-tier workflow:
- Tier 0: Checklist-based verification (fast-fail if fails)
- Tier 1: Component tests
- Tier 2: Integration check
- Tier 3: E2E test
"""

import os
import re
import sys
import uuid
from pathlib import Path
from typing import Any

# Import tier modules
from tiers.tier0_checklist import run_checklist_verification
from tiers.tier1_component import Tier1Component
from tiers.tier2_integration import Tier2Integration
from tiers.tier3_e2e import Tier3E2E

# Import skill coverage detector for GTO skill routing
_gto_lib = Path("P:/.claude/skills")
if str(_gto_lib) not in sys.path:
    sys.path.insert(0, str(_gto_lib))
from gto.lib.skill_coverage_detector import _append_skill_coverage  # type: ignore

# Import state manager for multi-terminal isolation (TASK-008)
from .state_manager import VerifyStateManager

_hooks_lib = Path("P:/.claude/hooks/__lib")
if str(_hooks_lib) not in sys.path:
    sys.path.insert(0, str(_hooks_lib))


def _get_session_transcript_text() -> str:
    """Read session transcript text. Copied from RNS lib.chain to avoid extra dep."""
    transcript_path = os.environ.get("CLAUDE_TRANSCRIPT_PATH") or os.environ.get(
        "TRANSCRIPT_PATH"
    )
    if transcript_path:
        p = Path(transcript_path)
        if p.exists():
            return p.read_text(encoding="utf-8")
    return ""


def _infer_target_from_session() -> str | None:
    """
    Infer verification target from session transcript.

    Returns a target string (e.g. 'skill:arch') or None if inference fails.
    Priority: slash-command skill references > skill name mentions > hook mentions.
    """
    text = _get_session_transcript_text()
    if not text:
        return None

    # Match /skill-name slash commands
    skill_refs = re.findall(r"/(\w{3,20})(?:\s|$|[\,\.\:\]\"\'])", text)
    valid_skills = {
        "arch": "skill:arch",
        "code": "skill:code",
        "planning": "skill:planning",
        "verify": "skill:verify",
        "tdd": "skill:tdd",
        "sqa": "skill:sqa",
        "rns": "skill:rns",
        "search": "skill:search",
        "gitready": "skill:gitready",
        "hook": "skill:hook",
    }
    for skill in reversed(skill_refs):
        if skill in valid_skills:
            return valid_skills[skill]

    # Match bare skill references: 'skill:arch', '/arch'
    for match in re.finditer(r"(?:skill:|/\b)(\w{3,20})(?:\s|$|[\,\.\:\]\"\'])", text):
        name = match.group(1)
        if name in valid_skills:
            return valid_skills[name]

    return None


class Verifier:
    """Verification orchestrator running 4-tier verification workflow (Tier 0 → 1 → 2 → 3)."""

    def __init__(self):
        """Initialize verifier with tier instances."""
        self.tier1 = Tier1Component()
        self.tier2 = Tier2Integration()
        self.tier3 = Tier3E2E()
        self._state_manager = None  # Lazy initialization

    def _get_state_manager(
        self, terminal_id: str | None, session_id: str | None
    ) -> VerifyStateManager:
        """
        Get or create state manager for this terminal (TASK-008).

        Args:
            terminal_id: Terminal identifier
            session_id: Session identifier for validation

        Returns:
            VerifyStateManager instance for this terminal
        """
        if self._state_manager is None:
            self._state_manager = VerifyStateManager(terminal_id=terminal_id, session_id=session_id)
        return self._state_manager

    def run_tier0_checklist(self, target_type: str, target_name: str) -> dict[str, Any]:
        """
        Run Tier 0 checklist-based verification.

        Tier 0 provides quick structured verification using checklists.
        If checklist fails, fast-fail and skip remaining tiers.

        Args:
            target_type: Type of target ("skill", "hook", "feature")
            target_name: Name/identifier of the target

        Returns:
            Dictionary with checklist results:
            {
                "status": "pass" | "partial" | "fail",
                "items_checked": int,
                "items_passed": int,
                "findings": List[str]
            }

        Raises:
            ValueError: If target_type is invalid
        """
        # Map target type to appropriate path
        target_path = self._get_target_path(target_type, target_name)

        # Run checklist verification
        try:
            result = run_checklist_verification(target_type, target_path)
            return result
        except ValueError:
            # Re-raise ValueError for invalid target types
            raise
        except Exception as e:
            # Return failure result for other errors
            return {
                "status": "fail",
                "items_checked": 0,
                "items_passed": 0,
                "findings": [f"Checklist verification failed: {str(e)}"],
            }

    def _get_target_path(self, target_type: str, target_name: str) -> str:
        """
        Get the filesystem path for a target type and name.

        Args:
            target_type: Type of target ("skill", "hook", "feature", "code")
            target_name: Name/identifier of the target

        Returns:
            Path string for the target

        Raises:
            ValueError: If target_type is invalid
        """
        if target_type == "skill":
            return f"P:/.claude/skills/{target_name}"
        elif target_type == "hook":
            # For hooks, target_name is the hook identifier (e.g., "breadcrumb_init")
            # The actual hook file pattern is *<name>*.py
            return f"P:/.claude/hooks/*{target_name}*.py"
        elif target_type == "feature":
            # Features use the name directly
            return target_name
        elif target_type == "code":
            # Code targets use the file path directly
            return target_name
        else:
            raise ValueError(
                f"Invalid target type: {target_type}. "
                "Must be 'skill', 'hook', 'feature', or 'code'."
            )

    def detect_target(self, target_input: str) -> dict[str, str]:
        """
        Detect target type from user input.

        Args:
            target_input: User input string (e.g., "skill:arch", "hook:init", "src/file.py")
                         If empty, falls back to session context inference.

        Returns:
            Dict with 'type' and 'name' keys

        Raises:
            ValueError: If target format is invalid and session inference also fails
        """
        if not target_input or not isinstance(target_input, str):
            target_input = target_input.strip() if isinstance(target_input, str) else ""

        if not target_input:
            # Try session context inference before declaring invalid
            inferred = _infer_target_from_session()
            if inferred:
                target_input = inferred

        if not target_input or not isinstance(target_input, str) or not target_input.strip():
            raise ValueError(
                "Invalid target format: empty and no target could be inferred from session context. "
                "Provide a target (e.g., 'skill:arch', 'hook:init', 'src/file.py')."
            )

        target_input = target_input.strip()

        if ":" in target_input:
            # Explicit type: "skill:arch" or "hook:init"
            target_type, target_name = target_input.split(":", 1)

            if target_type not in ("skill", "hook", "feature", "code"):
                raise ValueError(f"Invalid target type: {target_type}")

            return {"type": target_type, "name": target_name}

        # Auto-detect from target name
        # Check if it's a skill
        skill_path = Path(f"P:/.claude/skills/{target_input}/SKILL.md")
        if skill_path.exists():
            return {"type": "skill", "name": target_input}

        # Check if it's a code file
        if target_input.endswith(".py"):
            return {"type": "code", "name": Path(target_input).name}

        # Default: treat as bare name (might be skill or hook)
        return {"type": "unknown", "name": target_input}

    def verify(
        self,
        target: str,
        session_id: str | None = None,
        terminal_id: str | None = None,
        deep_lens: bool = False,
        adversarial: bool = False,
        full_state: bool = False,
        expected_files: list[str | Path] | None = None,
    ) -> dict[str, Any]:
        """
        Run full 4-tier verification workflow (Tier 0 → 1 → 2 → 3).

        Args:
            target: Target string (e.g., "skill:arch")
            session_id: Session ID for E2E tracking
            terminal_id: Terminal ID for E2E tracking
            deep_lens: Enable 6-lens deep analysis in Tier 2
            adversarial: Enable 9-agent adversarial review
            full_state: Enable Full State Verification (Source→Logic→Read) in Tier 3
            expected_files: List of files to verify (required for full_state verification)

        Returns:
            Verification report dict with overall_status and tier results
        """
        # Initialize state manager for multi-terminal isolation (TASK-008)
        state_manager = self._get_state_manager(terminal_id, session_id)

        # Validate session (TASK-008)
        if not state_manager.validate_session(session_id):
            return {
                "overall_status": "failed",
                "error": "Session validation failed - session ID mismatch",
                "session_id": session_id,
                "terminal_id": terminal_id,
            }

        # Detect target type
        detected = self.detect_target(target)

        # Resolve session_id
        if not session_id:
            session_id = os.environ.get("CLAUDE_SESSION_ID", "unknown-session")

        # Run Tier 0: Checklist Verification (FAST-FAIL if fails)
        try:
            tier0_result = self.run_tier0_checklist(detected["type"], detected["name"])
        except ValueError as e:
            # Invalid target type for checklist
            tier0_result = {
                "status": "fail",
                "items_checked": 0,
                "items_passed": 0,
                "findings": [f"Invalid target for checklist: {str(e)}"],
            }

        # Fast-fail: If Tier 0 fails, skip remaining tiers
        if tier0_result["status"] == "fail":
            report = self._build_fast_fail_report(
                target=target,
                detected=detected,
                tier0_result=tier0_result,
                skip_reason="Skipped due to Tier 0 failure",
            )
            return report

        # Tier 0 passed or partial, continue with remaining tiers
        # Run Tier 1: Component Tests
        tier1_result = self.tier1.run_tests(detected["type"], detected["name"])

        # Run Tier 2: Integration Check
        tier2_result = self.tier2.check_integration(
            detected["type"], detected["name"], deep_lens=deep_lens
        )

        # Run Tier 3: E2E Test (only if T1 and T2 pass)
        if tier1_result["status"] == "pass" and tier2_result["status"] == "pass":
            tier3_result = self.tier3.check_e2e(
                detected["type"],
                detected["name"],
                session_id=session_id,
                full_state_verification=full_state,
                expected_files=expected_files,
            )
        else:
            tier3_result = {"status": "skip", "evidence": "Skipped due to Tier 1 or Tier 2 failure"}

        # Determine overall status (all tiers must pass)
        all_pass = (
            tier0_result["status"] == "pass"
            and tier1_result["status"] == "pass"
            and tier2_result["status"] == "pass"
            and tier3_result["status"] == "pass"
        )

        overall_status = "verified" if all_pass else "failed"

        # Detect tier mismatches
        tier_mismatch = self._detect_tier_mismatches(
            tier0_result, tier1_result, tier2_result, tier3_result
        )

        # Generate verification ID
        verification_id = str(uuid.uuid4())

        # Build report with all 4 tiers
        report = {
            "verification_id": verification_id,
            "target": target,
            "target_type": detected["type"],
            "target_name": detected["name"],
            "overall_status": overall_status,
            "tier0": tier0_result,
            "tier1": tier1_result,
            "tier2": tier2_result,
            "tier3": tier3_result,
        }

        if tier_mismatch:
            report["tier_mismatch"] = tier_mismatch

        # Run Adversarial Review if enabled (TASK-007 integration)
        if adversarial:
            adversarial_result = self._run_adversarial_review(
                detected["type"], detected["name"], target
            )
            report["adversarial"] = adversarial_result

        # Save verification state for this terminal (TASK-008)
        state_manager.save_verification_state(
            verification_id,
            {
                "target": target,
                "overall_status": overall_status,
                "timestamp": uuid.uuid4().hex,  # Simple timestamp
            },
        )

        # Add state metadata to report (TASK-008)
        report["state_metadata"] = {
            "terminal_id": state_manager.terminal_id,
            "session_id": state_manager.session_id,
            "state_dir": str(state_manager.get_state_dir()),
        }

        # Log skill coverage for GTO skill routing
        try:
            # Derive target_key from the target being verified
            # Use detected name as the target_key for per-target isolation
            target_key = f"{detected['type']}/{detected['name']}"

            _append_skill_coverage(
                target_key=target_key,
                skill="/verify",
                terminal_id=state_manager.terminal_id,
                git_sha=None,
            )
        except Exception:
            # Skill coverage logging is best-effort - don't fail verification on error
            pass

        return report

    def _build_fast_fail_report(
        self, target: str, detected: dict[str, str], tier0_result: dict[str, Any], skip_reason: str
    ) -> dict[str, Any]:
        """
        Build a verification report when Tier 0 fails (fast-fail).

        Args:
            target: Original target string
            detected: Detected target info (type, name)
            tier0_result: Tier 0 verification result
            skip_reason: Reason why tiers 1-3 were skipped

        Returns:
            Verification report dict with failed status
        """
        return {
            "verification_id": str(uuid.uuid4()),
            "target": target,
            "target_type": detected["type"],
            "target_name": detected["name"],
            "overall_status": "failed",
            "tier0": tier0_result,
            "tier1": {"status": "skip", "evidence": skip_reason},
            "tier2": {"status": "skip", "evidence": skip_reason},
            "tier3": {"status": "skip", "evidence": skip_reason},
        }

    def _detect_tier_mismatches(
        self,
        tier0_result: dict[str, Any],
        tier1_result: dict[str, Any],
        tier2_result: dict[str, Any],
        tier3_result: dict[str, Any],
    ) -> list[str]:
        """
        Detect tier mismatches (e.g., lower tier passes, higher tier fails).

        Args:
            tier0_result: Tier 0 verification result
            tier1_result: Tier 1 verification result
            tier2_result: Tier 2 verification result
            tier3_result: Tier 3 verification result

        Returns:
            List of mismatch indicators
        """
        mismatches = []

        if tier0_result["status"] == "pass" and tier1_result["status"] == "fail":
            mismatches.extend(["tier0_pass", "tier1_fail"])
        if tier1_result["status"] == "pass" and tier2_result["status"] == "fail":
            mismatches.extend(["tier1_pass", "tier2_fail"])
        if tier2_result["status"] == "pass" and tier3_result["status"] == "fail":
            mismatches.extend(["tier2_pass", "tier3_fail"])

        return mismatches

    def _run_adversarial_review(
        self, target_type: str, target_name: str, target: str
    ) -> dict[str, Any]:
        """Run adversarial review using 9-agent system (TASK-007 integration).

        Args:
            target_type: Type of target (skill, hook, feature, code)
            target_name: Name of target
            target: Original target string

        Returns:
            Adversarial review results with envelopes, summaries, and status
        """
        # Import here to avoid circular dependency
        from tiers.adversarial_coordinator import adversarial_review

        # Determine content type based on target
        # For skills, hooks, features: review as "code"
        # For code targets: review as "code"
        review_target_type = "code"

        # Build content for review
        # For now, provide a summary of the target
        # In actual use, this would read the actual code/plan files
        context = {"target": target, "target_type": target_type, "target_name": target_name}

        content = f"Verification target: {target}\nType: {target_type}\nName: {target_name}"

        # Run adversarial review
        try:
            result = adversarial_review(
                target_type=review_target_type, content=content, context=context
            )

            return {
                "status": "completed",
                "overall_status": result.get("overall_status", "unknown"),
                "summaries": result.get("summaries_only", []),
                "artifact_dir": result.get("artifact_dir"),
                "timestamp": result.get("timestamp"),
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Adversarial review failed: {e}",
                "overall_status": "error",
            }

    def run_post_hoc_verification(
        self,
        plan_path: str | None = None,
        plan_content: str | None = None,
        evidence_ledger_path: str | None = None,
        transcript_path: str | None = None,
        terminal_id: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Run post-hoc verification using LLM-as-Judge approach.

        Analyzes completed work through chat history artifacts including:
        - Plan completeness (RTM - Requirements Traceability Matrix)
        - Implementation completeness (TSR - Task Success Rate)
        - Conversation completeness (all requirements addressed)

        Args:
            plan_path: Path to plan.md file
            plan_content: Full text of plan.md (alternative to plan_path)
            evidence_ledger_path: Path to evidence ledger JSON
            transcript_path: Path to chat transcript JSONL (optional)
            terminal_id: Terminal ID for state isolation (TASK-008)
            session_id: Session ID for validation (TASK-008)

        Returns:
            Comprehensive verification report with overall_status, RTM, TSR, and evaluation

        Raises:
            ValueError: If neither plan_path nor plan_content is provided
        """
        # Initialize state manager for multi-terminal isolation (TASK-008)
        state_manager = self._get_state_manager(terminal_id, session_id)

        # Use state manager's evidence ledger path if none provided (TASK-008)
        if not evidence_ledger_path:
            evidence_ledger_path = str(state_manager.get_evidence_ledger_path())

        # Import PostHocAnalyzer
        from tiers.post_hoc_analyzer import PostHocAnalyzer

        # Create analyzer instance
        analyzer = PostHocAnalyzer(
            plan_path=plan_path,
            plan_content=plan_content,
            evidence_ledger_path=evidence_ledger_path,
            transcript_path=transcript_path,
        )

        # Run complete analysis
        report = analyzer.run_analysis()

        # Add state metadata to report (TASK-008)
        report["state_metadata"] = {
            "terminal_id": state_manager.terminal_id,
            "session_id": state_manager.session_id,
            "state_dir": str(state_manager.get_state_dir()),
            "evidence_ledger_path": evidence_ledger_path,
        }

        return report

    def get_state_stats(
        self, terminal_id: str | None = None, session_id: str | None = None
    ) -> dict[str, Any]:
        """
        Get statistics about the verification state for this terminal (TASK-008).

        Args:
            terminal_id: Terminal identifier
            session_id: Session identifier

        Returns:
            State statistics dict
        """
        state_manager = self._get_state_manager(terminal_id, session_id)
        return state_manager.get_stats()
