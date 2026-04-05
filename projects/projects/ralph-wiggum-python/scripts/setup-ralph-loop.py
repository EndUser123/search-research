#!/usr/bin/env python3
"""
Ralph Loop Setup Script v2 - Bash-Free Input Handling

v2.0: Reads input from temp file to avoid bash quoting issues
v8.2: Auto project root detection, coverage threshold enforcement
v8.2: Auto project root detection, coverage threshold enforcement
"""

import sys
import os
import argparse
import uuid
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import subprocess

# v8.2: Auto project root detection, coverage threshold enforcement


def auto_detect_project_root() -> Optional[Path]:
    """Auto-detect project root by searching for common project markers."""
    cwd = Path.cwd()
    project_markers = ["pytest.ini", "pyproject.toml", "setup.py", "setup.cfg", "tox.ini", ".python-version", "poetry.lock", "Pipfile"]
    current = cwd
    while current != current.parent:
        for marker in project_markers:
            if (current / marker).exists():
                return current
        if (current / "tests").exists() and (current / "tests").is_dir():
            return current
        current = current.parent
    try:
        result = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            git_root = Path(result.stdout.strip())
            if (git_root / "tests").exists() or any((git_root / m).exists() for m in project_markers[:3]):
                return git_root
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


# v7.2: Task Decomposition Templates (embedded, no TaskMaster dependency)

DECOMPOSITION_TEMPLATES = {
    "test": [
        {"title": "Identify test coverage gaps", "description": "Analyze code for untested paths"},
        {"title": "Write unit tests", "description": "Create unit tests for core functionality"},
        {"title": "Write integration tests", "description": "Test component interactions"},
        {"title": "Verify test coverage", "description": "Ensure coverage meets threshold"},
    ],
    "refactor": [
        {"title": "Analyze current structure", "description": "Review existing code organization"},
        {"title": "Plan refactoring approach", "description": "Design new structure"},
        {"title": "Implement refactoring", "description": "Apply structural changes"},
        {"title": "Verify functionality", "description": "Run tests to ensure nothing broke"},
    ],
    "feature": [
        {"title": "Define requirements", "description": "Clarify what needs to be built"},
        {"title": "Design interface", "description": "Plan API/UI structure"},
        {"title": "Implement core logic", "description": "Build main functionality"},
        {"title": "Add error handling", "description": "Handle edge cases"},
        {"title": "Test and verify", "description": "Ensure it works correctly"},
    ],
    "fix": [
        {"title": "Reproduce the issue", "description": "Create reproducible test case"},
        {"title": "Identify root cause", "description": "Find where the bug originates"},
        {"title": "Implement fix", "description": "Apply the correction"},
        {"title": "Verify fix works", "description": "Test that issue is resolved"},
    ],
}

# State file location
STATE_DIR = Path(__file__).parent.parent / ".data"
STATE_FILE = STATE_DIR / "ralph-loop.local.md"


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
    import re

    lines = prompt.split('\n')
    # Pattern to detect numbered list items (doesn't consume first letter)
    detect_pattern = re.compile(r'^\s*\d+[\.\)]\s+\S')
    # Pattern to remove only the prefix (number + separator)
    strip_pattern = re.compile(r'^\s*\d+[\.\)]\s+')

    numbered_lines = []
    for i, line in enumerate(lines):
        if detect_pattern.match(line):
            numbered_lines.append((i, line))

    if len(numbered_lines) < 2:
        return prompt

    numbers = []
    for idx, line in numbered_lines:
        match = re.match(r'^\s*(\d+)[\.\)]', line)
        if match:
            numbers.append(int(match.group(1)))

    if len(numbers) >= 2:
        is_sequential = True
        for i in range(1, len(numbers)):
            diff = numbers[i] - numbers[i-1]
            if diff > 3 or diff < 1:
                is_sequential = False
                break

        if is_sequential:
            cleaned = []
            for i, line in enumerate(lines):
                if detect_pattern.match(line):
                    cleaned_line = strip_pattern.sub('', line).strip()
                    cleaned.append(cleaned_line)
                elif line.strip():
                    cleaned.append(line.strip())

            result = ' '.join(cleaned)
            if result != prompt.replace('\n', ' '):
                print(f'📝 Sanitized numbered list input ({len(numbered_lines)} items collapsed)', file=sys.stderr)
                return result

    return prompt


