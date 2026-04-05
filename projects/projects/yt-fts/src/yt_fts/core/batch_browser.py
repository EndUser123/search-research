"""
Browser detection for YouTube cookies.

Extracted from batch_download for better modularity.
"""
import os
from dataclasses import dataclass


@dataclass
class BrowserInfo:
    """Information about detected browsers."""
    firefox_available: bool = False
    chrome_available: bool = False
    edge_available: bool = False
    brave_available: bool = False
    opera_available: bool = False
    vivaldi_available: bool = False

    def get_optimal_browser(self) -> str | None:
        """Get the optimal browser for YouTube cookies.

        Returns:
            Browser name or None
        """
        if self.firefox_available:
            return "firefox"
        if self.brave_available:
            return "brave"
        if self.chrome_available:
            return "chrome"
        if self.edge_available:
            return "edge"
        if self.opera_available:
            return "opera"
        if self.vivaldi_available:
            return "vivaldi"
        return None

    def get_available_browsers(self) -> list[str]:
        """Get list of available browsers.

        Returns:
            List of browser names
        """
        browsers = []
        if self.firefox_available:
            browsers.append("firefox")
        if self.brave_available:
            browsers.append("brave")
        if self.chrome_available:
            browsers.append("chrome")
        if self.edge_available:
            browsers.append("edge")
        if self.opera_available:
            browsers.append("opera")
        if self.vivaldi_available:
            browsers.append("vivaldi")
        return browsers


def detect_available_browsers() -> BrowserInfo:
    """Detect which browsers are available on the system.

    Returns:
        BrowserInfo with detected browsers
    """
    info = BrowserInfo()
    home = os.path.expanduser("~")
    appdata = os.path.expandvars("$APPDATA") if os.name == "nt" else None

    # Firefox
    firefox_paths = [
        os.path.join(home, "AppData", "Roaming", "Mozilla", "Firefox", "Profiles"),
        os.path.join(home, ".mozilla", "firefox"),
    ]
    if appdata:
        firefox_paths.insert(0, os.path.join(appdata, "Mozilla", "Firefox", "Profiles"))
    info.firefox_available = any(os.path.exists(p) for p in firefox_paths)

    # Chrome
    chrome_paths = [
        os.path.join(home, "AppData", "Local", "Google", "Chrome", "User Data"),
        os.path.join(home, ".config", "google-chrome", "Default"),
        os.path.join(home, "Library", "Application Support", "Google", "Chrome"),
    ]
    info.chrome_available = any(os.path.exists(p) for p in chrome_paths)

    # Edge
    edge_paths = [
        os.path.join(home, "AppData", "Local", "Microsoft", "Edge", "User Data"),
        os.path.join(home, ".config", "microsoft-edge", "Default"),
        os.path.join(home, "Library", "Application Support", "Microsoft Edge"),
    ]
    info.edge_available = any(os.path.exists(p) for p in edge_paths)

    # Brave
    brave_paths = [
        os.path.join(home, "AppData", "Local", "BraveSoftware", "Brave-Browser", "User Data"),
        os.path.join(home, ".config", "BraveSoftware", "Brave-Browser", "Default"),
        os.path.join(home, "Library", "Application Support", "BraveSoftware", "Brave-Browser"),
    ]
    info.brave_available = any(os.path.exists(p) for p in brave_paths)

    # Opera
    opera_paths = [
        os.path.join(home, "AppData", "Roaming", "Opera Software", "Opera Stable"),
        os.path.join(home, ".config", "opera"),
        os.path.join(home, "Library", "Application Support", "com.operasoftware.Opera"),
    ]
    info.opera_available = any(os.path.exists(p) for p in opera_paths)

    # Vivaldi
    vivaldi_paths = [
        os.path.join(home, "AppData", "Local", "Vivaldi", "User Data"),
        os.path.join(home, ".config", "vivaldi", "Default"),
        os.path.join(home, "Library", "Application Support", "Vivaldi"),
    ]
    info.vivaldi_available = any(os.path.exists(p) for p in vivaldi_paths)

    return info


def suggest_browser_cookies(cookies_from_browser: str) -> str:
    """Suggest a browser for cookies if none specified.

    Args:
        cookies_from_browser: Current browser setting (empty if not set)

    Returns:
        Suggested browser name
    """
    if cookies_from_browser:
        return cookies_from_browser

    info = detect_available_browsers()
    return info.get_optimal_browser() or "firefox"
