
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        # Always returns the same issue
        return [
            {"severity": "HIGH", "type": "circular_reference", "file": "a.md", "message": "Circular ref", "fix": "Fix it"}
        ]
