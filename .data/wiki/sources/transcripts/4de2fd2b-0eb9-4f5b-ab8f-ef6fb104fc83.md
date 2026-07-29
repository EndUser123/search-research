---
source_id: "4de2fd2b-0eb9-4f5b-ab8f-ef6fb104fc83"
title: "I built a pre-commit linter that catches AI-generated code patterns : r/Python - Reddit"
notebook_id: e83b6a68-fedc-4757-b492-3360ae8377a2
url: https://www.reddit.com/r/Python/comments/1rlho78/i_built_a_precommit_linter_that_catches/
type: web_page
exported: 2026-07-27
---

# I built a pre-commit linter that catches AI-generated code patterns : r/Python - Reddit
I built a pre-commit linter that catches AI-generated code patterns : r/Python

Skip to main content

https://www.reddit.com/r/Python/comments/1rlho78/i_built_a_precommit_linter_that_catches/#main-content

 I built a pre-commit linter that catches AI-generated code patterns : r/Python

Open menu

Open navigation 

https://www.reddit.com/

Go to Reddit Home

Ask

https://www.reddit.com/answers/

Find anything

Sign Up

https://www.reddit.com/register/

Sign up for Reddit

Log In

https://www.reddit.com/login/

Log in to Reddit

Expand user menu

Open settings menu

Skip to Sign up

https://www.reddit.com/r/Python/comments/1rlho78/i_built_a_precommit_linter_that_catches/#left-sidebar-container

 

Skip to Right Sidebar

https://www.reddit.com/r/Python/comments/1rlho78/i_built_a_precommit_linter_that_catches/#right-sidebar-container

Back

Go to Python

https://www.reddit.com/r/Python/

r/Python

https://www.reddit.com/r/Python/

â€¢ 4mo ago

mmartoccia

https://www.reddit.com/user/mmartoccia/

Locked post

Stickied post

Archived post

Report

I built a pre-commit linter that catches AI-generated code patterns

Showcase

https://www.reddit.com/r/Python/?f=flair_name%3A%22Showcase%22

What My Project Does

grain

 is a pre-commit linter that catches code patterns commonly produced by AI code generators. It runs before your commit and flags things like:

NAKED_EXCEPT

 -- bare 

except: pass

 that silently swallows errors (156 instances in my own codebase)

HEDGE_WORD

 -- docstrings full of "robust", "comprehensive", "seamlessly"

ECHO_COMMENT

 -- comments that restate what the code already says

DOCSTRING_ECHO

 -- docstrings that expand the function name into a sentence and add nothing

I ran it on my own AI-assisted codebase and found 184 violations across 72 files. The dominant pattern was exception handlers that caught hardware failures, logged them, and moved on -- meaning the runtime had no idea sensors stopped working.

Target Audience

Anyone using AI code generation (Copilot, Claude, ChatGPT, etc.) in Python projects and wants to catch the quality patterns that slip through existing linters. This is not a toy -- I built it because I needed it for a production hardware abstraction layer where autonomous agents are regular contributors.

Comparison

Existing linters (pylint, ruff, flake8) catch syntax, style, and type issues. They don't catch AI-specific patterns like docstring padding, hedge words, or the tendency of AI generators to wrap everything in try/except and swallow the error. grain fills that gap. It's complementary to your existing linter, not a replacement.

Install

pip install grain-lint


Pre-commit compatible. Configurable via 

.grain.toml

 . Python only (for now).

Source:

 

github.com/mmartoccia/grain

https://github.com/mmartoccia/grain

Happy to answer questions about the rules, false positive rates, or how it compares to semgrep custom rules.

Upvote 71 Downvote 62 Go to comments

Share

Sort by: Best

Open comment sort options

Best

Top

New

Controversial

Old

Q&A

Search Comments Expand comment search

Cancel

Comments Section

another24tiger

https://www.reddit.com/user/another24tiger/

â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8s0719/

Youâ€™re telling me you slop-coded a slop code detectorâ€¦

Upvote 244 Downvote Reply Award

Share

Report

Award

Share

GraphicH

https://www.reddit.com/user/GraphicH/

â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8s32yl/

Okay, I know we're all on the AI hate train with a lot of good reasons. You have total neophytes vibe-coding thousands of lines and going "take my pr" or "use my library" that Claude/Gemini/ChatGPT/Grok performed verbal fellatio on me for, stating its better than everything else out there right now. Yeah these tools now allow morons to write bad code at scale; instead of just giving up after a syntax error on hello world.

That said, you can still use them to do and produce good works -- it is possible and something I feel like we can't just discount out of hand. Is this one of those works? I don't know for sure; I just do know there is an attitude of being dismissive by default and it's really going to screw a lot of people.

Upvote 61 Downvote Reply Award

Share

Report

Award

Share 

mmartoccia

https://www.reddit.com/user/mmartoccia/

OP â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8s7im1/

Yeah that's basically where I landed too. The tools aren't going away, and "just don't use them" isn't realistic advice for most teams. So the question becomes how do you keep the quality bar up when half your commits come from a model that thinks every function needs a try/except and a docstring that says "This function does the thing."

