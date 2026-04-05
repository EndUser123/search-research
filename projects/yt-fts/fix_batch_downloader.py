import re

file_path = "src/yt_fts/download/batch_downloader.py"

with open(file_path, 'r') as f:
    content = f.read()

# The file has a corrupted structure. Let me fix it by:
# 1. Completing the incomplete function call
# 2. Removing orphaned fragments
# 3. Removing duplicate quota display
# 4. Fixing the else block structure

# Fix the incomplete call
content = re.sub(
    r'(\s+)videos_data = backfill\.fetch_all_videos_from_channel\(\s*\n\s*\n(\s+)# Display per-key',
    r'\1videos_data = backfill.fetch_all_videos_from_channel(\1\1channel_id,\n\1\1progress_task=task\n\1)\n\n\2# Display per-key',
    content,
    count=1
)

# Remove orphaned fragments (the ones that got separated)
lines = content.split('\n')
new_lines = []
skip_next = 0

for i, line in enumerate(lines):
    if skip_next > 0:
        skip_next -= 1
        continue
    
    # Check if this is an orphaned fragment pattern
    if (i + 2 < len(lines) and
        'channel_id,' in line and
        i + 1 < len(lines) and 'progress_task=task' in lines[i + 1] and
        i + 2 < len(lines) and '                    )' in lines[i + 2]):
        # Check if this is NOT part of a valid call
        is_valid = False
        if i > 0:
            context = ''.join(lines[max(0, i-3):i])
            if 'fetch_all_videos_from_channel(' in context:
                is_valid = True
        
        if not is_valid:
            # Skip these orphaned lines
            continue
    
    new_lines.append(line)

content = '\n'.join(new_lines)

# Fix the else block - remove duplicate quota display
# Find "else:" followed by "# Display per-key quota status table"
# and replace with proper else block content
else_pattern = r'(\s+)else:\s*\n(\s+)# Display per-key quota status table.*?(?=\n\s+if videos_data:|\n\s+set_channel_api_total|\Z)'

# The else block should contain the suppress-progress-mode code, not duplicate quota display
replacement = r'''\1else:
\1    # Suppress progress mode
\1    backfill = YouTubeAPIBackfill(
\1        console=self.console,
\1        show_progress=False,
\1    )
\1    videos_data = backfill.fetch_all_videos_from_channel(channel_id)
\1    
\1    if not self.suppress_quota_print:
\1        from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill
\1        per_key_info = YouTubeAPIBackfill.get_per_key_quota_info()
\1        
\1        # Build table rows
\1        table_lines = []
\1        table_lines.append("   ⎿ API Key Quota Status:")
\1        table_lines.append("   ┌" + "─" * 75 + "┐")
\1        
\1        for key_info in per_key_info:
\1            key_idx = key_info["key_index"]
\1            key_name = key_info["key_name"]
\1            used = key_info["used"]
\1            remaining = key_info["remaining"]
\1            limit = key_info["limit"]
\1            pct = key_info["percentage"]
\1            
\1            # Color based on remaining quota
\1            if remaining == 0:
\1                status_color = "[red]"
\1            elif remaining < limit * 0.2:
\1                status_color = "[yellow]"
\1            else:
\1                status_color = "[green]"
\1            
\1            key_short = key_name.replace("YOUTUBE_API_KEY", "Key").replace("_", "")
\1            table_lines.append(
\1                f"   │ {status_color}{key_short}[/]: {used:5,}/{limit:<5,} "
\1                f"({pct:5.1f}%)  remaining: {status_color}{remaining:5,}[/] │"
\1            )
\1        
\1        table_lines.append("   └" + "─" * 75 + "┘")
\1        
\1        for table_line in table_lines:
\1            self.console.print(table_line)

'''

content = re.sub(else_pattern, replacement, content, flags=re.DOTALL)

with open(file_path, 'w') as f:
    f.write(content)

print("Fixed file structure")
