---
title: "Expected UI/UX Features — Modern Apps, Great Apps, Web Pages, TUIs"
created: 2026-07-24
source: session-2026-07-24
tags: [ui, ux, design, accessibility, best-practices, checklist, web, mobile, desktop, tui]
summary: >
  Tiered checklist of expected UI/UX features: table-stakes (all apps),
  good (competitive apps), great (category-defining apps), web-specific,
  and TUI-specific. Sources: Forbes Tech Council table-stakes predictions,
  Activate Design 7 must-haves, UX Pilot 2026 trends, WCAG 2.1, WebAIM.
  Includes a TUI-mapped checklist for the Keep-Smaller-Copy app.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
---

## Decision context

This research was motivated by the red-team UX audit of Keep-Smaller-Copy
(`D:\.code\Keep-Smaller-Copy`), a Textual TUI for file management. The operator
asked "what are the expected features all apps should have these days?" to
establish a baseline for evaluating the TUI against. The findings are structured
as tiers so any future app (TUI, desktop, or web) can be evaluated against the
same reference.

## Tier 1: Table-stakes (ALL apps must have — absence is a defect)

| Feature | Why it's baseline | Source |
|---------|-------------------|--------|
| **Responsive to input** — every click/key does something visible | "Did it register?" anxiety kills trust | Activate #5, UX Pilot #6 |
| **Clear error messages with recovery steps** — not "Error occurred" | Generic errors are the #1 UX complaint | Activate #7, Forbes |
| **Loading/progress indicator** for anything >1s | Blank screen = "is it frozen?" | Activate #5, UX Pilot #6 |
| **Keyboard navigation** — all actions reachable without mouse | Accessibility baseline (WCAG 2.4.3) | WCAG 2.1 |
| **Dark mode / theme support** | Battery + comfort; 85% of users prefer it | Activate #6, UX Pilot #5 |
| **Undo / confirmation for destructive actions** | Data loss = instant uninstall | Activate #7, Forbes |
| **State persistence** — remember last session (paths, preferences) | Repeating setup every launch is friction | Activate #5 |
| **Sufficient color contrast** — WCAG AA (4.5:1 text) | Legal requirement in many jurisdictions | WCAG 2.1 §1.4.3 |
| **Empty states with guidance** — not just blank | "No results" without guidance is a dead end | Activate #7 |
| **Fast startup / no unnecessary waits** | 32% bounce rate increase 1→3s load | Activate #5 (Google data) |

## Tier 2: Good apps (competitive — their absence makes an app feel "cheap")

| Feature | Why it differentiates | Source |
|---------|----------------------|--------|
| **Micro-interactions** — button press feedback, toggle animations, haptic cues | Confirms action registered; feels alive | UX Pilot #6, Activate #5 |
| **Contextual onboarding** — show help at point of need, not upfront wall | 60-second uninstall rule | Activate #1 |
| **Smart search/filter** — incremental filter on large lists | No one scrolls 500 rows manually | Carlos Smith checklist |
| **Column sorting** — click headers to sort | Data without sort = read-only dump | UX Planet |
| **Confirmation dialogs with summary** — "Move 47 files, save 12.3 GB?" | Lets user verify intent before committing | Activate #7 |
| **Swap/invert common operations** — "Swap Source/Target" | The #1 user error (paths swapped) gets a one-click fix | Session observation |
| **Dynamic labels** — button text reflects current mode | "Move" vs "Delete" confusion = data loss | Session observation |
| **Export results** — CSV/JSON of what was processed | Audit trail after batch operations | DevPulse |
| **Offline / degraded mode** — graceful handling when resources unavailable | Web: PWA; Desktop: local cache | Activate #7, UX Pilot #8 |

## Tier 3: Great apps (category-defining — creates loyalty and delight)

| Feature | Why it's exceptional | Source |
|---------|---------------------|--------|
| **Predictive / anticipatory UI** — surface the next likely action | Reduces clicks; feels like the app "knows" you | Forbes (Bauer, Wong), UX Pilot #1 |
| **Adaptive layout** — changes based on context (time, usage, device) | 22% task-completion boost (Design Shack data) | UX Pilot #7 |
| **Agentic UX** — app takes initiative, shows reasoning, allows override | "Here's what I did and why" transparency | UX Pilot #3 |
| **Consistent cross-platform experience** — same data, same flow everywhere | "Total experience" (Forbes, Schuerman) | Forbes |
| **Personalization with transparency** — "Recommended because you did X" | Personalization without explanation feels creepy | Activate #4, Forbes (Adel) |
| **Micro-copy with personality** — error messages and empty states that humanize | Turns frustration into a moment of delight | Activate #7 |
| **Performance profiling baked in** — app optimizes its own load times | AI-driven asset optimization | Forbes (Farseev) |
| **Inclusive design beyond compliance** — motion sensitivity, cognitive load, neurodiversity | 15% of global population has a disability; inclusive sites see 35% higher engagement | UX Pilot #8, WebAIM |

