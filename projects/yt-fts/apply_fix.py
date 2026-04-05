import re

file_path = "src/yt_fts/download/batch_downloader.py"

with open(file_path, 'r') as f:
    content = f.read()

# Find all YouTubeAPIBackfill instantiations with show_progress parameter
# and replace them to respect suppress_quota_print

# Pattern 1: Rich progress blocks (show_progress=progress)
# Should be: show_progress=progress if not suppress_quota_print else False
pattern1 = r'(\s+)backfill = YouTubeAPIBackfill\(\s*console=self\.console,\s*show_progress=progress,?\s*\)'

def replace_rich_progress(match):
    indent = match.group(1)
    return f'''{indent}# Conditionally pass progress object based on suppress_quota_print
{indent}backfill = YouTubeAPIBackfill(
{indent}    console=self.console,
{indent}    show_progress=progress if not self.suppress_quota_print else False,
{indent})'''

content = re.sub(pattern1, replace_rich_progress, content)

# Pattern 2: Suppress progress blocks (show_progress=False)
# Should remain: show_progress=False (already suppresses progress)
# No change needed

# Pattern 3: Comments about progress
# Update the comment in simple mode else block
content = re.sub(
    r'(# Suppress progress mode)',
    r'# Suppress progress mode (simple mode)\n                # Note: suppress_quota_print flag is for Rich Layout mode only',
    content
)

with open(file_path, 'w') as f:
    f.write(content)

print("Applied suppress_quota_print fix while preserving parent-owned progress pattern")
