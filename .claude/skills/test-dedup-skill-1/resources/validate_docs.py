
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        return [
            {"severity": "HIGH", "type": "circular_reference", "file": "a.md", "message": "Same issue", "fix": "Fix it"}
        ]
