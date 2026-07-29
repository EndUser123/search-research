---
source_id: "c16abbed-f9e3-4eaf-af3c-2b5c6b611ebd"
title: "Operational Specification for Claude Code Skill-Based Hooks in a Closed-Loop Validation Architecture"
notebook_id: 59329bf3-4765-4d4e-8ec6-f2eceeba0f41
url: null
type: generated_text
exported: 2026-07-27
---

# Operational Specification for Claude Code Skill-Based Hooks in a Closed-Loop Validation Architecture
Operational Specification for Claude Code Skill-Based Hooks in a Closed-Loop Validation Architecture

The Imperative for Deterministic Agentic Control

The emergence of agentic systems capable of autonomous file manipulation and tool execution has necessitated a rigorous shift from probabilistic guidance to deterministic control. In the context of the Claude Code ecosystem, the "vibe coding" paradigm—characterized by conversational requests and loose instruction adherence—is insufficient for production-grade environments where data integrity and architectural consistency are paramount.[1, 2, 3] To achieve 100% operational reliability, the Senior Agentic Systems Engineer must implement a closed-loop validation architecture. This architecture leverages lifecycle hooks to intercept agent actions, evaluate them against hard-coded invariants, and force remedial iterations through a structured repair protocol.[4, 5, 6]

A closed-loop architecture essentially functions as a real-time, state-aware middleware. Unlike static rules defined in a CLAUDE.md file, which the agent may selectively ignore or summarize away during context compaction, lifecycle hooks are infrastructure-level enforcement mechanisms.[7, 8, 9] They execute outside the model’s reasoning window, providing a non-bypassable safety and quality gate.[2, 4] By defining precise execution points, deterministic feedback signals, and specialized sub-agent orchestration patterns, organizations can transform Claude Code from a helpful assistant into a verified automated engineer.[1, 2, 10]

Hook Lifecycle and Contextual Execution Mechanics

The operational capability of a validation loop is fundamentally constrained by its visibility into the agent’s internal state and external actions. Claude Code exposes a lifecycle comprised of specific events that fire at critical junctions of the reasoning-action loop.[11, 12] For the Senior Agentic Systems Engineer, mastering the timing and payload of these events is the first requirement for defining an operational specification.

Exact Execution Points and Lifecycle Taxonomy

The hook lifecycle is divided into initialization, agentic loop, and termination phases. Each phase offers distinct opportunities for context injection or validation.[11]

Hook Event

Execution Phase

Trigger Point

Primary System Utility

SessionStart

Initialization

When the 

claude

 command is first invoked or a session is resumed.[11, 13]

Environment setup, project context loading, and pre-warming the context window.[9, 13]

UserPromptSubmit

Input Gate

Immediately after the user hits Enter, before the LLM processes the text.[11, 14]

Validating prompt safety, injecting project-wide constraints, or blocking prohibited requests.[11, 14]

PreToolUse

Action Gate

After the LLM decides to call a tool (Bash, Edit, Read) but before the command executes.[11, 15, 16]

Security filtering, destructive command blocking, and permission modification.[9, 17, 18]

PostToolUse

Validation Gate

After a tool call successfully returns a result from the system.[4, 11]

Quality assurance, linting, data integrity checks, and contextual feedback injection.[4, 12, 19]

PostToolUseFailure

Error Gate

After a tool call fails due to a system error (e.g., FileNotFoundError).[11, 12, 15]

Automated error analysis and custom recovery suggestions.[15]

Stop

Turn Gate

When the primary agent believes it has finished its current task turn.[9, 10, 11]

Completion verification, final audit, and generation of handoff reports.[12, 19]

SubagentStop

Audit Gate

When a tool-spawned sub-agent (via the Task tool) completes its independent work.[11, 14, 16]

Validating sub-agent artifacts and merging results into the global session state.[20]

The system also supports utility hooks like 

PreCompact

 and 

PostCompact

, which are critical for maintaining state across the "Compaction Barrier".[11, 21] During long engineering sessions, the harness automatically summarizes conversation history once the context window reaches its threshold.[21] A 

PreCompact

 hook allows the system to backup critical variables or the current repair status to a persistent file, which can then be re-read by the agent after the summary occurs, preventing the loss of current task objectives.[11, 14, 22]

Data Propagation and Context Access

