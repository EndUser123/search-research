# Intent-Driven CKS Filtering Criteria

**Purpose**: Document the signal/noise filtering criteria for automatic knowledge capture.

## Signal Quality Principles

### What Gets Captured (Signal)

**File Types**:
- Production code: `src/**/*.py`, `src/**/*.ts`, `src/**/*.js`
- Framework code: `__csf/**/*.py`
- Hook system: `.claude/hooks/**/*.py`

**Intent Types**:
- `bugfix`: "fix the circular import in cks_context"
- `feature`: "implement authentication system"
- `refactor`: "refactor the database module"
- `test`: "add tests for payment system"
- `optimization`: "optimize query performance"

**Change Thresholds**:
- Edit size: ≥100 characters
- Meaningful intent: work_type != "unknown" OR target != "unspecified"
- Content: Code preview with problem context

### What Gets Filtered (Noise)

**File Types** (60% filter rate):
- Test files: `tests/**`, `test_*.py`, `*_test.py`
- Documentation: `*.md`, `*.txt`, `*.rst`
- Configuration: `*.json`, `*.yaml`, `*.toml`, `*.ini`
- Git metadata: `.git/**`
- Build artifacts: `dist/**`, `build/**`, `*.egg-info`

**Change Thresholds**:
- Small edits: <100 characters
- Short prompts: <15 characters
- No clear intent: work_type = "unknown" AND target = "unspecified"

**Already Processed**:
- Prompts starting with: "CKS entry stored", "Intent extracted", "##"

## Intent Detection Patterns

### Bugfix Patterns
```python
r"fix(?:ed)?\s+(?:the\s+)?(?:bug|issue|problem|error)"
r"fix(?:ed)?\s+(?:the\s+)?[\w\s]+"  # General: "fix X"
r"debug(?:ging)?\s+\w+"
r"resolve\s+\w+"
```

### Feature Patterns
```python
r"(?:add|implement|create)\s+(?:new\s+)?(?:feature|functionality|capability)"
r"add\s+support\s+for"
```

### Refactor Patterns
```python
r"refactor(?:ing)?\s+\w+"
r"re(?:write|structure)\s+\w+"
r"clean\s+up\s+\w+"
```

## CKS Entry Format

### Question
```yaml
{work_type}: {target}
# Example: "bugfix: cks_context.py"
```

### Answer
```yaml
Problem: {problem_description}
User intent: {user_prompt_excerpt}

Changes made:
  Modified: {file_path}
  Size: {character_count}

Code preview:
  {code_snippet}

Timestamp: {iso_timestamp}
```

### Metadata
```json
{
  "source": "claude_code_auto_immediate",
  "work_type": "bugfix",
  "target": "cks_context.py",
  "problem": "circular import",
  "user_intent": "fix the circular import in cks_context",
  "file_path": "P:/.claude/hooks/UserPromptSubmit/cks_context.py",
  "size": 450,
  "stored_at": "2026-03-05T12:01:00Z"
}
```

## Performance Characteristics

**Intent Extraction**:
- Speed: <5ms per prompt (regex-based)
- Token cost: 0 (no LLM calls)
- Overhead: Negligible

**CKS Storage**:
- Write time: ~50-100ms per edit
- Reads: 1 JSON file load (<1ms)
- Impact: Background operation, doesn't block

**Total Token Cost**: 0 (all processing is local)

## Configuration

**Enable/Disable**:
```bash
# Enable intent-driven capture (default)
export CKS_INTEGRATION_ENABLED=true

# Disable completely
export CKS_INTEGRATION_ENABLED=false
```

**Debug Mode**:
```bash
# Show detected intents in stdout
export CKS_DEBUG=1
```

## Monitoring Commands

**Check CKS for enhanced entries**:
```bash
python -c "
import sqlite3
conn = sqlite3.connect('P:/__csf/data/cks.db')
cursor = conn.cursor()
cursor.execute('''
    SELECT title, created_at, metadata
    FROM entries
    WHERE metadata LIKE '%work_type%'
    ORDER BY created_at DESC
    LIMIT 10
''')
for row in cursor.fetchall():
    print(f'Title: {row[0]}')
    print(f'Created: {row[1]}')
    print(f'Metadata: {row[2][:200]}...')
    print()
conn.close()
"
```

**View intent state**:
```bash
cat P:/.claude/hooks/session_data/intent_state.json
```

**Check storage rate**:
```bash
python -c "
import sqlite3
conn = sqlite3.connect('P:/__csf/data/cks.db')
cursor = conn.cursor()

# Total entries
cursor.execute('SELECT COUNT(*) FROM entries')
total = cursor.fetchone()[0]

# Enhanced entries
cursor.execute('''
    SELECT COUNT(*) FROM entries
    WHERE metadata LIKE '%work_type%'
''')
enhanced = cursor.fetchone()[0]

print(f'Total CKS entries: {total}')
print(f'Enhanced entries: {enhanced}')
print(f'Enhancement rate: {enhanced/total*100:.1f}%')
conn.close()
"
```

## Maintenance

**Cleanup low-quality entries** (future feature):
```bash
# Delete entries with unknown work_type and no useful content
python P:/__csf/src/cks/cleanup.py --min-quality 0.3 --dry-run
```

**Rebuild intent patterns** (if detection rate drops):
```python
# Edit: P:/.claude/hooks/UserPromptSubmit/intent_extractor.py
# Update INTENT_PATTERNS dict with new regex patterns
```

## Verification

**Functional Test**:
```bash
python P:/.claude/hooks/tests/test_intent_cks_integration.py
```

**Expected Results**:
- Intent extraction: 4/4 patterns detected
- State persistence: Save/load verified
- CKS formatting: Enhanced format verified

## Date: 2026-03-05
## Status: Production Ready
