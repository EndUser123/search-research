---
source_id: "a3beaf53-0eea-4ad5-b2f1-b0bca52b1723"
title: "[BUG] Per-turn smoosh pipeline folds dynamic <system-reminder> text into tool_result.content, breaking prompt cache · Issue #49585 · anthropics/claude-code - GitHub"
notebook_id: 4017aa6e-35fb-426d-bc53-34620bec405e
url: https://github.com/anthropics/claude-code/issues/49585
type: 5
exported: 2026-08-08
---

# [BUG] Per-turn smoosh pipeline folds dynamic <system-reminder> text into tool_result.content, breaking prompt cache · Issue #49585 · anthropics/claude-code - GitHub
[BUG] Per-turn smoosh pipeline folds dynamic 
 text into tool_result.content, breaking prompt cache · Issue #49585 · anthropics/claude-code
Skip to content
https://github.com/anthropics/claude-code/issues/49585#start-of-content
Navigation Menu
Toggle navigation 
https://github.com/
Sign in
https://github.com/login?return_to=https%3A%2F%2Fgithub.com%2Fanthropics%2Fclaude-code%2Fissues%2F49585
Appearance settings
Platform
AI CODE CREATION
GitHub Copilot Write better code with AI
https://github.com/features/copilot
GitHub Copilot app Direct agents from issue to merge
https://github.com/features/ai/github-app
MCP Registry New Integrate external tools
https://github.com/mcp
DEVELOPER WORKFLOWS
Actions Automate any workflow
https://github.com/features/actions
Codespaces Instant dev environments
https://github.com/features/codespaces
Issues Plan and track work
https://github.com/features/issues
Code Review Manage code changes
https://github.com/features/code-review
APPLICATION SECURITY
GitHub Advanced Security Find and fix vulnerabilities
https://github.com/security/advanced-security
Code security Secure your code as you build
https://github.com/security/advanced-security/code-security
Secret protection Stop leaks before they start
https://github.com/security/advanced-security/secret-protection
EXPLORE
Why GitHub
https://github.com/why-github
Documentation
https://docs.github.com/
Blog
https://github.blog/
Changelog
https://github.blog/changelog
Marketplace
https://github.com/marketplace
 
View all features
https://github.com/features
Solutions
BY COMPANY SIZE
Enterprises
https://github.com/enterprise
Small and medium teams
https://github.com/team
Startups
https://github.com/enterprise/startups
Nonprofits
https://github.com/solutions/industry/nonprofits
BY USE CASE
App Modernization
https://github.com/solutions/use-case/app-modernization
DevSecOps
https://github.com/solutions/use-case/devsecops
DevOps
https://github.com/solutions/use-case/devops
CI/CD
https://github.com/solutions/use-case/ci-cd
View all use cases
https://github.com/solutions/use-case
BY INDUSTRY
Healthcare
https://github.com/solutions/industry/healthcare
Financial services
https://github.com/solutions/industry/financial-services
Manufacturing
https://github.com/solutions/industry/manufacturing
Government
https://github.com/solutions/industry/government
View all industries
https://github.com/solutions/industry
 
View all solutions
https://github.com/solutions
Resources
EXPLORE BY TOPIC
AI
https://github.com/resources/articles?topic=ai
Software Development
https://github.com/resources/articles?topic=software-development
DevOps
https://github.com/resources/articles?topic=devops
Security
https://github.com/resources/articles?topic=security
View all topics
https://github.com/resources/articles
EXPLORE BY TYPE
Customer stories
https://github.com/customer-stories
Events & webinars
https://github.com/resources/events
Ebooks & reports
https://github.com/resources/whitepapers
Business insights
https://github.com/solutions/executive-insights
GitHub Skills
https://skills.github.com/
SUPPORT & SERVICES
Documentation
https://docs.github.com/
Customer support
https://support.github.com/
Community forum
https://github.com/orgs/community/discussions
Trust center
https://github.com/trust-center
Partners
https://github.com/partners
 
View all resources
https://github.com/resources
Open Source
COMMUNITY
GitHub Sponsors Fund open source developers
https://github.com/sponsors
PROGRAMS
Security Lab
https://securitylab.github.com/
Maintainer Community
https://maintainers.github.com/
Accelerator
https://github.com/accelerator
GitHub Stars
https://stars.github.com/
Archive Program
https://archiveprogram.github.com/
REPOSITORIES
Topics
https://github.com/topics
Trending
https://github.com/trending
Collections
https://github.com/collections
Enterprise
ENTERPRISE SOLUTIONS
Enterprise platform AI-powered developer platform
https://github.com/enterprise
AVAILABLE ADD-ONS
GitHub Advanced Security Enterprise-grade security features
https://github.com/security/advanced-security
Copilot for Business Enterprise-grade AI features
https://github.com/features/copilot/copilot-business
Premium Support Enterprise-grade 24/7 support
https://github.com/premium-support
Pricing
https://github.com/pricing
Search or jump to...
Search code, repositories, users, issues, pull requests...
Search
Clear
Search syntax tips
https://docs.github.com/search-github/github-code-search/understanding-github-code-search-syntax
Provide feedback
We read every piece of feedback, and take your input very seriously.
 
[-]
Include my email address so I can be contacted
Cancel Submit feedback
Saved searches
Use saved searches to filter your results more quickly
Name
Query
To see all available qualifiers, see our 
documentation
https://docs.github.com/search-github/github-code-search/understanding-github-code-search-syntax
.
Cancel Create saved search
Sign in
https://github.com/login?return_to=https%3A%2F%2Fgithub.com%2Fanthropics%2Fclaude-code%2Fissues%2F49585
Sign up
https://github.com/signup?ref_cta=Sign+up&ref_loc=header+logged+out&ref_page=%2F%3Cuser-name%3E%2F%3Crepo-name%3E%2Fvoltron%2Fissues_fragments%2Fissue_layout&source=header-repo&source_repo=anthropics%2Fclaude-code
Appearance settings
Resetting focus
You signed in with another tab or window. 
Reload
https://github.com/anthropics/claude-code/issues/49585
 to refresh your session. You signed out in another tab or window. 
Reload
https://github.com/anthropics/claude-code/issues/49585
 to refresh your session. You switched accounts on another tab or window. 
Reload
https://github.com/anthropics/claude-code/issues/49585
 to refresh your session. Dismiss alert
Uh oh!
There was an error while loading. 
Please reload this page
https://github.com/anthropics/claude-code/issues/49585
.
anthropics
https://github.com/anthropics
 / 
claude-code
 Public
Notifications
https://github.com/login?return_to=%2Fanthropics%2Fclaude-code
 You must be signed in to change notification settings
Fork 21.9k
https://github.com/login?return_to=%2Fanthropics%2Fclaude-code
Star 136k
https://github.com/login?return_to=%2Fanthropics%2Fclaude-code
Code
https://github.com/anthropics/claude-code
Issues 5k+
https://github.com/anthropics/claude-code/issues
Pull requests 643
https://github.com/anthropics/claude-code/pulls
Actions
https://github.com/anthropics/claude-code/actions
Security and quality 30
https://github.com/anthropics/claude-code/security
Insights
https://github.com/anthropics/claude-code/pulse
Additional navigation options
Code
https://github.com/anthropics/claude-code
Issues
https://github.com/anthropics/claude-code/issues
Pull requests
https://github.com/anthropics/claude-code/pulls
Actions
https://github.com/anthropics/claude-code/actions
Security and quality
https://github.com/anthropics/claude-code/security
Insights
https://github.com/anthropics/claude-code/pulse
[BUG] Per-turn smoosh pipeline folds dynamic 
 text into tool_result.content, breaking prompt cache #49585
