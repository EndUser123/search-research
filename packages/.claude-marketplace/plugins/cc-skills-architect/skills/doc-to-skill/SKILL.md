---
name: doc-to-skill
description: Convert documentation into Claude Skills using automated scraping and AI enhancement
version: "1.0.0"
status: "stable"
category: generation
enforcement: advisory
triggers:
aliases:
suggest:
workflow_steps:
  - id: configure
    name: Configure source + selectors
    description: User selects source type (website, GitHub, PDF, local) and configures selectors or config file
  - id: convert
    name: Convert + enhance
    description: Run conversion with optional enhancement (local LLM or Anthropic API)
  - id: portability
    name: Portability pass
    description: Apply the 6 output-pitfall guards before validation. See PHASE 2.5 below.
  - id: validate
    name: Validate generated skill
    description: Run scripts/_validate.py (from template) and confirm all checks pass
---
# Documentation to Skill Converter

Automatically convert documentation (websites, GitHub repos, PDFs) into production-ready Claude Skills.

## Purpose

Convert documentation (websites, GitHub repos, PDFs) into production-ready Claude Skills using automated scraping and AI enhancement.

## Project Context

### Constitution/Constraints
- Follows CLAUDE.md constitutional principles
- Solo-dev appropriate (Director + AI workforce model)
- On-demand execution (no background services)
- Evidence-first (actual documentation content)

### Technical Context
- Website scraping with CSS selectors
- GitHub AST analysis for API extraction
- PDF processing with OCR support
- llms.txt detection for faster processing
- Async mode for 2-3x speed improvement

### Architecture Alignment
- Integrates with /skills-migrate workflow
- Part of CSF NIP generation tools
- Supports /orchestrator and /build

## Your Workflow

1. Select source type (website/github/pdf/local)
2. Configure selectors or options
3. Run conversion with optional enhancement
4. Validate generated skill structure
5. Test skill functionality

## Validation Rules

- YAML frontmatter must be valid
- Proper categorization applied
- Content quality verified
- Enhancement completed if enabled
- File structure compliant

## Quick Usage

```bash
/doc-to-skill https://docs.python.org/ --name python-reference
/doc-to-skill github:owner/repo --name my-library
/doc-to-skill path/to/document.pdf --name pdf-knowledge
```

## What It Does

| Source Type | Description | Output |
|-------------|-------------|--------|
| **Website** | Scrapes documentation sites using CSS selectors | Structured skill with categorized sections |
| **GitHub** | Performs AST analysis to extract APIs, functions, classes | Code-aware skill with signature detection |
| **PDF** | Extracts text, code, images, tables (with OCR) | Multi-format skill with visual content |

## Installation

```bash
pip install skill-seekers>=2.0 beautifulsoup4 requests
```

## Usage Modes

### Website Documentation

```bash
/doc-to-skill https://example.com/docs --name my-docs
/doc-to-skill https://example.com/docs --name my-docs --selector "article"
/doc-to-skill https://example.com/docs --name my-docs --include "/api,/reference"
```

### GitHub Repository

```bash
/doc-to-skill github:owner/repo --name repo-skill
/doc-to-skill github:owner/repo --name repo-skill --detect-conflicts
/doc-to-skill github:owner/repo --name repo-skill --branch develop
```

### PDF Document

```bash
/doc-to-skill path/to/document.pdf --name pdf-skill
/doc-to-skill path/to/scanned.pdf --name scanned-docs --ocr-enabled
/doc-to-skill path/to/document.pdf --name pdf-skill --extract-images --extract-tables
```

### Local Documentation

```bash
/doc-to-skill ./docs --name local-docs --format markdown
/doc-to-skill ./docs/*.md --name combined-docs
```

## Configuration

Create a JSON config file for complex scrapes:

```json
{
  "name": "my-library",
  "description": "Comprehensive documentation for MyLibrary",
  "base_url": "https://mylib.dev/docs",
  "selectors": {
    "main_content": "article, main",
    "title": "h1",
    "code_blocks": "pre code"
  },
  "url_patterns": {
    "include": ["/api", "/guides"],
    "exclude": ["/blog"]
  },
  "categories": {
    "getting_started": ["quick-start", "installation"],
    "api_reference": ["endpoints", "classes"]
  }
}
```

Use the config:
```bash
/doc-to-skill --config my-library.json
```

## Enhancement Options

