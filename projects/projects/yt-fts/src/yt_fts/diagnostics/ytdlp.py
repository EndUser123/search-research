"""yt-dlp health diagnostics."""


try:
    import yt_dlp
    YTDLP_AVAILABLE = True
except ImportError:
    YTDLP_AVAILABLE = False

from .checker import DiagnosticChecker, DiagnosticResult, Status


class YtdlpChecker(DiagnosticChecker):
    """Check yt-dlp installation and health."""

    def run(self) -> list[DiagnosticResult]:
        """Run all yt-dlp diagnostics."""
        self.results.clear()
        self._check_installation()
        if YTDLP_AVAILABLE:
            self._check_version()
            self._check_basic_test()
        return self.results

    def _check_installation(self) -> None:
        """Check if yt-dlp is installed."""
        if YTDLP_AVAILABLE:
            self.add_result(
                category="yt-dlp Installation",
                status=Status.PASS,
                message="Installed",
                details=[f"Location: {getattr(yt_dlp, '__file__', 'unknown')}"],
            )
        else:
            self.add_result(
                category="yt-dlp Installation",
                status=Status.FAIL,
                message="Not found",
                details=["yt-dlp package is not installed"],
                remediation="Run: pip install yt-dlp",
            )

    def _check_version(self) -> None:
        """Check yt-dlp version."""
        try:
            version = yt_dlp.version.__version__
            self.add_result(
                category="yt-dlp Version",
                status=Status.PASS,
                message=f"v{version}",
                details=[f"Installed: {version}"],
            )
        except Exception as e:
            self.add_result(
                category="yt-dlp Version",
                status=Status.WARN,
                message="Unknown",
                details=[f"Error: {e}"],
            )

    def _check_basic_test(self) -> None:
        """Test basic yt-dlp functionality."""
        try:
            # Try to get YouTube info for a known public video
            # Using a short, popular video for quick testing
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                "skip_download": True,
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Test with a very popular video (Rickroll - stable test target)
                ydl.extract_info("https://www.youtube.com/watch?v=dQw4w9WgXcQ", download=False)

            self.add_result(
                category="yt-dlp Functionality",
                status=Status.PASS,
                message="Working",
                details=["Successfully fetched video info"],
            )
        except Exception as e:
            error_str = str(e)
            if "HTTP Error 429" in error_str or "Too Many Requests" in error_str:
                self.add_result(
                    category="yt-dlp Functionality",
                    status=Status.WARN,
                    message="Rate limited",
                    details=["YouTube API quota exceeded"],
                    remediation="Wait a few minutes before trying again, or use cookies for authentication.",
                )
            else:
                self.add_result(
                    category="yt-dlp Functionality",
                    status=Status.FAIL,
                    message="Failed",
                    details=[str(e)[:100]],
                    remediation="Check yt-dlp is up to date: pip install --upgrade yt-dlp",
                )
