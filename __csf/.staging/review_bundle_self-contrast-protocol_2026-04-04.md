# Review Bundle: SELF-CONTRAST Protocol
**Generated**: 2026-04-04
**Scope**: SELF-CONTRAST Protocol — skill coverage analysis
**File Count**: 10 skill SKILL.md files read (single-agent mode)
**Execution Mode**: Single agent

---

## 1. PROJECT CONTEXT

### Bundle Metadata
- **Scope**: SELF-CONTRAST Protocol — a session retrospective framework
- **Purpose**: Map existing skills to protocol elements to identify coverage and gaps
- **Protocol Elements**: Self-Contrast (0), GAPS (1), IDEAS (2), STRESS-TEST (3), SCORES (4), NEXT STEPS (5)
- **Source**: Analysis of installed skill SKILL.md files in `P:/.claude/skills/` and `~/.claude/skills/`

### Scale Metrics
- Skills analyzed: 10 (recap, reflect, rns, pre-mortem, gto, critique, top-problems, diagnose, session, health-monitor, tldr-overview, truth)
- Skills with direct protocol coverage: 7
- Named gaps: 2 (Satisfaction scoring, Opportunity detection logic)

---

## 2. ARCHITECTURE OVERVIEW

```
SELF-CONTRAST Protocol
├── Element 0: Self-Contrast (2 contrasting summaries + discrepancies)
│   └── Skills: recap, reflect, critique, session
├── Element 1: GAPS (top 3 lost value from history)
│   └── Skills: gto, reflect, top-problems
├── Element 2: IDEAS (top 3 opportunities/extensions)
│   └── Skills: reflect (partial: gto mentions but lacks detection logic)
├── Element 3: STRESS-TEST (edge cases/disproofs)
│   └── Skills: pre-mortem, critique, diagnose
├── Element 4: SCORES (completeness/optimality/satisfaction)
│   └── Skills: gto (completeness/optimality), health-monitor (integrity)
│   └── GAP: Satisfaction scoring — no home
└── Element 5: NEXT STEPS (recover/prevent/realize)
    └── Skills: rns, pre-mortem, reflect
```

### Skill Multi-Coverage
| Skill | Elements Covered |
|-------|-----------------|
| reflect | 0, 1, 2, 5 |
| critique | 0, 3 |
| gto | 1, 4 (partial) |
| pre-mortem | 3, 5 |
| recap | 0 |

---

## 3. ELEMENT DETAIL

### Element 0: Self-Contrast
**Definition**: Summarize session in 2 contrasting ways; note discrepancies.

| Skill | File | Coverage |
|-------|------|----------|
| `recap` | `P:/.claude/skills/recap/SKILL.md` | Synthesizes problem vs optimal fix per session; transcript text for LLM reasoning |
| `reflect` | `~/.claude/skills/reflect/SKILL.md` | Retrospective modes (what happened, what failed, what should change) |
| `critique` | `P:/.claude/skills/critique/SKILL.md` | Multi-perspective adversarial review surfaces discrepancies |
| `session` | `P:/.claude/skills/session/SKILL.md` | Manages continuity across terminals/compaction |

### Element 1: GAPS
**Definition**: Top 3 missing/unmet from history.

| Skill | File | Coverage |
|-------|------|----------|
| `gto` | `P:/.claude/skills/gto/SKILL.md` | "Gap/Task/Opportunity analysis"; explicit "Chat history patterns (recurrent issues, cleanup opportunities)"; "contract gaps" |
| `reflect` | `~/.claude/skills/reflect/SKILL.md` | "Extract failures and unmet needs" from session transcripts |
| `top-problems` | `P:/.claude/skills/top-problems/SKILL.md` | "Analyze recent session history, premortem evidence, and task data to find the most impactful fixable problems" |

**Key distinction**: gto finds gaps in *code*; top-problems finds gaps in *process/decisions*.

### Element 2: IDEAS
**Definition**: Top 3 opportunities/extensions.

| Skill | File | Coverage |
|-------|------|----------|
| `reflect` | `~/.claude/skills/reflect/SKILL.md` | "Improvement" mode generates actionable improvements |
| `gto` | `P:/.claude/skills/gto/SKILL.md` | Tagline says "Gap/Task/Opportunity" but detection logic not defined in SKILL.md |

**Gap**: Opportunity detection in gto lacks defined detection logic. top-problems could serve as model.

### Element 3: STRESS-TEST
**Definition**: 1-2 edge cases/disproofs.