def decompose_task(prompt: str) -> list:
    """Simple task decomposition based on keywords."""
    prompt_lower = prompt.lower()

    # Detect task type
    if any(k in prompt_lower for k in ['test', 'testing', 'coverage']):
        template = DECOMPOSITION_TEMPLATES["test"]
    elif any(k in prompt_lower for k in ['refactor', 'cleanup', 'reorganize']):
        template = DECOMPOSITION_TEMPLATES["refactor"]
    elif any(k in prompt_lower for k in ['fix', 'bug', 'debug', 'broken']):
        template = DECOMPOSITION_TEMPLATES["fix"]
    elif any(k in prompt_lower for k in ['add', 'create', 'build', 'implement', 'feature']):
        template = DECOMPOSITION_TEMPLATES["feature"]
    else:
        return []

    return template


def assess_task(prompt: str) -> dict:
    """Assess task characteristics for auto-detection."""
    prompt_lower = prompt.lower()

    # Test gate auto-detection
    test_keywords = ['add', 'create', 'build', 'implement', 'feature', 'fix', 'bug', 'debug', 'broken']
    docs_keywords = ['doc', 'readme', 'document', 'comment', 'explore', 'investigate', 'research', 'analyze']
    refactor_keywords = ['refactor', 'cleanup', 'reorganize', 'optimize']

    test_required = any(k in prompt_lower for k in test_keywords)
    is_docs = any(k in prompt_lower for k in docs_keywords)
    is_refactor = any(k in prompt_lower for k in refactor_keywords)

    # Override: docs don't need tests
    if is_docs:
        test_required = False

    # Suggested iterations based on task type
    if is_docs:
        iterations = 3
        promise = "DOCS_COMPLETE"
    elif is_refactor:
        iterations = 10
        promise = "REFACTORING_COMPLETE"
    elif 'fix' in prompt_lower or 'bug' in prompt_lower or 'debug' in prompt_lower:
        iterations = 8
        promise = "BUG_FIXED"
    else:
        iterations = 12
        promise = "FEATURE_COMPLETE"

    return {
        "test_required": test_required,
        "suggested_iterations": iterations,
        "completion_promise": promise,
        "warning": None,
        "alternative": None,
    }


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog='ralph-loop',
        description='Ralph Loop - Interactive self-referential development loop',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        'prompt',
        nargs='*',
        help='Initial prompt to start the loop (can be multiple words)'
    )
    parser.add_argument(
        '--input-file',
        type=str,
        help='Read prompt from file (v2: bypasses bash quoting issues)'
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=0,
        metavar='N',
        help='Maximum iterations before auto-stop (default: pattern-based or 5)'
    )
    parser.add_argument(
        '--completion-promise',
        type=str,
        default='null',
        metavar='TEXT',
        help='Promise phrase to signal completion (default: auto-detected)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Skip task-fit assessment'
    )
    parser.add_argument(
        '--decompose',
        action='store_true',
        help='Enable task decomposition into subtasks'
    )
    parser.add_argument(
        '--test-required',
        action='store_true',
        default=None,
        help='Require passing tests before allowing loop exit'
    )
    parser.add_argument(
        '--no-tests',
        action='store_true',
        help='Disable test gate'
    )
    parser.add_argument(
        '--project-root',
        type=str,
        default=None,
        metavar='PATH',
        help='Project root directory for test execution (default: auto-detect)'
    )
    parser.add_argument(
        '--coverage-threshold',
        type=int,
        default=80,
        metavar='N',
        help='Coverage threshold for test gate (default: 80%%, 0 to disable)'
    )
    parser.add_argument(
        '--pre-sanitized',
        type=str,
        default=None,
        help=argparse.SUPPRESS  # Hidden
    )

    return parser.parse_args()


def read_prompt_from_file(filepath: str) -> str:
    """Read prompt from file, handling various encodings."""
    path = Path(filepath)
    if not path.exists():
        return ""

    # Try different encodings
    for encoding in ['utf-8', 'utf-16', 'latin-1']:
        try:
            content = path.read_text(encoding=encoding)
            # Clean up and return
            return content.strip()
        except UnicodeDecodeError:
            continue

    # Fallback: read as bytes and decode with errors='replace'
    return path.read_bytes().decode('utf-8', errors='replace').strip()


