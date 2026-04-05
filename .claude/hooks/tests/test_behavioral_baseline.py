#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

# Force hooks directory into path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from unified_claim_verifier import evaluate_claims


class TestBehavioralBaseline(unittest.TestCase):
    def test_blocks_unverified_claim(self):
        """Ensure that a claim about a file not mentioned in evidence is blocked."""
        response = "I found that the code in P:/nonexistent.py has been fixed."
        # Simulate empty tool history
        result = evaluate_claims(response, tool_sequence=[])
        print(f"\nDEBUG: result={result}")

        self.assertEqual(result["decision"], "block")
        self.assertEqual(result["reason"], "NO_EVIDENCE")

    def test_allows_verified_claim(self):
        """Ensure that a claim matching tool output is allowed."""
        response = "I found that P:/exists.py is correct."
        # Simulate a tool call that 'saw' exists.py
        tool_sequence = [
            {"command": "cat P:/exists.py", "output": "content of exists.py"}
        ]
        result = evaluate_claims(response, tool_sequence=tool_sequence)

        self.assertEqual(result["decision"], "allow")
        self.assertEqual(result["reason"], "CLAIMS_VERIFIED")

if __name__ == "__main__":
    unittest.main()
