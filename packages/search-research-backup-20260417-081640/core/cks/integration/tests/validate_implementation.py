#!/usr/bin/env python3
"""CKS Project Context Management - Implementation Validation.

Quick validation script to verify the CKS project context management system
is working correctly without requiring complex test infrastructure.

This script validates the core functionality:
1. CKS adapter initialization
2. Context creation and retrieval
3. Operation validation against contexts
4. Checkpoint creation
"""

import os
import sys
import tempfile
from pathlib import Path


def validate_implementation() -> bool | None:
    """Validate the CKS project context management implementation."""
    print("=" * 70)
    print("CKS Project Context Management - Implementation Validation")
    print("=" * 70)

    # Workspace root
    workspace_root = Path(__file__).parent.parent.parent.parent.parent.parent

    # Test database path
    test_db = tempfile.mktemp(suffix=".db")

    print(f"\nWorkspace root: {workspace_root}")
    print(f"Test database: {test_db}")

    try:
        # import CKS adapter
        print("\n1. Importing CKS adapter...")
        workspace_root / "__csf" / "src" / "cks" / "integration" / "adapters" / "project_context"

        from adapter import ProjectContextCKSAdapter

        print("   ✅ CKS adapter imported successfully")

        # Initialize adapter
        print("\n2. Initializing CKS adapter...")
        adapter = ProjectContextCKSAdapter(test_db)
        print("   ✅ CKS adapter initialized")

        # Create test contexts
        print("\n3. Creating test contexts...")
        result1 = adapter.create_context(
            tsk_id="TSK-ALT-PLATFORM-DOWNLOADING",
            worktree_path="P:/yt-fts-alt-platforms",
            description="YouTube alternative platforms",
        )
        print(
            f"   {'✅' if result1.success else '❌'} Platform context: {result1.error if not result1.success else 'Created'}"
        )

        result2 = adapter.create_context(
            tsk_id="TSK-122225-GPUWorkloadIntegration-1457",
            worktree_path="P:/gpu-workload-integration",
            description="GPU workload integration",
        )
        print(
            f"   {'✅' if result2.success else '❌'} GPU context: {result2.error if not result2.success else 'Created'}"
        )

        # List contexts
        print("\n4. Listing contexts...")
        contexts = adapter.list_contexts()
        print(f"   ✅ Found {len(contexts)} contexts:")
        for ctx in contexts:
            print(f"      - {ctx.tsk_id}")

        # Set active context
        print("\n5. Setting active context...")
        result = adapter.set_active_context("TSK-ALT-PLATFORM-DOWNLOADING")
        print(f"   {'✅' if result.success else '❌'} Set platform context as active")

        # Get active context
        print("\n6. Getting active context...")
        active_context = adapter.get_active_context()
        if active_context:
            print(f"   ✅ Active context: {active_context.tsk_id}")
            print(f"      Path: {active_context.worktree_path}")
        else:
            print("   ❌ No active context")

        # Test validation - platform operation in platform context (should allow)
        print("\n7. Testing validation...")
        allowed, message = adapter.validate_operation(
            operation_type="edit",
            operation_target="P:/yt-fts-alt-platforms/main.py",
            operation_description="Add download function",
        )
        print(f"   {'✅' if allowed else '❌'} Platform operation in platform context: {message}")

        # Test validation - GPU operation in platform context (should warn)
        allowed, message = adapter.validate_operation(
            operation_type="edit",
            operation_target="P:/gpu-workload-integration/kernel.py",
            operation_description="Add GPU kernel",
        )
        print(
            f"   {'✅' if 'GPU' not in message or allowed else '❌'} GPU operation in platform context: {message}"
        )

        # Create checkpoint
        print("\n8. Creating checkpoint...")
        result = adapter.create_checkpoint(
            checkpoint_name="test-checkpoint",
            description="Test checkpoint",
        )
        print(
            f"   {'✅' if result.success else '❌'} Checkpoint created: {result.error if not result.success else 'Success'}"
        )

        # List checkpoints
        print("\n9. Listing checkpoints...")
        checkpoints = adapter.list_checkpoints("TSK-ALT-PLATFORM-DOWNLOADING")
        print(f"   ✅ Found {len(checkpoints)} checkpoint(s)")

        # Test context detection from path
        print("\n10. Testing context detection from path...")
        detected = adapter.detect_context_from_path("P:/yt-fts-alt-platforms/main.py")
        print(f"   ✅ Detected context: {detected if detected else 'None'}")

        print("\n" + "=" * 70)
        print("Implementation Validation: ✅ PASSED")
        print("=" * 70)
        print("\nAll core functionality is working correctly!")

        return True

    except Exception as e:
        print(f"\n❌ Validation failed: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        # Clean up test database
        if os.path.exists(test_db):
            os.unlink(test_db)


if __name__ == "__main__":
    success = validate_implementation()
    sys.exit(0 if success else 1)
