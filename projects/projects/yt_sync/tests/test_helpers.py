import re


def sanitize_filename(title: str | None) -> str:
    """Sanitize filenames by removing invalid characters."""
    if title is None or title == "None" or title == "":
        return "untitled"
    # Replace invalid characters with underscores
    sanitized = re.sub(r"[/\\:*?\"<>|]", "_", title.strip())
    # Replace multiple spaces with a single space
    sanitized = re.sub(r"\s+", " ", sanitized)
    return sanitized
