#!/usr/bin/env python3
"""
Restore browser extension authentication approach by removing selenium automation
"""


def restore_browser_extension_auth():
    """Remove selenium automation and restore browser extension cookie capture approach"""

    file_path = "C:/_Python/_Projects/ai_studio/src/ai_studio/youtube_cookies.py"

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    # Remove selenium imports
    selenium_imports_to_remove = [
        "from selenium.webdriver.common.action_chains import ActionChains",
        "from selenium.webdriver.firefox.firefox_profile import FirefoxProfile",
        "from selenium.common.exceptions import ElementClickInterceptedException, ElementNotInteractableException",
        "from selenium import webdriver",
        "from selenium.webdriver.common.by import By",
        "from selenium.webdriver.support.ui import WebDriverWait",
        "from selenium.webdriver.support import expected_conditions as EC",
        "from selenium.webdriver.firefox.options import Options",
        "from selenium.common.exceptions import (NoSuchElementException)",
    ]

    for import_line in selenium_imports_to_remove:
        if import_line in content:
            content = content.replace(import_line + "\n", "")
            print(f"✅ Removed selenium import: {import_line}")

    # Remove selenium-based methods and replace with browser extension approach
    # Replace the entire class definition to focus on browser extension

    old_class_start = "class EnhancedYouTubeCookies:"
    new_class_content = '''class EnhancedYouTubeCookies:
    """
    Browser extension-based YouTube cookies management
    Uses browser extension for cookie extraction instead of selenium automation
    """

    def __init__(self, headless: bool = False, debug_mode: bool = True, *args, **kwargs):
        """Initialize for browser extension cookie capture"""
        self.headless = headless
        self.debug_mode = debug_mode
        self.max_retries = 3
        self.retry_delay = 5
        self.cookies_file = Path("temp/cookies/youtube_cookies.txt")
        self.cookies_file.parent.mkdir(exist_ok=True)

        # Import logger
        from loguru import logger
        self.logger = logger'''

    # Replace class initialization
    content = content.replace(old_class_start, new_class_content)

    # Remove selenium-based methods and replace with extension approach
    methods_to_remove = [
        "setup_firefox_driver",
        "enhanced_google_sign_in_flow",
        "_interactive_authentication_strategy",
        "_handle_auth_error",  # This was added by the bug fix but should be part of the class
    ]

    for method in methods_to_remove:
        # Remove method definitions
        import re

        method_pattern = rf"def {method}\(.*?\n(.*?\n)*?.*?(?=\n    def |\n\nclass |\Z)"
        content = re.sub(method_pattern, "", content, flags=re.DOTALL)
        print(f"✅ Removed selenium method: {method}")

    # Simplify the main cookie setup method to focus on browser extension
    new_setup_method = '''    def setup_youtube_cookies(self, config: dict = None) -> Optional[Path]:
        """
        Setup YouTube cookies using browser extension approach
        Prioritizes browser extension cookies over other methods
        """
        if config is None:
            config = {}

        self.logger.info("🍪 Setting up YouTube cookies using browser extension approach...")

        # CRITICAL FIX: Use browser extension approach first (most reliable)
        extension_cookies = self.setup_extension_cookies()
        if extension_cookies:
            self.logger.info("✅ Using browser extension cookies (preferred method)")
            return extension_cookies

        # Fallback: Check if cookies file already exists
        if self.cookies_file.exists() and self.test_cookies_file(self.cookies_file):
            self.logger.info(f"✅ Using existing cookies file: {self.cookies_file}")
            return self.cookies_file

        # Final fallback: Use Chrome cookie setup (non-automation approach)
        try:
            from .chrome_cookie_setup import ensure_youtube_cookies
            chrome_result = ensure_youtube_cookies(config)
            if chrome_result:
                self.logger.info("✅ Chrome cookie setup successful")
                return chrome_result
        except Exception as e:
            self.logger.warning(f"Chrome cookie setup failed: {e}")

        self.logger.error("❌ All cookie setup methods failed")
        return None

    def setup_extension_cookies(self) -> Optional[Path]:
        """
        Browser extension-based cookie extraction (most reliable approach)
        This method checks for cookies saved by the browser extension
        """
        if not self.cookies_file.exists():
            self.logger.info("📋 No extension cookies found")
            return None

        # Test if cookies are valid
        if self.test_cookies_file(self.cookies_file):
            self.logger.info("✅ Browser extension cookies found and valid")
            self.logger.info(f"🍪 Using cookies from: {self.cookies_file}")
            return self.cookies_file
        else:
            self.logger.warning("⚠️ Extension cookies found but invalid")
            return None

    def test_cookies_file(self, cookies_file: Path) -> bool:
        """Test if cookies file works with yt-dlp"""
        if not cookies_file.exists():
            return False

        try:
            import yt_dlp
            test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Public test video

            ydl_opts = {
                'cookies': str(cookies_file),
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'simulate': True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(test_url, download=False)
                return bool(info)
        except Exception as e:
            self.logger.debug(f"Cookies test failed: {e}")
            return False

    def _handle_auth_error(self, error: Exception, context: str = "authentication") -> str:
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

        return user_message'''

    content = re.sub(
        r"def setup_youtube_cookies.*?(?=\n    def |\n\nclass |\Z)",
        new_setup_method,
        content,
        flags=re.DOTALL,
    )

    # Write the corrected content back to the file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ Restored browser extension authentication approach")
    print("✅ Removed selenium automation code")
    print("✅ Prioritized browser extension cookie capture")
    return True


if __name__ == "__main__":
    restore_browser_extension_auth()
