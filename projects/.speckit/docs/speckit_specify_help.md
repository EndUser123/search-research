# Speckit Specify - Comprehensive Help Documentation

## Overview

The `/speckit.specify` command transforms feature descriptions into implementation-ready specifications with solo developer workflow automation. This document provides comprehensive help beyond the functional essentials needed for LLM execution.

## Command Syntax

```bash
/speckit.specify "feature description" [options]
```

### Required Arguments

- **feature description**: Natural language description of the feature to be specified

### Optional Parameters

| Parameter | Format | Description | Default |
|-----------|--------|-------------|---------|
| **implementation_focus** | `implementation_focus:true` | Include detailed implementation patterns and time estimates | `false` |
| **solo_dev** | `solo_dev:true` | Optimize scope for solo developer capacity and time constraints | `false` |
| **timebox** | `timebox:1week|2weeks|1month` | Set realistic time boundaries for solo development | `none` |
| **tech_stack** | `tech_stack:python,fastapi,postgres` | Include technology-specific implementation patterns | `auto-detected` |
| **complexity** | `complexity:simple|moderate|complex` | Solo developer implementation complexity level | `moderate` |
| **learning_mode** | `learning_mode:true` | Include learning resources and tutorials for new technologies | `false` |
| **automation_level** | `automation_level:basic|moderate|advanced` | Level of workflow automation patterns included | `moderate` |

## Detailed Examples

### Basic Feature Specification
```bash
/speckit.specify "User authentication system with social login"
```
Creates a standard specification with basic implementation guidance.

### Implementation-Focused Specification
```bash
/speckit.specify "E-commerce checkout process" "implementation_focus:true,solo_dev:true,timebox:2weeks"
```
Creates specification with detailed implementation patterns optimized for solo developer with 2-week timebox.

### Technology-Specific Specification
```bash
/speckit.specify "API gateway for microservices" "tech_stack:python,fastapi,docker,kubernetes,learning_mode:true"
```
Creates specification with Python/FastAPI patterns and learning resources for Docker/Kubernetes.

### Learning Project Specification
```bash
/speckit.specify "Real-time chat application" "learning_mode:true,tech_stack:websocket,redis,automation_level:basic"
```
Creates specification optimized for learning new technologies with basic automation.

## Advanced Configuration

### Custom Specification Templates
The command can use custom templates stored in `.speckit/templates/`:

```bash
# Use custom template
/speckit.specify "Feature" "template:custom-enterprise"

# Template locations
.speckit/templates/
├── spec-template.md              # Default template
├── enterprise-spec-template.md   # Enterprise-focused
├── mvp-spec-template.md          # MVP-focused
└── learning-spec-template.md     # Learning-focused
```

### Integration with Knowledge System

The command automatically integrates with CSF NIP knowledge system:

```bash
# Search for existing patterns before specification
python scripts/knowledge_interface.py search --query "authentication patterns"

# Store specification patterns for future use
python scripts/knowledge_interface.py store --type specification_pattern --evidence [evidence]
```

## Output Structure

Generated specifications follow this structure:

```markdown
# Implementation-Ready Specification: [Feature Name]

## Implementation Summary
Quick overview and immediate coding guidance.

## Core User Journey (Must Have)
User story with acceptance criteria and implementation start point.

## Additional Features (Should Have)
Feature descriptions with implementation hints.

## Future Enhancements (Could Have)
Feature descriptions for future iterations.

## Implementation Guidance
### Technical Approach
Recommended approach with potential challenges and learning resources.

### Solo Developer Estimates
Time estimates for core features, additional features, and testing.

### Prerequisites
Required libraries, knowledge requirements, and setup needs.

## Quality Checkpoints
Essential validation steps for successful implementation.

## Related Patterns
Implementation patterns from T017-T019 and CSF NIP knowledge base.
```

## Troubleshooting Guide

### Common Issues and Solutions

#### Specification Generation Fails

**Issue**: "Template not found"
```bash
# Solution: Check template availability
cd "C:\_Python\_Projects\.speckit"
ls templates/spec-template.md
# If missing, recreate template
speckit --init-templates
```

**Issue**: "Constitution not found"
```bash
# Solution: Create project constitution
/speckit.constitution create
# Or provide path to existing constitution
/speckit.constitution import --path /path/to/constitution.md
```

#### Quality Issues

