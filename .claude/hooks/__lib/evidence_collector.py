# Evidence Collector — extract and accumulate tool-action evidence for phase inference.
from __future__ import annotations

import re
from typing import Any, Optional

from __lib.v2_config import MIN_FILES_FOR_IMPLEMENTATION_PHASE, MIN_TESTS_FOR_VERIFICATION_PHASE


def _extract_paths_from_code(code: str) -> list[str]:
    """Extract file paths from Python code using common patterns."""
    paths = []
    # open(path, ...) or open(path)
    for m in re.finditer(r'open\(\s*["\']([^"\']+)["\']', code):
        paths.append(m.group(1))
    # with open(path, ...) as
    for m in re.finditer(r'with\s+open\(\s*["\']([^"\']+)["\']', code):
        paths.append(m.group(1))
    # Path("...") or Path.home() / "..."
    for m in re.finditer(r'Path\(\s*["\']([^"\']+)["\']', code):
        paths.append(m.group(1))
    # WriteFile / Edit tool inputs
    for m in re.finditer(r'["\']file_path["\']\s*:\s*["\']([^"\']+)["\']', code):
        paths.append(m.group(1))
    return list(dict.fromkeys(paths))  # deduplicate preserve order


def _extract_test_names_from_command(command: str) -> list[str]:
    """Extract test names/paths from pytest or test runner commands."""
    tests = []
    # pytest path/to/test_file.py::TestClass::test_name
    for m in re.finditer(r"([^\s]+\.py::[A-Za-z0-9_]+(?:\[.+?\])?)", command):
        tests.append(m.group(1))
    # bare pytest path/to/test_file.py
    for m in re.finditer(r"pytest\s+([^\s]+\.py)", command):
        tests.append(m.group(1))
    return list(dict.fromkeys(tests))


def _extract_paths_from_git(command: str) -> list[str]:
    """Extract file paths from git commands."""
    paths = []
    # git add path1 path2 ...
    for m in re.finditer(r"git\s+(?:add|commit|rm)\s+(.+?)(?:\s+--|\s*$)", command):
        paths.extend(m.group(1).split())
    return [p for p in paths if not p.startswith("-")]


def collect_from_turn(tool_uses: list[dict]) -> dict:
    """Extract evidence from tool uses in the current turn.

    Args:
        tool_uses: List of tool-use dicts from the hook context.
                   Each dict has keys: name, input (dict), output, etc.

    Returns:
        Evidence dict with keys:
            files_modified, tests_run, verification_commands_executed,
            code_generated, design_artifacts, git_commits
    """
    evidence = {
        "files_modified": [],
        "tests_run": [],
        "verification_commands_executed": [],
        "code_generated": False,
        "design_artifacts": [],
        "git_commits": 0,
    }

    for tool in tool_uses:
        name = tool.get("name", "")
        inp = tool.get("input", {})
        command = ""

        if name == "Bash":
            command = inp.get("command", "") or ""
            if not command:
                continue

            # pytest/test commands
            if "pytest" in command or "unittest" in command:
                evidence["tests_run"].extend(_extract_test_names_from_command(command))

            # Git commits
            if "git commit" in command or "git add" in command:
                evidence["git_commits"] += 1
                evidence["files_modified"].extend(_extract_paths_from_git(command))

            # Verification commands
            if any(kw in command for kw in ("test", "verify", "check", "validate")):
                evidence["verification_commands_executed"].append(command)

        elif name == "ExecutePython":
            code = inp.get("code", "")
            if code:
                evidence["files_modified"].extend(_extract_paths_from_code(code))
                if any(kw in code for kw in ["def ", "class ", "import ", "async def"]):
                    evidence["code_generated"] = True

        elif name in ("Write", "Edit"):
            path = inp.get("file_path", "")
            if path:
                evidence["files_modified"].append(path)
                lower = path.lower()
                if any(kw in lower for kw in ("design", "spec", "architecture", "plan", "adr")):
                    evidence["design_artifacts"].append(path)
                if any(ext in path for ext in (".py", ".js", ".ts", ".sh")):
                    evidence["code_generated"] = True
            output = tool.get("output", "")
            if output:
                evidence["files_modified"].extend(_extract_paths_from_code(output))

        elif name == "Task":
            prompt = inp.get("prompt", "")
            if prompt:
                if any(kw in prompt.lower() for kw in ("write", "edit", "create file", "modify")):
                    evidence["code_generated"] = True

    # Deduplicate
    evidence["files_modified"] = list(dict.fromkeys(evidence["files_modified"]))
    evidence["tests_run"] = list(dict.fromkeys(evidence["tests_run"]))
    evidence["verification_commands_executed"] = list(
        dict.fromkeys(evidence["verification_commands_executed"])
    )
    evidence["design_artifacts"] = list(dict.fromkeys(evidence["design_artifacts"]))

    return evidence


