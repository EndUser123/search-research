
import os
import re

def fix_content(content):
    # Fix the most common broken patterns
    # Handles "P:\" or 'P:\' or r"P:\" or r'P:\'
    # We want to replace these with safe forward-slash versions
    
    # 1. Double/triple backslash mess
    new_content = content
    new_content = new_content.replace('r"P:\\\\\\"', '"P:/"')
    new_content = new_content.replace('r"P:\\\\"', '"P:/"')
    new_content = new_content.replace('r"P:\\"', '"P:/"')
    new_content = new_content.replace('"P:\\\\\\\\"', '"P:/"')
    new_content = new_content.replace('"P:\\\\"', '"P:/"')
    new_content = new_content.replace('"P:\\"', '"P:/"')
    
    # 2. General regex for P followed by backslashes at end of string
    # This specifically looks for the pattern where the backslash is escaping the quote
    # e.g. "P:\" or r"P:\"
    new_content = re.sub(r'([rf]?["\'])P:\\+(["\'])', r'\1P:/\2', new_content)
    
    # 3. Path literals like Path("P:\.claude") -> Path("P:/.claude")
    new_content = re.sub(r'Path\(["\']P:\\([^\'"]+)["\']\)', r'Path("P:/\1")', new_content)
    
    return new_content

def main():
    root = r'P:\packages\skill-guard'
    for r, d, f in os.walk(root):
        for file in f:
            if file.endswith('.py'):
                path = os.path.join(r, file)
                try:
                    with open(path, 'r', encoding='utf-8') as fh:
                        content = fh.read()
                    
                    new_content = fix_content(content)
                    
                    if new_content != content:
                        with open(path, 'w', encoding='utf-8') as fh:
                            fh.write(new_content)
                        print(f"FIXED: {path}")
                except Exception as e:
                    print(f"ERROR processing {path}: {e}")

if __name__ == "__main__":
    main()
