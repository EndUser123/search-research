#!/usr/bin/env python3
"""Fix TaskMaster schema mismatch by updating db.py"""

import re


def fix_db_py():
    """Update db.py to include all 41 columns in INSERT statement"""

    with open('db.py') as f:
        content = f.read()

    # Fix 1: Replace the old INSERT statement with the new one
    old_pattern = r'INSERT INTO task VALUES \(:id, :tsk_id, :title, :description, :status, :priority, :phase, :task_type, :assigned_to, :estimated_duration, :actual_duration, :created_at, :started_at, :completed_at, :last_activity, :source, :parent_task_id, :tags, :acceptance_criteria, :verification_status, :completion_percentage, :migration_date, :entities, :validation_rules, :state_management, :auto_closure_enabled, :closure_conditions, :last_state_check, :state_transition_history, :workflow_automation, :automation_metadata, :completion_triggers, :auto_closure_confirmed, :closure_verification_required\)'

    new_insert = '''INSERT INTO task VALUES
    (:id, :tsk_id, :title, :description, :status, :priority, :phase, :task_type,
     :assigned_to, :estimated_duration, :actual_duration, :created_at, :started_at,
     :completed_at, :last_activity, :source, :parent_task_id, :tags, :acceptance_criteria,
     :verification_status, :completion_percentage, :migration_date, :entities,
     :validation_rules, :state_management, :auto_closure_enabled, :closure_conditions,
     :last_state_check, :state_transition_history, :workflow_automation,
     :automation_metadata, :completion_triggers, :auto_closure_confirmed,
     :closure_verification_required, :ai_complexity_score, :predicted_duration,
     :github_pr_number, :evidence_count, :atomicity_score, :is_atomic,
     :dependency_depth, :created_date)'''

    content = re.sub(old_pattern, new_insert, content, flags=re.MULTILINE | re.DOTALL)

    # Fix 2: Add default values for missing columns
    # Find the add_task method and add defaults after last_activity
    add_task_pattern = r'(\s+task_data\[\"last_activity\"\] = task_data\.get\(\s+\"last_activity\", datetime\.now\(\)\.isoformat\(\)\s+\)\s+\))'

    defaults_code = r'''\1

        # Set defaults for missing columns
        task_data.setdefault("ai_complexity_score", 0.5)
        task_data.setdefault("predicted_duration", task_data.get("estimated_duration", 1.0))
        task_data.setdefault("github_pr_number", None)
        task_data.setdefault("evidence_count", 0)
        task_data.setdefault("atomicity_score", 1.0)
        task_data.setdefault("is_atomic", True)
        task_data.setdefault("dependency_depth", 0)
        task_data.setdefault("created_date", datetime.now().date().isoformat())'''

    content = re.sub(add_task_pattern, defaults_code, content)

    with open('db.py', 'w') as f:
        f.write(content)

    print("✅ Fixed db.py - updated INSERT statement and added defaults")

def test_fix():
    """Test if the fix works"""
    print("\n🧪 Testing TaskMaster schema fix...")

    try:
        import sys
        sys.path.insert(0, '.')

        import db

        dal = db.get_dal()

        # Test task creation
        task_data = {
            'id': 'TDD-TEST-SCHEMA-FIX-20251212',
            'tsk_id': 'TSK-TDD-COMPLIANCE-20251212',
            'title': 'Test TaskMaster Schema Fix',
            'description': 'Testing if the schema fix allows task creation',
            'status': 'todo',
            'priority': 'medium',
            'phase': 'testing',
            'task_type': 'validation',
            'assigned_to': 'claude',
            'estimated_duration': 0.5
        }

        task_id = dal.add_task(task_data)
        print(f"✅ Successfully created task: {task_id}")

        # Verify the task was saved
        tasks = dal.get_tasks_by_tsk('TSK-TDD-COMPLIANCE-20251212')
        test_task = next((t for t in tasks if t['id'] == task_id), None)

        if test_task:
            print(f"✅ Task retrieved with {len(test_task)} fields")
            print(f"   - ai_complexity_score: {test_task.get('ai_complexity_score', 'MISSING')}")
            print(f"   - atomicity_score: {test_task.get('atomicity_score', 'MISSING')}")
            print(f"   - created_date: {test_task.get('created_date', 'MISSING')}")
            return True
        else:
            print("❌ Task not found after creation")
            return False

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    fix_db_py()
    if test_fix():
        print("\n🎉 TaskMaster schema fix successful!")
    else:
        print("\n❌ TaskMaster schema fix failed - check errors above")
