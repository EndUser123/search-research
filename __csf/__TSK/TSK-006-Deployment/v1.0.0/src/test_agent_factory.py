#!/usr/bin/env python3
"""
Test Suite for CSF NIP Agent Factory

Comprehensive test suite covering Agent Factory functionality including:
- Role definition loading
- Agent creation and spawning
- System prompt generation
- Tool assignment
- Session management
- Performance metrics
- Integration with existing CSF NIP components

CSF NIP Standards Compliance:
- TDD Red-Green-Refactor methodology
- 100% test coverage requirements
- Performance-driven implementation (<10ms operations)
- Comprehensive error scenario testing
"""

import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

# Import the Agent Factory components
from .agent_factory import (
    AgentDefinition,
    AgentFactory,
    AgentStatus,
    PromptTemplateEngine,
    SessionManager,
    ToolRegistry,
    ToolType,
    create_agent_factory,
)


class TestAgentDefinition:
    """Test suite for AgentDefinition class."""

    def test_from_dict_minimal(self):
        """Test creating AgentDefinition from minimal dictionary."""
        data = {
            "role_name": "test_agent",
            "description": "Test agent for testing",
            "responsibilities": ["Testing"],
            "required_skills": ["Python"],
            "workflows": ["Test workflow"],
            "collaboration": {"primary_partners": ["dev_agent"]}
        }

        agent_def = AgentDefinition.from_dict(data)

        assert agent_def.role_name == "test_agent"
        assert agent_def.description == "Test agent for testing"
        assert agent_def.responsibilities == ["Testing"]
        assert agent_def.required_skills == ["Python"]
        assert agent_def.workflows == ["Test workflow"]
        assert agent_def.collaboration == {"primary_partners": ["dev_agent"]}
        assert agent_def.tools == []
        assert agent_def.system_prompt_template is None

    def test_from_dict_with_tools(self):
        """Test creating AgentDefinition with tools."""
        data = {
            "role_name": "dev_agent",
            "description": "Development agent",
            "responsibilities": ["Coding"],
            "required_skills": ["Python"],
            "workflows": ["Dev workflow"],
            "collaboration": {},
            "tools": ["file_operations", "git_operations"],
            "system_prompt_template": "Custom prompt template"
        }

        agent_def = AgentDefinition.from_dict(data)

        assert agent_def.tools == [ToolType.FILE_OPERATIONS, ToolType.GIT_OPERATIONS]
        assert agent_def.system_prompt_template == "Custom prompt template"

    def test_from_dict_with_unknown_tool(self):
        """Test handling unknown tool types gracefully."""
        data = {
            "role_name": "test_agent",
            "description": "Test agent",
            "responsibilities": ["Testing"],
            "required_skills": ["Python"],
            "workflows": ["Test workflow"],
            "collaboration": {},
            "tools": ["file_operations", "unknown_tool"]
        }

        # Should not raise exception but log warning
        with patch('agent_factory.agent_factory.logger') as mock_logger:
            agent_def = AgentDefinition.from_dict(data)
            assert agent_def.tools == [ToolType.FILE_OPERATIONS]
            mock_logger.warning.assert_called_with("Unknown tool type: unknown_tool")


class TestToolRegistry:
    """Test suite for ToolRegistry class."""

    def test_initialization(self):
        """Test ToolRegistry initialization."""
        registry = ToolRegistry()
        assert len(registry._available_tools) == 10  # Default tools count
        assert ToolType.FILE_OPERATIONS in registry._available_tools

    def test_get_tool(self):
        """Test getting tool definition."""
        registry = ToolRegistry()
        tool = registry.get_tool(ToolType.FILE_OPERATIONS)

        assert tool is not None
        assert tool['name'] == 'File Operations'
        assert 'capabilities' in tool

    def test_get_unknown_tool(self):
        """Test getting unknown tool returns None."""
        registry = ToolRegistry()
        tool = registry.get_tool("unknown_tool")
        assert tool is None

    def test_assign_tools_to_agent(self):
        """Test assigning tools to agent."""
        registry = ToolRegistry()
        agent_id = "test_agent_001"
        tools = [ToolType.FILE_OPERATIONS, ToolType.GIT_OPERATIONS]

        registry.assign_tools_to_agent(agent_id, tools)
        assigned_tools = registry.get_agent_tools(agent_id)

        assert assigned_tools == set(tools)

    def test_remove_agent_tools(self):
        """Test removing agent tools."""
        registry = ToolRegistry()
        agent_id = "test_agent_001"
        tools = [ToolType.FILE_OPERATIONS]

        registry.assign_tools_to_agent(agent_id, tools)
        assert len(registry.get_agent_tools(agent_id)) == 1

        registry.remove_agent_tools(agent_id)
        assert len(registry.get_agent_tools(agent_id)) == 0


