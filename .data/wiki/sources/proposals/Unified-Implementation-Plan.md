# **Implementation Plan: Handoff & Recap Unified Architecture**

## **1\. Executive Summary**

This document is the definitive technical blueprint for a session continuity system. It links **Ground Truth (Git)** to **Rationale (Transcript)** using decentralized discovery, an **Action-Intent-Result (AIR)** auditing framework, and a proactive **Pre-mortem Protocol**.

## **2\. The Commit Policy (Traceability)**

Every change must be anchored to a session ID to enable "Why" analysis.

* **Session Tagging**: Every commit message must include the tag \[Session: \<sessionId\>\].  
* **Task Mapping**: Where possible, include the task ID: \[Task: \#104\] \[Session: abc-123\].  
* **Auto-Commit Hook**: Update the auto-fix pipeline to fetch $SESSION\_ID and append it to the commit.  
* **Manual Hook**: Install a .git/hooks/prepare-commit-msg to auto-inject the session ID into manual commits.

## **3\. The AIR Auditor (Decision Extraction)**

Use this triangulation logic to identify verified decisions:

* **The Signals**:  
  1. **Action**: A verified git diff or tool execution.  
  2. **Intent**: A goal found in the transcript, anchored to the **last explicit User Directive**.  
  3. **Result**: Absence of user "Veto" (e.g., "Stop," "Undo") in the subsequent 2 turns.  
* **Gap Analysis (Disagreement Handling)**:  
  * **Shadow Decisions (Action \> Intent)**: If code changed without intent, categorize as a **Silent Pivot**. Justify using terminal evidence (e.g., "Pytest Exit Code 1").  
  * **Ghost Decisions (Intent \> Action)**: If intent was stated but no code changed, flag as "Hallucinated" and ignore.  
  * **Reverts**: If no technical evidence exists for a pivot, flag as "Unjustified" for manual review.

## **4\. Decentralized Recap Logic**

The /recap tool reconstructs history on-demand without a global database.

* **Discovery**: Scan local staging (\_\_csf/.staging/handovers/) and current transcripts to resolve IDs.  
* **Blame Correlation**: Use git blame to find the Session ID, then fetch the corresponding transcript segments.  
* **Recapping Deletion**: Since git blame only shows existing lines, the tool must optionally use git log \-S or git log \--patch to find the "Why" behind deleted code.  
* **Semantic Drift**: The LLM evaluates if the *logic* of an old decision is still valid or if it has been **Superseded**.

## **5\. The Pre-mortem Protocol (Prevention)**

Before implementing or committing, the agent must simulate failure:

* **Micro-Audit**: "Is this implementation (e.g., regex/path) too rigid? Will it fail if spacing or OS changes?"  
* **Macro-Audit (Meta-Check)**: "Assume I am a new LLM with no context. Does my Handoff/Commit rationale provide enough **Evidence** for me to understand **Why** this was chosen?"  
* **Historical Intent Check**: Before changing code tagged with a previous session ID, verify that the new change doesn't violate the original AIR-verified intent.

## **6\. Output Standard: The "Quick Argument"**

Summaries must follow this evidence-based structure:

| Field | Description |
| :---- | :---- |
| **Type** | Directed, 🔄 Silent Pivot, or Heuristic (if no hard evidence) |
| **Action** | Technical description of the change. |
| **Evidence** | The trigger (e.g., Pytest ImportError, Mypy Error). |
| **Rationale** | Tactical justification for the implementation. |

## **7\. Human-in-the-Loop**

* **Rationale Overrides**: Provide a way for the user to manually refine the "Quick Argument" if the LLM's evidence-based guess is technically correct but logically misaligned with user intent.

## **8\. Implementation Steps**

1. **Update SKILL.md**: Inject Sections 5 and 6 into the system instructions for /handoff and /recap.  
2. **Install Hooks**: Setup the git prepare-commit-msg for session traceability.  
3. **Refine Pipeline**: Ensure all automated scripts include the session tag in commits.