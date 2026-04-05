---
name: "/speckit.checklist"
category: "Speckit Workflow"
purpose: "Generate a custom checklist for the current feature based on user requirements to validate requirements quality"
entry_point: "primary"
---

# Speckit Checklist - Requirements Quality Validation

Generate custom checklists that serve as "Unit Tests for English" - validating the quality, clarity, and completeness of requirements before implementation. Checklists test whether requirements are well-written, complete, unambiguous, and ready for implementation, NOT whether implementation works.

## 🚀 Quick Start

### Generate UX Requirements Checklist
```bash
cd "C:\_Python\_Projects\.speckit"
powershell -ExecutionPolicy Bypass -File ".\scripts\powershell\check-prerequisites.ps1" -Json
```

### Generate Security Checklist
```bash
/speckit.checklist "focus:security, audience:reviewer, depth:thorough"
```

### Generate Performance Checklist
```bash
/speckit.checklist "focus:performance, include:latency, throughput, scalability"
```

## ⚙️ Command Options

Checklist generation accepts dynamic parameters for customization:

| Parameter | Values | Description |
|-----------|--------|-------------|
| **Focus Areas** | `ux`, `security`, `performance`, `api`, `testing`, `accessibility` | Domain-specific checklist generation |
| **Audience** | `author`, `reviewer`, `qa`, `release` | Target user for checklist complexity |
| **Depth Level** | `standard`, `thorough`, `lightweight` | Checklist comprehensiveness |
| **Risk Priority** | `high`, `medium`, `low`, `critical` | Risk areas to emphasize |
| **Exclusion** | `performance`, `deployment`, `maintenance` | Areas to explicitly exclude |

## 📋 Use Cases

### When to Use /speckit.checklist

- **Requirements Review**: Validate spec quality before implementation planning
- **Team Collaboration**: Create structured review criteria for team members
- **Quality Gates**: Ensure requirements meet minimum quality standards
- **Domain-Specific Validation**: Generate checklists for specialized areas (security, UX, performance)
- **Compliance Requirements**: Validate adherence to regulatory or organizational standards

### When NOT to Use /speckit.checklist

- **Implementation Testing**: Use test frameworks for code validation
- **Code Review**: Use code review tools and checklists for implementation quality
- **User Acceptance Testing**: Use UAT frameworks for functionality validation

## 🔧 Prerequisites

### Required Context
1. **Feature Specification**: Complete spec.md with requirements and constraints
2. **Feature Directory**: Valid speckit feature directory structure
3. **Checklists Directory**: `FEATURE_DIR/checklists/` for generated checklists

### Validation Commands
```bash
# Verify feature directory structure
cd /path/to/feature
ls -la | grep -E "(spec\.md|plan\.md|tasks\.md)"

# Check prerequisites
cd "C:\_Python\_Projects\.speckit"
powershell -ExecutionPolicy Bypass -File ".\scripts\powershell\check-prerequisites.ps1" -Json

# Ensure checklists directory exists
mkdir -p /path/to/feature/checklists
```

## 🔧 Troubleshooting

### Common Issues and Solutions

**❌ "No spec.md found in feature directory"**
```bash
# Solution: Generate specification first
/speckit.specify "your feature description"
```

**❌ "Checklist directory not accessible"**
```bash
# Solution: Create checklists directory
mkdir -p /path/to/feature/checklists
chmod 755 /path/to/feature/checklists
```

**❌ "Ambiguous focus area specified"**
```bash
# Solution: Use specific focus areas
/speckit.checklist "focus:ux security"  # Multiple specific areas
/speckit.checklist "focus:standard"      # Standard comprehensive checklist
```

**❌ "Generate checklist with no actionable items"**
```bash
# Solution: Check spec completeness
cat /path/to/feature/spec.md
# Ensure spec has measurable requirements and acceptance criteria
```

### Checklist Quality Issues

**Too Generic Items**
- Be more specific with focus parameters
- Include domain-specific requirements in spec

**Missing Traceability**
- Ensure spec has section numbering or ID system
- Add requirement identifiers to spec before generating checklist