```bash
/doc-to-skill https://example.com/docs --name my-docs --enhance-local  # Local LLM
/doc-to-skill https://example.com/docs --name my-docs --enhance-api     # Anthropic API
```

## Advanced Features

- **llms.txt Detection**: Automatically uses llms.txt if available (10x faster)
- **Async Mode**: 2-3x faster with `--async` flag
- **Checkpoint/Resume**: Long jobs support resuming if interrupted
- **Router Skills**: Create router skills for large documentation with `--router-mode`

## Output Structure

```
my-docs/
├── SKILL.md              # Main skill file with YAML frontmatter
├── references/           # Extracted documentation
│   ├── getting-started.md
│   ├── api-reference.md
│   └── examples.md
└── resources/            # Optional extracted resources
    ├── images/
    └── diagrams/
```

## Evidence-First Principles

### E1 — Evidence before claims
Before claiming code is absent, unchanged, or non-existent — search the codebase and verify with tools first. Claims of absence are only valid after confirmed Read/Grep/git failures.

### E4 — Investigate before asking
Do NOT answer without reading relevant source files first. Do not ask the user for information you can obtain yourself via Read, Grep, Bash, git, or available MCP tools.

### E5 — Anti-lazy escape hatch
Prohibited:
- "I assume", "I think", "probably" without tool verification
- Claiming something doesn't exist without confirmed tool failure
- Skipping evidence gathering because the answer seems obvious

## PHASE STRUCTURE

```
PHASE 1: CONFIGURE + SCRAPE (Generation) — Select source type, configure selectors/options
    ↓ STOP: Present source configuration before conversion
PHASE 2: CONVERT + ENHANCE (Generation) — Run conversion with optional enhancement
    ↓ STOP: Present converted skill preview before validation
PHASE 2.5: PORTABILITY PASS (Generation) — Apply the 6 output-pitfall guards
    ↓ STOP: Confirm portability pass report before validation
PHASE 3: VALIDATE (Validation) — Validate YAML, categorization, structure compliance
```

**STOP conditions:**
- Between PHASE 1 and PHASE 2: STOP after source configured (confirm before scraping)
- Between PHASE 2 and PHASE 2.5: STOP after conversion completes (present preview before portability pass)
- Between PHASE 2.5 and PHASE 3: STOP after portability report (user confirms before validation)
- Between PHASE 3 and end: STOP after validation report (user confirms before test)

**Key separation**: Configuration and scraping is Generation. Conversion and enhancement is Generation. Portability pass is Generation. Validation is Validation.

## PHASE 2.5 — Portability Pass (mandatory)

Before running Phase 3 validation, apply the 6 output-pitfall guards. Each guard has a single mechanical action. Skip none.

| # | Pitfall | Action |
|---|---------|--------|
| 1 | Frontmatter `script:` keys for inlined body | If a phase's body inlines code, drop the `script:` key from that `workflow_steps[]` entry. Don't ship a script path that doesn't exist on disk. |
| 2 | Body code-block header drift | Inline body code blocks must NOT have a `# scripts/foo.py` header comment that disagrees with the actual file on disk. Either strip the header, or rename the file to match. |
| 3 | Validator blind spot | Always include `scripts/_validate.py` (copy from `scripts/_validate_template.py` in this skill) and run it. The template has the cross-check loop and structural anti-pattern check. |
| 4 | `output/` is not a registered slot | Output a `REGISTRATION.md` next to `SKILL.md` listing the 5 actions required to ship (move to `skills/<plugin>/skills/<name>/`, create `plugin.json`, register in `marketplace.json`, bump + reload). |
| 5 | Session-provenance leakage | Run a portability pass: replace absolute paths with env vars or CLI args; drop session UUIDs from helper-script docstrings (keep only in frontmatter `metadata.source_session`); abstract concrete filenames in body prose to generic principles. |
| 6 | Anti-patterns table is brittle | Use a structural anti-patterns table (Trap | Symptom | Mitigation columns) instead of a keyword-substring check. The structural check is robust to rephrasing. |

**Portability pass report** — emit a short markdown report after Phase 2.5 listing what was parameterized, what was abstracted, and what was registered. The user must confirm before Phase 3.

## Quality Gates

Generated skills validated for:
- Valid YAML frontmatter
- Proper categorization
- Content quality
- Enhancement completion
- File structure compliance
- Phase 2.5 portability pass applied (all 6 guards)
- `scripts/_validate.py` passes (uses template)
