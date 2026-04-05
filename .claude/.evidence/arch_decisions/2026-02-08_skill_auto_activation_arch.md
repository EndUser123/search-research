# Architecture Decision: Skill Auto-Activation System

**Date:** 2026-02-08
**Template:** fast.md
**Domain:** Generic

---

## Decision Statement

Implementing **Option A: Tiered Auto-Activation** - local skill-rules.json system for critical/frequently-used skills (/tdd, /debug, /rca, /build, /commit, /v) while relying on Claude Code cloud discovery for remaining skills. This hybrid approach fills documented gaps in Claude Code's default discovery while avoiding full local duplication.

---

## Options

**Option A:** Tiered Auto-Activation (Local + Cloud)
- **Pro:** Best of both worlds - local control for critical skills, cloud for discovery
- **Pro:** Reduces vendor lock-in on workflow-critical skills
- **Pro:** Fast response for high-frequency skills (no cloud latency)
- **Con:** Maintains two systems
- **Con:** More complex configuration
- **Differs on:** Vendor dependency, local control vs. cloud convenience

**Option B:** Cloud-Only (Default Claude Code)
- **Pro:** Zero local maintenance
- **Pro:** Single system to understand
- **Pro:** Automatic updates from Anthropic
- **Con:** Users report insufficient discoverability (GitHub issues #10246, #11266)
- **Con:** No local control over skill patterns
- **Con:** CLI lacks autocomplete parity with VS Code
- **Differs on:** Maintenance burden, discovery reliability

**Option C:** Local-Only (Full skill-rules.json)
- **Pro:** Complete local control
- **Pro:** Works offline/air-gapped
- **Pro:** Custom patterns for your infrastructure
- **Con:** High maintenance burden (117+ skills to configure)
- **Con:** Misses cloud improvements
- **Con:** Duplication of effort
- **Differs on:** Control vs. maintenance

---

## Recommendation

**Option A (Tiered Auto-Activation)** — Based on user reports (GitHub issues #10246, #11266) and community solutions (diet103, Reddit "Skill Matcher"), Claude Code cloud discovery is insufficient for critical workflows. Local tier fills the gap without full duplication.

---

## Implementation

### skill-rules.json (Local Tier Only)

```json
{
  "$schema": "./skill-rules.schema.json",
  "version": "1.0.0",
  "tier": "hybrid",
  "local_skills": [
    "tdd_workflow",
    "debugging",
    "build_workflow",
    "rca",
    "commit",
    "v_validation"
  ],
  "cloud_fallback": true,
  "confidence_threshold": 8,
  "tdd_workflow": {
    "description": "Test-Driven Development with PARALLEL subagent delegation",
    "priority": 10,
    "triggers": {
      "keywords": ["test", "jest", "pytest", "tdd", "spec", "mock"],
      "pathPatterns": ["**/*.test.*", "**/tests/**"],
      "intentPatterns": [
        "(?:write|add|create|fix).*(?:test|spec)",
        "(?:test|spec).*(?:for|of|the)"
      ]
    }
  },
  "debugging": {
    "description": "Self-Validating Unified Debugging Suite",
    "priority": 9,
    "triggers": {
      "keywords": ["debug", "investigate", "diagnose", "error", "bug", "crash"],
      "intentPatterns": [
        "(?:debug|investigate).*(?:error|issue|problem)",
        "why.*(?:failing|broken|not working)"
      ]
    }
  },
  "build_workflow": {
    "description": "AI-assisted feature development (Idea to PR)",
    "priority": 8,
    "triggers": {
      "keywords": ["build", "feature", "implement", "develop", "create feature"],
      "intentPatterns": [
        "(?:build|implement|create).*(?:feature|functionality)"
      ]
    }
  }
}
```

### Architecture Flow

```
User Prompt
    ↓
Local Auto-Activator (skill-rules.json + hook)
    ├─→ Match found (≥8) → Suggest local skill
    └─→ No match → Claude Code cloud discovery
```

### Rollback

Delete `.claude/skills/skill-rules.json` and remove hook registration from settings.json.

---

## Quick Ramifications

- **Breaks nothing:** Cloud discovery remains as fallback
- **Edge case:** If local hook conflicts with cloud, may see duplicate suggestions
- **Constraint:** Requires UserPromptSubmit hook registration

---

## Confidence

**Confidence: 75%** — Evidence from user reports (GitHub issues) and community-built solutions confirms gap in Claude Code cloud discovery. Local tier addresses this without full duplication.

**Weakest assumption:** Local hook system integrates cleanly with Claude Code cloud. If wrong: Integration conflicts may require disabling cloud discovery. Mitigation: Test with `CLOUD_SKILL_DISCOVERY_ENABLED=false` env var.

---

## Evidence Sources

- [GitHub Issue #10246: Add Skill Autocomplete to CLI](https://github.com/anthropics/claude-code/issues/10246)
- [GitHub Issue #11266: User skills not auto-discovered](https://github.com/anthropics/claude-code/issues/11266)
- [Reddit: I built an auto-activation system for Claude Code skills](https://www.reddit.com/r/GithubCopilot/comments/1qmnunw/i_built_an_autoactivation_system_for_claude_code/)
- [diet103/claude-code-infrastructure-showcase](https://github.com/diet103/claude-code-infrastructure-showcase)
- [Skills Auto-Activation via Hooks](https://paddo.dev/blog/claude-skills-hooks-solution/)
