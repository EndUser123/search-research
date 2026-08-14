---
title: "Can you read the text on the screen in the screenshot?  What is it about?"
date: "2026-03-16"
mode: "COPILOT"
uuid: "65dc2982-98de-4fff-89ec-d5ebac668d45"
entry_count: 7
---

## Human

Can you read the text on the screen in the screenshot?  What is it about?

## Assistant

I can’t directly read the small on‑screen text from this screenshot with enough fidelity to reliably transcribe it word‑for‑word, but I can infer its topic from what’s legible.[1]

The visible highlighted block is instructing someone (likely an engineer or agent) to perform “Full State Verification” after completing some logic or code.  It emphasizes defining a “Source of Truth” (such as a database, file, global variable, or UI state), then running the logic and doing a separate read operation on that source to confirm the data was processed correctly.  The text also mentions doing “Boundary & Edge Case Audit” by manually simulating edge cases (empty inputs, maximum limits, invalid formats), and printing the state of the system before and after actions to prove the outcome.[1]

Further down, it stresses manually verifying outputs by checking databases/tables or other physical proof that the operation actually produced the expected result, not just trusting return values.  It frames this as manual testing to ensure everything works, encourages testing both happy paths and edge cases, and talks about identifying root causes when errors appear and re‑running tests after fixes.  Overall, the text is about rigorous manual verification and validation practices for a system or agent, focusing on state inspection, edge‑case testing, and ensuring no lingering issues remain.[1]

Is your main goal to get a cleaner transcription for reuse in docs, or are you trying to turn these ideas into a concrete testing checklist or agent behavior spec?

## Human

"Make sure you always check subagents work personally yourself and don't rely on their responses to be correct without verifying/validating what they've done yourself.
/home/cabdru/datalab/docs2/constitution.md. RUN ALL SUBAGENTS Synchronously. ENSURE CORRECT ORDER of agent launch, don't launch an agent if it needs another agents
output to accomplish its mission. ultra think. You MUST read all of the documents I listed. ABSOLUTELY NO BACKWARDS COMPATIBILITY. the system needs to work after
changes or fail fast so it can be debugged.
/home/cabdru/datalab/docs2/SHARED-MIND-AGENT-PROTOCOL.md /home/cabdru/datalab/docs2/borisflow.md read these files.
you need to use subagents and optimally use the Claude flow system and memories to coordinate all of the agents doing this in a way that they are all working
together, sharing memories and knowing which memories to access so you can use 10 agents but with memories they can all act as 1. spawn them synchronously. MAKE SURE
ALL SUBAGENTS ARE TELLING YOU WHAT MEMORIES THEY LEFT SO YOU KNOW WHERE TO TELL THE NEXT SUBAGENT YOU CREATE TO LOOK FOR MEMORIES ENSURE CORRECT ORDER of agent
launch, don't launch an agent if it needs another agents output to accomplish its mission. ultra think. You MUST read all of the documents I listed.

After completing the logic, you must perform Full State Verification. Do not rely on return values alone. You must Define the 'Source of Truth': Identify where the
final result is stored (e.g., a database, a file, a global variable, or a UI state).Execute & Inspect: Run the logic, then immediately perform a separate 'Read'
operation on the Source of Truth to verify the data was processed correctly. Boundary & Edge Case Audit: Manually simulate 3 edge cases (e.g., empty inputs, maximum
limits, or invalid formats). For each, you must print the state of the system before and after the action to prove the outcome. Evidence of Success: Provide a log
showing the actual data residing in the system after execution.
IMPORTANT: You MUST check the database or tables or anything that might show physical proof that what you did actually worked then you need to check it to ensure the
outputs are what they should be on the manual tests you are running. if something is saved to a database or table or graph etc you need to actually manually verify
they exist, you should know what the output should be and you need to go look to see if its there. if there is some way you can validate the outcome for whatever it
is you are manually testing then you MUST MANUALLY VERIFY THE OUTPUT BY CHECKING IF THE OUTPUT EXISTS. Think about what you are testing, think about what the outcome
of your test should be and if there is any way for you to physically verify its done what its done then you MUST check that to ensure it worked. In computing, there's
almost always a trigger event that initiates process X, which in turn leads to outcome Y. Because the trigger event causes X, it can be identified, measured, or
observed when it occurs. Likewise, whatever Y produces can be tracked or analyzed in some way, since every triggered event exists to produce a specific, intended
outcome. I need full manual testing to ensure they all work. i need full happy path testing and edge case manual testing. I need you to think of synthetic
information that you can use so you'll know the input and expected outputs and run synthetic information through the commands and test for what you know the expected
output should be, that means looking for how it shows up in a database or however that might show itself. any time you see any errors or anything
be functioning correctly you need to stop and identify the root cause of the problem and fix it and update any tests and redo manual tests to e
working and not causing issues any longer. Use the code-simplifier subagent and have it review all the work that was done for the task and ref

to not

/home/cabdru/datalab/docs2/LICENSE-SYSTEM-ARCHITECTURE.md you MUST read this to understand he systm.