grain is my answer to that specific problem. It's not anti-AI, it's anti-autopilot. 

axonxorz

https://www.reddit.com/user/axonxorz/

â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8ytx5a/

Is this one of those works? I don't know for sure;

The problem is that the LLM convinces the author of this wholeheartedly, allowing them to export the responsibility of determining that very fact to the rest of us.

Sure, every project posted needs that same consideration, but when the author has had their humility exoriated by matrix math, people aren't as willing to give the benefit of the doubt.

More replies

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8s32yl/?force-legacy-sct=1

 

mmartoccia

https://www.reddit.com/user/mmartoccia/

OP â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8s1eym/

lol yeah pretty much. That's literally why it exists though. My codebase was a mess, I got tired of catching the same garbage patterns in review, so I automated it. Now it yells at me before I commit instead of after.

Upvote 31 Downvote Reply Award

Share

Report

Award

Share 

gdchinacat

https://www.reddit.com/user/gdchinacat/

â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8sheq4/

I doubt this will make your code less of a mess. AI slop is inherently messy.

21 more replies

21 more replies

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8sheq4/?force-legacy-sct=1

More replies

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8s1eym/?force-legacy-sct=1

More replies

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8s0719/?force-legacy-sct=1

marr75

https://www.reddit.com/user/marr75/

â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8sag6f/

I said this as a comment

https://www.reddit.com/r/Python/s/J2pVMHNF4o

 to a nearly identical project, but this is catching the smaller less impactful slop errors AI makes (that it just happens to share with human junior coders). The bigger more costly errors are all about verbosity, fragility, and incorrectness based on gold-plating, solving the wrong problem, no real architecture/design, choosing the wrong pattern, and sycophancy.

If someone figures out how to catch those...

Upvote 22 Downvote Reply Award

Share

Report

Award

Share 

KerPop42

https://www.reddit.com/user/KerPop42/

â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8sc75l/

xkcd 810 reference?

https://xkcd.com/810/

https://xkcd.com/810/

Upvote 10 Downvote Reply Award

Share

Report

Award

Share

3 more replies

3 more replies

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8sc75l/?force-legacy-sct=1

 

mmartoccia

https://www.reddit.com/user/mmartoccia/

OP â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8schl1/

You're right, and I'd frame it as two layers. Layer 1 is the stuff grain catches now -- the surface patterns that are easy to detect statically. Layer 2 is what you're describing -- wrong abstractions, gold-plating, solving problems that don't exist. That's harder because it requires understanding intent, not just syntax. I don't think a linter catches that. That's still a human review problem, or maybe eventually an LLM-powered review that understands the project's architecture. grain is just layer 1.

Upvote 2 Downvote Reply Award

Share

Report

Award

Share

More replies

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8sag6f/?force-legacy-sct=1

rabornkraken

https://www.reddit.com/user/rabornkraken/

â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8s700b/

The NAKED_EXCEPT rule alone makes this worth using. I have been bitten by this exact pattern where an AI assistant wrapped sensor reads in try/except pass and failures went completely silent for days. The hedge word detection is a nice touch too - I have started noticing how much padding AI-generated docstrings add. Do you have any plans to support custom rule definitions or is the ruleset fixed?

Upvote 7 Downvote Reply Award

Share

Report

Award

Share

wRAR_

https://www.reddit.com/user/wRAR_/

â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8s7u76/

The NAKED_EXCEPT rule alone makes this worth using.

Consider starting to use ruff.

Upvote 25 Downvote Reply Award

Share

Report

Award

Share 

mmartoccia

https://www.reddit.com/user/mmartoccia/

OP â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8scobf/

ruff catches bare except (no exception type). grain catches the next layer -- except SomeError: pass or except SomeError: logger.debug("failed") where you named the exception but still swallowed it. ruff sees the first one as fine because you specified a type. grain doesn't, because the error still disappears.

Upvote 5 Downvote Reply Award

Share

Report

Award

Share

1 more reply

1 more reply

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8scobf/?force-legacy-sct=1

 

spenpal_dev

https://www.reddit.com/user/spenpal_dev/

â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8scsos/

I was going to comment this exact same thing.

Upvote 1 Downvote Reply Award

Share

Report

Award

Share

More replies

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8s7u76/?force-legacy-sct=1

headykruger

https://www.reddit.com/user/headykruger/

â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8s9ozd/

Isnâ€™t that just a standard linting rule?

Upvote 8 Downvote Reply Award

Share

Report

Award

Share 

mmartoccia

https://www.reddit.com/user/mmartoccia/

OP â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8sdi61/

Bare except yeah, ruff catches that. But most AI-generated code specifies the exception type and then does nothing with it. That passes ruff fine. grain catches that pattern.

Upvote 5 Downvote Reply Award

Share

Report

Award

Share

1 more reply

1 more reply

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8sdi61/?force-legacy-sct=1

1 more reply

1 more reply

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8s9ozd/?force-legacy-sct=1

pip_install_account

https://www.reddit.com/user/pip_install_account/

â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8sa6mj/

 â€¢ Edited 4mo ago

Try searching this against your codebase. I wrote it one day when I was sick of this behaviour from ai tools, and I'm using it almost every day now.

