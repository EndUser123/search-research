# Review Bundle: /adversarial-review Skill
**Generated**: 2026-03-26T18:35:00Z
**Scope**: P:/.claude/skills/adversarial-review/
**File Count**: 1 file (SKILL.md only)
**Execution Mode**: single-agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name**: adversarial-review
- **Version**: (not in frontmatter)
- **Category**: analysis
- **Trigger**: `/adversarial-review [files] [--mode <perspectives>] [--depth <light|standard|deep>]`
- **Aliases**: `/ar`

### Domain & Purpose
Parallel adversarial code review system dispatching 7 specialist agents simultaneously (security, performance, compliance, quality, testing, logic, failure-modes), then running adversarial-critic as sequential meta-analysis to synthesize findings. Each agent writes JSON findings to `.claude/state/`; the critic aggregates them.

### Environment
- **OS**: Windows 11 Pro
- **Shell**: Bash
- **Primary Language**: Python/markdown
- **Key Integration**: Subagent dispatch via Agent tool

---

## 2. ARCHITECTURE OVERVIEW

```
                          ┌───────────────────────────────────────┐
                          │          /adversarial-review           │
                          │  Parallel 7-agent dispatch →         │
                          │  Sequential meta-analysis            │
                          └──────────────┬────────────────────────┘
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         ▼                               ▼                               ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│ adversarial-security │  │adversarial-perf    │  │adversarial-quality │
│ adversarial-testing  │  │adversarial-logic   │  │adversarial-failure │
│ adversarial-compliance│  │ code-critic        │  │ qa-engineer         │
└─────────┬───────────┘  └─────────┬───────────┘  └─────────┬───────────┘
          │                        │                        │
          └────────────────────────┴────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  adversarial-critic      │
                    │  (sequential meta-     │
                    │   analysis)            │
                    └─────────────────────────┘
```

### Agent Mapping

| Mode | Agent | Best for |
|------|-------|---------|
| security | adversarial-security | code & plans |
| performance | adversarial-performance | code |
| compliance | adversarial-compliance | code & plans |
| quality | adversarial-quality | code |
| testing | adversarial-testing | code & plans |
| logic | adversarial-logic | plans |
| failure-modes | adversarial-failure-modes | plans |
| rca | code-critic | code |
| qa | qa-engineer | code |
| all (default) | all 9 above | comprehensive |

---

## 3. EXECUTION AND DATA FLOW

### Step 1: Parse Input & Detect Target
- Extract `files` from first argument (optional)
- Extract `--mode` comma-separated list (default: all)
- Extract `--depth`: light|standard|deep (default: standard)
- If no files: auto-detect via `git diff --name-only HEAD | grep -E '\.(py|ts|js|go|rs)$'`

### Step 2: Parallel Agent Dispatch
- Launch ALL selected agents in ONE message (critical)
- Each agent writes JSON findings to `.claude/state/adversarial-{type}-[datetime].json`

### Step 3: Sequential Meta-Analysis
- AFTER all parallel agents complete
- adversarial-critic reads 7 JSON files
- Performs: consensus detection, blind spot detection, bias detection, contradiction detection, quality calibration
- Saves meta-findings to `.claude/state/adversarial-critic-[datetime].json`

### Step 4: Present Results
- GTO v2 RSN format with adversarial domains
- 7 sections: Security, Performance, Quality, Testing, Compliance, Root Cause, Meta-Analysis
- Mandatory terminator: `0 - Do ALL Recommended Next Steps`

---

## 4. COMPONENT INVENTORY

### Files
| File | Purpose |
|------|---------|
| SKILL.md | Complete skill definition (302 lines), dispatch protocol, output schema |

### Output Schema (JSON)
```json
{
  "findings": [{
    "id": "UNIQUE-ID",
    "severity": "CRITICAL|HIGH|MEDIUM|LOW",
    "triage": "nit|fix_before_merge|pre-existing",
    "title": "Short title",
    "description": "Detailed explanation",
    "evidence": {
      "code_excerpt": "relevant code",
      "file_path": "path/to/file.py",
      "line_number": 123,
      "proof": "why this is a problem"
    },
    "impact": {
      "business_consequence": "what breaks",
      "user_visible": true
    },
    "recommendation": {
      "action": "what to do",
      "code_fix": "example fix"
    },
    "confidence": 0.95
  }]
}
```

### State File Naming
- Pattern: `.claude/state/adversarial-{type}-YYYYMMDD-HHMMSS.json`
- Types: security, performance, compliance, quality, testing, logic, failure-modes, critic

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars
1. **Parallel dispatch** — All specialist agents launch simultaneously in single message
2. **Sequential meta-analysis** — adversarial-critic runs AFTER all parallel agents complete
3. **Disk-based findings** — Agents write JSON, critic reads and synthesizes
4. **Token-efficient prompts** — Reference SKILL.md schema, don't include inline
5. **Path-based passing** — Pass file paths, not contents (agents read files themselves)

### Constitutional Filter
**Remove findings containing prohibited patterns:**
- Continuous monitoring / always-on tracking (without idle timeout)
- Self-healing / auto-correction without approval
- Team coordination gates (solo dev environment)
- Enterprise deployment pipelines for local dev

**Allowed:**
- AI agent parallelism and coordination
- Observability of AI agent outputs
- Findings requiring Director approval before action

### Things That Must NOT Change
- Parallel → Sequential ordering (must wait for all agents before critic)
- JSON output schema (other tools depend on it)
- State file naming convention (adversarial-critic depends on glob pattern)

---

## 6. KNOWN ISSUES

No known issues. Single-file skill with clear dispatch protocol.

---

## 7. INTEGRATION POINTS

### With Other Skills
- **verify** — Full 4-tier verification
- **adversarial-critic** — Run meta-analysis on existing findings
- **adversarial-rca** — Root cause focus
- **refactor** — Can invoke for remediation
- **planning** — Can invoke for plan review

### Subagents Used
- adversarial-security
- adversarial-performance
- adversarial-compliance
- adversarial-quality
- adversarial-testing
- adversarial-logic
- adversarial-failure-modes
- code-critic
- qa-engineer
- adversarial-critic (meta-analysis)

### Invocation Pattern
```python
Agent(
  subagent_type="adversarial-review",
  prompt=f"Review these files: {file_list} Mode: {modes} Depth: {depth}",
  description="Adversarial review of [files]"
)
```

---

## 8. SQA ASSESSMENT

### Quality Attributes
| Attribute | Rating | Notes |
|---------|--------|-------|
| Test Coverage | N/A | No test files |
| Error Handling | GOOD | Graceful git fallback, file-based communication |
| Multi-terminal Safety | GOOD | State files in .claude/state/ |
| Documentation | EXCELLENT | 302-line SKILL.md with complete schema |
| Hook Integration | N/A | Skill-based, no hooks |
| Parallel Safety | GOOD | Independent agents, disk-based communication |

### SQA Relevance
- **HIGH** — This IS an SQA skill (adversarial code review)
- 7 specialist perspectives ensure comprehensive coverage
- JSON schema provides structured, machine-readable findings
- Meta-analysis catches blind spots and contradictions
