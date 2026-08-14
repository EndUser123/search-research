---
source_id: "ecaa5406-fba9-4fd1-93eb-0eddd51e97a9"
title: "ComposioHQ_awesome-claude-skills_part-003.md"
notebook_id: 3c6d83d9-9945-43d7-a6a0-d8a446ce9d3a
url: null
type: 4
exported: 2026-08-08
---

# ComposioHQ_awesome-claude-skills_part-003.md
ComposioHQ/awesome-claude-skills — Part 3

Total files: 1001 | Part: 3/3 | Files in part: 1

File List

webapp-testing/SKILL.md

Content

webapp-testing/SKILL.md

User task → Is it static HTML? ├─ Yes → Read HTML file directly to identify selectors │ ├─ Success → Write Playwright script using selectors │ └─ Fails/Incomplete → Treat as dynamic (below) │ └─ No (dynamic webapp) → Is the server already running? ├─ No → Run: python scripts/with_server.py --help │ Then use the helper + write simplified Playwright script │ └─ Yes → Reconnaissance-then-action: 1. Navigate and wait for networkidle 2. Take screenshot or inspect DOM 3. Identify selectors from rendered state 4. Execute actions with discovered selectors

Multiple servers (e.g., backend + frontend):

To create an automation script, include only Playwright logic (servers are managed automatically):

Reconnaissance-Then-Action Pattern

Inspect rendered DOM:

Identify selectors from inspection results

Execute actions using discovered selectors

Common Pitfall

❌ Don't inspect the DOM before waiting for networkidle on dynamic apps ✅ Do wait for page.wait_for_load_state('networkidle') before inspection

Best Practices

Use bundled scripts as black boxes - To accomplish a task, consider whether one of the scripts available in scripts/ can help. These scripts handle common, complex workflows reliably without cluttering the context window. Use --help to see usage, then invoke directly.

Use sync_playwright() for synchronous scripts

Always close the browser when done

Use descriptive selectors: text=, role=, CSS selectors, or IDs

Add appropriate waits: page.wait_for_selector() or page.wait_for_timeout()

Reference Files

examples/ - Examples showing common patterns:

element_discovery.py - Discovering buttons, links, and inputs on a page

static_html_automation.py - Using file:// URLs for local HTML

console_logging.py - Capturing console logs during automation