^\s*except\s+[A-Za-z0-9_,\s()]+:\n(?:(?![ \t]

raise\b).+\n)+\s

$

Upvote 3 Downvote Reply Award

Share

Report

Award

Share 

mmartoccia

https://www.reddit.com/user/mmartoccia/

OP â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8scy7l/

Nice regex. grain's NAKED_EXCEPT rule does something similar but also catches the cases where there's a logger.debug or a pass inside the handler -- basically any except block that doesn't re-raise or do meaningful recovery. The regex approach is solid for a quick grep though.

Upvote 3 Downvote Reply Award

Share

Report

Award

Share

1 more reply

1 more reply

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8scy7l/?force-legacy-sct=1

More replies

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8sa6mj/?force-legacy-sct=1

 

mmartoccia

https://www.reddit.com/user/mmartoccia/

OP â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8sk2xo/

Custom rules just shipped in v0.2.0. You can define your own patterns in .grain.toml now: 

[[grain.custom_rules]]

 

name = "PRINT_DEBUG"

 

pattern = '^\s*print\s*\('

 

files = "*.py"

 

message = "print() call -- use logging"

 

severity = "warn"

pip install --upgrade grain-lint to get it.

Upvote 2 Downvote Reply Award

Share

Report

Award

Share 

mmartoccia

https://www.reddit.com/user/mmartoccia/

OP â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8s81cq/

Yep, that's the one that started this whole thing for me. 156 of them across a hardware abstraction layer, total silence when sensors dropped.

Custom rules are on the roadmap. Right now you can disable rules or adjust severity in .grain.toml, but full "bring your own pattern" isn't there yet. If you're seeing patterns that aren't covered, open an issue -- that's how the current ruleset got built.

Upvote 1 Downvote Reply Award

Share

Report

Award

Share

More replies

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8s700b/?force-legacy-sct=1

 

eirikirs

https://www.reddit.com/user/eirikirs/

â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8tnx9c/

This is pretty much an AI-slop sanitiser, that only targets symptoms, not the true issues with low cohesion and tight coupling. Besides, I doubt your comment echo rule would even be usable, given the current limitations of AIs semantic analysis.

Upvote 9 Downvote Reply Award

Share

Report

Award

Share

ePaint

https://www.reddit.com/user/ePaint/

â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8tzn2i/

You can setup a skill to avoid these. I have a code-like-me that specifically indicates not to do any of these.

I still review every line of code produced by agents, but the skill alone works 99% of the time.

Upvote 3 Downvote Reply Award

Share

Report

Award

Share 

maafy6

https://www.reddit.com/user/maafy6/

â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8usjos/

Donâ€™t forget inconvenience functionsâ€”where it defines a function with some args and the body is a single line calling another function with those exact same arguments with no actual new logic.

Upvote 2 Downvote Reply Award

Share

Report

Award

Share

MisguidedFacts

https://www.reddit.com/user/MisguidedFacts/

â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8xddsb/

It loves ternaries, even for stuff that literally spits out a bool, it'll do:

some_flag = True if some_condition else False


Or even more annoying, the overly "defensive" ternary when you could just provide a default:

some_val = getattr(myobj, 'some_attr') if hasattr(myobj, 'some_attr') else 'some_default'


Upvote 2 Downvote Reply Award

Share

Report

Award

Share

wRAR_

https://www.reddit.com/user/wRAR_/

â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8y79el/

(for the record, ruff flags both of these lines)

Upvote 2 Downvote Reply Award

Share

Report

Award

Share

MisguidedFacts

https://www.reddit.com/user/MisguidedFacts/

â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8z5j03/

Nice!

My comment wasnâ€™t meant to be an endorsement to use this persons tool, I have eyeballs, itâ€™s pretty obvious when someone hasnâ€™t gone back over the code it generated and cleaned things up.

Maybe itâ€™s time to switch off of black (or at least see if thereâ€™s a configuration or rule we can change to also catch these) because Iâ€™m tired of seeing it in MRs.

Upvote 2 Downvote Reply Award

Share

Report

Award

Share

More replies

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8y79el/?force-legacy-sct=1

More replies

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8xddsb/?force-legacy-sct=1

WiseDog7958

https://www.reddit.com/user/WiseDog7958/

â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8x5224/

I have actually seen that kind of pattern too when looking through repos with a lot of AI-generated code.

Lots of doc-strings that sound confident but do not really explain anything.

Curious if you have noticed it more in certain areas like API wrappers, config modules, etc or if itâ€™s just everywhere.

Upvote 1 Downvote Reply Award

Share

Report

Award

Share 

Numerous_Draft_7852

https://www.reddit.com/user/Numerous_Draft_7852/

â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8yju2s/

Dude you are a legend

Upvote 1 Downvote Reply Award

Share

Report

Award

Share

mfaine

https://www.reddit.com/user/mfaine/

â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8ykxqp/

I love the idea. Does it have a 

- - fix

 option? :)

Upvote 1 Downvote Reply Award

Share

Report

Award

Share

mfaine

https://www.reddit.com/user/mfaine/

â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8ymrn2/

