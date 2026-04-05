# Speckit Developer Integration Guide

## Overview

This guide provides comprehensive instructions for developers on how to integrate Speckit into their development workflows, IDEs, CI/CD pipelines, and toolchains. Speckit is designed to enhance development productivity while maintaining high-quality standards through evidence-based development practices.

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [IDE Integration](#ide-integration)
3. [Git Workflow Integration](#git-workflow-integration)
4. [CI/CD Pipeline Integration](#cicd-pipeline-integration)
5. [API Integration](#api-integration)
6. [Custom Tool Development](#custom-tool-development)
7. [Testing Integration](#testing-integration)
8. [Monitoring and Reporting](#monitoring-and-reporting)
9. [Advanced Integration Patterns](#advanced-integration-patterns)
10. [Troubleshooting](#troubleshooting)

## Development Environment Setup

### Prerequisites

#### System Requirements
- **Operating System**: Windows 10+, macOS 10.15+, Ubuntu 18.04+
- **PowerShell**: 5.1+ (Windows) or PowerShell Core 6+ (Cross-platform)
- **Python**: 3.8+ (for advanced features)
- **Git**: 2.25+ (for workflow integration)
- **Node.js**: 14+ (for IDE extensions)

#### Required Tools
```bash
# Install PowerShell (if not present)
# Windows: Built-in
# macOS: brew install powershell
# Linux: sudo apt-get install powershell

# Install Python (if not present)
# Windows: Download from python.org
# macOS: brew install python
# Linux: sudo apt-get install python3

# Install required Python packages
pip install speckit-cli speckit-sdk

# Install Git hooks support
npm install -g speckit-git-hooks
```

### Initial Setup

#### 1. Project Initialization
```powershell
# Clone or create your project
git clone <your-repository>
cd <your-project>

# Initialize Speckit in your project
speckit init --project-type <type> --template <template>

# Or manually copy the framework
Copy-Item "C:\_Python\_Projects\.speckit" ".speckit" -Recurse -Force
```

#### 2. Configuration Setup
```powershell
# Create project configuration
.speckit\scripts\powershell\setup-project.ps1 `
  -ProjectName "MyProject" `
  -ProjectType "web-application" `
  -TechStack "python,fastapi,postgresql" `
  -TeamSize 5

# Configure developer preferences
speckit config set developer.name "Your Name"
speckit config set developer.email "your.email@company.com"
speckit config set editor.preferences "vscode"
```

#### 3. Validation
```bash
# Validate setup
speckit doctor

# Run initial constitution validation
speckit constitution --validate

# Test basic workflow
speckit specify "Test feature" --dry-run
```

### Environment Variables

Create a `.env` file in your project root:

```bash
# Speckit Configuration
SPECKIT_HOME=/path/to/.speckit
SPECKIT_CONFIG_PATH=.speckit/config
SPECKIT_CACHE_PATH=.speckit/cache
SPECKIT_LOG_LEVEL=info

# Integration Settings
SPECKIT_CSF_NIP_PATH=/path/to/csf-nip
SPECKIT_KNOWLEDGE_ENABLED=true
SPECKIT_AUTO_SAVE_EVIDENCE=true

# Development Settings
SPECKIT_DEV_MODE=true
SPECKIT_AUTO_BACKUP=true
SPECKIT_NOTIFICATION_LEVEL=warning
```

## IDE Integration

### Visual Studio Code

#### 1. Extension Installation
```bash
# Install Speckit VS Code extension
code --install-extension speckit.speckit-vscode

# Install recommended extensions
code --install-extension ms-vscode.vscode-json
code --install-extension ms-vscode.powershell
code --install-extension ms-python.python
```

#### 2. VS Code Configuration

Create `.vscode/settings.json`:
```json
{
  "speckit.enabled": true,
  "speckit.autoValidate": true,
  "speckit.showTaskStatus": true,
  "speckit.integrationPath": ".speckit",
  "speckit.commands": {
    "validate": "speckit constitution --validate",
    "analyze": "speckit analyze --quick-check",
    "tasks": "speckit tasks --current-feature"
  },
  "speckit.notifications": {
    "validationFailure": true,
    "taskUpdate": true,
    "evidenceGenerated": false
  },
  "files.associations": {
    "*.speckit": "markdown"
  },
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll": true
  }
}
```

Create `.vscode/tasks.json`:
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Speckit: Validate Project",
      "type": "shell",
      "command": "speckit",
      "args": ["constitution", "--validate"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      },
      "problemMatcher": []
    },
    {
      "label": "Speckit: Analyze Current File",
      "type": "shell",
      "command": "speckit",
      "args": ["analyze", "--file", "${file}"],
      "group": "build",
      "presentation": {
        "echo": true,
        "reveal": "always",
        "focus": false,
        "panel": "shared"
      }
    },
    {
      "label": "Speckit: Generate Tasks",
      "type": "shell",
      "command": "speckit",
      "args": ["tasks", "--export-dag", "--current-feature"],
      "group": "build"
    }
  ]
}
```

Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug Speckit Workflow",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/.speckit/scripts/debug_workflow.py",
      "args": ["--feature", "${workspaceFolder}"],
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}"
    }
  ]
}
```

#### 3. VS Code Keybindings

Create `.vscode/keybindings.json`:
```json
[
  {
    "key": "ctrl+shift+s v",
    "command": "speckit.validate",
    "args": ["constitution"]
  },
  {
    "key": "ctrl+shift+s a",
    "command": "speckit.analyze",
    "args": ["--file", "${file}"]
  },
  {
    "key": "ctrl+shift+s t",
    "command": "speckit.tasks",
    "args": ["--current-feature"]
  },
  {
    "key": "ctrl+shift+s e",
    "command": "speckit.execute",
    "args": ["--feature-dir", "${workspaceFolder}"]
  }
]
```

### JetBrains IDEs (IntelliJ, PyCharm, WebStorm)

#### 1. Plugin Installation
- Install the Speckit plugin from the JetBrains Marketplace
- Restart your IDE

#### 2. Configuration

**IDE Settings** → **Tools** → **Speckit**:
```
Speckit Home: /path/to/.speckit
Auto-validate on save: true
Show task status in status bar: true
Integration with Git: enabled
```

#### 3. External Tools Configuration

**Settings** → **Tools** → **External Tools**:

**Speckit Validate**:
- Name: `Speckit Validate`
- Program: `speckit`
- Arguments: `constitution --validate`
- Working directory: `$ProjectFileDir$`

**Speckit Analyze File**:
- Name: `Speckit Analyze File`
- Program: `speckit`
- Arguments: `analyze --file $FilePath$`
- Working directory: `$ProjectFileDir$`

### Vim/Neovim

#### 1. Plugin Setup

Using vim-plug:
```vim
" .vimrc
Plug 'speckit/speckit-vim'

" Configure Speckit
let g:speckit_auto_validate = 1
let g:speckit_integration_path = '.speckit'
let g:speckit_show_task_status = 1
```

#### 2. Key Mappings
```vim
" Speckit commands
nnoremap <leader>sv :SpeckitValidate<CR>
nnoremap <leader>sa :SpeckitAnalyze<CR>
nnoremap <leader>st :SpeckitTasks<CR>
nnoremap <leader>se :SpeckitExecute<CR>
```

### Emacs

#### 1. Package Setup

```elisp
;; init.el
(use-package speckit
  :ensure t
  :config
  (setq speckit-auto-validate t)
  (setq speckit-integration-path ".speckit")
  (global-speckit-mode 1))

;; Key bindings
(global-set-key (kbd "C-c s v") 'speckit-validate)
(global-set-key (kbd "C-c s a") 'speckit-analyze)
(global-set-key (kbd "C-c s t") 'speckit-tasks)
(global-set-key (kbd "C-c s e") 'speckit-execute)
```

## Git Workflow Integration

### Git Hooks Setup

#### 1. Automatic Hook Installation
```bash
# Install Git hooks
speckit git-hooks install

# Or manually install
speckit git-hooks install --hooks pre-commit,pre-push,commit-msg
```

#### 2. Pre-commit Hook
```bash
#!/bin/sh
# .git/hooks/pre-commit

echo "Running Speckit pre-commit validation..."

# Run quick validation
speckit analyze --quick-check --no-output
if [ $? -ne 0 ]; then
  echo "❌ Speckit validation failed"
  echo "Run 'speckit analyze' for details"
  exit 1
fi

# Check for required evidence files
speckit evidence check --required
if [ $? -ne 0 ]; then
  echo "❌ Missing required evidence files"
  exit 1
fi

echo "✅ Speckit validation passed"
```

#### 3. Pre-push Hook
```bash
#!/bin/sh
# .git/hooks/pre-push

echo "Running Speckit pre-push validation..."

# Comprehensive validation
speckit constitution --validate
if [ $? -ne 0 ]; then
  echo "❌ Constitution validation failed"
  exit 1
fi

# Generate push evidence
speckit evidence generate --type push --output .speckit/evidence/push_$(date +%Y%m%d_%H%M%S).json

echo "✅ Pre-push validation completed"
```

#### 4. Commit-msg Hook
```bash
#!/bin/sh
# .git/hooks/commit-msg

COMMIT_MSG_FILE=$1

# Validate commit message format
speckit git validate-commit-msg --file $COMMIT_MSG_FILE
if [ $? -ne 0 ]; then
  echo "❌ Commit message validation failed"
  echo "Format: <type>(<scope>): <description>"
  echo "Example: feat(auth): add OAuth2 authentication"
  exit 1
fi

# Check for task reference
if ! grep -q "TSK-[0-9]\{3\}" $COMMIT_MSG_FILE; then
  echo "⚠️  Warning: No task reference found in commit message"
  echo "Consider adding task reference (e.g., TSK-001)"
fi
```

### Git Branch Strategy Integration

#### 1. Feature Branch Creation
```bash
# Create feature branch with task ID
speckit git create-feature-branch --task-id TSK-001 --branch-name feature/user-auth

# Output: Creates branch "feature/TSK-001-user-auth"
```

#### 2. Branch Validation
```bash
# Validate branch before merge
speckit git validate-branch --branch feature/TSK-001-user-auth

# Check branch completeness
speckit git branch-status --require-evidence --require-tests
```

### Git Integration Script

Create `.speckit/scripts/git-integration.sh`:
```bash
#!/bin/bash
# Git integration helper script

COMMAND=$1
BRANCH_NAME=$2

case $COMMAND in
  "create-feature")
    if [ -z "$BRANCH_NAME" ]; then
      echo "Usage: $0 create-feature <branch-name>"
      exit 1
    fi

    # Get current task ID
    TASK_ID=$(speckit tasks current --format id)
    if [ -z "$TASK_ID" ]; then
      echo "No active task found"
      exit 1
    fi

    # Create feature branch
    FEATURE_BRANCH="feature/$TASK_ID-$BRANCH_NAME"
    git checkout -b $FEATURE_BRANCH

    # Update task with branch info
    speckit tasks update --task-id $TASK_ID --branch $FEATURE_BRANCH

    echo "Created feature branch: $FEATURE_BRANCH"
    ;;

  "validate-branch")
    CURRENT_BRANCH=$(git branch --show-current)

    # Check if task is linked
    TASK_ID=$(echo $CURRENT_BRANCH | grep -o "TSK-[0-9]\{3\}")
    if [ -z "$TASK_ID" ]; then
      echo "No task ID found in branch name"
      exit 1
    fi

    # Validate task completeness
    speckit tasks validate --task-id $TASK_ID --branch-validation

    echo "Branch validation completed for $CURRENT_BRANCH"
    ;;

  *)
    echo "Usage: $0 {create-feature|validate-branch} [args]"
    exit 1
    ;;
esac
```

## CI/CD Pipeline Integration

### GitHub Actions

#### 1. Speckit Validation Workflow

Create `.github/workflows/speckit-validate.yml`:
```yaml
name: Speckit Validation

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  speckit-validation:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3
      with:
        fetch-depth: 0

    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Setup Speckit
      run: |
        pip install speckit-cli
        speckit --version

    - name: Validate Constitution
      run: |
        speckit constitution --validate --output-format json > speckit-constitution.json

    - name: Analyze Project
      run: |
        speckit analyze --write-report --metrics --output-format json > speckit-analysis.json

    - name: Validate Tasks
      run: |
        speckit tasks validate --require-evidence --check-dependencies

    - name: Generate Evidence Summary
      run: |
        speckit evidence summary --output speckit-evidence-summary.json

    - name: Upload Speckit Reports
      uses: actions/upload-artifact@v3
      with:
        name: speckit-reports
        path: |
          speckit-*.json
          .speckit/evidence/
```

#### 2. Quality Gate Workflow

Create `.github/workflows/speckit-quality-gate.yml`:
```yaml
name: Speckit Quality Gate

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  quality-gate:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3
      with:
        fetch-depth: 0

    - name: Setup Speckit
      run: |
        pip install speckit-cli
        speckit init --ci-mode

    - name: Run Quality Checks
      run: |
        speckit quality-gate --threshold 0.75 --strict

    - name: Check Task Completeness
      run: |
        # Extract task ID from branch name
        TASK_ID=$(echo $GITHUB_HEAD_REF | grep -o "TSK-[0-9]\{3\}")
        if [ ! -z "$TASK_ID" ]; then
          speckit tasks validate --task-id $TASK_ID --completeness-check
        fi

    - name: Generate PR Comment
      if: always()
      uses: actions/github-script@v6
      with:
        script: |
          const fs = require('fs');

          // Read Speckit reports
          const constitutionReport = JSON.parse(fs.readFileSync('speckit-constitution.json', 'utf8'));
          const analysisReport = JSON.parse(fs.readFileSync('speckit-analysis.json', 'utf8'));

          // Generate comment
          const comment = `
          ## Speckit Validation Report

          ### Constitution Validation
          - Status: ${constitutionReport.valid ? '✅ Passed' : '❌ Failed'}
          - Score: ${constitutionReport.score}
          - Issues: ${constitutionReport.issues.length}

          ### Project Analysis
          - Trust Score: ${analysisReport.trust_score}
          - Coverage: ${analysisReport.test_coverage}
          - Quality Metrics: ${analysisReport.quality_score}

          ${constitutionReport.valid ? '✅ Ready for merge' : '❌ Address issues before merge'}
          `;

          github.rest.issues.createComment({
            issue_number: context.issue.number,
            owner: context.repo.owner,
            repo: context.repo.repo,
            body: comment
          });
```

### GitLab CI/CD

Create `.gitlab-ci.yml`:
```yaml
# GitLab CI/CD configuration for Speckit

stages:
  - validate
  - test
  - quality-gate

variables:
  SPECKIT_VERSION: "2.0.0"
  SPECKIT_CACHE_DIR: "$CI_PROJECT_DIR/.speckit/cache"

speckit-validate:
  stage: validate
  image: python:3.9
  cache:
    paths:
      - .speckit/cache/
  script:
    - pip install speckit-cli==$SPECKIT_VERSION
    - speckit constitution --validate --output-format json > speckit-constitution.json
    - speckit analyze --write-report --metrics
  artifacts:
    reports:
      junit: speckit-reports.xml
    paths:
      - speckit-*.json
      - .speckit/evidence/
    expire_in: 1 week

speckit-quality-gate:
  stage: quality-gate
  image: python:3.9
  dependencies:
    - speckit-validate
  script:
    - pip install speckit-cli==$SPECKIT_VERSION
    - speckit quality-gate --threshold 0.75 --strict
    - speckit evidence summary --format markdown > quality-report.md
  artifacts:
    paths:
      - quality-report.md
    expire_in: 1 month
  only:
    - merge_requests
```

### Azure DevOps

Create `azure-pipelines.yml`:
```yaml
# Azure DevOps Pipeline for Speckit

trigger:
  branches:
    include:
      - main
      - develop

pr:
  branches:
    include:
      - main

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.9'
  displayName: 'Setup Python'

- script: |
    pip install speckit-cli
  displayName: 'Install Speckit'

- script: |
    speckit constitution --validate --output-format json > $(Build.ArtifactStagingDirectory)/speckit-constitution.json
    speckit analyze --write-report --metrics --output-dir $(Build.ArtifactStagingDirectory)
  displayName: 'Run Speckit Validation'

- script: |
    speckit quality-gate --threshold 0.75
  displayName: 'Quality Gate Check'
  condition: and(succeeded(), eq(variables['Build.Reason'], 'PullRequest'))

- task: PublishBuildArtifacts@1
  inputs:
    pathToPublish: '$(Build.ArtifactStagingDirectory)'
    artifactName: 'speckit-reports'
  displayName: 'Publish Speckit Reports'
```

## API Integration

### Speckit REST API

#### 1. API Server Setup
```bash
# Start Speckit API server
speckit api start --port 8080 --host 0.0.0.0

# Or run as background service
speckit api start --daemon --config .speckit/api-config.json
```

#### 2. API Configuration

Create `.speckit/api-config.json`:
```json
{
  "server": {
    "host": "localhost",
    "port": 8080,
    "cors_enabled": true,
    "auth_required": false
  },
  "endpoints": {
    "constitution": "/api/v1/constitution",
    "tasks": "/api/v1/tasks",
    "evidence": "/api/v1/evidence",
    "analysis": "/api/v1/analysis"
  },
  "security": {
    "rate_limiting": {
      "enabled": true,
      "requests_per_minute": 60
    },
    "api_keys": {
      "enabled": false
    }
  }
}
```

#### 3. API Client Libraries

**Python Client**:
```python
# speckit_client.py
import requests
import json

class SpeckitClient:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.session = requests.Session()

    def validate_constitution(self):
        """Validate project constitution"""
        response = self.session.get(f"{self.base_url}/api/v1/constitution/validate")
        return response.json()

    def get_tasks(self, status=None):
        """Get tasks with optional status filter"""
        params = {"status": status} if status else {}
        response = self.session.get(f"{self.base_url}/api/v1/tasks", params=params)
        return response.json()

    def create_task(self, task_data):
        """Create a new task"""
        response = self.session.post(f"{self.base_url}/api/v1/tasks", json=task_data)
        return response.json()

    def update_task(self, task_id, updates):
        """Update existing task"""
        response = self.session.put(f"{self.base_url}/api/v1/tasks/{task_id}", json=updates)
        return response.json()

    def analyze_project(self, options=None):
        """Analyze project"""
        params = options or {}
        response = self.session.post(f"{self.base_url}/api/v1/analysis", json=params)
        return response.json()

    def get_evidence(self, task_id=None):
        """Get evidence files"""
        params = {"task_id": task_id} if task_id else {}
        response = self.session.get(f"{self.base_url}/api/v1/evidence", params=params)
        return response.json()

# Usage example
client = SpeckitClient()

# Validate constitution
result = client.validate_constitution()
print(f"Constitution valid: {result['valid']}")

# Get active tasks
tasks = client.get_tasks(status="active")
for task in tasks:
    print(f"Task {task['task_id']}: {task['title']}")
```

**JavaScript Client**:
```javascript
// speckit-client.js
class SpeckitClient {
    constructor(baseUrl = 'http://localhost:8080') {
        this.baseUrl = baseUrl;
    }

    async validateConstitution() {
        const response = await fetch(`${this.baseUrl}/api/v1/constitution/validate`);
        return await response.json();
    }

    async getTasks(status = null) {
        const url = new URL(`${this.baseUrl}/api/v1/tasks`);
        if (status) {
            url.searchParams.append('status', status);
        }
        const response = await fetch(url);
        return await response.json();
    }

    async createTask(taskData) {
        const response = await fetch(`${this.baseUrl}/api/v1/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(taskData)
        });
        return await response.json();
    }

    async analyzeProject(options = {}) {
        const response = await fetch(`${this.baseUrl}/api/v1/analysis`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(options)
        });
        return await response.json();
    }
}

// Usage example
const client = new SpeckitClient();

// Validate constitution
client.validateConstitution().then(result => {
    console.log(`Constitution valid: ${result.valid}`);
});

// Get active tasks
client.getTasks('active').then(tasks => {
    tasks.forEach(task => {
        console.log(`Task ${task.task_id}: ${task.title}`);
    });
});
```

### Webhook Integration

#### 1. Webhook Configuration

Create `.speckit/webhooks.json`:
```json
{
  "webhooks": [
    {
      "name": "task-updated",
      "events": ["task.created", "task.updated", "task.completed"],
      "url": "https://your-api.example.com/webhooks/speckit",
      "secret": "your-webhook-secret",
      "enabled": true
    },
    {
      "name": "validation-failed",
      "events": ["constitution.validation_failed", "quality_gate.failed"],
      "url": "https://your-slack.example.com/webhooks",
      "enabled": true
    }
  ]
}
```

#### 2. Webhook Event Handler

Create `.speckit/scripts/webhook-handler.py`:
```python
#!/usr/bin/env python3
# Webhook event handler for Speckit

from flask import Flask, request, jsonify
import hmac
import hashlib
import json
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_webhook_signature(payload, signature, secret):
    """Verify webhook signature"""
    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)

