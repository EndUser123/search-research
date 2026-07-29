---
source_id: "8e5a3217-acee-4675-acd3-fc7aabda49d5"
title: "Claude Code Hooks - all 23 explained and implemented : r/ClaudeAI - Reddit"
notebook_id: 29bbaa7b-965f-40b5-a404-76b4d2e7308c
url: https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/claude_code_hooks_all_23_explained_and_implemented/
type: web_page
exported: 2026-07-27
---

# Claude Code Hooks - all 23 explained and implemented : r/ClaudeAI - Reddit
Claude Code Hooks - all 23 explained and implemented : r/ClaudeAI

Skip to main content

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/claude_code_hooks_all_23_explained_and_implemented/#main-content

 Claude Code Hooks - all 23 explained and implemented : r/ClaudeAI

Open menu

Open navigation 

https://www.reddit.com/

Go to Reddit Home

 

r/ClaudeAI

TRENDING TODAY

Get App

Get the Reddit app

Log In

https://www.reddit.com/login/

Log in to Reddit

Expand user menu

Open settings menu

Skip to Navigation

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/claude_code_hooks_all_23_explained_and_implemented/#left-sidebar-container

 

Skip to Right Sidebar

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/claude_code_hooks_all_23_explained_and_implemented/#right-sidebar-container

Back

Go to ClaudeAI

https://www.reddit.com/r/ClaudeAI/

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

• 8d ago

shanraisshan

https://www.reddit.com/user/shanraisshan/

Locked post

Stickied post

Archived post

View post in other languages

Report

Claude Code Hooks - all 23 explained and implemented

 

 

Project is entirely built with Claude code. It implements all the 23 hooks, and I've also made a video which explains each use case of all the hooks. Do check it out. Hooks are one of the main features of Claude code which differentiate it from other CLI agents like Codex.

Repo link: 

https://github.com/shanraisshan/claude-code-hooks

https://github.com/shanraisshan/claude-code-hooks

Video link: 

https://www.youtube.com/watch?v=6_y3AtkgjqA

https://www.youtube.com/watch?v=6_y3AtkgjqA

Read more

253

· 27

Comments Section

dogazine4570

https://www.reddit.com/user/dogazine4570/

•

7d ago

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/comment/oba4rd1/

this is actually super helpful, I've been poking at hooks but only using like 2-3 of them. having all 23 implemented in one place makes it way easier to see patterns.

skimmed the repo and the pre/post tool ones especially clicked for me. nice job keeping it readable too, some CC demos get messy fast lol.

11

shanraisshan

https://www.reddit.com/user/shanraisshan/

OP

• 

7d ago

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/comment/oba9s3w/

thank you

1

BuyerOtherwise3077

https://www.reddit.com/user/BuyerOtherwise3077/

•

7d ago

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/comment/obbvx7a/

our 

CLAUDE.md

http://CLAUDE.md

 is 400+ lines and once context gets long enough the agent just stops reading the text instructions carefully. it pattern-matches the code instead. hooks actually fire regardless of context pressure so they catch the stuff that prose rules miss.

we started calling it "harness debt" because the instructions keep growing but compliance drops. v1.2 rules quietly stop matching v1.5 agent behavior and nobody notices until something breaks. ended up building a separate audit step just for that. PreToolUse hooks for the critical guardrails, text instructions for everything else.

5

shanraisshan

https://www.reddit.com/user/shanraisshan/

OP

• 

7d ago

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/comment/obcqa6o/

your 

claude.md

http://claude.md/

 should not exceed 200 lines. see 

https://github.com/shanraisshan/claude-code-best-practice?tab=readme-ov-file#-tips-and-tricks

https://github.com/shanraisshan/claude-code-best-practice?tab=readme-ov-file#-tips-and-tricks

6

Continue this thread

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/comment/obcqa6o/?force-legacy-sct=1

 

PlantainAmbitious3

https://www.reddit.com/user/PlantainAmbitious3/

•

7d ago

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/comment/obefxqb/

