# Universal Task Tracking Schema

## Overview
This document describes the universal schema for all project tracking files, including `tracking_dev.json` and `tracking_test.json`. It provides a consistent structure for managing development, testing, and other project-related tasks.

## Project-Level Fields
- `project`: (String) Project identifier (e.g., "YT_Sync")
- `version`: (String) Semantic version of the tracking schema
- `last_updated`: (ISO 8601 timestamp) When file was last modified
- `changelog`: (Array) History of major changes to the file
  - `timestamp`: When change occurred
  - `author`: Who made the change
  - `change_description`: What changed
- `phases`: (Array) Development phases
- `metrics`: (Object) Aggregated task metrics
  - `total_tasks`: Count of all tasks
  - `completed_tasks`: Count of done tasks
  - `in_progress_tasks`: Count of active tasks
  - `not_started_tasks`: Count of pending tasks

## Phase-Level Fields
- `name`: (String) Phase name/description
- `status`: (String) "Planned", "In Progress", or "Completed"
- `objective`: (String) High-level goal of the phase
- `phase_metrics`: (Object) Same structure as project metrics
- `tasks`: (Array) Tasks in this phase

## Task-Level Fields
- `id`: (String) Unique identifier (format: "YT-SYNC-[phase#]-[task#]")
- `description`: (String) Task summary
- `status`: (String) "Not Started", "In Progress", or "Completed"
- `priority`: (String) "Low", "Medium", "High", or "Critical"
- `effort`: (Integer 1-5) Relative complexity (1=trivial, 5=complex)
- `tags`: (Array of strings) Categories like ["bug", "ui", "backend"]
- `assignee`: (String) Person responsible (null if unassigned)
- `dependencies`: (Array of task IDs) Prerequisite tasks
- `type`: (String) Work type (e.g., "development")
- `comments`: (Array) Discussion history
  - `author`: Who wrote the comment
  - `timestamp`: When comment was added
  - `text`: Comment content
- `related_links`: (Array) External references
  - `type`: Link type (e.g., "Pull Request")
  - `url`: Resource location

## Example
```json
{
  "project": "YT_Sync",
  "version": "1.0.0",
  "phases": [
    {
      "name": "Phase 8",
      "tasks": [
        {
          "id": "YT-SYNC-8-1",
          "description": "Example task",
          "priority": "High",
          "tags": ["backend"],
          "effort": 3
        }
      ]
    }
  ]
}
