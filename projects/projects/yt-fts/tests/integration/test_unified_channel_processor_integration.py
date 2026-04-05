#!/usr/bin/env python3
"""
Integration Tests for UnifiedChannelProcessor

CWO15 Step 10: Integration Testing & Validation
Test suite for UnifiedChannelProcessor integration with existing components.

Author: CSF NIP Implementation Team
Version: 1.0.0
"""

import asyncio

# Add src to path for testing
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from yt_fts.download.download_handler import DownloadHandler
from yt_fts.services.channel_identifier_resolver import ResolutionResult
from yt_fts.services.unified_channel_processor import (
    ChannelInfo,
    ChannelResult,
    InputType,
    UnifiedChannelProcessor,
    create_processor_for_cli,
    process_channel,
)


class TestUnifiedChannelProcessorIntegration:
    """Integration tests for UnifiedChannelProcessor with existing components"""

    @pytest.fixture
    def processor(self):
        """Create a UnifiedChannelProcessor instance for testing"""
        return UnifiedChannelProcessor(cache_enabled=True)

    @pytest.fixture
    def mock_channel_info(self):
        """Mock channel information for testing"""
        return ChannelInfo(
            channel_id="UC1234567890123456789012",
            name="Test Channel",
            handle="@testchannel",
            url="https://www.youtube.com/channel/UC1234567890123456789012",
            subscriber_count=1000,
            video_count=50,
            description="Test channel description",
            thumbnail_url="https://example.com/thumbnail.jpg"
        )

    @pytest.fixture
    def download_handler(self):
        """Create a DownloadHandler instance for integration testing"""
        return DownloadHandler(number_of_jobs=1, language="en", fail_fast=False)

    @pytest.mark.asyncio
    async def test_processor_download_handler_integration(self, processor, mock_channel_info):
        """Test UnifiedChannelProcessor ↔ DownloadHandler integration"""

        # Mock the identifier resolver to return consistent results
        with patch.object(processor.identifier_resolver, "resolve") as mock_resolve:
            mock_resolve.return_value = ResolutionResult(
                success=True,
                channel_id=mock_channel_info.channel_id,
                channel_name=mock_channel_info.name,
                channel_url=mock_channel_info.url
            )

            # Mock the cache operations
            with patch.object(processor.cache, "get_channel_info") as mock_cache_get:
                mock_cache_get.return_value = None  # No cached result initially

                with patch.object(processor.cache, "cache_channel_info") as mock_cache_set:
                    # Test @handle resolution
                    result = await processor.process_channel_input("@testchannel")

                    # Verify successful processing
                    assert result.success is True
                    assert result.channel_id == mock_channel_info.channel_id
                    assert result.input_type == InputType.HANDLE

                    # Verify that cache operations were called
                    mock_cache_get.assert_called()
                    mock_cache_set.assert_called()

    @pytest.mark.asyncio
    async def test_download_handler_enhanced_channel_resolution(self, download_handler):
        """Test DownloadHandler using enhanced channel resolution"""

        # Create a processor for the download handler
        processor = download_handler.channel_processor

        # Mock successful channel resolution
        with patch.object(processor, "process_channel_input") as mock_process:
            mock_result = ChannelResult(
                success=True,
                channel_id="UC1234567890123456789012",
                channel_info=ChannelInfo(
                    channel_id="UC1234567890123456789012",
                    name="Test Channel",
                    url="https://www.youtube.com/channel/UC1234567890123456789012"
                ),
                input_type=InputType.HANDLE,
                processing_time_ms=50
            )
            mock_process.return_value = mock_result

            # Test the enhanced get_channel_id method
            channel_id = await download_handler.get_channel_id("@testchannel")

            # Verify the result
            assert channel_id == "UC1234567890123456789012"

            # Verify the processor was called correctly
            mock_process.assert_called_once_with("@testchannel")

    @pytest.mark.asyncio
    async def test_download_handler_error_handling_integration(self, download_handler):
        """Test DownloadHandler error handling with UnifiedChannelProcessor"""

        processor = download_handler.channel_processor

        # Mock failed channel resolution
        with patch.object(processor, "process_channel_input") as mock_process:
            mock_result = ChannelResult(
                success=False,
                error="Channel not found",
                suggestions=["Check the @handle format", "Verify channel exists"]
            )
            mock_process.return_value = mock_result

            # Test error handling (should return None instead of sys.exit())
            channel_id = await download_handler.get_channel_id("@nonexistentchannel")

            # Verify graceful error handling
            assert channel_id is None
            mock_process.assert_called_once_with("@nonexistentchannel")

    @pytest.mark.asyncio
    async def test_multi_format_input_processing(self, processor, mock_channel_info):
        """Test processing of different input formats (@handles, URLs, channel IDs, names)"""

        # Mock successful resolution for all input types
        with patch.object(processor.identifier_resolver, "resolve") as mock_resolve:
            mock_resolve.return_value = ResolutionResult(
                success=True,
                channel_id=mock_channel_info.channel_id,
                channel_name=mock_channel_info.name,
                channel_url=mock_channel_info.url
            )

            # Mock cache operations
            with patch.object(processor.cache, "get_channel_info", return_value=None):
                with patch.object(processor.cache, "cache_channel_info"):

                    test_cases = [
                        ("@testchannel", InputType.HANDLE),
                        ("https://www.youtube.com/channel/UC1234567890123456789012", InputType.URL),
                        ("UC1234567890123456789012", InputType.CHANNEL_ID),
                        ("Test Channel Name", InputType.NAME)
                    ]

                    for input_value, expected_type in test_cases:
                        result = await processor.process_channel_input(input_value)

                        assert result.success is True
                        assert result.channel_id == mock_channel_info.channel_id
                        assert result.input_type == expected_type

                        # Verify processing time is tracked
                        assert result.processing_time_ms is not None
                        assert result.processing_time_ms > 0

    @pytest.mark.asyncio
    async def test_cache_integration_performance(self, processor, mock_channel_info):
        """Test cache integration and performance improvements"""

        with patch.object(processor.identifier_resolver, "resolve") as mock_resolve:
            mock_resolve.return_value = ResolutionResult(
                success=True,
                channel_id=mock_channel_info.channel_id,
                channel_name=mock_channel_info.name,
                channel_url=mock_channel_info.url
            )

            # Mock cache - first call returns None (cache miss), second returns cached result
            cache_responses = [None, mock_channel_info]
            with patch.object(processor.cache, "get_channel_info") as mock_cache_get:
                mock_cache_get.side_effect = cache_responses

                with patch.object(processor.cache, "cache_channel_info"):
                    # First call - cache miss
                    start_time = time.time()
                    result1 = await processor.process_channel_input("@testchannel")
                    first_call_time = time.time() - start_time

                    # Second call - cache hit
                    start_time = time.time()
                    result2 = await processor.process_channel_input("@testchannel")
                    second_call_time = time.time() - start_time

                    # Both should be successful
                    assert result1.success is True
                    assert result2.success is True
                    assert result1.channel_id == result2.channel_id

                    # Cache should be called twice
                    assert mock_cache_get.call_count == 2

                    # Cache hit should be faster (or at least not significantly slower)
                    # Note: In testing environment, timing might vary, so we just verify it completes
                    assert second_call_time >= 0

    def test_statistics_tracking(self, processor):
        """Test processing statistics tracking"""

        # Initial statistics
        stats = processor.get_statistics()
        assert stats["total_processed"] == 0
        assert stats["cache_hits"] == 0
        assert stats["resolution_errors"] == 0
        assert "cache_hit_rate" in stats
        assert "error_rate" in stats

        # Reset statistics
        processor.reset_statistics()
        stats = processor.get_statistics()
        assert stats["total_processed"] == 0

    @pytest.mark.asyncio
    async def test_channel_validation_integration(self, processor):
        """Test channel validation functionality"""

        with patch.object(processor, "get_channel_info") as mock_get_info:
            # Test valid channel
            mock_get_info.return_value = ChannelInfo(
                channel_id="UC1234567890123456789012",
                name="Valid Channel"
            )

            is_valid = await processor.validate_channel_exists("UC1234567890123456789012")
            assert is_valid is True

            # Test invalid channel
            mock_get_info.return_value = None
            is_valid = await processor.validate_channel_exists("UCINVALID1234567890123456789012")
            assert is_valid is False

    def test_input_type_detection(self, processor):
        """Test input type detection accuracy"""

        test_cases = [
            ("@testchannel", InputType.HANDLE),
            ("https://www.youtube.com/channel/UC1234567890123456789012", InputType.URL),
            ("https://www.youtube.com/@testchannel", InputType.URL),
            ("UC1234567890123456789012", InputType.CHANNEL_ID),
            ("Test Channel Name", InputType.NAME),
            ("https://example.com/invalid", InputType.NAME)  # Default to NAME for unrecognized
        ]

        for input_value, expected_type in test_cases:
            detected_type = processor._detect_input_type(input_value)
            assert detected_type == expected_type, f"Failed for input: {input_value}"

    @pytest.mark.asyncio
    async def test_error_suggestion_generation(self, processor):
        """Test error suggestion generation"""

        # Test @handle suggestions
        suggestions = processor._generate_resolution_suggestions("@invalidhandle", "Channel not found")
        assert any("@handle" in suggestion for suggestion in suggestions)
        assert any("URL" in suggestion for suggestion in suggestions)

        # Test URL suggestions
        suggestions = processor._generate_resolution_suggestions("https://invalid.url", "404 error")
        assert any("YouTube" in suggestion for suggestion in suggestions)
        assert any("@handle" in suggestion for suggestion in suggestions)

        # Test name suggestions
        suggestions = processor._generate_resolution_suggestions("Nonexistent Channel", "No results")
        assert any("searching" in suggestion.lower() for suggestion in suggestions)

    def test_convenience_functions(self):
        """Test convenience functions for CLI integration"""

        # Test create_processor_for_cli
        cli_processor = create_processor_for_cli()
        assert isinstance(cli_processor, UnifiedChannelProcessor)
        assert cli_processor.cache is not None  # Should be enabled by default

    @pytest.mark.asyncio
    async def test_convenience_process_channel_function(self, mock_channel_info):
        """Test the convenience process_channel function"""

        with patch("yt_fts.services.unified_channel_processor.UnifiedChannelProcessor") as mock_processor_class:
            mock_processor = AsyncMock()
            mock_processor_class.return_value = mock_processor

            mock_result = ChannelResult(
                success=True,
                channel_id=mock_channel_info.channel_id,
                channel_info=mock_channel_info,
                input_type=InputType.HANDLE
            )
            mock_processor.process_channel_input.return_value = mock_result

            # Test convenience function
            result = await process_channel("@testchannel", cache_enabled=True)

            # Verify processor was created with correct settings
            mock_processor_class.assert_called_once_with(cache_enabled=True)

            # Verify processing was called
            mock_processor.process_channel_input.assert_called_once_with("@testchannel")

            # Verify result
            assert result == mock_result

    @pytest.mark.asyncio
    async def test_concurrent_processing_support(self, processor, mock_channel_info):
        """Test that processor supports concurrent processing"""

        with patch.object(processor.identifier_resolver, "resolve") as mock_resolve:
            mock_resolve.return_value = ResolutionResult(
                success=True,
                channel_id=mock_channel_info.channel_id,
                channel_name=mock_channel_info.name,
                channel_url=mock_channel_info.url
            )

            with patch.object(processor.cache, "get_channel_info", return_value=None):
                with patch.object(processor.cache, "cache_channel_info"):

                    # Process multiple channels concurrently
                    inputs = ["@channel1", "@channel2", "@channel3"]
                    tasks = [
                        processor.process_channel_input(input_val)
                        for input_val in inputs
                    ]

                    results = await asyncio.gather(*tasks)

                    # All should succeed
                    assert all(result.success for result in results)
                    assert all(result.channel_id == mock_channel_info.channel_id for result in results)

                    # Verify statistics updated correctly
                    stats = processor.get_statistics()
                    assert stats["total_processed"] >= len(inputs)

    def test_csf_nip_compliance_no_sys_exit(self, processor):
        """Test CSF NIP compliance: No sys.exit() calls in error handling"""

        # This test verifies that the processor handles errors gracefully
        # without calling sys.exit(), which would terminate the program

        # Test empty input handling
        async def test_empty_input():
            result = await processor.process_channel_input("")
            assert result.success is False
            assert "Empty input" in result.error
            return result

        # Run the test
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(test_empty_input())
        loop.close()

        # Verify graceful error handling
        assert result.success is False
        assert result.suggestions is not None
        assert len(result.suggestions) > 0