@app.route('/webhooks/speckit', methods=['POST'])
def handle_speckit_webhook():
    """Handle Speckit webhook events"""
    signature = request.headers.get('X-Speckit-Signature')
    secret = 'your-webhook-secret'

    if not verify_webhook_signature(request.data, signature, secret):
        return jsonify({'error': 'Invalid signature'}), 401

    event = request.json
    event_type = event.get('event_type')
    event_data = event.get('data')

    logger.info(f"Received event: {event_type}")

    # Handle different event types
    if event_type == 'task.created':
        handle_task_created(event_data)
    elif event_type == 'task.completed':
        handle_task_completed(event_data)
    elif event_type == 'validation_failed':
        handle_validation_failed(event_data)

    return jsonify({'status': 'ok'}), 200

def handle_task_created(task_data):
    """Handle task creation event"""
    task_id = task_data.get('task_id')
    title = task_data.get('title')
    assignee = task_data.get('assigned_to')

    logger.info(f"Task created: {task_id} - {title}")

    # Send notification, update external systems, etc.
    # send_notification(f"New task assigned: {title}", assignee)
    # update_project_management_tool(task_data)

def handle_task_completed(task_data):
    """Handle task completion event"""
    task_id = task_data.get('task_id')
    trust_score = task_data.get('trust_score')

    logger.info(f"Task completed: {task_id} (trust: {trust_score})")

    # Update metrics, notify stakeholders, etc.
    # update_completion_metrics(task_data)
    # send_completion_notification(task_data)

