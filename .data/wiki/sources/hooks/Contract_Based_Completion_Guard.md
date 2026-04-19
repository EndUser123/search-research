# Claude Code Contract-Based Completion Guard

## SOLUTION DESIGN

### Current State
Claude Code is currently allowed to declare tasks "done" based solely on its own textual claims, without reliable enforcement that required files were modified, tests were run, or verification criteria were met during the current session.
This leads to recurring issues where Claude asserts that bugs are fixed, tests have passed, or changes are complete when in fact no tests were executed, key files were untouched, or prior failures were never resolved.
Stop hooks exist but cannot inspect the current response, and prior attempts to enforce truthfulness relied on analyzing Claude's language instead of verifiable external state.
The system also lacks robust per-session tracking of actions taken (files touched, tests executed), which allows stale files or historical artifacts to masquerade as current verification evidence.

### Target State
All non-trivial tasks (e.g., "fix", "implement", "create", "refactor") are governed by an explicit JSON contract that defines required deliverables, tests, and success criteria for the current session.
Claude cannot successfully "stop" a governed task session unless the contract has been generated and all contractual conditions are satisfied using actions taken during that session.
Verification is based on concrete external evidence (files touched, test commands executed, passing results), not on Claude's textual claims or hallucinated success.
Multiple concurrent Claude Code sessions can operate safely, with each session maintaining its own isolated contract and progress state keyed by session_id.

### Architecture Overview
The solution introduces a **contract-based validation pipeline** wired into Claude Code hooks, focusing on preconditions and external state:
- **UserPromptSubmit** (optional): Detects substantive tasks in prompts (e.g., containing "fix", "implement", "create").
- **PreToolUse**: Enforces that a JSON contract exists for substantive tasks before any substantive tools (Write/Edit/Bash) may run.
- **PostToolUse_contract_extractor**: Extracts and persists a structured JSON contract from Claude's written content when present.
- **PostToolUse_progress_tracker**: Logs session-local progress by recording files touched and tests executed from tool calls.
- **Stop_contract_validator**: On Stop, loads the contract and progress for the current session_id and blocks completion if contractual obligations remain unmet.

Logical flow:
1. User issues a substantive task request.
2. PreToolUse blocks any substantive tools until a valid contract is generated.
3. Contract is written by Claude (as JSON) into a file; PostToolUse extracts and stores it as `{session_id}_contract.json`.
4. Throughout the session, PostToolUse_progress_tracker records files touched and test executions as `{session_id}_progress.json`.
5. When Claude attempts to stop, Stop_contract_validator compares contract deliverables against recorded progress and either allows stop or returns a detailed remediation list.

### Key Changes
1. **Introduce JSON Contracts for Substantive Tasks**  
   Why: Natural-language plans are ambiguous and hard to parse reliably. A structured JSON contract provides a stable schema for automated validation.

2. **Enforce Contract Before Work (PreToolUse Gate)**  
   Why: Prevents work from proceeding without a plan, avoiding the rage-inducing situation where work is done but later blocked for missing contracts.

3. **Track Session-Local Progress via PostToolUse**  
   Why: Distinguishes between stale artifacts from previous sessions and actions actually performed in the current session.

4. **Validate on Stop Using External State Only**  
   Why: Avoids architectural limitations of Stop hooks (no current response access) by relying purely on contract + recorded tool activity.

5. **Use Per-Session State Files**  
   Why: Prevents cross-session contamination when running multiple concurrent Claude Code sessions.

### Benefits & Metrics
- **False "Done" Claims**: Expected reduction of unverified "done" assertions by 80–90% for governed tasks, as completion is gated on concrete evidence instead of text.
- **Test Enforcement**: For contracts that require tests, the rate of tasks completed without any test execution should drop to near 0%.
- **Session Isolation**: Zero cross-session interference due to per-session contract and progress files.
- **Operator Confidence**: A Stop decision now includes a precise list of unmet contractual gaps, improving explainability and debuggability.

