# CWO12 Artifact Templates

This repository contains comprehensive, production-ready CWO12-compliant artifact templates for different project types. These templates help users create high-quality project documentation that passes the CWO12 artifact validator with confidence scores >0.7.

## Quick Start

### Generate Artifacts Interactively
```bash
cd cwo12-artifact-templates
python scripts/generate_artifacts.py
```

### Generate Artifacts from Configuration
```bash
python scripts/generate_artifacts.py --config examples/demo_api_project.json
```

### Generate Artifacts via Command Line
```bash
python scripts/generate_artifacts.py --name "My Project" --type api-development --output ./my-project
```

## Supported Project Types

| Project Type | Description | Use Case |
|-------------|-------------|----------|
| **api-development** | RESTful API development | Backend services, microservices, web APIs |
| **web-application** | Modern web applications | React/Vue/Angular apps, SPAs, PWAs |
| **data-processing** | Data pipelines and ETL | Big data processing, data engineering |
| **ml-project** | Machine learning projects | ML model development, data science |

## Template Structure

Each project type includes three core artifacts:

### plan.md
- **Objectives**: SMART goals and success criteria
- **Scope**: Project boundaries and deliverables
- **Risk Assessment**: Technical and operational risks with mitigation
- **Timeline**: Phased implementation schedule
- **Resource Requirements**: Team, tools, and infrastructure needs

### tasks.md
- **Task Breakdown**: Detailed, atomic task decomposition
- **Dependencies**: Task relationships and critical path
- **Resource Requirements**: Skills and tools needed
- **Risk Mitigation**: Proactive risk management strategies

### data_model.md
- **Data Model Overview**: High-level data architecture
- **Entity Definitions**: Complete data entities with relationships
- **Relationships**: Entity relationships and constraints
- **Data Integrity**: Validation rules and constraints

## Features

### CWO12 Compliance
- ✅ Meets all CWO12 constitutional requirements
- ✅ Includes required sections for all artifact types
- ✅ Follows CWO12 formatting standards
- ✅ Quality score >0.7 validated against official CWO12 validator

### Customization
- 📝 Template variables for easy customization
- 🔧 Optional configuration parameters
- 📊 Project-specific metrics and targets
- 🎯 Industry-specific success criteria

### Validation
- ✅ Built-in CWO12 compliance validation
- 🔍 Automated quality checks
- 📋 Required section verification
- ⚠️ Issue identification and guidance

## Usage Examples

### API Development Project
```json
{
  "project_name": "E-Commerce Order API",
  "task_id": "TSK-20251127-001",
  "project_description": "RESTful API for order management",
  "project_type": "api-development",
  "custom_vars": {
    "EXPECTED_RPS": "5000",
    "LATENCY_TARGET": "50",
    "DATABASE_SYSTEM": "PostgreSQL 15"
  }
}
```

### Web Application Project
```json
{
  "project_name": "Task Management Dashboard",
  "task_id": "TSK-20251127-002",
  "project_description": "Team collaboration web app",
  "project_type": "web-application",
  "custom_vars": {
    "FRAMEWORK": "React 18",
    "LCP_TARGET": "2.5",
    "ACCURACY_TARGET": "90"
  }
}
```

### Machine Learning Project
```json
{
  "project_name": "Customer Churn Prediction",
  "task_id": "TSK-20251127-003",
  "project_description": "ML system for churn prediction",
  "project_type": "ml-project",
  "custom_vars": {
    "ACCURACY_TARGET": "92",
    "ML_FRAMEWORK": "TensorFlow",
    "DATA_VOLUME": "10M"
  }
}
```

## Available Variables

### Standard Variables
- `{{PROJECT_NAME}}`: Project name
- `{{TASK_ID}}`: Task identifier
- `{{CURRENT_DATE}}`: Current date (YYYY-MM-DD)
- `{{PROJECT_DESCRIPTION}}`: Project description

