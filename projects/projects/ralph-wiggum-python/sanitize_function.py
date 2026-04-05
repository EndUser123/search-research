#!/usr/bin/env python3
"""
Temporary file - sanitize_prompt function to be inserted into setup-ralph-loop.py
"""

import re


def sanitize_prompt(prompt: str) -> str:
    """
    Robust prompt sanitization - detects and collapses numbered lists.

    Strategy: Detect PATTERNS, not individual lines.
    A numbered list has 2+ lines matching "N. text" pattern in sequence.

    This avoids false positives on valid input like:
    - "Fix issue 1 and 2" (single line, no pattern)
    - "See step 1 for details" (single line, no pattern)
    - "1.2.3 release notes" (dots without space after number)

    Only collapses when it's clearly a list being pasted.
    """
    lines = prompt.split('\n')

    # Count lines that look like numbered list items
    # Pattern: "1. ", "2. ", "10. ", "1) ", etc.
    numbered_pattern = re.compile(r'^\s*\d+[\.\)]\s+\S')

    numbered_lines = []
    for i, line in enumerate(lines):
        if numbered_pattern.match(line):
            numbered_lines.append((i, line))

    # Only sanitize if we have 2+ numbered lines (a pattern, not coincidence)
    if len(numbered_lines) < 2:
        return prompt

    # Check if numbered lines are in sequence (1, 2, 3... or 1, 3, 5...)
    # Extract numbers from numbered lines
    numbers = []
    for idx, line in numbered_lines:
        match = re.match(r'^\s*(\d+)[\.\)]', line)
        if match:
            numbers.append(int(match.group(1)))

    # If numbers are sequential-ish (difference of 1-3 between consecutive),
    # it's almost certainly a list
    if len(numbers) >= 2:
        is_sequential = True
        for i in range(1, len(numbers)):
            diff = numbers[i] - numbers[i-1]
            if diff > 3 or diff < 1:
                is_sequential = False
                break

        if is_sequential:
            # Collapse the list: remove "N. " prefixes from each line
            cleaned = []
            for i, line in enumerate(lines):
                match = numbered_pattern.match(line)
                if match:
                    # Remove the "N. " prefix
                    cleaned_line = numbered_pattern.sub('', line).strip()
                    cleaned.append(cleaned_line)
                elif line.strip():
                    # Keep non-numbered lines as-is
                    cleaned.append(line.strip())

            result = ' '.join(cleaned)
            # If result is different, we sanitized something
            if result != prompt.replace('\n', ' '):
                print(f'📝 Sanitized numbered list input ({len(numbered_lines)} items collapsed)', file=sys.stderr)
                return result

    return prompt