For a validator to function as a "Right Thing" check, it must receive the full context of the operation it is auditing. For command hooks (shell scripts or binaries), Claude Code passes this context via a JSON object on standard input (stdin).[8, 11, 19] This is a critical architectural property: the hook does not rely on global state but is explicitly passed the parameters of the current event.[15]

The JSON payload provided to a 

PostToolUse

 hook typically includes the following structure:

session_id

: A unique identifier for the current interactive session.[15, 19]

cwd

: The absolute path to the current working directory where the agent is operating.[15, 19]

tool_name

: The specific tool that was just fired (e.g., "Bash", "Edit", "MultiEdit").[8, 15]

tool_input

: A nested object containing the arguments the agent passed to the tool. For an "Edit" tool, this includes the 

file_path

 and the 

explanation

 of the change.[16]

tool_result

: The output returned by the system after tool execution, allowing the validator to see what actually happened.[15, 16]

Additionally, the Claude harness exposes several environment variables to the hook execution environment to assist in path resolution and script portability. The variable 

$CLAUDE_PROJECT_DIR

 is the most significant, as it always resolves to the root directory of the project, regardless of where in the subdirectory tree the agent is currently working.[2, 11] While some legacy versions of the CLI faced issues with variable propagation, current operational specifications mandate the use of stdin JSON as the primary source of truth, with environment variables used only for secondary path resolution.[23]

The Deterministic Repair Protocol: Mechanisms of Automated Recovery

A closed-loop system is defined by its ability to self-correct. The "Repair Protocol" is the logic that translates a detected violation into a mandatory remedial action.[5, 6, 12] In the Claude Code architecture, this is achieved by leveraging specific exit codes and standard error (stderr) patterns to interrupt the agent's linear path.[12, 16]

Signals of the Repair Cycle: Exit Codes 0 and 2

The harness interprets the exit code of a hook command as a binary instruction for task continuity.[12]

Exit Code 0 (Continuity):

 Signals that the validation logic has passed. If the hook produces any text on 

stdout

 during a 

UserPromptSubmit

 or 

SessionStart

 event, this text is appended to the conversation history as a "System Reminder".[9, 12, 13] This is useful for providing "soft advice" or hints that guide the agent without forcing a break in its flow.[24, 25]

Exit Code 2 (Intervention):

 Signals a validation failure that requires immediate agent attention. When a hook exits with code 2, the harness treats the content of the hook’s 

stderr

 as a critical system instruction.[12, 16] Crucially, this forces the agent to pause its current plan and initiates a "Repair Turn" where the model must address the failure message before it can attempt any other tool calls.[5, 12]

This distinction is the operational pivot of the closed-loop architecture. By using Exit Code 2, the systems engineer ensures that quality or security violations are treated as blocking errors rather than ignorable suggestions.[12]

Stdout JSON Patterns and Schema Evolution

While simple blocking is achieved via exit codes, advanced state control relies on the agent returning structured JSON to the harness. The system has evolved from top-level 

decision

 keys to a nested 

hookSpecificOutput

 schema.[26]

For a 

PreToolUse

 hook intended to block or modify a destructive command, the validator script must output a JSON object to 

stdout

 following this operational standard:

{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "Constraint Violation: Detected attempt to modify.env file. Use the SecretManager skill instead.",
    "updatedInput": null
  }
}


json

The 

permissionDecision

 can be set to 

allow

 (bypass the user prompt), 

deny

 (cancel the tool call and feedback the reason), or 

ask

 (force a manual user confirmation).[4, 12] This allows the validator to act as an automated security officer, selectively gating access based on complex logic that the LLM might otherwise attempt to circumvent.[2, 4]

The Finite State Machine of the Repair Loop

The operational repair loop follows a precise sequence of transitions:

State: Observation.

 The agent analyzes the codebase and proposes an edit.[6, 27]

State: Action.

 The agent calls the 

Edit

 tool.[28, 29]

State: Interception.

 The 

PostToolUse

 event triggers the validation script.[11, 19]

State: Evaluation.

 The script parses the file change. It detects an integrity violation (e.g., a balance increment that results in a negative value).[4, 30, 31]

State: Feedback Injection.

 The script writes the error to 

stderr

 and exits with code 2.[12, 16]

State: Forced Reasoning.

 The harness presents the error to the agent. The agent is prevented from closing the task and must now respond to the "DATA_VIOLATION" message.[5, 12]

State: Remediation.

 The agent performs a new edit to correct the state.[5, 6]

State: Re-Validation.

 The loop returns to step 3. The cycle completes only when the validator exits with code 0.[12]

