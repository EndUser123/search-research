#!/usr/bin/env python3
from __future__ import annotations

"""
Variable Naming Confusion Detector (Zero-Config)

Detects potentially confusable variable names WITHOUT requiring YAML contracts.
This is a heuristic-based check that suggests better names during code editing.

Key patterns detected:
- *_count vs *_count (multiple "count" variables)
- *_total vs *_completed (semantic overlap)
- completed_* vs successful_* (partial vs complete)
"""

import re
from typing import Any

# Semantic groups that suggest confusion
SEMANTIC_GROUPS = {
    "status": ["completed", "finished", "done", "processed", "successful",
               "succeeded", "valid", "passed", "failed", "attempted"],
    "total": ["total", "all", "overall", "entire"],
    "count": ["count", "num", "number", "quantity"],
    "result": ["downloads", "items", "entries", "records", "videos", "channels"],
}


type CheckResult = dict[str, Any] | None
type VariablePair = tuple[str, str]
type VariableList = list[tuple[str, str]]


def extract_variable_names(code: str) -> list[str]:
    """Extract variable names from code using regex.

    Looks for:
    - Assignment statements: var_name = ...
    - For loop variables: for var_name in ...
    """
    variables = set()

    # Assignment patterns
    assignment_patterns = [
        r"(\w+)\s*=",  # var_name =
        r"for\s+(\w+)\s+in",  # for var_name in
    ]

    for pattern in assignment_patterns:
        matches = re.findall(pattern, code)
        variables.update(matches)

    # Filter out Python keywords and single letters (in loop context)
    keywords = {
        "if", "else", "elif", "for", "while", "def", "class", "return",
        "import", "from", "as", "try", "except", "finally", "with", "lambda",
    }

    return [v for v in variables
            if v not in keywords
            and not v.isupper()  # Skip constants
            and len(v) > 1]  # Skip single letters


def compute_confusability_score(var1: str, var2: str) -> float:
    """Compute a score indicating how confusable two variables are.

    Returns 0.0 to 1.0, where 1.0 is highly confusable.
    """
    if var1 == var2:
        return 0.0

    score = 0.0

    # Check for common suffix
    var1_parts = var1.split("_")
    var2_parts = var2.split("_")

    # Same suffix (e.g., *_count, *_total)
    if var1_parts[-1] == var2_parts[-1] and len(var1_parts[-1]) > 2:
        score += 0.3

    # Same prefix
    if var1_parts[0] == var2_parts[0] and len(var1_parts[0]) > 2:
        score += 0.3

    # Semantic overlap
    for group in SEMANTIC_GROUPS.values():
        var1_in_group = any(part in group for part in var1_parts)
        var2_in_group = any(part in group for part in var2_parts)
        if var1_in_group and var2_in_group:
            score += 0.4
            break

    # Levenshtein-like similarity
    common_chars = set(var1) & set(var2)
    if len(common_chars) / max(len(set(var1)), len(set(var2))) > 0.6:
        score += 0.1

    return min(score, 1.0)


def detect_confusable_names(code: str, threshold: float = 0.4) -> VariableList:
    """Detect potentially confusable variable names in code.

    Args:
        code: The code content to analyze
        threshold: Minimum score to consider variables confusable (default 0.4)

    Returns:
        List of (var1, var2) tuples representing confusable pairs
    """
    variables = extract_variable_names(code)

    if len(variables) < 2:
        return []

    confusable_pairs = []

    # Compare all pairs
    for i, var1 in enumerate(variables):
        for var2 in variables[i + 1:]:
            score = compute_confusability_score(var1, var2)
            if score >= threshold:
                confusable_pairs.append((var1, var2))

    return confusable_pairs


def suggest_better_names(confusable_pair: VariablePair) -> list[str]:
    """Suggest clearer, more explicit variable names.

    Args:
        confusable_pair: Tuple of (var1, var2) that are confusable

    Returns:
        List of suggested better names
    """
    var1, var2 = confusable_pair

    # Analyze the pair to generate suggestions
    suggestions = []

    var1_parts = var1.split("_")
    var2_parts = var2.split("_")

    # Pattern: completed_count vs successful_downloads
    # Suggest: channels_attempted vs channels_with_videos
    if "completed" in var1_parts or "completed" in var2_parts:
        if "successful" in var1_parts or "successful" in var2_parts:
            # Find the object being counted
            obj = None
            for part in var1_parts + var2_parts:
                if part not in ["completed", "successful", "count", "downloads",
                                 "finished", "done", "processed", "failed",
                                 "succeeded", "valid", "passed"]:
                    obj = part
                    break

            if obj:
                suggestions.append(f"{obj}_attempted")
                suggestions.append(f"{obj}_with_content")
                return suggestions
            else:
                # No clear object - suggest generic names
                suggestions.append("items_attempted")
                suggestions.append("items_with_content")
                return suggestions

    # Pattern: *_count vs *_total
    if "count" in var1_parts or "count" in var2_parts:
        if "total" in var1_parts or "total" in var2_parts:
            prefix = var1_parts[0] if var1_parts[0] == var2_parts[0] else "items"
            suggestions.append(f"{prefix}_total_count")
            suggestions.append(f"{prefix}_current_count")
            return suggestions

    # Generic suggestion: make semantics more explicit
    for i, (var, parts) in enumerate([(var1, var1_parts), (var2, var2_parts)]):
        if any(s in parts for s in ["count", "total", "num"]):
            suggestions.append(f"{parts[0]}_all_items" if i == 0 else f"{parts[0]}_valid_items")
        else:
            suggestions.append(var)

    return suggestions[:2]  # Return exactly 2 suggestions


def check_variable_naming(
    file_path: str,
    old_string: str,
    new_string: str,
    source_content: str | None = None
) -> CheckResult:
    """Check for confusable variable names in new code.

    Public entry point for variable naming checking.

    Args:
        file_path: Path to file being edited
        old_string: Content being replaced
        new_string: New content
        source_content: Full file content (optional)

    Returns:
        Warning dict if confusable names detected, None otherwise
    """
    confusable_pairs = detect_confusable_names(new_string)

    if not confusable_pairs:
        return None

    # Get suggestions for the first pair
    suggestions = suggest_better_names(confusable_pairs[0])

    return {
        "allowed": True,  # Warning only, not a block
        "severity": "warning",
        "category": "confusable_variable_names",
        "reason": (
            f"Found potentially confusable variable names: "
            f"{confusable_pairs[0][0]} and {confusable_pairs[0][1]}. "
            f"These have similar semantics and could be accidentally swapped. "
            f"Consider: {suggestions[0]} vs {suggestions[1]}"
        ),
        "confusable_pairs": confusable_pairs,
        "suggestions": suggestions,
        "file_path": file_path,
    }
