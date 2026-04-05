# Review Bundle: /adversarial-critic Skill
**Generated**: 2026-03-26T18:40:00Z
**Scope**: P:/.claude/skills/adversarial-critic/
**File Count**: 1 file (SKILL.md only)
**Execution Mode**: single-agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Skill Name**: adversarial-critic
- **Version**: 1.0.0
- **Category**: analysis
- **Trigger**: `/adversarial-critic`
- **Aliases**: `/meta-review`, `/critic`

### Domain & Purpose
Meta-analysis agent for adversarial review consensus and blind spot detection. Reads findings from 7 specialist agents (security, performance, compliance, quality, testing, code-critic, qa-engineer), identifies consensus patterns, blind spots, bias, contradictions, and quality calibration issues.

### Environment
- **OS**: Windows 11 Pro
- **Shell**: Bash
- **Primary Language**: Python/markdown
- **Key Integration**: Reads JSON from `.claude/state/adversarial-*.json`

---

## 2. ARCHITECTURE OVERVIEW

```
                    ┌──────────────────────────────────────┐
                    │         /adversarial-critic            │
                    │   (Meta-Analysis After Parallel Dispatch) │
                    └──────────────┬─────────────────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │ Read 7 JSON files │  from .claude/state │
              ▼                    ▼                    ▼
    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
    │adversarial-sec  │ │adversarial-perf │ │adversarial-comp │
    │adversarial-qual │ │adversarial-test │ │adversarial-logic│
    │  code-critic    │ │   qa-engineer   │ │  (others)       │
    └────────┬────────┘ └────────┬────────┘ └────────┬────────┘
             └──────────────────┴──────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │   5 Meta-Analysis Funcs  │
              │ 1. Consensus Detection   │
              │ 2. Blind Spot Detection  │
              │ 3. Bias Detection        │
              │ 4. Contradiction Detect │
              │ 5. Quality Calibration   │
              └─────────────┬───────────┘
                            │
                 ┌──────────▼──────────┐
                 │ adversarial-critic- │
                 │ {datetime}.json     │
                 └─────────────────────┘
```

---

## 3. EXECUTION AND DATA FLOW

### Step 1: Discover Agent Outputs
```bash
ls -t .claude/state/adversarial-*.json .claude/state/code-critic-*.json .claude/state/qa-engineer-*.json | head -n 7
```
Required agents: security, performance, compliance, quality, testing, code-critic, qa-engineer

### Step 2: Read and Parse Findings
Load each JSON and extract: agent name, finding details (severity, category, location, evidence, confidence), triage priority

### Step 3: Meta-Analysis Logic

#### Consensus Detection
- Groups findings by location (file:line)
- **Consensus**: 3+ agents same issue at same location
- **Strong Consensus**: 5+ agents

#### Blind Spot Detection
- Reads target code, verifies critical issues missed by ALL agents
- Checks for common patterns not mentioned

#### Bias Detection
- Calculates category/severity distributions per agent
- Flags agents with extreme severity inflation or category focus

#### Contradiction Detection
- Finds findings at same location with:
  - Different severity levels
  - Conflicting recommendations
  - Conflicting category labels

#### Quality Calibration
- Checks if HIGH confidence (80+) findings provide specific evidence
- Flags overconfident (vague location) and underconfident (high-quality evidence but low score)

### Step 4: Generate Meta-Findings
```json
{
  "meta_findings": [{
    "id": "META-XXX",
    "meta_type": "consensus|blind_spot|bias|contradiction|calibration",
    "severity": "CRITICAL|HIGH|MEDIUM|LOW",
    "title": "Title",
    "description": "Analysis",
    "evidence": "Agent report snippets or code",
    "impact": "Impact",
    "recommendation": "Resolution",
    "agent_names": ["agent-a", "agent-b"]
  }]
}
```

### Step 5: Write Results
Save to: `.claude/state/adversarial-critic-{datetime}.json`

---

## 4. COMPONENT INVENTORY

### Files
| File | Purpose |
|------|---------|
| SKILL.md | Complete skill definition (139 lines), meta-analysis protocol |

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars
1. **Sequential after parallel** — Runs AFTER all specialist agents complete
2. **Disk-based findings** — Reads JSON from `.claude/state/`
3. **5 meta-analysis functions** — Consensus, blind spot, bias, contradiction, calibration
4. **Evidence ceiling enforcement** — Confidence cannot exceed weakest evidence tier

### Constitutional Filter
**Remove findings containing prohibited patterns:**
- Continuous monitoring / always-on tracking
- Self-healing / auto-correction without approval
- Enterprise-scale meta-analysis tools

**Allowed:**
- Consensus analysis of AI agents
- Identifying gaps in AI agent coverage
- Calibrating AI agent performance

---

## 6. KNOWN ISSUES

No known issues. Single-file skill with clear sequential protocol.

---

## 7. INTEGRATION POINTS

### With Other Skills
- `/adversarial-review` — Parent skill that dispatches specialists
- Specialist agents write JSON findings that adversarial-critic reads

### State File Naming
- Pattern: `.claude/state/adversarial-critic-{datetime}.json`
- Input pattern: `.claude/state/adversarial-{type}-{datetime}.json`

### Aliases
- `/meta-review` — Alternative trigger
- `/critic` — Alternative trigger

---

## 8. SQA ASSESSMENT

### Quality Attributes
| Attribute | Rating | Notes |
|-----------|--------|-------|
| Test Coverage | N/A | No test files |
| Error Handling | GOOD | Graceful missing-file handling |
| Multi-terminal Safety | GOOD | State files in .claude/state/ |
| Documentation | EXCELLENT | 139-line SKILL.md with complete schema |
| Hook Integration | N/A | No hooks |
| Parallel Safety | GOOD | Read-only analysis of agent outputs |

### SQA Relevance
- **HIGH** — This IS an SQA meta-analysis skill
- Synthesizes 7 specialist perspectives
- Detects blind spots that individual agents miss
- Quality calibration improves overall review accuracy