**Wrong Test Type**
- Remember: checklists test REQUIREMENTS, not implementation
- Focus on "Are X specified?" rather than "Does X work?"

## 🧠 Complete Operational Logic

The checklist generation follows this systematic process:

### 1. Setup and Context Discovery
Run prerequisite checker to identify feature context and available documentation

### 2. Dynamic Intent Clarification
Generate up to 3 contextual questions based on:
- User-provided hints and constraints
- Extracted signals from spec/plan/tasks
- Risk indicators and stakeholder requirements
- Missing dimensions that materially affect checklist content

### 3. Context Understanding
Combine user input with clarifying answers to derive:
- Checklist theme and domain focus
- Explicit must-have items
- Focus area selection and mapping
- Missing context inference from artifacts

### 4. Feature Context Loading
Load relevant content with progressive disclosure:
- **spec.md**: Feature requirements and scope
- **plan.md**: Technical details and dependencies (if exists)
- **tasks.md**: Implementation tasks (if exists)
- **constitution**: Project principles and constraints

### 5. Generate Requirements Quality Checklist
Create "Unit Tests for Requirements" that evaluate:
- **Requirement Completeness**: Are all necessary requirements documented?
- **Requirement Clarity**: Are requirements specific and unambiguous?
- **Requirement Consistency**: Do requirements align without conflicts?
- **Acceptance Criteria Quality**: Are success criteria measurable?
- **Scenario Coverage**: Are all flows/cases addressed?
- **Edge Case Coverage**: Are boundary conditions defined?
- **Non-Functional Requirements**: Performance, security, accessibility specifications
- **Dependencies & Assumptions**: Are they documented and validated?

### 6. Structure and Format
Apply canonical template structure:
- Unique checklist filename based on domain
- Sequential numbering starting from CHK001
- Category grouping by quality dimension
- Each run creates NEW file (never overwrites)

## 📝 Checklist Item Format

### Correct Pattern (Testing Requirements Quality)
```markdown
- [ ] CHK001 - Are the exact number and layout of featured episodes explicitly specified? [Completeness, Spec §FR-001]
- [ ] CHK002 - Are hover state requirements consistently defined for all interactive elements? [Consistency, Spec §FR-003]
- [ ] CHK003 - Are loading state requirements defined for asynchronous episode data? [Gap]
```

### Anti-Pattern (Testing Implementation)
```markdown
- [ ] CHK001 - Verify landing page displays 3 episode cards [WRONG]
- [ ] CHK002 - Test hover states work correctly on desktop [WRONG]
- [ ] CHK003 - Confirm logo click navigates to home page [WRONG]
```

## 📊 Generated Checklist Structure

```markdown
# [Domain] Requirements Quality Checklist

## Purpose: "Unit Tests for English"
## Focus Areas: [Selected domains]
## Depth: [Standard/Thorough/Lightweight]
## Created: [Date]
## Audience: [Target user]

### Requirement Completeness
- [ ] CHK001 - [Requirement completeness question] [Traceability]

### Requirement Clarity
- [ ] CHK002 - [Requirement clarity question] [Traceability]

### Requirement Consistency
- [ ] CHK003 - [Requirement consistency question] [Traceability]

[Additional categories as needed]

## Summary
- Total Items: [Count]
- Critical Items: [Count]
- Coverage Areas: [List]
```

## 🚨 Critical Constraints

**Unit Tests for Requirements**: Checklists validate requirement quality, NOT implementation correctness

**Progressive Disclosure**: Load only necessary content, avoid full file dumping

**Evidence-Based**: All checklist items must reference specific locations or identify gaps

**Non-Destructive**: Each run creates new file, never overwrites existing checklists

**80% Traceability Rule**: Minimum 80% of items must include traceability references

**Domain Specificity**: Use descriptive filenames (ux.md, security.md, api.md) for easy identification

## 📁 File Management

**Naming Convention**: `[domain].md` where domain indicates focus area

**Location**: `FEATURE_DIR/checklists/` directory

**Uniqueness**: Each invocation creates new file with timestamp if needed

**Cleanup**: Users responsible for cleaning up obsolete checklists when done
