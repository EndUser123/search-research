"""Network connectivity diagnostics."""

from __future__ import annotations

import socket
import time
import urllib.request
from urllib.error import URLError

from .checker import DiagnosticChecker, DiagnosticResult, Status


class NetworkChecker(DiagnosticChecker):
    """Check network connectivity for yt-fts."""

    YOUTUBE_HOSTS = [
        ("www.youtube.com", "YouTube main", "https://www.youtube.com/"),
        ("www.youtube.com", "YouTube API (no auth)", "https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&format=json"),
    ]

    def run(self) -> list[DiagnosticResult]:
        """Run all network diagnostics."""
        self.results.clear()
        self._check_internet()
        self._check_dns()
        self._check_youtube_reachability()
        return self.results

    def _check_internet(self) -> None:
        """Check basic internet connectivity."""
        try:
            # Try to reach a reliable external host
            urllib.request.urlopen("https://www.google.com", timeout=5)
            self.add_result(
                category="Internet Connection",
                status=Status.PASS,
                message="Connected",
                details=["Successfully reached google.com"],
            )
        except Exception as e:
            self.add_result(
                category="Internet Connection",
                status=Status.FAIL,
                message="Not connected",
                details=[f"Error: {e}"],
                remediation="Check your internet connection and try again.",
            )

    def _check_dns(self) -> None:
        """Check DNS resolution."""
        try:
            socket.gethostbyname("www.youtube.com")
            self.add_result(
                category="DNS Resolution",
                status=Status.PASS,
                message="Working",
                details=["Successfully resolved www.youtube.com"],
            )
        except socket.gaierror as e:
            self.add_result(
                category="DNS Resolution",
                status=Status.FAIL,
                message="Failed",
                details=[f"Error: {e}"],
                remediation="Check your DNS settings or try a different DNS server (e.g., 8.8.8.8).",
            )

    def _check_youtube_reachability(self) -> None:
        """Check reachability of YouTube endpoints."""
        details = []
        all_ok = True
        latencies = []

        for host, name, url in self.YOUTUBE_HOSTS:
            try:
                start = time.time()
                urllib.request.urlopen(url, timeout=5)
                latency_ms = int((time.time() - start) * 1000)
                latencies.append(f"{name}: {latency_ms}ms")
                details.append(f"✓ {host} ({name}) - {latency_ms}ms")
            except URLError as e:
                all_ok = False
                details.append(f"✗ {host} ({name}) - {e}")
            except Exception as e:
                all_ok = False
                details.append(f"✗ {host} ({name}) - {type(e).__name__}")

        if all_ok:
            self.add_result(
                category="YouTube Reachability",
                status=Status.PASS,
                message="All endpoints reachable",
                details=details,
            )
        else:
            self.add_result(
                category="YouTube Reachability",
                status=Status.WARN,
                message="Some endpoints failed",
                details=details,
                remediation="Check if YouTube is blocked in your region or network.",
            )
