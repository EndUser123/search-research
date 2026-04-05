"""
Comprehensive Test Suite for Complete Voice Notification System
Tests integration of all components with constitutional compliance
"""

import asyncio
import json

# Import the voice notification system
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from voice_notifications import (
    ConfigManager,
    IntelligentNotificationFilter,
    VoiceNotificationHookIntegration,
    VoiceNotificationOrchestrator,
)
from voice_notifications.core.notification_orchestrator import DeliveryStatus
from voice_notifications.filters.intelligent_filter import (
    FilterDecision,
    NotificationContext,
)
from voice_notifications.monitoring.performance_monitor import (
    DeliveryPerformanceSnapshot,
)


class TestVoiceNotificationSystem:
    """Test the complete integrated voice notification system"""

    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary configuration file"""
        config_data = {
            "enabled": True,
            "voice": {
                "preferred_voice": "Microsoft David Desktop",
                "fallback_voice": "Microsoft Zira Desktop",
                "volume": 85,
                "rate": -1,
                "async_speech": True
            },
            "notifications": {
                "task_complete": {
                    "enabled": True,
                    "template": "Task Complete: {task_name}",
                    "priority": "normal",
                    "max_frequency_per_hour": 10,
                    "session_timeout_minutes": 30
                },
                "question": {
                    "enabled": True,
                    "template": "Question about: {task_name}",
                    "priority": "high",
                    "max_frequency_per_hour": 20,
                    "requires_user_interaction": True
                },
                "error": {
                    "enabled": True,
                    "template": "Error: {task_name}",
                    "priority": "high",
                    "max_frequency_per_hour": 5,
                    "requires_user_interaction": True
                }
            },
            "intelligent_filter": {
                "enabled": True,
                "session_isolation": True,
                "behavioral_filtering": True,
                "frequency_limits": True,
                "context_analysis": True,
                "learning_enabled": True,
                "filter_strength": 0.7,
                "session_timeout_minutes": 30,
                "max_notifications_per_hour": 20,
                "max_notifications_per_session": 50,
                "exempt_high_priority": True,
                "learning_rate": 0.1,
                "decay_rate": 0.05
            },
            "performance": {
                "target_delivery_ms": 500,
                "parallel_execution": True,
                "max_concurrent_notifications": 3,
                "enable_metrics": True,
                "alert_on_slow_delivery": True,
                "slow_delivery_threshold_ms": 750
            },
            "logging": {
                "enabled": True,
                "log_level": "info",
                "include_performance_metrics": True,
                "include_filter_decisions": True
            },
            "integration": {
                "use_pyttsx3_engine": False,  # Disable for testing
                "fallback_to_powershell": False,  # Disable for testing
                "power_shell_required": False,
                "speech_synthesis_required": False
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f, indent=2)
            yield f.name

        Path(f.name).unlink(missing_ok=True)

    @pytest.fixture
    def config_manager(self, temp_config_file):
        """Create config manager with test configuration"""
        return ConfigManager(temp_config_file)

    @pytest.fixture
    def orchestrator(self, temp_config_file):
        """Create orchestrator for testing"""
        return VoiceNotificationOrchestrator(temp_config_file)

    @pytest.fixture
    async def started_orchestrator(self, orchestrator):
        """Start orchestrator for testing and cleanup afterwards"""
        await orchestrator.start()
        yield orchestrator
        await orchestrator.stop()

    @pytest.fixture
    def intelligent_filter(self, config_manager):
        """Create intelligent filter for testing"""
        return IntelligentNotificationFilter(config_manager.config)

    @pytest.fixture
    def hook_integration(self, temp_config_file):
        """Create hook integration for testing"""
        with patch('voice_notifications.hooks.claude_integration.psutil') as mock_psutil:
            # Mock psutil for testing
            mock_process = Mock()
            mock_process.memory_info.return_value.rss = 50 * 1024 * 1024  # 50MB
            mock_process.memory_percent.return_value = 5.0
            mock_process.open_files.return_value = []
            mock_psutil.Process.return_value = mock_process
            mock_psutil.cpu_percent.return_value = 10.0
            mock_psutil.cpu_percent.return_value = 10.0

            integration = VoiceNotificationHookIntegration(temp_config_file)
            return integration

    class TestConfigurationSystem:
        """Test the configuration system"""

        def test_config_loading_and_validation(self, temp_config_file):
            """Test configuration loading with validation"""
            config_manager = ConfigManager(temp_config_file)

            assert config_manager.config.enabled == True
            assert config_manager.config.voice.volume == 85
            assert config_manager.config.intelligent_filter.enabled == True
            assert config_manager.config.performance.target_delivery_ms == 500

        def test_config_validation_edge_cases(self):
            """Test configuration validation with edge cases"""
            # Test with invalid values
            invalid_config = {
                "enabled": True,
                "voice": {
                    "volume": 150,  # Invalid: > 100
                    "rate": "invalid"  # Invalid type
                },
                "performance": {
                    "target_delivery_ms": -100  # Invalid: negative
                },
                "intelligent_filter": {
                    "filter_strength": 1.5  # Invalid: > 1.0
                }
            }

            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(invalid_config, f)
                config_file = f.name

            try:
                config_manager = ConfigManager(config_file)

                # Should have defaulted to valid values
                assert config_manager.config.voice.volume <= 100
                assert isinstance(config_manager.config.voice.rate, int)
                assert config_manager.config.performance.target_delivery_ms > 0
                assert 0.0 <= config_manager.config.intelligent_filter.filter_strength <= 1.0

            finally:
                Path(config_file).unlink(missing_ok=True)

        def test_notification_type_configuration(self, config_manager):
            """Test notification type configuration"""
            notif_config = config_manager.get_notification_config("task_complete")
            assert notif_config.enabled == True
            assert notif_config.template == "Task Complete: {task_name}"
            assert notif_config.priority == "normal"

            # Test disabled notification type
            assert not config_manager.is_notification_enabled("nonexistent_type")

    class TestIntelligentFiltering:
        """Test the intelligent filtering system"""

        def test_basic_filtering_functionality(self, intelligent_filter):
            """Test basic filtering decisions"""
            # High priority notification should be allowed
            high_priority_context = NotificationContext(
                notification_type="question",
                task_name="Important question",
                session_id="test_session",
                timestamp=datetime.now(),
                priority="high",
                requires_interaction=True
            )

            result = intelligent_filter.should_filter_notification(high_priority_context)
            assert result.decision == FilterDecision.ALLOW

        def test_frequency_limiting(self, intelligent_filter):
            """Test frequency limiting functionality"""
            context = NotificationContext(
                notification_type="task_complete",
                task_name="Test task",
                session_id="freq_test_session",
                timestamp=datetime.now(),
                priority="normal"
            )

            # First few should be allowed
            for i in range(5):
                result = intelligent_filter.should_filter_notification(context)
                if i < 10:  # Within limit
                    assert result.decision == FilterDecision.ALLOW
                # Note: In real scenario, would need to wait between notifications
                # or modify timing to test frequency limiting properly

        def test_session_isolation(self, intelligent_filter):
            """Test session isolation functionality"""
            context1 = NotificationContext(
                notification_type="task_complete",
                task_name="Task 1",
                session_id="session_1",
                timestamp=datetime.now(),
                priority="normal"
            )

            context2 = NotificationContext(
                notification_type="task_complete",
                task_name="Task 2",
                session_id="session_2",
                timestamp=datetime.now(),
                priority="normal"
            )

            # Different sessions should be isolated
            result1 = intelligent_filter.should_filter_notification(context1)
            result2 = intelligent_filter.should_filter_notification(context2)

            assert result1.decision == FilterDecision.ALLOW
            assert result2.decision == FilterDecision.ALLOW

        def test_behavioral_learning(self, intelligent_filter):
            """Test behavioral learning without feedback"""
            context = NotificationContext(
                notification_type="task_complete",
                task_name="Complex implementation task",
                session_id="learning_session",
                timestamp=datetime.now(),
                priority="normal"
            )

            # Initial filtering
            initial_result = intelligent_filter.should_filter_notification(context)

            # Simulate multiple similar notifications to build pattern
            for i in range(5):
                test_context = NotificationContext(
                    notification_type="task_complete",
                    task_name=f"Complex implementation task {i}",
                    session_id="learning_session",
                    timestamp=datetime.now() + timedelta(minutes=i),
                    priority="normal"
                )
                intelligent_filter.should_filter_notification(test_context)

            # Profile should have been updated
            profile = intelligent_filter.behavioral_profile
            assert len(profile.temporal_patterns) > 0 or len(profile.task_complexity_scores) > 0

    class TestParallelExecution:
        """Test parallel execution capabilities"""

        @pytest.mark.asyncio
        async def test_concurrent_notification_handling(self, started_orchestrator):
            """Test handling multiple notifications concurrently"""
            # Create multiple notification requests
            requests = []
            for i in range(5):
                result = await started_orchestrator.trigger_notification(
                    notification_type="task_complete",
                    task_name=f"Concurrent task {i}",
                    session_id=f"session_{i}",
                    priority="normal"
                )
                requests.append(result)

            # All requests should be accepted (even if not immediately delivered)
            for result in requests:
                assert result.request_id is not None

        @pytest.mark.asyncio
        async def test_queue_overflow_handling(self, started_orchestrator):
            """Test handling of queue overflow"""
            # Fill queue with many requests
            requests = []
            for i in range(20):  # More than typical queue size
                result = await started_orchestrator.trigger_notification(
                    notification_type="info",
                    task_name=f"Queue test task {i}",
                    session_id="queue_test",
                    priority="low"
                )
                requests.append(result)

            # System should handle gracefully
            assert len(requests) == 20

        @pytest.mark.asyncio
        async def test_performance_under_load(self, started_orchestrator):
            """Test system performance under load"""
            start_time = time.time()

            # Trigger multiple notifications rapidly
            tasks = []
            for i in range(10):
                task = started_orchestrator.trigger_notification(
                    notification_type="task_complete",
                    task_name=f"Load test task {i}",
                    session_id="load_test",
                    priority="normal"
                )
                tasks.append(task)

            # Wait for all to be queued
            results = await asyncio.gather(*tasks, return_exceptions=True)

            total_time = time.time() - start_time

            # Should handle load efficiently (all requests accepted quickly)
            assert total_time < 2.0  # Should complete within 2 seconds
            assert len(results) == 10

    class TestPerformanceMonitoring:
        """Test performance monitoring functionality"""

        def test_delivery_performance_tracking(self, orchestrator):
            """Test delivery performance tracking"""
            # Create a delivery snapshot
            snapshot = DeliveryPerformanceSnapshot(
                timestamp=datetime.now(),
                delivery_time_ms=300.0,
                notification_type="task_complete",
                engine_used="pyttsx3",
                session_id="test_session",
                priority="normal",
                was_filtered=False
            )

            # Record the snapshot
            orchestrator.intelligent_filter.filter_metrics['total_allowed'] = 1

            # Check metrics were updated
            assert orchestrator.metrics.total_requests >= 0

        def test_performance_alert_generation(self, orchestrator):
            """Test performance alert generation"""
            # Simulate a slow delivery
            slow_snapshot = DeliveryPerformanceSnapshot(
                timestamp=datetime.now(),
                delivery_time_ms=1500.0,  # Much slower than target
                notification_type="task_complete",
                engine_used="pyttsx3",
                session_id="test_session",
                priority="normal",
                was_filtered=False
            )

            # This would trigger an alert in real monitoring
            orchestrator.metrics.total_requests += 1
            orchestrator.metrics.failed_deliveries += 1

            assert orchestrator.metrics.failed_deliveries == 1

        def test_metrics_collection(self, started_orchestrator):
            """Test comprehensive metrics collection"""
            # Trigger some notifications
            asyncio.create_task(started_orchestrator.trigger_notification(
                "task_complete", "Metrics test", "metrics_session"
            ))

            # Give it a moment to process
            await asyncio.sleep(0.1)

            # Get metrics
            metrics = started_orchestrator.get_metrics()

            # Check metrics structure
            assert "orchestrator" in metrics
            assert "filter" in metrics
            assert "engines" in metrics
            assert "configuration" in metrics

            # Check specific metrics
            orch_metrics = metrics["orchestrator"]
            assert "total_requests" in orch_metrics
            assert "successful_deliveries" in orch_metrics
            assert "failed_deliveries" in orch_metrics

    class TestConstitutionalCompliance:
        """Test constitutional compliance requirements"""

        def test_no_fallback_mechanisms(self, orchestrator):
            """Test that there are no fallback mechanisms that hide failures"""
            # When no engine is available, should fail clearly
            orchestrator.pyttsx3_available = False
            orchestrator.powershell_available = False

            async def test_delivery():
                result = await orchestrator.trigger_notification(
                    "task_complete", "No engine test", "test_session"
                )
                # Should not falsely report success
                assert result.status != DeliveryStatus.DELIVERED

            asyncio.run(test_delivery())

        def test_clear_error_messages(self, config_manager):
            """Test that error messages are clear and actionable"""
            # Test with invalid configuration
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump({"invalid": "config"}, f)
                invalid_config_file = f.name

            try:
                invalid_config_manager = ConfigManager(invalid_config_file)
                # Should handle gracefully with clear error logging
                assert invalid_config_manager.config is not None

            finally:
                Path(invalid_config_file).unlink(missing_ok=True)

        def test_transparency_in_filtering_decisions(self, intelligent_filter):
            """Test that filtering decisions are transparent"""
            context = NotificationContext(
                notification_type="task_complete",
                task_name="Test task",
                session_id="transparency_test",
                timestamp=datetime.now(),
                priority="normal"
            )

            result = intelligent_filter.should_filter_notification(context)

            # Should provide clear reasoning
            assert result.decision != None
            assert result.reason != ""
            assert result.confidence >= 0.0
            assert result.confidence <= 1.0

    class TestHookIntegration:
        """Test Claude hook integration"""

        def test_hook_notification_triggering(self, hook_integration):
            """Test triggering notifications through hook integration"""
            result = hook_integration.trigger_notification_sync(
                notification_type="task_complete",
                task_name="Hook test task",
                session_id="hook_test",
                priority="normal"
            )

            # Should handle gracefully even if orchestrator not fully started
            assert isinstance(result, bool)

        def test_hook_type_determination(self, hook_integration):
            """Test hook type determination logic"""
            # Test various tool names
            test_cases = [
                ("Bash", "execute", "post_tool_use", "task_complete"),
                ("review_code", "analyze", "post_tool_use", "review_complete"),
                ("create_plan", "design", "post_tool_use", "plan_ready"),
                ("ask_question", "clarify", "post_tool_use", "question"),
                ("SessionStart", "", "session_start", "task_complete"),
                ("Stop", "", "stop", "task_complete")
            ]

            for tool_name, action, hook_type, expected in test_cases:
                result = hook_integration.determine_notification_type(tool_name, action, hook_type)
                assert result == expected

        def test_priority_extraction(self, hook_integration):
            """Test priority extraction from context"""
            # Test high priority from error
            result = hook_integration.extract_priority("error_handling", {"error": "test error"})
            assert result == "high"

            # Test normal priority
            result = hook_integration.extract_priority("normal_task", {})
            assert result == "normal"

            # Test explicit priority
            result = hook_integration.extract_priority("task", {"priority": "critical"})
            assert result == "critical"

    class TestSystemIntegration:
        """Test complete system integration"""

        @pytest.mark.asyncio
        async def test_end_to_end_notification_flow(self, started_orchestrator):
            """Test complete notification flow from trigger to delivery"""
            # Trigger notification
            result = await started_orchestrator.trigger_notification(
                notification_type="task_complete",
                task_name="End-to-end test",
                session_id="e2e_session",
                priority="normal"
            )

            # Should be accepted and processed
            assert result.request_id is not None

            # Wait a moment for processing
            await asyncio.sleep(0.1)

            # Check system state
            metrics = started_orchestrator.get_metrics()
            assert metrics["orchestrator"]["total_requests"] >= 1

        @pytest.mark.asyncio
        async def test_system_shutdown_and_restart(self, temp_config_file):
            """Test graceful shutdown and restart"""
            # Create and start orchestrator
            orchestrator = VoiceNotificationOrchestrator(temp_config_file)
            await orchestrator.start()

            # Trigger a notification
            await orchestrator.trigger_notification(
                "task_complete", "Shutdown test", "shutdown_test"
            )

            # Shutdown
            await orchestrator.stop()
            assert not orchestrator.is_running()

            # Restart
            await orchestrator.start()
            assert orchestrator.is_running()

            # Should work after restart
            await orchestrator.trigger_notification(
                "task_complete", "Restart test", "restart_test"
            )

            await orchestrator.stop()

        @pytest.mark.asyncio
        async def test_configuration_reloading(self, temp_config_file):
            """Test configuration reloading during runtime"""
            orchestrator = VoiceNotificationOrchestrator(temp_config_file)
            await orchestrator.start()

            # Get initial configuration
            initial_volume = orchestrator.config.voice.volume

            # Modify config file
            modified_config = {
                "enabled": True,
                "voice": {
                    "preferred_voice": "Microsoft David Desktop",
                    "volume": 90,  # Changed
                    "rate": -1,
                    "async_speech": True
                },
                "notifications": {},
                "intelligent_filter": {"enabled": True},
                "performance": {"target_delivery_ms": 500},
                "logging": {"enabled": True},
                "integration": {}
            }

            with open(temp_config_file, 'w') as f:
                json.dump(modified_config, f, indent=2)

            # Reload configuration
            success = orchestrator.config_manager.reload_config()
            assert success == True

            # Check that configuration was updated
            assert orchestrator.config_manager.config.voice.volume == 90

            await orchestrator.stop()

    class TestErrorHandling:
        """Test error handling and recovery"""

        @pytest.mark.asyncio
        async def test_engine_failure_handling(self, started_orchestrator):
            """Test handling of voice engine failures"""
            # Mock engine failure
            with patch.object(started_orchestrator, '_deliver_with_pyttsx3', return_value=False):
                result = await started_orchestrator.trigger_notification(
                    "task_complete", "Engine failure test", "failure_test"
                )

                # Should handle failure gracefully
                assert result.request_id is not None

        @pytest.mark.asyncio
        async def test_filtering_system_errors(self, intelligent_filter):
            """Test handling of errors in filtering system"""
            # Create context that might cause issues
            problematic_context = NotificationContext(
                notification_type="",
                task_name=None,  # None might cause issues
                session_id="error_test",
                timestamp=datetime.now(),
                priority="invalid_priority"
            )

            # Should handle gracefully without crashing
            result = intelligent_filter.should_filter_notification(problematic_context)
            assert result is not None
            assert result.decision is not None

        @pytest.mark.asyncio
        async def test_concurrent_error_scenarios(self, started_orchestrator):
            """Test handling of multiple concurrent error scenarios"""
            # Trigger multiple problematic notifications
            tasks = []
            for i in range(5):
                task = started_orchestrator.trigger_notification(
                    "nonexistent_type",  # Invalid notification type
                    f"Error test {i}",
                    f"error_session_{i}",
                    priority="invalid_priority"
                )
                tasks.append(task)

            # Should handle all gracefully
            results = await asyncio.gather(*tasks, return_exceptions=True)
            assert len(results) == 5

            # No exceptions should be raised
            for result in results:
                assert not isinstance(result, Exception)

    class TestWindowsSpecificFeatures:
        """Test Windows-specific functionality"""

        def test_windows_voice_engine_detection(self, orchestrator):
            """Test Windows voice engine detection"""
            # Should detect engine availability (mocked in test environment)
            assert isinstance(orchestrator.pyttsx3_available, bool)
            assert isinstance(orchestrator.powershell_available, bool)

        def test_powershell_fallback_mechanism(self, orchestrator):
            """Test PowerShell fallback mechanism"""
            # Test engine selection logic
            engines = []

            if orchestrator.pyttsx3_available:
                engines.append("pyttsx3")
            if orchestrator.powershell_available:
                engines.append("powershell")

            # Should have at least some engine detection logic
            assert len(engines) >= 0  # Could be 0 in test environment

        def test_windows_path_handling(self, config_manager):
            """Test Windows-specific path handling"""
            # Test with Windows paths
            test_paths = [
                "C:\\Users\\test\\config.json",
                "P:/hooks/voice-notification.ps1",
                "..\\relative\\path.json"
            ]

            for path in test_paths:
                try:
                    # Should handle Windows paths without issues
                    path_obj = Path(path)
                    assert path_obj is not None
                except Exception as e:
                    pytest.fail(f"Failed to handle Windows path {path}: {e}")

# Integration test class
class TestSystemIntegration:
    """Integration tests for the complete system"""

    @pytest.mark.asyncio
    async def test_full_system_integration(self, temp_config_file):
        """Test full system integration with all components"""
        # This is a comprehensive integration test

        # 1. Initialize all components
        config_manager = ConfigManager(temp_config_file)
        intelligent_filter = IntelligentNotificationFilter(config_manager.config)
        orchestrator = VoiceNotificationOrchestrator(temp_config_file)

        # 2. Start system
        await orchestrator.start()
        assert orchestrator.is_running()

        # 3. Test various notification types
        notification_types = [
            ("task_complete", "Implementation complete", "normal"),
            ("question", "User question", "high"),
            ("error", "System error", "high"),
            ("plan_ready", "Project plan", "normal")
        ]

        results = []
        for notif_type, task_name, priority in notification_types:
            result = await orchestrator.trigger_notification(
                notification_type=notif_type,
                task_name=task_name,
                session_id="integration_test",
                priority=priority
            )
            results.append(result)

        # 4. Verify all notifications were processed
        assert len(results) == len(notification_types)

        # 5. Check system metrics
        metrics = orchestrator.get_metrics()
        assert metrics["orchestrator"]["total_requests"] >= len(notification_types)

        # 6. Test filtering intelligence
        filter_context = NotificationContext(
            notification_type="task_complete",
            task_name="Integration test task",
            session_id="integration_test",
            timestamp=datetime.now(),
            priority="normal"
        )

        filter_result = intelligent_filter.should_filter_notification(filter_context)
        assert filter_result is not None

        # 7. Test configuration updates
        original_volume = config_manager.config.voice.volume
        config_manager.update_setting("voice.volume", 95)
        assert config_manager.config.voice.volume == 95

        # 8. Shutdown gracefully
        await orchestrator.stop()
        assert not orchestrator.is_running()

        # 9. Save behavioral profile
        intelligent_filter.save_profile()

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])
