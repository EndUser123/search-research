import re
from re import Pattern

from pydantic import BaseModel, Field, validator


class BoundaryConfig(BaseModel):
    """Configuration model for boundary detection plugin"""

    tag_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "error": 5.0,
            "warning": 3.0,
            "critical": 7.0,
            "exception": 6.0,
        },
        description="Weights for different log entry tags",
    )

    threshold: float = Field(
        default=8.0, description="Minimum score required to trigger a boundary", gt=0.0
    )

    min_chunk_size: int = Field(
        default=5, description="Minimum number of lines in a chunk", gt=0
    )

    max_chunk_size: int = Field(
        default=50,
        description="Maximum number of lines in a chunk before forcing a boundary",
        gt=0,
    )

    boundary_patterns: list[str] = Field(
        default_factory=lambda: [r"^---.*---$", r"^====.*====$", r"^\*\*\*.*\*\*\*$"],
        description="List of regex patterns that indicate explicit boundaries",
    )

    @validator("boundary_patterns", each_item=True)
    def validate_regex(cls, v):
        """Validate that each pattern is a valid regex"""
        try:
            re.compile(v)
            return v
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {v} - {str(e)}")

    @property
    def compiled_patterns(self) -> list[Pattern]:
        """Return compiled regex patterns"""
        return [re.compile(p) for p in self.boundary_patterns]

    class Config:
        schema_extra = {
            "example": {
                "tag_weights": {"error": 5.0, "warning": 3.0, "critical": 8.0},
                "threshold": 10.0,
                "min_chunk_size": 10,
                "max_chunk_size": 100,
                "boundary_patterns": [
                    r"^--- START OF CHUNK ---$",
                    r"^=== SYSTEM RESTART ===$",
                ],
            }
        }
