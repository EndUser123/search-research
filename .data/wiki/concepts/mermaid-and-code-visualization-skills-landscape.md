---
title: "Mermaid, Diagram-as-Code, and Code Visualization Skills Landscape"
created: 2026-08-04
source: session-2026-08-04
tags: [visualization, mermaid, diagram, architecture, skills, diagram-as-code, d2, plantuml]
summary: >
  Comprehensive landscape of Mermaid diagram skills, diagram-as-code tool comparison
  (Mermaid vs D2 vs PlantUML vs Structurizr), and code-to-diagram visualization tools
  for AI agent fleets. Includes ranked installable SKILL.md skills, practitioner signal,
  and applicability analysis for the Grok Build / Claude Code workspace.
type: reference
agent: grok
host: both
cognitive_load: 2
verification: multi-source-verified
tier: warm
confidence: 0.88
last_verified: 2026-08-04
half_life_days: 180
stale_after: 2027-02-04
source_url: "https://github.com/mgranberry/mermaid-diagram-skill"
evidence_gaps:
  - "No first-hand testing of mermaid-diagram-skill render pipeline in Grok Build"
  - "D2 TALA layout engine quality not verified (requires paid license)"
relations:
  - "[[skill-auto-invocation-reliability]]"
  - "[[cross-environment-skill-portability]]"
  - "[[agentic-sdlc-skill-lifecycle-architecture]]"
---

# Mermaid, Diagram-as-Code, and Code Visualization Skills Landscape

## Workspace observations (Phase 1a)

1. **The workspace already has 6 diagram skills in the Claude plugin cache** — `mermaid-c4`, `code-flow-visualizer`, `concept-mapper` (cc-skills-sdlc/lab), plus `skill-to-page` and `doc-compiler` (which use Mermaid for HTML output). However, **none are active in the Grok Build session catalog** — they live in `~/.claude/plugins/cache/local/` and are not loaded as invocable slash-skills on this host.
2. **No prior wiki concept covers diagram/visualization skills** — the wiki grep returned only NotebookLM-related matches, not diagram-specific concepts. This is a gap.
3. **The operator wants to "ask for excellent diagrams and explanations"** — meaning they need skills that produce high-quality diagrams AND explanatory text, on demand, in their current Grok Build environment. This is both a "find/install the right skill" problem and a "Mermaid quality" problem.

## Decision context

### Why this research was needed

The operator asked: "find me a great mermaid skill or mermaid skills, and visualize code and architecture skills. I need to be able to ask for excellent diagrams and explanations."

The real question behind this: **the workspace has diagram skills in the Claude plugin cache but they're not active on Grok Build.** The operator needs to know (a) which external skills are best-in-class, (b) whether to bridge existing skills or install fresh ones, and (c) what the diagram-as-code tool landscape looks like so they can choose the right format.

### What alternatives were explored

- **Bridge existing Claude plugin cache skills** (mermaid-c4, code-flow-visualizer, concept-mapper) → viable, they're already on disk, but they're Claude-formatted and may not be optimal quality.
- **Install fresh from GitHub/marketplaces** → the external ecosystem has higher-quality, more actively maintained skills with render pipelines and theming.
- **Use AI-native web services** (Eraser DiagramGPT, CodeViz, DeepRepo) → powerful but require API/internet, not version-controlled, and vendor-locked.
- **Build a custom skill** → unnecessary; the external ecosystem already covers this well.

### What the research changed

The research confirmed that the external skill ecosystem has matured significantly. There are now 8+ installable Mermaid skills with varying quality, plus AI-native diagram tools and code-to-diagram services. The recommendation is to install the best external skills rather than bridging the Claude cache ones.

---

## Part 1: Diagram-as-Code Tool Comparison

### Mermaid (de facto standard) — `[HIGH confidence]`

**Verdict:** The best default for an AI agent fleet. LLMs generate Mermaid by default due to training-set bias. Native GitHub/GitLab/Notion/Obsidian rendering means zero build step.

