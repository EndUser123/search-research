# Pre-Mortem: Marketplace Comparison Dashboard

**Target**: Marketplace comparison dashboard (HTML + JSON reconciliation + update script)
**Date**: 2026-03-24
**Analysis**: USM skill marketplace comparison feature rebuild

---

## Step 0: Constraints (from CLAUDE.md)

- Discovery before implementation — search existing code first
- Three reasoning flaws: arbitrary thresholds, ignored concurrency, over-engineering
- Reversibility Scale — reversibility > 1.5 requires rollback plan
- Evidence-based — show pytest output, hook runtime evidence
- Format before output — no raw markdown in responses
- Tool patterns — stderr = hook error; hooks use stdout or silence

---

## Step 0.7: Kill Criteria

- If `update_marketplace_data.py --dry-run` fails with unhandled exception → abandon approach
- If HTML dashboard renders but KPIs don't animate (null `data-raw`) → fix required before use
- If any API source returns non-JSON and breaks reconciliation → add error handling
- If `data-raw` injection silently fails (element IDs don't match) → fix ID alignment

---

## Step 1: Failure Scenario

**"It's 6 months later. The marketplace dashboard is broken, stale, or misleading."**

---

## Step 1.5: Fix Side Effects (What NEW risks does this fix introduce?)

**Fix: Replace initKPIs() with data-raw attribute reading**
- NEW: Dashboard now depends on update script injecting correct `data-raw` values — if script fails, dashboard shows 0/animation-to-0 instead of graceful fallback
- NEW: `parseInt()` on `data-raw` silently returns 0 for malformed values (e.g., `"N/A"`) — no error thrown
- NEW: The `gradeEl.textContent` reads `data-raw` but `data-raw` format is `"94% Grade A"` — if update script ever changes format, textContent becomes inconsistent

**Fix: Replace HTML dashboard with Perplexity reference**
- NEW: Heavy JS (Chart.js, 552-line app.js, 657-line CSS) — first load performance risk
- NEW: `data-theme` attribute switching — if CSS custom properties aren't fully defined for both themes, flash of unstyled content

**Fix: Add 4 missing JSON sources (SkillsMP, SkillHub, ClawHub, skills.sh)**
- NEW: These sources return `null` for listings/stars — totals will be wrong until APIs are live-queried
- NEW: Script may crash if a new source's API endpoint changes or returns unexpected structure

---

## Step 2: Brainstorm Causes (10+)

### Tech failures
1. **API endpoint drift** — SkillsMP/SkillHub/ClawHub APIs change response schema; script silently returns `None`; JSON never updates; dashboard shows stale data
2. **HTML ID mismatch** — update script injects `id="kpi-total-listings"` but HTML uses different ID; `html.replace()` silently finds nothing; dashboard shows hardcoded 0
3. **Null totals collapse** — `totalListingsIndexed` sums `s.get("listings") or 0` — if all sources are null, total is 0, misleading
4. **GitHub rate limiting** — `query_skillssh()` hits GitHub API; unauthenticated limit is 60 req/hr; script fails silently on 403; skills.sh always shows 0
5. **JSON parse drift** — `marketplace-data.json` schema diverges from what `build_data_js()` expects; JS throws on load
6. **CSS/JS cache** — Browser caches old `style.css` or `app.js` after update; dashboard renders incorrectly with no indication
7. **Chart.js CDN failure** — `<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.4/dist/chart.umd.min.js">` fails to load; charts don't render; no error shown to user
8. **Regex DATA block replacement fails** — `const DATA = {...}` regex doesn't match due to formatting changes; HTML regenerates but DATA stays stale

### Process failures
9. **No automated refresh** — `update_marketplace_data.py` must be run manually; dashboard goes stale immediately after first publish
10. **No error alerting** — script fails in CI/cron but nobody checks output; dashboard runs with missing data indefinitely
11. **Metric inflation** — "Total listings" double-counts across sources (SkillsMP and claudemarketplaces.com may overlap); misleading comparative metric
12. **No schema validation** — no JSON Schema validation on `marketplace-data.json`; bad data written silently

### External failures
13. **Source disappears** — skillsdirectory.com or claudemarketplaces.com goes offline; regex matches nothing; `listings: null` propagates; KPI shows 0
14. **Source changes display format** — claudemarketplaces.com HTML changes; regex `r"([\d,]+)\s+skills?"` matches wrong number; dashboard data is off by 10x

---

## Step 2.5: Cascade Tracing (risks ≥ 6)

### API endpoint drift (Tech, Risk 6)
→ Script returns `None` → source not updated → JSON staleness grows
→ No error reported → user不知道 data is stale
→ Dashboard used for decisions → wrong marketplace selected
**3-step cascade confirmed**

### HTML ID mismatch (Tech, Risk 8)
→ `html.replace()` silently no-ops → `data-raw` never written
→ `initKPIs()` reads missing attribute → `parseInt(null)` = `NaN` → `animateCounter` animates to `NaN`
→ Dashboard shows `NaN` in KPI card → trust destroyed
**3-step cascade confirmed**

### GitHub rate limiting (Tech, Risk 7)
→ skills.sh query fails → `listings: null` in JSON
→ Total sum ignores null → total is wrong (missing skills.sh entries)
→ User sees lower total than reality → underestimates ecosystem size
**3-step cascade confirmed**

---

## Step 2.6: AI/LLM Failure Modes

- **Context window overflow** — `build_data_js()` serializes entire JSON including notes/URLs; if JSON grows large, DATA block becomes very large and slows HTML parse
- **Confident hallucination** — "Total listings indexed" shown as precise number (e.g., 12,185) implies precision measurement; actual coverage unknown due to overlap
- **Auto-completion bias** — `animateCounter()` makes data appear more real-time/accurate than it is

---

## Step 3: Categorization

| ID | Cause | Category |
|----|-------|----------|
| 1 | API endpoint drift | Tech |
| 2 | HTML ID mismatch | Tech |
| 3 | Null totals collapse | Tech |
| 4 | GitHub rate limiting | External |
| 5 | JSON parse drift | Tech |
| 6 | CSS/JS cache | Tech |
| 7 | Chart.js CDN failure | External |
| 8 | Regex DATA block fails | Tech |
| 9 | No automated refresh | Process |
| 10 | No error alerting | Process |
| 11 | Metric inflation | Process |
| 12 | No schema validation | Process |
| 13 | Source disappears | External |
| 14 | Source changes format | External |

---

## Step 3.5: Reference Class Forecasting

Similar marketplace aggregator projects (e.g., npms.io, libraries.io) show:
- API changes are the #1 failure mode (happens within 3 months)
- Dashboard staleness is the #2 failure mode
- Manual update processes degrade within 2 weeks

---

## Step 3.6: Success Theater Detection

- **"Total listings" counter** — precise number implies exactness; overlap between sources means actual unique count is lower
- **Security grade A** — shown as dashboard feature; only one source (skillsdirectory.com) provides it; others claim no security scanning
- **KPI animation** — makes data appear more authoritative than a static number

---

## Step 3.8: Operational Verification

- Need to run `python scripts/update_marketplace_data.py --dry-run` to verify it works without network
- Need to verify HTML loads in browser with dev tools open showing no console errors
- Need to verify `data-raw` attributes are actually written after a real run

---

## Step 4: Risk Ratings

| ID | Cause | Likelihood | Impact | Score |
|----|-------|-----------|--------|-------|
| 2 | HTML ID mismatch | 3 | 3 | **9** |
| 1 | API endpoint drift | 3 | 2 | **6** |
| 3 | Null totals collapse | 2 | 3 | **6** |
| 8 | Regex DATA block fails | 2 | 3 | **6** |
| 9 | No automated refresh | 3 | 2 | **6** |
| 4 | GitHub rate limiting | 2 | 2 | **4** |
| 6 | CSS/JS cache | 2 | 2 | **4** |
| 7 | Chart.js CDN failure | 1 | 2 | **2** |
| 5 | JSON parse drift | 1 | 3 | **3** |
| 10 | No error alerting | 2 | 2 | **4** |
| 11 | Metric inflation | 2 | 2 | **4** |
| 12 | No schema validation | 1 | 3 | **3** |
| 13 | Source disappears | 1 | 2 | **2** |
| 14 | Source changes format | 1 | 2 | **2** |

---

## Step 4.5: Dependency Cascades

- **ID mismatch (Risk 9)**: [causes: API endpoint drift creates null data → Dashboard shows NaN] — ID mismatch is independent but both lead to broken KPIs
- **No automated refresh (Risk 6)**: [causes: staleness accumulates → user makes decisions on old data] — causal chain but low urgency

---

## Step 5: Prevent Top 3 + Map to Actions

**Top risks by score:**
1. HTML ID mismatch (9) — Critical
2. API endpoint drift (6) — High
3. Null totals collapse / Regex fails / No refresh (6) — High

### Prevention actions:

**CRIT-001** (HTML ID mismatch — Risk 9):
- Add assertion in update script: verify all target IDs exist in HTML before writing
- Add `--dry-run` validation pass that checks ID presence

**RISK-002** (API endpoint drift — Risk 6):
- Wrap each source query in try/except with structured error logging
- Track last-successful-query timestamp per source in JSON

**RISK-003** (No automated refresh — Risk 6):
- Document cron job requirement in `updateInstructions`
- Add `lastSuccessfulUpdate` field to JSON

---

## Step 6: Warning Signs to Monitor

- `update_marketplace_data.py` output shows `[WARN]` for any source
- Dashboard KPI shows `0` or `NaN` after refresh
- GitHub API calls return 403 in script output
- `marketplace-data.json` `lastUpdated` is more than 7 days old