### Trade-offs & Constraints
- **Increased Friction for Substantive Tasks**: Tasks that require a contract will incur an upfront planning step and stricter completion checks; this is an intentional cost to eliminate fake "done".
- **Requires Claude to Emit JSON Contracts**: Prompts and examples must be tuned so Claude reliably emits valid JSON when asked for a contract.
- **Hook Logic Complexity**: The system adds multiple hooks and JSON state files; failures in these hooks can block or misclassify completion.
- **Coverage Limitations**: Simple Q&A or exploratory interactions are not governed by contracts unless explicitly chosen, so they are not validated by this system.

---

## IMPLEMENTATION

### Files Required
Project-relative paths (create these in your Claude Code workspace root):

```
.claude/
├── hooks/
│   ├── PreToolUse_contract_enforcer.py
│   ├── PostToolUse_contract_extractor.py
│   ├── PostToolUse_progress_tracker.py
│   └── Stop_contract_validator.py
└── session_state/
    └── (auto-created) {session_id}_contract.json / {session_id}_progress.json
```

All hooks are Python scripts and should be executable by the same Python used by Claude Code for hooks.

### Configuration Reference

| Item | Type | Default | Purpose |
|------|------|---------|---------|
| `CONTRACT_DIR` | string | `.claude/session_state` | Directory for per-session contract and progress files |
| `SUBSTANTIVE_KEYWORDS` | list[string] | `["fix","implement","create","refactor","add test"]` | Words that mark a task as requiring a contract |
| `TEST_COMMAND_MATCH` | pattern | `"pytest" in command.lower()` | Heuristic to identify test runs in Bash tool calls |
| `CONTRACT_REQUIRED_TOOLS` | list[string] | `["Write","Edit","Bash"]` | Tools blocked until contract exists for substantive tasks |

You can hard-code these in the hook files or adapt them as needed.

### Hook 1: PreToolUse Contract Enforcer

Path: `.claude/hooks/PreToolUse_contract_enforcer.py`

```python
import sys
import json
import os
import re

CONTRACT_DIR = os.path.join('.claude', 'session_state')
CONTRACT_REQUIRED_TOOLS = ["Write", "Edit", "Bash"]
SUBSTANTIVE_KEYWORDS = ["fix", "implement", "create", "refactor", "add test", "add tests"]

def is_substantive_task(text: str) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(re.search(rf"\b{re.escape(kw)}\b", lowered) for kw in SUBSTANTIVE_KEYWORDS)


def main() -> None:
    data = json.load(sys.stdin)

    session_id = data.get('session_id', '')
    tool_name = data.get('tool_name', '')
    tool_input = data.get('tool_input', {}) or {}

    # Only enforce for certain tools
    if tool_name not in CONTRACT_REQUIRED_TOOLS:
        sys.exit(0)

    # Derive text to inspect for substantive intent
    text = ""
    if tool_name in ("Write", "Edit"):
        text = tool_input.get('content', '') or ''
    elif tool_name == "Bash":
        text = tool_input.get('command', '') or ''

    if not is_substantive_task(text):
        sys.exit(0)

    contract_path = os.path.join(CONTRACT_DIR, f"{session_id}_contract.json")

    if not os.path.exists(contract_path):
        # Block execution until a contract exists
        message = (
            "Substantive task detected (e.g., fix/implement/create/refactor), "
            "but no PLAN_CONTRACT is present for this session.\n\n"
            "Before using Write/Edit/Bash for this task, generate a JSON contract like:\n\n"
            "{\n"
            "  \"contract_version\": \"1.0\",\n"
            "  \"session_id\": \"" + session_id + "\",\n"
            "  \"task_summary\": \"Short description of the task\",\n"
            "  \"deliverables\": {\n"
            "    \"files_to_modify\": [\"path/to/file.py\"],\n"
            "    \"files_to_create\": [\"tests/test_file.py\"],\n"
            "    \"tests_required\": true,\n"
            "    \"test_command\": \"pytest tests/test_file.py -v\"\n"
            "  },\n"
            "  \"acceptance\": {\n"
            "    \"tests_must_pass\": true,\n"
            "    \"manual_verification\": false\n"
            "  }\n"
            "}\n"
        )
        json.dump({"decision": "block", "reason": message}, sys.stdout)
        sys.exit(0)

    # Contract exists, allow execution
    sys.exit(0)


if __name__ == "__main__":
    main()
```

### Hook 2: PostToolUse Contract Extractor

Path: `.claude/hooks/PostToolUse_contract_extractor.py`

