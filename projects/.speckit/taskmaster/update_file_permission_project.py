#!/usr/bin/env python3
"""
Update/Insert File Permission Protection Project in TaskMaster Database
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

# Database path
DB_PATH = "P:/.speckit/taskmaster/tasks.db"

def update_file_permission_project():
    """Update or insert the file permission protection project in TaskMaster"""

    # Create TSK directory structure
    tsk_id = "TSK-FILE-PERMISSION-PROTECTION-20241209-1000"
    tsk_path = f"P:/{tsk_id}"

    # Ensure the TSK directory exists
    Path(tsk_path).mkdir(parents=True, exist_ok=True)

    # Project data
    project_data = {
        "title": "File Permission Protection System",
        "description": "Enhanced file permission protection with CSF NIP constitutional compliance",
        "status": "active",
        "priority": "high",
        "artifacts": [
            "plan.md",
            "tasks.md",
            "data_model.md"
        ],
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }

    # Create project metadata file
    metadata_path = Path(tsk_path) / "project.json"
    with open(metadata_path, 'w') as f:
        json.dump(project_data, f, indent=2)

    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if TSK already exists
        cursor.execute("SELECT id FROM tsk WHERE id = ?", (tsk_id,))
        exists = cursor.fetchone()

        if exists:
            # Update existing TSK
            cursor.execute("""
                UPDATE tsk SET
                    project = ?,
                    path = ?,
                    active = ?,
                    updated_at = ?,
                    cross_project_dependencies = ?,
                    unified_compliance_score = ?,
                    ai_optimization_suggestions = ?
                WHERE id = ?
            """, (
                project_data["title"],
                tsk_path,
                1,  # active
                project_data["updated_at"],
                json.dumps([]),  # cross_project_dependencies
                0.0,  # unified_compliance_score
                json.dumps([]),  # ai_optimization_suggestions
                tsk_id
            ))
            print(f"[UPDATED] Successfully updated project: {tsk_id}")
        else:
            # Insert new TSK
            cursor.execute("""
                INSERT INTO tsk (
                    id,
                    project,
                    path,
                    active,
                    created_at,
                    updated_at,
                    cross_project_dependencies,
                    unified_compliance_score,
                    ai_optimization_suggestions
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tsk_id,
                project_data["title"],
                tsk_path,
                1,  # active
                project_data["created_at"],
                project_data["updated_at"],
                json.dumps([]),  # cross_project_dependencies
                0.0,  # unified_compliance_score
                json.dumps([])  # ai_optimization_suggestions
            ))
            print(f"[INSERTED] Successfully inserted project: {tsk_id}")

        # Set all other TSKs to inactive
        cursor.execute("UPDATE tsk SET active = 0 WHERE id != ?", (tsk_id,))

        conn.commit()
        print(f"   Title: {project_data['title']}")
        print(f"   Path: {tsk_path}")
        print(f"   Status: {project_data['status']}")
        print(f"   Priority: {project_data['priority']}")

    except sqlite3.Error as e:
        print(f"[ERROR] Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

    # Create/update placeholder artifact files
    for artifact in project_data["artifacts"]:
        artifact_path = Path(tsk_path) / artifact
        if not artifact_path.exists():
            artifact_path.write_text(f"# {artifact.replace('.md', '').title()}\n\nTODO: Create content for {artifact}\n")

    print("\n[ARTIFACTS] Ready artifact files:")
    for artifact in project_data["artifacts"]:
        artifact_path = Path(tsk_path) / artifact
        status = "[CREATED]" if artifact_path.exists() else "[PENDING]"
        print(f"   {status} {tsk_path}/{artifact}")

    # Verify registration by checking the database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, project, path, active FROM tsk WHERE id = ?", (tsk_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        print("\n[VERIFICATION] Project registered in TaskMaster:")
        print(f"   TSK ID: {result[0]}")
        print(f"   Project: {result[1]}")
        print(f"   Path: {result[2]}")
        print(f"   Active: {bool(result[3])}")

if __name__ == "__main__":
    update_file_permission_project()
