#!/usr/bin/env python3
"""
PreToolUse Secret Scanner Hook

Detects potential secrets in Write/Edit operations and git commands.
Blocks operations that may be committing secrets to version control.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path


def read_stdin():
    """Read JSON input from stdin."""
    try:
        input_data = sys.stdin.read().strip()
        if not input_data:
            return {}
        return json.loads(input_data)
    except json.JSONDecodeError:
        return {}


def get_secret_patterns():
    """Return regex patterns for detecting secrets."""
    return {
        'openai_key': r'sk-[a-zA-Z0-9]{32,}',
        'aws_access_key': r'AKIA[0-9A-Z]{16}',
        'github_token': r'ghp_[a-zA-Z0-9]{36}',
        'slack_token': r'xoxb-[0-9]{10,}-[0-9]{10,}-[a-zA-Z0-9]{24}',
        'firebase_key': r'AAAA[a-zA-Z0-9_-]{28,}',  # Firebase keys start with AAAA (at least 28 more chars)
        'private_key_header': r'-----BEGIN RSA PRIVATE KEY-----',
        'api_key': r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']?[a-zA-Z0-9_\-]{20,}["\']?',
        'secret': r'(?i)(secret[_-]?key|password|pass|secret)\s*[=:]\s*["\']?[a-zA-Z0-9_\-]{12,}["\']?',
        'token': r'(?i)(token|auth[_-]?token)\s*[=:]\s*["\']?[a-zA-Z0-9_\-]{20,}["\']?',
        'bearer_token': r'Bearer\s+[a-zA-Z0-9_\-]{20,}',
    }


def get_whitelist_patterns():
    """Return regex patterns that should be whitelisted (not flagged)."""
    return [
        r'\b(example|test|dummy|fake|mock|sample|placeholder)\s*[-=]?\s*["\']?[a-zA-Z0-9_\-]+["\']?',
        r'\byour-?[a-z]+-?here\b',
        r'REPLACE_ME',
        r'TODO_[A-Z_]+',
        r'your-[a-z-]+-key',
        r'[a-z]+_key_here',
    ]


def is_test_file(file_path):
    """Check if file is a test file."""
    path_str = str(file_path)
    return any(pattern in path_str for pattern in ['test_', '/tests/', '\\tests\\', '/test_', '\\test_'])


def get_non_scanned_extensions():
    """Return file extensions that should not be scanned."""
    return {
        '.log', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg',
        '.pdf', '.zip', '.tar', '.gz', '.exe', '.dll', '.so', '.dylib',
        '.bin', '.dat', '.db', '.sqlite', '.mdb'
    }


def should_scan_file(file_path):
    """Check if file should be scanned for secrets."""
    if not file_path:
        return True

    path = Path(file_path)
    ext = path.suffix.lower()

    return ext not in get_non_scanned_extensions()


def is_whitelisted(content):
    """Check if content contains whitelisted patterns."""
    for pattern in get_whitelist_patterns():
        if re.search(pattern, content, re.IGNORECASE):
            return True
    return False


def remove_code_blocks(content):
    """Remove content within code blocks (```...```) for scanning."""
    # Remove code blocks
    content = re.sub(r'```[\s\S]*?```', '', content)
    return content


def remove_comments(content, file_path):
    """Remove comments from content before scanning."""
    if not file_path:
        return content

    ext = Path(file_path).suffix.lower()

    # Remove Python/JSON/YAML/shell comments
    if ext in {'.py', '.yaml', '.yml', '.sh', '.json', '.conf', '.env'}:
        # Remove single-line comments starting with #
        lines = []
        for line in content.split('\n'):
            # Preserve actual code but skip full-line comments
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            # Remove inline comments
            if '#' in line and not ('"' + '#' in line or "'" + '#' in line):
                line = line.split('#')[0]
            lines.append(line)
        content = '\n'.join(lines)

    # Remove JS/TS/C-style comments for those extensions
    if ext in {'.js', '.ts', '.jsx', '.tsx', '.c', '.cpp', '.h', '.hpp', '.java', '.go', '.rs'}:
        # Remove single-line comments //
        content = re.sub(r'//.*', '', content)
        # Remove multi-line comments /* */
        content = re.sub(r'/\*[\s\S]*?\*/', '', content)
    elif ext in {'.md', '.rst', '.txt'}:
        # Remove markdown/code block comments
        lines = []
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped.startswith('<!--') or stripped.startswith('#'):
                continue
            lines.append(line)
        content = '\n'.join(lines)

    return content


def scan_for_secrets(content, file_path=None):
    """Scan content for secret patterns. Returns list of detected secrets."""
    detected = []

    if not content:
        return detected

    # Check if file is whitelisted by type
    if is_test_file(file_path):
        return detected

    # Remove code blocks and comments before scanning
    scan_content = remove_code_blocks(content)
    scan_content = remove_comments(scan_content, file_path)

    # Check for whitelist patterns first
    if is_whitelisted(scan_content):
        return detected

    # Check for whitelist patterns in original content too
    if is_whitelisted(content):
        return detected

    # Scan for secrets
    patterns = get_secret_patterns()
    for secret_type, pattern in patterns.items():
        matches = re.finditer(pattern, scan_content, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            detected.append({
                'type': secret_type,
                'match': match.group(0)[:50],  # Truncate for output
                'line': scan_content[:match.start()].count('\n') + 1
            })

    return detected


def run_subprocess(command, **kwargs):
    """Helper to run subprocess that can be mocked for testing."""
    # Add CREATE_NO_WINDOW on Windows to prevent console flash
    if 'creationflags' not in kwargs:
        kwargs['creationflags'] = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
    return subprocess.run(command, **kwargs)


def scan_git_staged_files():
    """Scan git staged files for secrets."""
    detected = []

    # Check for test mode (for unit testing)
    test_mode = os.environ.get('SECRET_SCANNER_TEST_MODE')

    try:
        # Get list of staged files
        if test_mode == 'mock_git_diff':
            # Test mode: use mock data from environment
            staged_files_str = os.environ.get('SECRET_SCANNER_STAGED_FILES', '')
            staged_files = staged_files_str.split('\n') if staged_files_str else []
        else:
            result = run_subprocess(
                ['git', 'diff', '--cached', '--name-only'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                return detected

            staged_files = result.stdout.strip().split('\n')

        staged_files = [f for f in staged_files if f]  # Remove empty strings

        for file_path in staged_files:
            if not should_scan_file(file_path):
                continue

            if is_test_file(file_path):
                continue

            # Get staged content
            if test_mode == 'mock_git_diff':
                # Test mode: use mock content from environment
                mock_content_key = f'SECRET_SCANNER_FILE_CONTENT_{file_path}'
                file_content = os.environ.get(mock_content_key, '')
            else:
                content_result = run_subprocess(
                    ['git', 'show', f':{file_path}'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if content_result.returncode != 0:
                    continue

                file_content = content_result.stdout

            secrets = scan_for_secrets(file_content, file_path)
            for secret in secrets:
                secret['file'] = file_path
                detected.append(secret)

    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        pass

    return detected


def main():
    """Main entry point for the hook."""
    input_data = read_stdin()

    tool_name = input_data.get('tool_name', '')
    tool_input = input_data.get('tool_input', {})

    # Only scan Write, Edit, and Bash tools
    if tool_name not in {'Write', 'Edit', 'Bash'}:
        print(json.dumps({}))
        return 0

    detected = []

    if tool_name == 'Write':
        file_path = tool_input.get('file_path', '')
        content = tool_input.get('content', '')

        if should_scan_file(file_path):
            detected = scan_for_secrets(content, file_path)

    elif tool_name == 'Edit':
        file_path = tool_input.get('file_path', '')
        new_string = tool_input.get('new_string', '')

        if should_scan_file(file_path):
            detected = scan_for_secrets(new_string, file_path)

    elif tool_name == 'Bash':
        command = tool_input.get('command', '')

        # Check if this is a git command that should be scanned
        if command.strip().startswith('git '):
            git_cmd = command.strip()[4:].strip()
            if git_cmd.startswith('add ') or git_cmd.startswith('commit '):
                detected = scan_git_staged_files()

    # Build output
    if detected:
        secret_types = list(set(s['type'] for s in detected))
        output = {
            "hookSpecificOutput": {
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    "SECRET DETECTED: Potential secret(s) found in your operation. "
                    f"Detected types: {', '.join(secret_types)}. "
                    "Please remove sensitive data before committing. "
                    "Use environment variables or secret management systems instead. "
                    "If this is a false positive, add appropriate whitelist patterns."
                ),
                "hookEventName": "secret_scanner"
            }
        }
    else:
        output = {}

    print(json.dumps(output))
    return 0


if __name__ == '__main__':
    sys.exit(main())
