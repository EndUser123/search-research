"""CJK drift detector.

Blocks or warns when the assistant or a third-party CLI emits Chinese, Japanese,
or Korean text. Needed because the underlying models in this stack are
Chinese-trained and drift to CJK despite English-only instructions in CLAUDE.md.

Registered for three events (see settings.json):
- Stop:          block + force regenerate (main agent drift)
- SubagentStop:  block + force regenerate (subagent drift)
- PostToolUse:   advisory warning only (third-party CLI output cannot be regenerated cheaply)

False-positive control: fenced code blocks and inline backtick spans are stripped
before detection so the hook does not fire on legitimate quoted Chinese content
(file paths, source strings, log lines).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import logging as _li
_HOOKS_DIR = Path(__file__).resolve().parent
_LOG_DIR = _HOOKS_DIR / "logs" / "diagnostics"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_logger = _li.getLogger(__name__)
_handler = _li.FileHandler(_LOG_DIR / "hook_stderr.log", encoding="utf-8")
_handler.setFormatter(_li.Formatter("%(asctime)s %(levelname)s %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(_li.WARNING)



# Han + Hiragana + Katakana + Hangul ranges
CJK_PATTERN = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]+")

# Minimum total CJK chars to flag — ignore single stray characters
MIN_CJK_CHARS = 3

# CLIs known to wrap Chinese-trained models (PostToolUse advisory scope)
WATCHED_BASH_TOKENS = ("pi ", " pi.", "opencode ", "ai-pi-", "ai-oc-", "zai-")


def _strip_quoted(text: str) -> str:
    """Remove quoted/structured spans and data-display lines that may contain CJK (not model drift).

    Lines containing a URL are treated as data display (database results, channel lists)
    and stripped entirely — the CJK in channel names should not trigger drift detection.
    """
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`\n]+`", "", text)
    # Markdown links: strip entire line if it contains a URL (data display, not my language)
    text = re.sub(r"^.*\([^\)]*https?://[^\)]*\).*$", "", text, flags=re.MULTILINE)
    return text


def detect_cjk(text: str) -> str | None:
    """Return a short sample of detected CJK if present in non-quoted text, else None."""
    if not text:
        return None
    cleaned = _strip_quoted(text)
    matches = CJK_PATTERN.findall(cleaned)
    total_chars = sum(len(m) for m in matches)
    if total_chars < MIN_CJK_CHARS:
        return None
    return matches[0][:30]


def _last_assistant_text(transcript_path: str) -> str:
    """Extract concatenated text from the most recent assistant message in a JSONL transcript."""
    if not transcript_path:
        return ""
    path = Path(transcript_path)
    if not path.exists():
        return ""
    last = ""
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if evt.get("type") != "assistant":
                    continue
                msg = evt.get("message", {})
                content = msg.get("content", [])
                if isinstance(content, str):
                    last = content
                elif isinstance(content, list):
                    parts = [
                        b.get("text", "")
                        for b in content
                        if isinstance(b, dict) and b.get("type") == "text"
                    ]
                    if parts:
                        last = "\n".join(parts)
    except OSError:
        return ""
    return last


def _posttooluse_text(event: dict) -> str:
    """Extract scannable text from a PostToolUse event, scoped to CLIs likely to drift."""
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {}) or {}
    tool_response = event.get("tool_response", {}) or {}

    # Only scan Bash/Task results — and within Bash, only watched CLIs
    if tool_name == "Bash":
        cmd = str(tool_input.get("command", ""))
        if not any(tok in cmd for tok in WATCHED_BASH_TOKENS):
            return ""
    elif tool_name != "Task":
        return ""

    if isinstance(tool_response, dict):
        return json.dumps(tool_response, ensure_ascii=False)
    return str(tool_response)


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0

    event_name = event.get("hook_event_name", "")

    if event_name in ("Stop", "SubagentStop"):
        text = _last_assistant_text(event.get("transcript_path", ""))
    elif event_name == "PostToolUse":
        text = _posttooluse_text(event)
    else:
        return 0

    sample = detect_cjk(text)
    if not sample:
        return 0

    msg = (
        f"[CJK drift detected] Output contains non-English characters "
        f'(sample: "{sample}"). The underlying model drifted from English. '
        f"Respond in English only — no Chinese, Japanese, or Korean under any "
        f"circumstances, even when source content contains them."
    )

    if event_name in ("Stop", "SubagentStop"):
        # Block + force regenerate
            _logger.debug(msg)
            return 2

    # PostToolUse: advisory only
            _logger.debug(msg)
            return 0


if __name__ == "__main__":
    sys.exit(main())