def main():
    """Main setup function."""
    args = parse_args()

    # V2: Read from file first (bypasses bash quoting)
    if args.input_file:
        prompt = read_prompt_from_file(args.input_file)
        if not prompt:
            print("❌ Error: Could not read input file", file=sys.stderr)
            sys.exit(1)
        # Sanitize (numbered list collapsing)
        prompt = sanitize_prompt(prompt)
    # Environment variable fallback
    elif os.environ.get('RALPH_PROMPT'):
        prompt = sanitize_prompt(os.environ['RALPH_PROMPT'])
    # Pre-sanitized flag
    elif args.pre_sanitized:
        prompt = args.pre_sanitized
    # Normal argv path
    else:
        prompt = ' '.join(args.prompt).strip()
        prompt = sanitize_prompt(prompt)

    # Validate prompt is non-empty
    if not prompt:
        print("❌ Error: No prompt provided", file=sys.stderr)
        print("", file=sys.stderr)
        print("   Usage: ralph-loop 'your task here'", file=sys.stderr)
        print("   Or:    echo 'your task' | ralph-loop --input-file /dev/stdin", file=sys.stderr)
        sys.exit(1)

    # Smart task assessment
    assessment = assess_task(prompt)

    # Handle poor fit
    if assessment["warning"] and not args.force:
        print(f"RALPH: Poor fit - {assessment['warning']}. Suggestion: {assessment['alternative']}", file=sys.stderr)
        sys.exit(1)

    # Determine test_required
    if args.test_required is not None:
        test_required = True
    elif args.no_tests:
        test_required = False
    else:
        test_required = assessment["test_required"]

    # Auto-detect project root if not specified
    project_root = args.project_root
    detected_root = None
    if not project_root:
        detected_root = auto_detect_project_root()
        if detected_root:
            project_root = str(detected_root)
        else:
            project_root = str(Path.cwd())

    # Apply auto-detected defaults
    if args.max_iterations == 0:
        args.max_iterations = assessment["suggested_iterations"]
    if args.completion_promise == 'null':
        args.completion_promise = assessment["completion_promise"]

    # Task decomposition
    if args.decompose:
        subtasks = decompose_task(prompt)
        if subtasks:
            print(f"📋 Task decomposition: {len(subtasks)} subtasks")
            for i, st in enumerate(subtasks, 1):
                print(f"   {i}. {st['title']}")
            print()

    # Create .claude directory
    (Path.cwd() / ".claude").mkdir(exist_ok=True)

    # Create state directory
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    # Generate unique session ID
    session_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now(timezone.utc).isoformat()

    # Build state file content (YAML frontmatter + prompt)
    # Using YAML format for stop-hook compatibility
    state_content = f"""---
active: true
session_id: {session_id}
iteration: 1
max_iterations: {args.max_iterations}
completion_promise: {args.completion_promise}
started_at: "{timestamp}"
# v8.1: Track iteration start for TDD validation (files changed THIS iteration only)
iteration_started_at: "{timestamp}"
# v8.0: TDD is MANDATORY for Ralph loops
source: ralph
# v7.1: Test verification
test_required: {str(test_required).lower()}
# v8.2: Coverage threshold for test gate
coverage_threshold: {args.coverage_threshold}
project_root: {project_root}
---
{prompt}
"""

    # Write state file
    STATE_FILE.write_text(state_content, encoding='utf-8')

    # Output confirmation
    print(f"🔄 Ralph loop activated in this session!", file=sys.stderr)
    print(file=sys.stderr)
    print(f"Iteration: 1", file=sys.stderr)
    print(f"Max iterations: {args.max_iterations}", file=sys.stderr)
    print(f"Completion promise: {args.completion_promise} (ONLY output when TRUE - do not lie!)", file=sys.stderr)
    print(file=sys.stderr)

    if test_required:
        auto_detected = args.project_root is None and detected_root is not None
        root_note = " (auto-detected)" if auto_detected else ""
        print(f"🧪 Test gate: ENABLED", file=sys.stderr)
        print(f"   Project root: {project_root}{root_note}", file=sys.stderr)
        if args.coverage_threshold > 0:
            print(f"   Coverage threshold: {args.coverage_threshold}%", file=sys.stderr)
        print(file=sys.stderr)
        print(f"  📋 TDD MANDATORY: Write tests BEFORE code. Red-Green-Refactor.", file=sys.stderr)
        print(f"     1. Write failing test", file=sys.stderr)
        print(f"     2. Write minimal code to pass", file=sys.stderr)
        print(f"     3. Run tests to verify", file=sys.stderr)
        print(file=sys.stderr)

    print(file=sys.stderr)
    print("The stop hook is now active. When you try to exit, the SAME PROMPT will be", file=sys.stderr)
    print("fed back to you. You'll see your previous work in files and git history,", file=sys.stderr)
    print("allowing you to iterate and improve.", file=sys.stderr)
    print(file=sys.stderr)

    if test_required:
        print("⚠️  TEST GATE ACTIVE: TDD is MANDATORY for Ralph loops.", file=sys.stderr)
        print("    Loop will NOT exit until tests pass AND completion promise is detected.", file=sys.stderr)
        print("    Use --no-tests ONLY for non-code tasks (docs, analysis, etc.)", file=sys.stderr)
        print(file=sys.stderr)

    print("🔄", file=sys.stderr)
    print(file=sys.stderr)

    # Output the prompt for Claude to work on
    print(prompt)


if __name__ == "__main__":
    main()