### Optional Variables (Customizable)
- `{{EXPECTED_RPS}}`: Expected requests per second
- `{{ACCURACY_TARGET}}`: Model accuracy target (%)
- `{{LATENCY_TARGET}}`: Response time target (ms)
- `{{DATABASE_SYSTEM}}`: Database system name
- `{{API_FRAMEWORK}}`: API framework name
- `{{ML_FRAMEWORK}}`: Machine learning framework
- `{{STORAGE_SIZE}}`: Storage size requirement
- And many more...

## Directory Structure

```
cwo12-artifact-templates/
├── templates/
│   ├── api-development/
│   │   ├── plan.md
│   │   ├── tasks.md
│   │   └── data_model.md
│   ├── web-application/
│   │   ├── plan.md
│   │   ├── tasks.md
│   │   └── data_model.md
│   ├── data-processing/
│   │   ├── plan.md
│   │   ├── tasks.md
│   │   └── data_model.md
│   └── ml-project/
│       ├── plan.md
│       ├── tasks.md
│       └── data_model.md
├── examples/
│   ├── demo_api_project.json
│   ├── demo_web_app.json
│   └── demo_ml_project.json
├── scripts/
│   └── generate_artifacts.py
└── README.md
```

## Integration with /plan Command

These templates are designed to integrate seamlessly with the `/plan` command. The template generation utility can be used as a backend service for automated artifact generation.

### Integration Steps

1. **Copy Templates**: Deploy templates to your CWO12 environment
2. **Install Generator**: Set up the Python script as a service
3. **Configure /plan**: Modify `/plan` command to use the generator
4. **Customize**: Add project-specific variables and configurations

### Example Integration
```bash
# Integrate with /plan command
/plan --generate --type api-development --name "My API Project"
```

## Quality Assurance

### CWO12 Compliance Validation
All templates are validated against the official CWO12 artifact validator:

- ✅ **plan.md**: Objectives, Scope, Success Criteria, Risk Assessment, Timeline
- ✅ **tasks.md**: Task Breakdown, Dependencies, Resource Requirements
- ✅ **data_model.md**: Data Model Overview, Entity Definitions, Relationships, Data Integrity

### Quality Metrics
- **Template Completeness**: 100% required sections included
- **CWO12 Score**: >0.7 compliance score guaranteed
- **Usability**: Easy customization with clear documentation
- **Extensibility**: Modular design for easy enhancement

## Contributing

### Adding New Project Types

1. Create template directory: `templates/new-type/`
2. Create three artifact files: `plan.md`, `tasks.md`, `data_model.md`
3. Follow CWO12 requirements and existing template patterns
4. Add example configuration to `examples/`
5. Update documentation

### Template Guidelines

- Follow CWO12 constitutional requirements
- Include all required sections
- Use consistent formatting and structure
- Provide clear placeholder variables
- Include comprehensive examples and guidance

## Examples and Demos

### Generated Artifacts

See the `demo_output/` directory for examples of generated artifacts:

- **API Project**: Complete RESTful API project plan
- **Web App Project**: Modern web application specification
- **ML Project**: End-to-end machine learning project plan

### Validation Results

All generated artifacts pass CWO12 validation:

```
plan.md: [OK] Compliant
tasks.md: [OK] Compliant
data_model.md: [OK] Compliant

[SUCCESS] All artifacts generated successfully!
Artifacts are CWO12 compliant and ready for use.
```

## Support and Troubleshooting

### Common Issues

1. **Missing Variables**: Check that all required variables are provided
2. **Template Not Found**: Verify project type is supported
3. **Validation Errors**: Review CWO12 requirements and template content

### Getting Help

- Check the examples directory for working configurations
- Review the CWO12 documentation for requirements
- Validate generated artifacts with official CWO12 validator
- Use the built-in validation for immediate feedback

## License

This template collection is released under the MIT License and is designed to work with CWO12-compliant development workflows.

## Version History

- **v1.0.0**: Initial release with 4 project types
- Templates validated against CWO12 artifact validator
- Built-in validation and quality assurance
- Integration-ready for /plan command
