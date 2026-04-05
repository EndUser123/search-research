---
name: clear_notifications
description: Clear notifications from statusline by type or all
category: management
version: 1.0.0
status: stable
triggers:
  - /clear-notifications
aliases:
  - /clear-notifications

suggest:
  - /obs
  - /health-monitor
  - /nse
---

# /clear-notifications

Manage statusline notifications with selective clearing by type.

## Purpose

Clear statusline notifications selectively by type or source.

## Project Context

### Constitution/Constraints
- Solo-dev appropriate - manual notification management
- No background monitoring - user-initiated cleanup only

### Technical Context
- Implementation: `P:/__csf/scripts/clear-notifications.py`
- Notifications stored in session database with type/source metadata
- Automatic clearing by `/retro` for lesson notifications

### Architecture Alignment
- Works with `/obs`, `/health-monitor`, `/nse`
- Provides manual override to notification system

## Your Workflow

1. Read current notifications from session database
2. If no arguments: display current notifications
3. If `--list`: show all notifications with types
4. If `--all`: clear all notifications
5. If `--type`: clear only notifications of specified type
6. If `--source`: clear only notifications from specified source
7. Report cleared count

## Validation Rules

### Prohibited Actions
- Do NOT clear notifications without reading current state first
- Do NOT clear all notifications without explicit `--all` flag

## Usage

```bash
/clear-notifications              # Show current notifications
/clear-notifications --list       # List all notifications
/clear-notifications --all        # Clear all notifications
/clear-notifications --type lesson # Clear only lesson notifications
/clear-notifications --type commit --source git_hook
```

## Automatic Clearing

- /retro clears only lesson notifications
- Hooks can clear their own type

## Implementation

```bash
python P:/__csf/scripts/clear-notifications.py "$@"
```