This sequence guarantees that no code change is finalized until it has passed through the deterministic gauntlet of the validation engine.

Front Matter Schema Engineering for Skills and Commands

Skills serve as the organizational unit for agentic capability. They are essentially executable knowledge packages that include instructions, reference materials, and lifecycle hooks.[17, 32, 33, 34] The YAML front matter of a 

.md

 skill file is the configuration layer that defines how the agent and the harness interact when that skill is active.[17, 35]

###Verbatim YAML Front Matter Specification

For a skill to participate in a closed-loop validation architecture, its front matter must include the 

hooks

 object and context control fields.[16, 17, 36, 37]

---
name: ledger-integrity-skill
description: Comprehensive tool for modifying the financial ledger. This skill should be used when the user asks to "update balances", "record transactions", or "audit the ledger".
allowed-tools:
disable-model-invocation: false
user-invocable: true
context: fork
agent: data-auditor
effort: high
hooks:
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: "command"
          command: "python3 $CLAUDE_PROJECT_DIR/.claude/validators/ledger_audit.py"
          timeout: 45
          statusMessage: "Verifying ledger invariants..."
  Stop:
    - hooks:
        - type: "prompt"
          prompt: "Analyze the current transcript. Ensure every transaction recorded in the ledger has a corresponding entry in the audit_log.txt file. Return 'ok: true' if satisfied, or 'ok: false' with the missing transaction details."
---


yaml

Critical Field Analysis for Systems Reliability

The 

context: fork

 directive is the most powerful tool for ensuring "Context Isolation".[7, 17, 20] When this is set, the skill execution occurs in a dedicated sub-agent context.[17, 20] This sub-agent does not inherit the main conversation history, meaning its context window is 100% focused on the task instructions defined in the 

SKILL.md

 body.[7, 17, 20] This prevents "Context Poisoning," where irrelevant conversation history interferes with the precise logic required for data validation.[10]

The 

allowed-tools

 field implements the principle of least privilege at the skill level.[17, 36, 38] By restricting a validator skill to read-only tools or specific bash scripts, the engineer prevents the "Validation Regression" scenario where a flawed validator sub-agent accidentally modifies the code it was intended to audit.[36, 38, 39]

Multi-Agent Orchestration Architecture

In complex engineering environments, a single agent cannot handle the cognitive load of implementation and comprehensive validation simultaneously. A "Master Orchestrator" architecture is required to chain specialized sub-agents while maintaining a "Global Audit" layer.[20, 22, 40, 41]

The Master Orchestrator Prompt Pattern

The Master Orchestrator is a high-level agent whose system prompt defines the rules of task decomposition and delegation.[20, 22, 42] It acts as a "Strategic Command" that manages a team of specialists.[20, 22]

Operational Prompt Blueprint:

 

"You are the Lead Systems Architect. Your primary responsibility is to decompose complex user requests into discrete, verifiable milestones. You must NEVER perform implementation tasks directly. Instead, you will use the Task tool to delegate implementation to the 

feature-implementer

 sub-agent and validation to the 

quality-engineer

 sub-agent.

Isolation Rule:

 Every implementer must operate in a forked context.

Handoff Rule:

 Results from implementers must be written to the 

.claude/handoffs/

 directory as structured Markdown.

Audit Rule:

 No implementation is complete until the 

quality-engineer

 has verified the handoff against the project's data invariants.".[20, 25, 42, 43]

Ensuring Context Isolation and Global Auditing

Context isolation is maintained by ensuring each sub-agent handles exactly one task or file.[10, 20, 22, 24, 25] The Master Orchestrator stays "lean" by reading only the summarized outputs from these agents rather than their full tool transcripts.[22, 24, 25]

The "Global Audit" is enforced via a 

SubagentStop

 hook configured at the project level in 

.claude/settings.json

. This hook fires whenever any sub-agent completes its work, regardless of its specialization.[20]

Verbatim Global Audit Configuration:

{
  "hooks": {
    "SubagentStop":
      }
    ]
  }
}


json

This configuration ensures that the master orchestrator is automatically informed if a sub-agent has returned artifacts that fail the project's global safety or quality checks, even if the sub-agent’s internal reasoning believes the task was successful.[11, 20]

Validation Logic: The Python Blueprint for the "Right Thing" Check

