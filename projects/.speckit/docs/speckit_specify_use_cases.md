# Speckit Specify - Use Cases and Workflow Integration

## Overview

This document provides detailed workflow integration and decision guidance for the `/speckit.specify` command. It helps you understand when and how to use the command effectively within your development workflow.

## Decision Framework

### When to Use /speckit.specify

Use `/speckit.specify` when you need to:

**✅ Quick Feature Validation**
- Test if a feature idea is ready for implementation
- Validate scope against solo developer capacity
- Get initial time and complexity estimates

**✅ Implementation Planning**
- Create specifications that lead directly to coding
- Bridge requirements gap between ideas and implementation
- Establish clear success criteria

**✅ Scope Management**
- Define realistic scope for solo developer constraints
- Apply MoSCoW prioritization (Must, Should, Could, Won't)
- Set time boundaries with timebox parameter

**✅ Learning Projects**
- Create specs that include learning resources and tutorials
- Document learning journey and milestones
- Integrate new technology patterns

**✅ Team Collaboration**
- Create shared understanding of feature requirements
- Document decisions and rationale
- Provide baseline for technical discussions

### When NOT to Use /speckit.specify

**❌ Deep Technical Research**
→ Use `/speckit.research` for investigation and analysis
→ Research technology options, compare alternatives
→ Investigate complex technical challenges

**❌ Architecture Planning**
→ Use `/speckit.plan` for detailed technical design
→ Create system architecture diagrams
→ Design component interactions and data flow

**❌ Task Breakdown**
→ Use `/speckit.tasks` for implementation task creation
→ Generate dependency-ordered task lists
→ Create testing and documentation tasks

**❌ Simple Documentation**
→ Use standard markdown files for basic documentation
→ Create README files or simple guides
→ Document existing functionality

## Workflow Integration Patterns

### Pattern 1: Standard Feature Development

```bash
# Phase 1: Feature Specification
/speckit.specify "User authentication system" "implementation_focus:true,solo_dev:true"

# Phase 2: Technical Research (if needed)
speckit.research "Authentication best practices and security considerations"

# Phase 3: Architecture Planning
speckit.plan "User authentication system" "tech_stack:python,fastapi,jwt"

# Phase 4: Task Breakdown
speckit.tasks "User authentication system" "include:testing,documentation"

# Phase 5: Implementation
/speckit.implement "User authentication system"
```

**When to Use**: Standard new feature development with clear requirements
**Time Investment**: 2-4 hours for complete workflow
**Key Benefits**: Comprehensive approach with all phases covered

### Pattern 2: Rapid MVP Development

```bash
# Phase 1: MVP Specification (time-constrained)
/speckit.specify "Basic user profile management" "solo_dev:true,timebox:1week,complexity:simple"

# Phase 2: Quick Architecture
speckit.plan "User profile management" "focus:mvp,minimal_viable"

# Phase 3: Essential Tasks Only
speckit.tasks "User profile management" "focus:core_functionality,exclude:advanced_features"

# Phase 4: Focused Implementation
/speckit.implement "User profile management" "mvp_mode:true"
```

**When to Use**: Quick MVP with tight time constraints
**Time Investment**: 4-6 hours total
**Key Benefits**: Fast delivery with essential functionality only

### Pattern 3: Learning-Oriented Development

```bash
# Phase 1: Learning-Focused Specification
/speckit.specify "Real-time notifications" "learning_mode:true,tech_stack:websocket,redis"

# Phase 2: Learning Research
speckit.research "WebSocket tutorials and Redis best practices"

# Phase 3: Educational Architecture
speckit.plan "Real-time notifications" "learning_resources:true,include:tutorials"

# Phase 4: Learning Tasks
speckit.tasks "Real-time notifications" "include:learning_checkpoints,tutorials"

# Phase 5: Educational Implementation
/speckit.implement "Real-time notifications" "learning_mode:true"
```

**When to Use**: Learning new technologies while building features
**Time Investment**: 8-12 hours (including learning)
**Key Benefits**: Build skills while delivering value

### Pattern 4: Legacy System Integration

```bash
# Phase 1: Integration Specification
/speckit.specify "Payment gateway integration with existing system" "tech_stack:existing_tech,payment_api"

# Phase 2: System Analysis
speckit.research "Legacy system architecture and integration points"

# Phase 3: Integration Architecture
speckit.plan "Payment gateway integration" "existing_system:true,integration_patterns"

# Phase 4: Integration Tasks
speckit.tasks "Payment gateway integration" "focus:backward_compatibility,testing"

# Phase 5: Careful Implementation
speckit.implement "Payment gateway integration" "legacy_mode:true"
```

**When to Use**: Integrating with existing systems
**Time Investment**: 6-10 hours
**Key Benefits**: Safe integration with minimal disruption

## Context-Specific Guidelines

### Solo Developer Context

**Time Management**
```bash
# Always use solo_dev optimization
/speckit.specify "Feature" "solo_dev:true"

# Set realistic timeboxes
/speckit.specify "Feature" "timebox:2weeks,complexity:moderate"

# Focus on core functionality first
/speckit.specify "Feature" "implementation_focus:true"
```

**Scope Management**
- Start with Must requirements only
- Add Should requirements in iterations
- Skip Could requirements initially
- Use timebox to prevent scope creep

**Quality vs Speed Trade-offs**
```bash
# Quick delivery (sacrifice some quality)
/speckit.specify "Feature" "automation_level:basic,complexity:simple"

# Balanced approach (recommended)
/speckit.specify "Feature" "automation_level:moderate,complexity:moderate"

# High quality (slower delivery)
/speckit.specify "Feature" "automation_level:advanced,complexity:complex"
```

### Team Context

**Collaboration Specifications**
```bash
# Create specifications for team review
/speckit.specify "Feature" "include:team_review,decision_rationale"

# Share knowledge across team
/speckit.specify "Feature" "knowledge_integration:true"
```

**Consistency Requirements**
- Use standard templates across team
- Maintain consistent format and structure
- Document team-specific conventions
- Create shared knowledge base

### Enterprise Context

**Compliance Requirements**
```bash
# Include compliance considerations
/speckit.specify "Feature" "compliance:gdpr,security:high"

# Use enterprise templates
/speckit.specify "Feature" "template:enterprise"
```

**Documentation Standards**
- Maintain comprehensive audit trails
- Document all decisions and rationale
- Include stakeholder requirements
- Follow enterprise documentation guidelines

## Technology-Specific Workflows

### Web Application Development

```bash
# Frontend-focused specification
/speckit.specify "React dashboard" "tech_stack:react,typescript,automation_level:advanced"

# Backend-focused specification
/speckit.specify "API endpoints" "tech_stack:python,fastapi,postgres,implementation_focus:true"

# Full-stack specification
/speckit.specify "E-commerce site" "tech_stack:react,python,fastapi,postgresql,learning_mode:true"
```

### Data Processing Systems

```bash
# ETL pipeline specification
/speckit.specify "Data processing pipeline" "tech_stack:python,pandas,sql,automation_level:advanced"

# Analytics dashboard specification
/speckit.specify "Analytics dashboard" "tech_stack:python,streamlit,plotly,learning_mode:true"
```

### API Development

```bash
# REST API specification
/speckit.specify "User management API" "tech_stack:python,fastapi,sqlalchemy,implementation_focus:true"

# GraphQL API specification
/speckit.specify "Product catalog API" "tech_stack:python,ariadgraph,postgresql,learning_mode:true"
```

### Machine Learning Projects

```bash
# ML model specification
/speckit.specify "Image classification model" "tech_stack:python,scikit-learn,tensorflow,learning_mode:true"

# ML pipeline specification
/speckit.specify "ML training pipeline" "tech_stack:python,mlflow,kubernetes,automation_level:advanced"
```

## Common Pitfalls and Solutions

### Pitfall 1: Over-Specification

**Problem**: Creating specifications that are too detailed and complex
**Symptoms**: 50+ page documents, excessive technical detail
**Solution**:
```bash
# Focus on essentials only
/speckit.specify "Feature" "complexity:simple,implementation_focus:core_only"

# Use timebox to force focus
/speckit.specify "Feature" "timebox:1week,solo_dev:true"
```

### Pitfall 2: Under-Specification

**Problem**: Creating specifications that are too vague to be useful
**Symptoms**: Missing acceptance criteria, unclear requirements
**Solution**:
```bash
# Add implementation focus
/speckit.specify "Feature" "implementation_focus:true,include:acceptance_criteria"

# Use detailed template
/speckit.specify "Feature" "template:detailed"
```

### Pitfall 3: Ignoring Solo Developer Constraints

**Problem**: Creating specifications that assume team resources
**Symptoms**: Unrealistic time estimates, complex coordination requirements
**Solution**:
```bash
# Always optimize for solo development
/speckit.specify "Feature" "solo_dev:true,timebox:2weeks"

# Focus on sequential implementation
/speckit.specify "Feature" "implementation_focus:sequential"
```

### Pitfall 4: Not Updating Based on Learning

**Problem**: Using same approach regardless of project experience
**Symptoms**: Repeating mistakes, not improving estimates
**Solution**:
```bash
# Include learning integration
/speckit.specify "Feature" "learning_mode:true,knowledge_integration:true"

# Store lessons learned
python scripts/knowledge_interface.py store --type lessons_learned --evidence [project-experience]
```

## Measurement and Improvement

### Tracking Specification Quality

**Quality Metrics to Track**:
1. **Implementation Success Rate**: How often specs lead to successful implementation
2. **Time Estimate Accuracy**: Difference between estimated vs actual time
3. **Feature Completeness**: Percentage of specified features that get implemented
4. **Change Frequency**: How often specifications need to be modified

**Improvement Process**:
```bash
# After each project, analyze specification effectiveness
speckit.analyze "project-specification" --quality-metrics

# Store insights for future improvements
python scripts/knowledge_interface.py store --type specification_insights --evidence [analysis-results]
```

### Continuous Learning Loop

1. **Create Specification**: Use `/speckit.specify` with learning mode
2. **Implement Feature**: Follow the specification to build the feature
3. **Track Results**: Compare actual vs estimated time and effort
4. **Analyze Gaps**: Identify what worked and what didn't
5. **Update Knowledge**: Store lessons learned in knowledge system
6. **Improve Next Spec**: Apply insights to future specifications

## Advanced Usage Scenarios

### Multi-Project Coordination

```bash
# Create related specifications with dependencies
/speckit.specify "User authentication" "project_id:AUTH,dependencies:none"
speckit.specify "User profile management" "project_id:PROFILE,dependencies:AUTH"
speckit.specify "User dashboard" "project_id:DASHBOARD,dependencies:AUTH,PROFILE"

# Generate coordination plan
python scripts/project_coordinator.py generate-plan --projects AUTH,PROFILE,DASHBOARD
```

### Specification Templates by Domain

```bash
# E-commerce specification
/speckit.specify "Shopping cart" "template:ecommerce,tech_stack:react,nodejs,mongodb"

# SaaS specification
/speckit.specify "Multi-tenant dashboard" "template:saas,tech_stack:react,python,postgresql"

# Mobile app specification
/speckit.specify "Mobile task manager" "template:mobile,tech_stack:react-native,firebase"
```

### Automated Specification Generation

```bash
# Generate specifications from user stories
python scripts/spec_generator.py --input user_stories.md --template agile

# Generate specifications from API contracts
python scripts/spec_generator.py --input api_contract.yaml --template api_first

# Batch generate specifications for feature list
python scripts/batch_spec_generator.py --features features_list.json --template standard
```

## Integration with Development Tools

### IDE Integration

```bash
# VS Code extension integration
code --install-extension speckit-specify
# Provides syntax highlighting and validation for specifications

# Generate specification from IDE
speckit.specify.from-ide "current-file" --context current-project
```

### CI/CD Integration

```bash
# Validate specifications in CI pipeline
speckit.analyze "specification" --quality-gate --fail-on-errors

# Generate specification reports
speckit.report "specification" --format json --output spec_quality_report.json
```

### Version Control Integration

```bash
# Track specification changes in git
git add specs/
git commit -m "Add specification for user authentication system"

# Generate specification changelog
speckit.changelog "specification" --since v1.0.0 --output CHANGELOG.md
```

## FAQ

### Q: How detailed should my feature description be?
A: Provide enough detail for the specification to be meaningful. Include the core functionality, key requirements, and context. 1-3 sentences is usually sufficient for initial specifications.

### Q: Can I modify specifications after generation?
A: Yes, specifications are editable markdown files. However, significant changes should be documented and the reasons for changes should be stored in the knowledge system.

### Q: How do I handle changing requirements during development?
A: Use the knowledge system to track requirement changes and their impact. Update specifications as needed and document the evolution of requirements.

### Q: Can I use specifications for non-software projects?
A: Yes, the specification framework can be adapted for various types of projects. Adjust the templates and validation criteria accordingly.

### Q: How do I ensure specifications align with business goals?
A: Include business objectives and success criteria in your feature description. Use the knowledge system to track business alignment and measure success against business metrics.
