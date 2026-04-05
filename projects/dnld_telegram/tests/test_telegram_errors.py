"""
Unit tests for error handling functions in dnld_telegram/src/download/telegram_errors.py
"""

from dnld_telegram.src.download import telegram_errors


class DummyError:
    def __str__(self):
        return "FLOOD_WAIT_42"


def test_parse_flood_wait_seconds_various_formats():
    cases = [
        ("FLOOD_WAIT_10", 10),
        ("FLOOD_WAIT_99", 99),
        ("FLOOD_WAIT_1", 1),
        ("FLOOD_WAIT_", None),
        ("No flood", None),
        ("FLOOD_WAIT_9999", 9999),
    ]
    for msg, expected in cases:
        assert (
            telegram_errors.TelegramErrorHandler.parse_flood_wait_seconds(msg)
            == expected
        )


def test_should_retry_backoff_and_limits():
    # Should retry for rate_limit, up to attempt limit
    assert telegram_errors.TelegramErrorHandler.should_retry("rate_limit", 1)[0] is True
    assert (
        telegram_errors.TelegramErrorHandler.should_retry("rate_limit", 99)[0] is False
    )
    # Should not retry for fatal
    assert telegram_errors.TelegramErrorHandler.should_retry("fatal", 1)[0] is False
    # Backoff time decreases as attempt increases (matches code logic)
    assert (
        telegram_errors.TelegramErrorHandler.should_retry("rate_limit", 5)[1]
        < telegram_errors.TelegramErrorHandler.should_retry("rate_limit", 1)[1]
    )


def test_categorize_error_patterns():
    cases = [
        ("FLOOD_WAIT_10", "rate_limit"),
        ("Too Many Requests", "rate_limit"),
        ("Cannot send requests while disconnected", "disconnection"),
        ("Timeout", "unknown"),
        ("Random error", "unknown"),
    ]
    for msg, expected in cases:
        assert telegram_errors.TelegramErrorHandler.categorize_error(msg) == expected
