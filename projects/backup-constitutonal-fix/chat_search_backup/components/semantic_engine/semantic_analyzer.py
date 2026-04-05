from __future__ import annotations

import logging
import math
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ...domain_models.chat_models import ChatMessage, KnowledgeGraph
from ..interfaces.chat_interfaces import ISemanticEngine

#!/usr/bin/env python3
"""Enhanced Semantic Engine for CHS
Advanced semantic analysis with knowledge graph building and expertise tracking.
"""


# Add CSF NIP paths

sys.path.append(str(Path(__file__).parent.parent.parent.parent.parent.parent))
sys.path.append(
    str(Path(__file__).parent.parent.parent.parent.parent.parent / "src" / "lib")
)



@dataclass
class SemanticRelation:
    """Semantic relation between concepts."""

    source: str
    target: str
    relation_type: str  # "similar", "causes", "solves", "related_to", "part_of"
    strength: float
    evidence_count: int = 1
    last_observed: datetime = None

    def __post_init__(self):
        if self.last_observed is None:
            self.last_observed = datetime.now()


class TopicExtractor:
    """Extract topics from chat messages using various techniques."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.technical_terms = self._load_technical_terms()
        self.stop_words = self._load_stop_words()

    def _load_technical_terms(self) -> set[str]:
        """Load technical terms dictionary."""
        return {
            # Programming languages
            "python",
            "javascript",
            "java",
            "cpp",
            "csharp",
            "go",
            "rust",
            "ruby",
            # Technologies
            "docker",
            "kubernetes",
            "aws",
            "azure",
            "gcp",
            "terraform",
            "ansible",
            # Concepts
            "api",
            "rest",
            "graphql",
            "microservices",
            "monolith",
            "serverless",
            # Development practices
            "testing",
            "tdd",
            "cicd",
            "devops",
            "agile",
            "scrum",
            "kanban",
            # Database
            "sql",
            "nosql",
            "mongodb",
            "postgresql",
            "mysql",
            "redis",
            "elasticsearch",
            # Tools
            "git",
            "github",
            "gitlab",
            "jenkins",
            "travis",
            "circleci",
            # Security
            "authentication",
            "authorization",
            "oauth",
            "jwt",
            "ssl",
            "tls",
            # Performance
            "optimization",
            "caching",
            "load_balancing",
            "scaling",
            "monitoring",
            # AI/ML
            "machine_learning",
            "neural_network",
            "deep_learning",
            "tensorflow",
            "pytorch",
        }

    def _load_stop_words(self) -> set[str]:
        """Load common stop words."""
        return {
            "the",
            "is",
            "at",
            "which",
            "on",
            "and",
            "a",
            "to",
            "are",
            "as",
            "was",
            "were",
            "will",
            "be",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "but",
            "or",
            "if",
            "they",
            "he",
            "she",
            "it",
            "we",
            "you",
            "i",
            "this",
            "that",
            "these",
            "those",
            "am",
            "been",
            "being",
            "for",
            "in",
            "of",
            "with",
            "by",
            "from",
            "about",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "under",
            "again",
            "further",
            "then",
            "once",
        }

    def extract_keywords(self, text: str) -> list[str]:
        """Extract keywords from text."""
        # Convert to lowercase and split
        words = re.findall(r"\b\w+\b", text.lower())

        # Filter out stop words and short words
        keywords = [
            word for word in words if word not in self.stop_words and len(word) > 2
        ]

        # Boost technical terms
        technical_keywords = [word for word in keywords if word in self.technical_terms]

        # Combine technical terms and other keywords
        all_keywords = technical_keywords + [
            word for word in keywords if word not in technical_terms
        ]

        return all_keywords[:20]  # Limit to top 20

    def extract_phrases(self, text: str) -> list[str]:
        """Extract meaningful phrases from text."""
        phrases = []

        # Extract quoted phrases
        quoted_phrases = re.findall(r'"([^"]+)"', text)
        phrases.extend(quoted_phrases)

        # Extract code references
        code_refs = re.findall(r"`([^`]+)`", text)
        phrases.extend(code_refs)

        # Extract compound technical terms
        compound_patterns = [
            r"\b\w+\s+\w+\s+(?:api|service|database|server|client|system)\b",
            r"\b(?:docker|kubernetes|aws|azure|gcp)\s+\w+\b",
            r"\b\w+\s+(?:error|issue|problem|solution|fix)\b",
        ]

        for pattern in compound_patterns:
            matches = re.findall(pattern, text.lower())
            phrases.extend(matches)

        return list(set(phrases))  # Remove duplicates

    def extract_topics_from_message(self, message: ChatMessage) -> list[str]:
        """Extract topics from a single message."""
        topics = []

        # Extract keywords
        keywords = self.extract_keywords(message.content)
        topics.extend(keywords)

        # Extract phrases
        phrases = self.extract_phrases(message.content)
        topics.extend(phrases)

        # Use existing semantic tags
        topics.extend(message.semantic_tags)

        # Add context as topic
        topics.append(message.context.value)

        # Add project name if available
        if message.project_name:
            topics.append(message.project_name)

        # Remove duplicates and return
        return list(set(topics))

    def extract_topics_from_messages(
        self, messages: list[ChatMessage]
    ) -> dict[str, list[ChatMessage]]:
        """Extract topics from multiple messages."""
        topic_messages = defaultdict(list)

        for message in messages:
            topics = self.extract_topics_from_message(message)
            for topic in topics:
                topic_messages[topic].append(message)

        self.logger.info(
            f"Extracted {len(topic_messages)} topics from {len(messages)} messages"
        )
        return dict(topic_messages)


class SimilarityCalculator:
    """Calculate semantic similarity between messages."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def jaccard_similarity(self, set1: set[str], set2: set[str]) -> float:
        """Calculate Jaccard similarity between two sets."""
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0

    def cosine_similarity(self, vec1: list[float], vec2: list[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec1) != len(vec2) or len(vec1) == 0:
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2, strict=False))
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using multiple methods."""
        # Extract word sets
        words1 = set(re.findall(r"\b\w+\b", text1.lower()))
        words2 = set(re.findall(r"\b\w+\b", text2.lower()))

        # Jaccard similarity
        jaccard_sim = self.jaccard_similarity(words1, words2)

        # Word order similarity (simplified)
        words1_list = list(words1)
        words2_list = list(words2)
        order_sim = 0.0

        if words1_list and words2_list:
            # Calculate overlap in word positions
            overlap = 0
            min_len = min(len(words1_list), len(words2_list))
            for i in range(min_len):
                if words1_list[i] == words2_list[i]:
                    overlap += 1
            order_sim = overlap / max(len(words1_list), len(words2_list))

        # Combine similarities
        return jaccard_sim * 0.8 + order_sim * 0.2

    def calculate_message_similarity(
        self, message1: ChatMessage, message2: ChatMessage
    ) -> float:
        """Calculate semantic similarity between two messages."""
        similarity_scores = []

        # Text content similarity
        text_sim = self.calculate_text_similarity(message1.content, message2.content)
        similarity_scores.append(("text", text_sim, 0.4))

        # Topic overlap similarity
        topics1 = set(message1.semantic_tags)
        topics2 = set(message2.semantic_tags)
        topic_sim = self.jaccard_similarity(topics1, topics2)
        similarity_scores.append(("topics", topic_sim, 0.3))

        # Context similarity
        context_sim = 1.0 if message1.context == message2.context else 0.3
        similarity_scores.append(("context", context_sim, 0.1))

        # Project similarity
        project_sim = (
            1.0
            if message1.project_name == message2.project_name == message1.project_name
            else 0.5
        )
        similarity_scores.append(("project", project_sim, 0.1))

        # Temporal similarity (messages closer in time are more similar)
        time_diff = abs(message1.timestamp - message2.timestamp) / 1000 / 3600  # hours
        temporal_sim = max(0, 1 - time_diff / 168)  # Decay over a week
        similarity_scores.append(("temporal", temporal_sim, 0.1))

        # Weighted average
        weighted_sum = sum(score * weight for _, score, weight in similarity_scores)
        total_weight = sum(weight for _, _, weight in similarity_scores)

        return weighted_sum / total_weight if total_weight > 0 else 0.0


class KnowledgeGraphBuilder:
    """Build and maintain knowledge graphs from conversations."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.similarity_calculator = SimilarityCalculator()

    def build_initial_graph(self, messages: list[ChatMessage]) -> KnowledgeGraph:
        """Build initial knowledge graph from messages."""
        graph = KnowledgeGraph()

        # Add nodes for messages
        for message in messages:
            node_data = {
                "type": "message",
                "content_preview": (
                    message.content[:100] + "..."
                    if len(message.content) > 100
                    else message.content
                ),
                "timestamp": message.timestamp,
                "context": message.context.value,
                "project": message.project_name,
                "topics": message.semantic_tags,
                "intensity": message.intensity_score,
            }
            graph.add_node(message.id, node_data)

        # Add nodes for topics
        all_topics = set()
        for message in messages:
            all_topics.update(message.semantic_tags)

        for topic in all_topics:
            topic_messages = [m for m in messages if topic in m.semantic_tags]
            node_data = {
                "type": "topic",
                "message_count": len(topic_messages),
                "contexts": list({m.context.value for m in topic_messages}),
                "projects": list(
                    {m.project_name for m in topic_messages if m.project_name}
                ),
                "first_seen": min(m.timestamp for m in topic_messages),
                "last_seen": max(m.timestamp for m in topic_messages),
            }
            graph.add_node(f"topic_{topic}", node_data)

        # Add edges based on similarity and topic relationships
        self._add_similarity_edges(graph, messages)
        self._add_topic_edges(graph, messages)

        # Calculate centrality scores
        self._calculate_centrality_scores(graph)

        self.logger.info(
            f"Built knowledge graph with {graph.node_count} nodes and {graph.edge_count} edges"
        )
        return graph

    def update_graph(
        self, graph: KnowledgeGraph, new_messages: list[ChatMessage]
    ) -> KnowledgeGraph:
        """Update existing knowledge graph with new messages."""
        # Add new message nodes
        for message in new_messages:
            if message.id not in graph.nodes:
                node_data = {
                    "type": "message",
                    "content_preview": (
                        message.content[:100] + "..."
                        if len(message.content) > 100
                        else message.content
                    ),
                    "timestamp": message.timestamp,
                    "context": message.context.value,
                    "project": message.project_name,
                    "topics": message.semantic_tags,
                    "intensity": message.intensity_score,
                }
                graph.add_node(message.id, node_data)

        # Add new topic nodes
        existing_messages = [m for m in new_messages if m.id in graph.nodes]
        all_topics = set()
        for message in existing_messages:
            all_topics.update(message.semantic_tags)

        for topic in all_topics:
            topic_node_id = f"topic_{topic}"
            if topic_node_id not in graph.nodes:
                topic_messages = [
                    m for m in existing_messages if topic in m.semantic_tags
                ]
                node_data = {
                    "type": "topic",
                    "message_count": len(topic_messages),
                    "contexts": list({m.context.value for m in topic_messages}),
                    "projects": list(
                        {m.project_name for m in topic_messages if m.project_name}
                    ),
                    "first_seen": min(m.timestamp for m in topic_messages),
                    "last_seen": max(m.timestamp for m in topic_messages),
                }
                graph.add_node(topic_node_id, node_data)

        # Add new edges
        self._add_similarity_edges(graph, existing_messages)
        self._add_topic_edges(graph, existing_messages)

        # Update centrality scores
        self._calculate_centrality_scores(graph)

        self.logger.info(
            f"Updated knowledge graph with {len(new_messages)} new messages"
        )
        return graph

    def _add_similarity_edges(
        self, graph: KnowledgeGraph, messages: list[ChatMessage], threshold: float = 0.3
    ) -> None:
        """Add edges based on message similarity."""
        # Sample messages for performance if too many
        sample_size = min(len(messages), 100)
        sampled_messages = (
            messages[:sample_size] if len(messages) > sample_size else messages
        )

        for i, message1 in enumerate(sampled_messages):
            for message2 in sampled_messages[i + 1 :]:
                if message1.id in graph.nodes and message2.id in graph.nodes:
                    similarity = (
                        self.similarity_calculator.calculate_message_similarity(
                            message1, message2
                        )
                    )

                    if similarity > threshold:
                        edge_data = {
                            "type": "similarity",
                            "weight": similarity,
                            "method": "semantic_similarity",
                        }
                        graph.add_edge(message1.id, message2.id, edge_data)

    def _add_topic_edges(
        self, graph: KnowledgeGraph, messages: list[ChatMessage]
    ) -> None:
        """Add edges based on topic relationships."""
        for message in messages:
            if message.id not in graph.nodes:
                continue

            # Connect message to its topics
            for topic in message.semantic_tags:
                topic_node_id = f"topic_{topic}"
                if topic_node_id in graph.nodes:
                    edge_data = {
                        "type": "belongs_to",
                        "weight": 1.0,
                        "relationship": "message_topic",
                    }
                    graph.add_edge(message.id, topic_node_id, edge_data)

            # Connect messages with same topics
            for other_message in messages:
                if message.id != other_message.id and other_message.id in graph.nodes:
                    shared_topics = set(message.semantic_tags) & set(
                        other_message.semantic_tags
                    )
                    if shared_topics:
                        edge_data = {
                            "type": "shared_topics",
                            "weight": len(shared_topics)
                            / max(
                                len(message.semantic_tags),
                                len(other_message.semantic_tags),
                            ),
                            "shared_topics": list(shared_topics),
                        }
                        graph.add_edge(message.id, other_message.id, edge_data)

    def _calculate_centrality_scores(self, graph: KnowledgeGraph) -> None:
        """Calculate centrality scores for nodes."""
        if not graph.nodes:
            return

        # Degree centrality (simple version)
        degree_scores = defaultdict(int)
        for edge in graph.edges:
            degree_scores[edge["source"]] += edge.get("weight", 1)
            degree_scores[edge["target"]] += edge.get("weight", 1)

        # Normalize scores
        max_degree = max(degree_scores.values()) if degree_scores else 1
        graph.centrality_scores = {
            node_id: degree_scores[node_id] / max_degree for node_id in graph.nodes
        }

    def identify_clusters(self, graph: KnowledgeGraph) -> dict[str, list[str]]:
        """Identify clusters in the knowledge graph (simplified)."""
        clusters = defaultdict(list)

        # Simple clustering based on topic nodes
        for node_id, node_data in graph.nodes.items():
            if node_data.get("type") == "topic":
                # Find all messages connected to this topic
                connected_messages = []
                for edge in graph.edges:
                    if edge["target"] == node_id and edge["source"] in graph.nodes:
                        if graph.nodes[edge["source"]].get("type") == "message":
                            connected_messages.append(edge["source"])
                    elif edge["source"] == node_id and edge["target"] in graph.nodes:
                        if graph.nodes[edge["target"]].get("type") == "message":
                            connected_messages.append(edge["target"])

                clusters[node_id] = connected_messages

        graph.clusters = dict(clusters)
        return clusters


