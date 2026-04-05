#!/usr/bin/env python3
"""
CSF NIP Agent Factory

Comprehensive agent creation and management system for the Persistent Learning Agent Ecosystem.
This module provides role-based agent spawning with system prompt generation, tool integration,
and session management capabilities.

Features:
- YAML role definitions loading and validation
- Dynamic system prompt generation from templates
- Role-based agent spawning with tool assignment
- Session management for spawned agents
- Integration with existing CSF NIP agent infrastructure
- Support for agent collaboration and communication
- Performance monitoring and optimization

CSF NIP Standards Compliance:
- Evidence-based decision making
- Performance-driven implementation (<10ms agent creation)
- Security-first validation and sanitization
- Comprehensive error handling and recovery
- Integration with CSF NIP orchestration framework
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

# Import existing CSF NIP components
from .cks_integration import store_to_cks

# Try to import schemas, but handle gracefully if not available
try:
    from ..schemas.agent_schemas import BaseAgentSchema, SchemaValidator
except ImportError:
    # Fallback for testing without full CSF NIP infrastructure
    BaseAgentSchema = None
    SchemaValidator = None

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Supported agent roles in the ecosystem."""

    DEVELOPMENT = "development"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    SECURITY = "security"
    ARCHITECTURE = "architecture"
    PERFORMANCE = "performance"
    DEVOPS = "devops"
    DOMAIN_EXPERT = "domain_expert"
    CONTENT_VALIDATOR = "content_validator"
    PROJECT_MANAGER = "project_manager"
    QUALITY_ASSURANCE = "quality_assurance"
    CODE_REVIEWER = "code_reviewer"


class AgentStatus(Enum):
    """Agent lifecycle status."""

    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    IDLE = "idle"
    ERROR = "error"
    TERMINATED = "terminated"


class ToolType(Enum):
    """Available tool types for agents."""

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


@dataclass
class AgentDefinition:
    """Core agent definition loaded from YAML."""

    role_name: str
    description: str
    responsibilities: list[str]
    required_skills: list[str]
    workflows: list[str]
    collaboration: dict[str, Any]
    tools: list[ToolType] = field(default_factory=list)
    system_prompt_template: str | None = None
    configuration: dict[str, Any] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentDefinition:
        """Create AgentDefinition from dictionary."""
        # Convert string tool names to ToolType enum
        tools = []
        if 'tools' in data:
            for tool_name in data['tools']:
                try:
                    tools.append(ToolType(tool_name))
                except ValueError:
                    logger.warning(f"Unknown tool type: {tool_name}")

        return cls(
            role_name=data['role_name'],
            description=data['description'],
            responsibilities=data.get('responsibilities', []),
            required_skills=data.get('required_skills', []),
            workflows=data.get('workflows', []),
            collaboration=data.get('collaboration', {}),
            tools=tools,
            system_prompt_template=data.get('system_prompt_template'),
            configuration=data.get('configuration', {}),
            constraints=data.get('constraints', []),
            capabilities=data.get('capabilities', [])
        )


@dataclass
class AgentInstance:
    """Represents a spawned agent instance."""

    instance_id: str
    agent_definition: AgentDefinition
    status: AgentStatus
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_activity: datetime = field(default_factory=lambda: datetime.now(UTC))
    session_context: dict[str, Any] = field(default_factory=dict)
    system_prompt: str | None = None
    assigned_tools: list[ToolType] = field(default_factory=list)
    performance_metrics: dict[str, Any] = field(default_factory=dict)
    communication_channels: dict[str, str] = field(default_factory=dict)

    def update_activity(self) -> None:
        """Update last activity timestamp."""
        self.last_activity = datetime.now(UTC)


