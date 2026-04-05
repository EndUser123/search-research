#!/bin/bash
set -e
REPO_DIR="/c/Users/brsth/AppData/Local/Temp/gitingest_mbzuai-oryx_Video-LLaVA"  # pragma: allowlist secret
NOTEBOOKLM_DIR="$REPO_DIR/notebooklm"
mkdir -p "$NOTEBOOKLM_DIR"

# Read files into array
mapfile -d '' files < "$NOTEBOOKLM_DIR/file-list.txt"

# Generate repo-index slice
> "$NOTEBOOKLM_DIR/repo-index-part-1.md"
echo "# Video-LLaVA — Repository Index" >> "$NOTEBOOKLM_DIR/repo-index-part-1.md"
echo "" >> "$NOTEBOOKLM_DIR/repo-index-part-1.md"
echo "Video-LLaVA: An instruction-tuned audio-visual language model for video understanding, extending LLaVA to video domains." >> "$NOTEBOOKLM_DIR/repo-index-part-1.md"
echo "" >> "$NOTEBOOKLM_DIR/repo-index-part-1.md"
echo "## File Index" >> "$NOTEBOOKLM_DIR/repo-index-part-1.md"
echo "" >> "$NOTEBOOKLM_DIR/repo-index-part-1.md"

for f in "${files[@]}"; do
    ext="${f##*.}"
    fname="${f##*/}"

    # Inline full content for entry points and top-level py files
    if [[ "$fname" == "__main__.py" ]] || [[ "$fname" == "cli.py" ]] || [[ "$fname" == "app.py" ]] || [[ "$fname" == "train.py" ]] || [[ "$fname" == "eval"*".py" ]] || [[ "$fname" == "inference.py" ]] || [[ "$fname" == "chat.py" ]]; then
        echo "### $f" >> "$NOTEBOOKLM_DIR/repo-index-part-1.md"
        echo "" >> "$NOTEBOOKLM_DIR/repo-index-part-1.md"
        echo '```python' >> "$NOTEBOOKLM_DIR/repo-index-part-1.md"
        head -100 "$REPO_DIR/$f" >> "$NOTEBOOKLM_DIR/repo-index-part-1.md" 2>/dev/null || echo "# File not readable" >> "$NOTEBOOKLM_DIR/repo-index-part-1.md"
        echo '```' >> "$NOTEBOOKLM_DIR/repo-index-part-1.md"
        echo "" >> "$NOTEBOOKLM_DIR/repo-index-part-1.md"
    elif [[ "$ext" == "md" ]]; then
        echo "### $f" >> "$NOTEBOOKLM_DIR/repo-index-part-1.md"
        echo "" >> "$NOTEBOOKLM_DIR/repo-index-part-1.md"
        head -50 "$REPO_DIR/$f" >> "$NOTEBOOKLM_DIR/repo-index-part-1.md" 2>/dev/null || echo "# File not readable" >> "$NOTEBOOKLM_DIR/repo-index-part-1.md"
        echo "" >> "$NOTEBOOKLM_DIR/repo-index-part-1.md"
    else
        # Summary only for other files
        size=$(wc -c < "$REPO_DIR/$f" 2>/dev/null || echo 0)
        echo "### $f" >> "$NOTEBOOKLM_DIR/repo-index-part-1.md"
        echo "Source file ($size bytes). Part of the Video-LLaVA video-understanding model implementation." >> "$NOTEBOOKLM_DIR/repo-index-part-1.md"
        echo "" >> "$NOTEBOOKLM_DIR/repo-index-part-1.md"
    fi
done

echo "Slice lines: $(wc -l < $NOTEBOOKLM_DIR/repo-index-part-1.md)"
echo "Done: $NOTEBOOKLM_DIR/repo-index-part-1.md"