This hook looks for a JSON contract embedded in content written via Write/Edit and stores it as `{session_id}_contract.json`.

```python
import sys
import json
import os
import re

CONTRACT_DIR = os.path.join('.claude', 'session_state')

# Simple heuristic to find a JSON object containing a "deliverables" key
JSON_OBJECT_WITH_DELIVERABLES = re.compile(r"\{[\s\S]*?\"deliverables\"[\s\S]*?\}")

def main() -> None:
    data = json.load(sys.stdin)

    session_id = data.get('session_id', '')
    tool_name = data.get('tool_name', '')
    tool_input = data.get('tool_input', {}) or {}

    if tool_name not in ("Write", "Edit"):
        sys.exit(0)

    content = tool_input.get('content', '') or ''
    match = JSON_OBJECT_WITH_DELIVERABLES.search(content)
    if not match:
        sys.exit(0)

    raw_json = match.group(0)
    try:
        contract = json.loads(raw_json)
    except json.JSONDecodeError:
        sys.exit(0)

    # Ensure directory exists
    os.makedirs(CONTRACT_DIR, exist_ok=True)
    contract['session_id'] = session_id

    contract_path = os.path.join(CONTRACT_DIR, f"{session_id}_contract.json")
    with open(contract_path, 'w', encoding='utf-8') as f:
        json.dump(contract, f, indent=2)

    sys.exit(0)


if __name__ == "__main__":
    main()
```

### Hook 3: PostToolUse Progress Tracker

Path: `.claude/hooks/PostToolUse_progress_tracker.py`

This hook records files touched and tests executed for the current session.

```python
import sys
import json
import os

CONTRACT_DIR = os.path.join('.claude', 'session_state')


def load_progress(path: str) -> dict:
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {
        "session_id": "",
        "actions": {
            "files_touched": [],
            "tests_executed": []
        }
    }


def save_progress(path: str, progress: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(progress, f, indent=2)


def main() -> None:
    data = json.load(sys.stdin)

    session_id = data.get('session_id', '')
    tool_name = data.get('tool_name', '')
    tool_input = data.get('tool_input', {}) or {}
    tool_response = data.get('tool_response', {}) or {}

    progress_path = os.path.join(CONTRACT_DIR, f"{session_id}_progress.json")
    progress = load_progress(progress_path)
    progress['session_id'] = session_id

    # Track file touches
    if tool_name in ("Write", "Edit"):
        file_path = tool_input.get('file_path', '') or ''
        progress['actions']['files_touched'].append({
            'path': file_path,
            'tool': tool_name,
            'timestamp': data.get('timestamp', '')
        })

    # Track test executions via Bash
    if tool_name == "Bash":
        command = tool_input.get('command', '') or ''
        if 'pytest' in command.lower() or 'test ' in command.lower():
            exit_code = tool_response.get('exit_code', 999)
            stdout = tool_response.get('stdout', '') or ''

            # Basic heuristic: exit_code == 0 and "passed" in stdout
            passed = (exit_code == 0) and ('passed' in stdout.lower())

            progress['actions']['tests_executed'].append({
                'command': command,
                'exit_code': exit_code,
                'passed': passed,
                'timestamp': data.get('timestamp', '')
            })

    save_progress(progress_path, progress)
    sys.exit(0)


if __name__ == "__main__":
    main()
```

### Hook 4: Stop Contract Validator

Path: `.claude/hooks/Stop_contract_validator.py`

This hook compares the contract against session-local progress and blocks completion if gaps remain.

