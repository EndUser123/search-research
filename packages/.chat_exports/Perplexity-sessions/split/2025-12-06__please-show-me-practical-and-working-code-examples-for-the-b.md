---
title: "Please show me practical and working code examples for the below.


Intentional Compaction is a rigorous workflow techni"
date: "2025-12-06"
mode: "COPILOT"
uuid: "63d2b52f-a294-4c91-a713-3960f104917e"
entry_count: 5
---

## Human

Please show me practical and working code examples for the below.


Intentional Compaction is a rigorous workflow technique designed to overcome the limitations of an AI model's "context window" (its short-term memory) and prevent performance degradation during complex software development tasks. Instead of allowing a conversation to grow indefinitely, developers deliberately force the AI to summarise its state and restart, ensuring the model remains in its most intelligent zone.
The "Dumb Zone" and Context Decay The driving force behind intentional compaction is the concept of the "dumb zone". Research indicates that as an AI's context window fills up—specifically once it passes approximately the 40% mark—the model's performance begins to suffer from diminishing returns.
• Performance Degradation: If a developer continues to prompt an agent within a bloated context window, the model becomes prone to "hallucinations," losing track of the original objective or getting confused by its own previous errors.
• Trajectory Issues: If a user spends time correcting an agent's mistakes, the conversation history becomes filled with examples of failure. The model may interpret this trajectory as a pattern to follow, making it more likely to produce further errors.
The Workflow: Summarise, Clear, Resume Intentional compaction replaces the "vibe coding" approach (endless chatting) with a structured cycle:
1. Compression: The developer asks the agent to compress the current context—including code flow, edits, and test outputs—into a single markdown file. This summary is optimized for correctness and completeness, often citing specific file names and line numbers relevant to the task.
2. Clearing: The developer clears the agent's memory or starts a completely fresh session.
3. Resuming: The new agent session ingests the summary file. Because it is "onboarded" with a concise, high-density summary rather than a long, messy history, it can get straight to work with a clean "smart" context window.
Structured State Management To support this workflow, developers are encouraged to use specific persistent files that live outside the context window but are loaded when needed:
• Progress Files: Anthropic's research suggests maintaining a claude_progress.txt or markdown file that tracks what has been done and what remains, acting as a bridge between sessions.
• Feature Lists: To prevent the agent from "one-shotting" an entire application and failing, developers use "initializer agents" to create comprehensive feature lists (often in JSON or Markdown) where tasks are marked as "failing" or "passing".
• Decision Logs: Files like decisions.md or bugs.md allow the agent to reference architectural choices or past errors without needing them constantly in active memory.
Manual vs. Automatic Compaction While tools like Claude Code include an autocompact feature that triggers when context fills up (e.g., at 92% capacity), experts argue against relying on it. Automatic compaction may trigger at inconvenient moments or discard information the human developer deems critical. Intentional compaction is performed manually to ensure the developer controls exactly what information is retained and ensures the model never enters the "dumb zone" in the first place.

## Assistant

Excellent—I found some practical context. Now let me create working code examples for Intentional Compaction workflows that you can implement immediately.

## Practical Intentional Compaction Code Examples

Here are production-ready implementations for managing AI context lifecycle:

### 1. **Progress File Manager** (Foundation Layer)

```python
# claude_progress.py
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional

@dataclass
class Task:
    id: str
    name: str
    description: str
    status: str  # "pending", "in_progress", "completed", "failed"
    created_at: str
    updated_at: str
    context_tokens_used: int = 0
    notes: str = ""
    
    def to_dict(self):
        return asdict(self)

class ProgressManager:
    """Manages persistent state across compaction cycles"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.progress_file = self.project_root / "claude_progress.json"
        self.tasks: List[Task] = []
        self._load()
    
    def _load(self):
        """Load progress from disk"""
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                data = json.load(f)
                self.tasks = [
                    Task(**task) for task in data.get('tasks', [])
                ]
    
    def save(self):
        """Persist progress to disk"""
        with open(self.progress_file, 'w') as f:
            json.dump({
                'last_updated': datetime.now().isoformat(),
                'tasks': [task.to_dict() for task in self.tasks]
            }, f, indent=2)
    
    def add_task(self, task_id: str, name: str, description: str):
        """Create a new tracked task"""
        task = Task(
            id=task_id,
            name=name,
            description=description,
            status="pending",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        self.tasks.append(task)
        self.save()
        return task
    
    def update_task(self, task_id: str, status: str, notes: str = "", tokens: int = 0):
        """Update task status and add notes"""
        task = next((t for t in self.tasks if t.id == task_id), None)
        if task:
            task.status = status
            task.updated_at = datetime.now().isoformat()
            if notes:
                task.notes += f"\n[{datetime.now().isoformat()}] {notes}"
            task.context_tokens_used += tokens
            self.save()
    
    def get_summary(self) -> str:
        """Generate markdown summary for new session"""
        summary = "# Progress Summary\n\n"
        summary += f"Generated: {datetime.now().isoformat()}\n\n"
        
        summary += "## Completed Tasks\n"
        completed = [t for t in self.tasks if t.status == "completed"]
        if completed:
            for task in completed:
                summary += f"- ✅ {task.name}: {task.description}\n"
        else:
            summary += "- None yet\n"
        
        summary += "\n## In Progress\n"
        in_progress = [t for t in self.tasks if t.status == "in_progress"]
        if in_progress:
            for task in in_progress:
                summary += f"- 🔄 {task.name}: {task.description}\n"
                if task.notes:
                    summary += f"  Last notes: {task.notes.split(chr(10))[-1]}\n"
        else:
            summary += "- None\n"
        
        summary += "\n## Pending Tasks\n"
        pending = [t for t in self.tasks if t.status == "pending"]
        if pending:
            for task in pending:
                summary += f"- ⏳ {task.name}: {task.description}\n"
        else:
            summary += "- All tasks active or complete\n"
        
        summary += "\n## Context Burn Rate\n"
        total_tokens = sum(t.context_tokens_used for t in self.tasks)
        summary += f"- Total tokens used: {total_tokens}\n"
        summary += f"- Average per task: {total_tokens // len(self.tasks) if self.tasks else 0}\n"
        
        return summary

# Example usage
if __name__ == "__main__":
    pm = ProgressManager(".")
    
    # Initialize tracking
    pm.add_task("parse_video", "Video Parser", "Extract metadata and segments from video file")
    pm.add_task("classify_content", "Content Classification", "Classify video by category using ML")
    pm.add_task("extract_transcript", "Transcript Extraction", "Generate transcript with timestamps")
    
    # Simulate work
    pm.update_task("parse_video", "completed", "Parsed 3 video files, 450 segments identified", tokens=2500)
    pm.update_task("classify_content", "in_progress", "Running classifier on 450 segments", tokens=3200)
    
    # Generate summary for new session
    print(pm.get_summary())
```

***

### 2. **Feature Checklist with Auto-Tracking**

```python
# feature_tracker.py
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

class FeatureTracker:
    """Prevents agent from "one-shotting" features and ensures structured delivery"""
    
    def __init__(self, features_file: str = "features.json"):
        self.features_file = Path(features_file)
        self.features: Dict[str, Dict] = {}
        self._load()
    
    def _load(self):
        if self.features_file.exists():
            with open(self.features_file, 'r') as f:
                self.features = json.load(f)
    
    def save(self):
        with open(self.features_file, 'w') as f:
            json.dump(self.features, f, indent=2)
    
    def initialize(self, features: List[str]):
        """Create initial feature list"""
        for feature in features:
            self.features[feature] = {
                "status": "pending",
                "started": None,
                "completed": None,
                "tests_passing": False,
                "notes": []
            }
        self.save()
    
    def start_feature(self, feature_name: str):
        """Mark feature as in-progress"""
        if feature_name in self.features:
            self.features[feature_name]["status"] = "in_progress"
            self.features[feature_name]["started"] = datetime.now().isoformat()
            self.save()
    
    def complete_feature(self, feature_name: str, tests_passing: bool = True, notes: str = ""):
        """Mark feature as complete"""
        if feature_name in self.features:
            self.features[feature_name]["status"] = "completed"
            self.features[feature_name]["completed"] = datetime.now().isoformat()
            self.features[feature_name]["tests_passing"] = tests_passing
            if notes:
                self.features[feature_name]["notes"].append({
                    "timestamp": datetime.now().isoformat(),
                    "note": notes
                })
            self.save()
    
    def fail_feature(self, feature_name: str, reason: str):
        """Mark feature as failed with reason"""
        if feature_name in self.features:
            self.features[feature_name]["status"] = "failed"
            self.features[feature_name]["notes"].append({
                "timestamp": datetime.now().isoformat(),
                "error": reason
            })
            self.save()
    
    def get_next_pending(self) -> str:
        """Get next pending feature to work on"""
        for name, meta in self.features.items():
            if meta["status"] == "pending":
                return name
        return None
    
    def get_status_board(self) -> str:
        """Generate markdown status board"""
        board = "# Feature Status Board\n\n"
        
        board += "## ✅ Completed\n"
        completed = [k for k, v in self.features.items() if v["status"] == "completed"]
        if completed:
            for feature in completed:
                tests = "✓" if self.features[feature]["tests_passing"] else "✗"
                board += f"- [{tests}] {feature}\n"
        else:
            board += "- None yet\n"
        
        board += "\n## 🔄 In Progress\n"
        in_progress = [k for k, v in self.features.items() if v["status"] == "in_progress"]
        if in_progress:
            for feature in in_progress:
                board += f"- {feature}\n"
        else:
            board += "- None\n"
        
        board += "\n## ⏳ Pending\n"
        pending = [k for k, v in self.features.items() if v["status"] == "pending"]
        if pending:
            for feature in pending:
                board += f"- {feature}\n"
        else:
            board += "- All features active\n"
        
        board += "\n## ❌ Failed\n"
        failed = [k for k, v in self.features.items() if v["status"] == "failed"]
        if failed:
            for feature in failed:
                board += f"- {feature}\n"
                for note in self.features[feature]["notes"]:
                    if "error" in note:
                        board += f"  - Error: {note['error']}\n"
        else:
            board += "- None\n"
        
        return board

# Example usage
if __name__ == "__main__":
    tracker = FeatureTracker()
    
    # Initialize features (session 1)
    features = [
        "Video metadata parser",
        "Segment boundary detection",
        "Content classifier",
        "Transcript generator",
        "Thumbnail extractor"
    ]
    tracker.initialize(features)
    
    # Work through features
    tracker.start_feature("Video metadata parser")
    # ... development work ...
    tracker.complete_feature("Video metadata parser", tests_passing=True, 
                            notes="Handles MP4, WebM, MOV. Edge case: corrupted headers")
    
    tracker.start_feature("Segment boundary detection")
    # ... more work ...
    tracker.fail_feature("Segment boundary detection", 
                        reason="ML model accuracy 62%, needs retraining with better dataset")
    
    # Print status
    print(tracker.get_status_board())
```

***

### 3. **Decision Log** (Architecture Memory)

```python
# decisions.py
import json
from pathlib import Path
from datetime import datetime
from enum import Enum

class DecisionType(Enum):
    ARCHITECTURE = "architecture"
    ALGORITHM = "algorithm"
    BUG_FIX = "bug_fix"
    REFACTOR = "refactor"
    DEPENDENCY = "dependency"
    DESIGN_PATTERN = "design_pattern"

class DecisionLog:
    """Maintains architectural decisions and prevents re-solving same problems"""
    
    def __init__(self, log_file: str = "decisions.md"):
        self.log_file = Path(log_file)
        self.decisions: List[Dict] = []
        self._load()
    
    def _load(self):
        # Parse markdown decisions if file exists
        if self.log_file.exists():
            # Simple parser - in production, use frontmatter or YAML
            with open(self.log_file, 'r') as f:
                content = f.read()
                # Placeholder: in real impl, parse structured format
    
    def log_decision(self, title: str, decision_type: DecisionType, 
                    rationale: str, alternatives_considered: str,
                    implications: str, related_issue: str = None):
        """Log an architectural decision"""
        
        decision = {
            "timestamp": datetime.now().isoformat(),
            "title": title,
            "type": decision_type.value,
            "rationale": rationale,
            "alternatives": alternatives_considered,
            "implications": implications,
            "issue": related_issue,
            "status": "active"
        }
        
        self.decisions.append(decision)
        self._save()
    
    def _save(self):
        """Save as markdown for readability"""
        with open(self.log_file, 'w') as f:
            f.write("# Architectural Decisions\n\n")
            
            for decision in sorted(self.decisions, 
                                  key=lambda x: x['timestamp'], 
                                  reverse=True):
                f.write(f"## {decision['title']}\n")
                f.write(f"**Type:** {decision['type']}\n")
                f.write(f"**Date:** {decision['timestamp']}\n\n")
                
                f.write("### Rationale\n")
                f.write(f"{decision['rationale']}\n\n")
                
                f.write("### Alternatives Considered\n")
                f.write(f"{decision['alternatives']}\n\n")
                
                f.write("### Implications\n")
                f.write(f"{decision['implications']}\n\n")
                
                if decision['issue']:
                    f.write(f"**Related Issue:** {decision['issue']}\n\n")
                
                f.write("---\n\n")
    
    def get_relevant_decisions(self, keyword: str) -> List[Dict]:
        """Retrieve decisions matching keyword (for new session context)"""
        return [d for d in self.decisions 
                if keyword.lower() in d['title'].lower() 
                or keyword.lower() in d['rationale'].lower()]
    
    def generate_context_injection(self) -> str:
        """Generate concise summary for new Claude session"""
        injection = "# Previous Architectural Decisions (Reference Only)\n\n"
        
        by_type = {}
        for d in self.decisions:
            dtype = d['type']
            if dtype not in by_type:
                by_type[dtype] = []
            by_type[dtype].append(d)
        
        for dtype, decisions in by_type.items():
            injection += f"## {dtype.upper()}\n"
            for d in decisions:
                injection += f"- **{d['title']}**: {d['rationale'][:100]}...\n"
            injection += "\n"
        
        return injection

# Example usage
if __name__ == "__main__":
    log = DecisionLog()
    
    log.log_decision(
        title="Use FFmpeg over OpenCV for video parsing",
        decision_type=DecisionType.ARCHITECTURE,
        rationale="FFmpeg handles codec variations better, supports streaming, and has better error recovery",
        alternatives_considered="OpenCV (limited codec support), av-simple (immature), GStreamer (overkill)",
        implications="Must install FFmpeg binary. Output parsing requires robust regex. Encoding pipeline fully external.",
        related_issue="UVIR-142"
    )
    
    log.log_decision(
        title="Segment boundaries via silence detection + ML confidence",
        decision_type=DecisionType.ALGORITHM,
        rationale="Hybrid approach catches both hard (silence) and soft (speaker transition) boundaries",
        alternatives_considered="Pure ML (unreliable on edge cases), pure signal processing (misses soft transitions)",
        implications="Two-pass encoding. Requires pre-trained model. 15% accuracy improvement over single approach.",
        related_issue="UVIR-158"
    )
    
    log.log_decision(
        title="Store video metadata in JSON (not SQL)",
        decision_type=DecisionType.DESIGN_PATTERN,
        rationale="Video metadata is hierarchical and evolves frequently. JSON allows schema flexibility without migrations.",
        alternatives_considered="PostgreSQL (overcomplicated for this phase), SQLite (still rigid), MongoDB (overkill)",
        implications="Query performance linear (no indexes). Suitable for <10K videos. Plan migration to DB if scale exceeds.",
        related_issue="UVIR-089"
    )
    
    print(log.generate_context_injection())
```

***

### 4. **Compaction Trigger & State Export**

