---
title: "$PSVersionTable.PSVersion"
date: "2025-12-22"
mode: "COPILOT"
uuid: "4f367fa9-cdf7-4115-ba3f-2d2e46444032"
entry_count: 1
---

## Human

$PSVersionTable.PSVersion

## Assistant

`$PSVersionTable.PSVersion` is a PowerShell variable expression that prints the version of PowerShell you are running.[1]

## What the command does

- `$PSVersionTable` is an automatic **hashtable** that contains details about the current PowerShell session (version, edition, OS, etc.).[1]
- `.PSVersion` accesses the `PSVersion` entry in that table, returning a `System.Version` object like `7.4.2` that Cline’s docs use to verify you’re on PowerShell 7+.[1]

## Why it matters for Cline/VS Code

- Cline’s shell integration guide specifically tells Windows users to run `$PSVersionTable.PSVersion` and ensure the result is at least version 7 if they want to use PowerShell instead of Git Bash.[1]
- If the version is below 7, the guide recommends upgrading PowerShell 7 using Microsoft’s installation instructions before relying on shell integration.[1]
