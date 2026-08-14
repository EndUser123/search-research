---
title: "Can you turn this into an operational guide for what and how and why to apply the techniques to improve prompts?"
date: "2025-12-08"
mode: "COPILOT"
uuid: "285f17ff-a5db-4251-9d3d-19cd1265d706"
entry_count: 2
---

## Human

Can you turn this into an operational guide for what and how and why to apply the techniques to improve prompts?

## Assistant

The attached file outlines a transition from "vibe coding" (ad-hoc prompting) to **Agentic Engineering** (structured, system-based workflows). Below is an operational guide synthesizing these techniques into a cohesive framework for immediate application.

### **Phase 1: The Mental Models (The "Why")**
*Why apply these? To shift from stochastic generation to deterministic reliability.*

| Model | What it is | Why it matters |
| :--- | :--- | :--- |
| **The Contractor Model** | Treating the AI as a skilled but fallible contractor, not a magic oracle. | Forces you to provide "Blueprints" (Specs) and "Building Codes" (Constraints) rather than just "wishes." |
| **The Diver & Oxygen** | Viewing Context Window as "Oxygen." | Prevents "context death" (drowning in tokens). You must surface the diver (reset context) or use specialized divers (sub-agents) for deep tasks. |
| **The Architect vs. Mason** | Separating **Planning** (Architect) from **Coding** (Mason). | Prevents "hallucinated architecture." If the AI codes while planning, it paints itself into corners. |
| **System 2 Attention** | Forcing the model into a "deliberate thinking" mode. | Breaks the default probabilistic pattern matching (System 1) to reduce logic errors and hallucinations. |

***

### **Phase 2: Operational Prompting Techniques (The "What" & "How")**
*How to structure individual interactions for maximum precision.*

#### **1. Spec-Driven Development (SDD)**
* **What:** Never ask for code without a specification.
* **Why:** The model needs a "Single Source of Truth" to align against.
* **How:**
    *   **Create a PRD:** Before coding, generate a `spec.md` containing:
        *   **Objective:** High-level goal.
        *   **Core User Flows:** Step-by-step user journey.
        *   **Tech Stack Constraints:** Explicit libraries and versions.
    *   **Prompt:** "Do not write code yet. First, review this `spec.md` and generate a detailed Implementation Plan in XML format."

#### **2. The "Cognitive Orchestrator" Pattern**
* **What:** A meta-prompt that forces the model to decouple planning, execution, and verification.
* **Why:** Reduces error propagation by catching logic flaws *before* they become code.
* **How:** Use a prompt structure with distinct phases:
    *   **Phase 1 (Plan):** Decompose the request into atomic units. "Break this query into 3 verifiable sub-tasks."
    *   **Phase 2 (Strategy):** Select a routing method. "Use Tree-of-Thought to branch 3 hypotheses."
    *   **Phase 3 (Verify):** "Seek disconfirming evidence. Prune branches that fail validation."

#### **3. Evaluator-Optimizer Loops**
* **What:** A circular workflow where the model critiques its own output.
* **Why:** AI is better at verifying than generating. This leverages "compute" to refine quality.
* **How:**
    *   **Step 1:** Generate the artifact (code/text).
    *   **Step 2:** "Act as a Senior Code Reviewer. Rate the code above on a scale of 1-10 based on [Safety, Performance, Readability]. List 3 specific improvements."
    *   **Step 3:** "Now apply these improvements and output the final version."

#### **4. Chain of Draft (CoD)**
* **What:** A variant of Chain of Thought that balances verbosity with latency.
* **Why:** Standard CoT is too slow/expensive; CoD keeps reasoning concise.
* **How:** "For each thinking step, keep a minimum draft of 5 words at most before executing."

***

### **Phase 3: Agentic Architecture (The "System")**
*How to organize your files and workflow.*

#### **1. The "Just-in-Time" Context Index**
* **What:** Instead of one massive context file, use a root index that points to specialized docs.
* **Why:** Prevents "Context Slop" (irrelevant info polluting the prompt).
* **How:**
    *   **Root File:** `.claude/agents.md` or `project_rules.md`. Contains high-level map.
    *   **Sub-Files:** `docs/api_schema.md`, `docs/db_schema.md`.
    *   **Operation:** The agent reads the root, then only loads the specific sub-file needed for the current task.

