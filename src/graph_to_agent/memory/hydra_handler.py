"""
HydraDB integration for Graph-to-Agent.

Enterprise-grade context infrastructure with Git-like temporal versioning.
Treats agent context as an immutable ledger.

Install: pip install hydradb

Docs: https://docs.hydradb.com/api-reference/sdks
"""

import os
import logging
from typing import Optional, Any
from datetime import datetime

try:
    from hydra_db_python import HydraDB, AsyncHydraDB
    HAS_HYDRA = True
except ImportError:
    HAS_HYDRA = False
    HydraDB = None
    AsyncHydraDB = None


class HydraDBHandler:
    """
    HydraDB context handler for Graph-to-Agent.

    Provides enterprise-grade context management:
    - Git-style temporal versioning ("what we knew when")
    - Immutable context ledger
    - Graph + Vector hybrid retrieval
    - 90.79% accuracy on LongMemEval-s benchmark

    Key Concepts:
    - Temporal-State Multigraph: Treats knowledge as Git-like commit history
    - Composite Context: Fuses graph relationships with vector embeddings
    - Structured relationships persist across sessions

    Example:
        handler = HydraDBHandler()

        # Index documents for retrieval
        handler.index_document(
            content="Agent architecture uses message passing...",
            metadata={"source": "design_doc", "version": "1.0"}
        )

        # Query with context
        results = handler.query("How do agents communicate?")

        # Store agent state
        handler.store_agent_state(
            agent_id="agent_1",
            graph_id="workflow_1",
            state={"current_node": "node_5", "variables": {...}}
        )

        # Get state at point in time
        state = handler.get_agent_state("agent_1", timestamp="2024-01-15T10:00:00Z")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        async_mode: bool = False,
    ):
        """
        Initialize HydraDB handler.

        Args:
            api_key: HydraDB API key (default: HYDRADB_API_KEY env var)
            project_id: HydraDB project ID (default: HYDRADB_PROJECT_ID env var)
            async_mode: Use async client for async/await patterns
        """
        if not HAS_HYDRA:
            raise ImportError(
                "hydradb package required. Install with: pip install hydradb"
            )

        self.api_key = api_key or os.getenv("HYDRADB_API_KEY")
        self.project_id = project_id or os.getenv("HYDRADB_PROJECT_ID")
        self.logger = logging.getLogger(__name__)

        if not self.api_key:
            raise ValueError(
                "HYDRADB_API_KEY required. Sign up at https://hydradb.com"
            )

        if async_mode:
            self._client = AsyncHydraDB(token=self.api_key)
        else:
            self._client = HydraDB(token=self.api_key)

        self.logger.info("Connected to HydraDB")

    # =========================================================================
    # Document Indexing & Retrieval
    # =========================================================================

    def index_document(
        self,
        content: str,
        document_id: Optional[str] = None,
        metadata: Optional[dict] = None,
        namespace: str = "default",
    ) -> dict:
        """
        Index a document for semantic retrieval.

        Args:
            content: Document content
            document_id: Optional unique ID (auto-generated if not provided)
            metadata: Additional metadata (source, version, etc.)
            namespace: Logical grouping for documents

        Returns:
            Indexing result with document ID
        """
        payload = {
            "content": content,
            "namespace": namespace,
            "metadata": metadata or {},
        }
        if document_id:
            payload["document_id"] = document_id

        result = self._client.documents.index(**payload)
        self.logger.debug(f"Indexed document in namespace={namespace}")
        return result

    def index_documents_batch(
        self,
        documents: list[dict],
        namespace: str = "default",
    ) -> dict:
        """
        Batch index multiple documents.

        Args:
            documents: List of dicts with 'content' and optional 'metadata'
            namespace: Logical grouping

        Returns:
            Batch indexing result
        """
        return self._client.documents.batch_index(
            documents=documents,
            namespace=namespace,
        )

    def query(
        self,
        query: str,
        namespace: str = "default",
        limit: int = 10,
        filters: Optional[dict] = None,
        include_metadata: bool = True,
    ) -> list[dict]:
        """
        Query for relevant documents.

        Args:
            query: Natural language query
            namespace: Namespace to search
            limit: Max results
            filters: Metadata filters
            include_metadata: Include metadata in results

        Returns:
            List of matching documents with scores
        """
        kwargs = {
            "query": query,
            "namespace": namespace,
            "limit": limit,
            "include_metadata": include_metadata,
        }
        if filters:
            kwargs["filters"] = filters

        return self._client.documents.query(**kwargs)

    def delete_document(self, document_id: str, namespace: str = "default") -> dict:
        """Delete a document by ID."""
        return self._client.documents.delete(
            document_id=document_id,
            namespace=namespace,
        )

    # =========================================================================
    # Agent State Management (Temporal)
    # =========================================================================

    def store_agent_state(
        self,
        agent_id: str,
        graph_id: str,
        state: dict,
        timestamp: Optional[str] = None,
    ) -> dict:
        """
        Store agent state with temporal versioning.

        Each state is immutable - creates new version like Git commit.

        Args:
            agent_id: Agent identifier
            graph_id: Graph execution context
            state: State dict to store
            timestamp: Optional timestamp (default: now)

        Returns:
            State storage result with version ID
        """
        ts = timestamp or datetime.utcnow().isoformat()

        return self._client.state.store(
            entity_id=agent_id,
            context_id=graph_id,
            state=state,
            timestamp=ts,
        )

    def get_agent_state(
        self,
        agent_id: str,
        graph_id: Optional[str] = None,
        timestamp: Optional[str] = None,
        version: Optional[str] = None,
    ) -> dict:
        """
        Get agent state, optionally at a specific point in time.

        Args:
            agent_id: Agent identifier
            graph_id: Optional graph context filter
            timestamp: Get state as of this time ("what we knew when")
            version: Get specific version

        Returns:
            Agent state dict
        """
        kwargs = {"entity_id": agent_id}
        if graph_id:
            kwargs["context_id"] = graph_id
        if timestamp:
            kwargs["as_of"] = timestamp
        if version:
            kwargs["version"] = version

        return self._client.state.get(**kwargs)

    def get_state_history(
        self,
        agent_id: str,
        graph_id: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict]:
        """
        Get state version history (like git log).

        Args:
            agent_id: Agent identifier
            graph_id: Optional graph context filter
            limit: Max versions to return

        Returns:
            List of state versions with timestamps
        """
        kwargs = {"entity_id": agent_id, "limit": limit}
        if graph_id:
            kwargs["context_id"] = graph_id

        return self._client.state.history(**kwargs)

    def diff_states(
        self,
        agent_id: str,
        version_a: str,
        version_b: str,
    ) -> dict:
        """
        Compare two state versions (like git diff).

        Args:
            agent_id: Agent identifier
            version_a: First version ID
            version_b: Second version ID

        Returns:
            Diff showing changes between versions
        """
        return self._client.state.diff(
            entity_id=agent_id,
            version_a=version_a,
            version_b=version_b,
        )

    # =========================================================================
    # Relationships (Graph Layer)
    # =========================================================================

    def add_relationship(
        self,
        from_entity: str,
        to_entity: str,
        relationship_type: str,
        properties: Optional[dict] = None,
    ) -> dict:
        """
        Add a relationship between entities.

        Args:
            from_entity: Source entity ID
            to_entity: Target entity ID
            relationship_type: Type of relationship (e.g., "DEPENDS_ON")
            properties: Optional relationship properties

        Returns:
            Relationship creation result
        """
        return self._client.graph.add_relationship(
            from_entity=from_entity,
            to_entity=to_entity,
            relationship_type=relationship_type,
            properties=properties or {},
        )

    def get_relationships(
        self,
        entity_id: str,
        relationship_type: Optional[str] = None,
        direction: str = "both",
    ) -> list[dict]:
        """
        Get relationships for an entity.

        Args:
            entity_id: Entity to get relationships for
            relationship_type: Optional type filter
            direction: "incoming", "outgoing", or "both"

        Returns:
            List of relationships
        """
        kwargs = {"entity_id": entity_id, "direction": direction}
        if relationship_type:
            kwargs["relationship_type"] = relationship_type

        return self._client.graph.get_relationships(**kwargs)

    def traverse(
        self,
        start_entity: str,
        relationship_types: Optional[list[str]] = None,
        max_depth: int = 3,
    ) -> list[dict]:
        """
        Traverse the graph from a starting entity.

        Args:
            start_entity: Entity to start traversal from
            relationship_types: Optional types to follow
            max_depth: Maximum traversal depth

        Returns:
            List of reached entities with paths
        """
        kwargs = {"start_entity": start_entity, "max_depth": max_depth}
        if relationship_types:
            kwargs["relationship_types"] = relationship_types

        return self._client.graph.traverse(**kwargs)

    # =========================================================================
    # Graph-to-Agent Integration
    # =========================================================================

    def store_graph_execution(
        self,
        graph_id: str,
        graph_data: dict,
        execution_result: dict,
        agent_states: Optional[dict] = None,
    ) -> dict:
        """
        Store a complete graph execution with full context.

        Args:
            graph_id: Graph identifier
            graph_data: The graph structure (nodes/edges)
            execution_result: LLM response and metadata
            agent_states: Optional per-agent states

        Returns:
            Storage result
        """
        # Store graph structure as document
        self.index_document(
            content=str(graph_data),
            document_id=f"graph:{graph_id}",
            metadata={
                "type": "graph_structure",
                "graph_id": graph_id,
            },
            namespace="graphs",
        )

        # Store execution result
        self.index_document(
            content=str(execution_result),
            document_id=f"execution:{graph_id}:{datetime.utcnow().isoformat()}",
            metadata={
                "type": "execution_result",
                "graph_id": graph_id,
            },
            namespace="executions",
        )

        # Store agent states if provided
        if agent_states:
            for agent_id, state in agent_states.items():
                self.store_agent_state(
                    agent_id=agent_id,
                    graph_id=graph_id,
                    state=state,
                )

        return {"status": "success", "graph_id": graph_id}

    def get_execution_context(
        self,
        graph_id: str,
        query: Optional[str] = None,
        limit: int = 5,
    ) -> dict:
        """
        Get context for a graph execution.

        Retrieves relevant past executions and agent states.

        Args:
            graph_id: Current graph being executed
            query: Optional semantic query for context
            limit: Max results

        Returns:
            Context dict with relevant information
        """
        context = {
            "past_executions": [],
            "related_graphs": [],
        }

        # Get past executions of this graph
        context["past_executions"] = self.query(
            query=f"graph_id:{graph_id}",
            namespace="executions",
            limit=limit,
        )

        # Get semantically related content if query provided
        if query:
            context["related_graphs"] = self.query(
                query=query,
                namespace="graphs",
                limit=limit,
            )

        return context