## Tier 4: Web pages specifically (in addition to Tier 1-3)

| Feature | Why web-specific | Source |
|---------|-----------------|--------|
| **Responsive design** — works 320px to 4K | WCAG 1.4.10 Reflow requirement | WCAG 2.1 |
| **Semantic HTML + ARIA** — screen reader navigability | WCAG 4.1.2 (Name, Role, Value) | WCAG 2.1 |
| **Lighthouse score >90** — performance, accessibility, SEO, best practices | Google ranking signal; user retention | minimum-code.com |
| **No layout shift (CLS < 0.1)** — content doesn't jump during load | Core Web Vitals ranking factor | cygnis.co |
| **HTTPS + security headers** — not optional anymore | Browser warnings destroy trust | WCAG, WebAIM |
| **Service worker / PWA** — installable, works offline | App-like experience in browser | UX Pilot #8 |
| **Open Graph / social meta** — previews when shared | First impression happens on social media | thecyberiatech.com |
| **Reduced motion support** — `prefers-reduced-motion` media query | WCAG 2.3.3 (vestibular disorders) | WCAG 2.1 |
| **404/500 pages with recovery** — not default server error | Lost user = lost customer | Activate #7 |

## Tier 5: TUI-specific (terminal user interfaces like Keep-Smaller-Copy)

Not all desktop/web features apply to TUIs. Here's the TUI-mapped checklist:

| Feature | TUI equivalent | Keep-Smaller-Copy status |
|---------|---------------|--------------------------|
| Progress indicator | Status counter / ProgressBar | ❌ Missing (phase text only) |
| Confirmation before destructive action | ModalScreen dialog | ❌ Missing |
| Column sorting | DataTable.sort() | ❌ Missing |
| Search/filter results | Input filter on DataTable | ❌ Missing |
| Keyboard shortcuts visible | Footer bindings (✅) + help | ✅ Has Footer, ❌ no help panel |
| Dark mode | Textual theme system | ⚠️ Available but no in-app toggle |
| Error recovery | Descriptive status messages | ✅ Has diagnostic text |
| Empty state guidance | "0 to move (diagnosis)" | ✅ Has diagnostic (added this session) |
| State persistence | settings.json save/load | ✅ Has persistence + save-on-quit |
| Undo | Transaction log / rollback | ❌ Missing |
| Dynamic labels | Switch ON/OFF labels, button text | ✅ Switch labels (added), ❌ button not dynamic |
| Export results | CSV/JSON output | ❌ Missing |

## Sources

- https://www.activate.co.nz/Blog/What-Makes-a-Good-App-in-2025-7-UI-UX-Must-Haves-for-a-Seamless-User-Experience/ — 7 must-have UI/UX features (authority=2, recency=3, evidence=3)
- https://www.forbes.com/councils/forbestechcouncil/2023/03/02/16-tech-experts-predict-table-stakes-ux-trends-coming-in-the-next-five-years/ — Forbes Tech Council table-stakes predictions (authority=3, evidence=2)
- https://uxpilot.ai/blogs/mobile-app-design-trends — 2026 mobile design trends (authority=2, recency=3, evidence=3)
- https://www.w3.org/TR/WCAG21/ — WCAG 2.1 accessibility guidelines (authority=3, recency=3)
- https://www.minimum-code.com/blog/ui-ux-best-practises-web-app-design-2026 — Web app UI/UX best practices 2026 (authority=2, recency=3)
- https://cygnis.co/blog/web-app-ui-ux-best-practices-2025/ — Web app UI/UX 2025 (authority=2, recency=3)
- https://devpulse.com/insights/ux-ui-design-best-practices-2025-enterprise-applications/ — Enterprise UX/UI best practices (authority=2)

## Disconfirmation pass

Queries: "UI UX features unnecessary overrated", "accessibility not worth investment evidence"
Result: No credible source argues against any Tier 1 feature. The only disconfirming
evidence was for Tier 3 (predictive UI can feel invasive — confirmed and qualified as
"personalization with transparency"). One source (UX Pilot) noted glassmorphism
"wasn't a universal solution" for AR/3D. No Tier 1 or Tier 2 features were challenged.

## Related

- [[textual-tui-best-practices]]@related — Textual-specific patterns
- [[tui-frameworks-for-personal-scripts]]@related — Framework selection
- [[tui-testing-strategy-python-textual]]@related — Testing strategy
- avant-garde-ui@related — Visual design skill
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
