#!/usr/bin/env python3
"""
Stage 2.5: Integration Check

Verifies that implemented features are actually wired into the system.
Catches "implemented but not integrated" gaps where functions exist but aren't called.

Usage:
    python stage2_5_integration.py <target> --plan <plan-file.md>
    python stage2_5_integration.py <target> --use-chat-history

Exit codes:
    0 - Integration check passed
    1 - Integration check failed or missing requirements
"""

import argparse
import ast
import json
import re
import sys
from pathlib import Path


def extract_requirements_from_plan(plan_path: Path) -> list[dict]:
    """Extract requirements from a plan file.

    Parses markdown plan files and extracts requirements from sections like:
    - "## 7. Requirements"
    - "## Requirements"
    - "## 7. Implementation Plan"

    Returns list of dicts with keys: id, description, function (if specified)
    """
    content = plan_path.read_text()
    requirements = []

    # Pattern to match requirement items
    # Matches: - [ ] REQ-001: Implement function foo()
    # Or: - REQ-001: Implement function foo()
    req_pattern = re.compile(
        r'^-\s*\[[\sXx]?\]\s*(REQ-\d+|[\w-]+):\s*(.+?)(?:\s+(?:function|class)\s+(\w+))?\s*$',
        re.MULTILINE
    )

    matches = req_pattern.findall(content)

    for match in matches:
        req_id, description, function = match
        req = {
            "id": req_id,
            "description": description.strip()
        }
        if function:
            req["function"] = function
        requirements.append(req)

    return requirements


def extract_requirements_from_cli_args(req_args: list[str]) -> list[dict]:
    """Extract requirements from --req CLI arguments.

    Each --req argument specifies a requirement in the format:
        "description" or "id:description" or "id:description:function_name"

    Examples:
        --req "function run_block exists"
        --req "REQ-001:function run_block exists:run_block"

    Returns list of dicts with keys: id, description, function (if specified)
    """
    requirements = []
    for i, req_str in enumerate(req_args, 1):
        parts = req_str.split(":", 2)
        if len(parts) == 3:
            req = {"id": parts[0].strip(), "description": parts[1].strip(), "function": parts[2].strip()}
        elif len(parts) == 2:
            req = {"id": parts[0].strip(), "description": parts[1].strip()}
        else:
            req = {"id": f"REQ-{i:03d}", "description": parts[0].strip()}
        requirements.append(req)
    return requirements


def check_code_exists(target: Path, requirements: list[dict]) -> dict:
    """Check if required code exists in the target.

    For each requirement with a 'function' key, verifies that the function
    or class is defined in the target file or directory.

    Returns dict with 'items' list containing 'name' and 'exists' status.
    """
    items = []

    for req in requirements:
        function_name = req.get("function")
        if not function_name:
            continue

        if target.is_file():
            exists = _check_function_in_file(target, function_name)
        else:
            # Search in Python files within directory
            exists = False
            for py_file in target.rglob("*.py"):
                if _check_function_in_file(py_file, function_name):
                    exists = True
                    break

        items.append({
            "name": function_name,
            "exists": exists
        })

    return {"items": items}


