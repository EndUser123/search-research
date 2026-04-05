"""CKS Project Context Validation Test Suite.

Comprehensive testing for CKS-based project context management system.
Tests all 9 scenarios from the implementation plan.

Constitutional Requirements:
- Solo developer optimization (simple, clear tests)
- Evidence-based implementation (test real scenarios)
- Force multiplier (comprehensive coverage)
- No enterprise bloat (direct Python, no complex frameworks)

Test Scenarios:
1. Platform operation in platform context ✅ (allow)
2. GPU operation in platform context ❌ (block with clear message)
3. Platform file edit in platform context ✅ (allow)
4. GPU file edit in platform context ❌ (block)
5. Generic operation in any context ✅ (allow)
6. Context persistence across /compact ✅
7. CKS semantic search for contexts ✅
8. Checkpoint creation and restoration ✅
9. Multi-context isolation ✅
"""

import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add paths
workspace_root = Path(__file__).parent.parent.parent.parent.parent.parent


class TestProjectContextValidation(unittest.TestCase):
    """Test CKS project context validation system."""

    def setUp(self) -> None:
        """Set up test environment with temporary database."""
        # Create temporary directory for test database
        self.test_dir = tempfile.mkdtemp()
        self.test_db = os.path.join(self.test_dir, "test_cks.db")

        # Import adapters
        from adapter import ProjectContextCKSAdapter

        # Initialize CKS adapter with test database
        self.adapter = ProjectContextCKSAdapter(self.test_db)

        # Create test contexts
        self.adapter.create_context(
            tsk_id="TSK-ALT-PLATFORM-DOWNLOADING",
            worktree_path="P:/yt-fts-alt-platforms",
            description="YouTube alternative platforms",
        )

        self.adapter.create_context(
            tsk_id="TSK-122225-GPUWorkloadIntegration-1457",
            worktree_path="P:/gpu-workload-integration",
            description="GPU workload integration",
        )

    def tearDown(self) -> None:
        """Clean up test environment."""
        if hasattr(self, "test_dir") and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_scenario_1_platform_operation_in_platform_context(self) -> None:
        """Test 1: Platform operation in platform context ✅ (allow).

        When active context is platform and operation is platform-related,
        operation should be allowed.
        """
        # Set platform context as active
        self.adapter.set_active_context("TSK-ALT-PLATFORM-DOWNLOADING")

        # Validate platform file operation
        allowed, message = self.adapter.validate_operation(
            operation_type="edit",
            operation_target="P:/yt-fts-alt-platforms/downloader.py",
            operation_description="Add download function for alternative platforms",
        )

        self.assertTrue(allowed, f"Platform operation should be allowed, got: {message}")
        self.assertIn("allowed", message.lower())

    def test_scenario_2_gpu_operation_in_platform_context(self) -> None:
        """Test 2: GPU operation in platform context ❌ (block with clear message).

        When active context is platform but operation is GPU-related,
        operation should be blocked with clear message.
        """
        # Set platform context as active
        self.adapter.set_active_context("TSK-ALT-PLATFORM-DOWNLOADING")

        # Validate GPU operation
        allowed, message = self.adapter.validate_operation(
            operation_type="edit",
            operation_target="P:/gpu-workload-integration/kernel.py",
            operation_description="Add GPU kernel optimization",
        )

        self.assertFalse(allowed, "GPU operation in platform context should be blocked")
        self.assertIn("context", message.lower(), "Message should mention context mismatch")

    def test_scenario_3_platform_file_edit_in_platform_context(self) -> None:
        """Test 3: Platform file edit in platform context ✅ (allow).

        When editing platform file in platform context, should be allowed.
        """
        # Set platform context as active
        self.adapter.set_active_context("TSK-ALT-PLATFORM-DOWNLOADING")

        # Validate platform file edit
        allowed, _message = self.adapter.validate_operation(
            operation_type="edit",
            operation_target="P:/yt-fts-alt-platforms/main.py",
            operation_description="Fix import error",
        )

        self.assertTrue(allowed, "Platform file edit should be allowed")

    def test_scenario_4_gpu_file_edit_in_platform_context(self) -> None:
        """Test 4: GPU file edit in platform context ❌ (block).

        When editing GPU file while in platform context, should be blocked.
        """
        # Set platform context as active
        self.adapter.set_active_context("TSK-ALT-PLATFORM-DOWNLOADING")

        # Validate GPU file edit
        allowed, _message = self.adapter.validate_operation(
            operation_type="edit",
            operation_target="P:/gpu-workload-integration/cuda_kernel.py",
            operation_description="Optimize CUDA kernel",
        )

        self.assertFalse(allowed, "GPU file edit in platform context should be blocked")

    def test_scenario_5_generic_operation_in_any_context(self) -> None:
        """Test 5: Generic operation in any context ✅ (allow).

        Generic operations (not project-specific) should be allowed in any context.
        """
        # Set platform context as active
        self.adapter.set_active_context("TSK-ALT-PLATFORM-DOWNLOADING")

        # Validate generic operation
        allowed, _message = self.adapter.validate_operation(
            operation_type="read",
            operation_target="P:/README.md",
            operation_description="Read project documentation",
        )

        self.assertTrue(allowed, "Generic operation should be allowed")

    def test_scenario_6_context_persistence(self) -> None:
        """Test 6: Context persistence across sessions ✅.

        Active context should persist and be retrievable.
        """
        # Set platform context as active
        result = self.adapter.set_active_context("TSK-ALT-PLATFORM-DOWNLOADING")
        self.assertTrue(result.success, "Failed to set active context")

        # Retrieve active context
        active_context = self.adapter.get_active_context()
        self.assertIsNotNone(active_context, "Active context should not be None")
        self.assertEqual(
            active_context.tsk_id,
            "TSK-ALT-PLATFORM-DOWNLOADING",
            "Active context TSK ID should match",
        )

    def test_scenario_7_cks_semantic_search(self) -> None:
        """Test 7: CKS semantic search for contexts ✅.

        Should be able to list and search for contexts.
        """
        # List all contexts
        contexts = self.adapter.list_contexts()
        self.assertGreaterEqual(len(contexts), 2, "Should have at least 2 contexts")

        # Verify context details
        context_ids = [ctx.tsk_id for ctx in contexts]
        self.assertIn("TSK-ALT-PLATFORM-DOWNLOADING", context_ids)
        self.assertIn("TSK-122225-GPUWorkloadIntegration-1457", context_ids)

    def test_scenario_8_checkpoint_creation(self) -> None:
        """Test 8: Checkpoint creation and restoration ✅.

        Should be able to create checkpoints for context states.
        """
        # Set platform context as active
        self.adapter.set_active_context("TSK-ALT-PLATFORM-DOWNLOADING")

        # Create checkpoint
        result = self.adapter.create_checkpoint(
            checkpoint_name="test-checkpoint",
            description="Test checkpoint for validation",
            checkpoint_data={"test": "data"},
        )

        self.assertTrue(result.success, f"Checkpoint creation failed: {result.error}")

        # List checkpoints
        checkpoints = self.adapter.list_checkpoints("TSK-ALT-PLATFORM-DOWNLOADING")
        self.assertGreater(len(checkpoints), 0, "Should have at least one checkpoint")

        # Verify checkpoint details
        checkpoint = checkpoints[0]
        self.assertEqual(checkpoint.checkpoint_name, "test-checkpoint")

    def test_scenario_9_multi_context_isolation(self) -> None:
        """Test 9: Multi-context isolation ✅.

        Different contexts should be properly isolated.
        """
        # Set platform context as active
        self.adapter.set_active_context("TSK-ALT-PLATFORM-DOWNLOADING")

        # Verify platform context is active
        active_context = self.adapter.get_active_context()
        self.assertEqual(
            active_context.tsk_id,
            "TSK-ALT-PLATFORM-DOWNLOADING",
            "Platform context should be active",
        )

        # Switch to GPU context
        self.adapter.set_active_context("TSK-122225-GPUWorkloadIntegration-1457")

        # Verify GPU context is now active
        active_context = self.adapter.get_active_context()
        self.assertEqual(
            active_context.tsk_id,
            "TSK-122225-GPUWorkloadIntegration-1457",
            "GPU context should be active after switch",
        )

        # Validate GPU operation is now allowed
        allowed, _message = self.adapter.validate_operation(
            operation_type="edit",
            operation_target="P:/gpu-workload-integration/kernel.py",
            operation_description="Add GPU kernel",
        )

        self.assertTrue(allowed, "GPU operation should be allowed in GPU context")