It's probably possible to craft just the right Instructions.md file to do these kinds of things. Use something like: 

https://github.com/github/awesome-copilot/blob/main/docs/README.instructions.md

https://github.com/github/awesome-copilot/blob/main/docs/README.instructions.md

The add to it it if it's missing anything.

Upvote 1 Downvote Reply Award

Share

Report

Award

Share

More replies

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8ykxqp/?force-legacy-sct=1

 

[deleted]

â€¢ 4mo ago

Comment deleted by user 

mmartoccia

https://www.reddit.com/user/mmartoccia/

OP â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8sgtwp/

TAG_COMMENT just shipped in v0.1.3. It's opt-in -- add it to warn_only in your .grain.toml and every comment without a structured tag (TODO, BUG, NOTE, etc.) gets flagged. Section headers and dividers are skipped automatically.

https://github.com/mmartoccia/grain/commit/5cbb66e

https://github.com/mmartoccia/grain/commit/5cbb66e

CONST_SETTING is on the list for the next one. Open an issue if you want to spec it out. 

mmartoccia

https://www.reddit.com/user/mmartoccia/

OP â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8sjzgm/

 â€¢ Edited 4mo ago

Update -- v0.2.0 just shipped with custom rule support. Your CONST_SETTING idea is now a one-liner: 

[[grain.custom_rules]]

 

name = "CONST_SETTING"

 

pattern = '^\s*[A-Z_]{2,}\s*=\s*\d+'

 

files = "*.py"

 

message = "top-level constant -- use config or env vars"

 

severity = "warn"

No built-in needed. Define whatever patterns you want. 

mmartoccia

https://www.reddit.com/user/mmartoccia/

OP â€¢ 

4mo ago

https://www.reddit.com/r/Python/comments/1rlho78/comment/o8scs8b/

Both good ideas. TAG_COMMENT is interesting -- forcing structure on comments instead of banning them. I could see that as an optional strict mode. CONST_SETTING would need some project-level config to define what's allowed, but it's doable. Open issues for both if you want -- I'll tag them for the next release.

View more comments

People also ask about section

People also ask about

Overview of pre-commit linters for Python

https://www.reddit.com/answers/396c47ad-2bb7-4ec8-ac32-3daf8c4427bc/?q=Overview+of+pre-commit+linters+for+Python&source=PDP

Common linting errors in Python

https://www.reddit.com/answers/2cb94a15-aa66-4bd9-a0a3-9c29ada2564c/?q=Common+linting+errors+in+Python&source=PDP

Best practices for code linting

https://www.reddit.com/answers/1809d3eb-1257-4844-9a44-a6fba5eca7d7/?q=Best+practices+for+code+linting&source=PDP

AI code linting techniques

https://www.reddit.com/answers/d95fe207-faf1-40b9-8b0c-fba5154a5e5d/?q=AI+code+linting+techniques&source=PDP

Meaning of linter in programming

https://www.reddit.com/answers/3f1b5df9-c61f-4934-a101-6d0e0f31543b/?q=Meaning+of+linter+in+programming&source=PDP

More posts you may like

Related posts

I built a linter specifically for AI-generated code

https://www.reddit.com/r/Python/comments/1pf7vj8/i_built_a_linter_specifically_for_aigenerated_code/

 

r/Python

