"""
RCA Validator v2 - Wrapper for Core Validator Engine
"""
import json
import os
import re
import sys
from pathlib import Path

# Add validators directory to path for import
sys.path.insert(0, str(Path(__file__).resolve().parent))

from core_validator import CoreValidator, validate_file


def _extract_response_from_stdin() -> str:
    """Fallback path for hook invocations that don't pass a filepath argument."""
    raw = sys.stdin.read()
    if not raw.strip():
        return ""

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return raw

    response = payload.get("response", "")
    if isinstance(response, str) and response.strip():
        return response

    conversation = payload.get("conversation", []) or payload.get("messages", [])
    if isinstance(conversation, list):
        for msg in reversed(conversation):
            if not isinstance(msg, dict) or msg.get("role") != "assistant":
                continue
            content = msg.get("content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return " ".join(
                    block.get("text", "")
                    for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                )
    return ""


def _detect_strict_flag(text: str) -> bool:
    return bool(
        re.search(r"/(rca|arch)\b[^\n]*--strict\b", text, re.IGNORECASE)
        or re.search(r"\brca\b[^\n]*--strict\b", text, re.IGNORECASE)
        or re.search(r"\b--strict\b", text, re.IGNORECASE)
    )


if __name__ == "__main__":
    response_text = _extract_response_from_stdin()
    strict_from_payload = _detect_strict_flag(response_text)
    mode = os.environ.get("RCA_VALIDATION_MODE", "").strip().lower()
    if not mode:
        mode = "strict" if strict_from_payload else "rca"

    profile = {
        "strict": "rca_strict",
        "rca_strict": "rca_strict",
        "lite": "rca_lite",
        "rca_lite": "rca_lite",
        "rca": "rca",
    }.get(mode, "rca")

    if len(sys.argv) >= 2:
        filepath = sys.argv[1]
        sys.exit(validate_file(filepath, profile))

    validator = CoreValidator()
    passed, results = validator.validate(response_text, profile)
    validator.print_results(results)
    sys.exit(0 if passed else 1)
