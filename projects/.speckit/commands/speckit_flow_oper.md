# speckit-flow-orchestrator.md

## Metadata
- name: Speckit Flow Orchestrator
- description: Execute complete end-to-end development pipeline with discovery-driven phase orchestration and quality enforcement.
- argument-hint: "[project_dir] [optional_config_override]"


## Speckit Flow Orchestrator

### Purpose
Execute the complete 8-phase Speckit development pipeline from project discovery through final validation and completion. This orchestrator manages phase dependencies, evidence collection, quality enforcement, and error recovery to deliver validated implementations with full traceability.

### Variables
PROJECT_DIR: $1
CONFIG_OVERRIDE: $2
SESSION_ID: auto-generated-uuid
PHASE_STATE_FILE: '.speckit/.flow_session.json'
EVIDENCE_BASE_DIR: 'evidence'
MAX_RETRY_ATTEMPTS: 3
DEFAULT_TRUST_THRESHOLD: 0.8
DEFAULT_CONCURRENT_AGENTS: 5

### Session State Structure
The `PHASE_STATE_FILE` maintains comprehensive workflow tracking:
```json
{
  "session_id": "uuid-v4",
  "project_id": "TSK-###",
  "start_time": "ISO 8601 timestamp",
  "current_phase": "Phase X",
  "phase_status": {
    "phase_1": {"status": "completed", "duration": "minutes", "success_criteria_met": true},
    "phase_2": {"status": "completed", "duration": "minutes", "success_criteria_met": true},
    "phase_3": {"status": "skipped", "reason": "no clarifications needed"},
    "phase_4": {"status": "in_progress", "start_time": "timestamp"},
    "phase_5": {"status": "pending"},
    "phase_6": {"status": "pending"},
    "phase_7": {"status": "pending"}
  },
  "overall_success_rate": "percentage",
  "quality_gates_passed": "count/total",
  "evidence_collected": "artifact_count",
  "workflow_state": "active | completed | failed | paused"
}
```

### Success Criteria Tracking
Each phase includes specific success criteria that must be met before progression:

**Phase 1 Success**: Constitution validated and versioned
**Phase 2 Success**: Specification created with knowledge integration
**Phase 3 Success**: Specification refined and gaps resolved (if executed)
**Phase 4 Success**: Architecture and TDD plan validated
**Phase 5 Success**: Implementation completed with quality gates
**Phase 6 Success**: Cross-artifact validation passed
**Phase 7 Success**: Independent verification and archival complete

### Instructions
- Always validate phase completion before proceeding to next phase
- Collect and validate evidence at each phase transition
- Document all decisions and deviations in session log
- Use defined error recovery strategies before escalating
- Maintain continuous evidence flow from discovery through implementation

### Workflow

