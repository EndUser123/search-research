# speckit-specify.md

## Metadata
- name: Speckit Specify
- description: Generate implementation-ready feature specifications with solo developer workflow automation
- argument-hint: "[feature_description] [options]"

## Speckit Specify

### Purpose
Transform feature descriptions into practical specifications ready for immediate implementation, with integration to CSF NIP knowledge system and implementation patterns from real projects.

### Variables
FEATURE_DESCRIPTION: $1
OPTIONS: $2
SPEC_OUTPUT_DIR: '.speckit/specs/'
TEMPLATE_TYPE: 'feature'  # Default template type, will be dynamically determined
TEMPLATE_PATH: '.speckit/templates/feature-specification-template.md'  # Dynamic based on TEMPLATE_TYPE
CONSTITUTION_PATH: '.speckit/memory/constitution.md'

### Instructions
- Always validate prerequisites before proceeding
- Apply evidence-based answers standard - never assume, always verify with real data
- Follow command verification protocol for all operations
- Store findings in CSF NIP knowledge system for future reference

### Quality Constraints
- **Constitutional Compliance**: All specifications must align with project constitution principles
- **Requirement Clarity**: Avoid ambiguous terms; provide specific, measurable requirements
- **User-Centric Focus**: Structure around user stories and scenarios, not technical implementation
- **Scope Boundaries**: Clearly define what's in scope and explicitly state exclusions
- **Success Criteria**: Include measurable outcomes to validate feature completion
- **Traceability Foundation**: Structure requirements to support traceability through planning and implementation phases

### Supporting Documentation
For comprehensive documentation and advanced guidance:
- **Help Documentation**: `../docs/speckit_specify_help.md`
- **Use Cases & Workflows**: `../docs/speckit_specify_use_cases.md`

### Specification Structure Reference
Generate specifications using this structure:
```markdown
# [Feature Name] Specification

## 1. Overview and Context
### 1.1 Feature Purpose
### 1.2 Scope and Boundaries
### 1.3 Success Criteria

## 2. User Stories
### 2.1 User Story 1: [Title]
**As a** [user persona], **I want to** [action], **so that** [benefit].

**Acceptance Criteria:**
- Given [context], when [action], then [outcome]
- [Additional criteria]

## 3. Functional Requirements
### FR-001: [Requirement Title]
- [Requirement description]
- [Success criteria]
- [Dependencies]

## 4. Non-Functional Requirements
### NFR-001: [Category] - [Requirement]
- [Specific requirement]
- [Measurement criteria]

## 5. Constraints
### 5.1 Technical Constraints
### 5.2 Business Constraints
### 5.3 Regulatory Constraints

## 6. Assumptions and Dependencies
### 6.1 Assumptions
### 6.2 Dependencies

## 7. Glossary
[Key terms and definitions]
```

### Codebase Structure
# .speckit/
#  templates/
#    - spec-template.md
#  specs/
#    - active/
#    - completed/
#    - archived/
#  memory/
#    - constitution.md
#  registry/
#    - tsk_registry.json

### Workflow
1. **Validate Prerequisites:**
   - Check if `FEATURE_DESCRIPTION` is provided. If not, STOP immediately and ask for feature description.
   - Verify constitution exists at `CONSTITUTION_PATH`. If not found, run `/speckit.constitution create` first.
   - Validate template exists at `TEMPLATE_PATH`. If not found, STOP and report missing template.

2. **System Discovery Protocol:**
   - Run discovery protocol to research existing patterns:
   ```bash
   cd "C:\_Python\_Projects\__csf.nip"
   python src/modules/orchestration/discovery_engine.py discover --project [FEATURE_DESCRIPTION]
   ```
   - Search CSF NIP knowledge system for relevant specification patterns:
   ```bash
   python scripts/knowledge_interface.py search --query "[FEATURE_DESCRIPTION] specification patterns"
   ```

3. **Parse Options:**
   - Parse `OPTIONS` for implementation focus, solo dev optimization, timebox, tech stack, complexity, and template parameter
   - Extract template parameter if specified (e.g., "template:rca", "template:enhancement", "template:integration", "template:learning")
   - Set default values if not provided
   - **Validate template parameter**: If `template:parameter` specified, validate against available templates:
     ```bash
     AVAILABLE_TEMPLATES=("feature" "rca" "enhancement" "integration" "learning")
     if [[ ! " ${AVAILABLE_TEMPLATES[@]} " =~ " ${SPECIFIED_TEMPLATE} " ]]; then
       STOP and report error: "Invalid template: ${SPECIFIED_TEMPLATE}. Available templates: ${AVAILABLE_TEMPLATES[*]}"
     fi
     ```

