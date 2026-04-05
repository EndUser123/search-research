# Agent Factory Roles

This directory contains YAML role definitions for the Persistent Learning Agent Ecosystem.

## Available Role Definitions

### Core Expert Roles

- **[backend_expert.yaml](./backend_expert.yaml)** - Backend development, APIs, databases, and system architecture
- **[frontend_expert.yaml](./frontend_expert.yaml)** - Frontend development, UI/UX design, and client-side performance
- **[testing_expert.yaml](./testing_expert.yaml)** - Testing methodologies, test automation, and quality assurance
- **[infrastructure_expert.yaml](./infrastructure_expert.yaml)** - DevOps, infrastructure management, security, and monitoring

### Reference

- **[sample_role.yaml](./sample_role.yaml)** - Sample role definition demonstrating structure and format

## Role Definition Structure

Each role YAML file should contain:

### Core Information
- `role_name`: Unique identifier for the role
- `description`: Brief description of the role's purpose
- `core_competencies`: Main areas of expertise

### Technical Capabilities
- `technical_skills`: Programming languages, frameworks, tools
- `specialization_areas`: Advanced expertise areas with capability levels
- `tool_assignments`: Tools and permissions for the role

### Execution Protocols
- `protocol_steps`: Step-by-step procedures for task execution
- `prompt_templates`: Reusable prompt templates for common scenarios
- `decision_authority`: Autonomous vs collaborative decision boundaries

### Quality Standards
- `quality_standards`: Performance, security, and compliance requirements
- `learning_focus`: Continuous learning and knowledge sharing priorities

### Collaboration
- `collaboration_patterns`: How this role interacts with other roles
- `primary_partners`: Key collaborators and interaction protocols

## Role Integration

The roles are designed to work together in the Persistent Learning Agent Ecosystem:

1. **Backend Expert** collaborates with Frontend Expert on API contracts and data structures
2. **Frontend Expert** works with Testing Expert on component and E2E testing strategies
3. **Testing Expert** coordinates with Backend and Infrastructure Experts on comprehensive testing
4. **Infrastructure Expert** supports all roles with deployment, security, and monitoring

## Adding New Roles

1. Analyze the need for a new specialization
2. Create a new YAML file following naming convention: `{role_name}.yaml`
3. Follow the comprehensive structure demonstrated in existing roles
4. Define clear collaboration patterns with existing roles
5. Test the role definition with the agent factory
6. Update documentation and role registry

## Role Usage

The AgentFactory loads these YAML definitions to create specialized agents with:
- Defined competencies and skill sets
- Clear execution protocols
- Appropriate tool permissions
- Established collaboration patterns
- Quality standards and criteria