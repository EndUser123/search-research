import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse


def _validate_video_source(source: str) -> dict:
    """Comprehensive validation of video sources with security checks.

    Args:
        source: Video source (URL or file path)

    Returns:
        dict: {'valid': bool, 'type': str, 'sanitized': str, 'error': str}
    """
    if not source or not isinstance(source, str):
        return {
            "valid": False,
            "type": "invalid",
            "sanitized": "",
            "error": "Empty or invalid source",
        }

    source = source.strip()
    if not source:
        return {
            "valid": False,
            "type": "invalid",
            "sanitized": "",
            "error": "Empty source after stripping",
        }

    # Check for YouTube URLs
    youtube_patterns = [
        r"^https?://(?:www\.)?youtube\.com/watch\?v=[\w-]{11}",
        r"^https?://(?:www\.)?youtube\.com/embed/[\w-]{11}",
        r"^https?://(?:www\.)?youtu\.be/[\w-]{11}",
        r"^https?://(?:www\.)?youtube\.com/shorts/[\w-]{11}",
    ]

    for pattern in youtube_patterns:
        if re.match(pattern, source, re.IGNORECASE):
            # Additional YouTube URL validation
            try:
                parsed = urlparse(source)
                if parsed.netloc.lower() not in [
                    "youtube.com",
                    "www.youtube.com",
                    "youtu.be",
                ]:
                    return {
                        "valid": False,
                        "type": "url",
                        "sanitized": source,
                        "error": "Invalid YouTube domain",
                    }

                # Extract video ID for additional validation
                if "v=" in source:
                    video_id = parse_qs(parsed.query).get("v", [""])[0]
                    if not re.match(r"^[\w-]{11}$", video_id):
                        return {
                            "valid": False,
                            "type": "url",
                            "sanitized": source,
                            "error": "Invalid YouTube video ID",
                        }

                return {
                    "valid": True,
                    "type": "youtube",
                    "sanitized": source,
                    "error": "",
                }
            except Exception as e:
                return {
                    "valid": False,
                    "type": "url",
                    "sanitized": source,
                    "error": f"URL parsing error: {e}",
                }

    # Check for other video URLs (general validation)
    if source.startswith(("http://", "https://")):
        try:
            parsed = urlparse(source)
            if not parsed.netloc:
                return {
                    "valid": False,
                    "type": "url",
                    "sanitized": source,
                    "error": "Invalid URL format",
                }

            # Basic security checks for non-YouTube URLs
            if any(
                char in source
                for char in ["|", "&", ";", "`", "$", "(", ")", "{", "}", "<", ">"]
            ):
                return {
                    "valid": False,
                    "type": "url",
                    "sanitized": source,
                    "error": "Potentially malicious characters in URL",
                }

            return {"valid": True, "type": "url", "sanitized": source, "error": ""}
        except Exception as e:
            return {
                "valid": False,
                "type": "url",
                "sanitized": source,
                "error": f"URL validation error: {e}",
            }

    # File path validation
    try:
        # Prevent path traversal attacks
        if ".." in source or source.startswith(("/", "\\")):
            return {
                "valid": False,
                "type": "path",
                "sanitized": source,
                "error": "Potential path traversal attack",
            }

        # Check for suspicious characters in file paths
        suspicious_chars = ["|", "&", ";", "`", "$", ">", "<", "?", "*"]
        if any(char in source for char in suspicious_chars):
            return {
                "valid": False,
                "type": "path",
                "sanitized": source,
                "error": "Suspicious characters in file path",
            }

        # Validate file extension
        path_obj = Path(source)
        if path_obj.suffix.lower() not in [
            ".mp4",
            ".avi",
            ".mov",
            ".mkv",
            ".flv",
            ".webm",
            ".wmv",
        ]:
            return {
                "valid": False,
                "type": "path",
                "sanitized": source,
                "error": "Unsupported video file format",
            }

        # Check if file exists (for local files)
        if path_obj.exists():
            if not path_obj.is_file():
                return {
                    "valid": False,
                    "type": "path",
                    "sanitized": source,
                    "error": "Path is not a file",
                }

            # Basic file size check (prevent processing extremely large files)
            try:
                file_size = path_obj.stat().st_size
                if file_size > 10 * 1024 * 1024 * 1024:  # 10GB limit
                    return {
                        "valid": False,
                        "type": "path",
                        "sanitized": source,
                        "error": "File too large (max 10GB)",
                    }
                if file_size == 0:
                    return {
                        "valid": False,
                        "type": "path",
                        "sanitized": source,
                        "error": "File is empty",
                    }
            except OSError:
                return {
                    "valid": False,
                    "type": "path",
                    "sanitized": source,
                    "error": "Cannot access file",
                }

        return {"valid": True, "type": "file", "sanitized": str(path_obj), "error": ""}

    except Exception as e:
        return {
            "valid": False,
            "type": "path",
            "sanitized": source,
            "error": f"Path validation error: {e}",
        }


# Test the validation function
test_cases = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://youtu.be/dQw4w9WgXcQ",
    "test.mp4",
    "malicious|command",
    "../../../etc/passwd",
    "",
    None,
    "https://malicious.com/script.js",
    "video.mov",
]

print("Testing input validation function:")
for test in test_cases:
    result = _validate_video_source(test)
    print(f"Input: {test}")
    print(f"Result: {result}")
    print()
