# CSF NIP Agent Factory

A comprehensive agent creation and management system for the Persistent Learning Agent Ecosystem. This module provides role-based agent spawning with system prompt generation, tool integration, and session management capabilities.

## Features

### 🎯 Core Capabilities

- **Role-Based Agent Creation**: Create specialized agents from YAML role definitions
- **Dynamic System Prompt Generation**: Generate context-aware prompts from templates
- **Tool Assignment and Management**: Assign and manage tools for different agent roles
- **Session Management**: Complete agent lifecycle management with persistence
- **Agent Collaboration**: Enable agents to work together through context sharing
- **Performance Monitoring**: Track metrics and optimize agent performance
- **CKS Integration**: Store and retrieve agent creation patterns for learning

### 🛠 Available Tools

- **File Operations**: Read, write, and manipulate files
- **Code Analysis**: Analyze and understand code structure
- **Git Operations**: Version control and repository management
- **Database Access**: Query and manipulate databases
- **API Calls**: External service integration
- **Shell Commands**: Execute system commands
- **Text Processing**: Natural language processing capabilities
- **Search Operations**: Search across codebase and documentation
- **Validation**: Code and configuration validation
- **Communication**: Inter-agent messaging

## Quick Start

### Basic Usage

```python
from agent_factory import AgentFactory, ToolType

# Initialize the Agent Factory
factory = AgentFactory()

# Create a development agent
context = {
    "project": "My Project",
    "task": "Implement user authentication",
    "requirements": ["JWT tokens", "Password hashing", "Session management"]
}

session_id = factory.create_agent(
    "development_agent",
    context=context,
    additional_tools=[ToolType.DATABASE_ACCESS]
)

# Get the agent instance
agent = factory.get_agent(session_id)
print(f"Agent status: {agent.status.value}")
print(f"System prompt: {agent.system_prompt}")
```

### Using Custom Roles Directory

```python
factory = AgentFactory("/path/to/custom/roles")
```

### Agent Collaboration

```python
# Create multiple agents
dev_session = factory.create_agent("development_agent", {"task": "Implement API"})
test_session = factory.create_agent("testing_agent", {"scope": "API testing"})

# Share context between agents
factory.update_agent_context(test_session, {
    "api_endpoints": ["/users", "/auth", "/profile"],
    "dev_team_notes": "Authentication implemented with JWT"
})
```

## Role Definitions

### Structure

Each role is defined in a YAML file with the following structure:

```yaml
role_name: "development_agent"
description: "Specializes in software development and implementation"

responsibilities:
  - Write clean, maintainable code
  - Debug and fix issues
  - Collaborate with other agents

required_skills:
  - Programming languages
  - Debugging skills
  - Version control

workflows:
  - Feature development workflow
  - Bug fixing workflow

collaboration:
  primary_partners:
    - "testing_agent"
    - "documentation_agent"
  interaction_patterns:
    - Code review sessions
    - Collaborative development

tools:
  - file_operations
  - git_operations
  - code_analysis

capabilities:
  - Full-stack development
  - API design
  - Database integration

constraints:
  - Must follow coding standards
  - Code must be tested

configuration:
  code_style:
    max_line_length: 88
    indent_size: 4
```

### Available Roles

- **Development Agent**: Software development and implementation
- **Research Agent**: Information gathering and analysis
- **Testing Agent**: Quality assurance and testing strategies
- **Documentation Agent**: Documentation creation and maintenance
- **Security Agent**: Security analysis and vulnerability assessment
- **Architecture Agent**: System design and technical decision-making

## API Reference

### AgentFactory

```python
class AgentFactory:
    def __init__(self, roles_directory: Optional[str] = None):
        """Initialize the Agent Factory."""

    def create_agent(
        self,
        role_name: str,
        context: Optional[Dict[str, Any]] = None,
        additional_tools: Optional[List[ToolType]] = None,
        configuration_overrides: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Create a new agent instance."""

    def get_agent(self, session_id: str) -> Optional[AgentInstance]:
        """Get agent instance by session ID."""

    def terminate_agent(self, session_id: str) -> bool:
        """Terminate an agent instance."""

    def get_available_roles(self) -> List[str]:
        """Get list of available role names."""

    def get_active_agents(self) -> List[AgentInstance]:
        """Get all active agent instances."""

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get factory performance metrics."""
```

