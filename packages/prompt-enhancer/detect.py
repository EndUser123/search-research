import json
import re
from pathlib import Path
from typing import TypedDict


class TriageResult(TypedDict):
    classification: str  # bypass | clear | ambiguous | prohibited | confirm
    reason: str


def load_bypass_prefixes() -> list[str]:
    config_path = Path(__file__).parent / "config" / "bypass_prefixes.json"
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


def triage(prompt: str) -> TriageResult:
    prefixes = load_bypass_prefixes()
    for prefix in prefixes:
        if prompt.startswith(prefix):
            return TriageResult(classification="bypass", reason=f"bypass prefix matched: {prefix}")

    # Slash command invocations are always bypass — skill has its own triage
    # Covers: /skill args, /skill:sub args, /skill (bare no-args), /skill:sub (bare)
    if re.match(r"^/[a-z][a-z0-9_-]*(?::[a-z][a-z0-9_-]+)?(\s+|--?\s|$)", prompt.strip()):
        return TriageResult(classification="bypass", reason="skill invocation")

    if _is_destructive_ambiguous(prompt):
        return TriageResult(classification="confirm", reason="confirm: high-impact verb with ambiguous scope")

    if _is_clear(prompt):
        return TriageResult(classification="clear", reason="clear: verb + object + scope present")

    if _is_prohibited(prompt):
        return TriageResult(classification="prohibited", reason="prohibited: destructive without scope")

    return TriageResult(classification="ambiguous", reason="ambiguous: missing referent or underspecified")


def _is_clear(prompt: str) -> bool:
    prompt_lower = prompt.lower().strip()
    if _is_informational_trivial(prompt_lower):
        return True
    if _is_conversational_clear(prompt_lower):
        return True
    verb_match = re.search(
        r"\b(refactor|fix|add|delete|remove|open|create|update|change|implement|review|test|run|build|compile|debug|check|analyze|explain)\b",
        prompt_lower,
    )
    if not verb_match:
        return False
    verb_pos = verb_match.start()
    rest = prompt_lower[verb_pos + len(verb_match.group()):].strip()
    if not rest:
        return False
    extension_pattern = re.compile(r"\.[a-zA-Z0-9]{1,10}\b")
    has_extension = bool(extension_pattern.search(prompt))
    has_path_sep = bool(re.search(r"[/\\]", prompt))
    has_the = bool(re.search(r"\bthe\b", prompt_lower))
    if has_extension or has_path_sep:
        return True
    if has_the and len(rest) > 3:
        return True
    if len(rest.split()) <= 3 and bool(re.search(r"\bto\b|\bfor\b|\bin\b", rest)):
        return True
    return False


def _is_conversational_clear(prompt_lower: str) -> bool:
    """Recognize conversational prompts whose clarity comes from prior-turn context.

    These are NOT continuations (which the hook routes to ambiguous→resolved);
    they are prompts that are inherently clear given the conversation, e.g.:
      - "your proposal results in the best software development projects?"
      - "what about fix 3?"
      - "does that include the cleanup step?"

    Trigger conditions (any of):
      - Short question (< 20 words) ending in '?' that opens with a
        question-style or context-referencing word.
      - Conversational "what about X" / "how about X" / "let's X" pattern.
    """
    if prompt_lower.endswith("?") and len(prompt_lower.split()) < 20:
        question_openers = (
            "your", "it", "that", "this", "the", "those", "these",
            "does", "do", "is", "are", "can", "will", "would", "should",
            "what about", "how about", "what if", "why not",
        )
        for opener in question_openers:
            if prompt_lower.startswith(opener + " ") or prompt_lower == opener + "?":
                return True

    conversational_starts = (
        "let's ", "let us ", "let me see ", "tell me more",
        "go with ", "stick with ",
    )
    if any(prompt_lower.startswith(s) for s in conversational_starts):
        return True

    return False


def _is_informational_trivial(prompt_lower: str) -> bool:
    informational_starts = (
        "what", "how", "why", "when", "where", "explain",
        "describe", "list", "show", "tell me",
    )
    if any(prompt_lower.startswith(s) for s in informational_starts) and len(prompt_lower.split()) < 20:
        return True
    trivial = {"hi", "hello", "help", "?", "help me", "what's up"}
    if prompt_lower.strip() in trivial:
        return True
    global_requests = {"summarize this branch", "list open prs", "list open", "show git status"}
    return any(prompt_lower.strip() == r for r in global_requests)


def _is_prohibited(prompt: str) -> bool:
    prompt_lower = prompt.lower()
    destructive_verbs = {"rm -rf", "delete everything", "drop table", "truncate", "format disk", "del /f /s"}
    high_impact_no_scope = (
        "delete the database",
        "drop all tables",
        "remove all files",
        "destroy the repo",
        "wipe the disk",
    )
    for phrase in high_impact_no_scope:
        if phrase in prompt_lower:
            return True
    return any(prompt_lower.startswith(d) for d in destructive_verbs)


def _is_destructive_ambiguous(prompt: str) -> bool:
    prompt_lower = prompt.lower()
    high_impact_verbs = {"delete", "drop", "remove", "destroy", "wipe", "truncate", "format"}
    for verb in high_impact_verbs:
        if prompt_lower.startswith(verb) and "the" in prompt_lower and len(prompt.split()) < 10:
            return True
    return False
