"""Search modes for the unified router."""

from enum import Enum


class Mode(Enum):
    """Search mode determines which backends to use and optimization strategy.

    Attributes:
        FAST: Local backends only (<1s). Best for code search, finding patterns.
        COMPREHENSIVE: All backends with HyDE (5-10s). Best for research, learning.
        CUSTOM: User-specified backends and options.
    """

    FAST = "fast"
    COMPREHENSIVE = "comprehensive"
    CUSTOM = "custom"

    def __str__(self) -> str:
        return self.value

    @property
    def is_fast(self) -> bool:
        """Check if this is FAST mode."""
        return self == Mode.FAST

    @property
    def is_comprehensive(self) -> bool:
        """Check if this is COMPREHENSIVE mode."""
        return self == Mode.COMPREHENSIVE

    @property
    def is_custom(self) -> bool:
        """Check if this is CUSTOM mode."""
        return self == Mode.CUSTOM

    @property
    def timeout(self) -> float:
        """Get default timeout for this mode (seconds)."""
        if self.is_fast:
            return 0.5
        elif self.is_comprehensive:
            return 5.0
        else:
            return 1.0  # Default for custom

    @property
    def includes_web(self) -> bool:
        """Check if this mode includes web backends."""
        return self in (Mode.COMPREHENSIVE, Mode.CUSTOM)

    @property
    def includes_local(self) -> bool:
        """Check if this mode includes local backends."""
        return True  # All modes include local backends

    @property
    def uses_hyde(self) -> bool:
        """Check if this mode uses HyDE query enhancement."""
        return self == Mode.COMPREHENSIVE


# Convenience constants
FAST = Mode.FAST
COMPREHENSIVE = Mode.COMPREHENSIVE
CUSTOM = Mode.CUSTOM
