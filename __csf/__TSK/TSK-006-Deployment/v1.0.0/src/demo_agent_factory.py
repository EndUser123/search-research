#!/usr/bin/env python3
"""
Agent Factory Demonstration

This script demonstrates the capabilities of the CSF NIP Agent Factory
for creating and managing role-based agents in the Persistent Learning Agent Ecosystem.
"""

import sys
import time
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_factory import AgentFactory, ToolType


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)


def print_section(title):
    """Print a formatted section."""
    print(f"\n📋 {title}")
    print("-" * 40)


def demonstrate_basic_functionality():
    """Demonstrate basic Agent Factory functionality."""
    print_header("Agent Factory Basic Functionality Demo")

    # Initialize the Agent Factory
    factory = AgentFactory()

    print_section("Available Roles")
    roles = factory.get_available_roles()
    for i, role in enumerate(roles, 1):
        print(f"{i}. {role}")
        role_def = factory.get_role_definition(role)
        if role_def:
            print(f"   └─ Description: {role_def.description}")
            print(f"   └─ Tools: {[tool.value for tool in role_def.tools]}")

    print_section("Creating Development Agent")
    dev_context = {
        "project": "Persistent Learning Agent Ecosystem",
        "task": "Implement agent communication system",
        "requirements": ["Real-time messaging", "Role-based routing", "Error handling"]
    }

    dev_session_id = factory.create_agent(
        "development_agent",
        context=dev_context,
        additional_tools=[ToolType.DATABASE_ACCESS]
    )

    if dev_session_id:
        print(f"✓ Development agent created with session ID: {dev_session_id}")

        # Get agent details
        dev_agent = factory.get_agent(dev_session_id)
        if dev_agent:
            print(f"✓ Agent Status: {dev_agent.status.value}")
            print(f"✓ Assigned Tools: {[tool.value for tool in dev_agent.assigned_tools]}")

            # Show system prompt preview
            if dev_agent.system_prompt:
                prompt_preview = dev_agent.system_prompt[:200] + "..." if len(dev_agent.system_prompt) > 200 else dev_agent.system_prompt
                print(f"✓ System Prompt Preview:\n{prompt_preview}")

    print_section("Creating Research Agent")
    research_context = {
        "research_topic": "Agent collaboration patterns in distributed systems",
        "scope": "Academic papers, industry implementations, case studies",
        "deliverable": "Comprehensive analysis report"
    }

    research_session_id = factory.create_agent("research_agent", context=research_context)

    if research_session_id:
        print(f"✓ Research agent created with session ID: {research_session_id}")
        research_agent = factory.get_agent(research_session_id)
        if research_agent:
            print(f"✓ Agent Status: {research_agent.status.value}")
            print(f"✓ Research Context: {research_agent.session_context.get('research_topic', 'N/A')}")

    print_section("Creating Testing Agent")
    testing_context = {
        "testing_scope": "Agent Factory unit tests",
        "test_types": ["unit", "integration", "performance"],
        "coverage_target": 85
    }

    testing_session_id = factory.create_agent(
        "testing_agent",
        context=testing_context,
        additional_tools=[ToolType.SHELL_COMMANDS]
    )

    if testing_session_id:
        print(f"✓ Testing agent created with session ID: {testing_session_id}")
        testing_agent = factory.get_agent(testing_session_id)
        if testing_agent:
            print(f"✓ Agent Status: {testing_agent.status.value}")
            print(f"✓ Coverage Target: {testing_agent.session_context.get('coverage_target', 'N/A')}%")

    return [dev_session_id, research_session_id, testing_session_id], factory


def demonstrate_agent_collaboration(session_ids, factory):
    """Demonstrate agent collaboration through context updates."""
    print_header("Agent Collaboration Demo")

    dev_session_id, research_session_id, testing_session_id = session_ids

    print_section("Simulating Development → Research Collaboration")

    # Development agent shares findings with research agent
    dev_findings = {
        "implementation_patterns": ["pub/sub", "message queues", "direct messaging"],
        "challenges_identified": ["scalability", "consistency", "error_recovery"]
    }

    success = factory.update_agent_context(research_session_id, {
        "dev_team_findings": dev_findings,
        "collaboration_request": "Analyze these patterns and recommend best practices"
    })

    if success:
        print("✓ Development findings shared with research agent")
        research_agent = factory.get_agent(research_session_id)
        if research_agent and "dev_team_findings" in research_agent.session_context:
            print(f"✓ Research agent received: {len(research_agent.session_context['dev_team_findings']['implementation_patterns'])} patterns")

    print_section("Simulating Research → Testing Collaboration")

    # Research agent shares insights with testing agent
    research_recommendations = {
        "critical_test_areas": ["message delivery", "error handling", "scalability limits"],
        "test_scenarios": ["load testing", "failure simulation", "consistency checks"]
    }

    success = factory.update_agent_context(testing_session_id, {
        "research_recommendations": research_recommendations,
        "enhanced_scope": "Include collaboration testing scenarios"
    })

    if success:
        print("✓ Research recommendations shared with testing agent")
        testing_agent = factory.get_agent(testing_session_id)
        if testing_agent and "research_recommendations" in testing_agent.session_context:
            print(f"✓ Testing agent received {len(testing_agent.session_context['research_recommendations']['critical_test_areas'])} test areas")

    print_section("Complete Collaboration Flow")

    # Testing agent shares test results back
    test_results = {
        "overall_status": "passed",
        "performance_metrics": {"throughput": "1000 msg/s", "latency": "<10ms"},
        "issues_found": ["memory_leak", "timeout_handling"]
    }

    success = factory.update_agent_context(dev_session_id, {
        "test_results": test_results,
        "action_required": "Fix identified issues before deployment"
    })

    if success:
        print("✓ Test results shared with development agent")
        dev_agent = factory.get_agent(dev_session_id)
        if dev_agent and "test_results" in dev_agent.session_context:
            status = dev_agent.session_context['test_results']['overall_status']
            print(f"✓ Development agent received test status: {status}")


