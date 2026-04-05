#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

# Force hooks directory into path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from unified_claim_verifier import evaluate_claims


class TestSubtractionSafety(unittest.TestCase):
    def test_unified_verifier_is_stricter_than_text_gate(self):
        """
        Verify that unified_claim_verifier catches unverified claims that 
        the old text-gate would miss (or duplicate).
        """
        # Scenario: Assistant claims a file is VERIFIED but used a tool on a DIFFERENT file.
        # The old StopHook_truth_evidence_gate would ALLOW this because has_post_truth_evidence is True.
        # The unified_claim_verifier should BLOCK this because the entities don't match.

        response = "The file P:/critical_fix.py is VERIFIED."
        tool_sequence = [
            {"command": "ls P:/other_file.py", "output": "other_file.py"}
        ]

        result = evaluate_claims(response, tool_sequence=tool_sequence)

        self.assertEqual(result["decision"], "block", "Should block because critical_fix.py was not seen.")
        self.assertIn("UNVERIFIED_CLAIMS", result["reason"])

    def test_unified_verifier_blocks_without_any_tools(self):
        """Even without /truth active, unverified claims should be blocked."""
        response = "I have confirmed that P:/secret.txt is empty."
        result = evaluate_claims(response, tool_sequence=[])

        self.assertEqual(result["decision"], "block")

    def test_negative_proof_requires_diverse_strategies(self):
        """
        Verify that claims of absence require at least 2 different tool types.
        (Principle of Negative Proof)
        """
        response = "The file P:/deleted_file.py does not exist."

        # Scenario 1: Only 1 tool used (ls) -> Should BLOCK
        tool_sequence_1 = [
            {"name": "Bash", "command": "ls P:/deleted_file.py", "output": "File not found"}
        ]
        result_1 = evaluate_claims(response, tool_sequence=tool_sequence_1)
        self.assertEqual(result_1["decision"], "block", "Should block absence claim with only 1 strategy.")

        # Scenario 2: 2 different tools used (ls AND Glob) -> Should ALLOW
        tool_sequence_2 = [
            {"name": "Bash", "command": "ls P:/deleted_file.py", "output": "File not found"},
            {"name": "Glob", "command": "Glob(P:/deleted_file.py)", "output": "[]"}
        ]
        result_2 = evaluate_claims(response, tool_sequence=tool_sequence_2)
        self.assertEqual(result_2["decision"], "allow", "Should allow absence claim with 2 strategies.")

if __name__ == "__main__":
    unittest.main()
