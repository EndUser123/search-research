"""
Anti-Lazy Verification Module

Contains AntiLazyVerification class for Zero-Claim Verification Protocol.

Extracted from pre_tool_use.py for better modularity and maintainability.
"""


class AntiLazyVerification:
    """
    ANTI-LAZY-001: Zero-Claim Verification Protocol

    Forces verification of ALL claims against actual code implementation.
    Prevents lazy assumptions and documentation-only analysis.
    """

    @staticmethod
    def verify_system_claim(
        system_name: str, claimed_behavior: str, implementation_paths: list
    ) -> dict:
        """
        Verify a claimed behavior by checking actual implementation.

        Args:
            system_name: Name of system being claimed about
            claimed_behavior: What the system is claimed to do
            implementation_paths: List of files to check for actual behavior

        Returns:
            dict with verification results
        """
        import os

        verification_result = {
            "claim": claimed_behavior,
            "system": system_name,
            "verified": False,
            "evidence_found": [],
            "discrepancies": [],
            "lazy_analysis_detected": False,
        }

        for path in implementation_paths:
            if os.path.exists(path):
                verification_result["evidence_found"].append(
                    f"Found implementation file: {path}"
                )

                # Check if claimed behavior is actually implemented
                with open(path) as f:
                    content = f.read()

                    # Look for enforcement logic, not just documentation
                    if "enforce" in content.lower() or "require" in content.lower():
                        verification_result["evidence_found"].append(
                            f"Found enforcement logic in {path}"
                        )
                        verification_result["verified"] = True

                    # Check for TDD-specific enforcement
                    if "tdd" in claimed_behavior.lower():
                        tdd_enforcement = [
                            "test_required",
                            "must_have_test",
                            "test_before_code",
                            "tdd_enforcement",
                            "test_driven",
                        ]

                        if any(
                            enforcement in content.lower()
                            for enforcement in tdd_enforcement
                        ):
                            verification_result["evidence_found"].append(
                                f"Found TDD enforcement in {path}"
                            )
                            verification_result["verified"] = True
                        else:
                            verification_result["discrepancies"].append(
                                f"TDD claimed but not enforced in {path}"
                            )
                            verification_result["lazy_analysis_detected"] = True

        return verification_result

    @staticmethod
    def block_lazy_analysis(claim_description: str) -> bool:
        """
        Block tool use if lazy analysis patterns detected.
        """
        lazy_patterns = [
            "documentation says",
            "according to docs",
            "it should enforce",
            "supposed to require",
            "claims to enforce",
            "after detailed analysis",
            "based on my analysis",
            "if I recall correctly",
            "I believe",
            "probably",
            "should work",
        ]

        for pattern in lazy_patterns:
            if pattern in claim_description.lower():
                print(f"🚫 LAZY ANALYSIS BLOCKED: '{pattern}' detected")
                print(
                    "❌ ANTI-LAZY PROTOCOL: Verify actual implementation, "
                    "don't rely on documentation"
                )
                return True

        return False