https://www.reddit.com/r/Python/

 â€¢ 7mo ago [

I built a linter specifically for AI-generated code

](https://www.reddit.com/r/Python/comments/1pf7vj8/i_built_a_linter_specifically_for_aigenerated_code/) 7 comments

Linus on people who correlate developer impact with how many lines of code they've contributed to the project

https://www.reddit.com/r/linusrants/comments/1pbgbjl/linus_on_people_who_correlate_developer_impact/

 

r/linusrants

https://www.reddit.com/r/linusrants/

 â€¢ 7mo ago [

Linus on people who correlate developer impact with how many lines of code they've contributed to the project

](https://www.reddit.com/r/linusrants/comments/1pbgbjl/linus_on_people_who_correlate_developer_impact/) 

 0:24 1.5K upvotes Â· 62 comments

What's the best AI code review tool?

https://www.reddit.com/r/codereview/comments/1pqgmv4/whats_the_best_ai_code_review_tool/

 

r/codereview

https://www.reddit.com/r/codereview/

 â€¢ 7mo ago [

What's the best AI code review tool?

](https://www.reddit.com/r/codereview/comments/1pqgmv4/whats_the_best_ai_code_review_tool/) 2 upvotes Â· 51 comments

What do you think about this AI commit tool?

https://www.reddit.com/r/webdev/comments/18i0csc/what_do_you_think_about_this_ai_commit_tool/

 

r/webdev

https://www.reddit.com/r/webdev/

 â€¢ 3y ago [

What do you think about this AI commit tool?

](https://www.reddit.com/r/webdev/comments/18i0csc/what_do_you_think_about_this_ai_commit_tool/) 

 2 11 comments

How do you keep your code formatted and linted these days?

https://www.reddit.com/r/java/comments/1uefe66/how_do_you_keep_your_code_formatted_and_linted/

 

r/java

https://www.reddit.com/r/java/

 â€¢ 17d ago [

How do you keep your code formatted and linted these days?

](https://www.reddit.com/r/java/comments/1uefe66/how_do_you_keep_your_code_formatted_and_linted/) 19 upvotes Â· 47 comments

Suggested tactics for rolling out adoption of a linter?

https://www.reddit.com/r/ExperiencedDevs/comments/1crf0qu/suggested_tactics_for_rolling_out_adoption_of_a/

 

r/ExperiencedDevs

https://www.reddit.com/r/ExperiencedDevs/

 â€¢ 2y ago [

Suggested tactics for rolling out adoption of a linter?

](https://www.reddit.com/r/ExperiencedDevs/comments/1crf0qu/suggested_tactics_for_rolling_out_adoption_of_a/) 39 upvotes Â· 43 comments

linusInventedVibeCodingBeforeVibecodingWasAConcept

https://www.reddit.com/r/ProgrammerHumor/comments/1svkvtu/linusinventedvibecodingbeforevibecodingwasaconcept/

 

r/ProgrammerHumor

https://www.reddit.com/r/ProgrammerHumor/

 â€¢ 3mo ago [

linusInventedVibeCodingBeforeVibecodingWasAConcept

](https://www.reddit.com/r/ProgrammerHumor/comments/1svkvtu/linusinventedvibecodingbeforevibecodingwasaconcept/) 

 3.8K upvotes Â· 38 comments

I built a pre-commit linter that catches AI-generated code patterns before they land

https://www.reddit.com/r/GithubCopilot/comments/1rlqdat/i_built_a_precommit_linter_that_catches/

 

r/GithubCopilot

https://www.reddit.com/r/GithubCopilot/

 â€¢ 4mo ago [

I built a pre-commit linter that catches AI-generated code patterns before they land

](https://www.reddit.com/r/GithubCopilot/comments/1rlqdat/i_built_a_precommit_linter_that_catches/) 1 upvote Â· 3 comments

Post-Literate Programming

https://www.reddit.com/r/BetterOffline/comments/1us3pry/postliterate_programming/

 

r/BetterOffline

https://www.reddit.com/r/BetterOffline/

 â€¢ 1d ago [

Post-Literate Programming

](https://www.reddit.com/r/BetterOffline/comments/1us3pry/postliterate_programming/) 167 upvotes Â· 64 comments

I built a self-learning plugin for Claude Code that auto-generates specialized agents from usage patterns

https://www.reddit.com/r/ClaudeCode/comments/1qilh4y/i_built_a_selflearning_plugin_for_claude_code/

 

r/ClaudeCode

https://www.reddit.com/r/ClaudeCode/

 â€¢ 6mo ago [

I built a self-learning plugin for Claude Code that auto-generates specialized agents from usage patterns

](https://www.reddit.com/r/ClaudeCode/comments/1qilh4y/i_built_a_selflearning_plugin_for_claude_code/) 5 upvotes Â· 1 comment

noMoreTechnicalKnowlageRequiredAiWillReplaceUs

https://www.reddit.com/r/ProgrammerHumor/comments/1twolui/nomoretechnicalknowlagerequiredaiwillreplaceus/

 

r/ProgrammerHumor

https://www.reddit.com/r/ProgrammerHumor/

 â€¢ 1mo ago [

noMoreTechnicalKnowlageRequiredAiWillReplaceUs

](https://www.reddit.com/r/ProgrammerHumor/comments/1twolui/nomoretechnicalknowlagerequiredaiwillreplaceus/) 

 2K upvotes Â· 44 comments

theAverageStackOverflowQuestion

https://www.reddit.com/r/ProgrammerHumor/comments/1ul7lpz/theaveragestackoverflowquestion/

 

r/ProgrammerHumor

https://www.reddit.com/r/ProgrammerHumor/

 â€¢ 9d ago [

theAverageStackOverflowQuestion

](https://www.reddit.com/r/ProgrammerHumor/comments/1ul7lpz/theaveragestackoverflowquestion/) 

 1.1K upvotes Â· 50 comments

theFutureOfProgrammingWillBeLike

https://www.reddit.com/r/ProgrammerHumor/comments/1u3pfwn/thefutureofprogrammingwillbelike/

 

r/ProgrammerHumor

https://www.reddit.com/r/ProgrammerHumor/

 â€¢ 1mo ago [

theFutureOfProgrammingWillBeLike

](https://www.reddit.com/r/ProgrammerHumor/comments/1u3pfwn/thefutureofprogrammingwillbelike/) 

 88 upvotes Â· 11 comments

Built a linter that catches the code patterns Claude generates on autopilot

https://www.reddit.com/r/ClaudeAI/comments/1rlkqcv/built_a_linter_that_catches_the_code_patterns/

 

r/ClaudeAI

https://www.reddit.com/r/ClaudeAI/

 â€¢ 4mo ago [

Built a linter that catches the code patterns Claude generates on autopilot

](https://www.reddit.com/r/ClaudeAI/comments/1rlkqcv/built_a_linter_that_catches_the_code_patterns/) 5 upvotes Â· 4 comments

I built this last week, woke up to 300+ stars and a developer with 28k followers tweeting about it, now PRs are coming in from contributors I've never met. Sharing here since this community is exactly who it's built for.

https://www.reddit.com/r/LLMDevs/comments/1shtyzc/i_built_this_last_week_woke_up_to_300_stars_and_a/

 

r/LLMDevs

https://www.reddit.com/r/LLMDevs/

 â€¢ 3mo ago [

I built this last week, woke up to 300+ stars and a developer with 28k followers tweeting about it, now PRs are coming in from contributors I've never met. Sharing here since this community is exactly who it's built for.

](https://www.reddit.com/r/LLMDevs/comments/1shtyzc/i_built_this_last_week_woke_up_to_300_stars_and_a/) 

 86 upvotes Â· 25 comments

Code maintainability plummets in the AI coding era

https://www.reddit.com/r/coding/comments/1upnn2y/code_maintainability_plummets_in_the_ai_coding_era/

 

r/coding

https://www.reddit.com/r/coding/

 â€¢ 4d ago [

Code maintainability plummets in the AI coding era

](https://www.reddit.com/r/coding/comments/1upnn2y/code_maintainability_plummets_in_the_ai_coding_era/) 

 leaddev 370 upvotes Â· 63 comments

We built an LLM based evolutionary system that can redesign the RL task itself, not just the reward (Accepted at RLC 2026)

https://www.reddit.com/r/reinforcementlearning/comments/1ta3joq/we_built_an_llm_based_evolutionary_system_that/

 

r/reinforcementlearning

https://www.reddit.com/r/reinforcementlearning/

 â€¢ 2mo ago [

We built an LLM based evolutionary system that can redesign the RL task itself, not just the reward (Accepted at RLC 2026)

](https://www.reddit.com/r/reinforcementlearning/comments/1ta3joq/we_built_an_llm_based_evolutionary_system_that/) 

 0:44 42 upvotes Â· 6 comments

New research followed 500 devs at 4 orgs rolling out AI Coding Tools over several months

https://www.reddit.com/r/ExperiencedDevs/comments/1pqwcvq/new_research_followed_500_devs_at_4_orgs_rolling/

 

r/ExperiencedDevs

https://www.reddit.com/r/ExperiencedDevs/

 â€¢ 7mo ago [

New research followed 500 devs at 4 orgs rolling out AI Coding Tools over several months

](https://www.reddit.com/r/ExperiencedDevs/comments/1pqwcvq/new_research_followed_500_devs_at_4_orgs_rolling/) 350 upvotes Â· 100 comments

One of the most annoying programming challenges I've ever faced

https://www.reddit.com/r/rust/comments/1r6gz0z/one_of_the_most_annoying_programming_challenges/

 

r/rust

https://www.reddit.com/r/rust/

 â€¢ 5mo ago [

One of the most annoying programming challenges I've ever faced

](https://www.reddit.com/r/rust/comments/1r6gz0z/one_of_the_most_annoying_programming_challenges/) 

 sniffnet 93 upvotes Â· 19 comments

"My God, it's full of stars!" (kotlin code)

https://www.reddit.com/r/generative/comments/1s42qiz/my_god_its_full_of_stars_kotlin_code/

 

r/generative

https://www.reddit.com/r/generative/

 â€¢ 4mo ago [

"My God, it's full of stars!" (kotlin code)

](https://www.reddit.com/r/generative/comments/1s42qiz/my_god_its_full_of_stars_kotlin_code/) 

 253 upvotes Â· 13 comments

theSeniorDevReviewingPrs

https://www.reddit.com/r/ProgrammerHumor/comments/1s1whv1/theseniordevreviewingprs/

 

r/ProgrammerHumor

https://www.reddit.com/r/ProgrammerHumor/

 â€¢ 4mo ago [

theSeniorDevReviewingPrs

](https://www.reddit.com/r/ProgrammerHumor/comments/1s1whv1/theseniordevreviewingprs/) 

 331 upvotes Â· 11 comments

For every $1 spent on AI coding tools, only $0.18 reaches production. Analyzed 1M+ PRs to find where the rest goes.

https://www.reddit.com/r/coding/comments/1tw2o6q/for_every_1_spent_on_ai_coding_tools_only_018/

 

r/coding

https://www.reddit.com/r/coding/

 â€¢ 1mo ago [

For every $1 spent on AI coding tools, only $0.18 reaches production. Analyzed 1M+ PRs to find where the rest goes.

](https://www.reddit.com/r/coding/comments/1tw2o6q/for_every_1_spent_on_ai_coding_tools_only_018/) 50 upvotes Â· 9 comments

I built an Open Source K8s framework to run Claude Code safely with --dangerously-skip-permissions

https://www.reddit.com/r/ClaudeCode/comments/1r33l62/i_built_an_open_source_k8s_framework_to_run/

 

r/ClaudeCode

https://www.reddit.com/r/ClaudeCode/

 â€¢ 5mo ago [

I built an Open Source K8s framework to run Claude Code safely with --dangerously-skip-permissions

](https://www.reddit.com/r/ClaudeCode/comments/1r33l62/i_built_an_open_source_k8s_framework_to_run/) 3 upvotes Â· 9 comments

Done building.

https://www.reddit.com/r/pinescript/comments/1ugq1uz/done_building/

 

r/pinescript

https://www.reddit.com/r/pinescript/

 â€¢ 14d ago [

Done building.

](https://www.reddit.com/r/pinescript/comments/1ugq1uz/done_building/) 

 28 upvotes Â· 17 comments

pythonInventedFreeThreading

https://www.reddit.com/r/ProgrammerHumor/comments/1u6lreo/pythoninventedfreethreading/

 

r/ProgrammerHumor

https://www.reddit.com/r/ProgrammerHumor/

 â€¢ 26d ago [

pythonInventedFreeThreading

](https://www.reddit.com/r/ProgrammerHumor/comments/1u6lreo/pythoninventedfreethreading/) 

 1.1K upvotes Â· 74 comments

View Post in

æ—¥æœ¬èªž

https://www.reddit.com/r/Python/comments/1rlho78/i_built_a_precommit_linter_that_catches/?tl=ja

PortuguÃªs (Brasil)

https://www.reddit.com/r/Python/comments/1rlho78/i_built_a_precommit_linter_that_catches/?tl=pt-br

à¤¹à¤¿à¤¨à¥ à¤¦à¥€

https://www.reddit.com/r/Python/comments/1rlho78/i_built_a_precommit_linter_that_catches/?tl=hi

ç®€ä½“ä¸ æ–‡

https://www.reddit.com/r/Python/comments/1rlho78/i_built_a_precommit_linter_that_catches/?tl=zh-hans

Ð ÑƒÑ Ñ ÐºÐ¸Ð¹

https://www.reddit.com/r/Python/comments/1rlho78/i_built_a_precommit_linter_that_catches/?tl=ru

FranÃ§ais

https://www.reddit.com/r/Python/comments/1rlho78/i_built_a_precommit_linter_that_catches/?tl=fr

See more See fewer

Italiano

https://www.reddit.com/r/Python/comments/1rlho78/i_built_a_precommit_linter_that_catches/?tl=it

SlovenÄ ina

https://www.reddit.com/r/Python/comments/1rlho78/i_built_a_precommit_linter_that_catches/?tl=sk

Deutsch

https://www.reddit.com/r/Python/comments/1rlho78/i_built_a_precommit_linter_that_catches/?tl=de

à¹„à¸—à¸¢

https://www.reddit.com/r/Python/comments/1rlho78/i_built_a_precommit_linter_that_catches/?tl=th

Nederlands

https://www.reddit.com/r/Python/comments/1rlho78/i_built_a_precommit_linter_that_catches/?tl=nl

Svenska

https://www.reddit.com/r/Python/comments/1rlho78/i_built_a_precommit_linter_that_catches/?tl=sv

Polski

https://www.reddit.com/r/Python/comments/1rlho78/i_built_a_precommit_linter_that_catches/?tl=pl

Ø§Ù„Ø¹Ø±Ø¨ÙŠØ©

https://www.reddit.com/r/Python/comments/1rlho78/i_built_a_precommit_linter_that_catches/?tl=ar

Î• Î»Î»Î· Î½Î¹ÎºÎ¬

https://www.reddit.com/r/Python/comments/1rlho78/i_built_a_precommit_linter_that_catches/?tl=el

Filipino

https://www.reddit.com/r/Python/comments/1rlho78/i_built_a_precommit_linter_that_catches/?tl=fil

í• œêµì–´

https://www.reddit.com/r/Python/comments/1rlho78/i_built_a_precommit_linter_that_catches/?tl=ko

EspaÃ±ol (LatinoamÃ©rica)

https://www.reddit.com/r/Python/comments/1rlho78/i_built_a_precommit_linter_that_catches/?tl=es-419

Community Info Section

r/Python

https://www.reddit.com/r/Python/

 

 

Pycon US 2025

https://us.pycon.org/2025/

 starts next week!

Join

Python

The largest Python community for Reddit! Stay up to date with the latest news, packages, and meta information relating to the Python programming language. --- If you have questions or are new to Python use r/LearnPython

Show more

Public

Anyone can view, post, and comment to this community

Home

https://www.reddit.com/?feed=home

Popular

https://www.reddit.com/r/popular/

News

https://www.reddit.com/news/

Explore

https://www.reddit.com/explore/

Best of Reddit

https://www.reddit.com/posts/2026/global/

Best of Reddit in Portuguese

https://www.reddit.com/posts/2026/tl-pt-BR/

Best of Reddit in German

https://www.reddit.com/posts/2026/tl-de/

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

Reddit, Inc. Â© 2026. All rights reserved.

https://redditinc.com/

 

Join the most real place on the internet

Continue with Apple

ï£¿â€…Sign in with Apple

Continue with Phone Number

https://www.reddit.com/login/

Continue with Email

https://www.reddit.com/register/

By continuing, you agree to our 

User Agreement

https://www.redditinc.com/policies/user-agreement

 and acknowledge that you understand the 

Privacy Policy

https://www.redditinc.com/policies/privacy-policy

.

 

0cAFcWeA43yCDpLSITY7rOD3sFoMhz2g2i0xHwAG5i0y2p4s-vUD1AHGYQrYiH_QYKWFYK42qKMiCkO0TjwI9xRE3kwejDVz66hw4RBWYZHRzVLn3ufM7IxacZtGR_S8hNSXZXOGer-IULzDGHIEPOVxSwAQZsea_YJectEoGkhMolUxXcTa_ZJV1w5W8mEvXAeTgpHEKzrCQbgXRPes_vewY4Z1M8bAET_mj7M7tfEVGVK5RHvK8dh_a5qQEJPlyK1UTG5JUQnSZq5S5alZsVPcg5SmPHYeZqadNJ3QyfIy8PXd0Z0zjIqLC066UjVIqVvuQP0TDNEHsvpulIVF-4MfcdUCGHc-oEP_wJkHvyg1lOXlvpbQ1eSzqzZWOQXPWPGY1MCeA8veCEd5tGY_RzkZzfmrH6SGuj79V_3bYgq4JJ2Gerh8ygBCa8rtcTScYchpN9K3HjG7KymdVSG5MQ0spjq-UXXzPz0GK72jS29PBEWogMjmRzFhsCL__bHkZCsl6cTjYavPnvI8kVr4wYnhRm9JPezjBdk0cvpMTydGQwKQN-sYJ2b_FV5m4nBjaOlT3PZFLt017T0a-cbl1ySOUuKMZUjV3iCEFKj_VmvpMaRyeFXyPi-kzHuisp26csrQim8cxvC5K7qXZ2WC6WJsPHOSRAAxM-wp3VADml-1dRWcUaQP1NnooyP4294fKjqCDcZ5fY8BUhnawf6c2rUiuLb53Qzy3UtDYgxHtcBMFWzwQzIAAIMygX6umPstema4QfGTjDUQMHoZFdsNKQpE7JM2VzT_60r-BFTrF2xri69MLB77sMDxPLAOZg62AKbctDGdkC7Njxutz8KeySJ1BbNWOGxO9Vo51yyrsxb40raC0PyKCVEzkW7Y1d3ETrCapLHB6rXzTTmMGjNmbOnPht-enNYgl_r_9CrlPdLtgPD2bmCO07Hx_NKRXmJOJq9_SY2qB5UJ2nMJH90HYZPygU01Ko0bf7FbzRLaG9ZWzF46m3BVg8eeOePAv8wH2SFAi_nVM96CkjaxvdriIRy58iLKKkYLNfTxcuMJEzAIN9Jory4wbSnKil97g_Y83MM6mX8rHU0HYDqo8cM2l_zmd_Fb-QXGIkuoWcGXSFLT5qnS7cXtocFGUjfLfM-mgRDvm7hP0204qVaeirp3qZ37lyCVIBx8YOCCywol49ev4T8f_GPiKoL9LI2LzNTJvYIzjN3rn4FQn2SH6021zOtwPeqqc62zHnbd9Mry2xP-l0HtFTex-WPwzd8JIopn6hJ2Jg8jJWw7N_G1Dv-vNcbMNNiuIPMNGCU-fymtmShtxbQQGzQAFx0TQL8dvAFQEJFmExwSXjvwfxWgQIxC7ws7Qf96i9FMr9tZOITwrRAHPPlUYpupei6PLHFMf-5rs9_Hj0AzdNGsZoCxvnYVj-0wk5THbAH4o8GF1JnoHFSyZ_iY0JiKzrOljLKjHyBjStcoGa6JTxJYaQB_Q1G2Qq1jGF13LhrLzFK3cCJf032hGN_wtsw_ZqHCgF3w84xmyiT0lQcJ3BrQWT5pn3xnvUreZFFIL8smFjLAnhL-UqLKo15si75uqDpmDDCJ7PIkxpj6yPYJdrYakHpYOcqb66t61Dv9hMKZr_lVzwDtfVb5qUYx7qTb5T06jHkz2TY_5yt3LfxAx9Y1d2FygaTWgKCyDuXzHeVi6IqlfcTXyDaL64pdd1XDs0TO5QZPq49_d6qXlrF03z6LyCNW1S4TM7X83yICHWisWD7FHJ8jdikQvSlG0ex3P90966ac6lEKQ_hcV0IWFqZcOmX6rC_3gxJCGN92fuS9oLPRic4tH6oEDyJiBUPZaMugp55BldzNMH7__fYl9vKen3cm9iFw_iu4h2_2pxTN0uSqwZdkvI5mN0nCwFN9iUgIp08Mh_meBb2MiyBs0RaVfIEh7RP8X0wUX6usUFv67EIONcKP4xoatKqK6SCotCKy8cJMTmp7HHpaBFpCZv7D3ZMYD2i-QyuxIHAV8J3Ek-DX0xXpIiFKmbaqvnw2wGq_AlNT5krW0Uhiraf2anBu_078ftur65dioFXgFxCBklnhpAUKRCXt8-x7MDirg2GV7W8-wnRdeFa0UIrE7WeRPqHjB-gZ83KUizr6qVGMTGFg
