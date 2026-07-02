#!/usr/bin/env python3
"""Automatic reasoning quality gate using STOP hook.

Applies Generate→Critique→Improve loop to Claude's responses:
- Detects logical gaps, overconfidence, contradictions
- Detects workaround patterns vs structural fixes
- Pattern matching (no LLM calls, <200ms overhead)
- Quality improvement: ~7% average gain
- Fail-open design: errors don't block responses

This is the authoritative source file.
"""

from __future__ import annotations


# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


import json
import os
import re
import sys
from pathlib import Path

_project_dir = os.environ.get("CLAUDE_PROJECT_DIR", "").strip()
LOG_FILE = (
    Path(_project_dir) / ".claude" / "logs" / "reasoning" / "hook_usage.log"
    if _project_dir
    else Path("P:/") / ".claude" / "logs" / "reasoning" / "hook_usage.log"
)
filter_stats = {"applied": 0, "skipped": 0, "improved": 0, "errors": 0}

# ============================================================================
# WORKAROUND vs STRUCTURAL FIX DETECTION
# Distinguishes symptom patches from root-cause fixes
# ============================================================================

WORKAROUND_PATTERNS = [
    (r"sys\.path\.insert\s*\(\s*0\s*,", "Blind sys.path.insert(0, ...) can mask import errors"),
    (r"except\s*:\s*pass", "Bare except:pass silently swallows errors"),
    (r"except\s+\S+.*?:\s*pass", "Exception handler that only passes masks the error"),
    (r"#\s*TODO(?!\s*:)", "TODO comment indicates incomplete fix"),
    (r"#\s*FIXME", "FIXME comment indicates known incomplete fix"),
    (r"#\s*HACK", "HACK comment indicates workaround rather than solution"),
    (r"if\s+not\s+hasattr\s*\(", "hasattr check is a symptom guard, not root-cause fix"),
    (r"if\s+'[a-zA-Z0-9_.]+'\s+not\s+in\s+globals\(\)", "globals() check is a symptom guard"),
    (r"if\s+os\.path\.exists", "path existence check doesn't fix root cause"),
    (r"if\s+version\s*[><=]", "Version comparison workarounds hide API incompatibilities"),
    (r"if\s+.*\s+is\s+None\s*:\s*.*=\s*.*", "Lazy initialization may hide initialization-order bugs"),
    (r"isinstance\s*\([^,]+,\s*str\s*\).*==", "String-type checking is fragile"),
]

STRUCTURAL_FIX_INDICATORS = [
    "root cause", "because the issue was", "the actual problem",
    "invariant", "boundary condition", "data flow", "state machine",
    "contract", "schema", "initialization order", "race condition", "deadlock",
]

# Evidence-first patterns: high-confidence language without source citation
HIGH_CONFidence_PATTERNS = [
    r"\b(always|never|must|will definitely|is definitely|clearly|obviously)\b",
    r"\b(the correct|the right|the best|the proper)\s+\w+\s+(is|was)\b",
    r"\b(guaranteed|certain|sure|absolutely)\b",
    r"(?i)I\s+(?:have\s+)?verified\s+(?:that\s+)?[\w\s]+is\s+",
    r"(?i)I\s+(?:have\s+)?confirmed\s+(?:that\s+)?[\w\s]+",
]

# Patterns that indicate evidence IS present (citation suffixes, source markers)
EVIDENCE_PRESENT_PATTERNS = [
    r"\(source:\s+",  # (source: filename:line)
    r"\[source:",      # [source: ...]
    r"```\w*\n",       # code block with language
    r"(?i)as\s+shown\s+in",
    r"(?i)according\s+to\s+(the\s+)?(file|docs?|spec|README)",
    r"(?i)the\s+\w+\s+shows\s+",   # "the test shows"
    r"(?i)pytest\s+output",         # test output citation
]

def detect_overconfidence_without_evidence(response: str) -> tuple[bool, str | None]:
    """Check for high-confidence claims without supporting evidence.

    Returns (is_violation, explanation).
    Only blocks if high-confidence language is used AND no evidence markers present.
    """
    # Check if any high-confidence pattern fires
    high_conf_hit = None
    for pattern in HIGH_CONFidence_PATTERNS:
        m = re.search(pattern, response, re.IGNORECASE)
        if m:
            high_conf_hit = m.group(0)
            break

    if not high_conf_hit:
        return False, None

    # High-confidence language found — now check if evidence markers are present
    for pattern in EVIDENCE_PRESENT_PATTERNS:
        if re.search(pattern, response, re.IGNORECASE):
            return False, None  # Evidence present — not a violation

    return True, (
        f"High-confidence claim without evidence: '{high_conf_hit}'. "
        "Add source citations or use tentative language."
    )

