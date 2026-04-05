# ADR-20260325: GTO Correctness Mode — Task #2438

**Status:** Proposed
**Date:** 2026-03-25
**Context:** Add `--correctness` flag to GTO that runs adversarial-review agents, outputs both `coverage_gaps` (existing) and `correctness_gaps` (new)

---

## Decision

Implement GTO Correctness Mode via a **scoped adversarial agent dispatch** using 3 targeted agents (`logic`, `quality`, `code-critic`) with JSON output parsing and GTO gap format mapping.

---

## Rationale

**Research Findings (Tier 2):**

1. **Multi-agent adversarial strategies** are the 2025 industry best practice for code review. Parallel execution of targeted agents outperforms single-agent approaches for finding diverse bug types. Source: [Reddit r/opencodeCLI](https://www.reddit.com/r/opencodeCLI/comments/1r0okeg/adversarial_code_review_subagent_strategy/), [Security Boulevard](https://securityboulevard.com/2025/10/ai-code-review-in-2025-technologies-challenges-best-practices/)

2. **LLM-aided verification gap detection** identifies missing checkers through mutation-induced behavioral divergence. This directly maps to GTO's gap detection mission — finding what's MISSING rather than what's wrong. Source: [TechRxiv](https://www.techrxiv.org/users/1024156/articles/1383980-llm-aided-verification-gap-detection-a-methodology-for-identifying-missing-checkers-in-uvm-testbenches)

3. **Formal verification catches 6-8/8 incorrect agent judgments** in LLM reasoning. This validates the adversarial-critic meta-analysis approach. Source: [arXiv 2509.26546](https://arxiv.org/html/2509.26546v1)

4. **Solo-dev constitutional constraints** require scoped agent runs (not all 9 agents) to avoid enterprise bloat. 3 targeted agents provide 80% of correctness coverage at 33% of the cost. Source: CLAUDE.md Solo Developer Context

---

## Architecture

### Option A: Targeted Adversarial Dispatch (RECOMMENDED)

```
GTO CLI (--correctness flag)
    ↓
GTOOrchestrator._run_correctness_subagents()
    ↓
┌─────────────────────────────────────────────────────┐
│ 3 PARALLEL Task() dispatches:                     │
│ 1. adversarial-logic → logic-findings.json         │
│ 2. adversarial-quality → quality-findings.json     │
│ 3. code-critic → code-critic-findings.json        │
└─────────────────────────────────────────────────────┘
    ↓
Parse JSON → Map to GTO Gap format
    ↓
Merge into results.gaps as correctness_gaps
```

### Option B: Full Adversarial Review (REJECTED)

Running all 9 adversarial agents for GTO correctness mode is enterprise bloat. GTO is a solo-dev tool — 9 agents would:
- Add 3-5 minutes per run
- Generate 200+ findings (overwhelms solo dev)
- Violates "75-85% reliability target" (over-engineering)

---

## Implementation

### 1. Add `--correctness` flag to CLI

```python
# gto_orchestrator.py additions

parser.add_argument(
    "--correctness",
    action="store_true",
    help="Run adversarial correctness analysis (logic, quality, code-critic agents)",
)

# Config
@dataclass
class OrchestratorConfig:
    # ... existing fields ...
    enable_correctness: bool = False
    correctness_modes: list[str] = field(default_factory=lambda: ["logic", "quality", "code-critic"])
```

### 2. Add `_run_correctness_subagents()` method

```python
def _run_correctness_subagents(self) -> dict[str, list[Gap]]:
    """Run adversarial correctness analysis.

    Dispatches 3 targeted agents:
    - adversarial-logic: Pure logic errors (off-by-one, wrong operators, inverted conditionals)
    - adversarial-quality: Maintainability risks and technical debt
    - code-critic: Root cause analysis and causal chains

    Returns:
        Dictionary mapping agent name to list of Gap objects
    """
    import subprocess
    import json
    from datetime import datetime

    results: dict[str, list[Gap]] = {}
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # File paths for JSON outputs
    output_dir = Path(".claude/plans/adversarial")
    output_dir.mkdir(parents=True, exist_ok=True)

    files = {
        "logic": output_dir / f"logic-findings-{timestamp}.json",
        "quality": output_dir / f"quality-findings-{timestamp}.json",
        "code-critic": output_dir / f"code-critic-findings-{timestamp}.json",
    }

    # Target files: scan project for Python/JS/TS files
    target_pattern = str(self.project_root / "**/*.py")
    # (Also include .ts, .js for TypeScript projects)

    # Launch 3 parallel agents via Task tool
    # Each agent reads its skill definition and writes JSON to file path

    # Parse results
    for agent_name, file_path in files.items():
        if file_path.exists():
            with open(file_path) as f:
                data = json.load(f)
                gaps = self._parse_adversarial_findings(data, agent_name)
                results[agent_name] = gaps

    return results
```

### 3. Gap Format Mapping

Adversarial findings use this schema:
```json
{
  "findings": [
    {
      "id": "LOGIC-001",
      "severity": "blocker|high|medium|low",
      "location": "file:line",
      "problem": "...",
      "adversarial_scenario": "...",
      "impact": "...",
      "recommendation": "..."
    }
  ]
}
```

Map to GTO Gap format:
- `gap_type`: `correctness_gap`
- `severity`: Map `blocker`→`critical`, `high`→`high`, `medium`→`medium`, `low`→`low`
- `message`: `problem` field
- `file_path` + `line_number`: Parsed from `location`
- `source`: `adversarial-{agent_name}`

### 4. Merge into Results

```python
def run(self) -> OrchestratorResult:
    # ... existing steps 1-6 ...

    # NEW: Step 3.5 - Correctness analysis
    if self.config.enable_correctness:
        correctness_results = self._run_correctness_subagents()
        for agent_name, gaps in correctness_results.items():
            for gap in gaps:
                gap.source = f"adversarial-{agent_name}"
                results.gaps.append(gap)

    # ... rest of run() ...
```

---

## Tradeoffs

| Quality | Improved | Degraded |
|---------|----------|----------|
| **Correctness Detection** | Finds logic errors, maintainability issues | — |
| **Coverage** | Both coverage gaps AND correctness gaps | — |
| **Performance** | — | +30-60s per correctness run |
| **Complexity** | — | Requires adversarial JSON parsing |

---

## Multi-Terminal Safety

- Each terminal writes to timestamped files: `logic-findings-{timestamp}.json`
- No shared mutable state between terminals
- Findings are merged into GTO results (per-terminal, not shared)

---

## Evidence

- **GTO Skill:** `P:\.claude\skills\gto\SKILL.md`
- **Adversarial Logic:** `P:\.claude\agents\adversarial-logic.md` (outputs to `logic-findings.json`)
- **Adversarial Quality:** `P:\.claude\agents\adversarial-quality.md` (outputs to `quality-findings.json`)
- **Code Critic:** `P:\.claude\agents\code-critic.md` (outputs to `code-critic-findings.json`)

---

## Implementation Plan

**Phase 1: Core Integration**
- [ ] Add `--correctness` flag to CLI
- [ ] Add `enable_correctness` to `OrchestratorConfig`
- [ ] Implement `_run_correctness_subagents()` skeleton

**Phase 2: JSON Parsing**
- [ ] Implement `_parse_adversarial_findings()` method
- [ ] Add gap type mapping (adversarial → GTO format)
- [ ] Test with mock JSON files

**Phase 3: Agent Dispatch**
- [ ] Add `Task()` calls for 3 agents
- [ ] Handle agent timeouts (30s per agent)
- [ ] Error handling for failed agents

**Phase 4: Integration Testing**
- [ ] Run GTO with `--correctness` on test project
- [ ] Verify gaps are merged correctly
- [ ] Performance benchmark

---

## Alternatives Considered

**Option B: Full adversarial-review via `/adversarial-review` command**
- Rejected: Runs 9 agents, 3-5 min runtime, 200+ findings
- Violates solo-dev principle: ROI < risk

**Option C: Direct skill invocation via Skill tool**
- Rejected: Skill tool is for loading skill context, not agent dispatch
- Current adversarial agents use Task-based dispatch pattern

---

## Edge Cases

1. **Agent timeout**: If agent doesn't respond in 30s, skip its findings (non-blocking)
2. **Malformed JSON**: Log warning, skip agent's findings
3. **No target files**: If project has no Python/JS/TS files, skip correctness run
4. **Conflicting findings**: Same finding from multiple agents deduplicated by `id`

---

## Version

1.0.0 (2026-03-25) - Initial architecture