class ToolRegistry:
    """Registry for managing available tools and their assignments."""

    def __init__(self):
        """Initialize the tool registry."""
        self._available_tools: dict[ToolType, dict[str, Any]] = {}
        self._tool_assignments: dict[str, set[ToolType]] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register default available tools."""
        default_tools = {
            ToolType.FILE_OPERATIONS: {
                'name': 'File Operations',
                'description': 'Read, write, and manipulate files',
                'capabilities': ['read', 'write', 'delete', 'list', 'search']
            },
            ToolType.CODE_ANALYSIS: {
                'name': 'Code Analysis',
                'description': 'Analyze and understand code structure',
                'capabilities': ['parsing', 'static_analysis', 'complexity_analysis']
            },
            ToolType.GIT_OPERATIONS: {
                'name': 'Git Operations',
                'description': 'Git repository operations',
                'capabilities': ['status', 'commit', 'push', 'pull', 'branch']
            },
            ToolType.DATABASE_ACCESS: {
                'name': 'Database Access',
                'description': 'Database query and manipulation',
                'capabilities': ['query', 'insert', 'update', 'delete']
            },
            ToolType.API_CALLS: {
                'name': 'API Calls',
                'description': 'External API integration',
                'capabilities': ['http_get', 'http_post', 'authentication']
            },
            ToolType.SHELL_COMMANDS: {
                'name': 'Shell Commands',
                'description': 'Execute shell commands',
                'capabilities': ['execute', 'capture_output', 'error_handling']
            },
            ToolType.TEXT_PROCESSING: {
                'name': 'Text Processing',
                'description': 'Natural language text processing',
                'capabilities': ['parsing', 'generation', 'summarization']
            },
            ToolType.SEARCH_OPERATIONS: {
                'name': 'Search Operations',
                'description': 'Search across codebase and documentation',
                'capabilities': ['code_search', 'doc_search', 'semantic_search']
            },
            ToolType.VALIDATION: {
                'name': 'Validation',
                'description': 'Validate code and configurations',
                'capabilities': ['syntax_check', 'style_check', 'security_scan']
            },
            ToolType.COMMUNICATION: {
                'name': 'Communication',
                'description': 'Inter-agent communication',
                'capabilities': ['message_send', 'message_receive', 'broadcast']
            }
        }

        self._available_tools.update(default_tools)

    def get_tool(self, tool_type: ToolType) -> dict[str, Any] | None:
        """Get tool definition by type."""
        return self._available_tools.get(tool_type)

    def assign_tools_to_agent(self, agent_id: str, tools: list[ToolType]) -> None:
        """Assign tools to an agent instance."""
        self._tool_assignments[agent_id] = set(tools)

    def get_agent_tools(self, agent_id: str) -> set[ToolType]:
        """Get tools assigned to an agent."""
        return self._tool_assignments.get(agent_id, set())

    def remove_agent_tools(self, agent_id: str) -> None:
        """Remove tool assignments for an agent."""
        self._tool_assignments.pop(agent_id, None)


class PromptTemplateEngine:
    """Engine for generating system prompts from templates."""

    def __init__(self):
        """Initialize the prompt template engine."""
        self._templates: dict[str, str] = {}
        self._load_default_templates()

    def _load_default_templates(self) -> None:
        """Load default prompt templates."""
        self._templates = {
            'base': """You are a {role_name} agent in the CSF NIP Persistent Learning Agent Ecosystem.

Role Description: {description}

Your Responsibilities:
{responsibilities}

Required Skills:
{required_skills}

Your Capabilities:
{capabilities}

Your Constraints:
{constraints}

Collaboration Guidelines:
{collaboration}

You communicate using structured messages and always provide evidence for your decisions.
You work collaboratively with other agents and respect the CSF NIP constitution and standards.

Current Context: {context}
Available Tools: {tools}""",

            'development': """You are a Development Agent specializing in software development and implementation.

Role: {role_name}
Description: {description}

Core Responsibilities:
{responsibilities}

Technical Skills:
{required_skills}

Development Workflows:
{workflows}

You write clean, maintainable code following CSF NIP standards. You collaborate with testing,
documentation, and security agents to ensure high-quality deliverables.

Current Task Context: {context}
Available Development Tools: {tools}
Development Constraints: {constraints}""",

            'research': """You are a Research Agent specializing in information gathering and analysis.

Role: {role_name}
Description: {description}

Research Responsibilities:
{responsibilities}

Research Skills:
{required_skills}

Research Methodologies:
{workflows}

You conduct thorough research, validate sources, and provide evidence-based insights.
You collaborate with domain experts and content validators to ensure accuracy.

Research Focus: {context}
Available Research Tools: {tools}
Research Guidelines: {constraints}""",

            'analysis': """You are an Analysis Agent specializing in code and system analysis.

Role: {role_name}
Description: {description}

Analysis Responsibilities:
{responsibilities}

Analytical Skills:
{required_skills}

Analysis Workflows:
{workflows}

You perform comprehensive analysis, identify patterns, and provide actionable insights.
You work with development and architecture agents to drive improvements.

