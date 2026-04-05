with open("src/download/download.py") as f:
    lines = f.readlines()

# Fix the indentation issue
lines[
    1275
] = '    _log_with_progress("  ✨ Incremental Telegram sync completed", progress)\n'

with open("src/download/download.py", "w") as f:
    f.writelines(lines)

print("Fixed indentation issue")