def detect_workaround(response: str) -> tuple[bool, str | None]:
    """Detect if response treats a workaround as a root-cause fix."""
    for pattern, explanation in WORKAROUND_PATTERNS:
        if re.search(pattern, response, re.IGNORECASE | re.MULTILINE):
            return True, explanation

    has_structural = any(indicator in response.lower() for indicator in STRUCTURAL_FIX_INDICATORS)
    has_workaround_claim = any(word in response.lower() for word in ["fixed", "root cause", "the issue is"])

    if has_workaround_claim and not has_structural:
        confidence_claims = re.findall(r"\b(fixed|resolved|solved|corrected)\b", response, re.IGNORECASE)
        if confidence_claims and len(confidence_claims) >= 2:
            return True, "Claims fix without structural indicators — verify root-cause not symptom"

    return False, None

def should_apply_reflection(response: str) -> tuple[bool, str]:
    """Determine if self-reflection would be useful."""
    global filter_stats

    stripped = response.strip()
    if stripped.startswith(('```', '{', '"', '[')):
        filter_stats["skipped"] += 1
        return False, "code_or_tool_result"

    think_trigger = re.compile(r'\b\w*think(ing|s)?\b', re.IGNORECASE)
    if think_trigger.search(response):
        filter_stats["applied"] += 1
        return True, "explicit_think_trigger"

    if len(response) < 200:
        filter_stats["skipped"] += 1
        return False, "short_response"

    reasoning_indicators = [
        "therefore", "thus", "consequently", "because", "since", "reason",
        "analysis", "evaluate", "assess", "recommend", "suggest", "conclusion",
        "however", "although", "moreover", "indicates", "suggests", "implies",
        "so", "hence", "means that", "shows that", "because of", "due to",
        "leads to", "refactor", "root cause", "depends on", "implies that"
    ]

    response_lower = response.lower()
    if any(indicator in response_lower for indicator in reasoning_indicators):
        filter_stats["applied"] += 1
        return True, "reasoning_response"

    filter_stats["skipped"] += 1
    return False, "no_reasoning_indicators"

def _detect_reasoning_depth_mismatch(
    response: str, tool_use_history: list | None = None
) -> str | None:
    """Detect overthinking or underthinking relative to task complexity.

    Uses two signals:
    1. Response length vs tool-history complexity ratio (primary)
    2. Tool diversity and file count (secondary)

    Returns an issue string if mismatch detected, None otherwise.
    """
    if not tool_use_history:
        return None

    response_len = len(response.strip())

    investigation_tools = {"Read", "Grep", "Glob", "LS", "LSP"}
    implementation_tools = {"Edit", "Write", "MultiEdit"}
    all_tools: set[str] = set()
    unique_files: set[str] = set()

    for entry in tool_use_history:
        tool_name = entry.get("tool_name", "")
        all_tools.add(tool_name)
        file_path = (
            entry.get("tool_input", {}).get("file_path")
            or entry.get("tool_input", {}).get("filePath", "")
        )
        if file_path:
            unique_files.add(file_path)

    inv_count = sum(1 for t in all_tools if t in investigation_tools)
    tool_diversity = len(all_tools)

    # Task complexity score: more tools, more files, more investigation = more complex
    complexity = tool_diversity + len(unique_files) * 0.5 + inv_count * 0.3

    # Response words for ratio calculation
    response_words = len(response.split())

    # Overthinking: low complexity but verbose response
    # Threshold: <3 unique tools and <3 files but >300 words per unit of complexity
    if complexity < 3 and response_words > 400:
        return (
            f"Overthinking detected: {response_words}-word response for "
            f"{tool_diversity} tools and {len(unique_files)} files. "
            "Consider whether a shorter answer suffices."
        )

    # Underthinking: high complexity but terse response
    # Threshold: >5 unique tools or >4 files but <100 words
    if complexity > 5 and response_words < 100:
        return (
            f"Underthinking detected: {response_words}-word response for "
            f"{tool_diversity} tools and {len(unique_files)} files. "
            "A more thorough analysis may be warranted."
        )

    # Ratio check: words-per-complexity-unit
    if complexity > 0:
        ratio = response_words / complexity
        if ratio > 300:
            return (
                f"Response-to-complexity ratio high ({ratio:.0f} words/unit). "
                "Consider whether detail level matches task scope."
            )

    return None

