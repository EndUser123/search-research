"""Cookie file validation diagnostics."""

from __future__ import annotations

from pathlib import Path

from .checker import DiagnosticChecker, DiagnosticResult, Status


class CookieChecker(DiagnosticChecker):
    """Check cookie file for yt-dlp authentication."""

    DEFAULT_COOKIE_PATHS = [
        Path.home() / ".config" / "yt-dlp" / "cookies.txt",
        Path("cookies.txt"),
    ]

    def run(self) -> list[DiagnosticResult]:
        """Run all cookie diagnostics."""
        self.results.clear()
        self._check_cookie_file()
        return self.results

    def _check_cookie_file(self) -> None:
        """Check if cookie file exists and is valid."""
        found_paths = []
        for cookie_path in self.DEFAULT_COOKIE_PATHS:
            if cookie_path.exists():
                found_paths.append(cookie_path)

        if found_paths:
            # Check file size and content
            details = [f"Found: {p}" for p in found_paths]
            for p in found_paths:
                size = p.stat().st_size
                details.append(f"Size: {size} bytes")

                # Check if file has content
                if size > 0:
                    with open(p) as f:
                        content = f.read(100)  # Read first 100 chars
                        if "Netscape" in content or "Cookie" in content:
                            details.append("Format: Valid Netscape format")
                        else:
                            details.append("Format: Unknown (may not work)")
                else:
                    details.append("Warning: File is empty")

            self.add_result(
                category="Cookie File",
                status=Status.PASS,
                message="Found",
                details=details,
            )
        else:
            self.add_result(
                category="Cookie File",
                status=Status.WARN,
                message="Not found",
                details=[
                    "No cookie file found at expected locations:",
                    f"  • {self.DEFAULT_COOKIE_PATHS[0]}",
                    "  • cookies.txt (current directory)",
                ],
                remediation=(
                    "To download age-restricted/members-only videos:\n"
                    "  1. Export cookies from browser (Get cookies.txt LOCALLY extension)\n"
                    "  2. Run: yt-dlp --cookies cookies.txt https://www.youtube.com/watch?v=XXX\n"
                    "  3. Move cookies.txt to ~/.config/yt-dlp/cookies.txt"
                ),
            )
