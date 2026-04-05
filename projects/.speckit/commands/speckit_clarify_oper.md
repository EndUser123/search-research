---
name: "/speckit.clarify"
category: "Speckit Workflow"
purpose: "Identify underspecified areas in the current feature spec by asking up to 5 highly targeted clarification questions and encoding answers back into the spec"
entry_point: "primary"
---

# speckit-clarify.md

## Metadata
- name: Speckit Clarify
- description: Systematically improve specification quality through targeted clarification questions and gap resolution
- argument-hint: "[focus_areas] [options]"
- allowed-tools: [Read, Write, Bash, Grep, Glob]
- model: claude-sonnet-4

## Speckit Clarify - Requirements Refinement and Specification Enhancement

### Purpose
Identify underspecified areas, ambiguities, and gaps in feature specifications through targeted clarification questions. This command systematically improves specification quality by resolving unknowns and ensuring requirements are complete, clear, and actionable.

### Variables
FOCUS_AREAS: $1
OPTIONS: $2
SPEC_PATH: 'spec.md'
MAX_QUESTIONS: 5
CONSTITUTION_PATH: '.speckit/memory/constitution.md'

### Quality Constraints
- **Evidence-Based Validation**: Base clarification questions on actual gaps identified in specification, not assumptions
- **Requirement Clarity**: Focus on making requirements specific, measurable, and actionable
- **User-Centric Focus**: Structure questions around user needs and business value, not implementation details
- **Scope Boundaries**: Clarify what's in scope and explicitly state exclusions to avoid scope creep
- **Success Criteria**: Ensure clarifications result in measurable acceptance criteria and validation approaches
- **Traceability Foundation**: Structure clarified requirements to support planning and implementation phases

## Supporting Documentation
For comprehensive documentation and advanced guidance:
- **Help Documentation**: `../docs/speckit_clarify_help.md`
- **Use Cases & Workflows**: `../docs/speckit_clarify_use_cases.md`

## Usage Examples

### Clarify Specification with Default Questions
```bash
/speckit.clarify
```

### Clarify with Specific Focus Areas
```bash
/speckit.clarify "focus:security, performance, user_experience"
```

### Clarify with Provided Answers
```bash
/speckit.clarify "answers:performance_subsecond, security_oauth2, ux_mobile_first"
```

## Codebase Structure
# .speckit/
#  specs/
#    - active/
#       - TSK-XXX-*
#          - spec.md
#          - plan.md
#          - research.md
#    - completed/
#  memory/
#    - constitution.md
#  templates/
#    - spec-template.md

## Workflow
1. **Validate Prerequisites:**
   - Check if specification file exists at `SPEC_PATH`. If not found, STOP and report missing specification.
   - Verify project constitution exists at `CONSTITUTION_PATH`. If not found, STOP and report missing constitution.
   - Validate working directory is a valid speckit feature directory.

2. **Parse Parameters:**
   - Parse `FOCUS_AREAS` for specific clarification domains (security, performance, ux, integration, testing)
   - Parse `OPTIONS` for clarification parameters (max_questions, answer_mode, depth_level, priority, update_mode)
   - Set default values if not provided: max_questions=5, answer_mode=interactive, depth_level=detailed

3. **Specification Analysis:**
   - Read specification file to identify clarification opportunities:
   - Search for ambiguous terms: "fast", "secure", "intuitive", "robust", "user-friendly"
   - Look for placeholder markers: "TK", "TODO", "UNCLEAR", "NEEDS", "TBD", "TBC"
   - Identify missing acceptance criteria in user stories
   - Find undefined constraints and assumptions
   - Check for unmeasurable requirements and success criteria

4. **Context Discovery:**
   - Gather context from related artifacts if available:
   - Extract relevant information from plan.md, tasks.md, research.md
   - Identify constitutional requirements and principles
   - Apply domain-specific understanding to identify gaps
   - Consider different stakeholder viewpoints and needs

5. **Question Generation and Prioritization:**
   - Generate targeted clarification questions based on analysis results:
   - Prioritize questions by impact on implementation success
   - Identify questions blocking subsequent phases
   - Focus on questions addressing high-risk areas
   - Emphasize questions affecting user experience and value
   - Include questions affecting technical and business feasibility
   - Limit to MAX_QUESTIONS highest-priority questions

