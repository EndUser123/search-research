---
thread_id: maintenance-skill-ports-and-gap-closing-20260727
parent_handoff_path: none
current_session_id: 019f9a3c-a088-7230-97c3-7959e8bae1cd
current_terminal_id: console_1faf8be6-6283-4495-939e-9252
produced_at: 2026-07-27T14:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 9a3bd643bb11a43ce9902e99e2eec691204f795e
---

# Maintenance skill ports + Claude-to-Grok gap closing

## Objective

Port Claude-side maintenance and SDLC skills to Grok Build, closing domain
coverage gaps identified by a systematic gap analysis (187 Claude-only skills
vs 64 Grok-only skills). Ensure every SDLC domain has Grok-native coverage.

## Last user message (verbatim)

> "Emotionally I can't stand leaving any value on the table. So all gaps
> matter enough to port to enhance or fix what's missing."

## Status

**OPEN — 4 skills shipped, 15-22 identified for porting.**

### Shipped this session (4 maintenance skills)

| Skill | Adapted from | Location |
|---|---|---|
| `/skill-prune` | Claude `garden` | `P:/.agents/skills/skill-prune/SKILL.md` |
| `/recover` | Claude `recover` | `P:/.agents/skills/recover/SKILL.md` |
| `/workspace-health` | Claude `main` | `P:/.agents/skills/workspace-health/SKILL.md` |
| `/config-audit` | Claude `claudit` | `P:/.agents/skills/config-audit/SKILL.md` |

All four adapted for Grok Build: no CKS, config.toml not settings.json,
`[plugins].disabled` not `enabledPlugins`, session transcripts at
`~/.grok/sessions/` not `~/.claude/projects/`.

### Supporting work shipped this session

- `index_skills.py --audit` flag: surfaces duplicates (204), disabled-in-Grok (237), orphan references (187)
- AGENTS.md maintenance reminders (3 lines, 100% presence)
- `/www` research concept: `llm-instruction-non-compliance-activation-gap-2026.md`
- AGENTS.md meta-rule: "skill-specific instructions override general heuristics"

### Domain coverage matrix (after ports)

| Domain | Grok skills | Gap? |
|---|---|---|
| Discovery/Planning | 7 | ✅ |
| Design/Architecture | 1 | ⚠ Weak |
| Implementation | 4 | ⚠ Moderate |
| Testing/QA | 2 | ⚠ Weak |
| Review/Audit | 4 | ✅ |
| **Deployment/Ship** | **0** | **⛔ No coverage** |
| Maintenance | 8 | ✅ |
| Knowledge/Memory | 9 | ✅ |
| Collaboration | 4 | ✅ |
| Meta/Process | 5 | ✅ |

## Decisions

### D1. Port by domain gap priority, not by plugin source
Earlier attempts scanned only `cc-skills-*` plugins and missed skills in
`quickstop`, `search-research`, and other marketplaces. The proper approach
is the systematic gap analysis (187 Claude-only skills) which identifies
gaps by function, not by source.

### D2. Rename during port for clarity
`garden` → `skill-prune`, `main` → `workspace-health`, `claudit` →
`config-audit`. Original names were Claude-specific or ambiguous.

### D3. AGENTS.md reminders for activation (per activation-gap research)
Skills have 6-66% activation rate; AGENTS.md has 100%. The 3-line
maintenance reminder section in AGENTS.md ensures the skills get invoked
even when the skill body isn't loaded.

## Evidence

### Porting plan (full)
`P:/docs/plans/claude-to-grok-skill-porting-20260727.md` — 5 priority tiers,
19-26 skills, ~20-25h total effort, per-skill adaptation notes.

### Gap analysis script
`P:\tmp\gap_analysis.py` — parses the skill catalog, finds all Claude-only
skills (C=✓, G≠✓), groups by name to deduplicate across scopes.

### Committed work
- 4 maintenance skill SKILL.md files (`.agents/skills/`)
- `index_skills.py` `--audit` flag + `audit_skills()` function
- AGENTS.md maintenance reminders + meta-rule
- 2 `/www` research concepts (activation gap + video-to-wiki pipeline)

## Next steps

### Session 1 (highest priority — close zero-coverage gap)
1. Port `ship` (deploy readiness) — the only domain with 0 Grok coverage
2. Port `constraints` (30min, simplest P2)
3. Port `debt` (30min, read-only JSONL viewer)

### Session 2 (P2 batch — weak coverage gaps)
4. Port `tdd` (RED/GREEN enforcement)
5. Port `diagnose` (structured diagnostic protocol)
6. Port `trace` (manual trace-through verification)
7. Port `decision-tree` (SDLC decision engine)
8. Port `evolve` (modernization workflow)

### Session 3 (P3 batch — implementation depth)
9. Port `tldr-*` family (4 skills: code, overview, deep, router, stats)
10. Port `code` (feature dev mission control)

### Session 4 (P4 batch — maintenance enhancements)
11. Port `stale` (docs out of date vs code)
12. Port `skill-audit` (skill quality rubric)
13. Port `skill-similarity` (skill dedup)
14. Port `snapshot` (session snapshot capture/restore)
15. Port `capture` (merge into `/wiki` or standalone)

### Each port follows this pattern:
1. Read Claude SKILL.md source
2. Identify Claude-specific dependencies (CKS, settings.json, file-history, /rewind, hooks)
3. Write Grok-adapted SKILL.md at `P:/.agents/skills/<name>/`
4. Update AGENTS.md maintenance reminders if the skill needs a trigger
5. Commit

## Verification commands

```bash
# Verify all ported skills exist and are in catalog
python P:/.data/wiki/scripts/index_skills.py --audit

# Verify AGENTS.md has maintenance reminders
Select-String -Path P:/AGENTS.md -Pattern "skill-prune|recover|workspace-health|config-audit"

# Run the gap analysis to track progress
python P:\tmp\gap_analysis.py
```

## Open questions

None — the porting plan covers all gaps with priority ordering.

## Falsifier

This handoff fails if:
- The gap analysis misses skills (it scanned the catalog, not individual
  plugin directories — any skill not in the catalog is invisible)
- The adaptation notes are insufficient for a fresh session to port without
  re-reading the Claude source (each note should name what to change)
- The ported skills don't work on Grok Build (adaptation assumed no CKS,
  no CLAUDE hooks — if a skill needs one of these, it needs deeper adaptation)