/pushrepo when pushing the repo ensure that all requirements in /home/cabdru/steveprog/docs/tasks/TASK-STAKEHOLDER-202.md
update this with any information it needs to best be able to accomplish the task based off what you've learned so that it is better aware of
project. include anything you've learned that you think would be helpful to an ai agent coding assistant that knows nothing about what has ha
anything about the project so that they can look at this and perfectly implement it. to do this you must ensure there is no ambiguity in
task against the current codebase. Identify any discrepancies, particularly regarding file paths, names, or structures that have chan
all references align with the project's actual current state. Also you can review git history to get a better idea of what has happr
BACKWARDS COMPATIBILITY. the system needs to work after changes or fail fast so it can be debugged. Do not create workarounds or

vthina"

The youtube host is saying this:
"The AI Vibe Coding Mistake We All Make
[(00:00:00)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=0) Hi, in this video I'm going to give you some vibe coding tips. And this is the one tip that has changed everything for [(00:00:08)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=8) me and how I develop with AI tools. As soon as I started doing this, everything changed for me. Literally [(00:00:17)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=17) everything. And the reason this is is because we use AI and we use AI to code or build [(00:00:24)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=24) programs or whatever you're building, right? And then we're all in agreement that those outcomes need to be verified [(00:00:32)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=32) and validated. And often times people will say, well, this needs to be done by a human, right? But what I have [(00:00:38)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=38) highlighted here, the prompt that I use that's changed everything is just taking
The Full State Verification Prompt
[(00:00:43)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=43) what a human would do to verify that AI's output and making the AI do it. And it's relatively simple because all [(00:00:52)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=52) software works the same. And all software can be tested in the same exact way, right? Every software [(00:01:03)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=63) has trigger events. Those trigger events trigger. So, so say something triggers X, right? And you know what X is, you [(00:01:10)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=70) know what triggers X, you know what goes into X, and then X goes through some sort of processing transformation and [(00:01:18)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=78) then Y comes out the other side. All right? So I know what is that transformation is supposed to be and I [(00:01:26)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=86) know that if I put this data in at X then Y should be the outcome. So I have the AI go put in X see what Y is verify [(00:01:36)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=96) the output. Literally the same thing a human would do. You have the AI do this for every step of your development and [(00:01:43)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=103) things just work. All of my nightmares, all of my headaches with AI coding, all went away with this one prompt and [(00:01:53)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=113) partially has to do with the smarter models of course, but this is a big game changer. So, let's [(00:01:59)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=119)
read it. What is happening here? So,
Breaking Down the Code Verification Process
[(00:02:02)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=122) this is the prompt that I'm feeding to AI to get it to do this manual verification just like a human would do, [(00:02:09)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=129) right? I tell it you must perform full state verification. Do not rely on return values alone. You must define the [(00:02:16)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=136) source of truth. Identify where the final result is stored. A database, a file, a global variable or a UI state. [(00:02:23)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=143) Now we need to execute and inspect. Run the logic. Then immediately perform a separate read operation on the source [(00:02:29)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=149) source of truth to verify the data was processed correctly. Boundary and edge case audit. Manually simulate three edge [(00:02:37)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=157) cases. Empty inputs, maximum limits, invalid formats, things like this. For each you must print the state of the [(00:02:44)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=164) system before and after the action to prove the outcome. Evidence of success. Provide a log showing the actual data [(00:02:50)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=170) residing in the system. After execution, you must check the database or tables or anything that might show physical proof [(00:02:57)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=177)
that what you did actually worked. Then you need to check it to ensure the outputs are what they should be on the [(00:03:05)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=185) manual test you are running. If something is saved to a database or table or graph, whatever it is, you need [(00:03:11)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=191) to manually verify they exist. You should know what the output should be and you need to go look to see if it's [(00:03:18)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=198) there. If there is some way you can validate the outcome for whatever it is you are manually testing, then you must [(00:03:25)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=205) manually verify the output by checking if the output exists. Think about what you are testing. Think about what the [(00:03:30)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=210) outcome of your test should be. And if there is any way for you to physically verify it's done what it's done, then [(00:03:35)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=215) you must check that to ensure it worked. In computing, there's almost always a
How to Test Edge Cases with AI
[(00:03:38)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=218) In computing, there's almost always a trigger event that initiates process X, which in turn leads to outcome Y. [(00:03:44)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=224) Because the trigger event causes X, it can be identified, measured, or observed when it occurs. Likewise, whatever Y [(00:03:51)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=231) produces can be tracked or analyzed in some way. Since every triggered event exists to produce a specific intended [(00:03:58)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=238) outcome, I need full manual testing to ensure they all work. I need full happy path testing and edge case manual [(00:04:05)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=245) testing. I need you to think of synthetic information that you can use so you'll know the input and expected [(00:04:10)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=250) outputs and run synthetic information through the commands and test for what you know the expected output should be. [(00:04:16)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=256) That means looking for how it shows up in a database or however that might show itself. Anytime you see any errors or [(00:04:22)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=262) anything that appears to not be functioning correctly, you need to stop, identify the root cause of the problem, [(00:04:26)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=266)
and fix it and update any tests or redo manual tests to ensure the fix is working and not causing issues any [(00:04:31)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=271) longer. Use the code simplifier agent to
Using the Anthropic Code Simplifier Agent
[(00:04:34)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=274) review all the work. Code simplifier agent is really cool. Anthropic put this out. It's on their website. It is a [(00:04:40)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=280) public agent they gave out. Like all of their uh engineers use it. It's very good at simplifying your code. It's it's [(00:04:48)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=288) it's great. It's amazing. There's really no need to no reason to not use it unless you're worried about tokens. And [(00:04:55)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=295) another thing that I found to be quite interesting is Claude codes choice of sub agent. I have many sub
Why Claude Loves the Sherlock Holmes Agent
[(00:05:05)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=305) agents. I have like roof going and I got all of these different sub aents. I have a lot of sub agents and of say 150 sub [(00:05:13)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=313) agents, the Sherlock Holmes sub agent gets used all the time, right? Like more than [(00:05:21)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=321) pretty much any other agent that I have. And the difference between the Sherlock Holmes agent and all my other agents is [(00:05:28)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=328) my other agents tell the AI what to do, right? That's the sub agent prompt. But the Sherlock Holmes agent prompts the AI [(00:05:36)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=336) on how to think. Okay, so Claude really likes this agent that has been given the mental [(00:05:46)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=346) uh structure or architecture uh mirroring Sherlock Holmes, right? So it's how does Sherlock Holmes approach [(00:05:53)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=353) problems and solve problems and this thought process Claude really likes. So these are the things that have really [(00:06:01)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=361) helped me out a lot is the Sherlock Holmes agent for just finding problems, right?
The Secret to Indestructible Architecture
[(00:06:08)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=368) this full state verification every time you do implement a new feature or anything just as you're [(00:06:15)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=375) building one step of the way you need the AI to do full manual verification of everything right and as long as you're [(00:06:21)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=381) doing this and you're testing happy path and edge case test AI is going to catch a lot of its errors a lot of the [(00:06:27)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=387) problems with the system and the system will just will just work right so I mean that's the best way to put it the system [(00:06:34)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=394) will just work you need to build slowly make sure you're doing manual testing along the way. And as long as you keep [(00:06:40)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=400) building on top of solid building blocks, then your architecture will be solid itself. And this is what I do to [(00:06:47)](https://www.youtube.com/watch?v=xskRn_C6Sog&t=407) make sure that I am building on solid blocks along the way."

