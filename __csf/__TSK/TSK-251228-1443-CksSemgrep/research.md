# Research: CKS → Semgrep Auto-Fix Integration

## Existing CKS Schema Analysis

**File**: `P:/__csf.nip/data/cks.db`

```sql
CREATE TABLE entries (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,          -- 'python_standard', 'anti_pattern', etc.
    title TEXT,
    content TEXT NOT NULL,
    metadata TEXT,               -- JSON! ✅ Can store semgrep_yaml
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    embedding BLOB,
    usage_count INTEGER,
    ...
);
```

**Finding**: No schema changes needed. `metadata` is TEXT field that can store JSON containing YAML strings.

## Semgrep CLI Research

### Installation
```bash
pip install semgrep
# or
choco install semgrep
```

### Key Commands
```bash
# Run with auto-fix
semgrep --config=.semgrep.yml --autofix --json <target>

# Dry-run (preview fixes)
semgrep --config=.semgrep.yml --dryrun --json <target>

# Check only (no fixes)
semgrep --config=.semgrep.yml --json <target>
```

### Return Codes
- `0`: No issues found
- `1`: Issues found (not an error!)
- `2+`: Actual error (invalid config, syntax error, etc.)

### Output Format
```json
{
  "results": [
    {
      "check_id": "no-pickle",
      "path": "src/app.py",
      "start": {"line": 42, "col": 0},
      "end": {"line": 42, "col": 12},
      "extra": {
        "message": "Use json instead of pickle",
        "severity": "ERROR",
        "fix": "import json"
      }
    }
  ],
  "errors": []
}
```

## Existing CKS Integration

**File**: `P:/__csf.nip/src/quality/unified_analyzer.py`

Current CKS query pattern:
```python
def _get_cks_db_path(self) -> Path | None:
    for path in [
        Path.cwd() / "data" / "cks.db",
        Path(__file__).parent.parent.parent / "data" / "cks.db",
        Path("P:/__csf.nip/data/cks.db"),
    ]:
        if path.exists():
            return path
    return None
```

## YAML Merge Strategy

### Problem
Multiple CKS entries with individual `semgrep_yaml`:

```yaml
# Entry 1
rules:
  - id: no-pickle
    pattern: import pickle

# Entry 2
rules:
  - id: no-eval
    pattern: eval(...)
```

### Solution
Extract rule lists, merge under single `rules:` header:

```python
def merge_semgrep_yamls(yaml_strings: List[str]) -> str:
    """Merge multiple Semgrep YAML configs into one"""
    import yaml

    all_rules = []
    for yaml_str in yaml_strings:
        data = yaml.safe_load(yaml_str)
        if data and "rules" in data:
            all_rules.extend(data["rules"])

    merged = yaml.dump({"rules": all_rules}, sort_keys=False)
    return merged
```

## Windows Subprocess Considerations

### Issue
Windows subprocess may not find `semgrep` in PATH.

### Mitigations
1. Use `shell=True` on Windows
2. Find full path with `where semgrep` or `shutil.which()`
3. Handle path with spaces correctly

```python
import shutil
import platform

semgrep_path = shutil.which("semgrep")
if not semgrep_path:
    raise FileNotFoundError("Semgrep not installed")

cmd = [semgrep_path, "--config", config_path, "--json", "--autofix", target]
if platform.system() == "Windows":
    result = subprocess.run(cmd, shell=True, ...)
else:
    result = subprocess.run(cmd, ...)
```

## Temp File Cleanup Pattern

```python
from pathlib import Path
import tempfile

def run_with_temp_config(yaml_content: str, target: str):
    config_path = None
    try:
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            config_path = Path(f.name)

        # Run Semgrep
        result = subprocess.run([
            'semgrep', '--config', str(config_path), '--json', '--autofix', target
        ], capture_output=True, text=True)

        return json.loads(result.stdout)

    finally:
        # Always cleanup
        if config_path and config_path.exists():
            config_path.unlink()
```

## References
- https://semgrep.dev/docs/writing-rules/overview/
- https://semgrep.dev/docs/CLI-reference/
- https://github.com/returntocorp/semgrep
