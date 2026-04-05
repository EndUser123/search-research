#!/usr/bin/env python3
"""
Fix inconsistent authentication error handling - simplified version
"""

import re


def fix_authentication_error_handling():
    """Fix inconsistent authentication error handling with centralized error management"""

    file_path = "C:/_Python/_Projects/ai_studio/src/ai_studio/youtube_cookies.py"

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Add centralized error handling function if it doesn't exist
    if "_handle_auth_error" not in content:
        # Find the end of __init__ method and add our function after it
        init_end_pattern = r"(def __init__\(self.*?)(\n\s*pass\n)"

        def add_error_handler(match):
            init_code = match.group(1)
            pass_statement = match.group(2)
            error_handler_func = '''\\n\\n    def _handle_auth_error(self, error: Exception, context: str = "authentication") -> str:
        """Centralized error handling for authentication failures with user-friendly messages."""
        error_msg = str(error).lower()
        error_type = type(error).__name__

        # Categorize errors and provide actionable guidance
        if "blocked" in error_msg or "verification failed" in error_msg or "unusual traffic" in error_msg:
            user_message = "Authentication blocked by Google. Try waiting 30+ minutes or using a different network."
            log_level = "error"
        elif "timeout" in error_msg or "timed out" in error_msg:
            user_message = "Authentication timed out. Check your internet connection and try again."
            log_level = "warning"
        elif "element not found" in error_msg or "no such element" in error_msg:
            user_message = "Authentication page elements not found. Google may have changed their login page."
            log_level = "warning"
        elif "network" in error_msg or "connection" in error_msg:
            user_message = "Network connection issue during authentication. Check your internet connection."
            log_level = "warning"
        elif "permission" in error_msg or "denied" in error_msg:
            user_message = "Browser permission denied. Ensure browser automation is allowed."
            log_level = "warning"
        elif "geckodriver" in error_msg or "firefox" in error_msg:
            user_message = "Firefox/geckodriver issue detected. Ensure Firefox is properly installed."
            log_level = "error"
        else:
            user_message = f"Authentication failed during {context}: {error_msg}"
            log_level = "error"

        # Log with appropriate level
        if log_level == "error":
            self.logger.error(f"❌ Auth Error ({context}): {error_type} - {error_msg}")
            self.logger.error(f"💡 User Guidance: {user_message}")
        else:
            self.logger.warning(f"⚠️ Auth Issue ({context}): {error_type} - {error_msg}")
            self.logger.warning(f"💡 User Guidance: {user_message}")

        return user_message
'''
            return init_code + pass_statement + error_handler_func

        new_content = re.sub(
            init_end_pattern, add_error_handler, content, flags=re.DOTALL
        )

        if new_content != content:
            content = new_content
            print("✅ Added centralized error handling function")
        else:
            print("ℹ️ Could not find insertion point for error handler")
    else:
        print("ℹ️ Centralized error handler already exists")

    # Fix simple error handling patterns
    simple_patterns = [
        (
            r'except Exception as e:\s*logger\.error\(f".*?failed.*?: \{e\}"\)',
            'except Exception as e:\n                    user_message = self._handle_auth_error(e, "operation")',
        ),
        (
            r'except Exception as e:\s*self\.logger\.error\(f".*?failed.*?: \{e\}"\)',
            'except Exception as e:\n                user_message = self._handle_auth_error(e, "operation")',
        ),
    ]

    for pattern, replacement in simple_patterns:
        new_content = re.sub(
            pattern, replacement, content, flags=re.MULTILINE | re.DOTALL
        )
        if new_content != content:
            content = new_content
            print("✅ Fixed error handling pattern")
        else:
            content = new_content  # Ensure we keep previous changes

    # Write the improved content back to the file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Authentication error handling improvements completed")
    return True


if __name__ == "__main__":
    fix_authentication_error_handling()