## Assistant

The on‑screen text is a long system prompt plus instructions that implement the “Full State Verification” idea from the video transcript you pasted: making the AI test and verify its own work like a careful human tester would.[1][2]

### What the text on screen says

You already reconstructed almost all of the visible text correctly in your quoted block.  The highlighted part on screen matches the “Full State Verification Prompt” section from the YouTube transcript: define a **source** of truth, run the logic, do a separate read, simulate at least three edge cases, print state before/after, and log evidence of success.  It also includes the follow‑up paragraph about manually checking databases/tables/graphs, verifying that expected outputs actually exist, thinking in terms of trigger event X leading to outcome Y, and using synthetic inputs to run happy‑path and edge‑case tests while fixing root causes and rerunning tests as needed.[2][1]

Outside the highlighted area, the prompt adds coordination rules for Claude subagents: run all subagents synchronously in the correct order, don’t launch an agent that depends on another’s output until that output exists, share and record memories so later agents know where to look, and treat certain repo docs as required reading (constitution, shared‑mind protocol, borisflow, license architecture, stakeholder task doc).  It also repeats “ABSOLUTELY NO BACKWARDS COMPATIBILITY, the system needs to work after changes or fail fast so it can be debugged,” and says to use a code‑simplifier subagent to review completed work.[2]

### What it’s about

Conceptually, this text is:

- A “master” system/agent prompt that:
  - Describes how to orchestrate many Claude subagents and shared memories in a repo.[3][2]
  - Forces strict, synchronous, dependency‑aware execution instead of loose “vibe coding” with agents.[4][2]

- A testing and verification protocol:
  - Encode human‑style manual verification (define source of truth, run, read, edge cases, logs) as mandatory behavior for the AI itself.[1][2]
  - Require persistent, concrete evidence (database rows, files, logs) instead of trusting return values or summaries.[5][2]

- A workflow/discipline layer:
  - Keep stakeholder requirement docs up to date, align file paths and structures with reality, and avoid hacks or workarounds that hide bugs.[2]
  - Use a dedicated code‑simplifier agent (Anthropic’s internal one) for cleanup and maintainability.[6][7][2]

In other words, it’s a combined architecture + verification prompt designed to turn Claude and its subagents into a self‑auditing engineering system that tests itself thoroughly instead of just shipping “vibe coded” changes.[1][2]

If you want, I can turn this into a compact, reusable agent spec/checklist you can drop into Claude Code or your own orchestrator.

## Human

Is this concept a best practice?  Does it work?

## Assistant

Short answer: it’s directionally a best practice, but it’s not a silver bullet; it works very well in some contexts and is overkill or fragile in others.[1][2][3]

### Why the concept is sound

- Having AI explicitly define a **source** of truth and then read from it to verify behavior mirrors how good human testers work (state‑based verification, not just checking return values).[2][1]
- Requiring synthetic test data, happy‑path + edge‑case coverage, and insisting on evidence in logs or databases aligns with mainstream QA and eval patterns (unit tests, state checks, outcome verification).[1][2]
- Using structured prompts to push AI into deterministic, stepwise verification improves reliability versus “vibe coding” where you just glance at outputs and hope they’re right.[4][5][1]

### Where it clearly helps