The validation logic itself must be deterministic, fast, and capable of deep state analysis. Python is the industry standard for this layer because its rich library ecosystem (e.g., 

pandas

, 

ruff

, 

pyright

) allows for verification of both data integrity and code health.[31, 44]

Verbatim Python Validator Implementation

The following script implements a dual-layer audit: a 

ruff

 check for code health and a 

pandas

 check for financial data integrity.

#!/usr/bin/env python3
"""
Operational Validator Blueprint for Claude Code Closed-Loop Architecture.
Implements: 
1. Static Analysis Gate (Ruff)
2. Data Invariant Gate (Pandas)
3. Repair Protocol Trigger (Exit 2)
"""
import sys
import json
import subprocess
from pathlib import Path
import pandas as pd

def check_code_health(file_path):
    """Enforces strict linting standards using Ruff."""
    if not file_path or not file_path.endswith(".py"):
        return True
    
    # Run ruff check on the specific file touched by Claude
    result = subprocess.run(
        ["ruff", "check", "--format", "text", file_path],
        capture_output=True, text=True
    )
    
    if result.returncode!= 0:
        # Write exact linting errors to stderr for Repair Injection
        print(f"CRITICAL LINT ERROR in {file_path}:\n{result.stdout}", file=sys.stderr)
        return False
    return True

def validate_ledger_state(project_root):
    """Verifies balance increment invariants in the transaction ledger."""
    ledger_csv = Path(project_root) / "data/ledger.csv"
    if not ledger_csv.exists():
        return True
    
    try:
        df = pd.read_csv(ledger_csv)
        # Invariant: Account balance must always be positive
        negative_balances = df[df['balance'] < 0]
        if not negative_balances.empty:
            ids = negative_balances['account_id'].tolist()
            print(f"DATA_INTEGRITY_VIOLATION: Negative balance detected in accounts: {ids}", file=sys.stderr)
            return False
            
        # Invariant: Balance delta must match transaction log sum
        # (Simplified example of complex cross-table validation)
        if df['balance'].sum() > 1000000: # Example global cap
            print("DATA_INTEGRITY_VIOLATION: Total liquidity exceeds system cap.", file=sys.stderr)
            return False
            
    except Exception as e:
        print(f"VALIDATOR_SYSTEM_ERROR: {str(e)}", file=sys.stderr)
        return False
    return True

def main():
    # Parse hook input from stdin
    try:
        raw_input = sys.stdin.read()
        if not raw_input:
            sys.exit(0)
        input_data = json.loads(raw_input)
    except json.JSONDecodeError:
        sys.exit(0)

    # Context Extraction
    tool_name = input_data.get("tool_name")
    tool_input = input_data.get("tool_input", {})
    target_file = tool_input.get("file_path")
    project_root = input_data.get("cwd") or "."

    # Execute Validation Chain
    if tool_name in:
        # Code Gate
        if not check_code_health(target_file):
            sys.exit(2) # Enter Repair Cycle
            
        # Data Gate
        if not validate_ledger_state(project_root):
            sys.exit(2) # Enter Repair Cycle

    sys.exit(0) # All Checks Passed

if __name__ == "__main__":
    main()


python

This script exemplifies the "Deterministic Feedback Loop." By writing specific error messages to 

stderr

 and exiting with code 2, it transforms a standard tool call into a self-healing iteration.[4, 12, 16] The agent is not merely told "there is an error" but is given the exact output from 

ruff

 or the specific account IDs failing integrity checks, allowing it to perform a targeted fix.[4, 12]

Global vs. Specialized Safety: The Multi-Tier Security Model

A production-grade agentic system requires a tiered safety architecture that contrasts global "Damage Control" with specialized "Quality Gates".[7, 39, 45]

Global settings.json Hooks: The Damage Control Tier

Global hooks are defined in the user’s 

~/.claude/settings.json

 or a managed policy file.[2, 11, 45] These hooks are "Ambient Protection" layers that fire regardless of which skill or agent is currently active.[34, 39, 45] Their primary role is to block destructive system-level commands and prevent data exfiltration.[2, 9]

Typical Global Safety Patterns:

Shell Sanitization:

 A 

PreToolUse

 hook on the 

Bash

 tool that uses regex to deny commands like 

rm -rf /

, 

sudo

, or any attempts to modify system configuration files in 

/etc/

.[4, 11]

Credential Protection:

 A 

PreToolUse

 hook on the 

Read

 tool that returns a 

deny

 decision if the agent attempts to read 

.env

