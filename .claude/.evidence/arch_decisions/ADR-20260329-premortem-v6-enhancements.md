# ADR-20260329-premortem-v6-enhancements: Pre-Mortem Skill v6 Enhancement Portfolio

**Status:** Accepted
**Date:** 2026-03-29
**Context:** Pre-mortem skill v5.2 has 17-step adversarial framework but lacks: (1) first-principles grounding, (2) step completion enforcement, (3) mode-collapse mitigation in hypothesis generation, and (4) explicit confidence calibration. Research from NotebookLM session identified 13 enhancement ideas; portfolio analyzed for ROI.

### Decision

Implement 4 enhancements for pre-mortem v6, in priority order:

1. **H — Step-Back Prompting** (new instruction, ~15 lines)
2. **F — Stop Hook Quality Gates** (1 Python hook file, ~80 lines)
3. **A+D — Verbalized Sampling + Calibrated Confidence Prompting** (1 reference file, ~60 lines)
4. **C-light — ToT-lite for cascade analysis** (SKILL.md edit, ~25 lines)

Reject: Ralph Wiggum Loop, Metacognitive Co-Regulation, Context-Aware Decomposition, MCP Integration, Computed Skills, NLP feedback loop upgrade. Progressive disclosure is already implemented.

### Rationale

Tier 1 (do now): Step-Back Prompting and Stop Hook deliver highest ROI per complexity — zero infrastructure, direct quality and enforcement improvement. Tier 2 (do selectively): VS+CCP address mode collapse (documented LLM failure mode) and overconfidence in cascade predictions. ToT-lite adds branch evaluation without full ToT overhead.

### Alternatives Considered

| Option | Description | Pros | Cons | Why Rejected |
|--------|-------------|------|------|--------------|
| **Chosen** | Incremental v6 (4 items) | High ROI, low risk, 3-4hr total | Modest improvement | Best ratio |
| Full ToT rewrite | Complete Tree of Thoughts integration | Deep reasoning | Changes execution model, high risk | Over-engineering |
| Ralph Wiggum Loop | Bash-persisted autonomous iteration | Context fresh each step | Violates solo-dev interactive workflow, autonomous execution red flag | Constitutional violation |
| Metacognitive Co-Regulation | Supervisor agent watching main agent | Theoretical quality improvement | Creates agent-hierarchy complexity, unclear ROI | Premature abstraction |
| MCP Integration | Jira/Linear ticket creation | Automated action tracking | User explicitly rejected unless irreplaceable; markdown is sufficient | User constraint |
| NLP Feedback Loop | Semantic evaluation of risk occurrence | Accurate matching | External API dependency in hook; violates hook constraints | Hook design constraints |

### Tradeoffs

| Quality | Improved | Degraded |
|---------|----------|----------|
| Correctness | Step-Back grounding reduces misapplied logic | — |
| Reliability | Stop Hook enforces completion | — |
| Depth | VS+CCP produce diverse, calibrated hypotheses | — |
| Operational overhead | 3-4hr implementation | Some cognitive overhead from additional prompts |

### Multi-Terminal Safety

- **Stop Hook**: Read-only validation of output files. Uses timestamp+pid file naming. Multi-terminal safe.
- **Reference files**: Static, read-only. Multi-terminal safe.
- **SKILL.md edits**: No shared mutable state. Multi-terminal safe.

### Edge Case Considerations

- **Stop Hook false positives**: Script detects missing steps by keyword presence; may block valid short-form outputs. Mitigation: `--brief` flag skips validation.
- **VS generates implausible failures**: Prompt instructs realistic scope; user can override. No mechanism needed.
- **Step-Back delays analysis**: 1 additional prompt pass; negligible latency impact (~1 LLM call overhead).
- **Confidence scores become arbitrary**: CCP fields are guidance, not enforced. Model may inflate confidence. Acceptable risk — explicit uncertainty is better than implicit overconfidence.

### Implementation

**H: Step-Back Prompting**
- File: `P:\.claude\skills\pre-mortem\SKILL.md`
- Add to Step 2: "Before listing specific failure causes, apply Step-Back Prompting: Ask 'What general architectural principles or laws apply to this system?' Ground each failure in first principles."
- Test: Run pre-mortem on known feature; verify first-principles language appears before specific failures.

**F: Stop Hook Quality Gates**
- File: `P:\.claude\hooks\StopHook_premortem_quality_gate.py`
- Logic: On Stop event, parse premortem output file. Check required steps (3.8 Empirical Evidence, 6 Warning Signs) are present. Exit code 2 if missing.
- Registration: Add to `settings.json` HOOKS.stop
- Test: Run pre-mortem with intentionally omitted step; verify Stop hook blocks completion.

**A+D: VS + CCP**
- File: `P:\.claude\skills\pre-mortem\references\verbalized_sampling.md` (new)
- Contains: VS prompt template for diverse hypothesis generation; CCP fields for risk format (likelihood%, confidence%, uncertainty notes)
- Integration: Update Step 2 and Step 4 formats to use CCP fields
- Test: Run pre-mortem; verify risk items include confidence% fields and VS-generated diversity.

**C-light: ToT-lite for cascade analysis**
- File: `P:\.claude\skills\pre-mortem\SKILL.md`
- Add to Step 2.5: "For each risk ≥6, explore 3 cascade paths → evaluate each as 'sure/maybe/impossible' → recommend highest-certainty path"
- Test: Verify cascade analysis shows explicit evaluation labels, not just linear chains.

### Consequences

- **Positive:** Pre-mortem outputs are more rigorous, diverse, and enforced-complete. Step completion is mechanical, not optional.
- **Negative:** Slight increase in execution time (~30-60s per run). Additional prompts may increase context usage.
- **Mitigation:** Progressive disclosure already keeps SKILL.md under 500 lines; new prompts are additions, not replacements.

### Evidence Basis

- NotebookLM session notes (source: 9e018c4f-6ce3-44f5-bbd7-909ed9be9bae): 13 enhancement ideas from AI agent research
- Verbalized Sampling: Research confirms mode collapse in LLMs on creative tasks
- Constitutional principles: Hook design constraints (no external API calls in hooks)
- Solo-dev constraints: Autonomous execution patterns rejected per CLAUDE.md detection phrases