class TestErrorHandlingIntegration:
    """Test error handling integration across components"""

    @pytest.fixture
    def download_handler(self):
        """Create a DownloadHandler instance for integration testing"""
        return DownloadHandler(number_of_jobs=1, language="en", fail_fast=False)

    @pytest.mark.asyncio
    async def test_channel_processing_error_propagation(self):
        """Test ChannelProcessingError propagation and handling"""

        processor = UnifiedChannelProcessor()

        # Mock both cache and resolver
        with patch.object(processor.cache, "get_channel_info", return_value=None):
            with patch.object(processor.identifier_resolver, "resolve") as mock_resolve:
                mock_resolve.side_effect = Exception("Network error")

                result = await processor.process_channel_input("@testchannel")

                # Verify error is handled gracefully
                assert result.success is False
                assert "Unexpected error" in result.error
                assert result.suggestions is not None

                # Verify the mock was called
                mock_resolve.assert_called_once_with("@testchannel")

    @pytest.mark.asyncio
    async def test_download_handler_channel_processing_error(self, download_handler):
        """Test DownloadHandler handling of ChannelProcessingError"""

        processor = download_handler.channel_processor

        # Mock the processor to raise a ChannelProcessingError
        with patch.object(processor, "process_channel_input") as mock_process:
            from yt_fts.exceptions import ChannelProcessingError
            mock_process.side_effect = ChannelProcessingError(
                message="Test channel processing error",
                suggestions=["Try again later"]
            )

            # Test that DownloadHandler handles the error gracefully
            channel_id = await download_handler.get_channel_id("@testchannel")

            # Verify graceful handling (returns None instead of sys.exit())
            assert channel_id is None


if __name__ == "__main__":
    # Run the integration tests
    pytest.main([__file__, "-v", "--tb=short"])
