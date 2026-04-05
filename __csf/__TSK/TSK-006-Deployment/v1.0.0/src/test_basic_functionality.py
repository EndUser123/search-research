#!/usr/bin/env python3
"""
Basic functionality test for Agent Factory
Simplified test to verify core functionality works correctly.
"""

import shutil
import sys
import tempfile
from pathlib import Path

import yaml

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_factory import AgentFactory, ToolType


def test_basic_agent_creation():
    """Test basic agent creation functionality."""
    print("Testing basic agent creation...")

    # Create temporary directory for roles
    temp_dir = tempfile.mkdtemp()
    roles_dir = Path(temp_dir) / "roles"
    roles_dir.mkdir()

    try:
        # Create a simple test role
        role_data = {
            "role_name": "test_agent",
            "description": "Test agent for basic functionality test",
            "responsibilities": ["Testing functionality"],
            "required_skills": ["Python"],
            "workflows": ["Test workflow"],
            "collaboration": {"primary_partners": ["dev_agent"]},
            "tools": ["file_operations"]
        }

        role_file = roles_dir / "test_agent.yaml"
        with open(role_file, 'w') as f:
            yaml.dump(role_data, f)

        # Test Agent Factory initialization
        factory = AgentFactory(str(roles_dir))
        available_roles = factory.get_available_roles()

        assert "test_agent" in available_roles, f"Expected 'test_agent' in roles, got: {available_roles}"
        print("✓ Agent Factory initialization successful")

        # Test agent creation
        context = {"project": "test_project", "task": "basic_test"}
        session_id = factory.create_agent("test_agent", context)

        assert session_id is not None, "Agent creation failed - session_id is None"
        print(f"✓ Agent created successfully with session ID: {session_id}")

        # Test agent retrieval
        agent = factory.get_agent(session_id)
        assert agent is not None, "Failed to retrieve created agent"
        assert agent.session_context == context, "Agent context not set correctly"
        print("✓ Agent retrieval successful")

        # Test tool assignment
        assigned_tools = factory.get_agent_tools(session_id)
        assert ToolType.FILE_OPERATIONS in assigned_tools, "File operations tool not assigned"
        print("✓ Tool assignment working correctly")

        # Test agent termination
        success = factory.terminate_agent(session_id)
        assert success is True, "Agent termination failed"
        print("✓ Agent termination successful")

        # Verify agent is no longer available
        agent = factory.get_agent(session_id)
        assert agent is None, "Terminated agent still accessible"
        print("✓ Agent properly terminated")

        # Test performance metrics
        metrics = factory.get_performance_metrics()
        assert metrics["agents_created"] >= 1, "Agent creation not counted in metrics"
        assert metrics["agents_spawned"] >= 1, "Agent spawn not counted in metrics"
        print(f"✓ Performance metrics working: {metrics}")

        print("\n✅ All basic functionality tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Clean up
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_role_definitions():
    """Test role definition loading and validation."""
    print("Testing role definitions...")

    temp_dir = tempfile.mkdtemp()
    roles_dir = Path(temp_dir) / "roles"
    roles_dir.mkdir()

    try:
        # Test multiple role definitions
        roles = [
            {
                "role_name": "development_agent",
                "description": "Development agent",
                "responsibilities": ["Coding", "Debugging"],
                "required_skills": ["Python", "JavaScript"],
                "workflows": ["Dev workflow"],
                "collaboration": {"primary_partners": ["testing_agent"]},
                "tools": ["file_operations", "git_operations"],
                "capabilities": ["Full-stack development"],
                "constraints": ["Follow coding standards"]
            },
            {
                "role_name": "testing_agent",
                "description": "Testing agent",
                "responsibilities": ["Testing", "Quality assurance"],
                "required_skills": ["Testing frameworks"],
                "workflows": ["Test workflow"],
                "collaboration": {"primary_partners": ["development_agent"]},
                "tools": ["validation", "file_operations"]
            }
        ]

        for role in roles:
            role_file = roles_dir / f"{role['role_name']}.yaml"
            with open(role_file, 'w') as f:
                yaml.dump(role, f)

        factory = AgentFactory(str(roles_dir))
        available_roles = factory.get_available_roles()

        assert len(available_roles) == 2, f"Expected 2 roles, got {len(available_roles)}"
        assert "development_agent" in available_roles, "development_agent not found"
        assert "testing_agent" in available_roles, "testing_agent not found"
        print("✓ Multiple role definitions loaded successfully")

        # Test role definition retrieval
        dev_role = factory.get_role_definition("development_agent")
        assert dev_role is not None, "Failed to get development_agent definition"
        assert dev_role.description == "Development agent", "Role description incorrect"
        assert ToolType.GIT_OPERATIONS in dev_role.tools, "Git tool not found in role"
        print("✓ Role definition retrieval working correctly")

        print("✅ Role definition tests passed!")
        return True

    except Exception as e:
        print(f"❌ Role definition test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    """Run all tests."""
    print("🚀 Starting Agent Factory Basic Functionality Tests\n")

    tests_passed = 0
    total_tests = 2

    # Run tests
    if test_basic_agent_creation():
        tests_passed += 1

    if test_role_definitions():
        tests_passed += 1

    # Summary
    print(f"\n📊 Test Summary: {tests_passed}/{total_tests} tests passed")

    if tests_passed == total_tests:
        print("🎉 All tests passed! Agent Factory is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    exit(main())
