---
source_id: "59fa0c1c-38ce-476e-9fb7-2cefbc59db2b"
title: "Git Worktrees in Claude Code - Run Parallel AI Sessions - codewithmukesh"
notebook_id: afd2f1dd-ff64-44f7-9259-6f923b6c081a
url: https://codewithmukesh.com/blog/git-worktrees-claude-code/
type: 5
exported: 2026-08-08
---

# Git Worktrees in Claude Code - Run Parallel AI Sessions - codewithmukesh
Git Worktrees in Claude Code - Run Parallel AI Sessions - codewithmukesh
Skip to main content
https://codewithmukesh.com/blog/git-worktrees-claude-code/#main
Article complete
Get one like this every Tuesday at 7 PM IST.
Subscribe free
codewithmukesh codewith mukesh
https://codewithmukesh.com/
Home
https://codewithmukesh.com/
Blog
https://codewithmukesh.com/blog
Courses
https://codewithmukesh.com/courses
Resources
.NET Mock Interview Free auto-scored interview quiz →
https://codewithmukesh.com/dotnet-mock-interview
.NET Claude Kit Build with Claude + .NET →
https://codewithmukesh.com/resources/dotnet-claude-kit
.NET Web API Interview Questions 100 practical questions - free PDF →
https://codewithmukesh.com/resources/dotnet-webapi-interview-questions
Clean Architecture Template .NET 10 starter - free download →
https://codewithmukesh.com/resources/clean-architecture-template
Sponsor
https://codewithmukesh.com/sponsor
Contact
https://codewithmukesh.com/contact
Search 
Ctrl · K
Subscribe
Menu
Search articles
Resources
.NET Mock Interview Free auto-scored interview quiz
https://codewithmukesh.com/dotnet-mock-interview
.NET Claude Kit Build with Claude + .NET
https://codewithmukesh.com/resources/dotnet-claude-kit
.NET Web API Interview Questions 100 practical questions - free PDF
https://codewithmukesh.com/resources/dotnet-webapi-interview-questions
Clean Architecture Template .NET 10 starter - free download
https://codewithmukesh.com/resources/clean-architecture-template
Menu
Home
https://codewithmukesh.com/
Blog
https://codewithmukesh.com/blog
Courses
https://codewithmukesh.com/courses
Sponsor
https://codewithmukesh.com/sponsor
Contact
https://codewithmukesh.com/contact
Subscribe to the newsletter
← Back to blog
https://codewithmukesh.com/blog/
claude
https://codewithmukesh.com/categories/claude/
 Jun 21, 2026 25 min read 
Lesson 8/28
https://codewithmukesh.com/courses/claude-code-for-dotnet-developers/
 Updated
Git Worktrees in Claude Code - Run Parallel AI Sessions
Run parallel Claude Code sessions on isolated branches with built-in Git worktree support. Covers the --worktree flag, branching from a PR, .worktreeinclude, subagent isolation, hooks, and cleanup.
Run parallel Claude Code sessions on isolated branches with built-in Git worktree support. Covers the --worktree flag, branching from a PR, .worktreeinclude, subagent isolation, hooks, and cleanup.
claude
claude-code git-worktrees parallel-development isolated-branches ai-coding-assistant git developer-productivity subagents worktree-hooks multi-session ai-workflow developer-tools version-control branching-strategy claude-opus dotnet-development tmux cli-tools git-branching ci-cd-pipeline
 
Mukesh Murugan
Software Engineer
The .NET Weekly · Tue 7 PM IST
Level up your .NET, one Tuesday at a time.
The one email I'd want in my own inbox. Free, every week.
→ Production .NET patterns, not toy demos
→ Real benchmarks & architecture breakdowns
→ A 5-minute read. Zero fluff, unsubscribe anytime.
Your email address Subscribe - it's free →
Join 9,735 developers
· +355 this week
Tip jar · Reader-supported
Did this save you time?
A small tip keeps the .NET deep-dives coming. One-time, no subscription.
Buy me a coffee →
https://codewithmukesh.com/refer/bmc
In this post
19 sections
0
01 What Are Git Worktrees?
https://codewithmukesh.com/blog/git-worktrees-claude-code/#what-are-git-worktrees
02 How Do Claude Code Worktrees Differ from Plain Git Worktrees?
https://codewithmukesh.com/blog/git-worktrees-claude-code/#how-do-claude-code-worktrees-differ-from-plain-git-worktrees
03 Creating and Using Worktrees
https://codewithmukesh.com/blog/git-worktrees-claude-code/#creating-and-using-worktrees
04 How Does Worktree Cleanup Work in Claude Code?
https://codewithmukesh.com/blog/git-worktrees-claude-code/#how-does-worktree-cleanup-work-in-claude-code
05 How Does Subagent Worktree Isolation Work?
https://codewithmukesh.com/blog/git-worktrees-claude-code/#how-does-subagent-worktree-isolation-work
06 How Do WorktreeCreate and WorktreeRemove Hooks Work?
https://codewithmukesh.com/blog/git-worktrees-claude-code/#how-do-worktreecreate-and-worktreeremove-hooks-work
07 Worktrees + .gitignore
https://codewithmukesh.com/blog/git-worktrees-claude-code/#worktrees--gitignore
08 How Do I Get My .env Files Into Worktrees?
https://codewithmukesh.com/blog/git-worktrees-claude-code/#how-do-i-get-my-env-files-into-worktrees
09 When Should You Use Git Worktrees in Claude Code?
https://codewithmukesh.com/blog/git-worktrees-claude-code/#when-should-you-use-git-worktrees-in-claude-code
10 Worktrees vs. the Other Ways to Run Claude Code in Parallel
https://codewithmukesh.com/blog/git-worktrees-claude-code/#worktrees-vs-the-other-ways-to-run-claude-code-in-parallel
11 Real Workflow: Parallel Feature Development
https://codewithmukesh.com/blog/git-worktrees-claude-code/#real-workflow-parallel-feature-development
12 Do Worktrees Share CLAUDE.md and Project Settings?
https://codewithmukesh.com/blog/git-worktrees-claude-code/#do-worktrees-share-claudemd-and-project-settings
13 .NET-Specific Gotchas Worktrees Won't Warn You About
https://codewithmukesh.com/blog/git-worktrees-claude-code/#net-specific-gotchas-worktrees-wont-warn-you-about
14 SDK and Programmatic Usage
https://codewithmukesh.com/blog/git-worktrees-claude-code/#sdk-and-programmatic-usage
15 Tips from Real Usage
https://codewithmukesh.com/blog/git-worktrees-claude-code/#tips-from-real-usage
16 Changelog and Version History
https://codewithmukesh.com/blog/git-worktrees-claude-code/#changelog-and-version-history
17 Key Takeaways
https://codewithmukesh.com/blog/git-worktrees-claude-code/#key-takeaways
18 Troubleshooting Common Worktree Issues
https://codewithmukesh.com/blog/git-worktrees-claude-code/#troubleshooting-common-worktree-issues
19 Summary
https://codewithmukesh.com/blog/git-worktrees-claude-code/#summary
Share
Copy link
Post on X
https://twitter.com/intent/tweet?text=Git%20Worktrees%20in%20Claude%20Code%20-%20Run%20Parallel%20AI%20Sessions&url=https%3A%2F%2Fcodewithmukesh.com%2Fblog%2Fgit-worktrees-claude-code%2F
 
