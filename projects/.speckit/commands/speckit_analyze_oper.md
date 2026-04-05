---
name: "/speckit.analyze"
category: "Speckit Workflow"
purpose: "Perform a non-destructive cross-artifact consistency and quality analysis across spec.md, plan.md, and tasks.md after task generation"
entry_point: "primary"
---

# Speckit Analyze - Cross-Artifact Quality Validation

Perform a comprehensive consistency and quality analysis across the three core speckit artifacts (`spec.md`, `plan.md`, `tasks.md`) before implementation begins. This command identifies inconsistencies, duplications, ambiguities, and underspecified items while strictly adhering to read-only analysis.

## 🚀 Quick Start

### Analyze Current Feature
```bash
cd "C:\_Python\_Projects\.speckit"
powershell -ExecutionPolicy Bypass -File ".\scripts\powershell\check-prerequisites.ps1" -Json -RequireTasks -IncludeTasks
```

### Quick Analysis with Default Settings
```bash
# From feature directory root
cd /path/to/feature
python -c "
import json
import subprocess
result = subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', 'C:/_Python/_Projects/.speckit/scripts/powershell/check-prerequisites.ps1', '-Json', '-RequireTasks', '-IncludeTasks'], capture_output=True, text=True)
print(result.stdout)
"
```

## ⚙️ Command Options

The analyze command works through the prerequisite checker script. Key options:

| Option | Purpose |
|--------|---------|
| `-Json` | Output structured JSON for automated processing |
| `-RequireTasks` | Ensure tasks.md exists and is complete |
| `-IncludeTasks` | Include task analysis in validation scope |

## 📋 Use Cases

### When to Use /speckit.analyze

- **Pre-Implementation Validation**: After completing all planning but before starting implementation
- **Quality Gates**: Final validation before committing to implementation work
- **Team Review**: Provide structured analysis for team review and approval
- **Compliance Checking**: Ensure all artifacts align with project constitution
- **Risk Assessment**: Identify potential issues before they become implementation problems

### When NOT to Use /speckit.analyze

- **During Active Development**: Use when planning is complete, not during implementation
- **Single Artifact Review**: Use specific commands for individual file analysis
- **Emergency Fixes**: Bypass analysis for critical production issues

## 🔧 Prerequisites

### Required Artifacts
1. **Complete spec.md**: Feature specification with all requirements
2. **Complete plan.md**: Technical design and architecture decisions
3. **Complete tasks.md**: Implementation task breakdown with dependencies
4. **Project Constitution**: Located at `.speckit/memory/constitution.md`

### Validation Commands
```bash
# Verify all required files exist
cd /path/to/feature
ls -la | grep -E "(spec\.md|plan\.md|tasks\.md)"

# Check project constitution
cat .speckit/memory/constitution.md

# Run prerequisite checker
cd "C:\_Python\_Projects\.speckit"
powershell -ExecutionPolicy Bypass -File ".\scripts\powershell\check-prerequisites.ps1" -Json
```

## 🔧 Troubleshooting

### Common Issues and Solutions

**❌ "tasks.md not found or incomplete"**
```bash
# Solution: Generate tasks first
/speckit.tasks "your feature description"
```

**❌ "Constitution conflicts detected"**
```bash
# Solution: Review constitution and adjust artifacts
cat .speckit/memory/constitution.md
# Update spec.md, plan.md, or tasks.md to align with constitution principles
```

**❌ "PowerShell execution policy error"**
```bash
# Solution: Set execution policy for current session
powershell -ExecutionPolicy Bypass -File ".\scripts\powershell\check-prerequisites.ps1" -Json
```

**❌ "Inconsistent terminology across artifacts"**
```bash
# Solution: Review and standardize terminology
grep -r "inconsistent_term" /path/to/feature/
# Update all files to use consistent terminology
```

### Analysis Quality Issues

**Too Many Minor Issues**
- Focus on CRITICAL and HIGH severity items first
- Use analysis to guide prioritization, not block all progress

**Missing Constitution Reference**
- Ensure constitution path is correct: `.speckit/memory/constitution.md`
- Verify constitution contains required principles and constraints

## 🧠 Complete Operational Logic

The analysis executes through these systematic phases:

### 1. Initialize Analysis Context
Run prerequisite checker to identify feature context and validate required artifacts exist

### 2. Load Artifacts with Progressive Disclosure
Load only necessary content from each artifact:
- **spec.md**: Requirements, user stories, constraints
- **plan.md**: Architecture, technical decisions, dependencies
- **tasks.md**: Task breakdown, dependencies, implementation details
- **constitution**: Project principles and constraints

### 3. Build Semantic Models
Create internal representations for analysis:
- Requirements inventory with stable keys
- User story/action inventory
- Task coverage mapping
- Constitution rule set extraction

### 4. Detection Passes (Token-Efficient Analysis)
Focus on high-signal findings with severity assignment:
- **CRITICAL**: Constitution violations, missing core artifacts, zero coverage
- **HIGH**: Duplicate/conflicting requirements, ambiguous constraints
- **MEDIUM**: Terminology drift, missing non-functional coverage
- **LOW**: Style improvements, minor redundancies

### 5. Generate Analysis Report
Output structured Markdown report with:
- Findings table with ID, category, severity, location, summary, recommendation
- Coverage summary table
- Constitution alignment issues
- Unmapped tasks identification
- Metrics and statistics

### 6. Provide Next Actions
Recommend specific follow-up commands based on analysis results and issue severity

## 📊 Output Format

The analysis generates a structured report with these sections:

```markdown
## Specification Analysis Report
| ID | Category | Severity | Location(s) | Summary | Recommendation |
|----|----------|----------|-------------|---------|----------------|

## Coverage Summary Table
| Requirement Key | Has Task? | Task IDs | Notes |

## Constitution Alignment Issues
[List of any constitution violations]

## Unmapped Tasks
[List of tasks without requirement coverage]

## Metrics
- Total Requirements
- Total Tasks
- Coverage %
- Critical Issues Count
```

## 🚨 Critical Constraints

**STRICTLY READ-ONLY**: This command never modifies files - analysis only

**Constitution Authority**: Project constitution is non-negotiable. Conflicts require artifact adjustment, not constitution interpretation.

**Prerequisite Dependency**: Must run after `/speckit.tasks` completion. Cannot analyze incomplete artifact sets.

**Evidence-Based**: All findings must reference specific locations and evidence. No speculative or theoretical issues.
