# speckit.plan Configuration Guide

## Configuration Overview

speckit.plan uses a flexible configuration system that adapts to project complexity, development approach, and quality requirements. Configuration is handled through command-line parameters and automatic detection.

## Configuration Variables

### Core Variables

#### `project_complexity`
**Values**: `simple` | `moderate` | `complex` | `enterprise`
**Default**: `moderate`
**Description**: Overall project complexity affecting planning depth and validation requirements

**Behavior by Value**:
- `simple`: Basic architecture, minimal validation, quick completion focus
- `moderate`: Standard architecture planning, comprehensive validation
- `complex`: Multi-component architecture, extensive validation, risk assessment
- `enterprise`: Full enterprise planning, stakeholder coordination, compliance validation

#### `development_approach`
**Values**: `solo` | `team` | `hybrid` | `orchestration`
**Default**: `solo`
**Description**: Development team structure affecting planning approach and resource allocation

**Behavior by Value**:
- `solo`: Simplified architecture, individual constraints optimization, minimal dependencies
- `team`: Collaborative planning, role specialization, team coordination
- `hybrid`: Mixed approach with solo development but team coordination points
- `orchestration`: Multi-agent coordination, complex workflow management

#### `validation_level`
**Values**: `standard` | `comprehensive` | `mission_critical`
**Default**: `standard`
**Description**: Validation rigor affecting evidence requirements and quality gates

**Behavior by Value**:
- `standard`: Basic validation, evidence for major decisions, standard quality gates
- `comprehensive`: Extensive validation, evidence for all decisions, enhanced quality gates
- `mission_critical`: Maximum validation, comprehensive evidence requirements, full quality assurance

#### `integration_scope`
**Values**: `standalone` | `integrated` | `ecosystem`
**Default**: `integrated`
**Description**: System integration scope affecting interface planning and compatibility requirements

**Behavior by Value**:
- `standalone`: Minimal integration planning, self-contained system design
- `integrated`: Standard integration with existing systems, interface documentation
- `ecosystem`: Full ecosystem integration, extensive compatibility validation

#### `quality_gates`
**Values**: `basic` | `enhanced` | `full_csf_nip`
**Default**: `enhanced`
**Description**: Quality gate stringency affecting validation checkpoints and success criteria

**Behavior by Value**:
- `basic`: Essential validation, basic success criteria, minimal quality checks
- `enhanced`: Comprehensive validation, detailed success criteria, quality metrics
- `full_csf_nip`: Maximum validation, complete CSF NIP compliance, full quality assurance

## Technology Configuration

### Technology Stack Parameters

#### Technology Selection
```bash
# Single technology
/speckit.plan "tech:python"

# Multiple technologies
/speckit.plan "tech:python,react,postgresql"

# Technology with version
/speckit.plan "tech:python@3.11,nodejs@18"
```

#### Architecture Patterns
```bash
# Architectural style
/speckit.plan "architecture:microservices"

# Multiple architectural elements
/speckit.plan "architecture:microservices, event_driven, api_first"
```

#### Focus Areas
```bash
# Single focus
/speckit.plan "focus:security"

# Multiple focus areas
/speckit.plan "focus:security,performance,scalability"
```

### Database Configuration
```bash
# Database selection
/speckit.plan "database:postgresql"

# Database with configuration
/speckit.plan "database:postgresql,redis_cache"
```

### Deployment Configuration
```bash
# Deployment platform
/speckit.plan "deployment:docker"

# Deployment with environment
/speckit.plan "deployment:docker,aws_production"
```

## Template Configuration

### Template Types

#### Feature Development Template
```bash
/speckit.plan "template:feature-development"
```
**Use Cases**: New feature implementation, functionality enhancement
**Default Complexity**: moderate
**Validation Level**: standard

#### Bug Fix Template
```bash
/speckit.plan "template:bug-fix"
```
**Use Cases**: Bug resolution, issue fixing, regression prevention
**Default Complexity**: simple
**Validation Level**: standard

#### RCA Investigation Template
```bash
/speckit.plan "template:rca-investigation"
```
**Use Cases**: Root cause analysis, problem investigation, incident response
**Default Complexity**: moderate
**Validation Level**: comprehensive

#### Research Template
```bash
/speckit.plan "template:research"
```
**Use Cases**: Technology research, proof of concept, feasibility study
**Default Complexity**: moderate
**Validation Level**: comprehensive

#### Migration Template
```bash
/speckit.plan "template:migration"
```
**Use Cases**: System migration, technology upgrade, data migration
**Default Complexity**: complex
**Validation Level**: mission_critical

### Template Customization
```bash
# Template with complexity override
/speckit.plan "template:feature-development, complexity:complex"

# Template with validation override
/speckit.plan "template:bug-fix, validation:comprehensive"

# Template with focus areas
/speckit.plan "template:feature-development, focus:security,performance"
```

## Research Configuration

### Research Scope
```bash
# Basic research
/speckit.plan "research:existing_solutions"

# Comprehensive research
/speckit.plan "research:existing_solutions,best_practices,alternatives"

# Evidence-focused research
/speckit.plan "research:existing_solutions, evidence:required"
```

### Knowledge Integration
```bash
# Basic knowledge integration
/speckit.plan "knowledge:patterns"

# Full knowledge integration
/speckit.plan "knowledge:full-knowledge"

# Context7 integration
/speckit.plan "knowledge:context7"
```

