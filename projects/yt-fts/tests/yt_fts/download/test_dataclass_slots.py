"""
Test dataclass slots for download subsystem dataclasses.

Tests verify that @dataclass(slots=True) is properly applied:
1. Dataclass can be instantiated
2. Attributes are accessible
3. No __dict__ attribute (slots working)
4. No AttributeError on attribute access
"""
from __future__ import annotations

import pytest

from yt_fts.download.batch_config import BatchDownloadConfig, UIConfig
from yt_fts.download.channel_statistics_manager import InconsistencyReport
from yt_fts.download.cookie_auth_tester import CookieTestResult
from yt_fts.download.cookie_validator import ValidationResult
from yt_fts.download.download_checkpoint import CheckpointEntry, CheckpointResult
from yt_fts.download.dry_run_enhanced import ChannelPreview, DryRunSummary
from yt_fts.download.quota_strategy import QuotaConfig
from yt_fts.download.rich_parallel_progress import ChannelProgress


class TestChannelProgressSlots:
    """Test ChannelProgress has slots enabled."""

    def test_instantiate(self):
        """ChannelProgress can be instantiated."""
        obj = ChannelProgress(
            channel_name="Test Channel",
            channel_id="UC123",
            total_estimated=100,
            completed=50,
            status="fetching",
        )
        assert obj.channel_name == "Test Channel"
        assert obj.channel_id == "UC123"
        assert obj.completed == 50

    def test_no_dict_attribute(self):
        """ChannelProgress should not have __dict__ when slots=True."""
        obj = ChannelProgress(channel_name="Test")
        with pytest.raises(AttributeError):
            _ = obj.__dict__

    def test_attributes_accessible(self):
        """All attributes are accessible without errors."""
        obj = ChannelProgress(
            channel_name="Test",
            channel_id="UC123",
            total_estimated=100,
            completed=0,
            status="pending",
        )
        assert obj.channel_name == "Test"
        assert obj.channel_id == "UC123"
        assert obj.total_estimated == 100
        assert obj.completed == 0
        assert obj.status == "pending"
        assert obj.elapsed >= 0
        assert obj.percent_complete >= 0


class TestQuotaConfigSlots:
    """Test QuotaConfig has slots enabled."""

    def test_instantiate(self):
        """QuotaConfig can be instantiated."""
        obj = QuotaConfig(
            daily_quota=10000,
            conservative_threshold=0.24,
            aggressive_threshold=0.72,
        )
        assert obj.daily_quota == 10000
        assert obj.conservative_threshold == 0.24

    def test_no_dict_attribute(self):
        """QuotaConfig should not have __dict__ when slots=True."""
        obj = QuotaConfig()
        with pytest.raises(AttributeError):
            _ = obj.__dict__

    def test_attributes_accessible(self):
        """All attributes are accessible without errors."""
        obj = QuotaConfig(
            daily_quota=10000,
            conservative_threshold=0.24,
            aggressive_threshold=0.72,
            api_cost_per_video_metadata=1,
            api_cost_per_transcript=1,
            api_cost_per_channel=1,
        )
        assert obj.daily_quota == 10000
        assert obj.conservative_threshold == 0.24
        assert obj.aggressive_threshold == 0.72
        assert obj.api_cost_per_video_metadata == 1
        assert obj.api_cost_per_transcript == 1
        assert obj.api_cost_per_channel == 1


class TestChannelPreviewSlots:
    """Test ChannelPreview has slots enabled."""

    def test_instantiate(self):
        """ChannelPreview can be instantiated."""
        from yt_fts.download.dry_run_enhanced import PreviewStatus

        obj = ChannelPreview(
            channel_input="@test",
            status=PreviewStatus.SUCCESS,
            channel_id="UC123",
            channel_name="Test Channel",
        )
        assert obj.channel_input == "@test"
        assert obj.status == PreviewStatus.SUCCESS

    def test_no_dict_attribute(self):
        """ChannelPreview should not have __dict__ when slots=True."""
        from yt_fts.download.dry_run_enhanced import PreviewStatus

        obj = ChannelPreview(
            channel_input="@test",
            status=PreviewStatus.SUCCESS,
        )
        with pytest.raises(AttributeError):
            _ = obj.__dict__

    def test_attributes_accessible(self):
        """All attributes are accessible without errors."""
        from yt_fts.download.dry_run_enhanced import PreviewStatus

        obj = ChannelPreview(
            channel_input="@test",
            status=PreviewStatus.SUCCESS,
            channel_id="UC123",
            channel_name="Test Channel",
            videos_in_db=100,
            estimated_new_videos=10,
            quota_cost=5,
            message="Test message",
            would_download=True,
        )
        assert obj.channel_input == "@test"
        assert obj.status == PreviewStatus.SUCCESS
        assert obj.channel_id == "UC123"
        assert obj.channel_name == "Test Channel"
        assert obj.videos_in_db == 100
        assert obj.estimated_new_videos == 10
        assert obj.quota_cost == 5
        assert obj.message == "Test message"
        assert obj.would_download is True