def handle_validation_failed(validation_data):
    """Handle validation failure event"""
    validation_type = validation_data.get('validation_type')
    issues = validation_data.get('issues', [])

    logger.warning(f"Validation failed: {validation_type}")

    # Alert team, create remediation tasks, etc.
    # send_alert(f"Validation failed: {validation_type}", issues)
    # create_remediation_tasks(validation_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

## Custom Tool Development

### Speckit SDK

#### 1. Python SDK

```python
# custom_speckit_tool.py
from speckit import SpeckitSDK, Task, Evidence, ValidationResult

class CustomAnalysisTool:
    def __init__(self, speckit_path=".speckit"):
        self.sdk = SpeckitSDK(speckit_path)

    def analyze_code_quality(self, file_path):
        """Custom code quality analysis"""
        # Your custom analysis logic
        quality_score = self.calculate_quality_score(file_path)
        issues = self.detect_issues(file_path)

        # Create evidence
        evidence = Evidence(
            evidence_type="custom_quality_analysis",
            file_path=file_path,
            data={
                "quality_score": quality_score,
                "issues": issues,
                "timestamp": datetime.now().isoformat()
            }
        )

        # Save evidence
        self.sdk.save_evidence(evidence)

        return ValidationResult(
            valid=quality_score > 0.8,
            score=quality_score,
            issues=issues
        )

    def calculate_quality_score(self, file_path):
        """Custom quality score calculation"""
        # Implement your quality metrics
        # Complexity, maintainability, test coverage, etc.
        pass

    def detect_issues(self, file_path):
        """Custom issue detection"""
        # Implement your issue detection logic
        # Security vulnerabilities, performance issues, etc.
        pass

# Usage
tool = CustomAnalysisTool()
result = tool.analyze_code_quality("src/main.py")
print(f"Quality score: {result.score}")
```

