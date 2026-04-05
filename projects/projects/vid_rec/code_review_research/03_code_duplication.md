# AI Coder's Guide to Eliminating Code Duplication

This guide provides best practices for avoiding code duplication in Python, specifically tailored for an AI coder. By following these guidelines, you can write more maintainable, reusable, and bug-free code.

## 1. Refactoring Techniques

**The Problem:** Duplicated code makes your codebase harder to maintain. If you need to change the logic, you have to remember to change it in all the places where it is duplicated.

**The Solution:** Use these refactoring techniques to eliminate code duplication.

*   **Extract Functions/Methods:** If you find the same or very similar code in multiple places, extract it into its own function or method. This is one of the most common and straightforward ways to reduce duplication.

    **Example: Extracting a Function**

    **Before:**
    ```python
    def process_user_data(user):
        # ... some common setup ...
        if user.is_active:
            print(f"Processing active user: {user.name}")
            # Complex logic block A
            result_a = user.data * 2
            print(f"Result A: {result_a}")
        # ... some other logic ...

    def process_admin_data(admin):
        # ... some common setup ...
        if admin.has_permissions:
            print(f"Processing admin: {admin.name}")
            # Complex logic block A (duplicated)
            result_a = admin.data * 2
            print(f"Result A: {result_a}")
        # ... some other logic ...
    ```

    **After:**
    ```python
    def _process_common_logic_block_a(entity):
        """Handles common processing logic for an entity."""
        result_a = entity.data * 2
        print(f"Result A: {result_a}")
        return result_a

    def process_user_data(user):
        # ... some common setup ...
        if user.is_active:
            print(f"Processing active user: {user.name}")
            _process_common_logic_block_a(user)
        # ... some other logic ...

    def process_admin_data(admin):
        # ... some common setup ...
        if admin.has_permissions:
            print(f"Processing admin: {admin.name}")
            _process_common_logic_block_a(admin)
        # ... some other logic ...
    ```

*   **Use Inheritance:** If duplicate code exists in two or more subclasses, consider moving that code to a common superclass.
*   **Create Utility Modules:** For helper functions or utility code that is used across different parts of your application, create a separate module to house them. This promotes reusability.
*   **Use Decorators:** Decorators are a powerful Python feature that can help you add functionality to multiple functions without duplicating code. For example, you can use a decorator to add logging or timing to several functions.
*   **Closures:** A closure can be used to avoid repeating code in a simple way, especially when you need to create a function that is similar to another but with some parameters already filled in.

## 2. When to Allow Duplication

**The Problem:** Sometimes, removing duplication can make the code harder to understand and use.

**The Solution:** The "Don't Repeat Yourself" (DRY) principle is a good guideline, but there are situations where a little duplication is acceptable, and even preferable. The "Keep It Simple, Stupid" (KISS) principle should also be considered. If refactoring to remove duplication makes the code more complex, it might be better to leave it as is.

## 3. Tools for Detecting Duplicate Code

**The Problem:** It can be difficult to find all the duplicate code in a large codebase.

**The Solution:** Use these tools to find duplicate code in your Python projects.

*   **Pylint:** This is a popular Python linter that has a "similarities" checker to find duplicate code.
*   **PMD's CPD (Copy/Paste Detector):** This tool can be used to find duplicated code in various languages, including Python.
*   **cd4py:** A command-line tool specifically for detecting near and exact duplicate Python source code files.
*   **duplicate-code-detection-tool:** A Python tool and GitHub Action that uses `gensim` to find similarities between files.
*   **PyCharm Professional:** The professional version of the PyCharm IDE has a built-in tool for finding duplicate code.