class TestDryRunSummarySlots:
    """Test DryRunSummary has slots enabled."""

    def test_instantiate(self):
        """DryRunSummary can be instantiated."""
        obj = DryRunSummary(
            total_channels=5,
            valid_channels=4,
            channels_with_new_videos=3,
            estimated_quota_cost=10,
            estimated_new_videos=100,
        )
        assert obj.total_channels == 5
        assert obj.valid_channels == 4

    def test_no_dict_attribute(self):
        """DryRunSummary should not have __dict__ when slots=True."""
        obj = DryRunSummary()
        with pytest.raises(AttributeError):
            _ = obj.__dict__

    def test_attributes_accessible(self):
        """All attributes are accessible without errors."""
        obj = DryRunSummary(
            total_channels=5,
            valid_channels=4,
            channels_with_new_videos=3,
            estimated_quota_cost=10,
            estimated_new_videos=100,
            channels_previewed=[],
        )
        assert obj.total_channels == 5
        assert obj.valid_channels == 4
        assert obj.channels_with_new_videos == 3
        assert obj.estimated_quota_cost == 10
        assert obj.estimated_new_videos == 100
        assert obj.channels_previewed == []


class TestCookieTestResultSlots:
    """Test CookieTestResult has slots enabled."""

    def test_instantiate(self):
        """CookieTestResult can be instantiated."""
        from yt_fts.download.cookie_auth_tester import CookieTestStatus

        obj = CookieTestResult(
            status=CookieTestStatus.VALID,
            message="Cookies working",
            video_id="dQw4w9WgXcQ",
            availability="public",
        )
        assert obj.status == CookieTestStatus.VALID
        assert obj.message == "Cookies working"

    def test_no_dict_attribute(self):
        """CookieTestResult should not have __dict__ when slots=True."""
        from yt_fts.download.cookie_auth_tester import CookieTestStatus

        obj = CookieTestResult(
            status=CookieTestStatus.VALID,
            message="Test",
            video_id="abc123",
        )
        with pytest.raises(AttributeError):
            _ = obj.__dict__

    def test_attributes_accessible(self):
        """All attributes are accessible without errors."""
        from yt_fts.download.cookie_auth_tester import CookieTestStatus

        obj = CookieTestResult(
            status=CookieTestStatus.VALID,
            message="Cookies working",
            video_id="dQw4w9WgXcQ",
            availability="public",
        )
        assert obj.status == CookieTestStatus.VALID
        assert obj.message == "Cookies working"
        assert obj.video_id == "dQw4w9WgXcQ"
        assert obj.availability == "public"


class TestCheckpointEntrySlots:
    """Test CheckpointEntry has slots enabled."""

    def test_instantiate(self):
        """CheckpointEntry can be instantiated."""
        obj = CheckpointEntry(
            video_id="abc123",
            channel_id="UC123",
            timestamp="2024-01-01T00:00:00Z",
            success=True,
        )
        assert obj.video_id == "abc123"
        assert obj.channel_id == "UC123"

    def test_no_dict_attribute(self):
        """CheckpointEntry should not have __dict__ when slots=True."""
        obj = CheckpointEntry(
            video_id="abc123",
            channel_id="UC123",
            timestamp="2024-01-01T00:00:00Z",
        )
        with pytest.raises(AttributeError):
            _ = obj.__dict__

    def test_attributes_accessible(self):
        """All attributes are accessible without errors."""
        obj = CheckpointEntry(
            video_id="abc123",
            channel_id="UC123",
            timestamp="2024-01-01T00:00:00Z",
            success=True,
            error_message=None,
        )
        assert obj.video_id == "abc123"
        assert obj.channel_id == "UC123"
        assert obj.timestamp == "2024-01-01T00:00:00Z"
        assert obj.success is True
        assert obj.error_message is None


class TestCheckpointResultSlots:
    """Test CheckpointResult has slots enabled."""

    def test_instantiate(self):
        """CheckpointResult can be instantiated."""
        from yt_fts.download.download_checkpoint import CheckpointStatus

        obj = CheckpointResult(
            status=CheckpointStatus.SUCCESS,
            message="Completed",
            total_downloaded=100,
        )
        assert obj.status == CheckpointStatus.SUCCESS
        assert obj.message == "Completed"

    def test_no_dict_attribute(self):
        """CheckpointResult should not have __dict__ when slots=True."""
        from yt_fts.download.download_checkpoint import CheckpointStatus

        obj = CheckpointResult(
            status=CheckpointStatus.SUCCESS,
            message="Completed",
        )
        with pytest.raises(AttributeError):
            _ = obj.__dict__

    def test_attributes_accessible(self):
        """All attributes are accessible without errors."""
        from yt_fts.download.download_checkpoint import (
            CheckpointEntry,
            CheckpointStatus,
        )

        entry = CheckpointEntry(
            video_id="abc123",
            channel_id="UC123",
            timestamp="2024-01-01T00:00:00Z",
        )
        obj = CheckpointResult(
            status=CheckpointStatus.SUCCESS,
            message="Completed",
            entry=entry,
            total_downloaded=100,
        )
        assert obj.status == CheckpointStatus.SUCCESS
        assert obj.message == "Completed"
        assert obj.entry == entry
        assert obj.total_downloaded == 100