#### 2. Custom Command Development

Create `.speckit/scripts/custom-commands/security-scan.py`:
```python
#!/usr/bin/env python3
"""
Custom Speckit command for security scanning
"""

import argparse
import json
import sys
from pathlib import Path

# Add Speckit SDK to path
sys.path.append(str(Path(__file__).parent.parent.parent / "lib"))

from speckit import SpeckitCommand, Evidence, Task

class SecurityScanCommand(SpeckitCommand):
    def __init__(self):
        super().__init__()
        self.name = "security-scan"
        self.description = "Perform security vulnerability scan"

    def add_arguments(self, parser):
        parser.add_argument(
            "--target",
            required=True,
            help="Target directory or file to scan"
        )
        parser.add_argument(
            "--severity",
            choices=["low", "medium", "high", "critical"],
            default="medium",
            help="Minimum severity level to report"
        )
        parser.add_argument(
            "--output",
            help="Output file for scan results"
        )

    def execute(self, args):
        """Execute security scan"""
        print(f"Starting security scan on: {args.target}")

        # Perform security scan
        scan_results = self.perform_security_scan(args.target, args.severity)

        # Create evidence
        evidence = Evidence(
            evidence_type="security_scan",
            target=args.target,
            data=scan_results
        )

        # Save evidence
        self.save_evidence(evidence)

        # Generate report
        report = self.generate_report(scan_results)

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Report saved to: {args.output}")
        else:
            print(json.dumps(report, indent=2))

        # Update current task if available
        current_task = self.get_current_task()
        if current_task:
            self.add_evidence_to_task(current_task.task_id, evidence)

        return scan_results.get('critical_issues', 0) == 0

    def perform_security_scan(self, target, severity):
        """Perform actual security scan"""
        # Integrate with security tools
        # Example: bandit, semgrep, safety, etc.

        results = {
            "scan_time": datetime.now().isoformat(),
            "target": target,
            "severity_filter": severity,
            "issues": [],
            "summary": {}
        }

        # Run bandit for Python security issues
        if target.endswith('.py'):
            bandit_results = self.run_bandit(target)
            results["issues"].extend(bandit_results)

        # Run additional security tools
        # semgrep_results = self.run_semgrep(target)
        # results["issues"].extend(semgrep_results)

        # Filter by severity
        results["issues"] = [
            issue for issue in results["issues"]
            if self.severity_level(issue["severity"]) >= self.severity_level(severity)
        ]

        # Generate summary
        results["summary"] = {
            "total_issues": len(results["issues"]),
            "critical_issues": len([i for i in results["issues"] if i["severity"] == "critical"]),
            "high_issues": len([i for i in results["issues"] if i["severity"] == "high"]),
            "medium_issues": len([i for i in results["issues"] if i["severity"] == "medium"]),
            "low_issues": len([i for i in results["issues"] if i["severity"] == "low"])
        }

        return results

    def run_bandit(self, target):
        """Run bandit security scanner"""
        import subprocess
        import json

        try:
            result = subprocess.run(
                ["bandit", "-f", "json", target],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                bandit_data = json.loads(result.stdout)
                return [
                    {
                        "tool": "bandit",
                        "severity": issue.get("issue_severity", "medium").lower(),
                        "confidence": issue.get("issue_certainty", "medium").lower(),
                        "rule_id": issue.get("test_id"),
                        "message": issue.get("issue_text"),
                        "file": issue.get("filename"),
                        "line": issue.get("line_number")
                    }
                    for issue in bandit_data.get("results", [])
                ]
        except Exception as e:
            print(f"Error running bandit: {e}")

        return []

    def severity_level(self, severity):
        """Convert severity string to numeric level"""
        levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        return levels.get(severity.lower(), 0)

    def generate_report(self, scan_results):
        """Generate security scan report"""
        return {
            "security_scan_report": scan_results,
            "recommendations": self.generate_recommendations(scan_results),
            "next_steps": self.generate_next_steps(scan_results)
        }

    def generate_recommendations(self, scan_results):
        """Generate security recommendations"""
        recommendations = []

        critical_count = scan_results["summary"]["critical_issues"]
        high_count = scan_results["summary"]["high_issues"]

        if critical_count > 0:
            recommendations.append(f"Address {critical_count} critical security issues immediately")

        if high_count > 0:
            recommendations.append(f"Plan remediation for {high_count} high-severity issues")

        if len(recommendations) == 0:
            recommendations.append("No critical security issues found - continue monitoring")

        return recommendations

    def generate_next_steps(self, scan_results):
        """Generate next steps"""
        steps = [
            "Review all identified security issues",
            "Create tasks for high-priority remediation",
            "Update security training based on findings",
            "Schedule regular security scans"
        ]

        return steps

if __name__ == "__main__":
    command = SecurityScanCommand()
    exit_code = command.run()
    sys.exit(exit_code)
```

