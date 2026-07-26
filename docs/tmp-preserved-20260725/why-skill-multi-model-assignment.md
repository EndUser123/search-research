# Assignment: Optimize Grok Build `/why` skill

You are an independent analyst. Produce an optimization proposal for the Grok Build `/why` skill so it is optimally useful for diagnosing failures in agent-control systems (hooks, gates, receipts, verification, multi-agent workflows). Radical refactoring is allowed if long-term ROI is positive.

## Read these files first (absolute paths)

1. `C:/Users/brsth/.grok/skills/why/SKILL.md` — current skill (canonical target)
2. `P:/docs/handoffs/why-skill-enhancement-20260725/HANDOFF.md` — approved design + post-handoff optimizations A–F
3. `C:/Users/brsth/Downloads/why-from-codex.txt` — Codex design prompt (reference requirements; do NOT implement blindly)
4. Optionally for depth:
   - `P:/.data/wiki/concepts/multidimensional-root-cause-analysis-ai-agent-failures.md`
   - Claude RCA refs if present under `C:/Users/brsth/.claude/plugins/cache/local/cc-skills-sdlc/` (`evidence_tiers.md`, `rca_investigation_protocol.md`)
   - Sibling skills: `C:/Users/brsth/.grok/skills/aar/SKILL.md`, `C:/Users/brsth/.grok/skills/tp/SKILL.md`, `C:/Users/brsth/.grok/skills/red-team/SKILL.md` (boundaries only)

## Constraints (hard)

- Host is **Grok Build**, not Claude Code. Do not assume Claude hooks/MCP/CKS fire unless verified for Grok.
- Prefer **optimal long-term** over minimal patch. Transition effort is not a disqualifier.
- Preserve existing strengths: 5-dim Ishikawa, Five Whys, FACT/INFERENCE/UNKNOWN, competing explanations, falsifiers, observe-before-cause (diagnostic), no auto-implement, optional `--verify`.
- Do NOT add: decision-archaeology mode, mandatory 3–7 hypotheses, mandatory web research every run, durable state every short run, 10 mandatory control dimensions always.
- Skill must stay operational and concise enough for an LLM to follow. Ceremony without finding quality is a bug.
- Do NOT edit files. Analysis and design proposal only.

## Output format (strict)

```markdown
## Model: <your model name>

### 1. Current strengths (keep)
- bullet list with evidence from SKILL.md

### 2. Concrete gaps (what fails in practice)
- each gap: symptom → root → why current skill misses it

### 3. Recommended design (optimal long-term)
- step structure / dispatch model
- what to add, what to change, what to delete
- how radical vs incremental; ROI argument

### 4. Rejected alternatives
- at least 2 rejected options and why

### 5. Implementation priority
- ordered list (what ships first)

### 6. Falsifiers
- how we would know the design is wrong

### 7. Open questions / unknowns
```

Be concrete. Cite file paths. Prefer structural fixes over more prose checklists. If the handoff and the Codex prompt disagree, name the disagreement and pick a side with a criterion.