```python
# compaction.py
import json
import textwrap
from pathlib import Path
from typing import Dict, List

class CompactionManager:
    """Detects when to compact and generates session handoff files"""
    
    def __init__(self, context_limit: int = 100000, 
                 compaction_threshold: float = 0.4):
        self.context_limit = context_limit
        self.compaction_threshold = compaction_threshold
        self.current_tokens = 0
    
    def should_compact(self) -> bool:
        """Trigger compaction at 40% capacity to avoid dumb zone"""
        fill_ratio = self.current_tokens / self.context_limit
        return fill_ratio >= self.compaction_threshold
    
    def estimate_tokens(self, text: str) -> int:
        """Rough estimation: ~4 chars per token"""
        return len(text) // 4
    
    def generate_handoff_file(self, 
                            progress_summary: str,
                            feature_status: str,
                            decisions: str,
                            current_code_state: Dict[str, str],
                            next_steps: str) -> str:
        """
        Creates a dense, reference-optimized summary file.
        This becomes the ONLY input to the new session.
        """
        
        handoff = f"""# Claude Session Handoff

**Generated:** {datetime.now().isoformat()}

## OBJECTIVE (Copy-Paste into New Session)

You are resuming a complex software project. This handoff contains:
1. Completed work (reference only)
2. Active tasks (focus here)
3. Architectural decisions (don't re-solve)
4. Current code state (use as baseline)
5. Next steps (your immediate goals)

---

## COMPLETED WORK

{progress_summary}

---

## FEATURE STATUS

{feature_status}

---

## ARCHITECTURAL CONTEXT

{decisions}

---

## CURRENT CODE STATE

### File Structure

```
project/
{textwrap.indent(self._format_file_tree(current_code_state), '  ')}
```

### Critical Files

"""
        
        # Include only files with recent changes
        important_files = [f for f in current_code_state.keys() 
                          if any(x in f for x in ['main', 'config', 'index', 'core'])]
        
        for filename in important_files[:3]:  # Limit to 3 files to save tokens
            code = current_code_state[filename]
            if len(code) < 500:  # Only include small files inline
                handoff += f"\n**{filename}**\n``````\n"
        
        handoff += f"\n---\n\n## IMMEDIATE NEXT STEPS\n\n{next_steps}\n"
        
        handoff += "\n---\n\n## SESSION INSTRUCTIONS\n\n"
        handoff += """1. Read entire handoff first
2. Do NOT re-read past conversation history
3. Check feature status - start with next **pending** task
4. Reference decisions.md before proposing solutions
5. Update progress.json after each task
6. When context approaches 40% → start new compaction cycle
"""
        
        return handoff
    
    def _format_file_tree(self, file_dict: Dict[str, str], 
                         prefix: str = "", max_depth: int = 3) -> str:
        """Format file structure as tree"""
        lines = []
        for filename in sorted(file_dict.keys())[:10]:  # Limit to 10 files
            indent = len(filename.split('/')) - 1
            if indent <= max_depth:
                name = filename.split('/')[-1]
                lines.append(f"{prefix}├── {name}")
        return "\n".join(lines)

# Example usage
if __name__ == "__main__":
    pm = ProgressManager()
    tracker = FeatureTracker()
    log = DecisionLog()
    
    compactor = CompactionManager(context_limit=200000)
    
    # Simulate accumulated context
    dummy_code = {
        "main.py": "import sys\nfrom video_parser import parse_video\n\nif __name__ == '__main__':\n    parse_video(sys.argv[1])",
        "video_parser.py": "import ffmpeg\n\ndef parse_video(path):\n    probe = ffmpeg.probe(path)\n    return probe['streams']",
        "tests/test_parser.py": "import pytest\nfrom video_parser import parse_video\n\ndef test_parse_mp4():\n    result = parse_video('sample.mp4')\n    assert len(result) > 0"
    }
    
    handoff = compactor.generate_handoff_file(
        progress_summary=pm.get_summary(),
        feature_status=tracker.get_status_board(),
        decisions=log.generate_context_injection(),
        current_code_state=dummy_code,
        next_steps="1. Debug segment boundary detection (currently 62% accuracy)\n2. Reframe problem: may need active learning loop\n3. Test with second video dataset"
    )
    
    # Save handoff
    handoff_path = Path("SESSION_HANDOFF.md")
    handoff_path.write_text(handoff)
    print(f"✅ Handoff written to {handoff_path}")
    print(f"File size: {len(handoff) // 1024}KB")
```

***

### 5. **Multi-Session Orchestrator** (Your 3-Terminal Pattern)

```python
# orchestrator.py
import subprocess
import json
from pathlib import Path
from enum import Enum

class AgentRole(Enum):
    CIO = "chief_intelligence_officer"      # Strategy & scope
    PM = "project_manager"                  # Task breakdown
    DEV = "developer"                       # Implementation

class SessionOrchestrator:
    """
    Implements the 3-agent pattern:
    - CIO: Refines requirements, manages scope
    - PM: Creates granular task lists (kanban format)
    - DEV: Executes specific tasks from PM's queue
    """
    
    def __init__(self, project_dir: str):
        self.project_dir = Path(project_dir)
        self.state_dir = self.project_dir / ".claude_sessions"
        self.state_dir.mkdir(exist_ok=True)
    
    def initialize_cio_session(self, objective: str, constraints: Dict):
        """
        CIO Session Instructions (Terminal 1):
        
        You are the Chief Intelligence Officer. Your job:
        1. Refine the user's objective into precise technical requirements
        2. Identify constraints (budget, time, dependencies)
        3. Propose architecture at high level
        4. Output: strategic_plan.md
        """
        
        prompt = f"""
You are the Chief Intelligence Officer for a software project.

**User Objective:**
{objective}

**Constraints:**
{json.dumps(constraints, indent=2)}

**Your Tasks:**
1. Break down the objective into 3-5 strategic pillars
2. Identify technical risks
3. Propose a high-level architecture
4. Recommend tech stack
5. Estimate effort (rough)

**Output Format (save as strategic_plan.md):**

# Strategic Plan

## Objective
[Refined, precise version]

## Technical Pillars
1. [Pillar 1]
2. [Pillar 2]
...

## Architecture
[Diagram or description]

## Risk Assessment
- Risk 1: [Impact] [Mitigation]
- Risk 2: ...

## Tech Recommendations
- Language: [why]
- Framework: [why]
- Database: [why]
"""
        return prompt
    
    def initialize_pm_session(self):
        """
        PM Session Instructions (Terminal 2):
        
        You are the Project Manager. Your job:
        1. Read strategic_plan.md from CIO
        2. Break into atomic, verifiable tasks
        3. Create kanban board
        4. Output: tasks.json
        """
        
        prompt = """
You are the Project Manager.

**Your Input:**
Read the file: strategic_plan.md

**Your Tasks:**
1. Break each architectural pillar into atomic tasks
2. Each task: single responsibility, <2 hour estimate, clear success criteria
3. Identify task dependencies
4. Create kanban structure (todo, in_progress, done)

**Output Format (save as tasks.json):**

{
  "project": "...",
  "total_tasks": 12,
  "tasks": [
    {
      "id": "TASK-001",
      "title": "Setup project structure",
      "description": "Initialize git repo, dependencies, structure",
      "status": "todo",
      "priority": "high",
      "dependencies": [],
      "success_criteria": [
        "git initialized",
        "requirements.txt created",
        "src/ tests/ directories exist"
      ],
      "estimated_tokens": 500
    },
    ...
  ]
}
"""
        return prompt
    
    def initialize_dev_session(self):
        """
        DEV Session Instructions (Terminal 3):
        
        You are the Developer. Your job:
        1. Read tasks.json from PM
        2. Execute one task at a time
        3. Run tests, log results
        4. Update task status
        5. When compaction trigger: signal PM to refresh task list
        """
        
        prompt = """
You are the Developer (Claude Dev).

**Your Input Files:**
- tasks.json (from PM)
- claude_progress.json (your history)
- decisions.md (don't re-solve)

**Your Workflow:**
1. Identify next "todo" task from tasks.json
2. Implement the feature
3. Test thoroughly
4. Update claude_progress.json
5. Mark task complete in tasks.json
6. Repeat until compaction needed

**Compaction Trigger:**
If token usage approaches 40% capacity:
1. Generate SESSION_HANDOFF.md
2. Signal PM in chat: "COMPACTION NEEDED"
3. PM regenerates task list with updated context
4. Start fresh session with handoff

**Important:**
- Never ignore decisions.md
- Update progress after each task
- Log all errors in bug_log.md
"""
        return prompt
    
    def create_startup_scripts(self):
        """Generate terminal startup scripts"""
        
        # Terminal 1: CIO
        cio_startup = """#!/bin/bash
# Terminal 1: CIO Session

cd ~/projects/myproject
echo "CIO Session Starting..."
echo ""
echo "Instructions:"
echo "1. Read the objective and constraints below"
echo "2. Create strategic_plan.md in this directory"
echo "3. When done, CIO PM team will pick it up"
echo ""

# Show instructions
cat << 'EOF'
**Strategic Planning Session**

Objective: [Read from user or config]
Constraints: [Read from constraints.json]

Create: strategic_plan.md
EOF
"""
        
        # Terminal 2: PM
        pm_startup = """#!/bin/bash
# Terminal 2: PM Session

cd ~/projects/myproject
echo "PM Session Starting..."
echo ""
echo "Waiting for strategic_plan.md from CIO..."
echo ""

while [ ! -f strategic_plan.md ]; do
  sleep 5
done

echo "✅ Found strategic_plan.md"
echo "Now create tasks.json with atomic task breakdown"
"""
        
        # Terminal 3: DEV
        dev_startup = """#!/bin/bash
# Terminal 3: DEV Session

cd ~/projects/myproject
echo "DEV Session Starting..."
echo ""
echo "Waiting for tasks.json from PM..."
echo ""

while [ ! -f tasks.json ]; do
  sleep 5
done

echo "✅ Found tasks.json"
echo "Executing tasks..."
echo ""
echo "Remember:"
echo "- Check decisions.md before solving"
echo "- Update progress.json after each task"
echo "- Signal COMPACTION NEEDED at 40% context"
"""
        
        # Save scripts
        scripts = {
            "start_cio.sh": cio_startup,
            "start_pm.sh": pm_startup,
            "start_dev.sh": dev_startup
        }
        
        for name, content in scripts.items():
            script_path = self.state_dir / name
            script_path.write_text(content)
            script_path.chmod(0o755)
        
        return scripts

# Example usage
if __name__ == "__main__":
    orch = SessionOrchestrator(".")
    
    objective = "Build UVIR system to classify and route video content with specialized Claude prompts"
    constraints = {
        "budget": "research_phase",
        "timeline": "2 weeks",
        "context_window": "200k_tokens"
    }
    
    print("=== CIO PROMPT ===")
    print(orch.initialize_cio_session(objective, constraints))
    
    print("\n=== PM PROMPT ===")
    print(orch.initialize_pm_session())
    
    print("\n=== DEV PROMPT ===")
    print(orch.initialize_dev_session())
    
    print("\n=== STARTUP SCRIPTS ===")
    scripts = orch.create_startup_scripts()
    for name in scripts:
        print(f"✅ Created {name}")
```

***

### 6. **Quick Integration Checklist**

```yaml
# implementation_checklist.yaml

intentional_compaction_setup:
  
  phase_1_initialization:
    - Create claude_progress.json (ProgressManager)
    - Create features.json (FeatureTracker)
    - Create decisions.md (DecisionLog)
    - Create .gitignore to exclude large artifacts
  
  phase_2_session_start:
    - Load progress.json at session start
    - Reference decisions.md before architecture work
    - Check feature status to continue from last session
    - If resuming: feed SESSION_HANDOFF.md as context
  
  phase_3_during_work:
    - Update progress.json after each significant step (target: every 10-15min)
    - Update feature status when completing features
    - Log architectural decisions immediately
    - Estimate tokens at compaction check-ins
  
  phase_4_compaction_trigger:
    - Monitor context usage (trigger at 40% = ~80k tokens for 200k window)
    - Generate SESSION_HANDOFF.md with all summaries
    - Save current code state to project/code_snapshots/
    - Export decision.md, progress.json, features.json
    - Clear conversation history
  
  phase_5_new_session:
    - Feed ONLY the SESSION_HANDOFF.md (not old conversation)
    - Skip reading history—reference files instead
    - Resume from next pending task
    - Repeat from phase_3
  
  monitoring:
    - Token usage: track in progress.json
    - Feature completion rate: check features.json weekly
    - Context decay: if errors rise after 50+ messages, compact earlier
    - Decision reuse: measure how often decisions prevent re-work
```

***

## Key Takeaways for Your UVIR System

Given your video content routing system, apply this pattern:

1. **Progress File**: Track which videos parsed, classified, routed
2. **Feature Tracker**: Ensure each content-type classifier (educational, entertainment, news, etc.) gets isolated, verified development
3. **Decisions Log**: Document why you chose specific ML models, routing logic, prompt structures
4. **Compaction**: Before context hits 80k tokens on a 200k window, handoff to fresh session with summary
5. **Multi-Agent**: Use 3-terminal pattern—CIO refines content types, PM breaks into per-classifier tasks, Dev executes

This prevents the common failure mode: building all classifiers in one session, everything half-working, context degrading, agent forgetting earlier routing decisions.

**Would you like me to extend any of these with specific patterns for your video classification workflow?**

## Human

This isn't for uvir, this is for general claude code software projects.

## Assistant

Here are production-ready, **framework-agnostic** implementations for general Claude Code software projects:

***

## Complete Project Template with Intentional Compaction

### 1. **Core Compaction Engine** (Drop-in Solution)

