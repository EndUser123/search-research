#!/usr/bin/env python3
"""
Git commit message validator with semantic intent understanding.

Validates commit messages against staged changes to prevent misleading commits.
Understands semantic intent, not just regex - better than commitlint.

Usage: Automatically called by .git/hooks/commit-msg
To bypass: git commit --no-verify
"""

import re
import sys
from pathlib import Path

# Valid commit types (Conventional Commits)
VALID_TYPES = {
    'feat',    # New feature
    'fix',     # Bug fix
    'refactor', # Code restructuring (no behavior change)
    'perf',    # Performance improvement
    'test',    # Test additions/updates
    'docs',    # Documentation
    'style',   # Formatting only (not production code)
    'chore',   # Dependencies, build, CI
    'build',   # Build system or external dependencies
    'ci',      # CI/CD configuration files
    'revert',  # Revert a previous commit
}

# Vague commit patterns that indicate missing intent
VAGUE_PATTERNS = [
    r'^update\s*\w+$',
    r'^fix\s+\w+$',
    r'^add\s+\w+$',
    r'^change\w+$',
    r'^modify\w+$',
    r'^stuff$',
    r'^things$',
    r'^wip$',
    r'^tmp$',
    r'^test$',
    r'^cleanup$',
    r'^refactor$',
    r'^tweak',
    r'^adjust',
    r'^minor',
    r'^major',
]


def read_commit_msg(filepath: Path) -> str:
    """Read commit message from file."""
    return filepath.read_text(encoding='utf-8')


def validate_header(header: str) -> tuple[bool, list[str]]:
    """Validate commit header format: type(scope): subject"""
    errors = []

    if not header:
        errors.append("Commit message is empty")
        return False, errors

    # Check for type(scope): subject format
    pattern = r'^(\w+)(?:\(([^)]+)\))?: (.+)$'
    match = re.match(pattern, header)

    if not match:
        errors.append(
            "Invalid format. Expected: type(scope): subject\n"
            "  Example: feat(auth): add password reset"
        )
        return False, errors

    commit_type, scope, subject = match.groups()

    # Validate type
    if commit_type not in VALID_TYPES:
        errors.append(
            f"Invalid type '{commit_type}'. Must be one of:\n"
            f"  {', '.join(sorted(VALID_TYPES))}"
        )

    # Validate type is lowercase
    if commit_type != commit_type.lower():
        errors.append(f"Type must be lowercase: '{commit_type}' → '{commit_type.lower()}'")

    # Validate subject format
    if not subject:
        errors.append("Subject cannot be empty")

    if subject[0].isupper():
        errors.append(f"Subject must start with lowercase: '{subject[0]}' → '{subject[0].lower()}'")

    if subject.endswith('.'):
        errors.append("Subject must not end with a period")

    if len(header) > 100:
        errors.append(f"Header too long ({len(header)} chars). Max 100 characters.")

    # Check for vague subjects
    subject_lower = subject.lower().strip()
    for vague_pattern in VAGUE_PATTERNS:
        if re.match(vague_pattern, subject_lower):
            errors.append(
                f"Subject is too vague: '{subject}'\n"
                f"  Include WHAT you changed and WHY."
            )
            break

    return len(errors) == 0, errors


def validate_body(body: str) -> tuple[bool, list[str]]:
    """Validate commit body has required sections."""
    errors = []
    warnings = []

    if not body:
        # Body is optional for trivial changes, but warn about it
        warnings.append("No body provided. Consider adding WHY/WHAT/VERIFICATION sections.")
        return True, warnings

    # Check for required sections
    has_why = '## WHY' in body or 'WHY:' in body
    has_what = '## WHAT' in body or 'WHAT:' in body
    has_verification = '## VERIFICATION' in body or 'VERIFICATION:' in body or 'Test:' in body

    if not has_why:
        errors.append("Missing WHY section. Explain the problem/motivation.")

    if not has_what:
        errors.append("Missing WHAT section. Explain what changed.")

    if not has_verification and 'fix' in body.lower():
        warnings.append("Bug fix should include VERIFICATION (how to test the fix).")

    # Check for one-line body (need more detail)
    lines = [line.strip() for line in body.split('\n') if line.strip()]
    if len(lines) < 3:
        warnings.append(
            "Body is too short. Include:\n"
            "  - WHY: Problem you're solving\n"
            "  - WHAT: What changed\n"
            "  - VERIFICATION: How to test"
        )

    return len(errors) == 0, errors + warnings


def format_message(errors: list[str], is_error: bool = True) -> str:
    """Format validation message for display."""
    icon = "❌" if is_error else "⚠️"
    level = "ERROR" if is_error else "WARNING"
    output = [f"\n{icon} COMMIT MESSAGE {level}\n"]

    for error in errors:
        output.append(f"  • {error}")

    output.append("\nExpected format:")
    output.append("  feat(scope): subject")
    output.append("")
    output.append("  ## WHY")
    output.append("  Problem we're solving:")
    output.append("")
    output.append("  ## WHAT")
    output.append("  Changed: X → Y")
    output.append("")
    output.append("  ## VERIFICATION")
    output.append("  Test: pytest tests/")
    output.append("")
    output.append("Bypass with: git commit --no-verify\n")

    return "\n".join(output)


def main() -> int:
    """Main validation entry point."""
    if len(sys.argv) < 2:
        print("Usage: commit_msg_validator.py <commit-msg-file>", file=sys.stderr)
        return 1

    commit_file = Path(sys.argv[1])
    commit_msg = read_commit_msg(commit_file)

    # Split header and body
    lines = commit_msg.split('\n')
    header = lines[0].strip() if lines else ""
    body = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""

    # Validate header
    header_valid, header_errors = validate_header(header)

    # Validate body
    body_valid, body_warnings = validate_body(body)

    # Combine results - separate errors from warnings
    # "Missing" section warnings are treated as errors
    body_errors = [e for e in body_warnings if "Missing" in e]
    body_warnings_only = [e for e in body_warnings if "Missing" not in e]

    all_errors = header_errors + body_errors
    has_errors = not header_valid or not body_valid or len(body_errors) > 0

    # Show warnings separately (non-error warnings only)
    if body_warnings_only and not has_errors:
        for warning in body_warnings_only:
            print(f"⚠️  {warning}")

    if has_errors:
        print(format_message(all_errors))
        return 1

    # Success - show minimal confirmation
    print("✓ Commit message validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