class TestPromptTemplateEngine:
    """Test suite for PromptTemplateEngine class."""

    def test_initialization(self):
        """Test PromptTemplateEngine initialization."""
        engine = PromptTemplateEngine()
        assert len(engine._templates) == 4  # Default templates count
        assert 'base' in engine._templates

    def test_generate_prompt_base_template(self):
        """Test generating prompt with base template."""
        engine = PromptTemplateEngine()

        agent_def = AgentDefinition(
            role_name="test_agent",
            description="Test agent description",
            responsibilities=["Test responsibility"],
            required_skills=["Python"],
            workflows=["Test workflow"],
            collaboration={"primary_partners": ["dev_agent"]},
            capabilities=["Testing"],
            constraints=["Follow standards"]
        )

        context = {"project": "test_project"}
        tools = [ToolType.FILE_OPERATIONS]

        prompt = engine.generate_prompt(agent_def, context, tools)

        assert "test_agent" in prompt
        assert "Test agent description" in prompt
        assert "Test responsibility" in prompt
        assert "Python" in prompt
        assert "file_operations" in prompt
        assert "test_project" in prompt

    def test_generate_prompt_role_specific_template(self):
        """Test generating prompt with role-specific template."""
        engine = PromptTemplateEngine()

        agent_def = AgentDefinition(
            role_name="development",
            description="Development agent",
            responsibilities=["Coding"],
            required_skills=["Python", "JavaScript"],
            workflows=["Dev workflow"],
            collaboration={},
            capabilities=["Full-stack development"]
        )

        prompt = engine.generate_prompt(agent_def, {}, [])

        assert "Development Agent" in prompt
        assert "Write clean, maintainable code" in prompt

    def test_generate_fallback_prompt(self):
        """Test fallback prompt generation."""
        engine = PromptTemplateEngine()

        # Create agent def with template that will cause formatting error
        agent_def = AgentDefinition(
            role_name="test",
            description="Test",
            responsibilities=["Test"],
            required_skills=["Test"],
            workflows=["Test"],
            collaboration={},
            system_prompt_template="Invalid template with {unknown_var}"
        )

        prompt = engine.generate_prompt(agent_def, {}, [])

        assert prompt is not None
        assert "test" in prompt
        assert "Test" in prompt


class TestSessionManager:
    """Test suite for SessionManager class."""

    def test_create_session(self):
        """Test creating a new session."""
        manager = SessionManager()

        agent_def = AgentDefinition(
            role_name="test_agent",
            description="Test agent",
            responsibilities=["Test"],
            required_skills=["Test"],
            workflows=["Test"],
            collaboration={}
        )

        system_prompt = "Test system prompt"
        tools = [ToolType.FILE_OPERATIONS]
        context = {"project": "test"}

        session_id = manager.create_session(agent_def, system_prompt, tools, context)

        assert session_id is not None
        session = manager.get_session(session_id)
        assert session is not None
        assert session.agent_definition == agent_def
        assert session.system_prompt == system_prompt
        assert session.assigned_tools == tools
        assert session.session_context == context

    def test_get_nonexistent_session(self):
        """Test getting nonexistent session returns None."""
        manager = SessionManager()
        session = manager.get_session("nonexistent_id")
        assert session is None

    def test_update_session_status(self):
        """Test updating session status."""
        manager = SessionManager()

        agent_def = AgentDefinition(
            role_name="test",
            description="Test",
            responsibilities=["Test"],
            required_skills=["Test"],
            workflows=["Test"],
            collaboration={}
        )

        session_id = manager.create_session(agent_def, "prompt", [])

        success = manager.update_session_status(session_id, AgentStatus.BUSY)
        assert success is True

        session = manager.get_session(session_id)
        assert session.status == AgentStatus.BUSY

    def test_terminate_session(self):
        """Test terminating a session."""
        manager = SessionManager()

        agent_def = AgentDefinition(
            role_name="test",
            description="Test",
            responsibilities=["Test"],
            required_skills=["Test"],
            workflows=["Test"],
            collaboration={}
        )

        session_id = manager.create_session(agent_def, "prompt", [])

        success = manager.terminate_session(session_id)
        assert success is True

        session = manager.get_session(session_id)
        assert session is None

    def test_cleanup_inactive_sessions(self):
        """Test cleanup of inactive sessions."""
        manager = SessionManager()

        agent_def = AgentDefinition(
            role_name="test",
            description="Test",
            responsibilities=["Test"],
            required_skills=["Test"],
            workflows=["Test"],
            collaboration={}
        )

        # Create sessions
        session_ids = []
        for i in range(3):
            session_id = manager.create_session(agent_def, "prompt", [])
            session_ids.append(session_id)

        # Set some sessions to idle and simulate timeout
        for session_id in session_ids[:2]:
            manager.update_session_status(session_id, AgentStatus.IDLE)
            # Manually set last_activity to simulate timeout
            session = manager.get_session(session_id)
            session.last_activity = datetime.now(UTC).timestamp() - 4000  # Over 1 hour ago

        # Mock the timeout value for testing
        manager._session_timeout = 3600  # 1 hour

        cleaned_count = manager.cleanup_inactive_sessions()
        assert cleaned_count == 2

        # Only one session should remain
        active_sessions = manager.get_active_sessions()
        assert len(active_sessions) == 1


