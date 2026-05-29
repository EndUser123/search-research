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
# --- plugin bootstrap ---
_l = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in sys.path: sys.path.insert(0, str(_l))
from _bootstrap import bootstrap; _HOOKS_DIR = bootstrap(__file__)
# --- end bootstrap ---
_LOG_DIR = _HOOKS_DIR / "logs" / "diagnostics"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
_logger = _li.getLogger(__name__)
_handler = _li.FileHandler(_LOG_DIR / "hook_stderr.log", encoding="utf-8")
_handler.setFormatter(_li.Formatter("%(asctime)s %(levelname)s %(message)s"))
_logger.addHandler(_handler)
_logger.setLevel(_li.WARNING)



# Han + Hiragana + Katakana + Hangul ranges
CJK_PATTERN = re.compile(r"[一-鿿぀-ヿ가-힯]+")

# Minimum total CJK chars to flag - ignore single stray characters
MIN_CJK_CHARS = 3

# CLIs known to wrap Chinese-trained models (PostToolUse advisory scope)
WATCHED_BASH_TOKENS = ("pi ", " pi.", "opencode ", "ai-pi-", "ai-oc-", "zai-")


def _strip_quoted(text: str) -> str:
    """Remove quoted/structured spans and data-display lines that may contain CJK (not model drift).

    Lines containing a URL are treated as data display (database results, channel lists)
    and stripped entirely - the CJK in channel names should not trigger drift detection.
    """
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"```[\s\S]*$", "", text)
    text = re.sub(r"`[^`\n]+`", "", text)
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


def _posttooluse_text(event: dict) -> str:
    """Extract scannable text from a PostToolUse event, scoped to CLIs likely to drift."""
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {}) or {}
    tool_response = event.get("tool_response", {}) or {}

    # Only scan Bash/Task results - and within Bash, only watched CLIs
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
        # Use the "response" field directly - the Stop/SubagentStop event
        # provides the assistant response text in event["response"].
        # Previous code read transcript_path + JSONL parsing, but transcript_path
        # is not populated in Stop events, causing the detector to silently pass.
        text = event.get("response", "")
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
        f"Respond in English only - no Chinese, Japanese, or Korean under any "
        f"circumstances, even when source content contains them."
    )

    if event_name in ("Stop", "SubagentStop"):
        _logger.warning(msg)
        print(msg, file=sys.stderr)
        try:
            from cc_diagnostic_logger import log_hook_invocation
            log_hook_invocation(
                hook_name="cjk_drift_detector",
                event_type=event_name,
                action="block",
                reason=f"CJK drift: {sample[:60]}",
            )
        except Exception:
            pass
        return 2

    # PostToolUse: advisory only
    _logger.debug(msg)
    try:
        from cc_diagnostic_logger import log_hook_invocation
        log_hook_invocation(
            hook_name="cjk_drift_detector",
            event_type="PostToolUse",
            action="warn",
            reason=f"CJK advisory: {sample[:60]}",
        )
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
