---
source_id: "b479c7e2-76d1-4b0f-bc6f-acd21afe71ea"
title: "A pattern I've been using to call Python “tools” from a Node-based agent (manifest + subprocess) : r/ChatGPTCoding - Reddit"
notebook_id: 0fa07246-ba84-43fd-a9cd-f86999f24286
url: https://www.reddit.com/r/ChatGPTCoding/comments/1p0vh8o/a_pattern_ive_been_using_to_call_python_tools/
type: 5
exported: 2026-08-08
---

# A pattern I've been using to call Python “tools” from a Node-based agent (manifest + subprocess) : r/ChatGPTCoding - Reddit
A pattern I've been using to call Python “tools” from a Node-based agent (manifest + subprocess) : r/ChatGPTCoding
Skip to main content
https://www.reddit.com/r/ChatGPTCoding/comments/1p0vh8o/a_pattern_ive_been_using_to_call_python_tools/#main-content
 A pattern I've been using to call Python “tools” from a Node-based agent (manifest + subprocess) : r/ChatGPTCoding
Open menu
Open navigation 
https://www.reddit.com/
Go to Reddit Home
 
r/ChatGPTCoding
TRENDING TODAY
Get App
Get the Reddit app
Log In
https://www.reddit.com/login/
Log in to Reddit
Expand user menu
Open settings menu
Skip to Navigation
https://www.reddit.com/r/ChatGPTCoding/comments/1p0vh8o/a_pattern_ive_been_using_to_call_python_tools/#left-sidebar-container
 
Skip to Right Sidebar
https://www.reddit.com/r/ChatGPTCoding/comments/1p0vh8o/a_pattern_ive_been_using_to_call_python_tools/#right-sidebar-container
Back
Go to ChatGPTCoding
https://www.reddit.com/r/ChatGPTCoding/
r/ChatGPTCoding
https://www.reddit.com/r/ChatGPTCoding/
•
5mo ago
ZackHine
https://www.reddit.com/user/ZackHine/
Locked post
Stickied post
Archived post
Language and translations
Report
A pattern I've been using to call Python “tools” from a Node-based agent (manifest + subprocess)
Discussion
https://www.reddit.com/r/ChatGPTCoding/?f=flair_name%3A%22Discussion%22
I've been building LLM agents (including Open AI) in my spare time and ran into a common annoyance:
I want most of my agent logic in Node/TypeScript, but a lot of the tools I want (scrapers, ML utilities, etc.) are easier to write in Python.
Instead of constantly rewriting tools in both languages, I've been using a simple pattern:
describe each tool in a manifest
implement it in whatever language makes sense (often Python)
call it from a Node-based agent host via a subprocess and JSON
It's been working pretty well so I figured I'd share in case it's useful or someone has a better way.
The basic pattern
Each tool lives in its own folder with:
a manifest ( 
agent.json
 )