class TestAgentFactory:
    """Test suite for AgentFactory class."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.roles_dir = Path(self.temp_dir) / "roles"
        self.roles_dir.mkdir()

        # Create sample role definition
        role_data = {
            "role_name": "test_agent",
            "description": "Test agent for testing",
            "responsibilities": ["Testing"],
            "required_skills": ["Python", "Testing"],
            "workflows": ["Test workflow"],
            "collaboration": {
                "primary_partners": ["dev_agent"],
                "interaction_patterns": ["Testing collaboration"]
            },
            "tools": ["file_operations", "validation"],
            "capabilities": ["Unit testing", "Integration testing"],
            "constraints": ["Must follow testing best practices"]
        }

        role_file = self.roles_dir / "test_agent.yaml"
        with open(role_file, 'w') as f:
            yaml.dump(role_data, f)

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test AgentFactory initialization."""
        factory = AgentFactory(str(self.roles_dir))

        assert len(factory.get_available_roles()) == 1
        assert "test_agent" in factory.get_available_roles()

        role_def = factory.get_role_definition("test_agent")
        assert role_def is not None
        assert role_def.role_name == "test_agent"

    def test_initialization_no_roles_directory(self):
        """Test initialization with non-existent roles directory."""
        factory = AgentFactory("/nonexistent/path")
        assert len(factory.get_available_roles()) == 0

    def test_create_agent_success(self):
        """Test successful agent creation."""
        factory = AgentFactory(str(self.roles_dir))

        context = {"project": "test_project", "task": "testing"}
        session_id = factory.create_agent("test_agent", context)

        assert session_id is not None

        agent = factory.get_agent(session_id)
        assert agent is not None
        assert agent.status == AgentStatus.READY
        assert agent.session_context == context
        assert ToolType.FILE_OPERATIONS in agent.assigned_tools
        assert ToolType.VALIDATION in agent.assigned_tools

    def test_create_agent_unknown_role(self):
        """Test creating agent with unknown role."""
        factory = AgentFactory(str(self.roles_dir))

        session_id = factory.create_agent("unknown_role")
        assert session_id is None

    def test_create_agent_with_additional_tools(self):
        """Test creating agent with additional tools."""
        factory = AgentFactory(str(self.roles_dir))

        additional_tools = [ToolType.GIT_OPERATIONS, ToolType.SHELL_COMMANDS]
        session_id = factory.create_agent("test_agent", additional_tools=additional_tools)

        agent = factory.get_agent(session_id)
        assigned_tools = factory.get_agent_tools(session_id)

        assert ToolType.FILE_OPERATIONS in assigned_tools  # From role definition
        assert ToolType.VALIDATION in assigned_tools  # From role definition
        assert ToolType.GIT_OPERATIONS in assigned_tools  # Additional
        assert ToolType.SHELL_COMMANDS in assigned_tools  # Additional

    def test_create_agent_with_configuration_overrides(self):
        """Test creating agent with configuration overrides."""
        factory = AgentFactory(str(self.roles_dir))

        config_overrides = {
            "custom_setting": "value",
            "timeout": 30
        }

        session_id = factory.create_agent(
            "test_agent",
            configuration_overrides=config_overrides
        )

        agent = factory.get_agent(session_id)
        assert agent.agent_definition.configuration["custom_setting"] == "value"
        assert agent.agent_definition.configuration["timeout"] == 30

    def test_terminate_agent(self):
        """Test terminating an agent."""
        factory = AgentFactory(str(self.roles_dir))

        session_id = factory.create_agent("test_agent")
        assert factory.get_agent(session_id) is not None

        success = factory.terminate_agent(session_id)
        assert success is True
        assert factory.get_agent(session_id) is None

    def test_get_active_agents(self):
        """Test getting active agents."""
        factory = AgentFactory(str(self.roles_dir))

        # Create multiple agents
        session_ids = []
        for i in range(3):
            session_id = factory.create_agent("test_agent")
            session_ids.append(session_id)

        active_agents = factory.get_active_agents()
        assert len(active_agents) == 3

        # Terminate one agent
        factory.terminate_agent(session_ids[0])
        active_agents = factory.get_active_agents()
        assert len(active_agents) == 2

    def test_update_agent_context(self):
        """Test updating agent context."""
        factory = AgentFactory(str(self.roles_dir))

        session_id = factory.create_agent("test_agent", {"initial": "context"})

        context_updates = {
            "new_data": "value",
            "updated_field": "new_value"
        }

        success = factory.update_agent_context(session_id, context_updates)
        assert success is True

        agent = factory.get_agent(session_id)
        assert agent.session_context["initial"] == "context"
        assert agent.session_context["new_data"] == "value"
        assert agent.session_context["updated_field"] == "new_value"

    def test_get_performance_metrics(self):
        """Test getting performance metrics."""
        factory = AgentFactory(str(self.roles_dir))

        # Create some agents to generate metrics
        for _ in range(2):
            session_id = factory.create_agent("test_agent")
            factory.terminate_agent(session_id)

        metrics = factory.get_performance_metrics()

        assert metrics["agents_created"] == 2
        assert metrics["agents_spawned"] == 2
        assert metrics["available_roles"] == 1
        assert metrics["available_tools"] == 10
        assert "average_creation_time" in metrics
        assert metrics["average_creation_time"] >= 0

    def test_reload_role_definitions(self):
        """Test reloading role definitions."""
        factory = AgentFactory(str(self.roles_dir))
        initial_count = len(factory.get_available_roles())

        # Add new role definition
        new_role_data = {
            "role_name": "new_test_agent",
            "description": "New test agent",
            "responsibilities": ["New testing"],
            "required_skills": ["Python"],
            "workflows": ["New workflow"],
            "collaboration": {}
        }

        new_role_file = self.roles_dir / "new_test_agent.yaml"
        with open(new_role_file, 'w') as f:
            yaml.dump(new_role_data, f)

        new_count = factory.reload_role_definitions()
        assert new_count == initial_count + 1
        assert "new_test_agent" in factory.get_available_roles()

    def test_context_manager(self):
        """Test AgentFactory as context manager."""
        with AgentFactory(str(self.roles_dir)) as factory:
            session_id = factory.create_agent("test_agent")
            assert factory.get_agent(session_id) is not None

        # After context exit, agent should be terminated
        assert factory.get_agent(session_id) is None

    @patch('agent_factory.agent_factory.store_to_cks')
    def test_agent_creation_record_storage(self, mock_store_to_cks):
        """Test that agent creation records are stored in CKS."""
        mock_store_to_cks.return_value = True

        factory = AgentFactory(str(self.roles_dir))
        session_id = factory.create_agent("test_agent", {"project": "test"})

        # Verify CKS storage was called
        mock_store_to_ks.assert_called_once()
        call_args = mock_store_to_cks.call_args
        assert "Create test_agent agent" in call_args[0][0]
        assert "Agent Creation Success" in call_args[0][1]


