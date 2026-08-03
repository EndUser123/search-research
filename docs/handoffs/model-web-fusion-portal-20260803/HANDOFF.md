---
thread_id: model-web-fusion-portal-20260803
parent_handoff_path: docs/handoffs/session-019fbf77-20260802/HANDOFF.md
current_session_id: 019fbf77-8fe7-7070-bccd-e12f5d1807d8
produced_at: 2026-08-03T00:30:00-06:00
status: open
handoff_type: implementation
accurate_as_of_head: 96668cc346fbad6175591047373b86841850ca04
---

# Handoff: Model-web fusion portal + social media research + capture improvements

## Objective

Build a fusion portal for multi-model ensemble with configurable strategies
(single-pass Beam, dual-pass MoA), and improve the /capture skill to catch
stated-but-unactioned items and unverified assertions.

## Status: OPEN — UI built, Grok orchestration not yet wired

## What was completed this session

### Fusion portal (`fusion2.html`)
- Sidebar+content split layout with sticky prompt bar
- 5 model categories (US/CN/EU+Canada/Search/Aggregators) with 16 providers
- Per-model: variant dropdown, reasoning level dropdown, toggles, ELO, usage count, sub/free toggle
- Select-all per category with family colors matching launcher
- Collapsible controls (show only when model selected)
- Copy button on every response card
- File path input + drag-and-drop text files onto prompt
- Single-pass mode: 4 fusion strategies (consensus, best-elements, contradiction, ranked)
- Dual-pass MoA mode: Layer 2 models re-answer seeing all L1, then synthesis
- Phase indicator (Blast → Collect → Layer 2 → Fuse)
- JavaScript API: `window.fusionSetResponse()`, `fusionSetL2()`, `fusionSetFused()`, `fusionSetPhase()`
- Loads model-stats.js for dynamic ELO/usage data

### Launcher updates (`launcher.html`)
- Corrected all 15 model notes from Chrome DevTools picker inspection (12 were wrong)
- Added usage count, ELO, sub/free tags
- Added underused pulse animation
- Added model-stats.js dynamic loading
- Added Cohere to EU/Canada category

### Dynamic stats tracking
- `P:/.data/model-web/model-stats.json` — source of truth (16 models)
- `P:/.data/model-web/generate_stats_js.py` — generates JSONP `model-stats.js`
- Post-ensemble auto-update documented in SKILL.md

### /capture skill improvements
- Category 8: stated-but-unactioned items (scan for recommendations that were dropped)
- Category 9: unverified assertions (claims stated as fact without receipts)
- Pre-RNS trigger in /wiki (scan before generating recommended next steps)
- Session-completeness audit + propagation check added to /close-check

### Reddit MCP fix
- OAuth credentials wired (Arindam200-mcp app, config.toml env block)
- reddit-rss MCP disabled (redundant)
- 5 files updated for Reddit MCP-first routing (tool-fallbacks, www, web, tool-failure-lifecycle)
- Reddit API budget tiering added to /www Phase 2b

### Social media scraping research
- Landscape mapped: twscrape (X.com), existing tools cover other platforms
- Wiki concept: social-media-data-extraction-landscape-2026.md
- web-research-state-2026.md twscrape assessment corrected

### Research batch (3 wiki concepts from Reddit MCP)
- multi-agent-coordination-failure-modes (MAST taxonomy + practitioner data)
- llm-sycophancy-calibration-failure (Stanford/MASK/AbstentionBench research)
- prose-rules-vs-structural-enforcement (2026 production evidence)

### Domain overviews
- multi-agent-fleet-domain-overview (55 concepts indexed)
- enforcement-and-hooks-domain-overview (78 concepts indexed)

## What's NOT done — tasks for next session

### NEXT-1: Wire Grok orchestration to fusion2.html
The page has the JS API (`fusionSetResponse`, etc.) but Grok doesn't yet
have the orchestration logic to: read the blast signal from console,
execute /model-web ensemble to the selected tabs, collect responses,
and write them back to the page via evaluate_script.

### NEXT-2: Test fusion2.html with a real ensemble
Pick 3 models, type a prompt, click Blast, tell Grok to execute, and verify
the page populates correctly. This will surface any DOM/CDP issues.

### NEXT-3: Decide fusion.html vs fusion2.html
Both exist. fusion2.html is the redesigned version (sidebar layout).
fusion.html is the original (panel layout). The operator should pick one
and the other should be deleted.

### NEXT-4: twscrape install + /www Phase 2b wiring
From the social-media-scraping handoff. pip install, account setup, wire
into /www practitioner signal pass.

### NEXT-5: Verify/inference domain overview
10 overlapping concepts need an index page (handoff exists).

### NEXT-6: Model picker verification
The variant/reasoning/toggle data in fusion2.html and launcher.html was
corrected from SKILL.md picker inspection, but some of that inspection data
is from 2026-08-01 and may be stale. Re-verify against live pages if any
model has updated its picker since then.

## Related artifacts

- Launcher: `~/.grok/skills/model-web/launcher.html`
- Fusion v1: `~/.grok/skills/model-web/fusion.html`
- Fusion v2: `~/.grok/skills/model-web/fusion2.html`
- Stats: `P:/.data/model-web/model-stats.json`
- Generator: `P:/.data/model-web/generate_stats_js.py`
- Wiki: [[social-media-data-extraction-landscape-2026]]
- Handoffs: social-media-scraping-architecture, verify-inference-domain-overview

## Falsifier

This handoff is obsolete if the operator decides not to pursue the fusion
portal approach, or if a different tool (big-AGI, ChatALL) is deployed
instead of the custom page.

---

## Revision 1 — 2026-08-03T02:30:00-06:00 (session 019fbf77)

**Trigger:** auto-update — post-handoff commits + /tp session + /tp improve analysis.

**What changed since the original:**
- Cohere integrated into EU/Canada category across fusion2.html, launcher.html, and model-stats.json (commit f9e5543). Originally miscategorized as "aggregator" — corrected to "Canadian AI company" per operator feedback.
- Review fixes applied: F-01 basename match, F-02 escalation TOCTOU lock, F-03 var rename, F-04 dedup, F-06 sentinel, F-08 random tmp suffix, F-09 backoff simplify, F-10 quoted #, F-12 ownership check (commits c63be3e, 788fd7a).
- Copy buttons added to response cards + label wrapping for model entries (commit adc1989).
- /tp session + /tp improve analysis completed — 13 improvement findings across efficiency, effectiveness, insightfulness, thought-partnership dimensions.

**Updated evidence:**
- HEAD at revision: 96668cc (P:/ repo)
- The "build-on-unverified-data" pattern identified as session's dominant failure: 3+ instances (model notes 12/15 wrong, Reddit app "never registered", upload_file "blocked" claim). Wiki concept being written.

**Status update:** OPEN — UI complete + review-fixed. Primary gap is NEXT-1 (Grok orchestration).

**NEXT-3 resolved:** fusion.html should be deleted — fusion2.html is the redesign the operator has consistently worked with. Not a decision needed; it's cleanup.

**New open items from /tp improve:**
- The "build-on-unverified-data" pattern needs structural enforcement: a pre-build verification step for external-sourced values in UI/code. The wiki concept captures the pattern; structural fix (hook or skill check) is a separate workstream.
- Harvest CLI integration in /tp session protocol points to `P:/.data/harvest/harvest.py` which does not exist — needs correct path or removal.
