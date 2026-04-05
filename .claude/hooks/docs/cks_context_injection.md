# CKS Context Injection

**Version:** 2.0.0  
**Updated:** 2025-01-19  
**Purpose:** Progressive disclosure of prior conversation context

---

## Problem Solved

Claude Code would forget prior context when users reference past discussions:
- "We've been down this road before"
- "You keep making the same mistake"
- "Check CKS for what we discussed"

Previously, the CKS hook existed but used a non-existent `ClaudeCodeCKSBridge` module.

## Solution: Direct CKS Integration

CKS context injection now works directly in `UserPromptSubmit_router.py` using the CKS unified interface.

## Trigger Phrases

CKS is queried when the prompt contains any of these phrases:

**Explicit requests:**
- "check cks", "cks context", "search cks", "query cks"

**Prior context signals:**
- "prior context", "previous conversation", "past discussion"
- "we discussed", "we talked about", "as we mentioned"

**Frustration/memory signals:**
- "you forget", "been down this road", "we've done this before"
- "you keep making", "same mistake", "already told you"

**Historical reference:**
- "remember when", "last time", "earlier we", "before you"

## Performance

| Scenario | Time |
|----------|------|
| No trigger phrase | ~60ms (CKS skipped) |
| With trigger phrase | ~5-7s (CKS queried) |

CKS is slow due to model initialization. By default, it only runs when triggered.

## Configuration

```json
// settings.json
{
  "CKS_INTEGRATION_ENABLED": "true",
  "CKS_HOOK_FAST_MODE": "false"  // Set true to disable CKS completely
}
```

## Output Format

When CKS finds relevant memories:

```markdown
## 📚 Related Context from CKS

**1. [memory]**
[content from CKS entry]

**2. [pattern]**
[content from CKS entry]

---
*Consider this prior context if relevant.*
```

## Filtering

Results are filtered to remove:
- Template content (`[FILL]` markers)
- Meta-content (YAML frontmatter)
- Very short entries (<50 chars)

## Architecture

```
UserPromptSubmit_router.py
├── run_cks_context()
│   ├── Check trigger phrases
│   ├── If triggered: query CKS unified interface
│   ├── Filter low-quality results
│   └── Format and return context
└── HOOKS["cks_context"] (priority 3)
```

## Known Limitations

1. **Slow first query**: CKS model init takes ~5s
2. **Keyword search only**: Semantic search disabled (too slow for hooks)
3. **Content quality varies**: CKS has some template/meta content

## Future Improvements

- CKS daemon for faster queries (model stays loaded)
- Background pre-warming of CKS
- Semantic search with timeout fallback
- Better content quality filtering

## Related Files

- `P:/.claude/hooks/UserPromptSubmit_router.py` - Main integration
- `P:/__csf/src/cks/unified.py` - CKS unified interface
- `P:/.claude/hooks/user_prompt_submit_cks.py` - Legacy (broken, uses missing bridge)