, 

.ssh/

, or any files matching known credential patterns.[2, 31, 46]

Administrative Oversight:

 Managed policy hooks that cannot be overridden by the project or user, ensuring that organizational compliance rules are enforced at the hardware level.[45]

Specialized Skill Hooks: The Architectural Tier

Skill hooks are defined within the front matter of specific component files.[16, 17] They represent "Domain-Specific Verification" and are active only when the agent is performing tasks relevant to that domain.[16, 34]

Typical Specialized Validation Patterns:

Schema Enforcement:

 A skill for interacting with a specific database API includes hooks to verify that all SQL queries follow the company’s naming conventions and index usage policies.[16, 34, 39]

API Protocol Checking:

 A skill for microservice integration uses hooks to run a custom "Protocol Checker" after any code change to ensure the agent hasn't broken the downstream consumer's contract.[34, 39]

Dependency Auditing:

 A skill for package management that triggers a vulnerability scan (e.g., using 

snyk

) whenever the agent attempts to add a new library to 

package.json

.[34]

Feature

Global Hooks (settings.json)

Specialized Skill Hooks (SKILL.md)

Enforcement Scope

Machine-wide / All Projects.[2, 45]

Domain-specific / Context-aware.[16, 34]

Primary Intent

Damage Control & Security.[2]

Quality, Style, & Invariants.[16]

Ownership

DevOps / IT Security.[45, 47]

Engineering Lead / Domain Expert.[17, 35]

Model Interaction

Binary Block (Deny/Allow).[18, 45]

Collaborative Repair (Feedback Injection).[4, 12]

Operational Guide and Verbatim Configuration Blocks

To operationalize this specification, the systems engineer must integrate the following configuration blocks into the project’s infrastructure.

Verbatim settings.json Project Configuration

This block, placed in 

.claude/settings.json

, ensures that every sub-agent turn is followed by a global artifact audit and that all shell commands are sanitized.

{
  "$schema": "https://code.claude.com/docs/en/settings.schema.json",
  "hooks": {
    "SubagentStop":
      }
    ],
    "PreToolUse":
      }
    ]
  }
}


json

Verbatim Skill-Based Hook Definition (Billing Logic)

This block is included in 

.claude/skills/ledger-management/SKILL.md

 to establish the closed-loop for financial operations.

---
name: ledger-management
hooks:
  PostToolUse:
    - matcher: "Edit|Write|MultiEdit"
      hooks:
        - type: "command"
          command: "python3 scripts/validate_ledger.py"
          statusMessage: "Running financial invariant checks..."
  Stop:
    - hooks:
        - type: "agent"
          agent: ledger-validator
          prompt: "Verify that all changes to ledger.csv match the transaction descriptions in the audit log."
---


yaml

The Validation-Repair Loop Sequence Diagram

The following narrative describes the high-fidelity sequence of a closed-loop validation session, mapping the interaction between the User, Master Orchestrator, Validation Engine, and Specialized Sub-agent.

Request Initiation:

 The user submits a prompt: "Increase the transaction fee to 5% and update the historical ledger records for the current quarter to reflect the new processing overhead."

Strategic Decomposition:

 The Master Orchestrator parses the prompt. It identifies the need for financial domain expertise and invokes the 

ledger-management

 skill with 

context: fork

.[20, 22]

Specialist Initialization:

 A new sub-agent, the 

data-auditor

, is spawned in an isolated context. The 

ledger-management

 skill body is loaded as its primary system prompt, and the scoped 

PostToolUse

 hooks are registered for the session.[7, 16, 17]

The Action Step:

 The sub-agent reasons that it must first update 

overhead_constants.py

 and then run a bulk SQL update on the ledger files. It calls the 

Edit

 tool on 

overhead_constants.py

.

Quality Gate (Iterative):

 Immediately after the file is saved, the 

PostToolUse

 hook fires. The Python validator executes 

ruff

. It finds no linting errors and exits code 0. The agent proceeds.[4, 30, 31]

The Invariant Breach:

 The sub-agent now calls the 

Bash

 tool to execute the SQL update. The command succeeds, and the ledger file is modified.

The Repair Trigger:

 The 

PostToolUse

 hook fires again. It runs the 

pandas

 validation logic. The validator detects that the 5% overhead calculation has resulted in a global liquidity balance that exceeds the system's "Cap Invariant" defined in the source code.

Instruction Injection:

 The validator script writes the following to 

stderr

