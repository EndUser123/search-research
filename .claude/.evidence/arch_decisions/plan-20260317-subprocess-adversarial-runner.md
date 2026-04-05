# Implementation Plan: Subprocess-Based Adversarial Runner

**Status:** ✅ Phase 1 Complete | Phase 2 In Progress | Phase 3-4 Pending
**Created:** 2026-03-17
**Author:** /arch
**Related ADR:** ADR-20260317-subprocess-adversarial-runner.md

**Progress Tracking:**
- ✅ TASK-001: Create Agent Script Base Template
- ✅ TASK-002: Create 7 Standalone Agent Scripts
- ✅ TASK-003: Implement adversarial_runner.py
- ✅ TASK-004: Update plan-workflow SKILL.md
- 📋 TASK-004A: Add Markdown Summary Enhancement (Optional)
- ✅ TASK-005: Add CLI Argument Parser (Completed in TASK-003)
- ⏳ TASK-006: Create Test Infrastructure
- ⏳ TASK-007: Create Comparison Validation
- ⏳ TASK-008: Create Fallback Mechanism
- ⏳ TASK-009: Migration Path and Rollout

---

## Overview

Replace Agent tool-based adversarial review with subprocess-based runner to eliminate context bloat during plan-workflow review operations.

**Context Impact:** Reduces adversarial review from ~30KB to ~1KB (97% reduction)

---

## Phase 1: Infrastructure Creation

### TASK-001: Create Agent Script Base Template

**File:** `P:\.claude\skills\plan-workflow\agents\__init__.py`

**Purpose:** Shared infrastructure for all agent scripts

**Implementation:**
```python
#!/usr/bin/env python3
"""Base class for adversarial review agents."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict


class AdversarialAgent:
    """Base class for adversarial review agents."""

    def __init__(self, plan_path: str):
        """Initialize agent with plan path."""
        self.plan_path = Path(plan_path)
        self.plan_content = self._read_plan()

    def _read_plan(self) -> str:
        """Read plan content from file."""
        try:
            return self.plan_path.read_text(encoding="utf-8")
        except Exception as e:
            return self._error_response(f"Failed to read plan: {e}")

    def _error_response(self, message: str) -> str:
        """Create error response JSON."""
        return json.dumps({
            "status": "ERROR",
            "error": message,
            "agent": self.__class__.__name__,
        })

    def run(self) -> str:
        """Run the agent analysis. Override in subclasses."""
        raise NotImplementedError

    def main(self) -> None:
        """Entry point for subprocess execution."""
        try:
            result = self.run()
            print(result)
        except Exception as e:
            print(self._error_response(f"Agent crashed: {e}"))
```

**Acceptance Criteria:**
- [ ] Base template file created
- [ ] Passes lint (pylint, mypy if applicable)
- [ ] Has docstring and type hints

---

### TASK-002: Create Standalone Agent Scripts

**Files to Create:**

| Agent | Script File | Source Spec |
|-------|------------|-------------|
| compliance | `adversarial_compliance.py` | `.claude/agents/adversarial-compliance.md` |
| quality | `adversarial_quality.py` | `.claude/agents/adversarial-quality.md` |
| security | `adversarial_security.py` | `.claude/agents/adversarial-security.md` |
| testing | `adversarial_testing.py` | `.claude/agents/adversarial-testing.md` |
| qa | `adversarial_qa.py` | `.claude/agents/qa.md` |
| code-critic | `code_critic.py` | `.claude/agents/code-critic.md` |
| critic | `adversarial_critic.py` | `.claude/agents/adversarial-critic.md` |