New issue
https://github.com/login?return_to=https://github.com/anthropics/claude-code/issues/49585
Copy link
New issue
https://github.com/login?return_to=https://github.com/anthropics/claude-code/issues/49585
Copy link
Closed as not planned
Closed as not planned
[BUG] Per-turn smoosh pipeline folds dynamic  text into tool_result.content, breaking prompt cache
https://github.com/anthropics/claude-code/issues/49585#top
 #49585
Copy link
Labels
area:core
https://github.com/anthropics/claude-code/issues?q=state%3Aopen%20label%3A%22area%3Acore%22
 
area:cost
https://github.com/anthropics/claude-code/issues?q=state%3Aopen%20label%3A%22area%3Acost%22
 
bug Something isn't working
https://github.com/anthropics/claude-code/issues?q=state%3Aopen%20label%3A%22bug%22
 Something isn't working 
has repro Has detailed reproduction steps
https://github.com/anthropics/claude-code/issues?q=state%3Aopen%20label%3A%22has%20repro%22
 Has detailed reproduction steps 
stale Issue is inactive
https://github.com/anthropics/claude-code/issues?q=state%3Aopen%20label%3A%22stale%22
 Issue is inactive
Description
deafsquad
https://github.com/deafsquad
opened 
on Apr 16
https://github.com/anthropics/claude-code/issues/49585#issue-4279012241
Issue body actions
Summary
normalizeMessagesForAPI
 runs a smoosh pass every turn that folds 
<system-reminder>
 -prefixed text blocks into the preceding 
tool_result.content
 string. Because many of CC's own built-in reminders carry dynamic values ( 
token_usage
 , 
output_token_usage
 , 
budget_usd
 , 
deferred_tools_delta
 , 
todo_reminder
 , 
mcp_instructions_delta
 , etc.), the smoosh produces different byte output turn-over-turn. The resulting byte drift in historical user messages breaks the prompt cache prefix, causing 
cache_creation
 to spike by tens or hundreds of thousands of tokens on turns that should have been clean cache hits.
No user-side hooks required
 — CC-internal reminders alone are sufficient to trigger this. We ported the relevant functions and reproduced the byte divergence end-to-end (simulation below).
This is distinct from the resume/scatter bugs in 
#40524
https://github.com/anthropics/claude-code/issues/40524
 (closed, partial fix in 2.1.90), 
#44045
https://github.com/anthropics/claude-code/issues/44045
 (resume skill_listing scatter), 
#48644
https://github.com/anthropics/claude-code/issues/48644
 ( 
am7
 reminder breakpoint movement), 
#43657
https://github.com/anthropics/claude-code/issues/43657
 (resume cache invalidation), 
#49038
https://github.com/anthropics/claude-code/issues/49038
 (non-deterministic tool ordering), and our own 
#48734
https://github.com/anthropics/claude-code/issues/48734
 / 
#38542
https://github.com/anthropics/claude-code/issues/38542
 — all of which describe adjacent but different mechanisms. The smoosh bug fires 
per turn on non-resume paths
 and has not been reported specifically.
Affected code
src/utils/messages.ts
 (function names verified against the leaked TS source):
Function
Line
Role
normalizeMessagesForAPI
~1989
Entry point, runs the full pipeline every outgoing request
smooshSystemReminderSiblings
~1835
Walks each user message, extracts 
<system-reminder>
 -prefixed text blocks, folds them into the 
last
 
tool_result
 via 
smooshIntoToolResult
smooshIntoToolResult
~2534
The actual fold: joins 
tool_result.content
 + incoming text blocks with 
\n\n
 separators
mergeAdjacentUserMessages
called before smoosh
Combines consecutive user messages, creating the adjacencies smoosh then folds
Feature gate 
tengu_chair_sermon
~2274, ~2335
Statsig-cached ( 
_CACHED_MAY_BE_STALE
 ) gate; when ON, runs the merge+smoosh pipeline
The smoosh's own comment claims "Idempotent. Pure function of shape." That claim holds for a single fixed input — but the 
input
 is not stable turn-over-turn when:
Reminders carry dynamic values ( 
token_usage
 , etc.)
New attachments are appended between turns ( 
deferred_tools_delta
 , 
todo_reminder
 after N turns, 
mcp_instructions_delta
 )
The Statsig cache refreshes mid-session and toggles the gate
mergeAdjacentUserMessages
 creates different adjacencies as history grows
Any of the above makes the smoosh output differ from what was previously cached on the server, breaking the prefix match.
Observed fold is distributed by 
toolUseID
 , not concentrated on last tool_result
Our captured miss 
#1
https://github.com/anthropics/claude-code/pull/1
 showed 
msg[30]
 going from 6 blocks to 3, with each text block folded into 
a different
 
