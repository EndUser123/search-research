"""
Python Syntax Error Fixer - Provides suggestions for common syntax errors
"""

import ast
import re
from typing import List, Tuple


def analyze_syntax_error(code: str, error: ast.SyntaxError) -> Tuple[str, List[str]]:
    """Analyze a syntax error and provide fix suggestions.

    Args:
        code: The Python code with the syntax error
        error: The SyntaxError exception

    Returns:
        Tuple of (error_type, list of suggestions)
    """
    error_msg = error.msg.lower()
    line = error.lineno
    col = error.offset

    suggestions = []

    # Get the problematic line
    lines = code.split('\n')
    if 0 < line <= len(lines):
        problem_line = lines[line - 1]
    else:
        problem_line = ""

    # Category 1: Missing comma or operator
    if "perhaps you forgot a comma" in error_msg or "invalid syntax" in error_msg:
        # Check for common missing comma patterns (dictionary items, function args)
        if re.search(r'[\w"\']\s*[\w"\']', problem_line):
            suggestions.append("Add missing comma between items or arguments")

        # Check for missing colon in compound statements
        if any(keyword in problem_line for keyword in ["if", "else", "elif", "for", "while", "def", "class", "try", "except", "finally", "with"]):
            if not problem_line.rstrip().endswith(':'):
                suggestions.append("Add colon (:) at end of line for compound statement")
                suggestions.append(f"Example: {problem_line.strip()}:")

        # Check for f-string issues
        if 'f"' in problem_line or "f'" in problem_line:
            if '{{' not in problem_line:
                suggestions.append("In f-strings, use {{ for literal braces: f\"value: {{variable}}\"")
            suggestions.append("Check for unmatched quotes or braces in f-string")

    # Category 2: Unmatched parentheses
    if "unmatched" in error_msg or "parenthesis" in error_msg:
        open_parens = problem_line.count('(')
        close_parens = problem_line.count(')')
        if open_parens > close_parens:
            suggestions.append(f"Add {open_parens - close_parens} closing parenthesis(es) ')'")
        elif close_parens > open_parens:
            suggestions.append(f"Remove {close_parens - open_parens} opening parenthesis(es) '('")

        open_brackets = problem_line.count('[')
        close_brackets = problem_line.count(']')
        if open_brackets > close_brackets:
            suggestions.append(f"Add {open_brackets - close_brackets} closing bracket(s) ']'")
        elif close_brackets > open_brackets:
            suggestions.append(f"Remove {close_brackets - open_brackets} opening bracket(s) '['")

        open_braces = problem_line.count('{')
        close_braces = problem_line.count('}')
        if open_braces > close_braces:
            suggestions.append(f"Add {open_braces - close_braces} closing brace(s) '}}'")
        elif close_braces > open_braces:
            suggestions.append(f"Remove {close_braces - open_braces} opening brace(s) '{{'")

    # Category 3: Indentation errors
    if "indentation" in error_msg or "unexpected indent" in error_msg:
        suggestions.append("Check indentation - use consistent spaces (typically 4 per level)")
        if line > 1:
            prev_line = lines[line - 2] if line <= len(lines) else ""
            curr_indent = len(problem_line) - len(problem_line.lstrip())
            prev_indent = len(prev_line) - len(prev_line.lstrip())
            if curr_indent > prev_indent + 4:
                suggestions.append(f"Reduce indentation to match previous level (previous: {prev_indent} spaces, current: {curr_indent} spaces)")

    # Category 4: String quotes
    if "unterminated string" in error_msg or "eol while scanning string literal" in error_msg:
        single_quotes = problem_line.count("'")
        double_quotes = problem_line.count('"')
        if single_quotes % 2 == 1:
            suggestions.append("Close the single-quoted string with a matching '")
        if double_quotes % 2 == 1:
            suggestions.append("Close the double-quoted string with a matching \"")

        # Check for triple-quoted strings
        if "'''" in problem_line or '"""' in problem_line:
            suggestions.append("Close the triple-quoted string (triple quotes) ")

    # Category 5: Invalid characters
    if "unterminated" in error_msg and "line" in error_msg:
        suggestions.append("Check for incomplete multi-line statements (use \\ for line continuation)")

    # Category 6: F-string errors
    if "f-string" in error_msg:
        suggestions.append("Check f-string format:")
        suggestions.append("  - Use double quotes inside f-strings: f\"value: {var}\"")
        suggestions.append("  - Escape nested braces: f\"{{literal}} {variable}\"")

    # Category 7: Colon missing
    if "expected an indented block" in error_msg:
        suggestions.append("Add a colon (:) at the end of the previous line for compound statements")
        if line > 1:
            prev_line = lines[line - 2] if line <= len(lines) else ""
            if any(keyword in prev_line for keyword in ["if", "else", "elif", "for", "while", "def", "class", "try", "except", "finally", "with"]):
                if not prev_line.rstrip().endswith(':'):
                    suggestions.append(f"Previous line should end with ':': {prev_line.strip()}:")

    # Category 8: Assignment issues
    if "can't assign" in error_msg or "assignment" in error_msg:
        suggestions.append("Check for:")
        suggestions.append("  - Using = instead of == in comparisons")
        suggestions.append("  - Assignment to expression (e.g., 'x + 1 = 5' should be 'x + 1 == 5')")
        suggestions.append("  - Multiple assignment targets (e.g., 'a, b = c' should be 'a, b = c, d')")

    # If no specific suggestions, provide general guidance
    if not suggestions:
        suggestions.append("Review the line for:")
        suggestions.append("  - Unmatched brackets, braces, or quotes")
        suggestions.append("  - Missing operators (+, -, *, /, =)")
        suggestions.append("  - Incorrect Python syntax (check Python docs)")

    return error_msg, suggestions


def format_suggestions(filename: str, error: ast.SyntaxError) -> str:
    """Format syntax error suggestions for display.

    Args:
        filename: The file name
        error: The SyntaxError exception

    Returns:
        Formatted error message with suggestions
    """
    error_type, suggestions = analyze_syntax_error("", error)

    output = [f"{filename}:{error.lineno} - {error.msg}"]

    if error.text:
        output.append(f"  → {error.text.strip()}")

    output.append("\n💡 Suggestions to fix:")

    for i, suggestion in enumerate(suggestions, 1):
        if suggestion.startswith("Suggested fix:"):
            output.append(f"\n  {i}. {suggestion}")
        else:
            output.append(f"  {i}. {suggestion}")

    return "\n".join(output)
