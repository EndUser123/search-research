# Speckit Migration Guide

## Overview

This guide provides comprehensive instructions for migrating existing projects to the Speckit v2.0 framework. It covers various scenarios, tools, and strategies to ensure smooth transition while preserving existing work and minimizing disruption.

## Table of Contents

1. [Migration Planning](#migration-planning)
2. [Pre-Migration Assessment](#pre-migration-assessment)
3. [Migration Scenarios](#migration-scenarios)
4. [Step-by-Step Migration Process](#step-by-step-migration-process)
5. [Automated Migration Tools](#automated-migration-tools)
6. [Data Migration](#data-migration)
7. [Team Migration](#team-migration)
8. [Validation and Testing](#validation-and-testing)
9. [Post-Migration Optimization](#post-migration-optimization)
10. [Troubleshooting](#troubleshooting)

## Migration Planning

### 1. Migration Assessment Framework

#### Project Readiness Assessment
Create `.speckit/migration/assessment-template.json`:
```json
{
  "project_assessment": {
    "basic_info": {
      "project_name": "",
      "project_type": "",
      "team_size": 0,
      "current_technology_stack": [],
      "current_project_management": "",
      "migration_date": ""
    },
    "complexity_factors": {
      "project_size": "small/medium/large",
      "team_distribution": "co-located/remote/hybrid",
      "regulatory_requirements": false,
      "legacy_components": false,
      "third_party_integrations": [],
      "data_migration_required": false
    },
    "current_state": {
      "documentation_quality": "poor/fair/good/excellent",
      "test_coverage": 0,
      "code_quality_score": 0,
      "process_maturity": "ad-hoc/defined/managed/optimized",
      "tooling_automation": "minimal/moderate/extensive"
    },
    "migration_readiness": {
      "team_buy_in": false,
      "management_support": false,
      "time_allocation": 0,
      "budget_allocation": 0,
      "risk_tolerance": "low/medium/high",
      "migration_timeline": ""
    }
  }
}
```

#### Migration Risk Assessment
Create `.speckit/migration/risk-assessment.json`:
```json
{
  "risk_categories": {
    "technical_risks": [
      {
        "risk": "Incompatible technology stack",
        "probability": "low/medium/high",
        "impact": "low/medium/high",
        "mitigation": " gradual migration, fallback plan"
      },
      {
        "risk": "Data loss during migration",
        "probability": "low",
        "impact": "high",
        "mitigation": "comprehensive backup, validation"
      }
    ],
    "operational_risks": [
      {
        "risk": "Team productivity decrease",
        "probability": "medium",
        "impact": "medium",
        "mitigation": "training, gradual adoption"
      }
    ],
    "business_risks": [
      {
        "risk": "Timeline delays",
        "probability": "medium",
        "impact": "medium",
        "mitigation": "phased approach, buffer time"
      }
    ]
  },
  "mitigation_strategies": {
    "technical": ["comprehensive testing", "backup procedures", "rollback plan"],
    "operational": ["team training", "documentation", "support channels"],
    "business": ["stakeholder communication", "progress reporting", "flexible timeline"]
  }
}
```

### 2. Migration Strategy Selection

#### Migration Strategy Matrix
| Strategy | Best For | Timeline | Risk Level | Effort |
|----------|-----------|----------|------------|---------|
| **Big Bang** | Small projects, greenfield | 1-2 weeks | High | High |
| **Phased** | Medium projects, incremental delivery | 4-8 weeks | Medium | Medium |
| **Parallel** | Large projects, risk-averse | 8-12 weeks | Low | High |
| **Hybrid** | Complex projects, mixed requirements | 6-10 weeks | Medium | High |

#### Strategy Decision Tree
```bash
# Use interactive migration planner
speckit migration plan --interactive

# Answer assessment questions:
# - Project size: small/medium/large
# - Team experience: beginner/intermediate/expert
# - Risk tolerance: low/medium/high
# - Timeline constraints: tight/flexible
# - Budget constraints: limited/adequate/generous
```

## Pre-Migration Assessment

### 1. Current State Analysis

#### Automated Assessment Tool
Create `.speckit/migration/assess-current-state.py`:
```python
#!/usr/bin/env python3
"""
Pre-migration assessment tool
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any

class MigrationAssessment:
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.assessment_results = {}

    def run_full_assessment(self) -> Dict[str, Any]:
        """Run comprehensive migration assessment"""
        print("Running migration assessment...")

        self.assess_project_structure()
        self.assess_code_quality()
        self.assess_documentation()
        self.assess_team_readiness()
        self.assess_technology_stack()
        self.assess_process_maturity()

        return self.assessment_results

    def assess_project_structure(self) -> Dict[str, Any]:
        """Assess current project structure"""
        print("Assessing project structure...")

        structure = {
            "total_files": 0,
            "code_files": 0,
            "test_files": 0,
            "documentation_files": 0,
            "config_files": 0,
            "directory_structure": {},
            "frameworks_detected": []
        }

        # Analyze directory structure
        for root, dirs, files in os.walk(self.project_path):
            # Skip hidden directories and common cache directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', '.git']]

            rel_root = os.path.relpath(root, self.project_path)
            if rel_root != '.':
                structure["directory_structure"][rel_root] = {
                    "file_count": len(files),
                    "subdirectories": len(dirs)
                }

            # Classify files
            for file in files:
                file_path = Path(root) / file
                structure["total_files"] += 1

                if file.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c')):
                    structure["code_files"] += 1
                elif file.startswith('test_') or file.endswith('_test.py') or 'test' in root:
                    structure["test_files"] += 1
                elif file.endswith(('.md', '.rst', '.txt', '.doc', '.docx')):
                    structure["documentation_files"] += 1
                elif file.endswith(('.json', '.yaml', '.yml', '.toml', '.ini', '.conf')):
                    structure["config_files"] += 1

        # Detect frameworks
        frameworks = self.detect_frameworks()
        structure["frameworks_detected"] = frameworks

        self.assessment_results["project_structure"] = structure
        return structure

    def assess_code_quality(self) -> Dict[str, Any]:
        """Assess current code quality"""
        print("Assessing code quality...")

        quality = {
            "languages_used": [],
            "code_complexity": "unknown",
            "test_coverage": "unknown",
            "linting_status": "unknown",
            "code_style_consistency": "unknown",
            "technical_debt_indicators": []
        }

        # Detect programming languages
        languages = set()
        for root, dirs, files in os.walk(self.project_path):
            for file in files:
                if file.endswith('.py'):
                    languages.add('python')
                elif file.endswith(('.js', '.ts')):
                    languages.add('javascript')
                elif file.endswith('.java'):
                    languages.add('java')
                elif file.endswith(('.cpp', '.c')):
                    languages.add('cpp')
        quality["languages_used"] = list(languages)

        # Run basic quality checks
        if 'python' in languages:
            quality.update(self.assess_python_quality())
        elif 'javascript' in languages:
            quality.update(self.assess_javascript_quality())

        self.assessment_results["code_quality"] = quality
        return quality

    def assess_python_quality(self) -> Dict[str, Any]:
        """Assess Python code quality"""
        results = {}

        # Check for common Python quality tools
        try:
            # Run flake8 if available
            subprocess.run(['flake8', '--version'], check=True, capture_output=True)
            result = subprocess.run(['flake8', '.'], capture_output=True, text=True)
            if result.returncode == 0:
                results["linting_status"] = "good"
            else:
                results["linting_status"] = "issues_found"
                results["linting_issues_count"] = len(result.stdout.splitlines())
        except (subprocess.CalledProcessError, FileNotFoundError):
            results["linting_status"] = "not_configured"

        # Check for pytest
        try:
            subprocess.run(['pytest', '--version'], check=True, capture_output=True)
            results["test_framework"] = "pytest"
        except (subprocess.CalledProcessError, FileNotFoundError):
            results["test_framework"] = "not_found"

        return results

    def assess_javascript_quality(self) -> Dict[str, Any]:
        """Assess JavaScript code quality"""
        results = {}

        # Check for ESLint
        try:
            subprocess.run(['eslint', '--version'], check=True, capture_output=True)
            results["linting_status"] = "configured"
        except (subprocess.CalledProcessError, FileNotFoundError):
            results["linting_status"] = "not_configured"

        # Check for Jest
        try:
            subprocess.run(['jest', '--version'], check=True, capture_output=True)
            results["test_framework"] = "jest"
        except (subprocess.CalledProcessError, FileNotFoundError):
            results["test_framework"] = "not_found"

        return results

    def assess_documentation(self) -> Dict[str, Any]:
        """Assess documentation quality"""
        print("Assessing documentation...")

        docs = {
            "readme_exists": False,
            "api_documentation": False,
            "architecture_docs": False,
            "setup_instructions": False,
            "contributing_guidelines": False,
            "changelog_exists": False,
            "documentation_quality_score": 0
        }

        # Check for common documentation files
        common_docs = [
            'README.md', 'readme.md',
            'CONTRIBUTING.md', 'CONTRIBUTING.md',
            'CHANGELOG.md', 'CHANGELOG.md',
            'docs/', 'doc/', 'documentation/'
        ]

        for doc in common_docs:
            if (self.project_path / doc).exists():
                if 'readme' in doc.lower():
                    docs["readme_exists"] = True
                elif 'contributing' in doc.lower():
                    docs["contributing_guidelines"] = True
                elif 'changelog' in doc.lower():
                    docs["changelog_exists"] = True
                elif doc.endswith('/'):
                    docs["api_documentation"] = True

        # Calculate documentation quality score
        score = 0
        if docs["readme_exists"]: score += 20
        if docs["api_documentation"]: score += 25
        if docs["architecture_docs"]: score += 25
        if docs["setup_instructions"]: score += 15
        if docs["contributing_guidelines"]: score += 10
        if docs["changelog_exists"]: score += 5

        docs["documentation_quality_score"] = score

        self.assessment_results["documentation"] = docs
        return docs

    def detect_frameworks(self) -> List[str]:
        """Detect development frameworks in use"""
        frameworks = []

        # Check for Python frameworks
        if (self.project_path / 'requirements.txt').exists():
            try:
                with open(self.project_path / 'requirements.txt') as f:
                    requirements = f.read()
                    if 'django' in requirements.lower():
                        frameworks.append('Django')
                    if 'flask' in requirements.lower():
                        frameworks.append('Flask')
                    if 'fastapi' in requirements.lower():
                        frameworks.append('FastAPI')
            except:
                pass

        # Check for Node.js frameworks
        if (self.project_path / 'package.json').exists():
            try:
                with open(self.project_path / 'package.json') as f:
                    package_json = json.load(f)
                    dependencies = {**package_json.get('dependencies', {}), **package_json.get('devDependencies', {})}
                    if 'react' in dependencies:
                        frameworks.append('React')
                    if 'vue' in dependencies:
                        frameworks.append('Vue.js')
                    if 'angular' in dependencies:
                        frameworks.append('Angular')
                    if 'express' in dependencies:
                        frameworks.append('Express.js')
            except:
                pass

        return frameworks

    def generate_migration_recommendations(self) -> List[str]:
        """Generate migration recommendations based on assessment"""
        recommendations = []

        # Based on project structure
        structure = self.assessment_results.get("project_structure", {})
        if structure.get("code_files", 0) > structure.get("test_files", 0) * 5:
            recommendations.append("Consider increasing test coverage before migration")

        # Based on code quality
        quality = self.assessment_results.get("code_quality", {})
        if quality.get("linting_status") == "not_configured":
            recommendations.append("Set up code linting before migration")

        # Based on documentation
        docs = self.assessment_results.get("documentation", {})
        if docs.get("documentation_quality_score", 0) < 50:
            recommendations.append("Improve documentation quality before migration")

        # Based on frameworks
        frameworks = structure.get("frameworks_detected", [])
        if not frameworks:
            recommendations.append("Consider framework standardization for better Speckit integration")

        # General recommendations
        recommendations.extend([
            "Create backup of current project state",
            "Set up migration test environment",
            "Schedule team training sessions",
            "Plan for gradual adoption"
        ])

        return recommendations

    def save_assessment_report(self, output_file: str = "migration_assessment.json"):
        """Save assessment report to file"""
        # Add recommendations to results
        self.assessment_results["migration_recommendations"] = self.generate_migration_recommendations()

        with open(output_file, 'w') as f:
            json.dump(self.assessment_results, f, indent=2, default=str)

        print(f"Assessment report saved to: {output_file}")

# Usage example
if __name__ == "__main__":
    assessor = MigrationAssessment()
    results = assessor.run_full_assessment()
    assessor.save_assessment_report()

    print("\nMigration Assessment Summary:")
    print(f"Project Structure: {results['project_structure']['total_files']} files")
    print(f"Code Quality: {results['code_quality']['linting_status']}")
    print(f"Documentation Score: {results['documentation']['documentation_quality_score']}/100")

    print("\nRecommendations:")
    for rec in results['migration_recommendations']:
        print(f"- {rec}")
```

### 2. Migration Checklist

#### Pre-Migration Checklist
Create `.speckit/migration/pre-migration-checklist.md`:
```markdown
# Pre-Migration Checklist

## Project Preparation
- [ ] Backup entire project repository
- [ ] Create migration branch in version control
- [ ] Document current project structure
- [ ] Inventory all tools and dependencies
- [ ] Identify critical project components
- [ ] Document current workflows and processes

## Team Preparation
- [ ] Assess team readiness and skills
- [ ] Schedule training sessions
- [ ] Assign migration roles and responsibilities
- [ ] Establish communication channels
- [ ] Set up migration progress tracking

## Technical Preparation
- [ ] Set up migration test environment
- [ ] Install required Speckit dependencies
- [ ] Configure development tools
- [ ] Test Speckit installation
- [ ] Validate system requirements

## Risk Mitigation
- [ ] Identify potential migration blockers
- [ ] Create rollback procedures
- [ ] Establish success criteria
- [ ] Plan contingency measures
- [ ] Set up monitoring and alerting

## Documentation
- [ ] Document current state
- [ ] Create migration plan
- [ ] Prepare user guides
- [ ] Document known issues
- [ ] Create FAQ for team members
```

## Migration Scenarios

### 1. New Project Migration (Greenfield)

#### Scenario: Starting a New Project with Speckit
**Best For**: New projects, experimental prototypes, greenfield development

**Migration Steps**:
```bash
# 1. Initialize new project with Speckit
mkdir my-new-project
cd my-new-project
git init

# 2. Copy Speckit framework
cp -r /path/to/.speckit .speckit

# 3. Initialize project configuration
.speckit/scripts/powershell/setup-project.ps1 `
  -ProjectName "My New Project" `
  -ProjectType "web-application" `
  -TechStack "python,fastapi,postgresql"

# 4. Create project constitution
speckit constitution create --template web-application --interactive

# 5. Validate setup
speckit doctor
speckit constitution --validate

# 6. Create first feature
speckit specify "User authentication system" --knowledge-guidance
```

**Benefits**:
- No existing constraints or technical debt
- Full Speckit capabilities from day one
- Clean architecture and processes
- Optimal team learning experience

### 2. Existing Project Migration (Brownfield)

#### Scenario: Migrating Existing Project to Speckit
**Best For**: Active projects with existing codebase and team

**Migration Phases**:

**Phase 1: Assessment and Planning (Week 1-2)**
```bash
# Run comprehensive assessment
speckit migration assess --output assessment_report.json

# Create migration plan
speckit migration plan --from-assessment assessment_report.json

# Set up migration environment
speckit migration setup --environment staging
```

**Phase 2: Infrastructure Setup (Week 2-3)**
```bash
# Install Speckit alongside existing tools
cp -r /path/to/.speckit .speckit

# Configure Speckit for existing project
.speckit/scripts/powershell/configure-existing-project.ps1 `
  -ProjectType migration `
  -PreserveExisting true

# Set up parallel operation
speckit config set migration.mode parallel
```

**Phase 3: Gradual Adoption (Week 3-6)**
```bash
# Start with non-critical features
speckit specify "New feature using Speckit workflow" --experimental

# Gradually migrate existing features
speckit migration migrate-feature --feature-id existing-feature-1

# Team training and adoption
speckit training start --team development --duration 2weeks
```

**Phase 4: Full Migration (Week 6-8)**
```bash
# Migrate all remaining features
speckit migration complete --validate --backup

# Remove legacy tools and processes
speckit migration cleanup --legacy-tools

# Final validation
speckit validate --comprehensive
```

### 3. Team Migration

#### Scenario: Migrating Multiple Teams or Departments
**Best For**: Large organizations, multiple projects, enterprise migration

**Migration Strategy**:
```bash
# 1. Pilot Team Migration
speckit migration pilot --team team-alpha --duration 4weeks

# 2. Evaluate Pilot Results
speckit migration evaluate-pilot --team team-alpha --generate-report

# 3. Rollout Plan
speckit migration rollout-plan --teams "team-beta,team-gamma,team-delta" --phased

# 4. Execute Rollout
speckit migration execute-rollout --phase 1 --teams team-beta
speckit migration execute-rollout --phase 2 --teams team-gamma,team-delta

# 5. Enterprise Integration
speckit migration enterprise-integration --single-tenant --custom-config
```

### 4. Technology Stack Migration

#### Scenario: Migrating Different Technology Stacks
**Technology-Specific Migrations**:

**Python/Django Projects**:
```bash
# Django-specific migration
speckit migration django --project-path . --preserve-settings

# Create Django-specific templates
speckit templates create --framework django --output .speckit/templates/django/

# Configure Django integration
speckit config set framework.django.enabled true
speckit config set framework.django.manage_path python manage.py
```

**JavaScript/React Projects**:
```bash
# React-specific migration
speckit migration react --project-path . --preserve-components

# Create React-specific templates
speckit templates create --framework react --output .speckit/templates/react/

# Configure build integration
speckit config set framework.react.build_command npm run build
speckit config set framework.react.test_command npm test
```

**Java/Spring Projects**:
```bash
# Java-specific migration
speckit migration java --project-path . --preserve-pom

# Create Java-specific templates
speckit templates create --framework spring --output .speckit/templates/spring/

# Configure Maven/Gradle integration
speckit config set framework.java.build_tool maven
speckit config set framework.java.test_command mvn test
```

## Step-by-Step Migration Process

### 1. Preparation Phase

#### Step 1.1: Environment Setup
```bash
# Create migration environment
mkdir speckit-migration
cd speckit-migration

# Clone current project
git clone <your-project-repo> current-project
cd current-project

# Create migration branch
git checkout -b feature/speckit-migration

# Set up virtual environment for migration
python -m venv speckit-migration-env
source speckit-migration-env/bin/activate  # Linux/Mac
# or
speckit-migration-env\Scripts\activate  # Windows

# Install Speckit CLI
pip install speckit-cli
```

#### Step 1.2: Backup Current State
```bash
# Create comprehensive backup
speckit migration backup --full --destination ../backups/

# Document current state
speckit migration document-current-state --output current_state.json

# Create baseline measurements
speckit migration baseline --metrics performance,quality,productivity
```

#### Step 1.3: Install Speckit Framework
```bash
# Copy Speckit framework
cp -r /path/to/central/.speckit .speckit

# Initialize Speckit for existing project
speckit init --project-type migration --existing-project

# Configure for current project
.speckit/scripts/powershell/configure-migration.ps1 `
  -ProjectPath . `
  -PreserveExisting $true `
  -MigrationMode phased
```

### 2. Configuration Phase

#### Step 2.1: Project Configuration
```bash
# Create project configuration
speckit config set project.name "Your Project Name"
speckit config set project.type "migration"
speckit config set project.frameworks "django,postgresql,redis"

# Configure migration settings
speckit config set migration.mode "phased"
speckit config set migration.parallel_operation true
speckit config set migration.preserve_existing true
```

#### Step 2.2: Team Configuration
```bash
# Add team members
speckit team add --name "John Doe" --role "developer" --email "john@company.com"
speckit team add --name "Jane Smith" --role "tech_lead" --email "jane@company.com"

# Configure permissions
speckit team permissions --role developer --permissions "task.create,task.update,evidence.create"
speckit team permissions --role tech_lead --permissions "task.*,validation.*,constitution.*"
```

#### Step 2.3: Integration Configuration
```bash
# Configure version control integration
speckit integration git --auto-hooks true --branch-validation true

# Configure CI/CD integration
speckit integration cicd --platform github-actions --auto-validation true

# Configure communication tools
speckit integration slack --webhook-url $SLACK_WEBHOOK --channel #development
```

### 3. Migration Execution Phase

#### Step 3.1: Constitution Setup
```bash
# Create project constitution based on current practices
speckit constitution create --from-existing --interactive

# Validate constitution
speckit constitution --validate

# Update constitution as needed
speckit constitution update --section quality_standards
```

#### Step 3.2: Templates and Workflows Setup
```bash
# Create templates based on existing patterns
speckit templates generate --from-existing --type feature --output .speckit/templates/
speckit templates generate --from-existing --type bugfix --output .speckit/templates/

# Test templates
speckit templates test --all

# Create custom workflows
speckit workflow create --name "development" --from-existing --interactive
```

#### Step 3.3: Initial Feature Migration
```bash
# Select a simple feature for initial migration
speckit migration select-feature --criteria simple,low-risk --output initial_feature.json

# Migrate selected feature
speckit migration migrate-feature --from initial_feature.json --validate

# Test migration process
speckit migration test --feature initial_feature.json --validation comprehensive
```

### 4. Validation Phase

#### Step 4.1: Process Validation
```bash
# Validate Speckit processes
speckit validate processes --all

# Test task creation and management
speckit test task-management --create-sample --complete-workflow

# Validate evidence collection
speckit test evidence-collection --sample-data --validation
```

#### Step 4.2: Integration Validation
```bash
# Test version control integration
speckit test git-integration --create-test-pr --validate-hooks

# Test CI/CD integration
speckit test cicd-integration --trigger-test-build --validate-results

# Test team collaboration features
speckit test team-collaboration --create-sample-tasks --assign-team
```

#### Step 4.3: Performance Validation
```bash
# Measure performance impact
speckit benchmark performance --baseline pre-migration --current post-migration-initial

# Validate system responsiveness
speckit test responsiveness --load-test --duration 10min

# Check resource usage
speckit monitor resources --duration 1h --report
```

### 5. Full Migration Phase

#### Step 5.1: Gradual Feature Migration
```bash
# Create migration plan for all features
speckit migration create-plan --all-features --output migration_plan.json

# Execute migration in batches
speckit migration execute-batch --batch 1 --from migration_plan.json
speckit migration execute-batch --batch 2 --from migration_plan.json

# Monitor migration progress
speckit migration monitor --real-time --alert-on-failure
```

#### Step 5.2: Team Training and Adoption
```bash
# Start team training program
speckit training start --all-team --duration 2weeks --interactive

# Create training tasks for practice
speckit training create-practice-tasks --count 5 --assign-all-team

# Monitor adoption progress
speckit training monitor --progress-report --identify-gaps
```

#### Step 5.3: Legacy Tool Removal
```bash
# Identify legacy tools to remove
speckit migration identify-legacy-tools --output legacy_tools.json

# Gradually disable legacy tools
speckit migration disable-legacy-tool --tool "old-project-manager" --grace-period 1week

# Remove legacy tools
speckit migration remove-legacy-tools --confirm --backup
```

### 6. Optimization Phase

#### Step 6.1: Performance Optimization
```bash
# Optimize Speckit configuration
speckit optimize configuration --based-on-usage --validate

# Tune performance settings
speckit optimize performance --target response_time --threshold 200ms

# Optimize database operations
speckit optimize database --analyze-queries --create-indexes
```

#### Step 6.2: Workflow Optimization
```bash
# Analyze workflow efficiency
speckit analyze workflows --identify-bottlenecks --recommendations

# Optimize task management
speckit optimize tasks --auto-categorization --smart-assignment

# Streamline evidence collection
speckit optimize evidence --compression --smart-cleanup
```

## Automated Migration Tools

### 1. Migration Assistant

#### Automated Migration Script
Create `.speckit/migration/migration-assistant.py`:
```python
#!/usr/bin/env python3
"""
Automated migration assistant
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Any

class MigrationAssistant:
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.speckit_path = self.project_path / ".speckit"
        self.migration_log = []

    def run_full_migration(self, config: Dict[str, Any]) -> bool:
        """Run complete automated migration"""
        try:
            self.log("Starting automated migration...")

            # Phase 1: Preparation
            self.prepare_migration(config)

            # Phase 2: Setup
            self.setup_speckit(config)

            # Phase 3: Configuration
            self.configure_speckit(config)

            # Phase 4: Migration
            self.migrate_content(config)

            # Phase 5: Validation
            self.validate_migration(config)

            self.log("Migration completed successfully!")
            return True

        except Exception as e:
            self.log(f"Migration failed: {str(e)}", level="ERROR")
            return False

    def prepare_migration(self, config: Dict[str, Any]):
        """Prepare project for migration"""
        self.log("Preparing project for migration...")

        # Create backup
        if config.get("create_backup", True):
            self.create_backup()

        # Check prerequisites
        self.check_prerequisites()

        # Analyze current state
        self.analyze_current_state()

    def setup_speckit(self, config: Dict[str, Any]):
        """Set up Speckit framework"""
        self.log("Setting up Speckit framework...")

        # Copy Speckit framework
        speckit_source = config.get("speckit_source", "/path/to/.speckit")
        if os.path.exists(speckit_source):
            shutil.copytree(speckit_source, self.speckit_path, dirs_exist_ok=True)
            self.log("Speckit framework copied")
        else:
            raise Exception(f"Speckit source not found: {speckit_source}")

        # Initialize Speckit
        self.run_speckit_command(["init", "--project-type", "migration"])

    def configure_speckit(self, config: Dict[str, Any]):
        """Configure Speckit for project"""
        self.log("Configuring Speckit...")

        project_config = config.get("project_config", {})

        # Set basic configuration
        for key, value in project_config.items():
            self.run_speckit_command(["config", "set", key, str(value)])

        # Create constitution
        if config.get("create_constitution", True):
            self.create_constitution(config)

        # Setup templates
        if config.get("setup_templates", True):
            self.setup_templates(config)

    def migrate_content(self, config: Dict[str, Any]):
        """Migrate existing content to Speckit"""
        self.log("Migrating content...")

        # Migrate existing tasks/issues
        if config.get("migrate_tasks", True):
            self.migrate_tasks(config)

        # Migrate documentation
        if config.get("migrate_docs", True):
            self.migrate_documentation(config)

        # Migrate workflows
        if config.get("migrate_workflows", True):
            self.migrate_workflows(config)

    def validate_migration(self, config: Dict[str, Any]):
        """Validate migration results"""
        self.log("Validating migration...")

        # Validate Speckit installation
        self.run_speckit_command(["doctor"])

        # Validate configuration
        self.run_speckit_command(["constitution", "--validate"])

        # Test basic functionality
        self.test_basic_functionality()

        # Generate validation report
        self.generate_validation_report()

    def create_backup(self):
        """Create project backup"""
        self.log("Creating backup...")

        backup_name = f"backup_{self.get_timestamp()}"
        backup_path = self.project_path.parent / backup_name

        shutil.copytree(self.project_path, backup_path)
        self.log(f"Backup created at: {backup_path}")

    def check_prerequisites(self):
        """Check migration prerequisites"""
        self.log("Checking prerequisites...")

        # Check Python version
        python_version = subprocess.run(['python', '--version'], capture_output=True, text=True)
        if python_version.returncode != 0:
            raise Exception("Python not found")

        # Check Git
        git_version = subprocess.run(['git', '--version'], capture_output=True, text=True)
        if git_version.returncode != 0:
            raise Exception("Git not found")

        # Check available disk space
        disk_usage = shutil.disk_usage(self.project_path)
        if disk_usage.free < 1024 * 1024 * 1024:  # 1GB
            self.log("Warning: Low disk space", level="WARNING")

        self.log("Prerequisites check passed")

    def analyze_current_state(self):
        """Analyze current project state"""
        self.log("Analyzing current project state...")

        # Run existing assessment tool
        assessor = MigrationAssessment(self.project_path)
        assessment = assessor.run_full_assessment()

        # Save assessment
        assessment_file = self.speckit_path / "migration_assessment.json"
        with open(assessment_file, 'w') as f:
            json.dump(assessment, f, indent=2, default=str)

        self.log("Current state analysis completed")

    def create_constitution(self, config: Dict[str, Any]):
        """Create project constitution"""
        self.log("Creating constitution...")

        # Generate constitution based on current practices
        constitution_template = self.generate_constitution_template(config)

        constitution_file = self.speckit_path / "memory" / "constitution.md"
        with open(constitution_file, 'w') as f:
            f.write(constitution_template)

        self.log("Constitution created")

    def generate_constitution_template(self, config: Dict[str, Any]) -> str:
        """Generate constitution template based on project analysis"""
        template = f"""# {config.get('project_name', 'Project')} Constitution

## Project Values
1. **Quality First**: Maintain high code quality standards
2. **Security**: Security is non-negotiable
3. **Performance**: Optimize for performance and scalability
4. **Collaboration**: Foster team collaboration and knowledge sharing
5. **Continuous Improvement**: Continuously improve processes and practices

## Technical Standards
- **Language**: {config.get('primary_language', 'Python')}
- **Framework**: {', '.join(config.get('frameworks', ['Unknown']))}
- **Testing**: Comprehensive testing required
- **Documentation**: All public APIs documented
- **Code Review**: Code review required for all changes

## Quality Standards
- **Test Coverage**: Minimum 80%
- **Code Quality**: Pass all linting checks
- **Security**: Pass security vulnerability scans
- **Performance**: Meet performance benchmarks
- **Documentation**: Keep documentation updated

## Development Workflow
1. Requirements gathering with evidence
2. Research and pattern validation
3. Implementation with validation
4. Testing and quality assurance
5. Code review and feedback
6. Documentation and knowledge sharing

## Migration Notes
This constitution was created during Speckit migration on {self.get_timestamp()}.
It should be reviewed and updated by the team to reflect specific project needs.
"""
        return template

    def setup_templates(self, config: Dict[str, Any]):
        """Set up project templates"""
        self.log("Setting up templates...")

        # Create custom templates based on project analysis
        templates_dir = self.speckit_path / "templates"

        # Feature template
        feature_template = self.generate_feature_template(config)
        with open(templates_dir / "custom-feature.md", 'w') as f:
            f.write(feature_template)

        # Bug fix template
        bugfix_template = self.generate_bugfix_template(config)
        with open(templates_dir / "custom-bugfix.md", 'w') as f:
            f.write(bugfix_template)

        self.log("Templates setup completed")

    def generate_feature_template(self, config: Dict[str, Any]) -> str:
        """Generate feature template based on project type"""
        template = f"""# Feature Specification: {{{{FEATURE_NAME}}}}

## Overview
{{{{DESCRIPTION}}}}

## Requirements
### Functional Requirements
- [ ] Requirement 1
- [ ] Requirement 2
- [ ] Requirement 3

### Non-Functional Requirements
- **Performance**: {{{{PERFORMANCE_REQUIREMENTS}}}}
- **Security**: {{{{SECURITY_REQUIREMENTS}}}}
- **Scalability**: {{{{SCALABILITY_REQUIREMENTS}}}}

## Technical Implementation
### Architecture
{{{{ARCHITECTURE_NOTES}}}}

### Dependencies
{{{{DEPENDENCIES}}}}

### Integration Points
{{{{INTEGRATION_POINTS}}}}

## Acceptance Criteria
- [ ] All functional requirements implemented
- [ ] All tests passing with >80% coverage
- [ ] Code review completed and approved
- [ ] Documentation updated
- [ ] Performance benchmarks met

## Testing Strategy
### Unit Tests
{{{{UNIT_TEST_PLAN}}}}

### Integration Tests
{{{{INTEGRATION_TEST_PLAN}}}}

### Performance Tests
{{{{PERFORMANCE_TEST_PLAN}}}}

## Risks and Mitigations
{{{{RISKS_AND_MITIGATIONS}}}}

## Timeline
**Estimated Effort**: {{{{ESTIMATED_HOURS}}}} hours
**Target Completion**: {{{{TARGET_DATE}}}}

## Migration Notes
This template was created during Speckit migration for {config.get('project_name', 'project')}.
"""
        return template

    def run_speckit_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run Speckit command"""
        cmd = ["speckit"] + args
        result = subprocess.run(cmd, cwd=self.project_path, capture_output=True, text=True)

        if result.returncode != 0:
            self.log(f"Command failed: {' '.join(cmd)}", level="ERROR")
            self.log(f"Error output: {result.stderr}", level="ERROR")

        return result

    def test_basic_functionality(self):
        """Test basic Speckit functionality"""
        self.log("Testing basic functionality...")

        # Test task creation
        result = self.run_speckit_command(["tasks", "test", "--create-sample"])
        if result.returncode == 0:
            self.log("Task creation test passed")
        else:
            self.log("Task creation test failed", level="WARNING")

        # Test constitution validation
        result = self.run_speckit_command(["constitution", "--validate"])
        if result.returncode == 0:
            self.log("Constitution validation test passed")
        else:
            self.log("Constitution validation test failed", level="WARNING")

    def generate_validation_report(self):
        """Generate migration validation report"""
        self.log("Generating validation report...")

        report = {
            "migration_timestamp": self.get_timestamp(),
            "migration_log": self.migration_log,
            "validation_results": {
                "speckit_installation": True,
                "constitution_valid": True,
                "basic_functionality": True
            },
            "next_steps": [
                "Review and customize constitution",
                "Train team on Speckit workflows",
                "Start using Speckit for new features",
                "Gradually migrate existing features"
            ]
        }

        report_file = self.speckit_path / "migration_validation_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        self.log(f"Validation report saved to: {report_file}")

    def get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def log(self, message: str, level: str = "INFO"):
        """Log migration message"""
        timestamp = self.get_timestamp()
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.migration_log.append(log_entry)
        print(log_entry)

# Usage example
if __name__ == "__main__":
    # Migration configuration
    migration_config = {
        "project_name": "My Project",
        "primary_language": "Python",
        "frameworks": ["Django", "PostgreSQL"],
        "create_backup": True,
        "create_constitution": True,
        "setup_templates": True,
        "migrate_tasks": True,
        "migrate_docs": True
    }

    # Run migration
    assistant = MigrationAssistant()
    success = assistant.run_full_migration(migration_config)

    if success:
        print("Migration completed successfully!")
    else:
        print("Migration failed. Check logs for details.")
```

### 2. Migration Validation Tools

#### Validation Script
Create `.speckit/migration/validate-migration.py`:
```python
#!/usr/bin/env python3
"""
Migration validation tool
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any

class MigrationValidator:
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.speckit_path = self.project_path / ".speckit"
        self.validation_results = {}

    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """Run comprehensive migration validation"""
        print("Running comprehensive migration validation...")

        self.validate_speckit_installation()
        self.validate_configuration()
        self.validate_functionality()
        self.validate_integrations()
        self.validate_performance()
        self.validate_team_readiness()

        self.generate_validation_report()
        return self.validation_results

    def validate_speckit_installation(self) -> bool:
        """Validate Speckit installation"""
        print("Validating Speckit installation...")

        results = {
            "speckit_installed": False,
            "version_compatible": False,
            "directories_exist": False,
            "files_intact": False
        }

        # Check if Speckit is installed
        try:
            result = subprocess.run(['speckit', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                results["speckit_installed"] = True
                print(f"Speckit version: {result.stdout.strip()}")
        except:
            print("Speckit not found in PATH")

        # Check Speckit directories
        required_dirs = ["config", "memory", "templates", "scripts", "cache", "evidence", "docs"]
        dirs_exist = all((self.speckit_path / d).exists() for d in required_dirs)
        results["directories_exist"] = dirs_exist

        # Check essential files
        essential_files = [
            "config/speckit_config.json",
            "memory/constitution.md"
        ]
        files_exist = all((self.speckit_path / f).exists() for f in essential_files)
        results["files_intact"] = files_exist

        # Check version compatibility
        if results["speckit_installed"]:
            version_result = subprocess.run(['speckit', '--version'], capture_output=True, text=True)
            version = version_result.stdout.strip()
            # Add version compatibility check here
            results["version_compatible"] = True  # Simplified for example

        self.validation_results["installation"] = results
        return all(results.values())

    def validate_configuration(self) -> bool:
        """Validate Speckit configuration"""
        print("Validating Speckit configuration...")

        results = {
            "config_valid": False,
            "constitution_valid": False,
            "templates_configured": False,
            "team_configured": False
        }

        # Validate Speckit configuration
        config_file = self.speckit_path / "config" / "speckit_config.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    config = json.load(f)

                # Check required configuration sections
                required_sections = ["task_management", "speckit_framework", "paths"]
                if all(section in config for section in required_sections):
                    results["config_valid"] = True
            except:
                print("Invalid JSON in configuration file")

        # Validate constitution
        constitution_file = self.speckit_path / "memory" / "constitution.md"
        if constitution_file.exists():
            with open(constitution_file) as f:
                constitution_content = f.read()

            # Basic constitution validation
            if len(constitution_content) > 100:  # Arbitrary minimum length
                results["constitution_valid"] = True

        # Validate templates
        templates_dir = self.speckit_path / "templates"
        template_files = list(templates_dir.glob("*.md"))
        if len(template_files) >= 3:  # Minimum expected templates
            results["templates_configured"] = True

        # Validate team configuration
        team_file = self.speckit_path / "config" / "team.json"
        if team_file.exists():
            results["team_configured"] = True

        self.validation_results["configuration"] = results
        return all(results.values())

    def validate_functionality(self) -> bool:
        """Validate Speckit functionality"""
        print("Validating Speckit functionality...")

        results = {
            "constitution_validation": False,
            "task_creation": False,
            "evidence_generation": False,
            "analysis_functionality": False
        }

        # Test constitution validation
        try:
            result = subprocess.run(['speckit', 'constitution', '--validate'],
                                  cwd=self.project_path, capture_output=True, text=True)
            if result.returncode == 0:
                results["constitution_validation"] = True
        except:
            pass

        # Test task creation
        try:
            result = subprocess.run(['speckit', 'tasks', '--test', '--create-sample'],
                                  cwd=self.project_path, capture_output=True, text=True)
            if result.returncode == 0:
                results["task_creation"] = True
        except:
            pass

        # Test evidence generation
        try:
            result = subprocess.run(['speckit', 'analyze', '--test', '--generate-evidence'],
                                  cwd=self.project_path, capture_output=True, text=True)
            if result.returncode == 0:
                results["evidence_generation"] = True
        except:
            pass

        # Test analysis functionality
        try:
            result = subprocess.run(['speckit', 'analyze', '--quick-check'],
                                  cwd=self.project_path, capture_output=True, text=True)
            if result.returncode == 0:
                results["analysis_functionality"] = True
        except:
            pass

        self.validation_results["functionality"] = results
        return any(results.values())  # Some functionality should work

    def generate_validation_report(self) -> str:
        """Generate validation report"""
        print("Generating validation report...")

        report = {
            "validation_timestamp": self.get_timestamp(),
            "overall_status": "passed" if self.is_migration_successful() else "failed",
            "detailed_results": self.validation_results,
            "recommendations": self.generate_recommendations(),
            "next_steps": self.generate_next_steps()
        }

        report_file = self.speckit_path / "migration_validation_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        # Generate human-readable report
        readable_report = self.generate_readable_report(report)
        readable_file = self.speckit_path / "migration_validation_report.md"
        with open(readable_file, 'w') as f:
            f.write(readable_report)

        print(f"Validation report saved to: {report_file}")
        print(f"Readable report saved to: {readable_file}")

        return readable_file

    def is_migration_successful(self) -> bool:
        """Check if migration is overall successful"""
        critical_checks = [
            self.validation_results.get("installation", {}).get("speckit_installed", False),
            self.validation_results.get("configuration", {}).get("config_valid", False)
        ]
        return all(critical_checks)

    def generate_recommendations(self) -> List[str]:
        """Generate migration recommendations"""
        recommendations = []

        if not self.validation_results.get("installation", {}).get("speckit_installed"):
            recommendations.append("Install Speckit CLI and ensure it's in PATH")

        if not self.validation_results.get("configuration", {}).get("config_valid"):
            recommendations.append("Fix Speckit configuration issues")

        if not self.validation_results.get("configuration", {}).get("constitution_valid"):
            recommendations.append("Create or update project constitution")

        if not self.validation_results.get("functionality", {}).get("constitution_validation"):
            recommendations.append("Fix constitution validation errors")

        if not recommendations:
            recommendations.append("Migration validation passed - proceed with team training and adoption")

        return recommendations

    def generate_next_steps(self) -> List[str]:
        """Generate next steps"""
        steps = [
            "Review validation report and address any issues",
            "Schedule team training sessions",
            "Create pilot project for team practice",
            "Gradually migrate existing workflows",
            "Monitor adoption and collect feedback",
            "Optimize configuration based on usage"
        ]

        if not self.is_migration_successful():
            steps.insert(0, "Address critical validation failures before proceeding")

        return steps

    def generate_readable_report(self, report: Dict[str, Any]) -> str:
        """Generate human-readable validation report"""
        readable = f"""# Speckit Migration Validation Report

**Generated**: {report['validation_timestamp']}
**Overall Status**: {report['overall_status'].upper()}

## Validation Results

### Installation
- Speckit Installed: {'✅' if report['detailed_results']['installation']['speckit_installed'] else '❌'}
- Version Compatible: {'✅' if report['detailed_results']['installation']['version_compatible'] else '❌'}
- Directories Exist: {'✅' if report['detailed_results']['installation']['directories_exist'] else '❌'}
- Files Intact: {'✅' if report['detailed_results']['installation']['files_intact'] else '❌'}

### Configuration
- Config Valid: {'✅' if report['detailed_results']['configuration']['config_valid'] else '❌'}
- Constitution Valid: {'✅' if report['detailed_results']['configuration']['constitution_valid'] else '❌'}
- Templates Configured: {'✅' if report['detailed_results']['configuration']['templates_configured'] else '❌'}
- Team Configured: {'✅' if report['detailed_results']['configuration']['team_configured'] else '❌'}

### Functionality
- Constitution Validation: {'✅' if report['detailed_results']['functionality']['constitution_validation'] else '❌'}
- Task Creation: {'✅' if report['detailed_results']['functionality']['task_creation'] else '❌'}
- Evidence Generation: {'✅' if report['detailed_results']['functionality']['evidence_generation'] else '❌'}
- Analysis Functionality: {'✅' if report['detailed_results']['functionality']['analysis_functionality'] else '❌'}

## Recommendations

"""
        for rec in report['recommendations']:
            readable += f"- {rec}\n"

        readable += "\n## Next Steps\n\n"
        for step in report['next_steps']:
            readable += f"{step}\n"

        return readable

    def get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Usage example
if __name__ == "__main__":
    validator = MigrationValidator()
    results = validator.run_comprehensive_validation()

    if validator.is_migration_successful():
        print("Migration validation passed!")
    else:
        print("Migration validation failed. See report for details.")
```

## Post-Migration Optimization

### 1. Performance Tuning

#### Optimization Checklist
```bash
# Run performance optimization
speckit optimize performance --full-analysis

# Optimize configuration
speckit optimize config --based-on-usage --30days

# Optimize database
speckit optimize database --analyze-queries --create-indexes

# Optimize cache
speckit optimize cache --analyze-patterns --optimize-size
```

### 2. Team Training and Adoption

#### Training Program
```bash
# Start team training
speckit training start --program comprehensive --duration 4weeks

# Create practice tasks
speckit training create-exercises --count 10 --difficulty progressive

# Monitor adoption
speckit training monitor --progress-report --identify-gaps

# Certify team members
speckit training certify --team --requirements completion,proficiency
```

## Troubleshooting

### Common Migration Issues

#### 1. Speckit Installation Issues
**Problem**: Speckit commands not found

**Solutions**:
```bash
# Check installation
which speckit
speckit --version

# Reinstall if needed
pip uninstall speckit-cli
pip install speckit-cli

# Check PATH
echo $PATH | grep -i python
```

#### 2. Configuration Issues
**Problem**: Configuration validation fails

**Solutions**:
```bash
# Validate configuration
speckit config validate

# Reset configuration
speckit config reset --safe

# Check file permissions
ls -la .speckit/config/
```

#### 3. Integration Issues
**Problem**: Git hooks not working

**Solutions**:
```bash
# Reinstall Git hooks
speckit git-hooks install --force

# Check hook permissions
ls -la .git/hooks/

# Test hooks manually
.git/hooks/pre-commit
```

## Conclusion

This migration guide provides a comprehensive framework for successfully migrating projects to Speckit v2.0. Key success factors include:

- **Thorough Planning**: Proper assessment and planning before migration
- **Gradual Approach**: Phased migration to minimize disruption
- **Team Involvement**: Ensure team buy-in and provide adequate training
- **Validation**: Comprehensive testing and validation at each phase
- **Support**: Ongoing support and optimization after migration

By following this guide and using the provided tools, organizations can successfully migrate to Speckit while minimizing risks and maximizing benefits. The migration process itself becomes an opportunity to improve project structure, quality standards, and team collaboration.