LinkedIn
https://www.linkedin.com/sharing/share-offsite/?url=https%3A%2F%2Fcodewithmukesh.com%2Fblog%2Fgit-worktrees-claude-code%2F
Chapter · 08 of 28 · Module 2 of 8 · Free View course → Claude Code for .NET Developers From dotnet new to docker push - REST, EF Core 10, auth, caching, Clean Architecture, observability. 28 hands-on lessons, source on GitHub.
https://codewithmukesh.com/courses/claude-code-for-dotnet-developers/
TL;DR Came from search
Run parallel Claude Code sessions on isolated branches with built-in Git worktree support. Covers the --worktree flag, branching from a PR, .worktreeinclude, subagent isolation, hooks, and cleanup.
Want the version with benchmarks, judgment calls, and what the AI summary left out? Get it every Tuesday.
Your email address Subscribe ↗
Free · No spam · Unsubscribe anytime
Free Course Setup to multi-agent teams · Vol. 02 Claude Code for .NET Developers The full Claude Code stack, from CLAUDE.md to multi-agent workflows Master AI-powered .NET development with Claude Code. Learn CLAUDE.md, Plan Mode, MCP servers, hooks, skills, and multi-agent workflows that ship real features. 01 11 lessons - the full Claude Code stack, from first install to agent teams. 02 8+ hours - real .NET workflows, not generic AI demos with toy code. 03 All levels - beginner walkthroughs and advanced patterns in one course. Free Forever · No signup wall Start the course →
https://codewithmukesh.com/courses/claude-code-for-dotnet-developers/#join-course
I had Claude Code refactoring my authentication middleware when a critical bug report came in. In a pre-worktree world, my options were terrible: stash incomplete work and lose context, or open a second terminal, clone the repo again, install dependencies, and start a separate Claude session from scratch. Either way, I'm losing 10+ minutes of momentum and context.
With 
Git worktrees in Claude Code
, I typed 
claude --worktree hotfix-auth
 in a second terminal, fixed the bug in an isolated copy of the repo while my refactoring session continued untouched in the original, and merged the hotfix - all without either session knowing or caring about the other.
This is the feature that turned Claude Code from a powerful single-threaded tool into a 
parallel development engine
. Shipped in Claude Code v2.1.49 (February 2026), built-in worktree support lets you run multiple Claude Code sessions on the same repository, each with its own branch, its own files, and zero risk of one session's edits stomping on another's.
But knowing the commands isn't the hard part. The real value is knowing when parallel sessions help versus when they just add complexity, how to make a worktree usable the moment it's created, and how 
subagent isolation
 - where Claude spawns its own helper agents called subagents - lets Claude run parallel workers without you lifting a finger. That, plus the .NET-specific traps nobody else writes about, is what this guide covers.
The short version:
 Run 
claude --worktree <name>
 to start an isolated Claude Code session on its own branch under 
.claude/worktrees/
 , so you can build a feature in one terminal while fixing a bug in another - no stashing, no second clone. The commands are the easy part. What actually trips .NET developers up is everything around them: per-worktree 
dotnet restore
 , user secrets that are 
shared
 across worktrees rather than isolated, 
launchSettings.json
 port collisions, and EF Core migrations all hitting one local database. This guide covers the workflow and every one of those traps.
