---
type: plugin-guidance
load_when: [creation, quality]
priority: mandatory
estimated_lines: 120
---

# Skill Writing Standards (from skill-development)

This reference captures the plugin skill-development patterns that `/skill-ship` must enforce in Phase 2 creation and Phase 3b quality validation.

## Trigger Phrase Format

**Third-person description with concrete trigger phrases:**

```yaml
description: This skill should be used when the user asks to "create a hook", "add a PreToolUse hook", "validate tool use", or mentions hook events (PreToolUse, PostToolUse, Stop). Provides comprehensive hooks API guidance.
```

**Bad trigger formats:**
```yaml
description: Use this skill when working with hooks.       # Wrong person, vague
description: Load when user needs hook help.               # Not third person
description: Provides hook guidance.                        # No trigger phrases
```

**Trigger phrase rules:**
- Use third person ("This skill should be used when...")
- List explicit user phrases they would actually say
- Include concrete scenarios ("create X", "configure Y", "add Z")
- Be specific, not generic — avoid vague triggers like "when user needs help"

## Imperative/Infinitive Form

Write verb-first instructions, not second person:

**Correct:**
```
Parse the frontmatter using sed.
Extract fields with grep.
Validate values before use.
Configure the MCP server with authentication.
```

**Incorrect:**
```
You should start by reading the configuration file.
You need to validate the input.
You can use the grep tool to search.
```

## Progressive Disclosure

**SKILL.md body** (always loaded when skill triggers): 1,500-2,000 words max
- Core concepts and overview
- Essential procedures and workflows
- Quick reference tables
- Pointers to references/examples/scripts
- Most common use cases

**references/** (loaded as needed): unlimited
- Detailed patterns → `references/patterns.md`
- Advanced techniques → `references/advanced.md`
- Migration guides → `references/migration.md`
- API references → `references/api-reference.md`
- Edge cases and troubleshooting

**scripts/** (executed without full context load): unlimited
- Validation tools
- Testing helpers
- Parsing utilities
- Automation scripts

## SKILL.md Structure Checklist

- [ ] Frontmatter has `name` and `description` (required)
- [ ] `description` uses third person + specific trigger phrases
- [ ] Body uses imperative/infinitive form (verb-first)
- [ ] SKILL.md body is lean (1,500-2,000 words ideal, <3,000 max)
- [ ] Detailed content moved to `references/` files
- [ ] All referenced files actually exist
- [ ] Examples are complete and working
- [ ] Scripts are executable and documented

## Structural Warning Signs

❌ **SKILL.md over 3,000 words without references/** — bloats context
❌ **Everything in one file** — no progressive disclosure
❌ **Second person throughout** — "You should...", "You need to..."
❌ **Vague trigger description** — "Provides guidance for X"
❌ **Missing resource references** — body doesn't mention references/, examples/, scripts/

## Skill Anatomy Reference

```
skill-name/
├── SKILL.md            # Required — lean body, imperative form
├── references/         # Detailed docs loaded as needed
│   ├── patterns.md
│   └── advanced.md
├── examples/           # Working code examples
│   └── example.sh
└── scripts/            # Utility scripts
    └── validate.sh
```

## Validation in Phase 3b

When validating a skill in Phase 3b, check:
1. Description uses third person with specific trigger phrases
2. Body is imperative/infinitive form throughout
3. SKILL.md body ≤3,000 words
4. Detailed content lives in references/ not SKILL.md body
5. All referenced files (references/, examples/, scripts/) exist
6. Scripts are executable

**Reference:** Original `skill-development` at `C:\Users\brsth\.claude\plugins\cache\claude-plugins-official\plugin-dev\a52d38e0fc01\skills\skill-development`