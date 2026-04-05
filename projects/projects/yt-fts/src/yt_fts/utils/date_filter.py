"""
Date filtering utilities for yt-fts search commands.
"""
import re
from datetime import datetime, timedelta


def validate_date_format(date_str: str) -> bool:
    """
    Validate that a date string is in YYYY-MM-DD format.

    Args:
        date_str: Date string to validate

    Returns:
        True if valid, False otherwise
    """
    if not date_str:
        return True  # None is valid

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def parse_last_option(last_str: str) -> str | None:
    """
    Parse --last option (e.g., "7d", "1m", "3y") and return date string.

    Args:
        last_str: String like "7d", "1m", "3y"

    Returns:
        Date string in YYYY-MM-DD format, or None if invalid

    Raises:
        ValueError: If format is invalid
    """
    if not last_str:
        return None

    match = re.match(r"^(\d+)([dmy])$", last_str.lower())
    if not match:
        msg = f"Invalid --last format: '{last_str}'. Expected format: Nd (days), Nm (months), Ny (years)"
        raise ValueError(
            msg
        )

    amount = int(match.group(1))
    unit = match.group(2)

    now = datetime.now()
    if unit == "d":
        delta = timedelta(days=amount)
    elif unit == "m":
        # Approximate month as 30 days
        delta = timedelta(days=amount * 30)
    elif unit == "y":
        # Approximate year as 365 days
        delta = timedelta(days=amount * 365)
    else:
        msg = f"Invalid unit: {unit}"
        raise ValueError(msg)

    result_date = now - delta
    return result_date.strftime("%Y-%m-%d")


def parse_date_filters(
    after: str | None = None,
    before: str | None = None,
    last: str | None = None,
) -> tuple[str | None, str | None]:
    """
    Parse and validate date filter options.

    Args:
        after: Date string in YYYY-MM-DD format (videos after this date)
        before: Date string in YYYY-MM-DD format (videos before this date)
        last: Relative date like "7d", "1m", "3y"

    Returns:
        Tuple of (after_date, before_date) in YYYY-MM-DD format or None

    Raises:
        ValueError: If date format is invalid
    """
    # Handle --last option (overrides --after)
    if last:
        after = parse_last_option(last)

    # Validate date formats
    if after and not validate_date_format(after):
        msg = f"Invalid --after date format: '{after}'. Expected YYYY-MM-DD format."
        raise ValueError(
            msg
        )

    if before and not validate_date_format(before):
        msg = f"Invalid --before date format: '{before}'. Expected YYYY-MM-DD format."
        raise ValueError(
            msg
        )

    return after, before
