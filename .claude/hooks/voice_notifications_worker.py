#!/usr/bin/env python3
"""Detached SAPI voice worker for Claude notifications."""

from __future__ import annotations

import sys

import win32com.client


def _select_voice(voice: object) -> None:
    for token in voice.GetVoices():
        name = str(token.GetDescription())
        if "David" in name and "Desktop" in name:
            voice.Voice = token
            return


def main() -> int:
    message = " ".join(sys.argv[1:]).strip() or "Notification received"
    voice = win32com.client.Dispatch("SAPI.SpVoice")
    voice.Volume = 85
    voice.Rate = -1
    _select_voice(voice)
    voice.Speak(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