tool_result
 (+107, +107, +519 chars matching each reminder's size). A port-faithful simulation of 
smooshSystemReminderSiblings
 alone (which folds all text into the LAST tool_result) does NOT reproduce this shape — the mechanism must involve an earlier pass.
Tracing through 
normalizeMessagesForAPI
 (messages.ts:1989):
reorderAttachmentsForAPI
 (messages.ts:1481) — bubbles each hook-attachment user-message up in the list until it lands right after its matching 
tool_result
 . Unconditional (no gate).
mergeAdjacentUserMessages
 (messages.ts:2451) — walks the resulting list and merges consecutive user messages pairwise via 
mergeUserMessagesAndToolResults
 (messages.ts:2372).
That merge delegates to 
mergeUserContentBlocks
 (messages.ts:2600), which when 
tengu_chair_sermon
 is ON takes the universal-smoosh branch (messages.ts:2628-2643) and folds each incoming reminder into the 
currently-last
 
tool_result
 of the accumulating message.
Because the pairwise merges happen in order — and each hook attachment is positioned right after its own tool_result thanks to step 1 — each reminder lands on ITS specific tool_result rather than all piling onto the final one.
hoistToolResults
 (messages.ts:2470) then re-sorts all tool_results to the front of the content array.
Finally 
smooshSystemReminderSiblings
 (messages.ts:1835) mops up any remaining 
<system-reminder>
 -prefixed siblings that escaped the merge-time fold.
The distributed-fold pattern we observed is an emergent property of the pairwise-merge order combined with the attachment-position reorder — not a single dedicated function. 
tengu_chair_sermon
 controls the universal-smoosh branch; when OFF, 
mergeUserContentBlocks
 takes a narrower legacy path that only smooshes when the tool_result's content is a plain string and all incoming siblings are text. That narrower path still covers the common hook-reminder-after-Bash-result case but misses multi-block cases. Net effect: all users with dynamic hook output paired to tool_results are affected; the gate controls the 
aggressiveness
 of the fold, not its presence.
Reproduction (minimal, CC-internal only)
Ported 
smooshSystemReminderSiblings
 + 
smooshIntoToolResult
 to Python (logic verbatim from the leaked TS), fed two adjacent turns with 
only
 built-in CC reminders — no user hooks:
# Input shape (both turns):
user_msg(
    tool_result("toolu_01abc", "bash output: ls -la\ntotal 0\n"),
    token_usage(used, 200000),           # dynamic
    output_token_usage(turn_out, session_out),  # dynamic
    budget_usd(used_usd, 100.00),         # dynamic
)

# Turn N:   used=150_000, turn_out=500, session_out=3_200, used_usd=4.50
# Turn N+1: used=151_200, turn_out=580, session_out=3_780, used_usd=4.82

After 
smooshSystemReminderSiblings
 :
Turn N:   tool_result.content = "bash output: ls -la\ntotal 0\n\n<system-reminder>\nToken usage: 150000/200000; 50000 remaining\n</system-reminder>\n\n..."
Turn N+1: tool_result.content = "bash output: ls -la\ntotal 0\n\n<system-reminder>\nToken usage: 151200/200000; 48800 remaining\n</system-reminder>\n\n..."
                                                                                          ^
                                                                              First byte divergence at offset 161

The smoosh absorbed the dynamic token-usage numbers into what was previously a stable 
tool_result.content
 string. The cache entry for Turn N's tool_result.content no longer matches Turn N+1's version → cache-prefix break at that position → all bytes after the break point must re-cache on this turn.
Full 130-line port is runnable standalone: no CC install needed.
Real-session impact (one user, measured)
Methodology: log 
ctx_cache_w
 / 
ctx_cache_r
 from every statusline poll (14,797 samples over multiple weeks on Opus 4.7 1M-context). Bucket by cache-read signature:
Cause
Turns
cache_creation
Fusion-attributable
 ( 
cr ≈ 16k-19k
 , tools-only cached)
~204
~99M
Resume / TTL / server cold-start ( 
cr = 0
 )
53
32M
Normal hit-bound operation
14,481
39M
Partial/other
42
7.6M
The 204 fusion-attributable turns all show the fingerprint 
cache_read = tools-prefix-only
 (no message prefix matched) + 
cache_creation = full message prefix re-built
 . Their 
cr
 values cluster tightly at ~19,282 (the tools-only token count) and ~16,700 (smaller tools set when some MCP servers or skills were toggled). No fusion-signature cr values below 10k — those would indicate different causes.
~99M cache_creation tokens on fusion-attributable turns — ~56% of this session's total cache_creation spend went to re-caching content that was already present in prior turns.
 Token-cost at Opus 4.7 1M-context ephemeral rates works out to somewhere in the low-four-figure USD range for this one user across the logged window; I'm leaving the exact dollar figure to Anthropic's own pricing math since the per-tier rates shift by TTL and context band.
Consistent with the pattern of "abnormal quota drain" reports
The signature — a trivial user turn triggering 
cache_creation
 that bills as though the full message history were new — matches the shape of reports like 
#42052
https://github.com/anthropics/claude-code/issues/42052
, 
#43274
https://github.com/anthropics/claude-code/issues/43274
, 
#45756
https://github.com/anthropics/claude-code/issues/45756
, 
#41930
https://github.com/anthropics/claude-code/issues/41930
, 
#41617
https://github.com/anthropics/claude-code/issues/41617
, 
#16157
https://github.com/anthropics/claude-code/issues/16157
. Users without power hooks still hit this via CC's own dynamic reminders ( 
token_usage
 / 
output_token_usage
 every turn; 
todo_reminder
 after N turns; 
deferred_tools_delta
 / 
mcp_instructions_delta
 on MCP flaps). Worth investigating as a contributing factor to those reports — the mechanism would produce exactly the "I sent 5 prompts and my weekly quota is gone" symptom if any subset of turns hits a smoosh-drift path.