6. **Response Processing:**
   - **If answer_mode=interactive**: Present questions for immediate response
   - **If answer_mode=provided**: Process pre-specified answers from user input
   - **If answer_mode=auto**: Use domain knowledge to suggest reasonable defaults
   - Validate responses address the original questions
   - Ensure responses are specific and actionable

7. **Quality Enhancement:**
   - **Completeness Validation**: Ensure all identified gaps have been addressed
   - **Clarity Enhancement**: Confirm improved requirement clarity and specificity
   - **Measurability Validation**: Ensure requirements are measurable and testable
   - **Consistency Verification**: Validate specification internal consistency
   - **Constitution Compliance**: Ensure updates align with project constitution

8. **Specification Updates:**
   - **If update_mode=immediate**: Apply changes directly to specification file
   - **If update_mode=review**: Show proposed changes for user approval
   - **If update_mode=suggested**: Provide recommendations without applying changes
   - Maintain backup of original specification
   - Update specification with clarified requirements
   - Ensure consistency with existing specification content

9. **Store Knowledge:**
   - Store clarification findings and decisions in CSF NIP knowledge system
   - Record clarification questions and responses for future reference
   - Update project patterns based on clarification insights

## Template Structure Reference
Generate clarification questions and responses using this structure:
```markdown
# Specification Clarification Report

## Clarity Analysis
### Ambiguous Terms Identified:
- **Term 1**: [Current vague term] → [Suggested specific alternative]
- **Term 2**: [Current vague term] → [Suggested specific alternative]

### Missing Elements:
- [Missing element 1 with impact assessment]
- [Missing element 2 with impact assessment]

## Clarification Questions
### Question 1: [Specific, actionable question]
**Why important**: [Impact on implementation success]
**Current gap**: [What's unclear in current specification]

### Question 2: [Specific, actionable question]
**Why important**: [Impact on implementation success]
**Current gap**: [What's unclear in current specification]

[Continue up to max_questions]

## Response Integration
### Clarified Requirements:
- **Updated Requirement 1**: [Specific, measurable requirement]
- **Updated Requirement 2**: [Specific, measurable requirement]

### Specification Updates Applied:
- [Section updated]: [Summary of changes]
- [Impact assessment]: [How changes affect related requirements]
```

## Report Format
## Clarification Report for `[specification_name]`

### Analysis Summary:
- **Specification File**: `[path/to/spec.md]`
- **Focus Areas**: `[processed focus areas]`
- **Questions Generated**: `[number]/[max_questions]`

### Quality Improvements:
- **Clarity Score**: `[improvement_score]/100`
- **Gaps Addressed**: `[number] clarification targets resolved`
- **Measurable Requirements**: `[number] now measurable`
- **Consistency Check**: `[pass/fail]`

### Specification Updates:
- **Sections Modified**: `[number] sections updated`
- **Constraints Clarified**: `[number] constraints clarified`
- **Acceptance Criteria Added**: `[number] acceptance criteria added`

### Next Steps:
- Review updated specification at `[spec_path]`
- Proceed with `/speckit.plan` for architectural planning
- Use `/speckit.analyze` to validate artifact consistency

## 🧠 Complete Operational Logic

The clarification process follows this systematic approach:

### 1. Specification Analysis and Gap Identification
Analyze specification for clarification opportunities:
- **Ambiguous Terms**: Identify vague adjectives and undefined concepts
- **Missing Quantification**: Find unmeasurable requirements and criteria
- **Incomplete Scenarios**: Identify missing user stories and edge cases
- **Undefined Constraints**: Find unstated assumptions and limitations
- **Validation Gaps**: Identify requirements without clear acceptance criteria

### 2. Context Discovery and Research
Gather context from available artifacts:
- **Related Documents**: Extract relevant information from plan.md, tasks.md, research.md
- **Constitution Constraints**: Identify constitutional requirements and principles
- **Domain Knowledge**: Apply domain-specific understanding to identify gaps
- **Stakeholder Perspective**: Consider different stakeholder viewpoints and needs

### 3. Question Generation and Prioritization
Generate targeted clarification questions:
- **Impact Assessment**: Prioritize questions by impact on implementation success
- **Dependency Analysis**: Identify questions blocking subsequent phases
- **Risk Evaluation**: Focus on questions addressing high-risk areas
- **User Value**: Emphasize questions affecting user experience and value
- **Feasibility**: Include questions affecting technical and business feasibility

