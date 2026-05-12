"""Sample module for testing."""

from typing import List, Optional


def greet(name: str, greeting: str = "Hello") -> str:
    """Greet someone."""
    return f"{greeting}, {name}!"


class Greeter:
    """Greeter class."""

    def __init__(self, default_name: str = "World"):
        self.default_name = default_name

    def greet(self) -> str:
        return greet(self.default_name)

    @property
    def name(self) -> str:
        return self.default_name
