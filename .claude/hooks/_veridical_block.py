# ---------------------------------------------------------------------------
# Veridical integrity: scope gate, message builder, prompt
# ---------------------------------------------------------------------------

_VERIDICAL_AGREEMENT_PATTERNS = [
    re.compile(r"you're\s+right", re.IGNORECASE),
    re.compile(r"you\s+are\s+right", re.IGNORECASE),
    re.compile(r"that's\s+correct", re.IGNORECASE),
    re.compile(r"i\s+(?:see|understand)\s+now", re.IGNORECASE),
    re.compile(r"i\s+agree", re.IGNORECASE),
    re.compile(r"exactly[!.,]", re.IGNORECASE),
    re.compile(r"absolutely[!.,]", re.IGNORECASE),
    re.compile(r"good\s+(?:point|catch|question|observation)", re.IGNORECASE),
    re.compile(r"great\s+(?:point|catch|question|observation)", re.IGNORECASE),
    re.compile(r"I\s+(?:was\s+)?wrong", re.IGNORECASE),
    re.compile(r"I\s+misunderstood", re.IGNORECASE),
    re.compile(r"now\s+I\s+(?:see|understand)", re.IGNORECASE),
]
