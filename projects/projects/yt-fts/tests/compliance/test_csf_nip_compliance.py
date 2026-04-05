#!/usr/bin/env python3
"""
CSF NIP Compliance Tests for UnifiedChannelProcessor Integration

CWO15 Step 10: Integration Testing & Validation
CSF NIP compliance validation focusing on zero sys.exit() violations and constitutional standards.

Author: CSF NIP Implementation Team
Version: 1.0.0
"""

import asyncio
import os
import re
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from yt_fts.download.download_handler import DownloadHandler
from yt_fts.exceptions import ChannelProcessingError
from yt_fts.services.unified_channel_processor import (
    ChannelInfo,
    ChannelResult,
    InputType,
    UnifiedChannelProcessor,
)


class TestCSFNIPCompliance:
    """CSF NIP compliance tests for the UnifiedChannelProcessor integration"""

    @pytest.fixture
    def processor(self):
        """Create a processor for compliance testing"""
        return UnifiedChannelProcessor(cache_enabled=True)

    @pytest.fixture
    def download_handler(self):
        """Create a download handler for compliance testing"""
        return DownloadHandler(number_of_jobs=1, language="en", fail_fast=False)

    def test_no_sys_exit_calls_in_source_code(self):
        """Test that source code contains no sys.exit() calls (CSF NIP requirement)"""

        # Scan source files for sys.exit() calls
        src_dir = Path(__file__).parent.parent.parent / "src" / "yt_fts"
        sys_exit_violations = []

        # Check UnifiedChannelProcessor
        processor_file = src_dir / "services" / "unified_channel_processor.py"
        if processor_file.exists():
            content = processor_file.read_text()
            if re.search(r"\bsys\.exit\s*\(", content):
                sys_exit_violations.append(str(processor_file))

        # Check DownloadHandler
        download_file = src_dir / "download" / "download_handler.py"
        if download_file.exists():
            content = download_file.read_text()
            # Allow comments mentioning sys.exit() but not actual calls
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                if re.search(r"\bsys\.exit\s*\(", line) and not line.strip().startswith("#"):
                    sys_exit_violations.append(f"{download_file}:{i}")

        # Check UnifiedErrorHandler (excluding docstrings and comments)
        error_handler_file = src_dir / "services" / "unified_error_handler.py"
        if error_handler_file.exists():
            content = error_handler_file.read_text()
            # Remove docstrings and comments before checking
            lines = content.split("\n")
            cleaned_lines = []
            in_docstring = False

            for line in lines:
                stripped = line.strip()
                # Skip docstring content
                if '"""' in line or "'''" in line:
                    in_docstring = not in_docstring
                    continue
                if in_docstring:
                    continue
                # Skip comment lines
                if stripped.startswith("#"):
                    continue
                # Skip lines with docstring patterns
                if "sys.exit()" in line and ('"""' in line or "'''" in line):
                    continue
                cleaned_lines.append(line)

            cleaned_content = "\n".join(cleaned_lines)
            if re.search(r"\bsys\.exit\s*\(", cleaned_content):
                sys_exit_violations.append(str(error_handler_file))

        # Assert no violations found
        assert len(sys_exit_violations) == 0, (
            f"CSF NIP Violation: Found sys.exit() calls in: {sys_exit_violations}. "
            "All error handling must use exceptions instead of sys.exit()."
        )

    @pytest.mark.asyncio
    async def test_graceful_error_handling_no_system_exit(self, processor):
        """Test that all errors are handled gracefully without sys.exit()"""

        # Test various error conditions
        error_scenarios = [
            "",  # Empty input
            "   ",  # Whitespace input
            "@invalid-channel-format",  # Invalid format
            "https://invalid-url",  # Invalid URL
            None,  # None input
        ]

        for error_input in error_scenarios:
            # Mock resolver to raise exceptions
            with patch.object(processor.identifier_resolver, "resolve") as mock_resolve:
                mock_resolve.side_effect = Exception("Simulated error")

                try:
                    result = await processor.process_channel_input(error_input)

                    # Should return error result, not raise SystemExit
                    assert isinstance(result, ChannelResult)
                    assert result.success is False
                    assert result.error is not None
                    assert result.suggestions is not None

                except SystemExit:
                    pytest.fail(f"CSF NIP Violation: sys.exit() called for input: {error_input}")

    @pytest.mark.asyncio
    async def test_download_handler_compliance_no_system_exit(self, download_handler):
        """Test DownloadHandler compliance with CSF NIP standards"""

        error_scenarios = [
            "@nonexistent-channel",
            "https://youtube.com/invalid-channel",
            "UCINVALIDCHANNELID123456789012",
            "Invalid Channel Name That Doesn't Exist"
        ]

        for error_input in error_scenarios:
            # Mock processor to return error result
            with patch.object(download_handler.channel_processor, "process_channel_input") as mock_process:
                mock_result = ChannelResult(
                    success=False,
                    error=f"Channel not found: {error_input}",
                    suggestions=[
                        "Check the channel format",
                        "Verify the channel exists",
                        "Try using a different identifier"
                    ]
                )
                mock_process.return_value = mock_result

                try:
                    # Test get_channel_id method
                    channel_id = await download_handler.get_channel_id(error_input)

                    # Should return None for graceful error handling
                    assert channel_id is None

                except SystemExit:
                    pytest.fail(f"CSF NIP Violation: DownloadHandler called sys.exit() for input: {error_input}")

    @pytest.mark.asyncio
    async def test_channel_processing_error_propagation(self, processor):
        """Test ChannelProcessingError propagation without sys.exit()"""

        # Test custom channel processing errors
        with patch.object(processor.identifier_resolver, "resolve") as mock_resolve:
            mock_resolve.side_effect = ChannelProcessingError(
                message="Custom channel processing error",
                suggestions=["Try again later", "Check network connection"]
            )

            try:
                # Use unique channel name to avoid cache conflicts
                result = await processor.process_channel_input("@error-test-channel")

                # Should handle custom error gracefully
                assert isinstance(result, ChannelResult)
                assert result.success is False
                assert "Custom channel processing error" in result.error

            except SystemExit:
                pytest.fail("CSF NIP Violation: sys.exit() called during ChannelProcessingError handling")

    def test_error_message_quality_and_helpfulness(self, processor):
        """Test that error messages are helpful and actionable"""

        # Mock resolver to return error result
        with patch.object(processor.identifier_resolver, "resolve") as mock_resolve:
            mock_resolve.return_value = MagicMock(
                success=False,
                error_message="Channel resolution failed"
            )

            async def test_error_scenarios():
                error_inputs = [
                    ("@invalid-handle", "handle format validation"),
                    ("https://invalid.url", "URL format validation"),
                    ("", "empty input validation"),
                    ("nonexistent-channel", "channel not found")
                ]

                for input_val, description in error_inputs:
                    result = await processor.process_channel_input(input_val)

                    # Verify error result quality
                    assert result.success is False, f"Should fail for: {description}"
                    assert result.error is not None, f"Should have error message for: {description}"
                    assert len(result.error) > 0, f"Error message should not be empty for: {description}"

                    # Verify suggestions are provided
                    assert result.suggestions is not None, f"Should provide suggestions for: {description}"
                    assert len(result.suggestions) > 0, f"Should have at least one suggestion for: {description}"

                    # Verify suggestions are helpful
                    suggestions_text = " ".join(result.suggestions).lower()
                    assert any(keyword in suggestions_text for keyword in
                              ["check", "try", "verify", "make sure", "ensure"]), \
                           f"Suggestions should be actionable for: {description}"

            # Run async test
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(test_error_scenarios())
            finally:
                loop.close()

    def test_structured_logging_compliance(self, processor):
        """Test structured logging compliance with CSF NIP standards"""

        # Test that logging is properly structured and informative
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Create processor with mocked logger
            test_processor = UnifiedChannelProcessor(cache_enabled=False)

            # Verify logger was configured
            mock_get_logger.assert_called()

            # Test logging during processing
            with patch.object(test_processor.identifier_resolver, "resolve") as mock_resolve:
                mock_resolve.return_value = type(
                    "MockResult",
                    (),
                    {"success": True, "channel_id": "UC1234567890123456789012", "channel_name": "Test Channel"}
                )()

                async def test_logging():
                    result = await test_processor.process_channel_input("@testchannel")
                    return result

                # Run async test
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(test_logging())

                    # Verify logger was used appropriately
                    # (Should log successful processing)
                    mock_logger.info.assert_called()
                    mock_logger.debug.assert_called()

                finally:
                    loop.close()

    def test_exception_hierarchy_compliance(self):
        """Test that exception hierarchy follows CSF NIP standards"""

        # Verify custom exception classes exist and follow proper hierarchy
        from yt_fts.exceptions import ChannelProcessingError

        # Test custom exception creation
        custom_error = ChannelProcessingError(
            message="Test error message",
            suggestions=["Suggestion 1", "Suggestion 2"]
        )

        # Verify exception properties
        assert hasattr(custom_error, "message")
        assert hasattr(custom_error, "suggestions")
        assert isinstance(custom_error.message, str)
        assert isinstance(custom_error.suggestions, list)

        # Verify exception can be raised and caught
        try:
            raise custom_error
        except ChannelProcessingError as e:
            assert e.message == "Test error message"
            assert e.suggestions == ["Suggestion 1", "Suggestion 2"]
        except Exception:
            pytest.fail("Should be caught as ChannelProcessingError")

    @pytest.mark.asyncio
    async def test_retry_mechanism_compliance(self, processor):
        """Test retry mechanism compliance without sys.exit()"""

        # Test that retry mechanisms work without calling sys.exit()
        attempt_count = 0

        def failing_resolver(input_value):
            nonlocal attempt_count
            attempt_count += 1

            if attempt_count < 3:
                raise Exception(f"Temporary failure (attempt {attempt_count})")
            return MagicMock(
                success=True,
                channel_id="UC1234567890123456789012",
                channel_name="Test Channel"
            )

        with patch.object(processor.identifier_resolver, "resolve") as mock_resolve:
            mock_resolve.side_effect = failing_resolver

            try:
                # This should work with retries or handle the failure gracefully
                result = await processor.process_channel_input("@testchannel")

                # Either succeeds after retries or fails gracefully
                assert isinstance(result, ChannelResult)

            except SystemExit:
                pytest.fail("CSF NIP Violation: Retry mechanism should not call sys.exit()")

    def test_configuration_compliance(self):
        """Test configuration compliance with CSF NIP standards"""

        # Test that configuration follows CSF NIP patterns
        from yt_fts.services.unified_channel_processor import create_processor_for_cli

        # Test CLI processor creation
        cli_processor = create_processor_for_cli()

        # Verify proper initialization
        assert isinstance(cli_processor, UnifiedChannelProcessor)
        assert cli_processor.cache is not None  # Should have cache enabled

        # Test default configuration compliance
        default_processor = UnifiedChannelProcessor()

        # Should have reasonable defaults
        assert default_processor.cache is not None
        assert hasattr(default_processor, "logger")
        assert hasattr(default_processor, "stats")

    def test_performance_monitoring_compliance(self, processor):
        """Test performance monitoring compliance with CSF NIP standards"""

        # Test that performance monitoring doesn't violate compliance
        initial_stats = processor.get_statistics()

        # Verify required statistics fields
        required_fields = [
            "total_processed",
            "cache_hits",
            "resolution_errors",
            "average_processing_time_ms",
            "cache_hit_rate",
            "error_rate"
        ]

        for field in required_fields:
            assert field in initial_stats, f"Missing required statistics field: {field}"
            assert isinstance(initial_stats[field], (int, float)), f"Field {field} should be numeric"

        # Test statistics reset
        processor.reset_statistics()
        reset_stats = processor.get_statistics()

        # Reset should maintain structure
        for field in required_fields:
            assert field in reset_stats, f"Missing field after reset: {field}"

    def test_memory_safety_compliance(self, processor):
        """Test memory safety compliance with CSF NIP standards"""

        import gc
        import weakref

        # Test that objects are properly cleaned up
        test_objects = []

        def create_test_objects():
            # Create temporary objects that should be cleaned up
            for i in range(10):
                info = ChannelInfo(
                    channel_id=f"UC{i:022d}",
                    name=f"Test Channel {i}"
                )
                test_objects.append(weakref.ref(info))

        create_test_objects()

        # Force garbage collection
        gc.collect()

        # Check that weak references are cleaned up
        alive_count = sum(1 for ref in test_objects if ref() is not None)

        # Most objects should be cleaned up (allowing for some still in use)
        assert alive_count < len(test_objects), "Memory leak detected: objects not properly cleaned up"

    @pytest.mark.asyncio
    async def test_concurrent_safety_compliance(self, processor):
        """Test concurrent safety compliance with CSF NIP standards"""

        # Test that concurrent operations don't cause race conditions or sys.exit() calls
        async def concurrent_process(input_val):
            try:
                with patch.object(processor.identifier_resolver, "resolve") as mock_resolve:
                    mock_resolve.return_value = MagicMock(
                        success=True,
                        channel_id="UC1234567890123456789012",
                        channel_name="Concurrent Test Channel"
                    )

                    result = await processor.process_channel_input(input_val)
                    return result
            except SystemExit:
                pytest.fail(f"CSF NIP Violation: Concurrent processing called sys.exit() for: {input_val}")

        # Run concurrent operations
        inputs = [f"@concurrent{i}" for i in range(10)]
        tasks = [concurrent_process(input_val) for input_val in inputs]
        results = await asyncio.gather(*tasks)

        # Verify all completed successfully without sys.exit()
        assert len(results) == len(inputs)
        assert all(isinstance(result, ChannelResult) for result in results)

    def test_data_integrity_compliance(self, processor):
        """Test data integrity compliance with CSF NIP standards"""

        # Test that data structures maintain integrity
        channel_info = ChannelInfo(
            channel_id="UC1234567890123456789012",
            name="Test Channel",
            handle="@testchannel",
            url="https://www.youtube.com/channel/UC1234567890123456789012"
        )

        # Verify data structure integrity
        assert channel_info.channel_id == "UC1234567890123456789012"
        assert channel_info.name == "Test Channel"
        assert channel_info.handle == "@testchannel"
        assert channel_info.url == "https://www.youtube.com/channel/UC1234567890123456789012"

        # Test result structure integrity
        result = ChannelResult(
            success=True,
            channel_id="UC1234567890123456789012",
            channel_info=channel_info,
            input_type=InputType.HANDLE,
            processing_time_ms=50
        )

        assert result.success is True
        assert result.channel_id == "UC1234567890123456789012"
        assert result.channel_info is channel_info
        assert result.input_type == InputType.HANDLE
        assert result.processing_time_ms == 50