#### 3. Command Registration

Register custom command in `.speckit/config/commands.json`:
```json
{
  "custom_commands": [
    {
      "name": "security-scan",
      "script": "scripts/custom-commands/security-scan.py",
      "description": "Perform security vulnerability scan",
      "category": "security",
      "enabled": true
    },
    {
      "name": "performance-test",
      "script": "scripts/custom-commands/performance-test.py",
      "description": "Run performance tests",
      "category": "performance",
      "enabled": true
    }
  ]
}
```

## Testing Integration

### Automated Testing with Speckit

#### 1. Test Framework Integration

Create `.speckit/scripts/test-integration.py`:
```python
#!/usr/bin/env python3
"""
Integration with testing frameworks
"""

import pytest
import json
import subprocess
from pathlib import Path

class SpeckitTestPlugin:
    """Pytest plugin for Speckit integration"""

    def pytest_configure(self, config):
        """Configure pytest with Speckit settings"""
        self.speckit_config = self.load_speckit_config()
        self.test_evidence = []

    def pytest_runtest_setup(self, item):
        """Setup before each test"""
        # Record test setup evidence
        setup_evidence = {
            "test_name": item.name,
            "setup_time": datetime.now().isoformat(),
            "speckit_context": self.get_speckit_context()
        }
        self.test_evidence.append(setup_evidence)

    def pytest_runtest_teardown(self, item):
        """Teardown after each test"""
        # Record test completion evidence
        teardown_evidence = {
            "test_name": item.name,
            "teardown_time": datetime.now().isoformat(),
            "outcome": "passed" if item.rep_call.passed else "failed"
        }
        self.test_evidence.append(teardown_evidence)

    def pytest_sessionfinish(self, session):
        """Save test evidence after session"""
        self.save_test_evidence(session)

    def load_speckit_config(self):
        """Load Speckit configuration"""
        config_path = Path(".speckit/config/speckit_config.json")
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {}

    def get_speckit_context(self):
        """Get current Speckit context"""
        current_task = self.get_current_task()
        return {
            "current_task": current_task.task_id if current_task else None,
            "project_phase": self.get_project_phase(),
            "evidence_directory": ".speckit/evidence"
        }

    def get_current_task(self):
        """Get current active task"""
        # Logic to get current task from Speckit
        pass

    def get_project_phase(self):
        """Get current project phase"""
        # Logic to determine project phase
        return "testing"

    def save_test_evidence(self, session):
        """Save test evidence to Speckit"""
        evidence_file = ".speckit/evidence/test_session_{}.json".format(
            datetime.now().strftime("%Y%m%d_%H%M%S")
        )

        evidence_data = {
            "session_id": session.nodeid,
            "start_time": session.starttime.isoformat(),
            "end_time": datetime.now().isoformat(),
            "total_tests": len(session.items),
            "passed_tests": len([item for item in session.items if item.rep_call.passed]),
            "failed_tests": len([item for item in session.items if not item.rep_call.passed]),
            "test_evidence": self.test_evidence
        }

        with open(evidence_file, 'w') as f:
            json.dump(evidence_data, f, indent=2)

        print(f"Test evidence saved to: {evidence_file}")

def pytest_configure(config):
    """Register Speckit plugin"""
    config.pluginmanager.register(SpeckitTestPlugin())
```

