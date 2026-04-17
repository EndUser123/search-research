"""Graph abstractions for knowledge systems.

This module provides base classes for graph structures used in
KG (Knowledge Graph), CHS (Chat History System), and other
graph-based knowledge representations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Literal, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

T = TypeVar("T")


@dataclass(frozen=True)
class EntityId:
    """Type-safe identifier for graph entities.

    Attributes:
        value: The underlying string identifier
        kind: Optional entity type/kind for namespacing

    """

    value: str
    kind: str | None = None

    def __post_init__(self) -> None:
        """Validate entity ID."""
        if not self.value or not self.value.strip():
            msg = "EntityId.value cannot be empty"
            raise ValueError(msg)

    def __str__(self) -> str:
        """String representation with optional kind prefix."""
        if self.kind:
            return f"{self.kind}:{self.value}"
        return self.value

    @classmethod
    def parse(cls, value: str) -> EntityId:
        """Parse entity ID from string with optional kind prefix.

        Args:
            value: String representation like "kind:value" or "value"

        Returns:
            Parsed EntityId instance

        """
        if ":" in value:
            kind, val = value.split(":", 1)
            return cls(value=val, kind=kind)
        return cls(value=value)


@dataclass(frozen=True)
class Entity:
    """A node in a knowledge graph representing an entity.

    Entities can be code elements, concepts, documents, people,
    or any other domain object represented in the graph.

    Attributes:
        id: Unique entity identifier
        label: Human-readable name/label
        entity_type: Type/class of the entity
        properties: Additional properties as key-value pairs
        created_at: When this entity was added to the graph

    """

    id: EntityId
    label: str
    entity_type: str
    properties: dict[str, str | int | float | bool] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def degree(self) -> int:
        """Get total number of edges (in + out)."""
        raise NotImplementedError("Use Graph.degree(entity) instead")

    def with_property(
        self,
        key: str,
        value: str | int | float | bool,
    ) -> Entity:
        """Return new entity with additional/updated property."""
        new_props = {**self.properties, key: value}
        return Entity(
            id=self.id,
            label=self.label,
            entity_type=self.entity_type,
            properties=new_props,
            created_at=self.created_at,
        )


@dataclass(frozen=True)
class Relation:
    """A directed edge in a knowledge graph.

    Represents a relationship between two entities with optional
    weight and metadata.

    Attributes:
        id: Unique relation identifier (optional, auto-generated if None)
        source: Source entity (tail of the edge)
        target: Target entity (head of the edge)
        relation_type: Type of relationship (e.g., "calls", "imports", "related_to")
        weight: Optional weight for scoring/ranking (0-1)
        properties: Additional properties as key-value pairs
        created_at: When this relation was added to the graph

    """

    source: EntityId
    target: EntityId
    relation_type: str
    id: str | None = None
    weight: float = 1.0
    properties: dict[str, str | int | float | bool] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """Validate relation fields."""
        if not self.relation_type or not self.relation_type.strip():
            msg = "relation_type cannot be empty"
            raise ValueError(msg)
        if not 0.0 <= self.weight <= 1.0:
            msg = f"weight must be in [0, 1], got {self.weight}"
            raise ValueError(msg)

    @property
    def key(self) -> str:
        """Get unique key for this relation (source:type:target)."""
        return f"{self.source}:{self.relation_type}:{self.target}"

    def reverse(self) -> Relation:
        """Return new relation with swapped source and target."""
        return Relation(
            source=self.target,
            target=self.source,
            relation_type=self.relation_type,
            id=self.id,
            weight=self.weight,
            properties=self.properties,
            created_at=self.created_at,
        )


class Graph(ABC):
    """Abstract base class for graph data structures.

    Provides common interface for KG, CHS hypergraph, and other
    graph-based knowledge representations.
    """

    def __init__(self, directed: bool = True) -> None:
        """Initialize graph structure."""
        self.directed = directed
        self._entity_count = 0
        self._relation_count = 0

    @abstractmethod
    def add_entity(self, entity: Entity) -> bool:
        """Add an entity to the graph.

        Args:
            entity: Entity to add

        Returns:
            True if added, False if already exists

        """
        ...

    @abstractmethod
    def add_relation(self, relation: Relation) -> bool:
        """Add a relation to the graph.

        Args:
            relation: Relation to add

        Returns:
            True if added, False if already exists

        """
        ...

    @abstractmethod
    def get_entity(self, entity_id: EntityId) -> Entity | None:
        """Retrieve an entity by ID.

        Args:
            entity_id: Entity identifier

        Returns:
            Entity or None if not found

        """
        ...

    @abstractmethod
    def get_relation(
        self, source: EntityId, target: EntityId, relation_type: str
    ) -> Relation | None:
        """Retrieve a specific relation.

        Args:
            source: Source entity ID
            target: Target entity ID
            relation_type: Type of relation

        Returns:
            Relation or None if not found

        """
        ...

    @abstractmethod
    def neighbors(
        self,
        entity_id: EntityId,
        relation_type: str | None = None,
    ) -> Iterable[tuple[EntityId, Relation]]:
        """Get neighboring entities connected by relations.

        Args:
            entity_id: Starting entity ID
            relation_type: Optional filter by relation type

        Yields:
            Tuples of (neighbor_id, relation) for each neighbor

        """
        ...

    @abstractmethod
    def traverse(
        self,
        start: EntityId,
        direction: Literal["out", "in", "both"] = "out",
        max_depth: int = 3,
        visitor: Callable[[EntityId, int], bool] | None = None,
    ) -> Iterable[EntityId]:
        """Traverse graph from starting entity.

        Args:
            start: Starting entity ID
            direction: Traversal direction ("out", "in", or "both")
            max_depth: Maximum traversal depth
            visitor: Optional callback returning True to stop traversal

        Yields:
            Entity IDs encountered during traversal

        """
        ...

    @abstractmethod
    def find_paths(
        self,
        source: EntityId,
        target: EntityId,
        max_length: int = 5,
    ) -> Iterable[list[EntityId]]:
        """Find all paths between two entities.

        Args:
            source: Source entity ID
            target: Target entity ID
            max_length: Maximum path length (number of edges)

        Yields:
            Lists of entity IDs representing paths

        """
        ...

    @abstractmethod
    def query(
        self,
        entity_type: str | None = None,
        relation_type: str | None = None,
        properties: dict[str, str | int | float | bool] | None = None,
    ) -> Iterable[Entity]:
        """Query graph for entities matching criteria.

        Args:
            entity_type: Optional entity type filter
            relation_type: Optional relation type filter
            properties: Optional property filters

        Yields:
            Matching entities

        """
        ...

    @property
    def entity_count(self) -> int:
        """Get total number of entities in the graph."""
        return self._entity_count

    @property
    def relation_count(self) -> int:
        """Get total number of relations in the graph."""
        return self._relation_count

    @abstractmethod
    def degree(self, entity_id: EntityId, direction: Literal["in", "out", "both"] = "both") -> int:
        """Get degree (number of edges) for an entity.

        Args:
            entity_id: Entity identifier
            direction: Count direction ("in", "out", or "both")

        Returns:
            Number of edges

        """
        ...

    def clear(self) -> None:
        """Clear all entities and relations from the graph."""
        raise NotImplementedError("Subclasses must implement clear()")


class MutableGraph(Graph):
    """Mutable graph implementation with in-memory storage.

    Provides a simple graph implementation suitable for small to
    medium-sized graphs (up to ~100K entities).
    """

    def __init__(self, directed: bool = True) -> None:
        """Initialize mutable graph."""
        super().__init__(directed)
        self._entities: dict[EntityId, Entity] = {}
        self._adjacency: dict[EntityId, dict[EntityId, list[Relation]]] = {}

    def add_entity(self, entity: Entity) -> bool:
        """Add entity to graph."""
        if entity.id in self._entities:
            return False
        self._entities[entity.id] = entity
        self._entity_count += 1
        return True

    def add_relation(self, relation: Relation) -> bool:
        """Add relation to graph."""
        # Ensure entities exist
        if relation.source not in self._entities:
            return False
        if relation.target not in self._entities:
            return False

        # Initialize adjacency lists
        if relation.source not in self._adjacency:
            self._adjacency[relation.source] = {}
        if relation.target not in self._adjacency:
            self._adjacency[relation.target] = {}

        # Check if relation already exists
        if relation.target in self._adjacency[relation.source]:
            for existing in self._adjacency[relation.source][relation.target]:
                if existing.relation_type == relation.relation_type:
                    return False

        # Add forward relation
        self._adjacency[relation.source].setdefault(relation.target, []).append(relation)

        # Add reverse relation if not directed
        if not self.directed:
            self._adjacency[relation.target].setdefault(relation.source, []).append(
                relation.reverse(),
            )

        self._relation_count += 1
        return True

    def get_entity(self, entity_id: EntityId) -> Entity | None:
        """Get entity by ID."""
        return self._entities.get(entity_id)

    def get_relation(
        self, source: EntityId, target: EntityId, relation_type: str
    ) -> Relation | None:
        """Get specific relation."""
        if source not in self._adjacency:
            return None
        if target not in self._adjacency[source]:
            return None
        for rel in self._adjacency[source][target]:
            if rel.relation_type == relation_type:
                return rel
        return None

    def neighbors(
        self,
        entity_id: EntityId,
        relation_type: str | None = None,
    ) -> Iterator[tuple[EntityId, Relation]]:
        """Get neighboring entities."""
        if entity_id not in self._adjacency:
            return
        for target, relations in self._adjacency[entity_id].items():
            for rel in relations:
                if relation_type is None or rel.relation_type == relation_type:
                    yield target, rel

    def traverse(
        self,
        start: EntityId,
        direction: Literal["out", "in", "both"] = "out",
        max_depth: int = 3,
        visitor: Callable[[EntityId, int], bool] | None = None,
    ) -> Iterator[EntityId]:
        """BFS traversal from start entity."""
        from collections import deque

        visited: set[EntityId] = set()
        queue: deque[tuple[EntityId, int]] = deque([(start, 0)])

        while queue:
            current, depth = queue.popleft()
            if current in visited or depth > max_depth:
                continue
            visited.add(current)
            yield current

            if visitor and visitor(current, depth):
                break

            for neighbor, _ in self.neighbors(current):
                if neighbor not in visited:
                    queue.append((neighbor, depth + 1))

    def find_paths(
        self,
        source: EntityId,
        target: EntityId,
        max_length: int = 5,
    ) -> Iterator[list[EntityId]]:
        """DFS path finding between entities."""
        visited: set[EntityId] = set()
        path: list[EntityId] = []

        def dfs(current: EntityId) -> None:
            visited.add(current)
            path.append(current)

            if current == target:
                yield list(path)
            elif len(path) <= max_length:
                for neighbor, _ in self.neighbors(current):
                    if neighbor not in visited:
                        yield from dfs(neighbor)

            path.pop()
            visited.remove(current)

        yield from dfs(source)

    def query(
        self,
        entity_type: str | None = None,
        relation_type: str | None = None,
        properties: dict[str, str | int | float | bool] | None = None,
    ) -> Iterator[Entity]:
        """Query entities by type, relations, or properties."""
        for entity in self._entities.values():
            # Type filter
            if entity_type and entity.entity_type != entity_type:
                continue
            # Property filter
            if properties:
                if not all(
                    k in entity.properties and v == entity.properties[k]
                    for k, v in properties.items()
                ):
                    continue
            # Relation filter (check if entity has any matching relations)
            if relation_type:
                has_relation = any(
                    rel.relation_type == relation_type for _, rel in self.neighbors(entity.id)
                )
                if not has_relation:
                    continue
            yield entity

    def degree(self, entity_id: EntityId, direction: Literal["in", "out", "both"] = "both") -> int:
        """Get entity degree."""
        if entity_id not in self._adjacency:
            return 0

        count = 0
        if direction in ("out", "both"):
            count += sum(len(rels) for rels in self._adjacency[entity_id].values())
        if direction in ("in", "both"):
            for others in self._adjacency.values():
                count += len(others.get(entity_id, []))
        return count

    def clear(self) -> None:
        """Clear all entities and relations."""
        self._entities.clear()
        self._adjacency.clear()
        self._entity_count = 0
        self._relation_count = 0
