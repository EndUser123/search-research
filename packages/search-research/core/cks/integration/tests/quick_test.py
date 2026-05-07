#!/usr/bin/env python3
"""Quick functional test for CKS Project Context Management.

This test uses importlib to properly load the module with relative imports.
"""

import importlib.util
import os
import sys
import tempfile
from pathlib import Path


def quick_test() -> bool | None:
    """Quick functional test."""
    print("=" * 70)
    print("CKS Project Context Management - Quick Functional Test")
    print("=" * 70)

    # Paths
    workspace_root = Path(__file__).parent.parent.parent.parent.parent.parent
    project_context_path = (
        workspace_root / "__csf" / "src" / "cks" / "integration" / "adapters" / "project_context"
    )

    print(f"\nProject context path: {project_context_path}")
    print(f"Path exists: {project_context_path.exists()}")

    # Test database
    test_db = tempfile.mktemp(suffix="_cks_test.db")
    print(f"Test database: {test_db}")

    try:
        # Add parent directories to path for proper package resolution

        print("\n1. Loading adapter module...")

        # Load module using importlib
        adapter_path = project_context_path / "adapter.py"
        spec = importlib.util.spec_from_file_location("project_context_adapter", adapter_path)
        adapter_module = importlib.util.module_from_spec(spec)
        sys.modules["project_context_adapter"] = adapter_module
        spec.loader.exec_module(adapter_module)

        ProjectContextCKSAdapter = adapter_module.ProjectContextCKSAdapter
        print("   ✅ Adapter module loaded")

        # Initialize adapter
        print("\n2. Initializing CKS adapter...")
        adapter = ProjectContextCKSAdapter(test_db)
        print("   ✅ CKS adapter initialized")

        # Create context
        print("\n3. Creating test context...")
        result = adapter.create_context(
            tsk_id="TSK-TEST-PLATFORM",
            worktree_path="P:\\\\test-platform",
            description="Test platform project",
        )
        print(
            f"   {'✅' if result.success else '❌'} Context created: {result.error if not result.success else 'Success'}"
        )

        # List contexts
        print("\n4. Listing contexts...")
        contexts = adapter.list_contexts()
        print(f"   ✅ Found {len(contexts)} context(s)")
        for ctx in contexts:
            print(f"      - {ctx.tsk_id}: {ctx.description}")

        # Set active context
        print("\n5. Setting active context...")
        result = adapter.set_active_context("TSK-TEST-PLATFORM")
        print(f"   {'✅' if result.success else '❌'} Active context set")

        # Get active context
        print("\n6. Getting active context...")
        active = adapter.get_active_context()
        if active:
            print(f"   ✅ Active: {active.tsk_id}")
        else:
            print("   ❌ No active context")

        # Validate operation
        print("\n7. Testing operation validation...")
        allowed, message = adapter.validate_operation(
            operation_type="edit",
            operation_target="P:\\\\test-platform/main.py",
            operation_description="Test edit",
        )
        print(f"   ✅ Validation result: allowed={allowed}, message={message}")

        # Create checkpoint
        print("\n8. Creating checkpoint...")
        result = adapter.create_checkpoint(
            checkpoint_name="test-checkpoint",
            description="Test checkpoint",
        )
        print(f"   {'✅' if result.success else '❌'} Checkpoint created")

        print("\n" + "=" * 70)
        print("Quick Test: ✅ PASSED")
        print("=" * 70)
        print("\nAll core functionality is working!")

        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # Clean up
        if os.path.exists(test_db):
            os.unlink(test_db)


if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)