```python
import sys
import json
import os
from typing import List, Dict

CONTRACT_DIR = os.path.join('.claude', 'session_state')


def load_json(path: str) -> dict:
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def validate_completion(contract: dict, progress: dict) -> List[str]:
    gaps: List[str] = []

    deliverables: Dict = contract.get('deliverables', {}) or {}
    files_to_modify = deliverables.get('files_to_modify', []) or []
    tests_required = bool(deliverables.get('tests_required', False))

    actions = progress.get('actions', {}) or {}
    files_touched = actions.get('files_touched', []) or []
    tests_executed = actions.get('tests_executed', []) or []

    touched_paths = {entry.get('path', '') for entry in files_touched}

    # 1. Files promised vs touched this session
    for path in files_to_modify:
        if path and path not in touched_paths:
            gaps.append(f"PROMISED but NOT MODIFIED this session: {path}")

    # 2. Tests required vs actually executed and passed
    if tests_required:
        if not tests_executed:
            gaps.append("NO TESTS EXECUTED - contract requires tests")
        else:
            any_passing = any(
                (entry.get('exit_code') == 0) and bool(entry.get('passed'))
                for entry in tests_executed
            )
            if not any_passing:
                gaps.append("TESTS EXECUTED but NO PASSING RUNS - fix failures before completion")

    return gaps


def main() -> None:
    data = json.load(sys.stdin)

    session_id = data.get('session_id', '')
    stop_hook_active = bool(data.get('stop_hook_active'))

    # Prevent infinite loops: if this Stop hook already blocked once, allow next stop
    if stop_hook_active:
        sys.exit(0)

    contract_path = os.path.join(CONTRACT_DIR, f"{session_id}_contract.json")
    progress_path = os.path.join(CONTRACT_DIR, f"{session_id}_progress.json")

    contract = load_json(contract_path)
    progress = load_json(progress_path)

    # No contract: treat as simple session, allow stop
    if not contract:
        sys.exit(0)

    gaps = validate_completion(contract, progress)

    if gaps:
        reason = "Contract incomplete:\n" + "\n".join(f"- {g}" for g in gaps)
        json.dump({"decision": "block", "reason": reason}, sys.stdout)
        sys.exit(0)

    # All good, allow stop
    sys.exit(0)


if __name__ == "__main__":
    main()
```

### Step-by-Step Setup

1. **Create directories** (from your project root where `.claude` lives):

   ```powershell
   New-Item -ItemType Directory -Path .claude -ErrorAction SilentlyContinue | Out-Null
   New-Item -ItemType Directory -Path .claude/hooks -ErrorAction SilentlyContinue | Out-Null
   New-Item -ItemType Directory -Path .claude/session_state -ErrorAction SilentlyContinue | Out-Null
   ```

2. **Create each hook file** and paste the corresponding Python code:

   - `.claude/hooks/PreToolUse_contract_enforcer.py`
   - `.claude/hooks/PostToolUse_contract_extractor.py`
   - `.claude/hooks/PostToolUse_progress_tracker.py`
   - `.claude/hooks/Stop_contract_validator.py`

3. **Ensure Python is available** to Claude Code hooks (typically the same Python on your PATH in Windows PowerShell).

4. **Enable hooks in Claude Code settings** (if required by your version): point PreToolUse, PostToolUse, and Stop events to execute these scripts.

5. **Restart Claude Code sessions** so new hooks are discovered and applied.

### Testing Patterns

- **Test 1: Contract Enforcement**  
  Goal: Verify that substantive tasks are blocked until a contract exists.
  1. Start a new Claude Code session.
  2. Ask Claude to "fix the login bug in `src/auth/login.py`".
  3. Let Claude attempt to run Write/Edit/Bash without generating a contract.
  4. Confirm that PreToolUse returns a block with instructions to create a JSON contract.

- **Test 2: Contract Extraction**  
  Goal: Verify that contracts written by Claude are captured.
  1. In Claude, ask it to write a JSON PLAN_CONTRACT to a file via Write.
  2. Confirm `.claude/session_state/{session_id}_contract.json` is created and contains the JSON.

- **Test 3: Progress Tracking**  
  Goal: Confirm that file modifications and test runs are logged per session.
  1. Run Write/Edit on a file included in the contract.
  2. Run a Bash command that includes `pytest`.
  3. Inspect `.claude/session_state/{session_id}_progress.json` for `files_touched` and `tests_executed` entries.

- **Test 4: Stop Validation Blocks Incomplete Work**  
  Goal: Verify that Stop is blocked when contract conditions are not met.
  1. Create a contract requiring modification of `src/auth/login.py` and tests.
  2. Modify the file but do not run tests.
  3. Trigger a Stop event.
  4. Confirm that `Stop_contract_validator` blocks stop and returns a message about missing tests.

- **Test 5: Stop Allows Completed Work**  
  Goal: Verify that Stop succeeds after contractual obligations are met.
  1. Modify required files.
  2. Run the specified pytest command and ensure it passes.
  3. Trigger Stop.
  4. Confirm that Stop is allowed and session ends normally.

