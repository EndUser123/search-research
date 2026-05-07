import os
import re

def fix_invalid_escapes(content):
    # Pattern to match string literals with optional f prefix, and quotes (single, double, triple)
    # Group 1: optional f/F prefix
    # Group 2: quotes (''' or """ or ' or ")
    # Group 3: string body
    # Group 4: same quotes as Group 2
    string_pattern = re.compile(r'(?i)([f]?)(\'\'\'|\"\"\"|\'|\")(.*?)\2', re.DOTALL)

    def replacer(match):
        prefix = match.group(1) # f or empty
        quotes = match.group(2)
        body = match.group(3)
        
        # If it's already a raw string, we don't know (regex doesn't catch r prefix because of (?<!r))
        # Wait, the regex above doesn't even look for r prefix.
        
        # Check if it has invalid escapes
        if re.search(r'\\[^\\\'"abfnrtuvx0-7uUN]', body):
            # It needs to be raw.
            # If it has f prefix, it becomes fr. If not, it becomes r.
            new_prefix = prefix.lower() + 'r'
            return f"{new_prefix}{quotes}{body}{quotes}"
        
        return match.group(0)

    # We need to find all strings but exclude those that ALREADY have 'r' in prefix.
    # So we use a negative lookbehind for r/R.
    
    final_pattern = re.compile(r'(?i)(?<![rR])([f]?)(\'\'\'|\"\"\"|\'|\")(.*?)\2', re.DOTALL)
    
    # Actually, triple quotes might be tricky with non-greedy (.*?).
    # Let's do it more carefully.
    
    def process_match(m):
        full = m.group(0)
        prefix = m.group(1) # f or empty
        quotes = m.group(2)
        body = m.group(3)
        
        # Check for invalid escapes: \ followed by something not in the allowed set
        # and not followed by another \
        if re.search(r'\\[^\\\'"abfnrtuvx0-7uUN]', body):
            return f"{prefix}r{quotes}{body}{quotes}"
        return full

    return final_pattern.sub(process_match, content)

def process_dir(root_dir):
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    new_content = fix_invalid_escapes(content)
                    
                    if new_content != content:
                        with open(path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"Fixed: {path}")
                except Exception as e:
                    print(f"Error processing {path}: {e}")

if __name__ == "__main__":
    process_dir(r"P:\packages\skill-guard")