- Agentic coding flows: if the agent is allowed to edit code, run tools, etc., forcing it to run tests, inspect DB/file state, and justify success tends to catch many obvious failures before you ever see them.[3][2]
- Regression‑sensitive systems: combining this style of “full state verification” with automated evals (unit tests, state_check graders, CI) is very much in line with how serious teams guard against regressions when they let agents touch code.[2]
- Knowledge‑poor but tool‑rich tasks: when the agent can actually query the DB, hit the API, or run the test suite, this pattern lets it close the loop instead of hallucinating.[3][2]

### Limitations and pitfalls

- It depends completely on tools and observability: if the agent can’t actually run tests, inspect logs, or query state, you just get *text describing* verification, not verification itself.[1][2]
- Manual‑style probing is slower and can be brittle; if schemas or paths change often, hard‑coded “check this table X for field Y” instructions can go stale and cause false alarms or busywork.[1]
- It doesn’t replace human QA, security analysis, or systematic evals; current best practice is still: AI runs tests and self‑checks, but humans design eval suites, gate high‑risk changes, and review failures.[6][2][3]

### How I’d frame it as practice

- FACT: For AI coding/testing, explicit prompts that force the model to design tests, run them, and verify outputs against real system state are aligned with emerging industry guidance and large‑scale eval practices.[6][2][1]
- CONSENSUS: This is a strong pattern for increasing reliability of agentic workflows, especially when combined with automated tests and CI, but still requires human oversight and good tooling.[6][2][3]
- SPECULATION (high confidence): Your “full state verification” protocol is likely to materially reduce undetected failures in an AI‑driven dev workflow, especially compared to naive “ask AI to write code, then ship it” patterns, but it will need tailoring per project to avoid friction and brittleness.[2][1]

If you tell me what kind of system or repo you’re planning to apply this to (size, language, infra), I can suggest a minimal version of this protocol that gives you most of the benefit with the least ceremony.

## Human

It's for python and typescript.  Is there a combined prompt & hook solution?

## Assistant

Yes, you can absolutely turn this into a combined “prompt + hooks” setup for Python and TypeScript; nothing off‑the‑shelf does exactly your spec, but the pieces are there and play nicely together.[1][2][3]

### Overall pattern

- Put the **Full State Verification** logic into a reusable system prompt (or subagent spec) that every coding session inherits.[4][5]
- Use **Claude Code hooks** (Start/BeforeTool/Stop) to enforce that: tests are generated or present, tests are run, and state/log checks happen before the agent is allowed to say it’s “done.”[2][3][1]
- Wire hooks to deterministic commands: `pytest` / `ruff` / `mypy` for Python, `vitest`/`jest`/`playwright` + `eslint`/`tsc` for TypeScript; have the hook feed the results back into the agent for another pass if anything fails.[6][4]

### Concrete shape (high level)

You’d typically do something like:

- System prompt (or shared subagent): your full constitution + shared‑mind rules + “Full State Verification” block, framed as “for every change, you must: define source of truth, run code, run tests, inspect DB/files, log evidence, probe 3 edge cases.”[5][4]
- `Stop` hook: when the agent thinks it’s done, the hook runs `npm test` / `pytest`, checks exit codes and maybe parses junit JSON, then either:  
  - allows completion if all tests pass and verification logs exist, or  
  - injects a blocking message like “Tests X failed / no verification logs; fix and rerun” and forces another iteration.[7][3][1][4]
- Optional `BeforeTool` hook: whenever the agent tries to call tools that mutate code or DB migrations, enforce “no change without updating/creating tests touching this file/module.”[3][8][2]

### Python + TypeScript specifics

- For Python: standardize on `pytest`, `ruff`, `mypy`, and possibly a small “state probe” CLI (e.g., `python scripts/verify_state.py --scenario foo`) that hooks can call to implement your “source of truth” checks.[6][4]
- For TypeScript: `tsc --noEmit`, `eslint`, plus your test runner; again, a thin `node scripts/verify-state.ts` can wrap DB/file checks or HTTP health checks so hooks stay language‑agnostic.[6]
- Hooks just orchestrate commands; your prompt forces the agent to *write and maintain* those verification scripts and tests as part of every change.[1][3]

### What exists vs what you must build

- Existing examples (blog posts, sample repos) show hooks used to: block commits without tests, run full test suites before “done,” or loop until all test cases pass.[9][8][7][4][3]
- None of them ship a drop‑in, repo‑agnostic “Full State Verification + shared‑mind subagents” solution; you’ll need a thin glue layer that: encodes your rules in the system prompt, defines a few standard scripts/commands per language, and configures hooks to call them.[8][2][5][3]

If you share your current repo layout (where tests live, how you run them for Python/TS), I can sketch an explicit hooks JSON + prompt scaffold you can paste into Claude Code and adapt.  

## Human

