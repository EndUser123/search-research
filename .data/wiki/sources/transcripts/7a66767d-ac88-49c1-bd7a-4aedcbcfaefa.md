---
source_id: "7a66767d-ac88-49c1-bd7a-4aedcbcfaefa"
title: "PSA: Claude Code's Session Isolation Bug - How Shared History Corrupts Multiple Sessions (And why I'm shocked Anthropic still hasn't fixed it) : r/ClaudeCode - Reddit"
notebook_id: 59329bf3-4765-4d4e-8ec6-f2eceeba0f41
url: https://www.reddit.com/r/ClaudeCode/comments/1qt2l69/psa_claude_codes_session_isolation_bug_how_shared/
type: web_page
exported: 2026-07-27
---

# PSA: Claude Code's Session Isolation Bug - How Shared History Corrupts Multiple Sessions (And why I'm shocked Anthropic still hasn't fixed it) : r/ClaudeCode - Reddit
PSA: Claude Code's Session Isolation Bug - How Shared History Corrupts Multiple Sessions (And why I'm shocked Anthropic still hasn't fixed it) : r/ClaudeCode

Skip to main content

https://www.reddit.com/r/ClaudeCode/comments/1qt2l69/psa_claude_codes_session_isolation_bug_how_shared/#main-content

 PSA: Claude Code's Session Isolation Bug - How Shared History Corrupts Multiple Sessions (And why I'm shocked Anthropic still hasn't fixed it) : r/ClaudeCode

Open menu

Open navigation 

https://www.reddit.com/

Go to Reddit Home

 

r/ClaudeCode

TRENDING TODAY

Get App

Get the Reddit app

Log In

https://www.reddit.com/login/

Log in to Reddit

Expand user menu

Open settings menu

Skip to Navigation

https://www.reddit.com/r/ClaudeCode/comments/1qt2l69/psa_claude_codes_session_isolation_bug_how_shared/#left-sidebar-container

 

Skip to Right Sidebar

https://www.reddit.com/r/ClaudeCode/comments/1qt2l69/psa_claude_codes_session_isolation_bug_how_shared/#right-sidebar-container

Back

Go to ClaudeCode

https://www.reddit.com/r/ClaudeCode/

r/ClaudeCode

https://www.reddit.com/r/ClaudeCode/

• 2mo ago

marcopaulodirect

https://www.reddit.com/user/marcopaulodirect/

Locked post

Stickied post

Archived post

View post in other languages

Report

PSA: Claude Code's Session Isolation Bug - How Shared History Corrupts Multiple Sessions (And why I'm shocked Anthropic still hasn't fixed it)

TL;DR:

* If you run multiple Claude Code sessions in the same repo, they share history, transcripts, and state files. This has been reported since June 2025 and keeps getting closed as "duplicate" without being fixed. Workaround: use full git clones instead of one repo.

Why I'm posting this:

 I want to contribute something useful and actionable — not just vent. This bug has cost me real time, and based on the GitHub issues I've found, I'm not alone. My goal is to document this clearly enough that Anthropic finally prioritizes fixing it.

The most helpful thing you can do:

 Comment on 

GitHub issue #14036