**Issue**: "Specification too complex for solo implementation"
- **Symptoms**: Too many features, unrealistic time estimates
- **Solutions**:
  - Apply MoSCoW prioritization (Must, Should, Could, Won't)
  - Use `solo_dev:true` parameter for automatic scope optimization
  - Set realistic `timebox` parameter
  - Focus on core user journey first

**Issue**: "Implementation guidance too generic"
- **Symptoms**: Vague technical approach, no specific patterns
- **Solutions**:
  - Use `tech_stack` parameter for technology-specific patterns
  - Set `implementation_focus:true` for detailed guidance
  - Include `learning_mode:true` for new technology learning resources
  - Set higher `automation_level` for workflow automation patterns

#### Integration Issues

**Issue**: "Knowledge system integration failed"
```bash
# Solution: Check CSF NIP knowledge system status
cd "C:\_Python\_Projects\__csf.nip"
python scripts/knowledge_interface.py stats
python scripts/knowledge_interface.py health-check

# Fix common issues
python scripts/knowledge_interface.py rebuild-index
```

**Issue**: "System Discovery Protocol failed"
```bash
# Solution: Check discovery engine status
cd "C:\_Python\_Projects\__csf.nip"
python src/modules/orchestration/discovery_engine.py --help
python src/modules/orchestration/discovery_engine.py health-check

# Run discovery manually
python src/modules/orchestration/discovery_engine.py discover --project test-project
```

### Performance Issues

**Issue**: "Specification generation taking too long"
- **Causes**: Large knowledge base, slow discovery protocol
- **Solutions**:
  - Use focused search queries in knowledge system
  - Limit discovery scope with specific project boundaries
  - Cache frequently used patterns locally

**Issue**: "Memory usage too high during generation"
- **Causes**: Large templates, extensive knowledge system queries
- **Solutions**:
  - Use simplified templates for large features
  - Batch knowledge system queries
  - Implement result streaming for large specifications

## Advanced Workflows

### Multi-Feature Project Specification

```bash
# Specify related features together
/speckit.specify "User authentication and authorization" "tech_stack:python,fastapi,jwt"
speckit.specify "User profile management" "tech_stack:python,fastapi,s3" "depends:authentication"
speckit.specify "User dashboard" "tech_stack:react,typescript" "depends:authentication,profile"
```

### Learning Project Workflow

```bash
# Step 1: Create learning-focused specification
/speckit.specify "Real-time notifications" "learning_mode:true,tech_stack:websocket,redis"

# Step 2: Generate learning resources
speckit.research "websocket tutorials and best practices"

# Step 3: Create implementation plan
/speckit.plan "Real-time notifications" "learning_resources:true"

# Step 4: Generate tasks with learning checkpoints
speckit.tasks "Real-time notifications" "include:learning_checkpoints"
```

### Enterprise Feature Specification

```bash
# Use enterprise template with compliance requirements
/speckit.specify "Patient data management system" \
  "template:enterprise" \
  "compliance:hipaa" \
  "security:high" \
  "tech_stack:python,django,postgresql" \
  "implementation_focus:true"
```

## Best Practices

### Before Running Specification

1. **Clear Feature Description**: Have a clear, concise feature description ready
2. **Technology Context**: Know your tech stack or be ready to specify it
3. **Time Constraints**: Understand your time limitations (use timebox parameter)
4. **Learning Requirements**: Identify if you need learning resources

### During Specification Generation

1. **Review Generated Specification**: Check for completeness and accuracy
2. **Validate Time Estimates**: Ensure estimates are realistic for your capacity
3. **Check Implementation Guidance**: Verify technical approach is suitable
4. **Test Prerequisites**: Ensure you can meet all listed prerequisites

### After Specification Generation

1. **Store in Knowledge System**: Save successful patterns for future use
2. **Update Templates**: Improve templates based on results
3. **Track Time Estimates**: Compare estimates vs actual time for future accuracy
4. **Document Lessons Learned**: Record what worked and what didn't

## Integration with Other Commands

### Typical Workflow Sequence

```bash
# 1. Generate specification
/speckit.specify "Feature description" "implementation_focus:true"

# 2. Conduct technical research if needed
speckit.research "Technology options for feature"

# 3. Create architectural plan
/speckit.plan "Feature description" "tech_stack:python,fastapi"

# 4. Generate implementation tasks
speckit.tasks "Feature description" "include:testing,documentation"

# 5. Execute implementation
/speckit.implement "Feature description"
```

### Command Dependencies

- **speckit.research**: Use when feature requires technical investigation
- **speckit.plan**: Use after specification for architectural planning
- **speckit.tasks**: Use after planning for task breakdown
- **speckit.implement**: Use after tasks for implementation execution
- **speckit.analyze**: Use to validate specification quality and consistency

## Customization and Extensions

### Creating Custom Templates

Create custom specification templates in `.speckit/templates/`:

```markdown
---
template_type: "custom"
target_audience: "solo_developer"
focus_area: "mvp_development"
---

# Custom Specification Template: [Feature Name]

## MVP Implementation Focus
[Custom MVP-focused sections]

## Rapid Development Patterns
[Custom rapid development guidance]

## Timeboxing Guidelines
[Custom timeboxing recommendations]
```

### Extending Command Functionality

The command can be extended through:

1. **Custom Template Variables**: Add new variables for template substitution
2. **Additional Validation Rules**: Add domain-specific validation
3. **Enhanced Knowledge Integration**: Add specialized knowledge sources
4. **Custom Report Formats**: Add specialized output formats

## FAQ

### Q: Can I specify multiple features at once?
A: No, specify one feature at a time for best results. Use separate commands for related features.

### Q: How accurate are the time estimates?
A: Estimates are based on solo developer project data and improve with use. Track actual vs estimated time for better future accuracy.

### Q: Can I modify generated specifications?
A: Yes, specifications are editable markdown files. The command provides a solid foundation that you can customize.

### Q: What if I need help with a generated specification?
A: Use `/speckit.analyze` to validate specification quality, or consult the troubleshooting guide above.

### Q: How do I share specifications with team members?
A: Specifications are saved as markdown files in `.speckit/specs/` and can be shared through version control or direct file sharing.