I'm not claiming this is the sole cause of those drain reports — just that the mechanism here is one they'd reasonably produce.
Request
The smoosh is clearly intended (comment at line 2328 in messages.ts explains the 
tengu_chair_sermon
 gate's purpose). But for the smoosh to be safe under CC's current architecture, it needs at least one of:
Idempotency over persisted transcripts
: if the smoosh output is going to be re-computed from JSONL every turn, the inputs it consumes must be byte-stable between turns. Dynamic reminders ( 
token_usage
 , etc.) should be injected AFTER the smoosh pass, or excluded from it.
Store smooshed transcripts
: persist the post-smoosh message to JSONL, not the pre-smoosh attachment list. Then re-runs produce identical output.
Gate the smoosh off historical messages
: only smoosh the most-recent user message (the one being constructed), never re-smoosh history.
Opt-out env var
: 
CLAUDE_CODE_DISABLE_TOOLRESULT_SMOOSH=1
 or similar for quota-sensitive power users — similar to the 
CLAUDE_CODE_ATTRIBUTION_HEADER=false
 workaround added for the 
[BUG] Conversation history invalidated on subsequent turns #40524
https://github.com/anthropics/claude-code/issues/40524
 family.
The simulation file and our captured miss-pair bodies (three trios with full 
/v1/messages
 request bodies showing the before/after fusion) are available on request for internal repro.
Cross-references
Closed / partially-fixed family: 
[BUG] Conversation history invalidated on subsequent turns #40524
https://github.com/anthropics/claude-code/issues/40524
 (sentinel + scatter, 2.1.90/91), community RE by 
@jmarianski
https://github.com/jmarianski
 / 
@whiletrue0x
https://github.com/whiletrue0x
 / 
@VictorSun92
https://github.com/VictorSun92
 / 
@FlorianBruniaux
https://github.com/FlorianBruniaux
 / 
@ArkNill
https://github.com/ArkNill
Related open bugs in same class: 
[BUG] Historical user-message content drift invalidates prompt cache prefix (trailing \n on ) #48734
https://github.com/anthropics/claude-code/issues/48734
 
Bug: cache_control TTL ordering error when hooks/MCP inject additionalContext into long conversations #38542
https://github.com/anthropics/claude-code/issues/38542
 
[BUG] Resume/continue cache invalidation #43657
https://github.com/anthropics/claude-code/issues/43657
 
[BUG] Prompt cache partial miss on every --resume turn — skill_listing block missing from messages[0] #44045
https://github.com/anthropics/claude-code/issues/44045
 
[BUG] Hidden isMeta system-reminder causes 200k+ cache_creation burst mid-session (Opus 4.6) #48644
https://github.com/anthropics/claude-code/issues/48644
 
Prompt cache miss on resume: Agent tool description enumerates sub-agents in non-deterministic order #49038
https://github.com/anthropics/claude-code/issues/49038
 
Resume of long sessions loads disproportionate tokens from opaque thinking signatures #42260
https://github.com/anthropics/claude-code/issues/42260
 
Bug: --resume loads 0% context on v2.1.91 — three regressions in session loading pipeline (source code verified) #43044
https://github.com/anthropics/claude-code/issues/43044
 
[BUG] Max 20x plan: 100% usage after 2 hours of light work (5 commits, no agents) #42052
https://github.com/anthropics/claude-code/issues/42052
Reporter-side mitigation that would help: same "post-cache-fix" style env var lever used for 
[BUG] Conversation history invalidated on subsequent turns #40524
https://github.com/anthropics/claude-code/issues/40524
 bug 3
Leaving our earlier 
#48734
https://github.com/anthropics/claude-code/issues/48734
 open as a separate data point covering the same mechanism from a different angle — happy for maintainers to consolidate if they prefer.
Activity
Next
https://github.com/anthropics/claude-code/issues/49585?timeline_page=1
github-actions
https://github.com/apps/github-actions
added
bug Something isn't working
https://github.com/anthropics/claude-code/issues?q=state%3Aopen%20label%3A%22bug%22
 Something isn't working
has repro Has detailed reproduction steps
https://github.com/anthropics/claude-code/issues?q=state%3Aopen%20label%3A%22has%20repro%22
 Has detailed reproduction steps
area:cost
https://github.com/anthropics/claude-code/issues?q=state%3Aopen%20label%3A%22area%3Acost%22
area:core
https://github.com/anthropics/claude-code/issues?q=state%3Aopen%20label%3A%22area%3Acore%22
on Apr 16
https://github.com/anthropics/claude-code/issues/49585#event-24586586208
github-actions commented on Apr 16
github-actions
https://github.com/apps/github-actions
 bot
on Apr 16
https://github.com/anthropics/claude-code/issues/49585#issuecomment-4264015671
 – with 
GitHub Actions
https://help.github.com/en/actions
More actions
Found 3 possible duplicate issues:
[BUG] Historical user-message content drift invalidates prompt cache prefix (trailing \n on ) #48734
https://github.com/anthropics/claude-code/issues/48734
[BUG] Hidden isMeta system-reminder causes 200k+ cache_creation burst mid-session (Opus 4.6) #48644
https://github.com/anthropics/claude-code/issues/48644
[BUG] Prompt cache partial miss on every --resume turn — skill_listing block missing from messages[0] #44045
https://github.com/anthropics/claude-code/issues/44045
This issue will be automatically closed as a duplicate in 3 days.
If your issue is a duplicate, please close it and 👍 the existing issue instead
To prevent auto-closure, add a comment or 👎 this comment
🤖 Generated with 
Claude Code
https://claude.ai/code
👎 React with 👎 3 t-np, cnighswonger and neoblackxt
deafsquad
https://github.com/deafsquad
mentioned this 
on Apr 16
https://github.com/anthropics/claude-code/issues/49585#event-6068209097
[BUG] Resume/continue cache invalidation #43657
https://github.com/anthropics/claude-code/issues/43657
deafsquad commented on Apr 16
deafsquad
https://github.com/deafsquad
on Apr 16
https://github.com/anthropics/claude-code/issues/49585#issuecomment-4264233537
Author
More actions
Not a duplicate of the three flagged candidates — they're siblings in the "message-pipeline byte drift breaks prompt cache" family, but each names a different concrete code path. Differences below so the dup-detector can re-check:
Issue
Trigger
Code path cited
Manifestation
#49585 (this)
Dynamic 
<system-reminder>
 -prefixed text (CC-internal reminders with per-turn-variable values) being folded into 
tool_result.content
 strings by the smoosh pass
smooshSystemReminderSiblings
 (messages.ts:1835) → 
smooshIntoToolResult
 (messages.ts:2534), gated on 
tengu_chair_sermon
 — runs EVERY turn
Mid-history byte drift at the tool_result that absorbed the dynamic reminder
#48734
https://github.com/anthropics/claude-code/issues/48734
 (mine, earlier)
Trailing 
\n
 flip on 
</system-reminder>\n
 in persisted history
Not traced to a specific function; documented as observational byte drift
Mid-history byte drift at a 
system-reminder
 boundary
#48644
https://github.com/anthropics/claude-code/issues/48644
A hardcoded 
am7
 reminder string ( 
"Respond with just the action..."
 ) pushed onto the messages array by a pre-request hook, only on Opus 4.6 with 
loud_sugary_rock
 Statsig gate
Injection site in the pre-API hook loop (not in the smoosh); moves the cache_control breakpoint position
200-282k cache_creation bursts on trivial prompts, Opus 4.6 only
#44045
https://github.com/anthropics/claude-code/issues/44045
Resume-time regeneration of 
skill_listing
 attachment position
Attachment scatter at 
messages[0]
 vs 
messages[2]
 , tied to the resume codepath
Whole-prefix miss on every turn of a resumed session
Specifically different from each:
[BUG] Historical user-message content drift invalidates prompt cache prefix (trailing \n on ) #48734
: Same author (me), but that one is about trailing-newline drift on a persisted 
</system-reminder>
 — our 
ws_strip
 mitigation in the vendored preload catches it. This issue ( 
[BUG] Per-turn smoosh pipeline folds dynamic  text into tool_result.content, breaking prompt cache #49585
https://github.com/anthropics/claude-code/issues/49585
) is about a DIFFERENT drift: dynamic content changes between turns flowing through the smoosh transform. 
ws_strip
 does not catch it because the bytes that differ are inside the dynamic value (e.g. 
Token usage: 150k/200k
 → 
151k/200k
 ), not trailing whitespace. Distinct mechanism, distinct fix.
[BUG] Hidden isMeta system-reminder causes 200k+ cache_creation burst mid-session (Opus 4.6) #48644
: That one is about a SINGLE reminder string ( 
am7
 ) with a KNOWN hardcoded constant being pushed mid-stream under a specific gate. The cache break there is from breakpoint POSITION movement, not content fold. Different code path (pre-API hook loop vs. the smoosh), different model scope (Opus 4.6 only vs. all models). 
[BUG] Per-turn smoosh pipeline folds dynamic  text into tool_result.content, breaking prompt cache #49585
https://github.com/anthropics/claude-code/issues/49585
 fires on any model whenever dynamic reminders land in history with a tool_result adjacent.
[BUG] Prompt cache partial miss on every --resume turn — skill_listing block missing from messages[0] #44045
: That one is strictly resume-bound — attachment scatter happens because 
processSessionStartHooks('resume')
 injects a new attachment that reorders 
messages[0]
 . 
[BUG] Per-turn smoosh pipeline folds dynamic  text into tool_result.content, breaking prompt cache #49585
https://github.com/anthropics/claude-code/issues/49585
 fires per-turn on non-resume calls. I just posted a separate comment on 
[BUG] Resume/continue cache invalidation #43657
https://github.com/anthropics/claude-code/issues/43657
 (the parent thread for the resume bug) with the specific function-level diagnosis — that's the right home for resume-scatter discussion; this issue is for the per-turn smoosh-fusion that fires without any resume involvement.
The three are siblings in that they all boil down to "CC's request assembly isn't byte-idempotent over the stored transcript," but each has a different code path, different trigger, and would need a different fix. Consolidation would cost the granular attribution each separately contributes.
Simulation ported from the leaked TS source with byte-exact reproduction of the fold is already in this issue body — happy to run it against any specific scenario if the triage team wants to test.
cnighswonger
https://github.com/cnighswonger
added a commit that references this issue 
on Apr 16
https://github.com/anthropics/claude-code/issues/49585#event-24588368723
v2.0.0-beta.2: normalize smooshed dynamic system-reminders in tool_re…
https://github.com/cnighswonger/claude-code-cache-fix/commit/81ff47c40b9e6d69f117c294526051f9d18a3bdb
...
81ff47c
https://github.com/cnighswonger/claude-code-cache-fix/commit/81ff47c40b9e6d69f117c294526051f9d18a3bdb
deafsquad
https://github.com/deafsquad
added a commit that references this issue 
on Apr 16
https://github.com/anthropics/claude-code/issues/49585#event-24589151326
Add smoosh_split extension — universal un-smoosh, complements smoosh_…
https://github.com/deafsquad/claude-code-cache-fix/commit/92f2a8066e1a8b557c2057ef87d483d5ac3bfb19
...
92f2a80
https://github.com/deafsquad/claude-code-cache-fix/commit/92f2a8066e1a8b557c2057ef87d483d5ac3bfb19
deafsquad
https://github.com/deafsquad
mentioned this 
on Apr 16
https://github.com/anthropics/claude-code/issues/49585#event-6068967198
Add smoosh_split — universal un-smoosh complementing smoosh_normalize (#49585) cnighswonger/claude-code-cache-fix#26
https://github.com/cnighswonger/claude-code-cache-fix/pull/26
deafsquad
https://github.com/deafsquad
added a commit that references this issue 
on Apr 16
https://github.com/anthropics/claude-code/issues/49585#event-24589390119
Add smoosh_split extension — universal un-smoosh, complements smoosh_…
https://github.com/deafsquad/claude-code-cache-fix/commit/67a9e41c624fe19cad9333e9d6ea994ea5412615
...
67a9e41
https://github.com/deafsquad/claude-code-cache-fix/commit/67a9e41c624fe19cad9333e9d6ea994ea5412615
cnighswonger commented on Apr 16
cnighswonger
https://github.com/cnighswonger
on Apr 16
https://github.com/anthropics/claude-code/issues/49585#issuecomment-4264674784
More actions
We merged your smoosh_split PR (
#26
https://github.com/anthropics/claude-code/issues/26
) and published as v2.0.0-beta.4:
npm install -g claude-code-cache-fix@beta

beta.4 includes both smoosh_normalize (our pattern-based fix for 4 known counters) and your smoosh_split (universal un-smoosh). They compose: normalize runs first, split peels any remainder.
We couldn't trigger either fix locally — our account doesn't appear to have tengu_chair_sermon active. Your captured miss bodies were the validation. If you're able to run a session with the beta and CACHE_FIX_DEBUG=1, we'd like to confirm the split fires in production and the cache hit rate improves.
Clarification on methodology: our interceptor was built from reviewing the leaked TypeScript source (src/utils/messages.ts, sessionStart.ts), not from binary reverse engineering. Same functions, same conclusions — just different entry points.
deafsquad commented on Apr 16
deafsquad
https://github.com/deafsquad
on Apr 16
https://github.com/anthropics/claude-code/issues/49585#issuecomment-4264958767
Author
More actions
Confirmed on both counts. Running with v2.0.0-beta.4 (via our vendored fork) across a long-running session:
smoosh_split fires in production:
 
applied=208, skipped=23
 across ~250 requests. 
smoosh_normalize.applied=0
 — matches the complementary design: our hook injections ( 
thinking-enrichment
 , 
action-tracker
 , 
classify-user-intent
 ) don't match the 4 enumerated patterns, so normalize skips them and split peels them.
Cache hit rate improvement
 (first-request 
cw
 on 
--continue
 , same conversation, measured across restarts as we iteratively added mitigations):
Restart
First-request cw
Change
Baseline (no extensions)
940,251
—
+ smoosh_split only
~370K
−61%
+ cwd_normalize, git_status strip
154,799
−84%
+ session_start_normalize, deferred_tools_restore
168,127
(noise — different session state)
+ reminder_strip, cache_control_normalize, continue_trailer_strip
1,704
−99.8%
Subsequent in-session requests hold at 99%+ hit rate. The 940K → 1.7K collapse is the compound effect of the full stack; smoosh_split is necessary but not sufficient.
On methodology — understood and fair, leaked TS source vs. binary RE converge on the same entry points. I've been doing the same (OTEL bodies + the leaked source at 
yasasbanukaofficial/claude-code
 for function names).
Related — we've built 
5 additional extensions
 since the smoosh_split PR, each targeting a distinct cache-miss root cause we observed empirically:
session_start_normalize
 — 
SessionStart:resume
 → 
:startup
 rewrite ( 
[BUG] Resume/continue cache invalidation #43657
https://github.com/anthropics/claude-code/issues/43657
)
deferred_tools_restore
 — snapshots msg[0] deferred-tools block to survive MCP reconnect race
reminder_strip
 — drops Token usage / USD budget / Output tokens / TodoWrite / turn-counter bookkeeping
cache_control_normalize
 — pins the 
cache_control
 marker at a canonical position
continue_trailer_strip
 — removes the 
"Continue from where you left off."
 text block on 
--continue
Each is ~50–150 lines with ≥11 tests passing, idempotent, and gated. Happy to open PRs against your fork if you're interested — let me know preferred shape (single bundle vs. one-per-extension vs. proposal-issue-first).
junaidtitan commented on Apr 17
junaidtitan
https://github.com/junaidtitan
on Apr 17
https://github.com/anthropics/claude-code/issues/49585#issuecomment-4266330006
More actions
This is an excellent analysis — the smoosh folding dynamic reminder values into previously-stable tool_result content is a subtle but expensive cache-busting mechanism. The 99M cache_creation tokens on fusion-attributable turns alone is staggering.
cozempic
https://github.com/Ruya-AI/cozempic
 can partially mitigate the downstream effects, though it obviously can't fix the smoosh pipeline itself:
tool-output-trim
 reduces the tool_result content that gets folded with system-reminder text, so the byte delta from dynamic values affects a smaller payload
system-reminder-dedup
 deduplicates repeated system-reminder tags in the session, reducing the number of dynamic blocks that get smooshed in
General pruning keeps the session prefix shorter and more stable, which improves cache hit rates on the portion that cozempic controls
pip install cozempic
cozempic treat current -rx standard --execute

To be clear — the real fix needs to happen in CC's 
normalizeMessagesForAPI
 (your suggestion 
#3
https://github.com/anthropics/claude-code/issues/3
 of only smooshing the most-recent user message seems cleanest). But trimming tool_result bloat reduces the surface area for cache-busting byte drift in the meantime.
https://github.com/Ruya-AI/cozempic
https://github.com/Ruya-AI/cozempic
cnighswonger commented on Apr 17
cnighswonger
https://github.com/cnighswonger
on Apr 17
https://github.com/anthropics/claude-code/issues/49585#issuecomment-4267677678
Last edited by cnighswonger
More actions
@deafsquad
https://github.com/deafsquad
 Outstanding validation — 940K to 1.7K is exactly the compound result we were hoping for. The 208/23 applied/skipped ratio confirms the split fires on the hook-injected content our normalize couldn't reach.
On the 5 additional extensions — yes, we're interested. Preferred shape: one PR per extension so we can review and test individually. Each one gets its own env gate and stats counter following the existing pattern (shouldApplyFix, recordFixResult, _STATS_SCHEMA entry). If they pass the test suite and the dormancy detection handles accounts that don't have the relevant flags, they compose cleanly with the existing pipeline.
session_start_normalize and continue_trailer_strip are particularly interesting — those target cache busts we've documented but haven't fixed yet (
#43657
https://github.com/anthropics/claude-code/issues/43657
, 
#12
https://github.com/anthropics/claude-code/issues/12
).
4 remaining items
Load more
cnighswonger commented on Apr 17
cnighswonger
https://github.com/cnighswonger
on Apr 17
https://github.com/anthropics/claude-code/issues/49585#issuecomment-4269759566
More actions
v2.0.0 of 
claude-code-cache-fix
https://github.com/cnighswonger/claude-code-cache-fix
 shipped today with all seven PRs from 
@deafsquad
https://github.com/deafsquad
 merged (
#26
https://github.com/anthropics/claude-code/issues/26
–
#32
https://github.com/anthropics/claude-code/issues/32
). The interceptor now covers 15 cache-stability vectors — the combined stack measured a 99.8% reduction in unnecessary cache creation on affected sessions.
The latest find (
#32
https://github.com/anthropics/claude-code/issues/32
) is a new miss class 
@deafsquad
https://github.com/deafsquad
 identified live today: 
tool_use.input
 field-set drift between turns. CC re-serializes past 
tool_use
 blocks non-deterministically, adding or removing fields not in the tool's 
input_schema
 . A single SendMessage block drifted by 2334 bytes and triggered a 620K-token full cache rebuild. This is a distinct mechanism from the smoosh/resume/cache_control drift documented earlier in this thread — it happens mid-session with no restart event.
146 tests across the full fix suite, all green.
deafsquad commented on Apr 17
deafsquad
https://github.com/deafsquad
on Apr 17
https://github.com/anthropics/claude-code/issues/49585#issuecomment-4269829648
Author
More actions
Congrats on shipping v2.0.0 
@cnighswonger
https://github.com/cnighswonger
 — seven PRs landed in a day is a lot of reviewer-throughput. Appreciated.
Two items in the pipe:
#33
https://github.com/cnighswonger/claude-code-cache-fix/pull/33
 
cache_control_sticky
 — just opened. Addresses a 
new class
 of miss I caught at 16:27:13 UTC today: 
cw=619,722, hit=2.3%
 , mid-session, no restart. The issue is that CC's own 
cache_control
 marker moves to the new last-user-msg each turn — the previous position silently loses the marker, and those bytes now differ from the server's cached copy. Stack today (even with 
cache_control_normalize
 from 
EPIPE Crash When Running Claude Code in Python Project Directory #31
https://github.com/anthropics/claude-code/issues/31
) can't prevent this because CC removes the marker before we see the body. 
_sticky
 persists per-session marker-positions in a state file (same pattern as 
deferred_tools_restore
 ) and reinstates them on subsequent turns. 14 new tests, 121 total green.
