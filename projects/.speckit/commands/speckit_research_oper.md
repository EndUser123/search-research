---
name: "/speckit.research"
category: "Speckit Workflow"
purpose: "Run a focused research pass on the active feature to resolve unknowns and record architecture decisions before planning"
entry_point: "primary"
---

# Speckit Research - Technical Investigation and Analysis

Conduct focused research to resolve unknowns, evaluate options, and record architecture decisions before planning. This command gathers evidence, analyzes alternatives, and produces structured research findings that inform the planning phase.

## 🚀 Quick Start

### Conduct Basic Research
```bash
/speckit.research
```

### Research Specific Technology Area
```bash
/speckit.research "focus:database, options:postgresql_mysql_mongodb"
```

### Research Security Requirements
```bash
/speckit.research "focus:security, compliance:gdpr, depth:thorough"
```

### Research Performance Requirements
```bash
/speckit.research "focus:performance, requirements:low_latency_high_throughput"
```

## ⚙️ Command Options

Research accepts various parameters for investigation scope:

| Parameter | Values | Description |
|-----------|--------|-------------|
| **Focus Areas** | `database`, `security`, `performance`, `ui`, `api`, `deployment` | Primary research domains |
| **Technology Options** | Comma-separated list | Specific technologies to evaluate |
| **Compliance** | `gdpr`, `hipaa`, `pci`, `soc2` | Regulatory compliance research |
| **Depth Level** | `basic`, `thorough`, `comprehensive` | Research detail level |
| **Sources** | `internal`, `external`, `both` | Research source preferences |
| **Decision Required** | `true`, `false` | Require final decision recommendation |

## 📋 Use Cases

### When to Use /speckit.research

- **Technical Uncertainty**: When specification contains technical unknowns
- **Technology Selection**: When multiple technology options need evaluation
- **Compliance Requirements**: When regulatory compliance needs investigation
- **Performance Requirements**: When performance characteristics need research
- **Architecture Decisions**: When design decisions require evidence-based analysis
- **Risk Assessment**: When implementation risks need investigation and mitigation

### When NOT to Use /speckit.research

- **Requirements Definition**: Use `/speckit.specify` for specification creation
- **Implementation Planning**: Use `/speckit.plan` for design and architecture
- **Task Execution**: Use `/speckit.implement` for implementation work

## 🔧 Prerequisites

### Required Context
1. **Feature Specification**: `spec.md` with requirements and unknowns
2. **Plan TSK Context**: Parent plan with TSK-### identifier for research organization
3. **Research Targets**: Identified areas requiring investigation
4. **Project Constitution**: Located at `.speckit/memory/constitution.md`
5. **Plan Directory**: Valid speckit plan directory structure under `.speckit/specs/TSK-###-plan-name/`

### Multi-Project Research Coordination
Research activities must coordinate with multi-project infrastructure:
- **Plan-Level Context**: Research belongs to a parent TSK-### plan
- **Cross-Plan Research**: Research may impact or depend on other plans
- **Evidence Sharing**: Research findings shared across dependent plans
- **Dependency Research**: Research into cross-plan dependencies and integrations

### CSF NIP Research Standards Integration
All research activities follow established CSF NIP standards:
- **Evidence-Based Research Protocol**: All conclusions supported by specific evidence
- **Knowledge System Integration**: Research findings added to CSF NIP Knowledge System
- **Documentation Standards**: Structured research documentation with clear evidence trails
- **Quality Validation**: Research validated through systematic peer review processes
- **Lib-First Research**: Check existing knowledge base before conducting new research

### Validation Commands
```bash
# Verify plan context and TSK assignment
cd "C:\_Python\_Projects\.speckit"
ls -la specs/ | grep "TSK-"
cd specs/TSK-XXX-plan-name
ls -la | grep -E "(spec\.md)"

# Verify specification exists with research needs
grep -i "needs clarification\|unknown\|research" spec.md

# Check cross-plan research requirements
cd "C:\_Python\_Projects\.speckit"
cat registry/tsk_registry.json | jq '.[] | select(.dependencies != null) | .tsk_id'

# Check project constitution for constraints
cat .speckit/memory/constitution.md

# Verify research directory exists in plan context
mkdir -p evidence/research
```