| Skill | File | Coverage |
|-------|------|----------|
| `pre-mortem` | `P:/.claude/skills/pre-mortem/SKILL.md` | "Comprehensive Failure Analysis"; 8-agent adversarial validation; cascade analysis; AI/LLM failure modes |
| `critique` | `P:/.claude/skills/critique/SKILL.md` | 8 specialist subagents; adversarial logic, compliance, testing, quality |
| `diagnose` | `P:/.claude/skills/diagnose/SKILL.md` | Structured diagnostic protocol + AID bug hunting: edge case detection, race conditions, logical inconsistencies |

### Element 4: SCORES
**Definition**: 1-10 Completeness | Optimality | Satisfaction

| Skill | File | Coverage |
|-------|------|----------|
| `gto` | `P:/.claude/skills/gto/SKILL.md` | "Completeness Target" table with health score 0-100%; measures complete/partial/failed runs |
| `health-monitor` | `P:/.claude/skills/health-monitor/SKILL.md` | "Hook validation" as proxy for system integrity score |

**GAP**: Satisfaction (element 4) — no skill measures user satisfaction with session outcomes.

### Element 5: NEXT STEPS
**Definition**: 1-3 actions (recover/prevent/realize).

| Skill | File | Coverage |
|-------|------|----------|
| `rns` | `P:/.claude/skills/rns/SKILL.md` | Dynamic action list with priority/reversibility; ties findings to file:line |
| `pre-mortem` | `P:/.claude/skills/pre-mortem/SKILL.md` | "Prevent top 3 + map to actions" |
| `reflect` | `~/.claude/skills/reflect/SKILL.md` | "improvement_recommendations" generates specific actionable improvements |

---

## 4. SKILL INVENTORY (relevant skills)

| Skill | Path | Primary Protocol Role |
|-------|------|---------------------|
| recap | `P:/.claude/skills/recap/` | Element 0 |
| reflect | `~/.claude/skills/reflect/` | Elements 0,1,2,5 |
| rns | `P:/.claude/skills/rns/` | Element 5 |
| pre-mortem | `P:/.claude/skills/pre-mortem/` | Elements 3,5 |
| gto | `P:/.claude/skills/gto/` | Elements 1,4 (partial) |
| critique | `P:/.claude/skills/critique/` | Elements 0,3 |
| top-problems | `P:/.claude/skills/top-problems/` | Element 1 |
| diagnose | `P:/.claude/skills/diagnose/` | Element 3 |
| session | `P:/.claude/skills/session/` | Element 0 |
| health-monitor | `P:/.claude/skills/health-monitor/` | Element 4 (partial) |

---

## 5. NAMED GAPS

### Gap 1: Satisfaction Scoring (Element 4)
- **What**: No skill measures user satisfaction with session outcomes
- **Impact**: SCORES element is incomplete (2 of 3 sub-elements covered)
- **Distinction**: gto/health-monitor measure *system* health, not *user* satisfaction
- **Potential home**: None identified

### Gap 2: Opportunity Detection Logic (Element 2)
- **What**: gto tagline says "Gap/Task/Opportunity" but SKILL.md has no detection logic for opportunities
- **Impact**: IDEAS element relies on reflect's general improvement mode, not a structured detector
- **Potential home**: top-problems ranks by impact; could be extended to cover opportunities

---

## 6. UNCHANGED ITEMS

The following were audited and are not part of this protocol:
- Hooks system (P:/.claude/hooks/)
- CHS/CKS infrastructure (P:/__csf/src/features/)
- AI provider skills (ai-api, ai-apiv2, ai-chutes, etc.)
- Development skills (tdd, refactor, code, arch, planning, rca)
- Documentation skills (docs, doc-to-skill, notebooklm)
- Orchestration skills (orchestrator, gitbatch, ship, skill-ship)

---

## 7. AUDIT SOURCES

| File | Lines Read |
|------|-----------|
| `P:/.claude/skills/recap/SKILL.md` | 1-60 |
| `P:/.claude/skills/rns/SKILL.md` | 1-40 |
| `P:/.claude/skills/pre-mortem/SKILL.md` | 1-60 |
| `P:/.claude/skills/gto/SKILL.md` | 1-60 |
| `P:/.claude/skills/critique/SKILL.md` | 1-60 |
| `P:/.claude/skills/top-problems/SKILL.md` | 1-40 |
| `P:/.claude/skills/diagnose/SKILL.md` | 1-40 |
| `P:/.claude/skills/session/SKILL.md` | 1-40 |
| `P:/.claude/skills/health-monitor/SKILL.md` | 1-40 |
| `~/.claude/skills/reflect/SKILL.md` | 1-40 |