class TestCreateAgentFactory:
    """Test suite for create_agent_factory convenience function."""

    def test_create_agent_factory_default(self):
        """Test creating factory with default roles directory."""
        factory = create_agent_factory()
        assert isinstance(factory, AgentFactory)
        assert factory.roles_directory is not None

    def test_create_agent_factory_custom_directory(self):
        """Test creating factory with custom roles directory."""
        temp_dir = tempfile.mkdtemp()
        try:
            factory = create_agent_factory(temp_dir)
            assert isinstance(factory, AgentFactory)
            assert str(factory.roles_directory) == temp_dir
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestIntegrationWithExistingComponents:
    """Integration tests with existing CSF NIP components."""

    @patch('agent_factory.agent_factory.store_to_cks')
    @patch('agent_factory.agent_factory.query_cks')
    def test_cks_integration(self, mock_query, mock_store):
        """Test integration with CKS (Cognitive Knowledge System)."""
        mock_store.return_value = True
        mock_query.return_value = []

        temp_dir = tempfile.mkdtemp()
        try:
            roles_dir = Path(temp_dir) / "roles"
            roles_dir.mkdir()

            role_data = {
                "role_name": "test_agent",
                "description": "Test agent",
                "responsibilities": ["Testing"],
                "required_skills": ["Python"],
                "workflows": ["Test workflow"],
                "collaboration": {}
            }

            role_file = roles_dir / "test_agent.yaml"
            with open(role_file, 'w') as f:
                yaml.dump(role_data, f)

            factory = AgentFactory(str(roles_dir))
            session_id = factory.create_agent("test_agent")

            # Verify CKS integration was called
            mock_store.assert_called()

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