## 🔧 Troubleshooting

### Common Issues and Solutions

**❌ "No research targets identified"**
```bash
# Solution: Check specification for unclear areas
grep -i "tk\|todo\|needs\|unclear" /path/to/feature/spec.md
# Add specific research needs to specification
```

**❌ "Insufficient research sources"**
```bash
# Solution: Expand research scope
/speckit.research "sources:external, depth:comprehensive"
```

**❌ "Cannot reach decision on technology choice"**
```bash
# Solution: Focus on specific criteria
/speckit.research "focus:database, criteria:performance_cost_maintainability"
```

**❌ "Research conflicts with constitution"**
```bash
# Solution: Review constitution constraints
cat .speckit/memory/constitution.md
# Adjust research approach to comply with constitution
```

### Research Quality Issues

**Inadequate Evidence**
- Gather more comprehensive data and examples
- Include real-world case studies and performance data

**Biased Analysis**
- Consider multiple perspectives and options
- Include pros and cons for each alternative

**Missing Implementation Considerations**
- Research practical implementation challenges
- Include maintenance and operational considerations

## 🧠 Complete Operational Logic

The research process follows this systematic methodology:

### 1. Research Target Identification
Extract research requirements from specification:
- **Unknown Areas**: Identify `[NEEDS CLARIFICATION]` markers and ambiguous terms
- **Technology Decisions**: Extract explicit technology choices and alternatives
- **Dependencies**: Identify external integrations and dependencies
- **Constraints**: Extract performance, security, and compliance requirements
- **User Input**: Incorporate specific research themes from user arguments

### 2. Research Planning and Prioritization
Plan research approach based on impact and urgency:
- **High Priority**: Constitution compliance, critical path decisions
- **Medium Priority**: Technology selection, performance optimization
- **Low Priority**: Nice-to-have features, optimization opportunities
- **Research Queue**: Order research targets by dependency and impact

### 3. Evidence Gathering and Analysis
Execute systematic research across multiple sources:
- **Internal Evidence**: Search repository for reusable patterns and prior decisions
- **Knowledge Base**: Query organizational knowledge base for relevant experience
- **External Research**: Investigate best practices, case studies, and technical documentation
- **Expert Consultation**: Gather insights from domain experts when needed

### 4. Alternative Evaluation and Comparison
Analyze research findings systematically:
- **Option Identification**: List viable alternatives for each research target
- **Criteria Definition**: Establish evaluation criteria relevant to decision
- **Comparative Analysis**: Compare alternatives against defined criteria
- **Risk Assessment**: Identify risks and mitigation strategies for each option

### 5. Decision Making and Documentation
Make evidence-based decisions with comprehensive documentation:
- **Decision Rationale**: Document reasoning behind final choices
- **Supporting Evidence**: Include specific evidence supporting decisions
- **Alternatives Considered**: Document rejected options and reasoning
- **Residual Risks**: Identify remaining risks and follow-up requirements

### 6. Cross-Plan Research Coordination
Coordinate research activities with other plans:
- **Dependency Research**: Research dependencies on other TSK-### plans
- **Impact Analysis**: Assess research impact on dependent plans
- **Evidence Sharing**: Share research findings with relevant stakeholders
- **Coordination Planning**: Plan research coordination across multiple plans

### 7. Constitution Alignment and Validation
Ensure research decisions align with project constraints:
- **Compliance Validation**: Check decisions against regulatory requirements
- **Constitution Compliance**: Ensure alignment with project principles
- **Constraint Validation**: Verify decisions satisfy technical and business constraints
- **Risk Mitigation**: Document how identified risks will be addressed

## 📝 Research Documentation Structure