#### 2. Test Configuration

Create `pytest.ini`:
```ini
[tool:pytest]
addopts =
    --speckit-integration
    --evidence-dir=.speckit/evidence
    --speckit-task-link
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

#### 3. Test Evidence Collection

```python
# test_feature.py
import pytest
from speckit import Evidence, SpeckitSDK

class TestUserAuthentication:
    def setup_method(self):
        """Setup before each test method"""
        self.speckit = SpeckitSDK()
        self.test_evidence = []

    def test_user_login_success(self):
        """Test successful user login"""
        # Record test start evidence
        evidence = Evidence(
            evidence_type="test_execution",
            test_name="test_user_login_success",
            phase="setup"
        )
        self.test_evidence.append(evidence)

        # Test implementation
        result = self.perform_login("test@example.com", "password123")
        assert result.success is True
        assert result.user_id is not None

        # Record test completion evidence
        completion_evidence = Evidence(
            evidence_type="test_execution",
            test_name="test_user_login_success",
            phase="completion",
            data={
                "result": "passed",
                "assertions": 2,
                "execution_time": 0.15
            }
        )
        self.test_evidence.append(completion_evidence)

        # Save evidence to Speckit
        for evidence in self.test_evidence:
            self.speckit.save_evidence(evidence)

    def teardown_method(self):
        """Teardown after each test method"""
        # Generate test summary evidence
        summary = Evidence(
            evidence_type="test_summary",
            test_class="TestUserAuthentication",
            data={
                "total_evidence_items": len(self.test_evidence),
                "test_completion_time": datetime.now().isoformat()
            }
        )
        self.speckit.save_evidence(summary)
