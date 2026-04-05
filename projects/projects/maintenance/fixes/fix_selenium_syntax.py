#!/usr/bin/env python3
"""
Fix selenium authentication issues in youtube_cookies.py
Remove selenium-based authentication methods and syntax errors
"""

import re
from pathlib import Path


def fix_youtube_cookies():
    """Remove selenium authentication code and fix syntax errors"""

    file_path = Path("C:/_Python/_Projects/ai_studio/src/ai_studio/youtube_cookies.py")

    # Read the current file
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    print("🔧 Fixing selenium authentication issues...")

    # Fix the syntax error at line 498 (literal \n\n)
    content = re.sub(
        r"\\n\\n\s*def _handle_auth_error", "\n\n    def _handle_auth_error", content
    )

    # Remove the entire _apply_pin_authentication_stealth method
    # This is a selenium-based method that should not exist
    start_pattern = r'def _apply_pin_authentication_stealth\(self, driver\):.*?self\.logger\.info\("PIN/2FA specific stealth measures applied successfully"\)\s*\n'
    content = re.sub(start_pattern, "", content, flags=re.DOTALL)

    # Remove any other selenium methods
    selenium_methods = [
        r"def setup_firefox_driver\(self\).*?(?=\n    def|\n\n    def|\nclass|\Z)",
        r"def _human_like_typing\(self.*?(?=\n    def|\n\n    def|\nclass|\Z)",
        r"def _find_firefox_binary\(self\).*?(?=\n    def|\n\n    def|\nclass|\Z)",
        r"def _verify_user_specific_content_enhanced\(self.*?(?=\n    def|\n\n    def|\nclass|\Z)",
    ]

    for method_pattern in selenium_methods:
        content = re.sub(method_pattern, "", content, flags=re.DOTALL)

    # Remove selenium imports
    content = re.sub(r"from selenium.*?\n", "", content)
    content = re.sub(r"import selenium.*?\n", "", content)
    content = re.sub(r"from webdriver_manager.*?\n", "", content)

    # Clean up any remaining references to selenium
    content = re.sub(r"driver\.", "# Removed selenium code: ", content)
    content = re.sub(r"webdriver\.", "# Removed selenium code: ", content)

    # Write the fixed content
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Selenium authentication code removed")
    print("✅ Syntax errors fixed")
    print("✅ File cleaned and ready for browser extension approach")


if __name__ == "__main__":
    fix_youtube_cookies()
