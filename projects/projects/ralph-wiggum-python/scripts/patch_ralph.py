# Patch script for setup-ralph-loop.py

# Read original file
with open('scripts/setup-ralph-loop.py', 'r') as f:
    content = f.read()

# 1. Add subprocess import after Optional import
content = content.replace(
    'from typing import Optional\n\n# v7.2:',
    'from typing import Optional\nimport subprocess\n\n# v8.2: Auto project root detection, coverage threshold enforcement\n\n\ndef auto_detect_project_root() -> Optional[Path]:\n    """Auto-detect project root by searching for common project markers."""\n    cwd = Path.cwd()\n    project_markers = ["pytest.ini", "pyproject.toml", "setup.py", "setup.cfg", "tox.ini", ".python-version", "poetry.lock", "Pipfile"]\n    current = cwd\n    while current != current.parent:\n        for marker in project_markers:\n            if (current / marker).exists():\n                return current\n        if (current / "tests").exists() and (current / "tests").is_dir():\n            return current\n        current = current.parent\n    try:\n        result = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=5)\n        if result.returncode == 0:\n            git_root = Path(result.stdout.strip())\n            if (git_root / "tests").exists() or any((git_root / m).exists() for m in project_markers[:3]):\n                return git_root\n    except (subprocess.TimeoutExpired, FileNotFoundError):\n        pass\n    return None\n\n\n# v7.2:'
)

# 2. Update docstring
content = content.replace(
    'v2.0: Reads input from temp file to avoid bash quoting issues',
    'v2.0: Reads input from temp file to avoid bash quoting issues\nv8.2: Auto project root detection, coverage threshold enforcement'
)

# 3. Update project-root help text and add coverage-threshold arg
content = content.replace(
    "metavar='PATH',\n        help='Project root directory for test execution'\n    )\n    parser.add_argument(\n        '--pre-sanitized'",
    "metavar='PATH',\n        help='Project root directory for test execution (default: auto-detect)'\n    )\n    parser.add_argument(\n        '--coverage-threshold',\n        type=int,\n        default=80,\n        metavar='N',\n        help='Coverage threshold for test gate (default: 80%%, 0 to disable)'\n    )\n    parser.add_argument(\n        '--pre-sanitized'"
)

# 4. Add auto-detection logic in main()
old_section = """    # Determine test_required
    if args.test_required is not None:
        test_required = True
    elif args.no_tests:
        test_required = False
    else:
        test_required = assessment["test_required"]

    # Apply auto-detected defaults"""

new_section = """    # Determine test_required
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

    # Apply auto-detected defaults"""

content = content.replace(old_section, new_section)

# 5. Update state_content to include coverage_threshold
old_state = """test_required: {str(test_required).lower()}
project_root: {args.project_root or Path.cwd()}"""

new_state = """test_required: {str(test_required).lower()}
# v8.2: Coverage threshold for test gate
coverage_threshold: {args.coverage_threshold}
project_root: {project_root}"""

content = content.replace(old_state, new_state)

# 6. Update output to show coverage threshold and auto-detection
old_output = """    if test_required:
        print(f"🧪 Test gate: ENABLED", file=sys.stderr)
        print(f"   Project root: {args.project_root or Path.cwd()}", file=sys.stderr)
        print(file=sys.stderr)"""

new_output = """    if test_required:
        auto_detected = args.project_root is None and detected_root is not None
        root_note = " (auto-detected)" if auto_detected else ""
        print(f"🧪 Test gate: ENABLED", file=sys.stderr)
        print(f"   Project root: {project_root}{root_note}", file=sys.stderr)
        if args.coverage_threshold > 0:
            print(f"   Coverage threshold: {args.coverage_threshold}%", file=sys.stderr)
        print(file=sys.stderr)"""

content = content.replace(old_output, new_output)

# Write updated file
with open('scripts/setup-ralph-loop.py', 'w') as f:
    f.write(content)

print('File updated successfully')
