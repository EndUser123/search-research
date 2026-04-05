"""
Example: Using prompt-hook (Claude Code Integration) Standalone

This is the simplest way to get automatic prompt enhancement.
No Python code required - just configuration.
"""

# ============================================================================
# SETUP (One-time configuration)
# ============================================================================

# Step 1: Place the hook package in the right location
# ------------------------------------------------------
# Option A: Local development
# cp -r packages/hook ~/.claude/hooks/_packages/prompt-hook
#
# Option B: From P:/packages (auto-discovered)
# Already there if you're developing from P:/packages/prompting-toolkit/

# Step 2: Enable in Claude Code settings
# ---------------------------------------
# Add to P:/.claude/settings.json:
"""
{
  "env": {
    "PROMPT_ENHANCEMENT_ENABLED": "true",
    "PROMPT_CHOICE_ENABLED": "true",
    "PROMPT_ENHANCEMENT_DEBUG": "false"
  }
}
"""

# Step 3: Restart Claude Code
# ----------------------------
# That's it! The hook is now active.

# ============================================================================
# USAGE (Automatic - No code needed)
# ============================================================================

# Example 1: Simple prompt
# ------------------------
# User types: "fix bug in auth"
# Hook detects: Simple (3 words)
# Action: Pass through without enhancement
# Result: "fix bug in auth" (unchanged)

# Example 2: Moderate prompt
# --------------------------
# User types: "implement user authentication with JWT"
# Hook detects: Moderate (6 words), security domain
# Action: Add lightweight guidance + choice UI
# Result:
"""
**💡 Prompt Enhancement Available**

**Your original:**
implement user authentication with JWT

**Enhanced version:**
implement user authentication with JWT

**Security Context**: Considering security implications including input validation,
output encoding, authentication, authorization, and common vulnerabilities (OWASP Top 10).

**Action Required**
0 - Use enhanced prompt (recommended)
1 - Use your original prompt
"""

# Example 3: Complex prompt
# -------------------------
# User types: "design microservices architecture for e-commerce platform with
#              focus on scalability and fault tolerance"
# Hook detects: Complex (15 words), architecture domain
# Action: Add comprehensive guidance + choice UI
# Result: Similar to above but with more detailed guidance

# ============================================================================
# ADVANCED CONFIGURATION
# ============================================================================

# Environment Variables
# ---------------------
# PROMPT_ENHANCEMENT_ENABLED: "true" | "false"
#   Master enable/disable switch
#
# PROMPT_CHOICE_ENABLED: "true" | "false"
#   Enable/disable the interactive choice UI
#   When false: Always use enhanced prompts
#
# PROMPT_ENHANCEMENT_DEBUG: "true" | "false"
#   Enable debug output to stderr

# Complexity Thresholds
# ---------------------
# Simple: 0-10 words → Pass through
# Moderate: 10-30 words → Guidance + choice
# Complex: 30-60 words → Guidance + choice
# Expert: 60+ words → Guidance + choice

# Domain Detection
# ----------------
# The hook automatically detects these domains:
# - security: "auth", "security", "vulnerability", "OWASP", "injection"
# - testing: "test", "pytest", "unit test", "integration"
# - database: "database", "sql", "query", "migration", "schema"
# - frontend: "ui", "component", "react", "vue", "frontend"
# - general: Everything else

# ============================================================================
# STATE MANAGEMENT
# ============================================================================

# State files are stored in: .claude/state/prompt_choice/
#
# Each session gets: {session_id}.json
#
# Isolation priority:
# 1. session_id from hook input
# 2. terminal_id from hook input
# 3. Environment variables (CLAUDE_SESSION_ID, CLAUDE_TERMINAL_ID)
# 4. PID fallback (least stable)
#
# Auto-cleanup after 5 minutes.

# ============================================================================
# MULTI-TERMINAL SAFETY
# ============================================================================

"""
The hook is designed to work safely across multiple Claude Code terminals:

- Each terminal gets isolated state
- No cross-terminal pollution
- Automatic cleanup of stale state files
- No race conditions or conflicts

You can run Claude Code in multiple terminals safely!
"""

# ============================================================================
# WHEN TO USE HOOK ONLY
# ============================================================================

"""
Use hook alone (without framework) when:

✓ You're using Claude Code interactively
✓ You want automatic prompt improvement
✓ You don't want to write Python code
✓ You need quick, everyday enhancements
✓ You're not building custom AI applications

Consider adding framework when:

✗ You need programmatic control
✗ You want to use specific prompting strategies
✗ You're building AI-powered features
✗ You need meta-prompt optimization (GA/DE)
"""

# ============================================================================
# TROUBLESHOOTING
# ============================================================================

"""
Problem: Hook not running
Solution: Check PROMPT_ENHANCEMENT_ENABLED="true" in settings.json

Problem: No choice UI appearing
Solution: Check PROMPT_CHOICE_ENABLED="true" in settings.json

Problem: Prompts not being enhanced
Solution: Check prompt complexity - simple prompts (0-10 words) pass through

Problem: State not persisting
Solution: Check .claude/state/prompt_choice/ directory exists

Problem: Multiple terminals interfering
Solution: Each terminal should have separate state files (automatic)
"""

# ============================================================================
# CONCLUSION
# ============================================================================

"""
prompt-hook is the simplest way to get automatic prompt enhancement:

1. Place package in ~/.claude/hooks/_packages/
2. Enable in settings.json
3. Restart Claude Code
4. Done! Every prompt is automatically analyzed and enhanced

No Python code required. No API calls. No configuration beyond the basics.

Just better prompts, automatically.
"""

# For more information, see:
# - OLD_PROMPT_ENHANCEMENT_README.md (original documentation)
# - packages/hook/README.md (package-specific docs)
