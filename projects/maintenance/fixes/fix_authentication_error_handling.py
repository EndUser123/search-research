#!/usr/bin/env python3
"""
Fix inconsistent authentication error handling
"""

import re


def fix_authentication_error_handling():
    """Fix inconsistent authentication error handling with centralized error management"""

    file_path = "C:/_Python/_Projects/ai_studio/src/ai_studio/youtube_cookies.py"

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Add centralized error handling function if it doesn't exist
    centralized_error_handler = """    def _handle_auth_error(self, error: Exception, context: str = "authentication") -> str:
        \"\"\"Centralized error handling for authentication failures with user-friendly messages.\"\"\"
        error_msg = str(error).lower()
        error_type = type(error).__name__

        # Categorize errors and provide actionable guidance
        if "blocked" in error_msg or "verification failed" in error_msg or "unusual traffic" in error_msg:
            user_message = "Authentication blocked by Google. This may be due to automated detection. Try: 1) Waiting 30+ minutes, 2) Using a different network, 3) Manual authentication in a private browser window."
            log_level = "error"
        elif "timeout" in error_msg or "timed out" in error_msg:
            user_message = "Authentication timed out. Please check your internet connection and try again with a stable connection."
            log_level = "warning"
        elif "element not found" in error_msg or "no such element" in error_msg:
            user_message = "Authentication page elements not found. Google may have changed their login page. Please try again later."
            log_level = "warning"
        elif "network" in error_msg or "connection" in error_msg:
            user_message = "Network connection issue during authentication. Please check your internet connection and try again."
            log_level = "warning"
        elif "permission" in error_msg or "denied" in error_msg:
            user_message = "Browser permission denied. Please ensure browser automation is allowed and try again."
            log_level = "warning"
        elif "geckodriver" in error_msg or "firefox" in error_msg:
            user_message = "Firefox/geckodriver issue detected. Please ensure Firefox is properly installed and compatible."
            log_level = "error"
        else:
            user_message = f"Authentication failed during {context}: {error_msg}. Please try again or use a different authentication method."
            log_level = "error"

        # Log with appropriate level
        if log_level == "error":
            self.logger.error(f"❌ Auth Error ({context}): {error_type} - {error_msg}")
            self.logger.error(f"💡 User Guidance: {user_message}")
        else:
            self.logger.warning(f"⚠️ Auth Issue ({context}): {error_type} - {error_msg}")
            self.logger.warning(f"💡 User Guidance: {user_message}")

        return user_message

"""

    # Check if the function already exists
    if "_handle_auth_error" not in content:
        # Find a good place to insert it (after the __init__ method)
        init_pattern = r"(def __init__\(self.*?\n.*?(?:\n.*?)*?\n\s*pass\n)"

        def add_error_handler(match):
            return match.group(0) + "\n\n" + centralized_error_handler

        new_content = re.sub(init_pattern, add_error_handler, content, flags=re.DOTALL)

        if new_content != content:
            content = new_content
            print("✅ Added centralized error handling function")
        else:
            print("⚠️ Could not find insertion point for error handler")
    else:
        print("ℹ️ Centralized error handler already exists")

    # Now replace inconsistent error handling patterns
    # Pattern 1: Basic exception handling
    patterns_to_fix = [
        (
            r"except Exception as e:\s*self\.logger\.error\(f\"[^\"]*failed[^\"]*:\s*\{e\}\"\)\s*return False",
            "except Exception as e:\n                user_message = self._handle_auth_error(e, 'enhanced_google_sign_in_flow')\n                return False",
        ),
        (
            r"except Exception as e:\s*self\.logger\.error\(f\"[^\"]*failed[^\"]*:\s*\{e\}\"\)",
            "except Exception as e:\n                user_message = self._handle_auth_error(e, 'auth_operation')",
        ),
        (
            r"except Exception as e:\s*self\.logger\.warning\(f\"[^\"]*failed[^\"]*:\s*\{e\}\"\)",
            "except Exception as e:\n                user_message = self._handle_auth_error(e, 'auth_operation')",
        ),
    ]

    for pattern, replacement in patterns_to_fix:
        new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        if new_content != content:
            content = new_content
            print("✅ Fixed inconsistent error handling pattern")
        else:
            print(f"ℹ️ Pattern not found or already fixed: {pattern[:30]}...")

    # Enhance the enhanced_google_sign_in_flow method with better error handling
    enhanced_flow_pattern = r"""    def enhanced_google_sign_in_flow\(self, driver\) -> bool:
        \"\"\"Enhanced Google sign-in with multiple fallback strategies\"\"\"
        self\.logger\.info\(\"Starting enhanced Google sign-in flow\.\.\.\"\)

        # Try interactive authentication first \(solves timing issues\)
        self\.logger\.info\(\"🎯 Attempting interactive authentication workflow\.\.\.\"\)
        if self\._interactive_authentication_strategy\(driver\):
            self\.logger\.info\(\"✅ Interactive authentication strategy succeeded\")
            return True

        # Fallback to automated strategies
        strategies = \[
"""

    enhanced_flow_replacement = """    def enhanced_google_sign_in_flow(self, driver) -> bool:
        \"\"\"Enhanced Google sign-in with multiple fallback strategies\"\"\"
        self.logger.info(\"Starting enhanced Google sign-in flow...\")

        try:
            # Try interactive authentication first (solves timing issues)
            self.logger.info(\"🎯 Attempting interactive authentication workflow...\")
            if self._interactive_authentication_strategy(driver):
                self.logger.info(\"✅ Interactive authentication strategy succeeded\")
                return True

            # Fallback to automated strategies
            strategies = ["""

    # Replace the method start with better error handling
    new_content = re.sub(
        enhanced_flow_pattern, enhanced_flow_replacement, content, flags=re.DOTALL
    )

    if new_content != content:
        content = new_content
        print("✅ Enhanced error handling in authentication flow")
    else:
        print("ℹ️ Authentication flow pattern not found")

    # Add error handling wrapper for the final exception in the method
    final_exception_pattern = r"except Exception as e:\s*self\.logger\.error\(f\"Strategy '\{name\}' failed: \{str\(e\)\}\"\)"
    final_exception_replacement = """except Exception as e:
                user_message = self._handle_auth_error(e, f'strategy_{name}')
                self.logger.error(f\"Strategy '{name}' failed with context: {user_message}\")"""

    new_content = re.sub(final_exception_pattern, final_exception_replacement, content)
    if new_content != content:
        content = new_content
        print("✅ Enhanced final exception handling in strategies")
    else:
        print("ℹ️ Final exception pattern not found")

    # Write the improved content back to the file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Authentication error handling improvements completed")
    return True


if __name__ == "__main__":
    fix_authentication_error_handling()
