# P - Development Repository

## Git Aliases

This repo includes smart-commit for analyzing commits before pushing:

```bash
git smart-commit      # Interactive commit with anti-bleed analysis
git analyze-commit    # Analysis only, no commit
```

### What is Anti-Bleed?

Prevents commits that mix unrelated files (e.g., CSF NIP code + yt-fts project + skills docs).

**Smart-commit checks:**
- Directory coherence (≤3 top-level directories)
- CWO architectural analysis
- Constitutional compliance score
- Test coverage recommendations

**Example:**
```bash
# Stage your changes
git add file1.py file2.md

# Run smart-commit for analysis
git smart-commit
```

## Development Setup

```bash
# Clone repo
git clone https://github.com/EndUser123/P.git
cd P

# Configure git aliases (already set globally)
git smart-commit --help  # Verify it works
```

## Hooks

- **PostToolUse_anti_bleed_suggest.py**: Suggests smart-commit after `git add .`
- **PreToolUse_anti_bleed_gate.py**: Blocks wildcard git add in Claude Code (when functional)

## Documentation

- `docs/CONTENT_MAPPING.md` - Content organization
- `docs/SKILL_REFERENCE.md` - Skill documentation
- `__csf.nip/docs/` - CSF NIP system documentation

