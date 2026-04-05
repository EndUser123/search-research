#!/usr/bin/env python3
import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Force hooks directory into path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import evidence_store


class TestEvidenceTTL(unittest.TestCase):
    def setUp(self):
        # Use a temporary session ID for testing
        self.session_id = "00000000-0000-0000-0000-000000000001"
        evidence_store.init_db()
        # Clean up existing events for this session
        with evidence_store._connect() as conn:
            conn.execute("DELETE FROM tool_events WHERE session_id = ?", (self.session_id,))

    def test_ttl_filtering_works(self):
        """
        Verify that we can filter by time.
        """
        # 1. Insert an 'old' event (11 minutes ago)
        old_ts = (datetime.now(UTC) - timedelta(minutes=11)).isoformat()

        # 2. Insert a 'new' event (1 minute ago)
        new_ts = (datetime.now(UTC) - timedelta(minutes=1)).isoformat()

        with evidence_store._connect() as conn:
            conn.execute(
                "INSERT INTO tool_events (session_id, ts, tool_name, command) VALUES (?, ?, ?, ?)",
                (self.session_id, old_ts, "Bash", "old_command")
            )
            conn.execute(
                "INSERT INTO tool_events (session_id, ts, tool_name, command) VALUES (?, ?, ?, ?)",
                (self.session_id, new_ts, "Bash", "new_command")
            )

        # 3. Load events within the last 10 minutes (600 seconds)
        events = evidence_store.load_tool_events(self.session_id, within_seconds=600)
        self.assertEqual(len(events), 1, "Should only return 1 event within 10m")
        self.assertEqual(events[0]["command"], "new_command")

        # 4. Load events within the last 15 minutes (900 seconds)
        events = evidence_store.load_tool_events(self.session_id, within_seconds=900)
        self.assertEqual(len(events), 2, "Should return both events within 15m")

if __name__ == "__main__":
    unittest.main()