### Evidence Requirements
```bash
# Recommended evidence
/speckit.plan "evidence:recommended"

# Required evidence
/speckit.plan "evidence:required"

# Optional evidence
/speckit.plan "evidence:optional"
```

## Advanced Configuration

### Auto-Detection Features
```bash
# Technology stack detection
/speckit.plan "auto-detect:tech-stack"

# Pattern detection
/speckit.plan "auto-detect:patterns"

# Integration detection
/speckit.plan "auto-detect:integrations"

# Comprehensive auto-detection
/speckit.plan "auto-detect:tech-stack,patterns,integrations"
```

### Code Discovery Configuration
```bash
# Comprehensive discovery
/speckit.plan "code-discovery:comprehensive"

# Targeted discovery
/speckit.plan "code-discovery:targeted"

# Patterns only discovery
/speckit.plan "code-discovery:patterns_only"
```

### Custom Validation Rules
```bash
# Custom validation level
/speckit.plan "validation:custom, validation_rules:custom_rules.json"

# Custom quality gates
/speckit.plan "quality_gates:custom, gates:project_specific_gates.json"
```

## Configuration Precedence

### Parameter Priority Order
1. **Explicit Command Parameters**: Highest priority
2. **Template Defaults**: Template-specific configuration
3. **Auto-Detection**: Automatically detected values
4. **System Defaults**: Fallback values

### Resolution Example
```bash
# Command: /speckit.plan "tech:python, template:feature-development, complexity:enterprise"

# Resolution:
# 1. tech:python (explicit) → Python
# 2. template:feature-development (explicit) → Feature template
# 3. complexity:enterprise (explicit) → Enterprise complexity
# 4. validation_level (inherited from template) → comprehensive
# 5. development_approach (system default) → solo
```

## Environment Configuration

### Project-Level Configuration
Create `.speckit/config/project_config.json`:
```json
{
  "default_complexity": "moderate",
  "default_validation": "standard",
  "preferred_technologies": ["python", "postgresql", "docker"],
  "quality_standards": "enhanced",
  "auto_research": true,
  "component_validation": true
}
```

### User-Level Configuration
Create `.speckit/config/user_config.json`:
```json
{
  "preferred_approach": "solo",
  "default_focus": ["maintainability", "performance"],
  "evidence_requirements": "recommended",
  "research_sources": ["knowledge_base", "existing_code"],
  "validation_preferences": "comprehensive"
}
```

### Organization-Level Configuration
Create `.speckit/config/org_config.json`:
```json
{
  "standards_compliance": "full_csf_nip",
  "required_validation": "mission_critical",
  "approved_technologies": ["python", "typescript", "postgresql"],
  "security_requirements": "comprehensive",
  "documentation_standards": "enhanced"
}
```

## Configuration Validation

### Validation Commands
```bash
# Validate current configuration
python .speckit/scripts/validate_plan_config.py

# Test specific configuration
python .speckit/scripts/test_plan_config.py --config "complexity:enterprise,validation:comprehensive"

# Check configuration compatibility
python .speckit/scripts/check_config_compatibility.py --template "feature-development"
```

### Configuration Errors
Common configuration issues and solutions:

**❌ Invalid complexity level**
```bash
# Error: "Invalid complexity level: 'very_complex'"
# Solution: Use valid values: simple, moderate, complex, enterprise
/speckit.plan "complexity:complex"
```

**❌ Conflicting parameters**
```bash
# Error: "Conflict: 'template:bug-fix' incompatible with 'complexity:enterprise'"
# Solution: Adjust complexity or choose appropriate template
/speckit.plan "template:feature-development, complexity:enterprise"
```

**❌ Missing required parameters**
```bash
# Error: "Mission critical validation requires evidence:required"
# Solution: Add evidence requirement
/speckit.plan "validation:mission_critical, evidence:required"
```

## Best Practices

### Configuration Guidelines
1. **Start Simple**: Begin with basic configuration, add complexity as needed
2. **Be Specific**: Use explicit parameters for critical requirements
3. **Validate Early**: Test configuration before full planning session
4. **Document Decisions**: Keep configuration rationale in project documentation
5. **Review Regularly**: Adjust configuration based on project evolution

### Performance Optimization
1. **Use Appropriate Complexity**: Avoid over-configuring simple projects
2. **Leverage Auto-Detection**: Let the system detect obvious patterns
3. **Cache Configuration**: Store validated configurations for reuse
4. **Parallel Processing**: Configure for concurrent validation when possible

### Quality Assurance
1. **Validate Configuration**: Always validate configuration before use
2. **Test Edge Cases**: Verify behavior with extreme parameter values
3. **Monitor Performance**: Track configuration impact on planning speed
4. **Gather Feedback**: Collect user experience data for configuration improvements

## Troubleshooting

### Common Configuration Issues

**Configuration Not Applied**
- Check parameter syntax and spelling
- Verify configuration file format (JSON)
- Ensure no conflicting parameters
- Validate parameter values against allowed options

**Auto-Detection Not Working**
- Verify project structure is correct
- Check file permissions for code access
- Ensure required tools are available
- Validate auto-detection parameters

**Template Overrides Ignored**
- Check template name spelling
- Verify template exists
- Ensure parameters are compatible with template
- Validate parameter format and syntax

**Validation Level Not Respected**
- Check validation level spelling
- Ensure validation requirements are met
- Verify evidence collection is working
- Check validation gate configuration
