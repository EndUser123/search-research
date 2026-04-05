#!/usr/bin/env python3
"""Visual indicators for claim verification system.

Provides user-facing emoji badges and formatted output for verification hooks,
making it clear when claims are being checked and verified.

Icons:
- ✅ Verified - Claim backed by tool evidence
- ⚠️ Advisory - Claim lacks evidence but allowed (warn mode)
- 🔍 Checking - Verification in progress
- ❓ Unverified - No evidence found
"""

from __future__ import annotations


class VerificationVisualizer:
    """Format verification results with user-friendly visual indicators."""

    # Verification status icons
    ICON_VERIFIED = "✅"
    ICON_ADVISORY = "⚠️"
    ICON_CHECKING = "🔍"
    ICON_UNVERIFIED = "❓"
    ICON_BLOCKED = "🛑"

    # Verification type labels
    LABELS = {
        "integration": "Integration Verification",
        "observable_effect": "Observable Effect Verification",
        "unverified_stance": "Stance Verification",
        "completion_claim": "Completion Claim Verification",
        "cleanup": "Cleanup Verification",
        "dependency": "Dependency Verification",
    }

    @classmethod
    def format_advisory(
        cls,
        verification_type: str,
        claim: str,
        evidence_status: str,
        details: str = ""
    ) -> str:
        """Format an advisory (warn mode) with visual indicators.

        Args:
            verification_type: Type of verification (integration, stance, etc.)
            claim: The claim that was checked
            evidence_status: Status of evidence (missing, weak, partial)
            details: Additional details about what's missing

        Returns:
            Formatted advisory string with emoji icons
        """
        label = cls.LABELS.get(verification_type, "Verification")

        advisory = f"**{cls.ICON_ADVISORY} {label}**\n\n"
        advisory += f"**Claim**: {claim}\n\n"
        advisory += f"**Evidence Status**: {evidence_status}\n"

        if details:
            advisory += f"\n{details}\n"

        return advisory

    @classmethod
    def format_verified(
        cls,
        verification_type: str,
        claim: str,
        evidence_summary: str = ""
    ) -> str:
        """Format a verified claim with visual indicators.

        Args:
            verification_type: Type of verification
            claim: The claim that was verified
            evidence_summary: Brief summary of evidence found

        Returns:
            Formatted verification string with success icon
        """
        label = cls.LABELS.get(verification_type, "Verification")

        verified = f"**{cls.ICON_VERIFIED} {label}**\n\n"
        verified += f"**Claim**: {claim}\n\n"
        verified += "**Status**: Verified ✓\n"

        if evidence_summary:
            verified += f"\n{evidence_summary}\n"

        return verified

    @classmethod
    def format_blocked(
        cls,
        verification_type: str,
        claim: str,
        reason: str
    ) -> str:
        """Format a blocked claim with visual indicators.

        Args:
            verification_type: Type of verification
            claim: The claim that was blocked
            reason: Why it was blocked

        Returns:
            Formatted block message with stop icon
        """
        label = cls.LABELS.get(verification_type, "Verification")

        blocked = f"**{cls.ICON_BLOCKED} {label} - Claim Blocked**\n\n"
        blocked += f"**Claim**: {claim}\n\n"
        blocked += f"**Reason**: {reason}\n"

        return blocked

    @classmethod
    def format_checking(
        cls,
        verification_type: str,
        description: str
    ) -> str:
        """Format a "verification in progress" message.

        Args:
            verification_type: Type of verification
            description: What's being checked

        Returns:
            Formatted progress message with checking icon
        """
        label = cls.LABELS.get(verification_type, "Verification")

        checking = f"**{cls.ICON_CHECKING} {label}**\n\n"
        checking += f"{description}\n"

        return checking

    @classmethod
    def format_integration_warning(
        cls,
        skill_name: str,
        missing_targets: list[str],
        one_way_targets: list[str] | None = None
    ) -> str:
        """Format an integration warning with visual indicators.

        Args:
            skill_name: Name of the skill with integration issues
            missing_targets: Targets that don't exist
            one_way_targets: Targets that don't reciprocate

        Returns:
            Formatted integration warning
        """
        warning = f"**{cls.ICON_ADVISORY} Integration Verification**\n\n"
        warning += f"**Skill**: /{skill_name}\n\n"

        if missing_targets:
            warning += "**Missing Integrations**:\n"
            for target in missing_targets:
                warning += f"  • {target} (not found)\n"
            warning += "\n"

        if one_way_targets:
            warning += "**One-Way Integrations** (not reciprocated):\n"
            for target in one_way_targets:
                warning += f"  • {target} doesn't suggest /{skill_name}\n"
            warning += "\n"

        warning += "**Fix**: Add bidirectional integration or remove from suggest: field"

        return warning

    @classmethod
    def format_observable_effect_warning(
        cls,
        effect_type: str,
        expected_effect: str,
        verification_failed: str
    ) -> str:
        """Format an observable effect warning with visual indicators.

        Args:
            effect_type: Type of effect (logging, database, etc.)
            expected_effect: What was expected to happen
            verification_failed: Why verification failed

        Returns:
            Formatted observable effect warning
        """
        warning = f"**{cls.ICON_ADVISORY} Observable Effect Verification**\n\n"
        warning += f"**Effect Type**: {effect_type}\n"
        warning += f"**Expected**: {expected_effect}\n"
        warning += f"**Issue**: {verification_failed}\n"
        warning += "\n**Fix**: Verify the side effect actually occurs"

        return warning

    @classmethod
    def format_completion_claim_warning(
        cls,
        claim_text: str,
        evidence_found: bool,
        session_has_evidence: bool
    ) -> str:
        """Format a completion claim warning with visual indicators.

        Args:
            claim_text: The completion claim detected
            evidence_found: Whether runtime evidence exists
            session_has_evidence: Whether session has any tool evidence

        Returns:
            Formatted completion claim warning
        """
        warning = f"**{cls.ICON_ADVISORY} Completion Claim Verification**\n\n"
        warning += f"**Claim**: \"{claim_text}\"\n\n"

        if evidence_found:
            warning += "**Status**: Verified (runtime evidence found) ✓\n"
        elif session_has_evidence:
            warning += "**Status**: ⚠️ Claim made but no supporting evidence for this specific claim\n"
            warning += "(Session has tool usage, but not for this claim)\n"
        else:
            warning += "**Status**: ⚠️ Claim made without runtime testing evidence\n"
            warning += "(No tool usage detected in session)\n"

        return warning


# Convenience functions for quick formatting
def format_verification_warning(
    verification_type: str,
    message: str
) -> str:
    """Quick format for verification warnings.

    Args:
        verification_type: Type of verification
        message: Warning message

    Returns:
        Formatted warning with emoji
    """
    visualizer = VerificationVisualizer()
    return visualizer.format_advisory(
        verification_type=verification_type,
        claim=message,
        evidence_status="Advisory"
    )


def format_verification_success(
    verification_type: str,
    message: str
) -> str:
    """Quick format for verification success.

    Args:
        verification_type: Type of verification
        message: Success message

    Returns:
        Formatted success with emoji
    """
    visualizer = VerificationVisualizer()
    return visualizer.format_verified(
        verification_type=verification_type,
        claim=message,
        evidence_summary="Claim verified"
    )
