#!/usr/bin/env python3
"""
Data Access Layer for Workspace Task Database
Located at: P:/.speckit/taskmaster/db.py
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class WorkspaceTaskDAL:
    """Data Access Layer for workspace task management"""

    def __init__(self, db_path: Path = None):
        self.db_path = db_path or Path("P:/.speckit/taskmaster/tasks.db")
        self.conn = None

    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def get_active_tsk(self) -> Optional[Dict]:
        """Get currently active TSK"""
        with self.connect() as conn:
            result = conn.execute("SELECT * FROM tsk WHERE active = 1").fetchone()
            return dict(result) if result else None

    def set_active_tsk(self, tsk_id: str):
        """Set active TSK"""
        with self.connect() as conn:
            conn.execute("UPDATE tsk SET active = 0")
            conn.execute("UPDATE tsk SET active = 1 WHERE id = ?", (tsk_id,))

    def get_tasks_by_tsk(self, tsk_id: str) -> List[Dict]:
        """Get all tasks for a TSK"""
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM task WHERE tsk_id = ? ORDER BY created_at", (tsk_id,)
            ).fetchall()
            return self._parse_tasks(rows)

    def get_all_tasks(self) -> List[Dict]:
        """Get all tasks across workspace"""
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM task ORDER BY created_at").fetchall()
            return self._parse_tasks(rows)

    def add_task(self, task_data: Dict) -> str:
        """Add a new task"""
        task_data["created_at"] = task_data.get(
            "created_at", datetime.now().isoformat()
        )
        task_data["last_activity"] = task_data.get(
            "last_activity", datetime.now().isoformat()
        )

        with self.connect() as conn:
            conn.execute(
                "INSERT INTO task VALUES
    (:id, :tsk_id, :title, :description, :status, :priority, :phase, :task_type,
     :assigned_to, :estimated_duration, :actual_duration, :created_at, :started_at,
     :completed_at, :last_activity, :source, :parent_task_id, :tags, :acceptance_criteria,
     :verification_status, :completion_percentage, :migration_date, :entities,
     :validation_rules, :state_management, :auto_closure_enabled, :closure_conditions,
     :last_state_check, :state_transition_history, :workflow_automation,
     :automation_metadata, :completion_triggers, :auto_closure_confirmed,
     :closure_verification_required, :ai_complexity_score, :predicted_duration,
     :github_pr_number, :evidence_count, :atomicity_score, :is_atomic,
     :dependency_depth, :created_date)",
                task_data,
            )
            return task_data["id"]

    def update_task(self, task_id: str, updates: Dict):
        """Update existing task"""
        updates["last_activity"] = datetime.now().isoformat()

        with self.connect() as conn:
            set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [task_id]
            conn.execute(f"UPDATE task SET {set_clause} WHERE id = ?", values)

    def _parse_tasks(self, rows) -> List[Dict]:
        """Parse database rows with JSON fields - Constitutional evidence-based parsing"""
        tasks = []
        for row in rows:
            task = dict(row)

            # Constitutional: Evidence-based JSON parsing with error handling
            # Each JSON field is parsed with verifiable evidence collection

            # Parse tags with evidence
            try:
                tags = task.get("tags")
                if isinstance(tags, str):
                    task["tags"] = json.loads(tags or "[]")
                elif isinstance(tags, list):
                    task["tags"] = tags
                else:
                    task["tags"] = json.loads("[]")
                task["_parsing_evidence"] = task.get("_parsing_evidence", {})
                task["_parsing_evidence"]["tags_parsed"] = True
                task["_parsing_evidence"]["tags_count"] = len(task["tags"])
            except (json.JSONDecodeError, TypeError):
                task["tags"] = []
                task["_parsing_evidence"] = task.get("_parsing_evidence", {})
                task["_parsing_evidence"]["tags_parsed"] = False
                task["_parsing_evidence"]["tags_error"] = str(task.get("tags", "N/A"))

            # Parse acceptance_criteria with evidence
            try:
                task["_parsing_evidence"] = task.get("_parsing_evidence", {})
                acceptance_criteria = task.get("acceptance_criteria")
                if isinstance(acceptance_criteria, str):
                    task["acceptance_criteria"] = json.loads(
                        acceptance_criteria or "[]"
                    )
                elif isinstance(acceptance_criteria, list):
                    task["acceptance_criteria"] = acceptance_criteria
                else:
                    task["acceptance_criteria"] = json.loads("[]")
                task["_parsing_evidence"]["acceptance_criteria_parsed"] = True
                task["_parsing_evidence"]["acceptance_criteria_count"] = len(
                    task["acceptance_criteria"]
                )
            except (json.JSONDecodeError, TypeError):
                task["acceptance_criteria"] = []
                task["_parsing_evidence"] = task.get("_parsing_evidence", {})
                task["_parsing_evidence"]["acceptance_criteria_parsed"] = False
                task["_parsing_evidence"]["acceptance_criteria_error"] = str(
                    task.get("acceptance_criteria", "N/A")
                )

            # Parse verification_status with evidence
            try:
                task["_parsing_evidence"] = task.get("_parsing_evidence", {})
                verification_status = task.get("verification_status")
                if isinstance(verification_status, str):
                    # Handle double-encoded JSON like '"{}"'
                    parsed = json.loads(verification_status or "{}")
                    if isinstance(parsed, str):
                        task["verification_status"] = json.loads(parsed or "{}")
                    else:
                        task["verification_status"] = parsed
                elif isinstance(verification_status, dict):
                    task["verification_status"] = verification_status
                else:
                    task["verification_status"] = json.loads("{}")
                task["_parsing_evidence"]["verification_status_parsed"] = True
                task["_parsing_evidence"]["verification_status_keys"] = list(
                    task["verification_status"].keys()
                )
            except (json.JSONDecodeError, TypeError):
                task["verification_status"] = {}
                task["_parsing_evidence"] = task.get("_parsing_evidence", {})
                task["_parsing_evidence"]["verification_status_parsed"] = False
                task["_parsing_evidence"]["verification_status_error"] = str(
                    task.get("verification_status", "N/A")
                )

            # Parse entities with evidence
            try:
                task["_parsing_evidence"] = task.get("_parsing_evidence", {})
                entities = task.get("entities")
                if isinstance(entities, str):
                    task["entities"] = json.loads(entities or "[]")
                elif isinstance(entities, list):
                    task["entities"] = entities
                else:
                    task["entities"] = json.loads("[]")
                task["_parsing_evidence"]["entities_parsed"] = True
                task["_parsing_evidence"]["entities_count"] = len(task["entities"])
            except (json.JSONDecodeError, TypeError):
                task["entities"] = []
                task["_parsing_evidence"] = task.get("_parsing_evidence", {})
                task["_parsing_evidence"]["entities_parsed"] = False
                task["_parsing_evidence"]["entities_error"] = str(
                    task.get("entities", "N/A")
                )

            # Parse validation_rules with evidence
            try:
                task["_parsing_evidence"] = task.get("_parsing_evidence", {})
                validation_rules = task.get("validation_rules")
                if isinstance(validation_rules, str):
                    task["validation_rules"] = json.loads(validation_rules or "[]")
                elif isinstance(validation_rules, list):
                    task["validation_rules"] = validation_rules
                else:
                    task["validation_rules"] = json.loads("[]")
                task["_parsing_evidence"]["validation_rules_parsed"] = True
                task["_parsing_evidence"]["validation_rules_count"] = len(
                    task["validation_rules"]
                )
            except (json.JSONDecodeError, TypeError):
                task["validation_rules"] = []
                task["_parsing_evidence"] = task.get("_parsing_evidence", {})
                task["_parsing_evidence"]["validation_rules_parsed"] = False
                task["_parsing_evidence"]["validation_rules_error"] = str(
                    task.get("validation_rules", "N/A")
                )

            # Add constitutional compliance evidence
            task["_parsing_evidence"]["parsing_timestamp"] = datetime.now().isoformat()
            task["_parsing_evidence"]["parsing_successful"] = all(
                task["_parsing_evidence"].get(f"{field}_parsed", False)
                for field in [
                    "tags",
                    "acceptance_criteria",
                    "verification_status",
                    "entities",
                    "validation_rules",
                ]
            )

            tasks.append(task)
        return tasks


# Global instance for easy access
_dal = None


def get_dal() -> WorkspaceTaskDAL:
    """Get global DAL instance"""
    global _dal
    if _dal is None:
        _dal = WorkspaceTaskDAL()
    return _dal
