#!/usr/bin/env python3
"""
Completely remove all browser automation and ONLY use browser extension cookie capture
"""

import re
from pathlib import Path


def fix_browser_extension_only():
    """Remove all browser automation, keep only browser extension approach"""

    file_path = Path("C:/_Python/_Projects/ai_studio/src/ai_studio/youtube_cookies.py")

    # Read the current file
    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    print(
        "🔧 Removing ALL browser automation - keeping ONLY browser extension approach..."
    )

    # Remove the entire ensure_youtube_cookies function that tries Firefox setup
    ensure_function_pattern = r'def ensure_youtube_cookies\(config: Dict\[str, Any\]\) -> bool:.*?(?=\nif __name__ == "__main__":|\nclass|\ndef|\Z)'
    content = re.sub(ensure_function_pattern, "", content, flags=re.DOTALL)

    # Remove any remaining references to selenium, firefox, playwright, browser automation
    automation_patterns = [
        r"def setup_firefox_cookies.*?(?=\n    def|\nclass|\Z)",
        r"def setup_playwright_cookies.*?(?=\n    def|\nclass|\Z)",
        r"from selenium.*?\n",
        r"from webdriver_manager.*?\n",
        r"from playwright.*?\n",
        r"import selenium.*?\n",
        r"import playwright.*?\n",
        r"webdriver\.",
        r"ActionChains\(",
        r"WebDriverWait\(",
        r"EC\.",
        r"By\.",
        r"ElementClickInterceptedException",
        r"ElementNotInteractableException",
    ]

    for pattern in automation_patterns:
        content = re.sub(pattern, "", content, flags=re.DOTALL)

    # Simplify the EnhancedYouTubeCookies class to ONLY do browser extension
    simplified_class = '''
class EnhancedYouTubeCookies:
    def __init__(self, headless: bool = False, debug_mode: bool = True, *args, **kwargs):
        """Initialize for browser extension cookie capture only"""
        self.headless = headless
        self.debug_mode = debug_mode
        self.logger = logger
        self.cookies_file = Path("temp/cookies/youtube_cookies.txt")

    def setup_extension_cookies(self) -> Optional[Path]:
        """
        Browser extension-based cookie extraction (ONLY approach)
        This method checks for cookies saved by the browser extension
        """
        cookies_file = Path("temp/cookies/youtube_cookies.txt")

        if not cookies_file.exists():
            self.logger.info("📋 No extension cookies found")
            return None

        # Test if cookies are valid
        if self.test_cookies_file(cookies_file):
            self.logger.info("✅ Browser extension cookies found and valid")
            self.logger.info(f"🍪 Using cookies from: {cookies_file}")
            return cookies_file
        else:
            self.logger.warning("⚠️ Extension cookies found but invalid")
            return None

    def test_cookies_file(self, cookies_file: Path) -> bool:
        """Test if cookies file is valid"""
        try:
            with open(cookies_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Basic validation
            if 'youtube.com' in content and len(content) > 100:
                return True
            return False
        except Exception as e:
            self.logger.warning(f"Cookie file test failed: {e}")
            return False

def ensure_youtube_cookies(config: Dict[str, Any]) -> bool:
    """Ensure YouTube cookies are available using ONLY browser extension approach"""
    if shutdown_handler.shutdown_event.is_set():
        logger.info('Shutdown event set - skipping cookie setup')
        return False

    cookies_file = Path("temp/cookies/youtube_cookies.txt")
    if cookies_file.exists() and EnhancedYouTubeCookies().test_cookies_file(cookies_file):
        logger.info("✅ Valid browser extension cookies already available")
        return True

    logger.warning("⚠️ No browser extension cookies found - limited to public videos")
    logger.info("💡 Install browser extension to capture YouTube cookies")
    return False

'''

    # Replace the entire class with simplified version
    class_start_pattern = r'class EnhancedYouTubeCookies:.*?(?=def ensure_youtube_cookies|\nif __name__ == "__main__":|\Z)'
    content = re.sub(
        class_start_pattern, simplified_class.strip(), content, flags=re.DOTALL
    )

    # Add the simplified ensure_youtube_cookies function if it was removed
    if "def ensure_youtube_cookies" not in content:
        content += "\n\n" + simplified_class.split("def ensure_youtube_cookies")[1]

    # Write the fixed content
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print("✅ All browser automation removed")
    print("✅ Only browser extension cookie capture remains")
    print("✅ File simplified to browser extension approach only")


if __name__ == "__main__":
    fix_browser_extension_only()
