# Pre-Mortem Evidence Storage

This directory stores detailed findings from pre-mortem adversarial validation runs.

## Purpose

The compact snapshot output shown to users focuses on "now" - current failures and immediate actions. This `.evidence/` directory preserves the full analysis for deep-dive reference.

## Directory Structure

```
.evidence/
├── README.md                    # This file
├── premortem-<project>-<timestamp>-compliance.md    # Compliance review findings
├── premortem-<project>-<timestamp>-logic.md         # Logic review findings
├── premortem-<project>-<timestamp>-performance.md   # Performance review findings
├── premortem-<project>-<timestamp>-security.md      # Security review findings
├── premortem-<project>-<timestamp>-testing.md       # Testing review findings
├── premortem-<project>-<timestamp>-quality.md       # Quality review findings
├── premortem-<project>-<timestamp>-critic.md        # Critic meta-analysis findings
└── premortem-<project>-<timestamp>-qa.md            # QA review findings
```

## File Naming Convention

Files are named using the pattern:
```
premortem-{project}-{timestamp}-{agent}.md
```

Where:
- `project`: Sanitized project name (max 50 chars, alphanumeric + underscore + hyphen only)
- `timestamp`: ISO 8601 timestamp with colons replaced by dashes
- `agent`: One of `compliance`, `logic`, `performance`, `security`, `testing`, `quality`, `critic`, `qa`

## Evidence Retention

Evidence files are retained for 30 days by default. The skill includes automatic cleanup of old evidence files.

## Multi-Terminal Safety

Evidence file names include timestamps to prevent collisions when multiple terminals run pre-mortem analysis concurrently. Each terminal writes to its own unique files without coordination.

## Security Note

Pre-mortem prediction files stored in `memory/premortem/` use 0o600 permissions (owner read/write only) because they may contain sensitive project information. Evidence files in this directory are typically less sensitive (analysis findings rather than project details) but should still be handled with appropriate care.
