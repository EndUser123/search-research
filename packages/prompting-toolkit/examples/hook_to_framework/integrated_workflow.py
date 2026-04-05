"""
Example: Integrated Workflow Using Both Packages

This demonstrates how hook (automatic enhancement) and framework (strategy library)
work together to provide end-to-end prompt optimization.
"""

# ============================================================================
# SCENARIO: User wants to implement a websocket server securely
# ============================================================================

# Step 1: User types in Claude Code
# ---------------------------------
# User input: "implement websocket server"
#
# Step 2: hook (automatic) detects and enhances
# ---------------------------------------------
# - Complexity: Complex (3 words)
# - Domain: Security (detected "server", "implement")
# - Enhanced prompt adds:
#   "Security Context: Considering security implications including input validation,
#    output encoding, authentication, authorization, and common vulnerabilities
#    (OWASP Top 10)."
#
# Step 3: User approves enhanced prompt (choice UI)
# -------------------------------------------------
# User selects: "0 - Use enhanced prompt (recommended)"
#
# Step 4: Enhanced prompt sent to Claude
# ---------------------------------------
# Claude receives security-aware prompt and generates implementation
#
# Step 5: framework (optional) can further optimize
# -------------------------------------------------
# If using programmatically, framework can select best strategies:

from prompting_framework import PromptingContext, PromptingOrchestrator

# Create orchestrator
orchestrator = PromptingOrchestrator()

# Define context (matches what hook detected)
context = PromptingContext(
    query="implement websocket server with security considerations",
    domain="security",
    complexity="complex",
    user_intent="implement_feature"
)

# Auto-select best techniques for this context
techniques = await orchestrator.select_applicable_techniques(context)

print("Selected techniques:")
for technique in techniques:
    print(f"  - {technique.name}: {technique.description}")

# Output:
# Selected techniques:
#   - Chain-of-Verification: Multi-step verification for critical reasoning
#   - Constitutional Compliance: Safety constraints for security contexts
#   - Self-Refine: Iterative improvement for implementation quality

# ============================================================================
# VALUE PROPOSITION
# ============================================================================

"""
Why use both packages together?

1. hook (UX layer):
   - No code required - runs automatically
   - Improves user prompts before they reach Claude
   - Interactive choice gives user control
   - Perfect for day-to-day Claude Code usage

2. framework (Library layer):
   - Programmatic access to 23+ strategies
   - Fine-grained control over technique selection
   - Optimization algorithms (GA/DE) for meta-prompts
   - Perfect for building AI applications

3. Combined:
   - hook catches and improves everyday prompts
   - framework provides advanced strategies for complex use cases
   - Both understand security, complexity, domain in the same way
   - Seamless upgrade path from automatic to manual control
"""

# ============================================================================
# PRACTICAL EXAMPLE: Secure API Development
# ============================================================================

async def develop_secure_api():
    """
    Complete workflow from user input to optimized output
    """
    # 1. User types (in Claude Code):
    #    "create rest api for user management"

    # 2. hook automatically enhances to:
    #    "create rest api for user management
    #
    #     Security Context: Considering security implications including
    #     input validation, output encoding, authentication, authorization,
    #     and common vulnerabilities (OWASP Top 10).
    #
    #     Database Context: Ensure proper parameterized queries, avoid
    #     SQL injection, handle transactions correctly."

    # 3. User approves enhanced prompt

    # 4. If using framework for additional optimization:
    context = PromptingContext(
        query="create rest api for user management with security",
        domain="security",
        complexity="complex",
        user_intent="implement_feature"
    )

    orchestrator = PromptingOrchestrator()
    techniques = await orchestrator.select_applicable_techniques(context)

    # 5. Execute with selected techniques
    result = await orchestrator.execute_techniques(
        query=context.query,
        techniques=techniques
    )

    return result

# ============================================================================
# WHEN TO USE EACH
# ============================================================================

"""
Use hook alone when:
  - You're using Claude Code interactively
  - You want automatic prompt improvement
  - You don't want to write code
  - You need quick enhancements

Use framework alone when:
  - You're building a Python application
  - You need programmatic control
  - You want to use specific techniques
  - You're optimizing meta-prompts

Use both together when:
  - You want automatic enhancement + manual control
  - You're developing AI-powered features
  - You need both UX and library capabilities
  - You want the full prompting ecosystem
"""

# ============================================================================
# CONFIGURATION
# ============================================================================

# Enable hook in P:/.claude/settings.json:
"""
{
  "env": {
    "PROMPT_ENHANCEMENT_ENABLED": "true",
    "PROMPT_CHOICE_ENABLED": "true"
  }
}
"""

# Install framework:
# pip install prompting-framework

# ============================================================================
# CONCLUSION
# ============================================================================

"""
The monorepo structure provides:

1. Unified ecosystem - two packages that understand each other
2. Flexible usage - use one or both as needed
3. Shared standards - testing, documentation, code quality
4. Clear separation - UX vs library concerns
5. Easy migration - start with hook, add framework when needed

This is full-stack prompt engineering: from user experience to
advanced algorithms, all in one well-organized monorepo.
"""