Is the above related to this?
"
● Based on our analysis, the repeating failure pattern is:

  Evidence Ledger vs Reality Gap: Tasks marked "done" when actual implementation doesn't exist.

  ---
  Stage 2: Extract Pattern

  Class of problem: Detection/Verification Gap

  Evidence is recorded (test files, implementation files listed) but the actual files don't contain the expected changes.
  The system checks "did we record evidence?" not "does the evidence match reality?"

  ---
  Stage 3: Propose Changes

  ---
  Analysis: Improve Completion Verification System

  Failures Identified (from CKS)

  Failure 1: VS Configuration Missing (recent discovery)
  - What happened: Tasks marked "done" in evidence ledger, but VS configuration sections were never added to deep.md and
  fast.md
  - Fix: Manual verification via /verify discovered the gap
  - Pattern type: Detection gap - system didn't validate actual file content

  Failure 2: Evidence Ledger Without Reality Check
  - What happened: EvidenceManager.mark_done() checks only that evidence types exist, not that implementation matches
  evidence
  - Pattern type: Detection gap - evidence can be recorded without verification

  Pattern

  Evidence Completeness ≠ Implementation Reality: The system verifies all required evidence types are recorded (RED, GREEN,
   REFACTOR, VERIFY) but doesn't validate that the claimed changes actually exist in the referenced files.

  ---
  Proposed Changes

  Change A: File-Content Verification Before mark_done()

  File: P:\\.claude\\skills\\code\\utils\\evidence.py

  Logic: Extend mark_done() to verify actual file content before allowing completion:

  def mark_done(self, task_id: str, verify_content: bool = True):
      """Mark task as done after verifying evidence and implementation."""
      can_done, msg = self.can_mark_done(task_id)
      if not can_done:
          raise ValueError(msg)

      if verify_content:
          # NEW: Verify actual file content matches evidence claims
          missing = self._verify_implementation_exists(task_id)
          if missing:
              raise ValueError(
                  f"Cannot mark task done: implementation missing for {len(missing)} file(s).\\n"
                  f"Missing: {', '.join(missing)}\\n"
                  f"Evidence claims these files exist with changes, but verification failed."
              )

      ledger = self._load_ledger()
      ledger["tasks"][task_id]["done"] = True
      ledger["tasks"][task_id]["done_at"] = datetime.now().isoformat()
      self._save_ledger(ledger)

  def _verify_implementation_exists(self, task_id: str) -> list[str]:
      """Verify that files claimed in evidence actually exist with expected content.

      Returns list of files that failed verification (empty if all pass).
      """
      ledger = self._load_ledger()
      task = ledger["tasks"].get(task_id)
      if not task:
          return []

      evidence = task.get("evidence", {})
      missing_files = []

      # Check RED evidence: test files should exist
      red = evidence.get("RED", {})
      if red.get("completed"):
          for test_file in red.get("test_files", []):
              if not Path(test_file).exists():
                  missing_files.append(f"TEST: {test_file}")

      # Check GREEN evidence: implementation files should exist
      green = evidence.get("GREEN", {})
      if green.get("completed"):
          for impl_file in green.get("impl_files", []):
              if not Path(impl_file).exists():
                  missing_files.append(f"IMPL: {impl_file}")

      return missing_files

  Test: Create task with evidence pointing to non-existent files → mark_done() should raise

  Success: "Evidence recorded but file doesn't exist" prevented from claiming done

  ---
  Change B: Post-ToolUse Content Verification Hook

  File: P:\\.claude\\hooks\\posttooluse\\implementation_verifier.py (NEW)

  Logic: After Write/Edit, verify that claimed changes actually match file content:

  """PostToolUse hook that verifies implementation matches evidence claims."""

  from pathlib import Path
  from posttooluse.base import PostToolUseHook

  class ImplementationVerifier(PostToolUseHook):
      """Verifies that Write/Edit operations create claimed content."""

      env_var = "IMPLEMENTATION_VERIFIER_ENABLED"
      default_enabled = True
      tool_matcher = {"Write", "Edit"}

      def process(self, tool_name, tool_input, tool_response):
          """Verify file was actually written/edited with expected content."""
          # Extract file path from input
          file_path = tool_input.get("file_path") or tool_input.get("filePath")
          if not file_path:
              return {"passed": True}

          # Check if file exists after Write/Edit
          path = Path(file_path)
          if not path.exists():
              return {
                  "passed": False,
                  "injection": f"⚠️ FILE NOT CREATED: {file_path}\\n"
                  f"Claimed to write file, but it doesn't exist on disk."
              }

          # For evidence-claimed files, verify expected content exists
          # (This would integrate with evidence ledger for advanced verification)

          return {"passed": True}

  Test: Write file, verify hook confirms existence; try to mark done without actual changes

  Success: Catches "claimed done but file empty/missing" before stop

  ---
  Change C: Atomic Verify-Then-Commit Pattern

  File: P:\\.claude\\skills\\code\\scripts\\validate_done_claim.py (EXTEND)

  Logic: Add content verification to TSR validation:

  def validate_implementation_claims(
      evidence_mgr,
      task_ids: Optional[list[str]] = None,
  ) -> dict:
      """Verify that claimed implementations actually exist.

      Returns dict with:
          - verified: list of tasks with verified implementations
          - missing_files: dict mapping task_id → list of missing files
      """
      ledger = evidence_mgr._load_ledger()
      if task_ids is None:
          task_ids = list(ledger.get("tasks", {}).keys())

      verified = []
      missing_files = {}

      for task_id in task_ids:
          task = ledger["tasks"].get(task_id)
          if not task:
              continue

          evidence = task.get("evidence", {})
          task_missing = []

          # Check each evidence type for file claims
          for stage in ("RED", "GREEN", "REFACTOR"):
              stage_data = evidence.get(stage, {})
              if stage_data.get("completed"):
                  # Check test_files from RED
                  if stage == "RED":
                      for f in stage_data.get("test_files", []):
                          if not Path(f).exists():
                              task_missing.append(f)
                  # Check impl_files from GREEN
                  elif stage == "GREEN":
                      for f in stage_data.get("impl_files", []):
                          if not Path(f).exists():
                              task_missing.append(f)

          if task_missing:
              missing_files[task_id] = task_missing
          else:
              verified.append(task_id)

      return {"verified": verified, "missing_files": missing_files}

  Test: Run validate_done_claim → now checks actual file existence

  Success: Done claims blocked when files don't match evidence

  ---
  Implementation Order

  1. Change A — Easiest, highest payoff (30 min)
    - Extends existing EvidenceManager with minimal new code
    - Provides immediate protection against false completions
  2. Change C — Enables Change A (20 min)
    - Adds reusable verification function
    - Integrates with existing validate_done_claim workflow
  3. Change B — Final hardening (45 min)
    - Provides runtime detection of missing implementations
    - Prevents "almost done" from becoming "false done"

  Estimated effort: 1.5 hours total

  ---
  Multi-Terminal Considerations

  - Multi-terminal: SAFE — All changes use per-terminal evidence ledgers
  - File verification is stateless — Read/Grep checks don't require cross-terminal coordination
  - Evidence ledger isolation preserved — Each terminal has its own ledger

  Edge Case Considerations

  Internal self-reflection: "Are there other issues or edge cases?"

  Identified risks:
  1. Race condition: File deleted between evidence recording and verification → Mitigation: Fail open on FileNotFoundError,
   allow re-verification
  2. Path normalization: Windows paths (C:\\ vs P:\\) → Mitigation: Use Path.resolve() for canonical paths
  3. Symlinks/junctions: File exists but is redirect → Mitigation: Path.exists() follows redirects (correct behavior)
  4. Large file verification: Reading entire file is slow → Mitigation: Check existence first, content verification
  optional

  Failure conditions:
  - If disk is full: Write succeeds but file empty → Verification catches empty files
  - If permissions error: Write fails but evidence recorded → Verification catches non-existent files
  - If concurrent terminals: Each terminal has its own ledger → No cross-terminal interference

  ---
  Confidence: 85% — Evidence-based on code analysis + verification best practices research

  Evidence basis:
  - Code analysis: evidence.py, validate_done_claim.py, verification hooks
  - Web research: 5 sources on evidence-based verification, TDD best practices
  - Pattern: Detection gap between evidence recording and implementation reality

  Key assumptions:
  1. File system operations are reliable (writes persist)
  2. Evidence ledger accurately records claimed file paths
  3. Per-terminal isolation prevents cross-terminal contamination"