[The Newsletter Tue 7 PM IST
Weekly .NET Newsletter
Trusted by 9,735 .NET developers Every Tuesday, I send the one .NET insight I wish I'd had earlier that week. Production patterns, Claude Code workflows, and benchmarks - never published on the blog. 01 
This week's take
 - my verdict on the hottest .NET topic. 02 
3-5 quick wins
 you can use the same day. 03 
Bonus drop
 - Claude Code prompts that ship real features. Free · 52 issues a year Join the newsletter →](https://codewithmukesh.com/newsletter)
If you're new to Claude Code, start with the beginner guide first - this article assumes you're comfortable with basic Claude Code sessions.
[Read next · Companion article
New to Claude Code?
Learn installation, CLAUDE.md setup, and the basics of AI powered development from scratch.](https://codewithmukesh.com/blog/claude-code-for-beginners/)
[Read next · Companion article
Git Workflows Explained
Understand GitFlow, GitHub Flow, and Trunk-Based Development to choose the right branching strategy for your team.](https://codewithmukesh.com/blog/git-workflows-gitflow-vs-github-flow-vs-trunk-based/)
Let's get into it.
What Are Git Worktrees?
Claude Code's worktrees are a managed layer on top of standard Git worktrees, so the foundation matters. 
A Git worktree is a separate working directory linked to the same repository
 - each one checked out to a different branch, with its own files and staging area, all sharing a single Git history and remote. Instead of 
git checkout
 -ing between branches (and stashing incomplete work every time), you get multiple checkouts side by side.
Here's what's shared versus per-worktree:
Component
Shared Across Worktrees
Per-Worktree
Object database (commits, blobs, trees)
Yes
-
Remote tracking branches
Yes
-
Tags
Yes
-
Repository config
Yes
-
HEAD (current branch pointer)
-
Yes
Index (staging area)
-
Yes
Working files on disk
-
Yes
The payoff: a worktree only writes working files to disk and reuses the history that's already there, so a second checkout is ready in seconds - no re-clone, no 
git stash
 dance to keep two tasks open.
The Standard Git Worktree Commands
Claude Code abstracts most of this away, but the foundation helps when things go sideways (see the 
official Git worktree documentation
https://git-scm.com/docs/git-worktree
 for the full spec):
Terminal window
git worktree add ../my-feature -b feature/new-auth   # create + branch
git worktree list                                    # show all worktrees
git worktree remove ../my-feature                    # clean one up
git worktree prune                                   # clear stale metadata

The 
add
 command creates a directory at 
../my-feature
 , checks out a new branch, and links it back to the original repo - you work in it like a separate clone, except it shares history. 
One safety feature worth knowing:
 Git refuses to check out the same branch in two worktrees at once, which stops two directories from fighting over the same branch.
How Do Claude Code Worktrees Differ from Plain Git Worktrees?
Plain Git worktrees are powerful but manual. You have to pick branch names, choose directories, remember to clean up, and handle the lifecycle yourself. Claude Code's built-in worktree support turns this into a 
managed experience
 with automatic naming, automatic cleanup, session integration, and subagent isolation.
Here's what Claude Code handles for you:
Aspect
Plain Git Worktrees
Claude Code Worktrees
Creation
git worktree add <path> -b <branch>
claude --worktree <name>
Directory
You choose any path
Always 
<repo>/.claude/worktrees/<name>
Branch naming
You pick the name
Automatically 
worktree-<name>
Base branch
You choose the starting point
Default remote branch (usually 
main
 )
Cleanup
Manual 
git worktree remove
Automatic: no-change worktrees auto-cleaned, changed worktrees prompt you
Session tracking
None
/resume
 picker shows all worktree sessions
Config sharing
Manual
Project configs and auto-memory shared automatically
Subagent support
N/A
isolation: worktree
 gives each subagent its own copy
The managed experience matters more than it looks. Plain worktrees are easy to create and even easier to forget, and they pile up as stale directories and orphaned branches. Claude Code's automatic cleanup handles this - exit a session without making changes and the worktree and branch are silently removed. No manual housekeeping.
Creating and Using Worktrees
The —worktree Flag
The simplest way to start an isolated session:
Terminal window
claude --worktree feature-auth

This does three things:
Creates a Git worktree at 
<repo>/.claude/worktrees/feature-auth/
Creates a new branch called 
worktree-feature-auth
 from your default remote branch
Starts a Claude Code session scoped entirely to that worktree directory
You can also let Claude generate a random name:
Terminal window
claude --worktree

Claude picks something like 
bright-running-fox
 or 
bold-oak-a3f2
 . The short flag 
-w
 works too:
Terminal window
claude -w bugfix-login

Running Multiple Sessions in Parallel
The real power is running multiple sessions simultaneously. Open three terminals:
Terminal window
# Terminal 1 - main session (your normal repo)
claude

# Terminal 2 - feature work
claude -w feature-notifications

# Terminal 3 - hotfix
claude -w hotfix-payment-validation

Each terminal has its own Claude Code instance, its own branch, and its own files. Changes in one session are invisible to the others until you merge branches.
If you use the 
Claude Code desktop app
https://code.claude.com/docs/en/desktop
 instead of the terminal, this happens for free: every new session gets its own worktree automatically, no 
--worktree
 flag needed.
Branch From a Pull Request
If you want to review or test someone's pull request without disturbing your own work, point 
--worktree
 at the PR number (prefixed with 
#
 ) or a full GitHub PR URL:
Terminal window
claude --worktree "#1234"

Claude Code fetches 
pull/1234/head
 from 
origin
 and creates the worktree at 
.claude/worktrees/pr-1234
 . You get an isolated checkout of the PR branch, ready for Claude to read, run, and critique - and when you exit, your main session is exactly where you left it. This is the cleanest way I've found to review a large PR while a feature is still cooking in another terminal.
Choose the Base Branch
By default, a new worktree branches from your repository's default branch ( 
origin/HEAD
 ), so it starts from a clean tree matching the remote. That's usually what you want - independent work, no surprises from your local state.
But sometimes you need the opposite: a worktree that carries your 
unpushed commits and in-progress feature state
. Set 
worktree.baseRef
 to 
"head"
 in your 
.claude/settings.json
 :
{
  "worktree": {
    "baseRef": "head"
  }
}

Now new worktrees branch from your local 
HEAD
 instead of the remote. The setting accepts only 
"fresh"
 (the default) or 
"head"
 - not arbitrary refs. This matters most when you isolate subagents that need to operate on work you haven't pushed yet.
Combining with tmux
For maximum productivity, combine worktrees with tmux to manage sessions from a single terminal:
Terminal window
claude --worktree feature-auth --tmux

This launches Claude in its own tmux session. You can detach, switch to another pane, and start a second worktree session - all from one terminal window.
In-Session Worktree Creation
You don't need to plan ahead. If you're already in a Claude Code session and realize you need isolation, just ask:
> work in a worktree

Or:
> start a worktree called auth-refactor

Under the hood, Claude uses its 
EnterWorktree
 tool to create the worktree and switch your session into it. This is useful when a session starts as a quick fix and evolves into something that needs isolation.
Once you're inside a worktree, Claude can also switch 
between
 existing worktrees mid-session - just point it at another directory under 
.claude/worktrees/
 :
> switch to the notifications worktree

Claude calls 
EnterWorktree
 with the target path and moves your session there. The worktree you left stays on disk, untouched, exactly as you had it. When you're done, 
ExitWorktree
 returns you to the main checkout.
How Does Worktree Cleanup Work in Claude Code?
This is the part most developers miss, and it's one of the best things about Claude Code's worktree management.
Automatic Cleanup (Nothing to Lose)
If you exit a worktree session with 
no uncommitted changes, no untracked files, and no new commits
 - you were exploring, reading code, or abandoned the task - Claude 
automatically removes
 the worktree directory and its branch. No stale artifacts left behind.
One exception: if you gave the session a name, Claude prompts you instead of removing silently, so a named session you might want to resume isn't deleted out from under you.
Prompted Cleanup (Changes Exist)
If you made changes, left untracked files, or committed in the worktree, Claude prompts you when you exit:
Keep
: Preserves the worktree directory and branch. You can come back later with 
cd .claude/worktrees/feature-auth && claude
 or find the session in the 
/resume
 picker.
Remove
: Deletes the worktree directory and its branch, 
discarding all uncommitted changes, untracked files, and commits
. This is destructive - make sure you've pushed or merged anything you want to keep.
Two details worth knowing:
Non-interactive runs aren't swept.
 A 
--worktree
 session run with 
-p
 (print mode) has no exit prompt, so it isn't cleaned up automatically - remove it yourself with 
git worktree remove
 .
Subagent and background-session worktrees
 are swept once they're older than your 
cleanupPeriodDays
 setting, provided they have nothing uncommitted, untracked, or unpushed. Worktrees 
you
 create with 
--worktree
 are never touched by this sweep, and a running agent holds a 
git worktree lock
 so the sweep can't remove it mid-run.
Manual Cleanup
If you need to clean up outside of a Claude session (maybe you closed the terminal without properly exiting):
Terminal window
git worktree list
git worktree remove .claude/worktrees/feature-auth

My recommendation:
 Run 
git worktree list
 weekly to check for stale worktrees. It takes 5 seconds and prevents directory bloat.
How Does Subagent Worktree Isolation Work?
This is where worktrees get genuinely powerful. Instead of just running parallel sessions yourself, you let 
Claude parallelize its own work
. When Claude spawns subagents normally, they all share one working directory, so two agents editing the same file collide. With 
isolation: worktree
 , each subagent gets a fresh copy of the repo - they edit independently and you review the results after.
Configuring Subagent Isolation
Create an agent definition file at 
.claude/agents/migration-worker.md
 :
---
name: migration-worker
description: Handles code migration tasks in isolation
isolation: worktree
tools: Read, Edit, Bash, Grep, Glob
---

You are a code migration specialist. Your task is to migrate code
following the patterns and conventions in the project's CLAUDE.md.
Focus on one module at a time and verify the build passes after changes.

When Claude spawns this agent, it automatically:
Creates a temporary worktree for the agent
Runs the agent inside that isolated copy
If the agent finishes 
without changes
 - removes the worktree automatically
If the agent finishes 
with changes
 - returns the worktree path and branch name in the result
Real Use Case: Parallel Code Migration
Say you need to migrate 30 files from an old pattern to a new one. Instead of one agent doing them sequentially:
Spawn 3 migration-worker agents. Agent 1 handles files in src/Features/Products/,
Agent 2 handles src/Features/Orders/, Agent 3 handles src/Features/Users/.
Each should migrate from the old repository pattern to direct DbContext usage.

Each agent works in its own worktree. No conflicts, no waiting on a shared file, and the three migrations run concurrently instead of one after another. When they're done, you review the branches and merge.
Conversational Worktree Isolation
You don't always need a pre-configured agent file. During any session, you can tell Claude:
> use worktrees for your agents

Claude will create temporary worktrees for subagents it spawns during that session. This is great for ad-hoc parallelization without upfront configuration.
How Do WorktreeCreate and WorktreeRemove Hooks Work?
Here's a feature that separates the developers who read the docs from the developers who don't: 
worktree hooks
. These let you run custom commands whenever a worktree is created or removed - perfect for dependency installation, environment setup, or non-Git version control systems.
The Dependency Problem
A new worktree has your source files but 
not your installed dependencies
 - no 
node_modules/
 , no 
bin/
 / 
obj/
 for .NET. Build or run anything and it fails until you restore. This is the single most common worktree complaint, and a hook solves it cleanly.
Auto-Installing Dependencies with WorktreeCreate
Add this to your 
.claude/settings.json
 :
{
  "hooks": {
    "WorktreeCreate": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'NAME=$(jq -r .name); DIR=\".claude/worktrees/$NAME\"; cd \"$DIR\" && dotnet restore >&2 && echo \"$(pwd)\"'"
          }
        ]
      }
    ]
  }
}