| Strength | Detail |
|----------|--------|
| LLM-friendly syntax | LLMs produce valid Mermaid on first try with minimal prompting |
| Native rendering | GitHub, GitLab, Notion, Obsidian, VS Code, most SSGs |
| 16+ diagram types | flowchart, sequence, class, ER, state, Gantt, C4, mindmap, git graph, pie, journey, quadrant, etc. |
| Foundation-backed | Active maintenance, weekly releases, 87K+ GitHub stars |

| Weakness | Detail |
|----------|--------|
| Layout control | Auto-layout (Dagre) produces tall narrow columns for dense graphs; edges cross unexpectedly |
| No position pinning | Cannot pin node positions or fine-grained spacing |
| Scaling | Complex diagrams (>30 nodes) become unreadable in both source and rendered |
| Non-technical audience | Reddit signal: "terrific for engineers, terrible for suits" (r/softwarearchitecture, 39pts) |

### D2 — `[MEDIUM confidence]`

**Verdict:** Better-looking than Mermaid, but requires a build step and LLM training data is thinner. Use when Mermaid's layout is inadequate and CI can handle the render step.

- Multiple layout engines (dagre, ELK, TALA). TALA (best engine) requires paid license.
- Supports Markdown text in labels and LaTeX math.
- No native GitHub rendering.
- Smaller ecosystem than Mermaid.

### PlantUML — `[MEDIUM confidence]`

**Verdict:** Best for UML-heavy outputs (class, component, deployment diagrams). Requires Java runtime; no native GitHub rendering. Verbosity creates more room for LLM hallucination.

- Broadest UML coverage (20+ diagram types).
- Massive icon library (AWS, Azure, GCP, Kubernetes).
- Syntax is verbose (`@startuml`, `@enduml`, `skinparam`) — more LLM error surface.
- Battle-tested in enterprise (Confluence, IntelliJ).

### Structurizr DSL — `[LOW confidence for AI fleet use]`

**Verdict:** The C4 model reference implementation, but too heavy and niche for general-purpose AI agent diagramming. Very small LLM training data; unreliable syntax generation.

- Single model generates multiple diagram levels (context → container → component).
- Steep learning curve (must understand DSL + C4 taxonomy).
- Opinionated; fights you if architecture doesn't fit C4.
- 3,800 stars vs Mermaid's 87,000. Low GitHub activity.

### AI-native diagram generators (Eraser DiagramGPT, InfraSketch, Diagramming AI)

**Verdict:** Powerful for rapid generation, but vendor-locked, not version-controlled by default, and require internet/API. Best as a front-end generation layer paired with a diagram-as-code tool for storage.

- **Eraser DiagramGPT** has an MCP server for Claude/Cursor/VS Code integration. Exports to Mermaid/PlantUML.
- **Diagramming AI** supports multi-engine output (Mermaid, PlantUML, Graphviz, D2, Excalidraw) with AI error auto-resolution.
- Free tiers are limited (2-3 projects, 10 credits).

---

## Part 2: Ranked Installable Mermaid Skills

These are pure SKILL.md files (or plugin bundles) that work in any agent that reads SKILL.md format, including Grok Build. Ranked by quality signal + feature completeness.

### Tier 1 — Best all-around