## Assistant

Yes, they’re tightly related—your “evidence ledger vs reality gap” analysis is basically the *failure mode* that Full State Verification is trying to eliminate.[1][2]

### How they connect

- In the analysis block, the class of problem is a **Detection/Verification Gap**: the system only checks that evidence *metadata* exists (ledger entries, file paths), not that the underlying implementation or file content is real.[2]
- The Full State Verification prompt is about closing exactly that class of gap by making the agent:  
  - identify a concrete source of truth,  
  - read actual state from it after actions,  
  - and prove via logs/DB/file checks that the claimed changes are present.[3][2]

So: the prompt is a *behavioral rule*, and your EvidenceManager + hooks changes are the *mechanism* that makes it enforceable in code.

### Mapping your changes to the concept

- Change A (`mark_done` + `_verify_implementation_exists`) turns “evidence recorded” into “evidence + existence check,” forcing the ledger to consult the filesystem before allowing “done.”[2]
- Change B (PostToolUse hook) extends that to the **tool layer**, catching cases where the agent claims a Write/Edit succeeded but the file never appeared—another instance of “ledger vs reality.”[2]
- Change C (`validate_implementation_claims`) lets you batch‑check ledger vs disk, which is like running a periodic Full State Verification across tasks, not just per‑task.[2]

Together, these are a concrete implementation of “don’t trust return values or self‑reported evidence; cross‑check against reality.”

### Why this is a good direction

- FACT: Verification frameworks in safety‑critical and eval‑heavy AI setups explicitly warn about “metric vs reality” gaps and recommend tying evidence to verifiable artifacts (files, hashes, DB state).[4][5][3]
- CONSENSUS: Combining behavioral prompts (Full State Verification) with hard technical guards (ledger checks, hooks, scripts) is more reliable than either alone; prompts nudge the model, code prevents silent failure.[6][1][3]
- SPECULATION (high confidence): Your pattern (ledger + verification hooks) is a direct, domain‑specific instantiation of Full State Verification for coding tasks and should substantially reduce “false done” events in your workflow.[3][2]

If you want, I can help collapse these ideas into a single “Verification Layer” spec (prompt + Python/TS APIs + hooks contracts) so you can treat this as one module instead of scattered rules.  

## Human

Yes turn it into a single verification layer spec

## Assistant

Here’s a compact “Verification Layer” spec that unifies your Full State Verification prompt, evidence ledger, and hooks into one coherent contract.

***

## 1. Core Principle

Every task must prove alignment between:  
1) intent, 2) evidence ledger, 3) actual code/system state.[1]
No task is “done” until verification has checked real artifacts (files, DB, logs) and all checks pass.[2][1]

***

