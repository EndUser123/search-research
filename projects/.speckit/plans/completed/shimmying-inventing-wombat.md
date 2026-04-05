---
status: completed
completed_at: 2025-12-22T15:30:14.979385
implementing_commit: 33cacdf33c6e0735fce7adbea3d278973750752d
archived_at: 2025-12-22T15:30:14.979411
archive_path: P:/.speckit/plans/completed/shimmying-inventing-wombat.md
---

# Plan Lifecycle Management System

## Problem

When a Claude Code session is resumed, old plan files (from completed work) remain indistinguishable from new plans. This causes the AI to mistakenly re-implement already-completed work.

**Example of the mistake:**
- Session 1: Plan created → Implemented → Committed → Session ends
- Session 2: Resumed → AI finds plan file → Re-implements (thinking it's new work)

**Root cause:** Plan files lack status metadata (pending/completed) and automatic archival.

## Solution Overview

**Hybrid approach:**
1. YAML frontmatter for status tracking in plan files
2. Directory separation (active/ vs completed/)
3. Prompt-for-confirmation on plan mode exit
4. Automatic migration of existing plans via git history analysis
5. Hook-based status detection when reading plans

## Implementation Plan

### Phase 1: Core Infrastructure

#### 1.1 Enhanced Plan File Format

**Add YAML frontmatter to all new plans:**

```yaml
---
status: pending
created_at: 2025-12-22T22:15:00Z
created_by_session: shimmying-inventing-wombat
linked_tsk: null
completed_at: null
implementing_commit: null
archived_at: null
archive_path: P:/.speckit/plans/completed/shimmying-inventing-wombat.md
---

# Plan Title

Content continues...
```

**Status values:**
- `pending` - New plan, not yet implemented
- `completed` - Successfully implemented, archived
- `abandoned` - Cancelled or obsolete

#### 1.2 Directory Structure

**Create subdirectories:**
```
~/.claude/plans/
├── active/          # pending and in-progress plans
├── completed/       # successfully completed plans
└── abandoned/       # cancelled plans
```

**File: `P:\__csf.nip\src\utils\plan_lifecycle_manager.py`**

Core class for managing plan status transitions:
```python
class PlanLifecycleManager:
    """Manage plan status, metadata, and archival."""

    def __init__(self, plans_dir: Path):
        self.plans_dir = Path(plans_dir)
        self.active_dir = self.plans_dir / "active"
        self.completed_dir = self.plans_dir / "completed"
        self.abandoned_dir = self.plans_dir / "abandoned"
        self._ensure_directories()

    def create_plan(self, content: str, metadata: dict) -> Path:
        """Create new plan with YAML frontmatter."""

    def update_status(self, plan_path: Path, new_status: str,
                     commit_hash: Optional[str] = None) -> bool:
        """Update plan status in YAML frontmatter."""

    def archive_plan(self, plan_path: Path, status: str,
                    commit_hash: Optional[str] = None) -> Path:
        """Move plan to completed/ or abandoned/ with metadata update."""

    def is_plan_completed(self, plan_path: Path) -> bool:
        """Check if plan has status: completed."""
```

### Phase 2: Plan Redirector Enhancement

**File: `P:\.claude\hooks\plan_redirector.py`** (MODIFY)

**Change 1: Redirect to active/ subdirectory**
```python
# Line 135-137: Update path generation
plans_dir = os.path.join(str(project_dir), ".plans", "active")  # Add /active
filename = generate_plan_filename(project_id)
new_path = os.path.join(plans_dir, filename).replace("\\", "/")
```

**Change 2: Add YAML frontmatter instead of HTML comments**
```python
# Lines 66-73: Replace generate_plan_header()
def generate_plan_header(project_id: str, original_path: str) -> str:
    """Generate YAML frontmatter with status metadata."""
    timestamp = datetime.now().isoformat()
    session_id = os.path.basename(original_path).replace(".md", "")

    return f"""---
status: pending
created_at: {timestamp}
created_by_session: {session_id}
linked_tsk: {project_id}
completed_at: null
implementing_commit: null
archived_at: null
archive_path: P:/.speckit/plans/completed/shimmying-inventing-wombat.md
---

<!-- TSK: {project_id} -->
<!-- Redirected from: {original_path} -->
<!-- Generated: {timestamp} -->

"""
```

### Phase 3: Exit Plan Mode Hook

**File: `P:\.claude\hooks\on_exit_plan_mode.py`** (CREATE)

**Behavior:** When user exits plan mode, prompt for completion status.

```python
#!/usr/bin/env python3
"""
ExitPlanMode Hook - Plan Completion Confirmation

Prompts user to confirm plan completion status when exiting plan mode.
Automatically archives completed/abandoned plans with metadata updates.
"""

def main():
    """Execute on plan mode exit."""
    import sys
    import json
    from pathlib import Path

    # Read hook input (contains context about current plan)
    hook_input = json.loads(sys.stdin.read())
    plan_file = hook_input.get("plan_file")  # Path to current plan

    if not plan_file or not Path(plan_file).exists():
        print("[ExitPlanMode] No plan file found, skipping")
        sys.exit(0)

    # Prompt user for status (this will be printed to user)
    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  PLAN MODE EXITED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Current plan: {Path(plan_file).name}

Was this plan successfully implemented?

  [y] Yes  - Mark as completed and archive
  [n] No   - Keep as pending for later work
  [a] Abandon - Cancel and archive as obsolete

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

    # Get user choice via stdin
    choice = input("Choice (y/n/a): ").strip().lower()

    # Return output for hook processing
    output = {
        "decision": "archive" if choice == 'y' else "abandon" if choice == 'a' else "pending",
        "plan_file": plan_file,
        "choice": choice
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()
```

**Note:** Claude Code will need to invoke this hook after ExitPlanMode. This requires hook integration.

### Phase 4: Plan Status Detection Hook

**File: `P:\.claude\hooks\plan_status_detector.py`** (CREATE)

**Purpose:** Add visual status badges when reading plans so AI can distinguish old vs new.

```python
#!/usr/bin/env python3
"""
PlanStatusDetector Hook - Visual Status Badges

Adds status badges to plan content when read via Read tool.
Prevents AI from mistaking completed plans for pending work.
"""

def detect_and_annotate(content: str, file_path: str) -> str:
    """Add status annotation to plan content."""
    import re
    from pathlib import Path

    # Check for YAML frontmatter
    yaml_match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)

    if not yaml_match:
        # Legacy plan without metadata
        return "[LEGACY PLAN - STATUS UNKNOWN]\n\n" + content

    frontmatter = yaml_match.group(1)
    body = yaml_match.group(2)

    # Extract status
    status_match = re.search(r'status:\s*(\w+)', frontmatter)
    status = status_match.group(1) if status_match else "unknown"

    # Generate badge
    BADGES = {
        "pending": "⏳ [PENDING - IMPLEMENT THIS]",
        "completed": "✅ [COMPLETED - ALREADY DONE]",
        "abandoned": "🚫 [ABANDONED - CANCELLED]",
        "unknown": "❓ [UNKNOWN STATUS]"
    }

    badge = BADGES.get(status, BADGES["unknown"])

    # Extract additional metadata
    created_match = re.search(r'created_at:\s*([^\n]+)', frontmatter)
    created = created_match.group(1) if created_match else "unknown"

    completed_match = re.search(r'completed_at:\s*([^\n]+)', frontmatter)
    completed = completed_match.group(1) if completed_match else None

    # Add status header
    header = f"{badge}\n"
    header += f"Created: {created}\n"
    if completed:
        header += f"Completed: {completed}\n"
    header += "\n" + body

    return header

def main():
    """Execute on Read tool for plan files."""
    import sys
    import json

    hook_input = json.loads(sys.stdin.read())
    tool_input = hook_input.get("tool_input", {})
    content = tool_input.get("content", "")
    file_path = tool_input.get("file_path", "")

    # Only process plan files
    if "plan" not in file_path.lower():
        sys.exit(0)

    # Add status badge
    annotated = detect_and_annotate(content, file_path)

    # Return updated content
    output = {
        "decision": "approve",
        "updatedInput": {
            "content": annotated
        }
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()
```

### Phase 5: Migration Tool for Existing Plans

**File: `P:\__csf.nip\scripts\migrate_plan_files.py`** (CREATE)

**Purpose:** Analyze existing plans and auto-migrate to new structure with inferred completion status.

```python
#!/usr/bin/env python3
"""
Plan Migration Script - Auto-migrate existing plans

Analyzes git history to infer if plans were completed, then:
1. Adds YAML frontmatter with status
2. Moves to appropriate directory (active/ or completed/)
"""

import re
import subprocess
from datetime import datetime
from pathlib import Path

def extract_creation_date(plan_path: Path) -> datetime:
    """Extract creation date from plan HTML comments."""
    content = plan_path.read_text()
    match = re.search(r'<!-- Generated:\s*([^\n]+) -->', content)
    if match:
        return datetime.fromisoformat(match.group(1))
    return datetime.fromtimestamp(plan_path.stat().st_mtime)

def find_commits_after_date(after_date: datetime, file_patterns: list) -> list:
    """Find git commits after plan creation that match file patterns."""
    try:
        cmd = [
            "sl", "log", "-l", "100",
            "--template", "{node}\n{desc}\n"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        # Parse and filter commits
        # Return commits after creation date that seem related to plan
        return []
    except Exception:
        return []

def infer_plan_status(plan_path: Path) -> tuple:
    """
    Infer plan status from git history and content.

    Returns: (status, commit_hash)
    """
    created_date = extract_creation_date(plan_path)
    content = plan_path.read_text().lower()

    # Check for completion indicators
    completion_keywords = ["completed", "done", "implemented", "finished"]
    has_completion_keywords = any(kw in content for kw in completion_keywords)

    # Find related commits
    commits = find_commits_after_date(created_date, ["*.py", "*.md"])

    # Heuristics
    if commits and has_completion_keywords:
        # Likely completed
        latest_commit = commits[0]
        return "completed", latest_commit
    elif created_date < datetime.now().replace(day=1):
        # Old plan, probably abandoned
        return "abandoned", None
    else:
        # Recent or ambiguous, keep pending
        return "pending", None

def migrate_plan(plan_path: Path, manager) -> bool:
    """Migrate a single plan to new format."""
    status, commit_hash = infer_plan_status(plan_path)

    # Read original content
    content = plan_path.read_text()

    # Extract metadata from HTML comments
    tsk_match = re.search(r'<!-- TSK:\s*([^\n]+) -->', content)
    tsk_id = tsk_match.group(1) if tsk_match else None

    created_match = re.search(r'<!-- Generated:\s*([^\n]+) -->', content)
    created_at = created_match.group(1) if created_match else datetime.now().isoformat()

    # Generate YAML frontmatter
    yaml_header = f"""---
status: {status}
created_at: {created_at}
created_by_session: legacy_migration
linked_tsk: {tsk_id}
completed_at: {datetime.now().isoformat() if status == "completed" else None}
implementing_commit: {commit_hash}
archived_at: {datetime.now().isoformat()}
archive_path: P:/.speckit/plans/completed/shimmying-inventing-wombat.md
---

"""

    # Write new content
    new_content = yaml_header + content

    # Archive to appropriate directory
    if status == "completed":
        new_path = manager.archive_plan(
            plan_path,
            status="completed",
            commit_hash=commit_hash
        )
    elif status == "abandoned":
        new_path = manager.archive_plan(
            plan_path,
            status="abandoned",
            commit_hash=None
        )
    else:
        new_path = plan_path  # Stay in active/

    # Write updated content to new path
    new_path.write_text(new_content)

    # Remove old file
    if new_path != plan_path:
        plan_path.unlink()

    return True

def main():
    """Migrate all existing plans."""
    from plan_lifecycle_manager import PlanLifecycleManager

    plans_dir = Path.home() / ".claude" / "plans"
    manager = PlanLifecycleManager(plans_dir)

    # Find all plan files (excluding new structure)
    plan_files = []
    for plan_file in plans_dir.glob("plan-*.md"):
        if "active" not in str(plan_file) and "completed" not in str(plan_file):
            plan_files.append(plan_file)

    print(f"Found {len(plan_files)} legacy plans to migrate")

    for plan_file in plan_files:
        print(f"Migrating {plan_file.name}...")
        try:
            migrate_plan(plan_file, manager)
            print(f"  ✓ Migrated")
        except Exception as e:
            print(f"  ✗ Failed: {e}")

if __name__ == "__main__":
    main()
```

### Phase 6: CLI Tool for Manual Plan Management

**File: `P:\__csf.nip\src\commands\plan_cleanup.py`** (CREATE)

**Commands:**
- `python -m plan_cleanup list` - Show all plans with status
- `python -m plan_cleanup complete <id>` - Manually mark as completed
- `python -m plan_cleanup abandon <id>` - Manually mark as abandoned
- `python -m plan_cleanup migrate` - Run migration script

## Implementation Order

### Week 1: Core
1. ✅ Create `plan_lifecycle_manager.py`
2. ✅ Update `plan_redirector.py` (YAML + active/)
3. ✅ Create directory structure

### Week 2: Automation
4. ✅ Create `on_exit_plan_mode.py` hook
5. ✅ Create `plan_status_detector.py` hook
6. ✅ Test end-to-end workflow

### Week 3: Migration
7. ✅ Create `migrate_plan_files.py`
8. ✅ Run migration on existing plans
9. ✅ Verify and cleanup

### Week 4: Polish
10. ✅ Create `plan_cleanup.py` CLI
11. ✅ Documentation
12. ✅ Testing and refinement

## Critical Files

| File | Purpose | Action |
|------|---------|--------|
| `P:\__csf.nip\src\utils\plan_lifecycle_manager.py` | Core lifecycle logic | CREATE |
| `P:\.claude\hooks\plan_redirector.py` | Add YAML + active/ redirect | MODIFY |
| `P:\.claude\hooks\on_exit_plan_mode.py` | Prompt for completion | CREATE |
| `P:\.claude\hooks\plan_status_detector.py` | Add status badges | CREATE |
| `P:\__csf.nip\scripts\migrate_plan_files.py` | Migrate existing plans | CREATE |
| `P:\__csf.nip\src\commands\plan_cleanup.py` | Manual CLI tool | CREATE |

## Expected Outcome

**Before (current state):**
```
~/.claude/plans/
├── plan-rich-progress-fix.md  ← Is this done? Unknown!
├── plan-worktree-detection.md ← Still pending? Unknown!
└── plan-auth-system.md        ← Completed when? Unknown!
```

**After (with solution):**
```
~/.claude/plans/
├── active/
│   └── plan-new-feature-20251222.md
│       ✅ YAML shows status: pending
├── completed/
│   ├── plan-rich-progress-fix.md
│   │   ✅ YAML shows status: completed, commit: 76dc213
│   └── plan-worktree-detection.md
│       ✅ YAML shows status: completed, commit: d8906b9
└── abandoned/
    └── plan-deprecated-idea.md
        ✅ YAML shows status: abandoned
```

**AI Behavior:**
- Session resume: Reads plan files, sees status badges
- Completed plans show: ✅ [COMPLETED - ALREADY DONE]
- AI knows NOT to re-implement completed work
- Only pending plans show: ⏳ [PENDING - IMPLEMENT THIS]

## User Choices Applied

✅ **Completion Detection:** Prompt for confirmation on exit
- User gets asked "Was this plan completed? (y/n/a)"
- No automatic archival without user approval

✅ **Existing Plans:** Auto-migrate as completed
- Git history analysis infers completion status
- Likely-completed plans → completed/
- Old/abandoned plans → abandoned/
- Recent/ambiguous → pending in active/
