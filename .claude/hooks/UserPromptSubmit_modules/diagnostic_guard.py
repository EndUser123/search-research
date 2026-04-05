"""Diagnostic Guard Module.

Extracted from UserPromptSubmit_router.py.
Provides speculative claims detection and enforcement.
"""

from __future__ import annotations

import re

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# Constants
SPECULATIVE_CLAIM_PATTERNS = [
    r'\bit seems that\b',
    r'\bit appears\b',
    r'\bit looks like\b',
    r'\bit probably\b',
    r'\bit likely\b',
    r'\bmay be\b',
    r'\bmight be\b',
    r'\bcould be\b',
    r'\bshould be\b',
]

DEFINITIVE_CLAIM_PATTERNS = [
    r'\bis\b',
    r'\bare\b',
    r'\bwas\b',
    r'\bhas been\b',
    r'\bwill be\b',
]

CONFIDENCE_WORDS = [
    'certainly', 'definitely', 'undoubtedly', 'clearly',
    'obviously', 'surely', 'absolutely',
]


def detect_speculative_claim(text: str) -> bool:
    """Detect if text contains speculative claims.

    Args:
        text: Text to analyze

    Returns:
        True if speculative language detected
    """
    text_lower = text.lower()
    for pattern in SPECULATIVE_CLAIM_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def count_confidence_words(text: str) -> int:
    """Count confidence-indicating words in text.

    Args:
        text: Text to analyze

    Returns:
        Count of confidence words
    """
    text_lower = text.lower()
    return sum(1 for word in CONFIDENCE_WORDS if word in text_lower)


def check_high_confidence_without_evidence(prompt: str, response_text: str) -> bool:
    """Check for high-confidence claims without supporting evidence.

    Args:
        prompt: Original user prompt
        response_text: Response text to check

    Returns:
        True if high confidence without evidence detected
    """
    # Count confidence words
    confidence_count = count_confidence_words(response_text)

    # Check for evidence indicators
    evidence_indicators = [
        'according to', 'based on', 'from the', 'in the file',
        'the code shows', 'as shown in', 'the test results',
        'documentation says', 'per the docs',
    ]
    has_evidence = any(ind in response_text.lower() for ind in evidence_indicators)

    # High confidence (2+ words) without evidence
    return confidence_count >= 2 and not has_evidence


def build_speculative_claim_warning() -> str:
    """Build warning message for speculative claims.

    Returns:
        Warning text
    """
    return """**Speculative Claim Detected**

Your response contains speculative language. Consider:
- Verifying the claim before stating it
- Using tentative language ("might be", "seems like")
- Citing evidence from code or documentation
- Running tests or investigation before asserting"""


@register_hook('diagnostic_guard', priority=10.2)
def run_diagnostic_guard(context: HookContext) -> HookResult | None:
    """Main entry point for diagnostic guard.

    Args:
        context: HookContext with prompt, data, session_id, terminal_id

    Returns:
        HookResult with warning, or None if no issues detected
    """
    issues = []

    # Check for speculative claims in user prompt (would need verification in response)
    if detect_speculative_claim(context.prompt):
        issues.append('speculative_claim')

    # Could add more checks here for response analysis
    # But since this runs pre-response, focus on prompt patterns

    if not issues:
        return None

    # Build warning context
    warnings = []
    if 'speculative_claim' in issues:
        warnings.append(build_speculative_claim_warning())

    context_text = '\n\n'.join(warnings)
    return HookResult(context=context_text, tokens=estimate_tokens(context_text))


def estimate_tokens(text: str) -> int:
    """Estimate token count for text.

    Rough estimate: ~4 characters per token.
    """
    return len(text) // 4
