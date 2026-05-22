---
name: context7
description: "Docs-as-Code: Fetch fresh, version-specific documentation via Context7 API."
---
# Context7 - Fresh Documentation

**Objective:** Eliminate hallucinations by injecting real-time, version-specific documentation into the context.

## How to Use

1. **Trigger**: `/context7 [query]` or `use context7`
2. **Process**:
   - The agent searches for the library.
   - The agent fetches relevant docs for your query.
   - The agent generates code/answers based on *that* documentation.

## Requirements

- **MCP Server**: Context7 MCP server must be configured in your Claude Code settings
- **API Key**: Configure via MCP server settings (set in Claude Code MCP configuration)
- No environment variables needed - MCP handles authentication

## Workflow Example

**User:** "How do I do auth in Supabase? use context7"

**Agent:**
1.  Call `resolve-library-id` with `libraryName: "Supabase"`, `query: "authentication"` -> Returns `/supabase/supabase-js`
2.  Call `query-docs` with `libraryId: "/supabase/supabase-js"`, `query: "how to authenticate users with examples"`
3.  **Result:** Returns official Supabase Auth documentation with code examples.
4.  **Answer:** Generates code using the verified `supabase.auth.signInWithPassword()` method.

## Best Practices

1. **Be Specific**: Use natural language questions, not keywords
   - Good: "How to implement middleware in Next.js App Router"
   - Bad: "nextjs middleware"

2. **Pin Versions**: When discussing a specific version, include it
   - Format: `/org/library/v1.2.3`
   - Example: `/vercel/next.js/v15.1.8`

3. **Check Cache**: Don't re-fetch if recent docs are in context
   - Context7 docs update infrequently
   - Caching for hours/days is appropriate

4. **Mode Selection**: Choose based on what you need
   | Situation | Mode | Example Query |
   |----------|------|---------------|
   | Need explanation / learning | `full` | "how does Next.js middleware work" |
   | Debugging subtle behavior | `full` | "why is my middleware not being called" |
   | Unfamiliar library first contact | `full` | "how to use LangChain prompts" |
   | Need syntax / API signature | `code_only` | "Next.js middleware function signature" |
   | Implementing familiar pattern | `code_only` | "add JWT validation to Express middleware" |
   | Quick reference check | `code_only` | "React useCallback dependency array" |

   **Default to `code_only`** unless: the query asks "how does X work", involves debugging, or targets a library not yet seen in the session.

   Note: The MCP tool output is markdown with code blocks. Post-filter by keeping only ` ``` ` blocks for token-efficient code-only mode.