: "INVARIANT_BREACH: The total sum of the ledger balances (

1.2M) exceeds the defined system cap (

1.0M). The requested fee increase cannot be finalized." The script exits with code 2.[12, 16]

Agent Remediation:

 The harness interrupts the agent's turn. The agent receives the error. It updates its world model: it cannot simply increase the fee without violating global liquidity constraints. It proposes a "Tiered Fee" model instead to stay within the cap.[5, 6, 12]

The Successful Turn:

 The agent performs a new set of edits. The 

PostToolUse

 validator re-runs. All checks pass (Exit 0).

The Global Audit:

 The sub-agent signals task completion. The 

SubagentStop

 hook fires at the Master level. A separate validator agent reviews the handoff summary and confirms that the final architecture meets all safety criteria.[20]

Completion:

 The Master Orchestrator presents the final results to the user.

Strategic Conclusions for Systems Engineering

Implementing a closed-loop validation architecture using Claude Code Skill-Based Hooks marks the transition from conversational AI to automated systems engineering. By defining 100% operational specifications for each lifecycle event, the Senior Agentic Systems Engineer ensures that correctness is a property of the system’s architecture rather than a product of the model’s internal consistency.[1, 2, 3]

The integration of the Exit Code 2 Repair Protocol provides a robust mechanism for forcing agents to prioritize remedial cycles, while the use of 

context: fork

 and specialized sub-agents mitigates the risks of token bloat and context contamination.[12, 22, 25] As agentic capabilities continue to expand, the ability to build deterministic, cross-platform validation engines will be the defining characteristic of elite engineering teams operating at the frontier of autonomous development.


--------------------------------------------------------------------------------


Claude Code hooks: A practical guide with examples (2026) - eesel AI, 

https://www.eesel.ai/blog/hooks-in-claude-code

https://www.eesel.ai/blog/hooks-in-claude-code

Understanding Claude Code hooks documentation - PromptLayer Blog, 

https://blog.promptlayer.com/understanding-claude-code-hooks-documentation/

https://blog.promptlayer.com/understanding-claude-code-hooks-documentation/

Agents that run while I sleep | Hacker News, 

https://news.ycombinator.com/item?id=47327559

https://news.ycombinator.com/item?id=47327559

Claude Code Hooks: The Deterministic Control Layer for AI Agents - Dotzlaw Consulting, 

https://www.dotzlaw.com/insights/claude-hooks/

https://www.dotzlaw.com/insights/claude-hooks/

From Error to Fix in Seconds: Claude Code Live Preview Explained : r/AISEOInsider - Reddit, 

https://www.reddit.com/r/AISEOInsider/comments/1rero9c/from_error_to_fix_in_seconds_claude_code_live/

https://www.reddit.com/r/AISEOInsider/comments/1rero9c/from_error_to_fix_in_seconds_claude_code_live/

Claude Code Workflow: Create Tight Feedback Loops, 

https://claudefa.st/blog/guide/development/feedback-loops

https://claudefa.st/blog/guide/development/feedback-loops

A Mental Model for Claude Code: Skills, Subagents, and Plugins | by Dean Blank, 

https://levelup.gitconnected.com/a-mental-model-for-claude-code-skills-subagents-and-plugins-3dea9924bf05

https://levelup.gitconnected.com/a-mental-model-for-claude-code-skills-subagents-and-plugins-3dea9924bf05

Claude Code Hooks - DEV Community, 

https://dev.to/helderberto/claude-code-hooks-1k7a

https://dev.to/helderberto/claude-code-hooks-1k7a

Claude Code Hooks: Automate Your AI Coding Workflow - Kyle Redelinghuys, 

https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

https://www.ksred.com/claude-code-hooks-a-complete-guide-to-automating-your-ai-coding-workflow/

Learning Claude Code — From Context Engineering to Multi-Agent Workflows - Medium, 

https://medium.com/@aayushmnit/learning-claude-code-from-context-engineering-to-multi-agent-workflows-4825e216403f

https://medium.com/@aayushmnit/learning-claude-code-from-context-engineering-to-multi-agent-workflows-4825e216403f

Hooks reference - Claude Code Docs, 

https://code.claude.com/docs/en/hooks

https://code.claude.com/docs/en/hooks

Automate workflows with hooks - Claude Code Docs, 

https://code.claude.com/docs/en/hooks-guide

https://code.claude.com/docs/en/hooks-guide