**1. `mermaid-diagram-skill` (mgranberry)** — ⭐ Top pick
- GitHub: [github.com/mgranberry/mermaid-diagram-skill](https://github.com/mgranberry/mermaid-diagram-skill)
- 9+ diagram types, **render pipeline with visual validation** (renders output, catches syntax errors, iterates). Brand-customizable theming via single `references/mermaid-theme.md`.
- Includes render script (`render_mermaid.sh`), syntax-pitfalls reference, per-diagram-type reference files.
- Install: copy to `~/.grok/skills/mermaid-diagram/` or `.claude/skills/mermaid-diagram/`
- MIT license, forked from `coleam00/excalidraw-diagram-skill`

**2. `design-doc-mermaid` (SpillwaveSolutions)** — ⭐ Best for architecture + design docs
- GitHub: [github.com/SpillwaveSolutions/design-doc-mermaid](https://github.com/SpillwaveSolutions/design-doc-mermaid)
- v2.0.0. **Code-to-diagram conversion** (Spring Boot, FastAPI, React, Python ETL, Node, Java). Python utilities for extraction/validation/image conversion.
- Deployment diagrams (AWS/GCP/K8s/serverless), activity, architecture, sequence diagrams.
- Hierarchical decision-tree orchestrator (loads only needed guides on demand).
- Install: clone to `~/.grok/skills/design-doc-mermaid/` or Skilz Marketplace
- MIT license, 12 commits

**3. `mermaid-skill` (WH-2099)** — ⭐ Widest diagram type coverage
- GitHub: [github.com/WH-2099/mermaid-skill](https://github.com/WH-2099/mermaid-skill)
- **23 diagram types** including C4 architecture, ZenUML, Kanban, block, packet, Sankey, XY charts.
- GitHub Action auto-syncs documentation from official mermaid-js repo weekly.
- Install: copy `.claude/skills/mermaid/` or add as git submodule. Invoked via `/mermaid`.
- MIT license, 10 commits

### Tier 2 — Specialized / complementary

**4. `cc-visualization-skills` (tjboudreaux)** — Best visualization bundle
- GitHub: [github.com/tjboudreaux/cc-visualization-skills](https://github.com/tjboudreaux/cc-visualization-skills)
- 6 skills: Mermaid diagrams, ASCII architecture maps, workflow blueprints, state machines, CLI cheatsheets, retrospective templates.
- Proper `.claude-plugin` directory for marketplace distribution.
- Install: `/plugin install tjboudreaux/cc-visualization-skills`

**5. `architecture-diagramming` (britt)** — Best GitHub-architecture-specific
- Source: [britt.github.io/claude-code-skills/skills/architecture-diagramming/](https://britt.github.io/claude-code-skills/skills/architecture-diagramming/)
- Creates GitHub-compatible Mermaid architecture diagrams. Enforces strict syntax rules (no parentheses in labels, matching brackets) to avoid GitHub rendering errors.
- Structured analysis: identify components → determine layers → map relationships → apply boundaries → generate diagram.

**6. `OpenHop` (naorsabag)** — Best interactive data-flow (not static Mermaid)
- GitHub: [github.com/naorsabag/openhop](https://github.com/naorsabag/openhop)
- Step-through interactive flow visualization. Agent generates compact YAML → rendered as interactive web diagram (play/pause/scrub). Token-light (~100 tokens per step).
- 345 commits, npm package, active CI. Local-first, no telemetry.
- Install: `npx openhop init` (auto-detects Claude Code, Cursor, Windsurf, Cline)

### Tier 3 — Reference-quality (lower commitment)

**7. `mermaid-diagrams` (hoodini)** — 373-line reference SKILL.md
- GitHub: [github.com/hoodini/ai-agents-skills/blob/master/skills/mermaid-diagrams/SKILL.md](https://github.com/hoodini/ai-agents-skills/blob/master/skills/mermaid-diagrams/SKILL.md)
- Single SKILL.md covering 10+ diagram types with syntax reference and styling guidance.

**8. `mermaid` (BfdCampos dotfiles)** — GitHub styling focus
- GitHub: [github.com/BfdCampos/dotfiles/blob/main/claude/skills/mermaid/SKILL.md](https://github.com/BfdCampos/dotfiles/blob/main/claude/skills/mermaid/SKILL.md)
- 267 lines focused on GitHub markdown compatibility: dark/light mode, color palettes, common mistakes.

### Existing workspace skills (Claude plugin cache — not active on Grok Build)

| Skill | Location | Status |
|-------|----------|--------|
| `mermaid-c4` | `~/.claude/plugins/cache/local/cc-skills-sdlc/1.0.237/skills/mermaid-c4/` | Installed (Claude), not loaded on Grok Build |
| `code-flow-visualizer` | `~/.claude/plugins/cache/local/cc-skills-sdlc/1.0.237/skills/code-flow-visualizer/` | Installed (Claude), not loaded on Grok Build |
| `concept-mapper` | `~/.claude/plugins/cache/local/cc-skills-lab/1.0.16/skills/concept-mapper/` | Installed (Claude), not loaded on Grok Build |

These are simpler than the Tier 1 external skills — they lack render pipelines, theming, and code-to-diagram conversion.

---

## Part 3: Code-to-Diagram Visualization Tools

These tools **read a codebase and produce diagrams + explanations automatically** — not just render hand-written Mermaid.

### AI-native code visualization services

| Tool | What it does | Integration | Applicability |
|------|-------------|-------------|---------------|
| **CodeViz** | Scans codebases, auto-generates editable C4 architecture diagrams, traces dependencies/data flows | Web app + API | Agent calls via HTTP with repo URL → gets diagram |
| **DeepRepo** | Paste GitHub URL → interactive architecture diagram + AI chat to query codebase structure | Web app + API | Agent submits repo URL → diagram + chat analysis |
| **CodeBoarding** | Open-source: static analysis + LLM reasoning → architecture diagrams + component docs | CLI/GitHub, self-hosted | `git clone` + local execution → diagrams + docs |
| **OverViz** | GitHub URL or plain-English → publication-ready architecture diagram | Web app | URL-in, diagram-out pattern |

### AI coding agent skills (code → diagram + explanation)

| Skill | What it does | Source |
|-------|-------------|--------|
| **explain-code** (dotbrains) | Starts with analogy, draws Mermaid diagrams, walks through code step-by-step, highlights gotchas | [github.com/dotbrains/claude](https://github.com/dotbrains/claude) |
| **cc-visualization-skills** (tjboudreaux) | 6 skills including Mermaid + ASCII architecture maps + state machines | [github.com/tjboudreaux/cc-visualization-skills](https://github.com/tjboudreaux/cc-visualization-skills) |
| **visual-explainer-skill** (ericblue) | Converts content (including code) into visual explanations: whiteboard sketches, infographics, UI wireframes via gpt-image-1.5 | [github.com/ericblue/visual-explainer-skill](https://github.com/ericblue/visual-explainer-skill) |

---

## Part 4: The Visual Explainer Skill Class (deep-dive — 2026-08-04 follow-up research)

The operator flagged that YouTube recently discussed "visual explainer skills" as a distinct class. This is a **different category from Mermaid-only skills** — visual explainers use image generation (or rich HTML rendering) to produce polished visual artifacts, not text-based diagrams. They are the fastest-growing skill class in the AI coding agent ecosystem.

### Two sub-classes

| Sub-class | Mechanism | Output | Best for |
|-----------|-----------|--------|----------|
| **Image-generation** | Uses AI image models (gpt-image-1.5, Nano Banana 2, GPT Image 2) | Raster images (PNG) — infographics, whiteboards, mind maps | Non-technical audiences, presentations, share-ready visuals |
| **HTML/Mermaid rendering** | Generates self-contained HTML pages with CSS, interactive Mermaid, Chart.js | Browser-viewable HTML | Interactive exploration, dashboards, diff reviews |

### Ranked skills in this class

**1. `visual-explainer-skill` (ericblue)** — ⭐ Dominant leader, image-generation
- GitHub: [github.com/ericblue/visual-explainer-skill](https://github.com/ericblue/visual-explainer-skill)
- **10,050 stars**, 1,328 forks, **last updated 2026-08-04** (today). Version 1.3.0. MIT license.
- 7 visual styles: whiteboard, infographic, presentation slides, technical diagrams, colorful mind maps, XMind-style mind maps, UI wireframe mockups.
- Dual backend: OpenAI gpt-image-1.5 (default) or Google Gemini Nano Banana 2.
- Key innovation: **structured prompt engineering** — analyzes content first (concepts, relationships, visual metaphors, layout strategy), then builds 400-800 word prompts using style-specific templates with explicit spatial layout, icons, color palettes, typography.
- Supports `--from mermaid` to convert existing Mermaid diagrams into visual styles. Multi-frame progressive builds. Device-frame mockups.
- Install: `git clone && make install` → `~/.claude/commands/`

**2. `visual-explainer-extension` (Jakedismo)** — ⭐ Best for Gemini CLI
- GitHub: [github.com/Jakedismo/visual-explainer-extension](https://github.com/Jakedismo/visual-explainer-extension)
- **9,406 stars**, 632 forks, last updated 2026-08-04. MIT license.
- Fork of nicobailon re-engineered for Gemini CLI as native extension.
- Hybrid approach: HTML pages (CSS `@layer`, `@container`, premium typography) + AI-generated hero banners/icons via Nano Banana 2.
- 9 visualization commands + 5 image-generation commands. "Design Engineering Mandate" with anti-slop rules.

**3. `visual-explainer` (nicobailon)** — Original HTML/Mermaid variant
- GitHub: [github.com/nicobailon/visual-explainer](https://github.com/nicobailon/visual-explainer)
- 28 stars, 5 forks, 43 commits. MIT license. Version 0.6.3.
- Self-contained HTML pages with real typography, dark/light themes, interactive Mermaid (11 diagram types with zoom/pan), Chart.js dashboards.
- 7 slash commands: `/generate-web-diagram`, `/diff-review`, `/plan-review`, `/project-recap`, `/fact-check`, `/generate-slides`, `/generate-visual-plan`.
- Auto-detects complex tables (4+ rows or 3+ columns) and renders them as styled HTML instead of ASCII.
- Cross-harness: Claude Code, Pi, Codex, OpenCode, Cursor, OpenClaw.

**4. `garden-skills` (ConardLi)** — Best image-generation template library
- GitHub: [github.com/ConardLi/garden-skills](https://github.com/ConardLi/garden-skills)
- **646 stars**, 108 forks, 142 commits. MIT license.
- `gpt-image-2` skill: 18 visual categories, 79 structured prompt templates (posters, UI mockups, infographics, technical diagrams, comics, storyboards, branding).
- `beautiful-article` skill: 10 article types including `visual-essay` and `interactive-explainer`.
- Install: `npx skills add ConardLi/garden-skills -s gpt-image-2`

**5. `higgsfield-ai/skills`** — Multi-model image/video generation
- GitHub: [github.com/higgsfield-ai/skills](https://github.com/higgsfield-ai/skills)
- 8 stars, 80 commits. MIT license.
- Supports 30+ image models (Nano Banana 2, GPT Image 2, Soul V2, Veo 3.1, Kling 3.0, Seedance 2.0).
- `higgsfield-video-explainer`: creates narrated non-photoreal explainer videos. More general-purpose than dedicated visual explainer.

### YouTube coverage

A YouTube video (ID `tdKDHLgQCgY`, April 2026) covers the nicobailon visual-explainer skill specifically, demonstrating how it generates HTML plans and summaries from Claude Code. This is likely the video the operator saw referenced.

### Reddit practitioner signal on visual explainers (Phase 2b — direct MCP search)

**To directly answer the operator's question: the previous /www run did NOT search Reddit specifically for visual explainer skills.** The previous Reddit MCP call was on r/softwarearchitecture about architecture diagram tools broadly. This follow-up corrects that gap.

**Direct Reddit search results on visual explainer skills:**

| Post | Subreddit | Score | Key signal |
|------|-----------|-------|------------|
| "I built a Claude Code skill that turns any topic into visual explanations" (erictblue) | r/ClaudeCode | 2pts, 1 comment | Comment: "This is amazing. thank you!" — positive but very low engagement |
| "Visual Explainer - Open source project" (erictblue cross-post) | r/openclaw | 5pts, 4 comments | Question about OAuth support (wants to use ChatGPT Plus sub) |
| "Claude now creates interactive charts, diagrams and visualizations" | r/ClaudeAI | **1,305pts, 94 comments** | Community calls it "game-changer" — overwhelming enthusiasm for inline visuals |
| "I built a list of 48 design skill files with custom styles" | r/ClaudeAI | **1,055pts, 149 comments** | Style/template-driven skills are the most popular approach |
| "Drawpad - Giving coding agents a whiteboard" | r/ClaudeCode | 36pts, 9 comments | "Blank canvas" problem — users want AI to generate initial layout, then refine |
| "AI + human readable architecture diagrams?" | r/softwarearchitecture | 12pts, 34 comments | **Key insight:** text-based diagram-as-code preferred over image gen for architecture; image gen better for infographics/explanations |
| "Built an agent skill for Excalidraw diagrams with animation + image export" | r/ClaudeAI | 2pts, 4 comments | Existing Excalidraw MCP skills inadequate — want starting point, not blank canvas |

**What people like `[PRACTITIONER]`:**
1. Template-driven prompt engineering (style-specific templates) — the skill's value is in prompt quality, not the model
2. The "analyze first, then visualize" pipeline — extracting concepts/relationships before building the image
3. Conversion from Mermaid → visual styles (bridges the text-diagram and image-generation worlds)
4. Claude's native inline interactive visuals (1,305pts) — users want this in the terminal too, not just web chat

**What people don't like `[PRACTITIONER]`:**
1. The "blank canvas" problem — AI generates Excalidraw but you spend 10-15 minutes placing boxes before real thinking begins
2. Token cost — model generated a 300-line script to render one diagram (Drawpad)
3. Generic built-in skills (Claude's canvas-design) produce ugly, vague mockups — need hard constraints for quality
4. No "save and reference" mechanism — generated diagrams are ephemeral, can't be saved for future use
5. For **architecture diagrams specifically**, image generation is LESS reliable than Mermaid/diagram-as-code (not reproducible, not version-controllable)

**The key tension:** Image-generation visual explainers produce beautiful share-ready visuals but are not reproducible/version-controllable. Mermaid/diagram-as-code produces version-controllable diagrams but with worse aesthetics. The hybrid approach (ericblue's `--from mermaid` flag, Jakedismo's HTML + image overlay) is the emerging solution.

---

## Practitioner signal (Phase 2b)

### Reddit — r/softwarearchitecture (39pts, 47 comments, March 2026)

**Question:** "What's your go-to tool for creating architecture diagrams to share with non-technical stakeholders?"

Key signal:
- **48pts:** "I don't share architecture with non-technical people" — the most-upvoted answer. Architecture diagrams are for engineers, not stakeholders.
- **22pts:** "C4 high-level system context diagrams can be good" — C4 model is the bridge between technical and non-technical.
- **15pts:** "I use Excalidraw extensively nowadays, for both technical and non-technical people" — hand-drawn style is more approachable.
- **6pts:** "Mermaid sequence diagrams are terrific for communicating flow. I embed those into Markdown and generate PDFs to share."
  - Reply (2pts): "You misspelled terrible ;) They are good for engineers but for suits you will struggle."

**Takeaway:** Mermaid is the engineer's default. For non-technical stakeholders, Excalidraw or C4 context diagrams work better. `[PRACTITIONER]`

### Hacker News

- **266pts:** "Diagram as code tool with draggable customizations" (oxdraw) — strong interest in diagram-as-code with visual editing.
- **7pts:** "Progressive Mermaid and streaming diff code blocks - 100x faster render" — Mermaid rendering performance is a real pain point.
- **2pts:** "Excalidraw Architect MCP for AI Based IDEs" — Excalidraw + MCP for AI-native diagramming.

### Reddit — r/nocode (August 2025)

**Question:** "Best AI Diagram / Flow Chart Generator"
- Mermaid is mentioned as the primary diagram-as-code tool for AI workflows.
- Python → Mermaid → visual tweak is a common pattern for data-driven diagrams.

---

## Disconfirmation results (Round 3)

**Emerging conclusions tested:**
1. Mermaid is the best diagram-as-code format for AI agents → **CONFIRMED.** No source argued for a different default. D2/PlantUML are secondary, not primary.
2. There are high-quality installable Mermaid skills → **CONFIRMED with caveat.** 8+ skills found, but quality varies widely. The render-pipeline + theming features distinguish Tier 1 from Tier 3.
3. Code-to-diagram tools exist but are mostly web services → **CONFIRMED.** CodeViz, DeepRepo, OverViz are all web services. CodeBoarding is the only self-hosted option.

**Disconfirmation queries used:** `"mermaid diagram problems limitations LLM AI agent syntax errors layout issues"`, `"claude code skill mermaid broken not working SKILL.md issue"`

**Result:** No refuting evidence found. The known limitations (Mermaid layout, non-technical audience readability) are well-documented and not controversial.

---

## Applicability gate (Round 3.25)

For each top recommendation:

**FINDING:** Install mermaid-diagram-skill (mgranberry) as primary Mermaid skill
- CONDITIONS: Agent reads SKILL.md, Mermaid renders in target medium
- OUR CONTEXT: Grok Build reads SKILL.md; workspace uses GitHub/markdown heavily
- APPLIES? **Yes** — SKILL.md is the native skill format for this host
- PROMOTE? **Yes** — primary recommendation

**FINDING:** Install design-doc-mermaid (SpillwaveSolutions) for architecture + design docs
- CONDITIONS: Agent reads SKILL.md, Python available for utilities
- OUR CONTEXT: Python available, workspace produces design docs (`/design` skill)
- APPLIES? **Yes** — complements existing `/design` skill with diagram generation
- PROMOTE? **Yes** — secondary recommendation for architecture workflows

**FINDING:** Use Eraser DiagramGPT MCP for AI-native generation
- CONDITIONS: API access, internet, MCP server support
- OUR CONTEXT: MCP is available, but vendor-lock and API cost are concerns
- APPLIES? **Partially** — viable for one-off generation, not as primary workflow
- PROMOTE? **Conditional** — include with caveat about vendor-lock

**FINDING:** Use CodeBoarding for codebase-to-diagram (self-hosted)
- CONDITIONS: `git clone` + local execution
- OUR CONTEXT: Multi-agent fleet, worktrees available
- APPLIES? **Yes** — self-hosted, no vendor-lock, fits fleet architecture
- PROMOTE? **Yes** — for code visualization workflows

---

## Host invariant check (Round 3.5)

Scanned recommendations against known host invariants ([[invariants-beat-environment-comfort]], [[concurrent-cdp-auth-contention]]):

- **SKILL.md installation:** Safe. No browser state, no multi-terminal contention, no destructive operations.
- **Skill location:** Must go in `~/.grok/skills/<name>/SKILL.md` for user scope (per skill-location conventions).
- **Eraser DiagramGPT MCP:** Would add an MCP server. Safe — no browser state contention. But check MCP transport issues per `[[tool-fallbacks]]`.
- **CodeBoarding local execution:** Safe — static analysis + LLM, no shared browser state.
- **No `--cookies-from-browser` patterns** in any recommended tool.
- **No multi-terminal isolation violations** detected.

**Result:** Host invariant check passed. No violations found.

---

## Recommendations for this workspace

1. **Install `mermaid-diagram-skill` (mgranberry) as the primary Mermaid skill.** It has the best feature set (render pipeline, theming, per-type references). Install to `~/.grok/skills/mermaid-diagram/SKILL.md`. Confidence: HIGH.
2. **Install `design-doc-mermaid` (SpillwaveSolutions) for architecture and design-doc workflows.** Code-to-diagram conversion for multiple languages, Python utilities for validation/image export. Complements the existing `/design` skill. Confidence: HIGH.
3. **Install `cc-visualization-skills` (tjboudreaux) for the visualization bundle.** 6 skills (Mermaid + ASCII architecture + workflows + state machines + cheatsheets + retro templates). Confidence: MEDIUM.
4. **Install `visual-explainer-skill` (ericblue) for the image-generation visual explainer class.** 10K+ stars, 7 visual styles, Mermaid→image conversion, dual backend (gpt-image-1.5 + Nano Banana 2). This is the skill class YouTube discussed. Best for producing polished, share-ready infographics and explanations. Confidence: HIGH.
5. **Consider `mermaid-skill` (WH-2099) for maximum diagram-type coverage (23 types).** Auto-syncs upstream Mermaid docs. Good as a reference skill. Confidence: MEDIUM.
6. **For interactive flows, evaluate `OpenHop` (naorsabag).** Step-through data-flow visualization is a different paradigm than static Mermaid. Token-light and local-first. Confidence: LOW (needs evaluation).

**For code visualization (read code → diagram + explanation):**
7. **Evaluate `explain-code` (dotbrains) as a Claude Code skill.** Analogy + Mermaid + step-through. Fits the "ask for excellent diagrams and explanations" use case directly. Confidence: MEDIUM.
8. **Consider CodeBoarding for codebase-wide architecture diagrams.** Self-hosted, static-analysis + LLM. Fits the fleet architecture. Confidence: MEDIUM.

**Not recommended for this workspace:**
- Structurizr DSL — too heavy, too niche, poor LLM syntax reliability.
- Eraser DiagramGPT / InfraSketch / Diagramming AI — vendor-locked, not version-controlled, internet-dependent. Use as secondary tools only.

---

## What this means for the workspace

The external Mermaid skill ecosystem has matured well beyond what the Claude plugin cache provides. The workspace's existing `mermaid-c4`, `code-flow-visualizer`, and `concept-mapper` are simpler than the Tier 1 external skills — they lack render pipelines, theming, and code-to-diagram conversion. Installing 2-3 external skills would close the gap.

The key insight: **"excellent diagrams" requires both the right tool (Mermaid for engineers, Excalidraw/C4 for non-technical) AND the right skill (one with a render pipeline that validates output).** The best skills (mgranberry, SpillwaveSolutions) include validation loops that catch syntax errors before delivery — this is what separates "good" from "excellent."

## Falsifier

This concept is wrong if:
- Within 6 months, D2 replaces Mermaid as the LLM default for diagram-as-code (unlikely — Mermaid's training-set advantage is structural).
- The external skills listed here are abandoned (check `gh repo view --json updatedAt,stargazerCount` before installing).
- A new AI-native format (e.g., Eraser's syntax) becomes the dominant version-controlled format and Mermaid becomes legacy.

## Receipts

| Claim | Receipt |
|-------|---------|
| Workspace has mermaid-c4 in Claude plugin cache | `read_file` of `~/.claude/plugins/cache/local/cc-skills-sdlc/1.0.237/skills/mermaid-c4/SKILL.md` (Phase 1a) |
| Workspace has code-flow-visualizer in Claude cache | `read_file` of `~/.claude/plugins/cache/local/cc-skills-sdlc/1.0.237/skills/code-flow-visualizer/SKILL.md` (Phase 1a) |
| Workspace has concept-mapper in Claude cache | `read_file` of `~/.claude/plugins/cache/local/cc-skills-lab/1.0.16/skills/concept-mapper/SKILL.md` (Phase 1a) |
| These skills NOT in Grok Build session catalog | System-reminder skill list inspection (Phase 1a) — none of the 3 appear in invocable skills |
| mermaid-diagram-skill (mgranberry) exists with render pipeline | DDG subagent finding, source: `github.com/mgranberry/mermaid-diagram-skill` |
| design-doc-mermaid (SpillwaveSolutions) v2.0.0 with code-to-diagram | DDG subagent finding, source: `github.com/SpillwaveSolutions/design-doc-mermaid` |
| Mermaid "terrific for engineers, terrible for suits" | Reddit MCP `get_post_details` on `r/softwarearchitecture/comments/1rirj2e` (39pts, 47 comments) |
| Mermaid 87K+ stars, native GitHub rendering | DDG subagent finding, source: `github.com/mermaid-js/mermaid` |
| oxdraw (diagram-as-code) 266pts on HN | HN Algolia API search result |
| No prior wiki concept on diagram skills | `grep` of `P:/.data/wiki/concepts/` returned only NotebookLM-related matches |
| Mermaid best default for AI agents | Confirmed by 2 independent sources (diagram-as-code subagent + Reddit signal); disconfirmation pass found no refuting evidence |

---

## Cross-references

- [[skill-auto-invocation-reliability]] — skill triggering is the bottleneck for diagram skills
- [[cross-environment-skill-portability]] — SKILL.md portability between Grok Build and Claude Code
- [[agentic-sdlc-skill-lifecycle-architecture]] — where diagram skills fit in the SDLC lifecycle
- [[design-doc-spec-system-patterns]] — Mermaid skills complement design-doc workflows
- [[improve-codebase-architecture]] — code visualization supports architecture improvement

## Auto-related

- [[skill-catalog]]
- [[skill-graph]]
- [[claude-code-external-tool-integration-via-mcp]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]
- [[claude-code-skills-and-mcp-integration]]

