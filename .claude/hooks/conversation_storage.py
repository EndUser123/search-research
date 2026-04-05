#!/usr/bin/env python3
from __future__ import annotations

from __lib import prompt_session_state

# Import auto-logging decorator
from __lib.hook_base import hook_main

"""
Conversation Storage Hook - Knowledge Capture from Q&A
======================================================

Captures valuable knowledge exchanged during conversations:
- Q&A that solves problems
- Research results and findings
- Code explanations and patterns
- Debugging/investigation outcomes

HOOK TYPE: Stop (captures assistant response and pairs with prompt)

Design:
- Runs on Stop hook after assistant completes response
- Extracts user prompt + assistant response
- Accumulates high-value knowledge exchanges
- Stores to CKS when threshold reached
- Separate from file edit tracking (auto_cks_storage.py)

Author: CSF v2.4
Version: 1.1.0
"""

import json
import os
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

hooks_dir = Path(__file__).resolve().parent

# Add paths
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "__csf" / "src" / "lib"))

try:
    from core_utils.agent_factory.cks_integration import store_to_cks
    CKS_INTEGRATION_AVAILABLE = True
except ImportError:
    CKS_INTEGRATION_AVAILABLE = False
    store_to_cks = None

# Session state file
STATE_FILE = hooks_dir / "session_data/conversation_state.json"

# Value indicators - patterns that suggest valuable knowledge
VALUE_INDICATORS = [
    r"how\s+to\s+",  # "how to" explanations
    r"why\s+",  # "why" questions
    r"fix\s+\w+",  # fixing something
    r"debug",  # debugging
    r"solution",  # solutions
    r"implement",  # implementations
    r"pattern",  # patterns
    r"best\s+practice",  # best practices
    r"error",  # error explanations
    r"mistake",  # lessons learned
    r"^here's?",  # "here is/are" (providing something)
    r"the\s+problem\s+is",  # problem analysis
    r"the\s+issue\s+is",  # issue analysis
]

# Low-value patterns to skip
SKIP_PATTERNS = [
    r"^ok$",  # simple acknowledgments
    r"^sure",  # agreements
    r"^done\.?$",  # simple completion
    r"^\s*$",  # empty
    r"^let me know",  # closings
]

# Minimum response length to consider (characters)
MIN_RESPONSE_LENGTH = 150

# Maximum Q&A pairs to accumulate before auto-store
MAX_ACCUMULATED = 3


def has_value(text: str) -> bool:
    """Check if text contains valuable knowledge."""
    if not text or len(text) < MIN_RESPONSE_LENGTH:
        return False

    # Check skip patterns first
    first_line = text.strip().split('\n')[0]
    for pattern in SKIP_PATTERNS:
        if re.match(pattern, first_line.strip(), re.IGNORECASE):
            # But if the full text is long enough, it might still be valuable
            if len(text) < MIN_RESPONSE_LENGTH * 2:
                return False

    # Check for value indicators
    text_lower = text.lower()
    for indicator in VALUE_INDICATORS:
        if re.search(indicator, text_lower):
            return True

    # Check for code blocks (indicate technical content)
    if "```" in text:
        return True

    # Check for structured explanations (bullets, numbered lists, headers)
    if re.search(r'^[\s]*[-*#]+\s+', text, re.MULTILINE):
        return True

    # Check for problem-solution patterns
    if re.search(r'(issue|problem|error|bug|fix)', text_lower):
        return True

    return False


