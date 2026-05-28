#!/usr/bin/env python3
"""Start hook: Reasoning mode selector.

Analyzes user queries to determine optimal reasoning mode:
- Sequential: Step-by-step analysis
- Multi-Agent: Multiple perspectives for complex decisions
- Graph: Branching exploration of alternatives
- Two-Stage: Separate reasoning and implementation phases

Registers with UserPromptSubmit router to inject selected mode into context.
"""

from __future__ import annotations


# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


import json
import re
import sys
from typing import Any


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



def analyze_query(query: str | None) -> dict[str, Any]:
    """Analyze query to determine optimal reasoning mode."""
    if not query or not isinstance(query, str):
        return {"mode": "sequential", "confidence": 0, "reasoning_required": False}

    complexity_indicators = {
        'multi_agent': [
            r'\balternatives\b', r'\bcompare\b', r'\bvs\b', r'\bversus\b',
            r'should we use', r'trade-off', r'better option', r'decision between',
            r'\bor\b', r'\bprefer\b'
        ],
        'sequential': [
            r'how to', r'step by step', r'\bapproach\b', r'\bexplain\b',
            r'\bunderstand\b', r'\bdescribe\b', r'\boverview\b', r'\bsummary\b'
        ],
        'graph': [
            r'\bexplore\b', r'\bbranches\b', r'multiple paths', r'what if',
            r'\bscenarios\b', r'consider options', r'alternatives for', r'\bbranch\b'
        ],
        'two_stage': [
            r'write\s+\w*\s*function', r'create class', r'implement a', r'code to',
            r'develop a', r'build a', r'create\s+\w*\s*function'
        ]
    }

    query_lower = query.lower()
    scores = {}
    for mode, patterns in complexity_indicators.items():
        scores[mode] = sum(1 for p in patterns if re.search(p, query_lower))

    if scores and max(scores.values()) > 0:
        best_mode = max(scores, key=scores.get)
        confidence = scores[best_mode]
    else:
        best_mode = "sequential"
        confidence = 0

    return {
        "mode": best_mode,
        "confidence": confidence,
        "reasoning_required": len(query) > 20 and confidence > 0
    }


def process_prompt(data: dict) -> dict:
    """Process prompt and inject reasoning mode into context."""
    try:
        query = data.get("query", "")
        result = analyze_query(query)

        if result["confidence"] < 2:
            return {}

        mode_name = result["mode"]
        confidence = result["confidence"]
        context = (
            f"Reasoning mode: {mode_name}\n"
            f"Confidence: {confidence}/4\n"
            f"Using {mode_name} reasoning approach for this query.\n\n"
            f"Keep the active reasoning mode internal. Do not surface mode tags in the response."
        )
        return {"additionalContext": context, "tokens": len(context.split())}
    except Exception as e:
        sys.stderr.write(f"[Start_reasoning_mode_selector] Error: {e}\n")
        return {}


if __name__ == "__main__":
    import sys
    test_input = json.loads(sys.stdin.read())
    result = process_prompt(test_input)
    print(json.dumps(_normalize_stdout(result)))