an implementation (main.py, index.ts, etc.)
The manifest describes:
name, runtime, entrypoint
input/output schema
The host (in my case, a Node agent) uses the manifest to:
validate inputs
spawn the subprocess with the right command
send JSON in / read JSON out
Example manifest
{
  "name": "web-summarizer",
  "version": "0.1.0",
  "description": "Fetches a web page and returns a short summary.",
  "entrypoint": {
    "args": [
      "-u",
      "summarizer/main.py"
    ],
    "command": "python",
  },
  "runtime": {
    "type": "python",
    "version": "3.11"
  }
  "inputs": {
    "type": "object",
    "required": [
      "url"
    ],
    "properties": {
      "url": {
        "type": "string",
        "description": "URL to summarize"
      }
    },
    "additionalProperties": false
  },
  "outputs": {
    "type": "object",
    "required": [
      "summary"
    ],
    "properties": {
      "summary": {
        "type": "string",
        "description": "Summarized text"
      },
    },
    "additionalProperties": false
  }

Python side (main.py)
Very simple protocol: read JSON from stdin, write JSON to stdout.
import sys
import json
from textwrap import shorten

def summarize(text: str, max_words: int = 200) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "..."

def main():
    raw = sys.stdin.read()
    payload = json.loads(raw)

    url = payload["url"]
    max_words = payload.get("max_words", 200)

    # ... fetch page, extract text ...
    text = f"Fake page content for {url}"
    summary = summarize(text, max_words=max_words)

    result = {"summary": summary}
    sys.stdout.write(json.dumps(result))

if __name__ == "__main__":
    main()

Node side (host / agent)
The Node agent doesn't care that this is Python. It just knows:
there's a manifest
it can spawn a subprocess using the command in 
entrypoint.command
it should send JSON matching the 
inputs
 shape, and expect JSON back
import { spawn } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";

type ToolManifest = {
  name: string;
  runtime: string;
  entrypoint: { command : string; args: string[] };
  inputs: Record<string, any>;
  outputs: Record<string, any>;
};

async function callTool(toolDir: string, input: unknown): Promise<unknown> {
  const manifestPath = path.join(toolDir, "agent.json");
  const manifest: ToolManifest = 
JSON
.parse(
    readFileSync(manifestPath, "utf8")
  );


const cmd = manifest.entrypoint.command;
  const [ ...args] = manifest.entrypoint.args;
  const child = spawn(cmd, args, { cwd: toolDir });

  const payload = 
JSON
.stringify(input);
  child.stdin.write(payload);
  child.stdin.end();

  let stdout = "";
  let stderr = "";

  child.stdout.on("data", (chunk) => (stdout += chunk.toString()));
  child.stderr.on("data", (chunk) => (stderr += chunk.toString()));

  return new Promise((resolve, reject) => {
    child.on("close", (code) => {
      if (code !== 0) {
        return reject(new 
Error
(`Tool failed: ${stderr || code}`));
      }

      try {
        const result = 
JSON
.parse(stdout);
        resolve(result);
      } catch (e) {
        reject(new 
Error
(`Failed to parse tool output: ${e}`));
      }
    });
  });
}

// Somewhere in your agent code:
async function example() {
  const result = await callTool("./tools/web-summarizer", {
    url: "https://example.com",
    max_words: 100,
  });

  
console
.log(result);
}

Why I like this pattern
I can keep most orchestration in Node/TS (which I prefer for app code)
I can still use Python for tools where the ecosystem is better
Tools become mostly runtime-agnostic from the agent's perspective
If I want to share tools, I can package the folder + manifest and reuse it elsewhere
Under the hood, I'm wrapping all of this in a more structured system (CLI + SDK + registry) in a project I'm working on (AgentPM), but even without that, the pattern has been surprisingly handy.
Things I'm unsure about / would love feedback on
Have you found a cleaner way to manage cross-language tools in your agents?
Would you rather:
keep all tools in one language,
or lean into patterns like this to mix ecosystems?
Also curious if anyone has evolved something like this into a more formal internal standard for their team.
Upvote 0 Downvote 0 Go to comments Share
Comments Section
Be the first to comment
Nobody's responded to this post yet. Add your thoughts and get the conversation going.
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
Related Answers Section
Related Answers
Innovative ways to use ChatGPT in coding
https://www.reddit.com/answers/e2738cf7-edb6-418d-9c24-0d7bf4446375/?q=Innovative+ways+to+use+ChatGPT+in+coding&source=PDP
Best practices for integrating AI in apps
https://www.reddit.com/answers/3f93d6e8-85a7-4439-b0cd-6f3f87a11170/?q=Best+practices+for+integrating+AI+in+apps&source=PDP
Unique coding projects using ChatGPT
https://www.reddit.com/answers/11375b9a-62a4-4b80-aa52-705ccd1f7190/?q=Unique+coding+projects+using+ChatGPT&source=PDP
Optimizing ChatGPT responses in coding
https://www.reddit.com/answers/74b062ea-2527-4498-9b7d-2c941df2a2aa/?q=Optimizing+ChatGPT+responses+in+coding&source=PDP
How to debug code with ChatGPT assistance
https://www.reddit.com/answers/84030c0f-810c-4e60-85c8-1976b0a5946d/?q=How+to+debug+code+with+ChatGPT+assistance&source=PDP
More posts you may like
Did you know you can run Python code from within your .NET apps?
https://www.reddit.com/r/dotnet/comments/1kkbk12/did_you_know_you_can_run_python_code_from_within/
 
r/dotnet
https://www.reddit.com/r/dotnet/
 • 1y ago [
Did you know you can run Python code from within your .NET apps?
](https://www.reddit.com/r/dotnet/comments/1kkbk12/did_you_know_you_can_run_python_code_from_within/) 
 428 upvotes · 128 comments
Playwright Python or Typescript ?
https://www.reddit.com/r/Playwright/comments/1r3fd7e/playwright_python_or_typescript/
 
r/Playwright
https://www.reddit.com/r/Playwright/
 • 2mo ago [
Playwright Python or Typescript ?
](https://www.reddit.com/r/Playwright/comments/1r3fd7e/playwright_python_or_typescript/) 6 upvotes · 14 comments
Structural codes are still PDFs in 2026. So I turned NTC18 into a Python library.
https://www.reddit.com/r/StructuralEngineering/comments/1rocv6z/structural_codes_are_still_pdfs_in_2026_so_i/
 
r/StructuralEngineering
https://www.reddit.com/r/StructuralEngineering/
 • 1mo ago [
Structural codes are still PDFs in 2026. So I turned NTC18 into a Python library.
](https://www.reddit.com/r/StructuralEngineering/comments/1rocv6z/structural_codes_are_still_pdfs_in_2026_so_i/) 56 upvotes · 58 comments
I actually used Python practically the first time today!
https://www.reddit.com/r/Python/comments/1kh3uz7/i_actually_used_python_practically_the_first_time/
 
r/Python
https://www.reddit.com/r/Python/
 • 1y ago [
I actually used Python practically the first time today!
](https://www.reddit.com/r/Python/comments/1kh3uz7/i_actually_used_python_practically_the_first_time/) 333 upvotes · 44 comments
Recommend me some good python + playwright course that focuses on Framework creation and implementation.
https://www.reddit.com/r/Playwright/comments/1rkbaxy/recommend_me_some_good_python_playwright_course/
 
r/Playwright
https://www.reddit.com/r/Playwright/
 • 1mo ago [
Recommend me some good python + playwright course that focuses on Framework creation and implementation.
](https://www.reddit.com/r/Playwright/comments/1rkbaxy/recommend_me_some_good_python_playwright_course/) 5 upvotes · 6 comments
Do you need to know Python for good promt engineering?
https://www.reddit.com/r/PromptEngineering/comments/1k9pdc3/do_you_need_to_know_python_for_good_promt/
 
r/PromptEngineering
https://www.reddit.com/r/PromptEngineering/
 • 1y ago [
Do you need to know Python for good promt engineering?
](https://www.reddit.com/r/PromptEngineering/comments/1k9pdc3/do_you_need_to_know_python_for_good_promt/) 11 upvotes · 14 comments
Forget metaclasses; Python's __init_subclass__ is all you really need
https://www.reddit.com/r/Python/comments/1mevs3i/forget_metaclasses_pythons_init_subclass_is_all/
 
r/Python
https://www.reddit.com/r/Python/
 • 8mo ago [
Forget metaclasses; Python's 
__init_subclass__
 is all you really need
](https://www.reddit.com/r/Python/comments/1mevs3i/forget_metaclasses_pythons_init_subclass_is_all/) 245 upvotes · 60 comments
Why is Python type hinting so maddening compared to other implementations?
https://www.reddit.com/r/Python/comments/1nzl1nj/why_is_python_type_hinting_so_maddening_compared/
 
r/Python
https://www.reddit.com/r/Python/
 • 6mo ago [
Why is Python type hinting so maddening compared to other implementations?
](https://www.reddit.com/r/Python/comments/1nzl1nj/why_is_python_type_hinting_so_maddening_compared/) 311 upvotes · 159 comments
you all like the new python projects?
https://www.reddit.com/r/42_school/comments/1rl8lzk/you_all_like_the_new_python_projects/
 
r/42_school
https://www.reddit.com/r/42_school/
 • 1mo ago [
you all like the new python projects?
](https://www.reddit.com/r/42_school/comments/1rl8lzk/you_all_like_the_new_python_projects/) 15 upvotes · 26 comments
What hidden gem Python modules do you use and why?
https://www.reddit.com/r/Python/comments/1rrz3kx/what_hidden_gem_python_modules_do_you_use_and_why/
 
r/Python
https://www.reddit.com/r/Python/
 • 1mo ago [
What hidden gem Python modules do you use and why?
](https://www.reddit.com/r/Python/comments/1rrz3kx/what_hidden_gem_python_modules_do_you_use_and_why/) 404 upvotes · 190 comments
We let type hints completely ruin the readability of python..
https://www.reddit.com/r/Python/comments/1rwwjug/we_let_type_hints_completely_ruin_the_readability/
 
r/Python
https://www.reddit.com/r/Python/
 • 24d ago [
We let type hints completely ruin the readability of python..
](https://www.reddit.com/r/Python/comments/1rwwjug/we_let_type_hints_completely_ruin_the_readability/) 29 comments
Python Subject are so bad and confusing
https://www.reddit.com/r/42_school/comments/1qvc3uy/python_subject_are_so_bad_and_confusing/
 
r/42_school
https://www.reddit.com/r/42_school/
 • 2mo ago [
Python Subject are so bad and confusing
](https://www.reddit.com/r/42_school/comments/1qvc3uy/python_subject_are_so_bad_and_confusing/) 23 upvotes · 48 comments
Can I go straight into learning Manim or should I learn some python first?
https://www.reddit.com/r/manim/comments/1ocqmun/can_i_go_straight_into_learning_manim_or_should_i/
 
r/manim
https://www.reddit.com/r/manim/
 • 6mo ago [
Can I go straight into learning Manim or should I learn some python first?
](https://www.reddit.com/r/manim/comments/1ocqmun/can_i_go_straight_into_learning_manim_or_should_i/) 3 upvotes · 8 comments
What setup do you use for coding in python?
https://www.reddit.com/r/emacs/comments/1rz2il5/what_setup_do_you_use_for_coding_in_python/
 
r/emacs
https://www.reddit.com/r/emacs/
 • 21d ago [
What setup do you use for coding in python?
](https://www.reddit.com/r/emacs/comments/1rz2il5/what_setup_do_you_use_for_coding_in_python/) 31 upvotes · 37 comments
Is there anything R can do that Python can't?
https://www.reddit.com/r/AskStatistics/comments/1p0jfs0/is_there_anything_r_can_do_that_python_cant/
 
r/AskStatistics
https://www.reddit.com/r/AskStatistics/
 • 5mo ago [
Is there anything R can do that Python can't?
](https://www.reddit.com/r/AskStatistics/comments/1p0jfs0/is_there_anything_r_can_do_that_python_cant/) 202 upvotes · 139 comments
guys you can install python from python from python from python!!111!
https://www.reddit.com/r/ihadastroke/comments/1mddej5/guys_you_can_install_python_from_python_from/
 
r/ihadastroke
https://www.reddit.com/r/ihadastroke/
 • 8mo ago [
guys you can install python from python from python from python!!111!
](https://www.reddit.com/r/ihadastroke/comments/1mddej5/guys_you_can_install_python_from_python_from/) 
 23 upvotes · 6 comments
Structure Large Python Projects for Maintainability
https://www.reddit.com/r/Python/comments/1pccbk4/structure_large_python_projects_for/
 
r/Python
https://www.reddit.com/r/Python/
 • 4mo ago [
Structure Large Python Projects for Maintainability
](https://www.reddit.com/r/Python/comments/1pccbk4/structure_large_python_projects_for/) 48 upvotes · 27 comments
Best code editor or IDE to start with Python for an R programmer?
https://www.reddit.com/r/rstats/comments/1lwy1dt/best_code_editor_or_ide_to_start_with_python_for/
 
r/rstats
https://www.reddit.com/r/rstats/
 • 9mo ago [
Best code editor or IDE to start with Python for an R programmer?
](https://www.reddit.com/r/rstats/comments/1lwy1dt/best_code_editor_or_ide_to_start_with_python_for/) 46 upvotes · 44 comments
R user joining a Python-first team - how hard should I switch to Python?
https://www.reddit.com/r/rstats/comments/1rutje5/r_user_joining_a_pythonfirst_team_how_hard_should/
 
r/rstats
https://www.reddit.com/r/rstats/
 • 26d ago [
R user joining a Python-first team - how hard should I switch to Python?
](https://www.reddit.com/r/rstats/comments/1rutje5/r_user_joining_a_pythonfirst_team_how_hard_should/) 52 upvotes · 51 comments
Are there any prop firms that offer Python APIs?
https://www.reddit.com/r/algotrading/comments/1lzo158/are_there_any_prop_firms_that_offer_python_apis/
 
r/algotrading
https://www.reddit.com/r/algotrading/
 • 9mo ago [
Are there any prop firms that offer Python APIs?
](https://www.reddit.com/r/algotrading/comments/1lzo158/are_there_any_prop_firms_that_offer_python_apis/) 10 upvotes · 25 comments
Implementing Python in Python
https://www.reddit.com/r/ProgrammingLanguages/comments/1r0hx00/implementing_python_in_python/
 
r/ProgrammingLanguages
https://www.reddit.com/r/ProgrammingLanguages/
 • 2mo ago [
Implementing Python in Python
](https://www.reddit.com/r/ProgrammingLanguages/comments/1r0hx00/implementing_python_in_python/) 58 upvotes · 15 comments
For those of us who think in strategy logic but don't want to maintain a Python codebase, what are you using?
https://www.reddit.com/r/algotrading/comments/1rkub2n/for_those_of_us_who_think_in_strategy_logic_but/
 
r/algotrading
https://www.reddit.com/r/algotrading/
 • 1mo ago [
For those of us who think in strategy logic but don't want to maintain a Python codebase, what are you using?
](https://www.reddit.com/r/algotrading/comments/1rkub2n/for_those_of_us_who_think_in_strategy_logic_but/) 7 upvotes · 27 comments
Any tips for learning python
https://www.reddit.com/r/QGIS/comments/1pku8pe/any_tips_for_learning_python/
 
r/QGIS
https://www.reddit.com/r/QGIS/
 • 4mo ago [
Any tips for learning python
](https://www.reddit.com/r/QGIS/comments/1pku8pe/any_tips_for_learning_python/) 28 upvotes · 8 comments
Python open source projects to contribute
https://www.reddit.com/r/Python/comments/1sdan8c/python_open_source_projects_to_contribute/
 
r/Python
https://www.reddit.com/r/Python/
 • 5d ago [
Python open source projects to contribute
](https://www.reddit.com/r/Python/comments/1sdan8c/python_open_source_projects_to_contribute/) 11 upvotes · 32 comments
View Post in
See more See fewer
ไทย
https://www.reddit.com/r/ChatGPTCoding/comments/1p0vh8o/a_pattern_ive_been_using_to_call_python_tools/?tl=th
Community Info Section
r/ChatGPTCoding
https://www.reddit.com/r/ChatGPTCoding/
Join
For The Coding Side of ChatGPT
Welcome to our community! This subreddit focuses on the coding side of ChatGPT - from interactions you've had with it, to tips on using it, to posting full blown creations! Make sure to read our rules before posting!
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
 
0cAFcWeA4puEl7aqOWWUc6ZBDHa8zJccZSCtEQLtSfZDL3eEDRKZQlOLVv1cgtTWQHFm_1zZ_1HE1JrC7QtXFvufujQE_0FuM9UfPJttzS_lw8l8NKShPbqfREQM_InRBT2H4AOh5k4Relc1VXBE6zc1M5s5khJVDfQtyk_ruaSEj24pUZBSxDmB51OyWMehKusl9pTLHWy3lLyyUJaIqdJ7eL53D7wx_xc4QywW1hjMnMJ2TiVM0Y-Zh7bQewnrNjwGuPZVh3bsbVlarE2buE3Kdk5L7GgU8zzmhIjYLZG4vn2zJq2oEavRmBbcMUlxkk9lBig7HaJtVgGz1AusrR02vbkwKt2ogfl_ktCyCxYnLA49A5fHDRNbakvuNjYOZpIHDmzN39z0Jv04jT3WyytdVO06x8QyS6Vc8rw4mU3ICFkZcyq8r0YkCjOlgISEbwhLAuwf_EkbSWSARQx2FKFJzv_TukJ7nEa-2kIeFD5n5aAeJkNMbn16aiM8y40oOKolOiGQXpu19heWJV3TSgP6bO7efZ6F8WwD9QdAZIiqoTWKJL494L7vE081xesNt9ub8v3twH3Si0cVVipgyNaYBXIAUt6L122XyF_GFFd_f0JVMHpz9uvbZusM9u7y0BDp7YfinsKVg_PiXi5RzDc5zrtbhqI2rK-AtaBIm7fywcn51uKWLhIr6CUJlqOxd171ZFBnoTHfygEwBXrYaUEyP8qBEgj1TFvhkkuSyPR_pVRlnWLT_ge3NIwx5ihmFTNCMDEKBiqP6c2WKmMcsDCgxohT3DcvNnqzgK8OCVhCV2sdzqdLcaHDlKiYcz1YPDp7aMmBedJ8lvkp43U_VA45ScUtrFZ9HsmaiOBJ0Pf4RrrG-3PxF41mIeJ5FwUxLSFWaP_5L7lahC8sHcqjrQc5dUTVUwhaDe8qZJubjUXDQmpSW0fZ6LfH0pRvmPi8Z8FRxZglxXhT-wbxznT47SjpdM7vP79_iB696wJtcuJkwe_AQn8aef-YDgl6PtPQm1pHXZiUNRccIlxolGcbin9ph7ANodvRVekaoiBhdwsIhSgQSW0lWeXWsyzxdZA-iMs784fUfrMMSsHkyYld3AYX88SgnNRlPqpfHoWOlvS5rPyemRnW4xBuPTNz2Qi_ny7JX0SvJaF_4_0Oo45chXo8IZn2zUBm99sFpk6YSkb8rQ9MapiFavxdEet-a5s7EkFs29jIZHNSMzLNpLRNQa_V-ji8jd6RTckGD0fqFAQt9fq3hF55-m3D3ZPZHS-raIhbBZjmksVUM2KwehWnZ99Y_FoR1HvY_nXuOgLHOFGZZSCBtrJhWaTwubWkCd4IyOWHBqX6ZhXNLt5HmiA7l3V3MyfLiX1mZYriQE9csN8SX5LwiWmBMFeZfUMAtix0bZJgoMPYGobDxIjxoOdvuFZAr0Nmy_QsRLtve4EFNOnpgiQk3-FtbzYe0Oo0wI3woV3QOJ1V0YxEBWXnniWNOC7lzjSrtqGvn8_Vr3Q0CIdztEcsbqVGZUeqhibtXt_V6a7uwgAbJ_0g1AdcQOdvv7G_mG9peHMOq6VwhmW2rj0C0j3Limf4SZ1Lb3YZZJJvTa7AD1nMYLS1Ha4Tyn-pu0idz677wmaHs49UY46lug2Kr35-Mmm-2GfoufRluw5tgOt6qyPoHJABeTspAh68XnbJ_xoz7UfM_B-UoZg9LBLTkgZTfQbhhMTZjL4_ftp9pZoakCKaUQtZ5sJFgEFftHUvypRxEAWWPxN8fb6Q4Mm3olWPVLQyirp7_eJkMWU2GB0yZZOnxkMN2FTeyG3jRMuo0B8XVSHMmmLX6SMmyT33szU6Qr9LtM3XqQXjl1UxomQinyoTxNCcaerfvXpdAR3SFoX_fOVQEHfeEiHtxWksUSUWAv8mLSrXbWv6c8iNtbqQyZWDG1f6ttv8yNfVOOA03RUGpZu4lkxf8BX4-8h1IpzQbF_9B8i2t-lCKBGNNgTb34cFlWeoplON_apEa8_RnpZGpVDS91or4Z1WB8jQ0feeyKGW3-da5IJ_MRsC199FXCUk4Uj-4NEUnQ_M9L--GfVViHTLryyhK1NLiCygYi7dXnwp24rrKvXOmr9d1q7a5cIVfsSL3dbLzsxjH74_SB_8h1FHb687zguYDQDI6dZtI0C4zWU2Y
