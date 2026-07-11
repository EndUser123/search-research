from pydantic import BaseModel, Field

# Confidence ceiling for fully-known classifications (bypass/clear/prohibited/confirm).
# Resolved ambiguous prompts get a lower value computed at runtime in enhance().
_FULL_CONFIDENCE: float = float(1)


class EnhancementResult(BaseModel):
    clarified_intent: str = Field(description="Describes what the user is trying to accomplish")
    missing_details: list[str] = Field(description="Items that need user confirmation before execution")
    analysis: str | None = Field(default=None, description="Brief reasoning for triage decision")
    safety_flags: list[str] = Field(
        default_factory=list,
        description="High-impact flags, e.g. 'high-impact verb: delete database'"
    )
    confidence: float = Field(
        default=_FULL_CONFIDENCE,
        ge=float(0),
        le=float(1),
        description="Confidence in the enhancement (0..1). Hook may gate injection on this.",
    )
