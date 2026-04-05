from __future__ import annotations

import logging
import re
import sys
from pathlib import Path
from typing import Any

#!/usr/bin/env python3
"""Pattern Recognition Framework for Enhanced CHS.

Intelligent pattern recognition for identifying high-value conversation segments
including code blocks, technical solutions, decision points, and error analysis.

CSF NIP Constitution §3.6: Evidence-based development with real conversation data
CSF NIP Constitution §3.8: Modular design with clear interfaces
CSF NIP Constitution §3.9: Architectural thinking with performance considerations
"""



# Add CSF NIP paths
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent / "src" / "lib"))


class PatternRecognizer:
    """Advanced pattern recognition for chat conversation analysis.

    Identifies and extracts high-value patterns from conversations including:
    - Code blocks and technical solutions
    - Question-answer pairs
    - Error analysis and debugging discussions
    - Decision points and architectural choices
    - Technical keywords and concepts
    """

    def __init__(self, logger: logging.Logger | None = None) -> None:
        """Initialize pattern recognizer.

        Args:
        ----
            logger: Optional logger instance

        """
        self.logger = logger or logging.getLogger(__name__)

        # Compile regex patterns for efficiency
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for optimal performance."""
        # Code block patterns
        self.code_block_pattern = re.compile(
            r"```(\w+)?\n([\s\S]*?)```",
            re.MULTILINE,
        )
        self.inline_code_pattern = re.compile(r"`([^`]+)`")

        # Question patterns
        self.question_patterns = [
            re.compile(
                r"\b(how|what|why|when|where|which|who|can|could|would|should|is|are|do|does|did)\b.*\?",
                re.IGNORECASE,
            ),
            re.compile(r".*\?", re.MULTILINE),
        ]

        # Error patterns
        self.error_patterns = [
            re.compile(r"\b([A-Z][a-z]*(Error|Exception|Warning))\b"),
            re.compile(
                r"\b(traceback|stack trace|error occurred|failed to)\b", re.IGNORECASE
            ),
            re.compile(r'\b(file "[^"]+", line \d+)\b'),
        ]

        # Technical keywords
        self.technical_keywords = {
            "programming": [
                "python",
                "javascript",
                "java",
                "typescript",
                "go",
                "rust",
                "c++",
            ],
            "frameworks": [
                "fastapi",
                "django",
                "flask",
                "react",
                "vue",
                "angular",
                "spring",
            ],
            "concepts": [
                "async",
                "await",
                "api",
                "rest",
                "graphql",
                "database",
                "sql",
                "nosql",
            ],
            "practices": [
                "testing",
                "debugging",
                "refactoring",
                "optimization",
                "security",
            ],
            "tools": ["docker", "kubernetes", "git", "ci/cd", "jenkins", "github"],
        }

        # Decision indicators
        self.decision_patterns = [
            re.compile(
                r"\b(i think|i believe|i\'ll go with|let\'s use|we should|best approach)\b",
                re.IGNORECASE,
            ),
            re.compile(r"\b(decided|chose|selected|implemented|used)\b", re.IGNORECASE),
            re.compile(r"\b(because|since|due to|reason is)\b", re.IGNORECASE),
        ]

    def identify_patterns(self, text: str) -> dict[str, Any]:
        """Identify all patterns in the given text.

        Algorithm Approach: Multi-pattern recognition using optimized regex scanning
        with confidence scoring based on pattern strength and context.

        Time Complexity: O(n) where n is the text length (single pass through text)
        Space Complexity: O(m) where m is the number of patterns found

        Args:
        ----
            text: Text to analyze for patterns

        Returns:
        -------
            Dictionary containing all identified patterns with metadata

        Example:
        -------
        >>> recognizer = PatternRecognizer()
        >>> text = "How to implement async? ```python async def test(): pass```"
        >>> patterns = recognizer.identify_patterns(text)
        >>> patterns["questions"][0]["text"]
        'How to implement async?'
        >>> patterns["code_blocks"][0]["language"]
        'python'

        """
        patterns = {
            "code_blocks": self._identify_code_blocks(text),
            "questions": self._identify_questions(text),
            "error_patterns": self._identify_error_patterns(text),
            "technical_keywords": self._identify_technical_keywords(text),
            "decisions": self._identify_decisions(text),
            "solutions": self._identify_solutions(text),
            "debugging_steps": self._identify_debugging_steps(text),
        }

        # Calculate overall confidence scores
        patterns["confidence_scores"] = self._calculate_pattern_confidence(patterns)

        return patterns

    def _identify_code_blocks(self, text: str) -> list[dict[str, Any]]:
        """Identify code blocks with language detection and confidence scoring.

        Args:
        ----
            text: Text containing potential code blocks

        Returns:
        -------
            List of code block patterns with metadata

        """
        code_blocks = []

        for match in self.code_block_pattern.finditer(text):
            language = match.group(1) or "unknown"
            code = match.group(2).strip()

            # Calculate confidence based on code characteristics
            confidence = self._calculate_code_confidence(code, language)

            code_block = {
                "text": code,
                "language": language.lower(),
                "start_pos": match.start(),
                "end_pos": match.end(),
                "confidence": confidence,
                "line_count": len(code.split("\n")),
                "character_count": len(code),
                "functions_identified": self._identify_functions(code),
            }
            code_blocks.append(code_block)

        return code_blocks

    def _calculate_code_confidence(self, code: str, language: str) -> float:
        """Calculate confidence score for code block identification.

        Args:
        ----
            code: Code content
            language: Detected language

        Returns:
        -------
            Confidence score between 0.0 and 1.0

        """
        confidence = 0.5  # Base confidence

        # Boost for recognized languages
        if language.lower() in ["python", "javascript", "typescript", "java", "go"]:
            confidence += 0.2

        # Boost for code-like patterns
        if re.search(
            r"\b(function|def|class|import|from|var|let|const)\b", code, re.IGNORECASE
        ):
            confidence += 0.1

        # Boost for common programming syntax
        if re.search(r"[{}()\[\];]", code):
            confidence += 0.1

        # Boost for substantial code (multiple lines)
        if len(code.split("\n")) > 2:
            confidence += 0.1

        return min(confidence, 1.0)

    def _identify_functions(self, code: str) -> list[str]:
        """Identify function names in code block.

        Args:
        ----
            code: Code content

        Returns:
        -------
            List of function names found

        """
        functions = []

        # Python functions
        python_funcs = re.findall(r"def\s+(\w+)\s*\(", code)
        functions.extend(python_funcs)

        # JavaScript/TypeScript functions
        js_funcs = re.findall(
            r"function\s+(\w+)\s*\(|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:function|\()",
            code,
        )
        for func in js_funcs:
            if isinstance(func, tuple):
                functions.extend([f for f in func if f])
            else:
                functions.append(func)

        # Java/C# methods
        java_funcs = re.findall(
            r"(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\(", code
        )
        functions.extend(java_funcs)

        return functions

    def _identify_questions(self, text: str) -> list[dict[str, Any]]:
        """Identify questions in the text.

        Args:
        ----
            text: Text containing potential questions

        Returns:
        -------
            List of question patterns with metadata

        """
        questions = []

        for pattern in self.question_patterns:
            for match in pattern.finditer(text):
                question_text = match.group(0).strip()

                # Calculate confidence based on question characteristics
                confidence = self._calculate_question_confidence(question_text)

                question = {
                    "text": question_text,
                    "start_pos": match.start(),
                    "end_pos": match.end(),
                    "confidence": confidence,
                    "question_type": self._classify_question_type(question_text),
                }
                questions.append(question)

        return questions

    def _calculate_question_confidence(self, question: str) -> float:
        """Calculate confidence score for question identification.

        Args:
        ----
            question: Question text

        Returns:
        -------
            Confidence score between 0.0 and 1.0

        """
        confidence = 0.3  # Base confidence

        # Boost for question words
        question_words = [
            "how",
            "what",
            "why",
            "when",
            "where",
            "which",
            "can",
            "could",
            "would",
        ]
        if any(word in question.lower() for word in question_words):
            confidence += 0.3

        # Boost for ending with question mark
        if question.endswith("?"):
            confidence += 0.2

        # Boost for substantial questions (more than 5 words)
        if len(question.split()) > 5:
            confidence += 0.2

        return min(confidence, 1.0)

    def _classify_question_type(self, question: str) -> str:
        """Classify the type of question.

        Args:
        ----
            question: Question text

        Returns:
        -------
            Question type classification

        """
        question_lower = question.lower()

        if any(
            word in question_lower for word in ["how", "implement", "create", "build"]
        ):
            return "how_to"
        if any(word in question_lower for word in ["what", "which", "which one"]):
            return "what_which"
        if any(word in question_lower for word in ["why", "reason", "cause"]):
            return "why_explanation"
        if any(word in question_lower for word in ["error", "problem", "issue", "bug"]):
            return "troubleshooting"
        if any(
            word in question_lower
            for word in ["best", "better", "recommend", "suggest"]
        ):
            return "recommendation"
        return "general"

    def _identify_error_patterns(self, text: str) -> list[dict[str, Any]]:
        """Identify error messages and debugging patterns.

        Args:
        ----
            text: Text containing potential error patterns

        Returns:
        -------
            List of error patterns with metadata

        """
        error_patterns = []

        for pattern in self.error_patterns:
            for match in pattern.finditer(text):
                error_text = match.group(0)

                # Extract error type if available
                error_type = None
                error_type_match = re.search(
                    r"\b([A-Z][a-z]*(Error|Exception|Warning))\b", error_text
                )
                if error_type_match:
                    error_type = error_type_match.group(1)

                error = {
                    "text": error_text,
                    "error_type": error_type,
                    "start_pos": match.start(),
                    "end_pos": match.end(),
                    "confidence": 0.8 if error_type else 0.6,
                    "is_traceback": bool(
                        re.search(r"traceback|stack trace", error_text, re.IGNORECASE)
                    ),
                }
                error_patterns.append(error)

        return error_patterns

    def _identify_technical_keywords(self, text: str) -> list[dict[str, Any]]:
        """Identify technical keywords and their categories.

        Args:
        ----
            text: Text to analyze for technical keywords

        Returns:
        -------
            List of technical keywords with categories

        """
        keywords = []
        text_lower = text.lower()

        for category, terms in self.technical_keywords.items():
            for term in terms:
                if term in text_lower:
                    # Find all occurrences
                    for match in re.finditer(rf"\b{re.escape(term)}\b", text_lower):
                        keyword = {
                            "term": term,
                            "category": category,
                            "start_pos": match.start(),
                            "end_pos": match.end(),
                            "context": text[
                                max(0, match.start() - 20) : match.end() + 20
                            ],
                        }
                        keywords.append(keyword)

        return keywords

    def _identify_decisions(self, text: str) -> list[dict[str, Any]]:
        """Identify decision points and reasoning.

        Args:
        ----
            text: Text containing potential decision points

        Returns:
        -------
            List of decision patterns with alternatives and reasoning

        """
        decisions = []

        for pattern in self.decision_patterns:
            for match in pattern.finditer(text):
                decision_text = match.group(0).strip()

                # Extract decision context
                context_start = max(0, match.start() - 200)
                context_end = min(len(text), match.end() + 200)
                context = text[context_start:context_end]

                # Identify alternatives (simple heuristic)
                alternatives = self._extract_alternatives(context)

                # Extract reasoning
                reasoning = self._extract_reasoning(context)

                # Extract the actual choice from the decision text
                choice = self._extract_choice(decision_text, context)

                decision = {
                    "text": decision_text,
                    "context": context.strip(),
                    "alternatives": alternatives,
                    "choice": choice,
                    "reasoning": reasoning,
                    "confidence": 0.7 if reasoning else 0.5,
                    "start_pos": match.start(),
                    "end_pos": match.end(),
                }
                decisions.append(decision)

        return decisions

    def _extract_alternatives(self, context: str) -> list[str]:
        """Extract alternative options from decision context.

        Args:
        ----
            context: Context text around decision

        Returns:
        -------
            List of identified alternatives

        """
        alternatives = []

        # Look for "vs", "or", "between" patterns
        vs_pattern = re.compile(
            r"(\w+(?:\s+\w+)*)\s+(?:vs|versus|or)\s+(\w+(?:\s+\w+)*)", re.IGNORECASE
        )
        for match in vs_pattern.finditer(context):
            alternatives.extend([match.group(1), match.group(2)])

        # Look for "either...or" patterns
        either_or_pattern = re.compile(
            r"either\s+(\w+(?:\s+\w+)*)\s+or\s+(\w+(?:\s+\w+)*)", re.IGNORECASE
        )
        for match in either_or_pattern.finditer(context):
            alternatives.extend([match.group(1), match.group(2)])

        return list(set(alternatives))  # Remove duplicates

    def _extract_reasoning(self, context: str) -> str | None:
        """Extract reasoning from decision context.

        Args:
        ----
            context: Context text around decision

        Returns:
        -------
            Reasoning text if found, None otherwise

        """
        reasoning_patterns = [
            re.compile(r"because\s+([^,.!?]+)", re.IGNORECASE),
            re.compile(r"since\s+([^,.!?]+)", re.IGNORECASE),
            re.compile(r"due\s+to\s+([^,.!?]+)", re.IGNORECASE),
            re.compile(r"reason\s+(?:is|was)\s+([^,.!?]+)", re.IGNORECASE),
        ]

        for pattern in reasoning_patterns:
            match = pattern.search(context)
            if match:
                return match.group(1).strip()

        return None

    def _extract_choice(self, decision_text: str, context: str) -> str | None:
        """Extract the actual choice from decision text and context.

        Args:
        ----
            decision_text: The decision indicator text
            context: Context around the decision

        Returns:
        -------
            The extracted choice if found, None otherwise

        """
        # Look for patterns like "I'll go with X", "chose X", "use X"
        choice_patterns = [
            re.compile(
                r"(?:i\'ll go with|i will use|let\'s use|we should use|chose|selected|using)\s+([A-Z]\w+(?:\s+[A-Z]\w+)*)",
                re.IGNORECASE,
            ),
            re.compile(
                r"(?:i\'ll go with|i will use|let\'s use|we should use)\s+(\w+)",
                re.IGNORECASE,
            ),
        ]

        # Check decision text first
        for pattern in choice_patterns:
            match = pattern.search(decision_text)
            if match:
                return match.group(1).strip()

        # Then check context
        for pattern in choice_patterns:
            match = pattern.search(context)
            if match:
                return match.group(1).strip()

        # If no explicit choice, try to extract from "go with X" pattern
        go_with_match = re.search(r"go with\s+(\w+)", decision_text, re.IGNORECASE)
        if go_with_match:
            return go_with_match.group(1).strip()

        return None

    def _identify_solutions(self, text: str) -> list[dict[str, Any]]:
        """Identify solution patterns and approaches.

        Args:
        ----
            text: Text containing potential solutions

        Returns:
        -------
            List of solution patterns with metadata

        """
        solutions = []

        # Solution indicators
        solution_patterns = [
            re.compile(
                r"\b(solution|answer|fix|resolve|here\'s|try this|the way to|you need to|this creates)\b",
                re.IGNORECASE,
            ),
            re.compile(
                r"\b(implemented|created|built|developed|wrote)\b", re.IGNORECASE
            ),
            re.compile(
                r"([A-Z]\w+.*?(?:creates|provides|enables|handles|implements))",
                re.MULTILINE,
            ),
        ]

        for pattern in solution_patterns:
            for match in pattern.finditer(text):
                solution_text = text[
                    match.start() : match.end() + 300
                ]  # Include more context after

                solution = {
                    "text": solution_text.strip(),
                    "start_pos": match.start(),
                    "confidence": 0.7,
                    "has_code": bool(self.code_block_pattern.search(solution_text)),
                }
                solutions.append(solution)

        return solutions

    def _identify_debugging_steps(self, text: str) -> list[dict[str, Any]]:
        """Identify debugging and troubleshooting steps.

        Args:
        ----
            text: Text containing potential debugging steps

        Returns:
        -------
            List of debugging step patterns

        """
        debugging_steps = []

        # Debugging indicators
        debugging_patterns = [
            re.compile(
                r"\b(check|verify|test|debug|troubleshoot|diagnose)\b", re.IGNORECASE
            ),
            re.compile(
                r"\b(step\s+\d+|first|second|then|next|finally)\b", re.IGNORECASE
            ),
        ]

        for pattern in debugging_patterns:
            for match in pattern.finditer(text):
                step_text = match.group(0)

                debugging_step = {
                    "text": step_text,
                    "start_pos": match.start(),
                    "end_pos": match.end(),
                    "confidence": 0.6,
                }
                debugging_steps.append(debugging_step)

        return debugging_steps

    def _calculate_pattern_confidence(
        self, patterns: dict[str, Any]
    ) -> dict[str, float]:
        """Calculate confidence scores for all pattern types.

        Args:
        ----
            patterns: Dictionary of identified patterns

        Returns:
        -------
            Dictionary of confidence scores by pattern type

        """
        confidence_scores = {}

        for pattern_type, pattern_list in patterns.items():
            if pattern_type == "confidence_scores":
                continue  # Skip the confidence scores themselves

            if not pattern_list:
                confidence_scores[pattern_type] = 0.0
                continue

            # Calculate average confidence for this pattern type
            total_confidence = 0.0
            count = 0

            for pattern in pattern_list:
                if isinstance(pattern, dict) and "confidence" in pattern:
                    total_confidence += pattern["confidence"]
                    count += 1

            confidence_scores[pattern_type] = (
                total_confidence / count if count > 0 else 0.0
            )

        return confidence_scores

    def get_pattern_summary(self, patterns: dict[str, Any]) -> dict[str, Any]:
        """Generate a summary of identified patterns.

        Args:
        ----
            patterns: Dictionary of identified patterns

        Returns:
        -------
            Summary statistics and insights

        """
        summary = {
            "total_patterns": sum(
                len(patterns[key]) for key in patterns if key != "confidence_scores"
            ),
            "pattern_counts": {
                key: len(patterns[key])
                for key in patterns
                if key != "confidence_scores"
            },
            "high_confidence_patterns": {},
            "dominant_categories": [],
        }

        # Count high-confidence patterns (> 0.7)
        for pattern_type, pattern_list in patterns.items():
            if pattern_type == "confidence_scores":
                continue

            high_confidence = [
                p
                for p in pattern_list
                if isinstance(p, dict) and p.get("confidence", 0) > 0.7
            ]
            summary["high_confidence_patterns"][pattern_type] = len(high_confidence)

        # Determine dominant categories
        if "technical_keywords" in patterns:
            categories = {}
            for keyword in patterns["technical_keywords"]:
                category = keyword.get("category", "unknown")
                categories[category] = categories.get(category, 0) + 1

            if categories:
                summary["dominant_categories"] = sorted(
                    categories.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:3]

        return summary