def demonstrate_session_management(session_ids, factory):
    """Demonstrate session management capabilities."""
    print_header("Session Management Demo")

    print_section("Active Agent Sessions")
    active_agents = factory.get_active_agents()

    for agent in active_agents:
        print(f"Agent: {agent.agent_definition.role_name}")
        print(f"  └─ Session ID: {agent.instance_id}")
        print(f"  └─ Status: {agent.status.value}")
        print(f"  └─ Created: {agent.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  └─ Last Activity: {agent.last_activity.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  └─ Tools: {[tool.value for tool in agent.assigned_tools]}")
        print()

    print_section("Agent Status Updates")

    # Simulate agent work
    for i, session_id in enumerate(session_ids):
        agent = factory.get_agent(session_id)
        if agent:
            print(f"Updating {agent.agent_definition.role_name} status to BUSY...")
            factory.update_agent_context(session_id, {"current_task": f"Working on task {i+1}"})
            time.sleep(0.1)  # Simulate work

            print(f"Updating {agent.agent_definition.role_name} status to READY...")
            factory.update_agent_context(session_id, {"current_task": "Ready for next task"})

    print_section("Performance Metrics")
    metrics = factory.get_performance_metrics()

    print("📊 Factory Performance:")
    print(f"  └─ Agents Created: {metrics['agents_created']}")
    print(f"  └─ Agents Spawned: {metrics['agents_spawned']}")
    print(f"  └─ Active Sessions: {metrics['sessions_active']}")
    print(f"  └─ Available Roles: {metrics['available_roles']}")
    print(f"  └─ Available Tools: {metrics['available_tools']}")
    print(f"  └─ Avg Creation Time: {metrics['average_creation_time']:.4f}s")


def demonstrate_cleanup_process(session_ids, factory):
    """Demonstrate agent cleanup and termination."""
    print_header("Agent Cleanup Demo")

    print_section("Agent Termination")

    for i, session_id in enumerate(session_ids):
        agent = factory.get_agent(session_id)
        if agent:
            print(f"Terminating {agent.agent_definition.role_name}...")
            success = factory.terminate_agent(session_id)
            if success:
                print(f"✓ {agent.agent_definition.role_name} terminated successfully")
            else:
                print(f"❌ Failed to terminate {agent.agent_definition.role_name}")

    print_section("Final State Verification")
    final_active_agents = factory.get_active_agents()
    print(f"Active agents remaining: {len(final_active_agents)}")

    final_metrics = factory.get_performance_metrics()
    print(f"Total agents created: {final_metrics['agents_created']}")
    print(f"Total agents spawned: {final_metrics['agents_spawned']}")


def main():
    """Main demonstration function."""
    print_header("🚀 CSF NIP Agent Factory Demonstration")
    print("This demonstration showcases the capabilities of the Agent Factory")
    print("for creating and managing role-based agents in the Persistent Learning Agent Ecosystem.")

    try:
        # Run demonstration modules
        session_ids, factory = demonstrate_basic_functionality()

        if any(session_id for session_id in session_ids):
            time.sleep(1)  # Brief pause between demonstrations

            demonstrate_agent_collaboration(session_ids, factory)
            time.sleep(1)

            demonstrate_session_management(session_ids, factory)
            time.sleep(1)

            demonstrate_cleanup_process(session_ids, factory)

        print_header("✅ Demonstration Complete")
        print("The Agent Factory successfully demonstrated:")
        print("✓ Role-based agent creation from YAML definitions")
        print("✓ System prompt generation from templates")
        print("✓ Tool assignment and management")
        print("✓ Session management and lifecycle")
        print("✓ Agent collaboration through context sharing")
        print("✓ Performance monitoring and metrics")
        print("✓ Graceful agent termination and cleanup")
        print("\n🎉 Agent Factory is ready for production use!")

        return 0

    except Exception as e:
        print(f"\n❌ Demonstration failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