class TestValidationResultSlots:
    """Test ValidationResult has slots enabled."""

    def test_instantiate(self):
        """ValidationResult can be instantiated."""
        from yt_fts.download.cookie_validator import ValidationStatus

        obj = ValidationResult(
            status=ValidationStatus.SUCCESS,
            message="Valid",
            cookie_count=10,
            important_cookies=["session", "login"],
        )
        assert obj.status == ValidationStatus.SUCCESS
        assert obj.message == "Valid"

    def test_no_dict_attribute(self):
        """ValidationResult should not have __dict__ when slots=True."""
        from yt_fts.download.cookie_validator import ValidationStatus

        obj = ValidationResult(
            status=ValidationStatus.SUCCESS,
            message="Valid",
        )
        with pytest.raises(AttributeError):
            _ = obj.__dict__

    def test_attributes_accessible(self):
        """All attributes are accessible without errors."""
        from yt_fts.download.cookie_validator import ValidationStatus

        obj = ValidationResult(
            status=ValidationStatus.SUCCESS,
            message="Valid",
            cookie_count=10,
            important_cookies=["session", "login"],
            browser="firefox",
            cookie_file_path="/path/to/cookies.txt",
        )
        assert obj.status == ValidationStatus.SUCCESS
        assert obj.message == "Valid"
        assert obj.cookie_count == 10
        assert obj.important_cookies == ["session", "login"]
        assert obj.browser == "firefox"
        assert obj.cookie_file_path == "/path/to/cookies.txt"


class TestInconsistencyReportSlots:
    """Test InconsistencyReport has slots enabled."""

    def test_instantiate(self):
        """InconsistencyReport can be instantiated."""
        obj = InconsistencyReport(
            type="impossible_count",
            severity="critical",
            reason="with_subs > total",
        )
        assert obj.type == "impossible_count"
        assert obj.severity == "critical"

    def test_no_dict_attribute(self):
        """InconsistencyReport should not have __dict__ when slots=True."""
        obj = InconsistencyReport(
            type="video_gap",
            severity="high",
            reason="Gap detected",
        )
        with pytest.raises(AttributeError):
            _ = obj.__dict__

    def test_attributes_accessible(self):
        """All attributes are accessible without errors."""
        obj = InconsistencyReport(
            type="video_gap",
            severity="high",
            reason="Gap detected",
            special_total=10,
            unexplained_gap=5,
        )
        assert obj.type == "video_gap"
        assert obj.severity == "high"
        assert obj.reason == "Gap detected"
        assert obj.special_total == 10
        assert obj.unexplained_gap == 5


class TestBatchDownloadConfigSlots:
    """Test BatchDownloadConfig has slots enabled."""

    def test_instantiate(self):
        """BatchDownloadConfig can be instantiated with defaults."""
        obj = BatchDownloadConfig()
        assert obj.jobs == 2
        assert obj.language == "en"

    def test_no_dict_attribute(self):
        """BatchDownloadConfig should not have __dict__ when slots=True."""
        obj = BatchDownloadConfig()
        with pytest.raises(AttributeError):
            _ = obj.__dict__

    def test_attributes_accessible(self):
        """Key attributes are accessible without errors."""
        obj = BatchDownloadConfig(
            jobs=4,
            language="es",
            cookies_from_browser="chrome",
            delay=30.0,
            max_retries=5,
            parallel_workers=8,
            auto_backfill=True,
        )
        assert obj.jobs == 4
        assert obj.language == "es"
        assert obj.cookies_from_browser == "chrome"
        assert obj.delay == 30.0
        assert obj.max_retries == 5
        assert obj.parallel_workers == 8
        assert obj.auto_backfill is True


class TestUIConfigSlots:
    """Test UIConfig has slots enabled."""

    def test_instantiate(self):
        """UIConfig can be instantiated."""
        obj = UIConfig()
        assert obj.rich_mode is None
        assert obj.display_plugin is None

    def test_no_dict_attribute(self):
        """UIConfig should not have __dict__ when slots=True."""
        obj = UIConfig()
        with pytest.raises(AttributeError):
            _ = obj.__dict__

    def test_attributes_accessible(self):
        """All attributes are accessible without errors."""
        obj = UIConfig(
            rich_mode="new",
            display_plugin="default",
            suppress_verbose=True,
        )
        assert obj.rich_mode == "new"
        assert obj.display_plugin == "default"
        assert obj.suppress_verbose is True