Swap 
dotnet restore
 for 
npm install
 , 
uv sync
 , or whatever your stack needs - the shape is identical. This works for both 
.sln
 and the 
new .slnx solution format
https://codewithmukesh.com/blog/slnx-solution-format-dotnet/
, since 
dotnet restore
 handles either automatically.
Critical detail:
 The hook receives JSON on stdin with a 
name
 field and 
must print the absolute path
 to the worktree on stdout. The 
>&2
 redirect sends dependency installation output to stderr so it doesn't interfere with the path output. If the hook exits with a non-zero code, worktree creation fails.
Hook Input Format
The JSON your hook receives on stdin:
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/path/to/repo",
  "hook_event_name": "WorktreeCreate",
  "name": "feature-auth",
  "branch_name": "refs/heads/worktree-feature-auth",
  "upstream": "origin/main"
}

The 
name
 field is the worktree identifier - either what you passed to 
--worktree
 or the auto-generated random name. 
branch_name
 and 
upstream
 tell you which branch Claude wants and where it's tracking from, which is handy if your hook needs to create the branch itself (for non-Git VCS). For a standard 
dotnet restore
 / 
npm install
 setup, 
name
 is all you need.
WorktreeRemove for Cleanup
The remove hook fires when a worktree is being deleted:
{
  "hooks": {
    "WorktreeRemove": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -c 'jq -r .worktree_path | xargs rm -rf'"
          }
        ]
      }
    ]
  }
}

Important:
 WorktreeRemove hooks have no decision control - they cannot block removal. They fire-and-forget for cleanup purposes only. Failures are logged in debug mode.
Non-Git VCS Support
Because a configured 
WorktreeCreate
 hook 
replaces
 
git worktree add
 entirely, it also unlocks isolation for non-Git systems - SVN, Perforce, Mercurial. The hook does an 
svn checkout
 (or whatever your VCS needs) into the directory and prints the path; Claude Code treats that as the session's working copy. Note that only 
type: "command"
 hooks are supported here - no prompt, HTTP, or agent hooks, and no matcher patterns.