Analysis Scope: {context}
Available Analysis Tools: {tools}
Analysis Constraints: {constraints}"""
        }

    def generate_prompt(
        self,
        agent_def: AgentDefinition,
        context: dict[str, Any],
        tools: list[ToolType]
    ) -> str:
        """Generate system prompt from template and agent definition."""
        # Select template
        template_key = 'base'
        if agent_def.role_name in ['development', 'software_engineer']:
            template_key = 'development'
        elif agent_def.role_name in ['research', 'research_analyst']:
            template_key = 'research'
        elif agent_def.role_name in ['analysis', 'code_analyst']:
            template_key = 'analysis'

        template = agent_def.system_prompt_template or self._templates.get(template_key, self._templates['base'])

        # Prepare template variables
        responsibilities_text = '\n'.join(f'- {resp}' for resp in agent_def.responsibilities)
        skills_text = '\n'.join(f'- {skill}' for skill in agent_def.required_skills)
        capabilities_text = '\n'.join(f'- {cap}' for cap in agent_def.capabilities) if agent_def.capabilities else 'General agent capabilities'
        constraints_text = '\n'.join(f'- {constraint}' for constraint in agent_def.constraints) if agent_def.constraints else 'Follow CSF NIP standards'

        # Format collaboration information
        collab_text = self._format_collaboration_info(agent_def.collaboration)

        # Format tools
        tools_text = ', '.join(tool.value for tool in tools)

        # Format context
        context_text = json.dumps(context, indent=2) if context else 'No specific context provided'

        # Generate prompt
        try:
            prompt = template.format(
                role_name=agent_def.role_name,
                description=agent_def.description,
                responsibilities=responsibilities_text,
                required_skills=skills_text,
                workflows='\n'.join(f'- {workflow}' for workflow in agent_def.workflows),
                capabilities=capabilities_text,
                constraints=constraints_text,
                collaboration=collab_text,
                context=context_text,
                tools=tools_text
            )
            return prompt
        except KeyError as e:
            logger.error(f"Template formatting error: {e}")
            return self._generate_fallback_prompt(agent_def, context, tools)

    def _format_collaboration_info(self, collaboration: dict[str, Any]) -> str:
        """Format collaboration information for prompt."""
        if not collaboration:
            return "Work collaboratively with other agents"

        parts = []
        if 'primary_partners' in collaboration:
            parts.append(f"Primary Partners: {', '.join(collaboration['primary_partners'])}")

        if 'interaction_patterns' in collaboration:
            patterns = collaboration['interaction_patterns']
            if isinstance(patterns, list):
                parts.append(f"Interaction Patterns: {', '.join(patterns)}")
            else:
                parts.append(f"Interaction Patterns: {patterns}")

        return '\n'.join(parts) if parts else "Work collaboratively with other agents"

    def _generate_fallback_prompt(
        self,
        agent_def: AgentDefinition,
        context: dict[str, Any],
        tools: list[ToolType]
    ) -> str:
        """Generate fallback prompt if template formatting fails."""
        return f"""You are a {agent_def.role_name} agent.

Description: {agent_def.description}

Responsibilities:
{chr(10).join(f'- {resp}' for resp in agent_def.responsibilities)}

Skills:
{chr(10).join(f'- {skill}' for skill in agent_def.required_skills)}