Honestly the pre-commit hook alone made this worth bookmarking. I had no idea you could set up automatic linting and test runs before Claude even tries to commit. Been manually running checks after every code change like some kind of caveman. Going to try wiring up the file-watch hooks next to auto-reload my dev server when Claude edits files.

5 

Heavy_Matter_689

https://www.reddit.com/user/Heavy_Matter_689/

•

7d ago

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/comment/obbectk/

Great question! The hooks are mostly useful for: (1) Security guardrails - you can intercept dangerous tool calls in PreToolUse and reject them; (2) Session logging - PostToolUse lets you log all tool calls to a file for debugging/replay; (3) Custom validation - you can validate tool inputs before execution; (4) Cost tracking - aggregate token usage across sessions. Basically they let you build custom workflows around Claude Code rather than just using it as a REPL.

2 

PlantainAmbitious3

https://www.reddit.com/user/PlantainAmbitious3/

•

7d ago

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/comment/oberg1u/

Honestly the pre-commit hook alone made this worth bookmarking. I had no idea you could set up automatic linting and test runs before Claude even tries to commit. Been manually running checks after every code change like some kind of caveman. Going to try wiring up the file-watch hooks next to auto-reload my dev server when Claude edits files.

2 

Madtown94

https://www.reddit.com/user/Madtown94/

•

7d ago

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/comment/obaf2si/

Why would I need to use these hooks? What benefit is there outside of just hearing Claude code talk?

1 

themflyingjaffacakes

https://www.reddit.com/user/themflyingjaffacakes/

•

7d ago

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/comment/obaiwd3/

For example you can link a hook to python script that can block tools or patterns in a deterministic way (not just claude.md giving "soft" instructions).

6

Continue this thread

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/comment/obaiwd3/?force-legacy-sct=1

enterprise128

https://www.reddit.com/user/enterprise128/

•

7d ago

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/comment/obbhf8e/

I use a hook that blocks agents from writing to the same file at the same time, and another that provides the correct schema whenever an agent attempts a database call.

2

Continue this thread

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/comment/obbhf8e/?force-legacy-sct=1

 

gritob

https://www.reddit.com/user/gritob/

•

7d ago

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/comment/obc48db/

I use a hook for „rm *“ and „az“ (azure) create/edit/delete to always ask for permission including a surprise pikachu ascii face. Helps me not accidentally yes something

2

Kramilot

https://www.reddit.com/user/Kramilot/

•

7d ago

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/comment/obaffeb/

Hooks are THE THING that breaks the paradigm. The ability to tell an LLM “stop, be better first” is what lets it move from helpful with language and synthesis to productive monster. I made a PowerPoint called “the death of Claude via web” a few months ago when I realized I could make actual hard gates instead of suggestions around the behavior I needed or needed not to happen. Great stuff!

0

dovyp

https://www.reddit.com/user/dovyp/

•

7d ago

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/comment/obauy9q/

Really solid resource for anyone getting into Claude Code. The hooks system is genuinely under-appreciated, most people treat Claude Code like a basic REPL but the hooks let you build some surprisingly robust workflows aroundit. Going to dig into your PreToolUse and PostToolUse implementations specifically.

0

BP041

https://www.reddit.com/user/BP041/

•

7d ago

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/comment/obb7pty/

This is a great reference -- the hooks system is genuinely underused. Most people who've been on Claude Code for a while haven't gone beyond PreToolUse for basic safety checks.

The ones I found most valuable in practice: PostToolUse for logging tool calls to a file for session replay/debugging, and Stop for enforcing a final memory-write step so context doesn't get lost between sessions. The interaction between hooks and multi-agent setups is especially interesting -- you can implement basic coordination signals between agents through hooks without touching prompts.

Did you find any edge cases where hook execution order caused unexpected behavior? I've noticed occasional issues when multiple tools fire in quick succession and hooks need to share state.

1

jonathanlaliberte

https://www.reddit.com/user/jonathanlaliberte/

•

