# Handoff: Epistemic Knowledge System — Phases 2-4

## Status
OPEN — infrastructure design + implementation needed

## Created
2026-08-02

## Assignee
grok (fresh session)

## What's done

Phase 1 (8 behavioral changes) is committed and live:
- Confidence decay frontmatter (SCHEMA.md: `confidence`, `last_verified`, `half_life_days`)
- Stale concept detection (AGENTS.md per-turn + /wiki post-write)
- Contradiction alerts (/wiki post-write)
- Auto research triggers (AGENTS.md per-turn)
- Quality-of-run reports (/www Step 3.7)
- Epistemic debt tracking (/www Step 3.6)
- Adversarial persona weaving (/www Phase 2 instruction)
- Research thread surfacing (/www Phase 3.5 + Phase 1)

Full design: `P:/.data/wiki/concepts/epistemic-knowledge-system-design-2026.md`

## What remains

### Phase 2: Telemetry store + debt ledger + personas

**Source/query/failure pattern memory:**
- Create `P:/.data/wiki/_state/research-telemetry.json`
- Track: which sources produced high-quality findings vs noise, which query formulations worked for which domains, which research strategies failed
- `/www` reads this at Phase 1 to inform query formulation
- `/web` writes to it after each search (source URL + quality score + topic)

**Epistemic debt ledger (Python script):**
- Create `P:/.data/wiki/scripts/epistemic_debt.py`
- Scans all wiki concepts for confidence scores + verification tiers + downstream dependents
- Computes: `debt = (1 - confidence) × age_factor × dependency_count`
- Outputs debt-sorted priority list → writes to `_state/research-suggestions.json`
- `/todo` and `/www` Phase 1 consume the output

**Full adversarial personas:**
- 3 persistent personas (True Believer, Skeptic, Outsider) with memory scratchpads
- Each proposes searches from its bias
- Final wiki entry = intersection of concessions, not union of findings
- Design decision: subagent-based (spawn 3) or inline (same agent, 3 passes)?

### Phase 3: Graph infrastructure

**Graph index (Python script):**
- Create `P:/.data/wiki/scripts/build_graph.py`
- Reads all wiki frontmatter `relations:` + `[[wikilinks]]` → builds traversable graph
- Output: JSON adjacency list at `P:/.data/wiki/_state/knowledge-graph.json`
- CLI: `python build_graph.py query --from <concept> --to <concept>` (shortest path)
- CLI: `python build_graph.py cluster --tag <tag>` (concept clustering)
- CLI: `python build_graph.py stale` (concepts citing superseded ones)

**Confidence-weighted answers:**
- `/wiki <query>` returns confidence tier + provenance alongside the answer
- Concepts with `confidence < 0.5` flagged as "low confidence — consider re-research"

### Phase 4: Synthesis + anti-causal (research-level)

**Synthesis engine** — this is `/dream`'s domain. Needs a separate design doc.
- Cross-domain pattern detection ("inference-in-code ≈ plausible-narratives")
- New concept proposals from combinations

**Anti-causal traces** — research-paper-level. Needs design.
- Counterfactual dependency signatures per concept
- Perturbation-driven research (gaps = untested interventions)

## Selection criterion

Optimal long-term: the system gets qualitatively smarter with every use, not just additive. The epistemic debt ledger is the keystone — it makes the system self-motivating.

## Key files

- `P:/.data/wiki/concepts/epistemic-knowledge-system-design-2026.md` — full design
- `P:/.data/wiki/SCHEMA.md` — confidence decay frontmatter (already added)
- `C:/Users/brsth/.grok/skills/www/SKILL.md` — Phase 3.5/3.6/3.7 + adversarial lenses
- `C:/Users/brsth/.grok/skills/wiki/SKILL.md` — post-write gap detection
- `C:/Users/brsth/.grok/AGENTS.md` — per-turn auto-research triggers

## Context

Session 2026-08-02. Brainstorming + /tp critique + 2/5 web LLMs (DeepSeek gave epistemic debt ledger + adversarial personas; Claude gave confidence decay). All Phase 1 items shipped. Phases 2-4 are infrastructure work for a fresh session.