I tried verifying all patterns of Claude Code's SessionStart hook (Windows 11 + MINGW64), 

https://dev.classmethod.jp/en/articles/claude-code-session-start-hook-verification/

https://dev.classmethod.jp/en/articles/claude-code-session-start-hook-verification/

disler/claude-code-hooks-mastery - GitHub, 

https://github.com/disler/claude-code-hooks-mastery

https://github.com/disler/claude-code-hooks-mastery

Intercept and control agent behavior with hooks - Claude API Docs, 

https://platform.claude.com/docs/en/agent-sdk/hooks

https://platform.claude.com/docs/en/agent-sdk/hooks

claude-code/plugins/plugin-dev/skills/hook-development/SKILL.md at main - GitHub, 

https://github.com/anthropics/claude-code/blob/main/plugins/plugin-dev/skills/hook-development/SKILL.md

https://github.com/anthropics/claude-code/blob/main/plugins/plugin-dev/skills/hook-development/SKILL.md

Extend Claude with skills - Claude Code Docs, 

https://code.claude.com/docs/en/skills

https://code.claude.com/docs/en/skills

Secure Your Claude Skills with Custom PreToolUse Hooks | egghead.io, 

https://egghead.io/secure-your-claude-skills-with-custom-pre-tool-use-hooks~dhqko

https://egghead.io/secure-your-claude-skills-with-custom-pre-tool-use-hooks~dhqko

Claude Code Hooks: A Practical Guide to Workflow Automation - DataCamp, 

https://www.datacamp.com/tutorial/claude-code-hooks

https://www.datacamp.com/tutorial/claude-code-hooks

Create custom subagents - Claude Code Docs, 

https://code.claude.com/docs/en/sub-agents

https://code.claude.com/docs/en/sub-agents

Building Effective AI Coding Agents for the Terminal: Scaffolding, Harness, Context Engineering, and Lessons Learned - arXiv, 

https://arxiv.org/html/2603.05344v3

https://arxiv.org/html/2603.05344v3

AI Led Development + Growth Marketing Kits - Claude Fast, 

https://claudefa.st/readme

https://claudefa.st/readme

[BUG] Hook environment variables and $CLAUDE_TOOL_INPUT are always empty/unknown · Issue #9567 · anthropics/claude-code - GitHub, 

https://github.com/anthropics/claude-code/issues/9567

https://github.com/anthropics/claude-code/issues/9567

Built a multi-agent orchestrator to save context - here's what actually works (and what doesn't) : r/ClaudeCode - Reddit, 

https://www.reddit.com/r/ClaudeCode/comments/1q8diyu/built_a_multiagent_orchestrator_to_save_context/

https://www.reddit.com/r/ClaudeCode/comments/1q8diyu/built_a_multiagent_orchestrator_to_save_context/

Built a multi-agent orchestrator to save context - here's what actually works (and what doesn't) : r/ClaudeAI - Reddit, 

https://www.reddit.com/r/ClaudeAI/comments/1q8884m/built_a_multiagent_orchestrator_to_save_context/

https://www.reddit.com/r/ClaudeAI/comments/1q8884m/built_a_multiagent_orchestrator_to_save_context/

[DOCS] Conflicting JSON Response Schemas for Hook Events (

PreToolUse

 vs 

PostToolUse

) · Issue #19115 · anthropics/claude-code - GitHub, 

https://github.com/anthropics/claude-code/issues/19115

https://github.com/anthropics/claude-code/issues/19115

Claude Code overview - Claude Code Docs, 

https://code.claude.com/docs/en/overview

https://code.claude.com/docs/en/overview

Claude Code Frontend Dev - AI Visual Testing Plugin - GitHub, 

https://github.com/hemangjoshi37a/claude-code-frontend-dev

https://github.com/hemangjoshi37a/claude-code-frontend-dev

Getting Started with Claude Code for Data Scientists - Dataquest, 

https://www.dataquest.io/blog/getting-started-with-claude-code-for-data-scientists/

https://www.dataquest.io/blog/getting-started-with-claude-code-for-data-scientists/

Typifying 1000 Python files with Ruff + Claude | by Yair Morgenstern - Medium, 

https://yairm210.medium.com/typifying-1000-python-files-with-ruff-claude-afbea6eba94d

https://yairm210.medium.com/typifying-1000-python-files-with-ruff-claude-afbea6eba94d

Python > Bash for writing Claude Code Hooks - with 4 examples : r/ClaudeAI - Reddit, 