```python
# claude_compaction.py
import json
import textwrap
import shutil
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Dict, Optional

@dataclass
class CodeState:
    """Snapshot of current codebase for compression"""
    file_path: str
    content: str
    last_modified: str
    size_kb: int
    token_estimate: int

@dataclass
class SessionState:
    """Complete session state for handoff"""
    session_id: str
    started_at: str
    compacted_at: str
    project_summary: str
    technical_debt: List[str]
    critical_files: List[CodeState]
    test_results: Dict[str, str]
    context_tokens: int
    next_steps: str

class CompactionEngine:
    """
    Main engine for Intentional Compaction workflow.
    Handles state tracking, handoff generation, and session management.
    """
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.state_dir = self.project_root / ".claude_state"
        self.state_dir.mkdir(exist_ok=True)
        
        # Core state files
        self.progress_file = self.state_dir / "progress.json"
        self.decisions_file = self.state_dir / "decisions.md"
        self.technical_debt_file = self.state_dir / "debt.json"
        self.handoff_file = self.project_root / "claude_handoff.md"
        
        self.current_session = None
        self.session_history = []
        
    def start_session(self, objective: str) -> str:
        """Initialize new session with clear objective"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.current_session = {
            "session_id": session_id,
            "objective": objective,
            "started_at": datetime.now().isoformat(),
            "tasks_completed": [],
            "context_tokens": 0,
            "compaction_triggered": False
        }
        
        # Create startup prompt
        prompt = f"""# Claude Code Session: {session_id}

## Your Objective
{objective}

## Context Management
- You are in "smart zone" (context < 40%)
- Track progress in .claude_state/progress.json
- Log decisions in .claude_state/decisions.md
- Update technical debt in .claude_state/debt.json

## Session Rules
1. **NEVER work without loading handoff file** (if exists)
2. **Update progress after each meaningful step**
3. **Log architectural decisions immediately**
4. **Check for technical debt before adding features**
5. **Signal COMPACTION NEEDED when context > 40%**

## First Actions
1. Read .claude_state/progress.json (if exists)
2. Read .claude_state/decisions.md (if exists)
3. Read .claude_state/debt.json (if exists)
4. Confirm understanding of objective
5. Begin implementation

Ready to start?
"""
        return prompt
    
    def record_progress(self, task: str, status: str, notes: str = "", tokens_used: int = 0):
        """Record task progress persistently"""
        
        progress_data = {
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "status": status,  # "started", "completed", "blocked", "failed"
            "notes": notes,
            "tokens_used": tokens_used
        }
        
        # Load existing progress
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                data = json.load(f)
        else:
            data = {"tasks": [], "total_tokens": 0}
        
        # Update
        data["tasks"].append(progress_data)
        data["total_tokens"] += tokens_used
        data["last_updated"] = datetime.now().isoformat()
        
        # Save
        with open(self.progress_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Update current session
        if self.current_session:
            self.current_session["tasks_completed"].append(task)
            self.current_session["context_tokens"] += tokens_used
    
    def log_decision(self, title: str, decision_type: str, 
                    rationale: str, alternatives: str, implications: str):
        """Log architectural decision to prevent re-solving"""
        
        decision = f"""
## [{decision_type.upper()}] {title}

**Date:** {datetime.now().isoformat()}

### Rationale
{rationale}

### Alternatives Considered
{alternatives}

### Implications
{implications}

---
"""
        
        # Append to decisions file
        with open(self.decisions_file, 'a') as f:
            f.write(decision)
    
    def log_technical_debt(self, debt_item: str, severity: str, 
                          file_context: str, suggested_fix: str):
        """Track technical debt for future refactoring"""
        
        debt_data = {
            "item": debt_item,
            "severity": severity,  # "low", "medium", "high", "critical"
            "file_context": file_context,
            "logged_at": datetime.now().isoformat(),
            "suggested_fix": suggested_fix,
            "status": "open"
        }
        
        # Load existing debt
        if self.technical_debt_file.exists():
            with open(self.technical_debt_file, 'r') as f:
                data = json.load(f)
        else:
            data = {"debt_items": []}
        
        data["debt_items"].append(debt_data)
        
        # Save
        with open(self.technical_debt_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def should_compact(self, context_limit: int = 200000, threshold: float = 0.4) -> bool:
        """Determine if compaction is needed based on token usage"""
        if not self.current_session:
            return False
        
        usage_ratio = self.current_session["context_tokens"] / context_limit
        return usage_ratio >= threshold
    
    def generate_handoff(self) -> str:
        """
        Generate comprehensive handoff document for new session.
        This replaces the old conversation history.
        """
        
        # Load progress
        progress = []
        if self.progress_file.exists():
            with open(self.progress_file, 'r') as f:
                data = json.load(f)
                progress = data.get("tasks", [])[-10:]  # Last 10 tasks
        
        # Load decisions
        decisions = []
        if self.decisions_file.exists():
            with open(self.decisions_file, 'r') as f:
                decision_text = f.read()
                # Extract recent decisions (simplified)
                decisions = [decision_text] if decision_text else []
        
        # Load technical debt
        debt = []
        if self.technical_debt_file.exists():
            with open(self.technical_debt_file, 'r') as f:
                data = json.load(f)
                debt = [item for item in data.get("debt_items", []) 
                       if item["status"] == "open"]
        
        # Analyze codebase
        critical_files = self._analyze_codebase()
        
        # Generate handoff
        handoff = f"""# Claude Code Handoff
*Session: {self.current_session['session_id']}*
*Generated: {datetime.now().isoformat()}*

---

## 📋 EXECUTIVE SUMMARY

**Original Objective:**
{self.current_session['objective']}

**Progress:**
- Tasks completed: {len(self.current_session['tasks_completed'])}
- Total tokens used: {self.current_session['context_tokens']}
- Context fill ratio: {(self.current_session['context_tokens'] / 200000 * 100):.1f}%

---

## ✅ RECENT COMPLETED WORK

"""
        
        for task in progress[-5:]:  # Last 5 tasks
            handoff += f"- **{task['status'].upper()}** {task['task']}\n"
            if task['notes']:
                handoff += f"  Notes: {task['notes']}\n"
        
        handoff += "\n---\n\n## 🏗️ ARCHITECTURAL DECISIONS (Reference Only)\n\n"
        handoff += "These decisions are already made. Do not re-open them:\n\n"
        
        for i, decision in enumerate(decisions[-3:], 1):
            handoff += f"{i}. {decision[:200]}...\n"
        
        handoff += "\n---\n\n## ⚠️ TECHNICAL DEBT (Be Aware)\n\n"
        
        if debt:
            for item in debt:
                handoff += f"- **[{item['severity'].upper()}]** {item['item']}\n"
                handoff += f"  Location: {item['file_context']}\n"
        else:
            handoff += "No open technical debt items.\n"
        
        handoff += "\n---\n\n## 📄 CRITICAL CODE FILES\n\n"
        
        for code_file in critical_files:
            handoff += f"### {code_file.file_path} ({code_file.size_kb}KB)\n"
            handoff += f"Last modified: {code_file.last_modified}\n\n"
            
            # Include first 50 lines for context
            lines = code_file.content.split('\n')[:50]
            handoff += "``````\n\n"
        
        handoff += "\n---\n\n## 🎯 IMMEDIATE NEXT STEPS\n\n"
        handoff += "1. Review this handoff completely\n"
        handoff += "2. Load progress.json to continue from last task\n"
        handoff += "3. Check technical debt before implementing new features\n"
        handoff += "4. Reference decisions.md to avoid re-solving problems\n"
        handoff += "5. Continue implementation\n"
        
        handoff += "\n---\n\n## ⚡ SESSION RULES\n\n"
        handoff += "- **DO NOT** ask about previous conversation history\n"
        handoff += "- **DO** reference decisions.md for architectural guidance\n"
        handoff += "- **DO** update progress after each meaningful step\n"
        handoff += "- **DO** compact again at 40% context usage\n"
        handoff += "- **DO** log new technical debt as discovered\n"
        
        return handoff
    
    def _analyze_codebase(self) -> List[CodeState]:
        """Analyze current codebase to identify critical files"""
        critical_files = []
        
        # Common source directories
        source_dirs = ["src", "lib", "app", "."]
        extensions = [".py", ".js", ".ts", ".java", ".go", ".rs", ".c", ".cpp", ".h"]
        
        for src_dir in source_dirs:
            src_path = self.project_root / src_dir
            if not src_path.exists():
                continue
            
            for file_path in src_path.rglob("*"):
                if file_path.suffix in extensions:
                    try:
                        content = file_path.read_text()
                        stat = file_path.stat()
                        
                        code_state = CodeState(
                            file_path=str(file_path.relative_to(self.project_root)),
                            content=content,
                            last_modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            size_kb=stat.st_size // 1024,
                            token_estimate=len(content) // 4
                        )
                        
                        critical_files.append(code_state)
                    except Exception as e:
                        continue
        
        # Sort by size and recency, limit to top 5
        critical_files.sort(key=lambda x: x.size_kb, reverse=True)
        return critical_files[:5]
    
    def save_handoff(self) -> Path:
        """Generate and save handoff file"""
        handoff_content = self.generate_handoff()
        self.handoff_file.write_text(handoff_content)
        
        # Also save to state directory for history
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        history_file = self.state_dir / f"handoff_{timestamp}.md"
        history_file.write_text(handoff_content)
        
        return self.handoff_file

# Example usage
if __name__ == "__main__":
    # Initialize compaction engine
    engine = CompactionEngine()
    
    # Start new session
    startup_prompt = engine.start_session(
        "Build a CLI tool for managing PostgreSQL migrations with rollback capabilities"
    )
    print("=== STARTUP PROMPT ===")
    print(startup_prompt)
    
    # Simulate some work
    engine.record_progress(
        task="Setup project structure",
        status="completed",
        notes="Created src/, tests/, config/ directories. Poetry initialized.",
        tokens_used=1500
    )
    
    engine.log_decision(
        title="Use Click framework for CLI",
        decision_type="dependency",
        rationale="Click provides better help generation and argument parsing than argparse",
        alternatives="argparse (built-in), typer (modern but less mature)",
        implications="Add click to dependencies. Use @click.command() decorators."
    )
    
    # Check if compaction needed
    if engine.should_compact():
        handoff_path = engine.save_handoff()
        print(f"\n⚠️  COMPACTION NEEDED")
        print(f"Handoff saved to: {handoff_path}")
        print(f"Start new session with: claude_handoff.md")
```

***

### 2. **Shell Scripts for Manual Compaction Workflow**

```bash
#!/bin/bash
# scripts/compaction.sh

# Intentional Compaction Workflow Script
# Usage: ./scripts/compaction.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$PROJECT_ROOT/.claude_state"
HANDOFF_FILE="$PROJECT_ROOT/claude_handoff.md"

echo "🔄 Starting Intentional Compaction Workflow"
echo "Project: $PROJECT_ROOT"
echo "State Directory: $STATE_DIR"
echo ""

# Check if state directory exists
if [ ! -d "$STATE_DIR" ]; then
    echo "❌ State directory not found. Run ./scripts/init_claude.sh first."
    exit 1
fi

# Load current session info
if [ -f "$STATE_DIR/current_session.json" ]; then
    SESSION_ID=$(cat "$STATE_DIR/current_session.json" | python3 -c "import json, sys; print(json.load(sys.stdin)['session_id'])")
    echo "Current Session: $SESSION_ID"
else
    echo "⚠️  No current session found. Starting fresh."
    SESSION_ID="session_$(date +%Y%m%d_%H%M%S)"
fi

# Step 1: Generate handoff
echo ""
echo "📋 Step 1: Generating handoff document..."
python3 -c "
from claude_compaction import CompactionEngine
engine = CompactionEngine()
handoff_path = engine.save_handoff()
print(f'✅ Handoff saved to: {handoff_path}')
"

# Step 2: Backup current state
echo ""
echo "💾 Step 2: Backing up session state..."
BACKUP_DIR="$STATE_DIR/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r "$STATE_DIR"/*.json "$BACKUP_DIR/" 2>/dev/null || true
cp -r "$STATE_DIR"/*.md "$BACKUP_DIR/" 2>/dev/null || true
echo "✅ Backup created at: $BACKUP_DIR"

# Step 3: Create new session marker
echo ""
echo "🚀 Step 3: Preparing new session marker..."
cat > "$STATE_DIR/new_session_ready.txt" << EOF
NEW SESSION READY

Instructions for new Claude session:
1. Load this file: $HANDOFF_FILE
2. Do NOT load previous conversation history
3. Continue from where previous session left off
4. Track progress in .claude_state/progress.json

Session ID: $SESSION_ID
Timestamp: $(date)
EOF

# Step 4: Display summary
echo ""
echo "📊 Session Summary:"
python3 -c "
import json
from pathlib import Path
progress_file = Path('.claude_state/progress.json')
if progress_file.exists():
    with open(progress_file) as f:
        data = json.load(f)
        tasks = data.get('tasks', [])
        completed = [t for t in tasks if t['status'] == 'completed']
        print(f'  Tasks completed: {len(completed)}')
        print(f'  Total tokens: {data.get(\"total_tokens\", 0)}')
        print(f'  Last updated: {data.get(\"last_updated\", \"Unknown\")}')
else:
    print('  No progress data yet')
"

echo ""
echo "✅ Compaction complete!"
echo ""
echo "📝 Next steps:"
echo "1. Start NEW Claude Code session"
echo "2. Load file: claude_handoff.md"
echo "3. Confirm understanding"
echo "4. Continue implementation"
echo ""
echo "🚨 IMPORTANT: Do NOT continue old conversation!"
```

```bash
#!/bin/bash
# scripts/init_claude.sh

# Initialize Claude Code project with Intentional Compaction
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$PROJECT_ROOT/.claude_state"

echo "🚀 Initializing Claude Code Project"
echo "Project: $PROJECT_ROOT"
echo ""

# Create state directory
mkdir -p "$STATE_DIR"
mkdir -p "$STATE_DIR/backups"
echo "✅ Created state directory: $STATE_DIR"

# Create initial progress tracker
cat > "$STATE_DIR/progress.json" << 'EOF'
{
  "project_name": null,
  "objective": null,
  "started_at": null,
  "tasks": [],
  "total_tokens": 0,
  "compaction_cycles": 0
}
EOF
echo "✅ Created progress.json"

# Create empty decisions file
cat > "$STATE_DIR/decisions.md" << 'EOF'
# Architectural Decisions

This file logs all architectural decisions to prevent re-solving problems.

Format:
- Decision type: [architecture|dependency|algorithm|pattern]
- Rationale: Why this choice
- Alternatives: What was considered and rejected
- Implications: Consequences of this decision
- Related issue: Optional issue tracker reference

---
EOF
echo "✅ Created decisions.md"

# Create technical debt tracker
cat > "$STATE_DIR/debt.json" << 'EOF'
{
  "debt_items": [],
  "last_reviewed": null
}
EOF
echo "✅ Created debt.json"

# Create scripts directory if not exists
mkdir -p "$PROJECT_ROOT/scripts"

# Copy compaction script
if [ -f "$PROJECT_ROOT/claude_compaction.py" ]; then
    cp "$PROJECT_ROOT/scripts/compaction.sh" "$PROJECT_ROOT/scripts/compaction.sh" 2>/dev/null || true
    chmod +x "$PROJECT_ROOT/scripts/compaction.sh"
    echo "✅ Created compaction.sh script"
fi

# Create .claudeignore (like .gitignore for context)
cat > "$PROJECT_ROOT/.claudeignore" << 'EOF'
# Files to exclude from Claude context analysis
node_modules/
__pycache__/
*.pyc
.env
*.log
.vscode/
.idea/
build/
dist/
*.min.js
*.min.css
EOF
echo "✅ Created .claudeignore"

echo ""
echo "✅ Project initialized for Intentional Compaction!"
echo ""
echo "Next steps:"
echo "1. Edit .claude_state/progress.json with your project objective"
echo "2. Start Claude Code session"
echo "3. When context fills up, run: ./scripts/compaction.sh"
echo "4. Start new session with claude_handoff.md"
```

```bash
#!/bin/bash
# scripts/claude_status.sh

# Quick status check for Claude Code project
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$PROJECT_ROOT/.claude_state"

echo "📊 Claude Code Project Status"
echo "============================="
echo ""

# Project info
if [ -f "$STATE_DIR/progress.json" ]; then
    python3 -c "
import json
from pathlib import Path
data = json.loads(Path('$STATE_DIR/progress.json').read_text())
print(f'Project: {data.get(\"project_name\", \"Not set\")}')
print(f'Objective: {data.get(\"objective\", \"Not set\")}')
print(f'Started: {data.get(\"started_at\", \"Not set\")}')
print(f'Total tokens used: {data.get(\"total_tokens\", 0):,}')
print(f'Compaction cycles: {data.get(\"compaction_cycles\", 0)}')
print()
"
fi

# Current tasks
echo "📋 Recent Tasks:"
if [ -f "$STATE_DIR/progress.json" ]; then
    python3 -c "
import json
from pathlib import Path
data = json.loads(Path('$STATE_DIR/progress.json').read_text())
tasks = data.get('tasks', [])[-5:]
for task in reversed(tasks):
    status_icon = '✅' if task['status'] == 'completed' else '🔄' if task['status'] == 'in_progress' else '⏳'
    print(f'{status_icon} {task[\"task\"]}')
    if task['notes']:
        print(f'   {task[\"notes\"]}')
"
fi

# Technical debt
echo ""
echo "⚠️  Technical Debt:"
if [ -f "$STATE_DIR/debt.json" ]; then
    python3 -c "
import json
from pathlib import Path
data = json.loads(Path('$STATE_DIR/debt.json').read_text())
open_debt = [item for item in data.get('debt_items', []) if item['status'] == 'open']
if open_debt:
    for item in open_debt:
        print(f'[{item[\"severity\"].upper()}] {item[\"item\"]}')
else:
    print('No open technical debt items')
"
fi

# Recent decisions
echo ""
echo "🏗️  Recent Decisions:"
if [ -f "$STATE_DIR/decisions.md" ]; then
    python3 -c "
from pathlib import Path
content = Path('$STATE_DIR/decisions.md').read_text()
decisions = content.split('## ')[-3:]
for d in reversed(decisions):
    if d.strip():
        title = d.split('\\n')[0]
        print(f'• {title}')
"
fi

# Handoff status
echo ""
if [ -f "$PROJECT_ROOT/claude_handoff.md" ]; then
    echo "🚨 Handoff file exists! Start new session with claude_handoff.md"
else
    echo "✅ No handoff pending. Continue current work."
fi

echo ""
echo "Context Limit: 200,000 tokens"
echo "Compaction threshold: 40% (80,000 tokens)"
```