class ExpertiseTracker:
    """Track expertise domains from conversation patterns."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def identify_expertise_domains(
        self, messages: list[ChatMessage]
    ) -> dict[str, float]:
        """Identify expertise domains from conversation patterns."""
        domain_scores = defaultdict(float)

        # Technical expertise indicators
        technical_indicators = {
            "programming": [
                "python",
                "javascript",
                "java",
                "code",
                "function",
                "class",
                "method",
            ],
            "devops": [
                "docker",
                "kubernetes",
                "ci/cd",
                "deployment",
                "infrastructure",
                "automation",
            ],
            "database": ["sql", "database", "query", "index", "migration", "schema"],
            "security": [
                "authentication",
                "authorization",
                "security",
                "encryption",
                "vulnerability",
            ],
            "performance": [
                "optimization",
                "performance",
                "caching",
                "scaling",
                "monitoring",
            ],
            "architecture": [
                "architecture",
                "design",
                "pattern",
                "microservices",
                "system",
            ],
            "testing": [
                "testing",
                "test",
                "unit",
                "integration",
                "automation",
                "quality",
            ],
        }

        for message in messages:
            content_lower = message.content.lower()

            for domain, indicators in technical_indicators.items():
                # Count domain-specific terms
                term_count = sum(
                    1 for indicator in indicators if indicator in content_lower
                )

                # Calculate domain score based on term frequency and message intensity
                message_domain_score = (
                    term_count / len(indicators)
                ) * message.intensity_score
                domain_scores[domain] += message_domain_score

        # Normalize scores
        total_score = sum(domain_scores.values())
        if total_score > 0:
            domain_scores = {
                domain: score / total_score for domain, score in domain_scores.items()
            }

        # Filter out very low scores
        domain_scores = {
            domain: score for domain, score in domain_scores.items() if score > 0.05
        }

        self.logger.info(f"Identified {len(domain_scores)} expertise domains")
        return dict(domain_scores)

    def track_expertise_evolution(
        self, messages_by_time: dict[str, list[ChatMessage]]
    ) -> dict[str, dict[str, float]]:
        """Track how expertise evolves over time."""
        evolution = {}

        for time_period, period_messages in messages_by_time.items():
            domain_scores = self.identify_expertise_domains(period_messages)
            evolution[time_period] = domain_scores

        return evolution


class EnhancedSemanticAnalyzer(ISemanticEngine):
    """Enhanced semantic analyzer with comprehensive capabilities."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.topic_extractor = TopicExtractor()
        self.similarity_calculator = SimilarityCalculator()
        self.knowledge_graph_builder = KnowledgeGraphBuilder()
        self.expertise_tracker = ExpertiseTracker()

    def extract_topics(
        self, messages: list[ChatMessage]
    ) -> dict[str, list[ChatMessage]]:
        """Extract topics from messages."""
        return self.topic_extractor.extract_topics_from_messages(messages)

    def calculate_semantic_similarity(
        self, message1: ChatMessage, message2: ChatMessage
    ) -> float:
        """Calculate semantic similarity between messages."""
        return self.similarity_calculator.calculate_message_similarity(
            message1, message2
        )

    def build_knowledge_graph(self, messages: list[ChatMessage]) -> KnowledgeGraph:
        """Build knowledge graph from messages."""
        return self.knowledge_graph_builder.build_initial_graph(messages)

    def update_knowledge_graph(
        self, graph: KnowledgeGraph, new_messages: list[ChatMessage]
    ) -> KnowledgeGraph:
        """Update existing knowledge graph with new messages."""
        return self.knowledge_graph_builder.update_graph(graph, new_messages)

    def find_related_concepts(
        self, concept: str, graph: KnowledgeGraph, max_depth: int = 3
    ) -> list[str]:
        """Find related concepts in knowledge graph."""
        related_concepts = set()
        visited = set()
        queue = [(concept, 0)]

        concept_node_id = f"topic_{concept}"
        if concept_node_id not in graph.nodes:
            # Try to find messages containing the concept
            for node_id, node_data in graph.nodes.items():
                if node_data.get("type") == "message":
                    content_lower = node_data.get("content_preview", "").lower()
                    if concept.lower() in content_lower:
                        queue.append((node_id, 0))
                        break

        while queue and len(visited) < 50:  # Limit search
            current_node, depth = queue.pop(0)

            if current_node in visited or depth > max_depth:
                continue

            visited.add(current_node)

            # Find connected nodes
            for edge in graph.edges:
                neighbor = None
                if edge["source"] == current_node:
                    neighbor = edge["target"]
                elif edge["target"] == current_node:
                    neighbor = edge["source"]

                if neighbor and neighbor not in visited:
                    node_data = graph.nodes.get(neighbor, {})
                    if node_data.get("type") == "topic":
                        topic_name = neighbor.replace("topic_", "")
                        related_concepts.add(topic_name)
                    elif node_data.get("type") == "message":
                        # Extract topics from message
                        for topic in node_data.get("topics", []):
                            related_concepts.add(topic)

                    if depth < max_depth:
                        queue.append((neighbor, depth + 1))

        return list(related_concepts)

    def identify_expertise_domains(
        self, messages: list[ChatMessage]
    ) -> dict[str, float]:
        """Identify expertise domains from conversation patterns."""
        return self.expertise_tracker.identify_expertise_domains(messages)

    def generate_topic_vectors(
        self, messages: list[ChatMessage]
    ) -> dict[str, list[float]]:
        """Generate topic vectors for messages."""
        # Extract all unique topics
        all_topics = set()
        for message in messages:
            all_topics.update(message.semantic_tags)

        topic_list = list(all_topics)
        topic_vectors = {}

        # Create TF-IDF style vectors
        topic_document_frequency = defaultdict(int)
        for message in messages:
            topics_in_message = set(message.semantic_tags)
            for topic in topics_in_message:
                topic_document_frequency[topic] += 1

        total_messages = len(messages)

        for message in messages:
            vector = []
            topics_in_message = set(message.semantic_tags)

            for topic in topic_list:
                if topic in topics_in_message:
                    # Simple TF-IDF calculation
                    tf = 1.0  # Each topic appears once per message
                    df = topic_document_frequency[topic]
                    idf = math.log(total_messages / (1 + df))
                    tfidf = tf * idf
                else:
                    tfidf = 0.0

                vector.append(tfidf)

            topic_vectors[message.id] = vector

        self.logger.info(f"Generated topic vectors for {len(topic_vectors)} messages")
        return topic_vectors