Work with available tools and follow CSF NIP standards.
Context: {json.dumps(context, indent=2)}
Tools: {', '.join(tool.value for tool in tools)}"""


class SessionManager:
    """Manages agent sessions and lifecycle."""

    def __init__(self):
        """Initialize the session manager."""
        self._sessions: dict[str, AgentInstance] = {}
        self._session_lock = threading.Lock()
        self._cleanup_interval = 300  # 5 minutes
        self._session_timeout = 3600  # 1 hour
        self._start_cleanup_task()

    def create_session(
        self,
        agent_def: AgentDefinition,
        system_prompt: str,
        tools: list[ToolType],
        initial_context: dict[str, Any] | None = None
    ) -> str:
        """Create a new agent session."""
        session_id = str(uuid.uuid4())

        with self._session_lock:
            session = AgentInstance(
                instance_id=session_id,
                agent_definition=agent_def,
                status=AgentStatus.INITIALIZING,
                session_context=initial_context or {},
                system_prompt=system_prompt,
                assigned_tools=tools
            )

            self._sessions[session_id] = session

        logger.info(f"Created agent session: {session_id} for role: {agent_def.role_name}")
        return session_id

    def get_session(self, session_id: str) -> AgentInstance | None:
        """Get agent session by ID."""
        with self._session_lock:
            session = self._sessions.get(session_id)
            if session:
                session.update_activity()
            return session

    def update_session_status(self, session_id: str, status: AgentStatus) -> bool:
        """Update session status."""
        with self._session_lock:
            session = self._sessions.get(session_id)
            if session:
                session.status = status
                session.update_activity()
                return True
            return False

    def update_session_context(self, session_id: str, context_updates: dict[str, Any]) -> bool:
        """Update session context."""
        with self._session_lock:
            session = self._sessions.get(session_id)
            if session:
                session.session_context.update(context_updates)
                session.update_activity()
                return True
            return False

    def terminate_session(self, session_id: str) -> bool:
        """Terminate an agent session."""
        with self._session_lock:
            session = self._sessions.pop(session_id, None)
            if session:
                session.status = AgentStatus.TERMINATED
                logger.info(f"Terminated agent session: {session_id}")
                return True
            return False

    def get_active_sessions(self) -> list[AgentInstance]:
        """Get all active sessions."""
        with self._session_lock:
            return [session for session in self._sessions.values() if session.status != AgentStatus.TERMINATED]

    def cleanup_inactive_sessions(self) -> int:
        """Clean up inactive sessions."""
        current_time = datetime.now(UTC)
        sessions_to_remove = []

        with self._session_lock:
            for session_id, session in self._sessions.items():
                time_since_activity = (current_time - session.last_activity).total_seconds()
                if time_since_activity > self._session_timeout:
                    if session.status in [AgentStatus.IDLE, AgentStatus.ERROR]:
                        sessions_to_remove.append(session_id)

            for session_id in sessions_to_remove:
                self._sessions.pop(session_id, None)

        if sessions_to_remove:
            logger.info(f"Cleaned up {len(sessions_to_remove)} inactive sessions")

        return len(sessions_to_remove)

    def _start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        def cleanup_loop():
            import time
            while True:
                try:
                    time.sleep(self._cleanup_interval)
                    self.cleanup_inactive_sessions()
                except Exception as e:
                    logger.error(f"Session cleanup error: {e}")

        cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        cleanup_thread.start()


class AgentFactory:
    """
    Main Agent Factory class for creating and managing role-based agents.

    This class provides the primary interface for:
    - Loading YAML role definitions
    - Creating agents with specific roles
    - Managing agent sessions
    - Providing tools and capabilities to agents
    """

    def __init__(self, roles_directory: str | None = None):
        """
        Initialize the Agent Factory.

        Args:
            roles_directory: Path to directory containing YAML role definitions
        """
        self.roles_directory = Path(roles_directory or Path(__file__).parent / "roles")
        self._role_definitions: dict[str, AgentDefinition] = {}
        self._tool_registry = ToolRegistry()
        self._prompt_engine = PromptTemplateEngine()
        self._session_manager = SessionManager()
        self._schema_validator = SchemaValidator() if SchemaValidator else None
        self._performance_metrics = {
            'agents_created': 0,
            'agents_spawned': 0,
            'sessions_active': 0,
            'average_creation_time': 0.0,
            'total_creation_time': 0.0
        }

        # Load role definitions
        self._load_role_definitions()

        logger.info(f"Agent Factory initialized with {len(self._role_definitions)} roles")

    def _load_role_definitions(self) -> None:
        """Load all YAML role definitions from the roles directory."""
        if not self.roles_directory.exists():
            logger.warning(f"Roles directory not found: {self.roles_directory}")
            return

        for yaml_file in self.roles_directory.glob("*.yaml"):
            try:
                with open(yaml_file, encoding='utf-8') as f:
                    role_data = yaml.safe_load(f)

                if role_data and 'role_name' in role_data:
                    agent_def = AgentDefinition.from_dict(role_data)
                    self._role_definitions[agent_def.role_name] = agent_def
                    logger.info(f"Loaded role definition: {agent_def.role_name}")
                else:
                    logger.warning(f"Invalid role definition in {yaml_file}")

            except Exception as e:
                logger.error(f"Error loading role definition from {yaml_file}: {e}")

    def create_agent(
        self,
        role_name: str,
        context: dict[str, Any] | None = None,
        additional_tools: list[ToolType] | None = None,
        configuration_overrides: dict[str, Any] | None = None
    ) -> str | None:
        """
        Create a new agent instance.

        Args:
            role_name: Name of the role to create
            context: Initial context for the agent
            additional_tools: Additional tools to assign beyond role defaults
            configuration_overrides: Override configuration values

        Returns:
            Session ID of the created agent, or None if creation failed
        """
        start_time = datetime.now(UTC)

        try:
            # Get role definition
            agent_def = self._role_definitions.get(role_name)
            if not agent_def:
                logger.error(f"Unknown role: {role_name}")
                return None

            # Apply configuration overrides
            if configuration_overrides:
                agent_def.configuration.update(configuration_overrides)

            # Determine tools
            tools = list(agent_def.tools)
            if additional_tools:
                tools.extend(additional_tools)

            # Generate system prompt
            system_prompt = self._prompt_engine.generate_prompt(
                agent_def,
                context or {},
                tools
            )

            # Create session
            session_id = self._session_manager.create_session(
                agent_def,
                system_prompt,
                tools,
                context
            )

            # Register tools
            self._tool_registry.assign_tools_to_agent(session_id, tools)

            # Update session status to ready
            self._session_manager.update_session_status(session_id, AgentStatus.READY)

            # Update metrics
            creation_time = (datetime.now(UTC) - start_time).total_seconds()
            self._update_performance_metrics(creation_time)

            # Store in CKS for learning
            self._store_agent_creation_record(role_name, context, tools, creation_time)

            logger.info(f"Created agent {role_name} with session ID: {session_id}")
            return session_id

        except Exception as e:
            logger.error(f"Error creating agent {role_name}: {e}")
            return None

    def get_agent(self, session_id: str) -> AgentInstance | None:
        """Get agent instance by session ID."""
        return self._session_manager.get_session(session_id)

    def terminate_agent(self, session_id: str) -> bool:
        """Terminate an agent instance."""
        # Remove tool assignments
        self._tool_registry.remove_agent_tools(session_id)

        # Terminate session
        return self._session_manager.terminate_session(session_id)

    def get_available_roles(self) -> list[str]:
        """Get list of available role names."""
        return list(self._role_definitions.keys())

    def get_role_definition(self, role_name: str) -> AgentDefinition | None:
        """Get role definition by name."""
        return self._role_definitions.get(role_name)

    def update_agent_context(self, session_id: str, context_updates: dict[str, Any]) -> bool:
        """Update agent session context."""
        return self._session_manager.update_session_context(session_id, context_updates)

    def get_agent_tools(self, session_id: str) -> list[ToolType]:
        """Get tools assigned to an agent."""
        return list(self._tool_registry.get_agent_tools(session_id))

    def get_active_agents(self) -> list[AgentInstance]:
        """Get all active agent instances."""
        return self._session_manager.get_active_sessions()

    def get_performance_metrics(self) -> dict[str, Any]:
        """Get factory performance metrics."""
        metrics = self._performance_metrics.copy()
        metrics['sessions_active'] = len(self.get_active_agents())
        metrics['available_roles'] = len(self._role_definitions)
        metrics['available_tools'] = len(self._tool_registry._available_tools)
        return metrics

    def reload_role_definitions(self) -> int:
        """Reload role definitions from disk."""
        old_count = len(self._role_definitions)
        self._role_definitions.clear()
        self._load_role_definitions()
        new_count = len(self._role_definitions)

        logger.info(f"Reloaded role definitions: {old_count} -> {new_count}")
        return new_count

    def _update_performance_metrics(self, creation_time: float) -> None:
        """Update performance metrics."""
        self._performance_metrics['agents_created'] += 1
        self._performance_metrics['agents_spawned'] += 1
        self._performance_metrics['total_creation_time'] += creation_time

        if self._performance_metrics['agents_created'] > 0:
            self._performance_metrics['average_creation_time'] = (
                self._performance_metrics['total_creation_time'] /
                self._performance_metrics['agents_created']
            )

    def _store_agent_creation_record(
        self,
        role_name: str,
        context: dict[str, Any] | None,
        tools: list[ToolType],
        creation_time: float
    ) -> None:
        """Store agent creation record in CKS for learning."""
        try:
            question = f"Create {role_name} agent with context: {context}"
            answer = f"""Agent Creation Success:
- Role: {role_name}
- Tools: {[tool.value for tool in tools]}
- Creation Time: {creation_time:.3f}s
- Context: {context}
"""

            store_to_cks(
                question,
                answer,
                metadata={
                    "source": "agent_factory",
                    "role_name": role_name,
                    "creation_time": creation_time,
                    "tools_assigned": [tool.value for tool in tools]
                }
            )
        except Exception as e:
            logger.warning(f"Failed to store agent creation record: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources."""
        # Terminate all active sessions
        active_sessions = self.get_active_agents()
        for session in active_sessions:
            self.terminate_agent(session.instance_id)

        logger.info("Agent Factory shutdown complete")


# Convenience function for creating factory instances
def create_agent_factory(roles_directory: str | None = None) -> AgentFactory:
    """
    Create a new Agent Factory instance.

    Args:
        roles_directory: Path to directory containing YAML role definitions

    Returns:
        Configured Agent Factory instance
    """
    return AgentFactory(roles_directory)
