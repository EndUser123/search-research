
_call_count = 0

class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        global _call_count
        _call_count += 1
        # Return different issue each time
        if _call_count == 1:
            return [
                {"severity": "HIGH", "type": "circular_reference", "file": "a.md", "message": "First issue", "fix": "Fix 1"}
            ]
        else:
            return [
                {"severity": "MEDIUM", "type": "version_conflict", "file": "b.md", "message": "Second issue", "fix": "Fix 2"}
            ]