**Location:** `P:\.claude\skills\plan-workflow\agents\`

**Template Pattern (compliance example):**

```python
#!/usr/bin/env python3
"""Adversarial compliance review agent."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from __init__ import AdversarialAgent


class AdversarialComplianceAgent(AdversarialAgent):
    """Adversarial compliance review specialist."""

    def run(self) -> str:
        """Run compliance analysis and return JSON findings."""
        findings = []

        # Analysis logic (extracted from agent spec)
        # ... actual analysis code ...

        return json.dumps({
            "status": "OK",
            "agent": "adversarial-compliance",
            "findings": findings,
        })


def main():
    """Entry point for subprocess execution."""
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "ERROR",
            "error": "Usage: adversarial_compliance.py <plan_path>"
        }))
        return

    agent = AdversarialComplianceAgent(sys.argv[1])
    agent.main()


if __name__ == "__main__":
    main()
```

**Script Logic Requirements:**
- Extract plan content from file
- Apply agent-specific analysis (from agent spec)
- Return JSON with format: `{"status": "OK", "findings": [...]}`
- Handle all exceptions and return error JSON

**Acceptance Criteria:**
- [ ] All 7 agent scripts created
- [ ] Each script reads plan from file path argument
- [ ] Each script outputs valid JSON
- [ ] Error handling returns JSON (not exceptions)
- [ ] Scripts are executable (chmod +x)

---

### TASK-003: Implement adversarial_runner.py

**File:** `P:\.claude\skills\plan-workflow\lib\adversarial_runner.py`

**Key Implementation Requirements:**

1. **Multi-terminal isolation:**
```python
from __lib.runtime_env import get_terminal_id
from __lib.state_paths import get_terminal_state_dir

# Get terminal ID for terminal-scoped state
terminal_id = get_terminal_id()
if terminal_id:
    STATE_DIR = get_terminal_state_dir(terminal_id) / "adversarial-reviews"
else:
    STATE_DIR = Path(".claude/state/adversarial-reviews")  # Fallback
```

2. **Agent definitions:**
```python
AGENTS_FULL = [
    "compliance",
    "quality",
    "security",
    "testing",
    "qa",
    "critic",
]

AGENTS_LIGHT = [
    "compliance",
    "security",
    "qa",
]

# Map short names to script files
AGENT_SCRIPTS = {
    "compliance": "adversarial_compliance.py",
    "quality": "adversarial_quality.py",
    "security": "adversarial_security.py",
    "testing": "adversarial_testing.py",
    "qa": "adversarial_qa.py",
    "critic": "adversarial_critic.py",
}
```

3. **Error handling:**
```python
def run_agent(agent: str, plan_path: str) -> Dict[str, Any]:
    """Run a single agent script as subprocess."""
    script_path = AGENTS_DIR / AGENT_SCRIPTS[agent]

    try:
        proc = subprocess.run(
            [sys.executable, str(script_path), plan_path],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return {
            "agent": agent,
            "status": "ERROR",
            "error": "Timeout after 60s",
        }
    except FileNotFoundError:
        return {
            "agent": agent,
            "status": "ERROR",
            "error": f"Script not found: {script_path}",
        }

    if proc.returncode != 0:
        return {
            "agent": agent,
            "status": "ERROR",
            "error": proc.stderr.strip()[:2000],
        }

    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        return {
            "agent": agent,
            "status": "ERROR",
            "error": f"Invalid JSON: {e}",
            "raw": proc.stdout[:500],
        }
```

4. **Two-phase execution:**
```python
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("plan_path")
    parser.add_argument("--mode", choices=["full", "light"], default="full")
    args = parser.parse_args()

    # Phase 1: Run agents
    agents = AGENTS_FULL if args.mode == "full" else AGENTS_LIGHT
    payloads = []

    for agent in agents:
        p = run_agent(agent, args.plan_path)
        save_agent_output(agent, p)
        payloads.append(p)

    # Phase 2: Meta-analysis (full mode only)
    if args.mode == "full":
        meta_analysis = run_meta_analysis(args.plan_path)
        # Apply calibration if available
        if meta_analysis.get("calibration"):
            payloads = apply_calibration(payloads, meta_analysis["calibration"])

    # Phase 3: Summarize
    summary = summarize_findings(payloads)
    print(json.dumps(summary))
```

**Acceptance Criteria:**
- [ ] Runner script created with proper multi-terminal isolation
- [ ] Supports --mode flag (full/light)
- [ ] Implements two-phase execution (agents + meta-analysis)
- [ ] All error cases return JSON (never exceptions)
- [ ] Outputs compact summary to stdout
- [ ] Creates output directory if needed

---

## Phase 2: Skill Integration

### TASK-004: Update plan-workflow SKILL.md

**File:** `P:\.claude\skills\plan-workflow\SKILL.md`

**Changes Required:**

1. **Replace Agent tool pattern (lines 784-802):**

Current:
```markdown
# Make all 7 Agent calls in ONE message - they run in parallel automatically
Agent(subagent_type="adversarial-compliance", prompt=review_prompt, description="...")
Agent(subagent_type="adversarial-performance", prompt=review_prompt, description="...")
...
```

New:
```markdown
# Run adversarial review via subprocess runner (context-efficient)
Bash(
    command="cd P && python .claude/skills/plan-workflow/lib/adversarial_runner.py \"{{plan_path}}\" --mode=full"
    save_result_to=adversarial_summary
)

# Parse summary JSON
- set: adversarial_status = {{adversarial_summary.status}}
- set: total_findings = {{adversarial_summary.total_findings}}
- set: high_findings = {{adversarial_summary.high_findings}}
```

2. **Add "show details" workflow:**

```markdown
# On-demand access to full findings
Bash(
    command="cd P && python .claude/skills/plan-workflow/lib/adversarial_runner.py \"{{plan_path}}\" --show=security"
    save_result_to=security_details
)
```

**Acceptance Criteria:**
- [ ] SKILL.md updated with Bash pattern
- [ ] Old Agent tool pattern removed/commented
- [ ] New pattern includes --mode flag support
- [ ] On-demand file reading pattern documented
- [ ] Works with both review and quick-review commands

---

### TASK-004A: Add Markdown Summary Enhancement (Optional)

**Purpose:** Improve UX with human-readable summaries alongside JSON artifacts

**Files to Modify:**
- `P:\.claude\skills\plan-workflow\lib\adversarial_runner.py`

**Implementation:**

1. **Add markdown_summary() function:**
```python
def markdown_summary(plan_path: str, summary: Dict[str, Any]) -> str:
    """Generate Markdown summary from JSON summary."""
    plan_name = Path(plan_path).name
    lines = []

    lines.append(f"# Adversarial Review Summary for `{plan_name}`")
    lines.append("")
    lines.append(f"- Status: **{summary['status']}**")
    lines.append(f"- Total findings: {summary['total_findings']}")
    lines.append(f"- High severity findings: {summary['high_findings']}")
    lines.append(f"- Showing first {summary['shown_findings']} findings")
    lines.append("")

    if summary["errors"]:
        lines.append("## Agent Errors")
        for e in summary["errors"]:
            lines.append(f"- **{e['agent']}**: {e['error']}")
        lines.append("")

    if summary["findings"]:
        lines.append("## Findings")
        for f in summary["findings"]:
            lines.append(f"### [{f['severity']}] {f['agent']}: {f['title']}")
            if f["summary"]:
                lines.append("")
                lines.append(f"{f['summary']}")
            lines.append("")

    return "\n".join(lines)
```

2. **Add write_markdown() function:**
```python
def write_markdown(plan_path: str, summary: Dict[str, Any]) -> Path:
    """Write Markdown summary to hooks plans directory."""
    HOOKS_PLAN_DIR = ROOT / ".claude" / "hooks" / "plans"
    HOOKS_PLAN_DIR.mkdir(parents=True, exist_ok=True)

    plan = Path(plan_path)
    base = plan.stem  # e.g., plan-20260317-s-confidence-turn-taking
    out_path = HOOKS_PLAN_DIR / f"{base}-adversarial-summary.md"

    md = markdown_summary(plan_path, summary)
    with out_path.open("w", encoding="utf-8") as f:
        f.write(md)

    return out_path
```

3. **Update main() to include markdown_path in summary:**
```python
def main():
    # ... existing code ...

    summary = summarize_findings(payloads)
    md_path = write_markdown(args.plan_path, summary)

    # Add markdown_path to summary
    summary["markdown_path"] = str(md_path)
    print(json.dumps(summary))
```

4. **Update SKILL.md pattern to surface markdown_path:**
```markdown
- say: |
    Adversarial review complete.

    Status: {{adversarial_summary.status}}
    Total findings: {{adversarial_summary.total_findings}}
    High severity: {{adversarial_summary.high_findings}}

    Markdown summary file:
    {{adversarial_summary.markdown_path}}

    (Open that file in your editor to browse full details.)
```

**Benefits:**
- Human-readable artifact alongside JSON
- Persistent reference in `.claude/hooks/plans/` (consistent with plan location)
- Path-only reference keeps context small
- No need to invoke `--show` flag for basic review

**Acceptance Criteria:**
- [ ] `markdown_summary()` function generates formatted Markdown
- [ ] `write_markdown()` writes to `.claude/hooks/plans/<basename>-adversarial-summary.md`
- [ ] Summary JSON includes `markdown_path` field
- [ ] SKILL.md updated to display markdown_path
- [ ] Markdown file is well-formatted and readable

**Dependencies:**
- Requires TASK-003 (adversarial_runner.py) completion
- Optional enhancement, not blocking for core functionality

---

### TASK-005: Add CLI Argument Parser

**File:** `P:\.claude\skills\plan-workflow\lib\adversarial_runner.py`

**Implementation:**
```python
def main():
    parser = argparse.ArgumentParser(
        description="Run adversarial review agents as subprocesses"
    )
    parser.add_argument("plan_path", help="Path to plan file")
    parser.add_argument(
        "--mode",
        choices=["full", "light"],
        default="full",
        help="Review mode: full (7 agents) or light (3 agents)"
    )
    parser.add_argument(
        "--show",
        choices=["compliance", "quality", "security", "testing", "qa", "critic"],
        help="Show detailed findings for specific agent"
    )
    args = parser.parse_args()

    if args.show:
        show_findings(args.show)
        return

    # Normal execution
    run_review(args.plan_path, args.mode)
```

**Acceptance Criteria:**
- [ ] argparse imported and configured
- [ ] --mode flag selects agent set
- [ ] --show flag displays specific agent findings
- [ ] Help text is clear and accurate

---

## Phase 3: Testing & Validation

### TASK-006: Create Test Infrastructure

**File:** `P:\..claude\skills\plan-workflow\tests\test_adversarial_runner.py`

**Test Cases:**

1. **Test subprocess invocation:**
```python
def test_runner_invocation():
    """Test that runner can be invoked via Bash."""
    # Create test plan
    plan_path = create_test_plan()
    # Run via Bash
    result = Bash(
        command=f"cd P && python .claude/skills/plan-workflow/lib/adversarial_runner.py {plan_path}"
    )
    # Verify JSON output
    assert "status" in result
```

2. **Test terminal isolation:**
```python
def test_multi_terminal_isolation():
    """Test that concurrent runs don't corrupt each other."""
    # Run two reviews simultaneously
    # Verify separate state directories
    pass
