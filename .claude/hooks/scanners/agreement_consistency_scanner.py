#!/usr/bin/env python3
"""
Agreement-Action Consistency Scanner
====================================

Detects when the model agrees with a user correction but then contradicts
that agreement in its subsequent reasoning or proposed actions.

Example:
User: "that path is bad"
Model: "Agreed, that path is bad. [Later] Data at that path shows..." -> BLOCK
"""

import re

from .base_scanner import BaseScanner, ScanResult, ScanStatus


class AgreementConsistencyScanner(BaseScanner):
    """
    Scanner for detecting contradictions between stated agreement and subsequent actions.
    """

    AGREEMENT_TOKENS = [
        r"\bAgreed\b",
        r"\bI agree\b",
        r"\bYou['']re right\b",
        r"\bYou['']re correct\b",
        r"\bThat['']s correct\b",
        r"\bGood point\b",
        r"\bFair point\b",
        r"\bMy mistake\b",
        r"\bI was wrong\b",
    ]

    def scan(self, text: str, context: dict = None) -> ScanResult:
        """
        Scan response for agreement-action inconsistency.
        """
        if not self.enabled:
            return ScanResult(ScanStatus.SKIP, self.name)

        # 1. Find agreement tokens
        agreement_match = None
        for pattern in self.AGREEMENT_TOKENS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                agreement_match = match
                break

        if not agreement_match:
            return ScanResult(ScanStatus.PASS, self.name)

        # 2. Extract what was agreed to (from user message if available)
        messages = context.get("messages") or context.get("conversation", [])
        if not messages:
            return ScanResult(ScanStatus.PASS, self.name)

        user_messages = [m for m in messages if m.get("role") == "user"]
        if not user_messages:
            return ScanResult(ScanStatus.PASS, self.name)

        last_user_msg = user_messages[-1].get("content", "")
        if isinstance(last_user_msg, list):
            last_user_msg = " ".join([b.get("text", "") for b in last_user_msg if b.get("type") == "text"])

        # Extract keywords from user message
        # We focus on noun phrases or paths
        keywords = set(re.findall(r"[A-Za-z0-9_/\\:.-]{5,}", str(last_user_msg)))

        # 3. Check for contradictions in remainder of response
        # Skip the sentence containing the agreement token
        first_sentence_end = text.find(".", agreement_match.end())
        if first_sentence_end == -1:
            remainder = text[agreement_match.end():]
        else:
            remainder = text[first_sentence_end + 1:]

        # Check if model uses/references the same keywords in a positive/active context
        for kw in keywords:
            # If keyword appears again, check context
            kw_match = re.search(re.escape(kw), remainder, re.IGNORECASE)
            if kw_match:
                # Basic check: if keyword appears in a context that seems to use it
                # rather than migrate from it
                context_window = remainder[max(0, kw_match.start() - 50):kw_match.end() + 100].lower()

                # If agreement was "bad path", but later says "data at path"
                bad_indicators = ["bad", "invalid", "wrong", "broken", "incorrect", "don't use", "do not use"]
                usage_indicators = ["shows", "contains", "results", "output", "data", "check", "looking at", "read"]

                # If model agreed it's bad, but then cites data from it
                is_usage = any(re.search(rf"\b{re.escape(ind)}\b", context_window) for ind in usage_indicators)

                # Correction indicators should be whole words and NOT part of the keyword itself
                correction_indicators = ["migrate", "move", "fix", "update", "instead"]
                is_correction = any(re.search(rf"\b{re.escape(ind)}\b", context_window) for ind in correction_indicators)

                if is_usage and not is_correction:
                    return ScanResult(
                        status=ScanStatus.FAIL,
                        scanner_name=self.name,
                        matched_text=kw,
                        reason=f"Agreement-Action Inconsistency: You agreed with the user about '{kw}' but then proceeded to use it or citation its state without correction.",
                        severity="MEDIUM", # Start as warning
                        suggestion=f"If you agreed '{kw}' is invalid, do not use it. Propose a migration or alternative instead."
                    )

        return ScanResult(ScanStatus.PASS, self.name)
