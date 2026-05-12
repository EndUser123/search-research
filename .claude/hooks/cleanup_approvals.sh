#!/usr/bin/env bash
# cleanup_approvals.sh - Clean stale approval.json files (cron-safe)
# Usage: ./cleanup_approvals.sh [--dry-run] [--verbose]
# Cron example: 0 */6 * * * /path/to/cleanup_approvals.sh >> /var/log/approval-cleanup.log 2>&1

set -euo pipefail

DRY_RUN=false
VERBOSE=false
ARTIFACTS_DIR="${CLAUDE_ARTIFACTS_DIR:-P:/.claude/.artifacts}"
MAX_AGE_HOURS=24

usage() {
    echo "Usage: $0 [--dry-run] [--verbose] [--max-age-hours N]"
    echo "  --dry-run          Show what would be deleted without deleting"
    echo "  --verbose          Show detailed output"
    echo "  --max-age-hours N  Files older than N hours are deleted (default: 24)"
    echo "  --artifacts-dir    Override artifacts directory"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=true; shift ;;
        --verbose) VERBOSE=true; shift ;;
        --max-age-hours) MAX_AGE_HOURS="$2"; shift 2 ;;
        --artifacts-dir) ARTIFACTS_DIR="$2"; shift 2 ;;
        --help) usage; exit 0 ;;
        *) echo "Unknown option: $1"; usage; exit 1 ;;
    esac
done

if [[ ! -d "$ARTIFACTS_DIR" ]]; then
    echo "Artifacts directory not found: $ARTIFACTS_DIR"
    exit 1
fi

CURRENT_TIME=$(date +%s)
MAX_AGE_SECONDS=$((MAX_AGE_HOURS * 3600))
DELETED_COUNT=0
DELETED_SIZE=0

find "$ARTIFACTS_DIR" -name "approval.json" -type f 2>/dev/null | while read -r file; do
    FILE_MTIME=$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null)
    FILE_AGE=$((CURRENT_TIME - FILE_MTIME))

    if [[ $FILE_AGE -gt $MAX_AGE_SECONDS ]]; then
        FILE_SIZE=$(stat -c %s "$file" 2>/dev/null || stat -f %z "$file" 2>/dev/null || echo 0)
        FILE_DIR=$(dirname "$file")

        if [[ "$VERBOSE" == "true" ]]; then
            echo "Found stale approval: $file (age: $((FILE_AGE / 3600))h)"
        fi

        if [[ "$DRY_RUN" == "true" ]]; then
            echo "[DRY-RUN] Would delete: $file (age: $((FILE_AGE / 3600))h)"
        else
            rm -f "$file"
            # Also remove empty parent directories (terminal dirs)
            rmdir "$FILE_DIR" 2>/dev/null || true
            DELETED_COUNT=$((DELETED_COUNT + 1))
            DELETED_SIZE=$((DELETED_SIZE + FILE_SIZE))
            echo "Deleted: $file"
        fi
    fi
done

if [[ "$DRY_RUN" == "true" ]]; then
    echo "Dry run complete. No files were deleted."
else
    echo "Cleanup complete. Deleted $DELETED_COUNT files ($((DELETED_SIZE / 1024))KB reclaimed)"
fi