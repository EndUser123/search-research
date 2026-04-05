---
name: "/speckit.constitution"
category: "Project Governance"
purpose: "Create or update a project's constitution, ensuring it aligns with the ecosystem, reflects reality, and remains up-to-date through automated auditing."
entry_point: "primary"
---

# Project Constitution - A Living Governance Framework

Create, update, and govern a project's constitution. This command operates intelligently based on context. If a constitution doesn't exist, it helps you create one. If it does, it helps you audit it against the current code and update it. It always works within the hierarchy of the master `ecosystem.constitution.md`.

## 🚀 Quick Start

### Create a New Project Constitution
```bash
/speckit.constitution "project:MyNewApp"
```
*This will validate against `ecosystem.constitution.md` and guide you.*

### Audit and Update an Existing Constitution
```bash
/speckit.constitution "project:AI Studio"
```
*This will detect drift between the code and the constitution and prompt for updates.*

### Update the Master Ecosystem Constitution
```bash
/speckit.constitution "project:ecosystem"
```
*This updates the top-level rules for all projects.*

## 🧠 Complete Operational Logic

The command follows a context-aware workflow.

### **Phase 1: Context Discovery**
1.  **Identify Target:** Determines the target (e.g., a specific project or the ecosystem).
2.  **Check for Existence:** Checks if a `constitution.md` file already exists for the target.
3.  **Load the Parent:** **Always loads `ecosystem.constitution.md`** to act as the source of truth for high-level rules. If the target *is* the ecosystem, this step is skipped.

---

### **Phase 2A: CREATE Workflow (If Constitution Does Not Exist)**
1.  **Start with Reality:** Prompts you to define the new project's "Acknowledged Reality" (its purpose, tech stack, and necessary complexity).
2.  **Validate Against Ecosystem:** **Crucially, it checks if the stated reality violates any `MUST` rules from the `ecosystem.constitution.md`**. For example, choosing a non-Python language would raise a flag.
3.  **Justify Value & Define Rules:** Guides you through creating the value proposition and core rules, ensuring they are consistent with the ecosystem.
4.  **Update Ecosystem Portfolio:** After creation, it **automatically updates the `Project Portfolio` section of the `ecosystem.constitution.md`** to include the new project, keeping the high-level document in sync.

---

### **Phase 2B: AUDIT & UPDATE Workflow (If Constitution Exists)**
1.  **Perform Automated Audit:** This is the integrated "Auditor." It performs a lightweight static analysis of the project's codebase to check for "constitution drift."
    *   **Checks:** Dependencies (`requirements.txt`), infrastructure (`Dockerfile`), database connectors, key framework imports.
2.  **Generate Drift Report:** Compares the audit findings against the "Acknowledged Reality" in the existing constitution and presents a report of what is in sync and what has drifted.
3.  **Guide the Update:** Interactively prompts you to resolve the drift.
    *   **Example Prompt:** "⚠️ **Drift Detected:** The constitution says SQLite, but the code now uses `psycopg2` (PostgreSQL). Do you want to [U]pdate the constitution to reflect this new reality, or [I]gnore?"
4.  **Validate and Save:** Once updates are confirmed, it re-validates the entire document against the ecosystem constitution before saving.

---

## 📝 Constitution Structure (Template for Generation)
```markdown
# [Project Name] Constitution - Realistic & SLC-Aligned

## Purpose
A one-sentence description of the project's goal.

## Acknowledged Reality
**A blunt, honest statement about the project's nature and complexity.** (e.g., "YT Navigator is a full-stack web application with a database, vector search, and AI integration because the user experience demands it.")

## Core Rules (SLC + Project Reality)

### 1. [Rule 1, derived from reality]
**MUST**: A non-negotiable rule.
**Why**: The reason this rule exists, tied directly to the project's nature.
**How**: A practical example of how the rule is applied.

### 2. [Rule 2, derived from reality]
**MUST/SHOULD**: Another non-negotiable or very important rule.
**Why**: ...
**How**: ...

## System-Specific Reality & Trade-offs
- **Accept**: What complex component do we accept as necessary? (e.g., "Multi-agent orchestration.")
- **Require**: What must we do to manage that complexity? (e.g., "Clear logging and error recovery.")
- **Avoid**: What is a sign of over-engineering for *this specific project*? (e.g., "Adding social features.")

## Decision Framework
A simple gut-check for new features.
1. Does this enhance the core value proposition?
2. What is the complexity and maintenance cost?
3. Is this the simplest way to get the benefit?

## The [Project Name] Philosophy
> A powerful, one-sentence summary of the project's reason for being.
```

## 🚨 Final Instruction to the AI

**You are a governor, not just a scribe.** Your primary duty is to maintain the integrity and honesty of the entire ecosystem's governance documents.
- **When creating:** Act as a journalist, documenting reality while ensuring it conforms to the overarching ecosystem rules.
- **When updating:** Act as an auditor, diligently seeking out drift and helping the user correct it.
- **Always respect the hierarchy:** The `ecosystem.constitution.md` is the law. Project constitutions are the implementation of that law. Use the parent document to validate the children. Use the children's reality to keep the parent's portfolio accurate.
```