Live confirmation of the class today at 
16:41:45 UTC
: another 
cw=864,480, hit=2.2%
 miss on the same session. Same fingerprint. If 
Add bash/emacs keybindings to move around options #33
https://github.com/anthropics/claude-code/issues/33
 merges, this class becomes cheap.
One observation worth flagging for #30/#31 merge ordering:
In the vendored copy I was running (which predated your v2.0.0 so it had the full stack including 
#31
https://github.com/anthropics/claude-code/issues/31
 extensions active), a Wave-2 teammate of mine spotted what looks like an ordering issue in 
preload.mjs
 : 
cache_control_normalize
 runs BEFORE 
continue_trailer_strip
 . On a 
--continue
 body, 
cache_control_normalize
 places the marker on the "Continue from where you left off." trailer (because it's the last block); 
continue_trailer_strip
 then removes the whole trailer block — taking the marker with it. Result: the body goes to the wire with no user-side 
cache_control
 marker at all. Next turn, 
cache_control_normalize
 places a fresh one on the new last block, but the previous position's bytes have shifted.
Since 
#30
https://github.com/anthropics/claude-code/issues/30
 and 
#31
https://github.com/anthropics/claude-code/issues/31
 are still under review, a minimal fix: move the 
continue_trailer_strip
 call-site ABOVE the 
cache_control_normalize
 call-site in 
preload.mjs
 before merging. That way the trailer is gone when 
cache_control_normalize
 runs. No test changes needed.
This is a small (~50-100 byte) drift on 
--continue
 only, so not urgent — but worth doing before both merge because the interaction is subtle.
Validation setup on my side:
 I'll pull v2.0.0 into my vendored copy now that it's shipped and get 
#32
https://github.com/anthropics/claude-code/issues/32
's benefit live (the 15:16:52 miss class). 
#33
 sits in queue. If it helps the review, I can run a 
claude-code-cache-fix@beta
 install on a separate test workspace with before/after metrics on a 
--continue
 resume.
Onward.
deafsquad commented on Apr 17
deafsquad
https://github.com/deafsquad
on Apr 17
https://github.com/anthropics/claude-code/issues/49585#issuecomment-4269846734
Author
More actions
Correction to my "I'll pull v2.0.0 now" line from the previous comment — we're going to wait for PR 
#33
https://github.com/anthropics/claude-code/issues/33
 to land and do a single consolidated refresh of the vendored preload, so 
#32
https://github.com/anthropics/claude-code/issues/32
 and 
#33
https://github.com/anthropics/claude-code/issues/33
 go live together. Fewer moving parts to reason about when we're measuring.
New evidence for #33 in the meantime
 — a third ~900K cw full-prefix miss fired in my current long-running session just now:
16:27:13 UTC  cw=804,428  hit=2.3%
16:41:45 UTC  cw=864,480  hit=2.2%
16:57:41 UTC  cw=908,760  hit=2.1%   ← just now

~15 minute cadence, same pid (no restart), session is 1400+ messages. Every miss has the same fingerprint: one past-turn user-msg lost its 
cache_control
 marker because CC moved the marker to the new last-user-msg. 
cr
 floors at 19,282 (the stable system[2] ephemeral cache) on every one. Nothing from our current extension set catches it ( 
cache_control_normalize
 normalizes placement on the 
current
 last block, but can't preserve markers on 
past
 blocks — CC has already stripped them before the interceptor runs).
#33
https://github.com/anthropics/claude-code/issues/33
's 
cache_control_sticky
 persists a per-session state file of where markers have been placed and reinstates them on subsequent turns (up to Anthropic's 4-breakpoint cap). Same pattern as 
deferred_tools_restore
 .
Cost estimate for the pattern: three misses × 850K × Opus 4.7 ephemeral cache-creation rate ≈ ~$33 on this one session alone, 30-minute window. Whatever slice of Anthropic's fleet runs long 
--continue
 sessions is paying this tax continuously.
No action from you needed — just annotating the thread with production evidence while 
#33
https://github.com/anthropics/claude-code/issues/33
 waits for review.
deafsquad commented on Apr 17
deafsquad
https://github.com/deafsquad
on Apr 17
https://github.com/anthropics/claude-code/issues/49585#issuecomment-4270235440
Author
More actions
Quick follow-up, mostly for 
@cnighswonger
https://github.com/cnighswonger
 and anyone reading the thread for PR state:
Checked the state of PRs 
#30
https://github.com/anthropics/claude-code/issues/30
-
#33
https://github.com/anthropics/claude-code/issues/33
 against cnighswonger's fork. All four still show 
OPEN
 on GitHub, but their content is already in published releases via direct commits rather than GitHub merge-button merges:
PR
Extension
Commit on upstream/main
Released in
#30
https://github.com/cnighswonger/claude-code-cache-fix/pull/30
reminder_strip
6e2448d
v2.0.0
#31
https://github.com/cnighswonger/claude-code-cache-fix/pull/31
cache_control_normalize
dfeac92
v2.0.0
#32
https://github.com/cnighswonger/claude-code-cache-fix/pull/32
tool_use_input_normalize
ed4aac9
v2.0.0
#33
https://github.com/cnighswonger/claude-code-cache-fix/pull/33
cache_control_sticky
6ae092d
v2.0.1
So your v2.0.0 release note ("all seven PRs from 
@deafsquad
https://github.com/deafsquad
 merged (
#26
https://github.com/anthropics/claude-code/issues/26
-32)") is correct on content — the extensions are all live — but the PRs themselves weren't merged via the GitHub UI, which is why they still appear OPEN on the PR list. If you want the PR list to reflect reality, "Close with comment: 
content landed in <sha>, released in <tag>
 " on each would do it. Our deafsquad-fork branches can stay as historical-diff references.
One nice follow-up I noticed while checking: 
v2.0.2 patches a 4-marker-limit bug in cache_control_sticky
 that went out in v2.0.1. Good catch — thanks for shipping the fix quickly.
On my side: pulled v2.0.2 into the vendored copy we run end-to-end. Full 8-extension stack active again. The cache-miss class I was documenting (the 15-minute ~900K cw cadence from 
cache_control
 marker drift) is now covered by 
#33
https://github.com/anthropics/claude-code/issues/33
's sticky logic. Will report production cache-hit metrics once we've accumulated a few hours on the new stack.
Onward.
cnighswonger commented on Apr 17
cnighswonger
https://github.com/cnighswonger
on Apr 17
https://github.com/anthropics/claude-code/issues/49585#issuecomment-4270333905
More actions
Good audit — we just added close comments on 
#30
https://github.com/anthropics/claude-code/issues/30
-
#33
https://github.com/anthropics/claude-code/issues/33
 with the landed SHAs and release tags.
Looking forward to your production cache-hit numbers on v2.0.2.
cnighswonger commented on Apr 17
cnighswonger
https://github.com/cnighswonger
on Apr 17
https://github.com/anthropics/claude-code/issues/49585#issuecomment-4270471076
More actions
Heads up 
@deafsquad
https://github.com/deafsquad
 — if you're running v2.0.1 or v2.0.2 with 
cache_control_sticky
 enabled (the default), upgrade to v2.0.3 immediately:
npm update claude-code-cache-fix

The sticky extension assumed CC uses exactly 2 
cache_control
 markers, leaving a fixed budget of 2 for historical positions. CC v2.1.112 uses 3 markers in some configurations — pushing the total to 5 and exceeding Anthropic's hard limit of 4. Result: 
400 invalid_request_error
 .
v2.0.3 counts existing markers dynamically instead of assuming CC's budget. If you hit this before upgrading, 
CACHE_FIX_SKIP_CACHE_CONTROL_STICKY=1
 disables the extension as a workaround.
deafsquad commented on Apr 17
deafsquad
https://github.com/deafsquad
on Apr 17
https://github.com/anthropics/claude-code/issues/49585#issuecomment-4270615914
Author
More actions
@cnighswonger
https://github.com/cnighswonger
 — thanks for the rapid v2.0.2 → v2.0.3 turnaround.
Quick post-mortem from my side: the 
cache_control_sticky × cache_control_normalize × CC system[2]
 interaction was an own-goal in my original PR 
#33
https://github.com/anthropics/claude-code/issues/33
 design. I tested sticky in isolation against a body without any existing 
cache_control
 markers, so the 3-historical-slot budget looked fine. Running it against a real body where 
cache_control_normalize
 had already placed the canonical + CC had its system[2] = instant 5-block violation. Should have stress-tested the composition, not just the component.
Your v2.0.3 fix (count existing markers dynamically, cap total at 4) is the correct long-term shape — hardcoded budget assumptions are the wrong axis to compute on, especially since Anthropic's per-config marker count can drift (CC 2.1.112 using 3 proves it). Good call.
On my side: swapped the vendored copy we run to v2.0.3 this afternoon. Verified the dynamic-count logic runs clean across our 1400+ message session. No more 5-marker bodies crossing the wire.
One observation worth flagging for anyone upgrading: if you're upgrading from v2.0.1 / v2.0.2 and the interaction already bit you, the session state file at 
~/.claude/cache-fix-state/cache-control-sticky-<key>.json
 may contain 3 historical positions from the old budget. The v2.0.3 dynamic-count logic handles this gracefully (it caps at 4-total at emission time, not at state-write time), so no manual cleanup is required — but worth mentioning.
Still zero 
@anthropic.com
 engagement on the underlying thread, which continues to be the bigger issue: we're ~14 PRs deep into patching a closed-source tool via leaked TypeScript source, cnighswonger is running a production npm package to patch user-facing behavior, and Anthropic users are paying the cache-churn tax for bugs that would take one internal engineer a lunch break to fix. The asymmetry isn't getting better.
That aside — thanks 
@cnighswonger
https://github.com/cnighswonger
 for the turnaround. v2.0.3 is live on our side.
deafsquad commented on Apr 17
deafsquad
https://github.com/deafsquad
on Apr 17
https://github.com/anthropics/claude-code/issues/49585#issuecomment-4270996108
Author
More actions
Two releases this week materially changed the landscape for cache-fix mitigations, worth recording here for the thread:
v2.1.112 (silently cut context 5x)
The 
[1m]
 tag on model strings (e.g. 
claude-opus-4-6[1m]
 ) is gone. 
context-1m-2025-08-07
 experiment flag reset server-side. Max-5x accounts that had 1M on v2.1.97 are at 200K on v2.1.112 with zero UI indication. Filed at 
#50083
https://github.com/anthropics/claude-code/issues/50083
, reports cross-linked from 
#41082
https://github.com/anthropics/claude-code/issues/41082
 / 
#44403
https://github.com/anthropics/claude-code/issues/44403
 / 
#47549
https://github.com/anthropics/claude-code/issues/47549
 (appears to be a recurring flag-reset pattern: March 26, April 13, April 17).
Workaround that bypasses the server-side flag (documented by 
@cnighswonger
https://github.com/cnighswonger
 at 
#50083
https://github.com/anthropics/claude-code/issues/50083
):
export DISABLE_COMPACT=1
export CLAUDE_CODE_MAX_CONTEXT_TOKENS=1000000

Requires v2.1.112+. 
CLAUDE_CODE_AUTO_COMPACT_WINDOW
 alone does NOT work (code applies 
Math.min(modelWindow, configured)
 — if server says 200K, you're capped).
Relevant for this thread because the smoosh-fusion cache-miss class we identified is 
most expensive in long sessions with large context
. Cutting the window to 1/5 both (a) triggers auto-compaction every 15-20 exchanges instead of every few hours, and (b) each compaction cycle rewrites the conversation summary and busts prefix cache anew. The net effect on users running cache-fix mitigations is that the sticky-marker preservation and historical-cache work does a fraction of what it used to — you're paying the compaction cache rebuild more often than you're saving uncached rebuilds.
v2.1.113 (deleted cli.js, shipped a Bun binary)
The npm package is now just 
bin/claude.exe
 (245MB platform-specific Bun binary) + a postinstall copier. Filed at 
cnighswonger/claude-code-cache-fix#35
https://github.com/cnighswonger/claude-code-cache-fix/issues/35
 by 
@cowwoc
https://github.com/cowwoc
.
Architectural implication
: every JavaScript-preload-based cache-fix mitigation (including 
@cnighswonger
https://github.com/cnighswonger
's 
claude-code-cache-fix
 , the most-deployed community workaround for bugs in this thread) stops working on v2.1.113. 
NODE_OPTIONS=--import=preload.mjs
 has nothing to attach to — there's no 
cli.js
 , no Node process, no 
globalThis.fetch
 to patch. Users who auto-update silently fall back to native-mode (2.1.109 on the slower release channel), losing multiple months of Anthropic-side fixes. Users who pin to 2.1.112 keep preload working but lose the workaround path for the context-window cut.
Combined, these two releases in sequence put community cache-fix users in a position where they have to pick which bug they tolerate.
What the proxy architecture changes
ANTHROPIC_BASE_URL
 is an SDK-level contract that the Bun binary honors identically to the Node CLI did — the SDK client resolves it before any transport code runs. A local HTTP proxy at 
127.0.0.1:9801
 can intercept every outbound message body, apply the same byte-stabilization logic 
preload.mjs
 did (the 8 extensions from cnighswonger v2.0.3: smoosh_split, session_start_normalize, continue_trailer_strip, deferred_tools_restore, reminder_strip, cache_control_normalize, tool_use_input_normalize, cache_control_sticky), forward to Anthropic, and stream the SSE response back.
This approach survives the Bun switch because it operates at the protocol boundary, not the language runtime. It would also survive any future Bun-to-Deno or Bun-to-native-binary switch. The only way Anthropic could close it is by removing 
ANTHROPIC_BASE_URL
 support, which would break every enterprise proxy deployment (including their own customers' corporate firewall setups).
I've been building this locally over the past ~24h. It's working end-to-end — 1284+ tests green, rate limiting + circuit breaking + streaming + the 8-extension pipeline + per-session turn archive for miss diagnosis. Not packaged for distribution yet (it runs in a pre-existing hooks-orchestration process of ours). Design notes + forward-looking thoughts posted to 
cnighswonger/claude-code-cache-fix#35
https://github.com/cnighswonger/claude-code-cache-fix/issues/35
 if anyone wants to read the architecture.
What I'd ask the triage team
Still zero 
@anthropic.com
 green-badge engagement on this thread (
#49585
https://github.com/anthropics/claude-code/issues/49585
), 
#44045
https://github.com/anthropics/claude-code/issues/44045
, or 
#48734
https://github.com/anthropics/claude-code/issues/48734
, despite a month of empirical evidence and source-level attribution. 
@cnighswonger
https://github.com/cnighswonger
 is running a production npm package patching user-facing behavior. Community contributors (myself included) have filed 7+ PRs into that repo with tests and simulation. The response from Anthropic's release side has been to ship two releases that make the workarounds harder without acknowledging the underlying bugs.
If there's a policy reason community contributions aren't being engaged with, say so publicly. If there isn't — a single internal engineer spending a day reviewing this thread and 
#50083
https://github.com/anthropics/claude-code/issues/50083
 could resolve a recurring user frustration that's costing your own customers real money (per the OTEL billing analysis earlier in this thread).
Running out to dogfood the proxy. Will report cache-hit rate deltas on a long session once it's stable on v2.1.113.
cc 
@cnighswonger
https://github.com/cnighswonger
 
@junaidtitan
https://github.com/junaidtitan
 
@cowwoc
https://github.com/cowwoc
 
@fgrosswig
https://github.com/fgrosswig
 
@ArkNill
https://github.com/ArkNill
 
@wadabum
https://github.com/wadabum
 — for visibility on the combined window-cut + preload-kill picture.
👀 React with 👀 1 cnighswonger
YuriyKrasilnikov
https://github.com/YuriyKrasilnikov
mentioned this 
on Apr 18
https://github.com/anthropics/claude-code/issues/49585#event-6092567330
[MODEL] Complex engineering behavior regression across sessions; request RCA and auditability guarantees #50513
https://github.com/anthropics/claude-code/issues/50513
s6yoho
https://github.com/s6yoho
mentioned this 
on Apr 24
https://github.com/anthropics/claude-code/issues/49585#event-6209184369
[BUG] ToolSearch unlock invalidates prompt-cache prefix mid-session #53132
https://github.com/anthropics/claude-code/issues/53132
github-actions
https://github.com/apps/github-actions
mentioned this 
on Apr 28
https://github.com/anthropics/claude-code/issues/49585#event-6279364170
[Bug] Prompt cache unexpectedly collapses mid-session on Opus 4.x #54563
https://github.com/anthropics/claude-code/issues/54563
eunseokOh
https://github.com/eunseokOh
mentioned this 
on May 11
https://github.com/anthropics/claude-code/issues/49585#event-6521244353
[BUG] Excessive token usage (~20k–30k tokens) for trivial prompts in Claude Code CLI #52979
https://github.com/anthropics/claude-code/issues/52979
github-actions
https://github.com/apps/github-actions
added
stale Issue is inactive
https://github.com/anthropics/claude-code/issues?q=state%3Aopen%20label%3A%22stale%22
 Issue is inactive
on May 11
https://github.com/anthropics/claude-code/issues/49585#event-25378638997
github-actions commented on May 25
github-actions
https://github.com/apps/github-actions
 bot
on May 25
https://github.com/anthropics/claude-code/issues/49585#issuecomment-4537691624
 – with 
GitHub Actions
https://help.github.com/en/actions
More actions
Closing for now — inactive for too long. Please 
open a new issue
https://github.com/anthropics/claude-code/issues/new/choose
 if this is still relevant.
github-actions
https://github.com/apps/github-actions
closed this as 
not planned
https://github.com/anthropics/claude-code/issues?q=is%3Aissue%20state%3Aclosed%20archived%3Afalse%20reason%3Anot-planned
 
on May 25
https://github.com/anthropics/claude-code/issues/49585#event-25941839856
Sign up for free
https://github.com/signup?return_to=https://github.com/anthropics/claude-code/issues/49585
 
to join this conversation on GitHub.
 Already have an account? 
Sign in to comment
https://github.com/login?return_to=https://github.com/anthropics/claude-code/issues/49585
Metadata
Metadata
Assignees
No one assigned
Labels
area:core
https://github.com/anthropics/claude-code/issues?q=state%3Aopen%20label%3A%22area%3Acore%22
 
area:cost
https://github.com/anthropics/claude-code/issues?q=state%3Aopen%20label%3A%22area%3Acost%22
 
bug Something isn't working
https://github.com/anthropics/claude-code/issues?q=state%3Aopen%20label%3A%22bug%22
 Something isn't working 
has repro Has detailed reproduction steps
https://github.com/anthropics/claude-code/issues?q=state%3Aopen%20label%3A%22has%20repro%22
 Has detailed reproduction steps 
stale Issue is inactive
https://github.com/anthropics/claude-code/issues?q=state%3Aopen%20label%3A%22stale%22
 Issue is inactive
Type
No type
Fields
No fields configured for issues without a type.
Projects
No projects
Milestone
No milestone
Relationships
None yet
Development
No branches or pull requests
Participants
 
 
Issue actions
Open in GitHub Copilot app
Footer
© 2026 GitHub, Inc.
Footer navigation
Terms
https://docs.github.com/site-policy/github-terms/github-terms-of-service
Privacy
https://docs.github.com/site-policy/privacy-policies/github-privacy-statement
Security
https://github.com/security
Status
https://www.githubstatus.com/
Community
https://github.community/
Docs
https://docs.github.com/
Contact
https://support.github.com?tags=dotcom-footer
Manage cookies
Do not share my personal information
You can't perform that action at this time.
