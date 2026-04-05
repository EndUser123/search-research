#!/usr/bin/env python3
"""Update TaskMaster for Quadlet-03 completion."""
from __future__ import annotations

import sqlite3

conn = sqlite3.connect("P:/.speckit/taskmaster/tasks.db")
conn.execute("""
    UPDATE tasks
    SET description = ?,
        status = ?,
        updated_at = datetime("now")
    WHERE id = ?
""", (
    "CKS-enhanced git worktree confusion prevention system. Current: quadlet-04 (Explore Opportunity Detector)",
    "in_progress",
    "TSK-251222-GitWorktree-1745"
))
conn.commit()
print("TaskMaster updated to quadlet-04")
conn.close()
