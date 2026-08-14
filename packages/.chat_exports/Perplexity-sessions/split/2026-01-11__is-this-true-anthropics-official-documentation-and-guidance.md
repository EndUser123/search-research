---
title: "Is this true?
Anthropic's official documentation and guidance specify the following regarding 
CLAUDE.md:

Preferred Loc"
date: "2026-01-11"
mode: "COPILOT"
uuid: "6be4cf6a-2a53-4be8-93de-19a3a7e27f1c"
entry_count: 1
---

## Human

Is this true?
Anthropic's official documentation and guidance specify the following regarding 
CLAUDE.md:

Preferred Location: The Project Root (
your-repo/CLAUDE.md
) is the standard, authoritative location. This ensures the entire team shares the same context when checked into version control.
Global Fallback: 
~/.claude/CLAUDE.md
 (Global User Memory) is used for user-specific preferences across all projects.
Local Override: 
CLAUDE.local.md
 is supported for uncommitted, local-only instructions (add to .gitignore).
No .claude/CLAUDE.md Standard: There is no mention of keeping the project configuration inside a 
.claude/
 subdirectory (e.g., .claude/CLAUDE.md) as a standard practice. It supports parent/child directory inheritance, but the convention is explicitly CLAUDE.md at the root of the context you want to control.

## Assistant

## Is This Statement True? A Verification Against Official Anthropic Documentation

The claim contains **a mix of accurate and inaccurate statements** compared to Anthropic's official documentation. Here's the detailed breakdown:

### Accurate Claims

**Project Root as preferred location**: The statement that `your-repo/CLAUDE.md` in the project root is "the standard, authoritative location" is essentially correct. The official documentation describes it as "the most common usage" and recommends checking it into git to share across the team.[1][2]

**Global Fallback location**: The statement about `~/.claude/CLAUDE.md` being used for user-specific preferences across all projects is accurate.[3][1]

**CLAUDE.local.md support**: The claim that `CLAUDE.local.md` is supported for uncommitted, local-only instructions and should be added to `.gitignore` is correct.[4][1]

### Inaccurate Claims

**No standard for `.claude/CLAUDE.md`**: This is **incorrect**. Contrary to the statement, Anthropic's official documentation explicitly documents `./.claude/CLAUDE.md` as a valid and supported location for project memory. The official docs state: "Project memory can be stored in either `./CLAUDE.md` or `./.claude/CLAUDE.md`."[1]

The official memory types table shows both locations as equivalent options: `./CLAUDE.md` or `./.claude/CLAUDE.md` Additionally, the `.claude/` directory structure is actively promoted by Anthropic for organizing modular rules through `.claude/rules/*.md`, making `.claude/CLAUDE.md` an integrated part of the official directory convention, not an unsupported practice.[1]

### Key Difference

The statement claims there is "no mention of keeping the project configuration inside a `.claude/` subdirectory...as a standard practice." However, the official Anthropic documentation explicitly documents both locations as equal alternatives:

> "Project memory can be stored in either `./CLAUDE.md` or `./.claude/CLAUDE.md`."[1]

The `.claude/` directory structure is not merely "supported" as a fallback—it's an official first-class option alongside the project root, and Anthropic actively recommends organizing rules within `.claude/rules/` as part of their standard modular approach.[1]

### Summary

The statement is **partially false**. While the claims about project root preference and global/local memory locations are accurate, the assertion that `.claude/CLAUDE.md` lacks official standard status contradicts Anthropic's current documentation, which explicitly treats both `./CLAUDE.md` and `./.claude/CLAUDE.md` as supported, equivalent options for project memory configuration.