7d ago

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/comment/obcem46/

good stuff man

1

shanraisshan

https://www.reddit.com/user/shanraisshan/

OP

• 

7d ago

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/comment/obcqvg0/

thank you

1

Kind-Resident

https://www.reddit.com/user/Kind-Resident/

•

7d ago

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/comment/obcmm46/

.

1 

PlantainAmbitious3

https://www.reddit.com/user/PlantainAmbitious3/

•

7d ago

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/comment/obeqwx9/

Honestly the pre-commit hook alone made this worth bookmarking. I had no idea you could set up automatic linting and test runs before Claude even tries to commit. Been manually running checks after every code change like some kind of caveman. Going to try wiring up the file-watch hooks next to auto-reload my dev server when Claude edits files.

1 

PlantainAmbitious3

https://www.reddit.com/user/PlantainAmbitious3/

•

7d ago

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/comment/obeqype/

Honestly the pre-commit hook alone made this worth bookmarking. I had no idea you could set up automatic linting and test runs before Claude even tries to commit. Been manually running checks after every code change like some kind of caveman. Going to try wiring up the file-watch hooks next to auto-reload my dev server when Claude edits files.

1 

Fun_Nebula_9682

https://www.reddit.com/user/Fun_Nebula_9682/

•

7d ago

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/comment/obf3542/

we're using hooks heavily for our vibeguard system — 7 layers of automated guards that fire on PreToolUse, PostToolUse etc. the ones i use most are PreToolUse for blocking dangerous file edits and PostToolUse for auto-running type checks after code changes. pro tip: SessionStart hook is great for injecting project context automatically so you don't have to repeat yourself every session

1

shanraisshan

https://www.reddit.com/user/shanraisshan/

OP

• 

7d ago

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/comment/obf7lc8/

you can find more hooks related tips here 

https://github.com/shanraisshan/claude-code-best-practice?tab=readme-ov-file#-tips-and-tricks

https://github.com/shanraisshan/claude-code-best-practice?tab=readme-ov-file#-tips-and-tricks

1

Related Answers Section

Related Answers

Overview of Claude code hooks and their uses

https://www.reddit.com/answers/9b92fcf8-4968-409e-b259-bb3fedad9509/?q=Overview+of+Claude+code+hooks+and+their+uses&source=PDP

Best practices for using ClaudeAI effectively

https://www.reddit.com/answers/99168c92-2897-4de4-91e6-b871caf3ef33/?q=Best+practices+for+using+ClaudeAI+effectively&source=PDP

Comparing ClaudeAI with other AI tools

https://www.reddit.com/answers/e80ab51c-171c-41a5-b3cc-78db0e36c249/?q=Comparing+ClaudeAI+with+other+AI+tools&source=PDP

Common pitfalls when using Claude Code

https://www.reddit.com/answers/86052676-9f92-4a15-8b87-a634fe9375de/?q=Common+pitfalls+when+using+Claude+Code&source=PDP

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

Claude Code HOOKS explained in 5 minutes

https://www.reddit.com/r/ClaudeAI/comments/1qwju77/claude_code_hooks_explained_in_5_minutes/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 2mo ago [

