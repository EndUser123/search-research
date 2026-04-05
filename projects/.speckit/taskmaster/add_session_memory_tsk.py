#!/usr/bin/env python3
"""Add Session Memory Enhancement TSK to TaskMaster database"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


def add_session_memory_tsk():
    """Add the session memory enhancement TSK and its tasks to the database"""

    # Connect to database
    db_path = Path(__file__).parent / 'tasks.db'
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Check if TSK table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tsk'")
    tsk_exists = cursor.fetchone()

    if not tsk_exists:
        # Create TSK table
        cursor.execute('''
            CREATE TABLE tsk (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'active',
                created_at TEXT,
                updated_at TEXT,
                metadata TEXT
            )
        ''')
        print('Created TSK table')

    # Insert the session memory enhancement TSK
    tsk_data = {
        'id': 'TSK-20251214-1101-SESSION-MEMORY-ENHANCEMENT',
        'name': 'Session Memory Architecture Enhancement',
        'description': 'Incremental enhancements to session memory using LangChain patterns for conversation summarization, context compression, and cross-session learning. Current CHS integration provides excellent 3+ day conversation context.',
        'status': 'active',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'metadata': json.dumps({
            'complexity_tax': 17,
            'components': ['conversation_summarization', 'context_compression', 'cross_session_learning'],
            'duration_estimate_weeks': 6,
            'priority': 'high',
            'architecture_findings': {
                'current_strengths': ['CHS integration', 'SoloSessionBridge', 'TaskMaster integration'],
                'enhancement_opportunities': ['LangChain summarization', 'LlamaIndex compression', 'Pattern learning']
            }
        })
    }

    # Insert TSK with correct schema
    cursor.execute('''
        INSERT OR REPLACE INTO tsk
        (id, project, path, active, created_at, updated_at, cross_project_dependencies, unified_compliance_score, ai_optimization_suggestions)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        tsk_data['id'],
        tsk_data['name'],
        f'.speckit/memory/{tsk_data["id"]}',
        1,  # active
        tsk_data['created_at'],
        tsk_data['updated_at'],
        json.dumps([]),  # cross_project_dependencies
        0.95,  # unified_compliance_score
        json.dumps({
            'next_steps': ['Begin conversation summarization implementation', 'Set up LangChain integration'],
            'optimization_opportunities': ['Parallel processing for large conversations', 'Adaptive compression thresholds']
        })  # ai_optimization_suggestions
    ))

    # Create individual tasks for the three main components
    current_time = datetime.now().isoformat()
    tasks = [
        {
            'id': 'TASK-20251214-1102-CONVERSATION-SUMMARIZATION',
            'tsk_id': tsk_data['id'],
            'title': 'Conversation Summarization Implementation',
            'description': 'Implement LangChain SummarizationMiddleware for token-aware compression while preserving key decisions and context',
            'status': 'pending',
            'priority': 'high',
            'phase': 'foundation',
            'task_type': 'implementation',
            'estimated_duration': 2.0,
            'completion_percentage': 0,
            'created_at': current_time,
            'tags': json.dumps(['langchain', 'summarization', 'conversation']),
            'acceptance_criteria': json.dumps([
                'Map-reduce summarization for conversations > 32k tokens',
                'Decision-focused summarization preserving implementation details',
                'Real-time summarization during conversation flow',
                'Performance: < 500ms for 10k token conversations'
            ]),
            'ai_complexity_score': 0.6,
            'predicted_duration': 2.0,
            'is_atomic': True,
            'dependency_depth': 0
        },
        {
            'id': 'TASK-20251214-1103-CONTEXT-COMPRESSION',
            'tsk_id': tsk_data['id'],
            'title': 'Context Compression System',
            'description': 'LlamaIndex-inspired context compressors for selective information preservation while maintaining conversation continuity',
            'status': 'pending',
            'priority': 'medium',
            'phase': 'integration',
            'task_type': 'implementation',
            'estimated_duration': 1.5,
            'completion_percentage': 0,
            'created_at': current_time,
            'tags': json.dumps(['llamaindex', 'compression', 'optimization']),
            'acceptance_criteria': json.dumps([
                'Context relevance scoring with >95% importance preservation',
                '50-70% size reduction while preserving technical details',
                'Metadata preservation for session restoration',
                'Integration with SoloSessionBridge workflow'
            ]),
            'ai_complexity_score': 0.4,
            'predicted_duration': 1.5,
            'is_atomic': True,
            'dependency_depth': 1
        },
        {
            'id': 'TASK-20251214-1104-CROSS-SESSION-LEARNING',
            'tsk_id': tsk_data['id'],
            'title': 'Cross-Session Learning System',
            'description': 'Multi-session correlation patterns and learning from conversation themes for enhanced context bridging',
            'status': 'pending',
            'priority': 'medium',
            'phase': 'advanced',
            'task_type': 'implementation',
            'estimated_duration': 2.5,
            'completion_percentage': 0,
            'created_at': current_time,
            'tags': json.dumps(['machine_learning', 'patterns', 'correlation']),
            'acceptance_criteria': json.dumps([
                'Pattern recognition across multiple sessions with >85% accuracy',
                'Theme extraction and correlation for context bridging',
                'Learning from development workflow patterns',
                'Enhanced context suggestion system'
            ]),
            'ai_complexity_score': 0.7,
            'predicted_duration': 2.5,
            'is_atomic': True,
            'dependency_depth': 2
        }
    ]

    # Insert tasks
    for task in tasks:
        # Set required defaults for all 46 columns
        task.update({
            'assigned_to': 'CSF_NIP_DEVELOPMENT',
            'actual_duration': None,
            'started_at': None,
            'completed_at': None,
            'last_activity': datetime.now().isoformat(),
            'source': 'TSK_CREATION',
            'parent_task_id': None,
            'verification_status': json.dumps({}),
            'migration_date': None,
            'entities': json.dumps([]),
            'validation_rules': json.dumps([]),
            'state_management': json.dumps({}),
            'auto_closure_enabled': 0,
            'closure_conditions': json.dumps([]),
            'last_state_check': datetime.now().isoformat(),
            'state_transition_history': json.dumps([]),
            'workflow_automation': json.dumps({}),
            'automation_metadata': json.dumps({}),
            'completion_triggers': json.dumps([]),
            'auto_closure_confirmed': 0,
            'closure_verification_required': 1,
            'github_pr_number': None,
            'evidence_count': 0,
            'atomicity_score': 1.0,
            'session_id': None,
            'session_span': 1,
            'pre_compaction_state': json.dumps({}),
            'context_criticality': 0.8,
            'compaction_session_id': None
        })

        # Build dynamic insert like the test approach
        columns = list(task.keys())
        values = list(task.values())
        placeholders = ', '.join(['?'] * len(columns))

        cursor.execute(f'INSERT OR REPLACE INTO task ({", ".join(columns)}) VALUES ({placeholders})', values)

    conn.commit()
    conn.close()

    print(f'Successfully added TSK {tsk_data["id"]} with {len(tasks)} tasks to TaskMaster database')
    print('Tasks created:')
    for task in tasks:
        print(f'  - {task["id"]}: {task["title"]}')

if __name__ == '__main__':
    add_session_memory_tsk()
