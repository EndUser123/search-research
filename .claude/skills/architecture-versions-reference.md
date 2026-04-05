# Architecture Advisor: v1, v2, v3 - Complete Reference

**Date:** 2025-01-21
**Purpose:** Document all three architecture advisor versions with their prompts and system dependencies

---

## Quick Reference

| Version | Location | Lines | Artifacts | Complexity Detection |
|---------|----------|-------|-----------|----------------------|
| **v1** | /tmp/ai-software-architect/.claude/skills/ | ~500/skill | Always 13 | No |
| **v2** | P:/.claude/skills/arch-v2/SKILL.md | ~320 | 3-13 adaptive | Yes (2 systems) |
| **v3** | P:/.claude/skills/arch-v3/SKILL.md | ~74 | 3-13 adaptive | Yes (core) |

---

## Version 1: AI Software Architect (codenamev/ai-software-architect)

**Skills:** setup-architect, architecture-review, specialist-review, create-adr, list-members, architecture-status, pragmatic-guard

**Major Systems:**
1. Progressive Disclosure Pattern (ADR-008) - SKILL.md + references/ + assets/
2. Pragmatic Guard Mode (ADR-002) - YAGNI enforcement with intensity levels
3. Tool Permission Pattern (ADR-007) - allowed-tools in YAML frontmatter
4. Architecture Team (members.yml) - 7 core specialists
5. Configuration (config.yml) - pragmatic_mode + implementation settings

**Artifacts:** Always 13 (mental model, pre-mortem, risk, alternatives, rollback, tech debt, timeline, constitutional, ADR, checklist, handoff, confidence, adversarial)

---

## Version 2: /arch-v2 (Integrated Ecosystem)

**Major Systems Integrated:**
1. ComplexityDetector (yours) - quality attributes, estimated duration
2. SoloDevComplexityAnalyzer (yours) - solo feasibility, complexity score
3. measure_complexity (Phase 2 new) - linguistic/structural/risk signals
4. mental_model_selector (RCA) - cognitive framework recommendations
5. UAF decompose_architecture - agent mission generation
6. EnhancementRouter (csf) - mode-based output processing
7. Dependency scanning - import extraction from files
8. Constitutional context - CLAUDE.md + prohibited patterns
9. CKS Semantic Search - unified semantic daemon
10. Historical ADRs - adr index.md

**Artifacts:** Adaptive 3-13 based on decision complexity

---

## Version 3: /arch-v3 (Adaptive Core)

**Major Systems:**
1. complexity_measure.py - 3-dimension complexity detection
2. artifact_selector.py - complexity→artifact mapping

**Artifacts:** Adaptive 3-13 based on decision complexity

**What v3 does NOT have:** mental models, UAF, enhancement routing, CKS/CHS, constitutional, dependency scanning, hooks

---

## Decision Guide

| Scenario | Use Version | Why |
|----------|------------|-----|
| Full framework with ADRs, reviews, specialists | v1 | Complete ecosystem |
| Comprehensive analysis with mental models, UAF, knowledge | v2 | All integrations |
| Fast, complexity-scaled decision | v3 | Lightweight core |

---

## File Locations

- v1: /tmp/ai-software-architect/.claude/skills/
- v2: P:/.claude/skills/arch-v2/SKILL.md
- v3: P:/.claude/skills/arch-v3/SKILL.md
- Shared modules: P:/__csf/src/lib/{complexity_measure,artifact_selector}.py
