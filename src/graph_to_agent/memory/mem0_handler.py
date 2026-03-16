"""
Mem0 integration for Graph-to-Agent.

Adds persistent memory layer to agents - remember user preferences,
learn over time, and maintain context across sessions.

Install: pip install mem0ai

Docs: https://docs.mem0.ai/open-source/python-quickstart
"""

import os
import logging
from typing import Optional, Any
from datetime import datetime

try:
    from mem0 import Memory, MemoryClient
    HAS_MEM0 = True
except ImportError:
    HAS_MEM0 = False
    Memory = None
    MemoryClient = None


class Mem0Handler:
    """
    Mem0 memory handler for Graph-to-Agent.

    Provides persistent memory for agents:
    - Long-term memory (across sessions)
    - Semantic memory (concepts/facts)
    - Episodic memory (events/interactions)

    Benefits:
    - +26% accuracy over OpenAI Memory (LOCOMO benchmark)
    - 91% faster responses (selective retrieval)
    - 90% lower token usage

    Example:
        handler = Mem0Handler()

        # Store conversation memory
        handler.add_memory(
            messages=[
                {"role": "user", "content": "I prefer Python over JavaScript"},
                {"role": "assistant", "content": "Noted! I'll recommend Python solutions."}
            ],
            user_id="user_123",
            agent_id="coding_assistant"
        )

        # Retrieve relevant memories
        memories = handler.search("programming preferences", user_id="user_123")

        # Get all memories for a user
        all_memories = handler.get_all(user_id="user_123")
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        use_managed: bool = False,
        config: Optional[dict] = None,
    ):
        """
        Initialize Mem0 handler.

        Args:
            api_key: Mem0 API key (for managed platform, MEM0_API_KEY env var)
            use_managed: Use managed Mem0 platform (app.mem0.ai) vs local
            config: Custom configuration dict for local Memory()

        Local defaults:
        - LLM: OpenAI gpt-4.1-nano for fact extraction
        - Embeddings: OpenAI text-embedding-3-small (1536 dims)
        - Vector store: Qdrant on-disk at /tmp/qdrant
        """
        if not HAS_MEM0:
            raise ImportError(
                "mem0ai package required. Install with: pip install mem0ai"
            )

        self.logger = logging.getLogger(__name__)
        self.use_managed = use_managed

        if use_managed:
            self.api_key = api_key or os.getenv("MEM0_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "MEM0_API_KEY required for managed platform. "
                    "Sign up at https://app.mem0.ai"
                )
            self._client = MemoryClient(api_key=self.api_key)
            self.logger.info("Connected to Mem0 managed platform")
        else:
            # Local memory instance
            self._client = Memory(config=config) if config else Memory()
            self.logger.info("Initialized local Mem0 memory")

    # =========================================================================
    # Core Memory Operations
    # =========================================================================

    def add_memory(
        self,
        messages: list[dict],
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Add memories from a conversation.

        Args:
            messages: List of message dicts with 'role' and 'content'
            user_id: User identifier for personalization
            agent_id: Agent identifier (for agent-specific memories)
            run_id: Execution run identifier
            metadata: Additional metadata to store

        Returns:
            Dict with added memory info
        """
        kwargs = {}
        if user_id:
            kwargs["user_id"] = user_id
        if agent_id:
            kwargs["agent_id"] = agent_id
        if run_id:
            kwargs["run_id"] = run_id
        if metadata:
            kwargs["metadata"] = metadata

        result = self._client.add(messages, **kwargs)
        self.logger.debug(f"Added memory for user={user_id}, agent={agent_id}")
        return result

    def search(
        self,
        query: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        limit: int = 10,
    ) -> list[dict]:
        """
        Search for relevant memories.

        Args:
            query: Natural language search query
            user_id: Filter by user
            agent_id: Filter by agent
            limit: Max results to return

        Returns:
            List of matching memory dicts
        """
        filters = {}
        if user_id:
            filters["user_id"] = user_id
        if agent_id:
            filters["agent_id"] = agent_id

        kwargs = {"limit": limit}
        if filters:
            kwargs["filters"] = filters

        results = self._client.search(query, **kwargs)
        return results

    def get_all(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> list[dict]:
        """
        Get all memories, optionally filtered.

        Args:
            user_id: Filter by user
            agent_id: Filter by agent
            run_id: Filter by run

        Returns:
            List of all matching memories
        """
        kwargs = {}
        if user_id:
            kwargs["user_id"] = user_id
        if agent_id:
            kwargs["agent_id"] = agent_id
        if run_id:
            kwargs["run_id"] = run_id

        return self._client.get_all(**kwargs)

    def get(self, memory_id: str) -> dict:
        """Get a specific memory by ID."""
        return self._client.get(memory_id)

    def update(self, memory_id: str, data: str) -> dict:
        """Update a memory's content."""
        return self._client.update(memory_id, data)

    def delete(self, memory_id: str) -> dict:
        """Delete a specific memory."""
        return self._client.delete(memory_id)

    def delete_all(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
    ) -> dict:
        """Delete all memories, optionally filtered."""
        kwargs = {}
        if user_id:
            kwargs["user_id"] = user_id
        if agent_id:
            kwargs["agent_id"] = agent_id
        return self._client.delete_all(**kwargs)

    def history(self, memory_id: str) -> list[dict]:
        """Get version history of a memory."""
        return self._client.history(memory_id)

    # =========================================================================
    # Graph-to-Agent Integration
    # =========================================================================

    def store_graph_execution(
        self,
        graph_id: str,
        messages: list[dict],
        response: str,
        user_id: Optional[str] = None,
    ) -> dict:
        """
        Store a graph execution as a memory.

        Args:
            graph_id: The executed graph ID
            messages: The messages sent to LLM
            response: The LLM response
            user_id: Optional user context

        Returns:
            Memory storage result
        """
        # Add the response to messages for full context
        full_conversation = messages + [
            {"role": "assistant", "content": response}
        ]

        return self.add_memory(
            messages=full_conversation,
            user_id=user_id,
            metadata={
                "graph_id": graph_id,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "graph_to_agent",
            },
        )

    def get_relevant_context(
        self,
        graph_id: str,
        current_prompt: str,
        user_id: Optional[str] = None,
        limit: int = 5,
    ) -> list[dict]:
        """
        Get relevant memories for a graph execution.

        Useful for providing context from previous executions.

        Args:
            graph_id: Current graph being executed
            current_prompt: The prompt being sent
            user_id: Optional user context
            limit: Max memories to retrieve

        Returns:
            List of relevant memories
        """
        # Search for relevant past context
        return self.search(
            query=current_prompt,
            user_id=user_id,
            limit=limit,
        )

    def inject_memory_context(
        self,
        messages: list[dict],
        user_id: Optional[str] = None,
        memory_limit: int = 3,
    ) -> list[dict]:
        """
        Inject relevant memories into message context.

        Enhances messages with relevant past memories before LLM call.

        Args:
            messages: Original messages
            user_id: User to get memories for
            memory_limit: Max memories to inject

        Returns:
            Enhanced messages with memory context
        """
        if not messages:
            return messages

        # Get last user message as query
        last_user_msg = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break

        if not last_user_msg:
            return messages

        # Search for relevant memories
        memories = self.search(
            query=last_user_msg,
            user_id=user_id,
            limit=memory_limit,
        )

        if not memories:
            return messages

        # Format memories as context
        memory_text = "Relevant context from previous interactions:\n"
        for mem in memories:
            if isinstance(mem, dict) and "memory" in mem:
                memory_text += f"- {mem['memory']}\n"

        # Inject as system message at the start
        memory_msg = {
            "role": "system",
            "content": memory_text,
        }

        return [memory_msg] + messages