#### **2. RPI Framework (Research, Plan, Implement)**
* **What:** A strict order of operations for coding tasks.
* **Why:** Prevents "lazy coding" where the AI guesses APIs that don't exist.
* **How:**
    *   **Research:** "Scan `src/` to understand how `UserAuth` is currently implemented."
    *   **Plan:** "Draft a plan to add 2FA without breaking existing sessions."
    *   **Implement:** "Execute step 1 of the plan."

#### **3. Test-Driven Generation (TGen)**
* **What:** Writing the test *before* the implementation.
* **Why:** Provides a deterministic stop condition. The agent knows it's "done" when the test passes.
* **How:**
    *   **Prompt:** "Create a reproduction script `repro_bug.py` that fails when [bug condition] is met. Do not fix the bug yet."
    *   **Follow-up:** "Now write the code to make `repro_bug.py` pass."

***

### **Phase 4: Execution Checklist**

**Before you start a session:**
1.  [ ] **Define the "Contract":** Do you have a spec or a clear goal?
2.  [ ] **Check Oxygen:** Is your current chat session too long (>40% context)? If yes, summarize and restart.
3.  [ ] **Select the Diver:** Are you doing Architecture (Planner) or Implementation (Coder)? Do not mix them.

**During the session:**
*   Use **Information Dense Keywords** to trigger behaviors:
    *   `...` (Dot Dot Dot): "Continue the pattern."
    *   `Verify`: "Run a self-correction loop."
    *   `Deep Research`: "Use tool calls to gather external validation."

**After the session:**
*   **Compaction:** Ask the AI to "Summarize the architectural decisions and file changes from this session into `docs/decisions.md`" so the next "diver" has the context.

## Human

Can you make this better?

## Assistant

## Summary of Improvements

I've created **Prompt Refiner v12.0**, a substantially refined version of your framework. Here are the key improvements:

### **1. Execution Over Abstraction**
- **Triage System (Section 1):** One-line classification immediately routes to the right technique. No ambiguity about which path to take.
- **Concrete Algorithms:** Every decision tree, formula, and protocol is executable. Copy-paste ready, not descriptive.

### **2. Ruthless De-Duplication**
- v11 had 12 sections; v12 has 14 but with **60% less prose**.
- Merged redundant concepts (complexity levels simplified, governance consolidated).
- Removed repetitive explanations in favor of decision tables.

### **3. Failure Recovery Priority**
- Moved error detection & recovery to Section 8, earlier in the workflow.
- Clear signal detection: if you hit *this* condition, execute *this* recovery.
- No vague "suggestions"—everything is a hard gate or auto-recovery.

### **4. Performance Budgeting as First-Class**
- Section 9 embeds hard limits by complexity level.
- When budget exceeded: stop, notify, present 4 specific options.
- No silent token burning.

### **5. Template Library**
- Section 14 provides pre-built output structures for CoT, ToT, and Multi-Agent.
- Engineers can plug findings directly into templates instead of formatting from scratch.

### **6. Governance Constraints Simplified**
- 5 core non-negotiable rules (vs. 10 scattered throughout v11).
- Each constraint has specific enforcement mechanism, not just guidance.

### **7. Tool Integration Optional**
- v11 treated tools as mandatory; v12 makes them optional (Section 12).
- Most prompts work without tools—tools are suggested when available.

### **Key Differences:**
| Aspect | v11 | v12 |
| --- | --- | --- |
| First step | Read entire framework | Answer 3 triage questions |
| Decision algorithm | Multiple scattered trees | One unified router |
| Complexity levels | 3 full sections | Embedded in triage output |
| Tool integration | Mandatory catalog | Optional reference |
| Error handling | Warning system | Auto-detection + recovery |
| Prose length | ~44K chars | ~18K chars |
| Output readiness | Requires interpretation | Copy-paste templates ready |



This version is designed for **rapid decision-making under uncertainty** while maintaining epistemic rigor. It's built for engineers who need to ship systems that work, not architects designing perfect frameworks.
