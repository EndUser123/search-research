
class DocumentationValidator:
    def __init__(self, docs_dir):
        self.docs_dir = docs_dir

    def validate(self):
        return [
            {
                "severity": "HIGH",
                "type": "test_issue",
                "file": "test.md",
                "message": "Test issue for integration",
                "fix": "Fix the test issue"
            }
        ]