```

3. **Test error handling:**
```python
def test_agent_timeout():
    """Test that agent timeouts are handled gracefully."""
    # Create agent that sleeps too long
    # Verify timeout returns error JSON
    pass
```

4. **Test context reduction:**
```python
def test_context_reduction():
    """Verify subprocess runner uses less context than Agent tool."""
    # Measure context with Agent tool (baseline)
    # Measure context with subprocess runner
    # Assert subprocess uses < 5% of baseline
    pass
```

**Acceptance Criteria:**
- [ ] Test file created with 4+ test cases
- [ ] Tests pass with pytest
- [ ] Coverage >80% for runner code

---

### TASK-007: Create Comparison Validation

**File:** `P:\.claude\skills\plan-workflow\tests\test_runner_comparison.py`

**Purpose:** Verify subprocess runner produces equivalent results to Agent tool

**Implementation:**
```python
def test_equivalent_results():
    """Run same plan with both methods, compare outputs."""
    plan_path = create_test_plan()

    # Method 1: Agent tool (baseline)
    agent_result = run_with_agent_tool(plan_path)

    # Method 2: Subprocess runner
    runner_result = run_with_subprocess_runner(plan_path)

    # Compare
    assert agent_result["total_findings"] == runner_result["total_findings"]
    # More comparisons...
