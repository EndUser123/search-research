#!/usr/bin/env python3
"""Demo script showing verification visual indicators."""

import sys
from pathlib import Path

# Add hooks to path
sys.path.insert(0, str(Path("P:/.claude/hooks")))

from __lib.verification_visualizer import VerificationVisualizer


def demo_unverified_stance():
    """Show unverified stance warning."""
    print("=" * 70)
    print("DEMO 1: Unverified Stance Warning (Stop Hook)")
    print("=" * 70)
    print("\n**Situation**: You claim 'this bug is fixed' without running tests\n")

    visualizer = VerificationVisualizer()
    advisory = visualizer.format_advisory(
        verification_type="unverified_stance",
        claim="Completion claim without testing evidence",
        evidence_status="No tool evidence found",
        details="**Issue**: completion_claim\n\n**Self-Prompt**: Before claiming 'issue is fixed', 'bug is resolved', or 'tests passed', you must run actual runtime tests and show the test output evidence.\n\n**Severity**: medium\n\nThis would block in non-warn mode."
    )

    print("**What you'll see:**\n")
    print(advisory)
    print()


def demo_integration_warning():
    """Show integration verification warning."""
    print("=" * 70)
    print("DEMO 2: Integration Verification (PostToolUse Hook)")
    print("=" * 70)
    print("\n**Situation**: SKILL.md says suggest: /async-bugs, but it doesn't exist\n")

    visualizer = VerificationVisualizer()
    warning = visualizer.format_integration_warning(
        skill_name="my-skill",
        missing_targets=["/async-bugs", "/nonexistent-skill"],
        one_way_targets=["/code"]
    )

    print("**What you'll see:**\n")
    print(warning)
    print()


def demo_observable_effect_warning():
    """Show observable effect verification warning."""
    print("=" * 70)
    print("DEMO 3: Observable Effect Verification (PostToolUse Hook)")
    print("=" * 70)
    print("\n**Situation**: Code creates logging.FileHandler but log file doesn't exist\n")

    visualizer = VerificationVisualizer()
    warning = visualizer.format_observable_effect_warning(
        effect_type="Logging",
        expected_effect="app.log file created and writable",
        verification_failed="Log file does not exist at specified path"
    )

    print("**What you'll see:**\n")
    print(warning)
    print()


def demo_completion_claim():
    """Show completion claim verification."""
    print("=" * 70)
    print("DEMO 4: Completion Claim Verification (Stop Hook)")
    print("=" * 70)
    print("\n**Situation**: You say 'all tests pass' but no pytest evidence in session\n")

    visualizer = VerificationVisualizer()
    warning = visualizer.format_completion_claim_warning(
        claim_text="all tests pass",
        evidence_found=False,
        session_has_evidence=True
    )

    print("**What you'll see:**\n")
    print(warning)
    print()


def demo_verified_claim():
    """Show a verified claim."""
    print("=" * 70)
    print("DEMO 5: Verified Claim (Success Case)")
    print("=" * 70)
    print("\n**Situation**: You claim 'bug is fixed' AND show pytest output\n")

    visualizer = VerificationVisualizer()
    verified = visualizer.format_verified(
        verification_type="completion_claim",
        claim="Bug fix verified with test evidence",
        evidence_summary="**Evidence**: pytest output shown (exit code 0, 3 tests passed)"
    )

    print("**What you'll see:**\n")
    print(verified)
    print()


def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print(" VERIFICATION VISUALIZATION DEMO")
    print("=" * 70 + "\n")

    demo_unverified_stance()
    demo_integration_warning()
    demo_observable_effect_warning()
    demo_completion_claim()
    demo_verified_claim()

    print("=" * 70)
    print(" SUMMARY: When You'll See Verification Icons")
    print("=" * 70)
    print("""
**⚠️ Advisory** (Yellow warning) - Most common
→ Claim made without evidence, but allowed in warn mode
→ You'll see this several times per day when making claims

**✅ Verified** (Green checkmark) - Success case
→ Claim backed by tool evidence (Read, Bash, Grep, etc.)
→ Appears when you properly verify before claiming

**🛑 Blocked** (Stop sign) - In non-warn mode
→ Claim blocks response until evidence provided
→ Switch from warn to block mode for stricter enforcement

**Verification Types**:
- Integration Verification → SKILL.md suggest: targets
- Observable Effect → Logging, files, side effects
- Stance Verification → "already verified", "no hook for X"
- Completion Claim → "fixed", "tested", "verified"
""")


if __name__ == "__main__":
    main()