## 2. Behavioral Contract (Prompt Layer)

Use this as a system‑level rule or subagent spec that all coding agents inherit.

> **Verification Layer Contract (Human‑level Duties)**  
>  
> For every task you work on, you must behave like a careful human tester, not just a coder.[1][2]
>  
> 1. Define Source of Truth  
>    - Before changing code, explicitly identify where the final result will be observable: database tables, files, APIs, UI state, or logs.[1]
>    - Record this in the task evidence ledger under `VERIFY.source_of_truth`.  
>  
> 2. Plan Verification  
>    - For each change, define:  
>      - one happy‑path scenario with specific inputs and expected outputs;  
>      - at least three edge cases (empty, max/large, invalid).[1]
>    - Record these as structured entries under `VERIFY.cases` in the evidence ledger.  
>  
> 3. Implement with Evidence  
>    - RED: create or update tests for the behavior (Python: pytest; TypeScript: jest/vitest).  
>      - Record test files in `evidence.RED.test_files`.  
>    - GREEN: implement or modify code to make the tests pass.  
>      - Record implementation files in `evidence.GREEN.impl_files`.  
>    - REFACTOR (optional): clean up related code/tests, listing files under `evidence.REFACTOR.files`.  
>  
> 4. Perform Full State Verification  
>    - Run tests (pytest, jest/vitest) and ensure they pass.  
>    - For each planned verification case:  
>      - Execute the relevant command, script, or HTTP call.  
>      - Immediately read from the source of truth (DB query, file read, log grep, UI/API check).[1]
>      - Capture outputs and state snapshots in logs or verification files.  
>    - Do not rely on return values alone; always cross‑check the actual persisted state.[1]
>  
> 5. Record and Prove Success  
>    - Update the evidence ledger with:  
>      - `VERIFY.tests_passed = true`;  
>      - `VERIFY.state_checks` containing references to logs/files/queries used to confirm behavior.  
>    - Only claim the task is done after all verification steps complete successfully.  
>  
> 6. Handle Failures Rigorously  
>    - If any test or verification step fails, you must:  
>      - stop, identify the root cause;  
>      - fix the implementation or tests;  
>      - rerun tests and verification;  
>      - update evidence so it reflects reality, not intentions.[1]
>  
> 7. Shared‑Mind and Subagents  
>    - When using subagents, you must:  
>      - run them in correct dependency order;  
>      - pass along the current evidence ledger and sources of truth;  
>      - ensure each subagent updates evidence and performs verification for its part.[3][1]

***

## 3. Evidence Ledger Contract (Python/TS‑agnostic API)

The ledger defines the **data model** your hooks and agents agree on.

- Each task entry must include:

```json
{
  "tasks": {
    "<task_id>": {
      "title": "...",
      "done": false,
      "done_at": null,
      "evidence": {
        "RED": {
          "completed": false,
          "test_files": ["path/to/test_file.py", "path/to/test_file.spec.ts"]
        },
        "GREEN": {
          "completed": false,
          "impl_files": ["path/to/module.py", "path/to/component.tsx"]
        },
        "REFACTOR": {
          "completed": false,
          "files": []
        },
        "VERIFY": {
          "source_of_truth": [
            "db:table_name",
            "file:path/to/result.json",
            "api:/endpoint"
          ],
          "cases": [
            {
              "name": "happy_path",
              "input": { "..." : "..." },
              "expected": { "..." : "..." }
            }
          ],
          "tests_passed": false,
          "state_checks": [
            "log:path/to/verification.log",
            "script:verify_state:case=happy_path"
          ]
        }
      }
    }
  }
}
```

- EvidenceManager responsibilities (Python):[1]
  - `can_mark_done(task_id) -> (bool, msg)` – checks required evidence fields are present.  
  - `mark_done(task_id, verify_content=True)` – enforces existence/content checks before flipping `done`.  
  - `_verify_implementation_exists(task_id) -> list[str]` – ensures every file in RED/GREEN exists, returning missing ones.  
  - Optional: `validate_implementation_claims(task_ids=None) -> {verified, missing_files}` – batch verification.  

This API is language‑agnostic: TypeScript tools just write into the same ledger file (JSON or YAML) via small helpers.

***

## 4. Hook Layer Contract (Claude Code / Tooling)

Hooks enforce the contract regardless of what the model “claims.”

### 4.1 Post‑ToolUse Implementation Verifier

- Scope: tools `Write`, `Edit` (and any project‑specific write tools).[1]
- Behavior:

```python
# P:\.claude\hooks\posttooluse\implementation_verifier.py

from pathlib import Path
from posttooluse.base import PostToolUseHook

class ImplementationVerifier(PostToolUseHook):
    """Verifies that Write/Edit operations create claimed content."""
    env_var = "IMPLEMENTATION_VERIFIER_ENABLED"
    default_enabled = True
    tool_matcher = {"Write", "Edit"}

    def process(self, tool_name, tool_input, tool_response):
        file_path = tool_input.get("file_path") or tool_input.get("filePath")
        if not file_path:
            return {"passed": True}

        path = Path(file_path)
        if not path.exists():
            return {
                "passed": False,
                "injection": (
                    f"⚠️ FILE NOT CREATED: {file_path}\n"
                    f"You claimed to write or edit this file, but it does not exist on disk. "
                    f"Create it or fix the path, then rerun verification."
                )
            }

        # (Optional) further checks: non-empty, contains marker string, etc.

        return {"passed": True}
```