4. **Intelligent Template Selection:**
   - **Explicit Template Selection**: If `template:parameter` found in OPTIONS, use specified template
   - **Intelligent Detection**: Analyze `FEATURE_DESCRIPTION` for keywords to determine appropriate template:
     - RCA keywords: "bug", "issue", "problem", "investigation", "debug", "fix", "troubleshoot"
     - Enhancement keywords: "improve", "enhance", "optimize", "refactor", "upgrade", "better"
     - Integration keywords: "integrate", "connect", "api", "external", "third-party", "sync"
     - Learning keywords: "learn", "research", "explore", "investigate", "study", "understand"
   - **Default Fallback**: Use feature-specification-template.md for all other requests
   - **Update TEMPLATE_TYPE**: Set based on selected template (feature/rca/enhancement/integration/learning)
   - **Construct TEMPLATE_PATH**: Build path dynamically: `.speckit/templates/${TEMPLATE_TYPE}-specification-template.md`
   - **Validate template file exists**: Check if template file exists before proceeding:
     ```bash
     if [[ ! -f "${TEMPLATE_PATH}" ]]; then
       STOP and report error: "Template file not found: ${TEMPLATE_PATH}"
     fi
     ```

5. **Generate Specification:**
   - Read dynamic `TEMPLATE_PATH` to get specification template structure
   - Read `CONSTITUTION_PATH` to ensure compliance with project principles
   - Transform `FEATURE_DESCRIPTION` into structured specification using selected template
   - Apply implementation patterns discovered in step 2

5.5. **Quality Enhancement:**
   - **Completeness Validation**: Ensure all required sections are populated with meaningful content
   - **Clarity Enhancement**: Remove ambiguity and add specific details where needed
   - **Consistency Checking**: Verify terminology and requirement alignment throughout
   - **Measurability Addition**: Add quantifiable success criteria and validation metrics
   - **Traceability Preparation**: Structure requirements to support planning and implementation phases

6. **Automatic Clarification Check:**
   - **Analyze Generated Specification**: Scan the generated specification for clarity indicators:
     - Search for vague terms: "fast", "secure", "intuitive", "robust", "user-friendly"
     - Look for placeholder markers: "TK", "TODO", "UNCLEAR", "NEEDS", "TBD", "TBC"
     - Check for missing acceptance criteria in user stories
     - Identify undefined constraints and assumptions
   - **Calculate Clarity Score**: Rate specification clarity (0-100)
     - High clarity (80-100): No clarification needed
     - Medium clarity (60-79): Clarification recommended
     - Low clarity (0-59): Clarification required
   - **Automatic Clarification Trigger**: If clarity score < 80:
     ```bash
     echo "⚠️  Specification clarity score: [score]/100 - Automatic clarification recommended"
     echo "Vague terms found: [list of vague terms]"
     echo "Missing elements: [list of missing elements]"
     echo ""
     echo "🔧 Running automatic clarification: /speckit.clarify"
     echo ""
     /speckit.clarify "auto:true, focus:measurability, acceptance_criteria, constraints"
     ```
   - **Manual Clarification Option**: If clarity score 60-79, provide user choice:
     ```bash
     echo "⚠️  Specification clarity score: [score]/100 - Clarification recommended"
     echo "Run manual clarification: /speckit.clarify"
     echo "Or proceed with current specification to: /speckit.plan"
     ```

7. **Store Knowledge:**
   - Store specification generation findings in CSF NIP knowledge system:
   ```bash
   python scripts/knowledge_interface.py store --type specification_generation --evidence [generation-evidence]
   ```

8. **Output Results:**
   - Save specification to `SPEC_OUTPUT_DIR` with descriptive filename
   - Generate validation report for specification quality

### Report Format
## Specification Generated Successfully

### Feature: **[FEATURE_DESCRIPTION]**
- **Specification File**: `[path/to/generated/spec.md]`
- **Template Type**: `[TEMPLATE_TYPE]`
- **Implementation Focus**: `[implementation_focus_value]`
- **Complexity**: `[complexity_level]`
- **Estimated Time**: `[time_estimate]`

### Quality Validation:
- **Completeness Score**: `[score/100]`
- **Clarity Score**: `[score/100]` *[New automatic metric]*
- **Clarity Assessment**: `[assessment]`
- **Consistency Check**: `[pass/fail]`
- **Measurability**: `[number of measurable criteria]`
- **Traceability Ready**: `[yes/no]`
- **Clarification Needed**: `[yes/no/no - auto triggered]`

### Knowledge Integration:
- **Patterns Applied**: `[number] patterns from knowledge base`
- **Evidence Stored**: `[evidence_summary]`
- **Compliance Status**: `[constitution_compliance]`

### Previous Steps:
- Run `/speckit.constitution create` if constitution doesn't exist at `[CONSTITUTION_PATH]`

### Next Steps:
- Review specification at `[spec_path]`
- Use `/speckit.clarify` to resolve specification ambiguities (auto-triggered if needed, otherwise manual)
- Use `/speckit.plan` for architectural planning
- Use `/speckit.tasks` for implementation breakdown

### Technical Research (if needed):
- Use `/speckit.research` for technical investigation, technology selection, or compliance requirements
- Research is invoked separately when technical unknowns exist that impact planning decisions