```

## Monitoring and Reporting

### Speckit Dashboard

#### 1. Dashboard Setup

Create `.speckit/dashboard/dashboard.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Speckit Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .dashboard {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #3498db;
        }
        .metric-label {
            color: #7f8c8d;
            margin-top: 5px;
        }
        .charts-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        .chart-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .task-list {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .task-item {
            padding: 10px;
            border-bottom: 1px solid #ecf0f1;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .task-status {
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
        }
        .status-active { background-color: #f39c12; color: white; }
        .status-completed { background-color: #27ae60; color: white; }
        .status-blocked { background-color: #e74c3c; color: white; }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>Speckit Project Dashboard</h1>
            <p>Real-time project metrics and task status</p>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-value" id="trust-score">0.85</div>
                <div class="metric-label">Trust Score</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="active-tasks">12</div>
                <div class="metric-label">Active Tasks</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="completion-rate">78%</div>
                <div class="metric-label">Completion Rate</div>
            </div>
            <div class="metric-card">
                <div class="metric-value" id="evidence-count">245</div>
                <div class="metric-label">Evidence Files</div>
            </div>
        </div>

        <div class="charts-container">
            <div class="chart-card">
                <h3>Task Progress Trend</h3>
                <canvas id="progress-chart"></canvas>
            </div>
            <div class="chart-card">
                <h3>Quality Metrics</h3>
                <canvas id="quality-chart"></canvas>
            </div>
        </div>

        <div class="task-list">
            <h3>Recent Tasks</h3>
            <div id="task-container">
                <!-- Tasks will be populated here -->
            </div>
        </div>
    </div>

    <script>
        // Initialize dashboard
        class SpeckitDashboard {
            constructor() {
                this.apiBase = 'http://localhost:8080/api/v1';
                this.init();
            }

            async init() {
                await this.loadMetrics();
                await this.loadTasks();
                this.initCharts();
                this.startAutoRefresh();
            }

            async loadMetrics() {
                try {
                    const response = await axios.get(`${this.apiBase}/metrics`);
                    const metrics = response.data;

                    document.getElementById('trust-score').textContent = metrics.trust_score.toFixed(2);
                    document.getElementById('active-tasks').textContent = metrics.active_tasks;
                    document.getElementById('completion-rate').textContent = `${metrics.completion_rate}%`;
                    document.getElementById('evidence-count').textContent = metrics.evidence_count;
                } catch (error) {
                    console.error('Error loading metrics:', error);
                }
            }

            async loadTasks() {
                try {
                    const response = await axios.get(`${this.apiBase}/tasks?limit=10`);
                    const tasks = response.data;

                    const container = document.getElementById('task-container');
                    container.innerHTML = '';

                    tasks.forEach(task => {
                        const taskElement = this.createTaskElement(task);
                        container.appendChild(taskElement);
                    });
                } catch (error) {
                    console.error('Error loading tasks:', error);
                }
            }

            createTaskElement(task) {
                const div = document.createElement('div');
                div.className = 'task-item';

                const statusClass = `status-${task.status}`;
                const priority = task.priority ? ` (${task.priority})` : '';

                div.innerHTML = `
                    <div>
                        <strong>${task.task_id}</strong>: ${task.title}${priority}
                    </div>
                    <div class="task-status ${statusClass}">${task.status}</div>
                `;

                return div;
            }

            initCharts() {
                // Progress trend chart
                const progressCtx = document.getElementById('progress-chart').getContext('2d');
                new Chart(progressCtx, {
                    type: 'line',
                    data: {
                        labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
                        datasets: [{
                            label: 'Tasks Completed',
                            data: [3, 5, 4, 7, 6],
                            borderColor: '#3498db',
                            backgroundColor: 'rgba(52, 152, 219, 0.1)',
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });

                // Quality metrics chart
                const qualityCtx = document.getElementById('quality-chart').getContext('2d');
                new Chart(qualityCtx, {
                    type: 'radar',
                    data: {
                        labels: ['Security', 'Performance', 'Maintainability', 'Test Coverage', 'Documentation'],
                        datasets: [{
                            label: 'Current',
                            data: [85, 78, 92, 88, 75],
                            borderColor: '#27ae60',
                            backgroundColor: 'rgba(39, 174, 96, 0.2)'
                        }, {
                            label: 'Target',
                            data: [90, 85, 90, 90, 80],
                            borderColor: '#e74c3c',
                            backgroundColor: 'rgba(231, 76, 60, 0.1)'
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            r: {
                                beginAtZero: true,
                                max: 100
                            }
                        }
                    }
                });
            }

            startAutoRefresh() {
                // Refresh every 30 seconds
                setInterval(() => {
                    this.loadMetrics();
                    this.loadTasks();
                }, 30000);
            }
        }

        // Initialize dashboard when page loads
        document.addEventListener('DOMContentLoaded', () => {
            new SpeckitDashboard();
        });
    </script>
</body>
</html>
```

#### 2. Dashboard Server

Create `.speckit/scripts/dashboard-server.py`:
```python
#!/usr/bin/env python3
"""
Speckit dashboard server
"""

from flask import Flask, send_from_directory, jsonify
import json
import os
from pathlib import Path

app = Flask(__name__)

@app.route('/')
def dashboard():
    """Serve dashboard"""
    return send_from_directory('.speckit/dashboard', 'dashboard.html')

@app.route('/api/v1/metrics')
def get_metrics():
    """Get project metrics"""
    # Load evidence and calculate metrics
    evidence_dir = Path('.speckit/evidence')

    # Calculate metrics from evidence files
    trust_score = calculate_trust_score(evidence_dir)
    active_tasks = count_active_tasks()
    completion_rate = calculate_completion_rate()
    evidence_count = len(list(evidence_dir.glob('**/*.json')))

    return jsonify({
        'trust_score': trust_score,
        'active_tasks': active_tasks,
        'completion_rate': completion_rate,
        'evidence_count': evidence_count
    })

@app.route('/api/v1/tasks')
def get_tasks():
    """Get tasks"""
    limit = request.args.get('limit', 10, type=int)
    status = request.args.get('status')

    # Load tasks from cache
    tasks_file = '.speckit/cache/active_tasks.json'
    if os.path.exists(tasks_file):
        with open(tasks_file) as f:
            tasks = json.load(f)

        # Filter by status if provided
        if status:
            tasks = [t for t in tasks if t.get('status') == status]

        # Limit results
        tasks = tasks[:limit]

        return jsonify(tasks)

    return jsonify([])

def calculate_trust_score(evidence_dir):
    """Calculate trust score from evidence"""
    # Implementation to calculate trust score
    return 0.85

def count_active_tasks():
    """Count active tasks"""
    tasks_file = '.speckit/cache/active_tasks.json'
    if os.path.exists(tasks_file):
        with open(tasks_file) as f:
            tasks = json.load(f)
        return len([t for t in tasks if t.get('status') == 'active'])
    return 0

def calculate_completion_rate():
    """Calculate task completion rate"""
    # Implementation to calculate completion rate
    return 78

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
```

## Advanced Integration Patterns

### 1. Event-Driven Architecture

Create `.speckit/scripts/event-bus.py`:
```python
#!/usr/bin/env python3
"""
Event bus for Speckit integration
"""

import asyncio
import json
from typing import Dict, List, Callable
from dataclasses import dataclass
from datetime import datetime

@dataclass
class SpeckitEvent:
    event_type: str
    data: dict
    timestamp: datetime
    source: str
    task_id: str = None

class SpeckitEventBus:
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = {}
        self.event_history: List[SpeckitEvent] = []

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def publish(self, event: SpeckitEvent):
        """Publish event"""
        self.event_history.append(event)

        # Notify subscribers
        if event.event_type in self.subscribers:
            for callback in self.subscribers[event.event_type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"Error in event callback: {e}")

    def get_events(self, event_type: str = None, limit: int = 100):
        """Get events from history"""
        events = self.event_history
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]

# Global event bus instance
event_bus = SpeckitEventBus()

# Event handlers
def handle_task_created(event: SpeckitEvent):
    """Handle task creation event"""
    print(f"Task created: {event.data.get('task_id')}")
    # Send notifications, update dashboards, etc.

def handle_evidence_generated(event: SpeckitEvent):
    """Handle evidence generation event"""
    print(f"Evidence generated: {event.data.get('evidence_type')}")
    # Update metrics, trigger validations, etc.

def handle_validation_failed(event: SpeckitEvent):
    """Handle validation failure event"""
    print(f"Validation failed: {event.data.get('validation_type')}")
    # Send alerts, create remediation tasks, etc.

# Subscribe to events
event_bus.subscribe('task.created', handle_task_created)
event_bus.subscribe('evidence.generated', handle_evidence_generated)
event_bus.subscribe('validation.failed', handle_validation_failed)
```

### 2. Plugin System

Create `.speckit/plugins/plugin_manager.py`:
```python
#!/usr/bin/env python3
"""
Plugin system for Speckit extensions
"""

import importlib
import inspect
from typing import Dict, List, Type
from pathlib import Path

class SpeckitPlugin:
    """Base class for Speckit plugins"""

    def __init__(self):
        self.name = self.__class__.__name__
        self.version = "1.0.0"
        self.description = ""
        self.dependencies = []

    def initialize(self, speckit_instance):
        """Initialize plugin"""
        pass

    def execute(self, command, args):
        """Execute plugin command"""
        pass

    def cleanup(self):
        """Cleanup plugin resources"""
        pass

class PluginManager:
    def __init__(self, speckit_instance):
        self.speckit = speckit_instance
        self.plugins: Dict[str, SpeckitPlugin] = {}
        self.commands: Dict[str, SpeckitPlugin] = {}

    def load_plugins(self, plugin_dir: str = ".speckit/plugins"):
        """Load all plugins from directory"""
        plugin_path = Path(plugin_dir)
        if not plugin_path.exists():
            return

        for plugin_file in plugin_path.glob("*_plugin.py"):
            try:
                self.load_plugin(plugin_file)
            except Exception as e:
                print(f"Error loading plugin {plugin_file}: {e}")

    def load_plugin(self, plugin_file: Path):
        """Load single plugin"""
        spec = importlib.util.spec_from_file_location(
            plugin_file.stem, plugin_file
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find plugin classes
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and
                issubclass(obj, SpeckitPlugin) and
                obj != SpeckitPlugin):

                plugin_instance = obj()
                plugin_instance.initialize(self.speckit)

                self.plugins[plugin_instance.name] = plugin_instance

                # Register commands
                if hasattr(plugin_instance, 'commands'):
                    for command in plugin_instance.commands:
                        self.commands[command] = plugin_instance

                print(f"Loaded plugin: {plugin_instance.name}")

    def execute_command(self, command: str, args: list):
        """Execute plugin command"""
        if command in self.commands:
            plugin = self.commands[command]
            return plugin.execute(command, args)
        else:
            raise ValueError(f"Unknown command: {command}")

    def list_plugins(self):
        """List all loaded plugins"""
        return [
            {
                "name": plugin.name,
                "version": plugin.version,
                "description": plugin.description
            }
            for plugin in self.plugins.values()
        ]

# Example plugin
class SecurityPlugin(SpeckitPlugin):
    """Security analysis plugin"""

    def __init__(self):
        super().__init__()
        self.name = "security"
        self.version = "1.0.0"
        self.description = "Security analysis and vulnerability scanning"
        self.commands = ["security-scan", "security-audit"]

    def execute(self, command: str, args: list):
        """Execute security commands"""
        if command == "security-scan":
            return self.security_scan(args)
        elif command == "security-audit":
            return self.security_audit(args)

    def security_scan(self, args: list):
        """Perform security scan"""
        # Implementation
        return {"status": "completed", "issues_found": 0}

    def security_audit(self, args: list):
        """Perform security audit"""
        # Implementation
        return {"status": "completed", "audit_score": 0.92}
```

## Troubleshooting

### Common Integration Issues

#### 1. IDE Extension Problems
**Problem**: Speckit commands not working in IDE

**Solutions**:
```bash
# Check Speckit installation
speckit --version

# Verify integration path
ls -la .speckit/

# Restart IDE and reload extensions
# Clear IDE cache and reinstall extensions
```

#### 2. Git Hook Failures
**Problem**: Git hooks blocking commits

**Diagnosis**:
```bash
# Test hooks manually
.git/hooks/pre-commit

# Check hook permissions
ls -la .git/hooks/

# Validate Speckit configuration
speckit constitution --validate --verbose
```

#### 3. CI/CD Pipeline Issues
**Problem**: Speckit validation failing in CI

**Debugging**:
```yaml
# Add debug steps to CI
- name: Debug Speckit
  run: |
    speckit --version
    speckit doctor
    ls -la .speckit/
    cat .speckit/config/speckit_config.json
```

#### 4. API Connection Issues
**Problem**: Cannot connect to Speckit API

**Troubleshooting**:
```bash
# Check API server status
speckit api status

# Test API endpoint
curl http://localhost:8080/api/v1/health

# Check logs
speckit api logs
```

### Performance Optimization

#### 1. Cache Optimization
```bash
# Clear Speckit cache
speckit cache clear

# Optimize cache size
speckit cache optimize --max-size 100MB

# Preload common data
speckit cache preload --type tasks,evidence
```

#### 2. Parallel Processing
```json
{
  "performance": {
    "parallel_processing": true,
    "max_workers": 4,
    "timeout_seconds": 300,
    "memory_limit": "1GB"
  }
}
```

## Conclusion

The Speckit Developer Integration Guide provides comprehensive instructions for integrating Speckit into various development environments and workflows. By following these guidelines, development teams can:

- **Enhance Productivity**: Seamless integration with existing tools and workflows
- **Maintain Quality**: Automated validation and evidence collection
- **Enable Collaboration**: Shared task management and progress tracking
- **Ensure Compliance**: Continuous validation and quality gates
- **Scale Effectively**: Plugin system and API for custom extensions

The integration patterns and examples provided can be adapted to specific project requirements and organizational workflows, ensuring that Speckit enhances rather than disrupts existing development practices.