def load_state() -> dict:
    """Load conversation state."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except:
            pass

    return {
        "session_start": time.time(),
        "last_update": time.time(),
        "accumulated_qa": [],
        "total_count": 0,
        "seen_hashes": [],
    }


def save_state(state: dict) -> None:
    """Save conversation state."""
    state["last_update"] = time.time()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def get_pending_prompt_record(input_data: dict | None = None) -> tuple[str | None, int | None]:
    """Get latest user prompt + version scoped to current session+terminal."""
    try:
        record, status = prompt_session_state.read_latest_prompt_record(input_data or {})
        if status == "ok":
            prompt = str(record.get("prompt", "")).strip()
            updated_at = int(record.get("updated_at", 0))
            if prompt:
                return prompt, updated_at
    except Exception:
        pass
    return None, None


def clear_pending_prompt(input_data: dict | None = None, expected_updated_at: int | None = None) -> None:
    """Clear latest prompt scoped to current session+terminal.

    If expected_updated_at is provided, clear only when state version matches.
    """
    try:
        prompt_session_state.clear_latest_prompt(
            input_data or {},
            expected_updated_at=expected_updated_at,
        )
    except Exception:
        pass


def accumulate_qa(question: str, answer: str, state: dict) -> None:
    """Accumulate Q&A pair for later storage."""
    # Skip if not valuable
    if not has_value(answer):
        return

    # Create hash to detect duplicates
    qa_hash = hash(frozenset({
        "q": question[:100],
        "a": answer[:200]
    }.items()))

    # Skip duplicates
    seen_hashes = set(state.get("seen_hashes", []))
    if qa_hash in seen_hashes:
        return

    # Add to accumulated
    qa_item = {
        "question": question[:150] + "..." if len(question) > 150 else question,
        "answer": answer[:600] + "..." if len(answer) > 600 else answer,
        "timestamp": datetime.now(UTC).isoformat(),
        "answer_length": len(answer),
        "hash": qa_hash,
    }

    state["accumulated_qa"].append(qa_item)
    state["total_count"] += 1
    seen_hashes.add(qa_hash)
    state["seen_hashes"] = list(seen_hashes)
    save_state(state)


def should_store_to_cks(state: dict) -> bool:
    """Determine if accumulated Q&A is significant enough to store."""
    return len(state["accumulated_qa"]) >= MAX_ACCUMULATED


def format_question_from_state(state: dict) -> str:
    """Format a question/title from accumulated Q&A."""
    qa_items = state["accumulated_qa"]

    if not qa_items:
        return "Claude Code conversation"

    # Use first question as title
    first_q = qa_items[0]["question"]
    count = len(qa_items)

    if count == 1:
        return first_q
    else:
        return f"{first_q} (+{count - 1} related topics)"


def format_answer_from_state(state: dict) -> str:
    """Format answer/content from accumulated Q&A."""
    qa_items = state["accumulated_qa"]

    if not qa_items:
        return "No Q&A accumulated."

    lines = [
        "# Conversation Knowledge Summary",
        "",
        f"Total Q&A pairs: {len(qa_items)}",
        "",
        "## Questions & Answers",
        ""
    ]

    for i, item in enumerate(qa_items, 1):
        lines.append(f"### Q{i}: {item['question']}")
        lines.append(f"**Answer** ({item['answer_length']} chars):")
        lines.append(item['answer'])
        lines.append("")

    return "\n".join(lines)


def store_accumulated_qa(state: dict) -> bool:
    """Store accumulated Q&A to CKS."""
    if not should_store_to_cks(state):
        return False

    question = format_question_from_state(state)
    answer = format_answer_from_state(state)

    metadata = {
        "source": "conversation_auto",
        "qa_count": len(state["accumulated_qa"]),
        "session_duration_seconds": time.time() - state["session_start"],
        "stored_at": datetime.now(UTC).isoformat(),
    }

    success = store_to_cks(question, answer, metadata=metadata)

    if success:
        # Reset state after successful storage
        state["accumulated_qa"] = []
        state["total_count"] = 0
        # Keep seen_hashes to avoid re-storing same content
        state["session_start"] = time.time()
        save_state(state)

    return success


@hook_main
def main():
    """Main hook entry point."""
    input_data = json.load(sys.stdin)

    result = {
        "passed": True,
        "action": "pass",
        "metadata": {
            "hook": "conversation_storage",
            "version": "1.1.0",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    }

    # Get the response content
    # Stop hook receives: {current_response_content, ...}
    response_content = input_data.get("current_response_content", "")

    if response_content:
        # Get the pending user prompt
        question, prompt_version = get_pending_prompt_record(input_data)

        if question:
            # Accumulate Q&A
            state = load_state()
            accumulate_qa(question, response_content, state)

            result["metadata"]["qa_extracted"] = True
            result["metadata"]["question_preview"] = question[:50]
            result["metadata"]["answer_length"] = len(response_content)
            result["metadata"]["accumulated_count"] = len(state["accumulated_qa"])

            # Check if should store
            if should_store_to_cks(state):
                success = store_accumulated_qa(state)
                result["metadata"]["auto_stored"] = success

                # Silent success - only log errors
                DEBUG = os.environ.get("CONVERSATION_STORAGE_DEBUG", "0") == "1"
                if success and DEBUG:
                    count = len(state["accumulated_qa"])  # This will be 0 after reset
                    log_hook_event(
                        "conversation_storage",
                        "info",
                        f"Auto-stored {count} Q&A to CKS"
                    )

            # Clear pending prompt after processing
            clear_pending_prompt(input_data, expected_updated_at=prompt_version)
        else:
            result["metadata"]["note"] = "No pending prompt found"
    else:
        result["metadata"]["note"] = "No response content"

    print(json.dumps(result, default=str))
    sys.exit(0)

if __name__ == "__main__":
    main()