https://www.reddit.com/r/ClaudeAI/comments/1n1o29s/python_bash_for_writing_claude_code_hooks_with_4/

https://www.reddit.com/r/ClaudeAI/comments/1n1o29s/python_bash_for_writing_claude_code_hooks_with_4/

Inside Claude Code Skills: Structure, prompts, invocation | Mikhail Shilkov, 

https://mikhail.io/2025/10/claude-code-skills/

https://mikhail.io/2025/10/claude-code-skills/

Complete guide to building Skills for Claude — covers fundamentals, planning, testing, distribution, patterns, and YAML frontmatter reference (converted from Anthropic's official PDF) - GitHub Gist, 

https://gist.github.com/joyrexus/ff71917b4fc0a2cbc84974212da34a4a

https://gist.github.com/joyrexus/ff71917b4fc0a2cbc84974212da34a4a

Top 8 Claude Skills for Developers - Snyk, 

https://snyk.io/articles/top-claude-skills-developers/

https://snyk.io/articles/top-claude-skills-developers/

Claude Skills Explained: Build, Configure, and Use Custom Skills on Claude Code, 

https://www.analyticsvidhya.com/blog/2026/03/claude-skills-custom-skills-on-claude-code/

https://www.analyticsvidhya.com/blog/2026/03/claude-skills-custom-skills-on-claude-code/

Essential Claude Code Skills and Commands - Bozhidar Batsov, 

https://batsov.com/articles/2026/03/11/essential-claude-code-skills-and-commands/

https://batsov.com/articles/2026/03/11/essential-claude-code-skills-and-commands/

claude-code-best-practice/best-practice/claude-skills.md at main - GitHub, 

https://github.com/shanraisshan/claude-code-best-practice/blob/main/best-practice/claude-skills.md

https://github.com/shanraisshan/claude-code-best-practice/blob/main/best-practice/claude-skills.md

How Sub-Agents Work in Claude Code: A Complete Guide | by Kinjal Radadiya | Medium, 

https://medium.com/@kinjal01radadiya/how-sub-agents-work-in-claude-code-a-complete-guide-bafc66bbaf70

https://medium.com/@kinjal01radadiya/how-sub-agents-work-in-claude-code-a-complete-guide-bafc66bbaf70

Customizing Claude Code for Python Development: A Practical Guide | by Syed Asif, 

https://python.plainenglish.io/customizing-claude-code-for-python-development-a-practical-guide-25b5a2833e9c

https://python.plainenglish.io/customizing-claude-code-for-python-development-a-practical-guide-25b5a2833e9c

Multi-agent orchestration for Claude Code in 2026 - Shipyard.build, 

https://shipyard.build/blog/claude-code-multi-agent/

https://shipyard.build/blog/claude-code-multi-agent/

Building a Multi-Agent AI Orchestrator with Claude Code - Mae Capozzi, 

https://maecapozzi.com/blog/building-a-multi-agent-orchestrator

https://maecapozzi.com/blog/building-a-multi-agent-orchestrator

GitHub - lst97/claude-code-sub-agents: Collection of specialized AI subagents for Claude Code for personal use (full-stack development)., 

https://github.com/lst97/claude-code-sub-agents

https://github.com/lst97/claude-code-sub-agents

CLAUDE.md Mastery: Your AI's Operating System, 

https://claudefa.st/blog/guide/mechanics/claude-md-mastery

https://claudefa.st/blog/guide/mechanics/claude-md-mastery

I built a tool that tells Claude Code what exceptions Python functions can raise - here's how I use it : r/ClaudeAI - Reddit, 

https://www.reddit.com/r/ClaudeAI/comments/1q1vkj2/i_built_a_tool_that_tells_claude_code_what/

https://www.reddit.com/r/ClaudeAI/comments/1q1vkj2/i_built_a_tool_that_tells_claude_code_what/

Claude Code settings - Claude Code Docs, 

https://code.claude.com/docs/en/settings

https://code.claude.com/docs/en/settings

Hooks - ClaudeKit Documentation, 

https://docs.claudekit.cc/docs/engineer/configuration/hooks

https://docs.claudekit.cc/docs/engineer/configuration/hooks

Claude Code Organisation Rollout Playbook | systemprompt.io, 

https://systemprompt.io/guides/claude-code-organisation-rollout

https://systemprompt.io/guides/claude-code-organisation-rollout