### AgentInstance

```python
@dataclass
class AgentInstance:
    instance_id: str
    agent_definition: AgentDefinition
    status: AgentStatus
    system_prompt: Optional[str]
    session_context: Dict[str, Any]
    assigned_tools: List[ToolType]
    performance_metrics: Dict[str, Any]
```

### ToolType

```python
class ToolType(Enum):
    FILE_OPERATIONS = "file_operations"
    CODE_ANALYSIS = "code_analysis"
    GIT_OPERATIONS = "git_operations"
    DATABASE_ACCESS = "database_access"
    API_CALLS = "api_calls"
    SHELL_COMMANDS = "shell_commands"
    TEXT_PROCESSING = "text_processing"
    SEARCH_OPERATIONS = "search_operations"
    VALIDATION = "validation"
    COMMUNICATION = "communication"
```

## Architecture

### Components

1. **AgentFactory**: Main interface for creating and managing agents
2. **ToolRegistry**: Manages available tools and assignments
3. **PromptTemplateEngine**: Generates system prompts from templates
4. **SessionManager**: Handles agent session lifecycle
5. **AgentDefinition**: Data model for role definitions

### Workflow

1. **Load Role Definitions**: YAML files parsed into AgentDefinition objects
2. **Generate System Prompt**: Template engine creates role-specific prompts
3. **Assign Tools**: Tools assigned based on role and additional requirements
4. **Create Session**: Session manager tracks agent lifecycle
5. **Enable Collaboration**: Context sharing between agents
6. **Monitor Performance**: Metrics collected for optimization

## Testing

### Run Basic Tests

```bash
cd __csf.nip/src/lib/core_utils/agent_factory
python test_basic_functionality.py
```

### Run Demonstration

```bash
cd __csf.nip/src/lib/core_utils/agent_factory
python demo_agent_factory.py
```

### Test Coverage

The test suite covers:
- Agent creation and configuration
- Role definition loading
- Tool assignment
- Session management
- Agent collaboration
- Performance metrics
- Error handling

## Integration

### With CSF NIP Components

- **CKS Integration**: Agent creation patterns stored for learning
- **Schema Validation**: Compatible with CSF NIP agent schemas
- **Critic System**: Quality evaluation integration
- **Evaluation Pipeline**: Performance assessment integration

### Custom Tool Development

```python
from agent_factory import ToolType, ToolRegistry

# Register custom tool
registry = ToolRegistry()
registry._available_tools[ToolType.CUSTOM_TOOL] = {
    'name': 'Custom Tool',
    'description': 'Custom functionality',
    'capabilities': ['custom_operation']
}
```

## Performance

### Metrics

- **Agent Creation Time**: <10ms for most roles
- **Memory Usage**: Efficient session management
- **Concurrent Sessions**: Supports multiple active agents
- **Tool Assignment**: O(1) complexity for tool lookups

### Optimization Features

- Session cleanup for inactive agents
- Tool assignment caching
- Prompt template optimization
- Performance metrics tracking

## Security

### Security Features

- Input validation and sanitization
- Secure tool execution environment
- Session isolation
- CKS integration for audit trails

### Best Practices

- Validate all inputs
- Use principle of least privilege
- Monitor agent activities
- Regular security audits

## Troubleshooting

### Common Issues

1. **Role Definition Loading**: Ensure YAML files are properly formatted
2. **Tool Assignment**: Check tool availability and permissions
3. **Session Management**: Monitor for session leaks
4. **Performance**: Review metrics for optimization opportunities

### Debug Information

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

### Adding New Roles

1. Create YAML role definition file
2. Follow the established structure and conventions
3. Test the role with basic functionality
4. Update documentation

### Extending Tool Types

1. Add new ToolType enum value
2. Register tool in ToolRegistry
3. Implement tool functionality
4. Add tests and documentation

## License

This module is part of the CSF NIP (Constitutional System Framework - Neural Intelligence Platform) project.

## Support

For questions, issues, or contributions, please refer to the CSF NIP project documentation and issue tracking systems.