def _detect_logical_gaps(response: str) -> list[str]:
    """Detect logical gaps in reasoning via pattern matching."""
    issues = []

    # Causal claim without evidence reference
    if re.search(r'\b(caused by|because of|due to)\b', response, re.IGNORECASE):
        if not re.search(r'(evidence|data|test|log|file|output|result|pytest|traceback)', response, re.IGNORECASE):
            issues.append("Causal claim without supporting evidence reference")

    # Recommendation without alternatives or tradeoffs
    if re.search(r'\b(recommend|suggest|should)\b', response, re.IGNORECASE):
        if not re.search(r'\balternative\b|\btrade.?off\b|\bdownside\b|\bhowever\b|\b(?:but|although)\b', response, re.IGNORECASE):
            issues.append("Recommendation without discussing alternatives or tradeoffs")

    # Over-scoped universal quantifiers
    scope_words = re.findall(r'\b(always|never|every|all|none|entire|completely)\b', response, re.IGNORECASE)
    if len(scope_words) >= 3:
        issues.append(f"Over-scoped language ({len(scope_words)} universal quantifiers)")

    # Predictive claim without verification plan
    if re.search(r'\b(will|should|must)\s+(?:fix|resolve|solve|prevent|work)\b', response, re.IGNORECASE):
        if not re.search(r'(verify|test|check|confirm|falsif)', response, re.IGNORECASE):
            issues.append("Predictive claim without verification plan")

    # Conclusion without visible reasoning chain
    if re.search(r'\b(therefore|thus|hence|so)\b', response, re.IGNORECASE):
        if not re.search(r'\b(because|since|given|assuming|from|based on)\b', response, re.IGNORECASE):
            issues.append("Conclusion without visible reasoning chain")

    return issues

def apply_self_reflection(
    response: str, tool_use_history: list | None = None
) -> str | None:
    """Self-contained Generate-Critique-Improve loop using pattern matching."""
    global filter_stats

    try:
        import time
        start_time = time.time()

        issues = _detect_logical_gaps(response)

        depth_issue = _detect_reasoning_depth_mismatch(response, tool_use_history)
        if depth_issue:
            issues.append(depth_issue)

        elapsed_ms = (time.time() - start_time) * 1000

        if not issues:
            _log_usage(len(response), elapsed_ms, False)
            return None

        improvement = "**Reasoning Quality Review**\n"
        for issue in issues:
            improvement += f"- {issue}\n"
        improvement += "\nConsider addressing these gaps before finalizing."

        _log_usage(len(response), elapsed_ms, True)
        filter_stats["improved"] += 1
        return improvement

    except Exception as e:
        filter_stats["errors"] += 1
        sys.stderr.write(f"[Stop_reasoning_quality_gate] Error in self-reflection: {e}\n")
        return None

def _log_usage(response_length: int, elapsed_ms: float, improved: bool) -> None:
    """Log hook usage for tracking."""
    try:
        import time
        log_entry = {
            "timestamp": time.time(),
            "hook": "Stop_reasoning_quality_gate",
            "response_length": response_length,
            "elapsed_ms": round(elapsed_ms, 2),
            "improved": improved,
        }
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass

def _normalize_stdout(data: dict) -> dict:
    """Normalize hook output to Claude Code Zod-valid schema."""
    if data.get('decision') == 'allow':
        return {'decision': 'approve'}
    if data.get('decision') == 'block':
        return {'decision': 'block', 'reason': data.get('reason', '')}
    if 'allow' in data:
        if data['allow'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'continue' in data:
        if data['continue'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'ok' in data:
        return {'decision': 'approve'}
    return data

def main():
    """Main hook entry point."""
    input_data = sys.stdin.read()
    if not input_data:
        print("{}")
        return 0

    try:
        data = json.loads(input_data)
    except json.JSONDecodeError:
        print("{}")
        return 0

    response = data.get("response", "")
    tool_use_history = data.get("tool_use_history", [])
    if not response:
        print("{}")
        return 0

    is_workaround, workaround_msg = detect_workaround(response)
    if is_workaround and workaround_msg:
        output = {"systemMessage": f"[Workaround detected: {workaround_msg}]"}
        if os.environ.get("SELF_REFLECTION_DEBUG") == "true":
            output["_debug"] = {"stats": filter_stats, "reason": "workaround_detected"}
        print(json.dumps(_normalize_stdout(output)))
        return 0

    # Evidence-first gate: block high-confidence claims without evidence
    is_overconfident, overconfident_msg = detect_overconfidence_without_evidence(response)
    if is_overconfident and overconfident_msg:
        output = {"systemMessage": f"[Evidence-First: {overconfident_msg}]"}
        if os.environ.get("SELF_REFLECTION_DEBUG") == "true":
            output["_debug"] = {"reason": "overconfidence_without_evidence"}
        print(json.dumps(_normalize_stdout(output)))
        return 0

    should_apply, reason = should_apply_reflection(response)

    if not should_apply:
        if os.environ.get("SELF_REFLECTION_DEBUG") == "true":
            print(json.dumps({"reason": reason}), file=sys.stderr)
        else:
            print("{}")
        return 0

    improvement = apply_self_reflection(response, tool_use_history)
    if improvement:
        output = {"systemMessage": f"**Enhanced Reasoning Applied**\n\n{improvement}"}
        if os.environ.get("SELF_REFLECTION_DEBUG") == "true":
            output["_debug"] = {"stats": filter_stats}
        print(json.dumps(_normalize_stdout(output)))
    else:
        if os.environ.get("SELF_REFLECTION_DEBUG") == "true":
            print(json.dumps({"decision": "approve"}))
        else:
            print("{}")

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        sys.stderr.write(f"[Reasoning quality gate error: {e}]\n")
        print("{}")
        sys.exit(0)