def _check_function_in_file(file_path: Path, function_name: str) -> bool:
    """Check if a function or class is defined in a file."""
    try:
        content = file_path.read_text()
        tree = ast.parse(content, filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                if node.name == function_name:
                    return True
        return False
    except (SyntaxError, OSError):
        return False


def check_call_sites(target: Path, requirements: list[dict]) -> dict:
    """Check if functions are called from integration points.

    For each requirement with a 'function' key, searches for call sites
    in the target directory (excluding test files).

    Returns dict with 'items' list containing 'name', 'has_call_sites',
    and 'call_sites' list.
    """
    items = []

    for req in requirements:
        function_name = req.get("function")
        if not function_name:
            continue

        call_sites = []

        if target.is_file():
            search_root = target.parent
        else:
            search_root = target

        # Search for function calls in non-test Python files
        for py_file in search_root.rglob("*.py"):
            if "test" in py_file.name:
                continue

            try:
                content = py_file.read_text()
                if _find_call_sites_in_content(content, function_name):
                    rel_path = py_file.relative_to(search_root)
                    call_sites.append(str(rel_path))
            except OSError:
                continue

        items.append({
            "name": function_name,
            "has_call_sites": len(call_sites) > 0,
            "call_sites": call_sites
        })

    return {"items": items}


def _find_call_sites_in_content(content: str, function_name: str) -> bool:
    """Find if a function is called in the given content."""
    # Parse as AST to find actual function calls
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == function_name:
                    return True
                if isinstance(node.func, ast.Attribute) and node.func.attr == function_name:
                    return True
    except SyntaxError:
        # Fall back to regex for files with syntax errors
        pattern = rf'\b{re.escape(function_name)}\s*\('
        return bool(re.search(pattern, content))

    return False


def check_integration_tests(target: Path, requirements: list[dict]) -> dict:
    """Check if integration tests exist and pass.

    Runs pytest with -k "integration" filter on the target directory.

    Returns dict with 'passed', 'failed', 'total' counts and 'success' status.
    """
    import subprocess

    try:
        # Prevent blue console flash on Windows
        creation_flags = 0x08000000 if sys.platform == 'win32' else 0
        result = subprocess.run(
            ["pytest", "-k", "integration", str(target), "-v", "--tb=no"],
            capture_output=True,
            text=True,
            timeout=30,
            creationflags=creation_flags
        )

        # Parse pytest output to count tests
        output = result.stdout + result.stderr
        passed = len(re.findall(r'PASSED', output))
        failed = len(re.findall(r'FAILED', output))
        total = passed + failed

        return {
            "passed": passed,
            "failed": failed,
            "total": total,
            "success": failed == 0 and total > 0
        }
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return {
            "passed": 0,
            "failed": 0,
            "total": 0,
            "success": False
        }


def verify_requirements_satisfied(requirements: list[dict], implementation_check: dict, call_sites: dict) -> dict:
    """Verify all requirements from plan/chat are satisfied.

    A requirement is satisfied if:
    - The code exists (implementation_check shows exists=True)
    - The function has call sites (call_sites shows has_call_sites=True)

    Returns dict with 'requirements' list (each with 'id', 'satisfied'),
    'all_satisfied' boolean, and 'status' (INTEGRATED/NOT_INTEGRATED/PARTIAL).
    """
    req_results = []

    impl_items = {item["name"]: item for item in implementation_check.get("items", [])}
    call_items = {item["name"]: item for item in call_sites.get("items", [])}

    for req in requirements:
        function_name = req.get("function")
        if not function_name:
            # Requirements without function names are considered satisfied
            req_results.append({
                "id": req["id"],
                "description": req["description"],
                "satisfied": True
            })
            continue

        impl = impl_items.get(function_name, {"exists": False})
        calls = call_items.get(function_name, {"has_call_sites": False})

        satisfied = impl.get("exists", False) and calls.get("has_call_sites", False)

        req_results.append({
            "id": req["id"],
            "description": req["description"],
            "satisfied": satisfied
        })

    all_satisfied = all(r["satisfied"] for r in req_results)

    if all_satisfied:
        status = "INTEGRATED"
    elif any(r["satisfied"] for r in req_results):
        status = "PARTIAL"
    else:
        status = "NOT_INTEGRATED"

    return {
        "requirements": req_results,
        "all_satisfied": all_satisfied,
        "status": status
    }


def find_plan_file(target: Path) -> Path | None:
    """Find plan file using discovery priority order.

    Priority:
    1. Same directory (primary) - plan-*.md next to target
    2. Centralized plans/ (secondary) - .claude/plans/*.md
    3. README traversal (tertiary) - follow README.md links
    4. FAIL - No requirements source found

    Returns Path to plan file or None if not found.
    """
    if target.is_file():
        target_dir = target.parent
        target_name = target.stem
    else:
        target_dir = target
        target_name = target.name

    # Priority 1: Same directory - look for plan-<target>.md or plan-*.md
    for plan_file in target_dir.glob("plan-*.md"):
        # Prefer exact match
        if plan_file.stem == f"plan-{target_name}":
            return plan_file

    # Return any plan file found
    plan_files = list(target_dir.glob("plan-*.md"))
    if plan_files:
        return plan_files[0]

    # Priority 2: Centralized plans/
    claude_dir = Path.cwd() / ".claude"
    plans_dir = claude_dir / "plans"

    if plans_dir.exists():
        for plan_file in plans_dir.glob("*.md"):
            if target_name in plan_file.stem or plan_file.stem == target_name:
                return plan_file

    # Priority 3: README traversal (simplified - check if README mentions plan)
    readme_file = target_dir / "README.md"
    if readme_file.exists():
        content = readme_file.read_text()
        # Look for plan file references
        plan_match = re.search(r'plan[-\w]*\.md', content)
        if plan_match:
            potential_plan = target_dir / plan_match.group(0)
            if potential_plan.exists():
                return potential_plan

    # Priority 4: FAIL
    return None


def main():
    parser = argparse.ArgumentParser(
        description="Stage 2.5: Integration Check - Verify implemented features are wired into system"
    )
    parser.add_argument("target", help="Target file or directory to validate")
    parser.add_argument("--plan", help="Path to plan file with requirements")
    parser.add_argument("--req", action="append", default=[],
                       help="Requirement spec: 'description' or 'id:description' or 'id:description:function'")
    parser.add_argument("--use-chat-history", action="store_true",
                       help="[DEPRECATED] Use --req instead. This flag now exits with helpful message.")

    args = parser.parse_args()
    target = Path(args.target)

    if args.use_chat_history:
        print("NOTE: --use-chat-history is deprecated. Use --req instead.", file=sys.stderr)
        print("  Example: --req 'function run_block exists' --req 'REQ-001:registered in HOOKS:run_block'", file=sys.stderr)
        print("  Or omit flags to auto-discover plan-*.md files.", file=sys.stderr)
        sys.exit(1)

    # Determine requirements source
    requirements = []
    source = None

    if args.req:
        requirements = extract_requirements_from_cli_args(args.req)
        source = "CLI --req arguments"
    elif args.plan:
        plan_path = Path(args.plan)
        if not plan_path.exists():
            print(f"FAIL: Plan file not found: {plan_path}", file=sys.stderr)
            sys.exit(1)
        requirements = extract_requirements_from_plan(plan_path)
        source = str(plan_path)
    else:
        # Auto-discover plan file
        plan_path = find_plan_file(target)
        if plan_path and plan_path.exists():
            requirements = extract_requirements_from_plan(plan_path)
            source = str(plan_path)
        else:
            print("FAIL: No requirements source found.", file=sys.stderr)
            print("       Provide --plan <file.md> or --use-chat-history flag.", file=sys.stderr)
            sys.exit(1)

    if not requirements:
        print(f"FAIL: No requirements found in {source}", file=sys.stderr)
        sys.exit(1)

    # Run integration checks
    implementation_check = check_code_exists(target, requirements)
    call_sites = check_call_sites(target, requirements)
    integration_tests = check_integration_tests(target, requirements)
    requirements_check = verify_requirements_satisfied(requirements, implementation_check, call_sites)

    # Generate report
    print(f"## Integration Check Results")
    print(f"")
    print(f"**Source:** {source}")
    print(f"")
    print(f"**Implementation Check:**")
    for item in implementation_check.get("items", []):
        status = "OK" if item["exists"] else "MISSING"
        print(f"- {status} {item['name']}")

    print(f"")
    print(f"**Integration Check:**")
    for item in call_sites.get("items", []):
        status = "OK" if item["has_call_sites"] else "NOT_INTEGRATED"
        call_info = f"called from: {', '.join(item['call_sites'])}" if item["has_call_sites"] else "NOT INTEGRATED"
        print(f"- {status} {item['name']} - {call_info}")

    print(f"")
    print(f"**Requirements Coverage:**")
    for req in requirements_check.get("requirements", []):
        status = "OK" if req["satisfied"] else "FAIL"
        print(f"- {status} Requirement {req['id']}: {req['description']}")

    # Determine conclusion
    if requirements_check.get("all_satisfied"):
        print(f"")
        print(f"**Conclusion:** INTEGRATED")
        sys.exit(0)
    else:
        print(f"")
        print(f"**Conclusion:** NOT_INTEGRATED")
        sys.exit(1)


if __name__ == "__main__":
    main()