Claude Code HOOKS explained in 5 minutes

](https://www.reddit.com/r/ClaudeAI/comments/1qwju77/claude_code_hooks_explained_in_5_minutes/) 

 5:00 12 upvotes · 5 comments

Claude Code's Most Underrated Feature: Hooks (wrote a deep dive)

https://www.reddit.com/r/ClaudeAI/comments/1qlzxr1/claude_codes_most_underrated_feature_hooks_wrote/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 2mo ago [

Claude Code's Most Underrated Feature: Hooks (wrote a deep dive)

](https://www.reddit.com/r/ClaudeAI/comments/1qlzxr1/claude_codes_most_underrated_feature_hooks_wrote/) 234 upvotes · 40 comments

Claude Code now supports hooks

https://www.reddit.com/r/ClaudeAI/comments/1loodjn/claude_code_now_supports_hooks/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 9mo ago [

Claude Code now supports hooks

](https://www.reddit.com/r/ClaudeAI/comments/1loodjn/claude_code_now_supports_hooks/) 

 anthropic 482 upvotes · 152 comments

Two Claude Code features I slept on that completely changed how I use it: Stop Hooks + Memory files

https://www.reddit.com/r/ClaudeAI/comments/1rqxzlp/two_claude_code_features_i_slept_on_that/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 15d ago [

Two Claude Code features I slept on that completely changed how I use it: Stop Hooks + Memory files

](https://www.reddit.com/r/ClaudeAI/comments/1rqxzlp/two_claude_code_features_i_slept_on_that/) 516 upvotes · 102 comments

I built an interactive website that teaches Claude Code by letting you explore a simulated project in your browser

https://www.reddit.com/r/ClaudeAI/comments/1rmqk0x/i_built_an_interactive_website_that_teaches/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 20d ago [

I built an interactive website that teaches Claude Code by letting you explore a simulated project in your browser

](https://www.reddit.com/r/ClaudeAI/comments/1rmqk0x/i_built_an_interactive_website_that_teaches/) 

 1.1K upvotes · 59 comments

A thread for use cases of Claude Code

https://www.reddit.com/r/ClaudeAI/comments/1r6uaf9/a_thread_for_use_cases_of_claude_code/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 1mo ago [

A thread for use cases of Claude Code

](https://www.reddit.com/r/ClaudeAI/comments/1r6uaf9/a_thread_for_use_cases_of_claude_code/) 41 upvotes · 49 comments

Explaining Claude's features such as Hooks, Subagents, Skills, Plugins & Marketplaces

https://www.reddit.com/r/ClaudeAI/comments/1qm721h/explaining_claudes_features_such_as_hooks/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 2mo ago [

Explaining Claude's features such as Hooks, Subagents, Skills, Plugins & Marketplaces

](https://www.reddit.com/r/ClaudeAI/comments/1qm721h/explaining_claudes_features_such_as_hooks/) 10 upvotes · 3 comments

Claude Code hooks confuse everyone at first

https://www.reddit.com/r/ClaudeCode/comments/1p48uil/claude_code_hooks_confuse_everyone_at_first/

 

r/ClaudeCode

https://www.reddit.com/r/ClaudeCode/

 • 4mo ago [

Claude Code hooks confuse everyone at first

](https://www.reddit.com/r/ClaudeCode/comments/1p48uil/claude_code_hooks_confuse_everyone_at_first/) 

 140 upvotes · 14 comments

Claude code favorite hooks

https://www.reddit.com/r/ClaudeCode/comments/1m865de/claude_code_favorite_hooks/

 

r/ClaudeCode

https://www.reddit.com/r/ClaudeCode/

 • 8mo ago [

Claude code favorite hooks

](https://www.reddit.com/r/ClaudeCode/comments/1m865de/claude_code_favorite_hooks/) 15 upvotes · 13 comments

Claude Code's Most Underrated Feature: Hooks - wrote a complete guide

https://www.reddit.com/r/ClaudeCode/comments/1qlzzzf/claude_codes_most_underrated_feature_hooks_wrote/

 

r/ClaudeCode

https://www.reddit.com/r/ClaudeCode/

 • 2mo ago [

Claude Code's Most Underrated Feature: Hooks - wrote a complete guide

](https://www.reddit.com/r/ClaudeCode/comments/1qlzzzf/claude_codes_most_underrated_feature_hooks_wrote/) 173 upvotes · 25 comments

How to make Claude Code write ACTUALLY clean code (pre-tool-use hooks FTW)

https://www.reddit.com/r/ClaudeCode/comments/1o3czhw/how_to_make_claude_code_write_actually_clean_code/

 

r/ClaudeCode

https://www.reddit.com/r/ClaudeCode/

 • 6mo ago [

How to make Claude Code write ACTUALLY clean code (pre-tool-use hooks FTW)

](https://www.reddit.com/r/ClaudeCode/comments/1o3czhw/how_to_make_claude_code_write_actually_clean_code/) 5 upvotes · 8 comments

Claude Code - Changelog RSS feed

https://www.reddit.com/r/ClaudeAI/comments/1povzl6/claude_code_changelog_rss_feed/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 3mo ago [

Claude Code - Changelog RSS feed

](https://www.reddit.com/r/ClaudeAI/comments/1povzl6/claude_code_changelog_rss_feed/) 5 upvotes · 5 comments

Claude code creator shares update of v2.1.9 and about hooks option

https://www.reddit.com/r/ClaudeAI/comments/1qmuu4e/claude_code_creator_shares_update_of_v219_and/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 2mo ago [

Claude code creator shares update of v2.1.9 and about hooks option

](https://www.reddit.com/r/ClaudeAI/comments/1qmuu4e/claude_code_creator_shares_update_of_v219_and/) 

 4 115 upvotes · 10 comments

Claude Code Use Cases - What I Actually Do

https://www.reddit.com/r/ClaudeCode/comments/1rmd5d8/claude_code_use_cases_what_i_actually_do/

 

r/ClaudeCode

https://www.reddit.com/r/ClaudeCode/

 • 20d ago [

Claude Code Use Cases - What I Actually Do

](https://www.reddit.com/r/ClaudeCode/comments/1rmd5d8/claude_code_use_cases_what_i_actually_do/) 11 upvotes · 3 comments

Discovered Claude Code recently…

https://www.reddit.com/r/ClaudeAI/comments/1qrour7/discovered_claude_code_recently/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 2mo ago [

Discovered Claude Code recently…

](https://www.reddit.com/r/ClaudeAI/comments/1qrour7/discovered_claude_code_recently/) 

 121 upvotes · 22 comments

Claude code for reverse engineering

https://www.reddit.com/r/ClaudeAI/comments/1rvd6x0/claude_code_for_reverse_engineering/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 10d ago [

Claude code for reverse engineering

](https://www.reddit.com/r/ClaudeAI/comments/1rvd6x0/claude_code_for_reverse_engineering/) 

 13 upvotes · 6 comments

What are some good use cases for Claude Code for non-developers?

https://www.reddit.com/r/ClaudeAI/comments/1rnc5d8/what_are_some_good_use_cases_for_claude_code_for/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 19d ago [

What are some good use cases for Claude Code for non-developers?

](https://www.reddit.com/r/ClaudeAI/comments/1rnc5d8/what_are_some_good_use_cases_for_claude_code_for/) 6 upvotes · 11 comments

I built a Claude Code hook that stops it from re-reading files it already has in context

https://www.reddit.com/r/ClaudeAI/comments/1rnjf5e/i_built_a_claude_code_hook_that_stops_it_from/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 19d ago [

I built a Claude Code hook that stops it from re-reading files it already has in context

](https://www.reddit.com/r/ClaudeAI/comments/1rnjf5e/i_built_a_claude_code_hook_that_stops_it_from/) 5 upvotes · 9 comments

After 10 years as an engineer, I felt like a zombie. Claude Code actually made me love building again.

https://www.reddit.com/r/ClaudeCode/comments/1rxvn16/after_10_years_as_an_engineer_i_felt_like_a/

 

r/ClaudeCode

https://www.reddit.com/r/ClaudeCode/

 • 7d ago [

After 10 years as an engineer, I felt like a zombie. Claude Code actually made me love building again.

](https://www.reddit.com/r/ClaudeCode/comments/1rxvn16/after_10_years_as_an_engineer_i_felt_like_a/) 140 upvotes · 38 comments

Is Claude Code the best AI coding tool?

https://www.reddit.com/r/ClaudeAI/comments/1ruciiq/is_claude_code_the_best_ai_coding_tool/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 11d ago [

Is Claude Code the best AI coding tool?

](https://www.reddit.com/r/ClaudeAI/comments/1ruciiq/is_claude_code_the_best_ai_coding_tool/) 12 upvotes · 22 comments

Can someone with zero coding experience actually use Claude Code (or similar) to build stuff now?

https://www.reddit.com/r/ClaudeAI/comments/1s0krn2/can_someone_with_zero_coding_experience_actually/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 4d ago [

Can someone with zero coding experience actually use Claude Code (or similar) to build stuff now?

](https://www.reddit.com/r/ClaudeAI/comments/1s0krn2/can_someone_with_zero_coding_experience_actually/) 138 upvotes · 242 comments

How to setup Claude Code for winning hackathons

https://www.reddit.com/r/ClaudeAI/comments/1rxxub2/how_to_setup_claude_code_for_winning_hackathons/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 7d ago [

How to setup Claude Code for winning hackathons

](https://www.reddit.com/r/ClaudeAI/comments/1rxxub2/how_to_setup_claude_code_for_winning_hackathons/) 3 upvotes · 4 comments

3 months in Claude Code changed how I build things. now I'm trying to make it accessible to everyone.

https://www.reddit.com/r/ClaudeAI/comments/1rmdeli/3_months_in_claude_code_changed_how_i_build/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 • 20d ago [

3 months in Claude Code changed how I build things. now I'm trying to make it accessible to everyone.

](https://www.reddit.com/r/ClaudeAI/comments/1rmdeli/3_months_in_claude_code_changed_how_i_build/) 32 upvotes · 18 comments

Learning projects in the age of Claude Code

https://www.reddit.com/r/ClaudeCode/comments/1rz11ct/learning_projects_in_the_age_of_claude_code/

 

r/ClaudeCode

https://www.reddit.com/r/ClaudeCode/

 • 6d ago [

Learning projects in the age of Claude Code

](https://www.reddit.com/r/ClaudeCode/comments/1rz11ct/learning_projects_in_the_age_of_claude_code/) 4 upvotes · 12 comments

View Post in

繁體中文

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/claude_code_hooks_all_23_explained_and_implemented/?tl=zh-hant

Português (Brasil)

https://www.reddit.com/r/ClaudeAI/comments/1rxu41b/claude_code_hooks_all_23_explained_and_implemented/?tl=pt-br

Community Info Section

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 

 

Check Claude service status.

http://status.claude.com/

Join

ClaudeAI

This is a Claude and Claude Code discussion subreddit to help you make a fully informed decision about using Claude and Claude Code to best effect for your own purposes. ¹⌉ Anthropic does not control or operate this subreddit or endorse views expressed here. ²⌉ If your problem requires Anthropic's help, visit https://support.anthropic.com/ This subreddit is not the right place to fix your account issues. ³⌉ For more help, check the resources below. ⁴⌉ Please read the rules before posting.

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

 

0cAFcWeA61zij-lUMx81SlTeNSTzCveM3QlqjqctxruV4-dwfdszTe-zOjtu1jHr8BqsvXP76SGxUg3sIcTjee8zGFzCHiLUtu-eycBSOpth4DZWS43eG53lYo3h4ONKn3-8nX8B3C8opR8GO9hE6-vZ8EE0sN4eF2lCxlQ2dzzoohFgWp4CYsTBb70NM_tXT-DYPxPgP0SRmeuBTv27KN1uZUrkWnu79pXqyBrCc5NQjNTboiCZYlY8L4_jXv4D8liBTOuQiLwKHPz9IaoipVnSjxsR2P_ECvS7L881YqfLNVIssGiPmqN20VaEdDcZ2362i6noXB5PLxNTelCPoiWEVnsYutC-kM_b-JVbzcWvMUuW3aczYiPmPsMCmXo_j7ifK8Q22dIA4-VCYJSDaWVYbfXo5u2t7u6Ma7dbNoznyysXy7xUzzSzJqkitij9Ku3bzGp-jiM3XS-zDAnq9Vx2mmxpC_07rgKLk4sJY9FUX1ObJZYfgwvUxyYruVvaTt7VAFOA9UqlStPi7oK1BlHNi0PQ7A08bJJ-0uIgUJytvlDJ1wk9rWEWkm8AzKHgjRG5tT9rOe1FlLIvN1T3SVvHMYowF1pxjal673-hislZIajuOBvvYBhALM0S3AePXhgO101ToUaYg26LnHrg3c0iCrlt74wTegzcHwgzSpCBHOxNhgcIvYqM7-tPEPk17LsFR-IpLyJlINJYbEodckVmhta5aj_-T5hVDVRgDkoUrMy3k3iypm_CzqslocKg0IoV2f9DKAZ_xj4QCM2zNcbA44yo--Ghyij1FWfDWgkXbiCu7OMS-Oj9mPwSjpmY3UyNuM7Pm7_NV-U7ezOmMWQckM-xfyao3__8kz-v6s4-pftx1wNAdF5OHCdpVH_N9SocYq6Qq0mFRUCT2hCMepNq8Ea-24udQle6Lrm-vREDL6sikSKVIHnErSq1VbK-KGt_8vU8rg51pXEvi4hZBSUEQKLuscvEbgoPT_k6gAMJTeQ9xF1PYjAJ3VvZ97A9dChUINv7r8mnXR-HthYHnJYPm3IytN3hxheq-UYKZKpw3U_npdVmg5HusD27ySvg46I6Xwbv4QSLgMjQ7gur8T9AJcx-cNZMQeFElrFesKHFXr1opiEkgWYyzzx4ddrtq9_XGgrLAHObsWu2B2RadR5rSRCZXKzlCM9C5VrqulA7dkrEM9e0V5QL3tgnlGYPJh7A_UD8tUKIW8GJ2VP3Zg8qlk1P10OqhU4e0GyL303RYZwQ3aGlXhrkHf7fDFYb4jWFkHE6kAv3p2TVmqELXxUk69xTCjvJPb5AISWvDTWbX5TLK5HR02Q9KwfQgCaK4qN7KixvP5HCjeKeaM2d0lsFnddGeUuuy2Qo3wjM6wz_rzkGR8qbQUPkjvH3lVa94EvcZLOpUfv-6urnVRWEDdbg5JIKftnfJenVu8W3blJxbdKlAl0erhO2uAL3pLVrLzDuCXKRbBVJCB1PQXzV7zLXBZYLOlDVu3uNoa4vHfPvORpiM8q1P3_rgUWTlxQRovl_9pkSPfWHlRKmnVVrpOHP7Crn6m2Z7vjmSyH7dUACQTca0_gjsmX4zD4YtcieJpsybE3mt14NUmYAClEkmAE983MRS98QDVWgW6wDw-tKYEo7bAT-wmWlYUB-9FP8cOKSgT5euVwA9wjD2ds9-V0oYk6NkNUWJkCtD12e4OQEMROdMMZEG-1y6_Wwu4PUz1N5NkZ58svGddoTxj5yn1vRJrferAVqji76CKochZ13bNQoOIzZlK49KtBl6u5Tnon5HjWFPfzHik5x5h5B-nr0u__9uqJGmj9k2w3zbkbBgm_jJs4m_dThsM9sJRXGRjefdZyj6FVF-YL6KuCy1xBykZ-_es8WPNtjdA-AJw0VzFJfh0FZDMCKbla1slt-gI3YyxcwUn10cAw8qqBNImfbK1YXpwGHjYszpIXRf9vNiU9-0L0P4oI_gIBho6r-QMQbPbz8uloZMbm8CiBhwnAdn6QVRwAPNUDQC3aFAl9sv0bIQS2Miggu1ldwig4QVnpe69nZcBIZzC5s8yYAROIFQ6rZ8VFbMNon7hgUTSMCRhTR_fQXQixjWSavlZEbosALLhA_AMULTGPJPjlOWxUDOQGupYquEEXvdgIp2Sk4I0nykFE8S5w5P-Hb91pTd1mrkburOiB4Tz