[Free resource · Companion download
.NET Claude Kit
Open-source Claude Code companion with 47 skills and 10 specialist agents](https://codewithmukesh.com/resources/dotnet-claude-kit)
Worktrees + .gitignore
Since Claude Code creates worktrees inside your repository at 
.claude/worktrees/
 , you need to add this to your 
.gitignore
 :
.claude/worktrees/

Without this, every file in every worktree shows up as untracked in your main working directory's 
git status
 . Add it once and forget about it.
How Do I Get My .env Files Into Worktrees?
A worktree is a fresh checkout, so anything that's gitignored - 
.env
 , 
.env.local
 , local secrets - 
isn't there
. Your app boots in the main checkout and crashes in the worktree because the connection string went missing. For a long time the only fix was “copy them by hand,” which nobody remembers to do.
The clean answer now is a 
.worktreeinclude
 file at your project root. It tells Claude Code which gitignored files to copy into every new worktree:
.env
.env.local
config/secrets.json

It uses 
.gitignore
 syntax, with one important guardrail: 
only files that match a pattern and are gitignored get copied.
 Tracked files are never duplicated, so you can't accidentally fork a committed config. This applies to worktrees created with 
--worktree
 , subagent worktrees, and parallel sessions in the desktop app - all of them get your local config automatically.
One caveat: if you've configured a 
WorktreeCreate
 hook (covered in the hooks section above), it replaces the default creation logic entirely, so 
.worktreeinclude
 is 
not
 processed. In that case, copy the files inside your hook script instead.
When Should You Use Git Worktrees in Claude Code?
Not every session needs isolation. Worktrees add a small overhead - creation time, dependency installation, context that doesn't carry over - and for quick, focused tasks, that overhead isn't worth it.
Decision Matrix
Scenario
Worktree?
Why
Emergency hotfix while deep in a feature
Yes
Don't stash and lose context. Isolate the fix.
Two independent features in parallel
Yes
Each feature gets its own branch and files.
Running subagents that edit overlapping files
Yes
Isolation prevents file conflicts between agents.
Large codebase migration in batches
Yes
Multiple agents can migrate different modules simultaneously.
Quick one-file bug fix
No
Faster to just fix it in your current session.
Exploring or reading code (no edits)
No
Nothing to conflict. Plan Mode is cheaper for exploration.
Sequential work on the same feature
No
One session, one branch. No benefit from isolation.
Code review of a PR
Yes
claude --worktree "#1234"
 checks the PR out in isolation so you can run and critique it without disrupting your work.
My Rule of Thumb
If both of these are true, use a worktree:
I need to switch context (different feature, different bug, different concern)
I want to come back to what I'm currently doing without losing state
If either condition is false - I don't need to switch, or I'm done with the current task - I skip the worktree.
My take:
 I typically keep 
2-3 active worktrees
 at most during a workday. Beyond that, the cognitive overhead of tracking parallel work outweighs the benefit. Worktrees are a tool for focused parallelism, not an invitation to juggle 7 things at once. The win isn't a number on a stopwatch - it's that the stash/checkout/restore dance disappears entirely, and an interrupting bug no longer forces me to tear down whatever I was in the middle of.
The Honest Case Against Worktrees
Worktrees aren't free, and pretending otherwise is how people end up regretting them. Every worktree is a fresh checkout, so for .NET you pay a real cost: a separate 
bin/
 / 
obj/
 and a separate NuGet restore per worktree, which adds up on a large solution. There's a bootstrap tax too - dependencies, secrets, and database state don't come along, so a worktree isn't usable until your hooks finish setting it up. And parallel branches can create the exact merge conflicts you were trying to avoid if two sessions touch the same files. None of this makes worktrees a bad idea - it makes them a 
deliberate
 one. If a task is quick, sequential, or read-only, skip the overhead and work in your main session.
Worktrees vs. the Other Ways to Run Claude Code in Parallel
Worktrees are one of several ways to parallelize Claude Code, and they're not always the right one. Here's how they compare to the alternatives:
Approach
What it isolates
Reach for it when
Multiple --worktree sessions
Files + branch, per terminal
You're driving 2-3 independent tasks yourself
Desktop app sessions
Files + branch, automatically
You want parallel sessions without juggling flags
Subagent isolation: worktree
Files, per Claude-spawned agent
Claude needs to fan out its 
own
 work without conflicts
Agent teams
Nothing by itself (adds coordination)
One big feature split across agents that must talk to each other
tmux + worktrees
Files + branch, many in one terminal
You live in the terminal and want all sessions in one window
Single session / Plan Mode
Nothing
The work is sequential, quick, or read-only
The mental model: 
worktrees isolate files, agent teams coordinate work.
 They compose - for a large feature you might run agent teams 
inside
 a worktree. If you only need one thing at a time, none of this applies; a normal session is the right call.
Coming soon
· In the writing queue
Draft
Claude Code Agent Teams for .NET - Parallel AI Agents for ASP.NET Core
Coordinate multiple AI agents with shared task lists and inter-agent messaging for larger features.
[Read next · Companion article
Plan Mode in Claude Code
Think before you build - the 4-phase workflow that prevents wasted effort with AI coding.](https://codewithmukesh.com/blog/plan-mode-claude-code/)
Real Workflow: Parallel Feature Development
Let me walk you through how I actually use worktrees in a typical development session with a .NET project.
The Setup
I'm working on an ASP.NET Core API. I have three things to do today:
Add a notifications feature (new endpoints, new entity, new service)
Fix a pagination bug in the Products endpoint
Refactor the authentication middleware to support API keys alongside JWT
In the old world, I'd do these sequentially - finish one, commit, start the next, eating a context switch each time. With worktrees, all three run in parallel in their own isolated checkouts, and the only serial part left is reviewing and merging at the end.
Three Terminals, Three Branches
I open one terminal per task:
Terminal window
claude -w notifications                            # the main feature (multi-file)
claude -w fix-pagination                           # the quick cursor bug fix
claude -w auth-refactor --permission-mode plan     # the risky refactor, in Plan Mode

Terminal 1 builds the full notifications feature. Terminal 2 fixes the bug; I commit and, on exit, tell Claude to keep the worktree so I can merge it later. Terminal 3 starts in 
Plan Mode
https://codewithmukesh.com/blog/plan-mode-claude-code/
 because the auth refactor is architecturally significant - Claude proposes a plan, I edit it with 
Ctrl+G
 , then it implements. All three run at once, and none of them can see or stomp on the others.
[Read next · Companion article
Claude Code Prompts for .NET Developers
Copy-paste prompts for feature work, testing, and modernization audits - one ready to go for each terminal you just opened.](https://codewithmukesh.com/blog/claude-code-prompts-dotnet/)
Merging and Cleaning Up
When all three are done I have three branches - 
worktree-notifications
 , 
worktree-fix-pagination
 , 
worktree-auth-refactor
 . I switch to my main directory and merge each one, resolving any conflicts (rare when features are independent) where I have full context:
Terminal window
git merge worktree-fix-pagination
git merge worktree-notifications
git merge worktree-auth-refactor

Cleanup is mostly automatic - if I exited each Claude session properly, the worktrees are already gone. If I closed a terminal abruptly, 
git worktree list
 shows the strays and 
git worktree remove <path>
 clears them.
Do Worktrees Share CLAUDE.md and Project Settings?
A question I got asked when I first wrote about Agent Teams: “Does each worktree session start from scratch?”
No.
 As of Claude Code v2.1.63, project configs and auto-memory are 
shared across all worktrees
 of the same repository. Your 
CLAUDE.md
 , 
.claude/settings.json
 , custom agents, skills - they all carry over. Each worktree session has the same project context as your main session.
What 
doesn't
 carry over:
Conversation history
 - Each worktree session starts a fresh conversation. It doesn't know what you discussed in another session.
Installed dependencies
 - 
node_modules/
 , 
bin/
 , 
obj/
 , virtual environments are per-worktree. Use WorktreeCreate hooks to automate installation.
Environment files
 - 
.env
 files are gitignored, so they won't appear in worktrees. Use a 
.worktreeinclude
 file (covered above) to copy them in automatically.
Build artifacts
 - Each worktree maintains its own build output.
[Read next · Companion article
CLAUDE.md for .NET Developers
Complete guide with production-ready templates for Clean Architecture, Minimal APIs, and enterprise .NET projects.](https://codewithmukesh.com/blog/claude-md-mastery-dotnet/)
.NET-Specific Gotchas Worktrees Won't Warn You About
Most worktree guides use Node or Python examples, so the .NET footguns never get mentioned. After running parallel worktrees on ASP.NET Core projects for months, these are the five that actually bite:
Gotcha
Why it happens
The fix
bin/
 / 
obj/
 are missing
Build output is gitignored and per-worktree
First 
dotnet build
 restores + rebuilds; automate with a 
dotnet restore
 WorktreeCreate hook (above)
User secrets are shared, not isolated
dotnet user-secrets
 writes outside the repo, keyed by 
UserSecretsId
Expected for shared dev secrets; just know branches can't have different secret values
Port collisions on 
dotnet run
Every worktree has the same 
launchSettings.json
Override with 
--urls
 , or assign a deterministic port in the hook
IDE opens the wrong worktree
Rider/Visual Studio key on the 
.slnx
 / 
.sln
 path
Open the worktree's solution explicitly, not your main one
EF Core migrations clobber each other
Worktrees isolate files, not your local database
Point divergent schema work at separate databases
Two of these are sharp enough to expand on.
User secrets are shared across every worktree.
 This surprises people. 
dotnet user-secrets
 doesn't store anything in your project - it writes to 
~/.microsoft/usersecrets/<UserSecretsId>/secrets.json
 (or 
%APPDATA%\Microsoft\UserSecrets\
 on Windows), keyed by the 
UserSecretsId
 in your 
.csproj
 ( 
Microsoft Learn
https://learn.microsoft.com/en-us/aspnet/core/security/app-secrets
). Every worktree of the same repo carries the same 
UserSecretsId
 , so they all read the 
same
 secrets. That's usually what you want - one dev connection string everywhere - but it means 
.worktreeinclude
 can't isolate them (the file isn't in the tree) and a branch can't have its own secret values without changing the ID. Your tracked 
appsettings.{Environment}.json
https://codewithmukesh.com/blog/environment-based-configuration-aspnet-core/
 files, on the other hand, are committed to Git, so they show up in every worktree automatically - it's only the gitignored secrets and 
.env
 files you have to think about.
EF Core migrations hit a shared database.
 Worktrees give you isolated 
files
, not an isolated 
database
. Run 
dotnet ef database update
 from two worktrees with diverging migrations against the same LocalDB or SQL Server instance and they'll fight over one schema. For parallel schema work, give each worktree its own database by changing the database name in its connection string. Doing this cleanly - a fresh, seeded database per branch wired through a WorktreeCreate hook - deserves its own walkthrough, which I'll cover in a follow-up. Until then, the rule is simple: don't run conflicting migrations against one shared dev database from parallel worktrees.
If you run dev servers in parallel, 
.NET Aspire
https://codewithmukesh.com/blog/aspire-for-dotnet-developers-deep-dive/
 sidesteps the port problem entirely - the AppHost assigns ports for every resource, so two worktrees running through Aspire don't collide.
SDK and Programmatic Usage
If you're automating with the Claude Agent SDK (formerly Claude Code SDK), the same isolation is available programmatically: set 
isolation: "worktree"
 when running agents to give each one its own copy of the repo. It's the right tool for automated PR review, batch migrations, and CI-driven refactoring - for example, spinning up isolated build environments as part of your 
CI/CD pipeline
https://codewithmukesh.com/blog/docker-guide-for-dotnet-developers/
 when 
containerizing .NET apps
https://codewithmukesh.com/blog/containerize-dotnet-without-dockerfile/
. As with the CLI, the worktree is auto-removed if the agent makes no changes; otherwise its path and branch come back in the result for you to review and merge.
Tips from Real Usage
A few habits that keep parallel work sane:
Plan dependencies first.
 If feature A needs feature B's migrations, don't run them in parallel - by default each worktree branches from the clean remote branch and can't see the other's changes. Build the dependency, merge it, then start A. (Or set 
worktree.baseRef
 to 
"head"
 so the worktree carries your unpushed work - see 
Choose the Base Branch
https://codewithmukesh.com/blog/git-worktrees-claude-code/#choose-the-base-branch
.)
Name worktrees for the work.
 
claude -w w1
 tells you nothing a week later; 
claude -w refactor-auth-middleware
 does.
Don't nest them.
 You can't create a worktree from inside a worktree - always start from your main repo directory.
Keep lifetimes short.
 Create, work, merge, clean up. Long-lived worktrees diverge from main and accumulate conflicts. More patterns like this in my 
20+ tips from a senior .NET developer
https://codewithmukesh.com/blog/20-tips-from-a-senior-dotnet-developer/
.
Changelog and Version History
The worktree feature has evolved across several 
Claude Code
https://docs.anthropic.com/en/docs/claude-code/overview
 releases (see the 
changelog on GitHub
https://github.com/anthropics/claude-code/releases
 for full details):
Version
What Changed
v2.1.49
Introduced the 
--worktree
 ( 
-w
 ) flag and subagent 
isolation: "worktree"
 support.
v2.1.50
Added 
isolation: worktree
 in agent frontmatter, plus the WorktreeCreate and WorktreeRemove hook events.
v2.1.63
Project configs and auto-memory now shared across worktrees of the same repository.
v2.1.143
Added the 
worktree.bgIsolation: "none"
 setting, letting background sessions edit the working copy directly for repos where worktrees are impractical.
v2.1.157
EnterWorktree
 can now switch between Claude-managed worktrees mid-session. Claude-managed worktrees are left unlocked when the agent finishes, so 
git worktree remove
 / 
prune
 can clean them up without 
--force
 .
Newer releases also added the 
.worktreeinclude
 file for copying gitignored config into worktrees, the 
worktree.baseRef
 setting for choosing the base branch, and 
--worktree "#1234"
 for branching directly from a pull request - all covered in the sections above.
If you're on a version older than v2.1.49, update with 
npm update -g @anthropic-ai/claude-code
 to get worktree support.
Key Takeaways
Git worktrees give you multiple working directories on different branches
, sharing the same repository history - no cloning needed.
Claude Code's --worktree flag
 manages the lifecycle automatically: creation, naming, session tracking, and cleanup.
Subagent isolation
 ( 
isolation: worktree
 ) lets Claude spawn parallel workers that each get their own copy of the repo - no file conflicts.
WorktreeCreate hooks and .worktreeinclude
 close the setup gap - hooks auto-install dependencies, and 
.worktreeinclude
 copies your gitignored 
.env
 and secrets into every new worktree.
Branch from a PR
 with 
claude --worktree "#1234"
 to review someone's pull request in isolation, and set 
worktree.baseRef: "head"
 when a worktree needs your unpushed local work.
Use worktrees when you need to switch context
 without losing state. Skip them for quick, focused tasks where isolation adds overhead without benefit.
Troubleshooting Common Worktree Issues
Worktree Fails to Create with “Branch Already Checked Out”
Git's safety mechanism prevents the same branch from being checked out in two places. This happens when you try to create a worktree for a branch that's already active somewhere. 
Fix:
 Use a different branch name, or remove the existing worktree that has the branch checked out with 
git worktree remove <path>
 .
—worktree Exits With a Trust Error on First Use
The first time you run 
claude --worktree
 in a directory, it can exit immediately and tell you to run 
claude
 in the directory first. This is the 
workspace trust check
https://code.claude.com/docs/en/security
 - Claude Code won't spin up an isolated session in a folder you haven't explicitly trusted. 
Fix:
 Run plain 
claude
 once in that directory and accept the trust dialog, then 
--worktree
 works. Non-interactive runs with 
-p
 skip the trust check, so 
claude -p --worktree
 proceeds without it.
A Worktree Session Lost My Commits
If you chose 
Remove
 at the exit prompt (or removed a worktree with uncommitted work), the branch and its commits are gone. 
Fix:
 Before removing, push or merge anything you want to keep - and when in doubt, choose 
Keep
 and clean up later with 
git worktree remove
 . Commits that were made but not merged may still be recoverable through 
git reflog
 if you act quickly, but don't rely on it.
Frequently asked
· 08 questions
Click to expand
01 What are Git worktrees in Claude Code?
Git worktrees in Claude Code are a built-in feature (shipped in v2.1.49) that lets you run multiple Claude Code sessions on the same repository without file conflicts. Each session gets its own isolated working directory and branch, all sharing the same Git history. You create them with claude --worktree name or the short flag claude -w name.
02 How do I create a worktree in Claude Code?
Run claude --worktree feature-name (or claude -w feature-name) from your repository. Claude Code creates a new directory at .claude/worktrees/feature-name/ with a branch called worktree-feature-name branching from your default remote branch. You can also ask Claude to start a worktree during an existing session by saying work in a worktree.
03 Do worktrees share my CLAUDE.md and project settings?
Yes. As of Claude Code v2.1.63, project configs and auto-memory are shared across all worktrees of the same repository. Your CLAUDE.md, .claude/settings.json, custom agents, and skills all carry over. What does not carry over is conversation history, installed dependencies, environment files, and build artifacts.
04 How does worktree cleanup work in Claude Code?
When you exit a worktree session without making changes, Claude automatically removes the worktree directory and branch. If you made changes or commits, Claude prompts you to keep or remove the worktree. Keeping preserves the directory and branch for later. Removing deletes everything, including uncommitted changes and commits.
05 How do I install dependencies automatically in new worktrees?
Use a WorktreeCreate hook in your .claude/settings.json. The hook runs a shell command when a worktree is created. For .NET projects, the command would run dotnet restore. For Node.js, npm install. The hook receives JSON input with the worktree name and must print the absolute path to the worktree directory on stdout.
06 How do I copy my .env file into a Claude Code worktree?
Add a .worktreeinclude file to your project root listing the gitignored files to copy, such as .env, .env.local, and any local secrets config. It uses .gitignore syntax and only copies files that are both matched and gitignored, so tracked files are never duplicated. Claude Code copies them into every new worktree created with --worktree, subagent worktrees, and desktop sessions. Note that .worktreeinclude is skipped if you configure a WorktreeCreate hook, since the hook replaces the default creation logic.
07 How do I review a pull request in a Claude Code worktree?
Run claude --worktree with the PR number prefixed by a hash, for example claude --worktree "#1234", or pass a full GitHub pull request URL. Claude Code fetches the PR branch and creates an isolated worktree at .claude/worktrees/pr-1234, so you can run and review the PR code without disturbing your current work.
08 When should I use worktrees versus Agent Teams in Claude Code?
Use worktrees when you want multiple independent Claude Code sessions working on separate tasks in parallel, each on its own branch. Use Agent Teams when the work requires coordination between agents through a shared task list and direct messaging. Worktrees provide file isolation. Agent Teams provide collaboration. For maximum parallelism on complex features, combine both.
Summary
Git worktrees are one of those features most developers never discover, and Claude Code's managed support makes them genuinely practical for daily .NET work. The 
--worktree
 flag handles the lifecycle, 
.worktreeinclude
 and a 
dotnet restore
 hook make a fresh worktree usable in seconds, subagent isolation lets Claude parallelize its own work, and the gotchas section above is the part no other guide will warn you about.
The pattern I keep coming back to: 
start in a normal session, and reach for claude -w the moment you need to context-switch without losing state.
 It's the difference between juggling and having extra hands.
If you want more Claude Code productivity patterns - including the tmux + worktree launch script I use to spin up three isolated sessions in one command - join the newsletter. I share real workflow breakdowns every Tuesday.
Happy Coding :)
Sponsor This newsletter reaches 9,735 .NET developers every Tuesday. 
Sponsor a Tuesday →
https://codewithmukesh.com/sponsor
 
← Previous lesson Plan Mode in Claude Code - Think Before You Build with AI
https://codewithmukesh.com/blog/plan-mode-claude-code/
Next lesson Skills in Claude Code - Reusable Prompts and Workflows →
https://codewithmukesh.com/blog/skills-claude-code/
Work with me
Want this working inside your company?
I consult with teams on adopting Claude Code and AI-assisted development: setting up the workflows, training developers, and shipping real projects with it. If your company wants help implementing this, let's talk.
Book a consulting call
https://codewithmukesh.com/contact/?intent=consulting&subject=AI+%2F+Claude+Code+Consulting&message=Hi+Mukesh%2C%0A%0AWe%27re+looking+at+bringing+Claude+Code+%2F+AI-assisted+development+into+our+team.+Here%27s+our+context%3A%0A%0ACompany%3A%0ATeam+size%3A%0AWhat+we%27re+trying+to+do%3A%0A%0AWhat+does+working+with+you+look+like%3F
For .NET tool vendors
Reach 9,735 .NET developers next Tuesday - $500.
 53.6% open rate. 8.99% CTR. Only 2 sponsor slots per issue.
See open Tuesday slots →
https://codewithmukesh.com/sponsor
More from the archive.
View all articles
https://codewithmukesh.com/blog
[
 N° 01 Read → claude · May 23, 2026
Skills in Claude Code - Reusable Prompts and Workflows
](https://codewithmukesh.com/blog/skills-claude-code/)
[
 N° 02 Read → claude · Apr 7, 2026
Anatomy of the .claude Folder - Every File Explained (2026)
](https://codewithmukesh.com/blog/anatomy-of-the-claude-folder/)
[
 N° 03 Read → claude · Feb 25, 2026
Plan Mode in Claude Code - Think Before You Build with AI
](https://codewithmukesh.com/blog/plan-mode-claude-code/)
[
 N° 04 Read → claude · Jun 8, 2026
20 Advanced Claude Code Tips for .NET Developers
](https://codewithmukesh.com/blog/claude-code-tips-advanced/)
The Tuesday Dispatch
Every Tuesday.
One email.
Subscribe free
Keep digging. 8 more from the archive.
[05 claude · Jul 2026
Claude Code Prompts for .NET Developers - A Copy-Paste Library for Every Workflow Stage
](https://codewithmukesh.com/blog/claude-code-prompts-dotnet/)
[06 claude · Mar 2026
Anatomy of a Claude Code Session - What Happens Under the Hood
](https://codewithmukesh.com/blog/anatomy-claude-code-session/)
[07 claude · Jun 2026
I Built a Claude Code Skill That Scaffolds My .NET Architecture
](https://codewithmukesh.com/blog/claude-code-skill-scaffold-dotnet-architecture/)
[08 claude · Mar 2026
Prompt Engineering for Claude Code - The .NET Developer's Guide
](https://codewithmukesh.com/blog/prompt-engineering-claude-code-dotnet/)
[09 claude · Jan 2026
Claude Code Tutorial for Beginners - Complete 2026 Guide
](https://codewithmukesh.com/blog/claude-code-for-beginners/)
[10 dotnet · Jan 2026
CLAUDE.md for .NET - The Perfect Setup with Copy-Paste Templates
](https://codewithmukesh.com/blog/claude-md-mastery-dotnet/)
[11 architecture · Feb 2026
GitFlow vs GitHub Flow vs Trunk-Based Development Guide
](https://codewithmukesh.com/blog/git-workflows-gitflow-vs-github-flow-vs-trunk-based-development/)
[12 dotnet · Jul 2026
Identity API Endpoints in ASP.NET Core: When to Use Them (.NET 10)
](https://codewithmukesh.com/blog/identity-endpoints-aspnet-core/)
What's your take?
Push back, share a war story, or ask the obvious question someone else is wondering. I read every comment.
View on GitHub
https://github.com/codewithmukesh/discussions/discussions
Loading comments…
 
Written by
Mukesh Murugan
Software Engineer
← All articles
https://codewithmukesh.com/blog/
Thanks for reading. I write one deep .NET and Claude Code piece a week. If this was useful, the newsletter is where the next one lands first.
Follow on LinkedIn
https://www.linkedin.com/in/iammukeshm
 
X
https://twitter.com/intent/user?screen_name=iammukeshm
 
← All articles
https://codewithmukesh.com/blog/
Building something .NET developers should know about? 
Sponsor the newsletter.
https://codewithmukesh.com/sponsor
Contents 19
On this page
· 19 sections
Jump to a section.
01 What Are Git Worktrees?
https://codewithmukesh.com/blog/git-worktrees-claude-code/#what-are-git-worktrees
02 How Do Claude Code Worktrees Differ from Plain Git Worktrees?
https://codewithmukesh.com/blog/git-worktrees-claude-code/#how-do-claude-code-worktrees-differ-from-plain-git-worktrees
03 Creating and Using Worktrees
https://codewithmukesh.com/blog/git-worktrees-claude-code/#creating-and-using-worktrees
04 How Does Worktree Cleanup Work in Claude Code?
https://codewithmukesh.com/blog/git-worktrees-claude-code/#how-does-worktree-cleanup-work-in-claude-code
05 How Does Subagent Worktree Isolation Work?
https://codewithmukesh.com/blog/git-worktrees-claude-code/#how-does-subagent-worktree-isolation-work
06 How Do WorktreeCreate and WorktreeRemove Hooks Work?
https://codewithmukesh.com/blog/git-worktrees-claude-code/#how-do-worktreecreate-and-worktreeremove-hooks-work
07 Worktrees + .gitignore
https://codewithmukesh.com/blog/git-worktrees-claude-code/#worktrees--gitignore
08 How Do I Get My .env Files Into Worktrees?
https://codewithmukesh.com/blog/git-worktrees-claude-code/#how-do-i-get-my-env-files-into-worktrees
09 When Should You Use Git Worktrees in Claude Code?
https://codewithmukesh.com/blog/git-worktrees-claude-code/#when-should-you-use-git-worktrees-in-claude-code
10 Worktrees vs. the Other Ways to Run Claude Code in Parallel
https://codewithmukesh.com/blog/git-worktrees-claude-code/#worktrees-vs-the-other-ways-to-run-claude-code-in-parallel
11 Real Workflow: Parallel Feature Development
https://codewithmukesh.com/blog/git-worktrees-claude-code/#real-workflow-parallel-feature-development
12 Do Worktrees Share CLAUDE.md and Project Settings?
https://codewithmukesh.com/blog/git-worktrees-claude-code/#do-worktrees-share-claudemd-and-project-settings
13 .NET-Specific Gotchas Worktrees Won't Warn You About
https://codewithmukesh.com/blog/git-worktrees-claude-code/#net-specific-gotchas-worktrees-wont-warn-you-about
14 SDK and Programmatic Usage
https://codewithmukesh.com/blog/git-worktrees-claude-code/#sdk-and-programmatic-usage
15 Tips from Real Usage
https://codewithmukesh.com/blog/git-worktrees-claude-code/#tips-from-real-usage
16 Changelog and Version History
https://codewithmukesh.com/blog/git-worktrees-claude-code/#changelog-and-version-history
17 Key Takeaways
https://codewithmukesh.com/blog/git-worktrees-claude-code/#key-takeaways
18 Troubleshooting Common Worktree Issues
https://codewithmukesh.com/blog/git-worktrees-claude-code/#troubleshooting-common-worktree-issues
19 Summary
https://codewithmukesh.com/blog/git-worktrees-claude-code/#summary
Weekly .NET tips · free
Subscribe ↗
Newsletter
· Tue 7 PM IST
Get weekly .NET tips.
9,735 subs
· +355 this week
Your email address Subscribe ↗
Newsletter
stay ahead in .NET
One email every Tuesday at 7 PM IST. One topic, deep. The week's articles. No filler.
Tutorials Architecture DevOps AI
Your email address Subscribe
Join 9,735 developers · Delivered every Tuesday
codewith mukesh
https://codewithmukesh.com/
.NET, Cloud & AI. Simplified for developers.
Navigate
Home
https://codewithmukesh.com/
Blog
https://codewithmukesh.com/blog
Courses
https://codewithmukesh.com/courses
Resources
https://codewithmukesh.com/blog/git-worktrees-claude-code/
Sponsor
https://codewithmukesh.com/sponsor
Contact
https://codewithmukesh.com/contact
Resources
Newsletter
https://codewithmukesh.com/newsletter
Courses
https://codewithmukesh.com/courses
Clean Architecture Template
https://codewithmukesh.com/resources/clean-architecture-template
Interview Questions PDF
https://codewithmukesh.com/resources/dotnet-webapi-interview-questions
.NET Claude Kit
https://codewithmukesh.com/resources/dotnet-claude-kit
About
https://codewithmukesh.com/about
Sponsor
https://codewithmukesh.com/sponsor
AI Consulting
https://codewithmukesh.com/contact/?intent=consulting&subject=AI%20%2F%20Claude%20Code%20Consulting
Contact
https://codewithmukesh.com/contact
© 2026 Mukesh Murugan. All rights reserved.
Subscribe to the newsletter
https://codewithmukesh.com/newsletter
Subscribed
· Next drop · Tue 7 PM IST Tue 7 PM IST
You're in. Welcome to the crew.
Tuesday's issue lands in your inbox at 7 PM IST. One last step: confirm your email so it actually arrives.
01 · Check your inbox
Gmail
https://mail.google.com/mail/u/0/#search/from%3Acodewithmukesh
 
Outlook
https://outlook.live.com/mail/0/inbox
 
Yahoo
https://mail.yahoo.com/
02 · Every Tuesday
Benchmarks, architecture insights, and production tips that never make it to the blog.
Keep reading
The Tuesday Dispatch
· Free forever
Every Tuesday, one email.
.NET tips, benchmarks, and architecture insights. Straight from production.
01 A weekly hot take
02 Quick wins, copy-paste ready
03 Exclusive benchmarks
Your email Subscribe free
9,735 developers
· +355 this week
· No spam 
Preview an issue →
https://codewithmukesh.com/newsletter
Search articles 
ESC
Try
Clean Architecture EF Core JWT Docker Claude Code Benchmarks
Jump to
01 All articles →
https://codewithmukesh.com/blog
 
02 The Tuesday Dispatch →
https://codewithmukesh.com/newsletter
 
03 Free .NET courses →
https://codewithmukesh.com/courses
 
04 Browse by category →
https://codewithmukesh.com/categories
No matches
Nothing found in the archive. Try a broader keyword, or browse 
all articles →
https://codewithmukesh.com/blog
Searching the archive… 
↑
 
↓
 navigate 
↵
 select
Powered by Orama
Privacy notice
· 30s read
Cookies, but only the useful ones.
I use cookies to understand which articles get read and which CTAs actually work. No third-party advertising trackers, ever. 
Read the privacy policy →
https://codewithmukesh.com/privacy-policy
Essentials only Accept all
