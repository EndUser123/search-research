import ast, re
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class SelfHealingTestFramework:
    def __init__(self):
        self.element_patterns = self._load_element_patterns()
        self.failure_history = self._load_failure_history()

    def detect_ui_changes(self, test_failure_log: str) -> dict:
        """Analyze test failures to detect UI changes."""
        patterns = {
            "element_not_found": r"ElementNotFound.*?(id|class|xpath)['"](.*?)['"]",
            "timeout": r"TimeoutException.*?waiting for (.*)",
            "stale_element": r"StaleElementReferenceException"
        }

        detected_changes = {}
        for change_type, pattern in patterns.items():
            matches = re.findall(pattern, test_failure_log, re.IGNORECASE)
            if matches:
                detected_changes[change_type] = matches

        return detected_changes

    def suggest_element_alternatives(self, failed_locator: str) -> list[str]:
        """Suggest alternative element locators using similarity analysis."""
        # Load current page elements (would integrate with actual browser inspection)
        current_elements = self._get_current_page_elements()

        # Use TF-IDF to find similar elements
        all_locators = [failed_locator] + list(current_elements.keys())
        vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(1, 3))
        tfidf_matrix = vectorizer.fit_transform(all_locators)

        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

        # Return top 3 most similar alternatives
        similar_indices = similarities.argsort()[-3:][::-1]
        alternatives = [list(current_elements.keys())[i] for i in similar_indices
                       if similarities[i] > 0.3]

        return alternatives

    def auto_update_test_script(self, test_file: Path, failed_locator: str,
                               new_locator: str) -> bool:
        """Automatically update test script with new locator."""
        try:
            with test_file.open("r") as f:
                content = f.read()

            # Replace failed locator with new one
            updated_content = content.replace(failed_locator, new_locator)

            # Validate syntax before saving
            try:
                ast.parse(updated_content)
            except SyntaxError:
                return False

            with test_file.open("w") as f:
                f.write(updated_content)

            print(f"🔧 Auto-healed test: {test_file}")
            print(f"   Replaced: {failed_locator}")
            print(f"   With: {new_locator}")

            return True
        except Exception as e:
            print(f"❌ Auto-healing failed: {e}")
            return False

    def _load_element_patterns(self) -> dict:
        """Load historical element patterns for prediction."""
        # In practice, this would load from ML model or pattern database
        return {
            "login_button": ["#login", ".login-btn", "[data-test='login']"],
            "username_field": ["#username", "[name='username']", ".username-input"],
            "submit_form": ["[type='submit']", ".submit-btn", "#submit"]
        }

    def _load_failure_history(self) -> dict:
        """Load test failure history for pattern learning."""
        # Would integrate with test result database
        return {}

    def _get_current_page_elements(self) -> dict:
        """Get current page elements (mock - would use actual browser)."""
        return {
            "#new-login-btn": "Login Button",
            ".user-input": "Username Field",
            "[data-cy='submit']": "Submit Button"
        }

# Pytest integration for self-healing
# This part would typically be in conftest.py, but for demonstration
# purposes as a standalone script, it's included here.
# @pytest.fixture(autouse=True)
# def self_healing_on_failure(request):
#     """Automatically attempt to heal failing tests."""
#     healing_framework = SelfHealingTestFramework()
#
#     yield
#
#     # Check if test failed
#     if hasattr(request.node, 'rep_call') and request.node.rep_call.failed:
#         failure_log = request.node.rep_call.longrepr
#
#         # Detect UI changes
#         changes = healing_framework.detect_ui_changes(str(failure_log))
#
#         if changes.get("element_not_found"):
#             failed_locator = changes["element_not_found"][0][1]
#             alternatives = healing_framework.suggest_element_alternatives(failed_locator)
#
#             if alternatives:
#                 test_file = Path(request.node.fspath)
#                 # Try first alternative
#                 success = healing_framework.auto_update_test_script(
#                     test_file, failed_locator, alternatives[0]
#                 )
#
#                 if success:
#                     # Rerun test to verify fix
#                     print(f"🔄 Retrying healed test: {request.node.name}")