- Contract: if `passed=False`, the model must treat the injection as a blocking error, repair, and retry before proceeding.

### 4.2 Stop Hook: Verify‑Then‑Complete

- Scope: triggers when the agent thinks a task is done.  
- Responsibilities:  
  1. Run language‑specific test commands (Python + TS).  
  2. Call `validate_implementation_claims` (or similar) to confirm existence.  
  3. If anything fails, inject a structured error and prevent the user‑visible “done” message.

Pseudo‑Python:

```python
# P:\.claude\hooks\stop\verification_gate.py

import subprocess
from pathlib import Path
from stop.base import StopHook
from skills.code.utils.evidence import EvidenceManager, validate_implementation_claims

class VerificationGate(StopHook):
    env_var = "VERIFICATION_GATE_ENABLED"
    default_enabled = True

    def process(self, conversation, final_response):
        task_id = self._extract_task_id(conversation)
        if not task_id:
            return {"passed": True}

        errors = []

        # 1. Run Python tests
        if Path("pyproject.toml").exists() or Path("pytest.ini").exists():
            if subprocess.call(["pytest"]) != 0:
                errors.append("pytest failed")

        # 2. Run TypeScript tests
        if Path("package.json").exists():
            if subprocess.call(["npm", "test"]) != 0:
                errors.append("npm test failed")

        # 3. Verify implementation vs evidence
        mgr = EvidenceManager()
        res = validate_implementation_claims(mgr, [task_id])
        missing = res.get("missing_files", {}).get(task_id, [])
        if missing:
            errors.append(
                "Evidence ledger references files that do not exist:\n"
                + "\n".join(f" - {p}" for p in missing)
            )

        if errors:
            return {
                "passed": False,
                "injection": (
                    "⚠️ VERIFICATION FAILED:\n"
                    + "\n".join(errors)
                    + "\nYou must fix these issues, update tests/evidence, "
                    "rerun verification, and only then mark the task as done."
                )
            }

        # Optionally auto-call mark_done here
        mgr.mark_done(task_id)
        return {"passed": True}
```

***

## 5. Minimal Contracts Between Pieces

To keep this maintainable, constrain interfaces:

- **Prompt ↔ Ledger**  
  - The prompt never hard‑codes paths; it only refers to ledger keys: `evidence.RED.test_files`, `evidence.GREEN.impl_files`, `evidence.VERIFY.*`.  
  - Agents must update these keys whenever they create/edit relevant files.

- **Ledger ↔ Hooks**  
  - Hooks treat the ledger as the single Source of Truth for *claims*; they only check existence/content of paths that the ledger says should exist.  
  - `mark_done` and `validate_implementation_claims` are the only functions hooks call; they do not need to know ledger internals.

- **Hooks ↔ Language Tooling**  
  - Test commands are configured in one place (e.g., `verify_config.json`):  

```json
{
  "python": { "test_cmd": ["pytest"] },
  "typescript": { "test_cmd": ["npm", "test"] }
}
```

  - Hooks read this config and execute commands; they don’t embed Python/TS specifics elsewhere.

***

If you’d like, next step I can:  
- trim this into a literal `.md` spec + concrete `evidence.py`/hook files you can drop into your repo, or  
- design a minimal JSON schema for the ledger so you can validate it with a single script.  

## Human

this look ok?

## Assistant

Yes—this plan is coherent, technically consistent with your goal, and implementable with incremental risk.[1]

### Strengths

- Clear problem framing (false completion, detection gap) and direct mapping from gaps to concrete changes in hooks and EvidenceManager.[1]
- Architecture diagram matches the three‑phase verification story: post‑write check → guarded `mark_done` → stop‑hook gate.[1]
- Implementation snippets for `ImplementationVerifier`, `_verify_implementation_exists`, and `mark_done` are minimal, composable, and align with the contracts you described earlier.[1]

### Things I’d tune before implementing

- Centralize `EvidenceManager` locking: your draft introduces `_load_ledger_locked` / `_save_ledger_locked` but still calls `_load_ledger()` in `_verify_implementation_exists`; I’d either always use locked versions internally or document when lock‑free reads are allowed.[1]
- Be explicit about Python‑only locking: `msvcrt.locking` is Windows‑specific; if you might ever run this on WSL or Linux, note a fallback (e.g., `portalocker` or SQLite) in the Risks section.[2][1]
- Clarify `VerificationGate._extract_task_id`: right now it’s a stub; I’d specify exactly where the task id comes from (env var, system prompt, or a convention in conversation metadata), since this is critical for correctness.[1]

### Optional but nice improvements

- Extend `_verify_implementation_exists` to optionally treat empty files as failures (config flag), which aligns more closely with your “file exists with expected content” aim, even if you don’t yet parse content.[1]
- In Phase 3, consider running JS/TS tests too (`npm test`/`pnpm test`) if `package.json` is present; you already mention TypeScript in the broader design, so encoding that now prevents drift.[1]

Overall: this is a solid draft; you can implement Phases 1–2 almost as‑is, then refine the stop hook’s task‑ID extraction and test strategy once you see real traffic patterns.[1]

Do you want help tightening the locking API so every ledger read/write uses one consistent code path?  