### 4. Question Delivery and Response Collection
Present questions and collect responses:
- **Interactive Mode**: Present questions for immediate response
- **Provided Answers**: Process pre-specified answers from user input
- **Auto-resolution**: Use domain knowledge to suggest reasonable defaults
- **Multi-format**: Support various response formats and structures

### 5. Response Processing and Integration
Process clarification responses and update specifications:
- **Answer Validation**: Ensure responses address the original questions
- **Specification Updates**: Integrate clarified requirements into specification
- **Consistency Checking**: Ensure updates align with existing specification content
- **Impact Analysis**: Assess how changes affect related requirements and plans

### 6. Quality Validation and Completion
Validate clarification quality and completion:
- **Requirement Completeness**: Verify all identified gaps have been addressed
- **Clarity Enhancement**: Confirm improved requirement clarity and specificity
- **Measurability Validation**: Ensure requirements are now measurable and testable
- **Consistency Verification**: Validate specification internal consistency

## 📝 Clarification Question Examples

### Performance Requirements
**Before**: "The system must be fast"
**Clarification Questions**:
- "What specific response time requirements exist for different user operations?"
- "How many concurrent users must the system support while maintaining performance?"
- "Are there specific throughput requirements for data processing operations?"

**After**: "The system must respond to user actions within 200ms for 95% of requests and support 1000 concurrent users"

### Security Requirements
**Before**: "The system must be secure"
**Clarification Questions**:
- "What specific authentication methods are required (OAuth 2.0, JWT, SAML)?"
- "What data protection requirements exist (encryption at rest, in transit, both)?"
- "Are there specific compliance standards that must be met (GDPR, SOC 2, PCI DSS)?"

**After**: "The system must implement OAuth 2.0 authentication, encrypt all data at rest and in transit using AES-256, and comply with GDPR data protection requirements"

### User Experience Requirements
**Before**: "The interface must be intuitive"
**Clarification Questions**:
- "What specific user personas will be using the system?"
- "Are there accessibility requirements (WCAG 2.1 AA compliance, screen reader support)?"
- "What specific devices and screen sizes must be supported?"

**After**: "The system must support admin, end-user, and moderator personas, comply with WCAG 2.1 AA accessibility standards, and provide responsive design for desktop, tablet, and mobile devices"

## 📊 Clarification Categories and Examples

### Quantification Clarification
- **Performance Metrics**: Response times, throughput, concurrent users
- **Capacity Limits**: Data volumes, user counts, transaction rates
- **Availability Requirements**: Uptime percentages, maintenance windows

### Scenario Clarification
- **User Workflows**: Complete user journey specifications
- **Edge Cases**: Error conditions, boundary conditions, failure modes
- **Integration Points**: External system interactions and data flows

### Constraint Clarification
- **Technical Constraints**: Technology limitations, infrastructure requirements
- **Business Constraints**: Budget limitations, timeline requirements, resource constraints
- **Regulatory Constraints**: Compliance requirements, legal restrictions

### Acceptance Criteria Clarification
- **Success Metrics**: Measurable outcomes and validation criteria
- **Testing Requirements**: Test scenarios, validation approaches, acceptance testing
- **Quality Standards**: Performance benchmarks, security standards, usability requirements

## 🚨 Critical Constraints

**Maximum 5 Questions**: Limit to 5 high-impact clarification questions per session

**Specificity Required**: Questions must be specific and actionable, not generic

**Evidence-Based**: Questions should be based on identified gaps and ambiguities

**User-Centric**: Focus on user needs and business value, not implementation details

**Measurable Outcomes**: Clarifications must result in measurable, testable requirements

**Consistency Maintenance**: Updates must maintain specification internal consistency

**Constitution Compliance**: Clarifications must align with project constitution principles

## 📁 File Management

**Location**: Updates `FEATURE_DIR/spec.md` in place

**Backup**: Creates backup of original specification before updates

**Version Control**: Track clarification changes and decisions

**Documentation**: Maintains clarification log of questions and decisions

## 🔗 Related Commands

- **Before**: `/speckit.specify` (initial specification creation)
- **After**: `/speckit.plan` (technical design and architecture)
- **Optional**: `/speckit.research` (technical investigation)
- **Quality Gate**: `/speckit.analyze` (validate artifact consistency)
