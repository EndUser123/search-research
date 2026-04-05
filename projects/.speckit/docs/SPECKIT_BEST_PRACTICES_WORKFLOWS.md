# Speckit Best Practices and Workflows Guide

## Overview

This guide provides comprehensive best practices, proven workflows, and optimization strategies for using Speckit effectively in various development scenarios. Following these practices ensures maximum productivity, quality, and value from the Speckit framework.

## Table of Contents

1. [Core Principles](#core-principles)
2. [Project Setup Best Practices](#project-setup-best-practices)
3. [Development Workflows](#development-workflows)
4. [Evidence Management Best Practices](#evidence-management-best-practices)
5. [Task Management Strategies](#task-management-strategies)
6. [Quality Assurance Workflows](#quality-assurance-workflows)
7. [Team Collaboration Patterns](#team-collaboration-patterns)
8. [Performance Optimization](#performance-optimization)
9. [Security Best Practices](#security-best-practices)
10. [Scaling Strategies](#scaling-strategies)
11. [Common Pitfalls and Solutions](#common-pitfalls-and-solutions)

## Core Principles

### 1. Evidence-First Development

**Principle**: Every decision and implementation must be backed by evidence.

**Implementation**:
```bash
# Always start with knowledge search
cd "C:\_Python\_Projects\__csf.nip" && python scripts/knowledge_interface.py search --keywords "your topic"

# Generate evidence at each stage
/speckit.specify "Feature" --evidence-first
/speckit.research --document-sources
/speckit.plan --validation-evidence
/speckit.execute --save-evidence
```

**Benefits**:
- Reduced technical debt
- Better decision making
- Improved knowledge sharing
- Enhanced quality assurance

### 2. Continuous Validation

**Principle**: Validation should be continuous, not a final gate.

**Implementation**:
```bash
# Validate at each stage
/speckit.constitution --validate
/speckit.analyze --quick-check
/speckit.checklist --bundle security,perf,ux

# Automated validation in CI/CD
speckit quality-gate --threshold 0.75 --continuous
```

**Benefits**:
- Early issue detection
- Reduced rework
- Consistent quality
- Faster feedback loops

### 3. Knowledge Integration

**Principle**: Leverage existing knowledge and contribute back to the community.

**Implementation**:
```bash
# Before implementation
cd "C:\_Python\_Projects\__csf.nip" && python scripts/knowledge_interface.py search --type implementation

# After completion
cd "C:\_Python\_Projects\__csf.nip" && python scripts/knowledge_interface.py add --type lessons_learned
```

**Benefits**:
- Avoids reinventing solutions
- Builds on proven patterns
- Contributes to organizational knowledge
- Accelerates development

### 4. Incremental Delivery

**Principle**: Deliver value incrementally with frequent feedback.

**Implementation**:
```bash
# Break down large features
/speckit.tasks --export-dag --max-task-size 2days

# Iterate with feedback
/speckit.execute --mode feedback_driven --max-feedback-loops 3
```

**Benefits**:
- Faster value delivery
- Reduced risk
- Better stakeholder alignment
- Improved adaptability

## Project Setup Best Practices

### 1. Initial Configuration

#### Project Structure
```
my-project/
├── .speckit/
│   ├── config/
│   │   ├── speckit_config.json
│   │   ├── project-config.json
│   │   └── commands.json
│   ├── memory/
│   │   └── constitution.md
│   ├── templates/
│   ├── scripts/
│   ├── cache/
│   ├── evidence/
│   └── docs/
├── src/
├── tests/
├── docs/
└── .gitignore
```

#### Constitution Configuration
Create `.speckit/memory/constitution.md`:
```markdown
# Project Constitution

## Project Values
1. **Security First**: Security is non-negotiable
2. **Performance Matters**: Response time < 200ms
3. **Code Quality**: Maintainability score > 0.8
4. **Test Coverage**: Minimum 80% coverage
5. **Documentation**: All public APIs documented

## Technical Standards
- **Language**: Python 3.9+
- **Framework**: FastAPI
- **Database**: PostgreSQL 13+
- **Testing**: pytest with >80% coverage
- **Code Style**: Black + isort + flake8

## Quality Gates
- All tests must pass
- Security scan must pass
- Performance benchmarks must be met
- Code review required for all changes
- Documentation updated for API changes

## Development Workflow
1. Requirements gathering with evidence
2. Research and pattern validation
3. Architecture design with validation
4. Implementation with TDD
5. Code review and validation
6. Documentation update
```

### 2. Team Configuration

#### Developer Setup Script
Create `.speckit/scripts/setup-developer.ps1`:
```powershell
param(
  [Parameter(Mandatory=$true)]
  [string]$DeveloperName,

  [string]$Email,
  [string]$Role = "developer"
)

# Create developer configuration
$devConfig = @{
  name = $DeveloperName
  email = $Email
  role = $Role
  preferences = @{
    auto_save_evidence = $true
    validation_frequency = "on_commit"
    notification_level = "important"
    default_task_priority = "medium"
  }
}

# Update project configuration
$configPath = ".speckit/config/project-config.json"
if (Test-Path $configPath) {
  $config = Get-Content $configPath | ConvertFrom-Json
  $config.team_members += $devConfig
  $config | ConvertTo-Json -Depth 10 | Set-Content $configPath
}

# Setup developer environment
Write-Host "Setting up environment for $DeveloperName..."

# Create developer evidence directory
New-Item -ItemType Directory -Force -Path ".speckit/evidence/developers/$DeveloperName"

# Setup Git configuration
git config user.name $DeveloperName
if ($Email) {
  git config user.email $Email
}

# Install pre-commit hooks
speckit git-hooks install

# Validate setup
speckit constitution --validate

Write-Host "Developer setup completed for $DeveloperName"
```

#### Team Permissions Configuration
Create `.speckit/config/team-permissions.json`:
```json
{
  "roles": {
    "lead_developer": {
      "permissions": [
        "task.create",
        "task.assign",
        "task.approve",
        "evidence.validate",
        "constitution.update"
      ]
    },
    "senior_developer": {
      "permissions": [
        "task.create",
        "task.assign",
        "evidence.create",
        "evidence.validate"
      ]
    },
    "developer": {
      "permissions": [
        "task.create",
        "task.update",
        "evidence.create"
      ]
    },
    "qa_engineer": {
      "permissions": [
        "task.validate",
        "evidence.review",
        "quality_gate.execute"
      ]
    }
  },
  "default_permissions": [
    "task.view",
    "evidence.view",
    "analysis.view"
  ]
}
```

### 3. Quality Standards Configuration

#### Quality Gates Setup
Create `.speckit/config/quality-gates.json`:
```json
{
  "gates": {
    "code_quality": {
      "enabled": true,
      "threshold": 0.8,
      "checks": [
        "maintainability_index",
        "complexity_analysis",
        "code_duplication",
        "test_coverage"
      ]
    },
    "security": {
      "enabled": true,
      "threshold": 0.9,
      "checks": [
        "vulnerability_scan",
        "dependency_check",
        "secret_detection",
        "owasp_compliance"
      ]
    },
    "performance": {
      "enabled": true,
      "threshold": 0.75,
      "checks": [
        "response_time",
        "throughput",
        "resource_usage",
        "scalability_test"
      ]
    },
    "documentation": {
      "enabled": true,
      "threshold": 0.7,
      "checks": [
        "api_documentation",
        "code_comments",
        "readme_completeness",
        "architecture_docs"
      ]
    }
  },
  "enforcement": {
    "block_merge_on_failure": true,
    "require_approval_for_recovery": false,
    "auto_create_remediation_tasks": true
  }
}
```

## Development Workflows

### 1. Feature Development Workflow

#### Phase 1: Discovery and Requirements
```bash
# 1.1 Knowledge Research
cd "C:\_Python\_Projects\__csf.nip" && python scripts/knowledge_interface.py search --keywords "feature requirements" --limit 10

# 1.2 Requirements Specification
/speckit.specify "User authentication with OAuth2" --knowledge-context

# 1.3 Requirements Clarification
/speckit.clarify --focus security,performance,ux

# 1.4 Validation Check
/speckit.analyze --validate-requirements --evidence-first
```

#### Phase 2: Research and Planning
```bash
# 2.1 Comprehensive Research
/speckit.research --spike "OAuth2 security patterns" --knowledge-synthesis

# 2.2 Architecture Planning
/speckit.plan --pattern-validation --threat-model

# 2.3 Quality Checklist
/speckit.checklist --bundle security,performance,ux,accessibility

# 2.4 Task Generation
/speckit.tasks --export-dag --time-estimates --knowledge-guidance
```

#### Phase 3: Implementation
```bash
# 3.1 Task Assignment
speckit tasks assign --task-id TSK-001 --assignee "developer-name"

# 3.2 Implementation with Validation
/speckit.execute --task TSK-001 --mode orchestrated --trust-threshold 0.8

# 3.3 Continuous Validation
speckit validate --continuous --auto-save-evidence

# 3.4 Code Review Integration
speckit review --create --task TSK-001 --require-approval
```

#### Phase 4: Testing and Validation
```bash
# 4.1 Comprehensive Testing
/speckit.test --unit --integration --performance --security

# 4.2 Quality Gate Validation
speckit quality-gate --threshold 0.8 --strict

# 4.3 Final Analysis
/speckit.analyze --write-report --comprehensive --evidence-summary

# 4.4 Task Completion
speckit tasks complete --task-id TSK-001 --validate-evidence
```

### 2. Bug Fix Workflow

#### Bug Report and Analysis
```bash
# 2.1 Bug Documentation
speckit bug report --title "Authentication fails on mobile" --severity high

# 2.2 Root Cause Analysis
/speckit debug --analyze --evidence-collection --task-id TSK-BUG-001

# 2.3 Impact Assessment
/speckit analyze --impact-assessment --component authentication
```

#### Bug Fix Implementation
```bash
# 2.4 Fix Planning
speckit.plan --bug-fix --root-cause "session timeout issue" --task-id TSK-BUG-001

# 2.5 Implementation
/speckit.execute --task TSK-BUG-001 --mode focused --regression-testing

# 2.6 Validation
/speckit test --regression --affected-modules authentication
speckit validate --security --performance
```

### 3. Refactoring Workflow

#### Refactoring Planning
```bash
# 3.1 Technical Debt Analysis
speckit analyze --technical-debt --component legacy-module

# 3.2 Refactoring Specification
/speckit.specify "Refactor authentication service" --type refactoring --evidence debt_analysis.json

# 3.3 Migration Planning
/speckit.plan --refactoring --migration-strategy --backward-compatibility
```

#### Refactoring Execution
```bash
# 3.4 Incremental Refactoring
/speckit.execute --mode incremental --preserve-functionality --task-id TSK-REFACTOR-001

# 3.5 Continuous Testing
speckit test --continuous --parallel --focus affected_areas

# 3.6 Performance Validation
speckit validate --performance --before-after --regression-test
```

### 4. Emergency Hotfix Workflow

#### Rapid Response Process
```bash
# 4.1 Emergency Assessment
speckit emergency assess --severity critical --impact production

# 4.2 Rapid Fix Planning
/speckit.plan --hotfix --minimal-change --rollback-plan

# 4.3 Fast-Track Implementation
/speckit.execute --mode hotfix --skip-non-essential-validation --task-id TSK-HOTFIX-001

# 4.4 Rapid Deployment
speckit deploy --hotfix --validation-post-deployment --monitoring-enabled
```

## Evidence Management Best Practices

### 1. Evidence Collection Strategy

#### Evidence Types and Frequency
```json
{
  "evidence_strategy": {
    "collection_frequency": {
      "implementation": "on_save",
      "testing": "on_test_completion",
      "validation": "on_stage_completion",
      "metrics": "daily",
      "reviews": "on_review_completion"
    },
    "retention_policy": {
      "implementation_evidence": "90_days",
      "test_results": "180_days",
      "validation_reports": "365_days",
      "metrics_data": "730_days"
    },
    "compression": {
      "enabled": true,
      "algorithm": "gzip",
      "threshold": "10MB"
    }
  }
}
```

#### Evidence Structure Standards
```
.speckit/evidence/
├── TSK-001/
│   ├── requirements/
│   │   ├── specification.json
│   │   └── clarification.json
│   ├── research/
│   │   ├── security_patterns.json
│   │   └── performance_benchmarks.json
│   ├── implementation/
│   │   ├── code_changes.json
│   │   ├── test_results.json
│   │   └── performance_metrics.json
│   ├── validation/
│   │   ├── security_scan.json
│   │   ├── quality_metrics.json
│   │   └── peer_review.json
│   └── summary/
│       ├── completion_report.json
│       └── lessons_learned.json
└── project_metrics/
    ├── daily_metrics.json
    ├── quality_trends.json
    └── performance_history.json
```

### 2. Evidence Quality Standards

#### Evidence Validation Rules
Create `.speckit/config/evidence-validation.json`:
```json
{
  "validation_rules": {
    "required_fields": {
      "all": ["timestamp", "evidence_type", "task_id", "data"],
      "implementation": ["files_modified", "lines_added", "test_coverage"],
      "testing": ["test_results", "coverage_report", "performance_metrics"],
      "validation": ["validation_type", "result", "score", "issues"]
    },
    "data_quality": {
      "min_data_size": 10,
      "max_data_size": "10MB",
      "required_format": "json",
      "schema_validation": true
    },
    "completeness_check": {
      "require_supporting_files": true,
      "minimum_evidence_items": 3,
      "validation_threshold": 0.8
    }
  }
}
```

#### Evidence Generation Script
Create `.speckit/scripts/evidence-generator.py`:
```python
#!/usr/bin/env python3
"""
Automated evidence generation
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class EvidenceGenerator:
    def __init__(self, speckit_path: str = ".speckit"):
        self.speckit_path = Path(speckit_path)
        self.evidence_path = self.speckit_path / "evidence"

    def generate_implementation_evidence(self, task_id: str, files_changed: list) -> Dict[str, Any]:
        """Generate implementation evidence"""
        evidence = {
            "evidence_type": "implementation",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "files_modified": files_changed,
                "total_files": len(files_changed),
                "lines_added": self.count_lines_added(files_changed),
                "lines_removed": self.count_lines_removed(files_changed),
                "test_files_created": self.extract_test_files(files_changed),
                "complexity_metrics": self.calculate_complexity(files_changed),
                "dependencies_added": self.extract_new_dependencies(files_changed)
            }
        }

        # Save evidence
        self.save_evidence(task_id, "implementation", evidence)
        return evidence

    def generate_test_evidence(self, task_id: str, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate testing evidence"""
        evidence = {
            "evidence_type": "testing",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "test_summary": test_results,
                "coverage_report": self.generate_coverage_report(),
                "performance_benchmarks": self.run_performance_tests(),
                "security_tests": self.run_security_tests(),
                "quality_metrics": self.calculate_quality_metrics()
            }
        }

        self.save_evidence(task_id, "testing", evidence)
        return evidence

    def generate_validation_evidence(self, task_id: str, validation_type: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate validation evidence"""
        evidence = {
            "evidence_type": "validation",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "validation_type": validation_type,
                "validation_results": results,
                "trust_score": self.calculate_trust_score(results),
                "issues_found": results.get("issues", []),
                "recommendations": self.generate_recommendations(results)
            }
        }

        self.save_evidence(task_id, "validation", evidence)
        return evidence

    def save_evidence(self, task_id: str, evidence_type: str, evidence: Dict[str, Any]):
        """Save evidence to file system"""
        task_dir = self.evidence_path / task_id / evidence_type
        task_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{evidence_type}_{timestamp}.json"
        filepath = task_dir / filename

        with open(filepath, 'w') as f:
            json.dump(evidence, f, indent=2, default=str)

        print(f"Evidence saved: {filepath}")

    # Helper methods for evidence generation
    def count_lines_added(self, files: list) -> int:
        """Count lines added in modified files"""
        # Implementation to count added lines
        return 0

    def calculate_complexity(self, files: list) -> Dict[str, Any]:
        """Calculate complexity metrics"""
        # Implementation to analyze code complexity
        return {"cyclomatic_complexity": 0, "cognitive_complexity": 0}

    def generate_coverage_report(self) -> Dict[str, Any]:
        """Generate test coverage report"""
        # Implementation to generate coverage report
        return {"line_coverage": 0, "branch_coverage": 0}

    def calculate_trust_score(self, validation_results: Dict[str, Any]) -> float:
        """Calculate trust score from validation results"""
        # Implementation to calculate trust score
        return 0.0

    def generate_recommendations(self, results: Dict[str, Any]) -> list:
        """Generate recommendations based on validation results"""
        # Implementation to generate recommendations
        return []
```

### 3. Evidence Analysis and Reporting

#### Evidence Analytics Script
Create `.speckit/scripts/evidence-analytics.py`:
```python
#!/usr/bin/env python3
"""
Evidence analysis and reporting
"""

import json
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

class EvidenceAnalytics:
    def __init__(self, evidence_path: str = ".speckit/evidence"):
        self.evidence_path = Path(evidence_path)

    def generate_quality_trends(self, days: int = 30) -> Dict[str, Any]:
        """Generate quality trends over time"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        quality_data = []

        for date in self.date_range(start_date, end_date):
            daily_metrics = self.get_daily_metrics(date)
            quality_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "trust_score": daily_metrics.get("trust_score", 0),
                "test_coverage": daily_metrics.get("test_coverage", 0),
                "security_score": daily_metrics.get("security_score", 0),
                "performance_score": daily_metrics.get("performance_score", 0)
            })

        return {
            "period": f"{days} days",
            "trends": {
                "trust_score": self.calculate_trend([d["trust_score"] for d in quality_data]),
                "test_coverage": self.calculate_trend([d["test_coverage"] for d in quality_data]),
                "security_score": self.calculate_trend([d["security_score"] for d in quality_data]),
                "performance_score": self.calculate_trend([d["performance_score"] for d in quality_data])
            },
            "data": quality_data
        }

    def analyze_task_patterns(self) -> Dict[str, Any]:
        """Analyze task completion patterns"""
        tasks = self.get_all_tasks()

        patterns = {
            "completion_times": [],
            "trust_scores": [],
            "task_sizes": [],
            "common_issues": {},
            "success_factors": {}
        }

        for task in tasks:
            if task.get("status") == "completed":
                # Analyze completion patterns
                completion_time = self.calculate_completion_time(task)
                trust_score = task.get("trust_score", 0)
                task_size = task.get("estimated_hours", 0)

                patterns["completion_times"].append(completion_time)
                patterns["trust_scores"].append(trust_score)
                patterns["task_sizes"].append(task_size)

        # Calculate statistics
        patterns["statistics"] = {
            "avg_completion_time": statistics.mean(patterns["completion_times"]) if patterns["completion_times"] else 0,
            "avg_trust_score": statistics.mean(patterns["trust_scores"]) if patterns["trust_scores"] else 0,
            "avg_task_size": statistics.mean(patterns["task_sizes"]) if patterns["task_sizes"] else 0,
            "completion_rate": len([t for t in tasks if t.get("status") == "completed"]) / len(tasks) if tasks else 0
        }

        return patterns

    def generate_productivity_report(self) -> Dict[str, Any]:
        """Generate productivity report"""
        last_week = datetime.now() - timedelta(days=7)
        recent_tasks = self.get_tasks_since(last_week)

        report = {
            "period": "Last 7 days",
            "tasks_completed": len([t for t in recent_tasks if t.get("status") == "completed"]),
            "tasks_in_progress": len([t for t in recent_tasks if t.get("status") == "active"]),
            "avg_completion_time": self.calculate_avg_completion_time(recent_tasks),
            "productivity_score": self.calculate_productivity_score(recent_tasks),
            "bottlenecks": self.identify_bottlenecks(recent_tasks),
            "recommendations": self.generate_productivity_recommendations(recent_tasks)
        }

        return report

    def generate_evidence_summary(self, task_id: str = None) -> Dict[str, Any]:
        """Generate evidence summary for task or project"""
        if task_id:
            return self.generate_task_evidence_summary(task_id)
        else:
            return self.generate_project_evidence_summary()

    # Helper methods
    def date_range(self, start: datetime, end: datetime):
        """Generate date range"""
        current = start
        while current <= end:
            yield current
            current += timedelta(days=1)

    def calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction"""
        if len(values) < 2:
            return "stable"

        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]

        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)

        if second_avg > first_avg * 1.05:
            return "improving"
        elif second_avg < first_avg * 0.95:
            return "declining"
        else:
            return "stable"

    def get_daily_metrics(self, date: datetime) -> Dict[str, Any]:
        """Get metrics for specific date"""
        # Implementation to retrieve daily metrics
        return {}

    def calculate_completion_time(self, task: Dict[str, Any]) -> float:
        """Calculate task completion time in hours"""
        # Implementation to calculate completion time
        return 0.0

    def calculate_productivity_score(self, tasks: List[Dict[str, Any]]) -> float:
        """Calculate productivity score"""
        # Implementation to calculate productivity score
        return 0.0
```

## Task Management Strategies

### 1. Task Definition Best Practices

#### SMART Task Definition
```json
{
  "task_template": {
    "title": "Specific, measurable, achievable, relevant, time-bound",
    "description": {
      "what": "What needs to be done",
      "why": "Why this is important",
      "how": "How it will be done",
      "acceptance_criteria": "Specific success criteria"
    },
    "definition_of_done": [
      "Code is implemented and tested",
      "Documentation is updated",
      "Code review is completed",
      "All quality gates pass"
    ],
    "time_estimation": {
      "optimistic": "Best case scenario",
      "realistic": "Most likely scenario",
      "pessimistic": "Worst case scenario"
    }
  }
}
```

#### Task Sizing Guidelines
```bash
# Ideal task characteristics
speckit tasks guidelines --size-optimal

# Task size recommendations:
# Small: 0.5 - 1 day (simple fixes, minor features)
# Medium: 1 - 3 days (typical features, moderate complexity)
# Large: 3 - 5 days (complex features, significant refactoring)
# Extra Large: 5+ days (break down further)

# Split large tasks
speckit tasks split --task-id TSK-001 --max-size 3days
```

### 2. Dependency Management

#### Dependency Types and Management
Create `.speckit/config/dependency-management.json`:
```json
{
  "dependency_types": {
    "hard_dependency": {
      "description": "Task cannot start until dependency is complete",
      "blocking": true,
      "auto_block": true
    },
    "soft_dependency": {
      "description": "Task is enhanced by dependency completion",
      "blocking": false,
      "auto_block": false
    },
    "shared_dependency": {
      "description": "Multiple tasks depend on same prerequisite",
      "blocking": true,
      "auto_block": true,
      "priority": "high"
    }
  },
  "management_rules": {
    "max_dependency_depth": 5,
    "circular_dependency_detection": true,
    "dependency_validation": true,
    "auto_dependency_cleanup": true
  }
}
```

#### Dependency Visualization Script
Create `.speckit/scripts/dependency-visualizer.py`:
```python
#!/usr/bin/env python3
"""
Task dependency visualization
"""

import json
import matplotlib.pyplot as plt
import networkx as nx
from pathlib import Path

class DependencyVisualizer:
    def __init__(self, tasks_file: str = ".speckit/cache/active_tasks.json"):
        self.tasks_file = Path(tasks_file)
        self.tasks = self.load_tasks()

    def load_tasks(self) -> list:
        """Load tasks from file"""
        if self.tasks_file.exists():
            with open(self.tasks_file) as f:
                return json.load(f)
        return []

    def create_dependency_graph(self) -> nx.DiGraph:
        """Create dependency graph"""
        G = nx.DiGraph()

        # Add nodes
        for task in self.tasks:
            task_id = task["task_id"]
            G.add_node(task_id, **task)

        # Add edges (dependencies)
        for task in self.tasks:
            task_id = task["task_id"]
            dependencies = task.get("dependencies", [])
            for dep in dependencies:
                G.add_edge(dep, task_id)

        return G

    def visualize_dependencies(self, output_file: str = "dependency_graph.png"):
        """Create dependency visualization"""
        G = self.create_dependency_graph()

        plt.figure(figsize=(12, 8))

        # Layout
        pos = nx.spring_layout(G, k=2, iterations=50)

        # Draw nodes
        node_colors = []
        for node in G.nodes():
            task = G.nodes[node]
            status = task.get("status", "unknown")
            if status == "completed":
                node_colors.append("green")
            elif status == "active":
                node_colors.append("blue")
            elif status == "blocked":
                node_colors.append("red")
            else:
                node_colors.append("gray")

        nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=1000)
        nx.draw_networkx_edges(G, pos, edge_color="gray", arrows=True)
        nx.draw_networkx_labels(G, pos, font_size=8)

        plt.title("Task Dependency Graph")
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(output_file, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"Dependency graph saved to: {output_file}")

    def analyze_dependencies(self) -> dict:
        """Analyze dependency patterns"""
        G = self.create_dependency_graph()

        analysis = {
            "total_tasks": len(G.nodes()),
            "total_dependencies": len(G.edges()),
            "avg_dependencies_per_task": len(G.edges()) / len(G.nodes()) if G.nodes() else 0,
            "critical_path": self.find_critical_path(G),
            "circular_dependencies": list(nx.simple_cycles(G)),
            "bottleneck_tasks": self.find_bottleneck_tasks(G),
            "dependency_depth": nx.dag_longest_path_length(G) if nx.is_directed_acyclic_graph(G) else "N/A"
        }

        return analysis

    def find_critical_path(self, G: nx.DiGraph) -> list:
        """Find critical path in dependency graph"""
        if nx.is_directed_acyclic_graph(G):
            return nx.dag_longest_path(G)
        return []

    def find_bottleneck_tasks(self, G: nx.DiGraph) -> list:
        """Find tasks that block many other tasks"""
        in_degrees = dict(G.in_degree())
        out_degrees = dict(G.out_degree())

        # Tasks with high out-degree are potential bottlenecks
        bottlenecks = [
            node for node, degree in out_degrees.items()
            if degree > 2  # Blocks more than 2 tasks
        ]

        return bottlenecks
```

### 3. Task Prioritization Framework

#### Priority Matrix
Create `.speckit/config/priority-matrix.json`:
```json
{
  "priority_matrix": {
    "axes": {
      "impact": ["low", "medium", "high", "critical"],
      "effort": ["low", "medium", "high", "very_high"]
    },
    "priorities": {
      "critical_impact/low_effort": "critical",
      "critical_impact/medium_effort": "high",
      "high_impact/low_effort": "high",
      "high_impact/medium_effort": "medium",
      "medium_impact/low_effort": "medium",
      "medium_impact/medium_effort": "low",
      "low_impact/low_effort": "low"
    },
    "auto_prioritization": {
      "enabled": true,
      "factors": [
        "business_value",
        "technical_debt_reduction",
        "dependency_blockers",
        "security_impact",
        "user_impact"
      ],
      "weight_distribution": {
        "business_value": 0.3,
        "technical_debt_reduction": 0.2,
        "dependency_blockers": 0.25,
        "security_impact": 0.15,
        "user_impact": 0.1
      }
    }
  }
}
```

#### Prioritization Script
Create `.speckit/scripts/task-prioritizer.py`:
```python
#!/usr/bin/env python3
"""
Task prioritization engine
"""

import json
from typing import Dict, List, Any
from datetime import datetime

class TaskPrioritizer:
    def __init__(self, config_file: str = ".speckit/config/priority-matrix.json"):
        self.config = self.load_config(config_file)

    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load prioritization configuration"""
        with open(config_file) as f:
            return json.load(f)

    def prioritize_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prioritize tasks based on multiple factors"""
        for task in tasks:
            priority_score = self.calculate_priority_score(task)
            task["priority_score"] = priority_score
            task["suggested_priority"] = self.determine_priority(priority_score)

        # Sort by priority score (descending)
        prioritized_tasks = sorted(tasks, key=lambda t: t["priority_score"], reverse=True)
        return prioritized_tasks

    def calculate_priority_score(self, task: Dict[str, Any]) -> float:
        """Calculate priority score for a task"""
        weights = self.config["auto_prioritization"]["weight_distribution"]

        score = 0.0

        # Business value
        business_value = self.assess_business_value(task)
        score += business_value * weights["business_value"]

        # Technical debt reduction
        debt_reduction = self.assess_technical_debt_reduction(task)
        score += debt_reduction * weights["technical_debt_reduction"]

        # Dependency impact
        dependency_impact = self.assess_dependency_impact(task)
        score += dependency_impact * weights["dependency_blockers"]

        # Security impact
        security_impact = self.assess_security_impact(task)
        score += security_impact * weights["security_impact"]

        # User impact
        user_impact = self.assess_user_impact(task)
        score += user_impact * weights["user_impact"]

        return score

    def assess_business_value(self, task: Dict[str, Any]) -> float:
        """Assess business value (0-1 scale)"""
        # Implementation to assess business value
        tags = task.get("tags", [])
        description = task.get("description", "").lower()

        score = 0.0

        # Check for business value indicators
        if any(tag in tags for tag in ["revenue", "customer", "market"]):
            score += 0.3
        if any(keyword in description for keyword in ["new feature", "customer", "revenue"]):
            score += 0.2
        if task.get("priority") == "critical":
            score += 0.5
        elif task.get("priority") == "high":
            score += 0.3

        return min(score, 1.0)

    def assess_technical_debt_reduction(self, task: Dict[str, Any]) -> float:
        """Assess technical debt reduction (0-1 scale)"""
        tags = task.get("tags", [])
        description = task.get("description", "").lower()

        score = 0.0

        if any(tag in tags for tag in ["refactor", "cleanup", "debt", "performance"]):
            score += 0.4
        if any(keyword in description for keyword in ["refactor", "optimize", "improve"]):
            score += 0.3
        if "technical debt" in description:
            score += 0.3

        return min(score, 1.0)

    def assess_dependency_impact(self, task: Dict[str, Any]) -> float:
        """Assess dependency impact (0-1 scale)"""
        # Count tasks that depend on this task
        blocking_tasks = len(task.get("blocking_tasks", []))

        # More blocking tasks = higher impact
        if blocking_tasks >= 5:
            return 1.0
        elif blocking_tasks >= 3:
            return 0.7
        elif blocking_tasks >= 1:
            return 0.4
        else:
            return 0.1

    def assess_security_impact(self, task: Dict[str, Any]) -> float:
        """Assess security impact (0-1 scale)"""
        tags = task.get("tags", [])
        description = task.get("description", "").lower()

        score = 0.0

        if any(tag in tags for tag in ["security", "vulnerability", "auth", "encryption"]):
            score += 0.5
        if any(keyword in description for keyword in ["security", "vulnerability", "auth"]):
            score += 0.3
        if "security" in tags:
            score += 0.2

        return min(score, 1.0)

    def assess_user_impact(self, task: Dict[str, Any]) -> float:
        """Assess user impact (0-1 scale)"""
        description = task.get("description", "").lower()
        tags = task.get("tags", [])

        score = 0.0

        if any(tag in tags for tag in ["ux", "ui", "user", "customer"]):
            score += 0.3
        if any(keyword in description for keyword in ["user experience", "interface", "customer"]):
            score += 0.4
        if "bug" in tags and "user" in description:
            score += 0.3

        return min(score, 1.0)

    def determine_priority(self, score: float) -> str:
        """Determine priority based on score"""
        if score >= 0.8:
            return "critical"
        elif score >= 0.6:
            return "high"
        elif score >= 0.4:
            return "medium"
        else:
            return "low"
```

## Quality Assurance Workflows

### 1. Continuous Quality Validation

#### Quality Gate Pipeline
Create `.speckit/config/quality-pipeline.json`:
```json
{
  "quality_pipeline": {
    "stages": [
      {
        "name": "code_quality",
        "enabled": true,
        "checks": [
          "linting",
          "code_style",
          "complexity_analysis",
          "duplication_detection"
        ],
        "threshold": 0.8,
        "failure_action": "block"
      },
      {
        "name": "security_validation",
        "enabled": true,
        "checks": [
          "vulnerability_scan",
          "dependency_check",
          "secret_detection",
          "owasp_compliance"
        ],
        "threshold": 0.9,
        "failure_action": "block"
      },
      {
        "name": "performance_validation",
        "enabled": true,
        "checks": [
          "response_time_check",
          "memory_usage_check",
          "scalability_test",
          "load_test"
        ],
        "threshold": 0.75,
        "failure_action": "warn"
      },
      {
        "name": "testing_validation",
        "enabled": true,
        "checks": [
          "unit_tests",
          "integration_tests",
          "api_tests",
          "ui_tests"
        ],
        "threshold": 0.8,
        "failure_action": "block"
      }
    ],
    "execution": {
      "trigger": "on_commit",
      "parallel_execution": true,
      "timeout_minutes": 30,
      "retry_on_failure": true,
      "max_retries": 2
    }
  }
}
```

#### Automated Quality Script
Create `.speckit/scripts/quality-validator.py`:
```python
#!/usr/bin/env python3
"""
Automated quality validation
"""

import subprocess
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

class QualityValidator:
    def __init__(self, config_file: str = ".speckit/config/quality-pipeline.json"):
        self.config = self.load_config(config_file)
        self.results = {}

    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load quality pipeline configuration"""
        with open(config_file) as f:
            return json.load(f)

    def run_quality_pipeline(self) -> Dict[str, Any]:
        """Run complete quality validation pipeline"""
        pipeline_results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "passed",
            "stages": [],
            "summary": {}
        }

        total_score = 0.0
        stage_count = 0

        for stage in self.config["quality_pipeline"]["stages"]:
            if not stage["enabled"]:
                continue

            stage_result = self.run_quality_stage(stage)
            pipeline_results["stages"].append(stage_result)

            if stage_result["status"] == "failed" and stage["failure_action"] == "block":
                pipeline_results["overall_status"] = "failed"
                break

            total_score += stage_result["score"]
            stage_count += 1

        # Calculate overall score
        if stage_count > 0:
            pipeline_results["overall_score"] = total_score / stage_count
        else:
            pipeline_results["overall_score"] = 0.0

        # Generate summary
        pipeline_results["summary"] = self.generate_pipeline_summary(pipeline_results)

        # Save results
        self.save_pipeline_results(pipeline_results)

        return pipeline_results

    def run_quality_stage(self, stage: Dict[str, Any]) -> Dict[str, Any]:
        """Run individual quality stage"""
        stage_name = stage["name"]
        checks = stage["checks"]
        threshold = stage["threshold"]

        print(f"Running quality stage: {stage_name}")

        stage_result = {
            "stage": stage_name,
            "timestamp": datetime.now().isoformat(),
            "status": "passed",
            "score": 0.0,
            "checks": [],
            "issues": []
        }

        total_check_score = 0.0
        check_count = 0

        for check in checks:
            check_result = self.run_quality_check(check)
            stage_result["checks"].append(check_result)

            if check_result["status"] == "failed":
                stage_result["issues"].append({
                    "check": check,
                    "message": check_result.get("message", "Check failed"),
                    "severity": check_result.get("severity", "medium")
                })

            total_check_score += check_result["score"]
            check_count += 1

        # Calculate stage score
        if check_count > 0:
            stage_result["score"] = total_check_score / check_count
        else:
            stage_result["score"] = 0.0

        # Determine stage status
        if stage_result["score"] < threshold:
            stage_result["status"] = "failed"
        elif stage_result["issues"]:
            stage_result["status"] = "warning"

        return stage_result

    def run_quality_check(self, check: str) -> Dict[str, Any]:
        """Run individual quality check"""
        check_methods = {
            "linting": self.run_linting_check,
            "code_style": self.run_code_style_check,
            "complexity_analysis": self.run_complexity_check,
            "duplication_detection": self.run_duplication_check,
            "vulnerability_scan": self.run_vulnerability_scan,
            "dependency_check": self.run_dependency_check,
            "secret_detection": self.run_secret_detection,
            "owasp_compliance": self.run_owasp_check,
            "response_time_check": self.run_response_time_check,
            "memory_usage_check": self.run_memory_check,
            "scalability_test": self.run_scalability_test,
            "load_test": self.run_load_test,
            "unit_tests": self.run_unit_tests,
            "integration_tests": self.run_integration_tests,
            "api_tests": self.run_api_tests,
            "ui_tests": self.run_ui_tests
        }

        if check in check_methods:
            return check_methods[check]()
        else:
            return {
                "check": check,
                "status": "skipped",
                "message": f"Check {check} not implemented",
                "score": 0.0
            }

    # Individual check implementations
    def run_linting_check(self) -> Dict[str, Any]:
        """Run code linting check"""
        try:
            # Run flake8
            result = subprocess.run(
                ["flake8", "src/", "--format=json"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return {
                    "check": "linting",
                    "status": "passed",
                    "score": 1.0,
                    "message": "No linting issues found"
                }
            else:
                issues = len(result.stdout.splitlines())
                score = max(0.0, 1.0 - (issues / 10.0))  # Penalize based on issue count

                return {
                    "check": "linting",
                    "status": "warning" if score > 0.7 else "failed",
                    "score": score,
                    "message": f"Found {issues} linting issues",
                    "issues_count": issues
                }

        except Exception as e:
            return {
                "check": "linting",
                "status": "error",
                "score": 0.0,
                "message": f"Error running linting: {str(e)}"
            }

    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests"""
        try:
            # Run pytest
            result = subprocess.run(
                ["pytest", "tests/unit/", "--cov=src", "--cov-report=json"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                # Read coverage report
                coverage_file = Path("coverage.json")
                if coverage_file.exists():
                    with open(coverage_file) as f:
                        coverage_data = json.load(f)

                    total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
                    score = min(1.0, total_coverage / 100.0)

                    return {
                        "check": "unit_tests",
                        "status": "passed",
                        "score": score,
                        "message": f"Tests passed with {total_coverage:.1f}% coverage",
                        "coverage": total_coverage
                    }
                else:
                    return {
                        "check": "unit_tests",
                        "status": "passed",
                        "score": 0.8,  # Default score if coverage not available
                        "message": "Tests passed but coverage not available"
                    }
            else:
                return {
                    "check": "unit_tests",
                    "status": "failed",
                    "score": 0.0,
                    "message": "Unit tests failed",
                    "output": result.stdout
                }

        except Exception as e:
            return {
                "check": "unit_tests",
                "status": "error",
                "score": 0.0,
                "message": f"Error running unit tests: {str(e)}"
            }

    def run_vulnerability_scan(self) -> Dict[str, Any]:
        """Run security vulnerability scan"""
        try:
            # Run safety check
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                vulnerabilities = json.loads(result.stdout)
                vuln_count = len(vulnerabilities)

                if vuln_count == 0:
                    return {
                        "check": "vulnerability_scan",
                        "status": "passed",
                        "score": 1.0,
                        "message": "No security vulnerabilities found"
                    }
                else:
                    # Score based on vulnerability count and severity
                    critical_vulns = len([v for v in vulnerabilities if v.get("vulnerability_id", "").startswith("CVE")])
                    score = max(0.0, 1.0 - (vuln_count * 0.2) - (critical_vulns * 0.3))

                    return {
                        "check": "vulnerability_scan",
                        "status": "failed" if score < 0.7 else "warning",
                        "score": score,
                        "message": f"Found {vuln_count} vulnerabilities ({critical_vulns} critical)",
                        "vulnerabilities": vulnerabilities
                    }

        except Exception as e:
            return {
                "check": "vulnerability_scan",
                "status": "error",
                "score": 0.0,
                "message": f"Error running vulnerability scan: {str(e)}"
            }

    def save_pipeline_results(self, results: Dict[str, Any]):
        """Save pipeline results to evidence"""
        evidence_dir = Path(".speckit/evidence/quality")
        evidence_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"quality_pipeline_{timestamp}.json"
        filepath = evidence_dir / filename

        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"Quality pipeline results saved to: {filepath}")

    def generate_pipeline_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate pipeline summary"""
        stages = results["stages"]

        summary = {
            "total_stages": len(stages),
            "passed_stages": len([s for s in stages if s["status"] == "passed"]),
            "warning_stages": len([s for s in stages if s["status"] == "warning"]),
            "failed_stages": len([s for s in stages if s["status"] == "failed"]),
            "total_issues": sum(len(s.get("issues", [])) for s in stages),
            "recommendations": []
        }

        # Generate recommendations
        if summary["failed_stages"] > 0:
            summary["recommendations"].append("Address failed quality stages before proceeding")

        if summary["total_issues"] > 5:
            summary["recommendations"].append("Consider addressing quality issues incrementally")

        if results["overall_score"] < 0.8:
            summary["recommendations"].append("Focus on improving overall quality score")

        return summary
```

## Team Collaboration Patterns

### 1. Team Workflow Integration

#### Collaborative Development Workflow
```bash
# 1. Team Planning Session
/speckit.plan --collaborative --team-review --consensus-required

# 2. Task Assignment and Collaboration
speckit tasks assign --task-id TSK-001 --assignee "developer1" --reviewers "developer2,senior-dev"
speckit tasks assign --task-id TSK-002 --assignee "developer2" --reviewers "developer1,senior-dev"

# 3. Peer Review Integration
speckit review create --task-id TSK-001 --reviewers "developer2" --checklist security,performance
speckit review submit --task-id TSK-001 --review-id REV-001

# 4. Knowledge Sharing
speckit knowledge share --task-id TSK-001 --team "development-team"
```

#### Team Configuration
Create `.speckit/config/team-workflow.json`:
```json
{
  "team_structure": {
    "roles": {
      "tech_lead": {
        "responsibilities": [
          "architecture_review",
          "technical_decisions",
          "mentoring",
          "quality_gates"
        ],
        "permissions": ["approve_tasks", "modify_constitution", "override_quality_gates"]
      },
      "senior_developer": {
        "responsibilities": [
          "code_review",
          "mentoring",
          "complex_feature_implementation"
        ],
        "permissions": ["review_code", "create_tasks", "modify_technical_standards"]
      },
      "developer": {
        "responsibilities": [
          "feature_implementation",
          "testing",
          "documentation"
        ],
        "permissions": ["implement_tasks", "create_evidence", "update_documentation"]
      },
      "qa_engineer": {
        "responsibilities": [
          "test_planning",
          "quality_validation",
          "bug_reporting"
        ],
        "permissions": ["run_quality_gates", "create_bug_reports", "validate_completion"]
      }
    },
    "collaboration_rules": {
      "require_review_for_critical_changes": true,
      "pair_programming_for_complex_tasks": false,
      "knowledge_sharing_sessions": "weekly",
      "retrospective_frequency": "biweekly"
    }
  }
}
```

### 2. Communication and Notification Patterns

#### Notification Configuration
Create `.speckit/config/notifications.json`:
```json
{
  "notification_channels": {
    "slack": {
      "enabled": true,
      "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
      "channels": {
        "development": "#dev-team",
        "alerts": "#dev-alerts",
        "quality": "#quality-reports"
      }
    },
    "email": {
      "enabled": true,
      "smtp_server": "smtp.company.com",
      "recipients": {
        "tech_lead": "tech-lead@company.com",
        "team": "dev-team@company.com"
      }
    },
    "github": {
      "enabled": true,
      "create_issues": true,
      "update_pr_status": true,
      "comment_on_pr": true
    }
  },
  "notification_triggers": {
    "task_completed": {
      "channels": ["slack", "email"],
      "recipients": ["team"],
      "message": "Task {{task_id}} completed by {{assignee}}"
    },
    "quality_gate_failed": {
      "channels": ["slack", "email"],
      "recipients": ["tech_lead"],
      "message": "Quality gate failed for {{task_id}}: {{issues}}"
    },
    "security_vulnerability": {
      "channels": ["slack", "email"],
      "recipients": ["tech_lead", "team"],
      "message": "Security vulnerability detected: {{vulnerability}}"
    }
  }
}
```

#### Notification Handler Script
Create `.speckit/scripts/notification-handler.py`:
```python
#!/usr/bin/env python3
"""
Notification handler for team collaboration
"""

import json
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from typing import Dict, List, Any

class NotificationHandler:
    def __init__(self, config_file: str = ".speckit/config/notifications.json"):
        self.config = self.load_config(config_file)

    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load notification configuration"""
        with open(config_file) as f:
            return json.load(f)

    def send_notification(self, event_type: str, data: Dict[str, Any]):
        """Send notification based on event type"""
        if event_type not in self.config["notification_triggers"]:
            print(f"No notification configuration for event type: {event_type}")
            return

        trigger_config = self.config["notification_triggers"][event_type]
        channels = trigger_config["channels"]
        recipients = trigger_config["recipients"]
        message_template = trigger_config["message"]

        # Format message with data
        message = self.format_message(message_template, data)

        # Send to each channel
        for channel in channels:
            if channel == "slack":
                self.send_slack_notification(message, recipients, data)
            elif channel == "email":
                self.send_email_notification(message, recipients, data)
            elif channel == "github":
                self.send_github_notification(message, recipients, data)

    def format_message(self, template: str, data: Dict[str, Any]) -> str:
        """Format message template with data"""
        try:
            return template.format(**data)
        except KeyError as e:
            return f"Error formatting message: missing key {e}"

    def send_slack_notification(self, message: str, recipients: List[str], data: Dict[str, Any]):
        """Send Slack notification"""
        if not self.config["notification_channels"]["slack"]["enabled"]:
            return

        webhook_url = self.config["notification_channels"]["slack"]["webhook_url"]

        # Determine channel
        channel = self.config["notification_channels"]["slack"]["channels"].get("development", "#general")

        slack_payload = {
            "channel": channel,
            "text": message,
            "username": "Speckit Bot",
            "icon_emoji": ":robot_face:",
            "attachments": [
                {
                    "fields": [
                        {"title": "Task ID", "value": data.get("task_id", "N/A"), "short": True},
                        {"title": "Assignee", "value": data.get("assignee", "N/A"), "short": True},
                        {"title": "Timestamp", "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "short": True}
                    ]
                }
            ]
        }

        try:
            response = requests.post(webhook_url, json=slack_payload)
            if response.status_code == 200:
                print("Slack notification sent successfully")
            else:
                print(f"Failed to send Slack notification: {response.status_code}")
        except Exception as e:
            print(f"Error sending Slack notification: {e}")

    def send_email_notification(self, message: str, recipients: List[str], data: Dict[str, Any]):
        """Send email notification"""
        if not self.config["notification_channels"]["email"]["enabled"]:
            return

        smtp_config = self.config["notification_channels"]["email"]

        # Compose email
        subject = f"Speckit Notification: {data.get('event_type', 'Unknown Event')}"
        body = f"{message}\n\nDetails:\n{json.dumps(data, indent=2)}"

        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = "speckit@company.com"

        # Get recipient email addresses
        recipient_emails = []
        for recipient in recipients:
            email = smtp_config["recipients"].get(recipient)
            if email:
                recipient_emails.append(email)

        if not recipient_emails:
            print("No valid email recipients found")
            return

        msg["To"] = ", ".join(recipient_emails)

        try:
            with smtplib.SMTP(smtp_config["smtp_server"]) as server:
                server.send_message(msg)
            print("Email notification sent successfully")
        except Exception as e:
            print(f"Error sending email notification: {e}")

    def send_github_notification(self, message: str, recipients: List[str], data: Dict[str, Any]):
        """Send GitHub notification"""
        if not self.config["notification_channels"]["github"]["enabled"]:
            return

        # Implementation for GitHub notifications
        # This could create issues, update PR status, or add comments
        print(f"GitHub notification: {message}")

# Example usage
if __name__ == "__main__":
    handler = NotificationHandler()

    # Example task completion notification
    handler.send_notification("task_completed", {
        "task_id": "TSK-001",
        "assignee": "John Doe",
        "event_type": "task_completed"
    })
```

## Performance Optimization

### 1. Speckit Performance Tuning

#### Configuration Optimization
Create `.speckit/config/performance.json`:
```json
{
  "optimization": {
    "cache_settings": {
      "enabled": true,
      "max_size_mb": 100,
      "ttl_hours": 24,
      "compression": true,
      "preload_common_data": true
    },
    "parallel_processing": {
      "enabled": true,
      "max_workers": 4,
      "chunk_size": 10,
      "timeout_seconds": 300
    },
    "memory_management": {
      "max_memory_mb": 512,
      "gc_frequency": "medium",
      "cleanup_temp_files": true
    },
    "database_optimization": {
      "connection_pool_size": 10,
      "query_timeout": 30,
      "index_optimization": true
    }
  },
  "monitoring": {
    "enabled": true,
    "metrics_collection": true,
    "performance_logging": true,
    "alert_thresholds": {
      "response_time_ms": 5000,
      "memory_usage_mb": 400,
      "cpu_usage_percent": 80
    }
  }
}
```

#### Performance Monitoring Script
Create `.speckit/scripts/performance-monitor.py`:
```python
#!/usr/bin/env python3
"""
Speckit performance monitoring
"""

import psutil
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

class PerformanceMonitor:
    def __init__(self, config_file: str = ".speckit/config/performance.json"):
        self.config = self.load_config(config_file)
        self.metrics_history = []

    def load_config(self, config_file: str) -> Dict[str, Any]:
        """Load performance configuration"""
        with open(config_file) as f:
            return json.load(f)

    def start_monitoring(self):
        """Start performance monitoring"""
        print("Starting performance monitoring...")

        while True:
            metrics = self.collect_metrics()
            self.metrics_history.append(metrics)

            # Keep only last 1000 metrics
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]

            # Check for alerts
            self.check_alerts(metrics)

            # Save metrics periodically
            if len(self.metrics_history) % 10 == 0:
                self.save_metrics()

            time.sleep(60)  # Collect metrics every minute

    def collect_metrics(self) -> Dict[str, Any]:
        """Collect current performance metrics"""
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')

        # Speckit-specific metrics
        speckit_metrics = self.collect_speckit_metrics()

        metrics = {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_mb": memory.used / (1024 * 1024),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024 * 1024 * 1024)
            },
            "speckit": speckit_metrics
        }

        return metrics

    def collect_speckit_metrics(self) -> Dict[str, Any]:
        """Collect Speckit-specific metrics"""
        metrics = {
            "cache_size_mb": self.calculate_cache_size(),
            "active_tasks_count": self.count_active_tasks(),
            "evidence_files_count": self.count_evidence_files(),
            "response_time_ms": self.measure_response_time()
        }

        return metrics

    def calculate_cache_size(self) -> float:
        """Calculate cache directory size in MB"""
        cache_path = Path(".speckit/cache")
        if not cache_path.exists():
            return 0.0

        total_size = 0
        for file_path in cache_path.rglob("*"):
            if file_path.is_file():
                total_size += file_path.stat().st_size

        return total_size / (1024 * 1024)  # Convert to MB

    def count_active_tasks(self) -> int:
        """Count active tasks"""
        tasks_file = Path(".speckit/cache/active_tasks.json")
        if not tasks_file.exists():
            return 0

        try:
            with open(tasks_file) as f:
                tasks = json.load(f)
            return len([t for t in tasks if t.get("status") == "active"])
        except:
            return 0

    def count_evidence_files(self) -> int:
        """Count evidence files"""
        evidence_path = Path(".speckit/evidence")
        if not evidence_path.exists():
            return 0

        return len(list(evidence_path.rglob("*.json")))

    def measure_response_time(self) -> float:
        """Measure Speckit response time"""
        start_time = time.time()

        try:
            # Run a simple Speckit command
            result = subprocess.run(
                ["speckit", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            end_time = time.time()
            return (end_time - start_time) * 1000  # Convert to milliseconds
        except:
            return 0.0

    def check_alerts(self, metrics: Dict[str, Any]):
        """Check for performance alerts"""
        alert_thresholds = self.config["monitoring"]["alert_thresholds"]

        alerts = []

        # Check CPU usage
        if metrics["system"]["cpu_percent"] > alert_thresholds["cpu_usage_percent"]:
            alerts.append({
                "type": "cpu_high",
                "message": f"CPU usage is {metrics['system']['cpu_percent']}%",
                "severity": "warning"
            })

        # Check memory usage
        if metrics["system"]["memory_used_mb"] > alert_thresholds["memory_usage_mb"]:
            alerts.append({
                "type": "memory_high",
                "message": f"Memory usage is {metrics['system']['memory_used_mb']:.1f} MB",
                "severity": "warning"
            })

        # Check Speckit response time
        if metrics["speckit"]["response_time_ms"] > alert_thresholds["response_time_ms"]:
            alerts.append({
                "type": "response_slow",
                "message": f"Speckit response time is {metrics['speckit']['response_time_ms']:.1f} ms",
                "severity": "critical"
            })

        # Send alerts if any
        for alert in alerts:
            self.send_alert(alert)

    def send_alert(self, alert: Dict[str, Any]):
        """Send performance alert"""
        print(f"ALERT: {alert['message']}")

        # Here you could integrate with notification systems
        # For example, send to Slack, email, etc.

    def save_metrics(self):
        """Save metrics to file"""
        metrics_file = Path(".speckit/evidence/performance/metrics.json")
        metrics_file.parent.mkdir(parents=True, exist_ok=True)

        with open(metrics_file, 'w') as f:
            json.dump(self.metrics_history, f, indent=2)

    def generate_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate performance report for specified period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)

        # Filter metrics for the period
        period_metrics = [
            m for m in self.metrics_history
            if datetime.fromisoformat(m["timestamp"]) > cutoff_time
        ]

        if not period_metrics:
            return {"error": "No metrics available for the specified period"}

        # Calculate statistics
        cpu_values = [m["system"]["cpu_percent"] for m in period_metrics]
        memory_values = [m["system"]["memory_used_mb"] for m in period_metrics]
        response_times = [m["speckit"]["response_time_ms"] for m in period_metrics if m["speckit"]["response_time_ms"] > 0]

        report = {
            "period_hours": hours,
            "metrics_count": len(period_metrics),
            "statistics": {
                "cpu": {
                    "avg": sum(cpu_values) / len(cpu_values),
                    "max": max(cpu_values),
                    "min": min(cpu_values)
                },
                "memory": {
                    "avg": sum(memory_values) / len(memory_values),
                    "max": max(memory_values),
                    "min": min(memory_values)
                },
                "response_time": {
                    "avg": sum(response_times) / len(response_times) if response_times else 0,
                    "max": max(response_times) if response_times else 0,
                    "min": min(response_times) if response_times else 0
                }
            },
            "trends": self.calculate_trends(period_metrics),
            "recommendations": self.generate_performance_recommendations(period_metrics)
        }

        return report

    def calculate_trends(self, metrics: List[Dict[str, Any]]) -> Dict[str, str]:
        """Calculate performance trends"""
        if len(metrics) < 2:
            return {"overall": "insufficient_data"}

        # Split metrics into two halves
        mid_point = len(metrics) // 2
        first_half = metrics[:mid_point]
        second_half = metrics[mid_point:]

        # Calculate averages for each half
        first_cpu = sum(m["system"]["cpu_percent"] for m in first_half) / len(first_half)
        second_cpu = sum(m["system"]["cpu_percent"] for m in second_half) / len(second_half)

        first_memory = sum(m["system"]["memory_used_mb"] for m in first_half) / len(first_half)
        second_memory = sum(m["system"]["memory_used_mb"] for m in second_half) / len(second_half)

        # Determine trends
        cpu_trend = "increasing" if second_cpu > first_cpu * 1.1 else "decreasing" if second_cpu < first_cpu * 0.9 else "stable"
        memory_trend = "increasing" if second_memory > first_memory * 1.1 else "decreasing" if second_memory < first_memory * 0.9 else "stable"

        return {
            "cpu": cpu_trend,
            "memory": memory_trend,
            "overall": "concerning" if cpu_trend == "increasing" and memory_trend == "increasing" else "stable"
        }

    def generate_performance_recommendations(self, metrics: List[Dict[str, Any]]) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []

        avg_cpu = sum(m["system"]["cpu_percent"] for m in metrics) / len(metrics)
        avg_memory = sum(m["system"]["memory_used_mb"] for m in metrics) / len(metrics)

        if avg_cpu > 70:
            recommendations.append("Consider optimizing CPU-intensive operations or upgrading hardware")

        if avg_memory > 400:
            recommendations.append("Memory usage is high - consider cache optimization or memory cleanup")

        cache_size = self.calculate_cache_size()
        if cache_size > 50:
            recommendations.append("Consider cleaning up old cache files to free disk space")

        if not recommendations:
            recommendations.append("Performance metrics are within acceptable ranges")

        return recommendations
```

## Common Pitfalls and Solutions

### 1. Evidence Management Pitfalls

#### Pitfall: Evidence Overload
**Problem**: Too many evidence files making it difficult to find relevant information.

**Solution**:
```bash
# Implement evidence retention policy
speckit evidence cleanup --retention 90days --compress-old

# Use evidence tagging and categorization
speckit evidence tag --task-id TSK-001 --tags security,performance

# Generate evidence summaries
speckit evidence summary --task-id TSK-001 --format markdown
```

#### Pitfall: Inconsistent Evidence Quality
**Problem**: Evidence files vary in quality and completeness.

**Solution**:
```json
{
  "evidence_quality_controls": {
    "validation_rules": "strict",
    "required_fields": ["timestamp", "evidence_type", "task_id", "data"],
    "quality_threshold": 0.8,
    "auto_enhancement": true
  }
}
```

### 2. Task Management Pitfalls

#### Pitfall: Task Dependencies Not Managed
**Problem**: Tasks blocked by unclear or circular dependencies.

**Solution**:
```bash
# Visualize dependencies
speckit tasks dependencies --visualize

# Detect circular dependencies
speckit tasks detect-cycles

# Auto-resolve simple dependencies
speckit tasks resolve-dependencies --auto
```

#### Pitfall: Task Size Inconsistency
**Problem**: Tasks are too large or too small, affecting workflow efficiency.

**Solution**:
```bash
# Analyze task sizes
speckit tasks analyze-size --recommendations

# Auto-split large tasks
speckit tasks split --task-id TSK-001 --max-size 3days

# Combine related small tasks
speckit tasks combine --tasks TSK-005,TSK-006 --new-task "Combined task"
```

### 3. Quality Assurance Pitfalls

#### Pitfall: Quality Gates Too Strict or Lenient
**Problem**: Quality gates either block all progress or allow poor quality.

**Solution**:
```bash
# Calibrate quality thresholds
speckit quality calibrate --baseline 30days --target 0.8

# Implement graduated quality gates
speckit quality configure --graduated-gates --stage-appropriate

# Monitor quality gate effectiveness
speckit quality monitor --effectiveness-report
```

#### Pitfall: Slow Quality Validation
**Problem**: Quality checks take too long, slowing development.

**Solution**:
```json
{
  "quality_optimization": {
    "parallel_execution": true,
    "incremental_checks": true,
    "caching_enabled": true,
    "fast_feedback_mode": true
  }
}
```

## Conclusion

This comprehensive guide provides best practices and workflows for maximizing the value of Speckit in development environments. By following these practices, teams can:

- **Improve Quality**: Consistent validation and evidence collection
- **Increase Productivity**: Streamlined workflows and automation
- **Enhance Collaboration**: Clear task management and communication patterns
- **Ensure Sustainability**: Performance optimization and maintenance strategies
- **Enable Continuous Improvement**: Analytics and monitoring capabilities

The key to success is adapting these practices to your specific context while maintaining the core principles of evidence-based development and continuous validation. Regular review and refinement of these practices will ensure they remain effective as your team and projects evolve.
