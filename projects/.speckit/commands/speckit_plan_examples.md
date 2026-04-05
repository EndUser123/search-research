# speckit.plan Examples and Use Cases

## Basic Examples

### Simple Feature Development
```bash
/speckit.plan "tech:python, database:sqlite, template:feature-development"
```
**Output**: Implementation plan for Python feature with SQLite database, following solo developer optimization principles.

### Microservices Architecture
```bash
/speckit.plan "architecture:microservices, focus:scalability, tech:docker"
```
**Output**: Microservices design with Docker deployment, scalability focus, and comprehensive integration planning.

### Security-Focused Planning
```bash
/speckit.plan "focus:security, validation:comprehensive, include:threat_model"
```
**Output**: Security-first implementation plan with threat modeling, authentication strategies, and compliance validation.

### Research-Informed Planning
```bash
/speckit.plan "research:existing_solutions, evidence:required, template:feature-development"
```
**Output**: Evidence-based plan leveraging existing components and patterns, with comprehensive research documentation.

## Advanced Examples

### Enterprise-Level Integration
```bash
/speckit.plan "complexity:enterprise, development_approach:team, validation:mission_critical"
```
**Output**: Enterprise-grade plan with team coordination, comprehensive validation, and detailed risk assessment.

### API-First Development
```bash
/speckit.plan "focus:api_design, include:database_schema, validation:comprehensive"
```
**Output**: API-centric implementation with database design, contract specifications, and integration planning.

### Performance Optimization
```bash
/speckit.plan "focus:performance, architecture:serverless, tech:python, validation:comprehensive"
```
**Output**: Performance-optimized serverless architecture with comprehensive performance validation and monitoring.

## Template-Specific Examples

### Bug Fix Template
```bash
/speckit.plan "template:bug-fix, research:existing_patterns, validation:standard"
```
**Output**: Bug fix implementation plan with root cause analysis, testing strategy, and regression prevention.

### Research Investigation Template
```bash
/speckit.plan "template:rca-investigation, include:evidence_collection, validation:comprehensive"
```
**Output**: Root cause analysis plan with evidence collection, investigation framework, and reporting structure.

### Migration Template
```bash
/speckit.plan "template:migration, include:data_migration, validation:mission_critical"
```
**Output**: System migration plan with data migration strategy, rollback procedures, and comprehensive validation.

## Technology Stack Examples

### Full-Stack Web Application
```bash
/speckit.plan "tech:react, nodejs, postgresql, deployment:aws, architecture:spa"
```
**Output**: Complete full-stack implementation plan with React frontend, Node.js backend, PostgreSQL database, and AWS deployment.

### Data Processing Pipeline
```bash
/speckit.plan "tech:python, pandas, redis, focus:performance, architecture:batch_processing"
```
**Output**: Data processing pipeline with performance optimization, batch processing architecture, and comprehensive monitoring.

### Mobile Application Backend
```bash
/speckit.plan "tech:python, fastapi, postgresql, deployment:docker, focus:api_design"
```
**Output**: Mobile backend API with FastAPI, PostgreSQL database, Docker deployment, and comprehensive API documentation.

## Solo Developer Optimization Examples

### Quick Implementation
```bash
/speckit.plan "complexity:simple, development_approach:solo, focus:quick_completion"
```
**Output**: Simplified implementation plan optimized for solo developer with quick completion focus and minimal complexity.

### Maintainable Architecture
```bash
/speckit.plan "development_approach:solo, focus:maintainability, validation:standard"
```
**Output**: Maintainable architecture designed for solo developer with standard validation and long-term maintenance considerations.

### Learning-Focused Development
```bash
/speckit.plan "tech:python, development_approach:solo, include:learning_resources, validation:comprehensive"
```
**Output**: Learning-focused implementation plan with educational resources, comprehensive validation, and skill development opportunities.

## Integration Examples

### CSF NIP System Integration
```bash
/speckit.plan "integration_scope:ecosystem, include:csf_nip_integration, validation:comprehensive"
```
**Output**: Comprehensive integration plan with CSF NIP ecosystem, existing system compatibility, and detailed integration testing.

### Multi-System Coordination
```bash
/speckit.plan "integration_scope:integrated, include:system_coordination, development_approach:orchestration"
```
**Output**: Multi-system coordination plan with orchestration approach, integration patterns, and comprehensive system management.

## Output Structure Examples

### Generated Plan Structure
Each plan includes:
- **Architecture Overview**: System design with component validation
- **Technology Stack**: Evidence-based technology choices
- **Implementation Strategy**: Phased development with risk mitigation
- **Integration Planning**: System interfaces and data flow
- **Quality Gates**: Validation checkpoints and success criteria
- **Resource Requirements**: Tools, timeline, and expertise needs

### Example Output Snippet
```markdown
## Planning Summary
- **Project Scope**: User authentication system with OAuth integration
- **Complexity Assessment**: moderate
- **Architecture Decision**: Microservices with separate auth and user services
- **TSK Integration**: T001, T002, T003 applied

### Task Breakdown
1. **High** Database Schema Design - 4 hours
   - Acceptance Criteria: User and auth tables with proper indexing
   - Dependencies: Technology stack validation
   - Validation Gate: Schema performance testing
```

## Best Practice Examples

### Evidence-Based Planning
```bash
/speckit.plan "research:existing_solutions, evidence:required, validation:comprehensive"
```
**Key Features**:
- Component existence validation before planning
- Evidence collection for all architectural decisions
- Research documentation with specific references
- Risk mitigation based on existing patterns

### TSK-010 Integration
```bash
/speckit.plan "template:feature-development, knowledge:full-knowledge, validation:comprehensive"
```
**Key Features**:
- Template engine integration (T001)
- Knowledge system patterns (T003)
- Validation framework (T002)
- Flow orchestrator coordination (T009-T012)

### Solo Developer Focus
```bash
/speckit.plan "development_approach:solo, complexity:simple, focus:quick_completion"
```
**Key Features**:
- Simplified architecture for single developer
- Quick completion optimization
- Maintainable code structure
- Minimal external dependencies

## Common Use Case Patterns

### New Feature Development
- Start with `/speckit.specify` for requirements
- Use `/speckit.clarify` if requirements need refinement
- Apply `/speckit.plan` with appropriate template
- Execute `/speckit.tasks` for implementation

### System Enhancement
- Research existing components first
- Validate component existence and capabilities
- Plan integration with existing architecture
- Focus on minimal disruption and maintainability

### Problem Investigation
- Use RCA investigation template
- Include evidence collection framework
- Plan systematic analysis approach
- Document findings and recommendations

### Technology Migration
- Comprehensive research of existing patterns
- Detailed migration strategy with rollback
- Extensive validation and testing
- Risk mitigation and contingency planning

## Command Combinations

### Research-First Workflow
```bash
# Step 1: Research existing solutions
/speckit.research "authentication patterns in current codebase"

# Step 2: Plan based on research findings
/speckit.plan "research:existing_solutions, evidence:required, template:feature-development"
```

### Quality-Focused Workflow
```bash
# Step 1: High-quality specification
/speckit.specify "detailed feature requirements"

# Step 2: Comprehensive clarification
/speckit.clarify "validate requirements and identify gaps"

# Step 3: Mission-critical planning
/speckit.plan "validation:mission_critical, evidence:required, complexity:complex"
```

### Rapid Development Workflow
```bash
# Step 1: Quick specification
/speckit.specify "basic feature outline"

# Step 2: Simplified planning
/speckit.plan "complexity:simple, development_approach:solo, focus:quick_completion"
```
