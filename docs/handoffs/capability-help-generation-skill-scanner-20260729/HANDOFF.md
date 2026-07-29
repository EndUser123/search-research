# Handoff: Capability help generation + skill scanner + LLM classifier (items 4-5)

## Status: COMPLETED (2026-07-29)

## Objective

Build the remaining items from the `/tp explore` analysis of the capability graph system:
- Item 4: Auto-generate help text from the capability registry instead of hardcoding
- Item 5: Scan all external skills (Claude plugins, bundled, etc.) and classify them into fleet domains

## What was built

### Item 4 — auto-generate help from registry

Added output modes to `P:/.data/wiki/scripts/capabilities.py`:
- `--help-text` — formatted markdown of all domains + capabilities
- `--for-domain <name>` — capabilities in a specific domain
- `--for-skill <name>` — what a skill provides, consumes, uses
- `--consumers <cap>` — who provides + who uses a capability

Updated 3 skills to reference the registry dynamically:
- `/tp help` (line ~1108): appends review-domain capabilities
- `/go` (line ~69): introspection reference in capability map
- `/review` (line ~29): introspection reference in intro

### Item 5 — external skill scanning

Two scripts, pure code + free model:

**`P:/.data/wiki/scripts/scan_external_skills.py`** (pure Python):
- Walks 811 SKILL.md files across all roots (plugins, bundled, agents, grok-fleet)
- Keyword heuristics classify into 12 fleet domains (87.3% match rate)
- Flags 103 unmatched for LLM classification
- Modes: default summary, `--by-domain`, `--unmatched`, `--json`

**`P:/.data/wiki/scripts/classify_skills_llm.py`** (free model):
- Classifies the 103 keyword-misses via mistral-medium-latest (free, 2s/batch)
- NVIDIA gpt-oss-20b as fallback
- Position-based batch matching (handles duplicate names from plugin version caches)
- 11 API calls, 18.5s total for 103 skills → 100% coverage

**Shared utility: `P:/.agents/scripts/models/load_api_key.py`**:
- Extracted from classify_skills_llm.py's key-loading logic
- Reads from env vars first, falls back to config.toml
- Supports mistral, nvidia, openrouter, glm, groq
- All future model-calling scripts should use this instead of hardcoding keys

### Item 2 (bonus) — skill graph rebuilt
- `build_skill_graph.py` re-run: 289 delegation edges, 135 provider edges, 101 wiki-reference edges

### Wiki concept
- `P:/.data/wiki/concepts/stop-hook-verification-receipt-capability-hierarchy.md`
- Documents the capability hierarchy (syntax < static_analysis < unit_behavior < ...)
- Path-based derivation rules (scripts/ → static_analysis, hooks/*.json → runtime_hook)
- Reflex pattern for avoiding blocked cycles

## Commits

| Hash | Repo | Description |
|------|------|-------------|
| `2319436` | P: | Items 4+5: auto-generate help from registry + external skill scanner |
| `bd2fe2e` | P: | Item 5: LLM classifier for unmatched skills via mistral-medium-latest |
| `35678d6` | P: | Fix ruff lint: remove unused imports and f-strings without placeholders |
| `89dd535` | ~/.grok | Item 4: reference capability registry from /tp help, /go, /review |

## Remaining work

- **Item 6 (design notes for 60 of 64 capabilities)** — deferred. Lower priority since contracts are lean and only high-consumer capabilities need design notes.
- **Context-firewall Layer 1 extract.py** — the generalized extraction utility described in `[[context-firewall-architecture]]` is still not built. `dgemma_read.py` and `classify_skills_llm.py` are two ad-hoc implementations of the same pattern.
- **103 LLM-classified plugin skills triage** — some represent capabilities the fleet doesn't have natively (context7, smart-explore, pi-cli-runtime). Worth a triage pass to see if any should be promoted to the fleet.

## Verification

- `ruff check` passes on all three scripts (capabilities.py, scan_external_skills.py, classify_skills_llm.py, load_api_key.py)
- `py_compile` passes
- Functional verification: capabilities.py loads 68 caps/13 domains; scan_external_skills.py scans 811 skills; classify_skills_llm.py classified 103 skills live
- Skill graph rebuilt: 289 delegation edges, 135 provider edges

## Key decisions

1. **Pure code first, free model second** — keyword heuristics handle 87% of classifications for free. Only the residual 13% needs an LLM. The LLM is mistral-medium-latest (free, 2s/batch) per the coding-model-pool tier-1.

2. **Direct API, not spawn_subagent** — per `[[context-firewall-architecture]]`, mistral fails via spawn_subagent (422) but works via direct HTTP API. The script IS the firewall.

3. **No persistence of LLM classification results** — the pipeline re-runs in ~20s on demand. Saving to P:/tmp is pointless (gitignored). Saving elsewhere creates stale files. The scan+classify is cheap enough to run live each time.

4. **Shared key loader** — extracted `load_api_key.py` as the third script (after dgemma_read.py and benchmark scripts) to use the direct-API pattern. Prevents gitleaks blocks and centralizes key management.
