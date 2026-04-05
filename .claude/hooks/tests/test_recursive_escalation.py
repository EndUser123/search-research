#!/usr/bin/env python3
import datetime
import json
import os
import sys
import unittest
from pathlib import Path

# Force hooks directory into path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import recursive_failure_detector


class TestRecursiveEscalation(unittest.TestCase):
    def setUp(self):
        self.session_id = "test_loop_session"
        os.environ["CLAUDE_SESSION_ID"] = self.session_id
        # Ensure bypass is OFF
        if "CONSTITUTIONAL_HOOKS_BYPASS" in os.environ:
            del os.environ["CONSTITUTIONAL_HOOKS_BYPASS"]

        self.session_file = recursive_failure_detector.get_session_file()
        if self.session_file.exists():
            self.session_file.unlink()

    def test_new_behavior_provides_prescriptive_directive(self):
        """
        Verify that it now gives a prescriptive directive.
        """
        tool = "Bash"
        command = "python -c \"print('fail')\""
        cmd_hash = recursive_failure_detector.compute_command_hash(command)

        # Inject failures directly to avoid timing/env issues
        now = datetime.datetime.now().isoformat()
        failures = [
            {"timestamp": now, "tool": tool, "command_hash": cmd_hash, "error_snippet": "SyntaxError"},
            {"timestamp": now, "tool": tool, "command_hash": cmd_hash, "error_snippet": "SyntaxError"}
        ]
        with open(self.session_file, "w") as f:
            json.dump(failures, f)

        # Verify load_failures sees them
        loaded = recursive_failure_detector.load_failures()
        self.assertEqual(len(loaded), 2)

        result = recursive_failure_detector.check_for_catch22(tool, command)

        print(f"\nDEBUG: result={result}")

        self.assertTrue(result.get("block"))
        self.assertIn("Prescriptive Directive", result["message"])
        self.assertIn("Stop. Your `python -c` quoting is failing.", result["message"])
        self.assertIn("Write your Python code to a temporary file", result["message"])

if __name__ == "__main__":
    unittest.main()