#### 0. Initialize Orchestrator Session
1. **Validate Project Context:**
   - Check if `PROJECT_DIR` exists and contains valid speckit structure
   - Verify `.speckit/specs/TSK-###-plan-name/` directory exists
   - Extract `PROJECT_ID` from directory name (TSK-### format)

2. **Initialize Session Management:**
   - Generate unique `SESSION_ID` for this execution
   - Create `PHASE_STATE_FILE` with session metadata
   - Set up `EVIDENCE_BASE_DIR` structure for all phases

3. **Load Configuration:**
   - Parse any `CONFIG_OVERRIDE` parameters
   - Apply defaults for missing parameters
   - Validate parameter constraints and compatibility

#### 1. Phase 1: Constitution Orchestration (MANDATORY)
**Command**: `/speckit.constitution`

**Purpose**: Establish project principles, boundaries, and governance framework before any discovery work.

**Initialize Memory Directory:**
```bash
# Constitution goes to .speckit/memory/constitution.md (per constitution command)
mkdir -p "$PROJECT_DIR/.speckit/memory/"
```

##### 1.1 Constitution Command Orchestration
**Execute Constitution Command:**
```bash
# Let the constitution command handle creation/validation intelligently
cd "$PROJECT_DIR"
/speckit.constitution "project:$PROJECT_ID"
```

**Validate Constitution Command Results:**
- Verify constitution command completed successfully
- Check `constitution.md` exists in `.speckit/memory/` and is complete
- **Note**: The constitution command handles its own audit, drift detection, and validation internally
- **If constitution command reports issues**: Follow its guidance for resolution

##### 1.2 Constitution Version Tracking
- Generate version identifier: `v{major}.{minor}.{patch}` based on changes detected
- Create git commit: `git add . && git commit -m "Constitution v{version}: {summary}"`
- Tag version: `git tag -a "constitution-v{version}" -m "Constitution version {version}"`
- Store version info in session state: `{ "version": "v1.0.0", "commit_hash": "...", "timestamp": "..." }`

**Phase 1 Validation:**
- Verify constitution command completed successfully
- Constitution file exists in `.speckit/memory/` and is complete
- **Note**: Constitution command handles its own internal validation and audit
- **If constitution command reported issues**: STOP and resolve before proceeding

**Update Session State:**
- Mark Phase 1 as completed in `PHASE_STATE_FILE`
- Store constitution version and completion status
- Document constitutional principles and boundaries for discovery phases

#### 2. Phase 2: Knowledge-Guided Specification (MANDATORY)
**Commands**: Knowledge Search → `/speckit.specify`

**Purpose**: Transform the user's request into a comprehensive specification enhanced by existing organizational knowledge and patterns.

##### 2.1 Pre-Specification Knowledge Discovery
**Search CSF NIP Knowledge System for Relevant Patterns:**
```bash
cd "$PROJECT_DIR"
# Search for existing patterns related to the request domain
python "C:\_Python\_Projects\__csf.nip\scripts\knowledge_interface.py" search --pattern_type "best_practice" --query "$USER_REQUEST"

# Search for security patterns if applicable
python "C:\_Python\_Projects\__csf.nip\scripts\knowledge_interface.py" search --type security --query "$USER_REQUEST"

# Search for architecture patterns
python "C:\_Python\_Projects\__csf.nip\scripts\knowledge_interface.py" search --type architecture --query "$USER_REQUEST"
```

**Integrate Knowledge Findings:**
- Document relevant patterns found in knowledge base
- Identify applicable standards and compliance requirements
- Note similar implementations or lessons learned
- Prepare knowledge-enhanced context for specification

##### 2.2 Specification Generation
**Execute Specification Command with Knowledge Context:**
```bash
cd "$PROJECT_DIR"
/speckit.specify "$USER_REQUEST" "tsk_assignment:true, complexity:moderate, include:dependencies, knowledge_guided:true"
```

**Validate Specification Results:**
- Verify specification document created and complete
- Confirm functional and non-functional requirements defined
- Validate user stories and acceptance criteria are clear
- Check TSK ID assigned and registered in coordination system
- **NEW**: Verify knowledge patterns have been incorporated where applicable
- **NEW**: Validate specification leverages existing organizational knowledge

##### 2.3 Specification Quality Check
**Initial Quality Validation:**
```bash
cd "$PROJECT_DIR"
# Quick specification quality validation
powershell -ExecutionPolicy Bypass -File "C:\_Python\_Projects\.speckit\scripts\powershell\check-prerequisites.ps1" -Json -RequireSpec

# Validate knowledge integration
python "C:\_Python\_Projects\__csf.nip\scripts\knowledge_interface.py" validate --spec_file "specification.md"
```

**Update Session State:**
- Mark Phase 2 as completed in `PHASE_STATE_FILE`
- Store specification document and TSK assignment details
- Document any quality issues identified for Phase 3 refinement

#### 3. Phase 3: Specification Refinement (OPTIONAL/CONDITIONAL)
**Commands**: `/speckit.clarify` and `/speckit.research` (as needed)

**Purpose**: Refine specification through targeted clarification and research to resolve ambiguities and knowledge gaps.

**Initialize Refinement Directory:**
```bash
mkdir -p "$PROJECT_DIR/$EVIDENCE_BASE_DIR/specification_refinement/"
```

##### 3.1 Requirements Clarification (If specification has gaps)
**Execute Clarification Command:**
```bash
cd "$PROJECT_DIR"
/speckit.clarify "focus:security,performance,user_experience, max_questions:5"
```

**When to Use Clarification:**
- Specification contains ambiguous or incomplete requirements
- Missing critical details for implementation planning
- Unclear user acceptance criteria or success metrics

##### 3.2 Technical Research (If technical unknowns exist)
**Execute Research Command:**
```bash
cd "$PROJECT_DIR"
/speckit.research "focus:technology_options, depth:thorough, decision_required:true"
```

**When to Use Research:**
- Multiple technology options need evaluation
- Architecture decisions require investigation
- Performance or security requirements need technical analysis

##### 3.3 Specification Integration
**Update Specification with Refinements:**
- Incorporate clarification answers into specification
- Integrate research findings and decisions
- Validate refined specification is complete and actionable

**Phase 3 Validation:**
- Verify all specification gaps addressed
- Confirm technical decisions documented
- Validate refined specification is ready for architecture planning

**Update Session State:**
- Mark Phase 3 as completed (if executed) or skipped (if not needed)
- Store refinement evidence and updated specification
- Document research findings and clarification outcomes

#### 4. Phase 4: TDD-Enhanced Architecture & Planning
**Commands**: `/speckit.plan` and `/speckit.tasks`

**Purpose**: Create technical architecture design with TDD integration and generate implementation tasks based on refined specification.

##### 4.1 Architecture Design with Test Planning
**Execute Planning Command:**
```bash
cd "$PROJECT_DIR"
/speckit.plan "focus:architecture, include:api_design, database_schema, tdd_strategy"
```

**TDD Integration Requirements:**
- Define test strategy for each architectural component
- Plan test pyramid structure (unit, integration, end-to-end)
- Identify test doubles and mocking requirements
- Define test data management approach
- Plan continuous testing integration

##### 4.2 Test-Driven Task Generation
**Execute Tasks Command with TDD Emphasis:**
```bash
cd "$PROJECT_DIR"
/speckit.tasks "parallel:true, include:testing, documentation, tdd_first:true"
```

**TDD Task Structure:**
- **Test-First Tasks**: Each implementation task paired with corresponding test task
- **Red-Green-Refactor Cycles**: Tasks organized into TDD iterations
- **Test Infrastructure Tasks**: Setup test frameworks and utilities first
- **Validation Gates**: Tasks include acceptance test definitions

##### 4.3 Architecture and Test Plan Validation
**Validate Planning Results:**
- Verify architecture document complete
- Confirm implementation plan detailed and actionable
- Validate task list created with dependencies and TDD structure
- Check resource requirements identified
- **NEW**: Verify TDD strategy is comprehensive and practical
- **NEW**: Validate test pyramid structure is appropriate for project complexity
- **NEW**: Confirm test infrastructure tasks are prioritized correctly

**Update Session State:**
- Mark Phase 4 as completed in `PHASE_STATE_FILE`
- Store architecture and task breakdown details

#### 5. Phase 5: Implementation
**Command**: `/speckit.implement`

1. **Determine Execution Strategy:**
   - Analyze project complexity and dependencies
   - **Simple projects:** Use sequential execution
   - **Complex projects:** Use concurrent agents (max 5)
   - **Very complex:** Use hybrid phased deployment

2. **Execute Implementation:**
   ```bash
   cd "$PROJECT_DIR"
   /speckit.implement "parallel:true, quality-gates:true, testing:comprehensive"
   ```

3. **Validate Implementation Results:**
   - Verify all tasks completed successfully
   - Check code quality gates passed (ruff, mypy, bandit, pip-audit)
   - Confirm security scan passed
   - Validate documentation generated
   - Ensure tests pass with adequate coverage

4. **Update Session State:**
   - Mark Phase 5 as completed in `PHASE_STATE_FILE`
   - Store implementation artifacts and quality reports

#### 6. Phase 6: Analysis & Validation
**Command**: PowerShell `check-prerequisites.ps1` script

1. **Execute Analysis Command:**
   ```bash
   cd "$PROJECT_DIR"
   # Cross-artifact analysis using PowerShell prerequisite checker
   powershell -ExecutionPolicy Bypass -File "C:\_Python\_Projects\.speckit\scripts\powershell\check-prerequisites.ps1" -Json -RequireTasks -IncludeTasks
   ```

2. **Validate Analysis Results:**
   - Verify cross-artifact consistency validated
   - Confirm all quality gates passed
   - Check security vulnerabilities resolved
   - Validate performance requirements met
   - Ensure documentation complete and verified

3. **Update Session State:**
   - Mark Phase 6 as completed in `PHASE_STATE_FILE`
   - Store validation reports and analysis results

#### 7. Phase 7: Final Verification & Completion
**Commands**: DUF6 verification, Knowledge contribution, Evidence archival

1. **Execute Final Verification:**
   ```bash
   cd "$PROJECT_DIR"
   # DUF6 independent verification
   python src/modules/verification/duf6/src/validate_implementation.py --project $PROJECT_ID --session-id $SESSION_ID

   # Knowledge contribution
   python src/modules/knowledge_system/contribute_patterns.py --project $PROJECT_ID --evidence-based --session-id $SESSION_ID

   # Evidence archival
   python src/modules/evidence/archive_project_evidence.py --project $PROJECT_ID --session-id $SESSION_ID
   ```

2. **Validate Completion:**
   - Verify independent verification passed
   - Confirm knowledge patterns contributed
   - Validate evidence properly archived
   - Check plan lifecycle updated to "completed"

3. **Update Session State:**
   - Mark Phase 7 as completed in `PHASE_STATE_FILE`
   - Store final verification and archival details

#### 8. Generate Completion Report
1. **Compile Evidence Package:**
   - Collect all phase evidence from `EVIDENCE_BASE_DIR`
   - Generate comprehensive completion report
   - Validate all success criteria met

2. **Report in Completion Format:**
   - Provide detailed summary of all phases completed
   - List all evidence collected and validated
   - Document any deviations or issues encountered
   - Confirm project completion status

### Error Handling & Recovery
   - Verify architecture document complete
   - Confirm implementation plan detailed and actionable
   - Validate task list created with dependencies
   - Check resource requirements identified

3. **Update Session State:**
   - Mark Phase 4 as completed in `PHASE_STATE_FILE`
   - Store architecture and task breakdown details

#### 8. Generate Completion Report
1. **Compile Evidence Package:**
   - Collect all phase evidence from `EVIDENCE_BASE_DIR`
   - Generate comprehensive completion report
   - Validate all success criteria met

2. **Report in Completion Format:**
   - Provide detailed summary of all phases completed
   - List all evidence collected and validated
   - Document any deviations or issues encountered
   - Confirm project completion status

### Error Handling & Recovery

#### Phase Failure Recovery Protocol
For any phase failure:
1. **Classify Error Type:**
   - **Retryable errors:** Resource conflicts, temporary failures
   - **Configuration errors:** Missing prerequisites, invalid parameters
   - **Critical errors:** Security issues, fundamental conflicts

2. **Apply Recovery Strategy:**
   - **Retryable:** Re-execute phase with exponential backoff (max `MAX_RETRY_ATTEMPTS`)
   - **Configuration:** Fix prerequisites and retry
   - **Critical:** Stop and escalate to user guidance

3. **Document Recovery:**
   - Log all retry attempts and outcomes
   - Document final resolution strategy
   - Update session state with recovery details

#### Fallback Mechanisms
- **Parallel → Sequential:** Reduce concurrent agents on resource conflicts
- **Comprehensive → Minimal:** Reduce validation scope on repeated failures
- **Auto → Manual:** Escalate to user decision on critical failures

### Report Format

## Speckit Flow Execution Report

**Session ID:** `<SESSION_ID>`
**Project ID:** `<PROJECT_ID>`
**Execution Date:** `<timestamp>`
**Total Duration:** `<total_time>`

### Phase Execution Summary
| Phase | Status | Duration | Evidence Collected | Issues Encountered |
|-------|--------|----------|-------------------|-------------------|
| Phase 1: Constitution Orchestration | ✅/❌ | `<duration>` | `<count>` artifacts | `<description>` |
| Phase 2: Request Analysis & Specification | ✅/❌ | `<duration>` | `<count>` artifacts | `<description>` |
| Phase 3: Specification Refinement | ✅/❌ | `<duration>` | `<count>` artifacts | `<description>` |
| Phase 4: Architecture & Planning | ✅/❌ | `<duration>` | `<count>` artifacts | `<description>` |
| Phase 5: Implementation | ✅/❌ | `<duration>` | `<count>` artifacts | `<description>` |
| Phase 6: Analysis & Validation | ✅/❌ | `<duration>` | `<count>` artifacts | `<description>` |
| Phase 7: Final Verification & Completion | ✅/❌ | `<duration>` | `<count>` artifacts | `<description>` |

### Success Metrics
- **Phase Completion Rate:** `<percentage>%` (target: 100%)
- **Quality Gate Pass Rate:** `<percentage>%` (target: ≥95%)
- **Security Compliance:** `<percentage>%` (target: 100%)
- **Evidence Completeness:** `<percentage>%` (target: 100%)

### Evidence Archive Location
`<PROJECT_DIR>/<EVIDENCE_BASE_DIR>/` containing:
- `constitution/` - Constitutional governance and principles
  - `constitution.md` - Project constitution document
  - `constitution_version.json` - Version tracking and audit results
  - `governance_evidence.json` - Constitutional compliance evidence
- `specification/` - Knowledge-guided specifications and TSK assignments
  - `specification.md` - Complete specification document
  - `knowledge_search_results.json` - Patterns found and integrated
  - `tsk_assignment.json` - TSK ID assignment and registration details
  - `quality_validation.json` - Initial specification quality check results
  - `knowledge_integration_report.json` - How organizational knowledge was applied
- `specification_refinement/` - Optional specification refinement evidence
  - `clarification_questions.json` - Questions asked and answers received
  - `research_findings.json` - Technical research results and decisions
  - `refined_specification.md` - Updated specification after refinement
- `architecture/` - TDD-enhanced architecture documentation and plans
  - `architecture.md` - System architecture design
  - `tdd_strategy.md` - Test-driven development strategy and test pyramid
  - `technology_decisions.json` - Technology choices and rationale
  - `integration_design.md` - Integration approach and patterns
  - `test_plan_validation.json` - TDD plan validation results
- `implementation/` - Code, tests, and implementation artifacts
  - `source_code/` - Implementation source code
  - `tests/` - Unit and integration tests
  - `documentation/` - Implementation documentation
  - `quality_reports.json` - Code quality and security scan results
- `analysis/` - Cross-artifact validation and analysis reports
  - `cross_artifact_analysis.json` - Consistency validation results
  - `quality_gates.json` - Quality gate validation outcomes
- `completion/` - Final verification and archival documentation
  - `final_verification.json` - Independent verification results
  - `completion_report.md` - Comprehensive completion summary
  - `evidence_package.tar.gz` - Compressed evidence archive

### Final Status
**Overall Result:** ✅ SUCCESS / ❌ FAILED / ⚠️ PARTIAL SUCCESS

**Completion Certificate:**
```
Project <PROJECT_ID> completed on <date>
All phases validated with <quality_score>% quality score
Evidence archived at <archive_path>
Session ID: <SESSION_ID>
```

**Next Steps:**
- [ ] Review completion report and evidence package
- [ ] Validate all deliverables meet requirements
- [ ] Archive project and update knowledge base
- [ ] Schedule post-completion review (if needed)