def accumulate(existing: dict, new: dict) -> dict:
    """Merge new evidence into existing evidence, deduplicating lists."""
    result = {
        "files_modified": list(
            dict.fromkeys(existing.get("files_modified", []) + new.get("files_modified", []))
        ),
        "tests_run": list(
            dict.fromkeys(existing.get("tests_run", []) + new.get("tests_run", []))
        ),
        "verification_commands_executed": list(
            dict.fromkeys(
                existing.get("verification_commands_executed", [])
                + new.get("verification_commands_executed", [])
            )
        ),
        "code_generated": existing.get("code_generated", False) or new.get("code_generated", False),
        "design_artifacts": list(
            dict.fromkeys(existing.get("design_artifacts", []) + new.get("design_artifacts", []))
        ),
        "git_commits": existing.get("git_commits", 0) + new.get("git_commits", 0),
    }
    return result


def files_overlap_with_contract(
    subject_tokens: list[str],
    files_modified: list[str],
) -> bool:
    """Return True if any modified file overlaps with contract subject tokens."""
    if not subject_tokens or not files_modified:
        return False
    token_set = {t.lower() for t in subject_tokens}
    for filepath in files_modified:
        filename = filepath.split("/")[-1].split("\\")[-1].lower()
        for token in token_set:
            if token in filename:
                return True
    return False


def evidence_summary(evidence: dict) -> str:
    """Compact human-readable summary of evidence state."""
    parts = []
    files = evidence.get("files_modified", [])
    tests = evidence.get("tests_run", [])
    verifications = evidence.get("verification_commands_executed", [])
    commits = evidence.get("git_commits", 0)
    code_gen = evidence.get("code_generated", False)
    artifacts = evidence.get("design_artifacts", [])

    if files:
        parts.append(f"{len(files)} file(s) modified")
    if tests:
        parts.append(f"{len(tests)} test(s) run")
    if verifications:
        parts.append(f"{len(verifications)} verification(s)")
    if commits:
        parts.append(f"{commits} commit(s)")
    if code_gen:
        parts.append("code generated")
    if artifacts:
        parts.append(f"{len(artifacts)} design artifact(s)")

    return "; ".join(parts) if parts else "no evidence"


# ---------------------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------------------

if __name__ == "__main__":
    # Test file extraction
    code = 'open("foo.py").write("x")\nwith open("bar.py") as f: pass\nPath("baz.py")'
    paths = _extract_paths_from_code(code)
    assert "foo.py" in paths
    assert "bar.py" in paths
    assert "baz.py" in paths

    # Test evidence collection from Write tool
    tools = [
        {
            "name": "Write",
            "input": {"file_path": "P:/src/module.py"},
        }
    ]
    ev = collect_from_turn(tools)
    assert "P:/src/module.py" in ev["files_modified"]
    assert ev["code_generated"] is True

    # Test pytest command parsing
    cmd = "pytest tests/test_foo.py::TestBar::test_baz -v"
    tests = _extract_test_names_from_command(cmd)
    assert any("test_foo.py" in t for t in tests)

    # Test accumulation deduplication
    existing = {"files_modified": ["a.py"], "tests_run": ["test_a"]}
    new = {"files_modified": ["a.py", "b.py"], "tests_run": ["test_b"]}
    acc = accumulate(existing, new)
    assert acc["files_modified"] == ["a.py", "b.py"]
    assert acc["tests_run"] == ["test_a", "test_b"]

    # Test overlap detection
    tokens = ["stop", "cache", "hook"]
    files = ["P:/Stop.py", "P:/runner.py"]
    assert files_overlap_with_contract(tokens, files) is True
    assert files_overlap_with_contract(tokens, ["P:/other.py"]) is False

    print("All evidence_collector self-tests passed.")