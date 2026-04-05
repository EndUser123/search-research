#!/usr/bin/env python3
"""Shim: re-export from __lib for import compatibility."""

from __lib.terminal_detection import detect_console_host_terminal, detect_terminal_id

__all__ = ["detect_console_host_terminal", "detect_terminal_id"]
