"""Graph-of-Thought (GoT) analysis for search result enhancement.

Extracts nodes, analyzes edges, and clusters search results for better organization.
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class GotNode:
    """A node extracted from search results."""
    text: str
    node_type: str  # keyword, entity, theme, constraint, idea, risk
    source_result_id: str
    confidence: float = 0.5


@dataclass
class GotEdge:
    """An edge relationship between two nodes or results."""
    from_id: str
    to_id: str
    edge_type: str  # supports, contradicts, related, unrelated
    strength: float
    reason: str = ''


@dataclass
class GotCluster:
    """A cluster of related search results."""
    cluster_id: str
    label: str
    result_ids: list[str]
    nodes: list[GotNode]
    confidence: float


class GotAnalyzer:
    """Graph-of-Thought analyzer for search results.

    Extracts nodes, analyzes edges, detects cycles, and clusters results.
    """

    CONSTRAINT_PATTERNS = [
        r'\bmust\b', r'\bshould\b', r'\brequired\b', r'\bneed\b',
        r'\bonly\b', r'\bnever\b', r'\balways\b'
    ]

    IDEA_PATTERNS = [
        r'\bcan\b', r'\bcould\b', r'\bmight\b', r'\bmay\b',
        r'\bsuggest\b', r'\brecommend\b', r'\bpropose\b'
    ]

    RISK_PATTERNS = [
        r'\brisk\b', r'\bdanger\b', r'\bwarning\b', r'\bcaution\b',
        r'\bproblem\b', r'\bissue\b', r'\berror\b', r'\bfail\b'
    ]

    def __init__(
        self,
        min_cluster_size: int = 2,
        min_edge_strength: float = 0.3,
    ):
        self.min_cluster_size = min_cluster_size
        self.min_edge_strength = min_edge_strength
        self.nodes: dict[str, GotNode] = {}
        self.edges: list[GotEdge] = []
        self.clusters: list[GotCluster] = []

    def extract_nodes_from_result(
        self,
        result: Any,
        result_id: str,
    ) -> list[GotNode]:
        """Extract nodes from a single search result."""
        nodes = []

        text = ''
        if hasattr(result, 'content') and result.content:
            text = result.content.lower()
        if hasattr(result, 'title') and result.title:
            text += ' ' + result.title.lower()

        if not text.strip():
            return nodes

        # Extract keywords
        keywords = re.findall(r'\b[a-z][a-z]+ [a-z][a-z]+\b', text)
        for keyword in set(keywords[:10]):
            nodes.append(GotNode(
                text=keyword,
                node_type='keyword',
                source_result_id=result_id,
                confidence=0.6
            ))

        # Extract constraints
        for pattern in self.CONSTRAINT_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end].strip()
                nodes.append(GotNode(
                    text=context[:50],
                    node_type='constraint',
                    source_result_id=result_id,
                    confidence=0.7
                ))

        # Extract ideas
        for pattern in self.IDEA_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end].strip()
                nodes.append(GotNode(
                    text=context[:50],
                    node_type='idea',
                    source_result_id=result_id,
                    confidence=0.6
                ))

        # Extract risks
        for pattern in self.RISK_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                start = max(0, match.start() - 30)
                end = min(len(text), match.end() + 30)
                context = text[start:end].strip()
                nodes.append(GotNode(
                    text=context[:50],
                    node_type='risk',
                    source_result_id=result_id,
                    confidence=0.7
                ))

        return nodes


    def analyze_results(
        self,
        results: list[Any],
    ) -> dict[str, Any]:
        """Analyze search results with GoT."""
        if not results:
            return {
                'nodes': [],
                'edges': [],
                'clusters': [],
                'cycles': [],
                'summary': 'No results to analyze'
            }

        # Step 1: Extract nodes
        self.nodes = {}
        result_to_nodes = defaultdict(list)

        for i, result in enumerate(results):
            result_id = f'result_{i}'
            nodes = self.extract_nodes_from_result(result, result_id)

            for node in nodes:
                node_key = f'{result_id}_{node.text}_{node.node_type}'
                self.nodes[node_key] = node
                result_to_nodes[result_id].append(node_key)

        # Step 2: Analyze edges
        self.edges = self._analyze_edges(results, result_to_nodes)

        # Step 3: Cluster results
        self.clusters = self._cluster_results(results, result_to_nodes)

        # Step 4: Detect cycles
        cycles = self._detect_cycles()

        # Step 5: Generate summary
        summary = self._generate_summary(results, len(self.nodes), len(self.edges), len(self.clusters))

        return {
            'nodes': list(self.nodes.values()),
            'edges': self.edges,
            'clusters': self.clusters,
            'cycles': cycles,
            'summary': summary,
        }

    def _analyze_edges(
        self,
        results: list[Any],
        result_to_nodes: dict[str, list[str]],
    ) -> list[GotEdge]:
        """Analyze relationships between results."""
        edges = []

        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                result_i = f'result_{i}'
                result_j = f'result_{j}'

                nodes_i = set(result_to_nodes.get(result_i, []))
                nodes_j = set(result_to_nodes.get(result_j, []))

                if not nodes_i or not nodes_j:
                    continue

                # Calculate Jaccard similarity
                intersection = len(nodes_i & nodes_j)
                union = len(nodes_i | nodes_j)
                similarity = intersection / union if union > 0 else 0

                # Determine edge type
                if similarity >= 0.3:
                    edge_type = 'supports'
                    strength = similarity
                    reason = f'Shared {intersection} nodes ({similarity:.1%} similarity)'
                elif similarity >= 0.1:
                    edge_type = 'related'
                    strength = similarity
                    reason = f'Related via {intersection} nodes'
                else:
                    if self._are_contradictory(results[i], results[j]):
                        edge_type = 'contradicts'
                        strength = 0.5
                        reason = 'Potential contradiction detected'
                    else:
                        edge_type = 'unrelated'
                        strength = 0.0
                        reason = 'No clear relationship'

                if strength >= self.min_edge_strength or edge_type == 'contradicts':
                    edges.append(GotEdge(
                        from_id=result_i,
                        to_id=result_j,
                        edge_type=edge_type,
                        strength=strength,
                        reason=reason
                    ))

        return edges


    def _are_contradictory(self, result1: Any, result2: Any) -> bool:
        """Check if two results contradict each other."""
        text1 = ''
        text2 = ''

        if hasattr(result1, 'content') and result1.content:
            text1 = result1.content.lower()
        if hasattr(result2, 'content') and result2.content:
            text2 = result2.content.lower()

        negation_words = ['not', 'never', 'no', 'none', 'nothing', 'neither', 'nor']

        has_negation1 = any(word in text1 for word in negation_words)
        has_negation2 = any(word in text2 for word in negation_words)

        if has_negation1 != has_negation2:
            words1 = set(re.findall(r'\b[a-z]{4,}\b', text1))
            words2 = set(re.findall(r'\b[a-z]{4,}\b', text2))

            overlap = len(words1 & words2)
            if overlap > 3:
                return True

        return False

    def _cluster_results(
        self,
        results: list[Any],
        result_to_nodes: dict[str, list[str]],
    ) -> list[GotCluster]:
        """Cluster related results together."""
        if len(results) < self.min_cluster_size:
            return []

        # Build adjacency list
        adjacency = defaultdict(set)
        for edge in self.edges:
            if edge.edge_type in ('supports', 'related'):
                adjacency[edge.from_id].add(edge.to_id)
                adjacency[edge.to_id].add(edge.from_id)

        # Find connected components
        visited = set()
        clusters = []

        for result_id in adjacency.keys():
            if result_id in visited:
                continue

            # BFS to find connected component
            component = set()
            queue = [result_id]

            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue

                visited.add(current)
                component.add(current)
                queue.extend(adjacency[current] - visited)

            if len(component) >= self.min_cluster_size:
                # Get common nodes
                node_keys = set()
                for rid in component:
                    node_keys.update(result_to_nodes.get(rid, []))

                common_nodes = [
                    self.nodes[key] for key in node_keys
                    if key in self.nodes
                ]

                # Generate label
                node_texts = [n.text for n in common_nodes]
                label = self._generate_cluster_label(node_texts, results, component)

                # Calculate confidence
                cluster_edges = [
                    e for e in self.edges
                    if e.from_id in component and e.to_id in component
                ]
                confidence = (
                    sum(e.strength for e in cluster_edges) / len(cluster_edges)
                    if cluster_edges else 0.5
                )

                clusters.append(GotCluster(
                    cluster_id=f'cluster_{len(clusters)}',
                    label=label,
                    result_ids=list(component),
                    nodes=common_nodes,
                    confidence=confidence
                ))

        return sorted(clusters, key=lambda c: len(c.result_ids), reverse=True)


    def _generate_cluster_label(
        self,
        node_texts: list[str],
        results: list[Any],
        result_ids: set[str],
    ) -> str:
        """Generate cluster label from nodes."""
        from collections import Counter

        node_freq = Counter(node_texts)
        top_nodes = [n for n, _ in node_freq.most_common(3)]

        if not top_nodes:
            # Fallback: use result titles
            titles = []
            for rid in result_ids:
                idx = int(rid.split('_')[1])
                if idx < len(results) and hasattr(results[idx], 'title'):
                    titles.append(results[idx].title)

            if titles:
                all_words = ' '.join(titles).lower()
                keywords = re.findall(r'\b[a-z]{4,}\b', all_words)
                keyword_freq = Counter(keywords)
                top_keywords = [k for k, _ in keyword_freq.most_common(3)]
                return ' + '.join(top_keywords)

        return ' + '.join(top_nodes[:3])

    def _detect_cycles(self) -> list[list[str]]:
        """Detect cycles in edge graph."""
        if not self.edges:
            return []

        # Build adjacency list
        adjacency = defaultdict(set)
        for edge in self.edges:
            if edge.edge_type in ('supports', 'related'):
                adjacency[edge.from_id].add(edge.to_id)

        cycles = []
        visited = set()
        rec_stack = set()
        path = []

        def dfs(node: str):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in adjacency.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)

            path.pop()
            rec_stack.remove(node)

        for node in adjacency:
            if node not in visited:
                dfs(node)

        return cycles

    def _generate_summary(
        self,
        results: list[Any],
        num_nodes: int,
        num_edges: int,
        num_clusters: int,
    ) -> str:
        """Generate GoT analysis summary."""
        parts = []

        parts.append(f'Analyzed {len(results)} results')

        if num_nodes > 0:
            parts.append(f'extracted {num_nodes} nodes')

        if num_edges > 0:
            strong_edges = sum(1 for e in self.edges if e.strength >= 0.5)
            parts.append(f'found {num_edges} edges ({strong_edges} strong)')

        if num_clusters > 0:
            avg_cluster_size = sum(len(c.result_ids) for c in self.clusters) / num_clusters
            parts.append(f'created {num_clusters} clusters (avg {avg_cluster_size:.1f} results)')

        if not parts:
            return 'GoT analysis complete - no significant patterns found'

        return 'GoT: ' + ', '.join(parts) + '.'


    def format_results_with_got(
        self,
        results: list[Any],
        got_analysis: dict[str, Any],
    ) -> str:
        """Format search results with GoT metadata."""
        from collections import defaultdict

        output = []

        # Add summary
        summary = got_analysis.get('summary')
        if summary:
            output.append(f"**{summary}**")
            output.append("")

        # Show clusters
        clusters = got_analysis.get('clusters', [])
        if clusters:
            output.append('## Result Clusters')
            output.append('')

            for cluster in clusters[:3]:
                output.append(f"### {cluster.label}")
                output.append(f"Cluster: {cluster.cluster_id} | Confidence: {cluster.confidence:.1%}")
                output.append(f"Results: {len(cluster.result_ids)} items")

                # Show node types
                node_types = defaultdict(int)
                for node in cluster.nodes[:5]:
                    node_types[node.node_type] += 1

                if node_types:
                    node_summary = ', '.join(f'{count} {ntype}' for ntype, count in node_types.items())
                    output.append(f"Nodes: {node_summary}")

                output.append("")

        # Show cycles
        cycles = got_analysis.get('cycles', [])
        if cycles:
            output.append('## Detected Cycles')
            output.append(f"Found {len(cycles)} circular relationship(s):")
            output.append('')

            for i, cycle in enumerate(cycles[:3], 1):
                cycle_str = ' → '.join(cycle)
                output.append(f"{i}. {cycle_str}")

            output.append("")

        # Show edge summary
        edges = got_analysis.get('edges', [])
        if edges:
            edge_types = defaultdict(int)
            for edge in edges:
                edge_types[edge.edge_type] += 1

            output.append('## Edge Relationships')
            for edge_type, count in sorted(edge_types.items()):
                output.append(f"- {edge_type}: {count}")

            output.append("")

        return '\n'.join(output)