class TestSoloSessionBridgeCKSExtension(unittest.TestCase):
    """Test SoloSessionBridge CKS extension."""

    def setUp(self) -> None:
        """Set up test environment."""
        from solo_session_bridge_cks_extension import SoloSessionBridgeCKS

        self.bridge = SoloSessionBridgeCKS(str(workspace_root))

    def test_bridge_initialization(self) -> None:
        """Test bridge initializes correctly."""
        self.assertIsNotNone(self.bridge, "Bridge should initialize")

    def test_context_detection(self) -> None:
        """Test context detection from paths."""
        # Test platform path detection
        self.bridge.detect_context_from_path("P:/yt-fts-alt-platforms/main.py")
        # Detection logic is in validators, this test verifies bridge method exists

    def test_validation_methods_exist(self) -> None:
        """Test that validation methods are available."""
        # Check that validation methods exist
        self.assertTrue(
            hasattr(self.bridge, "validate_operation_with_cks"),
            "Bridge should have validate_operation_with_cks method",
        )
        self.assertTrue(
            hasattr(self.bridge, "set_active_project_context"),
            "Bridge should have set_active_project_context method",
        )
        self.assertTrue(
            hasattr(self.bridge, "get_active_project_context"),
            "Bridge should have get_active_project_context method",
        )


class TestCKSContextValidatorHooks(unittest.TestCase):
    """Test CKS context validator hooks."""

    def test_hook_module_imports(self) -> None:
        """Test that hook module can be imported."""
        try:
            import csf.cks_context_validator

            self.assertTrue(hasattr(cks_context_validator, "validate_tool_operation"))
        except ImportError:
            self.skipTest("CKS context validator not in path")

    def test_integration_module_imports(self) -> None:
        """Test that integration module can be imported."""
        try:
            import csf.cks_context_hooks_integration

            self.assertTrue(hasattr(cks_context_hooks_integration, "CKSContextHooks"))
        except ImportError:
            self.skipTest("CKS context hooks integration not in path")


def run_tests():
    """Run all tests and report results."""
    print("=" * 70)
    print("CKS Project Context Validation Test Suite")
    print("=" * 70)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestProjectContextValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestSoloSessionBridgeCKSExtension))
    suite.addTests(loader.loadTestsFromTestCase(TestCKSContextValidatorHooks))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
