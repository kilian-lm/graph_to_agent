"""
Redis Streams messaging for Graph-to-Agent.

Replaces legacy Pub/Sub with lightweight, persistent message streams.
Ideal for agent-to-agent communication with message history.

Install: pip install redis
"""

import os
import json
import logging
from typing import Optional, Callable, Any
from datetime import datetime

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False
    redis = None


class RedisStreamsHandler:
    """
    Redis Streams handler for agent messaging.

    Advantages over legacy Pub/Sub:
    - Message persistence (survives restarts)
    - Consumer groups (multiple workers)
    - Message acknowledgment
    - Replay capability
    - Lightweight and fast

    Example:
        handler = RedisStreamsHandler()

        # Publish message
        handler.publish("agent_responses", {"agent_id": "agent_1", "content": "Hello"})

        # Subscribe and process
        for message in handler.subscribe("agent_responses"):
            print(message)
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: int = 6379,
        password: Optional[str] = None,
        db: int = 0,
        decode_responses: bool = True,
    ):
        """
        Initialize Redis connection.

        Args:
            host: Redis host (default: REDIS_HOST env var or localhost)
            port: Redis port (default: 6379)
            password: Redis password (default: REDIS_PASSWORD env var)
            db: Redis database number
            decode_responses: Decode bytes to strings
        """
        if not HAS_REDIS:
            raise ImportError("redis package required. Install with: pip install redis")

        self.host = host or os.getenv("REDIS_HOST", "localhost")
        self.port = port
        self.password = password or os.getenv("REDIS_PASSWORD")
        self.db = db
        self.logger = logging.getLogger(__name__)

        self._client = None

    @property
    def client(self) -> "redis.Redis":
        """Lazy-load Redis client."""
        if self._client is None:
            self._client = redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                db=self.db,
                decode_responses=True,
            )
            # Test connection
            self._client.ping()
            self.logger.info(f"Connected to Redis at {self.host}:{self.port}")
        return self._client

    def close(self):
        """Close Redis connection."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    # =========================================================================
    # Stream Operations
    # =========================================================================

    def publish(
        self,
        stream: str,
        message: dict,
        max_len: Optional[int] = 10000,
    ) -> str:
        """
        Publish a message to a stream.

        Args:
            stream: Stream name (e.g., "agent_responses")
            message: Dict to publish (will be JSON-encoded)
            max_len: Max stream length (older messages trimmed)

        Returns:
            Message ID assigned by Redis
        """
        # Flatten message for Redis (no nested dicts)
        flat_message = {
            "data": json.dumps(message),
            "timestamp": datetime.utcnow().isoformat(),
        }

        message_id = self.client.xadd(
            stream,
            flat_message,
            maxlen=max_len,
            approximate=True,
        )

        self.logger.debug(f"Published to {stream}: {message_id}")
        return message_id

    def subscribe(
        self,
        stream: str,
        last_id: str = "$",
        count: int = 10,
        block: int = 5000,
    ):
        """
        Subscribe to a stream and yield messages.

        Args:
            stream: Stream name
            last_id: Start from this ID ("$" = new messages only, "0" = all)
            count: Max messages per read
            block: Block timeout in ms (0 = forever)

        Yields:
            Tuple of (message_id, parsed_message_dict)
        """
        current_id = last_id

        while True:
            try:
                messages = self.client.xread(
                    {stream: current_id},
                    count=count,
                    block=block,
                )

                if not messages:
                    continue

                for stream_name, stream_messages in messages:
                    for message_id, message_data in stream_messages:
                        current_id = message_id
                        parsed = json.loads(message_data.get("data", "{}"))
                        yield message_id, parsed

            except Exception as e:
                self.logger.error(f"Error reading stream {stream}: {e}")
                raise

    def read_history(
        self,
        stream: str,
        start: str = "-",
        end: str = "+",
        count: int = 100,
    ) -> list:
        """
        Read message history from a stream.

        Args:
            stream: Stream name
            start: Start ID ("-" = beginning)
            end: End ID ("+" = end)
            count: Max messages to return

        Returns:
            List of (message_id, message_dict) tuples
        """
        messages = self.client.xrange(stream, start, end, count=count)

        result = []
        for message_id, message_data in messages:
            parsed = json.loads(message_data.get("data", "{}"))
            result.append((message_id, parsed))

        return result

    # =========================================================================
    # Consumer Groups (for distributed processing)
    # =========================================================================

    def create_consumer_group(
        self,
        stream: str,
        group: str,
        start_id: str = "$",
    ):
        """
        Create a consumer group for distributed processing.

        Args:
            stream: Stream name
            group: Consumer group name
            start_id: Where to start reading ("$" = new, "0" = beginning)
        """
        try:
            self.client.xgroup_create(stream, group, start_id, mkstream=True)
            self.logger.info(f"Created consumer group {group} on {stream}")
        except redis.ResponseError as e:
            if "BUSYGROUP" in str(e):
                self.logger.debug(f"Consumer group {group} already exists")
            else:
                raise

    def consume_group(
        self,
        stream: str,
        group: str,
        consumer: str,
        count: int = 10,
        block: int = 5000,
    ):
        """
        Consume messages as part of a consumer group.

        Args:
            stream: Stream name
            group: Consumer group name
            consumer: This consumer's name
            count: Max messages per read
            block: Block timeout in ms

        Yields:
            Tuple of (message_id, parsed_message_dict)
        """
        while True:
            try:
                messages = self.client.xreadgroup(
                    group,
                    consumer,
                    {stream: ">"},
                    count=count,
                    block=block,
                )

                if not messages:
                    continue

                for stream_name, stream_messages in messages:
                    for message_id, message_data in stream_messages:
                        parsed = json.loads(message_data.get("data", "{}"))
                        yield message_id, parsed

            except Exception as e:
                self.logger.error(f"Error consuming from {stream}/{group}: {e}")
                raise

    def ack(self, stream: str, group: str, message_id: str):
        """Acknowledge a message as processed."""
        self.client.xack(stream, group, message_id)

    # =========================================================================
    # Agent-Specific Helpers
    # =========================================================================

    def publish_agent_message(
        self,
        graph_id: str,
        from_agent: str,
        to_agent: str,
        content: str,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        Publish an agent-to-agent message.

        Args:
            graph_id: The graph execution context
            from_agent: Sender agent ID
            to_agent: Receiver agent ID
            content: Message content
            metadata: Optional additional data

        Returns:
            Message ID
        """
        message = {
            "graph_id": graph_id,
            "from": from_agent,
            "to": to_agent,
            "content": content,
            "metadata": metadata or {},
        }

        stream = f"agent_messages:{graph_id}"
        return self.publish(stream, message)

    def get_agent_messages(
        self,
        graph_id: str,
        agent_id: Optional[str] = None,
        count: int = 100,
    ) -> list:
        """
        Get messages for a graph execution, optionally filtered by agent.

        Args:
            graph_id: The graph execution context
            agent_id: Optional agent to filter for
            count: Max messages

        Returns:
            List of messages
        """
        stream = f"agent_messages:{graph_id}"
        messages = self.read_history(stream, count=count)

        if agent_id:
            messages = [
                (mid, msg) for mid, msg in messages
                if msg.get("to") == agent_id or msg.get("from") == agent_id
            ]

        return messages

    def publish_graph_event(
        self,
        graph_id: str,
        event_type: str,
        data: dict,
    ) -> str:
        """
        Publish a graph lifecycle event.

        Event types: "started", "node_executed", "completed", "error"
        """
        message = {
            "graph_id": graph_id,
            "event": event_type,
            "data": data,
        }

        return self.publish("graph_events", message)
