---
title: "Fusion portal design discipline: token system, design cleanup, and the AI design tell problem"
created: 2026-08-03
source: session-2026-08-03
tags: [design-tokens, fusion-portal, model-web, ai-design-tells, design-cleanup, naming-convention]
summary: >
  Session building the model-web fusion portal (fusion2.html). Key decisions:
  (1) shared design token system (tokens.css) to prevent drift between HTML tools,
  (2) full design cleanup consolidating 14 color variables to 1 accent system,
  (3) naming convention: "CLI"/"terminal" for orchestrator, "Grok" for grok.com only,
  (4) tab visibility toggle validated by /www research as good design practice.
type: decision
agent: grok
host: grok
cognitive_load: 2
verification: local-only
---

# Fusion portal design discipline: token system, design cleanup, and the AI design tell problem

## Decision context

The model-web skill accumulated 3 HTML tools (launcher.html, fusion.html, fusion2.html)
across multiple sessions. Each defined its own `:root` CSS variables with different
hex values for the same semantic purpose — 3 files, 3 palettes, no shared design
language. The fusion2.html portal additionally accumulated visual cruft: 14
overloaded color variables, emoji everywhere, hover-scale animations on every
element, 8 type sizes, animated phase pills.

The operator triggered the cleanup with "it's getting a little silly" — the pivot
point that shifted the session from feature-building to design discipline.

## What was decided

### 1. Shared design token system (`tokens.css`)

A single CSS file linked by every HTML tool via `<link rel="stylesheet" href="tokens.css">`.
Encodes: 4 surface levels, 1 accent family, 2 text levels, 3 type sizes (11/13/16px),
5-step spacing rhythm, 1 transition speed, 5 category colors scoped to labels only,
1 font stack. Change once, every tool updates.

**Rejected alternative:** inline `:root` block pasted into each file. Rejected because
it creates a copy-paste maintenance burden and doesn't prevent drift when an agent
edits one file without checking others.

### 2. Design cleanup principles (from /www research + operator feedback)

- **One accent color** for all interactive states (not 14 overloaded vars)
- **3 type sizes** max (11/13/16px — not 8)
- **No emoji** (functional symbols like → and ✓ are fine)
- **No hover-scale animations** (the AI-generated tell)
- **Phase indicators are quiet text**, not animated pills
- **Labels say what happens** ("Background" / "Visible" — not "Stealth Mode")

### 3. Naming convention: CLI vs Grok

"CLI" or "terminal" = the orchestrator (the terminal LLM). "Grok" = the grok.com
web LLM (one of 16 ensemble targets). This resolves the collision where "Grok"
appeared as both orchestrator and ensemble target. Aggregator option changed from
`"grok"` to `"cli"` in the blast signal.

### 4. Tab visibility toggle validated

The Background/Visible toggle was validated by the /www design research as good
design practice: controls say what happens, labels are domain-accurate verbs,
and the toggle gives operators a way to verify extraction by seeing raw model
responses in their native UI.

## What the research changed

The /www research on web design skills (State of CSS 2025 + AI design tells)
confirmed the cleanup direction and identified the structural fix: a shared
token file. Without the research, the cleanup would have been ad-hoc per-tool
fixes. With it, the token system prevents the problem from recurring.

## Key artifacts

- `~/.grok/skills/model-web/tokens.css` — shared design tokens
- `~/.grok/skills/model-web/fusion2.html` — redesigned portal (tokens.css linked)
- `~/.grok/skills/model-web/launcher.html` — migrated to tokens.css
- `~/.grok/skills/model-web/__lib/fusion_orchestrate.py` — orchestration script
- `~/.grok/skills/model-web/SKILL.md` — v1.2, Fusion Portal Protocol section
- `P:/.data/wiki/concepts/web-design-skills-ai-generated-internal-tools-2026.md` — research

## Falsifier

The token system fails if:
- New HTML tools are generated without linking tokens.css
- The token file is edited without updating all consuming tools
- A future agent overrides shared tokens with local `:root` definitions

## Related

- [[expected-ui-ux-features]] — tier-1/2/3 UI checklist
- [[agent-skills-fleet-patterns-solo-director-2026]] — flagged the missing design skill gap
