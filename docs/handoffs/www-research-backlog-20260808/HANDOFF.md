# Handoff — www research backlog (7 items from wiki gap scan)

## Status
OPEN — 7 research items from the wiki gap scan (2026-08-07) and epistemic-debt cache.

## Objective

These items surfaced from two sources:
1. Wiki gap scan (2026-08-07): tag clusters that are large and would benefit from consolidation
2. Epistemic-debt cache: concepts at 0.54-0.58 with documented evidence gaps

Each item needs a /www research session (wiki → web → wiki) to address.

## Items

### R1: Consolidate Grok Build thought-partner, hook, and MCP boundaries into domain overviews
**Source:** Wiki gap scan — grok-build tag has 59 concepts, hooks has 39, mcp has 1
**What to do:** /www to research how other agent frameworks organize their domain boundaries (Claude Code, OpenAI Codex, etc.), then consolidate the workspace's scattered concepts into 3-5 domain overviews with cross-links.

### R2: Cross-link shared progressive-disclosure and MCP sources across skill architecture concepts
**Source:** Wiki gap scan — Anthropic, OpenAI Codex, and MCP source URLs recur across multiple concepts
**What to do:** /www to find the authoritative progressive-disclosure documentation, then cross-link all concepts that reference it.

### R3: User Modeling for Agentic CLIs: research landscape and operator-profile recommendation
**Source:** Epistemic debt 0.58 — 6 evidence gaps documented
**What to do:** /www to research academic literature on user modeling for CLI agents (CHI, UIST, ICSE papers), then write a concept with the operator-profile recommendation.

### R4: Writing a discipline doesn't enforce it: the self-referential gap
**Source:** Epistemic debt 0.56 — Verification is 'inferred'
**What to do:** /www to research the compliance ceiling of prose rules vs structural enforcement (EGDP, hooks, etc.), then update the concept with empirical evidence.

### R5: Grok Build Compat Layer Does Not Surface Marketplace Plugin-Bundled Skills
**Source:** Epistemic debt 0.54
**What to do:** Verify whether this is still true after recent config changes. If fixed, mark resolved.

### R6: Grok Build's `~/.grok/disabled-hooks` Per-Hook Disable Layer
**Source:** Epistemic debt 0.54
**What to do:** Verify whether this layer exists and works. Document the mechanism.

### R7: Plan Mode in Grok Build is Structured-Thinking, Not a Security Sandbox
**Source:** Epistemic debt 0.54
**What to do:** Verify the security properties of plan mode. Document what it does and doesn't prevent.

## Acceptance criteria

- Each item either gets a /www research session producing an updated concept, OR is marked resolved if the evidence gap is no longer relevant.
- R5-R7 are quick verifications (<30 min each). R1-R4 are multi-hour research sessions.

## Provenance

- Source: /todo scanner (2026-08-08), wiki gap scan (2026-08-07), epistemic-debt cache
- Session: 019fdf3c
