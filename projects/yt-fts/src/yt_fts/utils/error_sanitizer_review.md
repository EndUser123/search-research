# Error Sanitization Review and Recommendations

## Overview
This document reviews the `error_sanitizer.py` module, which provides secure logging
by redacting sensitive information from error messages and context.

## Current Implementation Review

### Strengths

1. **Comprehensive Sensitive Key Detection**
   - Covers common sensitive patterns: API keys, tokens, passwords, secrets
   - Checks key names case-insensitively
   - Includes variants like "apikey", "api-key", "auth_key", etc.

2. **Privacy-First Approach**
   - Shows only first/last 4 chars for sensitive values
   - Redacts file paths to show only filename
   - Handles both dictionary context and raw string messages

3. **Multiple Integration Points**
   - `sanitize_error_context()`: For structured logging
   - `sanitize_log_message()`: For raw string sanitization
   - `get_sanitized_logger()`: Drop-in replacement for standard loggers

### Potential Issues & Recommendations

#### 1. **Over-Aggressive Path Redaction** (MEDIUM)
**Issue:** Path sanitization is too aggressive, losing diagnostic value.

```python
# Current: All paths reduced to "...filename"
"/home/user/projects/yt-fts/data/config.json" → "...config.json"
```

**Impact:** Difficult to trace which component/file had an error.

**Recommendation:**
```python
# Show partial path (last 2-3 directories)
"/home/user/projects/yt-fts/data/config.json" → ".../yt-fts/data/config.json"
```

#### 2. **API Key Pattern Misses** (LOW)
**Issue:** Regex pattern for API keys doesn't cover all formats.

**Missing:**
- Google API keys: `AIzaSyXXXXXXXXXXXXXXXXXXXXXXX`
- Firebase: `AAAAAXXXXXXX`
- OAuth client IDs: `123456789-abc123.apps.googleusercontent.com`

**Recommendation:** Add these patterns to `sanitize_log_message()`:
```python
# Add to regex patterns:
r'(AIza[A-Za-z0-9_-]{35})',  # Google API keys
r'(AAAAA[A-Za-z0-9_-]{35})',  # Firebase
r'[\w.-]+\.apps\.googleusercontent\.com',  # OAuth client IDs
```

#### 3. **Cookie Value Redaction** (MEDIUM)
**Issue:** Cookie values are partially shown (first/last 4 chars), but:
- YouTube cookies like `SID`, `HSID`, `SSID` should be fully redacted
- Session tokens are sensitive even with partial disclosure

**Recommendation:**
```python
def _is_session_cookie(cookie_name: str) -> bool:
    """Check if cookie is a session identifier."""
    session_patterns = ["sid", "ssid", "hsid", "sessionid", "phpsessid"]
    return any(pattern in cookie_name.lower() for pattern in session_patterns)

# In sanitize_error_context():
if is_sensitive and isinstance(value, str):
    if key_lower in ["cookie", "cookies"] or _is_session_cookie(key):
        sanitized[key] = "[REDACTED]"  # Full redaction for session cookies
    elif len(value) > 8:
        sanitized[key] = f"{value[:4]}...{value[-4:]}"  # Partial for others
```

#### 4. **Query Parameter Redaction** (LOW)
**Issue:** URLs with sensitive query params aren't sanitized.

**Example:**
```
"https://api.example.com/endpoint?api_key=sk-1234567890abcdef&token=xyz"
```

**Recommendation:**
```python
def sanitize_url(url: str) -> str:
    """Redact sensitive query parameters from URLs."""
    import re
    sensitive_params = ["api_key", "token", "password", "secret"]
    for param in sensitive_params:
        url = re.sub(f"{param}=[^&]+", f"{param}=[REDACTED]", url, flags=re.IGNORECASE)
    return url
```

#### 5. **Error Stack Trace Sanitization** (HIGH)
**Issue:** Stack traces may contain sensitive info in:
- Function arguments
- Local variable names
- File paths

**Recommendation:** Add stack trace sanitization:
```python
import traceback

def sanitize_traceback(exc: Exception) -> str:
    """Sanitize a traceback while preserving debug info."""
    tb_lines = traceback.format_exception(type(exc), exc, exc.__traceback__)

    # Sanitize each line
    sanitized_lines = []
    for line in tb_lines:
        # Sanitize file paths (keep structure)
        line = re.sub(r'File "([^"]+)"', lambda m: f'File "{sanitize_path(m.group(1))}"', line)
        # Sanitize string values in lines (but preserve structure)
        line = sanitize_log_message(line)
        sanitized_lines.append(line)

    return "".join(sanitized_lines)
```

## Balance: Privacy vs Debuggability

### Diagnostic Information Preserved
| Information | Handling | Retained? |
|-------------|----------|-----------|
| Error type/category | ✓ | Yes |
| Error message | ✓ | Yes (sanitized) |
| Stack trace structure | ✓ | Yes (paths sanitized) |
| File names | ✓ | Yes |
| Error context | ✓ | Yes (values sanitized) |
| Function names | ✓ | Yes |

### Sensitive Information Redacted
| Information | Redaction Level |
|-------------|----------------|
| API keys/tokens | First/last 4 chars → Full for sessions |
| Passwords/secrets | Full redaction |
| File paths | Filename only → Recommend partial path |
| Cookies | Partial → Recommend full for sessions |
| Query params | Not implemented → Should be added |

## Recommended Enhancements

### Priority 1: High
1. Add stack trace sanitization (`sanitize_traceback()`)
2. Full redaction for session cookies
3. Add URL query parameter sanitization

### Priority 2: Medium
4. Partial path redaction (last 2-3 directories)
5. Expand API key regex patterns

### Priority 3: Low
6. Add user-configurable sanitization levels
7. Add allowlist for local development (skip sanitization)

## Implementation Example

```python
# Enhanced sanitization with debuggable paths

def sanitize_path_for_debug(path: str, keep_dirs: int = 2) -> str:
    """
    Sanitize path while keeping some directory structure for debugging.

    Args:
        path: Full file path
        keep_dirs: Number of trailing directories to keep

    Returns:
        Sanitized path with partial structure
    """
    path_obj = Path(path)
    parts = path_obj.parts

    if len(parts) <= keep_dirs:
        return path_obj.name  # Short path, just filename

    # Keep last N directories
    kept_parts = parts[-keep_dirs:]
    return "..." / Path(*kept_parts)

# Usage:
sanitize_path_for_debug("/home/user/projects/yt-fts/data/config.json")
# Returns: ".../yt-fts/data/config.json" (more debuggable than just "config.json")
```

## Summary

The current error sanitization implementation is **solid** with good coverage
of common sensitive patterns. The main areas for improvement are:

1. **Balance privacy with debuggability** - Partial paths instead of just filenames
2. **Expand pattern coverage** - More API key formats, URL query params
3. **Stack trace sanitization** - Important for exception logging
4. **Session cookie handling** - Full redaction for auth/session identifiers

The module is **production-ready** as-is, but would benefit from the above
enhancements to improve debugging capabilities while maintaining privacy.