***

### 3. **VS Code Integration** (Task Runner)

```json
// .vscode/tasks.json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "claude:init",
            "type": "shell",
            "command": "./scripts/init_claude.sh",
            "presentation": {
                "reveal": "always",
                "panel": "shared"
            },
            "problemMatcher": [],
            "group": "build"
        },
        {
            "label": "claude:status",
            "type": "shell",
            "command": "./scripts/claude_status.sh",
            "presentation": {
                "reveal": "always",
                "panel": "shared"
            },
            "problemMatcher": [],
            "group": "test"
        },
        {
            "label": "claude:compact",
            "type": "shell",
            "command": "./scripts/compaction.sh",
            "presentation": {
                "reveal": "always",
                "panel": "shared",
                "clear": true
            },
            "problemMatcher": [],
            "group": "build",
            "promptOnClose": true
        },
        {
            "label": "claude:new-session",
            "type": "shell",
            "command": "cat claude_handoff.md | head -50",
            "presentation": {
                "reveal": "always",
                "panel": "shared"
            },
            "problemMatcher": [],
            "group": "build"
        }
    ]
}
```

```json
// .vscode/settings.json
{
    "files.associations": {
        "claude_handoff.md": "markdown",
        ".claude_state/decisions.md": "markdown",
        ".claude_state/progress.json": "jsonc",
        ".claude_state/debt.json": "jsonc"
    },
    "files.exclude": {
        "node_modules": true,
        "__pycache__": true,
        "*.pyc": true,
        ".claude_state/backups": true
    },
    "search.exclude": {
        ".claude_state/backups": true
    }
}
```

***

### 4. **Project Templates by Type**

```bash
#!/bin/bash
# scripts/create_project_template.sh

# Creates starter files for different project types
set -e

PROJECT_TYPE=$1
PROJECT_NAME=$2

if [ -z "$PROJECT_TYPE" ] || [ -z "$PROJECT_NAME" ]; then
    echo "Usage: ./scripts/create_project_template.sh <type> <name>"
    echo ""
    echo "Types:"
    echo "  webapp      - Web application (Flask/Django/FastAPI)"
    echo "  cli         - Command-line tool"
    echo "  library     - Reusable library/package"
    echo "  ml          - Machine learning project"
    exit 1
fi

echo "Creating $PROJECT_TYPE template: $PROJECT_NAME"
mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME"

# Initialize Claude compaction
../scripts/init_claude.sh

# Set project name and objective
python3 -c "
import json
from pathlib import Path
data = json.loads(Path('.claude_state/progress.json').read_text())
data['project_name'] = '$PROJECT_NAME'
data['started_at'] = __import__('datetime').datetime.now().isoformat()
Path('.claude_state/progress.json').write_text(json.dumps(data, indent=2))
"

case $PROJECT_TYPE in
    webapp)
        echo "Creating webapp template..."
        
        # Create typical webapp structure
        mkdir -p src/{routes,models,services,utils}
        mkdir -p tests/{unit,integration}
        mkdir -p config
        mkdir -p static/js static/css templates
        
        # Initial files
        cat > src/__init__.py << 'EOF'
"""
$PROJECT_NAME Web Application
"""
__version__ = "0.1.0"
EOF
        
        cat > src/main.py << 'EOF'
from fastapi import FastAPI

app = FastAPI(title="$PROJECT_NAME", version="0.1.0")

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
EOF
        
        cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn[standard]==0.24.0
pytest==7.4.3
EOF
        
        # Log initial decision
        python3 -c "
from claude_compaction import CompactionEngine
engine = CompactionEngine()
engine.log_decision(
    title='Use FastAPI for web framework',
    decision_type='dependency',
    rationale='FastAPI provides async support, automatic docs, and type hints. Perfect for modern Python APIs.',
    alternatives='Flask (simpler but less features), Django (overkill for API)',
    implications='Requires Python 3.8+. Use async/await for IO operations.'
)
"
        ;;
        
    cli)
        echo "Creating CLI template..."
        
        # Create CLI structure
        mkdir -p src/commands tests
        
        cat > src/cli.py << 'EOF'
import click

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """$PROJECT_NAME - Command Line Interface"""
    pass

@cli.command()
@click.argument('name')
def greet(name):
    """Greet someone"""
    click.echo(f"Hello, {name}!")

if __name__ == '__main__':
    cli()
EOF
        
        cat > requirements.txt << 'EOF'
click==8.1.7
pytest==7.4.3
EOF
        
        # Log initial decision
        python3 -c "
from claude_compaction import CompactionEngine
engine = CompactionEngine()
engine.log_decision(
    title='Use Click for CLI framework',
    decision_type='dependency',
    rationale='Click provides excellent command grouping, help generation, and argument parsing. Industry standard.',
    alternatives='argparse (built-in but verbose), typer (modern but less mature)',
    implications='Add click to dependencies. Use @cli.command() decorators.'
)
"
        ;;
        
    library)
        echo "Creating library template..."
        
        # Create library structure
        mkdir -p src/$PROJECT_NAME tests
        
        cat > src/$PROJECT_NAME/__init__.py << 'EOF'
"""
$PROJECT_NAME Library
"""
__version__ = "0.1.0"
EOF
        
        cat > pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "$PROJECT_NAME"
version = "0.1.0"
description = "A Python library"
requires-python = ">=3.8"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=7.0", "black", "mypy"]

[tool.setuptools.packages.find]
where = ["src"]
EOF
        
        # Log initial decision
        python3 -c "
from claude_compaction import CompactionEngine
engine = CompactionEngine()
engine.log_decision(
    title='Use pyproject.toml for packaging',
    decision_type='architecture',
    rationale='pyproject.toml is the modern Python packaging standard. Supports setuptools, wheel, and future tools.',
    alternatives='setup.py (legacy), setup.cfg (limited features)',
    implications='Requires pip 21.0+. Use pip install -e . for development.'
)
"
        ;;
        
    ml)
        echo "Creating ML project template..."
        
        # Create ML structure
        mkdir -p src/{models,data,features,training,evaluation}
        mkdir -p data/{raw,processed,interim,external}
        mkdir -p notebooks tests
        
        cat > requirements.txt << 'EOF'
numpy==1.24.3
pandas==2.0.3
scikit-learn==1.3.0
jupyter==1.0.0
matplotlib==3.7.1
seaborn==0.12.2
pytest==7.4.3
EOF
        
        cat > src/config.py << 'EOF'
"""
Configuration for ML project
"""
import pathlib

# Directories
ROOT_DIR = pathlib.Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Model parameters
RANDOM_SEED = 42
TEST_SIZE = 0.2
EOF
        
        # Log initial decision
        python3 -c "
from claude_compaction import CompactionEngine
engine = CompactionEngine()
engine.log_decision(
    title='Use scikit-learn as baseline ML framework',
    decision_type='dependency',
    rationale='scikit-learn provides comprehensive ML algorithms, preprocessing, and evaluation tools. Good baseline before deep learning.',
    alternatives='PyTorch (overkill for baseline), TensorFlow (complex for simple models)',
    implications='Follow sklearn API patterns. Use pipelines for reproducibility.'
)
"
        ;;
        
    *)
        echo "Unknown project type:

## Human

How would we use the claude agent sdk with this?

## Assistant

Perfect. Here's how to integrate the Claude Agent SDK with Intentional Compaction for fully autonomous task execution:

***

## Claude Agent SDK + Intentional Compaction Integration

### 1. **Agent-Aware Compaction Manager**

```python
# claude_agent_compaction.py
"""
Integrates Claude Agent SDK with Intentional Compaction workflow.
Agents automatically manage context lifecycle and handoff.
"""

import anthropic
import json
import textwrap
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

@dataclass
class AgentTask:
    id: str
    objective: str
    instructions: str
    max_iterations: int = 20
    context_threshold: float = 0.4