class TestSystemIntegrationCompliance:
    """System integration compliance tests"""

    def test_cli_integration_compliance(self):
        """Test CLI integration compliance with CSF NIP standards"""

        # Test that CLI integration doesn't violate compliance
        from yt_fts.services.unified_channel_processor import create_processor_for_cli

        # This should work without calling sys.exit()
        try:
            cli_processor = create_processor_for_cli()
            assert isinstance(cli_processor, UnifiedChannelProcessor)
        except SystemExit:
            pytest.fail("CSF NIP Violation: CLI integration called sys.exit()")

    def test_database_integration_compliance(self):
        """Test database integration compliance with CSF NIP standards"""

        # Test that database operations don't call sys.exit()
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_db = f.name

        try:
            with patch("yt_fts.utils.config.get_db_path", return_value=temp_db):
                handler = DownloadHandler(number_of_jobs=1, language="en", fail_fast=False)

                # Mock processor to avoid network calls
                with patch.object(handler.channel_processor, "process_channel_input") as mock_process:
                    mock_result = ChannelResult(
                        success=True,
                        channel_id="UC1234567890123456789012",
                        channel_info=ChannelInfo(
                            channel_id="UC1234567890123456789012",
                            name="Test Channel"
                        ),
                        input_type=InputType.HANDLE
                    )
                    mock_process.return_value = mock_result

                    async def test_db_integration():
                        # Test channel resolution (shouldn't call sys.exit())
                        channel_id = await handler.get_channel_id("@testchannel")
                        return channel_id

                    # Run async test
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(test_db_integration())
                        # Should complete without sys.exit()
                        assert result == "UC1234567890123456789012"
                    except SystemExit:
                        pytest.fail("CSF NIP Violation: Database integration called sys.exit()")
                    finally:
                        loop.close()

        finally:
            # Cleanup
            try:
                os.unlink(temp_db)
            except OSError:
                pass


if __name__ == "__main__":
    # Run the compliance tests
    pytest.main([__file__, "-v", "--tb=short"])
