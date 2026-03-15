"""OpenAI agent backend - Updated for OpenAI SDK v1.x (2024+)."""

import os
import logging
from typing import Optional, Iterator

try:
    from openai import OpenAI
    HAS_OPENAI_SDK = True
except ImportError:
    HAS_OPENAI_SDK = False
    OpenAI = None


class OpenAIAgent:
    """
    OpenAI API agent for executing chat completions.

    Uses the modern OpenAI Python SDK v1.x with client instances.

    Example:
        agent = OpenAIAgent()
        response = agent.complete([
            {"role": "user", "content": "Hello!"}
        ])

    For streaming:
        for chunk in agent.stream([{"role": "user", "content": "Hello!"}]):
            print(chunk, end="", flush=True)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",  # Updated to latest recommended model
        base_url: Optional[str] = None,
        timeout: int = 60,
        organization: Optional[str] = None,
    ):
        """
        Initialize OpenAI agent.

        Args:
            api_key: API key (defaults to OPENAI_API_KEY env var)
            model: Model ID to use (gpt-4o, gpt-4-turbo, gpt-3.5-turbo, etc.)
            base_url: Optional API endpoint override
            timeout: Request timeout in seconds
            organization: Optional organization ID
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.organization = organization
        self.logger = logging.getLogger(__name__)

        # Initialize client lazily
        self._client: Optional["OpenAI"] = None

    @property
    def client(self) -> "OpenAI":
        """Get or create the OpenAI client instance."""
        if self._client is None:
            if not HAS_OPENAI_SDK:
                raise ImportError(
                    "openai library required. Install with: pip install openai>=1.0.0"
                )

            if not self.api_key:
                raise ValueError(
                    "API key required. Set OPENAI_API_KEY or pass api_key parameter."
                )

            client_kwargs = {
                "api_key": self.api_key,
                "timeout": self.timeout,
            }

            if self.base_url:
                client_kwargs["base_url"] = self.base_url

            if self.organization:
                client_kwargs["organization"] = self.organization

            self._client = OpenAI(**client_kwargs)

        return self._client

    def complete(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> str:
        """
        Execute a chat completion.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model override (defaults to instance model)
            temperature: Sampling temperature (0-2)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters passed to the API

        Returns:
            Response content string
        """
        self.logger.debug(f"Calling OpenAI with {len(messages)} messages")

        params = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            **kwargs,
        }

        if max_tokens:
            params["max_tokens"] = max_tokens

        response = self.client.chat.completions.create(**params)

        return response.choices[0].message.content

    def stream(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs,
    ) -> Iterator[str]:
        """
        Stream a chat completion.

        Args:
            messages: List of message dicts
            model: Model override
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Yields:
            Content chunks as they arrive
        """
        self.logger.debug(f"Streaming OpenAI with {len(messages)} messages")

        params = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
            "stream": True,
            **kwargs,
        }

        stream = self.client.chat.completions.create(**params)

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def list_models(self) -> list[str]:
        """
        List available models.

        Returns:
            List of model IDs
        """
        models = self.client.models.list()
        return [m.id for m in models.data]


# Backwards-compatible alias
class LegacyOpenAIAgent:
    """
    Legacy agent using raw requests (for environments without openai SDK).

    Prefer OpenAIAgent when possible.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        base_url: str = "https://api.openai.com/v1/chat/completions",
        timeout: int = 60,
    ):
        try:
            import requests
            self._requests = requests
        except ImportError:
            raise ImportError("requests library required: pip install requests")

        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)

    def complete(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Execute a chat completion using raw HTTP requests."""
        if not self.api_key:
            raise ValueError("API key required")

        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature,
        }

        if max_tokens:
            payload["max_tokens"] = max_tokens

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        response = self._requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=self.timeout,
        )
        response.raise_for_status()

        return response.json()["choices"][0]["message"]["content"]