```markdown
# Research Log: TSK-[PLAN-ID] - [Plan Name]

## Summary
- **Date**: YYYY-MM-DD
- **Prepared by**: [Researcher/Agent]
- **Plan Context**: TSK-XXX - [Plan Name]
- **Research Focus**: [Primary research areas]

## Findings

### Database Technology Selection
**Decision**: PostgreSQL
**Evidence**:
- ACID compliance required for data integrity
- Strong JSON support for flexible schema
- Proven scalability for read-heavy workloads
- Extensive community support and documentation

**Alternatives Considered**:
- MySQL: Good performance, less flexible schema
- MongoDB: Excellent flexibility, weaker consistency guarantees

**Cross-Plan Impact**:
- Affects TSK-YYY (data migration plan)
- Coordinates with TSK-ZZZ (API development plan)

**Residual Risks**:
- Migration complexity if requirements change significantly
- Performance optimization may require specialized expertise

### Authentication Strategy
**Decision**: JWT-based authentication with refresh tokens
**Evidence**:
- Stateless architecture supports microservices
- Well-established security patterns
- Good library support across platforms
- Scales well for distributed systems

**Cross-Plan Dependencies**:
- Depends on TSK-AAA (security standards plan)
- Impacts TSK-BBB (user management plan)

**Residual Risks**:
- Token revocation complexity
- Refresh token management overhead

## Cross-Plan Research Coordination
### Shared Research Findings
- **Database Pattern**: Shared with TSK-YYY, TSK-ZZZ
- **Security Standards**: Aligned with TSK-AAA
- **Authentication Flow**: Coordinated with TSK-BBB

### Dependency Research Status
- **TSK-YYY**: Research complete, findings shared ✅
- **TSK-ZZZ**: Research in progress, coordination ongoing 🔄
- **TSK-AAA**: Research pending, blocked by this plan ⏳

## Unresolved Questions
- [Question] → [Why unresolved, who owns follow-up]

## Recommendations
- Proceed with PostgreSQL and JWT authentication architecture
- Conduct proof-of-concept for high-risk integration points
- Schedule specialist consultation for performance optimization
- Share research findings with dependent plans
- Coordinate research timeline with TSK-ZZZ and TSK-AAA
```

## 📊 Research Categories and Examples

### Technology Selection Research
- **Database Evaluation**: PostgreSQL vs MySQL vs MongoDB based on consistency requirements
- **Framework Selection**: React vs Vue vs Angular based on team expertise and requirements
- **Infrastructure Choices**: AWS vs Azure vs GCP based on cost and feature requirements

### Compliance Research
- **GDPR Compliance**: Data protection requirements and implementation strategies
- **Security Standards**: OWASP Top 10 compliance and security best practices
- **Accessibility Requirements**: WCAG compliance and implementation guidelines

### Performance Research
- **Scalability Patterns**: Microservices vs monolith based on growth projections
- **Caching Strategies**: Redis vs Memcached based on data access patterns
- **CDN Selection**: CloudFlare vs AWS CloudFront based on geographic requirements

### Integration Research
- **API Design**: REST vs GraphQL based on client requirements
- **Authentication Methods**: OAuth 2.0 vs JWT based on security requirements
- **Payment Processing**: Stripe vs PayPal based on feature and cost requirements

## 🚨 Critical Constraints

**Evidence-Based Decisions**: All research conclusions must be supported by specific evidence

**Constitution Compliance**: Research decisions must comply with project constitution principles

**Risk Awareness**: Must identify and document risks associated with decisions

**Practical Implementation**: Research must consider practical implementation challenges

**Completeness**: Must address all identified research targets and unknowns

**Documentation Quality**: Research findings must be clearly documented and accessible

**Decision Quality**: Must provide clear recommendations with supporting rationale

## 📁 File Management

**Location**: `.speckit/specs/TSK-###-plan-name/research.md`

**Evidence Collection**: Research evidence stored in `evidence/research/` subdirectory

**Incremental Updates**: New research sessions append to existing findings

**Version Control**: Track research evolution and decision changes

**Integration**: Research findings integrate with `/speckit.plan` for architecture decisions

**Cross-Plan Sharing**: Research findings shared with dependent and dependent plans

**Plan Context**: Research linked to parent TSK-### plan in registry

## 🔗 Related Commands

- **Before**: `/speckit.specify` (specification with research needs)
- **After**: `/speckit.plan` (architecture and design decisions)
- **Quality Gate**: `/speckit.analyze` (validate artifact consistency)
- **Optional**: `/speckit.clarify` (resolve remaining ambiguities)
