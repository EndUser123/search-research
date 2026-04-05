#!/bin/bash
set -e
NOTEBOOK_ID="bdfca419-7312-4e21-bc2d-32aab929557f"

REPOS=(
    "byjlw:video-analyzer:https://github.com/byjlw/video-analyzer"
    "saebyn:glowing-telegram:https://github.com/saebyn/glowing-telegram"
    "Swish78:VidInsights.ai:https://github.com/Swish78/VidInsights.ai"
    "taco-group:Video-Quality-Assessment-A-Comprehensive-Survey:https://github.com/taco-group/Video-Quality-Assessment-A-Comprehensive-Survey"
)

for entry in "${REPOS[@]}"; do
    IFS=':' read -r OWNER REPO URL <<< "$entry"
    SANITIZED="${OWNER}_${REPO}"
    TEMP_DIR="/c/Users/brsth/AppData/Local/Temp/gitingest_${SANITIZED}"
    NOTEBOOKLM_DIR="$TEMP_DIR/notebooklm"

    echo "=== Processing $OWNER/$REPO ==="

    # Clone
    if [ -d "$TEMP_DIR" ]; then
        echo "Already cloned, skipping"
    else
        git clone --depth=1 --filter=blob:none "$URL" "$TEMP_DIR" 2>&1
    fi

    # Build file list
    mkdir -p "$NOTEBOOKLM_DIR"
    git -C "$TEMP_DIR" ls-files -z | grep -zEv '(\.png$|\.jpg$|\.lock$|\.bin$|\.pyc$|__pycache__|\.pytest_cache|node_modules|\.git)' | grep -zv '/\.' | sort > "$NOTEBOOKLM_DIR/file-list.txt"
    FILE_COUNT=$(git -C "$TEMP_DIR" ls-files | grep -vE '(\.png$|\.jpg$|\.lock$|\.bin$|\.pyc$|__pycache__|\.pytest_cache|node_modules)' | wc -l)
    echo "Files: $FILE_COUNT"

    # Collect description from README (use absolute path to avoid cd issues)
    README_CONTENT=""
    README_FILE=""
    for rf in README.md readme.md README README; do
        if [ -f "$TEMP_DIR/$rf" ]; then
            README_FILE="$TEMP_DIR/$rf"
            break
        fi
    done
    if [ -n "$README_FILE" ]; then
        README_CONTENT=$(head -20 "$README_FILE" 2>/dev/null | tr '\n' ' ' | sed 's/^[[:space:]]*//' | cut -c1-500)
    fi

    # Generate slice (summary-only to stay under 150 lines)
    SLICE="$NOTEBOOKLM_DIR/repo-index-part-1.md"

    # Write slice using printf to avoid heredoc variable expansion issues
    {
        printf '# %s — Repository Index (%s/%s)\n\n' "$REPO" "$OWNER" "$REPO"
        printf '## Overview\n%s\n\n' "$README_CONTENT"
        printf '## Full File Inventory (%d files)\n' "$FILE_COUNT"
        git -C "$TEMP_DIR" ls-files | grep -vE '(\.png$|\.jpg$|\.lock$|\.bin$|\.pyc$|__pycache__|\.pytest_cache|node_modules)' | sort
        printf '\n---\n'
        printf 'Slice generated from %s/%s | %d files\n' "$OWNER" "$REPO" "$FILE_COUNT"
    } > "$SLICE"

    LINES=$(wc -l < "$SLICE")
    echo "Slice: $LINES lines"

    # Upload
    nlm source add "$NOTEBOOK_ID" --file "$SLICE" --wait 2>&1
    echo ""

    # Cleanup
    rm -rf "$TEMP_DIR"
    echo "Cleaned up $TEMP_DIR"
done

echo "=== ALL DONE ==="
