"""Content security validation for URLs and content."""

import re

class ContentSecurityValidator:
    """Validates URLs and content for security risks.

    Attributes:
        dangerous_patterns: List of dangerous regex patterns to detect.
        safe_content_types: Set of allowed content types.
        blocked_domains: Set of blocked domains.
        max_url_length: Maximum allowed URL length.
        max_content_size: Maximum allowed content size in bytes.
    """

    # Dangerous patterns to detect in URLs and content
    DANGEROUS_PATTERNS = [
        r"onclick\s*=",
        r"onerror\s*=",
        r"onload\s*=",
        r"onmouseover\s*=",
        r"eval\s*\(",
        r"<script[^>]*>",
        r"javascript:",
        r"vbscript:",
        r"data:",
    ]

    # Blocked domains (ads, tracking, known malicious)
    BLOCKED_DOMAINS = {
        "ads.doubleclick.net",
        "doubleclick.net",
        "googleads.com",
        "googlesyndication.com",
        "facebook.com/tr",
        "facebookpixel.com",
        "tracking.example.com",
    }

    # Safe content types
    SAFE_CONTENT_TYPES = {
        "text/html",
        "text/plain",
        "text/markdown",
        "text/xml",
        "application/json",
        "application/xml",
        "text/css",
        "text/javascript",
        "application/javascript",
    }

    # Unsafe protocols
    UNSAFE_PROTOCOLS = {
        "file:",
        "javascript:",
        "data:",
        "ftp:",
        "vbscript:",
        "mailto:",
        "telnet:",
    }

    def __init__(
        self,
        max_url_length: int = 2048,
        max_content_size: int = 1024 * 1024,  # 1MB
    ):
        """Initialize ContentSecurityValidator.

        Args:
            max_url_length: Maximum allowed URL length.
            max_content_size: Maximum allowed content size in bytes.
        """
        self.dangerous_patterns = self.DANGEROUS_PATTERNS
        self.safe_content_types = self.SAFE_CONTENT_TYPES
        self.blocked_domains = self.BLOCKED_DOMAINS
        self.max_url_length = max_url_length
        self.max_content_size = max_content_size

    def validate_url(self, url: str | None) -> tuple[bool, str | None]:
        """Validate a URL for security issues.

        Args:
            url: The URL to validate.

        Returns:
            Tuple of (is_valid, error_message). error_message is None if valid.
        """
        # Check for None or empty
        if url is None:
            return False, "URL cannot be None"

        if not url or not isinstance(url, str):
            return False, "URL must be a non-empty string"

        url = url.strip()

        if not url:
            return False, "URL cannot be empty"

        # Check URL length
        if len(url) > self.max_url_length:
            return False, f"URL is too long (max {self.max_url_length} characters)"

        # Check for unsafe protocols
        url_lower = url.lower()
        for protocol in self.UNSAFE_PROTOCOLS:
            if url_lower.startswith(protocol):
                return False, f"Unsupported protocol: {protocol}"

        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False, f"Dangerous pattern detected: {pattern}"

        # Check for blocked domains
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            # Remove port if present
            if ":" in domain:
                domain = domain.split(":")[0]

            # Check if domain or any parent domain is blocked
            for blocked in self.blocked_domains:
                if domain == blocked or domain.endswith("." + blocked):
                    return False, f"Blocked domain: {domain}"

            # Check for missing domain
            if not parsed.netloc:
                return False, "Missing domain in URL"

        except Exception:
            return False, "Invalid URL format"

        return True, None

    def validate_content(
        self, content: str, content_type: str = "text/html"
    ) -> tuple[bool, str | None]:
        """Validate content for security issues.

        Args:
            content: The content to validate.
            content_type: The content type (MIME type).

        Returns:
            Tuple of (is_safe, error_message). error_message is None if safe.
        """
        # Check for empty content
        if not content:
            return False, "Content is empty"

        # Check content size
        if len(content) > self.max_content_size:
            return False, f"Content too large (max {self.max_content_size} bytes)"

        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return False, f"Dangerous pattern detected in content: {pattern}"

        # Check content type safety
        if content_type and content_type not in self.safe_content_types:
            # Warn but allow - could be text/plain, binary files etc.
            # For safety, we reject unknown executable types
            if content_type.startswith("application/"):
                if content_type not in [
                    "application/json",
                    "application/xml",
                    "application/javascript",
                ]:
                    return False, f"Potentially unsafe content type: {content_type}"

        return True, None