[https://github.com/anthropics/claude-code/issues/14036](https://github.com/anthropics/claude-code/issues/14036)

 with your experience — it's at risk of auto-close due to inactivity. A 👍 reaction and brief comment about your use case goes further than another duplicate issue.

I've also added 5 comments below representing different impact levels. Find the one that matches your experience and share your story there — it helps show the scope of this problem.

My Experience

When running multiple Claude Code sessions in the same git repository, they share conversation history, causing serious workflow disruption:

Prompt history pollution

: Using up arrow to reuse a prompt shows ALL prompts from ALL open sessions mixed together

Transcript contamination

: My automated scripts that parse session end summaries (not just compact summaries) are completely broken because transcripts contain context from multiple unrelated sessions

Custom command failures

: I use 

/precompact

 and 

/cexit

 commands that extract structured context from session transcripts via external LLMs (Gemini/Perplexity) and save to PostgreSQL for searchable history. These would randomly extract the 

wrong session's transcript

 or get contaminated with cross-session content

State file collisions

: Snapshot pointer files written by my automation would get overwritten by parallel sessions

Community-Reported Symptoms (GitHub Issues)

This isn't just my problem. Here are documented issues from GitHub that many users may not realize are caused by the same shared history bug:

Critical Security/Privacy Issues

Information leaking between sessions

: File paths and context from one project appearing in completely unrelated sessions

Environment file exposure

: Sensitive files like 

.env.swarm

 from one project bleeding into another project's session

Cross-session summary contamination

: Session summaries containing metadata and context from different projects

Workflow Disruption

Incorrect commit messages

: Claude mixing commit messages between concurrent sessions - e.g., Session A working on MariaDB pulls commit content from Session B working on Docker issues

Context confusion

: Sessions getting mixed up between debugging and feature development work, causing Claude to switch tasks unexpectedly

Cross-project configuration leakage

: Project configurations bleeding across unrelated sessions

Data Integrity Issues

Resume command failures

: 

--resume

 flag displaying incorrect session metadata across projects

Session metadata corruption

: Sessions losing proper context isolation

The Root Cause

Claude Code identifies projects by 

git repository root

. All concurrent sessions in the same repo share:

Command history (up-arrow pollution)

Transcript storage location

Session state files

This means if you're running one session for debugging and another for feature development in the same repo, they're fighting over the same storage.

The Official Status

This is confirmed as a 

BUG, not a feature

. It's been reported since at least June 2025 with labels including "area:security," "memory," and "Session Isolation Failure". GitHub shows at least 7-8 duplicate issues filed over multiple months, yet it remains unresolved as of February 2026.

Expected Behavior

Each Claude Code session should be completely isolated. The ONLY time history should be shared is when explicitly using 

--resume

 to continue a specific previous session.

My Workaround: Full Git Clones (Not Worktrees)

After extensive experimentation, I found that 

separate full git clones

 provide complete isolation:

Result:

 Complete isolation — separate transcript files, separate prompt history, separate pointer files. My 

/precompact

 and 

/cexit

 automation now reliably captures the correct session's context.

Note:

 Git worktrees don't fully solve this because Claude still treats them as the same repository root.

Why This Matters for Power Users

If you're doing any of the following, this bug is silently breaking your workflow:

Running automation on session transcripts

 — Scripts that parse 

/compact

 summaries or session end data will get contaminated cross-session content

Using custom commands

 — Any command that reads/writes session-specific files can collide with parallel sessions

Maintaining searchable session history

 — Database imports of session data become unreliable when sessions bleed into each other

Building context extraction pipelines

 — External LLM analysis of Claude transcripts gets confused by merged context

Decision archaeology

 — Looking back at "Why did I decide X?" becomes impossible when sessions are mixed

Handoff generation

 — Auto-generating TODO files from session summaries produces garbage when multiple work streams pollute each other

Real-World Impact Example

I use 

/precompact

 before compacting sessions to extract structured context (session objectives, current task, last completed step, breakthroughs, key decisions, files touched, etc.) via Gemini/Perplexity and save it to PostgreSQL. This gives me:

Quick search across all sessions ("When did I last discuss X?")

Continuity across projects

Pattern detection for recurring obstacles

Infrastructure audit trails

Before the workaround:

 

/precompact

 would randomly pull transcripts from my debugging session when I was trying to summarize my feature work, corrupting my entire session history database.

After full git clones:

 Perfect isolation. Each work stream maintains clean, searchable history.

Who's Affected?

Anyone running multiple Claude Code instances in the same repo

Anyone with automation/scripts parsing session data

Anyone working on multiple tasks simultaneously

Anyone concerned about sensitive information leaking between sessions

Anyone using custom commands that depend on session state

Has anyone else hit this? What workarounds have you found?

Since polls aren't available in this sub:

 I've added 5 comments below representing different impact levels. Find the one that matches your experience and reply with your story — it helps show Anthropic the scope of this issue. And if you have a specific story, reply to that comment with details.

Read more

1

Comments Section

Related Answers Section

Related Answers

Innovative uses for Claude Code in projects

Claude Code has been a game-changer for many users, offering a wide range of innovative applications beyond traditional coding tasks. Here are some of the most interesting and practical use cases shared by Redditors:

Software Development and Coding

Code Generation and Testing

: Claude Code is frequently used to generate code, create test cases, and even write complete applications from scratch. 

"I built a movie night planner app for my family..."

https://www.reddit.com/r/ClaudeCode/comments/1rlglgq/comment/o8sfwsb/

Debugging and Refactoring

: It can help in debugging code, refactoring, and optimizing performance. 

"Claude Code has been extremely useful for me in setting up tools integration..."

https://www.reddit.com/r/ClaudeAI/comments/1r6uaf9/a_thread_for_use_cases_of_claude_code/

Git and GitHub Tasks

: Claude Code can manage Git and GitHub CLI tasks, including committing, branching, pulling, and pushing. 

"Just ask Claude to handle your Git and GitHub CLI tasks."

https://www.reddit.com/r/ClaudeAI/comments/1qcan9z/my_top_10_claude_code_tips_from_11_months_of/

Data Management and Analysis

PDF and Document Processing

: Claude Code can handle large PDF and Word documents, extracting and summarizing information. 

"Huge word and pdf documents"

https://www.reddit.com/r/ClaudeCode/comments/1rlglgq/comment/o8rzmo5/

Data Analysis and Reporting

: It can be used to analyze data from various sources and generate reports. 

"We use it for analytics..."

https://www.reddit.com/r/ProductManagement/comments/1quo0qk/comment/o3bsdq7/

Business and Productivity

Meeting Summaries and Task Management

: Claude Code can create executive summaries of meetings and manage task lists. 

"I record Teams meetings, etc (as allowed) and have Claude give me an executive summary."

https://www.reddit.com/r/ClaudeAI/comments/1r9weig/comment/o6fi21d/

Board Meeting Preparation

: It can help in preparing for board meetings by anticipating questions and building narratives. 

"I use it heavily for board meeting prep."

https://www.reddit.com/r/ClaudeAI/comments/1r9weig/comment/o6fewc9/

Life Organization

: Claude Code can be integrated with tools like Notion to create a comprehensive life organization system. 

"I use it together with notion for a life organisation system."

https://www.reddit.com/r/ClaudeAI/comments/1r9weig/comment/o6fjoz9/

Creative and Personal Uses

Role-Playing and Storytelling

: Users have found it useful for role-playing and creating interactive stories. 

"I role play with Claude where it puts me in a very specific time and place from history..."

https://www.reddit.com/r/ClaudeAI/comments/1r9weig/comment/o6fmqk1/

Writing and Content Creation

: Claude Code can assist in writing books, articles, and other creative content. 

"I'm using it to write a book, using Claude and obsidian."

https://www.reddit.com/r/ClaudeAI/comments/1r9weig/comment/o6fc9rc/

Unique and Unusual Uses

Etsy Shop Organization

: It can help in organizing and backing up Etsy shop data. 

"I run a decent Etsy shop and my organization went to trash."

https://www.reddit.com/r/ClaudeAI/comments/1r9weig/comment/o6ffa3i/

Retirement Planning

: Claude Code can read and summarize legal documents like trusts to aid in retirement planning. 

"It's helping me plan retirement."

https://www.reddit.com/r/ClaudeAI/comments/1r9weig/comment/o6fdhlv/

Customizing Windows 11

: It can be used to customize Windows 11 settings and disable telemetry. 

"The best non coding use case for me has been the ability to customize windows 11 pro much better."

https://www.reddit.com/r/ClaudeAI/comments/1r6uaf9/comment/o5u1n7l/

Claude Skills and Integrations

Rube MCP Connector

: This skill allows Claude to connect with over 500 apps, streamlining automation workflows. "Rube MCP Connector - This one's wild."

Superpowers

: A dev toolkit that includes commands for brainstorming, planning, and executing tasks. 

"Superpowers - obra's dev toolkit."

https://www.reddit.com/r/ClaudeAI/comments/1ojuqhm/10_claude_skills_that_actually_changed_how_i_work/

Document Suite

: Official skill for working with Word, Excel, PowerPoint, and PDF files. 

"Document Suite - Official one."

https://www.reddit.com/r/ClaudeAI/comments/1ojuqhm/10_claude_skills_that_actually_changed_how_i_work/

These examples demonstrate the versatility and power of Claude Code in various fields, from software development to business and personal productivity.

Claude Code Project Communities

ClaudeCode 692K weekly visitors Join a community where claude code enthusiasts build, share, and solve together.

https://www.reddit.com/r/ClaudeCode/

ClaudeAI 1.9M weekly visitors Join This is a Claude and Claude Code discussion subreddit to help you make a fully informed decision about using Claude and Claude Code to best effect for your own purposes. ¹⌉ Anthropic does not control or operate this subreddit or endorse views expressed here. ²⌉ If your problem requires Anthropic's help, visit https://support.anthropic.com/ This subreddit is not the right place to fix your account issues. ³⌉ For more help, check the resources below. ⁴⌉ Please read the rules before posting.

https://www.reddit.com/r/ClaudeAI/

opencodeCLI 76K weekly visitors Join r/opencodeCLI is a community-driven subreddit for sharing resources, discussions, and tips around OpenCode which is a Go + TypeScript open-source CLI TUI for coding assistance. It supports multiple providers (Anthropic Claude, OpenAI, Gemini, local models, etc.)

https://www.reddit.com/r/opencodeCLI/

claude 275K weekly visitors Join Community for Anthropic's generative AI model, Claude.

https://www.reddit.com/r/claude/

ClaudeAIJailbreak 28K weekly visitors Join A community to celebrate all things Claude and the fine art of jailbreaking all Anthropic Models, we will also be exploring prompt engineering and various jailbreaking of other models.

https://www.reddit.com/r/ClaudeAIJailbreak/

ClaudeCowork 14K weekly visitors Join A community where Claude Cowork fans can come and chat!

https://www.reddit.com/r/ClaudeCowork/

See Answer

https://www.reddit.com/answers/766ff150-7097-4b30-b3b2-6bbf0029608c/?q=Innovative+uses+for+Claude+Code+in+projects&source=PDP

Best practices for coding with Claude Code

https://www.reddit.com/answers/bf02af44-2e71-42d9-a04e-c690d1b31d7b/?q=Best+practices+for+coding+with+Claude+Code&source=PDP

How Claude Code enhances AI development

https://www.reddit.com/answers/15166aac-8443-4ec5-aa16-efc51f23f9ac/?q=How+Claude+Code+enhances+AI+development&source=PDP

Challenges faced when using Claude Code

https://www.reddit.com/answers/8f314328-ebc7-4b55-9308-ec1d174044ac/?q=Challenges+faced+when+using+Claude+Code&source=PDP

Comparing Claude Code with other AI tools

https://www.reddit.com/answers/1af7a930-520f-4c08-a284-030b8a0219af/?q=Comparing+Claude+Code+with+other+AI+tools&source=PDP

New to Reddit?

Create your account and connect with a world of communities.

Continue with Email

https://www.reddit.com/register/

Continue With Phone Number

https://www.reddit.com/login/

By continuing, you agree to our 

User Agreement

https://www.redditinc.com/policies/user-agreement

 and acknowledge that you understand the 

Privacy Policy

https://www.redditinc.com/policies/privacy-policy

.

More posts you may like

How do people run multiple Claude Code sessions?

https://www.reddit.com/r/ClaudeAI/comments/1q6u7xz/how_do_people_run_multiple_claude_code_sessions/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 3mo ago [

How do people run multiple Claude Code sessions?

](https://www.reddit.com/r/ClaudeAI/comments/1q6u7xz/how_do_people_run_multiple_claude_code_sessions/) 35 upvotes · 56 comments

Claude Code isn't "stupid now": it's being system prompted to act like that

https://www.reddit.com/r/ClaudeCode/comments/1rshmq8/claude_code_isnt_stupid_now_its_being_system/

 

r/ClaudeCode

https://www.reddit.com/r/ClaudeCode/

 • 11d ago [

Claude Code isn't "stupid now": it's being system prompted to act like that

](https://www.reddit.com/r/ClaudeCode/comments/1rshmq8/claude_code_isnt_stupid_now_its_being_system/) 150 upvotes · 118 comments

Finally fixed the Claude Code bug that kills your entire session (open source tool)

https://www.reddit.com/r/ClaudeAI/comments/1qasblk/finally_fixed_the_claude_code_bug_that_kills_your/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 2mo ago [

Finally fixed the Claude Code bug that kills your entire session (open source tool)

](https://www.reddit.com/r/ClaudeAI/comments/1qasblk/finally_fixed_the_claude_code_bug_that_kills_your/) 9 upvotes · 6 comments

Mental burnout from too many parallel Claude Code sessions?

https://www.reddit.com/r/ClaudeCode/comments/1r6y7od/mental_burnout_from_too_many_parallel_claude_code/

 

r/ClaudeCode

https://www.reddit.com/r/ClaudeCode/

 • 1mo ago [

Mental burnout from too many parallel Claude Code sessions?

](https://www.reddit.com/r/ClaudeCode/comments/1r6y7od/mental_burnout_from_too_many_parallel_claude_code/) 37 upvotes · 26 comments

Claude Code Bash Tool Broken on Windows - EINVAL Error on All Sessions Since Feb 25

https://www.reddit.com/r/ClaudeCode/comments/1re082h/claude_code_bash_tool_broken_on_windows_einval/

 

r/ClaudeCode

https://www.reddit.com/r/ClaudeCode/

 • 27d ago [

Claude Code Bash Tool Broken on Windows - EINVAL Error on All Sessions Since Feb 25

](https://www.reddit.com/r/ClaudeCode/comments/1re082h/claude_code_bash_tool_broken_on_windows_einval/) 10 upvotes · 6 comments

Discovered: How to bypass Claude Code conversation limits by manipulating session logs

https://www.reddit.com/r/ClaudeAI/comments/1nkdffp/discovered_how_to_bypass_claude_code_conversation/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 6mo ago [

Discovered: How to bypass Claude Code conversation limits by manipulating session logs

](https://www.reddit.com/r/ClaudeAI/comments/1nkdffp/discovered_how_to_bypass_claude_code_conversation/) 30 upvotes · 37 comments

Found 3 instructions in Anthropic's docs that dramatically reduce Claude's hallucination. Most people don't know they exist.

https://www.reddit.com/r/ClaudeAI/comments/1rzyqqt/found_3_instructions_in_anthropics_docs_that/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 2d ago [

Found 3 instructions in Anthropic's docs that dramatically reduce Claude's hallucination. Most people don't know they exist.

](https://www.reddit.com/r/ClaudeAI/comments/1rzyqqt/found_3_instructions_in_anthropics_docs_that/) 2.1K upvotes · 168 comments

Claude Code policy clear up from Anthropic.

https://www.reddit.com/r/ClaudeCode/comments/1r88vbs/claude_code_policy_clear_up_from_anthropic/

 

r/ClaudeCode

https://www.reddit.com/r/ClaudeCode/

 • 1mo ago [

Claude Code policy clear up from Anthropic.

](https://www.reddit.com/r/ClaudeCode/comments/1r88vbs/claude_code_policy_clear_up_from_anthropic/) 

 176 upvotes · 87 comments

When you close your session

https://www.reddit.com/r/ClaudeCode/comments/1rc79mh/when_you_close_your_session/

 

r/ClaudeCode

https://www.reddit.com/r/ClaudeCode/

 • 1mo ago [

When you close your session

](https://www.reddit.com/r/ClaudeCode/comments/1rc79mh/when_you_close_your_session/) 

 80 upvotes · 11 comments

How do you handle context loss between Claude Code sessions?

https://www.reddit.com/r/ClaudeAI/comments/1qn64j4/how_do_you_handle_context_loss_between_claude/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 2mo ago [

How do you handle context loss between Claude Code sessions?

](https://www.reddit.com/r/ClaudeAI/comments/1qn64j4/how_do_you_handle_context_loss_between_claude/) 8 upvotes · 39 comments

Claude Code just spinning endlessly without a response?

https://www.reddit.com/r/ClaudeAI/comments/1rcrzed/claude_code_just_spinning_endlessly_without_a/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 28d ago [

Claude Code just spinning endlessly without a response?

](https://www.reddit.com/r/ClaudeAI/comments/1rcrzed/claude_code_just_spinning_endlessly_without_a/) 

 14 upvotes · 15 comments

Claude Code loves breaking stuff and then declaring it an existing error

https://www.reddit.com/r/ClaudeCode/comments/1qp7qbe/claude_code_loves_breaking_stuff_and_then/

 

r/ClaudeCode

https://www.reddit.com/r/ClaudeCode/

 • 2mo ago [

Claude Code loves breaking stuff and then declaring it an existing error

](https://www.reddit.com/r/ClaudeCode/comments/1qp7qbe/claude_code_loves_breaking_stuff_and_then/) 34 upvotes · 39 comments

claude --resume: This session is being continued from a previous conversation that ran out of context. The conversation is summarized

https://www.reddit.com/r/ClaudeCode/comments/1plje40/claude_resume_this_session_is_being_continued/

 

r/ClaudeCode

https://www.reddit.com/r/ClaudeCode/

 • 3mo ago [

claude --resume: This session is being continued from a previous conversation that ran out of context. The conversation is summarized

](https://www.reddit.com/r/ClaudeCode/comments/1plje40/claude_resume_this_session_is_being_continued/) 4 upvotes · 9 comments

I gave Claude's Cowork a memory that survives between conversations. It never asks me to re-explain myself now, and I can't go back.

https://www.reddit.com/r/ClaudeAI/comments/1r6ipdk/i_gave_claudes_cowork_a_memory_that_survives/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 1mo ago [

I gave Claude's Cowork a memory that survives between conversations. It never asks me to re-explain myself now, and I can't go back.

](https://www.reddit.com/r/ClaudeAI/comments/1r6ipdk/i_gave_claudes_cowork_a_memory_that_survives/) 

 30 comments

Long-running Claude Code sessions have a fundamental DX problem: you can't walk away.

https://www.reddit.com/r/ClaudeAI/comments/1qkqd8m/longrunning_claude_code_sessions_have_a/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 2mo ago [

Long-running Claude Code sessions have a fundamental DX problem: you can't walk away.

](https://www.reddit.com/r/ClaudeAI/comments/1qkqd8m/longrunning_claude_code_sessions_have_a/) 25 upvotes · 36 comments

How do you all deal with Claude's small context window?

https://www.reddit.com/r/ClaudeCode/comments/1qps9xj/how_do_you_all_deal_with_claudes_small_context/

 

r/ClaudeCode

https://www.reddit.com/r/ClaudeCode/

 • 2mo ago [

How do you all deal with Claude's small context window?

](https://www.reddit.com/r/ClaudeCode/comments/1qps9xj/how_do_you_all_deal_with_claudes_small_context/) 33 upvotes · 49 comments

Is Claude now hiding thinking with no toggle? What the hell?

https://www.reddit.com/r/ClaudeCode/comments/1ry71b1/is_claude_now_hiding_thinking_with_no_toggle_what/

 

r/ClaudeCode

https://www.reddit.com/r/ClaudeCode/

 • 4d ago [

Is Claude now hiding thinking with no toggle? What the hell?

](https://www.reddit.com/r/ClaudeCode/comments/1ry71b1/is_claude_now_hiding_thinking_with_no_toggle_what/) 10 upvotes · 40 comments

Claude Code now hides its reasoning - where is it stored?

https://www.reddit.com/r/ClaudeAI/comments/1rtibjo/claude_code_now_hides_its_reasoning_where_is_it/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 10d ago [

Claude Code now hides its reasoning - where is it stored?

](https://www.reddit.com/r/ClaudeAI/comments/1rtibjo/claude_code_now_hides_its_reasoning_where_is_it/) 4 upvotes · 11 comments

TIL Claude Code's conversation logs are a recovery goldmine

https://www.reddit.com/r/ClaudeAI/comments/1r7tx5a/til_claude_codes_conversation_logs_are_a_recovery/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 1mo ago [

TIL Claude Code's conversation logs are a recovery goldmine

](https://www.reddit.com/r/ClaudeAI/comments/1r7tx5a/til_claude_codes_conversation_logs_are_a_recovery/) 8 upvotes · 3 comments

I built an open-source tool to stop Claude Code from re-reading my files every session (Persistent Memory)

https://www.reddit.com/r/ClaudeAI/comments/1pcylc9/i_built_an_opensource_tool_to_stop_claude_code/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 4mo ago [

I built an open-source tool to stop Claude Code from re-reading my files every session (Persistent Memory)

](https://www.reddit.com/r/ClaudeAI/comments/1pcylc9/i_built_an_opensource_tool_to_stop_claude_code/) 50 upvotes · 31 comments

Why is Claude being overly sensitive?

https://www.reddit.com/r/ClaudeAI/comments/1rlr7nt/why_is_claude_being_overly_sensitive/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 18d ago [

Why is Claude being overly sensitive?

](https://www.reddit.com/r/ClaudeAI/comments/1rlr7nt/why_is_claude_being_overly_sensitive/) 

 30 comments

I've found if you start a conversation with thinking off, then turn it on, Claude won't realize it's thinking, or that you can see it. Under that assumption, it went through a system prompt I've never seen that it shouldn't "reveal". New tweak by Anthropic or just a hallucination?

https://www.reddit.com/r/ClaudeAI/comments/1mvmn9j/ive_found_if_you_start_a_conversation_with/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 7mo ago [

I've found if you start a conversation with thinking off, then turn it on, Claude won't realize it's thinking, or that you can see it. Under that assumption, it went through a system prompt I've never seen that it shouldn't "reveal". New tweak by Anthropic or just a hallucination?

](https://www.reddit.com/r/ClaudeAI/comments/1mvmn9j/ive_found_if_you_start_a_conversation_with/) 

 imgur 37 upvotes · 11 comments

TIL Claude Code can speak to you when it needs help!

https://www.reddit.com/r/ClaudeAI/comments/1q2fhco/til_claude_code_can_speak_to_you_when_it_needs/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 3mo ago [

TIL Claude Code can speak to you when it needs help!

](https://www.reddit.com/r/ClaudeAI/comments/1q2fhco/til_claude_code_can_speak_to_you_when_it_needs/) 89 upvotes · 22 comments

Does anyone else start a new chat when Claude gets slow and then lose everything from the old one?

https://www.reddit.com/r/ClaudeAI/comments/1rxsu98/does_anyone_else_start_a_new_chat_when_claude/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 5d ago [

Does anyone else start a new chat when Claude gets slow and then lose everything from the old one?

](https://www.reddit.com/r/ClaudeAI/comments/1rxsu98/does_anyone_else_start_a_new_chat_when_claude/) 1 upvote · 26 comments

I gave Claude a memory for its own mistakes — it gets better every session

https://www.reddit.com/r/ClaudeAI/comments/1rlbjvl/i_gave_claude_a_memory_for_its_own_mistakes_it/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 19d ago [

I gave Claude a memory for its own mistakes — it gets better every session

](https://www.reddit.com/r/ClaudeAI/comments/1rlbjvl/i_gave_claude_a_memory_for_its_own_mistakes_it/) 14 upvotes · 22 comments

Community Info Section

r/ClaudeCode

https://www.reddit.com/r/ClaudeCode/

 

 

weekly limit reached.

Join

ClaudeCode

a community where claude code enthusiasts build, share, and solve together.

Show more

Public

Anyone can view, post, and comment to this community

Reddit Rules

https://www.redditinc.com/policies/content-policy

 

Privacy Policy

https://www.reddit.com/policies/privacy-policy

 

User Agreement

https://www.redditinc.com/policies/user-agreement

 

Your Privacy Choices

https://support.reddithelp.com/hc/articles/43980704794004

 

Accessibility

https://support.reddithelp.com/hc/sections/38303584022676-Accessibility

 

Reddit, Inc. © 2026. All rights reserved.

https://redditinc.com/

Expand Navigation

Expand Navigation

Collapse Navigation

Collapse Navigation

 

0cAFcWeA5fTAcJrBluxfM1C6mGWhjeb70Mu116ow5UXvtBchbvCpzrEG1gJgLPK1jQrf6mXlEP0wLUjvpreQrtFnpB6pTnxipWa8y5gup49GUnmi99h-1HBGM64Fp2j9F-yOO5wT9WEvXlueC_FLXZl851AW1qqa_RFJmsnXyyU_yBqc88705gpW7OX2v0bBSwHnM6la7lH7kExDBeowXURgexl5vpOwW3YSAjYjlbN2fV_5mTEKexIpZ5aoGn4xMhwSlPfK2vCtWkBIcplRtLxdhhats0Kay_CMsICX5-0aovzTMudTepkFpJaXc8hVigK8j83ualaeBKNJy7BJQk2lEOpUhKUAhLzXVY7BohkCEEzrkYM7PJ9x5zOCqmG8v5kGNrwAK09HJmxjy6SYRE6td3harhLe_ZvWzwzWxiuigOzl8VhDdsosxz_HrpsAguKCQhi9mRlbzuhcS-700JE0VwPxWMY_KxHvsuGJn4eVz7sIZE__jqX4uWdi6e8ZudwirLEdXvNsqkDEYct08OhR6NqdZJzkNKYjZXElmI6jMAZsuXfwQzHqLfiAOYA26l8Cp7H1VSd-xiJ2Zhm4XRp3vCj8qwWDSE8p4VH0C8fvzfeHIidL6cKH9s_I8mFJXo6J2DS1cdkVb16wC4hvM00GjLzyrKKUcY7CL0RntebjVlsqKylbRlW9nzFj4A_YLfCOytmLxnk0iN9r7ryhlrLIzB8K1j90S5FWx8utjdPwgT6jMc5K8dNf8_fhnzBBpzy7h8WlfekFlNi042LgHFmLiMr1u07MH66iHOuFOJF1w9VcxUV1MbJWX7JnRc5dPMz9yURAA9UmThjCR7iCn2reIU4dTbfECc0TkWunObE-JQAFLztcrCdi6icDYiyNsdrergv8dqScgFLBD02pmhJeyrtajD47IprXuq6V22_TVeHx_DrbYoBR16hflwY8C7EbdtS8ItKRPdUHki8iPhHnBAQXJ4hAPeQQ_aKY2Re-TeTL-znP3mU4cshZ7lIldkmcofwt7Pgw8f9GGNew7s7inin_FaPSmovKTjdoQV1KFvkJrR1Lx5DXBGCk6Fwb9ISAYwpwzjYnFDY9XbYvT7nxVa_HCN8nhfzzebvPQFQmEKbt_GzryG_T-Rh_VQOavNsQCILGhZ7PG28F9wsm5IPrjIuJmhPVRvG7u_-SkAThR4mnVC9Lqp4DFlX4b-NsHIrb5Muguv2YrRVGIHvTU50QXl0NGlWbq9heNV0FW4ro4rauRiZS9698_bOpm1FmsJ4XUo0ngXGNfu79U_28SHSgckJKHD9taG8jOSbv0c4MmObOxcwg2zy-PvB1sQ0-gFLmaCNGsTnZ-E7-3vbL7DKXvXzdKtdiYVrhJqB36-EcPMqLKpsVrlD6HnlGDVWP2FHLXhXgKJMaKEelU4UT84I5LqkQxIyqtdR5NSEHCypc-pJItl659_mQ5g93lVmABbXwdRPOI6Yscw012tfaannQDTX1ONGe65O8y2TPezjxjTNvFGmnxF3iC56RuJHA5Wl9Y1CMM7k2PoVLfKHJCH3_2xHxdH7TxzEArfzf1ChHkwHV8YnWoQiDc1KA0r-tUhitiaqZ10MsGbKQUeaz9GgVtW4r9t4Ai4WAXTCed-r8yuYWw-PV4DgyS9uDtNtTOKVP9Dv0-9Bn1c77alfFdpZQH78W9yby4JZcS7ZpK4fIox8VM_CWShSIKrilic7quNxPX-aDAqfUcwzBQHGEwBZR0W6O8hcjyN1OWbuoRwk5g_H5Y4yRYftC8Gf75Og7NeswCEmM-Xd39Jn5t2wVOeeU95f6G-amHZQgDxMkjySfxPobGDlzlukSVcsne4VIPUV8LHGVzeqda5WxBOJKKlFE0Z8P_6m7tgr2ilh0JzPy46-IXzTJqcBLyHriWwE-YnQVyzelUO7JooW5FoZkjIBy2YT6H6p6yJjZ6XMWX2PaR5U4vs-ZBdZR1_JAVLUHgXDtBStrcJ7f8KaAmH2prvystKYiaxK7tfQQzqFieJURaokdbQzMwB7WrYRbD2zRGg5rFSW4Ai5dxCPDOPuBVpJGywTUbpg3xWAwPP80EOHQrSb4g00iQplI-Px6t5jPTJVbeYg11aq2Tu0DFxilEo_6Fg8Ob2rpctVQbc75iyKtrdXgfNy4UCwSOZU0sUWu3I9q_FvU7Dy4t-
