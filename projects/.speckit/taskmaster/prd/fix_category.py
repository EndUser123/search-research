#!/usr/bin/env python3
"""
Quick fix script to update the _infer_category method in parser.py
"""

parser_file = "/p/.speckit/taskmaster/prd/parser.py"

# Read the file
with open(parser_file) as f:
    content = f.read()

# Find and replace the _infer_category method
old_method_start = "    def _infer_category(self, context: str, title: str) -> Optional[str]:"
old_method_end = "        return None"

old_method = """    def _infer_category(self, context: str, title: str) -> Optional[str]:
        \"\"\"Infer requirement category from context and title.

        Args:
            context: Surrounding text context
            title: Requirement title

        Returns:
            Inferred category or None
        \"\"\"
        context_lower = context.lower()
        title_lower = title.lower()

        # Category keywords
        category_keywords = {
            "User Interface": ["ui", "interface", "display", "screen", "view", "cli"],
            "Data": ["data", "database", "storage", "persistence", "file", "cache"],
            "API": ["api", "endpoint", "rest", "graphql", "http"],
            "Authentication": ["auth", "login", "security", "permission"],
            "Performance": ["performance", "speed", "latency", "throughput"],
            "Testing": ["test", "coverage", "unit test"],
            "Configuration": ["config", "setting", "option"],
        }

        for category, keywords in category_keywords.items():
            if any(keyword in title_lower or keyword in context_lower for keyword in keywords):
                return category

        return None"""

new_method = """    def _infer_category(self, context: str, title: str) -> Optional[str]:
        \"\"\"Infer requirement category from context and title.

        Args:
            context: Surrounding text context
            title: Requirement title

        Returns:
            Inferred category or None
        \"\"\"
        context_lower = context.lower()
        title_lower = title.lower()

        # Category keywords - ordered by priority (more specific first)
        # Must check "api" before "interface" to avoid mis-categorization
        category_keywords = [
            ("API", ["api", "endpoint", "rest", "graphql", "http"]),
            ("Authentication", ["authentication", "login", "auth", "security", "permission"]),
            ("Data", ["database", "storage", "persistence", "data", "cache"]),
            ("User Interface", ["ui", "user interface", "display", "screen", "view", "cli"]),
            ("Performance", ["performance", "speed", "latency", "throughput"]),
            ("Testing", ["test", "coverage", "unit test"]),
            ("Configuration", ["config", "setting", "option"]),
        ]

        # Check title first (higher priority), then context
        # Use word boundary matching to avoid partial matches
        for category, keywords in category_keywords:
            # Check title first
            for keyword in keywords:
                # Check for word boundaries or exact match
                pattern = r'\\b' + re.escape(keyword) + r'\\b'
                if re.search(pattern, title_lower, re.IGNORECASE):
                    return category

            # Then check context
            for keyword in keywords:
                pattern = r'\\b' + re.escape(keyword) + r'\\b'
                if re.search(pattern, context_lower, re.IGNORECASE):
                    return category

        return None"""

# Check if old method exists
if old_method in content:
    content = content.replace(old_method, new_method)
    print("Successfully replaced _infer_category method")
else:
    print("Could not find old method exactly. Trying alternative approach...")
    # Find the method and replace line by line
    lines = content.split('\n')
    new_lines = []
    in_method = False
    indent_level = 0
    method_lines = []

    for i, line in enumerate(lines):
        if old_method_start in line:
            in_method = True
            indent_level = len(line) - len(line.lstrip())
            method_lines = [line]
            continue

        if in_method:
            method_lines.append(line)
            # Check if we've reached the end of the method
            if old_method_end in line and line.strip().startswith(old_method_end):
                in_method = False
                # Add the new method instead
                new_method_lines = new_method.split('\n')
                new_lines.extend(new_method_lines)
                continue
        else:
            new_lines.append(line)

    content = '\n'.join(new_lines)

# Write back
with open(parser_file, 'w') as f:
    f.write(content)

print(f"Updated {parser_file}")