### Troubleshooting

#### Issue: Hooks Do Not Seem to Run
**Symptom:** No contract or progress files are created; Claude behaves as before.
**Solution:**
- Verify hook scripts are in `.claude/hooks/` with exact filenames.
- Check Claude Code hook settings for PreToolUse, PostToolUse, and Stop events.
- Add temporary logging (e.g., writing to a debug file) inside hooks to confirm execution.

#### Issue: Contract Extraction Fails
**Symptom:** Claude writes a contract, but no `{session_id}_contract.json` is created.
**Solution:**
- Ensure the contract is valid JSON containing a `"deliverables"` key.
- Adjust the regex in `PostToolUse_contract_extractor.py` if your contract format differs.
- Manually test `json.loads` on the emitted contract to confirm it's parseable.

#### Issue: Stop Blocks Even When Work Seems Complete
**Symptom:** Stop returns gaps, but you believe all work is done.
**Solution:**
- Inspect `{session_id}_progress.json` to see which files and tests were actually recorded.
- Confirm that file paths in the contract match actual paths used in Write/Edit.
- Confirm that tests were executed via Bash with commands containing `pytest` and that they passed.

#### Issue: Multiple Sessions Interfere
**Symptom:** One session's contract appears to affect another.
**Solution:**
- Verify that all contract and progress files are named `{session_id}_contract.json` and `{session_id}_progress.json`.
- Confirm that session_id is correctly passed in the hook input (log it if necessary).

---

## STEADY-STATE OPERATION

### Daily Workflows

- **Starting a Substantive Task**  
  1. Open a Claude Code session for a task like "Fix the login bug".
  2. Prompt Claude: "First, create a JSON PLAN_CONTRACT for this task and write it to a file using Write. Then proceed with the implementation."  
  3. Ensure the contract includes `files_to_modify`, `files_to_create`, `tests_required`, and `test_command`.

- **Working Under a Contract**  
  - Let Claude use Write/Edit/Bash to implement changes and run tests.  
  - The progress tracker will automatically log files touched and test runs.

- **Completing a Task**  
  - When Claude believes the task is complete, it will attempt to stop.  
  - If contractual gaps exist (untouched files, missing or failing tests), Stop will be blocked with a precise remediation list.
  - After addressing all gaps, a subsequent Stop will be allowed.

### Health Checks (On-Demand)

Run these from a PowerShell terminal in the project root.

```powershell
# List all contract files
Get-ChildItem .claude\session_state\*_contract.json | Select-Object Name, LastWriteTime

# View the current session's contract (replace SESSION_ID)
Get-Content .claude\session_state\SESSION_ID_contract.json

# View progress for a session
Get-Content .claude\session_state\SESSION_ID_progress.json
```

Expected results:
- Contract files exist for substantive sessions.
- Progress files show recent files_touched and tests_executed entries.

### Common Operational Tasks

- **Reset Contract for a Session**  
  Use when a task's scope changes significantly.

  ```powershell
  Remove-Item .claude\session_state\SESSION_ID_contract.json -ErrorAction SilentlyContinue
  Remove-Item .claude\session_state\SESSION_ID_progress.json -ErrorAction SilentlyContinue
  ```

- **Archive Old Session State**  
  Periodically move completed session state files to an archive directory.

  ```powershell
  New-Item -ItemType Directory -Path .claude\session_state_archive -ErrorAction SilentlyContinue | Out-Null
  Move-Item .claude\session_state\*_*.json .claude\session_state_archive\
  ```

- **Temporarily Disable the System**  
  Rename hook files to disable enforcement without deleting them.

  ```powershell
  Rename-Item .claude\hooks\PreToolUse_contract_enforcer.py PreToolUse_contract_enforcer.py.disabled
  Rename-Item .claude\hooks\Stop_contract_validator.py Stop_contract_validator.py.disabled
  ```

- **Re-enable the System**  

  ```powershell
  Rename-Item .claude\hooks\PreToolUse_contract_enforcer.py.disabled PreToolUse_contract_enforcer.py
  Rename-Item .claude\hooks\Stop_contract_validator.py.disabled Stop_contract_validator.py
  ```
