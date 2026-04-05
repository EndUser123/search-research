from __future__ import annotations

from collections import Counter, defaultdict
from collections import defaultdict
from datetime import datetime, timedelta
from datetime import timedelta
from typing import Any
import logging
import os
import re

from ..interfaces.analysis_interfaces import (

#!/usr/bin/env python3
"""Pattern Recognizer Implementation
Follows CSF NIP standards for pattern detection and analysis.
"""


    ChatMessage,
    IConfigurationManager,
    ILogger,
    IPatternRecognizer,
)


class PatternRecognizer(IPatternRecognizer):
    """Pattern recognizer following SRP with comprehensive analysis capabilities."""

    def __init__(self, container=None) -> None:
        self.container = container
        self.logger = container.resolve(ILogger) if container else None
        self.config_manager = (
            container.resolve(IConfigurationManager) if container else None
        )

        # Initialize pattern definitions
        self._conversation_patterns = self._load_conversation_patterns()
        self._intent_patterns = self._load_intent_patterns()
        self._temporal_patterns = self._load_temporal_patterns()

    async def detect_patterns(
        self, messages: list[ChatMessage]
    ) -> list[dict[str, Any]]:
        """Detect comprehensive conversation patterns."""
        try:
            if not messages:
                return []

            if self.logger:
                await self.logger.debug(
                    f"Detecting patterns in {len(messages)} messages"
                )

            patterns = []

            # Detect conversation flow patterns
            flow_patterns = await self._detect_conversation_flow_patterns(messages)
            patterns.extend(flow_patterns)

            # Detect temporal patterns
            temporal_patterns = await self._detect_temporal_patterns(messages)
            patterns.extend(temporal_patterns)

            # Detect content patterns
            content_patterns = await self._detect_content_patterns(messages)
            patterns.extend(content_patterns)

            # Detect interaction patterns
            interaction_patterns = await self._detect_interaction_patterns(messages)
            patterns.extend(interaction_patterns)

            # Detect sentiment patterns
            sentiment_patterns = await self._detect_sentiment_patterns(messages)
            patterns.extend(sentiment_patterns)

            if self.logger:
                await self.logger.info(f"Detected {len(patterns)} patterns")

            return patterns

        except Exception as e:
            if self.logger:
                await self.logger.exception(f"Error detecting patterns: {e}")
            return []

    async def classify_intent(self, message: ChatMessage) -> str:
        """Classify message intent using pattern matching."""
        try:
            content = message.content.lower()
            scores = {}

            # Score against each intent pattern
            for intent, patterns in self._intent_patterns.items():
                score = 0
                for pattern in patterns:
                    matches = len(re.findall(pattern, content, re.IGNORECASE))
                    score += matches * self._get_intent_weight(intent)
                scores[intent] = score

            # Return intent with highest score
            if scores:
                best_intent = max(scores, key=scores.get)
                if scores[best_intent] > 0:
                    return best_intent

            return "general"

        except Exception as e:
            if self.logger:
                await self.logger.exception(f"Error classifying intent: {e}")
            return "general"

    async def get_pattern_confidence(self, pattern: str, message: ChatMessage) -> float:
        """Calculate confidence score for pattern detection."""
        try:
            if not pattern or not message.content:
                return 0.0

            content = message.content.lower()

            # Find matching patterns
            pattern_matches = []
            for intent, patterns in self._intent_patterns.items():
                if intent == pattern:
                    for p in patterns:
                        matches = re.findall(p, content, re.IGNORECASE)
                        pattern_matches.extend(matches)

            if not pattern_matches:
                return 0.0

            # Calculate confidence based on multiple factors
            base_confidence = min(len(pattern_matches) * 0.2, 1.0)

            # Adjust for message length (longer messages get higher confidence)
            length_factor = min(len(message.content) / 200, 1.0)

            # Adjust for context (metadata patterns)
            context_factor = self._get_context_confidence(message, pattern)

            confidence = (
                base_confidence * 0.6 + length_factor * 0.2 + context_factor * 0.2
            )
            return min(confidence, 1.0)

        except Exception as e:
            if self.logger:
                await self.logger.exception(
                    f"Error calculating pattern confidence: {e}"
                )
            return 0.0

    async def _detect_conversation_flow_patterns(
        self, messages: list[ChatMessage]
    ) -> list[dict[str, Any]]:
        """Detect conversation flow patterns."""
        patterns = []

        try:
            # Question-answer pairs
            qa_pairs = self._find_question_answer_pairs(messages)
            if qa_pairs:
                patterns.append(
                    {
                        "type": "conversation_flow",
                        "pattern": "question_answer",
                        "count": len(qa_pairs),
                        "confidence": 0.8,
                        "examples": qa_pairs[:3],
                    },
                )

            # Topic transitions
            transitions = self._detect_topic_transitions(messages)
            if transitions:
                patterns.append(
                    {
                        "type": "conversation_flow",
                        "pattern": "topic_transitions",
                        "count": len(transitions),
                        "confidence": 0.7,
                        "examples": transitions[:3],
                    },
                )

            # Thread patterns
            threads = self._identify_conversation_threads(messages)
            if len(threads) > 1:
                patterns.append(
                    {
                        "type": "conversation_flow",
                        "pattern": "multiple_threads",
                        "count": len(threads),
                        "confidence": 0.9,
                        "details": {"thread_lengths": [len(t) for t in threads]},
                    },
                )

        except Exception as e:
            if self.logger:
                await self.logger.exception(
                    f"Error detecting conversation flow patterns: {e}"
                )

        return patterns

    async def _detect_temporal_patterns(
        self, messages: list[ChatMessage]
    ) -> list[dict[str, Any]]:
        """Detect temporal patterns."""
        patterns = []

        try:
            if not messages:
                return patterns

            # Activity bursts
            bursts = self._detect_activity_bursts(messages)
            if bursts:
                patterns.append(
                    {
                        "type": "temporal",
                        "pattern": "activity_bursts",
                        "count": len(bursts),
                        "confidence": 0.8,
                        "details": bursts,
                    },
                )

            # Response times
            response_times = self._calculate_response_times(messages)
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                patterns.append(
                    {
                        "type": "temporal",
                        "pattern": "response_times",
                        "average_time": avg_response_time,
                        "confidence": 0.9,
                        "details": {"times": response_times[:10]},
                    },
                )

            # Peak activity hours
            peak_hours = self._identify_peak_activity_hours(messages)
            if peak_hours:
                patterns.append(
                    {
                        "type": "temporal",
                        "pattern": "peak_activity_hours",
                        "hours": peak_hours,
                        "confidence": 0.7,
                    },
                )

        except Exception as e:
            if self.logger:
                await self.logger.exception(f"Error detecting temporal patterns: {e}")

        return patterns

    async def _detect_content_patterns(
        self, messages: list[ChatMessage]
    ) -> list[dict[str, Any]]:
        """Detect content-based patterns."""
        patterns = []

        try:
            # Common keywords
            keywords = self._extract_common_keywords(messages)
            if keywords:
                patterns.append(
                    {
                        "type": "content",
                        "pattern": "common_keywords",
                        "keywords": keywords[:10],
                        "confidence": 0.8,
                    },
                )

            # Code snippets
            code_snippets = self._detect_code_snippets(messages)
            if code_snippets:
                patterns.append(
                    {
                        "type": "content",
                        "pattern": "code_snippets",
                        "count": len(code_snippets),
                        "confidence": 0.9,
                        "examples": code_snippets[:3],
                    },
                )

            # URLs and links
            links = self._extract_links(messages)
            if links:
                patterns.append(
                    {
                        "type": "content",
                        "pattern": "shared_links",
                        "count": len(links),
                        "confidence": 0.95,
                        "examples": links[:5],
                    },
                )

        except Exception as e:
            if self.logger:
                await self.logger.exception(f"Error detecting content patterns: {e}")

        return patterns

    async def _detect_interaction_patterns(
        self, messages: list[ChatMessage]
    ) -> list[dict[str, Any]]:
        """Detect interaction patterns."""
        patterns = []

        try:
            # Participant activity
            activity = self._analyze_participant_activity(messages)
            if activity:
                patterns.append(
                    {
                        "type": "interaction",
                        "pattern": "participant_activity",
                        "participants": activity,
                        "confidence": 0.9,
                    },
                )

            # Mention patterns
            mentions = self._detect_mentions(messages)
            if mentions:
                patterns.append(
                    {
                        "type": "interaction",
                        "pattern": "mentions",
                        "count": len(mentions),
                        "confidence": 0.8,
                        "details": mentions,
                    },
                )

        except Exception as e:
            if self.logger:
                await self.logger.exception(
                    f"Error detecting interaction patterns: {e}"
                )

        return patterns

    async def _detect_sentiment_patterns(
        self, messages: list[ChatMessage]
    ) -> list[dict[str, Any]]:
        """Detect sentiment patterns."""
        patterns = []

        try:
            # Simple sentiment analysis based on keywords
            sentiment_scores = self._calculate_sentiment_scores(messages)
            if sentiment_scores:
                avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                patterns.append(
                    {
                        "type": "sentiment",
                        "pattern": "overall_sentiment",
                        "score": avg_sentiment,
                        "confidence": 0.7,
                        "sentiment": self._classify_sentiment(avg_sentiment),
                    },
                )

        except Exception as e:
            if self.logger:
                await self.logger.exception(f"Error detecting sentiment patterns: {e}")

        return patterns

    def _load_conversation_patterns(self) -> dict[str, list[str]]:
        """Load conversation pattern definitions."""
        return {
            "greeting": [r"\b(hi|hello|hey|good morning|good afternoon)\b"],
            "farewell": [r"\b(goodbye|bye|see you|take care)\b"],
            "question": [r"\?", r"\b(how|what|why|when|where|which|who)\b"],
            "agreement": [r"\b(yes|yeah|sure|absolutely|definitely)\b"],
            "disagreement": [r"\b(no|disagree|don't think|not sure)\b"],
            "request": [r"\b(can you|could you|please|help)\b"],
            "thanks": [r"\b(thank|thanks|appreciate)\b"],
        }

    def _load_intent_patterns(self) -> dict[str, list[str]]:
        """Load intent pattern definitions."""
        return {
            "question": [r"\?", r"\b(how|what|why|when|where|which|who)\b"],
            "command": [r"\b(do|run|execute|start|stop|create|delete)\b"],
            "information": [r"\b(according to|based on|the answer is)\b"],
            "greeting": [r"\b(hi|hello|hey|good morning)\b"],
            "farewell": [r"\b(goodbye|bye|see you)\b"],
            "help": [r"\b(help|assist|support|guidance)\b"],
            "technical": [r"\b(code|programming|debug|error|function)\b"],
            "discussion": [r"\b(think|believe|opinion|maybe|perhaps)\b"],
        }

    def _load_temporal_patterns(self) -> dict[str, Any]:
        """Load temporal pattern definitions."""
        return {
            "burst_threshold": 5,  # messages in 5 minutes
            "burst_window": 300,  # 5 minutes in seconds
            "peak_hour_threshold": 3,  # messages per hour
        }

    def _get_intent_weight(self, intent: str) -> float:
        """Get weight for intent scoring."""
        weights = {
            "question": 1.0,
            "command": 0.9,
            "help": 0.8,
            "technical": 0.7,
            "information": 0.6,
            "greeting": 0.5,
            "farewell": 0.5,
            "discussion": 0.4,
        }
        return weights.get(intent, 0.3)

    def _get_context_confidence(self, message: ChatMessage, pattern: str) -> float:
        """Get context-based confidence."""
        confidence = 0.0

        # Check metadata for context clues
        if message.metadata:
            if (
                "category" in message.metadata
                and message.metadata["category"] == pattern
            ):
                confidence += 0.3
            if "tags" in message.metadata and pattern in str(message.metadata["tags"]):
                confidence += 0.2

        return min(confidence, 1.0)

    # Helper methods for pattern detection
    def _find_question_answer_pairs(
        self, messages: list[ChatMessage]
    ) -> list[dict[str, Any]]:
        """Find question-answer pairs in conversation."""
        pairs = []
        for i, msg in enumerate(messages):
            if "?" in msg.content:
                # Look for answer in next few messages
                for j in range(i + 1, min(i + 4, len(messages))):
                    if (
                        messages[j].author != msg.author
                        and len(messages[j].content) > 10
                    ):
                        pairs.append(
                            {
                                "question": (
                                    msg.content[:100] + "..."
                                    if len(msg.content) > 100
                                    else msg.content
                                ),
                                "answer": (
                                    messages[j].content[:100] + "..."
                                    if len(messages[j].content) > 100
                                    else messages[j].content
                                ),
                            },
                        )
                        break
        return pairs

    def _detect_topic_transitions(
        self, messages: list[ChatMessage]
    ) -> list[dict[str, Any]]:
        """Detect topic transitions in conversation."""
        transitions = []
        keywords = [
            "by the way",
            "also",
            "speaking of",
            "that reminds me",
            "another thing",
        ]

        for _i, msg in enumerate(messages):
            for keyword in keywords:
                if keyword in msg.content.lower():
                    transitions.append(
                        {
                            "message": msg.content[:100],
                            "transition_keyword": keyword,
                        },
                    )
        return transitions

    def _identify_conversation_threads(
        self, messages: list[ChatMessage]
    ) -> list[list[ChatMessage]]:
        """Identify separate conversation threads."""
        # Simple implementation: group by time gaps
        threads = []
        current_thread = []

        for _i, msg in enumerate(messages):
            if not current_thread:
                current_thread.append(msg)
            else:
                # Check time gap
                prev_time = datetime.fromisoformat(
                    current_thread[-1].timestamp.replace("Z", "+00:00")
                )
                curr_time = datetime.fromisoformat(msg.timestamp.replace("Z", "+00:00"))
                time_diff = (curr_time - prev_time).total_seconds()

                if time_diff > 1800:  # 30 minutes gap
                    threads.append(current_thread)
                    current_thread = [msg]
                else:
                    current_thread.append(msg)

        if current_thread:
            threads.append(current_thread)

        return threads

    def _detect_activity_bursts(
        self, messages: list[ChatMessage]
    ) -> list[dict[str, Any]]:
        """Detect periods of high activity."""
        bursts = []
        window_size = self._temporal_patterns["burst_window"]
        threshold = self._temporal_patterns["burst_threshold"]

        for i in range(len(messages)):
            window_start = datetime.fromisoformat(
                messages[i].timestamp.replace("Z", "+00:00")
            )
            window_end = window_start + timedelta(seconds=window_size)

            window_messages = []
            for msg in messages[i:]:
                msg_time = datetime.fromisoformat(msg.timestamp.replace("Z", "+00:00"))
                if msg_time <= window_end:
                    window_messages.append(msg)
                else:
                    break

            if len(window_messages) >= threshold:
                bursts.append(
                    {
                        "start_time": window_start.isoformat(),
                        "message_count": len(window_messages),
                        "duration": window_size,
                    },
                )

        return bursts

    def _calculate_response_times(self, messages: list[ChatMessage]) -> list[float]:
        """Calculate response times between messages."""
        response_times = []

        for i in range(1, len(messages)):
            if messages[i].author != messages[i - 1].author:
                prev_time = datetime.fromisoformat(
                    messages[i - 1].timestamp.replace("Z", "+00:00")
                )
                curr_time = datetime.fromisoformat(
                    messages[i].timestamp.replace("Z", "+00:00")
                )
                response_time = (curr_time - prev_time).total_seconds()
                response_times.append(response_time)

        return response_times

    def _identify_peak_activity_hours(self, messages: list[ChatMessage]) -> list[int]:
        """Identify peak activity hours."""
        hour_counts = Counter()

        for msg in messages:
            hour = datetime.fromisoformat(msg.timestamp.replace("Z", "+00:00")).hour
            hour_counts[hour] += 1

        threshold = self._temporal_patterns["peak_hour_threshold"]
        peak_hours = [hour for hour, count in hour_counts.items() if count >= threshold]

        return sorted(peak_hours)

    def _extract_common_keywords(
        self, messages: list[ChatMessage]
    ) -> list[tuple[str, int]]:
        """Extract common keywords from messages."""
        word_counts = Counter()

        for msg in messages:
            words = re.findall(r"\b\w+\b", msg.content.lower())
            # Filter out common words
            words = [
                w
                for w in words
                if w
                not in [
                    "the",
                    "a",
                    "an",
                    "and",
                    "or",
                    "but",
                    "in",
                    "on",
                    "at",
                    "to",
                    "for",
                    "of",
                    "with",
                    "by",
                    "i",
                    "you",
                    "he",
                    "she",
                    "it",
                    "we",
                    "they",
                ]
            ]
            word_counts.update(words)

        return word_counts.most_common(20)

    def _detect_code_snippets(self, messages: list[ChatMessage]) -> list[str]:
        """Detect code snippets in messages."""
        code_patterns = [
            r"```[\s\S]*?```",  # Code blocks
            r"`[^`]+`",  # Inline code
            r"\b(def |function |class |import |from |#|//|/\*)",  # Code indicators
        ]

        snippets = []
        for msg in messages:
            for pattern in code_patterns:
                matches = re.findall(pattern, msg.content)
                snippets.extend(matches)

        return snippets[:10]

    def _extract_links(self, messages: list[ChatMessage]) -> list[str]:
        """Extract URLs from messages."""
        url_pattern = r'https?://[^\s<>"]+'
        links = []

        for msg in messages:
            matches = re.findall(url_pattern, msg.content)
            links.extend(matches)

        return links

    def _analyze_participant_activity(
        self, messages: list[ChatMessage]
    ) -> list[dict[str, Any]]:
        """Analyze participant activity levels."""
        activity = Counter()
        total_chars = defaultdict(int)

        for msg in messages:
            activity[msg.author] += 1
            total_chars[msg.author] += len(msg.content)

        participants = []
        for author, count in activity.items():
            participants.append(
                {
                    "name": author,
                    "message_count": count,
                    "total_characters": total_chars[author],
                    "avg_message_length": total_chars[author] / count,
                },
            )

        return sorted(participants, key=lambda x: x["message_count"], reverse=True)

    def _detect_mentions(self, messages: list[ChatMessage]) -> list[dict[str, Any]]:
        """Detect mentions of other participants."""
        mentions = []

        for msg in messages:
            # Simple @mention detection
            mention_pattern = r"@(\w+)"
            matches = re.findall(mention_pattern, msg.content)
            for mention in matches:
                mentions.append(
                    {
                        "mentioner": msg.author,
                        "mentioned": mention,
                        "message_id": msg.id,
                    },
                )

        return mentions

    def _calculate_sentiment_scores(self, messages: list[ChatMessage]) -> list[float]:
        """Calculate simple sentiment scores."""
        positive_words = {
            "good",
            "great",
            "excellent",
            "awesome",
            "nice",
            "love",
            "like",
            "thank",
            "thanks",
            "appreciate",
        }
        negative_words = {
            "bad",
            "terrible",
            "awful",
            "hate",
            "dislike",
            "problem",
            "issue",
            "error",
            "wrong",
            "fail",
        }

        scores = []
        for msg in messages:
            words = set(re.findall(r"\b\w+\b", msg.content.lower()))
            positive_count = len(words & positive_words)
            negative_count = len(words & negative_words)

            if positive_count + negative_count > 0:
                score = (positive_count - negative_count) / (
                    positive_count + negative_count
                )
            else:
                score = 0.0

            scores.append(score)

        return scores

    def _classify_sentiment(self, score: float) -> str:
        """Classify sentiment based on score."""
        if score > 0.3:
            return "positive"
        if score < -0.3:
            return "negative"
        return "neutral"
