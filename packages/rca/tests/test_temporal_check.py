"""Tests for temporal_check module.

Tests for time-based validation and staleness checks.
"""

import pytest
from datetime import datetime, timedelta, UTC

from rca.temporal_check import (
    StalenessStatus,
    TemporalCheck,
    TimeValidator,
)


class TestStalenessStatus:
    """Test StalenessStatus enum."""

    def test_status_values(self):
        """StalenessStatus has expected values."""
        assert StalenessStatus.FRESH.value == "fresh"
        assert StalenessStatus.STALE.value == "stale"
        assert StalenessStatus.EXPIRED.value == "expired"


class TestTimeValidatorInit:
    """Test TimeValidator initialization."""

    def test_default_creation(self):
        """TimeValidator can be created with defaults."""
        validator = TimeValidator()

        assert validator is not None

    def test_custom_thresholds(self):
        """Custom thresholds can be set."""
        validator = TimeValidator(
            fresh_threshold_hours=24,
            stale_threshold_hours=72,
        )

        assert validator.fresh_threshold_hours == 24


class TestCheckStaleness:
    """Test staleness checking."""

    def test_fresh_timestamp(self):
        """Recent timestamp is fresh."""
        validator = TimeValidator()
        now = datetime.now(UTC)

        status = validator.check_staleness(now)

        assert status == StalenessStatus.FRESH

    def test_stale_timestamp(self):
        """Old timestamp is stale."""
        validator = TimeValidator(fresh_threshold_hours=1)
        old_time = datetime.now(UTC) - timedelta(hours=2)

        status = validator.check_staleness(old_time)

        assert status == StalenessStatus.STALE

    def test_expired_timestamp(self):
        """Very old timestamp is expired."""
        validator = TimeValidator(
            fresh_threshold_hours=1,
            stale_threshold_hours=2,
        )
        old_time = datetime.now(UTC) - timedelta(hours=3)

        status = validator.check_staleness(old_time)

        assert status == StalenessStatus.EXPIRED


class TestIsFresh:
    """Test freshness checks."""

    def test_is_fresh_true(self):
        """Recent time is fresh."""
        validator = TimeValidator(fresh_threshold_hours=24)
        recent = datetime.now(UTC) - timedelta(hours=1)

        assert validator.is_fresh(recent) is True

    def test_is_fresh_false(self):
        """Old time is not fresh."""
        validator = TimeValidator(fresh_threshold_hours=24)
        old = datetime.now(UTC) - timedelta(hours=25)

        assert validator.is_fresh(old) is False


class TestIsStale:
    """Test staleness checks."""

    def test_is_stale_true(self):
        """Stale time is identified."""
        validator = TimeValidator(fresh_threshold_hours=24)
        stale = datetime.now(UTC) - timedelta(hours=25)

        assert validator.is_stale(stale) is True

    def test_is_stale_false(self):
        """Fresh time is not stale."""
        validator = TimeValidator(fresh_threshold_hours=24)
        fresh = datetime.now(UTC) - timedelta(hours=1)

        assert validator.is_stale(fresh) is False


class TestIsExpired:
    """Test expiration checks."""

    def test_is_expired_true(self):
        """Expired time is identified."""
        validator = TimeValidator(stale_threshold_hours=48)
        expired = datetime.now(UTC) - timedelta(hours=49)

        assert validator.is_expired(expired) is True

    def test_is_expired_false(self):
        """Recent time is not expired."""
        validator = TimeValidator(stale_threshold_hours=48)
        recent = datetime.now(UTC) - timedelta(hours=1)

        assert validator.is_expired(recent) is False


class TestTemporalCheck:
    """Test TemporalCheck functionality."""

    def test_temporal_check_creation(self):
        """TemporalCheck can be created."""
        check = TemporalCheck(
            timestamp=datetime.now(UTC),
            context="RCA session",
        )

        assert check.context == "RCA session"

    def test_get_age(self):
        """Age can be calculated."""
        past = datetime.now(UTC) - timedelta(hours=2)
        check = TemporalCheck(timestamp=past)

        age = check.get_age()

        assert age.total_seconds() >= timedelta(hours=2).total_seconds()

    def test_get_status(self):
        """Status can be retrieved."""
        validator = TimeValidator(fresh_threshold_hours=24)
        check = TemporalCheck(
            timestamp=datetime.now(UTC),
            validator=validator,
        )

        status = check.get_status()

        assert status == StalenessStatus.FRESH


class TestEdgeCases:
    """Test edge cases."""

    def test_none_timestamp(self):
        """None timestamp is handled."""
        validator = TimeValidator()

        status = validator.check_staleness(None)

        assert status == StalenessStatus.EXPIRED

    def test_future_timestamp(self):
        """Future timestamp is fresh."""
        validator = TimeValidator()
        future = datetime.now(UTC) + timedelta(hours=1)

        status = validator.check_staleness(future)

        assert status == StalenessStatus.FRESH

    def test_zero_threshold(self):
        """Zero threshold means everything is stale."""
        validator = TimeValidator(fresh_threshold_hours=0)
        now = datetime.now(UTC)

        assert validator.is_fresh(now) is False