```

**Acceptance Criteria:**
- [ ] Comparison test created
- ] Both methods produce equivalent findings
- [ ] Subprocess runner has no false negatives
- [ ] Subprocess runner has no false positives

---

## Phase 4: Rollback & Migration

### TASK-008: Create Fallback Mechanism

**Purpose:** Graceful degradation if subprocess runner fails

**Implementation in SKILL.md:**
```python
# Try subprocess runner first
Bash(
    command="cd P && python .claude/skills/plan-workflow/lib/adversarial_runner.py \"{{plan_path}}\" --mode=full"
    save_result_to=adversarial_summary
)

# Fallback: Check if runner failed
- if: adversarial_summary.status == "ERROR"
    - say: "Subprocess runner failed, falling back to Agent tool..."
    - # Use old Agent tool pattern as fallback
    - Agent(adversarial-compliance, ...)
```

**Acceptance Criteria:**
- [ ] Fallback logic documented in SKILL.md
- [ ] Tests verify fallback activates on failure
- [ ] No circular fallback (fallback doesn't fail back to fallback)

---

### TASK-009: Migration Path

**Rollout Strategy:**

1. **Week 1:** Create infrastructure (TASK-001 to TASK-003)
2. **Week 2:** Integrate and test (TASK-004 to TASK-007)
3. **Week 3:** Deploy with fallback (TASK-008)
4. **Week 4:** Monitor and validate

**Acceptance Criteria:**
- [ ] All tasks completed
- [ ] Tests pass
- [ ] Documentation updated
- [] CKS ingest completed (learn from this implementation)

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Agent scripts don't exist | HIGH | HIGH | Create scripts from agent specs |
| Multi-terminal race conditions | MEDIUM | HIGH | Use state_paths.py infrastructure |
| Subprocess timeout issues | MEDIUM | MEDIUM | 60s timeout per agent |
| JSON schema drift | LOW | MEDIUM | Schema validation with graceful degradation |
| Lost conversational debugging | LOW | LOW | Persistent files enable post-hoc analysis |

---

## Success Criteria

1. **Functional:** Subprocess runner produces equivalent results to Agent tool
2. **Context Reduction:** Adversarial review uses <5% of baseline context
3. **Multi-Terminal Safe:** Concurrent reviews don't corrupt state
4. **Error Resilient:** All error cases return JSON, never exceptions
5. **Well-Tested:** Test coverage >80% for new code

---

## Next Steps

1. Review and approve this implementation plan
2. Execute tasks sequentially (TASK-001 through TASK-009)
3. Validate against success criteria
4. Deploy with fallback mechanism
5. Monitor and iterate based on feedback

---

**Dependencies:**
- Existing agent specifications in `.claude/agents/`
- Existing state_paths.py infrastructure
- Existing adversarial_review_coordinator.py (for reference)

**Blocked By:**
- None - ready to start Phase 1