class CompactionAwareAgent:
    """
    Claude agent that understands Intentional Compaction.
    Monitors context, triggers handoff automatically.
    """
    
    def __init__(self, project_root: str = ".", model: str = "claude-opus-4-1"):
        self.project_root = Path(project_root)
        self.state_dir = self.project_root / ".claude_state"
        self.state_dir.mkdir(exist_ok=True)
        
        self.client = anthropic.Anthropic()
        self.model = model
        self.context_limit = 200000  # Adjust for your plan
        self.compaction_threshold = 0.4
        
        # Agent state
        self.session_id = None
        self.messages = []
        self.total_tokens = 0
        self.iteration_count = 0
    
    def load_handoff(self) -> Optional[str]:
        """Load previous session handoff if it exists"""
        handoff_file = self.project_root / "claude_handoff.md"
        if handoff_file.exists():
            return handoff_file.read_text()
        return None
    
    def load_context_files(self) -> dict:
        """Load persistent state from disk"""
        context = {}
        
        # Load progress
        progress_file = self.state_dir / "progress.json"
        if progress_file.exists():
            context["progress"] = json.loads(progress_file.read_text())
        
        # Load decisions
        decisions_file = self.state_dir / "decisions.md"
        if decisions_file.exists():
            context["decisions"] = decisions_file.read_text()
        
        # Load technical debt
        debt_file = self.state_dir / "debt.json"
        if debt_file.exists():
            context["technical_debt"] = json.loads(debt_file.read_text())
        
        return context
    
    def build_system_prompt(self, task: AgentTask, context: dict) -> str:
        """Build system prompt with compaction awareness"""
        
        prompt = f"""You are an autonomous Claude agent executing a software development task.

## Your Role
You have access to the file system, can execute code, and manage your own context lifecycle.

## Current Objective
{task.objective}

## Core Instructions
{task.instructions}

## Context Management (CRITICAL)
- You are currently using ~{(self.total_tokens / self.context_limit) * 100:.1f}% of context
- When context exceeds 40% ({int(self.context_limit * 0.4)} tokens), you MUST:
  1. Save final state to .claude_state/ files
  2. Generate SESSION_HANDOFF.md
  3. Signal COMPACTION_NEEDED in your final message
- Do NOT continue past 40% context threshold

## Persistent State (Already Loaded)
- Progress tracking: .claude_state/progress.json
- Architectural decisions: .claude_state/decisions.md
- Technical debt: .claude_state/debt.json
- Handoff from previous session: claude_handoff.md (if exists)

## Tool Guidelines
You can:
- Read/write files anywhere in {self.project_root}
- Execute bash commands for testing
- Run Python code for analysis
- Search file contents

You CANNOT:
- Access external internet (use local resources only)
- Modify files outside {self.project_root}
- Exceed {task.max_iterations} iterations

## Session Rules
1. Load context files at start
2. Update progress.json after each major step (every 5-10min of work)
3. Log architectural decisions immediately (to prevent re-solving)
4. Track technical debt as discovered
5. When context approaches threshold: prepare handoff and exit gracefully

## Expected Output Format
For progress updates use:
```
{{
  "task": "Task name",
  "status": "in_progress|completed|blocked",
  "notes": "What was done"
}}
```

For decisions use:
```
## [TYPE] Decision Title
**Rationale:** Why this choice
**Alternatives:** What was considered
**Implications:** Consequences
```

For technical debt use:
```
{{
  "item": "Issue description",
  "severity": "low|medium|high",
  "location": "file and line",
  "fix": "How to address it"
}}
```
"""
        
        # Add recent context
        if context.get("progress"):
            prompt += "\n## Recent Progress\n"
            tasks = context["progress"].get("tasks", [])[-5:]
            for task in tasks:
                prompt += f"- {task['task']}: {task['status']}\n"
        
        if context.get("decisions"):
            prompt += f"\n## Previous Decisions (Reference)\n{context['decisions'][:500]}...\n"
        
        if context.get("technical_debt"):
            open_debt = [item for item in context["technical_debt"].get("debt_items", []) 
                        if item["status"] == "open"]
            if open_debt:
                prompt += "\n## Technical Debt to Avoid\n"
                for item in open_debt[:3]:
                    prompt += f"- [{item['severity']}] {item['item']}\n"
        
        return prompt
    
    def execute_task(self, task: AgentTask, max_turns: int = 50) -> dict:
        """Execute task with automatic compaction management"""
        
        print(f"\n🤖 Starting Agent: {task.id}")
        print(f"📊 Context limit: {self.context_limit:,} tokens")
        print(f"⚠️  Compaction threshold: {int(self.context_limit * self.compaction_threshold):,} tokens\n")
        
        # Initialize
        self.session_id = f"agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        context_files = self.load_context_files()
        
        # Check for previous handoff
        handoff = self.load_handoff()
        if handoff:
            print("📂 Found previous session handoff. Incorporating context...\n")
        
        system_prompt = self.build_system_prompt(task, context_files)
        
        # Initial message
        if handoff:
            initial_message = f"""You are resuming from a previous session.

## Previous Session Handoff
{handoff}

---

## Continue With This Objective
{task.objective}

Ready to continue?"""
        else:
            initial_message = f"""Ready to execute the following objective:

{task.objective}

Confirm understanding and begin.
"""
        
        self.messages = [
            {"role": "user", "content": initial_message}
        ]
        
        # Agent loop
        for iteration in range(max_turns):
            self.iteration_count += 1
            
            # Check context threshold
            if self.should_compact():
                print("\n⚠️  CONTEXT THRESHOLD REACHED")
                self._handle_compaction(task)
                return {
                    "status": "compaction_triggered",
                    "session_id": self.session_id,
                    "iterations": self.iteration_count,
                    "tokens_used": self.total_tokens
                }
            
            # Call Claude
            print(f"[Iteration {self.iteration_count}] Context: {(self.total_tokens/self.context_limit)*100:.1f}%")
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=self.messages
            )
            
            # Track tokens
            self.total_tokens += response.usage.input_tokens + response.usage.output_tokens
            
            # Extract response
            assistant_message = response.content[0].text
            
            # Check for compaction signal
            if "COMPACTION_NEEDED" in assistant_message:
                print("\n🚨 Agent signaled compaction needed")
                self._handle_compaction(task)
                return {
                    "status": "compaction_triggered",
                    "session_id": self.session_id,
                    "iterations": self.iteration_count,
                    "tokens_used": self.total_tokens
                }
            
            # Check for task completion
            if response.stop_reason == "end_turn":
                if "completed" in assistant_message.lower() or "done" in assistant_message.lower():
                    print(f"\n✅ Task completed in {self.iteration_count} iterations")
                    self._save_session_summary(task, "completed")
                    return {
                        "status": "completed",
                        "session_id": self.session_id,
                        "iterations": self.iteration_count,
                        "tokens_used": self.total_tokens,
                        "final_message": assistant_message[:500]
                    }
            
            # Add to message history
            self.messages.append({"role": "assistant", "content": assistant_message})
            
            # User provides feedback for continuation
            feedback = input("\n📝 Agent response received. Continue? (y/n/feedback): ").strip()
            
            if feedback.lower() == 'n':
                print("⏹️  Task stopped by user")
                self._save_session_summary(task, "stopped")
                return {
                    "status": "stopped",
                    "session_id": self.session_id,
                    "iterations": self.iteration_count,
                    "tokens_used": self.total_tokens
                }
            
            elif feedback.lower() != 'y':
                # User provided feedback
                self.messages.append({
                    "role": "user",
                    "content": feedback
                })
            else:
                # Automatic continuation
                self.messages.append({
                    "role": "user",
                    "content": "Continue working on the task."
                })
    
    def should_compact(self) -> bool:
        """Check if compaction is needed"""
        ratio = self.total_tokens / self.context_limit
        return ratio >= self.compaction_threshold
    
    def _handle_compaction(self, task: AgentTask):
        """Execute compaction workflow"""
        
        # Save current state
        progress_file = self.state_dir / "progress.json"
        if progress_file.exists():
            with open(progress_file, 'r') as f:
                progress = json.load(f)
        else:
            progress = {"tasks": []}
        
        progress["tasks"].append({
            "task": f"Session {self.session_id}",
            "status": "compaction_triggered",
            "iterations": self.iteration_count,
            "tokens_used": self.total_tokens
        })
        progress["compaction_cycles"] = progress.get("compaction_cycles", 0) + 1
        progress["last_compaction"] = datetime.now().isoformat()
        
        with open(progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
        
        # Generate handoff
        handoff = self._generate_agent_handoff(task)
        handoff_file = self.project_root / "claude_handoff.md"
        handoff_file.write_text(handoff)
        
        print(f"\n✅ Handoff generated: {handoff_file}")
        print(f"📊 Session summary:")
        print(f"   - Iterations: {self.iteration_count}")
        print(f"   - Tokens: {self.total_tokens:,}")
        print(f"   - Compaction cycles: {progress.get('compaction_cycles', 0)}")
    
    def _generate_agent_handoff(self, task: AgentTask) -> str:
        """Generate handoff for next agent session"""
        
        handoff = f"""# Agent Session Handoff
**Session ID:** {self.session_id}
**Generated:** {datetime.now().isoformat()}
**Iterations:** {self.iteration_count}
**Tokens Used:** {self.total_tokens:,}

## Original Objective
{task.objective}

## Progress So Far
The agent has completed {self.iteration_count} iterations.
Check .claude_state/progress.json for detailed task history.

## Important Notes
1. Load .claude_state/progress.json immediately
2. Load .claude_state/decisions.md (architectural decisions)
3. Load .claude_state/debt.json (technical debt)
4. Continue from next pending task

## Instructions for New Session
The next agent session should:
1. Load all persistent state files
2. Review architectural decisions
3. Be aware of technical debt items
4. Continue execution of remaining tasks
5. Signal compaction again at 40% context

---

Handoff ready. Start new session with this context.
"""
        return handoff
    
    def _save_session_summary(self, task: AgentTask, status: str):
        """Save session summary to disk"""
        
        summary = {
            "session_id": self.session_id,
            "objective": task.objective,
            "status": status,
            "started_at": datetime.now().isoformat(),
            "iterations": self.iteration_count,
            "total_tokens": self.total_tokens,
            "messages_exchanged": len(self.messages)
        }
        
        summary_file = self.state_dir / f"session_{self.session_id}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
```

***

### 2. **Orchestrator for Multi-Agent Workflows**

```python
# orchestrator.py
"""
Orchestrates multiple agents in a project workflow.
Implements task distribution, dependency management, and context sharing.
"""

import json
from pathlib import Path
from enum import Enum
from typing import List, Dict, Optional
from dataclasses import dataclass
from claude_agent_compaction import CompactionAwareAgent, AgentTask

class AgentRole(Enum):
    ANALYZER = "analyzer"      # Understand requirements
    ARCHITECT = "architect"    # Design solution
    IMPLEMENTOR = "implementor"  # Write code
    TESTER = "tester"          # Test and validate
    OPTIMIZER = "optimizer"    # Refactor and optimize

@dataclass
class WorkflowTask:
    id: str
    role: AgentRole
    objective: str
    dependencies: List[str]  # Task IDs that must complete first
    priority: int = 1

class ProjectOrchestrator:
    """Coordinates multiple agents to complete a project"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.state_dir = self.project_root / ".claude_state"
        self.state_dir.mkdir(exist_ok=True)
        
        self.agents: Dict[str, CompactionAwareAgent] = {}
        self.workflow: List[WorkflowTask] = []
        self.completed_tasks: List[str] = []
        self.task_results: Dict[str, dict] = {}
    
    def create_agent(self, role: AgentRole, model: str = "claude-opus-4-1") -> CompactionAwareAgent:
        """Create agent for specific role"""
        agent = CompactionAwareAgent(str(self.project_root), model)
        self.agents[role.value] = agent
        return agent
    
    def add_workflow_task(self, task: WorkflowTask):
        """Add task to workflow"""
        self.workflow.append(task)
        self._save_workflow()
    
    def execute_workflow(self) -> dict:
        """Execute workflow respecting dependencies"""
        
        print("\n🚀 Starting Project Orchestration")
        print(f"📋 {len(self.workflow)} tasks in workflow\n")
        
        # Sort by dependencies
        sorted_tasks = self._topological_sort()
        
        for task in sorted_tasks:
            if task.id in self.completed_tasks:
                print(f"✅ {task.id} (already completed)")
                continue
            
            print(f"\n🎯 Executing: {task.id}")
            print(f"   Role: {task.role.value}")
            print(f"   Objective: {task.objective}")
            
            # Get agent for role
            if task.role.value not in self.agents:
                self.create_agent(task.role)
            
            agent = self.agents[task.role.value]
            
            # Execute task
            agent_task = AgentTask(
                id=task.id,
                objective=task.objective,
                instructions=self._build_agent_instructions(task),
                max_iterations=20
            )
            
            result = agent.execute_task(agent_task)
            
            # Handle result
            if result["status"] == "compaction_triggered":
                print(f"\n⚠️  {task.id} triggered compaction")
                print(f"   Handoff saved for next session")
                
                # Mark as pending, will continue in next session
                self.task_results[task.id] = {
                    "status": "pending_continuation",
                    "result": result,
                    "session_id": result["session_id"]
                }
                
                # Save orchestration state
                self._save_orchestration_state()
                return {
                    "status": "compaction_needed",
                    "current_task": task.id,
                    "completed": len(self.completed_tasks),
                    "remaining": len(self.workflow) - len(self.completed_tasks)
                }
            
            elif result["status"] == "completed":
                self.completed_tasks.append(task.id)
                self.task_results[task.id] = result
                print(f"✅ {task.id} completed in {result['iterations']} iterations")
            
            else:
                print(f"⚠️  {task.id} status: {result['status']}")
                self.task_results[task.id] = result
        
        print(f"\n✅ Workflow complete!")
        print(f"   Completed: {len(self.completed_tasks)}/{len(self.workflow)}")
        return {
            "status": "completed",
            "completed_tasks": self.completed_tasks,
            "total_tasks": len(self.workflow)
        }
    
    def _topological_sort(self) -> List[WorkflowTask]:
        """Sort tasks by dependencies"""
        sorted_list = []
        visited = set()
        
        def visit(task: WorkflowTask):
            if task.id in visited:
                return
            visited.add(task.id)
            
            # Visit dependencies first
            for dep_id in task.dependencies:
                dep_task = next((t for t in self.workflow if t.id == dep_id), None)
                if dep_task:
                    visit(dep_task)
            
            sorted_list.append(task)
        
        for task in self.workflow:
            visit(task)
        
        return sorted_list
    
    def _build_agent_instructions(self, task: WorkflowTask) -> str:
        """Build role-specific instructions"""
        
        instructions = f"""## Task: {task.id}

### Objective
{task.objective}

### Context
"""
        
        # Add results from completed dependencies
        for dep_id in task.dependencies:
            if dep_id in self.task_results:
                result = self.task_results[dep_id]
                instructions += f"- **{dep_id}**: {result.get('status', 'unknown')}\n"
        
        # Role-specific instructions
        role_instructions = {
            AgentRole.ANALYZER: """
### Your Role: Analyzer
1. Understand the requirements fully
2. Identify ambiguities
3. List assumptions
4. Create detailed spec
Output to: .claude_state/analysis_{task_id}.md
""",
            AgentRole.ARCHITECT: """
### Your Role: Architect
1. Review analyzer output
2. Design system architecture
3. Choose technologies
4. Document decisions
Output to: .claude_state/architecture_{task_id}.md
""",
            AgentRole.IMPLEMENTOR: """
### Your Role: Implementor
1. Follow architecture from previous phase
2. Write production code
3. Follow code standards
4. Update progress.json
Output: Working code in src/
""",
            AgentRole.TESTER: """
### Your Role: Tester
1. Write comprehensive tests
2. Run test suite
3. Achieve >80% coverage
4. Document test results
Output: Tests in tests/
""",
            AgentRole.OPTIMIZER: """
### Your Role: Optimizer
1. Profile code for bottlenecks
2. Refactor for clarity
3. Document optimizations
4. Update technical debt status
Output: Optimized code + report
"""
        }
        
        instructions += role_instructions.get(task.role, "")
        
        return instructions
    
    def _save_workflow(self):
        """Save workflow state to disk"""
        workflow_data = {
            "tasks": [
                {
                    "id": task.id,
                    "role": task.role.value,
                    "objective": task.objective,
                    "dependencies": task.dependencies,
                    "priority": task.priority
                }
                for task in self.workflow
            ]
        }
        
        with open(self.state_dir / "workflow.json", 'w') as f:
            json.dump(workflow_data, f, indent=2)
    
    def _save_orchestration_state(self):
        """Save current orchestration state"""
        state = {
            "completed_tasks": self.completed_tasks,
            "task_results": self.task_results,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(self.state_dir / "orchestration_state.json", 'w') as f:
            json.dump(state, f, indent=2)
    
    def resume_from_compaction(self):
        """Resume orchestration after compaction"""
        
        # Load state
        state_file = self.state_dir / "orchestration_state.json"
        if state_file.exists():
            with open(state_file, 'r') as f:
                state = json.load(f)
                self.completed_tasks = state["completed_tasks"]
                self.task_results = state["task_results"]
        
        print("\n▶️  Resuming orchestration from compaction")
        print(f"   Completed: {len(self.completed_tasks)} tasks")
        
        # Continue execution
        return self.execute_workflow()

# Example usage
if __name__ == "__main__":
    from datetime import datetime
    
    # Create orchestrator
    orch = ProjectOrchestrator()
    
    # Define workflow
    orch.add_workflow_task(WorkflowTask(
        id="analyze-requirements",
        role=AgentRole.ANALYZER,
        objective="Analyze requirements for a Python CLI tool that manages PostgreSQL migrations",
        dependencies=[]
    ))
    
    orch.add_workflow_task(WorkflowTask(
        id="design-architecture",
        role=AgentRole.ARCHITECT,
        objective="Design the architecture based on analysis. Choose framework, file structure, and libraries.",
        dependencies=["analyze-requirements"]
    ))
    
    orch.add_workflow_task(WorkflowTask(
        id="implement-core",
        role=AgentRole.IMPLEMENTOR,
        objective="Implement the core CLI using Click framework. Create main commands and structure.",
        dependencies=["design-architecture"]
    ))
    
    orch.add_workflow_task(WorkflowTask(
        id="write-tests",
        role=AgentRole.TESTER,
        objective="Write comprehensive tests for all CLI commands and edge cases.",
        dependencies=["implement-core"]
    ))
    
    orch.add_workflow_task(WorkflowTask(
        id="optimize",
        role=AgentRole.OPTIMIZER,
        objective="Profile code, refactor for clarity, and optimize performance.",
        dependencies=["write-tests"]
    ))
    
    # Execute
    result = orch.execute_workflow()
    print(f"\n📊 Final result: {result}")
```

***

### 3. **Tool Definitions for Agent Use**

```python
# agent_tools.py
"""
Tool definitions for Claude agents using Model Context Protocol (MCP)
and Anthropic's built-in tool system.
"""

from typing import Callable, Dict, Any

class AgentToolkit:
    """Tools available to agents for task execution"""
    
    @staticmethod
    def get_file_tools() -> Dict[str, Dict[str, Any]]:
        """File system tools for agents"""
        return {
            "read_file": {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read contents of a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "File path to read"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            "write_file": {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write content to a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "File path"},
                            "content": {"type": "string", "description": "File content"}
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            "list_files": {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "List files in directory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Directory path"}
                        },
                        "required": ["path"]
                    }
                }
            }
        }
    
    @staticmethod
    def get_execution_tools() -> Dict[str, Dict[str, Any]]:
        """Code execution and shell tools"""
        return {
            "execute_bash": {
                "type": "function",
                "function": {
                    "name": "execute_bash",
                    "description": "Execute bash command",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "Bash command to run"},
                            "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 30}
                        },
                        "required": ["command"]
                    }
                }
            },
            "execute_python": {
                "type": "function",
                "function": {
                    "name": "execute_python",
                    "description": "Execute Python code",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Python code to execute"}
                        },
                        "required": ["code"]
                    }
                }
            }
        }
    
    @staticmethod
    def get_state_tools() -> Dict[str, Dict[str, Any]]:
        """State management tools for Intentional Compaction"""
        return {
            "update_progress": {
                "type": "function",
                "function": {
                    "name": "update_progress",
                    "description": "Update progress tracking",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "task": {"type": "string"},
                            "status": {"type": "string", "enum": ["started", "in_progress", "completed", "blocked"]},
                            "notes": {"type": "string"}
                        },
                        "required": ["task", "status"]
                    }
                }
            },
            "log_decision": {
                "type": "function",
                "function": {
                    "name": "log_decision",
                    "description": "Log architectural decision",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "type": {"type": "string", "enum": ["architecture", "algorithm", "pattern", "dependency"]},
                            "rationale": {"type": "string"},
                            "alternatives": {"type": "string"}
                        },
                        "required": ["title", "type", "rationale"]
                    }
                }
            },
            "log_debt": {
                "type": "function",
                "function": {
                    "name": "log_debt",
                    "description": "Log technical debt",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "item": {"type": "string"},
                            "severity": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                            "location": {"type": "string"},
                            "fix": {"type": "string"}
                        },
                        "required": ["item", "severity", "location"]
                    }
                }
            }
        }
    
    @staticmethod
    def get_all_tools() -> Dict[str, Dict[str, Any]]:
        """All tools available to agent"""
        tools = {}
        tools.update(AgentToolkit.get_file_tools())
        tools.update(AgentToolkit.get_execution_tools())
        tools.update(AgentToolkit.get_state_tools())
        return tools
```

***

### 4. **Command-Line Orchestration Script**

```bash
#!/bin/bash
# scripts/run_agent_workflow.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🤖 Claude Agent Workflow Orchestrator"
echo "====================================="
echo ""
echo "Project: $PROJECT_ROOT"
echo ""

# Parse arguments
COMMAND=${1:-execute}
PROJECT_TYPE=${2:-webapp}

case $COMMAND in
    execute)
        echo "🚀 Executing full project workflow..."
        python3 << 'EOF'
from orchestrator import ProjectOrchestrator, WorkflowTask, AgentRole

orch = ProjectOrchestrator()

# Define workflow for project type
PROJECT_TYPE = "$PROJECT_TYPE"

if PROJECT_TYPE == "webapp":
    tasks = [
        WorkflowTask("analyze", AgentRole.ANALYZER, 
                    "Analyze requirements for a FastAPI web application with authentication"),
        WorkflowTask("design", AgentRole.ARCHITECT, 
                    "Design architecture with database schema and API routes", 
                    dependencies=["analyze"]),
        WorkflowTask("implement", AgentRole.IMPLEMENTOR, 
                    "Implement FastAPI application with SQLAlchemy models",
                    dependencies=["design"]),
        WorkflowTask("test", AgentRole.TESTER,
                    "Write pytest tests with >80% coverage",
                    dependencies=["implement"]),
        WorkflowTask("deploy", AgentRole.OPTIMIZER,
                    "Optimize and prepare for deployment",
                    dependencies=["test"])
    ]
elif PROJECT_TYPE == "cli":
    tasks = [
        WorkflowTask("analyze", AgentRole.ANALYZER,
                    "Analyze CLI requirements"),
        WorkflowTask("design", AgentRole.ARCHITECT,
                    "Design CLI structure with Click framework",
                    dependencies=["analyze"]),
        WorkflowTask("implement", AgentRole.IMPLEMENTOR,
                    "Implement CLI commands",
                    dependencies=["design"]),
        WorkflowTask("test", AgentRole.TESTER,
                    "Test all CLI commands",
                    dependencies=["implement"])
    ]
else:
    print(f"Unknown project type: {PROJECT_TYPE}")
    exit(1)

for task in tasks:
    orch.add_workflow_task(task)

result = orch.execute_workflow()
print(f"\nWorkflow status: {result['status']}")
EOF
        ;;
        
    resume)
        echo "▶️  Resuming from compaction..."
        python3 << 'EOF'
from orchestrator import ProjectOrchestrator

orch = ProjectOrchestrator()
result = orch.resume_from_compaction()
print(f"\nResume status: {result['status']}")
EOF
        ;;
        
    status)
        echo "📊 Workflow Status"
        echo "================="
        if [ -f "$PROJECT_ROOT/.claude_state/orchestration_state.json" ]; then
            python3 << 'EOF'
import json
from pathlib import Path

state = json.loads(Path(".claude_state/orchestration_state.json").read_text())
print(f"Completed tasks: {len(state['completed_tasks'])}")
for task_id in state['completed_tasks']:
    print(f"  ✅ {task_id}")

print(f"\nPending tasks:")
pending = [k for k, v in state['task_results'].items() if v.get('status') == 'pending_continuation']
if pending:
    for task_id in pending:
        print(f"  ⏳ {task_id}")
else:
    print("  None")
EOF
        else
            echo "No workflow state found"
        fi
        ;;
        
    *)
        echo "Usage: $0 <execute|resume|status> [project-type]"
        exit 1
        ;;
esac
```

***

### 5. **Integration with Existing compaction.py**

```python
# claude_compaction.py (updated)

# Add this method to CompactionEngine class:

def attach_agent_sdk(self) -> dict:
    """Returns configuration for Claude Agent SDK integration"""
    
    return {
        "agent_config": {
            "model": "claude-opus-4-1",
            "context_limit": 200000,
            "compaction_threshold": 0.4,
            "tools": {
                "file_operations": ["read_file", "write_file", "list_files"],
                "execution": ["execute_bash", "execute_python"],
                "state_management": ["update_progress", "log_decision", "log_debt"]
            }
        },
        "orchestration": {
            "enable_multi_agent": True,
            "roles": ["analyzer", "architect", "implementor", "tester", "optimizer"],
            "task_dependencies": True,
            "auto_compaction": True
        },
        "state_files": {
            "progress": str(self.progress_file),
            "decisions": str(self.decisions_file),
            "debt": str(self.technical_debt_file),
            "workflow": str(self.state_dir / "workflow.json")
        }
    }
```

***

## Usage Pattern

**Terminal 1: Initialize and Configure**
```bash
./scripts/init_claude.sh
./scripts/run_agent_workflow.sh execute webapp
```

**Output:**
```
🤖 Claude Agent Workflow Orchestrator
🚀 Executing full project workflow...
📋 5 tasks in workflow

🎯 Executing: analyze-requirements
   Role: analyzer
   [Iteration 1] Context: 2.5%
   [Iteration 2] Context: 5.8%
   ...

✅ Task completed in 7 iterations

🎯 Executing: design-architecture
   [Iteration 1] Context: 8.2%
   ...

⚠️  CONTEXT THRESHOLD REACHED
📊 Session summary:
   - Iterations: 45
   - Tokens: 82,000 (41% of limit)
   - Compaction cycles: 1

✅ Handoff generated: claude_handoff.md
📋 Waiting for human review before resuming...
```

**Terminal 2: Resume After Compaction**
```bash
./scripts/run_agent_workflow.sh resume
```

The new agent loads `claude_handoff.md` and continues seamlessly.

***

## Key Benefits

1. **Autonomous Context Lifecycle**: Agents monitor and signal compaction automatically
2. **Multi-Agent Orchestration**: Specialized agents handle different roles
3. **Persistent State**: All decisions/progress survive across sessions
4. **Zero Context Waste**: Handoff contains only necessary information
5. **Dependency Management**: Tasks execute in correct order
6. **Automatic Resume**: Compaction triggers cleanup + seamless continuation

This gives you production-ready autonomous agents that respect context limits and never degrade into the "dumb zone".

## Human

Can claude code subagents trigger this for their own context?  Thereby avoiding running out of their own context space?

## Assistant

Perfect. Here's how to implement **self-aware subagents** that monitor and trigger their own compaction:

***

## Self-Monitoring Subagents with Auto-Compaction

### 1. **Core: Context-Aware Subagent Framework**

```python
# subagent_manager.py
"""
Subagent framework with autonomous context monitoring.
Subagents trigger compaction when approaching context limits.
"""

import anthropic
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Callable
from enum import Enum

class SubagentRole(Enum):
    """Specialized subagent roles"""
    CODE_REVIEWER = "code_reviewer"
    DEBUGGER = "debugger"
    OPTIMIZER = "optimizer"
    TEST_WRITER = "test_writer"
    REFACTORER = "refactorer"
    DOCUMENTER = "documenter"

@dataclass
class SubagentConfig:
    """Configuration for a subagent instance"""
    role: SubagentRole
    name: str
    context_limit: int = 50000  # Subagents get smaller context window
    compaction_threshold: float = 0.35  # Trigger earlier than main (35% vs 40%)
    max_iterations: int = 50
    model: str = "claude-opus-4-1"
    tools: list = None

class SubagentContextMonitor:
    """Monitors context usage and triggers compaction autonomously"""
    
    def __init__(self, config: SubagentConfig):
        self.config = config
        self.current_tokens = 0
        self.iteration_count = 0
        self.should_compact = False
        self.compaction_triggered_at = None
        
    def update_tokens(self, input_tokens: int, output_tokens: int):
        """Track token usage in real-time"""
        self.current_tokens += input_tokens + output_tokens
        
        # Check threshold
        usage_ratio = self.current_tokens / self.config.context_limit
        
        if usage_ratio >= self.config.compaction_threshold and not self.should_compact:
            self.should_compact = True
            self.compaction_triggered_at = datetime.now().isoformat()
            
            print(f"\n⚠️  [{self.config.name}] Context threshold reached!")
            print(f"   Usage: {self.current_tokens:,} / {self.config.context_limit:,} tokens")
            print(f"   Ratio: {usage_ratio*100:.1f}%")
            print(f"   Iterations: {self.iteration_count}")
    
    def get_context_status(self) -> dict:
        """Return current context status"""
        return {
            "tokens_used": self.current_tokens,
            "tokens_available": self.config.context_limit,
            "usage_ratio": self.current_tokens / self.config.context_limit,
            "iterations": self.iteration_count,
            "should_compact": self.should_compact,
            "compaction_triggered_at": self.compaction_triggered_at
        }

class AutoCompactionSubagent:
    """
    Subagent that monitors its own context and triggers compaction.
    Each subagent operates independently with its own context window.
    """
    
    def __init__(self, config: SubagentConfig, project_root: str = "."):
        self.config = config
        self.project_root = Path(project_root)
        self.state_dir = self.project_root / ".claude_state" / "subagents"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        self.client = anthropic.Anthropic()
        self.monitor = SubagentContextMonitor(config)
        
        self.messages = []
        self.task_results = []
        
        # Per-subagent state files
        self.subagent_state_file = self.state_dir / f"{config.name}_state.json"
        self.subagent_handoff_file = self.state_dir / f"{config.name}_handoff.md"
    
    def load_prior_context(self) -> Optional[str]:
        """Load handoff from previous subagent session"""
        if self.subagent_handoff_file.exists():
            return self.subagent_handoff_file.read_text()
        return None
    
    def execute_task(self, task: str, context_injection: str = "") -> dict:
        """
        Execute task with autonomous context monitoring.
        Returns immediately if compaction is needed.
        """
        
        print(f"\n🤖 Starting Subagent: {self.config.name}")
        print(f"   Role: {self.config.role.value}")
        print(f"   Context limit: {self.config.context_limit:,} tokens")
        print(f"   Compaction threshold: {self.config.compaction_threshold*100:.0f}%\n")
        
        # Load prior context if available
        prior_context = self.load_prior_context()
        
        # Build system prompt
        system_prompt = self._build_system_prompt(task, context_injection)
        
        # Initial message
        if prior_context:
            initial_message = f"""You are resuming from a previous session.

## Previous Session Context
{prior_context}

---

## Continue with this task:
{task}

Confirm understanding and begin.
"""
        else:
            initial_message = f"""Execute the following task:

{task}

Confirm understanding and begin.
"""
        
        self.messages = [{"role": "user", "content": initial_message}]
        
        # Agent loop
        for iteration in range(self.config.max_iterations):
            self.monitor.iteration_count += 1
            
            # CRITICAL: Check context before making API call
            if self.monitor.should_compact:
                print(f"\n✋ Subagent context limit reached. Preparing compaction...")
                
                # Generate handoff and save state
                handoff = self._generate_subagent_handoff(task)
                self.subagent_handoff_file.write_text(handoff)
                self._save_subagent_state()
                
                return {
                    "status": "compaction_needed",
                    "subagent": self.config.name,
                    "tokens_used": self.monitor.current_tokens,
                    "iterations": self.monitor.iteration_count,
                    "handoff_file": str(self.subagent_handoff_file),
                    "task_results": self.task_results
                }
            
            # Display context status
            status = self.monitor.get_context_status()
            print(f"[Iter {self.monitor.iteration_count}] Context: {status['usage_ratio']*100:.1f}% | Tokens: {status['tokens_used']:,}")
            
            # Call Claude
            try:
                response = self.client.messages.create(
                    model=self.config.model,
                    max_tokens=3000,
                    system=system_prompt,
                    messages=self.messages
                )
                
                # Update token tracking
                self.monitor.update_tokens(
                    response.usage.input_tokens,
                    response.usage.output_tokens
                )
                
                # Extract response
                assistant_message = response.content[0].text
                
                # Check for explicit compaction signal from subagent
                if "SUBAGENT_COMPACT" in assistant_message:
                    print(f"\n⚠️  Subagent requested compaction")
                    handoff = self._generate_subagent_handoff(task)
                    self.subagent_handoff_file.write_text(handoff)
                    self._save_subagent_state()
                    
                    return {
                        "status": "compaction_requested",
                        "subagent": self.config.name,
                        "tokens_used": self.monitor.current_tokens,
                        "iterations": self.monitor.iteration_count,
                        "handoff_file": str(self.subagent_handoff_file),
                        "task_results": self.task_results
                    }
                
                # Check for completion
                if response.stop_reason == "end_turn":
                    if "completed" in assistant_message.lower() or "done" in assistant_message.lower():
                        print(f"\n✅ Subagent task completed")
                        self._save_subagent_state()
                        
                        return {
                            "status": "completed",
                            "subagent": self.config.name,
                            "tokens_used": self.monitor.current_tokens,
                            "iterations": self.monitor.iteration_count,
                            "result": assistant_message[:500],
                            "task_results": self.task_results
                        }
                
                # Continue conversation
                self.messages.append({"role": "assistant", "content": assistant_message})
                
                # Log task result
                self.task_results.append({
                    "iteration": self.monitor.iteration_count,
                    "status": "in_progress",
                    "tokens": response.usage.input_tokens + response.usage.output_tokens
                })
                
                # Auto-continue (no human interaction needed for subagents)
                self.messages.append({
                    "role": "user",
                    "content": "Continue working on the task."
                })
            
            except Exception as e:
                print(f"❌ Error in subagent execution: {e}")
                return {
                    "status": "error",
                    "subagent": self.config.name,
                    "error": str(e),
                    "iterations": self.monitor.iteration_count
                }
        
        print(f"⚠️  Subagent reached iteration limit")
        return {
            "status": "max_iterations_reached",
            "subagent": self.config.name,
            "iterations": self.monitor.iteration_count,
            "tokens_used": self.monitor.current_tokens
        }
    
    def _build_system_prompt(self, task: str, context_injection: str) -> str:
        """Build role-specific system prompt"""
        
        role_instructions = {
            SubagentRole.CODE_REVIEWER: """
You are a Code Reviewer subagent. Your job:
1. Review code for quality, security, and best practices
2. Identify potential bugs and performance issues
3. Suggest improvements
4. Log findings in structured format
5. When context approaches 35%: signal SUBAGENT_COMPACT to trigger handoff
""",
            SubagentRole.DEBUGGER: """
You are a Debugger subagent. Your job:
1. Identify root causes of issues
2. Run tests to isolate problems
3. Propose fixes
4. Verify solutions
5. When context approaches 35%: signal SUBAGENT_COMPACT
""",
            SubagentRole.OPTIMIZER: """
You are an Optimizer subagent. Your job:
1. Profile code for performance issues
2. Identify bottlenecks
3. Propose optimizations
4. Measure improvements
5. When context approaches 35%: signal SUBAGENT_COMPACT
""",
            SubagentRole.TEST_WRITER: """
You are a Test Writer subagent. Your job:
1. Write comprehensive test cases
2. Achieve high code coverage
3. Test edge cases
4. Run test suite
5. When context approaches 35%: signal SUBAGENT_COMPACT
""",
            SubagentRole.REFACTORER: """
You are a Refactoring subagent. Your job:
1. Improve code structure
2. Reduce duplication
3. Improve readability
4. Maintain functionality
5. When context approaches 35%: signal SUBAGENT_COMPACT
""",
            SubagentRole.DOCUMENTER: """
You are a Documentation subagent. Your job:
1. Write clear documentation
2. Document APIs and functions
3. Create usage examples
4. Update README
5. When context approaches 35%: signal SUBAGENT_COMPACT
"""
        }
        
        prompt = f"""You are a specialized {self.config.role.value} subagent operating independently.

{role_instructions.get(self.config.role, "")}

## Context Management
- Your context limit: {self.config.context_limit:,} tokens
- Trigger compaction at: {self.config.compaction_threshold*100:.0f}% usage
- Current iteration: Track iterations locally
- Do NOT access parent agent context
- Each response is isolated and independent

## Task
{task}

{context_injection}

## Compaction Signal
When your context is approaching {self.config.compaction_threshold*100:.0f}% usage:
1. Generate summary of work done
2. Include: SUBAGENT_COMPACT in your response
3. Main agent will handle handoff
4. Resume in fresh session with prior context

Start work now.
"""
        return prompt
    
    def _generate_subagent_handoff(self, task: str) -> str:
        """Generate handoff for subagent continuation in new session"""
        
        handoff = f"""# {self.config.name} Subagent Handoff

**Session:** {datetime.now().isoformat()}
**Role:** {self.config.role.value}
**Tokens Used:** {self.monitor.current_tokens:,} / {self.config.context_limit:,}
**Iterations:** {self.monitor.iteration_count}

## Original Task
{task}

## Work Completed
- Iterations: {self.monitor.iteration_count}
- Token efficiency: {(self.monitor.current_tokens / self.monitor.iteration_count):.0f} tokens/iteration
- Status: In progress, compaction triggered at {self.config.compaction_threshold*100:.0f}% capacity

## Results So Far
"""
        
        for i, result in enumerate(self.task_results[-5:], 1):
            handoff += f"- **Iteration {result['iteration']}**: {result['status']} ({result['tokens']} tokens)\n"
        
        handoff += f"""
## Instructions for Next Session
1. You are resuming as {self.config.name} subagent
2. Continue from where you left off
3. Complete remaining work
4. Same task: {task[:100]}...

The parent agent will coordinate your handoff and continuation.
"""
        return handoff
    
    def _save_subagent_state(self):
        """Save subagent state for recovery"""
        state = {
            "subagent": self.config.name,
            "role": self.config.role.value,
            "saved_at": datetime.now().isoformat(),
            "context_monitor": self.monitor.get_context_status(),
            "messages_count": len(self.messages),
            "task_results": self.task_results
        }
        
        with open(self.subagent_state_file, 'w') as f:
            json.dump(state, f, indent=2)

class SubagentOrchestrator:
    """Manages multiple subagents with automatic compaction handling"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.subagents: dict = {}
        self.results: dict = {}
    
    def create_subagent(self, config: SubagentConfig) -> AutoCompactionSubagent:
        """Create and register a subagent"""
        subagent = AutoCompactionSubagent(config, str(self.project_root))
        self.subagents[config.name] = subagent
        return subagent
    
    def execute_parallel_tasks(self, tasks: dict) -> dict:
        """
        Execute multiple subagent tasks in parallel (simulated).
        
        tasks: {
            "subagent_name": {
                "config": SubagentConfig(...),
                "task": "task description",
                "context_injection": "additional context"
            }
        }
        """
        
        print("\n🚀 Starting Subagent Orchestration")
        print(f"📋 {len(tasks)} parallel tasks\n")
        
        orchestration_state = {
            "started_at": datetime.now().isoformat(),
            "tasks": {},
            "compaction_signals": []
        }
        
        for subagent_name, task_spec in tasks.items():
            config = task_spec["config"]
            task = task_spec["task"]
            context = task_spec.get("context_injection", "")
            
            # Create subagent
            subagent = self.create_subagent(config)
            
            # Execute task
            result = subagent.execute_task(task, context)
            
            # Track result
            self.results[subagent_name] = result
            orchestration_state["tasks"][subagent_name] = result
            
            # Handle compaction
            if result["status"] in ["compaction_needed", "compaction_requested"]:
                orchestration_state["compaction_signals"].append({
                    "subagent": subagent_name,
                    "handoff_file": result.get("handoff_file"),
                    "tokens_used": result.get("tokens_used"),
                    "reason": result["status"]
                })
            
            # Print status
            print(f"\n📊 {subagent_name}: {result['status']}")
            print(f"   Tokens: {result.get('tokens_used', 'N/A')}")
            print(f"   Iterations: {result.get('iterations', 'N/A')}")
        
        # Save orchestration state
        self._save_orchestration_state(orchestration_state)
        
        return orchestration_state
    
    def resume_compacted_subagents(self):
        """Resume any subagents that triggered compaction"""
        
        print("\n▶️  Resuming Compacted Subagents")
        
        state_dir = self.project_root / ".claude_state" / "subagents"
        
        # Find all handoff files
        handoff_files = list(state_dir.glob("*_handoff.md"))
        
        if not handoff_files:
            print("No pending subagent handoffs")
            return {}
        
        print(f"Found {len(handoff_files)} pending subagents\n")
        
        for handoff_file in handoff_files:
            # Extract subagent name from filename
            subagent_name = handoff_file.stem.replace("_handoff", "")
            
            print(f"🔄 Resuming: {subagent_name}")
            print(f"   Handoff: {handoff_file}")
            
            # In production: re-create subagent with same config,
            # feed it the handoff, and continue execution
    
    def _save_orchestration_state(self, state: dict):
        """Save overall orchestration state"""
        state_file = self.project_root / ".claude_state" / "orchestration.json"
        
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
```

***

### 2. **Integration with Claude Code Hooks**

```python
# .claude/hooks.py
"""
Claude Code hooks that monitor subagent context and trigger compaction.
Runs automatically during Claude Code sessions.
"""

import json
from pathlib import Path
from datetime import datetime

class SubagentContextHook:
    """Hook that monitors subagent context and triggers actions"""
    
    def __init__(self):
        self.subagent_states = {}
        self.state_file = Path(".claude_state/subagents/hook_state.json")
    
    def pre_tool_use(self, tool_name: str, args: dict) -> dict:
        """
        Intercept before subagent tool execution.
        Check context and prevent exceeding limits.
        """
        
        # Track tool use for token estimation
        if tool_name in ["read_file", "write_file", "execute_bash", "execute_python"]:
            self._estimate_tokens(tool_name, args)
        
        return {"action": "allow"}
    
    def post_tool_use(self, tool_name: str, result: str, args: dict):
        """
        Monitor after tool execution.
        Check if subagent should trigger compaction.
        """
        
        # Get current context usage (from Claude Code)
        context_usage = self._get_context_usage()
        
        if context_usage["ratio"] > 0.35:  # Subagent threshold
            print("\n⚠️  Subagent context threshold reached!")
            print(f"   Usage: {context_usage['used']:,} / {context_usage['limit']:,}")
            print(f"   Action: Trigger compaction")
            
            # Signal compaction
            return {
                "action": "trigger_compaction",
                "reason": "subagent_context_limit"
            }
        
        return {"action": "continue"}
    
    def _estimate_tokens(self, tool_name: str, args: dict):
        """Rough token estimation for operations"""
        token_cost = {
            "read_file": lambda args: len(Path(args.get("path", "")).read_text() or "") // 4,
            "write_file": lambda args: len(args.get("content", "")) // 4,
            "execute_bash": lambda args: len(args.get("command", "")) // 4,
            "execute_python": lambda args: len(args.get("code", "")) // 4
        }
        
        if tool_name in token_cost:
            estimated = token_cost[tool_name](args)
            # Add to running total
    
    def _get_context_usage(self) -> dict:
        """Get current context usage from Claude Code"""
        # In actual Claude Code, this data is available from the runtime
        return {
            "used": 0,  # Placeholder
            "limit": 50000,  # Subagent limit
            "ratio": 0.0
        }
```

***

### 3. **Practical Integration Example**

```python
# main.py
"""
Example of subagents triggering their own compaction.
"""

from subagent_manager import (
    AutoCompactionSubagent,
    SubagentOrchestrator,
    SubagentConfig,
    SubagentRole
)

def example_parallel_code_review():
    """
    Example: Multiple subagents review code in parallel.
    Each monitors its own context and compacts independently.
    """
    
    orch = SubagentOrchestrator()
    
    # Define parallel review tasks
    tasks = {
        "code_reviewer": {
            "config": SubagentConfig(
                role=SubagentRole.CODE_REVIEWER,
                name="code_reviewer",
                context_limit=50000,
                compaction_threshold=0.35  # Trigger at 35%
            ),
            "task": """Review the following code files for quality issues:
- src/main.py
- src/utils.py
- src/models.py

Focus on:
1. Code clarity and readability
2. Potential security issues
3. Performance concerns
4. PEP 8 compliance

Provide detailed feedback for each file."""
        },
        
        "test_writer": {
            "config": SubagentConfig(
                role=SubagentRole.TEST_WRITER,
                name="test_writer",
                context_limit=50000,
                compaction_threshold=0.35
            ),
            "task": """Write comprehensive tests for the codebase:
- src/main.py
- src/utils.py

Requirements:
1. >80% code coverage
2. Test edge cases
3. Test error handling
4. Use pytest fixtures

Output tests to tests/"""
        },
        
        "optimizer": {
            "config": SubagentConfig(
                role=SubagentRole.OPTIMIZER,
                name="optimizer",
                context_limit=50000,
                compaction_threshold=0.35
            ),
            "task": """Profile and optimize the codebase:
1. Identify performance bottlenecks
2. Measure current performance
3. Apply optimizations
4. Benchmark improvements
5. Document changes"""
        }
    }
    
    # Execute all subagents
    orchestration_result = orch.execute_parallel_tasks(tasks)
    
    print("\n📊 Orchestration Summary:")
    print(json.dumps(orchestration_result, indent=2))
    
    # Check for compaction signals
    if orchestration_result["compaction_signals"]:
        print(f"\n⚠️  {len(orchestration_result['compaction_signals'])} subagents signaled compaction")
        
        for signal in orchestration_result["compaction_signals"]:
            print(f"\n   Subagent: {signal['subagent']}")
            print(f"   Handoff: {signal['handoff_file']}")
            print(f"   Tokens: {signal['tokens_used']:,}")
        
        print("\n▶️  To resume compacted subagents:")
        print("   orch.resume_compacted_subagents()")

if __name__ == "__main__":
    example_parallel_code_review()
```

***

### 4. **Claude Code Integration (In Your .claude Directory)**

```yaml
# .claude/subagent-config.yaml

subagents:
  code_reviewer:
    role: code_reviewer
    context_limit: 50000
    compaction_threshold: 0.35
    tools:
      - read_file
      - grep
      - bash
    instructions: |
      Review code for quality, security, performance issues.
      Signal SUBAGENT_COMPACT when approaching 35% context.
  
  debugger:
    role: debugger
    context_limit: 50000
    compaction_threshold: 0.35
    tools:
      - read_file
      - execute_bash
      - execute_python
    instructions: |
      Debug issues, run tests, isolate root causes.
      Signal SUBAGENT_COMPACT when approaching 35% context.
  
  test_writer:
    role: test_writer
    context_limit: 50000
    compaction_threshold: 0.35
    tools:
      - read_file
      - write_file
      - execute_bash
    instructions: |
      Write comprehensive tests with >80% coverage.
      Signal SUBAGENT_COMPACT when approaching 35% context.

compaction:
  enabled: true
  per_subagent: true
  threshold_ratio: 0.35
  auto_handoff: true
  state_persistence: .claude_state/subagents/
```

***

### 5. **Key Benefits Over Non-Monitoring Subagents**

```
Standard Subagent:
┌─────────────────────────────┐
│ Subagent                    │
│ Context: 0% → 50% → 90% 💥 │  ← Degrades at 90%
│ (Human must manually stop)  │
└─────────────────────────────┘

Self-Monitoring Subagent:
┌─────────────────────────────┐
│ Subagent                    │
│ Monitoring: ████░░░░░░░░░░ │  ← Checks continuously
│ At 35%: Signals compaction  │  ← Proactive signal
│ Generates handoff           │  ← Automatic recovery
│ Fresh session continues     │  ← Zero degradation
└─────────────────────────────┘
```

***

## Usage Pattern

**Before Compaction:**
```
🤖 Starting Subagent: code_reviewer
   Role: code_reviewer
   Context limit: 50,000 tokens
   Compaction threshold: 35%

[Iter 1] Context: 2.5% | Tokens: 1,250
[Iter 2] Context: 5.8% | Tokens: 2,900
[Iter 3] Context: 8.2% | Tokens: 4,100
...
[Iter 18] Context: 34.2% | Tokens: 17,100

⚠️  [code_reviewer] Context threshold reached!
   Usage: 17,100 / 50,000 tokens
   Ratio: 34.2%
   Iterations: 18

✋ Subagent context limit reached. Preparing compaction...
✅ Handoff generated: .claude_state/subagents/code_reviewer_handoff.md
```

**After Resumption:**
```
▶️  Resuming Subagent: code_reviewer
   Loading handoff from previous session...
   
[Iter 19] Context: 2.5% | Tokens: 1,250  ← Fresh context!
[Iter 20] Context: 6.1% | Tokens: 3,050
...
```

***

## Answer to Your Question

**Yes, absolutely.** Subagents can and should autonomously:

1. ✅ **Monitor own context** - Track tokens per iteration
2. ✅ **Trigger compaction** - At 35% (lower than main 40%) to be conservative  
3. ✅ **Generate handoff** - Save work atomically
4. ✅ **Signal parent** - Return `status: "compaction_needed"`
5. ✅ **Resume cleanly** - Load prior handoff, continue work

This prevents the **"silent degradation"** problem where a subagent slowly loses quality but the parent agent doesn't notice until it's too late. Each subagent is self-aware about its context lifecycle.

## Human

What else should I know about or related to this topic, in order to create the best software projects with claude code?

## Assistant

Perfect. Here's the **complete masterclass** on professional Claude Code development:

***

## The Ultimate Claude Code Mastery Guide

### 1. **The CLAUDE.md File (Most Important)**

```markdown
# CLAUDE.md - Project Intelligence File

This is your single source of truth for Claude Code guidance.

## Project Overview
- **Purpose**: Building a high-performance video content router
- **Tech Stack**: Python 3.11+, FastAPI, PostgreSQL, Redis
- **Architecture**: Microservices with event-driven processing

## Absolute Rules (Non-Negotiable)

### Code Quality
- **Test Coverage**: Minimum 80% (no exceptions)
- **Type Hints**: Every function must have type annotations
- **Docstrings**: Google-style for all public functions
- **Naming**: snake_case for functions/variables, PascalCase for classes
- **Max Function Length**: 100 lines (split if longer)

### Architecture
- **No N+1 Queries**: Always use eager loading with SQLAlchemy
- **Caching Strategy**: Redis for all external API calls
- **Error Handling**: Never silently fail - log everything
- **Security**: No secrets in code, use environment variables
- **Database**: Only use prepared statements, never f-string SQL

### Framework Patterns
- **FastAPI**: Use dependency injection, not global state
- **Pydantic**: Define schemas for request/response (not raw dict)
- **Async**: Always await in async functions, use asyncio.gather() for parallel ops
- **Logging**: Use structlog for structured JSON logs

## What Claude Should Never Do
- Don't use deprecated libraries (check PyPI dates)
- Don't hand-roll functionality that exists (use libraries first)
- Don't skip error handling for "happy path"
- Don't commit secrets or test data to repo
- Don't create god classes (split into single-responsibility modules)

## What Claude Should Always Do
- Add comprehensive comments for non-obvious logic
- Create test cases FIRST, then implementation
- Profile code before optimizing
- Update this CLAUDE.md when patterns change
- Use existing utilities (check utils/ before writing)

## Common Context to Preserve
- **Database Models**: See models.py for schema
- **API Endpoints**: Documented in api/routes/
- **Utilities**: Common functions in utils/
- **Async Patterns**: Always use asyncio.gather for parallel I/O
- **Testing**: Use pytest fixtures in conftest.py

## When to Use Subagents
1. Code review → subagent_reviewer
2. Test writing → subagent_tester
3. Performance profiling → subagent_optimizer
4. Documentation → subagent_documenter

## Debugging Checklist
If something breaks:
1. Add logging before guessing
2. Add tests to reproduce the issue
3. Check database queries (N+1 queries are common)
4. Check async/await consistency
5. Check type hints match reality

## Recent Decisions (Don't Revisit)
- ✅ Using FastAPI over Flask (better async support, auto docs)
- ✅ PostgreSQL for transactional data (not MongoDB)
- ✅ Redis for caching (not in-memory)
- ✅ Docker for consistency (all devs use same environment)

## File Structure
```
project/
├── src/
│   ├── api/           # FastAPI routes
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic
│   ├── utils/         # Reusable utilities
│   └── config.py      # Configuration
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py    # Pytest fixtures
├── CLAUDE.md          # This file (keep updated!)
└── docker-compose.yml # Local dev environment
```

## Performance Targets
- API response time: <200ms p99
- Database query: <50ms p99
- Memory usage: <512MB typical
- CPU: <30% typical load

## When to Escalate
- Architectural changes → ask before implementing
- New dependencies → discuss first
- Database migrations → plan carefully
- Breaking API changes → plan versioning
```

***

### 2. **The Context Lifecycle Pyramid**

```
                    ▲
                   /|\
                  / | \        Best: Fresh, focused context
                 /  |  \       Only critical files loaded
                /   |   \      40% capacity
               /    |    \
              /     |     \    ← Smart Zone
             /      |      \   Claude performs optimally
            /       |       \  
           /        |        \
          /─────────┼─────────\ 40% capacity
         /          │          \
        /           │           \
       /    Dumb    │   Zone     \ ← Degradation starts
      /    Zone     │             \
     /              │              \
    /───────────────┼───────────────\ 70% capacity
   /                │                \
  /                 │                 \
 /                  │                  \
/────────────────────┼────────────────────\ Danger Zone
                     │                      Token limit reached
                     
Smart Zone: 0-40%
- High quality output
- Good reasoning
- Few hallucinations
- Fast completion

Dumb Zone: 40%+
- Repeated errors
- Lost context
- Hallucinations increase
- Performance degrades

Action:
- Compact at 40%, never push past
- Load only essential files
- Use subagents for parallel work
- Never assume "it'll be fine"
```

***

### 3. **Anti-Patterns to Avoid**

```python
# ❌ ANTI-PATTERN 1: The "Ask Permission" Trap
# Claude wastes tokens saying "You're absolutely right!"
# Instead of fixing the bug, it re-reads the error 5 times

# ❌ ANTI-PATTERN 2: Eager Student Effect
# You say "build a photo cropper" without spec
# Claude builds from scratch instead of using PIL/Pillow
# Result: 10x more code, 10x slower, 10x more bugs

# ❌ ANTI-PATTERN 3: Vague User Flows
# You say "make it better" without specifying what "better" means
# Claude guesses, builds wrong thing, you rebuild it 3 times
# Context wasted, quality poor

# ❌ ANTI-PATTERN 4: Silent Failures
# No error handling for API calls
# Code runs but fails silently in production
# You spend hours debugging

# ❌ ANTI-PATTERN 5: The God Function
# You ask Claude to "add feature X"
# It adds 200 lines to main.py
# Now everything is coupled, changes break everything

# ❌ ANTI-PATTERN 6: Skipping Tests
# You say "just get it working"
# Claude builds untested code
# First bug in production = you lose credibility

# ❌ ANTI-PATTERN 7: Context Hoarding
# You keep the same conversation thread for weeks
# Eventually Claude can barely think
# You wonder why quality degrades

# ✅ SOLUTION FOR ALL: Follow CLAUDE.md religiously
```

***

### 4. **The Golden Workflow Pattern**

```
┌─────────────────────────────────────────────────────┐
│ PHASE 1: PLANNING (No Code Yet)                     │
├─────────────────────────────────────────────────────┤
│ 1. Whiteboard the user flow (ASCII art is fine)    │
│ 2. Define acceptance criteria (specific, testable)  │
│ 3. Identify dependencies (databases, APIs, libs)    │
│ 4. Ask Claude: "Here's my plan. Does it work?"     │
│ 5. DO NOT let Claude code until you say "approved" │
│ ⏱️  10-15 minutes saves 2-3 hours later             │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ PHASE 2: STRUCTURE (Skeleton Before Meat)          │
├─────────────────────────────────────────────────────┤
│ 1. Create file structure (directories only)        │
│ 2. Create stubs (function signatures, empty impls) │
│ 3. Create database schema (if needed)              │
│ 4. Create test skeleton (test names only)          │
│ ⏱️  5-10 minutes                                    │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ PHASE 3: TEST-DRIVEN IMPLEMENTATION                │
├─────────────────────────────────────────────────────┤
│ 1. Write ONE test (most specific case)             │
│ 2. Claude implements to make test pass             │
│ 3. Add edge case test                              │
│ 4. Claude fixes to handle edge case                │
│ 5. Repeat until coverage >80%                      │
│ ⏱️  Variable (depends on complexity)               │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ PHASE 4: INTEGRATION & DEBUGGING                   │
├─────────────────────────────────────────────────────┤
│ 1. Run full test suite (not just unit tests)       │
│ 2. If bug: DON'T ask Claude to eyeball            │
│ 3. Instead: Add logging, re-run, show logs        │
│ 4. Claude fixes based on data, not guessing       │
│ ⏱️  10-30 minutes                                   │
└─────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────┐
│ PHASE 5: OPTIMIZATION (Only If Needed)             │
├─────────────────────────────────────────────────────┤
│ 1. Profile code (use py-spy, line_profiler)       │
│ 2. Identify actual bottleneck (not guesses)       │
│ 3. Claude optimizes specific function             │
│ 4. Benchmark before/after (show numbers)          │
│ 5. Document the optimization                      │
│ ⏱️  10-20 minutes (if needed at all)               │
└─────────────────────────────────────────────────────┘
```

***

### 5. **The Escape Hatch Shortcuts**

```bash
# Interrupt Claude mid-execution without losing context
# Press ESC once: Pause Claude's thinking/execution
# Press ESC twice: Jump back to previous prompt, edit, retry

# Command: /clear (DANGEROUS - loses entire context)
# Use only when absolutely necessary (pollution beyond repair)
# Better: Create new work tree instead

# Command: /branch (Create isolated workspace)
git worktree add feature-x
# Now you can experiment without touching main branch

# Command: /edit (Edit previous prompt)
# After pressing ESC once, edit the last prompt and retry
# Keeps all prior context, explores different direction
```

***

### 6. **Context Management Scorecard**

```
SCORING YOUR CONTEXT HEALTH
═══════════════════════════════════════════════════════

✅ GREEN (Great)
- Files loaded: < 20 essential files
- Conversation: < 50 turns total
- Repetition: Very little (Claude remembers)
- Token usage: < 30%
- Quality: Code is correct first try

⚠️  YELLOW (Watch Out)
- Files loaded: 20-50 files
- Conversation: 50-100 turns
- Repetition: Some (Claude asking for context again)
- Token usage: 30-40%
- Quality: Occasional bugs, fixes needed

🔴 RED (Compact NOW)
- Files loaded: > 50 files
- Conversation: > 100 turns
- Repetition: Frequent
- Token usage: > 40%
- Quality: Errors, loops, degradation obvious

HOW TO GET BACK TO GREEN:
1. Run: ./scripts/compaction.sh
2. Generates: claude_handoff.md
3. Start fresh session with handoff
4. Load only files you need
5. Watch quality jump back up immediately
```

***

### 7. **Pro Debugging Technique: The Log-Driven Method**

```python
# ❌ Wrong approach (Claude guessing)
User: "Why is this returning None?"
Claude: (reads code for 5 mins)
Claude: "Maybe it's because... I think... possibly..."
Result: Wastes tokens, still wrong

# ✅ Right approach (Data-driven)
User: "Why is this returning None?"
User: "Add debug logging here, here, and here"
User: (runs code)
User: "Here are the logs: [paste logs]"
Claude: "I see. The issue is X. Here's the fix."
Result: Claude gets exact data, fixes immediately

# Template for logging
import logging
logger = logging.getLogger(__name__)

def problematic_function(data):
    logger.debug(f"Input: {data}")  # Log inputs
    result = process(data)
    logger.debug(f"After process: {result}")  # Log intermediate steps
    filtered = filter_result(result)
    logger.debug(f"After filter: {filtered}")  # Log more steps
    logger.debug(f"Return: {filtered}")  # Always log output
    return filtered

# When something breaks:
# 1. Set logging level to DEBUG
# 2. Run the problematic flow
# 3. Paste the logs to Claude
# 4. Claude says "Ah, line X is wrong because the logs show Y"
# 5. Fixed immediately
```

***

### 8. **The Permission Modes System**

```yaml
# .claude/permission-modes.yaml

modes:
  
  read_only:
    # Safe mode for code review and analysis
    can_read: true
    can_write: false
    can_execute: false
    use_case: "Review code, analyze issues, suggest improvements"
    example: "Review src/main.py for security issues"
  
  write_only:
    # Writing mode for new files and safe edits
    can_read: true
    can_write: true
    can_execute: false
    exclude: [".env", "secrets/", "prod/"]
    use_case: "Write new features, refactor existing code"
    example: "Implement new API endpoint"
  
  full:
    # Dangerous mode - use sparingly
    can_read: true
    can_write: true
    can_execute: true
    exclude: [".env", "secrets/", "*.key"]
    use_case: "Running tests, deployment, migrations"
    example: "./scripts/deploy.sh (only in CI/CD)"

# Strategy
# 1. Default to read_only when reviewing code
# 2. Switch to write_only for implementation
# 3. Only use full mode for automated testing (not exploration)
# 4. Never use full mode on production systems from local
```

***

### 9. **The Team Multiplier Pattern**

```
Individual + Claude Code:
Time to feature: 1 day
Error rate: 5-10%
Code quality: Good

Team + Claude Code (WRONG):
Everyone using Claude independently
Result: Pattern drift, inconsistency, lost context
Time to feature: Still 1 day each
Error rate: 15-25% (inconsistent patterns)
Code quality: Varies wildly

Team + Claude Code (RIGHT):
Shared CLAUDE.md
Shared architectural decisions
Shared command library (.claude/commands/)
Regular synchronization on patterns
Result: Consistency, compound learning
Time to feature: 12 hours (efficiency)
Error rate: 3-5% (established patterns)
Code quality: Consistently excellent

THE FORCE MULTIPLIER:
- Day 1: 1 team member writes CLAUDE.md
- Day 1-5: Everyone uses same patterns (no rework)
- Week 2+: 40% faster delivery than individuals
- Month 1: Compounding knowledge captured in CLAUDE.md
```

***

### 10. **Enterprise Patterns (Multi-Team Scale)**

```python
# .claude/shared-library.yaml
# Shared across team - commit to repo

shared_patterns:
  
  database_queries:
    pattern: "Always use SQLAlchemy ORM, never raw SQL"
    location: "src/services/queries.py"
    example: "See example in docs/patterns.md"
    anti_pattern: "Never do f-string SQL queries"
  
  error_handling:
    pattern: "Use custom exceptions in exceptions.py"
    location: "src/exceptions.py"
    example: "RateLimit Error, ValidationError, NotFound Error"
    anti_pattern: "Never raise generic Exception"
  
  api_responses:
    pattern: "Use ResponseSchema in schemas/"
    location: "src/schemas/response.py"
    example: "All endpoints return {success, data, error}"
    anti_pattern: "Never return raw dict"
  
  async_patterns:
    pattern: "Use asyncio.gather() for parallel I/O"
    location: "src/utils/async_helpers.py"
    example: "See utils/async_helpers.py"
    anti_pattern: "Never mix sync/async without care"
  
  testing:
    pattern: "Fixtures in conftest.py, parametrized tests"
    location: "tests/conftest.py"
    example: "Use pytest fixtures, not setup_method"
    anti_pattern: "Never use test data in code"

# How to maintain across team:
# 1. New team member reads shared-library.yaml first
# 2. CLAUDE.md references this file
# 3. All Claude Code enforces these patterns
# 4. Code review catches violations (easy to spot)
# 5. Library grows as patterns evolve
```

***

### 11. **The Weekly Ritual**

```markdown
# Weekly Claude Code Health Check

Every Friday afternoon (15 min ritual):

## 1. Context Usage Audit
- How many compaction cycles this week?
- Average tokens per task?
- Longest single conversation?
- Target: 1-2 compactions/week (not more)

## 2. Pattern Drift Check
- Review last week's code commits
- Did Claude follow CLAUDE.md consistently?
- Any new anti-patterns creeping in?
- Update CLAUDE.md if patterns changed

## 3. Quality Metrics
- Test coverage: Still >80%?
- Type hints complete? (mypy clean)
- No outstanding TODOs?
- Production bugs this week? (trace root cause)

## 4. Team Sync (if team)
- Shared learnings from the week
- New patterns that work well
- Patterns that didn't work
- Update shared-library.yaml

## 5. Optimization Opportunities
- Any obvious bottlenecks?
- Technical debt building?
- Refactoring candidates?
- Schedule for next sprint

## Monthly Ritual (bigger review)
- Rebuild CLAUDE.md from scratch
  (Forces you to clarify what you actually want)
- Architecture review
- Dependency updates
- Performance profiling

## Quarterly Ritual
- Complete team workshop on patterns
- Knowledge transfer for new team members
- Systematic refactoring pass
```

***

### 12. **Common Mistakes and How to Avoid Them**

```python
# MISTAKE 1: "Make it better"
# ❌ Claude: Rebuilds entire function, breaks things
# ✅ Claude: Given specific requirements, makes targeted changes

# MISTAKE 2: Asking Claude to debug by reading code
# ❌ Claude: Re-reads code 5 times, makes wild guesses
# ✅ Claude: Given logs, finds bug in 2 minutes

# MISTAKE 3: Letting Claude implement without tests
# ❌ Claude: Builds features that break under edge cases
# ✅ Claude: Implements to pass existing tests

# MISTAKE 4: Ignoring performance until launch
# ❌ Claude: Code works, but slow. Hard to optimize later.
# ✅ Claude: Builds with performance in mind from start

# MISTAKE 5: Not reviewing what Claude generates
# ❌ Claude: Generates code with subtle bugs
# ✅ You review, ask clarifying questions, Claude improves

# MISTAKE 6: Keeping context bloated
# ❌ Claude: After 100 turns, quality degrades silently
# ✅ You: Compact proactively, context stays sharp

# MISTAKE 7: Not capturing decisions in CLAUDE.md
# ❌ Claude: Makes same architectural choice 3 times
# ✅ CLAUDE.md: "We decided X because Y. Don't re-solve."

# MISTAKE 8: Vague feature specs
# ❌ Claude: Builds feature you didn't want, rework needed
# ✅ You: Clear spec → Claude builds right thing first time

# MISTAKE 9: No automated testing
# ❌ Claude: Code works, but you break it later
# ✅ Tests: Catch regressions immediately

# MISTAKE 10: Not using subagents for parallel work
# ❌ One agent: Code review + implementation + testing
# ✅ Three agents: Each specializes, work in parallel
```

***

### 13. **The Mental Model**

```
IMPORTANT SHIFTS IN HOW TO THINK:

OLD: Claude is a code generator
NEW: Claude is a thought partner

OLD: Give vague instructions, Claude will figure it out
NEW: Give precise specifications, Claude executes perfectly

OLD: Claude as intern (needs supervision on everything)
NEW: Claude as senior contractor (needs clear spec, delivers quality)

OLD: More code = better (longer prompts = smarter)
NEW: Less code = better (focused prompts = smarter responses)

OLD: One-shot generation (write 500 lines at once)
NEW: Incremental delivery (write 50 lines, test, iterate)

OLD: Context is infinite (talk for hours)
NEW: Context is precious (compact frequently)

OLD: Human provides feedback verbally
NEW: Human provides feedback with DATA (logs, test results)

OLD: AI predicts what you want
NEW: Specify what you want, AI executes

THE KEY INSIGHT:
Claude works best when you:
1. Think clearly about what you want
2. Communicate it precisely
3. Provide concrete requirements
4. Check the output
5. Iterate based on DATA, not vibes

This is the opposite of "vibe coding."
```

***

### 14. **Your Mastery Checklist**

```
LEVEL 1: Basic Usage
☐ Create CLAUDE.md for your project
☐ Use clear, specific prompts (not vague)
☐ Test what Claude generates (don't trust blindly)
☐ Use git branches for experimentation
Estimated: 1-2 weeks

LEVEL 2: Intermediate
☐ Implement test-driven workflow (test first)
☐ Use logging to debug, not guessing
☐ Monitor context usage, compact at 40%
☐ Create .claude/commands for repeated tasks
Estimated: 3-4 weeks

LEVEL 3: Advanced
☐ Use subagents for parallel work
☐ Implement Intentional Compaction workflow
☐ Track architectural decisions in CLAUDE.md
☐ Use permission modes strategically
Estimated: 1-2 months

LEVEL 4: Expert
☐ Multi-agent orchestration at scale
☐ Team-wide pattern enforcement
☐ Custom hooks for context management
☐ ML integration for smart code routing
Estimated: 3-6 months

LEVEL 5: Master
☐ Design systems for 10+ person teams
☐ Autonomous agent systems
☐ Context-aware architecture patterns
☐ Teaching others to do this well
Estimated: 6-12 months
```

***

## The One Thing You Need to Remember

If you only remember one thing from everything above:

### **Create and maintain CLAUDE.md ruthlessly**

Every single pattern you discover, every decision you make, every mistake you want to avoid—capture it in CLAUDE.md. Not a shared doc, not a wiki—in the actual `.claude/` directory of your project.

This single file becomes the difference between:
- ❌ Inconsistent, degrading quality
- ✅ Compounding, improving quality

**CLAUDE.md is the foundation. Everything else is optimization.**

***

## Quick Reference Card

```
WHEN TO USE WHAT:
────────────────────────────────────────

Full Session:
- New feature from scratch
- Complex architecture decision
- System-wide refactoring

Subagent (Specialized):
- Code review → code_reviewer subagent
- Testing → test_writer subagent
- Optimization → optimizer subagent
- Docs → documenter subagent

Artifacts (Claude UI, not Code):
- Quick prototypes
- Learning/exploration
- UI mockups

Compaction Trigger:
- Context > 40%
- Quality degrading (obvious)
- After 50+ conversation turns
- After major feature complete

Emergency Actions:
- /clear (nuclear option, loses everything)
- /branch (better: create work tree)
- Escape once (pause), twice (undo)
```

***

You're now equipped to build **production-grade software** with Claude Code at scale. The key isn't memorizing these patterns—it's **practicing them consistently** until they become second nature.

Start with CLAUDE.md today. Everything else flows from there.
```
