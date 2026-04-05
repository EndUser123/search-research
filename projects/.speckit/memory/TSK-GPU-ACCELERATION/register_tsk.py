#!/usr/bin/env python3
"""
TSK-GPU-ACCELERATION registration script for TaskMaster database
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


def register_tsk_gpu_acceleration():
    """Register TSK-GPU-ACCELERATION in TaskMaster database"""

    # Database path
    db_path = Path(".speckit/taskmaster/tasks.db")

    # TSK metadata
    tsk_data = {
        "tsk_id": "TSK-GPU-ACCELERATION",
        "title": "GPU Acceleration for TaskMaster Enhancement System",
        "description": "Implement RTX 5070 GPU acceleration using dual-environment UV strategy for Python 3.14/CUDA compatibility",
        "status": "active",
        "created_at": "2025-12-02T22:30:00Z",
        "updated_at": "2025-12-02T22:30:00Z",
        "project_files": [
            str(Path(".speckit/memory/TSK-GPU-ACCELERATION/plan.md").absolute()),
            str(Path(".speckit/memory/TSK-GPU-ACCELERATION/data_model.md").absolute()),
            str(Path(".speckit/memory/TSK-GPU-ACCELERATION/tasks.json").absolute())
        ],
        "categories": {
            "primary": "infrastructure",
            "secondary": ["performance", "security", "integration", "testing"]
        },
        "deliverables": [
            "CWO12-compliant artifact triplet",
            "GPU environment manager",
            "Self-invocation GPU bridge",
            "Enhanced semantic search integration",
            "Security validation framework",
            "Performance monitoring system"
        ],
        "team": [
            {
                "role": "Project Lead",
                "assigned": "auto"
            },
            {
                "role": "GPU Development Specialist",
                "assigned": "auto"
            },
            {
                "role": "Security Engineer",
                "assigned": "auto"
            },
            {
                "role": "Python Development Engineer",
                "assigned": "auto"
            },
            {
                "role": "Performance Optimization Engineer",
                "assigned": "auto"
            }
        ],
        "timeline": {
            "start_date": "2025-12-02",
            "end_date": "2025-12-30",
            "phases": [
                {
                    "phase": 1,
                    "name": "Foundation and GPU Environment Setup",
                    "start": "2025-12-02",
                    "end": "2025-12-08"
                },
                {
                    "phase": 2,
                    "name": "GPU Operation Bridge Development",
                    "start": "2025-12-09",
                    "end": "2025-12-15"
                },
                {
                    "phase": 3,
                    "name": "Enhanced Semantic Search Integration",
                    "start": "2025-12-16",
                    "end": "2025-12-22"
                },
                {
                    "phase": 4,
                    "name": "Production Deployment and Optimization",
                    "start": "2025-12-23",
                    "end": "2025-12-30"
                }
            ]
        },
        "success_criteria": [
            "GPU environment automatically created and configured",
            "RTX 5070 successfully detected and utilized",
            "Semantic search operations accelerated by 3-5x",
            "Seamless CPU fallback when GPU unavailable",
            "Zero security vulnerabilities in GPU operations",
            "Complete documentation and user guides",
            "Production-ready monitoring and alerting",
            "Performance benchmarks established and validated"
        ],
        "metrics": {
            "total_tasks": 28,
            "estimated_effort_hours": 120,
            "target_completion": "2025-12-30"
        }
    }

    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if TSK table exists, create if not
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tsk (
                id TEXT PRIMARY KEY,
                project TEXT NOT NULL,
                path TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT,
                status TEXT DEFAULT 'active'
            )
        ''')

        # Check if task table exists, create if not
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS task (
                id TEXT PRIMARY KEY,
                tsk_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'pending',
                priority TEXT DEFAULT 'normal',
                phase TEXT DEFAULT 'planning',
                task_type TEXT DEFAULT 'development',
                assigned_to TEXT,
                estimated_duration REAL DEFAULT 0.0,
                actual_duration REAL DEFAULT 0.0,
                created_at TEXT NOT NULL,
                started_at TEXT,
                completed_at TEXT,
                last_activity TEXT NOT NULL,
                source TEXT DEFAULT 'claude_code',
                parent_task_id TEXT,
                tags TEXT,
                acceptance_criteria TEXT,
                verification_status TEXT,
                completion_percentage REAL DEFAULT 0.0,
                migration_date TEXT,
                entities TEXT,
                validation_rules TEXT,
                FOREIGN KEY (tsk_id) REFERENCES tsk (id)
            )
        ''')

        # Insert TSK record
        cursor.execute('''
            INSERT OR REPLACE INTO tsk
            (id, project, path, active, created_at, updated_at, metadata, status)
            VALUES (?, ?, ?, 1, ?, ?, ?, ?)
        ''', (
            tsk_data["tsk_id"],
            "gpu-acceleration",
            ".speckit/memory/TSK-GPU-ACCELERATION",
            tsk_data["created_at"],
            tsk_data["updated_at"],
            json.dumps(tsk_data),
            tsk_data["status"]
        ))

        # Set other TSKs as inactive
        cursor.execute('UPDATE tsk SET active = 0 WHERE id != ?', (tsk_data["tsk_id"],))

        # Insert main project task
        main_task_id = f'task_{datetime.now().strftime("%Y%m%d_%H%M%S")}_main'
        main_task_data = {
            'id': main_task_id,
            'tsk_id': tsk_data["tsk_id"],
            'title': tsk_data["title"],
            'description': tsk_data["description"],
            'status': 'active',
            'priority': 'high',
            'phase': 'planning',
            'task_type': 'project_management',
            'assigned_to': 'claude',
            'estimated_duration': 120.0,
            'actual_duration': 0.0,
            'created_at': datetime.now().isoformat() + 'Z',
            'started_at': datetime.now().isoformat() + 'Z',
            'completed_at': None,
            'last_activity': datetime.now().isoformat() + 'Z',
            'source': 'claude_code',
            'parent_task_id': None,
            'tags': json.dumps(['project', 'tsk', 'planning', 'gpu', 'acceleration']),
            'acceptance_criteria': json.dumps([
                'TSK structure created with triplet organization',
                'TSK registered as active in TaskMaster database',
                'GPU acceleration plan comprehensive and actionable',
                'Task breakdown complete with dependencies mapped',
                'Data model defined with security constraints'
            ]),
            'verification_status': json.dumps({
                'structure_validation': 'pending',
                'database_registration': 'in_progress',
                'plan_completeness': 'completed',
                'task_breakdown_validation': 'completed',
                'data_model_validation': 'completed'
            }),
            'completion_percentage': 20.0,  # 20% completion for planning phase
            'migration_date': None,
            'entities': json.dumps([]),
            'validation_rules': json.dumps([])
        }

        cursor.execute('''
            INSERT INTO task VALUES (
                :id, :tsk_id, :title, :description, :status, :priority, :phase,
                :task_type, :assigned_to, :estimated_duration, :actual_duration,
                :created_at, :started_at, :completed_at, :last_activity, :source,
                :parent_task_id, :tags, :acceptance_criteria, :verification_status,
                :completion_percentage, :migration_date, :entities, :validation_rules
            )
        ''', main_task_data)

        # Insert phase 1 foundation task
        phase1_task_id = f'task_{datetime.now().strftime("%Y%m%d_%H%M%S")}_phase1'
        phase1_task_data = {
            'id': phase1_task_id,
            'tsk_id': tsk_data["tsk_id"],
            'title': 'Phase 1: Foundation and GPU Environment Setup',
            'description': 'Implement GPU environment management, security validation, and UV configuration for Python 3.11 GPU operations',
            'status': 'pending',
            'priority': 'critical',
            'phase': 'implementation',
            'task_type': 'infrastructure',
            'assigned_to': 'auto',
            'estimated_duration': 32.0,
            'actual_duration': 0.0,
            'created_at': datetime.now().isoformat() + 'Z',
            'started_at': None,
            'completed_at': None,
            'last_activity': datetime.now().isoformat() + 'Z',
            'source': 'claude_code',
            'parent_task_id': main_task_id,
            'tags': json.dumps(['phase1', 'infrastructure', 'gpu', 'environment', 'security']),
            'acceptance_criteria': json.dumps([
                'GPU environment manager implemented using UV patterns',
                'Security validator with operation whitelisting',
                'UV configuration for GPU dependencies',
                'RTX 5070 detection and CUDA validation',
                'Environment health monitoring system',
                'Phase 1 integration testing completed'
            ]),
            'verification_status': json.dumps({
                'environment_manager': 'pending',
                'security_validator': 'pending',
                'uv_configuration': 'pending',
                'hardware_detection': 'pending',
                'health_monitoring': 'pending',
                'integration_testing': 'pending'
            }),
            'completion_percentage': 0.0,
            'migration_date': None,
            'entities': json.dumps(['GPUEnvironmentManager', 'GPUOperationSecurityValidator', 'GPUEnvironmentStatus']),
            'validation_rules': json.dumps(['environment_creation_validation', 'security_validation', 'cuda_compatibility'])
        }

        cursor.execute('''
            INSERT INTO task VALUES (
                :id, :tsk_id, :title, :description, :status, :priority, :phase,
                :task_type, :assigned_to, :estimated_duration, :actual_duration,
                :created_at, :started_at, :completed_at, :last_activity, :source,
                :parent_task_id, :tags, :acceptance_criteria, :verification_status,
                :completion_percentage, :migration_date, :entities, :validation_rules
            )
        ''', phase1_task_data)

        # Create registry entry
        registry_entry = {
            "tsk_id": "TSK-GPU-ACCELERATION",
            "registered_at": datetime.now().isoformat() + 'Z',
            "registered_by": "claude_code",
            "project_path": ".speckit/memory/TSK-GPU-ACCELERATION",
            "status": "active",
            "metadata": tsk_data
        }

        registry_path = Path(".speckit/registry/active/TSK-GPU-ACCELERATION.json")
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(json.dumps(registry_entry, indent=2), encoding='utf-8')

        # Commit changes
        conn.commit()

        print("✅ Successfully registered TSK-GPU-ACCELERATION in TaskMaster database")
        print("📁 TSK Path: .speckit/memory/TSK-GPU-ACCELERATION")
        print(f"🗃️ Database: {db_path}")
        print(f"📋 Registry: {registry_path}")
        print(f"📊 Main Task ID: {main_task_id}")
        print(f"🚀 Phase 1 Task ID: {phase1_task_id}")

        # Display summary
        print("\n📈 TSK Summary:")
        print("   Total Tasks: 28")
        print("   Estimated Hours: 120")
        print("   Project Duration: 4 weeks")
        print("   Success Criteria: 8 items")
        print("   Team Members: 5 roles")

        return True

    except Exception as e:
        print(f"❌ Error registering TSK: {e}")
        return False

    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    success = register_tsk_gpu_acceleration()
    exit(0 if success else 1)
